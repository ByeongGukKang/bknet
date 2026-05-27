from enum import StrEnum
from typing import Callable

from picows import WSFrame

from bknet.src import WebsocketWrapper


class InstType(StrEnum):
    USDT_FUTURES = "USDT-FUTURES"
    COIN_FUTURES = "COIN-FUTURES"
    USDC_FUTURES = "USDC-FUTURES"


class PublicChannel(StrEnum):
    Candle1m = "candle1m"
    Candle5m = "candle5m"
    Candle15m = "candle15m"
    Candle30m = "candle30m"
    Candle1H = "candle1H"
    Candle4H = "candle4H"
    Candle12H = "candle12H"
    Ticker = "ticker"
    Trade = "trade"
    Books = "books"
    Books1 = "books1"
    Books5 = "books5"
    Books15 = "books15"


class PrivateChannel(StrEnum):
    Account = "account"
    AdlNotification = "adl-noti"
    CancelOrder = "cancel-order"
    Equity = "equity"
    Fill = "fill"
    HistoryPosition = "positions-history"
    Order = "orders"
    PlaceOrder = "place-order"
    Position = "positions"
    TriggerOrder = "orders-algo"


class BitgetWsPublic(WebsocketWrapper):
    @classmethod
    async def New(
        cls,
        on_connected: Callable[[], None],
        on_disconnected: Callable[[], None],
        on_frame: Callable[[WSFrame], None],
        url: str = "wss://ws.bitget.com/v2/ws/public",
    ) -> "BitgetWsPublic":
        return await cls._new(on_connected, on_disconnected, on_frame, url)  # type: ignore

    def subscribe(self, instType: InstType, channel: PublicChannel, instId: str):
        self.send_text(
            f'{{"op":"subscribe","args":[{{"instType":"{instType}","channel":"{channel}","instId":"{instId}"}}]}}'
        )

    def unsubscribe(self, instType: InstType, channel: PublicChannel, instId: str):
        self.send_text(
            f'{{"op":"unsubscribe","args":[{{"instType":"{instType}","channel":"{channel}","instId":"{instId}"}}]}}'
        )


# TODO Add Private Websocket Client
class BitgetWsPrivate(WebsocketWrapper):
    @classmethod
    async def New(
        cls,
        api_key: str,
        api_secret: str,
        on_connected: Callable[[], None],
        on_disconnected: Callable[[], None],
        on_frame: Callable[[WSFrame], None],
        url: str = "wss://ws.bitget.com/v2/ws/private",
    ) -> BitgetWsPrivate:  # noqa
        client = await cls._new(on_connected, on_disconnected, on_frame, url)  # type: ignore
        # client.ws_client.send_byte()
        return client

    def subscribe(self, instType: InstType, channel: PrivateChannel, instId: str):
        self.send_text(
            f'{{"op":"subscribe","args":[{{"instType":"{instType}","channel":"{channel}","instId":"{instId}"}}]}}'
        )

    def unsubscribe(self, instType: InstType, channel: PrivateChannel, instId: str):
        self.send_text(
            f'{{"op":"unsubscribe","args":[{{"instType":"{instType}","channel":"{channel}","instId":"{instId}"}}]}}'
        )
