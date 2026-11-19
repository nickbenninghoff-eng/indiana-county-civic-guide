# Phase 6 step 3: Government pages and the Governments hub (2026-11-16)

Design direction: `planning/design-direction-2026-11-16.md`, section 6 step 3. Nothing is committed. All changes are in the working tree.

## What was built

### Government pages

There is one home per government at `governments/<id>/`. Each tab is a real URL, and empty tabs are neither built nor linked. The tabs, in order, are Overview, Elections, Money, History and Sources.

There are 40 governments:
- the county
- 2 cities
- 7 towns
- 13 townships
- 6 school corporations
- 11 libraries and special units, listed only when the state money files have figures for them. These get Overview, Money and Sources only.

**Overview**
- An "at a glance" box. This is the existing `answer_box`; school corporations and special units get a glance list instead.
- Where it is: a small static locator SVG, with the townships it lies in or the places inside it.
- How it is organised: the existing rule text. The one-row-per-body table now sits in a fold.
- Offices and who holds them: one row per office (office, holder with party tag, next election), each linking to `offices/<id>/`. South Bend, Mishawaka and the county keep their district maps.
- Appointed boards, in folds.
- Contact and meetings.
- The community strip with margins of error. It comes last, after Contact (rule F6).
- The "More about" rail.

The county's Overview also has the row officers, the courts, the appointed boards and the state delegation, each table in a fold.

**Elections**
- Recent results, the mayoral history, and school labels and referenda. These reuse `places._results_section` and the county's `_results_body`.
- Each race links to its office's Elections tab.
- The county also gets retention votes.

**Money**
- Budget over time: the chart first, the table behind "Show the table". It reuses `money._unit_charts`, the dollars toggle and the "others" table.
- Then the tax base and rate, then debt (the new `money.unit_debt_parts`).
- Then money in and money out, and the 2024 breakdowns. Both are folded and both are the existing renderers.
- Then state audits.
- No figure is re-derived.

**History**
- Party control (`control`) and holders over time, each holder linking to its office's History tab.

**Sources**
- `T.sources_body` with this government's gaps (budget flags, money gaps, unit gaps).

### Governments hub (`governments/index.html`)

- It leads with the boundary map, with layers for cities and towns, townships and school corporations. The panel links to the government's page and each of its tabs.
- Then a list grouped by type: County, Cities, Towns, Townships, School corporations, Libraries and special units.
- Then "Also": Offices, Your governments, Officeholders, Who handles this, and the full map.
- It opens on the reader's saved place through `here_slot("map")`. Guide defaults do not count. Checked: a saved Penn Township selected the Townships layer and Penn's panel; with no saved place the slot stayed hidden.
- The header's Governments item and its dropdown point at the hub: County, Cities and towns, Townships, School corporations, Libraries and special units, State government.

### Forwarding pages

`places/index.html`, the 22 `places/<id>/` pages, `county/` and `schools/` are now small forwarding pages. Each has:
- a title and one line with a plain link
- `rel=canonical`
- a "Where each part of the old page is now" list that carries the old ids, so a JS-off reader on an old `#anchor` lands on a line that links to the new place
- the `#moved-anchors` map, read by `moved.js`, which gained `"to"` handling

### Netlify 301s

- `netlify_prep.py` now appends forced 301s (`301!`), both the folder form and the `index.html` form, for every page carrying `<meta name="civic-moved-to">`. That is 48 lines (24 pages).
- `schools/` gets no 301, because it was split in six.
- Each government Overview ships its own moved-anchors map, so `/places/south-bend/#budget` still ends on Money#budget after the 301.

### Other changes

**Search**
- Every government page, and each tab with plain keywords ("south bend budget" finds Money), is in the index as the new type 9, "Government".
- Forwarding pages are left out.
- Office fallback links no longer point at forwarding pages.

**CSS**
- New `static/css/governments.css`, tokens only.

## Every old URL and where it goes now

