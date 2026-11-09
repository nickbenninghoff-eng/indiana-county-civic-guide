"""Build the community/people CSVs for the St. Joseph edition (and Indiana-wide indicators.csv).
Run: python -P -E tools/build_community_people.py   (images.csv needs site/images downloads + commons meta.json)"""
import csv, json, os, re, sys, collections

R = r"C:\Users\nickb\local-gov-guide"
ED = R + r"\data\editions\st-joseph"
IN = R + r"\data\indiana"
META = sys.argv[1] if len(sys.argv) > 1 else None   # commons meta.json
os.makedirs(ED, exist_ok=True)
os.makedirs(IN, exist_ok=True)


def wcsv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            assert len(r) == len(header), (path, r)
            w.writerow(r)


def count_sent(s):
    for ab in ("U.S.", "St.", "Jr.", "Sen.", "Rep.", "Gov.", "Dr.", "Mr.", "Mrs.", "J."):
        s = s.replace(ab, ab.replace(".", "~"))
    return len([x for x in re.split(r"(?<=[.!?])\s+(?=[A-Z'])", s.strip()) if x])


ACC = "2026-11-07"
# ------------------------------------------------------------------ sources
COM = [
 ("COM-001", "https://api.censusreporter.org/1.0/data/show/acs2024_5yr", "ACS 2020-2024 5-year tables B01002 B01003 B03002 B05002 B15003 B17001 B19013 B19301 B25003 B25064 B25070 B25077 C24050 (Census Reporter API); local copies in sources/demographics/censusreporter/", "U.S. Census Bureau via Census Reporter", "dataset", "County, South Bend, Mishawaka, 13 townships, Indiana, U.S.; estimates and 90% MOEs"),
 ("COM-002", "https://www2.census.gov/programs-surveys/acs/summary_file/2010/data/5_year_seq_by_state/", "ACS 2006-2010 5-year Summary File (sequence files 10,11,13,17,40,44,53,59,75,95,98,99 for Indiana and United States; geography files g20105in.csv, g20105us.csv)", "U.S. Census Bureau", "dataset", "Downloaded to sources/demographics/acs2010/. Table-to-sequence lookup: Sequence_Number_and_Table_Number_Lookup.txt. Dollars are 2010 inflation-adjusted."),
 ("COM-003", "https://api.bls.gov/publicAPI/v1/timeseries/data/", "BLS Local Area Unemployment Statistics (LAUS) annual averages: LAUCN181410000000003 (county), LAUCT187100000000003 (South Bend), LAUCT184993200000003 (Mishawaka), LAUST180000000000003 (Indiana), LNU04000000 (U.S.)", "U.S. Bureau of Labor Statistics", "dataset", "Saved in sources/demographics/bls-laus/. Period M13 = annual average, not seasonally adjusted."),
 ("COM-004", "https://data.bls.gov/cew/data/files/{YEAR}/csv/{YEAR}_annual_by_area.zip ; https://data.bls.gov/cew/data/api/{YEAR}/a/area/18141.csv", "BLS Quarterly Census of Employment and Wages (QCEW) annual averages, St. Joseph County (area 18141), 2001-2025", "U.S. Bureau of Labor Statistics", "dataset", "2001-2013 extracted from the bulk annual-by-area zips with HTTP range requests (tools/fetch_qcew_county.py); 2014+ from the open-data API. Saved in sources/demographics/bls-qcew/."),
 ("COM-005", "https://en.wikipedia.org/wiki/St._Joseph_County,_Indiana ; https://en.wikipedia.org/wiki/South_Bend,_Indiana ; https://en.wikipedia.org/wiki/Mishawaka,_Indiana", "Decennial population tables (Wikipedia, citing U.S. Census Bureau)", "Wikipedia", "secondary", "Secondary; re-pull from census.gov before publication (per research/10 A1)."),
 ("COM-006", "https://en.wikipedia.org/wiki/St._Joseph_County,_Indiana ; https://en.wikipedia.org/wiki/South_Bend,_Indiana", "2010 and 2020 race/ethnicity tables derived from Census PL 94-171 (Wikipedia)", "Wikipedia", "secondary", "Secondary."),
 ("COM-007", "https://docs.southbendin.gov/WebLink/0/edoc/407204/2024%20Annual%20Comprehensive%20Financial%20Report.pdf", "City of South Bend Annual Comprehensive Financial Report, fiscal year ended 12/31/2024 (demographic and economic narrative)", "City of South Bend", "primary", "Local copy sources/demographics/other/south-bend-2024-ACFR.pdf. Narrative lists largest employers without counts; the principal-employers statistical table was not in the text extraction."),
 ("COM-008", "https://en.wikipedia.org/wiki/South_Bend,_Indiana", "Top-10 employers table quoting the City of South Bend 2017 ACFR (Wikipedia)", "Wikipedia", "secondary", "Check against the 2017 ACFR itself."),
 ("COM-009", "https://publicaffairs.nd.edu/assets/595413/economic_impact_2024.pdf", "University of Notre Dame, Regional Economic Impact (PDF created 2024-10-24)", "University of Notre Dame", "primary", "University's own figure and definition of employee. Local copy sources/demographics/other/notre-dame-economic-impact-2024.pdf."),
 ("COM-010", "https://www.hoosierdata.in.gov/major_employers.asp?areaID=141", "Hoosiers by the Numbers: Major Employers, St. Joseph County (copyright 2026; licensed Data Axle)", "Indiana Business Research Center / Indiana Department of Workforce Development", "secondary", "Commercial-directory ranking; no counts or data year shown."),
 ("COM-011", "https://uaw.org/uaw-members-at-am-general-ratify-strongest-contract-in-decades/", "UAW members at AM General ratify strongest contract in decades (press release, 2025-09-26)", "UAW", "primary", "Union's own statement; about 400 UAW members at the Mishawaka complex."),
 ("COM-012", "https://region2b.uaw.org/uaw-local-5/history", "UAW Region 2B, Local 5 history", "UAW Region 2B", "primary", "Seen only in a search summary; page not fetched. A historian's source is needed for the 1936 sit-down strike claim."),
 ("COM-013", "https://www.newamerica.org/insights/automation-nation/south-bend-reinventing-a-dying-city/", "South Bend: Reinventing a 'Dying City'", "New America", "secondary", "Cites NPR (28 Jun 2012) for 1963 job losses and Newsweek (21 Jan 2011)."),
 ("COM-014", "https://www.ksat.com/tech/2024/04/25/amazon-cloud-computing-unit-plans-to-invest-11-billion-to-build-data-center-in-northern-indiana", "Amazon cloud computing unit plans to invest $11 billion to build data center in northern Indiana", "Associated Press via KSAT", "news", ""),
 ("COM-015", "https://blackridgeresearch.com/project-profiles/aws-project-rainier-new-carlisle-indiana-usa-data-center-supercluster-cost-contractors-timeline-latest-updates", "AWS Project Rainier, New Carlisle, Indiana profile (April 2026)", "Black Ridge Research", "secondary", "Third-party tracker; building counts conflict across trackers; no official AWS or IEDC status found."),
 ("COM-016", "https://en.wikipedia.org/wiki/Studebaker", "Studebaker (Wikipedia)", "Wikipedia", "secondary", "Cites period sources for the 20 Dec 1963 South Bend production end."),
 ("COM-017", "https://en.wikipedia.org/wiki/AM_General", "AM General (Wikipedia)", "Wikipedia", "secondary", ""),
 ("COM-018", "https://en.wikipedia.org/wiki/Mishawaka,_Indiana", "Mishawaka, Indiana (Wikipedia)", "Wikipedia", "secondary", ""),
 ("COM-019", "https://en.wikipedia.org/wiki/Mayoral_elections_in_South_Bend,_Indiana", "Mayoral elections in South Bend, Indiana (Wikipedia)", "Wikipedia", "secondary", "Cites Indiana Election Division and newspapers; official canvass figures in the fact-check report supersede vote counts."),
 ("COM-020", "https://en.wikipedia.org/wiki/South_Bend_Common_Council", "South Bend Common Council (Wikipedia; citing Howard's history of St. Joseph County)", "Wikipedia", "secondary", ""),
 ("COM-021", "https://en.wikipedia.org/wiki/List_of_mayors_of_South_Bend,_Indiana", "List of mayors of South Bend, Indiana (Wikipedia)", "Wikipedia", "secondary", "Page flags internal inconsistencies (Miller, Longley, Fogarty)."),
 ("COM-022", "https://www.wvpe.org/indiana-news/2021-12-30/st-joseph-county-council-overrides-commissioners-veto-of-democratic-redistricting-plan", "St. Joseph County Council overrides commissioners' veto of Democratic redistricting plan (2021-12-30)", "WVPE", "news", "Seen as a search listing only."),
 ("COM-023", "https://www.wvpe.org/wvpe-news/2022-11-09/republicans-may-win-st-joseph-county-council-majority-flipping-body-from-democrats", "Republicans may win St. Joseph County Council majority (2022-11-09)", "WVPE", "news", "Also source for the mediated redistricting settlement."),
 ("COM-024", "https://www.wvpe.org/wvpe-news/2022-08-30/st-joseph-county-commissioners-pick-newcomer-carl-baxmeyer-as-president", "St. Joseph County commissioners pick newcomer Carl Baxmeyer as president (2022-08-30)", "WVPE", "news", ""),
 ("COM-025", "", "WVPE reports 2024-01-12 and 2023-11-22 on Fleming's retirement and the Jan 20, 2024 Republican caucus selecting Tony Hazen (as read in planning/fact-check-report.md)", "WVPE", "news", "URL not retained in the research notes; the fact-check report read the items as search results."),
 ("COM-026", "https://www.abc57.com/news/judge-rules-st-joseph-county-election-system-violates-indiana-constitution", "Judge rules St. Joseph County election system violates Indiana Constitution (2026-04-22)", "ABC57", "news", "Names no judge or court; says the ruling could still be appealed."),
 ("COM-027", "https://www.953mnc.com/2026/11/04/democrats-sweep-major-st-joseph-county-races-winning-sheriff-prosecutor-commissioner-seats/", "2026 general election results article (2026-11-04)", "95.3 MNC", "news", "Unofficial as of 2026-11-04; the headline wording is not reproduced in the data. County figures are from county document 73081."),
 ("COM-028", "https://www.sjcindiana.gov/DocumentCenter/View/73081", "St. Joseph County 2026 general election results, unofficial 11/3/2026 9:07:47 PM", "St. Joseph County Election Board", "primary", "Read in the fact-check report; unofficial."),
 ("COM-029", "https://www.sjcindiana.gov/DocumentCenter/View/64951", "St. Joseph County 2024 general election results (official)", "St. Joseph County Election Board", "primary", "Read in the fact-check report (OCR)."),
 ("COM-030", "planning/fact-check-report.md", "Fact-check report: St. Joseph County civic guide research files (2026-11-07)", "Project fact-check pass", "derived", "Corrections applied; see _corrections_applied_community_people.md."),
 ("COM-031", "https://www.wvpe.org/wvpe-news/2023-11-07/democrats-celebrate-big-election-day-wins-in-south-bend-mishawaka-city-races", "Democrats celebrate big Election Day wins in South Bend, Mishawaka city races (2023-11-07)", "WVPE", "news", ""),
 ("COM-032", "https://www.953mnc.com/?p=232257", "City of South Bend (and Warren & Iris Outlaw) v. Indiana Election Commission, filed Feb 2023 (95.3 MNC, 2023-02-11)", "95.3 MNC", "news", "Per fact-check: filed in Marion County; link to the April 2026 ruling is inferred, not confirmed."),
 ("COM-033", "https://www.wvpe.org/wvpe-news/2026-05-28/judge-rules-for-officers-in-south-bend-police-tapes-case", "Judge rules for officers in South Bend Police Tapes case (2026-05-28)", "WVPE", "news", ""),
 ("COM-034", "https://www.wndu.com/2024/11/01/red-blue-perspectives-st-joseph-berrien-counties-2024-election/", "Red and Blue Perspectives: St. Joseph and Berrien counties on 2024 election (2024-11-01)", "WNDU", "news", "Partisan quotes only; not an analysis (not used in research_on_voting.csv)."),
 ("COM-035", "https://wishtv.com/?p=1292118", "Election data suggest shifting political landscape in Indiana (2024-11-21; updated 2024-11-22)", "WISH-TV", "news", "Fetched 2026-11-07."),
 ("COM-036", "https://southbendvoice.com/2015/05/07/what-does-electoral-victory-look-like-visualizing-mayor-pete-buttigiegs-win", "What does electoral victory look like? Visualizing Mayor Pete Buttigieg's win (2015-05-07)", "The South Bend Voice", "news", "Author Kyle W. Bell; fetched 2026-11-07."),
 ("COM-037", "https://www.wndu.com/2020/11/06/republican-candidates-control-all-seats-of-st-joseph-county-board-of-commissioners/", "Republican candidates control all seats of St. Joseph County Board of Commissioners (2020-11-06)", "WNDU", "news", "Seen as a search listing only."),
 ("COM-038", "https://www.wvpe.org/wvpe-news/2026-01-29/redman-hopes-to-challenge-baxmeyer-for-commissioner-seat", "Redman hopes to challenge Baxmeyer for commissioner seat (2026-01-29)", "WVPE", "news", "Source of 'first majority since 2012' wording."),
]
PPL = [
 ("PPL-001", "https://en.wikipedia.org/wiki/Schuyler_Colfax", "Schuyler Colfax", "Wikipedia", "secondary", ""),
 ("PPL-002", "https://en.wikipedia.org/wiki/List_of_mayors_of_South_Bend,_Indiana", "List of mayors of South Bend, Indiana", "Wikipedia", "secondary", "Flags internal inconsistencies."),
 ("PPL-003", "https://en.wikipedia.org/wiki/John_Brademas", "John Brademas", "Wikipedia", "secondary", ""),
 ("PPL-004", "https://en.wikipedia.org/wiki/Tim_Roemer", "Tim Roemer", "Wikipedia", "secondary", ""),
 ("PPL-005", "https://en.wikipedia.org/wiki/Joe_Kernan_(politician)", "Joe Kernan (politician)", "Wikipedia", "secondary", "Governor and other dates match the standard record (fact-check, knowledge-only); cite an official source before publication."),
 ("PPL-006", "https://en.wikipedia.org/wiki/Stephen_Luecke", "Stephen Luecke", "Wikipedia", "secondary", ""),
 ("PPL-007", "https://en.wikipedia.org/wiki/Pete_Buttigieg", "Pete Buttigieg", "Wikipedia", "secondary", ""),
 ("PPL-008", "https://en.wikipedia.org/wiki/Joe_Donnelly", "Joe Donnelly", "Wikipedia", "secondary", ""),
 ("PPL-009", "https://en.wikipedia.org/wiki/Jackie_Walorski", "Jackie Walorski", "Wikipedia", "secondary", ""),
 ("PPL-010", "https://en.wikipedia.org/wiki/B._Patrick_Bauer", "B. Patrick Bauer", "Wikipedia", "secondary", "Speaker dates unverified (fact-check)."),
 ("PPL-011", "https://en.wikipedia.org/wiki/Maureen_Bauer", "Maureen Bauer", "Wikipedia", "secondary", "Gives two start dates (Nov 4 and Nov 16, 2020)."),
 ("PPL-012", "https://en.wikipedia.org/wiki/Michael_Dvorak", "Michael Dvorak", "Wikipedia", "secondary", ""),
 ("PPL-013", "https://en.wikipedia.org/wiki/Ryan_Dvorak", "Ryan Dvorak", "Wikipedia", "secondary", ""),
 ("PPL-014", "https://en.wikipedia.org/wiki/Craig_Fry", "Craig Fry", "Wikipedia", "secondary", "Sparse."),
 ("PPL-015", "https://en.wikipedia.org/wiki/David_Niezgodski", "David Niezgodski", "Wikipedia", "secondary", ""),
 ("PPL-016", "https://en.wikipedia.org/wiki/Ryan_Mishler", "Ryan Mishler", "Wikipedia", "secondary", ""),
 ("PPL-017", "https://wsbt.com/news/local/mishawakas-longest-serving-mayor-dies-at-age-84", "Mishawaka's longest-serving mayor dies at age 84", "WSBT", "news", ""),
 ("PPL-018", "https://www.abc57.com/news/former-mishawaka-mayor-robert-c-beutter-dies", "Former Mishawaka mayor Robert C. Beutter dies", "ABC57", "news", "Seen as a search listing only; gives 1982 start, which the fact-check rejects."),
 ("PPL-019", "https://journalreview.com/stories/cracking-the-mayoral-glass-ceiling,245697", "Cracking the mayoral glass ceiling", "Journal Review", "news", "Search result only; not opened."),
 ("PPL-020", "https://en.wikipedia.org/wiki/Mishawaka,_Indiana", "Mishawaka, Indiana", "Wikipedia", "secondary", ""),
 ("PPL-021", "https://www.yahoo.com/news/black-history-month-j-chester-110429823.html", "Black History Month: J. Chester Allen (South Bend Tribune via Yahoo)", "South Bend Tribune", "news", "Single article; 'first on Common Council' wording removed per fact-check."),
 ("PPL-022", "https://docs.southbendin.gov/WebLink/0/doc/38214/Page2.aspx", "South Bend 2003 city resolution naming Eugenia Braboy", "City of South Bend", "primary", "Seen only in a search summary."),
 ("PPL-023", "https://www.wvpe.org/commentary/2019-03-07/women-making-history-charlotte-pfeifer", "Women making history: Charlotte Pfeifer", "WVPE", "news", "Search summary only; first name conflicts across sources."),
 ("PPL-024", "https://southbendin.gov/official/sherry-bolden-simpson/", "Sherry Bolden-Simpson (official page)", "City of South Bend", "primary", "Self-described 'firsts'."),
 ("PPL-025", "https://en.wikipedia.org/wiki/Mayoral_elections_in_South_Bend,_Indiana", "Mayoral elections in South Bend, Indiana", "Wikipedia", "secondary", "Source for 1963-1971 narrative, Janet Allen."),
 ("PPL-026", "https://en.wikipedia.org/wiki/South_Bend_Common_Council", "South Bend Common Council", "Wikipedia", "secondary", ""),
 ("PPL-027", "https://en.wikipedia.org/wiki/Indiana%27s_2nd_congressional_district", "Indiana's 2nd congressional district", "Wikipedia", "secondary", "Source for Rudy Yakym succeeding Jackie Walorski."),
 ("PPL-028", "https://abc57.com/news/city-settles-with-plaintiffs-in-south-bend-police-tape-scandal", "City settles with plaintiffs in South Bend police tape scandal", "ABC57", "news", ""),
 ("PPL-029", "https://wowo.com/south-bend-settles-2-police-wiretapping-lawsuits/", "South Bend settles 2 police wiretapping lawsuits", "WOWO", "news", ""),
 ("PPL-030", "https://theindianalawyer.com/?p=124892", "South Bend council urged to stop seeking police recordings", "The Indiana Lawyer", "news", "Reports the four officers shared a $500,000 payment."),
 ("PPL-031", "https://www.wvpe.org/wvpe-news/2026-05-28/judge-rules-for-officers-in-south-bend-police-tapes-case", "Judge rules for officers in South Bend Police Tapes Case (2026-05-28)", "WVPE", "news", ""),
 ("PPL-032", "https://www.wndu.com/2026/06/02/officer-recorded-south-bend-police-tapes-speaks-out-after-judge-rules-recordings-were-illegal/", "Officer recorded on South Bend police tapes speaks out after judge rules recordings were illegal (2026-06-02)", "WNDU", "news", "Reports the Common Council considering an appeal."),
 ("PPL-033", "https://www.wvpe.org/wvpe-news/2024-04-18/sen-david-niezgodski-paid-former-employee-to-drop-sexual-harassment-claims-report-finds", "Sen. David Niezgodski paid former employee to drop sexual harassment claims, report finds (2024-04-18)", "WVPE (reporting IndyStar)", "news", "Used only in notes, attributed; not an official finding."),
 ("PPL-034", "planning/fact-check-report.md", "Fact-check report: St. Joseph County civic guide research files (2026-11-07)", "Project fact-check pass", "derived", ""),
 ("PPL-035", "https://commons.wikimedia.org/wiki/Category:South_Bend,_Indiana", "Wikimedia Commons file pages and API metadata (license, credit)", "Wikimedia Commons", "dataset", "Each image's own file page is in images.csv."),
 ("PPL-036", "https://www.wvpe.org/wvpe-news/2023-11-07/democrats-celebrate-big-election-day-wins-in-south-bend-mishawaka-city-races", "Democrats celebrate big Election Day wins in South Bend, Mishawaka city races (2023-11-07)", "WVPE", "news", ""),
 ("PPL-037", "https://www.wndu.com/2023/11/06/decision-2023-municipal-general-election-results", "Decision 2023 municipal general election results (2023-11-06)", "WNDU", "news", "Karen White 2023 votes."),
 ("PPL-038", "https://www.953mnc.com/2019/05/07/indiana-primary-and-special-election-results/", "Indiana primary and special election results (2019-05-07)", "95.3 MNC", "news", "Sheila Niezgodski 2019 primary."),
 ("PPL-039", "https://www.newamerica.org/insights/automation-nation/south-bend-reinventing-a-dying-city/", "South Bend: Reinventing a 'Dying City'", "New America", "secondary", ""),
 ("PPL-040", "https://www.sjcindiana.gov/DocumentCenter/View/73081", "St. Joseph County 2026 general election results, unofficial 11/3/2026", "St. Joseph County Election Board", "primary", "Unofficial; read in the fact-check report."),
]
wcsv(ED + r"\sources_community.csv", "id,url,title,publisher,accessed,kind,notes".split(","), [[a, b, c, d, ACC, e, f] for a, b, c, d, e, f in COM])
wcsv(ED + r"\sources_people.csv", "id,url,title,publisher,accessed,kind,notes".split(","), [[a, b, c, d, ACC, e, f] for a, b, c, d, e, f in PPL])

