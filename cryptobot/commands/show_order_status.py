from cryptobot.commands import AbstractCommand
from cryptobot.components import ServiceComponent
from cryptobot.models import Order
from cryptobot.views.view import View


class ShowOrderStatusCommand(AbstractCommand):

    def __init__(self):
        super().__init__()
        self._view = None

    def set_payload(self, binance_order_id: int, chat_id: int):
        self._payload["binance_order_id"] = binance_order_id
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
        db_order = Order.select().where(Order.binance_order_id == self._payload["binance_order_id"]).first()
        self._service_component.show_order_status(db_order=db_order, chat_id=self._payload['chat_id'])
        return True