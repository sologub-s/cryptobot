import datetime
import io
from decimal import Decimal

from cryptobot.commands import AbstractCommand
from cryptobot.components import ServiceComponent
from cryptobot.helpers import dec_to_str
from cryptobot.mappers.order_mapper import OrderMapper
from cryptobot.models import Order
from cryptobot.views.view import View

KLINE_INTERVAL_1SECOND = "1s"
KLINE_INTERVAL_1MINUTE = "1m"
KLINE_INTERVAL_3MINUTE = "3m"
KLINE_INTERVAL_5MINUTE = "5m"
KLINE_INTERVAL_15MINUTE = "15m"
KLINE_INTERVAL_30MINUTE = "30m"
KLINE_INTERVAL_1HOUR = "1h"
KLINE_INTERVAL_2HOUR = "2h"
KLINE_INTERVAL_4HOUR = "4h"
KLINE_INTERVAL_6HOUR = "6h"
KLINE_INTERVAL_8HOUR = "8h"
KLINE_INTERVAL_12HOUR = "12h"
KLINE_INTERVAL_1DAY = "1d"
KLINE_INTERVAL_3DAY = "3d"
KLINE_INTERVAL_1WEEK = "1w"
KLINE_INTERVAL_1MONTH = "1M"

class ShowPriceChartCommand(AbstractCommand):

    def __init__(self):
        super().__init__()
        self._view = None
        self._plt = None

    def set_payload(self, binance_symbol: str, period: str, interval: str, chat_id: int):
        self._payload["binance_symbol"] = binance_symbol
        self._payload["period"] = period
        #print(f'interval: {interval}')
        self._payload["interval"] = interval
        self._payload["chat_id"] = chat_id
        self._initialized = True
        return self

    def set_deps(self, service_component: ServiceComponent, view: View, plt):
        self._service_component = service_component
        self._view = view
        self._plt = plt
        return self

    def execute(self):
        if not self._initialized:
            print(f"ERROR: Command {self.__class__.__name__} is NOT initialized")
            return False

        klines = self._service_component.get_historical_klines(self._payload["binance_symbol"], self._payload["period"], self._payload["interval"])
        price = self._service_component.get_price_for_binance_symbol(self._payload["binance_symbol"])
        #orders = self._service_component.get_open_orders()

        statuses: list[int] = [
            OrderMapper.STATUS_UNKNOWN,
            OrderMapper.STATUS_PENDING_NEW,
            OrderMapper.STATUS_NEW,
            OrderMapper.STATUS_PARTIALLY_FILLED,
            OrderMapper.STATUS_PENDING_CANCEL,
        ]
        db_orders: [Order] = Order.select().where(Order.status.in_(statuses))

        timestamps = []
        high_prices = []
        low_prices = []
        close_prices = []
        average_prices = []
        dates = []
        price_highest: Decimal|None = None
        price_lowest: Decimal|None = None
        for kline in klines:
            timestamps.append(kline['open_time'])
            high_prices.append(kline['high_price'])
            low_prices.append(kline['low_price'])
            close_prices.append(kline['close_price'])
            average_prices.append(kline['average_price'])
            dates.append(datetime.datetime.fromtimestamp(kline['open_time']))
            price_highest = Decimal(kline['high_price']) if price_highest is None else price_highest
            price_highest = Decimal(kline['high_price']) if Decimal(kline['high_price']) > price_highest else price_highest
            price_lowest = Decimal(kline['low_price']) if price_lowest is None else price_lowest
            price_lowest = Decimal(kline['low_price']) if Decimal(kline['low_price']) < price_lowest else price_lowest

        timestamps.append(round(int(price['closeTime']) / 1000))
        high_prices.append(round(Decimal(price['price']), 2))
        low_prices.append(round(Decimal(price['price']), 2))
        close_prices.append(round(Decimal(price['price']), 2))
        average_prices.append(round(Decimal(price['price']), 2))
        dates.append(datetime.datetime.fromtimestamp(round(int(price['closeTime']) / 1000)))

        self._plt.figure(figsize=(10, 5))
        self._plt.fill_between(dates, low_prices, high_prices, color = 'skyblue', alpha = 0.3, label = "Price range (Low-High)")
        self._plt.plot(dates, close_prices, color = 'blue', label = "Close Price", linewidth = 2)

        if price_highest is not None:
            self._plt.axhline(y=round(price_highest, 2), color='skyblue', linestyle="dotted")
            self._plt.text(dates[len(dates)-1], round(price_highest, 2), f"Highest price: {price_highest}", va='bottom', ha='right',  color='skyblue')

        if price_lowest is not None:
            self._plt.axhline(y=round(price_lowest, 2), color='skyblue', linestyle="dotted")
            self._plt.text(dates[len(dates)-1], round(price_lowest, 2), f"Lowest price: {price_lowest}", va='top', ha='right', color='skyblue')

        if len(average_prices):
            self._plt.axhline(y = average_prices[-1], color = "blue", linestyle = "--")
            self._plt.text(dates[0], average_prices[-1], f"Current price: {average_prices[-1]}", va = 'bottom', color = "blue")

        for db_order in db_orders:
            color: str = 'green' if db_order.side == OrderMapper.SIDE_BUY else 'red'
            self._plt.axhline(y = round(db_order.order_price, 2), color = color, linestyle = "--")
            textline: str = f"{round(db_order.order_price, 2)} ({OrderMapper.remap_side(db_order.side).lower()} {round(db_order.original_quantity, 4)}, order amount: {round(db_order.order_price  * db_order.original_quantity, 2)})"
            if db_order.delta_up is not None or db_order.delta_up is not None:
                textline += f", Δ↗:{dec_to_str(db_order.delta_up)+'%' if db_order.delta_up is not None else 'n/a'},Δ↘:{dec_to_str(db_order.delta_down)+'%' if db_order.delta_down is not None else 'n/a'}"
            self._plt.text(dates[0], round(db_order.order_price, 2), textline, va = 'bottom', color=color)

        title: str = f"{self._payload["binance_symbol"]} - Price History (since {self._payload["period"]}, interval {self._payload["interval"]})"
        self._plt.title(title)
        self._plt.xlabel("Date")
        self._plt.ylabel(f"Price ({self._payload["binance_symbol"]})")
        self._plt.legend()
        self._plt.grid(True)

        """
        self._plt.tight_layout()
        self._plt.savefig("chart.png")
        self._plt.close()
        """

        buf = io.BytesIO()
        self._plt.savefig(buf, format = 'png')
        self._plt.close()
        buf.seek(0)

        """
        message = self._view.render('telegram/price.j2', {
            'price': price,
            'binance_symbol': self._payload["binance_symbol"],
        })
        """
        #self._service_component.send_telegram_message(self._payload["chat_id"], json.dumps(klines))
        self._service_component.send_telegram_photo(self._payload["chat_id"], buf, title)
        return True