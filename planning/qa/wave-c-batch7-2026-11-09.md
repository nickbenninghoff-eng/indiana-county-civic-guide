# Wave C, batch 7: after the map work, 2026-11-09

This batch is the follow-up redesign of the four pages that got map-click navigation:
- `county/`
- `schools/`
- `state/your-legislators/`
- `money/budgets/`

The spec is `site-ux-review-2026-11-09.md` §3.3, the budgets part of §3.5, patterns P1, P3 and P5, and the batch 7 row. Nothing is committed.

Checks, all run at the end:
- `python -P -E tools/site/build.py --edition st-joseph --check` ends **PASSED** (113 pages).
- `python -P -E -m unittest discover -s tools/tests` gives **277 OK**. 18 of those are new, in `tools/tests/test_wave_c_batch7.py`.
- `python -P -E tools/check_gov.py` reports **0 errors**.
- `python -P -E tools/check_money.py` reports **OK**.

One mid-run checker failure ("data/results/index.html: missing viewport meta") came from another agent's files. It passed on the rerun. I did not touch those files.

## 1. What changed

### county/
- **"More about" rail.**
  - The map link to "Treasurer, 2024" is gone. The county has no head office, so the "latest county race" stood for nothing.
  - The rail now shows, in order:
    - Campaign money: county races
    - Campaign money: judges' races (`money/campaigns/courts/`)
    - Budget
    - Tax rate
    - Who lives here
    - Your state legislators
    - School boards
    - History: party control over time (`history/#control`)
    - Run for county council
    - 2028 on the calendar
- **Recent results, grouped by district (pick_one).**
  - Each of the 3 commissioner and 9 council seats is one item, `#results-<office id>`.
  - Its key is the office id: the same key as its officeholder line and its map district. So picking District C on the map opens both the officeholder line and its result.
  - When collapsed, an item reads, for example: "Nov 3, 2026 (unofficial): Jan Cervelli (D) 51.8% elected, James A O'Brien (R) 48.2%". Candidates are in ballot order.
  - When opened, it shows the chart (same `#res-<contest>` id) plus links to the results explorer (P10) and the precinct map.
  - A seat that was not on the 2024 or 2026 ballot says so, with its next election and a link to its last result in the explorer.
  - The turnout lines are kept as a two-item list.
- **Countywide offices** (row officers, prosecutor, Probate and Circuit judges):
  - one row per race in `#results-countywide`: candidates in ballot order with votes, share and "elected"; status; Chart · Explorer · Map;
  - every chart sits in the "See all 10 countywide result charts" fold (`#results-charts-county`).
- **How it's organized.**
  - The lawsuit text (about 2,400 characters) was printed twice: the commissioners' and the council's office notes carry the same text.
  - It is now printed once, in the fold "Litigation over the district elections, as of Nov 7, 2026" (`#litigation`), with both offices' citations.
  - The council's rule points to it.
- **Party control.** The current breakdown stays visible, with a line linking to the History page's `#control`. Both charts, each with its table view, are in the fold "Seat-by-seat charts: County Council 2011 to 2027; Board of Commissioners 2009 to 2027" (`#control-charts`).
- **Money in and out.**
  - The intro, the budgets link and the tax-base line stay visible.
  - The state-report charts are in `#money-flows-county`, as on the place pages. Its summary line gives the counted spending and income.
  - This stays the county's own page for these figures (review (d)).

### schools/
- **Seat lists (P5).**
  - Each corporation's old "Board seats and how they are elected" table and its member cards are merged into one line per seat (`civic/holder_rows.py seat_row`): seat · who votes · holder (party label as printed) · term end and next election, plus any incoming 2026 winner.
  - Each line opens to the full card fields and sources, and keeps the card id `office-<id>`.
  - Seat lines are plain folds inside the corporation's item, not pick_one keys. So the "corporations" state line stays right, and a link to `#office-phm-board-madison` opens PHM, then that seat.
  - Seats with a source conflict keep the conflict card.
  - The old seats table (same id `seats-<uid>`) is in "See all N seat groups as a table".
