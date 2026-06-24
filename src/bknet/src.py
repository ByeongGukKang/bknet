import asyncio
import sys
import time
from abc import abstractmethod
from collections import deque
from dataclasses import dataclass, field
from inspect import iscoroutinefunction
from types import coroutine
from typing import Callable, Coroutine, Dict, Generic, Optional, Self, TypeVar

import whenever
from gufo.http import RequestMethod, Response
from gufo.http.async_client import HttpClient as gufoHttpClient
from picows import WSFrame, WSListener, WSMsgType, WSTransport, ws_connect

T = TypeVar("T")


### Macros
class Macro:
    @staticmethod
    def as_async(func):
        if iscoroutinefunction(func):
            return func

        async def _coro(*args, **kwargs):
            return func(*args, **kwargs)

        return _coro

    @staticmethod
    async def async_sleep(seconds: float):
        return await asyncio.sleep(seconds)

    @staticmethod
    async def async_yield():
        return coroutine(lambda: (yield))

    @staticmethod
    def async_schedule(
        coro: Callable[..., Coroutine],
        bg_task_set: set[asyncio.Task],
        *args,
        **kwargs,
    ):
        """Run a coroutine in the background and add it to the provided set of background tasks.

        Args:
            coro: The coroutine function to run in the background.
            bg_task_set: A set to which the created background task will be added. The task will be automatically removed from the set when it is done.
            *args: Positional arguments to pass to the coroutine function.
            **kwargs: Keyword arguments to pass to the coroutine function.
        """
        task = asyncio.get_running_loop().create_task(coro(*args, **kwargs))
        bg_task_set.add(task)
        task.add_done_callback(bg_task_set.discard)

    @staticmethod
    def async_chain(
        coro1: Callable[..., Coroutine],
        coro2: Callable[..., Coroutine],
        after: Optional[float] = None,
        coro1_args: Optional[tuple] = None,
        coro2_args: Optional[tuple] = None,
    ) -> Callable[[], Coroutine]:
        async def chain():
            await coro1(*(coro1_args or ()))
            if after is not None:
                await asyncio.sleep(after)
            await coro2(*(coro2_args or ()))

        return chain

    @staticmethod
    def async_add_callback(
        coro: Callable[..., Coroutine],
        callback: Callable,
        coro_args: Optional[tuple] = None,
        callback_args: Optional[tuple] = None,
    ) -> Callable[[], Coroutine]:
        async def wrapper():
            result = await coro(*(coro_args or ()))
            callback(*(callback_args or ()))
            return result

        return wrapper

    @staticmethod
    def sleep(seconds: float):
        time.sleep(seconds)

    @staticmethod
    def timestamp_ms():
        return time.time_ns() // 1_000_000

    @staticmethod
    def timestamp_ns():
        return time.time_ns()

    @staticmethod
    def nowutc() -> whenever.Instant:
        return whenever.Instant.now()

    @staticmethod
    def nowtz(tz: str) -> whenever.ZonedDateTime:
        """Get the current datetime in the specified timezone.

        Args:
            tz (str): The timezone to get the current datetime in. e.g.) "Asia/Seoul"
        """
        return whenever.Instant.now().to_tz(tz)

    @staticmethod
    def timedelta(
        weeks: float = 0,
        days: float = 0,
        hours: float = 0,
        minutes: float = 0,
        seconds: float = 0,
        milliseconds: float = 0,
        microseconds: float = 0,
        nanoseconds: int = 0,
        days_assumed_24h_ok: bool = True,
    ) -> whenever.TimeDelta:
        return whenever.TimeDelta(
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            milliseconds=milliseconds,
            microseconds=microseconds,
            nanoseconds=nanoseconds,
            days_assumed_24h_ok=days_assumed_24h_ok,
        )

    @staticmethod
    def nowutc_str() -> str:
        return whenever.Instant.now().format("YYYY-MM-DD hh:mm:ss.ffffff")

    @staticmethod
    def nowtz_str(tz: str) -> str:
        """Get the current datetime in the specified timezone as a formatted string.

        Args:
            tz (str): The timezone to get the current datetime in. e.g.) "Asia/Seoul"
        """
        return whenever.Instant.now().to_tz(tz).format("YYYY-MM-DD hh:mm:ss.ffffff")


def run_system(main: Coroutine):
    match sys.platform:
        case "win32":
            import winloop

            asyncio.set_event_loop(winloop.new_event_loop())
        case "linux" | "darwin":
            import uvloop  # type: ignore

            asyncio.set_event_loop(uvloop.new_event_loop())
        case _:
            pass
    asyncio.run(main)


