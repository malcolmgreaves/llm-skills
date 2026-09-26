"""BACKLOG.md task `errors`."""

from conftest import is_error, value


# spec: errors E1
def test_unknown_function_is_name_error():
    assert is_error(value("=FOO(1)"), "#NAME?")


# spec: errors E1 (a bare name)
def test_bare_name_is_name_error():
    assert is_error(value("=FOO+1"), "#NAME?")


# spec: errors E2
def test_error_literals():
    assert is_error(value("=#N/A"), "#N/A")
    assert is_error(value("=1+#REF!"), "#REF!")
    assert is_error(value("=#DIV/0!"), "#DIV/0!")
    assert is_error(value("=#NAME?"), "#NAME?")


# spec: errors E2 (constants: a code string or a CellError for each code)
def test_error_constants():
    from cells import CellError, errors

    constants = [getattr(errors, name) for name in dir(errors)]
    codes = {c for c in constants if isinstance(c, str)} | {c.code for c in constants if isinstance(c, CellError)}
    assert {"#DIV/0!", "#VALUE!", "#NAME?", "#N/A", "#REF!", "#CYCLE!", "#ERROR!"} <= codes


# spec: errors E3
def test_na():
    assert is_error(value("=NA()"), "#N/A")


# spec: errors E4
def test_iserror():
    assert value("=ISERROR(1/0)") is True
    assert value("=ISERROR(1)") is False
    assert value("=ISERROR(A1)", A1="=NA()") is True


# spec: G4 (the errors=True option that task errors adds)
def test_errors_option():
    from cells.functions import function

    seen = []

    @function("ERRORPROBE", 1, 2, errors=True)
    def probe(*args):
        seen.extend(args)
        return 1

    assert value("=ERRORPROBE(1/0, 2)") == 1
    assert is_error(seen[0], "#DIV/0!") and seen[1] == 2


# spec: errors E5
def test_iferror():
    assert value("=IFERROR(1/0, 7)") == 7
    assert value("=IFERROR(4, 7)") == 4
    assert value("=IFERROR(1, 1/0)") == 1
    assert is_error(value("=IFERROR(1/0, NA())"), "#N/A")
