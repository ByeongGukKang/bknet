from typing import Dict, List, Literal, NotRequired, Optional, Tuple, TypedDict, Union

### Websocket Market Data Types


class HypeWsAllMids(TypedDict):
    mids: Dict[str, str]
    "coin -> mid_price mapping snapshot dictionary for all active listings"


class HypeWsNotification(TypedDict):
    notification: str
    "System notification broadcast or error alert text raw string pushed by backend"


class HypeWsWebData3(TypedDict):
    class _userState(TypedDict):  # type: ignore
        agentAddress: Optional[str]
        agentValidUntil: Optional[int]
        serverTime: int
        cumLedger: str
        isVault: bool
        user: str
        optOutOfSpotDusting: NotRequired[bool]
        dexAbstractionEnabled: NotRequired[bool]

    userState: _userState

    class _perpDexState(TypedDict):  # type: ignore
        totalVaultEquity: str
        perpsAtOpenInterestCap: NotRequired[List[str]]

        class _leadingVault(TypedDict):  # type: ignore
            address: str
            name: str

        leadingVaults: NotRequired[List[_leadingVault]]

    perpDexStates: List[_perpDexState]


class HypeWsTwapStates(TypedDict):
    dex: str
    "exchange identifier string"
    user: str
    "Target user wallet mapping address key"

    class _state(TypedDict):  # type: ignore
        coin: str
        "coin symbol (e.g., 'xyz:SP500')"
        user: str
        "user identifier"
        side: Literal["B", "A"]
        "order side, either 'B' or 'A'"
        sz: str
        "total size"
        executedSz: str
        "executed size"
        executedNtl: str
        "executed notional"
        minutes: int
        "TWAP duration in minutes"
        reduceOnly: bool
        "True if order is designated to only close or shrink an existing position"
        randomize: bool
        "True if sub-slice time intervals are randomized to hide order presence from toxic sniping bots"
        timestamp: int
        "TWAP start time in unix milliseconds"

    states: List[Tuple[int, _state]]
    "TWAP states array Tuple[TWAP id, TWAP state] for all active TWAP orders"


class HypeClearinghouseState(TypedDict):
    dex: str
    "exchange identifier string"
    user: str
    "querying account identifier wallet key"

    class _clearhouseState(TypedDict):  # type: ignore
        class _assetPosition(TypedDict):  # type: ignore
            type: Literal["oneWay"]
            "position mode type"

            class _position(TypedDict):  # type: ignore
                coin: str
                "coin symbol (e.g., 'xyz:SP500')"
                szi: str
                "aggregate open size"
                entryPx: Optional[str]
                "average entry price"

                class _leverage(TypedDict):  # type: ignore
                    type: Literal["cross", "isolated"]
                    value: int
                    rawUsd: NotRequired[str]

                leverage: _leverage
                "leverage information"
                liquidationPx: Optional[str]
                "liquidation price, only present if isolated margin"
                marginUsed: str
                "aggregate margin currently used to sustain this position"
                positionValue: str
                "real-time mark-to-market value"
                returnOnEquity: str
                "return on equity, ROE"

            position: _position
            "active contract position"

        assetPositions: List[_assetPosition]
        "Array storing inventory balance sheets metrics for every running open listing"

        class _marginsummary(TypedDict):  # type: ignore
            accountValue: str
            "Authoritative total equity value of account combining cash balances and unrealized PnL fields"
            totalNtlPos: str
            "Total collective absolute dollar volume value exposure across all leverage assets legs"
            totalRawUsd: str
            "Raw uninvested liquid cash asset balance string value remaining uncollateralized"
            totalMarginUsed: str
            "Aggregated volume of collateral cash actively locked to sustain remaining inventory"

        marginSummary: _marginsummary
        "General margin, value, and collateral calculations summarizing the root ledger layer"
        crossMarginSummary: _marginsummary
        "Shared margin metrics allocated inside cross pooling liquidity engine structures"
        crossMaintenanceMarginUsed: str
        "Minimum absolute buffer balance required before global liquidation systems fire"
        withdrawable: str
        "Authoritative maximum size of USDC that can be immediately extracted to secondary networks via cross-bridges"

    clearinghouseState: _clearhouseState
    "clearing house state"


class HypeOpenOrders(TypedDict):
    dex: str
    "exchange identifier string"
    user: str
    "Account identifier string for target order tree owner"

    class _order(TypedDict):  # type: ignore
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

    orders: List[_order]
    "orders currently live in the book"


