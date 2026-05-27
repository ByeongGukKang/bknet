import asyncio
import datetime
import weakref
from typing import Callable, Dict, Optional, Self, Tuple

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from gufo.http import RequestMethod, Response
from gufo.http.async_client import HttpClient
from orjson import loads as orjson_loads
from picows import WSFrame
from pybase64 import b64decode

from bknet.kis.tr_websocket import WebsocketTr
from bknet.src import ForceAsyncNew, HttpWrapper, WebsocketWrapper


class KisHttpClient(HttpWrapper, ForceAsyncNew):
    """Http client for KIS open API.

    use .New() to create an instance of this class.
    """

    # User initialization parameters
    appkey: str
    """API app key issued by KIS."""
    appsecret: str
    """API app secret issued by KIS."""
    custtype: str
    """Customer type. 'P' for individual, 'B' for corporate."""

    # Authentication state
    auth_token: str
    """OAuth2 access token for API authentication."""
    auth_token_expiry: datetime.datetime
    """Expiration time of the OAuth2 access token."""
    websocket_key: str
    """Websocket access key for KIS websocket connection."""

    # API rate limit management
    _api_limit_queue: asyncio.Queue[None]

    @classmethod
    async def New(
        cls,
        appkey: str,
        appsecret: str,
        custtype: str = "P",
        url: str = "https://openapi.koreainvestment.com:9443",
        api_limit: int = 17,
        *args,
        **kwargs,
    ):
        """Http client for KIS open API.

        Args:
            appkey: API app key issued by KIS.
            appsecret: API app secret issued by KIS.
            custtype: Customer type. 'P' for individual, 'B' for corporate. Default is 'P'.
            url: Base URL for the KIS open API. Default is 'https://openapi.koreainvestment.com:9443'.
            api_limit: Maximum number of API requests per second. Default is 17, which is the documented 18 - 1(buffer) for the KIS open API.
        """
        instance = cls(cls._prevented)
        instance.bg_tasks = set()
        instance.client = HttpClient(*args, **kwargs)
        instance.client.headers = {}
        instance.url = url
        instance.appkey = appkey
        instance.appsecret = appsecret
        instance.custtype = custtype
        # Initialize API rate limit queue
        instance._api_limit_queue = asyncio.Queue(maxsize=api_limit)
        for _ in range(api_limit):
            instance._api_limit_queue.put_nowait(None)

        async def _refresh_api_limit():
            try:
                while True:
                    await asyncio.sleep(1.0)  # refresh API limit every 1 second
                    while not instance._api_limit_queue.full():
                        instance._api_limit_queue.put_nowait(None)
            except asyncio.CancelledError:
                pass

        task = asyncio.create_task(_refresh_api_limit())
        instance.bg_tasks.add(task)
        task.add_done_callback(instance.bg_tasks.discard)
        # automatically cancel the API limit refresh task when the instance is garbage collected
        weakref.finalize(instance, task.cancel)

        # Connect and authenticate with the KIS open API to obtain tokens
        await instance.connect()
        return instance

    def api_limit_reached(self) -> bool:
        """Return True if the API Limit is reached."""
        return self._api_limit_queue.empty()

    async def request(
        self,
        method: RequestMethod,
        params: Optional[str] = None,
        body: Optional[bytes] = None,
        headers: Optional[Dict[str, bytes]] = None,
        timeout: float = 1.0,
    ) -> Response:
        """Make an authenticated request to the KIS open API, respecting the API rate limit.

        Args:
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
                self._api_limit_queue.get(), timeout=timeout
            )  # Wait for an available API slot based on the rate limit
        except (asyncio.TimeoutError, TimeoutError):
            raise RuntimeError("API rate limit exceeded. Please try again later.")
        return await self.client.request(
            method,
            f"{self.url}{params}" if (params is not None) else self.url,
            body,
            headers if (headers is not None) else self.client.headers,
        )

    async def connect(self):
        """Authenticate with the KIS open API and obtain the necessary tokens for API access and websocket connection.

        - This method internally consumes 2 API calls for authentication.
        """
        # Get OAuth2 token
        resp: Response = await self.request(  # type: ignore
            method=RequestMethod.POST,  # type: ignore
            params="/oauth2/tokenP",
            body=f'{{"grant_type":"client_credentials","appkey":"{self.appkey}","appsecret":"{self.appsecret}"}}'.encode(),
            headers={"content-type": b"application/json; charset=utf-8"},
        )
        resp_json = orjson_loads(resp.content)
        try:
            self.auth_token = resp_json["access_token"]
        except KeyError:
            raise ValueError(f"Authentication failed. Response: {resp_json}")
        self.auth_token_expiry = datetime.datetime.now() + datetime.timedelta(
            seconds=int(resp_json["expires_in"]) - 60
        )  # 1 minute buffer

        # Get Websocket Access Key
        resp: Response = await self.request(
            method=RequestMethod.POST,  # type: ignore
            params="/oauth2/Approval",
            body=f'{{"grant_type":"client_credentials","appkey":"{self.appkey}","secretkey":"{self.appsecret}"}}'.encode(),
            headers={"content-type": b"application/json; charset=utf-8"},
        )
        resp_json = orjson_loads(resp.content)
        try:
            self.websocket_key = resp_json["approval_key"]
        except KeyError:
            raise ValueError(f"Failed to obtain websocket key. Response: {resp_json}")

        # Set default headers for authenticated requests
        self.client.headers = {
            "content-type": b"application/json; charset=utf-8",
            "authorization": f"Bearer {self.auth_token}".encode(),
            "appkey": self.appkey.encode(),
            "appsecret": self.appsecret.encode(),
            "custtype": self.custtype.encode(),
            "tr_id": b"",  # to be set per-request
        }


class KisWsClient(WebsocketWrapper):
    """Websocket client for KIS open API.

    use .New() classmethod to create an instance of this class.
    """

    http_client: KisHttpClient
    """KisHttpClient instance for authentication and websocket key management."""

    _aes_iv: bytes = bytes()
    """Initialization vector for AES decryption. Obtained from the first JSON message received from the websocket after connection."""
    _aes_key: bytes = bytes()
    """Encryption key for AES decryption. Obtained from the first JSON message received from the websocket after connection."""

    _callbacks: dict[bytes, Tuple[int, Callable[[Self, list[bytes]], None]]]
    """Dictionary mapping tr_id (as bytes) to a tuple of (tr_length, callback function). The callback function is called when a message with the corresponding tr_id is received. Signature of callback functions: (KisWsClient, list[bytes]) -> None"""

    _callback_default: Callable[[Self, list[bytes]], None]
    """Default callback function that is called when a message with an unregistered tr_id is received. Signature: (KisWsClient, list[bytes]) -> None"""

    @classmethod
    async def New(
        cls,
        http_client: KisHttpClient,
        on_connected: Callable[[Self], None] = lambda self: None,
        on_disconnected: Callable[[Self], None] = lambda self: None,
        on_frame: dict[type[WebsocketTr], Callable[[Self, list[bytes]], None]] = {},
        on_frame_default: Callable[[Self, list[bytes]], None] = lambda self, msg: None,
        url: str = "ws://ops.koreainvestment.com:21000",
    ) -> "KisWsClient":
        """Websocket client for KIS open API.

        Args:
            http_client: KisHttpClient instance for authentication and websocket key management.
            on_connected: Callback function that is called when the websocket connection is established. Signature: (KisWsClient) -> None
            on_disconnected: Callback function that is called when the websocket connection is disconnected. Signature: (KisWsClient) -> None
            on_frame: Dictionary mapping WebsocketTr classes to their corresponding callback functions. The callback functions are called when a message with the corresponding tr_id is received. Signature of callback functions: (KisWsClient, list[bytes]) -> None
            url: Websocket server URL. Default is 'ws://ops.koreainvestment.com:21000'
        """
        instance = await cls._new(
            on_connected, on_disconnected, cls._on_frame_wrapper, url
        )
        instance.http_client = http_client
        instance._callbacks = {}
        for tr, callback in on_frame.items():
            if not issubclass(tr, WebsocketTr):
                raise ValueError(
                    f"on_frame keys must be of subclass of WebsocketTr, got {type(tr)}"
                )
            if not callable(callback):
                raise ValueError(
                    f"on_frame values must be of type Callable with signature (KisWsClient, list[bytes]) -> None, got {type(callback)}"
                )
            instance._callbacks[tr.TrId.encode()] = (tr.TrLength, callback)
        instance._callback_default = on_frame_default
        return instance

    def _on_frame_wrapper(self, frame: WSFrame):
        """on_frame wrapper.

        Handles decryping encrypted messages, parsing JSON messages, and dispatching messages to the appropriate callbacks based on tr_id.
        """
        msg_view = frame.get_payload_as_memoryview()

        if msg_view[0] == 123:  # JSON message
            json_msg = orjson_loads(msg_view)
            header = json_msg.get("header", {})
            if header.get("tr_id", "") == "PINGPONG":
                self.send_text(
                    f'{{"header":{{"tr_id":"PINGPONG","datetime":"{header.get("datetime", "")}"}}}}'
                )
                return
            body = json_msg.get("body", {})
            if body.get("rt_cd", "") == "1":  # Error message
                print(f"Error message received from websocket: {json_msg}")
                return
            if len(self._aes_iv) == 0:
                self._aes_iv = body.get("output", {}).get("iv", "").encode("utf-8")
                self._aes_key = body.get("output", {}).get("key", "").encode("utf-8")
                return
            # Else
            return

        msg_byte = msg_view[15:].tobytes()
        if msg_view[0] == 49:  # Decrypt message
            msg_byte = unpad(
                AES.new(self._aes_key, AES.MODE_CBC, self._aes_iv).decrypt(
                    b64decode(msg_byte)
                ),
                16,
            )

        # tr_id is located at bytes 2-9 of the raw message
        trlen, callback = self._callbacks.get(msg_view[2:10].tobytes(), (0, None))

        msg_cnt = int(msg_view[11:14])
        msg_splited = msg_byte.split(b"^")
        if callback is None:
            self._callback_default(self, msg_splited)
            return
        if msg_cnt == 1:
            callback(self, msg_splited)
            return
        for i in range(msg_cnt):
            callback(self, msg_splited[i * trlen : (i + 1) * trlen])

    def set_callbacks(
        self,
        on_connected: Optional[Callable[[Self], None]] = None,
        on_disconnected: Optional[Callable[[Self], None]] = None,
        on_frame: Optional[
            dict[type[WebsocketTr], Callable[[Self, list[bytes]], None]]
        ] = None,
        on_frame_default: Optional[Callable[[Self, list[bytes]], None]] = None,
    ):
        if on_connected is not None:
            self.on_ws_connected = on_connected  # type: ignore
        if on_disconnected is not None:
            self.on_ws_disconnected = on_disconnected  # type: ignore
        if on_frame is not None:
            for tr, callback in on_frame.items():
                if not issubclass(tr, WebsocketTr):
                    raise ValueError(
                        f"on_frame keys must be of subclass of WebsocketTr, got {type(tr)}"
                    )
                if not callable(callback):
                    raise ValueError(
                        f"on_frame values must be of type Callable with signature (KisWsClient, list[bytes]) -> None, got {type(callback)}"
                    )
                self._callbacks[tr.TrId.encode()] = (tr.TrLength, callback)
        if on_frame_default is not None:
            self._callback_default = on_frame_default

    def subscribe(self, tr_id: str, tr_key: str):
        """실시간 데이터 구독 등록

        Args:
            tr_id: 거래ID
            tr_key: 구분값
        """
        self.send_text(
            f"{{"
            f'"header":{{"approval_key":"{self.http_client.websocket_key}","custtype":"{self.http_client.custtype}","tr_type":"1","content-type":"utf-8"}},'
            f'"body":{{"input":{{"tr_id":"{tr_id}","tr_key":"{tr_key}"}}}}'
            f"}}"
        )

    def unsubscribe(self, tr_id: str, tr_key: str):
        """실시간 데이터 구독 해제

        Args:
            tr_id: 거래ID
            tr_key: 구분값
        """
        self.send_text(
            f"{{"
            f'"header":{{"approval_key":"{self.http_client.websocket_key}","custtype":"{self.http_client.custtype}","tr_type":"2","content-type":"utf-8"}},'
            f'"body":{{"input":{{"tr_id":"{tr_id}","tr_key":"{tr_key}"}}}}'
            f"}}"
        )
