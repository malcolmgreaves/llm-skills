#!/usr/bin/env python3
"""Report words and punctuation that the google-developer-style skill rules out.

Usage:
    python3 lint.py FILE [FILE ...]
    python3 lint.py < draft.md
    python3 lint.py --strict FILE     # also fail on "caution" findings
    python3 lint.py --all FILE.py     # check every line of a source file
    python3 lint.py --prose FILE      # treat the file as prose regardless of extension

Prose files (.md, .markdown, .mdx, .txt, .rst, and stdin):
    Fenced code blocks are skipped. Inline code (`term`), bold (**term**),
    and italic mentions (*term* or _term_) are ignored, and so is the first
    cell of a table row, so a document can discuss a term without being
    flagged for using it. Text between <!-- style-lint: off --> and
    <!-- style-lint: on --> is skipped.

Source files (.py, .js, .ts, .go, .rs, .java, .c, .rb, .sh, .yaml, ...):
    Only comments and docstrings are checked.

Output:  PATH:LINE: [avoid|caution] "matched text" -> suggestion
Exit:    1 if any "avoid" finding (or any finding with --strict), else 0.

The script reports; it doesn't rewrite. Standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

AVOID = "avoid"
CAUTION = "caution"

# Each rule: (regex, severity, suggestion). Word-boundary matching is
# case-insensitive unless the pattern sets its own flags.
RULES: list[tuple[str, str, str]] = []


def words(terms: str, severity: str, suggestion: str) -> None:
    """Register a rule for a |-separated list of words or phrases."""
    alternatives = [re.escape(t.strip()).replace(r"\ ", r"\s+") for t in terms.split("|")]
    RULES.append((r"\b(?:" + "|".join(alternatives) + r")\b", severity, suggestion))


def raw(pattern: str, severity: str, suggestion: str) -> None:
    RULES.append((pattern, severity, suggestion))


# --- Figurative language (SKILL.md rule 1, llm-habits.md) -------------------
words("load-bearing|load bearing", AVOID, "state what depends on it")
words("seam|seams", AVOID, "name the boundary, interface, or module")
words("footgun|footguns|gotcha|gotchas", AVOID, "describe the behavior that causes the mistake")
words("under the hood|behind the scenes|under the covers", AVOID, "delete; say what the code does")
words("low-hanging fruit|low hanging fruit|quick win|quick wins", AVOID, "name the small changes with a large effect")
words("north star", AVOID, "goal or target metric")
words("guardrail|guardrails|safety net", AVOID, "limits, checks, or validation; name them")
words("blast radius", AVOID, "affected area")
words("rabbit hole|in the weeds", AVOID, "say which details don't affect the decision")
words("moving parts", AVOID, "components; count and name them")
words("silver bullet|holy grail", AVOID, "describe what the thing does and doesn't solve")
words("plumbing", AVOID, "the code or configuration that connects A to B")
raw(r"\bwir(?:e|ed|es|ing)\s+up\b", AVOID, "connect, configure, register")
raw(r"\bhook(?:s|ed|ing)?\s+up\b", AVOID, "connect, configure")
raw(r"\bbubbl(?:e|es|ed|ing)\s+up\b", AVOID, "propagates, is re-raised, is passed to")
raw(r"\bpaper(?:s|ed|ing)?\s+over\b", AVOID, "hide, conceal, suppress")
raw(r"\bbak(?:e|es|ed|ing)\s+in\b", AVOID, "include, build in")
raw(r"\bbolt(?:s|ed|ing)?\s+on\b", AVOID, "add")
words("sharp edges|rough edges|papercut|papercuts", AVOID, "list the specific problems")
words("golden path|paved road", AVOID, "the recommended approach")
words("happy path", CAUTION, "the case where every step succeeds; define on first use if kept")
words("deep dive|deep-dive|deep dives", AVOID, "describe, examine, explain")
raw(r"\bdelv(?:e|es|ed|ing)\b", AVOID, "describe, examine, explain")
raw(r"\bdiv(?:e|es|ed|ing)\s+into\b", AVOID, "describe, examine, explain")
raw(r"\bdrill(?:s|ed|ing)?\s+down\b", AVOID, "examine; name the section")
raw(r"\bdig(?:s|ging)?\s+into\b", AVOID, "examine, read")
raw(r"\bunpack(?:s|ed|ing)?\b", CAUTION, "explain (unless literally unpacking data)")
words("zoom out|big picture|30,000-foot view|at a high level", AVOID, "in summary; this section summarizes")
words("boil the ocean|yak shaving|yak-shaving|bikeshedding|bikeshed", AVOID, "describe the work or the discussion")
words("table stakes|no-brainer|slam dunk", AVOID, "required; clearly better, and say why")
words("escape hatch", AVOID, "a way to bypass X; name it")
words("belt and suspenders", AVOID, "a redundant check")
words("single source of truth|source of truth", CAUTION, "the one place where X is defined")
words("first-class|first class citizen|second-class", AVOID, "describe what the thing can and can't do")
words("spaghetti|big ball of mud|cargo cult|cargo-cult", AVOID, "describe the coupling or the copied practice")
words("cruft|bit rot|bitrot", AVOID, "unused code; out of date")
raw(r"\bchok(?:e|es|ed|ing)\s+on\b", AVOID, "fails, returns an error, raises X")
raw(r"\b(?:blows?|blew)\s+up\b", AVOID, "fails, panics, raises X")
raw(r"\b(?:falls?|fell)\s+over\b", AVOID, "fails, stops responding")
raw(r"\bbail(?:s|ed|ing)?(?:\s+out)?\b", CAUTION, "returns early, exits")
raw(r"\bbarf(?:s|ed|ing)?\b", AVOID, "fails, returns an error")
raw(r"\bcomplain(?:s|ed|ing)?\b", AVOID, "reports an error, prints a warning (anthropomorphism)")
words("confused|gets confused|is confused", CAUTION, "misparses, treats X as Y (anthropomorphism)")
raw(r"\bswallow(?:s|ed|ing)?\b", CAUTION, "catches and discards; catches and ignores")
words("janky|jank|wonky|borked|hosed|busted", AVOID, "broken; describe the symptom")
words("brittle|fragile", CAUTION, "breaks when X changes; say what")
words("code smell|smells", CAUTION, "name the specific problem")
words("kludge|kludgy|hacky", AVOID, "workaround; say what it works around and what it costs")
words("band-aid|band aid|duct tape|duct-tape", AVOID, "temporary fix; describe it")
raw(r"\bsp(?:in|ins|un|inning)\s+up\b", AVOID, "create, start, deploy")
raw(r"\bstand(?:s|ing)?\s+up\b|\bstood\s+up\b", CAUTION, "deploy, start (if figurative)")
raw(r"\bkick(?:s|ed|ing)?\s+off\b", AVOID, "start, run")
raw(r"\bfir(?:e|es|ed|ing)\s+off\b", AVOID, "send, start")
raw(r"\bpunt(?:s|ed|ing)?\b", AVOID, "defer; say until when")
raw(r"\bnuk(?:e|es|ed|ing)\b", AVOID, "delete, remove")
raw(r"\bblow(?:s|n|ing)?\s+away\b|\bblew\s+away\b", AVOID, "delete")
raw(r"\bclobber(?:s|ed|ing)?\b|\bstomp(?:s|ed|ing)?\s+on\b", AVOID, "overwrite")
raw(r"\bmassag(?:e|es|ed|ing)\b|\bmung(?:e|es|ed|ing)\b", AVOID, "transform; say how")
raw(r"\btweak(?:s|ed|ing)?\b", CAUTION, "adjust; say what and to what")
raw(r"\bsprinkl(?:e|es|ed|ing)\b|\bpepper(?:s|ed|ing)?\b", AVOID, "add to each of; add throughout")
raw(r"\bteas(?:e|es|ed|ing)\s+apart\b", AVOID, "separate, split")
raw(r"\breach(?:es|ed|ing)?\s+for\b|\blean(?:s|ed|ing)?\s+on\b", AVOID, "use")
raw(r"\bhit(?:s|ting)?\s+(?:the\s+)?(?:api|endpoint|server|url|database|db)\b", AVOID, "send a request to; call")
raw(r"\bsurfac(?:e|es|ed|ing)\b", CAUTION, "make available, expose, report (if used as a verb)")
raw(r"\bship(?:s|ped|ping)?\b", CAUTION, "release, deploy (if figurative)")
raw(r"\b(?:lands?|landed|landing)\s+(?:in|on)\s+(?:main|master|trunk)\b", AVOID, "merged into main")
words("unlock|unlocks|empower|empowers|tap into|elevate|elevates|supercharge|turbocharge|streamline|streamlines", AVOID, "lets you; use; improves X by Y")
raw(r"\bharness(?:es|ed|ing)?\s+(?:the|its|their|your|this|these|all|our)\b", AVOID, "use (harness is fine as a noun, as in test harness)")
words("sanity check|sanity-check|sanity checks|sanity", AVOID, "quick check, confidence check, preliminary check")
words("kick the tires", AVOID, "try, test")
words("dogfood|dogfooding", CAUTION, "use internally; define on first use")
raw(r"\broll(?:s|ed|ing)?\s+out\b|\brollout\b", CAUTION, "release in stages; define what you mean")
words("canary|canaries", CAUTION, "define on first use; not a verb")
words("knob|knobs|dials|lever|levers", CAUTION, "setting, option, parameter (if figurative)")
words("out of the box|out-of-the-box", CAUTION, "by default, without configuration (literal use only)")
words("off the shelf|off-the-shelf", AVOID, "ready-made, prebuilt, standard")
words("plug and play|plug-and-play|turnkey", AVOID, "requires no configuration")
words("black box|black-box|blackbox|white box|white-box|gray box|gray-box", CAUTION, "opaque-box testing, clear-box testing, synthetic monitoring")
words("single pane of glass", AVOID, "single interface")
words("slice and dice", AVOID, "segment the data for analysis")
words("shift left|shift-left", CAUTION, "shift earlier; move to an earlier phase")
words("postmortem|post-mortem", CAUTION, "retrospective (blameless postmortem is fine in incident response)")
words("anti-pattern|anti-patterns|antipattern", CAUTION, "name the practice")
words("legacy", CAUTION, "define it, or use a precise term")
words("native", CAUTION, "built-in; say what you mean")
words("traditional|traditionally", CAUTION, "conventionally; a precise term")
words("at scale", CAUTION, "give a direction and magnitude")
words("think of it as|imagine|picture this|it's like a|analogous to", AVOID, "describe the thing itself (no analogies)")

# --- Anthropomorphism and vague verbs --------------------------------------
words("knows about|cares about|is aware of", CAUTION, "reads, checks, has access to")
raw(r"\bhandl(?:e|es|ed|ing)\b", CAUTION, "the specific verb: parses, validates, retries, routes")
words("deals with|takes care of", AVOID, "the specific verb")
words("is responsible for|are responsible for", CAUTION, "does; state the action")
words("serves as|acts as|functions as", AVOID, "is")
raw(r"\bleverag(?:e|es|ed|ing)\b", AVOID, "use, build on")
raw(r"\butiliz(?:e|es|ed|ing)\b", AVOID, "use (utilization is fine for a measured quantity)")
words("allows you to|allow you to|enables you to|enable you to|provides the ability to|makes it possible to", AVOID, "lets you; you can")
words("goes ahead and|go ahead and|proceeds to|proceed to", AVOID, "delete")
raw(r"\bensur(?:e|es|ed|ing)\b", CAUTION, "only if literally ensured; else 'checks that', 'so that'")
raw(r"\bguarante(?:e|es|ed|ing)\b", CAUTION, "only if literally guaranteed")

# --- Filler, softeners, hype (rule 2) --------------------------------------
words("simply|easily|trivial|trivially|obviously|basically|essentially|straightforward|needless to say|of course", AVOID, "delete")
words("just", CAUTION, "delete, or use 'only'")
words("easy|quick|quickly", CAUTION, "delete; what is easy for you might not be for the reader")
words("clearly|actually|really|very|extremely|incredibly|truly|definitely|certainly|absolutely|arguably|a bit|pretty much|fairly|somewhat", CAUTION, "delete")
raw(r"\b(?:is|was|are|were|it's|its|be|been|being|seems?|looks?|feels?)\s+(?:kind|sort)\s+of\b", CAUTION, "delete the softener")
words("please note|note that|it's worth noting|it is worth noting|worth noting|keep in mind|importantly|crucially|at this time|at its core|at the end of the day|in a nutshell|the key insight|the key takeaway|here's the thing|that said|that being said|with that said|having said that|moving forward|going forward|in terms of|when it comes to|with respect to|as you can see|the short answer|long story short|simply put|to put it simply", AVOID, "delete; state the fact")
words("in order to", AVOID, "to")
words("a number of", AVOID, "some, many, or the number")
words("please", AVOID, "delete (only when asking permission or forgiveness)")
words("let's|lets us", AVOID, "imperative, or 'you'")
words("great question|certainly!|absolutely!|you're absolutely right|you are absolutely right|i'd be happy to|happy to help|hope this helps|feel free to|let me know if", AVOID, "start with the information; delete closings")
words("successfully", CAUTION, "state the result instead")
words("robust|seamless|seamlessly|elegant|elegantly|powerful|blazing|blazing-fast|lightning-fast|lightning fast|battle-tested|bulletproof|rock solid|rock-solid|ironclad|airtight|production-ready|enterprise-grade|best-in-class|world-class|cutting-edge|state-of-the-art|next-generation|game-changer|game changer|revolutionary|holistic|future-proof|performant|actionable", AVOID, "a measurable statement, or delete")
words("comprehensive", CAUTION, "say what is covered")
words("best|fastest|simplest|perfect|perfectly", CAUTION, "an excessive claim; verify or delete")
words("it is recommended|it's recommended", CAUTION, "We recommend")

# --- Modal verbs and tense (rule 4) ----------------------------------------
words("should", CAUTION, "must, can, might, or 'We recommend'")
words("will", CAUTION, "present tense, unless the action happens later")
words("would", CAUTION, "can; or present tense")
words("could", CAUTION, "can")
raw(r"\b(?-i:may)\b", CAUTION, "can or might (may is for policy and legal text)")
words("shall", AVOID, "must")

# --- Timeless documentation --------------------------------------------------
words("currently|presently|at present|as of this writing|as of now|eventually|in the future|does not yet|doesn't yet|not yet", AVOID, "delete; state what is true now")
words("latest|soon", CAUTION, "give a version or date, or delete")
words("newer|older", CAUTION, "later, earlier, with a version number")

# --- Word list: don't use ---------------------------------------------------
words("crazy|insane|bonkers|loony|dumb down|retarded|lame|gimp|gimpy|chubby|ghetto|gypsy|sexy|voodoo", AVOID, "a precise, non-figurative term")
raw(r"\bcrippl(?:e|es|ed|ing)\b", AVOID, "slowed; describe the effect")
words("dummy|dummy variable|dummy data", AVOID, "placeholder, sample")
words("blind to|blind spot|blind eye|blindly", AVOID, "ignore, unaware of, without checking")
words("whitelist|whitelisted|whitelisting|whitelists|blacklist|blacklisted|blacklisting|blacklists|graylist|greylist", AVOID, "allowlist, denylist, blocklist; or describe the action")
words("slave|slaves", AVOID, "worker, replica, secondary, follower")
words("master", CAUTION, "primary, main, parent, controller, leader (never with slave)")
words("grandfathered|grandfather clause", AVOID, "legacy, exempt, made an exception")
words("tribal knowledge|tribal wisdom", AVOID, "knowledge held by the team")
words("war room|brown bag|brown-bag|dojo|mom test|monkey test|build cop|build sheriff", AVOID, "a precise term for the activity")
words("ninja|guru|sherpa|rockstar|rock star|wizard", CAUTION, "expert, guide (unless a product name)")
words("man-hours|man hours|manhours|manpower|manned|manmade|man-made|man-in-the-middle", AVOID, "person-hours, staff, staffed, artificial, on-path attacker")
words("you guys", AVOID, "everyone, folks")
words("female adapter|male adapter", AVOID, "socket, plug")
words("blackhat|black hat|whitehat|white hat|grayhat|gray hat", AVOID, "illegal, unethical, legal, ethical")
words("stonith", AVOID, "fence failed nodes")
words("hang|hangs|hung|hanging", CAUTION, "stops responding, not responding (if about software)")
raw(r"\bkill(?:s|ed|ing)?\b", CAUTION, "stop, exit, cancel, end (signals excepted)")
raw(r"\babort(?:s|ed|ing)?\b", CAUTION, "stop, exit, cancel, end (signals excepted)")
raw(r"\bterminat(?:e|es|ed|ing)\b", CAUTION, "stop, exit, cancel, end (signals and networking excepted)")
words("final solution|denigrate|housekeeping|hands-off|hands-on|break-glass|break glass|hotspotting|learnings|agnostic", AVOID, "a precise term")
raw(r"\bcompris(?:e|es|ed|ing)\b", AVOID, "consist of, contain, include")
raw(r"\bdesir(?:e|es|ed)\b", AVOID, "want, need")
raw(r"\bwish(?:es|ed)?\b", AVOID, "want, need")
raw(r"\bimpact(?:s|ed|ing)\b", AVOID, "affect (impact is a noun only)")
words("k8s", AVOID, "Kubernetes")
words("repo|repos", CAUTION, "repository")
words("regex|regexes|regexp", CAUTION, "regular expression")
words("config|configs", CAUTION, "configuration (code font if it's a literal name)")
words("admin|admins", CAUTION, "administrator (unless matching a UI label)")
words("functionality", CAUTION, "features, capabilities")
words("e-mail", AVOID, "email")
raw(r"\bssh(?:'?ing|ed)?\s+(?:in|into)\b|\bssh'ing\b", AVOID, "connect by using SSH")
raw(r"\bhover(?:s|ed|ing)?\b", AVOID, "hold the pointer over; point to")
words("grayed out|greyed out|grayed-out|greyed-out", AVOID, "unavailable")
words("hamburger menu|hamburger icon|kebab menu|kebab icon|zippy|expando|disclosure triangle", AVOID, "the icon's label; expander arrow")
words("pop-up|popup|pop up window", AVOID, "dialog, menu")
words("drop-down|dropdown|drop down", CAUTION, "list, menu")
words("uncheck|unselect|deselect", CAUTION, "clear (for checkboxes)")
words("click on", AVOID, "click")
words("click here", AVOID, "descriptive link text")
words("copy and paste|copy-paste|copy/paste", AVOID, "say what to enter where")
words("for instance", AVOID, "for example")
words("and so on|and so forth", AVOID, "introduce the list with 'such as' instead")
raw(r"\betc\.?(?=[\s,.;:)]|$)", AVOID, "introduce the list with 'such as' instead")
raw(r"\be\.g\.", AVOID, "for example")
raw(r"\bi\.e\.", AVOID, "that is")
raw(r"\bvs\.?(?=\s)", AVOID, "versus")
raw(r"\bw/(?=\s|\w)", AVOID, "with")
words("and/or", AVOID, "X, Y, or both")
words("via", AVOID, "by using, through, with")
words("vice versa|vice-versa", AVOID, "write out both directions, or 'conversely'")
words("aka", AVOID, "also known as")
raw(r"\ba\.k\.a\.?", AVOID, "also known as")
words("tl;dr|tldr|ymmv|fwiw|iirc|imho|imo|afaik|rtfm|lgtm|ptal", AVOID, "write it out, or delete")
raw(r"\bper\b(?!\s+(?:second|minute|hour|day|week|month|year|millisecond|ms|sec)\b)", CAUTION, "only for rates; else 'according to', 'for each'")
raw(r"\bsince\b", CAUTION, "because (if causal)")
raw(r"\bonce\b", CAUTION, "after (if sequential)")
raw(r"\bwhile\b", CAUTION, "although (if contrastive)")
words("above|below", CAUTION, "preceding, following, earlier, later (no directional language)")
raw(r"\bor\s+(?:higher|lower|above|below)\b", AVOID, "or later; or earlier")
words("left-hand|right-hand|left side|right side|upper left|upper right|lower left|lower right|top left|top right|bottom left|bottom right", CAUTION, "no directional language; add context or a screenshot")
words("n/a", CAUTION, "spell out on first use: not applicable")

# --- Punctuation and typography ---------------------------------------------
raw(r"!(?![=\[])", AVOID, "no exclamation points")
raw(r"[“”‘’]", AVOID, "straight quotation marks")
raw(r"–", AVOID, "en dash: use a hyphen or 'to'")
raw(r"…", AVOID, "ellipsis character: don't use ellipses in prose")
raw(r"\s—|—\s", AVOID, "no spaces around an em dash")
raw(r"(?<=\S)\s+-\s+(?=\S)", CAUTION, "spaced hyphen used as a dash: em dash with no spaces, or a colon")
raw(r"(?<![-\w])--(?![-\w>])", CAUTION, "double hyphen used as a dash: use an em dash")
raw(r"(?<!^)\.\.\.(?!\.)", CAUTION, "no ellipses in prose (fine in command output)")
raw(r"\w\(s\)", AVOID, "no optional plurals; use the plural or 'one or more'")
raw(r"\b\d+x\b", AVOID, "'10 times', not '10x' (dimensions like 192x192 excepted)")
raw(r"\b\d+(?:st|nd|rd|th)\b", AVOID, "spell out ordinals: first, second")
raw(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", AVOID, "write the date as January 19, 2017 or 2017-01-19")
raw(r"\b\d{1,2}(?::\d{2})?\s?(?-i:am|pm|Am|Pm)\b", CAUTION, "AM or PM, uppercase, with a space: 3 PM")
raw(r"\b\d{1,2}(?::\d{2})?(?-i:AM|PM)\b", CAUTION, "a space before AM or PM: 3 PM")
raw(r"\b\d+(?:GB|MB|KB|TB|GiB|MiB|KiB|Gbps|Mbps|Kbps|ms|GHz|MHz)\b", CAUTION, "a space between the number and the unit: 64 GB")
raw(r"[.!?]  +(?=\S)", CAUTION, "one space between sentences")
raw(r"[\U0001F300-\U0001FAFF☀-➿⬀-⯿✅❌]", CAUTION, "no emoji or symbols; use words")
raw(r"\s&\s", CAUTION, "'and', not '&' (UI labels excepted)")

COMPILED = [(re.compile(p, re.IGNORECASE), s, m) for p, s, m in RULES]

PROSE_SUFFIXES = {".md", ".markdown", ".mdx", ".txt", ".rst", ".adoc", ".text"}
HASH_COMMENT = {".py", ".rb", ".sh", ".bash", ".zsh", ".yaml", ".yml", ".toml", ".pl", ".r",
                ".cfg", ".ini", ".conf", ".mk", ".nix", ".ex", ".exs", ".ps1", ".tf"}
SLASH_COMMENT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".kt", ".kts",
                 ".swift", ".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".cs", ".m", ".mm", ".scala",
                 ".dart", ".php", ".proto", ".groovy", ".scss", ".less", ".zig", ".v"}
DASH_COMMENT = {".sql", ".lua", ".hs", ".elm"}
BLOCK_COMMENT = SLASH_COMMENT | {".css"}

PLACEHOLDER = "\u2400"  # marks removed spans without adding spaces
SPAN_BODY = r"(?:[^%s\n]|\n(?!\n))+?"  # a span can wrap lines but not cross a blank line
BOLD = re.compile(r"\*\*" + (SPAN_BODY % "*") + r"\*\*")
INLINE_CODE = re.compile(r"``(?:[^`\n]|\n(?!\n))+?``|`(?:[^`\n]|\n(?!\n))+?`")
ITALIC_STAR = re.compile(r"(?<![*\w\\])\*(?!\*)" + (SPAN_BODY % "*") + r"\*(?![*\w])")
ITALIC_UNDERSCORE = re.compile(r"(?<![\w_\\])_(?!_)" + (SPAN_BODY % "_") + r"_(?![\w_])")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
URL = re.compile(r"https?://\S+|www\.\S+")
LINK_TARGET = re.compile(r"\]\([^)\n]*\)")
HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
LINT_OFF = re.compile(r"<!--\s*style-lint:\s*off\s*-->")
LINT_ON = re.compile(r"<!--\s*style-lint:\s*on\s*-->")
BLOCKQUOTE = re.compile(r"^\s*(?:>\s?)+")
LIST_MARKER = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
TABLE_SEPARATOR = re.compile(r"\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?")
HORIZONTAL_RULE = re.compile(r"-{3,}|\*{3,}|_{3,}")


def _blank_span(match: re.Match) -> str:
    """Replace a span with a placeholder, keeping its newlines so line numbers hold."""
    return PLACEHOLDER + "".join(c for c in match.group(0) if c == "\n")


def clean_spans(text: str) -> str:
    """Remove text that the linter doesn't check: code, bold, italics, links, comments."""
    text = HTML_COMMENT.sub(_blank_span, text)
    text = INLINE_CODE.sub(_blank_span, text)
    text = BOLD.sub(_blank_span, text)
    text = ITALIC_STAR.sub(_blank_span, text)
    text = ITALIC_UNDERSCORE.sub(_blank_span, text)
    text = text.replace("![", "[")
    text = LINK_TARGET.sub("]", text)
    text = URL.sub(PLACEHOLDER, text)
    return text


