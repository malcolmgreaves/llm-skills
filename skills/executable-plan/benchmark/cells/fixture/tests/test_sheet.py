import os
import subprocess
import sys
import tempfile
import unittest

from cells import CellError, Sheet

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SheetTest(unittest.TestCase):
    def test_content_types(self):
        sheet = Sheet()
        sheet.set("A1", "12")
        sheet.set("A2", "-3.5")
        sheet.set("A3", "true")
        sheet.set("A4", "hello")
        self.assertEqual(sheet.value("A1"), 12)
        self.assertEqual(sheet.value("A2"), -3.5)
        self.assertIs(sheet.value("A3"), True)
        self.assertEqual(sheet.value("A4"), "hello")
        self.assertIsNone(sheet.value("A5"))

    def test_content_is_kept(self):
        sheet = Sheet()
        sheet.set("B2", "=1+1")
        self.assertEqual(sheet.content("B2"), "=1+1")
        sheet.set("B2", "")
        self.assertEqual(sheet.content("B2"), "")
        self.assertIsNone(sheet.value("B2"))

    def test_display(self):
        sheet = Sheet()
        for ref, content in {"A1": "3", "A2": "=1/4", "A3": "FALSE", "A4": "=1/0", "A5": "x"}.items():
            sheet.set(ref, content)
        shown = [sheet.display(ref) for ref in ("A1", "A2", "A3", "A4", "A5", "A6")]
        self.assertEqual(shown, ["3", "0.25", "FALSE", "#DIV/0!", "x", ""])

    def test_values_follow_changes(self):
        sheet = Sheet()
        sheet.set("A1", "1")
        sheet.set("A2", "=A1*10")
        self.assertEqual(sheet.value("A2"), 10)
        sheet.set("A1", "2")
        self.assertEqual(sheet.value("A2"), 20)

    def test_addresses(self):
        sheet = Sheet()
        for ref in ("B2", "A2", "C1"):
            sheet.set(ref, "1")
        self.assertEqual(sheet.addresses(), ["C1", "A2", "B2"])

    def test_bad_address(self):
        with self.assertRaises(ValueError):
            Sheet().set("1A", "1")
        self.assertEqual(CellError("#VALUE!"), CellError("#VALUE!"))


class CliTest(unittest.TestCase):
    def run_cli(self, *args):
        env = {**os.environ, "PYTHONPATH": ROOT}
        return subprocess.run([sys.executable, "-m", "cells", *args], capture_output=True, text=True, env=env)

    def test_eval(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sheet.csv")
            with open(path, "w") as file:
                file.write("1,2\n=A1+B1,\n")
            result = self.run_cli("eval", path, "A2")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "3\n")

    def test_missing_file(self):
        result = self.run_cli("eval", "/nonexistent/sheet.csv", "A1")
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.startswith("cells: "))


if __name__ == "__main__":
    unittest.main()
