# <skill-name>

> Human-facing docs. Agents read `SKILL.md`, never this file — so nothing here
> may be load-bearing. See [AGENTS.md](../AGENTS.md).

One-paragraph summary of what the skill does and the problem it solves.

## When it triggers

Paraphrase the `description` in plain language, and give two or three example
prompts that should activate it:

- "..."
- "..."

Also note what it deliberately does *not* cover, and which skill to reach for
instead.

## Requirements

Tools, runtimes, credentials, or network access the skill assumes. Delete this
section if there are none. Mirror anything listed here into the `compatibility`
frontmatter field.

## Bundled files

| Path | Purpose |
| --- | --- |
| `SKILL.md` | The skill itself. |
| `scripts/example.py` | What it does, and how `SKILL.md` invokes it. |
| `references/REFERENCE.md` | What it contains, and when the agent reads it. |

## Design notes

Why the skill is shaped this way: what was tried and rejected, which constraints
are load-bearing, what to be careful about when editing it. This is the section
that saves the next person an hour.
