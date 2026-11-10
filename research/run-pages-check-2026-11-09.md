# Run for office pages: check against official rules (2026-11-09)

Scope: `run/index.html` and the six office pages (`run/city-council/`, `county-council/`, `precinct-committeeperson/`,
`school-board/`, `township-board/`, `township-trustee/`), plus the 2027 dates on `elections/calendar/` and the shared
rule rows on `elections/how-it-works/`. Generator: `tools/site/pages/participate.py`. Rule data:
`data/indiana/election_rules.csv`. Gap rows: `data/editions/st-joseph/gaps_services.csv` (area `run`).

## Sources read (copies in `sources/elections-run/`, git-ignored)

| Id | Document | Notes |
|---|---|---|
| IND-078 (new) | Indiana Election Division, **2027 Indiana Election Calendar brochure** (`in.gov/sos/elections/files/2027%20Calendar%20Brochure.FINAL.pdf`) | "reflects Indiana law as of August 2026". The official 2027 dates. |
| IND-079 (new) | **2026 Indiana Candidate Guide** (`in.gov/dA/1eada35c3e/2026-Candidate-Guide.FINAL.pdf`) | The latest guide. A 2027 guide is not posted yet (candidate-information page checked 2026-11-09). |
| IND-080 (new) | **2026 Campaign Finance Manual**, revised July 2026 | CFA-1 and report rules. |
| IND-081 (new) | FindLaw IC 3-10-1-4.5 and 3-10-1-4.6 ("Current as of January 01, 2026") | Precinct committeemen election years. |
| IND-082 (new) | FindLaw IC 3-8-2-7 | Party-affiliation test for declarations. |
| IND-011 (note updated) | FindLaw IC 3-13-11-3, -5, -10 | Local vacancy caucus. |
| also read | FindLaw IC 3-8-1-21, -26, -27; IC 36-6-4-2; IC 36-2-3-2, -4; IC 3-13-5-1 | Residency, trustee, county council, legislative caucus. |
| also read | Election Division candidate-information page (form list) | CAN-44 "Petition of Nomination for City or Town Office in 2027" is posted; CAN-42 (2027) is not yet listed. |
| also read | 2026 Indiana Election Legislation Summary (IND-001) | HEA 1377 straight-party change; no 2026 change to filing windows found. |
| also read | Wayback: sjcindiana.gov /2387 (2026-04-03) and /2229 (2025-05-16) | The county site returns 403 to scripts. |

Justia still returns 403; FindLaw worked. No WebSearch calls were used (0 of 30).

## Claims checked

Result key: **OK** (source agrees), **fixed** (source said otherwise; changed), **upgraded** (value was right but marked
computed or unsourced; now cited to the official document), **unverified** (not confirmed; not changed).

### Dates and filing windows (2027 municipal election)

| Page | Claim | Source | Result |
|---|---|---|---|
| run/, office pages, calendar | Municipal primary Tue May 4, 2027; municipal election Tue Nov 2, 2027 | IND-078 | OK (pages still badge them COMPUTED from the calendar rule, which is accurate) |
| run/, run/city-council/, calendar | Declaration deadline noon Fri Feb 5, 2027, with the county election board | IND-078 (Feb 5 entry); IND-079 p. 20 (city offices file with the county election board) | OK |
| run/, run/city-council/ | "Opening day: Confirm with the county election office" | IND-078: Jan 6, 2027 is the first day | upgraded: page now says Jan 6, 2027 |
| rules (municipal_2027_filing) | Jan 6 opening and June 30 petition deadline "computed from IC 3-8-2-4 and IC 3-8-6-10" | IND-078 prints both | upgraded (confidence medium to high) |
| run/ | 2027 petitions: form CAN-44 | Election Division form list | OK |
| run/ | 2027 petition window and consent | IND-078: Jan 6 to noon June 30 at the county voter registration office; consent and certified petition by noon July 15 | upgraded: added to the page (was "Confirm") |
| run/ | Petition signature number | IC 3-8-6-3 (IND-069): 2% of the last Secretary of State vote in the district | now stated as the rule; district counts still "Confirm" |
| calendar | Registration ends Apr 5 / Oct 4, 2027; early voting starts Apr 6 / Oct 5; mail-ballot applications by Apr 22 / Oct 21 | IND-078 | OK |
| run/ | "Filing windows for 2028 and 2030 not in the guide's data" | IND-079 lists only 2026 | OK (not published) |

### Forms and where to file

