"""BACKLOG.md task `csvio`."""

from conftest import run_cli, sheet_with, write_csv


# spec: csvio C1
def test_load(tmp_path):
    from cells import csvio

    path = write_csv(tmp_path / "s.csv", [["1", "", "x"], ["=A1+1"]])
    sheet = csvio.load(path)
    assert sheet.value("A1") == 1 and sheet.value("B1") is None and sheet.value("C1") == "x"
    assert sheet.value("A2") == 2


# spec: csvio C1 (RFC 4180 quoting)
def test_load_quoted_fields(tmp_path):
    from cells import csvio

    path = tmp_path / "s.csv"
    path.write_text('"a,b","say ""hi""","line1\nline2"\r\n', encoding="utf-8")
    sheet = csvio.load(str(path))
    assert sheet.value("A1") == "a,b"
    assert sheet.value("B1") == 'say "hi"'
    assert sheet.value("C1") == "line1\nline2"


# spec: csvio C1 (the 27th field is AA1) -- also needs the column fix
def test_load_27th_column(tmp_path):
    from cells import csvio

    path = write_csv(tmp_path / "s.csv", [[str(n) for n in range(1, 28)]])
    sheet = csvio.load(path)
    assert sheet.value("AA1") == 27
    assert sheet.value("A1") == 1


# spec: csvio C2
def test_quote_prefix_forces_text():
    sheet = sheet_with(A1="'12", A2="'=1+1", A3="'TRUE")
    assert sheet.value("A1") == "12"
    assert sheet.value("A2") == "=1+1"
    assert sheet.value("A3") == "TRUE"
    assert sheet.content("A1") == "'12"


# spec: csvio C3 (values=False writes contents; minimal quoting; \r\n)
def test_save_contents(tmp_path):
    from cells import csvio

    sheet = sheet_with(A1="1", B1="a,b", A2="=A1*2")
    path = tmp_path / "out.csv"
    csvio.save(sheet, str(path))
    assert path.read_bytes() == b'1,"a,b"\r\n=A1*2,\r\n'


# spec: csvio C3 (values=True writes display text)
def test_save_values(tmp_path):
    from cells import csvio

    sheet = sheet_with(A1="1", B1="=1/0", A2="=A1/4")
    path = tmp_path / "out.csv"
    csvio.save(sheet, str(path), values=True)
    assert path.read_bytes() == b"1,#DIV/0!\r\n0.25,\r\n"


# spec: csvio C3 (grid from A1; an empty sheet writes an empty file)
def test_save_grid_and_empty(tmp_path):
    from cells import Sheet, csvio

    sheet = sheet_with(B2="5")
    path = tmp_path / "grid.csv"
    csvio.save(sheet, str(path))
    assert path.read_bytes() == b",\r\n,5\r\n"
    empty = tmp_path / "empty.csv"
    csvio.save(Sheet(), str(empty))
    assert empty.read_bytes() == b""


# spec: csvio C4
def test_round_trip(tmp_path):
    from cells import csvio

    contents = {"A1": "'12", "B1": 'a "q", b', "C1": "=A2*2", "A2": "-3.5", "C3": "'=x", "B3": "TRUE"}
    sheet = sheet_with(**contents)
    path = tmp_path / "rt.csv"
    csvio.save(sheet, str(path))
    loaded = csvio.load(str(path))
    for ref, content in contents.items():
        assert loaded.content(ref) == content
    assert loaded.value("C1") == -7


# spec: csvio C5 (the command line reads files with csvio.load: quoted fields)
def test_command_line_reads_quoted_fields(tmp_path):
    path = write_csv(tmp_path / "q.csv", [["a,b", "2"]])
    assert run_cli("eval", path, "A1").stdout == "a,b\n"
    assert run_cli("eval", path, "B1").stdout == "2\n"
