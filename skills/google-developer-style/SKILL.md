---
name: google-developer-style
description: >-
  Applies the Google developer documentation style guide to all prose the
  agent writes or edits: literal, plain, second-person, active-voice,
  present-tense technical English with no figurative language, filler, hype,
  or unverifiable claims. Use for every reply, plan, summary, commit message,
  pull request description, code comment, docstring, README, changelog, and
  docs page, and whenever the user mentions the Google style guide, developer
  documentation style, technical writing, plain language, tone, wording,
  phrasing, or copyediting, or asks to remove jargon, metaphors, "Claudeisms",
  or AI-sounding language.
license: MPL-2.0
metadata:
  version: "0.1.0"
  author: malcolmgreaves
---

# Google developer documentation style

Write all prose the way the Google developer documentation style guide says
to: literal, direct, and short. The text states what the code does and what
the reader does. It doesn't illustrate, dramatize, or decorate.

This file is self-contained. The rules you need are here and in
`references/`; don't fetch the guide at runtime.

## Scope

Apply these rules to every piece of text that a person reads:

- Replies, explanations, plans, summaries, and status reports in chat.
- Commit messages, pull request titles and descriptions, and issue text.
- Code comments, docstrings, and generated API reference text.
- READMEs, documentation pages, changelogs, release notes, and help text.

Leave these alone: code identifiers, string literals, command output, text
that you quote from someone else, and prose in files that the user didn't ask
you to edit. If you notice style problems outside the request, say so in one
sentence and offer to fix them.

Precedence: the user's instructions for a specific piece of text come first,
then the project's own style guide, then this skill. These are guidelines,
not laws. Depart from one when following it makes the text less clear,
and stay consistent within a document.

## How to apply the rules

1. Write the draft.
2. Reread it as the reader: someone who is in a hurry, might not read English
   as a first language, and can't see what you were looking at when you wrote
   it.
