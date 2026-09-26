"""Cell addresses in A1 notation: column letters, then a row number from 1."""

import re

ADDRESS = re.compile(r"([A-Za-z]+)([1-9][0-9]*)")
# A reference in a formula: an address whose column and row can each be marked absolute with `$`.
REFERENCE = re.compile(r"(\$?)([A-Za-z]+)(\$?)([1-9][0-9]*)")


def column_number(letters: str) -> int:
    """Returns the 1-based column number of column letters: A is 1, Z is 26, AA is 27."""
    number = 0
    for letter in letters.upper():
        number = number * 26 + (ord(letter) - ord("A") + 1)
    return number


def column_letters(number: int) -> str:
    """Returns the letters of a 1-based column number: 1 is A, 27 is AA."""
    letters = ""
    while number > 0:
        number, remainder = divmod(number - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def parse(text: str) -> tuple[int, int]:
    """Returns (column, row) for an address such as `B12`. Raises ValueError for anything else."""
    match = ADDRESS.fullmatch(text)
    if not match:
        raise ValueError(f"not a cell address: {text!r}")
    return column_number(match.group(1)), int(match.group(2))


def parse_reference(text: str) -> tuple[int, int]:
    """Returns (column, row) for a reference that can carry `$` marks, such as `$B$12`."""
    match = REFERENCE.fullmatch(text)
    if not match:
        raise ValueError(f"not a cell reference: {text!r}")
    return column_number(match.group(2)), int(match.group(4))


def parse_range(text: str) -> tuple[int, int, int, int]:
    """Returns (first column, first row, last column, last row) for `B3:A1` or a single address."""
    first, _, last = text.partition(":")
    c1, r1 = parse(first)
    c2, r2 = parse(last) if last else (c1, r1)
    return min(c1, c2), min(r1, r2), max(c1, c2), max(r1, r2)


def name(column: int, row: int) -> str:
    """Returns the address of a column and row: (2, 12) is `B12`."""
    return f"{column_letters(column)}{row}"
