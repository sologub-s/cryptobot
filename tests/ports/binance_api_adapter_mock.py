from typing import Protocol, runtime_checkable, Any

from binance import KLINE_INTERVAL_1DAY
from binance.client import Client


@runtime_checkable
class BinanceApiAdapterMockPort(Protocol):

    def clear(self) -> None: ...

    def seed_my_trades(self, my_trades: dict[str, list[dict[str, str | int | bool]]], clear: bool = True) -> None: ...

    def seed_asset_transfers(self, asset_transfers: dict[str, dict[str, int]], clear: bool = True) -> None: ...