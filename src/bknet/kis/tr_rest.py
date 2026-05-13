import asyncio
from dataclasses import dataclass
from enum import StrEnum
from this import s
from typing import Callable, Iterable, Literal, TypeAlias, Union

from gufo.http import RequestMethod, Response
from numpy import acos
from orjson import loads as orjson_loads

from bknet.kis.core import KisHttpClient, KisWsClient
from bknet.kis.tr_websocket import WsKrStkExecAlert


class KrOrderKind(StrEnum):
    pass


class OrderKindKRX(KrOrderKind):
    Limit = "00"
    "['00'] 지정가"
    Market = "01"
    "['01'] 시장가"
    CondLimit = "02"
    "['02'] 조건부지정가"
    BestMarket = "03"
    "['03'] 최유리지정가"
    BestLimit = "04"
    "['04'] 최우선지정가"
    BeforeMarket = "05"
    "['05'] 장전시간외"
    AfterMarket = "06"
    "['06'] 장후시간외"
    SinglePriceAuction = "07"
    "['07'] 시간외단일가"
    IOCLimit = "11"
    "['11'] IOC지정가"
    FOKLimit = "12"
    "['12'] FOK지정가"
    IOCMarket = "13"
    "['13'] IOC시장가"
    FOKMarket = "14"
    "['14'] FOK시장가"
    IOCBestMarket = "15"
    "['15'] IOC최유리시장가"
    FOKBestMarket = "16"
    "['16'] FOK최유리시장가"
    MidPrice = "21"
    "['21'] 중간가"
    StopLimit = "22"
    "['22'] 스톱지정가 - 지원 X"
    MidIOC = "23"
    "['23'] 중간가IOC"
    MidFOK = "24"
    "['24'] 중간가FOK"


class OrderKindNXT(KrOrderKind):
    Limit = "00"
    "['00'] 지정가"
    BestMarket = "03"
    "['03'] 최유리지정가"
    BestLimit = "04"
    "['04'] 최우선지정가"
    IOCLimit = "11"
    "['11'] IOC지정가"
    FOKLimit = "12"
    "['12'] FOK지정가"
    IOCMarket = "13"
    "['13'] IOC시장가"
    FOKMarket = "14"
    "['14'] FOK시장가"
    IOCBestMarket = "15"
    "['15'] IOC최유리시장가"
    FOKBestMarket = "16"
    "['16'] FOK최유리시장가"
    MidPrice = "21"
    "['21'] 중간가"
    StopLimit = "22"
    "['22'] 스톱지정가"
    MidIOC = "23"
    "['23'] 중간가IOC"
    MidFOK = "24"
    "['24'] 중간가FOK"


class OrderKindSOR(KrOrderKind):
    Limit = "00"
    "['00'] 지정가"
    Market = "01"
    "['01'] 시장가"
    BestMarket = "03"
    "['03'] 최유리지정가"
    BestLimit = "04"
    "['04'] 최우선지정가"
    IOCLimit = "11"
    "['11'] IOC지정가"
    FOKLimit = "12"
    "['12'] FOK지정가"
    IOCMarket = "13"
    "['13'] IOC시장가"
    FOKMarket = "14"
    "['14'] FOK시장가"
    IOCBestMarket = "15"
    "['15'] IOC최유리시장가"
    FOKBestMarket = "16"
    "['16'] FOK최유리시장가"


class OrderAdjCanKind(StrEnum):
    Cancel = "01"
    "['01'] 취소"
    Adjust = "02"
    "['02'] 정정"


class TradeError(Exception):
    """KrStkTradeRuntime에서 발생하는 에러의 베이스 클래스"""

    pass


class OrphanExecutionError(TradeError):
    """체결 메시지 수신 시 주문 접수 메시지를 아직 수신하지 못한 경우 발생하는 에러"""

    pass


class ErrInsufficientPosition(TradeError):
    """보유 수량이 부족한 경우 발생하는 에러"""

    pass


class ErrInsufficientCash(TradeError):
    """주문 시 보유 현금이 부족한 경우 발생하는 에러"""

    pass


