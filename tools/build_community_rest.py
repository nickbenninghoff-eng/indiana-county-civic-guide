"""Build timeline.csv, employers.csv, research_on_voting.csv, indicators.csv (Indiana), gaps, corrections log.
Run after build_community_people.py (reads tools/_people_stats.json)."""
import csv, json, os

R = r"C:\Users\nickb\local-gov-guide"
ED = R + r"\data\editions\st-joseph"
IN = R + r"\data\indiana"
os.makedirs(IN, exist_ok=True)


def wcsv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            assert len(r) == len(header), (path, r)
            w.writerow(r)


# ------------------------------------------------------------------ timeline
T = [
 ("1852", "economic", "Studebaker begins making wagons in South Bend", "H.C. Studebaker begins making wagons and horse-drawn buggies in South Bend, later automobiles (City of South Bend 2024 ACFR narrative).", "secondary", "medium", "COM-007"),
 ("1850", "population", "South Bend population 1,652 (1850 census)", "Earliest South Bend count collected: 1,652 in 1850, 3,832 in 1860, 35,999 in 1900 and 104,193 in 1930 (decennial counts as tabulated in Wikipedia).", "secondary", "medium", "COM-005"),
 ("1865-05-22", "government", "City of South Bend incorporated", "South Bend was incorporated as a city on May 22, 1865; William G. George was elected its first mayor that year.", "secondary", "medium", "COM-019;COM-020;COM-021"),
 ("1865-06-05", "government", "First Common Council elected", "The first South Bend Common Council was elected on June 5, 1865 (Wikipedia, citing Howard's history of St. Joseph County).", "secondary", "medium", "COM-020"),
 ("1933", "economic", "Studebaker workers organized as AFL Local 18310", "Studebaker workers organized as AFL Local 18310, later UAW Local 5, per the UAW Region 2B history page (seen in a search summary only).", "secondary", "low", "COM-012"),
 ("1936-11-17", "economic", "Sit-down strike at Bendix Corporation, South Bend", "The UAW Region 2B history page describes a sit-down strike at Bendix on this date as the first sit-down strike in America. This is the union's characterization; a historian's source is needed before publication.", "secondary", "low", "COM-012"),
 ("1960", "population", "South Bend reaches its peak census population", "South Bend had 132,445 residents in the 1960 census, its highest count. By 2020 the city had 103,453 (about 22 percent fewer) while the county grew from 238,614 to 272,912 (about 14 percent more).", "computed", "high", "COM-005"),
 ("1960-09-02", "political", "Mayor Edward Voorde dies in office", "Mayor Edward F. Voorde died in office on September 2, 1960; Frank J. Bruggner became acting mayor and did not seek election in 1963. How Bruggner was selected was not confirmed.", "secondary", "medium", "COM-019;COM-021"),
 ("1963-12-20", "economic", "Studebaker ends production in South Bend", "Studebaker's South Bend plant ceased production on December 20, 1963 (last Avanti December 26); the engine block plant closed in 1964. Sources report about 7,000 local jobs affected, but plant employment figures are inconsistent across sources.", "secondary", "medium", "COM-016;COM-013")
 ,
 ("1967-11", "political", "Lloyd M. Allen re-elected mayor; last Republican elected mayor of South Bend", "Republican Lloyd M. Allen was re-elected mayor in 1967 with 58 percent. Every mayor elected since has been a Democrat.", "secondary", "medium", "COM-019;COM-021"),
 ("1971-11", "political", "Jerry Miller elected mayor; continuous Democratic control of the mayor's office begins", "Democrat Jerry Miller won the 1971 mayoral election, beginning continuous Democratic control of the office. He campaigned on a cabinet form of government and restructured the executive branch after taking office.", "secondary", "medium", "COM-019"),
 ("1979-11", "political", "Lowest South Bend mayoral turnout since 1925", "The 1979 mayoral general election drew 29,196 votes, the lowest since 1925 (Wikipedia, citing the South Bend Tribune).", "secondary", "medium", "COM-019"),
 ("1983-03", "economic", "AM General wins initial Humvee contract", "AM General won an initial $1.2 billion contract in March 1983 for 55,000 Humvees; the Mishawaka plant was built in 1984 and production began that fall. LTV Corp. bought AM General in 1983.", "secondary", "medium", "COM-017"),
 ("1987-11", "political", "Closest modern South Bend mayoral general election", "Joe Kernan defeated Carl Baxmeyer 53 percent to 47 percent (17,030 to 15,104) in 1987.", "secondary", "medium", "COM-019"),
 ("1997-01-03", "political", "Kernan leaves mayor's office for lieutenant governor; Luecke fills vacancy", "Mayor Joe Kernan resigned after being elected lieutenant governor in 1996; council member Steve Luecke was appointed unanimously by the council (single secondary source) and was then elected in 1999, 2003 and 2007.", "single_source", "medium", "COM-019;COM-021")
 ,
 ("1997", "economic", "Ball Band (Uniroyal) plant in Mishawaka closes", "The Ball Band (Uniroyal) plant in Mishawaka closed in 1997 after import competition (Wikipedia).", "secondary", "medium", "COM-018"),
 ("2009", "economic", "County unemployment rate reaches 11.4 percent annual average", "BLS LAUS annual-average unemployment for St. Joseph County was 11.4 percent in 2009 and 11.2 percent in 2010, the highest annual values in the 2000-2025 series.", "official", "high", "COM-003"),
 ("2011-01-21", "economic", "Newsweek lists South Bend among 'America's Dying Cities'", "Newsweek published its 'America's Dying Cities' list, on which South Bend appeared, on January 21, 2011 per New America; Notre Dame Magazine reportedly dates the list to 2010. The article itself was not obtained.", "secondary", "low", "COM-013")
 ,
 ("2011-02", "political", "Indiana House Democrats leave the chamber over right-to-work bill", "A group of 37 Democrats, led by Rep. B. Patrick Bauer of South Bend, left the Indiana House in February 2011 to block a right-to-work bill; they returned on March 28, 2011. Daily fines rose from $250 to $350 during the walkout.", "secondary", "medium", "COM-030")
 ,
 ("2012-01-01", "political", "Pete Buttigieg takes office as mayor of South Bend", "Buttigieg won the 2011 Democratic primary with 54.9 percent and the general election with 73.85 percent and took office on January 1, 2012. New America describes his election as widely cited as the start of a new era.", "secondary", "medium", "COM-013;COM-019")
 ,
 ("2012", "legal", "Police recordings dispute leads to litigation against the City of South Bend", "In 2012 the mayor demoted police chief Darryl Boykins amid a dispute over recorded calls. The city later settled suits with Boykins ($75,000) and with officers ($500,000 combined); on May 28, 2026 a federal judge ruled for the officers and ordered the recordings destroyed.", "secondary", "medium", "PPL-028;PPL-029;PPL-030;PPL-031;COM-030")
 ,
 ("2020-01-01", "political", "James Mueller takes office as mayor of South Bend", "Mueller, a Democrat and former chief of staff to Buttigieg, took office on January 1, 2020 after winning the 2019 election with 63.40 percent (official canvass: 9,406 to 5,429).", "official", "high", "COM-030")
 ,
 ("2021-12-30", "government", "County Council overrides commissioners' veto of redistricting plan", "The Democratic-majority County Council overrode the Republican-majority commissioners' veto of a Democratic redistricting plan on December 30, 2021 (WVPE, search listing only).", "secondary", "medium", "COM-022")
 ,
 ("2022", "legal", "Mediated settlement of county redistricting suit", "Democrats sued over the 2021 maps; a mediated settlement in early 2022 produced compromise maps, approved by an Elkhart County judge, at a cost of hundreds of thousands of dollars in legal fees (WVPE).", "secondary", "medium", "COM-023")
 ,
 ("2022-08", "government", "Republican caucus selects Carl Baxmeyer as commissioner", "A Republican caucus chose Carl Baxmeyer in August 2022 to fill the District 1 commissioner seat vacated by Andy Kostielney, who resigned; Baxmeyer was elected board president 2-1.", "secondary", "medium", "COM-024")
 ,
 ("2022-11-08", "political", "Republicans win a 5-4 majority on the County Council", "Republicans won a 5-4 majority on the nine-member County Council in November 2022; the council had been 6 Democrats and 3 Republicans. WNDU described it as the first Republican majority; that 'first' was not independently verified.", "secondary", "medium", "COM-023;COM-030")
 ,
 ("2023-02", "economic", "AM General wins JLTV A2 production contract", "AM General won a U.S. Army Joint Light Tactical Vehicle A2 production contract worth more than $8.66 billion in February 2023 (Wikipedia).", "secondary", "medium", "COM-017")
 ,
 ("2023-11-07", "political", "Democrats win all nine South Bend Common Council seats", "Democrats won all nine council seats in the 2023 municipal election. District 5 was decided 1,414 to 1,376 (38 votes) in a district that had elected Republicans since at least the early 1990s (WVPE).", "secondary", "high", "COM-031;COM-030")
 ,
 ("2024-01-20", "government", "Republican caucus selects Tony Hazen as District 3 commissioner", "Tony Hazen was the only candidate at the January 20, 2024 Republican caucus after Deb Fleming's retirement took effect January 31, 2024. He won the November 2024 election with 58.50 percent (22,491 votes).", "official", "high", "COM-025;COM-029;COM-030")
 ,
 ("2024-04-25", "economic", "Amazon Web Services announces data center investment near New Carlisle", "AWS announced an investment of about $11 billion for a data center campus near New Carlisle; the state said at least 1,000 jobs, and Gov. Holcomb called it the largest capital investment announcement in Indiana's history (AP). Construction reportedly began in September 2024 (third-party tracker; no official status found).", "secondary", "medium", "COM-014;COM-015")
 ,
 ("2024-11-05", "political", "Narrowest county row-office results in the 2024 general election", "Official 2024 results: Recorder decided by 81 votes (54,038 to 53,957) and Surveyor by 172 votes (54,375 to 54,203).", "official", "high", "COM-029;COM-030")
 ,
 ("2025-09-25", "economic", "UAW Local 5 members ratify new AM General contract", "About 400 UAW members at the Mishawaka complex ratified a contract with a 12 percent wage increase over three years, per the UAW. The figure is the bargaining unit, not total plant employment.", "official", "high", "COM-011")
 ,
 ("2026-04-22", "legal", "Judge rules commissioner district elections violate 'free and equal elections' clause", "ABC57 reported on April 22, 2026 that a judge ruled the county's district-based election of commissioners violates the Indiana Constitution. The report names no judge or court and says the ruling could be appealed; the November 2026 election used the district system. A related suit by the City of South Bend was filed in Marion County in February 2023; the link between the two is not confirmed.", "secondary", "medium", "COM-026;COM-032;COM-030")
 ,
 ("2026-11-03", "political", "Democrats win county offices on the November 2026 ballot (unofficial)", "Unofficial returns (county document dated 11/3/2026): Democrats won sheriff, prosecutor, commissioner District 1, clerk, auditor, assessor and council Districts A, B, C, E and H. The Board of Commissioners will be 2-1 Democratic and the County Council 7-2 Democratic from January 2027. WVPE describes the commissioner result as the first Democratic board majority since 2012; county results document a Republican majority each year from 2013 (2009-2012 composition not verified).", "unofficial", "medium", "COM-028;COM-027;COM-038;COM-030"),
 ("2020", "population", "County population 272,912; South Bend 103,453 (2020 census)", "St. Joseph County had 272,912 residents in the 2020 census; South Bend 103,453 and Mishawaka 51,063.", "secondary", "high", "COM-005"),
]
T.sort(key=lambda r: r[0])
wcsv(ED + r"\timeline.csv","date,category,title,description,status,confidence,source_ids".split(","), T)

