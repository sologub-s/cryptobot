from decimal import Decimal
from io import BytesIO
from logging import info, error

from peewee import MySQLDatabase

from helpers import current_millis
from mappers.balance_mapper import BalanceMapper
from models import Balance, Order
from .binance_raw_client import BinanceRawClientComponent
from .binance import BinanceComponent
from .telegram import TelegramComponent

class ServiceComponent:
    def __init__(
            self,
            binance_component: BinanceComponent,
            binance_raw_client_component: BinanceRawClientComponent,
            telegram_component: TelegramComponent,
            db: MySQLDatabase,
    ):
        super().__init__()
        self.binance_component = binance_component
        self.binance_raw_client_component = binance_raw_client_component
        self.telegram_component = telegram_component
        self.db = db

    @classmethod
    def create(cls, config: dict, db: MySQLDatabase):
        return cls(
            binance_component=BinanceComponent.create(config["binance"]),
            binance_raw_client_component=BinanceRawClientComponent.create(config["binance"]),
            telegram_component=TelegramComponent.create(config["telegram"]),
            db=db,
        )

    def check_telegram_bot_api_secret_token(self, bot_api_secret_token: str) -> bool:
        return self.telegram_component.check_telegram_bot_api_secret_token(bot_api_secret_token)

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

    def update_assets_from_binance_to_db(self, assets: list=None, force_insert=False):
        if assets is None:
            assets = []
        saved_count = 0
        for asset in assets:
            with self.db.atomic():
                # get asset balance from Binance
                binance_balance = self.get_asset_balance(asset)
                info(f"Asset {asset} balance: {binance_balance} -> {BalanceMapper.map_asset(binance_balance['asset'])}")
                # last balance obj from db of the same asset with the same free&locked
                if force_insert:
                    balance_db = None
                else:
                    balance_db = (
                        Balance.select()
                            .where(
                                (Balance.asset == BalanceMapper.map_asset(binance_balance['asset']))
                                &
                                (Balance.free == Decimal(binance_balance['free']))
                                &
                                (Balance.locked == Decimal(binance_balance['locked']))
                            )
                            .order_by(Balance.checked_at.desc())
                            .limit(1)
                            .first()
                    )
                # if it's present = update its checked_at time, no need to insert new record
                if balance_db:
                    info (f'Balance existed record found (force_insert: {force_insert}), id: {balance_db.id}')
                    balance_db.updated_at = current_millis()
                    balance_db.checked_at = current_millis()
                else: # otherwise - insert new record
                    info(f'Balance existed record not found (force_insert: {force_insert}), creating the new one...')
                    balance_db = Balance().fill_from_binance(binance_balance)

                if balance_db.save():
                    info(f'Balance saved: {balance_db.as_dict()}')
                    saved_count += 1
                else:
                    error(f"Cannot save balance record: {balance_db.as_dict()}")
        return saved_count

    def create_or_update_db_order(self, binance_order: dict):
        db_order = Order().fill_from_binance(binance_order)
        db_order.upsert()
        return db_order
