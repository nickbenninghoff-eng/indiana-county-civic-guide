# Gap-fill 2026-11-08: what was applied

Applied by a subagent on 2026-11-08, from the six gap-fill reports in `planning/qa/gapfill-2026-11-08-*.md`, in the order F, C1, C2, A, B, D. Nothing is committed. Per-row reasons are in the dated sections of:
- `data/editions/st-joseph/_corrections_applied_results.md` (F, and the results edits from C1 and A)
- `_corrections_applied_gov.md` (C1, C2, A units, B)
- `_corrections_applied_community_people.md` (C1 people)
- `_corrections_applied_money.md` (D)
- `data/indiana/_corrections_applied_indiana.md` (A rules)

All CSVs were edited with Python csv, keeping each file's line endings and column order. `tools/res_main.py` and `tools/build_money.py` were not run. Both regenerate their files from raw data, so a rebuild would drop these hand edits (`build_money.py` writes budgets, tax_rates, sources_money and gaps_money).

## Counts per report

| Report | Edit rows | Applied | Adapted | Notes-only | Skipped / not applied | Verification failed |
|---|---|---|---|---|---|---|
| F canvass | 104 | 99 | 5 | 0 | 0 | 0 |
| C1 people and judges | 46 | 16 | 7 | 21 | 2 | 0 |
| C2 towns and schools | 47 | 18 | 4 | 10 | 15 | 0 |
| A election rules | 41 | 26 | 3 | 2 | 10 | 0 |
| B services and boards | 56 | 27 | 9 | 17 | 3 | 0 |
| D money | 215 | 128 | 0 | 2 | 85 (main session) | 0 |

"Adapted" means the fact was applied in a different form from the proposal. Examples: a judge successor became a term on the existing office instead of a new office; an exact day the source does not give became year-only; a proposed new row was merged into an existing one.

D's 128 applied rows are: 93 tax rates; 4 proposed sources plus the DLGF memo; 1 budgets note; 30 gap rows. The SBCSC-scope gap row was also narrowed, though it had no edit row of its own.

D's 85 "not applied" rows are all for the main session:
- 37 net_assessed_value rows
- 42 indicator_values rows
- 2 budgets rows and 1 debt row (instructed not to add)
- 3 sources that no applied row cites

New source ids:
- GOV-144 to GOV-170
- PPL-044
- RES-045 and RES-046
- SVC-023 to SVC-031
- IND-065 to IND-077
- MON-033 to MON-037 (MON-060 and up belong to the other agent; its rows MON-060 to MON-068 are intact)

## Verifications done

### Required items (rule 3)

| Item | Result | Source |
|---|---|---|
| Robles death and Monterrosa appointment | Confirmed: died 2017-09-25; appointed Tuesday 2017-10-24 | ABC57 same-day reports (GOV-152, GOV-153) |
| Reagan retirement 2021-05-31 | Confirmed, but by one source only: "who retired May 31". 95.3 MNC and ND Law pages checked did not mention it. | The Indiana Lawyer ?p=169179 (GOV-145) |
| Brisco appointment and 2024 departure | Confirmed: named June 3, 2021; Superior Court 2021-2024; federal commission 2024-01-26 | The Indiana Lawyer; FJC biographical directory (GOV-146) |
| Fronk 2024 appointment | Confirmed: appointed June 28, 2024 to Superior Court 1; swearing-in "to be determined" | South Bend Tribune via AOL, 2024-08-06 (GOV-147) |
| Francisco 2024 appointment | Confirmed: announced Jan 16, 2024 to succeed Marnocha (planned retirement Jan 31) | NWI Business (GOV-148); Judicial Branch 2023-11-15 (GOV-149) |
| Results vote changes over 50 or winner flips | Confirmed from the printed pages. Dvorak 14,772 (60006 p.1); Harris Price 4,002 (60006 p.2); New Prairie 2024 Yacullo 677 / Smith 1,177 (64951 p.5); probate total 108,353 (64951 p.3); Lakeville 2015 Hathaway 63 / Iovino 44 and the new Law and Tyler rows (60010 p.3) | County canvass PDFs, rendered in a browser or read from disk |
| Hurley office | Two sources: county staff directory (Superior 8) and Wikipedia | GOV-144, GOV-151 |
| North Liberty next_election 2030 (rule 7) | Every North Liberty council race in results.csv is in an even year (2010, 2014, 2022, 2026) | results.csv |

