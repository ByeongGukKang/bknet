import asyncio
import weakref
from typing import Callable, Dict, Optional, Self

from gufo.http import RequestMethod, Response
from gufo.http.async_client import HttpClient
from orjson import loads as orjson_loads
from picows import WSFrame

from bknet.src import ForceAsyncNew, HttpWrapper, WebsocketWrapper


class HypeHttpClient(HttpWrapper, ForceAsyncNew):
    """Http client for Hyperliquid REST API.

    use .New() to create an instance of this class.
    """

    _api_limit_weight_max: int
    _api_limit_weight: int
    _api_limit_cond: asyncio.Condition

    @classmethod
    async def New(
        cls,
        url: str = "https://api.hyperliquid.xyz",
        *args,
        **kwargs,
    ) -> Self:
        """Http client for Hyperliquid REST API."""
        instance = cls(cls._prevented)
        instance.bg_tasks = set()

        instance.client = HttpClient(*args, **kwargs)
        instance.client.headers = {"Content-Type": b"application/json"}
        instance.url = url

        instance._api_limit_weight_max = 1200
        instance._api_limit_weight = 1200
        instance._api_limit_cond = asyncio.Condition()

        async def _refresh_api_limit():
            weight_refill_per_period = 2  # 1200 weight per 1 minute = 1200 weight per 60 seconds = 20 weight per second
            try:
                while True:
                    await asyncio.sleep(
                        0.1
                    )  # Sleep for 100ms to refill the API limit weight
                    if instance._api_limit_weight == instance._api_limit_weight_max:
                        continue
                    async with instance._api_limit_cond:
                        instance._api_limit_weight = min(
                            instance._api_limit_weight_max,
                            instance._api_limit_weight + weight_refill_per_period,
                        )
                        instance._api_limit_cond.notify_all()
            except asyncio.CancelledError:
                pass

        task = asyncio.create_task(_refresh_api_limit())
        instance.bg_tasks.add(task)
        task.add_done_callback(instance.bg_tasks.discard)
        # automatically stop the background task when the instance is garbage collected
        weakref.finalize(instance, task.cancel)

        return instance

    async def api_limit_acquire(self, weight: int):
        async with self._api_limit_cond:
            while self._api_limit_weight < weight:
                await self._api_limit_cond.wait()
            self._api_limit_weight -= weight

    async def request(  # type: ignore
        self,
        weight: int,
        method: RequestMethod,
        params: Optional[str] = None,
        body: Optional[bytes] = None,
        headers: Optional[Dict[str, bytes]] = None,
        timeout: float = 1.0,
    ) -> Response:
        """Make an authenticated request to the Hyperliquid API, respecting the API rate limit.

        Args:
            weight: The weight of the API request. The API rate limit is based on the total weight of requests made in a 10-minute window. If the total weight exceeds 1200, further requests will be blocked until the weight drops below the limit.
            method: HTTP method for the request (e.g., GET, POST).
            params: URL parameters to append to the base URL. Optional.
            body: Request body as bytes. Optional.
            headers: Additional headers to include in the request. Optional.
            timeout: Maximum time to wait for an available API slot based on the rate limit. If the timeout is reached, a RuntimeError is raised. Default is 1.0.

        Returns:
            Response object from the HTTP request.

        Raises:
            RuntimeError: If the API rate limit is exceeded and the timeout is reached.
        """
        try:
            await asyncio.wait_for(
                self.api_limit_acquire(weight), timeout=timeout
            )  # Wait for an available API slot based on the rate limit
        except (asyncio.TimeoutError, TimeoutError):
            raise RuntimeError(
                f"API rate limit exceeded. Failed to acquire {weight} weight within {timeout}s."
            )
        return await self.client.request(
            method,
            f"{self.url}{params}" if (params is not None) else self.url,
            body,
            headers if (headers is not None) else self.client.headers,
        )

    async def request_unsafe(
        self,
        method: RequestMethod,
        params: Optional[str] = None,
        body: Optional[bytes] = None,
        headers: Optional[Dict[str, bytes]] = None,
    ) -> Response:
        """unsafe, Make an authenticated request to the Hyperliquid API.

        Args:
            method: HTTP method for the request (e.g., GET, POST).
            params: URL parameters to append to the base URL. Optional.
            body: Request body as bytes. Optional.
            headers: Additional headers to include in the request. Optional.

        Returns:
            Response object from the HTTP request.

        Note:
            This method does not respect the API rate limit and should be used with caution.
            It bypasses weight-checking and avoids any Task/Future allocation, maximizing performance.
        """
        return await self.client.request(
            method,
            f"{self.url}{params}" if (params is not None) else self.url,
            body,
            headers if (headers is not None) else self.client.headers,
        )


