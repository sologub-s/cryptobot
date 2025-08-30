from decimal import Decimal

from cryptobot.components import ServiceComponent
from cryptobot.helpers import current_millis
from cryptobot.models import CronJob
from tests.ports.telegram_http_transport_mock import TelegramHttpTransportComponentMockPort


def _get_new_safe_price(sc: ServiceComponent, symbol: str, new_side: str, old_price: Decimal, percent: Decimal) -> Decimal:
    if new_side == 'BUY':
        new_price: str = f"{old_price - old_price / 100 * percent:.2f}"
    else:
        new_price: str = f"{old_price + old_price / 100 * percent:.2f}"

    symbol_info = sc.binance_gateway.get_symbol_info(symbol)

    tick_size = None
    for f in symbol_info['filters']:
        if f["filterType"] == "PRICE_FILTER":
            tick_size = Decimal(f["tickSize"])

    new_price = (Decimal(new_price) // tick_size) * tick_size
    return new_price

def _print_tlg_messages(tlg_transport: TelegramHttpTransportComponentMockPort):
    print('====================================')
    for i in range(tlg_transport.memory_length()):
        print(tlg_transport.get_from_memory(i))
        print('--------------------------------')
    tlg_transport.clear()
    print('====================================')

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