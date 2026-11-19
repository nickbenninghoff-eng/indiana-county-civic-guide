# Unmatched contests audit (phase 6, 2026-11-16)

`results.csv` has 1,243 contests. `Edition._contest_office` (civic/data.py) gives 1,132 of them an office; the other
111 match no row of `offices.csv`, so they appear on no office's Elections tab. This file lists all 111, one row each,
with a category. No data file was edited.

Method: every unmatched contest was read from `results.csv` (label, candidates, vote-for) and compared with
`offices.csv` (titles, districts, notes) and `terms.csv` (who held which seat when). The categories are the four the
brief asked for:

- **Spelling variant of an existing office**: the contest is plainly an office in `offices.csv` under another id
  spelling, certain from the label, district and year. Only these get an alias.
- **Office missing from offices.csv**: a real office, but not one `offices.csv` lists (statewide offices, state
  appellate judges, a pre-2011 House district).
- **Out of scope**: not an office at all (straight-party tallies, public questions, referendums).
- **Ambiguous**: could be an office in `offices.csv`, but the match is not certain from the label, district and year.

## Result

| Category | Contests |
|---|---|
| Spelling variant of an existing office | 0 |
| Office missing from offices.csv | 68 |
| Out of scope | 28 |
| Ambiguous | 15 |
| Total | 111 |

**No alias was added to `CONTEST_OFFICE_ALIASES`.** None of the 111 is a spelling variant: the existing alias table
(reviewed 2026-11-09) and the derivation rules already catch every spelling of an office that is in `offices.csv`.
What remains is either not in `offices.csv` or needs a decision about which seat it was.

## For the owner's review (not applied)

Two ambiguous contests have strong evidence in the guide's own data. They are not spelling variants (each names a
seat by a different judge than the office id does), so they were left unmatched as the brief requires. If accepted,
each is a one-line alias in `civic/data.py`:

1. `2020g-county-superior-court-retention-chapleau` -> `superior-court-judge-woods`. `terms.csv` row
   `superior-court-judge-woods__chapleau__2021-01` says David Chapleau held that seat and was "Retained 2020 (county
   canvass)". The 2014 Chapleau retention is probably the same seat, but nothing in the data says so for 2014.
2. `2016g-state-retention-judge-hurley` -> `superior-court-judge-hurley`. Elizabeth C. Hurley was appointed to the
   St. Joseph Superior Court in 2013 (`terms.csv`, `offices.csv` notes), so a first retention vote in 2016 fits; but
   the contest is filed with the state retention questions and its label names no court.

Also worth a decision: Osceola's council was elected by ward in 2011 and 2019 (6 contests). `offices.csv` models one
at-large office of 3 seats and its notes say the 2019 canvass was by ward. Either add ward offices (as Walkerton has)
or decide the ward contests belong to the at-large office; until then they stay unmatched.

## Every unmatched contest

