from time import sleep

import pytest

from cryptobot.commands import ShowPriceCommand, CronCommand
from cryptobot.components import ServiceComponent
from cryptobot.helpers import current_millis
from cryptobot.models import CronJob
from cryptobot.views.view import View
from cryptobot.views.view_helper import dec_to_str, format_timestamp
from tests.components.binance_client_adapter_mock import BinanceClientAdapterMock
from tests.components.telegram_http_transport_mock import TelegramMessageDataObject
from tests.mocks.binance.asset_balance import get_mock_asset_balance
from tests.mocks.binance.avg_price import get_mock_avg_price
from tests.mocks.telegram.reply_markup import get_mock_reply_markup
from tests.ports.telegram_http_transport_mock import TelegramHttpTransportComponentMockPort


@pytest.mark.integration

def test_integration_cron_notify_working(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    di = make_di
    config = make_config
    sc: ServiceComponent = di['service_component']
    view: View = di['view']
    tlg_transport: TelegramHttpTransportComponentMockPort = sc.telegram_component.telegram_http_transport_component
    binance_client_adapter: BinanceClientAdapterMock = sc.binance_gateway.binance_client_adapter

    _prepare_cron_jobs_table(['notify-working'])

    chat_id: int = 112233

    (CronCommand()
    .set_payload(
        chat_id,
    )
    .set_deps(sc, view)
    .execute())

    assert tlg_transport.memory_length() == 1
    msg: TelegramMessageDataObject = tlg_transport.get_from_memory(index=0)

    assert msg is not None
    assert msg.url == f'https://api.telegram.org/bot{config['telegram']['bot_token']}/sendMessage'
    assert msg.data.get('chat_id', None) == chat_id
    assert msg.data.get('disable_notification', None) == True
    assert msg.data.get('parse_mode', None) == 'HTML'
    assert msg.data.get('reply_markup', None) == get_mock_reply_markup()
    assert msg.files is None

    assert f'Up & running...' in msg.data.get('text', '')

def test_integration_cron_check_balance_from_binance(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    di = make_di
    config = make_config
    sc: ServiceComponent = di['service_component']
    view: View = di['view']
    tlg_transport: TelegramHttpTransportComponentMockPort = sc.telegram_component.telegram_http_transport_component
    binance_client_adapter: BinanceClientAdapterMock = sc.binance_gateway.binance_client_adapter

    mock_asset_balance: dict[str, dict[str, str]] = get_mock_asset_balance()
    binance_client_adapter.seed_asset_balance(mock_asset_balance)

    _prepare_cron_jobs_table(['check-balance-from-binance'])

    chat_id: int = 112233

    (CronCommand()
    .set_payload(
        chat_id,
    )
    .set_deps(sc, view)
    .execute())

    """
    assert tlg_transport.memory_length() == 1
    msg: TelegramMessageDataObject = tlg_transport.get_from_memory(index=0)

    assert msg is not None
    assert msg.url == f'https://api.telegram.org/bot{config['telegram']['bot_token']}/sendMessage'
    assert msg.data.get('chat_id', None) == chat_id
    assert msg.data.get('disable_notification', None) == False
    assert msg.data.get('parse_mode', None) == 'HTML'
    assert msg.data.get('reply_markup', None) == get_mock_reply_markup()
    assert msg.files is None

    assert f'Up & running...' in msg.data.get('text', '')
    """


def _prepare_cron_jobs_table(execute_cron_jobs=None) -> None:
    if execute_cron_jobs is None:
        execute_cron_jobs = []
    cron_jobs: list[CronJob] = list(
        CronJob
        .select()
    )
    for cron_job in cron_jobs:
        cron_job.last_executed_at = current_millis() + (1000 * 3600)
        if cron_job.name in execute_cron_jobs:
            cron_job.last_executed_at = 0
        cron_job.save()