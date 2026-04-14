from decimal import Decimal, ROUND_HALF_UP

from django import template

register = template.Library()


@register.filter
def money(value):
    """Format a number as money with 2 decimal places and space as thousands separator.

    Example: 14764.54 → "14 764,54"
    """
    if value is None:
        return ""
    try:
        d = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception:
        return str(value)
    # Format with 2 decimals, space thousands separator, comma decimal
    sign = "-" if d < 0 else ""
    d = abs(d)
    integer_part = int(d)
    decimal_part = f"{d % 1:.2f}"[2:]  # Get "54" from "0.54"
    # Add space thousands separator
    int_str = f"{integer_part:,}".replace(",", " ")
    return f"{sign}{int_str},{decimal_part}"