def prose_lines(text: str):
    """Yield (line_number, checkable_text, is_heading) for a Markdown document.

    Fenced code blocks, lint-off regions, table separators, and horizontal
    rules are skipped. Blockquote and list markers are removed. The first
    cell of a table row is treated as the term under discussion and skipped.
    Inline code, bold, and italic spans are removed, so a document can name
    a term without being flagged for using it.
    """
    lines = text.splitlines()
    headings = [False] * len(lines)
    in_fence = False
    fence_marker = ""
    off = False
    for index, line in enumerate(lines):
        if off:
            if LINT_ON.search(line):
                off = False
            lines[index] = ""
            continue
        if LINT_OFF.search(line):
            off = True
            lines[index] = ""
            continue
        fence = FENCE.match(line)
        if fence:
            marker = fence.group(1)[0]
            if not in_fence:
                in_fence, fence_marker = True, marker
            elif marker == fence_marker:
                in_fence = False
            lines[index] = ""
            continue
        if in_fence:
            lines[index] = ""
            continue
        stripped = line.strip()
        if TABLE_SEPARATOR.fullmatch(stripped) or HORIZONTAL_RULE.fullmatch(stripped):
            lines[index] = ""
            continue
        cleaned = BLOCKQUOTE.sub("", line)
        heading = HEADING.match(cleaned)
        if heading:
            headings[index] = True
            cleaned = heading.group(2)
        else:
            cleaned = LIST_MARKER.sub("", cleaned)
        if cleaned.lstrip().startswith("|"):
            cells = cleaned.split("|")
            if len(cells) > 2:
                cells[1] = " "
            cleaned = "|".join(cells)
        lines[index] = cleaned
    cleaned_text = clean_spans("\n".join(lines))
    for index, content in enumerate(cleaned_text.split("\n")):
        if content.strip():
            yield index + 1, content, headings[index]


