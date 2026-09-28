# Worked examples

Each example targets Python 3.12 and passes `mypy --strict` and the strict
ruff configuration that `SKILL.md` recommends. For an older minimum
version, translate the syntax with the table in `SKILL.md`.

## Contents

1. [Refactor a large function into composed pieces](#1-refactor-a-large-function-into-composed-pieces)
2. [Convert decoded JSON into typed values](#2-convert-decoded-json-into-typed-values)
3. [Test code that depends on a service](#3-test-code-that-depends-on-a-service)
4. [Type a decorator](#4-type-a-decorator)
5. [Write a table test with unittest](#5-write-a-table-test-with-unittest)
6. [Write a justified type-checker workaround](#6-write-a-justified-type-checker-workaround)

## 1. Refactor a large function into composed pieces

Before: one function reads a file, parses, filters, aggregates, and prints.
Nothing in it can be tested without a file on disk and a captured stdout,
and the types of its values are unknown.

```python
def report(path):
    totals = {}
    with open(path) as f:
        for line in csv.DictReader(f):
            if line["status"] != "shipped":
                continue
            c = line["customer"]
            totals[c] = totals.get(c, 0) + float(line["amount"])
    for c in sorted(totals):
        print(f"{c}: {totals[c]:.2f}")
```

After: the data shapes come first, then one function per step. Only
`read_rows` and `main` do I/O.

```python
import csv
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import NewType

CustomerId = NewType("CustomerId", str)


class Status(Enum):
    """Where an order is in fulfillment."""

    PENDING = "pending"
    SHIPPED = "shipped"


@dataclass(frozen=True, slots=True)
class Order:
    """One row of the orders file."""

    customer: CustomerId
    amount: Decimal
    status: Status


def read_rows(path: Path) -> list[dict[str, str]]:
    """Returns the rows of a CSV file, keyed by column name."""
    with path.open(newline="") as file:
        return list(csv.DictReader(file))


def parse_order(row: Mapping[str, str]) -> Order:
    """Converts one CSV row into an Order."""
    return Order(
        customer=CustomerId(row["customer"]),
        amount=Decimal(row["amount"]),
        status=Status(row["status"]),
    )


def is_shipped(order: Order) -> bool:
    """True if the order has shipped."""
    return order.status is Status.SHIPPED


def total_by_customer(orders: Iterable[Order]) -> dict[CustomerId, Decimal]:
    """Sums the order amounts for each customer."""
    totals: dict[CustomerId, Decimal] = {}
    for order in orders:
        totals[order.customer] = totals.get(order.customer, Decimal(0)) + order.amount
    return totals


def format_report(totals: Mapping[CustomerId, Decimal]) -> str:
    """Formats one line per customer, sorted by customer ID."""
    lines = [f"{customer}: {totals[customer]:.2f}" for customer in sorted(totals)]
    return "\n".join(lines)


def main(path: Path) -> None:
    """Prints the total of the shipped orders in `path` for each customer."""
    orders = [parse_order(row) for row in read_rows(path)]
    shipped = [order for order in orders if is_shipped(order)]
    totals = total_by_customer(shipped)
    print(format_report(totals))  # noqa: T201  # the report is the output
```

What changed, and why:

- `float` became `Decimal`, because money must not round.
- The status string became an `Enum`, so a typo such as `"shiped"` fails at
  parse time instead of silently filtering out every row.
- Customer IDs became a `NewType`, so the checker rejects a plain `str` or
  another kind of ID where a customer ID belongs.
- `total_by_customer` builds its result in a local dict. No caller can see
  that dict change, so the function is still pure.
- `main` prints, which ruff's `T201` reports. Printing the report is what
  the command is for, so the `noqa` comment names the rule and the reason.

Each pure step gets a table:

```python
from decimal import Decimal

import pytest

ALICE = CustomerId("alice")
BOB = CustomerId("bob")


def shipped_order(customer: CustomerId, amount: str) -> Order:
    """Returns a shipped order for `customer` with the given amount."""
    return Order(customer=customer, amount=Decimal(amount), status=Status.SHIPPED)


@pytest.mark.parametrize(
    ("orders", "expected"),
    [
        pytest.param([], {}, id="no orders"),
        pytest.param(
            [shipped_order(ALICE, "1.50")],
            {ALICE: Decimal("1.50")},
            id="one order",
        ),
        pytest.param(
            [
                shipped_order(ALICE, "1.50"),
                shipped_order(BOB, "2"),
                shipped_order(ALICE, "3"),
            ],
            {ALICE: Decimal("4.50"), BOB: Decimal(2)},
            id="sums per customer",
        ),
    ],
)
def test_total_by_customer(
    orders: list[Order], expected: dict[CustomerId, Decimal]
) -> None:
    """Sums the order amounts for each customer."""
    assert total_by_customer(orders) == expected


@pytest.mark.parametrize(
    ("totals", "expected"),
    [
        pytest.param({}, "", id="empty"),
        pytest.param({ALICE: Decimal("4.5")}, "alice: 4.50", id="two decimal places"),
        pytest.param(
            {BOB: Decimal(2), ALICE: Decimal(1)},
            "alice: 1.00\nbob: 2.00",
            id="sorted by customer",
        ),
    ],
)
def test_format_report(totals: dict[CustomerId, Decimal], expected: str) -> None:
    """Formats two decimal places, one line per customer, in sorted order."""
    assert format_report(totals) == expected
```

## 2. Convert decoded JSON into typed values

`json.loads` returns `Any`. Annotate the parser's parameter as `object`, not
`Any`: the checker then rejects every use of the value until the code has
narrowed it with `isinstance`, so the validation can't be skipped.

```python
import json
from typing import NotRequired, TypedDict


class UserPayload(TypedDict):
    """A user object from the accounts API."""

    id: int
    email: str
    nickname: NotRequired[str]


def parse_user(raw: object) -> UserPayload:
    """Validates a decoded JSON value as a UserPayload.

    Raises TypeError if the value isn't an object, or if a key is missing or
    its value has the wrong type.
    """
    if not isinstance(raw, dict):
        msg = f"expected a JSON object, got {type(raw).__name__}"
        raise TypeError(msg)
    user_id = raw.get("id")
    email = raw.get("email")
    if not isinstance(user_id, int) or not isinstance(email, str):
        msg = "`id` must be an integer and `email` must be a string"
        raise TypeError(msg)
    user: UserPayload = {"id": user_id, "email": email}
    nickname = raw.get("nickname")
    if nickname is not None:
        if not isinstance(nickname, str):
            msg = "`nickname` must be a string"
            raise TypeError(msg)
        user["nickname"] = nickname
    return user


user = parse_user(json.loads('{"id": 7, "email": "a@example.com"}'))
```

If the project uses pydantic, `pydantic.TypeAdapter(UserPayload).validate_python(raw)`
or a `BaseModel` does the same job. If it uses msgspec, use
`msgspec.json.decode(data, type=UserPayload)`.

## 3. Test code that depends on a service

Accept a Protocol, and pass a fake in tests. The fake needs no inheritance
and no mocking library, and the checker verifies that it matches the
Protocol.

```python
from dataclasses import dataclass
from typing import NewType, Protocol

UserId = NewType("UserId", int)


@dataclass(frozen=True, slots=True)
class User:
    """A user account."""

    email: str
    nickname: str | None = None


class UserStore(Protocol):
    """Looks up users by ID."""

    def get(self, user_id: UserId) -> User | None:
        """Returns the user with `user_id`, or None if there is none."""


def display_name(store: UserStore, user_id: UserId) -> str:
    """Returns the user's nickname, or their email if they have none."""
    user = store.get(user_id)
    if user is None:
        return "unknown user"
    return user.nickname or user.email
```

```python
import pytest


@dataclass(frozen=True, slots=True)
class FakeUserStore:
    """A UserStore that reads from a dict."""

    users: dict[UserId, User]

    def get(self, user_id: UserId) -> User | None:
        """Returns the user with `user_id`, or None if there is none."""
        return self.users.get(user_id)


STORE = FakeUserStore(
    {
        UserId(1): User(email="ada@example.com", nickname="Ada"),
        UserId(2): User(email="bob@example.com"),
    }
)


@pytest.mark.parametrize(
    ("user_id", "expected"),
    [
        pytest.param(UserId(1), "Ada", id="nickname"),
        pytest.param(UserId(2), "bob@example.com", id="no nickname"),
        pytest.param(UserId(3), "unknown user", id="missing user"),
    ],
)
def test_display_name(user_id: UserId, expected: str) -> None:
    """Prefers the nickname, then the email, and handles a missing user."""
    assert display_name(STORE, user_id) == expected
```

When the function needs only one value from a service, pass the value
instead: `is_expired(token: Token, now: datetime) -> bool` is simpler to
call and to test than `is_expired(token: Token, clock: Clock) -> bool`.

## 4. Type a decorator

`ParamSpec` keeps the wrapped function's parameter types, so callers of the
decorated function are still checked.

```python
import functools
import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


def logged[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Logs each call to the decorated function at DEBUG level."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        logger.debug("calling %s", func.__name__)
        return func(*args, **kwargs)

    return wrapper
```

Before Python 3.12, declare `P = ParamSpec("P")` and `R = TypeVar("R")` at
module level and write `def logged(func: Callable[P, R]) -> Callable[P, R]:`.

## 5. Write a table test with unittest

```python
import unittest
from typing import ClassVar


class ParseQuantityTest(unittest.TestCase):
    """Tests for parse_quantity."""

    CASES: ClassVar[list[tuple[str, str, int]]] = [
        ("single digit", "3", 3),
        ("surrounding whitespace", " 42 ", 42),
        ("underscore separator", "1_000", 1000),
    ]

    def test_parse_quantity(self) -> None:
        """Parses each valid quantity."""
        for name, raw, expected in self.CASES:
            with self.subTest(name, raw=raw):
                self.assertEqual(parse_quantity(raw), expected)
```

In a project that uses unittest, ruff's `PT` rules, which are for pytest,
don't apply: `PT009` reports `self.assertEqual`. Ignore `PT` in that
project's ruff configuration.

## 6. Write a justified type-checker workaround

A workaround is one line long, names the error code, and says in a comment
why the code is correct. Link the checker's issue when one exists. The next
reader can then check whether the limitation still applies and remove the
workaround.

```python
value = compute(arg)  # type: ignore[arg-type]  # <why the call is correct>; <link to the issue>
```

Prefer to convert an untyped value at the boundary over ignoring an error.
Here the library has no types, so its return value is `Any`, and `float()`
turns it into a checked `float` in the one place it enters the code:

```python
import legacy_geo  # untyped; the project's mypy config ignores its imports


def distance_km(a: Point, b: Point) -> float:
    """Returns the great-circle distance between two points in kilometers."""
    # legacy_geo.distance is untyped and documented to return kilometers.
    return float(legacy_geo.distance(a.lat, a.lon, b.lat, b.lon))
```
