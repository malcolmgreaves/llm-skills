# cells

A small spreadsheet engine in Python. Cells hold numbers, text, booleans, or
formulas, and a formula computes its value from other cells.

## Values

A cell's value is one of:

- a number (a Python `float`)
- text (`str`)
- a boolean, `TRUE` or `FALSE` (`bool`)
- an error such as `#DIV/0!` (`cells.CellError`)
- empty (`None`)

## Cell content

`Sheet.set(address, content)` sets a cell from a string:

- Content that starts with `=` is a formula.
- Content that is a number, such as `12`, `-3.5`, `.5`, or `1e3`, is a number.
- `TRUE` and `FALSE`, in any case, are booleans.
- Anything else is text.
- Empty content (`""`) clears the cell.

## Addresses

An address is column letters followed by a row number from 1, such as `A1` or
`B12`. Letters can be lowercase. Columns run `A` to `Z`, then `AA`, `AB`, and
so on: `Z1` is column 26, `AA1` is column 27, `AZ1` is column 52, and `BA1` is
column 53. `cells.address.parse` returns `(column, row)`, and
`cells.address.name` turns a column and a row back into an address.

## Formulas

A formula can contain numbers, references to other cells, the operators
`+ - * / ^`, parentheses, unary `-` and `+`, and function calls such as
`ROUND(A1, 2)`.

Operators, from loosest to tightest binding:

| Operators | Groups |
| --- | --- |
| `+`, `-` | left: `=10-4-3` is 3 |
| `*`, `/` | left: `=8/4/2` is 1 |
| unary `-`, `+` | `=2*-3` is -6 |
| `^` | right: `=2^3^2` is 512 |

`^` binds tighter than unary minus, so `=-2^2` is -4.

### Operands

Arithmetic converts each operand to a number:

- A number is itself.
- `TRUE` is 1 and `FALSE` is 0.
- An empty cell is 0.
- Text is the error `#VALUE!`: `=A1+1` is `#VALUE!` when A1 holds `abc`.

A formula whose result is an empty cell's value, such as `=A9` when A9 is
empty, has the value 0.

### Errors

A failed computation gives an error value; evaluation never raises.

| Error | Cause |
| --- | --- |
| `#DIV/0!` | Division by zero, or 0 raised to a negative power |
| `#VALUE!` | Text in arithmetic; a result that isn't a finite real number (`=(-8)^0.5`, `=10^400`); an unknown function; the wrong number of arguments |
| `#ERROR!` | Formula text that doesn't parse, such as `=1+` |

Errors propagate. An operator converts its operands left to right, and the
first error, either an error value or a failed conversion, is the result: when
A1 holds `abc` and A2 holds `=1/0`, `=A1+A2` is `#VALUE!` and `=A2+A1` is
`#DIV/0!`. A function evaluates its arguments left to right, and if any of
them is an error, it returns the first one.

### Functions

Function names ignore case: `=abs(-2)` is 2.

| Function | Returns |
| --- | --- |
| `ABS(number)` | The absolute value |
| `ROUND(number, [digits])` | The number rounded to `digits` decimal places (default 0), with halves rounded away from zero: `=ROUND(2.5)` is 3, `=ROUND(-2.5)` is -3, `=ROUND(1.25, 1)` is 1.3. A negative `digits` rounds to tens, hundreds, and so on: `=ROUND(1234, -2)` is 1200. |
| `SQRT(number)` | The square root; `#VALUE!` for a negative number |

Each family of functions is a module in `cells/functions/` that registers its
functions with the `function` decorator in `cells/functions/__init__.py` and
is imported at the end of that file.

## Display

`Sheet.display(address)` returns the text a cell shows:

- A number shows up to 15 significant digits, with no trailing zeros and no
  trailing decimal point: `3` shows `3`, `=1/4` shows `0.25`, `=1/3` shows
  `0.333333333333333`, `1234567` shows `1234567`, and `=0.1+0.2` shows `0.3`.
  A number whose exponent is 15 or more, or less than -4, shows in exponent
  notation: `=10^20` shows `1e+20` and `=1/100000` shows `1e-05`. This is
  C's `%.15g` format.
- A boolean shows `TRUE` or `FALSE`.
- Text shows as itself.
- An error shows its code, such as `#DIV/0!`.
- An empty cell shows nothing (`""`).

## The Sheet API

```python
from cells import Sheet, CellError

sheet = Sheet()
sheet.set("A1", "2")
sheet.set("A2", "=A1*10")
sheet.value("A2")    # 20.0
sheet.display("A2")  # "20"
sheet.content("A2")  # "=A1*10", exactly as set
sheet.addresses()    # ["A1", "A2"]: non-empty cells in row-major order
```

Row-major order is row 1 from left to right, then row 2, and so on. Values
always reflect the current contents: after `set`, every value that depends on
the changed cell is up to date. `set` and the other methods raise
`ValueError` for an invalid address.

Cycles aren't detected: a formula that refers to itself, directly or through
other cells, fails with `RecursionError`.

## Command line

```sh
python3 -m cells eval FILE CELL
```

Prints the display text of one cell. `FILE` is a CSV grid: the first line is
row 1, and its first field is column A. For an unreadable file or an invalid
address, the command prints a message that starts with `cells: ` to stderr
and exits with status 2.
