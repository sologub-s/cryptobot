import json
from logging import warn

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

    statuses: list[int] = [
        OrderMapper.STATUS_UNKNOWN,
        OrderMapper.STATUS_PENDING_NEW,
        OrderMapper.STATUS_NEW,
        OrderMapper.STATUS_PARTIALLY_FILLED,
        OrderMapper.STATUS_PENDING_CANCEL,
    ]
    db_open_orders_count = Order.select().where(Order.status.in_(statuses)).count()

    assert tlg_transport.memory_length() == db_open_orders_count + 1

    asserts_applied: int = 0
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
            'Delta up: 3.00%',
            'Delta down: 3.00%',
        ],
        [
            '<code>34632411326</code>\n',
            '<b>2025-08-22 17:02:08</b>\n',
            '<b>Type: LIMIT</b>\n',
            'Side: BUY\n',
            'Symbol: ETHUSDT\n',
            'Price: 4189.50\n',
            'Original quantity: 0.00760000\n',
            'Executed quantity: 0.00000000\n',
            'Cummulative quote quantity: 0.00000000\n',
            'Status: NEW\n',
        ],
        [
            '<code>35055318220</code>\n',
            '<b>2025-08-28 22:56:08</b>\n',
            '<b>Type: LIMIT</b>\n',
            'Side: SELL\n',
            'Symbol: ETHUSDT\n',
            'Price: 4672.50\n',
            'Original quantity: 0.00460000\n',
            'Executed quantity: 0.00000000\n',
            'Cummulative quote quantity: 0.00000000\n',
            'Status: NEW\n',
        ],
    ]

    for i in range(db_open_orders_count + 1):

        mem_msg: TelegramMessageDataObject = tlg_transport.get_from_memory(index=i)

        assert mem_msg is not None

        assert mem_msg.url == f'https://api.telegram.org/bot{config['telegram']['bot_token']}/sendMessage'
        assert mem_msg.data.get('chat_id', None) == chat_id
        assert mem_msg.data.get('disable_notification', None) == False
        assert mem_msg.data.get('parse_mode', None) == 'HTML'
        assert mem_msg.files is None

        if i == 0:
            assert mem_msg.data.get('text', '').lstrip('\n ').startswith(f'<b>The list of orders (total: {db_open_orders_count}):</b>')

        msg_text = mem_msg.data.get('text', '')

        for the_assert in asserts:
            if the_assert[0] in msg_text:
                asserts_applied += 1
                deltas_present: bool = False
                for the_assert_substr in the_assert:
                    assert the_assert_substr in msg_text
                    if 'Delta' in the_assert_substr:
                        deltas_present = True
                reply_markup: dict = json.loads(mem_msg.data.get('reply_markup', ''))
                assert reply_markup.get('keyboard', None) == None
                assert reply_markup.get('inline_keyboard', None) is not None
                assert mem_msg.data.get('reply_markup', None) != get_mock_reply_markup()

                if not deltas_present:
                    assert 'Delta up:' not in msg_text
                    assert 'Delta down:' not in msg_text

