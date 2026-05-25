from typing import Dict, List, Literal, Optional, Tuple, TypedDict

from gufo.http import RequestMethod
from orjson import loads as orjson_loads

from bknet.hype.client import HypeHttpClient


class HypeInfoUniverse(TypedDict):
    # Hyperliquid API fields
    szDecimals: int
    name: str
    "coin name (e.g., 'BTC', 'xyz:SP500')"
    maxLeverage: int
    isDelisted: Optional[bool]
    marginTableId: Optional[int]
    onlyIsolated: Optional[bool]
    "deprecated. Means either 'strictIsolated' or 'noCross'"
    marginMode: Optional[Literal["strictIsolated", "noCross"]]
    "margin mode, 'strictIsolated' means margin cannot be removed, 'noCross' means only isolated margin allowed"
    growthMode: Optional[str]
    lastGrowthModeChangeTime: Optional[str]
    # For internal use
    dev_meta_index: int


class HypeInfoMarginTier(TypedDict):
    lowerBound: str
    maxLeverage: int


class HypeInfoMarginTable(TypedDict):
    # Hyperliquid API fields
    description: str
    marginTiers: List[HypeInfoMarginTier]


class HypeInfoPerpDexs(TypedDict):
    # Hyperliquid API fields
    name: str
    "short name (e.g., 'xyz')"
    fullName: str
    "full name"
    deployer: str
    "deployer address"
    oracleUpdater: Optional[str]
    "oracle updater address"
    feeRecipient: Optional[str]
    "fee recipient address, if null fee goes to deployer"
    assetToStreamingOiCap: List[Tuple[str, str]]
    "open intrest cap, List[coin, OI cap]"
    assetToFundingMultiplier: List[Tuple[str, str]]
    "funding multiplier, List[coin, funding multiplier]"
    # For internal use
    dev_dex_index: int


class HypeRestInfo:
    @staticmethod
    async def perpDexs(http_client: HypeHttpClient) -> Dict[str, HypeInfoPerpDexs]:
        """Get perpetual dex information"""
        resp = await http_client.request(
            20,
            RequestMethod.POST,  # type: ignore
            params="/info",
            body=b'{"type":"perpDexs"}',
        )
        resp_json: List[Optional[HypeInfoPerpDexs]] = orjson_loads(resp.content)
        result: Dict[str, HypeInfoPerpDexs] = {}
        for dex_index, dex_info in enumerate(resp_json):
            if dex_info is None:
                continue
            dex_info["dev_dex_index"] = dex_index
            result[dex_info["name"]] = dex_info
        return result

    @staticmethod
    async def meta(
        http_client: HypeHttpClient, dex: str
    ) -> Tuple[Dict[str, HypeInfoUniverse], Dict[int, HypeInfoMarginTable]]:
        """Get perpetual dex information"""
        resp = await http_client.request(
            20,
            RequestMethod.POST,  # type: ignore
            params="/info",
            body=f'{{"type":"meta","dex":"{dex}"}}'.encode(),
        )
        resp_json = orjson_loads(resp.content)
        universe: List[HypeInfoUniverse] = resp_json.get("universe", [])
        margin_tables: List[Tuple[int, HypeInfoMarginTable]] = resp_json.get(
            "marginTables", []
        )
        result_universe: Dict[str, HypeInfoUniverse] = {}
        for meta_index, v in enumerate(universe):
            v["dev_meta_index"] = meta_index
            result_universe[v["name"]] = v
        result_margin_tables: Dict[int, HypeInfoMarginTable] = {}
        for table_index, v in margin_tables:
            result_margin_tables[table_index] = v
        return result_universe, result_margin_tables
