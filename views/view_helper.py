from datetime import datetime


def format_timestamp(timestamp: int, format_string: str = '%Y-%m-%d %H:%M:%S') -> str:
    return datetime.fromtimestamp(timestamp).strftime(format_string)

def get_globals():
    return {
        'format_timestamp': format_timestamp,
    }

