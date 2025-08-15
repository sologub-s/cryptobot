from typing import Protocol, runtime_checkable

from requests import Response


@runtime_checkable
class TelegramHttpTransportComponentPort(Protocol):

    def request_post(self, url: str, data: dict | None = None, files: dict | None = None) -> Response | None: ...