import argparse
from logging import info, warning, error

from cryptobot.commands import ShowOrdersCommand, WebserverCommand, HookCommand, ShowSettingsCommand
from cryptobot.commands import ShowOrderStatusCommand, ShowPriceCommand
from cryptobot.commands import ShowPriceChartOptionsCommand, ShowPriceChartCommand
from cryptobot.commands import CronCommand
from cryptobot.commands import MiscCommand
from cryptobot.commands.cron_check_balance_from_binance import CronCheckBalanceFromBinanceCommand
from cryptobot.commands.cron_do_orders_updating_routine import CronDoOrdersUpdatingRoutineCommand
from cryptobot.commands.cron_notify_working import CronNotifyWorkingCommand
from cryptobot.commands.cron_update_trades_for_partially_filled_orders import \
    CronUpdateTradesForPartiallyFilledOrdersCommand
from cryptobot.helpers import current_millis
from cryptobot.models import CronJob

millis_on_start = current_millis() - 10000 # dirty bidlokod

def dispatch(di: dict, args) -> None | tuple[None, type[ShowOrdersCommand]] | tuple[str, None]:

    if args.command == "show_orders":
        return (
            None,
            ShowOrdersCommand()
                .set_payload(args.chat_id)
                .set_deps(di['service_component'], di['view'])
        )
    elif args.command == "show_order_status":
        return (
            None,
            ShowOrderStatusCommand()
                .set_payload(
                    binance_order_id=args.binance_order_id,
                    chat_id=args.chat_id,
                )
                .set_deps(di['service_component'], di['view'])
        )
    elif args.command == "show_price":
        return (
            None,
            ShowPriceCommand()
                .set_payload(
                    args.binance_symbol,
                    args.chat_id,
                )
                .set_deps(di['service_component'], di['view'])
        )
    elif args.command == "show_price_chart_options":
        return (
            None,
            ShowPriceChartOptionsCommand()
                .set_payload(
                    args.binance_symbol,
                    args.chat_id,
                )
                .set_deps(di['service_component'], di['view'])
        )
    elif args.command == "show_price_chart":
        return (
            None,
            ShowPriceChartCommand()
                .set_payload(
                    args.binance_symbol,
                    args.period.replace('_', ' '),
                    args.interval,
                    args.chat_id,
                )
                .set_deps(di['service_component'], di['view'], di['plt'])
        )
    elif args.command == "show_settings":
        return (
            None,
            ShowSettingsCommand()
                .set_payload(args.chat_id,)
                .set_deps(di['service_component'], di['view'])
        )
    elif args.command == "webserver":
        return (
            None,
            WebserverCommand()
                .set_payload(
                    args.host,
                    args.port,
                    args.chat_id,
                )
                .set_deps(di['service_component'])
        )
    elif args.command == "hook":
        return (
            None,
            HookCommand()
                .set_deps(di['service_component'], di['view'], di['plt'])
        )
    elif args.command == "cron":
        return (
            None,
            CronCommand()
                .set_payload(
                    #args.chat_id,
                    # TODO: remove chat_id
                    #   send messages to order's owners (need table for that)
                    di['config']['telegram']['chat_id'],
                )
                .set_deps(di['service_component'], di['view'])
        )
    elif args.command == "misc":
        return (
            None,
            MiscCommand()
                .set_deps(
                    service_component = di['service_component'],
                    view = di['view'],
                    config = di['config'],
                )
        )

    else:
        err = f"ERROR: Unknown command: {args.command}\n"
        error(err)
        return err, None

def parse_args(cli_name: str):
    parser = argparse.ArgumentParser(description=cli_name)
    subparsers = parser.add_subparsers(dest="command", required=True)

    #
    (subparsers
         .add_parser("show_orders", help="Show orders")
         .add_argument("--chat_id", type=int, help="Telegram chat id")
     )

    # show_order_status
    parser_status = subparsers.add_parser("show_order_status", help="Show order status")
    parser_status.add_argument("--binance_order_id", type=int, help="Order ID")
    #parser_status.add_argument("--binance_symbol", default="ETHUSDT", help="Trading pair (symbol)")
    parser_status.add_argument("--chat_id", type=int, help="Telegram chat id")

    # show_price
    parser_price = subparsers.add_parser("show_price", help="Show symbol price")
    parser_price.add_argument("--binance_symbol", default="ETHUSDT", help="Trading pair (symbol)")
    parser_price.add_argument("--chat_id", type=int, help="Telegram chat id")

    # show_price_chart_options
    parser_price_chart_options = subparsers.add_parser("show_price_chart_options", help="Show options for price chart")
    parser_price_chart_options.add_argument("--binance_symbol", default="ETHUSDT", help="Trading pair (symbol)")
    parser_price_chart_options.add_argument("--chat_id", type=int, help="Telegram chat id")

    # show_price_chart
    parser_price_chart = subparsers.add_parser("show_price_chart", help="Show symbol price chart for period")
    parser_price_chart.add_argument("--binance_symbol", default="ETHUSDT", help="Trading pair (symbol)")
    parser_price_chart.add_argument("--period", default="1 week ago", help="Period to show")
    parser_price_chart.add_argument("--interval", default="1d", help="Interval for resolution")
    parser_price_chart.add_argument("--chat_id", type=int, help="Telegram chat id")

    # show_settings
    parser_show_settings = subparsers.add_parser("show_settings", help="Show settings")
    parser_show_settings.add_argument("--chat_id", type=int, help="Telegram chat id")

    # telegram_hook
    parser_telegram_hook = subparsers.add_parser("webserver", help="Wait for Telegram hooks")
    parser_telegram_hook.add_argument("--host", type=str, default="0.0.0.0", help="Host to listen to")
    parser_telegram_hook.add_argument("--port", type=int, default=8765, help="Port to listen to")
    parser_telegram_hook.add_argument("--chat_id", type=int, help="Telegram chat id")

    subparsers.add_parser("hook", help="Dispatch & execute hook")

    subparsers.add_parser("cron", help="Run cron tasks")
    #parser_cron = subparsers.add_parser("cron", help="Run cron tasks")
    #parser_cron.add_argument("--chat_id", type=int, help="Telegram chat id")

    subparsers.add_parser("misc", help="Some misc checks etc.")

    args = parser.parse_args()
    return args
