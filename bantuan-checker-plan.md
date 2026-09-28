# Bantuan Checker — Plan

## Top-Level Overview

Build a minimal Python FastAPI web app ("Bantuan Checker") that lets Malaysians discover which of 7 government assistance schemes they likely qualify for.

- **Backend**: FastAPI (`app.py`), single `/api/check` POST endpoint, rules loaded from `rules.json`
- **Frontend**: Single-page HTML/JS (`static/index.html`), submits a form, renders two result tiers
- **Tests**: `pytest` covering the rules engine logic
- **Run command**: `uvicorn app:app`

Two result tiers are returned:
- **Likely Eligible** — all criteria met
- **Check Eligibility** — exactly 1 criterion not met (partial match)

---

## File Structure

```
bantuan-checker/
├── app.py              # FastAPI app + /api/check endpoint
├── rules.json          # Scheme eligibility rules
├── engine.py           # Rules evaluation logic (imported by app.py)
├── static/
│   └── index.html      # Single-page frontend
├── tests/
│   └── test_engine.py  # pytest tests for engine.py
└── requirements.txt    # fastapi, uvicorn
```

---

## Sub-Tasks

---

### Sub-Task 1 — Define `rules.json` data model and populate all 7 schemes

**Intent**
Encode the eligibility criteria for all 7 schemes as structured JSON so the rules engine can evaluate them programmatically without any hardcoded scheme logic.

**Expected Outcomes**
- `rules.json` exists with 7 scheme entries
- Each entry has a consistent, machine-readable structure
- All known public eligibility criteria are captured accurately

**Rules JSON Schema (per scheme)**

```json
{
  "id": "str",
  "name": "str",
  "criteria": [
    {
      "field": "age | state | household_income | household_size | marital_status | employment_status",
      "op": "lte | gte | eq | in | between",
      "value": "<scalar or array or [min, max]>"
    }
  ]
}
```

**Schemes and Criteria to Encode**

| Scheme | Key Criteria |
|---|---|
| STR (Sumbangan Tunai Rahmah) | household_income <= 5000, household_size >= 2 |
| SARA | household_income <= 2500, employment_status in [working, unemployed] |
| eBelia Rahmah | age between 18–30, employment_status = student or working |
| JKM Warga Emas | age >= 60, household_income <= 3000 |
| MADANI Medical | household_income <= 4000 |
| MyKasih | household_income <= 2000, household_size >= 3 |
| Zakat | household_income <= 2500, religion = Muslim |

**Todo List**
- [ ] Create `rules.json` with the schema above
- [ ] Add all 7 scheme entries with their criteria arrays
- [ ] Verify each criterion uses only fields from the accepted form field set

**Relevant Context**
- Form fields: `age` (int), `state` (str), `household_income` (int), `household_size` (int), `marital_status` (str: single/married/widowed/divorced), `employment_status` (str: student/working/unemployed/retired), `religion` (str, optional: Muslim/Non-Muslim — defaults to `null` if omitted)

**Status**: `[ ] pending`

---

### Sub-Task 2 — Implement `engine.py` (rules evaluator)

**Intent**
Implement the evaluation logic that, given a user's form data and the loaded rules, returns which schemes fall into each of the two result tiers.

**Expected Outcomes**
- `engine.py` exports a single function: `check_eligibility(user: dict, rules: list) -> dict`
- Returns `{"likely": [...scheme names...], "check": [...scheme names...]}`
- "likely" = all criteria met
- "check" = exactly 1 criterion not met
- Supports operators: `lte`, `gte`, `eq`, `in`, `between`

**Evaluation Logic (pseudo)**
```
for each scheme:
    failed = [c for c in scheme.criteria if not evaluate(c, user)]
    if len(failed) == 0: → likely
    if len(failed) == 1: → check
    else: → omit
```

**Todo List**
- [ ] Create `engine.py`
- [ ] Implement `evaluate_criterion(criterion, user)` for all 5 operators
- [ ] Implement `check_eligibility(user, rules)` returning `{likely, check}` with scheme id + name
- [ ] Handle missing/null user fields gracefully (treat as failing that criterion)

**Relevant Context**
- Reads rules passed in as a list (caller loads from `rules.json`)
- No external dependencies beyond Python stdlib

