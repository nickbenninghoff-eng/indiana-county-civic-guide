# Fact-check findings applied: GOV area (county-edition government structure and officeholders)

Source of corrections: `planning/fact-check-report.md` (source id GOV-015 in `sources_gov.csv`). Files built by a script from the research notes; validated with `tools/check_gov.py`.

## Conventions used in the GOV files
- **Terms are service stints.** One row per person per contiguous service in a seat. Consecutive re-elections up to the 2026 cycle are merged (the "Elected ..." list in `notes` shows each election). A re-elected incumbent gets a separate row for the term starting 2027-01-01 so the unofficial 2026 result stays distinguishable.
- **Dates.** Terms from county, municipal, township and school-board elections start Jan 1 after the election and run four years (inferred from the election year; stated in `notes`). Legislators start in November of the election year (month precision). `end` blank = still serving as of 2026-11-07; the scheduled end is then written as `scheduled_end=...` in `notes`. Rows starting 2027-01-01 are future terms: `end` holds the scheduled end.
- **Status.** `official` = text-layer county canvass (2020, 2022, 2023, 2026 primary); `from_scan` = canvass read by OCR (2010-2019 and the 2024 general) or a stint that includes such years; `unofficial` = 2026 general (election night, 11/3/2026 9:07 PM EST); `secondary` = Wikipedia, Ballotpedia, news (mayors list, legislators, caucus appointments, retention judges). A merged stint takes its weakest status.
- **Unit and office type vocabulary** (for reconciliation with `data/indiana/unit_types.csv` / `office_types.csv`): unit types `county, court_system, city, town, township, school_corporation, library, transit, airport_authority, health_board, housing_authority, state_chamber`; office types `county_commissioner, county_council_member, county_auditor, county_treasurer, county_recorder, county_clerk, county_sheriff, county_coroner, county_surveyor, county_assessor, county_prosecutor, circuit_court_judge, probate_court_judge, superior_court_judge, mayor, city_clerk, city_council_district, city_council_at_large, town_council_ward, town_council_at_large, town_clerk_treasurer, town_judge, township_trustee, township_board_member, township_assessor, school_board_district, school_board_at_large, school_board_appointed, state_house, state_senate`.
- `OVERLAP_OK` in `notes` exempts a row from the overlap check (Fleming/Hazen 2024; Voorde/Bruggner 1960; Wax).
- Blank `seats` means the seat count could not be determined from sources.
- Names are the common form of the printed ballot name; the printed variant is noted where it differs.

## Findings applied

