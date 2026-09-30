#!/usr/bin/env bash
# Runs the robust-rust eval suite with a Rust toolchain that the agent's
# sandbox can read.
#
# Usage: skills/robust-rust/evals/run.sh [claude plugin eval options]
# Example: skills/robust-rust/evals/run.sh --case database-ids --runs 1
set -euo pipefail

evals_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(dirname "$evals_dir")"
tools="$skill_dir/.eval-tools"

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
  echo "run.sh: this shell can't start the OS sandbox that the eval uses." >&2
  echo "Run this script from a shell outside any sandbox." >&2
  exit 1
fi

sysroot="$(rustc --print sysroot)"
for tool in cargo cargo-clippy cargo-fmt clippy-driver rustc rustdoc rustfmt; do
  if [[ ! -x "$sysroot/bin/$tool" ]]; then
    echo "run.sh: $sysroot/bin/$tool is missing. Install the stable toolchain" >&2
    echo "with the clippy and rustfmt components." >&2
    exit 1
  fi
done

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

# The sandbox can't read the home directory, but in both the with-skill and
# the baseline arm it allows reads from each directory on PATH that is inside
# the home directory, and the agent's session inherits PATH. The sysroot's
# bin directory comes first, so that `cargo` is the real cargo and not the
# rustup proxy in ~/.cargo/bin, which reads ~/.rustup. The sysroot itself is
# on PATH only so that rustc can read the standard library under lib/.
# Each run gets its own HOME, so cargo's default home ($HOME/.cargo) is
# writable, and fixture.sh sets cargo offline in the workspace.
export PATH="$sysroot/bin:$sysroot:$PATH"
# fixture.sh refuses to run without this record, so a case can't start
# without the setup above. The harness doesn't pass run.sh's other
# variables to the scaffold script, so the record is a file.
printf '%s\n' "$sysroot" > "$tools/sysroot"

# The default Haiku judge is unreliable on rubrics with several conditions.
# A --judge-model in the arguments comes later, so it overrides this one.
status=0
claude plugin eval "$skill_dir" --scaffold --judge-model sonnet "$@" \
  --allow-tools Write Edit Bash || status=$?
exit "$status"