class ErrOrderNotFound(TradeError):
    """주문 취소 시 해당 주문을 찾을 수 없는 경우 발생하는 에러"""

    pass


MaybeError: TypeAlias = Union[None, Exception]  # Error returnable type
"""MaybeError는 KrStkTradeRuntime의 메서드에서 발생할 수 있는 에러를 나타내는 타입 별칭입니다.
- None: 에러가 발생하지 않은 경우
- Exception: 에러가 발생한 경우, Exception 또는 그 하위 클래스(TradeError)의 인스턴스가 반환됩니다.
"""


@dataclass(slots=True)
class KrStkOrder:
    locId: str
    exgId: str
    code: str
    side: Literal["B", "S", "A", "C"]  # 'B','S','A','C' (Buy, Sell, Adjust, Cancel)
    kind: Union[str, KrOrderKind]
    qty: int
    prc: int


class KisKrStkTradeRuntime:
    cano: str
    acnt_prdt_cd: str
    http_client: KisHttpClient
    on_order_cash: Callable[["KisKrStkTradeRuntime", dict], None]
    "on_order_cash(KisKrStkTradeRuntime, json)"
    on_order_cancel: Callable[["KisKrStkTradeRuntime", dict], None]
    "on_order_cancel(KisKrStkTradeRuntime, json)"
    on_order_executed: Callable[
        ["KisKrStkTradeRuntime", str, Literal["B", "S"], int, int, str], None
    ]
    "on_order_executed(KisKrStkTradeRuntime, code, odrside, exeqty, exeprc, exgcode)"
    on_error: Callable[["KisKrStkTradeRuntime", Exception], None]
    "on_error(KisKrStkTradeRuntime, Exception)"
    timeout: float = 1.0

    cash: list[int]
    "[pending_cash, active_cash]"
    posits: dict[str, list[int]]
    "code -> [pending_qty, active_qty]"

    _headers_buy: dict[str, bytes]
    _headers_sell: dict[str, bytes]
    _headers_cancel: dict[str, bytes]
    orders_pending: dict[str, KrStkOrder]
    "locId -> KrStkOrder"
    orders_active: dict[str, dict[str, KrStkOrder]]
    "code -> exgId -> KrStkOrder"
    orders_orphan: dict[str, list[tuple[int, int, str]]]
    "exgId -> list[tuple[exeqty, exeprc, exgcode]]"

    _background_tasks: set[asyncio.Task]
    _loop: asyncio.AbstractEventLoop
    _locId: int

    def __init__(
        self,
        cano: str,
        acnt_prdt_cd: str,
        hts_id: str,
        http_client: KisHttpClient,
        ws_client: KisWsClient,
        on_order_cash: Callable[["KisKrStkTradeRuntime", dict], None],
        on_order_cancel: Callable[["KisKrStkTradeRuntime", dict], None],
        on_order_executed: Callable[
            ["KisKrStkTradeRuntime", str, Literal["B", "S"], int, int, str], None
        ],
        on_error: Callable[["KisKrStkTradeRuntime", Exception], None],
        timeout: float = 1.0,
    ):
        """KIS 국내주식 실시간 주문/체결 관리

        Args:
            cano (str): 계좌번호
            acnt_prdt_cd (str): 상품유형코드
            hts_id (str): HTS 아이디
            http_client (KisHttpClient): KisHttpClient 인스턴스
            ws_client (KisWsClient): KisWsClient 인스턴스
            on_order_cash (Callable[[KisKrStkTradeRuntime, dict], None]): 현금 주문 결과 콜백, on_order_cash(self, json)
            on_order_cancel (Callable[[KisKrStkTradeRuntime, dict], None]): 주문 취소 결과 콜백, on_order_cancel(self, json)
            on_order_executed (Callable[[KisKrStkTradeRuntime, str, Literal["B", "S"], int, int, str], None]): 주문 체결 결과 콜백, on_order_executed(self, code, odrside, exeqty, exeprc, exgcode)
            on_error (Callable[[KisKrStkTradeRuntime, Exception], None]): 에러 콜백, on_error(self, Exception)
            timeout (float): HTTP 요청 타임아웃, default 1.0

        Note:
        - ws_clinet에 자동으로 WsKrStkExecAlert 등록, 체결 메시지 수신 시 on_order_executed 호출.
        - ws_clinet에 WsKrStkExecAlert 콜백을 덮어쓰지 마세요.
        """
        self.cano = cano
        self.acnt_prdt_cd = acnt_prdt_cd
        self.http_client = http_client
        self.on_order_cash = on_order_cash
        self.on_order_cancel = on_order_cancel
        self.on_order_executed = on_order_executed
        self.on_error = on_error
        self.timeout = timeout

        self.cash = [0, 0]
        self.posits = {}

        base_headers = {
            "content-type": b"application/json",
            "authorization": http_client.client.headers["authorization"],  # type: ignore
            "appkey": http_client.client.headers["appkey"],  # type: ignore
            "appsecret": http_client.client.headers["appsecret"],  # type: ignore
            "custtype": http_client.custtype.encode(),
        }

        # header types per order type, tr_id is different for buy/sell/cancel, illiminate header copying
        self._headers_buy = base_headers.copy()
        self._headers_buy["tr_id"] = b"TTTC0012U"  # 매수
        self._headers_sell = base_headers.copy()
        self._headers_sell["tr_id"] = b"TTTC0011U"  # 매도
        self._headers_cancel = base_headers.copy()
        self._headers_cancel["tr_id"] = b"TTTC0013U"  # 취소

        self.orders_pending = {}
        self.orders_active = {}
        # executed message received before order accepted message
        self.orders_orphan = {}

        self._background_tasks = set()
        self._loop = asyncio.get_event_loop()
        self._locId = 0

        def handle_WsKrStkExecAlert(_: KisWsClient, msg: list[bytes]) -> None:
            if msg[13] == b"1":  # not executed message
                return
            exgId = msg[2].decode()
            odrside = "S" if msg[4] == b"01" else "B"
            code = msg[8].decode()
            exeqty = int(msg[9])
            exeprc = int(msg[10])
            exgcode = msg[19].decode()
            err = self._handle_order_executed(
                code, odrside, exeqty, exeprc, exgId, exgcode
            )
            if err is None:
                on_order_executed(self, code, odrside, exeqty, exeprc, exgcode)
            else:
                self.on_error(self, err)

        ws_client._callbacks[WsKrStkExecAlert.TrId.encode()] = (
            WsKrStkExecAlert.TrLength,
            handle_WsKrStkExecAlert,
        )
        ws_client.subscribe(WsKrStkExecAlert.TrId, hts_id)

    def get_cash(self) -> list[int]:
        """[pending_cash, active_cash]를 반환합니다.

        Note:
            - pending_cash: 아직 체결되지 않은 주문에 예약된 현금
            - active_cash: 실제 현금 잔고
        """
        return self.cash

    def get_posit(self, code: str) -> list[int]:
        """code 종목의 [pending_qty, active_qty]를 반환합니다.

        Args:
            code: 종목 코드, 예) '252670'

        Note:
            - pending_qty: 아직 체결되지 않은 수량
            - active_qty: 체결된 수량
        """
        return self.posits.get(code, [0, 0])

    def get_active_bids(self, code: str) -> Iterable[KrStkOrder]:
        """code 종목의 활성 매수 주문들을 반환합니다.

        Args:
            code: 종목 코드, 예) '005930'

        Note:
            - 활성 주문: 접수되어 체결을 기다리는 주문
            - 값이 없는 경우 빈 tuple, 있는 경우 generator를 반환합니다. list가 필요한 경우 list()로 감싸서 사용하세요.
        """
        active_orders = self.orders_active.get(code, {})
        if not active_orders:
            return ()
        return (odr for odr in active_orders.values() if odr.side == "B")

    def get_active_asks(self, code: str) -> Iterable[KrStkOrder]:
        """code 종목의 활성 매도 주문들을 반환합니다.

        Args:
            code: 종목 코드, 예) '005930'

        Note:
            - 활성 주문: 접수되어 체결을 기다리는 주문
            - 값이 없는 경우 빈 tuple, 있는 경우 generator를 반환합니다. list가 필요한 경우 list()로 감싸서 사용하세요.
        """
        active_orders = self.orders_active.get(code, {})
        if not active_orders:
            return ()
        return (odr for odr in active_orders.values() if odr.side == "S")

    def get_pending_orders(
        self, code: str, side: Literal["B", "S", "A", "C"]
    ) -> Iterable[KrStkOrder]:
        """code 종목의 side 방향의 모든 예약 주문들을 반환합니다.

        Args:
            code: 종목 코드, 예) '005930'
            side: 주문 방향 ['B', 'S', 'A', 'C'] (Buy, Sell, Adjust, Cancel)

        Note:
            - 예약 주문: 아직 체결되지 않은 주문 (접수 대기 중이거나 접수되어 체결을 기다리는 주문)
            - 값이 없는 경우 빈 tuple, 있는 경우 generator를 반환합니다. list가 필요한 경우 list()로 감싸서 사용하세요.
        """
        if not self.orders_pending:
            return ()
        return (
            odr
            for odr in self.orders_pending.values()
            if odr.code == code and odr.side == side
        )

    def get_pending_orders_any(
        self, code: str, side: Literal["B", "S", "A", "C"]
    ) -> bool:
        """code 종목의 side 방향의 예약 주문의 존재 여부를 반환합니다.

        Args:
            code: 종목 코드, 예) '005930'
            side: 주문 방향 ['B', 'S', 'A', 'C'] (Buy, Sell, Adjust, Cancel)
        """
        if not self.orders_pending:
            return False
        return any(
            odr
            for odr in self.orders_pending.values()
            if odr.code == code and odr.side == side
        )

    async def _async_order_cash(
        self,
        code: str,
        odrside: Literal["B", "S"],
        odrkind: Union[str, KrOrderKind],
        odrqty: int,
        odrprc: int,
        exgcode: str = "KRX",
    ) -> None:
        locId = self.get_locId()
        self.orders_pending[locId] = KrStkOrder(
            locId, "", code, odrside, odrkind, odrqty, odrprc
        )
        try:
            resp = await self.http_client.request(
                method=RequestMethod.POST,  # type: ignore
                params="/uapi/domestic-stock/v1/trading/order-cash",
                body=f'{{"CANO":"{self.cano}","ACNT_PRDT_CD":"{self.acnt_prdt_cd}","PDNO":"{code}","ORD_DVSN":"{odrkind}","ORD_QTY":"{odrqty}","ORD_UNPR":"{odrprc}","EXCG_ID_DVSN_CD":"{exgcode}"}}'.encode(),
                headers=self._headers_buy if odrside == "B" else self._headers_sell,
                timeout=self.timeout,
            )
            # update order status
            pending_odr = self.orders_pending.pop(locId, None)
            if pending_odr is None:
                return
            resp_json: dict = orjson_loads(resp.content)
            rt_cd = resp_json.get("rt_cd", "")
            if rt_cd == "0":  # B/S order accepted
                exgId = resp_json["output"]["ODNO"]
                pending_odr.exgId = exgId

                self.orders_active.setdefault(code, {})[exgId] = pending_odr
                orphan_odrs = self.orders_orphan.pop(exgId, None)
                if orphan_odrs is None:
                    return
                for exeqty, exeprc, exgcode in orphan_odrs:
                    err = self._handle_order_executed(
                        code, odrside, exeqty, exeprc, exgId, exgcode
                    )
                    if err is None:
                        self.on_order_executed(
                            self, code, odrside, exeqty, exeprc, exgcode
                        )
                    else:
                        self.on_error(self, err)
            else:  # order rejected
                if odrside == "B":
                    self.cash[0] += odrqty * odrprc
                    self.posits[code][0] -= odrqty
                else:
                    self.posits[code][0] += odrqty

            self.on_order_cash(self, resp_json)
        except Exception as e:
            self.orders_pending.pop(locId, None)
            if odrside == "B":
                self.cash[0] += odrqty * odrprc
                self.posits[code][0] -= odrqty
            else:
                self.posits[code][0] += odrqty
            self.on_error(self, e)

    async def _async_order_cancel(
        self,
        odrno: str,
        code: str,
        odrqty: int,
        allqty: str = "Y",
        exgcode: str = "KRX",
    ) -> None:
        locId = self.get_locId()
        self.orders_pending[locId] = KrStkOrder(locId, "", code, "C", "00", 0, 0)
        try:
            resp = await self.http_client.request(
                method=RequestMethod.POST,  # type: ignore
                params="/uapi/domestic-stock/v1/trading/order-rvsecncl",
                body=f'{{"CANO":"{self.cano}","ACNT_PRDT_CD":"{self.acnt_prdt_cd}","ORGN_ODNO":"{odrno}","ORD_DVSN":"02","RVSE_CNCL_DVSN_CD":"{allqty}","ORD_QTY":"{odrqty}","ORD_UNPR":"0","QTY_ALL_ORD_YN":"{allqty}","EXCG_ID_DVSN_CD":"{exgcode}"}}'.encode(),
                headers=self._headers_cancel,
                timeout=self.timeout,
            )

            self.orders_pending.pop(locId, None)
            resp_json: dict = orjson_loads(resp.content)
            rt_cd = resp_json.get("rt_cd", "")
            if rt_cd == "0":  # B/S order accepted
                active_odr = self.orders_active.setdefault(code, {}).pop(odrno, None)
                if (
                    active_odr is None
                ):  # active_odr is None when order is already executed.
                    return
                if active_odr.side == "B":
                    self.cash[0] += active_odr.qty * active_odr.prc
                    self.posits[code][0] -= active_odr.qty
                else:
                    self.posits[code][0] += active_odr.qty
            else:  # order rejected
                pass

            self.on_order_cancel(self, resp_json)
        except Exception as e:
            self.orders_pending.pop(locId, None)
            self.on_error(self, e)

    def _handle_order_executed(
        self,
        code: str,
        odrside: Literal["B", "S"],
        exeqty: int,
        exeprc: int,
        exgId: str,
        exgcode: str,
    ) -> MaybeError:
        active_odr = self.orders_active.setdefault(code, {}).get(exgId, None)
        if (
            active_odr is None
        ):  # orphan execution, order accepted message is not received yet.
            orphan_odr = self.orders_orphan.get(exgId, None)
            if orphan_odr is None:
                self.orders_orphan[exgId] = [(exeqty, exeprc, exgcode)]
            else:
                orphan_odr.append((exeqty, exeprc, exgcode))
            return OrphanExecutionError(f"Orphan execution received for exgId {exgId}")

        if odrside == "B":
            posits = self.posits[code]
            posits[0] -= exeqty
            posits[1] += exeqty
            self.cash[0] += exeqty * exeprc
            self.cash[1] -= exeqty * exeprc
        elif odrside == "S":
            posits = self.posits[code]
            posits[0] += exeqty
            posits[1] -= exeqty
            self.cash[1] += exeqty * exeprc
        active_odr.qty -= exeqty
        if active_odr.qty == 0:
            del self.orders_active[code][exgId]

        return None

    def get_locId(self) -> str:
        self._locId += 1
        return str(self._locId)

    def order_cash(
        self,
        code: str,
        odrside: Literal["B", "S"],
        odrkind: Union[str, KrOrderKind],
        odrqty: int,
        odrprc: int,
        exgcode: str = "KRX",
    ) -> MaybeError:
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
        pending_pos, active_pos = self.posits.setdefault(code, [0, 0])
        if odrside == "B":
            pending_cash -= odrqty * odrprc
            pending_pos += odrqty
            if (pending_cash + active_cash) < 0:
                return ErrInsufficientCash(
                    f"code:{code}, cash: {pending_cash + active_cash} < 0"
                )
        else:
            pending_pos -= odrqty
            if (pending_pos + active_pos) < 0:
                return ErrInsufficientPosition(
                    f"code:{code}, pos: {pending_pos + active_pos} < 0"
                )
        self.cash[0] = pending_cash
        self.posits[code][0] = pending_pos

        task = self._loop.create_task(
            self._async_order_cash(code, odrside, odrkind, odrqty, odrprc, exgcode),
            # eager_start = True # type: ignore
        )
        task.add_done_callback(self._background_tasks.discard)
        self._background_tasks.add(task)
        return None

    def order_cancel(
        self,
        odrno: str,
        code: str,
        odrqty: int,
        allqty: str = "Y",
        exgcode: str = "KRX",
    ) -> MaybeError:
        """주문 취소

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/trading/order-rvsecncl

        Args:
            odrno: 원주문 번호
            code: 종목 코드
            odrqty: 주문 수량 (전량 취소 시 0 입력)
            allqty: 전량 주문 여부 ['Y', 'N'], default 'Y'
            exgcode: 거래소 ['KRX', 'NXT', 'SOR'], default 'KRX'
        """
        oodr = self.orders_active.setdefault(code, {}).get(odrno, None)
        if oodr is None:
            return ErrOrderNotFound(f"Order[{odrno}] not found")
        task = self._loop.create_task(
            self._async_order_cancel(odrno, code, odrqty, allqty, exgcode),
            # eager_start = True
        )
        task.add_done_callback(self._background_tasks.discard)
        self._background_tasks.add(task)
        return None


