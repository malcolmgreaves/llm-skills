# Formatting reference

Rules for documents longer than a chat message: READMEs, docs pages,
procedures, tables, code samples, and images. Condensed from the Google
developer documentation style guide (https://developers.google.com/style/,
Creative Commons Attribution 4.0). `SKILL.md` has the short version; this
file has the details.

## Contents

- [Headings and titles](#headings-and-titles)
- [Paragraphs](#paragraphs)
- [Lists](#lists)
- [Procedures](#procedures)
- [Tables](#tables)
- [Notices](#notices)
- [Links and cross-references](#links-and-cross-references)
- [Code in text](#code-in-text)
- [Code samples and commands](#code-samples-and-commands)
- [Placeholders](#placeholders)
- [UI elements](#ui-elements)
- [Text formatting summary](#text-formatting-summary)
- [Capitalization](#capitalization)
- [Abbreviations](#abbreviations)
- [Punctuation](#punctuation)
- [Numbers, units, dates, and times](#numbers-units-dates-and-times)
- [Possessives and plurals](#possessives-and-plurals)
- [Filenames and file types](#filenames-and-file-types)
- [Example names and addresses](#example-names-and-addresses)
- [Images](#images)
- [Markdown](#markdown)

## Headings and titles

- Sentence case: capitalize the first word, the first word after a colon,
  and proper nouns. No period at the end.
- Task-based headings start with a base verb: "Create an instance," not
  "Creating an instance." Concept headings are noun phrases: "Migration to
  the new API," not "Migrating to the new API." Don't start any heading with
  an *-ing* word unless there's no alternative (*Billing*, *Pricing*).
- Keep articles: "Create a VM instance," not "Create VM instance."
- One level-1 heading on each page, and it's the page title. Don't skip levels
  (an `###` only under an `##`). Don't leave a heading with no text under it
  before the next heading.
- No numbers to show sequence, no links, and no code items without a noun
  ("The `config.yaml` file," not "`config.yaml`"). Keep punctuation out of
  headings; punctuation is a sign that the heading is too long.
- Prefix an optional section with *Optional:* ("Optional: Customize the
  alias").
- To introduce a group of subsections, write "The following sections
  describe ..." Don't write "this section" or "these sections" to mean a
  group.
- Don't repeat the page title as a heading on the page.

## Paragraphs

- One idea in each paragraph, key point first. A paragraph longer than five or
  six sentences usually holds more than one idea. A one-sentence paragraph is
  fine.
- Shorter sentences, not fewer sentences.
- Left-align text. Don't force line breaks inside a sentence in rendered
  output (wrapping source lines is fine).

## Lists

- Numbered list for a sequence (steps, phases, priorities). Bulleted list
  for everything else, and make it clear whether every item is required.
  Description list (term plus description) for pairs.
- Introduce a list with a complete sentence, ending in a colon if the list
  follows immediately, or a period if a paragraph comes between. Don't
  complete the sentence with the list items: "Use the button for any of the
  following purposes:", not "Use the button to:". In procedures: "To get the
  driver, follow these steps:" or "To get the driver, do the following:".
- Start each item with a capital letter. End an item with a period if it's
  a sentence (or contains a verb). No period for a single word, a phrase
  without a verb, code, or a link. If punctuation ends up inconsistent,
  rewrite the items to be parallel or punctuate them all.
- Parallel structure: every item the same grammatical shape.
- A one-item list isn't a list. Set the item off some other way.
- Description list with run-in headings: bold the term, end it with a colon
  or a period (consistently within the list), then the description. After a
  colon, the description starts lowercase and ends without a period unless it
  contains a verb. After a period, it starts uppercase and ends with a
  period. Never a dash between term and description.
- Sub-items in a numbered list use lowercase letters, then lowercase Roman
  numerals.
- In a comma-separated list in a sentence, use the serial comma. Don't end
  with *etc.* or *and so on*; introduce the list with *such as* or *like*.

## Procedures

- Introduce with a sentence that adds context the heading doesn't give. If
  the heading says it all, skip the introduction.
- One action in each step. Combine only menu selections: "Click **File > New >
  Document**."
- Order within a step: location, then goal, then action, then result. "In
  the console, go to the **Monitoring** page." "To start a new document,
  click **File > New > Document**." "Click **Run**. The results appear after
  the query runs."
- Start each step with an imperative verb. Use complete sentences.
- If a step's goal might make it read as optional, use the colon form:
  "Sort the data by date: click **Sort**."
- Mark optional steps with *Optional:* at the start, not *(Optional)*.
- A single-step procedure is one bulleted sentence, not a numbered list.
- Don't repeat a procedure; link to it. Don't say *please*. Don't give
  keyboard shortcuts in steps; say *copy* and *paste*. If the reader must
  press Enter, put it in the step.
- Don't introduce a command with "run the following command"; say what the
  command does: "Deploy the load generator:".
- A complex step goes in this order: the action, the command, the
  placeholder explanations, more detail, the output, and the result in its
  own paragraph.
- Give one way to do the task, the shortest one that works with a keyboard
  alone. If you must document several, separate them into sections or tabs.
- List prerequisites before the procedure, not in a note in the middle.

## Tables

- Use a table when each item has three or more pieces of data. Two pieces:
  a description list. One piece: a bulleted list.
- Introduce every table with a complete sentence ("The following table
  lists ..."), because screen readers don't announce tables.
- Sentence case in every cell. Concise column headings with no end
  punctuation. Header cells only in the first row and first column.
- Don't merge cells. Sort rows logically, or alphabetically if there's no
  logic. Split a long or complicated table.
- No tables for layout, for code, for a long one-column list split into
  columns, or in the middle of a numbered procedure.
- With more than one table near each other, caption them "Table 1. Bird
  species" and refer to them by number: "as shown in table 2."

## Notices

- Types: *Note* (useful but not needed), *Caution* (proceed carefully),
  *Warning* (don't do this; data loss or security risk). *Success* only in
  interactive content.
- Format: `**Note**: All VPC networks include firewall rules.` The label is
  bold; the text after the colon starts with a capital letter.
- Use a note only when the information is relevant but not necessary, when
  interrupting the reader doesn't cost them, and when the information isn't
  part of the flow of the text.
- Never a note for a cross-reference, a prerequisite, a step, a result, or
  anything the reader needs to succeed.
- Readers skip notices. Two in a row lose their effect. If in doubt, write
  regular text.

## Links and cross-references

- Link text is the target's title in sentence case, or a descriptive phrase.
  Put the important words first. Keep it short. Never *click here*, *this
  document*, *here*, or a raw URL.
- Introduce a standalone cross-reference with "For more information, see X."
  Add "about Y" when the link text doesn't say what the reader gains by
  following it: "For more information about authentication, see X." Use *about*, not
  *on*. Use *see*.
- Link to a destination one time on a page, in the place where it helps
  most.
- Include the abbreviation in the link text: "[Google Kubernetes Engine
  (GKE)](...)". Include the noun with a code item: "the [`--hostname`
  flag](...)".
- Say when a link does something unexpected: downloads a file (and its
  type), opens email, or goes to another section of the same page ("see the
  X section of this document").
- Don't force links to open in a new tab. Don't use an external-link icon;
  say it in words if it matters.
- Punctuation goes outside the link. No quotation marks around linked text.
  An unlinked reference to a section uses quotation marks; to a book,
  italics.
- Provide context on the page instead of a link when a definition, a short
  explanation, or a couple of steps is all the reader needs.

## Code in text

Use code font (backticks) for these and anything else that is code:

attribute names and values, class names, command output, command-line
utility names (`gcloud`, `kubectl`, `curl`), data types, database row and
column names, defined constant values, DNS record types, HTML and XML element
names (without angle brackets), enum names, environment variables, filenames
and paths, folders and directories, HTTP content types, HTTP status codes
(`404 Not Found`), HTTP verbs (`POST`), IAM role names, IP addresses,
language keywords, method and function names, namespaces, placeholders,
package names, port numbers, query parameters, strings used in commands, and
text that the reader enters.

Ordinary font for: domain names in running text, names of products,
services, and organizations, and URLs that the reader visits in a browser
(better: link them with descriptive text).

Sometimes code font:

- Boolean values as data (`true`, `false`) in code font; the evaluation of a
  condition ("if true, validates ...") in ordinary font.
- A utility name in code font, the project name in ordinary font: "the
  `curl` command," "the curl project."
- An email address in code font when it's input or output; linked in
  ordinary font when it's a way to contact someone.

Grammar around code:

- Add a noun and inflect the noun: "the `ADDRESS` constant's value," "send a
  `POST` request," "`Intent` objects." Never "POST the data," "GETting,"
  "`Intents`," or "`close`ing."
- Refer to a method by name alone unless the class is needed to avoid
  ambiguity: "call its `get` method."
- An HTTP status code is "an HTTP `400 Bad Request` status code"; a range is
  "an HTTP `2xx` status code." Say *status code*, not *response code* or
  *error code*.
- A UI element whose text is code gets both bold and code font: "select
  **`my-net-2`**."
- No quotation marks around code unless they're part of the code.

## Code samples and commands

- Follow the language's style guide for indentation (usually two spaces, no
  tabs). Wrap lines at 80 characters.
- Mark omitted code with a comment in the language ("# Several lines are
  omitted here."), not `...`. Don't make a block with an omission
  click-to-copy.
- Introduce a sample with a sentence: a colon if the sample follows
  directly, a period if a paragraph comes between or the sentence isn't about
  the sample.
- Link to the command's reference page when you introduce it. Use as few
  arguments as the task needs; the reference has the rest.
- Make commands copyable without editing: only runnable text and
  placeholders. Keep `[optional]`, `{a|b}`, and `...` notation out of
  copyable blocks. Instead: drop the optional arguments, give one block for each
  variant, document variants in separate sections, or say in the
  introduction that the command contains optional arguments.
- Break a long command before a hyphen, underscore, or quotation mark;
  indent continuation lines by four spaces; end every line but the last with
  ` \` (Linux) or ` ^` (Windows).
- Show a prompt (`$`) when a block has several input lines; it's optional
  for one line. Don't show the current directory in the prompt. Put input and
  output in separate blocks.
- Show output only when the reader must copy or verify something. Introduce
  it with "The output is similar to the following:" or "The output is the
  following:". Mark omitted output lines with `...` on their own line.
- Document an option's description with end punctuation if it's a sentence
  and none if it's a phrase.
- Prefer *option* as the general term when the tool's own vocabulary
  (*flag*, *argument*, *parameter*) is more than the reader needs.

## Placeholders

- Uppercase with underscores: `PROJECT_ID`, `INSTANCE_NAME`. Never
  `apiName`, `api-name`, `YOUR_API_NAME`, or `MY_API_NAME`. Don't use *x* or
  `xxx` as a placeholder except where it's the convention (`2xx`).
- In Markdown, an inline placeholder is code font with italics:
  `` *`PROJECT_ID`* ``. Inside a code fence, plain `PROJECT_ID`.
- Explain a placeholder the first time it appears. One placeholder: "Replace
  `BUILD_ID` with the ID of the build." Two or more: "Replace the following:"
  then a list in order of appearance, each item "`PLACEHOLDER`: description"
  with a lowercase description. An example inside a description follows an
  em dash or *such as*.
- For placeholders in sample output: "This output includes the following
  values:" and the same list form.

## UI elements

- State the goal rather than the widget when the widget isn't the point:
  "Refresh the page," "Expand the **Advanced options** section." Name the
  widget when the reader needs help finding it.
- Bold the name of every UI element that has a visible label: buttons,
  menus, dialogs, windows, fields, tabs, checkboxes. Don't bold a product or
  feature name unless it's the label on the element.
- Match the label's capitalization, except use sentence case when labels
  are all caps or inconsistent.
- Don't use a UI label as a verb or a noun: "In the **Name** field, enter a
  name," not "Name the account."
- Terms: *window* (the application window), *page* (a web page or a console
  sub-page), *dialog* (a smaller window in front), *pane* or *panel* (a region
  in a window), *section* (a labeled group of controls), *menu* and *command*
  (an item in a menu), *navigation menu*, *toolbar*, *button*, *tab*, *box*
  or *field* (text entry), *list*, *checkbox*, *radio button*, *expander
  arrow*, *toggle*. Not *pop-up*, *drop-down*, *hamburger*, *kebab*, *zippy*.
- Menu paths: "Select **View > Tools > Developer Tools**," the whole path in
  one bold span. Only for menus, not for mixed elements.
- Icons: the icon's tooltip name in bold, with the icon before it. Never
  "click the bell icon." If the tooltip is missing, file a bug.
- Leave out an ellipsis that's part of a label: "click **Browse**."
- Verbs: *click* (mouse; never *click on*), *tap* (touch), *select* (an
  item, text, a checkbox), *clear* (a checkbox), *enter* (text; prefer to
  *type*), *press* (a key), *turn on* or *enable* (consistently), *drag*,
  *point to*, *hold the pointer over* (only when waiting matters), *go to*
  (not *scroll to*), *expand*.
- Prepositions: *in* a dialog, field, list, menu, pane, or window; *on* a
  page, tab, or toolbar.
- Keys: "Press Control+C." Uppercase letters. Spell out modifier names
  (Control, Command, Option, Shift); no symbols. "Control+C (or Command+C on
  macOS)." *Press* for a key; *enter* for text.
- No directional language: not *above*, *below*, *left*, *right-hand*. Add
  context ("On the Cloud Run toolbar, click **Refresh**") or a screenshot.
- Outside a procedure, give the element context: "in the **Current jobs**
  section of the service console."

## Text formatting summary

- **Bold** (`**`): UI element names and run-in headings, including notice
  labels. Nothing else.
- *Italic* (`_` in Markdown): a term you're defining ("A *Clos network* is
  ..."), a word as a word ("Don't use *&* as a conjunction"), an abbreviation
  introduction ("*Border Gateway Protocol* (*BGP*)"), titles of full-length
  works, mathematical and version variables (version 1.4.*x*). Emphasis
  rarely; the words carry it.
- Underline: links only.
- Code font: code in text, inline code, user input; code fences for blocks.
- Don't override fonts, sizes, or colors. Don't use *&* for *and* except in
  a UI label or a space-limited table heading.
- Quotation marks: titles of short works (articles, episodes) when not
  linked; a section title you can't link to; a direct quotation; a term used
  metaphorically that isn't established (and then consider not using it).
- Punctuation and quotation marks go outside link text.

## Capitalization

- Sentence case for headings, titles, captions, labels in figures, table
  cells, list items, glossary terms, and navigation.
- Don't capitalize to convey meaning (a capitalized *Pod* versus a lowercase
  *pod*). Don't use all caps or camel case except in official names, in
  abbreviations, or when matching code.
- After a colon, lowercase, unless what follows is a proper noun, a heading,
  a quotation, or a notice label.
- Product names in their official capitalization (title case for most).
  Feature names lowercase unless officially capitalized. Match a UI label
  when referring to the label.
- A lowercase official name stays lowercase at the start of a sentence, but
  rewrite the sentence to avoid it: "You can use macOS to run the app."
- A hyphenated word at the start of a sentence or heading capitalizes only
  its first element.
- Spell out an abbreviation in lowercase unless the long form is a proper
  noun: "data manipulation language (DML)."
- Don't name a casing style (*camel case*, *snake case*). Describe it and
  give an example: "no spaces, with the first letter of each word
  capitalized, such as `AssertionAccount`."
- Product names: don't put *the* before a product name unless it modifies
  something ("the Cloud Datastore options page"). Do put *the* before tool
  and API names ("the `gcloud` CLI," "the Transcoder API"). Use the full
  name; don't shorten it unless matching a label. Never as a verb, plural,
  or possessive; use it as a modifier ("a Chromebook computer").

## Abbreviations

- Spell out on first use with the abbreviation in parentheses, both in
  italics: "*Border Gateway Protocol* (*BGP*)". Then use the abbreviation.
  If a term appears once, include the abbreviation only if it's as common as
  the long form.
- Don't spell out abbreviations that are more familiar than their expansion:
  AI, API, DVD, HTML, PC, PDF, RAM, REST, URL, USB, XML, and units like MB
  and GiB.
- Don't abbreviate terms outside the document's main topic, and don't use
  abbreviations that your readers won't know.
- No periods in acronyms and initialisms. A period after a shortened word
  (*etc.*, *Dr.*), except date and time abbreviations and country and state
  abbreviations (US, CA). None after a short form that's a word (*app*,
  *demo*, *sync*).
- Prefer the common spelled-out form: *approximately*, not *approx.*;
  *10 times*, not *10x*.
- Plurals without an apostrophe: *APIs*, *OSes*. A unit with a number stays
  singular: *64 GB*. Match the number of the spelled-out term: "virtual
  machines (VMs)."
- Don't use an abbreviation as a verb: "Use SSH to connect," not *ssh into*.
- Don't use *e.g.*, *i.e.*, *tl;dr*, *ymmv*, *RTFM*, or similar. *Etc.* is
  acceptable when nothing else works; keep the period.
- If a heading introduces an abbreviation, define it in the first paragraph
  after the heading.

## Punctuation

- **Serial comma**: "zones, regions, and multi-regions."
- **Commas**: after an introductory word or phrase. Between two independent
  clauses joined by *and*, *but*, *or*, *so*, unless both are short.
  Not between an independent and a dependent clause unless the sentence
  misreads without it. Before *which* (nonrestrictive), not before *that*
  (restrictive). Not before *because* unless it starts a nonrestrictive
  clause. A semicolon, period, or em dash before *however*, *otherwise*,
  *therefore*, and a comma after.
- **Colons**: the text before a colon that introduces a list is a complete
  sentence ("The fields are defined as follows:", not "The fields are:").
  Lowercase after a colon in running text.
- **Em dashes** (—): a break in the sentence, no spaces on either side.
  Never a hyphen, a double hyphen, or an en dash in its place. Never to
  separate a term from its description; use a colon.
- **En dashes**: don't use. A hyphen or *to* for ranges.
- **Hyphens**: closed prefixes (*metadata*, *preprocessing*, *nonempty*),
  except after *self-* and *cross-*, before a capital or a number
  (*non-Google*, *post-2000*), to avoid a misreading (*re-sign*), and for
  consistency within a document. *Non-* is often hyphenated when the result is
  hard to parse (*non-integer*, *non-key*). Compound nouns closed
  (*webpage*, *hostname*, *tradeoff*, *workaround*). Compound modifiers
  before a noun hyphenated when it aids clarity (*well-designed app*,
  *Android-specific techniques*), not after a verb (*the app is well
  designed*), and never after an *-ly* adverb (*publicly available*). Avoid
  compound modifiers of more than two words. A number and a spelled-out unit
  before a noun (*64-bit system*, *five-minute wait*); not with an
  abbreviated unit (*200 GB disk*). Ranges: *8-20 files*, or *from 8 to 20
  files*, never *from 8-20*. Suspended hyphens: *one- or two-hour intervals*.
  No spaces around a hyphen.
- **Parentheses**: readers skip them, so nothing important goes inside.
  Keep them short; often commas or a second sentence work better. A whole
  sentence in parentheses keeps its period inside.
- **Periods**: one space after. None at the end of headings, table
  headings, or list items that aren't sentences. Inside quotation marks,
  except after a literal string in quotation marks ("enter `escape`," or
  "escape",). Don't end a sentence with a URL; move it or put it on its own
  line.
- **Quotation marks**: straight, double. Single only for a quotation inside
  a quotation and in code that uses them.
- **Semicolons**: avoid. Acceptable to join two closely related sentences,
  before *therefore* or *that is*, and to separate list items that contain
  commas.
- **Slashes**: only in code, paths, and URLs (backslashes for Windows
  paths). Not for alternatives (*and* or *or*), dates, fractions (*0.75*,
  *75%*), or abbreviations (*c/o*, *w/*). Not *and/or*.
- **Ellipses**: don't use in prose. Acceptable inside a quotation to mark an
  omission (three periods, with spaces around) and in output to mark omitted
  lines. Leave an ellipsis out of a UI label.
- **Exclamation points**: never in concept, reference, or procedural text.
  Only when part of code or a literal string.
- **Ampersand**: *and*, except in a UI label or a space-limited table
  heading.

## Numbers, units, dates, and times

- Spell out zero through nine and numbers that start a sentence (or rewrite
  the sentence). Numerals for 10 and greater, and always for version numbers,
  technical quantities (6 queries per second, 128 bits), page and step
  numbers, prices, numbers in math, negative numbers, decimals, percentages,
  dimensions, measurements, and ranges. A number next to a numeral is spelled
  out: "fifteen 100,000-byte files." Numbers under 10 in a sentence with
  numbers over nine are numerals.
- Casual quantities as words: "thousands of combinations."
- Ordinals as words: *first*, *twelfth*. Not *1st*.
- Commas in numbers of four or more digits: 2,000. Period for the decimal
  point; a leading zero on decimals under one (0.5). Decimals are plural:
  "1.0 inches."
- Percent: numerals with no space, *40%*. At the start of a sentence, "Forty
  percent."
- Fractions as decimals when possible. As words, hyphenated: *two-fifths*.
- Dimensions: *192x192*, lowercase *x*, no spaces. Exponents as superscripts,
  not `^`.
- Ranges: a hyphen with no spaces (2012-2016). With units, repeat the unit
  and use *to*: "-40 °C to 85 °C."
- Units: a nonbreaking space between the number and the unit (`64&nbsp;GB`),
  except currency, percent, and degrees of angle (\$10, 65%, 180°).
  Temperature: `50&nbsp;°C`. A number and abbreviated unit before a noun
  aren't hyphenated: "200 GB disk." Multiplied units are hyphenated:
  "5 vCPU-hours." *Per*, not a slash: "requests per day"; *Gbps*, not *Gb/s*.
  Say which currency: US\$10. Match the byte system: *MB* is decimal, *MiB*
  is binary.
- *k* for thousands only with a noun and no space: "55k download operations."
- Dates: "January 19, 2017"; "Tuesday, April 27, 2021"; "January 2017" (no
  comma). In a sentence, a comma after the year. If you must use numerals,
  ISO format: 2017-04-15, and pick a day greater than 12 in examples.
  Abbreviated only where space is limited, and then consistently: "Mon, Sep
  3, 2018."
- Times: 12-hour clock unless the product uses 24-hour. "3 PM," "3:45 PM,"
  uppercase with a space. *Noon* and *midnight* are fine. Ranges with a
  hyphen: "5-10 minutes." Time zones only when needed, spelled out with the
  UTC offset: "Pacific Standard Time (UTC-8)." Date before time: "May 4,
  2009, at 6 PM."
- No seasons (*summer* means different months in each hemisphere). Use
  months or quarters.
- Attach a practical implication to a number when you can (a cost, a limit,
  a link to a calculator).

## Possessives and plurals

- Possessives: add *'s* to singular nouns, including ones ending in *s*
  ("the class's quota"); an apostrophe alone to plurals ending in *s* ("the
  models' capabilities"). If the result is awkward, rewrite with *of*.
- No possessive of a product, feature, or company name used as a trademark,
  and no possessive of a code item: "the `wordCount` method's return value,"
  not "`wordCount`'s."
- Plurals: never with *'s*. Abbreviations like words: *APIs*, *IDEs*, *OSes*.
  Class names stay singular with a plural noun: "`Intent` objects."
- Subject-verb agreement with long subjects: "the number of entries is."
  Two subjects with *and* take a plural verb.
- "One or more tests fail" (plural). "More than one instance" (singular).
  No optional plurals in parentheses: "your API keys," not *key(s)*.

## Filenames and file types

- New files and directories: lowercase, hyphens between words
  (`query-data.html`), ASCII only, descriptive (not `document1.html`).
  Underscores only to match a directory that already uses them.
- Refer to a file in code font with the word *file* after it, spelled
  exactly as it is: "the `build.sh` file."
- Name a file type by its type, not its extension: "a PNG file," "a Bash
  file," "a YAML file," not "a `.png` file." Don't use a file type as a verb:
  "extract a zip file," not "unzip."

## Example names and addresses

- Domains: example.com, example.org, example.net.
- Email: a name from the following list at an example domain (dana@example.com),
  or a generic address (support@example.net).
- People: Alex, Amal, Ariel, Bola, Charlie, Cruz, Dana, Dani, Hao, Ira,
  Izumi, Jie, Kai, Kalani, Kim, Kiran, Lee, Lucian, Luka, Mahan, Noam, Nur,
  Quinn, Raha, Rosario, Sasha, Tal, Taylor, Tristan, Yuri. Surnames as an
  initial: "Quinn N." Use singular *they*; don't attach gender, and don't
  reinforce stereotypes in roles. Alice and Bob only when documenting a
  specification that uses them.
- Company: Example Organization.
- Phone: 800-555-0100 through 800-555-0199.
- IPv4: 192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24. IPv6: 2001:db8::/32.
- Project and resource names: descriptive, like `frontend-development` or
  `production-1`. Not `foo`, `bar`, `baz`.
- Never real personal data, real addresses, or real credentials.

## Images

- Use an image only when words can't do the job. Never an image of text,
  code, or terminal output.
- Introduce an image with a complete sentence. Alt text on every image: a
  sentence or noun phrase under 155 characters, with punctuation, no "image
  of," and consistent for repeated images. Empty alt text (`alt=""`) for
  decorative images and for screenshots that only repeat the text.
- Anything the image conveys must also be in the text. Caption format:
  "**Figure 1.** Description." Refer to it as "figure 1," never *the image
  above*.
- Crop screenshots to the relevant area. No personal data (cover it with a
  solid overlay, not a blur). SVG for diagrams if available, otherwise PNG,
  no transparent background. MP4, not GIF, for motion.

## Markdown

- `_italic_` and `**bold**`; underscores for italics are easier to tell
  from bold in source. Backticks for code; fences for blocks, with the
  language name on the fence.
- Headings with `#` marks, in hierarchy. Lists with `-` for bullets and `1.`
  for numbers.
- Indent with spaces, not tabs. Wrap source at 80 characters where the tool
  allows; the rendered paragraph is what matters.
- A custom heading anchor is lowercase with hyphens.
- An inline placeholder is `` *`PLACEHOLDER`* ``. Inside a fence, plain
  `PLACEHOLDER`.
- `&nbsp;` for a nonbreaking space between a number and its unit.
