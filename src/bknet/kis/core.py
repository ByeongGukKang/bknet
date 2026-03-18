import datetime
from typing import Callable, Self, Tuple

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from gufo.http import RequestMethod, Response
from gufo.http.async_client import HttpClient
from orjson import loads as orjson_loads
from picows import WSFrame
from pybase64 import b64decode

from bknet.src import ForceNew, HttpWrapper, WebsocketWrapper
from bknet.kis.tr_websocket import WebsocketTr


class KisHttpClient(HttpWrapper, ForceNew):
    """Http client for KIS open API.
    
    use .New() classmethod to create an instance of this class.
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

    @classmethod
    async def New(
        cls, 
        appkey: str,
        appsecret: str,
        custtype: str = 'P',
        url: str = 'https://openapi.koreainvestment.com:9443',
        *args, **kwargs
    ):
        """Http client for KIS open API.
        
        Args:
            appkey: API app key issued by KIS.
            appsecret: API app secret issued by KIS.
            custtype: Customer type. 'P' for individual, 'B' for corporate. Default is 'P'.
            url: Base URL for the KIS open API. Default is 'https://openapi.koreainvestment.com:9443'.
        """
        instance = cls(cls._prevented)
        instance.client = HttpClient(*args, **kwargs)
        instance.url = url

        instance.appkey = appkey
        instance.appsecret = appsecret
        instance.custtype = custtype
        await instance.connect()
        return instance

    async def connect(self):
        """Authenticate with the KIS open API and obtain the necessary tokens for API access and websocket connection.
        """
        # Get OAuth2 token
        resp: Response = await self.request(
            method = RequestMethod.POST, # type: ignore
            params = '/oauth2/tokenP',
            body = f'{{"grant_type":"client_credentials","appkey":"{self.appkey}","appsecret":"{self.appsecret}"}}'.encode(),
            headers = {'content-type': b'application/json; charset=utf-8'}
        )
        resp_json = orjson_loads(resp.content)
        self.auth_token: str = resp_json['access_token']
        self.auth_token_expiry: datetime.datetime = datetime.datetime.now() + datetime.timedelta(seconds=int(resp_json['expires_in'])-60) # 1 minute buffer

        # Get Websocket Access Key
        resp: Response = await self.request(
            method = RequestMethod.POST, # type: ignore
            params = '/oauth2/Approval',
            body = f'{{"grant_type":"client_credentials","appkey":"{self.appkey}","secretkey":"{self.appsecret}"}}'.encode(),
            headers = {'content-type': b'application/json; charset=utf-8'}
        )
        self.websocket_key: str = orjson_loads(resp.content)['approval_key']

        # Set default headers for authenticated requests
        self.client.headers = {
            'content-type': b'application/json; charset=utf-8',
            'authorization': f'Bearer {self.auth_token}'.encode(),
            'appkey':    self.appkey.encode(),
            'appsecret': self.appsecret.encode(),
            'custtype':  self.custtype.encode(),
            'tr_id': b'', # to be set per-request
        }

    async def kr_future_board(self, mrkt_cls_code: str):
        """국내옵션전광판_선물

        Args:
            mrkt_cls_code: 시장구분코드
                - 공백: KOSPI200
                - MKI: 미니 KOSPI200
                - WKM: KOSPI200위클리(월)
                - WKI: KOSPI200위클리(목)
                - KQI: KOSDAQ150
        """
        self.client.headers['tr_id'] = b'FHPIF05030200' # type: ignore
        return await self.request(
            RequestMethod.GET, # type: ignore
            params=f'/uapi/domestic-futureoption/v1/quotations/display-board-futures?FID_COND_MRKT_DIV_CODE=F&FID_COND_SCR_DIV_CODE=20503&FID_COND_MRKT_CLS_CODE={mrkt_cls_code}',
        )
    

class KisWsClient(WebsocketWrapper):
    """Websocket client for KIS open API.
    
    use .New() classmethod to create an instance of this class.
    """
    
    http_client: KisHttpClient
    """KisHttpClient instance for authentication and websocket key management."""

    _aes_iv:  bytes  = bytes()
    """Initialization vector for AES decryption. Obtained from the first JSON message received from the websocket after connection."""
    _aes_key: bytes  = bytes()
    """Encryption key for AES decryption. Obtained from the first JSON message received from the websocket after connection."""

    _callbacks: dict[bytes, Tuple[int, Callable[[Self, list[bytes]], None]]] = {}
    """Dictionary mapping tr_id (as bytes) to a tuple of (tr_length, callback function). The callback function is called when a message with the corresponding tr_id is received. Signature of callback functions: (KisWsClient, list[bytes]) -> None"""

    @classmethod
    async def New(
        cls,
        http_client: KisHttpClient,
        on_connected: Callable[[Self], None],
        on_disconnected: Callable[[Self], None],
        on_frame: dict[type[WebsocketTr], Callable[[Self, list[bytes]], None]],
        url: str = 'ws://ops.koreainvestment.com:21000',
    ) -> KisWsClient:
        """Websocket client for KIS open API.
        
        Args:
            http_client: KisHttpClient instance for authentication and websocket key management.
            on_connected: Callback function that is called when the websocket connection is established. Signature: (KisWsClient) -> None
            on_disconnected: Callback function that is called when the websocket connection is disconnected. Signature: (KisWsClient) -> None
            on_frame: Dictionary mapping WebsocketTr classes to their corresponding callback functions. The callback functions are called when a message with the corresponding tr_id is received. Signature of callback functions: (KisWsClient, list[bytes]) -> None
            url: Websocket server URL. Default is 'ws://ops.koreainvestment.com:21000'
        """
        instance = await cls._new(on_connected, on_disconnected, cls._on_frame_wrapper, url)
        instance.http_client = http_client
        for tr, callback in on_frame.items():
            if not issubclass(tr, WebsocketTr):
                raise ValueError(f'on_frame keys must be of subclass of WebsocketTr, got {type(tr)}')
            if not callable(callback):
                raise ValueError(f'on_frame values must be of type Callable with signature (KisWsClient, list[bytes]) -> None, got {type(callback)}')
            instance._callbacks[tr.TrId.encode()] = (tr.TrLength, callback)
        return instance

    def _on_frame_wrapper(self: KisWsClient, frame: WSFrame):
        """on_frame wrapper.

        Handles decryping encrypted messages, parsing JSON messages, and dispatching messages to the appropriate callbacks based on tr_id.
        """
        msg_view = frame.get_payload_as_memoryview()

        if msg_view[0] == 123: # JSON message
            json_msg = orjson_loads(msg_view)
            header = json_msg.get('header', {})
            if header.get('tr_id', '') == 'PINGPONG':
                self.send_text(f'{{"header":{{"tr_id":"PINGPONG","datetime":"{header.get("datetime", "")}"}}}}')
                return
            body = json_msg.get('body', {})
            if body.get('rt_cd', '') == '1': # Error message
                return 
            if len(self._aes_iv) == 0:
                self._aes_iv  = body.get('output', {}).get('iv', '').encode('utf-8')
                self._aes_key = body.get('output', {}).get('key', '').encode('utf-8')
                return
            # Else
            return

        msg_byte = msg_view[15:].tobytes()
        if msg_view[0] == 49: # Decrypt message
            msg_byte = unpad(AES.new(self._aes_key, AES.MODE_CBC, self._aes_iv).decrypt(b64decode(msg_byte)), 16)
        
        trlen, callback = self._callbacks.get(
            msg_view[2:10].tobytes(), # tr_id is located at bytes 2-9 of the raw message
            (0, lambda client, msg: print('Callback not found for tr_id:', msg_view[2:10].tobytes()))
        )

        msg_cnt = int(msg_view[11:14])
        msg_splited = msg_byte.split(b'^')
        if msg_cnt == 1:
            callback(self, msg_splited)
            return
        for i in range(msg_cnt):
            callback(self, msg_splited[i*trlen:(i+1)*trlen])

    def subscribe(self, tr_id: str, tr_key: str):
        """실시간 데이터 구독 등록

        Args:
            tr_id: 거래ID
            tr_key: 구분값
        """
        self.send_text(
            f'{{'
            f'"header":{{"approval_key":"{self.http_client.websocket_key}","custtype":"{self.http_client.custtype}","tr_type":"1","content-type":"utf-8"}},'
            f'"body":{{"input":{{"tr_id":"{tr_id}","tr_key":"{tr_key}"}}}}'
            f'}}'
        )

    def unsubscribe(self, tr_id: str, tr_key: str):
        """실시간 데이터 구독 해제

        Args:
            tr_id: 거래ID
            tr_key: 구분값
        """
        self.send_text(
            f'{{'
            f'"header":{{"approval_key":"{self.http_client.websocket_key}","custtype":"{self.http_client.custtype}","tr_type":"2","content-type":"utf-8"}},'
            f'"body":{{"input":{{"tr_id":"{tr_id}","tr_key":"{tr_key}"}}}}'
            f'}}'
        )

