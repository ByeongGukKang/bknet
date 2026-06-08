from bknet.kis.client import KisHttpClient
from bknet.kis.tr_rest import KisRestKrDerivatives
from bknet.src import run_system


async def main():

    httpClient = await KisHttpClient.New(appkey="appkey", appsecret="appsecret")

    resp = await KisRestKrDerivatives.fut_board(httpClient, "")
    print(resp.content)


if __name__ == "__main__":
    run_system(main())
