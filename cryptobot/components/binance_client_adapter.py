from typing import Any

from binance import Client

from cryptobot.commands.show_price_chart import KLINE_INTERVAL_1DAY
from cryptobot.ports.binance_client_adapter import BinanceClientAdapterPort


class BinanceClientAdapter(BinanceClientAdapterPort):
    def __init__(
            self,
            binance_client: Client,
    ):
        super().__init__(binance_client)
        self.binance_client = binance_client

    @classmethod
    def create(
        cls,
        binance_client: Client,
    ):
        return cls(
            binance_client=binance_client,
        )

    def get_open_orders(self) -> list[dict[str, Any]]:
        try:
            orders: list[dict[str, Any]] = self.binance_client.get_open_orders()
            """print(json.dumps(orders, indent=4))"""
            return orders
        except Exception as e:
            print("ERROR: cannot get the list of orders:", e)
            return []

    def get_all_orders(self, symbol: str) -> list[dict[str, Any]]:
        try:
            orders: list[dict[str, Any]] = self.binance_client.get_all_orders(symbol=symbol)
            """print(json.dumps(orders, indent=4))"""
            return orders
        except Exception as e:
            print("ERROR: cannot get the list of orders:", e)
            return []

    def get_order_by_binance_order_id(self, binance_order_id: int, binance_order_symbol: str) -> dict[str, Any]:
        try:
            order: dict[str, Any] = self.binance_client.get_order(
                orderId=binance_order_id,
                symbol=binance_order_symbol,
            )
            return order
        except Exception as e:
            print(f"ERROR: cannot get the order with binance_order_id: {binance_order_id}", e)
            return {}

    def get_price_for_binance_symbol(self, binance_order_symbol: str) -> dict[str, Any]:
        try:
            price: dict[str, Any] = self.binance_client.get_avg_price(
                symbol=binance_order_symbol,
            )
            return price
        except Exception as e:
            print(f"ERROR: cannot get the price for binance_order_symbol: {binance_order_symbol}", e)
            return {}

    def get_historical_klines(self, binance_order_symbol: str, period: str, interval: str = KLINE_INTERVAL_1DAY) -> list:
        try:
            klines: list = self.binance_client.get_historical_klines(
                symbol = binance_order_symbol,
                start_str = period,
                interval = interval,
            )
            return klines
        except Exception as e:
            print(f"ERROR: cannot get the klines for binance_order_symbol: {binance_order_symbol} and period: {period}", e)
            return []

    def get_asset_balance(self, asset=None) -> dict[str, Any]:
        try:

            balance: dict[str, Any] = self.binance_client.get_asset_balance(
                asset = asset,
            )
            return balance
        except Exception as e:
            print(f"ERROR: cannot get the asset balance for asset: {asset}", e)
            return {}

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        return self.binance_client.get_symbol_info(symbol)

    def create_test_order(self, **params: Any) -> dict[str, Any]:
        return self.binance_client.create_test_order(**params)

    def create_order(self, **params: Any) -> dict[str, Any]:
        return self.binance_client.create_order(**params)