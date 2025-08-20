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
        return self.binance_client.get_open_orders()

    def get_all_orders(self, symbol: str) -> list[dict[str, Any]]:
        return self.binance_client.get_all_orders(symbol=symbol)

    def get_order(self, orderId: int, symbol: str) -> dict[str, Any]:
        return self.binance_client.get_order(orderId=orderId, symbol=symbol)

    def get_avg_price(self, symbol: str) -> dict[str, Any]:
        return self.binance_client.get_avg_price(symbol=symbol)

    def get_historical_klines(self, symbol: str, start_str: str, interval: str = KLINE_INTERVAL_1DAY) -> list:
        return self.binance_client.get_historical_klines(symbol=symbol, start_str=start_str, interval=interval)

    def get_asset_balance(self, asset=None) -> dict[str, Any] | None:
        return self.binance_client.get_asset_balance(asset=asset)

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        return self.binance_client.get_symbol_info(symbol)

    def create_test_order(self, **params: Any) -> dict[str, Any]:
        return self.binance_client.create_test_order(**params)

    def create_order(self, **params: Any) -> dict[str, Any]:
        return self.binance_client.create_order(**params)