- **Who votes: corrected in code, from the guide's own results** (`_residency_evidence`, `_who_votes`). The old page said "Voters in Harris Township" and so on. The data says otherwise for every corporation with named seats:
  - **PHM:** the Madison Township seat drew 11,269 votes in 2026 (and 11,421 in 2022), while about 1,891 people live in Madison Township (ACS 2020-2024, COM-001). The corporation's page names the seats by residency (MAP-033), and the 2024 ballot labels fit (MAP-037).
  - **John Glenn:** the Johnson Township and Polk Township seats are named for townships outside the county, yet the county's canvass counts votes for them (1,648 in 2024; 2,054 in 2026).
  - **LaVille:** the North Township seat is outside the county; 716 county votes in 2026.
  - **New Prairie:** the 2026 ballot labels District 2 "(Hudson, Wills Townships)", both outside the county; 897 county votes.
  - **The wording now reads** "All voters in the corporation; the member must live in Harris Township".
  - **One evidence note per corporation** gives the facts with their citations and a COMPUTED badge ("inferred from the vote counts; the statute section and the corporation's plan were not read"). A Gaps row records that the statute and plans were not read.
  - **SBCSC:** its numbered districts stay "Voters in District N" (MAP-031: five members elected by district, two at large).
  - **Map panel.** The map panel's "How they are chosen" uses the same rule.
