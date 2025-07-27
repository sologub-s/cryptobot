import time
from peewee import (
    MySQLDatabase, Model, BigIntegerField, DecimalField, AutoField, SmallIntegerField, DatabaseProxy
)
from mappers.order_mapper import OrderMapper

from .db import db_proxy

def current_millis():
    return int(time.time() * 1000)

class BaseModel(Model):
    class Meta:
        database = db_proxy

class Order(BaseModel):
    # fields
    id = AutoField()
    binance_order_id = BigIntegerField()
    binance_order_type = SmallIntegerField(default=0)
    created_at = BigIntegerField(default=current_millis)
    updated_at = BigIntegerField(null=True)
    binance_created_at = BigIntegerField(null=True)
    binance_updated_at = BigIntegerField(null=True)
    symbol = BigIntegerField(default=OrderMapper.SYMBOL_UNKNOWN)
    side = SmallIntegerField(default=OrderMapper.SIDE_UNKNOWN)
    order_price = DecimalField(max_digits=10, decimal_places=2, auto_round=True)
    original_quantity = DecimalField(max_digits=20, decimal_places=10, auto_round=True)
    status = SmallIntegerField(default=OrderMapper.STATUS_UNKNOWN)
    created_by_bot = SmallIntegerField(default=0)

    class Meta:
        table_name = 'orders'

    # --- validation ---
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._validation_errors = {}

    def add_error(self, field: str, message: str):
        if field not in self._validation_errors:
            self._validation_errors[field] = []
        self._validation_errors[field].append(message)

    def validate(self) -> bool:
        self._validation_errors = {}

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

    def is_valid(self) -> bool:
        return self.validate()

    def get_validation_errors(self):
        return self._validation_errors

    # --- save & touch ---
    def save(self, *args, **kwargs):
        self.updated_at = current_millis()
        if not self.validate():
            return False
        return super().save(*args, **kwargs)

    def upsert(self):
        data = self.__data__.copy()
        data.pop('id', None)
        data.pop('created_at', None)

        row_id = Order.insert(**data).on_conflict(
            update=data
        ).execute()

        if row_id != 0:
            self.id = row_id
        elif self.id is None:
            existing = Order.get(Order.binance_order_id == self.binance_order_id)
            self.id = existing.id

        return self.id

    def touch(self):
        self.updated_at = current_millis()
        return super().save(only=[Order.updated_at])

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
            "order_price": float(self.order_price) if self.order_price else None,
            "original_quantity": float(self.original_quantity) if self.original_quantity else None,
            "status": self.status,
            "created_by_bot": bool(self.created_by_bot),
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
        self.order_price = float(data.get("price", 0) or 0)
        self.original_quantity = float(data.get("origQty", 0) or 0)
        self.status = OrderMapper.map_status(data.get("status"))
        return self