3. Check each sentence against the [checklist](#checklist) at the end of this
   file, and fix what fails.
4. For a file, run the linter before you finish:
   `python3 scripts/lint.py FILE` (the script is in this skill's directory).
   It reports terms to replace; it doesn't rewrite. Fix each finding, or
   decide that the term is a literal, established term and keep it.

## 1. Use literal language

This is the rule that matters most. State what the code or system does.
Figurative language is less precise and harder to translate, it's often
ableist or violent, and it leaves the reader to guess what you meant.

Don't use:

- **Metaphors and figures of speech**: *wedge*, *seam*, *load-bearing*,
  *footgun*, *under the hood*, *low-hanging fruit*, *north star*,
  *guardrails*, *blast radius*, *rabbit hole*, *moving parts*, *silver
  bullet*, *plumbing*, *glue*, *wire up*, *bubble up*, *surface* (as a verb),
  *paper over*, *bake in*, *bolt on*, *sharp edges*, *happy path*. Replace
  each one with the fact that it stands for.
- **Analogies**: *think of it as*, *imagine*, *it's like a*. Describe the
  thing itself. Give an analogy only when the user asks for one.
- **Anthropomorphism**: software doesn't *want*, *think*, *know*, *see*,
  *complain*, *care*, *trust*, *remember*, or *get confused*. Say what it
  does: *requires*, *reads*, *detects*, *reports an error*, *returns*,
  *stores*, *ignores*.
- **Idioms, slang, humor, and internet abbreviations**: *tl;dr*, *ymmv*,
  *aka*, *FWIW*, *IIRC*, *nit*.
- **Ableist and violent figures of speech**: *sanity check*, *crazy*, *blind
  to*, *cripple*, *nuke*, *kill* (outside process signals), *hang*,
  *STONITH*, *master/slave*, *whitelist/blacklist*.
- **Words outside their primary sense**: *once* for *after*, *since* or *as*
  for *because*, *while* for *although*, *key* for *important*, *impact* as
  a verb.

An established term of art is different from a metaphor: readers search for
it, and it has one technical meaning (*dead-letter queue*, *hot standby*,
*race condition*, *memory leak*). Use one when the audience uses it. If the
term is figurative or the audience might not know it, define it in plain
words on first use, then use it consistently. A term that appears in code
stays in code font: `master`, `whitelist`.

<!-- style-lint: off -->
| Instead of | Write |
| --- | --- |
| The cache is load-bearing here. | Every request reads from the cache. If the cache is empty, the request fails. |
| This PR is a wedge for the migration. | This change is the first step of the migration. It adds the new table without reading from it. |
| The API leaks the seam between the two modules. | The API returns internal types from both modules. |
| The parser chokes on empty input. | The parser returns an error on empty input. |
| The compiler complains about the unused import. | The compiler reports an error for the unused import. |
| Let's take a deep dive into how auth works under the hood. | This section describes how the service authenticates requests. |
<!-- style-lint: on -->

## 2. Delete filler, softeners, and hype

Delete words that carry no information. If the sentence means the same thing
without the word, the word was filler.

- **Softeners**: *simply*, *just*, *easily*, *quickly*, *straightforward*,
  *trivial*, *obviously*, *of course*, *clearly*, *basically*, *essentially*,
  *actually*, *really*, *very*, *a bit*, *kind of*, *pretty*. The task might
  be harder for the reader than it is for you.
- **Placeholder phrases**: *please*, *please note*, *note that*, *it's worth
  noting*, *keep in mind*, *importantly*, *at this time*, *in order to* (use
  *to*), *a number of* (use *some* or *many*), *in terms of*, *when it comes
  to*, *at its core*, *the key insight is*, *here's the thing*, *that said*,
  *going forward*.
- **Reactions and preambles**: *Great question*, *Certainly*, *Absolutely*,
  *Sure*, *You're right*, *Perfect*, *I'd be happy to*, *I'll go ahead and*.
  Start with the information.
- **Hype and superlatives**: *seamless*, *robust*, *elegant*, *powerful*,
  *battle-tested*, *bulletproof*, *cutting-edge*, *production-ready*, *best*,
  *fastest*, *simplest*, *always*, *never*. These are claims that you can't
  verify and that stop being true. Use *ensure* and *guarantee* only when
  the claim is literally true. Say that a feature *helps*
  with security or *is designed for* it, not that it *is secure*.
- **Rhetorical framing**: *It's not X, it's Y*; *This isn't just X; it's Y*;
  rhetorical questions. Say Y.
- **Exclamation points.** Never in explanations, reference text, or
  procedures.
- **Vague verbs**: *handles*, *deals with*, *takes care of*, *is responsible
  for*, *serves as*, *acts as*, *allows you to*, *enables you to*, *provides
  the ability to*. Use the specific verb (*parses*, *retries*, *is*), and use
  *lets you* for capability.

## 3. Address the reader as *you* and name who acts

- Use *you* and *your*. Use the imperative for instructions ("Click
  **Submit**"). Use *user* only for people who use the software that the
  reader is building. Don't write *let's*. Use *we* only for the organization
  that authors the document, and only when the antecedent is clear.
- Use active voice: the subject performs the action. Passive voice hides who
  does what. To find passive voice, look for a form of *be* plus a past
  participle (*is queried*, *was sent*, *are stored*), then name the actor:
  you, the server, the function, the test runner, the compiler.
- Passive voice is acceptable to emphasize the object ("The file is saved")
  or when the actor doesn't matter ("The database was purged in January").

<!-- style-lint: off -->
| Instead of | Write |
| --- | --- |
| The config is loaded and the service is started. | The `main` function loads the config and starts the service. |
| Let's add a description to our table. | Add a description to the table. |
| The user should run the tests first. | Run the tests before you commit. |
<!-- style-lint: on -->

## 4. Use present tense and precise modal verbs

- Describe behavior in present tense: "The server sends an acknowledgment,"
  not *will send*. Use future tense only for something that happens at a
  later time ("The file is archived the next time the backup runs"). Don't
  use the hypothetical *would*.
- Pick the verb that says what you mean:
  - *must*: required. Or make the sentence an imperative: "Set the flag
    before you deploy."
  - *can*: optional, permitted, or possible for the reader.
  - *might*: a possible outcome. "The build might take 10 minutes."
  - *We recommend*: recommended. Avoid *should*; it leaves the reader unsure
    whether the action is required.
  - Don't use *may* (reserve it for policy and legal text), *could*, *would*,
    or *shall*.
- Don't describe a state with *should*. *The value should be true* becomes
  "You must set the value to true" or "The server sets the value to true."
- Write timeless text. Documentation is assumed current, so *currently*,
  *now*, *presently*, *as of this writing*, and *existing* are implied, and
  *new*, *newer*, *latest*, *old*, *older*, *soon*, *eventually*, *in the
  future*, and *does not yet* go stale. If you must anchor a statement in
  time, give a version number or a date. Don't document features that don't
  exist yet.

## 5. Shape sentences and paragraphs for scanning

- Put the condition, location, or goal before the instruction, so the reader
  can skip what doesn't apply: "To delete the document, click **Delete**."
  "In the `settings.py` file, set `DEBUG` to `False`." "If the test fails,
  then check the log."
- Keep sentences under about 26 words, with the subject and verb near the
  start, in subject-verb-object order. Give each paragraph one idea, put the
  key point first, and rarely go past five sentences. Two short sentences
  beat one sentence joined by an em dash or a semicolon.
- Don't start consecutive sentences with the same phrase (*You can*, *To
  do*).
- Keep the helper words that casual English drops: *that*, *then*, *the*,
  *a*, *an*, *of*. "Update the rules that you defined." "If the key isn't
  found, then the default is returned." Keep articles in headings: "Create a
  VM instance."
- Give every pronoun a clear antecedent. Put a noun after *this*, *these*,
  and *that*: "Set this value," not "Set this." Repeat the noun instead of
  *it* when either of two nouns might be meant.
- Use singular *they*. Never *he/she*, *(s)he*, or a gendered pronoun for a
  generic person.
- Use contractions (*don't*, *isn't*, *you're*). Readers skim past *not* but
  rarely misread *don't*. Don't invent contractions (*guides're*) or stack
  them (*mightn't've*).
- Use the simple word: *use* not *utilize* or *leverage*; *start* not
  *commence*; *so* not *consequently*; *about* not *regarding*; *because*
  not *since* or *as*; *to* not *in order to*; *before* not *prior to*;
  *after* not *subsequent to*; *if* not *in the event that*; *want* not
  *desire* or *wish*; *run* not *execute*; *stop* not *terminate* or *kill*;
  *extract* not *unzip*; *lets you* not *allows you to*.
- Where *using* is ambiguous, write *by using* or *that uses*: "Filter the
  roles by using custom permissions."
- Don't use *and/or*, slashes for alternatives, *etc.*, *and so on*, *e.g.*,
  *i.e.*, *via*, *vice versa*, *per* (except in rates like *requests per
  second*), or optional plurals in parentheses (*file(s)*). Write *for
  example*, *that is*, *such as*, and *one or more files*.
- Say what the reader can do, not what they can't. Avoid double negatives.
- Don't use directional words for position: not *above*, *below*, *left*,
  *right-hand*, *higher*, *lower*, or *under*. Use *preceding*, *following*,
  *earlier*, and *later*. For versions, use *earlier* and *later*, not
  *lower* and *higher*.

## 6. Tone in messages to the user

Sound like a knowledgeable colleague: conversational, friendly, and
respectful, without slang, jokes, or cuteness. Not formal, not chatty. Give
the information first; the reader might be in a hurry.

- Lead with the result or the answer, then the details: "The tests pass. I
  changed `parser.py` and `test_parser.py`." Don't write *successfully* or
  *I've successfully*; state the outcome.
- Report facts, including failures, plainly: "Two tests fail: `test_parse`
  and `test_render`. The output follows."
- Don't apologize as a reflex, and don't thank the reader for a task.
- Don't close with *Let me know if you'd like...*, *Hope this helps!*, or
  *Feel free to...*. If there is a real decision for the user to make, state
  it as a question in one sentence.

<!-- style-lint: off -->
Too informal: "Boom, auth is wired up and the tests are green!"
About right: "Authentication is implemented and the tests pass."
Too formal: "The implementation of the authentication mechanism has been
completed and validated by the test suite."
<!-- style-lint: on -->

## 7. Format text the same way everywhere

These rules apply in chat as well as in files. For a full document (a
README, a docs page, a procedure, a table, an image), read
[formatting.md](references/formatting.md) first.

- **Headings**: sentence case; no end period; no numbers, links, or bare
  code; don't start with an *-ing* word. Task headings start with a base verb
  ("Configure logging"); concept headings are noun phrases ("Logging
  overview"). Don't skip heading levels.
- **Bold** only for the names of UI elements and for run-in list headings.
  Don't bold for emphasis. **Italics** for a term that you're defining, a
  word as a word, or rare emphasis. Never underline.
- **Code font** for anything that is code or is entered or output verbatim:
  filenames, paths, commands, flags, identifiers, values, keywords, HTTP
  methods and status codes, environment variables, ports, IP addresses,
  package names, and output. Not for product names, plain domain names, or
  URLs that the reader visits in a browser.
- Add a noun after a code item and inflect the noun, not the code: "the
  `config.yaml` file," "the `--force` flag," "`Job` objects," "send a `POST`
  request" (not "POST the data"), "the `wordCount` method's return value"
  (not "`wordCount`'s value").
- **Lists**: introduce a list with a complete sentence that ends in a colon.
  Numbered for sequences, bulleted otherwise. Items are parallel in structure
  and start with a capital letter. End an item with a period if it's a
  sentence; no period for a fragment, a single word, code, or a link. Don't
  make a one-item list. For term-and-description pairs, use a bold run-in
  heading and a colon: "**Term**: description".
- **Punctuation**: serial comma. Em dash with no spaces for a break in a
  sentence; never a spaced hyphen or an en dash. Hyphen for ranges (2-5).
  Straight quotes. Avoid semicolons. No ellipses in prose. One space between
  sentences. No *&* for *and*.
- **Numbers**: spell out zero through nine; numerals for 10 and greater;
  always numerals for versions, technical quantities, units, percentages, and
  decimals ("version 3," "6 queries per second," "64 GB," "40%," "0.5").
  Spell out ordinals (*first*, not *1st*) and multipliers (*10 times*, not
  *10x*). Commas in numbers of four or more digits (2,000).
- **Dates and times**: "January 19, 2017" or "2017-04-15"; "3 PM"; no
  seasons.
- **Links**: link text is the page title or a descriptive phrase, never
  *click here*, *this document*, or a raw URL. Introduce a link with "For
  more information, see X" or "For more information about Y, see X."
  Punctuation goes outside the link.
- **Notices** (`**Note**:`, `**Caution**:`, `**Warning**:`) sparingly, and
  never for prerequisites, steps, results, or cross-references. If you're
  not sure that something needs to be a notice, write it as regular text.

## 8. Comments, docstrings, and reference text

Read [code-comments.md](references/code-comments.md) when you write or edit
docstrings, API reference comments, inline comments, commit messages, or PR
descriptions. The short version:

- Describe what the code does now, in present tense, third person: "Returns
  the user's ID." "Creates a task on the specified list." Not *This function
  will return* and not *Create a task* (the imperative is for instructions to the
  reader).
- Make the first sentence short and unique. Don't repeat the name. Don't use
  *e.g.* or another period in it, because doc generators cut the summary at
  the first period.
- Parameters: "The ID of the item to get." Booleans: "If true, validates the
  certificate. If false, trusts it without validating." Boolean returns:
  "True if the item exists; false otherwise." Exceptions: "Thrown when no key
  is assigned."
- A comment explains what the code does or why, in literal terms. It doesn't
  narrate how the code was written, what you tried first, or how you feel
  about it (*hack*, *ugly*, *clever*, *magic*).
- Don't pluralize class names: "`Intent` objects," not "`Intents`."

## Word choice

[word-list.md](references/word-list.md) condenses the guide's own word list:
terms to avoid, terms to use with caution, and their replacements, A to Z.
Open it when you're unsure whether a term is acceptable, and when the linter
flags a term that you don't recognize.

[llm-habits.md](references/llm-habits.md) lists the figurative, filler, and
hype terms and the formatting habits that LLM-written prose overuses, with
replacements. Read it the first time you apply this skill in a session, and
again if the user says your text still sounds like an AI wrote it.

[examples.md](references/examples.md) shows before-and-after rewrites of a
chat summary, a plan, a commit message, a PR description, a README section, a
docstring, and inline comments. Read it when you want a model for a specific
kind of text.

## Checklist

Check every reply, message, and file against this list before you send or
save it:

- Every term is literal, or an established term used in its technical sense.
  No metaphors, analogies, anthropomorphism, or idioms.
- No filler, softeners, hype, preambles, rhetorical framing, or exclamation
  points.
- The reader is *you*. Every sentence names who or what acts. Present tense.
  *Must*, *can*, *might*, or *We recommend*, not *should*, *will*, *may*,
  *could*, or *would*.
- Nothing anchors the text in time (*currently*, *new*, *soon*), and nothing
  claims *best*, *always*, *guaranteed*, or *secure*.
- Conditions come before instructions. Sentences are short. Paragraphs hold
  one idea, key point first.
- Headings are sentence case. Bold is for UI names only. Code is in code
  font with a noun after it.
- Lists are introduced, parallel, and punctuated consistently. Links describe
  their target. Serial commas are present.
- For files: `scripts/lint.py` reports nothing that you haven't deliberately
  kept.
