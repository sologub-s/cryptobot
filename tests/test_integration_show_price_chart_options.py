import json

import pytest

from cryptobot.commands import ShowPriceCommand, ShowPriceChartOptionsCommand
from cryptobot.components import ServiceComponent
from cryptobot.views.view_helper import dec_to_str, format_timestamp
from tests.components.binance_client_adapter_mock import BinanceClientAdapterMock
from tests.components.telegram_http_transport_mock import TelegramMessageDataObject
from tests.mocks.binance.avg_price import get_mock_avg_price
from tests.mocks.telegram.reply_markup import get_mock_reply_markup
from tests.ports.telegram_http_transport_mock import TelegramHttpTransportComponentMockPort


@pytest.mark.integration

def test_integration_show_price_chart_options(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    di = make_di
    config = make_config
    sc: ServiceComponent = di['service_component']
    tlg_transport: TelegramHttpTransportComponentMockPort = sc.telegram_component.telegram_http_transport_component
    binance_client_adapter: BinanceClientAdapterMock = sc.binance_gateway.binance_client_adapter

    chat_id: int = 112233
    binance_symbols = ['ETHUSDT',]

    for binance_symbol in binance_symbols:
        tlg_transport.clear()

        command = (ShowPriceChartOptionsCommand()
                   .set_payload(binance_symbol, chat_id)
                   .set_deps(sc, di['view'])
                   )
        command.execute()

        assert tlg_transport.memory_length() == 2

        msg_options: TelegramMessageDataObject = tlg_transport.get_from_memory(index=0)
        msg_keyboard: TelegramMessageDataObject = tlg_transport.get_from_memory(index=1)

        keys = [
            f"show_price_chart:{binance_symbol}:1_year_ago_UTC:1M",
            f"show_price_chart:{binance_symbol}:6_months_ago_UTC:1M",
            f"show_price_chart:{binance_symbol}:3_months_ago_UTC:1w",
            f"show_price_chart:{binance_symbol}:1_months_ago_UTC:1d",
            f"show_price_chart:{binance_symbol}:1_week_ago_UTC:1d",
            f"show_price_chart:{binance_symbol}:3_days_ago_UTC:1h",
            f"show_price_chart:{binance_symbol}:1_day_ago_UTC:1h",
            f"show_price_chart:{binance_symbol}:3_hours_ago_UTC:1m",
            f"show_price_chart:{binance_symbol}:1_hour_ago_UTC:1m",
        ]

        for msg in [msg_options, msg_keyboard]:
            assert msg is not None
            assert msg.url == f'https://api.telegram.org/bot{config['telegram']['bot_token']}/sendMessage'
            assert msg.data.get('chat_id', None) == chat_id
            assert msg.data.get('disable_notification', None) == False
            assert msg.data.get('parse_mode', None) == 'HTML'
            assert msg.data.get('files', None) is None
            assert msg.files is None

        assert msg_options.data.get('text', None) is not None
        assert f'Choose price options for <code>{binance_symbol}</code>:' in msg_options.data.get('text', '')
        assert msg_options.data.get('reply_markup', None) is not None
        reply_markup = json.loads(msg_options.data.get('reply_markup', '{}'))
        assert reply_markup.get('resize_keyboard', None) is True
        assert reply_markup.get('one_time_keyboard', None) is False
        assert reply_markup.get('inline_keyboard', None) is not None
        assert len(reply_markup.get('inline_keyboard', [])) == len(keys)
        for keyline in reply_markup.get('inline_keyboard', []):
            assert len(keyline) == 1
            assert keyline[0].get('text', None) == keyline[0].get('callback_data', None)
            assert keyline[0].get('text', None) in keys

        assert msg_keyboard.data.get('text', None) is not None
        assert f'Or choose another command from the menu in the bottom.' in msg_keyboard.data.get('text', '')
        assert msg_keyboard.data.get('reply_markup', None) == get_mock_reply_markup()



    """
    
    mem_msg: TelegramMessageDataObject = tlg_transport.get_from_memory(index=i)
    assert mem_msg is not None
    assert mem_msg.url == f'https://api.telegram.org/bot{config['telegram']['bot_token']}/sendMessage'
    assert mem_msg.data.get('chat_id', None) == chat_id
    assert mem_msg.data.get('disable_notification', None) == False
    assert mem_msg.data.get('parse_mode', None) == 'HTML'
    assert mem_msg.data.get('reply_markup', None) == get_mock_reply_markup()
    assert mem_msg.files is None
    """
