from typing import Protocol, runtime_checkable


@runtime_checkable
class BinanceApiAdapterPort(Protocol):
    def __init__(self,
        base_url: str,
        binance_api_key: str,
        binance_api_secret: str,
    ): ...

    def request(self, endpoint: str, params: dict) -> dict | list: ...