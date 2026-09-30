#!/usr/bin/env python3
"""Checks every ```rust block in the skill's Markdown files.

Each block becomes src/lib.rs of a scratch library crate named `my_crate`
(edition 2024, with serde and thiserror available), and must pass
`cargo clippy --all-targets -- -D warnings`, `cargo test` (unit tests and
doctests), and `rustfmt --check`. The first line of a block changes that:

- `// Does not compile` -> `cargo check` must fail, with each error code
  (such as `E0515`) that the line names.
- `// In <path>:` -> a file of another target; skipped.

Usage (from anywhere; needs cargo, clippy, rustfmt, and the two crates in
the local registry or network access):

    python3 skills/robust-rust/evals/check_examples.py            # all files
    python3 skills/robust-rust/evals/check_examples.py FILE.md    # one file
    python3 skills/robust-rust/evals/check_examples.py --fix-fmt  # rewrite blocks with rustfmt
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CARGO_TOML = """[package]
name = "my_crate"
version = "0.1.0"
edition = "2024"

[dependencies]
serde = { version = "1", features = ["derive"] }
thiserror = "2"

[dev-dependencies]
serde_json = "1"
"""


def blocks(path):
    """Yields (line number, code, (start, end) line span) for each rust block."""
    lines = path.read_text().splitlines()
    i = 0
    while i < len(lines):
        if re.match(r"^```rust\s*$", lines[i]):
            start = i + 1
            end = start
            while not lines[end].startswith("```"):
                end += 1
            yield start + 1, "\n".join(lines[start:end]) + "\n", (start, end)
            i = end + 1
        else:
            i += 1


def run(crate, cmd):
    return subprocess.run(cmd, cwd=crate, capture_output=True, text=True)


def check_block(crate, code, fix_fmt):
    """Returns (problems, formatted code or None)."""
    lib = crate / "src" / "lib.rs"
    lib.write_text(code)
    first = code.lstrip().splitlines()[0] if code.strip() else ""
    if first.lower().startswith("// does not compile"):
        result = run(crate, ["cargo", "check", "-q"])
        if result.returncode == 0:
            return ["expected a compile error, but the block compiled"], None
        missing = [
            code
            for code in re.findall(r"\bE\d{4}\b", first)
            if f"error[{code}]" not in result.stderr
        ]
        if missing:
            return [f"expected {', '.join(missing)}, got:\n" + result.stderr[-3000:]], None
        return [], None
    problems = []
    result = run(crate, ["cargo", "clippy", "-q", "--all-targets", "--", "-D", "warnings"])
    if result.returncode != 0:
        problems.append("clippy:\n" + result.stderr[-3000:])
    else:
        result = run(crate, ["cargo", "test", "-q"])
        if result.returncode != 0:
            problems.append("test:\n" + (result.stdout + result.stderr)[-3000:])
    fmt = run(crate, ["rustfmt", "--check", "--edition", "2024", str(lib)])
    if fmt.returncode == 0:
        return problems, None
    if fix_fmt:
        run(crate, ["rustfmt", "--edition", "2024", str(lib)])
        return problems, lib.read_text()
    return problems + ["rustfmt:\n" + fmt.stdout[-3000:]], None


def main(argv):
    fix_fmt = "--fix-fmt" in argv
    files = [Path(a) for a in argv if a.endswith(".md")]
    if not files:
        files = [SKILL_DIR / "SKILL.md", *sorted((SKILL_DIR / "references").glob("*.md"))]
    failures = total = 0
    with tempfile.TemporaryDirectory() as tmp:
        crate = Path(tmp)
        (crate / "src").mkdir()
        (crate / "Cargo.toml").write_text(CARGO_TOML)
        for path in files:
            rewrites = []
            for line, code, span in blocks(path):
                label = f"{path.name}:{line}"
                first = code.lstrip().splitlines()[0] if code.strip() else ""
                if re.match(r"// In \S+:", first):
                    print(f"skip  {label}")
                    continue
                total += 1
                problems, formatted = check_block(crate, code, fix_fmt)
                if formatted is not None:
                    rewrites.append((span, formatted))
                    print(f"fmt   {label}: rewrote the block with rustfmt")
                if problems:
                    failures += 1
                    print(f"FAIL  {label}")
                    for problem in problems:
                        print("      " + problem.replace("\n", "\n      "))
                else:
                    print(f"ok    {label}")
            if rewrites:
                lines = path.read_text().splitlines()
                for (start, end), new in sorted(rewrites, reverse=True):
                    lines[start:end] = new.rstrip("\n").splitlines()
                path.write_text("\n".join(lines) + "\n")
    print(f"\n{total - failures}/{total} blocks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
