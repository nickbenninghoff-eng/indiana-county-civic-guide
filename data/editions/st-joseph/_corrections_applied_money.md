# Corrections applied: money area (source ids MON-xxx)

Fact-check report: `planning/fact-check-report.md` (MON-023). Build script: `tools/build_money.py`; validator: `tools/check_money.py`. Raw downloads: `sources/money/`.

## Fact-check findings applied

| Fact-check finding | What was done |
|---|---|
| F-05 Mishawaka "$15M / ~20% of the general fund by 2028" was CORRECTED: the figures are ABC57's characterization, not Mayor Wood's, and the article does not say "general fund". | Not attributed to Wood anywhere. Stated in `budgets.csv` (Mishawaka 2026 row notes), `sources_money.csv` (MON-014) and `gaps_money.csv` as "reporter's characterization, not a quote from Mayor Wood". "Of the general fund" dropped. |
| F-05 County 2026: WNDU "just over $90 million" and auditor "$97 million general fund = 39% of total" are exact quotes but the interpretation is UNVERIFIABLE; present both as quoted, Gateway as the documented number. | Two separate `secondary` series (`county-news-wndu-2026`, `county-news-auditor-2026`), both 2026, each with the quote and the conflict in notes. Documented numbers: Gateway General fund $90,704,400 (`county-gateway-general-fund`, official) and all advertised funds $248.2M (`county-st-joseph-gateway-advertised-funds`, computed). The county $90M (general fund) vs about $248M (all funds) distinction is in the notes of the 2026 rows. |
| F-05 South Bend news totals ($417M 2024, more than $424M 2025; Police over $60M, Fire just under $49M, transit $14M) CONFIRMED. | Series `sb-news-allfunds`, status `secondary`; department figures in `budget_breakdowns.csv` (basis `abc57_2025_adopted_selected_departments`). Entered as the stated rounded floor ("more than"). |
| F-05 South Bend Gateway $427M (2023) to about $166-171M (2024-26) series break CONFIRMED (logic). | Two series (`sb-gateway-allfunds-2012-2023`, `sb-gateway-10funds-2024-2026`) with an explicit `series_break` row in each at 2024. Verified in the raw data that pre-2024 totals include water, sewage and trash funds and 2024+ does not. |
| F-05 Gateway tables UNVERIFIABLE (not re-pulled). | Re-derived from the raw Gateway download (see "Verification" below). All county, South Bend and Mishawaka sums matched the research tables. |
| F-05 HB 1210 signed 2026-03-12, delays LIT changes to 2029: CONFIRMED. 04's SEA 1 "from 2028" is stale. | Used 2029 (MON-018). The "cities of 3,500+" detail is flagged unconfirmed in `gaps_money.csv`. |
| F-05 SBCSC: not a fact-check row, but the ABC57 $213.25M board vote conflicts with the Gateway $248.3M. | Kept both; the board figure is a `secondary` series with scope flagged unverified. |
| F-G 06: State bulk-CSV totals UNVERIFIABLE (not spot-checked). | Re-downloaded all 2016-2026 contribution and expenditure zips and recomputed. 53 of 53 research table rows for the committees kept here match exactly (to the dollar). |
| F-G 06 / D: Which legislative districts include the county: SD 8, 9, 10, 11 and HD 5, 6, 7, 8, 21; HD 20 (Pressel) and HD 9 (Novak) never appear: drop. | Pressel committee ("Friends of Jim Pressel") excluded. Districts in `cf_state.csv` are limited to confirmed ones. The research's "UNCONFIRMED" labels on Rogers, Mishler, Bohacek were cleared (SD11, SD9, SD8). Niezgodski SD10 per the research table. |
| F-B 01/06: County party committees "not found" in the state database: CONFLICT-RESOLVED, they file locally. | Not in `cf_state.csv`; listed in `gaps_money.csv` as a local-filing item. |
| F-G 06 Mishawaka clerk: Hazen over $50,000; Ladyga-Block $30,352: UNVERIFIABLE. | Not encoded. |
| F-D 04: SD11 Gratzol (D) vs Schmutzler (R); Rogers lost the May 2026 R primary to Schmutzler (CONFIRMED direction). | Committees for Gratzol, Schmutzler and Rogers added with those roles; notes say the general-election result is unofficial as of 2026-11-07. HD5: Alex Wait (D) added (2026 committee). |

