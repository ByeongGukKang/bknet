import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Literal, NotRequired, Optional, Self, TypedDict, Union

from coincurve import PrivateKey
from Crypto.Hash import keccak
from gufo.http import RequestMethod
from orjson import loads as orjson_loads
from ormsgpack import packb as ormsgpack_packb

from bknet.hype.client import HypeHttpClient, HypeWsClient
from bknet.hype.tr_rest import HypeRestInfo
from bknet.src import ForceAsyncNew, MaybeError, MemoryPool, async_in_def


class OrderTypeLimit(TypedDict):
    tif: Literal["alo", "Ioc", "Gtc"]


class OrderTypeMarket(TypedDict):
    isMarket: bool
    triggerPx: str
    tpsl: Literal["tp", "sl"]


OrderType = Union[OrderTypeLimit, OrderTypeMarket]


class HypeOrderPlace(TypedDict):
    asset: int
    isbuy: bool
    price: str
    size: str
    reduce_only: bool
    odr_type: OrderType
    client_oid: NotRequired[str]
    builder_address: NotRequired[str]
    builder_fee: NotRequired[float]


class HypeOrderCancel(TypedDict):
    asset: int
    oid: str


class HypeOrderModify(TypedDict):
    oid: Union[int, str]
    asset: int
    isbuy: bool
    price: str
    size: str
    reduce_only: bool
    odr_type: OrderType
    client_oid: NotRequired[str]
    builder_address: NotRequired[str]
    builder_fee: NotRequired[float]


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


class HypeOMS(ForceAsyncNew):
    """Order management system for Hyperliquid exchange.

    use .New() to create an instance of this class.
    """

    private_key: str
    http_client: HypeHttpClient
    timeout: float = 1.0

    cash: List[float]
    "[pending_cash, active_cash]"
    posits: Dict[str, list[float]]
    "coin: [pending_size, active_size]"

    orders_pending: dict[str, HypeOrderPlace]
    "oid: order"
    orders_active: dict[str, HypeOrderPlace]
    "oid: order"
    orders_orphan: dict[str, HypeOrderPlace]
    "oid: order"

    bg_tasks: set[asyncio.Task]
    _loop: asyncio.AbstractEventLoop

    # crypt values
    _crypt_domain_separator: bytes
    _crypt_agent_typehash: bytes
    _crypt_source_hash: bytes

    coin_info_table: Dict[str, HypeCoinInfo]
    "e.g.) 'xyz:SP500': HypeCoinInfo"
    _mempool_order_place: MemoryPool
    _mempool_order_cancel: MemoryPool
    _mempool_order_modify: MemoryPool

    @classmethod
    async def New(
        cls,
        private_key: str,
        http_client: HypeHttpClient,
        ws_client: HypeWsClient,
        dex_list: Optional[List[str]] = None,
        memory_pool_size: int = 64,
        is_mainnet: bool = True,
        *args,
        **kwargs,
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
        instance.private_key = private_key
        instance.http_client = http_client

        instance.orders_pending = {}
        instance.orders_active = {}
        instance.orders_orphan = {}  # executed message received before order accepted message

        instance.bg_tasks = http_client.bg_tasks
        instance._loop = asyncio.get_running_loop()

        # Cryptographic values for order signing.
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

        # Initialize coin info table
        instance.coin_info_table = {}

        # Native Perpetuals have aid = meta_index
        if (dex_list is None) or ("" in dex_list):
            meta_result = await HypeRestInfo.meta(http_client, "")
            for universe_info in meta_result[0].values():
                instance.coin_info_table[universe_info["name"]] = HypeCoinInfo(
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
                instance.coin_info_table[universe_info["name"]] = HypeCoinInfo(
                    asset_id=100000 + (perp_dex_index * 10000) + meta_coin_index,
                    szDecimals=universe_info["szDecimals"],
                    maxLeverage=universe_info["maxLeverage"],
                )

        # Initialize memory pools for orders
        instance._mempool_order_place = MemoryPool(HypeOrderPlace, memory_pool_size)
        instance._mempool_order_cancel = MemoryPool(HypeOrderCancel, memory_pool_size)
        instance._mempool_order_modify = MemoryPool(HypeOrderModify, memory_pool_size)

        return instance

    async def _async_order_place(
        self, orders: Union[HypeOrderPlace, List[HypeOrderPlace]]
    ):
        pass

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
        cloid: Optional[str] = None,
        grouping: Literal["na", "normalTpsl", "positionTpsl"] = "na",
        vaultAddress: Optional[str] = None,
        expiresAfter: Optional[int] = None,
    ):
        coin_info = self.coin_info_table[coin]

        b_str = "true" if isbuy else "false"
        r_str = "true" if reduceOnly else "false"
        p_str = coin_info.format_price(price)
        s_str = coin_info.format_size(size)

        if cloid is None:
            action = (
                f'{{"type":"order","orders":['
                f'{{"a":{coin_info.asset_id},'
                f'"b":{b_str},'
                f'"p":"{p_str}",'
                f'"s":"{s_str}",'
                f'"r":{r_str},'
                f'"t":{{"limit":{{"tif":"{odrtype}"}}}}}}'
                f'],"grouping":"{grouping}"}}'
            )
        else:
            action = (
                f'{{"type":"order","orders":['
                f'{{"a":{coin_info.asset_id},'
                f'"b":{b_str},'
                f'"p":"{p_str}",'
                f'"s":"{s_str}",'
                f'"r":{r_str},'
                f'"t":{{"limit":{{"tif":"{odrtype}"}}}},'
                f'"cloid":"{cloid}"}}'
                f'],"grouping":"{grouping}"}}'
            )

        vault_str = "" if vaultAddress is None else f',"vaultAddress":"{vaultAddress}"'
        expires_str = "" if expiresAfter is None else f',"expiresAfter":{expiresAfter}'

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
