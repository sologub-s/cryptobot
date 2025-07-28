import asyncio
import os
import matplotlib

from helpers import current_millis
from models import Order, CronJob

matplotlib.use('Agg')
import matplotlib.pyplot as plt

import requests

from commands import AbstractCommand
import json

from components import ServiceComponent
from components import BinanceComponent
from views.view import View

from binance import AsyncClient, BinanceSocketManager, ThreadedWebsocketManager


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
        print('Misc...')
        return True

    def test_cron_jobs_insert(self):

        # SELECT * FROM cron_jobs WHERE (last_executed_at IS NULL) OR (last_executed_at + execution_interval_seconds * 1000 <= UNIX_TIMESTAMP(NOW(3)) * 1000) ;
        cron_jobs_list: list = [
            {
                'name': 'check-all-orders-from-binance',
                'execution_interval_seconds': 60,
            },

            {
                'name': 'notify-working',
                'execution_interval_seconds': 14400,
            },
            {
                'name': 'check-balance-from-binance',
                'execution_interval_seconds': 180,
            },
        ]

        for cron_job_dict in cron_jobs_list:
            cron_job = CronJob().fill(cron_job_dict)
            if not cron_job.validate():
                print(f'CronJob validation failed: {cron_job.get_validation_errors()}')
            else:
                print(f'Save {cron_job.name}: {cron_job.save()}')

    def test_upsert(self):
        bc = self._service_component.binance_component.binance_client

        all_orders = bc.get_all_orders(symbol = 'ETHUSDT')
        #print(json.dumps(all_orders, indent = 4))

        for binance_order in all_orders:
            order = Order().fill_from_binance(binance_order)
            print(order.as_dict())
            print(order.upsert())
            print(order.as_dict())
            print('-----------------------')


        return True

    async def s(self):
        client = await AsyncClient.create()
        bm = BinanceSocketManager(client)
        # start any sockets here, i.e a trade socket
        ts = bm.trade_socket('BNBBTC')
        # then start receiving messages
        async with ts as tscm:
            while True:
                res = await tscm.recv()
                print(res)

        await client.close_connection()

    def test_websocket(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.s())
        return

    def test_plt(self):
        x = [1, 2, 3, 4, 5]
        y = [10, 20, 15, 30, 25]

        plt.plot(x, y, label="Price")
        plt.axhline(y=22, color="red", linestyle="--", label="Order Level")
        plt.legend()
        plt.title("ETH/USDT - Week Chart")
        plt.savefig("chart.png")  # Зберегти картинку
        plt.close()

    def test_view(self):
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