## Corrections found while re-deriving from raw data (not in the fact-check)

- **Gateway budget file repeats every row 5 times** (4,736 unique rows x 5). Summing without de-duplication gives totals 5 times too large. De-duplicated on (year, unit, fund); no conflicting duplicates exist. The research tables already used correct sums.
- Research 05 section 3b lists Mishawaka "Local Road & Street $1,000,000". The budget book shows Local Road & Street $1,065,000 and Motor Vehicle Highway - Restricted $1,000,000. Fixed in `budget_breakdowns.csv`; the 15 fund lines sum exactly to $77,919,352.
- Mishawaka General fund 2020 and 2022: Gateway (fund 0101) gives $42.06M and $37.80M; the research notes cite $35.27M and $37.92M from city books (not re-extracted). Both kept visible in row notes; 2021 ($36.64M) agrees.
- Mishawaka general-fund department list: only Fire ($20,482,149), Police ($17,343,945) and Controller ($5,960,348) were confirmed against department detail in the budget book text; the summary-page labels for smaller departments are misaligned in the text extraction, so they were not encoded.
- South Bend 2024 revenue-by-source figures come from the research transcription of the city PDF (rows sum to the stated $420,595,379 total); the label alignment is still unconfirmed. Marked in notes.

## Conventions used

- `status`: `official` for single Gateway fund figures and city-book figures; `computed` for sums we made (unit totals, department roll-ups, filing-year committee totals); `secondary` for news figures.
- `adopted_or_actual`: `adopted`, `actual`, `proposed` or `series_break` (amount blank).
- `budget_breakdowns.basis` names the source table and scope (for example `afr_2024_actual_by_department`); rows with the same basis do not mix kinds, and each basis group is meant to be read alone.
- Unit ids are provisional slugs (`county-st-joseph`, `city-south-bend`, `city-mishawaka`, `town-*`, `township-*`, `school-*`, `library-*`, `special-*`); map to `units.csv` ids when merged. Examples: `school-sbcsc` is South Bend Community School Corporation, `library-mishawaka` is the Mishawaka-Penn-Harris Public Library, `special-airport` is the St. Joseph County airport authority.
- Gateway "Centre Township" is Center Township (state spelling kept in unit label).
- Campaign finance: filing-year basis (reports filed in that calendar year), spelling variants split funder names, so only funder TYPE totals are given; cash on hand is not in the bulk data (blank); 2026 is partial (extracted 2026-11-07); a few rows flagged Amended may repeat originals (counts in row notes).

## 2026-11-08: gap-fill D (money)

