"""Lookup functions: VLOOKUP, MATCH, INDEX."""

from cells.compare import compare
from cells.errors import NA, REF, VALUE, CellError
from cells.functions import function
from cells.ranges import RangeValue
from cells.values import to_number


def _equal(cell, key) -> bool:
    return not isinstance(cell, CellError) and compare(cell, key) == 0


def _position(value) -> int | CellError:
    number = to_number(value)
    return number if isinstance(number, CellError) else int(number)


@function("VLOOKUP", 3, 3, ranges=True)
def vlookup(key, table, column):
    if not isinstance(table, RangeValue):
        return CellError(VALUE)
    column = _position(column)
    if isinstance(column, CellError):
        return column
    if column < 1:
        return CellError(VALUE)
    if column > table.width:
        return CellError(REF)
    for row in table.rows:
        if _equal(row[0], key):
            return row[column - 1]
    return CellError(NA)


@function("MATCH", 2, 2, ranges=True)
def match(key, table):
    if not isinstance(table, RangeValue) or (table.height > 1 and table.width > 1):
        return CellError(NA)
    for position, cell in enumerate(table.values(), start=1):
        if _equal(cell, key):
            return float(position)
    return CellError(NA)


@function("INDEX", 2, 3, ranges=True)
def index(table, row, column=1.0):
    if not isinstance(table, RangeValue):
        return CellError(VALUE)
    row, column = _position(row), _position(column)
    for arg in (row, column):
        if isinstance(arg, CellError):
            return arg
    if not (1 <= row <= table.height and 1 <= column <= table.width):
        return CellError(REF)
    return table.rows[row - 1][column - 1]
