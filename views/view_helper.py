from datetime import datetime
from helpers import slugify as slugify_helper


def format_timestamp(timestamp: int, format_string: str = '%Y-%m-%d %H:%M:%S') -> str:
    return datetime.fromtimestamp(timestamp).strftime(format_string)

def slugify(value: str) -> str:
    return slugify_helper(value)

def get_globals():
    return {
        'format_timestamp': format_timestamp,
        'slugify': slugify,
    }

