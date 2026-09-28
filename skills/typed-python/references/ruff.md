# Ruff

The strict ruff configuration to recommend, what it leaves out and why, the
rules that enforce the rules in `SKILL.md`, and how to suppress a finding.
Checked against ruff 0.16.9.

## Strict configuration

Recommend this configuration when the user sets up ruff or asks for
stricter linting. On existing code it can report hundreds of findings, so
apply it only if the user agrees.

```toml
[tool.ruff.lint]
select = ["ALL"]
ignore = [
    "COM812",  # Conflicts with the formatter, which manages trailing commas.
    "CPY001",  # Copyright headers are a policy. Delete this line to require them.
]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.per-file-ignores]
"**/test_*.py" = [
    "S101",     # pytest checks results with `assert`.
    "PLR2004",  # A test compares results with literal expected values.
]
```

In `ruff.toml` or `.ruff.toml`, drop the `tool.ruff.` prefix from each table
name: `[lint]`, `[lint.pydocstyle]`, `[lint.per-file-ignores]`.

What each setting does:

- **`select = ["ALL"]`** turns on every stable rule. A new ruff release can
  add rules, so pin ruff's version (in the project's development
  dependencies or `.pre-commit-config.yaml`) and upgrade it on purpose.
- **No `target-version`**: ruff reads the minimum Python version from
  `requires-python` in `pyproject.toml`. Set `target-version` (for example,
  `"py312"`) only if the project has no `requires-python`. The `UP` rules
  use it to decide which newer syntax to require.
- **No `preview`**: preview rules can change or disappear between releases.
- **`convention`** selects which docstring rules apply, and turns off the
  pairs that conflict (`D203` with `D211`, `D212` with `D213`). Use
  `"google"`, `"numpy"`, or `"pep257"` to match the project's docstrings.
  The Google convention expects a summary line in the third person
  ("Returns the total.") and turns off `D401`, which requires the
  imperative mood.
- **`per-file-ignores`** covers test files. If the tests live in a `tests/`
  directory with other file names, add `"tests/**/*.py"` with the same
  rules.

Add these only when they apply to the project:

| Situation | Setting |
| --- | --- |
| The project uses unittest, not pytest | Add `"PT"` to `ignore`. The `PT` rules are for pytest. |
| A module's job is to print to the terminal, such as a command-line entry point | Add `"T201"` for that file in `per-file-ignores`. |
| Scripts or tests live in directories without `__init__.py` on purpose | Add `"INP001"` for those directories in `per-file-ignores`. |
| The project requires a license header | Delete `"CPY001"` from `ignore`, and set `[tool.ruff.lint.flake8-copyright] notice-rgx`. |

## Rules that enforce SKILL.md

These rules check the same things as the rules in `SKILL.md`. A finding from
one of them is almost never a false positive in code that follows the
skill, so fix it:

| Rules | What they report | SKILL.md rule |
| --- | --- | --- |
| `ANN001`, `ANN201`, `ANN202`, `ANN204` | A parameter or return type without an annotation | Annotate every public name |
| `ANN401` | `Any` in an annotation | Never write `Any` to satisfy an annotation |
| `UP006`, `UP007`, `UP035`, `UP040`, `UP045`, `UP046`, `UP047` | Older typing syntax than the target version needs, such as `List[int]`, `Optional[X]`, or `TypeVar` on 3.12 | Syntax by Python version |
| `PGH003` | `# type: ignore` without an error code | Workarounds name the error code |
| `PLW0603` | A `global` statement | Contain mutation |
| `B006`, `B008` | A mutable or computed default argument | Contain mutation |
| `RUF012` | A mutable class attribute without `ClassVar` | Contain mutation |
| `C901`, `PLR0911`, `PLR0912`, `PLR0913`, `PLR0915`, `PLR0917` | A function with too many branches, returns, statements, or arguments | One job per function |
| `FBT001`, `FBT002`, `FBT003` | A boolean positional parameter or argument | Readable over clever: make it keyword-only |
| `PT006`, `PT007`, `PT011` | A parametrize table in the wrong shape, or `pytest.raises` without `match=` | Write table tests |

Some rules ask for a change that looks longer but has a reason. Read the
reason with `ruff rule CODE` before you decide that a fix makes the code
worse:

- `EM101`, `EM102`, and `TRY003` ask you to put an exception message in a
  variable (`msg = f"..."`, then `raise ValueError(msg)`), so that a
  traceback doesn't print the message twice.
- `TRY004` asks for `TypeError`, not `ValueError`, when a check on a value's
  type fails.
- `TC001` to `TC003` move an import that only annotations use into an
  `if TYPE_CHECKING:` block. If a library reads annotations at run time
  (pydantic, or a dataclass-based serializer), list its base classes or
  decorators in `[tool.ruff.lint.flake8-type-checking]`
  (`runtime-evaluated-base-classes`, `runtime-evaluated-decorators`)
  instead of suppressing each finding.

## Suppress a finding

Suppress a finding only when it's a false positive, or when the fix makes
the code worse in a way you can measure: it changes behavior, fails a test,
or slows code that you timed. Then:

- Put `# noqa: CODE` on the line that ruff reports, followed by the reason
  as a second comment: `print(report)  # noqa: T201  # the report is the output`.
  Name several codes with commas: `# noqa: E501, T201`. `E501` doesn't count
  a trailing `noqa` comment toward the line length.
- Don't write a bare `# noqa`: `PGH004` reports it, because it hides every
  rule on the line. Don't write a file-wide `# ruff: noqa` in new code.
- Delete each `noqa` that `RUF100` reports as unused.
- Use `ruff check --add-noqa` only when the user adopts a stricter
  configuration on existing code and asks you to suppress the existing
  findings. It adds a `noqa` to every finding, so never use it on new code.

## Commands

| Command | What it does |
| --- | --- |
| `ruff check FILES` | Reports findings. |
| `ruff check --fix FILES` | Applies the fixes that ruff marks safe. |
| `ruff check --diff FILES` | Shows the safe fixes without applying them. |
| `ruff check --statistics` | Counts the findings for each rule. Use it to size the work before adopting a stricter configuration. |
| `ruff rule CODE` | Explains a rule and why it exists. |
| `ruff format FILES` | Formats the files. It doesn't sort imports. |
| `ruff check --select I --fix FILES` | Sorts imports (`I001`). |
| `ruff format --check FILES` | Reports files that `ruff format` would change, without changing them. |
