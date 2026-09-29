---
type: regex
pattern: '\b(?:old|purpose|should|few|several|things?|whose|ensure[sd]?|verif(?:y|ies|ied)|confirm(?:s|ed)?|once|so|any|needs? to|requires?|what|why|either|perform(?:s|ed)?|execute[sd]?|please|however|currently|now)\b|\b(?:has|have|had)\s+(?:not\s+)?(?:been|\w+ed)\b'
flags: i
match: not_contains
---

The runbook uses none of these words that STE does not approve and that a
runbook frequently uses: old, purpose, should, few, several, thing, whose,
ensure, verify, confirm, once, so, any, need to, require, what, why, either,
perform, execute, please, however, currently, and now. It also has no perfect
tense.
