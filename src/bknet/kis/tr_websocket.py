class WebsocketTr:
    TrId: str
    """TR ID for the websocket message. Must be defined in subclasses."""
    TrLength: int
    """Length of the TR message in bytes. Must be defined in subclasses."""


class WsKrxStkExec(WebsocketTr):
    """국내주식체결 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0STCNT0
    """

    TrId = "H0STCNT0"
    TrLength = 46

    Code = 0
    "[0] 종목코드"
    ExecTime = 1
    "[1] 체결시간"
    ExecPrc = 2
    "[2] 체결가격"
    Ap1 = 10
    "[10] 매도호가1"
    Bp1 = 11
    "[11] 매수호가1"
    ExecQty = 12
    "[12] 체결수량"
    AcumTvol = 13
    "[13] 누적거래량"
    AcumDvol = 14
    "[14] 누적거래대금"
    SellTrdCnt = 15
    "[15] 매도체결건수"
    BuyTrdCnt = 16
    "[16] 매수체결건수"
    NetBuyTrdCnt = 17
    "[17] 순매수체결건수"
    Cttr = 18
    "[18] 체결강도"
    SellTvol = 19
    "[19] 총매도수량"
    BuyTvol = 20
    "[20] 총매수수량"
    ExecSide = 21
    "[21] 체결구분 ('1': 매수, '3': 장전, '5': 매도)"
    Aq1 = 36
    "[36] 매도호가1 잔량"
    Bq1 = 37
    "[37] 매수호가1 잔량"
    AqSum = 38
    "[38] 매도호가 잔량 합계"
    BqSum = 39
    "[39] 매수호가 잔량 합계"
    TvolTurnover = 40
    "[40] 거래량회전율"
    ViPrice = 45
    "[45] VI발동가격"


class WsKrxStkBook(WebsocketTr):
    """국내주식호가 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0STASP0
    """

    TrId = "H0STASP0"
    TrLength = 59

    Code = 0
    "[0] 종목코드"
    Ap1 = 3
    "[3] 매도호가1"
    Ap2 = 4
    "[4] 매도호가2"
    Ap3 = 5
    "[5] 매도호가3"
    Ap4 = 6
    "[6] 매도호가4"
    Ap5 = 7
    "[7] 매도호가5"
    Ap6 = 8
    "[8] 매도호가6"
    Ap7 = 9
    "[9] 매도호가7"
    Ap8 = 10
    "[10] 매도호가8"
    Ap9 = 11
    "[11] 매도호가9"
    Ap10 = 12
    "[12] 매도호가10"
    Bp1 = 13
    "[13] 매수호가1"
    Bp2 = 14
    "[14] 매수호가2"
    Bp3 = 15
    "[15] 매수호가3"
    Bp4 = 16
    "[16] 매수호가4"
    Bp5 = 17
    "[17] 매수호가5"
    Bp6 = 18
    "[18] 매수호가6"
    Bp7 = 19
    "[19] 매수호가7"
    Bp8 = 20
    "[20] 매수호가8"
    Bp9 = 21
    "[21] 매수호가9"
    Bp10 = 22
    "[22] 매수호가10"
    Aq1 = 23
    "[23] 매도호가1 잔량"
    Aq2 = 24
    "[24] 매도호가2 잔량"
    Aq3 = 25
    "[25] 매도호가3 잔량"
    Aq4 = 26
    "[26] 매도호가4 잔량"
    Aq5 = 27
    "[27] 매도호가5 잔량"
    Aq6 = 28
    "[28] 매도호가6 잔량"
    Aq7 = 29
    "[29] 매도호가7 잔량"
    Aq8 = 30
    "[30] 매도호가8 잔량"
    Aq9 = 31
    "[31] 매도호가9 잔량"
    Aq10 = 32
    "[32] 매도호가10 잔량"
    Bq1 = 33
    "[33] 매수호가1 잔량"
    Bq2 = 34
    "[34] 매수호가2 잔량"
    Bq3 = 35
    "[35] 매수호가3 잔량"
    Bq4 = 36
    "[36] 매수호가4 잔량"
    Bq5 = 37
    "[37] 매수호가5 잔량"
    Bq6 = 38
    "[38] 매수호가6 잔량"
    Bq7 = 39
    "[39] 매수호가7 잔량"
    Bq8 = 40
    "[40] 매수호가8 잔량"
    Bq9 = 41
    "[41] 매수호가9 잔량"
    Bq10 = 42
    "[42] 매수호가10 잔량"
    AqSum = 43
    "[43] 매도호가 잔량 합계"
    BqSum = 44
    "[44] 매수호가 잔량 합계"
    AcumTvol = 53
    "누적거래량"
    AqSumDiff = 54
    "총 매도호가 잔량 증감"
    BqSumDiff = 55
    "총 매수호가 잔량 증감"


