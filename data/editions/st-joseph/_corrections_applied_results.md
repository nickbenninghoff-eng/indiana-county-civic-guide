# Corrections applied: elections and results (RES)

Source of findings: `planning/fact-check-report.md` (2026-11-07), cited here as FC with its section letter. Files written by `tools/res_main.py` from `research/results-2010-2014.md`, `results-2015-2019.md` and `results-2020-2026.md` (county canvass transcriptions), plus `research/02-south-bend.md` (pre-2010 mayoral) and `research/09-gap-fill-ballotpedia-statutes.md` (Ballotpedia). Validation: `tools/check_results.py`.

## Findings applied

| # | FC finding | What was done |
|---|---|---|
| 1 | FC D / must-fix 10: the 2020 primary header prints "May 5, 2020" but the election was held June 2, 2020 | `elections.csv` row `2020p` has date `2020-06-02`; the note records "rescheduled from May 5" and that the PDF header still prints May 5. |
| 2 | FC D: docs 37457 and 60003 are the same election (identical registered 191,025, ballots 37,445, run date 6/12/2020) | Encoded once, from 37457 (`2020p`). 60003 is listed in `sources_results.csv` as a duplicate copy and cited on the election row only. The 36 rows of the 60003 section in `results-2015-2019.md` were not encoded. The single value that differs (Teshka, State Rep 7, 2,650 in the 37457 text layer vs 2,651 in the 60003 OCR) uses 2,650 per FC and says so in the row note. |
| 3 | FC D / must-fix 11: 2019 South Bend mayor official canvass is 9,406 (63.40%) / 5,429 (36.60%), total 14,835, not Wikipedia 9,437 / 5,445 | `2019g-south-bend-mayor` is taken from county doc 60004 (9,406 / 5,429); the Wikipedia figures are not encoded. Row note records the difference. |
| 4 | FC D: 2011 Republican mayoral nominee's ballot name is Wayne Curry (2,884, 19.38%), not "Norris Curry Jr." | `2011g-south-bend-mayor` carries "Wayne Curry"; row note records the Wikipedia name. Buttigieg 10,991 and Farrell 1,008 as in the canvass. |
| 5 | FC D: 2023 mayor official 7,878 / 2,939; clerk Tirado 7,323; D5 margin 38 (1,414 vs 1,376); Districts 1, 4, 6 uncontested (Lee 1,603; Warner 1,938; Niezgodski 743) | Taken from county doc 60569, not from WNDU. |
| 6 | FC D: 2023 single-seat district races (SB D2, D3, D5; Mishawaka D1, D2, D4 etc.) were flagged "multi-seat" with no winner | Winners derived as top vote-getter for city-council numbered districts, town wards and numbered South Bend school districts (`vote_for` = 1); row note says "winner derived". City council at-large (3 seats, per research/03 and FC B/E), township boards (3 seats, per the 2018 canvass header) and lone candidates are flagged by the same rule. No other multi-seat winners were inferred. |
| 7 | FC D: 2019 council results (Warner is District 4 at 2,257 / 68.00%; Teshka District 5 at 2,056 / 57.75%) | County canvass values used (`2019g-south-bend-council-4`, `-5`). |
| 8 | FC A: 2026 primary figures (Rolfes 5,836, Cook 4,193, O'Brien 1,667, Ruszkowski 9,661, Wigfall 4,938, Camp 1,116) supersede the narrative file | Official doc 71640 values are in `results.csv`. Uncontested commissioner D1 primary (Baxmeyer 4,137; Redman 4,467) included. |
| 9 | FC A: 2026 general is unofficial; numbers match the county doc | All `2026g` rows and the election row are `unofficial`; every row note says "Unofficial as of 2026-11-03 21:07 EST". Uncontested Council E (Camp 5,931) and H (Tanner 5,051), HD6 (Bauer 12,411) included. |
| 10 | FC A: HD7 2026 county portion Teshka 9,881 vs Davis 9,840 (50.10 / 49.90); district-wide Ballotpedia totals differ because the district extends beyond the county. HD8 is 66.45% | County canvass values used. Winner is blank for HD7 2026 (and for every legislative contest not shown to lie wholly in the county); note says "leads within the St. Joseph County tally". Ballotpedia district totals were not substituted. |
| 11 | FC A: SD11 2026 county portion Gratzol 14,254 (55.58%) vs Ballotpedia district 19,450 | County canvass used; winner blank; district totals not encoded (the district is on the canvass). |
| 12 | FC A / must-fix 12: five "RETAIN JUSTICE" rows (DeBoer, Felix, McAdam, Francisco, Fronk) are not Supreme Court justices | Contest ids `2026g-state-retention-<name>`; labels read "Retention: <name> (court not stated in the canvass)"; row note records the printed heading and the FC point. |
| 13 | FC A: no St. Joseph Superior Court retention appears on the 2026 ballot; HD20 (Pressel) and HD9 (Novak) never appear | No such rows exist. |
| 14 | FC A/B: 2024 county results use the official canvass (doc 64951), not election-night counts (e.g. Recorder Brown 54,038 vs Banicki 53,957; Treasurer 54,617 / 53,161; Surveyor 54,375 / 54,203; Coroner 57,006 / 51,052; Council D, F, I; Hazen 22,491 / Carbone 14,112 / Mitchell 1,842; Council G and Commissioner D2 uncontested) | All from 64951. |
| 15 | FC B: 2022 Auditor 35,572 vs 34,905; Clerk 36,732 vs 33,916; Assessor with Ted Booker (D) 33,183 vs Castellon 37,568; Council E Hess 3,789 vs Jason Kring 3,209; 2022 D1 primary Westerhausen 68.89%; 2018 Sheriff Redman 61.47% (56,334 vs Jonas 35,313); Sheriff Grzegorek 54.05% (2010) and unopposed 37,776 (2014); Cotter 2014 | From the county canvass (57716, 60001, 60006, 60019, 60012). |
| 16 | FC B: the Circuit Court judge was on the 2022 ballot (Broden, uncontested, 41,815); the 2024 judicial race was the Probate judge | `2022g-county-circuit-judge` and `2024g-county-probate-judge` as in the canvass. |
| 17 | FC B: 2024 Hazen won the Republican primary 2,525 vs 2,479 | In `2024p-county-commissioner-3-r`. |
| 18 | FC D: 2012 county governor Gregg 59,411 / Pence 47,182 (43.08%), not 59,410 / 47,208 | County doc 60015 values used. |
| 19 | FC D: 2012 retention values for Barnes, Frese, Manier were corrected from garbled OCR; 2014 Prosecutor Sanford 26,201 derived and arithmetically sound | Kept with `status=from_scan`, `confidence=medium`, and a note on each row. |
| 20 | FC E: Mishawaka 2023 primary at-large Mammolenti, Hixenbaugh and Hahn ran in the Democratic primary (816 / 809 / 788); D2 Carroll 52.35% (computed) | Encoded as party D in `2023p-mishawaka-council-at-large-d`; pct computed from votes. |
| 21 | FC D: turnout percentages for 10 elections recomputed and consistent | `check_results.py` recomputes ballots/registered for every election with all three values (tolerance 0.02); no mismatches. |
| 22 | FC A: 2024 primary header says Unofficial (doc 62697) | `2024p` and all its rows are `unofficial`; note gives "Unofficial as of 2024-05-07 20:01 (election-night header)". |
| 23 | FC A: Ballotpedia vs canvass for state legislative contests; "county totals = district totals in 2018-2026" for HD5 | County canvass is the record. District-wide Ballotpedia totals are encoded only where a district/year is missing from the canvass transcription: `2018g-state-house-8` (Dvorak, 16,141, unopposed), status `secondary`, notes say the total is district-wide. Where county totals equal the Ballotpedia totals the winner flag is kept (districts shown to lie wholly in the county). |

## Conventions used (not fact-check findings)

- `status`: `official` or `unofficial` follows the header of each county file. Unofficial: 2012 primary, 2012 general (page 1 stamped Official, pages 2-4 Unofficial; the page of each row was not recorded), 2014 primary, 2015 primary and general (election-night run), 2024 primary, 2026 general. Rows the research marks OCR-uncertain, derived or otherwise unreadable are `from_scan` with `confidence` `medium` or `low`. Pre-2010 mayoral rows and the one Ballotpedia row are `secondary`.
- Everything transcribed from a scan (2010-2019 and the 2024 general) is read from OCR; clean rows keep `official`, flagged rows are `from_scan`. The election-row notes say which files are scans.
- `pct`: 2010-2019 values are as printed; the 2020-2026 files print counts and the transcription computed percents, so those rows say "pct computed from votes". Percentages for multi-seat contests are each candidate's share of all votes cast in the contest.
- `winner`: as flagged in the source, except where the contest is a county tally of a statewide or multi-county contest (left blank; the note says the county tally cannot decide it), or derived as described in row 6. In primaries `Y` means nominated. `uncontested` and `passed` map to `Y`.
- `vote_for`: stated seat count where the research gives one (township board 3, council at-large 3, wards and districts 1, explicit "(3)" labels); otherwise the number of winners flagged in the source; blank for yes/no questions.
- Straight-party rows are encoded as a contest per election (`<id>-county-straight-party`) and also summed into `elections.csv` columns (blank for primaries, which have none, and for the 2011 general, whose two straight-party blocks cover separate city areas).
- Party codes: DEM/REP/LIB/IND/NP/WI/write-in mapped to D/R/L/I/NP/W. WTP, IRP, LINC and LP are `O`, with the printed code in the row note (LP is not defined in the canvass text).
- Skipped by instruction: federal races, precinct-committee and convention-delegate races, precinct-level files.
- Rows with no readable votes or percent were not encoded and are listed in `gaps_results.csv` (2015-2019 lines 476, 740, 752, 787, 791).
- `office_id` is blank in `results.csv`; the main session joins it to the offices file.

## 2026-11-08: gap-fill F (canvass re-reads), plus results edits from C1 and A

Source: `planning/qa/gapfill-2026-11-08-F-canvass.md` and `-edits.csv` (104 rows). Every changed contest was re-summed against its printed total (pct within 0.1). Summary and verification log: `planning/qa/gapfill-2026-11-08-applied.md`.

### F: applied
- New rows (16), each noted "re-read 2026-11-08 from <doc> p.<n>": 2016g New Prairie at-large Shail (60008); 2018g Clay Fountain, Greene Whitesel, Penn Hahn, Portage Ashe (60006); 2015p South Bend D at-large Tom Price (60011); 2015g Lakeville council Debra L. Law and Martha Tyler (60010); 2022g Union trustee Carrico and Watts, Union board Schafer, T. Carrico and Wozny, New Carlisle council Kauffman, North Liberty council G. Brown and T. England (57716 p.7).
- 2016g Zeiger: confidence high and status official (name printed clearly, 60008 p.3).
- 2018g Clay: Baxmeyer 4,180 -> 4,189 (matches printed 15.74%); winners derived for Clay, Greene, Penn (top three) and Portage (all three elected); "further candidate" notes cleared.
- 2018g Harris trustee: "(name not captured)" -> William Price, 4,002 (60006 p.2); Lindsay winner Y.
- 2018g Penn: Brandon K. Tran confidence high; printed "TRTAN" is noted as a probable typo.
- 2015p South Bend D at-large: the notes about percents summing to 90.68 removed, now that the missing candidate (Price) has been added.
- 2015g Walkerton clerk-treasurer: Terri Buckmaster (60010 p.2).
- 2015g Lakeville council: Eric -> April L. Hathaway (pct 29.86) and Karen S. Loving -> Karen S. Iovino (44, 20.85); both winners, vote_for 3. Iovino matches the SBOA Schedule of Officials.
- 2024g New Prairie at-large: Yacullo 877 -> 677 (36.52), Smith 63.48 (total 1,854; 64951 p.5); vote_for 1; status official.
- 2024g probate judge: status official (printed total 108,353 matches; 64951 p.3).
- 2012g page-1 contests (straight party, statewide offices, state senate 8/9/10, house 5-8): status official, since page 1 is stamped OFFICIAL RESULTS (60015 p.1).
- elections.csv 2015p: registered 112,482, ballots 13,642, turnout 12.13 (computed); the note says these cover only the precincts that held the municipal primary.
- gaps_results.csv: 13 rows removed as resolved and 5 narrowed (2012 stamp, 2010 retention headings, 2010/2011 primary stamps, 2020 Court of Appeals names, 2024 now presidential write-ins only).

### F: adapted
- 2018g State Rep 8, Dvorak: 16,141 -> 14,772 (county tally on 60006 p.1). This also changed the label to "State Representative, District 8", the status to official and the source from Ballotpedia RES-035 to the county canvass RES-016.
- 2012g HD7 Niezgodski: status kept from_scan, because the vote figure is OCR-flagged and was not re-read. Its note records the page-1 stamp.
- 2015g Lakeville Law and Tyler (new rows): confidence medium -> high after a second independent read.
- 2018g Clay Fountain (new row): confidence high -> medium, because the party is inferred from a truncated "(DE".
- 2015g Lakeville clerk-treasurer McQueen (proposed confidence medium): applied as "Cindy McQueen". The surname is printed; the first name comes from the SBOA Schedule of Officials (GOV-092), because the first letter is clipped.
- elections.csv 2012g: the note now says which pages are official. The row's own status was left unofficial pending a decision.

### C1 (results rows)
- Applied: 2026g Court of Appeals and Tax Court retention labels for DeBoer (Fourth District), Felix (Fifth District) and McAdam (Tax Court), from the Indiana Judicial Branch release of 2026-08-27 (new RES-045).
- Notes-only: 2026g Francisco and Fronk. Both are St. Joseph Superior judges (county directory), so the contest is most likely the county Superior Court retention. The contest_id and the "state" label were kept: no renames without the certified canvass.
- Notes-only: 2010g May, Brown and Robb (Court of Appeals) and Chamblee (probably a county Superior Court retention). The Indiana Lawyer article was not re-opened, and the county page prints no court heading.
- Notes-only: 2016g Hostetler/Hurley (probably county retentions), 2022g county retention (probably Hurley; inferred) and 2020g Supreme Court retention (Goff; search snippet only).

### A (results rows)
- Applied: 2010g-state-public-question label -> "Public Question #1: property tax caps in the state constitution (Art. 10, Sec. 1)", from the Election Division's prescribed ballot text (new RES-046).
- Skipped: elections.csv 2016 and 2018 question text. The county results have no 2016 or 2018 statewide question rows to attach it to.
