from helpers.time import current_millis
from peewee import (
    MySQLDatabase, Model, BigIntegerField, DecimalField, AutoField, SmallIntegerField, DatabaseProxy
)

from .db import db_proxy

class BaseModel(Model):
    class Meta:
        database = db_proxy

    id = AutoField()
    created_at = BigIntegerField(default=current_millis)
    updated_at = BigIntegerField(null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._validation_errors = {}

    def add_error(self, field: str, message: str):
        if field not in self._validation_errors:
            self._validation_errors[field] = []
        self._validation_errors[field].append(message)

    def validate(self) -> bool:
        self._validation_errors = {}
        return True

    def is_valid(self) -> bool:
        return self.validate()

    def get_validation_errors(self):
        return self._validation_errors

    # --- save & touch ---
    def save(self, *args, **kwargs):
        if self.id is not None:
            self.updated_at = current_millis()
        if not self.validate():
            return False
        return super().save(*args, **kwargs)

    def upsert(self):
        data = self.__data__.copy()
        data.pop('id', None)
        data.pop('created_at', None)

        row_id = self.__class__.insert(**data).on_conflict(
            update=data
        ).execute()

        if row_id != 0:
            self.id = row_id
        elif self.id is None:
            existing = self.__class__.get(self.__class__.binance_order_id == self.binance_order_id)
            self.id = existing.id

        return self.id

    def touch(self):
        self.updated_at = current_millis()
        return super().save(only=[self.__class__.updated_at])

    def fill(self, data: dict, exclude=None):
        if exclude is None:
            exclude = [
                self.__class__.id.name,
                self.__class__.created_at.name,
                self.__class__.updated_at.name,
            ]

        for field in self._meta.fields:
            if field in exclude:
                continue
            print(f"field: {field}")
            if field in data:
                print(f"field: {field} : {data[field]}")
                setattr(self, field, data[field])
        return self

    def as_dict(self) -> dict:
        pass