class WsKrStkExecAlert(WebsocketTr):
    """국내주식 실시간체결통보

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0STCNI0"""

    TrId = "H0STCNI0"
    TrLength = 24

    CustId = 0
    "[0] 고객 ID"
    AcntNo = 1
    "[1] 계좌번호"
    OdrNo = 2
    "[2] 주문번호"
    OodrNo = 3
    "[3] 원주문번호"
    SelnByovCls = 4
    "[4] 매도/매수 구분, 01:매도, 02:매수"
    RctfCls = 5
    "[5] 정정/취소 구분, 0:정상, 1:정정, 2:취소"
    OdrKind = 6
    "[6] 주문종류"
    OdrCond = 7
    "[7] 주문조건, 0:없음, 1:IOC, 2:FOK"
    Code = 8
    "[8] 종목코드"
    ExecQty = 9
    "[9] 체결수량"
    ExecPrc = 10
    "[10] 체결가격"
    ExecTime = 11
    "[11] 체결시간"
    RfusYn = 12
    "[12] 거부여부, 0:승인, 1:거부"
    ExecYn = 13
    "[13] 체결여부, 1:주문,정정,취소,거부, 2:체결"
    AcntYn = 14
    "[14] 접수여부, 1:주문접수, 2:확인, 3:취소(IOC/FOK)"
    BrncNo = 15
    "[15] 지점번호"
    OdrQty = 16
    "[16] 주문수량"
    AcntName = 17
    "[17] 계좌명"
    OdrCondPrc = 18
    "[18] 주문조건가격"
    OdrExg = 19
    "[19] 주문거래소구분, 1:KRX, 2:NXT, 3:SOR-KRX, 4:SOR-NXT"
    PopupYn = 20
    "[20] 실시간체결창 표시여부, Y/N"
    Filler = 21
    "[21] 필러"
    CrdtCls = 22
    "[22] 신용거래구분"
    CrdtDate = 23
    "[23] 신용대출일자"
    StkName = 24
    "[24] 종목명"
    OdrPrc = 25
    "[25] 주문가격"


class WsKrxStkAfterMarketBook(WebsocketTr):
    """국내주식시간외호가 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0STOAA0
    """

    TrId = "H0STOAA0"
    TrLength = 54


class WsKrxStkAfterMarketExec(WebsocketTr):
    """국내주식시간외체결 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0STOUP0
    """

    TrId = "H0STOUP0"
    TrLength = 43


class WsAggStkExec(WebsocketTr):
    """국내주식체결 [통합]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0UNCNT0
    """

    TrId = "H0UNCNT0"
    TrLength = 46


class WsAggStkBook(WebsocketTr):
    """국내주식호가 [통합]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0UNASP0
    """

    TrId = "H0UNASP0"
    TrLength = 65


class WsNxtStkExec(WsKrxStkExec):
    """국내주식체결 [NXT]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0NXCNT0
    """

    TrId = "H0NXCNT0"
    TrLength = 46


class WsNxtStkBook(WsKrxStkBook):
    """국내주식호가 [NXT]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0NXASP0
    """

    TrId = "H0NXASP0"
    TrLength = 65


