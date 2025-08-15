import json
from io import BytesIO

from requests import Response

from cryptobot.helpers import slugify

import requests

from cryptobot.ports.telegram import TelegramComponentPort
from cryptobot.ports.telegram_http_transport import TelegramHttpTransportComponentPort


class TelegramComponent(TelegramComponentPort):

    def __init__(self, bot_token: str, bot_api_secret_token: str, telegram_http_transport_component: TelegramHttpTransportComponentPort):
        super().__init__(bot_token, bot_api_secret_token, telegram_http_transport_component)
        self.bot_token = bot_token
        self.bot_api_secret_token = bot_api_secret_token
        self.telegram_http_transport_component = telegram_http_transport_component

    @classmethod
    def create(cls, telegram_config: dict, telegram_http_transport_component: TelegramHttpTransportComponentPort):
        return cls(telegram_config["bot_token"], telegram_config["bot_api_secret_token"], telegram_http_transport_component)

    @property
    def bot_token(self):
        return self.__bot_token

    @bot_token.setter
    def bot_token(self, bot_token: str):
        self.__bot_token = bot_token

    @property
    def bot_api_secret_token(self):
        return self.__bot_api_secret_token

    @bot_api_secret_token.setter
    def bot_api_secret_token(self, bot_api_secret_token: str):
        self.__bot_api_secret_token = bot_api_secret_token

    def get_reply_markup(self):
        return\
            {
                "keyboard": [
                    #["show_orders", "status"],
                    ["show_orders",],
                    ["show_settings",],
                    ["show_price:ETHUSDT",],
                    ["show_price_chart_options:ETHUSDT",],
                ],
                "resize_keyboard": True,
                "one_time_keyboard": False
            }

    def check_telegram_bot_api_secret_token(self, bot_api_secret_token: str) -> bool:
        return bot_api_secret_token == self.__bot_api_secret_token

    def send_telegram_message(self, chat_id: int, text: str, inline_keyboard: list = [], disable_notification=False, parse_mode="HTML"):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        reply_markup = self.get_reply_markup()
        if inline_keyboard:
            del reply_markup["keyboard"]
            reply_markup['inline_keyboard'] = inline_keyboard

        #print(json.dumps(reply_markup, indent=4))

        data = {
            "chat_id": chat_id,
            "text": text,
            "disable_notification": disable_notification,
            "parse_mode": parse_mode,
            "reply_markup": json.dumps(reply_markup),
        }

        return self.telegram_http_transport_component.request_post(url, data = data)

    def send_telegram_photo(self, chat_id: int, photo_buf: BytesIO, photo_name: str = None, parse_mode = "HTML"):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
        reply_markup = self.get_reply_markup()
        #if inline_keyboard:
            #reply_markup['inline_keyboard'] = inline_keyboard
        files = {"photo": photo_buf}
        if photo_name:
           files = {"photo": (slugify(photo_name) + ".png", photo_buf, "image/png")}
        data = {
            "chat_id": chat_id,
            "caption": photo_name,
            "reply_markup": json.dumps(reply_markup),
        }
        return self.telegram_http_transport_component.request_post(url, data = data, files = files)