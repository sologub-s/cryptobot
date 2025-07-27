from commands import AbstractCommand
from components import ServiceComponent
from mappers.order_mapper import OrderMapper
from models import Order
from views.view import View
from helpers import find_first_key_by_value


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
        all_db_orders = Order.select()
        all_db_orders_indexed: dict[int, Order] = {}
        for db_order in all_db_orders:
            all_db_orders_indexed[db_order.binance_order_id] = db_order
        del all_db_orders
        #print(f"all_db_orders_indexed: {all_db_orders_indexed}")

        all_binance_orders = self._service_component.get_all_orders('ETHUSDT')

        for binance_order in all_binance_orders:
            if binance_order['orderId'] not in all_db_orders_indexed:
                all_db_orders_indexed[binance_order['orderId']] = Order().fill_from_binance(binance_order)
                all_db_orders_indexed[binance_order['orderId']].upsert()
            mapped_binance_status = OrderMapper.map_status(binance_order['status'])
            if mapped_binance_status != all_db_orders_indexed[binance_order['orderId']].status:
                previous_status: str = find_first_key_by_value(OrderMapper.status_mapping, all_db_orders_indexed[binance_order['orderId']].status, 'UNKNOWN')
                all_db_orders_indexed[binance_order['orderId']].status = mapped_binance_status
                all_db_orders_indexed[binance_order['orderId']].save()
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

        return True