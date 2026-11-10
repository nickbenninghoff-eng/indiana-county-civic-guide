# Debug pass, 2026-11-09

Nick asked for agents "to make sure everything is working correctly" and chose "fix everything" (he reviews the diff).
This pass looked for functional bugs in the built site (site/st-joseph, 113 pages) and the generator (tools/site).
Nothing committed, pushed or deployed. Scripts used are in the session scratchpad (`debug/`); they are not part of the
repo.

## How it was checked

| Check | What | Result |
|---|---|---|
| Crawl, 12 configurations | Every page in headless Chromium: console errors and warnings, page errors, failed requests (404s, JSON/GeoJSON), every link on the page after the scripts ran (so links the scripts write, like the "You are here" bar, are included) checked against the target file and its ids and `#moved-anchors`, buttons without a name, `aria-expanded` against what it controls, page overflow. Configurations: no saved place; South Bend with township and school chosen; Mishawaka with defaults only; unincorporated Harris Township; old format without `set` (Walkerton); corrupt JSON plus a bogus look and theme; unknown place id with a number for the township; unknown township and school; Line look in dark; Wayfinding in light; JavaScript off; 400 px phone width | 0 problems in every configuration (one false overflow on money/campaigns/how-it-works at 400 px: `scrollWidth` counts the wide table, but `#site` clips it and the page cannot scroll sideways) |
| JS off, 400 px | Content hidden without JS (hidden attribute, display:none) | Only controls that need JS (search box, look switch, filters, map tabs, legends of non-default layers, the office sub-label in grouped campaign tables, which the group heading already states). Nothing important hidden |
| Every linked anchor | Each of the 4,871 `#fragment` targets linked anywhere on the site (all non-source ids, plus samples of `#src-` and `#contest-`), loaded fresh: after the scripts, is the target visible and on screen (folds, pick_one items, the results explorer's card)? Run at 1280 and 400 px | 1 of 1,936 at 1280 px: `map/index.html#list-votes` (see "Left"). At 400 px 2 of 1,896: the same, and `index.html#paths`, which was off by 426 px only under the 6-tab parallel load; loaded alone it settles at the nav line (64 px) within 300 ms (anchor_landing.js) |
| Interaction scripts | Place picker (choose, township, school, clear, school-before-place, landing map as picker); nav menus (Enter, Escape returns focus, one open at a time, outside click, phone width); search (options, arrows, `aria-activedescendant`, Escape, Enter, odd input); source search; every table filter (no-match, restore, every select option, every sort); looks and theme (pressed state, storage, persistence); pick_one (hash into an item, hashchange, Back/Forward, Show all, map clicks); every saved-place preselect line on 12 pages with 4 saved places (button applies and undoes, page text restored); boundary and vote map (keyboard focus, Enter drills, Back, every level/office/district/year) | Bugs 2, 3, 4 below; everything else passed |
| Tab walk | Tab through 16 pages with a saved place: every stop visible and named, no loop, reaches the footer | Bug 1 below |
| Build twice | Snapshot of tools/site + data built under different `PYTHONHASHSEED` values, `diff -r` | Bug 5 below; identical after the fix (seeds 1, 2, 3) |
| Blank-cell fuzz | In the snapshot, blank cells (30-50%) only in columns that already have blanks somewhere in the real data, file by file, then build: any page that turns into a stub is a code path that cannot take a blank the data already has | Bugs 6-10 below; clean after the fixes for indicator_values, results, terms, offices, cf_local, people, units, rules, office types, control, cf_state, tax rates, assessed values, debt, audits, timeline, boards, services |

## Bugs found and fixed (by reader impact)

1. **Keyboard focus fell off every map (43 pages).** Tab from the last area of any map (landing picker, Map, county,
   places, schools, budgets, margins, community, campaign pages) went to the page body instead of the panel's
   "Open page" link: the shape's `focusout` redrew the panel, removing the link focus was moving to. A keyboard reader
   lost their place and the Tab walk stopped early (landing 45 of ~150 stops, margins 67 of ~360). Fix:
   `static/js/map.js:130` and `static/js/map_votes.js:532` leave the panel alone when focus moves into it.
   Reproduce (before): map/index.html, focus the last area, press Tab, `document.activeElement` is `<body>`.
2. **Back from a linked contest stayed on that one contest.** On elections/results/, a "Link to this result" (or any
   `#contest-<id>` link) shows one contest; Back restored the plain address but the explorer kept "Showing one
   contest". Fix: `static/js/elections.js:292` leaves the one-contest view when the address loses its `#anchor`
   (a source link inside the card keeps the view).
3. **The vote map forgot the chosen race.** On map/index.html, choosing a race writes `#race-<id>`; switching to
   another layer and back left `#votes`, so a reload or a copied link opened the default race. Fix:
   `static/js/map_votes.js:581` writes the race back when the layer is shown again.
4. **Tax bill preselect blocked by a stale saved choice.** money.js skipped the saved-place preselect whenever any
   saved tax-bill state existed, even one whose district code is no longer in the data (it is not restored either), so
   the reader saw the page's example district with no offer. Fix: `static/js/money.js:362` only a restored choice wins.
5. **Builds were not deterministic.** `pages/money_history.py` picked a committee's candidate name, party and office
   with `max(set(values), key=values.count)`; on a tie the winner followed set order, which changes with Python's
   per-process string hashing. Two builds wrote "Dr. Oliver J. Davis, Jr." / "Oliver J. Davis" (county page) and
   "Gene Reese" / "Robert E. Reese (Gene)" (Walkerton); 5+ campaign pages differed between builds. Fix: `_most_common`
   (Counter order: the value seen first wins a tie; rows are sorted by report date and filing id), lines 43, 157, 211.
6. **Blank Census/QCEW values crashed whole pages into stubs** (the data already has 43 blank `indicator_values.value`
   cells: unpublished ACS estimates, suppressed QCEW counts; a fact-checker blanking one more would do it):
   - place pages' "Population change since 2010" (`pages/places.py:368`): blank count or zero base;
   - school residency evidence (`pages/places.py:1488`): blank township population;
   - schools page / budgets map panel (`civic/school_stats.py:83` `per_student`): a state median row with a blank value;
   - community pages (`pages/community_history.py:214, 313`): a row flagged "CV>30%" in its notes with no margin of
     error (`cv_of` is None) crashed the "unreliable" label;
   - history page (`pages/community_history.py:1264`): a blank South Bend decennial count;
   - budgets "per resident" (`pages/money.py:701`): blank population (or a blank amount) divided.
7. **2026 state legislative results with a blank vote count crashed state/your-legislators/** (`pages/state.py:572`
   tally and `:605` chart): now "votes not in the data" / results_bars' own "votes not recorded".
8. **A retention vote recorded 0 yes / 0 no divided by zero** on elections/judges-and-questions/
   (`pages/elections.py:1434`): skipped like a vote with blank counts.
9. **Straight-party share with a blank or zero `ballots_cast`** crashed elections/turnout/ and landscape/
   (`pages/elections_numbers.py:728`): such an election is left out of `straight_elections`.
10. **Table sort put rows with no number first in a descending sort** (`static/js/tablefilter.js:85`: NaN became
    Infinity). Latent today (the only numeric sort, margins, is ascending); blanks now go last both ways, as
    campaigns.js already does.
11. **Non-ASCII in static JS** (README rule "JS stays ASCII"; app.js builds its middle dot with `fromCharCode` for
    hosts that send another charset): `map_votes.js` had literal middle dots, `search.js` a literal combining-mark
    range in the accent-folding regex. Now `·` and `[̀-ͯ]` escapes; no behaviour change.

## Tests added

`tools/tests/test_debug_pass.py` (11 tests, ~30 s):
- `_most_common` tie-break; no `max/min(set(...), key=...)` call left in pages/ or civic/ (AST check);
- the campaign area pages are byte-identical when built under `PYTHONHASHSEED` 1 and 3 (subprocess; fails on the old
  code: county, courts, German and Harris township pages differed);
- every place page, schools, budgets, history and the three community pages build with every other indicator value
  blank, every row flagged CV>30% and a third of the margins of error blank;
- state/your-legislators with blank 2026 state votes; judges-and-questions with a 0-0 retention vote;
  turnout + landscape with blank and zero `ballots_cast`;
- static JS is ASCII;
- browser (skipped without Playwright/Chromium; builds the pages into a temp dir and serves them): Back from
  `#contest-<id>` shows the list again; Tab from the last map area lands in the panel; the vote layer keeps `#race-<id>`
  after a trip to another layer.

Full suite: 409 tests, 2 failures, both caused by a concurrent data edit (below), not by this pass.

## Left, and why

- **Data (for the fact-checkers / Nick): the Chapleau merge broke two existing tests.** offices.csv and terms.csv
  (uncommitted, a fact-checker on 2026-11-09) merged `superior-court-judge-chapleau` into `superior-court-judge-woods`.
  The county page no longer has `#office-superior-court-judge-chapleau`, so `test_map_navigation` and
  `test_wave_c_batch7` ("every old anchor still on its page") fail. Needs a forward for the old id (a `moved-anchors`
  entry or an alias span on the Woods card) by whoever owns that merge; not edited here to avoid crossing an in-flight
  data change. The Woods office notes now also contain both the old "earlier term is under office
  superior-court-judge-chapleau" sentence and the new "was merged into this one" sentence, which contradict each other.
- `map/index.html#list-votes` (the vote layer's no-JS list) loaded fresh shows the Cities layer, so the target is
  hidden. Only reachable by copying an address; the 224 links to it are vote-layer shapes whose clicks the script
  handles. Low value.
- A `budgets.csv` data row with a blank amount still crashes money pages (`usd_short("")`). Today blanks exist only on
  `series_break` rows, which are never charted, so this is a data-integrity rule rather than a code path the data uses.
  Same for a state House/Senate office with a blank district (`pages/state.py:291`).
- `civic/data.py parse_date` raises on an impossible date (2026-02-30, month 13); kept loud on purpose: a typo should
  fail the build, not vanish.
- Saved place changed in another tab: here.js follows it, but the preselect lines (preselect.js, the explorer, the tax
  bill) keep the old place until reload. Cosmetic.
- pick_one: Back to the plain address after choosing an area keeps the area open (the page started with all closed).
  Reasonable either way; not changed.
- Theme toggle has a descriptive label but no `aria-pressed`; app.js is the foundation's file. Not changed.
- money.py: a breakdown whose amounts sum to zero would divide by zero (`pages/money.py:1054`); generated file, never
  happens. Not changed.

## Build and test results

- Locked build (build_locked.sh) after the fixes: PASSED (links, titles, structure, CSS tokens, neutrality, contract).
- Crawl re-run after the fixes (7 configurations, 113 pages each): 0 problems.
- Tab walk after the fixes: every page reaches the footer (landing 151 stops, margins 362, budgets 352).
- `python -P -E -m unittest discover -s tools/tests`: 409 run, 407 pass; the 2 failures are the Chapleau anchor above.
