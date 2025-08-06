from decimal import Decimal

from peewee import (
    MySQLDatabase, Model, BigIntegerField, DecimalField, AutoField, SmallIntegerField, DatabaseProxy
)
from mappers.order_mapper import OrderMapper

from .base import BaseModel

class Order(BaseModel):
    # fields
    binance_order_id = BigIntegerField()
    binance_order_type = SmallIntegerField(default=0)
    binance_created_at = BigIntegerField(null=True)
    binance_updated_at = BigIntegerField(null=True)
    symbol = BigIntegerField(default=OrderMapper.SYMBOL_UNKNOWN)
    side = SmallIntegerField(default=OrderMapper.SIDE_UNKNOWN)
    order_price = DecimalField(max_digits=10, decimal_places=2, auto_round=True)
    original_quantity = DecimalField(max_digits=20, decimal_places=10, auto_round=True)
    executed_quantity = DecimalField(max_digits=20, decimal_places=10, auto_round=True)
    cummulative_quote_quantity = DecimalField(max_digits=20, decimal_places=10, auto_round=True)
    status = SmallIntegerField(default=OrderMapper.STATUS_UNKNOWN)
    created_by_bot = SmallIntegerField(default=0)
    trades_checked = SmallIntegerField(default=0)

    class Meta:
        table_name = 'orders'

    # --- validation ---

    def validate(self) -> bool:
        if not super().validate():
            return False

        if self.side not in (OrderMapper.SIDE_UNKNOWN, OrderMapper.SIDE_BUY, OrderMapper.SIDE_SELL):
            self.add_error("side", f"Invalid side value: {self.side}")

        if self.symbol not in (OrderMapper.SYMBOL_UNKNOWN, OrderMapper.SYMBOL_ETHUSDT):
            self.add_error("symbol", f"Invalid symbol value: {self.symbol}")

        valid_statuses = (
            OrderMapper.STATUS_UNKNOWN,
            OrderMapper.STATUS_NEW,
            OrderMapper.STATUS_PENDING_NEW,
            OrderMapper.STATUS_PARTIALLY_FILLED,
            OrderMapper.STATUS_FILLED,
            OrderMapper.STATUS_CANCELED,
            OrderMapper.STATUS_PENDING_CANCEL,
            OrderMapper.STATUS_REJECTED,
            OrderMapper.STATUS_EXPIRED,
            OrderMapper.STATUS_EXPIRED_IN_MATCH,
        )
        if self.status not in valid_statuses:
            self.add_error("status", f"Invalid status value: {self.status}")

        if self.order_price is None or self.order_price <= 0:
            self.add_error("order_price", "order_price must be greater than 0")

        if self.original_quantity is None or self.original_quantity <= 0:
            self.add_error("original_quantity", "original_quantity must be greater than 0")

        return len(self._validation_errors) == 0

    # --- utilities ---
    def as_dict(self):
        return {
            "id": self.id,
            "binance_order_id": self.binance_order_id,
            "binance_order_type": self.binance_order_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "binance_created_at": self.binance_created_at,
            "binance_updated_at": self.binance_updated_at,
            "symbol": self.symbol,
            "side": self.side,
            "order_price": Decimal(self.order_price) if self.order_price else None,
            "original_quantity": Decimal(self.original_quantity) if self.original_quantity else None,
            "executed_quantity": Decimal(self.executed_quantity) if self.executed_quantity else None,
            "cummulative_quote_quantity": Decimal(self.cummulative_quote_quantity) if self.cummulative_quote_quantity else None,
            "status": self.status,
            "created_by_bot": bool(self.created_by_bot),
            "trades_checked": bool(self.trades_checked),
        }

    # --- from binance ---
    def fill_from_binance(self, data: dict):
        self.binance_order_id = int(data.get("orderId", 0))
        self.binance_order_type = int(OrderMapper.map_type(data.get("type", 0)))
        if self.binance_created_at is None:
            self.binance_created_at = int(data.get("updateTime", 0))
        self.binance_updated_at = int(data.get("updateTime", 0))
        self.symbol = OrderMapper.map_symbol(data.get("symbol"))
        self.side = OrderMapper.map_side(data.get("side"))
        self.order_price = Decimal(data.get("price", 0) or 0)
        self.original_quantity = Decimal(data.get("origQty", 0) or 0)
        self.executed_quantity = Decimal(data.get("executedQty", 0) or 0)
        self.cummulative_quote_quantity = Decimal(data.get("cummulativeQuoteQty", 0) or 0)
        self.status = OrderMapper.map_status(data.get("status"))
        return self
