# Backlog

Ten tasks that extend `cells`. Each task lists the tasks it depends on and
numbered rules. Everything in README.md keeps holding unless a rule here
changes it.

## Rules for every task

- **G1.** Values always reflect the current contents. After any `Sheet.set`,
  `Sheet.fill`, or file load, every value that depends on a changed cell,
  directly or through other cells or ranges, is up to date.
- **G2.** Errors propagate as README.md describes, unless a rule says
  otherwise for a specific function.
- **G3.** Function names ignore case.
- **G4.** The `function` decorator takes `function(name, min_args, max_args, **options)`.
  Two tasks add options:
  - `ranges=True` (task `ranges`): the function receives range arguments.
  - `errors=True` (task `errors`): the function receives error arguments
    instead of the call returning the first error.

  If a task needs an option that another task adds, it implements the option
  exactly as described here.
- **G5.** Every task documents its behavior in README.md, keeps
  `python3 -m unittest discover -s tests -q` passing, and adds tests.
- **G6.** Standard library only.

## Task `ranges`

Depends on: nothing.

- **R1.** `A1:B3` is a range: two addresses joined by `:`. It covers every
  cell whose column and row lie between the two corners, inclusive. The
  corners can come in either order: `B3:A1` and `A3:B1` are the same range as
  `A1:B3`.
- **R2.** A range can only be a function argument. Anywhere else, a range
  is the error `#VALUE!`, which propagates like any other error: `=A1:B2`
  and `=A1:A2+1` are `#VALUE!`.
- **R3.** A function registered with `ranges=True` receives a
  `cells.ranges.RangeValue` for each range argument. For any other
  function, a range argument is the error `#VALUE!`: `=ABS(A1:A2)` is
  `#VALUE!`.
- **R4.** `RangeValue.rows` is a list of rows from top to bottom; each row is
  a list of cell values from left to right, with `None` for an empty cell.
  `RangeValue.values()` returns the same values in one list, in row-major
  order. Errors inside a range don't propagate on their own; each function
  decides what an error in a range means.
- **R5.** `ROWS(range)` and `COLUMNS(range)` return the number of rows and
  columns in a range: `=ROWS(B3:A1)` is 3, and `=COLUMNS(Z1:AB1)` is 3.
  Given a single value instead of a range, they return `#VALUE!`, or the
  error if the value is an error (G2).

## Task `errors`

Depends on: nothing.

- **E1.** An unknown function name gives `#NAME?` (it gave `#VALUE!`), and so
  does a name that isn't a function call or a reference: `=FOO(1)` and
  `=FOO+1` are `#NAME?`. (Task `logic` makes the names `TRUE` and `FALSE`
  booleans instead; see L3.)
- **E2.** Error codes can be written in a formula, in uppercase exactly as
  shown: `#DIV/0!`, `#VALUE!`, `#NAME?`, `#N/A`, `#REF!`, `#CYCLE!`, and
  `#ERROR!`. Each one evaluates to that error: `=#N/A` is `#N/A`, and
  `=1+#REF!` is `#REF!`. The module `cells.errors` defines a constant for
  each code.
- **E3.** `NA()` returns `#N/A`.
- **E4.** `ISERROR(value)` returns TRUE if the value is an error and FALSE
  otherwise.
- **E5.** `IFERROR(value, fallback)` returns `value` unless it's an error, and
  `fallback` if it is. An error in `fallback` matters only when `fallback` is
  returned: `=IFERROR(1, 1/0)` is 1, and `=IFERROR(1/0, "none")` is `none`
  once task `text` adds text literals.

## Task `logic`

Depends on: nothing.

- **L1.** The comparison operators `=`, `<>`, `<`, `<=`, `>`, and `>=` return
  TRUE or FALSE. They bind more loosely than every other operator, including
  `&` from task `text`, and group left: `=1+1=2` is TRUE.
- **L2.** Comparison rules:
  - Two numbers compare numerically.
  - Two texts compare ignoring case: `a` equals `A`, and `a` is less than `B`.
  - FALSE is less than TRUE.
  - Values of different types order as number < text < boolean, so every
    number is less than every text, and `=5<TRUE` is TRUE.
  - An empty value compares as 0 against a number, as empty text against
    text, and as FALSE against a boolean. Two empty values are equal.
  - If either side is an error, the result is the first error, left to right.

  The module `cells.compare` provides `compare(a, b)`, which returns -1, 0,
  or 1 for two values that aren't errors, following these rules.
- **L3.** `TRUE` and `FALSE` in a formula, in any case, are the boolean values.
- **L4.** `IF(condition, then, [else])` returns `then` if the condition is
  true and `else` otherwise; `else` defaults to FALSE. Only the returned
  branch matters: an error in the other branch doesn't affect the result, so
  `=IF(TRUE, 1, 1/0)` is 1.
- **L5.** A condition converts to true or false like this: a boolean is
  itself, a number is true unless it's 0, an empty value is false, text is
  `#VALUE!`, and an error is that error. `IF`, `AND`, `OR`, and `NOT` all use
  this conversion.