class HypeWsClient(WebsocketWrapper):
    """Websocket client for Hyperliquid websocket API.

    use .New() to create an instance of this class.
    """

    _callbacks: dict[str, Callable[[Self, Dict], None]]
    """Dictionary mapping channel names to callback functions. The callback function is called when a message with the corresponding channel is received. Signature of callback functions: (HypeWsClient, Dict) -> None"""
    _callback_default: Callable[[Self, Dict], None]
    """Default callback function that is called when a message with an unregistered channel is received. Signature: (HypeWsClient, Dict) -> None"""

    @classmethod
    async def New(
        cls,
        on_connected: Callable[[Self], None] = lambda self: None,
        on_disconnected: Callable[[Self], None] = lambda self: None,
        on_frame: Dict[str, Callable[[Self, Dict], None]] = {},
        on_frame_default: Callable[[Self, Dict], None] = lambda self, msg: None,
        url: str = "wss://api.hyperliquid.xyz/ws",
    ) -> Self:
        """Websicjet client for Hyperliquid websocket API.

        Args:
            on_connected: Callback function that is called when the websocket connection is established. Signature: (HypeWsClient) -> None
            on_disconnected: Callback function that is called when the websocket connection is disconnected. Signature: (HypeWsClient) -> None
            on_frame: Dictionary mapping channel names to callback functions. The callback function is called when a message with the corresponding channel is received. Signature of callback functions: (HypeWsClient, Dict) -> None
            on_frame_default: Default callback function that is called when a message with an unregistered channel is received. Signature: (HypeWsClient, Dict) -> None
            url: Websocket URL to connect to. Default is "wss://api.hyperliquid.xyz/ws".
        """
        instance = await cls._new(
            on_connected, on_disconnected, cls._on_frame_wrapper, url
        )
        instance._callbacks = {}
        instance._callbacks.update(on_frame)
        instance._callback_default = on_frame_default

        # Initialize auto ping-pong
        async def _auto_ping():
            while True:
                await asyncio.sleep(30)
                instance.send_text('{"method":"ping"}')

        task = asyncio.create_task(_auto_ping())
        instance.bg_tasks.add(task)
        task.add_done_callback(instance.bg_tasks.discard)
        weakref.finalize(instance, task.cancel)
        return instance

    def _on_frame_wrapper(self, frame: WSFrame):
        msg = orjson_loads(frame.get_payload_as_memoryview())
        channel = msg.get("channel", "")
        callback = self._callbacks.get(channel, None)
        if callback is not None:
            callback(self, msg["data"])
        elif channel == "pong":
            pass  # ignore pong messages
        else:
            self._callback_default(self, msg)

    def set_callbacks(
        self,
        on_connected: Optional[Callable[[Self], None]] = None,
        on_disconnected: Optional[Callable[[Self], None]] = None,
        on_frame: Optional[Dict[str, Callable[[Self, Dict], None]]] = None,
        on_frame_default: Optional[Callable[[Self, Dict], None]] = None,
    ):
        if on_connected is not None:
            self.on_ws_connected = on_connected
        if on_disconnected is not None:
            self.on_ws_disconnected = on_disconnected
        if on_frame is not None:
            self._callbacks.update(on_frame)
        if on_frame_default is not None:
            self._callback_default = on_frame_default

    def subscribe(self, message: str):
        """Send a subscribe message to the websocket server.

        https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions
        """
        self.send_text(f'{{"method":"subscribe","subscription":{message}}}')
