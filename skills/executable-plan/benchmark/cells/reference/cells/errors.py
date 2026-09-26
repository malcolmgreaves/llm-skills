"""Error values. A formula that fails has an error value; evaluation never raises."""

from dataclasses import dataclass

DIV0 = "#DIV/0!"
VALUE = "#VALUE!"
NAME = "#NAME?"
NA = "#N/A"
REF = "#REF!"
CYCLE = "#CYCLE!"
ERROR = "#ERROR!"  # the formula text doesn't parse

CODES = (DIV0, VALUE, NAME, NA, REF, CYCLE, ERROR)


@dataclass(frozen=True)
class CellError:
    """An error value such as `#DIV/0!`. Two errors with the same code are equal."""

    code: str

    def __str__(self) -> str:
        return self.code
