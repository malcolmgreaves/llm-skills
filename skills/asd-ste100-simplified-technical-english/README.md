# asd-ste100-simplified-technical-english

> Human-facing docs. Agents read `SKILL.md`, not this file. Thus, the skill
> can operate without this file. See [AGENTS.md](../../AGENTS.md).

This skill makes an agent write all its prose in ASD-STE100 Simplified
Technical English (STE). The prose includes chat replies, plans, commit
messages, pull request descriptions, code comments, docstrings, error
messages, and documentation. STE is a controlled language. It uses a small
vocabulary in which each word has one meaning. It also uses short sentences in
the active voice, and commands for instructions. A reader with a limited
knowledge of English, a translator, or a machine translation engine can read
STE text without ambiguity.

This skill is not affiliated with ASD or the STEMG, and they do not endorse
it.

## About STE

- The aerospace industry made STE in the 1980s as AECMA Simplified English.
  Its function was to make aircraft maintenance manuals clear to technicians
  who are not native speakers of English. ATA iSpec 2200 and S1000D refer to
  it, and aviation authorities (EASA, FAA, CAAC) include it in their
  directives.
- The latest version is ASD-STE100 Issue 9 (January 2025). Issue 9 changed
  STE from a specification to a standard. The STEMG (Simplified Technical
  English Maintenance Group) of ASD keeps it, and the next issue is planned
  for 2028.
- The standard has two parts. Part 1 has 53 writing rules in 9 sections
  (words, multi-word nouns, verbs, sentences, procedural writing, descriptive
  writing, safety instructions, punctuation and word count, and writing
  practices). Part 2 is a dictionary of approximately 875 approved words and
  1,274 words that are not approved, each with approved alternatives.
- Words that are not in the dictionary are permitted if they are technical
  nouns or technical verbs of the subject field. A company usually keeps
  these terms in a glossary.
