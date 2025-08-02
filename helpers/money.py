from decimal import Decimal, ROUND_DOWN

def calculate_order_quantity(
    balance: Decimal,
    price: Decimal,
    step_size: Decimal,
    side: str
) -> Decimal:
    """
    Calculates quantity for a LIMIT order, rounded down to step size.

    :param balance: available balance (USDT for BUY, ETH for SELL)
    :param price: current price of the asset (ETH/USDT)
    :param step_size: minimum quantity increment (step size for ETH)
    :param side: "BUY" or "SELL"
    :return: valid order quantity rounded down
    """
    if side.upper() == "BUY":
        raw_qty = balance / price
    elif side.upper() == "SELL":
        raw_qty = balance
    else:
        raise ValueError("Side must be 'BUY' or 'SELL'")

    # Calculate precision from step_size (e.g., 0.001 → 3)
    quantized_qty = raw_qty.quantize(step_size, rounding=ROUND_DOWN)

    return quantized_qty

def increase_price_percent(price: Decimal, percent: Decimal) -> Decimal:
    price += (price / 100 * percent)
    return price

def decrease_price_percent(price: Decimal, percent: Decimal) -> Decimal:
    price -= (price / 100 * percent)
    return price

def dec_to_str(price: Decimal) -> str:
    return f"{price:.2f}"