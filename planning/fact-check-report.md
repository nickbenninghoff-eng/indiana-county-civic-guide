# Fact-check report: St. Joseph County civic guide research files

Reviewer: adversarial fact-check pass, 2026-11-07. Research files were not edited.
Method: claims checked against (a) the county's own election PDFs, read in-browser (pdf.js text layer for 2020-2026 files, tesseract OCR for scanned 2010-2019 files and the 2024 general), (b) Indiana statutes on FindLaw, in.gov pages and the SOS 2026 legislation summary PDF, (c) reputable news (Indiana Capital Chronicle, WVPE, ABC57, WNDU), and (d) cross-file comparison. **WebSearch calls used: 17 of 25.**
Verdict key: CONFIRMED / CORRECTED (claim wrong or imprecise; correct value given) / CONTRADICTED (primary source says otherwise) / CONFLICT-RESOLVED / UNVERIFIABLE (could not settle with sources checked) / REMOVE (should not be published as written). "Knowledge-only" means I checked it against established public record I'm confident of but did not fetch a source; add a citation before publishing.

---

## 1. Summary

**Verdict counts (findings table, 137 rows, by leading verdict):** CONFIRMED 56 · CORRECTED 32 · CONTRADICTED 5 · CONFLICT-RESOLVED 26 · UNVERIFIABLE 15 · REMOVE 3. Some CONFIRMED rows are marked "knowledge-only": the claim matches established record but still needs a citation.

**Election-row spot check:** 74 result rows were read straight from the county PDFs: 2026 general (doc 73081) 30 rows, 2024 general (64951) 13, 2022 general (57716) 8, 2019 general (60004) 2 plus totals, 2014 general (60012) 7, 2012 general (60015) 9, 2011 general (60017) 5. **Every one of the 74 matched the results-*.md transcriptions exactly.** I recomputed turnout percentages for 10 elections, and all were consistent. The results files are the most reliable material in the set. Several narrative files (01, 02, 04) disagree with them, and in each case the narrative file is the one that's wrong.

**Most serious problems:**
1. **04 says Indiana "eliminated straight-ticket voting in 2019."** That is false. The county's own 2026 results show 49,335 straight-ticket ballots. HEA 1377 (2026) actually *extends* straight-party voting to at-large partisan races from 2027 (school board excluded).
2. **04 says the supermajority threshold is "3/5" (60 House, 34 Senate).** The threshold that matters is two-thirds, the constitutional quorum (Art. 4 §11): 67 House, 34 Senate. 04 also cites the wrong section (§10). The "2027 House 54R-46D" figure comes from a Wikipedia infobox whose own popular-vote numbers contradict the page body. The "Senate 15D-34R" figure adds up to 49, not 50. The Capital Chronicle confirms only that the House supermajority was broken and that Democrats gained "at least four" Senate seats.
3. **01 dates Tony Hazen's caucus appointment as commissioner to "2022."** The county's 2023 ballot shows Hazen re-elected to the Mishawaka council in Nov 2023. He was chosen by GOP caucus on **Jan 20, 2024** after Deb Fleming retired effective Jan 31, 2024.
4. **01's 2024 county results are partial election-night counts.** Example: Recorder is given as 50,523 vs 48,185 (51-49). The official result is **54,038 vs 53,957**, an 81-vote race. Coroner, Surveyor, Treasurer, Commissioner D3 and Councils D/F/I are also off.
5. **01 says St. Joseph is one of "two" merit-selection counties (the other "Allen").** It is one of four: Lake, St. Joseph, Allen, Marion.
6. **09 misreads IC 36-2-3-4.** It says opted-in counties get a 4-district + 3-at-large council. The statute says opted-in 185k-300k counties get **nine single-member districts** (36-2-3-4(c); 36-2-3-2(b)). The 4+3 structure is the default for other counties.
7. **07 Niezgodski allegation.** The core facts (a 2017 Indiana Civil Rights Commission complaint, dropped in exchange for $8,000) are reported by IndyStar and WVPE (Apr 18, 2024). The file's sourcing is wrong ("Redress South Bend, Apr 12"), and its framing ("his plumbing company settled... on condition of non-disclosure") goes beyond the reporting. It must be rewritten with exact attribution or cut.
8. **07 Buttigieg/Boykins:** the "over $800,000" settlement figure is not supported. Reported settlements were **$75,000 (Boykins) + $500,000 (officers)**.
9. **2020 primary mislabeled "May 5, 2020"** in both results files. The PDF header does print May 5 (ballots were pre-printed), but the election was held **June 2, 2020** under Gov. Holcomb's March 20, 2020 executive order. Docs 37457 and 60003 are the same election, so 15-19's statement that 60003 "is not a duplicate" is wrong.
10. **02's 2019 mayoral numbers (Wikipedia: 9,437 / 5,445) differ from the official county canvass (9,406 / 5,429).** 02 also names the 2011 GOP mayoral nominee as "Norris Curry Jr." The official ballot reads **Wayne Curry**.

**Reliability rating per file:**

| File | Rating | Why |
|---|---|---|
| results-2020-2026.md | **High** | 30/30 rows in the 2026 general match, plus all spot-checks in 2022 and 2024. Issues are labeling only: the 2020 primary date, single-seat races flagged "multi-seat" in 2023, and "Retain Justice" judges labeled as if Supreme Court. |
| results-2010-2014.md | **High** | OCR spot-checks matched, and the OCR-derived values (e.g. Sanford 26,201) check out arithmetically. |
| results-2015-2019.md | **High** (data) / Medium (metadata) | 2019 data matched. The 2020 primary is misdated and the duplicate claim is wrong. |
| 08-browser-findings.md | **High** | The Mueller CFA-4 figures I could OCR match, and the arithmetic closes exactly. |
| 05-budgets.md | **Medium-High** | News figures confirmed. One quote misattributed (Mishawaka $15M). Gateway sums not independently re-pulled. |
| 02-south-bend.md | **Medium** | Mayor list faithful to Wikipedia. Its Wikipedia-sourced vote counts differ from the official canvass in 2019, and it gives the wrong 2011 nominee name. Many "not found" items are answered in the results files. |
| 03-mishawaka-townships-schools.md | **Medium** | Most "unverified" party gaps are answerable from county records (now resolved below). Few outright errors. |
| 09-gap-fill-ballotpedia-statutes.md | **Medium** | Ballotpedia tables are consistent with county docs. One significant statute misreading; HEA 1377 summary incomplete. |
| 06-campaign-finance.md | **Medium** | Bulk-CSV figures not spot-checked (would require downloading files). District "UNCONFIRMED" flags can be cleared for SD8/9/11; HD20 can be dropped. |
| 01-county.md | **Medium-Low** | 2026 data correct. The 2024 table uses partial counts. Hazen's appointment year is wrong, as are the merit-selection county count and the Circuit Court election year. |
| 07-notable-figures-and-images.md | **Medium-Low** | Most career facts hold. Problems: one wrong settlement figure, one wrong headcount, a mis-sourced allegation, an unrelated portrait (Philip Sharp), one garbled "first" (J. Chester Allen), and the naming of an uncharged student. |
| 04-state-and-elections.md | **Low-Medium** | The "from memory" items are where the errors cluster: straight-ticket, quorum section, supermajority threshold, session dates, HEA 1210. Most 2026 seat-total and percentage claims are unconfirmed or internally inconsistent. |

