from decimal import Decimal, ROUND_DOWN

def calculate_order_quantity(
    balance: Decimal,
    price: Decimal,
    step_size: Decimal,
    side: str,
    min_qty: Decimal = None
) -> Decimal:
    """
    Calculates a quantity that is:
    - correctly rounded down to step_size
    - ≥ min_qty (if provided)
    - suitable for Binance LOT_SIZE filter

    Returns Decimal('0') if balance is too low.
    """
    if side.upper() == "BUY":
        raw_qty = balance / price
    elif side.upper() == "SELL":
        raw_qty = balance
    else:
        raise ValueError("Side must be 'BUY' or 'SELL'")

    quantized_qty = (raw_qty // step_size) * step_size

    if min_qty is not None and quantized_qty < min_qty:
        return Decimal('0')

    return quantized_qty


def increase_price_percent(price: Decimal, percent: Decimal) -> Decimal:
    price += (price / 100 * percent)
    return price

def decrease_price_percent(price: Decimal, percent: Decimal) -> Decimal:
    price -= (price / 100 * percent)
    return price

def dec_to_str(price: Decimal) -> str:
    return f"{price:.2f}"

def round_price(price: Decimal, tick_size: Decimal) -> Decimal:
    return (price // tick_size) * tick_size

def trim_trailing_zeros(d: Decimal) -> str:
    return format(d.normalize(), 'f').rstrip('0').rstrip('.') if '.' in str(d) else str(d)
