import asyncio

from bknet.hype.client import HypeWsClient
from bknet.hype.tr_websocket import HypeWsBbo, HypeWsL2Book, HypeWsTrades
from bknet.src import Macro, run_system

NOWSTR = lambda: Macro.nowtz_str("Asia/Seoul")  # noqa


async def main():

    def on_frame_l2Book(self: HypeWsClient, msg: HypeWsL2Book):
        # msg: HypeWsBook = msg
        bids, asks = msg["levels"]
        bid_px = ",".join([bid["px"] for bid in bids])
        ask_px = ",".join([ask["px"] for ask in asks])
        bid_sz = ",".join([bid["sz"] for bid in bids])
        ask_sz = ",".join([ask["sz"] for ask in asks])
        bid_n = ",".join([str(bid["n"]) for bid in bids])
        ask_n = ",".join([str(ask["n"]) for ask in asks])
        print(msg["time"])
        print(ask_px)
        print(bid_px)
        # print(
        #     f"{msg['time']},{NOWSTR()},{msg['coin']}"
        #     f",{ask_px},{bid_px},{ask_sz},{bid_sz},{ask_n},{bid_n}"
        # )

    def on_frame_bbo(self: HypeWsClient, msg: HypeWsBbo):
        print(msg)

    def on_frame_trade(self: HypeWsClient, msg: list[HypeWsTrades]):
        for trd in msg:
            print(trd["time"], trd["coin"], trd["side"], trd["px"], trd["sz"])
        print()

    wsClient = await HypeWsClient.New(
        on_connected=lambda self: print("Websocket connected"),
        on_disconnected=lambda self: print("Websocket disconnected"),
        on_frame={
            "l2Book": on_frame_l2Book,  # type: ignore
            "bbo": on_frame_bbo,  # type: ignore
            "trades": on_frame_trade,  # type: ignore
        },
    )
    # wsClient.subscribe('{"type":"l2Book","coin":"xyz:SMSN"}')
    # wsClient.subscribe('{"type":"trades","coin":"xyz:SP500"}')
    wsClient.subscribe('{"type":"bbo","coin":"xyz:SP500"}')
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    run_system(main())
