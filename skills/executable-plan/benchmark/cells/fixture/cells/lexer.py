"""Splits formula text (the part after `=`) into tokens."""

import re
from dataclasses import dataclass

from cells import address


class FormulaSyntaxError(ValueError):
    """Raised when formula text isn't a valid formula."""


@dataclass(frozen=True)
class Token:
    kind: str  # number, ref, func, name, op, (, ), comma, or end
    text: str
    start: int  # the index of the token's first character in the formula text


_TOKEN = re.compile(
    r"""
    (?P<space>\s+)
  | (?P<number>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)
  | (?P<word>[A-Za-z_][A-Za-z0-9_.]*)
  | (?P<op>[-+*/^])
  | (?P<punct>[(),])
    """,
    re.VERBOSE,
)


def tokenize(text: str) -> list[Token]:
    """Returns the tokens of formula text, ending with an `end` token."""
    tokens = []
    pos = 0
    while pos < len(text):
        match = _TOKEN.match(text, pos)
        if not match:
            raise FormulaSyntaxError(f"unexpected {text[pos]!r} at position {pos}")
        kind, word = match.lastgroup, match.group()
        if kind == "word":
            if text[match.end():].lstrip().startswith("("):
                kind = "func"
            elif address.ADDRESS.fullmatch(word):
                kind = "ref"
            else:
                kind = "name"
        elif kind == "punct":
            kind = "comma" if word == "," else word
        if kind != "space":
            tokens.append(Token(kind, word, pos))
        pos = match.end()
    tokens.append(Token("end", "", len(text)))
    return tokens
