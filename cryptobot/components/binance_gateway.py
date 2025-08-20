from logging import error
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
        try:
            orders: list[dict[str, Any]] = self.binance_client_adapter.get_open_orders()
            return orders
        except Exception as e:
            print("ERROR: cannot get the list of orders:", e)
            return []

    def get_all_orders(self, symbol: str) -> list[dict[str, Any]]:
        try:
            orders: list[dict[str, Any]] = self.binance_client_adapter.get_all_orders(symbol=symbol)
            return orders
        except Exception as e:
            print("ERROR: cannot get the list of orders:", e)
            return []

    def get_order_by_binance_order_id(self, binance_order_id: int, binance_order_symbol: str) -> dict[str, Any]:
        try:
            order: dict[str, Any] = self.binance_client_adapter.get_order(
                orderId=binance_order_id,
                symbol=binance_order_symbol,
            )
            return order
        except Exception as e:
            print(f"ERROR: cannot get the order with binance_order_id: {binance_order_id}", e)
            return {}

    def get_price_for_binance_symbol(self, binance_order_symbol: str) -> dict[str, Any]:
        try:
            price: dict[str, Any] = self.binance_client_adapter.get_avg_price(
                symbol=binance_order_symbol,
            )
            return price
        except Exception as e:
            print(f"ERROR: cannot get the price for binance_order_symbol: {binance_order_symbol}", e)
            return {}

    def get_historical_klines(self, binance_order_symbol: str, period: str, interval: str = KLINE_INTERVAL_1DAY) -> list:
        try:
            klines: list = self.binance_client_adapter.get_historical_klines(
                symbol=binance_order_symbol,
                start_str=period,
                interval=interval,
            )
            return klines
        except Exception as e:
            print(f"ERROR: cannot get the klines for binance_order_symbol: {binance_order_symbol} and period: {period}", e)
            return []

    def get_asset_balance(self, asset=None) -> dict[str, Any]:
        try:

            balance: dict[str, Any] = self.binance_client_adapter.get_asset_balance(
                asset = asset,
            )
            return balance
        except Exception as e:
            print(f"ERROR: cannot get the asset balance for asset: {asset}", e)
            return {}

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        return self.binance_client_adapter.get_symbol_info(symbol)

    def create_test_order(self, **params: Any) -> dict[str, Any]:
        return self.binance_client_adapter.create_test_order(**params)

    def create_order(self, **params: Any) -> dict[str, Any]:
        return self.binance_client_adapter.create_order(**params)

    def get_all_trades(self, binance_symbol: str) -> list[dict]:
        params: dict = {
            "symbol": binance_symbol,
            "limit": 1000,
            "fromId": 0,
        }

        result_list: list[dict] = []
        tries: int = 0

        while True and tries < 1000:
            tries += 1
            # @TODO add try..except
            partial_list: list[dict] = self.binance_api_adapter.request(endpoint="/api/v3/myTrades", params=params)
            for trade in partial_list:
                if int(trade['id']) > params['fromId']:
                    params['fromId'] = int(trade['id'])
            params['fromId'] += 1
            result_list += partial_list
            if len(partial_list) == 0:
                break
            if tries == 1000:
                error(f"max load myTrades tries: '{tries}'")

        return result_list

    """
    Get internal transfers history (Spot-to-Funding and vise-versa).
    transfer_type: MAIN_FUNDING, FUNDING_MAIN, MAIN_UMFUTURE, ...
    """
    def get_asset_transfer(self, type, start_time=None, end_time=None, limit=100):
        params = {
            "limit": limit,
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if type:
            params["type"] = type

        # @TODO clarify return structure/type
        return self.binance_api_adapter.request(endpoint="/sapi/v1/asset/transfer", params=params)

    def get_asset_ledger(self, asset=None, start_time=None, end_time=None, limit=500):
        params = {
            "limit": limit,
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if asset:
            params["asset"] = asset

        # @TODO clarify return structure/type
        return self.binance_api_adapter.request(endpoint="/sapi/v1/asset/ledger", params=params)