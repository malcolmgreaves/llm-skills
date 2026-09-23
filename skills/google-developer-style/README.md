# google-developer-style

> Human-facing docs. Agents read `SKILL.md`, never this file, so nothing here
> is required for the skill to work. See [AGENTS.md](../../AGENTS.md).

Makes an agent write the way the [Google developer documentation style
guide](https://developers.google.com/style/) says to, in everything it
writes: chat replies, plans, commit messages, pull request descriptions,
code comments, docstrings, READMEs, and docs. The skill exists to remove the
figurative, filler, and hype language that language models produce by
default (*wedge*, *load-bearing*, *seam*, *under the hood*, *simply*,
*robust*, *let's dive in*) and replace it with literal statements about what
the code does and what the reader does.

The guide's rules that do most of the work:

- Literal language: no metaphors, analogies, anthropomorphism, or idioms.
- Second person, active voice, present tense.
- *Must*, *can*, *might*, and *We recommend* instead of *should*, *will*,
  *may*, *could*, and *would*.
- No filler (*simply*, *just*, *please note*), no excessive claims
  (*robust*, *best*, *guaranteed*), no time-anchored words (*currently*,
  *new*, *soon*).
- Sentence-case headings, bold only for UI elements, code font for code,
  serial commas, no exclamation points.

## When it triggers

The description covers every kind of prose, so the skill is meant to be on
for the whole session rather than for one task. Two ways to get that:

- Start the session with `/google-developer-style`.
- Add a line to the project's `CLAUDE.md` or `AGENTS.md`: "Follow the
  `google-developer-style` skill for all prose."

It also triggers on requests such as:

- "Rewrite this README in Google developer documentation style."
- "Make these docstrings follow the Google style guide."
- "Remove the jargon and metaphors from this PR description."
- "This sounds like an AI wrote it. Make it plain."
- "Copyedit these release notes."

What it doesn't cover:

- UI copy (button labels, in-product strings). The guide defers to Material
  Design for that.
- HTML and CSS markup rules, which the guide has and this skill omits.
- Google-product-specific terminology (Cloud, Android, Workspace entries in
  the word list).
- Code style. The skill governs comments and docstrings, not the code.

## Requirements

`scripts/lint.py` needs Python 3.8 or later and nothing else. The rest of
the skill is text.

## Bundled files

| Path | Purpose |
| --- | --- |
| `SKILL.md` | The skill: scope, the eight rules, a checklist, and pointers to the references. |
| `references/word-list.md` | The guide's word list, condensed and paraphrased, A to Z. Read when unsure whether a term is acceptable. |
| `references/llm-habits.md` | Figurative, filler, and hype terms and formatting habits that models overuse, with replacements. Read at the start of a session. |
| `references/formatting.md` | Headings, lists, procedures, tables, code in text, placeholders, UI elements, punctuation, numbers, dates. Read before writing a full document. |
| `references/code-comments.md` | API reference comments, docstrings, inline comments, commit messages, PR descriptions, release notes, error messages. Read before writing any of those. |
| `references/examples.md` | Before-and-after rewrites of a chat summary, a plan, a commit, a PR, a README section, a docstring, and comments. |
| `scripts/lint.py` | Reports terms and punctuation that the skill rules out. `python3 scripts/lint.py FILE...` or stdin. Skips code blocks; checks only comments in source files. |

## Design notes

- **Literal language is rule 1, before grammar.** The guide's grammar rules
  are things a model already mostly does. What it doesn't do by default is
  stop illustrating. Putting the figurative-language rule first, with a
  replacement table, is what makes the skill's output differ from the
  model's default.
- **Replacements are facts, not synonyms.** *Load-bearing* has no synonym;
  it stands for a specific dependency. The references say so and give
  examples, because a synonym list produces the same vagueness in
  different words.
- **Two word lists.** `word-list.md` is the guide's list, paraphrased under
  its CC BY 4.0 license, so an agent can check a term against the source.
  `llm-habits.md` is the list of what models do, which the guide covers only
  by principle. Keeping them apart makes each one shorter and makes it clear
  which entries are the guide's and which are this skill's application of
  it.
- **The linter reports; it doesn't rewrite.** A mechanical replacement of
  *leverage* with *use* is safe; a mechanical replacement of *wedge* is not.
  Mentions in italics, bold, or code font are exempt, and so is the first
  cell of a table row, so a document can discuss a term (as this skill's own
  files do) without tripping the check. A
  `<!-- style-lint: off -->` / `<!-- style-lint: on -->` pair exempts a
  region, which `examples.md` uses around its "before" text.
- **The skill's own text follows the skill.** If you edit it, run the linter
  on it. A style skill that breaks its own rules teaches the wrong thing.
- **SKILL.md is long for a skill (about 350 lines).** The rules are the
  deliverable, and an agent that has to open a reference file to learn that
  *should* is out will not do it in a chat reply. The references hold the
  material an agent needs only for particular kinds of text.
- **Testing.** Run the same prompt (for example, "summarize what you
  changed") with and without the skill and compare. The skill is working if
  the with-skill output has no term from `llm-habits.md`, leads with the
  result, and is shorter.
