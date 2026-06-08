from typing import Dict, List, Literal, Optional, Tuple, TypedDict

from gufo.http import RequestMethod
from orjson import loads as orjson_loads

from bknet.hype.client import HypeHttpClient


class HypeRestInfoPerpResult:
    class perpDexs(TypedDict):
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

    class metaUniverse(TypedDict):
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

    class metaMarginTable(TypedDict):
        # Hyperliquid API fields
        description: str

        class _marginTier(TypedDict):  # type: ignore
            lowerBound: str
            maxLeverage: int

        marginTiers: List[_marginTier]

    class clearingHouseState(TypedDict):
        class _assetPosition(TypedDict):  # type: ignore
            class _Position(TypedDict):  # type: ignore
                class _CumFunding(TypedDict):  # type: ignore
                    allTime: str
                    sinceChange: str
                    sinceOpen: str

                coin: str
                cumFunding: _CumFunding
                entryPrx: str

                class _Leverage(TypedDict):  # type: ignore
                    rawUsd: str
                    type: Literal["cross", "isolated"]
                    value: int

                leverage: _Leverage
                liquidationPx: str
                marginUsed: str
                maxLeverage: int
                positionValue: str
                returnOnEquity: str
                szi: str
                unrealizedPnl: str

            position: _Position
            type: Literal["oneway"]

        assetPositions: List[_assetPosition]
        crossMaintenanceMarginUsed: str

        class _marginSummary(TypedDict):  # type: ignore
            accountValue: str
            totalMarginUsed: str
            totalNtlPos: str
            totalRawUsd: str

        crossMarginSummary: _marginSummary
        marginSummary: _marginSummary
        time: int
        withdrawable: str


class HypeRestInfoPerp:
    @staticmethod
    async def perpDexs(
        http_client: HypeHttpClient,
    ) -> Dict[str, HypeRestInfoPerpResult.perpDexs]:
        """Get perpetual dex information"""
        resp = await http_client.request(
            20,
            RequestMethod.POST,  # type: ignore
            params="/info",
            body=b'{"type":"perpDexs"}',
        )
        resp_json: List[Optional[HypeRestInfoPerpResult.perpDexs]] = orjson_loads(
            resp.content
        )
        result: Dict[str, HypeRestInfoPerpResult.perpDexs] = {}
        for dex_index, dex_info in enumerate(resp_json):
            if dex_info is None:
                continue
            dex_info["dev_dex_index"] = dex_index
            result[dex_info["name"]] = dex_info
        return result

    @staticmethod
    async def meta(
        http_client: HypeHttpClient, dex: str
    ) -> Tuple[
        Dict[str, HypeRestInfoPerpResult.metaUniverse],
        Dict[int, HypeRestInfoPerpResult.metaMarginTable],
    ]:
        """Get perpetual dex information"""
        resp = await http_client.request(
            20,
            RequestMethod.POST,  # type: ignore
            params="/info",
            body=f'{{"type":"meta","dex":"{dex}"}}'.encode(),
        )
        resp_json = orjson_loads(resp.content)
        universe: List[HypeRestInfoPerpResult.metaUniverse] = resp_json.get(
            "universe", []
        )
        margin_tables: List[Tuple[int, HypeRestInfoPerpResult.metaMarginTable]] = (
            resp_json.get("marginTables", [])
        )
        result_universe: Dict[str, HypeRestInfoPerpResult.metaUniverse] = {}
        for meta_index, v in enumerate(universe):
            v["dev_meta_index"] = meta_index
            result_universe[v["name"]] = v
        result_margin_tables: Dict[int, HypeRestInfoPerpResult.metaMarginTable] = {}
        for table_index, v in margin_tables:
            result_margin_tables[table_index] = v
        return result_universe, result_margin_tables

    @staticmethod
    async def clearinghouseState(
        http_client: HypeHttpClient, address: str, dex: str = ""
    ) -> HypeRestInfoPerpResult.clearingHouseState:
        resp = await http_client.request(
            20,
            RequestMethod.POST,  # type: ignore
            params="/info",
            body=f'{{"type":"clearinghouseState","user":"{address}","dex":"{dex}"}}'.encode(),
        )
        resp_json: HypeRestInfoPerpResult.clearingHouseState = orjson_loads(
            resp.content
        )
        return resp_json


class HypeRestInfoSpotResult:
    class clearingHouseState(TypedDict):
        class _balance(TypedDict):  # type: ignore
            coin: str
            token: int
            hold: str
            total: str
            entryNtl: str

        balances: List[_balance]
        tokenToAvailableAfterMaintenance: List[Tuple[int, str]]


class HypeRestInfoSpot:
    @staticmethod
    async def clearinghouseState(
        http_client: HypeHttpClient, address: str
    ) -> HypeRestInfoSpotResult.clearingHouseState:
        resp = await http_client.request(
            20,
            RequestMethod.POST,  # type: ignore
            params="/info",
            body=f'{{"type":"spotClearinghouseState","user":"{address}"}}'.encode(),
        )
        resp_json: HypeRestInfoSpotResult.clearingHouseState = orjson_loads(
            resp.content
        )
        return resp_json
