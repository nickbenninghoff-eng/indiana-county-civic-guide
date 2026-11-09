# Gap fill D (money), 2026-11-08

Collect-and-report only. No existing data, code or docs were edited. Proposed changes are in `planning/qa/gapfill-2026-11-08-D-money-edits.csv` (215 rows). WebSearch used: 13 of 25. New source ids are written as NEW-S2 ... NEW-S8 (rows for `sources_money.csv` are in the edits file); the main session should assign real MON ids.

Method notes that matter for review:
- The DLGF/IDOE/SBOA files were read as text with pdftotext or an xlsx parser in a scratch folder, not through a browser download. PDF table layouts interleave columns, so each number below says how it was checked.
- `sources/money/gateway_budget_county71_2012-2026.psv` holds every fund row 5 times. Any sum from it must deduplicate first (item 7 does).

## Status summary

| # | Gap | Status |
|---|-----|--------|
| 1 | South Bend 2026 all-funds budget | Partly: $429,975,283 from the Sept 2026 deck; adopting ordinance not found |
| 2 | Net assessed valuation by unit | Filled for 2026 (37 rows); other years not searched |
| 3 | Combined tax-district rates | Filled 2022-2024 (93 rows); 2012-2021 not available on the DLGF page |
| 4 | Enrollment and per-student spending | Mostly filled; enrollment year label unconfirmed |
| 5 | SBCSC 2026 scope | Partly: certified fund list explains $246.29M; board $213.25M scope not stated; third figure $257M |
| 6 | HB 1210 and SEA 1 dollars | HB 1210 filled; SEA 1 only for SBCSC; South Bend and county not found |
| 7 | Unexplained jumps (23 gap rows) | 7 explained with documents or exact fund matches, 9 by fund names only, 6 not explained, 1 reframed (South Bend 2021-22) |
| 8 | RDC, jail, Mishawaka revenue | RDC partly; jail not found; Mishawaka blocked |

## 1. South Bend 2026 all-funds budget

Finding: the "2027 Budget Overview - Council Hearing #1" deck (MON-030, docs.southbendin.gov DocView id 413308, filed 2026-09-02) has an expenditure table by department with a "2026 Budget" column. Extracted Grand Total row: 2023 Actuals 370,910,948; 2024 Actuals 377,435,094; 2025 Actuals 415,691,418; 2026 Budget 429,975,283; 2027 Proposed 433,757,721 (YOY 0.88%). 433,757,721 / 429,975,283 = 1.0088, which ties the 2026 cell. The same deck's revenue table gives 2026 Budget Grand Total 423,223,905 and 2027 Proposed 422,271,665 (-0.2%). The deck notes it excludes the Redevelopment Commission.

Water and sewage: the deck's 2027 proposed total (433.76M) is the figure the guide already records as including utilities, and ordinance 11317-26 (439.06M) includes funds 620/622/625 and 641/642/649. The 2026 column is on the same table, so it is very likely the same basis, but the deck does not label it.

Caveats: (a) it is the 2026 budget as shown in September 2026, so it may include additional appropriations and transfers after the Oct 2025 adoption (the council passed quarterly additional-appropriation and transfer bills in 2026); (b) the text of the table has stray cells, so confirm visually. Confidence: medium.

Not found: the 2026 adopting ordinance. The Legislation > Ordinances folder (Browse id 88) lists years with paging that did not render in the browser tool, and a name search page (Search.aspx) returned only the empty form. The 2026 budget materials folder is `Browse.aspx?id=395495` (subfolders: Meeting Notices, Minutes, Presentations, Public Input, Recordings); the Hearing #2 deck (edoc 399088) had only bond information in text.

Related, March 2026 Monthly Financial Report (edoc 407521): Expenditure Summary "Current Amended Budget" Grand Total $728,470,209 (includes Redevelopment Commission $135,109,942). This is an amended, encumbrance-heavy basis and is not comparable to the $429.98M.

## 2. Net assessed valuation 2026 (DLGF budget order, MON-026)