class HypeCandle(TypedDict):
    t: int
    "open time in unix milliseconds"
    T: int
    "close time in unix milliseconds"
    s: str
    "coin symbol (e.g., 'xyz:SP500')"
    i: str
    "candle interval (e.g., '1m')"
    o: str
    "open price"
    c: str
    "close price"
    h: str
    "high price"
    l: str  # noqa
    "low price"
    v: str
    "volume (base unit)"
    n: int
    "number of trades"


class HypeWsl2Book(TypedDict):
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"

    class _level(TypedDict):  # type: ignore
        px: str
        "price"
        sz: str
        "size"
        n: int
        "number of orders"

    levels: Tuple[List[_level], List[_level]]
    "tuple of (bid levels, ask levels)"
    time: int
    "unix timestamp in milliseconds"


class HypeWsTrades(TypedDict):
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


class HypeWsOrderUpdates(TypedDict):
    class _order(TypedDict):  # type: ignore
        coin: str
        "coin symbol (e.g., 'xyz:SP500')"
        side: Literal["B", "A"]
        "order side, either 'B' or 'A'"
        limitPx: str
        "limit price"
        sz: str
        "size"
        oid: int
        "order ID"
        timestamp: int
        "unix timestamp in milliseconds"
        origSz: str
        "original size"
        cloid: NotRequired[str]
        "client order ID"

    order: _order
    "basic order details"
    status: Literal[
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
    "order status"
    statusTimestamp: int
    "timestamp of the last status update in unix milliseconds"


HypeWsUserEvents = Union[
    "HypeWsUserFills", "HypeWsUserFundings", "HypeWsLiquidation", "HypeWsNonUserCancel"
]


class HypeWsUserFills(TypedDict):
    isSnapshot: NotRequired[bool]
    user: str

    class _fill(TypedDict):  # type: ignore
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

        class _liquidation(TypedDict):  # type: ignore
            liquidatedUser: NotRequired[str]
            "liquidated user's identifier"
            markPx: str
            "mark price"
            method: Literal["market", "backstop"]
            "market: order book liquidation, backstop: clearing house liquidation"

        liquidation: NotRequired[_liquidation]
        "liquidation details, only present if this fill was a liquidation"
        feeToken: str
        "the token the fee was paid in"
        builderFee: NotRequired[str]
        "amount paid to builder, also included in fee"

    fills: List[_fill]
    "list of fills"


class HypeWsUserFundings(TypedDict):
    isSnapshot: NotRequired[bool]
    user: str

    class _funding(TypedDict):  # type: ignore
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

    fundings: List[_funding]
    "list of funding events"


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


class HypeWsUserNonFundingLedgerUpdates(TypedDict):
    time: int
    "unix timestamp in milliseconds"
    hash: str
    "unique layer-1 block receipt transaction hash reference code lookup text"

    class _deposit(TypedDict):  # type: ignore
        type: Literal["deposit"]
        usdc: str

    class _withdraw(TypedDict):  # type: ignore
        type: Literal["withdraw"]
        usdc: str
        nonce: int
        fee: str

    class _internalTransfer(TypedDict):  # type: ignore
        type: Literal["internalTransfer"]
        usdc: str
        user: str
        destination: str
        fee: str

    class _subAccountTransfer(TypedDict):  # type: ignore
        type: Literal["subAccountTransfer"]
        usdc: str
        user: str
        destination: str

    class _ledgerLiquidation(TypedDict):  # type: ignore
        type: Literal["liquidation"]
        accountValue: str
        leverageType: Literal["Cross", "Isolated"]

        class _liquidatedPosition(TypedDict):  # type: ignore
            coin: str
            szi: str

        liquidatedPositions: List[_liquidatedPosition]

    class _vaultDelta(TypedDict):  # type: ignore
        type: Literal["vaultCreate", "vaultDeposit", "vaultDistribution"]
        vault: str
        usdc: str

    class _vaultWithdrawal(TypedDict):  # type: ignore
        type: Literal["vaultWithdraw"]
        vault: str
        user: str
        requestedUsd: str
        commission: str
        closingCost: str
        basis: str
        netWithdrawnUsd: str

    class _vaultLeaderCommission(TypedDict):  # type: ignore
        type: Literal["vaultLeaderCommission"]
        user: str
        usdc: str

    class _spotTransfer(TypedDict):  # type: ignore
        type: Literal["spotTransfer"]
        token: str
        amount: str
        usdcValue: str
        user: str
        destination: str
        fee: str

    class _accountClassTransfer(TypedDict):  # type: ignore
        type: Literal["accountClassTransfer"]
        usdc: str
        toPerp: bool

    class _spotGenesis(TypedDict):  # type: ignore
        type: Literal["spotGenesis"]
        token: str
        amount: str

    class _rewardsClaim(TypedDict):  # type: ignore
        type: Literal["rewardsClaim"]
        amount: str

    delta: Union[
        _deposit,
        _withdraw,
        _internalTransfer,
        _subAccountTransfer,
        _ledgerLiquidation,
        _vaultDelta,
        _vaultWithdrawal,
        _vaultLeaderCommission,
        _spotTransfer,
        _accountClassTransfer,
        _spotGenesis,
        _rewardsClaim,
    ]
    "ledger update event"


class HypeWsActiveAssetCtx(TypedDict):
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"

    class _ctx_perp(TypedDict):  # type: ignore
        dayNtlVlm: str
        "day notional volume"
        prevDayPx: str
        "previous day price"
        markPx: str
        "mart price"
        midPx: NotRequired[str]
        "mid price"
        funding: str
        "cumulative funding index"
        openInterest: str
        "open interest"
        oraclePx: str
        "oracle price"

    class _ctx_spot(TypedDict):  # type: ignore
        dayNtlVlm: str
        "day notional volume"
        prevDayPx: str
        "previous day price"
        markPx: str
        "mart price"
        midPx: NotRequired[str]
        "mid price"
        circulatingSupply: str
        "circulating supply"

    ctx: Union[_ctx_perp, _ctx_spot]
    "asset context"


class HypeWsActiveAssetData(TypedDict):
    "only supports perpetual"

    user: str
    "user identifier"
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"

    class _leverage(TypedDict):  # type: ignore
        type: Literal["cross", "isolated"]
        "margin mode type, either 'cross' or 'isolated'"
        value: int
        "leverage multiplier (e.g., 20, 50)"
        rawUsd: NotRequired[str]
        "collateral amount in USDC, only present if isolated margin"

    leverage: _leverage
    "leverage information"
    maxTradeSzs: Tuple[str, str]
    "maximum trade sizes (long, short)"
    availableToTrade: Tuple[str, str]
    "available to trade amounts (long, short)"


class HypeWsUserTwapSliceFills(TypedDict):
    isSnapshot: NotRequired[bool]
    "True if this data payload is an initial snapshot, False or missing if incremental real-time update"
    user: str
    "user identifier"

    class _twapSliceFill(TypedDict):  # type: ignore
        class _fill(TypedDict):  # type: ignore
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

            class _liquidation(TypedDict):  # type: ignore
                liquidatedUser: NotRequired[str]
                "liquidated user's identifier"
                markPx: str
                "mark price"
                method: Literal["market", "backstop"]
                "market: order book liquidation, backstop: clearing house liquidation"

            liquidation: NotRequired[_liquidation]
            "liquidation details, only present if this fill was a liquidation"
            feeToken: str
            "the token the fee was paid in"
            builderFee: NotRequired[str]
            "amount paid to builder, also included in fee"

        fill: _fill
        "fill details"
        twapId: int
        "TWAP order id"

    twapSliceFills: List[_twapSliceFill]
    "list of TWAP slice fills"


class HypeWsUserTwapHistory(TypedDict):
    isSnapshot: NotRequired[bool]
    user: str
    "user identifier"

    class _history(TypedDict):  # type: ignore
        class _state(TypedDict):  # type: ignore
            coin: str
            "coin symbol (e.g., 'xyz:SP500')"
            user: str
            "user identifier"
            side: Literal["B", "A"]
            "order side, either 'B' or 'A'"
            sz: str
            "total size"
            executedSz: str
            "executed size"
            executedNtl: str
            "executed notional"
            minutes: int
            "TWAP duration in minutes"
            reduceOnly: bool
            "True if order is designated to only close or shrink an existing position"
            randomize: bool
            "True if sub-slice time intervals are randomized to hide order presence from toxic sniping bots"
            timestamp: int
            "TWAP start time in unix milliseconds"

        state: _state
        "order state"

        class _status(TypedDict):  # type: ignore
            status: Literal["activated", "terminated", "finished", "error"]
            description: str

        status: _status
        "order status"

        time: int

    history: List[_history]
    "TWAP history list"


class HypeWsBbo(TypedDict):
    coin: str
    "coin symbol (e.g., 'xyz:SP500')"
    time: int
    "unix timestamp in milliseconds"

    class _level(TypedDict):  # type: ignore
        px: str
        "price"
        sz: str
        "size"
        n: int
        "number of orders"

    bbo: Tuple[Optional[_level], Optional[_level]]  # [bid, ask]
    "tuple of (bid level, ask level). If there is no bid or ask, the corresponding element will be None"


class HypeWsSpotState(TypedDict):
    user: str
    "Target account tracking wallet address string"

    class _spotState(TypedDict):  # type: ignore
        class _balance(TypedDict):  # type: ignore
            coin: str
            "coin symbol (e.g., 'xyz:SP500')"
            token: str
            "Gross numerical inventory units held inside spot balance arrays"
            hold: str
            "Token size tightly bound inside pending spot resting limit sell structures"
            total: str
            "Net aggregations of available and locked token pools in text formatting representation"
            entryNtl: str
            "Historical cost-basis pricing threshold baseline captured for capital gains audit tracking"

        balances: List[_balance]
        "Array tracking net inventory parameters across decentralized현물(Spot) asset layers"

    spotState: _spotState
    "Underlying asset matrix mapping variables reflecting physical coin holdings"


class HypeWsAllDexsClearinghouseState(TypedDict):
    user: str
    "Authoritative session tracking Metamask identity key string"

    class _innerClearinghouseState(TypedDict):  # type: ignore
        class _assetPosition(TypedDict):  # type: ignore
            type: Literal["oneWay"]

            class _position(TypedDict):  # type: ignore
                coin: str
                "coin symbol, e.g. BTC"

                class _cumFunding(TypedDict):  # type: ignore
                    allTime: str
                    sinceChange: str
                    sinceOpen: str

                cumFunding: _cumFunding
                entryPx: str

                class _leverage(TypedDict):  # type: ignore
                    rawUsd: str
                    type: Literal["cross", "isolated"]
                    value: int

                leverage: _leverage
                liquidationPx: str
                marginUsed: str
                maxLeverage: int
                positionValue: str
                returnOnEquity: str
                szi: str
                unrealizedPnl: str

            position: _position

        assetPositions: List[_assetPosition]

        class _marginSummary(TypedDict):  # type: ignore
            accountValue: str
            totalNtlPos: str
            totalRawUsd: str
            totalMarginUsed: str

        marginSummary: _marginSummary
        crossMarginSummary: _marginSummary
        crossMaintenanceMarginUsed: str
        withdrawable: str

    clearinghouseStates: List[Tuple[str, _innerClearinghouseState]]
    "Cross venue pairs mapping specific localized trading margin limits configurations structures"


class HypeWsAllDexsAssetCtxs(TypedDict):
    class _ctx(TypedDict):  # type: ignore
        funding: str
        "cumulative funding index"
        openInterest: str
        "open interest"
        oraclePx: str
        "oracle price"

    ctxs: List[Tuple[str, List[_ctx]]]
    "Authoritative index map capturing macroeconomic metadata variables separated via marketplace divisions tags"


HypeWsOutcomeMetaUpdates = Union[
    "HypeWsOutcomeCreated",
    "HypeWsOutcomeSettled",
    "HypeWsQuestionUpdated",
    "HypeWsQuestionSettled",
]


class HypeWsOutcomeCreated(TypedDict):
    class _outcomeSpec(TypedDict):  # type: ignore
        outcome: int
        name: str
        description: str

        class _outcomeSideSpec(TypedDict):  # type: ignore
            name: str

        sideSpecs: Tuple[_outcomeSideSpec, _outcomeSideSpec]

    outcomeCreated: _outcomeSpec
    "outcome created"


class HypeWsOutcomeSettled(TypedDict):
    outcomeSettled: str


class HypeWsQuestionUpdated(TypedDict):
    class _questionSpec(TypedDict):  # type: ignore
        question: int
        name: str
        description: str
        fallbackOutcome: int
        namedOutcomes: List[int]
        settledNamedOutcomes: List[int]

    questionUpdated: _questionSpec
    "question updated"


class HypeWsQuestionSettled(TypedDict):
    questionSettled: int
