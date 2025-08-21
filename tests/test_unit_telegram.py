import pytest

from cryptobot.components import ServiceComponent
from cryptobot.helpers import slugify
from tests.ports.telegram_http_transport_mock import TelegramHttpTransportComponentMockPort

@pytest.mark.unit

def test_unit_telegram_send_message(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    config = make_config
    di = make_di
    chat_id: int = config['telegram']['chat_id']
    sc: ServiceComponent = di['service_component']
    tlg_transport: TelegramHttpTransportComponentMockPort = sc.telegram_component.telegram_http_transport_component

    message = 'hello world from test'
    sc.send_telegram_message(chat_id=chat_id, message=message)

    # message has been sent
    assert tlg_transport.memory_length() == 1
    # message has been sent to the desired chat_id
    assert tlg_transport.get_from_memory(0).data.get('chat_id') == str(chat_id)
    # message is the same that has been sent
    assert tlg_transport.get_from_memory(0).data.get('text') == message



@pytest.mark.unit
def test_unit_telegram_send_photo(db_session_conn, apply_seed_fixture, make_config, make_di):
    apply_seed_fixture(seed_name='common')
    config = make_config
    di = make_di
    chat_id: int = config['telegram']['chat_id']
    sc: ServiceComponent = di['service_component']
    tlg_transport: TelegramHttpTransportComponentMockPort = sc.telegram_component.telegram_http_transport_component

    plt = di['plt']

    plt.figure(figsize=(10, 5))
    plt.plot([1,101], [-3, 103], [5, 105], [-7, 107], [9, 109], [-11, 111], color='red', label="test", linewidth=5)
    plt.grid(True)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    buf_value: bytes = buf.getvalue()

    caption: str = 'test image'
    sc.send_telegram_photo(chat_id=chat_id, photo_buf=buf, photo_name=caption,)

    # message has been sent
    assert tlg_transport.memory_length() == 1
    # message has been sent to the desired chat_id
    assert tlg_transport.get_from_memory(0).data.get('chat_id') == str(chat_id)
    # message is the same that has been sent
    assert tlg_transport.get_from_memory(0).data.get('caption') == caption
    # assert image name is as expected
    assert tlg_transport.get_from_memory(0).files.get('photo')[0] == slugify(caption) + ".png"
    # assert image is the same that has been sent
    assert tlg_transport.get_from_memory(0).files.get('photo')[1].getvalue() == buf_value
    # assert type of the image is png
    assert tlg_transport.get_from_memory(0).files.get('photo')[2] == 'image/png'