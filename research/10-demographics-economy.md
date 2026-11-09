# 10 - Community social and economic context: St. Joseph County, Indiana (FIPS 18141)

Compiled 2026-11-07 by a research agent. Collect-and-report only; no causal claims about voting. Every table lists its source. ACS = American Community Survey. MOE = margin of error (90% confidence unless noted).

## Access notes (read first)

1. **The Census API (api.census.gov) now requires a key.** Keyless calls such as `https://api.census.gov/data/2023/acs/acs5/profile?get=NAME,DP03_0062E&for=county:141&in=state:18` return a 302 redirect to `https://api.census.gov/data/missing_key.html` ("A valid key must be included with each data API request"). I did not look for or use any key. A free key can be requested from the Census Bureau if the owner wants the official API.
2. **Substitute used: Census Reporter API** (`api.censusreporter.org`), which serves the same ACS tables (B/C table IDs, estimates plus MOEs) without a key. It only supports the **latest release (ACS 2024 5-year, 2020-2024)**. Every older release I tried (`acs2010_5yr` through `acs2023_5yr`, 1-year releases, `dec2010_pl`, `dec2020_pl`) returned "release isn't supported". It rejects the default Python urllib User-Agent (HTTP 403); curl works.
3. **Consequence: no ACS ~2010 comparison was obtained.** The 2010 comparison in this file is limited to decennial 2010 race/ethnicity (from Wikipedia, which cites Census PL 94-171) and BLS LAUS 2010. See "Gaps".
4. `data.census.gov` and `census.gov/quickfacts` returned HTTP 403 to WebFetch. DataUSA's old API URL now returns an HTML page.
5. ACS 5-year estimates are period estimates (2020-2024), not a single year. Dollar values are in **2024 inflation-adjusted dollars** (Census Reporter table titles say so). Anyone comparing with other years must re-inflate (e.g., BLS CPI-U or the Census-published ACS adjustment factors); I did not adjust anything.
6. Township percentages for small townships (Greene, Liberty, Lincoln, Madison, Olive, Union, Warren) rest on small samples. Only population and median household income MOEs are shown below; other MOEs were pulled but not tabulated (they are in the saved JSON). Treat small-township values as rough.
7. Census "county subdivisions" in Indiana are the 13 civil townships. **Cities do not follow township lines** (South Bend and Mishawaka each cover parts of several townships); I did not obtain a place-to-township crosswalk, so city and township rows overlap and must not be added together.

---

## A. Demographics

### A1. Population trend (decennial census)

Source: Wikipedia articles "St. Joseph County, Indiana", "South Bend, Indiana", "Mishawaka, Indiana" (tables citing the U.S. Census Bureau decennial counts), fetched 2026-11-07. These are secondary; the primary series is the Census Bureau's decennial census (a re-pull from census.gov is recommended before publication).

| Year | St. Joseph County | South Bend | Mishawaka |
|---|---|---|---|
| 1930 | 160,033 | 104,193 | 28,630 |
| 1940 | 161,823 | 101,268 | 28,298 |
| 1950 | 205,058 | 115,911 | 32,918 |
| 1960 | 238,614 | 132,445 | 33,361 |
| 1970 | 245,045 | 125,850 | 36,060 |
| 1980 | 241,617 | 109,727 | 40,201 |
| 1990 | 247,052 | 105,511 | 42,608 |
| 2000 | 265,559 | 107,789 | 46,557 |
| 2010 | 266,931 | 101,168 | 48,252 |
| 2020 | 272,912 | 103,453 | 51,063 |
| ACS 2020-2024 5-yr (not a census count) | 273,040 | 103,085 (MOE +/-716) | 51,021 (MOE +/-49) |

Observation (arithmetic only): South Bend's 1960 peak (132,445) to 2020 (103,453) is a decline of about 22%; the county grew over the same period (238,614 to 272,912, about +14%).

Township population, ACS 2020-2024 (see A3). Township decennial history 1950-2020 was **not collected** (gap).

### A2. Race/ethnicity, 2010 vs 2020 (decennial; non-Hispanic categories, Hispanic any race shown separately)

Source: Wikipedia tables derived from Census PL 94-171 (county and South Bend). Mishawaka 2010 non-Hispanic table not obtained; its page gives only 2010 percentages with Hispanics included in race categories.

| Group | County 2010 | County 2020 | South Bend 2010 | South Bend 2020 |
|---|---|---|---|---|
| White alone, non-Hispanic | 75.56% | 69.09% | 55.82% | 50.16% |
| Black alone, non-Hispanic | 12.52% | 12.98% | 26.19% | 25.23% |
| Asian alone, non-Hispanic | 1.87% | 2.41% | 1.28% | 1.50% |
| Two or more races, non-Hispanic | 2.27% | 4.94% | 3.15% | 5.47% |
| Hispanic or Latino (any race) | 7.27% | 9.74% | 12.96% | 16.67% |
| Total population | 266,931 | 272,912 | 101,168 | 103,453 |

Mishawaka (race categories include Hispanics, so not comparable to the table above): 2010 White 86.1%, Black 6.9%, Asian 1.9%, Hispanic any race 4.5%; 2020 White 77.2%, Black 9.5%, Asian 2.8%, Two or more 7.9%, Hispanic any race 6.1%. Caution: Census changed its race-question processing in 2020, which raised "two or more races" counts; apparent 2010-2020 changes in that category are partly methodological.

### A3. Profile: county, cities, 13 townships (ACS 2020-2024 5-year)

Source: Census Reporter API, release `acs2024_5yr`. Tables B01003, B01002, B01001, B03002, B05002, B25010, B15003, B21001, B18101. Percentages calculated by me from the table cells (formulas in "Reusable queries"). Race columns are non-Hispanic (B03002); "Hisp" is Hispanic any race. "HS+" = high school graduate or higher, age 25+. "Bach+" = bachelor's degree or higher, age 25+. "Vets" = share of civilian population 18+ who are veterans. "Disab" = share of civilian noninstitutionalized population with a disability. Population MOE is the 90% MOE reported by the Census Bureau.

