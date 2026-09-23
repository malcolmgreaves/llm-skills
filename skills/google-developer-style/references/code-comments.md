# Comments, docstrings, commit messages, and pull requests

How to apply the style guide to text that lives next to code. The API
reference rules are the guide's own (https://developers.google.com/style/,
"API reference code comments" and "Verb forms in reference documentation").
The guide doesn't cover inline comments, commit messages, or pull requests;
the sections on those apply its general rules and say so.

## Contents

- [What a comment is for](#what-a-comment-is-for)
- [API reference comments and docstrings](#api-reference-comments-and-docstrings)
- [Inline comments](#inline-comments)
- [Code samples in documentation](#code-samples-in-documentation)
- [Commit messages](#commit-messages)
- [Pull request descriptions](#pull-request-descriptions)
- [Changelogs and release notes](#changelogs-and-release-notes)
- [Error messages and help text](#error-messages-and-help-text)

## What a comment is for

A comment states a fact about the code that the code doesn't state itself:
what a function does, what a value means, why the code takes this path
instead of the obvious one, or which external constraint it satisfies. Every
rule in `SKILL.md` applies: literal language, present tense, active voice,
no filler, no hype, no time-anchored words.

A comment doesn't record:

- How the code was written or what you tried first.
- How you feel about the code (*hack*, *ugly*, *clever*, *magic*, *gross*).
- A restatement of the line under it (`i += 1  # increment i`).
- A promise about the future (*will be refactored*, *someday*). If work
  remains, say what it is and link to the issue.

## API reference comments and docstrings

Provide a description for every public class, interface, struct, constant,
field, enum, typedef, and method, with every parameter, the return value, and
every exception. Use the language's docstring format for the layout; these
rules govern the words.

### First sentence

- Short, unique, and descriptive. Doc generators extract it for lists of
  members, so it must stand alone.
- Third person, present tense, starting with a verb for methods: "Returns
  the user's ID." "Creates a task on the specified list." Not "Create a
  task" (that's an instruction to the reader), and not *This method will
  return*.
- Don't repeat the class or method name. Don't write "This class ..."
- No period before the real end of the sentence. Write *for example*, never
  *e.g.*, because some generators cut the summary at the first period.

### Classes, interfaces, and structs

- State the purpose in the first sentence with information that the name
  and signature don't already give.
- Follow with how to use the class: how to create or get an instance, the
  main features, prerequisites, and pitfalls.
- Include a short code sample (5 to 20 lines) at the top of each class page
  where the tooling allows.
- Spell class names exactly as in code, in code font, and link the first
  mention in a section. Don't pluralize a class name; add a noun: "`Intent`
  objects." A class whose name is a common word can be referred to by that
  word in ordinary font ("activities") when you mean the concept.
- String literals in code font with double quotation marks: `"wrap_content"`.

### Members

Keep constant and field descriptions as short as possible, and link to the
methods that use them.

### Methods

- First sentence: what the method does. Then why and how to use it,
  prerequisites, exceptions, and related APIs.
- Verb choice by kind of method:
  - Performs an operation and returns data: "Adds a bird to the list and
    returns its ID."
  - Getter returning a boolean: "Checks whether ..."
  - Other getter: "Gets the ..."
  - No return value: "Sets the ...", "Updates the ...", "Deletes the ...",
    "Registers ..."
  - Callback: "Called by the runtime when ..." Later: "Subclasses implement
    this method to ..."
  - Factory or convenience constructor: "Creates a ..."
- Document dependencies (a permission, an initialized client) and what
  happens without them: "the method throws `SecurityException`," "the
  method returns `null`."

### Parameters

- Capitalize the first word; end with a period.
- Non-boolean: start with *The* or *A*: "The ID of the bird to get." "A
  description of the bird."
- Boolean that controls behavior: "If true, validates the certificate before
  connecting. If false, trusts the certificate without validating it."
- Boolean that reports state: "True if the zoom is set; false otherwise."
- Don't put *true* and *false* in code font or quotation marks in these
  sentences.
- Defaults: explain the behavior for each value or range, then "Default:
  30."

### Return values

- As brief as possible; detail belongs in the class description.
- Non-boolean: "The bird with the given ID."
- Boolean: "True if the bird is in the sanctuary; false otherwise."
- If the method can return nothing, say so: "... or `None` if no bird
  matches."

### Exceptions

- Where the generator prints "Throws": "If no key is assigned."
- Otherwise: "Thrown when no key is assigned."

### Deprecations

- First sentence: what to use instead, and the version where it was
  deprecated if you track versions: "Deprecated since 2.3. Use
  `CameraPose` instead."
- Then why, and what the reader must change to keep their code working.

### Language-specific layouts

The rules for words are the same in every language. Layouts differ:

- Python: a one-line summary, a blank line, then `Args:`, `Returns:`,
  `Raises:` sections (Google Python style) or the project's format.
- Java and Kotlin: Javadoc or KDoc with `@param`, `@return`, `@throws`.
- JavaScript and TypeScript: JSDoc or TSDoc with `@param`, `@returns`,
  `@throws`.
- Go: a comment that starts with the name: "// Fetch returns the user with
  the given ID." Go's convention overrides the "don't repeat the name" rule.
- Rust: `///` doc comments with `# Arguments`, `# Returns`, `# Errors`, `#
  Panics`, `# Examples` sections.

## Inline comments

This section applies the guide's general rules; the guide doesn't address
inline comments directly.

- Present tense, literal, active: "The endpoint returns `count` as a string
  for accounts created before 2021." Not "the API is weird and gives us a
  string sometimes."
- Say why when the code is not the obvious way: "Sort before dedup because
  `unique` only removes adjacent duplicates."
- Cite the constraint when there is one: an issue number, an RFC, a
  documented limit.
- Wrap comments at 80 characters (or the project's limit) and match the
  project's comment style.
- If the project uses `TODO` comments, keep the project's format and make
  the text a task with an owner or an issue: `TODO(#412): convert the string
  form of count.` Not `TODO: clean this up someday`.
- Don't leave a comment that describes what you removed or why you changed
  it; that belongs in the commit message.

## Code samples in documentation

- Introduce every sample with a sentence that says what it shows.
- Two-space indentation (or the language's standard), spaces not tabs, lines
  under 80 characters.
- Omitted code is a comment in the language, not `...`.
- Descriptive names, not `foo`, `bar`, `baz`. Example domains, names, and
  addresses from `formatting.md`.
- Placeholders in `UPPER_SNAKE_CASE`, explained after the sample.
- Follow the language's style guide for the code itself.

## Commit messages

This section applies the guide's rules to commit messages; the guide doesn't
cover them. Follow the project's commit format (Conventional Commits, a
prefix convention, a length limit) first. Within it:

- Subject line: the change as a task heading. Base verb, sentence case, no
  period: "Add retries to the upload client." "fix(auth): reject expired
  tokens." Under about 72 characters. Describes what the change does, not
  what you did ("Refactored stuff," "WIP," "fixes").
- Body: what the problem was, why it happened, and what the code does now.
  Present tense for the new behavior. Name files, functions, and numbers.
  Say what didn't change if a reader might assume it did.
- Literal language. Not *flaky*, *janky*, *tweak*, *bump*, *clean up*, *snuck
  in*, *quick fix*, *simply*, *just*.
- No exclamation points, no emoji, no *please*.
- Include the attribution line that the project or the agent's environment
  requires, unchanged.

## Pull request descriptions

Same rules as commit messages, plus:

- First paragraph: what the change does and why, in two or three sentences.
  If the change is one of a series, say which one and what comes next.
- A list of the files or behaviors that changed, each with what it does now.
- A testing statement with the command you ran and its result: "`pytest
  tests/` passes locally (118 passed)." If you didn't run something, say so.
- Anything the reviewer must decide, as a direct question.
- No headings for a description under 200 words. No emoji in headings. No
  *This PR simply* and no *should be safe to merge*; the tests say
  whether it's safe.
- Include the attribution line that the project or the agent's environment
  requires, unchanged.

## Changelogs and release notes

Release notes are time-stamped content, so the guide allows *new*, *now*,
and *added* in them. Everything else still applies:

- Each entry states what changed and what the reader must do, in present
  tense: "The `--timeout` flag accepts a duration such as `30s`. Integer
  values are still accepted as seconds."
- Group by type (added, changed, fixed, removed, deprecated, security) if the
  project follows Keep a Changelog; otherwise follow the project's format.
- Link to the issue or pull request. No hype, no exclamation points, no
  internal jargon.

## Error messages and help text

- State what went wrong, where, and what to do: "Can't read `config.yaml`:
  line 12 has no value for `timeout`. Add a value in seconds, such as
  `timeout: 30`."
- Sentence case, one sentence for each idea, no exclamation points, no *please*,
  no *oops*, no blame ("you entered an invalid value" becomes "`--count` must
  be a positive integer; got `-3`").
- Help text for a command or option: a phrase or a sentence in present tense
  that says what the option does. "Retries failed uploads up to N times.
  Default: 3." End punctuation for sentences, none for phrases, consistent
  within the tool.
