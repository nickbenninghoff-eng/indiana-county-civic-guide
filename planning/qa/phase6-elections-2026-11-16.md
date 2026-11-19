# Phase 6, step 4: election pages (2026-11-16)

Built by a sub-agent from the brief "Build the Election pages". Nothing is committed. Read this file with
`planning/design-direction-2026-11-16.md` (sections 0 and 2 to 5) and `planning/qa/phase6-step1-2026-11-16.md`.

## What was built

### One page per election: `elections/<election_id>/` (all 42 rows of elections.csv)
The pages use the civic/tabs.py template, the same one the Office pages use: header, facts line, tab bar and the
`tsec` sections. Each tab has a real URL. A tab with nothing in it is not built and gets no sitemap entry.

| Tab | When | What |
|---|---|---|
| Overview `elections/<id>/` | always | Turnout as a big figure with its base (ballots / registered, who could vote: countywide, or the places that held a municipal election), the status mark, and a link to Compare: Turnout. **On the ballot**: contest count by level, each linked to its block on Contests. Uncontested count using Compare's rule ("N of the M races for local office decided inside the county had no contest", same `margin_races` code, with a computed mark). **Closest races**: the 3 smallest margins, each linked to its contest. **Elections before and after**: the previous and next election, plus the previous and next election of the same kind. **Notes from the records**: a fold. |
| Contests `elections/<id>/contests/` | when results.csv has any contest | Grouped by level: county, township, city, town, school board, state legislature, statewide (county tally only), public questions, straight-party, other. Primaries are grouped by party first (alphabetical by party name, then "On every primary ballot (no party)"), then by level. One hairline row per contest: office name linked to `offices/<office_id>/elections/` through `civic/offices.py href`; the winner and share ("Elected:", "Ahead (unofficial count):" for 2026g, "Only candidate:"); the margin or "Uncontested", "County portion only", "Yes or no" or "Not a race"; and the status mark. Under the row is a fold "Every candidate" holding the existing results bars, a link to the office's Elections tab and, on mapped elections, the race on the Map tab. Each row keeps `id="contest-<contest_id>"`. |
| Map `elections/<id>/map/` | only 2020g, 2022g, 2024g (the elections with precinct results) | The "How areas voted" layer, limited to this election's races. It reuses `civic/map.py` vote controls, legend, layer group and tables with a filtered copy of the vote payload (`election_votes`). No new geometry. The race rule, labels, palette and caveat are unchanged. The tables sit in a fold (ships open; JS closes it). `#race-<id>` opens one race, and a link goes to the full map. |
| Sources `elections/<id>/sources/` | always | `tabs.sources_body`, with this election's gaps (the gap rows that name its year). |

The facts line reads like "November 5, 2024 · General election · Turnout 54.5% · 47 contests in the guide's results".
Titles read like "2024 general election", "2023 municipal primary" and "2013 special election". The breadcrumb is
Elections › <election> › <tab>.

### Elections hub: `elections/index.html`
1. **Next election in the county.** The highlighted strip shows the dates from the calendar code and links to the
   Election calendar. Under it is "Offices on the 2027 ballot, place by place (N places, N offices): <place names>", a
   fold of one card per government with each office linked to its page. The fold ships open, so with JS off it is a
   plain list. With JS on, folds.js closes it.
   - **Saved place** (preselect conventions; `m.sure` only, so guide defaults never count): elections.js shows only the
     reader's governments, adds the usual on/off line and opens the fold. A saved place with no seat on this ballot
     gets a note instead. `#hash` wins.
   - here.js still marks the unincorporated line.
   - Below the fold are the calendar's "What's on your next ballot", "Deadlines" and "Every seat" links.
2. **Every election.** Newest first, grouped by year. Each row shows the election link, date, turnout with its source,
   contest count and status mark.
   - The 3 newest years are open. The other 36 elections sit in one fold, "Earlier elections, 2022 back to 1963 (36)",
     which ships open (JS off: the whole list).
   - A line says that before 2010 the guide has only South Bend's mayoral races.
3. **Four doors:** Compare elections (with the 608-of-981 fact), Judges & ballot questions, How elections work, Run
   for office. After them is a "Find a result" line and the two learning paths.

