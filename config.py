import os
from dotenv import load_dotenv

load_dotenv()

def get_config() -> dict:
    """

    :rtype: dict
    """
    return {
        "binance": {
            "api": {
                "key": os.getenv("BINANCE_API_KEY", ""),
                "secret": os.getenv("BINANCE_API_SECRET", ""),
            },
        },
        "telegram": {
            "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
            "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
        },
    }