| Old URL | Now | How |
|---|---|---|
| `places/index.html` | `governments/index.html` | 301 plus JS forward. `#cities`/`#towns`/`#townships` and each place's id go to its hub row. `#citys` goes to `#cities`. `#src-*` goes to the hub's sources. |
| `places/<id>/` (22 pages) | `governments/<id>/` | 301 plus JS forward. Each old id goes to the tab that holds it: `#budget`, `#money-<id>`, `#audits` go to Money. `#results`, `#mayor-results`, `#res-*` go to Elections. `#control` goes to History. `#gaps`, `#sources`, `#src-*` go to Sources. Office ids stay on the Overview. |
| `county/` | `governments/county/` | 301 plus JS forward. Same rules. `#money*` goes to Money#money-in-out. `#control*` goes to History. `#results`, `#retention` go to Elections. `#boards`, `#courts`, `#row-officers` stay on the Overview. `#office-superior-court-judge-chapleau` goes to `#office-superior-court-judge-woods`. |
| `schools/` | `governments/index.html#schools` | JS forward only, no 301. Each corporation's ids go to `governments/<id>/` (and their tabs). The page's own sections go to the hub's School corporations group. |

The `PATHS` learning-path stop moved: `county/#boards` is now `governments/county/index.html#boards`.

Every id in `tools/tests/fixtures/anchors_before_governments.json` resolves. That is every id on those 25 pages at the 20:25 build, which is a superset of the older fixtures. It is checked by `test_phase6_governments.test_every_old_anchor_resolves`. The older fixture tests (place template, batch 7, map navigation) now follow the maps too, through `tools/tests/gov_moved.py`.

## Files changed

**New**
- `civic/governments.py`
- `pages/governments.py`
- `pages/gov_parts.py`
- `static/css/governments.css`
- `tools/tests/test_phase6_governments.py`
- `tools/tests/gov_moved.py`
- `tools/tests/fixtures/anchors_before_governments.json`

**Mine**
- `pages/places.py`: the place and school tab renderers; the old builders now forward.
- `pages/county.py`
- `pages/money.py`: per-unit parts; `gaps_href` added to `_unit_charts`.

**Shared** (small, additive edits; each file re-read first)
- `civic/sitemap.py`: entries, NAV, `NAV_OF_TOPIC`, `nav_of`, PATHS stop, `moved_to`
- `civic/search.py`
- `static/js/search.js`: `T_GTAB`
- `civic/shell.py`: `head_extra`; footer links; three forwarding pages removed from `ONPAGE_PAGES` by subtracting from the set (the original set is untouched)
- `static/js/moved.js`: `"to"`
- `civic/related.py`, `civic/map.py`, `civic/money_map.py`, `civic/picker.py`: link targets
- `pages/community_history.py`, `pages/participate.py`, `pages/campaign_pages.py`: link targets
- `netlify_prep.py`

**Tests updated**
- `test_place_template`, `test_wave_c_batch7`, `test_map_navigation`, `test_wave_a_patterns`, `test_wave_d_nav`, `test_wave_e_preselect`, `test_netlify_prep` (new redirect test).
- `test_phase6_offices` (owned by the offices agent): one line changed. The place-page link check now reads `governments/south-bend/`.

`civic/tabs.py` was not changed.

## Decisions and why

- **Party control goes on History** on every government, so Elections holds only results (rule F6). The community strip is on the Overview only, after Contact. A test checks this.
- **`schools/` forwards with no 301.** It was split into six pages, so there is no single target; the hub's `#schools` group is the canonical page.
- **`places/index.html` forwards to the hub.** The hub has the same map and every city, town and township. The hub rows keep the old card ids.
- **Folded to keep tabs short**, all closed by `folds.js` with JS on and open with JS off: the body table, appointed-board tables, the county's rules, row officers, boards and delegation, money in/out and the 2024 breakdowns. A link to an id inside a fold opens it.
- **The Money tab order** is budget, tax base, debt, money in/out (folded), breakdowns (folded), then audits.
- **District maps are capped at 460px tall** on Overviews (CSS only).
- **Flag "see Gaps" links on Money** point to the Sources tab (`gaps_href`, a new optional parameter on `money._unit_charts`).

## Verification

