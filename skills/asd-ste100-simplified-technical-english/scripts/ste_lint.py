#!/usr/bin/env python3
"""Report the text that does not obey the rules of the asd-ste100-simplified-technical-english skill.

Usage:
    python3 ste_lint.py FILE [FILE ...]
    python3 ste_lint.py < draft.md
    python3 ste_lint.py --strict FILE
    python3 ste_lint.py --prose FILE

With --strict, a warning also causes exit status 1. With --prose, the linter
examines each file as prose, for all extensions.

Prose files (.md, .markdown, .mdx, .txt, .rst, and stdin):
    The linter examines paragraphs, list items, table cells, and headings.
    It does not examine fenced code blocks, YAML front matter, HTML comments,
    or the header row of a table. Text in code font, bold, italics, or
    quotation marks is quoted text. It counts as one word, and the linter does
    not examine its words. The linter also does not examine the text between
    <!-- ste-lint: off --> and <!-- ste-lint: on -->.

Source files (.py, .js, .ts, .go, .rs, .java, .c, .rb, .sh, .yaml, and others):
    The linter examines only comments and docstrings. It does not examine a
    line that starts with a shell prompt or a doctest prompt.

The linter examines these items:
    - The length of each sentence, with the word count of STE rule 8
    - Verb forms, modal verbs, and the passive voice
    - Contractions, semicolons, and Latin abbreviations
    - Words that end in "-ing", phrasal verbs, and pronouns
    - The length of each paragraph
    - The words in references/vocabulary.md and references/software-terms.md.

The linter cannot find the part of speech or the meaning of a word, the topic
of a sentence or a paragraph, or multi-word nouns. A person must do those
checks.

Output: PATH:LINE: [error|warning] RULE: "text" -> advice
Exit status: 1 if there is an error, or a warning with --strict. 2 if the
linter cannot read a file. 0 in all other conditions.

The script reports problems. It does not change the text. It uses only the
standard library of Python 3.8 or a subsequent version.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import tokenize
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Set, Tuple

ERROR = "error"
WARNING = "warning"

SKILL_DIR = Path(__file__).resolve().parent.parent
VOCABULARY_FILE = SKILL_DIR / "references" / "vocabulary.md"
SOFTWARE_TERMS_FILE = SKILL_DIR / "references" / "software-terms.md"

PROCEDURAL_LIMIT = 20
DESCRIPTIVE_LIMIT = 25
PARAGRAPH_LIMIT = 6

# A placeholder for quoted text: code, bold, italics, quotations, links' URLs.
# It counts as one word (rule 8.6) and no word rule examines it.
Q = "‹q›"


@dataclass
class Finding:
    line: int
    severity: str
    rule: str
    text: str
    advice: str


@dataclass
class Unit:
    """A block of prose: a paragraph, a list item, a table cell, or a heading."""

    kind: str  # "para", "item", "cell", "heading"
    lines: List[Tuple[int, str]] = field(default_factory=list)
    ordered: bool = False
    raw_first: str = ""

    def text(self) -> str:
        return "\n".join(t for _, t in self.lines)

    def line_at(self, offset: int) -> int:
        count = self.text()[:offset].count("\n")
        return self.lines[min(count, len(self.lines) - 1)][0]


# ---------------------------------------------------------------------------
# Word forms


DOUBLE_FINAL = {
    "set", "shut", "run", "spin", "dig", "begin", "get", "put", "cut", "hit",
    "stop", "plan", "drop", "ship", "skip", "admit", "commit", "omit", "refer",
    "occur", "prefer", "rebut", "wrap", "log", "tag",
}
IRREGULAR: Dict[str, Tuple[str, ...]] = {
    "be": ("is", "are", "was", "were", "been", "being", "am"),
    "have": ("has", "had", "having"),
    "do": ("does", "did", "done", "doing"),
    "go": ("goes", "went", "gone", "going"),
    "come": ("came",),
    "find": ("found",),
    "take": ("took", "taken"),
    "give": ("gave", "given"),
    "run": ("ran",),
    "deal": ("dealt",),
    "lead": ("led",),
    "hold": ("held",),
    "keep": ("kept",),
    "break": ("broke", "broken"),
    "bring": ("brought",),
    "show": ("shown",),
    "spin": ("spun",),
    "dig": ("dug",),
    "fall": ("fell", "fallen"),
    "begin": ("began", "begun"),
    "choose": ("chose", "chosen"),
    "understand": ("understood",),
    "seek": ("sought",),
    "build": ("built",),
    "dive": ("dove",),
}


def verb_forms(verb: str) -> Set[str]:
    """Return the inflections of an English verb. For a regular verb, the result is a close guess."""
    forms = {verb}
    forms.update(IRREGULAR.get(verb, ()))
    if verb.endswith("ie"):
        forms.update({verb + "s", verb + "d", verb[:-2] + "ying"})
    elif verb.endswith("e"):
        forms.update({verb + "s", verb + "d", verb[:-1] + "ing"})
    elif verb.endswith("y") and len(verb) > 1 and verb[-2] not in "aeiou":
        forms.update({verb[:-1] + "ies", verb[:-1] + "ied", verb + "ing"})
    elif verb.endswith(("s", "x", "z", "ch", "sh")):
        forms.update({verb + "es", verb + "ed", verb + "ing"})
    else:
        forms.update({verb + "s", verb + "ed", verb + "ing"})
    if verb in DOUBLE_FINAL:
        forms.update({verb + verb[-1] + "ing", verb + verb[-1] + "ed"})
    return forms


def noun_forms(noun: str) -> Set[str]:
    if noun.endswith("y") and len(noun) > 1 and noun[-2] not in "aeiou":
        return {noun, noun[:-1] + "ies"}
    if noun.endswith(("s", "x", "z", "ch", "sh")):
        return {noun, noun + "es"}
    return {noun, noun + "s"}


def phrase_forms(phrase: str, pos: str) -> Set[str]:
    """Inflect the first word of a phrase (for verbs) or the last word (for nouns)."""
    words = phrase.split()
    if pos == "v":
        if words[0].endswith("ing") and len(words) > 1:
            return {phrase}
        return {" ".join([form] + words[1:]) for form in verb_forms(words[0])}
    if pos == "n":
        return {" ".join(words[:-1] + [form]) for form in noun_forms(words[-1])}
    return {phrase}


def words_regex(phrases: Set[str]) -> str:
    alternatives = sorted(phrases, key=len, reverse=True)
    body = "|".join(re.escape(p).replace(r"\ ", r"\s+") for p in alternatives)
    return r"(?<![\w'’-])(?:" + body + r")(?![\w'’-])"


# ---------------------------------------------------------------------------
# Word lists from references/vocabulary.md and references/software-terms.md


@dataclass
class WordRule:
    pattern: re.Pattern
    severity: str
    rule: str
    advice: str
    position: str  # "", "verb", "noun", "adj": report only in this position


STATUS = {
    "not approved": (ERROR, "1.1", ""),
    "not listed": (ERROR, "1.1", ""),
    "phrasal verb": (ERROR, "9.3", ""),
    "jargon": (ERROR, "1.10", ""),
    "noun only": (WARNING, "1.2", "verb"),
    "technical noun only": (WARNING, "1.1", ""),
    "verb only": (WARNING, "1.2", "noun"),
}
ROW = re.compile(r"^\|\s*(?P<words>[^|]+?)\s*\|\s*(?P<status>[^|]+?)\s*\|\s*(?P<use>.+?)\s*\|\s*$")
ITALIC = re.compile(r"\*([^*]+)\*")
POS = re.compile(r"\((n|v|adj|adv|conj|prep|pron)\)\s*$")
APPROVED_FORM = re.compile(r"(?:adjective|noun|form) \*([^*]+)\* is approved", re.IGNORECASE)


def strip_markup(text: str) -> str:
    return re.sub(r"[*`]", "", text).strip()


def load_word_rules(path: Path) -> List[WordRule]:
    rules: List[WordRule] = []
    if not path.is_file():
        return rules
    for line in path.read_text(encoding="utf-8").splitlines():
        match = ROW.match(line)
        if not match:
            continue
        status = match.group("status").strip().lower()
        if status not in STATUS:
            continue
        cell = match.group("words")
        pos_match = POS.search(cell)
        pos = pos_match.group(1) if pos_match else ""
        phrases: Set[str] = set()
        approved = {w.lower() for w in APPROVED_FORM.findall(match.group("use"))}
        for word in ITALIC.findall(cell):
            word = word.strip()
            if pos in ("v", "n"):
                phrases.update(phrase_forms(word, pos))
            else:
                phrases.add(word)
        phrases = {p for p in phrases if p.lower() not in approved}
        severity, rule, position = STATUS[status]
        if pos == "adj" and status in ("noun only", "verb only", "technical noun only"):
            position = "adj"
        flags = 0 if any(w.isupper() for w in phrases) else re.IGNORECASE
        rules.append(
            WordRule(
                pattern=re.compile(words_regex(phrases), flags),
                severity=severity,
                rule=rule,
                advice=strip_markup(match.group("use")),
                position=position,
            )
        )
    return rules


def load_technical_nouns(path: Path) -> Set[str]:
    """Italic terms in the "Technical nouns" section of software-terms.md."""
    terms: Set[str] = set()
    if not path.is_file():
        return terms
    section = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
            continue
        if section == "technical nouns":
            line = re.sub(r"\*\*[^*]+\*\*", "", line)
            terms.update(t.strip().lower() for t in ITALIC.findall(line))
    return terms


# ---------------------------------------------------------------------------
# Rules that do not come from references/vocabulary.md

COULD = re.compile(r"\bcould\b", re.IGNORECASE)

CONTRACTION = re.compile(
    r"\b(?:\w+n['’]t|(?:i|you|we|they|he|she|it|that|there|here|what|who|where|when|how|let)"
    r"['’](?:s|re|ve|ll|d|m))\b",
    re.IGNORECASE,
)
LATIN = re.compile(r"(?<!\w)(?:e\.\s?g\.|i\.\s?e\.|etc\.?|et al\.?|vs\.?|cf\.|viz\.|n\.b\.)(?!\w)", re.IGNORECASE)
GENDERED = re.compile(r"\b(?:he|she|him|his|her|hers|himself|herself)\b", re.IGNORECASE)
FIRST_SINGULAR = re.compile(r"(?<![\w'])(?:I|me|my|mine|myself)(?![\w'])")
FIRST_PLURAL = re.compile(r"\b(?:we|us|our|ours|ourselves)\b", re.IGNORECASE)
MAKE_SURE = re.compile(r"\bmak(?:e|es|ing)\s+sure\b(?!\s+that\b)", re.IGNORECASE)
RECOMMEND_YOU = re.compile(r"\brecommends?\s+(?:you|the)\b", re.IGNORECASE)
THIS_VERB = re.compile(
    r"^(?:This|These|That)\s+(?:is|was|are|were|means|meant|makes|made|lets|causes|caused|will|can|shows|gives|helps|also)\b"
)
DASH = re.compile(r"\s?—\s?|\s--\s|\s–\s")
SEMICOLON = re.compile(r";")

BE = r"(?:is|are|was|were|be|been|being|am)"
# No alternative can match a word that "\w+ly" also matches ("only", "usually"). If two
# alternatives can match one word, the time of the backtracking is exponential in the number
# of adverbs.
ADVERBS = r"(?:\s+(?:not|also|then|now|already|still|always|\w+ly))*"
PARTICIPLES = (
    "built|done|found|given|gone|known|made|seen|sent|set|shown|taken|told|written|kept|held|left|lost|"
    "meant|put|cut|begun|broken|chosen|drawn|driven|fallen|forgotten|frozen|hidden|led|paid|said|sold|"
    "spent|split|spun|stuck|thrown|understood|won|worn|bound|caught|dealt|fed|felt|fought|got|gotten|"
    "heard|hit|hurt|let|lit|overridden|rebuilt|reset|shut|sought|stolen|struck|swept|taught|thought|run|read"
)
PARTICIPLE = r"(?:\w+ed|" + PARTICIPLES + r")"
PERFECT = re.compile(r"\b(?:has|have|had)" + ADVERBS + r"\s+(?:been|" + PARTICIPLE + r")\b", re.IGNORECASE)
PASSIVE = re.compile(r"\b" + BE + ADVERBS + r"\s+(" + PARTICIPLE + r")\b(\s+by\b)?", re.IGNORECASE)
PROGRESSIVE = re.compile(r"\b" + BE + ADVERBS + r"\s+(\w+ing)\b", re.IGNORECASE)
ING = re.compile(r"(?<![\w'-])([A-Za-z]+ing)(?![\w'-])")
ING_STEMS = {
    "thing", "things", "something", "nothing", "anything", "everything", "string", "strings",
    "ring", "rings", "spring", "king", "sing", "wing", "wings", "bring", "sting", "swing",
    "ceiling", "during", "morning", "evening", "lightning", "opening", "openings", "lighting",
    "routing", "servicing", "mating", "missing", "remaining", "warning", "warnings", "bearing",
    "housing", "fitting", "fittings", "coupling", "sealing", "packaging", "packing", "shipping",
    "handling", "cleaning", "testing", "troubleshooting", "engineering", "building", "setting",
    "settings", "heading", "headings", "listing", "billing", "pricing", "wording", "meaning",
    "meanings", "spelling", "training", "offering", "painting", "drawing", "drawings",
}
ING_BEFORE = re.compile(
    r"\b(?:by|for|of|in|on|with|without|before|after|when|while|from|about|to|at|into|than|instead)\s+$",
    re.IGNORECASE,
)

DETERMINERS = r"(?:the|a|an|this|that|these|those|its|your|their|each|some|no|any|of|for|with|one|more)"
VERB_CONTEXT = re.compile(
    r"(?:\b(?:to|you|we|i|they|it|must|can|cannot|will|do|does|did|not|then|please)\s+|^)$",
    re.IGNORECASE,
)
NOUN_CONTEXT = re.compile(r"\b" + DETERMINERS + r"\s+$", re.IGNORECASE)
ADJ_CONTEXT = re.compile(r"\b(?:is|are|was|were|be|been|become|becomes|a|an|the|fully|not)\s+$", re.IGNORECASE)

# Verbs that frequently start an instruction. If a sentence starts with one of
# these verbs (after a condition), the sentence is procedural.
IMPERATIVE = set(
    "add apply attach calculate cancel change clean close compare complete configure connect "
    "continue copy correct count cut decrease delete deploy disable disconnect divide do "
    "download drag enable enter erase examine find get give go identify ignore include "
    "increase install keep let load lock look make measure merge monitor move obey open "
    "operate paste prepare press prevent pull push put read record refer release remove "
    "rename repair replace restart run save select send set show start stop tag tell try "
    "turn type unlock update upgrade upload use wait write check ensure verify confirm "
    "create fix build test perform execute implement specify provide avoid review commit "
    "rebase fetch clone revert import export call return raise log print "
    .split()
)
CONDITION = re.compile(
    r"^(?:if|when|before|after|until|unless|while|during|to|for|in|on|at)\b[^,]*,\s*", re.IGNORECASE
)
LATER_CONDITION = re.compile(
    r"[^,]\s(?:(?:if|when|unless|until|once)\s|(?:before|after)\s+(?:you|it|they|we|i|the \w+ (?:is|are|was|has|runs|fails|passes))\b)",
    re.IGNORECASE,
)
NOTE_PREFIX = re.compile(r"^\s*(?:\*\*|__)?note(?:\*\*|__)?\s*:", re.IGNORECASE)
SAFETY_PREFIX = re.compile(r"^\s*(?:\*\*|__)?(?:warning|caution)(?:\*\*|__)?\s*:", re.IGNORECASE)

ABBREVIATIONS = {
    "e.g", "i.e", "etc", "vs", "no", "fig", "approx", "dr", "mr", "ms", "mrs", "st", "a.m", "p.m",
    "u.s", "cf", "viz", "al", "inc", "ltd", "jr", "sr", "v", "ver", "min", "max", "sec",
}


# ---------------------------------------------------------------------------
# Prose extraction

FENCE = re.compile(r"^\s*(```+|~~~+)")
HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
BULLET = re.compile(r"^(\s*)([-*+])\s+(.*)$")
ORDERED = re.compile(r"^(\s*)(\d+|[a-zA-Z])[.)]\s+(.*)$")
TABLE_SEPARATOR = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?$")
HORIZONTAL_RULE = re.compile(r"^\s*([-*_])\s*(\1\s*){2,}$")
BLOCKQUOTE = re.compile(r"^\s*>\s?")
LINT_OFF = re.compile(r"<!--\s*ste-lint:\s*off\s*-->")
LINT_ON = re.compile(r"<!--\s*ste-lint:\s*on\s*-->")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

# Each span has a maximum length. Without it, a paragraph with many markers that do not
# close takes a time that is the square of its length.
INLINE_CODE = re.compile(r"(`+)(?!`)(.{1,2000}?)(?<!`)\1", re.DOTALL)
BOLD = re.compile(r"\*\*(?=\S)(.{1,500}?)(?<=\S)\*\*|__(?=\S)(.{1,500}?)(?<=\S)__", re.DOTALL)
ITALIC_SPAN = re.compile(
    r"(?<![\w*])\*(?=[^\s*])(.{1,500}?)(?<=[^\s*])\*(?![\w*])|(?<![\w_])_(?=\S)(.{1,500}?)(?<=\S)_(?![\w_])", re.DOTALL
)
QUOTED = re.compile(r"\"[^\"]{1,300}?\"|\u201c[^\u201d]{1,300}?\u201d")
LINK = re.compile(r"!?\[([^\]]{0,500})\]\([^)]{0,2000}\)")
URL = re.compile(r"https?://\S+|www\.\S+")
FILE_PATH = re.compile(
    r"(?<![\w/])(?:[\w.-]+/)+[\w.-]*[\w-]|\b[\w-]+\.(?:md|py|txt|json|ya?ml|toml|sh|js|ts|rs|go|html|css|cfg|ini|lock)\b"
)
HTML_TAG = re.compile(r"</?[a-zA-Z][^>]*>")
ENTITY = re.compile(r"&[a-zA-Z]+;|&#\d+;")


def blank(match: re.Match) -> str:
    return Q + "\n" * match.group(0).count("\n")


def clean_spans(text: str) -> str:
    """Replace quoted text with the placeholder and remove markup."""
    text = HTML_COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    text = INLINE_CODE.sub(blank, text)
    text = LINK.sub(lambda m: m.group(1), text)
    text = URL.sub(Q, text)
    text = FILE_PATH.sub(Q, text)
    text = HTML_TAG.sub("", text)
    text = ENTITY.sub(" ", text)
    text = BOLD.sub(blank, text)
    text = ITALIC_SPAN.sub(blank, text)
    text = QUOTED.sub(blank_quote, text)
    return text


def blank_quote(match: re.Match) -> str:
    """Replace a quotation with the placeholder, and keep the period at the end of the quotation."""
    inner = match.group(0)[1:-1].rstrip()
    end = inner[-1] if inner and inner[-1] in ".!?" else ""
    return Q + end + "\n" * match.group(0).count("\n")


def markdown_units(text: str) -> Iterator[Unit]:
    lines = text.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() in ("---", "..."):
                start = index + 1
                break
    in_fence = False
    fence_char = ""
    off = False
    in_comment = False
    in_list = False
    current: Optional[Unit] = None

    def flush() -> Iterator[Unit]:
        nonlocal current
        if current is not None and current.lines:
            yield current
        current = None

    for index in range(start, len(lines)):
        number = index + 1
        line = lines[index]
        if off:
            if LINT_ON.search(line):
                off = False
            continue
        if LINT_OFF.search(line):
            yield from flush()
            off = True
            continue
        fence = FENCE.match(line)
        if fence:
            yield from flush()
            char = fence.group(1)[0]
            if not in_fence:
                in_fence, fence_char = True, char
            elif char == fence_char:
                in_fence = False
            continue
        if in_fence:
            continue
        if in_comment:
            if "-->" in line:
                in_comment = False
                line = line.split("-->", 1)[1]
            else:
                continue
        if "<!--" in line and "-->" not in line.split("<!--", 1)[1]:
            in_comment = True
            line = line.split("<!--", 1)[0]
        line = BLOCKQUOTE.sub("", line)
        stripped = line.strip()
        if not stripped or HORIZONTAL_RULE.fullmatch(stripped):
            yield from flush()
            continue
        indented = line.startswith(("    ", "\t"))
        if current is None and indented and not in_list:
            continue  # An indented code block: code, not prose. In a list, it continues an item.
        heading = HEADING.match(line)
        if heading:
            yield from flush()
            in_list = False
            yield Unit("heading", [(number, heading.group(2))])
            continue
        if stripped.startswith("|"):
            yield from flush()
            in_list = False
            if TABLE_SEPARATOR.fullmatch(stripped):
                continue
            following = lines[index + 1].strip() if index + 1 < len(lines) else ""
            if TABLE_SEPARATOR.fullmatch(following):
                continue  # A header row gives labels, not sentences.
            for cell in stripped.strip("|").split("|"):
                if cell.strip():
                    yield Unit("cell", [(number, cell.strip())])
            continue
        bullet = BULLET.match(line)
        ordered = ORDERED.match(line)
        if bullet or ordered:
            yield from flush()
            in_list = True
            item = bullet or ordered
            current = Unit("item", [(number, item.group(3))], ordered=bool(ordered and not bullet))
            current.raw_first = item.group(3)
            continue
        if current is None:
            if not indented:
                in_list = False
            current = Unit("para", [(number, stripped)])
            current.raw_first = stripped
        else:
            current.lines.append((number, stripped))
    yield from flush()


HASH_COMMENT = {".py", ".sh", ".bash", ".zsh", ".rb", ".pl", ".r", ".yaml", ".yml", ".toml", ".cfg", ".conf", ".ini", ".mk", ".nix", ".tf", ".ps1"}
SLASH_COMMENT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".kt", ".kts", ".scala", ".swift", ".c", ".h", ".cc", ".cpp", ".hpp", ".cs", ".dart", ".php", ".proto", ".zig"}
DASH_COMMENT = {".sql", ".lua", ".hs", ".elm"}
BLOCK_COMMENT = SLASH_COMMENT | {".css", ".scss", ".less", ".sql"}
SOURCE_SUFFIXES = HASH_COMMENT | SLASH_COMMENT | DASH_COMMENT | BLOCK_COMMENT
DOC_FIELD = re.compile(r"^\s*(?:[:@][\w ]+:?|\w[\w. ]*(?:\s*\([^)]*\))?:\s|(?:Args|Arguments|Returns|Yields|Raises|Throws|Examples?|Notes?|Attributes|Parameters|See Also|Usage)\s*:?\s*$|.*:$)")


def python_comments(text: str) -> Optional[Dict[int, str]]:
    """Map line numbers to the comment and docstring text of Python source, from its tokens.

    A docstring is a string that is a full statement. Strings in expressions are code. The
    result is None if the tokenizer cannot read the source.
    """
    found: Dict[int, List[str]] = {}

    def add(line: int, body: str) -> None:
        found.setdefault(line, []).append(body.strip())

    previous = tokenize.NEWLINE
    pending: Optional[tokenize.TokenInfo] = None
    try:
        for token in tokenize.generate_tokens(io.StringIO(text).readline):
            if token.type == tokenize.COMMENT:
                if not (token.start[0] == 1 and token.string.startswith("#!")):
                    add(token.start[0], token.string[1:])
                continue
            if token.type == tokenize.NL:
                continue
            if pending is not None and token.type in (tokenize.NEWLINE, tokenize.ENDMARKER):
                quote = re.match(r"[a-zA-Z]*(\"\"\"|'''|\"|')", pending.string)
                width = len(quote.group(1)) if quote else 0
                body = pending.string[quote.end() if quote else 0:len(pending.string) - width]
                for offset, part in enumerate(body.split("\n")):
                    add(pending.start[0] + offset, part)
            pending = None
            if token.type == tokenize.STRING and previous in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT):
                pending = token
            previous = token.type
    except (tokenize.TokenError, SyntaxError):
        return None
    return {line: " ".join(p for p in parts if p) for line, parts in found.items()}


def closing_quote(line: str, start: int, quote: str) -> int:
    """Return the index of the quote that closes a string, or -1. A backslash escapes the next character."""
    index = start
    while index < len(line):
        if line[index] == "\\":
            index += 2
            continue
        if line[index] == quote:
            return index
        index += 1
    return -1


def scan_line(line: str, suffix: str, block: bool) -> Tuple[str, bool]:
    """Return the comment text of one source line, and True if a block comment continues after it.

    A comment marker in a string is code. A quotation mark starts a string only if the
    line also closes the string, thus an apostrophe (a Rust lifetime, a word in a shell
    script) does not hide the comment after it.
    """
    parts: List[str] = []
    index = 0
    if block:
        end = line.find("*/")
        if end < 0:
            return re.sub(r"^\s*\*\s?", "", line).strip(), True
        parts.append(re.sub(r"^\s*\*\s?", "", line[:end]))
        index = end + 2
    while index < len(line):
        char = line[index]
        before = line[index - 1] if index else " "
        if char in "\"'`":
            end = closing_quote(line, index + 1, char)
            if end >= 0:
                index = end + 1
                continue
        if suffix in BLOCK_COMMENT and line.startswith("/*", index):
            end = line.find("*/", index + 2)
            if end < 0:
                parts.append(line[index + 2:].lstrip("*"))
                return " ".join(p.strip() for p in parts if p.strip()), True
            parts.append(line[index + 2:end].lstrip("*"))
            index = end + 2
            continue
        if suffix in SLASH_COMMENT and line.startswith("//", index) and not (before == ":" or before.isalnum() or before == "_"):
            parts.append(line[index:].lstrip("/").lstrip("!"))
            break
        if suffix in HASH_COMMENT and char == "#" and before.isspace() and not line.startswith(("#{", "#!"), index):
            parts.append(line[index + 1:])
            break
        if suffix in DASH_COMMENT and line.startswith("--", index) and before.isspace():
            parts.append(line[index + 2:])
            break
        index += 1
    return " ".join(p.strip() for p in parts if p.strip()), False


def comment_lines(text: str, suffix: str) -> Iterator[Tuple[int, str]]:
    """Yield (line number, comment text) for each line of a source file. The text is empty for a line of code.

    If the Python tokenizer cannot read a .py file, the linter examines only its comments.
    """
    lines = text.splitlines()
    if suffix == ".py":
        found = python_comments(text)
        if found is not None:
            for number in range(1, max(len(lines), max(found, default=0)) + 1):
                yield number, found.get(number, "")
            return
    block = False
    for number, line in enumerate(lines, start=1):
        if number == 1 and line.startswith("#!"):
            yield number, ""
            continue
        body, block = scan_line(line, suffix, block)
        yield number, body


PROMPT = re.compile(r"^(?:\$ |>>>|\.\.\. |python3? |uv run |pip |npm |npx )")
ITEM = re.compile(r"^(?:[-*+]|\d+[.)])\s+")


def source_units(text: str, suffix: str) -> Iterator[Unit]:
    current: Optional[Unit] = None
    for number, body in comment_lines(text, suffix):
        if PROMPT.match(body):
            body = ""
        if ITEM.match(body):
            if current is not None:
                yield current
            current = Unit("item", [(number, ITEM.sub("", body))])
            current.raw_first = current.lines[0][1]
            continue
        if not body or re.fullmatch(r"[-=*#/~]+", body):
            if current is not None:
                yield current
            current = None
            continue
        if DOC_FIELD.match(body) and current is not None:
            yield current
            current = None
        if current is None:
            current = Unit("para", [(number, body)])
            current.raw_first = body
        else:
            current.lines.append((number, body))
    if current is not None:
        yield current


# ---------------------------------------------------------------------------
# Sentences and word count


SPLIT = re.compile(r"(?<=[.!?])[\"')\]”]*\s+(?=[A-Z0-9\"'(\[“‹])")


def sentences(text: str) -> Iterator[Tuple[int, str]]:
    """Yield (offset, sentence) for each sentence of a unit's text."""
    start = 0
    for match in SPLIT.finditer(text):
        before = text[start:match.start()].rstrip("\"')]”")
        last = re.search(r"([\w.]+)\.$", before)
        if last and (last.group(1).lower() in ABBREVIATIONS or re.fullmatch(r"[A-Z]", last.group(1))):
            continue
        yield start, text[start:match.start()]
        start = match.end()
    if text[start:].strip():
        yield start, text[start:]


