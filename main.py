import argparse
import json
import sys

from config import get_config

from components import ServiceComponent

def main():
    config: dict = get_config()

    parser = argparse.ArgumentParser(description="Cryptobot CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # read_orders
    subparsers.add_parser("read_orders", help="Read orders")

    # show_order_status
    parser_status = subparsers.add_parser("show_order_status", help="Show order status")
    parser_status.add_argument("--binance_order_id", type=int, help="Order ID")
    parser_status.add_argument("--binance_symbol", default="ETHUSDT", help="Trading pair (symbol)")

    # telegram_hook
    subparsers.add_parser("telegram_hook_listener", help="Wait for Telegram hooks")
    subparsers.add_parser("hook", help="Dispatch & execute hook")

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
    elif args.command == "telegram_hook_listener":
        service_component.telegram_hook_listener()
    elif args.command == "hook":
        raw_data = sys.stdin.read()
        try:
            #json_text = json.loads(raw_data)

            #print(json_text)
            json_dict = json.loads(raw_data)
            chat_id = json_dict["message"]["chat"]["id"]
            if chat_id != config["telegram"]["chat_id"]:
                print("ERROR: wrong chat_id")

            if json_dict["message"]["text"] == "read_orders":
                service_component.read_orders(chat_id)

            elif json_dict["message"]["text"].startswith("show_order_status:"):
                json_dict["message"]["text"] = json_dict["message"]["text"].replace(" ", "")
                binance_order_id = json_dict["message"]["text"].split(":")[1]
                binance_symbol = json_dict["message"]["text"].split(":")[2]
                service_component.show_order_status(
                    binance_order_id,
                    binance_symbol,
                    chat_id,
                )
            else:
                json_text = json_dict["message"]["text"]
                json_text = "Unknown command: " + json_text
                service_component.telegram_component.send_telegram_message(config["telegram"]["chat_id"], json_text)
        except json.JSONDecodeError:
            print("Invalid JSON input")
        return
    else:
        print(f"Unknown command: {args.command}\n")


if __name__ == "__main__":
    main()