# Fact-check findings applied: community, people, images, timeline

Source of findings: `planning/fact-check-report.md` (2026-11-07). IDs: PPL-034 / COM-030 in the sources files.

## People and images (research/07)

| Finding | Action |
|---|---|
| REMOVE: Prince Shembo's name (Lizzy Seeberg case under Michael Dvorak) | Not encoded anywhere. The 2010 charging decision is omitted entirely (the fact-check allowed describing it without the name; omitted because it adds no encoded criterion). Validator fails the build if either name appears in people.csv. |
| REMOVE: J. Chester Allen "first person elected to serve on the South Bend Common Council" | Claim dropped. The remaining "firsts" (first African American to represent South Bend in state government, first Black school-board appointee, first bar-association president) are single-article claims; kept as FIRST with `confidence=low`, `status=single_source`, and flagged for re-sourcing. |
| REMOVE: Philip Sharp portrait | Not downloaded, not in images.csv. |
| CORRECTED: Boykins settlement "over $800,000" | Encoded as $75,000 (Boykins) + $500,000 (officers, combined) in Buttigieg's `documented_findings`, attributed to the city as defendant; sources ABC57, WOWO, The Indiana Lawyer. Added the May 28, 2026 federal ruling (WVPE) and the reported Council appeal (WNDU 2026-06-02). The fact-check text says the Council filed an appeal; WNDU's June 2 report says it was considering one; both noted. |
| CORRECTED (defamation-sensitive): Niezgodski allegation | Not an official finding (no court ruling, censure, or agency finding; a complaint dropped in exchange for $8,000). Left out of `documented_findings`. Recorded in `notes` only, attributed to WVPE citing IndyStar (2024-04-18), with his response and with the details of the alleged conduct omitted. The unverified "Redress South Bend, Apr 12" sourcing and the "non-disclosure" framing are not used. |
| CORRECTED: Bauer walkout "36-member", fines "up to $3,500" | Encoded as 37 Democrats; fines rose from $250 to $350 a day (timeline). The Mar 28, 2011 return is kept. |
| UNVERIFIABLE: Bauer Speaker "2003-05 and 2007-11" | Offices summary says "two periods, dates differ across sources"; note carries the fact-check's alternative (2002-04, 2007-10). |
| CONFIRMED (knowledge-only): Kernan, Colfax, Brademas, Hiler, Roemer, Donnelly, Walorski, Luecke offices and dates; governor start years "from memory" | Encoded at confidence medium/high with a note to cite an official source before publication (Kernan row). Brademas "first Greek-American member of Congress" was not checked, so it is not encoded as FIRST. |
| UNVERIFIABLE: Margaret Prickett "first woman mayor" | Not encoded; TENURE only, confidence low. |
| UNVERIFIABLE: Wood "21st mayor"; Rea start year/party | "21st mayor" kept in the summary as a single-source description; Rea excluded (no criterion met). |
| UNVERIFIABLE: Pfeifer first name; Braboy "first" | Kept as FIRST, confidence low; name field states the conflict. |
| UNVERIFIABLE: Bolden-Simpson "first Democrat elected to D5 since 1962" | Encoded as the city page's self-description; margin corrected to 38 votes (official canvass). |
| UNVERIFIABLE: Dvorak 2013 special prosecutor | Omitted. |
| CONFIRMED (partial): Craig Fry HD5 1988-2012 | Added the fact-check's context that he was the 2011 Democratic nominee for Mishawaka mayor (lost to Wood). |
| CONFLICT-RESOLVED: Beutter 1984-2003 | Encoded as 1984-2003 (city statement); ABC57's 1982 not used. Prickett's loss and Kovach's term (1980-83, one term) consistent with this. |
| CONFIRMED: Ruszkowski is the sitting SBPD chief | Not applicable (no person row created). |
| Image license data (Commons) "not re-checked" | Re-checked against the Commons API on 2026-11-07 for every file; all matched research/07 (the three files whose license was not recorded were looked up and recorded). |
| REMOVE/DROP: HD20 (Pressel), HD9 (Novak) | Not in people. |

