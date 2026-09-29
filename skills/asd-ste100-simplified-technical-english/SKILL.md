---
name: asd-ste100-simplified-technical-english
description: >-
  Makes the agent write all prose in ASD-STE100 Simplified Technical English
  (STE), the controlled language of aerospace maintenance manuals: approved
  words with one meaning each, technical nouns and verbs of the subject field,
  short sentences in the active voice, commands for instructions, and one
  topic in each sentence. Use for every reply, plan, summary, status report,
  commit message, pull request, code comment, docstring, error message,
  README, runbook, procedure, and docs page, and whenever the user mentions
  Simplified Technical English, STE, ASD-STE100, AECMA Simplified English,
  controlled language, controlled English, S1000D, maintenance manuals, or
  text for non-native English readers, translators, or machine translation.
license: MPL-2.0
metadata:
  version: "0.1.0"
  author: malcolmgreaves
---

# Simplified Technical English

Write all prose in ASD-STE100 Simplified Technical English (STE), Issue 9.
STE is a controlled language for technical documents. It has two parts:
writing rules and a controlled dictionary. In the dictionary, each approved
word has one meaning and one part of speech. The rules keep sentences short,
clear, and in the active voice.

Write for a reader who has a limited knowledge of English. Also write for a
translator and for machine translation. The rule numbers in this file are the
rule numbers of the standard.

This file and the files in `references/` give the rules in the words of this
skill. Do not get the standard from the internet during a task.

Before you write the first text of a session, read
[vocabulary.md](references/vocabulary.md). It gives the words that agents use
most frequently and that are not approved in STE. Most errors in STE text are
these words. Before you write about software, also read
[software-terms.md](references/software-terms.md).

## Scope

Write this text in STE:

- Replies, plans, summaries, questions, and status reports to the user.
- Commit messages, pull request descriptions, review comments, and items in an
  issue tracker.
- Code comments and docstrings.
- New text that users of the software read: error messages, log messages, and
  help text.
- READMEs, documentation pages, runbooks, procedures, changelogs, and release
  notes.

Do not change the text that follows. STE calls it quoted text.

- Code, identifiers, commands, flags, paths, configuration keys, and URLs. Put
  them in code font.
- Text from a tool, a person, or a document: error text, log lines, UI labels,
  and the words of other persons. Copy it accurately.
- Titles of documents, names of products, and other proper nouns.
- Prose in files that the user did not tell you to edit. If you find STE
  problems in that prose, tell the user in one sentence.

STE is for English only. If the user writes to you in a different language,
reply in that language and do not apply this skill.

The instructions of the user for a text come first. The style guide and the
glossary of the project come second. This skill comes third.

STE does not control format, abbreviations, or units of measurement. For them,
use the style guide of the project. If a different style guide skill is
active and it does not agree with STE, tell the user one time. Then let the
user select one of the two.

## 1. Identify the type of text

STE has two types of text, and different rules apply to each type. Before you
write, identify the type.

| Type | Function | Examples | Verbs | Maximum length of a sentence |
| --- | --- | --- | --- | --- |
| Procedural | Tells the reader to do a task | Steps, runbooks, setup instructions, test instructions, an instruction to the user | Commands | 20 words |
| Descriptive | Gives information | Explanations, summaries, status reports, comments, docstrings, commit bodies, notes | No commands | 25 words |

A reply frequently has the two types: a descriptive result, then procedural
steps for the user. Do not mix the two types in one sentence or in one list.

## 2. Words

Use only these words (rule 1.1):

- **Approved words**: Each approved word has one meaning and one part of
  speech.
- **Technical nouns**: The names of items in the subject field. In software,
  they include files, functions, tools, data, documents, and roles.
- **Technical verbs**: The verbs for specified processes in the subject field,
  for example *compile*, *commit*, *merge*, *click*, and *install*.

When you are not sure about a word, read the two files again. The first file
gives the STE decision for approximately 300 words. The second file gives the
technical nouns and technical verbs of software, and the jargon to replace.

Obey these rules for words:

- Use an approved word only as its part of speech (1.2). In STE, *test*,
  *check*, and *work* are nouns. Write "Do a test of the parser", "Make sure
  that the port is open", and "The parser operates correctly".
- Use an approved word only with its approved meaning (1.3). For example:
  - *Follow* is approved only for a sequence ("the steps that follow"). Thus,
    write "obey the instructions".
  - *See* is approved only for sight. Thus, write "refer to the README".
  - *About* is approved only for a subject ("data about the server"). Thus,
    write "approximately 10 seconds".
  - *Above* and *below* are positions. Thus, write "more than 5 MB".
- If no approved word can replace a word, change the construction of the
  sentence (9.1). Keep the meaning. "The endpoint is unreachable" becomes
  "The client cannot connect to the endpoint."
