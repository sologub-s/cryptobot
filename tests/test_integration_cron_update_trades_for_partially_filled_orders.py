from decimal import Decimal
from typing import Any

import pytest

from cryptobot.commands.cron_check_balance_from_binance import CronCheckBalanceFromBinanceCommand
from cryptobot.commands.cron_do_orders_updating_routine import CronDoOrdersUpdatingRoutineCommand
from cryptobot.commands.cron_update_trades_for_partially_filled_orders import \
    CronUpdateTradesForPartiallyFilledOrdersCommand
from cryptobot.components import ServiceComponent
from cryptobot.helpers import current_millis, dec_to_str
from cryptobot.mappers.balance_mapper import BalanceMapper
from cryptobot.mappers.order_mapper import OrderMapper
from cryptobot.models import Order, Balance, OrderTrade
from cryptobot.views.view import View
from tests.components.binance_api_adapter_mock import BinanceApiAdapterMock
from tests.components.binance_client_adapter_mock import BinanceClientAdapterMock
from tests.mocks.binance.asset_balance import get_mock_asset_balance
from tests.mocks.binance.avg_price import get_mock_avg_price
from tests.mocks.binance.orders import get_mock_orders
from tests.mocks.binance.symbol_info import get_mock_symbol_info
from tests.mocks.binance.trades import get_mock_trades
from tests.ports.telegram_http_transport_mock import TelegramHttpTransportComponentMockPort


@pytest.mark.integration

def test_integration_cron_update_trades_for_partially_filled_orders(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    di = make_di
    config = make_config
    sc: ServiceComponent = di['service_component']
    view: View = di['view']
    tlg_transport: TelegramHttpTransportComponentMockPort = sc.telegram_component.telegram_http_transport_component
    binance_client_adapter: BinanceClientAdapterMock = sc.binance_gateway.binance_client_adapter
    binance_api_adapter: BinanceApiAdapterMock = sc.binance_gateway.binance_api_adapter

    # load balances to mock
    mock_asset_balance: dict[str, dict[str, str]] = get_mock_asset_balance()
    binance_client_adapter.seed_asset_balance(mock_asset_balance)
    # load prices to db
    mock_avg_price = get_mock_avg_price()
    binance_client_adapter.seed_avg_price(mock_avg_price)
    # load symbol_info to db
    mock_symbol_info: dict[str, Any] = get_mock_symbol_info()
    binance_client_adapter.seed_symbol_info(mock_symbol_info)
    # load trades to db
    mock_trades: dict[str, list[dict[str, str|int|bool]]] = get_mock_trades()
    binance_api_adapter.seed_my_trades(my_trades=mock_trades)
    # load orders to db
    mock_orders: list[dict[str, Any]] = get_mock_orders()
    binance_client_adapter.seed_orders(mock_orders)

    chat_id: int = 112233

    # check balance (for db consistency)
    CronCheckBalanceFromBinanceCommand().set_payload(chat_id,).set_deps(sc, view).execute()

    # id=31, symbol=ETHUSDT, side=SELL, status: NEW -> PARTIALLY_FILLED
    id: int = 31
    db_order: Order = Order.get_by_id(id)
    binance_order_id: int = db_order.binance_order_id
    order_price: Decimal = db_order.order_price

    db_balance_base_before: Balance = Balance.select().where(Balance.asset == BalanceMapper.ASSET_ETH).order_by(Balance.created_at.desc()).limit(1).get()
    db_balance_quote_before: Balance = Balance.select().where(Balance.asset == BalanceMapper.ASSET_USDT).order_by(Balance.created_at.desc()).limit(1).get()

    binance_client_adapter.fake_change_order_status(binance_order_id=binance_order_id, status='PARTIALLY_FILLED')

    # do orders updating routine
    CronDoOrdersUpdatingRoutineCommand().set_payload(chat_id, ).set_deps(sc, view).execute()

    """
    0.00080000 of 0.00690000
    """
    changes: list[str] = [
        '0.00080000', # 0.00080000 of 0.00690000
        '0.00340000', # 0.00420000 of 0.00690000
        '0.00110000', # 0.00530000 of 0.00690000
        '0.00160000', # 0.00690000 of 0.00690000
    ]

    for i in range(len(changes)):
        change: str = changes[i]
        mock_trade = {
            'commission': '0.00000000',
            'commissionAsset': 'USDT',
            'id': current_millis(),
            'isBestMatch': True,
            'isBuyer': False,
            'isMaker': True,
            'orderId': binance_order_id,
            'orderListId': -1,
            'price': f"{order_price:.8f}",
            'qty': change,
            'quoteQty': f"{order_price * Decimal(change):.8f}",
            'symbol': 'ETHUSDT',
            'time': current_millis(),
        }
        # load trades to db
        mock_trades[OrderMapper.remap_symbol(db_order.symbol)].append(mock_trade)
        binance_api_adapter.seed_my_trades(my_trades=mock_trades)
        binance_client_adapter.fake_apply_mock_trade(mock_trade=mock_trade)

        db_order_trades: list[OrderTrade] = list(OrderTrade.select().where(OrderTrade.binance_order_id == binance_order_id))
        assert len(db_order_trades) == i

        # update trades
        CronUpdateTradesForPartiallyFilledOrdersCommand().set_payload(chat_id,).set_deps(sc, view).execute()

        db_order_trades: list[OrderTrade] = list(OrderTrade.select().where(OrderTrade.binance_order_id == binance_order_id))
        assert len(db_order_trades) == i + 1

    CronDoOrdersUpdatingRoutineCommand().set_payload(chat_id, ).set_deps(sc, view).execute()

    db_order: Order = Order.get_by_id(id)
    assert db_order.status == OrderMapper.STATUS_FILLED
    assert db_order.original_quantity == db_order.executed_quantity

    CronCheckBalanceFromBinanceCommand().set_payload(chat_id, ).set_deps(sc, view).execute()

    db_balance_base: Balance = Balance.select().where(Balance.asset == BalanceMapper.ASSET_ETH).order_by(Balance.created_at.desc()).limit(1).get()
    db_balance_quote: Balance = Balance.select().where(Balance.asset == BalanceMapper.ASSET_USDT).order_by(Balance.created_at.desc()).limit(1).get()
    assert Decimal(db_balance_base.locked) == Decimal(db_balance_base_before.locked) - db_order.original_quantity
    assert Decimal(db_balance_quote.free) == Decimal(db_balance_quote_before.free) + db_order.original_quantity * db_order.order_price