Source: https://www.in.gov/dlgf/files/2026-reports/2026-budget-orders/St-Joseph-260114-2026-Budget-Order.pdf, read 2026-11-08, "Certified AV" column of each unit's fund table. County $14,611,493,562 matches the figure already in the gap row. AV differs by fund within a unit (fire territory and debt funds use other bases). The 37 proposed rows use the AV repeated across each unit's general/operating funds; alternates are in the notes. Examples: South Bend civil city $4,396,041,441; Mishawaka civil city $2,126,759,474; Penn Twp $3,316,256,356; Portage Twp $3,260,758,257; Clay Twp $2,274,712,395; SBCSC operations $7,720,180,896; PHM $4,328,152,992; SJCPL $8,499,391,190. School and township units straddling county lines show the St. Joseph County part only. No `net_assessed_value.csv` exists, so the rows are for a proposed new file. Confidence: high (values), medium (which AV is "the" unit AV).

## 3. Combined tax-district rates

tax_rates.csv already has 2025 and 2026 (31 districts each). New: 2022, 2023, 2024, 31 districts each.
- DLGF Reports page https://www.in.gov/dlgf/reports-and-data/reports/ lists statewide files for 2022-2026 only: `2022_Certifed_Tax_Rates_by_District.xlsx` (/dA/e466483808), `2023_..._v2.xlsx` (/dA/9a6e15eab9), `2024_..._by_District.xlsx` (/dA/3e602b68cb), plus unit-level `2024_..._by_District_Unit.xlsx` (/dA/c4487b05bf). 2022 and 2023 files give "Certified Gross Tax Rate (per $100 AV)" per district; the 2024 file is by unit and fund, so the district rate is the sum over county 71 rows.
- Validation: summing the 2025 unit file reproduces all 31 existing 2025 district rates exactly. 2024 district sums from the two 2024 files are identical.
- Example (South Bend - Centre, district 002): 2022 5.8259; 2023 5.2513; 2024 5.3227; 2025 4.9608 (existing); 2026 4.8274 (existing).
- 2012-2021: not on that page; the county budget orders for those years are the likely source (not searched). Per-unit-in-district rates exist for 2024 only (can be generated).

## 4. Enrollment and spending per student

