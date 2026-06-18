import asyncio
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Callable, Iterable, Literal, Optional, Self, Union

from gufo.http import RequestMethod
from orjson import loads as orjson_loads

from bknet.error import Error
from bknet.kis.client import KisHttpClient, KisWsClient
from bknet.kis.error import (
    KisErrApiLimit,
    KisErrNotEnoughMargin,
    KisErrNotEnoughPosition,
    KisErrOrderNotFund,
    KisErrOrderRejected,
    KisErrOrphanOrderOccured,
    KisErrPython,
)
from bknet.kis.tr_websocket import WsKrStkExecAlert, WsKrxDevExecAlert
from bknet.src import ForceAsyncNew, MemoryPool, async_schedule


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


@dataclass(slots=True)
class KrStkOrder:
    omsid: int = 0
    oid: str = ""
    code: str = ""
    # 'B','S','A','C' (Buy, Sell, Adjust, Cancel)
    side: Literal["", "B", "S", "A", "C"] = ""
    kind: Union[str, KrOrderKind] = ""
    qty: int = 0
    prc: int = 0
    status: Literal["", "onwire", "onwait", "partial"] = ""

    def init(
        self,
        omsid: int,
        code: str,
        side: Literal["B", "S", "A", "C"],
        kind: Union[str, KrOrderKind],
        qty: int,
        prc: int,
    ) -> None:
        self.omsid = omsid
        self.oid = ""
        self.code = code
        self.side = side
        self.kind = kind
        self.qty = qty
        self.prc = prc
        self.status = "onwire"


@dataclass(slots=True)
class KrDevOrder:
    omsid: int = 0
    oid: str = ""
    code: str = ""
    # 'B','S','A','C' (Buy, Sell, Adjust, Cancel)
    side: Literal["", "B", "S", "A", "C"] = ""
    kind: Literal["", "01", "02", "03", "04", "10", "11", "12", "13", "14", "15"] = ""
    qty: int = 0
    prc: Decimal = Decimal(0)
    leverage: Decimal = Decimal(1.0)
    status: Literal["", "onwire", "onwait", "partial"] = ""

    def init(
        self,
        omsid: int,
        code: str,
        side: Literal["B", "S", "A", "C"],
        kind: Literal["01", "02", "03", "04", "10", "11", "12", "13", "14", "15"],
        qty: int,
        prc: Decimal,
        leverage: Decimal,
    ) -> None:
        self.omsid = omsid
        self.oid = ""
        self.code = code
        self.side = side
        self.kind = kind
        self.qty = qty
        self.prc = prc
        self.leverage = leverage
        self.status = "onwire"


@dataclass(slots=True, frozen=True)
class KrDevMarginInfo:
    initMrgRatio: Decimal
    mainMrgRatio: Decimal
    multipler: Decimal
    mrgPerUnit: int


