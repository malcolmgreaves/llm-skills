"""Reads and writes sheets as CSV files."""

import csv
from typing import TextIO

from cells import address
from cells.sheet import Sheet


def load(path: str) -> Sheet:
    """Reads a CSV file: the field in row r, column c goes to the cell at column c, row r."""
    sheet = Sheet()
    with open(path, newline="", encoding="utf-8") as file:
        for row, record in enumerate(csv.reader(file), start=1):
            for column, field in enumerate(record, start=1):
                if field:
                    sheet.set(address.name(column, row), field)
    return sheet


def write(sheet: Sheet, file: TextIO, values: bool = False) -> None:
    """Writes the grid from A1 to the last used row and column: contents, or display text if `values`."""
    keys = [address.parse(ref) for ref in sheet.addresses()]
    if not keys:
        return
    last_column = max(column for column, _ in keys)
    last_row = max(row for _, row in keys)
    field = sheet.display if values else sheet.content
    writer = csv.writer(file)
    for row in range(1, last_row + 1):
        writer.writerow([field(address.name(column, row)) for column in range(1, last_column + 1)])


def save(sheet: Sheet, path: str, values: bool = False) -> None:
    """Writes a sheet to a CSV file; see `write`."""
    with open(path, "w", newline="", encoding="utf-8") as file:
        write(sheet, file, values)
