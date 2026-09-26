"""The command line: python3 -m cells eval FILE CELL."""

import argparse
import sys

from cells import address
from cells.sheet import Sheet


def load(path: str) -> Sheet:
    """Reads a CSV grid: the field in row r, column c goes to the cell at column c, row r."""
    sheet = Sheet()
    with open(path, encoding="utf-8") as file:
        for row, line in enumerate(file.read().splitlines(), start=1):
            for column, field in enumerate(line.split(","), start=1):
                if field:
                    sheet.set(address.name(column, row), field)
    return sheet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cells", description="Evaluate spreadsheet files.")
    commands = parser.add_subparsers(dest="command", required=True)
    evaluate = commands.add_parser("eval", help="print the value of one cell")
    evaluate.add_argument("file")
    evaluate.add_argument("cell")
    args = parser.parse_args(argv)

    try:
        sheet = load(args.file)
    except OSError as error:
        print(f"cells: cannot read {args.file}: {error.strerror}", file=sys.stderr)
        return 2
    try:
        text = sheet.display(args.cell)
    except ValueError as error:
        print(f"cells: {error}", file=sys.stderr)
        return 2
    print(text)
    return 0
