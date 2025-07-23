import json
from datetime import datetime

from binance.client import Client

class BinanceComponent:
    def __init__(self, client: Client):
        super().__init__()
        self.binance_client = client

    @classmethod
    def create(cls, binance_config: dict):
        return cls(Client(binance_config['api']['key'], binance_config['api']['secret']))

    @property
    def binance_client(self):
        return self.__binance_client

    @binance_client.setter
    def binance_client(self, client: Client):
        self.__binance_client = client

    def get_open_orders(self):
        try:
            orders: dict = self.binance_client.get_open_orders()
            """print(json.dumps(orders, indent=4))"""
            return orders
        except Exception as e:
            print("ERROR: cannot get the list of orders:", e)
            return {}

    def get_order_by_binance_order_id(self, binance_order_id: int, binance_order_symbol: str):
        try:
            order: dict = self.binance_client.get_order(
                orderId = binance_order_id,
                symbol = binance_order_symbol,
            )
            print(json.dumps(order, indent=4))
            return order
        except Exception as e:
            print(f"ERROR: cannot get the order with binance_order_id: {binance_order_id}", e)
            return {}

    def get_price_for_binance_symbol(self, binance_order_symbol: str):
        try:
            price: dict = self.binance_client.get_avg_price(
                symbol = binance_order_symbol,
            )
            print(json.dumps(price, indent=4))
            return price
        except Exception as e:
            print(f"ERROR: cannot get the price for binance_order_symbol: {binance_order_symbol}", e)
            return {}
