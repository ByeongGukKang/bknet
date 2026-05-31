from typing import Dict

from bknet.error import Error, SomethingNotEnough


class HypeErrPython(Error[Exception]):
    code = "HypeErrPython"
    msg = "[Hype] Python exception"


class HypeErrApiLimit(Error[None]):
    code = "HypeApiError"
    msg = "[Hype] API limit reached"


class HypeErrOrphanOrderExecuted(Error[str]):
    code = "HypeErrOrphanOrderExecuted"
    msg = "[Hype] Orphan order executed"
    data: str
    "order_id"


class HypeErrOrderNotFund(Error[str]):
    code = "HypeErrOrderNotFund"
    msg = "[Hype] Order not found"
    data: str
    "order_id"


class HypeErrOrderRejected(Error[str]):
    code = "HypeErrOrderRejected"
    msg = "[Hype] Order rejected"
    data: str
    "str message from Hype"


class HypeErrOrderFailed(Error[Dict]):
    code = "HypeErrOrderFailed"
    msg = "[Hype] Order failed"
    data: Dict
    "json message from Hype"


class HypeErrNotEnoughMargin(Error[SomethingNotEnough]):
    code = "HypeErrNotEnoughMargin"
    msg = "[Hype] Not enough margin"


class HypeErrNotEnoughPosition(Error[SomethingNotEnough]):
    code = "HypeErrNotEnoughPosition"
    msg = "[Hype] Not enough position"
