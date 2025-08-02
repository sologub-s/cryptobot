class OrderMapper:
    # Symbol constants
    SYMBOL_UNKNOWN = 0
    SYMBOL_ETHUSDT = 1

    # Side constants
    SIDE_UNKNOWN = 0
    SIDE_BUY = 1
    SIDE_SELL = 2

    # Status constants
    STATUS_UNKNOWN = 0
    STATUS_NEW = 1
    STATUS_PENDING_NEW = 2
    STATUS_PARTIALLY_FILLED = 3
    STATUS_FILLED = 4
    STATUS_CANCELED = 5
    STATUS_PENDING_CANCEL = 6
    STATUS_REJECTED = 7
    STATUS_EXPIRED = 8
    STATUS_EXPIRED_IN_MATCH = 9

    # Type constants
    TYPE_UNKNOWN = 0
    TYPE_LIMIT = 1
    TYPE_MARKET = 2
    TYPE_STOP_LOSS = 3
    TYPE_STOP_LOSS_LIMIT = 4
    TYPE_TAKE_PROFIT = 5
    TYPE_TAKE_PROFIT_LIMIT = 6
    TYPE_LIMIT_MAKER = 7

    status_mapping = {
            "UNKNOWN": STATUS_UNKNOWN,
            "NEW": STATUS_NEW,
            "PENDING_NEW": STATUS_PENDING_NEW,
            "PARTIALLY_FILLED": STATUS_PARTIALLY_FILLED,
            "FILLED": STATUS_FILLED,
            "CANCELED": STATUS_CANCELED,
            "PENDING_CANCEL": STATUS_PENDING_CANCEL,
            "REJECTED": STATUS_REJECTED,
            "EXPIRED": STATUS_EXPIRED,
            "EXPIRED_IN_MATCH": STATUS_EXPIRED_IN_MATCH,
        }

    symbol_mapping = {
        'UNKNOWN': 0,
        'ETHUSDT': 1,
    }

    @classmethod
    def map_symbol(cls, symbol: str) -> int:
        if not symbol:
            return cls.SYMBOL_UNKNOWN
        symbol = symbol.upper()
        if symbol == "ETHUSDT":
            return cls.SYMBOL_ETHUSDT
        return cls.SYMBOL_UNKNOWN

    @classmethod
    def remap_symbol(cls, symbol: int) -> str|None:
        for binance_symbol in cls.symbol_mapping:
            if cls.symbol_mapping[binance_symbol] == symbol:
                return binance_symbol
        return None

    @classmethod
    def map_side(cls, side: str) -> int:
        if not side:
            return cls.SIDE_UNKNOWN
        side = side.upper()
        if side == "BUY":
            return cls.SIDE_BUY
        if side == "SELL":
            return cls.SIDE_SELL
        return cls.SIDE_UNKNOWN

    @classmethod
    def remap_side(cls, side: int) -> str|None:
        if not side:
            return None
        if side == cls.SIDE_BUY:
            return 'BUY'
        if side == cls.SIDE_SELL:
            return 'SELL'
        return None

    @classmethod
    def map_status(cls, status: str) -> int:
        if not status:
            return cls.STATUS_UNKNOWN
        status = status.upper()
        return cls.status_mapping.get(status, cls.STATUS_UNKNOWN)

    @classmethod
    def map_type(cls, type: str) -> int:
        if not type:
            return cls.TYPE_UNKNOWN
        type = type.upper()
        mapping = {
            "LIMIT": cls.TYPE_LIMIT,
            "MARKET": cls.TYPE_MARKET,
            "STOP_LOSS": cls.TYPE_STOP_LOSS,
            "STOP_LOSS_LIMIT": cls.TYPE_STOP_LOSS_LIMIT,
            "TAKE_PROFIT": cls.TYPE_TAKE_PROFIT,
            "TAKE_PROFIT_LIMIT": cls.TYPE_TAKE_PROFIT_LIMIT,
            "LIMIT_MAKER": cls.TYPE_LIMIT_MAKER,
        }
        return mapping.get(type, cls.TYPE_UNKNOWN)