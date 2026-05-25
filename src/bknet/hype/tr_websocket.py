from typing import Dict, List, Literal, NotRequired, Optional, Tuple, TypedDict, Union

# HypeLeverage = Dict[str, Union[str, int, bool]]  # 하이퍼리퀴드 레버리지 스펙 대응
# HypeOrder = Dict[str, Union[str, int, bool]]  # 일반 주문 지정가/시장가 오브젝트 스텁
# HypePosition = Dict[str, Union[str, int, float]]  # 포지션 데이터 개별 스텁

### Websocket Market Data Types


class HypeLeverage(TypedDict):
    type: Literal["cross", "isolated"]
    "margin mode type, either 'cross' or 'isolated'"
    value: int
    "leverage multiplier (e.g., 20, 50)"
    rawUsd: NotRequired[str]
    "collateral amount in USDC, only present if isolated margin"


class HypeOrder(TypedDict):
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"
    limitPx: str
    "price"
    oid: int
    "order id"
    side: Literal["B", "A"]
    "order side, either 'B' or 'A'"
    sz: str
    "order size"
    timestamp: int
    "unix timestamp in milliseconds"


class HypePosition(TypedDict):
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"
    szi: str
    "aggregate open size"
    entryPx: Optional[str]
    "average entry price"
    leverage: HypeLeverage
    "leverage information"
    liquidationPx: Optional[str]
    "liquidation price, only present if isolated margin"
    marginUsed: str
    "aggregate margin currently used to sustain this position"
    positionValue: str
    "real-time mark-to-market value"
    returnOnEquity: str
    "return on equity, ROE"


class HypeWsLevel(TypedDict):
    px: str
    "price"
    sz: str
    "size"
    n: int
    "number of orders"


class HypeWsTrade(TypedDict):
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"
    side: Literal["B", "A"]
    "trade side, either 'B' or 'A'"
    px: str
    "price"
    sz: str
    "size"
    hash: str
    "unique identifier for the trade"
    time: int
    "unix timestamp in milliseconds"
    tid: int
    "trade ID"
    users: Tuple[str, str]
    "tuple of (buyer, seller)"


class HypeWsBook(TypedDict):
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"
    levels: Tuple[List[HypeWsLevel], List[HypeWsLevel]]
    "tuple of (bid levels, ask levels)"
    time: int
    "unix timestamp in milliseconds"


class HypeWsBbo(TypedDict):
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"
    time: int
    "unix timestamp in milliseconds"
    bbo: Tuple[Optional[HypeWsLevel], Optional[HypeWsLevel]]  # [bid, ask]
    "tuple of (bid level, ask level). If there is no bid or ask, the corresponding element will be None"


class HypeNotification(TypedDict):
    notification: str
    "System notification broadcast or error alert text raw string pushed by backend"


class HypeAllMids(TypedDict):
    mids: Dict[str, str]
    "coin -> mid_price mapping snapshot dictionary for all active listings"


class HypeCandle(TypedDict):
    t: int
    "open time in unix milliseconds"
    T: int
    "close time in unix milliseconds"
    s: str
    "coin symbol (e.g., 'xyz:SP500')"
    i: str
    "candle interval (e.g., '1m')"
    o: float
    "open price"
    c: float
    "close price"
    h: float
    "high price"
    l: float  # noqa
    "low price"
    v: float
    "volume (base unit)"
    n: int
    "number of trades"


### Websocket User Data Types


class HypeFillLiquidation(TypedDict):
    liquidatedUser: NotRequired[str]
    "liquidated user's identifier"
    markPx: float
    "mark price"
    method: Literal["market", "backstop"]
    "market: order book liquidation, backstop: clearing house liquidation"


class HypeWsFill(TypedDict):
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"
    px: str
    "price"
    sz: str
    "size"
    side: Literal["B", "A"]
    "trade side, either 'B' or 'A'"
    time: int
    "unix timestamp in milliseconds"
    startPosition: str
    "position before this fill"
    dir: str
    "used for frontend display"
    closedPnl: str
    "realized PnL from this fill"
    hash: str
    "L1 transaction hash"
    oid: int
    "order id"
    crossed: bool
    "True if taker, False if maker"
    fee: str
    "fee, negative if it's a rebate"
    tid: int
    "trade id"
    liquidation: NotRequired[HypeFillLiquidation]
    "liquidation details, only present if this fill was a liquidation"
    feeToken: str
    "the token the fee was paid in"
    builderFee: NotRequired[str]
    "amount paid to builder, also included in fee"


