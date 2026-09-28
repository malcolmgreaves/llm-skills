#!/usr/bin/env bash
# Seeds this case's workspace with a Python 3.12 project that runs
# `mypy --strict` and pytest through `make check`.
# Case files: users.py, which fails the type check.
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

cat > users.py <<'PY'
from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    name: str
    email: str


USERS: dict[str, User] = {
    "ada": User("ada", "ada@example.com"),
    "grace": User("grace", "grace@example.com"),
}


def find_user(users: dict[str, User], name: str) -> User:
    return users.get(name)


def email_for(name: str) -> str:
    return find_user(USERS, name).email
PY
