"""Text functions: LEN, UPPER, LOWER, TRIM, LEFT, RIGHT, MID."""

import re

from cells.errors import VALUE, CellError
from cells.functions import function
from cells.values import to_number, to_text


def _text_function(transform):
    def implementation(value):
        text = to_text(value)
        return text if isinstance(text, CellError) else transform(text)

    return implementation


function("LEN", 1, 1)(_text_function(lambda text: float(len(text))))
function("UPPER", 1, 1)(_text_function(str.upper))
function("LOWER", 1, 1)(_text_function(str.lower))
function("TRIM", 1, 1)(_text_function(lambda text: re.sub(" +", " ", text).strip(" ")))


def _whole(value, minimum: int) -> int | CellError:
    number = to_number(value)
    if isinstance(number, CellError):
        return number
    if number < minimum:
        return CellError(VALUE)
    return int(number)


@function("LEFT", 1, 2)
def left(value, count=1.0):
    text, count = to_text(value), _whole(count, 0)
    for arg in (text, count):
        if isinstance(arg, CellError):
            return arg
    return text[:count]


@function("RIGHT", 1, 2)
def right(value, count=1.0):
    text, count = to_text(value), _whole(count, 0)
    for arg in (text, count):
        if isinstance(arg, CellError):
            return arg
    return text[max(0, len(text) - count):] if count else ""


@function("MID", 3, 3)
def mid(value, start, count):
    text, start, count = to_text(value), _whole(start, 1), _whole(count, 0)
    for arg in (text, start, count):
        if isinstance(arg, CellError):
            return arg
    return text[start - 1:start - 1 + count]
