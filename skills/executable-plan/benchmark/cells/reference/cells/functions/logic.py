"""Logical functions: IF, AND, OR, NOT."""

from cells.errors import VALUE, CellError
from cells.functions import function
from cells.values import is_number


def truth(value) -> bool | CellError:
    """Converts a condition: booleans as is, numbers true unless 0, empty false, text #VALUE!."""
    if isinstance(value, (bool, CellError)):
        return value
    if value is None:
        return False
    if is_number(value):
        return value != 0
    return CellError(VALUE)


@function("IF", 2, 3, lazy=True)
def if_(condition, then, otherwise=None):
    test = truth(condition())
    if isinstance(test, CellError):
        return test
    if test:
        return then()
    return otherwise() if otherwise is not None else False


def _tests(values) -> list | CellError:
    tests = [truth(value) for value in values]
    for test in tests:
        if isinstance(test, CellError):
            return test
    return tests


@function("AND", 1, None, errors=True)
def and_(*values):
    tests = _tests(values)
    return tests if isinstance(tests, CellError) else all(tests)


@function("OR", 1, None, errors=True)
def or_(*values):
    tests = _tests(values)
    return tests if isinstance(tests, CellError) else any(tests)


@function("NOT", 1, 1)
def not_(value):
    test = truth(value)
    return test if isinstance(test, CellError) else not test