class HypeWsUserFills(TypedDict):
    isSnapshot: NotRequired[bool]
    "True if this data payload represents a full history snapshot, missing if incremental real-time push"
    user: str
    "user identifier"
    fills: List[HypeWsFill]
    "list of fills"


class HypeWsUserFunding(TypedDict):
    time: int
    "unix timestamp in milliseconds"
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"
    usdc: str
    "funding amount in USDC, positive if received, negative if paid"
    szi: str
    "size in quote units"
    fundingRate: str
    "funding rate"


class HypeWsLiquidation(TypedDict):
    lid: int
    "liquidation id"
    liquidator: str
    "liquidator's identifier"
    liquidated_user: str
    "liquidated user's identifier"
    liquidated_ntl_pos: str
    "notional position of the liquidated position"
    liquidated_account_value: str
    "account value of the liquidated position"


class HypeWsNonUserCancel(TypedDict):
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"
    oid: int
    "order id"


# WsUserEvent
class HypeWsUserEventFills(TypedDict):
    fills: List[HypeWsFill]
    "list of fills"


class HypeWsUserEventFunding(TypedDict):
    funding: HypeWsUserFunding
    "funding update"


class HypeWsUserEventLiquidation(TypedDict):
    liquidation: HypeWsLiquidation
    "liquidation update"


class HypeWsUserEventNonUserCancel(TypedDict):
    nonUserCancel: List[HypeWsNonUserCancel]
    "list of non-user cancellations"


HypeWsUserEvent = Union[
    HypeWsUserEventFills,
    HypeWsUserEventFunding,
    HypeWsUserEventLiquidation,
    HypeWsUserEventNonUserCancel,
]


### Order Trading & Updates


class HypeWsBasicOrder(TypedDict):
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"
    side: Literal["B", "A"]
    "order side, either 'B' or 'A'"
    limitPx: str
    "limit price, '0' for market orders"
    sz: str
    "order size"
    oid: int
    "order id"
    timestamp: int
    "order creation timestamp in unix milliseconds"
    origSz: str
    "original order size, used for tracking how much of the order has been filled"
    cloid: Optional[str]
    "client order id, optional and only present if the order was created with a client order id"


HypeOrderStatus = Literal[
    "open",  # Placed successfully
    "filled",  # Filled
    "canceled",  # Canceled by user
    "triggered",  # Trigger order triggered
    "rejected",  # Rejected at time of placement
    "marginCanceled",  # Canceled because insufficient margin to fill
    "vaultWithdrawalCanceled",  # Vaults only. Canceled due to a user's withdrawal from vault
    "openInterestCapCanceled",  # Canceled due to order being too aggressive when open interest was at cap
    "selfTradeCanceled",  # Canceled due to self-trade prevention
    "reduceOnlyCanceled",  # Canceled reduced-only order that does not reduce position
    "siblingFilledCanceled",  # TP/SL only. Canceled due to sibling ordering being filled
    "delistedCanceled",  # Canceled due to asset delisting
    "liquidatedCanceled",  # Canceled due to liquidation
    "scheduledCancel",  # API only. Canceled due to dead man's switch timeout
    "tickRejected",  # Rejected due to invalid tick price
    "minTradeNtlRejected",  # Rejected due to order notional below minimum
    "perpMarginRejected",  # Rejected due to insufficient margin
    "reduceOnlyRejected",  # Rejected due to reduce only
    "badAloPxRejected",  # Rejected due to post-only immediate match
    "iocCancelRejected",  # Rejected due to IOC not able to match
    "badTriggerPxRejected",  # Rejected due to invalid TP/SL price
    "marketOrderNoLiquidityRejected",  # Rejected due to lack of liquidity for market order
    "positionIncreaseAtOpenInterestCapRejected",  # Rejected due to open interest cap
    "positionFlipAtOpenInterestCapRejected",  # Rejected due to open interest cap
    "tooAggressiveAtOpenInterestCapRejected",  # Rejected due to price too aggressive at open interest cap
    "openInterestIncreaseRejected",  # Rejected due to open interest cap
    "insufficientSpotBalanceRejected",  # Rejected due to insufficient spot balance
    "oracleRejected",  # Rejected due to price too far from oracle
    "perpMaxPositionRejected",  # Rejected due to exceeding margin tier limit at current leverage
]


