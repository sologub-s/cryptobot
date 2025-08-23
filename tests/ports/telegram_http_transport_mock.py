# tests/ports/telegram_http_transport_mock_port.py
from typing import Protocol, Any

from tests.classes.TelegramMessageDataObject import TelegramMessageDataObject


class TelegramHttpTransportComponentMockPort(Protocol):
    """Extra control surface for tests (memory operations)."""
    def clear(self) -> None: ...

    def memory_length(self) -> int: ...

    def get_from_memory(self, index: int) -> TelegramMessageDataObject | None: ...
