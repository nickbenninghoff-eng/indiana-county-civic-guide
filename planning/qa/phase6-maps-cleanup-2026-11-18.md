# Phase 6: maps on every major page + cleanup (2026-11-18)

Brief: `planning/maps-cleanup-brief-2026-11-18.md`. Nothing committed, staged or deployed; no edits under `data/`; no
data builders run. All work is in the working tree.

## Part A: the map navigator

One reusable component: `tools/site/civic/navmap.py`, `static/js/navmap.js`, `static/css/navmap.css`.

- **Shared geometry.** Every area path sits once in `assets/navmap.svg` (72 KB, cached). It holds the official
  boundary files unchanged, with no colour or class. Pages draw areas with `<use href="…/assets/navmap.svg#nm-…">`
  and never inline a path. `check.py` now also reports a link or `<use>` that names a missing id in an SVG file.
  `<use>` with an external file works under the Netlify CSP (`img-src 'self'`; tested in Chromium with the CSP
  headers sent).
- **JS off.** Every area is a plain link to its page (the government, office or Money/Elections tab), so the map is
  a working index. The layer bar stays hidden and the first layer shows. The full list is on the page as before.
- **Row keys, once per page.** Rows carry base-36 numbers into one key list, `data-nm-dict` on the navigator
  (`navmap.compact_row_keys`). The results page's 1,259 rows had carried 57 KB of repeated keys, which took the page
  over the 700 KB budget in `test_phase6_elections`. It is now 697 KB, and that budget was not raised.
- **JS on.**
  - Layer buttons (`aria-pressed`). Selecting an area filters the page's rows (tagged `data-nm`) and shows
    "Showing N … for X." in a polite live status line. Selecting the same area again opens its page.
  - "Show every …" button. A tablefilter bar, where there is one, is scoped through its `tf-scope` event. The
    all-filings table filters itself through `nm-scope`.
- **Not on the map.** Countywide, statewide, federal, courts, libraries and money-only governments appear as chips
  beside the map.
- **Fills.** Neutral kind fills only (the existing `.cmap-*` and `dmap-f*` classes); never party colours, never
  amounts.
- **Saved place.**
  - The map preselects the reader's saved place only when the page has no saved-place line of its own and the URL has
    no #anchor. The status line says it is the saved place.
  - Selecting anything pauses an active saved-place line.
  - A saved place that no longer exists is ignored, and the whole list is shown (checked in the browser).

### Coverage

| Page | Map | Default | Filters |
|---|---|---|---|
| Money hub `money/` | yes | open | governments with money on record (new "Money by government" list) |
| Campaign money: By office `money/campaigns/` | yes | folded ("Show map") | office rows, plus the tablefilter |
| By election | yes | folded | race rows and charts per election |
| By candidate | yes | folded | names (by race office, news contest, state district) |
| Every filing `money/campaigns/all-filings/` | yes | folded | the filings table, through its own filter |
| Elections hub `elections/` | yes | open | the election timeline and ballot cards |
| Results `elections/results/` | yes | open | "Pick an office" and the every-contest table |
| Calendar | yes | folded | seat rows, plus the tablefilter |
| Judges & questions | yes | folded | public questions |
| Each election's Contests tab (with more than one contest) | yes | folded | contests |
| People hub | yes | open | people (by the seats they held or ran for) |
| Who holds office `officeholders/` | yes | open | officeholder rows |
| Community hub | yes | open | a new "area by area" list linking each place's community figures |

Pages that already had a map were kept as they are: home, the Offices and Governments hubs, Compare budgets, close
races, Your legislators, the community indicator map and `map/`.

**Deliberate exclusions.**

- Learn and guide pages; About, Sources and method pages; single office, person and government pages; data downloads.
  This follows the brief.
- **Committees** (`money/campaigns/other-committees/`). The brief asked for a map here. Its rows are, by definition,
  committees tied to no government or office, so a map would have nothing to filter.
- **Turnout.** Turnout figures are countywide or municipal only; there is no per-area turnout to filter.
- **Compare overview.** It is summary cards; Close races already has its own map.
- **History.** Four party-control charts and the mayors. Each government's History tab is reached from the
  Governments hub map.
- **State government.** State level only.
- **Run for office and Who handles this.** Guides, not lists by area.
- **Your place.** It is the place picker itself.
- **Tax bill.** Tax districts have no boundary file.
- **The Indiana page.** The guide never draws Indiana.
- **`schools/`.** A forwarding page.

### Checks

- **Tests.** New file `tools/tests/test_maps_navigator.py`: 14 tests, OK. They cover:
  - the asset equals the boundary files, with no colour;
  - no page inlines geometry, and every `<use>` resolves;
  - per-page presence, open or folded, live status, hidden bar;
  - every row key is reachable;
  - neutral fills and correct row keys;
  - exclusions;
  - edge cases: unknown office, court, no-boundary unit, money-only government, no tagged rows;
  - the script contract;
  - the checker catching a missing id.