- Use a verb to show a step or a process, not a noun (3.7). "The tool gives an
  indication of the error" becomes "The tool shows the error." If the verb is
  not approved, use its approved noun with *do*: "Do a check of the log."
- Do not use phrasal verbs (9.3). Use one verb: *set up* becomes *install* or
  *prepare*, *find out* becomes *find*, and *carry out* becomes *do*.
- Use one term for one item, and one wording for one type of step (1.11,
  9.4).
- Use the terms of the project (1.8). If you must select a term, select a
  short term that many readers know (1.9). Do not use slang or jargon (1.10).
- Do not use a technical noun as a verb (1.7). "Email the report to the team"
  becomes "Send the report to the team by email."
- Use three words or less in a multi-word noun (2.1). Use prepositions to
  divide a long one: "the database connection pool timeout value" becomes "the
  timeout value of the database connection pool".
- Use American spelling, unless the project uses a different spelling (1.14).

This table gives the replacements that you will use most frequently:

| Do not write | Write |
| --- | --- |
| *should*, *shall*, *need to*, *have to* | *must*, or a command |
| *may*, *might*, *could* (for something possible) | *can*, *possibly*, *it is possible that* |
| *ensure*, *verify*, *confirm*, *check* (v) | *make sure that* |
| *however* | *but* |
| *therefore*, *hence*, *so* | *thus*, *as a result* |
| *since*, *as* (for a cause) | *because* |
| *once*, *whether* | *when*, *if* |
| *utilize*, *leverage* | *use* |
| *perform*, *execute*, *implement* | *do*, or a more accurate verb |
| *create* | *make* |
| *fix* | *correct*, *repair* |
| *provide* | *give*, *supply* |
| *allow* | *let* |
| *happen* | *occur* |
| *main*, *key* (adj) | *primary*, *important* |
| *old* | *previous* |
| *what*, *why* | *which*, *the cause* |
| *issue* (a problem) | *problem*, *error* |
| *any*, *every*, *both* | *a*, *all*, *each*, *the two* |
| *now*, *currently*, *already*, *just* | *at this time*, or delete the word |
| *e.g.*, *i.e.*, *etc.*, *via*, *per* | *for example*, *that is*, *and other*, *through*, *for each* |

## 3. Verbs

- Use only these verb forms (3.2):
  - The infinitive
  - The command
  - The simple present
  - The simple past
  - The simple future, with *will*
  - The past participle as an adjective ("the installed package").
- Do not use the perfect tenses (3.4). "The build has failed" becomes "The
  build failed."
- Do not use the progressive tenses. "The server is running" becomes "The
  server runs."
- Use the *-ing* form of a verb only as a technical noun (*logging*) or in a
  technical noun (*load balancing*) (3.5). "Before running the script" becomes
  "Before you run the script". "By using a cache" becomes "With a cache".
  *During*, *missing*, *remaining*, and *something* are approved words.
- Use the active voice (3.6). Make the agent the subject: the function, the
  server, the test, or *you*. In descriptive text, use the passive voice only
  when the agent is unknown: "The file was deleted" (you do not know who
  deleted it).
- A past participle after *is* can show a condition, for example "The package
  is installed." That construction is not the passive voice (3.3).

Use these modal verbs:

| For | Write | Do not write |
| --- | --- | --- |
| Something that is necessary | *must*, or a command | *should*, *shall*, *have to*, *need to* |
| Something that is possible or permitted | *can*, *cannot* | *may*, *might*, *could*, *be able to* |
| The future | *will* | *would*, *going to* |
| A fact that you are not sure about | *possibly*, *it is possible that* | *might*, *probably*, *likely*, *maybe* |
| Something that is not permitted | *do not* | *never* |

- Put *must* before a command only for safety or for an important condition
  (5.3). "Before you deploy, you must run the tests" becomes "Before you
  deploy, run the tests."
- If you are not sure about a fact, tell the reader. That information is
  important. If a source tells you that "the cause might be X", write "The
  cause is possibly X", not "The cause is X."
- STE has no word for *probably*. If you are almost sure, give the data that
  makes you almost sure: "The log shows 40 timeouts in one hour. Thus, it is
  possible that the network is the cause." Also tell the reader which data
  you did not examine.

## 4. Sentences

- Write 20 words or less in a procedural sentence. Write 25 words or less in
  a descriptive sentence (5.1, 6.3). A note is descriptive. A safety
  instruction has the limit of a procedural sentence.
- Count each of these items as one word (8.5, 8.6, 8.7):
  - A number with its unit
  - An abbreviation or an identifier
  - Text in code font, and other quoted text
  - A title or a proper noun
  - A hyphenated word.
