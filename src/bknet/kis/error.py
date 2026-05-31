from typing import Dict

from bknet.error import Error, SomethingNotEnough


class KisErrPython(Error[Exception]):
    code = "KisErrPython"
    msg = "[Kis] Python exception"


class KisErrApiLimit(Error[None]):
    code = "KisErrApiLimit"
    msg = "[Kis] API limit reached"


class KisErrOrphanOrderExecuted(Error[str]):
    code = "KisErrOrphanOrderExecuted"
    msg = "[Kis] Orphan order executed"
    data: str
    "order_id"


class KisErrOrderNotFund(Error[str]):
    code = "KisErrOrderNotFund"
    msg = "[Kis] Order not found"
    data: str
    "order_id"


class KisErrOrderRejected(Error[Dict]):
    code = "KisErrOrderRejected"
    msg = "[Kis] Order rejected"
    data: Dict
    "json message from Kis"


class KisErrNotEnoughMargin(Error[SomethingNotEnough]):
    code = "KisErrNotEnoughMargin"
    msg = "[Kis] Not enough margin"


class KisErrNotEnoughPosition(Error[SomethingNotEnough]):
    code = "KisErrNotEnoughPosition"
    msg = "[Kis] Not enough position"
