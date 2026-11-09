# 06 - Campaign Finance, St. Joseph County, Indiana (research notes, collected 2026-11-07)

Status: PARTIAL. State-legislative committee data was pulled from the Indiana state bulk files (strong). Local (mayor, council, county, school board, township) data was NOT obtainable: county filings are not in the state database and the county site blocks automated fetches. 12 of 25 WebSearch calls used (the search tool returned almost no finance figures; remaining budget unused).

## 1. Where the data lives

| Filer group | Where filed / found | Machine-readable? | Notes |
|---|---|---|---|
| State legislature, statewide candidates, PACs, party committees that file with the state | Indiana Election Division: https://campaignfinance.in.gov/PublicSite/Search.aspx | YES: bulk CSV (below) | Candidate search: .../SearchPages/CandidateSearch.aspx ; Committee: .../CommitteeSearch.aspx ; Race: .../PoliticalRaceSearch.aspx ; Contributions: .../ContributionSearch.aspx ; Expenditures: .../ExpenditureSearch.aspx |
| County and municipal candidates (mayor, council, clerk, sheriff, prosecutor, auditor, etc.), school board, township | County Voter Registration / Election Board (CFA-4 reports filed locally). Other Indiana counties host PDFs (e.g., Allen County https://allencountyinvoters.gov/wp-content/uploads/2023/10/Hartman-Nathan-2023-Pre-General.pdf; LaPorte https://laporteco.in.gov/wp-content/uploads/2026/01/Osborne-Campaign-Fund-Ian-Osborne.pdf). I found no St. Joseph County equivalent. | Scanned/PDF if posted | Per search-result summary, local-office reports go to the county election office (not checked against statute text). |
| Federal candidates | FEC | yes | Out of scope |

Bulk download (works with plain curl; no login): page https://campaignfinance.in.gov/PublicSite/Reporting/DataDownload.aspx . Files 2000-2026, extracted 2026-11-07 01:03. URL pattern (use forward slash, not the backslash printed on the page):
`https://campaignfinance.in.gov/PublicSite/Docs/BulkDataDownloads/{YEAR}_ContributionData.csv.zip` and `.../{YEAR}_ExpenditureData.csv.zip`
- Contribution columns: FileNumber, CommitteeType, Committee, CandidateName, ContributorType, Name, Address, City, State, Zip, Occupation, Type, Description, Amount, ContributionDate, Received_By, Amended.
- Expenditure columns: FileNumber, CommitteeType, Committee, CandidateName, ExpenditureCode, Name, ..., OfficeSought, ExpenditureType, Description, Purpose, Amount, Expenditure_Date, Amended.
- LIMITS: grouped by calendar year FILED (not election cycle); no district/county field; no cash-on-hand or beginning balance; amended rows may duplicate; some CSV rows malformed. Cash on hand must come from the report views on the website (ASP.NET search pages; only the landing and download pages were read).

Verified: searching all 2015-2026 contribution files for committee names containing Mueller, Wood, Upchurch, Critchlow, Haas, Hazen, Ladyga, "South Bend", "Mishawaka", Sheriff, Prosecutor, Common Council, school board, township found NO municipal/county candidate committees. Only state candidates, PACs, and parties appear. Local candidates are NOT in the state database.

County site: https://www.sjcindiana.gov/ and https://southbendin.gov/ returned HTTP 403 to WebFetch and to curl with browser user-agent, so I could not check for an online portal. Try a real browser (Claude in Chrome) on the Voter Registration/Election Board page and Document Center. southbendtribune.com is blocked to the search tool's crawler.

## 2. Mayors (South Bend, Mishawaka) - 2019, 2023

No dollar totals found. Only qualitative/outcome facts:

| Race | Candidate | Party | Outcome | Finance fact | Source |
|---|---|---|---|---|---|
| South Bend mayor, 2019 Dem primary (2019-05-07) | James Mueller | D | Won, 4,447 votes (37.37%) | Led field in fundraising per article; no amount; Buttigieg donated to his campaign | https://en.wikipedia.org/wiki/2019_South_Bend_mayoral_election |
| same | Jason Critchlow | D | 3,081 (25.89%) | Second in fundraising; no amount | same |
| same | Lynn Coleman 2,701; Regina Williams-Preston 876; Oliver Davis 723; others under 25 votes | D | lost | none found | same |
| South Bend mayor 2019 general (2019-11-05) | Mueller (D) 9,437 / 63.41%; Sean Haas (R) 5,445 / 36.58% | | Mueller won | none found | same |
| South Bend mayor 2023 Dem primary | Mueller (won, ~68%) vs Henry Davis Jr. | D | Mueller nominated | A Tribune headline (title only seen) says Mueller's money wins up and down the primary ballot; no figures | search result title, Tribune via Yahoo |
| South Bend mayor 2023 general | Mueller (D) vs Desmont Upchurch (R) | | Mueller reelected 2023-11-07 | Colwell column (updated 2023-09-29): Upchurch "has scant funding" and gets no help from the Republican organization; no amounts | https://www.yahoo.com/news/colwell-apathy-could-contender-south-093145458.html |
| Mishawaka mayor 2019, 2023 | Dave Wood (incumbent) | R (not verified here) | not confirmed in this pass | NOT FOUND | - |

A search result titled "Colwell: Indiana's biggest spending mayoral race ever is ... not local" (https://www.aol.com/colwell-indianas-biggest-spending-mayoral-093855409.html) returned 404; its relevance to St. Joseph County is unknown.

## 3. Indiana House and Senate - state-filed committees (from bulk CSVs)

Method: summed Amount by calendar year filed per candidate committee (C = contributions filed that year; E = expenditures filed that year). NOT election-cycle totals, NOT cash on hand. Rounded to dollars.

District mapping (per search-result summaries of statisticalatlas.com pages; current boundaries; verify at iga.in.gov): St. Joseph County lies in Senate Districts 8, 9, 10, 11 and House Districts 5, 6, 7, 8, 21. HD 7 includes parts of Mishawaka/South Bend; HD 5 Mishawaka/Granger; HD 6 part of South Bend; HD 8 Granger/Hudson Lake/Notre Dame. 2024 incumbents per https://en.wikipedia.org/wiki/2024_Indiana_House_of_Representatives_election : HD5 Dale DeVon (R), HD7 Jake Teshka (R), HD8 Ryan Dvorak (D), HD21 Timothy Wesco (R), all held. Bauer (HD6, D) and Niezgodski (SD10, D) per party/Senate Democrats sites. Pressel, Rogers, Mishler, Bohacek links to SJC are UNCONFIRMED (and boundaries changed in 2021); they are in the tables only because they matched searches. Verify before use.

Source for every row: https://campaignfinance.in.gov/PublicSite/Docs/BulkDataDownloads/{YEAR}_ContributionData.csv.zip and _ExpenditureData.csv.zip (extract 2026-11-07). Committee names as filed.

### 3a. By committee and filing year (USD)

| Committee (seat) | Year filed | Receipts C | Expenditures E |
|---|---|---|---|
| David Niezgodski for Senate District 10 (D; SD10) | 2016 | 144,014 | 142,826 |
| same | 2017 | 57,100 | 43,354 |
| same | 2018 | 104,400 | 125,238 |
| same | 2019 | 90,368 | 65,901 |
| same | 2020 | 162,653 | 194,477 |
| same | 2021 | 83,450 | 43,728 |
| same | 2022 | 91,340 | 82,294 |
| same | 2023 | 94,197 | 64,232 |
| same | 2024 | 224,851 | 303,845 |
| same | 2025 | 74,162 | 50,046 |
| Committee to Elect Jake Teshka (R; HD7) | 2020 | 353,664 | 350,207 |
| same (a 2018 committee "Friends of Jake Teshka" exists; not totaled) | 2021 | 73,776 | 40,847 |
| same | 2022 | 318,863 | 328,231 |
| same | 2023 | 114,139 | 117,878 |
| same | 2024 | 224,796 | 110,461 |
| same | 2025 | 135,050 | 167,138 |
| same | 2026 (to 11/7) | 155,384 | 61,903 |
| Ryan Dvorak for State Representative (D; HD8) | 2016 | 19,465 | 16,878 |
| same | 2017 | 5,375 | 4,998 |
| same | 2018 | 9,137 | 10,755 |
| same | 2019 | 3,950 | 4,988 |
| same | 2020 | 7,500 | 8,321 |
| same | 2021 | 6,424 | 4,914 |
| same | 2022 | 4,900 | 3,689 |
| same | 2023 | 8,200 | 3,766 |
| same | 2024 | 7,800 | 5,118 |
| same | 2025 | 5,700 | 3,620 |
| same | 2026 | 16,850 | 15,339 |
| Dale DeVon for State Rep (R; HD5) | 2016 | 23,100 | 32,931 |
| same | 2017 | 13,200 | 13,166 |
| same | 2018 | 380,963 | 393,259 |
| same | 2019 | 14,809 | 5,627 |
| same | 2020 | 373,060 | 389,760 |
| same | 2021 | 33,328 | 12,106 |
| same | 2022 | 342,247 | 364,821 |
| same | 2023 | 29,600 | 10,092 |
| same | 2024 | 261,929 | 271,571 |
| same | 2025 | 23,150 | 12,311 |
| same | 2026 | 186,795 | 208,256 |
| Maureen Bauer for State Representative (D; HD6) | 2020 | 55,156 | 48,011 |
| same | 2021 | 25,078 | 3,148 |
| same | 2022 | 34,993 | 29,520 |
| same | 2023 | 23,202 | 16,457 |
| same | 2024 | 38,294 | 34,502 |
| same | 2025 | 37,734 | 17,822 |
| same | 2026 | 32,530 | 39,858 |
| Wesco Victory Committee (Timothy Wesco, R; HD21) | 2016 | 18,170 | 26,039 |
| same | 2018 | 8,471 | 9,752 |
| same | 2020 | 9,014 | 17,476 |
| same | 2022 | 41,852 | 45,415 |
| same | 2024 | 13,750 | 24,400 |
| same | 2025 | 28,129 | 10,812 |
| same | 2026 | 10,030 | 28,422 |
| (Wesco odd years: C 2015 8,350; 2017 8,449; 2019 7,604; 2021 5,550; 2023 17,300) | | | |
| UNCONFIRMED district: Friends of Jim Pressel (R) | 2016 | 283,677 | 286,505 |
| same | 2018 | 129,474 | 147,914 |
| same | 2022 | 119,294 | 107,574 |
| same | 2024 | 146,409 | 123,232 |
| same | 2026 | 241,545 | 275,453 |
| UNCONFIRMED: Linda Rogers for State Senate (R) | 2018 | 282,147 | 308,885 |
| same | 2022 | 445,582 | 552,600 |
| same | 2026 | 544,172 | 532,876 |
| UNCONFIRMED: Mishler for State Senate (Ryan Mishler, R) | 2018 | 91,430 | 60,367 |
| same | 2020 | 106,740 | 101,418 |
| same | 2022 | 97,444 | 79,392 |
| same | 2024 | 105,031 | 50,660 |
| UNCONFIRMED: Committee to Elect Bohacek for Senate (Mike Bohacek, R) | 2020 | 110,546 | 63,540 |
| same | 2024 | 190,081 | 285,297 |
| Joe Zakas for State Senator (R; former Senate seat) | 2016 | 11,100 | 10,721 |
| same | 2018 | 33,177 | 35,961 |

Other committees surfaced by name search but district/county not confirmed and not tabulated: Friends of Shelli Yoder (2020 C 118,113); Andy Lyons; Friends of Joseph Trost; Tracy Brown for Indiana; Devon Wellington (2026 C 80,928, E 69,886). Pat Bauer for Indiana (B. Patrick Bauer, former HD6 leader) is a residual committee (C 2016 7,450; 2018 9,450; E 2020 44,917).

### 3b. Largest funders, filing years 2016-2026 (summed by name as listed; spelling variants split totals, so understated)

| Committee | Top funders (USD) | Contributor-type totals (USD) |
|---|---|---|
| Niezgodski SD10 | I-PACE 73,000; IBEW PAC Voluntary Fund 65,050; UA Political Education Committee 65,000; Indiana State Pipe Trades Assn PAC Fund 32,500; Ironworkers Local 395 PAL 29,700 | PAC 629,170; "Political Action" 283,691; Other Org 57,679; Corporation 51,891; Labor Org 47,940 |
| Teshka HD7 | House Republican Campaign Committee 283,527; Indiana Republican Party 163,230; Indiana BANKPAC 40,000; Indiana Realtors PAC 33,000; Michael & Lindsay Misch 31,388 | Other Org 626,592; Individual 327,685; Political Action 289,600; PAC 67,350; Corp 63,256 |
| Dvorak HD8 | IBEW PAC Voluntary Fund 16,500; LAWPAC of Indiana 9,000 (+4,500 alt. spelling); Indiana Realtors PAC 7,000; Indiana Democratic State Central Committee 6,400 | PAC 59,875; Other Org 14,600; Individual 9,611; Labor 3,900; Corp 3,800 |
| DeVon HD5 | HRCC 848,108; Indiana Republican State Committee 206,972; Indiana Republican Party 102,576; Hoosiers for Quality Education PAC 27,300 | Other Org 1,136,762; PAC 396,756; Individual 68,937; Corp 40,827 |
| Maureen Bauer HD6 | B. Pat Bauer for State Rep 42,827; IBEW PAC Voluntary Fund 29,000; ActBlue Indiana 20,274; Iron Workers Local 395 IPAL 6,000; I-PACE 5,750 | PAC 120,194; Other Org 56,503; Political Action 31,040; Individual 20,115; Corp 18,265 |
| (unconfirmed) Pressel | Indiana House Republican Campaign Committee 262,102; Indiana Realtors PAC 56,000 | - |
| (unconfirmed) Rogers | Senate Majority Campaign Committee 470,073; Indiana Republican State Committee 167,306 | - |

Opponents in each race were NOT identified (bulk files have no race field). To do: PoliticalRaceSearch (https://campaignfinance.in.gov/PublicSite/SearchPages/PoliticalRaceSearch.aspx) or Ballotpedia/Wikipedia district results, then sum their committees the same way. Cash on hand not computed.

## 4. County officers, Commissioners, County Council, Common Councils, clerks, township, school board

Only news items found, none full reports:

| Race | Candidate | Fact | Report period | Source |
|---|---|---|---|---|
| South Bend city clerk 2023 general | Bianca Tirado (D) | Spent nearly $52,000 | "as of Oct. 20" (2023) | https://www.yahoo.com/news/everything-know-south-bends-contested-084132878.html |
| South Bend city clerk 2023 general | Tina Wilson (R) | St. Joseph County Republican Party gave her more than $13,000 (most it spent on any South Bend candidate, per article) | not stated | same |
| South Bend Common Council Dist. 3, 2023 | Sonia Perez (R) | county GOP paying nearly $3,800 for her campaign | not stated | same |
| South Bend Common Council at-large, 2023 | Rhonda Richards (R) | received more than $2,800 from county Republicans | "this election cycle" | same |
| Mishawaka city clerk (year unconfirmed, likely 2023) | Hazen vs. Ladyga-Block | Per search-result summary only: Hazen raised more than $50,000; Ladyga-Block $30,352; Ladyga-Block won ninth term. Article not fetched (aol/yahoo URLs 404). UNVERIFIED | unknown | search result "Ladyga-Block elected to ninth term as city clerk in Mishawaka" |

Everything else (Sheriff, Prosecutor, Auditor, Treasurer, Clerk, Recorder, Assessor, Coroner, Surveyor, Commissioners, County Council, township, school board): not found.

## 5. Parties and PACs

State-filed committees with St. Joseph names (2015-2026 contribution files; totals are contributions as filed):

| Committee | Type | Rows | Total contributions | Years |
|---|---|---|---|---|
| South Bend Fire Fighters Political Action Committee | PAC | 502 | ~105,100 | 2015-2026 |
| St. Joseph Valley Plumbing, Heating and Cooling PAC Fund | PAC | 24 | ~25,700 | 2015, 2018-2026 |
| St Joseph Libertarian Party | Regular Party | 13 | ~1,172 | 2022-2025 |
| Chamber of Commerce of St. Joseph County PAC | PAC | 2 | ~200 | 2015-2016 |

St. Joseph County Democratic and Republican party committees: not found under "St. Joseph" / "Joseph County" in the state files; they may file locally or under another name. Unresolved. Evidence the county GOP funds city candidates: Section 4.

## 6. Gaps / not found

- South Bend mayor 2019, 2023 (primary and general): no raised/spent/COH for any candidate.
- Mishawaka mayor 2019, 2023: nothing.
- South Bend and Mishawaka Common Councils: only 3 partial party-support figures.
- City clerks: South Bend 2023 partial; Mishawaka unverified.
- County Commissioners, County Council, Sheriff, Prosecutor, Auditor, Treasurer, Clerk, Recorder, Assessor, Coroner, Surveyor 2016-2026: nothing.
- Township and school board 2018-2026: nothing.
- County party committee totals: not found.
- Legislative races: opponents' committees not identified; cash on hand not obtained; election-cycle totals not computed; Teshka 2018 committee not totaled; some committees' early years absent (e.g., Bauer begins 2020, Teshka 2020) - possibly other/prior committee names, unresolved.
- FollowTheMoney.org / OpenSecrets state data: not searched. WVPE, South Bend Voice, Inside Indiana Business: not specifically searched.
- Outside/PAC spending in local races in news: not found.

Next steps: (1) open sjcindiana.gov Voter Registration/Election Board and southbendin.gov in a real browser; if no portal, file an Indiana APRA request for CFA-4s; (2) use campaignfinance.in.gov Race search for opponents and cash on hand; (3) Wikipedia/Ballotpedia district pages for challengers.

## 7. Sources

- https://campaignfinance.in.gov/PublicSite/Search.aspx (and SearchPages/*, Reporting/DataDownload.aspx)
- https://campaignfinance.in.gov/PublicSite/Docs/BulkDataDownloads/{2015..2026}_ContributionData.csv.zip and _ExpenditureData.csv.zip
- https://en.wikipedia.org/wiki/2019_South_Bend_mayoral_election
- https://en.wikipedia.org/wiki/2024_Indiana_House_of_Representatives_election
- https://www.yahoo.com/news/everything-know-south-bends-contested-084132878.html
- https://www.yahoo.com/news/colwell-apathy-could-contender-south-093145458.html
- Search-result-only (not fetched): Mishawaka clerk article; statisticalatlas.com district pages; https://ballotpedia.org/Campaign_finance_in_Indiana
- Blocked: https://www.sjcindiana.gov/ , https://southbendin.gov/ (HTTP 403); southbendtribune.com (crawler-blocked)
