"""
Defensive parsing helpers.

These are used in two places that must never disagree with each other:
  1. the importer, which stores raw strings but may want a quick sanity check
  2. the comparator, which needs canonical keys and canonical numbers

Both call the SAME functions here, so "how do we normalize a reference" is
answered in exactly one place.
"""
import re
from decimal import Decimal, InvalidOperation
from typing import Optional

_DIGITS_RE = re.compile(r"\d+")
_NON_NUMERIC_RE = re.compile(r"[^\d.\-]")

_NULLISH = {"", "N/A", "NA", "NULL", "NONE", "-", "--"}


def normalize_reference(raw: Optional[str]) -> str:
    """
    Reduce a record identifier to a canonical matching key.

    System A uses ids like "REC-1001". System B's record_ref shows up as
    "REC-1001", " REC - 1070 ", "rec1034", or bare "1112". All four must
    resolve to the same key.

    Strategy: pull out the digit run and normalize away leading zeros by
    round-tripping through int(). This is intentionally narrow (it assumes
    the numeric portion of the id is what's authoritative) which is true for
    this dataset's "REC-####" scheme. A future dataset with non-numeric,
    semantically meaningful ids would need a different canonicalization —
    see DECISIONS.md.
    """
    if not raw:
        return ""
    match = _DIGITS_RE.findall(str(raw))
    if not match:
        return ""
    digits = "".join(match)
    try:
        return str(int(digits))
    except ValueError:
        return digits


def safe_parse_decimal(raw: Optional[str]) -> Optional[Decimal]:
    """
    Parse a numeric-ish string while tolerating currency symbols, thousands
    separators (including non-US groupings like "1,25,400.00"), stray
    whitespace, and explicit null markers ("N/A", "NULL", "-", blank).

    Returns None when the value cannot be meaningfully parsed as a number —
    callers must decide what None means for their comparison (it is NOT
    silently treated as zero).
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text.upper() in _NULLISH:
        return None
    cleaned = _NON_NUMERIC_RE.sub("", text)
    if cleaned in ("", "-", "."):
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def clean_text(raw: Optional[str]) -> str:
    """Trim whitespace and collapse a null-marker string down to ''."""
    if raw is None:
        return ""
    text = str(raw).strip()
    if text.upper() in _NULLISH:
        return ""
    return text
