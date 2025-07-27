from commands import AbstractCommand
from components import ServiceComponent
from models import Order
from views.view import View


class ShowOrderStatusCommand(AbstractCommand):

    def __init__(self):
        super().__init__()
        self._view = None

    def set_payload(self, binance_order_id: int, binance_symbol: str, chat_id: int):
        self._payload["binance_order_id"] = binance_order_id
        self._payload["binance_symbol"] = binance_symbol
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
        binance_order = self._service_component.get_order_by_binance_order_id_and_binance_symbol(
            self._payload["binance_order_id"],
            self._payload["binance_symbol"],
        )
        message = self._view.render('telegram/orders/order_item.j2', {
            'order': binance_order,
        })
        self._service_component.send_telegram_message(self._payload["chat_id"], message)
        return True