class HypeWsOrder(TypedDict):
    order: HypeWsBasicOrder
    "basic order details"
    status: HypeOrderStatus
    "order status"
    statusTimestamp: int
    "timestamp of the last status update in unix milliseconds"


### Asset Context & Macro Indicator Types


class HypeSharedAssetCtx(TypedDict):
    dayNtlVlm: float
    "day notional volume"
    prevDayPx: float
    "previous day price"
    markPx: float
    "mart price"
    midPx: NotRequired[float]
    "mid price"


class HypePerpsAssetCtx(HypeSharedAssetCtx):
    funding: float
    "cumulative funding index"
    openInterest: float
    "open interest"
    oraclePx: float
    "oracle price"


class HypeSpotAssetCtx(HypeSharedAssetCtx):
    circulatingSupply: float
    "circulating supply"


class HypeWsActiveAssetCtx(TypedDict):
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"
    ctx: HypePerpsAssetCtx
    "asset context"


class HypeWsActiveSpotAssetCtx(TypedDict):
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"
    ctx: HypeSpotAssetCtx
    "asset context"


class HypeWsActiveAssetData(TypedDict):
    user: str
    "user identifier"
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"
    leverage: HypeLeverage
    "leverage information"
    maxTradeSzs: Tuple[float, float]
    "maximum trade sizes (long, short)"
    availableToTrade: Tuple[float, float]
    "available to trade amounts (long, short)"


### TWAP Types


class HypeWsTwapSliceFill(TypedDict):
    fill: HypeWsFill
    "fill details"
    twapId: int
    "TWAP order id"


class HypeWsUserTwapSliceFills(TypedDict):
    isSnapshot: NotRequired[bool]
    "True if this data payload is an initial snapshot, False or missing if incremental real-time update"
    user: str
    "user identifier"
    twapSliceFills: List[HypeWsTwapSliceFill]
    "list of TWAP slice fills"


class HypeTwapState(TypedDict):
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"
    user: str
    "user identifier"
    side: Literal["B", "A"]
    "order side, either 'B' or 'A'"
    sz: float
    "total size"
    executedSz: float
    "executed size"
    executedNtl: float
    "executed notional"
    minutes: int
    "TWAP duration in minutes"
    reduceOnly: bool
    "True if order is designated to only close or shrink an existing position"
    randomize: bool
    "True if sub-slice time intervals are randomized to hide order presence from toxic sniping bots"
    timestamp: int
    "TWAP start time in unix milliseconds"


HypeTwapStatus = Literal["activated", "terminated", "finished", "error"]


class HypeTwapStatusInfo(TypedDict):
    status: HypeTwapStatus
    "TWAP status"
    description: str
    "termination or operational audit logging text returned from server"


class HypeWsTwapHistory(TypedDict):
    state: HypeTwapState
    "TWAP state"
    status: HypeTwapStatusInfo
    "TWAP status"
    time: int
    "unix timestamp in milliseconds"


class HypeWsUserTwapHistory(TypedDict):
    isSnapshot: NotRequired[bool]
    user: str
    "user identifier"
    history: List[HypeWsTwapHistory]
    "TWAP history list"


class HypeLeadingVault(TypedDict):
    address: str
    name: str


class HypePerpDexState(TypedDict):
    totalVaultEquity: float
    perpsAtOpenInterestCap: NotRequired[List[str]]
    leadingVaults: NotRequired[List[HypeLeadingVault]]


class HypeWebData3UserState(TypedDict):
    agentAddress: Optional[str]
    agentValidUntil: Optional[int]
    serverTime: int
    cumLedger: float
    isVault: bool
    user: str
    optOutOfSpotDusting: NotRequired[bool]
    dexAbstractionEnabled: NotRequired[bool]


class HypeWebData3(TypedDict):
    userState: HypeWebData3UserState
    perpDexStates: List[HypePerpDexState]


class HypeMarginSummary(TypedDict):
    accountValue: float
    "Authoritative total equity value of account combining cash balances and unrealized PnL fields"
    totalNtlPos: float
    "Total collective absolute dollar volume value exposure across all leverage assets legs"
    totalRawUsd: float
    "Raw uninvested liquid cash asset balance string value remaining uncollateralized"
    totalMarginUsed: float
    "Aggregated volume of collateral cash actively locked to sustain remaining inventory"


class HypeAssetPosition(TypedDict):
    type: Literal["oneWay"]
    "position mode type"
    position: HypePosition
    "active contract position"


