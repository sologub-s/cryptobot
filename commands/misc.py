import os
import sys
from logging import info, error
from pprint import pprint

import requests
from flask import jsonify

from commands import AbstractCommand
import json

from components import ServiceComponent
from components import BinanceComponent
from views.view import View


class MiscCommand(AbstractCommand):

    def __init__(self):
        super().__init__()
        self._view = None
        self._initialized = True

    def set_deps(self, service_component: ServiceComponent, view: View):
        self._service_component = service_component
        self._view = view
        return self

    def execute(self):
        #print("OK, let's go...")
        print(self._view.render('some.j2', {
            'name': 'Serhii',
        }))

    def test_tlg(self):
        #tc = self._service_component.telegram_component
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        reply_markup = json.dumps({
            "keyboard": [
                ["show_orders", "status"],
                ["show_price:ETHUSDT"],
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        })

        reply_markup = json.dumps({
            "remove_keyboard": True,
        })

        data = {
            "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
            "text": '<a href="https://t.me/'+os.getenv("TELEGRAM_BOT_USERNAME", "")+'?start=show_orders">show_orders</a>',
            "parse_mode": 'HTML',
            "reply_markup": reply_markup,
            "resize_keyboard": True,
            "one_time_keyboard": False,
        }
        response = requests.post(url, data = data)
        #result = tc.send_telegram_message()

        print(response.json())