class RestKrStock:
    @staticmethod
    async def stk_price(
        http_client: KisHttpClient, mrkt_div_code: Literal["J", "NX", "UN"], code: str
    ) -> Response:
        """[국내주식-기본시세] 주식현재가

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/quotations/inquire-price

        Args:
            http_client: KisHttpClient 인스턴스
            mrkt_div_code: 시장구분코드 {'J': KRX, 'NX': NXT, 'UN': 통합}
            code: 종목 코드 (e.g. 005930, ETN은 6자리 앞에 Q입력 필수)
        """
        req_headers: dict[str, bytes] = http_client.client.headers.copy()  # type: ignore
        req_headers["tr_id"] = b"FHKST01010100"
        return await http_client.request(
            RequestMethod.GET,  # type: ignore
            params=f"/uapi/domestic-stock/v1/quotations/inquire-price?FID_COND_MRKT_DIV_CODE={mrkt_div_code}&FID_INPUT_ISCD={code}",
            headers=req_headers,
        )

    @staticmethod
    async def stk_hist_price(
        http_client: KisHttpClient,
        mrkt_div_code: Literal["J", "NX", "UN"],
        code: str,
        sdate: str,
        edate: str,
        period_div_code: Literal["D", "W", "M", "Y"],
        adj_prc: bool = True,
    ) -> Response:
        """[국내주식-기본시세] 주식기간별시세

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice

        Args:
            http_client: KisHttpClient 인스턴스
            mrkt_div_code: 시장구분코드 {'J': KRX, 'NX': NXT, 'UN': 통합}
            code: 종목 코드 (e.g. 005930)
            sdate: 조회 시작 일자 (YYYYMMDD)
            edate: 조회 종료 일자 (YYYYMMDD), 최대 100개
            period_div_code: 기간구분코드 {'D': 일봉, 'W': 주봉, 'M': 월봉, 'Y': 년봉}
            adj_prc: 수정주가 여부 (True: 수정주가, False: 원주가), default True
        """
        req_headers: dict[str, bytes] = http_client.client.headers.copy()  # type: ignore
        req_headers["tr_id"] = b"FHKST03010100"
        return await http_client.request(
            RequestMethod.GET,  # type: ignore
            params=f"/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice?FID_COND_MRKT_DIV_CODE={mrkt_div_code}&FID_INPUT_ISCD={code}&FID_INPUT_DATE_1={sdate}&FID_INPUT_DATE_2={edate}&FID_PERIOD_DIV_CODE={period_div_code}&FID_ORG_ADJ_PRC={'0' if adj_prc else '1'}",
            headers=req_headers,
        )

    @staticmethod
    async def etf_nav_daily(
        http_client: KisHttpClient,
        mrkt_div_code: Literal["J"],
        code: str,
        sdate: str,
        edate: str,
    ) -> Response:
        """[국내주식-기본시세] NAV 비교추이(일)

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/etfetn/v1/quotations/nav-comparison-daily-trend

        Args:
            http_client: KisHttpClient 인스턴스
            mrkt_div_code: 시장구분코드 {'J': KRX}
            code: 종목 코드 (e.g. 005930)
            sdate: 조회 시작 일자 (YYYYMMDD)
            edate: 조회 종료 일자 (YYYYMMDD), 최대 100개
        """
        req_headers: dict[str, bytes] = http_client.client.headers.copy()  # type: ignore
        req_headers["tr_id"] = b"FHPST02440200"
        return await http_client.request(
            RequestMethod.GET,  # type: ignore
            params=f"/uapi/etfetn/v1/quotations/nav-comparison-daily-trend?FID_COND_MRKT_DIV_CODE={mrkt_div_code}&FID_INPUT_ISCD={code}&FID_INPUT_DATE_1={sdate}&FID_INPUT_DATE_2={edate}",
            headers=req_headers,
        )