# ------------------------------------------------------------------ people
# fields: id,name,offices,parties,criteria,in_office,summary,findings,image_key,status,conf,sources,notes, first_year (not written), party list for stats
P = []


def person(pid, name, offices, parties, crit, now, summary, findings, img, status, conf, src, notes, first, era_note=""):
    P.append(dict(pid=pid, name=name, offices=offices, parties=parties, crit=crit, now=now, summary=summary, findings=findings,
                  img=img, status=status, conf=conf, src=src, notes=notes, first=first))


person("PPL-001", "Schuyler Colfax", "U.S. Representative, Indiana 9th district (1855-1869); Speaker of the U.S. House (1863-1869); Vice President of the United States (1869-1873)", "O;R", "HIGHER;FAMILY", "false",
       "Moved with his family to South Bend in 1841 and edited the South Bend Free Press from 1842, buying it in 1845 and renaming it the St. Joseph Valley Register. He served in the U.S. House from 1855 to 1869, including as Speaker from 1863, and as Vice President from 1869 to 1873. He belonged to the Whig Party and later the Republican Party. His son Schuyler Colfax III served as mayor of South Bend.",
       "A 1872-73 congressional investigation found that he accepted a $1,200 check for 20 shares of Credit Mobilier stock from Oakes Ames in 1868 (per Wikipedia); an impeachment resolution failed and he did not run for office again.",
       "colfax", "secondary", "high", "PPL-001;PPL-002", "Party code O = Whig (earlier affiliation); R = Republican.", 1855)
