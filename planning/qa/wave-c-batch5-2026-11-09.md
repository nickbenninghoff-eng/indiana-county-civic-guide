# Wave C, batch 5: Judges & ballot questions, 2026-11-09

Uncommitted. Checks: build `--check` PASSED, 252 unit tests OK (6 new in `tools/tests/test_wave_c_judges.py`), `check_gov.py` 0 errors.

## What changed (`elections/judges-and-questions/`)
- **Explainer first** (`#how`): how Superior Court judges are chosen and retained (the existing variant slot, moved up) and how questions get on the ballot (rules `no_citizen_initiative` and `school_and_local_referendums`, with a note that petition and threshold rules were not collected, see Gaps).
- **Public questions** (`#questions`): 14 `entity_list` rows in groups by jurisdiction (Statewide first, then by name; newest first within each). Each row: short title, year, outcome, "Yes x% . No y%", status badge. Opens to ballot line, election, verbatim wording or GAP line, the existing result bar, and a link to `elections/results/#contest-<id>`.
  - Outcome is Passed/Failed for local questions; "County voted yes/no" for statewide ones; "(unofficial)" / "Unofficial: ahead" for 2026.
  - Short titles for the 3 questions with captured wording are in `QUESTION_TITLES` (derived from the quoted wording); the rest are the cleaned ballot label.
- **Retention** (`#retention`, `#state-retention`): hbar chart kept; both tables are now `see_all_table` folds (ids `retention-table`, `state-retention-table` kept) with a new "Result" column linking to `#contest-<id>` (or "Not in explorer" for pre-2010).
- **share_bars not used**: the review's section 3.4 says keep the chart and fold the tables; the by-year share_bars line appears only in the pattern table, and summing yes/no across different judges per year would mislead.
- Sections renumbered 01-05. All old ids kept (`q-<id>` is now the row's `<details>`); fixture `anchors_before_wave_c5.json` + test confirm. No moved-anchors needed.

## Measurements (Chrome tab, viewport 597 px wide; the window would not resize to 1280)
- Page: 14.3 screens before (review) to 7.5 now (one row open); Public questions section 7.5 to 2.4 screens (/800).
- All 3 looks x light/dark: no horizontal overflow. Dark theme screenshot checked. JS off: rows and folds ship open (shared helpers).

## Notes
- Rounded shares can sum to 100.1 (2026 Q2: 65.7 / 34.4) because they are the printed percentages.
- Not browser-tested at exactly 400 px or 1280 px, nor keyboard beyond the shared helpers' tested behavior.

## Files
`tools/site/pages/elections.py` (judges code), `tools/site/static/css/elections.css`, `tools/tests/test_wave_c_judges.py`, `tools/tests/fixtures/anchors_before_wave_c5.json`, this report.