class _KisKrStkOMS_depreciated(ForceAsyncNew):
    cano: str
    acnt_prdt_cd: str
    hts_id: str
    http_client: KisHttpClient
    on_order_cash: Callable[[Self, dict], None]
    "on_order_cash(KisKrStkOMS, json)"
    on_order_cancel: Callable[[Self, dict], None]
    "on_order_cancel(KisKrStkOMS, json)"
    on_order_executed: Callable[
        [Self, str, Literal["B", "S", "A", "C"], int, int, str], None
    ]
    "on_order_executed(KisKrStkOMS, code, odrside, exeqty, exeprc, exgcode)"
    on_error: Callable[[Self, Error], None]
    "on_error(KisKrStkOMS, Error)"
    timeout: float = 1.0

    cash: list[float]
    "[pending_cash, active_cash]"
    posits: dict[str, list[int]]
    "code -> [pending_qty, active_qty]"

    _headers_buy: dict[str, bytes]
    _headers_sell: dict[str, bytes]
    _headers_cancel: dict[str, bytes]
    orders_onwire: dict[str | int, KrStkOrder]
    "omsid -> KrStkOrder, or odrno -> KrStkOrder for cancel orders"
    orders_onwait: dict[str, dict[str, KrStkOrder]]
    "code -> exgId -> KrStkOrder"
    orders_orphan: dict[str, list[tuple[int, int, str]]]
    "exgId -> list[tuple[exeqty, exeprc, exgcode]]"

    bg_tasks: set[asyncio.Task]
    "Share the same background task set with KisHttpClient to run background tasks such as order cash/cancel requests and periodic updates."
    _loop: asyncio.AbstractEventLoop
    _omsid: int
    _mempool: MemoryPool[KrStkOrder]

    @classmethod
    async def New(
        cls,
        cano: str,
        acnt_prdt_cd: str,
        hts_id: str,
        http_client: KisHttpClient,
        ws_client: KisWsClient,
        on_order_cash: Callable[[Self, dict], None],
        on_order_cancel: Callable[[Self, dict], None],
        on_order_executed: Callable[
            [Self, str, Literal["B", "S", "A", "C"], int, int, str],
            None,
        ],
        on_error: Callable[[Self, Error], None],
        timeout: float = 1.0,
        mempool_size: int = 128,
    ) -> Self:
        """KIS 국내주식 실시간 주문/체결 관리

        Args:
            cano (str): 계좌번호
            acnt_prdt_cd (str): 상품유형코드
            hts_id (str): HTS 아이디
            http_client (KisHttpClient): KisHttpClient 인스턴스
            ws_client (KisWsClient): KisWsClient 인스턴스
            on_order_cash (Callable[[KisKrStkOMS, dict], None]): 현금 주문 결과 콜백, on_order_cash(self, json)
            on_order_cancel (Callable[[KisKrStkOMS, dict], None]): 주문 취소 결과 콜백, on_order_cancel(self, json)
            on_order_executed (Callable[[KisKrStkOMS, str, Literal["B", "S"], int, int, str], None]): 주문 체결 결과 콜백, on_order_executed(self, code, odrside, exeqty, exeprc, exgcode)
            on_error (Callable[[KisKrStkOMS, Error], None]): 에러 콜백, on_error(self, Error)
            timeout (float): HTTP 요청 타임아웃, default 1.0
            mempool_size (int): 메모리 풀 크기, default 128

        Note:
        - ws_clinet에 자동으로 WsKrStkExecAlert 등록, 체결 메시지 수신 시 on_order_executed 호출.
        - ws_clinet에 WsKrStkExecAlert 콜백을 덮어쓰지 마세요.
        """
        instance = cls(cls._prevented)
        instance.cano = cano
        instance.acnt_prdt_cd = acnt_prdt_cd
        instance.hts_id = hts_id

        instance.http_client = http_client

        instance.on_order_cash = on_order_cash
        instance.on_order_cancel = on_order_cancel
        instance.on_order_executed = on_order_executed
        instance.on_error = on_error
        instance.timeout = timeout

        instance.cash = [0.0, 0.0]
        instance.posits = {}

        base_headers = {
            "content-type": b"application/json",
            "authorization": http_client.client.headers["authorization"],  # type: ignore
            "appkey": http_client.client.headers["appkey"],  # type: ignore
            "appsecret": http_client.client.headers["appsecret"],  # type: ignore
            "custtype": http_client.custtype.encode(),
        }

        # header types per order type, tr_id is different for buy/sell/cancel, illiminate header copying
        instance._headers_buy = base_headers.copy()
        instance._headers_buy["tr_id"] = b"TTTC0012U"  # Buy
        instance._headers_sell = base_headers.copy()
        instance._headers_sell["tr_id"] = b"TTTC0011U"  # Sell
        instance._headers_cancel = base_headers.copy()
        instance._headers_cancel["tr_id"] = b"TTTC0013U"  # Adjust & Cancel

        instance.orders_onwire = {}
        instance.orders_onwait = {}
        instance.orders_orphan = {}  # executed message received before order accepted message

        instance.bg_tasks = http_client.bg_tasks
        instance._loop = asyncio.get_running_loop()
        instance._omsid = 0

        instance._mempool = MemoryPool(KrStkOrder, mempool_size)

        # Bind WsKrStkExecAlert handler to ws_client
        instance.bind_ws_client(ws_client, hts_id)

        # Initialize cash and positions
        await instance.update_cash()
        await instance.update_posits()

        return instance

    def _get_omsid(self) -> int:
        self._omsid += 1
        return self._omsid

    def _handle_orphan_orders(self, exgId: str, code: str, odrside: Literal["B", "S"]):
        orphan_odrs = self.orders_orphan.pop(exgId, None)
        if orphan_odrs is None:
            return
        for exeqty, exeprc, exgcode in orphan_odrs:
            err = self._handle_order_executed(
                code, odrside, exeqty, exeprc, exgId, exgcode
            )
            if err is None:
                self.on_order_executed(self, code, odrside, exeqty, exeprc, exgcode)
            else:
                self.on_error(self, err)

    async def _async_order_cash(
        self,
        omsid: int,
        code: str,
        odrside: Literal["B", "S"],
        odrkind: Union[str, KrOrderKind],
        odrqty: int,
        odrprc: int,
        exgcode: str = "KRX",
    ) -> None:
        try:
            resp = await self.http_client.request_unsafe(
                method=RequestMethod.POST,  # type: ignore
                params="/uapi/domestic-stock/v1/trading/order-cash",
                body=f'{{"CANO":"{self.cano}","ACNT_PRDT_CD":"{self.acnt_prdt_cd}","PDNO":"{code}","ORD_DVSN":"{odrkind}","ORD_QTY":"{odrqty}","ORD_UNPR":"{odrprc}","EXCG_ID_DVSN_CD":"{exgcode}"}}'.encode(),
                headers=self._headers_buy if odrside == "B" else self._headers_sell,
            )
            # update order status
            pending_odr = self.orders_onwire.pop(omsid, None)
            if pending_odr is None:
                return
            resp_json: dict = orjson_loads(resp.content)
            rt_cd = resp_json.get("rt_cd", "")
            if rt_cd == "0":  # B/S order accepted
                exgId = resp_json["output"]["ODNO"]
                pending_odr.oid = exgId
                pending_odr.status = "onwait"
                self.orders_onwait.setdefault(code, {})[exgId] = pending_odr
                self._handle_orphan_orders(exgId, code, odrside)
            else:  # order rejected
                self._mempool.free(pending_odr)
                if odrside == "B":
                    self.cash[0] += odrqty * odrprc
                    self.posits[code][0] -= odrqty
                else:
                    self.posits[code][0] += odrqty
                self.on_error(self, KisErrOrderRejected(resp_json))

            self.on_order_cash(self, resp_json)
        except Exception as e:
            pending_odr = self.orders_onwire.pop(omsid, None)
            if pending_odr is not None:
                self._mempool.free(pending_odr)
            if odrside == "B":
                self.cash[0] += odrqty * odrprc
                self.posits[code][0] -= odrqty
            else:
                self.posits[code][0] += odrqty
            self.on_error(self, KisErrPython(e))

    async def _async_order_cancel(
        self,
        odrno: str,
        odrqty: int,
        allqty: str = "Y",
        exgcode: str = "KRX",
    ) -> None:
        try:
            resp = await self.http_client.request_unsafe(
                method=RequestMethod.POST,  # type: ignore
                params="/uapi/domestic-stock/v1/trading/order-rvsecncl",
                body=f'{{"CANO":"{self.cano}","ACNT_PRDT_CD":"{self.acnt_prdt_cd}","ORGN_ODNO":"{odrno}","ORD_DVSN":"00","RVSE_CNCL_DVSN_CD":"02","ORD_QTY":"{odrqty}","ORD_UNPR":"0","QTY_ALL_ORD_YN":"{allqty}","EXCG_ID_DVSN_CD":"{exgcode}"}}'.encode(),
                headers=self._headers_cancel,
            )
            resp_json: dict = orjson_loads(resp.content)
            rt_cd = resp_json.get("rt_cd", "")
            if rt_cd == "0":  # Cancel order accepted
                pass
            else:  # order rejected
                pending_odr = self.orders_onwire.pop(odrno, None)
                if pending_odr is not None:
                    self._mempool.free(pending_odr)
                self.on_error(self, KisErrOrderRejected(resp_json))
            self.on_order_cancel(self, resp_json)
        except Exception as e:
            pending_odr = self.orders_onwire.pop(odrno, None)
            if pending_odr is not None:
                self._mempool.free(pending_odr)
            self.on_error(self, KisErrPython(e))

    def _handle_order_executed(
        self,
        code: str,
        odrside: Literal["B", "S"],
        exeqty: int,
        exeprc: int,
        exgId: str,
        exgcode: str,
    ) -> Optional[KisErrOrphanOrderOccured]:
        onwait_odr = self.orders_onwait.setdefault(code, {}).get(exgId, None)
        if (
            onwait_odr is None
        ):  # orphan execution, order accepted message is not received yet.
            orphan_odr = self.orders_orphan.get(exgId, None)
            if orphan_odr is None:
                self.orders_orphan[exgId] = [(exeqty, exeprc, exgcode)]
            else:
                orphan_odr.append((exeqty, exeprc, exgcode))
            return KisErrOrphanOrderOccured(exgId)

        posits = self.posits[code]
        if odrside == "B":
            posits[0] -= exeqty
            posits[1] += exeqty
            self.cash[0] += exeqty * onwait_odr.prc  # refund pending cash
            self.cash[1] -= exeqty * exeprc
        else:  # "S"
            posits[0] += exeqty
            posits[1] -= exeqty
            self.cash[1] += exeqty * exeprc * 0.998  # 매도대금 재사용비율?
        onwait_odr.qty -= exeqty
        if onwait_odr.qty == 0:
            del self.orders_onwait[code][exgId]
            self._mempool.free(onwait_odr)
        else:
            onwait_odr.status = "partial"

        return None

    def _handle_order_cancelled(
        self,
        code: str,
        odrside: Literal["B", "S"],
        exeqty: int,
        odrprc: int,
        exgId: str,
    ) -> Optional[KisErrOrderNotFund]:
        onwait_odr = self.orders_onwait.setdefault(code, {}).get(exgId, None)
        if onwait_odr is None:
            return KisErrOrderNotFund(exgId)

        posits = self.posits.setdefault(code, [0, 0])
        if odrside == "B":
            posits[0] -= exeqty
            self.cash[0] += exeqty * odrprc
        else:
            posits[0] += exeqty

        onwait_odr.qty -= exeqty
        if onwait_odr.qty == 0:
            del self.orders_onwait[code][exgId]
            self._mempool.free(onwait_odr)
        else:
            onwait_odr.status = "partial"

        return None

    def bind_ws_client(self, ws_client: KisWsClient, hts_id: str):
        def _handle_WsKrStkExecAlert(_: KisWsClient, msg: list[bytes]) -> None:
            if msg[14] == b"1":  # Order Received message
                return

            exgId = msg[2].decode()
            odrside = "S" if msg[4] == b"01" else "B"
            code = msg[8].decode()
            exeqty = int(msg[9])
            exgcode = msg[19].decode()
            if msg[5] == b"2":  # Cancel message
                # Original order id
                oexgId = msg[3].decode()
                # remove pending cancel order
                odr = self.orders_onwire.pop(oexgId, None)
                if odr is None:
                    self.on_error(self, KisErrOrderNotFund(oexgId))
                    return
                odrprc = odr.prc
                self._mempool.free(odr)
                err = self._handle_order_cancelled(
                    code, odrside, exeqty, odrprc, oexgId
                )
                if err is None:
                    self.on_order_executed(self, code, "C", exeqty, odrprc, exgcode)
                else:
                    self.on_error(self, err)
            elif msg[5] == b"1":  # Adjust message
                pass
            else:  # execution message
                exeprc = int(msg[10])
                err = self._handle_order_executed(
                    code, odrside, exeqty, exeprc, exgId, exgcode
                )
                if err is None:
                    self.on_order_executed(self, code, odrside, exeqty, exeprc, exgcode)
                else:
                    self.on_error(self, err)

        ws_client._callbacks[WsKrStkExecAlert.TrId.encode()] = (
            WsKrStkExecAlert.TrLength,
            _handle_WsKrStkExecAlert,
        )
        ws_client.subscribe(WsKrStkExecAlert.TrId, hts_id)

    def update_all(self):
        """현금 잔고와 모든 종목의 잔고를 조회하여 self.cash와 self.posits를 업데이트합니다."""
        async_schedule(self.update_cash, self.bg_tasks)
        async_schedule(self.update_posits, self.bg_tasks)

    async def update_cash(self):
        """현재 현금 잔고를 조회하여 self.cash를 업데이트합니다."""
        req_header = self.http_client.client.headers.copy()  # type: ignore
        req_header["tr_id"] = b"TTTC0869R"
        try:
            resp = await self.http_client.request(
                method=RequestMethod.GET,  # type: ignore
                params=f"/uapi/domestic-stock/v1/trading/intgr-margin?CANO={self.cano}&ACNT_PRDT_CD={self.acnt_prdt_cd}&CMA_EVLU_AMT_ICLD_YN=N&WCRC_FRCR_DVSN_CD=02&FWEX_CTRT_FRCR_DVSN_CD=02",
                headers=req_header,
                timeout=self.timeout,
            )
            resp_json = orjson_loads(resp.content)
            if resp_json.get("rt_cd", "") != "0":
                raise Exception(resp_json)
            self.cash[1] = float(resp_json["output"]["stck_cash_ord_psbl_amt"])
        except Exception as e:
            self.on_error(self, KisErrPython(e))

    async def update_posits(self):
        """현재 잔고를 조회하여 self.posits를 업데이트합니다."""
        req_header = self.http_client.client.headers.copy()  # type: ignore
        req_header["tr_id"] = b"TTTC8434R"
        try:
            ctx_area_fk100 = ""
            ctx_area_nk100 = ""
            while True:
                resp = await self.http_client.request(
                    method=RequestMethod.GET,  # type: ignore
                    params=f"/uapi/domestic-stock/v1/trading/inquire-balance?CANO={self.cano}&ACNT_PRDT_CD={self.acnt_prdt_cd}&AFHR_FLPR_YN=N&INQR_DVSN=01&UNPR_DVSN=01&FUND_STTL_ICLD_YN=N&FNCG_AMT_AUTO_RDPT_YN=N&PRCS_DVSN=00&CTX_AREA_FK100={ctx_area_fk100}&CTX_AREA_NK100={ctx_area_nk100}",
                    headers=req_header,
                    timeout=self.timeout,
                )
                resp_json = orjson_loads(resp.content)
                if resp_json.get("rt_cd", "") != "0":
                    raise Exception(resp_json)
                ctx_area_fk100 = resp_json.get("ctx_area_fk100", "")
                ctx_area_nk100 = resp_json.get("ctx_area_nk100", "")
                posit_msgs = resp_json.get("output1", [])
                for posit_msg in posit_msgs:
                    code = posit_msg["pdno"]
                    curr_pos = self.posits.get(code, None)
                    if curr_pos is None:
                        self.posits[code] = [0, int(posit_msg["hldg_qty"])]
                    else:
                        self.posits[code][1] = int(posit_msg["hldg_qty"])
                if ctx_area_nk100.strip() == "":
                    break
        except Exception as e:
            self.on_error(self, KisErrPython(e))
        req_header["tr_id"] = b"TTTC0084R"
        try:
            ctx_area_fk100 = ""
            ctx_area_nk100 = ""
            while True:
                resp = await self.http_client.request(
                    method=RequestMethod.GET,  # type: ignore
                    params=f"/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl?CANO={self.cano}&ACNT_PRDT_CD={self.acnt_prdt_cd}&CTX_AREA_FK100={ctx_area_fk100}&CTX_AREA_NK100={ctx_area_nk100}&INQR_DVSN_1=0&INQR_DVSN_2=0",
                    headers=req_header,
                    timeout=self.timeout,
                )
                resp_json = orjson_loads(resp.content)
                if resp_json.get("rt_cd", "") != "0":
                    raise Exception(resp_json)
                ctx_area_fk100 = resp_json.get("ctx_area_fk100", "")
                ctx_area_nk100 = resp_json.get("ctx_area_nk100", "")
                posit_msgs = resp_json.get("output1", [])
                for posit_msg in posit_msgs:
                    code = posit_msg["pdno"]
                    curr_pos = self.posits.get(code, None)
                    existing_qty = int(posit_msg["psbl_qty"]) * (
                        1 if posit_msg["sll_buy_dvsn_cd"] == "02" else -1
                    )
                    if curr_pos is None:
                        self.posits[code] = [existing_qty, 0]
                    else:
                        self.posits[code][0] += existing_qty
                if ctx_area_nk100.strip() == "":
                    break
        except Exception as e:
            self.on_error(self, KisErrPython(e))

    def get_cash(self) -> list[float]:
        """[pending_cash, active_cash]를 반환합니다.

        Note:
            - pending_cash: 아직 체결되지 않은 주문에 예약된 현금
            - active_cash: 실제 현금 잔고
        """
        return self.cash

    def get_posit(self, code: str) -> list[int]:
        """code 종목의 [pending_qty, active_qty]를 반환합니다.

        Args:
            code: 종목 코드, 예) '005930'

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
        active_orders = self.orders_onwait.get(code, {})
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
        active_orders = self.orders_onwait.get(code, {})
        if not active_orders:
            return ()
        return (odr for odr in active_orders.values() if odr.side == "S")

    def get_pending_orders(
        self, code: str, side: Literal["B", "S", "A", "C"]
    ) -> Iterable[KrStkOrder]:
        """code 종목의 side 방향의 모든 OnWire/OnWait 주문들을 반환합니다.

        Args:
            code: 종목 코드, 예) '005930'
            side: 주문 방향 ['B', 'S', 'A', 'C'] (Buy, Sell, Adjust, Cancel)

        Note:
            - 예약 주문: 아직 체결되지 않은 주문 (접수 대기 중이거나 접수되어 체결을 기다리는 주문)
            - 값이 없는 경우 빈 tuple, 있는 경우 generator를 반환합니다. list가 필요한 경우 list()로 감싸서 사용하세요.
        """
        if not self.orders_onwire:
            return ()
        return (
            odr
            for odr in self.orders_onwire.values()
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
        if not self.orders_onwire:
            return False
        return any(
            odr
            for odr in self.orders_onwire.values()
            if odr.code == code and odr.side == side
        )

    def order_cash(
        self,
        code: str,
        odrside: Literal["B", "S"],
        odrkind: Union[str, KrOrderKind],
        odrqty: int,
        odrprc: int,
        exgcode: str = "KRX",
    ) -> None:
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
        try:
            self.http_client._api_limit_queue.get_nowait()
        except asyncio.QueueEmpty:
            self.on_error(self, KisErrApiLimit(None))
            return

        pending_cash, active_cash = self.cash
        pending_pos, active_pos = self.posits.setdefault(code, [0, 0])
        if odrside == "B":
            pending_cash -= odrqty * odrprc
            pending_pos += odrqty
            if (pending_cash + active_cash) < 0:
                self.http_client._api_limit_queue.put_nowait(None)  # API token rollback
                self.on_error(
                    self,
                    KisErrNotEnoughMargin(
                        {
                            "action": "order_cash",
                            "current": active_cash,
                            "required": odrqty * odrprc,
                        }
                    ),
                )
                return
        else:
            pending_pos -= odrqty
            if (pending_pos + active_pos) < 0:
                self.http_client._api_limit_queue.put_nowait(None)  # API token rollback
                self.on_error(
                    self,
                    KisErrNotEnoughPosition(
                        {
                            "action": "order_cash",
                            "current": active_pos,
                            "required": odrqty,
                        }
                    ),
                )
                return
        self.cash[0] = pending_cash
        self.posits[code][0] = pending_pos

        # Allocate pending order
        omsid = self._get_omsid()
        odr = self._mempool.alloc()
        odr.init(self._get_omsid(), code, odrside, odrkind, odrqty, odrprc)
        self.orders_onwire[omsid] = odr

        task = self._loop.create_task(
            self._async_order_cash(
                omsid, code, odrside, odrkind, odrqty, odrprc, exgcode
            ),
            # eager_start = True # type: ignore
        )
        self.bg_tasks.add(task)
        task.add_done_callback(self.bg_tasks.discard)

    def order_cancel(
        self,
        odrno: str,
        code: str,
        odrqty: int,
        allqty: str = "Y",
        exgcode: str = "KRX",
    ) -> None:
        """주문 취소

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/trading/order-rvsecncl

        Args:
            odrno: 원주문 번호
            code: 종목 코드
            odrqty: 주문 수량 (전량 취소 시 0 입력)
            allqty: 전량 주문 여부 ['Y', 'N'], default 'Y'
            exgcode: 거래소 ['KRX', 'NXT', 'SOR'], default 'KRX'
        """
        oodr = self.orders_onwait.setdefault(code, {}).get(odrno, None)
        if oodr is None:
            self.on_error(self, KisErrOrderNotFund(odrno))
            return

        # If cancel is ongoing, return immediately to prevent duplicate cancel attempts.
        if odrno in self.orders_onwire:
            return

        try:
            self.http_client._api_limit_queue.get_nowait()
        except asyncio.QueueEmpty:
            self.on_error(self, KisErrApiLimit(None))
            return

        # Allocate pending cancel,
        # Cancel orders are special, key for orders_pending is not omsid, but the original order number(odrno)
        odr = self._mempool.alloc()
        odr.init(self._get_omsid(), code, "C", "00", odrqty, oodr.prc)
        self.orders_onwire[odrno] = odr

        task = self._loop.create_task(
            self._async_order_cancel(odrno, odrqty, allqty, exgcode),
            # eager_start = True
        )
        self.bg_tasks.add(task)
        task.add_done_callback(self.bg_tasks.discard)


class KisKrStkOMS(ForceAsyncNew):
    ## user inputs
    # KisKrStkOMS specific inputs
    cano: str
    acnt_prdt_cd: str
    hts_id: str
    # shared
    http_client: KisHttpClient
    on_order_filled: Callable[[Self, str, bool, int, int], None]
    "on_order_filled(KisKrStkOMS, code, isBuy, qty, prc)"
    on_order_canceled: Callable[[Self, str, bool, int, int], None]
    "on_order_canceled(KisKrStkOMS, code, isBuy, qty, prc)"
    on_order_adjusted: Callable[[Self, KrStkOrder], None]
    "on_order_adjusted(KisKrStkOMS, KrStkOrder)"
    on_error: Callable[[Self, Error], None]
    "on_error(KisKrStkOMS, Error)"
    timeout: float = 1.0

    ## internal states
    # KisKrStkOMS specific states
    _headers_buy: dict[str, bytes]
    _headers_sell: dict[str, bytes]
    _headers_cancel: dict[str, bytes]
    # shared
    margin: list[int]
    "[pending_margin, active_margin]"
    posits: dict[str, list[int]]
    "code -> [pending_qty, active_qty]"
    orders_onwire: dict[str | int, KrStkOrder]
    "omsid -> KrStkOrder, oOid for cancel orders"
    orders_onwait: dict[str, dict[str, KrStkOrder]]
    "code -> oid -> KrStkOrder"
    orders_orphan: dict[str, list[tuple[Literal["B", "S", "A", "C"], int, int]]]
    "oid -> list[tuple[side, qty, prc]]"
    # order management
    _omsid: int
    _mempool: MemoryPool[KrStkOrder]
    # async management
    _loop: asyncio.AbstractEventLoop
    bg_tasks: set[asyncio.Task]

    @classmethod
    async def New(
        cls,
        cano: str,
        acnt_prdt_cd: str,
        hts_id: str,
        http_client: KisHttpClient,
        ws_client: KisWsClient,
        on_order_filled: Callable[[Self, str, bool, int, int], None],
        on_order_canceled: Callable[[Self, str, bool, int, int], None],
        on_error: Callable[[Self, Error], None],
        timeout: float = 1.0,
        mempool_size: int = 128,
    ) -> Self:
        """KIS 국내주식 실시간 주문/체결 관리

        Args:
            cano (str): 계좌번호
            acnt_prdt_cd (str): 상품유형코드
            hts_id (str): HTS 아이디
            http_client (KisHttpClient): KisHttpClient 인스턴스
            ws_client (KisWsClient): KisWsClient 인스턴스
            on_order_filled (Callable[[KisKrStkOMS, str, bool, int, int], None]): 주문 체결 콜백, on_order_filled(self, code, isBuy, qty, prc)
            on_order_canceled (Callable[[KisKrStkOMS, str, bool, int, int], None]): 주문 취소 콜백, on_order_canceled(self, code
            on_error (Callable[[KisKrStkOMS, Error], None]): 에러 콜백, on_error(self, Error)
            timeout (float): HTTP 요청 타임아웃, default 1.0
            mempool_size (int): 메모리 풀 크기, default 128

        Note:
        - ws_clinet에 자동으로 WsKrxDevExecAlert 등록, 체결 메시지 수신 시 on_order_filled 호출.
        - ws_clinet에 WsKrxDevExecAlert 콜백을 덮어쓰지 마세요.
        """
        instance = cls(cls._prevented)
        instance.cano = cano
        instance.acnt_prdt_cd = acnt_prdt_cd
        instance.hts_id = hts_id

        instance.http_client = http_client

        instance.on_order_filled = on_order_filled
        instance.on_order_canceled = on_order_canceled
        instance.on_error = on_error
        instance.timeout = timeout

        instance.margin = [0, 0]
        instance.posits = {}

        base_headers = {
            "content-type": b"application/json",
            "authorization": http_client.client.headers["authorization"],  # type: ignore
            "appkey": http_client.client.headers["appkey"],  # type: ignore
            "appsecret": http_client.client.headers["appsecret"],  # type: ignore
            "custtype": http_client.custtype.encode(),
        }

        # header types per order type, tr_id is different for buy/sell/cancel, illiminate header copying
        instance._headers_buy = base_headers.copy()
        instance._headers_buy["tr_id"] = b"TTTC0012U"  # Buy
        instance._headers_sell = base_headers.copy()
        instance._headers_sell["tr_id"] = b"TTTC0011U"  # Sell
        instance._headers_cancel = base_headers.copy()
        instance._headers_cancel["tr_id"] = b"TTTC0013U"  # Adjust & Cancel

        instance.orders_onwait = {}
        instance.orders_onwire = {}
        instance.orders_orphan = {}  # cancelled/executed message received before order accepted message

        instance.bg_tasks = http_client.bg_tasks
        instance._loop = asyncio.get_running_loop()
        instance._omsid = 0

        instance._mempool = MemoryPool[KrStkOrder](KrStkOrder, mempool_size)

        # Bind WsKrStkExecAlert handler to ws_client
        instance.bind_ws_client(ws_client, hts_id)

        # Initialize margin and positions
        await instance.update_balance()

        return instance

    def _get_omsid(self) -> int:
        self._omsid += 1
        return self._omsid

    async def _async_order_place(
        self,
        omsid: int,
        code: str,
        isBuy: bool,
        odrkind: Union[str, KrOrderKind],
        qty: int,
        prc: int,
        exgcode: Literal["KRX", "NXT", "SOR"],
    ) -> None:
        try:
            resp = await self.http_client.request_unsafe(
                method=RequestMethod.POST,  # type: ignore
                params="/uapi/domestic-stock/v1/trading/order-cash",
                body=f'{{"CANO":"{self.cano}","ACNT_PRDT_CD":"{self.acnt_prdt_cd}","PDNO":"{code}","ORD_DVSN":"{odrkind}","ORD_QTY":"{qty}","ORD_UNPR":"{prc}","EXCG_ID_DVSN_CD":"{exgcode}"}}'.encode(),
                headers=self._headers_buy if isBuy else self._headers_sell,
            )
            # update order status
            onwire_odr = self.orders_onwire.pop(omsid, None)
            if onwire_odr is None:
                return
            resp_json: dict = orjson_loads(resp.content)
            rt_cd = resp_json.get("rt_cd", "")
            if rt_cd == "0":  # B/S order accepted
                oid = resp_json["output"]["ODNO"]
                onwire_odr.oid = oid
                onwire_odr.status = "onwait"
                self.orders_onwait.setdefault(code, {})[oid] = onwire_odr
                self._handle_orphan_orders(oid, code, isBuy)
            else:  # order rejected
                self._mempool.free(onwire_odr)
                # recover margin and position
                if isBuy:
                    self.margin[0] += prc * qty
                    self.posits[code][0] -= qty
                else:
                    self.posits[code][0] += qty
                self.on_error(self, KisErrOrderRejected(resp_json))
        except Exception as e:
            onwire_odr = self.orders_onwire.pop(omsid, None)
            if onwire_odr is not None:
                self._mempool.free(onwire_odr)
            if isBuy:
                self.margin[0] += prc * qty
                self.posits[code][0] -= qty
            else:
                self.posits[code][0] += qty
            self.on_error(self, KisErrPython(e))

    async def _async_order_cancel(
        self,
        oOid: str,
        qty: int,
        isAllQty: Literal["Y", "N"],
        exgcode: Literal["KRX", "NXT", "SOR"],
    ) -> None:
        try:
            resp = await self.http_client.request_unsafe(
                method=RequestMethod.POST,  # type: ignore
                params="/uapi/domestic-stock/v1/trading/order-rvsecncl",
                body=f'{{"CANO":"{self.cano}","ACNT_PRDT_CD":"{self.acnt_prdt_cd}","ORGN_ODNO":"{oOid}","ORD_DVSN":"00","RVSE_CNCL_DVSN_CD":"02","ORD_QTY":"{qty}","ORD_UNPR":"0","QTY_ALL_ORD_YN":"{isAllQty}","EXCG_ID_DVSN_CD":"{exgcode}"}}'.encode(),
                headers=self._headers_cancel,
            )
            resp_json: dict = orjson_loads(resp.content)
            rt_cd = resp_json.get("rt_cd", "")
            if rt_cd == "0":  # Cancel order accepted
                pass
            else:  # order rejected
                onwire_odr = self.orders_onwire.pop(oOid, None)
                if onwire_odr is not None:
                    self._mempool.free(onwire_odr)
                self.on_error(self, KisErrOrderRejected(resp_json))
        except Exception as e:
            onwire_odr = self.orders_onwire.pop(oOid, None)
            if onwire_odr is not None:
                self._mempool.free(onwire_odr)
            self.on_error(self, KisErrPython(e))

    def _handle_orphan_orders(self, oid: str, code: str, isBuy: bool):
        orphan_odrs = self.orders_orphan.pop(oid, None)
        if orphan_odrs is None:
            return
        for side, qty, prc in orphan_odrs:
            if side in ("B", "S"):
                err = self._handle_order_filled(code, isBuy, qty, prc, oid)
                self.on_order_filled(
                    self, code, isBuy, qty, prc
                ) if err is None else self.on_error(self, err)
            elif side == "C":
                err = self._handle_order_cancelled(code, isBuy, qty, prc, oid)
                self.on_order_canceled(
                    self, code, isBuy, qty, prc
                ) if err is None else self.on_error(self, err)
            else:
                # TODO handle adjust
                pass

    def _handle_order_filled(
        self,
        filled_code: str,
        isBuy: bool,
        filled_qty: int,
        filled_prc: int,
        filled_oid: str,
    ) -> Optional[KisErrOrphanOrderOccured]:
        onwait_odr = self.orders_onwait.setdefault(filled_code, {}).get(
            filled_oid, None
        )
        if (
            onwait_odr is None
        ):  # orphan execution, order accepted message is not received yet.
            orphan_odr = self.orders_orphan.get(filled_oid, None)
            side = "B" if isBuy else "S"
            if orphan_odr is None:
                self.orders_orphan[filled_oid] = [(side, filled_qty, filled_prc)]
            else:
                orphan_odr.append((side, filled_qty, filled_prc))
            return KisErrOrphanOrderOccured(filled_oid)

        posits = self.posits[filled_code]  # ASSERT No KeyError,
        if isBuy:
            posits[0] -= filled_qty
            posits[1] += filled_qty
            self.margin[0] += filled_qty * filled_prc  # refund pending cash
            self.margin[1] -= filled_qty * filled_prc
        else:  # "S"
            posits[0] += filled_qty
            posits[1] -= filled_qty
            self.margin[1] += filled_qty * filled_prc  # TODO: 매도대금 재사용비율 차감
        onwait_odr.qty -= filled_qty
        if onwait_odr.qty == 0:
            del self.orders_onwait[filled_code][filled_oid]
            self._mempool.free(onwait_odr)
        else:
            onwait_odr.status = "partial"

        return None

    def _handle_order_cancelled(
        self,
        cancel_code: str,
        isBuy: bool,
        cancel_qty: int,
        cancel_prc: int,
        oOid: str,
    ) -> Optional[KisErrOrphanOrderOccured]:
        onwait_odr = self.orders_onwait.setdefault(cancel_code, {}).get(oOid, None)
        if (
            onwait_odr is None
        ):  # orphan execution, order accepted message is not received yet.
            orphan_odr = self.orders_orphan.get(oOid, None)
            if orphan_odr is None:
                self.orders_orphan[oOid] = [("C", cancel_qty, cancel_prc)]
            else:
                orphan_odr.append(("C", cancel_qty, cancel_prc))
            return None

        posits = self.posits.setdefault(cancel_code, [0, 0])
        if isBuy:
            posits[0] -= cancel_qty
            self.margin[0] += cancel_qty * cancel_prc
        else:
            posits[0] += cancel_qty

        onwait_odr.qty -= cancel_qty
        if onwait_odr.qty == 0:
            del self.orders_onwait[cancel_code][oOid]
            self._mempool.free(onwait_odr)
        else:
            onwait_odr.status = "partial"

        return None

    def bind_ws_client(self, ws_client: KisWsClient, hts_id: str):
        def _handle_WsKrxDevExecAlert(_: KisWsClient, msg: list[bytes]) -> None:
            if msg[13] == b"1":  # Order Received message
                return

            oid = msg[2].decode()
            isBuy = False if msg[4] == b"01" else True
            code = msg[8].decode()
            qty = int(msg[9])
            prc = int(msg[10])
            if msg[13] == b"2":  # execution message
                err = self._handle_order_filled(code, isBuy, qty, prc, oid)
                self.on_order_filled(
                    self, code, isBuy, qty, prc
                ) if err is None else self.on_error(self, err)
            elif msg[5] == b"2":  # Cancel message
                if msg[14] == b"3":  # IOC/FOK cancel
                    oOid = oid
                else:  # Regular cancel
                    oOid = msg[3].decode()
                    cancel_odr = self.orders_onwire.pop(oOid, None)
                    if cancel_odr is not None:
                        self._mempool.free(cancel_odr)
                err = self._handle_order_cancelled(code, isBuy, qty, prc, oOid)
                self.on_order_canceled(
                    self, code, isBuy, qty, prc
                ) if err is None else self.on_error(self, err)
            elif msg[5] == b"1":  # Adjust message
                # TODO
                pass
            else:
                # TODO Error handling
                pass

        ws_client._callbacks[WsKrxDevExecAlert.TrId.encode()] = (
            WsKrxDevExecAlert.TrLength,
            _handle_WsKrxDevExecAlert,
        )
        ws_client.subscribe(WsKrxDevExecAlert.TrId, hts_id)

    def schedule_update_balance(self):
        async_schedule(self.update_balance, self.bg_tasks)

    async def update_balance(self):
        """현재 잔고를 조회하여 self.margins 및 self.posits 업데이트."""
        temp_posits: dict[str, list[int]] = {}
        temp_margin: list[int] = [0, 0]
        isError = False

        req_header = self.http_client.client.headers.copy()  # type: ignore
        # req_header["tr_id"] = b"TTTC0869R"
        # try:
        #     resp = await self.http_client.request(
        #         method=RequestMethod.GET,  # type: ignore
        #         params=f"/uapi/domestic-stock/v1/trading/intgr-margin?CANO={self.cano}&ACNT_PRDT_CD={self.acnt_prdt_cd}&CMA_EVLU_AMT_ICLD_YN=N&WCRC_FRCR_DVSN_CD=02&FWEX_CTRT_FRCR_DVSN_CD=02",
        #         headers=req_header,
        #         timeout=self.timeout,
        #     )
        #     resp_json = orjson_loads(resp.content)
        #     if resp_json.get("rt_cd", "") != "0":
        #         raise Exception(resp_json)
        #     temp_margin[1] = int(resp_json["output"]["stck_cash_ord_psbl_amt"])
        # except Exception as e:
        #     isError = True
        #     self.on_error(self, KisErrPython(e))

        req_header["tr_id"] = b"TTTC8434R"
        try:
            ctx_area_fk100 = ""
            ctx_area_nk100 = ""
            while True:
                resp = await self.http_client.request(
                    method=RequestMethod.GET,  # type: ignore
                    params=f"/uapi/domestic-stock/v1/trading/inquire-balance?CANO={self.cano}&ACNT_PRDT_CD={self.acnt_prdt_cd}&AFHR_FLPR_YN=N&INQR_DVSN=01&UNPR_DVSN=01&FUND_STTL_ICLD_YN=N&FNCG_AMT_AUTO_RDPT_YN=N&PRCS_DVSN=00&CTX_AREA_FK100={ctx_area_fk100}&CTX_AREA_NK100={ctx_area_nk100}",
                    headers=req_header,
                    timeout=self.timeout,
                )
                resp_json = orjson_loads(resp.content)
                if resp_json.get("rt_cd", "") != "0":
                    raise Exception(resp_json)
                ctx_area_fk100 = resp_json.get("ctx_area_fk100", "")
                ctx_area_nk100 = resp_json.get("ctx_area_nk100", "")
                posit_msgs = resp_json.get("output1", [])
                for posit_msg in posit_msgs:
                    code = posit_msg["pdno"]
                    posit = temp_posits.setdefault(code, [0, 0])
                    posit[1] = int(posit_msg["hldg_qty"])
                if ctx_area_nk100.strip() == "":
                    temp_margin[1] = int(resp_json["output2"]["dnca_tot_amt"])
                    break
        except Exception as e:
            isError = True
            self.on_error(self, KisErrPython(e))

        req_header["tr_id"] = b"TTTC0084R"
        try:
            ctx_area_fk100 = ""
            ctx_area_nk100 = ""
            while True:
                resp = await self.http_client.request(
                    method=RequestMethod.GET,  # type: ignore
                    params=f"/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl?CANO={self.cano}&ACNT_PRDT_CD={self.acnt_prdt_cd}&CTX_AREA_FK100={ctx_area_fk100}&CTX_AREA_NK100={ctx_area_nk100}&INQR_DVSN_1=0&INQR_DVSN_2=0",
                    headers=req_header,
                    timeout=self.timeout,
                )
                resp_json = orjson_loads(resp.content)
                if resp_json.get("rt_cd", "") != "0":
                    raise Exception(resp_json)
                ctx_area_fk100 = resp_json.get("ctx_area_fk100", "")
                ctx_area_nk100 = resp_json.get("ctx_area_nk100", "")
                posit_msgs = resp_json.get("output1", [])
                for posit_msg in posit_msgs:
                    code = posit_msg["pdno"]
                    posit = temp_posits.setdefault(code, [0, 0])
                    pending_qty = int(posit_msg["psbl_qty"]) * (
                        1 if posit_msg["sll_buy_dvsn_cd"] == "02" else -1
                    )
                    posit[0] += pending_qty
                if ctx_area_nk100.strip() == "":
                    break
        except Exception as e:
            isError = True
            self.on_error(self, KisErrPython(e))

        if not isError:
            self.posits = temp_posits
            self.margin = temp_margin

    def get_margin(self) -> list[int]:
        """[pedmrg, actmrg]를 반환합니다.

        Note:
            - pedmrg: 아직 체결되지 않은 주문에 예약된 증거금
            - actmrg: 실제 증거금 잔고
        """
        return self.margin

    def get_posit(self, code: str) -> list[int]:
        """code 종목의 [pedpos, actpos]를 반환합니다.

        Args:
            code: 종목 코드, 예) 'A01603'

        Note:
            - pedpos: 아직 체결되지 않은 수량
            - actpos: 체결된 수량
        """
        return self.posits.get(code, [0, 0])

    def get_onwait_bids(self, code: str) -> Iterable[KrStkOrder]:
        """code 종목의 OnWait 매수 주문들을 반환합니다.

        Args:
            code: 종목 코드, 예) 'A01603'

        Note:
            - OnWait: 접수되어 체결을 기다리는 주문
            - 값이 없는 경우 빈 tuple, 있는 경우 generator를 반환합니다. list가 필요한 경우 list()로 감싸서 사용하세요.
        """
        active_orders = self.orders_onwait.get(code, {})
        if not active_orders:
            return ()
        return (odr for odr in active_orders.values() if odr.side == "B")

    def get_onwait_asks(self, code: str) -> Iterable[KrStkOrder]:
        """code 종목의 OnWait 매도 주문들을 반환합니다.

        Args:
            code: 종목 코드, 예) 'A01603'

        Note:
            - OnWait: 접수되어 체결을 기다리는 주문
            - 값이 없는 경우 빈 tuple, 있는 경우 generator를 반환합니다. list가 필요한 경우 list()로 감싸서 사용하세요.
        """
        active_orders = self.orders_onwait.get(code, {})
        if not active_orders:
            return ()
        return (odr for odr in active_orders.values() if odr.side == "S")

    def get_onwire_orders(
        self, code: str, side: Literal["B", "S", "A", "C"]
    ) -> Iterable[KrStkOrder]:
        """code 종목의 side 방향의 모든 OnWire 주문들을 반환합니다.

        Args:
            code: 종목 코드, 예) '005930'
            side: 주문 방향 ['B', 'S', 'A', 'C'] (Buy, Sell, Adjust, Cancel)

        Note:
            - 예약 주문: 아직 체결되지 않은 주문 (접수 대기 중이거나 접수되어 체결을 기다리는 주문)
            - 값이 없는 경우 빈 tuple, 있는 경우 generator를 반환합니다. list가 필요한 경우 list()로 감싸서 사용하세요.
        """
        if not self.orders_onwire:
            return ()
        return (
            odr
            for odr in self.orders_onwire.values()
            if odr.code == code and odr.side == side
        )

    def get_onwire_orders_any(
        self, code: str, side: Literal["B", "S", "A", "C"]
    ) -> bool:
        """code 종목의 side 방향의 OnWire 주문의 존재 여부를 반환합니다.

        Args:
            code: 종목 코드, 예) '005930'
            side: 주문 방향 ['B', 'S', 'A', 'C'] (Buy, Sell, Adjust, Cancel)
        """
        if not self.orders_onwire:
            return False
        return any(
            odr
            for odr in self.orders_onwire.values()
            if odr.code == code and odr.side == side
        )

    def order_cash(
        self,
        code: str,
        isBuy: bool,
        odrKind: Union[str, KrOrderKind],
        qty: int,
        prc: int,
        exgcode: Literal["KRX", "NXT", "SOR"] = "KRX",
    ) -> Optional[KisErrApiLimit | KisErrNotEnoughMargin | KisErrNotEnoughPosition]:
        """현금 주문

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/trading/order-cash

        Args:
            code: 종목코드 (예: 005930)
            isBuy: 매수주문 여부
            odrkind: 주문유형
            qty: 주문수량
            prc: 주문가격
            exgcode: 거래소 코드 ['KRX', 'NXT', 'SOR'], default 'KRX'
        """
        try:
            self.http_client._api_limit_queue.get_nowait()
        except asyncio.QueueEmpty:
            return KisErrApiLimit(None)

        # check margin and position
        pedmrg, actmrg = self.margin
        pending_pos, active_pos = self.posits.setdefault(code, [0, 0])
        if isBuy:
            pedmrg -= qty * prc
            pending_pos += qty
            if (pedmrg + actmrg) < 0:
                self.http_client._api_limit_queue.put_nowait(None)  # API token rollback
                return KisErrNotEnoughMargin(
                    {
                        "action": "order_cash",
                        "current": actmrg,
                        "required": qty * prc,
                    }
                )
        else:
            pending_pos -= qty
            if (pending_pos + active_pos) < 0:
                self.http_client._api_limit_queue.put_nowait(None)  # API token rollback
                return KisErrNotEnoughPosition(
                    {
                        "action": "order_cash",
                        "current": active_pos,
                        "required": qty,
                    }
                )
        self.margin[0] = pedmrg
        self.posits[code][0] = pending_pos

        # Allocate pending order
        omsid = self._get_omsid()
        odr = self._mempool.alloc()
        odr.init(omsid, code, "B" if isBuy else "S", odrKind, qty, prc)
        self.orders_onwire[omsid] = odr

        task = self._loop.create_task(
            self._async_order_place(omsid, code, isBuy, odrKind, qty, prc, exgcode),
            # eager_start = True # type: ignore
        )
        self.bg_tasks.add(task)
        task.add_done_callback(self.bg_tasks.discard)

    def order_cancel(
        self,
        oOid: str,
        code: str,
        qty: int,
        isAllQty: Literal["Y", "N"] = "Y",
        exgcode: Literal["KRX", "NXT", "SOR"] = "KRX",
    ) -> Optional[KisErrApiLimit | KisErrOrderNotFund]:
        """주문취소

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/trading/order-rvsecncl

        Args:
            oOid: 원주문번호
            code: 종목코드
            qty: 주문수량 (전량 취소 시 0 입력)
            isAllQty: 전량 주문 여부 ['Y', 'N'], default 'Y'
            exgcode: 거래소 코드 ['KRX', 'NXT', 'SOR'], default 'KRX'
        """
        oodr = self.orders_onwait.setdefault(code, {}).get(oOid, None)
        if oodr is None:
            return KisErrOrderNotFund(oOid)

        # If cancel is ongoing, return immediately to prevent duplicate cancel attempts.
        if oOid in self.orders_onwire:
            return

        try:
            self.http_client._api_limit_queue.get_nowait()
        except asyncio.QueueEmpty:
            return KisErrApiLimit(None)

        # Allocate pending cancel,
        # Cancel orders are special, key for orders_pending is not omsid, but the original order number(odrno)
        odr = self._mempool.alloc()
        odr.init(self._get_omsid(), code, "C", "01", qty, oodr.prc)
        self.orders_onwire[oOid] = odr

        task = self._loop.create_task(
            self._async_order_cancel(oOid, qty, isAllQty, exgcode),
            # eager_start = True
        )
        self.bg_tasks.add(task)
        task.add_done_callback(self.bg_tasks.discard)


class KisKrDevOMS(ForceAsyncNew):
    ## user inputs
    # KisKrDevOMS specific inputs
    cano: str
    acnt_prdt_cd: str
    hts_id: str
    # shared
    http_client: KisHttpClient
    on_order_filled: Callable[[Self, str, bool, int, Decimal], None]
    "on_order_filled(KisKrStkOMS, code, isBuy, qty, prc)"
    on_order_canceled: Callable[[Self, str, bool, int, Decimal], None]
    "on_order_canceled(KisKrStkOMS, code, isBuy, qty, prc)"
    on_order_adjusted: Callable[[Self, KrDevOrder], None]
    "on_order_adjusted(KisKrStkOMS, KrFutOptOrder)"
    on_error: Callable[[Self, Error], None]
    "on_error(KisKrStkOMS, Error)"
    timeout: float = 1.0

    ## internal states
    # KisKrDevOMS specific states
    _headers_buysell_day: dict[str, bytes]
    _headers_buysell_night: dict[str, bytes]
    _headers_adjcan_day: dict[str, bytes]
    _headers_adjcan_night: dict[str, bytes]
    # shared
    margin: list[Decimal]
    "[pending_margin, active_margin]"
    posits: dict[str, list[int]]
    "code -> [pending_qty, active_qty]"
    orders_onwire: dict[str | int, KrDevOrder]
    "omsid -> KrDevOrder, oOid for cancel orders"
    orders_onwait: dict[str, dict[str, KrDevOrder]]
    "code -> oid -> KrDevOrder"
    orders_orphan: dict[str, list[tuple[Literal["B", "S", "A", "C"], int, Decimal]]]
    "oid -> list[tuple[side, qty, prc]]"
    # order management
    _omsid: int
    _mempool: MemoryPool[KrDevOrder]
    # async management
    _loop: asyncio.AbstractEventLoop
    bg_tasks: set[asyncio.Task]

    @classmethod
    async def New(
        cls,
        cano: str,
        acnt_prdt_cd: str,
        hts_id: str,
        http_client: KisHttpClient,
        ws_client: KisWsClient,
        on_order_filled: Callable[[Self, str, bool, int, Decimal], None],
        on_order_canceled: Callable[[Self, str, bool, int, Decimal], None],
        on_error: Callable[[Self, Error], None],
        timeout: float = 1.0,
        mempool_size: int = 128,
    ) -> Self:
        """KIS 국내파생 실시간 주문/체결 관리

        Args:
            cano (str): 계좌번호
            acnt_prdt_cd (str): 상품유형코드
            hts_id (str): HTS 아이디
            http_client (KisHttpClient): KisHttpClient 인스턴스
            ws_client (KisWsClient): KisWsClient 인스턴스
            on_order_filled (Callable[[KisKrStkOMS, str, bool, int, Decimal], None]): 주문 체결 콜백, on_order_filled(self, code, isBuy, qty, prc)
            on_order_canceled (Callable[[KisKrStkOMS, str, bool, int, Decimal], None]): 주문 취소 콜백, on_order_canceled(self, code
            on_error (Callable[[KisKrStkOMS, Error], None]): 에러 콜백, on_error(self, Error)
            timeout (float): HTTP 요청 타임아웃, default 1.0
            mempool_size (int): 메모리 풀 크기, default 128

        Note:
        - ws_clinet에 자동으로 WsKrxDevExecAlert 등록, 체결 메시지 수신 시 on_order_filled 호출.
        - ws_clinet에 WsKrxDevExecAlert 콜백을 덮어쓰지 마세요.
        """
        instance = cls(cls._prevented)
        instance.cano = cano
        instance.acnt_prdt_cd = acnt_prdt_cd
        instance.hts_id = hts_id

        instance.http_client = http_client

        instance.on_order_filled = on_order_filled
        instance.on_order_canceled = on_order_canceled
        instance.on_error = on_error
        instance.timeout = timeout

        instance.margin = [Decimal(0.0), Decimal(0.0)]
        instance.posits = {}

        base_headers = {
            "content-type": b"application/json",
            "authorization": http_client.client.headers["authorization"],  # type: ignore
            "appkey": http_client.client.headers["appkey"],  # type: ignore
            "appsecret": http_client.client.headers["appsecret"],  # type: ignore
            "custtype": http_client.custtype.encode(),
        }

        # header types per order type, tr_id is different for buy/sell/cancel, illiminate header copying
        instance._headers_buysell_day = base_headers.copy()
        instance._headers_buysell_day["tr_id"] = b"TTTO1101U"  # Daytime Buy/Sell
        instance._headers_buysell_night = base_headers.copy()
        instance._headers_buysell_night["tr_id"] = b"STTN1101U"  # Nighttime Buy/Sell
        instance._headers_adjcan_day = base_headers.copy()
        instance._headers_adjcan_day["tr_id"] = b"TTTO1103U"  # Daytime Adjust/Cancel
        instance._headers_adjcan_night = base_headers.copy()
        instance._headers_adjcan_night["tr_id"] = (
            b"STTN1103U"  # Nighttime Adjust/Cancel
        )

        instance.orders_onwait = {}
        instance.orders_onwire = {}
        instance.orders_orphan = {}  # cancelled/executed message received before order accepted message

        instance.bg_tasks = http_client.bg_tasks
        instance._loop = asyncio.get_running_loop()
        instance._omsid = 0

        instance._mempool = MemoryPool(KrDevOrder, mempool_size)

        # Bind WsKrStkExecAlert handler to ws_client
        instance.bind_ws_client(ws_client, hts_id)

        # Initialize margin and positions
        await instance.update_balance()

        return instance

    def _get_omsid(self) -> int:
        self._omsid += 1
        return self._omsid

    async def _async_order_place(
        self,
        omsid: int,
        code: str,
        isBuy: bool,
        odrKind: Literal["01", "02", "03", "04", "10", "11", "12", "13", "14", "15"],
        qty: int,
        prc: Decimal,
        leverage: Decimal,
    ) -> None:
        try:
            buysell_code = "02" if isBuy else "01"
            resp = await self.http_client.request_unsafe(
                method=RequestMethod.POST,  # type: ignore
                params="/uapi/domestic-futureoption/v1/trading/order",
                body=f'{{"ORD_PRCS_DVSN_CD":"02","CANO":"{self.cano}","ACNT_PRDT_CD":"{self.acnt_prdt_cd}","SLL_BUY_DVSN_CD":"{buysell_code}","SHTN_PDNO":"{code}","ORD_QTY":"{qty}","UNIT_PRICE":"{prc}","ORD_DVSN_CD":"{odrKind}"}}'.encode(),
                headers=self._headers_buysell_day,
            )
            # update order status
            onwire_odr = self.orders_onwire.pop(omsid, None)
            if onwire_odr is None:
                return
            resp_json: dict = orjson_loads(resp.content)
            rt_cd = resp_json.get("rt_cd", "")
            if rt_cd == "0":  # B/S order accepted
                oid = resp_json["output"]["ODNO"]
                onwire_odr.oid = oid
                onwire_odr.status = "onwait"
                self.orders_onwait.setdefault(code, {})[oid] = onwire_odr
                self._handle_orphan_orders(oid, code, isBuy)
            else:  # order rejected
                self._mempool.free(onwire_odr)
                # recover margin and position
                self.margin[0] += prc * qty / leverage
                self.posits[code][0] -= qty if isBuy else -qty
                self.on_error(self, KisErrOrderRejected(resp_json))
        except Exception as e:
            onwire_odr = self.orders_onwire.pop(omsid, None)
            if onwire_odr is not None:
                self._mempool.free(onwire_odr)
            self.margin[0] += prc * qty / leverage
            self.posits[code][0] -= qty if isBuy else -qty
            self.on_error(self, KisErrPython(e))

    async def _async_order_cancel(
        self,
        oOid: str,
        qty: int,
        isAllQty: Literal["Y", "N"],
    ) -> None:
        try:
            resp = await self.http_client.request_unsafe(
                method=RequestMethod.POST,  # type: ignore
                params="/uapi/domestic-futureoption/v1/trading/order-rvsecncl",
                body=f'{{"ORD_PRCS_DVSN_CD":"02","CANO":"{self.cano}","ACNT_PRDT_CD":"{self.acnt_prdt_cd}","RVSE_CNCL_DVSN_CD":"02","ORGN_ODNO":"{oOid}","ORD_QTY":"{qty}","UNIT_PRICE":"0","NMPR_TYPE_CD":"01","KRX_NMPR_CNDT_CD":"0","RMN_QTY_YN":"{isAllQty}","ORD_DVSN_CD":"01"}}'.encode(),
                headers=self._headers_adjcan_day,
            )
            resp_json: dict = orjson_loads(resp.content)
            rt_cd = resp_json.get("rt_cd", "")
            if rt_cd == "0":  # Cancel order accepted
                pass
            else:  # order rejected
                onwire_odr = self.orders_onwire.pop(oOid, None)
                if onwire_odr is not None:
                    self._mempool.free(onwire_odr)
                self.on_error(self, KisErrOrderRejected(resp_json))
        except Exception as e:
            onwire_odr = self.orders_onwire.pop(oOid, None)
            if onwire_odr is not None:
                self._mempool.free(onwire_odr)
            self.on_error(self, KisErrPython(e))

    def _handle_orphan_orders(self, oid: str, code: str, isBuy: bool):
        orphan_odrs = self.orders_orphan.pop(oid, None)
        if orphan_odrs is None:
            return
        for side, qty, prc in orphan_odrs:
            if side in ("B", "S"):
                err = self._handle_order_filled(code, isBuy, qty, prc, oid)
                self.on_order_filled(
                    self, code, isBuy, qty, prc
                ) if err is None else self.on_error(self, err)
            elif side == "C":
                err = self._handle_order_cancelled(code, isBuy, qty, prc, oid)
                self.on_order_canceled(
                    self, code, isBuy, qty, prc
                ) if err is None else self.on_error(self, err)
            else:
                # TODO handle adjust
                pass

    def _handle_order_filled(
        self,
        filled_code: str,
        isBuy: bool,
        filled_qty: int,
        filled_prc: Decimal,
        filled_oid: str,
    ) -> Optional[KisErrOrphanOrderOccured]:
        onwait_odr = self.orders_onwait.setdefault(filled_code, {}).get(
            filled_oid, None
        )
        if (
            onwait_odr is None
        ):  # orphan execution, order accepted message is not received yet.
            orphan_odr = self.orders_orphan.get(filled_oid, None)
            side = "B" if isBuy else "S"
            if orphan_odr is None:
                self.orders_orphan[filled_oid] = [(side, filled_qty, filled_prc)]
            else:
                orphan_odr.append((side, filled_qty, filled_prc))
            return KisErrOrphanOrderOccured(filled_oid)

        posits = self.posits[filled_code]  # ASSERT No KeyError,
        actpos_before = abs(posits[1])
        if isBuy:
            posits[0] -= filled_qty
            posits[1] += filled_qty
        else:
            posits[0] += filled_qty
            posits[1] -= filled_qty
        delta_actpos = abs(posits[1]) - actpos_before

        qty_div_leverage = filled_qty / onwait_odr.leverage
        margin = self.margin
        margin[0] += qty_div_leverage * onwait_odr.prc  # pending margin is released
        # active margin is changed according to whether the fill increases or decreases the absolute position
        margin[1] -= delta_actpos * (filled_prc / onwait_odr.leverage)

        onwait_odr.qty -= filled_qty
        if onwait_odr.qty == 0:
            del self.orders_onwait[filled_code][filled_oid]
            self._mempool.free(onwait_odr)
        else:
            onwait_odr.status = "partial"

        return None

    def _handle_order_cancelled(
        self,
        cancel_code: str,
        isBuy: bool,
        cancel_qty: int,
        cancel_prc: Decimal,
        oOid: str,
    ) -> Optional[KisErrOrphanOrderOccured]:
        onwait_odr = self.orders_onwait.setdefault(cancel_code, {}).get(oOid, None)
        if (
            onwait_odr is None
        ):  # orphan execution, order accepted message is not received yet.
            orphan_odr = self.orders_orphan.get(oOid, None)
            if orphan_odr is None:
                self.orders_orphan[oOid] = [("C", cancel_qty, cancel_prc)]
            else:
                orphan_odr.append(("C", cancel_qty, cancel_prc))
            return None

        posits = self.posits[cancel_code]
        posits[0] += -cancel_qty if isBuy else cancel_qty
        self.margin[0] += cancel_qty * cancel_prc / onwait_odr.leverage

        onwait_odr.qty -= cancel_qty
        if onwait_odr.qty == 0:
            del self.orders_onwait[cancel_code][oOid]
            self._mempool.free(onwait_odr)
        else:
            onwait_odr.status = "partial"

        return None

    def bind_ws_client(self, ws_client: KisWsClient, hts_id: str):
        def _handle_WsKrxDevExecAlert(_: KisWsClient, msg: list[bytes]) -> None:
            if msg[13] == b"1":  # Order Received message
                return

            oid = msg[2].decode()
            isBuy = False if msg[4] == b"01" else True
            code = msg[7].decode()
            qty = int(msg[8])
            prc = Decimal(msg[9].decode())
            if msg[12] == b"2":  # execution message
                err = self._handle_order_filled(code, isBuy, qty, prc, oid)
                self.on_order_filled(
                    self, code, isBuy, qty, prc
                ) if err is None else self.on_error(self, err)
            elif msg[5] == b"2":  # Cancel message
                if msg[13] == b"3":  # IOC/FOK cancel
                    oOid = oid
                else:  # Regular cancel
                    oOid = msg[3].decode()
                    cancel_odr = self.orders_onwire.pop(oOid, None)
                    if cancel_odr is not None:
                        self._mempool.free(cancel_odr)
                err = self._handle_order_cancelled(code, isBuy, qty, prc, oOid)
                self.on_order_canceled(
                    self, code, isBuy, qty, prc
                ) if err is None else self.on_error(self, err)
            elif msg[5] == b"1":  # Adjust message
                # TODO
                pass
            else:
                # TODO Error handling
                pass

        ws_client._callbacks[WsKrxDevExecAlert.TrId.encode()] = (
            WsKrxDevExecAlert.TrLength,
            _handle_WsKrxDevExecAlert,
        )
        ws_client.subscribe(WsKrxDevExecAlert.TrId, hts_id)

    def schedule_update_balance(self):
        async_schedule(self.update_balance, self.bg_tasks)

    async def update_margin_rate(self):
        """선물옵션 증거금률 업데이트"""
        pass

    async def update_balance(self):
        """현재 잔고를 조회하여 self.margins 및 self.posits 업데이트."""
        temp_posits: dict[str, list[int]] = {}
        temp_margin: list[Decimal] = [Decimal(0.0), Decimal(0.0)]
        isError = False

        req_header = self.http_client.client.headers.copy()  # type: ignore
        req_header["tr_id"] = b"CTFO6118R"
        try:
            ctx_area_fk200 = ""
            ctx_area_nk200 = ""
            while True:
                resp = await self.http_client.request(
                    method=RequestMethod.GET,  # type: ignore
                    params=f"/uapi/domestic-futureoption/v1/trading/inquire-balance?CANO={self.cano}&ACNT_PRDT_CD={self.acnt_prdt_cd}&MGNA_DVSN=02&EXCC_STAT_CD=01&CTX_AREA_FK200={ctx_area_fk200}&CTX_AREA_NK200={ctx_area_nk200}",
                    headers=req_header,
                    timeout=self.timeout,
                )
                resp_json = orjson_loads(resp.content)
                if resp_json.get("rt_cd", "") != "0":
                    raise Exception(resp_json)
                ctx_area_fk200 = resp_json.get("ctx_area_fk200", "")
                ctx_area_nk200 = resp_json.get("ctx_area_nk200", "")
                posit_msgs = resp_json.get("output1", [])
                for posit_msg in posit_msgs:
                    sideMsg = posit_msg["sll_buy_dvsn_cd"]
                    if sideMsg == "매수" or sideMsg == "BUY":
                        sideSign = 1
                    elif sideMsg == "매도" or sideMsg == "SELL":
                        sideSign = -1
                    else:
                        continue
                    code = posit_msg["shtn_pdno"]
                    posits = temp_posits.setdefault(code, [0, 0])
                    posits[1] += int(posit_msg["cblc_qty"]) * sideSign

                if ctx_area_nk200.strip() == "":
                    temp_margin[1] = Decimal(resp_json["output2"]["ord_psbl_tota"])
                    break
        except Exception as e:
            isError = True
            self.on_error(self, KisErrPython(e))

        req_header["tr_id"] = b"TTTO5201R"
        try:
            from datetime import datetime, timedelta

            today_str = (datetime.utcnow() + timedelta(hours=9)).strftime("%Y%m%d")
            ctx_area_fk200 = ""
            ctx_area_nk200 = ""
            while True:
                resp = await self.http_client.request(
                    method=RequestMethod.GET,  # type: ignore
                    params=f"/uapi/domestic-futureoption/v1/trading/inquire-ccnl?CANO={self.cano}&ACNT_PRDT_CD={self.acnt_prdt_cd}&STRT_ORD_DT={today_str}&END_ORD_DT={today_str}&SLL_BUY_DVSN_CD=00&CCLD_NCCS_DVSN=02&SORT_SQN=AS&CTX_AREA_FK200={ctx_area_fk200}&CTX_AREA_NK200={ctx_area_nk200}",
                    headers=req_header,
                    timeout=self.timeout,
                )
                resp_json = orjson_loads(resp.content)
                if resp_json.get("rt_cd", "") != "0":
                    raise Exception(resp_json)
                ctx_area_fk200 = resp_json.get("ctx_area_fk200", "")
                ctx_area_nk200 = resp_json.get("ctx_area_nk200", "")
                order_msgs = resp_json.get("output1", [])
                for order_msg in order_msgs:
                    code = order_msg["shtn_pdno"]
                    unfilled_qty = int(order_msg["rmn_qty"])
                    isBuy = order_msg["sll_buy_dvsn_cd"] == "02"
                    posits = temp_posits.setdefault(code, [0, 0])
                    posits[0] += unfilled_qty if isBuy else -unfilled_qty
                if ctx_area_nk200.strip() == "":
                    break
        except Exception as e:
            isError = True
            self.on_error(self, KisErrPython(e))

        if not isError:
            self.posits = temp_posits
            self.margin = temp_margin

    def get_margin(self) -> list[Decimal]:
        """[pedmrg, actmrg]를 반환합니다.

        Note:
            - pedmrg: 아직 체결되지 않은 주문에 예약된 증거금
            - actmrg: 실제 증거금 잔고
        """
        return self.margin

    def get_posit(self, code: str) -> list[int]:
        """code 종목의 [pedpos, actpos]를 반환합니다.

        Args:
            code: 종목 코드, 예) 'A01603'

        Note:
            - pedpos: 아직 체결되지 않은 수량
            - actpos: 체결된 수량
        """
        return self.posits.get(code, [0, 0])

    def get_onwait_bids(self, code: str) -> Iterable[KrDevOrder]:
        """code 종목의 OnWait 매수 주문들을 반환합니다.

        Args:
            code: 종목 코드, 예) 'A01603'

        Note:
            - OnWait: 접수되어 체결을 기다리는 주문
            - 값이 없는 경우 빈 tuple, 있는 경우 generator를 반환합니다. list가 필요한 경우 list()로 감싸서 사용하세요.
        """
        active_orders = self.orders_onwait.get(code, {})
        if not active_orders:
            return ()
        return (odr for odr in active_orders.values() if odr.side == "B")

    def get_onwait_asks(self, code: str) -> Iterable[KrDevOrder]:
        """code 종목의 OnWait 매도 주문들을 반환합니다.

        Args:
            code: 종목 코드, 예) 'A01603'

        Note:
            - OnWait: 접수되어 체결을 기다리는 주문
            - 값이 없는 경우 빈 tuple, 있는 경우 generator를 반환합니다. list가 필요한 경우 list()로 감싸서 사용하세요.
        """
        active_orders = self.orders_onwait.get(code, {})
        if not active_orders:
            return ()
        return (odr for odr in active_orders.values() if odr.side == "S")

    def get_onwire_orders(
        self, code: str, side: Literal["B", "S", "A", "C"]
    ) -> Iterable[KrDevOrder]:
        """code 종목의 side 방향의 모든 OnWire 주문들을 반환합니다.

        Args:
            code: 종목 코드, 예) '005930'
            side: 주문 방향 ['B', 'S', 'A', 'C'] (Buy, Sell, Adjust, Cancel)

        Note:
            - 예약 주문: 아직 체결되지 않은 주문 (접수 대기 중이거나 접수되어 체결을 기다리는 주문)
            - 값이 없는 경우 빈 tuple, 있는 경우 generator를 반환합니다. list가 필요한 경우 list()로 감싸서 사용하세요.
        """
        if not self.orders_onwire:
            return ()
        return (
            odr
            for odr in self.orders_onwire.values()
            if odr.code == code and odr.side == side
        )

    def get_onwire_orders_any(
        self, code: str, side: Literal["B", "S", "A", "C"]
    ) -> bool:
        """code 종목의 side 방향의 OnWire 주문의 존재 여부를 반환합니다.

        Args:
            code: 종목 코드, 예) '005930'
            side: 주문 방향 ['B', 'S', 'A', 'C'] (Buy, Sell, Adjust, Cancel)
        """
        if not self.orders_onwire:
            return False
        return any(
            odr
            for odr in self.orders_onwire.values()
            if odr.code == code and odr.side == side
        )

    def order_place(
        self,
        code: str,
        isBuy: bool,
        odrKind: Literal["01", "02", "03", "04", "10", "11", "12", "13", "14", "15"],
        qty: int,
        prc: Decimal,
        leverage: Decimal,
    ) -> Optional[KisErrApiLimit | KisErrNotEnoughMargin]:
        """현금 주문

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-futureoption/v1/trading/order

        Args:
            code: 종목코드 (선물 6자리 (예: A01603), 옵션 9자리 (예: B01603955))
            isbuy: 매수주문 여부
            odrkind: 주문유형
                {01:지정가, 02:시장가, 03:조건부, 04:최유리, 00:지정가(IOC), 01:지정가(FOK), 02:시장가(IOC), 03:시장가(FOK), 04:최유리(IOC), 05:최유리(FOK)}
            qty: 주문수량
            prc: 주문가격
            leverage: 레버리지, 증거금 계산에 사용
        """
        try:
            self.http_client._api_limit_queue.get_nowait()
        except asyncio.QueueEmpty:
            return KisErrApiLimit(None)

        # check margin and position
        pedmrg, actmrg = self.margin
        delta_mrg = prc * qty / leverage
        pedmrg -= delta_mrg

        posits = self.posits.setdefault(code, [0, 0])
        delta_pedpos = qty if isBuy else -qty

        if (pedmrg + actmrg) < 0:
            actpos = posits[1]
            expected_actpos = posits[0] + actpos + delta_pedpos
            reduceOnly = (
                (0 <= expected_actpos < actpos)
                if (actpos >= 0)
                else (actpos < expected_actpos <= 0)
            )
            # margin error does not occur for reduce-only order
            if not reduceOnly:
                self.http_client._api_limit_queue.put_nowait(None)  # API token rollback
                return KisErrNotEnoughMargin(
                    {
                        "action": "order_place",
                        "current": actmrg,
                        "required": delta_mrg,
                    }
                )

        self.margin[0] = pedmrg
        posits[0] += delta_pedpos

        # Allocate pending order
        omsid = self._get_omsid()
        odr = self._mempool.alloc()
        odr.init(omsid, code, "B" if isBuy else "S", odrKind, qty, prc, leverage)
        self.orders_onwire[omsid] = odr

        task = self._loop.create_task(
            self._async_order_place(omsid, code, isBuy, odrKind, qty, prc, leverage),
            # eager_start = True # type: ignore
        )
        self.bg_tasks.add(task)
        task.add_done_callback(self.bg_tasks.discard)

    def order_cancel(
        self,
        oOid: str,
        code: str,
        qty: int,
        isAllQty: Literal["Y", "N"] = "Y",
    ) -> Optional[KisErrApiLimit | KisErrOrderNotFund]:
        """주문취소

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-futureoption/v1/trading/order-rvsecncl

        Args:
            oOid: 원주문번호
            code: 종목코드
            qty: 주문수량 (전량 취소 시 0 입력)
            isAllQty: 전량 주문 여부 ['Y', 'N'], default 'Y'
        """
        oodr = self.orders_onwait.setdefault(code, {}).get(oOid, None)
        if oodr is None:
            return KisErrOrderNotFund(oOid)

        # If cancel is ongoing, return immediately to prevent duplicate cancel attempts.
        if oOid in self.orders_onwire:
            return

        try:
            self.http_client._api_limit_queue.get_nowait()
        except asyncio.QueueEmpty:
            return KisErrApiLimit(None)

        # Allocate pending cancel,
        # Cancel orders are special, key for orders_pending is not omsid, but the original order number(odrno)
        odr = self._mempool.alloc()
        odr.init(self._get_omsid(), code, "C", "01", qty, oodr.prc, oodr.leverage)
        self.orders_onwire[oOid] = odr

        task = self._loop.create_task(
            self._async_order_cancel(oOid, qty, isAllQty),
            # eager_start = True
        )
        self.bg_tasks.add(task)
        task.add_done_callback(self.bg_tasks.discard)
