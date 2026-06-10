import asyncio
from dataclasses import dataclass, field
from hashlib import md5
from typing import (
    Callable,
    Dict,
    List,
    Literal,
    NotRequired,
    Optional,
    Self,
    Tuple,
    TypedDict,
    Union,
)

from coincurve import PrivateKey
from Crypto.Hash import keccak
from gufo.http import RequestMethod
from orjson import loads as orjson_loads
from ormsgpack import packb as ormsgpack_packb

from bknet.error import Error
from bknet.hype.client import HypeHttpClient, HypeWsClient
from bknet.hype.error import (
    HypeErrApiLimit,
    HypeErrNotEnoughMargin,
    HypeErrOrderFailed,
    HypeErrOrderNotFund,
    HypeErrOrderRejected,
    HypeErrOrphanFilled,
    HypeErrorTinyOrder,
    HypeErrPython,
)
from bknet.hype.tr_rest import HypeRestInfoPerp, HypeRestInfoSpot
from bknet.hype.tr_websocket import HypeWsOrderUpdates
from bknet.src import ForceAsyncNew, Macro, MemoryPool, async_schedule


class OrderTypeLimit(TypedDict):
    tif: Literal["alo", "Ioc", "Gtc"]


class OrderTypeMarket(TypedDict):
    isMarket: bool
    triggerPx: str
    tpsl: Literal["tp", "sl"]


OrderType = Union[OrderTypeLimit, OrderTypeMarket]


class HypeOrderPlace(TypedDict):
    assetid: int
    isbuy: bool
    price: str
    size: str
    reduce_only: bool
    odr_type: OrderType
    cloid: NotRequired[str]
    builder_address: NotRequired[str]
    builder_fee: NotRequired[float]


class HypeOrderCancel(TypedDict):
    assetid: int
    oid: str


class HypeOrderModify(TypedDict):
    oid: Union[int, str]
    assetid: int
    isbuy: bool
    price: str
    size: str
    reduce_only: bool
    odr_type: OrderType
    client_oid: NotRequired[str]
    builder_address: NotRequired[str]
    builder_fee: NotRequired[float]


# Type for cloid
class HypeTyCloid:
    """128-bit Client Order ID container for Hyperliquid."""

    __slots__ = ("hex_clean", "raw_bytes")

    hex_clean: str
    raw_bytes: bytes

    def __init__(self, cloid: Union[str, int]) -> None:
        if isinstance(cloid, int):
            clean = f"{cloid:032x}"
        elif isinstance(cloid, str):
            clean = cloid[2:] if cloid.startswith("0x") else cloid
            if len(clean) != 32:
                clean = md5(cloid.encode("utf-8")).hexdigest()
        else:
            raise TypeError(f"Invalid cloid type: {type(cloid)}")

        self.hex_clean = clean.lower()
        self.raw_bytes = bytes.fromhex(self.hex_clean)

    def __str__(self) -> str:
        return self.hex_clean


@dataclass(slots=True, frozen=True)
class HypeCoinInfo:
    asset_id: int
    szDecimals: int
    maxLeverage: int
    prcDecimals: int = field(init=False)

    # Multiplier for low-latency optimization
    _price_multiplier: float = field(init=False, repr=False)
    _size_multiplier: float = field(init=False, repr=False)

    # Format strings for low-latency optimization
    _price_fmt: str = field(init=False, repr=False)
    _size_fmt: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        prc_dec = 6 - self.szDecimals
        object.__setattr__(self, "prcDecimals", prc_dec)

        # multiplier precomputation for numeric normalization (e.g., 10^prcDecimals)
        object.__setattr__(self, "_price_multiplier", 10.0**prc_dec)
        object.__setattr__(self, "_size_multiplier", 10.0**self.szDecimals)

        # precompute C-style format strings for price and size to avoid dynamic string construction during formatting
        object.__setattr__(self, "_price_fmt", f"%.{prc_dec}f")
        object.__setattr__(self, "_size_fmt", f"%.{self.szDecimals}f")

    def format_price(self, price: float) -> str:
        """float price to Hyperliquid API string format"""
        s = self._price_fmt % price
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s if s != "-0" and s != "" else "0"

    def format_size(self, size: float) -> str:
        """float size to Hyperliquid API string format"""
        s = self._size_fmt % size
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s if s != "-0" and s != "" else "0"


