---
type: llm
focus:
  source: file
  path: report.py
---

PASS if all four of these are true of report.py:
1. Parsing a row, deciding whether an order counts, summing per
   customer, and formatting the output are each done in a function
   whose job is that step, not inline in a function that also does
   another of these steps.
2. Only functions whose job is input or output read the file or
   print. A separate reading function (for example `read_rows`)
   called by the top-level function (for example `main`) is fine.
   The functions that parse, decide, sum, and format take values
   and return values.
3. No module-level variable is reassigned or mutated when the code
   runs. Constants are fine.
4. Every function has annotations on its parameters and return type.

FAIL if any of the four is false. Judge only these four points, not
names, docstrings, style, or other design choices.