| Fact-check finding | Where applied | Value encoded |
|---|---|---|
| Hazen's commissioner appointment was Jan 20, 2024 (not 2022); Fleming served Nov 2014-Jan 31, 2024 | `terms`: county-commissioner-d3 (Hazen, Fleming) | Hazen start 2024-01-20, selected_by/first_selected_by caucus; Fleming start 2014-11, end 2024-01-31 (low confidence, mechanism of her 2014 start unknown); overlap exempted |
| Hazen was re-elected to Mishawaka D3 in Nov 2023, then resigned; Lou Ann Hazen is a Republican | `terms`: mishawaka-council-d3 | Tony Hazen 2020-01-01 to 2024-01; Lou Ann Hazen R from 2024-01, selected_by caucus (inferred, medium) |
| Mishawaka D5 Violi and D6 Banicki are Democrats; 7-2 D council after 2023 (2015 also 7-2 D) | `terms`: mishawaka-council-d5, d6 | Party D, 2023 uncontested; council parties all populated from the canvass (none left blank) |
| Beidinger was chosen by caucus May 20, 2026 for District 4, not elected in 2019; Warner won D4 in 2019 and 2023 | `terms`: south-bend-council-d4 | Warner 2020-01-01 to 2026-05; Beidinger start 2026-05-20, caucus, scheduled end 2027-12-31 |
| 2019 SB Warner is District 4, not at-large; Teshka D5 2019 | `terms` | Warner/Teshka encoded in D4/D5 |
| Council E and H 2026 uncontested (Camp, Tanner) | `terms`: county-council-e, h | Camp and Tanner 2027-01-01 rows, unofficial |
| Council went 6-3 D before Nov 2022; 5-4 R after 2022/2024; 7-2 D incoming | `terms` (derived from per-seat winners) | Seats A-I encoded per canvass 2010-2026 |
| Commissioners 2-1 D from Jan 2027 (Redman D1, Morton D2, Hazen D3); do NOT use WNDU's "first D majority in 20 years" | `terms` only; claim not encoded | Terms only; no majority claim |
| Ruszkowski is the sitting (not former) SBPD chief, retiring as chief at end of 2026 | `terms`: county-sheriff 2027 row | Note on the row |
| Sheriff before 2019: Grzegorek elected 2010 and 2014 | `terms`: county-sheriff | Grzegorek 2011-01-01 to 2018-12-31 |
| Redman 2018 margin 61.47% (not ~59%); 2022 Auditor margin 667 (not ~663) | `terms` notes | Official figures |
| 2024 official canvass replaces election-night counts (Recorder 81 votes, Surveyor 172, Treasurer, Coroner, Commissioner D3, Council D/F/I) | `terms` notes | Recorder Brown, Surveyor Dieter, Coroner Jordan, Treasurer Wisniewski, Hazen D3, Shabazz/Figg/Rutten from doc 64951 |
| Wisniewski is not a "re-elected" Treasurer: she was Recorder (2016, 2020) and was elected Treasurer in 2024; 2020 Treasurer was Tim Swager | `terms`: county-treasurer, county-recorder | Encoded per canvass |
| Prosecutor and Surveyor are not on the Art. 6 sec. 2 term-limit list (limit covers Clerk, Auditor, Recorder, Treasurer, Sheriff, Coroner) | `offices` notes | Stated per office |
| Circuit judge was on the 2022 ballot (Broden, uncontested), not 2024; 2024 was the Probate judge race | `terms`: circuit-court-judge, probate-court-judge; `offices` notes | Broden 2023-2028; Zappia 2025-2030 |
| Superior Court merit selection is one of FOUR counties (Lake, St. Joseph, Allen, Marion); 7-member commission; HEA 1453 (2021) changes; no Superior retention on 2026 ballot | `offices`: superior-court-judge-* | Stated in notes |
| County council is nine single-member districts under IC 36-2-3-4(c) (not 4 + 3 at-large); opt-in unverified | `offices`: county-council-a to i; `gaps_gov.csv` | Nine districts, seats = 1 each |
| April 2026 ruling: say "a judge ruled" (ABC57); no court named; suit originated in Marion County in 2023 (fact-check); appeal unknown | `offices`: county-commissioner-d1/d2/d3 notes; `gaps_gov.csv` | Wording as specified |
| Kovach mayor 1980-1983 (one term; "retired end of 2012" is wrong); Beutter 1984-2003 (ABC57's 1982 impossible); Rea took office 2004 | `terms`: mishawaka-mayor | Kovach 1980-1983, Beutter 1984-2003, Rea 2004-2010 |
| South Bend mayors list: 33 rows faithful to Wikipedia; Kernan/Luecke "Jan 3" dates conflict with normal Jan 1 start; Miller/Longley/Fogarty inconsistencies | `terms`: south-bend-mayor | 33 rows; conflicts in notes; Luecke low confidence |
| Luecke 1997 appointment (council, single source) | `terms`: south-bend-mayor No. 31 | selected_by appointment; low confidence |
| Last Republican SB mayor elected 1967 (Allen) | `terms` note | Allen noted as last Republican |
| Bolden-Simpson won by 38 votes (not 37) | `terms`: south-bend-council-d5 | 38 |
| Districts 1, 4, 6 2023 were uncontested (Lee, Warner, Niezgodski) | `terms` | Encoded |
| SB 2019 mayoral official canvass 9,406 / 5,429; 2011 nominee Wayne Curry | not needed for terms (no vote counts in terms.csv) | Mayor rows only |
| HD7 Teshka: county portion 9,881 vs 9,840 (41 votes); describe as leading narrowly, unofficial | `terms`: state-house-7 2026 row | Low confidence, unofficial |
| HD8 Dvorak 66.45% (66.4), not 66.5 | `terms` note | 66.45% |
| HD6 Bauer general uncontested (12,411) | `terms`: state-house-6 2026 | Uncontested |
| SD11 Gratzol county portion 55.58%; Rogers lost the May 2026 GOP primary | `terms`: state-senate-11 | Both noted |
| HD20 (Pressel) and HD9 (Novak) never appear on county ballots: drop them | `offices`, `units` | Not encoded; delegation = HD 5, 6, 7, 8, 21 and SD 8, 9, 10, 11 |
| Nov 2026 township and school-board results exist in the canvass | `terms` | Centre Baker (D) over Galloway; Penn Duncan (D) over Portolese; Harris Vos (D) over Lindsay; all others from doc 73081 |
| Straight-ticket, supermajority, session-date, HB 1210, SEA 1 findings | not in the GOV area | Not applicable here |
| J. Chester Allen "first" claim, Prince Shembo name, Philip Sharp portrait, Niezgodski allegation, Boykins settlement | not encoded | Not part of the terms/offices data; the Niezgodski allegation and settlement text are not copied. Wikipedia-derived office dates for Walorski, Bauer, Dvorak, Fry, Niezgodski are encoded with secondary status |
| Bauer Speaker years "2003-05 and 2007-11" likely off by a year | `terms` note | Marked unverified |
| Council president Tanner elected 6-3 Jan 2026 (ABC57) | `terms` note | Kept as sourced |

## Conflicts the fact-check did not resolve (encoded with confidence=low and a note)
- South Bend council D1: canvass shows Tim Scott elected 2019; Wikipedia says Canneth Lee "elected 2020". Scott ends "2020", Lee starts "2020" (selected_by unknown).
- South Bend clerk Jan 2020-Dec 2023: winner of the Jan 2020 caucus not confirmed; Dawn Jones encoded (Tirado coverage calls her the previous clerk).
- South Bend council D5: Eli Wax's start (after Teshka) not sourced.
- Commissioner D3 2014: McClure's exit and Fleming's "Nov 2014" start; mechanism unknown.
- Luecke end date (infobox Jan 1, 2012 vs body "until 2011"); Miller/Nemeth overlap; Longley 1888 vs 1884; Colfax III 1898-1901 vs 1902.
- Superior Court retention cycle: Chapleau and Marnocha retained 2020 but absent from the 2026 ballot; end date unresolved.
- SBCSC at-large seat count (research and ABC57: 2; 2016 canvass transcription: 3 winners); office seats left blank.
- Mishawaka mayor Prickett start year (source range 1963-1979, Jan 1964 start inferred) and "first woman mayor" (unverified, not asserted).
- New Carlisle, North Liberty and Roseland 2026 town winners: seat counts not printed.

## 2026-11-08: SBCSC 2016 at-large race
- The 2016 transcription labelled the SBCSC at-large race "3 seats" and marked McCullough a winner. Statute (IC 20-23-15-6(c), 2016 text: two at-large members) and ABC57 (Nov 6, 2020, GOV-138: McCullough a "new board member" after 2020, taking Rudy Monterrosa's place) show two seats; winners Robles and Anella.
- results.csv: vote_for 2 on all 8 rows; McCullough winner N. terms.csv: McCullough term now starts 2021-01-01 (id ...__2021-01); Robles end date marked as scheduled, likely earlier; Monterrosa term added (start unknown, end 2020-12-31). research/results-2015-2019.md corrected so a regeneration keeps the fix. Source: planning/qa/research-2026-11-08-roseland-sbcsc.md.
- Not yet re-read: the printed "Vote for" line on canvass View/60008 (county site blocks automated fetches).
