"""README.md: behavior that exists before the backlog and must keep working."""

import pytest

from conftest import is_error, run_cli, sheet_with, value, write_csv


# spec: README "Formulas" (operator table)
@pytest.mark.parametrize("formula, expected", [
    ("=1+2*3", 7), ("=10-4-3", 3), ("=8/4/2", 1), ("=2*-3", -6), ("=2^3^2", 512), ("=-2^2", -4),
])
def test_operators_and_grouping(formula, expected):
    assert value(formula) == expected


# spec: README "Operands"
def test_operands():
    assert value("=A1+1", A1="TRUE") == 2
    assert value("=A1+1") == 1
    assert is_error(value("=A1+1", A1="abc"), "#VALUE!")


# spec: README "Operands" (an empty result is 0)
def test_empty_result_is_zero():
    assert value("=A9") == 0


# spec: README "Errors" (table and propagation example)
def test_errors_and_propagation():
    assert is_error(value("=1/0"), "#DIV/0!")
    assert is_error(value("=10^400"), "#VALUE!")
    assert is_error(value("=1+"), "#ERROR!")
    assert is_error(value("=A1+A2", A1="abc", A2="=1/0"), "#VALUE!")
    assert is_error(value("=A2+A1", A1="abc", A2="=1/0"), "#DIV/0!")


# spec: README "Functions"
def test_functions():
    assert value("=abs(-2)") == 2
    assert value("=SQRT(9)") == 3
    assert is_error(value("=SQRT(-1)"), "#VALUE!")
    assert value("=ROUND(1234, -2)") == 1200


# spec: README "Functions" (ROUND rounds halves away from zero) -- planted defect
def test_planted_round_halves_away_from_zero():
    assert value("=ROUND(2.5)") == 3
    assert value("=ROUND(-2.5)") == -3
    assert value("=ROUND(1.25, 1)") == 1.3


# spec: README "Addresses" (AA1 is column 27) -- planted defect
def test_planted_columns_after_z():
    sheet = sheet_with(AA1="5", AZ3="7", BA1="9")
    assert sheet.value("AA1") == 5
    assert sheet.value("A1") is None
    assert sheet.value("AZ3") == 7 and sheet.value("BA1") == 9
    from cells import address
    assert address.parse("AA1") == (27, 1)
    assert address.parse("BA1") == (53, 1)


# spec: README "Display" -- planted defect
def test_planted_display_uses_15_digits():
    sheet = sheet_with(A1="1234567", A2="=1/3", A3="=10^20", A4="=1/100000", A5="=0.1+0.2")
    assert [sheet.display(ref) for ref in ("A1", "A2", "A3", "A4", "A5")] == [
        "1234567", "0.333333333333333", "1e+20", "1e-05", "0.3"]


# spec: README "Display" and "Cell content"
def test_display_of_each_type():
    sheet = sheet_with(A1="3", A2="=1/4", A3="true", A4="hello", A5="=1/0")
    assert [sheet.display(ref) for ref in ("A1", "A2", "A3", "A4", "A5", "A6")] == [
        "3", "0.25", "TRUE", "hello", "#DIV/0!", ""]


# spec: README "The Sheet API"
def test_sheet_api():
    sheet = sheet_with(B2="=1+1", A2="x", C1="4")
    assert sheet.content("B2") == "=1+1"
    assert sheet.addresses() == ["C1", "A2", "B2"]
    sheet.set("B2", "")
    assert sheet.value("B2") is None and sheet.content("B2") == ""
    with pytest.raises(ValueError):
        sheet.set("1A", "1")


# spec: README "The Sheet API" (values reflect the current contents)
def test_values_follow_changes():
    sheet = sheet_with(A1="1", A2="=A1*10", A3="=A2+1")
    assert sheet.value("A3") == 11
    sheet.set("A1", "2")
    assert sheet.value("A3") == 21


# spec: README "Command line"
def test_cli_eval(tmp_path):
    path = write_csv(tmp_path / "s.csv", [["1", "2"], ["=A1+B1"]])
    result = run_cli("eval", path, "A2")
    assert result.returncode == 0 and result.stdout == "3\n"


# spec: README "Command line" (errors)
def test_cli_eval_errors(tmp_path):
    missing = run_cli("eval", str(tmp_path / "missing.csv"), "A1")
    assert missing.returncode == 2 and missing.stderr.startswith("cells: ")
    path = write_csv(tmp_path / "s.csv", [["1"]])
    bad = run_cli("eval", path, "1A")
    assert bad.returncode == 2 and bad.stderr.startswith("cells: ")
