from peewee import (
    MySQLDatabase, Model, BigIntegerField, DecimalField, AutoField, SmallIntegerField, DatabaseProxy, CharField
)

from .base import BaseModel

class CronJob(BaseModel):
    # fields
    execution_interval_seconds = BigIntegerField(null=False)
    last_executed_at = BigIntegerField(null=True)
    name = CharField(null=False, unique=True)

    class Meta:
        table_name = 'cron_jobs'

    # --- validation ---

    def validate(self) -> bool:
        if not super().validate():
            return False

        # name
        if self.name == '':
            self.add_error("name", f"Name cannot be blank: '{self.name}'")
        if self.id is None:
            #print(f"1: {self.select().where(self.__class__.name == self.name).exists()} , '{self.name}'")
            if self.select().where(self.__class__.name == self.name).exists():
                self.add_error("name", f"Name already exists: '{self.name}'")
        else:
            if self.select().where((self.__class__.name == self.name) & (self.__class__.id != self.id)).exists():
                self.add_error("name", f"Name already exists: '{self.name}'")

        # execution_interval_seconds
        if self.execution_interval_seconds is None:
            self.add_error("execution_interval_seconds",
                           f"Execution interval (seconds) cannot be None: '{self.execution_interval_seconds}'")
        else:
            if not isinstance(self.execution_interval_seconds, int):
                self.add_error("execution_interval_seconds",
                               f"Execution interval (seconds) must be int: '{self.execution_interval_seconds}'")
            else:
                if self.execution_interval_seconds < 60:
                    self.add_error("execution_interval_seconds", f"Execution interval (seconds) cannot be less then 0: '{self.execution_interval_seconds}'")

        return len(self._validation_errors) == 0

    # --- utilities ---
    def as_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "execution_interval_seconds": int(self.execution_interval_seconds),
            "last_executed_at": int(self.last_executed_at),
            "name": self.name,
        }