| Area | Pop | Pop MOE | Median age | Under 18 % | 65+ % | White NH % | Black NH % | Asian NH % | Hisp % | 2+ races NH % | Foreign-born % | Avg hh size | HS+ % | Bach+ % | Vets % | Disab % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| St. Joseph County | 273,040 | n/a | 36.7 | 23.2 | 16.9 | 68.9 | 12.3 | 2.7 | 10.5 | 4.9 | 6.9 | 2.44 | 91.5 | 33.5 | 5.5 | 13.4 |
| South Bend (city) | 103,085 | 716 | 34.8 | 25.5 | 15.0 | 50.9 | 22.4 | 2.3 | 17.9 | 5.8 | 8.5 | 2.44 | 87.8 | 29.3 | 4.9 | 15.0 |
| Mishawaka (city) | 51,021 | 49 | 36.0 | 20.8 | 16.6 | 73.7 | 10.7 | 2.4 | 6.4 | 6.3 | 7.0 | 2.18 | 91.1 | 29.2 | 5.2 | 15.1 |
| Centre Twp | 14,438 | 27 | 43.5 | 24.3 | 23.9 | 77.1 | 8.8 | 0.5 | 10.6 | 2.4 | 3.8 | 2.48 | 94.7 | 39.1 | 6.0 | 12.7 |
| Clay Twp | 34,246 | 29 | 39.6 | 16.4 | 20.6 | 74.1 | 12.5 | 5.5 | 3.8 | 3.6 | 9.4 | 2.15 | 93.5 | 42.6 | 6.8 | 12.7 |
| German Twp | 10,020 | 33 | 38.9 | 22.0 | 18.9 | 66.6 | 20.1 | 2.6 | 8.2 | 2.4 | 6.7 | 2.36 | 95.3 | 32.2 | 6.7 | 12.9 |
| Greene Twp | 2,954 | 16 | 51.9 | 16.6 | 30.2 | 89.0 | 1.3 | 0.0 | 1.9 | 5.7 | 0.3 | 2.30 | 94.7 | 36.5 | 9.4 | 14.4 |
| Harris Twp | 24,558 | 39 | 36.9 | 28.9 | 13.9 | 75.1 | 4.0 | 8.4 | 7.9 | 4.2 | 10.0 | 2.79 | 97.6 | 55.5 | 5.7 | 7.8 |
| Liberty Twp | 3,412 | 20 | 40.3 | 21.1 | 19.8 | 95.7 | 0.9 | 0.1 | 1.3 | 1.8 | 0.6 | 2.61 | 95.1 | 28.6 | 3.9 | 13.9 |
| Lincoln Twp | 2,775 | 213 | 32.9 | 26.7 | 16.0 | 90.6 | 1.5 | 0.5 | 3.1 | 4.0 | 2.0 | 2.54 | 94.0 | 24.1 | 4.9 | 15.5 |
| Madison Twp | 1,891 | 211 | 37.2 | 35.5 | 18.1 | 93.1 | 0.9 | 0.0 | 0.0 | 6.0 | 1.3 | 3.19 | 90.4 | 24.3 | 4.9 | 11.1 |
| Olive Twp | 4,363 | 18 | 38.9 | 25.8 | 18.2 | 89.1 | 0.7 | 0.4 | 3.4 | 4.1 | 1.3 | 2.44 | 97.6 | 29.8 | 7.7 | 13.0 |
| Penn Twp | 68,620 | 53 | 37.0 | 23.3 | 17.1 | 79.1 | 7.3 | 1.8 | 5.2 | 6.0 | 5.2 | 2.42 | 92.0 | 30.6 | 5.5 | 14.2 |
| Portage Twp | 94,489 | 85 | 32.5 | 24.2 | 13.5 | 51.2 | 20.8 | 1.9 | 19.4 | 6.0 | 8.4 | 2.47 | 86.3 | 26.7 | 4.4 | 14.8 |
| Union Twp | 3,475 | 29 | 43.6 | 22.8 | 21.4 | 88.0 | 0.2 | 0.0 | 8.1 | 2.5 | 0.3 | 2.37 | 95.7 | 21.6 | 6.0 | 12.8 |
| Warren Twp | 7,799 | 23 | 50.4 | 19.2 | 22.8 | 86.3 | 1.6 | 0.0 | 8.9 | 2.1 | 1.2 | 2.42 | 96.4 | 33.3 | 7.7 | 11.7 |

Notes: (a) Township populations sum to about the county total; city rows overlap townships. (b) Census Reporter returned the "average household size" in the B25010 total cell; verify against DP02 before publication. (c) Veteran share uses B21001 (civilian population 18+). (d) The Census Bureau's population MOE for the county is not reported by Census Reporter for B01003 (it is a controlled total).

---

## B. Income and housing

### B1. Income, poverty, housing (ACS 2020-2024 5-year; dollars in 2024 dollars)

Source: Census Reporter `acs2024_5yr`. Tables B19013 (median household income), B19301 (per-capita income), B17001 (poverty status), B19001 (income brackets), B25003 (tenure), B25077 (median home value, owner-occupied), B25064 (median gross rent), B25070 (gross rent as % of income). Child poverty = under-18 below poverty / under-18 for whom poverty is determined. Rent burdened = share of renter households (excluding "not computed") paying 30%+ of income. "n/a" = not published (too few cases).

