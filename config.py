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
            "bot_username": os.getenv("TELEGRAM_BOT_USERNAME", ""),
            "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
        },
        "view": {
            "views_folder": "../views"
        },
        "db": {
            "host": os.getenv("DATABASE_HOST", ""),
            "port": int(os.getenv("DATABASE_PORT", "")),
            "name": os.getenv("DATABASE_NAME", ""),
            "user": os.getenv("DATABASE_USER", ""),
            "pass": os.getenv("DATABASE_PASS", ""),
        }
    }
