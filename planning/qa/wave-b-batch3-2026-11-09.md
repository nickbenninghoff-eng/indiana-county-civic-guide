# Wave B, batch 3: place-page template, 2026-11-09

This batch redesigns the 22 city, town and township pages under `places/<id>/`. The spec is `site-ux-review-2026-11-09.md` §3.2, P1/P2/P4/P5 and §1.3. Nothing is committed.

Checks, all run at the end:
- `python -P -E tools/site/build.py --edition st-joseph --check` ends **PASSED** (112 pages).
- `python -P -E -m unittest discover -s tools/tests` gives **219 OK**. 20 of those are new, in `tools/tests/test_place_template.py`.
- `python -P -E tools/check_gov.py` reports **0 errors**.

Mid-run, the checker and three `test_page_organization` / `test_wave_a_patterns` tests failed. They failed on batch 2's elections files while those were mid-edit. They passed on the rerun, and I did not touch those files.

## 1. What changed

### New page order (every place page)

| # | Section | Notes |
|---|---|---|
| — | Hero: At a glance, then the **"More about" rail** (now on all 22 pages), badges, coverage strip, TOC | |
| 1 | **Who holds office now** (`#officeholders`) | One compact holder row per office (`civic/holder_rows.py`). Each summary line gives the holder with party, since when, the next election and any incoming 2026 winner. Rows are grouped: "City/Town/Township officers", then one h3 per elected body with its party breakdown and seat count. Each row opens to the card fields plus **"This seat:"** links to the result on this page, the results explorer, the map (precinct view) and the race card on the campaign money page. South Bend and Mishawaka add a council district map; Walkerton adds a ward note |
| 2 | **How it's organized** (`#structure`) | One explainer per page. One row per body, with every office in a See-all fold. The township location lists sit here |
| 3 | Unelected but powerful (`#unelected`) | Cities only, unchanged |
| 4 | **Recent results** (`#results`) | One summary row per race: candidates in ballot order with votes, share and "elected"; status; links to the chart, the explorer and the map. The charts are in a See-all fold. Cities also get the mayoral history sub-block: chart, then the table folded |
| 5 | Party control over time (`#control`) | unchanged |
| 6 | Budget (`#budget`) | The text and tax-base line stay visible. The state-report "Money in and money out" charts (about 2 screens) move into a fold |
| 7 | State audits (`#audits`) | The intro and the SBOA-charges callout stay visible. The report cards move into a fold |
| 8 | Context (`#context`) | unchanged |
| — | Gaps, Sources | unchanged |

**One departure from the review's order.** The review proposed Budget before Party control. Party control comes first here so that Context never sits right after a results or party-control visual (neutrality review F6, the rule the old code enforced).
- `_place_order` enforces this, with a fallback for a place that has no budget or audit section. No place in this edition has neither.
- A test checks every page.

### Dedupe (P2)
- **Township explainer.** "What townships do" was printed twice on all 13 township pages: once as its own section and again at the top of "How it's organized". It is now printed once, as the first sub-block of How it's organized. A test checks the paragraph appears exactly once.
- **Organization table, one row per body.** Example: "South Bend Common Council · 9 (6 district seats, 3 at-large) · 4 years · 2027".
  - Walkerton's council row shows when each seat is up: "2027 (Ward 3, Ward 4, at-large); 2030 (Ward 1, Ward 2)".
  - The per-seat table, with its old id, moves into "See all N offices". Only South Bend, Mishawaka and Walkerton need the fold; townships and the other towns were already one row per body.
- **Party breakdown.** The old "Boards and councils by party" list duplicated the body headings, so the breakdown now sits in each body's h3.
  - The as-of note stays.
  - Cities get one line pointing to "Unelected but powerful" for their appointed boards, which keeps the caveat "Party is not tracked for appointed boards".

