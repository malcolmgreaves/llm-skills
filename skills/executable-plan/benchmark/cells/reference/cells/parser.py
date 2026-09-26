"""Parses formula text into a syntax tree."""

from cells import address
from cells.lexer import FormulaSyntaxError, Token, tokenize
from cells.nodes import Binary, Bool, Call, ErrorLiteral, Name, Node, Number, Range, Ref, Text, Unary

# Binary operators: (binding power, groups to the right). A higher power binds tighter.
BINARY = {
    "=": (1, False),
    "<>": (1, False),
    "<": (1, False),
    "<=": (1, False),
    ">": (1, False),
    ">=": (1, False),
    "&": (5, False),
    "+": (10, False),
    "-": (10, False),
    "*": (20, False),
    "/": (20, False),
    "^": (40, True),
}
# Unary + and - bind tighter than * and / and looser than ^, so -2^2 is -4.
PREFIX = 30


def parse(text: str) -> Node:
    """Returns the syntax tree of formula text. Raises FormulaSyntaxError."""
    parser = _Parser(tokenize(text))
    node = parser.expression(0)
    parser.expect("end")
    return node


class _Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def expect(self, kind: str) -> Token:
        token = self.advance()
        if token.kind != kind:
            found = token.text or "the end of the formula"
            raise FormulaSyntaxError(f"expected {kind} at position {token.start}, found {found}")
        return token

    def expression(self, min_power: int) -> Node:
        left = self.prefix()
        while True:
            token = self.peek()
            if token.kind != "op" or token.text not in BINARY:
                return left
            power, groups_right = BINARY[token.text]
            if power <= min_power:
                return left
            self.advance()
            right = self.expression(power - 1 if groups_right else power)
            left = Binary(token.text, left, right)

    def prefix(self) -> Node:
        token = self.advance()
        if token.kind == "number":
            return Number(float(token.text))
        if token.kind == "string":
            return Text(token.text[1:-1].replace('""', '"'))
        if token.kind == "error":
            return ErrorLiteral(token.text)
        if token.kind == "ref":
            first = address.parse_reference(token.text)
            if self.peek().kind == "op" and self.peek().text == ":":
                self.advance()
                last = address.parse_reference(self.expect("ref").text)
                return Range(min(first[0], last[0]), min(first[1], last[1]),
                             max(first[0], last[0]), max(first[1], last[1]))
            return Ref(*first)
        if token.kind == "name":
            if token.text.upper() in ("TRUE", "FALSE"):
                return Bool(token.text.upper() == "TRUE")
            return Name(token.text)
        if token.kind == "op" and token.text in ("+", "-"):
            return Unary(token.text, self.expression(PREFIX))
        if token.kind == "(":
            node = self.expression(0)
            self.expect(")")
            return node
        if token.kind == "func":
            return self.call(token)
        found = token.text or "the end of the formula"
        raise FormulaSyntaxError(f"unexpected {found} at position {token.start}")

    def call(self, name: Token) -> Call:
        self.expect("(")
        args: list[Node] = []
        if self.peek().kind != ")":
            args.append(self.expression(0))
            while self.peek().kind == "comma":
                self.advance()
                args.append(self.expression(0))
        self.expect(")")
        return Call(name.text.upper(), tuple(args))
