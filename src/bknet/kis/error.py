from typing import Dict

from bknet.error import Error, SomethingNotEnough


class KisErrPython(Error[Exception]):
    code = "KisErrPython"
    msg = "[Kis] Python exception"


class KisErrApiLimit(Error[None]):
    code = "KisErrApiLimit"
    msg = "[Kis] API limit reached"


class KisErrOrphanOrderExecuted(Error[str]):
    data: str
    "order_id"
    code = "KisErrOrphanOrderExecuted"
    msg = "[Kis] Orphan order executed"


class KisErrOrderNotFund(Error[str]):
    data: str
    "order_id"
    code = "KisErrOrderNotFund"
    msg = "[Kis] Order not found"


class KisErrOrderRejected(Error[Dict]):
    data: Dict
    "json message from Kis"
    code = "KisErrOrderRejected"
    msg = "[Kis] Order rejected"


class KisErrNotEnoughMargin(Error[SomethingNotEnough]):
    code = "KisErrNotEnoughMargin"
    msg = "[Kis] Not enough margin"


class KisErrNotEnoughPosition(Error[SomethingNotEnough]):
    code = "KisErrNotEnoughPosition"
    msg = "[Kis] Not enough position"
