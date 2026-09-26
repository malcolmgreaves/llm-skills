"""The function registry.

Each family of functions lives in its own module in this package, registers its
functions with the `function` decorator, and is imported at the end of this file.
"""

from dataclasses import dataclass
from typing import Callable

from cells.errors import VALUE, CellError


@dataclass(frozen=True)
class Function:
    name: str
    implementation: Callable
    min_args: int
    max_args: int | None  # None: no limit


FUNCTIONS: dict[str, Function] = {}


def function(name: str, min_args: int, max_args: int | None):
    """Registers the decorated callable as the spreadsheet function `name`.

    The callable receives the evaluated arguments. If any argument is an error,
    the call returns the first one without calling it.
    """

    def register(implementation: Callable) -> Callable:
        FUNCTIONS[name.upper()] = Function(name.upper(), implementation, min_args, max_args)
        return implementation

    return register


def call(name: str, arg_nodes: tuple, sheet, evaluate) -> object:
    """Calls a function with unevaluated argument nodes. Returns a value."""
    found = FUNCTIONS.get(name.upper())
    if found is None:
        return CellError(VALUE)
    count = len(arg_nodes)
    if count < found.min_args or (found.max_args is not None and count > found.max_args):
        return CellError(VALUE)
    args = [evaluate(node, sheet) for node in arg_nodes]
    for arg in args:
        if isinstance(arg, CellError):
            return arg
    return found.implementation(*args)


from cells.functions import numeric  # noqa: E402,F401  (registers ABS, ROUND, SQRT)
