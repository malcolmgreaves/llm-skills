---
type: regex
pattern: '#\s*(?:keep|examine|identify|record|skip|check|return|sort|add|store|get|set|compute|calculate|build|create|update|remove|ignore|loop|iterate|track|use|make|find|save|drop|collect|group|filter|append|initialize|map|compare|remember)\b(?!\s+of\b)'
flags: i
match: not_contains
---

No inline comment starts with a command. A word that is followed by "of" is a
noun ("# Map of user IDs"), thus the pattern does not match it. A comment gives information, so the
skill tells the agent to write it as descriptive text ("The loop examines the
events in time order"), not as a command ("Examine the events").