class WsKrxIdxFutBook(WebsocketTr):
    """국내지수선물호가 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0IFASP0
    """

    TrId = "H0IFASP0"
    TrLength = 38

    Code = 0
    "[0] 종목코드"
    BizTime = 1
    "[1] 영업시간"
    Ap1 = 2
    "[2] 매도호가1"
    Ap2 = 3
    "[3] 매도호가2"
    Ap3 = 4
    "[4] 매도호가3"
    Ap4 = 5
    "[5] 매도호가4"
    Ap5 = 6
    "[6] 매도호가5"
    Bp1 = 7
    "[7] 매수호가1"
    Bp2 = 8
    "[8] 매수호가2"
    Bp3 = 9
    "[9] 매수호가3"
    Bp4 = 10
    "[10] 매수호가4"
    Bp5 = 11
    "[11] 매수호가5"
    Acnt1 = 12
    "[12] 매도호가건수1"
    Acnt2 = 13
    "[13] 매도호가건수2"
    Acnt3 = 14
    "[14] 매도호가건수3"
    Acnt4 = 15
    "[15] 매도호가건수4"
    Acnt5 = 16
    "[16] 매도호가건수5"
    Bcnt1 = 17
    "[17] 매수호가건수1"
    Bcnt2 = 18
    "[18] 매수호가건수2"
    Bcnt3 = 19
    "[19] 매수호가건수3"
    Bcnt4 = 20
    "[20] 매수호가건수4"
    Bcnt5 = 21
    "[21] 매수호가건수5"
    Aq1 = 22
    "[22] 매도호가1 잔량"
    Aq2 = 23
    "[23] 매도호가2 잔량"
    Aq3 = 24
    "[24] 매도호가3 잔량"
    Aq4 = 25
    "[25] 매도호가4 잔량"
    Aq5 = 26
    "[26] 매도호가5 잔량"
    Bq1 = 27
    "[27] 매수호가1 잔량"
    Bq2 = 28
    "[28] 매수호가2 잔량"
    Bq3 = 29
    "[29] 매수호가3 잔량"
    Bq4 = 30
    "[30] 매수호가4 잔량"
    Bq5 = 31
    "[31] 매수호가5 잔량"
    AcntSum = 32
    "[32] 매도호가건수 합계"
    BcntSum = 33
    "[33] 매수호가건수 합계"
    AqSum = 34
    "[34] 매도호가 잔량 합계"
    BqSum = 35
    "[35] 매수호가 잔량 합계"
    AqSumDiff = 36
    "총 매도호가 잔량 증감"
    BqSumDiff = 37
    "총 매수호가 잔량 증감"


class WsKrxIdxFutExec(WebsocketTr):
    """국내지수선물체결 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0IFCNT0
    """

    TrId = "H0IFCNT0"
    TrLength = 50

    Code = 0
    "[0] 종목코드"
    BizTime = 1
    "[1] 영업시간"
    ExecPrc = 5
    "[5] 체결가격"
    ExecQty = 9
    "[9] 체결수량"
    AcumTvol = 10
    "[10] 누적거래량"
    AcumDvol = 11
    "[11] 누적거래대금"
    Ap1 = 34
    "[34] 매도호가1"
    Bp1 = 35
    "[35] 매수호가1"
    Aq1 = 36
    "[36] 매도호가1 잔량"
    Bq1 = 37
    "[37] 매수호가1 잔량"
    SellTrdCnt = 38
    "[38] 매도체결건수"
    BuyTrdCnt = 39
    "[39] 매수체결건수"
    NetBuyTrdCnt = 40
    "[40] 순매수체결건수"
    SellTvol = 41
    "[41] 총매도수량"
    BuyTvol = 42
    "[42] 총매수수량"
    AqSum = 43
    "[43] 매도호가 잔량 합계"
    BqSum = 44
    "[44] 매수호가 잔량 합계"


class WsKrxComFutBook(WsKrxIdxFutBook):
    """국내상품선물호가 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0CFASP0
    """

    TrId = "H0CFASP0"
    TrLength = 38