# ------------------------------------------------------------------ employers
E = []
sel17 = "Ten largest employers listed in the City of South Bend 2017 ACFR, as quoted by Wikipedia"
for nm, sec, n in [("Beacon Health System (Memorial)", "Health care", 7088), ("University of Notre Dame", "Higher education", 6086),
                   ("South Bend Community School Corporation", "K-12 education", 3432), ("Indiana University South Bend", "Higher education", 1401),
                   ("St. Joseph County", "Local government", 1377), ("City of South Bend", "Local government", 1285),
                   ("Four Winds Casino", "Gaming and hospitality", 1200), ("AM General", "Vehicle manufacturing", 1200),
                   ("The South Bend Clinic", "Health care", 854), ("Press Ganey", "Not stated in source", 850)]:
    E.append([nm, sec, n, "2017", sel17, "secondary", "COM-008", "Wikipedia relays the ACFR table; verify against the 2017 ACFR itself. Employee-count definition not stated."])
sel24 = "Named as a largest employer in the narrative of the City of South Bend 2024 ACFR; no counts and no ranking stated"
for nm, sec in [("Beacon Health System", "Health care"), ("University of Notre Dame", "Higher education"), ("South Bend Community School Corporation", "K-12 education"),
                ("St. Joseph Health System", "Health care"), ("Indiana University - South Bend", "Higher education"), ("St. Joseph County", "Local government"),
                ("City of South Bend", "Local government"), ("AM General", "Vehicle manufacturing"), ("Honeywell International, Inc", "Manufacturing"),
                ("Press Ganey Associates, Inc.", "Not stated in source")]:
    E.append([nm, sec, "", "2024", sel24, "official", "COM-007", "Order is as printed in the ACFR but the ACFR does not say it is a ranking."])
