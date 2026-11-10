# Fact-check 2026-11-09: community indicators (F5)

Scope: indicator_values.csv, employers.csv, research_on_voting.csv, sources_community*.csv, gaps_community_people.csv; pages community/*, places community sections.

## Checked (re-derived from local source files; all independent of the builder code)
- ACS 2020-2024 (COM-001/043/044): 372 headline cells (pop_total, median age, median HH income, per-capita income, median home value, median gross rent, poverty %, bachelor's+ %, owner-occupied %, foreign-born %, White NH %, Hispanic %) across county, South Bend, Mishawaka, 7 towns, 6 school districts, 13 townships, Indiana, U.S., re-derived from sources/demographics/censusreporter/**. 372/372 match (Indian Village rent is a Census sentinel, correctly blank). County pop 273,040, MHI 66,868 +/-1,255, home value 192,800 +/-3,481 also confirmed against the live Census Reporter API.
- ACS 2006-2010 (COM-002): 186 cells (6 indicators, all geos) re-read from the Summary File zips using the Census lookup start positions; 186/186 match values and MOEs. Poverty (county 14.57, South Bend 24.33) and bachelor's+ (25.57, 21.73) recomputed by hand: match.
- BLS LAUS: all 106 unemployment_rate rows match the saved annual-average (M13) series. 2025 rows carry the 11-month-average caveat, and the page shows it.
- QCEW: 600 rows; 560 match sources/demographics/bls-qcew exactly; 40 are blank "suppressed" cells (blank in CSV, shown as "suppressed" on page). Gap-row claims (education 11,373 -> 8,857; management 2,348 -> 871) confirmed.
- Census 2020 P1: 29/29 pop_census_2020 rows match the PL 94-171 extract.
- Decennial history (secondary, Wikipedia): spot-compared with Wikipedia South Bend page (all 18 city years, 2025 est. 103,201) - match the secondary source. County/Mishawaka figures match known census values.
- Employers: 2017 top-10 table matches Wikipedia exactly (secondary, status already flagged); 2024 ACFR narrative list and order match the local ACFR PDF p. text; Notre Dame 8,340 matches the PDF (p.4); Hoosiers-by-the-Numbers rows: see fix below. UAW 400 per research file (not re-fetched).
- research_on_voting.csv RV-001 (80 of 85 precincts, six districts, 78-22, Davis 4 in D2 + 1 in D6, Sunnymede 96%) and RV-002 (four counties, Harris 50.0/Trump 48.5, McCormick 49.8/Braun 47.2) confirmed against the articles. Date of RV-002 confirmed.
- Pages: people, income-and-work, housing-and-education community pages show the CSV values, years, +/- and the CV-flag legend correctly.
- Consistency over all rows: no duplicate (geo, indicator, vintage); every source_id resolves; race shares sum to ~100%; percents within 0-100.

## Fixes
1. employers.csv, Hoosiers by the Numbers (COM-010) rows 6-10: was Honeywell Aerospace, Performance Plus, South Bend Tribune, Central Blood Bank, ITR Concession; the live page (fetched 2026-11-09, curl and WebFetch) lists 6 South Bend Tribune, 7 I/N Tek I/N Kote (New Carlisle), 8 Central Blood Bank, 9 Performance Plus, 10 ITR Concession Co LLC (Granger); no Honeywell. Rows rewritten, correction appended to notes. tools/build_community_rest.py list fixed to match (not run; builder also rewrites sources_community.csv from an older list, so do not run it). NOTE (main session): the 2026-11-07 capture in research/10-demographics-economy.md shows the same old list, so this is most likely a directory refresh, not a transcription error; notes reworded to "Updated" and COM-010 accessed date set to 2026-11-09.

## Unresolved / notes
- South Bend 1970 census = 125,850 in CSV (matches Wikipedia). I recall the Census Bureau figure as 125,603 but could not confirm from a primary source; secondary source flagged in the data. Needs a Census historical-table check.
- Hispanic % MOE is 0/blank for county, Indiana, U.S. (Census controls these totals; B03002 cell 12 has a null MOE). Pages show no +/- for them; fine, but not explained on the page.
- COM-010 table content may change over time (it did between the 2026-11-07 pull and now).
- AM General 400 (UAW) and 2017 Wikipedia employer counts not checked against the 2017 ACFR (not available locally).
- Not checked: school_enrollment_total, school_spending_per_student (owned by other sources), places/** community sections beyond sampling, indicator map, teach page. WebSearch calls used: 0.
- Builder tools/build_community_people.py contains a stale COM source list (35 vs current 45 rows); running it would overwrite sources_community.csv. build_indicator_values.py not run.

## Build / checks
Site build passes generation; site check reports one CSS issue (.ehub-grid defined in elections.css and nav.css) which is theme-agent territory. check_gov: 0 errors. check_money: OK. check_results: one error, "unknown source IND-031" at results line 2335 (not this area).