### Other checks I ran

- **County staff directory (re-read 2026-11-08):** eight Superior judges, including "Mark P. Telloyan - Superior 7", "Stephanie E. Steele-Superior 4", Jamie Woods (Superior 6), Fronk (Superior 1), Francisco (Superior 2) and Hurley (Superior 8).
- **The Indiana Lawyer ?p=173242:** Chapleau "retired in July" 2021; Woods to Superior 6.
- **Indiana Judicial Branch 2026/0827:** DeBoer, Felix, Kenworthy and McAdam on the 2026 retention ballot.
- **City of Mishawaka timeline (?p=204):** Fisher first mayor in 1899; Prickett "first woman mayor".
- **WVPE 2026-06-24:** Woods ruling of May 28, 2026, and the council's appeal.
- **PHM ?p=4377:** Dec 1, 2021 appointments.
- **PHM board terms page:** 3 Penn seats.
- **PHM Oct 10 and Nov 9, 2025 posts:** Chaffee's resignation effective Oct 8; Smoker sworn in Nov 8.
- **ABC57 2019-09-16:** Ball chosen 4-2.
- **SBOA 78484A:** Williams-Inez to 09-28-24; Rulli from 09-29-24.
- **South Bend Tribune 2022-07-06 (via Yahoo):** Weber succeeds Roberts; hybrid board.
- **Justia, 2025 Indiana Code, read in a browser:** IC 3-11-10-26; 3-10-1-4.5; 36-4-1-1; 3-8-6-3 and -10; 3-8-1-1, -21, -22 and -26 to -29 and -34; 3-11-18.1-13; 3-9-5-6, -7 and -10; 3-8-2.5-4; 3-11-2-10 (P.L.21-2016); 3-8-2-4.
- **Election Division PDFs:**
  - 2026 election calendar: Feb 5, 2027; Jan 20, 2027; Nov 2, 2027; CAN-44.
  - CAN-34 2026 revision: May 19 to June 18; 10 signatures.
  - 2010 legislative summary: Public Question #1 text.
- **Ballot Access News ?p=50389:** SB 61 signed March 21, 2016.
- **SBOA 85115A:** Housing Authority of South Bend, seven commissioners appointed by the mayor.
- **City of Mishawaka 2025 appointing-authority disclosure, read in a browser:** seat counts and appointers only. The PDF also lists members' home addresses, which were NOT collected.
- **Mishawaka department pages:** Central Services, Utilities, Building, Parks, Planning and Report a Problem. Phones 258-1660, -1630, -1607, -1664, -1625, -1678 and -1649.
- **Other B pages:**
  - Area Plan Commission pages 2142 and 2157.
  - Transpo board page.
  - SJCPL library board page.
  - Humane Society animal control page.
  - INDOT4U.
  - Township pages for Greene, Liberty, Olive, Harris, Centre, Penn and German.
- **D: tax rates.** All 93 rates for 2022-2024 re-derived from the DLGF xlsx files: 31 of 31 match for each year.
- **D: DLGF 2026 budget order** (downloaded): p.37 SBCSC funds, total $246,289,187. AV values: county p.5, South Bend p.21, Mishawaka p.23. Liberty territory $2,155,968 (p.12). Union emergency fire loan $391,965 (p.18). Olive-New Carlisle-Hudson territory (p.43).
- **D: Gateway psv spot checks:** Portage 2025 territory $6,083,530, equipment $225,000 and debt $1,106,433; Union 2026 debt $391,965; Centre 2019 $1,727,690 and $308,487.
- **D: DLGF memo "Legislation Affecting Local Income Taxes":** section 133 text; ordinances expire 2029-01-01; signed March 12, 2026.
- **D: WVPE 2025-11-04:** "$257 million spending plan".
- **D: Mishawaka 2026 budget (wpdmdl=13302):** in a browser on mishawaka.in.gov it opened as a 77-page PDF WITH a text layer. The D agent called it image-only, which is wrong; the revenue lines were not extracted.

### Not verified by me

