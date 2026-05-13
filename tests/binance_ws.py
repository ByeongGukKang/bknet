import asyncio

from bknet.binance.futures.public_stream import (
    BinanceFutPublicStream,
    BinanceFutPublicStreamTr,
)
from bknet.src import MACRO_DATETIME_NOW_STR, run_system


async def main():

    wsClient = await BinanceFutPublicStream.New(
        on_connected=lambda self: print("Websocket connected"),
        on_disconnected=lambda self: print("Websocket disconnected"),
        on_frame={
            BinanceFutPublicStreamTr.Depth: lambda self, msg: print(
                f"{MACRO_DATETIME_NOW_STR()}: {msg}"
            )
        },
        on_frame_error=lambda self, err, frame: print(
            f"Error occurred: {err}\n Frame: {frame.get_payload_as_utf8_text()}"
        ),
    )
    wsClient.sub_or_unsub("SUBSCRIBE", ["btcusdt@depth5"])

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    run_system(main())
