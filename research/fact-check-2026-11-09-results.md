# Fact-check 2026-11-09: election results (agent F1)

Files: results.csv, precinct_results.csv, elections.csv, gaps_results.csv, gaps_elections.csv, sources_results.csv, sources_elections.csv.

## Method and coverage
Local source copies exist only for the 2020 general (42820), 2022 general (57716), 2024 general (64951, scanned) and 2026 general (73081). All sjcindiana.gov DocumentCenter files return 403 to scripts, so every other year's canvass (2010-2019, 2020-2024 primaries, 2023, 2026 primary) is NOT re-derived: "needs browser check".

| Check | Rows | Result |
|---|---|---|
| 2026g (73081): every vote re-matched to the PDF by word position (candidate name and number on the same printed line); pages 1-2 also read as images | 162 | all match (one wrapped name checked by hand: Gorski 3,614) |
| 2026g registered 193,942 / ballots 77,909 / 40.17%; straight-party 29,724 / 19,372 / 194+45 | 3 + 4 | match |
| 2022g (57716 pp.1-10): numbers matched by position; 25 name-wrap/OCR misses inspected; page 7 read as an image (Portage, Warren, Union, New Carlisle, North Liberty) | 156 | all match |
| 2022g registered 196,917 / ballots 72,678 / 36.91%; straight-party 21,088 / 22,427 / 269 | | match |
| 2020g (42820, 6 pages): every number present; governor, AG, House, Senate lines read in text | 81 | match |
| 2024g (64951, scanned): every vote value found in OpenElections 2024 precinct sums (independent of OCR); page 1 read as an image (PQ#1 49,529/51,395; straight-party 33,609/35,410/237/397/115) | 98 | match |
| 2024g registered 205,991 / ballots 112,329 / 54.53% (OpenElections sums and page 1) | | match |
| 2020g registered/ballots vs OpenElections | | match |
| precinct_results.csv county sums vs results.csv (2020g, 2022g, 2024g), 182 candidate matches by name | 182 | 0 differences (builder also self-checks) |
| South Bend mayor 1963-2023 vs Wikipedia (RES-031) 1963-1999, 2003-2011, 2015 | ~75 | match (see below for 2019/2023) |
| 2024p turnout 201,542 / 23,810 vs state report (ELX-008, PDF read as image) | 2 | match (11.81%; state prints 12%) |
| Election dates: all 26 dated elections are Tuesdays; types plausible | 26 | OK |
| turnout_pct = ballots/registered, all elections | 27 | OK |
| Page display: results explorer shows every 2010+ candidate row's votes; judges-and-questions shows all 132 YES/NO rows; turnout, margins, landscape tables match elections.csv; your-legislators District 7 block matches; 260 "Name (P) N votes" phrases across the site all match results.csv | | OK |
| Internal: no duplicate (contest, candidate); no winner with fewer votes than a non-winner; seat counts equal winners flagged; election_id prefixes consistent | all | OK |

Percent check: all one-seat contests recompute from votes except 1983g Goodhew (35.70, Wikipedia rounding), 2016g governor and 2018g SoS (write-ins excluded from the sum). Not errors.

## Fixes made
1. results.csv, 2023p Walkerton Council Ward 4 (Republican primary): Kyle Norris and Bryan Vandall are tied at 55 votes. The notes said the winner was "derived: top 1 by votes", which cannot be true of a tie. Notes rewritten on both rows (TIE 55-55; winner flag follows Norris being the Republican nominee on the 2023 general ballot; how the tie was broken is not in the canvass). No figure changed. The margins page already shows this race as "0 (tied)".

## Unresolved / source ambiguity
- South Bend mayor 2019 general: CSV (county canvass RES-018) Mueller 9,406 / Haas 5,429; Wikipedia 9,437 / 5,445. 2019 primary also differs (Mueller 4,434 vs 4,447, etc.). 2023 general: CSV 7,878 / 2,939; Wikipedia 7,877 / 2,938. CSV follows the county PDF, which could not be opened (403); needs browser check. Planning/fact-check-report.md noted the 2019 difference earlier.
- All other years' canvasses (2010-2019 general/primary, 2020p, 2022p, 2023, 2024p, 2026p) not re-derived: needs browser check. Pre-1975 South Bend mayor rows have no vote counts in the source (consistent with the CSV).
- 2026p, 2026g district-wide Ballotpedia counts (House 7 10,394-10,102, etc.): not searched.
- Federal races (president, U.S. Senate, U.S. House) are not in results.csv by design (gaps_results.csv says federal is out of scope); 2026 U.S. House 2 and 2024 president exist in the PDFs only.

## Checker output misunderstood
check_results.py reports 8 "unknown source" errors (ELX-008, GOV-044 x6, IND-031). All resolve: ELX-008 in sources_elections.csv, GOV-044 in sources_gov.csv, IND-031 in data/indiana/sources_indiana.csv. The checker only loads sources_results.csv. Not data errors.

## Builder fixes needed
None (the fix was a notes edit; tools/res_main.py regenerates results.csv from scratch and would lose it: it needs the same note change for the 2023p Walkerton Ward 4 tie).

## Build / test
Site build failed on a CSS check not related to this area: ".ehub-grid defined in elections.css and nav.css" (theme agents). check_gov errors 0, check_money OK, check_results only the 8 known false errors above.
