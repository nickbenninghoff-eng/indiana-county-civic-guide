# Phase 6, office pages part 2 (2026-11-16)

Brief: Money tab controls, primary/general split, chart width, Offices hub map and collapsed groups, unmatched
contests, small fixes. Nothing is committed. No file under `data/` was edited, and none of the forbidden build tools
was run.

## Checks

| Check | Result |
|---|---|
| `python -P -E tools/site/build.py --edition st-joseph --check` | **PASSED**, no BUILD FAILED (last run after every change). Earlier runs failed only on the other agents' work in progress (`pages.governments` missing for a while, election-page anchors). |
| `test_phase6_offices2.py` (new, 17 tests) | OK |
| `test_css_duplicates`, `test_campaign_money`, `test_money_history`, `test_security_escaping` | OK |
| `test_phase6_offices.py` (step 1) | 22 of 24 OK. **2 fail because of the other agents' moves, not this work**: `test_cross_links_to_office_pages` (places/south-bend/ is now a forward to governments/south-bend/, so it no longer links the Mayor page) and `test_every_page_within_two_clicks` (elections/landscape/ and elections/turnout/ are no longer within two clicks). |
| Full suite `python -P -E -m unittest discover -s tools/tests` | 459 tests, 40 failures and 21 errors. Every one I checked is in the government or election pages (places/, county/, schools/, elections/margins, turnout, the old-anchor fixtures). None names an office page, the offices hub, the money charts or the footer. |
| `python -P -E tools/check_gov.py` | errors=0, warnings=23 (the existing blank-start warnings) |
| Browser (Playwright, pm2 preview on 8787) | 108 page views with no horizontal overflow and no console errors. Each view had the look and theme applied as set. Detail below. |

## What changed

Files (all in my ownership list, plus the one shared edit):
- `tools/site/pages/offices.py`
  - Money tab rewritten around phases and the party filter.
  - Elections tab: older contests ship open, and the bars are drawn in HTML.
  - Offices hub: map plus collapsed groups.
- `tools/site/civic/offices.py`, additive: `committee_split`, `candidate_split`, `race_split` (the primary/general split).
- `tools/site/civic/charts.py`, additive only:
  - `money_rows`: an HTML version of `money_pairs`.
  - `results_rows`: an HTML version of `results_bars`.
  - Existing helpers are unchanged. `money_pairs` is now unused, but kept.
- `tools/site/static/js/offices.js` (new):
  - the Money tab controls;
  - the hub map's office lists;
  - the hub's saved-place line.
- `tools/site/static/css/offices.css`: styles for the new parts. It uses tokens only, and the old SVG `min-width` rule is removed.
- `tools/tests/test_phase6_offices2.py` (new).
- `planning/qa/phase6-unmatched-contests-2026-11-16.md` (new; task 5).
- **Shared edit, `tools/site/civic/shell.py` `_footer`:** the print colophon (`edition-stamp`) now reads only "series · edition".
  - The data date and version stay in the footer stamp, once.
  - The file was re-read just before this one small edit.
- `civic/data.py`: **not changed.** No alias qualified (see task 5).

### 1. Money tab controls
- Above the charts sit an **Election** switch (Both / Primary / General) and a **Party** select.
  - The party options are All parties, then each party code on the page alphabetically, then "Party not recorded".
  - Both controls are neutral: the edition accent or ink, never a party colour.
  - They are themed for all three looks.
- **The controls ship `hidden`.** With JavaScript off every chart shows, as before (tested, and checked with JS off in the browser).
- **How the switch works:**
  - Every chart carries `data-mt-phase`:
    - `whole`: whole-cycle filings;
    - `primary` or `general`: a news-reported contest, or one side of a split cycle. Split charts also carry `data-mt-split`.
  - Both shows the whole-cycle charts and the news charts of both contests.
  - Primary and General show only their side.
  - Each candidate row carries `data-party`. Rows of other parties hide, and a chart with no rows left hides.
- **Hidden elections:** an election left with nothing to show is hidden. A line says how many and why, for example: "1 election is hidden: 2023 (whole-cycle figures only: the county posted no 2023 pre-primary reports)" or "2019 (no figures for Republican (R))".
- **Linking:** the choice is written to the address (`#show=primary&party=D`; defaults leave it clean) and read on load and on hashchange. Other `#ids` are left alone.
- **State legislator tabs:** they get the same two controls. Their figures are by filing year, so Primary or General hides them, and the line says "filing-year figures for each candidate's committees, not split by election".

