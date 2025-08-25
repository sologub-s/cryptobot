import _io
from typing import Any

import pytest

from cryptobot.commands import ShowPriceChartCommand
from cryptobot.components import ServiceComponent
from tests.components.binance_client_adapter_mock import BinanceClientAdapterMock
from tests.components.telegram_http_transport_mock import TelegramMessageDataObject
from tests.mocks.binance.avg_price import get_mock_avg_price
from tests.mocks.binance.historical_klines import get_mock_historical_klines
from tests.mocks.binance.orders import get_mock_orders
from tests.mocks.telegram.reply_markup import get_mock_reply_markup
from tests.ports.telegram_http_transport_mock import TelegramHttpTransportComponentMockPort


@pytest.mark.integration

def test_integration_show_price_chart(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    di = make_di
    config = make_config
    sc: ServiceComponent = di['service_component']
    tlg_transport: TelegramHttpTransportComponentMockPort = sc.telegram_component.telegram_http_transport_component
    binance_client_adapter: BinanceClientAdapterMock = sc.binance_gateway.binance_client_adapter

    mock_historical_klines: dict[str, list[list[Any]]] = get_mock_historical_klines()
    binance_client_adapter.seed_historical_klines(mock_historical_klines)
    binance_client_adapter.seed_avg_price(get_mock_avg_price())
    binance_client_adapter.seed_orders(get_mock_orders())

    chat_id: int = 112233
    binance_symbols = ['ETHUSDT',]
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

    for binance_symbol in binance_symbols:
        for key in keys:
            tlg_transport.clear()
            key_splitted: list[str] = key.split(':')
            period: str = key_splitted[0]
            interval: str = key_splitted[1]

            command = (ShowPriceChartCommand()
                       .set_payload(binance_symbol, period, interval, chat_id)
                       .set_deps(sc, di['view'], di['plt'])
                       )
            command.execute()

            assert tlg_transport.memory_length() == 1
            msg: TelegramMessageDataObject = tlg_transport.get_from_memory(index=0)

            assert msg is not None
            assert msg.url == f'https://api.telegram.org/bot{config['telegram']['bot_token']}/sendPhoto'
            assert msg.data.get('chat_id', None) == chat_id
            assert msg.data.get('caption', '') == f'{binance_symbol} - Price History (since {period}, interval {interval})'
            assert msg.data.get('reply_markup', None) == get_mock_reply_markup()
            assert msg.files is not None
            assert msg.files.get('photo', None) is not None
            assert len(msg.files['photo']) == 3
            assert msg.files['photo'][0] == f'{binance_symbol.lower()}-price-history-since-{period.replace('_', '-').lower()}-interval-{interval.lower()}.png'
            assert type(msg.files['photo'][1]) == _io.BytesIO
            assert msg.files['photo'][2] == 'image/png'