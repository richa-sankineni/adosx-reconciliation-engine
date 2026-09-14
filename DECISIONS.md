# Architectural Decisions

Each entry: what I did, what I rejected, and the one line of reasoning that
separated them.

### 1. No database foreign key between System A and System B tables

- **Decision:** `SystemARecord` and `SystemBEntry` are independent tables. The link between them (`record_ref` → `record_id`) is resolved in Python at query time, not enforced by the schema.
- **Alternative:** A `ForeignKey` from `SystemBEntry.record_ref` to `SystemARecord.record_id`.
- **Reasoning:** The whole exercise is about System B entries that *don't* resolve (orphans) and System A records with *no* System B row — a real FK constraint would make those rows impossible to insert without dropping them, which violates "must survive all of it without silently dropping rows."

### 2. Reference normalization by digit-extraction, not string-cleaning

- **Decision:** `normalize_reference()` pulls out the digit run from an id (`"REC-1070"`, `" REC - 1070 "`, `"1070"` all → `"1070"`) and compares digits, not cleaned strings.
- **Alternative:** Strip non-alphanumerics and lowercase (e.g. `"rec1070"`), matching System A's cleaned id against System B's cleaned ref directly.
- **Reasoning:** The dataset has a ref (`"1112"`) with no `REC-` prefix at all — string-cleaning alone doesn't unify `"REC-1112"` and `"1112"`, but digit-extraction does; this is a narrow, dataset-specific assumption and is called out as a risk below.

### 3. Discrepancies computed on demand and cached, not persisted to a table

- **Decision:** `reconcile_records()` runs against the full (unscoped) dataset on first request and the result list is cached in-process for 5 minutes; there is no `Discrepancy` model or table.
- **Alternative:** Run reconciliation once at import time and store the results as rows, queried directly by the API.
- **Reasoning:** At 120 rows a side the full comparison runs in milliseconds, so a persisted table would only add a migration and a staleness problem (re-import wouldn't update it) for no real benefit at this scale.

### 4. Tenant isolation enforced at the query layer, no auth

- **Decision:** `org_id` is a required query parameter; the view 400s without it and 404s on an unrecognized org. There is no login, session, or token.
- **Alternative:** Django's auth app with per-user org membership and `request.user`.
- **Reasoning:** The brief explicitly waives authentication ("skip it entirely") while making the tenant boundary the one thing that must never fail — mandatory, validated query-layer scoping satisfies the isolation requirement without building auth that wasn't asked for.

### 5. Comparator is a pure, framework-free function

- **Decision:** `reconcile_records()` takes and returns plain dicts/dataclasses, with zero Django imports. The Django view converts ORM querysets to dicts before calling it.
- **Alternative:** Write the comparison as a queryset method or manager, mixing DB access into the matching logic.
- **Reasoning:** The brief asks specifically for tests on "the part where the disagreements are decided" — keeping that part free of the ORM means the test suite needs no test database for 9 of its 12 tests and runs in well under a second.

### 6. Duplicate takes precedence over value mismatch

- **Decision:** If a System A record has more than one matching System B entry, it's reported once as `DUPLICATE_IN_SYSTEM_B`, even if one of the duplicate values also disagrees with System A.
- **Alternative:** Report both a duplicate discrepancy and a separate value-mismatch discrepancy per disagreeing duplicate.
- **Reasoning:** With two System B rows claiming the same record, there's no principled way to say which one is "the" value to compare — reporting a value mismatch on top would be noise for a problem (duplication) that's already flagged.

### 7. Split-entry values are not summed or specially reconciled

- **Decision:** `REC-1055`'s two System B entries (labeled "Entry part 2 of 2", values that sum to the System A total) are reported as a plain `DUPLICATE_IN_SYSTEM_B`, not detected as a "split payment" and reconciled by summing.
- **Alternative:** Detect same-record duplicates whose values sum to the System A total and treat them as a match rather than a discrepancy.
- **Reasoning:** Out of scope for a one-day build — flagging it for human review is correct and honest; silently auto-summing would hide a genuinely ambiguous case and risks masking real duplicate-billing errors in a production dataset.

### 8. Comparison field: System A's `total_value` vs System B's `value`

- **Decision:** The value compared for `VALUE_MISMATCH` is System A's `total_value` column against System B's single `value` column.
- **Alternative:** Compare System A's `base_value` (pre-adjustment) instead, or compare all three of `base_value`/`adjustment`/`total_value` separately.
- **Reasoning:** System B only records one number per entry, and by inspection it lines up with System A's post-adjustment `total_value` for matching rows — comparing anything else would produce false positives on every correctly-matching record.

### 9. Frontend talks to `/api/...` via a Vite dev proxy, no hardcoded host

- **Decision:** `vite.config.js` proxies `/api` to `http://127.0.0.1:8000`; the React app fetches relative paths only.
- **Alternative:** Put `VITE_API_BASE_URL=http://localhost:8000` in an `.env` file and prefix every fetch with it.
- **Reasoning:** For a same-machine take-home reviewer running both servers locally, a proxy needs zero configuration and can't be left pointing at the wrong host by mistake.
