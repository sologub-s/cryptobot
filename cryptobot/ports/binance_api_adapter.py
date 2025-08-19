from typing import Protocol, runtime_checkable


@runtime_checkable
class BinanceApiAdapterPort(Protocol):
    def __init__(self,
        base_url: str,
        binance_api_key: str,
        binance_api_secret: str,
    ): ...

    def get_all_trades(self, binance_symbol: str) -> list[dict]: ...

    """
    Get internal transfers history (Spot-to-Funding and vise-versa).
    transfer_type: MAIN_FUNDING, FUNDING_MAIN, MAIN_UMFUTURE, ...
    """
    def get_asset_transfer(self, type, start_time=None, end_time=None, limit=100): ...

    def get_asset_ledger(self, asset=None, start_time=None, end_time=None, limit=500): ...