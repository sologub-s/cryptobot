import pytest

from cryptobot.commands import ShowPriceCommand
from cryptobot.components import ServiceComponent
from cryptobot.views.view_helper import dec_to_str, format_timestamp
from tests.components.binance_client_adapter_mock import BinanceClientAdapterMock
from tests.components.telegram_http_transport_mock import TelegramMessageDataObject
from tests.mocks.binance.avg_price import get_mock_avg_price
from tests.mocks.telegram.reply_markup import get_mock_reply_markup
from tests.ports.telegram_http_transport_mock import TelegramHttpTransportComponentMockPort


@pytest.mark.integration

def test_integration_show_price(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    di = make_di
    config = make_config
    sc: ServiceComponent = di['service_component']
    tlg_transport: TelegramHttpTransportComponentMockPort = sc.telegram_component.telegram_http_transport_component
    binance_client_adapter: BinanceClientAdapterMock = sc.binance_gateway.binance_client_adapter
    mock_avg_price = get_mock_avg_price()
    binance_client_adapter.seed_avg_price(mock_avg_price)

    chat_id: int = 112233

    i = 0
    for binance_symbol in mock_avg_price.keys():
        command = (ShowPriceCommand()
                   .set_payload(binance_symbol, chat_id)
                   .set_deps(sc, di['view'])
                   )
        command.execute()

        assert tlg_transport.memory_length() == i + 1
        mem_msg: TelegramMessageDataObject = tlg_transport.get_from_memory(index=i)
        assert mem_msg is not None
        assert mem_msg.url == f'https://api.telegram.org/bot{config['telegram']['bot_token']}/sendMessage'
        assert mem_msg.data.get('chat_id', None) == chat_id
        assert mem_msg.data.get('disable_notification', None) == False
        assert mem_msg.data.get('parse_mode', None) == 'HTML'
        assert mem_msg.data.get('reply_markup', None) == get_mock_reply_markup()
        assert mem_msg.files is None

        assert f'Price info for <code>{binance_symbol}</code>\n' in mem_msg.data.get('text', '')
        assert f'Price: <b>{dec_to_str(mock_avg_price[binance_symbol]['price'])}</b>\n' in mem_msg.data.get('text', '')
        assert f'Mins: <b>{mock_avg_price[binance_symbol]['mins']}</b>\n' in mem_msg.data.get('text', '')
        assert f'Close time: <b>{format_timestamp(mock_avg_price[binance_symbol]['closeTime'] / 1000, '%Y-%m-%d %H:%M:%S')}</b>' in mem_msg.data.get('text', '')