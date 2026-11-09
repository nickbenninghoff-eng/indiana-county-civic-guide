# Town research pass: Indian Village, Lakeville, New Carlisle, North Liberty, Roseland

Collected 2026-11-08. Proposed edits: `planning/qa/data-edits-towns.csv` (100 rows; new source ids are in a GOV-201 to GOV-219 block so they cannot collide with other QA agents). Nothing in `data/` was edited. WebSearch calls used: 19 of 30. Saved copies of the primary documents are in `sources/towns/` (PDF and docx only).

All fetched text was treated as data. No personal addresses, phones or e-mails were recorded. gopsjc.com was not used.

## Summary table

| Town | Council size | Current holders | Cycle | Main remaining gap |
|---|---|---|---|---|
| New Carlisle | 5 (official page) | Fully sourced, official | 2 seats 2022/2026, 3 seats 2023/2027 | Council members 2018-2023 individually; Brown's start; Pemberton vs Doll |
| North Liberty | 5 (minutes, 5/0 votes) | Fully sourced, official | Inferred (2 and 3 split) | Term dates; who holds the 3 non-2026 seats' terms |
| Lakeville | 3 (inferred from signature block) | Fully sourced (town-published minutes) | Inferred 2027 | Start dates; election history after 2015 |
| Roseland | 3 (Wikipedia, WNDU indirectly) | Partly: clerk change found, council replacement not | 1 seat 2022/2026, 2 seats 2023/2027 | Catanzarite's replacement; 3-2 vote puzzle |
| Indian Village | Not documented | Historical only (to 2019) | Unknown | Everything current |

## New Carlisle

