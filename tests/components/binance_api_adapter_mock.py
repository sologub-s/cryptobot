from cryptobot.ports.binance_api_adapter import BinanceApiAdapterPort
from tests.ports.binance_api_adapter_mock import BinanceApiAdapterMockPort


class BinanceApiAdapterMock(BinanceApiAdapterMockPort, BinanceApiAdapterPort):
    def __init__(self):
        super().__init__()
        self.memory_my_trades: dict[str, list[dict[str, str|int|bool]]] = {}
        self.memory_asset_transfers: dict[str, dict[str, int]] = {}

    def clear(self) -> None:
        self.memory_my_trades: dict[str, list[dict[str, str|int|bool]]] = {}
        self.memory_asset_transfers: dict[str, dict[str, int]] = {}

    def seed_my_trades(self, my_trades: dict[str, list[dict[str, str | int | bool]]], clear: bool = True) -> None:
        if clear:
            self.memory_my_trades = my_trades
            return None
        for key in my_trades.keys():
            if key not in self.memory_my_trades:
                self.memory_my_trades[key] = my_trades[key]
            else:
                self.memory_my_trades[key] += my_trades[key]
        return None

    def seed_asset_transfers(self, asset_transfers: dict[str, dict[str, int]], clear: bool = True) -> None:
        if clear:
            self.memory_asset_transfers = asset_transfers
            return None
        for key in asset_transfers.keys():
            if key not in self.memory_asset_transfers:
                self.memory_asset_transfers[key] = asset_transfers[key]
            else:
                self.memory_asset_transfers[key] += asset_transfers[key]
        return None

    def request(self, endpoint: str, params: dict) -> dict | list:
        if endpoint == "/api/v3/myTrades":
            symbol: str|None = params.get("symbol", None)
            if symbol is None:
                return []
            if params['fromId'] != 0:
                return []
            return self.memory_my_trades.get(symbol, [])

        if endpoint == "/sapi/v1/asset/transfer":
            type: str|None = params.get("type", None)
            if type is None:
                return {}
            return self.memory_asset_transfers.get(type, {})
        return []