person("PPL-002", "Schuyler Colfax III", "Mayor of South Bend (1898-1902; the Colfax article gives 1898-1901)", "R", "FAMILY", "false",
       "Son of Vice President Schuyler Colfax. The Wikipedia mayors list shows him as the Republican mayor of South Bend from 1898 to 1902, while the article on his father gives 1898 to 1901.",
       "", "", "secondary", "medium", "PPL-001;PPL-002", "The 'youngest mayor' remark in the mayors list has no stated basis and is not encoded.", 1898)
person("PPL-003", "William G. George", "Mayor of South Bend (1865-1868)", "R", "FIRST", "false",
       "Listed as the first mayor of South Bend after the city was incorporated on May 22, 1865. The Wikipedia mayors list gives his term as 1865 to 1868 and his party as Republican. No other biographical information was collected.",
       "", "", "secondary", "medium", "PPL-002;PPL-025", "", 1865)
person("PPL-004", "Janet Allen", "South Bend Common Council (elected 1963); Republican nominee for mayor (1971)", "R", "FIRST", "false",
       "Wikipedia's page on South Bend mayoral elections identifies her as the first woman elected to the Common Council, in 1963. She was the Republican nominee for mayor in 1971 and lost to Jerry Miller.",
       "", "", "single_source", "low", "PPL-025", "Single secondary source; no council dates collected.", 1963)
