# IBM Bob usage log

Chronological record of every prompt given to IBM Bob during the 40-minute build.

## 1. Plan mode — initial design
**Prompt:**
> I'm building "Bantuan Checker" – a web app that helps Malaysians find which government assistance schemes they likely qualify for (STR, SARA, eBelia Rahmah, JKM Warga Emas, MADANI Medical, MyKasih, Zakat) from a short form: age, state, household income, household size, marital status, student/working status. Stack: Python FastAPI backend with a JSON rules engine (rules.json), a single-page HTML/JS frontend in /static, and pytest tests. Must run with `uvicorn app:app`. Plan the file structure, the rules data model, and the /api/check endpoint. Keep it minimal – I have 40 minutes.

**Bob's response:** Used its built-in `create-plan` skill and asked two clarifying questions before writing anything:
1. Matching strictness (hard / soft / two tiers) → **I chose two tiers**: "Likely Eligible" (all criteria met) and "Check Eligibility" (one criterion short, with the failing condition shown).
2. Zakat depends on religion but the form didn't collect it → **I chose an optional Religion field** (blank = Zakat goes to "Check" rather than guessing).

Output: [`bantuan-checker-plan.md`](bantuan-checker-plan.md) — overview, file structure, 5 sub-tasks with intent / expected outcomes / todo lists, and implementation order.

**My review of the plan:** it assumed an empty folder and proposed `household_size >= 2` for STR (which would wrongly exclude singles). I corrected both in the next prompt.

## 2. Plan → Agent mode — implement on top of the existing scaffold
**Prompt:**
> Plan looks good. Switch to Agent mode and implement it, but build on the existing files in this folder instead of starting fresh (app.py, rules.json, static/index.html, tests/test_rules.py already exist and 7 tests pass). Keep the existing rules.json … Do NOT use household_size >= 2 for STR (singles qualify). Move evaluation logic out of app.py into a new engine.py exposing check_eligibility(user, rules) -> {"likely": [...], "check": [...]} … with a human-readable "reason" for the failed condition … Update app.py and static/index.html … Add tests/test_engine.py … Run pytest -q and make sure all tests pass.

**What Bob did:**
- Requested the mode switch Plan → Agent itself, then created a 7-item todo list and ticked it off.
- Created `engine.py` (operators, reason generator, `check_eligibility`), rewired `app.py`, rebuilt the results UI into two tiers, wrote `tests/test_engine.py`, updated `tests/test_rules.py`.
- Ran `pytest`: **1 failure**. Bob diagnosed it itself — a 17-year-old fails eBelia branch 1 by exactly one condition, so "check" was correct and the *test expectation* was wrong. It fixed the test, re-ran (17 passed), then removed a now-duplicate test → **16/16 passing**.


## 3. Agent mode + `impeccable` design skill — UI redesign
**Prompt (summary):** Redesign `static/index.html` so it is polished and demo-ready; plain HTML/CSS/JS only; do not touch the API, engine or tests; hero header, grouped form, two-tier result cards with benefit pills, reasons, collapsible document checklists and apply links; responsive, dark mode, accessible, reduced-motion aware.

**What Bob did:** Loaded its built-in `impeccable` design skill, ran the skill's context script on the page, chose a direction ("government notice remade as a living document": Malaysian red header, blue ink, amber accent, monospaced labels), rewrote the page, then ran the skill's `detect.mjs` checker, which flagged side-tab card borders. Bob replaced them with top borders and re-ran the checker (zero findings) and `pytest` (16/16).

**Polish round (prompt):** Always show the Check reason; move the long benefit pill onto its own line; replace the floating "2026" badge with an "Indicative only" badge.

**Human-in-the-loop catch:** Bob reported the reason as "always visible", but when I rendered the page in a browser it was still hidden. It sat inside `<details>` but outside `<summary>`, so it only showed once a card was expanded. I told Bob exactly why and it moved the reason into the summary with an "Almost:" prefix. I verified it in the browser afterwards. **Lesson:** always check AI-built UI in a real browser, not just the diff.

## Takeaways
- Plan → Agent → Ask matched the workflow taught in the workshop.
- Bob's clarifying question in Plan mode surfaced a product decision I hadn't considered.
- Scoping each Agent prompt to one feature and "keep tests passing" made its changes safe to accept.
