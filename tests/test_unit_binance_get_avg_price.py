import pytest

from cryptobot.components import ServiceComponent
from tests.ports.telegram_http_transport_mock_port import TelegramHttpTransportComponentMockPort

@pytest.mark.unit
def test_unit_binance_get_avg_price(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    config = make_config
    di = make_di
    sc: ServiceComponent = di['service_component']
    binance_client = sc.binance_component.binance_client

    symbol: str = 'ETHUSDT'
    mock_price: dict = {
        'mins': 5,
        'price': '4423.94003084',
        'closeTime': 1755388879049,
    }
    #binance_client.mock_price = mock_price
    #price = sc.get_price_for_binance_symbol(symbol)
    #

    #apply_seed_fixture(seed_name='', files='clear.sql')