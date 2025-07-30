from decimal import Decimal

from peewee import (
    MySQLDatabase, Model, BigIntegerField, DecimalField, AutoField, SmallIntegerField, DatabaseProxy, CharField
)

from helpers import current_millis
from .base import BaseModel
from mappers.balance_mapper import BalanceMapper



class Balance(BaseModel):
    # fields
    checked_at = BigIntegerField(null=False)
    asset = SmallIntegerField(null=False)
    free = DecimalField(max_digits=18, decimal_places=8, null=False,)
    locked = DecimalField(max_digits=18, decimal_places=8, null=False,)

    class Meta:
        table_name = 'balances'

    # --- validation ---

    def validate(self) -> bool:
        if not super().validate():
            return False

        # asset
        if self.asset is None:
            self.add_error("asset", f"asset cannot be blank: '{self.asset}'")
        elif self.asset not in BalanceMapper.get_assets().values():
            self.add_error("asset", f"Unknown asset: '{self.asset}'")

        # checked_at
        if self.checked_at is None:
            self.add_error("checked_at", f"checked_at cannot be blank: '{self.checked_at}'")

        # free
        if self.free is None:
            self.add_error("free", f"free cannot be blank: '{self.free}'")
        elif self.free < 0:
            self.add_error("free", f"free cannot be negative: '{self.free}'")

        # locked
        if self.locked is None:
            self.add_error("locked", f"locked cannot be blank: '{self.locked}'")
        elif self.locked < 0:
            self.add_error("locked", f"locked cannot be negative: '{self.locked}'")

        return len(self._validation_errors) == 0

    # --- utilities ---
    def as_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "checked_at": int(self.checked_at),
            "asset": int(self.asset),
            "free": Decimal(self.free),
            "locked": Decimal(self.locked),
        }
    # --- from binance ---
    def fill_from_binance(self, data: dict):
        self.checked_at = int(data.get("checked_at", current_millis()))
        self.asset = BalanceMapper.map_asset(data.get("asset"))
        self.free = float(data.get("free", 0) or 0)
        self.locked = float(data.get("locked", 0) or 0)
        return self
