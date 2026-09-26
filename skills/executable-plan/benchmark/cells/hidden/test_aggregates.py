"""BACKLOG.md task `aggregates`."""

from conftest import is_error, value

A = {"A1": "2", "A2": "3", "A3": "hello", "A4": "TRUE"}


# spec: aggregates A6 (examples)
def test_examples():
    assert value("=SUM(A1:A3)", **A) == 5
    assert value("=COUNT(A1:A3)", **A) == 2
    assert value("=COUNTA(A1:A3)", **A) == 3
    assert value("=SUM(A1:A3, A4)", **A) == 6
    assert value("=SUM(A1:A4)", **A) == 5
    assert is_error(value("=SUM(A3)", **A), "#VALUE!")
    assert is_error(value("=AVERAGE(B1:B3)"), "#DIV/0!")


# spec: aggregates A6 (ROUND of AVERAGE) -- also needs the ROUND fix
def test_round_average_example():
    assert value("=ROUND(AVERAGE(A1:A2), 0)", **A) == 3


# spec: aggregates A2, A4 (booleans and text in a range are skipped)
def test_ranges_skip_text_and_booleans():
    cells = {"A1": "1", "A2": "TRUE", "A3": "x", "A4": "4"}
    assert value("=SUM(A1:A5)", **cells) == 5
    assert value("=AVERAGE(A1:A5)", **cells) == 2.5
    assert value("=MAX(A1:A5)", **cells) == 4
    assert value("=MIN(A1:A5)", **cells) == 1


# spec: aggregates A1, A3 (single values)
def test_single_values():
    assert value("=SUM(1, 2, A1)", A1="4") == 7
    assert value("=SUM(B1, B2, 1)", B1="TRUE", B2="FALSE") == 2
    assert value("=AVERAGE(4, A9)") == 4
    assert is_error(value('=SUM(1, A1)', A1="x"), "#VALUE!")


# spec: aggregates A4 (multiple ranges and single values)
def test_mixed_arguments():
    cells = {"A1": "1", "A2": "2", "B1": "10", "B2": "20"}
    assert value("=SUM(A1:A2, B1:B2, 100)", **cells) == 133
    assert value("=MAX(A1:B2, 5)", **cells) == 20
    assert value("=MIN(A1:B2, -1)", **cells) == -1


# spec: aggregates A4 (none counted)
def test_nothing_counted():
    assert value("=SUM(B1:B3)") == 0
    assert value("=MIN(B1:B3)") == 0
    assert value("=MAX(B1:B3)") == 0


# spec: aggregates A4 (the first error, in argument order then row-major order)
def test_errors_in_ranges():
    cells = {"A1": "1", "A2": "=NA()", "A3": "=1/0", "B1": "=SQRT(-1)"}
    assert is_error(value("=SUM(A1:A3)", **cells), "#N/A")
    assert is_error(value("=AVERAGE(B1:B1, A1:A3)", **cells), "#VALUE!")
    assert is_error(value("=MAX(A1:B3)", **cells), "#VALUE!")


# spec: aggregates A5 (COUNT and COUNTA never return an error)
def test_counts_ignore_errors():
    cells = {"A1": "1", "A2": "=1/0", "A3": "x", "A4": "TRUE"}
    assert value("=COUNT(A1:A5)", **cells) == 1
    assert value("=COUNTA(A1:A5)", **cells) == 4
    assert value("=COUNT(1, B1, A9)", B1="TRUE") == 2
    assert value("=COUNTA(1, A9, A2)", **cells) == 2
