import io
import zipfile
from decimal import Decimal
from typing import Dict, Literal, TypedDict, Union

import pandas as pd
from curl_cffi import requests
from gufo.http import RequestMethod, Response
from orjson import loads as orjson_loads

from bknet.error import Errorable, Failure, Success
from bknet.kis.client import KisHttpClient
from bknet.kis.error import KisErrApiRequestRejected, KisErrPython


class KisRestKrStock:
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


class KisRestKrDerivativesResult:
    class marginRatio(TypedDict):
        code: str
        name: str
        initMrgRatio: Decimal
        mainMrgRatio: Decimal
        basePrc: Decimal
        multipler: Decimal
        mrgPerUnit: Decimal

    class histPrice1(TypedDict):
        prdyVrss: float
        "전일대비"
        prdyVrssSign: str
        "전일대비부호"
        prdyCtrt: float
        "전일대비율"
        prdyClpr: float
        "전일종가"
        acmlTvol: int
        "누적거래량"
        acmlTval: int
        "누적거래대금"
        name: str
        "HTS한글종목명"
        prc: float
        "현재가"
        code: str
        "단축종목코드"
        prdyVol: int
        "전일거래량"
        maxPrc: float
        "상한가"
        minPrc: float
        "하한가"
        open: float
        "시가"
        high: float
        "고가"
        low: float
        "저가"
        prdyOpen: float
        "전일시가"
        prdyHigh: float
        "전일고가"
        prdyLow: float
        "전일저가"
        ap1: float
        "매도호가"
        bp1: float
        "매수호가"
        basis: float
        "베이시스"
        kospi200: float
        "KOSPI200 지수"
        kospi200PrdyVrss: float
        "KOSPI200 전일대비"
        kospi200PrdyCtrt: float
        "KOSPI200 전일대비율"
        kospi200PrdyVrssSign: str
        "KOSPI200 전일대비부호"
        openInterestQty: int
        "미결제약정수량"
        openInterestQtyDelta: int
        "미결제약정수량증감"
        volumePower: float
        "체결강도"
        thoeryPrc: float
        "이론가"
        dispersionRatio: float
        "괴리도"

    class histPrice2(TypedDict):
        date: str
        "영업일자"
        close: float
        "종가"
        open: float
        "시가"
        high: float
        "고가"
        low: float
        "저가"
        tvol: int
        "거래량"
        tval: int
        "거래대금"
        modYn: str
        "변경여부"