Page height with JS on: 1,983 px at 1280 (2.2 screens), 3,546 px at 400. With JS off it is the full plain list.

### Compare: `elections/compare/`, three real-URL tabs
| Tab | URL | Was |
|---|---|---|
| Close races | `elections/compare/index.html` | `elections/margins/` |
| Turnout | `elections/compare/turnout/index.html` | `elections/turnout/` |
| Uncontested seats and overview | `elections/compare/overview/index.html` | `elections/landscape/` |

The content is moved, not rewritten: the same builders now write to the new paths. Every id and figure is
unchanged. The tests assert 608 uncontested of 981; the turnout table has one row per election and keeps
`turnout-denominators-all`; the straight-party tables are there too.
- Each tab has a tab-template header ("Compare elections", a crumb, a facts line and the 3-tab bar), then the old
  page's own lead, badges and contents.
- The margin and turnout charts keep the accent/ink ramp; a test asserts no party classes.

### Find a result: `elections/results/index.html`
The explorer is gone (its 300 KB JSON payload and its controls). The page has four sections:
- **By election:** every election by year, linked.
- **By office:** offices grouped by level and government, each linked to its Elections tab.
- **Every contest:** the existing filterable table, in its fold, unchanged.
- **How to read results.**

| | bytes |
|---|---|
| before (fixture build, 2026-11-16) | **971,508** |
| after | **655,422** (-33%) |

**Office links kept.** The every-contest table's "Office" links (added by the Offices agent) are 1,114 links, about
105 KB or 16% of the page. They are not what bloated it; the explorer payload was. The rest of the size is the table
itself, which is behind a fold. Moving it to its own page would be the next lever (open question 1).

### Other changes
- **Calendar:** unchanged, apart from its two "Results" links, which now go to the 2026 general election page.
- **Judges & questions:** each result links to its contest on the election page. Contests not on an election page say so.
- **How it works:** unchanged, apart from its straight-party link, which now goes to Compare: Turnout.
- **Header Elections menu** (6 links): Calendar, Find a result, Compare elections, Judges & ballot questions, How
  elections work, Run for office. TOPICS leaves and MENU_LABELS point at the Compare tabs.
- **Search:** elections are indexed as a new "Election" type, with their tabs as "… › Contests" etc. Forwarding pages
  are not indexed.

## Every old URL and anchor, and where it goes
| Old | With JS | JS off | Netlify |
|---|---|---|---|
| `elections/margins/` | elections.js replaces the page with `elections/compare/` | small page: title, one line, plain link "Compare elections: Close races", `<link rel=canonical>` | `301!` to `/elections/compare/` |
| `elections/margins/#<id>` | moved.js: every id on Close races → same id there | plain link (anchor dropped) | 301 keeps the #fragment |
| `elections/turnout/` and `#<id>` | → `elections/compare/turnout/` (same ids) | plain link | `301!` |
| `elections/landscape/` and `#<id>` | → `elections/compare/overview/` (same ids). The landscape's old forwards (bands, margins table, turnout tables, `straight-<eid>` tables, cards) go to the Close races or Turnout tab that has them. | plain link | `301!` to `/elections/compare/overview/` |
| `elections/results/#contest-<id>` | elections.js `#results-forward` → `elections/<eid>/contests/#contest-<id>`, with the fold opened. `location.replace`, so Back skips it. | lands on the contest's row in the every-contest table (the id is kept) | n/a |
| `elections/results/#turnout`, `#turnout-h`, `#turnout-general*`, `#turnout-table*` | moved.js → Compare: Turnout | id not on page (top of page) | n/a |
| `elections/results/#elx-*` (explorer controls) | → `#by-election` | top of page | n/a |
| `elections/index.html#card-calendar` | → `#next` | | |
| `#card-results` | → Find a result | | |
| `#card-landscape`, `#card-margins`, `#card-turnout` | → the Compare tabs | | |
| hub `#primaries-low`, `#vacancies-low` (+`-copy`) | → how-it-works `#primaries` / `#vacancies` when the low-confidence table is not printed (fix: it pointed at a missing id) | | |
| Learning paths | "Vote smarter" stop 3 → `elections/index.html#timeline`; "Elections by the numbers" stops 1-2 → `elections/compare/turnout/#turnout`, `elections/compare/#short-answer` | | |