| Page | Claim | Source | Result |
|---|---|---|---|
| run/ | CAN-2 = 2026 primary declaration; CAN-42 = 2027 municipal primary declaration, filed with CAN-12 | IND-079 p. 20; form list | OK |
| run/, run/precinct-committeeperson/ | Precinct committeeperson candidates file CAN-37 | IND-079 p. 12, p. 133 | OK |
| run/ | Towns under 3,500 hold a major-party primary only by ordinance | IND-079 p. 107 ("large towns" definition); IND-078 small-town convention entries | OK |
| run/ | 2026 petition forms "CAN-19 (state and legislative), CAN-21 (local), CAN-34 (school board); due at noon June 30" | IND-079 pp. 13, 18, 105: CAN-34 had its own window, May 19 to noon June 18, 2026 | **fixed** (CAN-34 split out; CAN-19 described as federal, state, legislative) |
| run/school-board/ | "Candidates reach the ballot through a party primary or by petition" | IND-079 pp. 104-105: no primary; every school board candidate files a petition (CAN-34) and CAN-12 with the county election board | **fixed** |
| rules (school_board_filing; not rendered on these pages) | Filed "with the county voter registration office" | IND-079 p. 105: with the county election board of the county holding most of the corporation's population (IC 3-8-2-6) | **fixed** |
| run/ contacts | The election board takes candidate filings for county and city offices | IND-079 pp. 20-21; county page /2387 (Wayback 2026-04-03) | OK |
| run/ contacts | Board: one Democrat, one Republican, the County Clerk as secretary | county page /2387 (Wayback 2026-04-03) | OK |
| run/ contacts | Phone 574-235-9635, voter@sjcindiana.gov | county page /2229 (Wayback 2025-05-16) | OK |
| run/ contacts | "County-City Building, 4th Floor, 227 W. Jefferson Blvd." | Only Wayback copy (May 2025) says "County-City Building, Basement, 101 S. Main St."; research/11 (read 2026-11-07, newer staff list) says 4th Floor | **OK** — browser check 2026-11-09 of the live sjcindiana.gov/2229/Contact-Us: 4th Floor, 227 W. Jefferson Blvd.; phone and email match |

### Qualifications and party rules

| Page | Claim | Source | Result |
|---|---|---|---|
| run/ | "The only residence rule in the guide's data is that a township trustee must live in the township" | The rules table has had the registration (IC 3-8-1-1) and residency (IC 3-8-1-20 to -34) rules since 2026-11-08; IND-079 pp. 7, 81, 103; FindLaw IC 3-8-1-21, -26, -27 | **fixed**: page now states registration by the filing deadline and the residency periods |
| run/township-trustee/ | Trustee must live in the township; term starts Jan 1 after the election; 4-year term | FindLaw IC 36-6-4-2(b), (c) | OK |
| run/ , how-it-works | "A candidate's two most recent primary votes must match the party they run under" | IC 3-8-2-7(a)(4) (IND-082); IND-079 pp. 3, 11: or a certification from the party's county chair | **fixed** (both routes stated) |
| run/, run/school-board/, how-it-works | School board: "A candidate's last two primary votes must match any party they list" | IND-079 p. 105: Democratic or Republican label needs the two-primary history or a county chair's certification; minor-party, independent or no-party choices cannot be challenged on party grounds | **fixed** |
| run/, school board | Since 2025 (SEA 287) a candidate may list a party, independent or no party; no primary | IND-079 p. 105 | OK |
| run/county-council/ hero | Counties of 185,000 to 300,000 that opt in have nine single-member council districts | FindLaw IC 36-2-3-2(b), 36-2-3-4(c) | OK (statute). That St. Joseph County opted in stays UNVERIFIED as the page already says |
| run/ | Minimum age | IND-079: no general minimum age; IC 20-26-4-9 only bars disqualifying a school board member who is at least 18 | unverified; page still says "Confirm" |
| run/ | Party primary basics (no party registration; poll-worker challenge) | Ballotpedia (IND-041) | not re-checked |

### Precinct committeeperson

| Page | Claim | Source | Result |
|---|---|---|---|
| rules, gap row, how-it-works | Elected May 2026, 2030 ...; "the next election is the May 2030 primary" | IC 3-10-1-4.6 (IND-081): Republican committeemen 2024, 2028, 2032; IC 3-10-1-4.5: others 2026, 2030; IND-079 p. 3: Democratic on the 2026 ballot, Republican in 2028 | **fixed** |
| run/precinct-committeeperson/, run/ card | "Term length and next election year: Confirm" | same | upgraded: Democratic next May 2030, Republican next May 2028 |
| run/precinct-committeeperson/ | (added) no CAN-12 and no campaign-finance reports | IND-079 pp. 11, 36, 133; IND-080 p. 10 | added from source |
| run/precinct-committeeperson/ | County chairs are elected by the committeepersons | party rules, not read | unverified (stays LOW CONFIDENCE) |
| run/precinct-committeeperson/ | Filing window: Confirm | 2028/2030 windows not published | OK as worded |
| run/precinct-committeeperson/ | Legislative vacancy filled by a caucus of the party's committeepersons from the district | FindLaw IC 3-13-5-1 | OK |

### Campaign finance

