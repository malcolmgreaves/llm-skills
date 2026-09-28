#!/usr/bin/env bash
# Runs the typed-python eval suite with one tools environment for every case.
#
# Builds a Python 3.12 virtual environment with mypy, pytest, and ruff for the
# whole run, links each case's workspace .venv to it (in fixture.sh), and
# deletes it when this script exits.
#
# Usage: skills/typed-python/evals/run.sh [claude plugin eval options]
# Example: skills/typed-python/evals/run.sh --case silence-checker --runs 1
set -euo pipefail

evals_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(dirname "$evals_dir")"
# The sandbox that runs the agent's shell commands can't read the home
# directory or any temporary directory, and can write only to the run's own
# directories. In both the with-skill and the baseline arm, the settings that
# the harness writes for each run allow reads from each directory on PATH
# that is inside the home directory (but not from one inside a temporary
# directory). So the environment lives in the plugin's directory, inside the
# repository, and its directory goes on PATH (see below). fixture.sh finds it
# relative to its own path. .gitignore lists it in case a run is killed
# before it can delete it.
tools="$skill_dir/.eval-tools"
tools_packages=(mypy==2.3.1 pytest==9.1.1 ruff==0.16.9)

# Claude Code runs the agent's shell commands in an OS sandbox. That sandbox
# can't start inside another one, such as a sandboxed Claude Code session, so
# every Bash command in the eval would fail. Check before spending anything.
sandbox_works() {
  case "$(uname -s)" in
    Darwin) sandbox-exec -p '(version 1)(allow default)' /usr/bin/true 2> /dev/null ;;
    Linux) bwrap --ro-bind / / --dev /dev /usr/bin/true 2> /dev/null ;;
    *) return 0 ;;
  esac
}
if ! sandbox_works; then
  cat >&2 << 'EOF'
run.sh: this shell can't start the OS sandbox (Seatbelt on macOS, bubblewrap
on Linux) that the eval uses for the agent's shell commands. It is probably
running inside another sandbox, or bubblewrap isn't installed. Every Bash
command in the eval would fail. Run this script from a shell outside the
sandbox.
EOF
  exit 1
fi

if [[ -e "$tools" ]]; then
  echo "run.sh: $tools exists, so another run is using it." >&2
  echo "If no run is in progress, delete it." >&2
  exit 1
fi
mkdir "$tools"
# shellcheck disable=SC2329  # The EXIT trap calls it.
cleanup() { rm -rf "$tools"; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "run.sh: building the tools environment in $tools"
# The interpreter goes inside the environment's directory too, because uv's
# own Pythons live in the home directory. Its directory isn't named `python`,
# so that it can't shadow a `python` command on PATH.
UV_PYTHON_INSTALL_DIR="$tools/interpreter" \
  uv venv --quiet --managed-python --python 3.12 "$tools/venv"
# Compiled bytecode means Python never needs to write into the environment.
uv pip install --quiet --compile-bytecode --python "$tools/venv/bin/python" \
  "${tools_packages[@]}"

# The agent's session inherits PATH. $tools/venv/bin comes first, so `mypy`,
# `pytest`, and `ruff` also work without the .venv/bin/ prefix. $tools is on
# PATH only so that the sandbox lets the agent read all of the environment:
# the interpreter and the installed packages as well as the scripts in bin.
# With only bin on PATH, the baseline arm, which loads no plugin and so can't
# read the plugin's directory, got "Operation not permitted" from mypy.
export PATH="$tools/venv/bin:$tools:$PATH"
# The default Haiku judge is unreliable on rubrics with several conditions,
# such as refactor-global-state's `composed`. A --judge-model in the
# arguments comes later, so it overrides this one.
status=0
claude plugin eval "$skill_dir" --scaffold --judge-model sonnet "$@" \
  --allow-tools Write Edit Bash || status=$?
exit "$status"
