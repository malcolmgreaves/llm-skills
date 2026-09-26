"""The command line: python3 -m cells eval|print|set|check."""

import argparse
import json
import sys

from cells import address, csvio
from cells.errors import CellError


def _eval(sheet, args) -> int:
    print(sheet.display(args.cell))
    return 0


def _json_value(value):
    """A number, text, or boolean is itself in JSON; an error is {"error": code}."""
    return {"error": value.code} if isinstance(value, CellError) else value


def _print(sheet, args) -> int:
    if args.format == "csv":
        csvio.write(sheet, sys.stdout, values=True)
    elif args.format == "json":
        print(json.dumps({ref: _json_value(sheet.value(ref)) for ref in sheet.addresses()}))
    else:
        for ref in sheet.addresses():
            print(f"{ref}: {sheet.display(ref)}")
    return 0


def _set(sheet, args) -> int:
    sheet.set(args.cell, args.content)
    csvio.save(sheet, args.file)
    print(sheet.display(args.cell))
    return 0


def _check(sheet, args) -> int:
    failed = False
    for ref in sheet.addresses():
        value = sheet.value(ref)
        if isinstance(value, CellError):
            print(f"{ref}: {value.code}")
            failed = True
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cells", description="Evaluate spreadsheet files.")
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("eval", help="print the value of one cell")
    command.add_argument("file")
    command.add_argument("cell")
    command.set_defaults(run=_eval)
    command = commands.add_parser("print", help="print every non-empty cell")
    command.add_argument("file")
    command.add_argument("--format", choices=("text", "csv", "json"), default="text")
    command.set_defaults(run=_print)
    command = commands.add_parser("set", help="set a cell and save the file")
    command.add_argument("file")
    command.add_argument("cell")
    command.add_argument("content")
    command.set_defaults(run=_set)
    command = commands.add_parser("check", help="list the cells whose values are errors")
    command.add_argument("file")
    command.set_defaults(run=_check)
    args = parser.parse_args(argv)

    if hasattr(args, "cell"):
        try:
            address.parse(args.cell)
        except ValueError as error:
            print(f"cells: {error}", file=sys.stderr)
            return 2
    try:
        sheet = csvio.load(args.file)
    except (OSError, UnicodeDecodeError) as error:
        print(f"cells: cannot read {args.file}: {getattr(error, 'strerror', None) or error}", file=sys.stderr)
        return 2
    return args.run(sheet, args)