PAREN = re.compile(r"\([^()]*\)")
NUMBER = re.compile(r"^[~≈<>+-]?\d[\d.,:x]*%?$")
# Units of measurement (rule 8.6). A short word after a number is not always a unit: "3 of 5 pods".
UNIT_SYMBOLS = set(
    "% s ms us µs ns min h hr hrs d B kB KB MB GB TB PB KiB MiB GiB TiB b Kb Mb Gb bps kbps Mbps Gbps "
    "Hz kHz MHz GHz V mV A mA W kW °C °F K m cm mm km g kg mg lb lbs ft px pt em rem rpm psi Nm L mL x "
    "req rps qps ops dpi".split()
)
UNIT_NAMES = set(
    "second millisecond microsecond nanosecond minute hour day week month year byte kilobyte megabyte "
    "gigabyte terabyte bit percent degree pixel meter metre kilometer centimeter millimeter gram kilogram "
    "volt watt ohm inch inches foot feet".split()
)


def is_unit(token: str) -> bool:
    word = token.rstrip(".,:;)")
    parts = word.split("/")
    return bool(word) and all(
        part in UNIT_SYMBOLS or part.lower() in UNIT_NAMES or part.lower()[:-1] in UNIT_NAMES for part in parts
    )


def count_words(sentence: str) -> int:
    """Count the words of a sentence as STE rules 8.4 to 8.7 tell."""
    text = PAREN.sub(" " + Q + " ", sentence)
    tokens = [t for t in re.split(r"\s+", text) if re.search(r"[\w‹]", t)]
    count = 0
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if NUMBER.match(token) and index + 1 < len(tokens) and is_unit(tokens[index + 1]):
            index += 2
            count += 1
            continue
        # A run of capitalized words after the first word is one proper noun.
        if index > 0 and token[:1].isupper() and not token.isupper():
            while index + 1 < len(tokens) and tokens[index + 1][:1].isupper() and not tokens[index + 1].isupper():
                index += 1
        count += 1
        index += 1
    return count