- **L6.** `AND(value, ...)` and `OR(value, ...)` take one or more arguments.
  Each argument is converted as in L5, and the first error, in argument
  order, is the result. `NOT(value)` negates one value.

## Task `text`

Depends on: nothing.

- **T1.** Text literals are written in double quotes. Two double quotes
  inside a literal stand for one: `="say ""hi"""` is `say "hi"`.
- **T2.** `&` joins two values as text. It binds more loosely than `+` and
  `-` and more tightly than comparisons, and groups left: `=1+2&3` is `33`.
- **T3.** A value converts to text like this, for `&` and for the functions in
  T4 and T5: text is itself, a number is its display text (README.md,
  "Display"), a boolean is `TRUE` or `FALSE`, an empty value is empty text,
  and an error is that error. `=1/4&""` is `0.25`, `=1234567&""` is
  `1234567`, and `=A1&"!"` is `TRUE!` when A1 holds `TRUE`.
- **T4.** `LEN(text)` returns the number of characters. `UPPER(text)` and
  `LOWER(text)` change case. `TRIM(text)` removes leading and trailing spaces
  and replaces each run of spaces inside the text with one space.
- **T5.** `LEFT(text, [count])` returns the first `count` characters, and
  `RIGHT(text, [count])` the last `count`; `count` defaults to 1.
  `MID(text, start, count)` returns `count` characters starting at position
  `start`, where the first character is position 1. A `count` longer than
  the text returns as much as there is. `count` and `start` convert like
  arithmetic operands. A negative `count`, or a `start` less than 1, is
  `#VALUE!`.
- **T6.** Text still never converts to a number: `="1"+1` is `#VALUE!`.

## Task `csvio`

Depends on: nothing.

- **C1.** `cells.csvio.load(path)` reads a CSV file (RFC 4180, UTF-8) and
  returns a `Sheet`. The field in row r, column c goes to the cell at column
  c, row r, through `Sheet.set`. An empty field leaves the cell empty. The
  27th field of the first row is cell AA1.
- **C2.** Content that starts with `'` is text: the characters after the `'`,
  even if they look like a number, a boolean, or a formula. `'=1+1` is the
  text `=1+1`, and `'12` is the text `12`. This rule applies to `Sheet.set`,
  so it applies to loaded files too. `Sheet.content` still returns the content
  exactly as set, including the `'`.