E.append(["University of Notre Dame", "Higher education", 8340, "2023", "University's own count of faculty, staff, postdocs and graduate students in its Regional Economic Impact report (data mostly FY/CY 2023)", "single_source", "COM-009",
          "University-defined employee count; the report says more people work at Notre Dame than anywhere else in St. Joseph County."])
E.append(["AM General (UAW Local 5 bargaining unit only)", "Vehicle manufacturing", 400, "2025-09", "UAW press release on contract ratification", "single_source", "COM-011",
          "About 400 UAW members at the Mishawaka complex; this is the bargaining unit, not total plant employment."])
sel_h = "Rank order in the Data Axle-licensed Hoosiers by the Numbers directory; counts not shown"
for nm in ["Notre Dame Alumni Assn", "University of Notre Dame", "University-Notre Dame-Harper", "St Joseph County", "AM General Mfg Campus (Mishawaka)",
           "Honeywell Aerospace", "Performance Plus", "South Bend Tribune", "Central Blood Bank", "ITR Concession Co LLC (Granger)"]:
    E.append([nm, "Not stated in source", "", "2026", sel_h, "secondary", "COM-010", "Commercial directory; not a reliable ordering of employers. Data year not shown."])
wcsv(ED + r"\employers.csv", "name,sector,employees,as_of,selection_rule,status,source_ids,notes".split(","), E)

