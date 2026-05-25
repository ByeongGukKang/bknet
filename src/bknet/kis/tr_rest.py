from typing import Literal

from gufo.http import RequestMethod, Response

from bknet.kis.client import KisHttpClient


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
