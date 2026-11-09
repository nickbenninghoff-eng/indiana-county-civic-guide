# Gap fill F: election canvass re-reads (2026-11-08)

Method: on-disk PDFs (2020, 2022, 2024) rendered locally; county documents 60006/60008/60010/60011/60015/60018/60019/60020 opened in Claude in Chrome (own tab, nothing downloaded or saved; pages rendered with pdf.js in the tab, scanned images read at up to 3x zoom). No documents failed to open. No existing data/code/docs edited. All proposed changes are in `gapfill-2026-11-08-F-canvass-edits.csv` (104 rows). All 8 browser docs are image-only scans (no text layer), so every value below is a visual read.

URL pattern for all sources: https://www.sjcindiana.gov/DocumentCenter/View/<id>. "p." = PDF page index.

## Task 1: 2016 general (60008, official report run 11/18/16)
- **SBCSC at-large vote-for: CONFIRMED = 2.** p.3: "SOUTH BEND COMM SCHOOL AT LARGE / VOTE FOR NOT MORE THAN 2 / (WITH 135 OF 135 PRECINCTS COUNTED)". Anella 14,395 19.01; Brown 8,345 11.02; Gathright 7,303 9.64; James 4,779 6.31; Malone 8,314 10.98; McCullough 12,780 16.87; Nichols 4,677 6.18; Robles 15,147 20.00; Total 75,740. Matches results.csv; winners Robles, Anella, McCullough 3rd is correct. No change.
- **New Prairie at-large: RESOLVED.** p.3: "NEW PRAIRIE UNITED SCHOOL AT-LARGE / VOTE FOR NOT MORE THAN 1 / (WITH 4 OF 4 PRECINCTS COUNTED) / RICHARD ALAN SHAIL 1,204 100.00 / Total 1,204". NEW row. High.
- Side finding: p.3 prints "DANIEL ZEIGER" cleanly (Union-North at-large 911); the "(?)" can go.