**Status**: `[ ] pending`

---

### Sub-Task 3 — Implement `app.py` (FastAPI app + endpoint)

**Intent**
Wire up the FastAPI application: serve static files, expose `/api/check`, validate input with a Pydantic model, and call the engine.

**Expected Outcomes**
- `uvicorn app:app` starts successfully
- `POST /api/check` accepts JSON body, returns `{likely: [...], check: [...]}`
- Static files served from `/static`
- `rules.json` loaded once at startup

**Input Schema (Pydantic)**
```python
class CheckRequest(BaseModel):
    age: int
    state: str
    household_income: int
    household_size: int
    marital_status: str         # single | married | widowed | divorced
    employment_status: str      # student | working | unemployed | retired
    religion: str | None = None # Muslim | Non-Muslim | None
```

**Todo List**
- [ ] Create `app.py` with FastAPI instance
- [ ] Mount `StaticFiles` at `/static`
- [ ] Load `rules.json` at module level into a `RULES` constant
- [ ] Define `CheckRequest` Pydantic model
- [ ] Implement `POST /api/check` handler — call `check_eligibility`, return result
- [ ] Add `requirements.txt` with `fastapi`, `uvicorn[standard]`

**Relevant Context**
- `engine.check_eligibility(user_dict, RULES)` — user dict is `request.model_dump()`
- FastAPI's `StaticFiles` requires `python-multipart` only if forms are used — not needed here

**Status**: `[ ] pending`

---

### Sub-Task 4 — Build `static/index.html` (single-page frontend)

**Intent**
Create a clean, minimal single-page form that collects the 7 inputs, POSTs to `/api/check`, and renders results in two labeled sections.

**Expected Outcomes**
- Form has all 7 inputs with sensible HTML types and options
- On submit, sends JSON to `/api/check` via `fetch`
- Renders "✅ Likely Eligible" and "🔍 Check Eligibility" sections with scheme names
- Shows a clear empty state if neither list has results
- No external dependencies (no CDN, no frameworks) — plain HTML/CSS/JS only

**Todo List**
- [ ] Create `static/index.html`
- [ ] Add form fields: age (number), state (select, all 16 states + WP), household_income (number), household_size (number), marital_status (select), employment_status (select), religion (select: Muslim / Non-Muslim, with a blank "Prefer not to say" default)
- [ ] Add fetch-based submit handler — POST JSON, parse response
- [ ] Render two result sections from response
- [ ] Add minimal inline CSS for readability (no framework required)

**Relevant Context**
- Endpoint: `POST /api/check` with `Content-Type: application/json`
- Response shape: `{ "likely": [{"id":..., "name":...}], "check": [...] }`

**Status**: `[ ] pending`

---

### Sub-Task 5 — Write `tests/test_engine.py` (pytest)

**Intent**
Validate the rules engine with targeted test cases covering both result tiers and edge cases, so correctness can be confirmed before the app runs.

**Expected Outcomes**
- At least 6 tests passing with `pytest`
- Covers: full match → likely, one-off → check, two-off → omitted, edge values (boundary ages/incomes), missing field handling

**Test Cases to Cover**
- User matching all STR criteria → STR in `likely`
- User with income 1 above STR threshold → STR in `check`
- User with income and size both failing STR → STR not in either list
- User aged 30 matching eBelia Rahmah → eBelia in `likely`
- User aged 31 → eBelia in `check` (age fails, rest pass)
- User with `None` for a field → that criterion fails gracefully

**Todo List**
- [ ] Create `tests/__init__.py` (empty)
- [ ] Create `tests/test_engine.py`
- [ ] Import `check_eligibility` from `engine` and load `rules.json` as fixture
- [ ] Write the 6+ test cases above

**Relevant Context**
- `engine.check_eligibility(user_dict, rules_list)`
- Tests load `rules.json` directly — no mocking needed

**Status**: `[ ] pending`

---

## Implementation Order

1. `rules.json` (data foundation everything else depends on)
2. `engine.py` (pure logic, testable in isolation)
3. `tests/test_engine.py` (validate engine before wiring)
4. `app.py` + `requirements.txt` (wire up FastAPI)
5. `static/index.html` (frontend last, depends on API shape being stable)
