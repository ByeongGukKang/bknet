
from bknet.src import MACRO_ASYNC_YIELD, run_system
from bknet.bitget.futures.stream import BitgetWsPublic, InstType, PublicChannel


async def main():
    wsClient = await BitgetWsPublic.New(
        on_connected = lambda: print("Websocket connected"),
        on_disconnected = lambda: print("Websocket disconnected"),
        on_frame = lambda frame: print(f"Received frame: {frame.get_payload_as_utf8_text()}")
    )
    wsClient.subscribe(InstType.USDT_FUTURES, PublicChannel.Trade, 'BTCUSDT')

    while True:
        await MACRO_ASYNC_YIELD()

if __name__ == "__main__":  
    run_system(main())

