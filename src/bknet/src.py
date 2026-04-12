import asyncio
from collections import deque
from dataclasses import dataclass, field
import datetime
from inspect import iscoroutinefunction
import time
import sys
from typing import Callable, Coroutine, Dict, Optional, Self
from types import coroutine

from gufo.http import RequestMethod, Response
from gufo.http.async_client import HttpClient as gufoHttpClient

from picows import ws_connect, WSFrame, WSListener, WSMsgType, WSTransport


### Macros
def __MACRO_AS_ASYNC(func):
    if iscoroutinefunction(func):
        return func
    async def _coro(*args, **kwargs):
        return func(*args, **kwargs)
    return _coro
MACRO_AS_ASYNC = __MACRO_AS_ASYNC

MACRO_ASYNC_SLEEP = asyncio.sleep
MACRO_ASYNC_YIELD = coroutine(lambda: (yield))
MACRO_TIMESTAMP_NS = time.time_ns
MACRO_TIMESTAMP_MS = lambda: int(time.time() * 1000)
MACRO_DATETIME_NOW = datetime.datetime.now
MACRO_DATETIME_NOW_STR = lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
MACRO_DATETIME_UTCNOW = lambda: datetime.datetime.now(datetime.timezone.utc)
MACRO_DATETIME_UTCNOW_STR = lambda: datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
MACRO_PERF_COUNTER = time.perf_counter_ns


def run_system(main: Coroutine):
    match sys.platform:
        case 'win32':
            import winloop
            asyncio.set_event_loop(winloop.new_event_loop())
        case 'linux' | 'darwin':
            import uvloop # type: ignore
            asyncio.set_event_loop(uvloop.new_event_loop())
        case _:
            pass
    asyncio.run(main)


@dataclass(init=False, slots=True)
class _MemoryPool:
    slots: deque[object] = field(default_factory=deque)

    def __init__(self, type_: type, size: int):
        self.slots = deque(type_() for _ in range(size))

    def alloc(self) -> object:
        return self.slots.popleft()
    
    def free(self, obj: object):
        self.slots.append(obj)


class LoggerWithBuffer:

    def __init__(self, log_file_path: str, buffer_size: int = 256):
        self.log_file_path = log_file_path
        self.buffer: list = [None] * buffer_size
        self.buffer_size = buffer_size
        self.buffer_index = 0
        self.fileIo = open(log_file_path, 'a')

    def log(self, message: str):
        self.buffer[self.buffer_index] = message
        self.buffer_index += 1
        if self.buffer_index >= self.buffer_size:
            self.fileIo.writelines(self.buffer)
            self.buffer_index = 0

    def close(self):
        if self.buffer_index > 0:
            self.fileIo.writelines(self.buffer[:self.buffer_index])
        self.fileIo.flush()
        self.fileIo.close()


class ForceNew:

    _prevented = object()
    "Use for preventing direct instantiation of classes that inherit from ForceNew. Do not use this object for any other purpose."

    def __init__(self, prevented: object, *args, **kwargs):
        if prevented is not ForceNew._prevented:
            raise TypeError(f'{self.__class__.__name__} cannot be instantiated directly. Use .New() instead.')

class HttpWrapper(ForceNew):

    url: str
    client: gufoHttpClient

    async def request(
        self,
        method: RequestMethod,
        params: Optional[str] = None,
        body: Optional[bytes] = None,
        headers: Optional[Dict[str, bytes]] = None
    ) -> Response:
        return await self.client.request(method, f'{self.url}{params}' if (params is not None) else self.url, body, headers if (headers is not None) else self.client.headers) # type: ignore

class _WebsocketClient(WSListener):
    
    transport: WSTransport
    disconnected_event: asyncio.Event


    async def connect(self, **kwargs):
        """Establish a websocket connection to the server.

        Args:
            **kwargs: Additional keyword arguments to pass to ws_connect.

        Note:
            This method must be called before sending any data using send_byte or send_text.
            An AttributeError will be raised if send_byte or send_text is called before a successful connection is established.
        """
        raise NotImplementedError()

class WebsocketWrapper(ForceNew):

    disconnected_event: asyncio.Event
    "Event that is set when the websocket connection is disconnected."
    transport: WSTransport
    "Underlying transport instance for the websocket connection."
    ws_client: _WebsocketClient
    "Underlying websocket client instance."

    @classmethod
    async def _new(
        cls,
        on_connected: Callable[[Self], None],
        on_disconnected: Callable[[Self], None],
        on_frame: Callable[[Self, WSFrame], None],
        url: str,
    ) -> Self:
        
        instance = cls(cls._prevented)
        disconnected_event = asyncio.Event()
        instance.disconnected_event = disconnected_event

        class WebsocketClientImpl(_WebsocketClient):

            def on_ws_connected(self, transport: WSTransport):
                disconnected_event.clear()
                on_connected(instance)

            def on_ws_disconnected(self, transport: WSTransport):
                disconnected_event.set()
                on_disconnected(instance)

            def on_ws_frame(self, transport: WSTransport, frame: WSFrame):
                on_frame(instance, frame)

            async def connect(self, **kwargs):
                return await ws_connect(WebsocketClientImpl, url, **kwargs)

        instance.ws_client = WebsocketClientImpl()
        instance.transport, _ = await instance.ws_client.connect()
        return instance
    
    async def connect(self):
        await self.ws_client.connect()

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
