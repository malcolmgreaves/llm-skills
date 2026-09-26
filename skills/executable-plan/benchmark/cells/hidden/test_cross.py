"""Behavior that needs two or more tasks, each part stated by a rule of its own task."""

from conftest import is_error, parse_json, run_cli, sheet_with, value, write_csv


# spec: G1, recalc K2 and K3, aggregates A4
def test_sum_updates_when_its_range_changes():
    sheet = sheet_with(A1="1", A2="2", A3="3", B1="=SUM(A1:A3)")
    assert sheet.value("B1") == 6
    start = sheet.evaluation_count
    sheet.set("A2", "20")
    assert sheet.value("B1") == 24
    assert sheet.value("B1") == 24
    assert sheet.evaluation_count - start == 1


# spec: G1, lookup V1
def test_vlookup_updates_when_its_table_changes():
    sheet = sheet_with(A1="1", B1="one", A2="2", B2="two", D1="=VLOOKUP(2, A1:B2, 2)")
    assert sheet.value("D1") == "two"
    sheet.set("B2", "deux")
    assert sheet.value("D1") == "deux"


# spec: recalc K3 and K4, aggregates A1
def test_range_that_contains_its_own_cell_is_a_cycle():
    sheet = sheet_with(A1="1", A2="2", A3="=SUM(A1:A3)")
    assert is_error(sheet.value("A3"), "#CYCLE!")


# spec: recalc K4 (every cell in a cycle is #CYCLE!), errors E5 (a cell outside the cycle can catch it)
def test_iferror_inside_a_cycle_is_still_a_cycle():
    sheet = sheet_with(A1="=A2+B1", A2="=A1", B1="=IFERROR(A1, 5)", C1="=IFERROR(A1, 5)")
    assert is_error(sheet.value("A1"), "#CYCLE!")
    assert is_error(sheet.value("B1"), "#CYCLE!")
    assert sheet.value("C1") == 5


# spec: logic L1 and L2, text T2
def test_concatenation_binds_tighter_than_comparison():
    assert value('="a"&"b"="AB"') is True
    assert value('=1&2=12') is False  # "12" is text, 12 is a number


# spec: errors E4 and E5, text T3 and T5
def test_error_functions_with_text():
    assert is_error(value("=LEN(1/0)"), "#DIV/0!")
    assert value('=ISERROR(LEFT("abc", -1))') is True
    assert value('=IFERROR(1/0, "none")') == "none"


# spec: errors E5, aggregates A4
def test_iferror_around_an_average():
    assert value("=IFERROR(AVERAGE(B1:B3), 0)") == 0


# spec: logic L4, aggregates A4, errors E4
def test_if_with_aggregates_and_errors():
    assert value("=IF(SUM(A1:A2)>4, 1, 0)", A1="2", A2="3") == 1
    assert value("=IF(ISERROR(1/0), 1, 2)") == 1


# spec: errors E5, lookup V1
def test_iferror_around_a_failed_lookup():
    assert value("=IFERROR(VLOOKUP(9, A1:B2, 2), -1)", A1="1", B1="x") == -1


# spec: fill F3 (example), text T1 and T2
def test_fill_leaves_text_literals_alone():
    sheet = sheet_with(A2="z")
    sheet.set("C1", '="A1"&A1')
    sheet.fill("C1", "C2:C2")
    assert sheet.content("C2") == '="A1"&A2'
    assert sheet.value("C2") == "A1z"


# spec: G1, fill F2
def test_filled_formulas_follow_changes():
    sheet = sheet_with(A1="1", A2="2", B1="=A1*2")
    sheet.fill("B1", "B2:B2")
    assert sheet.value("B2") == 4
    sheet.set("A2", "5")
    assert sheet.value("B2") == 10


# spec: csvio C1, aggregates A4, G1
def test_loaded_file_with_aggregates(tmp_path):
    from cells import csvio

    path = write_csv(tmp_path / "s.csv", [["=SUM(A2:A3)"], ["4"], ["5"]])
    sheet = csvio.load(path)
    assert sheet.value("A1") == 9
    sheet.set("A3", "6")
    assert sheet.value("A1") == 10


# spec: cli X4, aggregates A4, text T2
def test_cli_json_with_formulas(tmp_path):
    path = write_csv(tmp_path / "s.csv", [["2", "3", "=SUM(A1:B1)", '=A1&"x"']])
    data = parse_json(run_cli("print", path, "--format", "json").stdout)
    assert data == {"A1": 2, "B1": 3, "C1": 5, "D1": "2x"}
