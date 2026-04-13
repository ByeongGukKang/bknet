import asyncio
from enum import StrEnum
from typing import Callable, Union

from gufo.http import RequestMethod, Response
from orjson import loads as orjson_loads

from bknet.kis.core import KisHttpClient


class OrderSide(StrEnum):
    Buy = "B"
    "['B'] 매수"
    Sell = "S"
    "['S'] 매도"

class KrOrderKind(StrEnum):
    pass

class OrderKindKRX(KrOrderKind):
    Limit        = '00'
    "['00'] 지정가"
    Market       = '01'
    "['01'] 시장가"
    CondLimit    = '02'
    "['02'] 조건부지정가"
    BestMarket   = '03'
    "['03'] 최유리지정가"
    BestLimit    = '04'
    "['04'] 최우선지정가"
    BeforeMarket = '05'
    "['05'] 장전시간외"
    AfterMarket  = '06'
    "['06'] 장후시간외"
    SinglePriceAuction = '07'
    "['07'] 시간외단일가"
    IOCLimit     = '11'
    "['11'] IOC지정가"
    FOKLimit     = '12'
    "['12'] FOK지정가"
    IOCMarket    = '13'
    "['13'] IOC시장가"
    FOKMarket    = '14'
    "['14'] FOK시장가"
    IOCBestMarket = '15'
    "['15'] IOC최유리시장가"
    FOKBestMarket = '16'
    "['16'] FOK최유리시장가"
    MidPrice     = '21'
    "['21'] 중간가"
    StopLimit    = '22'
    "['22'] 스톱지정가 - 현재 bknet에서 지원 X"
    MidIOC       = '23'
    "['23'] 중간가IOC"
    MidFOK       = '24'
    "['24'] 중간가FOK"

class OrderKindNXT(KrOrderKind):
    Limit        = '00'
    "['00'] 지정가"
    BestMarket   = '03'
    "['03'] 최유리지정가"
    BestLimit    = '04'
    "['04'] 최우선지정가"
    IOCLimit     = '11'
    "['11'] IOC지정가"
    FOKLimit     = '12'
    "['12'] FOK지정가"
    IOCMarket    = '13'
    "['13'] IOC시장가"
    FOKMarket    = '14'
    "['14'] FOK시장가"
    IOCBestMarket = '15'
    "['15'] IOC최유리시장가"
    FOKBestMarket = '16'
    "['16'] FOK최유리시장가"
    MidPrice     = '21'
    "['21'] 중간가"
    StopLimit    = '22'
    "['22'] 스톱지정가"
    MidIOC       = '23'
    "['23'] 중간가IOC"
    MidFOK       = '24'
    "['24'] 중간가FOK"

class OrderKindSOR(KrOrderKind):
    Limit        = '00'
    "['00'] 지정가"
    Market       = '01'
    "['01'] 시장가"
    BestMarket   = '03'
    "['03'] 최유리지정가"
    BestLimit    = '04'
    "['04'] 최우선지정가"
    IOCLimit     = '11'
    "['11'] IOC지정가"
    FOKLimit     = '12'
    "['12'] FOK지정가"
    IOCMarket    = '13'
    "['13'] IOC시장가"
    FOKMarket    = '14'
    "['14'] FOK시장가"
    IOCBestMarket = '15'
    "['15'] IOC최유리시장가"
    FOKBestMarket = '16'
    "['16'] FOK최유리시장가"

class OrderAdjCanKind(StrEnum):
    Cancel = '01'
    "['01'] 취소"
    Adjust = '02'
    "['02'] 정정"