- **Board district layers.**
  - **No layer was added: none has a shape.** SBCSC's map is an image-only PDF (MAP-031/032). PHM's (and the others') seats are residency seats voted corporation-wide, so drawing townships as "your board district" would mislead.
  - **SBCSC lists its districts instead.** It gets a note: the 5 districts are voting districts, listed and not drawn, because the corporation publishes only an image of voter precincts (SB1 to SB5) with no boundary file, and the guide never traces one by hand.
- **A rail per corporation (P1), with an h3 inside its item.** It shows:
  - the latest board result (explorer);
  - campaign money (school board races);
  - budget;
  - tax rate;
  - "Public questions: Referenda, by jurisdiction" (`elections/judges-and-questions/#questions`; only for corporations with questions in the data);
  - run for school board;
  - next election.

  I linked the questions page's stable section id, not batch 5's per-question ids, which were still being edited.
- **Folds.** Each corporation's state-report money charts are in `#money-flows-<uid>`, the target of the budgets page's new links.

### state/your-legislators/
Inside each district's item:
- the member card, then the 2026 county-portion chart;
- a **rail** (`#related-house-7` …): latest result, on the map, next election. Campaign money is left out of the rail because the money block below links it;
- **results:** one row per general election (`#results-<k>-summary`): candidates in canvass order with votes, share and the result as recorded, plus "What the votes cover" (the county-portion caveat on every row) and status. The old per-candidate table (`#results-<k>-table`) is in "See all N result rows";
- **campaign money:** one line per committee (role, latest two filing years, status, citations), the filing-year basis note, links to "Every district's committees" and to `money/campaigns/state-legislature/`. The old table (`#cf-<k>`) is in "See all N filing-year rows".

In section 4, the all-district chart stays visible. The committee matrix (`#cf-matrix`, kept per the map batch's Q4) and the every-row table (`#cf-long`) are each in a See-all fold.

### money/budgets/
- **Chips for the units with no boundary.** There are 11, as the map's "no boundary" table counts them, and they sit right under the map:
  - the county (the whole county);
  - 4 libraries;
  - Transpo, SB Redevelopment Commission, Airport Authority, Solid Waste;
  - Regional Water and Sewer and the Redevelopment Authority (these two have only money-in-and-out blocks).

  Each chip is an in-page link that chooses the unit (`civic/pick_one.py one_chips`). The two flows-only units' articles got ids `flows-<anchor>` with `data-one-for`.
- **Per-unit flows (review (a)).**
  - Each unit's budget item now ends with one line: "Money in and out: counted spending … in 2025; counted income …", noting that its scope differs from the adopted budgets.
  - That line links to the full charts on the unit's own page: `county#money`, `places/<id>#money-<id>`, `schools#money-flows-<id>`, or the item below for libraries and special units.
  - The 2024 breakdown blocks for the county and the two cities also link to their own page's money in and out.
- **Debt.** The summary chart stays. The 105-row table is a See-all fold (`#debt-classes-all`, `pick_one.one_wrap_see_all`) that still opens for the chosen unit, shows only that unit's rows, and copies them ("Copy 3 shown rows").
- **Unchanged.** "Show all units" (the escape hatch) and "Comparing units" are as they were.

## 2. Screens (height ÷ 800; before = the build at the start of this batch)

| Page | Collapsed 1280 | Collapsed 400 | One open 1280 | One open 400 | JS off 1280 | JS off 400 |
|---|---|---|---|---|---|---|
| county | 22.9 → **15.2** | 36.9 → **23.4** | 23.1 → **15.8** (Council A) | 37.4 → **24.2** | 38.7 → 42.8 | 58.4 → 61.6 |
| schools | 4.7 → 4.7 | 6.6 → 6.6 | 10.0 → **7.4** (PHM) | 16.1 → **10.6** | 38.9 → 48.2 | 61.5 → 75.4 |
| your-legislators | 8.6 → **7.4** | 11.4 → **10.3** | 11.5 → **9.5** (HD7) | 15.0 → **13.3** | 34.2 → 51.0 | 45.5 → 66.4 |
| budgets | 17.5 → 17.8 | 23.0 → 23.7 | 25.2 → 25.7 (South Bend) | 33.7 → 34.6 | 95.1 → 98.8 | 133.4 → 138.5 |

County sections at 1280, before → after:

| Section | Before | After |
|---|---|---|
| How it's organized | 2.8 | 1.3 |
| Party control | 2.4 | 0.5 |
| Recent results | 3.9 | 2.5 |
| Money | 3.3 | 0.35 |

**Budgets.**
- It grew by about 0.3–0.9 screens: the chips plus one flows line per unit.
- Its big cuts came in the map batch (80.7 → 17.5). This batch's budget asks were navigation and links, not length.

**With JavaScript off,** pages are longer: every fold ships open, and the new summary rows, rails and evidence notes sit next to the full tables they summarize. Nothing is hidden. The only closed `<details>` with JS off are the nav menus and the charts' existing "Show table" views.

## 3. Rules kept
- **Anchors.** Every one of the 1,404 ids the four pages had is still on its page (`tools/tests/fixtures/anchors_before_batch7.json`), with no duplicate ids. Old links such as `#cf-senate-9`, `#office-phm-board-madison`, `#transpo` and `#litigation` land on the right item, opened (browser-checked).
- **Text diff, old against new.** The only missing strings are:
  - the nav labels (another agent's shell change);
  - the three renamed headings ("Board seats and how they are elected", "Current and incoming members", the debt fold title, the cf-long button);
  - the reworded turnout lines;
  - the dropped "Treasurer, 2024" rail link;
  - the corrected "Voters in <X> Township" lines;
  - two source-count numbers.
- **Nonpartisan.** No new fills; the chips and folds use only neutral tokens. Party colors appear only in the existing `results_bars`. Candidates stay in ballot or canvass order, and seats stay in office and district order.
- **Every fact still carries its citation.** The evidence notes cite the results rows and the population row they use.

## 4. Browser checks (Playwright, own contexts)
- **Matrix.** 4 pages × 3 looks × light/dark × 1280/400 = 48 loads. The look and theme applied every time, with no horizontal overflow and no console errors.
- **Keyboard.** On county Council C: focus, Enter (panel), Enter again. The address becomes `#office-county-council-c`, and both `office-county-council-c` and `results-county-council-c` open. The state line reads "Showing County Council, District C…".
- **Chips.**
  - Transpo: only its items open; the debt fold opens with 3 rows and reads "Copy 3 shown rows".
  - The flows-only chip lands on its block.
  - Show all opens all 54 items.
- **Deep links and JS off.**
  - `schools#office-phm-board-madison`: PHM opens, the seat line opens, SBCSC stays closed, and the seat is at the top of the screen.
  - JS off: every `data-fold` and `data-one` item is open, every one-bar is hidden, and no row is hidden.
- **Screenshots** are in `.playwright-mcp/c7-*.png`: county rail and results at 1280; county results at 400 (line, dark); schools PHM at 1280; SBCSC at 400 (wayfinding, dark); legislators HD7 at 1280; budgets map and chips at 1280 and 400 (ballot, dark).

## 5. Data note: `school-new-prairie`
- **The file is hand-maintained.**
  - No tool writes `derived/unit_id_aliases.csv`: only readers reference it (`civic/data.py`, `related.py`, `tax_base.py`, `money.py`), and no tool in `tools/` generates it.
  - It dates from the initial commit, and its notes say "mapped to units.csv by name".
  - `SCHEMA.md` does not describe the `derived/` files.
- **Fix.**
  - I added the row `school-new-prairie,new-prairie,` after `school-union-north`. That is the only data edit.
  - I removed the workaround `EXTRA_UNIT_IDS` from `civic/tax_base.py`, `pages/money.py` and `civic/related.py`, and updated the test comment in `test_tax_base_schools.py`.
  - The build warning no longer lists `school-new-prairie` as unmapped.
  - A test pins the alias and that `EXTRA_UNIT_IDS` is gone.

## 6. Questions and notes for the main session
1. **The seat wording now covers every corporation with named seats,** not only PHM, because the same code made the same claim for all of them, and the guide's own counts contradict it for John Glenn, LaVille and New Prairie too.
   - New Prairie's District 1 and 3 seats are labelled corporation-wide by extension from District 2; the note says so.
   - The statute and plans are a Gaps row.
   - Should someone read IC 20-23-4 plans to confirm?
2. **The `offices.csv` notes and titles still say "Harris Township" and so on.** That is correct as a seat name, so no CSV change is needed.
3. **New Prairie's 2026 contest "At-Large / District 2"** is a ballot oddity already noted in `offices.csv`; it is not touched.
4. **County page default state.** It still loads collapsed. A saved-place preselect is batch 8.
5. **I did not update** `Roadmap.md`, `docs/session-handoff.md` or the redesign plan's status line; that is left to the main session.

## 7. Files
New:
- `tools/tests/test_wave_c_batch7.py`
- `tools/tests/fixtures/anchors_before_batch7.json`
- this report

Changed:
- `tools/site/pages/county.py`: rail, litigation fold, results by district, control and money folds, helpers
- `tools/site/pages/state.py`: legislators per-district results summary, money lines, rail, matrix folds
- `tools/site/pages/money.py`: chips, per-unit flows lines, debt fold, flows ids; workaround removed
- `tools/site/pages/places.py`: **schools functions only** (`build_schools`, `_school_board_facts`, new `_who_votes` / `_residency_evidence` / `_seat_basis_note` / `_school_rail` helpers) plus two import lines; the place template is untouched
- `tools/site/civic/pick_one.py`: additive (`one_wrap_see_all`, `one_chips`)
- `tools/site/civic/holder_rows.py`: additive (`seat_row`, `term_end_text`)
- `tools/site/civic/related.py`:
  - additive: `related_rail`, which `related_links` now calls (same markup);
  - the removal of the two `EXTRA_UNIT_IDS` lines
- `tools/site/civic/tax_base.py`: removed `EXTRA_UNIT_IDS` (the New Prairie workaround)
- `tools/site/static/css/pick_one.css`, `money.css`, `state.css`: additions only
- `data/editions/st-joseph/derived/unit_id_aliases.csv`: one row
- `tools/tests/test_map_navigation.py`: the debt-fold regex now matches the See-all markup
- `tools/tests/test_wave_a_patterns.py`: the rail test also builds the county rail's added targets
- `tools/tests/test_tax_base_schools.py`: one comment
- `tools/site/README.md`: notes on the three helper rows