| Area | Median HH income | HH income MOE | Per-capita income | Poverty % | Child poverty % | HH <$25k % | $25-50k % | $50-100k % | $100-150k % | $150k+ % | Own-occupied % | Median home value | Median rent | Rent-burdened % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| St. Joseph County | $66,868 | $1,255 | $36,834 | 14.2 | 19.7 | 15.9 | 21.2 | 31.6 | 16.2 | 15.1 | 69.0 | $192,800 | $1,062 | 49.1 |
| South Bend | $55,786 | $1,639 | $30,791 | 20.8 | 29.1 | 21.6 | 23.2 | 32.8 | 13.5 | 8.8 | 60.2 | $140,400 | $1,033 | 50.3 |
| Mishawaka | $54,291 | $4,328 | $34,469 | 16.4 | 26.5 | 18.6 | 28.0 | 31.8 | 12.2 | 9.4 | 49.3 | $155,500 | $1,070 | 47.5 |
| Centre Twp | $79,120 | $6,376 | $39,175 | 6.7 | 6.8 | 13.1 | 15.3 | 34.0 | 21.4 | 16.2 | 91.0 | $203,200 | $938 | 44.4 |
| Clay Twp | $72,406 | $3,600 | $43,698 | 9.8 | 8.9 | 13.7 | 18.9 | 33.2 | 16.7 | 17.5 | 66.5 | $226,400 | $1,132 | 49.6 |
| German Twp | $74,918 | $7,928 | $37,926 | 7.4 | 15.0 | 7.8 | 24.2 | 33.4 | 19.1 | 15.5 | 69.4 | $226,200 | $1,114 | 52.5 |
| Greene Twp | $74,587 | $14,842 | $42,308 | 6.1 | 8.2 | 10.4 | 15.1 | 37.2 | 19.6 | 17.8 | 97.2 | $209,500 | n/a | 57.9 |
| Harris Twp | $112,056 | $7,899 | $54,236 | 7.1 | 7.1 | 7.1 | 15.6 | 22.3 | 19.0 | 36.0 | 76.8 | $350,900 | $1,440 | 55.7 |
| Liberty Twp | $76,418 | $6,114 | $44,168 | 5.1 | 6.8 | 9.9 | 16.0 | 34.3 | 13.9 | 26.0 | 88.1 | $222,500 | $960 | 61.5 |
| Lincoln Twp | $66,622 | $5,674 | $30,264 | 6.1 | 6.6 | 14.5 | 22.0 | 36.9 | 18.7 | 8.0 | 75.5 | $145,800 | $821 | 53.1 |
| Madison Twp | $100,804 | $18,946 | $37,170 | 5.8 | 7.2 | 5.9 | 17.1 | 25.5 | 31.6 | 19.9 | 94.9 | $287,300 | $914 | 60.0 |
| Olive Twp | $78,964 | $6,673 | $40,013 | 3.5 | 1.2 | 8.1 | 20.6 | 33.0 | 21.1 | 17.1 | 77.1 | $232,100 | $1,043 | 24.1 |
| Penn Twp | $65,544 | $2,803 | $35,773 | 12.5 | 17.8 | 14.8 | 23.0 | 32.6 | 16.9 | 12.7 | 66.3 | $189,800 | $1,009 | 43.5 |
| Portage Twp | $52,872 | $2,198 | $28,867 | 23.2 | 32.9 | 22.9 | 23.9 | 32.1 | 12.3 | 8.7 | 60.5 | $121,500 | $1,038 | 52.1 |
| Union Twp | $76,636 | $13,607 | $40,287 | 9.6 | 8.6 | 18.7 | 16.3 | 29.3 | 13.9 | 21.9 | 85.3 | $238,200 | $873 | 40.6 |
| Warren Twp | $89,958 | $22,008 | $45,693 | 11.0 | 19.6 | 9.0 | 17.0 | 26.0 | 22.3 | 25.7 | 97.9 | $239,200 | $1,644 | 70.1 |

Caution: the "Own-occupied %" column is the share of occupied housing units that are owner-occupied (homeownership rate). Rent-burden values for townships with few renters (Greene, Liberty, Madison, Olive, Union, Warren) are unreliable (MOEs large). Compare the large-area rows (county, cities, Penn, Portage, Clay, Harris, Centre) with confidence; treat the rest as indicative.

Local context (not Census): the City of South Bend 2024 Annual Comprehensive Financial Report (ACFR) states St. Joseph County has about 106,330 households with median household income of $59,325 (a Census-source figure from an older ACS vintage; it differs from the 2020-2024 value above), compared with Indiana $62,723 and the U.S. $74,580; surrounding counties: Elkhart $58,350, La Porte $51,584, Marshall $53,889, Cass MI $52,741, Berrien MI $51,262. (ACFR PDF, "Demographic and Economic" narrative, ~p. 315 in the text extraction; vintage of the Census figures is not stated in the ACFR extract.)

### B2. Unemployment, St. Joseph County (BLS LAUS, annual average, not seasonally adjusted)

Source: BLS Public Data API v1 (no key), series `LAUCN181410000000003` (unemployment rate), `...06` (labor force), `...05` (employed). Query form: `POST https://api.bls.gov/publicAPI/v1/timeseries/data/` with JSON body `{"seriesid":["LAUCN181410000000003","LAUCN181410000000006"],"startyear":"2000","endyear":"2009","annualaverage":true}` (v1 allows max 10 years per request, so 3 requests). Period `M13` = annual average. Footnote on 2025: "Annual estimates for 2025 are 11-month averages that exclude October" (BLS API footnote, so the 2025 value is provisional and excludes October).

| Year | Unemployment rate % | Labor force | | Year | Unemployment rate % | Labor force |
|---|---|---|---|---|---|---|
| 2000 | 3.2 | 134,168 | | 2013 | 8.6 | 127,400 |
| 2001 | 4.5 | 133,122 | | 2014 | 6.5 | 128,902 |
| 2002 | 5.3 | 133,425 | | 2015 | 5.0 | 130,487 |
| 2003 | 5.2 | 132,488 | | 2016 | 4.5 | 134,333 |
| 2004 | 5.2 | 132,927 | | 2017 | 3.6 | 134,108 |
| 2005 | 5.3 | 134,430 | | 2018 | 3.6 | 136,342 |
| 2006 | 5.1 | 135,286 | | 2019 | 3.6 | 136,828 |
| 2007 | 5.0 | 133,094 | | 2020 | 8.8 | 131,664 |
| 2008 | 6.6 | 133,896 | | 2021 | 4.7 | 129,841 |
| 2009 | 11.4 | 130,258 | | 2022 | 3.5 | 130,527 |
| 2010 | 11.2 | 130,572 | | 2023 | 4.0 | 130,484 |
| 2011 | 9.9 | 130,977 | | 2024 | 4.7 | 129,768 |
| 2012 | 9.3 | 127,993 | | 2025 | 4.1 (provisional) | 130,397 |

Uncertainty: LAUS county figures are model-based estimates that are revised annually; the values above were retrieved 2026-11-07 and may differ from earlier publications.

---

## C. Economy and employers

### C1. Employment by industry, ACS 2020-2024 (workers 16+ by industry of employment; residents, all ownership)

Source: Census Reporter `acs2024_5yr`, table C24050 (summed across occupation groups from the "Total" cells). Shares of employed civilians 16+. Categories are the ACS 13-sector groupings.

