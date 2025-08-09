from decimal import Decimal

from peewee import (
    MySQLDatabase, Model, BigIntegerField, DecimalField, AutoField, SmallIntegerField, DatabaseProxy, CharField,
    TextField
)
from mappers.order_mapper import OrderMapper

from .base import BaseModel

class Setting(BaseModel):
    # fields
    key = CharField(max_length=20, null=False)
    value = TextField(null=False)

    class Meta:
        table_name = 'settings'

    # --- validation ---

    def validate(self) -> bool:
        if not super().validate():
            return False

        if not isinstance(self.key, str) or len(str(self.key)) == 0:
            self.add_error("key", "key must be present and be non-empty string")

        if not isinstance(self.value, str):
            self.add_error("value", "value must be string")

        return len(self._validation_errors) == 0

    # --- utilities ---
    def as_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "key": self.key,
            "value": self.value,
        }

    def fill(self, data: dict, exclude=None):
        self.key = data.get("key")
        self.value = data.get("value")
        return self