def first_word(sentence: str) -> str:
    body = CONDITION.sub("", sentence.strip(), count=1)
    match = re.match(r"[\s\-‹›q(*]*([A-Za-z]+)", body)
    return match.group(1).lower() if match else ""


def is_procedural(sentence: str) -> bool:
    word = first_word(sentence)
    if word in IMPERATIVE:
        return True
    return bool(re.match(r"^\s*(?:do not|make sure|be careful)\b", CONDITION.sub("", sentence.strip(), count=1), re.IGNORECASE))


# ---------------------------------------------------------------------------
# Checks


class Linter:
    def __init__(self) -> None:
        self.word_rules = load_word_rules(VOCABULARY_FILE) + load_word_rules(SOFTWARE_TERMS_FILE)
        self.technical_nouns = load_technical_nouns(SOFTWARE_TERMS_FILE)
        multi: Set[str] = set()
        for term in self.technical_nouns:
            if " " in term:
                multi.update(phrase_forms(term, "n"))
        self.multiword = re.compile(words_regex(multi), re.IGNORECASE) if multi else None

    def check_unit(self, unit: Unit) -> List[Finding]:
        findings: List[Finding] = []
        text = clean_spans(unit.text())
        if unit.kind == "heading":
            self.check_words(unit, text, 0, findings, heading=True)
            return findings
        note = bool(NOTE_PREFIX.match(unit.raw_first))
        safety = bool(SAFETY_PREFIX.match(unit.raw_first))
        count = 0
        for offset, sentence in sentences(text):
            if not re.search(r"[A-Za-z]", sentence.replace(Q, "")):
                continue
            count += 1
            line = unit.line_at(offset)
            self.check_sentence(unit, sentence, line, note, findings, safety)
            self.check_words(unit, text, offset, findings, sentence=sentence)
        if unit.kind == "para" and count > PARAGRAPH_LIMIT:
            findings.append(Finding(unit.lines[0][0], WARNING, "6.6", f"{count} sentences", f"a paragraph has {PARAGRAPH_LIMIT} sentences or less. Divide it."))
        return findings

    def check_sentence(self, unit: Unit, sentence: str, line: int, note: bool, findings: List[Finding], safety: bool = False) -> None:
        body = NOTE_PREFIX.sub("", sentence) if note else SAFETY_PREFIX.sub("", sentence) if safety else sentence
        procedural = not note and is_procedural(body)
        # Rule 5.1: the sentences of a warning or a caution also have the limit of a procedure.
        limit = PROCEDURAL_LIMIT if procedural or safety else DESCRIPTIVE_LIMIT
        words = count_words(body)
        if words > limit and unit.kind != "cell":
            kind = "procedural" if procedural else "safety instruction" if safety else "descriptive"
            rule = "5.1" if procedural or safety else "6.3"
            findings.append(Finding(line, ERROR, rule, excerpt(sentence), f"{words} words. The limit for a {kind} sentence is {limit}. Divide it."))
        if note and is_procedural(body):
            findings.append(Finding(line, WARNING, "5.5", excerpt(sentence), "a note gives information only. Make the command a step."))
        if procedural:
            stripped = CONDITION.sub("", body.strip(), count=1)
            if LATER_CONDITION.search(stripped) and not CONDITION.match(body.strip()):
                findings.append(Finding(line, WARNING, "5.4", excerpt(sentence), "put the condition first, then a comma, then the command"))
            if re.search(r",\s*then\s|\band then\b", stripped, re.IGNORECASE):
                findings.append(Finding(line, WARNING, "5.2", excerpt(sentence), "write one instruction in each sentence"))
        if THIS_VERB.match(body.strip()):
            findings.append(Finding(line, WARNING, "GR-4", excerpt(sentence, 40), "if 'this' can refer to more than one item, put a noun after it"))

    def check_words(self, unit: Unit, text: str, offset: int, findings: List[Finding], sentence: Optional[str] = None, heading: bool = False) -> None:
        segment = sentence if sentence is not None else text
        masked = segment
        if self.multiword is not None:
            masked = self.multiword.sub(lambda m: Q + " " * (len(m.group(0)) - len(Q)), segment)

        def report(match: re.Match, severity: str, rule: str, advice: str, source: str = masked) -> None:
            line = unit.line_at(offset + match.start())
            findings.append(Finding(line, severity, rule, match.group(0).strip(), advice))

        for match in SEMICOLON.finditer(masked):
            report(match, ERROR, "8.1", "do not use a semicolon. Write two sentences.")
        for match in CONTRACTION.finditer(masked):
            report(match, ERROR, "4.2", "write the words in full: do not, is not, it is")
        for match in LATIN.finditer(masked):
            report(match, ERROR, "GR-6", "for example, that is, and other items, compare")
        for match in GENDERED.finditer(masked):
            report(match, ERROR, "GR-7", "they, them, their, or the role (the user, the reviewer)")
        for match in FIRST_SINGULAR.finditer(masked):
            report(match, WARNING, "GR-3", "STE has no first person. Rewrite in a document. In a reply, keep it only where the reader must know what you did.")
        for match in FIRST_PLURAL.finditer(masked):
            report(match, WARNING, "GR-3", "use 'we' only for the organization that publishes the document")
        for match in COULD.finditer(masked):
            report(match, WARNING, "3.1", "use 'could' only as the past tense of 'can'. For a possibility, use can or possibly.")
        for match in PERFECT.finditer(masked):
            if re.search(r"\b(?:must|can|cannot|will|to)(?:\s+not)?\s+$", masked[:match.start()], re.IGNORECASE):
                continue  # "must have" + an adjective: "have" is the primary verb.
            report(match, ERROR, "3.4", "use the simple past or the simple present")
        for match in PROGRESSIVE.finditer(masked):
            if match.group(1).lower() not in ING_STEMS and match.group(1).lower() not in self.technical_nouns:
                report(match, ERROR, "3.2", "use the simple present, past, or future: 'runs', not 'is running'")
        for match in PASSIVE.finditer(masked):
            if match.group(2):
                report(match, ERROR, "3.6", "passive voice with a known agent. Make the agent the subject.")
            else:
                report(match, WARNING, "3.6", "possibly passive voice. Name the agent, unless the agent is unknown or the participle shows a condition.")
        if not heading:
            for match in ING.finditer(masked):
                word = match.group(1).lower()
                if word in ING_STEMS or word in self.technical_nouns or len(word) <= 4:
                    continue
                before = masked[:match.start()]
                if PROGRESSIVE.search(masked[max(0, match.start() - 40):match.end()]):
                    continue
                if ING_BEFORE.search(before) or before.strip() == "" or before.rstrip().endswith((",", ":")):
                    report(match, ERROR, "3.5", "use an '-ing' word only as a technical noun. Write 'before you run', 'with X', 'that includes'.")
                else:
                    report(match, WARNING, "3.5", "use an '-ing' word only as a technical noun or in a technical noun")
        for match in MAKE_SURE.finditer(masked):
            report(match, WARNING, "GR-1", "write 'make sure that'")
        for match in RECOMMEND_YOU.finditer(masked):
            report(match, WARNING, "GR-1", "write 'recommend that'")
        for match in DASH.finditer(masked):
            report(match, WARNING, "4.1", "a dash often adds a second topic. Write two sentences.")
        for rule in self.word_rules:
            for match in rule.pattern.finditer(masked):
                if rule.position and (heading or not self.in_position(masked[:match.start()], rule.position, match.group(0))):
                    continue
                if match.group(0) == "May" and re.match(r"\s+\d", masked[match.end():]):
                    continue
                report(match, rule.severity, rule.rule, rule.advice)

    @staticmethod
    def in_position(before: str, position: str, word: str = "") -> bool:
        if position == "verb":
            if before.strip() == "" and word.lower().endswith("s"):
                return False
            return bool(VERB_CONTEXT.search(before))
        if position == "noun":
            return bool(NOUN_CONTEXT.search(before))
        if position == "adj":
            return bool(ADJ_CONTEXT.search(before))
        return True