def source_lines(text: str, suffix: str, check_all: bool):
    """Yield (line_number, comment_text, False) for a source file."""
    if check_all:
        for number, line in enumerate(text.splitlines(), start=1):
            yield number, line, False
        return
    in_docstring = False
    doc_quote = ""
    in_block = False
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if suffix == ".py":
            if in_docstring:
                yield number, line, False
                if doc_quote in line:
                    in_docstring = False
                continue
            match = re.match(r'^\s*[rRbBuU]{0,2}("""|\'\'\')', line)
            if match:
                doc_quote = match.group(1)
                body = line[match.end():]
                yield number, body, False
                if doc_quote not in body:
                    in_docstring = True
                continue
        if suffix in BLOCK_COMMENT:
            if in_block:
                yield number, line, False
                if "*/" in line:
                    in_block = False
                continue
            if "/*" in line:
                start = line.index("/*")
                segment = line[start + 2:]
                yield number, segment, False
                if "*/" not in segment:
                    in_block = True
                continue
        if suffix in HASH_COMMENT or suffix in {"", ".dockerfile", ".makefile"}:
            if stripped.startswith("#!"):
                continue
            match = re.search(r"(?:^|\s)#(?!\{)(.*)$", line)
            if match:
                yield number, match.group(1), False
            continue
        if suffix in SLASH_COMMENT:
            match = re.search(r"(?<!:)//(.*)$", line)
            if match:
                yield number, match.group(1), False
            continue
        if suffix in DASH_COMMENT:
            match = re.search(r"(?:^|\s)--(.*)$", line)
            if match:
                yield number, match.group(1), False
            continue


