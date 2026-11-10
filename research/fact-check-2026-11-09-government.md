# Fact-check 2026-11-09: governments, offices, officeholders (agent F2)

Scope: units/offices/terms/people/appointed_boards CSVs, pages officeholders, your-governments, county, places, run/**, home header counts. Sampled, not every row.

## Fix made
- terms.csv: Union Township Board (union-township-board) had NO members for 2023-2026 (officeholders page showed the board empty; 163 -> 166 people now). Added 3 rows: Trisha N. Carrico (R), Ryan Schafer (R), Mike Wozny (R), start 2023-01-01, scheduled_end 2026-12-31. Source GOV-005 (2022 official results, doc 57716; local copy sources/precincts/sjc-county/57716.txt line ~74429, "UNION TOWNSHIP BOARD MEMBERS", 3 candidates for 3 seats; votes Schafer 767, Carrico 700, Wozny 692 per results.csv). Ryan Schafer also has the existing 2027 row.

## Checked and OK
- Home header: 37 local governments = 39 units minus 2 state chambers (39 = 13 townships, 7 towns, 6 school corps, 2 cities, 2 libraries, 2 housing authorities, county, courts, transit, airport, health board). 13 townships, 7 towns, 2 cities, 6 corporations match known county facts.
- 2022/2024 county winners vs precinct_results.csv aggregates: Rolfes, Murphy (35,572-34,905), Castellon, Baxmeyer (13,232-12,483), Redman sheriff, council A/B/C/E/H, Broden, Cotter, Morton, Hazen, Jordan, Shabazz, Figg, Catanzarite, Rutten, Zappia, Brown (54,038-53,957), Dieter, Wisniewski. All match terms.csv.
- 2026 general winners (results.csv) vs 2027-01-01 terms for every county/township/town/school contest: all match (names/parties).
- next_election vs scheduled_end: consistent for every office (2026 winners -> 2030; 2024 -> 2028; city 2027).
- Seat counts: run/ pages (city council 18, county council 9, township board 39, trustee 13) match offices.csv. County row officers 8 + prosecutor.
- Primary/general dates 2027/2028/2030 recomputed (first Tue after first Mon): May 4/Nov 2 2027, May 2/Nov 7 2028, May 7/Nov 5 2030. 2027 municipal filing deadline Friday Feb 5, 2027 = 88 days before May 4, consistent with the Feb 3, 2023 deadline pattern. Organization day (Nov 17, 2026), 8-in-12 governor limit, 29-day registration, 28-day early voting, 12-day mail application match my knowledge of the statutes.
- Union Township trustee, Walkerton wards 1-2 and New Carlisle/North Liberty council split (2026 vs 2027 classes) agree with canvass.

## Unresolved / not changed
1. Superior court seat double-counted: superior-court-judge-chapleau (retired 2021) and superior-court-judge-woods are the same seat (Superior 6, per offices notes). County page says "11 judgeships: 32 offices", your-governments says "Judges: you vote for 11", home "174 elected seats" includes it. True count is 10 judgeships (1 circuit, 1 probate, 8 superior) -> 31 county offices, 173 seats. Not fixed: removing/merging the office breaks anchor-fixture tests (tools/tests/fixtures/anchors_before_*.json) and needs a code change to counts in county.py, landing.py, layers.
2. Home "174 elected seats" also counts Indian Village council (seats blank) as 1. Real size unknown (gap exists).
3. School City of Mishawaka board: offices.csv next_election 2030 for the 3 at-large seats, but Layman and Johnson terms run to 2028 (run/school-board shows "2030 (at-large)"). Single-valued field cannot express two classes; same for New Carlisle council (2 seats 2030, 3 seats 2027, field says 2027) and Walkerton ("Next municipal general Nov 2, 2027" while wards 1-2 are 2030). Not changed.
4. Seat holders short of seats (known gaps): john-glenn-board-lincoln, union-north-board-north, union-north-board-union (1 of 2 each), indian-village-council.
5. Not verified (sjcindiana.gov blocked; justia.com constitution and IC pages returned 403): Ind. Const. art. 6 sec. 2 list of term-limited offices (election_rules row county_row_office_term_limits is flagged secondary in the data), IC 3-8-2-4 exact text, appointed_boards seat counts/appointers (Board of Health 9, Transpo 9, APC 9), CAN form numbers. 2026 results are unofficial (not certified as of Nov 7).
6. Libraries: whether other independent library districts exist in the county (affects "37") not resolved; one search, inconclusive.

## Builder status
tools/build_gov.py is stale: its output differs from the committed CSVs (393 vs 439 terms, 83 vs 170 sources); do not rerun. All edits were made in the CSV.

## Counts
Checked ~120 figures/rows (all county row/council/commissioner/judge terms, ~60 township/town/school 2026 winners, 20 statutory rules, 10 page figures); OK ~117; fixed 1 (3 rows); unresolved 6.
