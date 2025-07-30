from decimal import Decimal

from commands import AbstractCommand
from components import ServiceComponent
from mappers.balance_mapper import BalanceMapper
from mappers.order_mapper import OrderMapper
from models import Order, CronJob, Balance
from views.view import View
from helpers import find_first_key_by_value, current_millis

import logging
from logging import error, info, warning, debug
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

        handlers_list = {
            'check-all-orders-from-binance': self.handler_check_all_orders_from_binance,
            'notify-working': self.handler_notify_working,
            'check-balance-from-binance': self.handler_check_balance_from_binance,
        }

        cron_jobs_to_execute = list(
            CronJob
                .select()
                .where(
                    (CronJob.last_executed_at.is_null())
                    | (CronJob.last_executed_at + CronJob.execution_interval_seconds * 1000 <= millis_on_start)
                )
                .execute()
        )

        for cron_job_to_execute in cron_jobs_to_execute:
            handler_name: str = cron_job_to_execute.name
            if handler_name not in handlers_list:
                warning(f"Cron: Handler '{handler_name}' not found in handlers list")
                continue
            if handlers_list[handler_name]():
                cron_job_to_execute.last_executed_at = millis_on_start
                cron_job_to_execute.save()
            else:
                error(f"Cron: Cannot execute handler '{handler_name}' !")

        return True

    def handler_check_all_orders_from_binance(self) -> bool:
        info(f"Cron executing 'handler_check_all_orders_from_binance'...")
        # get all orders from db
        all_db_orders = Order.select()
        all_db_orders_indexed: dict[int, Order] = {}
        for db_order in all_db_orders:
            all_db_orders_indexed[db_order.binance_order_id] = db_order
        del all_db_orders

        # get all orders from binance
        all_binance_orders = self._service_component.get_all_orders('ETHUSDT')

        changed_orders: int = 0

        for binance_order in all_binance_orders:
            #upsert order into db if not exists
            if binance_order['orderId'] not in all_db_orders_indexed:
                all_db_orders_indexed[binance_order['orderId']] = Order().fill_from_binance(binance_order)
                all_db_orders_indexed[binance_order['orderId']].upsert()
            mapped_binance_status = OrderMapper.map_status(binance_order['status'])
            # if status has changed
            if mapped_binance_status != all_db_orders_indexed[binance_order['orderId']].status:
                # save new status to db
                previous_status: str = find_first_key_by_value(OrderMapper.status_mapping, all_db_orders_indexed[binance_order['orderId']].status, 'UNKNOWN')
                all_db_orders_indexed[binance_order['orderId']].status = mapped_binance_status
                all_db_orders_indexed[binance_order['orderId']].save()
                # update saved_orders counter
                changed_orders += 1
                # send telegram notification
                message = self._view.render('telegram/orders/order_status_changed.j2', {
                    'order': binance_order,
                    'previous_status': previous_status
                })
                keys = [
                    f"show_order_status:{binance_order['orderId']}:{binance_order['symbol']}",
                ]
                inline_keyboard: list = []
                for key in keys:
                    inline_keyboard.append([{"text": key, "callback_data": key}, ])
                self._service_component.send_telegram_message(self._payload["chat_id"], message, inline_keyboard)
                self._service_component.send_telegram_message(self._payload["chat_id"], self._view.render(
                    'telegram/or_choose_another_option.j2', {}))

        if changed_orders > 0:
            # update assets balances
            self._service_component.update_assets_from_binance_to_db(
                assets=BalanceMapper.get_assets().keys(),
                force_insert=True,
            )

        return True

    def handler_notify_working(self):
        message = self._view.render('telegram/up_and_running.j2', {})
        self._service_component.send_telegram_message(self._payload["chat_id"], message, None, True)
        return True

    def handler_check_balance_from_binance(self):
        # for all available assets
        assets_updated = self._service_component.update_assets_from_binance_to_db(
            assets=BalanceMapper.get_assets().keys(),
            force_insert=False,
        )
        info(f"Assets updated from Binance to db: '{assets_updated}'")

        return True