| Industry | County % | South Bend % | Mishawaka % | Penn Twp % | Portage Twp % | Harris Twp % | Clay Twp % | Centre Twp % |
|---|---|---|---|---|---|---|---|---|
| Employed civilians 16+ (count) | 130,237 | 46,783 | 25,492 | 33,508 | 42,653 | 11,733 | 17,790 | 6,788 |
| Educational services, health care, social assistance | 28.8 | 27.2 | 28.1 | 26.5 | 28.3 | 33.9 | 36.7 | 24.1 |
| Manufacturing | 16.7 | 15.8 | 17.9 | 18.4 | 15.7 | 15.6 | 13.9 | 15.3 |
| Retail trade | 10.5 | 10.8 | 10.5 | 9.9 | 10.7 | 12.4 | 9.8 | 13.2 |
| Professional, scientific, management, administrative | 9.0 | 8.5 | 9.5 | 9.7 | 8.2 | 9.0 | 9.6 | 10.5 |
| Arts, entertainment, recreation, accommodation, food | 7.6 | 9.5 | 8.3 | 8.4 | 9.8 | 3.9 | 5.5 | 6.3 |
| Construction | 5.3 | 5.3 | 3.7 | 4.6 | 5.9 | 3.8 | 3.9 | 6.6 |
| Transportation, warehousing, utilities | 5.3 | 6.3 | 4.6 | 4.8 | 5.9 | 4.6 | 3.7 | 4.6 |
| Finance, insurance, real estate | 4.5 | 3.7 | 5.3 | 5.2 | 3.5 | 5.1 | 5.8 | 2.9 |
| Other services | 4.5 | 4.8 | 4.6 | 4.5 | 5.0 | 3.8 | 4.2 | 5.8 |
| Public administration | 3.1 | 3.0 | 4.3 | 4.3 | 2.6 | 2.2 | 2.3 | 3.1 |
| Wholesale trade | 2.9 | 3.2 | 1.9 | 2.4 | 2.4 | 3.8 | 2.4 | 5.2 |
| Information | 1.4 | 1.6 | 1.1 | 0.9 | 1.5 | 1.7 | 1.7 | 1.9 |
| Agriculture, forestry, fishing, mining | 0.5 | 0.3 | 0.2 | 0.4 | 0.5 | 0.3 | 0.4 | 0.6 |

Other townships' shares are in the saved JSON (`sources/demographics/censusreporter/acs2024_5yr_twp.json`, table C24050). Highest manufacturing shares among the small townships: Liberty 27.1%, Madison 24.4%, Lincoln 23.8%, Union 21.9%, Warren 21.7% (small samples).

### C2. Jobs located in the county, by industry (BLS QCEW, annual average employment, private sector unless noted)

Source: BLS QCEW open-data API, area slice for St. Joseph County: `https://data.bls.gov/cew/data/api/{YEAR}/a/area/18141.csv` (rows with `own_code`=5, `agglvl_code`=74 for private NAICS sectors; `agglvl_code` 70/71 for ownership totals). **The API only returns 2014 and later**; years 2001-2013 returned 404, so the requested 2005-2010 comparison could not be pulled this way (it exists only in the bulk annual files; see Gaps). Suppressed/zero cells reflect disclosure rules. These are jobs at workplaces in the county, a different universe from C1 (which counts residents).

| Sector (NAICS) | 2014 | 2015 | 2019 | 2024 |
|---|---|---|---|---|
| Manufacturing (31-33) | 14,834 | 15,129 | 14,743 | 13,078 |
| Health care and social assistance (62) | 19,115 | 19,593 | 20,767 | 23,097 |
| Retail trade (44-45) | 14,015 | 14,159 | 14,107 | 13,316 |
| Accommodation and food services (72) | 10,787 | 11,241 | 11,487 | 11,246 |
| Educational services, private (61) | 10,451 | 10,638 | 11,373 | 8,857 |
| Wholesale trade (42) | 5,431 | 5,718 | 5,750 | 5,641 |
| Construction (23) | 3,942 | 4,572 | 5,414 | 5,631 |
| Administrative and waste services (56) | 5,366 | 5,558 | 5,555 | 5,029 |
| Professional, scientific, technical (54) | 4,036 | 4,190 | 4,635 | 4,936 |
| Transportation and warehousing (48-49) | 2,839 | 2,932 | 3,482 | 3,823 |
| Other services (81) | 3,700 | 3,660 | 3,641 | 3,917 |
| Finance and insurance (52) | 3,355 | 3,365 | 3,623 | 3,500 |
| Arts, entertainment, recreation (71) | 1,050 | 1,106 | 1,966 | 2,708 |
| Real estate (53) | 1,531 | 1,433 | 1,605 | 1,727 |
| Information (51) | 1,688 | 1,603 | 1,289 | 1,253 |
| Management of companies (55) | 2,034 | 2,101 | 2,348 | 871 |
| Utilities (22) | 317 | 237 | 250 | 201 |
| Federal government (all) | 880 | 855 | 853 | 819 |
| State government (all) | 2,023 | 2,004 | 1,967 | 1,796 |
| Local government incl. public schools (all) | 9,704 | 9,798 | 9,815 | 9,377 |
| **All ownerships total** | **117,280** | **120,075** | **124,850** | **121,043** |
| Private total | 104,674 | 107,417 | 112,214 | 109,051 |

Caution: private "Educational services" (NAICS 61) covers private universities such as Notre Dame; the 2019-to-2024 drop (11,373 to 8,857) and the "Management of companies" drop (2,348 to 871) may reflect reclassification or disclosure changes rather than real job losses; I have not verified either. Average annual pay, all ownerships, 2024: $59,303 (2015: $41,787) (nominal dollars, QCEW `avg_annual_pay`).

### C3. Largest employers

No single dated, sourced, employee-count list for 2024-2026 was found. What exists:

| Source (vintage) | What it says |
|---|---|
| City of South Bend 2024 ACFR (fiscal year ended 12/31/2024), narrative | "The largest employers in St. Joseph County are: Beacon Health System, University of Notre Dame, South Bend Community School Corporation, St. Joseph Health System, Indiana University - South Bend, St. Joseph County, City of South Bend, AM General, Honeywell International, Inc, and Press Ganey Associates, Inc." Also: "Health and education lead the employment statistics for St. Joseph County." The extract showed no employee counts in this list. |
| Same 2024 ACFR, property tax ranking | Top ten taxpayers by assessed value (not employers): University of Notre Dame, AEP/Indiana Michigan Power, Air Wisconsin Airlines, Honeywell/Bendix, Lock Joint Tube, Edward Rose of Indiana, Tire Rack, etc. Ten largest = 12.28% of $4.216 billion total net assessed value. (Table text was jumbled by PDF extraction; rank order of names uncertain.) |
| City of South Bend 2017 ACFR (as quoted in Wikipedia "South Bend, Indiana") | Beacon Health System (Memorial) 7,088; University of Notre Dame 6,086; South Bend Community School Corporation 3,432; Indiana University South Bend 1,401; St. Joseph County 1,377; City of South Bend 1,285; Four Winds Casino 1,200; AM General 1,200; The South Bend Clinic 854; Press Ganey 850. Secondary source; check the 2017 ACFR itself. |
| University of Notre Dame, "Regional Economic Impact" report (PDF created 2024-10-24; data mostly FY/CY 2023) | "Notre Dame employs 8,340 faculty, staff, postdocs and graduate students"; says more people are employed at Notre Dame than anywhere else in St. Joseph County; regional economic impact $3.3 billion supporting 21,000 jobs in the region ("region" is a multi-county definition in the report). Saved copy: `sources/demographics/other/notre-dame-economic-impact-2024.pdf`. This is the university's own figure and uses its own definition of employee. |
| Indiana "Hoosiers by the Numbers" Major Employers, St. Joseph County (copyright 2026; licensed Data Axle; no counts or data year shown) | Ranked 1-10: Notre Dame Alumni Assn; University of Notre Dame; University-Notre Dame-Harper; St Joseph County; AM General Mfg Campus (Mishawaka); Honeywell Aerospace; Performance Plus; South Bend Tribune; Central Blood Bank; ITR Concession Co LLC (Granger). Commercial-directory ranking; not a reliable ordering of employers. URL: https://www.hoosierdata.in.gov/major_employers.asp?areaID=141 |
| Beacon Health System headcount | Search results gave inconsistent third-party values (about 4,187 to 5,146; one nonprofit database 1,608 for the parent entity). No authoritative 2024-2026 figure found. |
| UAW press release, 26 Sep 2025 | UAW Local 5 members at AM General ratified a contract on 25 Sep 2025: "around 400 UAW members at the company's Mishawaka complex"; 12% wage increase over three years (per the UAW). That is the bargaining unit, not total plant employment. |

