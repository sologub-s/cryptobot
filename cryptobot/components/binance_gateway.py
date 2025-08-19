from typing import Any

from binance import KLINE_INTERVAL_1DAY

from cryptobot.ports.binance_api_adapter import BinanceApiAdapterPort
from cryptobot.ports.binance_client_adapter import BinanceClientAdapterPort
from cryptobot.ports.binance_gateway import BinanceGatewayPort


class BinanceGateway(BinanceGatewayPort):
    def __init__(
            self,
            binance_client_adapter: BinanceClientAdapterPort,
            binance_api_adapter: BinanceApiAdapterPort,
    ):
        super().__init__(binance_client_adapter, binance_api_adapter)
        self.binance_client_adapter = binance_client_adapter
        self.binance_api_adapter = binance_api_adapter

    @classmethod
    def create(
        cls,
        binance_client_adapter: BinanceClientAdapterPort,
        binance_api_adapter: BinanceApiAdapterPort,
    ):
        return cls(
            binance_client_adapter=binance_client_adapter,
            binance_api_adapter=binance_api_adapter,
        )

    def get_open_orders(self) -> list[dict[str, Any]]:
        return self.binance_client_adapter.get_open_orders()

    def get_all_orders(self, symbol: str) -> list[dict[str, Any]]:
        return self.binance_client_adapter.get_all_orders(symbol)

    def get_order_by_binance_order_id(self, binance_order_id: int, binance_order_symbol: str) -> dict[str, Any]:
        return self.binance_client_adapter.get_order_by_binance_order_id(binance_order_id, binance_order_symbol)

    def get_price_for_binance_symbol(self, binance_order_symbol: str) -> dict[str, Any]:
        return self.binance_client_adapter.get_price_for_binance_symbol(binance_order_symbol)

    def get_historical_klines(self, binance_order_symbol: str, period: str, interval: str = KLINE_INTERVAL_1DAY) -> list:
        return self.binance_client_adapter.get_historical_klines(binance_order_symbol, period, interval)

    def get_asset_balance(self, asset=None) -> dict[str, Any]:
        return self.binance_client_adapter.get_asset_balance(asset)

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        return self.binance_client_adapter.get_symbol_info(symbol)

    def create_test_order(self, **params: Any) -> dict[str, Any]:
        return self.binance_client_adapter.create_test_order(**params)

    def create_order(self, **params: Any) -> dict[str, Any]:
        return self.binance_client_adapter.create_order(**params)

    def get_all_trades(self, binance_symbol: str) -> list[dict]:
        return self.binance_api_adapter.get_all_trades(binance_symbol)

    """
    Get internal transfers history (Spot-to-Funding and vise-versa).
    transfer_type: MAIN_FUNDING, FUNDING_MAIN, MAIN_UMFUTURE, ...
    """
    def get_asset_transfer(self, type, start_time=None, end_time=None, limit=100):
        return self.binance_api_adapter.get_asset_transfer(type, start_time, end_time, limit)

    def get_asset_ledger(self, asset=None, start_time=None, end_time=None, limit=500):
        return self.binance_api_adapter.get_asset_ledger(asset, start_time, end_time, limit)