person("PPL-005", "Lloyd M. Allen", "Mayor of South Bend (1964-1972)", "R", "TURNING_POINT", "false",
       "Elected mayor in 1963 and re-elected in 1967 with 58 percent of the vote. He is identified as the last Republican elected mayor of South Bend; every mayor since 1972 has been a Democrat.",
       "", "", "secondary", "medium", "PPL-002;PPL-025", "Last Republican mayor confirmed against the Wikipedia table in the fact-check.", 1964)
person("PPL-006", "Jerry Miller", "Mayor of South Bend (1972-1975; a sidebar gives 1972-85)", "D", "TURNING_POINT", "false",
       "Won the 1971 mayoral election, which began continuous Democratic control of the mayor's office. He campaigned on a cabinet form of government and restructured the executive branch after taking office. Sources differ on the end of his term (1975 in the table, 1985 in a sidebar).",
       "", "", "secondary", "medium", "PPL-002;PPL-025", "Wikipedia mayoral-elections page implies Miller served through December 1975 and Peter Nemeth from January 1976.", 1972)
person("PPL-007", "John Brademas", "U.S. Representative, Indiana 3rd district (1959-1981); House Majority Whip (1977-1981); president of New York University (1981-1991 or 1992)", "D", "TENURE", "false",
       "Born in Mishawaka. He served 22 years in the U.S. House and lost his 1980 re-election bid to John Hiler. Wikipedia describes him as a co-sponsor of the 1965 law that created the National Endowment for the Arts and the National Endowment for the Humanities.",
       "", "brademas", "secondary", "high", "PPL-003", "'First Greek-American member of Congress' was not checked in the fact-check and is not encoded as FIRST. No prior local office documented, so HIGHER not applied beyond TENURE.", 1959)