**Found (official).**
- Town Council page (https://townofnewcarlisle.in.gov/town-council/): Marcy Kauffman, President (1/1/2023-12/31/2026); Jerry Colanese, Vice President (1/1/2024-12/31/2027); Nancy Pemberton (2024-2027); William Short (2023-2026); Alison Abbott (2024-2027). The page says terms are four years, staggered.
- May 5, 2026 minutes (https://townofnewcarlisle.in.gov/wp-content/uploads/2026/05/Minutes-5-5-2026-General-Meeting.pdf, read directly): Kauffman, Colanese and Pemberton present; Short and Abbott absent. Roster matches.
- Clerk-Treasurer page (https://townofnewcarlisle.in.gov/departments/clerk-treasurer/): Julie Brown, Clerk-Treasurer; Yvonne Hoffmaster, Deputy Clerk. No term dates.
- SBOA schedule 2019-2023 (https://www.in.gov/sboa/WebReports/000000951A.pdf, read directly): Clerk-Treasurer Susan I. Moffitt 1/1/2019-12/31/2023. Council presidents: Kenneth Carter (2019), Kauffman (2020), Samantha Rush (2021-2022), Kauffman (2023).
- SBOA 2015-2018 supplemental (https://www.in.gov/sboa/WebReports/B53320.pdf): July 30, 2019 exit conference names Moffitt, Carter (President), Dan Vermillion (Vice President) and Kauffman (council member). Its schedule-of-officials layout is ambiguous for Moffitt's dates, so only the 2019-2023 term is proposed.

**Seat count and cycle.** Five seats. Two terms end 12/31/2026 (Kauffman, Short), three end 12/31/2027 (Colanese, Pemberton, Abbott). That explains why the canvasses show vote-for-3 in 2011/2015/2019 and a two-seat contest in 2018: only the seats up that year are counted. The old "3 seats" in offices.csv should become 5.

**2026 result (unofficial).** Candidates in the county summary: Kauffman 334, Dan Caruso 245, Marcel Lebbin 228. With two seats expiring, Kauffman and Caruso win. William Short does not appear in the summary. This depends on the two-seat reading, so Caruso is proposed at medium, not high. Check against the certified canvass.

**Conflicts and oddities.**
- The town's `council-years/2025` page (https://townofnewcarlisle.in.gov/council-years/2025/) lists Dave Doll as Vice President and no Pemberton; the current page and May 2026 minutes show Pemberton and Colanese as Vice President. Doll is a 2019 council winner (scan) and may have held the 2024-2027 seat Pemberton now shows. When and why the change happened was not found. Not resolved in the data.
- Marcellus (Marcel) Lebbin, the 2026 Republican candidate, is named as Town Attorney in North Liberty's September 2026 minutes. Reported as a fact; no inference drawn.
- The PDF metadata on the town's agendas and minutes lists "Sue Moffitt" as author, and a search summary describes her as Special Projects Assistant in 2024-2026 (May 5, 2026 minutes list "Special Projects Assistant Susan Moffitt"). Do not confuse her with the current Clerk-Treasurer.

**Not found.** Individual council members 2018-2023 (only presidents and the July 2019 trio are sourced; the 2018 and 2019 canvass winners are flagged uncertain in the scans); how and when Julie Brown took office (start 1/1/2024 is inferred); Brown's party; New Carlisle minutes before 2024 are mostly scanned images (no text layer, no OCR available), so Dec 2025 and January 2023 minutes could not be read.

## North Liberty

**Found (official).**
- Sept 8, 2026 minutes (https://www.in.gov/dA/1d8a7a65bb/minutes.09082026.docx?language_id=1, read directly): council members Randy Lemert (President), Will Groves Jr., Joe Reed, Tom England, Gerry Brown; Clerk-Treasurer Vicki Kitchen; Town Attorney Marcel Lebbin; consent agenda passed 5/0.
- Dec 1, 2025 minutes (https://www.in.gov/towns/northliberty/files/minutes/2025/minutes.12012025.docx, read directly): the same five names; another vote recorded 5/0. This upgrades the five-seat count from "search summary" to read directly.
- Departments page (https://www.in.gov/towns/northliberty/departments): Vicki Kitchen, Clerk/Treasurer; Jackie James, Deputy Clerk. No council roster.
- SBOA schedules: Kitchen as Clerk-Treasurer 1/1/2019-12/31/2019 (B55553) and 1/1/2020-12/31/2022 (B59963); Randy Lemert President of the Town Council 1/1/2020-12/31/2022; Gerry E. Brown President in 2019. The 2012-2019 schedule (B49836) layout is ambiguous (Kitchen possibly from 2013).
- Aug 18 and Nov 3, 2025 minutes (search summaries, not read): Aug lists Tom England; Nov lists four members without England (probably absent).

**2026.** Brown 283 and England 224 were the only two candidates on the county summary (both Republican per earlier canvasses). The 2010 and 2014 canvasses were vote-for-2 for this same pair of seats, so two seats is the likely structure and both incumbents are the unofficial winners. The other three seats (Lemert, Groves, Reed) would then fall in 2027. Confidence low-medium; no source states it.

**Not found.** Term dates for any member; Brown's and England's start years; holders before 2019 other than Brown (council president 2019) and Kitchen; whether the council is at-large (canvasses say "At-Large"; not otherwise confirmed). The town site (in.gov/towns/northliberty) has no roster page.

## Lakeville

**Found.**
- Town Council minutes, Oct 5, 2026 (https://img1.wsimg.com/blobby/go/c7045ec4-b10d-4ded-9cb7-8e1fe9faee4f/Untitled%20document%20(7).pdf, linked from https://townoflakevilleindiana.com/ under "Town Clerk"; read directly): Town President Lori Kelly, Vice President April Hathaway, Board Member Dean Rouch (absent that night); Clerk-Treasurer Nicole Carr. Signature block has exactly three names.
- November 2026 newsletter (https://img1.wsimg.com/blobby/go/c7045ec4-b10d-4ded-9cb7-8e1fe9faee4f/November2026%20Lakeville%20Newsletter%20(4).pdf): Clerk Nicole Carr, Deputy Clerk Cindy McCan; Town Board meeting Nov 2, 2026.
- Council meets the first Monday of each month (town site).

**Seat count.** Three is read from the signature block and matches the 2011 vote-for-3. The town publishes no statement of size, so this is medium-high, not high. Rouch's absence does not change the count.

**Oddities.** SBOA (GOV-093) lists "Lori L. Kelly (interim)" as Clerk-Treasurer for 6/26/2019-12/31/2019. Whether she is the same person as the current Town President is not confirmed. The older site lakevilleindiana.org now redirects to a private WordPress site, so it is not usable. Christine Rowe is the last SBOA-listed Clerk-Treasurer (through 12/31/2023); Carr's start date is unknown.

**Not found.** Start dates and party for all four people; election history after 2015; the cycle (2027 inferred from the clerk-treasurer pattern, low confidence).

## Roseland

**Found.**
- WNDU Sept 30, 2024 (https://www.wndu.com/2024/09/30/roseland-town-council-accepts-clerk-treasurers-resignation-elects-new-one): council accepted Shane Williams-Inez's resignation and elected Ann Rulli Clerk-Treasurer by a 3-2 vote at a special meeting. ABC57 (https://www.abc57.com/news/state-board-of-accounts-investigating-roslands-finances): his term was 1/1/2024-12/31/2027, resignation effective Sept 30, 2024; SBOA special investigation report filed Dec 31, 2025 (covers 2024). WSBT reports the matter was referred to the Indiana Attorney General and the county prosecutor (search summary; not read).
- WNDU Feb 6, 2025 (https://www.wndu.com/2025/02/06/another-roseland-town-council-member-resigns): Councilman Ryan Catanzarite resigned effective Jan 31, 2025; the "two remaining" members were to choose a replacement Feb 13. The replacement was not found.
- Wikipedia (https://en.wikipedia.org/wiki/Roseland,_Indiana): "The town has three council members and a Clerk-Treasurer." No citation was visible for that line, so it is secondary and flagged.
- ABC57 and 95.3 MNC, May-July 2026: Mike Schalk is Town Council President. One 95.3 MNC item prints his first name as "Jeff"; every other source, and the 2023 canvass, says Mike. No current clerk-treasurer or other council member is named in those reports.

**Seat count.** Three is consistent with: Wikipedia; WNDU's "two remaining" after Catanzarite left; one seat on the 2022 ballot (Newman) and two on 2023 (Schalk, Catanzarite). This also fits one seat up in 2026 (Mudrovich 104, Clark 59). Proposed: next election 2027 (two seats), Mudrovich confidence low to medium (still unofficial).

**Conflict not resolved: the 3-2 vote.** A 3-2 vote does not fit a three-member council. Possible explanations (none verified): the vote was a different body or included non-council voters; the council was larger than three; or the reported tally is wrong. This is the same caveat already in the offices.csv notes; this pass found no source that settles it. No vacancy-filling rule was read (IC 3-13-9-3 and similar pages returned HTTP 429).

**Not found.** Who replaced Catanzarite in Feb 2025; whether Ann Rulli is still Clerk-Treasurer in 2026; Roseland's own website (townofroseland.org is Roseland, a different place; in.gov/towns/roseland returned 404); the SBOA special investigation report itself.

## Indian Village

**Found (historical only).**
- SBOA 2013-2016 report (https://www.in.gov/sboa/WebReports/B49995.pdf, read directly): Clerk-Treasurer Suzette Jozwiak, 1/1/2012-12/31/2019; President of the Town Council Geraldine Oppenheim, 1/1/2013-12/31/2018; Deputy Clerk-Treasurer Michael Eby; exit conference Feb 12, 2018. It says the Town Council had not adopted internal-control standards, so there is a council, but it does not give the size.
- SBOA 2005-2006 report (https://www.in.gov/sboa/WebReports/B31031.pdf): Clerk-Treasurer Catherine M. Schosker 1/1/2004-12/31/2007; President of the Town Council "Geri" Oppenheim 1/1/2005-12/31/2007.
- Wikipedia: town in Clay Township, population 118 (2020), 133 (2010).

**Form of government.** The council size is not documented in anything read. Indiana lets a town set 3 to 7 members (Westport's explainer, citing IC 36-5-2-4.2; towns under 3,500 may elect at large, IC 36-5-2-4.1: https://www.in.gov/towns/westport/about/town-council/). The statute text itself was not read (justia, findlaw, counselstack, legalfix all blocked or rate-limited), so this is a secondary reading. No seat count is proposed for Indian Village.

**Not found.** Any current officeholder; any election result (the town is not in the county canvasses already in the data, including the 2026 summary); a town website; a 2019-2022 SBOA report (one search; the only 2019-2022 hit was for the Soil and Water Conservation District). The Indiana Gateway page reached through WebFetch was a generic reports landing page with no unit data.

## Open items outside the five towns

**Eli Wax (South Bend Council District 5).** The start of late 2020 is now backed by: the 2023 city proclamation as summarized in two separate search results (Republican precinct leaders elected him in Nov 2020 to fill Jake Teshka's vacated seat); Jake Teshka's Wikipedia article (council 2018-2020, assumed Indiana House office Nov 4, 2020, https://en.wikipedia.org/wiki/Jake_Teshka); and the earlier-sourced 2018 Teshka caucus (WSBT, June 2018). The proclamation itself could not be read (the docs.southbendin.gov WebLink page returns a cookie-wall error), so the exact day and the caucus vote count are unknown. Proposed: confidence low to medium, start stays 2020-11.

**Cheryl Moody and Eric Beebe (school-board party labels).** Not resolved. Moody's campaign site (https://sites.google.com/view/cheryl-moody-for-school-board) states no party; ABC57's school-board results page (https://abc57.com/news/election-results-indiana-school-boards) carries no party labels and does not list New Prairie or South Bend District 1. A search for Beebe found only New Prairie school-corporation meeting agendas that never mention him. The existing Ballotpedia reading (Moody Independent) and the single county-file reading (Beebe D) stand as they are in `data-edits-B.csv`. I could not download the county file (HTTP 403 to curl and WebFetch), so file 73081 page 8 remains unread.

## Not searched or not completed

- Roseland replacement councilmember and 2025-2026 Roseland council minutes: one targeted search, no name found.
- A direct reading of Indiana Code 36-5-2 and 3-13-9-3: not read.
- County Voter Registration pages for 2027 candidate filings, certified 2026 canvass: not read (sjcindiana.gov returns 403 to automated fetches).
- Indiana Gateway unit officials listing: the unit page was not reachable through WebFetch.
- Osceola and Walkerton before 2018: not searched (outside the five assigned towns).
- Scanned New Carlisle minutes (2023, Dec 2025, Oct 2026): image-only PDFs, no OCR tool available.
