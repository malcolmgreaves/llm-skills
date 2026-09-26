"""Hidden acceptance tests for the cells benchmark.

Set CELLS_REPO to the checkout under test. Each test names, in a `spec:` comment,
the README.md section or BACKLOG.md rule that it checks; the tests use only the
interfaces those documents require.
"""

import csv
import io
import json
import os
import signal
import subprocess
import sys

import pytest

REPO = os.environ.get("CELLS_REPO")
if not REPO:
    raise RuntimeError("set CELLS_REPO to the checkout under test")
sys.path.insert(0, REPO)
TIMEOUT = int(os.environ.get("CELLS_TEST_TIMEOUT", "30"))
HIDDEN = os.path.realpath(os.path.dirname(__file__))
_TEST_FILES: dict[str, bool] = {}


class TimeLimitExceeded(BaseException):
    """A test ran out of time. A BaseException, so `except Exception` in the code under test can't swallow it."""


def _in_a_test(frame) -> bool:
    """True while a function of a hidden test file is on the stack, and not while pytest reports."""
    while frame is not None:
        path = frame.f_code.co_filename
        if path not in _TEST_FILES:
            real = os.path.realpath(path)
            _TEST_FILES[path] = os.path.dirname(real) == HIDDEN and os.path.basename(real).startswith("test_")
        if _TEST_FILES[path]:
            return True
        frame = frame.f_back
    return False


@pytest.fixture(autouse=True)
def _time_limit():
    def expire(signum, frame):
        if _in_a_test(frame):
            raise TimeLimitExceeded(f"the test took longer than {TIMEOUT} s")

    previous = signal.signal(signal.SIGALRM, expire)
    # After the first expiry the timer fires every second, in case the code under test catches it anyway.
    signal.setitimer(signal.ITIMER_REAL, TIMEOUT, 1)
    yield
    signal.setitimer(signal.ITIMER_REAL, 0)
    signal.signal(signal.SIGALRM, previous)


def sheet_with(**cells):
    from cells import Sheet

    sheet = Sheet()
    for ref, content in cells.items():
        sheet.set(ref, content)
    return sheet


def value(formula, **cells):
    """The value of a formula in cell ZZ99 of a sheet that also holds `cells`."""
    sheet = sheet_with(**cells)
    sheet.set("ZZ99", formula)
    return sheet.value("ZZ99")


def error(code):
    from cells import CellError

    return CellError(code)


def is_error(result, code):
    from cells import CellError

    return isinstance(result, CellError) and result.code == code


def run_cli(*args, cwd=None):
    env = {**os.environ, "PYTHONPATH": REPO}
    return subprocess.run([sys.executable, "-m", "cells", *args], capture_output=True, text=True,
                          env=env, cwd=cwd, timeout=TIMEOUT)


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as file:
        csv.writer(file).writerows(rows)
    return str(path)


def read_csv_text(text):
    return list(csv.reader(io.StringIO(text)))


def parse_json(text):
    return json.loads(text)