person("PPL-008", "Tim Roemer", "U.S. Representative, Indiana 3rd district (1991-2003); U.S. Ambassador to India (2009-2011)", "D", "HIGHER", "false",
       "Born in South Bend. He defeated John Hiler in 1990 and served six terms in the U.S. House. He chaired the New Democrat Coalition from 1997 to 2001, served on the 9/11 Commission and was U.S. Ambassador to India from 2009 to 2011.",
       "", "roemer", "secondary", "high", "PPL-004", "HIGHER applied to anyone documented in a federal or statewide office (see _corrections file).", 1991)
person("PPL-009", "Joe Kernan", "South Bend Controller (1980-1984); Mayor of South Bend (1988-1997); Lieutenant Governor of Indiana (1997-2003); Governor of Indiana (September 2003-January 2005)", "D", "HIGHER", "false",
       "A Navy flight officer, he was shot down over North Vietnam and held as a prisoner of war for about 11 months. He became governor in September 2003 on the death of Gov. Frank O'Bannon and lost the 2004 governor's race to Mitch Daniels. His successor as mayor, Steve Luecke, was chosen by the South Bend Common Council in 1997.",
       "", "kernan", "secondary", "medium", "PPL-005;PPL-002;PPL-006", "Governor and Lt. Governor dates match the standard record (fact-check, knowledge-only); cite an official state source before publication. Luecke's 1997 selection mechanism rests on one source.", 1980)
person("PPL-010", "Stephen Luecke", "South Bend Common Council, 1st District (1988-1997); Mayor of South Bend (1997-2012)", "D", "TENURE", "false",
       "Joined the Common Council in 1988 and became mayor in January 1997 after Joe Kernan was elected lieutenant governor; he was then elected in 1999, 2003 and 2007. The Wikipedia mayors list shows his term as the longest of any mayor, 14 years and 363 days. Projects associated with his administration include the Morris Performing Arts Center renovation, Eddy Street Commons and Ignition Park. South Bend was named an All-America City in 2011.",
       "", "luecke", "secondary", "high", "PPL-006;PPL-002", "TENURE counts council plus mayoral service in the same city (about 24 years). Wikipedia gives both 2011 and 2012 as the end year; the list says Jan 1, 2012.", 1988)
person("PPL-011", "Pete Buttigieg", "Mayor of South Bend (2012-2020); U.S. Secretary of Transportation (2021-2025)", "D", "HIGHER;TURNING_POINT", "false",
       "Won the 2011 mayoral election with 73.85 percent and took office on January 1, 2012 at age 29. New America cites his election as the start of a new era after South Bend appeared on a 2011 Newsweek list of 'America's Dying Cities'. Programs listed for his administration include Smart Streets and '1,000 Properties in 1,000 Days'. He served as U.S. Secretary of Transportation from February 2021 to January 2025.",
       "Police recordings litigation (city as defendant): the city settled with former police chief Darryl Boykins for $75,000 and with officers for $500,000 combined (ABC57; WOWO; The Indiana Lawyer). On May 28, 2026 a federal judge ruled for the officers, finding the recordings were made without consent in violation of the Indiana and federal wiretap acts, and ordered the city to destroy them (WVPE); the Common Council was reported to be considering an appeal in early June 2026 (WNDU).",
       "buttigieg", "secondary", "high", "PPL-007;PPL-039;PPL-028;PPL-029;PPL-030;PPL-031;PPL-032;PPL-034", "Settlement figures corrected per fact-check ($75,000 + $500,000, not 'over $800,000'). Appeal status after June 2026 not confirmed (the fact-check report says the Council filed an appeal; WNDU 2026-06-02 says it was considering one).", 2012)
