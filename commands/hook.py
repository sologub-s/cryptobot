import sys
from logging import info, error

from commands import AbstractCommand, ShowOrderStatusCommand, ShowPriceCommand, ShowOrdersCommand
import json

from components import ServiceComponent
from views.view import View


class HookCommand(AbstractCommand):

    def __init__(self):
        super().__init__()
        self._view = None
        self._initialized = True

    def set_deps(self, service_component: ServiceComponent, view: View):
        self._service_component = service_component
        self._view = view
        return self

    def execute(self):
        if not self._initialized:
            print(f"ERROR: Command {self.__class__.__name__} is NOT initialized")
            return False

        raw_data = sys.stdin.read()
        error(f" raw_data: {type(raw_data)} : {raw_data}")
        try:
            json_dict = json.loads(raw_data)
            chat_id = json_dict["message"]["chat"]["id"]
            text = json_dict["message"]["text"]

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