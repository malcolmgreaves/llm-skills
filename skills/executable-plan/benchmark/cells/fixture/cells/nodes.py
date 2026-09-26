"""The syntax tree of a parsed formula."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Number:
    value: float


@dataclass(frozen=True)
class Ref:
    column: int
    row: int


@dataclass(frozen=True)
class Unary:
    op: str
    operand: "Node"


@dataclass(frozen=True)
class Binary:
    op: str
    left: "Node"
    right: "Node"


@dataclass(frozen=True)
class Call:
    name: str  # uppercase
    args: tuple["Node", ...]


Node = Number | Ref | Unary | Binary | Call
