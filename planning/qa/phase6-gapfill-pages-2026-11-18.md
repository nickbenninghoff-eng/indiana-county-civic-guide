# Gap-fill round 2: the site shows the merged data (2026-11-18)

Brief: `planning/gapfill/PAGES-BRIEF.md` (items 1-10). Work is uncommitted, and no files under `data/` were edited.
Status marks are as built in the status-marks round: official figures carry no mark, ‖ means computed, † means unofficial.

## What was built (by brief item)

1. **Unclassified contests.** Compare and Margins no longer crash with `KeyError 'Other'` (the U.S. House contest
   caused it). If `classify()` can't place a contest, it is counted in a neutral "Other contests" group with its own
   area level. The new "Federal offices" group covers U.S. House (district, county portion, multi-county) and
   U.S. Senate/President (statewide). In the 2026 canvass, the retention lines for Fronk and Francisco sit under a state
   heading. The site now maps them to the Superior Court seats (Reagan and Marnocha) and puts them under "Superior Court
   retention". Aliases were added for treasurer, Supreme Court, Court of Appeals and Tax Court.
2. **2026 wording now follows the data.** The new `civic/results_status.py` reads each row's status. Its summary:
   124 of the 166 result lines are official (from the official county canvass of Nov 13, 2026) and 42 are not. Of
   the 42: 5 lines in 2 contests are waiting for a recount window to close, 10 lines in 7 contests are waiting for
   another county's figures, and 27 lines in 11 contests are waiting for state certification. This text replaced the
   hard-coded "unofficial until certified" sentences on the following pages: the calendar, About, the county page,
   place pages, the state pages, the GA chart note, the office Elections tabs, and the definitions of the status
   badge and figure mark. When a 2026 tab mixes official and unofficial results, it now opens with "Unofficial" and
   this split; each unofficial contest keeps its own mark.
3. **Ballot-question wording comes from `ballot_questions.csv`.** It is shown verbatim with its kind, notes, status
   and source. "[number not read]" is gone.
4. **Contacts.** The contact section was rebuilt to show office contacts only: phone, website, contact page and office
   email. Office emails are printed as text, never as `mailto:` links, because `check.py` forbids that link scheme.
   Each body's meeting rule is shown as stored, with its schedule year and "as of" date. A blank rule points to the
   body's own site. Only http(s) addresses become links. A personal-mailbox pattern triggers a warning and the row is
   not shown. A contact for a body with no page of its own (the county Board of Health) appears on its parent's page.
   The Participate page links to these sections.
5. **Board rosters** are folds with ids `roster-<board>`, on the county, place, school and special-district pages. Each
   shows "N members listed, M vacant seats", the seats as stored, an "other seats not in sources" line, holdovers and
   who appoints. No party or contact details are shown. South Bend's Board of Public Safety lists 3 members, never 5.