- **Build:** `python -P -E tools/site/build.py --edition st-joseph --check` ends **PASSED**, with no BUILD FAILED. 1013 pages.
- **`check_gov.py`:** 0 errors, 23 warnings (pre-existing data warnings).
- **`check_money.py`:** OK.
- **Unit tests:** `python -P -E -m unittest discover -s tools/tests` ran 500 tests with **1 failure**: `test_wave_e_onpage.test_marked_pages_have_a_toc_that_resolves`, on `elections/margins/index.html`. That page now belongs to the elections agent; see open question 5. Every test I own or updated passes.
- **Browser** (Playwright, localhost:8787). Screenshots are in `planning/qa/phase6-shots/gov-*`.
  - Every tab of South Bend, Mishawaka, Roseland, Penn and Clay Townships, the county, PHM, SBCSC, Walkerton, SJCPL and Transpo loads with no console errors.
  - No horizontal overflow at 1280 or at 400.
  - Looks: ballot light and dark, line light and dark, wayfinding light and dark, spread across the pages.
  - Keyboard: Tab reaches all five tab links, with a 2px focus outline.
  - Old URLs with JS on: `places/south-bend/#budget` → Money#budget. `county/#office-county-sheriff` → the Overview row. `schools/#office-phm-board-penn` → the PHM page. `places/#townships` → hub. `places/penn-township/#control` → History. `county/#boards` → Overview. `schools/` → hub#schools.
  - Old URLs with JS off: each old id lands on its line in "Where each part is now", which links to the new place.
  - Hub with JS off: the plain grouped list with 40 links, and folds open.

## Not met, or not fully verified

**Tab length at 1280x900**, including header and footer (about 600px), folds closed:
- **County Overview: 6.5 screens.** It carries 31 office rows plus the district map; everything else is folded. Office rows were kept visible because they are the page's core. Folding the judges is an option.
- **Sources tabs: 4 to 8 screens** (South Bend 7.8, Mishawaka 6.8, county 6.8). These are the full citation lists from the shared `T.sources_body` plus long gap texts.
- South Bend and Mishawaka Overviews: 4.2. South Bend Money: 4.4.
- **Hub: 3.7 screens with JS on. With JS off it is about 6.7**, because its gaps and sources folds ship open, as on every page. The map and list alone are about 2.4.

**Charts are not at full content width.** The budget charts render at the chart system's natural width (up to 760px, in `civic/charts.py` and `money.flag_columns`). Making them span 1148px would mean changing shared chart code, so it was left.

**Not checked:** screen readers; Safari and Firefox; every look-and-theme pair on every page. Six combinations were spread across eight pages, not all 36 per page.

**The hub's saved place selects the township or city layer only.** It does not select the school layer: preselect.js uses `m.muni || m.township`.

## Old links I could not update (owned by other agents)

These still work: they land on the forwarding pages, which send the reader on. They are about 420 links in the built site.
- **`civic/offices.py` `government_page` (lines 78-84):** still `places/<id>/`, `county/`, `county/#courts`, `schools/#<id>`. This drives the office pages' "part of" links (266 links). Suggested fix: `gm.unit_page(ed, unit_id)` / `gm.unit_href`. Map `sjc-courts` to `governments/county/index.html#courts`.
- **`pages/elections_numbers.py` lines 847-862** (officeholders page office links, 157 links): suggest `governments/<id>/index.html#office-<office id>`, with the county for `sjc-courts`.
- **`who-handles-this` and `your-governments` (participate.py):** I updated `_unit_link`, `office_cell`, `_layer_href` and `YP_BROWSE`. That file is not on the do-not-edit list, so please check this was acceptable. Other links on those pages may still come from `civic/offices.py`.

## Data problems seen

- Build warnings are unchanged: 5 money unit ids with no alias (library-new-carlisle, library-walkerton and three special units); every result row's office_id is blank and derived for 1132 of 1243 contests; 2 campaign-race filing mismatches.
- `check_gov` warns about blank term starts (for example Lakeville's Dean Rouch, Roseland's Mudrovich).
- The 2027 South Bend general-fund chart shows an empty 2027 column, because only the all-funds 2027 figure exists. The budgets page shows the same.

## Open questions

1. Should the county Overview be cut further (fold the judges, or move the state delegation to a later tab)?
2. Should Sources tabs fold the citation list behind "Show all N sources"? That is a change to shared `tabs.sources_body`.
3. Should budget charts widen to content width? That is a change to the shared chart code.
4. The hub's saved place does not choose a school layer. Is that wanted?
5. **Failures in other agents' areas:** `test_wave_e_onpage` fails on `elections/margins/index.html`, which is in `ONPAGE_PAGES` but is now the elections agent's forwarding page. `test_phase6_elections` `Static.test_elections_js_contracts` failed in one earlier run (`"contest-forward"`) and passed later, so it was in progress on their side.
