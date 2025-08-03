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

from views.view_helper import to_eng_string

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
        # @TODO remove after debug !!!
        self.handler_do_orders_updating_routine()
        return True
        info(f"Cron execution started")

        handlers_list = {
            'check-all-orders-from-binance': self.handler_check_all_orders_from_binance,
            'do-orders-updating-routine': self.handler_do_orders_updating_routine,
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

    def handler_do_orders_updating_routine(self):

        # get all orders from db
        db_orders: dict[int, Order] = self._service_component.get_all_db_orders_indexed()
        info(f"len(db_orders): '{len(db_orders)}'")

        # collect all symbols
        symbols: list[str] = []
        for order in db_orders.values():
            symbols.append(OrderMapper.remap_symbol(order.symbol))
        symbols = list(set(symbols))
        info(f"symbols: {symbols}")

        # get all orders from binance for each symbol
        binance_orders: list[dict] = []
        for symbol in symbols:
            binance_orders += self._service_component.get_all_orders(symbol=symbol)
        del symbols
        del symbol
        info(f"len(binance_orders): '{len(binance_orders)}'")

        for binance_order in binance_orders:
            info(f"iteration : binance_order_id '{binance_order['orderId']}'")
            # upsert order into db if not exists
            if binance_order['orderId'] not in db_orders:
                info(f"writing binance_order#{binance_order['orderId']} to database...")
                db_order = self._service_component.create_or_update_db_order(binance_order)
                info(f"new db_order.id: '{db_order.id}'")
                # notify about new order creation
                self._service_component.notify_order_created(
                    chat_id=self._payload["chat_id"],
                    db_order=db_order,
                )
                # show new order's status
                self._service_component.show_order_status(
                    db_order=db_order,
                    chat_id=self._payload["chat_id"],
                )
            else: # if order exists - take it from collection of existed orders
                db_order = db_orders[binance_order['orderId']]
                info(f"existed db_order.id: '{db_order.id}'")

            # remember old order's status
            old_db_order_status = db_order.status
            info(f"old_db_order_status: '{old_db_order_status}'")

            # if executedQty has changed - order's filling happened (it may be partial)
            if Decimal(binance_order['executedQty']) != Decimal(db_order.executed_quantity):
                info(f"order's qty changed: '{to_eng_string(Decimal(binance_order['executedQty']))}' != '{to_eng_string(Decimal(db_order.executed_quantity))}'")
                # save `orders_filling_history`
                info(f"saving `orders_filling_history` for db_order.id = '{db_order.id}'")
                if not self._service_component.write_orders_filling_history(
                    binance_order=binance_order,
                    db_order_id=db_order.id,
                    logged_at=millis_on_start - 1,
                ):
                    error(f"ERROR: Cannot write `orders_filling_history` for db_order.id: '{db_order.id}' and binance_order: '{binance_order}'")

                # remember old quantities
                old_executed_quantity = db_order.executed_quantity
                old_cummulative_quote_quantity = db_order.cummulative_quote_quantity
                info(f"old_executed_quantity: '{to_eng_string(old_executed_quantity)}'")
                info(f"old_cummulative_quote_quantity: '{to_eng_string(old_cummulative_quote_quantity)}'")
                # change db_order's quantity
                info(f"changing db_order.id#{db_order.id} quantities...")
                db_order = self._service_component.create_or_update_db_order(binance_order)
                info(f"changing db_order.id#{db_order.id} executed_quantity: '{to_eng_string(db_order.executed_quantity)}'")
                info(f"changing db_order.id#{db_order.id} cummulative_quote_quantity: '{to_eng_string(db_order.cummulative_quote_quantity)}'")
                # send telegram notification
                self._service_component.notify_order_quantity_changed(
                    db_order=db_order,
                    old_executed_quantity=old_executed_quantity,
                    old_cummulative_quote_quantity=old_cummulative_quote_quantity,
                    chat_id=self._payload["chat_id"],
                )

            # if order's status has changed
            mapped_binance_order_status = OrderMapper.map_status(binance_order['status'])
            if old_db_order_status != mapped_binance_order_status:
                info(f"db_order.id#{db_order.id} status change: '{old_db_order_status}' != '{mapped_binance_order_status}'")

                # save new status to db
                #previous_status: str = find_first_key_by_value(OrderMapper.status_mapping, db_order.status, 'UNKNOWN')
                db_order.status = mapped_binance_order_status
                db_order.save()
                info(f"db_order.id#{db_order.id} status: '{db_order.status}'")
                # update assets balances
                sleep(1)
                self._service_component.update_assets_from_binance_to_db(
                    assets=BalanceMapper.get_assets().keys(),
                    force_insert=True,
                )
                # notify about order's status change
                self._service_component.notify_order_status_changed(
                    db_order=db_order,
                    previous_status=old_db_order_status,
                    chat_id=self._payload["chat_id"],
                )

                # if status has changed and the new status is FILLED then place new order
                if db_order.status == OrderMapper.STATUS_FILLED:
                    info(f"db_order.id#{db_order.id} status is 'FILLED' ('{db_order.status}')")
                    # creating new order
                    info(f"starting to create new binance order...")
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
                    info(f"params for new binance order: '{order_params}'")
                    self._service_component.create_order_on_binance(**order_params)

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

        for binance_order in all_binance_orders:

            # upsert order into db if not exists
            if binance_order['orderId'] not in all_db_orders_indexed:
                db_order = self._service_component.create_or_update_db_order(binance_order)
                m_order_created = self._view.render('telegram/orders/order_created.j2', {
                    'order': db_order,
                })
                self._service_component.send_telegram_message(self._payload["chat_id"], m_order_created)
                (ShowOrderStatusCommand()
                    .set_payload(
                        binance_order_id=db_order.binance_order_id,
                        chat_id=self._payload["chat_id"],
                    )
                    .set_deps(self._service_component, self._view)
                    .execute()
                )
            else:
                db_order = all_db_orders_indexed[binance_order['orderId']]
            mapped_binance_status = OrderMapper.map_status(binance_order['status'])

            # if executedQty has changed
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
                    f"show_order_status:{binance_order['orderId']}",
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
                    f"show_order_status:{binance_order['orderId']}",
                ]
                inline_keyboard: list = []
                for key in keys:
                    inline_keyboard.append([{"text": key, "callback_data": key}, ])
                self._service_component.send_telegram_message(self._payload["chat_id"], message, inline_keyboard)
                self._service_component.send_telegram_message(self._payload["chat_id"], self._view.render(
                    'telegram/or_choose_another_option.j2', {}
                ))

                # if status has changed then create new order
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

