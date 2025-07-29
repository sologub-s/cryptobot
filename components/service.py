from io import BytesIO

from .binance_raw_client import BinanceRawClientComponent
from .binance import BinanceComponent
from .telegram import TelegramComponent

class ServiceComponent:
    def __init__(
            self,
            binance_component: BinanceComponent,
            binance_raw_client_component: BinanceRawClientComponent,
            telegram_component: TelegramComponent,
    ):
        super().__init__()
        self.binance_component = binance_component
        self.binance_raw_client_component = binance_raw_client_component
        self.telegram_component = telegram_component

    @classmethod
    def create(cls, config: dict):
        return cls(
            binance_component=BinanceComponent.create(config["binance"]),
            binance_raw_client_component=BinanceRawClientComponent.create(config["binance"]),
            telegram_component=TelegramComponent.create(config["telegram"]),
        )

    def get_open_orders(self):
        return self.binance_component.get_open_orders()

    def get_all_orders(self, symbol: str):
        return self.binance_component.get_all_orders(symbol)

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

    def send_telegram_message(self, chat_id: int, message: str, inline_keyboard=None, disable_notification=False):
        if inline_keyboard is None:
            inline_keyboard = []
        self.telegram_component.send_telegram_message(chat_id, message, inline_keyboard, disable_notification)

    def send_telegram_photo(self, chat_id: int, photo_buf: BytesIO, photo_name: str = 'image'):
        self.telegram_component.send_telegram_photo(chat_id, photo_buf, photo_name)

    def get_asset_transfer(self, type: str, start_time=None, end_time=None, limit=100):
        return self.binance_raw_client_component.get_asset_transfer(type=type, start_time=start_time, end_time=end_time, limit=limit)

    def get_asset_ledger(self, asset=None, start_time=None, end_time=None, limit=100):
        return self.binance_raw_client_component.get_asset_ledger(asset=asset, start_time=start_time, end_time=end_time, limit=limit)

    def get_asset_balance(self, asset=None):
        return self.binance_component.get_asset_balance(asset)
