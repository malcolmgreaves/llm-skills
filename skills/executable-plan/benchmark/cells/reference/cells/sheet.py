"""A sheet of cells addressed in A1 notation, with cached values and dependency tracking."""

import re
from dataclasses import dataclass, field

from cells import address
from cells.errors import CYCLE, ERROR, CellError
from cells.evaluate import evaluate
from cells.lexer import FormulaSyntaxError, tokenize
from cells.nodes import Node, references
from cells.parser import parse
from cells.values import Value, display

NUMBER = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")

Key = tuple[int, int]


@dataclass
class Cell:
    content: str  # exactly as set
    is_formula: bool = False
    formula: Node | None = None  # the parsed formula; None if it doesn't parse
    literal: Value = None  # the value of content that isn't a formula
    refs: frozenset = field(default_factory=frozenset)  # the cells the formula refers to


def read_content(content: str) -> Cell:
    """Classifies cell content: a formula, forced text, a number, a boolean, or text."""
    if content.startswith("="):
        try:
            formula = parse(content[1:])
        except FormulaSyntaxError:
            return Cell(content, is_formula=True)
        return Cell(content, is_formula=True, formula=formula, refs=frozenset(references(formula)))
    if content.startswith("'"):
        return Cell(content, literal=content[1:])
    if NUMBER.fullmatch(content):
        return Cell(content, literal=float(content))
    if content.upper() in ("TRUE", "FALSE"):
        return Cell(content, literal=content.upper() == "TRUE")
    return Cell(content, literal=content)


