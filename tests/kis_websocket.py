import asyncio

from bknet.src import run_system
from bknet.kis.core import KisHttpClient, KisWsClient
from bknet.kis.tr_websocket import WsKrxStkBook

async def main():

    httpClient = await KisHttpClient.New(
        appkey = 'appkey',
        appsecret = 'appsecret',
    )

    wsClient = await KisWsClient.New(
        http_client = httpClient,
        on_connected = lambda self: print("Websocket connected"),
        on_disconnected = lambda self: print("Websocket disconnected"),
        on_frame = {
            WsKrxStkBook: lambda self, msg: print(f"Received frame: {msg}")
        }
    )
    wsClient.subscribe(WsKrxStkBook.TrId, '005930')

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    run_system(main())
