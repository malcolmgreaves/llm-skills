"""BACKLOG.md task `text`."""

from conftest import is_error, value


# spec: text T1
def test_literals():
    assert value('="hello"') == "hello"
    assert value('="say ""hi"""') == 'say "hi"'


# spec: text T2
def test_concatenation():
    assert value('="a"&"b"&"c"') == "abc"
    assert value("=1+2&3") == "33"


# spec: text T3 (examples) -- the 1234567 case also needs the display fix
def test_conversion_to_text():
    assert value('=1/4&""') == "0.25"
    assert value('=1234567&""') == "1234567"
    assert value('=A1&"!"', A1="TRUE") == "TRUE!"
    assert value('=A1&"x"') == "x"
    assert is_error(value('=1/0&"x"'), "#DIV/0!")


# spec: text T4
def test_len_upper_lower():
    assert value('=LEN("hello")') == 5
    assert value("=LEN(123)") == 3
    assert value('=UPPER("aBc")') == "ABC"
    assert value('=LOWER("aBc")') == "abc"


# spec: text T4 (TRIM)
def test_trim():
    assert value('=TRIM("  a   b  c ")') == "a b c"


# spec: text T5
def test_left_right():
    assert value('=LEFT("hello", 2)') == "he"
    assert value('=LEFT("hello")') == "h"
    assert value('=RIGHT("hello", 3)') == "llo"
    assert value('=RIGHT("hello", 9)') == "hello"


# spec: text T5 (MID)
def test_mid():
    assert value('=MID("spreadsheet", 3, 4)') == "read"
    assert value('=MID("abc", 2, 10)') == "bc"


# spec: text T5 (a count of 0 is valid and returns no characters)
def test_zero_counts():
    assert value('=LEFT("abc", 0)') == ""
    assert value('=RIGHT("abc", 0)') == ""
    assert value('=MID("abc", 2, 0)') == ""


# spec: text T5 (invalid counts)
def test_invalid_counts():
    assert is_error(value('=LEFT("abc", -1)'), "#VALUE!")
    assert is_error(value('=MID("abc", 0, 1)'), "#VALUE!")
    assert is_error(value('=LEFT("abc", "x")'), "#VALUE!")


# spec: text T6
def test_text_is_not_a_number():
    assert is_error(value('="1"+1'), "#VALUE!")
