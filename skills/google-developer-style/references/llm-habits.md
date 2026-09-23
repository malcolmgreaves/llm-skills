# Terms and habits that LLM-written prose overuses

This file lists the figurative, filler, and hype terms, and the formatting
habits, that show up in text written by language models and that the Google
developer documentation style guide rules out. Each entry is an application
of the guide's rules on figurative language, jargon, tone, timeless
documentation, and excessive claims. For the guide's own word list, see
[word-list.md](word-list.md).

The replacement for a figurative term is never a synonym. It's the fact that
the term stood in for. *The cache is load-bearing* means something specific
about this cache; write that.

## Contents

- [Metaphors for structure and dependencies](#metaphors-for-structure-and-dependencies)
- [Metaphors for failure](#metaphors-for-failure)
- [Metaphors for actions](#metaphors-for-actions)
- [Metaphors for scope and planning](#metaphors-for-scope-and-planning)
- [Discourse filler](#discourse-filler)
- [Hype and unverifiable claims](#hype-and-unverifiable-claims)
- [Softeners and intensifiers](#softeners-and-intensifiers)
- [Vague verbs and constructions](#vague-verbs-and-constructions)
- [Anthropomorphism](#anthropomorphism)
- [Analogies](#analogies)
- [Abbreviations and slang](#abbreviations-and-slang)
- [Chat reflexes](#chat-reflexes)
- [Formatting habits](#formatting-habits)

## Metaphors for structure and dependencies

| Term | Write instead |
| --- | --- |
| load-bearing | State what depends on it: "Three services read this table. If it's unavailable, they fail." |
| seam | The boundary, interface, or module that you mean: "the boundary between the parser and the renderer" |
| wedge | The first change, the smallest change, or the change that the rest depends on |
| backbone, spine, skeleton, heart, core (of) | Name the component: "the request loop," "the `Scheduler` class" |
| crux, meat, gist, essence | "The cause is ..." or "In summary, ..." |
| scaffolding (figurative) | "starter code," "the initial project structure." Literal scaffolding tools are fine. |
| glue, glue code | "the code that converts between X and Y," "the adapter." Don't use *glue* as a verb. |
| plumbing, wiring | "the code that passes X from A to B," "the configuration that connects A to B" |
| wire up, hook up, plumb through, thread through, pipe through | connect, configure, pass X to Y, register |
| sits on top of, sits behind, lives in, hangs off | uses, calls, is in, is a field of, is behind (a proxy) |
| owns (a module owns X) | defines, creates, controls |
| surface area (of an API) | the number of public functions, endpoints, or types |
| footprint (except memory footprint) | size, number of files, disk usage |
| single source of truth, source of truth | "the one place where X is defined," "the authoritative copy" |
| first-class, second-class citizen | Describe what the thing can and can't do. (Guide: don't use.) |
| moving parts | components; count and name them |
| tight/loose coupling | Acceptable as established terms. Say what depends on what. |
| leaky abstraction | "The interface exposes X, which callers must know about." |

## Metaphors for failure

| Term | Write instead |
| --- | --- |
| chokes on, blows up on, falls over, dies, barfs, trips on | fails, returns an error, panics, exits with status N, raises `ValueError` |
| bails, bails out | returns early, exits |
| hangs, hung, wedged | stops responding, blocks, doesn't return (Guide: don't use *hang*.) |
| complains, screams, yells | reports an error, prints a warning, rejects the input |
| is confused, gets confused | misparses, misidentifies, treats X as Y |
| swallows, eats (an error) | catches and discards, catches and ignores, doesn't report |
| fails silently | "fails without reporting an error" (acceptable if you say what isn't reported) |
| bubbles up, trickles down, ripples | propagates, is re-raised, is passed to |
| blast radius | affected area, the set of affected services (Guide: don't use.) |
| footgun | Describe the mistake that the API invites: "Calling `close()` twice corrupts the file." |
| gotcha | Describe the behavior: "The default timeout is 0, which disables retries." |
| sharp edges, rough edges, papercuts | the specific problems; list them |
| code smell, smell | the specific problem: duplicated logic, a 400-line function |
| cruft | unused code, obsolete configuration |
| bloat, bloated | large; give the size or count |
| bit rot, rot | out of date, no longer compiles, untested since version X |
| brittle, fragile | "breaks when X changes," "fails if the order of Y changes" |
| flaky | Acceptable for tests that pass and fail without a code change. Say why if you know. |
| janky, wonky, borked, hosed, busted | broken; describe the symptom. (Guide: *jank* only for graphics.) |
| a hack, hacky, kludge, band-aid, duct tape | a workaround; state what it works around and what it costs |

## Metaphors for actions

| Term | Write instead |
| --- | --- |
| spin up, stand up, bring up | create, start, deploy (Guide: *spin up* only for disks.) |
| tear down | Acceptable for the cleanup step of a test fixture. Elsewhere: delete, stop, remove. |
| kick off, fire off | start, send, run |
| fires (an event fires) | Acceptable as an established term. Or: "the runtime calls the handler." |
| bake in, bolt on | include, build in; add |
| paper over | hide, conceal, suppress |
| punt, park, shelve, table | defer; say until when or what must happen first |
| ship, land, cut (a release) | release, merge, create a release |
| bump (a version) | increase, update to version N |
| flip (a flag, a switch) | set, enable, turn on |
| nuke, blow away, clobber, stomp on | delete, overwrite (Guide: don't use *nuke*.) |
| massage, munge | transform; say how |
| tweak, fiddle with, twiddle | adjust, change; say what and to what |
| sprinkle, pepper, litter | add to each of, add throughout |
| tease apart, untangle, unwind | separate, split into |
| reach for, lean on | use |
| hit (an endpoint, an API) | send a request to, call |
| surface (verb) | make available, expose, report (Guide: avoid.) |
| unlock, empower, harness, tap into, elevate, supercharge, turbocharge, streamline | lets you, use, improves X by Y percent, removes the need to Z |
| delve into, dive into, deep dive, drill down, dig into, unpack, zoom in on | describe, examine, explain; name the section |
| sanity check | quick check, confidence check, preliminary check (Guide: don't use.) |
| kick the tires | try, test |
| dogfood | use internally; define on first use |
| roll out | release in stages; define what you mean (Guide.) |
| canary | Acceptable as an established term for a staged release; define on first use. Not a verb. |

## Metaphors for scope and planning

| Term | Write instead |
| --- | --- |
| rabbit hole, in the weeds | details that don't affect the decision; say which |
| big picture, at a high level, 30,000-foot view | in summary; "this section summarizes" |
| low-hanging fruit, quick win | small changes with a large effect; name them |
| boil the ocean | change everything at once |
| yak shaving | prerequisite work; name it |
| bikeshedding | discussion of details that don't matter to the outcome |
| north star | goal, target metric |
| guardrails, safety net | limits, checks, validation; name them |
| belt and suspenders | a redundant check |
| escape hatch | a way to bypass X; name it |
| knob, dial, lever | setting, option, parameter |
| happy path | the case where every step succeeds; define on first use if you keep it |
| golden path, paved road | the recommended approach |
| table stakes | required |
| no-brainer, slam dunk | better because X; say why |
| silver bullet, holy grail, magic | Describe what the thing does and doesn't solve. |
| black box | Guide: avoid for testing and monitoring; use *opaque-box testing*, *synthetic monitoring*. |
| out of the box | by default, without configuration (Guide: literal use only.) |
| off the shelf | ready-made, prebuilt, standard (Guide.) |
| plug and play, drop-in, turnkey | requires no configuration; has the same interface as X |
| end-to-end, boilerplate, technical debt | Acceptable as established terms. Say what the debt is. |
| spaghetti, big ball of mud | Describe the coupling: "Every module imports every other module." |
| cargo cult | copied without understanding why; say what was copied |

## Discourse filler

Delete these. If the sentence needs a connector, use *so*, *because*,
*however*, or *for example*.

*at its core*, *essentially*, *basically*, *fundamentally*, *at the end of the
day*, *the bottom line*, *long story short*, *in a nutshell*, *the key
insight*, *the key takeaway*, *it's worth noting*, *note that*, *please
note*, *importantly*, *crucially*, *notably*, *that said*, *that being said*,
*with that said*, *having said that*, *going forward*, *moving forward*, *in
terms of*, *when it comes to*, *with respect to*, *as such*, *as you can
see*, *needless to say*, *obviously*, *clearly*, *of course*, *here's the
thing*, *the short answer is*, *to put it simply*, *simply put*, *let's*.

Rhetorical patterns to drop: *It's not X, it's Y* (say Y). *This isn't just
X; it's Y* (say Y). *Not only X but also Y* (say X and Y). Rhetorical
questions (*So what does this mean?*). Triplets added for rhythm (*fast,
reliable, and secure*) when you can verify only one.

## Hype and unverifiable claims

The guide calls these *excessive claims*. They can't be verified by the
reader and they become false. Replace each one with a measurable statement or
delete it.

*robust*, *seamless*, *seamlessly*, *elegant*, *clean* (as praise), *powerful*,
*blazing fast*, *lightning-fast*, *battle-tested*, *bulletproof*, *rock
solid*, *ironclad*, *airtight*, *production-ready*, *enterprise-grade*,
*best-in-class*, *world-class*, *cutting-edge*, *state-of-the-art*,
*next-generation*, *game-changer*, *revolutionary*, *comprehensive*,
*holistic*, *performant*, *future-proof*, *best*, *fastest*, *simplest*,
*perfect*, *always*, *never*.

Use *ensure* and *guarantee* only when the claim is literally true. Say that a feature *helps* secure X or *is designed for* X, not
that X *is secure*. *Scalable* needs a direction and a size: "scales to 10,000
concurrent connections on each node."

## Softeners and intensifiers

Delete: *simply*, *just*, *easily*, *easy*, *quickly*, *quick*,
*straightforward*, *trivial*, *trivially*, *a bit*, *a little*, *kind of*,
*sort of*, *pretty*, *fairly*, *quite*, *rather*, *somewhat*, *really*,
*very*, *extremely*, *incredibly*, *super*, *truly*, *definitely*,
*certainly*, *absolutely*, *actually*, *arguably*, *more or less*.

The guide's reason: the task might be harder or slower for the reader than
for you, and the sentence means the same thing without the word. *Just* is
acceptable in the sense of *only* when no other word fits.

## Vague verbs and constructions

| Term | Write instead |
| --- | --- |
| handles, deals with, takes care of, manages | the specific verb: parses, validates, retries, closes, routes |
| is responsible for | does; "the `Scheduler` class starts and stops jobs" |
| serves as, acts as, functions as | is |
| leverages, utilizes | uses |
| allows you to, enables you to, provides the ability to, makes it possible to | lets you; you can |
| ensures that | checks that; so that; or describe the mechanism |
| goes ahead and, proceeds to | delete |
| helps to | helps |
| supports X | say what works: "accepts X as input," "runs on X" |
| works with, plays nicely with, integrates with | is compatible with; say how |
| is aware of, knows about | reads, checks, has access to |
| expects | requires, accepts |
| wants, needs (of software) | requires |
| decides | selects X based on Y |
| assumes | Acceptable when literal: "assumes that the list is sorted." |

## Anthropomorphism

Software doesn't have intentions or feelings. Say what it does.

| Term | Write instead |
| --- | --- |
| the compiler complains | the compiler reports an error |
| the function is happy / unhappy | the function succeeds / fails; the check passes / fails |
| the parser sees an empty string | the parser reads an empty string |
| the service thinks the token is expired | the service rejects the token as expired |
| the cache remembers / forgets | the cache stores / discards |
| the client trusts the certificate | the client accepts the certificate without validating it |
| the module cares about ordering | the module requires sorted input |
| the code wants an integer | the function requires an integer |
| the test is confused by | the test misidentifies X as Y |

## Analogies

Don't use *think of it as*, *imagine*, *picture this*, *it's like a*, *similar
to how*, *analogous to*, or *metaphorically*. An analogy is figurative
language; describe the thing itself. If the user asks for an analogy, give
one and label it as an analogy.

## Abbreviations and slang

| Term | Write instead |
| --- | --- |
| tl;dr | To summarize; or delete the section and put the summary first |
| ymmv | Your results might vary |
| aka | also known as; or put the alternative in parentheses |
| fwiw, iirc, imo, imho, afaik, btw | delete, or state the fact |
| nit, lgtm, ptal, wip | delete; write the comment in full |
| +1 | agree; say why |
| e.g., i.e., etc., vs., w/, c/o | for example; that is; such as (and stop the list); versus; with; care of |
| k8s | Kubernetes |
| repo | repository |
| config (as a word) | configuration. Code font when it's a filename or identifier. |
| regex | regular expression |
| admin | administrator, unless it matches a UI label |
| auth | authentication or authorization; say which |
| env, dev, prod, db, fn, func, param, arg, var, deps, impl | environment, development, production, database, function, parameter, argument, variable, dependencies, implementation. Code font when it's a literal name. |
| docs | documentation, unless space is limited |
| 10x, 2x | 10 times, twice |
| 1st, 2nd, 3rd | first, second, third |

## Chat reflexes

These are habits in replies to the user rather than in documents. The guide's
tone rules cover them: give the information first, avoid exclamation points,
don't be cutesy, don't use *please*.

| Reflex | Write instead |
| --- | --- |
| Great question! Certainly! Absolutely! Sure! | Start with the answer. |
| You're absolutely right. | State the correction: "The default is 30 seconds, not 60." |
| I'd be happy to. I'll go ahead and ... | Do it, then report it. |
| I've successfully ... | State the result: "The tests pass." |
| Perfect! Done! All set! | "Done." is acceptable in chat. Or state the result. |
| I apologize for the confusion. | State the corrected fact. |
| Let me know if you'd like ... Feel free to ... Hope this helps! | Delete. If the user must make a decision, ask one question. |
| Let's dive in. Let's break this down. | Delete; start the explanation. |
| Here's what I did: (before a list) | Acceptable as a list introduction. Better: "I changed three files:" |
| This should work. | "This works when X." Or run it and report the result. |

## Formatting habits

| Habit | Write instead |
| --- | --- |
| Title Case Headings | Sentence case. |
| Bold for emphasis, bold key phrases in every bullet | Bold only UI element names and run-in headings. Let the words carry the emphasis. |
| Emoji, check marks, and symbols as bullets or labels | Words. |
| Em dashes joining clauses in every other sentence | A period. Em dash only for a real break, with no spaces. |
| Nested bullets three levels deep | Restructure: headings, or a paragraph for each topic. |
| A one-item list | A sentence. |
| Headings in a three-sentence reply | Paragraphs. |
| `**Note:**` boxes for ordinary sentences | Regular text. Notes are for information that the reader can skip. |
| Horizontal rules between sections | Headings, or nothing. |
| A table for text that isn't two-dimensional | A list. |
| A code block for text that isn't code | Regular text. |
| Arrows (→) and colons as sentence connectors | Words: *becomes*, *returns*, *then*. |
| "TL;DR" or "Summary" sections at the top | Put the summary first, without a label, or use a heading that names the topic. |
| Curly quotes, en dashes, the ellipsis character | Straight quotes, hyphens or em dashes, three periods (and only in output). |
| A colon after a fragment to introduce a list ("To do this:") | A complete sentence: "To do this, follow these steps:" |