### 2. Primary vs general (filed cycles)
- **Rule.** The split is at the committee's pre-primary report, and nothing is estimated.
  - Primary side, "Through the pre-primary report": the "this period" columns of the counted reports in slots earlier / prior-annual / pre-primary.
  - General side, "After the pre-primary report": the counted pre-election, year-end and later reports.
  - Which reports count comes straight from `campaign_money.committee_summary`: its amendment, duplicate, nesting and cash-chain rules.
  - Both parts are sums of whole reports, and the code refuses any split whose parts don't add up exactly to the whole-cycle figure.
- **A committee is not split when** it has:
  - no pre-primary report on file;
  - a pre-primary report folded into a later report covering both periods;
  - an unreadable pre-primary report;
  - a date-doubt flag;
  - conflicting dates;
  - overlapping reports;
  - a year-to-date basis for any year.
- **What the reader sees when it can't be split:**
  - The candidate stays only in the whole-cycle chart.
  - A line names them with the reason.
  - A group with no splittable candidate gets no empty chart.
- **Where it applies:** 19 candidates in 2024 and 32 in 2026 (of 51 and 87 with a race record).
- **2023:** never split. Each 2023 race says "Not split into primary and general: the county posted no 2023 pre-primary reports."
- **Placement:** the split charts follow the whole-cycle chart. With JS off all three are on the page. With JS, Both shows the whole cycle and a hint to choose Primary or General.
- **Note on report type:** the split follows the period, not the box marked on the form.
  - Example: Cichowicz's cfl-62625 is marked "Pre-Election" but covers Jan 1 to Mar 31, 2024, so it is the pre-primary report.
  - This is the same rule as the campaign pages (`slot_of`), and the race card already notes the mismatch.

**Hand-checked figures**, from `cf_local.csv` rows read directly against the split's output (2024 cycle):

| Candidate (office) | Row | cf_local.csv receipts / expenditures (this period) | Split: through the pre-primary report |
|---|---|---|---|
| Sharon Banicki (County Recorder) | cfl-62638, Pre-Primary, 2024-01-01 to 2024-04-19 | 8193.31 / 6132.81 | $8,193.31 / $6,132.81 |
| Anthony "Tony" Hazen (Commissioner D3) | cfl-62641, Pre-Primary, to 2024-04-12 | 86350.84 / 75509.04 | $86,350.84 / $75,509.04 |
| Randall L Figg (Council F) | cfl-62637, Pre-Primary, to 2024-04-12 | 16284.27 / 12583.15 | $16,284.27 / $12,583.15 |
| Kent D. Hizer (Council I) | cfl-62628, Pre-Primary, to 2024-04-12 (filer-inconsistent; counted, as in the whole cycle) | 24848.69 / 18375.82 | $24,848.69 / $18,375.82 |
| Jason Cichowicz (Probate Judge) | cfl-62625, marked Pre-Election, period to 2024-03-31 | 5073.80 / 4016.18 | $5,073.80 / $4,016.18 |
| Candace Brown (County Recorder) | cfl-62643, marked Pre-Election, period to 2024-04-12 | 9970.47 / 6388.70 | $9,970.47 / $6,388.70 |

After the pre-primary report:

| Candidate | Rows | Check |
|---|---|---|
| Figg | cfl-64471 (250.00 / 3917.19) + cfl-65668 (500.00 / 0.00) | $750.00 / $3,917.19. Correct. |
| Hizer | cfl-66179 Final (148.25 / 8543.80) | $148.25 / $8,543.80. Correct. |

All of these are pinned in `test_phase6_offices2.py`.

### 3. Chart width
- **Money charts** are now HTML bars (`charts.money_rows`):
  - a name column of 9 to 15 rem, and the bars across the rest of the content width;
  - each figure is printed right after its bar, in a reserved strip, so it is never cut off;
  - one shared scale per office, as before.
  - At 1280 px the bars run about 730 px instead of about 300 px.
  - At 400 px the name sits above its bars; there is no inner scroll and no page overflow.
