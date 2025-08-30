import time
from decimal import Decimal
from io import BytesIO
from logging import info, error, warn
from typing import Any

from cryptobot.helpers.money import round_price
from cryptobot.views.view import View

from peewee import MySQLDatabase
from cryptobot.helpers import current_millis, calculate_order_quantity, l
from cryptobot.mappers.balance_mapper import BalanceMapper
from cryptobot.mappers.order_mapper import OrderMapper
from cryptobot.models import Balance, Order, OrderFillingHistory, OrderTrade
from ..ports.binance_gateway import BinanceGatewayPort
from ..ports.telegram import TelegramComponentPort

class ServiceComponent:

    def __init__(
            self,
            binance_gateway: BinanceGatewayPort,
            telegram_component: TelegramComponentPort,
            db: MySQLDatabase,
            view: View,
    ):
        super().__init__()
        self.binance_gateway: BinanceGatewayPort = binance_gateway
        self.telegram_component: TelegramComponentPort = telegram_component
        self.db: MySQLDatabase = db
        self.view: View = view

    @classmethod
    def create(
        cls,
        db: MySQLDatabase,
        view: View,
        telegram_component: TelegramComponentPort,
        binance_gateway: BinanceGatewayPort,
    ):
        return cls(
            telegram_component=telegram_component,
            db=db,
            view=view,
            binance_gateway=binance_gateway,
        )

    def check_telegram_bot_api_secret_token(self, bot_api_secret_token: str) -> bool:
        return self.telegram_component.check_telegram_bot_api_secret_token(bot_api_secret_token)

    def get_open_orders(self):
        return self.binance_gateway.get_open_orders()

    def get_all_orders(self, symbol: str):
        return self.binance_gateway.get_all_orders(symbol)

    def get_order_by_binance_order_id_and_binance_symbol(self, binance_order_id: int, binance_order_symbol: str):
        return self.binance_gateway.get_order_by_binance_order_id(binance_order_id, binance_order_symbol)

    def get_price_for_binance_symbol(self, binance_order_symbol: str) -> dict[str, Any]:
        return self.binance_gateway.get_price_for_binance_symbol(binance_order_symbol)

    def map_historical_klines(self, klines: list) -> list:
        klines_mapped: list = []
        for kline in klines:
            kline_mapped: dict = {
                'open_time': round(int(kline[0]) / 1000),
                'open_price': round(Decimal(kline[1]), 2),
                'high_price': round(Decimal(kline[2]), 2),
                'low_price': round(Decimal(kline[3]), 2),
                'close_price': round(Decimal(kline[4]), 2),
                'average_price': round((Decimal(kline[2]) + Decimal(kline[3])) / 2, 2),
                'volume': kline[5],
                'close_time': round(int(kline[6]) / 1000),
            }
            klines_mapped.append(kline_mapped)
        return klines_mapped

    def get_historical_klines(self, binance_order_symbol: str, period: str, interval: str) -> list:
        klines = self.binance_gateway.get_historical_klines(binance_order_symbol, period, interval)
        return self.map_historical_klines(klines)

    def send_telegram_message(self, chat_id: int, message: str, inline_keyboard=None, disable_notification=False):
        if inline_keyboard is None:
            inline_keyboard = []
        self.telegram_component.send_telegram_message(chat_id, message, inline_keyboard, disable_notification)

    def send_telegram_photo(self, chat_id: int, photo_buf: BytesIO, photo_name: str = 'image'):
        self.telegram_component.send_telegram_photo(chat_id, photo_buf, photo_name)

    def get_asset_transfer(self, type: str, start_time=None, end_time=None, limit=100):
        return self.binance_gateway.get_asset_transfer(type=type, start_time=start_time, end_time=end_time, limit=limit)

    def get_asset_balance(self, asset=None):
        return self.binance_gateway.get_asset_balance(asset)

    def get_all_trades(self, binance_symbol: str) -> list[dict]:
        return self.binance_gateway.get_all_trades(binance_symbol=binance_symbol)

    def upsert_binance_trades(self, trades: list[dict]) -> list[int]:
        if len(trades) == 0:
            return []
        inserted_trades: list[int] = []

        binance_orders_ids = []
        for trade in trades:
            binance_orders_ids.append(trade['orderId'])

        db_orders = Order.select().where(Order.binance_order_id.in_(binance_orders_ids))
        db_orders_indexed = {}
        for db_order in db_orders:
            db_orders_indexed[db_order.binance_order_id] = db_order
        db_orders = db_orders_indexed.copy()
        del db_orders_indexed

        for trade in trades:
            db_order_trade = OrderTrade().fill_from_binance(trade)
            db_order_trade.order_id = db_orders[trade['orderId']].id
            id = OrderTrade.insert(db_order_trade.__data__).on_conflict(
                preserve=[
                    OrderTrade.id,
                    OrderTrade.created_at,
                ],
            ).execute()
            if id is not None:
                inserted_trades.append(id)

        return inserted_trades

    def update_trades_from_binance_to_db(self, order_ids=None):
        if order_ids is None:
            order_ids = []
        order_ids = list(set(order_ids))
        if len(order_ids) == 0:
            m_err = "order_ids is empty, doing nothing..."
            l(self, m_err, 'info')
            return []
        db_orders: list[Order] = list(Order.select().where(Order.id.in_(order_ids)))
        if len(db_orders) == 0:
            m_err = f"db_orders with ids: '{order_ids}' not found"
            l(self, m_err)
            raise Exception(m_err)
        all_binance_symbols = []
        all_orders_binance_order_ids = []
        for db_order in db_orders:
            if db_order.symbol == OrderMapper.SYMBOL_UNKNOWN:
                continue
            all_binance_symbols.append(OrderMapper.remap_symbol(db_order.symbol))
            all_orders_binance_order_ids.append(db_order.binance_order_id)
        all_trades = []
        for binance_symbol in all_binance_symbols:
            all_trades += self.binance_gateway.get_all_trades(
                binance_symbol=binance_symbol,
            )

        upserted_trades_ids: list[int] = []

        for trade in all_trades:
            if trade['orderId'] in all_orders_binance_order_ids:
                upserted_trades_ids += self.upsert_binance_trades([trade])
        return upserted_trades_ids

    def update_assets_from_binance_to_db(self, assets: list=None, force_insert=False):
        if assets is None:
            assets = []
        saved_count = 0
        for asset in assets:
            with self.db.atomic():
                # get asset balance from Binance
                binance_balance = self.get_asset_balance(asset)
                info(f"Asset {asset} balance: {binance_balance} -> {binance_balance['asset']} ({BalanceMapper.map_asset(binance_balance['asset'])})")
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

    def write_orders_filling_history(self, binance_order: dict, db_order_id: int, logged_at: int) -> int | None:
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

        l(self, f"!!! PREPARING TO CREATE AN ORDER ON BINANCE !!!", 'info', chat_id)

        if not str_price:
            l(self, f"Cannot create order on Binance - str_price not set", 'error', chat_id)
            return None
        else:
            #price: Decimal = Decimal('3600.00')
            price = Decimal(str_price)

        if not db_symbol:
            l(self, f"Cannot create order on Binance - db_symbol not set", 'error', chat_id)
            return None
        else:
            #symbol = 'ETHUSDT'
            symbol = OrderMapper.remap_symbol(db_symbol)
            if not symbol:
                l(self, f"Cannot create order on Binance - unknown symbol '{db_symbol}'", 'error', chat_id)

        if not db_side:
            l(self, f"Cannot create order on Binance - db_side not set", 'error', chat_id)
            return None
        else:
            #side = 'BUY'
            side = OrderMapper.remap_side(db_side)
            if not side:
                l(self, f"Cannot create order on Binance - unknown side '{db_side}'", 'error', chat_id)

        symbol_info = self.binance_gateway.get_symbol_info(symbol)
        if side == 'BUY':
            asset_to_sell = symbol_info['quoteAsset']
        else:
            asset_to_sell = symbol_info['baseAsset']

        step_size = None
        min_qty = None
        max_qty = None
        min_notional = None
        tick_size = None

        l(self, f"symbol_info['filters']: {symbol_info['filters']}", 'info', chat_id)

        for f in symbol_info["filters"]:
            if f["filterType"] == "LOT_SIZE":
                step_size = Decimal(f["stepSize"])
                min_qty = Decimal(f["minQty"])
                max_qty = Decimal(f["maxQty"])
            elif f["filterType"] == "MIN_NOTIONAL":
                min_notional = Decimal(f["minNotional"])
            elif f["filterType"] == "PRICE_FILTER":
                tick_size = Decimal(f["tickSize"])

        l(self, f"asset_to_sell: {asset_to_sell}", 'info', chat_id)
        l(self, f"step_size: {step_size}", 'info', chat_id)
        l(self, f"min_qty: {min_qty}", 'info', chat_id)
        l(self, f"max_qty: {max_qty}", 'info', chat_id)
        l(self, f"min_notional: {min_notional}", 'info', chat_id)
        l(self, f"tick_size: {tick_size}", 'info', chat_id)

        safe_price = round_price(price=price, tick_size=tick_size)

        binance_balance = self.get_asset_balance(asset_to_sell)
        l(self, f"binance_balance: {binance_balance}", 'info', chat_id)
        actual_balance = Decimal(binance_balance['free'])
        #actual_balance = Decimal('0.00809190') # @TODO REMOVE !!!
        l(self, f"actual_balance: {actual_balance}", 'info', chat_id)

        quantity = calculate_order_quantity(
            balance=actual_balance,
            price=safe_price,
            step_size=step_size,
            side=side,
            min_qty=min_qty,
        )
        l(self, f"quantity: {quantity}", 'info', chat_id)

        if quantity == 0:
            err_m = f"prepared quantity is '{quantity}' - there is no sense even to try to create an order..."
            l(self, err_m, 'warning', chat_id)
            self.send_telegram_message(chat_id, err_m)
            return None

        can_create = False
        tries = 0
        while not can_create and tries <= 10:
            l(self, f"trying to create test order...", 'info', chat_id)
            tries += 1
            try:
                params: dict = {
                    'symbol': symbol,
                    'side': side,
                    'type': 'LIMIT',
                    'timeInForce': 'GTC',
                    'quantity': str(quantity),
                    'price': str(safe_price),
                }
                l(self, f"attempt #{tries} to create test order on binance with the following params: {params}...", 'info', chat_id)
                result = self.binance_gateway.create_test_order(**params)
                l(self, f"create_test_order() result: {result}", 'info', chat_id)
                can_create = True
            except Exception as e:
                l(self, str(e), 'error', chat_id)
                if 'LOT_SIZE' in str(e):
                    err_m = f"buy_qty '{quantity}' is too big or too small (cannot pass LOT_SIZE validation, decreasing quantity '{quantity}' by step_size '{step_size}')"
                    l(self, err_m, 'error', chat_id)
                    self.send_telegram_message(chat_id, err_m)
                    quantity -= step_size
                    info('sleeping 5 secs...')
                    l(self, f"sleeping 5 secs...", 'info', chat_id)
                    time.sleep(5)
                elif 'MIN_NOTIONAL' in str(e):
                    err_m = f"actual_balance '{actual_balance}' is less then '{min_notional}' (cannot pass MIN_NOTIONAL validation, need more free balance...')"
                    l(self, err_m, 'error', chat_id)
                    self.send_telegram_message(chat_id, err_m)
                elif 'PRICE_FILTER' in str(e):
                    err_m = f"safe_price '{safe_price}' must be multiple of tick_size '{tick_size}' (cannot pass PRICE_FILTER validation, please fix the price...')"
                    l(self, err_m, 'error', chat_id)
                    self.send_telegram_message(chat_id, err_m)
                elif 'MAX_NUM_ORDERS' in str(e):
                    err_m = f"too many open orders (cannot pass MAX_NUM_ORDERS validation, please wait or cancel some orders...')"
                    l(self, err_m, 'error', chat_id)
                    self.send_telegram_message(chat_id, err_m)
                else:
                    err_m = f"create_test_order ERROR: {e}"
                    l(self, err_m, 'error', chat_id)
                    self.send_telegram_message(chat_id, err_m)
                if quantity <= min_qty:
                    err_m = f"not enough balance for minimal order quantity (requested quantity: '{quantity}', minimal quantity: '{min_qty}')"
                    l(self, err_m, 'warning', chat_id)
                    self.send_telegram_message(chat_id, err_m)
                    break

        l(self, f"can_create: {can_create}", 'info', chat_id)

        if can_create:
            # create real order here
            m = f"creation of REAL ORDER ON BINANCE, the params: {params}"
            l(self, m, 'info', chat_id)
            # todo replace with order's owner's chat_id
            self.send_telegram_message(chat_id, m,)
            real_result = self.binance_gateway.create_order(**params)
            l(self, f"create_order() result: {real_result}", 'info', chat_id)
            return real_result
        return None