# ------------------------------------------------------------------ research on voting
V = [
 ("RV-001", "Kyle W. Bell", "What Does Electoral Victory Look Like? Visualizing Mayor Pete Buttigieg's Win", "The South Bend Voice", "2015-05-07", "South Bend (85 precincts; 6 council districts)", "2015 municipal primary (Democratic mayoral primary; city clerk race)",
  "Descriptive precinct- and district-level comparison of vote margins using public City of South Bend and county results; no statistical modeling.",
  "Buttigieg won 80 of 85 precincts and all six council districts in a 78-22 win over Henry Davis Jr.; Davis won four precincts in District 2 and one in District 6. The strongest precinct (Sunnymede, near IUSB) gave Buttigieg about 96 percent. The author interprets the result as broad support across neighborhoods with different socioeconomic profiles.",
  "One primary election; no demographic or income data linked to precincts; the interpretation is the author's, not a tested finding.", "https://southbendvoice.com/2015/05/07/what-does-electoral-victory-look-like-visualizing-mayor-pete-buttigiegs-win", "single_source"),
 ("RV-002", "Garrett Bergquist; Jason Ronimous", "Election data suggest shifting political landscape in Indiana", "WISH-TV (News 8)", "2024-11-21", "All 92 Indiana counties, including St. Joseph", "2024 presidential and governor general elections (some comparison with 2016)",
  "County-by-county review of presidential and governor results, presented in tables; official data source not named.",
  "St. Joseph was one of four counties (with Marion, Monroe and Lake) that Donald Trump did not carry in 2024: Harris 50.0 percent, Trump 48.5 percent. In the governor race, Jennifer McCormick took 49.8 percent in St. Joseph and Mike Braun 47.2 percent.",
  "Statewide coverage; the St. Joseph portion is a results table, not an analysis of why areas voted differently; no demographic comparison.", "https://wishtv.com/?p=1292118", "single_source"),
]
wcsv(ED + r"\research_on_voting.csv", "study_id,authors,title,outlet,date,geography,period,method,finding_summary,limits,url,status".split(","), V)

