from cryptobot.commands import AbstractCommand
from cryptobot.components import ServiceComponent
from cryptobot.views.view import View

class ShowPriceChartOptionsCommand(AbstractCommand):

    def __init__(self):
        super().__init__()
        self._view = None

    def set_payload(self, binance_symbol: str, chat_id: int):
        self._payload["binance_symbol"] = binance_symbol
        self._payload["chat_id"] = chat_id
        self._initialized = True
        return self

    def set_deps(self, service_component: ServiceComponent, view: View):
        self._service_component = service_component
        self._view = view
        return self

    def execute(self):
        if not self._initialized:
            print(f"ERROR: Command {self.__class__.__name__} is NOT initialized")
            return False
        message = self._view.render('telegram/price_chart_options.j2', {
            'binance_symbol': self._payload["binance_symbol"],
        })

        keys = [
            f"show_price_chart:{self._payload["binance_symbol"]}:1_year_ago_UTC:1M",
            f"show_price_chart:{self._payload["binance_symbol"]}:6_months_ago_UTC:1M",
            f"show_price_chart:{self._payload["binance_symbol"]}:3_months_ago_UTC:1w",
            f"show_price_chart:{self._payload["binance_symbol"]}:1_months_ago_UTC:1d",
            f"show_price_chart:{self._payload["binance_symbol"]}:1_week_ago_UTC:1d",
            f"show_price_chart:{self._payload["binance_symbol"]}:3_days_ago_UTC:1h",
            f"show_price_chart:{self._payload["binance_symbol"]}:1_day_ago_UTC:1h",
            f"show_price_chart:{self._payload["binance_symbol"]}:3_hours_ago_UTC:1m",
            f"show_price_chart:{self._payload["binance_symbol"]}:1_hour_ago_UTC:1m",
        ]
        inline_keyboard: list = []
        for key in keys:
            inline_keyboard.append([{"text": key, "callback_data": key},])

        self._service_component.send_telegram_message(self._payload["chat_id"], message, inline_keyboard)
        self._service_component.send_telegram_message(self._payload["chat_id"], self._view.render('telegram/or_choose_another_option.j2', {}))
        return True