`tools/tests/test_phase6_elections.py::test_every_old_anchor_resolves` checks every id the hub, landscape, margins,
turnout and results pages had before this step. The ids come from
`tools/tests/fixtures/anchors_before_phase6_elections.json`, taken from the built site before any change. Each id is
either still on its page or forwarded to a built page that has it. A second test checks that every forwarding map
names only ids that left the page and only targets that exist.

`tools/site/netlify/_redirects` is new (none existed). netlify_prep.py copies it into the publish directory, and a
test checks the copy. The forwarding pages stay, for the claude.ai preview host, which has no redirects; that is why
the rules are `301!`.

## Decisions
- **civic/tabs.py: constants only, no signature change.** `TAB_ORDER` gains "contests" and "map", and `TAB_LABELS`
  gains their labels. Office pages are unaffected: they register PAGES for every key, but build.py builds only
  sitemap entries.
- **Sitemap `Entry.moved_to`** (new field, default ""). It marks forwarding pages, which search skips. The Offices
  two-click reachability test skips them (an edit to `test_phase6_offices.py`, see below).
- **`Page.canonical`** (new attribute, default None, civic/shell.py) writes `<link rel="canonical">`.
- **Folds ship open and JS closes them** (house pattern): contest rows, the hub's earlier years, the hub's ballot
  offices and the map tables.
- **Saved place on the hub** reuses the `explorer` slot kind, now handled by elections.js. Only certain matches count.
- **Map tab:** `civic/map.py` gains `election_votes` and `election_vote_map` (appended), and map_votes.js gains
  `onlyElection` (when the root has `data-vote-eid`). The full map page is unchanged: same payload, same markup, no
  `data-vote-eid`.
- **Straight-party "contest"** shows its party marks ("Straight-party marks: …", "Not a race"), with no winner.
- **Cross-county contests** (statewide, legislative districts crossing the county line) show "County tally" with no
  winner, as before.

## Files
- **New:**
  - `tools/site/civic/election_pages.py`
  - `tools/site/pages/election_pages.py`
  - `tools/site/netlify/_redirects`
  - `tools/tests/test_phase6_elections.py`
  - `tools/tests/fixtures/anchors_before_phase6_elections.json`
- **Mine, edited:**
  - `pages/elections.py`
  - `pages/elections_numbers.py`
  - `static/js/elections.js` (rewritten)
  - `static/css/elections.css` (appended)
- **Shared, small additive edits:**
  - `civic/sitemap.py`: moved_to, hub/results entries, election entries, nav, TOPICS, MENU_LABELS, PATHS
  - `civic/shell.py`: canonical; ONPAGE_PAGES gains compare
  - `civic/search.py`: Election types
  - `static/js/search.js`: rank for the two new types
  - `netlify_prep.py`: copies `_redirects`
  - `civic/tabs.py`: constants only
  - `civic/map.py`: appended
  - `static/js/map_votes.js`: additive