#     def format_price(self, price: float) -> str:
#         """Format the price according to the prcDecimals of the coin."""
#         rounded = f"{price:.{self.prcDecimals}f}"
#         if rounded == "-0":
#             rounded = "0"
#         return f"{Decimal(rounded).normalize():f}"

#     def format_size(self, size: float) -> str:
#         """Format the size according to the szDecimals of the coin."""
#         rounded = f"{size:.{self.szDecimals}f}"
#         if rounded == "-0":
#             rounded = "0"
#         return f"{Decimal(rounded).normalize():f}"


@dataclass(slots=True)
class HypeOrder:
    omsid: int = 0
    oid: int = 0
    cloid: Optional[HypeTyCloid] = None
    coin: str = ""
    side: Literal["", "B", "S", "A", "C"] = ""
    kind: Literal["", "Alo", "Ioc", "Gtc"] = ""
    qty: float = 0.0
    prc: float = 0.0
    status: Literal["", "onwire", "onwait", "partial"] = ""

    def init(
        self,
        omsid: int,
        coin: str,
        side: Literal["B", "S", "A", "C"],
        kind: Literal["Alo", "Ioc", "Gtc"],
        qty: float,
        prc: float,
        cloid: Optional[HypeTyCloid] = None,
    ) -> None:
        self.omsid = omsid
        self.cloid = cloid
        self.coin = coin
        self.side = side
        self.kind = kind
        self.qty = qty
        self.prc = prc
        self.status = "onwire"


