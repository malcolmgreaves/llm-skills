# Vocabulary

This file gives the STE decision for words that occur frequently in replies,
plans, code comments, and software documents. It is not the STE dictionary.
The dictionary has approximately 2,100 entries. ASD has the copyright of the
dictionary, and a copy of it in this skill is not permitted. This file has
approximately 250 entries.

Each decision agrees with ASD-STE100 Issue 9. For a word that the dictionary
does not include, the *Use* column gives the recommendation of this skill.

`scripts/ste_lint.py` reads the tables in this file. Thus, keep the format of
each row. The first cell gives the word in italics and its part of speech. The
second cell gives the status.

## Contents

- [How to read the tables](#how-to-read-the-tables)
- [When a word is not in this file](#when-a-word-is-not-in-this-file)
- [Modal verbs and helper verbs](#modal-verbs-and-helper-verbs)
- [Certainty and degree](#certainty-and-degree)
- [Connecting words](#connecting-words)
- [Time and frequency](#time-and-frequency)
- [Quantity](#quantity)
- [Verbs](#verbs)
- [Nouns](#nouns)
- [Pronouns and question words](#pronouns-and-question-words)
- [Adjectives](#adjectives)
- [Prepositions and phrases](#prepositions-and-phrases)
- [Phrasal verbs](#phrasal-verbs)
- [Approved modal verbs and connecting words](#approved-modal-verbs-and-connecting-words)

## How to read the tables

The *Status* column has one of these values:

- **not approved**: The STE dictionary gives the word as not approved. The
  *Use* column gives the approved alternatives.
- **not listed**: The STE dictionary does not include the word. Thus, you can
  use it only as a technical noun or a technical verb.
- **noun only**, **verb only**: STE gives approval to the word only as that
  part of speech.
- **technical noun only**: The word is not approved in general text. But
  software uses it as a technical noun. Refer to
  [software-terms.md](software-terms.md).
- **restricted**: STE gives approval to the word, but only with the meaning in the
  *Use* column.
- **phrasal verb**: Rule 9.3 does not let you use it.

The linter reports an error for *not approved*, *not listed*, and *phrasal
verb*. It gives a warning for *noun only*, *verb only*, and *technical noun
only*, because it cannot find the part of speech. It does not report
*restricted* words, because it cannot find the meaning.

## When a word is not in this file

Do these steps:

1. Find the simplest word that has the same meaning. Frequently, it is a word
   in the tables that follow.
2. If that word has more than one meaning, select a word that has one meaning
   only.
3. If no single word gives the same meaning, change the sentence construction
   (rule 9.1). Keep the meaning of the sentence.
4. If the word is the name of an item or a process in software, refer to
   [software-terms.md](software-terms.md).

If the user gives you a copy of ASD-STE100, its dictionary (part 2) is the
authority. Use it before this file.

## Modal verbs and helper verbs

| Word | Status | Use |
| --- | --- | --- |
| *should* (v) | not approved | *must* for a requirement, *can* for a possibility |
| *shall* (v) | not approved | *must* |
| *may* (v) | not approved | *can* for a permission or a possibility, *possibly* for a fact that you are not sure about |
| *might* (v) | not listed | *possibly*, *it is possible that*, *can* |
| *would* (v) | not approved | *can*, *will*, or a condition with *if* |
| *ought* (v) | not listed | *must* |
| *need* (v) | not approved | *necessary* ("It is necessary to ..."), *must*, or a command |
| *require* (v) | not approved | *necessary*, *must* |
| *have to* (v) | not approved | A command, or *must* |
| *able* (adj) | not approved | *can* |
| *going to* (v) | not listed | *will* |
| *could* (v) | restricted | Only as the past tense of *can* ("The client could not connect"). For a possibility, use *can* or *possibly*. |

## Certainty and degree

| Word | Status | Use |
| --- | --- | --- |
| *probably* (adv) | not listed | *possibly*, *it is possible that*. Also give the data. |
| *likely* (adj) | not listed | *possible*, *possibly*. Also give the data. |
| *perhaps*, *maybe* (adv) | not listed | *possibly* |
| *roughly* (adv) | not listed | *approximately* |
| *nearly* (adv) | not approved | *almost* |
| *exactly* (adv) | not approved | *accurately*, *fully*, *correct* |
| *just* (adv) | not approved | *only*, *immediately*, or delete it |
| *simply*, *basically*, *essentially*, *actually*, *really* (adv) | not listed | Delete it. |
| *please* (adv) | not listed | Delete it. A command is not rude in STE. |
| *quite*, *rather*, *fairly*, *pretty* (adv) | not listed | *very*, or give the value |
| *apparently* (adv) | not listed | *it is possible that*, or give the data |
| *apparent* (adj) | not approved | *see*, *find* |
| *obvious* (adj) | not listed | Delete it. |
| *about* (prep) | restricted | Only for a subject ("data about the server"). For a quantity, use *approximately*. |

## Connecting words

| Word | Status | Use |
| --- | --- | --- |
| *however* (adv) | not approved | *but* |
| *therefore* (adv) | not approved | *thus*, *as a result* |
| *hence* (adv) | not listed | *thus* |
| *so* (conj) | not listed | *thus*, *as a result*. For the result that you want, use *to*. |
| *whether* (conj) | not approved | *if* |
| *whenever* (conj) | not approved | *when* |
| *once* (conj) | not approved | *when*, *after*. For a number of times, use *one time*. |
| *moreover*, *furthermore*, *additionally*, *besides* (adv) | not listed | *also* |
| *addition* (n) | not approved | *add* (v). For "in addition", use *also*. |
| *instead* (adv) | not approved | Change the construction: "Use X. Do not use Y." Or use *alternative* (n). |
| *otherwise* (adv) | not approved | *if ... not*, *differently* |
| *finally*, *lastly* (adv) | not listed | *then*, or give numbers to the steps |
| *meanwhile* (adv) | not listed | *at the same time*, *while* |
| *yet* (adv) | not approved | *but*. For "until this time", use *at this time*. |
| *though* (conj) | not listed | *although*, *but* |
| *whereas* (conj) | not listed | *but* |
| *since* (conj) | restricted | Only for time ("since version 2"). For a cause, use *because*. |
| *as* (conj) | restricted | Approved as a preposition and in *as follows* and *as necessary*. For a cause, use *because*. For two events that occur together, use *while*. |
| *while* (conj) | restricted | Only for two events that occur together. For a contrast, use *but* or *although*. |
| *next* (adv) | restricted | Approved only as an adjective ("the next step"). As an adverb, use *then*. |

## Time and frequency

| Word | Status | Use |
| --- | --- | --- |
| *now* (adv) | not approved | *at this time*, or delete it |
| *currently* (adv) | not listed | *at this time*, or delete it |
| *already* (adv) | not approved | Delete it. Or use *in progress*, *no other*. |
| *still* (adv) | not approved | *continue* (v), *stay* (v) |
| *soon* (adv) | not approved | Give the time. |
| *recently* (adv) | not listed | Give the date or the version. Or use *previously*. |
| *later* (adv) | not approved | *subsequently*, *then*, *after* |
| *eventually* (adv) | not approved | Give the time or the condition. |
| *often* (adv) | not approved | *frequently* |
| *sometimes* (adv) | not listed | *frequently*, or give the condition with *if* or *when* |
| *never* (adv) | not approved | *do not*, *not* |

## Quantity

| Word | Status | Use |
| --- | --- | --- |
| *any* (adj) | not approved | Delete it, or use *a*, *one or more*, *all* |
| *anything*, *everything*, *nothing* (pron) | not listed | *something*, *all*, *no*, or name the items |
| *both* (adj) | not approved | *the two* |
| *either* (adj) | not approved | *one of the two*, *or* |
| *neither* (adj) | not approved | *the two ... not* |
| *every* (adj) | not approved | *all*, *each* |
| *few* (adj) | not approved | *some*, *a small number of*. Give the number. |
| *several* (adj) | not approved | *some*. Give the number. |
| *various* (adj) | not approved | *different* |
| *multiple* (adj) | not listed | *more than one*, *many*. Give the number. |
| *numerous* (adj) | not listed | *many* |
| *enough* (adj) | not approved | *sufficient* |
| *whole*, *entire* (adj) | not approved | *full*, *all* |
| *another* (adj) | not approved | *one more*, *different*, *again* |
| *amount* (n) | not approved | *quantity*. For items that you can count, use *number*. |

## Verbs

| Word | Status | Use |
| --- | --- | --- |
| *allow* (v) | not approved | *let* |
| *appear* (v) | not approved | *show*, *think*, *possible* |
| *seem* (v) | not listed | *show*, *think*, *possible* |
| *attempt* (v) | not approved | *try* |
| *begin*, *commence*, *initiate* (v) | not approved | *start* |
| *choose*, *decide* (v) | not approved | *select*, *make a decision* |
| *confirm*, *verify*, *ensure* (v) | not approved | *make sure that* |
| *consider*, *assume* (v) | not approved | *think* |
| *believe* (v) | not listed | *think* |
| *understand* (v) | not listed | *know* |
| *create* (v) | not approved | *make*, *cause* |
| *describe*, *mention* (v) | not approved | *give*, *tell* |
| *specify* (v) | not listed | *give*, *tell*. The adjective *specified* is approved. |
| *explain* (v) | not approved | *tell* |
| *detect*, *locate* (v) | not approved | *find* |
| *determine* (v) | not approved | *find*, *calculate*, *select* |
| *display* (v) | noun only | *show*. The noun *display* (a screen) is approved. |
| *indicate* (v) | not approved | *show* |
| *execute*, *perform*, *implement*, *accomplish* (v) | not approved | *do*, or a more accurate verb |
| *achieve*, *obtain* (v) | not approved | *get* |
| *expect* (v) | not approved | *possible* ("It is possible that ..."), *must* |
| *fix* (v) | not approved | *correct*, *repair* |
| *handle* (v) | not approved | A more accurate verb: *catch*, *process*, *use*, *move* |
| *happen* (v) | not approved | *occur* |
| *improve* (v) | not approved | Give the result: *better*, *faster*, *increase*, *decrease* |
| *insert* (v) | not approved | *put*, *add* |
| *append* (v) | not listed | *add* |
| *inspect* (v) | not approved | *examine* |
| *review* (v) | not listed | *examine* |
| *investigate*, *analyze* (v) | not approved | *examine*, *find the cause of* |
| *maintain* (v) | not approved | *keep*, *hold* |
| *modify* (v) | not approved | *change* |
| *provide* (v) | not approved | *give*, *supply* |
| *reduce* (v) | not approved | *decrease* |
| *repeat* (v) | not approved | *do ... again* |
| *suggest*, *propose* (v) | not listed | *recommend* |
| *utilize* (v) | not approved | *use* |
| *leverage* (v) | not listed | *use* |
| *wish* (v) | not listed | *want* |
| *ask* (v) | not approved | *tell* (for an order), or write the question |
| *affect*, *impact* (v) | not approved | *change*, *have an effect on* |
| *comprise* (v) | not approved | *have*, *contain*, *include* |
| *consist* (v) | not listed | *have*, *contain* |
| *terminate* (v) | not approved | *stop* |
| *exist* (v) | not approved | *be* ("There is a file ..."), *available*, *missing* |
| *omit* (v) | not approved | *do not do*, *ignore* |
| *permit* (v) | not approved | *let*. The adjective *permitted* is approved. |
| *certify*, *approve* (v) | not approved | *write*, *approval* (n). The adjective *approved* is approved. |
| *present* (v) | not approved | *give*, *show* |
| *check* (v) | noun only | *make sure that*, *examine*, *measure*, or *do a check of* |
| *test* (v) | noun only | *do a test of*, or *run* the tests |
| *work* (v) | noun only | *operate*, *operate correctly* |
| *damage* (v) | noun only | *cause damage to* |
| *end*, *finish* (v) | noun only | *stop*, *complete* |
| *use* (n) | verb only | Use the verb: "when you use X". Or use *operation*. |
| *help* (n) | verb only | *aid* (n), or use *help* as a verb |
| *complete* (adj) | verb only | *full*, *all*, *completed* |
| *follow* (v) | restricted | Only for a sequence ("the steps that follow"). For instructions, use *obey*. |
| *get* (v) | restricted | Only when you come to have something ("get the logs"). For a change of condition, use *become*. |
| *go* (v) | restricted | Only for a movement ("go to the directory"). For a value, use *increase*, *decrease*, or *become*. |
| *see* (v) | restricted | Only for sight ("you can see the error on the screen"). Or use *refer to*, *make sure that*, *find*. |
| *turn* (v) | restricted | Only for a rotation ("turn the knob"). For a change, use *change to*, *become*, or *set*. |
| *extend* (v) | restricted | Only for an increase in length or range. For "applies to", write *is applicable to*. |

## Nouns

| Word | Status | Use |
| --- | --- | --- |
| *thing* (n) | not listed | Name the item, or use *something* |
| *reason* (n) | not approved | *cause*, *because of* |
| *purpose*, *goal*, *objective* (n) | not listed | Write *to* + a verb ("You do this step to ..."), or *function* |
| *way* (n) | not approved | *procedure*, *method* |
| *approach* (n) | not listed | *method*, *procedure* |
| *behavior* (n) | not listed | *operation*, *function*, or tell the function |
| *capability* (n) | not approved | *function*, *can* |
| *functionality* (n) | not listed | *function* |
| *ability* (n) | not approved | *can* |
| *detail* (n) | not approved | *information*, *instruction* |
| *kind* (n) | not approved | *type* |
| *people* (n) | not approved | *persons*, *personnel*, or the role (*users*, *developers*) |
| *portion* (n) | not approved | *part* |
| *improvement* (n) | not listed | Give the result that you can measure. |
| *evidence* (n) | not approved | *data*, *facts*, *indication*, *sign* |
| *action* (n) | not approved | *step*, *procedure*, *task* |
| *reference* (n) | not approved | *refer* (v) |
| *variety* (n) | not listed | Change the construction. |
| *form* (n) | technical noun only | *shape*. Use *form* only for a web form or a verb form. |
| *issue* (n) | technical noun only | *problem*, *error*. Use *issue* only for an item in an issue tracker. |
| *option* (n) | technical noun only | *alternative*, *can*. Use *option* only for a command or setting option. |
| *order* (n) | technical noun only | *sequence*. Use *order* only for a sort order. |
| *state* (n) | technical noun only | *condition*. Use *state* only for the state of a program. |
| *status* (n) | technical noun only | *condition*. Use *status* only for a status code or a status field. |
| *request* (n) | technical noun only | *tell* (v). Use *request* only for a request to a server or an API. Do not use it as a verb. |

## Pronouns and question words

| Word | Status | Use |
| --- | --- | --- |
| *what* (pron) | not listed | *which*, *something that*, or *the* + a noun + *that* ("the files that changed") |
| *why* (adv) | not listed | *the cause*, *because* |
| *whose* (pron) | not approved | Change the construction. |
| *whom* (pron) | not listed | *who*, or change the construction |
| *anyone*, *someone*, *everyone*, *somebody* (pron) | not listed | *a person*, *all persons* |
| *nobody* (pron) | not listed | *no person* |

## Adjectives

| Word | Status | Use |
| --- | --- | --- |
| *acceptable* (adj) | not approved | *permitted* |
| *appropriate*, *suitable* (adj) | not approved | *applicable*, *correct* |
| *proper* (adj) | not approved | *correct* |
| *big* (adj) | not approved | *large*. Give the value. |
| *certain* (adj) | not approved | *sure*, *some*, *specified* |
| *complex* (adj) | not listed | *not easy*. Tell the cause. |
| *complicated*, *difficult* (adj) | not approved | *not easy* |
| *critical* (adj) | not approved | *very important*, *careful* |
| *crucial*, *essential* (adj) | not listed | *very important*, *necessary* |
| *vital* (adj) | not approved | *mandatory* |
| *main* (adj) | not approved | *primary* |
| *old* (adj) | not approved | *previous*, *remaining*, *used*, *expired* |
| *current* (adj) | not listed | Delete it, or use *at this time*. |
| *similar* (adj) | not approved | *equivalent*, *almost the same* |
| *simple* (adj) | not listed | *easy*. Tell the cause. |
| *specific* (adj) | not approved | *specified*, *approved* |
| *relevant* (adj) | not approved | *related*, *applicable* |
| *significant* (adj) | not approved | *important*. Give the value. |
| *wrong* (adj) | not approved | *incorrect* |
| *quick* (adj) | not approved | *fast* (adj), *quickly* (adv) |
| *robust*, *seamless*, *powerful*, *elegant*, *optimal* (adj) | not listed | Delete it. Give a fact that the reader can measure. |
| *present* (adj) | not approved | *be* ("If there is ..."), or delete it |
| *inside*, *outside* (adj) | not approved | *inner*, *external*, *outer* |
| *key* (adj) | technical noun only | *primary*, *important*. Use *key* only as a noun ("API key"). |
| *right* (adj) | restricted | Only a direction ("the right side"). For "correct", use *correct*. |
| *well* (adv) | not approved | *correctly*, *fully*, *good* (adj) |
| *hard* (adj) | restricted | Only a physical property. For "not easy", write *not easy*. |
| *fast* (adj) | restricted | Approved as an adjective. As an adverb, use *quickly*. |

## Prepositions and phrases

| Word | Status | Use |
| --- | --- | --- |
| *over* (prep) | not approved | *above* (a position), *on*, *along*, *more than* (a value) |
| *under* (prep) | not approved | *below* (a position), *in*, *less than* (a value) |
| *via* (prep) | not approved | *through*, *with* |
| *per* (prep) | not approved | *for each* |
| *within* (prep) | not approved | *in*, *in less than* |
| *throughout* (prep) | not approved | *during*, *in all parts of* |
| *inside* (prep) | not approved | *in*, *into* |
| *outside* (prep) | not approved | *near*, *out of* |
| *like* (prep) | not listed | *for example*, *the same as*, *equivalent to* |
| *despite* (prep) | not listed | *although* |
| *such as* (prep) | not approved | *for example* |
| *according to* (prep) | not approved | *refer to*, or make the source the subject: "The log shows that ..." |
| *in order to* (prep) | not listed | *to* |
| *due to* (prep) | not approved | *because of* |
| *prior to* (prep) | not approved | *before* |
| *and/or* (conj) | not listed | *or*, or write the two conditions |
| *above*, *below* (prep) | restricted | Only a position. For a value, use *more than* or *less than*. |

## Phrasal verbs

Rule 9.3 does not let you use a verb and a preposition or adverb that together
have a new meaning. Use one verb. STE gives approval to a small number of
phrasal verbs only, for example *put on*, *come on*, and *go off*.

| Word | Status | Use |
| --- | --- | --- |
| *set up* (v) | phrasal verb | *install*, *prepare*, *set*, *make* |
| *find out* (v) | phrasal verb | *find*, *know* |
| *figure out* (v) | phrasal verb | *find*, *calculate* |
| *carry out* (v) | phrasal verb | *do* |
| *point out* (v) | phrasal verb | *show*, *tell* |
| *look into* (v) | phrasal verb | *examine* |
| *look up* (v) | phrasal verb | *find* |
| *come up with* (v) | phrasal verb | *make*, *find* |
| *come up* (v) | phrasal verb | *occur* |
| *go through* (v) | phrasal verb | *examine*, *read* |
| *go over* (v) | phrasal verb | *examine* |
| *end up* (v) | phrasal verb | *become*, or give the result |
| *turn on*, *switch on* (v) | phrasal verb | *set to ON*, *start*, *enable* |
| *turn off*, *switch off* (v) | phrasal verb | *set to OFF*, *stop*, *disable* |
| *shut down* (v) | phrasal verb | *stop*. The noun *shutdown* is a technical noun. |
| *start up* (v) | phrasal verb | *start* |
| *back up* (v) | phrasal verb | *make a backup of* |
| *clean up* (v) | phrasal verb | *clean*, *remove* |
| *fill in*, *fill out* (v) | phrasal verb | *write*, *complete* |
| *pick up* (v) | phrasal verb | *get*, *read* |
| *take out*, *take off* (v) | phrasal verb | *remove* |
| *give off* (v) | phrasal verb | *release* |
| *run into* (v) | phrasal verb | *find*, *get* |
| *deal with* (v) | phrasal verb | A more accurate verb: *correct*, *process*, *catch* |
| *lead to* (v) | phrasal verb | *cause* |
| *give up* (v) | phrasal verb | *stop* |
| *hold off* (v) | phrasal verb | *wait* |
| *keep up* (v) | phrasal verb | *continue* |
| *break down* (v) | phrasal verb | *divide* (a task), *stop* (a machine) |
| *bring up* (v) | phrasal verb | *start* (a server), *tell* (a subject) |
| *show up* (v) | phrasal verb | *show*, *occur* |
| *work out* (v) | phrasal verb | *calculate*, *find* |
| *sort out* (v) | phrasal verb | *correct*, *repair* |
| *spin up* (v) | phrasal verb | *start*, *make* |
| *roll out* (v) | phrasal verb | *release*, *deploy* |
| *roll back* (v) | phrasal verb | *revert*, *install the previous version*. The noun *rollback* is a technical noun. |
| *wire up*, *hook up* (v) | phrasal verb | *connect* |
| *rule out* (v) | phrasal verb | Write that the item is not the cause. |
| *narrow down* (v) | phrasal verb | *decrease*, *find* |
| *reach out* (v) | phrasal verb | *tell*, *send a message to* |
| *kick off* (v) | phrasal verb | *start* |
| *dive into*, *dig into* (v) | phrasal verb | *examine*, *read* |
| *fall back* (v) | phrasal verb | *use* (the alternative). The noun *fallback* is a technical noun. |

## Approved modal verbs and connecting words

These words are approved. Use each one only with the meaning given.

- **Modal verbs**: *must* (an obligation), *can* (possible or
  permitted), *cannot*, *will* (the simple future), *do not* (a prohibition).
- **Connecting words**: *and*, *but*, *or*, *then*, *thus*, *also*, *because*,
  *if*, *when*, *before*, *after*, *until*, *unless*, *although*, *as a
  result*, *at the same time*.
