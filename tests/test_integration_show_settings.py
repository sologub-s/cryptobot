import pytest

from cryptobot.commands import ShowSettingsCommand
from cryptobot.components import ServiceComponent
from cryptobot.models import Setting
from cryptobot.views.view_helper import show_type
from tests.components.binance_client_adapter_mock import BinanceClientAdapterMock
from tests.components.telegram_http_transport_mock import TelegramMessageDataObject
from tests.mocks.telegram.reply_markup import get_mock_reply_markup
from tests.ports.telegram_http_transport_mock import TelegramHttpTransportComponentMockPort


@pytest.mark.integration

def test_integration_show_settings(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    di = make_di
    config = make_config
    sc: ServiceComponent = di['service_component']
    tlg_transport: TelegramHttpTransportComponentMockPort = sc.telegram_component.telegram_http_transport_component
    binance_client_adapter: BinanceClientAdapterMock = sc.binance_gateway.binance_client_adapter

    chat_id: int = 112233

    db_settings: list[Setting] = Setting.select()

    settings: dict[str, dict[str, str]] = {}

    for db_setting in db_settings:
        settings[db_setting.the_key] = {
            'type': db_setting.the_type,
            'value': db_setting.the_value,
        }

    print(settings)

    command = (ShowSettingsCommand()
               .set_payload(chat_id)
               .set_deps(service_component=sc, view=di['view'])
               )
    command.execute()

    assert tlg_transport.memory_length() == 1
    msg: TelegramMessageDataObject = tlg_transport.get_from_memory(index=0)
    assert msg is not None
    assert msg.url == f'https://api.telegram.org/bot{config['telegram']['bot_token']}/sendMessage'
    assert msg.data.get('chat_id', None) == chat_id
    assert msg.data.get('disable_notification', None) == False
    assert msg.data.get('parse_mode', None) == 'HTML'
    assert msg.data.get('reply_markup', None) == get_mock_reply_markup()
    assert msg.files is None

    assert f'<b>The list of settings (total: {len(settings)}):</b>\n' in msg.data.get('text', '')
    for the_key in settings.keys():
        typed_value = di['settings_component']._map_from_db(settings[the_key]['type'], settings[the_key]['value'])
        assert f'<b>{the_key}: ({show_type(typed_value)}) {typed_value}</b>\n' in msg.data.get('text', '')