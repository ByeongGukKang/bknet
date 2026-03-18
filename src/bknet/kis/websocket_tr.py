

class WebsocketTr:
    Trid: str
    TrLength: int

class KrxStkExec(WebsocketTr):
    """국내주식체결 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0STCNT0
    """
    Trid = 'H0STCNT0'
    TrLength = 46
    
class KrxStkBook(WebsocketTr):
    """국내주식호가 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0STASP0
    """
    Trid = 'H0STASP0'
    TrLength = 59

class KrxStkAfterMarketBook(WebsocketTr):
    """국내주식시간외호가 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0STOAA0
    """
    Trid = 'H0STOAA0'
    TrLength = 54

class KrxStkAfterMarketExec(WebsocketTr):
    """국내주식시간외체결 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0STOUP0
    """
    Trid = 'H0STOUP0'
    TrLength = 43

class AggStkExec(WebsocketTr):
    """국내주식체결 [통합]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0UNCNT0
    """
    Trid = 'H0UNCNT0'
    TrLength = 46

class AggStkBook(WebsocketTr):
    """국내주식호가 [통합]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0UNASP0
    """
    Trid = 'H0UNASP0'
    TrLength = 65

class NxtStkExec(WebsocketTr):
    """국내주식체결 [NXT]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0NXCNT0
    """
    Trid = 'H0NXCNT0'
    TrLength = 46

class NxtStkBook(WebsocketTr):
    """국내주식호가 [NXT]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0NXASP0
    """
    Trid = 'H0NXASP0'
    TrLength = 65

class KrxIdxFutBook(WebsocketTr):
    """국내지수선물호가 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0IFASP0
    """
    Trid = 'H0IFASP0'
    TrLength = 38

class KrxIdxFutExec(WebsocketTr):
    """국내지수선물체결 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0IFCNT0
    """
    Trid = 'H0IFCNT0'
    TrLength = 50