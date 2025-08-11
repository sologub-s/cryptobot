from cryptobot.commands import AbstractCommand
from cryptobot.components import ServiceComponent
from cryptobot.views.view import View


class ShowPriceCommand(AbstractCommand):

    def __init__(self):
        super().__init__()
        self._view = None

    def set_payload(self, binance_symbol: str, chat_id: int):
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
        price = self._service_component.get_price_for_binance_symbol(self._payload["binance_symbol"])
        message = self._view.render('telegram/price.j2', {
            'price': price,
            'binance_symbol': self._payload["binance_symbol"],
        })
        self._service_component.send_telegram_message(self._payload["chat_id"], message)
        return True