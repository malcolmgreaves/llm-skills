---
name: template
description: >-
  Replace this. State what the skill does, then state when an agent should use
  it — name the concrete words and phrases a user would actually say, since this
  field is the only thing matched against their request. Max 1024 characters.
license: MPL-2.0
metadata:
  version: "0.1.0"
  author: malcolmgreaves
---

# <Skill Name>

One or two sentences on what this skill does and the outcome it produces.
Everything about *when* to use it lives in `description`, not here — by the time
an agent reads this line, the skill has already triggered.

## Workflow

1. Step one, in the imperative.
2. Step two.
3. Step three.

## Output format

State the expected shape of the result. If the format is fixed, show it:

```
# [Title]
## Summary
## Details
```

## Examples

**Input:** what the user says
**Output:** what the agent produces

## Edge cases

- The case that breaks the naive approach, and what to do instead.
- What to do when a precondition is missing — ask, or pick a default and say so.

<!--
Optional bundled files. Delete the directories you don't use.

  scripts/      Executable code. Never enters context — only its output does.
                Use for anything deterministic or repetitive.
  references/   Docs read on demand. Point at them from here with a relative
                path AND a condition:
                  "Read references/AWS.md when the target is AWS."
  assets/       Templates, fonts, images that end up in the output.

Keep this file under 500 lines. Past that, split into references/.
-->
