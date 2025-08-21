from decimal import Decimal
from typing import Any

import pytest

from cryptobot.components import ServiceComponent
from mocks.binance.orders import get_mock_orders
from mocks.binance.avg_price import get_mock_avg_price
from mocks.binance.trades import get_mock_trades
from tests.components.binance_api_adapter_mock import BinanceApiAdapterMock
from tests.components.binance_client_adapter_mock import BinanceClientAdapterMock
from tests.mocks.binance.asset_balance import get_mock_asset_balance
from tests.mocks.binance.asset_transfers import get_mock_asset_transfers
from tests.mocks.binance.historical_klines import get_mock_historical_klines


@pytest.mark.unit

def test_unit_binance_get_open_orders(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    di = make_di
    sc: ServiceComponent = di['service_component']
    binance_client_adapter: BinanceClientAdapterMock = sc.binance_gateway.binance_client_adapter

    mock_orders: list[dict[str, Any]] = get_mock_orders()
    mock_orders_open: list[dict[str, Any]] = []
    for mock_order in mock_orders:
        if mock_order['status'] in ['NEW', 'PARTIALLY_FILLED', 'PENDING',]:
            mock_orders_open.append(mock_order)

    binance_client_adapter.seed_orders(mock_orders)

    open_orders = sc.get_open_orders()
    assert len(open_orders) == len(mock_orders_open)

    for open_order in open_orders:
        mock_open_order = _find_open_order(open_orders=open_orders, orderId=open_order['orderId'])
        assert mock_open_order is not None
        for key in mock_open_order.keys():
            assert open_order.get(key, None) is not None
            assert open_order[key] == mock_open_order[key]

def _find_open_order(open_orders: list[dict[str, Any]], orderId: int) -> dict[str, Any] | None:
    for order in open_orders:
        if order['orderId'] == orderId:
            return order
    return None

def test_unit_binance_get_avg_price(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    di = make_di
    sc: ServiceComponent = di['service_component']
    binance_client_adapter: BinanceClientAdapterMock = sc.binance_gateway.binance_client_adapter

    mock_avg_price: dict[str, Any] = get_mock_avg_price()
    binance_client_adapter.seed_avg_price(mock_avg_price)

    symbols: list[str] = ['ETHUSDT']

    for symbol in symbols:
        price = sc.get_price_for_binance_symbol(symbol)
        assert price is not None
        assert price['mins'] == mock_avg_price[symbol]['mins']
        assert price['price'] == mock_avg_price[symbol]['price']
        assert price['closeTime'] == mock_avg_price[symbol]['closeTime']

    price_for_unexisted_symbol = sc.get_price_for_binance_symbol('JHDFHSDHHDJKS')
    assert price_for_unexisted_symbol == {}

def test_unit_binance_get_historical_klines(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    di = make_di
    sc: ServiceComponent = di['service_component']
    binance_client_adapter: BinanceClientAdapterMock = sc.binance_gateway.binance_client_adapter

    mock_historical_klines: dict[str, list[list[Any]]] = get_mock_historical_klines()
    binance_client_adapter.seed_historical_klines(mock_historical_klines)

    symbols: list[str] = ['ETHUSDT']

    keys = [
        "1_year_ago_UTC:1M",
        "6_months_ago_UTC:1M",
        "3_months_ago_UTC:1w",
        "1_months_ago_UTC:1d",
        "1_week_ago_UTC:1d",
        "3_days_ago_UTC:1h",
        "1_day_ago_UTC:1h",
        "3_hours_ago_UTC:1m",
        "1_hour_ago_UTC:1m",
    ]

    for symbol in symbols:
        for key in keys:
            key_splitted: list[str] = key.split(':')
            period: str = key_splitted[0]
            interval: str = key_splitted[1]
            klines = sc.get_historical_klines(symbol, period, interval)
            full_key = f'{symbol}:{period}:{interval}'
            assert mock_historical_klines.get(full_key, None) is not None
            assert len(mock_historical_klines[full_key]) == len(klines)
            if len(mock_historical_klines[full_key]) == len(klines):
                for i in range(len(klines)):
                    mock_kline = mock_historical_klines[full_key][i]
                    kline = klines[i]
                    # open_time
                    assert kline.get('open_time', None) is not None
                    assert kline.get('open_time', None) * 1000 == mock_kline[0]
                    # open_price
                    assert kline.get('open_price', None) is not None
                    assert Decimal(str(kline.get('open_price'))) == Decimal(mock_kline[1])
                    # high_price
                    assert kline.get('high_price', None) is not None
                    assert Decimal(str(kline.get('high_price'))) == Decimal(mock_kline[2])
                    # low_price
                    assert kline.get('low_price', None) is not None
                    assert Decimal(str(kline.get('low_price'))) == Decimal(mock_kline[3])
                    # close_price
                    assert kline.get('close_price', None) is not None
                    assert Decimal(str(kline.get('close_price'))) == Decimal(mock_kline[4])
                    # average_price
                    assert kline.get('average_price', None) is not None
                    average_price = round((Decimal(mock_kline[2]) + Decimal(mock_kline[3])) / 2, 2)
                    assert Decimal(str(kline.get('average_price'))) == average_price
                    # volume
                    assert kline.get('volume', None) is not None
                    assert Decimal(str(kline.get('volume'))) == Decimal(mock_kline[5])
                    # close_time
                    assert kline.get('close_time', None) is not None
                    if i + 1 < len(mock_historical_klines[full_key]):
                        assert kline.get('close_time', None) * 1000 == mock_historical_klines[full_key][i+1][0]
                    else:
                        assert kline.get('close_time', 0) > kline.get('open_time', 0)

def test_unit_binance_get_asset_balance(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    di = make_di
    sc: ServiceComponent = di['service_component']
    binance_client_adapter: BinanceClientAdapterMock = sc.binance_gateway.binance_client_adapter

    mock_asset_balance: dict[str, dict[str, str]] = get_mock_asset_balance()
    binance_client_adapter.seed_asset_balance(mock_asset_balance)

    for asset in mock_asset_balance.keys():
        asset_balance = sc.get_asset_balance(asset)
        assert asset_balance.get('asset', None) == asset
        assert asset_balance.get('free', None) == mock_asset_balance[asset]['free']
        assert asset_balance.get('locked', None) == mock_asset_balance[asset]['locked']

    assert sc.get_asset_balance('unexisted_asset_sasadad') is None

def test_unit_binance_get_all_trades(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    di = make_di
    sc: ServiceComponent = di['service_component']
    binance_api_adapter: BinanceApiAdapterMock = sc.binance_gateway.binance_api_adapter

    mock_trades: dict[str, list[dict[str, str|int|bool]]] = get_mock_trades()

    binance_api_adapter.seed_my_trades(my_trades=mock_trades)

    symbols: list[str] = ['ETHUSDT',]

    for symbol in symbols:
        my_trades = sc.get_all_trades(binance_symbol=symbol)
        assert len(mock_trades[symbol]) == len(my_trades)
        for i in range(len(mock_trades[symbol])):
            for key in mock_trades[symbol][i].keys():
                assert mock_trades[symbol][i][key] == my_trades[i].get(key, None)

def test_unit_binance_get_asset_transfer(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    di = make_di
    sc: ServiceComponent = di['service_component']
    binance_api_adapter: BinanceApiAdapterMock = sc.binance_gateway.binance_api_adapter

    mock_asset_transfers: dict[str, dict[str, int]] = get_mock_asset_transfers()

    binance_api_adapter.seed_asset_transfers(asset_transfers=mock_asset_transfers)

    types: list[str] = [
        'MAIN_UMFUTURE',
        'UMFUTURE_MAIN',
        'MAIN_CMFUTURE',
        'CMFUTURE_MAIN',
        'MAIN_MARGIN',
        'MARGIN_MAIN',
        'MAIN_MINING',
        'MINING_MAIN',
        'MAIN_FUNDING',
        'FUNDING_MAIN',
    ]

    for type in types:
        asset_transfer = sc.get_asset_transfer(type=type)
        assert asset_transfer.get('total', None) is not None
        assert asset_transfer.get('total', None) == mock_asset_transfers[type]['total']