"""Evaluates a syntax tree to a value."""

import math

from cells import functions
from cells.compare import compare
from cells.errors import DIV0, NAME, VALUE, CellError
from cells.nodes import Binary, Bool, Call, ErrorLiteral, Name, Node, Number, Range, Ref, Text, Unary
from cells.values import Value, to_number, to_text

COMPARISONS = {
    "=": lambda order: order == 0,
    "<>": lambda order: order != 0,
    "<": lambda order: order < 0,
    "<=": lambda order: order <= 0,
    ">": lambda order: order > 0,
    ">=": lambda order: order >= 0,
}


def evaluate(node: Node, sheet) -> Value:
    """Returns the value of a syntax tree. Errors are values; this never raises for bad input."""
    return EVALUATORS[type(node)](node, sheet)


def _unary(node: Unary, sheet) -> Value:
    operand = to_number(evaluate(node.operand, sheet))
    if isinstance(operand, CellError):
        return operand
    return -operand if node.op == "-" else operand


def _binary(node: Binary, sheet) -> Value:
    if node.op in COMPARISONS:
        convert = lambda value: value  # noqa: E731
    elif node.op == "&":
        convert = to_text
    else:
        convert = to_number
    # Operands convert left to right; the first error is the result.
    left = convert(evaluate(node.left, sheet))
    if isinstance(left, CellError):
        return left
    right = convert(evaluate(node.right, sheet))
    if isinstance(right, CellError):
        return right
    if node.op in COMPARISONS:
        return COMPARISONS[node.op](compare(left, right))
    if node.op == "&":
        return left + right
    return arithmetic(node.op, left, right)


def arithmetic(op: str, a: float, b: float) -> float | CellError:
    """Applies an arithmetic operator to two numbers."""
    if op == "+":
        result = a + b
    elif op == "-":
        result = a - b
    elif op == "*":
        result = a * b
    elif op == "/":
        if b == 0:
            return CellError(DIV0)
        result = a / b
    else:  # ^
        if a == 0 and b < 0:
            return CellError(DIV0)
        try:
            result = a**b
        except OverflowError:
            return CellError(VALUE)
        if isinstance(result, complex):
            return CellError(VALUE)
    if not math.isfinite(result):
        return CellError(VALUE)
    return result


EVALUATORS = {
    Number: lambda node, sheet: node.value,
    Text: lambda node, sheet: node.value,
    Bool: lambda node, sheet: node.value,
    ErrorLiteral: lambda node, sheet: CellError(node.code),
    Name: lambda node, sheet: CellError(NAME),
    Ref: lambda node, sheet: sheet.value_at(node.column, node.row),
    Range: lambda node, sheet: CellError(VALUE),  # a range outside a function argument
    Unary: _unary,
    Binary: _binary,
    Call: lambda node, sheet: functions.call(node.name, node.args, sheet, evaluate),
}
