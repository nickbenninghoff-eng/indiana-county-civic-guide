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
