import pytest

from cryptobot.components import ServiceComponent
from tests.ports.telegram_http_transport_mock_port import TelegramHttpTransportComponentMockPort

@pytest.mark.unit
def test_unit_telegram_send_message(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    config = make_config
    di = make_di

    chat_id: int = config['telegram']['chat_id']

    sc: ServiceComponent = di['service_component']

    message = 'hello world from test'

    sc.send_telegram_message(chat_id=chat_id, message=message)

    tlg_transport: TelegramHttpTransportComponentMockPort = sc.telegram_component.telegram_http_transport_component

    #for i in range(tlg_transport.memory_length()):
    #    print(tlg_transport.get_from_memory(i))

    assert tlg_transport.memory_length() == 1
    assert tlg_transport.get_from_memory(0).data.get('chat_id') == str(chat_id)
    assert tlg_transport.get_from_memory(0).data.get('text') == message

    #apply_seed_fixture(seed_name='', files='clear.sql')