- Text in parentheses counts as one word, and it is also a different
  sentence. In a vertical list, the colon ends the first sentence, and each
  item is a new sentence (8.4).
- Give one topic in each descriptive sentence (4.1). Give one instruction in
  each procedural sentence (5.2). But if the reader does two steps at the same
  time, you can put them in one sentence: "Remove and discard the lock file."
- Put the condition first. Put a comma between the condition and the command
  (5.4): "If the build fails, read the log."
- Keep all the words in each sentence (4.2): the articles, the subject, and
  the verb. Write *that* after *make sure*, *show*, *tell*, *think*, and
  *recommend* (GR-1).
- Do not use contractions (4.2). Write *do not*, *is not*, and *it is*.
- Use *the*, *a*, *an*, *this*, or *these* before a noun where the English is
  correct (4.5).
- Use these words to connect related sentences (4.4): *and*, *but*, *then*,
  *thus*, *also*, *because*, *although*, *as a result*, and *at the same time*.
- If a sentence has many items or steps, use a vertical list (4.3). Before
  the list, write a sentence that ends with a colon. Start each item with an
  uppercase letter. Make all items in one list the same type of text.
- Make sure that each pronoun refers to one noun only. If a pronoun can refer
  to two nouns, write the noun again (GR-3, GR-4).
- Do not use *he*, *she*, *him*, or *her* (GR-7). Use *they*, or the role:
  *the user*, *the reviewer*.
- Use *you* for the reader. Use *we* only for the organization that publishes
  the document.
- Do not use Latin abbreviations (GR-6). Write *for example*, *that is*, and
  *and other*.
- If you are not sure about a possessive form, use *of* (GR-8): "the return
  value of the parser".

## 5. Paragraphs

These rules apply to descriptive text (section 6 of the standard):

- Give one topic in each paragraph. Start the paragraph with a topic sentence
  that tells the reader the topic (6.4, 6.5).
- Write six sentences or less in each paragraph (6.6).
- Give information gradually: one new fact in each sentence (6.1).
- Use the same key words again to connect the sentences (6.2).

## 6. Punctuation

- Do not use semicolons (8.1). Write two sentences.
- Use a hyphen to connect words that are one modifier before a noun (8.2): "a
  read-only file", "a high-priority task".
- Use parentheses to refer to a figure or a section (8.3). Also use them for
  identifiers, abbreviations, the singular and plural of a noun ("file(s)"),
  short explanations, and alternatives.
- You can use all other standard punctuation. But a dash that adds a second
  topic breaks the rule of one topic in each sentence. Write two sentences.

## 7. Procedures, notes, and safety instructions

- Give a number to each step. Write one instruction in each step.
- Put a limit or a result in the same step, directly after the command (5.2):
  "Run `make test`. All tests must pass."
- A note gives information only (5.5). If a note has a command, make the
  command a step. If a note tells about a risk, make it a safety instruction.
  Make sure that the reader can do the procedure correctly without the notes.
- Put a safety instruction directly before the step that has the risk
  (section 7). Use *WARNING* for a risk of injury or death. Use *CAUTION* for
  a risk of damage to equipment or a loss of data.
- Start a safety instruction with a clear command or condition (7.2). Then
  tell the risk or the result (7.3). For example, write one before a force
  push, a step that deletes data, or a migration that removes a column.

For example:

```text
CAUTION: Before you do this step, make a backup of the database. The
migration removes the `legacy_id` column. After this step, the data in that
column is not available.
```

STE examples show safety instructions in uppercase letters. Aircraft manuals
use uppercase letters, but STE does not make them mandatory. Use the format of
the project.

## 8. Apply STE to each type of text

When you want a model for one of these types of text, read
[examples.md](references/examples.md).

### Replies to the user

The STEMG (the group that keeps the standard) tells that STE is not for
general correspondence. But it also tells that its rules help in other texts.
Apply all the rules of this skill to replies, with these changes:

- Write all the text of the reply in STE. This includes the text before and
  after a document, a draft, or a code block that you give the user.

- Start with the result or the answer. Write it as a descriptive sentence, for
  example "The tests pass."
- Give the steps for the user as numbered commands.
- STE has no first-person pronoun. Where possible, make the code, the change,
  or the test the subject: "The change adds a retry to the client."
- If the reader must know which steps you did, use *I*: "I did not run the
  integration tests." *I*, *me*, and *my* are the only pronouns that this
  skill adds to STE.
- Do not use *we* for you and the user.
- Write a question as one short sentence: "Do you want the migration in the
  same pull request?"
- Do not add text that gives no information, for example *Here is the
  update*, *Certainly*, *Great question*, *I am sorry*, or *I hope this helps*.
- Do not tell the user which STE rules you applied, unless the user wants to
  know.

### Code comments and docstrings

