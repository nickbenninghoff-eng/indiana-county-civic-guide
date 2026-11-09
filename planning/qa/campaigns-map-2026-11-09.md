# Campaign finance reorganized by place: map, area pages, whole-campaign totals (2026-11-09)

Status: built and verified (build --check PASSED, 114 tests OK, check_gov 0 errors, browser checks below). Nothing committed.

## What was built

| Page | What's on it |
|---|---|
| `money/campaigns/index.html` (225 KB, was 384 KB) | Short intro, "money is not support" note, quick links; **map by place** with a race-type row (County, City, Town, Township, School board, Courts, State legislature) and, where a type has district maps, a second row (e.g. County: Countywide offices / Commissioner districts / Council districts; City: Cities / Council districts; State: House / Senate districts); side panel; **Every area** list grouped by race type (filtered with the map when JS is on); short "About these figures" with anchors `#obligations`, `#public`, `#method` kept for inbound links |
| `money/campaigns/<area>/index.html` (30 pages: county, courts, 2 cities, 7 towns, 13 townships, 6 school corporations) | Breadcrumb "Campaign finance › <area>", latest-election summary (spent, raised, by party, record), then each election newest first → each race → candidates in ballot order with whole-campaign spent/raised/cash and reports on file vs expected → collapsible table of every report (with "in the totals" column and notes), the existing like-for-like "same report, same period" pre-election comparison for that area's races, other reports for its offices (other cycles / offices with no race), its large contributions |
| `money/campaigns/state-legislature/` | cf_state by district and filing year, labelled as a different basis (not race totals) |
| `money/campaigns/other-committees/` | The 47 filings in no race: party/PAC/issue committees (30), no office written (12), no office sought (3), office named but no government (2), each committee by cycle with the same sums |
| `money/campaigns/how-it-works/` | All the old explainer sections (reporting, CFA-4, report types, CFA-11, what's public, method + status badges, coverage matrix, delinquent filers, full Gaps) plus a new "How the guide adds up a campaign" section |
| `money/campaigns/all-filings/` | The full every-filing explorer (moved as is) and the large-contribution table |

Nothing was lost: every former section has a home (explorer → All filings; races → area pages; large → All filings + each area page; delinquent, coverage, method, gaps → How it works). A test checks that each of the 479 cf_local rows is placed exactly once.

**CSV:** the site contract forbids file downloads (`check.py` rejects `<a download>`; README: "no downloads"). So "All filings" keeps the guide's **Copy CSV** button ("Copy CSV of the rows shown"; choose all cycles/offices to copy every filing), and the raw file is also on the data pages. No download link was added.

**Inbound links:** `about/` now points to `how-it-works/#method` (meta.py, the one link the coordinator cleared). The learning-path stops `#obligations`/`#public` now land on how-it-works (sitemap PATHS). `run/` still links to `index.html#obligations`, which still exists (short version + link). Status badges on all campaign pages link to how-it-works `#method`.

## Design choices (for Nick to confirm)

- **Filter = map layers.** The race-type row picks the layer group; map.js's own tab row shows only that type's layers (hidden when a type has one layer). Default view: County › Countywide offices (first in your list).
- **Shading:** total reported spending by all candidates for the area's (or district's) **latest election**, natural breaks per layer, the single teal ramp (`civic/shading.py`, `cmap-mm-*`). Hatched = no reports on file or no race (never shown as $0). Layers mix years where areas' latest elections differ (e.g. towns 2023 vs 2026); the legend names the years and the panel names the election.
- **Incomplete marking:** 90 of 111 races are incomplete (mostly candidates with no reports at all), so a visual mark on shapes would be noise. Instead: legend line "N of M shaded areas have an incomplete record… a floor, not a final total", "(incomplete)" on each race bar and candidate bar, and the Record fact in the panel with the reasons.
- **State districts are not shaded** (neutral fill): cf_state is filing-year totals for listed committees only, not race totals. Panel shows each committee's last two filing years with the basis caveat and the district's share of the county area; "drawn only inside the county" is stated.
- **Panel bars:** a district or single-race area shows candidates (ballot order, share of the race total, whole dollars); a multi-race area shows races (office order). Never sorted by money.
- **Area total = latest election only.** County panel: 2026 races; the 2024 county races are on the page ("Also on its page: 10 races last held in 2024").
- **District layers:** driven by `sources/boundaries/districts/manifest.csv` through new `tools/build_district_shapes.py` → `data/editions/st-joseph/derived/district_shapes.json` (50 KB), same projection, clip rectangle and shared-arc simplification as `tools/build_map.py` (imported from it); the site refuses the file if its viewBox no longer matches `map_shapes.json`. A set matches races by `office_pattern` with `{d}` and its first/last election years. Sets without a file (SBCSC, Walkerton wards, PHM, other towns) degrade to "listed under the parent area" with a note saying why; the PHM residency-seat note is on the PHM page and in the school legend. Set caveats from the research (county 2022 settlement maps; SB Ord. 10906-22 for 2023; Mishawaka "current" districts, medium confidence; state districts clipped) appear in the legend and panel; MAP-020..030/034 cited under the map. Rerun after new files land: `python -P -E tools/build_district_shapes.py --edition st-joseph`.