person("PPL-012", "Joe Donnelly", "Mishawaka Marian School Board (1997-2001); U.S. Representative, Indiana 2nd district (2007-2013); U.S. Senator (2013-2019); U.S. Ambassador to the Holy See (2022-2024)", "D", "HIGHER", "false",
       "Served on the Mishawaka Marian School Board from 1997 to 2001 before election to the U.S. House in 2006. He represented Indiana in the U.S. Senate from 2013 to 2019 and lost his 2018 re-election bid. He lives in Granger.",
       "", "donnelly_rep", "secondary", "high", "PPL-008", "Two Commons portraits exist (Representative; Ambassador).", 1997)
person("PPL-013", "Jackie Walorski", "Indiana House, 21st district (2005-2010); U.S. Representative, Indiana 2nd district (2013-2022)", "R", "HIGHER", "false",
       "Born in South Bend. She served in the Indiana House from January 2005 to November 2010 and in the U.S. House from January 2013 until her death on August 3, 2022 in a car crash near Nappanee. She was ranking member of the House Ethics Committee in 2021-22. A VA clinic in Mishawaka is named for her.",
       "", "walorski", "secondary", "high", "PPL-009;PPL-027", "", 2005)
person("PPL-014", "Rudy Yakym", "U.S. Representative, Indiana 2nd district (since the 2022 special election)", "R", "HIGHER", "true",
       "Won the special election held after the death of Rep. Jackie Walorski in August 2022. In the unofficial November 2026 county returns, the St. Joseph County portion of the 2nd district vote was 38.69 percent for Yakym and 59.35 percent for Decio (D); the district-wide result was not checked.",
       "", "yakym", "secondary", "medium", "PPL-009;PPL-027;PPL-034", "in_office_now reflects the term ending January 2027; the 2026 district-wide result was not checked, so succession in January 2027 is unknown.", 2022)
person("PPL-015", "B. Patrick Bauer", "Indiana House, 6th district (1970-2020); Speaker of the Indiana House (two periods, dates differ across sources); House Minority Leader (2011)", "D", "TENURE;FIRST;FAMILY;TURNING_POINT", "false",
       "Served in the Indiana House from November 1970 to November 2020; Wikipedia describes him as the longest-serving member of the House and the first General Assembly member to serve 50 years. In February 2011 he led 37 Democrats in a walkout to block a right-to-work bill; it ended on March 28, 2011. His father, Burnie Bauer, served in the legislature, and his daughter, Maureen Bauer, succeeded him in the 6th district.",
       "", "", "secondary", "medium", "PPL-010;PPL-011;PPL-034", "Walkout count corrected to 37 (Ballotpedia via fact-check; Wikipedia said 36). Speaker years in Wikipedia (2003-05, 2007-11) are unverified; knowledge suggests 2002-04 and 2007-10. 'First to serve 50 years' rests on Wikipedia alone.", 1970)
person("PPL-016", "Burnie Bauer", "State representative and state senator (dates and district not collected)", "", "FAMILY", "false",
       "Father of B. Patrick Bauer. Wikipedia's article on his son states that he served as a state representative and a state senator. Dates and districts were not collected.",
       "", "", "single_source", "low", "PPL-010", "Party not documented. Included because the FAMILY criterion (two or more family members in elected office here) is met on the Bauer family.", None)
person("PPL-017", "Maureen Bauer", "Indiana House, 6th district (since November 2020)", "D", "FAMILY", "true",
       "Succeeded her father, B. Patrick Bauer, in the 6th district in November 2020; Wikipedia gives two start dates, November 4 and November 16, 2020. She won the 2024 election with 81 percent against a Libertarian candidate. The 6th district race in the unofficial 2026 county returns was uncontested.",
       "", "", "secondary", "high", "PPL-011;PPL-010;PPL-034", "", 2020)
person("PPL-018", "Michael Dvorak", "Indiana House, 8th district (1986-2002); St. Joseph County Prosecutor (2003-2015)", "D", "TENURE;FAMILY", "false",
       "Won the House seat in 1986 by defeating three-term Republican incumbent Lloyd Taylor and served until 2002. He was county prosecutor from January 2003 to January 2015 and did not seek re-election in 2014. His son Ryan Dvorak succeeded him in the House seat.",
       "", "", "secondary", "high", "PPL-012;PPL-013", "A December 2010 charging decision in a case involving a private individual and a 2013 special-prosecutor request were omitted: the first per the fact-check's editorial instruction, the second because it is unverified.", 1986)
person("PPL-019", "Ryan Dvorak", "Indiana House, 8th district (2002-present); Assistant Democratic Leader (after 2012)", "D", "TENURE;FAMILY", "true",
       "Succeeded his father, Michael Dvorak, in House District 8 in 2002. He placed third in the 2011 Democratic primary for South Bend mayor with 14.62 percent and was a senior aide to Tim Roemer from 1996 to 2001. In the unofficial 2026 county returns he led the District 8 race 12,953 votes to 6,541.",
       "", "", "secondary", "high", "PPL-013;PPL-012;PPL-040", "2026 District 8 figures are unofficial (county document 73081, dated 11/3/2026).", 2002)
person("PPL-020", "Craig Fry", "Indiana House, 5th district (1988-2012)", "D", "TENURE", "false",
       "Represented the Mishawaka area in the Indiana House for 24 years. Dale DeVon (R) won the open seat in 2012. Fry was an Ivy Tech apprenticeship director and the 2011 Democratic nominee for Mishawaka mayor, losing to Dave Wood.",
       "", "", "secondary", "medium", "PPL-014;PPL-034", "Sparse biography.", 1988)