class KisRestKrDerivatives:
    @staticmethod
    async def futopt_margin_ratio(
        httpClient: KisHttpClient, target_date: str
    ) -> Errorable[
        Dict[str, KisRestKrDerivativesResult.marginRatio],
        Union[KisErrApiRequestRejected, KisErrPython],
    ]:
        try:
            req_headers: Dict[str, bytes] = httpClient.client.headers.copy()  # type: ignore
            req_headers["tr_id"] = b"TTTO6032R"

            mrgTable: Dict[str, KisRestKrDerivativesResult.marginRatio] = {}
            ctx_area_nk200 = ""
            while True:
                if ctx_area_nk200 != "":
                    req_headers["tr_cont"] = b"N"
                resp = await httpClient.request(
                    method=RequestMethod.GET,  # type: ignore
                    params=f"/uapi/domestic-futureoption/v1/quotations/margin-rate?BASS_DT={target_date}&CTX_AREA_NK200={ctx_area_nk200}",
                    headers=req_headers,
                )
                resp_json = orjson_loads(resp.content)

                if resp_json.get("rt_cd", "") != "0":
                    raise KisErrApiRequestRejected(resp_json)

                mrgmsgs = resp_json.get("output", [])
                for mrgmsg in mrgmsgs:
                    code: str = mrgmsg["bast_id"]
                    mrgTable[code] = {
                        "code": code,
                        "name": mrgmsg["bast_name"],
                        "initMrgRatio": Decimal(mrgmsg["brkg_mgna_rt"]),
                        "mainMrgRatio": Decimal(mrgmsg["tr_mgna_rt"]),
                        "basePrc": Decimal(mrgmsg["bast_pric"]),
                        "multipler": Decimal(mrgmsg["tr_mtpl_idx"]),
                        "mrgPerUnit": Decimal(mrgmsg["ctrt_per_futr_mgna"]),
                    }
                ctx_area_nk200 = resp_json.get("ctx_area_nk200", "").strip()
                if ctx_area_nk200 == "":
                    break
        except KisErrApiRequestRejected as e:
            return Failure(None, e)
        except Exception as e:
            return Failure(None, KisErrPython(e))
        else:
            return Success(mrgTable)

    @staticmethod
    async def fut_board(httpClient: KisHttpClient, mrkt_cls_code: str) -> Response:
        """[국내선물옵션] 국내옵션전광판_선물

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-futureoption/v1/quotations/display-board-futures

        Args:
            httpClient: KisHttpClient 인스턴스
            mrkt_cls_code: 시장구분코드 {'': KOSPI200, 'MKI': 미니KOSPI200, 'WKM': KOSPI200위클리(월), 'WKI': KOSPI200위클리(목), 'KQI': KOSDAQ150}
        """
        req_headers: dict[str, bytes] = httpClient.client.headers.copy()  # type: ignore
        req_headers["tr_id"] = b"FHPIF05030200"
        return await httpClient.request(
            RequestMethod.GET,  # type: ignore
            params=f"/uapi/domestic-futureoption/v1/quotations/display-board-futures?FID_COND_MRKT_DIV_CODE=F&FID_COND_SCR_DIV_CODE=20503&FID_COND_MRKT_CLS_CODE={mrkt_cls_code}",
            headers=req_headers,
        )

    @staticmethod
    async def futopt_hist_price(
        httpClient: KisHttpClient,
        mrkt_div_code: str,
        code: str,
        sdate: str,
        edate: str,
        period_div_code: Literal["D", "W", "M"],
    ) -> Response:
        """[국내선물옵션] 선물옵션기간별시세

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-futureoption/v1/quotations/inquire-daily-fuopchartprice

        Args:
            httpClient: KisHttpClient 인스턴스
            mrkt_div_code: 시장구분코드 {'F': 지수선물, 'O': 지수옵션, 'JF': 주식선물, 'JO': 주식옵션, 'CF': 상품선물, 'CM': 야간선물, 'EU': 야간옵션}
            code: 종목 코드 (지수선물: 6자리, 지수옵션: 9자리)
            sdate: 조회 시작 일자 (YYYYMMDD)
            edate: 조회 종료 일자 (YYYYMMDD)
            period_div_code: 기간구분코드 {'D': 일간, 'W': 주간, 'M': 월간}
        """
        req_headers: dict[str, bytes] = httpClient.client.headers.copy()  # type: ignore
        req_headers["tr_id"] = b"FHKIF03020100"
        return await httpClient.request(
            RequestMethod.GET,  # type: ignore
            params=f"/uapi/domestic-futureoption/v1/quotations/inquire-daily-fuopchartprice?FID_COND_MRKT_DIV_CODE={mrkt_div_code}&FID_INPUT_ISCD={code}&FID_INPUT_DATE_1={sdate}&FID_INPUT_DATE_2={edate}&FID_PERIOD_DIV_CODE={period_div_code}",
            headers=req_headers,
        )