- **Tests updated deliberately:**
  - `test_wave_b_numbers` (paths → Compare; old pages checked through their forwarding maps; race links → election pages)
  - `test_page_organization` (paths → Compare)
  - `test_wave_a_patterns` (explorer payload → results-forward)
  - `test_wave_c_judges` (contest links)
  - `test_wave_d_nav` ("Compare elections" label; four doors)
  - `test_wave_e_preselect` (hub "explorer" slot; hub ballot layers instead of the explorer payload)
  - `test_here_money_results` (MARGINS → compare)
  - `test_debug_pass` (browser: old #contest- link lands on the election page; Back skips the forwarder)
  - `test_phase6_offices`: moved_to skip in two-click reachability, and the explorer-payload lines. This is the
    Offices agent's file; the edit is deliberate and limited to those two spots.

## Verification
- `python -P -E tools/site/build.py --edition st-joseph --check`: **PASSED**, no BUILD FAILED (1,013 pages). An
  earlier run had BUILD FAILED, with 25 places/county/schools builders raising "governments/... is not in
  civic/sitemap.py". That was the Governments agent mid-change; it cleared on re-run without any edit from me.
- `python -P -E tools/check_gov.py`: **0 errors** (23 warnings, all pre-existing term/date warnings).
- `python -P -E -m unittest discover -s tools/tests`: **NOT OK**. Ran 486; 27 failures and 12 errors, all in the
  places, county and schools pages that the Governments agent is moving to `governments/`. None of them is in an
  election page:
  - test_map_navigation ×7
  - test_place_template ×11
  - test_wave_c_batch7 ×9 (county/school)
  - test_wave_a_patterns: the rail and related-items tests on places/county
  - test_wave_d_nav: current_page_marked and section_hubs expect `places/index.html`
  - test_wave_e_onpage: county toc
  - test_wave_e_preselect: county slot, county map, schools keys
  - test_phase6_offices.test_cross_links_to_office_pages: `places/south-bend/` no longer links the mayor's office.
    The election part of that test was updated and passes.

  Per the brief I did not touch those files. Every election test passes, including the new
  `test_phase6_elections.py` (24 tests) and the updated wave tests. The baseline before this step was 442 tests OK.

## Browser QA (own Chromium via Python Playwright against http://localhost:8787; the shared MCP browser was used once)
- **Matrix:**
  - 12 pages: hub, 2024g Overview, Contests and Map, 2023p Contests, 2026g Contests, 2013s Overview, the three Compare
    tabs, Find a result, and old margins.
  - 1280 and 400 px × 3 looks × light/dark = 144 loads.
  - Result: no horizontal overflow, no console errors, looks applied.
- **Forwarding:**
  - With JS: old margins, turnout and landscape (bare and with anchors), results `#contest-` (7 samples across
    2010-2026), results `#turnout-general` and hub `#card-margins` each landed on the right page with the target
    present and visible.
  - With JS off: the forwarding pages show the plain link, and results `#contest-` lands on the row.
- **Keyboard on the 2024g Map tab:** 70 Tab presses. Focus stays visible and never falls to `<body>` (25 stops in the
  map: layer buttons, race select, year, area buttons, the race list fold, the SVG and every area link).
- `#race-us-house-2024` selects that race.
- **Screenshots** in `planning/qa/phase6-shots/` (elec-*.png): hub (1280 ballot light, 400 wayfinding dark, JS off),
  2024g overview/contests/map, 2023p contests 400, 2026g contests dark, 2013s 400, three Compare tabs, Find a result,
  old margins JS off.

## Not verified
- Netlify redirects on a real Netlify deploy (no deploy; only the copy step is tested).
- The saved-place hub view in a browser with a real saved place. It is covered by the markup tests and the
  elections.js contract test, not clicked through.
- Screen reader pass.
- After the last layout changes (hub ballot fold, map tables fold), the hub (1280 and 400 px) and 2024g map shots were
  retaken. A second 36-load matrix on the hub, 2024g map and Find a result found no overflow and no errors. The other
  shots predate those two changes. Hub height is now 1,983 px at 1280 (2.2 screens) and 3,546 px at 400.

## Data problems seen (not edited; no edits under data/)
- **2024g:** 11 school-board contests show "Winner not recorded in the guide's data" and "No margin: seat count not in
  data" (results.csv has no `vote_for` or winner for them). The same applies to 2026g LaVille, John Glenn Lincoln
  Township and New Prairie At-Large / District 2.
- **2024g:** 8 of the 30 local races can't be measured (a seat count or vote count is missing).
- **2024g:** "Public Question #1 (wording not captured)". **2026g:** two questions, "wording not captured".
- **2026g retention:** two judges' court is "not stated in the canvass".
- **2023p Walkerton Town Council Ward 4 (R):** "Tied on votes", and the record marks Kyle Norris elected.
- **results.csv:** office_id is blank on every row; it is derived from contest_id for 1,132 of 1,243 contests (a
  build warning). Contests without a derived office get no office link.
- **how-it-works:** the "primaries-low" table is no longer printed (its rule is no longer low confidence), but the
  hub's forwarding map still sent its id there. Now fixed (see above).

## Open questions
1. Find a result is still 655 KB, almost all of it the every-contest table. Should the table move to its own page (or
   to data/results/, which already has the CSV)?
2. Municipal elections' turnout counts only the places that held them. The overview says so, but should the hub
   timeline show the base next to the figure?
3. `landing.py` (not my file) still links `elections/margins/`. The forwarding page and the 301 cover it, but the owner
   may want to point it at `elections/compare/`.
