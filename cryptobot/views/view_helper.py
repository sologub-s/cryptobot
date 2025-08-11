from datetime import datetime
from decimal import Decimal

from cryptobot.helpers import slugify as slugify_helper, money
from cryptobot.mappers.order_mapper import OrderMapper


def format_timestamp(timestamp: int, format_string: str = '%Y-%m-%d %H:%M:%S') -> str:
    return datetime.fromtimestamp(timestamp).strftime(format_string)

def slugify(value: str) -> str:
    return slugify_helper(value)

def remap_db_order_type(db_order_type: int) -> str:
    return OrderMapper.remap_type(db_order_type)

def remap_db_order_side(db_order_side: int) -> str:
    return OrderMapper.remap_side(db_order_side)

def remap_db_order_symbol(db_order_symbol: int) -> str:
    return OrderMapper.remap_symbol(db_order_symbol)

def remap_db_order_status(db_order_status: int) -> str:
    return OrderMapper.remap_status(db_order_status)

def decimal(value) -> Decimal:
    return Decimal(value)

def to_eng_string(value: Decimal) -> str:
    return value.to_eng_string()

def dec_to_str(value: Decimal) -> str:
    return money.dec_to_str(Decimal(value))

def show_type(value) -> str:
    return type(value).__name__

def get_globals():
    return {
        'format_timestamp': format_timestamp,
        'slugify': slugify,
        'remap_db_order_type': remap_db_order_type,
        'remap_db_order_side': remap_db_order_side,
        'remap_db_order_symbol': remap_db_order_symbol,
        'remap_db_order_status': remap_db_order_status,
        'decimal': decimal,
        'to_eng_string': to_eng_string,
        'dec_to_str': dec_to_str,
        'show_type': show_type,
    }

