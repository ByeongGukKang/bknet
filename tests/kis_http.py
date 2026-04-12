from bknet.src import run_system
from bknet.kis import KisHttpClient
from bknet.kis.tr_rest import RestKrDerivatives

async def main():

    httpClient = await KisHttpClient.New(
        appkey = 'appkey',
        appsecret = 'appsecret'
    )

    resp = await RestKrDerivatives.kr_futures_board(httpClient, '')
    print(resp.content)

if __name__ == "__main__":
    run_system(main())