---

## 2. Findings table

Source shorthand: **73081** = https://www.sjcindiana.gov/DocumentCenter/View/73081 (2026 general, unofficial 11/3/2026 9:07 PM); **64951** = 2024 general official; **57716** = 2022 general official; **60004** = 2019 municipal general; **60012/60015/60017** = 2014/2012/2011 generals; **37457** = 2020 primary (all at sjcindiana.gov/DocumentCenter/View/&lt;id&gt;). **ICC-House** = https://indianacapitalchronicle.com/2026/11/03/indiana-dems-break-gop-supermajority-in-house/ ; **ICC-Comp** = https://indianacapitalchronicle.com/2026/11/04/indiana-republicans-lose-2nd-statewide-office-in-comptroller-race/ ; **ICC-Treas** = https://indianacapitalchronicle.com/2026/11/04/elliott-declares-reelection-victory-in-indiana-treasurer-race-with-comptroller-vote-tight/ ; **SOS-2026** = https://www.in.gov/sos/elections/files/2026-Indiana-Election-Legislation-Summary.FINAL.pdf

### A. 2026 results and current/incoming officeholders

| File | Claim | Verdict | Correct value / explanation | Source checked |
|---|---|---|---|---|
| 01, 20-26 | 2026 Sheriff Ruszkowski (D) 47,951 / Laureys (R) 28,674 | CONFIRMED | 62.58% / 37.42% | 73081 |
| 01, 20-26 | Prosecutor Cressy 45,438 / Maciejczyk 30,868 | CONFIRMED | 59.55 / 40.45 | 73081 |
| 01, 20-26 | Commissioner D1 Redman 16,735 / Baxmeyer 11,924 | CONFIRMED | 58.39 / 41.61; total 28,659 | 73081 |
| 01, 20-26 | Clerk Ball 43,737 / Rolfes 32,422; Auditor Kaylor 43,708 / Doyle 32,407; Assessor Cummings 42,936 / Castellon 33,280 | CONFIRMED | as transcribed | 73081 |
| 01, 20-26 | Council A Hamann 5,572 / Thomas 4,476; B Rohatgi 4,594 / Drake 3,404; C Cervelli 5,521 / O'Brien 5,145 | CONFIRMED | as transcribed | 73081 |
| 01 | "Council E and H Nov result NOT reported" | CONFLICT-RESOLVED | Both uncontested: Camp (D) 5,931; Tanner (D) 5,051 | 73081 |
| 01 | Council shifts 5-4 R → 7-2 D | CONFIRMED | Pre-election R: A, B, C (won 2022), F, I (2024); D: D, E, G, H. Democrats flip A, B, C, giving 7 D (A, B, C, D, E, G, H) to 2 R (F, I). WSBT's "one-seat shift" headline reflects an early count. | 57716, 64951, 73081 |
| 01 | Commissioners 2-1 D from Jan 2027 | CONFIRMED | Redman D1 (D), Morton D2 (D, uncontested 2024, 22,160), Hazen D3 (R) | 64951, 73081 |
| 01 | "first D majority in 20 years" (WNDU) vs "first since 2012" (WVPE) | CONFLICT-RESOLVED (partial) | County results show the board R-majority every year from Jan 2013: D1 R since 2009 (Kostielney); D3 R from the 2012 election (McClure 51.26%) onward; D2 D 2013-2020 (Dave Thomas) and R 2021-24 (Dieter). So "no Democratic majority since at least 2013" is documented. WVPE's exact wording is "their first majority since 2012." No source checked supports WNDU's "20 years." **Use WVPE's wording, or "first since at least 2013."** The 2009-2012 composition is unverified. | 60015 and results files; WVPE 2026-01-29; WNDU 2026-11-04 |
| 01, 04 | 2026 figures are unofficial | CONFIRMED | 73081 header: "Unofficial Results 11/3/2026 9:07:47 PM." Numbers equal the 95.3 MNC figures, so this appears to be the full unofficial count. Not certified as of 11/7. | 73081 |
| 01 | 2026 primary figures (Rolfes 5,829, Cook 4,190, O'Brien 1,665, Ruszkowski 9,655, Wigfall 4,937, Camp 1,115) | CORRECTED | Official 71640 (as transcribed in 20-26): Rolfes 5,836, Cook 4,193, O'Brien 1,667, Ruszkowski 9,661, Wigfall 4,938, Camp 1,116. Use the official doc. | results-2020-2026.md (71640 transcription) |
| 01 | "Commissioner D1 primary result not found" | CONFLICT-RESOLVED | Both uncontested: Baxmeyer (R) 4,137; Redman (D) 4,467 | 20-26 (71640) |
| 01 | Ruszkowski "former South Bend police chief" (search summary) | CORRECTED | **Sitting** SBPD chief (appointed 2015; joined 1988). Said he will retire as chief at end of 2026. | WVPE 2026-01-23 / WNDU 2026-05-06 (search results) |
| 04, 09 | HD5: Wait (D) 10,925 (52.5%) beat DeVon 9,901 | CONFIRMED | HD5 lies wholly in the county (county totals = district totals in 2018-2026) | 73081; Ballotpedia via 09 |
| 04, 09 | HD7 Teshka 50.6/49.4 (10,460-10,213, Wikipedia) vs 50.7/49.3 (10,394-10,102, Ballotpedia) | UNVERIFIABLE (conflict stands) | The county portion is Teshka **9,881** vs Davis **9,840** (50.10/49.90, a 41-vote lead). Since 2022, HD7 extends outside the county (2022 county 11,189 vs district 11,969), so the district totals can't be checked here. Capital Chronicle listed Teshka among GOP incumbents "too close to call" on election night. **Describe as "Teshka leading narrowly, unofficial."** | 73081; 57716; ICC-House |
| 04, 09 | HD8 Dvorak 12,953 / Harris 6,541; 04 says 66.5% | CORRECTED | 66.45% → 66.4% (09's figure is right; 04's 66.5 + 33.6 = 100.1) | 73081 |
| 04 | HD6 Bauer "general result not retrieved" | CONFLICT-RESOLVED | Uncontested, 12,411 | 73081 |
| 04, 09 | SD11 Gratzol (D) 51.4% (19,450) beat Schmutzler 18,381 | CONFIRMED (unofficial) | County portion Gratzol 14,254 (55.58%). Capital Chronicle on election night: "leaning toward another Democratic pickup." | 73081; ICC-House |
| 04 | Rogers lost May 2026 GOP primary to Schmutzler 59.2-40.8 | CONFIRMED (direction) | County portion Schmutzler 3,312 (55.75%) vs Rogers 2,629. District-wide % not checked. | 20-26 (71640) |
| 04 | House 2027: 54 R / 46 D | UNVERIFIABLE | The Wikipedia infobox says 54/46, but the same page's popular-vote overview (R 53.02%) contradicts its infobox (D 52.73%). ICC-House confirms only that the House supermajority was broken ("surpass the four-seat margin required"). | Wikipedia 2026 IN House election; ICC-House |
| 04 | "Democrats broke the GOP House supermajority for the first time since 2012" | CONFIRMED | ICC-House: "shattered the GOP's 14-year supermajority" | ICC-House |
| 04 | "the House speaker was ousted" | UNVERIFIABLE | ICC-House says only that Speaker Huston "was trailing" with 99% reporting. Don't say "ousted" without a race call. | ICC-House |
| 04 | Senate 2027: 15 D / 34 R; "R kept Senate supermajority" | CONTRADICTED (internal) | 15 + 34 = 49; the Senate has 50 seats. ICC: Democrats gained "at least four" seats (from 10). Final count unconfirmed. | ICC-House |
| 04 | SOS: Beau Bayh (D) won | CONFIRMED | ICC-Comp: "Democrat Beau Bayh's win for secretary of state." Statewide % (51.8 / 42.6) not verified. County: Bayh 60.77%. Engling is the R nominee on the ballot, consistent with Morales losing the nomination. | ICC-Comp; 73081 |
| 04 | Comptroller: Bailey 49.1% vs Nieshalla 48.0% (95% reporting) | CORRECTED | Bailey won. ICC at 95%: "50% to 47%," lead almost 45,000; Schick 3%. Nieshalla conceded. The "first Democrat since 1982" claim is unverified. | ICC-Comp |
| 04 | Auditor renamed "State Comptroller", reason not found | CONFLICT-RESOLVED | The office was renamed: "The comptroller, formerly known as the state auditor" (ICC). Nieshalla was appointed by Holcomb in 2023 after Klutz resigned. Statute number for the rename not checked. | ICC-Comp |
| 04 | Treasurer: Elliott (R) 51.0 vs Kebe 49.0 (shaky) | CONFIRMED (winner) / UNVERIFIABLE (%) | Elliott won: "three-point lead... with 91% of votes reporting." Kebe carried St. Joseph County 58.12%. | ICC-Treas; 73081 |
| 20-26 | 2026 retention rows labelled "Retention - Justice Mary DeBoer / Paul A. Felix / Justin L. McAdam / David L. Francisco / Christopher C. Fronk" (filed under State offices) | CORRECTED (label) | The PDF prints "RETAIN JUSTICE," but none of these five sits on the Indiana Supreme Court (Rush and Slaughter confirmed still serving per courts.in.gov; the full roster is knowledge-only). They are almost certainly Court of Appeals judges. **Don't call them Supreme Court justices.** No St. Joseph Superior Court retention appears on the 2026 ballot (0 "SUPERIOR" matches). | 73081; https://secure.in.gov/courts/selection/st-joseph |
| 01 | Superior Court retention for 2026 "not found" | CONFLICT-RESOLVED | None on the 2026 county ballot | 73081 |

### B. County structure, history and law (01, 09)

| File | Claim | Verdict | Correct value / explanation | Source checked |
|---|---|---|---|---|
| 01 | Council: 9 members from districts A-I; the 9-member size applies to 185k-300k counties that opt in under IC 36-2-2-4(c) | CONFIRMED | IC 36-2-3-2(b); IC 36-2-3-4(c): nine single-member districts, three nested in each commissioner district, all elected by district voters | FindLaw IC 36-2-3-2, 36-2-3-4 |
| 09 | Opted-in counties get "four single-member district seats plus three at-large" (36-2-3-4(a)) | CONTRADICTED | 36-2-3-4(a) (4 + 3) is the **default** for most counties. Opt-in counties (subsec. (c)) get **9 district seats, no at-large**. | FindLaw IC 36-2-3-4 |
| 09 | Opt-in by resolution of the executive "not later than September 1, 2023"; three single-member commissioner districts | CONFIRMED | IC 36-2-2-4(c) | FindLaw IC 36-2-2-4 |
| 01, 09 | Whether St. Joseph County opted in | UNVERIFIABLE | Practice is consistent with opting in (9 district councillors and district-only commissioners still elected in 2024 and 2026), but no resolution was found. Check the commissioners' 2023 minutes. | 64951, 73081 |
| 01 | Commissioners elected by district; St. Joseph "one of three (with Lake and Marion)" | CONFIRMED (that ABC57 says it) / UNVERIFIABLE (substance) | ABC57 does say this. But Marion County's Board of Commissioners is ex officio (auditor, treasurer, assessor) under Unigov (knowledge-only). Don't repeat the "three counties" line without a statute check. | ABC57 2026-04-22 |
| 01, 04 | April 2026 ruling that district commissioner elections violate the "free and equal elections" clause | CONFIRMED (fact of ruling) / UNVERIFIABLE (judge, court, case, appeal) | ABC57, Apr 22, 2026, names no judge or court; says the ruling "could still be appealed"; no change for the 2026 primary. The case appears to grow out of *City of South Bend (and Warren & Iris Outlaw) v. Indiana Election Commission*, filed Feb 2023 **in Marion County** (95.3 MNC, Feb 11, 2023), citing Art. 4 §§22-23 (special laws). The court is therefore probably a Marion County court, not a St. Joseph one, but the ruling court is unconfirmed. Appeal status unknown. | https://abc57.com/news/judge-rules-st-joseph-county-election-system-violates-indiana-constitution ; https://www.953mnc.com/?p=232257 |
| 01 | Hazen appointed by GOP caucus in **2022** after Fleming retired | CONTRADICTED | Fleming retired effective **Jan 31, 2024**; Hazen was the only candidate at the **Jan 20, 2024** GOP caucus and then resigned his Mishawaka council seat. He was on the Nov 2023 Mishawaka D3 ballot (uncontested, 943). Won the 2024 R primary by 46 votes (2,525 vs 2,479) and the general 58.50%. | WVPE 2024-01-12, WVPE 2023-11-22 (search results); 60569 transcription; 64951 |
| 01 | Hazen 2024: 21,163 (60%) vs Carbone 12,685 (36%), Mitchell 1,717 (5%) | CORRECTED | Official: Hazen **22,491 (58.50%)**, Carbone **14,112 (36.71%)**, Mitchell **1,842 (4.79%)** | 64951 (OCR p.4) |
| 01 | 2024 Recorder Brown 50,523 (51%) vs D 48,185 (49%) | CORRECTED | Official: Candace Brown **54,038 (50.04%)** vs **Sharon Banicki** (D) **53,957 (49.96%)**, an 81-vote margin | 64951 p.3 |
| 01 | 2024 Treasurer Wisniewski 54,571 vs Rose 53,122 | CORRECTED | **54,617 (50.68%) vs 53,161 (49.32%)** | 64951 p.3 |
| 01 | 2024 Surveyor Dieter 50,706 vs Fisher 48,577 (WVPE "171 votes") | CORRECTED | **54,375 (50.08%) vs 54,203 (49.92%)**, a margin of 172 | 64951 p.4 |
| 01 | 2024 Coroner Jordan 53,044 (54%) vs McGann 45,720 (46%) | CORRECTED | **57,006 (52.76%) vs 51,052 (47.24%)** | 64951 p.4 |
| 01 | 2024 Council D Shabazz 5,416 / Fleming 1,130; F Figg 9,343 / Wolfe 4,332; I Rutten 7,281 / Springer 4,625 | CORRECTED | Official: D 5,769 / 1,212; F 9,860 / 4,790; I 7,797 (59.75%) / 5,253 | 20-26 (64951 transcription; all 2024 races reconcile per transcriber) |
| 01 | 2024 Council G and Commissioner D2 "not found" | CONFLICT-RESOLVED | Both uncontested: Catanzarite (D) 8,730; Morton (D) 22,160 | 64951 p.4 |
| 01 | 2024 Probate: Zappia 54 / Cichowicz 46; straight-ticket R 51-48; turnout ~55% | CONFIRMED | 58,560 (54.05%) / 49,793; straight R 50.75 / D 48.17; turnout 54.53% | 64951 p.3 |
| 01 | 2022 Auditor Murphy beat Upchurch by ~663 (prelim) | CORRECTED | Official 35,572 vs 34,905, a margin of **667** | 57716 |
| 01 | 2022 Clerk Rolfes (R) beat Cleary; Council B Drake by 35; H Tanner ~1 pt | CONFIRMED | 36,732 vs 33,916; 3,672 vs 3,637; 3,386 vs 3,310 | 57716 |
| 01 | 2022 Assessor: "Ted Booker D per one line (conflicting)" | CONFLICT-RESOLVED | Ted Booker was the D nominee: 33,183 vs Castellon 37,568 | 57716 transcription |
| 01 | 2022 Council E Hess 54%, opponent "not named" | CONFLICT-RESOLVED | Jason Kring (R) 3,209 (45.86%) | 57716 transcription |
| 01 | 2022 Westerhausen won D1 D primary "with 70+%" | CORRECTED | 68.89% (1,687 vs 762) | 60001 transcription |
| 01 | Sheriff Redman 2018 "~59%" | CORRECTED | 61.47% (56,334 vs Paul Jonas 35,313) | 60006 transcription |
| 01 | Sheriff before 2019 "not found (Canarecci/Grzegorek unverified)" | CONFLICT-RESOLVED | Mike Grzegorek (D) elected 2010 (54.05% over Jim Fox) and 2014 (unopposed, 37,776) | 60012 (OCR) + 60019 transcription |
| 01 | Prosecutor Cotter defeated Sanford 2014 | CONFIRMED | Cotter 31,119 (54.29%), Sanford 26,201 (derived; OCR-partial "26,19x") | 60012 OCR p.1 |
| 01 | Prosecutor term limit "not confirmed" | CONFLICT-RESOLVED | Not term-limited. Art. 6 §2's 8-in-12 limit covers Clerk, Auditor, Recorder, Treasurer, Sheriff, Coroner only. Also shown empirically: Dvorak (2003-14) and Cotter (2015-26) each served 12 years. | search result summary of Art. 6 §2 (Justia/SBOA); results files |
| 01, 09 | Surveyor term-limited? (LOW confidence) | CONFLICT-RESOLVED | Surveyor is a constitutional office but **not** in the term-limit list | same |
| 01 | Circuit Court judge on ballot "2024" | CORRECTED | The Circuit Court judge was on the **2022** ballot (John E. Broden, uncontested, 41,815). The 2024 race was the **Probate** judge. | 57716 transcription |
| 01 | Superior Court: St. Joseph "one of two" merit-selection counties (other: Allen) | CONTRADICTED | **Four**: Lake, St. Joseph, Allen, Marion (Marion since 2017). Also, a 2021 law (HEA 1453) changed the Lake/St. Joseph commissions, so re-check 01's description of the commission against the current IC 33-33-71. | Indiana Lawyer / courts.in.gov results (search) |
| 01 | Commission sends the governor 5 nominees; 7-member commission | CONFIRMED | courts.in.gov: 7 members (3 by Governor, 3 by County Commissioners, 1 Supreme Court justice as chair); "five most highly qualified" | https://secure.in.gov/courts/selection/st-joseph |
| 01 | 8 Superior Court judges | UNVERIFIABLE | Not stated on courts.in.gov. Retention rows 2020 (2) + 2022 (1) + 2024 (5) = 8 is consistent, but that isn't proof. | results files |
| 01 | Council before Nov 2022 was 6 D - 3 R | CONFIRMED | 2018: A, B, E, H D, C R; 2020: D, G D, F, I R → 6-3 | 60006, 42820 transcriptions |
| 01, 06 | County party committees not found in the state database | CONFLICT-RESOLVED | They file locally: the county Candidate Filings page lists "St. Joseph County Democratic Central Committee" and "St. Joseph County Republican Party" | campaign-finance-county-filings.md inventory |

### C. State law and process (04, 09)

| File | Claim | Verdict | Correct value / explanation | Source checked |
|---|---|---|---|---|
| 04 | "Indiana eliminated straight-ticket voting in 2019" [L] | CONTRADICTED | Straight-ticket voting exists: 2026 county 49,335 straight-ticket votes (D 29,724, R 19,372). **HEA 1377 (2026), effective Jan 1, 2027:** a straight-party vote will apply to at-large multi-seat partisan offices (county council at-large, township board, city/town council at-large) unless the voter marks an individual candidate in that race; straight-party "do[es] not apply to school board elections." | 73081; SOS-2026 pp.3, 19 |
| 09 | HEA 1377 summary: "straight-party votes will not count for school board candidates" | CORRECTED (incomplete) | True, but the main change is the reverse: straight-party voting now *applies* to at-large partisan races from 2027. 09's "SB 61 (2016) removed straight-party for at-large races" (via NCSL) is not checked but is consistent with this reversal. | SOS-2026 |
| 04 | Quorum is "Art. 4 sec. 10: two-thirds" [L] | CORRECTED | Two-thirds is right; the section is **Art. 4 §11** ("Two-thirds of each House shall constitute a quorum to do business") | in.gov Historical Bureau, Constitution of 1851 Art. 4 |
| 04 | Supermajority "3/5... >=60 House / >=34 Senate?" | CORRECTED | The relevant supermajority is two-thirds, the quorum-proof threshold: **67 of 100 House, 34 of 50 Senate**. ICC-House frames it the same way ("two-thirds GOP hold"). | Art. 4 §11; ICC-House |
| 04 | Long session adjourns by April 30; short session by March 15 | CORRECTED | Statute IC 2-2.1-1-2: long (odd-year) session adjourns sine die **not later than April 29**, short session **not later than March 14** (Justia/FindLaw search summaries). The 61/30-day limits not re-checked. | search results for IC 2-2.1-1-2 |
| 04 | Veto override by simple majority of each chamber | CONFIRMED | Art. 5 §14: majority of all members elected to each house (1851 text; still the rule, knowledge-only for the current text) | in.gov Historical Bureau Art. 5 |
| 04 | Governor 4-yr term, max 8 of 12 years | CONFIRMED (knowledge-only for the current text) | Original 1851 text was 4 of 8; the 1972 amendment gives 8 of 12 | in.gov Historical Bureau Art. 5 |
| 04, 09 | Property tax caps 1% / 2% / 3%; constitutional since 2010 | CONFIRMED (statute) / UNVERIFIABLE (constitution text) | IC 6-1.1-20.6-7.5 caps per 09's Justia read. Voters approved the 2010 constitutional amendment (knowledge-only); the Justia Art. 10 §1 text 09 saw was stale. Cite Art. 10 §1(a)/(b) from iga.in.gov before publishing. | 09 (Justia), not re-fetched |
| 04, 05 | HB 1210 (2026): 04 says "expands disabled veteran relief"; 05 says it delays SEA 1 LIT changes to 2029 | CONFLICT-RESOLVED | 05 is right. Signed **Mar 12, 2026**; delays the 2028 LIT overhaul to **2029**; allows county-municipal "Municipal Unit Strategic Taskforce"; orders a study committee. It is PL 157-2026, the DLGF omnibus. 04's veteran claim is unverified (could be one section of the omnibus); drop it or source it. | ICC 2026-03-23; SOS-2026 p.2 |
| 04 | SEA 1: "from 2028 max LIT 2.9%, municipal LIT" | CORRECTED (stale) | Now **2029** (HB 1210). Cap 2.9% (down from 3.75%); cities and larger towns up to 1.2% within the county total. 05's "cities of 3,500+" is not confirmed. | ICC 2026-03-23 |
| 03, 04 | SEA 287 (2025) partisan school board: signed by Braun May 6, 2025; effective July 1, 2025; party, independent or nonpartisan options; no primary | CONFIRMED | Final Senate vote 26-24; House stripped the primary requirement | Ballotpedia News / Chalkbeat (search results) |
| 04 | Superintendent → appointed Secretary of Education; Jenner first, Jan 11, 2021; "bill number not confirmed" | CONFIRMED | HEA 1005-2017 created the post (originally effective 2025); HEA 1005-2019 (P.L. 8-2019) moved it to 2021 | IBJ / WFYI / Ballotpedia (search results) |
| 04 | Governors since 1945 and start years "from memory" | CONFIRMED (knowledge-only) | All 16 start years match the standard record (Gates 1945 … Braun 2025). Note Schricker also served 1941-45. Cite the W-Govs page. | knowledge |
| 04 | 2020 county governor results Myers 48,610 / Holcomb 60,696 / Rainwater 5,387 | CONFIRMED | matches county doc 42820 transcription | 20-26 |
| 04 | 2012 county governor Gregg 59,410 (54.25) / Pence 47,208 (43.11) | CORRECTED | County doc: Gregg **59,411**, Pence **47,182 (43.08%)** | 60015 OCR p.1 |
| 04 | 2016 county governor Gregg 57,835 / Holcomb 48,839 | CONFIRMED | matches 60008 transcription | 15-19 |
| 04 | Photo ID required at polls; no statewide citizen initiative | CONFIRMED (knowledge-only) | Well established (photo-ID law upheld in *Crawford*, 2008; Indiana has no initiative or referendum process). **Add citations** (SOS photo-ID page; Ballotpedia "Initiative and referendum in Indiana"). | knowledge |
| 04 | DLGF budget-approval role | UNVERIFIABLE | Not checked | — |
| 04, 09 | Caucus vacancy procedure (IC 3-13-5 legislative; IC 3-13-11 local) | CONFIRMED (practice) | Consistent with documented caucuses (Hazen Jan 2024; Beidinger May 2026; Dawn Jones 2019). Statute text not re-read. | WVPE (search); 02 sources |
| 02, 09 | South Bend and Mishawaka are second-class cities | CONFIRMED (by statute band) | IC 36-4-1-1 per 09's Justia read. The 6 district + 3 at-large councils match second-class structure (IC 36-4-6-3). Note: 09 reads the threshold as 34,000; I didn't re-read it. | 09; FindLaw 36-4-6-3 (02) |

### D. Election-results files: metadata and cross-file conflicts

| File | Claim | Verdict | Correct value / explanation | Source checked |
|---|---|---|---|---|
| 20-26, 15-19 | 2020 primary "May 5, 2020" (docs 37457 and 60003) | CORRECTED | The PDF header prints "PRIMARY ELECTION TUESDAY, MAY 5, 2020" (ballots dated May 5 were declared valid), but the election was held **June 2, 2020** under Holcomb's Mar 20, 2020 executive order. Official canvass dated 6/12/2020. Label it "June 2, 2020 (rescheduled from May 5)." | 37457 p.1; IPR/WFYI/ABC57 Mar 20, 2020 (search) |
| 15-19 | 60003 "is not a duplicate of any file in this batch" | CORRECTED | It duplicates 37457 (identical registered 191,025, ballots 37,445, party split, run date 6/12/2020). Use one. Minor transcription difference: Teshka 2,650 (37457 text layer) vs 2,651 (60003 OCR); prefer the text layer. | 37457; both files |
| 20-26 | 2023 general and primary: single-seat district races flagged "multi-seat" with no winner (SB D2, D3, D5; Mishawaka D1, D2, D4 etc.) | CORRECTED (labeling) | These are single-seat races; flag winners (e.g. Bolden-Simpson 1,414 over Wax 1,376; Carroll 591 over Bellovich 538; Voelker 434 over Treely 418) | 20-26 internal |
| 02 | 2019 SB mayor Mueller 9,437 (63.41) / Haas 5,445 (36.58), total 14,882 (Wikipedia) | CORRECTED | Official canvass: **9,406 (63.40%) / 5,429 (36.60%)**, total **14,835** | 60004 OCR p.1 |
| 02 | 2011 GOP mayoral nominee "Norris Curry Jr." (Wikipedia) | CORRECTED | Ballot name: **Wayne Curry** (REP) 2,884 (19.38%). Buttigieg 10,991 (73.85%) and Farrell 1,008 (6.77%) confirmed. Possibly the same person under a full legal name, but publish the ballot name. | 60017 OCR p.1 |
| 02 | 2011, 2015 mayoral and primary rows (Buttigieg 8,515 / Jones 2,074; 2015 D primary 8,369 / 2,405; 2011 D primary) | CONFIRMED | match county docs | 60017; 15-19 (60010, 60011); 10-14 (60018) |
| 02 | 2023 mayor Mueller 7,877 / Upchurch 2,938 (WNDU) | CORRECTED (minor) | Official 7,878 / 2,939 (72.83 / 27.17). Clerk Tirado 7,323 (not 7,322). | 20-26 (60569) |
| 02 | 2023 D5 Bolden-Simpson won by 37 votes | CORRECTED | Official 1,414 vs 1,376 = **38** | 20-26 (60569) |
| 02 | 2023 Districts 1, 4, 6 "not found" | CONFLICT-RESOLVED | Uncontested: Lee 1,603; Warner 1,938; Niezgodski 743 | 20-26 (60569) |
| 02 | 2019 Warner "at-large" label (snippet) | CONFLICT-RESOLVED | **District 4**: Warner 2,257 (68.00%) vs Gillean 1,062. Teshka D5 2,056 (57.75%) vs Combs 1,504. 02's 953mnc figures (2,262 / 2,061 / 1,508) are unofficial. | 60004 transcription |
| 02 | Wikipedia lists Beidinger as "elected 2019" in D4 | CONFLICT-RESOLVED | Wrong. Warner won D4 in 2019 and in 2023 (uncontested). Beidinger ran for HD5 in 2022 and 2024 (lost to DeVon) and was chosen by caucus for D4 on May 20, 2026. | 60004; 57716; 64951 |
| 02 | Council composition after 2019 "not found" | CONFLICT-RESOLVED | 8 D - 1 R (only D5 Teshka R). Eli Wax (R) later held D5. 9-0 D after 2023. | 60004; 60569 transcriptions |
| 02 | County turnout 2019 (SOS) 110,108 / 24,139 / 22% vs Wikipedia 15% | CONFLICT-RESOLVED | The county municipal canvass is 106,860 / 20,816 / **19.48%**. Wikipedia's 15% matches the **2019 primary** turnout (15.05%). SOS 2015 figures (116,309 / 15,937) match the county doc. | 60004, 60005, 60010 transcriptions |
| 02 | SB mayor list (33 mayors, years, parties) | CONFIRMED (as faithful to Wikipedia) / UNVERIFIABLE (vs city) | All 33 rows match the current Wikipedia table exactly. That page itself has "TBA" placeholders and the noted internal inconsistencies (Miller, Longley, Fogarty). The odd "Jan 3" take-office dates for Kernan and Luecke conflict with the normal noon-Jan-1 start, and Luecke's start depends on Kernan's Lt. Gov. swearing-in. No city source checked. | https://en.wikipedia.org/wiki/List_of_mayors_of_South_Bend,_Indiana |
| 02 | Last Republican mayor elected 1967 (Allen) | CONFIRMED | Consistent with Wikipedia table (all Democrats since 1972) | same |
| 04, 09 | HD5 2018-2024 and HD7 2018-2020 Ballotpedia numbers | CONFIRMED | Equal to county canvass (whole-district-in-county years): e.g. 2018 HD5 11,713 / 11,240; 2018 HD7 11,267 / 10,540; 2020 HD7 14,668 / 12,498 | 60006, 42820, 57716, 64951 transcriptions |
| 04, 06, 07 | Which legislative districts include St. Joseph County ("UNCONFIRMED") | CONFLICT-RESOLVED | County ballots 2020-2026 include SD 8, 9, 10, 11 and HD 5, 6, 7, 8, 21, so Bohacek, Mishler, Rogers/Gratzol, Wesco all represent part of the county. **HD 20 (Pressel) and HD 9 (Novak) never appear: drop them.** | results-2020-2026.md |
| 20-26 | Turnout % rows (10 elections) | CONFIRMED | Recomputed ballots/registered for 2010-2026; all match to 0.01 | results files |

### E. South Bend, Mishawaka, townships, schools (02, 03)

| File | Claim | Verdict | Correct value / explanation | Source checked |
|---|---|---|---|---|
| 03 | Mishawaka D3 Lou Ann Hazen: party unverified | CONFLICT-RESOLVED | **Republican.** Tony Hazen (R) won D3 in Nov 2023 (uncontested, 943) and resigned in Jan 2024 on becoming commissioner. A seat vacated by a Republican is filled by an R caucus (IC 3-13-11). Lou Ann Hazen is described as "fellow Republican" (WVPE Jan 2024) and was the 2023 R clerk nominee. Caucus result itself not found; the city roster lists her. | 60569 transcription; WVPE 2024-01-12 (search) |
| 03 | D5 Violi, D6 Banicki: party not found | CONFLICT-RESOLVED | Both **D** (uncontested 2023: Violi 607, Banicki 286) | 20-26 (60569) |
| 03 | Mishawaka council 7-2 D after 2023; 5-4 before | CONFIRMED | 2023: D = D1, D2, D5, D6 + 3 AL; R = D3, D4. 2019: D = 2 AL, D1, D5, D6; R = 1 AL (DeMaegd), D2, D3, D4. Also: **2015 produced 7-2 D** (worth adding). | 60004, 60010, 60569 transcriptions |
| 03 | 2023 primary snippet labels Mammolenti, Hixenbaugh, Hahn "R" | CONFLICT-RESOLVED | All three ran in the **Democratic** primary (816 / 809 / 788) | 20-26 (59108) |
| 03 | Bob Kovach: one term vs "retired end of 2012" | CONFLICT-RESOLVED | Mayor **1980-1983**, one term (won 1979 over Prickett; did not seek re-election). The 2012 claim is wrong for the mayoralty. He was also a state senator (1974-78) and county commissioner. | WSBT/Tribune obits (search results) |
| 03, 07 | Beutter 1984-2003 vs 2004 (ABC57: 1982) | CONFLICT-RESOLVED | **1984-2003** (five terms; city statement). ABC57's 1982 is impossible given Kovach served through 1983. Rea took office 2004. Party still unconfirmed. | WNDU/WSBT/ABC57 (search results) |
| 03 | Wood ran unopposed 2023; "fourth full term" | CONFIRMED | 2023 uncontested 3,806; elected 2011, 2015, 2019, 2023 | 20-26; 15-19; 10-14 |
| 03 | Mishawaka 2023 D2: source printed 42%, computed 52 | CONFIRMED (computed) | Carroll 591 (52.35%) | 20-26 |
| 03 | "No Nov 2026 results found for townships/schools" | CONFLICT-RESOLVED | Full 2026 township and school-board results are in results-2020-2026.md (e.g. Centre trustee Ron Baker (D) 52.68% over incumbent Galloway; Penn trustee Nancy Duncan (D) over Portolese; Harris Veronica Vos (D) over Lindsay) | 73081 transcription |
| 02 | Common Council veto override = 6 votes | CONFIRMED (knowledge-only) | Two-thirds of 9 = 6 (IC 36-4-6-16) | knowledge |
| 03 | SBCSC 7 seats (5 district + 2 at-large) | CONFIRMED (consistent) | District and at-large rows appear on the 2020, 2022, 2024 and 2026 ballots | results files |

### F. Budgets (05)

| File | Claim | Verdict | Correct value / explanation | Source checked |
|---|---|---|---|---|
| 05 | SB budget 2024 ~$417M; 2025 "more than $424M"; Police >$60M; Fire just under $49M; Transpo $14M | CONFIRMED | ABC57, Oct 15, 2024 | https://www.abc57.com/news/the-south-bend-common-council-approves-2025-budget |
| 05 | County 2026: WNDU "just over $90 million"; auditor "$97 million general fund = 39% of total"; "+$1,400, 1%" | CONFIRMED (quotes) / UNVERIFIABLE (interpretation) | Quotes are exact (WNDU, Sep 9, 2025). WNDU calls $90M the "total balanced budget" and $97M the "general fund," the reverse of 05's reading. 05's mapping ($90M = Gateway General fund $90.7M; $97M/0.39 ≈ $249M ≈ Gateway all-funds $248.2M) is plausible arithmetic, but a $97M general fund doesn't match Gateway's $90.7M. **Present both news figures as quoted, with Gateway as the documented number.** | https://www.wndu.com/2025/09/10/st-joseph-county-council-discusses-2026-budget-public-hearing |
| 05 | Mishawaka: "Mayor Dave Wood: about $15M, about 20% of the general fund, by 2028" | CORRECTED | The $15M / 20% / 2028 figures are the **reporter's**, not Wood's ("Mishawaka is one of those cities expected to face about a 20 percent, or $15 million, budget cut by 2028"). Wood said only that most cities "seem to be impacted in the 20 percent range." The article doesn't say "general fund"; 20% of the $49.6M general fund would be ~$10M, so "% of general fund" conflicts with 05's own table. | https://www.abc57.com/news/local-leaders-discuss-sea-1-impacts-and-possible-solutions (Nov 18, 2025) |
| 05 | South Bend Gateway $427M (2023) → ~$166-171M (2024-26) is a series break | CONFIRMED (logic) | Consistent with the news all-funds $417M / $424M. Gateway data not re-pulled. | ABC57 above |
| 05 | HB 1210 signed 2026-03-12, delays LIT changes to 2029, orders study | CONFIRMED | see C | ICC 2026-03-23 |
| 05 | Gateway tables (county, cities, townships, schools, libraries), AFR breakdowns, debt figures | UNVERIFIABLE (not re-pulled) | Not spot-checked: it would require re-downloading the Gateway bulk files. The internal caveats are appropriate. | — |

### G. Campaign finance (06, 08)

| File | Claim | Verdict | Correct value / explanation | Source checked |
|---|---|---|---|---|
| 08 | Mueller 2023 Annual CFA-4: COH Jan 1 $262,508.60; itemized receipts YTD $383,787.90; total receipts $393,342.90; expenditures $610,625.36; COH end $45,226.14 | CONFIRMED | OCR read: committee "Mueller for South Bend," acronym "Mueller for Mayor," Democrat, $262,508.60 and $383,787.90. The other cells didn't OCR, but the arithmetic closes exactly (262,508.60 + 393,342.90 − 610,625.36 = 45,226.14). Note: the report period printed is **10/14/2023-12/31/2023** (Column A); the YTD figures are Column B. Doc is a JPEG, not a PDF. | https://www.sjcindiana.gov/DocumentCenter/View/60871 |
| 06 | State bulk-CSV committee totals (Niezgodski, Teshka, DeVon, Dvorak, Bauer, Wesco) | UNVERIFIABLE (not checked) | Not spot-checked: requires downloading zipped CSVs. Teshka's large 2020/2022 receipts and HRCC as top funder are plausible for a targeted seat. | — |
| 06 | Local candidates are not in the state database | CONFIRMED (consistent) | The county posts local CFA-4s on its Candidate Filings page | 08; county filings inventory |
| 06 | Mishawaka clerk: Hazen >$50,000; Ladyga-Block $30,352 | UNVERIFIABLE | Search summary only. The county has 2023 filings for Lou Ann Hazen (doc 60859) that could settle it. | — |

### H. Notable figures (07)

| File | Claim | Verdict | Correct value / explanation | Source checked |
|---|---|---|---|---|
| 07 | Niezgodski: "Redress South Bend reported Apr 12, 2024 sexual harassment allegations dating to 2017; his plumbing company settled with a former employee for $8,000 on condition of non-disclosure (per Wikipedia)" | CORRECTED (keep only if rewritten; defamation-sensitive) | Reputable reporting (IndyStar, WVPE **Apr 18, 2024**): a former office assistant at his plumbing business filed an **Indiana Civil Rights Commission complaint in 2017** and **dropped it in exchange for $8,000**. Niezgodski's statement expressed regret, took "full responsibility" for any pain or discomfort, called it a personnel matter resolved "mutually and confidentially," and did not admit harassment. No charges or findings. He won the 2024 D primary over Tim Swager. The "Redress South Bend Apr 12" sourcing is unverified. **If published, attribute to WVPE/IndyStar, use "alleged," include his response, and omit the details of the alleged conduct.** | https://www.wvpe.org/wvpe-news/2024-04-18/sen-david-niezgodski-paid-former-employee-to-drop-sexual-harassment-claims-report-finds |
| 07 | Buttigieg/Boykins: "city settled related suits for over $800,000" | CORRECTED | Boykins **$75,000** ($50k + $25k fees); officers **$500,000** combined, about $575,000 total in settlements. Also new: a federal judge ruled in May 2026 that the recordings were illegal and ordered them destroyed; the Common Council filed an appeal (June 2026). | WOWO/Tribune, ABC57, CNN, WVPE 2026-05-28 / 06-24 (search results) |
| 07 | Bauer led a "36-member" walkout Feb 2011; ended Mar 28; fines "up to $3,500" | CORRECTED | **37** Democrats (Ballotpedia). Fines rose from $250 to $350 a day, roughly $3,000-3,500 each in total. Mar 28 return confirmed. | Ballotpedia / IBJ / ABC57 (search results) |
| 07 | Bauer Speaker "2003-05 and 2007-11" | UNVERIFIABLE (likely off by a year) | By knowledge: Speaker 2002-2004 and 2007-2010 (Republicans took the House in Nov 2010). Verify. | knowledge |
| 07 | Lizzy Seeberg / Prince Shembo detail under Michael Dvorak | REMOVE (the student's name) | Shembo was never charged. Naming an uncharged private individual in a civic guide adds defamation risk and no civic value. If the prosecutorial decision stays, describe it without his name. | editorial |
| 07 | J. Chester Allen "first person elected to serve on the South Bend Common Council" | REMOVE (as written) | Self-evidently garbled (the council dates from 1865). Other "firsts" (state rep 1938?, school board, bar president) are single-snippet. Re-source before use. | — |
| 07 | Philip Sharp portrait | REMOVE | Muncie-area congressman with no documented St. Joseph County link | 07 itself |
| 07 | Kernan, Colfax, Brademas, Hiler, Roemer, Donnelly, Walorski, Luecke offices and dates | CONFIRMED (knowledge-only) | Dates and offices match the standard record. Brademas's "first Greek-American member of Congress" and the post-office naming not checked. | knowledge |
| 07 | Mueller: b. 1982; PhD oceanography (Delaware); Buttigieg chief of staff; took office Jan 1, 2020; 63.4% / 72.8% | CONFIRMED | Wikipedia (b. June 29, 1982; Notre Dame BA 2004; PhD oceanography, Univ. of Delaware) | https://en.wikipedia.org/wiki/James_Mueller_(mayor) |
| 07 | Ryan Dvorak lost 2011 D mayoral primary | CONFIRMED | 2,041 (14.62%), third | 60018 transcription |
| 07 | Craig Fry HD5 1988-2012, succeeded by DeVon | CONFIRMED (partial) | 2010 re-election confirmed (70.93%); DeVon won the 2012 open seat. Missing context: Fry was the 2011 D nominee for Mishawaka mayor (lost to Wood 23.68%). | 10-14 (60019, 60017) |
| 07 | Mishler SD9 since 2004, unopposed 2024 | CONFIRMED | 2024 unopposed (county 14,026; Ballotpedia 42,276) | 64951 |
| 07 | Prickett elected 1963, lost 1979 to Kovach | CONFIRMED | Tribune via search | search results |
| 07 | Margaret Prickett "first woman mayor" of Mishawaka | UNVERIFIABLE | 03 marks it [H]/[M]; 07 says unconfirmed. Not checked. | — |
| 07 | Wood "21st mayor"; Rea start year/party | UNVERIFIABLE | Single WNDU source | — |
| 07 | Pfeifer first name (Beverly vs Charlotte); Braboy "first" | UNVERIFIABLE | Not checked. Use the city resolution doc's wording. | — |
| 07 | Sherry Bolden-Simpson "first Democrat elected to D5 since 1962" | UNVERIFIABLE | Self-described on the city page. Consistent with R wins in D5 in 2011, 2015 and 2019. | results files |
| 07 | Michael Dvorak 2013 special-prosecutor request (petition fraud) | UNVERIFIABLE (not checked) | single ABC57 snippet | — |

---

## 3. Must-fix before publishing

1. **Straight-ticket voting (04):** delete "eliminated in 2019." Replace with: Indiana has straight-party voting. From 2016 it did not apply to multi-seat at-large races; HEA 1377 (2026, effective Jan 1, 2027) makes it apply to at-large partisan races again (unless the voter marks individual candidates in that race) and keeps it inapplicable to school board races.
2. **Supermajority and quorum (04):** the threshold is two-thirds (67/34), from the quorum rule in Art. 4 §11. Don't publish 54-46 or 15-34 until the certified results are out. Say "Democrats broke the House GOP supermajority (first time since the 2012 election) and gained at least four Senate seats (unofficial)." Drop "speaker ousted" unless a race call is found.
3. **Session deadlines (04):** April 29 / March 14, not April 30 / March 15.
4. **Hazen appointment (01):** Jan 20, 2024, not 2022. Fix the commissioner timeline (Fleming served Nov 2014-Jan 31, 2024). Hazen was re-elected to the Mishawaka council in Nov 2023 before switching offices, so Lou Ann Hazen (R) holds Mishawaka D3.
5. **2024 county results (01):** replace all ABC57 election-night numbers with the official canvass (doc 64951). This matters most for Recorder (81-vote margin) and Surveyor (172).
6. **Merit selection (01):** four counties, not two. Re-check the commission's composition after the 2021 changes.
7. **Council structure (09):** strike "4 district + 3 at-large" for opt-in counties. The opt-in structure is 9 single-member districts.
8. **Niezgodski (07):** rewrite per the table, attributed to WVPE/IndyStar Apr 18, 2024, with his response; otherwise cut. **Remove Prince Shembo's name.** **Remove the J. Chester Allen "first" as written** and **the Philip Sharp image.**
9. **Boykins settlements (07):** $75,000 + $500,000, not "over $800,000."
10. **2020 primary date (both results files):** June 2, 2020. Dedupe 37457 and 60003.
11. **South Bend 2019 and 2011 mayoral (02):** use the official canvass (9,406 / 5,429; total 14,835) and the ballot name Wayne Curry.
12. **"Retain Justice" rows (20-26):** don't present DeBoer, Felix, McAdam, Francisco or Fronk as Supreme Court justices.
13. **"First D commissioner majority in 20 years":** don't use it. Use "first since 2012" (WVPE) or "first since at least 2013" (documented).
14. **Mishawaka SEA 1 quote (05):** attribute "$15M / ~20% by 2028" to ABC57's reporting, not to Mayor Wood, and drop "of the general fund."
15. **Comptroller (04):** Bailey won ("50% to 47%" at 95%), not 49.1/48.0. Treasurer: Elliott won.
16. **Drop HD20 (Pressel) and HD9 (Novak)** from the county delegation (04, 06). Keep SD8, SD9, SD11 as confirmed.
17. **April 2026 ruling (01/04):** say "a judge ruled" (ABC57, Apr 22, 2026). Don't name a court. Note the underlying suit was filed in Marion County in Feb 2023 by the City of South Bend; appeal status unknown.

---

## 4. Systematic issues

- **Election-night news numbers used instead of the canvass (01, 02, 03).** 01's 2024 figures, its 2022 auditor margin, and its 2026 primary figures, plus 02's 2019/2023 SB figures, are all early or partial counts. The results-*.md files from the county canvass should be the single source for vote counts, and narrative files should cite them rather than news.
- **"From memory" legal claims in 04 are the least reliable content.** Four of the six [L] items I checked were wrong or mis-cited (straight-ticket, quorum section, supermajority fraction, session dates). The two that held (veto override, photo ID / no initiative) still need citations.
- **Wikipedia as a vote source (02, 04).** Its figures sometimes diverge from the official canvass (2012 governor, 2019 mayor, 2011 nominee name), and the 2026 pages are internally inconsistent. Treat Wikipedia as secondary only.
- **Gaps that other files already answer.** Many "not found" items in 01, 02, 03 and 06 are answered in the results files: council E/H, D2 2024, Assessor 2022 opponent, Mishawaka party labels, 2019 council, township 2026 results, which legislative districts are in the county. A reconciliation pass before drafting would remove most of them.
- **Results-file labeling.** Both 2020-primary transcriptions inherit the ballot's pre-printed "May 5" date. 2023 single-seat races are flagged "multi-seat." The 2026 judicial retention rows are filed as "State" offices under "Justice."
- **Statute reading (09).** 09 confused the default subsection of IC 36-2-3-4 with the opt-in subsection. Statute summaries need a second reader.
- **OCR quality (10-14, 15-19).** The OCR files are good: every OCR value I re-read matched, and the "(?)" derivations I tested (e.g. Sanford 26,201) are arithmetically correct. No digit-swap pattern found in the rows checked.

---

## 5. Not checked

- 10-demographics-economy.md and the cf\ folder (still being written; files modified within the last few minutes). campaign-finance-county-filings.md was used only for its document inventory.
- 06 state bulk-CSV committee totals: not re-pulled (would require downloading zipped CSVs).
- 05 Gateway-derived tables (county/city/township/school/library budgets, tax rates, AFR breakdowns, debt): not re-pulled. Only the news-cited figures were checked.
- Statewide 2026 percentages (SOS 51.8/42.6; Treasurer 51.0/49.0) and the "first Democrat comptroller since 1982" claim.
- Commissioner board composition 2009-2012 (decides "since 2012" vs anything earlier).
- Whether St. Joseph County formally opted in under IC 36-2-2-4(c) by Sept 1, 2023.
- Judge, court and appeal status of the April 2026 ruling.
- Number of Superior Court judges; the current IC 33-33-71 commission text.
- Art. 10 §1 cap text on iga.in.gov; DLGF statutory role; IC 3-11-8-25.1 photo-ID text; the 61/30-day session limits.
- 07: Brademas "first Greek-American" and post-office naming; Luecke's council district; J. Chester Allen; Braboy/Pfeifer; Prickett "first woman"; Wood "21st mayor"; Dvorak 2013 special prosecutor; Colfax III "youngest"; image license data (Commons) not re-checked.
- 03: school board 2022/2024 news figures; library/airport/health board rosters; township trustees list (partly superseded by 2026 results).
- 02: Beidinger caucus details (May 20, 2026), Redevelopment Commission composition, Luecke's 1997 selection mechanism, clerk history.
- 04: House/Senate composition history 2009-2025 (matches my knowledge, not fetched); A2 seat history before 2012 (DeVon 2008, Baxmeyer 2002 opponents); IN-2 2026 result (county portion: Decio (D) 59.35% vs Yakym 38.69%; district result not checked).
- Precinct-level data (out of scope).

Searches: 17 WebSearch calls used of 25 (no cap reached).
