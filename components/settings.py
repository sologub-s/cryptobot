from decimal import Decimal

from peewee import MySQLDatabase

from mappers.setting_mapper import SettingMapper
from models import Setting


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
        if db_setting.the_type == SettingMapper.TYPE_INT:
            return int(db_setting.the_value)
        elif db_setting.the_type == SettingMapper.TYPE_FLOAT:
            return float(db_setting.the_value)
        elif db_setting.the_type == SettingMapper.TYPE_DECIMAL:
            return Decimal(db_setting.the_value)
        elif db_setting.the_type == SettingMapper.TYPE_BOOL:
            return True if db_setting.the_value == 'true' else False
        elif db_setting.the_type == SettingMapper.TYPE_STR:
            return db_setting.the_value
        else:
            return None

    def _save_to_db(self, key:str, value:int|float|Decimal|bool|str) -> int:
        db_setting = Setting.select().where(Setting.the_key == key).first()
        if not db_setting:
            raise KeyError(f"Setting with the the_key='{key}' not found")
            #return Setting().fill({'the_key': key, 'the_value': value}).save() # only preset settings, no new
        if db_setting.the_type == SettingMapper.TYPE_INT:
            db_setting.the_value = str(value)
        elif db_setting.the_type == SettingMapper.TYPE_FLOAT:
            db_setting.the_value = str(value)
        elif db_setting.the_type == SettingMapper.TYPE_DECIMAL:
            db_setting.the_value = Decimal(value).to_eng_string()
        elif db_setting.the_type == SettingMapper.TYPE_BOOL:
            db_setting.the_value = 'true' if value == True else 'false'
        elif db_setting.the_type == SettingMapper.TYPE_STR:
            db_setting.the_value = str(value)
        else:
            return 0
        db_setting.save()
        return db_setting.id


