"""Parse user-entered numbers with dots, commas and grouping spaces."""

import math
from decimal import Decimal, InvalidOperation


def parse_number(value):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        try:
            number = Decimal(str(value))
        except InvalidOperation:
            return None
    else:
        text = str(value).strip()
        if not text:
            return None
        try:
            number = Decimal("".join(text.split()).replace(",", "."))
        except InvalidOperation:
            return None
    return number if number.is_finite() else None


def number_or_none(value):
    number = parse_number(value)
    if number is None:
        return None
    result = float(number)
    return result if math.isfinite(result) else None
