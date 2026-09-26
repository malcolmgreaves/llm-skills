"""BACKLOG.md task `cli`."""

from conftest import parse_json, read_csv_text, run_cli, write_csv


def sample(tmp_path):
    rows = [["1", "hello", "=A1/0"] + [""] * 23 + ["=A1+1"], ["TRUE", "=A1*12"]]
    return write_csv(tmp_path / "s.csv", rows)


# spec: cli X1, X2 (text format; row-major order puts B1 before AA1 before A2)
def test_print_text(tmp_path):
    result = run_cli("print", sample(tmp_path))
    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "A1: 1", "B1: hello", "C1: #DIV/0!", "AA1: 2", "A2: TRUE", "B2: 12"]


# spec: cli X2 (explicit --format text)
def test_print_text_explicit(tmp_path):
    path = write_csv(tmp_path / "t.csv", [["=2+2"]])
    assert run_cli("print", path, "--format", "text").stdout == "A1: 4\n"


# spec: cli X3
def test_print_csv(tmp_path):
    path = write_csv(tmp_path / "t.csv", [["1", "=A1/4"], ["a,b", "=1/0"]])
    result = run_cli("print", path, "--format", "csv")
    assert result.returncode == 0
    assert read_csv_text(result.stdout) == [["1", "0.25"], ["a,b", "#DIV/0!"]]


# spec: cli X4
def test_print_json(tmp_path):
    result = run_cli("print", sample(tmp_path), "--format", "json")
    assert result.returncode == 0
    data = parse_json(result.stdout)
    assert list(data) == ["A1", "B1", "C1", "AA1", "A2", "B2"]
    assert data["A1"] == 1 and data["B1"] == "hello" and data["A2"] is True
    assert data["C1"] == {"error": "#DIV/0!"}


# spec: cli X5
def test_set(tmp_path):
    path = write_csv(tmp_path / "t.csv", [["1", "=A1*2"]])
    result = run_cli("set", path, "A1", "=3+4")
    assert result.returncode == 0 and result.stdout == "7\n"
    assert run_cli("eval", path, "B1").stdout == "14\n"
    with open(path, newline="", encoding="utf-8") as file:
        assert file.read() == "=3+4,=A1*2\r\n"


# spec: cli X5 (empty content clears the cell)
def test_set_clears(tmp_path):
    path = write_csv(tmp_path / "t.csv", [["1", "2"]])
    assert run_cli("set", path, "B1", "").returncode == 0
    assert run_cli("print", path).stdout == "A1: 1\n"


# spec: cli X6
def test_check(tmp_path):
    result = run_cli("check", sample(tmp_path))
    assert result.returncode == 1
    assert result.stdout == "C1: #DIV/0!\n"
    clean = write_csv(tmp_path / "ok.csv", [["1", "=A1+1"]])
    result = run_cli("check", clean)
    assert result.returncode == 0 and result.stdout == ""


# spec: cli X1 (every command reads FILE with csvio.load: quoted fields)
def test_quoted_fields(tmp_path):
    path = write_csv(tmp_path / "q.csv", [["a,b", "=1/0"]])
    assert run_cli("print", path).stdout == "A1: a,b\nB1: #DIV/0!\n"
    assert run_cli("check", path).stdout == "B1: #DIV/0!\n"


# spec: cli X7
def test_errors(tmp_path):
    path = write_csv(tmp_path / "t.csv", [["1"]])
    for args in (("print", str(tmp_path / "missing.csv")), ("check", str(tmp_path / "missing.csv")),
                 ("set", path, "1A", "2"), ("eval", path, "A0")):
        result = run_cli(*args)
        assert result.returncode == 2, args
        assert result.stderr.startswith("cells: "), args
