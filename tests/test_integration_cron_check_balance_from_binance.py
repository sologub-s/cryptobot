from decimal import Decimal

import pytest

from cryptobot.commands import CronCommand
from cryptobot.components import ServiceComponent
from cryptobot.helpers import current_millis
from cryptobot.mappers.balance_mapper import BalanceMapper
from cryptobot.models import CronJob, Balance
from cryptobot.views.view import View
from cryptobot.views.view_helper import dec_to_str
from tests.components.binance_client_adapter_mock import BinanceClientAdapterMock
from tests.mocks.binance.asset_balance import get_mock_asset_balance
from tests.ports.telegram_http_transport_mock import TelegramHttpTransportComponentMockPort


@pytest.mark.integration

def test_integration_cron_check_balance_from_binance(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    di = make_di
    config = make_config
    sc: ServiceComponent = di['service_component']
    view: View = di['view']
    tlg_transport: TelegramHttpTransportComponentMockPort = sc.telegram_component.telegram_http_transport_component
    binance_client_adapter: BinanceClientAdapterMock = sc.binance_gateway.binance_client_adapter

    # load balances to mock
    mock_asset_balance: dict[str, dict[str, str]] = get_mock_asset_balance()
    binance_client_adapter.seed_asset_balance(mock_asset_balance)

    chat_id: int = 112233

    # count balances records
    balances_count_0: dict[str, int] = {}
    for asset_binance in BalanceMapper.asset_mapping.keys():
        balances_count_0[asset_binance] = Balance.select().where(Balance.asset == BalanceMapper.map_asset(asset_binance)).count()

    # check balance
    _prepare_cron_jobs_table(['check-balance-from-binance'])
    (CronCommand()
    .set_payload(
        chat_id,
    )
    .set_deps(sc, view)
    .execute())

    # count balances records (must be )
    balances_count_1: dict[str, int] = {}
    for asset_binance in BalanceMapper.asset_mapping.keys():
        balances_count_1[asset_binance] = Balance.select().where(Balance.asset == BalanceMapper.map_asset(asset_binance)).count()
        assert balances_count_1[asset_binance] - balances_count_0[asset_binance] == 1

    # check balance again
    _prepare_cron_jobs_table(['check-balance-from-binance'])
    (CronCommand()
    .set_payload(
        chat_id,
    )
    .set_deps(sc, view)
    .execute())

    # calculate count again, must be the same
    balances_count_2: dict[str, int] = {}
    for asset_binance in BalanceMapper.asset_mapping.keys():
        balances_count_2[asset_binance] = Balance.select().where(Balance.asset == BalanceMapper.map_asset(asset_binance)).count()
        assert balances_count_2[asset_binance] - balances_count_1[asset_binance] == 0

    # BALANCES CHANGE
    for key in mock_asset_balance.keys():
        mock_asset_balance[key]['free'] = dec_to_str(Decimal(mock_asset_balance[key]['free']) + Decimal('0.3'))
        mock_asset_balance[key]['locked'] = dec_to_str(Decimal(mock_asset_balance[key]['locked']) + Decimal('0.8'))
    binance_client_adapter.seed_asset_balance(mock_asset_balance)

    # check balance again
    _prepare_cron_jobs_table(['check-balance-from-binance'])
    (CronCommand()
    .set_payload(
        chat_id,
    )
    .set_deps(sc, view)
    .execute())

    # calculate count again, must be 1 more per each asset
    balances_count_3: dict[str, int] = {}
    for asset_binance in BalanceMapper.asset_mapping.keys():
        balances_count_3[asset_binance] = Balance.select().where(Balance.asset == BalanceMapper.map_asset(asset_binance)).count()
        assert balances_count_3[asset_binance] - balances_count_2[asset_binance] == 1

    # check balance again
    _prepare_cron_jobs_table(['check-balance-from-binance'])
    (CronCommand()
    .set_payload(
        chat_id,
    )
    .set_deps(sc, view)
    .execute())

    # calculate count again, must be the same
    balances_count_4: dict[str, int] = {}
    for asset_binance in BalanceMapper.asset_mapping.keys():
        balances_count_4[asset_binance] = Balance.select().where(Balance.asset == BalanceMapper.map_asset(asset_binance)).count()
        assert balances_count_4[asset_binance] - balances_count_3[asset_binance] == 0


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