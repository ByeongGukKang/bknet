
class WebsocketTr:
    TrId: str
    """TR ID for the websocket message. Must be defined in subclasses."""
    TrLength: int
    """Length of the TR message in bytes. Must be defined in subclasses."""

class WsKrxStkExec(WebsocketTr):
    """국내주식체결 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0STCNT0
    """
    TrId = 'H0STCNT0'
    TrLength = 46

    Code = 0 
    "종목코드"
    ExecTime = 1
    "체결시간"
    ExecPrc = 2
    "체결가격"
    Ap1 = 10
    "매도호가1"
    Bp1 = 11
    "매수호가1"
    ExecQty = 12
    "체결수량"
    AcumTvol = 13
    "누적거래량"
    AcumDvol = 14
    "누적거래대금"
    SellTrdCnt = 15
    "매도체결건수"
    BuyTrdCnt = 16
    "매수체결건수"
    NetBuyTrdCnt = 17
    "순매수체결건수"
    Cttr = 18
    "체결강도"
    SellTvol = 19
    "총매도수량"
    BuyTvol = 20
    "총매수수량"
    ExecSide = 21
    "체결구분 ('1': 매수, '3': 장전, '5': 매도)"
    Aq1 = 36
    "매도호가1 잔량"
    Bq1 = 37
    "매수호가1 잔량"
    AqSum = 38
    "매도호가 잔량 합계"
    BqSum = 39
    "매수호가 잔량 합계"
    TvolTurnover = 40
    "거래량회전율"
    ViPrice = 45
    "VI발동가격"
    
class WsKrxStkBook(WebsocketTr):
    """국내주식호가 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0STASP0
    """
    TrId = 'H0STASP0'
    TrLength = 59

    Code = 0
    Ap1 = 3
    Ap2 = 4
    Ap3 = 5
    Ap4 = 6
    Ap5 = 7
    Ap6 = 8
    Ap7 = 9
    Ap8 = 10
    Ap9 = 11
    Ap10 = 12
    Bp1 = 13
    Bp2 = 14
    Bp3 = 15
    Bp4 = 16
    Bp5 = 17
    Bp6 = 18
    Bp7 = 19
    Bp8 = 20
    Bp9 = 21
    Bp10 = 22
    Aq1 = 23
    Aq2 = 24
    Aq3 = 25
    Aq4 = 26
    Aq5 = 27
    Aq6 = 28
    Aq7 = 29
    Aq8 = 30
    Aq9 = 31
    Aq10 = 32
    Bq1 = 33
    Bq2 = 34
    Bq3 = 35
    Bq4 = 36
    Bq5 = 37
    Bq6 = 38
    Bq7 = 39
    Bq8 = 40
    Bq9 = 41
    Bq10 = 42
    AqSum = 43
    BqSum = 44
    AcumTvol = 53
    "누적거래량"
    AqSumDiff = 54
    "총 매도호가 잔량 증감"
    BqSumDiff = 55
    "총 매수호가 잔량 증감"

class KrxStkAfterMarketBook(WebsocketTr):
    """국내주식시간외호가 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0STOAA0
    """
    TrId = 'H0STOAA0'
    TrLength = 54

class KrxStkAfterMarketExec(WebsocketTr):
    """국내주식시간외체결 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0STOUP0
    """
    TrId = 'H0STOUP0'
    TrLength = 43

class AggStkExec(WebsocketTr):
    """국내주식체결 [통합]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0UNCNT0
    """
    TrId = 'H0UNCNT0'
    TrLength = 46

class AggStkBook(WebsocketTr):
    """국내주식호가 [통합]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0UNASP0
    """
    TrId = 'H0UNASP0'
    TrLength = 65

class NxtStkExec(WebsocketTr):
    """국내주식체결 [NXT]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0NXCNT0
    """
    TrId = 'H0NXCNT0'
    TrLength = 46

class NxtStkBook(WebsocketTr):
    """국내주식호가 [NXT]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0NXASP0
    """
    TrId = 'H0NXASP0'
    TrLength = 65

class WsKrxIdxFutBook(WebsocketTr):
    """국내지수선물호가 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0IFASP0
    """
    TrId = 'H0IFASP0'
    TrLength = 38

    Code = 0
    BizTime = 1
    Ap1 = 2
    Ap2 = 3
    Ap3 = 4
    Ap4 = 5
    Ap5 = 6
    Bp1 = 7
    Bp2 = 8
    Bp3 = 9
    Bp4 = 10
    Bp5 = 11
    Acnt1 = 12
    Acnt2 = 13
    Acnt3 = 14
    Acnt4 = 15
    Acnt5 = 16
    Bcnt1 = 17
    Bcnt2 = 18
    Bcnt3 = 19
    Bcnt4 = 20
    Bcnt5 = 21
    Aq1 = 22
    Aq2 = 23
    Aq3 = 24
    Aq4 = 25
    Aq5 = 26
    Bq1 = 27
    Bq2 = 28
    Bq3 = 29
    Bq4 = 30
    Bq5 = 31
    AcntSum = 32
    BcntSum = 33
    AqSum = 34
    BqSum = 35
    AqSumDiff = 36
    BqSumDiff = 37

class WsKrxIdxFutExec(WebsocketTr):
    """국내지수선물체결 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0IFCNT0
    """
    TrId = 'H0IFCNT0'
    TrLength = 50

    Code = 0
    BizTime = 1
    ExecPrc = 5
    ExecQty = 9
    AcumTvol = 10
    AcumDvol = 11
    Ap1 = 34
    Bp1 = 35
    Aq1 = 36
    Bq1 = 37
    SellTrdCnt = 38
    BuyTrdCnt = 39
    NetBuyTrdCnt = 40
    SellTvol = 41
    BuyTvol = 42
    AqSum = 43
    BqSum = 44
