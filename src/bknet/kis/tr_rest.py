import asyncio
from dataclasses import dataclass
from enum import StrEnum
from pyexpat.errors import codes
from typing import Callable, Literal, TypeAlias, Union

from gufo.http import RequestMethod, Response
from orjson import loads as orjson_loads

from bknet.kis.core import KisHttpClient

MaybeError: TypeAlias = Union[None, Exception] # Error returnable type

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

@dataclass(slots=True)
class KrStkOrder:   
    locId: str
    exgId: str
    code: str
    side: Literal['B', 'S', 'A', 'C'] # 'B','S','A','C' (Buy, Sell, Adjust, Cancel)
    kind: KrOrderKind
    qty: int
    prc: int

class KisKrStkTradeRuntime:

    http_client: KisHttpClient
    cano: str
    acnt_prdt_cd: str
    callbacks: dict[str, Callable[[dict], None]]
    headers: dict[str, bytes]

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

        self.cash: list[int] = [0, 0] # [pending_cash, active_cash]
        "[pending_cash, active_cash]"
        self.posits: dict[str, list[int]] = {code: [0, 0] for code in codes}
        "code -> [pending_qty, active_qty]"

        self._orders_pending: dict[str, KrStkOrder] = {}
        "locId -> KrStkOrder"
        self._orders_active: dict[str, dict[str, KrStkOrder]] = {code: {} for code in codes} 
        "code -> exgId -> KrStkOrder"
        # executed message received before order accepted message
        self._orders_orphan: dict[str, list[tuple[int, int]]] = {} 
        "exgId -> list[tuple[exeqty, exeprc]]"

        self._loop = asyncio.get_event_loop()
        self._locId = 0

    async def _async_order_cash(
        self,
        code: str,
        odrside: Literal['B', 'S'],
        odrkind: Union[str, KrOrderKind],
        odrqty: int,
        odrprc: int,
        exgcode: str = 'KRX'
    ) -> None:
        locId = self.get_locId()
        self._orders_pending[locId] = KrStkOrder(locId, '', code, odrside, odrkind, odrqty, odrprc) # type: ignore
        self.headers['tr_id'] = b'TTTC0011U' if odrside == 'S' else b'TTTC0012U' # TODO Is this safe?
        resp = await self.http_client.request(
            method = RequestMethod.POST, # type: ignore
            params = '/uapi/domestic-stock/v1/trading/order-cash',
            body = f'{{"CANO":"{self.cano}","ACNT_PRDT_CD":"{self.acnt_prdt_cd}","PDNO":"{code}","ORD_DVSN":"{odrkind}","ORD_QTY":"{odrqty}","ORD_UNPR":"{odrprc}","EXCG_ID_DVSN_CD":"{exgcode}"}}'.encode(),
            headers = self.headers
        )

        # update order status
        pending_odr = self._orders_pending.pop(locId)
        resp_json: dict = orjson_loads(resp.content)
        rt_cd = resp_json.get('rt_cd', '')
        if rt_cd == '0': # B/S order accepted
            exgId = resp_json['output']['ODNO']
            pending_odr.exgId = exgId
            self._orders_active[code][exgId] = pending_odr
            orphan_odrs = self._orders_orphan.pop(exgId, None)
            if orphan_odrs is None:
                return
            for exeqty, exeprc in orphan_odrs:
                self.handle_order_executed(code, odrside, exeqty, exeprc, exgId)
        else: # order rejected
            if odrside == 'B':
                self.cash[0] += odrqty * odrprc
                self.posits[code][0] -= odrqty
            else:
                self.posits[code][0] += odrqty

        # callback
        cb = self.callbacks.get('order_cash', None)
        if cb is None:
            return
        cb(resp_json)

    async def _async_order_cancel(
        self,
        odrno: str,
        code: str,
        allqty: str = 'Y',
        exgcode: str = 'KRX'
    ) -> None: # TODO return type
        locId = self.get_locId()
        self._orders_pending[locId] = KrStkOrder(locId, '', code, 'C', '00', 0, 0) # type: ignore
        self.headers['tr_id'] = b'TTTC0013U'
        resp = await self.http_client.request(
            method = RequestMethod.POST, # type: ignore
            params = '/uapi/domestic-stock/v1/trading/order-rvsecncl',
            body = f'{{"CANO":"{self.cano}","ACNT_PRDT_CD":"{self.acnt_prdt_cd}","ORGN_ODNO":"{odrno}","ORD_DVSN":"02","RVSE_CNCL_DVSN_CD":"{allqty}","ORD_QTY":"0","ORD_UNPR":"0","QTY_ALL_ORD_YN":"{allqty}","EXCG_ID_DVSN_CD":"{exgcode}"}}'.encode(),
            headers = self.headers
        )

        self._orders_pending.pop(locId)
        resp_json: dict = orjson_loads(resp.content)
        rt_cd = resp_json.get('rt_cd', '')
        if rt_cd == '0': # B/S order accepted
            active_odr = self._orders_active.get(code, {}).pop(odrno, None)
            if active_odr is None: # active_odr is None when order is already executed.
                return
            if active_odr.side == 'B':
                self.cash[0] += active_odr.qty * active_odr.prc
                self.posits[code][0] -= active_odr.qty
            else:
                self.posits[code][0] += active_odr.qty
        else: # order rejected
            pass

        cb = self.callbacks.get('order_cancel', None)
        if cb is None:
            return
        cb(resp_json)

    def get_locId(self) -> str:
        self._locId += 1
        return str(self._locId)

    def order_cash(
        self,
        code: str,
        odrside: Literal['B', 'S'],
        odrkind: Union[str, KrOrderKind],
        odrqty: int,
        odrprc: int,
        exgcode: str = 'KRX'
    ) -> MaybeError: # TODO return type
        """현금 주문

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/trading/order-cash
        
        Args:
            code: 종목 코드
            odrside: 주문 방향 ['B', 'S']
            odrkind: 주문 유형
            odrqty: 주문 수량
            odrprc: 주문 가격
            exgcode: 거래소 ['KRX', 'NXT', 'SOR'], default 'KRX'
        """
        pending_cash, active_cash = self.cash
        pending_pos, active_pos = self.posits.get(code, [0, 0])
        if odrside == 'B':
            pending_cash -= odrqty * odrprc
            pending_pos += odrqty
        else:
            pending_pos -= odrqty
        if (pending_pos + active_pos) < 0:
            return Exception('Not enough position to sell')
        if (pending_cash + active_cash) < 0:
            return Exception('Not enough cash to buy')
        self.cash[0] = pending_cash
        self.posits[code][0] = pending_pos

        self._loop.create_task(self._async_order_cash(code, odrside, odrkind, odrqty, odrprc, exgcode))
        return None

    def order_cancel(
        self,
        odrno: str,
        code: str,
        allqty: str = 'Y',
        exgcode: str = 'KRX'
    ) -> MaybeError:
        """주문 취소

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/trading/order-rvsecncl
        
        Args:
            odrno: 원주문 번호
            code: 종목 코드
            allqty: 전량 주문 여부 ['Y', 'N'], default 'Y'
            exgcode: 거래소 ['KRX', 'NXT', 'SOR'], default 'KRX'
        """
        oodr = self._orders_active.get(code, {}).get(odrno, None)
        if oodr is None:
            return Exception(f'Order[{odrno}] not found')
        self._loop.create_task(self._async_order_cancel(odrno, code, allqty, exgcode))
        return None

    def handle_order_executed(
        self,
        code: str,
        odrside: Literal['B', 'S'],
        exeqty: int,
        exeprc: int,
        exgId: str,
    ) -> None:
        active_odr = self._orders_active.get(code, {}).get(exgId, None)
        if active_odr is None: # orphan execution, order accepted message is not received yet.
            orphan_odr = self._orders_orphan.get(exgId, None)
            if orphan_odr is None:
                self._orders_orphan[exgId] = [(exeqty, exeprc)]
            else:
                orphan_odr.append((exeqty, exeprc))
            return
        
        if odrside == 'B':
            posits = self.posits[code]
            posits[0] -= exeqty
            posits[1] += exeqty
            self.cash[0] += exeqty * exeprc
            self.cash[1] -= exeqty * exeprc      
        elif odrside == 'S':
            posits = self.posits[code]
            posits[0] += exeqty
            posits[1] -= exeqty
            self.cash[1] += exeqty * exeprc
        active_odr.qty -= exeqty 
        if active_odr.qty == 0:
            del self._orders_active[code][exgId]


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
    