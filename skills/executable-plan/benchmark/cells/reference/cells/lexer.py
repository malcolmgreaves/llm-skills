"""Splits formula text (the part after `=`) into tokens."""

import re
from dataclasses import dataclass


class FormulaSyntaxError(ValueError):
    """Raised when formula text isn't a valid formula."""


@dataclass(frozen=True)
class Token:
    kind: str  # number, string, error, ref, func, name, op, (, ), comma, or end
    text: str
    start: int  # the index of the token's first character in the formula text


_TOKEN = re.compile(
    r"""
    (?P<space>\s+)
  | (?P<string>"(?:[^"]|"")*")
  | (?P<error>\#(?:DIV/0!|VALUE!|NAME\?|N/A|REF!|CYCLE!|ERROR!))
  | (?P<number>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)
  | (?P<ref>\$?[A-Za-z]+\$?[1-9][0-9]*)(?![A-Za-z0-9_.$])
  | (?P<word>[A-Za-z_][A-Za-z0-9_.]*)
  | (?P<op><>|<=|>=|[-+*/^&=<>:])
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
        if kind in ("ref", "word"):
            if text[match.end():].lstrip().startswith("(") and "$" not in word:
                kind = "func"
            elif kind == "word":
                kind = "name"
        elif kind == "punct":
            kind = "comma" if word == "," else word
        if kind != "space":
            tokens.append(Token(kind, word, pos))
        pos = match.end()
    tokens.append(Token("end", "", len(text)))
    return tokens