def async_schedule(
    coro: Callable[..., Coroutine],
    bg_task_set: set[asyncio.Task],
    *args,
    **kwargs,
):
    """Run a coroutine in the background and add it to the provided set of background tasks.

    Args:
        coro: The coroutine function to run in the background.
        bg_task_set: A set to which the created background task will be added. The task will be automatically removed from the set when it is done.
        *args: Positional arguments to pass to the coroutine function.
        **kwargs: Keyword arguments to pass to the coroutine function.
    """
    task = asyncio.get_running_loop().create_task(coro(*args, **kwargs))
    bg_task_set.add(task)
    task.add_done_callback(bg_task_set.discard)


@dataclass(init=False, slots=True)
class MemoryPool(Generic[T]):
    slots: deque[T] = field(default_factory=deque)

    def __init__(self, type_: type, size: int):
        self.slots = deque(type_() for _ in range(size))

    def alloc(self) -> T:
        return self.slots.popleft()

    def free(self, obj: T):
        self.slots.append(obj)


class ForceAsyncNew:
    _prevented = object()
    "Use for preventing direct instantiation of classes that inherit from ForceNew. Do not use this object for any other purpose."

    def __init__(self, prevented: object, *args, **kwargs):
        if prevented is not ForceAsyncNew._prevented:
            raise TypeError(
                f"{self.__class__.__name__} cannot be instantiated directly. Use .New() instead."
            )

    @classmethod
    async def New(cls, *args, **kwargs) -> Self:
        raise NotImplementedError(
            f"{cls.__class__.__name__} does not implement the .New() method."
        )


class HttpWrapper(ForceAsyncNew):
    bg_tasks: set[asyncio.Task]
    url: str
    client: gufoHttpClient

    @abstractmethod
    async def request(
        self,
        method: RequestMethod,
        params: Optional[str] = None,
        body: Optional[bytes] = None,
        headers: Optional[Dict[str, bytes]] = None,
    ) -> Response:
        return await self.client.request(
            method,
            f"{self.url}{params}" if (params is not None) else self.url,
            body,
            headers if (headers is not None) else self.client.headers,
        )  # type: ignore


class _WebsocketClient(WSListener):
    transport: WSTransport

    @abstractmethod
    async def connect(self, **kwargs) -> tuple[WSTransport, WSListener]:
        """Establish a websocket connection to the server.

        Args:
            **kwargs: Additional keyword arguments to pass to ws_connect.

        Note:
            This method must be called before sending any data using send_byte or send_text.
            An AttributeError will be raised if send_byte or send_text is called before a successful connection is established.
        """
        raise NotImplementedError()


class WebsocketWrapper(ForceAsyncNew):
    bg_tasks: set[asyncio.Task] = set()

    disconnected_event: asyncio.Event
    "Event that is set when the websocket connection is disconnected."
    transport: WSTransport
    "Underlying transport instance for the websocket connection."
    ws_client: _WebsocketClient
    "Underlying websocket client instance."

    on_ws_connected: Callable[[Self], None]
    on_ws_disconnected: Callable[[Self], None]
    on_ws_frame: Callable[[Self, WSFrame], None]

    @classmethod
    async def _new(
        cls,
        on_connected: Callable[[Self], None],
        on_disconnected: Callable[[Self], None],
        on_frame: Callable[[Self, WSFrame], None],
        url: str,
    ) -> Self:

        instance = cls(cls._prevented)
        instance.disconnected_event = asyncio.Event()
        instance.on_ws_connected = on_connected
        instance.on_ws_disconnected = on_disconnected
        instance.on_ws_frame = on_frame

        class WebsocketClientImpl(_WebsocketClient):
            def on_ws_connected(self, transport: WSTransport):
                instance.transport = transport
                instance.disconnected_event.clear()
                instance.on_ws_connected(instance)

            def on_ws_disconnected(self, transport: WSTransport):
                instance.disconnected_event.set()
                instance.on_ws_disconnected(instance)

            def on_ws_frame(self, transport: WSTransport, frame: WSFrame):
                instance.on_ws_frame(instance, frame)

            async def connect(self, **kwargs):
                return await ws_connect(WebsocketClientImpl, url, **kwargs)

        instance.ws_client = WebsocketClientImpl()
        instance.transport, _ = await instance.ws_client.connect()
        return instance

    async def _reconnect(self):
        "Reconnect to the websocket server"
        self.transport, _ = await self.ws_client.connect()

    def reconnect(self):
        "Reconnect to the websocket server"
        async_schedule(self._reconnect, self.bg_tasks)

    def send_byte(self, data: bytes):
        """Send binary data to the websocket server.

        Args:
            data (bytes): binary data to send.

        Note:
            An AttributeError will be raised if the transport is not connected.
            This typically means the websocket is disconnected or not yet established.
        """
        self.transport.send(WSMsgType.BINARY, data)

    def send_text(self, data: str):
        """Send text data to the websocket server.

        Args:
            data (str): text data to send.

        Note:
            An AttributeError will be raised if the transport is not connected.
            This typically means the websocket is disconnected or not yet established.
        """
        self.transport.send(WSMsgType.TEXT, data.encode())