class WsKrxComFutExec(WebsocketTr):
    """국내상품선물체결 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0CFCNT0
    """

    TrId = "H0CFCNT0"
    TrLength = 50

    Code = 0
    "[0] 선물단축종목코드"
    BsopHour = 1
    "[1] 영업시간"
    FutsPrdyVrss = 2
    "[2] 선물전일대비"
    PrdyVrssSign = 3
    "[3] 선물전일대비부호"
    FutsPrdyCtrt = 4
    "[4] 선물전일대비율"
    CntgPrc = 5
    "[5] 체결가격"
    Open = 6
    "[6] 시가"
    High = 7
    "[7] 고가"
    Low = 8
    "[8] 저가"
    CntgQty = 9
    "[9] 체결수량"
    AcmlQty = 10
    "[10] 누적체결수량"
    AcmlDvol = 11
    "[11] 누적거래대금"
    HtsThpr = 12
    "[12] HTS이론가"
    Basis = 13
    "[13] 베이시스"
    Dprt = 14
    "[14] 괴리율"
    NmscFctnStplPrc = 15
    "[15] 근월물약정가"
    FmscFctnStplPrc = 16
    "[16] 원월물약정가"
    SpredPrc = 17
    "[17] 스프레드"
    HtsOtstStplQty = 18
    "[18] HTS미결제약정수량"
    OtstStplQtyIcdc = 19
    "[19] 미결제약정수량증감"
    OprcHour = 20
    "[20] 시가시간"
    OprcVrssPrprSign = 21
    "[21] 시가대비부호"
    OprcVrssPrpr = 22
    "[22] 시가대비"
    HgprHour = 23
    "[23] 고가시간"
    HgprVrssPrprSign = 24
    "[24] 고가대비부호"
    HgprVrssPrpr = 25
    "[25] 고가대비"
    LwprHour = 26
    "[26] 저가시간"
    LwprVrssPrprSign = 27
    "[27] 저가대비부호"
    LwprVrssPrpr = 28
    "[28] 저가대비"
    ShnuRate = 29
    "[29] 매수비율"
    Cttr = 30
    "[30] 체결강도"
    Esdg = 31
    "[31] 괴리도"
    OtstStplRgbfQtyIcdc = 32
    "[32] 미결제약정직전수량증감"
    ThprBasis = 33
    "[33] 이론베이시스"
    Ap1 = 34
    "[34] 매도호가1"
    Bp1 = 35
    "[35] 매수호가1"
    Aq1 = 36
    "[36] 매도호가1잔량"
    Bq1 = 37
    "[37] 매수호가1잔량"
    SellTrdCnt = 38
    "[38] 매도체결건수"
    BuyTrdCnt = 39
    "[39] 매수체결건수"
    NetBuyTrdCnt = 40
    "[40] 순매수체결건수"
    SellTvol = 41
    "[41] 총매도수량"
    BuyTvol = 42
    "[42] 총매수수량"
    AqSum = 43
    "[43] 총매도호가잔량"
    BqSum = 44
    "[44] 총매수호가잔량"
    PrdyVolVrssAcmlVolRate = 45
    "[45] 전일거래량대비등락률"
    DscsBlTrAcmlQty = 46
    "[46] 협의대량거래량"
    DynmMxpr = 47
    "[47] 실시간상한가"
    DynmLlam = 48
    "[48] 실시간하한가"
    DynmPrcLimtYn = 49
    "[49] 실시간가격제한구분"


