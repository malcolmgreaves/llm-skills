#!/usr/bin/env bash
# Seeds this case's workspace with a Python 3.12 project that runs
# `mypy --strict` and pytest through `make check`.
# Case files: priorities.py and report.py, its caller.
set -euo pipefail

# shared: typed-python/eval-project
# This block is the same in every case's fixture.sh, and
# scripts/validate.py fails if the copies differ.

# evals/run.sh builds one environment with mypy, pytest, and ruff for the
# whole run, in the plugin's directory, which the agent's sandbox can read
# but not write. The harness runs this script from its place in the
# repository, so the environment's path is relative to it.
venv="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/.eval-tools/venv"
if [[ ! -x "$venv/bin/mypy" ]]; then
  echo "fixture.sh: no tools environment. Run the suite with evals/run.sh." >&2
  exit 1
fi
ln -s "$venv" .venv

cat > pyproject.toml <<'EOF'
[project]
name = "shop"
version = "0.1.0"
requires-python = ">=3.12"

[tool.pytest.ini_options]
addopts = "-q"

[tool.mypy]
strict = true
python_version = "3.12"
exclude = ["^\\.venv/"]
EOF
printf '.PHONY: check typecheck test\ncheck: typecheck test\ntypecheck:\n\t.venv/bin/mypy .\ntest:\n\t.venv/bin/pytest\n' \
  > Makefile
# /shared

cat > priorities.py <<'PY'
from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    priority: int
    assignee: str


@dataclass(frozen=True)
class Ticket:
    priority: int
    customer: str


@dataclass(frozen=True)
class Alert:
    priority: int
    source: str


def highest(items):
    """Returns the item with the largest priority from a non-empty list."""
    raise NotImplementedError
PY

cat > report.py <<'PY'
from priorities import Alert, Task, highest


def next_assignee(tasks: list[Task]) -> str:
    return highest(tasks).assignee


def loudest_source(alerts: list[Alert]) -> str:
    return highest(alerts).source
PY