### "More about" rail (P1) on all 22 pages
- `related_links(page, uid)` now runs on every place page, not only South Bend.
- **Campaign money link.** Every rail links to its campaign money area page (`money/campaigns/<id>/`), so all 22 area pages that match a place now get an inbound link from that place. A test checks this.
- **Towns now get a "Run for office" link.** There is no town-council run page, so towns link to `run/index.html`. This is a small addition in `related_items`. Every place page now answers "how do I get involved".
- The rail only links to targets that exist. `check.py` fails the build on a missing page or `#id`. The new test also follows every rail link, every "This seat" link and every map-panel link (the panel's JSON links, which `check.py` does not read) into built pages: 300+ links, all land.

### Council district maps (P4) on South Bend and Mishawaka
- **Map.** `district_map` with the `south-bend-council-2022` / `mishawaka-council-2022` shapes.
  - The map is cropped to the city (padded union of the district boxes). Labels are rescaled per zoom step in `places.css`.
  - Fills only separate neighboring districts (district_map.css); they are never party colors. A test checks for no party or shade classes.
- **Panel.** It shows:
  - the council member (with party label), since when and the next election with term length;
  - links to the 2023 result on the page, the explorer and the 2023 campaign money race card;
  - the caveat from `campaign_map.SET_NOTES`.
- **Mishawaka caveat.** Mishawaka also carries "Confidence: medium… no ordinance or precinct list was found…", taken from the district-maps research §4. It appears in the panel and the legend.
- **Legend.** The adoption source (ordinance, cited MAP-024/025 or MAP-026/028) and "The 3 at-large seats are elected by the whole city, so they are not on the map."
- **Selecting a district.** Clicking it, or pressing Enter on it, opens that member's row and folds the others (`pick_one`). The address becomes `#office-<id>`. Show all / Collapse all is in the state bar.
- **Walkerton.** Its wards are listed, not drawn. A "Council wards" note gives the 4 ward seats plus 1 at-large, explains that the wards are defined by street descriptions with no boundary file (`campaign_map.NO_SHAPES["town"]`), says the written description controls and that the map is on file with the Clerk-Treasurer (cited MAP-036), then lists each ward's member row.

### Long tables
- **Results.** The summary table is visible, and every results chart (with its table view) is in "See all N result charts".
- **Mayoral history.** The 17-row (South Bend) table is under its chart, in "See all N mayoral elections, with every candidate".
- **Per-seat organization rows.** These are folded, as described above.

## 2. Where every old piece went

| Old (section id) | Now |
|---|---|
| `#what-townships-do` (section, townships) | `<div class="sub-block" id="what-townships-do">` with `<h3 id="what-townships-do-h">` at the top of How it's organized. The second copy of the explainer is gone (same paragraph, same page) |
| `#structure` office table `#offices-<id>` | Still `#offices-<id>`. For SB, Mishawaka and Walkerton it is inside the fold `#offices-<id>-all`, under the new `#bodies-<id>` summary |
| `#officeholders` cards `#office-<office id>` | Holder rows (`<details id="office-<office id>">`), same ids. Conflict panels and conflict cards are unchanged in markup |
| "Boards and councils by party" (bodies_block) | Party breakdown in each body's h3, plus the as-of note. Cities' appointed-board seat lines are in the Unelected tables (Seats column), with a pointer line and APPOINTED_NOTE |
| `#control` | unchanged, now section 5 for cities and towns |
| `#mayor-results` (section) | Sub-block inside Recent results, with the same ids (`mayor-results`, `mayor-results-h`, `mayor-results-<id>…`, `mayor-table-<id>`). The table is in the fold `#mayor-table-<id>-all` |
| `#townships` / `#places-inside` (sections) | Sub-blocks inside How it's organized, with the same ids and `-h` ids |
| `#unelected` | unchanged |
| `#results` charts `#res-<contest>…` | Inside the fold `#results-charts-<id>`. The "Show most recent results" button on city pages is replaced by the summary table plus the fold. The sentence "The bar scale is 0 to 100%" moved into the fold |
| `#budget`, `#money-<id>`, `#sp-<id>-…` | Same ids. The state-report block is inside the fold `#money-flows-<id>`, and links to `#money-<id>` (from the budgets map) open it |
| `#audits` | The report cards are inside `#audits-<id>-all` |
| `#context`, `#glance`, `#related`, `#gaps`, `#sources` | unchanged |

A text diff over all 22 pages, old against new, finds only these strings missing:
- the reworded officeholder intro sentence;
- the "Boards and councils by party" heading;
- section numbers;
- the source-count number, now higher because the map sources were added;
- the bodies_block seat lines, which are now in the h3 headings or the Unelected tables.

## 3. Anchor proof
- **Snapshot.** `tools/tests/fixtures/anchors_before_place_template.json` holds every id on the 22 pages before this batch: 2,541 ids from the 01:52 build.
- **Test.** `test_every_old_anchor_is_still_on_its_page` passes: every id is still on its own page, so no `moved.js` forwarding is needed.
- **No duplicate ids** on any page.
- **Old section ids that are now sub-blocks** keep both their `id` and `-h` ids (tested). A section anchor or path stop lands on the same heading text.
- **Inbound links from other pages** (`places/<id>/#context`, `#money-<id>`, `history#mayors` back) all still resolve, and `check.py` PASSED.

## 4. Screens (document height ÷ 800, JS on, first load, all folds closed)

Measured by a script that loads each built page in an iframe at 1280 and 400 px wide. "Before" is the build just before this batch.

| Page | Before 1280 | After 1280 | Before 400 | After 400 |
|---|---|---|---|---|
| centre-township | 10.2 | 6.9 | 15.2 | 10.6 |
| clay-township | 10.4 | 7.1 | 15.5 | 11.0 |
| german-township | 10.0 | 6.9 | 14.8 | 10.6 |
| greene-township | 9.6 | 6.7 | 14.2 | 10.3 |
| harris-township | 10.3 | 7.0 | 15.2 | 10.7 |
| liberty-township | 10.0 | 6.9 | 14.7 | 10.6 |
| lincoln-township | 9.9 | 6.9 | 14.9 | 10.6 |
| madison-township | 9.6 | 6.7 | 14.3 | 10.3 |
| olive-township | 9.9 | 6.8 | 14.9 | 10.6 |
| penn-township | 11.0 | 7.3 | 16.5 | 11.4 |
| portage-township | 10.1 | 6.9 | 15.5 | 10.5 |
| union-township | 8.8 | 6.1 | 13.9 | 9.6 |
| warren-township | 10.0 | 6.9 | 14.9 | 10.6 |
| indian-village | 6.7 | 4.7 | 10.4 | 7.3 |
| lakeville | 8.4 | 5.9 | 12.7 | 9.1 |
| new-carlisle | 10.3 | 6.6 | 15.0 | 10.1 |
| north-liberty | 9.0 | 5.8 | 13.6 | 9.0 |
| osceola | 9.7 | 6.7 | 14.6 | 10.1 |
| roseland | 11.0 | 6.8 | 16.5 | 10.3 |
| walkerton | 10.5 | 7.9 | 17.3 | 11.7 |
| south-bend | 13.4 | 11.2 | 21.3 | 15.3 |
| mishawaka | 12.7 | 11.5 | 19.8 | 15.8 |

- **Totals.** About 30% shorter on average: 221.5 to 156.2 screens at 1280, and 335.7 to 236.1 at 400.
- **The two cities.** They gain the district map (about 1.2 screens at 1280) and still come out shorter.
  - On South Bend at 1280, the sections run: officeholders 2.3 (map included), structure 1.1, appointed boards 1.2, results 2.1 (the summary table plus the mayoral chart), party control 1.0.
  - Both cities are still over 11 screens, so they are candidates for P9 (sticky in-page nav).
- **Before numbers** match the review's table within 0.1.

## 5. Browser checks (Claude in Chrome, own tab; scripted iframes on a local copy of the build)
- **Matrix.** South Bend, Mishawaka, Walkerton, Lakeville, Penn and Union × 3 looks × light/dark × 1280/400 = 72 loads.
  - The look and theme applied every time.
  - There was no page-level horizontal overflow and no JS errors.
  - The only elements past the right edge are SVG paths clipped inside the map.
- **Screenshots checked:**
  - South Bend at 1280 (ballot, light and dark): hero, rail and map;
  - Mishawaka at 400 (wayfinding dark, line dark): map labels readable after the label fix;
  - Walkerton at 400 (ballot light): ward note and holder rows;
  - Penn at 400 (wayfinding dark): explainer once;
  - Lakeville at 1280 (line light): results summary and folds;
  - Union at 1280 (ballot dark): rail and holder rows.
- **Keyboard.**
  - Focusing District 5 fills the panel: member, since, next election, caveat and three links.
  - Enter navigates to `#office-south-bend-council-d5`, opens only that row (state line: "Showing South Bend Common Council, District 5…") and scrolls to it.
  - The row's "2023 result on this page" link opens the results fold and lands on the chart.
- **JS off.** Every `details` ships `open` (tested on all 22 pages), and the one-bar is `hidden`. Every map district is a plain `<a href="#office-…">`.
- **Limitation.** The Chrome window could not be resized past a 597 px viewport (it is shared with other agents). I checked desktop width with an iframe scaled to fit, not a real 1280 window.

## 6. Tests (`tools/tests/test_place_template.py`, 20)
- **Anchors and ids.**
  - Every old id is still on its page.
  - There are no duplicate ids.
- **Order and dedupe.**
  - The order rule, plus the `_place_order` fallback unit tests.
  - Sub-blocks keep their `id` and `-h` ids.
  - The township explainer appears once.
  - The organization table is one row per body, with the fold shipping open and the Walkerton years.
- **Links.**
  - The rail is on all 22 pages, with the campaign money and run links.
  - Every rail, seat-line and map-panel link lands.
  - The South Bend District 5 seat links point to the result, the explorer and the campaign race card.
- **Maps.**
  - The district maps link 6 districts each, with no party or shade classes, panel facts and links, and Mishawaka's medium-confidence caveat.
  - Walkerton is listed, not drawn.
  - No other page has a map.
- **Folds.**
  - The results summary row count equals the number of charts, and the fold ships open.
  - Every fold ships open.
  - The mayoral table is folded under its chart.
- **related.py.**
  - Towns get the general run page.
  - `seat_items` returns its keys in order, invents nothing and raises on bad input.

## 7. Notes and questions for the main session
1. **Party control before Budget** (a departure from the review, for neutrality rule F6). Keep it, or should Budget move up and Context move elsewhere?
2. **Default state.** Officeholder rows load collapsed (summary lines only), the same as the county page. The summary line already answers "who represents me, since when, next election". Should the saved place's district open instead (P4 preselect, batch 8)?
3. **Budget charts folded.** "Money in and money out" was 2.2 to 2.6 screens per page and is now one line. The review names the unit's own page as this content's single home. It is still here, just folded. OK?
4. **Data issue: Walkerton Town Judge.** The contest `2023g-walkerton-judge` derives the office id `walkerton-judge`, but the office is `walkerton-town-judge`. The judge's row therefore gets no "This seat" links. The race still appears in the results summary. Fixing it means editing data or the contest-to-office rule (`civic/data.py`); I did neither.
5. **Seat campaign links depend on batch 4's ids.** They point at `money/campaigns/<area>/#r-<contest>`, read from the same `cf_all` model `campaign_pages.build_area` prints from. If batch 4 renames those ids, `check.py` will fail the build. The test's link-landing check covers it too.
6. **Rail candidate for later.** Batch 2's new `officeholders/` page could become a rail item ("Every officeholder") once it lands. I did not add it, because the page was mid-edit.
7. **Not done.** I did not update `Roadmap.md` or `docs/session-handoff.md`; that is left for the main session. I did not edit any data CSV, and I did not touch the schools code in `places.py`.

## 8. Files
New:
- `tools/tests/test_place_template.py`
- `tools/tests/fixtures/anchors_before_place_template.json`
- this report

Changed:
- `tools/site/pages/places.py`
  - The place template is rewritten: `build_place` and its helpers. `_results_block` is replaced by `_results_section`.
  - `_mayor_block` also returns its row count.
  - `_budget_block` and `_audits_block` fold their long parts.
  - The schools code is untouched.
- `tools/site/civic/related.py`, additions only:
  - `seat_items`, `campaign_race_anchor` and `RUN_INDEX`;
  - the towns' run-page fallback in `related_items`.
- `tools/site/static/css/places.css`: sub-blocks, seat links, results cells, map label sizes per zoom.
- `tools/site/README.md`: the related.py row and a new row for the place template.
