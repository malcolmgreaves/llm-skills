"""BACKLOG.md task `fill`."""

from conftest import is_error, sheet_with


# spec: fill F1
def test_absolute_marks_evaluate_normally():
    sheet = sheet_with(A1="3", Z9="=$A$1+A$1+$A1")
    assert sheet.value("Z9") == 9


# spec: fill F1 (range corners with marks)
def test_marked_range_corners():
    sheet = sheet_with(A1="1", D5="=ROWS($A$1:B3)")
    assert sheet.value("D5") == 3


# spec: fill F2 (example)
def test_fill_example():
    sheet = sheet_with(C1="=A1+$B$1+A$1+$A1")
    sheet.fill("C1", "D2:D2")
    assert sheet.content("D2") == "=B2+$B$1+B$1+$A2"


# spec: fill F2 (every target cell; the source is unchanged)
def test_fill_range():
    sheet = sheet_with(A1="1", A2="2", A3="3", B1="=A1*10")
    sheet.fill("B1", "B1:B3")
    assert sheet.content("B1") == "=A1*10"
    assert [sheet.value(ref) for ref in ("B1", "B2", "B3")] == [10, 20, 30]


# spec: fill F2 (example: Z1 moves to AA1) -- also needs the column fix
def test_fill_past_z():
    sheet = sheet_with(AA1="7", A2="=Z1")
    sheet.fill("A2", "B2:B2")
    assert sheet.content("B2") == "=AA1"
    assert sheet.value("B2") == 7


# spec: fill F3 (the rest of the formula text is unchanged)
def test_rest_of_formula_unchanged():
    sheet = sheet_with(A1="=round( B1 ,  2 )+sum(B1:C2)")
    sheet.fill("A1", "A2:A2")
    assert sheet.content("A2") == "=round( B2 ,  2 )+sum(B2:C3)"


# spec: fill F4
def test_reference_off_the_sheet():
    sheet = sheet_with(B2="=A1")
    sheet.fill("B2", "A1:A1")
    assert sheet.content("A1") == "=#REF!"
    assert is_error(sheet.value("A1"), "#REF!")


# spec: fill F4 (a range with a corner off the sheet)
def test_range_off_the_sheet():
    sheet = sheet_with(B2="=ROWS(A1:B2)+1")
    sheet.fill("B2", "B1:B1")
    assert sheet.content("B1") == "=ROWS(#REF!)+1"
    assert is_error(sheet.value("B1"), "#REF!")


# spec: fill F5
def test_non_formula_copied():
    sheet = sheet_with(A1="hello", B1="12")
    sheet.fill("A1", "A2:A3")
    sheet.fill("B1", "C1:C1")
    assert sheet.content("A3") == "hello" and sheet.content("C1") == "12"
