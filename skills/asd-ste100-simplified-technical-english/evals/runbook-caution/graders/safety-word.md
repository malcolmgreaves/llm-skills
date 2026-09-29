---
type: regex
pattern: '\b(?:CAUTION|WARNING)\b|\b(?:Caution|Warning)\b[*_]*:'
match: contains
---

The runbook has a safety instruction that starts with CAUTION or WARNING. The
skill does not make uppercase letters mandatory, thus a label such as
"Caution:" also passes.
