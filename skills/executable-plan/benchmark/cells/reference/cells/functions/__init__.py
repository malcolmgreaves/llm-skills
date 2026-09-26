"""The function registry.

Each family of functions lives in its own module in this package, registers its
functions with the `function` decorator, and is imported at the end of this file.
"""

from dataclasses import dataclass
from functools import partial
from typing import Callable

from cells.errors import NAME, VALUE, CellError
from cells.nodes import Range
from cells.ranges import RangeValue


@dataclass(frozen=True)
class Function:
    name: str
    implementation: Callable
    min_args: int
    max_args: int | None  # None: no limit
    ranges: bool = False  # receives a RangeValue for each range argument
    errors: bool = False  # receives error arguments instead of the call returning the first one
    lazy: bool = False  # receives a callable per argument that evaluates it


FUNCTIONS: dict[str, Function] = {}


def function(name: str, min_args: int, max_args: int | None, *, ranges=False, errors=False, lazy=False):
    """Registers the decorated callable as the spreadsheet function `name`.

    By default the callable receives the evaluated arguments, and if any argument
    is an error, the call returns the first one without calling it.
    """

    def register(implementation: Callable) -> Callable:
        FUNCTIONS[name.upper()] = Function(name.upper(), implementation, min_args, max_args, ranges, errors, lazy)
        return implementation

    return register


def range_value(node: Range, sheet) -> RangeValue:
    rows = []
    for row in range(node.first_row, node.last_row + 1):
        rows.append([sheet.value_at(column, row) for column in range(node.first_column, node.last_column + 1)])
    return RangeValue(rows)


def call(name: str, arg_nodes: tuple, sheet, evaluate) -> object:
    """Calls a function with unevaluated argument nodes. Returns a value."""
    found = FUNCTIONS.get(name.upper())
    if found is None:
        return CellError(NAME)
    count = len(arg_nodes)
    if count < found.min_args or (found.max_args is not None and count > found.max_args):
        return CellError(VALUE)

    def argument(node):
        if isinstance(node, Range):
            return range_value(node, sheet) if found.ranges else CellError(VALUE)
        return evaluate(node, sheet)

    if found.lazy:
        return found.implementation(*[partial(argument, node) for node in arg_nodes])
    args = [argument(node) for node in arg_nodes]
    if not found.errors:
        for arg in args:
            if isinstance(arg, CellError):
                return arg
    return found.implementation(*args)


from cells.functions import aggregate, information, logic, lookup, numeric, shape, text  # noqa: E402,F401