class WsKrxStkFutBook(WsKrxIdxFutBook):
    """국내주식선물호가 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0ZFASP0
    """

    TrId = "H0ZFASP0"
    TrLength = 68

    Code = 0
    "[0] 선물단축종목코드"

    Ap1 = 2
    "[2] 매수호가1"
    Ap2 = 3
    "[3] 매수호가2"
    Ap3 = 4
    "[4] 매수호가3"
    Ap4 = 5
    "[5] 매수호가4"
    Ap5 = 6
    "[6] 매수호가5"
    Ap6 = 7
    "[7] 매수호가6"
    Ap7 = 8
    "[8] 매수호가7"
    Ap8 = 9
    "[9] 매수호가8"
    Ap9 = 10
    "[10] 매수호가9"
    Ap10 = 11
    "[11] 매수호가10"
    Bp1 = 12
    "[12] 매수호가1"
    Bp2 = 13
    "[13] 매수호가2"
    Bp3 = 14
    "[14] 매수호가3"
    Bp4 = 15
    "[15] 매수호가4"
    Bp5 = 16
    "[16] 매수호가5"
    Bp6 = 17
    "[17] 매수호가6"
    Bp7 = 18
    "[18] 매수호가7"
    Bp8 = 19
    "[19] 매수호가8"
    Bp9 = 20
    "[20] 매수호가9"
    Bp10 = 21
    "[21] 매수호가10"
    Acnt1 = 22
    "[22] 매도호가건수1"
    Acnt2 = 23
    "[23] 매도호가건수2"
    Acnt3 = 24
    "[24] 매도호가건수3"
    Acnt4 = 25
    "[25] 매도호가건수4"
    Acnt5 = 26
    "[26] 매도호가건수5"
    Acnt6 = 27
    "[27] 매도호가건수6"
    Acnt7 = 28
    "[28] 매도호가건수7"
    Acnt8 = 29
    "[29] 매도호가건수8"
    Acnt9 = 30
    "[30] 매도호가건수9"
    Acnt10 = 31
    "[31] 매도호가건수10"
    Bcnt1 = 32
    "[32] 매수호가건수1"
    Bcnt2 = 33
    "[33] 매수호가건수2"
    Bcnt3 = 34
    "[34] 매수호가건수3"
    Bcnt4 = 35
    "[35] 매수호가건수4"
    Bcnt5 = 36
    "[36] 매수호가건수5"
    Bcnt6 = 37
    "[37] 매수호가건수6"
    Bcnt7 = 38
    "[38] 매수호가건수7"
    Bcnt8 = 39
    "[39] 매수호가건수8"
    Bcnt9 = 40
    "[40] 매수호가건수9"
    Bcnt10 = 41
    "[41] 매수호가건수10"
    Aq1 = 42
    "[42] 매수호가잔량1"
    Aq2 = 43
    "[43] 매수호가잔량2"
    Aq3 = 44
    "[44] 매수호가잔량3"
    Aq4 = 45
    "[45] 매수호가잔량4"
    Aq5 = 46
    "[46] 매수호가잔량5"
    Aq6 = 47
    "[47] 매수호가잔량6"
    Aq7 = 48
    "[48] 매수호가잔량7"
    Aq8 = 49
    "[49] 매수호가잔량8"
    Aq9 = 50
    "[50] 매수호가잔량9"
    Aq10 = 51
    "[51] 매수호가잔량10"
    Bq1 = 52
    "[52] 매도호가잔량1"
    Bq2 = 53
    "[53] 매도호가잔량2"
    Bq3 = 54
    "[54] 매도호가잔량3"
    Bq4 = 55
    "[55] 매도호가잔량4"
    Bq5 = 56
    "[56] 매도호가잔량5"
    Bq6 = 57
    "[57] 매도호가잔량6"
    Bq7 = 58
    "[58] 매도호가잔량7"
    Bq8 = 59
    "[59] 매도호가잔량8"
    Bq9 = 60
    "[60] 매도호가잔량9"
    Bq10 = 61
    "[61] 매도호가잔량10"
    AcntSum = 62
    "[62] 매도호가잔량합계"
    BcntSum = 63
    "[63] 매수호가잔량합계"
    AqSum = 64
    "[64] 매수호가잔량합계"
    BqSum = 65
    "[65] 매도호가잔량합계"
    AqSumDiff = 66
    "[66] 총매도호가잔량증감"
    BqSumDiff = 67
    "[67] 총매수호가잔량증감"


