---
type: regex
pattern: '\b(?:however|therefore|hence|currently|now|already|yet|still|so|ensure[sd]?|verif(?:y|ies|ied)|confirm(?:s|ed)?|needs? to|needed|requires?|required|any|whether|once|what|why|few|several|multiple|various|things?|either|please)\b|\b(?:has|have|had)\s+(?:not\s+)?(?:been|\w+ed)\b|\b(?:is|are|was|were)\s+(?:not\s+)?(?!(?:missing|remaining|something)\b)\w+ing\b'
flags: i
match: not_contains
---

The message uses none of these words that STE does not approve and that a
summary of a change frequently uses: however, therefore, hence, currently,
now, already, yet, still, so, ensure, verify, confirm, need to, require, any,
whether, once, what, why, few, several, multiple, various, thing, either, and
please. It also has no perfect tense and no progressive tense. The approved
words missing, remaining, and something are not progressive verbs.
