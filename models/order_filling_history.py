from decimal import Decimal

from peewee import (
    MySQLDatabase, Model, BigIntegerField, DecimalField, AutoField, SmallIntegerField, DatabaseProxy
)
from mappers.order_mapper import OrderMapper

from .base import BaseModel

class OrderFillingHistory(BaseModel):
    # fields
    logged_at = BigIntegerField(null=False)
    order_id = BigIntegerField(null=False)
    status = SmallIntegerField(default=OrderMapper.STATUS_UNKNOWN)
    original_quantity = DecimalField(max_digits=20, decimal_places=10, auto_round=True)
    executed_quantity = DecimalField(max_digits=20, decimal_places=10, auto_round=True)
    cummulative_quote_quantity = DecimalField(max_digits=20, decimal_places=10, auto_round=True)

    class Meta:
        table_name = 'orders_filling_history'

    # --- validation ---

    def validate(self) -> bool:
        if not super().validate():
            return False

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

        if self.original_quantity is None or self.original_quantity <= 0:
            self.add_error("original_quantity", "original_quantity must be greater than 0")

        return len(self._validation_errors) == 0

    # --- utilities ---
    def as_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "logged_at": self.logged_at,
            "order_id": self.order_id,
            "status": self.status,
            "original_quantity": Decimal(self.original_quantity) if self.original_quantity else None,
            "executed_quantity": Decimal(self.executed_quantity) if self.executed_quantity else None,
            "cummulative_quote_quantity": Decimal(self.cummulative_quote_quantity) if self.cummulative_quote_quantity else None,
        }

    # --- from binance ---
    def fill_from_binance(self, data: dict):
        self.status = OrderMapper.map_status(data.get("status"))
        self.original_quantity = float(data.get("origQty", 0) or 0)
        self.executed_quantity = float(data.get("executedQty", 0) or 0)
        self.cummulative_quote_quantity = float(data.get("cummulativeQuoteQty", 0) or 0)
        return self
