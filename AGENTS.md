# AGENTS.md

Instructions for AI agents working in this repository.

This repo is a collection of reusable **Agent Skills**. It contains no application
code — the deliverable is the skill text itself. Treat every change here as
editing a prompt that other agents will execute.

## Repository layout

```
skills/<skill-name>/     one directory per skill
  SKILL.md               required: the skill itself (frontmatter + instructions)
  README.md              required here: human-facing docs (agents never read this)
  scripts/               optional: executable code, run via bash
  references/            optional: docs the agent reads on demand
  assets/                optional: templates, fonts, images used in output
template/                starter files for a new skill — not a loadable skill
scripts/validate.py      spec linter for everything under skills/
```

`skills/` is the only directory a skill loader sees. Do not put anything under it
that is not a real, working skill.

## The one rule that matters

**`SKILL.md` must be self-contained.** An agent loads `SKILL.md` and the files it
explicitly points to — nothing else. It never reads `README.md`. If a fact is
needed to perform the task, it belongs in `SKILL.md` or in a file `SKILL.md`
names by relative path. `README.md` explains the skill to a human deciding
whether to install it; it is documentation, not instruction.

## Writing SKILL.md

Follow the [Agent Skills specification](https://agentskills.io/specification).

### Frontmatter

Use only the six fields in the open spec. Claude Code accepts many more
(`disable-model-invocation`, `context`, `model`, `paths`, `argument-hint`, ...),
but a skill using them **fails to upload to claude.ai** with
`Unexpected key(s) in SKILL.md frontmatter`. Skills here are meant to be
portable, so keep them portable.

| Field | Required | Constraints |
| --- | --- | --- |
| `name` | yes | 1–64 chars, lowercase `a-z0-9-` only. No leading, trailing, or consecutive hyphens. Must equal the directory name. No XML tags. Must not contain "anthropic" or "claude". |
| `description` | yes | 1–1024 chars. What it does **and** when to use it. |
| `license` | no | `MPL-2.0` for everything in this repo. |
| `compatibility` | no | ≤500 chars. Only if the skill has real environment requirements (`Requires git, docker, and network access`). Most skills omit it. |
| `metadata` | no | String→string map. Put `version` and `author` here, not at top level. |
| `allowed-tools` | no | Space-separated, e.g. `Bash(git:*) Read`. Experimental; support varies by agent. |

### description is the trigger

`description` is the only part of the skill that is always in context. It is
matched against the user's request to decide whether to load the skill at all —
so all "when to use this" information goes there, not in the body. Name the
concrete nouns and phrases a user would actually say.

Agents systematically *under*-trigger skills, so be direct about coverage:

```yaml
# Weak — never fires
description: Helps with changelogs.

# Works
description: >-
  Generates and updates CHANGELOG.md entries from git history following
  Keep a Changelog format. Use whenever the user mentions changelogs, release
  notes, "what changed since", or is preparing a version bump or release.
```

### Body

Structure for progressive disclosure — the agent pays for what it loads:

| Level | Loaded | Budget |
| --- | --- | --- |
| `name` + `description` | always, for every installed skill | ~100 tokens |
| `SKILL.md` body | when the skill triggers | under 5k tokens |
| `scripts/`, `references/`, `assets/` | only when read or executed | free until used |

- Keep `SKILL.md` under 500 lines. Past that, split into `references/` and tell
  the agent, in `SKILL.md`, exactly when to open each file.
- Reference files with relative paths from the skill root:
  `See [the API reference](references/REFERENCE.md) when the user asks about rate limits.`
- Keep references one level deep. No chains of files pointing at other files.
- Give reference files over ~300 lines a table of contents.
- Prefer a script over prose for anything deterministic and repetitive. Script
  code never enters context — only its output does.
- Write in the imperative. Explain *why* a constraint exists rather than stacking
  MUSTs; an agent that understands the reason handles the cases you didn't list.
- When a skill spans variants (clouds, frameworks, languages), put the selection
  logic in `SKILL.md` and one file per variant in `references/`.

## Adding a skill

1. `cp -r template skills/<skill-name>`
2. Set `name:` to `<skill-name>` — it must match the directory exactly.
3. Write the `description` first. If you can't state when it should trigger, the
   skill's scope is still unclear.
4. Write the body. Then reread it cold, as an agent with no context, and cut
   whatever you only understood because you'd just written it.
5. Fill in `README.md`, listing every bundled file and what it is for.
6. Add the skill to the table in the root `README.md`.
7. Validate: `uv run scripts/validate.py`.

## Validating

`scripts/validate.py` is a [uv](https://docs.astral.sh/uv/) single-file script —
its dependencies are declared inline, so there is no venv to create or activate:

```bash
uv run scripts/validate.py              # skills/* and template/
uv run scripts/validate.py skills/foo   # one directory
uv run scripts/validate.py --strict     # warnings fail too
```

Errors are spec violations and broken links; warnings are conventions from this
file. It exits non-zero on any error. Run it before every commit that touches a
skill.

## Testing a skill

The real test is behavioral, not structural: run a realistic prompt with the
skill installed and the same prompt without it, and compare. If the outputs are
indistinguishable, the skill is not earning its context. Common causes, in order
of frequency: the `description` never triggered, or the body only restated what
the model already does by default.

## Conventions

- Skill names are lowercase kebab-case, verb-or-domain first: `changelog-writer`,
  `rust-error-handling`. The directory name is the public interface — renaming it
  breaks installs.
- One skill, one job. Two loosely related workflows are two skills.
- Every skill is MPL-2.0, matching the repo `LICENSE`.
- Never add a skill that fetches instructions from a URL at runtime. Fetched
  content becomes instructions the user never reviewed.

## Commits

Conventional commit subjects scoped to the skill: `feat(changelog-writer): ...`,
`docs(readme): ...`, `fix(pdf-forms): ...`.
