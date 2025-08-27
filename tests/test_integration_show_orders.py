import pytest

from cryptobot.commands import ShowOrdersCommand
from cryptobot.components import ServiceComponent
from cryptobot.mappers.order_mapper import OrderMapper
from cryptobot.models import Order
from tests.components.telegram_http_transport_mock import TelegramMessageDataObject
from tests.mocks.telegram.reply_markup import get_mock_reply_markup
from tests.ports.telegram_http_transport_mock import TelegramHttpTransportComponentMockPort


@pytest.mark.integration

def test_integration_show_orders(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    di = make_di
    config = make_config
    sc: ServiceComponent = di['service_component']
    tlg_transport: TelegramHttpTransportComponentMockPort = sc.telegram_component.telegram_http_transport_component

    chat_id: int = 112233

    command = (ShowOrdersCommand()
               .set_payload(chat_id)
               .set_deps(sc, di['view'])
               )
    command.execute()

    assert tlg_transport.memory_length() == 1

    statuses: list[int] = [
        OrderMapper.STATUS_UNKNOWN,
        OrderMapper.STATUS_PENDING_NEW,
        OrderMapper.STATUS_NEW,
        OrderMapper.STATUS_PARTIALLY_FILLED,
        OrderMapper.STATUS_PENDING_CANCEL,
    ]
    db_open_orders_count = Order.select().where(Order.status.in_(statuses)).count()

    mem_msg: TelegramMessageDataObject = tlg_transport.get_from_memory(index=0)

    assert mem_msg is not None

    assert mem_msg.url == f'https://api.telegram.org/bot{config['telegram']['bot_token']}/sendMessage'
    assert mem_msg.data.get('chat_id', None) == chat_id

    assert mem_msg.data.get('text', '').lstrip('\n ').startswith(f'<b>The list of orders (total: {db_open_orders_count}):</b>')

    msg_orders = mem_msg.data.get('text', '').split('---')
    assert len(msg_orders) == db_open_orders_count

    asserts: list[list[str]] = [
        [
            '<code>34089919693</code>\n',
            '<b>2025-08-14 03:00:08</b>\n',
            '<b>Type: LIMIT</b>\n',
            'Side: SELL\n',
            'Symbol: ETHUSDT\n',
            'Price: 4987.50\n',
            'Original quantity: 0.00440000\n',
            'Executed quantity: 0.00000000\n',
            'Cummulative quote quantity: 0.00000000\n',
            'Status: NEW\n',
        ],
        [
            '<code>34217627731</code>\n',
            '<b>2025-08-15 18:50:09</b>\n',
            '<b>Type: LIMIT</b>\n',
            'Side: SELL\n',
            'Symbol: ETHUSDT\n',
            'Price: 4620.00\n',
            'Original quantity: 0.00690000\n',
            'Executed quantity: 0.00000000\n',
            'Cummulative quote quantity: 0.00000000\n',
            'Status: NEW\n',
        ],
        [
            '<code>34285044672</code>\n',
            '<b>2025-08-17 06:51:34</b>\n',
            '<b>Type: LIMIT</b>\n',
            'Side: BUY\n',
            'Symbol: ETHUSDT\n',
            'Price: 4200.00\n',
            'Original quantity: 0.00720000\n',
            'Executed quantity: 0.00000000\n',
            'Cummulative quote quantity: 0.00000000\n',
            'Status: NEW\n',
        ],
    ]

    assert mem_msg.url == f'https://api.telegram.org/bot{config['telegram']['bot_token']}/sendMessage'
    assert mem_msg.data.get('chat_id', None) == chat_id
    assert mem_msg.data.get('disable_notification', None) == False
    assert mem_msg.data.get('parse_mode', None) == 'HTML'
    assert mem_msg.data.get('reply_markup', None) == get_mock_reply_markup()
    assert mem_msg.files is None

    for i in range(len(msg_orders)):
        for the_assert_substr in asserts[i]:
            assert the_assert_substr in msg_orders[i]