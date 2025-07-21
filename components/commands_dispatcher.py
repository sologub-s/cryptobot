import argparse

from commands import ShowOrdersCommand, TelegramHookListenerCommand, HookCommand
from commands import ShowOrderStatusCommand

def dispatch(di: dict, args) -> None | tuple[None, type[ShowOrdersCommand]] | tuple[str, None]:

    if args.command == "show_orders":
        return (
            None,
            ShowOrdersCommand()
                .set_payload(args.chat_id)
                .set_deps(di['service_component'])
        )
    elif args.command == "show_order_status":
        return (
            None,
            ShowOrderStatusCommand()
                .set_payload(
                    args.binance_order_id,
                    args.binance_symbol,
                    args.chat_id,
                )
                .set_deps(di['service_component'])
        )
    elif args.command == "telegram_hook_listener":
        return (
            None,
            TelegramHookListenerCommand()
                .set_payload(
                    args.host,
                    args.port,
                    args.chat_id,
                )
        )
    elif args.command == "hook":
        return (
            None,
            HookCommand()
                .set_deps(di['service_component'])
        )

    else:
        err = f"ERROR: Unknown command: {args.command}\n"
        print()
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
    parser_status.add_argument("--binance_symbol", default="ETHUSDT", help="Trading pair (symbol)")
    parser_status.add_argument("--chat_id", type=int, help="Telegram chat id")

    # telegram_hook
    parser_telegram_hook = subparsers.add_parser("telegram_hook_listener", help="Wait for Telegram hooks")
    parser_telegram_hook.add_argument("--host", type=str, default="0.0.0.0", help="Host to listen to")
    parser_telegram_hook.add_argument("--port", type=int, default=8765, help="Port to listen to")
    parser_telegram_hook.add_argument("--chat_id", type=int, help="Telegram chat id")

    subparsers.add_parser("hook", help="Dispatch & execute hook")

    args = parser.parse_args()
    return args
