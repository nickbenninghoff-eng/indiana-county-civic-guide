# Budgets money map and follow-on maps: build and QA (2026-11-08)

Nothing committed. Roadmap.md and docs/session-handoff.md not touched. tools/res_main.py and tools/build_money.py not run.

Sections: 1 budgets money map; 2 places index map; 3 Schools page map; 4 Results-to-map race links; 5 community indicator maps; 6 final results, files and decisions.

## 1. Budgets page money map (money/budgets/index.html, new section 1 "Money map: spending per resident")

### What was built
- New section at the top of the budgets page (old sections 1-6 renumbered 2-7; anchors unchanged; TOC gets "Money map").
- County line above the map: county government counted spending, per resident (county 2020 Census count), counted income, link to the county page's Money in and money out block (`county/index.html#money-county`). Not a map layer.
- Map with three tabs (Cities and towns, Townships, School corporations), one layer at a time, the same component as map/index.html:
  - Shading: counted spending per resident (latest spending year per unit; residents = 2020 Census count of that geography). One teal ramp (the --cm-city hue), 5 shades, breaks computed per layer, legend per layer with a title, the area count per step, and "No data" (hatched) where needed. Places layer: land outside cities and towns drawn as a neutral background ("Outside any city or town (not shaded)").
  - Side panel on hover/focus (keeps the last area after the pointer leaves, same as the other map): name and type; year (school years labelled "2025-26 school year"; split if the income year differs); counted income; counted spending; spending per resident with the population used; money passed through or moved between funds (in and out, one line); data status (computed); top 3 income sources and top 3 spending purposes as ranked bars with % and amount; the year's caveats from spending.py (held-back income year with "Income shown: ...", school-year file note, exclusions-reviewed-by-name note, borrowing not counted); "See the full breakdown" link.
  - Click (desktop) / Enter (keyboard) opens that government's Money in and money out block: `places/<id>/index.html#money-<id>` (cities, towns, townships) or `schools/index.html#money-<id>` (school corporations). Those `money-<id>` anchors already existed (civic/spending.py block id); no new anchors needed. Touch: first tap selects, second opens (map.js, unchanged logic).
  - The map does not read or write the URL hash on this page (`data-hash="off"`), so links like `money/budgets/index.html#south-bend` keep working.
- Method note under the map (township figure divided by whole township population, including city residents; school districts by district population, residents not students, whole district even where it extends past the county line; breaks per layer, compare within a layer; a figure equal to a break falls in the higher step), cited to the Census and AFR sources.
- Tables under the map (present with or without JS): one per layer (Area, Type, Year, Counted income, Counted spending, Residents (2020 Census), Spending per resident, Breakdown link), then "Governments with no boundary on the map": the county, the 4 libraries and the 5 special units (airport, redevelopment authority, regional water and sewer, Transpo, solid waste), per resident only for the county.

### Breaks per layer (current data, 2025 / 2025-26 school year)
| Layer | Breaks | Steps (count) | Shades used |
|---|---|---|---|
| Cities and towns | under $1,000 / $1,000-3,000 / $3,000-5,000 / $5,000-7,000 / $7,000+ | 2, 2, 2, 2, 1 | 1-5 |
| Townships | under $80 / $80-200 / $200-350 / $350-700 / $700+ | 4, 2, 3, 3, 1 | 1-5 |
| School corporations | under $2,000 / $2,000-2,500 / $2,500-2,750 / $2,750+ ; no data 1 | 1, 1, 1, 2 | 1, 2, 4, 5 |

