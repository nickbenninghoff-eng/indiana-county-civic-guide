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

## 2026-11-08: gap-fill C1 (judges, clerk, mayors), C2 (towns and schools), A (units) and B (services and boards)

Sources: `planning/qa/gapfill-2026-11-08-{C1-people,C2-towns-schools,A-rules,B-services}.md` and their `-edits.csv`. Summary and verification log: `planning/qa/gapfill-2026-11-08-applied.md`. Superior Court seats keep the `superior-court-judge-<surname>` office model; successors are new terms on the same office id.

### C1: applied
- Chapleau: "David Chapleau", end 2021-07 (retired in July 2021; day not found; GOV-150).
- Marnocha: "John M. Marnocha", end 2024-01-31 (the planned retirement date; GOV-148, GOV-149).
- Reagan: end 2021-05-31 (The Indiana Lawyer, GOV-145; single source for the day), status secondary. The old end of 2024-12-31 was wrong.
- Full names for Steele, Telloyan and Woods, matching the county directory ("Stephanie E. Steele", "Mark P. Telloyan", "Jamie C. Woods"; GOV-144, re-checked 2026-11-08).
- New office superior-court-judge-hurley (Superior 8; county directory plus Wikipedia), with term __hurley__unk. Start is blank: the 2013 appointment rests on one secondary source.
- Office notes for chapleau, marnocha and reagan rewritten to describe the succession. The stale sentence "No Superior Court retention appears on the 2026 ballot" was replaced in every Superior office.
- New sources GOV-144 to GOV-151. The C1 WVPE appeal article went to sources_people.csv as PPL-044.
- gaps_gov: the Tim Scott/Lee row removed (terms already match). The judges row narrowed to swearing-in dates and Hurley's retention years. The clerk, mayors and Kromkowski rows narrowed.

### C1: adapted
- Brisco, Fronk and Francisco were proposed as new offices. They are recorded instead as terms on the existing offices: __brisco__2021-06 and __fronk__2024 on superior-court-judge-reagan, and __francisco__2024 on superior-court-judge-marnocha. All three starts are blank, because no swearing-in date was found. Brisco's end is 2024-01-26 (federal commission, FJC).
- Steele, Telloyan and Woods proposed starts (2021-05-04, 2022-02-11, 2021-11-15): not applied to the 2025-01 retention-term rows. The appointment terms are not encoded, so these dates went into notes instead.
- Hurley office: next_election left blank, not the proposed 2028, which was inferred.

### C1: notes-only
- Clerk Jones: the 2023 Tribune lead is in the notes; confidence stays low.
- Beutter and Rea: "not a Democrat" (from the Kovach obituary) is in the notes. The proposed party R was not applied, since it is inferred.
- Rea: the resignation lead from the Bethel Beacon. Prickett: "first woman mayor" now quoted from the city timeline (GOV-039). Canfield: the 1963 defeat confirmed.
- Manuel Fisher (1899) is noted on the mishawaka-mayor office. The proposed term was not added, as no term dates exist.
- Kromkowski HD7 1982-2006 is noted on state-house-7. Not encoded, because the source is a secondary database.

### C1: skipped
- Lee start (row says "no change; confirmed"). Hazen swearing-in (row says "keep open").

### C2: applied
- SBCSC: Robles end 2017-09-25 (died in office; ABC57, GOV-152). Monterrosa start 2017-10-24, selected_by appointment (GOV-153).
- SBCSC: new term sbcsc-board-d4__ball__2019-09 (2019-09-16 to 2020-12-31; GOV-157). Ball's 2021 term now has first_selected_by appointment.
- PHM: new terms __turnwald__2021-12 and __mccullough__2021-12 (appointed Dec 1, 2021; GOV-154). Chaffee end 2025-10-08 (GOV-155). Smoker start 2025-11-03, the appointment vote; sworn in Nov 8 (GOV-156).
- phm-board-penn: seat count 3 confirmed and the "unresolved" note replaced.
- School City of Mishawaka appointed seat: new term __weber__2022-07 (to 2025-12-31; GOV-158). Office notes describe the hybrid board.
- Roseland: Williams-Inez end 2024-09-28 and Rulli start 2024-09-29, both from the SBOA Schedule of Officials (78484A).
- north-liberty-council next_election 2027 -> 2030, "inferred from canvass cycle": every North Liberty council race in results.csv is in an even year (2010, 2014, 2022, 2026).
- gaps_gov: the PHM and Robles clauses removed; the town-officeholder and Roseland rows narrowed. gaps_elections: the Indian Village/North Liberty cycle row narrowed.

