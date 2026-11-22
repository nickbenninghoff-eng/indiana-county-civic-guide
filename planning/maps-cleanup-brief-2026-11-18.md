# Maps on every major page + cleanup round (2026-11-18)

Written by the main session. Baseline: commit 2dee977 (live). Owner (Nick), 2026-11-18: "How come money and campaign
money pages don't have a map view as well? ... a while ago I asked that all major pages should have the map view to
help users navigate easier. Those are definitely pages and there's probably many more major pages like those that
would benefit from it." Then: "Go ahead and combine it with the cleanup round".

## Read first
1. `planning/design-direction-2026-11-16.md` (approved Phase 6 design: calm look, page types, tabs, status marks)
2. `tools/site/README` (helpers are added, never re-signed)
3. How the existing maps work: home (`pages/landing.py`, `static/js/home.js`, `static/css/home.css`), Offices hub
   (`pages/offices.py`, `static/js/offices.js`), Governments hub (`pages/governments.py`), campaign money By place
   (`pages/money_browser.py` / `pages/campaigns.py`, `civic/money_map.py`), Compare budgets, Margins; shared map code
   `civic/map.py`, `district_map.py`, `layers.py`; saved-place preselect (`civic/preselect.py`, `static/js/here.js`).
4. Phase 6 reports in `planning/qa/phase6-*.md` for what each page does now.

## Part A: a map view on every major page (do this first)
Goal: the county map is a consistent way to navigate on every hub, browse and landing page. One shared component, not
a new one-off per page: build (or extract from the home/Offices hub code) a reusable "map navigator" in `civic/` with
one JS module and one CSS partial, then use it everywhere below. Same behaviour everywhere: choose a layer, point at or
select an area, and the page either filters its own list to that area or shows that area's links for this topic;
selecting again (or a button) opens the area's page. It honours the saved place ("My place") as the starting
selection where one is saved. County map only (the guide never draws Indiana or the U.S., and never draws boundaries
it has no official file for); areas with no boundary file are reachable from the list beside/below the map.

Pages that must get it (confirm each against the built site; the first column of the main session's scan may be
imperfect, so check for yourself and list the final coverage in your report):
- Money hub (`money/`): pick an area → that government's Money tab, its budget, tax and campaign-money links.
- Campaign money: the default "By office" view (`money/campaigns/`), By election, By candidate, Committees, Every
  filing: pick an area → the list filters to offices/races/candidates/committees for that area. The existing By place
  map stays; the others should feel like the same tool, not a second design.
- Elections hub (`elections/`), results explorer (`elections/results/`), each election page (`elections/<id>/`, on the
  tab where it helps most), calendar, turnout: pick an area → contests / dates / turnout for that area.
- People hub (`people/`): pick an area → the people who hold or have run for that area's seats.
- Who holds every seat (`officeholders/` or its Phase 6 successor): pick an area → its seats.
- Community hub: pick an area → that area's community pages. Rule F6 still applies: community context never beside
  election results or party control.
- Any other hub/browse/landing page you find without one (e.g. Compare-style pages, judges, public questions,
  "by the numbers"): add it, or say in the report why a map does not help there.
Not needed: Learn hub and individual guide pages, About/Sources/method pages, single office/person/government pages
(they already have their own location context), data downloads. List these as deliberate exclusions.

Requirements:
- Works without JavaScript: the map still renders with links, and the full unfiltered list is always in the page.
- Keyboard: every area reachable and selectable by keyboard with a visible focus; filters announce the result count
  (aria-live, polite). Do not trap focus.
- The map never becomes the only route: the list and search stay.
- Do not make pages heavier than needed: the map geometry/JSON must be shared (one cached asset referenced by every
  page), not inlined again on each page. See Part B item 2; design the shared asset once for both.
- Layout: at 1280 the map sits beside or above the list without pushing the page's main content below the first
  screen more than necessary (a compact, collapsible map is acceptable: open by default on hubs, a "Show map" fold on
  long browse pages if it would otherwise dominate; state which you chose per page). At 400 px it stacks, no
  horizontal overflow.
