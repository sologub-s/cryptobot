import sys
from logging import info, error

from commands import AbstractCommand, ShowOrderStatusCommand
from commands import ShowPriceCommand, ShowPriceChartOptionsCommand, ShowPriceChartCommand
from commands import ShowOrdersCommand
import json

from components import ServiceComponent
from views.view import View


class HookCommand(AbstractCommand):

    def __init__(self):
        super().__init__()
        self._view = None
        self._plt = None
        self._initialized = True

    def set_deps(self, service_component: ServiceComponent, view: View, plt):
        self._service_component = service_component
        self._view = view
        self._plt = plt
        return self

    def execute(self):
        if not self._initialized:
            print(f"ERROR: Command {self.__class__.__name__} is NOT initialized")
            return False

        raw_data = sys.stdin.read()
        error(f" raw_data: {type(raw_data)} : {raw_data}")
        try:
            json_dict = json.loads(raw_data)
            if json_dict.get('message'):
                chat_id = json_dict["message"]["chat"]["id"]
                text = json_dict["message"]["text"]
            elif json_dict.get('callback_query'):
                chat_id = json_dict["callback_query"]["message"]["chat"]["id"]
                text = json_dict["callback_query"]["data"]
            else:
                error(f"Cannot find neither 'message' nor 'callback_query' in {json.dumps(json_dict)}")
                return False

            if text.startswith("/start"):
                text = text.replace("/start", "", 1)

            if text.lower() == "show_orders":
                command = (ShowOrdersCommand()
                           .set_payload(chat_id)
                           .set_deps(self._service_component, self._view)
                           )
                command.execute()

            elif text.lower().startswith("show_order_status:"):
                text = text.replace(" ", "")
                binance_order_id = text.split(":")[1]
                binance_symbol = text.split(":")[2].upper()

                command = (ShowOrderStatusCommand()
                           .set_payload(binance_order_id, binance_symbol, chat_id)
                           .set_deps(self._service_component, self._view)
                           )
                command.execute()

            elif text.lower().startswith("show_price_chart:"):
                text = text.replace(" ", "")
                binance_symbol = text.split(":")[1].upper()
                period = text.split(":")[2].replace("_", " ")
                interval = text.split(":")[3]
                command = (ShowPriceChartCommand()
                           .set_payload(binance_symbol, period, interval, chat_id)
                           .set_deps(self._service_component, self._view, self._plt)
                           )
                command.execute()

            elif text.lower().startswith("show_price_chart_options:"):
                text = text.replace(" ", "")
                binance_symbol = text.split(":")[1].upper()
                command = (ShowPriceChartOptionsCommand()
                           .set_payload(binance_symbol, chat_id)
                           .set_deps(self._service_component, self._view)
                           )
                command.execute()

            elif text.lower().startswith("show_price:"):
                text = text.replace(" ", "")
                binance_symbol = text.split(":")[1].upper()
                command = (ShowPriceCommand()
                           .set_payload(binance_symbol, chat_id)
                           .set_deps(self._service_component, self._view)
                           )
                command.execute()

            else:
                self._service_component.telegram_component.send_telegram_message(chat_id, "Unknown command: " + text)
        except json.JSONDecodeError:
            print("Invalid JSON input")
            return False
        return True