### C2: adapted
- Woods and Galloway (PHM) proposed end 2021-11-30: recorded as "2021" (year only), because the exact days are not known. Galloway is confidence low.
- SBCSC Jones D4 proposed end 2019-09-15: recorded as "2019", for the same reason.
- New term school-city-mishawaka-board-appointed__roberts__unk: start blank, end 2022, from the Tribune line "Weber succeeds Amanda Roberts". The proposed start is a snippet, so it went into notes.

### C2: notes-only
- Lakeville Kelly and Hathaway, and North Liberty Brown and Lemert: their SBOA "President" years went into notes. Those are the earliest documented service, not start dates.
- North Liberty Kincaid (president in 2013): noted on the office instead of being added as a term.
- New Carlisle Pemberton/Doll conflict noted. Rulli 2026 status is still unconfirmed. Weber's 2026-2029 reappointment (a Ballotpedia lead) is in the notes. Roseland council size: data-pattern evidence added to the gap.

### C2: skipped
- Seat counts marked "no change" (PHM, School City of Mishawaka, John Glenn) and the 2026 school-board party rows marked "confirmed".
- The Monterrosa term_id rename (ids are not renamed). Carr start ("do not apply"). Rouch and Mudrovich starts ("not found").
- New Carlisle Rush and Budreau new terms: low confidence, no dates, a missing first name, and minutes not re-read.

### A (units and gaps_gov)
- Applied: south-bend and mishawaka notes now say "second class city under IC 36-4-1-1" (new GOV-159, Justia). The gaps_gov statutory-class row removed.

### B: applied
- sjcpl: status official. The appointer split is in both units and appointed_boards (Commissioners 2, Council 2, SBCSC board 2, John Glenn and Union North presidents 1), and the board meets the 4th Monday at 4:15 pm (GOV-160).
- Transpo: board of 9 (South Bend mayor 3, South Bend council 4, Mishawaka mayor 1, Mishawaka council 1; GOV-161); unit and board status official.
- Area Plan Commission: 9 seats, appointers and what_it_decides corrected. It covers the unincorporated county and five towns, not South Bend or Mishawaka (GOV-164, GOV-170).
- Housing Authority of South Bend: unit renamed. New board of 7, appointed by the mayor (SBOA-reviewed audit, GOV-162). The 2023 news count of 6 is recorded as a conflict.
- New board mishawaka-housing-authority-board: 7, all appointed by the mayor (city 2025 appointing-authority disclosure, GOV-163). Only seat counts and appointers were taken; that PDF also lists home addresses, which were not collected.
- From the same disclosure: Mishawaka BZA 5 (Mayor 3, Council 1, Plan Commission 1) and Parks 6 (Mayor 4, Library 1, School 1).
- mphpl-board: the meeting-day conflict (3rd vs 2nd Thursday) recorded, not resolved.
- Township office contacts added to the units notes for Centre, German, Greene, Harris, Liberty, Olive and Penn, from official township or in.gov pages (GOV-165 to GOV-169).
- gaps_gov: the housing, Transpo/boards, Mishawaka appointed trustees and meeting-times rows narrowed. Meeting times confirmed on the bodies' own pages are separated from the unverified leads.

### B: adapted
- Mishawaka plan commission: 9 seats (Mayor 5, BPW&S 1, Council 1), and the city disclosure leaves 2 seats untagged. The proposed Parks Board appointee comes from a fetch summary only, so it was left out.
- Mishawaka Board of Public Works: appointer set to Mayor. The proposed "three members" is not confirmed, so it is in notes only.

### B: notes-only
- Mishawaka housing authority legal name (search summary only). Mishawaka and South Bend redevelopment commission appointers and meeting times (leads). Party pages and police contacts (leads in gaps).

### B: skipped
- The county Animal Care and Control Commission (members and appointers not found) and the Mishawaka Animal Control Commission (not confirmed on a page I read).
- The bonus judge list (used only as a cross-check for C1).