| Page | Claim | Source | Result |
|---|---|---|---|
| run/, office pages | County, city, township and school board candidates report to the county (badge said "not checked against statute text") | IND-079 pp. 35-36 | OK; badge now OFFICIAL with IND-079 |
| run/ | "Due dates: Confirm. The guide's rules table has no campaign-finance schedule yet" | The rules table has local_candidate_reports; IND-078 prints the 2027 dates | **fixed**: pre-primary noon Apr 16, 2027 (period ends Apr 9); pre-election noon Oct 15, 2027 (period ends Oct 8); annual noon Jan 19, 2028 (for 2027) and Jan 20, 2027 (for 2026) |
| run/ | (added) CFA-1 committee timing; $500 threshold for school board and offices paying under $5,000 | IND-080 pp. 9-10 (IC 3-9-1-5, -5.5) | added from source |
| rules (local_candidate_reports) | 2027 dates "computed from the statute" | IND-078 | upgraded (values unchanged) |
| run/ | County posts scanned CFA-4 and CFA-11 filings | sjcindiana.gov (403 to scripts) | unverified: needs browser check (not a rule) |

### Vacancies

| Page | Claim | Source | Result |
|---|---|---|---|
| run/, how-it-works, places | County chair gives notice within 10 days | IC 3-13-11-3(a) | OK |
| same | Committeepersons "in precincts that voted for the departing official" take part | IC 3-13-11-5(a)(2): precincts whose voters were eligible to vote for the official at the last election | **fixed** (old wording read as "precincts the official carried") |
| same | Appointed committeepersons must have served 30 days before the vacancy | IC 3-13-11-5(b) | OK |
| same | "Selection is by secret ballot" | IC 3-13-11-10: majority vote; secret ballot if more than one person seeks the seat | **fixed** |
| same | Pro tempore under Art. 2 sec. 11 | IC 3-13-11-1 | OK |

### Terms, seats, partisan status, other

| Page | Claim | Source | Result |
|---|---|---|---|
| office pages | 4-year terms (city council, county council, school board, township board, trustee) | Trustee: IC 36-6-4-2(c). Others from office_types.csv | trustee OK; others not re-read |
| office pages | Seat counts and next-election years by government | offices.csv (covered by the 2026-11-09 government fact-check) | not re-checked here |
| run/township-board/ | Township officials elected 2026, next 2030 | IND-079 p. 89 (all township officials elected in 2026; boards may stagger terms by resolution, IC 36-6-6-2.3) | OK; whether any SJC township board adopted staggering: unverified |
| run/township-board/, run/city-council/ | From 2027 straight-party votes count for at-large races unless the voter marks individual candidates; not school board | IND-001 p. 3 (HEA 1377) | OK |
| how-it-works | Resign-to-run, dual office, Hatch Act | not stated on the run pages | n/a |

## Counts

- Claim rows: 48.
- OK: 22. Fixed: 10. Upgraded from "Confirm" or computed to an official statement: 6. Added from source: 2.
  Unverified: 5 (contact floor/address, posted CFA filings, minimum age, county-chair rule, plus the partial items
  county council opt-in and township board staggering inside OK rows). Not re-checked: 2 (Ballotpedia primary
  details; seat counts and non-trustee term lengths from offices.csv). n/a: 1.

## Time-sensitive: re-check when the 2027 Candidate Guide is published

1. The 2027 brochure reflects law "as of August 2026". The 2027 General Assembly session (January to April 2027) can
   change election law; most changes take effect July 1, after the Feb 5 deadline, but check the 2027 legislation summary.
2. CAN-42 (2027) is not yet on the Election Division form list (CAN-44 is). Confirm the form number and the CAN-12
   revision when forms are released (usually at the December clerks' conference).
3. The 2027 Candidate Guide's city chapter: city residency, CFA-1 deadline for city candidates (7 days after Feb 5 is
   noon Feb 12, 2027, computed, not stated on the page), and the withdrawal deadline (noon Feb 12, 2027 in the brochure;
   not on the page).
4. Petition signature counts per district from the certified November 2026 Secretary of State vote (the gap row).
5. Contact card: confirm the County Election Board's current room (4th floor, 227 W. Jefferson vs basement, 101 S. Main) — done 2026-11-09: 4th floor confirmed in the browser
   in a browser on sjcindiana.gov/2229.

## Left for the main session (not changed)

- `elections/how-it-works/` gap rows from `gaps_elections.csv` are stale: "Primary filing deadlines and signature
  requirements ... The 2026 candidate guide PDF returned 404" (it is now on in.gov) and "Precinct committeeperson term
  (4 years) ... Read IC 3-6-5" (the statute is IC 3-10-1-4.5/4.6). Not run pages, so not edited.
- Office pages still say "Age, length of residence and voter-registration rules for this office: Confirm". Correct but
  thinner than run/index, which now states the rules.
- The run/ "Pick an office" cards and office pages still badge the 2027 dates COMPUTED; the brochure now prints them.
