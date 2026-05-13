from enum import StrEnum
from typing import Callable, Literal, Self

from orjson import loads as orjson_loads
from picows import WSFrame

from bknet.src import WebsocketWrapper


class BinanceFutPublicStreamTr(StrEnum):
    """Transaction types for Binance Futures public stream."""

    BookTicker = "bookTicker"
    Depth = "depthUpdate"


class BinanceFutPublicStream(WebsocketWrapper):
    _callbacks: dict[str, Callable[[Self, dict], None]] = {}
    """Dictionary mapping tr(str) to callback. The callback function is called when a message with the corresponding tr is received."""

    _on_frame_error: Callable[[Self, Exception, WSFrame], None]
    __id: int = 0

    @classmethod
    async def New(
        cls,
        on_connected: Callable[[Self], None],
        on_disconnected: Callable[[Self], None],
        on_frame: dict[BinanceFutPublicStreamTr, Callable[[Self, dict], None]] = {},
        on_frame_error: Callable[
            [Self, Exception, WSFrame], None
        ] = lambda self, err, frame: None,
        url: str = "wss://fstream.binance.com/public/ws",
    ) -> Self:
        """
        Create a new instance of BinanceFutPublicStream.

        """
        instance = await cls._new(
            on_connected, on_disconnected, cls._on_frame_wrapper, url
        )
        for tr, callback in on_frame.items():
            if not isinstance(tr, BinanceFutPublicStreamTr):
                raise ValueError(
                    f"on_frame keys must be one of BinanceFutPublicStreamTr, got {tr} of type {type(tr)}"
                )
            if not callable(callback):
                raise ValueError(
                    f"on_frame values must be of type Callable with signature (BinanceFutPublicStream, dict) -> None, got {type(callback)}"
                )
            instance._callbacks[tr] = callback
        instance._on_frame_error = on_frame_error
        return instance

    def get_id(self) -> int:
        self.__id += 1
        return self.__id

    def _on_frame_wrapper(self, frame: WSFrame):
        try:
            json_data = orjson_loads(frame.get_payload_as_memoryview())
            cb = self._callbacks.get(json_data.get("e"), None)
            if cb is None:
                cb = self._callbacks.get(str(json_data.pop("id", None)), None)
                if cb is None:
                    raise ValueError(f"No callback found for tr {json_data.get('e')}")
            cb(self, json_data)
        except Exception as err:
            self._on_frame_error(self, err, frame)

    def set_on_frame(
        self,
        callbacks: dict[BinanceFutPublicStreamTr, Callable[[Self, dict], None]],
    ):
        """Set the callback function for a specific transaction type (tr).

        Args:
            callbacks (dict[BinanceFutPublicStreamTr, Callable[[Self, dict], None]]): A dictionary mapping tr to callback function. The callback function should have the signature (BinanceFutPublicStream, dict) -> None.
        """
        for tr, callback in callbacks.items():
            self._callbacks[tr] = callback

    def sub_or_unsub(
        self,
        method: Literal[
            "SUBSCRIBE",
            "UNSUBSCRIBE",
        ],
        stream_names: list[str],
        response_callback: Callable[[Self, dict], None] = lambda self, msg: None,
    ):
        """Subscribe to a specific transaction.

        Args:
            stream_names (list[str]): The name of the stream to subscribe to. For example, "btcusdt@bookTicker" for the book ticker stream of the BTCUSDT trading pair.
        """
        id_ = self.get_id()
        self._callbacks[str(id_)] = response_callback
        self.send_text(
            f'{{"method":"{method}","params":["{'","'.join(str(param) for param in stream_names)}"],"id":{id_}}}'
        )
