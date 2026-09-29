# Software terms

STE lets you use words that are not in its dictionary if they are technical nouns
or technical verbs of a subject field (rules 1.5 and 1.12). A company usually
keeps these terms in a glossary. This file is the glossary of this skill for
software. The terms of the project come first. Use the names that the code,
the README, and the issue tracker use (rule 1.8).

`scripts/ste_lint.py` reads this file. It does not report the technical nouns
in the lists, and it reports the words in the jargon table.

## Contents

- [How to use technical terms](#how-to-use-technical-terms)
- [Technical verbs](#technical-verbs)
- [Technical nouns](#technical-nouns)
- [Jargon and slang](#jargon-and-slang)

## How to use technical terms

- Use one term for one item, and use it each time (rule 1.11). Do not use
  *the service*, *the backend*, and *the API* for the same item.
- Use a technical verb only with its technical meaning in the table. If an
  approved verb gives the same information, use the approved verb (rule 1.12).
  For example, write *start the server*, not *boot the server*, if the two
  verbs give the same information.
- Do not use a technical noun as a verb (rule 1.7). Write *make a branch*,
  not *branch from `main`*. A word can be a noun and a verb only if it is in
  the two lists (*build*, *commit*, *log*, *cache*).
- Keep a multi-word technical noun to three words or less (rule 2.1). Write a
  longer official name in full one time. Then use a short form (rule 2.2).
- If the reader possibly does not know a term, tell its meaning the first time
  that you use it.
- Put code, commands, file names, and identifiers in code font. Code font
  shows quoted text, and the linter does not examine it.

## Technical verbs

| Verb | Technical meaning | For other meanings, use |
| --- | --- | --- |
| *run* | To start a program, command, script, test, or job, and let it operate | *operate*, *do* |
| *build* | To compile source code and make a package or an executable file | *make*, *assemble* |
| *compile* | To change source code into machine code or bytecode | *change* |
| *call* | To start the operation of a function or a method | *tell* |
| *return* | To give a value back to the caller | *go*, *give* |
| *raise*, *throw* | To send an exception | *cause* |
| *catch* | To receive an exception and stop it | *hold* |
| *pass* | To give a value to a function. For a test or a check, to have a satisfactory result. | *give*, *satisfactory* |
| *fail* | For a test, a check, a build, a command, or a request: to have an unsatisfactory result, or to stop with an error | *if ... not*, *unsatisfactory* |
| *commit*, *merge*, *rebase*, *push*, *pull*, *fetch*, *clone*, *revert*, *cherry-pick*, *stash* | The Git operation of the same name | *send*, *get*, *connect* |
| *deploy* | To put a release into operation | This word is approved. |
| *install* | To put software on a computer, to let it operate there | This word is approved. |
| *import*, *export* | To load a module, or to write data in a format for a different program | *get*, *send* |
| *parse* | To read text and make a data structure from it | *read* |
| *render* | To make the output (HTML, an image, or text) from a template or data | *make* |
| *serialize*, *deserialize* | To change data into a format that you can store or send, or to change it back | *change* |
| *encode*, *decode*, *encrypt*, *decrypt*, *hash*, *sign* | The operation of the same name on data | *change* |
| *cache* | To keep a result for the next request that is the same | *keep* |
| *index*, *query* | To make a search index, or to get data from a database | *find* |
| *log* | To write a record to a log | *record* |
| *print* | To write text to the terminal or on paper | *write* |
| *load*, *save*, *open*, *close*, *delete*, *copy*, *paste*, *cut*, *rename* | The operation of the same name on a file, a record, or text | *remove*, *put* |
| *sort*, *filter*, *validate*, *format* | The operation of the same name on data | *put in sequence*, *make sure that* |
| *configure* | To set the options of a program. For one value, use *set*. | *set* |
| *enable*, *disable* | To set a function or an option to on or to off | *let*, *stop* |
| *update*, *upgrade*, *download*, *upload* | The operation of the same name on software or data | *change*, *send*, *get* |
| *boot*, *reboot*, *restart*, *abort*, *debug*, *process* | The operation of the same name in a computer system | *start*, *stop*, *find the cause of* |
| *click*, *type*, *enter*, *press*, *tap*, *swipe*, *scroll*, *drag* | The step of the same name that a user does on a screen or a keyboard | *push*, *write*, *go into* |
| *log in*, *log out*, *sign in*, *sign out* | To start or stop a session with a user name and a password | *start*, *stop* |
| *refactor* | To change the structure of code without a change to its function | *change* |
| *lint* | To examine code with a linter | *examine* |
| *mock* | To replace a dependency with a test object | *replace* |
| *publish* | To make a package or a message available to other users | *release*, *send* |

## Technical nouns

These lists give examples only. A word that names an item
or a process in software is a technical noun if developers know it.

- **Code**: *function*, *method*, *class*, *module*, *package*, *library*,
  *dependency*, *variable*, *constant*, *parameter*, *argument*,
  *attribute*, *field*, *property*, *interface*, *string*, *integer*,
  *boolean*, *array*, *list*, *dictionary*, *map*, *tuple*, *object*,
  *instance*, *exception*, *stack trace*, *return value*, *callback*,
  *thread*, *queue*, *buffer*, *pointer*, *regular expression*, *decorator*,
  *iterator*, *generator*, *coroutine*, *signature*, *docstring*,
  *comment*, *null*, *expected value*, *expected result*, *expected output*,
  *edge case*, *race condition*, *deadlock*, *memory leak*, *bug*,
  *regression*, *feature*, *feature flag*, *state machine*, *type hint*.
- **Files and tools**: *file*, *directory*, *folder*, *path*,
  *working directory*, *current directory*, *repository*, *branch*,
  *current branch*, *default branch*, *commit*, *tag*, *diff*, *patch*,
  *merge conflict*, *pull request*, *code review*, *reviewer*,
  *review comment*, *issue tracker*, *release*, *version*, *changelog*,
  *configuration file*, *environment variable*, *command*, *flag*,
  *subcommand*, *script*, *shell*, *terminal*, *command line*, *editor*,
  *compiler*, *interpreter*, *linter*, *formatter*, *debugger*, *profiler*,
  *unit test*, *integration test*, *test case*, *test suite*, *fixture*,
  *mock*, *build*, *pipeline*, *CI*, *job*, *workflow*, *container*,
  *image*, *cluster*, *node*, *virtual environment*, *lock file*,
  *setting*, *settings*, *shutdown*, *rollback*, *fallback*, *backup*,
  *timeout*, *retry*, *log*, *log file*, *logging*, *warning*.
- **Network and data**: *server*, *client*, *API*, *endpoint*, *request*,
  *response*, *header*, *payload*, *token*, *session*, *cookie*, *URL*,
  *host*, *port*, *database*, *table*, *row*, *column*, *index*, *query*,
  *schema*, *migration*, *transaction*, *record*, *event*, *message*,
  *topic*, *latency*, *throughput*, *load balancer*, *load balancing*,
  *caching*, *encoding*, *hashing*, *routing*, *rendering*, *mapping*,
  *binding*, *padding*, *streaming*, *billing*, *pricing*, *deployment*,
  *pod*, *secret*, *health check*, *host name*, *resolver*, *traffic*,
  *backoff*, *exponential backoff*, *idempotent call*, *history*,
  *root directory*, *default settings*, *dictionary comprehension*,
  *service*, *microservice*, *wait time*.
- **AI**: *model*, *large language model*, *prompt*, *context window*,
  *agent*, *tool*, *tool call*, *embedding*, *hallucination*, *skill*,
  *subagent*.
- **People**: *user*, *end user*, *developer*, *maintainer*,
  *contributor*, *operator*, *customer*, *on-call engineer*, *owner*.
- **Writing and documents**: *text*, *word*, *sentence*, *paragraph*,
  *reader*, *writer*, *heading*, *title*, *section*, *note*, *caution*,
  *table*, *figure*, *README*, *runbook*, *docs page*, *release notes*,
  *status report*, *style guide*, *glossary*, *writing rules*,
  *approved word*, *approved meaning*, *part of speech*, *technical noun*,
  *technical verb*, *proper noun*, *phrasal verb*, *modal verb*,
  *multi-word noun*, *simple present*, *simple past*, *simple future*,
  *past participle*, *present perfect*, *passive voice*, *active voice*,
  *topic sentence*, *key word*, *key phrase*, *vertical list*, *quoted text*,
  *code font*, *safety instruction*, *procedural text*, *descriptive text*,
  *connecting word*, *connecting phrase*, *sentence construction*,
  *noun*, *verb*, *adjective*, *adverb*, *article*, *pronoun*,
  *preposition*, *conjunction*, *subject*, *subject line*, *subject field*,
  *tense*, *perfect tense*, *progressive tense*, *verb form*,
  *possessive form*, *infinitive*, *contraction*, *abbreviation*,
  *identifier*, *modifier*, *punctuation*, *hyphen*, *dash*, *colon*,
  *comma*, *semicolon*, *parentheses*, *question*, *reply*, *vocabulary*,
  *checklist*, *data module*, *UI label*, *force push*.

## Jargon and slang

Rule 1.10 does not let you use regional words, slang, or jargon. Only a small
number of persons know them, and a translator cannot find them in a
dictionary. Replace each word with the fact that it gives.

| Word | Status | Use |
| --- | --- | --- |
| *footgun* (n) | jargon | Tell which error the design makes easy. |
| *gotcha* (n) | jargon | Tell the unusual operation that causes the error. |
| *nuke* (v) | jargon | *delete*, *erase* |
| *brick* (v) | jargon | "set the device to a condition in which it cannot operate" |
| *yak shaving* (n) | jargon | Tell the task. |
| *bikeshedding* (n) | jargon | Tell the decision that is necessary. |
| *LGTM* (n) | jargon | "The change is correct." Give the approval in the tool for code review. |
| *nit* (n) | jargon | "Small change, optional:" |
| *WIP* (n) | jargon | "This change is not complete." |
| *TL;DR* (n) | jargon | "Summary:" |
| *IIRC*, *AFAIK*, *FWIW*, *IMO*, *IMHO* (n) | jargon | Delete it, or write "I think that". |
| *happy path* (n) | jargon | "the procedure when no error occurs" |
| *sanity check* (n) | jargon | *check*, *basic test* |
| *flaky* (adj) | jargon | "a test that gives different results for the same code" |
| *hacky*, *kludge*, *janky* (adj) | jargon | Tell the problem. |
| *under the hood* (adv) | jargon | Delete it. Tell the function of the code. |
| *out of the box* (adv) | jargon | "with the default settings" |
| *load-bearing* (adj) | jargon | Tell which parts cannot operate without it. |
| *blast radius* (n) | jargon | Name the components that an error can stop. |
| *boilerplate* (n) | jargon | "code that is the same in each file" |
| *grok* (v) | jargon | *know* |
| *dogfood* (v) | jargon | "use the product in our own work" |
| *deep dive* (n) | jargon | *examine* (v), or tell the subject of the text |
| *low-hanging fruit* (n) | jargon | "the changes that are easy and that have a large effect" |
