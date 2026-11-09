# Gap-fill C2: towns and school boards (read 2026-11-08)

Collect-and-report only; no data, code or docs were edited. Proposed changes: `gapfill-2026-11-08-C2-towns-schools-edits.csv` (47 rows). WebSearch calls used: 18 of 25. Chrome tab opened and closed (own tab).

Method note: SBOA reports are text PDFs; `curl` plus `pdftotext -raw` read them reliably. WebFetch summarizes PDFs poorly, so quotes below from SBOA come from the extracted text. The town of New Carlisle's 2023 to 2026 minutes are image scans with no text layer (no OCR available).

## Summary by gap

| # | Gap | Status |
|---|-----|--------|
| 1 Indian Village | council members; 2024 terms | not found |
| 1 Lakeville | start dates; 2024-2026 history | partly (earliest documented dates only; Carr, Rouch not found) |
| 1 North Liberty | Brown start; holders before 2019 | partly filled (Kincaid 2013, Brown President 2014-2019; Brown start inferred 2011-01-01) |
| 1 Roseland | Mudrovich start; Catanzarite replacement; Rulli 2026; council size | not found (Rulli SBOA dates refined) |
| 1 New Carlisle | Pemberton vs Doll; members 2018-2023 | partly (2016, 2020-2022 members sourced; Pemberton/Doll still open) |
| 2 Town cycles | Lakeville, North Liberty, Indian Village | not found; one internal inconsistency flagged for North Liberty |
| 3 2026 seat counts (NC, NL, Roseland) | certified canvass | not fillable yet (county files blocked by Cloudflare; certified canvass not reached) |
| 4 PHM Penn | seat count; Nov 2025 appointee | filled |
| 4 Mishawaka | appointed trustees; seat counts | partly (Roberts, Weber sourced; mayor's appointee only on Ballotpedia) |
| 4 John Glenn | seat counts | filled (7 members: 1/2/2/2, Ballotpedia, lead-level) |
| 4 SBCSC | Robles/Monterrosa | filled |
| 5 Party labels | Moody; others | not resolved (Moody); others confirm NP via Ballotpedia only |

## 4. School boards

### PHM Penn Township (filled)
- Seat count 3. PHM "Board Members and Terms" page (https://www.phmschools.org/board-members-terms, read 2026-11-08): "seven members who serve four-year, staggered terms"; "three people elected from Penn Township"; "two people elected from Harris Township"; "one person elected from Madison Township"; "one person elected at-large". Seat numbers seen: Penn Seat 1, Madison Seat 5, Harris Seat 6, At-Large Seat 7. Confidence high.
- Nov 2025 appointee: Jen (Jennifer) Smoker, Penn Township Seat 1. Matthew Chaffee's resignation was "effective October 8, 2025" (https://www.phmschools.org/2025/10/10/school-board-seeking-applicants-for-penn-twp-seat-1/). Nov 3, 2025 page: "voted unanimously this morning to appoint Mrs. Jennifer (Jen) Smoker"; special meeting Monday Nov 3, 2025; five applicants; interviews Oct 28. Sworn in Saturday Nov 8, 2025 (https://www.phmschools.org/2025/11/09/new-board-member-jen-smoker-sworn-in/). Serves the balance of the term to 2026-12-31. Confidence high.
- Side finding: Dec 1, 2021, the board appointed James Turnwald (Seat #1, vacancy of Karyn Jaye Galloway) and Ryan McCullough (Seat #2, vacancy of Jamie Woods) (https://www.phmschools.org/?p=4377). Existing rows say Woods served to 2024-12-31 and Galloway to 2022-12-31, and McCullough "Incumbent per research"; those should change. Katie Bell's seat is unknown (presumably Seat 3). Chaffee took Seat 1 in the Nov 2022 election (sworn Jan 9, 2023).

### SBCSC at-large (filled; one correction)
- Robles did not resign; she died. ABC57, "Posted: Sep 25, 2017 9:11 AM EST": "the death early this morning of Maritza Robles" (announced Monday morning). https://abc57.com/news/south-bend-school-board-member-maritza-robles-has-died. Confidence medium on the exact day.
- Monterrosa was appointed by the SBCSC board: ABC57 "Posted: Oct 24, 2017 9:44 PM EST": the board "appointed a new board member Tuesday night. Rudy Monterossa was selected"; seat vacant after "the death of Maritza Robles in September"; "seventh seat" (https://www.abc57.com/news/sbcsc-appoints-new-board-member). Start 2017-10-24. ABC57 spells "Monterossa". Vote tally not stated; the finalists (Liggins, Brown) come only from a search snippet.
- Side finding: Sept 16, 2019, the board chose Stephanie Ball 4-2 over Jasmine Brown to fill the seat of Dawn Jones, who became South Bend City Clerk (https://abc57.com/news/south-bend-school-board-votes-on-new-board-member). Existing D4 rows show Jones to 2020-12-31 and Ball from 2021-01-01; proposed fix in the edits CSV.

### School City of Mishawaka (partly)
- Structure: Tribune, July 6, 2022: "School City of Mishawaka voters decided in 2011 to make the school board a hybrid one"; five seats: one appointed by the council, three elected, one by the mayor; four-year terms (https://www.yahoo.com/news/retired-longtime-beiger-elementary-teacher-145251903.html). Elected seats in data: 3 (Parks, Layman, Johnson).
- Council appointee: Amanda Roberts (first appointed Nov 2017, began Jan 2018 per a search snippet; stepped down June 2022; Tribune June 10, 2022: "The Mishawaka common council appoints her replacement") then David Weber, appointed Tuesday July 5, 2022 by the Mishawaka Common Council, "a four-year term ending in December 2025". ABC57 July 15, 2022 says the same ("Weber's term on the board will last through December of 2025"). Confidence medium.
- Ballotpedia (lead only, read 2026-11-08) lists: David Weber (term ends 2029), Mellissa Johnson 2028, Angela Layman 2028, Holly Parks 2026, William Pemberton 2026. So Weber was apparently reappointed late 2025 and William Pemberton is the other appointee (presumably the mayor's), unconfirmed by a primary source. Not found: appointment dates for Pemberton and the 2025 reappointment; the school corporation board page returned 404 at the URL guessed.
- Seat counts: 5 total, 3 elected. Conflict: Ballotpedia headed the 2026 race "At-large (2 seats)" but listed one candidate (Holly Parks); the data's single seat for 2026 matches the 2024/2022 cycles.

### John Glenn (filled, lead-level)
Ballotpedia: "seven members serving four-year terms"; Liberty Township (Carson, Mattix), Lincoln (Jaworski, Smith), Polk (Egger, McGaughey), Johnson (Knowlton): so 2/2/2/1, matching the offices rows. Only Lincoln Township's holder Kathy Jaworski is absent from terms.csv; likely the 2024 winner. 2026: Carson, McGaughey uncontested, Smith vs Metz. Confidence medium (Ballotpedia).

## 5. Party labels
- Moody: Ballotpedia (read in Chrome 2026-11-08): "Cheryl H. Moody (Independent)". The county file 73081 could not be read: sjcindiana.gov served a Cloudflare challenge to curl and 403 to WebFetch, and Chrome's PDF viewer exposed no text and blocked screenshots. Unresolved; keep the conflict note.
- Ballotpedia shows "No Party Affiliation" for Holly Parks (Mishawaka) and Carson, Metz, Smith, McGaughey (John Glenn). These match the existing NP values; this is corroboration from one non-primary source.

## 1 and 2. Towns

### Lakeville (partly)
SBOA 000000416A (financial statements audit 2019-2022, filed 08/23/2023, https://www.in.gov/sboa/WebReports/000000416A.pdf), Schedule of Officials: Clerk-Treasurer Shirley Rynearson 01-01-19 to 06-25-19; Lori L. Kelly (interim) 06-26-19 to 12-31-19; Christine Rowe 01-01-20 to 12-31-23. President of the Town Council: April Hathaway 01-01-19 to 12-31-19; Lori L. Kelly 01-01-20 to 12-31-23. Utility Office Manager Dan Casad, then Larry Clady (from 03-30-22).
- Proposed: Kelly start 2020-01-01 and Hathaway start 2019-01-01 as earliest documented dates (true starts may be earlier). Confidence medium.
- Carr (Clerk-Treasurer): no source; Rowe's term ended 2023-12-31, so 2024-01-01 is only an inference. Dean Rouch: no source. No SBOA report after 2023 for Lakeville was located (search returned none). Lakeville's town website (townoflakevilleindiana.com) lists no officials or minutes on its home page (meetings 1st Monday 6 PM).
- Cycle: not found. Data shows 2011 and 2015 Lakeville races (odd years), consistent with 2019/2023/2027, unconfirmed.

### North Liberty (partly)
- Council page (https://www.in.gov/towns/northliberty/council, 2026-11-08): "Our Town Council is a five person council": Randy Lemert, Tom England, Will Groves, Gerry Brown, Joe Reed, Jr.
- SBOA B49836 (2013-2016 examination, filed 04/06/2018): President of the Town Council: Jayson Kincaid 01-01-13 to 12-31-13; Gerry E. Brown 01-01-14 to 12-31-18. B54839 (2017-2018, filed 04/07/2020): Brown 01-01-17 to 12-31-19, Randy Lemert 01-01-20 to 12-31-20. B55553 (2019, filed 08/10/2020): Brown 01-01-19 to 12-31-19; Lemert 2020. B59962 (2020-2021): Lemert 01-01-20 to 12-31-22; 81943A (2022-2023, filed 12/19/2024): Lemert 01-01-22 to 12-31-23. Clerk-Treasurer Vicki Kitchen throughout (01-01-12 onward).
- So Brown was Council President from 2014 through 2019, and Kincaid was President in 2013 (holder before 2019). Brown start: the data's own 2010g canvass has him winning, so 2011-01-01 is a reasonable inferred start (medium).
- Cycle flag (internal): North Liberty council races appear in 2010 and 2014 (even years) and 2026, so the Brown/England seats likely run 2026, 2030; offices.csv's next_election 2027 should be reviewed. Not externally confirmed.

### Roseland (not found, refinements)
- SBOA 78484A (compliance engagement 2020-2023, filed 12/02/2024): Clerk-Treasurer Robin Ackerson 01-01-20 to 12-31-23; Shane Williams-Inez 01-01-24 to 09-28-24; Ann Rulli 09-29-24 to 12-31-24. President of the Town Council: Elizabeth McCombs 01-01-20 to 12-31-23; Michael Schalk 01-01-24 to 12-31-24. Existing rows use 2024-09-30 (meeting date); SBOA is 09-28/09-29.
- Rulli in 2026: unknown. 953mnc July 21, 2026: "the current clerk-treasurer has been working without pay since January" (unnamed). ABC57 May 14, 2026: Schalk refers to "our prior clerk that was in office and his assistant"; no current clerk named. (953mnc spells the president "Jeff Schalk" in July; ABC57 and SBOA say Mike/Michael.)
- Catanzarite's replacement, Mudrovich start, council size: no source found. No official Roseland town website found (townofroseland.org is a different, out-of-state town; in.gov/towns/roseland 404). Wikipedia: "The town has three council members and a Clerk-Treasurer." Data pattern: 2022 one seat, 2023 two seats, fitting 1+2=3, while the reported 3-2 vote (not re-found) does not.
- Not searched: the SBOA special investigation report itself (filed 12/31/2025); ABC57 embeds it without a URL.

### New Carlisle (partly)
- Minutes with text: Jan 14, 2016 council: Vojtko, Carter, Rypma, Vermillion, Budreau; Clerk-Treasurer Susan Moffitt. July 21, 2020: "President Kauffman called the meeting to order with Council Member Rush, Council Member Doll, Council Member Colanese and Clerk-Treasurer Susan Moffitt present. Vice President Budreau was absent." Jan 12, 2021: Kauffman, Rush, Doll, Colanese present, Budreau absent; "Samantha Rush was elected to serve as Council President for 2021"; Kauffman elected VP. Jan 4, 2022: Rush, Budreau, Doll, Colanese present, Kauffman absent; Rush president, Kauffman VP for 2022. (URLs in the edits CSV.) Which Doll is not stated (Dave Doll likely; Jill Doll appears as an attendee).
- Pemberton vs Doll: the town's "Council Resources" pages for 2022, 2023, 2024 and 2025 all show the same five (Kauffman, Doll VP, Colanese, Short, Abbott). Since the 2022 page also shows Short and Abbott, who joined in 2023, these year pages are template-copied and are not reliable evidence that Doll held the seat. The 2025 page's latest minutes are Dec 16, 2025. The current page shows Pemberton; she is not on the 2025 page. Status: unresolved; the change likely occurred between Dec 2025 and May 2026 or the earlier pages were never updated.

### Indian Village (not found)
One WebSearch returned nothing. Existing data (SBOA 81337A via GOV-128) already shows Jozwiak and Oppenheim with a listed term to 12-31-26. No new facts.

## 3. 2026 seat counts (not fillable yet)
The county file (DocumentCenter 73081) and a certified canvass could not be reached (Cloudflare). No town notice found. Evidence from earlier cycles supports the existing inferences (New Carlisle 2, North Liberty 2: SBOA-independent 2010/2014 canvasses show two-seat races; Roseland 1).

## Conflicts
- Moody: Ballotpedia Independent vs county file unread.
- Mishawaka 2026 seats: Ballotpedia "2 seats" vs 1 in data.
- New Carlisle VP: Doll vs Pemberton (unresolved; archive pages unreliable).
- Roseland: council of 3 vs 3-2 vote.
- Rulli dates: SBOA 09-29-24 vs WNDU meeting 09-30-24.
- PHM page caption "Appointed Nov 8" vs official appointment Nov 3 (Nov 8 was the oath).

## Failed or unproductive URLs
- https://www.sjcindiana.gov/DocumentCenter/View/73081: Cloudflare challenge (curl), 403 (WebFetch), Chrome PDF viewer: no text, screenshot blocked.
- https://ballotpedia.org/... via WebFetch: empty (worked in Chrome).
- https://www.phmschools.org/board-of-school-trustees: no member list.
- https://www.mishawakaschools.com/about-us/board-of-trustees: 404.
- https://www.in.gov/towns/roseland/, /lakeville/, /indianvillage/: 404. https://www.townofroseland.org: wrong town.
- WebFetch of PDFs (SBOA 78484A, New Carlisle minutes): garbage output; used curl and pdftotext instead.
- New Carlisle 2023-2026 minutes and agendas: image scans (no text).
- Not searched: WNDU Roseland coverage, Lakeville/North Liberty/Indian Village ordinances, Lakeville canvass 2019/2023, Indian Village cycle.