def looks_title_case(heading: str) -> bool:
    body = heading.split(":", 1)[-1] if ":" in heading else heading
    tokens = [t for t in re.findall(r"[A-Za-z][A-Za-z'-]*", body)][1:]
    candidates = [t for t in tokens if len(t) > 3 and not t.isupper()]
    if len(candidates) < 2:
        return False
    capitalized = [t for t in candidates if t[0].isupper()]
    return len(capitalized) >= 2 and len(capitalized) * 2 >= len(candidates)


SOURCE_SUFFIXES = HASH_COMMENT | SLASH_COMMENT | DASH_COMMENT | BLOCK_COMMENT | {"", ".dockerfile", ".makefile"}


def check(path: str, text: str, mode: str, check_all: bool) -> list[tuple[int, str, str, str]]:
    findings = []
    suffix = Path(path).suffix.lower() if path != "-" else ".md"
    if mode == "prose" or path == "-" or suffix not in SOURCE_SUFFIXES:
        lines = prose_lines(text)
    else:
        lines = ((n, clean_spans(c), h) for n, c, h in source_lines(text, suffix, check_all))
    for number, content, is_heading in lines:
        if is_heading:
            title = content.replace(PLACEHOLDER, "").strip()
            if looks_title_case(title):
                findings.append((number, CAUTION, title, "heading looks like title case; use sentence case"))
            if re.search(r"[.:!?]\s*$", title):
                findings.append((number, CAUTION, title, "no end punctuation in headings"))
        for pattern, severity, suggestion in COMPILED:
            for match in pattern.finditer(content):
                findings.append((number, severity, match.group(0).strip(), suggestion))
    findings.sort(key=lambda f: (f[0], f[1] != AVOID, f[2].lower()))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*", help="files to check; reads stdin if none")
    parser.add_argument("--strict", action="store_true", help="exit 1 on caution findings too")
    parser.add_argument("--all", action="store_true", help="check every line of source files")
    parser.add_argument("--prose", action="store_true", help="treat every file as prose")
    parser.add_argument("--quiet", action="store_true", help="print only the summary")
    args = parser.parse_args()

    targets = args.files or ["-"]
    total_avoid = total_caution = 0
    for target in targets:
        if target == "-":
            text = sys.stdin.read()
            label = "<stdin>"
        else:
            try:
                text = Path(target).read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                print(f"{target}: {exc}", file=sys.stderr)
                return 2
            label = target
        mode = "prose" if args.prose else "auto"
        for number, severity, matched, suggestion in check(target, text, mode, args.all):
            if severity == AVOID:
                total_avoid += 1
            else:
                total_caution += 1
            if not args.quiet:
                print(f'{label}:{number}: [{severity}] "{matched}" -> {suggestion}')

    print(f"\n{total_avoid} avoid, {total_caution} caution")
    if total_avoid or (args.strict and total_caution):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
