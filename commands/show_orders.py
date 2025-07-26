from commands import AbstractCommand
from components import ServiceComponent
from mappers.order_mapper import OrderMapper
from models import Order
from views.view import View


class ShowOrdersCommand(AbstractCommand):

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
        binance_orders = self._service_component.get_open_orders()
        for binance_order in binance_orders:
            self._service_component.check_if_order_status_changed_and_upsert(binance_order, self._payload["chat_id"])

        message = self._view.render('telegram/orders/orders_list.j2', {
            'orders': binance_orders,
        })
        self._service_component.send_telegram_message(self._payload["chat_id"], message)
        return True