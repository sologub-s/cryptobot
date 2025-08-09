from peewee import MySQLDatabase

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

    def get(self, key:str=None, default=None) -> str|None:
        if key is None:
            raise ValueError("key is required")
        if key not in self.data_map:
            self.data_map[key] = self._load_from_db(key=key)
        return self.data_map.get(key, default)

    def set(self, key:str, value:str) -> None:
        if self._save_to_db(key=key, value=value):
            self.data_map[key] = value

    def _load_from_db(self, key:str) -> str|None:
        db_setting = Setting.select().where(Setting.key == key).first()
        if not db_setting:
            return None
        return db_setting.value

    def _save_to_db(self, key:str, value:str) -> int:
        db_setting = Setting.select().where(Setting.key == key).first()
        if not db_setting:
            return Setting().fill({'key': key, 'value': value}).save()
        db_setting.value = value
        return db_setting.id