def excerpt(sentence: str, limit: int = 60) -> str:
    text = " ".join(sentence.replace(Q, "`...`").split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def units_for(path: str, text: str, prose: bool) -> Iterator[Unit]:
    suffix = Path(path).suffix.lower() if path != "-" else ".md"
    if not prose and suffix in SOURCE_SUFFIXES:
        return source_units(text, suffix)
    return markdown_units(text)


def lint(path: str, text: str, prose: bool = False, linter: Optional[Linter] = None) -> List[Finding]:
    linter = linter or Linter()
    findings: List[Finding] = []
    for unit in units_for(path, text, prose):
        findings.extend(linter.check_unit(unit))
    unique = {(f.line, f.severity, f.rule, f.text, f.advice): f for f in findings}
    return sorted(unique.values(), key=lambda f: (f.line, f.severity != ERROR, f.rule))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("files", nargs="*", help="files to examine; reads stdin if there are none")
    parser.add_argument("--strict", action="store_true", help="exit 1 on warnings too")
    parser.add_argument("--prose", action="store_true", help="examine every file as prose")
    parser.add_argument("--quiet", action="store_true", help="print only the summary")
    args = parser.parse_args(argv)

    linter = Linter()
    errors = warnings = 0
    for target in args.files or ["-"]:
        if target == "-":
            # Decode stdin as the files are decoded: a byte that is not UTF-8 does not stop the linter.
            raw = sys.stdin.buffer.read() if hasattr(sys.stdin, "buffer") else sys.stdin.read().encode("utf-8")
            text, label = raw.decode("utf-8-sig", errors="replace"), "<stdin>"
        else:
            try:
                text = Path(target).read_text(encoding="utf-8-sig", errors="replace")
            except OSError as exc:
                print(f"{target}: {exc}", file=sys.stderr)
                return 2
            label = target
        for finding in lint(target, text, args.prose, linter):
            if finding.severity == ERROR:
                errors += 1
            else:
                warnings += 1
            if not args.quiet:
                print(f'{label}:{finding.line}: [{finding.severity}] {finding.rule}: "{finding.text}" -> {finding.advice}')
    print(f"\n{errors} errors, {warnings} warnings")
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
