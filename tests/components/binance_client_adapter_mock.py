from typing import Any

from binance import Client, BinanceAPIException

from cryptobot.commands.show_price_chart import KLINE_INTERVAL_1DAY
from cryptobot.ports.binance_client_adapter import BinanceClientAdapterPort
from tests.ports.binance_client_adapter_mock import BinanceClientAdapterMockPort


class BinanceClientAdapterMock(BinanceClientAdapterMockPort, BinanceClientAdapterPort):
    def __init__(self,):
        super().__init__()
        self.memory_orders: dict[str, list[dict[str, Any]]] = {}
        self.memory_avg_price: dict[str, list[dict[str, Any]]] = {}
        self.memory_historical_klines: dict[str, list[list[Any]]] = {}
        self.memory_asset_balance: dict[str, dict[str, str]] = {}

    @classmethod
    def create(cls,):
        return cls()

    def clear(self) -> None:
        self.memory_orders: dict[str, list[dict[str, Any]]] = {}
        self.memory_avg_price: dict[str, list[dict[str, Any]]] = {}
        self.memory_historical_klines: dict[str, list[list[Any]]] = {}
        self.memory_asset_balance: dict[str, dict[str, str]] = {}

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

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        return self.binance_client.get_symbol_info(symbol)

    def create_test_order(self, **params: Any) -> dict[str, Any]:
        return self.binance_client.create_test_order(**params)

    def create_order(self, **params: Any) -> dict[str, Any]:
        return self.binance_client.create_order(**params)