"""Value types and the conversions between them.

A value is a number (float), text (str), a boolean (bool), an error (CellError),
or None for an empty cell.
"""

from cells.errors import VALUE, CellError

Value = float | str | bool | CellError | None


def is_number(value: Value) -> bool:
    """True if the value is a number; booleans aren't numbers."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def to_number(value: Value) -> float | CellError:
    """Converts an arithmetic operand: TRUE is 1, FALSE and empty are 0, text is #VALUE!."""
    if isinstance(value, CellError):
        return value
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if value is None:
        return 0.0
    if is_number(value):
        return float(value)
    return CellError(VALUE)


def number_text(number: float) -> str:
    """Returns a number as it displays: up to 15 significant digits, no trailing zeros."""
    return f"{number:g}"


def display(value: Value) -> str:
    """Returns the text that a cell shows for a value."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if is_number(value):
        return number_text(value)
    if isinstance(value, CellError):
        return value.code
    return value