| # | contest_id | Label in results.csv | Category | Why |
|---|---|---|---|---|
| 1 | `2010g-county-straight-party` | Straight-party ballots | Out of scope | Straight-party ballot tally: a count of party-ticket ballots, not an office. |
| 2 | `2010g-state-auditor-of-state` | Auditor of State | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 3 | `2010g-state-house-48` | State Representative, District 48 | Office missing from offices.csv | Indiana House District 48 under the pre-2011 lines; offices.csv lists the five current districts (5, 6, 7, 8, 21). |
| 4 | `2010g-state-public-question` | Public Question #1: property tax caps in the state constitution (Art. 10, Sec. 1) | Out of scope | Public question or referendum: not an office. |
| 5 | `2010g-state-retention-brown` | Retention: Brown (court heading not legible) | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 6 | `2010g-state-retention-chamblee` | Retention: Chamblee (court heading not legible) | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 7 | `2010g-state-retention-may` | Retention: May (court heading not legible) | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 8 | `2010g-state-retention-robb` | Retention: Robb (court heading not legible) | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 9 | `2010g-state-secretary-of-state` | Secretary of State | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 10 | `2010g-state-treasurer-of-state` | Treasurer of State | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 11 | `2010p-state-house-48-r` | State Representative, District 48 (Republican primary) | Office missing from offices.csv | Indiana House District 48 under the pre-2011 lines; offices.csv lists the five current districts (5, 6, 7, 8, 21). |
| 12 | `2011g-mishawaka-public-question` | Mishawaka: Public question (text not captured) | Out of scope | Public question or referendum: not an office. |
| 13 | `2011g-mishawaka-straight-party` | Mishawaka: Straight-party ballots | Out of scope | Straight-party ballot tally: a count of party-ticket ballots, not an office. |
| 14 | `2011g-osceola-council-ward-1` | Town of Osceola: Town Council, Ward 1 | Ambiguous | Osceola elected its council by ward (Wards 1 to 3) in these years; offices.csv models one at-large council office of 3 seats (its notes say the 2019 canvass was by ward). Whether each ward is a separate office, or the at-large seats under another name, is a modelling decision, not a spelling. |
| 15 | `2011g-osceola-council-ward-2` | Town of Osceola: Town Council, Ward 2 | Ambiguous | Osceola elected its council by ward (Wards 1 to 3) in these years; offices.csv models one at-large council office of 3 seats (its notes say the 2019 canvass was by ward). Whether each ward is a separate office, or the at-large seats under another name, is a modelling decision, not a spelling. |
| 16 | `2011g-osceola-council-ward-3` | Town of Osceola: Town Council, Ward 3 | Ambiguous | Osceola elected its council by ward (Wards 1 to 3) in these years; offices.csv models one at-large council office of 3 seats (its notes say the 2019 canvass was by ward). Whether each ward is a separate office, or the at-large seats under another name, is a modelling decision, not a spelling. |
| 17 | `2011g-south-bend-straight-party` | South Bend: Straight-party ballots | Out of scope | Straight-party ballot tally: a count of party-ticket ballots, not an office. |
| 18 | `2012g-county-straight-party` | Straight-party ballots | Out of scope | Straight-party ballot tally: a count of party-ticket ballots, not an office. |
| 19 | `2012g-county-superior-court-retention-frese` | Superior Court retention: Frese | Ambiguous | Superior Court retention for a judge whose seat offices.csv does not name (seats are identified by the current incumbent's surname, and the guide's data does not say which seat this judge held). |
| 20 | `2012g-state-attorney-general` | Attorney General | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 21 | `2012g-state-governor` | Governor and Lt. Governor | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 22 | `2012g-state-retention-court-of-appeals-judge-barnes` | Retention: Court of Appeals - Judge Barnes | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 23 | `2012g-state-retention-court-of-appeals-judge-mathias` | Retention: Court of Appeals - Judge Mathias | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 24 | `2012g-state-retention-court-of-appeals-judge-vaidik` | Retention: Court of Appeals - Judge Vaidik | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 25 | `2012g-state-retention-supreme-court-justice-david` | Retention: Supreme Court - Justice David | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 26 | `2012g-state-retention-supreme-court-justice-rucker` | Retention: Supreme Court - Justice Rucker | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 27 | `2012g-state-superintendent` | Superintendent of Public Instruction | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 28 | `2012p-state-governor-d` | Governor (Democratic primary) | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 29 | `2012p-state-governor-r` | Governor (Republican primary) | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 30 | `2013s-mishawaka-public-question` | Mishawaka: Public question (wording not on page) | Out of scope | Public question or referendum: not an office. |
| 31 | `2014g-county-straight-party` | Straight-party ballots | Out of scope | Straight-party ballot tally: a count of party-ticket ballots, not an office. |
| 32 | `2014g-county-superior-court-retention-chapleau` | Superior Court retention: Chapleau | Ambiguous | Superior Court retention for a judge whose seat offices.csv does not name (seats are identified by the current incumbent's surname, and the guide's data does not say which seat this judge held). |
| 33 | `2014g-county-superior-court-retention-miller` | Superior Court retention: Miller | Ambiguous | Superior Court retention for a judge whose seat offices.csv does not name (seats are identified by the current incumbent's surname, and the guide's data does not say which seat this judge held). |
| 34 | `2014g-state-auditor-of-state` | Auditor of State | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 35 | `2014g-state-retention-court-of-appeals-judge-pyle` | Retention: Court of Appeals - Judge Pyle | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 36 | `2014g-state-retention-supreme-court-justice-massa` | Retention: Supreme Court - Justice Massa | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 37 | `2014g-state-retention-supreme-court-justice-rush` | Retention: Supreme Court - Justice Rush | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 38 | `2014g-state-retention-tax-court-judge-wentworth` | Retention: Tax Court - Judge Wentworth | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 39 | `2014g-state-secretary-of-state` | Secretary of State | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 40 | `2014g-state-treasurer-of-state` | Treasurer of State | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 41 | `2015g-county-straight-party` | Straight-party ballots | Out of scope | Straight-party ballot tally: a count of party-ticket ballots, not an office. |
| 42 | `2016g-county-straight-party` | Straight-party ballots | Out of scope | Straight-party ballot tally: a count of party-ticket ballots, not an office. |
| 43 | `2016g-mishawaka-public-question` | Mishawaka: Public question (header printed 'MISH MISHAWAKA') | Out of scope | Public question or referendum: not an office. |
| 44 | `2016g-mishawaka-public-question-fund-levy` | Mishawaka: 'Fund levy' public question | Out of scope | Public question or referendum: not an office. |
| 45 | `2016g-state-attorney-general` | Attorney General | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 46 | `2016g-state-constitutional-amendment` | Constitutional amendment | Out of scope | Public question or referendum: not an office. |
| 47 | `2016g-state-governor` | Governor | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 48 | `2016g-state-retention-judge-crone` | Retention: Judge Crone | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 49 | `2016g-state-retention-judge-hostetler` | Retention: Judge Hostetler | Ambiguous | Probably a St. Joseph Superior Court judge (no court named in the label); no office in offices.csv is identified by the surname Hostetler, so the seat can't be named. |
| 50 | `2016g-state-retention-judge-hurley` | Retention: Judge Hurley | Ambiguous | Probably the St. Joseph Superior Court seat held by Elizabeth C. Hurley (superior-court-judge-hurley; terms.csv: appointed 2013, so a first retention vote in 2016 fits), but the contest is filed with the state retention questions and the label names no court. Not a spelling variant; left unmatched. Proposed alias for review: 2016g state-retention-judge-hurley -> superior-court-judge-hurley. |
| 51 | `2016g-state-retention-judge-riley` | Retention: Judge Riley | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 52 | `2016g-state-superintendent` | Superintendent of Public Instruction | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 53 | `2016p-new-prairie-schools-question-school-public-question` | New Prairie schools: School public question | Out of scope | Public question or referendum: not an office. |
| 54 | `2016p-state-governor-d` | Governor (Democratic primary) | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 55 | `2016p-state-governor-r` | Governor (Republican primary) | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 56 | `2018g-county-straight-party` | Straight-party ballots | Out of scope | Straight-party ballot tally: a count of party-ticket ballots, not an office. |
| 57 | `2018g-state-auditor-of-state` | Auditor of State | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 58 | `2018g-state-retention-court-of-appeals-dist-2-robert-r-bob-altice-jr` | Retention: Court of Appeals Dist. 2 - Robert R. (Bob) Altice Jr. | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 59 | `2018g-state-retention-supreme-court-geoffrey-g-slaughter` | Retention: Supreme Court - Geoffrey G. Slaughter | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 60 | `2018g-state-secretary-of-state` | Secretary of State | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 61 | `2018g-state-state-question` | State question | Out of scope | Public question or referendum: not an office. |
| 62 | `2018g-state-treasurer-of-state` | Treasurer of State | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 63 | `2019g-county-straight-party` | Straight-party ballots | Out of scope | Straight-party ballot tally: a count of party-ticket ballots, not an office. |
| 64 | `2019g-osceola-council-ward-1` | Town of Osceola: Town Council, Ward 1 | Ambiguous | Osceola elected its council by ward (Wards 1 to 3) in these years; offices.csv models one at-large council office of 3 seats (its notes say the 2019 canvass was by ward). Whether each ward is a separate office, or the at-large seats under another name, is a modelling decision, not a spelling. |
| 65 | `2019g-osceola-council-ward-2` | Town of Osceola: Town Council, Ward 2 | Ambiguous | Osceola elected its council by ward (Wards 1 to 3) in these years; offices.csv models one at-large council office of 3 seats (its notes say the 2019 canvass was by ward). Whether each ward is a separate office, or the at-large seats under another name, is a modelling decision, not a spelling. |
| 66 | `2019g-osceola-council-ward-3` | Town of Osceola: Town Council, Ward 3 | Ambiguous | Osceola elected its council by ward (Wards 1 to 3) in these years; offices.csv models one at-large council office of 3 seats (its notes say the 2019 canvass was by ward). Whether each ward is a separate office, or the at-large seats under another name, is a modelling decision, not a spelling. |
| 67 | `2019g-osceola-unknown-office` | Town of Osceola: Town office (header not read) | Ambiguous | The canvass header was not read, so the office is unknown (candidate Denese Thornburg; she ran for Osceola Clerk-Treasurer in 2023, which is suggestive but not proof). |
| 68 | `2020g-county-straight-party` | Straight-party ballots | Out of scope | Straight-party ballot tally: a count of party-ticket ballots, not an office. |
| 69 | `2020g-county-superior-court-retention-chapleau` | Superior Court retention: Chapleau | Ambiguous | Same seat as superior-court-judge-woods per terms.csv (superior-court-judge-woods__chapleau__2021-01: "Retained 2020 (county canvass)"), but the office id names the seat by its current holder (Woods), so this is not a spelling variant. Proposed alias for review: 2020g county-superior-court-retention-chapleau -> superior-court-judge-woods. |
| 70 | `2020g-state-attorney-general` | Attorney General | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 71 | `2020g-state-governor` | Governor and Lt. Governor | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 72 | `2020g-state-retention-court-of-appeals-district-3` | Retention: Court of Appeals (District 3) | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 73 | `2020g-state-retention-court-of-appeals-district-4` | Retention: Court of Appeals (District 4) | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 74 | `2020g-state-retention-court-of-appeals-label-as-printed-district-5-first-listing` | Retention: Court of Appeals (label as printed: District 5, first listing) | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 75 | `2020g-state-retention-court-of-appeals-label-as-printed-district-5-second-listing` | Retention: Court of Appeals (label as printed: District 5, second listing) | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 76 | `2020g-state-retention-justice-of-the-supreme-court-of-indiana` | Retention: Justice of the Supreme Court of Indiana | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 77 | `2020p-south-bend-schools-question-public-question-one` | South Bend Community Schools: Public Question One | Out of scope | Public question or referendum: not an office. |
| 78 | `2020p-south-bend-schools-question-public-question-two` | South Bend Community Schools: Public Question Two | Out of scope | Public question or referendum: not an office. |
| 79 | `2020p-state-governor-d` | Governor (Democratic primary) | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 80 | `2020p-state-governor-r` | Governor (Republican primary) | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 81 | `2022g-county-straight-party` | Straight-party ballots | Out of scope | Straight-party ballot tally: a count of party-ticket ballots, not an office. |
| 82 | `2022g-county-superior-court-retention` | Superior Court retention (St. Joseph County; judge names not captured) | Ambiguous | Superior Court retention for a judge whose seat offices.csv does not name (seats are identified by the current incumbent's surname, and the guide's data does not say which seat this judge held), and the canvass does not give the judge's name. |
| 83 | `2022g-state-auditor-of-state` | Auditor of State | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 84 | `2022g-state-retention-court-of-appeals-3rd-district` | Retention: Court of Appeals (3rd District) | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 85 | `2022g-state-retention-court-of-appeals-5th-district` | Retention: Court of Appeals (5th District) | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 86 | `2022g-state-secretary-of-state` | Secretary of State | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 87 | `2022g-state-treasurer-of-state` | Treasurer of State | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 88 | `2023g-county-straight-party` | Straight-party ballots | Out of scope | Straight-party ballot tally: a count of party-ticket ballots, not an office. |
| 89 | `2023p-mishawaka-schools-question-tax-levy-referendum` | School City of Mishawaka: Tax Levy Referendum | Out of scope | Public question or referendum: not an office. |
| 90 | `2024g-county-public-question-1` | Public Question #1 (wording not captured) | Out of scope | Public question or referendum: not an office. |
| 91 | `2024g-county-straight-party` | Straight-party ballots | Out of scope | Straight-party ballot tally: a count of party-ticket ballots, not an office. |
| 92 | `2024g-state-attorney-general` | Attorney General | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 93 | `2024g-state-governor` | Governor and Lt. Governor | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 94 | `2024g-state-retention-judge-rudolph-reginald-pyle-iii-court-of-appeals` | Retention: Judge Rudolph Reginald Pyle III (Court of Appeals) | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 95 | `2024g-state-retention-justice-derek-read-molter` | Retention: Justice Derek Read Molter | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 96 | `2024g-state-retention-justice-loretta-h-rush` | Retention: Justice Loretta H. Rush | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 97 | `2024g-state-retention-justice-mark-s-massa` | Retention: Justice Mark S. Massa | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 98 | `2024p-state-governor-d` | Governor (Democratic primary) | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 99 | `2024p-state-governor-r` | Governor (Republican primary) | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 100 | `2026g-county-public-question-1` | Public Question #1 (wording not captured) | Out of scope | Public question or referendum: not an office. |
| 101 | `2026g-county-public-question-2` | Public Question #2 (wording not captured) | Out of scope | Public question or referendum: not an office. |
| 102 | `2026g-county-straight-party` | Straight-party ballots | Out of scope | Straight-party ballot tally: a count of party-ticket ballots, not an office. |
| 103 | `2026g-new-prairie-schools-board-at-large-district-2` | New Prairie schools: School Board, At-Large / District 2 | Ambiguous | One canvass line for 'At-Large / District 2' covers two offices in offices.csv (new-prairie-board-at-large, new-prairie-board-d2); it can't be given to one. |
| 104 | `2026g-state-auditor-of-state` | State Comptroller (Auditor of State) | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 105 | `2026g-state-retention-christopher-c-fronk` | Retention: Christopher C. Fronk (court not stated in the canvass) | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 106 | `2026g-state-retention-david-l-francisco` | Retention: David L. Francisco (court not stated in the canvass) | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 107 | `2026g-state-retention-justin-l-mcadam` | Retention: Judge Justin L. McAdam (Indiana Tax Court) | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 108 | `2026g-state-retention-mary-deboer` | Retention: Judge Mary A. DeBoer (Court of Appeals, Fourth District) | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 109 | `2026g-state-retention-paul-a-felix` | Retention: Judge Paul A. Felix (Court of Appeals, Fifth District) | Office missing from offices.csv | Retention of an Indiana appellate judge or justice (Supreme Court, Court of Appeals or Tax Court, or a court the label leaves unstated); state courts are not in offices.csv. |
| 110 | `2026g-state-secretary-of-state` | Secretary of State | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
| 111 | `2026g-state-treasurer-of-state` | Treasurer of State | Office missing from offices.csv | Statewide executive office; offices.csv lists local offices and the county's state legislators only. |
