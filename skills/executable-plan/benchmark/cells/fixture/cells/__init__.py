"""A small spreadsheet engine: cells hold numbers, text, booleans, or formulas."""

from cells.errors import CellError
from cells.sheet import Sheet

__all__ = ["CellError", "Sheet"]