- **C3.** `cells.csvio.save(sheet, path, values=False)` writes the grid from
  A1 to the last row and the last column that have a non-empty cell, one CSV
  record per row. Fields are quoted only when they must be (the `csv`
  module's default quoting), and records end with `\r\n`. With
  `values=False`, each field is the cell's content exactly as set; with
  `values=True`, each field is the cell's display text. An empty sheet writes
  an empty file.
- **C4.** Saving with `values=False` and loading the file gives a sheet with
  the same content in every cell.
- **C5.** The command line reads its files with `cells.csvio.load`. (It split
  lines on commas, which breaks quoted fields.)

## Task `recalc`

Depends on: nothing.

- **K1.** `Sheet.evaluation_count` is the number of times the sheet has
  evaluated a formula cell. Evaluating one formula cell once adds 1.
- **K2.** Values are cached. Reading a value evaluates a formula cell only if
  its content or a cell it depends on changed since the cell was last
  evaluated. After a change, each formula cell that depends on the changed
  cell is evaluated at most once until the next change, no matter how many
  values are read. Formula cells that don't depend on the change aren't
  evaluated again.
- **K3.** A formula depends on every cell it references, including every cell
  of every range in it.
- **K4.** A cell whose formula depends on itself, directly or through other
  cells, has the value `#CYCLE!`, and so does every other cell in that cycle.
  A cell that depends on a cycle cell gets `#CYCLE!` through normal error
  propagation. After the cycle is broken, the values recover.
- **K5.** A chain of 10,000 formulas works: A1 holds `1`, A2 holds `=A1+1`,
  and so on up to A10000. Whatever order the cells are set in, A10000 is
  10000, and setting all of them and then reading every value takes under 5
  seconds. After A1 changes, reading every value again takes under 5
  seconds.

## Task `aggregates`

Depends on: `ranges`, `errors`.

- **A1.** `SUM`, `AVERAGE`, `MIN`, `MAX`, `COUNT`, and `COUNTA` take one or
  more arguments. Each argument is either a range or a single value. A
  single reference such as `A1` is a single value, not a range.
- **A2.** Inside a range, numbers are counted, and empty cells, text, and
  booleans are skipped.
- **A3.** A single value is counted if it's a number. TRUE and FALSE count as
  1 and 0. An empty single value is skipped. Text is `#VALUE!`.
- **A4.** For `SUM`, `AVERAGE`, `MIN`, and `MAX`, the result is the first
  error, in argument order and then row-major order within a range, if there
  is one. Otherwise:
  - `SUM` adds the counted values, and is 0 if there are none.
  - `AVERAGE` divides that sum by the number of counted values, and is
    `#DIV/0!` if there are none.
  - `MIN` and `MAX` return the smallest and largest counted value, and are 0
    if there are none.
- **A5.** `COUNT` returns the number of values that `SUM` would count.
  `COUNTA` returns the number of non-empty values, including text, booleans,
  and errors, in ranges and as single values. Neither ever returns an error.
- **A6.** Examples, with A1 holding `2`, A2 holding `3`, A3 holding
  `hello`, and A4 holding `TRUE`: `=SUM(A1:A3)` is 5, `=COUNT(A1:A3)` is 2,
  `=COUNTA(A1:A3)` is 3, `=ROUND(AVERAGE(A1:A2), 0)` is 3, `=SUM(A1:A3, A4)`
  is 6, `=SUM(A1:A4)` is 5, and `=SUM(A3)` is `#VALUE!`. With B1 to B3 empty, `=AVERAGE(B1:B3)` is
  `#DIV/0!`.

## Task `lookup`

Depends on: `ranges`, `logic`, `errors`.

- **V1.** `VLOOKUP(key, range, column)` takes exactly three arguments. It
  finds the first row of the range, from the top, whose first cell equals
  `key`, and returns that row's cell in the given column, where 1 is the
  range's first column. Equality is the `=` operator's (L2): text ignores
  case, and a number never equals text. If no row matches, the result is
  `#N/A`. A `column` less than 1 is `#VALUE!`, and one greater than the
  range's number of columns is `#REF!`.
- **V2.** `MATCH(key, range)` returns the position, from 1, of the first cell
  equal to `key` in a range that is one row or one column. If no cell
  matches, or the range has more than one row and more than one column, the
  result is `#N/A`.
- **V3.** `INDEX(range, row, [column])` returns the cell at that row and
  column of the range, both counted from 1; `column` defaults to 1. A row or
  column outside the range is `#REF!`.
- **V4.** A `key` that is an error returns that error. An error cell inside
  the range never equals the key, and it matters only if it's the cell
  returned.

## Task `fill`

Depends on: `ranges`, `errors`.

- **F1.** A reference can mark its column, its row, or both as absolute with
  `$`: `$A$1`, `$A1`, and `A$1`. The marks don't change what a reference
  points to: `=$A$1+A$1` has the same value as `=A1+A1`. Range corners can
  have marks too: `$A$1:B2`.
- **F2.** `Sheet.fill(source, target)` copies the source cell's content into
  every cell of the target range except the source itself. `target` is a
  range such as `B1:D3`. If the content is a formula, each reference in the
  copy moves by the offset from the source to the destination cell: columns
  move by the column offset, rows by the row offset, and parts marked with
  `$` don't move. Filling `=A1+$B$1+A$1+$A1` from C1 into D2 gives
  `=B2+$B$1+B$1+$A2`, and filling `=Z1` from A2 into B2 gives `=AA1`.
- **F3.** Only references change. The rest of the formula text stays exactly
  as written, including spaces, case, and text literals: filling
  `="A1"&A1` one row down gives `="A1"&A2`. Moved references are written in
  uppercase with their `$` marks.
- **F4.** A reference that would move left of column A or above row 1 becomes
  `#REF!` in the formula text, and the formula then evaluates to `#REF!`:
  filling `=A1` from B2 into A1 gives `=#REF!`. If either corner of a range
  would move off the sheet, the whole range becomes `#REF!`.
- **F5.** Content that isn't a formula is copied unchanged.

## Task `cli`

Depends on: `csvio`.

- **X1.** The commands are `eval FILE CELL` (as before), `print FILE`,
  `set FILE CELL CONTENT`, and `check FILE`, run as `python3 -m cells ...`.
  Every command reads `FILE` with `cells.csvio.load`.
- **X2.** `print FILE --format text` prints one line, `ADDRESS: DISPLAY`, for
  each non-empty cell in row-major order. `text` is the default format. For
  example, `A1: 3`. Row-major order puts `B1` before `AA1`, and `AA1` before
  `A2`.
- **X3.** `print FILE --format csv` writes what `cells.csvio.save` writes with
  `values=True` to stdout.
- **X4.** `print FILE --format json` prints one JSON object. Its keys are the
  addresses of the non-empty cells in row-major order. A number is a JSON
  number, text is a string, a boolean is `true` or `false`, and an error is
  an object such as `{"error": "#DIV/0!"}`.
- **X5.** `set FILE CELL CONTENT` sets the cell, saves the file as
  `cells.csvio.save` does with `values=False`, and prints the cell's display
  text. Empty `CONTENT` clears the cell.
- **X6.** `check FILE` prints `ADDRESS: CODE` for each cell whose value is an
  error, in row-major order, and exits with status 1. If no cell has an
  error, it prints nothing and exits with status 0.
- **X7.** For an unreadable file or an invalid address, every command prints a
  message that starts with `cells: ` to stderr and exits with status 2.
