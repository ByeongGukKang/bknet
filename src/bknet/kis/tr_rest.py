from bknet.kis.core import KisHttpClient

from gufo.http import RequestMethod, Response


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