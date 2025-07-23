from .binance import BinanceComponent
from .telegram import TelegramComponent

class ServiceComponent:
    def __init__(
            self,
            binance_component: BinanceComponent,
            telegram_component: TelegramComponent,
    ):
        super().__init__()
        self.binance_component = binance_component
        self.telegram_component = telegram_component

    @classmethod
    def create(cls, config: dict):
        return cls(
            BinanceComponent.create(config["binance"]),
            TelegramComponent.create(config["telegram"]),
        )

    @property
    def binance_component(self):
        return self.__binance_component

    @binance_component.setter
    def binance_component(self, binance_component: BinanceComponent):
        self.__binance_component = binance_component

    @property
    def telegram_component(self):
        return self.__telegram_component

    @telegram_component.setter
    def telegram_component(self, telegram_component: TelegramComponent):
        self.__telegram_component = telegram_component

    def get_open_orders(self):
        return self.binance_component.get_open_orders()

    def get_order_by_binance_order_id_and_binance_symbol(self, binance_order_id: int, binance_order_symbol: str):
        return self.binance_component.get_order_by_binance_order_id(binance_order_id, binance_order_symbol)

    def get_price_for_binance_symbol(self, binance_order_symbol: str) -> dict | dict:
        return self.binance_component.get_price_for_binance_symbol(binance_order_symbol)

    def send_telegram_message(self, chat_id: int, message: str):
        self.telegram_component.send_telegram_message(chat_id, message)
