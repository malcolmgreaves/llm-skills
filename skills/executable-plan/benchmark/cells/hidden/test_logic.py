"""BACKLOG.md task `logic`."""

import pytest

from conftest import is_error, value


# spec: logic L1
@pytest.mark.parametrize("formula, expected", [
    ("=1<2", True), ("=2<=2", True), ("=3>4", False), ("=3>=4", False), ("=1=1", True), ("=1<>1", False),
])
def test_comparisons(formula, expected):
    assert value(formula) is expected


# spec: logic L1 (binds loosest, groups left)
def test_comparison_precedence():
    assert value("=1+1=2") is True
    assert value("=2*3>5") is True
    assert value("=1<2=TRUE") is True


# spec: logic L2 (text ignores case, types order)
def test_comparison_rules():
    assert value("=A1=A2", A1="abc", A2="ABC") is True
    assert value("=A1<A2", A1="a", A2="B") is True
    assert value("=5<TRUE") is True
    assert value("=A1<A2", A1="99", A2="zz") is True
    assert value("=FALSE<TRUE") is True


# spec: logic L2 (empty values)
def test_comparison_with_empty():
    assert value("=A1=0") is True
    assert value("=A1<1") is True
    assert value("=A1=A2") is True
    assert value("=A1=FALSE") is True


# spec: logic L2 (cells.compare.compare)
def test_compare_function():
    from cells.compare import compare

    assert compare(1.0, 2.0) == -1 and compare(2.0, 2.0) == 0
    assert compare("abc", "ABC") == 0 and compare("b", "A") == 1
    assert compare(5.0, "a") == -1 and compare(True, "z") == 1 and compare(False, True) == -1
    assert compare(None, 0.0) == 0 and compare(None, "") == 0 and compare(None, False) == 0 and compare(None, None) == 0


# spec: logic L2 (errors)
def test_comparison_errors():
    assert is_error(value("=1/0=1"), "#DIV/0!")
    assert is_error(value("=1=A1", A1="=1/0"), "#DIV/0!")


# spec: logic L3
def test_boolean_literals():
    assert value("=TRUE") is True
    assert value("=false") is False
    assert value("=TRUE+1") == 2


# spec: logic L4
def test_if():
    assert value("=IF(1<2, 10, 20)") == 10
    assert value("=IF(1>2, 10, 20)") == 20
    assert value("=IF(1>2, 10)") is False


# spec: logic L4 (only the returned branch matters)
def test_if_ignores_the_other_branch():
    assert value("=IF(TRUE, 1, 1/0)") == 1
    assert value("=IF(FALSE, NOPE(), 2)") == 2


# spec: logic L5
def test_condition_conversion():
    assert value("=IF(2, 1, 0)") == 1
    assert value("=IF(0, 1, 0)") == 0
    assert value("=IF(A1, 1, 0)") == 0
    assert is_error(value("=IF(A1, 1, 0)", A1="x"), "#VALUE!")
    assert is_error(value("=IF(1/0, 1, 0)"), "#DIV/0!")


# spec: logic L6
def test_and_or_not():
    assert value("=AND(TRUE, 1, 2>1)") is True
    assert value("=AND(TRUE, 0)") is False
    assert value("=OR(FALSE, 0, 3)") is True
    assert value("=OR(FALSE)") is False
    assert value("=NOT(0)") is True
    assert is_error(value("=AND(TRUE, 1/0)"), "#DIV/0!")