class KisRestSecurityMasterFile:
    """종목정보파일

    https://apiportal.koreainvestment.com/apiservice-category
    """

    _url_derivatives_commodity = (
        "https://new.real.download.dws.co.kr/common/master/fo_com_code.mst.zip"
    )
    _url_derivatives_stock = (
        "https://new.real.download.dws.co.kr/common/master/fo_stk_code_mts.mst.zip"
    )
    _url_derivatives_index = (
        "https://new.real.download.dws.co.kr/common/master/fo_idx_code_mts.mst.zip"
    )

    _url_derivatives_margin = "https://www.shinhansec.com/siw/customer-center/guide/business_guide_deposit_tab4/view.do"

    @staticmethod
    def derivatives_index() -> pd.DataFrame:
        """지수선물옵션 마스터파일 데이터프레임

        https://github.com/koreainvestment/open-trading-api/blob/main/stocks_info/종목마스터정보(지수선물옵션).h

        Note:
            dataframe columns: ['상품종류','단축코드','표준코드','한글종목명','ATM구분','행사가','월물구분코드','기초자산단축코드',' 기초자산명']
        """
        resp = requests.get(
            KisRestSecurityMasterFile._url_derivatives_index, impersonate="chrome"
        )
        resp.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(resp.content)) as zip_file:
            file_list = zip_file.namelist()
            mst_filename = [f for f in file_list if f.endswith(".mst")][0]

            with zip_file.open(mst_filename) as f:
                content = f.read().decode("cp949")

        df = pd.read_table(io.StringIO(content), sep="|", header=None)
        df.columns = [
            "상품종류",
            "단축코드",
            "표준코드",
            "한글종목명",
            "ATM구분",
            "행사가",
            "월물구분코드",
            "기초자산단축코드",
            "기초자산명",
        ]

        return df

    @staticmethod
    def derivatives_commodity() -> pd.DataFrame:
        """상품선물옵션 마스터파일 데이터프레임

        https://github.com/koreainvestment/open-trading-api/blob/main/stocks_info/종목마스터정보(상품선물옵션).h

        Note:
            dataframe columns: ["상품구분", "상품종류", "단축코드", "표준코드", "한글종목명", "월물구분코드", "기초자산단축코드", "기초자산명"]
        """
        resp = requests.get(
            KisRestSecurityMasterFile._url_derivatives_commodity, impersonate="chrome"
        )
        resp.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(resp.content)) as zip_file:
            file_list = zip_file.namelist()
            mst_filename = [f for f in file_list if f.endswith(".mst")][0]

            with zip_file.open(mst_filename) as f:
                content = f.read().decode("cp949")

        rows_data = []
        for line in content.splitlines():
            if not line.strip():
                continue

            p1_1 = line[0:1]
            p1_2 = line[1:2]
            p1_3 = line[2:11].strip()
            p1_4 = line[11:23].strip()
            p1_5 = line[23:55].strip()

            part2 = line[55:]
            p2_1 = part2[8:9]
            p2_2 = part2[9:12]
            p2_3 = part2[12:].strip()

            rows_data.append([p1_1, p1_2, p1_3, p1_4, p1_5, p2_1, p2_2, p2_3])

        columns = [
            "상품구분",
            "상품종류",
            "단축코드",
            "표준코드",
            "한글종목명",
            "월물구분코드",
            "기초자산단축코드",
            "기초자산명",
        ]
        df = pd.DataFrame(rows_data, columns=columns)

        return df

    @staticmethod
    def derivatives_stock() -> pd.DataFrame:
        """주식선물옵션 마스터파일 데이터프레임

        https://github.com/koreainvestment/open-trading-api/blob/main/stocks_info/종목마스터정보(주식선물옵션).h

        Note:
            dataframe columns: ["상품종류", "단축코드", "표준코드", "한글종목명", "ATM구분", "행사가", "월물구분코드", "기초자산단축코드", "기초자산명"]
        """
        resp = requests.get(
            KisRestSecurityMasterFile._url_derivatives_stock, impersonate="chrome"
        )
        resp.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(resp.content)) as zip_file:
            file_list = zip_file.namelist()
            mst_filename = [f for f in file_list if f.endswith(".mst")][0]

            with zip_file.open(mst_filename) as f:
                content = f.read().decode("cp949")

        df = pd.read_table(io.StringIO(content), sep="|", header=None)
        df.columns = [
            "상품종류",
            "단축코드",
            "표준코드",
            "한글종목명",
            "ATM구분",
            "행사가",
            "월물구분코드",
            "기초자산단축코드",
            "기초자산명",
        ]

        return df

    @staticmethod
    def derivatives_margin() -> pd.DataFrame:
        """(지수,상품,주식) 선물옵션 마진 데이터프레임

        https://www.shinhansec.com/siw/customer-center/guide/business_guide_deposit_tab4/view.do

        Note:
            dataframe columns: ["종목코드", "위탁증거금율", "유지증거금율", "기초자산전일종가", "계약당거래승수", "선물옵션종목한글명", "선물옵션주문증거금"]
        """
        resp = requests.get(
            KisRestSecurityMasterFile._url_derivatives_margin, impersonate="chrome"
        )
        resp.raise_for_status()

        dfs = []
        for qty_code in ("1", "2", "3"):
            for sprd_yn in ("N", "Y"):
                resp = requests.post(
                    "https://www.shinhansec.com/siw/customer-center/guide/business_guide_deposit_tab4/data.do",
                    json={
                        "body": {"qry_code": qty_code, "sprd_yn": sprd_yn},
                        "header": {
                            "SVW": "/siw/customer-center/guide/business_guide_deposit_tab4/view.do",
                            "TCD": "S",
                        },
                    },
                    impersonate="chrome",
                )
                dfs.append(pd.DataFrame(resp.json()["body"]["list01"]))

        df = pd.concat(dfs, ignore_index=True)
        df.columns = [
            "종목코드",
            "위탁증거금율",
            "유지증거금율",
            "기초자산전일종가",
            "계약당거래승수",
            "선물옵션종목한글명",
            "선물옵션주문증거금",
        ]

        return df

    @staticmethod
    def derivatives_aggregated() -> pd.DataFrame:
        """(지수,상품,주식) 선물옵션 마스터 + 증거금 통합 데이터프레임

        내부적으로 derivatives_index, derivatives_commodity, derivatives_stock, derivatives_margin 호출 후
        통합한 데이터프레임 반환

        Note:
            dataframe columns: ["단축코드","표준코드","한글종목명","ATM구분","행사가","월물구분코드","기초자산명","파생상품명","파생구분","위탁증거금율","유지증거금율","계약당거래승수"]
        """
        df_margin = KisRestSecurityMasterFile.derivatives_margin()
        df_master_all = pd.concat(
            [
                KisRestSecurityMasterFile.derivatives_index(),
                KisRestSecurityMasterFile.derivatives_commodity(),
                KisRestSecurityMasterFile.derivatives_stock(),
            ],
            ignore_index=True,
        )
        df_master_all["종목코드"] = (
            df_master_all["표준코드"]
            .str.replace("KR4", "")
            .apply(lambda x: f"{x[:5]}" if x.startswith("A") else f"{x[:8]}")
        )

        regex_pattern = r"(?:^|[^A-Za-z])(SP|F|C|P)(?:\s+|$)"

        df_master_all["파생구분"] = df_master_all["한글종목명"].str.extract(
            regex_pattern
        )[0]
        df_margin["파생구분"] = df_margin["선물옵션종목한글명"].str.extract(
            regex_pattern
        )[0]
        margin_cols = [
            "종목코드",
            "파생구분",
            "위탁증거금율",
            "유지증거금율",
            "기초자산전일종가",
            "계약당거래승수",
            "선물옵션주문증거금",
        ]
        df_margin_lookup = df_margin[margin_cols].drop_duplicates(
            subset=["종목코드", "파생구분"]
        )  # type: ignore
        df_final = pd.merge(
            df_master_all, df_margin_lookup, on=["종목코드", "파생구분"], how="left"
        )

        df_final["파생상품명"] = df_final["한글종목명"].str.extract(
            r"(^.*?(?:SP|F|C|P))(?=\s+\d)"
        )[0]

        fill_columns = [
            "위탁증거금율",
            "유지증거금율",
            "기초자산전일종가",
            "계약당거래승수",
            "선물옵션주문증거금",
        ]
        df_final[fill_columns] = (
            df_final.groupby(["파생상품명", "파생구분"])[fill_columns].ffill().bfill()
        )
        df_final["월물구분코드"] = df_final["월물구분코드"].replace(" ", "0")
        df_final["ATM구분"] = df_final["ATM구분"].replace(" ", "0").fillna("0")
        df_final["상품구분"] = df_final["상품구분"].fillna("0")
        df_final["행사가"] = df_final["행사가"].fillna("0")
        df_final: pd.DataFrame = df_final[  # type: ignore
            [
                "단축코드",
                "표준코드",
                "한글종목명",
                "ATM구분",
                "행사가",
                "월물구분코드",
                "기초자산명",
                "파생상품명",
                "파생구분",
                "위탁증거금율",
                "유지증거금율",
                "계약당거래승수",
            ]
        ]

        df_final = df_final.astype(
            {
                "단축코드": "str",
                "표준코드": "str",
                "한글종목명": "str",
                "ATM구분": "int",
                "행사가": "float",
                "월물구분코드": "int",
                "기초자산명": "str",
                "파생상품명": "str",
                "파생구분": "str",
                "위탁증거금율": "float",
                "유지증거금율": "float",
                "계약당거래승수": "float",
            }
        )

        return df_final
