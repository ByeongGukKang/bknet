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
    TypedDict,
    Union,
)

from coincurve import PrivateKey
from Crypto.Hash import keccak
from gufo.http import RequestMethod
from orjson import loads as orjson_loads
from ormsgpack import packb as ormsgpack_packb

from bknet.error import Error, MaybeError
from bknet.hype.client import HypeHttpClient, HypeWsClient
from bknet.hype.error import (
    HypeErrApiLimit,
    HypeErrNotEnoughMargin,
    HypeErrOrderFailed,
    HypeErrOrderNotFund,
    HypeErrOrderRejected,
    HypeErrOrphanOrderExecuted,
    HypeErrPython,
)
from bknet.hype.tr_rest import HypeRestInfo
from bknet.src import ForceAsyncNew, Macro, MemoryPool, async_in_def


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


# Type alias for cloid
class HypeCloid(str):
    "Always valid 128 bit hex string"

    def __new__(cls, cloid: Union[str, int]) -> "HypeCloid":
        if type(cloid) is HypeCloid:
            return cloid
        elif type(cloid) is int:
            return HypeCloid(f"0x{cloid:032x}")
        elif type(cloid) is str:
            clean = cloid[2:] if cloid.startswith("0x") else cloid
            cl_len = len(clean)

            if cl_len == 32:
                try:
                    int(clean, 16)
                    return HypeCloid(f"0x{clean.lower()}")
                except ValueError:
                    pass

            if cl_len < 32:
                try:
                    int(clean, 16)
                    return HypeCloid(f"0x{clean.lower():0>32}")
                except ValueError:
                    pass

            hashed = md5(cloid.encode("utf-8")).hexdigest()
            return HypeCloid(f"0x{hashed}")
        else:
            raise TypeError(f"Invalid cloid type: {type(cloid)}")


@dataclass(slots=True, frozen=True)
class HypeCoinInfo:
    asset_id: int
    szDecimals: int
    maxLeverage: int
    prcDecimals: int = field(init=False)

    def __post_init__(self) -> None:
        """Automatically set prcDecimals.

        https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/tick-and-lot-size
        """
        # frozen=True bypass
        object.__setattr__(self, "prcDecimals", 6 - self.szDecimals)

    def format_price(self, price: float) -> str:
        """Format the price according to the prcDecimals of the coin."""
        return f"{price:.{self.prcDecimals}f}"

    def format_size(self, size: float) -> str:
        """Format the size according to the szDecimals of the coin."""
        return f"{size:.{self.szDecimals}f}"


@dataclass(slots=True)
class HypeOrder:
    omsid: int = 0
    oid: int = 0
    cloid: Optional[HypeCloid] = None
    coin: str = ""
    side: Literal["", "B", "S", "A", "C"] = ""
    kind: Literal["", "Alo", "Ioc", "Gtc"] = ""
    qty: float = 0.0
    prc: float = 0.0
    status: Literal["", "wire", "wait", "partial"] = ""

    def init(
        self,
        omsid: int,
        coin: str,
        side: Literal["B", "S", "A", "C"],
        kind: Literal["Alo", "Ioc", "Gtc"],
        qty: float,
        prc: float,
        cloid: Optional[HypeCloid] = None,
    ) -> None:
        self.omsid = omsid
        self.cloid = cloid
        self.coin = coin
        self.side = side
        self.kind = kind
        self.qty = qty
        self.prc = prc
        self.status = "wire"