class HypePerpOMS(ForceAsyncNew):
    """Order management system for Hyperliquid exchange (perpetual).

    use .New() to create an instance of this class.
    """

    user_address: str
    # private_key: str
    dex_list: List[str]

    http_client: HypeHttpClient
    on_error: Callable[[Self, Error], None]
    timeout: float = 1.0

    margin: List[float]
    "[pending_margin, active_margin]"
    posits: Dict[str, list[float]]
    "coin: [pending_size, active_size]"

    orders_onwire: Dict[int, HypeOrder]
    "omsid: HypeOrder"
    orders_onwait: Dict[str, Dict[int, HypeOrder]]
    "coin: {oid: HypeOrder}"
    orders_orphan_filled: Dict[int, List[Tuple[float, float]]]
    "oid: [(filled_qty, filled_prc), ...]"

    bg_tasks: set[asyncio.Task]
    _loop: asyncio.AbstractEventLoop
    _omsid: int
    _headers: Dict[str, bytes]

    # crypt values
    _crypt_private_key: PrivateKey
    _crypt_domain_separator: bytes
    _crypt_agent_typehash: bytes
    _crypt_source_hash: bytes

    map_coin_info: Dict[str, HypeCoinInfo]
    "e.g.) 'xyz:SP500': HypeCoinInfo"

    # Memory management
    _mempool: MemoryPool[HypeOrder]
    _membuf_order_place: Dict
    _membuf_order_cancel: Dict
    _membuf_order_modify: Dict

    @classmethod
    async def New(
        cls,
        user_address: str,
        private_key: str,
        dex_list: List[str],
        http_client: HypeHttpClient,
        ws_client: HypeWsClient,
        on_error: Callable[[Self, Error], None],
        mempool_size: int = 128,
        is_mainnet: bool = True,
    ) -> Self:
        """Create a new instance of HypeOMS.

        Args:

            user_address: (main/sub account) Wallet address
            private_key: (main/agent wallet) Private key
            dex_list: list of HIP-3 dex names to trade (e.g., ['', 'xyz', 'flx']). Empty string '' corresponds to the default dex.
            http_client: HypeHttpClient instance to use for REST API calls
            ws_client: HypeWsClient instance to use for WebSocket API calls
            on_error: callback function to handle errors
            mempool_size: size of the mempool to use for order placement
            is_mainnet: whether to use the mainnet or testnet API
        """
        instance = cls(cls._prevented)
        instance.user_address = user_address
        instance.dex_list = dex_list

        instance.http_client = http_client

        instance.on_error = on_error

        instance.orders_onwire = {}
        instance.orders_onwait = {}
        instance.orders_orphan_filled = {}  # executed message received before order accepted message

        instance.bg_tasks = http_client.bg_tasks
        instance._loop = asyncio.get_running_loop()
        instance._omsid = 0
        instance._headers = {"Content-Type": b"application/json"}

        # Cryptographic values for order signing.
        instance._crypt_private_key = PrivateKey(
            bytes.fromhex(
                private_key[2:] if private_key.startswith("0x") else private_key
            )
        )

        def _local_keccak(b: bytes) -> bytes:
            k = keccak.new(digest_bits=256)
            k.update(b)
            return k.digest()

        instance._crypt_domain_separator = _local_keccak(
            _local_keccak(
                b"EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
            )
            + _local_keccak(b"Exchange")
            + _local_keccak(b"1")
            + (1337).to_bytes(32, "big")
            + (b"\x00" * 32)
        )
        instance._crypt_agent_typehash = _local_keccak(
            b"Agent(string source,bytes32 connectionId)"
        )
        instance._crypt_source_hash = _local_keccak(b"a" if is_mainnet else b"b")

        ### Memory Buffers
        # memory pool for orders
        instance._mempool = MemoryPool(HypeOrder, mempool_size)
        instance._membuf_order_place = {
            "type": "order",
            "orders": [
                {
                    "a": 0,
                    "b": False,
                    "p": "",
                    "s": "",
                    "r": False,
                    "t": {"limit": {"tif": "Gtc"}},
                }
            ],
            "grouping": "na",
        }  # single action buffers

        # Coin info table
        instance.map_coin_info = {}
        await instance.update_coin_info(dex_list)

        # Balance
        instance.margin = [0.0, 0.0]
        instance.posits = {}
        await instance.update_balance(user_address, dex_list)

        return instance

    def _get_omsid(self) -> int:
        self._omsid += 1
        return self._omsid

    def _sign(self, bytes_: bytes) -> tuple[str, str, int]:
        k = keccak.new(digest_bits=256)
        k.update(bytes_)
        connection_id = k.digest()

        k_agent = keccak.new(digest_bits=256)
        k_agent.update(
            self._crypt_agent_typehash + self._crypt_source_hash + connection_id
        )

        k_final = keccak.new(digest_bits=256)
        k_final.update(b"\x19\x01" + self._crypt_domain_separator + k_agent.digest())
        final_signing_hash = k_final.digest()

        sig_bytes = self._crypt_private_key.sign_recoverable(
            final_signing_hash, hasher=None
        )
        r_hex = sig_bytes[0:32].hex()
        s_hex = sig_bytes[32:64].hex()
        v_val = sig_bytes[64] + 27
        return r_hex, s_hex, v_val

    async def _async_order_place(
        self,
        omsid: int,
        coin: str,
        isbuy: bool,
        price: float,
        size: float,
        reduceOnly: bool,
        odrtype: Literal["Alo", "Ioc", "Gtc"],
        cloid: Optional[HypeTyCloid],
        grouping: Literal["na", "normalTpsl", "positionTpsl"],
        # vaultAddress: Optional[str] = None,
        # expiresAfter: Optional[int] = None,
    ):
        # get coin info
        coin_info = self.map_coin_info[coin]
        # use .get(coin, None) with if coin_info is None: return HypeErrCoinNotFound ???

        # format side, price and size
        isbuy_str = "true" if isbuy else "false"
        reduceOnly_str = "true" if reduceOnly else "false"
        price_str = coin_info.format_price(price)
        size_str = coin_info.format_size(size)

        # get nonce
        nonce = Macro.timestamp_ms()

        ### Generate signature
        action_dict = self._membuf_order_place
        order_slot = action_dict["orders"][0]

        order_slot["a"] = coin_info.asset_id
        order_slot["b"] = isbuy
        order_slot["p"] = price_str
        order_slot["s"] = size_str
        order_slot["r"] = reduceOnly
        order_slot["t"]["limit"]["tif"] = odrtype

        if cloid is None:
            order_slot.pop("c", None)
        else:
            order_slot["c"] = f"0x{cloid.hex_clean}"

        action_dict["grouping"] = grouping

        # pack for signing
        pack_for_signing = (
            ormsgpack_packb(action_dict)  #  option=OPT_SORT_KEYS
            + nonce.to_bytes(8, "big")
            + b"\x00"  # \x00 # valutAddress & expiresAfter
        )

        # generate signature
        r_hex, s_hex, v_val = self._sign(pack_for_signing)

        ### Generate post data
        if cloid is None:
            action_json = (
                f'{{"type":"order","orders":['
                f'{{"a":{coin_info.asset_id},'
                f'"b":{isbuy_str},'
                f'"p":"{price_str}",'
                f'"s":"{size_str}",'
                f'"r":{reduceOnly_str},'
                f'"t":{{"limit":{{"tif":"{odrtype}"}}}}}}'  #
                f'],"grouping":"{grouping}"}}'
            )
        else:
            action_json = (
                f'{{"type":"order","orders":['
                f'{{"a":{coin_info.asset_id},'
                f'"b":{isbuy_str},'
                f'"p":"{price_str}",'
                f'"s":"{size_str}",'
                f'"r":{reduceOnly_str},'
                f'"t":{{"limit":{{"tif":"{odrtype}"}}}},'
                f'"c":"0x{cloid.hex_clean}"}}'
                f'],"grouping":"{grouping}"}}'
            )

        try:
            resp = await self.http_client.request_unsafe(
                method=RequestMethod.POST,  # type: ignore
                params="/exchange",
                body=(
                    f'{{"action":{action_json},'
                    f'"nonce":{nonce},'
                    f'"signature":{{"r":"0x{r_hex}","s":"0x{s_hex}","v":{v_val}}}}}'
                ).encode("utf-8"),
                headers=self._headers,
            )
            pedodr: HypeOrder = self.orders_onwire.pop(omsid, None)  # type: ignore
            # NEVER FAIL, order_place is called with a valid omsid, assert(pedodr is not None)
            resp_json = orjson_loads(resp.content)
            status: Dict = (
                resp_json.get("response", {}).get("data", {}).get("statuses", [{}])[0]
            )
            oid: int | None = None
            resting = status.get("resting")
            if resting is not None:
                oid = resting.get("oid")
            else:
                filled = status.get("filled")
                if filled is not None:
                    oid = filled.get("oid")
            # TODO
            if oid is None:  # Error, order failed or rejected
                # free memory
                self._mempool.free(pedodr)
                # error handling
                errmsg: str | None = status.get("error", None)
                # recover margin and position
                self.margin[0] += price * (size if isbuy else -size)
                self.posits[coin][0] -= size
                self.on_error(
                    self,
                    HypeErrOrderFailed(resp_json)
                    if errmsg is None
                    else HypeErrOrderRejected(errmsg),
                )
                return
            # success, update orders_active
            pedodr.oid = oid
            pedodr.status = "onwait"
            self.orders_onwait.setdefault(coin, {})[oid] = pedodr

        except Exception as e:
            pedodr = self.orders_onwire.pop(omsid, None)  # type: ignore
            if pedodr is not None:  # free memory
                self._mempool.free(pedodr)
            # recover margin and position
            self.margin[0] += price * (size if isbuy else -size)
            self.posits[coin][0] -= size
            self.on_error(self, HypeErrPython(e))

    async def _async_order_cancel(
        self, orders: Union[HypeOrderCancel, List[HypeOrderCancel]]
    ):
        pass

    async def _async_order_cancel_coid(
        self, orders: Union[HypeOrderCancel, List[HypeOrderCancel]]
    ):
        pass

    async def _async_order_cancel_schedule_all(self, time: int):
        pass

    async def _async_order_modify(self, order: HypeOrderModify):
        pass

    async def _async_order_modify_multiple(self, orders: List[HypeOrderModify]):
        pass

    def _handle_order_filled(
        self,
        odr: HypeWsOrderUpdates._order,
    ) -> Optional[HypeErrOrphanFilled]:
        filled_coin = odr["coin"]
        filled_oid = odr["oid"]
        filled_qty: float = float(odr["sz"])
        filled_prc: float = float(odr["limitPx"])

        onwait_odr = self.orders_onwait.setdefault(filled_coin, {}).get(
            filled_oid, None
        )
        if (
            onwait_odr is None
        ):  # orphan filled, filled msg received first than order placed
            orphan_odr = self.orders_orphan_filled.get(filled_oid, None)
            if orphan_odr is None:
                self.orders_orphan_filled[filled_oid] = [(filled_qty, filled_prc)]
            else:
                orphan_odr.append((filled_qty, filled_prc))
            return HypeErrOrphanFilled(filled_oid)

        posits = self.posits[
            filled_coin
        ]  # assert No KeyError, posit is initialized when order is placed
        actpos_before = abs(posits[1])

        if odr["side"] == "B":
            posits[0] -= filled_qty
            posits[1] += filled_qty
        else:
            posits[0] += filled_qty
            posits[1] -= filled_qty

        margin = self.margin
        if abs(posits[1]) < actpos_before:  # position reduced
            margin[1] += (
                filled_qty * filled_prc
            )  # available margin increases when position is reduced
        else:  # position increased
            margin[0] += filled_qty * onwait_odr.prc  # pending margin is released
            margin[1] -= (
                filled_qty * filled_prc
            )  # available margin decreases when position is increase
        onwait_odr.qty -= filled_qty
        if onwait_odr.qty == 0:
            del self.orders_onwait[filled_coin][filled_oid]
            self._mempool.free(onwait_odr)
        else:
            onwait_odr.status = "partial"

        return None

    def _handle_order_canceled(
        self, odr: HypeWsOrderUpdates._order
    ) -> Optional[HypeErrOrderNotFund]:
        coin = odr["coin"]
        oid = odr["oid"]
        onwait_odr = self.orders_onwait.setdefault(coin, {}).get(oid, None)
        if onwait_odr is None:
            return HypeErrOrderNotFund(oid)

        posits = self.posits[coin]
        odrqty = onwait_odr.qty
        posits[0] += odrqty if odr["side"] == "B" else -odrqty
        self.margin[0] += odrqty * onwait_odr.prc

        del self.orders_onwait[coin][oid]
        self._mempool.free(onwait_odr)

        return None

    def bind_ws_client(self, ws_client: HypeWsClient):
        def _handle_WsHypeOrderUpdates(_: HypeWsClient, msg: HypeWsOrderUpdates):
            odr = msg["order"]
            odr_status = msg["status"]
            if odr_status == "filled":  # "filled"
                self._handle_order_filled(odr)
            # elif odr_status == "open": # "open"
            #     pass
            elif odr_status == "canceled":  # "canceled"
                self._handle_order_canceled(odr)
            elif odr_status == "rejected":  # "rejected"
                pass
            elif odr_status.endswith("Canceled"):  # "canceled" (e.g., "marginCanceled")
                pass
            elif odr_status.endswith("Rejected"):  # "rejected" (e.g., "tickRejected")
                pass
            else:
                # TODO handle other statuses
                pass

        ws_client._callbacks["orderUpdates"] = _handle_WsHypeOrderUpdates  # type: ignore
        ws_client.subscribe(f'{{"type":"orderUpdates","user":"{self.user_address}"}}')

    async def update_coin_info(self, dex_list: List[str]):
        """Update the coin info table with the latest coin information from the Hyperliquid API.

        Args:
            dex_list: list of HIP-3 dex names to trade (e.g., ['xyz', 'flx']). If None, all dexs will be included.
        """
        # Native Perpetuals have aid = meta_index
        if "" in dex_list:
            meta_result = await HypeRestInfoPerp.meta(self.http_client, "")
            for universe_info in meta_result[0].values():
                self.map_coin_info[universe_info["name"]] = HypeCoinInfo(
                    asset_id=universe_info["dev_meta_index"],
                    szDecimals=universe_info["szDecimals"],
                    maxLeverage=universe_info["maxLeverage"],
                )

        perpDexs = await HypeRestInfoPerp.perpDexs(self.http_client)
        perpDexs = {dex: info for dex, info in perpDexs.items() if dex in dex_list}

        meta_results = await asyncio.gather(
            *[HypeRestInfoPerp.meta(self.http_client, name) for name in perpDexs.keys()]
        )

        for idx, dex_name in enumerate(perpDexs.keys()):
            dex_info = perpDexs[dex_name]
            perp_dex_index = dex_info["dev_dex_index"]
            for universe_info in meta_results[idx][0].values():
                meta_coin_index = universe_info["dev_meta_index"]
                # Perpetuals on HIP-3 dexs have aid = 100000 + (dex_index * 10000) + meta_index
                self.map_coin_info[universe_info["name"]] = HypeCoinInfo(
                    asset_id=100000 + (perp_dex_index * 10000) + meta_coin_index,
                    szDecimals=universe_info["szDecimals"],
                    maxLeverage=universe_info["maxLeverage"],
                )

    async def update_balance(self, user_address: str, dex_list: List[str]):
        """Update the margin and position information.

        Note:
            Only USDC balance is considered for margin.
        """
        if "" not in dex_list:
            dex_list.append("")

        resp = None
        for dex_name in dex_list:
            resp = await HypeRestInfoPerp.clearinghouseState(
                self.http_client, user_address, dex_name
            )
            for v in resp["assetPositions"]:
                position = v["position"]
                posit = self.posits.setdefault(position["coin"], [0.0, 0.0])
                posit[1] = float(position["szi"])
        # if resp is not None:
        #     self.margin[1] = float(resp["marginSummary"]["totalRawUsd"])
        resp = await HypeRestInfoSpot.clearinghouseState(self.http_client, user_address)
        if resp is not None:
            for token, total in resp["tokenToAvailableAfterMaintenance"]:
                if token == 0:  # USDC
                    self.margin[1] = float(total)
                    break
                # 235:USDE, 268:USDT0, 360:USDH

    def order_place(
        self,
        coin: str,
        isbuy: bool,
        price: float,
        size: float,
        reduceOnly: bool,
        odrtype: Literal["Alo", "Ioc", "Gtc"],
        cloid: Optional[Union[HypeTyCloid, Literal[""]]] = None,
        grouping: Literal["na", "normalTpsl", "positionTpsl"] = "na",
        # vaultAddress: Optional[str] = None,
        # expiresAfter: Optional[int] = None,
    ) -> Optional[HypeErrApiLimit | HypeErrorTinyOrder | HypeErrNotEnoughMargin]:
        """Order a new limit order on the Hyperliquid exchange.

        Args:
            coin (str): The coin symbol to order. e.g.) xyz:SP500
            isbuy (bool): Whether to buy or sell.
            price (float): The price of the order.
            size (float): The size of the order.
            reduceOnly (bool): Whether the order is reduce-only.
            odrtype (Literal["Alo", "Ioc", "Gtc"]): The order type.
            cloid (Optional[str]): The client order ID. If empty string '', auto-generated omsid is used as cloid.
            grouping (Literal["na", "normalTpsl", "positionTpsl"]): The order grouping. Defaults to "na".
        """
        # check API limit
        if self.http_client._api_limit_weight >= 1:
            self.http_client._api_limit_weight -= 1
        else:
            return HypeErrApiLimit(None)

        # check margin and position
        pedmrg, actmrg = self.margin
        delta_mrg = price * size
        pedmrg -= delta_mrg

        posits = self.posits.setdefault(coin, [0, 0])
        delta_pos = size if isbuy else -size

        if reduceOnly:
            pass
        elif delta_mrg < 10:
            self.http_client._api_limit_weight += 1  # API token rollback
            return HypeErrorTinyOrder(  # Minimum order size is 10 USDC
                {"action": "order_place", "current": delta_mrg, "required": 10.0}
            )
        elif (pedmrg + actmrg) < 0:
            actpos = posits[1]
            if abs(actpos + delta_pos) > abs(
                actpos
            ):  # if new position is larger than current position, check margin
                self.http_client._api_limit_weight += 1  # API token rollback
                return HypeErrNotEnoughMargin(
                    {"action": "order_place", "current": actmrg, "required": delta_mrg}
                )

        self.margin[0] = pedmrg
        posits[0] += delta_pos

        # Allocate pending order
        omsid = self._get_omsid()
        if cloid is None:
            pass
        elif cloid == "":  # cloid as omsid
            cloid = HypeTyCloid(omsid)

        odr = self._mempool.alloc()
        odr.init(
            omsid=omsid,
            coin=coin,
            side="B" if isbuy else "S",
            kind=odrtype,
            qty=size,
            prc=price,
            cloid=cloid,
        )
        self.orders_onwire[omsid] = odr

        # async order place
        async_schedule(
            self._async_order_place,
            self.bg_tasks,
            omsid,
            coin,
            isbuy,
            price,
            size,
            reduceOnly,
            odrtype,
            cloid,
            grouping,
        )

    def order_place_mult(self, orders: List[HypeOrderPlace]):
        pass

    def order_cancel_mult(self, orders: List[HypeOrderCancel]):
        pass

    def order_cancel_coid_mult(self, orders: List[HypeOrderCancel]):
        pass

    def order_cancel_schedule_all(self, time: int):
        pass

    def order_modify(self, order: HypeOrderModify):
        pass

    def order_modify_mult(self, orders: List[HypeOrderModify]):
        pass