- **Elections tab** results also used a fixed 200 px SVG plot. They are now `charts.results_rows`:
  - HTML, 0 to 100% across the width;
  - party marks only beside their text label, as before;
  - the same table view.
  - The figures are prepared by a copy of `pages/county.py _contest_figure`'s data step, kept in `pages/offices.py`, because county.py belongs to the government agent. Only the drawing differs; see the open questions.

### 4. Offices hub
- **The map leads** (section "Who your area elects"). It is built only from the existing `map_shapes.json` and `district_shapes.json`; no new geometry.
- **Nine layers:** Countywide, Cities and towns, Townships, School corporations, Commissioners, County council, City councils (South Bend and Mishawaka sets together), Indiana House, Indiana Senate.
- **It uses the `.cmap` contract**, so `map.js` gives:
  - hover, focus, and touch select-then-open;
  - layer tabs;
  - the panel that keeps the last area.
- **`offices.js` adds the office list to the panel.** Each area's list is shipped hidden in `#ofm-lists`, and the script copies it in whenever `map.js` redraws the panel. Each entry has:
  - the office linked to its page;
  - the holder(s) with the usual party tag;
  - the next election.
- **Seats with no boundary file** (Walkerton wards, SBCSC districts, New Prairie districts, and the PHM, John Glenn and LaVille township seats) are listed under their government as "No drawn boundary in the guide (elected by district or ward)".
  - The government's panel also counts them.
  - Districts that are drawn say which layer draws them.
- **JS off:**
  - The default layer shows, and every area is a link.
  - A government links to its group in the list; a district links to its office page.
- **Saved place:**
  - The hub selects the reader's city or town (or township) on the map and scopes the list to the reader's governments (`tablefilter` `tf-scope`, rows carry `data-here-layer`).
  - The visible line reads "Showing: … [Show all]".
  - Only what the reader chose counts. With defaults only, a South Bend reader gets all 6 of the city's townships and every school corporation.
  - An explicit `#anchor` wins, and then the line is only an offer.
  - Reset in the filter turns the line back into an offer.
- **The list** is one line per government: name, number of offices, seats, and the party breakdown already used for bodies.
  - Groups sit three to a row at 1280 px; an open group takes the full row.
  - The groups are `<details data-fold open>`: they ship open (JS off: all 127 offices visible, tested) and `folds.js` closes them on load.
  - The breadcrumb's `#g-<unit>` opens its group, and the filter still opens matching groups.
  - All existing ids are kept: `county`, `cities`, `towns`, `townships`, `schools`, `state` and `g-<unit_id>`.
- **Height** at 1280×900 (Ballot light), before anything is opened: **3.04 screens** (was 8.9).

### 5. Unmatched contests
- See `planning/qa/phase6-unmatched-contests-2026-11-16.md`: all 111, one row each.
  - 68: office missing from offices.csv (statewide offices, state appellate retentions, House District 48 in 2010).
  - 28: out of scope (straight-party tallies, public questions).
  - 15: ambiguous.
  - 0: spelling variants.
- **No alias was added.** Every spelling of an office in `offices.csv` is already caught.
- Two strong candidates are listed for review, not applied, because they are not spelling variants:
  - 2020 Chapleau retention → `superior-court-judge-woods`. `terms.csv` says Chapleau held that seat and was retained in 2020.
  - 2016 "Retention: Judge Hurley" → `superior-court-judge-hurley`.
- A test keeps the file in step with the data: it fails if the set of unmatched contests changes.

### 6. Small fixes
- **Footer:** the data date now appears once (tested on the hub).
- **Elections tab:** older contests ship open with JS off (`data-fold="contest"`, so `folds.js` closes them on load and reopens a linked one).
  - Checked with JS off on the Mayor page: all 27 folds are open.
  - With JS the tab is unchanged at 3.8 screens.

## Browser QA (Playwright, preview on pm2, not restarted)

- **Matrix:** 1280 and 400 px × 3 looks × light/dark. Pages:
  - the hub;
  - the Mayor's Money tab in five states: Both, `#show=primary`, `#show=general&party=R`, `#party=D`, and the Elections tab;
  - the County Recorder's Money tab, Both and `#show=general`;
  - State House 5 with `#party=R`.
