import time
from decimal import Decimal
from typing import Any

from binance import Client, BinanceAPIException

from cryptobot.commands.show_price_chart import KLINE_INTERVAL_1DAY
from cryptobot.models import Order
from cryptobot.ports.binance_client_adapter import BinanceClientAdapterPort
from tests.ports.binance_client_adapter_mock import BinanceClientAdapterMockPort


class BinanceClientAdapterMock(BinanceClientAdapterMockPort, BinanceClientAdapterPort):
    def __init__(self,):
        super().__init__()
        self.memory_orders: dict[str, list[dict[str, Any]]] = {}
        self.memory_avg_price: dict[str, list[dict[str, Any]]] = {}
        self.memory_historical_klines: dict[str, list[list[Any]]] = {}
        self.memory_asset_balance: dict[str, dict[str, str]] = {}
        self.memory_symbol_info: dict[str, Any] = {}

    @classmethod
    def create(cls,):
        return cls()

    def clear(self) -> None:
        self.memory_orders: dict[str, list[dict[str, Any]]] = {}
        self.memory_avg_price: dict[str, list[dict[str, Any]]] = {}
        self.memory_historical_klines: dict[str, list[list[Any]]] = {}
        self.memory_asset_balance: dict[str, dict[str, str]] = {}
        self.memory_symbol_info: dict[str, Any] = {}

    def seed_orders(self, orders: list[dict[str, Any]], clear = True) -> None:
        if clear:
            self.memory_orders: dict[str, list[dict[str, Any]]] = {}
        for order in orders:
            if self.memory_orders.get(order["symbol"]) is None:
                self.memory_orders[order["symbol"]] = []
            self.memory_orders[order["symbol"]].append(order)

    def get_open_orders(self) -> list[dict[str, Any]]:
        orders: list[dict[str, Any]] = []
        for symbol_orders in self.memory_orders.values():
            for order in symbol_orders:
                if order["status"] in ['NEW', 'PARTIALLY_FILLED', 'PENDING',]:
                    orders.append(order)
        return orders

    def get_all_orders(self, symbol: str) -> list[dict[str, Any]]:
        orders: list[dict[str, Any]] = []
        if self.memory_orders.get(symbol) is None:
            self.memory_orders[symbol] = []
        for order in self.memory_orders.get(symbol):
            orders.append(order)
        return orders

    def get_order(self, orderId: int, symbol: str) -> dict[str, Any]:
        for symbol_orders in self.memory_orders.values():
            for order in symbol_orders:
                if order["orderId"] == orderId:
                    return order
        return {}

    def seed_avg_price(self, avg_price: dict[str, Any]) -> None:
        self.memory_avg_price = avg_price

    def get_avg_price(self, symbol: str) -> dict[str, Any]:
        return self.memory_avg_price.get(symbol, {})

    def seed_historical_klines(self, historical_klines: dict[str, list[list[Any]]]) -> None:
        self.memory_historical_klines = historical_klines

    def get_historical_klines(self, symbol: str, start_str: str, interval: str = KLINE_INTERVAL_1DAY) -> list:
        key = f'{symbol}:{start_str}:{interval}'
        if self.memory_historical_klines.get(key) is None:
            raise BinanceAPIException(response='', status_code='400', text='')
        return self.memory_historical_klines.get(key)

    def seed_asset_balance(self, asset_balance: dict[str, dict[str, str]]) -> None:
        self.memory_asset_balance = asset_balance

    def get_asset_balance(self, asset=None) -> dict[str, Any] | None:
        if asset is None:
            return None
        return self.memory_asset_balance.get(asset, None)

    def seed_symbol_info(self, symbol_info: dict[str, Any]) -> None:
        self.memory_symbol_info = symbol_info

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        return self.memory_symbol_info.get(symbol, {})

    def _check_base_order_params(self, **params: Any) -> bool:
        if params.get('symbol', None) is None or params['symbol'] not in ['ETHUSDT',]:
            raise Exception
        if params.get('side', None) is None or params['side'] not in ['BUY', 'SELL',]:
            raise Exception
        if params.get('type', None) is None or params['type'] not in ['LIMIT',]:
            raise Exception
        if params.get('timeInForce', None) is None or params['timeInForce'] not in ['GTC',]:
            raise Exception
        if params.get('quantity', None) is None or Decimal(params['quantity']) <= 0:
            raise Exception
        if params.get('price', None) is None or Decimal(params['price']) <= 0:
            raise Exception
        return True

    def create_test_order(self, **params: Any) -> dict[str, Any]:
        self._check_base_order_params(**params)
        return {}

    def create_order(self, **params: Any) -> dict[str, Any] | None:
        if self._check_base_order_params(**params):
            params: dict[str, str] = {
                'symbol': 'ETHUSDT',
                'side': 'SELL',
                'type': 'LIMIT',
                'timeInForce': 'GTC',
                'quantity': '0.00720000',
                'price': '4410.00000000',
            }

            new_binance_id: int = 0
            memory_orders_symbol: list[dict[str, Any]] = self.memory_orders.get(params['symbol'], [])
            for memory_order in memory_orders_symbol:
                new_binance_id = memory_order['orderId'] if memory_order['orderId'] > new_binance_id else new_binance_id
            new_binance_id += 1

            cur_time_millis: int = int(time.time() * 1000)

            new_order: dict[str, Any] = {
                'symbol': params['symbol'],
                'orderId': new_binance_id,
                'orderListId': -1,
                'clientOrderId': params.get('newClientOrderId', hash(new_binance_id)),
                'price': params['price'],
                'origQty': params['quantity'],
                'executedQty': '0.00000000',
                'cummulativeQuoteQty': '0.00000000',
                'status': 'NEW',
                'timeInForce': params['timeInForce'],
                'type': 'LIMIT',
                'side': params['side'],
                'stopPrice': '0.00000000',
                'icebergQty': '0.00000000',
                'time': cur_time_millis,
                'updateTime': 0,
                'isWorking': True,
                'workingTime': cur_time_millis,
                'origQuoteOrderQty': '0.00000000',
                'selfTradePreventionMode': 'EXPIRE_MAKER',
            }

            self.memory_orders[params['symbol']].append(new_order)

            return new_order
