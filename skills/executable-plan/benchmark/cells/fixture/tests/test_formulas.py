import unittest

from cells import CellError, Sheet


def value(formula: str, **cells: str):
    sheet = Sheet()
    for ref, content in cells.items():
        sheet.set(ref, content)
    sheet.set("Z9", formula)
    return sheet.value("Z9")


class ArithmeticTest(unittest.TestCase):
    def test_operators(self):
        self.assertEqual(value("=1+2*3"), 7)
        self.assertEqual(value("=(1+2)*3"), 9)
        self.assertEqual(value("=7-2"), 5)
        self.assertEqual(value("=9/3"), 3)
        self.assertEqual(value("=2^3"), 8)

    def test_grouping(self):
        self.assertEqual(value("=10-4-3"), 3)
        self.assertEqual(value("=8/4/2"), 1)
        self.assertEqual(value("=2^3^2"), 512)

    def test_unary(self):
        self.assertEqual(value("=-2^2"), -4)
        self.assertEqual(value("=2*-3"), -6)
        self.assertEqual(value("=+4"), 4)

    def test_references(self):
        self.assertEqual(value("=A1*B2", A1="3", B2="4"), 12)
        self.assertEqual(value("=A1+1"), 1)  # empty is 0
        self.assertEqual(value("=A1+1", A1="TRUE"), 2)

    def test_empty_result_is_zero(self):
        self.assertEqual(value("=A1"), 0)


class ErrorTest(unittest.TestCase):
    def test_division_by_zero(self):
        self.assertEqual(value("=1/0"), CellError("#DIV/0!"))
        self.assertEqual(value("=0^-1"), CellError("#DIV/0!"))

    def test_text_in_arithmetic(self):
        self.assertEqual(value("=A1+1", A1="abc"), CellError("#VALUE!"))

    def test_not_a_real_number(self):
        self.assertEqual(value("=(-8)^0.5"), CellError("#VALUE!"))
        self.assertEqual(value("=10^400"), CellError("#VALUE!"))

    def test_first_error_wins(self):
        self.assertEqual(value("=A1+A2", A1="abc", A2="=1/0"), CellError("#VALUE!"))
        self.assertEqual(value("=A2+A1", A1="abc", A2="=1/0"), CellError("#DIV/0!"))

    def test_syntax_error(self):
        self.assertEqual(value("=1+"), CellError("#ERROR!"))
        self.assertEqual(value("=(1"), CellError("#ERROR!"))


class FunctionTest(unittest.TestCase):
    def test_abs(self):
        self.assertEqual(value("=ABS(-3)"), 3)

    def test_round(self):
        self.assertEqual(value("=ROUND(2.4)"), 2)
        self.assertEqual(value("=ROUND(1.234, 2)"), 1.23)
        self.assertEqual(value("=ROUND(1234, -2)"), 1200)

    def test_sqrt(self):
        self.assertEqual(value("=SQRT(9)"), 3)
        self.assertEqual(value("=SQRT(-1)"), CellError("#VALUE!"))

    def test_names_ignore_case(self):
        self.assertEqual(value("=abs(-2)"), 2)

    def test_bad_calls(self):
        self.assertEqual(value("=NOPE(1)"), CellError("#VALUE!"))
        self.assertEqual(value("=ABS(1, 2)"), CellError("#VALUE!"))
        self.assertEqual(value("=ABS(1/0)"), CellError("#DIV/0!"))


if __name__ == "__main__":
    unittest.main()