# ------------------------------------------------------------------ Indiana indicators.csv
ACS_COMMON = ("ACS 5-year. Official API (free key required): https://api.census.gov/data/{YEAR}/acs/acs5?get=NAME,{VARS}&for=county:{COUNTY_FIPS}&in=state:{STATE_FIPS}&key={KEY} ; "
              "places: for=place:{PLACE_FIPS}&in=state:{STATE_FIPS} ; townships: for=county%20subdivision:*&in=state:{STATE_FIPS}%20county:{COUNTY_FIPS} ; state: for=state:{STATE_FIPS} ; nation: for=us:1. "
              "Key-free (latest release only): curl -s \"https://api.censusreporter.org/1.0/data/show/latest?table_ids={TABLE}&geo_ids=05000US{STATE_FIPS}{COUNTY_FIPS},16000US{STATE_FIPS}{PLACE_FIPS},060|05000US{STATE_FIPS}{COUNTY_FIPS},04000US{STATE_FIPS},01000US\" "
              "(pipe form = all townships in the county). Earlier vintages: ACS 2006-2010 summary file sequence files at https://www2.census.gov/programs-surveys/acs/summary_file/2010/data/5_year_seq_by_state/{STATE_NAME}/All_Geographies_Not_Tracts_Block_Groups/ with the table-to-sequence lookup in documentation/5_year/user_tools/Sequence_Number_and_Table_Number_Lookup.txt. "
              "Variable pattern: <TABLE>_<cell>E estimate, <TABLE>_<cell>M margin of error.")
MOE_DIRECT = "Use the published 90% MOE."
MOE_SUM = "Sum: MOE = sqrt(sum of squared component MOEs)."
MOE_PROP = "Proportion p = N/D: MOE = sqrt(MOE_N^2 - p^2*MOE_D^2)/D (use + inside the root if negative), x100; Census ACS General Handbook ch. 8."
DISPLAY = "Show the estimate with its MOE. Flag CV>30% (CV = MOE/1.645/estimate) and do not use in headings or charts. ACS 5-year values are period estimates, not point-in-time counts."
DOLLAR = " Dollars are inflation-adjusted to the final year of the vintage (2010 dollars for 2006-2010; 2024 dollars for 2020-2024); inflate before comparing across vintages."
I = []


def ind(i, label, definition, universe, ds, tv, moe, disp=DISPLAY):
    I.append([i, label, definition, universe, ds, tv, moe, disp])


ind("pop_total", "Total population", "Total population (ACS 5-year estimate; decennial counts for earlier years).", "Total population", "ACS 5-year B01003; decennial census (PL 94-171 / SF1)", "B01003_001E, B01003_001M; decennial: P1_001N (2020 PL 94-171) / P001001 (2010 SF1) via https://api.census.gov/data/{YEAR}/dec/pl", "Published MOE (controlled totals have none).")
ind("pop_census_2020", 'Total population, 2020 Census count', 'Total resident population counted in the 2020 Decennial Census (redistricting file table P1). A count with no sampling margin of error; ACS pop_total is a period estimate and can differ.', "Total population", "2020 Decennial Census, PL 94-171 Redistricting Data", 'P1_001N (PL 94-171 P0010001); https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171/Indiana/in2020.pl.zip', 'No MOE (complete count; differential-privacy noise is not published as a margin).', "Show as 'Census count' with vintage 2020; do not compare to ACS estimates without noting the difference. Counts for school districts cover the whole district, which can extend outside the county.", "Show as 'Census count' with vintage 2020; do not compare to ACS estimates without noting the difference. Counts for school districts cover the whole district, which can extend outside the county.")
ind("median_age", "Median age", "Median age of the total population.", "Total population", "ACS 5-year B01002", "B01002_001E, B01002_001M", MOE_DIRECT)
rl = [("race_white_nh_pct", "Not Hispanic or Latino: White alone", 3), ("race_black_nh_pct", "Not Hispanic or Latino: Black or African American alone", 4),
      ("race_aian_nh_pct", "Not Hispanic or Latino: American Indian and Alaska Native alone", 5), ("race_asian_nh_pct", "Not Hispanic or Latino: Asian alone", 6),
      ("race_nhpi_nh_pct", "Not Hispanic or Latino: Native Hawaiian and Other Pacific Islander alone", 7), ("race_other_nh_pct", "Not Hispanic or Latino: Some other race alone", 8),
      ("race_two_or_more_nh_pct", "Not Hispanic or Latino: Two or more races", 9), ("race_hispanic_pct", "Hispanic or Latino (of any race)", 12)]
for i, lab, n in rl:
    ind(i, lab + " (percent of total population)", "Census category label used verbatim: '%s'. Share of total population." % lab, "Total population", "ACS 5-year B03002",
        "B03002_%03dE / B03002_001E (MOE per variable _M)" % n, MOE_PROP, DISPLAY + " Use the Census category label verbatim. 2020 'two or more races' is partly affected by Census 2020 race-processing changes.")
