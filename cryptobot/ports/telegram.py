from typing import Protocol, runtime_checkable
from io import BytesIO

from cryptobot.ports.telegram_http_transport import TelegramHttpTransportComponentPort


@runtime_checkable
class TelegramComponentPort(Protocol):
    def __init__(self, bot_token: str, bot_api_secret_token: str, telegram_transport_component: TelegramHttpTransportComponentPort): ...

    @classmethod
    def create(cls, telegram_config: dict, telegram_transport_component: TelegramHttpTransportComponentPort): ...

    @property
    def bot_token(self): ...

    @bot_token.setter
    def bot_token(self, bot_token: str): ...

    @property
    def bot_api_secret_token(self): ...

    @bot_api_secret_token.setter
    def bot_api_secret_token(self, bot_api_secret_token: str): ...

    def check_telegram_bot_api_secret_token(self, bot_api_secret_token: str) -> bool: ...

    def send_telegram_message(self, chat_id: int, text: str, inline_keyboard: list = [], disable_notification=False, parse_mode="HTML"): ...

    def send_telegram_photo(self, chat_id: int, photo_buf: BytesIO, photo_name: str = None, parse_mode = "HTML"): ...