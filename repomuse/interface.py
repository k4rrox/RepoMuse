"""The English interface strings, and checks for the translations agents write into strings.json.

The page's strings live in web/js/strings.js (the `STRINGS` object); the chat digest adds a few `digest.*` keys.
One strings.json translates both, so it is checked against the union.
"""
import difflib
import re

from .config import ROOT
from .digest import DEFAULT_STRINGS

PLACEHOLDER = re.compile(r"\{(\w+)\}")
ENTRY = re.compile(r"'([\w.-]+)': '((?:[^'\\]|\\.)*)'")


def page_strings(root=ROOT):
    source = (root / "web" / "js" / "strings.js").read_text(encoding="utf-8")
    start = source.index("const STRINGS = {")
    block = source[start:source.index("\n};\n", start)]  # values may contain "};", e.g. "{time}; not ..."
    return {key: value.replace("\\'", "'") for key, value in ENTRY.findall(block)}


def english_strings(root=ROOT):
    english = dict(DEFAULT_STRINGS)
    english.update(page_strings(root))
    return english


def translation_problems(strings, english):
    """Unknown keys and changed {placeholders}; untranslated keys are fine, they fall back to English."""
    problems = []
    for key, value in sorted(strings.items()):
        if key not in english:
            close = difflib.get_close_matches(key, english, n=1)
            problems.append(f"{key!r} is not an interface key" + (f"; did you mean {close[0]!r}?" if close else ""))
        elif set(PLACEHOLDER.findall(value)) != set(PLACEHOLDER.findall(english[key])):
            expected = ", ".join(sorted("{" + name + "}" for name in PLACEHOLDER.findall(english[key]))) or "none"
            problems.append(f"{key!r} must keep the placeholders of the English text ({expected})")
    return problems
