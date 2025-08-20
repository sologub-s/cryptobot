from typing import Protocol, runtime_checkable, Any

from binance import KLINE_INTERVAL_1DAY
from binance.client import Client


@runtime_checkable
class BinanceClientAdapterMockPort(Protocol):

    def clear(self) -> None: ...

    def seed_orders(self, orders: list[dict[str, Any]], clear: bool = True) -> None: ...

    def seed_avg_price(self, avg_price: dict[str, Any]) -> None: ...

    def seed_historical_klines(self, historical_klines: dict[str, list[list[Any]]]) -> None: ...

    def seed_asset_balance(self, asset_balance: dict[str, dict[str, str]]) -> None: ...