ind("foreign_born_pct", "Foreign-born population (percent)", "Foreign-born share of the total population.", "Total population", "ACS 5-year B05002", "B05002_013E / B05002_001E", MOE_PROP)
ind("bachelors_plus_pct", "Bachelor's degree or higher (percent)", "Bachelor's, master's, professional or doctorate degree share of the population 25 and over.", "Population 25 years and over", "ACS 5-year B15003 (2012+ vintages) or B15002 (2006-2010 vintage)",
    "B15003_022E..025E / B15003_001E; for the 2006-2010 vintage use B15002_015E..018E and B15002_032E..035E / B15002_001E", MOE_SUM + " " + MOE_PROP)
ind("median_hh_income", "Median household income", "Median household income in the past 12 months.", "Households", "ACS 5-year B19013", "B19013_001E, B19013_001M", MOE_DIRECT, DISPLAY + DOLLAR)
ind("per_capita_income", "Per-capita income", "Per capita income in the past 12 months.", "Total population", "ACS 5-year B19301", "B19301_001E, B19301_001M", MOE_DIRECT, DISPLAY + DOLLAR)
ind("poverty_pct", "Persons below the poverty level (percent)", "Share of persons for whom poverty status is determined who are below the poverty level.", "Population for whom poverty status is determined", "ACS 5-year B17001", "B17001_002E / B17001_001E", MOE_PROP)
ind("child_poverty_pct", "Children under 18 below the poverty level (percent)", "Under-18 persons below poverty divided by under-18 persons with poverty status determined.", "Persons under 18 for whom poverty status is determined", "ACS 5-year B17001",
    "sum B17001_004E..009E and _018E..023E (below poverty, under 18) / (that sum + B17001_033E..038E and _047E..052E (at or above poverty, under 18))", MOE_SUM + " " + MOE_PROP)
ind("owner_occupied_pct", "Owner-occupied housing units (percent of occupied units)", "Homeownership rate.", "Occupied housing units", "ACS 5-year B25003", "B25003_002E / B25003_001E", MOE_PROP)
ind("median_home_value", "Median home value", "Median value of owner-occupied housing units.", "Owner-occupied housing units", "ACS 5-year B25077", "B25077_001E, B25077_001M", MOE_DIRECT, DISPLAY + DOLLAR)
ind("median_gross_rent", "Median gross rent", "Median gross rent of renter-occupied units paying cash rent.", "Renter-occupied housing units paying cash rent", "ACS 5-year B25064", "B25064_001E, B25064_001M", MOE_DIRECT, DISPLAY + DOLLAR)
ind("rent_burdened_pct", "Renter households paying 30 percent or more of income on rent (percent)", "Rent-burdened share of renter households with computed rent burden.", "Renter-occupied units with gross rent as % of income computed", "ACS 5-year B25070",
    "sum B25070_007E..010E / (B25070_001E - B25070_011E)", MOE_SUM + " " + MOE_PROP)
ind("unemployment_rate", "Unemployment rate (annual average)", "Annual-average unemployment rate, not seasonally adjusted.", "Civilian labor force", "BLS Local Area Unemployment Statistics",
    "POST https://api.bls.gov/publicAPI/v1/timeseries/data/ with seriesid LAUCN{STATE_FIPS}{COUNTY_FIPS}0000000003 (county), LAUCT{STATE_FIPS}{PLACE_FIPS}00000003 (city, where published), LAUST{STATE_FIPS}0000000000003 (state), LNU04000000 (U.S.); annualaverage=true; keep period M13; v1 allows 10 years per request. Suffix 03=rate, 04=unemployed, 05=employed, 06=labor force.",
    "LAUS provides no MOE; estimates are model-based and revised annually.", "Show year and revision caveat; city series exist only for larger places.")
