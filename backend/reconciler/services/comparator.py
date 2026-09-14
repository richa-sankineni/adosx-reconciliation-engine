"""
Core reconciliation logic.

Deliberately framework-free: reconcile_records() takes plain dicts and a
plain dict lookup, and returns plain dataclasses. This is the "part where
the disagreements are decided" that the brief asks to be tested directly —
keeping it free of the ORM means tests run in milliseconds with no database.

Four passes, matching the brief exactly:
  1. Duplicate check       -> DUPLICATE_IN_SYSTEM_B
  2. Missing in System B   -> MISSING_IN_SYSTEM_B
  3. Orphan in System B    -> ORPHAN_IN_SYSTEM_B
  4. Value discrepancies   -> VALUE_MISMATCH

Passes 1, 2 and 4 are evaluated together per System A record (an A record
either has zero, one, or many matching B entries; each case maps to exactly
one outcome). Pass 3 is a separate sweep over B because an orphan by
definition has no corresponding A record to iterate from.

Precedence: a record with more than one B match is reported as a duplicate,
not as a value mismatch, even if one of the duplicate values also happens to
disagree. Reporting both would be noise for the same underlying reason (the
importer can't tell which of two System B rows is "the" comparison value).
"""
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .parsing import normalize_reference, safe_parse_decimal


REASON_MISSING = "MISSING_IN_SYSTEM_B"
REASON_ORPHAN = "ORPHAN_IN_SYSTEM_B"
REASON_DUPLICATE = "DUPLICATE_IN_SYSTEM_B"
REASON_VALUE_MISMATCH = "VALUE_MISMATCH"

ALL_REASONS = (REASON_MISSING, REASON_ORPHAN, REASON_DUPLICATE, REASON_VALUE_MISMATCH)


@dataclass
class Discrepancy:
    reason: str
    record_ref: str  # canonical/display identifier for the disagreement
    location_id: str = ""
    org_id: str = "UNKNOWN"
    val_a: Optional[str] = None
    val_b: Optional[str] = None
    system_a_record_id: Optional[str] = None
    system_b_entry_ids: List[str] = field(default_factory=list)
    detail: str = ""

    def sort_value(self) -> float:
        """Best-effort numeric value for the frontend's "sort by value" control."""
        for candidate in (self.val_a, self.val_b):
            parsed = safe_parse_decimal(candidate)
            if parsed is not None:
                return float(parsed)
        return 0.0

    def as_dict(self) -> dict:
        return {
            "reason": self.reason,
            "record_ref": self.record_ref,
            "location_id": self.location_id,
            "org_id": self.org_id,
            "val_a": self.val_a,
            "val_b": self.val_b,
            "system_a_record_id": self.system_a_record_id,
            "system_b_entry_ids": self.system_b_entry_ids,
            "detail": self.detail,
            "sort_value": self.sort_value(),
        }


def reconcile_records(
    records_a: List[dict],
    records_b: List[dict],
    location_org_map: Dict[str, str],
) -> List[Discrepancy]:
    """
    records_a: dicts with keys record_id, location_id, value
    records_b: dicts with keys entry_id, record_ref, location_id, value
    location_org_map: location_id -> org_id
    """
    discrepancies: List[Discrepancy] = []

    a_normalized_ids = {normalize_reference(a["record_id"]) for a in records_a}

    b_by_ref = defaultdict(list)
    for b in records_b:
        norm_ref = normalize_reference(b.get("record_ref"))
        b_by_ref[norm_ref].append(b)

    # Passes 1, 2, 4: iterate System A, classify by how many B entries match.
    for a in records_a:
        norm_id = normalize_reference(a["record_id"])
        org_id = location_org_map.get(a.get("location_id"), "UNKNOWN")
        matches = b_by_ref.get(norm_id, [])

        if not matches:
            discrepancies.append(
                Discrepancy(
                    reason=REASON_MISSING,
                    record_ref=a["record_id"],
                    location_id=a.get("location_id") or "",
                    org_id=org_id,
                    val_a=a.get("value"),
                    val_b=None,
                    system_a_record_id=a["record_id"],
                    detail="No System B entry references this record.",
                )
            )
        elif len(matches) > 1:
            discrepancies.append(
                Discrepancy(
                    reason=REASON_DUPLICATE,
                    record_ref=a["record_id"],
                    location_id=a.get("location_id") or "",
                    org_id=org_id,
                    val_a=a.get("value"),
                    val_b="; ".join(str(m.get("value")) for m in matches),
                    system_a_record_id=a["record_id"],
                    system_b_entry_ids=[m.get("entry_id", "") for m in matches],
                    detail=f"{len(matches)} System B entries reference this record.",
                )
            )
        else:
            b = matches[0]
            val_a = safe_parse_decimal(a.get("value"))
            val_b = safe_parse_decimal(b.get("value"))
            if val_a != val_b:
                discrepancies.append(
                    Discrepancy(
                        reason=REASON_VALUE_MISMATCH,
                        record_ref=a["record_id"],
                        location_id=a.get("location_id") or "",
                        org_id=org_id,
                        val_a=a.get("value"),
                        val_b=b.get("value"),
                        system_a_record_id=a["record_id"],
                        system_b_entry_ids=[b.get("entry_id", "")],
                        detail="Parsed numeric values do not match.",
                    )
                )

    # Pass 3: sweep System B for refs that never resolve to a System A record.
    for norm_ref, matches in b_by_ref.items():
        if norm_ref == "" or norm_ref not in a_normalized_ids:
            for b in matches:
                org_id = location_org_map.get(b.get("location_id"), "UNKNOWN")
                discrepancies.append(
                    Discrepancy(
                        reason=REASON_ORPHAN,
                        record_ref=b.get("record_ref") or b.get("entry_id", ""),
                        location_id=b.get("location_id") or "",
                        org_id=org_id,
                        val_a=None,
                        val_b=b.get("value"),
                        system_a_record_id=None,
                        system_b_entry_ids=[b.get("entry_id", "")],
                        detail="No System A record matches this reference.",
                    )
                )

    return discrepancies