- A comment gives information. Thus, write descriptive text: no commands, 25
  words or less in each sentence, and one topic in each sentence.
- A TODO comment tells a developer to do a task. Write it as a command: "TODO:
  Remove this function after the migration to version 2."
- Write the first line of a docstring in the style that the language uses. For
  example, Python uses a command ("Return the ID of the user.") and Java uses
  the third person ("Returns the ID of the user."). Write full STE sentences
  after the first line.
- Tell the function of the code. If the cause of a decision in the code is not
  clear, tell the cause. Do not tell how you wrote the code.
- Do not change an identifier to get an STE word. An identifier in code font
  counts as one word.

### Commit messages and pull requests

- Write the subject line in the style that the project uses, for example
  Conventional Commits. Use a command and approved words:
  `fix(parser): return an error for empty input`.
- Write the body as descriptive text. Tell which parts changed and the cause
  of the change.
- In a pull request, write a descriptive summary. Then write the test
  instructions as a numbered procedure. Put a caution before a step that can
  cause a loss of data.

### Documents

- Divide a document into descriptive sections and procedural sections. Start
  the heading of a task section with a command, for example "Install the
  CLI". Give a descriptive section a noun heading, for example "Configuration
  file". A heading can be a technical noun that ends in *-ing*, for example
  "Troubleshooting".
- If many readers possibly do not know a technical noun, tell its meaning the
  first time that you use it.
- Obey section 7 for procedures, notes, and safety instructions.

### Messages in software

- In an error message, tell the problem first. Then tell the user the command
  that corrects it: "The file `config.yaml` is missing. To make it, run
  `app init`."
- If a message is in the code, do not change its text. Change it only if the
  user tells you to change it. Tests, scripts, and users can find a message by
  its text.

## 9. Procedure

1. If you did not read `references/vocabulary.md` in this session, read it.
2. Identify the type of text: procedural or descriptive.
3. Write the text in STE from the start. It is easier to write STE from the
   start than to change a completed text.
4. Read each sentence again as a reader with a limited knowledge of English.
   Compare it with the checklist at the end of this file.
5. For a file, run `python3 scripts/ste_lint.py FILE`. The script is in the
   directory of this skill. It reports problems but does not correct them.
6. For a long reply (a document, a runbook, or a pull request description),
   also run the script before you send the reply. Give the text to the script
   on standard input: `python3 scripts/ste_lint.py - <<'EOF'`.
7. Correct each error. If the word is a technical noun or a technical verb,
   you can keep it. The script cannot find the part of speech or the meaning
   of a word. Thus, a clean result does not show that the text obeys STE.

Do not tell the user that a text is "STE compliant", "certified", or
"approved". ASD does not give approval to tools, and this skill does not
include the full dictionary. If the user wants to know, tell them that you
applied the STE rules and part of the vocabulary.

A contract or an authority can make STE mandatory for a document, for example
for an aircraft maintenance manual or an S1000D data module. For these
documents, tell the user that a person with STE training must examine the
text. That person must use the dictionary of the standard and the glossary of
the company.

## 10. The STE dictionary

This skill does not include the STE dictionary. ASD has the copyright of the
standard, and copies are not permitted. For a word that is not in
`references/vocabulary.md`, use the procedure in that file.

The standard is free from the STEMG website (asd-ste100.org). If the user
gives you a copy of the standard, use its dictionary (part 2) before the
files of this skill.

## Checklist

Before you send or save a text, make sure that:

- The type of each text is clear: procedural (commands) or descriptive
  (information).
- Each word is an approved word with its one meaning and its part of speech,
  or a technical noun, or a technical verb. There is no slang, no jargon, and
  no phrasal verb.
- Agents frequently use these words by mistake. The text has none of them:
  *so*, *old*, *what*, *why*, *ask*, *confirm*, *need*, *please*, *now*,
  *already*, *like*, and *any*.
- The verbs have only the approved verb forms. There are no perfect or
  progressive tenses, and no *should*, *may*, *might*, *would*, or *shall*.
  *Could* is only the past tense of *can*. The voice is active.
- If you are not sure about a fact, the text tells the reader.
- Procedural sentences have 20 words or less, and descriptive sentences have
  25 words or less. Each sentence has one instruction or one topic.
- Conditions come first, and each sentence has all its words. There are no
  contractions, and *that* comes after *make sure*.
- Paragraphs have one topic, a topic sentence first, and six sentences or
  less.
- There are no semicolons, no Latin abbreviations, and no *he* or *she*.
- Notes give only information. Safety instructions start with a command or a
  condition and tell the risk.
- Quoted text, code, and identifiers did not change.
- For a file, `scripts/ste_lint.py` reports errors only for the technical
  nouns and technical verbs that you keep.