## Timeline and community (research/01, 02, 10)

| Finding | Action |
|---|---|
| 01: Hazen appointed in 2022 (CONTRADICTED) | Timeline uses Jan 20, 2024 caucus; Fleming's retirement effective Jan 31, 2024; Hazen official 2024 result 22,491 (58.50%). |
| 01: first Democratic commissioner majority "in 20 years" (WNDU) | Not used. Timeline cites WVPE's "first majority since 2012" and the documented "Republican majority each year from 2013"; 2009-2012 composition flagged unverified. |
| 01: 2024 county row-office numbers from election night | Timeline uses official canvass: Recorder 54,038 to 53,957 (81 votes), Surveyor 54,375 to 54,203 (172). |
| 01/04: April 2026 ruling | Worded as "a judge ruled" (ABC57, 2026-04-22); no court named; appeal status unknown; Marion County suit noted as filed Feb 2023, link unconfirmed. |
| 01: Council 6-3 D before Nov 2022 (CONFIRMED); 7-2 D from 2027 | Used in timeline. WNDU's "first Republican majority" labelled as unverified. |
| 02: 2019 mayoral numbers (9,437 / 5,445) | Timeline uses the official canvass 9,406 / 5,429 (63.40%). |
| 02: 2023 D5 won by 37 votes | Corrected to 38 (1,414 to 1,376). |
| 02: 2011 GOP nominee "Norris Curry Jr." | Not used (ballot name is Wayne Curry); no row depends on it. |
| 02: Beidinger "elected 2019" | Not used. |
| 02: Kernan 53%-47% over Carl Baxmeyer, 1987 (Wikipedia) | Kept as a Wikipedia-sourced timeline item (vote counts in the 1987 row are Wikipedia's, not canvass). |
| 10: figures labelled unconfirmed (UAW first sit-down strike, Newsweek date, AWS construction status, Dec 2025 cancelled campus) | Kept at confidence low or medium and attributed; the single-listing Dec 2025 cancellation claim is not encoded. |
| 10: ACFR 2024 unemployment "2.7%" inconsistent with BLS | Not used; BLS LAUS 4.7% for 2024 is encoded. |

## Applied rules (not from the fact-check)

- HIGHER is applied to anyone documented in a statewide or federal office (elected or appointed), regardless of earlier path.
- TENURE counts cumulative years in elected seats within the same governmental unit (county, city, or the General Assembly). It needs 16+ documented years.
- TURNING_POINT is applied only where the event appears in the sourced turning-point lists in research 01/02/10 (not to every notable election).
- Excluded because no criterion is met by the sources: James Mueller (current mayor), John Hiler, Bob Kovach, Alexis Coquillard, Jeff Rea, Frank Bruggner, Edward Voorde. See `gaps_community_people.csv`.

## 2026-11-08: gap-fill C1 (people)

Source: `planning/qa/gapfill-2026-11-08-C1-people.md` and `-edits.csv`. Log: `planning/qa/gapfill-2026-11-08-applied.md`.

- Applied: gaps_community_people "Boykins/police-recordings appeal". It is a state case: Judge Jamie Woods ruled May 28, 2026, and the council filed notice of appeal (WVPE 2026-06-24, new source PPL-044). how_to_fill now points to the Court of Appeals docket.
- Applied: PPL-025 (Prickett). "First woman mayor" is now quoted from the City of Mishawaka timeline (GOV-039), and that clause was removed from the Braboy/Prickett gap row.
- Notes-only: PPL-016 (B. Patrick Bauer). "First elected in 1964" comes from Wikipedia only, and the "Burnett" spelling from a snippet only.
- Notes-only: PPL-017. The start date conflict (Nov 4 vs Nov 16, 2020, both from Wikipedia) is recorded, not resolved.