Recommendation for the main session: pull the "Principal Employers" schedule from the South Bend ACFR statistical section (the 2024 PDF text extraction did not contain that table) and/or ask the South Bend Regional Chamber and the South Bend-Elkhart Regional Partnership for a dated list. The Chamber's 2025-2030 Strategic Plan (https://www.sbrchamber.com/clientuploads/PDFs/Strategic_Plan/FINAL_2025-2030_Strategic_Plan.pdf) says it represents "over 1,300 employers and 60,000 workers" (per search summary; not itself a largest-employer list).

### C4. Economic history milestones

| Date | Event | Source and caveat |
|---|---|---|
| 1852 | H.C. Studebaker begins making wagons and horse-drawn buggies in South Bend, later automobiles | South Bend 2024 ACFR narrative |
| 1933 | Studebaker workers organized as AFL Local 18310, later UAW Local 5; first UAW constitutional convention held in South Bend in 1936 | UAW Region 2B Local 5 history page (https://region2b.uaw.org/uaw-local-5/history), quoted via search summary; page itself not fetched |
| 17 Nov 1936 | Sit-down strike at Bendix Corporation, South Bend, described by the same UAW page as the first sit-down strike in America | Same UAW page (search summary); a historian's source is needed before publication |
| 20 Dec 1963 | Studebaker's South Bend plant ceased production (last Larks and Hawks 20 Dec; last Avanti 26 Dec) | Wikipedia "Studebaker" (cites period sources). Engine block plant closed 1964 (Wikipedia "South Bend"). Hamilton, Ontario plant closed 17 Mar 1966. |
| 1963 | "Eliminated 7,000 local jobs" | New America, "South Bend: Reinventing a 'Dying City'", citing NPR (S. Glinton, 28 Jun 2012). An AP story (via search summary) says about 7,000 Studebaker employees were about 8% of county employment. Earlier peak employment was far higher (Wikipedia says 45,000 at one time in South Bend; older company history figures differ). Employment numbers for the plant over time are inconsistent across sources; do not publish one number without a primary source. |
| 1963 onward | South Bend population fell from 132,445 (1960) to 101,168 (2010) | Census decennial (see A1) |
| 1983-1985 | AM General wins initial $1.2 billion contract (March 1983) for 55,000 Humvees; Mishawaka plant built 1984; production began fall 1984 | Wikipedia "AM General". LTV Corp. bought AM General in 1983. |
| 1997 | Ball Band (Uniroyal) in Mishawaka closes after import competition | Wikipedia "Mishawaka, Indiana" |
| 21 Jan 2011 | Newsweek published "America's Dying Cities," on which South Bend appeared | Cited by New America (Newsweek, 21 Jan 2011). Notre Dame Magazine reportedly dates the list differently (2010). I did not obtain the Newsweek article itself. |
| 2012 | Pete Buttigieg elected mayor; widely cited as the start of a new era | New America |
| 2015-2017 | Mercedes-Benz R-Class built at AM General Mishawaka | Wikipedia "AM General" |
| Feb 2023 | AM General wins U.S. Army JLTV A2 production contract worth more than $8.66 billion | Wikipedia "AM General" |
| Apr 2024 | AWS announces about $11 billion data center investment near New Carlisle; state says at least 1,000 jobs; Gov. Holcomb called it "the largest capital investment announcement in Indiana's history"; sales-tax exemptions over 50 years; up to $18.3 million in performance credits; AWS to contribute up to $7 million for State Road 2 | AP, 25 Apr 2024 (via ksat.com and others). Timeline: "over the next decade" per County Commissioners president Carl Baxmeyer. |
| Sep 2024 - 2026 | Construction began September 2024; Phase I reported operational about October 2025; Phase II planned for 2026 | Black Ridge Research profile (April 2026), a third-party tracker; building counts conflict across trackers. No official AWS or IEDC status was found. |
| Dec 2025 | A listing on Baxtel says the County Council cancelled a separate proposed $12 billion data center campus in New Carlisle | Single third-party listing; unverified. |
| 25 Sep 2025 | UAW Local 5 ratifies new AM General contract | UAW press release, 26 Sep 2025 |

**EV battery plant:** I found no evidence of an EV battery plant in St. Joseph County (the one search that touched the region returned only the AWS campus). Not specifically searched; mark as "not searched" for EV battery plants.

**Microsoft or Google data center in St. Joseph County:** not found; not specifically searched beyond the AWS query.

**RV industry:** Not searched. The RV industry is centered in neighboring Elkhart County (18039), with cross-county commuting; no sourced St. Joseph County figures collected.

### C5. Labor unions

- UAW Local 5 (South Bend; origins in Studebaker workers organized 1933; represents about 400 AM General workers in Mishawaka as of Sep 2025). Sources: UAW Region 2B (https://region2b.uaw.org/uaw-local-5/history); UAW press release (https://uaw.org/uaw-members-at-am-general-ratify-strongest-contract-in-decades/).
- St. Joseph County AFL-CIO Council (South Bend Common Council 1981 resolution recognizing it, via search result https://docs.southbendin.gov/WebLink/0/doc/97352/Page1.aspx, not fetched).
- A CauseIQ directory (third-party; unverified) lists IBEW Local 153 and UAW Local 2093 among larger union organizations in the South Bend metro.
- AM General reportedly planned to lay off more than 430 workers at its commercial assembly plant in Mishawaka (represented by UAW Local 5) (Inside Indiana Business; article date not shown in my results; search summary only).
- Not found: current union membership or density for St. Joseph County (BLS/CPS union membership is published only at the state level; see Gaps), Bendix/IUE local history, Michiana Area Labor Council history. Indiana University South Bend's Division of Labor Studies and the St. Joseph County Public Library's Michiana Memory collection are suggested leads.

---

## D. Social and economic patterns vs. voting (handled with care)

### D1. Published analyses found

I searched for credible academic, Census-based, or local-news analyses of how voting differs across St. Joseph County. **I found very little that qualifies.** The material below is attributed; none of it is my own causal claim.

| Item | What it says (paraphrase unless quoted) | Source and quality |
|---|---|---|
| WNDU, "Red and Blue Perspectives: St. Joseph and Berrien counties on 2024 election", 1 Nov 2024, by Davante Wade | Describes the county as one that "rests in a sea of red" and quotes local party officials. Donald Westerhausen (Vice Chair, St. Joseph County Democratic Party): "There's a majority of Democrats still in St. Joe County." Tony Hazen (St. Joseph County Commissioner, a Republican) quoted on Trump's record. The article makes no claims about urban/suburban/rural, Notre Dame, or union differences. | Local TV news; partisan quotes only. https://www.wndu.com/2024/11/01/red-blue-perspectives-st-joseph-berrien-counties-2024-election/ |
| WISH-TV, "Election data suggest shifting political landscape in Indiana" | Reports Trump won every Indiana county except Marion, Monroe, Lake, and St. Joseph in 2024 (per search summary). | https://wishtv.com/?p=1292118 (not fetched; verify). |
| Aggregator county totals (city-stats.com, via search summary) | 2024 presidential: Democratic 55,215 (about 50.0%) vs Republican 53,585 (about 48.5%) of 110,419 votes; 2020 Democratic margin about 5.9 points. | Third-party aggregator; **verify against the county clerk or Indiana Secretary of State before use.** Another site reported a different figure that did not fit; not used. |
| WNDU, 6 Nov 2020 (headline: "Republican candidates control all seats of St. Joseph County Board of Commissioners") | Republicans won all three commissioner seats in 2020 (WNDU noted it surprised some who view the county as more liberal, per search summary). | https://www.wndu.com/2020/11/06/republican-candidates-control-all-seats-of-st-joseph-county-board-of-commissioners/ (not fetched). |
| South Bend Voice, "What Does Electoral Victory Look Like? Visualizing Buttigieg's Win", 7 May 2015 | Precinct-level map of the 2015 Democratic mayoral primary; South Bend has 85 precincts; strongest Buttigieg precinct Sunnymede (over 96%). | Local outlet; primary only. https://southbendvoice.com/2015/05/07/what-does-electoral-victory-look-like-visualizing-mayor-pete-buttigiegs-win |
| Wikipedia "Mayoral elections in South Bend" (1999 entry, search summary) | A past Democratic primary split largely along East Side versus West Side lines. | Encyclopedia summary, historical only. |
| New America, "South Bend: Reinventing a 'Dying City'" | Contains no voting data. | Context only. |

**Not found despite searching:** any academic or journalistic study of township-by-township or precinct-by-precinct voting differences in St. Joseph County; any analysis of Notre Dame or student voting (campus precinct turnout; the Notre Dame student voter-engagement office or the county clerk may hold data); any analysis linking the Studebaker closure or union history to local voting. Search queries 6, 7, 11 and 14 targeted these. Suggested next steps for the main session: (1) compute neutral precinct/township tables from the county election board and Indiana Secretary of State results; (2) ask the South Bend Tribune and WVPE whether they have run data stories (not searched directly); (3) look for the Brookings, Pew, or Census-based urban-rural vote studies that include Indiana (not searched).

### D2. Precinct-level election datasets (identified, **not downloaded**)

All listed below are shapefile/CSV products; the owner said precinct shapefiles are not needed, so only URLs and sizes are recorded.

| Dataset | Years | Format | Size (Indiana file) | License | URL |
|---|---|---|---|---|---|
| VEST, "2016 Precinct-Level Election Results", Harvard Dataverse | 2016 general | ESRI shapefile (ZIP), state-by-state; Indiana file `in_2016.zip` (file ID 5117322) | 10,389,689 bytes (about 10.4 MB) | CC BY 4.0 | https://doi.org/10.7910/DVN/NH5S2I (dataset version 98, released 2026-10-03) |
| VEST, "2018 Precinct-Level Election Results" | 2018 general | `in_2018.zip` (file ID 5117325) | 10,839,968 bytes | CC BY 4.0 | https://doi.org/10.7910/DVN/UBKYRU (version 73) |
| VEST, "2020 Precinct-Level Election Results" | 2020 general | `in_2020.zip` (file ID 5143396), dataset has 54 files | 10,993,048 bytes | CC BY 4.0 | https://doi.org/10.7910/DVN/K7760H (version 49) |
| VEST, "2020 Precinct Shapefiles" (boundaries only) | 2020 | ESRI shapefile | not checked | not checked | https://doi.org/10.7910/DVN/XPW7T7 |
| University of Florida Election Lab data archive, Indiana | 2016, 2018, 2020, 2022, 2024 precinct-level results and boundary maps (VEST-sourced); a 2020 boundary map for St. Joseph County; locality results incl. "City of Mishakawa" (sic) 2023 | listed as results/boundary maps; format, size, license not shown on index page | not shown | not shown | https://election.lab.ufl.edu/data-archive/indiana/ ; 2024 page https://election.lab.ufl.edu/dataset/in-2024-precinct-level-election-results/ ; St. Joseph County map https://election.lab.ufl.edu/dataset/st-joseph-county/ |
| Redistricting Data Hub, Indiana | 2024 general precinct-level results (IN SOS and county officials, uploaded 9/21/26); 2024 results with boundaries (RDH, 10/23/26); 2024 results disaggregated to 2020 blocks; 2020 and 2018 and 2016 VEST precinct results; 2016 MGGG; 2016 and 2018 VEST data projected to 2020 VTDs; 2020 VTD boundaries (Census) | CSV and/or SHP | not shown | Account registration required to download; terms not shown per dataset | https://redistrictingdatahub.org/state/indiana/ |
| Harvard Dataverse "Indiana Data Files" | published 2011-06-14, "Indiana shapefile and election results" | not checked | not checked | not checked | https://doi.org/10.7910/DVN/WYXFW3 (identified in search only; not evaluated) |
| MIT Election Data and Science Lab (MEDSL) | not searched | | | | not searched |

Note: VEST precinct datasets are state-by-state ZIPs of about 10 MB for Indiana; there is no St. Joseph-only file. The Dataverse metadata API used to find sizes (`https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:10.7910/DVN/K7760H`) returns JSON only. Precinct-to-township assignment would still need a crosswalk.

### D3. Ecological-fallacy caveat

Area-level patterns (a township's income and its vote share) do not describe individual voters. Standard citations: Robinson, W.S. (1950), "Ecological Correlations and the Behavior of Individuals," *American Sociological Review* 15(3): 351-357, doi:10.2307/2087176; King, Gary (1997), *A Solution to the Ecological Inference Problem*, Princeton University Press, ISBN 978-0-691-01240-7. Definition as summarized from Wikipedia ("Ecological fallacy", fetched 2026-11-07): the error of drawing conclusions about individuals from findings about the groups they belong to. A primary or textbook source should replace the Wikipedia summary in the published guide.

---

## Reusable queries for other counties

Set `STATE_FIPS=18` (Indiana). `CO` = 3-digit county FIPS: St. Joseph = `141`, LaPorte = `091`, Elkhart = `039`. `GEOID_CO` = `05000US18${CO}`. `PLACE` = 5-digit place FIPS (St. Joseph: South Bend `71000`, Mishawaka `49932`). Verified for St. Joseph: South Bend = `16000US1871000`, Mishawaka = `16000US1849932`; LaPorte and Elkhart place codes are not verified (look them up with the geo search endpoint below).

1. **ACS profile tables for county and places (Census Reporter, no key, latest release only):**
   `curl -s "https://api.censusreporter.org/1.0/data/show/latest?table_ids=B01003,B01002,B01001,B03002,B05002,B25010,B15003,B21001,B18101,B19013,B19301,B17001,B19001,B25003,B25077,B25064,B25070,C24050,B23025&geo_ids=05000US18${CO},16000US18${PLACE}"`
   Replace `latest` with `acs2024_5yr` to pin the vintage. Use `curl`, not Python urllib (403). Release metadata is in the response `release` field.
2. **All townships (county subdivisions) in a county:** same URL with `geo_ids=060|05000US18${CO}` (the pipe means "children at summary level 060 of that parent"; URL-encode as `060%7C05000US18${CO}`). Names and geoids are in the response `geography` object.
3. **Find a place's geoid:** `https://api.censusreporter.org/1.0/geo/search?q=<place name>&sumlevs=160` (not tested in this session; confirm).
4. **Unemployment (BLS LAUS, no key, v1, max 10 years per request):**
   `curl -s -X POST -H "Content-type: application/json" -d '{"seriesid":["LAUCN18${CO}0000000003","LAUCN18${CO}0000000005","LAUCN18${CO}0000000006"],"startyear":"2000","endyear":"2009","annualaverage":true}' https://api.bls.gov/publicAPI/v1/timeseries/data/`
   Series suffix: 03 = unemployment rate, 04 = unemployed, 05 = employed, 06 = labor force. Repeat for 2010-2019 and 2020-2025. Use `period=="M13"` for annual averages.
5. **Jobs by industry (BLS QCEW, 2014 onward):** `curl -s -A "Mozilla/5.0 research" "https://data.bls.gov/cew/data/api/${YEAR}/a/area/18${CO}.csv"`. Keep rows with `own_code=5` and `agglvl_code=74` (private sectors), and `agglvl_code` 70/71 for ownership totals. The area code is the 5-digit county FIPS (18141 = St. Joseph).
6. **Census API (official, requires a free key):** `https://api.census.gov/data/2024/acs/acs5/profile?get=NAME,DP03_0062E&for=county:${CO}&in=state:18&key=YOUR_KEY`; townships `for=county%20subdivision:*&in=state:18%20county:${CO}`; places `for=place:${PLACE}&in=state:18`. Not run; would provide ACS 2010 comparison vintages (`/data/2010/acs/acs5/profile`).
7. **Precinct data:** Harvard Dataverse VEST DOIs listed in D2 contain all states; Indiana file is `in_{YEAR}.zip`. Metadata query: `https://dataverse.harvard.edu/api/search?q=Indiana%20precinct&subtree=electionscience&type=dataset`.
8. **Derived formulas used (ACS cell numbers; same for any county):**
   - Under 18 = B01001 cells 003-006 and 027-030 divided by B01001001; 65+ = cells 020-025 and 044-049.
   - Race/ethnicity = B03002 cells 003 (White NH), 004 (Black NH), 006 (Asian NH), 009 (two or more NH), 012 (Hispanic) divided by B03002001.
   - Foreign-born = B05002013 / B05002001. HS+ = 1 - (B15003 cells 002-016 / B15003001). Bachelor's+ = B15003 cells 022-025 / B15003001. Veteran = B21001002 / B21001001.
   - Disability = sum of "With a disability" cells in B18101 / B18101001.
   - Poverty = B17001002 / B17001001. Child poverty = sum of the six under-18 age cells below poverty (B17001 cells 004-009 male, 018-023 female; matched by name in the script) over under-18 total.
   - Income brackets (B19001): <$25k = cells 002-005; $25-50k = 006-010; $50-100k = 011-013; $100-150k = 014-015; $150k+ = 016-017.
   - Homeownership = B25003002 / B25003001. Rent-burdened = B25070 cells 007-010 divided by (B25070001 - B25070011).
   - Industry (C24050 totals): cells 002-014 divided by C24050001.
9. **Population history:** Wikipedia county/city articles quote decennial counts; the primary source for any county is the Census Bureau decennial tables (not pulled here).

---

## Gaps / not found

- **ACS ~2010 comparison (income, poverty, education, housing, industry): not obtained.** Reasons: Census API requires a key; Census Reporter has only the latest release; data.census.gov and QuickFacts blocked (403). Options: get a Census API key, or download the 2006-2010 ACS summary tables (a bulk download; not done).
- **Industry employment 2005-2010: not obtained.** QCEW API returns only 2014+. Older annual QCEW area files are bulk downloads (not downloaded). I did not check STATS Indiana (stats.indiana.edu) for a 2005-2010 sector series; "not searched".
- Inflation adjustment to a common year: not done.
- Township decennial population 1950-2020: not collected. Place-to-township crosswalk: not collected.
- Child poverty and disability by township come with large MOEs; not tabulated.
- Mishawaka 2010 non-Hispanic race table: not obtained.
- Verified employee counts for Beacon Health System / Trinity Health Michiana (Saint Joseph Health System), AM General (total), School Corporations, Honeywell: not found with dated authoritative sources. The 2024 South Bend ACFR statistical-section principal-employers table was not in the extracted text.
- Union density for St. Joseph County, Bendix/IUE local history, Michiana Area Labor Council: not found.
- RV industry role: not searched. EV battery plant: not searched specifically. Microsoft/Google data centers: not searched. Notre Dame growth milestones (enrollment, dates): not searched.
- Published analyses of local voting patterns by area, student vote, union history: essentially not found (see D1).
- MIT MEDSL, Brookings, Pew urban-rural analyses: not searched.
- ACFR narrative statement that the 2024 annual average unemployment was 2.7% "slightly higher than" Indiana's 2.9% is internally inconsistent and does not match BLS LAUS (4.7% for 2024); I did not use it.
- Web searches used: 15 of 20 (queries: largest employers; AWS New Carlisle; ACFR principal employers; Newsweek/Studebaker; UAW Local 5/AM General; voting patterns precinct; 2024 results by township; South Bend precinct turnout analysis; Notre Dame employees; Beacon Health employees; AWS status 2026; urban-rural partisan divide; unions/Labor Council). The 5 unused searches were deliberately held back.

---

## Sources

Census / BLS APIs and datasets (all queried 2026-11-07):
- Census Reporter API: https://api.censusreporter.org/1.0/data/show/acs2024_5yr (county, South Bend, Mishawaka: `geo_ids=05000US18141,16000US1871000,16000US1849932`; townships: `geo_ids=060|05000US18141`). Underlying data: U.S. Census Bureau ACS 2020-2024 5-year.
- BLS LAUS via Public Data API v1: https://api.bls.gov/publicAPI/v1/timeseries/data/ (series LAUCN181410000000003/05/06).
- BLS QCEW open data API: https://data.bls.gov/cew/data/api/{2014,2015,2019,2024}/a/area/18141.csv
- Hoosiers by the Numbers major employers: https://www.hoosierdata.in.gov/major_employers.asp?areaID=141
- Harvard Dataverse metadata API (VEST datasets): https://dataverse.harvard.edu/api/search?q=Indiana%20precinct&subtree=electionscience&type=dataset ; dataset metadata for doi:10.7910/DVN/K7760H, NH5S2I, UBKYRU.
- UF Election Lab Indiana archive: https://election.lab.ufl.edu/data-archive/indiana/
- Redistricting Data Hub Indiana: https://redistrictingdatahub.org/state/indiana/

Documents and pages:
- City of South Bend 2024 Annual Comprehensive Financial Report: https://docs.southbendin.gov/WebLink/0/edoc/407204/2024%20Annual%20Comprehensive%20Financial%20Report.pdf
- University of Notre Dame, Regional Economic Impact 2024: https://publicaffairs.nd.edu/assets/595413/economic_impact_2024.pdf
- UAW, "UAW members at AM General ratify strongest contract in decades", 26 Sep 2025: https://uaw.org/uaw-members-at-am-general-ratify-strongest-contract-in-decades/
- New America, "South Bend: Reinventing a 'Dying City'": https://www.newamerica.org/insights/automation-nation/south-bend-reinventing-a-dying-city/
- WNDU, 1 Nov 2024: https://www.wndu.com/2024/11/01/red-blue-perspectives-st-joseph-berrien-counties-2024-election/
- AP via KSAT, 25 Apr 2024, AWS $11 billion: https://www.ksat.com/tech/2024/04/25/amazon-cloud-computing-unit-plans-to-invest-11-billion-to-build-data-center-in-northern-indiana
- Black Ridge Research AWS Project Rainier profile (April 2026): https://blackridgeresearch.com/project-profiles/aws-project-rainier-new-carlisle-indiana-usa-data-center-supercluster-cost-contractors-timeline-latest-updates
- Data Center Dynamics: https://www.datacenterdynamics.com/en/news/aws-breaks-ground-on-11bn-data-center-campus-in-indiana
- UAW Region 2B Local 5 history: https://region2b.uaw.org/uaw-local-5/history (search result only)
- Wikipedia (secondary): St. Joseph County, Indiana; South Bend, Indiana; Mishawaka, Indiana; Studebaker; AM General; Ecological fallacy.
- Other search-result pages cited above (South Bend Voice, WISH-TV, WNDU 2020, city-stats.com aggregator) were not fetched.

### Files downloaded (saved under `C:\Users\nickb\local-gov-guide\sources\demographics\`; treated as data, never executed)

| File | Source URL | Size (bytes) |
|---|---|---|
| bls-laus/bls_2000.json | BLS API v1 POST, series LAUCN18141..., 2000-2009 | 33,837 |
| bls-laus/bls_2010.json | same, 2010-2019 | 33,846 |
| bls-laus/bls_2020.json | same, 2020-2025 | 21,117 |
| bls-qcew/qcew_2014.csv | https://data.bls.gov/cew/data/api/2014/a/area/18141.csv | 248,176 |
| bls-qcew/qcew_2015.csv | https://data.bls.gov/cew/data/api/2015/a/area/18141.csv | 248,180 |
| bls-qcew/qcew_2019.csv | https://data.bls.gov/cew/data/api/2019/a/area/18141.csv | 252,437 |
| bls-qcew/qcew_2024.csv | https://data.bls.gov/cew/data/api/2024/a/area/18141.csv | 250,710 |
| censusreporter/acs2024_5yr_cty.json | Census Reporter API, county + South Bend + Mishawaka, 19 tables | 69,908 |
| censusreporter/acs2024_5yr_twp.json | Census Reporter API, 13 townships, 19 tables | 213,027 |
| other/south-bend-2024-ACFR.pdf | https://docs.southbendin.gov/WebLink/0/edoc/407204/2024%20Annual%20Comprehensive%20Financial%20Report.pdf | 5,993,255 |
| other/notre-dame-economic-impact-2024.pdf | https://publicaffairs.nd.edu/assets/595413/economic_impact_2024.pdf | 4,007,832 |

(The two PDFs were saved by the fetch tool and copied into this folder; text was extracted with pdftotext only. The QCEW slices and Census Reporter JSON are small API responses. No executables or scripts were downloaded. Working scripts I wrote are in `C:\Users\nickb\local-gov-guide\research\tmp\` (pull and parse code), separate from the data.)
