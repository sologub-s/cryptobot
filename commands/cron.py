from decimal import Decimal
from time import sleep

from commands import AbstractCommand, ShowOrderStatusCommand
from components import ServiceComponent
from mappers.balance_mapper import BalanceMapper
from mappers.order_mapper import OrderMapper
from models import Order, CronJob, Balance, OrderFillingHistory
from views.view import View
from helpers import find_first_key_by_value, current_millis, increase_price_percent, decrease_price_percent, dec_to_str

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

        changed_orders_present: bool = False

        for binance_order in all_binance_orders:
            #upsert order into db if not exists
            # test
            #if binance_order['orderId'] == 33048596553:
            #    binance_order['status'] = 'PARTIALLY_FILLED'
            if binance_order['orderId'] not in all_db_orders_indexed:
                db_order = self._service_component.create_or_update_db_order(binance_order)
                m_order_created = self._view.render('telegram/orders/order_created.j2', {
                    'order': db_order,
                })
                self._service_component.send_telegram_message(self._payload["chat_id"], m_order_created)
                (ShowOrderStatusCommand()
                    .set_payload(db_order.binance_order_id, binance_order['symbol'], self._payload["chat_id"])
                    .set_deps(self._service_component, self._view)
                    .execute()
                )
            else:
                db_order = all_db_orders_indexed[binance_order['orderId']]
            mapped_binance_status = OrderMapper.map_status(binance_order['status'])
            # test
            #if binance_order['orderId'] == 33048596553:
            #    binance_order['executedQty'] = '0.00150000'
            #    binance_order['cummulativeQuoteQty'] = '10.02100000'
            # if executedQty has changed
            #print(binance_order['orderId'], float(binance_order['executedQty']), float(db_order.executed_quantity))
            if Decimal(binance_order['executedQty']) != Decimal(db_order.executed_quantity):
                # implement saving to `orders_filling_history`
                order_filling_history = OrderFillingHistory().fill_from_binance(binance_order)
                order_filling_history.order_id = db_order.id
                order_filling_history.logged_at = millis_on_start -1
                order_filling_history.save()
                db_order.executed_quantity = Decimal(binance_order['executedQty'])
                db_order.cummulative_quote_quantity = Decimal(binance_order['cummulativeQuoteQty'])
                db_order.save()
                # send telegram notification
                message_qty = self._view.render('telegram/orders/order_executed_quantity_changed.j2', {
                    'binance_order': binance_order,
                    'db_order': db_order,
                })
                keys = [
                    f"show_order_status:{binance_order['orderId']}:{binance_order['symbol']}",
                ]
                inline_keyboard: list = []
                for key in keys:
                    inline_keyboard.append([{"text": key, "callback_data": key}, ])
                self._service_component.send_telegram_message(self._payload["chat_id"], message_qty, inline_keyboard)
                self._service_component.send_telegram_message(self._payload["chat_id"], self._view.render(
                    'telegram/or_choose_another_option.j2', {}))
            # if status has changed
            if mapped_binance_status != db_order.status:
                # save new status to db
                previous_status: str = find_first_key_by_value(OrderMapper.status_mapping, db_order.status, 'UNKNOWN')
                db_order.status = mapped_binance_status
                db_order.save()
                # update assets balances
                sleep(1)
                self._service_component.update_assets_from_binance_to_db(
                    assets=BalanceMapper.get_assets().keys(),
                    force_insert=True,
                )
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
                    'telegram/or_choose_another_option.j2', {}
                ))
                if db_order.status == OrderMapper.STATUS_FILLED:
                    # creating new order
                    order_params: dict = {
                        'chat_id': self._payload["chat_id"],
                        'db_symbol': db_order.symbol,
                    }
                    if db_order.side == OrderMapper.SIDE_BUY:
                        order_params['db_side'] = OrderMapper.SIDE_SELL
                        order_params['str_price'] = dec_to_str(increase_price_percent(Decimal(db_order.order_price), Decimal(5)))
                    if db_order.side == OrderMapper.SIDE_SELL:
                        order_params['db_side'] = OrderMapper.SIDE_BUY
                        order_params['str_price'] = dec_to_str(decrease_price_percent(Decimal(db_order.order_price), Decimal(5)))
                    self._service_component.create_order_on_binance(**order_params)


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