Enrollment: IDOE `corporation-enrollment-grade-2006-26.xlsx` (https://www.in.gov/doe/files/corporation-enrollment-grade-2006-26.xlsx), column TOTAL ENROLLMENT, one sheet per year. Totals by sheet label:

| Corporation | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|
| South Bend Community | 15,965 | 15,444 | 14,484 | 13,580 | 12,851 |
| Penn-Harris-Madison | 11,513 | 11,360 | 11,538 | 11,329 | 11,185 |
| School City of Mishawaka | 5,274 | 5,128 | 5,034 | 5,063 | 5,036 |
| John Glenn | 2,003 | 2,012 | 1,999 | 1,993 | 1,960 |
| New Prairie United | 2,869 | 2,910 | 2,850 | 2,815 | 2,819 |
| Union-North United | 1,274 | 1,228 | 1,227 | 1,221 | 1,188 |

Conflict to resolve: the file does not say what "2026" means. Aggregators cited SBCSC 14,486 and Mishawaka 5,034 for 2025-26, and PHM 11,360 from CCD 2024-25; these match the sheets labelled 2024, 2024 and 2023, which suggests the aggregators are one to two years behind, or the sheet label runs ahead of the school year. Verify against a known official count before showing a year.

Spending per student: DLGF Report on Expenditures Per Capita (2026-04-30), Schools table, "Per Student" = total expenditures (net of interfund loans, transfers, investment purchases; IDOE data, current as of 2026-04-01) / ADM, calendar years 2024 and 2025:

| Corporation | 2024 | 2025 |
|---|---|---|
| South Bend Community | $24,129.63 | $24,600.56 |
| Mishawaka | $20,017.68 | $15,241.25 |
| Penn-Harris-Madison | $11,406.67 | $17,963.83 |
| John Glenn | $11,047.54 | $14,144.41 |
| New Prairie | $14,111.19 | $14,617.30 |
| Union-North | $14,133.40 | $14,782.51 |

State median 2024 $15,983.06, 2025 $17,286.94; average $17,822.02 / $17,844.46. Check: `pdftotext -layout` put these values on the wrong rows (alternate shaded rows). The `-table` mode ranks line up with the values (for example SBCSC 2025 rank 9, $24,600.56; PHM 2024 rank 262, $11,406.67), so I used it, but a visual check of the PDF is recommended. Large year-to-year swings (PHM +57%, Mishawaka -24%) likely reflect timing of capital and debt expenditure, which is in "total expenditures"; this is not a statement about classroom spending. Confidence: medium.

## 5. SBCSC 2026 scope

- DLGF certified order (MON-026), SBCSC funds: Referendum Fund-Exempt Operating $32,403,013; Debt Service $7,658,907; Debt Payment $10,212,938; Referendum Debt-Exempt Capital $3,803,000; Education $133,523,770; Operations $58,687,559; Unit Total $246,289,187 (these sum exactly). The DLGF note on the Debt Payment fund: "Budget has been reduced and approved for the displayed amt."
- Gateway sum $248,301,887 is $2.0M above the certified total (advertised before DLGF adjustment).
- Board vote $213,254,807 (ABC57 2025-11-04: "The 2026 budget passed 7-0, and totals $213,254,807"): neither article says which funds. Certified total minus the referendum operating fund is $213,886,174 (0.3% above); this is an arithmetic coincidence until confirmed.
- WVPE 2025-11-04: "The $257 million spending plan includes more than $132 million for salaries and classroom supplies." That is a third figure; the $132M matches the Education fund ($133.5M) roughly.
- Not found: the board's adopted budget document. Next step: SBCSC board packet for the 2025-11-03 meeting, or the Form 4 / Gateway "adopted" columns by fund.

## 6. HB 1210 (2026) and SEA 1

HB 1210 (HEA 1210-2026), signed 2026-03-12. DLGF memo "Legislation Affecting Local Income Taxes" (https://www.in.gov/dlgf/files/2026-memos/Legislation-Affecting-Local-Income-Taxes.pdf): current LIT ordinances expire 2029-01-01 (SEA 1 said 2028-01-01); counties and eligible municipalities may adopt new LIT ordinances from 2028-07-01 for collections starting 2029; "Under current law, distributions would therefore begin in 2030"; the repeal of the property tax replacement credit, LIT councils and levy freeze is delayed one year.
The unconfirmed gap detail is a mis-statement: section 133 (IC 6-3.6-6-23) says "a municipality with a population of 3,500 or more, instead of between 3,500 and 7,000, may adopt a resolution to be treated as eligible for a small town LIT rate", i.e., eligibility to share in the county's small-town LIT rate, not a city setting its own rate.
LSA fiscal note (LS 6805, prepared 2026-03-03, enrolled), mirror URL in the edits file: summary lists, among many items, "Effective Date for New LIT" (2028 to 2029), "LIT MUST" (local strategic task force to negotiate maximum LIT rates), "LIT-Funded Debt Service" reporting to DLGF, "Small Municipality LIT", Fire/EMS LIT, and the veterans deduction change to 100% for the totally disabled. Statewide property tax net revenue change from current law: CY2027 +$4.0M, CY2028 +$258.8M (2.1%). Appendix A, St. Joseph County, all units combined: CY2027 +$0.22M (0.0%), CY2028 +$45.89M (9.8%), CY2029 +$0.24M (0.0%). The CY2028 amount reflects the delay, not new money. No split for county, South Bend or schools. The primary URL on iga.in.gov (HB1210.06.ENRS.FN001) was not fetched directly; a billtexts.s3 mirror was used.

SEA 1 (2025) dollars: SBCSC only. ABC57 (2025-04-16): "$4,872,630 of funding in 2026, $7,361,920 in 2027, and $15,198,240 for 2028" (about $27M, "legislative estimates"); IPM (2025-04-09) attributes about $27.4M to LSA for the House-amended bill. These predate the final law. South Bend: the city's Legislative Impact deck (2025-08-13, edoc 398902) has only charts; it says MLGQ was capped at 4% for 2026 (5.6% estimated uncapped) and "There is no LSA estimate of LIT revenues under the new LIT structure". The LSA "Estimated Net Levies SB 1 (2025)" report by unit that the deck cites was not located; that is where county, South Bend and other school figures would be. The same deck cites DLGF's county Circuit Breaker Reports 2020-2025, a lead for the circuit-breaker gap.

## 7. Unexplained budget jumps (23 gap rows)

All amounts are Gateway adopted amounts by fund, deduplicated. Full per-row text is in the edits file.

Explained with a document or exact match (7 rows):
- Portage Twp 2024-25: new St. Joseph County Fire Territory (Portage and Warren). Territory general $0 to $6,083,530, new debt service $1,106,433. WVPE 2024-03-29 and ABC57 2024-03-28.
- Union Twp 2025-26: new debt service $391,965 equals the DLGF order's Emergency Fire Loan $391,965.
- Walkerton Library 2017-18 and 2018-19 (2 rows): new building; Construction fund $775,000 in 2018 only; news reports bid award 2017 and opening 2018.
- Centre Twp 2018-19 and Portage Twp 2018-19 (2 rows): fire territory funds move from Portage (to $0) to Centre in 2019, matching WVPE's description of the Southwest Central territory covering Portage and Centre. The 2019 start is inferred from the fund pattern.
- Olive Twp 2019-20: township fire funds replaced by a Special Fire Protection Territory fund in 2020; DLGF 2026 order lists the Olive-New Carlisle-Hudson Fire Protection Territory (formation date inferred).

Explained by what the new fund is (9 rows): New Carlisle 2024-25 (Local Road & Bridge Match $1.875M, 2022 GO Bond Proceeds $0.9M); North Liberty 2023-24 and Osceola 2022-23 (ARPA funds); Walkerton 2023-24 (Community Crossings Matching Grant $2.2M); Warren 2021-22 and 2022-23 (fire building and equipment debt funds); Liberty 2025-26 (larger fire-territory appropriation); Airport 2019-20 and 2022-23 (consistent in timing with the $105M Taxiway Bravo project 2020-2025 and the $70M apron/taxiway project 2023, not linked by a document).

Not explained (6): Harris Twp 2015-16; Liberty Twp 2020-21; Penn Twp 2012-13; Warren Twp 2015-16 and 2018-19; South Bend civil city 2016-17 (fund renames plus an unexplained +$32M General fund). Reframed (1): South Bend 2021-22 is better described as a low 2021 (General $73.2M against $104.5M in 2020 and $109.6M in 2022).

## 8. RDC, jail, Mishawaka

- Redevelopment Commission: March 2026 Monthly Financial Report (https://docs.southbendin.gov/WebLink/0/edoc/407521/2026-03%20Monthly%20Financial%20Report.pdf): RDC controlled funds Current Amended Budget expenditures $135,109,942 (TIF $107,047,275; redevelopment funds $27,032,666; debt service $1,030,000), estimated revenue $48,613,328. Amended, not adopted. The same report's debt schedule: total debt at 1/1/2026 $298,686,137 (civil city $181,211,137; RDC revenue bonds $117,475,000), projected 12/31/2026 $270,264,580; proposed as a debt.csv row.
- County jail construction cost and funding: not found in two searches (results were other counties or St. Joseph County, Michigan).
- Mishawaka revenue by source (MON-010): not filled. https://mishawaka.in.gov/download/?wpdmdl=13302 returned HTTP 403 to a scripted fetch; I did not try to work around it. In Chrome it opens as an image-only PDF with no extractable text; reading it needs a visual pass or a manual download.

## Failed or unproductive URLs

- https://docs.southbendin.gov/WebLink/0/fol/398646/Row1.aspx (WebFetch: "Cookies must be enabled"; worked in Chrome as Browse.aspx?id=398646)
- https://docs.southbendin.gov/WebLink/Browse.aspx?id=88&dbid=0&repo=sbend (Ordinances: year folders page, 2025 not reachable in the tool)
- https://docs.southbendin.gov/WebLink/Search.aspx?... searchcommand name search (form only, no results)
- https://docs.southbendin.gov/WebLink/DocView.aspx?id=414922 via scripted fetch (empty); use the browser
- https://mishawaka.in.gov/download/?wpdmdl=13302 (403 scripted; image-only in Chrome)
- https://www.in.gov/dlgf/reports-and-data/budget-orders/ (404)
- https://www.in.gov/doe/school-operations/finance/school-financial-reports (no per-pupil files linked)
- LSA SEA 1 fiscal note guessed URLs on billtexts.s3 (none resolved; not pursued further)

## Not searched

DLGF budget orders for 2012-2021 (rates and AV); AV for 2012-2025; circuit-breaker reports; reserves for county and Mishawaka; Gateway AFR debt for years before 2024; unit-level HB 1210/SEA 1 figures for the county and South Bend; Mishawaka utility budgets; the 2025 SBCSC board packet.
