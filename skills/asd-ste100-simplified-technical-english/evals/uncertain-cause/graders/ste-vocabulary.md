---
type: regex
pattern: '\b(?:either|neither|yet|already|still|now|currently|confirm(?:s|ed)?|verif(?:y|ies|ied)|suspect(?:s|ed)?|so|whether|what|why|any|few|several|multiple|issue)\b|\b(?:has|have|had)\s+(?:not\s+)?(?:been|\w+ed)\b|\b(?:is|are|was|were|am)\s+(?:not\s+)?(?!(?:missing|remaining|something)\b)\w+ing\b'
flags: i
match: not_contains
---

The update uses none of these words that STE does not approve and that a
status update frequently uses: either, neither, yet, already, still, now,
currently, confirm, verify, suspect, so, whether, what, why, any, few,
several, multiple, and issue. It also has no perfect tense and no progressive
tense. The approved words missing, remaining, and something are not
progressive verbs.