class RestKrDerivatives:
    @staticmethod
    async def fut_board(http_client: KisHttpClient, mrkt_cls_code: str) -> Response:
        """[국내선물옵션] 국내옵션전광판_선물

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-futureoption/v1/quotations/display-board-futures

        Args:
            http_client: KisHttpClient 인스턴스
            mrkt_cls_code: 시장구분코드 {'': KOSPI200, 'MKI': 미니KOSPI200, 'WKM': KOSPI200위클리(월), 'WKI': KOSPI200위클리(목), 'KQI': KOSDAQ150}
        """
        req_headers: dict[str, bytes] = http_client.client.headers.copy()  # type: ignore
        req_headers["tr_id"] = b"FHPIF05030200"
        return await http_client.request(
            RequestMethod.GET,  # type: ignore
            params=f"/uapi/domestic-futureoption/v1/quotations/display-board-futures?FID_COND_MRKT_DIV_CODE=F&FID_COND_SCR_DIV_CODE=20503&FID_COND_MRKT_CLS_CODE={mrkt_cls_code}",
            headers=req_headers,
        )

    @staticmethod
    async def futopt_hist_price(
        http_client: KisHttpClient,
        mrkt_div_code: str,
        code: str,
        sdate: str,
        edate: str,
        period_div_code: Literal["D", "W", "M"],
    ) -> Response:
        """[국내선물옵션] 선물옵션기간별시세

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-futureoption/v1/quotations/inquire-daily-fuopchartprice

        Args:
            http_client: KisHttpClient 인스턴스
            mrkt_div_code: 시장구분코드 {'F': 지수선물, 'O': 지수옵션, 'JF': 주식선물, 'JO': 주식옵션, 'CF': 상품선물, 'CM': 야간선물, 'EU': 야간옵션}
            code: 종목 코드 (지수선물: 6자리, 지수옵션: 9자리)
            sdate: 조회 시작 일자 (YYYYMMDD)
            edate: 조회 종료 일자 (YYYYMMDD)
            period_div_code: 기간구분코드 {'D': 일간, 'W': 주간, 'M': 월간}
        """
        req_headers: dict[str, bytes] = http_client.client.headers.copy()  # type: ignore
        req_headers["tr_id"] = b"FHKIF03020100"
        return await http_client.request(
            RequestMethod.GET,  # type: ignore
            params=f"/uapi/domestic-futureoption/v1/quotations/inquire-daily-fuopchartprice?FID_COND_MRKT_DIV_CODE={mrkt_div_code}&FID_INPUT_ISCD={code}&FID_INPUT_DATE_1={sdate}&FID_INPUT_DATE_2={edate}&FID_PERIOD_DIV_CODE={period_div_code}",
            headers=req_headers,
        )
