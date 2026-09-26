"""Numeric functions: ABS, ROUND, SQRT."""

import math
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from cells.errors import VALUE, CellError
from cells.functions import function
from cells.values import to_number


@function("ABS", 1, 1)
def abs_(number):
    number = to_number(number)
    if isinstance(number, CellError):
        return number
    return abs(number)


@function("ROUND", 1, 2)
def round_(number, digits=0.0):
    number, digits = to_number(number), to_number(digits)
    for arg in (number, digits):
        if isinstance(arg, CellError):
            return arg
    try:
        exact = Decimal(repr(number)).quantize(Decimal(1).scaleb(-int(digits)), rounding=ROUND_HALF_UP)
    except InvalidOperation:  # more digits than Decimal carries: nothing to round
        return number
    return float(exact)


@function("SQRT", 1, 1)
def sqrt(number):
    number = to_number(number)
    if isinstance(number, CellError):
        return number
    if number < 0:
        return CellError(VALUE)
    return math.sqrt(number)
