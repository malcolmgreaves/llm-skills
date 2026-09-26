"""BACKLOG.md task `recalc`."""

import time

from conftest import is_error, sheet_with


# spec: recalc K1, K2 (one formula, read twice, is evaluated once, whether on set or on read)
def test_values_are_cached():
    sheet = sheet_with(A1="1", A2="=A1+1")
    assert sheet.value("A2") == 2
    assert sheet.value("A2") == 2
    assert sheet.evaluation_count == 1


# spec: recalc K2 (only dependents are evaluated again, each once)
def test_only_dependents_recompute():
    cells = {"A1": "1", "Z1": "=5*5"}
    cells.update({f"B{n}": f"=A1+{n}" for n in range(1, 51)})
    sheet = sheet_with(**cells)
    refs = list(cells)
    for ref in refs:
        sheet.value(ref)
    start = sheet.evaluation_count
    sheet.set("A1", "2")
    for _ in range(3):
        for ref in refs:
            sheet.value(ref)
    assert sheet.evaluation_count - start == 50
    assert sheet.value("B50") == 52


# spec: recalc K2 (indirect dependents)
def test_indirect_dependents_recompute_once():
    sheet = sheet_with(A1="1", A2="=A1*2", A3="=A2+A1", A4="=A3+A2")
    for ref in ("A2", "A3", "A4"):
        sheet.value(ref)
    start = sheet.evaluation_count
    sheet.set("A1", "10")
    assert sheet.value("A4") == 50
    assert sheet.value("A3") == 30
    assert sheet.evaluation_count - start == 3


# spec: recalc K4 (self reference and a two-cell cycle)
def test_cycles():
    sheet = sheet_with(A1="=A1+1", B1="=B2", B2="=B1")
    assert is_error(sheet.value("A1"), "#CYCLE!")
    assert is_error(sheet.value("B1"), "#CYCLE!")
    assert is_error(sheet.value("B2"), "#CYCLE!")


# spec: recalc K4 (a cell depending on a cycle, and recovery)
def test_cycle_propagates_and_recovers():
    sheet = sheet_with(A1="=A3", A2="=A1", A3="=A2", B1="=A1*2")
    assert is_error(sheet.value("B1"), "#CYCLE!")
    assert is_error(sheet.value("A2"), "#CYCLE!")
    sheet.set("A3", "4")
    assert sheet.value("A1") == 4
    assert sheet.value("A2") == 4
    assert sheet.value("B1") == 8


def _chain(order):
    from cells import Sheet

    sheet = Sheet()
    for n in order:
        sheet.set(f"A{n}", "1" if n == 1 else f"=A{n - 1}+1")
    return sheet


# spec: recalc K5 (set in reverse order; deep chain)
def test_long_chain_in_reverse_order():
    started = time.perf_counter()
    sheet = _chain(range(10000, 0, -1))
    assert sheet.value("A10000") == 10000
    values = [sheet.value(f"A{n}") for n in range(1, 10001)]
    assert values[-1] == 10000
    assert time.perf_counter() - started < 5


# spec: recalc K5 (set in order; read every value; then change A1)
def test_long_chain_performance():
    started = time.perf_counter()
    sheet = _chain(range(1, 10001))
    for n in range(1, 10001):
        sheet.value(f"A{n}")
    assert time.perf_counter() - started < 5
    started = time.perf_counter()
    sheet.set("A1", "5")
    values = [sheet.value(f"A{n}") for n in range(1, 10001)]
    assert values[-1] == 10004
    assert time.perf_counter() - started < 5
