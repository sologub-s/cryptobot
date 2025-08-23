from dataclasses import dataclass


@dataclass(frozen=True)
class TelegramMessageDataObject:
    url: str
    data: dict | None
    files: dict | None