class Sheet:
    """Cells keyed by address. Formula values are cached until a cell they depend on changes."""

    def __init__(self) -> None:
        self._cells: dict[Key, Cell] = {}
        self._cache: dict[Key, Value] = {}  # formula cell -> its current value
        self._dependents: dict[Key, set[Key]] = {}  # cell -> formula cells that refer to it
        self.evaluation_count = 0

    def set(self, ref: str, content: str) -> None:
        """Sets a cell's content. Empty content clears the cell. Raises ValueError for a bad address."""
        self._put(address.parse(ref), content)

    def _put(self, key: Key, content: str) -> None:
        old = self._cells.pop(key, None)
        if old is not None:
            for ref in old.refs:
                dependents = self._dependents[ref]
                dependents.discard(key)
                if not dependents:
                    del self._dependents[ref]
        if content != "":
            cell = read_content(content)
            self._cells[key] = cell
            for ref in cell.refs:
                self._dependents.setdefault(ref, set()).add(key)
        self._invalidate(key)

    def _invalidate(self, key: Key) -> None:
        # A formula is cached only after everything it refers to is, so an uncached
        # formula has no cached dependents, and the walk can stop there.
        self._cache.pop(key, None)
        pending = list(self._dependents.get(key, ()))
        while pending:
            dependent = pending.pop()
            if dependent in self._cache:
                del self._cache[dependent]
                pending.extend(self._dependents.get(dependent, ()))

    def content(self, ref: str) -> str:
        """Returns a cell's content exactly as set, or "" for an empty cell."""
        cell = self._cells.get(address.parse(ref))
        return cell.content if cell else ""

    def value(self, ref: str) -> Value:
        """Returns a cell's value: a float, str, bool, CellError, or None for an empty cell."""
        return self.value_at(*address.parse(ref))

    def value_at(self, column: int, row: int) -> Value:
        key = (column, row)
        cell = self._cells.get(key)
        if cell is None:
            return None
        if not cell.is_formula:
            return cell.literal
        if key not in self._cache:
            self._compute(key)
        return self._cache[key]

    def _is_pending(self, key: Key) -> bool:
        cell = self._cells.get(key)
        return cell is not None and cell.is_formula and key not in self._cache

    def _compute(self, key: Key) -> None:
        """Evaluates a formula and every uncached formula it depends on, without recursion.

        This is Tarjan's algorithm over the uncached formulas that `key` reaches. It finishes each
        strongly connected component after every component it depends on. A component of one cell
        that doesn't refer to itself is evaluated; every cell of any other component is in a cycle.
        """
        index = {key: 0}
        low = {key: 0}
        path = [key]  # visited cells whose component isn't finished yet
        on_path = {key}
        stack = [(key, iter(self._cells[key].refs))]
        while stack:
            current, refs = stack[-1]
            for ref in refs:
                if ref in on_path:
                    low[current] = min(low[current], index[ref])
                elif ref not in index and self._is_pending(ref):
                    index[ref] = low[ref] = len(index)
                    path.append(ref)
                    on_path.add(ref)
                    stack.append((ref, iter(self._cells[ref].refs)))
                    break
            else:
                stack.pop()
                if stack:
                    parent = stack[-1][0]
                    low[parent] = min(low[parent], low[current])
                if low[current] != index[current]:
                    continue
                component = []
                while not component or component[-1] != current:
                    component.append(path.pop())
                    on_path.discard(component[-1])
                if len(component) > 1 or current in self._cells[current].refs:
                    for member in component:
                        self._cache[member] = CellError(CYCLE)
                else:
                    self._cache[current] = self._evaluate(current)

    def _evaluate(self, key: Key) -> Value:
        self.evaluation_count += 1
        cell = self._cells[key]
        if cell.formula is None:
            return CellError(ERROR)
        result = evaluate(cell.formula, self)
        return 0.0 if result is None else result

    def display(self, ref: str) -> str:
        """Returns the text that a cell shows."""
        return display(self.value(ref))

    def addresses(self) -> list[str]:
        """Returns the addresses of the non-empty cells in row-major order."""
        return [address.name(column, row) for column, row in sorted(self._cells, key=lambda k: (k[1], k[0]))]

    def fill(self, source: str, target: str) -> None:
        """Copies a cell's content into every cell of a range, moving relative references."""
        from_column, from_row = address.parse(source)
        content = self.content(source)
        first_column, first_row, last_column, last_row = address.parse_range(target)
        for row in range(first_row, last_row + 1):
            for column in range(first_column, last_column + 1):
                if (column, row) == (from_column, from_row):
                    continue
                copy = content
                if content.startswith("="):
                    copy = "=" + move_references(content[1:], column - from_column, row - from_row)
                self._put((column, row), copy)


def _move(reference: str, columns: int, rows: int) -> str | None:
    match = address.REFERENCE.fullmatch(reference)
    column_mark, letters, row_mark, digits = match.groups()
    column = address.column_number(letters) + (0 if column_mark else columns)
    row = int(digits) + (0 if row_mark else rows)
    if column < 1 or row < 1:
        return None
    return f"{column_mark}{address.column_letters(column)}{row_mark}{row}"


def move_references(formula: str, columns: int, rows: int) -> str:
    """Moves each relative reference in formula text; a reference moved off the sheet becomes #REF!."""
    try:
        tokens = tokenize(formula)
    except FormulaSyntaxError:
        return formula
    pieces, copied, i = [], 0, 0
    while i < len(tokens):
        token = tokens[i]
        if token.kind != "ref":
            i += 1
            continue
        is_range = tokens[i + 1].text == ":" and tokens[i + 2].kind == "ref" if i + 2 < len(tokens) else False
        last = tokens[i + 2] if is_range else token
        first, second = _move(token.text, columns, rows), _move(last.text, columns, rows)
        pieces.append(formula[copied:token.start])
        if first is None or second is None:
            pieces.append("#REF!")
        else:  # a range keeps whatever it had between its corners, such as spaces around the colon
            pieces.append(first + formula[token.start + len(token.text):last.start] + second if is_range else first)
        copied = last.start + len(last.text)
        i += 3 if is_range else 1
    pieces.append(formula[copied:])
    return "".join(pieces)