- Neutral: fills only tell kinds of government or neighbouring districts apart; never party colours, never amounts
  implied by fill on the navigator.

## Part B: cleanup (after Part A is built and the build passes)
1. Learn hub guide cards: lighter borders (owner approved: the heavy black borders read louder than the calm look).
2. Page weight: the site is ~250 MB because the header/navigation and map/search JSON repeat on every page. Move
   repeated JSON (map data, search index hooks, anything large and identical) into shared cached assets; shrink the
   repeated header markup where it can be done without losing no-JS navigation. Report site size and the ten heaviest
   pages before and after. Area pages are heavy in bytes: look there first.
3. Sources tabs run 4-8 screens: shorten (group by kind with folds, show the count, keep every source reachable and
   every existing `#src-`/citation anchor working).
4. Campaign pages: about 525 "incomplete" words and "(incomplete)" labels in the campaign map SVG remain. Apply the
   status-marks system: mark with the fixed symbol, state the shared status once in the caption or the page's "About
   these figures" note.
5. "computed": say it once per tab (caption or the About-these-figures note) instead of beside every figure (owner
   approved). The fixture test `tools/tests/test_status_marks.py` proves no status is lost: keep it honest (a status
   moved to a caption must still be found by the scoped check; do not weaken the test, and if the fixture needs
   regenerating explain exactly why and list every substantive difference).
6. Footer link "What the badges mean": rename to match the marks system (e.g. "What the marks mean").
7. Compare budgets is 4.6 screens: bring it to about 3 without removing data (folds, tighter charts).
8. Final checks the earlier rounds did not do: keyboard pass on the new and Phase 6 interactive parts (tabs, map
   layers, folds, money switch, search); JavaScript-off pass on every hub; the Netlify CSP still passes
   (`python -P -E tools/site/netlify_prep.py` on a copy, as the tests do); old-URL and old-anchor fixtures all pass.

## Hard rules
- No edits under `data/`. Never run tools/res_main.py, build_money.py, build_gov.py, build_community_people.py,
  build_indicator_values.py. No new dependencies (Python stdlib; no JS libraries).
- No git add/commit/push/stash/checkout/reset. Leave all work in the working tree. Do not deploy anything.
- Neutrality: money charts never party colours; community context never beside election results or party control
  (F6); party tags display-only; identical treatment for every party and candidate.
- No literal colours outside the CSS token block. All three looks (`html[data-look]`: default ballot, `line`,
  `wayfinding`) × light and dark must work. No horizontal overflow at 1280 or 400 px.
- Old URLs and anchors keep working. Status marks as built (no mark on official figures; one "About these figures"
  note per page). Calm look: no new heavy borders or badge clutter.
- Privacy: only official office contacts; never home addresses, personal phones, personal emails.
- Preview server: pm2 `civic-guide-preview` serves `site/st-joseph` at http://localhost:8787 (already running; do not
  start another). Run at most one site build at a time.
- Quality over speed: root-cause fixes, tests for every new behaviour, edge cases handled (area with no boundary
  file, area with no rows for this topic, saved place that no longer exists, JS off, very long lists).

## Done means
- `python -P -E tools/site/build.py --edition st-joseph --check` ends PASSED.
- New tests (one file for the map navigator and its per-page coverage, one for the cleanup items) and all updated
  tests pass; full suite run once at the end in the background
  (`python -P -E -m unittest discover -s tools/tests`, about 30 minutes): report its exact last lines.
- `python -P -E tools/check_gov.py` 0 errors, `check_money.py` OK, `check_results.py` 0 errors.
- Browser check with screenshots in `planning/qa/phase6-shots/` (prefix `maps-`): every page that gained a map at
  1280 and 400 px in the default look, light and dark, plus each other look once; one keyboard walk-through and one
  JS-off view described in the report.
- Report at `planning/qa/phase6-maps-cleanup-2026-11-18.md`: coverage table (page, has map, how it filters, open or
  folded by default, deliberate exclusions with reasons), cleanup items done / partly / not done, site size and
  heaviest pages before and after, exact check output, what you did not check, open questions for the owner.
