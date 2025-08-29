from decimal import Decimal
from time import sleep

from cryptobot.commands import AbstractCommand
from cryptobot.commands.cron_check_balance_from_binance import CronCheckBalanceFromBinanceCommand
from cryptobot.commands.cron_do_orders_updating_routine import CronDoOrdersUpdatingRoutineCommand
from cryptobot.commands.cron_notify_working import CronNotifyWorkingCommand
from cryptobot.commands.cron_update_trades_for_partially_filled_orders import \
    CronUpdateTradesForPartiallyFilledOrdersCommand
from cryptobot.components import ServiceComponent
from cryptobot.mappers.balance_mapper import BalanceMapper
from cryptobot.mappers.order_mapper import OrderMapper
from cryptobot.models import Order, CronJob
from cryptobot.views.view import View
from cryptobot.helpers import current_millis, increase_price_percent, decrease_price_percent, dec_to_str, \
    l, sg

import logging
from logging import error, info, warning

from cryptobot.views.view_helper import to_eng_string

logging.basicConfig(level=logging.INFO)

millis_on_start = current_millis() - 10000 # dirty bidlokod

class CronCommand(AbstractCommand):

    def __init__(self):
        super().__init__()
        self._view = None

    def set_payload(self, chat_id: int):
        self._payload["chat_id"] = chat_id
        self._initialized = True
        return self

    def set_deps(self, service_component: ServiceComponent, view: View):
        self._service_component = service_component
        self._view = view
        return self

    def execute(self):
        if not self._initialized:
            print(f"ERROR: Command {self.__class__.__name__} is NOT initialized")
            return False
        
        info(f"Cron execution started")

        cron_jobs_to_execute = list(
            CronJob
                .select()
                .where(
                    (CronJob.last_executed_at.is_null())
                    | (CronJob.last_executed_at + CronJob.execution_interval_seconds * 1000 <= millis_on_start)
                )
                .execute()
        )

        if len(cron_jobs_to_execute) == 0:
            info(f"Cron : no jobs to execute")

        for cron_job_to_execute in cron_jobs_to_execute:

            if cron_job_to_execute.name == 'notify-working':
                if (CronNotifyWorkingCommand()
                        .set_payload(chat_id=self._payload["chat_id"])
                        .set_deps(service_component=self._service_component, view=self._view)
                        .execute()):
                    cron_job_to_execute.last_executed_at = millis_on_start
                    cron_job_to_execute.save()
            if cron_job_to_execute.name == 'check-balance-from-binance':
                if(CronCheckBalanceFromBinanceCommand()
                        .set_payload(chat_id=self._payload["chat_id"])
                        .set_deps(service_component=self._service_component, view=self._view)
                        .execute()):
                    cron_job_to_execute.last_executed_at = millis_on_start
                    cron_job_to_execute.save()
            if cron_job_to_execute.name == 'update-trades-for-partially-filled-orders':
                if(CronUpdateTradesForPartiallyFilledOrdersCommand()
                        .set_payload(chat_id=self._payload["chat_id"])
                        .set_deps(service_component=self._service_component, view=self._view)
                        .execute()):
                    cron_job_to_execute.last_executed_at = millis_on_start
                    cron_job_to_execute.save()
            if cron_job_to_execute.name == 'do-orders-updating-routine':
                if(CronDoOrdersUpdatingRoutineCommand()
                        .set_payload(chat_id=self._payload["chat_id"])
                        .set_deps(service_component=self._service_component, view=self._view)
                        .execute()):
                    cron_job_to_execute.last_executed_at = millis_on_start
                    cron_job_to_execute.save()

        return True