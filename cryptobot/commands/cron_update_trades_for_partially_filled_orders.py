from decimal import Decimal
from time import sleep

from cryptobot.commands import AbstractCommand
from cryptobot.components import ServiceComponent
from cryptobot.mappers.balance_mapper import BalanceMapper
from cryptobot.mappers.order_mapper import OrderMapper
from cryptobot.models import Order, CronJob
from cryptobot.views.view import View
from cryptobot.helpers import current_millis, increase_price_percent, decrease_price_percent, dec_to_str, \
    l, sg

import logging
from logging import error, info

logging.basicConfig(level=logging.INFO)


class CronUpdateTradesForPartiallyFilledOrdersCommand(AbstractCommand):

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
        
        info(f"CronUpdateTradesForPartiallyFilledOrders execution started")

        l(self, f"handler_update_trades_for_partially_filled_orders: working...", 'info')
        db_orders = Order.select().where(Order.status == OrderMapper.STATUS_PARTIALLY_FILLED)
        db_order_ids: list[int] = []
        for db_order in db_orders:
            db_order_ids.append(db_order.id)
        l(self, f"handler_update_trades_for_partially_filled_orders: loaded order ids: {db_order_ids}", 'info')
        updated_trades = self._service_component.update_trades_from_binance_to_db(
            order_ids=db_order_ids,
        )
        if len(updated_trades) > 0:
            l(self, f"handler_update_trades_for_partially_filled_orders: updated trades: '{updated_trades}' (total: '{len(updated_trades)}')", 'info')
        return True


