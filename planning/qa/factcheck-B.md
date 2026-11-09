# Fact-check, QA agent B

**Scope:** elections/* (elections.py), state/* (state.py), history/, history/people/, community/* (community_history.py).
**Checked:** 2026-11-08 against `site/st-joseph/` and the edition data.
**Build check:** `build.py --edition st-joseph --check` PASSES after the module edits.
**Data edits:** proposed in `planning/qa/data-edits-B.csv` (137 rows). No data files were edited.
**WebSearch:** 7 of the 25-call budget used. Other checks used direct fetches of known URLs, plus Ballotpedia via curl.

Severity: **BLOCKER** means wrong in a way that misleads a reader. **FIX** means a clear error or unevenness to correct. **NOTE** means minor, or a disclosure.

## Findings

| # | Page | Claim as shown | Problem | Severity | Evidence | Action taken |
|---|------|----------------|---------|----------|----------|--------------|
| 1 | elections/index, elections/landscape | Office holder counts and "Up next" list both the sitting member and the 2026 winner as current holders (for example, Gratzol shown with a current SD11 term) | Unofficial incoming terms were counted as second current holders | BLOCKER | `ed.current_terms` returns the unofficial 2026-11 rows alongside the sitting member | Fixed in module: `_holders_now()` prefers settled terms (157 holders) |
| 2 | elections/turnout | 2024 primary: 201,540 registered, 23,843 ballots, 11.83%, unofficial | No certified county canvass exists. The state's post-election report differs: 201,542 / 23,810 / 11.81% | FIX | Indiana Election Division 2024 Primary Turnout and Registration Report (Feb 7, 2025). The county page returns 403; its Wayback snapshot (2025-05-17) lists no 2024 primary summary | Data edit proposed (turnout to the state report and official; candidate rows stay unofficial) |
| 3 | state/your-legislators; offices data | Senate District 10: "only part of the district lies in St. Joseph County" | Wrong. SD10 lies wholly in the county | BLOCKER | IC 2-1-15-10 (2021 plan) lists only St. Joseph townships. County totals equal Ballotpedia's in 2012, 2016, 2020 and 2024 | Fixed in module (computed whole-district wording, hard-coded SD10 gap removed). Data edit proposed for the office note |
| 4 | state/your-legislators | Hero: "Every district crosses the county line" / HD7-only low-confidence note | Not true of HD5, HD6, SD10 or HD8 since 2022. The low-confidence treatment covered HD7 only, not HD21 or SD11 | FIX | Ballotpedia district totals vs county canvass (research/09) | Fixed in module: new hero text, plus a uniform `cross-county-2026` table (HD7, HD21, SD11) with the same columns. Per-district office notes proposed |
| 5 | elections/margins | Legislative races excluded as "not wholly in the county" | Whole-district contests were dropped too | FIX | Results rows noted "district lies wholly in the county" | Fixed in module: `classify()` keeps them (331 to 342 races); text reworded |
| 6 | elections/results | 2018/2020 HD5 and 2016/2018 HD7 shown as "county tally only" | County totals equal the district totals, so these are whole-district results | FIX | Ballotpedia HD5 and HD7 pages | Data edit proposed (notes/winner). 2014/2016 HD5/HD6 and 2026 HD6 (unopposed) proposed as map-level inference, for the main session to decide |
| 7 | state/your-legislators | 2026 card: "won", plus term start shown as January | Unofficial results; Indiana terms begin the day after the general election | FIX | Ind. Const. Art. 4 §3; Ballotpedia lists the Nov 4, 2026 start | Fixed in module: "Leads (unofficial)" / "Trails (unofficial)", and term-start sentence added |
| 8 | state/your-legislators | Cross-county 2026 rows: district-wide count only for Gratzol | Uneven: Teshka (HD7) and Wesco (HD21) district-wide counts are missing | FIX | Ballotpedia: Teshka 10,394 to 10,102; Wesco 7,486 to 5,302 | Data edit proposed (terms notes; Teshka confidence low to medium). The table fills in automatically |
| 9 | elections/results, elections/candidates | 2026 school-board candidates all "NP" | SEA 287 allows labels. Ballotpedia lists Hawkins (D), McClements (I), Moody (I), Sullivan (R), Riley (R), Smoker (R). The county file reads Beebe (D) | FIX | Ballotpedia SBCSC and PHM 2026 pages; research/11 | Data edit proposed. Moody conflict flagged (county file reading shows no label) |
| 10 | elections/results, state/your-legislators | Candidates listed in ballot order with no explanation | N4: the reason for the order is not stated | NOTE | IC 3-11-2-6 (IND-056); RES-023: 2022 Secretary of State county vote Wells (D) 34,746, Morales (R) 33,748 | Fixed in module: one sentence with `IND-056;RES-023` on both pages |
| 11 | elections/results | Straight-party periods labelled "X to now" | "To now" was wrong for the period ending in 2026. Order was not chronological | FIX | election_rules data | Fixed in module: "From X on", chronological order. N5 note added for the years with printed totals |
| 12 | elections/judges-and-questions | Superior Court judges: next retention blank | Five can be derived. Three are unresolved | FIX | Retention results 2012–2024. IC 33-33-71-43 (6-year terms, retention at the general election before expiry) | Data edit proposed: Manier, Sanford, Steele, Telloyan, Woods = 2030. Chapleau and Marnocha (due 2026) and Reagan (due 2024) are not on the canvass; left blank with a note |
| 13 | elections/calendar | Town next_election blank (New Carlisle, North Liberty, Roseland, Lakeville) | Not derivable: the towns elect in both even and odd years and have no seat counts | NOTE | results.csv history | Left as gap |
| 14 | state/index | Statewide table: Comptroller "No holder" | Office-name mismatch with "(Auditor of State)" | FIX | statewide_terms vs statewide_offices | Fixed in module (`_office_key`). Data hygiene edit proposed |
| 15 | state/index | Empty "Elected 2026" cells | No explanation of why they are empty | NOTE | term notes | Fixed in module: "Not elected (appointed)" / "Not on the 2026 ballot" / "No 2026 winner in the guide's data" |
| 16 | state/index, state/how-the-state-shapes-local | Sentence fragments such as "4 sec. 10; the quorum rule…" and "the statute text differs." | The sentence splitter broke on abbreviations. Some data sentences describe the research process | FIX | page text | Fixed in module (`ABBREV_END`). Data edit proposed to remove research-process sentences |
| 17 | state/how-the-state-shapes-local | SEA 1 raised the business personal property exemption "from $80,000 to $2 million" | Step not shown: $1M for the 2025 assessment date, $2M from 2026 (HEA 1427) | FIX | Indiana CPA Society SEA 1 hub | Data edit proposed |
| 18 | state/how-the-state-shapes-local | SEA 1 effects: only local officials' revenue-loss claims | One-sided (F7): the homeowner relief isn't stated | FIX | ABC57 $1.3B relief (IND-046); Capital Chronicle $1.4B lost revenue (IND-024, IND-033) | Fixed in module (both figures, attributed; caption reworded). Rule-text edits proposed (sea1_overview, school_levy_sharing) |
| 19 | state/how-the-state-shapes-local | SEA 270 = P.L. 134-2026, effective Mar 5, 2026; HEA 1210 = P.L. 157-2026 | Confirmed | NOTE | SOS 2026 Election Legislation Summary | No action |
| 20 | state/how-the-state-shapes-local | HEA 1210 "Effective: Mar 12, 2026" | That is the signing date (Capital Chronicle). The SOS gives Jul 1, 2027 for the notice sections; the date for the LIT-delay sections was not confirmed | NOTE | SOS summary | Data note proposed |
| 21 | state/how-the-state-shapes-local | Local income tax: the 1.2% municipal share disappeared | The page drops sentences mentioning "research", which removed the fact | FIX | state_local_rules local_income_tax detail | Data edit proposed (reworded detail) |
| 22 | history/people | Colfax card: "Other party (O)" | A literal backspace character in the `_parties` regex | FIX | module source | Fixed in module: "Whig (O); Republican (R)" |
| 23 | history/people | Criteria assigned by hand; HIGHER applied unevenly (Brademas TENURE-only; Hiler excluded) | B1/B2: one definition, computed | BLOCKER | people/terms/timeline data | Fixed in module: `people_pool()` computes TENURE, HIGHER and TURNING_POINT for everyone in people.csv and terms.csv. Brademas is now HIGHER. Hiler row proposed (data edit) |
| 24 | history/people | Long-tenure holders missing (Wesco, Zakas) | B3: uneven coverage | FIX | Wesco 2010–2026 in terms.csv; Zakas SD11 1982–2018 (Wikipedia) | Fixed in module: Wesco now picked up from terms. Zakas and Kovach (SD11) terms rows proposed. Gap added for pre-2010 legislators |
| 25 | history/people | TURNING_POINT applied by hand | B4: uneven | FIX | timeline titles | Fixed in module: computed from political, government and legal titles, published as table §4. Kernan and Luecke gain it; Bauer and Bolden-Simpson lose it; Mueller, Baxmeyer, Hazen and Voorde (low) gain it |
| 26 | history/people | Party split of selected people not shown by office status | B5 | NOTE | computed | Fixed in module: `people-in-office` table. In office: D 7 / R 6. Not in office: D 11 / R 7 / not documented 5. Pool: D 18 / R 13 / 5 |
| 27 | history/people | Cards with vote counts and shares (Buttigieg, Allen, Yakym, Dvorak and others) | B6: uneven, and results belong on the results pages | FIX | people.csv summaries | Fixed in module: `_card_summary` drops result sentences. Summary rewrites proposed (12 people) |
| 28 | history/people | Accomplishment and naming lines on some cards (Brademas, Luecke, Buttigieg, Beutter, Walorski) | F2: uneven praise-type content | FIX | people.csv | Data edits proposed (summaries) |
| 29 | history/people | Buttigieg "start of a new era" (New America) | F1: characterization | FIX | people.csv, timeline 2012-01-01 | Data edits proposed |
| 30 | history/people | Buttigieg documented_findings: police-recordings litigation | F3: the litigation names the City, not him | FIX | COM-033 | Data edit proposed (clear; the timeline keeps the event and names the mayor, N10) |
| 31 | history/people | Prickett party blank or "presumed" | Item 4: Republican, sourced | FIX | South Bend Tribune (Colwell, 2022-11-21): "defeating Republican Maggie Prickett" | Data edit proposed. The page already shows R via terms |
| 32 | history/people | Beutter party | Not stated in any source found | NOTE | WSBT (GOV-041), Tribune | Left as gap (reason in the note) |
| 33 | history/people | J. Chester Allen "firsts" (low, single source) | Item 6: the legislature "first" now has a second source; the others don't | FIX | IHB blog (2020-12-31): "voters elected J. Chester (D) the first African American to represent St. Joseph County"; IHB marker: elected 1938 and 1940 | Data edit proposed (party D, offices, summary, confidence medium; school-board and bar firsts dropped) |
| 34 | history/people | Donnelly offices: "Mishawaka Marian School Board" | N9: a private school board is not a public office | FIX | PPL-008 | Data edit proposed (moved to the summary) |
| 35 | history/people | Bolden-Simpson "first" wording | N3: the city's own claim, not independently verified | NOTE | city council page | Data edit proposed (attributed wording) |
| 36 | history/people | Skew callout and gaps rows with hand counts ("No Republican in 1980–1999", "Excluded because no criterion…") | Stale after the computed pool; one row excused leaving out Hiler | FIX | gaps_community_people | Fixed in module (rows filtered; counts computed). Data edit proposed to delete the rows |
| 37 | history/index §3 | 2021–22 redistricting entries: party labels on plans, "search listing only", "hundreds of thousands" in fees | B8: not neutral or sequential. The cost is not in the source. COM-023 is the wrong article | BLOCKER | WVPE 2021-11-16, 2021-12-30 (COM-022), 2022-03-01 | Data edit proposed: new 2021-11-16 row, rewrite of 2021-12-30, 2022 row replaced with 2022-03-01 and the correct source |
| 38 | history/index | Mishawaka mayor changes absent; South Bend's are present | F4: uneven | FIX | Tribune; GOV-041; mishawaka-mayor terms | Data edit proposed: 1979, 1983 and 2010 rows |
| 39 | history/index, community/income-and-work | UAW ratification status "official" | F8: union press release | FIX | COM-011 | Data edit proposed (single_source) |
| 40 | history/index | 2011 walkout: aim stated as fact, outcome missing | N2 | NOTE | IndyStar 2012-02-01 (Daniels signs right-to-work) | Data edit proposed |
| 41 | history/index | 2012 legal row: "the mayor" | N10: officeholder not named | NOTE | existing sources | Data edit proposed |
| 42 | history/index | 2026-04-22 ruling linked by inference to the city's suit | F14: unsupported link | FIX | ABC57 2023-05-22 (city's suit added county defendants; no court named) | Data edit proposed (both facts attributed separately) |
| 43 | history/index §01 | Control method computed separately from the county page | Inconsistency risk | NOTE | pages.county | Fixed in module: imports `CONTROL_METHOD` / `control_by_year` |
| 44 | community/research-on-voting | WISH note: guide's shares "differ" | Wrong: governor shares match the canvass after rounding (McCormick 49.76%, Braun 47.18%) | FIX | RES-027 canvass, recomputed | Fixed in module. Gap row and finding_summary edits proposed (F10, F11) |
| 45 | community/research-on-voting | Inclusion rule | Loose wording | NOTE | page text | Fixed in module (method described; publisher type stated) |
| 46 | community/* | Population change (1960 and 2020: -22%, +14%), income and poverty figures | Recomputed in Python; all match | NOTE | indicator_values | No action |
| 47 | elections/*, state/index | Governors list and General Assembly seat counts | Checked; correct | NOTE | statewide_terms, offices | No action |
| 48 | history/index | N1 merge of the walkout and RTW rows | Merging would drop Lloyd Allen (R) from TURNING_POINT under the computed rule | NOTE | computed tp_map | Not proposed; main session to decide |

**Counts:** BLOCKER 4 · FIX 29 · NOTE 15.

**Selection-rule wording for About §3 (agent C / main session should match it exactly):**
- **Tenure:** Held elected seats in one government (St. Joseph County, one city, or the Indiana General Assembly) for 16 or more years in total. Years are counted as the last year minus the first year of each documented term, with overlapping terms counted once; a term still running counts to 2026.
- **First:** Is documented, with a source, as the first person to hold an office or the first of a group to hold it.
- **Higher office:** Held a statewide Indiana office or a federal office, elected or appointed, as documented in the sources.
- **Family:** Two or more members of the same family held elected office here, as documented in the sources.
- **Turning point:** Is named in the title of a political, government or legal event in the guide's sourced timeline of turning points (History, section 3).
- Tenure, Higher office and Turning point are computed by the build. First and Family are taken from the sources as recorded.

Test cases: Hiler is HIGHER once his row is added. Brademas is HIGHER, and not TENURE because the U.S. House is not counted. Roemer is HIGHER. Colfax is HIGHER.

## Could NOT check

- The 2024 primary certified county canvass: sjcindiana.gov returns 403. Candidate rows stay unofficial.
- Enrolled bill text on iga.in.gov (script-only app): SEA 1 BPP schedule, LIT 2.9% cap, councils ending Jul 1, 2027, HEA 1210 effective dates. Secondary sources only.
- DLGF levy-control rules and the homestead credit beyond the "10% or $300" consistency check.
- Unemployment benchmark values on community/income-and-work.
- Full read of elections/calendar, elections/judges-and-questions (beyond retention years) and most of history/index prose.
- Courts of the 2026 RETAIN JUSTICE / judge rows.
- Katie Jenner's current status (Secretary of Education).
- Beutter's and Rea's party.
- Whether Chapleau, Marnocha and Reagan still serve.
- Town election years and seat counts.
- N6 ("Left office" field: needs a new data column) and F12 (full General Assembly gap-fill before 2010). Out of scope for module edits.
- Moody (SBCSC D1) label: Ballotpedia and the research reading of county file 73081 conflict. 73081 was not re-read.
