import time
from decimal import Decimal
from io import BytesIO
from logging import info, error
from views.view import View

from peewee import MySQLDatabase

from helpers import current_millis, calculate_order_quantity
from mappers.balance_mapper import BalanceMapper
from mappers.order_mapper import OrderMapper
from models import Balance, Order, OrderFillingHistory
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
            view: View,
    ):
        super().__init__()
        self.binance_component = binance_component
        self.binance_raw_client_component = binance_raw_client_component
        self.telegram_component = telegram_component
        self.db = db
        self.view = view

    @classmethod
    def create(cls, config: dict, db: MySQLDatabase, view: View):
        return cls(
            binance_component=BinanceComponent.create(config["binance"]),
            binance_raw_client_component=BinanceRawClientComponent.create(config["binance"]),
            telegram_component=TelegramComponent.create(config["telegram"]),
            db=db,
            view=view,
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

    def notify_order_created(self, chat_id: int, db_order: Order):
        message = self.view.render('telegram/orders/order_created.j2', {
            'order': db_order,
        })
        self.send_telegram_message(chat_id, message)

    def write_orders_filling_history(self, binance_order: dict, db_order_id: int, logged_at: int) -> int|None:
        order_filling_history = OrderFillingHistory().fill_from_binance(binance_order)
        order_filling_history.order_id = db_order_id
        order_filling_history.logged_at = logged_at
        if not order_filling_history.save():
            return None
        return order_filling_history.id

    def show_orders(self, db_orders: [Order], chat_id: int):
        message = self.view.render('telegram/orders/orders_list.j2', {
            'db_orders': db_orders,
        })
        self.send_telegram_message(chat_id, message)

    def show_order_status(self, db_order: Order, chat_id: int):
        message = self.view.render('telegram/orders/order_item.j2', {
            'db_order': db_order,
        })
        self.send_telegram_message(chat_id, message)

    def notify_order_status_changed(self, db_order: Order, previous_status: int, chat_id: int):
        # send telegram notification
        message = self.view.render('telegram/orders/order_status_changed.j2', {
            'db_order': db_order,
            'previous_status': previous_status,
        })
        keys = [
            f"show_order_status:{db_order.binance_order_id}",
        ]
        inline_keyboard: list = []
        for key in keys:
            inline_keyboard.append([{"text": key, "callback_data": key}, ])
        self.send_telegram_message(chat_id, message, inline_keyboard)
        self.send_telegram_message(chat_id, self.view.render(
            'telegram/or_choose_another_option.j2', {}
        ))

    def notify_order_quantity_changed(self, db_order: Order, old_executed_quantity: int, old_cummulative_quote_quantity: int, chat_id: int):
        message = self.view.render('telegram/orders/order_quantity_changed.j2', {
            'db_order': db_order,
            'old_executed_quantity': old_executed_quantity,
            'old_cummulative_quote_quantity': old_cummulative_quote_quantity,
        })
        keys = [
            f"show_order_status:{db_order.binance_order_id}",
        ]
        inline_keyboard: list = []
        for key in keys:
            inline_keyboard.append([{"text": key, "callback_data": key}, ])
        self.send_telegram_message(chat_id, message, inline_keyboard)
        self.send_telegram_message(chat_id, self.view.render(
            'telegram/or_choose_another_option.j2', {}))

    def create_or_update_db_order(self, binance_order: dict):
        db_order = Order().fill_from_binance(binance_order)
        db_order.upsert()
        return db_order

    def get_all_db_orders_indexed(self) -> dict[int, Order]:
        all_db_orders = Order.select()
        all_db_orders_indexed: dict[int, Order] = {}
        for db_order in all_db_orders:
            all_db_orders_indexed[db_order.binance_order_id] = db_order
        del all_db_orders
        return all_db_orders_indexed


    def create_order_on_binance(self, chat_id: int, str_price:str = None, db_symbol:int=None, db_side:int=None,) -> None|dict:

        info('!!! PREPARING TO CREATE ORDER ON BINANCE !!!')

        if not str_price:
            error('Cannot create order on Binance - str_price not set')
            return None
        else:
            #price: Decimal = Decimal('3600.00')
            price = Decimal(str_price)

        if not db_symbol:
            error('Cannot create order on Binance - db_symbol not set')
            return None
        else:
            #symbol = 'ETHUSDT'
            symbol = OrderMapper.remap_symbol(db_symbol)
            if not symbol:
                error(f"Cannot create order on Binance - unknown symbol '{db_symbol}'")

        if not db_side:
            error('Cannot create order on Binance - db_side not set')
            return None
        else:
            #side = 'BUY'
            side = OrderMapper.remap_side(db_side)
            if not side:
                error(f"Cannot create order on Binance - unknown side '{db_side}'")

        symbol_info = self.binance_component.get_symbol_info(symbol)
        if side == 'BUY':
            asset_to_sell = symbol_info['quoteAsset']
        else:
            asset_to_sell = symbol_info['baseAsset']

        step_size = None
        min_qty = None
        max_qty = None
        min_notional = None

        for f in symbol_info["filters"]:
            if f["filterType"] == "LOT_SIZE":
                step_size = Decimal(f["stepSize"])
                min_qty = Decimal(f["minQty"])
                max_qty = Decimal(f["maxQty"])
            elif f["filterType"] == "MIN_NOTIONAL":
                min_notional = Decimal(f["minNotional"])

        info(f'asset_to_sell: {asset_to_sell}')
        info(f'step_size: {step_size}')
        info(f'min_qty: {min_qty}')
        info(f'max_qty: {max_qty}')
        info(f'min_notional: {min_notional}')

        binance_balance = self.get_asset_balance(asset_to_sell)
        info(f'binance_balance: {binance_balance}')
        actual_balance = Decimal(binance_balance['free'])
        info(f'actual_balance: {actual_balance}')

        quantity = calculate_order_quantity(actual_balance, price, step_size, side)
        info(f"quantity: {quantity}")

        can_create = False
        tries = 0
        while not can_create and tries <= 10:
            info('trying to create test order')
            tries += 1
            try:
                params: dict = {
                    'symbol': symbol,
                    'side': side,
                    'type': 'LIMIT',
                    'timeInForce': 'GTC',
                    'quantity': str(quantity),
                    'price': str(price),
                }
                info(f"attempt #{tries} to create test order on binance with the following params: {params}...")
                result = self.binance_component.create_test_order(**params)
                info(f'result: {result}')
                can_create = True
            except Exception as e:
                info(e.__dict__)
                if 'LOT_SIZE' in e.__dict__['message']:
                    err_m = f"buy_qty '{quantity}' is too big (cannot pass LOT_SIZE validation, decreasing by step_size '{step_size}')"
                    info(err_m)
                    self.send_telegram_message(chat_id, err_m)
                    quantity -= step_size
                    info('sleeping 5 secs...')
                    time.sleep(5)
                else:
                    err_m = f"create_test_order ERROR: {e}"
                    error(err_m)
                    self.send_telegram_message(chat_id, err_m)
                if quantity <= 0:
                    err_m = f'not enough balance for minimal order: {quantity}'
                    info(err_m)
                    self.send_telegram_message(chat_id, err_m)
                    break

        info(f'can_create: {can_create}')

        if can_create:
            # create real order here
            m = f"REAL ORDER ON BINANCE CREATION SHOULD BE HERE, the params: {params}"
            info(m)
            # todo replace with order's owner's chat_id
            self.send_telegram_message(chat_id, m,)
            return True
        return False