- **Result:** 108 views, no horizontal overflow, no console errors or page errors, looks and themes applied.
- **Hub map:** every shape on every layer was hovered, and each showed its office list (1/1, 9/9, 13/13, 6/6, 3/3, 9/9, 12/12, 5/5, 4/4).
- **Keyboard:** Tab runs through a layer's shapes with the panel following focus. After the last shape, focus goes into the panel's office links and then "Show its offices in the list below". Focus never fell to the page.
- **Saved place:**
  - defaults only;
  - chosen township and school;
  - Show all (127 rows back, groups closed);
  - `#g-mishawaka` (an offer only; the Mishawaka group open).
- **JS off** (a new context with JavaScript disabled):
  - hub: 127 rows visible, all groups open, map default layer drawn;
  - County Recorder Money: 7 of 7 charts visible, controls hidden;
  - Mayor Elections: 27 of 27 folds open.
- **Screenshots** are `planning/qa/phase6-shots/offices2-*.png`, 42 files:
  - each page in Ballot light at 1280 and 400, Line dark at 1280 and Wayfinding light at 400;
  - the hub in Wayfinding dark;
  - the hub with a saved place, the council, schools (SBCSC) and House layers, and JS off.

## Not verified

- **Screen reader:** none was run. The accessible names (the control group, the chart list labels, the map shapes' aria labels) were checked only in the markup.
- **Visual review was partial.** I looked at about 10 screenshots. The other combinations were checked by metrics only (overflow, console, look and theme).
- **Touch:** select-then-open on the hub map was not tested with a real touch pointer. It is `map.js`'s existing behaviour, unchanged.
- **Browsers:** Chromium only. No Safari, Firefox or real devices.
- **Full test suite:** not green, because of the other agents' work in progress (see Checks). I could not run it in a quiet tree.

## Data problems seen (not edited)

1. At least two 2024 committees mark their pre-primary-period report as "Pre-Election" on the form (Cichowicz cfl-62625, Brown cfl-62643). The guide follows the period, as the campaign pages do.
2. Kent Hizer's 2024 pre-primary report (cfl-62628) is `filer-inconsistent`. It is counted, as in the whole-cycle total.
3. Osceola's council was elected by ward in 2011 and 2019, but `offices.csv` has one at-large office. That leaves 6 contests unmatched (see the audit).
4. Seven 2026 committees can't be split because a year's figure uses a year-to-date column. The split refuses rather than guesses.

## Open questions for the owner

1. **Both = whole cycle.** For filed cycles, "Both" shows the whole-cycle chart, and the primary and general parts appear only under Primary or General (all three show with JS off). The alternative is to show the two parts side by side under Both. Keep the current choice?
2. **The Chapleau 2020 and Hurley 2016 aliases** (audit file): apply them?
3. **Osceola wards:** add ward offices to `offices.csv`, or treat the ward contests as the at-large office?
4. **`pages/county.py _contest_figure`** still draws the narrow SVG on the government pages. The government agent could switch it to `charts.results_rows`; the office pages keep a copy of its data step until then.
5. **README:** `tools/site/README.md` was not updated (it is not in my file list). It needs lines for:
   - `charts.money_rows` and `charts.results_rows`;
   - `civic/offices.py`'s split functions;
   - `static/js/offices.js`;
   - the hub map.
6. **Roadmap:** `Roadmap.md` was not touched (not in my file list).

## Follow-up fix (coordinator report): "�b7" in the hub map panel

- **Cause:** a NUL byte in `static/css/offices.css`. A Python edit turned the CSS escape `\00b7` in `.ofm-next::before` into byte 0x00 followed by "b7", so the panel showed "�b7" between the holder and "Next election".
- **Fix:** the rule is now the ASCII escape `content: " \B7  "`.
- **Search for others:** `offices.css` and `offices.js` contain no NUL or other non-ASCII bytes. The built `style.css` has no NUL. The built hub has no U+FFFD.
- **Tests:** `test_no_control_or_stray_bytes_in_offices_assets` and `test_built_hub_has_no_replacement_glyph` in `test_phase6_offices2.py`.
- **After the fix:** rebuilt with `--check` (PASSED); the 19 tests pass.
- **Browser:** on the County council, Townships and School corporations layers, the separator renders as " · " with no "�" or "b7".
- **Screenshots** `offices2-hub-council-layer-*`, `offices2-hub-townships-layer-*` and `offices2-hub-schools-sbcsc-*` were re-taken. The earlier council-layer shot predated the fix.
- **Aliases:** the Chapleau and Hurley aliases remain unapplied, pending review.
