from decimal import Decimal
from typing import Any

from peewee import MySQLDatabase

from cryptobot.mappers.setting_mapper import SettingMapper
from cryptobot.models import Setting


class SettingsComponent:
    def __init__(self, db: MySQLDatabase,):
        super().__init__()
        self.data_map = {}
        self.db = db

    @classmethod
    def create(cls, db: MySQLDatabase):
        return cls(
            db=db,
        )

    def get_many(self, only_keys=None) -> dict:
        if only_keys is None:
            only_keys = []
        db_settings = Setting.select()
        if len(only_keys) > 0:
            db_settings.where(Setting.the_key.in_(only_keys))
        values: dict = {}
        for db_setting in db_settings:
            values[db_setting.the_key] = self.get(db_setting.the_key)
        return values

    def get(self, key: str = None, default=None) -> int | float | Decimal | bool | str | None:
        if key is None:
            raise ValueError("key is required")
        if key in self.data_map:
            return self.data_map[key]
        value = self._load_from_db(key=key)
        if value is not None:
            self.data_map[key] = value
            return value
        return default

    def set(self, key:str, value:int|float|Decimal|bool|str) -> None:
        if self._save_to_db(key=key, value=value):
            self.data_map[key] = value

    def _load_from_db(self, key:str) -> int|float|Decimal|bool|str|None:
        db_setting = Setting.select().where(Setting.the_key == key).first()
        if not db_setting:
            return None
        return self._map_from_db(db_setting.the_type, db_setting.the_value)

    def _map_from_db(self, the_type: str, the_value: Any) -> Any|None:
        if the_type == SettingMapper.TYPE_INT:
            return int(the_value)
        elif the_type == SettingMapper.TYPE_FLOAT:
            return float(the_value)
        elif the_type == SettingMapper.TYPE_DECIMAL:
            return Decimal(the_value)
        elif the_type == SettingMapper.TYPE_BOOL:
            return True if the_value == 'true' else False
        elif the_type == SettingMapper.TYPE_STR:
            return the_value
        else:
            return None

    def _save_to_db(self, key:str, value:int|float|Decimal|bool|str) -> int:
        db_setting = Setting.select().where(Setting.the_key == key).first()
        if not db_setting:
            raise KeyError(f"Setting with the the_key='{key}' not found")
            #return Setting().fill({'the_key': key, 'the_value': value}).save() # only preset settings, no new
        db_setting.the_value = self._map_to_db(db_setting.the_type, value)
        if db_setting.the_value is None:
            return 0
        db_setting.save()
        return db_setting.id

    def _map_to_db(self, the_type: str, value: Any) -> Any|None:
        if the_type == SettingMapper.TYPE_INT:
            return str(value)
        elif the_type == SettingMapper.TYPE_FLOAT:
            return str(value)
        elif the_type == SettingMapper.TYPE_DECIMAL:
            return Decimal(value).to_eng_string()
        elif the_type == SettingMapper.TYPE_BOOL:
            return 'true' if value == True else 'false'
        elif the_type == SettingMapper.TYPE_STR:
            return str(value)
        else:
            return None



