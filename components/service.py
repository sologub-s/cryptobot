from datetime import date, datetime

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

    def read_orders(self, chat_id: int):
        orders = self.binance_component.get_open_orders()
        message = self.binance_component.format_open_orders(orders)
        print("Sending to Telegram...\n")
        self.telegram_component.send_telegram_message(chat_id, message)

    def show_order_status(self, binance_order_id: int, binance_order_symbol: str, chat_id: int):
        order: dict = self.binance_component.get_order_by_binance_order_id(binance_order_id, binance_order_symbol)
        message = self.binance_component.format_order(order)
        print("Sending to Telegram...\n")
        self.telegram_component.send_telegram_message(chat_id, message)