class WsKrxStkFutExec(WebsocketTr):
    """국내주식선물체결 [KRX]

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0ZFCNT0
    """

    TrId = "H0ZFCNT0"
    TrLength = 49

    Code = 0
    "[0] 선물단축종목코드"
    BsopHour = 1
    "[1] 영업시간"
    CntgPrc = 2
    "[2] 체결가격"
    PrdyVrssSign = 3
    "[3] 전일대비부호"
    PrdyVrss = 4
    "[4] 전일대비"
    FutsPrdyCtrt = 5
    "[5] 선물전일대비율"
    Open = 6
    "[6] 시가"
    High = 7
    "[7] 고가"
    Low = 8
    "[8] 저가"
    CntgQty = 9
    "[9] 체결수량"
    AcmlQty = 10
    "[10] 누적체결수량"
    AcmlDvol = 11
    "[11] 누적거래대금"
    HtsThpr = 12
    "[12] HTS이론가"
    Basis = 13
    "[13] 베이시스"
    Dprt = 14
    "[14] 괴리율"
    NmscFctnStplPrc = 15
    "[15] 근월물약정가"
    FmscFctnStplPrc = 16
    "[16] 원월물약정가"
    SpredPrc = 17
    "[17] 스프레드"
    HtsOtstStplQty = 18
    "[18] HTS미결제약정수량"
    OtstStplQtyIcdc = 19
    "[19] 미결제약정수량증감"
    OprcHour = 20
    "[20] 시가시간"
    OprcVrssPrprSign = 21
    "[21] 시가대비부호"
    OprcVrssPrpr = 22
    "[22] 시가대비"
    HgprHour = 23
    "[23] 고가시간"
    HgprVrssPrprSign = 24
    "[24] 고가대비부호"
    HgprVrssPrpr = 25
    "[25] 고가대비"
    LwprHour = 26
    "[26] 저가시간"
    LwprVrssPrprSign = 27
    "[27] 저가대비부호"
    LwprVrssPrpr = 28
    "[28] 저가대비"
    ShnuRate = 29
    "[29] 매수비율"
    Cttr = 30
    "[30] 체결강도"
    Esdg = 31
    "[31] 괴리도"
    OtstStplRgbfQtyIcdc = 32
    "[32] 미결제약정직전수량증감"
    ThprBasis = 33
    "[33] 이론베이시스"
    Ap1 = 34
    "[34] 매도호가1"
    Bp1 = 35
    "[35] 매수호가1"
    Aq1 = 36
    "[36] 매도호가1잔량"
    Bq1 = 37
    "[37] 매수호가1잔량"
    SellTrdCnt = 38
    "[38] 매도체결건수"
    BuyTrdCnt = 39
    "[39] 매수체결건수"
    NetBuyTrdCnt = 40
    "[40] 순매수체결건수"
    SellTvol = 41
    "[41] 총매도수량"
    BuyTvol = 42
    "[42] 총매수수량"
    AqSum = 43
    "[43] 총매도호가잔량"
    BqSum = 44
    "[44] 총매수호가잔량"
    PrdyVolVrssAcmlVolRate = 45
    "[45] 전일거래량대비등락률"
    DynmMxpr = 46
    "[46] 실시간상한가"
    DynmLlam = 47
    "[47] 실시간하한가"
    DynmPrcLimtYn = 48
    "[48] 실시간가격제한구분"


class WsKrxDevExecAlert(WebsocketTr):
    """국내선물옵션 실시간체결통보

    https://apiportal.koreainvestment.com/apiservice-apiservice?/tryitout/H0IFCNI0
    """

    TrId = "H0IFCNI0"
    TrLength = 22

    CustId = 0
    "[0] 고객 ID"
    AcntNo = 1
    "[1] 계좌번호"
    OderNo = 2
    "[2] 주문번호"
    OoderNo = 3
    "[3] 원주문번호"
    SelnByovCls = 4
    "[4] 매도/매수 구분, 01:매도, 02:매수"
    RctfCls = 5
    "[5] 정정/취소 구분, 0:정상, 1:정정, 2:취소"
    OdrKind2 = 6
    "[6] 주문종류2 L:주문접수통보, 0:체결통보"
    StckShrnIscd = 7
    "[7] 단축종목코드"
    CntgQty = 8
    "[8] 체결수량"
    CntgUnPr = 9
    "[9] 체결단가"
    StckCntgHour = 10
    "[10] 체결시간"
    RfusYn = 11
    "[11] 거부여부, 0:승인, 1:거부"
    CntgYn = 12
    "[12] 체결여부, 1:주문,정정,취소,거부, 2:체결"
    AcntYn = 13
    "[13] 접수여부, 1:주문접수, 2:확인, 3:취소(IOC/FOK)"
    BrncNo = 14
    "[14] 지점번호"
    OderQty = 15
    "[15] 주문수량"
    AcntName = 16
    "[16] 계좌명"
    CntgIsNm = 17
    "[17] 체결종목명"
    OderCond = 18
    "[18] 주문조건, 0:없음, 1:IOC, 2:FOK"
    OrdGrp = 19
    "[19] 주문그룹ID"
    OrdGrpSeq = 20
    "[20] 주문그룹SEQ"
    OrderPrc = 21
    "[21] 주문가격"