## How totals are computed (civic/campaign_money.py; published on how-it-works #adding; source CFM-010)

Money is integer cents throughout.
1. **Race** = a contest on the 2023/2024/2026 general ballot (plus that office's primaries). Candidates = general + primary candidates, plus committees that filed for the exact office in the cycle with no ballot line. Each committee-cycle counts in one race only (tested).
2. **Cycle** per the cf_coverage rule (`cycle_of`, now single-sourced; pages/campaigns.py imports it). Each report gets a **slot** from its period vs the primary/general dates (prior-year annual, pre-primary, pre-election, year-end); a mismatch with the marked box is noted (e.g. Candace Brown's three "Pre-Election" boxes).
3. **Amendments** replace the report they amend (same slot, overlapping period). cf_local already merges them; the code still guards and is tested.
4. **Overlaps:** cash chaining wins (dates overlapping but opening cash = prior closing cash → back to back, noted); a report whose period lies inside another's is not added again (real case: Kris Verash's pre-primary inside his full-year final); an untangleable overlap gives no committee total (none in the data).
5. **Per calendar year:** if the reports on file cover the year from Jan 1 with no gap → sum of "this period" columns (a different YTD is noted, e.g. Cichowicz: YTD omits his first report). Otherwise, if the year's latest report reconciles → its **year-to-date** column. This matters a lot: the county posted no 2023 pre-primary/pre-election reports, so 2023 annual "this period" columns start in the fall — Mueller's 2023 period column is $85,493 but his YTD (whole year) is $610,625. 24 committee-years use YTD, each noted. If the latest report doesn't reconcile → period sum, noted.
6. **Expected reports** from cf_coverage expected_report_types, adjusted: general candidates with no primary line aren't expected to file pre-primary; primary-only not pre-election; no-ballot-line committees only the annual; nothing after a final. Any expected report missing, a blank line, an unreadable scan, or a candidate with no reports → race **incomplete**. "Not on file", never "late".
7. **Cash** = latest report's closing cash only if VERIFIED/DERIVED.
8. **Matching** reuses the old surname/given/nickname rule (now in civic), plus: one-letter surname slips and surname-first forms when unique ("Matthew Mammolent" → Matt Mammolenti; "McCormick Thomas Eric, aka Tom" → Tom E McCormick); "(not stated)" filings join only on a full name match.

## Tests (tools/tests/test_campaign_money.py)

Synthetic: cents/usd, cycle rule, slots (incl. year-only dates), full cycle sum, amendment replaces, contained report, chained overlap, tangled overlap → None, 1-day overlap, YTD used/not used/overridden, expected-by-ballot-line, final, blanks, cash only when clean, name matching, contest mapping. Real data: **every candidate, race and by-party total recomputed independently from the raw cf_local.csv text with Decimal** from each committee's recorded basis (row ids + column) and compared to the cent; area totals = latest races; every filing placed once; no filing counted twice; no two counted reports in one slot contain each other; listed filings' cycles follow the rule; no-reports races have no total; the map panel's "Spent" fact and shading value equal the model for every race shape and area shape; shades only ramp/none; district layers degrade with no or empty shapes. Suite: 114 OK.

## Browser checks (preview :8787, rebuilt; screenshots in .playwright-mcp/cf-*.png)

1280 and 400 px × light/dark × Ballot/Line/Wayfinding on the index, county and state pages, plus all other campaign page types in Ballot light/dark: no horizontal overflow, no console errors. Hover and keyboard focus fill the panel and draw the highlight (focus stroke 3px); Tab moves through shapes; Enter on a type button switches layer and filters the list; "Show every race type" restores it; synthetic touch tap selects (panel stays, no navigation), second tap opens. JS off: list shows all 7 groups with 33 links (every area page), map default layer's shapes are links, area pages show every race (South Bend: 9 races, 19 report tables).

## Data issues found (not edited)

- cf_local `cfl-73119` (Dvorak for Prosecutor, doc 73119): Annual with period 2026-01-01 to 2026-12-31, posted before the year ended — probably the 2025 annual misdated. Flagged on the page ("ending after the date the data was built"). `cfl-68014` (Pemberton, New Carlisle) is the already-known 2026-period-in-2025-batch case.
- `cfl-66448` (George L Jones, SBCSC at-large): period written as year only "2024 to 2024".
- Name spellings on forms vs ballot: "Matthew Mammolent" (ballot Mammolenti); "McCormick Thomas Eric, aka Tom" (surname first). Matched, with "Name on the form" shown.
- YTD columns that disagree with complete period sequences (22 committee-years), e.g. Cichowicz 2024 YTD $203,940.28 vs reports $207,956.46 (YTD omits his Jan–Mar report); Sharon Banicki 2024 YTD $9,843.28 vs $22,652.64 (filer-inconsistent).
- Henry Davis Jr (2023 SB mayor primary), Kate Voelker, Sonia Perez and many board candidates: no committee filings under the office (reported as "no reports on file").
- Matt Clayton: committee filed for County Council B (primary), then on the general ballot for Clay Township Trustee; his money counts in the Council B race only. Michelle Shaw: only a no-office filing.
- Carolyn Richardson Freet (2024 recorder committee, D) matches no ballot candidate (Carolyn Topolski was on the ballot) — possibly the same person under another surname; not merged.

## Files

New: `tools/site/civic/campaign_money.py`, `tools/site/civic/campaign_map.py`, `tools/site/pages/campaign_pages.py`, `tools/site/static/js/campaigns_map.js`, `tools/build_district_shapes.py`, `data/editions/st-joseph/derived/district_shapes.json`, `tools/tests/test_campaign_money.py`, this report.
Changed: `tools/site/pages/campaigns.py` (index → how-it-works + all-filings builders, shared cf_all/crumbs/doc_link/cf_badge_short, helpers single-sourced), `tools/site/civic/sitemap.py` (campaign entries hook; two path stops → how-it-works; index description), `tools/site/static/js/map.js` (two additive, backward-compatible changes: bar amount optional; highlight reads the shape's path when an entry omits `d`), `tools/site/static/css/campaigns.css`, `tools/site/pages/meta.py` (one link), `data/editions/st-joseph/sources_cf_method.csv` (+CFM-010), `Roadmap.md` (one line).

## Open questions for Nick

1. Default view: County › Countywide offices (one big shape). Prefer Townships or Cities as the opening layer?
2. Mixed election years within a layer (towns 2023 vs 2026; county districts 2024 vs 2026): OK, or shade only areas whose latest election is the most recent one?
3. YTD rule for years not fully covered (mainly 2023): OK to show the filer's year-to-date figure (noted), rather than the much smaller sum of the reports on file?
4. Expected-report adjustments (no pre-primary for general-only candidates, etc.) go beyond cf_coverage's flat list. Keep, or apply the flat list (which would mark more races incomplete)?
5. County area page is large (~490 KB, 21 races + 80 other-cycle reports). Split county into countywide / commissioners / council pages?


---

## Part 3: nested-period / YTD correctness fix (Eli Wax case), 2026-11-09

### The bug
The South Bend District 5 panel showed Eli Wax at $61.63 and "Republican (R) $61.63". The root cause was in `year_figure`, not in the stack rule. Two of his reports were involved:

- **Doc 60837:** the real 2023 annual. Its start date is blank, it reports $30,287.82 spent, and its closing cash is $1,731.53.
- **Doc 66082:** dated 1/1/2023 to 12/31/2023. It reports $61.63 spent, and its opening cash is $1,731.53.

Both were "counted". But the year wasn't covered from January 1 (60837 has no start date), so the year's figure came from the year-to-date column of the "latest" report by date sort. That was 66082, so its $61.63 replaced $30,287.82 of real spending.

The same shortcut erased money in two other ways:
- A latest report's YTD was *smaller* than the reports on file (Dieter, Young Republicans).
- The old "inside" rule dropped a report whose money the outer report didn't contain (Verash).

### Root fix (tools/site/civic/campaign_money.py)
1. **Cash chains are sequential.** When one report opens with the non-zero cash another closed with, they are two periods, whatever the dates say.
   - If their dates nest, or the later one doesn't end later, both are counted. They are flagged `date-conflict`, with a note on each report. This applies in either direction.
   - A zero balance proves nothing, but a 0 = 0 chain with nested dates still drops nothing. Both are counted and flagged (rule 1 taken literally); nothing is dropped on a guess.
   - An ordinary chain whose start date overlaps a little (Gary Fox, 11 days) is still counted back to back with the old note. It is not a conflict.
2. **A blank period_from is never "inside".** `_contains` needs all four dates, so a blank start never contains another report and is never contained.
3. **Date-correcting notes are followed only when explicit** (`date_fix`). The CSVs are untouched, and `cycle_of`/`effective_year` stay as written, so the coverage matrix still matches build_cf_local.py. The money model reads dates through `money_year`, `money_cycle`, `_pf` and `_pt`.
   - Doc 66082's note says "the year is probably miswritten for 2024". The money model shifts its period to 2024, so it now sits in the 2024 cycle under South Bend's "Other reports" (there is no 2024 council race).
   - Doc 72875's note says "From date handwritten 4/11/2024 (likely typo for 2026". Its start reads 4/11/2026.
   - Notes about slips the transcriber already fixed in the CSV (60855, 70523) change nothing.
   - A note that only doubts a year (68014, "likely year typo") keeps the dates and flags `date-doubt`.
   - Each case is visible in four places:
     - a line in the candidate's row on the area page (`.cf-date-note`);
     - a full note under the reports table;
     - a caveat in the map panel (`date_caveats`);
     - for conflicts and doubts, a reason in the race's incomplete list.
4. **A report is dropped only when it is truly redundant:**
   - an amendment (never across a non-zero cash chain);
   - the same report filed twice (same period, same figures), with reason `duplicate`;
   - a report wholly inside another whose figures include its money (`_covers`: at least as much raised and spent).

   Every drop is recorded in the summary's `drops` (id, why, by). The races now have **0 drops**.
5. **The YTD shortcut is guarded** (`year_figure`). It is never used in two cases:
   - The YTD figure is below the sum of the year's reports on file. The flag is `ytd-low`, and the period sum is used with a note.
   - Any of the year's reports is in a date conflict. The period sum is used, and the YTD is quoted in the note.

   For cash on hand, the "latest" report follows the cash chain past the date-latest report.

The pages, map, how-it-works text and gaps changed to match:
- **campaign_pages.py:** `money_cycle`/`money_year`, a WHY entry for "duplicate", `_date_subs`, and the party text.
- **campaign_map.py:** `_party_line` and `date_caveats`.
- **campaigns.py:** the how-it-works rule text and the "Report periods that look miswritten" gap are updated. A new gap, "Reports whose dates disagree with their figures", covers docs 66176, 65671 and 65634.

### Audit: every report whose treatment changed (old rule to new rule)
I snapshotted all 479 cf_local filings before and after: race groups, area-other groups and other-committee groups. Only the reports below changed. No other report, race total or party total moved.

| Filing | Candidate / committee | Spent (period col.) | Old treatment | New treatment |
|---|---|---|---|---|
| cfl-60837 | Eli Wax (SB council 5, 2023) | $30,287.82 | "Covered by" 66082's 2023 YTD ($61.63), so effectively dropped | Counted (its own 2023 YTD = its period) |
| cfl-66082 | Eli Wax | $61.63 | Counted in the 2023 race via its YTD | Counted in the 2024 cycle (explicit note), listed under South Bend "Other reports" |
| cfl-62629 | Kris Verash (County Council F, 2024) | $4,945.21 | Dropped "inside" final 66176 | Counted: 66176 reports $0 spent, so it can't contain this report; `date-conflict` flagged |
| cfl-64452 | Derek D. Dieter (County Surveyor, 2024) | $45,026.52 | "Covered by" 65634's YTD ($1,874.78), so effectively dropped | Counted: the YTD is below the reports on file (`ytd-low`), so the sum is used |
| cfl-65634 | Derek D. Dieter | $1,874.78 | Its YTD stood for the whole year | Counted by its period column |
| cfl-64455 / cfl-65637 | Gary Fox (PHM Harris) | $4,720.42 / $1,529.42 | YTD of 65637 ($6,249.84) | Period sum, $6,249.84. The totals are unchanged to the cent ($6,249.84 / $9,050.00); only the column the basis names changed. |
| cfl-64476 / cfl-66220 | St. Joseph County Young Republicans (other committees) | $650.00 / $0.00 | 66220's YTD ($0.00) erased $650 | Period sum, $650.00 (`ytd-low`) |
| cfl-60881 | Rudy Monterrosa (Greene Twp, other reports) | $505.01 | Own YTD ($337.97, because the period starts before Jan 1) | Period column, $505.01 (`ytd-low`; the note says the period can start before Jan 1) |

In several other cases a report was covered by a later YTD equal to the period sum, so no money moved. These are unchanged: Fisher 64454, Mitchell 64481, Chaffee 64453, Sniadecki 64480, Kruszynski 70552 and Searfoss 70557.

All three race totals that changed had real money dropped before:

| Race | Old spent / raised / by party | New |
|---|---|---|
| 2023g-south-bend-council-5 | $9,416.01 / $1,700.00 / D $9,354.38, R $61.63 | $39,642.20 / $26,456.35 / D $9,354.38, R $30,287.82 |
| 2024g-county-surveyor | $12,076.51 / $12,141.73 / D $10,201.73, R $1,874.78 | $57,103.03 / $59,065.76 / D $10,201.73, R $46,901.30 |
| 2024g-county-council-f | $19,208.32 / $20,365.52 / D $2,707.98, R $16,500.34 | $24,153.53 / $25,934.00 / D $2,707.98, R $21,445.55 |

One area total changed: South Bend's latest election, from $785,024.60 to $815,250.79 spent, with R going from $61.63 to $30,287.82. Every other race, area and party total is identical.

Flags now in the races:
- `date-read`: 1 (Wax).
- `date-conflict`: 2 (Verash, and McCullough, whose two reports were already both counted and are now visibly flagged).
- `ytd-low`: 1 (Dieter).
- `ytd-used`: 22. Each has a YTD at least as large as the reports on file, which a real-data test now enforces.

**Data issues to report (CSVs not edited):**
- 66082 is probably Wax's 2024 annual; the county should confirm.
- 66176 (Verash final) doesn't reconcile, and reports $0 spent for a whole year that includes a $4,945.21 pre-primary.
- 65671 (McCullough annual) starts the same day as his pre-election report and repeats its $2,260.86 spent. It may be cumulative, in which case the race double-counts $2,260.86. This is flagged, not guessed.
- 65634 (Dieter annual) has a YTD equal to its own period.
- 72875 (Shaw) has a slip in its start date.

### By party is now safe
Each party's sum says how many of that party's candidates in the race it covers (for an area, the candidates in its latest election's races). The same `party_parts` helper drives both the panel and the pages.
- Example: "Democrat (D) $9,354.38: 1 of 2 candidates with reports; Republican (R) $30,287.82: 1 of 1 candidate with reports".
- A party with candidates but no added reports reads "Republican (R): no reports added for its 1 candidate".
- Candidates whose reports can't be added up are counted separately ("(1 more with reports that can't be added up)").

The how-it-works by-party paragraph explains this.

### Tests (tools/tests/test_campaign_money.py): 127, all OK
New synthetic tests:
- `test_wax_cash_chain_with_nested_dates_counts_both`: no note, so both are counted, no YTD is used, and cash comes from the chain end.
- `test_wax_note_naming_the_year_moves_the_report`
- `test_cash_chain_is_sequential_even_when_dates_nest`: forward and reverse chains, plus an ordinary small overlap that is not a conflict.
- `test_zero_balance_chain_with_nested_dates_drops_nothing`
- `test_blank_start_never_puts_a_report_inside_another`
- `test_ytd_below_the_reports_on_file_is_not_used` (Dieter)
- `test_contained_report_whose_money_the_outer_lacks_is_kept` (Verash)
- `test_same_report_filed_twice_is_added_once`
- `test_date_fix_reads_only_explicit_corrections`
- `test_party_line_says_how_many_candidates_it_covers`

New real-data tests:
- `test_wax_counts_his_2023_annual`: $30,287.82; R $30,287.82; 1 of 1; 66082 under South Bend's other reports.
- `test_no_real_report_dropped_or_erased_by_a_ytd_figure`: every uncounted report has a recorded drop, every "inside" drop is covered, and every YTD basis is at least the period sum.
- `test_party_counts_cover_every_candidate`

Updated tests:
- `test_cycles_follow_the_rule` uses `money_cycle`. It allows a difference from the written cycle only for an explicit year note.
- The double-count test exempts pairs flagged `date-conflict`, which are counted on purpose.

### Checks
- `python -P -E tools/site/build.py --edition st-joseph --check`: 109 pages, **PASSED**.
- `python -P -E -m unittest discover -s tools/tests`: **127 tests OK**.
- `python -P -E tools/check_gov.py`: **errors=0** (the 23 warnings were already there).
- Playwright on localhost:8787 at 1280 and 400 px, light and dark, in the ballot, line and wayfinding looks. There were no console errors and no horizontal overflow in any run.
  - **Map:** City, then Council districts, then District 5 (hover at 1280, touch and focus at 400). The panel shows $39,642.20 and "Democrat (D) $9,354.38: 1 of 2 candidates with reports; Republican (R) $30,287.82: 1 of 1 candidate with reports", plus the Wax date caveat. $61.63 no longer appears.
  - **Area page** (/money/campaigns/south-bend/#r-2023g-south-bend-council-5):
    - The race shows $39,642.20 spent and $26,456.35 raised, and the party line has the counts.
    - Wax's row shows "Doc 66082 is counted in the 2024 cycle…" and cash of $1,731.53.
    - The reports fold toggles with Enter.
    - "In the totals" reads "Yes (its 2023 year-to-date column)" for 60837.
    - 66082's 2024 block shows $61.63 spent and $1,669.90 cash.
  - **JS off, 400 px:** the area page shows the party counts and the moved-report line, and the index areas list renders. No overflow.
  - Screenshots: `.playwright-mcp/cf-wax-panel-{1280,400}-{light,dark}.png` and `.playwright-mcp/cf-wax-area-{1280,400}-{light,dark}.png`.

Files touched in this pass:
- campaign_money.py
- campaign_map.py
- campaign_pages.py
- campaigns.py (how-it-works text and gaps only)
- campaigns.css (one rule)
- test_campaign_money.py
- this report

Not touched: county.py, state.py, money.py, the schools page code, static/js/app.js, map.js, and the data CSVs. Nothing was committed.


---

## Part 4: 2023 year-to-date rule (Bolden-Simpson case), 2026-11-09

### Root cause
`year_figure` used a year-to-date (YTD) column only when the latest report reconciles (status `verified` or `derived`). Doc 60884 (Sherry L. Bolden-Simpson) is `filer-inconsistent`: her column B writes 17c as $24,607.97, copied from line 16, while 17a reads $24,878.71, and her two closing cash figures disagree. The rule therefore fell back to her "this period" column, $9,354.38. That column is known to fall short: the period start is blank, opening cash is $8,262.29, and the county posted no earlier 2023 reports.

Tirado, Banicki and Morgan use YTD only because their forms reconcile. The gate was the reconciliation status, not anything about her.

Six other 2023 candidates were hit the same way:
- Ladyga-Block
- Lou Ann Hazen
- DeMaegd
- Bellovich
- Treely
- Compton (YTD = period, so no money moved)

Canneth Lee is also affected; his YTD equals his period figure, so no money moved for him either.

### The rule, fixed (tools/site/civic/campaign_money.py)
- **2023 uses the filer's YTD as filed.** For a year the county posted no earlier reports for (`NOT_POSTED = {2023: ...}`), the latest report's YTD column is used even when the form doesn't reconcile, because the period columns are known to be incomplete. The flag `ytd-unreconciled` and a note say the figure is as written.
- **Other years keep the reconciliation gate.** I tried lifting the gate everywhere first, and it went wrong in 2024 and 2026:
  - Laureys' 2026 YTD of $90,369.64 equals his 2025 report ($23,861.39) plus both 2026 reports. Using it would double count $23,861.39 in the sheriff race.
  - Hizer's and Jordan's non-reconciling YTDs don't match their reports either.
  - So outside 2023, a non-reconciling YTD is still only checked against the reports, not used.
- **New guard, any year:** a YTD is not used when the committee has earlier-year reports in the same cycle and the YTD reaches both years' reports added together. Such a YTD may be cumulative, and the earlier money is already counted. This sets the flag `ytd-cumulative`. No committee in the current data hits it; a test covers the Laureys pattern.
- **The candidate line always says so.** Whenever a figure uses a YTD that differs from the period sum, the candidate's row on the area page carries a line, built by `ytd_uses` and `ytd_line`. Example: "2023 spent and raised: year-to-date figure from the filer's annual report (doc 60884); the county did not post earlier 2023 reports. That form's own numbers don't reconcile; the figure is as written."
  - The reason comes from `ytd_reason`, in this order: an expected earlier report not on file; the 2023 not-posted rule; the reports don't cover the year from Jan 1; or no start dates.
  - A race's map panel adds one caveat per reason, naming the candidates.
  - An area panel with several races says how many candidates use a YTD.
  - The "(uses a year-to-date figure)" money-cell tag now appears only when the YTD actually differs.
- The how-it-works "One year at a time" rule text is updated to match.

### Effect: every filing and total that changed
I took before and after snapshots over all 479 filings. Only these 11 reports changed, all 2023 annual or final reports moving from "this period" to "own YTD":

| Filing | Candidate | Placed in |
|---|---|---|
| 60825 | Canneth Lee | SB council 1 |
| 60833 | Ladyga-Block | Mishawaka clerk |
| 60842 | Turnwald | PHM other |
| 60859 | Lou Ann Hazen | Mishawaka clerk |
| 60860 | DeMaegd | Mishawaka at-large |
| 60862 | Root | county other |
| 60866 | McGann | county other |
| 60867 | Bellovich | Mishawaka council 2 |
| 60884 | Bolden-Simpson | SB council 5 |
| 61143 | Treely | Mishawaka council 4 |
| 68199 | Compton | Mishawaka council 5 |

Five of them (60825, 60842, 60862, 60866 and 68199) have a YTD spending figure equal to the period figure, so no money moved for those.

| Race | Old spent (by party) | New spent (by party) |
|---|---|---|
| 2023g-south-bend-council-5 | $39,642.20 (D $9,354.38, R $30,287.82) | **$54,895.79** (D $24,607.97, R $30,287.82); raised $49,364.32 |
| 2023g-mishawaka-clerk | $32,612.56 (D $24,912.25, R $7,700.31) | $97,133.91 (D $43,687.16, R $53,446.75) |
| 2023g-mishawaka-council-2 | $8,177.83 | $26,768.27 (R $839.58 → $19,430.02) |
| 2023g-mishawaka-council-4 | $21,126.86 | $24,342.30 (D $2,439.16 → $5,654.60) |
| 2023g-mishawaka-council-at-large | $92,064.51 | $119,256.00 (R $59,926.97 → $87,118.46) |

Area totals changed only for:
- Mishawaka: $204,764.36 → $318,283.08
- South Bend: $815,250.79 → $830,504.38

No 2024 or 2026 race changed.

### Audit: every 2023 annual or final report whose YTD spending exceeds its period spending
There are 22 such reports, with YTD spending totalling $1,354,839.90. That includes the St. Joseph County Republican Party at $277,066.61; the 21 candidate committees come to $1,077,773.29. Every one now uses its own YTD. None has another 2023 report on file, so the period columns are known to fall short.

For all 22 the reason shown is "the county did not post earlier 2023 reports". The five flagged "(as written)" are the forms that don't reconcile.

| Filing | Candidate / committee | Placed in | Start | Status | Period spent | YTD spent | Basis used |
|---|---|---|---|---|---|---|---|
| 60819 | Anthony "Tony" Hazen | Mishawaka council 3 | blank | verified | $450.00 | $5,984.33 | YTD |
| 60888 | Anthony "Tony" Violi | Mishawaka council 5 | blank | verified | $2,037.92 | $8,729.72 | YTD |
| 60822 | Bianca Latrice Tirado | SB clerk | blank | verified | $13,179.56 | $71,397.96 | YTD |
| 60832 | David A. (Dave) Wood | Mishawaka mayor | 10/14/2023 | verified | $2,402.92 | $29,200.35 | YTD |
| 60833 | Debbie Ladyga-Block | Mishawaka clerk | blank | filer-inconsistent | $24,912.25 | $43,687.16 | YTD (as written) |
| 60836 | Doris J Portolese | Penn Twp other reports | blank | verified | blank | $1,263.65 | YTD |
| 60839 | Gloria Niedbalski | Mishawaka at-large | blank | verified | $0.00 | $32,730.23 | YTD |
| 60840 | Gregg A. Hixenbaugh | Mishawaka at-large | blank | verified | $12,310.02 | $27,034.92 | YTD |
| 60871 | James Mueller | SB mayor | 10/14/2023 | verified | $85,493.16 | $610,625.36 | YTD |
| 60843 | Jason Banicki | SB clerk | blank | verified | $2,558.86 | $7,290.47 | YTD |
| 60859 | Lou Ann Hazen | Mishawaka clerk | blank | filer-inconsistent | $7,700.31 | $53,446.75 | YTD (as written) |
| 60860 | Maggie DeMaegd (Final) | Mishawaka at-large | blank | filer-inconsistent | $845.39 | $28,036.88 | YTD (as written) |
| 60856 | Mary C. Willson | Mishawaka council 4 | blank | verified | $4,031.77 | $18,687.70 | YTD |
| 60864 | Matthew Branch Carroll | Mishawaka council 2 | blank | verified | $1,961.09 | $7,338.25 | YTD |
| 60865 | Matthew Mammolent | Mishawaka at-large | blank | verified | $768.17 | $3,668.17 | YTD |
| 60867 | Michael Allen Bellovich | Mishawaka council 2 | blank | filer-inconsistent | $839.58 | $19,430.02 | YTD (as written) |
| 60874 | Rachel Tomas Morgan | SB at-large | blank | verified | $12,064.85 | $45,359.56 | YTD |
| 60883 | Sheila Ann Niezgodski | SB council 6 | 10/14/2023 | verified | $950.00 | $18,938.05 | YTD |
| 61143 | Shelli Treely | Mishawaka council 4 | blank | filer-inconsistent | $2,439.16 | $5,654.60 | YTD (as written) |
| 60884 | Sherry L. Bolden-Simpson | SB council 5 | blank | filer-inconsistent | $9,354.38 | $24,607.97 | YTD (as written) |
| 60889 | Troy D. Warner | SB council 4 | blank | derived | $1,223.49 | $14,661.19 | YTD |
| 61117 | St. Joseph County Republican Party | other committees | 10/14/2023 | verified | $26,400.02 | $277,066.61 | YTD |

Three more 2023-cycle reports with YTD above period also use their YTD, by the same rule:
- Doc 60821 (Portolese-Miller): marked Pre-Election but runs through 12/31/2023, so it counts as the year-end report.
- Doc 60879 (Ron Banicki): marked "Other".
- Doc 60824 (Tanner): a 2022 annual in county other reports. The reason shown for it is "the reports on file don't say when their periods start".

**The opposite failure.** No committee currently has more than one 2023 report on file; Wax's second report is now read as 2024. So no 2023 period sum can be doubled by a YTD. The rule is still pinned by tests:
- reports running from Jan 1 with no gap use the period sum, and the latest YTD is only checked, never added (2023 and 2024 tests);
- the cumulative-YTD guard covers cross-year doubling.

**Data notes (CSVs not edited).** These five 2023 forms don't reconcile, and their YTD figures are the filers' as written: 60833, 60859, 60860, 60867, 61143. Doc 60884 also has its YTD spending in doubt: 17aB reads $24,878.71, while 17cB, the figure used, reads $24,607.97.

### Tests (tools/tests/test_campaign_money.py)
New tests:
- `test_bolden_simpson_2023_uses_the_filers_ytd_even_when_the_form_does_not_reconcile`, which also checks the candidate-line wording and that cash still comes only from a reconciling report.
- `test_2023_reports_from_january_1_are_added_not_doubled_by_ytd`
- `test_cumulative_ytd_is_not_added_to_an_earlier_year_already_counted` (the Laureys pattern)
- real data: `test_bolden_simpson_counts_her_2023_ytd` (her $24,607.97; race $54,895.79; D $24,607.97)
- real data: `test_every_2023_annual_with_a_larger_ytd_uses_it`

Changed test: `test_year_to_date_not_used_when_report_does_not_reconcile` now checks a 2024 case. Its old 2023 version encoded the bug.

### Checks
- `build.py --edition st-joseph --check`: 109 pages, **PASSED**.
- `unittest discover -s tools/tests`: **153 tests OK**. That count includes tests added in other agents' files.
- `check_gov.py`: **errors=0**.
- Playwright, at 1280 and 400 px, light and dark, in the ballot, line and wayfinding looks:
  - No console errors or overflow anywhere.
  - Map panel for District 5 (hover, or touch and focus): $54,895.79; "Democrat (D) $24,607.97: 1 of 2 candidates with reports; Republican (R) $30,287.82: 1 of 1 candidate with reports"; a $24,608 bar; and the YTD caveat naming Bolden-Simpson.
  - Area page: "$54,895.79 spent, $49,364.32 raised" and her YTD line.
  - Her reports fold opens with Enter and shows "Yes (its 2023 year-to-date column)".
  - With JS off at 400 px, the total and the YTD line render with no overflow.
- Screenshots: `.playwright-mcp/cf-p4-panel-{1280,400}-{light,dark}.png` and `.playwright-mcp/cf-p4-area-{1280,400}-{light,dark}.png`.

### Files touched in this part
- campaign_money.py
- campaign_map.py
- campaign_pages.py
- campaigns.py (how-it-works text only)
- test_campaign_money.py
- this report

Not touched: county.py, state.py, money.py, the schools page code, app.js, map.js, and the data CSVs. Nothing was committed.
