from typing import Union

from gufo.http import RequestMethod, Response

from bknet.kis.core import KisHttpClient



class OrderSide:
    Buy = "B"
    "매수"
    Sell = "S"
    "매도"

class OrderType:
    pass

class OrderTypeKRX(OrderType):
    Limit        = '00'
    "지정가"
    Market       = '01'
    "시장가"
    CondLimit    = '02'
    "조건부지정가"
    BestMarket   = '03'
    "최유리지정가"
    BestLimit    = '04'
    "최우선지정가"
    BeforeMarket = '05'
    "장전시간외"
    AfterMarket  = '06'
    "장후시간외"
    SinglePriceAuction = '07'
    "시간외단일가"
    IOCLimit     = '11'
    "IOC지정가"
    FOKLimit     = '12'
    "FOK지정가"
    IOCMarket    = '13'
    "IOC시장가"
    FOKMarket    = '14'
    "FOK시장가"
    IOCBestMarket = '15'
    "IOC최유리시장가"
    FOKBestMarket = '16'
    "FOK최유리시장가"
    MidPrice     = '21'
    "중간가"
    StopLimit    = '22'
    "스톱지정가 - 현재 bknet에서 지원 X"
    MidIOC       = '23'
    "중간가IOC"
    MidFOK       = '24'
    "중간가FOK"

class OrderTypeNXT(OrderType):
    Limit        = '00'
    "지정가"
    BestMarket   = '03'
    "최유리지정가"
    BestLimit    = '04'
    "최우선지정가"
    IOCLimit     = '11'
    "IOC지정가"
    FOKLimit     = '12'
    "FOK지정가"
    IOCMarket    = '13'
    "IOC시장가"
    FOKMarket    = '14'
    "FOK시장가"
    IOCBestMarket = '15'
    "IOC최유리시장가"
    FOKBestMarket = '16'
    "FOK최유리시장가"
    MidPrice     = '21'
    "중간가"
    StopLimit    = '22'
    "스톱지정가"
    MidIOC       = '23'
    "중간가IOC"
    MidFOK       = '24'
    "중간가FOK"

class OrderTypeSOR(OrderType):
    Limit        = '00'
    "지정가"
    Market       = '01'
    "시장가"
    BestMarket   = '03'
    "최유리지정가"
    BestLimit    = '04'
    "최우선지정가"
    IOCLimit     = '11'
    "IOC지정가"
    FOKLimit     = '12'
    "FOK지정가"
    IOCMarket    = '13'
    "IOC시장가"
    FOKMarket    = '14'
    "FOK시장가"
    IOCBestMarket = '15'
    "IOC최유리시장가"
    FOKBestMarket = '16'
    "FOK최유리시장가"

class OrderAdjCanType:
    Cancel = '01'
    "취소"
    Adjust = '02'
    "정정"

class RestKrStockOrder:

    def __init__(
        self,
        http_client: KisHttpClient,
        cano: str,
        acnt_prdt_cd: str,
    ):
        self.http_client = http_client
        self.cano = cano
        self.acnt_prdt_cd = acnt_prdt_cd
        self.custtype_binary = http_client.custtype.encode()

    async def order_cash(
        self,
        side: Union[str, OrderSide],
        ordtype: Union[str, OrderType],
        code: str,
        ordqty: str,
        ordprc: str,
        exgid: str = 'KRX'
    ) -> Response:
        """현금 주문

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/trading/order-cash
        
        Args:
            side: 주문 방향 (매수/매도)
            ordtype: 주문 유형
            code: 종목 코드
            ordqty: 주문 수량
            ordprc: 주문 가격
            exgid: 거래소 (KRX/NXT/SOR)
        """
        return await self.http_client.request(
            method = RequestMethod.POST, # type: ignore
            params = '/uapi/domestic-stock/v1/trading/order-cash',
            body = f'{{"CANO":"{self.cano}","ACNT_PRDT_CD":"{self.acnt_prdt_cd}","PDNO":"{code}","ORD_DVSN":"{ordtype}","ORD_QTY":"{ordqty}","ORD_UNPR":"{ordprc}","EXCG_ID_DVSN_CD":"{exgid}"}}'.encode(),
            headers = {'tr_id': b'TTTC0011U' if side == OrderSide.Sell else b'TTTC0012U', 'custtype': self.custtype_binary}
        )

    async def order_adjcan(
        self,
        adjcan: Union[str, OrderAdjCanType],
        ordtype: Union[str, OrderType],
        ordno: str,
        ordqty: str,
        ordprc: str,
        allqty: str = 'Y',
        exgid: str = 'KRX'
    ) -> Response:
        """주문 정정/취소

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/trading/order-rvsecncl
        
        Args:
            adjcan: 정정/취소 구분
            ordtype: 주문 유형
            ordno: 원주문 번호
            ordqty: 주문 수량
            ordprc: 주문 가격
            allqty: 전량 주문 여부 (Y/N)
            exgid: 거래소 (KRX/NXT/SOR)
        """
        return await self.http_client.request(
            method = RequestMethod.POST, # type: ignore
            params = '/uapi/domestic-stock/v1/trading/order-cash',
            body = f'{{"CANO":"{self.cano}","ACNT_PRDT_CD":"{self.acnt_prdt_cd}","ORGN_ODNO":"{ordno}","ORD_DVSN":"{ordtype}","RVSE_CNCL_DVSN_CD":"{adjcan}","ORD_QTY":"{ordqty}","ORD_UNPR":"{ordprc}","QTY_ALL_ORD_YN":"{allqty}","EXCG_ID_DVSN_CD":"{exgid}"}}'.encode(),
            headers = {'tr_id': b'TTTC0013U', 'custtype': self.custtype_binary}
        )
    

class RestKrDerivatives:

    @staticmethod
    async def kr_futures_board(http_client: KisHttpClient, mrkt_cls_code: str) -> Response:
        """국내옵션전광판_선물

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-futureoption/v1/quotations/display-board-futures

        Args:
            http_client: KisHttpClient 인스턴스
            mrkt_cls_code: 시장구분코드
                - 공백: KOSPI200
                - MKI: 미니 KOSPI200
                - WKM: KOSPI200위클리(월)
                - WKI: KOSPI200위클리(목)
                - KQI: KOSDAQ150
        """
        http_client.client.headers['tr_id'] = b'FHPIF05030200' # type: ignore
        return await http_client.request(
            RequestMethod.GET, # type: ignore
            params=f'/uapi/domestic-futureoption/v1/quotations/display-board-futures?FID_COND_MRKT_DIV_CODE=F&FID_COND_SCR_DIV_CODE=20503&FID_COND_MRKT_CLS_CODE={mrkt_cls_code}',
        )
    