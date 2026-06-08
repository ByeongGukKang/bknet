from typing import Dict

from bknet.error import Error, SomethingNotEnough


class HypeErrPython(Error[Exception]):
    data: Exception
    "python exception"
    code = "HypeErrPython"
    msg = "[Hype] Python exception"


class HypeErrApiLimit(Error[None]):
    data: None
    code = "HypeApiError"
    msg = "[Hype] API limit reached"


class HypeErrOrphanFilled(Error[int]):
    data: int
    "oid, order_id"
    code = "HypeErrOrphanOrderExecuted"
    msg = "[Hype] Orphan order executed"


class HypeErrOrderNotFund(Error[int]):
    data: int
    "oid, order_id"
    code = "HypeErrOrderNotFund"
    msg = "[Hype] Order not found"


class HypeErrOrderRejected(Error[str]):
    data: str
    "string message from Hype"
    code = "HypeErrOrderRejected"
    msg = "[Hype] Order rejected"


class HypeErrOrderFailed(Error[Dict]):
    data: Dict
    "json message from Hype"
    code = "HypeErrOrderFailed"
    msg = "[Hype] Order failed"


class HypeErrNotEnoughMargin(Error[SomethingNotEnough]):
    code = "HypeErrNotEnoughMargin"
    msg = "[Hype] Not enough margin"


class HypeErrNotEnoughPosition(Error[SomethingNotEnough]):
    code = "HypeErrNotEnoughPosition"
    msg = "[Hype] Not enough position"


class HypeErrorTinyOrder(Error[SomethingNotEnough]):
    code = "HypeErrorTinyOrder"
    msg = "[Hype] Tiny order"