class HypeInnerClearinghouseState(TypedDict):
    assetPositions: List[HypeAssetPosition]
    "Array storing inventory balance sheets metrics for every running open listing"
    marginSummary: HypeMarginSummary
    "General margin, value, and collateral calculations summarizing the root ledger layer"
    crossMarginSummary: HypeMarginSummary
    "Shared margin metrics allocated inside cross pooling liquidity engine structures"
    crossMaintenanceMarginUsed: float
    "Minimum absolute buffer balance required before global liquidation systems fire"
    withdrawable: float
    "Authoritative maximum size of USDC that can be immediately extracted to secondary networks via cross-bridges"


class HypeClearinghouseState(TypedDict):
    dex: str
    "exchange identifier string"
    user: str
    "querying account identifier wallet key"
    clearinghouseState: HypeInnerClearinghouseState
    "clearing house state"


class HypeOpenOrders(TypedDict):
    dex: str
    "exchange identifier string"
    user: str
    "Account identifier string for target order tree owner"
    orders: List[HypeOrder]
    "orders currently live in the book"


class HypeTwapStates(TypedDict):
    dex: str
    "exchange identifier string"
    user: str
    "Target user wallet mapping address key"
    states: List[Tuple[int, HypeTwapState]]
    "TWAP states array Tuple[TWAP id, TWAP state] for all active TWAP orders"


class HypeUserBalance(TypedDict):
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"
    token: float
    "Gross numerical inventory units held inside spot balance arrays"
    hold: str
    "Token size tightly bound inside pending spot resting limit sell structures"
    total: str
    "Net aggregations of available and locked token pools in text formatting representation"
    entryNtl: str
    "Historical cost-basis pricing threshold baseline captured for capital gains audit tracking"


class HypeSpotState(TypedDict):
    balances: List[HypeUserBalance]
    "Array tracking net inventory parameters across decentralized현물(Spot) asset layers"


class HypeWsSpotState(TypedDict):
    user: str
    "Target account tracking wallet address string"
    spotState: HypeSpotState
    "Underlying asset matrix mapping variables reflecting physical coin holdings"


class HypeWsAllDexsClearinghouseState(TypedDict):
    user: str
    "Authoritative session tracking Metamask identity key string"
    clearinghouseStates: List[Tuple[str, HypeInnerClearinghouseState]]
    "Cross venue pairs mapping specific localized trading margin limits configurations structures"


class HypeWsAllDexsAssetCtxs(TypedDict):
    ctxs: List[Tuple[str, List[HypePerpsAssetCtx]]]
    "Authoritative index map capturing macroeconomic metadata variables separated via marketplace divisions tags"


###  Hyperliquid HyperPredict Types


class HypeOutcomeSideSpec(TypedDict):
    name: str


class HypeOutcomeSpec(TypedDict):
    outcome: int
    name: str
    description: str
    sideSpecs: Tuple[HypeOutcomeSideSpec, HypeOutcomeSideSpec]


class HypeQuestionSpec(TypedDict):
    question: int
    name: str
    description: str
    fallbackOutcome: int
    namedOutcomes: List[int]
    settledNamedOutcomes: List[int]


class HypeWsOutcomeMetaUpdateCreated(TypedDict):
    outcomeCreated: HypeOutcomeSpec


class HypeWsOutcomeMetaUpdateSettled(TypedDict):
    outcomeSettled: int


class HypeWsOutcomeMetaUpdateQuestionUpdated(TypedDict):
    questionUpdated: HypeQuestionSpec


class HypeWsOutcomeMetaUpdateQuestionSettled(TypedDict):
    questionSettled: int


### Websocket User Non-Funding Ledger Update Types
# Ledger deposits, withdrawals, transfers, sub-account transfers, liquidations, vault interactions,
# spot transfers, and rewards claims that affect the user's balance but are not related to funding payments.


class HypeLiquidatedPosition(TypedDict):
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"
    szi: float
    "size"


class HypeWsDeposit(TypedDict):
    type: Literal["deposit"]
    "ledger update type classification"
    usdc: float
    "USDC amount"


class HypeWsWithdraw(TypedDict):
    type: Literal["withdraw"]
    "ledger update type classification"
    usdc: float
    "withdrawn USDC amount"
    nonce: int
    "unique cryptographic transaction nonce identifier"
    fee: float
    "layer-1 network bridge outbound transaction gas fee paid in USDC"


class HypeWsInternalTransfer(TypedDict):
    type: Literal["internalTransfer"]
    "ledger update type classification"
    usdc: float
    "transferred USDC amount"
    user: str
    "user wallet address"
    destination: str
    "recipient target master account wallet address identity code"
    fee: float
    "DEX broker processing framework internal commission tariff applied"


