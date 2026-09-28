---
name: typed-python
description: >-
  Writes readable, composable Python: full type annotations on every public
  name, precise types (TypeVar generics with bounds, TypedDict, frozen
  dataclasses, Protocol, Literal, NewType), clean runs of the project's type
  checker and of ruff, small pure functions composed into larger behavior,
  mutation kept inside classes, and table-driven tests. Use whenever you
  write, edit, refactor, or review Python code (.py or .pyi files, packages,
  scripts, or tests), and whenever the user mentions type hints, type
  annotations, typing, mypy, pyright, type errors, ruff, linting, lint
  errors, noqa, Any, TypedDict, dataclass, NamedTuple, TypeVar, generics,
  Protocol, composable or pure functions, side effects, global state,
  immutability, pytest parametrize, table tests, or test-driven development
  in Python.
license: MPL-2.0
metadata:
  version: "0.1.0"
  author: malcolmgreaves
---

# Typed, composable Python

Write Python whose types state exactly what each value is, whose behavior is
built from small functions that each do one thing, and whose logic is covered
by table-driven tests. The type checker and the tests then catch mistakes
before a person has to.

The rules apply in full to projects: packages, libraries, services, and any
module that other code imports. [One-off scripts](#6-one-off-scripts) relax
some of them.

The project's own conventions come first. If the project uses pydantic,
attrs, or msgspec for data classes, or unittest instead of pytest, use those
in the roles that this skill gives to dataclasses and pytest.

## Workflow

1. **Read the project setup.** Find the minimum Python version
   (`requires-python` in `pyproject.toml`, `.python-version`, or
   `setup.cfg`), the type checker and its settings (`[tool.mypy]`,
   `mypy.ini`, `[tool.pyright]`, `pyrightconfig.json`,
   `[tool.basedpyright]`, `[tool.pyrefly]`, `pyrefly.toml`, `[tool.ty]`,
   `ty.toml`, `[tool.zuban]`), the ruff settings (`[tool.ruff]`,
   `ruff.toml`, `.ruff.toml`), the test runner, and the commands that run
   them (`Makefile`, `justfile`, `noxfile.py`, `tox.ini`,
   `.pre-commit-config.yaml`, CI workflows). The Python version decides which
   typing syntax you can use: see
   [Syntax by Python version](#syntax-by-python-version).
2. **Design the types.** Define the data shapes first: dataclasses,
   TypedDicts, enums, and aliases. Then write each function's signature and a
   one-line docstring.
3. **Write the test table.** From the signature, predict the output for each
   of a set of inputs, including edge cases, and write them as a
   [table test](#7-write-table-tests). Writing the table before the
   implementation is preferred, not required. The tests are required either
   way.
4. **Implement** each function as a small transformation, then compose them.
5. **Check.** Run the type checker, ruff, and the tests, and fix every new
   finding. Don't report the work as done while any of them fails.

## 1. Annotate every public name

Annotate all of these, including the cases that look obvious:

- Every parameter and the return type of every public function and method,
  including `-> None`. `self` and `cls` are the only parameters without an
  annotation.
- `*args` and `**kwargs`, with the type of one element: `*paths: Path`,
  `**labels: str`.
- Every public class attribute and instance attribute. Declare instance
  attributes in the class body, or annotate them at their first assignment in
  `__init__`.
- Every public module-level variable. Mark constants `Final`.
- Test functions: `def test_parse(raw: str, expected: int) -> None:`. The
  annotations let the checker compare the test table with the signature of
  the function under test.

Annotate a local variable when the checker can't infer the type you mean: an
empty container (`seen: set[UserId] = set()`), a variable that starts as
`None`, or a value from an untyped call. Don't annotate a local whose type is
clear from its right-hand side.

**Private exemption.** A private function (its name starts with `_`) or a
function defined inside another function can omit annotations only when it is
a few lines long and its types are obvious from the call site. mypy doesn't
check the body of a function that has no annotations, so an unannotated
function is an unchecked function. Annotate it as soon as it grows.

When the project's checker requires annotations on every function (mypy's
`disallow_untyped_defs`, which `strict` turns on), annotate small private
functions too. Under strict mypy, an unannotated function costs more than
its annotations: its `def` line needs `# type: ignore[no-untyped-def]`,
each call from annotated code needs `# type: ignore[no-untyped-call]`, and
each result is `Any`. Use that fallback only if you can't make a small
private function's annotations type-check, and add a comment that says why.

Never write `Any` to satisfy this rule. `Any` turns off checking for every
value it touches. If a parameter accepts any value and the function doesn't
use the value's attributes, annotate it `object`.

## 2. Make types precise

A type is documentation that the checker verifies. The more exactly it
describes the values, the more mistakes the checker catches, and the less a
reader has to guess.

**Parameters accept the most general type you need; returns state the
specific type you build.** Take `Iterable[T]`, `Sequence[T]`, or
`Mapping[K, V]` from `collections.abc` when the function only reads the
argument, and return `list[T]` or `dict[K, V]`. A read-only parameter type
tells callers that you don't change their data, and it accepts tuples,
generators, and other containers.

**Containers name their key, value, and element types.** Never write bare
`dict`, `list`, or `tuple`. Don't write `dict[str, Any]` when you know what
the values are.

- Homogeneous mappings: `dict[UserId, Order]`, `Mapping[str, float]`.
- Tuples: `tuple[str, int]` for a fixed length, `tuple[int, ...]` for a
  variable length.
- IDs and units that share a runtime type:
  `UserId = NewType("UserId", int)`, so that the checker rejects an `OrderId`
  where a `UserId` belongs.
- Closed sets of values: `Literal["read", "write"]`, or an `Enum` when
  several modules use the set or it needs methods.

**A dict with a fixed set of keys gets a TypedDict.** When a dict has known
keys with a type per key (a JSON payload, a section of a config file, the
`**kwargs` of an API), define a `TypedDict` that describes it exactly. Mark
optional keys `NotRequired[...]`. Use a TypedDict only when the value must
stay a dict because it crosses a JSON, library, or `**kwargs` boundary. For
data that your own code creates and consumes, use a dataclass.

```python
class OrderPayload(TypedDict):
    """The JSON body of a request to place an order."""

    id: str
    quantity: int
    note: NotRequired[str]
```

**Struct-like data is a dataclass.** Default to
`@dataclass(frozen=True, slots=True)`. A frozen instance can't change after
construction, so any code can share it, hash it, and use it as a dict key.
Derive a modified copy with `dataclasses.replace(order, quantity=2)`. Add
`kw_only=True` when the class has more than a few fields, so call sites name
each value.

**A NamedTuple is for growing a tuple.** Prefer a dataclass to a
`NamedTuple`. A NamedTuple is still a tuple: it unpacks, indexes, and
compares equal to a plain tuple with the same values (`Point(1, 2) == (1, 2)`
is `True`). Its field order is part of its API, and adding a field breaks
every caller that unpacks it. Use a NamedTuple when a function already
returns a plain tuple: a NamedTuple with the same fields in the same order
gives the fields names without breaking callers that unpack or index the
result.

**A type variable connects an output type to an input type.**

```python
class Shape(Protocol):
    """Anything that has an area."""

    def area(self) -> float:
        """Returns the area."""


def largest[S: Shape](shapes: Sequence[S]) -> S:
    """Returns the shape with the largest area."""
    return max(shapes, key=lambda shape: shape.area())
```

With the signature `(shapes: Sequence[Shape]) -> Shape`, a caller that passes
`list[Circle]` gets back a `Shape` and loses the `Circle` attributes. With the
type variable `S`, the caller gets a `Circle`. The bound, `S: Shape`, states
the requirement (the value has `area()`) and lets the body call it. Add a
bound whenever the body relies on a method or attribute, or when the bound
tells the reader what the function is for. Constrain the type variable to a
fixed list, `[T: (str, bytes)]`, when the type must be exactly one of them. A
type variable that appears only once in a signature connects nothing: use
its bound, or `object`, instead. Before Python 3.12, declare it with
`TypeVar` at module level, `S = TypeVar("S", bound=Shape)`, and write
`def largest(shapes: Sequence[S]) -> S:`.

**A Protocol describes required behavior.** When a function needs "any
object with a `read()` method," accept a `Protocol` instead of a concrete
class. Callers and tests can then pass any object that has the methods, with
no inheritance.

**Functions passed as values have types.** Use `Callable[[Order], bool]` for
a predicate parameter, and `ParamSpec` for a decorator that keeps the
wrapped function's signature.

**None is explicit.** Write `X | None` for every value that can be `None`,
and handle the `None` case before you use the value. Don't return `None` to
report an error from a function that otherwise returns a value. Raise an
exception.

**Any stops at the boundary.** `json.loads`, untyped libraries, and
`getattr` return `Any`. In the function that receives such a value, validate
it and convert it to a precise type (a TypedDict, a dataclass, or a checked
primitive), so that `Any` doesn't spread into the rest of the code.

**Long types get a name.** Give a type alias to a type that appears in
several signatures: `type Totals = dict[CustomerId, Decimal]` on 3.12 and
later, or `Totals: TypeAlias = dict[CustomerId, Decimal]`.

### Syntax by Python version

Use the newest syntax that the project's minimum Python version supports.
The `typing_extensions` package backports the newer `typing` names. Use it
if the project already depends on it.

| Minimum Python | Adds |
| --- | --- |
| 3.9 | Built-in generics (`list[int]`, `dict[str, int]`); subscriptable `collections.abc` types |
| 3.10 | `X \| Y` unions, `TypeAlias`, `ParamSpec`, `TypeGuard`, `@dataclass(slots=True, kw_only=True)` |
| 3.11 | `Self`, `Required` and `NotRequired`, `Never`, `assert_never`, `LiteralString` |
| 3.12 | Type parameter lists (`def f[T](x: T) -> T:`, `class C[T]:`), `type X = ...` aliases, `@override`, `Unpack[SomeTypedDict]` for `**kwargs` |
| 3.13 | `TypeIs`, `ReadOnly` TypedDict items, TypeVar defaults |
| 3.14 | Lazy evaluation of annotations: forward references need no quotes |

Before 3.14, `from __future__ import annotations` lets annotations use
forward references and the 3.9 and 3.10 syntax on older versions. It doesn't
change expressions that run, such as a `TypeAlias` value or a `cast`
argument.

## 3. Run the checkers and trust them

The type checker and ruff run on every change. Treat what each one reports
as a bug in your code until you can show otherwise.

### Type checker

Run the project's type checker through the project's environment
(`uv run mypy`, `poetry run pyright`, `make typecheck`) after each change and
before you report the work as done. The checker must see the project's
installed dependencies, or it reports false errors about imports.

If the project has no type checker configured, run `mypy --strict` on the
files that you changed, if mypy is available, and tell the user what it
reported. Don't add a checker or its configuration to the project unless the
user asks.

Recommend the strictest practical settings for the project's checker when
the user sets up a checker or asks for stricter checking, and when the
project runs its checker without them. Apply a configuration only if the
user agrees. Read [type-checkers.md](references/type-checkers.md) for the
exact configuration of each checker (mypy, pyright, basedpyright, pyrefly,
ty, zuban), what each setting reports, each checker's ignore-comment
syntax, and, when the user asks which checker to use, a comparison of them.

Treat each reported error as a bug in your code. Type checkers report some
false positives and miss some real errors, but the checker is right far more
often than a first guess that it's wrong. Fix the error in the code or the
types: narrow with `isinstance` or an early return, make a function generic,
add an `@overload`, or split a function whose return type depends on the
value of an argument.

Work around an error only when both of these are true:

1. You tried to fix the code and the types, and the error remains.
2. You can show that the checker is wrong: a minimal example that is correct
   Python and still fails the check, or the checker's documentation or issue
   tracker describing the limitation.

Then use the narrowest workaround, in this order:

1. `cast(PreciseType, value)`, or an ignore comment with the error code on
   the one line, with a comment that says why the code is correct and links
   the issue if there is one. Use the syntax of the project's checker:
   `# type: ignore[code]` for mypy, `# pyright: ignore[rule]` for pyright
   and basedpyright, `# pyrefly: ignore[kind]`, or `# ty: ignore[rule]`.
   Each checker reads another checker's comment differently.
2. A wider type on the one value or parameter.
3. `Any`, confined to the smallest scope and converted back to a precise type
   as soon as possible.

Don't silence errors by changing the checker's configuration (disabling a
flag, adding an `ignore_errors` override, or setting
`ignore_missing_imports` for a package) unless the user agrees. For a
third-party package with no types, use its stub package (for example,
`types-requests`) if one exists, or write a `.pyi` stub for the parts that
you use.

Types don't replace tests. The checker can't see values, and it misses some
errors.

### Ruff

Ruff is a linter and formatter. Its rules find bugs and unclear code that a
type checker doesn't look for: a mutable default argument (`B006`), a
`global` statement (`PLW0603`), or older syntax than the target Python
version needs (the `UP` rules).

Run ruff the way the project does (`uv run ruff check`, `make lint`,
`pre-commit run ruff`) on the files that you changed, after each change and
before you report the work as done. If the project formats with ruff (a
`[tool.ruff.format]` section, a `ruff-format` pre-commit hook, or files that
`ruff format --check` already accepts), run `ruff format` on the files that
you changed, and on no others.

If the project has no ruff configuration, check the files that you changed
with the strict settings, with `--target-version` set to the project's
minimum Python version, and tell the user what ruff reported:

```bash
ruff check --isolated --select ALL --ignore COM812,CPY001 \
  --config "lint.pydocstyle.convention = 'google'" --target-version py312 FILES
```

Change the code the way each finding asks. Before you decide that a rule
doesn't apply, read why it exists with `ruff rule CODE`. Leave a finding
unfixed only when you can show one of these:

- It's a false positive: the code doesn't do what the rule describes.
- The fix makes the code worse in a way you can measure: it changes
  behavior, it fails a test, or it slows code that you timed.

Then suppress it on its one line, with the rule code and the reason:
`# noqa: T201  # the report is this command's output`. Don't write a bare
`# noqa` or a file-wide `# ruff: noqa`, and delete each `noqa` that ruff
reports as unused (`RUF100`). `ruff check --fix` applies only fixes that
ruff marks safe; review the diff. Don't apply `--unsafe-fixes` without
reading what each fix changes, because those fixes can change behavior.

As with the type checker, don't add rules to `ignore` or `per-file-ignores`
unless the user agrees. Read [ruff.md](references/ruff.md) when the user
sets up ruff or asks for stricter linting, for the strict configuration to
recommend, and when you decide whether a finding applies, for the rules
that enforce this skill.

## 4. Build behavior from small functions

Write functions that take values and return new values, each doing one thing
that its name states. Build larger behavior by composing them. A small pure
function is easy to read, to type precisely, to test with a table, and to
reuse. A large function that reads input, makes decisions, and writes output
is none of those.

- **One job per function.** If the docstring needs "and" to say what the
  function does, split the function. Name it with a verb phrase that says
  what it returns or does: `parse_order`, `is_shipped`, `total_by_customer`.
- **Pure by default.** The return value depends only on the arguments, and
  the function changes nothing outside itself. Pass in what the function
  needs: a value (`now: datetime`) when it needs one value, or a service
  typed by a Protocol or `Callable` when it needs to call something. Don't
  read a clock, a random generator, or a client from a global.
- **I/O at the edges.** Read input at the start, pass values through pure
  functions, and write output at the end. The pure middle needs no mocks to
  test. This pattern is called *functional core, imperative shell*.
- **Return new values; don't mutate arguments.** Build a new list or dict,
  or use `dataclasses.replace`. If a function must change an argument, say
  so in its name and docstring and return `None`, as `list.sort` does.
- **Readable over clever.** Prefer a comprehension to `map` or `filter` with
  a lambda. Name intermediate values. Use a plain loop when it reads more
  clearly than a comprehension. A list that a function builds and returns is
  not the mutation that this skill limits, because no caller sees it change.

The top level then reads as a list of steps:

```python
def main(path: Path) -> None:
    """Prints the total of the shipped orders in `path` for each customer."""
    orders = [parse_order(row) for row in read_rows(path)]  # input
    shipped = [order for order in orders if is_shipped(order)]
    totals = total_by_customer(shipped)
    print(format_report(totals))  # noqa: T201  # output
```

`parse_order`, `is_shipped`, `total_by_customer`, and `format_report` are
pure, and each one has its own table test.

## 5. Contain mutation

Mutate shared state only for performance: a large buffer, an incremental
index, a cache, or an in-place array operation. When you do, put the mutable
state inside a class and give callers restricted access to it:

- Store the state in private attributes (`self._lines`).
- Change the state only through methods that keep it valid.
- Return copies or read-only views (`tuple`, `frozenset`,
  `types.MappingProxyType`), never the internal object.

```python
class WordIndex:
    """Maps each word to the line numbers where it appears."""

    def __init__(self) -> None:
        """Creates an empty index."""
        self._lines: defaultdict[str, list[int]] = defaultdict(list)

    def add_line(self, number: int, text: str) -> None:
        """Records that each word in `text` appears on line `number`."""
        for word in text.split():
            self._lines[word].append(number)

    def lines_for(self, word: str) -> tuple[int, ...]:
        """Returns the lines where `word` appears, in the order added."""
        return tuple(self._lines.get(word, ()))
```

**Global state.** Module-level constants (`Final`) are fine. So is a global
cache whose entries never change after they are computed: `@functools.cache`
on a pure function, or a lookup table built once at import. Avoid mutable
module-level state in importable code. It couples every caller to every
other caller, makes test results depend on test order, and makes import
order matter. If a process-wide mutable object is unavoidable (a registry or
a connection pool), keep it private to one module and expose it through a
small function or class.

## 6. One-off scripts

A one-off script is a single file that you run directly (`python tool.py`,
`uv run tool.py`) and that nothing imports. In a script, you can:

- Keep mutable state at module level, such as a counter or parsed options.
- Use fewer abstractions: a dataclass instead of a Protocol, one file
  instead of several modules.

Keep the rest, because scripts often grow into modules: annotations on every
function, small functions with one job each, a `main()` function called from
`if __name__ == "__main__":`, and table tests for each function with
nontrivial logic. Code built this way moves into a package without a
rewrite.

## 7. Write table tests

Write tests with every change. Prefer to write them before the
implementation: after the signature and docstring exist, you can predict the
outputs.

For logic, write a table test: one test function and a table of inputs with
their expected outputs. Each row is one case, so a new case is one line, and
a reader sees all the behavior at once. Cover a typical input, empty input,
one element, boundaries, and invalid input. Give each row an ID that says
what it tests. Put error cases in a separate table, and match each error's
message, so that a test fails when the right exception type has the wrong
cause.

```python
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param("3", 3, id="single digit"),
        pytest.param(" 42 ", 42, id="surrounding whitespace"),
        pytest.param("1_000", 1000, id="underscore separator"),
    ],
)
def test_parse_quantity(raw: str, expected: int) -> None:
    """Parses each valid quantity."""
    assert parse_quantity(raw) == expected


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        pytest.param("", "invalid literal", id="empty"),
        pytest.param("-1", "negative", id="negative"),
        pytest.param("three", "invalid literal", id="not a number"),
    ],
)
def test_parse_quantity_rejects(raw: str, message: str) -> None:
    """Rejects each input that isn't a non-negative whole number."""
    with pytest.raises(ValueError, match=message):
        parse_quantity(raw)
```

With unittest, loop over a table and run each case in `self.subTest(...)`.

Test the I/O edges with a few tests that pass in fakes: small classes that
satisfy the Protocol that the function accepts. Test behavior through public
functions. Don't assert on private helpers, and don't write tests that
restate the implementation.

## Worked examples

Read [examples.md](references/examples.md) when you refactor a large
function into composed pieces, convert decoded JSON into typed values, test
code that depends on a service, write a decorator, write a unittest table
test, or need the format for a justified type-checker workaround.

## Checklist

Before you report Python work as done, confirm each item:

- Every public function, method, parameter, return value, attribute, and
  module-level variable has an annotation. Each unannotated private function
  is short and obvious, and the checker doesn't require its annotations.
- No bare `dict`, `list`, or `tuple`; no `dict[str, Any]` with known keys;
  no `Any` without a comment that justifies it.
- Each fixed-key dict has a TypedDict. Struct-like data is a dataclass,
  frozen unless there's a reason.
- Each type variable appears at least twice in its signature, with a bound
  (`[S: Shape]` or `bound=`) when the body relies on the bound's methods.
- The type checker and ruff report no new findings, and each `type: ignore`
  or `noqa` has a rule code and a comment with its reason.
- Functions are small and do one job. I/O is at the edges. No function
  changes its arguments unless its name says so.
- Shared mutable state lives in a class with private attributes.
  Module-level state is constant or a read-only cache, except in one-off
  scripts.
- Table tests cover the new logic, including edge and error cases, and they
  pass.
