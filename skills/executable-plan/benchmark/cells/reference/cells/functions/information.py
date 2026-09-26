"""Error functions: NA, ISERROR, IFERROR."""

from cells.errors import NA, CellError
from cells.functions import function


@function("NA", 0, 0)
def na():
    return CellError(NA)


@function("ISERROR", 1, 1, errors=True)
def iserror(value):
    return isinstance(value, CellError)


@function("IFERROR", 2, 2, errors=True)
def iferror(value, fallback):
    return fallback if isinstance(value, CellError) else value
