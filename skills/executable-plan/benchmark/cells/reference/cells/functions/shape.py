"""Range shape functions: ROWS, COLUMNS."""

from cells.errors import VALUE, CellError
from cells.functions import function
from cells.ranges import RangeValue


@function("ROWS", 1, 1, ranges=True)
def rows(value):
    return float(value.height) if isinstance(value, RangeValue) else CellError(VALUE)


@function("COLUMNS", 1, 1, ranges=True)
def columns(value):
    return float(value.width) if isinstance(value, RangeValue) else CellError(VALUE)
