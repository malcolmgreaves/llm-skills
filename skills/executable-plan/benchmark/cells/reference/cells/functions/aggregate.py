"""Aggregate functions: SUM, AVERAGE, MIN, MAX, COUNT, COUNTA."""

import math

from cells.errors import DIV0, VALUE, CellError
from cells.functions import function
from cells.ranges import RangeValue
from cells.values import is_number


def _counted(args) -> list[float] | CellError:
    """The values SUM counts, or the first error in argument order and row-major order."""
    numbers = []
    for arg in args:
        if isinstance(arg, RangeValue):
            for value in arg.values():
                if isinstance(value, CellError):
                    return value
                if is_number(value):
                    numbers.append(float(value))
        elif isinstance(arg, CellError):
            return arg
        elif isinstance(arg, bool):
            numbers.append(1.0 if arg else 0.0)
        elif is_number(arg):
            numbers.append(float(arg))
        elif arg is not None:
            return CellError(VALUE)  # text as a single value
    return numbers


def _aggregate(name, reduce):
    @function(name, 1, None, ranges=True, errors=True)
    def implementation(*args):
        numbers = _counted(args)
        if isinstance(numbers, CellError):
            return numbers
        result = reduce(numbers)
        # A sum can overflow; a result that isn't a finite number is #VALUE! (README "Errors").
        return CellError(VALUE) if is_number(result) and not math.isfinite(result) else result

    return implementation


_aggregate("SUM", lambda numbers: float(sum(numbers)))
_aggregate("AVERAGE", lambda numbers: sum(numbers) / len(numbers) if numbers else CellError(DIV0))
_aggregate("MIN", lambda numbers: min(numbers) if numbers else 0.0)
_aggregate("MAX", lambda numbers: max(numbers) if numbers else 0.0)


@function("COUNT", 1, None, ranges=True, errors=True)
def count(*args):
    total = 0
    for arg in args:
        if isinstance(arg, RangeValue):
            total += sum(1 for value in arg.values() if is_number(value))
        elif isinstance(arg, bool) or is_number(arg):
            total += 1
    return float(total)


@function("COUNTA", 1, None, ranges=True, errors=True)
def counta(*args):
    total = 0
    for arg in args:
        if isinstance(arg, RangeValue):
            total += sum(1 for value in arg.values() if value is not None)
        elif arg is not None:
            total += 1
    return float(total)