class HypeOMS(ForceAsyncNew):
    """Order management system for Hyperliquid exchange.

    use .New() to create an instance of this class.
    """

    http_client: HypeHttpClient
    on_error: Callable[[Self, Error], None]
    timeout: float = 1.0

    margin: List[float]
    "[pending_margin, active_margin]"
    posits: Dict[str, list[float]]
    "coin: [pending_size, active_size]"

    orders_pending: Dict[int, HypeOrder]
    "omsid: HypeOrder"
    orders_active: Dict[str, Dict[int, HypeOrder]]
    "coin: {oid: HypeOrder}"
    orders_orphan: Dict[int, HypeOrder]
    "oid: order"

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
        private_key: str,
        http_client: HypeHttpClient,
        ws_client: HypeWsClient,
        on_error: Callable[[Self, Error], None],
        dex_list: Optional[List[str]] = None,
        mempool_size: int = 128,
        is_mainnet: bool = True,
    ) -> Self:
        """Create a new instance of HypeOMS.

        Args:
            http_client: HypeHttpClient instance to use for REST API calls
            ws_client: HypeWsClient instance to use for WebSocket API calls
            dex_list: list of HIP-3 dex names to trade (e.g., ['xyz', 'flx']). If None, all dexs will be included.

        Note:
            - empty string '' in dex_list corresponds to the default dex.

        urls:
            - Asset ID: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/asset-ids

        """
        instance = cls(cls._prevented)
        instance.http_client = http_client

        instance.orders_pending = {}
        instance.orders_active = {}
        instance.orders_orphan = {}  # executed message received before order accepted message

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

        # Initialize memory pool for orders
        instance._mempool = MemoryPool(HypeOrder, mempool_size)

        # Initialize single action buffers
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
        }

        ###  Initialize coin info table
        instance.map_coin_info = {}

        # Native Perpetuals have aid = meta_index
        if (dex_list is None) or ("" in dex_list):
            meta_result = await HypeRestInfo.meta(http_client, "")
            for universe_info in meta_result[0].values():
                instance.map_coin_info[universe_info["name"]] = HypeCoinInfo(
                    asset_id=universe_info["dev_meta_index"],
                    szDecimals=universe_info["szDecimals"],
                    maxLeverage=universe_info["maxLeverage"],
                )

        perpDexs = await HypeRestInfo.perpDexs(http_client)
        if dex_list is not None:
            perpDexs = {dex: info for dex, info in perpDexs.items() if dex in dex_list}

        tasks = [HypeRestInfo.meta(http_client, name) for name in perpDexs.keys()]
        meta_results = await asyncio.gather(*tasks)

        for idx, dex_name in enumerate(perpDexs.keys()):
            dex_info = perpDexs[dex_name]
            perp_dex_index = dex_info["dev_dex_index"]
            for universe_info in meta_results[idx][0].values():
                meta_coin_index = universe_info["dev_meta_index"]
                # Perpetuals on HIP-3 dexs have aid = 100000 + (dex_index * 10000) + meta_index
                instance.map_coin_info[universe_info["name"]] = HypeCoinInfo(
                    asset_id=100000 + (perp_dex_index * 10000) + meta_coin_index,
                    szDecimals=universe_info["szDecimals"],
                    maxLeverage=universe_info["maxLeverage"],
                )

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
        cloid: Optional[str],
        grouping: Literal["na", "normalTpsl", "positionTpsl"],
        # vaultAddress: Optional[str] = None,
        # expiresAfter: Optional[int] = None,
    ):
        # get coin info
        coin_info = self.map_coin_info[coin]

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
            order_slot["c"] = cloid

        action_dict["grouping"] = grouping

        # pack for signing
        pack_for_signing = (
            ormsgpack_packb(action_dict)
            + nonce.to_bytes(8, "big")
            + b"\x00\x00"  # valutAddress & expiresAfter
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
                f'"t":{{"limit":{{"tif":"{odrtype}"}}}}}}'
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
                f'"c":"{cloid}"}}'
                f'],"grouping":"{grouping}"}}'
            )

        try:
            resp = await self.http_client.request_unsafe(
                method=RequestMethod.POST,  # type: ignore
                body=(
                    f'{{"action":{action_json},'
                    f'"nonce":{nonce},'
                    f'"signature":{{"r":"0x{r_hex}","s":"0x{s_hex}","v":{v_val}}}}}'
                ).encode("utf-8"),
                headers=self._headers,
            )
            pedodr: HypeOrder = self.orders_pending.pop(omsid, None)  # type: ignore
            # NEVER FAIL, order_place is called with a valid omsid
            # assert(pedodr is not None)
            resp_json = orjson_loads(resp.content)
            status: Dict = (
                resp_json.get("response", {}).get("data", {}).get("statuses", [{}])[0]
            )
            oid: int | None = status.get("resting", {}).get("oid", None)
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
            pedodr.status = "wait"
            self.orders_active.setdefault(coin, {})[oid] = pedodr

        except Exception as e:
            pedodr = self.orders_pending.pop(omsid, None)  # type: ignore
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

    def order_place(
        self,
        coin: str,
        isbuy: bool,
        price: float,
        size: float,
        reduceOnly: bool,
        odrtype: Literal["Alo", "Ioc", "Gtc"],
        cloid: Optional[Union[HypeCloid, Literal[""]]] = None,
        grouping: Literal["na", "normalTpsl", "positionTpsl"] = "na",
        # vaultAddress: Optional[str] = None,
        # expiresAfter: Optional[int] = None,
    ) -> MaybeError[HypeErrApiLimit]:
        """Order a new limit order on the Hyperliquid exchange.

        Args:
            coin (str): The coin symbol to order. e.g.) xyz:SP500
            isbuy (bool): Whether to buy or sell.
            price (float): The price of the order.
            size (float): The size of the order.
            reduceOnly (bool): Whether the order is reduce-only.
            odrtype (Literal["Alo", "Ioc", "Gtc"]): The order type.
            cloid (Optional[str]): The client order ID.
            grouping (Literal["na", "normalTpsl", "positionTpsl"]): The order grouping.

        Notes:
            If cloid == "", auto-generated omsid is used as cloid.
        """
        # check API limit
        if self.http_client._api_limit_weight >= 1:
            self.http_client._api_limit_weight -= 1
        else:
            return HypeErrApiLimit(None)

        # check margin and position
        pedmgr, actmrg = self.margin
        pedpos, _ = self.posits.setdefault(coin, [0, 0])

        pedmgr -= price * (size if isbuy else -size)
        pedpos += size
        if (pedmgr + actmrg) < 0:
            self.http_client._api_limit_weight += 1  # API token rollback
            self.on_error(
                self,
                HypeErrNotEnoughMargin(
                    {
                        "action": "order_place",
                        "current": actmrg,
                        "required": price * (size if isbuy else -size),
                    }
                ),
            )
            return
        # update pending margin and position
        self.margin[0] = pedmgr
        self.posits[coin][0] = pedpos

        # Allocate pending order
        omsid = self._get_omsid()
        if cloid is None:
            pass
        elif cloid == "":  # cloid as omsid
            cloid = HypeCloid(omsid)

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
        self.orders_pending[omsid] = odr

        # async order place
        async_in_def(
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
