from decimal import Decimal

from peewee import (
    MySQLDatabase, Model, BigIntegerField, DecimalField, AutoField, SmallIntegerField, DatabaseProxy, CharField,
    ForeignKeyField
)
from mappers.order_mapper import OrderMapper
from . import Order

from .base import BaseModel

class OrderTrade(BaseModel):
    # fields
    binance_id = BigIntegerField(unique=True)
    order = ForeignKeyField(Order, backref='trades', on_delete='CASCADE')
    binance_order_id = BigIntegerField()
    symbol = BigIntegerField(default=OrderMapper.SYMBOL_UNKNOWN)
    order_list_id = BigIntegerField()
    price = DecimalField(max_digits=10, decimal_places=2, auto_round=True)
    quantity = DecimalField(max_digits=20, decimal_places=10, auto_round=True)
    quote_quantity = DecimalField(max_digits=20, decimal_places=10, auto_round=True)
    commission = DecimalField(max_digits=20, decimal_places=10, auto_round=True)
    commission_asset_char = CharField(max_length=10)
    binance_time = BigIntegerField(null=False)
    is_buyer = SmallIntegerField(null=False)
    is_maker = SmallIntegerField(null=False)
    is_best_match = SmallIntegerField(null=False)

    class Meta:
        table_name = 'order_trades'

    # --- validation ---
    def validate(self) -> bool:
        if not super().validate():
            return False

        # binance_id
        if self.binance_id is None:
            self.add_error("binance_id", "binance_id must be present")

        if self.binance_id < 0:
            self.add_error("binance_id", "binance_id must be greater than 0")

        if self.binance_id != int(self.binance_id):
            self.add_error("binance_id", "binance_id must be an integer")

        # binance_order_id
        if self.binance_order_id is None:
            self.add_error("binance_order_id", "binance_order_id must be present")

        if Order.select().where(Order.binance_order_id == self.binance_order_id).count() == 0:
            self.add_error("binance_order_id", f"Order with binance_order_id = {self.binance_order_id} must exist in db")

        # symbol
        if self.symbol not in (OrderMapper.SYMBOL_UNKNOWN, OrderMapper.SYMBOL_ETHUSDT):
            self.add_error("symbol", f"Invalid symbol value: {self.symbol}")

        # order_list_id
        if self.order_list_id is None:
            self.add_error("order_list_id", "order_list_id must be present")

        if self.order_list_id != int(self.order_list_id):
            self.add_error("order_list_id", "order_list_id must be an integer")

        # price
        if self.price is None or self.price <= 0:
            self.add_error("price", "price must be present and greater than 0")

        # quantity
        if self.quantity is None or self.quantity <= 0:
            self.add_error("quantity", "quantity must be present and greater than 0")

        # quote_quantity
        if self.quote_quantity is None or self.quote_quantity <= 0:
            self.add_error("quote_quantity", "quote_quantity must be present and greater than 0")

        return len(self._validation_errors) == 0

    # --- utilities ---
    def as_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "binance_id": self.binance_id,
            "order_id": self.order_id,
            "order": self.order,
            "binance_order_id": self.binance_order_id,
            "symbol": self.symbol,
            "order_list_id": self.order_list_id,
            "price": Decimal(self.price),
            "quantity": Decimal(self.quantity),
            "quote_quantity": Decimal(self.quote_quantity),
            "commission": Decimal(self.commission),
            "commission_asset_char": str(self.commission_asset_char),
            "binance_time": self.binance_time,
            "is_buyer": bool(self.is_buyer),
            "is_maker": bool(self.is_maker),
            "is_best_match": bool(self.is_best_match),
        }

    # --- from binance ---
    def fill_from_binance(self, data: dict):
        self.binance_id = int(data["id"])
        self.binance_order_id = int(data["orderId"])
        self.symbol = OrderMapper.map_symbol(data.get("symbol"))
        self.order_list_id = int(data.get("orderListId"))
        self.price = Decimal(data.get("price", 0) or 0)
        self.quantity = Decimal(data.get("qty", 0) or 0)
        self.quote_quantity = Decimal(data.get("quoteQty", 0) or 0)
        self.commission = Decimal(data.get("commission", 0) or 0)
        self.commission_asset_char = str(data.get("commissionAsset", '') or '')
        self.binance_time = int(data.get("time", 0) or 0)
        self.is_buyer = bool(data.get("isBuyer", False) or False)
        self.is_maker = bool(data.get("isMaker", False) or False)
        self.is_best_match = bool(data.get("isBestMatch", False) or False)
        return self