- **2016 Shail and Zeiger (60008) and 2015 primary Tom Price and totals (60011):** taken from the F agent's printed-page reads. The rows say "re-read 2026-11-08", meaning that agent's read.
- **Leads kept as notes only, not as facts:**
  - Steele, Telloyan and Woods appointment dates
  - Kromkowski
  - Mishawaka redevelopment commission and animal control commission
  - South Bend redevelopment meeting times
  - Party pages and police numbers
  - The MPHPL library page (it timed out on re-check)
- **D's SEA 1 SBCSC estimates (ABC57) and the LSA HB 1210 county figures:** not re-opened; written as reported.
- **WebSearch count:** not tracked exactly across the session. Most checks were direct page or PDF reads, not searches.

## Checks (final run, after all six reports)

- `python -P -E tools/check_gov.py`: errors=0, warnings=23 (baseline 19).
  - The net 4 extra warnings are 5 new blank-start warnings, on terms whose start was deliberately left blank (Fronk, Francisco, Hurley, Brisco and Roberts), minus the Monterrosa blank-start warning, which is now resolved.
  - The unreferenced-source warnings are the same set as the baseline.
- `python -P -E tools/check_results.py`: the same 8 pre-existing errors (unknown sources ELX-008, GOV-044 x6 and IND-031); 0 warnings.
- `python -P -E tools/site/build.py --edition st-joseph --check`: PASSED (60 pages).
- `tools/validate_indiana_csv.py`: only the pre-existing COM-025 x2.
- `tools/check_money.py` (known stale; not fixed): FAILED with 611 errors, against a baseline of 518 on the HEAD money files. All 93 extra errors are "bad rate_kind" for certified_district_rate. The checker only knows the three old kinds and already flags the existing 2025 and 2026 certified rows.

## Needs Nick's judgment

1. **2012 general:** should the elections.csv 2012g row be official? Its figures are all on page 1, which is stamped OFFICIAL. Pages 2-4 are stamped UNOFFICIAL, so their rows stay unofficial. HD7 Niezgodski is still from_scan.
2. **2026 Francisco and Fronk retention rows:** still labelled and keyed as "state" contests, though both are St. Joseph Superior judges. Rename to county contests once the certified canvass is out?
3. **2010 Chamblee and 2016 Hostetler/Hurley retentions:** probably county Superior Court contests, but currently "state" ids. Same decision as item 2.
4. **Hurley:** start date and retention years are unsourced. 2016 and 2022 are inferred, which would make next_election 2028; it is left blank for now.
5. **Reagan's retirement date (2021-05-31):** rests on one source (The Indiana Lawyer). Status is secondary.
6. **PHM Galloway:** end "2021" is low confidence. All we know is the seat was vacant by Dec 1, 2021.
7. **Housing Authority of South Bend board size:** 7 (SBOA-reviewed audit, 2024) or 6 (2023 news)? Both are recorded; the data uses 7.
8. **Mishawaka-Penn-Harris Public Library board meeting day:** 3rd Thursday (library page, per the gap-fill agent) or 2nd Thursday (city disclosure)? Both are recorded.
9. **Mishawaka Plan Commission:** 2 of 9 seats have no appointer tagged in the city disclosure.
10. **office_types.csv** has no eligibility column, so the A eligibility rows went into election_rules.csv instead. Add a column? Precinct committeeperson term_years was not set, because the statute gives election years, not a term.
11. **Ross Deal (HD7 2018-2020) lead:** conflicts with terms.csv (Joe Taylor III 2016-2020). Unverified; noted in gaps_gov.
12. **Greene Township contact:** the in.gov township directory gives only a "(Trustee)" phone and no street address. It is an official listing, but could be a personal line. Check that it is OK to publish.
13. **D, for the main session:**
    - net_assessed_value.csv (37 rows): needs a schema decision, and which AV counts as "the" unit AV.
    - 42 indicator_values rows (enrollment, per-student): need indicator ids, plus a check of the IDOE school-year labels.
    - Rows deliberately not added: South Bend 2026 $429,975,283 budget; Redevelopment Commission amended 2026 $135,109,942; debt $298,686,137.
    - check_money.py needs certified_unit_rate, certified_district_unit_rate and certified_district_rate added to its rate_kind list.
14. **Rebuild risk:** build_money.py and res_main.py would overwrite these hand edits if re-run. The builders, or their raw inputs, need the same changes before any rebuild.