## Task 2: five research line references (all resolved)
- Line 476 = 2016 New Prairie at-large (above).
- Line 740 = 2018 Clay township board missing line. Printed (p.2): MELINDA J (MINDY) FOUNTAIN (DE... 4,790 17.99 (party truncated; DEM inferred). The "~13.99%" in the md was wrong. Also Baxmeyer is 4,189 not 4,180 (results.csv old value 4180 -> 4189). Rowland 3,868 14.53 and others as in csv.
- Line 752 = Greene: RON WHITESEL (DEM) 575 22.50 (p.2). Md "~22.5%" correct.
- Line 787 = Penn: LACY HAHN (DEM) 7,972 17.45 (p.3). Tran prints "TRTAN" 6,204 13.58.
- Line 791 = Portage: CHERYL ASHE (DEM) 10,012 34.15 (p.3; md "34.16" was off by 0.01). Hunt 9,338 31.85; Wright 9,965 33.99.
- All four boards print "vote for not more than 3", so winners are derivable (edits proposed, medium confidence as derived). Winners: Clay O'Brien, Fountain, Robbins; Greene Jaworski, Hooten, Whitmer; Penn Schmidt, Hahn, Hizer; Portage all three.

## Task 3: 2015 primary (60011, printed UNOFFICIAL REPORTS, run 05/15/15)
- Missing South Bend Dem at-large line: **TOM PRICE 2,549 9.31** (p.3; 8 candidates, vote for 3, 85 of 85 precincts). Percents now sum 99.99. NEW row (loser). High.
- Turnout: the gap text was wrong that no totals exist. Statistics table PDF p.9 (printed "4 of 21") TOTALS row: Registered Voters 112482, Ballots Cast 13642 -> 12.13% (computed; no percent printed). Scope = precincts in the municipal primary (South Bend, Mishawaka, Clay Twp 1), not the whole county. Medium confidence (read, not summed independently).

## Task 4: 2015 general (60010, run 11/03/15)
- Walkerton clerk-treasurer: **TERRI BUCKMASTER (DEM) 166 100.00, Total 166** (p.2). High.
- Lakeville council at-large (p.3, vote for 3, 1 of 1 precinct): DEBRA L. LAW (REP) 62 29.38; MARTHA TYLER (REP) 42 19.91; APRIL L. HATHAWAY (DEM) 63 29.86; KAREN S. IOVINO (DEM) 44 20.85; Total 211 (sum checks). So results.csv is wrong beyond the gap: "Eric L. Hathaway 23.88" should be April L. Hathaway 29.86; "Karen S. Loving" is Iovino with 44 votes, 20.85 (not 20.88); Law and Tyler rows are missing. Name I/L in Iovino is read from a noisy scan (medium).
- Lakeville clerk-treasurer: surname McQUEEN (REP) 71 100.00; first letter clipped at the scan edge (":INDY"), "Cindy" inferred; csv has "Judy Hou...". Medium.

## Task 5: 2018 general (60006, official, run 11/16/18)
- Clay, Greene, Penn, Portage: see Task 2 (pp.2-3).
- Harris trustee opponent: **WILLIAM PRICE (DEM) 4,002 40.92** (p.2). High.
- State Rep District 8: **RYAN M DVORAK (DEM) 14,772 100.00**, NO CANDIDATE FILED 0 (p.1). Replaces the district-wide Ballotpedia 16,141 in results.csv. High.

## Task 6
- **2010 general retention headings (60019 p.6): not an OCR problem.** The page prints bare headings MAY / BROWN / ROBB / CHAMBLEE (yes/no) directly after New Prairie District 2 and before PUBLIC QUESTION, with no court heading anywhere on pp.5-6 (also none on p.4). Gap stays open (narrowed): need Indiana Election Division or courts.in.gov to name the courts (a web search found only that five Court of Appeals judges were on the 2010 ballot; Brown, Elaine B. is one; Robb/Chamblee not confirmed). Do not guess.
- **2012 general (60015): resolved.** p.1 "OFFICIAL RESULTS" (statistics, straight party, president, U.S. Senate, governor, AG, superintendent, U.S. House 2, state senate 8/9/10, state house 5/6/7/8). pp.2-4 "UNOFFICIAL RESULTS" (house 21, county offices, all school boards, retention). Same run stamp 11/16/12 10:34 AM. 23 results.csv rows (straight party, governor, AG, superintendent, state senate 8/9/10, state house 5-8) -> official; the rest stay unofficial.
- **2010 primary (60020, run 05/14/10) and 2011 primary (60018, run 05/17/11):** pp.1-3 carry no OFFICIAL/UNOFFICIAL stamp (checked at zoom). Status stays as the county canvass; gap narrowed to "no stamp printed". (2010 general pp.4-5 print "OFFICIAL RESULTS" partially clipped.)

## Task 7: on-disk
- **2020 general (42820):** office labels all printed and all correct as inferred (p.2 recorder/treasurer; p.3 coroner, surveyor, commissioner 2/3, council D/F/G/I) -> remove gap. Court of Appeals retention: p.6 prints only "COURT OF APPEALS JUDICIAL RETENTION DISTRICT 3 / 5 / 4 / 5" (District 5 printed twice, no judge names anywhere). Unresolvable from this document; look up elsewhere.
- **2024 general (64951, scanned):** Probate judge: printed Total Votes 108,353; Cichowicz 49,793 45.95%, Zappia 58,560 54.05% (p.3/8). results.csv votes already match; the "differ by 10" note is stale (OCR total was the misread). New Prairie at-large (p.5/8): Total 1,854; Smith 1,177 63.48%; Yacullo 677 36.52%. results.csv has Yacullo 877 / 42.70 and Smith 57.30: fix to 677 / 36.52 and 63.48.
- **2022 general (57716):** NOT stale. results.csv has no 2022g Union Township or New Carlisle rows (they exist only in the map data). Summary p.7/10: Union trustee Total 1,206: Kelly Carrico (REP) 726 60.20%, Debra A Watts (IND) 480 39.80%. Union board (vote for 3) Total 2,159: Trisha N Carrico 700 32.42, Ryan Schafer 767 35.53, Mike Wozny 692 32.05. New Carlisle council at-large (vote for 2) Total 358: Marcy Kauffman (DEM) 358 100.00. Bonus not in gap list and also absent from results.csv: North Liberty council at-large (vote for 2) Total 537: Gerry E Brown 287 53.45, Thomas England 250 46.55. Walkerton ward 2 is already 438 in results.csv (no action).

## Counts
- Gaps resolved/removable: 13 (incl. 5 line refs). Narrowed: 5 (2010 retention headings, 2010/11 stamps, 2012 stamps, 2020 CoA names, 2024 OCR). Stale/misdescribed: 2022 (not stale, needs rows), 2024 probate (stale note), 2015 primary turnout (totals exist).
- Edit rows: 104 = 16 NEW results rows, 67 results.csv field changes (corrections, derived winners, 2012 status), 3 elections.csv (2015p), 18 gaps_results.csv rows (13 remove, 5 narrow).

## Caveats
- Party of Fountain (2018 Clay) inferred from truncated "(DE". Lakeville "Iovino" and "Cindy" are scan-quality reads. 2015 primary totals are a printed TOTALS row, not independently summed.
- Winners flagged "derived" follow printed vote-for counts, top N by votes.
- Not touched: 2010 retention court identities, 2020 CoA judge names, 2026 items, pre-2010, public question wording, the other gap rows.
