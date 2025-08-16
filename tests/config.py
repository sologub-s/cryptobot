import os
from dotenv import load_dotenv
from cryptobot.config import get_config as get_original_config
load_dotenv()

def get_config() -> dict:
    """

    :rtype: dict
    """
    config: dict = get_original_config()

    config['db'] = {
        "host": os.getenv("TEST_DATABASE_HOST", ""),
        "port": int(os.getenv("TEST_DATABASE_PORT", "")),
        "name": os.getenv("TEST_DATABASE_NAME", ""),
        "user": os.getenv("TEST_DATABASE_USER", ""),
        "pass": os.getenv("TEST_DATABASE_PASS", ""),
    }

    config["view"]["views_folder"] = "../cryptobot/views"

    return config
