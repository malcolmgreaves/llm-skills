"""BACKLOG.md task `lookup`. Keys that are text sit in cells, because text literals come from task `text`."""

from conftest import is_error, value

TABLE = {"A1": "apple", "B1": "3", "C1": "red",
         "A2": "Pear", "B2": "5", "C2": "green",
         "A3": "10", "B3": "7", "C3": "=1/0",
         "E1": "pear", "E2": "APPLE", "E3": "plum", "E4": "'10", "E5": "red"}


# spec: lookup V1
def test_vlookup():
    assert value("=VLOOKUP(E1, A1:C3, 2)", **TABLE) == 5
    assert value("=VLOOKUP(E2, A1:C3, 3)", **TABLE) == "red"
    assert value("=VLOOKUP(10, A1:C3, 2)", **TABLE) == 7


# spec: lookup V1 (no match; a number never equals text)
def test_vlookup_no_match():
    assert is_error(value("=VLOOKUP(E3, A1:C3, 2)", **TABLE), "#N/A")
    assert is_error(value("=VLOOKUP(E4, A1:C3, 2)", **TABLE), "#N/A")
    assert is_error(value("=VLOOKUP(3, A1:C3, 2)", **TABLE), "#N/A")


# spec: lookup V1 (column out of range)
def test_vlookup_bad_column():
    assert is_error(value("=VLOOKUP(E1, A1:C3, 0)", **TABLE), "#VALUE!")
    assert is_error(value("=VLOOKUP(E1, A1:C3, 4)", **TABLE), "#REF!")


# spec: lookup V2
def test_match():
    assert value("=MATCH(E1, A1:A3)", **TABLE) == 2
    assert value("=MATCH(5, A2:C2)", **TABLE) == 2
    assert is_error(value("=MATCH(E3, A1:A3)", **TABLE), "#N/A")
    assert is_error(value("=MATCH(5, A1:C3)", **TABLE), "#N/A")


# spec: lookup V3
def test_index():
    assert value("=INDEX(A1:C3, 2, 3)", **TABLE) == "green"
    assert value("=INDEX(A1:C3, 3)", **TABLE) == 10
    assert is_error(value("=INDEX(A1:C3, 4, 1)", **TABLE), "#REF!")
    assert is_error(value("=INDEX(A1:C3, 1, 4)", **TABLE), "#REF!")


# spec: lookup V4 (an error key; errors in the range)
def test_errors():
    assert is_error(value("=VLOOKUP(1/0, A1:C3, 2)", **TABLE), "#DIV/0!")
    assert is_error(value("=VLOOKUP(10, A1:C3, 3)", **TABLE), "#DIV/0!")
    assert value("=VLOOKUP(E5, C1:C3, 1)", **TABLE) == "red"
    cells = {"A1": "=NA()", "A2": "x", "B2": "found", "E1": "x"}
    assert value("=VLOOKUP(E1, A1:B2, 2)", **cells) == "found"
