from dataclasses import dataclass
from typing import Any

import requests
from requests import Response

from tests.ports.telegram_http_transport_mock_port import TelegramHttpTransportComponentMockPort
from cryptobot.ports.telegram_http_transport import TelegramHttpTransportComponentPort

@dataclass(frozen=True)
class TelegramMessage:
    url: str
    data: dict | None
    files: dict | None


class TelegramHttpTransportMockComponent(TelegramHttpTransportComponentMockPort, TelegramHttpTransportComponentPort):

    def __init__(self):
        super().__init__()
        self.messages = []

    def clear(self) -> None:
        self.messages = []

    def memory_length(self) -> int:
        return len(self.messages)

    def get_from_memory(self, index: int) -> dict[str, Any] | None:
        if 0 <= index < len(self.messages):
            return self.messages[index]
        else:
            return None

    def request_post(self, url: str, data: dict | None = None, files: dict | None = None) -> Response | None:
        self.messages.append(TelegramMessage(url=url, data=data, files=files))
        return Response()