- The standard is free for all users from the
  [STEMG website](https://www.asd-ste100.org/STE_downloads.html).

The STEMG FAQ tells that STE is not for general correspondence, but that its
principles help in other texts. This skill applies the rules to all prose, and
it changes some of them for replies and code. Refer to
[How the skill applies STE](#how-the-skill-applies-ste) and
[Where the skill departs from the standard](#where-the-skill-departs-from-the-standard).

## When it triggers

The `description` covers all types of prose. Thus, the skill is for a full
session, not for one task. To start it for a session, do one of these steps:

- Start the session with `/asd-ste100-simplified-technical-english`.
- Add this line to the `CLAUDE.md` or `AGENTS.md` file of the project: "Follow
  the `asd-ste100-simplified-technical-english` skill for all prose."

The skill also triggers on prompts of these types:

- "Rewrite this runbook in Simplified Technical English."
- "Write the release notes in STE. Our readers are not native speakers."
- "Make these docstrings easy to machine-translate."
- "Does this procedure obey ASD-STE100?"

The skill does not do these tasks:

- Write in a language other than English. STE is for English only.
- Give approval to a text. The skill tells the user that a person with STE
  training must examine regulated documents.
- Change code, identifiers, quoted output, or the text of messages that are
  in the code.

## How the skill applies STE

The skill first identifies the type of each text. STE has two types, with
different rules.

| Type | Examples | Primary rules |
| --- | --- | --- |
| Procedural | Steps, runbooks, test instructions, instructions to the user | Commands, 20 words for each sentence, one instruction for each sentence, condition first |
| Descriptive | Replies, summaries, comments, docstrings, commit bodies | No commands, 25 words for each sentence, one topic for each sentence, six sentences for each paragraph |

For each type of text, the skill makes these decisions:

| Text | Decision |
| --- | --- |
| Replies | The result comes first, as descriptive text. Steps for the user are numbered commands. The agent can use *I* when the user must know which steps it did. |
| Plans | Numbered commands. |
| Commit messages | The subject line obeys the style of the project, for example Conventional Commits. The body is descriptive. |
| Pull requests | A descriptive summary, a numbered test procedure, and a caution before a step that can cause a loss of data. |
| Code comments | Descriptive text. A TODO comment is a command. |
| Docstrings | The first line obeys the style of the language (a command in Python, the third person in Java). The other lines are descriptive STE. |
| Documents | Task sections have command headings and numbered steps. Concept sections have noun headings. |
| Error messages | The problem first, then the command that corrects it. |
| Quoted text | Code, identifiers, commands, tool output, and UI labels do not change. |

## Requirements

`scripts/ste_lint.py` operates with Python 3.8 or a subsequent version. It
uses no other software. The other files are text. The skill does not use the
network.

## Bundled files

| Path | Purpose |
| --- | --- |
| `SKILL.md` | The skill: scope, the two types of text, the rules for words, verbs, sentences, paragraphs, punctuation, and procedures, how to apply them to each type of text, and a checklist. |
| `references/vocabulary.md` | STE decisions for approximately 300 words that agents use frequently: modal verbs, words for certainty, connecting words, verbs, nouns, pronouns, adjectives, prepositions, and phrasal verbs. The agent reads it at the start of a session. The linter reads its tables. |
| `references/software-terms.md` | The glossary of the skill: technical verbs and technical nouns for software and for documents, and jargon to replace. The linter reads it. |
| `references/examples.md` | Texts before and after a rewrite in STE: a reply, a status report, an explanation, a plan, a runbook, a commit message, a pull request, a README section, a docstring, an error message, and a review comment. |
| `scripts/ste_lint.py` | Reports text that does not obey the rules. It examines Markdown and plain text, and the comments and docstrings of source files. It does not change the text. |
| `evals/` | Cases for `claude plugin eval`. Refer to [Evals](#evals). |

## Evals

Run the suite from the root of the repository:

```bash
claude plugin eval skills/asd-ste100-simplified-technical-english --judge-model sonnet
```

The cases use only the `Skill` and `Read` tools, and no scaffold. The agent
writes each result in its reply. Each prompt tells the agent to write in STE.
Thus, the two arms try STE, and the difference in score shows the effect of
the skill on the quality of the STE.

| Case | Function |
| --- | --- |
| `evals/trigger-basic/` | Makes sure that a prompt to write in STE loads the skill. |
| `evals/reply-summary/` | A summary of a change must give the result first and tell which tests did not run. It must not start with a preamble, and it must not have unapproved modal verbs, contractions, semicolons, or other frequent unapproved words. |
| `evals/uncertain-cause/` | A status report must keep the uncertainty of the facts. It must not use *might*, *probably*, or other unapproved words, or the perfect and progressive tenses. |
| `evals/runbook-caution/` | A runbook must have numbered steps and a caution before the step that stops the connections. It must not have frequent unapproved words. |
| `evals/docstring/` | The docstring must give the rule of the function correctly, the comments must be descriptive (not commands), and the code must not change. |
| `evals/quoted-error/` | The explanation of an error must keep the path in the error, give safe numbered steps, and not have frequent unapproved words. |

The vocabulary graders are strict. Each one fails if the reply has one word
from its list.

On 2026-09-29, the suite ran with the default of three runs for each case
(judge model: Sonnet). The mean difference was +0.32.

| Case | With the skill | Without the skill |
| --- | --- | --- |
| trigger-basic | 1.00 | 0.00 |
| reply-summary | 1.00 | 0.61 |
| docstring | 1.00 | 0.67 |
| runbook-caution | 0.87 | 0.73 |
| uncertain-cause | 0.83 | 0.75 |
| quoted-error | 0.67 | 0.67 |

With the skill, only the vocabulary graders failed. Without the skill, these
graders also failed:

- The preamble grader, in 3 of 3 runs
- The grader for descriptive comments, in 3 of 3 runs
- The graders for the docstring rule, the modal verbs, and the position of
  the caution, in 1 run each.

The vocabulary grader of `quoted-error` failed in all runs of the two arms.
Thus, that grader does not show a difference between the arms.

An earlier run on 2026-09-28, with two runs for each case, kept the replies.
In that run, `scripts/ste_lint.py` examined 10 pairs of replies. (It does not
examine the docstring replies, because they are code.) The replies with the
skill had fewer errors in 7 pairs, the same number in 1 pair, and more errors
in 2 pairs. The largest difference was in the runbooks: 0 and 0 errors with
the skill, 13 and 4 errors without it. The words that the agent used by
mistake most frequently were *so*, *old*, and *confirmed*. After that run, the
checklist in `SKILL.md` got a list of these words.

## Design notes

- **The dictionary is not in this repository.** ASD has the copyright of the
  standard. The standard tells that no part of it can be copied or published
  without written permission from ASD.
- **The free permission covers specified groups only.** These groups are ASD
  and AIA members and their customers, defense ministries, A4A,
  airworthiness authorities, and universities. This repository is not in
  those groups.
- **Thus, the skill uses its own words.** `SKILL.md` gives the rules in the
  words of this skill, with the rule numbers of the standard.
  `references/vocabulary.md` gives the decisions for a small selection of
  words only. This repository has no definition and no example from the
  dictionary. For a word that the dictionary does not include, the status is
  *not listed*, and the *Use* column gives the recommendation of this skill.
  If the user gives the agent a copy of the standard, the agent uses its
  dictionary first.
- **The name.** "ASD-STE100 Simplified Technical English" is an EU trade mark
  of ASD. The name of the skill uses it only to identify the standard that the
  skill applies. The skill is not affiliated with ASD or the STEMG. The skill
  tells the agent not to call a text "STE compliant" or "certified". The
  STEMG does not give approval to tools, and this includes AI tools. Its
  white paper on STE and AI (June 2026) tells that AI tools can help writers,
  but they cannot replace the persons who examine the text.
- **The skill is written in STE.** `SKILL.md`, this README, and the files in
  `references/` obey the rules that they give. `scripts/ste_lint.py` reports
  no errors on them. An agent that reads STE instructions writes STE more
  easily. If you edit the skill, run the linter on the files that you change.
- **The two types of text come first.** Most STE rules depend on the type:
  the length limit, commands, notes, and paragraphs. A reply usually has the
  two types. Thus, the skill tells the agent to keep them in different
  sentences and lists.
- **Uncertainty is information.** STE has no word for *probably*, *likely*,
  or *might*. A rewrite that deletes a hedge makes a different claim. The
  skill tells the agent to use *possibly* or *it is possible that*. It also
  tells the agent to give the data and the steps that it did not do.
- **The linter reports only.** It masks quoted text (code font, bold,
  italics, quotations, paths, and URLs), and it counts words as rule 8 tells.
  It gets its word lists from the files in `references/`, thus each word has
  one source.
- **The linter cannot find the part of speech of a word.** STE gives
  approval to some words only as one part of speech. For these words, the
  linter makes a guess from the word before them, and it gives a warning, not
  an error. A clean result does not show that the text obeys STE.
- **The skill and google-developer-style do not agree on some rules.** Google
  style uses contractions, *might*, and sentences of up to approximately 26
  words. STE does not. If the two skills are active, `SKILL.md` tells the
  agent to tell the user one time and to let the user select one.

### Where the skill departs from the standard

- **First person.** STE has no *I*, *me*, or *my*. But a reply must frequently
  tell the user which steps the agent did or did not do. The skill lets the
  agent use these three words in replies only.
- **Technical verbs for software.** The dictionary replaces *fail* with *if
  ... not* or *unsatisfactory*, and *run* with *operate*. In software, *run*,
  *pass*, *fail*, *return*, *call*, and *build* have one technical meaning.
  Rule 1.12 lets a writer use the technical verbs of the subject field. But
  it also tells the writer to use an approved verb when one gives the same
  information, and the dictionary gives one for these verbs.
  `references/software-terms.md` gives these verbs and their meanings.
- **Conventions of the language and the project.** A docstring summary obeys
  the style of the language, and a commit subject obeys the style of the
  project. STE tells that it operates together with the style guides of a
  project, and that it does not control format.
- **Cautions for data.** STE uses a caution for a risk of damage to objects.
  The skill also uses a caution for a risk of loss of data.

### Prior art

[danyuchn/asd-ste100-skill](https://github.com/danyuchn/asd-ste100-skill)
applies STE when the user tells it to rewrite a text that a different agent
reads. It uses the vocabulary rules as advice only. It also keeps compound
tenses where they give information. This skill operates on all prose of a
session. It applies the vocabulary decisions of the dictionary where it has
them. It also tells the agent how to apply STE to each type of text.
