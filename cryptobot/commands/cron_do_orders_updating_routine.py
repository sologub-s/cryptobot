from decimal import Decimal
from time import sleep

from cryptobot.commands import AbstractCommand
from cryptobot.components import ServiceComponent
from cryptobot.mappers.balance_mapper import BalanceMapper
from cryptobot.mappers.order_mapper import OrderMapper
from cryptobot.models import Order
from cryptobot.views.view import View
from cryptobot.helpers import current_millis, increase_price_percent, decrease_price_percent, dec_to_str, \
    l, sg

import logging
from logging import error, info, warning

from cryptobot.views.view_helper import to_eng_string

logging.basicConfig(level=logging.INFO)

millis_on_start = current_millis() - 10000 # dirty bidlokod

class CronDoOrdersUpdatingRoutineCommand(AbstractCommand):

    def __init__(self):
        super().__init__()
        self._view = None

    def set_payload(self, chat_id: int):
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
        
        info(f"CronDoOrdersUpdatingRoutine execution started")

        # get all orders from db
        db_orders: dict[int, Order] = self._service_component.get_all_db_orders_indexed()
        info(f"len(db_orders): '{len(db_orders)}'")

        # collect all symbols
        symbols: list[str] = []
        for order in db_orders.values():
            symbols.append(OrderMapper.remap_symbol(order.symbol))
        symbols = list(set(symbols)) # array_unique
        info(f"symbols: {symbols}")

        # get all orders from binance for each symbol
        binance_orders: list[dict] = self.func_get_binance_orders(symbols=symbols)
        del symbols

        for binance_order in binance_orders:
            info(f"iteration : binance_order_id '{binance_order['orderId']}'")
            # upsert order into db if not exists
            if binance_order['orderId'] not in db_orders:
                db_order = self.func_upsert_binance_order_and_notify(
                    binance_order=binance_order,
                    chat_id=self._payload["chat_id"],
                )
            else: # if order exists - take it from collection of existed orders
                db_order = db_orders[binance_order['orderId']]
                info(f"existed db_order.id: '{db_order.id}'")

            # remember old order's status
            old_db_order_status = db_order.status
            info(f"old_db_order_status: '{old_db_order_status}'")

            db_order.binance_created_at = binance_order.get('updateTime', None) if db_order.binance_created_at is None else db_order.binance_created_at
            db_order.binance_updated_at = binance_order.get('updateTime', None)
            db_order.save()

            # if executedQty has changed - order's filling happened (it may be partial)
            if Decimal(binance_order['executedQty']) != Decimal(db_order.executed_quantity):
                db_order = self.func_handle_quantity_change_and_notify(
                    binance_order=binance_order,
                    db_order=db_order,
                    millis_on_start=millis_on_start,
                    chat_id=self._payload["chat_id"],
                )

            # if order's status has changed
            mapped_binance_order_status = OrderMapper.map_status(binance_order['status'])
            if old_db_order_status != mapped_binance_order_status:
                db_order = self.func_handle_order_status_change(
                    db_order=db_order,
                    old_db_order_status=old_db_order_status,
                    mapped_binance_order_status=mapped_binance_order_status,
                    chat_id=self._payload["chat_id"],
                )

                # if status has changed and the new status is in [CANCELLED, PARTIALLY_FILLED, FILLED]
                if db_order.status in [
                    OrderMapper.STATUS_CANCELED,
                    OrderMapper.STATUS_PARTIALLY_FILLED,
                    OrderMapper.STATUS_FILLED,
                ]:
                    # load and upsert trades for the db_order
                    self._service_component.update_trades_from_binance_to_db(order_ids=[db_order.id],)
                    db_order.trades_checked = True
                    db_order.save()
                    info(f"db_order.id#{db_order.id} trades_checked: '{db_order.trades_checked}'")

                # if status has changed and the new status is FILLED then place new order
                if db_order.status == OrderMapper.STATUS_FILLED:
                    self.proc_place_new_binance_order(db_order=db_order, chat_id=self._payload["chat_id"])

        return True

    def func_get_binance_orders(self, symbols: list[str]) -> list[dict]:
        binance_orders: list[dict] = []
        for symbol in symbols:
            binance_orders += self._service_component.get_all_orders(symbol=symbol)
        info(f"len(binance_orders): '{len(binance_orders)}'")
        return binance_orders

    def func_upsert_binance_order_and_notify(self, binance_order: dict, chat_id: int) -> Order:
        info(f"writing binance_order#{binance_order['orderId']} to database...")
        db_order = self._service_component.create_or_update_db_order(binance_order)
        info(f"new db_order.id: '{db_order.id}'")
        # notify about new order creation
        self._service_component.notify_order_created(
            chat_id=chat_id,
            db_order=db_order,
        )
        # show new order's status
        self._service_component.show_order_status(
            db_order=db_order,
            chat_id=chat_id,
        )
        return db_order

    def func_handle_quantity_change_and_notify(self, binance_order: dict, db_order: Order, millis_on_start: int, chat_id: int) -> Order:
        info(
            f"order's qty changed: '{to_eng_string(Decimal(binance_order['executedQty']))}' != '{to_eng_string(Decimal(db_order.executed_quantity))}'")
        # save `orders_filling_history`
        info(f"saving `orders_filling_history` for db_order.id = '{db_order.id}'")
        if not self._service_component.write_orders_filling_history(
                binance_order=binance_order,
                db_order_id=db_order.id,
                logged_at=millis_on_start - 1,
        ):
            error(
                f"ERROR: Cannot write `orders_filling_history` for db_order.id: '{db_order.id}' and binance_order: '{binance_order}'")

        # remember old quantities
        old_executed_quantity = db_order.executed_quantity
        old_cummulative_quote_quantity = db_order.cummulative_quote_quantity
        info(f"old_executed_quantity: '{to_eng_string(old_executed_quantity)}'")
        info(f"old_cummulative_quote_quantity: '{to_eng_string(old_cummulative_quote_quantity)}'")
        # change db_order's quantity
        info(f"changing db_order.id#{db_order.id} quantities...")
        #db_order = self._service_component.create_or_update_db_order(binance_order)
        db_order.fill_from_binance(binance_order)
        db_order.save()
        info(f"changing db_order.id#{db_order.id} executed_quantity: '{to_eng_string(db_order.executed_quantity)}'")
        info(
            f"changing db_order.id#{db_order.id} cummulative_quote_quantity: '{to_eng_string(db_order.cummulative_quote_quantity)}'")
        # send telegram notification
        self._service_component.notify_order_quantity_changed(
            db_order=db_order,
            old_executed_quantity=old_executed_quantity,
            old_cummulative_quote_quantity=old_cummulative_quote_quantity,
            chat_id=chat_id,
        )
        return db_order

    def func_handle_order_status_change(self, db_order: Order, old_db_order_status: int, mapped_binance_order_status: int, chat_id: int) -> Order:
        info(f"db_order.id#{db_order.id} status change: '{old_db_order_status}' != '{mapped_binance_order_status}'")

        # save new status to db
        # previous_status: str = find_first_key_by_value(OrderMapper.status_mapping, db_order.status, 'UNKNOWN')
        db_order.status = mapped_binance_order_status
        db_order.trades_checked = False
        db_order.save()
        info(f"db_order.id#{db_order.id} status: '{db_order.status}'")
        info(f"db_order.id#{db_order.id} trades_checked: '{db_order.trades_checked}'")
        # update assets balances
        sleep(1)
        self._service_component.update_assets_from_binance_to_db(
            assets=BalanceMapper.get_assets().keys(),
            force_insert=True,
        )

        # notify about order's status change
        self._service_component.notify_order_status_changed(
            db_order=db_order,
            previous_status=old_db_order_status,
            chat_id=chat_id,
        )
        self._service_component.show_order_status(
            db_order=db_order,
            chat_id=chat_id,
        )
        return db_order

    def proc_place_new_binance_order(self, db_order: Order, chat_id: int):
        l(self._service_component, f"db_order.id#{db_order.id} status is 'FILLED' ('{db_order.status}')", 'info', chat_id)
        # creating new order
        l(self._service_component, f"starting to create new binance order...", 'info', chat_id)
        order_params: dict = {
            'chat_id': chat_id,
            'db_symbol': db_order.symbol,
        }
        delta: Decimal = Decimal('5')
        delta_up: Decimal = db_order.delta_up if db_order.delta_up is not None else delta
        delta_down: Decimal = db_order.delta_down if db_order.delta_down is not None else delta
        if db_order.side == OrderMapper.SIDE_BUY:
            order_params['db_side'] = OrderMapper.SIDE_SELL
            order_params['str_price'] = dec_to_str(increase_price_percent(Decimal(db_order.order_price), delta_up))
        if db_order.side == OrderMapper.SIDE_SELL:
            order_params['db_side'] = OrderMapper.SIDE_BUY
            order_params['str_price'] = dec_to_str(decrease_price_percent(Decimal(db_order.order_price), delta_down))
        l(self._service_component, f"params for new binance order: '{order_params}'", 'info', chat_id)

        if order_params['db_side'] == OrderMapper.SIDE_SELL and not sg('autocreate_sell_order'):
            l(self._service_component, f"new_binance_order side is 'SELL' and autocreate_sell_order is {sg('autocreate_sell_order')} - the new order WILL NOT be created", 'warning', chat_id)
            return None
        if order_params['db_side'] == OrderMapper.SIDE_BUY and not sg('autocreate_buy_order'):
            l(self._service_component, f"new_binance_order side is 'BUY' and autocreate_buy_order is {sg('autocreate_buy_order')} - the new order WILL NOT be created", 'warning', chat_id)
            return None

        new_binance_order: dict = self._service_component.create_order_on_binance(**order_params)
        """
        new_binance_order: dict = {
            "symbol": "ETHUSDT",
            "orderId": 35431840769,
            "orderListId": -1,
            "clientOrderId": "x-HNA2TXFJc44b331cecb22a1dc0bd34",
            "transactTime": 1757084531110,
            "price": "4476.15000000",
            "origQty": "0.00750000",
            "executedQty": "0.00000000",
            "origQuoteOrderQty": "0.00000000",
            "cummulativeQuoteQty": "0.00000000",
            "status": "NEW",
            "timeInForce": "GTC",
            "type": "LIMIT",
            "side": "SELL",
            "workingTime": 1757084531110,
            "fills": [],
            "selfTradePreventionMode": "EXPIRE_MAKER",
        }
        """
        l(self._service_component, f"new_binance_order binance_order dict: {new_binance_order}", 'info', chat_id)


        info(f"writing new_binance_order#{new_binance_order['orderId']} to database...")
        new_db_order = self._service_component.create_or_update_db_order(new_binance_order)
        new_db_order.delta_up = db_order.delta_up
        new_db_order.delta_down = db_order.delta_down
        new_db_order.created_by_bot = 1
        if not new_db_order.save():
            l(self._service_component, f"cannot save deltas for new_db_order#{new_db_order.id}", 'error', chat_id)
        l(self._service_component, f"new_db_order.id: '{new_db_order.id}'", 'info')
        # notify about new order creation
        self._service_component.notify_order_created(
            chat_id=chat_id,
            db_order=new_db_order,
        )
        # show new order's status
        self._service_component.show_order_status(
            db_order=new_db_order,
            chat_id=chat_id,
        )
