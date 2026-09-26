"""The value a range argument passes to a function."""

from dataclasses import dataclass

from cells.values import Value


@dataclass
class RangeValue:
    """The values of a range: rows top to bottom, each row left to right, None for an empty cell."""

    rows: list[list[Value]]

    def values(self) -> list[Value]:
        """Returns every value in row-major order."""
        return [value for row in self.rows for value in row]

    @property
    def height(self) -> int:
        return len(self.rows)

    @property
    def width(self) -> int:
        return len(self.rows[0]) if self.rows else 0
