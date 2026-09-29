---
type: regex
pattern: '\b(?:what|why|so|now|still|old|probably|likely|maybe|might|should|either|ensure[sd]?|verif(?:y|ies|ied)|confirm(?:s|ed)?|once|any|finish(?:es|ed)?|fix|please|however)\b'
flags: i
match: not_contains
---

The reply uses none of these words that STE does not approve and that an
explanation of an error frequently uses: what, why, so, now, still, old,
probably, likely, maybe, might, should, either, ensure, verify, confirm, once,
any, finish, fix, please, and however. The list leaves out "already" and
"another", because the error text contains them, and the reply must be able to
copy the error text without a change.
