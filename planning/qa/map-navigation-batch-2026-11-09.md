# Map-navigation batch, 2026-11-09

Four pages now use map-click navigation: your-legislators, county, the budgets page below its top map, and schools. Copy CSV on a filtered table now copies only the rows shown. Nothing is committed.

Checks, all run at the end:
- `python -P -E tools/site/build.py --edition st-joseph --check` ends PASSED (109 pages).
- `python -P -E -m unittest discover -s tools/tests` gives 153 OK. 21 of those are new, in `tools/tests/test_map_navigation.py`.
- `python -P -E tools/check_gov.py` reports 0 errors.

## 1. One pattern for all four pages: "show one"

New shared files: `civic/pick_one.py`, `static/js/pick_one.js` and `static/css/pick_one.css`.

How it works:
- **Each area's detail is a `<details data-one="KEY" data-fold="one" open>`.** An area is a district, an office, a unit or a corporation. Its summary line stays visible when it is closed and gives the name plus a short digest.
- **JavaScript off: everything is visible.** The HTML ships every item open. With JS on, `folds.js` (already on the site) closes them on load, unless the address points inside one.
- **Choosing an area opens that area and closes the others.** You can choose by clicking a map shape, a list or table link, a TOC link, a panel link, an old `#id` in the address, or back/forward. Choosing opens every item with that key, in every section, and closes the items of the other keys. Nothing is removed: any other area opens from its summary line.
- **Rows can be filtered too.** Table rows with `data-one` are hidden while another area is chosen. Today that is only the budgets debt table. The table then fires `rows-filtered`, so Copy CSV copies only those rows.
- **Old anchors still land.** An id that sits outside its item, such as `<section id="sbcsc">` or `<article id="south-bend">`, carries `data-one-for`, so the old `#id` still chooses the area. Ids inside an item, like `#money-phm` or `#results-house-5`, choose it automatically.
- **A state line shows what is open.** It reads "Showing X. The other … are collapsed below." and has **Show all** and **Collapse all** buttons. It only appears with JS.
- **The map side reuses `.cmap`.** No second map engine: `map.js` still gives hover and focus, the panel that keeps the last area, touch select-then-open, and layer tabs.

## 2. Per page

### state/your-legislators/
- **New House/Senate district map** (`civic/district_map.py`) with Indiana House and Indiana Senate tabs. All 9 districts are drawn, clipped to the county.
- **Not shaded.** The fills only tell neighbors apart: four neutral fills, chosen so no two districts that share an edge get the same one. City and town lines and city names are drawn on top so readers can find where they live.
- **The panel shows:**
  - the member now (with party label) and since when;
  - the Nov 3, 2026 result: "Re-elected (unofficial)" or "X leads the unofficial count";
  - the next election and term length;
  - each committee's latest two filing years from `cf_state.csv` (raised and spent), with its role: member, unofficial 2026 leader, candidate or former member;
  - a caveat on the filing-year basis: "totals of the items on reports FILED in each calendar year, not election-cycle totals… the latest year is partial". The same basis line is printed next to the map.
- **New page structure:**
  1. Find your district: the map, plus the districts table with a new "Member now" column whose links choose the district.
  2. One collapsible item per district: the officeholder card, the 2026 county-portion chart, the 2012–2026 results table, and a new per-district committee table (`cf-house-5` and so on).
  3. Results: how to read them, with links to each district's table.
  4. Campaign money: the all-district comparison chart and the matrix, unchanged.
- Every table is still on the page and reachable.

### county/
- **New commissioner (1–3) and council (A–I) district map.**
- **The panel shows:**
  - who represents the district, from terms;
  - since when, and "first chosen by" when that was a caucus or an appointment;
  - the 2026 incoming or re-elected line;
  - the next election and term length;
  - three caveats: the 2022 settlement map (used for 2022/2024/2026 and checked against 2024 only), the council layer named 2025, and the pending lawsuit over district-only elections.
- **A click opens that seat's row.**
- **The 32 officeholder cards are now compact one-line rows** (`civic/holder_rows.py`): office | holder (party) | since, next election, incoming. Each row opens to the card's fields. They keep the card ids (`office-<id>`).
- **Countywide officers and judges are a compact list.** They are labelled "elected by the whole county, so … not on the district map".
- **Superior Court rows use short titles** ("Superior Court judge, Manier seat"). The full listed title is inside the row.