Source: `planning/qa/gapfill-2026-11-08-D-money.md` and `-edits.csv` (215 rows). Edited by hand with Python csv; `tools/build_money.py` was NOT run, so a rebuild from raw data would drop these edits unless the builder is updated. New sources MON-033 to MON-037 (ids below MON-060, which is reserved for another agent's rows; sources_money.csv was re-read right before an append-only write). Log: `planning/qa/gapfill-2026-11-08-applied.md`.

### Applied
- tax_rates.csv: 93 rows of certified_district_rate for 2022, 2023 and 2024 (31 districts each), unit county-st-joseph, status official, sources MON-033/034/035. All 93 were re-derived from the DLGF statewide xlsx files and matched to 4 decimals: for 2022 and 2023 the "Certified Gross Tax Rate (per $100 AV)" column; for 2024 the sum of CERTD_TAX_RATE_PCNT over county-71 rows, which is the same method that reproduces the existing 2025 rates. The rows sit after the 2025 district block, in the file's year-block layout.
- budgets.csv, school-sbcsc 2026 board-vote row (series sbcsc-news-board-vote): the note now carries the DLGF certified fund list. The order (p.37) was re-checked, and its six funds sum to $246,289,187. Leaving out the referendum operating fund gives $213,886,174, within 0.3% of the board's $213,254,807. The note says this match is not confirmed, and it adds the WVPE "$257 million" figure (MON-036).
- gaps_money narrowed:
  - South Bend 2026 budget: the deck figure is described but not encoded.
  - Net AV: 2026 values found; file not created.
  - Combined district rates: only 2012-2021 still missing.
  - Enrollment and per-student: sources found; no indicator ids exist.
  - HB 1210: corrected from the DLGF memo (MON-037). Section 133 is about eligibility for the small-town LIT rate, not cities setting their own rate. Current ordinances expire 2029-01-01.
  - SEA 1: SBCSC estimates only.
  - SBCSC scope: the referendum-fund explanation is "likely".
  - Redevelopment Commission: the March 2026 amended figure is described and not encoded.
  - Jail: still not found.
  - Mishawaka revenue: the 2026 budget file has a text layer when opened in a browser.
- gaps_money "unexplained budget jump" rows (23) narrowed with fund-level detail from Gateway (MON-001, deduplicated). Spot checks match: Portage 2025, Union 2026 and Centre 2019.
  - Explained: Portage 2024-25 (new St. Joseph County Fire Territory), Liberty 2025-26 (by fund detail) and Union 2025-26 (a matching amount).
  - "Likely": the towns' new ARPA, grant-match and bond funds; Centre and Portage 2018-19; Olive 2019-20; Warren 2021-23; Walkerton library.
  - Not explained: Harris 2015-16, Liberty 2020-21, Penn 2012-13 and Warren 2015-16 and 2018-19. The Airport is "not confirmed". South Bend 2016-17 is partly explained and 2021-22 is reframed.

### Notes-only
- The SEA 1 SBCSC estimates ($4.87M, $7.36M and $15.20M) are in the gap text as reported legislative estimates.
- The LSA HB 1210 county estimate is cited only as "county-wide only". Its figures came from a mirror of the fiscal note and were not re-read.

### Not applied (listed for the main session)
- net_assessed_value.csv (37 proposed rows): a new file needs a schema decision, and certified AV differs by fund within a unit.
- indicator_values (42 rows: IDOE enrollment and DLGF expenditure per student): indicators.csv has no enrollment or per-student indicator, and the IDOE sheet's school-year labels are unclear.
- budgets: the South Bend 2026 $429,975,283 row and the Redevelopment Commission amended 2026 $135,109,942 row (instructed not to add).
- debt: the $298,686,137 row (instructed not to add).
- sources_money: the March 2026 Monthly Financial Report, the DLGF Expenditures Per Capita report and the IDOE enrollment file were not added as sources, because no applied row cites them. The gap text names them.

### Checks
- tools/check_money.py (known stale; not fixed): FAILED with 611 errors. The baseline on the HEAD money files is 518. All 93 new errors are "bad rate_kind" on certified_district_rate, a kind the checker does not list, which it also flags on the existing 2025 and 2026 rows. No duplicate-key or rate-range errors were added.

## 2026-11-08: five held money datasets (main-session follow-up to gap-fill D)

Approved by Nick 2026-11-08. Full report: `planning/qa/held-money-data-2026-11-08.md`. Nothing committed; `tools/build_money.py` and `tools/res_main.py` were not run.

### Added
- **assessed_values.csv (new, 732 rows)**, written by the new `tools/build_assessed_values.py` (test: `tools/tests/test_build_assessed_values.py`).
  - 256 `dlgf_certified` rows: 37 units for 2023-2026, 36 for 2020-2022 (the Olive-New Carlisle-Hudson fire territory first appears in 2023), read from the DLGF certified budget orders 2020-2026 (MON-074, MON-073, MON-072, MON-071, MON-070, MON-027, MON-026), General fund (schools: Operations).
  - 476 `gateway_budget_estimate` rows, 2012-2026, from the Gateway budget download (MON-001), deduplicated (every fund row appears exactly 5 times; no conflicting duplicates).
  - Correction to the plan: the Gateway "Net Assessed Valuation" is NOT the certified tax base. For 2026 it differs from the budget order for every unit (from 35.7% below for Mishawaka to 2.7% above for the Airport; the county's is a round $10,000,000,000 against a certified $14,611,493,562). It is kept as a separately labelled estimate, and each row says by how much it differs where a certified value exists.
  - The 37 values D proposed for 2026 are reproduced exactly. Hand-checked against the PDF: county p.5, South Bend p.21 (rendered page viewed), Mishawaka p.23, Penn p.16, Portage p.17, SBCSC p.37, PHM p.35, SJCPL p.42.
- **indicator_values.csv (+104 rows)** and **data/indiana/indicators.csv (+3 definitions)**:
  - `school_enrollment_total`: 6 corporations x school years 2011-12 to 2025-26 (MON-075). Year convention verified: the IDOE data page lists the file as "Updated - SY 2025-2026", so sheet "2026" = 2025-26. Corroboration: the statewide kindergarten count drops in sheet "2021" (78,649 to 72,993), the fall-2020 school year.
  - `school_spending_per_student`: 6 corporations x calendar years 2024 and 2025 (MON-076).
  - `school_spending_per_student_median`: 2 state rows.
  - All 12 per-student values and ranks were checked visually on the rendered report pages (PDF p.54-56). They match D's values. The word-position extraction used here also puts them on the right rows.
- **budgets.csv (+2 rows)**:
  - South Bend 2026, all funds incl. utilities: $437,446,265, adopted, Ordinance 11229-25 (MON-078). The ordinance was found in WebLink Ordinances > 2025 (doc 401021).
    - Exhibit A's grand total was read on the page image (p.8). Department totals sum to $437,446,264. The OCR text layer misreads the City Clerk total as 672,863; the image shows 572,863.
    - Water works (620, 622, 625) and sewage works (641, 642, 649) funds are in Exhibit A.
    - The row is inserted before the 2027 rows; 2027 adopted is still South Bend's last row (checked in the built place page).
    - The $429,975,283 overview figure was NOT used. It is $7,470,982 below the ordinance, with no stated reason (gap row kept).
  - Redevelopment Commission 2026: $135,109,942, basis `amended_all_funds`, kind `amended` (MON-077, p.15). Revenue of $48,613,328 (p.12) is in the note. The row routes to the "Other reported figures" table, not a chart.
- **debt.csv (+1 row)**: South Bend $298,686,137 at 2026-01-01 (MON-077, pp.26-27).
  - Civil city $181,211,137 plus RDC revenue bonds $117,475,000; the components were checked.
  - Inserted after the existing 2026-09-04 row, so money.py's "first non-2024 South Bend row" is unchanged.
- **sources_money.csv (+9)**: MON-070 to MON-078.
- **gaps_money.csv**: 4 rows narrowed to what is still missing: South Bend 2026 ordinance vs overview; certified AV 2012-2019; per-student before 2024; RDC adopted budget.
- **data/SCHEMA.md**: assessed_values.csv; the table-only budget bases and kinds; debt_type convention; the school indicators.

### Checks
- `python -P -E tools/site/build.py --edition st-joseph --check`: PASSED (60 pages, no unknown source ids).
- `python -P -E -m unittest discover -s tools/tests`: 49 tests OK (8 new).
- `python -P -E tools/check_gov.py`: errors=0, warnings=23 (unchanged).
- `tools/check_money.py` (known stale): 613 errors, against 611 before. The 2 new errors are the RDC row's basis `amended_all_funds` and kind `amended`, which the checker does not know.
