"""BACKLOG.md task `ranges`."""

from conftest import is_error, value


# spec: ranges R1, R5
def test_rows_and_columns():
    assert value("=ROWS(A1:B3)") == 3
    assert value("=COLUMNS(A1:B3)") == 2


# spec: ranges R1 (corners in either order), R5 example
def test_corners_in_either_order():
    assert value("=ROWS(B3:A1)") == 3
    assert value("=COLUMNS(B3:A1)") == 2
    assert value("=ROWS(A3:B1)") == 3


# spec: ranges R5 example (COLUMNS(Z1:AB1) is 3) -- also needs the column fix
def test_columns_past_z():
    assert value("=COLUMNS(Z1:AB1)") == 3


# spec: ranges R2
def test_range_outside_a_function_is_value_error():
    assert is_error(value("=A1:B2"), "#VALUE!")
    assert is_error(value("=A1:A2+1"), "#VALUE!")


# spec: ranges R3 (a function not registered for ranges)
def test_range_to_scalar_function():
    assert is_error(value("=ABS(A1:A2)"), "#VALUE!")


# spec: ranges R5 (a single value instead of a range)
def test_rows_of_a_single_value():
    assert is_error(value("=ROWS(5)"), "#VALUE!")
    assert is_error(value("=COLUMNS(A1)"), "#VALUE!")
    assert value("=ROWS(A1:A2)") == 2


# spec: ranges R3, R4 (RangeValue.rows and values(); an error in a range doesn't propagate)
def test_range_value_shape():
    from cells.functions import function
    from cells.ranges import RangeValue

    seen = {}

    @function("RANGEPROBE", 1, 1, ranges=True)
    def probe(arg):
        seen["arg"] = arg
        return 0

    assert value("=RANGEPROBE(B2:A1)", A1="1", B1="x", B2="=1/0") == 0  # the error in the range didn't propagate
    arg = seen["arg"]
    assert isinstance(arg, RangeValue)
    assert arg.rows[0] == [1, "x"]
    assert arg.rows[1][0] is None and is_error(arg.rows[1][1], "#DIV/0!")
    assert arg.values()[:3] == [1, "x", None]
