# Site redesign plan, 2026-11-09

Plan of record for the overnight redesign. Source: `planning/qa/site-ux-review-2026-11-09.md` (the "review"; all 109
pages have a verdict: 61 Keep, 37 Adjust, 2 Redesign, 2 Split, 7 Merge). Nick's instruction (2026-11-09): "Do a commit
after the site-wide review is complete and the plan is established. After the commit, run the plan as you recommend."

Rollback point: the commit made right after this plan, once the map batch and campaigns Part 4 have landed and pass.
The work after it stays uncommitted for Nick to review in the morning.

## Decisions on the review's open questions (made by Claude per Nick's instruction; Nick can overrule)

| # | Question | Decision | Why |
|---|---|---|---|
| Q1 | Nav bar | `Your place · Topics ▾ · Learn ▾ · About`, each Topics group heading links to its hub | Fits one row at 400 px; "Reference" is unclear; every section gets a parent page |
| Q2 | Landscape URL | Keep `elections/landscape/` as the "By the numbers" overview | Old links and the learning path keep working |
| Q3 | Margins name | Title "Margins: how close each race was"; nav label "Close races" | Plain, and implies nothing about future races |
| Q4 | Uncontested count first | Yes, with its definition and COMPUTED badge beside it | Most useful civic lesson in the data; applies to every party equally |
| Q5 | Officeholders | New `officeholders/` page under Your governments | "Who holds every seat" is a resident question |
| Q6 | Taxing-district map | Saved-place preselect only; no new geometry this round | The guide never draws boundaries itself; needs a DLGF source check first ("Later") |
| Q7 | Copy CSV filtered | Copy only the rows shown, count on the button | Already decided by Nick ("That's fine"); being built by the map batch |
| Q8 | Run office pages | Trim to office-specific facts, keep URLs | URLs are linked from paths; future "which seat" pages |
| Q9 | your-governments, no saved place | Inline list of links | JS-off works; nobody bounces |
| Q10 | Margin chart colors | Accent/ink ramp only, never party colors | Nonpartisan rule |
| B4 | Campaigns map default view | NOT changed: stays "Whole county" | Nick chose "Keep whole county" on 2026-11-09 after the same trade-off was explained |

## Batches, waves and owners

Each batch: `build.py --check` PASSED, unittest, check_gov 0 errors, an old-anchor fixture test for anything moved,
browser checks at 1280 and 400 px × 3 looks × light/dark, keyboard, JS-off. No data CSV edits; never run res_main.py,
build_money.py, build_indicator_values.py. No commits by agents. Helpers are added, never re-signed (README rule).
Claude verifies every batch (checks + browser spot checks) before the next wave starts; failures go back to the agent.

| Wave | Batch | Scope (review §4) | Model | Files owned |
|---|---|---|---|---|
| A | 0. Bugs | B1 `.cov` CSS collision (31 screens), B2 here-tag contrast, B3 seat-diagram layout, plus a checker rule against duplicate bare classes across area CSS. (B4 dropped; B5 goes into batch 2) | Sonnet | static/css/places.css, here.css, landing/looks CSS, tools/site/check.py |
| A | 1. Foundation | P3 "see all rows" fold, P1 `civic/related.py` "More about" rail, P10 results `#contest-<id>` deep links, P5 entity list on `one_fold`, P7 `charts.share_bars()` | Opus | civic/components.py (additive), new civic/related.py, charts (additive), static/js/elections.js (P10 only), new CSS partial |
| B | 2. Elections by the numbers | landscape → overview + `elections/margins/` + `elections/turnout/` + `officeholders/`; Up next → calendar; results turnout dedupe; B5 sentence; PATHS; moved anchors | Opus | pages/elections.py (or new pages/elections_numbers.py), civic/sitemap.py, static/js/elections.js, new margins.js, elections.css |
| B | 3. Place template | Dedupe, reorder, P1 rail, SB/Mishawaka council-district maps on place pages (Walkerton: list only, no shapes), one row per body | Opus | pages/places.py (not schools code), static/css/places.css |
| B | 4. Lists instead of stacks | history/people list; other-committees and all-filings by committee; who-handles-this; run pages trim + run/index cards; data/pull folds; community employer folds | Sonnet | pages/community_history.py, pages/campaigns.py, pages/campaign_pages.py, pages/participate.py (run/who-handles only), pages/data_sets.py |
| C | 5. Judges & ballot questions | Question list by jurisdiction, retention folds | Sonnet | pages/elections.py (after 2) |
| C | 7. After the map work | County results per district + rail; schools seat lists + board layers + rail; legislators results/money per district; budgets per-unit flows, special units as chips, debt fold | Opus | pages/county.py, schools code in places.py (after 3), pages/state.py, pages/money.py |
| D | 6. Navigation and hubs | Topics/Learn nav, renames, elections hub + `elections/how-it-works/`, your-governments → "Your place" (Q9) | Opus | civic/shell.py, civic/sitemap.py, pages/elections.py (index split), pages/participate.py (your-governments), nav CSS |
| E | 8. Saved-place preselect | P4 `preselect_from_here` on calendar, tax bill (district), officeholders, judges, community maps, results | Opus | static/js/here.js (additive), page JS |
| E | 9. Sticky in-page nav | P9 on pages still over ~12 screens | Sonnet | civic/shell.py, CSS (after 6, and not alongside 8 if 8 needs shell) |
| Later | — | Taxing-district map (DLGF source check), "by seat" margins history if deferred, districts as a place type in the results explorer | — | — |

At most 3 agents run at once. Usage guard: pause everything at 90% of the 5-hour window, resume after reset
(docs/session-handoff.md has the procedure). Expected scale: roughly 2–3M tokens across the waves.

## Status
- [x] Map batch (pre-plan, in flight) verified (build PASSED 109 pages, 153 tests, check_gov 0, check_money OK, browser)
- [x] Campaigns Part 4 (2023 YTD basis audit) verified (spot-checked against raw filings)
- [x] Commit (rollback point): 240a3e8, not pushed
- [x] Wave A (verified ~03:30)  - [x] Wave B (verified ~05:00)  - [x] Wave C (verified ~06:40)  - [x] Wave D (verified ~07:30)  - [x] Wave E (verified ~09:40)
