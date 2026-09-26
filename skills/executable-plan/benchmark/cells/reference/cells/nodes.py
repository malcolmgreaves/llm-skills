"""The syntax tree of a parsed formula."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Number:
    value: float


@dataclass(frozen=True)
class Text:
    value: str


@dataclass(frozen=True)
class Bool:
    value: bool


@dataclass(frozen=True)
class ErrorLiteral:
    code: str


@dataclass(frozen=True)
class Name:
    name: str


@dataclass(frozen=True)
class Ref:
    column: int
    row: int


@dataclass(frozen=True)
class Range:
    """A rectangle of cells, with its corners normalized to top left and bottom right."""

    first_column: int
    first_row: int
    last_column: int
    last_row: int

    def keys(self):
        for row in range(self.first_row, self.last_row + 1):
            for column in range(self.first_column, self.last_column + 1):
                yield column, row


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


Node = Number | Text | Bool | ErrorLiteral | Name | Ref | Range | Unary | Binary | Call


def references(node: Node) -> set[tuple[int, int]]:
    """Returns every cell a syntax tree refers to, including each cell of each range."""
    found: set[tuple[int, int]] = set()
    stack = [node]
    while stack:
        node = stack.pop()
        if isinstance(node, Ref):
            found.add((node.column, node.row))
        elif isinstance(node, Range):
            found.update(node.keys())
        elif isinstance(node, Unary):
            stack.append(node.operand)
        elif isinstance(node, Binary):
            stack.extend((node.left, node.right))
        elif isinstance(node, Call):
            stack.extend(node.args)
    return found