- **Browser** (localhost:8787, Chromium):
  - Every page that gained a map, at 1280 and 400 px, ballot look, light and dark (52 shots).
  - Other looks: Results at 1280 in line/light and wayfinding/dark; Money hub at 400 in line/dark; People at 1280 in
    wayfinding/light.
  - No horizontal overflow and no console errors on any of them.
  - Filtering checked on every page (e.g. Elections hub: Walkerton → 10 elections; Results: Mishawaka → 95 contests;
    By office: County council C → 1).
  - Screenshots in `planning/qa/phase6-shots/`, named `maps-<page>-<width>-<look>-<theme>.png`, plus
    `maps-results-1280-nojs.png` and `maps-learn-cards-1280-ballot-light.png`.
- **Keyboard walk-through** (Elections hub). Tab reaches "Cities and towns" (pressed). Tab moves to "Townships",
  and Enter makes it pressed. Tab moves through the township links: Centre, then Clay. Enter on Clay Township gives
  it `aria-current`, and the status reads "Showing 10 elections for Clay Township." 10 of 50 rows stay visible.
  "Show every election" restores all 50. Enter twice on an area opens
  `governments/centre-township/elections/`.
  - Defect found and fixed: after "Show every …", focus fell to the page body, because the button hides itself.
    Focus now returns to the area that was selected. This is pinned in the navigator test.
- **JS-off view** (a separate browser context with JavaScript disabled).
  - The six open hubs and By office have navigators made of plain links (28 to 61 per page). The layer bar is hidden
    and one layer shows.
  - Governments, Offices, Learn, About, Data, State, History, Compare budgets and a Sources tab all render.
  - No overflow anywhere.
  - Results screenshot: `maps-results-1280-nojs.png`.
- **Saved place.**
  - On the People hub, Mishawaka is preselected and the status reads "Your saved place (kept on this device only):
    Showing 49 people for City of Mishawaka."
  - A saved place that no longer exists shows the default status and all 752 rows.

## Part B: cleanup

| # | Item | State |
|---|---|---|
| 1 | Learn cards | **Done.** A 1px `--line` hairline in every look (`learn.css`); screenshot taken. |
| 2 | Page weight | **Done**; details below. |
| 3 | Sources tabs | **Done.** Tabs that ran 4.1 to 7.9 screens (with every fold open) now open at 1.5 to 1.9 at 1280×1080. |
| 4 | Campaign "incomplete" | **Done.** |
| 5 | "Computed" once | **Done.** |
| 6 | Footer "What the badges mean" | **Done.** |
| 7 | Compare budgets | **Done**, measured at 3.49 screens (target "about 3"). |
| 8 | Final checks | **Done**; results below. |

**Item 2: page weight.**

- The saved-place data and the learning paths are now one shared script, `assets/site-data.js` (11 KB), which sets
  `window.civicData` before `app.js`. Five scripts were changed to read it: app, community, moved, here and
  your_place.
- The masthead's Indiana glyph (92 county paths, 12 KB a page) is now `assets/indiana-glyph.svg`, drawn with two
  `<use>` elements. CSS still colours it in every look.
- Together these were 86 MB of repeated bytes: glyph 46.7 MB, here-data 19.9 MB, paths-data 19.8 MB.
- The remaining masthead (7 KB) is the no-JS navigation, and was kept.

**Item 3: Sources tabs.**

- The sources are grouped by kind (official records, laws, datasets, derived files, secondary, news). Each group is a
  fold that shows its count.
- Every item keeps its id `src-<id>` and its footnote number (`<li value>`).
- A gaps list of 4 or more is folded, and so is the marks key.
- The folds ship open (JS off), and `folds.js` opens the group a link points into. Checked: a footnote link from the
  Money tab lands on its open group.
- A list under 9 sources stays one plain list.

**Item 4: campaign "incomplete".**

- Map bars, candidate bars and panel record lines now use `*`; legends say "N of M are marked *" with the linked mark.
  Subtitles say "a total marked * is a floor".
- Screen-reader names keep "incomplete record (marked *)", because a bare symbol would be read aloud as "star".
- What is left: the verbatim transcription notes from the data ("office line blank or incomplete").

**Rows in a "Show the other N" fold keep their status.** `test_status_marks` found that Compare budgets' "other N"
charts carried no status, so rows 7 to 10 lost "computed" when the lists were shortened. This was already true for
rows 11 and up. `pages/money.ranked` now passes the status to the fold's chart, so every row has it again.

**Item 5: "computed" once.**

- Each computed symbol is replaced by a hidden marker (`<span class="fquiet" data-fquiet="computed" hidden>`). The
  status stays recorded on its figure, and Copy CSV still writes "COMPUTED".
- The page's note says it once, with one added sentence.
- `test_status_marks.py`:
  - The fixture was **not** regenerated for this item. Six entries were updated for item 7, and nothing else
    changed:
    - Compare budgets' three ranked charts now say "top 6 of N" where they said "top 10 of N".
    - The six caption contexts (each chart's title alone, and title plus subtitle, for `…top10of15`, `…top10of16`
      and `…top10of25`) were replaced by the three new caption contexts.
    - Each new entry has the same status (computed).
    - The change is recorded in the fixture's `_about`.
  - `status_marks_lib.mark_kind` now reads the marker as "computed" on its own row, so the per-figure check still
    finds every computed figure in place.
  - The symbol and note test also counts quiet kinds.
  - Two other tests now look for `data-fquiet` where they looked for the symbol.