class KisKrStkTradeRuntime:

    http_client: KisHttpClient
    cano: str
    acnt_prdt_cd: str
    callbacks: dict[str, Callable[[dict], None]]
    headers: dict[str, bytes]
    _order_queue: asyncio.Queue
    _task_order_queue_process: asyncio.Task

    def __init__(
        self,
        http_client: KisHttpClient,
        cano: str,
        acnt_prdt_cd: str,
        callbacks: dict[str, Callable[[dict], None]]
    ):
        self.http_client = http_client
        self.cano = cano
        self.acnt_prdt_cd = acnt_prdt_cd
        self.callbacks = callbacks

        self.headers = {
            'content-type': b'application/json',
            'authorization': http_client.client.headers['authorization'], # type: ignore
            'appkey':    http_client.client.headers['appkey'],    # type: ignore
            'appsecret': http_client.client.headers['appsecret'], # type: ignore
            'custtype':  http_client.custtype.encode(),
        }
        
        self._order_queue = asyncio.Queue()
        self._task_order_queue_process = asyncio.create_task(self._process_orders())

    async def _process_orders(self):
        while True:
            ord_method, ord_args = await self._order_queue.get()
            if ord_method == 'order_cash':
                self.headers['tr_id'] = b'TTTC0011U' if ord_args[0] == 'S' else b'TTTC0012U'
                resp = await self.http_client.request(
                    method = RequestMethod.POST, # type: ignore
                    params = '/uapi/domestic-stock/v1/trading/order-cash',
                    body = f'{{"CANO":"{self.cano}","ACNT_PRDT_CD":"{self.acnt_prdt_cd}","PDNO":"{ord_args[2]}","ORD_DVSN":"{ord_args[1]}","ORD_QTY":"{ord_args[3]}","ORD_UNPR":"{ord_args[4]}","EXCG_ID_DVSN_CD":"{ord_args[5]}"}}'.encode(),
                    headers = self.headers
                )
            elif ord_method == 'order_adjcan':
                self.headers['tr_id'] = b'TTTC0013U'
                resp =  await self.http_client.request(
                    method = RequestMethod.POST, # type: ignore
                    params = '/uapi/domestic-stock/v1/trading/order-cash',
                    body = f'{{"CANO":"{self.cano}","ACNT_PRDT_CD":"{self.acnt_prdt_cd}","ORGN_ODNO":"{ord_args[2]}","ORD_DVSN":"{ord_args[1]}","RVSE_CNCL_DVSN_CD":"{ord_args[0]}","ORD_QTY":"{ord_args[3]}","ORD_UNPR":"{ord_args[4]}","QTY_ALL_ORD_YN":"{ord_args[5]}","EXCG_ID_DVSN_CD":"{ord_args[6]}"}}'.encode(),
                    headers = self.headers
                )
            else:
                # TODO
                raise ValueError(f'Unknown order method: {ord_method}')
            cb = self.callbacks.get(ord_method, None)
            if cb is not None:
                cb(orjson_loads(resp.content))

    def order_cash(
        self,
        side: Union[str, OrderSide],
        odrkind: Union[str, KrOrderKind],
        code: str,
        odrqty: str,
        odrprc: str,
        exgid: str = 'KRX'
    ) -> None:
        """현금 주문

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/trading/order-cash
        
        Args:
            side: 주문 방향 (매수/매도)
            odrkind: 주문 유형
            code: 종목 코드
            odrqty: 주문 수량
            odrprc: 주문 가격
            exgid: 거래소 (KRX/NXT/SOR)
        """
        self._order_queue.put_nowait(('order_cash', (side, odrkind, code, odrqty, odrprc, exgid)))

    def order_adjcan(
        self,
        adjcan: Union[str, OrderAdjCanKind],
        odrkind: Union[str, KrOrderKind],
        odrno: str,
        odrqty: str,
        odrprc: str,
        allqty: str = 'Y',
        exgid: str = 'KRX'
    ) -> None:
        """주문 정정/취소

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/trading/order-rvsecncl
        
        Args:
            adjcan: 정정/취소 구분
            odrkind: 주문 유형
            odrno: 원주문 번호
            odrqty: 주문 수량
            odrprc: 주문 가격
            allqty: 전량 주문 여부 (Y/N)
            exgid: 거래소 (KRX/NXT/SOR)
        """
        self._order_queue.put_nowait(('order_adjcan', (adjcan, odrkind, odrno, odrqty, odrprc, allqty, exgid)))


class RestKrDerivatives:

    @staticmethod
    async def kr_futures_board(http_client: KisHttpClient, mrkt_cls_code: str) -> Response:
        """국내옵션전광판_선물

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-futureoption/v1/quotations/display-board-futures

        Args:
            http_client: KisHttpClient 인스턴스
            mrkt_cls_code: 시장구분코드
                - '': KOSPI200
                - 'MKI': 미니 KOSPI200
                - 'WKM': KOSPI200위클리(월)
                - 'WKI': KOSPI200위클리(목)
                - 'KQI': KOSDAQ150
        """
        http_client.client.headers['tr_id'] = b'FHPIF05030200' # type: ignore
        return await http_client.request(
            RequestMethod.GET, # type: ignore
            params=f'/uapi/domestic-futureoption/v1/quotations/display-board-futures?FID_COND_MRKT_DIV_CODE=F&FID_COND_SCR_DIV_CODE=20503&FID_COND_MRKT_CLS_CODE={mrkt_cls_code}',
        )
    