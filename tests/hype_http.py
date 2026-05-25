from bknet.hype.client import HypeHttpClient
from bknet.hype.tr_rest import HypeRestInfo
from bknet.src import run_system


async def main():

    httpClient = await HypeHttpClient.New()

    resp = await HypeRestInfo.perpDexs(httpClient)
    print(resp)


if __name__ == "__main__":
    run_system(main())
