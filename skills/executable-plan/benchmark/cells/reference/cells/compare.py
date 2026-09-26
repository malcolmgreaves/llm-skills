"""Ordering of values for the comparison operators and lookups."""

from cells.values import Value, is_number


def _rank(value: Value) -> int:
    if isinstance(value, bool):
        return 2
    if is_number(value):
        return 0
    return 1  # text


def _empty_like(other: Value) -> Value:
    if isinstance(other, bool):
        return False
    if is_number(other):
        return 0.0
    return ""


def compare(a: Value, b: Value) -> int:
    """Returns -1, 0, or 1. Numbers < text < booleans; text ignores case; empty matches the other type."""
    if a is None and b is None:
        return 0
    if a is None:
        a = _empty_like(b)
    if b is None:
        b = _empty_like(a)
    rank_a, rank_b = _rank(a), _rank(b)
    if rank_a != rank_b:
        return -1 if rank_a < rank_b else 1
    if rank_a == 1:
        a, b = a.casefold(), b.casefold()
    return (a > b) - (a < b)
