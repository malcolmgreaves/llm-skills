#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "pytest>=8"]
# ///
"""Tests for validate.py. Run: uv run scripts/test_validate.py"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import validate  # noqa: E402

PATH = Path("SKILL.md")

# (line, text, language, inline) for each piece of code, in document order.
CodeRow = tuple[int, str, str, bool]


@pytest.mark.parametrize(
    ("markdown", "first_line", "prose_words", "code"),
    [
        pytest.param("text [a](b.md)\n", 1, ["text", "[a](b.md)"], [], id="no code"),
        pytest.param(
            "see `f[T](x)` here\n", 1, ["see", "here"], [(1, "f[T](x)", "", True)], id="inline span"
        ),
        pytest.param(
            "a ``x ` y`` b\n", 1, ["a", "b"], [(1, "x ` y", "", True)], id="double backticks"
        ),
        pytest.param(
            "a `b\nc` d\n", 1, ["a", "d"], [(1, "b\nc", "", True)], id="span wraps a line"
        ),
        pytest.param(
            "a `b\n\nc` d\n", 1, ["a", "`b", "c`", "d"], [], id="span can't cross a blank line"
        ),
        pytest.param(
            "x\n```python\ndef f[T](a: T) -> T: ...\n```\ny\n",
            1,
            ["x", "y"],
            [(3, "def f[T](a: T) -> T: ...\n", "python", False)],
            id="fenced block with language",
        ),
        pytest.param(
            "~~~py title\ncode\n~~~\n", 1, [], [(2, "code\n", "py", False)], id="tilde fence"
        ),
        pytest.param(
            "   ```\nc\n   ```\n", 1, [], [(2, "c\n", "", False)], id="indented fence"
        ),
        pytest.param(
            "````md\n```\ninner\n```\n````\nafter\n",
            1,
            ["after"],
            [(2, "```\ninner\n```\n", "md", False)],
            id="longer fence holds a shorter one",
        ),
        pytest.param(
            "```\nopen `x`\nstill code\n",
            1,
            [],
            [(2, "open `x`\nstill code\n", "", False)],
            id="unclosed fence runs to the end",
        ),
        pytest.param(
            "```a``` b\n", 1, ["b"], [(1, "a", "", True)], id="backticks with text are inline"
        ),
        pytest.param(
            "prose\n`x`\n", 10, ["prose"], [(11, "x", "", True)], id="offset by first line"
        ),
    ],
)
def test_split_code(
    markdown: str, first_line: int, prose_words: list[str], code: list[CodeRow]
) -> None:
    prose, found = validate.split_code(markdown, PATH, first_line=first_line)
    assert prose.split() == prose_words
    assert [(c.line, c.text, c.language, c.inline) for c in found] == code
    assert all(c.path == PATH for c in found)
    # Blanking keeps every line break, so line numbers in prose still match.
    assert len(prose) == len(markdown)
    assert [i for i, ch in enumerate(prose) if ch == "\n"] == [
        i for i, ch in enumerate(markdown) if ch == "\n"
    ]


def write_skill(root: Path, body: str) -> Path:
    directory = root / "demo"
    directory.mkdir()
    (directory / "SKILL.md").write_text(
        f"---\nname: demo\ndescription: Does a demo. Use when testing.\n---\n{body}",
        encoding="utf-8",
    )
    (directory / "README.md").write_text("# demo\n", encoding="utf-8")
    return directory


@pytest.mark.parametrize(
    ("body", "errors"),
    [
        pytest.param(
            "Write `def f[T](x: T) -> T`.\n\n```python\nclass C[T](Base): ...\n```\n",
            [],
            id="python generics are not links",
        ),
        pytest.param("`[a](missing.md)`\n", [], id="link inside code is ignored"),
        pytest.param(
            "[a](missing.md)\n",
            ["SKILL.md links to `missing.md`, which does not exist"],
            id="broken link in prose",
        ),
    ],
)
def test_links_ignore_code(tmp_path: Path, body: str, errors: list[str]) -> None:
    assert validate.validate_skill(write_skill(tmp_path, body)).errors == errors


def test_check_code_receives_code_from_skill_and_references(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = write_skill(tmp_path, "Run `a`.\n")
    (directory / "references").mkdir()
    (directory / "references" / "more.md").write_text("# More\n\n```sh\nb\n```\n")
    received: list[validate.Code] = []
    monkeypatch.setattr(validate, "check_code", lambda code, report: received.extend(code))

    validate.validate_skill(directory)

    assert [(c.path.name, c.line, c.text, c.language) for c in received] == [
        ("SKILL.md", 5, "a", ""),
        ("more.md", 4, "b\n", "sh"),
    ]


SHELL_BLOCK = "# shared: demo/setup\necho setup\n# /shared\n"
MARKDOWN_BLOCK = "<!-- shared: demo/text -->\nSame text.\n<!-- /shared -->\n"


@pytest.mark.parametrize(
    ("files", "errors", "warnings"),
    [
        pytest.param(
            {"a/fixture.sh": SHELL_BLOCK, "b/fixture.sh": SHELL_BLOCK},
            [],
            [],
            id="matching shell copies",
        ),
        pytest.param(
            {"a/fixture.sh": SHELL_BLOCK, "b/fixture.sh": SHELL_BLOCK.replace("echo setup", "echo other")},
            ["differs"],
            [],
            id="differing shell copies",
        ),
        pytest.param(
            {"a/fixture.sh": "# shared: demo/setup\necho setup\n"},
            ["is never closed"],
            [],
            id="unclosed shell block",
        ),
        pytest.param(
            {"a/fixture.sh": SHELL_BLOCK, "a/SKILL.md": MARKDOWN_BLOCK},
            [],
            ["only one copy", "only one copy"],
            id="one copy of each kind",
        ),
        pytest.param(
            {"a/notes.md": "# shared: demo/setup\n", "a/run.sh": "<!-- shared: demo/text -->\n"},
            [],
            [],
            id="markers of the other file kind are ignored",
        ),
    ],
)
def test_shared_blocks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    files: dict[str, str],
    errors: list[str],
    warnings: list[str],
) -> None:
    monkeypatch.setattr(validate, "REPO_ROOT", tmp_path)
    skill = tmp_path / "skills" / "demo"
    for relative, text in files.items():
        (skill / relative).parent.mkdir(parents=True, exist_ok=True)
        (skill / relative).write_text(text, encoding="utf-8")

    report = validate.validate_shared_blocks([skill])

    assert len(report.errors) == len(errors)
    assert all(e in message for e, message in zip(errors, report.errors))
    assert len(report.warnings) == len(warnings)
    assert all(w in message for w, message in zip(warnings, report.warnings))


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q", "-p", "no:cacheprovider"]))
