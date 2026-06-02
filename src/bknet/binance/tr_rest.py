from typing import List, Literal, Optional

from gufo.http import RequestMethod
from orjson import loads as orjson_loads

from bknet.binance.client import BinanceSptHttpClient


class BinanceSptRest:
    @staticmethod
    async def exchangeInfo(
        http_client: BinanceSptHttpClient,
        symbols: Optional[List[str]] = None,
        permissions: Optional[List[Literal["SPOT", "MARGIN", "LEVERAGED"]]] = None,
        showPermissionSets: Optional[bool] = None,
        symbolStatus: Optional[Literal["TRADING", "HALT", "BREAK"]] = None,
    ):
        resp = await http_client.request(
            20,
            RequestMethod.GET,  # type: ignore
            params="/api/v3/exchangeInfo",
        )
