# Wave B fix-ups, 2026-11-09

Uncommitted.

## 1. all-filings with JavaScript off
- Root cause: `pages/campaigns.py` shipped the 479 filings only as JSON (`#cf-data`); `campaigns.js` built the table and the committee list.
- Fix: each filing is now one `<tr>` in the HTML (`#cf-table`, `_filing_row`), in office order with the group and office heading rows, inside the `#cf-all-fold` fold (ships open; folds.js closes it with JS). Rows carry `data-ci/oi/gi/cy/pt/rec/exp/cash/st`. The JSON no longer holds rows (only committee names, cycle totals, offices, groups, badge text).
- `campaigns.js` now only filters and sorts those rows (non-matching rows are detached from the tbody, never deleted, so Copy CSV copies what is shown), and derives the per-committee list from clones of the rows. Each filing therefore exists once in the HTML. The per-committee list is JS-only (a view of the same rows); without JS the full table is complete, with the committee column, sorted by office then committee.
- All ids kept (`cf-table`, `cf-table-copy`, `cf-all-fold`, `cf-list`, `cf-comm-N`, `cf-controls`, etc.). The `hidden` flag on the explorer block and the noscript callout were removed.
- Size: 228,096 B before, 576,846 B raw after (63 KB gzipped). JSON fell from 147 KB to 30 KB; the rows cost about 1 KB each. Status badges use the short link form (no per-row definitions).
- Not changed: cycle totals for a selected committee still need JS (they are also on the area pages).
- Verified (Chrome, own tab): 479 rows and 211 committee folds on load; cycle filter (169 reports, 120 committees, fold label follows); amount sort drops headings and shows the office line; group filter keeps headings; committee fold opens to its 5 reports; committee select shows totals; reset returns 479; Copy CSV runs on the shown rows. Python count of raw HTML: 479 `<tr data-ci=`. Test updated in `test_wave_b_batch4.py`.

## 2. entity_list status
`civic/components.py`: a `Markup` status is passed through unchanged; a plain key goes through `status_badge`. history/people already passes the plain key, so I left it alone (no cleaner alternative). Tests in `test_wave_b_fixups.py`.

## 3. Contest to office mapping
- Code: `Edition._contest_office` in `civic/data.py`. Added `CONTEST_OFFICE_ALIASES` (documented, explicit, built by `_board_aliases`). No CSV edits.
- Walkerton: `2015g-walkerton-judge`, `2023p-walkerton-judge-r`, `2023g-walkerton-judge` now resolve to `walkerton-town-judge`; the Walkerton page shows the seat links.
- Audit (results.csv x offices.csv, 1,243 contests): unmatched went from 268 to 109. Also fixed as clearly the same office: at-large town councils (Roseland, New Carlisle, North Liberty, Lakeville, Osceola) and the school boards of South Bend, Penn-Harris-Madison, John Glenn (including Lincoln's "first/second listed"), Union-North/LaVille, New Prairie (numbered districts, at-large, "2 (Hudson, Wills)") and School City of Mishawaka (elected seats).
- Still unmatched, by design: state offices, statewide and county retention votes, public questions, straight-party counts (101, no office row). Ambiguous, left unmatched: Osceola ward 1-3 council contests (2011, 2019; the office row is a 3-seat at-large council), `2019g-osceola-unknown-office`, `2026g-new-prairie-schools-board-at-large-district-2` (combined line). `test_unmatched_contests_are_only_the_reviewed_kinds` pins this list.
- Side effect to watch: school-board contests now attach to their seats, which may add links on school pages (not my files).

## Checks
`build.py --edition st-joseph --check` PASSED (112 pages); unittest 259 OK; `check_gov.py` 0 errors.

## Files
Changed: `tools/site/pages/campaigns.py`, `static/js/campaigns.js`, `static/css/campaigns.css`, `civic/components.py`, `civic/data.py`, `tools/tests/test_wave_b_batch4.py`. New: `tools/tests/test_wave_b_fixups.py`, this report.
