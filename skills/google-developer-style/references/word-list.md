# Word list

A condensed, paraphrased version of the word list in the Google developer
documentation style guide, keeping the entries that apply to general
developer writing and leaving out entries that are specific to Google
products. The full list is at https://developers.google.com/style/word-list
(Creative Commons Attribution 4.0). For terms that LLM-written prose
overuses, see [llm-habits.md](llm-habits.md).

How to read an entry:

- **Don't use**: never use the term in prose. If it appears in code, use it
  only in code font and in direct reference to the code item.
- **Avoid**: use the term only if no precise alternative fits. Define it on
  first use.
- Everything else is a spelling, capitalization, or usage rule.

If a term isn't here, use the first spelling that Merriam-Webster lists, and
follow the project's existing usage.

## Contents

- [A](#a) [B](#b) [C](#c) [D](#d) [E](#e) [F](#f) [G](#g) [H](#h) [I](#i)
  [J](#j) [K](#k) [L](#l) [M](#m) [N](#n) [O](#o) [P](#p) [Q](#q) [R](#r)
  [S](#s) [T](#t) [U](#u) [V](#v) [W](#w) [Y](#y) [Z](#z)

## A

- **a, an**: choose by the sound that follows: *a SQL query* (pronounced
  "sequel"), *an SAP system*, *a FHIR store*, *an HTML file*.
- **abort**: avoid. Use *stop*, *exit*, *cancel*, or *end*. Acceptable for
  the Linux signal.
- **about versus on**: "For more information *about* X," not "*on* X."
- **above**: don't use for versions (use *later*), for a position in a
  document (use *earlier* or *preceding*), or for a position in the UI.
  Acceptable for a hierarchy.
- **access** (verb): avoid. Use *see*, *edit*, *find*, *use*, or *view*.
- **actionable**: avoid. Delete it, or write *that you can act on*.
- **admin**: write *administrator* unless you're matching a UI label.
- **agnostic**: don't use. Use *platform-independent* or the specific
  independence.
- **aka**: don't use. Write *also known as*, or put the alternative in
  parentheses.
- **allowlist, denylist** (verbs): don't use as verbs. Rewrite: "To allow
  requests from a range, add the CIDR block." Nouns are fine.
- **allows you to**: don't use. Use *lets you*.
- **alpha, beta**: lowercase unless part of a product name.
- **and/or**: don't use unless space is limited. Write *X, Y, or both*.
- **and so on**: avoid. See *etc.*
- **anti-pattern**: avoid, especially as a heading. Name the practice.
- **API**: a web API or a language API. Not a synonym for a method or class.
- **app, application**: *app* for end-user programs; *application* in set
  phrases and where the complexity matters.
- **appendix**: plural *appendixes*.
- **as**: if you mean *because*, write *because*.
- **as of this writing**: avoid. It's implied.
- **authentication, authorization**: users are *authenticated*; requests are
  *authorized*. "Authenticate *against*."
- **authN, authZ**: don't use.
- **autoscaling, autohealing, autopopulate**: one word, no hyphen.
- **autoupdate**: don't use. Write *automatically update*.
- **-aware**: avoid as a compound modifier (*healthcare-aware*).

## B

- **backend, frontend**: one word.
- **bare metal** (noun), **bare-metal** (adjective).
- **base64**: lowercase; code font only when it's a literal.
- **below**: same rules as *above*. Use *later* or *following*.
- **best effort**: avoid. Describe the behavior.
- **between, among**: *between* for distinct things (even more than two);
  *among* for members of a group.
- **big-endian, little-endian**: hyphenated, lowercase.
- **black-box, white-box, gray-box**: avoid for testing and monitoring. Use
  *opaque-box testing*, *clear-box testing*, *synthetic monitoring*,
  *introspective monitoring*.
- **blackhat, whitehat, grayhat**: don't use. Say *illegal*, *unethical*,
  *legal*, *ethical*.
- **blackhole** (verb): don't use. Write *dropped without notification*.
- **blacklist, whitelist, graylist**: don't use. Use *denylist*, *blocklist*,
  *allowlist*, *trustlist*, *provisional list*, or describe the action. For
  the verb, rewrite the sentence. In code, use the literal in code font once,
  then the replacement term.
- **blast radius**: don't use. Use *affected area*.
- **blind**: avoid *blind to*, *blind write*, *change blindly*. Use *ignore*,
  *unaware of*, *a write without a read*, *change without checking*.
- **blue-green**: hyphenated.
- **boolean**: code font and exact spelling for a language type; lowercase
  for the abstract type; *Boolean* for logic and mathematics.
- **break-glass**: don't use. Use *emergency access* or *manual fallback*.
- **brown bag**: don't use. Use *learning session* or *informal training*.
- **build cop, build sheriff**: don't use. Use *build monitor*.
- **button**: not a link. You *press* a mechanical button and *tap* an
  on-screen button.

## C

- **can**: permission, ability, an optional action, or a possible outcome.
- **canary**: not a verb. Define on first use.
- **cell phone, cellular**: use *mobile phone*, *mobile data*, *mobile
  network*. *Phone* alone is fine when clear.
- **chapter**: don't use for online documentation. Use *document*, *page*,
  or *section*.
- **check, uncheck** (checkboxes): use *select* and *clear*.
- **checkbox**: one word.
- **choose**: fine in general; for UI elements, use *select*.
- **chubby**: don't use. Use *unused* or *overextended*.
- **CLI**: don't use generically. Name the tool.
- **click**: not *click on*. *right-click*, *double-click*. On touch
  devices, *tap*.
- **click here**: don't use. Use descriptive link text.
- **clickthrough** (noun), **click through** (verb).
- **client**: in API docs, the client app. Not short for *client library*.
- **codebase, codelab**: one word.
- **cold, hot, warm** (failover, standby, spare): jargon. Define on first
  use.
- **colocate**: not *co-locate* or *colo*.
- **compliant**: use with caution. It's a strong claim.
- **comprise**: don't use. Use *consist of*, *contain*, or *include*.
- **config**: avoid as a word. Write *configuration*; code font for a
  literal name.
- **cons, pros**: don't use. Use *disadvantages*, *advantages*.
- **console**: name the specific console, with *the*. A sub-page of a
  console is a *page*.
- **Control+S**: `Control+CHARACTER`, uppercase letter. Not *Ctrl-S* or
  *Cmd-S*. Give the macOS form in parentheses: "Control+S (Command+S on
  macOS)."
- **copy and paste**: avoid. Say what to enter where.
- **could**: avoid. Use *can*.
- **CPU**: all caps, no expansion.
- **crazy, insane, mad, bonkers, loony**: don't use. Use *complicated*,
  *baffling*, *strange*, or *unexpected*, and only for things.
- **Create a new ...**: write *Create a ...* unless you're distinguishing it
  from an item that you created earlier.
- **cripple**: don't use. Write *slowed*, or describe the effect.
- **currently**: avoid. It's implied.
- **curl**: not *cURL*.

## D

- **dash**: not the same as a hyphen. Don't call a hyphen a dash.
- **dashboard**: lowercase unless part of a product name.
- **data**: singular mass noun. *The data is*; *less data*.
- **data center, data source, data type**: two words. **datastore**: one
  word. **data flow** (flow of data) versus **dataflow** (the programming
  model).
- **dead-letter queue**: define on first use.
- **deficient, deformed**: not for people.
- **demilitarized zone (DMZ)**: don't use. Use *perimeter network*.
- **denigrate**: don't use. Use *disparage*.
- **deprecate**: to recommend against. Not a synonym for *removed*.
- **deselect**: not for checkboxes (use *clear*).
- **desire, desired**: don't use. Use *want* or *need*.
- **dialog**: the UI element. *Dialogue* is conversation.
- **directory, folder**: *directory* in command-line contexts, *folder* in
  GUIs. Default to *directory*.
- **disable**: not for something broken. Prefer *inactive*, *unavailable*,
  *turn off*, *deactivate*, used consistently.
- **display** (verb): transitive only. "The pane appears" or "is displayed,"
  not "the pane displays."
- **document, documentation**: *this document*, not *this article*, *this
  topic*, *this doc*, or *this page*. Spell out *documentation*.
- **does not yet**: avoid. Write what's true now.
- **dojo**: don't use. Use *training* or *workshop*.
- **double-tap**: hyphenated.
- **downscope**: prefer *reduce the scope*; define if you use it.
- **drag**: not *click and drag* or *drag and drop* (the adjective
  *drag-and-drop* is fine).
- **drop-down**: usually omit; write *list* or *menu*. Never a noun.
- **dumb down**: don't use. Use *simplify*.
- **dummy variable**: don't use. Use *placeholder*.

## E

- **each**: individual items, not all of them. *A list of the items*, not
  *a list of each item*.
- **earlier, later**: for versions and for positions in a document. Not
  *lower*, *higher*, *above*, *below*.
- **easy, easily**: avoid. Delete the word.
- **ecommerce**: no hyphen.
- **e.g.**: don't use. Use *for example* or *such as*.
- **either**: two things, with parallel syntax: "either do X or do Y."
- **element, tag**: a tag marks the start or end of an element. Don't call
  an element a tag.
- **email**: not *e-mail*. Not a verb: *send email*.
- **emoji**: plural *emoji*.
- **enable**: for a UI action, use the label's verb (*turn on*, *select*).
  For capability, use *lets you*, not *enables you to*. Use *enable* or
  *turn on* consistently within a document.
- **endpoint**: one word.
- **enter**: for text that the user enters. Prefer to *type*.
- **error-prone**: hyphenated.
- **etc.**: avoid, with *and so forth* and *and so on*. Introduce the list
  with *such as* or *including* instead.
- **eventually**: avoid.
- **execute**: use *run* when it means the same thing.
- **expander arrow**: not *disclosure triangle*, *expando*, or *zippy*.
- **exploit**: only in the security sense. Not a synonym for *use*.
- **extract**: not *unarchive*, *uncompress*, *untar*, or *unzip*.

## F

- **fail over** (verb), **failover** (noun, adjective).
- **fat**: don't use figuratively. Use *high-capacity*, *full-featured*.
- **female adapter, male adapter**: don't use. Use *socket*, *plug*.
- **filename**: one word. **file system**: two words.
- **fill in** (a field), **fill out** (a form).
- **final solution**: don't use.
- **first-class, first-class citizen**: don't use. Describe the capability,
  or use *higher-order*, *nested*, *anonymous*.
- **following**: "the following table," or "do the following:" without a
  noun.
- **foo, bar, baz**: avoid. Use meaningful names.
- **for example**: follow with a comma. Set the example off with a comma, an
  em dash, or parentheses, or make it a separate sentence.
- **for instance**: don't use. Use *for example*.
- **functionality**: use with caution. Often *features* or *capabilities* is
  what you mean.
- **future, in the future**: avoid.

## G

- **Gbps, GBps, Mbps, MBps, Kbps, KBps**: not *Gb/s*.
- **gender-neutral he or she**: don't use. Use singular *they*.
- **generative AI**: spelled out, lowercase. Not *gen AI*.
- **ghetto**: don't use. Use *clumsy*, *inelegant*, *workaround*.
- **gimp, gimpy, lame**: don't use. Describe the deficiency.
- **Google** (verb): don't use. Write *search with Google*.
- **grandfathered**: don't use. Use *legacy*, *exempt*, or *made an
  exception*.
- **grayed-out**: don't use. Use *unavailable*.
- **guru, ninja, sherpa, rockstar**: don't use for people. Use *expert*,
  *guide*.
- **guys, you guys**: use *everyone* or *folks*.

## H

- **hamburger menu, kebab menu**: don't use. Use the icon's label.
- **hands-off, hands-on**: use *automated*, *customizable*, or describe the
  activity.
- **hang, hung**: don't use. Use *stops responding* or *not responding*.
- **hardcode, hardcoded**: one word.
- **healthy, health check**: use with caution. Prefer *responsive*, and use
  *health check* only when the interface uses it.
- **high availability** (noun), **high-availability** (adjective); *HA*
  after first use.
- **higher, lower**: not for versions (use *later*, *earlier*), documents,
  or UI positions.
- **hit**: not a synonym for *click*, *press*, or *type*.
- **hold the pointer over**: only when the user must wait for the UI to
  react. Otherwise *point to*. Never *hover*.
- **holidays, the holidays**: name the months or quarter.
- **hostname**: one word.
- **hotspot**: noun only; not *hotspotting*.
- **housekeeping**: don't use. Use *maintenance* or *cleanup*.
- **HTTPS**: not *HTTPs*.

## I

- **IaaS, PaaS, SaaS**: spell out on first mention.
- **ID**: not *Id* or *id* outside code.
- **i.e.**: don't use. Use *that is*.
- **if ... then**: keep *then*.
- **image**: add context: *disk image*, *container image*.
- **impact**: noun only. For the verb, use *affect*.
- **index**: plural *indexes* outside mathematics and finance.
- **ingest**: only when significant processing is involved. Otherwise
  *import*, *load*, or *copy*.
- **in order to**: use *to*, unless *in order to* prevents a misreading.
- **inline**: one word.
- **interface** (verb): don't use. Use *interact*, *communicate*, *talk to*.
- **internet, web**: lowercase.
- **I/O**: with the slash.

## J

- **jank, janky**: only for graphics glitches. Otherwise describe the
  problem.
- **just**: avoid. Delete it, or use *only*, *instead*, or *previously*.
  Acceptable in the sense of "or just `example-kind`."

## K

- **k8s**: don't use. Write *Kubernetes*.
- **kebab case**: don't use. Write *dash-case*.
- **key** (adjective): don't use to mean *important*. As a noun, say which
  kind of key.
- **key pair** (two keys) versus **key-value pair** (a variable and its
  value).
- **kill**: avoid. Use *stop*, *exit*, *cancel*, or *end*. Acceptable for
  signals.

## L

- **latest**: avoid. If you must, give a version or date.
- **learnings**: don't use. Use *knowledge* or *what you learned*.
- **left-nav, right-nav**: don't use. Use *navigation menu*.
- **legacy**: prefer a precise term. Define it; never as an insult.
- **let's**: don't use.
- **leverage**: avoid. Use *use*, *build on*, or *take advantage of*.
- **lifecycle**: one word.
- **like**: fine for comparisons and for examples.
- **limits, quota**: say which kind: *usage limit*, *service limit*.
- **load balancing** (noun), **load-balancing** (adjective).
- **login** (noun, adjective), **log in** (verb). Prefer *sign in* unless the
  tool says *log in*.
- **long-running operation**: hyphenated; *LRO* after first use.

## M

- **man-hours, manpower, manned, manmade**: use *person-hours*, *staff*,
  *staffed*, *artificial*.
- **man-in-the-middle**: use *on-path attacker* or *person-in-the-middle*.
- **Markdown**: capitalized.
- **master**: use with caution; never with *slave*. Prefer *primary*,
  *main*, *parent*, *controller*, *leader*, *original*. In code, code font
  once, then the replacement term.
- **matrix**: plural *matrixes* outside mathematics.
- **may**: reserve for policy and legal text. Use *can* or *might*.
- **media type**: not *MIME type*. *Content type* when you mean the header.
- **method**: in class-based contexts, don't also use it to mean *approach*.
- **microservices**: lowercase, one word.
- **might**: possibility or an uncertain outcome.
- **mobile**: not a noun. *Mobile phone*, *mobile device*.
- **mom test, grandmother test**: don't use. Use *novice user test*.
- **monkey test**: don't use. Say *automated random tests*.
- **multi-cluster, multi-service, multi-tenancy, multi-region**: hyphenated
  (exceptions to the closed-prefix rule).
- **must**: a requirement. Or *you need*.

## N

- **N/A**: not *NA*. Spell out on first use.
- **name server**: two words. **namespace**: one word.
- **native**: not for people. For software, prefer *built-in*.
  *Cloud-native* is ambiguous; say what you mean.
- **navigation bar**: don't use for a navigation menu.
- **neither ... nor**: not *neither ... or*.
- **new, newer**: avoid. Give a version or date. For versions, use *later*.
- **nonce**: use with caution; define on first use.
- **non-key**: hyphenated.
- **NoOps**: don't use. Use *fully managed*.
- **NoSQL**: no hyphen.
- **now**: avoid unless you're contrasting past and present versions.
- **nuke**: don't use. Use *remove* or *attack*.

## O

- **OAuth 2.0**: not *OAuth2*.
- **off-the-shelf**: use *ready-made*, *prebuilt*, *standard*, or *default*.
- **old, older**: use *earlier*, with a version number.
- **omnibox**: don't use. Use *address bar*.
- **once**: if you mean *after*, write *after*.
- **on-premises**: hyphenated in every use. Not *on-prem* or *on premise*.
- **OS**: fine.
- **out of the box**: literal use only.

## P

- **page**: a web page, or a sub-page of a console.
- **path**: not *filepath* or *pathname*.
- **per**: only for rates (*requests per second*). Not *per the guide* (use
  *according to*) or *per Pod* (use *for each Pod*).
- **performant**: avoid. Say what is fast or accurate.
- **persist**: not a transitive verb. Prefer *persistent*.
- **personally identifiable information (PII)**: this spelling.
- **pets versus cattle**: don't use. Use *manually configured versus
  automated*.
- **plain text**; **plaintext** in cryptography.
- **please**: don't use in instructions. Never *please note*. Only when
  asking for permission or forgiveness.
- **plugin** (noun), **plug-in** (adjective), **plug in** (verb).
- **point to**: pointing without waiting.
- **POJO**: only for a Java audience. Otherwise *simple object*.
- **pop-up, popup**: don't use. Use *dialog* or *menu*.
- **populate**: for a process. A person *fills in* a form.
- **port**: *listen on*, not *listen to*.
- **possible, impossible**: not to mean *you can* or *you can't*.
- **postmortem**: use *retrospective*, except *blameless postmortem* in
  incident-response contexts.
- **practitioner**: name the roles.
- **prebuilt, precapture, preemptible, prerecorded, presubmit**: closed.
  **pre-existing, pre-shared key**: hyphenated.
- **presently, at present**: avoid.
- **press**: keys and mechanical buttons. *Tap* on-screen buttons.
- **primitive**: not disparagingly.

## Q

- **quick, quickly**: avoid. Delete the word.

## R

- **RDP**: not a verb. *Connect using RDP.*
- **read-only**: always hyphenated.
- **redline**: not a verb.
- **regex**: don't use. Write *regular expression*.
- **rehost**: associate with *lift and shift* on first mention. Not *the
  forklift approach*.
- **repo**: don't use. Write *repository*.
- **REST**: don't expand it.
- **retriable, retryable**: write around: *can be tried again*.
- **review**: only for a critical read. If you mean *read*, write *read*.
- **RFC 2318**: with a space.
- **roll out**: not for an instantaneous launch. Prefer *in stages*,
  *gradual*, or define it.
- **RTFM**: don't use. Write *For more information, see ...*
- **runbook**: one word.
- **runtime** (the environment) versus **run time** (the time of execution).

## S

- **sane**: don't use. Use *valid* or *sensible*.
- **sanity check**: don't use. Use *quick check*, *confidence check*,
  *preliminary check*, or *coherence check*.
- **scale**: give a direction and magnitude: *scales up*, *at a larger
  scale*. Not *at scale* alone.
- **screenshot**: one word; not a verb (*take a screenshot*).
- **scroll**: prefer *go to*. Never *scroll up* or *scroll down*.
- **see**: fine for links and cross-references.
- **select**: choose an item, select text, or mark a checkbox.
- **sensitive** (harmful if released) versus **confidential** (protected
  from unauthorized access).
- **service level agreement, service level indicator, service level
  objective**: lowercase; *SLA*, *SLI*, *SLO* after first use.
- **setup** (noun, adjective), **set up** (verb).
- **sexy**: don't use. Use *fast*, *powerful*, or *elegant*.
- **shall**: avoid, except on legal advice.
- **shift left**: use *shift earlier* or *move to an earlier phase*.
  Acceptable for bit operations.
- **should**: avoid. Use *must*, *can*, *might*, or *We recommend*.
- **sign in, sign out** (verbs); **sign-in, sign-out** (nouns, adjectives).
  *Sign in to*, not *sign into*. Not *log in* or *signin*.
- **simple, simply**: avoid. Delete the word.
- **since**: if you mean *because*, write *because*.
- **single pane of glass**: avoid. Use *single interface*.
- **slave**: don't use. Use *worker*, *replica*, *secondary*, *follower*,
  *subscriber*, *responder*, paired with the matching term for *master*.
- **slice and dice**: don't use. Say *segment the data for analysis*.
- **smartphone**: use *mobile phone* or *phone*.
- **soon**: avoid.
- **spin up**: avoid except for disks. Use *create* or *start*.
- **ssh, SSH**: not verbs. "Connect by using SSH." "Use the `ssh` command."
  Never *ssh into* or *ssh'ing*.
- **startup** (noun, adjective), **start up** (verb).
- **status bar**: two words.
- **STONITH**: avoid. Write *fence failed nodes*.
- **style sheet, stylesheet**: either, consistently.
- **sub-command**: hyphenated. **subnet, subtree, subzone**: closed.
- **such as**: introduces a non-exhaustive list. Don't add *etc.*
- **surface** (verb): avoid. Use *make available*, *expose*, or *report*.

## T

- **tab**: for a console sub-page, use *page*.
- **tap**: on touch devices, instead of *click* and *touch*. *Touch & hold*
  is the exception.
- **tarball**: don't use. Write *tar file*.
- **target** (verb): avoid, especially for people. *Intended for*, *focused
  on*. The adjective *target audience* is fine.
- **terminate**: avoid as a synonym for *stop*. Fine for signals and for
  telephony and networking senses.
- **text box**: write *box*, or *field* in console and Workspace contexts.
- **then**: keep it in *if ... then* sentences.
- **they**: the singular gender-neutral pronoun. It takes a plural verb.
- **third party** (noun), **third-party** (adjective). Not *3rd party*.
- **this, that**: put a noun after them.
- **timeframe**: avoid. Use *period*, *schedule*, *deadline*, or *when*.
- **timeout** (noun), **time out** (verb). **timestamp**: one word.
- **time to live**: no hyphens; *TTL* after first use.
- **time zone** (noun), **time-zone** (adjective).
- **tl;dr**: don't use. Write *To summarize*, or restructure.
- **toolkit, touchscreen, walkthrough, whitespace, wildcard**: one word.
- **traditional, traditionally**: prefer a precise term: *conventionally*,
  *on-premises*.
- **tribal knowledge**: don't use. Say *knowledge held by the team*.
- **turn on, turn off**: fine; use consistently with *enable*.
- **type**: prefer *enter*, because text can also be pasted or dictated.
- **typically**: not as the first word of a sentence.

## U

- **UI**: not generically. Use *page*, *console*, or *web interface*.
- **unarchive, uncompress, untar, unzip**: don't use. Use *extract*.
- **uncheck, unselect**: don't use. Use *clear* for checkboxes.
- **under**: not for versions (*earlier*) or UI positions ("In the **Name**
  field," not "Under **Name**").
- **Unicode**: not *UNICODE*. **Unix-like**: hyphenated.
- **US**: not *U.S.*
- **user**: only the users of the software that the reader builds. The
  reader is *you*.
- **using**: when ambiguous, write *by using* or *that uses*.
- **UTF-8**: with the hyphen.
- **utilize**: don't use to mean *use*. *Utilization* is fine for a measured
  quantity.

## V

- **v** (for version): lowercase.
- **via**: don't use. Use *by using*, *through*, or *with*.
- **vice versa**: don't use. Write out both directions, or use *conversely*.
- **virtual machine (VM) instance**: spell out on first mention.
- **voila**: don't use.
- **voodoo**: don't use. Use *mysterious*, *complicated*, or
  *nondeterministic*.
- **vs.**: don't use. Write *versus*.

## W

- **wake lock** (noun), **wake-lock** (adjective).
- **war room**: don't use. Use *incident-management team* or *situation
  room*.
- **we**: not for the reader. Only for the authoring organization, with a
  clear antecedent.
- **WebAssembly, Wasm**: this capitalization.
- **webmaster**: don't use. Use *website owner* or *website administrator*.
- **web server**: two words.
- **whether**: use *whether* for alternatives; add *or not* only when it
  means *regardless*.
- **while**: not for contrast (use *although*). Fine for time.
- **white glove, white label**: use *premium*, *unbranded*.
- **whitepaper**: one word; prefer a precise term.
- **will**: avoid. Use present tense. Same for *would*.
- **wish**: don't use. Use *want* or *need*.
- **with**: not for ownership (*a phone that has 2 GB*) or means (*use the
  debugger to*).
- **workload**: define on first use, or use a precise term.
- **World Wide Web**: don't use. Write *web*.
- **would**: avoid. Use *can*.

## Y

- **ymmv**: don't use. Write *Your results might vary*.
- **you**: how to address the reader.

## Z

- **zippy**: don't use. Use *expander arrow*.
