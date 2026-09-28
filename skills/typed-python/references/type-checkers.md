# Type checkers

A comparison of the Python type checkers, the strictest practical
configuration for each maintained one, the ignore-comment syntax that each
one honors, and how to find and run the one that a project uses. Checked on
2026-09-25 by running each tool, at the version named in its section, on a
sample file with known problems.

## Contents

- [Compare the checkers](#compare-the-checkers)
- [Recommend a strict configuration](#recommend-a-strict-configuration)
- [mypy](#mypy)
- [pyright](#pyright)
- [basedpyright](#basedpyright)
- [pyrefly](#pyrefly)
- [ty](#ty)
- [zuban](#zuban)
- [pytype and Pyre](#pytype-and-pyre)
- [Ignore comments](#ignore-comments)
- [Find and run the project's checker](#find-and-run-the-projects-checker)
- [Sources](#sources)

## Compare the checkers

Use this section when the user asks which checker to use. Otherwise, keep
the checker that the project already runs.

| Checker | Maintainer | Written in | Status on 2026-09-25 | Speed | Conformance | Strict mode |
| --- | --- | --- | --- | --- | --- | --- |
| [mypy](https://www.mypy-lang.org/) | The mypy team (`python/mypy`) | Python, compiled with mypyc | Active, stable. 2.3.1 | 5.7 s | 109 / 146 | `strict = true`, plus settings |
| [pyright](https://microsoft.github.io/pyright/) | Microsoft | TypeScript, on Node.js | Active, stable. 1.1.414 | 11.3 s | 135.5 / 146 | `typeCheckingMode = "strict"`, plus 3 rules |
| [basedpyright](https://docs.basedpyright.com/) | DetachHead and contributors; a fork of pyright | TypeScript; the PyPI package includes Node.js | Active. 1.40.1 | 12.1 s | Not in the suite; uses pyright's type evaluator | `typeCheckingMode = "recommended"`, the default |
| [pyrefly](https://pyrefly.org/) | Meta | Rust | Active, stable since 1.0.0 (2026-05-12). 1.3.1 | 0.69 s | 141 / 146 | `preset = "strict"`, plus settings |
| [ty](https://docs.astral.sh/ty/) | Astral | Rust | Beta. 0.0.84 | 0.73 s | 139.5 / 146 | No preset; a list of rules |
| [zuban](https://zubanls.com/) | David Halter | Rust | Active, before 1.0. 0.10.0 | 0.79 s | 146 / 146 | `strict = true`, with mypy's option names |
| [pytype](https://google.github.io/pytype/) | Google | Python | Archived. Last release 2024.10.11 | 40 s on a 27,000-line project | Removed from the suite in 2025 | Separate opt-in flags |
| [Pyre](https://pyre-check.org/) | Meta | OCaml | Archived 2026-06-26; replaced by pyrefly | 1.9 s on a 27,000-line project | Removed from the suite in 2025 | `"strict": true` |

- **Speed** is one cold run on the mypy 2.3.1 source (about 129,000 lines)
  on an Apple M1 Max, with each tool's default settings. It's a single
  measurement, not a benchmark. The ty, pyrefly, and zuban projects claim
  10 to 200 times the speed of mypy; those claims weren't measured.
- **Conformance** is the score on the
  [typing conformance suite](https://github.com/python/typing/tree/main/conformance)
  (146 tests; a pass counts 1 and a partial pass 0.5), for the version in
  the suite's results, which can trail the latest release. It measures
  agreement with the typing specification, not how many optional strict
  checks a checker offers.

What each checker reported on the sample file with its strict
configuration:

| Problem | mypy | pyright | basedpyright | pyrefly | ty | zuban |
| --- | --- | --- | --- | --- | --- | --- |
| Function with no annotations | Yes | Yes | Yes | Yes | No; ruff `ANN` does | Yes |
| Missing return annotation that the checker can infer | Yes | No | No | Yes | No; ruff `ANN` does | Yes |
| `Any` written in an annotation | Stricter option | No | Yes | Stricter option | No; ruff `ANN401` does | Stricter option |
| `# type: ignore` without a code | Yes | No | Yes | No | No; ruff `PGH003` does | No |
| Unused ignore comment in its own syntax | Yes | Yes | Yes | Yes | Yes | No |
| Code that can't run | Yes | Yes | Yes | No; reports a false missing `return` | No | Yes |
| Override without `@override` | Yes | Yes | Yes | Yes | Yes | Yes |
| Coroutine that is never awaited | Yes | Yes | Yes | Yes | Yes | Yes |
| Typed function that returns an untyped call's result | Yes | No | No | Yes | Yes | Yes |
| Discarded return value | No | Stricter option | Yes | Stricter option | No | No |

### mypy

- **Pros**: the most users (about 151 million downloads a month). A plugin
  API: the django-stubs plugin and pydantic's plugin run only under mypy.
  The widest set of optional checks; with the strict configuration it
  reported 11 of the sample's 13 problems, the most of any checker. zuban
  and `pyrefly init` read its configuration.
- **Cons**: the lowest conformance score of the maintained checkers. Slower
  than the Rust checkers; mypy 2.0 added parallel checking (`-n N`), which
  wasn't measured. No language server. Without `check_untyped_defs`, which
  `strict` turns on, it skips the bodies of unannotated functions.

### pyright

- **Pros**: mature, and the engine of Microsoft's Pylance extension. A
  language server is included. It checks unannotated functions and infers
  their return types. Strict mode's `reportUnknown*` rules track `Any` that
  comes from untyped code.
- **Cons**: needs Node.js (the PyPI package `pyright` downloads it). No
  plugins, by design. It can't require a rule name on an ignore comment,
  has no rule for an explicit `Any`, and doesn't require a return
  annotation that it can infer. Because it infers types at each call site,
  it doesn't report a typed function that returns an untyped call's result.

### basedpyright

- **Pros**: everything pyright does, plus rules that pyright lacks
  (`reportAny`, `reportExplicitAny`, `reportIgnoreCommentWithoutRule`,
  `reportUnusedParameter`, and others). Every rule is on by default.
  Baseline files let a project adopt strict rules on existing code. It
  finds `.venv` without configuration, and its PyPI package includes
  Node.js.
- **Cons**: a small team that follows upstream pyright. The default mode
  reports many warnings on existing code, including `reportAny` for every
  value from an untyped library. `# type: ignore` is off by default, so
  ignore comments written for mypy do nothing. It shares
  `pyrightconfig.json` with pyright, so that file doesn't show which of the
  two a project runs.

### pyrefly

- **Pros**: among the fastest measured, and conformance second only to
  zuban. Built-in support for Django, Pydantic, attrs, and pytest fixtures,
  with no plugins. A language server. `pyrefly init` converts a mypy or
  pyright configuration, and it can require return annotations.
- **Cons**: with no configuration it uses a preset that checks very little,
  and it hides warnings by default. It can't require a code on an ignore
  comment, and a `# type: ignore` with another checker's code suppresses
  every pyrefly error on the line. In 1.3.1 it reports code after a
  `return` as a missing `return`, and its documentation lists an error kind
  that 1.3.1 rejects.

### ty

- **Pros**: among the fastest measured, with high conformance. It always
  checks the bodies of unannotated functions. A language server. It reports
  unused ignore comments by default and fails the run on warnings.
- **Cons**: in beta, so diagnostics can change between any two releases.
  No rules for a missing annotation, an explicit `Any`, or code after a
  `return`; it needs ruff's `ANN` rules alongside. No plugins, and no plan
  for them. It ignores `# type: ignore[code]` comments whose code has no
  `ty:` prefix. Astral announced on 2026-03-19 that it will join OpenAI.

### zuban

- **Pros**: 146 of 146 on the conformance suite. A mode that imitates mypy,
  reads mypy's configuration, and uses mypy's error codes. Fast, with a
  language server.
- **Cons**: licensed under AGPL-3.0, which some organizations don't allow;
  a commercial license is available. One main developer and a small user
  base. It doesn't report unused ignore comments or enforce
  `ignore-without-code`, and an unknown configuration key stops it with
  exit code 101.

### pytype and Pyre

Both are archived; don't adopt either one. pytype supports Python 3.12 at
most, and its FAQ suggests mypy, pyright, pyrefly, or ty instead. Pyre's
README names pyrefly as its replacement; the `pyre-check` package now ships
Pysa, a security analyzer, which depends on pyrefly.

### Other checkers

| Checker | Status on 2026-09-25 | Notes |
| --- | --- | --- |
| [pycroscope](https://github.com/JelleZijlstra/pycroscope) | Active. 0.5.0 | 138.5 / 146 on the conformance suite. It imports the modules that it checks, which runs their top-level code. Its strict settings weren't researched. |
| [pyanalyze](https://github.com/quora/pyanalyze) | Inactive; last release 2024-08-07 | pycroscope is its fork. |
| [basedmypy](https://github.com/KotlinIsland/basedmypy) | Deprecated in July 2025 | Its README recommends basedpyright or ty. |
| [pylyzer](https://github.com/mtshiba/pylyzer) | Bug fixes only; last release 2025-02-25 | |
| Pylance | Closed-source VS Code extension, built on pyright | Not a command-line checker. Run pyright or basedpyright in CI. |

## Recommend a strict configuration

Recommend the strict configuration for the project's checker when the user
sets up a checker, asks for stricter checking, or when the project runs its
checker without these settings. On existing code a strict configuration can
report hundreds of errors, so apply it only if the user agrees. Set the
Python version in each configuration to the project's minimum supported
version.

Each section gives a **strict** configuration, which is the one to
recommend, and **stricter options**, which catch more but report many
findings that aren't bugs. Offer the stricter options only if the user asks
for the strictest possible settings, and say what each one costs.

pyright, basedpyright, and ty don't report a missing return annotation
when they can infer the return type. Of those three, only basedpyright
reports an explicit `Any`. With those checkers, ruff's `ANN` rules enforce
the rule in `SKILL.md` that every public name has an annotation. The strict
ruff configuration includes them.

## mypy

Checked with mypy 2.3.1. `strict = true` turns on a bundle of flags that
changes between releases. In 2.3.1 it doesn't include `warn_unreachable`,
`warn_unused_configs` (removed from the bundle in 1.20), or the optional
error codes below. mypy 2.0 made `strict_bytes` and `local_partial_types`
the default, so they no longer need settings.

Strict:

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_unreachable = true           # Code that type analysis shows can't run.
strict_equality_for_none = true   # Comparisons with None that are never true.
disallow_any_unimported = true    # Types that became Any because an import failed.
warn_unused_configs = true        # Per-module sections that match no file.
enable_error_code = [
    "deprecated",           # Uses of APIs marked @deprecated.
    "exhaustive-match",     # A match statement that misses a case.
    "explicit-override",    # An override without @override.
    "ignore-without-code",  # A `# type: ignore` without an error code.
    "mutable-override",     # An unsafe override of a mutable attribute.
    "possibly-undefined",   # A variable defined on only some paths.
    "redundant-expr",       # An expression whose value is fixed.
    "redundant-self",       # A redundant Self annotation.
    "truthy-bool",          # An object in a boolean context that is always true.
    "truthy-iterable",      # An Iterable in a boolean context; it's true when empty.
    "unimported-reveal",    # reveal_type without an import.
    "unused-awaitable",     # An awaitable that is created and not used.
]
```

In `mypy.ini`, `.mypy.ini`, or `setup.cfg`, put the same keys under
`[mypy]`, with `True` for `true` and the error codes as one comma-separated
value. If mypy runs in its own tool environment (`uvx`, `pipx`, or a
pre-commit hook), add `python_executable = ".venv/bin/python"` so that it
finds the project's installed packages.

Stricter options:

| Setting | What it reports | Cost |
| --- | --- | --- |
| `disallow_any_explicit = true` | `Any` written anywhere in a type | JSON values and `**kwargs` boundaries need `object` and narrowing, or an ignore comment. |
| `disallow_any_expr = true` | Every expression whose type is `Any` | Every value from an untyped library. |
| `disallow_any_decorated = true` | A function whose signature has `Any` after decoration | Many third-party decorators are typed with `Any`. |

## pyright

Checked with pyright 1.1.414. `strict` mode leaves `reportImplicitOverride`,
`reportUnnecessaryTypeIgnoreComment`, and `reportUnreachable` off, so turn
them on.

Strict:

```toml
[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"
deprecateTypingAliases = true                  # typing.List and similar are deprecated.
reportImplicitOverride = "error"               # An override without @override.
reportUnnecessaryTypeIgnoreComment = "error"   # An ignore comment that suppresses nothing.
reportUnreachable = "error"                    # Code that can't run.
```

In `pyrightconfig.json`, use the same keys and values as JSON. That file
takes precedence over `pyproject.toml` when both exist. `reportShadowedImports`
was removed in 1.1.406; delete it from an existing configuration.

Stricter options:

| Setting | What it reports | Cost |
| --- | --- | --- |
| `enableTypeIgnoreComments = false` | Makes only `# pyright: ignore[rule]` work | Breaks `# type: ignore` comments shared with another checker. |
| `reportUnusedCallResult = "error"` | A discarded non-`None` result | `list.pop()`, `dict.setdefault()`, `subprocess.run()`. |
| `reportUninitializedInstanceVariable = "error"` | An attribute not assigned in the class body or `__init__` | `__init__` that delegates to a helper method. |
| `reportMissingSuperCall = "error"` | `__init__` and similar methods that don't call the base method | Classes whose base is `object`, and mixins. |
| `reportImportCycles = "error"` | Cyclic imports | Fixing a cycle means restructuring modules. |
| `reportCallInDefaultInitializer = "error"` | A call in a parameter default | Harmless defaults such as `frozenset()`. |
| `reportImplicitStringConcatenation = "error"` | Adjacent string literals | Formatters split long strings this way. |
| `reportPropertyTypeMismatch = "error"` | A setter whose type differs from the getter's | The typing spec allows it. |

## basedpyright

Checked with basedpyright 1.40.1, which is based on pyright 1.1.414. Its
default mode, `recommended`, turns on every rule, including the rules it
adds to pyright: `reportAny`, `reportExplicitAny`, and
`reportIgnoreCommentWithoutRule`.

Strict:

```toml
[tool.basedpyright]
pythonVersion = "3.12"
typeCheckingMode = "recommended"   # Every rule on; the default.
failOnWarnings = true              # Warnings fail the run; set so a mode change keeps it.
enableTypeIgnoreComments = false   # Only `# pyright: ignore[rule]` works; the default.
```

basedpyright also reads `[tool.pyright]` and `pyrightconfig.json`. On
existing code, `reportAny` reports every value from an untyped library; the
`allowedUntypedLibraries` setting turns the unknown-type rules off for the
listed modules only, and a baseline file (`basedpyright --writebaseline`)
records the existing findings so that only new ones fail.

Stricter option: `typeCheckingMode = "all"` reports every rule as an error
instead of a warning and adds `reportIncompatibleUnannotatedOverride`. With
`failOnWarnings = true`, the pass or fail result is otherwise the same.

## pyrefly

Checked with pyrefly 1.3.1. Without a `pyrefly.toml` or `[tool.pyrefly]`
section, and with no mypy or pyright configuration to convert, pyrefly uses
its `basic` preset, which checks very little. It also hides warnings unless
`min-severity = "warn"` is set.

Strict:

```toml
[tool.pyrefly]
python-version = "3.12"
preset = "strict"
check-unannotated-defs = true   # Check the bodies of unannotated functions.
min-severity = "warn"           # Show warnings, and fail the run on them.

[tool.pyrefly.errors]
empty-body = "error"                  # A body of only `...` whose return type excludes None.
implicit-reexport = "error"           # Importing a name that a module didn't re-export.
incompatible-comparison = "error"     # `==` between incompatible built-in types.
invalid-cast = "error"                # cast() between types that can't overlap.
no-any-return = "error"               # Returning Any from a function with a precise return type.
not-required-key-access = "error"     # Reading a NotRequired TypedDict key without a check.
unannotated-return = "error"          # A function without a return annotation.
unknown-argument-type = "error"       # Passing an implicit-Any value as an argument.
unknown-attribute-type = "error"      # An attribute inferred as Any.
unknown-variable-type = "error"       # A variable inferred as Any.
untyped-class-decorator = "error"     # A class decorator typed as Any.
untyped-function-decorator = "error"  # A function decorator typed as Any.
unused-type-ignore = "error"          # A `# type: ignore` that suppresses nothing.
```

In `pyrefly.toml`, drop the `tool.pyrefly` prefix: the top-level keys go at
the top of the file and the error kinds under `[errors]`. If another checker
shares the project's `# type: ignore` comments, set `unused-type-ignore` to
`"ignore"`.

pyrefly 1.3.1 reports code after a `return` as a missing `return`
(`bad-return`) instead of as unreachable code. Its documentation lists
`uninitialized-instance-variable`, but 1.3.1 rejects that name as a fatal
configuration error, so don't add it.

Stricter options (under `[tool.pyrefly.errors]`, set to `"error"`):
`explicit-any` (reports `Any` at JSON and `**kwargs` boundaries),
`unused-call-result` (discarded results, as in pyright), `implicit-bool`
(idiomatic truthiness tests), `missing-super-call`, `implicit-abstract-class`,
and `implicitly-defined-attribute`. `preset = "all"` turns on every kind;
pyrefly's documentation recommends `strict` plus selected kinds instead.

## ty

Checked with ty 0.0.84. ty is in beta: a 0.0.x release can change its
diagnostics, so pin its version. It has no rule for a missing annotation, an
explicit `Any`, or code after a `return`; pair it with the strict ruff
configuration, which covers annotations with the `ANN` rules. It exits with
code 1 on warnings.

Strict (the configuration from ty's "Coming from mypy or pyright" guide,
plus the ignore-comment and override rules):

```toml
[tool.ty.environment]
python-version = "3.12"

[tool.ty.rules]
blanket-ignore-comment = "error"             # A `# ty: ignore` without a rule name.
dynamic-function-decorator-return = "error"  # A decorator that replaces a function with Any.
missing-override-decorator = "error"         # An override without @override.
missing-type-argument = "error"              # A generic type without type arguments.
possibly-unresolved-reference = "warn"       # A name that may be undefined on some paths.
unsound-return-statement = "error"           # Returning Any from a function with a precise return type.
unused-ignore-comment = "error"              # A `# ty: ignore` that suppresses nothing.
unused-type-ignore-comment = "error"         # A `# type: ignore` that suppresses nothing.

[tool.ty.terminal]
error-on-warning = true
```

In `ty.toml`, drop the `tool.ty.` prefix from each table name.

Stricter options: `unsound-assignment` and `unsound-yield` (every untyped
value assigned to an annotated variable), `redundant-condition-strict`,
`possibly-missing-attribute`, `possibly-missing-import`, and
`division-by-zero`. ty's documentation says the last four have a high rate
of false positives. `all = "error"` under `[tool.ty.rules]` turns on every
rule, which ty's documentation advises against.

## zuban

Checked with zuban 0.10.0. zuban uses mypy's option names and also reads
mypy's configuration. Its default mode turns on `allow_redefinition` and
`allow_untyped_globals`, so set them to `false`.

Strict: the mypy configuration above, under `[tool.zuban]`, with these keys
added:

```toml
[tool.zuban]
mode = "default"               # zuban's own mode; "mypy" imitates mypy.
allow_redefinition = false     # Don't allow rebinding a name to another type.
allow_untyped_globals = false  # Require an annotation on a global whose type can't be inferred.
```

zuban 0.10.0 accepts `ignore-without-code` but doesn't enforce it, and it
doesn't report unused ignore comments; ruff's `PGH003` requires a code on
each `# type: ignore` instead. An unknown key in its configuration stops it
with exit code 101. zuban is licensed under AGPL-3.0.

## pytype and Pyre

Both are archived. pytype's last release is 2024.10.11, and it supports
Python 3.12 at most. Pyre was archived on 2026-06-26, and its README names
pyrefly as its replacement. If a project uses either one, recommend moving
to a maintained checker instead of making the old one stricter: for Pyre,
`pyrefly init` converts the configuration.

## Ignore comments

Write a workaround in the syntax of the checker that the project runs. A
mypy-style `# type: ignore[code]` means something different in each
checker:

| Checker | Its own syntax | Effect of `# type: ignore[return-value]` | Requires a code | Reports unused |
| --- | --- | --- | --- | --- |
| mypy | `# type: ignore[code]` | Suppresses only `return-value` | `ignore-without-code` | `warn_unused_ignores` (in `strict`) |
| pyright | `# pyright: ignore[rule]` | Suppresses every error on the line | Not available | `reportUnnecessaryTypeIgnoreComment` |
| basedpyright | `# pyright: ignore[rule]` | Nothing: `# type: ignore` is off by default | `reportIgnoreCommentWithoutRule` | `reportUnnecessaryTypeIgnoreComment` |
| pyrefly | `# pyrefly: ignore[kind]`, or `# type: ignore[pyrefly:kind]` | Suppresses every error on the line | Not available | `unused-ignore`, `unused-type-ignore` |
| ty | `# ty: ignore[rule]`, or `# type: ignore[ty:rule]` | Nothing: ty ignores codes without `ty:` | `blanket-ignore-comment` (for `ty: ignore` only) | `unused-ignore-comment`, `unused-type-ignore-comment` |
| zuban | `# type: ignore[code]`, `# zuban: ignore[code]` | Suppresses only `return-value` | Not enforced | Not available |

For every checker, ruff's `PGH003` reports a `# type: ignore` without a code.
When a project runs two checkers, use each checker's own syntax on the line,
so that each comment suppresses only the error it names.

## Find and run the project's checker

A configuration file shows which checker a project uses, but not always
conclusively: pyright and basedpyright share `pyrightconfig.json`, and
pyrefly and zuban read mypy's configuration. Also check the development
dependencies in `pyproject.toml` and the lock file, `.pre-commit-config.yaml`
(for example, a `mirrors-mypy` hook), CI workflows, and task runners
(`Makefile`, `justfile`, `tox.ini`, `noxfile.py`).

| Configuration | Checker |
| --- | --- |
| `mypy.ini`, `.mypy.ini`, `[tool.mypy]` in `pyproject.toml`, `[mypy]` in `setup.cfg` | mypy; zuban in mypy mode also reads them |
| `pyrightconfig.json`, `[tool.pyright]` | pyright; basedpyright also reads them |
| `[tool.basedpyright]` | basedpyright |
| `pyrefly.toml`, `[tool.pyrefly]` | pyrefly |
| `ty.toml`, `[tool.ty]` | ty |
| `[tool.zuban]` | zuban |
| `[tool.pytype]`, `[pytype]` in `setup.cfg`, `pytype.cfg` | pytype |
| `.pyre_configuration` | Pyre |

Run the checker in the project's environment, so that it sees the installed
packages:

| Checker | Command | How it finds the project's packages |
| --- | --- | --- |
| mypy | `uv run mypy .` | The interpreter that runs mypy, or `python_executable` |
| pyright | `uv run pyright` | `venvPath` and `venv`, or else the `python` on `PATH`; `--pythonpath` |
| basedpyright | `uv run basedpyright` | Its configuration, or else `./.venv`, or else the `python` on `PATH`; `--pythonpath` |
| pyrefly | `uv run pyrefly check` | The active environment, its configuration, or a `.venv`, `venv`, or `env` directory; `pyrefly dump-config` shows what it found |
| ty | `uv run ty check` | `VIRTUAL_ENV`, or else `.venv`; `--python` |
| zuban | `uv run zuban check`, or `uv run zmypy` for mypy mode | The active environment; `--python-executable` |

## Sources

- Status, versions, and licenses: each package's page on PyPI
  (`https://pypi.org/project/<name>/`) and pyright on npm.
- Conformance: the results page of the
  [typing conformance suite](https://github.com/python/typing/tree/main/conformance),
  at commit `dc0a8a9`.
- mypy: [configuration](https://mypy.readthedocs.io/en/stable/config_file.html),
  [optional error codes](https://mypy.readthedocs.io/en/stable/error_code_list2.html),
  [changelog](https://github.com/python/mypy/blob/master/CHANGELOG.md).
- pyright: [configuration](https://github.com/microsoft/pyright/blob/main/docs/configuration.md),
  [comments](https://github.com/microsoft/pyright/blob/main/docs/comments.md).
- basedpyright: [configuration](https://docs.basedpyright.com/latest/configuration/config-files/),
  [rules it adds](https://docs.basedpyright.com/latest/benefits-over-pyright/new-diagnostic-rules/).
- pyrefly: [configuration](https://pyrefly.org/en/docs/configuration/),
  [error kinds](https://pyrefly.org/en/docs/error-kinds/),
  [suppressions](https://pyrefly.org/en/docs/error-suppressions/).
- ty: [coming from mypy or pyright](https://docs.astral.sh/ty/coming-from-mypy-or-pyright/),
  [rules](https://docs.astral.sh/ty/reference/rules/),
  [configuration](https://docs.astral.sh/ty/reference/configuration/),
  [suppression](https://docs.astral.sh/ty/suppression/).
- zuban: [usage](https://docs.zubanls.com/en/latest/usage.html),
  [license](https://docs.zubanls.com/en/latest/license.html).
- pytype: [FAQ issue](https://github.com/google/pytype/issues/1925).
  Pyre: its [repository](https://github.com/facebook/pyre-check) README.
