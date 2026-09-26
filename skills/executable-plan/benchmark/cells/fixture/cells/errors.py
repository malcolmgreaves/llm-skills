"""Error values. A formula that fails has an error value; evaluation never raises."""

from dataclasses import dataclass

DIV0 = "#DIV/0!"
VALUE = "#VALUE!"
ERROR = "#ERROR!"  # the formula text doesn't parse


@dataclass(frozen=True)
class CellError:
    """An error value such as `#DIV/0!`. Two errors with the same code are equal."""

    code: str

    def __str__(self) -> str:
        return self.code
