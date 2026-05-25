import asyncio

from bknet.hype.client import HypeWsClient
from bknet.src import run_system


async def main():

    wsClient = await HypeWsClient.New(
        on_connected=lambda self: print("Websocket connected"),
        on_disconnected=lambda self: print("Websocket disconnected"),
        on_frame={"l2Book": lambda self, msg: print(msg)},
    )
    wsClient.subscribe('{"type":"l2Book","coin":"xyz:SP500"}')
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    run_system(main())
