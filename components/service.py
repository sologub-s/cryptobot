from io import BytesIO

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

    def map_historical_klines(self, klines: list) -> list:
        klines_mapped: list = []
        for kline in klines:
            kline_mapped: dict = {
                'open_time': round(int(kline[0]) / 1000),
                'open_price': round(float(kline[1]), 2),
                'high_price': round(float(kline[2]), 2),
                'low_price': round(float(kline[3]), 2),
                'close_price': round(float(kline[4]), 2),
                'average_price': round((float(kline[2]) + float(kline[3])) / 2, 2),
                'volume': kline[5],
                'close_time': round(int(kline[6]) / 1000),
            }
            klines_mapped.append(kline_mapped)
        return klines_mapped

    def get_historical_klines(self, binance_order_symbol: str, period: str, interval: str) -> list:
        return self.binance_component.get_historical_klines(binance_order_symbol, period, interval)

    def send_telegram_message(self, chat_id: int, message: str, inline_keyboard=None):
        if inline_keyboard is None:
            inline_keyboard = []
        self.telegram_component.send_telegram_message(chat_id, message, inline_keyboard)

    def send_telegram_photo(self, chat_id: int, photo_buf: BytesIO, photo_name: str = 'image'):
        self.telegram_component.send_telegram_photo(chat_id, photo_buf, photo_name)