class HypeWsSubAccountTransfer(TypedDict):
    type: Literal["subAccountTransfer"]
    "ledger update type classification"
    usdc: float
    "transferred USDC amount migrated between master account and child sub-account matrices"
    user: str
    "source root or child sub-account node address"
    destination: str
    "destination target child or root node location address"


class HypeWsLedgerLiquidation(TypedDict):
    type: Literal["liquidation"]
    "ledger update type classification"
    accountValue: float
    "total account value at bankruptcy, represents isolated account value for isolated positions"
    leverageType: Literal["Cross", "Isolated"]
    "margin mode of the liquidated position"
    liquidatedPositions: List[HypeLiquidatedPosition]
    "list of liquidated positions"


class HypeWsVaultDelta(TypedDict):
    type: Literal["vaultCreate", "vaultDeposit", "vaultDistribution"]
    "specific strategy copy-trading vault transactional ledger movement tag"
    vault: str
    "target institutional automated vault smart contract protocol address"
    usdc: float
    "USDC allocation adjustment size locked or extracted from the vault cache pool"


class HypeWsVaultWithdrawal(TypedDict):
    type: Literal["vaultWithdraw"]
    "ledger update type classification"
    vault: str
    "target strategy vault smart contract protocol address"
    user: str
    "investor profile address extracting liquidity pools"
    requestedUsd: float
    "gross numerical capital share size volume requested for clearance"
    commission: float
    "performance sharing management fee matching builder incentive rules deducted"
    closingCost: float
    "inventory liquidation scaling impact cost tariff buffer applied by exchange"
    basis: float
    "historical baseline cost value tracking threshold bound for tax calculation purposes"
    netWithdrawnUsd: float
    "final net USDC cash balance physically transferred into customer personal wallet balance"


class HypeWsVaultLeaderCommission(TypedDict):
    type: Literal["vaultLeaderCommission"]
    "ledger update type classification"
    user: str
    "vault strategy manager or pool developer profile identifier receiving revenue share"
    usdc: float
    "aggregated performance or management dividend income collected in USDC"


class HypeWsSpotTransfer(TypedDict):
    type: Literal["spotTransfer"]
    "ledger update type classification"
    token: str
    "physical underlying spot asset naming symbol (e.g., 'PURR', 'USDC')"
    amount: float
    "gross spot inventory unit asset token size shifted"
    usdcValue: float
    "fair asset conversion valuation converted into oracle index USDC dollar metrics"
    user: str
    "spot inventory transaction sender wallet string identity"
    destination: str
    "spot inventory transaction receiver storage location database element"
    fee: float
    "spot structural transfer transaction processing fee paid"


class HypeWsAccountClassTransfer(TypedDict):
    type: Literal["accountClassTransfer"]
    "ledger update type classification"
    usdc: float
    "internal database partition balance shift cash size"
    toPerp: bool
    "True if cash migrates to Perps clearinghouse system, False if cash returns to physical Spot balance sheets"


class HypeWsSpotGenesis(TypedDict):
    type: Literal["spotGenesis"]
    "ledger update type classification"
    token: str
    "native spot token symbol name identifier"
    amount: float
    "initial system drop minting generation size distributed to user account history record"


class HypeWsRewardsClaim(TypedDict):
    type: Literal["rewardsClaim"]
    "ledger update type classification"
    amount: float
    "aggregated promotional campaign reward tokens or ecosystem programmatic rebate volume claimed"


# 태그 기반의 타입 분기(Discriminated Union)를 가능하게 만들어 주는 제로 코스트 결합 레이어
HypeWsLedgerUpdate = Union[
    HypeWsDeposit,
    HypeWsWithdraw,
    HypeWsInternalTransfer,
    HypeWsSubAccountTransfer,
    HypeWsLedgerLiquidation,
    HypeWsVaultDelta,
    HypeWsVaultWithdrawal,
    HypeWsSpotTransfer,
    HypeWsAccountClassTransfer,
    HypeWsSpotGenesis,
    HypeWsRewardsClaim,
]


class HypeWsUserNonFundingLedgerUpdate(TypedDict):
    time: int
    "unix timestamp in milliseconds"
    hash: str
    "unique layer-1 block receipt transaction hash reference code lookup text"
    delta: HypeWsLedgerUpdate
    "ledger update event"
