import argparse
from config import get_config

from components import ServiceComponent

def main():
    config: dict = get_config()

    parser = argparse.ArgumentParser(description="Cryptobot CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # read_orders
    subparsers.add_parser("read_orders", help="Read orders")
    #parser_read.add_argument("--symbol", default="ETHUSDT", help="Trading pair")

    # show_order_status
    parser_status = subparsers.add_parser("show_order_status", help="Show order status")
    parser_status.add_argument("--binance_order_id", type=int, help="Order ID")
    parser_status.add_argument("--binance_symbol", default="ETHUSDT", help="Trading pair (symbol)")

    args = parser.parse_args()

    service_component = ServiceComponent.create(config)

    if args.command == "read_orders":
        service_component.read_orders(config["telegram"]["chat_id"])
    elif args.command == "show_order_status":
        service_component.show_order_status(
            args.binance_order_id,
            args.binance_symbol,
            config["telegram"]["chat_id"],
        )
    else:
        print(f"Unknown command: {args.command}\n")


if __name__ == "__main__":
    main()