6. **Debt by year (2022-2025).** Each unit's Money tab now has a by-year column chart in the accent color only, a
   latest-year breakdown by class, and a table with every class. On Compare budgets, the `debt-2024` id is kept but
   the chart now ranks the latest year, and a new `debt-by-year` fold was added. The stored notes ("never add the two
   totals", "Includes utility debt") are grouped by sentence and shown wherever those totals appear. The
   whole-corporation note for New Prairie and Union-North appears once per page.
7. **Federal and statewide offices.** They have pages: the hub skips a "how to run locally" section and adds "Who
   votes here". The Offices hub map and the home map gain Statewide and Federal layers. Each layer is the county
   outline plus a label and a note; no new geometry is drawn. "Includes all of the county" is shown only when
   `units.csv` says the district covers the county wholly. The home page now reads "173 elected local seats", leaving
   out legislature, state and federal seats.
8. **Campaigns.** U.S. contests are skipped, because those candidates don't file with the county. This removes the
   warning that 2026g-us-house-2 has no office mapping.
9. **County vote beside the overall result** (new `civic/overall.py`). In a multi-county contest, the county chart is
   titled "St. Joseph County portion" and no winner is marked on its bars. A table follows comparing the county with
   the whole electorate: "Won" goes to the overall winner, and a different county leader is described as "received
   the most votes in St. Joseph County". Computed figures are marked ‖, and the cited source is "official results as
   reported to the Secretary of State". Other cases get one sentence each:
   - Districts wholly inside the county: the wholly-in-county sentence, once per district per page.
   - 2026 contests: "Overall result awaits state reporting."
   - No overall row: "Overall result not in the guide yet."

   Result and margin lines on election and office pages now use the overall result. On Compare and Margins,
   cross-county school races are ranked on the overall margin, with a "Margin from" column. A county portion with no
   overall figure is never ranked; it is counted as "can't be measured".
10. **Tests.** The new file `tools/tests/test_gapfill_pages.py` has 26 tests. These existing tests were updated:
    - `test_phase6_offices`: the office count is now 139.
    - `test_phase6_offices2`: rows follow `offices.csv`. HD48, from the 2001-2011 map, has no area on today's map;
      the test asserts it is still listed below the map. The unmatched-contest audit checks that newly matched
      contests map to this round's offices.
    - `test_landing_header`: counts local seats only.
    - `test_status_marks` and `test_phase6_elections`: 2026 tabs can now be mixed. The banner appears exactly when
      the tab shows an unofficial figure. The uncontested count went from 608 to 612, because four races became
      measurable from merged data.
    - `test_wave_c_judges`: the sources the page no longer cites (src-ELX-003, src-ELX-004, src-RES-029) now redirect
      to the sources index through `#moved-anchors`.

### Fixes after the first full test run (12 failures, all from the merged data)

- **Old source links.** A source whose notes say "Superseded ... by X" now keeps its old `#src-<id>` on X's entry in
  any Sources list that cites X but not the old source; the entry shows "Replaces RES-029". The data hub's map
  follows it as well (`civic/components.py superseded_by`, `pages/data_sets.py`). This keeps RES-029 and GOV-001,
  both replaced by RES-048, working on the calendar, Elections, Your legislators and Data pages.
- **Sources no longer cited.** On the Money hub (MON-004) and Your place (GOV-072/073), a source that is no longer
  cited forwards by the `src-` prefix to the sources index, which lists every source.
- **Calendar.** The statewide and federal offices of `offices.csv` are filed as "Statewide offices" and "Federal".
  The rule-made Governor, Attorney General, Secretary of State and Treasurer rows are skipped when an office row
  already covers them.
- **Question groups.** The merged canvass labels name the corporations in full, so the 2013 and 2016 "mishawaka"
  questions are now the School City's. A question now takes the layer of the government its ballot line names. The
  old group ids `q-group-new-prairie-schools` and `q-group-south-bend-community-schools` forward to the new ones.
- **Fixture regenerated.** `tools/tests/fixtures/status_marks_before.json` was regenerated from the merged build:
  same 43 pages, 2,663 pairs. The old copy is saved at
  `C:\Users\nickb\AppData\Local\Temp\claude\771e0876d42c3705\0e1b2f9c-dae6-42c6-949d-8defb306c076\scratchpad\status_marks_before.pre-gapfill.json`.
  570 old pairs no longer matched. 537 of them have a mark of the same kind whose context starts the same way: only
  the text changed (new "Margin from" column, counts 608 → 612). The other 33 were checked one by one; each status
  changed in the data or its numbers moved. Example: 2012 HD7, Niezgodski, `from_scan` → `official`.
- Test updates: `test_wave_e_preselect` (group names), `test_phase6_home` (two more layers), `test_wave_d_nav`
  (forwarded sources).

## Files changed this round

`tools/site/civic/{overall.py (new), results_status.py (new), data.py, components.py, offices.py, preselect.py}`;
`tools/site/pages/{elections.py, election_pages.py, elections_numbers.py, county.py, places.py, meta.py, state.py,
community_history.py, gov_parts.py, governments.py, participate.py, money.py, offices.py, landing.py, people.py,
campaigns.py, data_sets.py}`; `tools/site/static/css/{governments,money,map,home,elections}.css` (tokens only);
`tools/tests/{test_gapfill_pages.py (new), test_phase6_offices.py, test_phase6_offices2.py, test_landing_header.py,
test_status_marks.py, test_phase6_elections.py, test_wave_c_judges.py, test_wave_e_preselect.py, test_phase6_home.py,
test_wave_d_nav.py, fixtures/status_marks_before.json (regenerated)}`; `Roadmap.md` (one line).

## Checks (exact output)

- `build.py --edition st-joseph --check`: `Checked 3530 pages, 1 stylesheet(s).` /
  `PASSED: links, titles, document structure, CSS tokens, neutrality terms, contract extras.` (The build before that
  failed on 7 `mailto:` links; this is fixed.)
- `check_gov.py`: `units=42 offices=139 terms=446 appointed_boards=20 sources=211 gaps=24 unit_contacts=36
  appointed_board_members=105 | errors=0 warnings=24`
- `check_money.py`: `OK: all rows parse; no series mixes bases; amounts numeric; every row has status and source_ids.`
- `check_results.py`: `ERRORS: 0` / `WARNINGS: 0`
- Full test suite (`python -P -E -m unittest discover -s tools/tests`, after the final build): `Ran 714 tests in 1449.412s` / `OK`. The first full run, before the fixes above, reported `FAILED (failures=11, errors=1)` out of 711 tests.
- Browser (Playwright, localhost:8787): 11 views (listed below) × 6 combinations, 66 in all. The combinations were
  1280 and 400 px in the ballot look, light and dark (4), plus 1280 line/light and 400 wayfinding/dark. No view
  scrolls sideways, and each target element was present. On the home map, Federal was active (`.is-on`). Screenshots
  are in `planning/qa/phase6-shots/gapfill-<view>-<width>-<look>-<theme>.png`. The views:
  - county contacts
  - county rosters
  - South Bend
  - debt by year
  - Governor
  - U.S. House 2
  - home map with the Federal layer
  - 2016 Governor county vs overall
  - 2024 question 1
  - State House 7, 2026
  - New Prairie school board

## Not checked or left open

- Keyboard and JS-off were not checked for the new folds or the map layers. The folds are `<details>` and the layer
  notes ship visible, but nobody tried them.
- At 400 px the county-vs-overall table scrolls inside its own frame (the existing table pattern), not across the page.
- The 2016 county-vs-overall and 2024-question screenshots were retaken after the final build. The new wording,
  "Statewide (all counties)", is shown; the question is opened from its link and reads "Statewide: Yes (ratified)".
- Open questions for Nick:
  - Should HD48 (2001-2011 map) stay an office? It has no area on today's map.
  - 49 legislative contests have no overall row ("missing"). These are the pre-2011 and 2011-plan multi-county
    districts.
  - Office emails are printed but not linked, because `check.py` bans `mailto:`. Confirm that is wanted.