- A page-wide scope was tried first and rejected: it would have claimed that every figure on the page was computed,
  and that would have made the fixture check pass for any figure.

**Item 6: footer and About wording.** The link now reads "What the marks mean", and the `#badges` anchor is kept. The
About section is titled "How figures are marked", and the About description and two lesson prompts no longer say
"badges".

**Item 7: Compare budgets.**

- At 1280×1080 the page went from 4.63 to 3.49 screens.
- Changes:
  - three per-resident lists side by side;
  - six rows per list, with the rest in the existing "Show the other N" folds;
  - the county figure and the map's method note moved into the map's side column;
  - the map is capped at 440 px tall;
  - the debt notes and the whole-corporation note are folds;
  - the lead is shorter.
- No figure was removed, and every old id is kept (`test_phase6_money` passes).

**Item 8: final checks.**

- CSP: `netlify_prep.py` on a copy of the build reports "CSP check passed".
- Old-URL and old-anchor fixtures: all pass (one note below).
- `pages/campaigns._filing_row` now writes `data-nm` last, so `data-ci` stays the first attribute of a filing row
  (`test_wave_b_batch4` counts `<tr data-ci="`).
- Keyboard and JS-off checks: as above.

**Old-anchor fixtures and the retired data-block ids.**

- The fixtures had recorded `here-data` and `paths-data` as page ids. These were `<script type="application/json">`
  blocks, which are not rendered, so they were never places a link could land.
- New loader `tools/tests/anchor_fixtures.py` leaves just these two ids out. The 13 fixture files are unchanged, and
  every other id is checked as before.

### Site size

| | Before | After |
|---|---|---|
| Site | 250,010,112 bytes | **165,112,685** (−34%) |
| HTML | 190,009,149 | 104,994,111 |

Images are unchanged at 58.4 MB. A typical page (`offices/south-bend-mayor/`) went from 43,929 to 19,809 bytes.

Heaviest pages, before:

| Bytes | Page |
|---|---|
| 1,299,916 | `money/campaigns/county` |
| 934,807 | `data/indicators` |
| 883,710 | `elections/compare` |
| 719,199 | `money/budgets` |
| 682,051 | `money/campaigns/state-legislature` |
| 669,543 | `elections/results` |
| 610,616 | `data/results` |
| 564,261 | `money/campaigns/all-filings` |
| 546,209 | `state/your-legislators` |
| 522,381 | `data/cf-local` |

Heaviest pages, after:

| Bytes | Page |
|---|---|
| 1,212,360 | `money/campaigns/county` |
| 910,687 | `data/indicators` |
| 858,113 | `elections/compare` |
| 697,020 | `elections/results` (navigator, about +28 KB) |
| 637,639 | `money/budgets` |
| 586,496 | `data/results` |
| 572,121 | `money/campaigns/all-filings` (navigator) |
| 530,530 | `money/campaigns/state-legislature` |
| 518,468 | `state/your-legislators` |
| 498,261 | `data/cf-local` |

These are content-heavy pages: race cards and tables, and the CSV blocks on the data pages. They are not repeated
chrome.

## Exact check output

- Build (`--check`, final code): `Checked 3526 pages, 1 stylesheet(s).` / `PASSED: links, titles, document structure, CSS tokens, neutrality terms, contract extras.`
- Full suite (`python -P -E -m unittest discover -s tools/tests`, final code): `Ran 744 tests in 1001.957s` / `OK`. An earlier run of the suite failed 3 tests (results page over its 700 KB budget; Compare budgets fold rows had lost their status; filing rows' `data-ci` was no longer the first attribute). All three were fixed at the root, as described above.
- `check_gov.py`: `units=42 offices=138 terms=446 appointed_boards=20 sources=211 gaps=24 unit_contacts=36 appointed_board_members=105 | errors=0 warnings=24`
- `check_money.py`: `OK: all rows parse; no series mixes bases; amounts numeric; every row has status and source_ids.`
- `check_results.py`: `ERRORS: 0` / `WARNINGS: 0`

## Not checked

- Firefox and Safari: only Chromium was used. External SVG `<use>` is widely supported, but it was not tested here.
- A screen reader was not used; only the accessible names and the live region were checked in the DOM.
- Charts' "Show table" views are not filtered by the map.
- The home, Offices and Governments hubs still inline their own map SVGs; they were not converted to the shared
  asset.

## Open questions for the owner

1. Committees has no map: its rows belong to no area. Agree, or should it get an "area of the candidate" map once
   that is in the data?
2. Should the home, Offices and Governments hub maps move onto the shared `navmap.svg`? This would save about 50 to
   100 KB on each of those pages.
3. "Computed" is now said only in each page's note. Should a short caption line also say it near the figures on chart
   pages?
4. Status columns still print "COMPUTED" and "OFFICIAL" as words in tables. Keep that, or drop them?