for lab, iid, n in zip(["Agriculture, forestry, fishing and hunting, and mining", "Construction", "Manufacturing", "Wholesale trade", "Retail trade", "Transportation and warehousing, and utilities", "Information",
                        "Finance and insurance, and real estate, and rental and leasing", "Professional, scientific, and management, and administrative, and waste management services",
                        "Educational services, and health care and social assistance", "Arts, entertainment, and recreation, and accommodation and food services", "Other services, except public administration", "Public administration"],
                       ["agri_mining", "construction", "manufacturing", "wholesale", "retail", "transport_utilities", "information", "finance_real_estate", "professional_admin", "education_health", "arts_food_accom", "other_services", "public_admin"], range(2, 15)):
    ind("emp_ind_%s_pct" % iid, "Employed residents in: " + lab + " (percent)", "Share of employed civilians 16+ (by residence) working in this ACS industry group.", "Employed civilian population 16 years and over", "ACS 5-year C24050",
        "C24050_%03dE / C24050_001E" % n, MOE_PROP, DISPLAY + " Counts residents wherever they work; QCEW (qcew_jobs_*) counts jobs located in the county.")
ind("emp_ind_employed_total", "Employed civilians 16 and over (count)", "Denominator for emp_ind_* percentages.", "Employed civilian population 16 years and over", "ACS 5-year C24050", "C24050_001E, C24050_001M", MOE_DIRECT)
QD = ("Jobs located in the county (not residents). Query: for YEAR>=2014 GET https://data.bls.gov/cew/data/api/{YEAR}/a/area/{STATE_FIPS}{COUNTY_FIPS}.csv (send a browser-style User-Agent); for earlier years open "
      "https://data.bls.gov/cew/data/files/{YEAR}/csv/{YEAR}_annual_by_area.zip using HTTP range requests and read the one member whose name contains the 5-digit area code (tools/fetch_qcew_county.py). "
      "Filters on the CSV: ")
ind("qcew_jobs_all_ownerships", "Jobs in the county, all ownerships", "Annual average employment, total covered, all establishment sizes.", "Covered employment", "BLS QCEW annual averages", QD + "own_code=0, agglvl_code=70; field annual_avg_emplvl", "No MOE (administrative census of covered employment).", "Show year; disclosure-suppressed cells are blank.")
ind("qcew_jobs_private", "Jobs in the county, private sector", "Annual average employment, private ownership total.", "Covered employment", "BLS QCEW annual averages", QD + "own_code=5, industry_code=10, agglvl_code=71", "No MOE.", "Show year.")
for k, nm in [("federal_gov", "federal government (own_code=1)"), ("state_gov", "state government (own_code=2)"), ("local_gov", "local government incl. public schools (own_code=3)")]:
    ind("qcew_jobs_" + k, "Jobs in the county, " + nm.split(" (")[0], "Annual average employment, " + nm + ".", "Covered employment", "BLS QCEW annual averages", QD + nm.split("(")[1].rstrip(")") + ", industry_code=10, agglvl_code=71", "No MOE.", "Show year.")
for code, nm in {"11": "Agriculture, forestry, fishing and hunting", "21": "Mining, quarrying, and oil and gas extraction", "22": "Utilities", "23": "Construction", "31-33": "Manufacturing", "42": "Wholesale trade", "44-45": "Retail trade", "48-49": "Transportation and warehousing", "51": "Information", "52": "Finance and insurance", "53": "Real estate and rental and leasing", "54": "Professional, scientific, and technical services", "55": "Management of companies and enterprises", "56": "Administrative and support and waste management", "61": "Educational services", "62": "Health care and social assistance", "71": "Arts, entertainment, and recreation", "72": "Accommodation and food services", "81": "Other services (except public administration)"}.items():
    ind("qcew_jobs_naics_" + code.replace("-", "_"), "Jobs in the county, private, NAICS %s %s" % (code, nm), "Annual average employment, private ownership, NAICS 2-digit sector.", "Covered employment", "BLS QCEW annual averages",
        QD + "own_code=5, agglvl_code=74, industry_code=%s" % code, "No MOE.", "Show year; NAICS revisions (2002, 2007, 2012, 2017) limit comparability; disclosure-suppressed cells are blank.")
def ds(r):
    if r[0] == "pop_total":
        return r[4] + ". " + ACS_COMMON.replace("{TABLE}", "B01003")
    if r[4].startswith("ACS 5-year"):
        return r[4] + ". Query pattern: same as the pop_total row, substituting the table and variables in table_variable."
    return r[4]


wcsv(IN + r"\indicators.csv", "indicator_id,label,definition,universe,source_dataset,table_variable,moe_rule,display_rule".split(","),
     [[r[0], r[1], r[2], r[3], ds(r), r[5], r[6], r[7]] for r in I])

print(len(T), "timeline;", len(E), "employers;", len(V), "voting;", len(I), "indicators")
