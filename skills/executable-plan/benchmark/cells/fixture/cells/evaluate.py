"""Evaluates a syntax tree to a value."""

import math

from cells import functions
from cells.errors import DIV0, VALUE, CellError
from cells.nodes import Binary, Call, Node, Number, Ref, Unary
from cells.values import Value, to_number


def evaluate(node: Node, sheet) -> Value:
    """Returns the value of a syntax tree. Errors are values; this never raises for bad input."""
    return EVALUATORS[type(node)](node, sheet)


def _number(node: Number, sheet) -> Value:
    return node.value


def _ref(node: Ref, sheet) -> Value:
    return sheet.value_at(node.column, node.row)


def _unary(node: Unary, sheet) -> Value:
    operand = to_number(evaluate(node.operand, sheet))
    if isinstance(operand, CellError):
        return operand
    return -operand if node.op == "-" else operand


def _binary(node: Binary, sheet) -> Value:
    # Operands convert left to right; the first error is the result.
    left = to_number(evaluate(node.left, sheet))
    if isinstance(left, CellError):
        return left
    right = to_number(evaluate(node.right, sheet))
    if isinstance(right, CellError):
        return right
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


def _call(node: Call, sheet) -> Value:
    return functions.call(node.name, node.args, sheet, evaluate)


EVALUATORS = {
    Number: _number,
    Ref: _ref,
    Unary: _unary,
    Binary: _binary,
    Call: _call,
}
