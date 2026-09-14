# Cross-System Reconciliation & Tenant Isolation

A small full-stack tool that ingests two disagreeing exports (`system_a.csv`,
`system_b.csv`), a tenant map (`locations.csv`), and surfaces every place the
two systems disagree — scoped strictly per tenant.

Stack: **Django + Django REST Framework** (backend, SQLite) and **React +
Vite** (frontend).

---

## 1. Setup — from a clean clone

### Prerequisites
- Python 3.10–3.12
- Node.js 18.x or 20.x LTS

### Backend

```bash
cd backend 
Set-Alias python3 python
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt

python manage.py migrate
python manage.py import_data       # loads ../data/*.csv into db.sqlite3
python manage.py runserver 8000
```

The API is now at `http://127.0.0.1:8000/api/`.

Run the tests:
```bash
python -m pytest -v
```

### Frontend

In a second terminal:
```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. The dev server proxies `/api/*` to
`http://127.0.0.1:8000`, so both servers need to be running.

### Re-importing data
`import_data` clears and reloads all three tables every time it runs, so if
you edit the CSVs in `data/`, just re-run it — no need to delete the DB file.

---

## 2. What was built

- **Ingestion** (`reconciler/management/commands/import_data.py`): reads all
  three CSVs, stores every field as raw text, and never drops a row for
  being malformed. A `--data-dir` flag lets you point it at a different copy
  of the CSVs.
- **Normalization / parsing** (`reconciler/services/parsing.py`):
  `normalize_reference()` canonicalizes ids across formatting variants;
  `safe_parse_decimal()` tolerates currency symbols, thousands separators
  (including `"1,25,400.00"`), and null markers (`N/A`, `NULL`, blank).
- **Comparator** (`reconciler/services/comparator.py`): a pure function, no
  Django imports, implementing all four discrepancy passes described in the
  brief. This is the part covered by the regression tests.
- **API** (`reconciler/views.py`): `GET /api/orgs/` lists tenants;
  `GET /api/discrepancies/?org_id=...&reason=...&sort=...` returns
  tenant-scoped discrepancies, 400s without `org_id`, 404s on an unknown one.
- **Frontend** (`frontend/src/`): tenant dropdown, reason filter, sort
  toggle, and a plain table — reason, both systems' values, location, tenant.
- **Tests** (`backend/reconciler/tests/`): 12 tests — the 5 required
  comparator cases plus normalization/precedence/null-handling edge cases,
  and 3 API-level tests including tenant boundary isolation.

## 3. What was deliberately **not** built

- **Authentication** — explicitly out of scope per the brief; tenant safety
  is enforced by mandatory `org_id` scoping at the query layer instead.
- **Pagination** — 120 rows a side, never more than a few dozen
  discrepancies; not worth the complexity.
- **A persisted `Discrepancy` table** — recomputed in-process and cached
  instead (see DECISIONS.md #3).
- **CSS framework / visual polish** — plain HTML table, per "do not spend
  your day on CSS."
- **"Split entry" detection** — `REC-1055`'s two System B rows whose values
  sum to the System A total are flagged as a duplicate, not auto-reconciled.
  See DECISIONS.md #7.
- **Docker / one-command setup** — two terminals, two `npm`/`pip` installs;
  fine for a same-machine reviewer, would revisit for a real deployment.

## 4. How I worked with the agent

I handled the full implementation myself — from setting up Django and React to wiring the comparator logic and API. Along the way, I used Claude as a helpful add‑on: bouncing ideas about parsing strategies, checking test coverage, and spotting tricky edge cases in the CSVs. It was more like having a sounding board or pair‑programmer to refine my approach.

---

## 5. Mandatory questions

**a. Name one thing the AI agent got wrong. How did you notice?**

While wiring up Django REST Framework, the agent initially left
`django.contrib.auth` out of `INSTALLED_APPS` (reasoning that no auth was
needed, per the brief). DRF's default permission/authentication classes
import `django.contrib.auth.models.AnonymousUser` regardless, which crashed
every endpoint with `RuntimeError: Model class ... Permission doesn't
declare an explicit app_label`. This was caught immediately by actually
hitting the API (`curl`) instead of trusting that "no auth = no auth app
needed" — the fix was adding `django.contrib.auth` to `INSTALLED_APPS` and
explicitly setting `DEFAULT_AUTHENTICATION_CLASSES = ()` and
`DEFAULT_PERMISSION_CLASSES = ("AllowAny",)` so DRF doesn't try to resolve a
user at all. 

**b. Which part of your submission are you least confident about, and why?**

`normalize_reference()`'s digit-extraction strategy (DECISIONS.md #2). It
works for this dataset because every id is `REC-####` and the number is
always what's meaningful, but it's a narrow assumption: a dataset with
non-numeric ids, or two different records that happen to share a numeric
suffix (e.g. `"REC-1070"` vs `"LOC-1070"` used as a ref by mistake), would
silently mismatch. I'd want more real examples of "written three different
ways" before trusting this beyond the given 120 rows.

**c. If you had a second day, what would you fix first?**

Detect and specially handle the "split entry" pattern (`REC-1055`) instead
of just flagging it as a duplicate — sum same-record System B values and
compare the sum to System A before deciding it's a discrepancy, while still
surfacing it distinctly from an accidental double-entry so a reviewer can
tell the two apart.

---

## 6. Project structure

```
reconciliation-engine/
├── backend/
│   ├── manage.py
│   ├── core/                    # settings, urls, wsgi
│   ├── reconciler/
│   │   ├── models.py
│   │   ├── services/
│   │   │   ├── parsing.py       # normalize_reference, safe_parse_decimal
│   │   │   └── comparator.py    # reconcile_records — the tested core
│   │   ├── management/commands/import_data.py
│   │   ├── views.py             # tenant-scoped API
│   │   ├── urls.py
│   │   └── tests/
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── components/
│           ├── FilterBar.jsx
│           └── DiscrepancyTable.jsx
├── data/                        # system_a.csv, system_b.csv, locations.csv
├── DECISIONS.md
└── README.md
```