person("PPL-021", "David Niezgodski", "Indiana House, 7th district (2006-2016); Indiana Senate, 10th district (2016-present)", "D", "TENURE;FAMILY", "true",
       "Served in the Indiana House from November 2006 to November 2016 and in the Indiana Senate since November 2016. His spouse, Sheila Niezgodski, is a member of the South Bend Common Council. He won the 2024 Democratic primary over Tim Swager.",
       "", "niezgodski", "secondary", "medium", "PPL-015;PPL-033;PPL-034", "Reported by WVPE (citing IndyStar), 2024-04-18: a former office assistant at his plumbing business filed an Indiana Civil Rights Commission complaint in 2017 and dropped it in exchange for $8,000. His statement expressed regret, took 'full responsibility' for any pain or discomfort, described the matter as a personnel issue resolved 'mutually and confidentially', and did not admit harassment. No charges or findings were reported. Not placed in documented_findings because it is not an official finding; details of the alleged conduct omitted per the fact-check.", 2006)
person("PPL-022", "Sheila Niezgodski", "South Bend Common Council, 6th District (since 2019)", "D", "FAMILY", "true",
       "Won the 2019 Democratic primary for District 6 with 619 votes (53 percent) to Jason Banicki's 543. Her second term began on January 1, 2024. She is the spouse of State Sen. David Niezgodski.",
       "", "", "secondary", "medium", "PPL-038;PPL-015", "", 2019)
person("PPL-023", "Ryan Mishler", "Indiana Senate, 9th district (2004-present)", "R", "TENURE", "true",
       "Has held the 9th district Senate seat since 2004 and chairs the Appropriations Committee. He is a funeral director in Bremen. Wikipedia describes the district as spanning Kosciusko, Marshall, St. Joseph and Elkhart counties; he was unopposed in 2024.",
       "", "", "secondary", "high", "PPL-016;PPL-034", "District boundaries after redistricting not re-checked.", 2004)
person("PPL-024", "Robert Beutter", "Mayor of Mishawaka (1984-2003)", "", "TENURE", "false",
       "Served five terms and was described by WSBT and the city as the longest-serving mayor in Mishawaka's history. He began as assistant city attorney under Mayor Margaret Prickett. His administration led the city's purchase of the former Uniroyal plant from the bankruptcy trustee, which led to the Riverwalk and a park named for him. He died in January 2020 at age 84.",
       "", "", "secondary", "medium", "PPL-017;PPL-018;PPL-034", "End year 2003 per the city statement (fact-check); ABC57's 1982 start is impossible given Kovach's 1980-83 term. Party not documented in the sources.", 1984)
person("PPL-025", "Margaret Prickett", "Mayor of Mishawaka (elected 1963; lost in 1979)", "", "TENURE", "false",
       "Elected mayor of Mishawaka in 1963 and served four terms, about 16 years, until losing in 1979 to Democrat Bob Kovach. Robert Beutter began his career as assistant city attorney under her.",
       "", "", "single_source", "low", "PPL-017;PPL-019", "Search-result summaries only. Party not confirmed (a snippet says she carried the whole Republican ticket). 'First woman mayor' is unverified and not encoded.", 1964)
person("PPL-026", "Dave Wood", "Mayor of Mishawaka (since 2010)", "R", "TENURE", "true",
       "Took over in 2010 to finish Jeff Rea's term and was elected in 2011, 2015, 2019 and 2023, unopposed in 2023. A city source describes him as Mishawaka's 21st mayor.",
       "", "", "secondary", "low", "PPL-020;PPL-034", "TENURE is not fully documented: the month he took office in 2010 was not found, so 16 years of service is reached in late 2026 or 2027 depending on that date. '21st mayor' rests on a single WNDU source.", 2010)
person("PPL-027", "Karen White", "South Bend Common Council, at-large (first elected 1999)", "D", "TENURE", "true",
       "First elected to the Common Council in 1999 according to Wikipedia and re-elected to an at-large seat in November 2023 with 7,172 votes. She is among nine Democrats on the council.",
       "", "", "secondary", "medium", "PPL-026;PPL-037", "Continuous service from 1999 is assumed, not documented year by year.", 1999)
person("PPL-028", "Eugenia Braboy", "South Bend Common Council, district seat (1984-1987)", "", "FIRST", "false",
       "A 2003 city resolution names her as the first African American to hold a district seat on the South Bend Common Council and as the first African American woman on the council. The resolution page was seen only in search-result summaries and has not been read in full.",
       "", "", "single_source", "low", "PPL-022", "Resolution seen only in a search summary; party not documented.", 1984)
person("PPL-029", "Pfeifer (given name unconfirmed: Beverly or Charlotte)", "South Bend Common Council (1996-2007); council president (2000)", "", "FIRST", "false",
       "According to a WVPE profile, she served on the council from 1996 to 2007 and was its first African American president, in 2000. Sources conflict on her first name.",
       "", "", "single_source", "low", "PPL-023", "Use the city resolution's wording for the name before publication. Party not documented.", 1996)
person("PPL-030", "Sherry Bolden-Simpson", "South Bend Common Council, 5th District (since January 1, 2024)", "D", "FIRST;TURNING_POINT", "true",
       "Won District 5 in November 2023 with 1,414 votes to incumbent Eli Wax's 1,376, a 38-vote margin. The city's page says she is the first Democrat elected to the seat since 1962 and the first woman and first Black woman to hold it; these statements are self-described. The 2023 election gave Democrats all nine council seats.",
       "", "", "single_source", "medium", "PPL-024;PPL-036;PPL-037;PPL-034", "Margin corrected to 38 per official canvass (fact-check). District 5 had elected Republicans since at least the early 1990s (WVPE).", 2024)
person("PPL-031", "J. Chester Allen", "Attorney; Indiana House (1938, per one search snippet); South Bend school board appointee", "", "FIRST", "false",
       "A South Bend Tribune piece describes him as the first African American to represent South Bend in state government, the first Black appointee to the school board and the first president of the local bar association. These claims come from a single article and have not been re-sourced. He ran a law firm with his wife, Elizabeth Fletcher.",
       "", "", "single_source", "low", "PPL-021;PPL-034", "The article's wording that he was 'the first person elected to serve on the South Bend Common Council' is removed per the fact-check (council dates from 1865). Remaining 'firsts' are single-snippet and need re-sourcing. Party and dates not documented.", 1938)

