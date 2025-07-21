from commands import AbstractCommand
from components import ServiceComponent

class ShowOrderStatusCommand(AbstractCommand):

    def set_payload(self, binance_order_id: int, binance_symbol: str, chat_id: int):
        self._payload["binance_order_id"] = binance_order_id
        self._payload["binance_symbol"] = binance_symbol
        self._payload["chat_id"] = chat_id
        self._initialized = True
        return self

    def set_deps(self, service_component: ServiceComponent):
        self._service_component = service_component
        return self

    def execute(self):
        if not self._initialized:
            print(f"ERROR: Command {self.__class__.__name__} is NOT initialized")
            return False
        self._service_component.show_order_status(
            self._payload["binance_order_id"],
            self._payload["binance_symbol"],
            self._payload["chat_id"],
        )
        return True