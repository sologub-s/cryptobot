from typing import Protocol, runtime_checkable


@runtime_checkable
class BinanceApiAdapterPort(Protocol):

    def request(self, endpoint: str, params: dict) -> dict | list: ...