IMGKEY = {}  # filled when images built
ERAS = [("pre-1950", 0, 1949), ("1950-1979", 1950, 1979), ("1980-1999", 1980, 1999), ("2000-present", 2000, 9999)]


def era(y):
    if y is None:
        return "unknown"
    for n, a, b in ERAS:
        if a <= y <= b:
            return n


# ------------------------------------------------------------------ images
imgrows = []
IMG_FOR = {}
if META:
    meta = json.load(open(META))
    md = open(R + r"\research\07-notable-figures-and-images.md", encoding="utf-8").read()
    partb = md[md.index("## PART B"):md.index("## Gaps / not found")]
    dl = json.load(open(sys.argv[2]))
    key_by_title = {}
    n = 0
    for line in partb.splitlines():
        if not line.startswith("|"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 5 or "commons.wikimedia.org/wiki/File:" not in c[1]:
            continue
        if "Philip_Sharp" in c[1]:
            continue
        subject, page, direct, lic, credit = c[0], c[1], c[2], c[3], c[4]
        notes = c[5] if len(c) > 5 else ""
        title = "File:" + re.sub(r"_", " ", __import__("urllib.parse").parse.unquote(page.split("/wiki/File:")[1]))
        n += 1
        p = meta[title]
        ii = p["imageinfo"][0]
        em = ii.get("extmetadata", {})
        d = dl.get(title)
        local = ""
        extra = []
        if d:
            local = "site/images/" + d["file"]
            if d["resized"]:
                extra.append("Local copy is a 3840 px-wide Commons thumbnail (original %.1f MB, %dx%d px)" % (ii["size"] / 1e6, ii["width"], ii["height"]))
        api_lic = em.get("LicenseShortName", {}).get("value", "")
        if api_lic and api_lic.lower().replace("-", " ") != lic.lower().replace("-", " "):
            extra.append("Commons API license '%s' differs from research/07 value" % api_lic)
        if "sweep" in local.lower():
            newname = "south_bend_election_map_by_district_2023.svg"
            if os.path.exists(R + "\\" + local.replace("/", "\\")):
                os.replace(R + "\\" + local.replace("/", "\\"), R + "\\site\\images\\" + newname)
            local = "site/images/" + newname
            extra.append("Local file renamed from the Commons title, which contains a non-neutral term; the Commons page title is unchanged")
        iid = "IMG-%03d" % n
        key_by_title[title] = iid
        imgrows.append([iid, subject.replace("(2020s Democratic sweep)", ""), page, direct, lic, credit, local, "; ".join(x for x in [notes] + extra if x)])
    # the 2024 view listed in research/07 as 'not fetched'
    t24 = "File:County-City Building, lower front, South Bend, IN 2024-04-14.jpg"
    p = meta[t24]; ii = p["imageinfo"][0]; em = ii["extmetadata"]; d = dl.get(t24)
    n += 1
    iid = "IMG-%03d" % n
    key_by_title[t24] = iid
    imgrows.append([iid, "County-City Building, lower front (2024-04-14)", "https://commons.wikimedia.org/wiki/File:County-City_Building,_lower_front,_South_Bend,_IN_2024-04-14.jpg",
                    ii["url"].split("?")[0], em["LicenseShortName"]["value"], "Xnatedawgx, own work (Commons API artist field)", ("site/images/" + d["file"]) if d else "",
                    "Listed in research/07 as a search hit with license unverified; license and credit taken from the Commons API on 2026-11-07. A second 2024 view ('NW corner') named in research/07 was not located."])
    wcsv(ED + r"\images.csv", "image_id,subject,file_page_url,direct_url,license,credit,local_file,notes".split(","), imgrows)
    keymap = {"brademas": "John_Brademas", "roemer": "Timothy_J._Roemer", "kernan": "Joe_Kernan", "colfax": "Schuyler_Colfax_portrait", "luecke": "Mayor_steve_luecke", "buttigieg": "Pete_Buttigieg,_Secretary", "donnelly_rep": "Congressman_joedonnelly",
              "walorski": "Jackie_Walorski", "yakym": "Rudy_Yakym", "niezgodski": "David_Niezgodski"}
    for k, frag in keymap.items():
        for r in imgrows:
            if frag in r[2]:
                IMG_FOR[k] = r[0]

# ------------------------------------------------------------------ write people
rows = []
for p in P:
    img = IMG_FOR.get(p["img"], "")
    s = p["summary"]
    nsent = count_sent(s)
    if not 2 <= nsent <= 4:
        print('SENT', p['name'], nsent)
    rows.append([p["pid"], p["name"], p["offices"], p["parties"], p["crit"], p["now"], s, p["findings"], img, p["status"], p["conf"], p["src"], p["notes"]])
wcsv(ED + r"\people.csv", "person_id,name,offices_summary,parties,criteria,in_office_now,summary,documented_findings,image_id,status,confidence,source_ids,notes".split(","), rows)

# distribution
by_party = collections.Counter(); by_era = collections.Counter(); cross = collections.Counter(); by_crit = collections.Counter()
for p in P:
    labs = [x for x in p["parties"].split(";") if x] or ["unknown"]
    main = labs[-1] if labs[-1] != "O" else labs[0]
    by_party[main] += 1
    e = era(p["first"]); by_era[e] += 1; cross[(e, main)] += 1
    for c in p["crit"].split(";"):
        by_crit[c] += 1
print("N people", len(P))
print("by party (current/last party)", dict(by_party))
print("by era (first documented service year)", dict(by_era))
for k in sorted(cross): print("  ", k, cross[k])
print("by criterion", dict(by_crit))
print("in office now", sum(p["now"] == "true" for p in P))
json.dump({"party": by_party, "era": by_era, "cross": {"%s|%s" % k: v for k, v in cross.items()}, "crit": by_crit, "n": len(P)}, open(ED + r"\..\..\..\tools\_people_stats.json", "w"))
