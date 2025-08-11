from peewee import (
    CharField,
    TextField, IntegerField, SmallIntegerField
)

from cryptobot.mappers.setting_mapper import SettingMapper
from .base import BaseModel

class Setting(BaseModel):
    # fields
    the_key = CharField(max_length=40, null=False, unique=True)
    the_value = TextField(null=False)
    the_type = SmallIntegerField(default=SettingMapper.TYPE_UNKNOWN)

    class Meta:
        table_name = 'settings'

    # --- validation ---

    def validate(self) -> bool:
        if not super().validate():
            return False

        if not isinstance(self.the_key, str) or len(str(self.the_key)) == 0:
            self.add_error("the_key", "the_key must be present and be non-empty string")

        if not isinstance(self.the_value, str):
            self.add_error("the_value", "the_value must be string")

        if self.the_type not in [
            SettingMapper.TYPE_UNKNOWN,
            SettingMapper.TYPE_INT,
            SettingMapper.TYPE_FLOAT,
            SettingMapper.TYPE_DECIMAL,
            SettingMapper.TYPE_BOOL,
            SettingMapper.TYPE_STR,
        ]:
            self.add_error("the_type", f"the_type '{self.the_type}' is not supported'")

        return len(self._validation_errors) == 0

    # --- utilities ---
    def as_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "the_key": self.the_key,
            "the_value": self.the_value,
            "the_type": self.the_type,
        }

    def fill(self, data: dict, exclude=None):
        self.the_key = data.get("the_key")
        self.the_value = data.get("the_value")
        self.the_type = data.get("the_type")
        return self
