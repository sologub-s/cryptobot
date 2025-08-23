import pytest

from cryptobot.commands import ShowOrderStatusCommand
from cryptobot.components import ServiceComponent
from tests.components.telegram_http_transport_mock import TelegramMessageDataObject
from tests.mocks.telegram.reply_markup import get_mock_reply_markup
from tests.ports.telegram_http_transport_mock import TelegramHttpTransportComponentMockPort


@pytest.mark.integration

def test_integration_show_order_status(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    di = make_di
    config = make_config
    sc: ServiceComponent = di['service_component']
    tlg_transport: TelegramHttpTransportComponentMockPort = sc.telegram_component.telegram_http_transport_component

    binance_order_id: int = 33375951540
    chat_id: int = 112233
    command = (ShowOrderStatusCommand()
               .set_payload(
                    binance_order_id=binance_order_id,
                    chat_id=chat_id,
                )
               .set_deps(sc, di['view'])
           )
    command.execute()

    assert tlg_transport.memory_length() == 1

    mem_msg: TelegramMessageDataObject = tlg_transport.get_from_memory(index=0)

    assert mem_msg is not None

    assert mem_msg.url == f'https://api.telegram.org/bot{config['telegram']['bot_token']}/sendMessage'
    assert mem_msg.data.get('chat_id', None) == chat_id
    assert '<code>33375951540</code>\n' in mem_msg.data.get('text', '')
    assert '<b>2025-08-01 11:05:56</b>\n' in mem_msg.data.get('text', '')
    assert '<b>Type: LIMIT</b>\n' in mem_msg.data.get('text', '')
    assert 'Side: BUY\n' in mem_msg.data.get('text', '')
    assert 'Symbol: ETHUSDT\n' in mem_msg.data.get('text', '')
    assert 'Price: 3600.00\n' in mem_msg.data.get('text', '')
    assert 'Original quantity: 0.00810000\n' in mem_msg.data.get('text', '')
    assert 'Executed quantity: 0.00810000\n' in mem_msg.data.get('text', '')
    assert 'Cummulative quote quantity: 29.16000000\n' in mem_msg.data.get('text', '')
    assert 'Status: FILLED' in mem_msg.data.get('text', '')
    assert mem_msg.data.get('disable_notification', None) == False
    assert mem_msg.data.get('parse_mode', None) == 'HTML'
    assert mem_msg.data.get('reply_markup', None) == get_mock_reply_markup()
    assert mem_msg.files is None