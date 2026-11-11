"""Shared helpers of the Kodeks scripts: the quotation rules kodeks.me checks
reports by, and JSON files.

quote_text is a port of quoteText in kodeks.me's backend
(internal/analysis/validate.go). Both are tested against the same vectors, so a
quotation found here is found there: whitespace, letter case, typographic
quotes and dashes, soft hyphens and zero-width characters do not matter; every
word does.
"""

import json
import os
import unicodedata

# Go's unicode.IsSpace: the Latin-1 spaces and the Unicode White_Space set.
_SPACES = set(
    "\t\n\v\f\r \u0085         "
    "        　"
)
_DROPPED = set("­​‌‍⁠﻿")
_DOUBLE = set("„“”‟«»″")
_SINGLE = set("‚‘’‛′`")
_DASHES = set("‐‑‒–—―−")


def _lower(ch):
    # Go lowers one code point to one code point (simple case mapping);
    # Python's str.lower uses the full mapping, which differs only for İ.
    if ch == "İ":
        return "i"
    lowered = ch.lower()
    return lowered if len(lowered) == 1 else ch


def quote_text(value):
    out = []
    for ch in unicodedata.normalize("NFC", value):
        if ch in _SPACES or ch in _DROPPED:
            continue
        if ch in _DOUBLE:
            out.append('"')
        elif ch in _SINGLE:
            out.append("'")
        elif ch in _DASHES:
            out.append("-")
        elif ch == "…":
            out.append("...")
        else:
            out.append(_lower(ch))
    return "".join(out)


def quote_found(source_text, quote):
    """Whether quote is in source_text by kodeks.me's rules; an empty
    quotation is never found."""
    needle = quote_text(quote)
    return needle != "" and needle in quote_text(source_text)


def matched_prefix(source_text, quote):
    """The longest run of the quotation's opening words found in the source,
    to show where a quotation departs from the text."""
    words = quote.split()
    text = quote_text(source_text)
    low, high = 0, len(words)
    while low < high:
        mid = (low + high + 1) // 2
        if quote_text(" ".join(words[:mid])) in text:
            low = mid
        else:
            high = mid - 1
    prefix = " ".join(words[:low])
    return prefix if len(prefix) <= 300 else "…" + prefix[-300:]


def read_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, value):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