### money/budgets/ (below the map)
- **Map clicks stay on the page.** A click on an area now goes to that unit's block on the page instead of leaving it. The panel's main link is "Show its budgets on this page". A new optional second link, `u.more` in `map.js`, keeps "Full breakdown on its own page".
- **Choosing a unit opens all of its items:** its budget history in Budgets over time, its 2024 breakdown and any "other breakdowns", its rows in the debt table (other units' rows are hidden), and its Money in and out block for libraries and special units.
- **Sections that have nothing for the chosen unit say so.** For example: "No debt rows for X in the state's debt file."
- **Each unit block has a one-line digest when collapsed,** for example "Latest adopted: $108.5M in 2026 (general fund)".
- **Units with no boundary are in the list only.** The 11 libraries and special units are in the unit list above the blocks (now introduced as the place to pick from), and that list chooses the unit too.
- **All-unit comparisons are untouched:** per resident, the debt chart, and tax base.
- **Two tables are now collapsible:** the debt-by-class table (106 rows) and the map's "every figure, as tables" block.
- **Fix: New Prairie.** Its money id `school-new-prairie` was not in `unit_id_aliases.csv`, so the map linked it off the page. `Money` now also uses `EXTRA_UNIT_IDS`, which `tax_base.py` already uses. New Prairie has a block saying it has no budget data. School units now link to their Schools page section.

### schools/
- **Each corporation's section is now one collapsible item.** Its summary line is the section heading plus "N board seats · next election · N students enrolled (year)".
- **One corporation at a time.** The existing map, the at-a-glance table and the TOC each choose one corporation and fold the others.

### Copy CSV (item 5)
- **Filtered tables say how many rows they copy.** When `tablefilter.js` (or `pick_one.js`) hides rows, `static/app.js` marks the table `data-rows-filtered`. The button then reads "Copy 12 shown rows" (or "Copy 1 shown row"), or is disabled as "No rows shown to copy".
- **The CSV matches.** It has the header plus only the rows shown.
- **Unfiltered tables are unchanged:** the label goes back to "Copy CSV" and all rows are copied.

## 3. Screens (height ÷ 800 at 1280×800)

| Page | Before | After, all collapsed (first load) | After, one area open | Before at 400 px | After at 400 px (collapsed / one open) |
|---|---|---|---|---|---|
| your-legislators | 17.8 | 8.6 | 11.5 (HD7) | 26.0 | 11.4 / 15.0 |
| county | 23.9 | 22.7 | 23.0 (Council A) | 44.5 | 36.6 / 37.0 |
| budgets | 80.7 | 17.5 | 25.2 (South Bend) | 109.1 | 23.0 / 33.7 |
| schools | 32.9 | 4.7 | 10.0 (PHM) | 55.0 | 6.6 / 16.1 |

(The survey's figures were higher: legislators 22, county 31, budgets 93, schools 39. Since then the Gaps/Sources folds have taken off some screens on every page.)

- **County barely moved.** The officeholders section is 5.0 screens, down from 5.5, even though it now holds the map (about 1.7 screens). The rest of the page (structure 2.8, results 3.9, money 3.4, party control 2.4) was out of scope.
- **With JavaScript off,** the pages are 34.2, 38.5, 95.1 and 38.9 screens with everything open. Legislators is longer than before because each district now carries its own committee table and the map.

## 4. Design choices
- **I collapse rather than hide.** A reader can still open several items to compare, find-in-page still reaches folded text in Chrome, and printing opens all folds (`folds.js`).
- **The address records the choice.** Choosing an area changes `#` to that area's anchor (normal link navigation), so links are shareable and back/forward work. "Show all" does not clear the hash.
- **No shading on either district map.** Legislators has no meaningful value to shade. County could be shaded by spending, but that belongs to the campaigns map. The fills reuse existing neutral tokens (`--cm-school-0/1/2`, `--cm-township`), which `map.css` already keeps far from both party colors. Party colors appear only in the existing `results_bars` charts.
- **No change to `section()` or other existing helper signatures.** Two existing behaviours did change, for a reason:
  - `money_map()` gained an optional `in_page` keyword. It is backward compatible.
  - `map.js` gained the optional `u.more` links, which other maps do not use.
- **I edited `static/app.js`, which the README says is foundation-owned.** The task required it, because Copy CSV lives there. The change adds 30 lines and nothing else in the file moved.
- **Re-tested every page that uses the shared map code:** places, landing, map (including `#townships`), campaigns, community and calendar. The panel works and there are no console errors.

## 5. Browser checks (Playwright, isolated contexts)
- **Overflow and errors.** 11 pages (the four, plus the shared-map pages and the table-filter pages) × 3 looks × light/dark × 1280/400 = 132 loads. Look and theme applied every time, with no horizontal overflow and no console errors.
- **Hover and focus:** the panel fills and keeps the last area after the pointer leaves.
- **Keyboard:** Senate tab by Enter, focus a district, Enter opens only that district.
- **Show all / Collapse all:** work; the state line reads "Showing all 9 districts."
- **Table links and back:** a districts-table link chooses its district; Back returns to the previous district.
- **Touch at 400 px:** the first tap on Council A fills the panel without navigating; the second tap opens `#office-county-council-a`.
- **Old anchors**, loaded fresh: `schools#money-phm`, `schools#new-prairie`, `county#office-county-sheriff`, `budgets#lakeville` (its 5 debt rows shown), `budgets#breakdown-county`, `legislators#results-senate-9`. Each opens its item and lands on the target.
- **Copy CSV:**
  - calendar filtered to 2026 reads "Copy 60 shown rows" and the clipboard has 61 lines;
  - after a reset it reads "Copy CSV", with 189 lines;
  - budgets with Mishawaka chosen reads "Copy 6 shown rows", all of them Mishawaka;
  - a search with no match gives a disabled "No rows shown to copy".
- **JS off:** all items are open on all four pages (9, 32, 54 and 6), no row is hidden, and every map shape is a plain link.
- **Screenshots** are in `.playwright-mcp/`, which is gitignored:
  - `leg-map-1280.png`, `leg-after-click-1280.png`, `leg-map-400-wayfinding-dark.png`
  - `county-1280.png`, `county-map-1280-line-dark.png`, `county-400-ballot-light.png`
  - `budgets-sb-1280.png`, `budgets-map-hover-1280.png`, `budgets-overtime-400-dark.png`
  - `schools-phm-1280.png`, `schools-1280-wayfinding.png`
- The test scripts are `matrix.js`, `interact.js` and `shots.js`.

## 6. Tests added (`tools/tests/test_map_navigation.py`, 21)
- **Anchors.** Every id the four pages had before is still there; the snapshot is `tools/tests/fixtures/anchors_before_map_batch.json`. There are no duplicate ids, and old unit and district ids choose their item.
- **Progressive enhancement.** Every item ships open.
- **Map links.** Every map shape links to an item on the same page: legislators 9, county 12, all 28 budget areas, and schools.
- **Panels.**
  - Legislator panel: has member, next election and the filing-year basis caveat.
  - County map: covers every commissioner and council seat, and its panel starts with "Represented by".
  - Budgets panel: keeps a link to the unit's own page.
- **Page contents.**
  - Every county office is a row.
  - The budgets unit list keys are all real.
  - Debt rows are keyed and wrapped.
  - Comparison charts are kept and not keyed.
- **District maps:** no party or value classes.
- **Unit tests:** the neighbor-fill logic, the officeholder line (vacant, incoming, re-elected, caucus), and name matching ("Timothy Wesco" = "Tim Wesco").
- **Static script checks:** Copy CSV logic present, ASCII only, no innerHTML, and `pick_one.js` runs after `folds.js`.

## 7. Data issues found (data CSVs not edited)
1. **Four Superior Court seats have no current holder in `terms.csv`:** the Reagan, Chapleau, Marnocha and Hurley seats. The page says "No current officeholder in the guide's data", as the old cards did.
2. **`school-new-prairie` is missing from `derived/unit_id_aliases.csv`.** The build warning already lists it as unmapped. I worked around it in the page code with the existing `EXTRA_UNIT_IDS`. Adding the alias row would be the clean fix.
3. **PHM board seats contradict the district-maps research.** The seats table says "Voters in Harris Township" (and Penn, Madison). The research (`district-maps-2026-11-09.md` §5) found that the 2024 results show these township seats voted corporation-wide, with a residency requirement. One of them should be checked.
4. **`cf_state.csv` names do not always match terms names** ("Timothy Wesco" vs "Tim Wesco"). I handled it with last name plus first initial. HD6 also includes B. Patrick Bauer's committee (former member), labelled as such.
5. Not a data error: the county commissioner and council panels use land-area share. That is not population; districts are drawn by population.

## 8. Questions for Nick
1. **County page length.** The officeholders section is compact now, but the page is still about 23 screens because of the results, money and structure sections. Should the next step fold "Recent results" by district (the same pattern), so a chosen district shows only its races?
2. **Default state.** Every page now loads with all items collapsed (summary lines only). Should the county or schools page open the reader's saved place (the "You are here" choice) by default instead?
3. **Budgets "Show all units"** reopens about 50 items (about 95 screens, the old page). Keep it as an escape hatch, or remove it from the budgets page?
4. **Legislators per-district committee tables** repeat rows that are also in the all-district matrix. Keep both, or drop the matrix's per-committee rows now that each district has its own?

## 9. Files
New:
- `tools/site/civic/pick_one.py`
- `tools/site/civic/district_map.py`
- `tools/site/civic/holder_rows.py`
- `tools/site/static/js/pick_one.js`
- `tools/site/static/css/pick_one.css`
- `tools/site/static/css/district_map.css`
- `tools/tests/test_map_navigation.py`
- `tools/tests/fixtures/anchors_before_map_batch.json`
- this report

Changed:
- `tools/site/pages/state.py` (legislators builder)
- `tools/site/pages/county.py`
- `tools/site/pages/money.py` (budgets builder, `Money._uid`)
- `tools/site/pages/places.py` (schools builder)
- `tools/site/civic/money_map.py` (optional `in_page`)
- `tools/site/static/js/map.js` (optional `u.more`)
- `tools/site/static/app.js` (Copy CSV)
- `tools/site/static/js/tablefilter.js` (fires `rows-filtered`)
- `tools/site/README.md` (three new rows)

Not touched: the campaigns files, data CSVs, and the rest of `planning/qa/`. I did not update `Roadmap.md` or `docs/session-handoff.md`; that is left for the main session.
