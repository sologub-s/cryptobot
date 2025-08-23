from dataclasses import dataclass
from typing import Any

import requests
from requests import Response

from tests.classes.TelegramMessageDataObject import TelegramMessageDataObject
from tests.ports.telegram_http_transport_mock import TelegramHttpTransportComponentMockPort
from cryptobot.ports.telegram_http_transport import TelegramHttpTransportComponentPort


class TelegramHttpTransportMockComponent(TelegramHttpTransportComponentMockPort, TelegramHttpTransportComponentPort):

    def __init__(self):
        super().__init__()
        self.messages: list[TelegramMessageDataObject] = []

    def clear(self) -> None:
        self.messages: list[TelegramMessageDataObject] = []

    def memory_length(self) -> int:
        return len(self.messages)

    def get_from_memory(self, index: int) -> TelegramMessageDataObject | None:
        if 0 <= index < len(self.messages):
            return self.messages[index]
        else:
            return None

    def request_post(self, url: str, data: dict | None = None, files: dict | None = None) -> Response | None:
        self.messages.append(TelegramMessageDataObject(url=url, data=data, files=files))
        return Response()


