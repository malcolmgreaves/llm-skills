"""A sheet of cells addressed in A1 notation."""

import re
from dataclasses import dataclass

from cells import address
from cells.errors import ERROR, CellError
from cells.evaluate import evaluate
from cells.lexer import FormulaSyntaxError
from cells.nodes import Node
from cells.parser import parse
from cells.values import Value, display

NUMBER = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")


@dataclass
class Cell:
    content: str  # exactly as set
    is_formula: bool = False
    formula: Node | None = None  # the parsed formula; None if it doesn't parse
    literal: Value = None  # the value of content that isn't a formula


def read_content(content: str) -> Cell:
    """Classifies cell content: a formula, a number, a boolean, or text."""
    if content.startswith("="):
        try:
            return Cell(content, is_formula=True, formula=parse(content[1:]))
        except FormulaSyntaxError:
            return Cell(content, is_formula=True)
    if NUMBER.fullmatch(content):
        return Cell(content, literal=float(content))
    if content.upper() in ("TRUE", "FALSE"):
        return Cell(content, literal=content.upper() == "TRUE")
    return Cell(content, literal=content)


class Sheet:
    """Cells keyed by address. Values are computed from the contents every time they're read."""

    def __init__(self) -> None:
        self._cells: dict[tuple[int, int], Cell] = {}

    def set(self, ref: str, content: str) -> None:
        """Sets a cell's content. Empty content clears the cell. Raises ValueError for a bad address."""
        key = address.parse(ref)
        if content == "":
            self._cells.pop(key, None)
        else:
            self._cells[key] = read_content(content)

    def content(self, ref: str) -> str:
        """Returns a cell's content exactly as set, or "" for an empty cell."""
        cell = self._cells.get(address.parse(ref))
        return cell.content if cell else ""

    def value(self, ref: str) -> Value:
        """Returns a cell's value: a float, str, bool, CellError, or None for an empty cell."""
        return self.value_at(*address.parse(ref))

    def value_at(self, column: int, row: int) -> Value:
        cell = self._cells.get((column, row))
        if cell is None:
            return None
        if not cell.is_formula:
            return cell.literal
        if cell.formula is None:
            return CellError(ERROR)
        result = evaluate(cell.formula, self)
        return 0.0 if result is None else result

    def display(self, ref: str) -> str:
        """Returns the text that a cell shows."""
        return display(self.value(ref))

    def addresses(self) -> list[str]:
        """Returns the addresses of the non-empty cells in row-major order."""
        return [address.name(column, row) for column, row in sorted(self._cells, key=lambda k: (k[1], k[0]))]