Method: natural breaks (Fisher-Jenks, exact) into min(5, distinct-1) classes (5+ values), each break moved to the roundest whole-dollar figure inside the gap between classes (nearest the gap's middle). Fewer classes use spread-out shades (4 classes -> shades 1,2,4,5) so neighbors stay far apart.

Per-resident values: towns/cities Indian Village $459, Osceola $820, Lakeville $1,299, Roseland $1,644, Mishawaka $4,035, South Bend $4,216, Walkerton $5,330, New Carlisle $5,950, North Liberty $7,877. Townships Greene $24, German $47, Harris $47, Lincoln $64, Penn $87, Portage $112, Warren $217, Centre $265, Madison $310, Liberty $372, Union $388, Clay $447, Olive $905. Schools SBCSC $1,741, Union-North (LaVille) $2,263, Mishawaka $2,627, PHM $2,836, John Glenn $2,885. County $998.

### Population source
`indicator_values.csv`, indicator `pop_census_2020` (vintage "2020 Census", source COM-045): 29 geographies (county, 2 places, 7 towns, 6 school districts, 13 county subdivisions). Matched to each map shape by the shape's own Census name (exact, before the first comma), so all 28 mapped areas resolve, including Mishawaka School City and Union-North.

### Units without data
- New Prairie United School Corporation: on the map, no money rows in spending_breakdowns.csv -> hatched "No data", panel says so, click opens its Schools page section (`schools/index.html#new-prairie`).
- Every other mapped area has money data and a population. Every money unit is either on the map or in the no-boundary table (unit test).

### Colors (validated)
Light ramp #76c4b6 #43a798 #1a887a #00695d #004940; dark #20584f #25786c #33998a #60baac #92dbce (OKLCH hue 182, tokens --cm-mm-1..5 in static/css/money_map.css with light + both dark blocks).
- Adjacent-step OKLab dE (x100): light 10.1 / 10.0 / 9.9 / 10.5; dark 10.2 / 10.2 / 10.9 / 11.1. Lightness monotone.
- Lightest light step vs white surface 2.03:1; darkest dark step vs the three dark surfaces (#1b1a17, #16161a, #1a1918) 2.13-2.21:1. dataviz `validate_palette.js --ordinal` passes for light and for each dark surface.
- Distance from party colors: >= 16.2 from --party-d, >= 25 from --party-r (both modes).
- In the browser, computed fills, legend keys and the map background were read in all 12 combinations (2 widths x light/dark x 3 looks); every look uses surface #ffffff in light and the validated dark surfaces, and the cm-mm tokens are not redefined per look.
- Dark mode runs from near-background (least) to bright (most): "more" is always farther from the background. Nick: the brief said "darker = more"; this is the dark-mode equivalent.

### Code changes
- `tools/site/civic/money_map.py` (new): computation (`summarize_rows`, `per_resident`, `census_population`, `money_map_data`) and rendering (`money_map`, `county_figure`, `method_note`, `money_map_tables`). The break and legend code later moved to `civic/shading.py` (section 5) and is re-exported here; the budgets page HTML was byte-identical before and after that move.
- Not changed: `civic/spending.py` (another session was editing it and `spending_breakdowns.csv` at the same time; the money map only imports its helpers).
- `tools/site/civic/map.py`: the layer-drawing loop of `boundary_map` moved into a shared `government_layers(page, ed, shapes, default_layer, area, back_cls=...)`; `boundary_map` calls it. Output is byte-identical (map/index.html and index.html diffed against a pre-change build: identical).
- `tools/site/static/js/map.js`: optional panel fields `bars` (ranked share bars), `cav` (caveat lines), `open` (link label); `data-hash="off"` opt-out. Existing maps send none of these, so they behave as before.
- `tools/site/static/css/money_map.css` (new).
- `tools/site/pages/money.py`: `_money_map_section`, TOC entry, section renumbering.
- `tools/tests/test_money_map.py` (new, 18 tests).

### Results
- Build: `python -P -E tools/site/build.py --edition st-joseph --check` -> PASSED (60 pages).
- Tests: `python -P -E -m unittest discover -s tools/tests` -> 37 tests OK.
- Browser (Playwright), 1280 and 400 px x light/dark x Ballot/Line map/Wayfinding (12 runs): panel content correct on hover; panel keeps the last area after the pointer leaves; legend per layer switches with the tab; desktop click lands on `places/mishawaka/index.html#money-mishawaka` and `schools/index.html#money-phm` (target scrolls into view after the page's smooth scroll); keyboard Tab focuses an area (focus outline + panel), Enter opens it; touch (400 px, hasTouch): first tap selects (URL unchanged, panel shows), second tap opens `places/south-bend/index.html#money-south-bend`; no horizontal overflow at 400 px; no console errors (only the site-wide favicon 404). No-JS: 28 area links, all 4 tables present, default layer shown, no overflow.
- Regression: map/index.html and index.html HTML byte-identical to before. In the browser: map page hash layers (#townships start, #schools/#votes written), panel facts and "Open page", last-area-stays, "How areas voted" loads and shades, click opens place page; landing map hover panel, tab switch leaves the hash alone, click picks the place (here.js) without navigating. No console errors.

### For Nick to decide
1. School population is all district residents (Census school district count), not students; districts extending past the county line (John Glenn, Union-North/LaVille, New Prairie) use the whole district population because the spending covers the whole district. Per-student would need enrollment (another agent is adding enrollment data).
2. Pre-existing bug found, not fixed: the boundary map's panel and list on map/index.html and the landing page show "Population: not in the guide's data yet" for School City of Mishawaka and LaVille (Union-North) although the 2020 Census counts are in the data (civic/map.py `population()` matches by unit name, and those unit names differ from the Census names). Fixing it changes the existing map's output, so it was left for your call; the money map matches by the shape's Census name instead.
3. Data moved under me: during this session spending_breakdowns.csv was regenerated by other work, and SBCSC's 2025 income is no longer held back, so the "held" caveat currently shows for no unit (the logic and a unit test for it remain).
4. Olive Township ($905) is the only area in the top township step; the breaks are data-driven per layer and will move when the data does.

## 2. Places index map (places/index.html)

- New section "On the map" (unnumbered; TOC "Map") above the Cities / Towns / Townships lists: the boundary map with the Cities and towns (default) and Townships tabs only. Panel = the existing unit facts from civic/map.py `unit_facts` (population, elected seats, head official, party mix, latest adopted budget). Click / Enter / second tap opens `places/<id>/index.html`. Type colors as on the full map; a note under the map (color = type of government, never party; every city and town also lies in a township) links to the full map. The page's #anchors are left alone (`data-hash="off"`).
- Code: new `civic/map.py embedded_map(...)` (layer subset, hash off; a one-layer map hides its tab bar via `.cmap-single`), `facts_area()` and `LEGEND_ITEMS` factored out of `boundary_map` (output byte-identical), `government_layers(..., only=)`; `static/css/map_embed.css` (new).
- QA (12 runs: 1280/400 x light/dark x 3 looks): panel on hover, last area stays, hash untouched, Enter opens `places/osceola/index.html` and (Townships tab) `places/harris-township/index.html`, touch first tap selects / second opens, no overflow, no console errors.

## 3. Schools page map (schools/index.html)

- In "Corporations at a glance", above the table: the map with the School corporations layer only (tab bar hidden). Panel: board seats; how they are chosen (grouped from offices.csv with the page's own `_how_elected`, e.g. PHM "All voters in the corporation: 1 seat; Voters in Harris Township: 2 seats; Voters in Madison Township: 1 seat; Voters in Penn Township: 3 seats"); current members in the guide's data; next election; the partly-outside-the-county note. Same counts as the table. Click / Enter / second tap goes to the district's section on the page (`#<id>`; `#phm` lands at the top under the sticky header).
- QA (12 runs): tab bar hidden, panel content, last area stays, `schools/index.html#phm` reached by Enter and by second tap, no overflow, no console errors.

## 4. Results page to map race links (elections/results/index.html)

- Every contest card in the Results explorer whose race is on the "How areas voted" layer gets "See this race by area on the map", linking to `map/index.html#race-<race id>`. 94 of the 102 mapped races have a results.csv contest (all but the 8 federal races, which results.csv doesn't have). Each linked contest has exactly one race, from the same election (tests).
- Bridge between the two id schemes: `civic/map.py results_contest_ids / race_by_contest` (direct id; statewide offices `state-...`; townships `<name>-township-<office>`; towns `<town>-council-at-large` or `-council-ward-N`).
- Address format `#race-<id>`: the brief suggested `#votes&race=<id>`, but the checker allows only letters, digits and hyphens in a fragment and requires the target id to exist. The map page's "Every race on the map" table now carries `id="race-<id>"` on each race name, so without JavaScript the link lands on that race's county-total row. With JavaScript, map.js opens the votes layer and map_votes.js selects the race when its data loads and scrolls the map into view.
- Behavior change on map/index.html: picking a race now writes `#race-<id>` to the address (replaceState, no history entry), so a reload or shared link reopens it. `#cities`, `#townships`, `#schools`, `#votes` and no hash behave as before (checked). An unknown race id falls back to the default race (`#votes`). The only change to the map page's HTML is the 102 race anchors (diffed).
- Not handled: changing the hash on an already-open map page (same-document navigation) does not switch the race; the map never reacted to hash changes.
- QA: the 2024 filter shows 11 linked cards of 30; the County Coroner card opens the map on that race with the map at the top; direct loads of a township board, a Walkerton ward, State Senate 9 2020 and Governor 2020 open the right race at 400 px; no overflow; no console errors. Tests: `tools/tests/test_map_links.py` (4).

## 5. Community indicator maps (community/people/, community/income-and-work/, community/housing-and-education/)

- New last section on each page, "On the map: townships, cities and towns" (people section 7, income section 6, housing section 4; TOC "On the map"): the map with Cities and towns + Townships, a "Shade by" picker of the indicators already in that page's township and place tables, and a legend per indicator and layer.
  - people: total population, median age, foreign-born %, the 8 race and Hispanic origin shares;
  - income and work: median household income, per-capita income, poverty %, child poverty %;
  - housing and education: owner-occupied %, median home value, median gross rent, rent-burdened %, bachelor's or higher %.
- Shading: the same teal ramp and rounded natural breaks as the money map (`civic/shading.py`, now shared), computed separately for each indicator and each layer (percentages and ages may break at one decimal via `min_unit=0.1`; dollars and counts at whole units). Estimates with a CV above 30% are never shaded (hatched, "Not shaded: no estimate, or margin of error too large (CV above 30%)"), matching the page rule that unreliable estimates are never used in charts.
- Panel: the area's whole row for the page's indicators, each "estimate ± MOE", unreliable ones flagged with their CV and "not shaded"; the shaded indicator's row is marked; the ACS vintage and Census area name; "Open its page" to `places/<id>/index.html#context`. Under the map: the method note, the page's existing CV legend (`cv_legend()`), and the overlap note ("every city and town lies inside a township ... Don't add areas together, and compare shades only within one layer").
- Data: indicator_values.csv rows for the latest ACS vintage, matched to each shape by geography type and Census name. The Cities and towns layer includes the 7 towns, which the page tables don't list (the data has them); most town estimates are unreliable and stay hatched.
- Code: `civic/shading.py` (new: breaks, `classify`, `shade_legend`, `shade_class`; `round_between`/`class_breaks` gained `min_unit`, default unchanged); `pages/community_history.py indicator_map_section`; `static/js/indicator_map.js` (new); map.js: optional `fk` keys + `data-lead` mark the shaded row, and a `cmap-refresh` event redraws the panel. CSS in `static/css/money_map.css`.
- QA (12 runs x 3 pages): picker visible, legend switches with the indicator and the layer, area classes change, the panel marks the picked indicator (and re-marks after a change), Walkerton click / second tap opens `places/walkerton/index.html#context`, no overflow at 400 px, no console errors.

## 6. Final results, files, decisions

- Build `python -P -E tools/site/build.py --edition st-joseph --check`: PASSED (60 pages), no BUILD FAILED.
- Tests `python -P -E -m unittest discover -s tools/tests`: 49 OK (18 money map + 4 map links + the existing spending tests + another session's new assessed-value tests; one of those failed once mid-session while that session was regenerating its CSV, then passed).
- Regression: index.html byte-identical to the pre-change build; map/index.html identical except the 102 `race-<id>` anchors; browser checks of the full map (layers, hash, panel, votes layer, click) and the landing map (hover panel, tab switch leaves the hash alone, click picks the place) after the last JS change, light and dark: no console errors.

Files changed or added (all uncommitted):
- `tools/site/civic/map.py` (government_layers, facts_area, LEGEND_ITEMS, embedded_map, shade_defs, results_contest_ids, race_by_contest, race anchors in vote_tables)
- `tools/site/civic/money_map.py` (new), `tools/site/civic/shading.py` (new)
- `tools/site/pages/money.py`, `tools/site/pages/places.py`, `tools/site/pages/elections.py`, `tools/site/pages/community_history.py`
- `tools/site/static/js/map.js`, `tools/site/static/js/map_votes.js`, `tools/site/static/js/elections.js`, `tools/site/static/js/indicator_map.js` (new)
- `tools/site/static/css/money_map.css` (new), `tools/site/static/css/map_embed.css` (new), `tools/site/static/css/elections.css` (one rule)
- `tools/tests/test_money_map.py` (new), `tools/tests/test_map_links.py` (new)
- `tools/site/README.md` (layout rows for the new modules)
- this report

For Nick to decide (all sections):
1. School "per resident" = all district residents, not students; per-student needs enrollment (another session is adding it).
2. Existing map bug left as is: the full map, the landing map and the places-index panel show "Population: not in the guide's data yet" for School City of Mishawaka and LaVille (Union-North), because civic/map.py `population()` matches by unit name. Fixing it changes the existing map's output.
3. The dark-mode ramp runs from near the background to bright (more = farther from the background), not literally darker.
4. Race links use `#race-<id>` instead of `#votes&race=<id>` (checker rule), and the map now keeps the picked race in the address.
5. The indicator maps include the 7 towns though the community tables list only the two cities; say if they should be left out (most town estimates are unreliable and hatched).
6. The race and Hispanic origin shares are offered as shading on the people page (they are in that page's township table). The page's framing rule keeps demographics away from election results, and these maps have no votes layer, but say if you'd rather not shade by race at all.

---

# Round 2 (2026-11-08): population fix and the data agent's new money data

Rules unchanged: nothing committed; Roadmap.md and docs/session-handoff.md untouched; res_main.py, build_money.py and build_indicator_values.py never run; no data CSV edited (the only gap-row changes are in page code, see 7.5).

## 7. What changed, by page

### 7.1 Map population (item A), `civic/map.py`
- `population()` now matches the unit's own map shape by its Census name (`_shape_names`, `SHAPE_GEO_TYPES`; exact match before the first comma, per layer geo type), and falls back to the old name match only for units with no shape.
- Checked every area on every layer (places, townships, school districts: 28 areas): all have a 2020 Census count and an ACS estimate. Output changed only for School City of Mishawaka (30,799 census; ACS 30,258 ±1,129) and LaVille / Union-North (7,532; ACS 7,507 ±24), on index.html and map/index.html (they said "not in the guide's data yet"). Test: `MapPopulation` in `tools/tests/test_tax_base_schools.py`.
- People page indicator map: RACE_IDS stay removed (coordinator's change kept); the 7 towns stay on the community maps.

### 7.2 Budgets page (money/budgets/index.html), `pages/money.py`
- Section 6 "How the tax base shapes budgets": new block "The tax base: certified assessed value". It has a 2020-2026 line (county, South Bend, Mishawaka) and four 2026 bar charts by unit (county and cities; towns; townships; school corporations, libraries and special units). Only `dlgf_certified` rows are used.
  - The four cross-county corporations (John Glenn, LaVille, New Prairie, PHM) carry " *" and the note "St. Joseph County part only ... the other county's part is not included".
  - A bar's tip says when a unit levies on the same value as another: the airport and solid waste district share the county's value; New Prairie, the New Carlisle library and the fire territory share Olive's; LaVille shares Union's.
  - The Gateway estimates are mentioned once, without numbers, as "the units' own estimates ... the guide does not chart them".
  - The old "does not yet have reliable assessed values" sentence now reads "does not yet have certified assessed values before 2020, or the dollar amount of tax-cap credits ...".
  - The rates line's subtitle now uses the rate file's own years (2012-2026) instead of the budget file's (2012-2027).
- Section 3 "Per resident": new third chart "Certified assessed value per resident, 2026" (county, both cities, 13 townships). It divides the 2026 certified AV by the ACS 2020-2024 `Money.population`, with a computed badge. The note says the county covers everyone and townships include their cities and towns. Part-only units are excluded by rule.
- Pre-existing bug fixed in the same section: both per-resident charts were EMPTY and titled "2027", in the pre-session build too.
  - Cause: the year was the budget file's latest year, and South Bend's 2027 ordinance is the only 2027 figure.
  - Fix: the year is now `comparison_year()`, the latest year that most of the compared units have figures for (2026).
- South Bend all-funds chart: the legend now reads "Adopted: Gateway state budget file, 2012-2023; council budget ordinance, 2026-2027", plus the news series.
  - Each column's tip names its source.
  - The note keeps the Gateway series' shared sentence again; it had been dropped once the ordinance series became a second primary series.
  - The labels come from `_source_label()`: MON-001 rows are Gateway, a series id with "ordinance" is a council budget ordinance, anything else is "the unit's own budget document".
- `BASIS["amended_all_funds"] = ("Amended budget, all funds (later financial report)", ...)`. The Other reported figures table shows this label; no raw key is left.
- Debt: the paragraph under the 2024 chart now lists both city-reported figures. They are picked by `debt_type` ("Total debt outstanding as of <date> (<source>)") and sorted by date, not by file order.
  - The text: "$298.7M as of January 1, 2026 (city monthly financial report: civil city and Redevelopment Commission); roughly $280.7M as of September 4, 2026 (city budget page)".
  - Each figure has its badge and source, and the paragraph says they are "not on the chart and not added together".
  - "roughly" comes from the row's note saying "rounded".
- Debt chart labels: long unit names were clipped off the left edge (pre-existing). The chart now uses `chart_label()`: it drops the parenthetical, shortens "Corporation" to "Corp." and removes "St. Joseph County" from special units. The tip keeps the full name.
- Budgets money map panel (`civic/money_map.py`): new facts after "Data status":
  - "Tax base (certified net assessed value)", with the part-only note.
  - "Tax base per resident", divided by the same 2020 Census count as spending per resident; left out for part-only units.
  - School districts also get "Enrollment, school year 2025-26" and "Spending per student, calendar year 2025 ... (state median ...); total spending divided by average daily membership; not classroom spending; calendar year, not school year".
  - Units with no money-in/out rows (New Prairie) still get these facts.

### 7.3 Place pages (all 23) and county page
- `_budget_block` (places.py) and the county "Money in and money out" section now have one "Tax base:" paragraph each, with a badge and both years' sources. Example: "Tax base: $4,396,041,441 certified net assessed value for 2026 ($2.73 billion in 2020, +61%), from the state's certified budget order (fund 0101 General). Property taxes are levied on this value."
- The county's line adds "It covers all property in the county, inside the cities and towns too."
- Places with no budget rows still get the line.

### 7.4 Schools page (schools/index.html)
- Each corporation's "Superintendent, budget and enrollment" list now has:
  - Enrollment, e.g. "12,851 in school year 2025-26, down 36% from 20,156 in 2011-12. Whole corporation, pre-kindergarten through grade 12 plus adult students ..." (official, MON-075).
  - Spending per student, e.g. "$24,601 in calendar year 2025 (state median $17,287). Total spending divided by average daily membership; not classroom spending; calendar year, not school year." (official, MON-076).
  - The Tax base line, with the part-only sentence for the four cross-county corporations.
  - A small line chart, "Students enrolled, by school year" (2011-12 to 2025-26).
- Budgets are never divided by enrollment.
- Schools map panel: the same enrollment and spending-per-student facts follow the board facts.
- New Prairie is not in derived/unit_id_aliases.csv, so `tax_base.money_id()` maps it. EXTRA_UNIT_IDS moved to civic/tax_base.py, and money.py now imports it from there.

### 7.5 Community housing and education page
- The text now reads: "Other attainment levels (high school, some college) are not in the guide's data yet. Each school corporation's enrollment and spending per student are on the Schools page."
- Page gap rows (in page code, not a CSV):
  - The attainment gap is narrowed to "Educational attainment below the bachelor's level, and the survey count of residents in school". It says the IDOE enrollment is on the Schools page and that the ACS count of residents in school is a different measure.
  - The "School-district indicators (ACS school districts, SAIPE child poverty)" row was stale: indicator_values.csv has 12 rows for each ACS indicator for the school districts. It is narrowed to "SAIPE school-district poverty estimates".
  - The only CSV gap rows on this topic (gaps_money.csv lines 8 and 12) were already updated by the data agent and were not touched.

### 7.6 tools/check_money.py
- Added:
  - table-only bases `dlgf_certified` and `amended_all_funds`, plus a check that they never have a series_break row;
  - kind `amended`;
  - budget years up to next calendar year (`MAX_BUDGET_YEAR = today.year + 1`, so 2027 now; it won't go stale);
  - rate kinds `certified_unit_rate`, `certified_district_rate` and `certified_district_unit_rate`;
  - a certified rate of exactly 0, allowed only when the row's note says "levy $0" (Indian Village and the solid waste district, 2025 and 2026);
  - cf_state years up to the current year.
- Nothing else was loosened.
- Result: **0 errors** ("OK: all rows parse ..."), down from 613. It still prints 36 year-over-year jumps over 40%. These are informational (the site lists them under Gaps), not errors.

## 8. Round 2 checks

- Build `--check`: PASSED (60 pages), no BUILD FAILED.
- Tests: 67 OK. The new `tools/tests/test_tax_base_schools.py` has 18 tests: tax base helpers and data, the part-only rule for cross-county units, money_id including New Prairie, school stats per corporation, the median from the same vintage, the caption in the panel facts, every mapped area's population, the BASIS label, source labels, the comparison year, AV per resident leaving out part-only units, and later debt rows picked by type and date.
- Pages changed since the pre-round-2 build:
  - budgets, schools, county, and community housing and education;
  - all 23 place pages (the tax base line, and sources renumbered);
  - index.html and map/index.html (population only).
- Browser (localhost:8787): 1280 and 400 px x light/dark x ballot/line/wayfinding, on these pages: budgets, South Bend, Lakeville, Centre Township, county, schools, housing and education, landing, full map.
  - No console errors and no horizontal overflow anywhere.
  - Every tax base line is present and inside the viewport.
  - No clipped or overlapping chart text in the new charts.
  - Budgets map panel at 400 px with touch (light and dark): shows the new facts for South Bend Community School Corporation.
  - Schools map panel (hover at 1280, and at 400): shows enrollment and spending per student.
  - Screenshots: `.playwright-mcp/r2-*.png` (gitignored).
- Still there, not new:
  - On line charts the "$0"/"0" y tick touches the first x label. rates-over-time had this before; the new av-over-time and enrollment charts share it.
  - Bar chart text is small at 400 px, because every hbar scales down from 620 px.

## 9. Files (round 2, all uncommitted)

- New: `tools/site/civic/tax_base.py`, `tools/site/civic/school_stats.py`, `tools/tests/test_tax_base_schools.py`
- Changed: `tools/site/civic/map.py` (population), `tools/site/civic/money_map.py` (panel facts), `tools/site/pages/money.py`, `tools/site/pages/places.py`, `tools/site/pages/county.py`, `tools/site/pages/community_history.py`, `tools/check_money.py`, `tools/site/README.md` (two module rows), this report.

## 10. For Nick (round 2)

1. The per-resident charts on the budgets page had been empty since the 2027 South Bend ordinance row was added. They are fixed and now compare 2026.
   - Watch for anything else that treats the budget file's latest year as every unit's latest year.
   - The unit charts now show an empty 2027 column for every unit except South Bend. I left that as an honest "no figure yet".
2. The two population bases are on purpose.
   - The budgets page's per-resident charts use the ACS 2020-2024 estimate, as its existing charts do.
   - The map panel uses the 2020 Census count, as its spending per resident does.
   - So the same AV gives slightly different per-resident numbers (South Bend: $42,645 on the page, $42,493 in the panel).
3. Enrollment and spending per student cover the whole corporation, but the four cross-county corporations' tax base is the St. Joseph County part only. Both are labelled, but one should not be divided by the other.
4. Not done (optional in the data agent's hooks); say if you want any of them:
   - a "rate x AV = levy" example on the tax bill page;
   - a per-unit AV line inside each unit's budget block;
   - a South Bend "Debt:" line on its place page;
   - a 2025 per-student bar chart of the six corporations.
5. LaVille (Union-North) still has no budget rows. Its Schools entry says "Budget: not in the guide's data yet" next to its tax base, enrollment and spending per student.
