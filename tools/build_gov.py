#!/usr/bin/env python
# Builder for data/editions/st-joseph/{units,offices,terms,appointed_boards}.csv, sources_gov.csv, gaps_gov.csv
import csv, os, re
from collections import defaultdict

OUT = r"C:\Users\nickb\local-gov-guide\data\editions\st-joseph"
TODAY = "2026-11-07"
ACC = "2026-11-07"

# ---------------------------------------------------------------- sources
SRC = {}      # key -> (url,title,publisher,kind,notes)
SRC_ORDER = []
def src(key, url, title, publisher, kind, notes=""):
    SRC[key] = (url, title, publisher, kind, notes); SRC_ORDER.append(key)

DC = "https://www.sjcindiana.gov/DocumentCenter/View/"
CO = "St. Joseph County Election Board"
src("k26g", DC+"73081", "2026 General Election summary results (UNOFFICIAL as of 11/3/2026 9:07 PM EST)", CO, "primary", "Text-layer PDF. Unofficial election-night/central-count results; official canvass not posted as of 2026-11-07.")
src("k26p", DC+"71640", "2026 Primary Election official results (5/15/2026)", CO, "primary", "Text-layer PDF.")
src("k24", DC+"64951", "2024 General Election FINAL official results (11/15/2024)", CO, "primary", "Scanned PDF; read by OCR (research/results-2020-2026.md).")
src("k23", DC+"60569", "2023 Municipal General official results (11/17/2023)", CO, "primary", "Text-layer PDF.")
src("k22", DC+"57716", "2022 General Election official results (11/18/2022)", CO, "primary", "Summary pages of a 1,388-page file; OCR-quality text layer.")
src("k20", DC+"42820", "2020 General Election official results (11/13/2020)", CO, "primary", "Text-layer PDF; some office labels inferred from page order by the transcriber.")
src("k19", DC+"60004", "2019 Municipal General official results (run 11/15/2019)", CO, "primary", "Scanned PDF; read by OCR.")
src("k18", DC+"60006", "2018 General Election official results (run 11/16/2018)", CO, "primary", "Scanned PDF; read by OCR.")
src("k16", DC+"60008", "2016 General Election official report (run 11/18/2016)", CO, "primary", "Scanned PDF; read by OCR.")
src("k15", DC+"60010", "2015 Municipal General summary report (run 11/03/2015, election night)", CO, "primary", "Scanned PDF; read by OCR. Header is an election-night run, not a certified canvass.")
src("k14", DC+"60012", "2014 General Election summary results", CO, "primary", "Scanned PDF; read by OCR.")
src("k12", DC+"60015", "2012 General Election summary results", CO, "primary", "Scanned PDF; read by OCR.")
src("k11", DC+"60017", "2011 Municipal General summary results (run 11/18/2011)", CO, "primary", "Scanned PDF; read by OCR.")
src("k10", DC+"60019", "2010 General Election summary results", CO, "primary", "Scanned PDF; read by OCR.")
src("fc", "planning/fact-check-report.md", "Fact-check report: St. Joseph County civic guide research files (2026-11-07)", "Project fact-check pass", "derived", "Local planning file. Cited where a fact-check finding corrected or resolved a value.")
src("r01", "research/01-county.md", "Research slice 01: County government", "Project research notes", "derived", "Local research file; secondary compilation of news and Wikipedia.")
src("r02", "research/02-south-bend.md", "Research slice 02: City of South Bend", "Project research notes", "derived", "Local research file; mayors list from Wikipedia.")
src("r03", "research/03-mishawaka-townships-schools.md", "Research slice 03: Mishawaka, townships, school boards, other units", "Project research notes", "derived", "Local research file.")
src("r04", "research/04-state-and-elections.md", "Research slice 04: State government and election law (section A: legislators)", "Project research notes", "derived", "Local research file.")
src("r07", "research/07-notable-figures-and-images.md", "Research slice 07: Notable figures (office dates)", "Project research notes", "derived", "Local research file; Wikipedia-sourced, condensed.")
src("r09", "research/09-gap-fill-ballotpedia-statutes.md", "Research slice 09: Ballotpedia legislative history and statutes", "Project research notes", "derived", "Local research file.")
src("wp_county", "https://en.wikipedia.org/wiki/St._Joseph_County,_Indiana", "St. Joseph County, Indiana", "Wikipedia", "secondary")
src("wp_mayors", "https://en.wikipedia.org/wiki/List_of_mayors_of_South_Bend,_Indiana", "List of mayors of South Bend, Indiana", "Wikipedia", "secondary", "Page flags internal inconsistencies (Miller, Longley, Fogarty; odd Jan 3 dates for Kernan/Luecke).")
src("wp_mayoral", "https://en.wikipedia.org/wiki/Mayoral_elections_in_South_Bend,_Indiana", "Mayoral elections in South Bend, Indiana", "Wikipedia", "secondary")
src("wp_luecke", "https://en.wikipedia.org/wiki/Stephen_Luecke", "Stephen Luecke", "Wikipedia", "secondary", "Single source for the 1997 council appointment.")
src("wp_sbcc", "https://en.wikipedia.org/wiki/South_Bend_Common_Council", "South Bend Common Council", "Wikipedia", "secondary")
src("wvpe_beid", "https://www.wvpe.org/wvpe-news/2026-05-20/beidinger-wins-warners-south-bend-council-seat-in-party-caucus", "Beidinger wins Warner's South Bend council seat in party caucus", "WVPE", "news")
src("wndu_beid", "https://www.wndu.com/2026/05/20/heidi-beidinger-burnett-chosen-take-vacant-south-bend-common-council-seat/", "Heidi Beidinger-Burnett chosen to take vacant South Bend Common Council seat", "WNDU", "news", "Used for the expected end of term (Dec 31, 2027), via search summary.")
src("abc57_jones", "https://www.abc57.com/news/dawn-jones-elected-as-south-bend-city-clerk-in-special-caucus-vote", "Dawn Jones elected as South Bend city clerk in special caucus vote", "ABC57", "news")
src("abc57_tirado", "https://www.abc57.com/news/tirado-to-serve-alongside-majority-female-council-as-south-bend-city-clerk", "Tirado to serve alongside majority-female council as South Bend city clerk", "ABC57", "news", "Describes Jones as the previous clerk.")
src("wvpe_bax", "https://www.wvpe.org/wvpe-news/2022-08-30/st-joseph-county-commissioners-pick-newcomer-carl-baxmeyer-as-president", "St. Joseph County commissioners pick newcomer Carl Baxmeyer as president", "WVPE", "news", "GOP caucus pick Aug 2022 to replace resigning Andy Kostielney.")
src("wvpe_hazen", "", "WVPE report on Jan 20, 2024 GOP caucus choosing Tony Hazen (dated 2024-01-12)", "WVPE", "news", "URL not recorded in the fact-check report; cited there as 'WVPE 2024-01-12 (search results)'.")
src("wndu_cotter", "https://www.wndu.com/2026/01/21/st-joseph-county-prosecutor-kenneth-cotter-announces-retirement", "St. Joseph County prosecutor Kenneth Cotter announces retirement", "WNDU", "news")
src("wvpe_ruszk", "", "WVPE 2026-01-23 / WNDU 2026-05-06 coverage of Scott Ruszkowski (sitting South Bend police chief)", "WVPE; WNDU", "news", "URLs not recorded in the fact-check report; cited there as search results.")
src("abc57_ruling", "https://www.abc57.com/news/judge-rules-st-joseph-county-election-system-violates-indiana-constitution", "Judge rules St. Joseph County election system violates Indiana Constitution", "ABC57", "news", "Apr 22, 2026. Names no judge or court; says the ruling could be appealed.")
src("mnc26", "https://www.953mnc.com/2026/11/04/democrats-sweep-major-st-joseph-county-races-winning-sheriff-prosecutor-commissioner-seats/", "Democrats sweep major St. Joseph County races (2026, unofficial)", "95.3 MNC", "news", "Unofficial, Nov 4, 2026.")
src("mish_site", "https://mishawaka.in.gov/government/elected-appointed-officials/", "City of Mishawaka: elected and appointed officials", "City of Mishawaka", "primary", "Lists boards and commissions; does not say who appoints.")
src("mish_council", "https://mishawaka.in.gov/government/elected-appointed-officials/common-council/", "City of Mishawaka: Common Council", "City of Mishawaka", "primary", "Roster labeled '2024 Mishawaka Common Council'; no party shown.")
src("mish_hist", "https://mishawaka.in.gov/?p=204", "City of Mishawaka history page (first mayor after incorporation as a city)", "City of Mishawaka", "primary")
src("wndu_kovach", "https://www.wndu.com/2022/11/21/former-mishawaka-mayor-bob-kovach-dies", "Former Mishawaka mayor Bob Kovach dies", "WNDU", "news")
src("wsbt_beutter", "https://wsbt.com/news/local/mishawakas-longest-serving-mayor-dies-at-age-84", "Mishawaka's longest-serving mayor dies at age 84", "WSBT", "news")
src("wndu_wood", "https://www.wndu.com/2022/12/16/mishawaka-mayor-dave-wood-announces-reelection-campaign", "Mishawaka mayor Dave Wood announces reelection campaign", "WNDU", "news", "Calls Wood the 21st mayor; Rea preceded him.")
src("journal_prickett", "https://journalreview.com/stories/cracking-the-mayoral-glass-ceiling,245697", "Cracking the mayoral glass ceiling (Margaret Prickett)", "Journal Review", "news", "Search result only; not opened by the researcher.")
src("bp_house", "https://ballotpedia.org/Indiana_House_of_Representatives_District_5", "Ballotpedia: Indiana House of Representatives districts 5, 6, 7, 8, 21", "Ballotpedia", "secondary", "Also district_6/_7/_8/_21 pages. Election history back to 2012.")
src("bp_senate", "https://ballotpedia.org/Indiana_State_Senate_District_8", "Ballotpedia: Indiana State Senate districts 8, 9, 10, 11", "Ballotpedia", "secondary", "Also district_9/_10/_11 pages. Election history back to 2012.")
src("wp_bauer", "https://en.wikipedia.org/wiki/B._Patrick_Bauer", "B. Patrick Bauer", "Wikipedia", "secondary")
src("wp_mbauer", "https://en.wikipedia.org/wiki/Maureen_Bauer", "Maureen Bauer", "Wikipedia", "secondary", "Gives two start dates (Nov 4 vs Nov 16, 2020).")
src("wp_mdvorak", "https://en.wikipedia.org/wiki/Michael_Dvorak", "Michael Dvorak", "Wikipedia", "secondary")
src("wp_rdvorak", "https://en.wikipedia.org/wiki/Ryan_Dvorak", "Ryan Dvorak", "Wikipedia", "secondary")
src("wp_fry", "https://en.wikipedia.org/wiki/Craig_Fry", "Craig Fry", "Wikipedia", "secondary")
src("wp_niez", "https://en.wikipedia.org/wiki/David_Niezgodski", "David Niezgodski", "Wikipedia", "secondary")
src("wp_walorski", "https://en.wikipedia.org/wiki/Jackie_Walorski", "Jackie Walorski", "Wikipedia", "secondary")
src("wp_mishler", "https://en.wikipedia.org/wiki/Ryan_Mishler", "Ryan Mishler", "Wikipedia", "secondary")
src("ic36232", "https://codes.findlaw.com/in/title-36-local-government/in-code-sect-36-2-3-2/", "IC 36-2-3-2 (county council size)", "FindLaw (Indiana Code)", "statute")
src("ic36234", "https://law.justia.com/codes/indiana/title-36/article-2/chapter-3/", "IC 36-2-3-4 (county council districts) and IC 36-2-2-4 (commissioner districts)", "Justia (Indiana Code)", "statute", "Fact-check: opted-in 185k-300k counties get nine single-member council districts under 36-2-3-4(c); the 4+3 structure is the default for other counties.")
src("ic36463", "https://codes.findlaw.com/in/title-36-local-government/in-code-sect-36-4-6-3/", "IC 36-4-6-3 (second-class city council: 6 district + 3 at-large)", "FindLaw (Indiana Code)", "statute")
src("ic36452", "https://codes.findlaw.com/in/title-36-local-government/in-code-sect-36-4-5-2/", "IC 36-4-5-2 (mayor)", "FindLaw (Indiana Code)", "statute")
src("ic364102", "https://codes.findlaw.com/in/title-36-local-government/in-code-sect-36-4-10-2/", "IC 36-4-10-2 (city clerk, second-class cities)", "FindLaw (Indiana Code)", "statute")
src("ic3_13_11", "https://law.justia.com/codes/indiana/title-3/article-13/chapter-11/", "IC 3-13-11 (local-office vacancies filled by party caucus)", "Justia (Indiana Code)", "statute")
src("ic3_13_5", "https://law.justia.com/codes/indiana/title-3/article-13/chapter-5/", "IC 3-13-5 (legislative vacancies filled by party caucus)", "Justia (Indiana Code)", "statute")
src("const_a6", "https://law.justia.com/constitution/indiana/art6.html", "Indiana Constitution Art. 6 sec. 2 (county officers, 8-in-12 limit)", "Justia", "statute", "Text not read by the researcher; summary via search. Fact-check: limit covers Clerk, Auditor, Recorder, Treasurer, Sheriff, Coroner only.")
src("ic333371", "https://secure.in.gov/courts/selection/st-joseph", "St. Joseph County Superior Court judicial selection (nominating commission)", "Indiana Judicial Branch", "primary", "Per fact-check: 7-member commission (3 governor, 3 county commissioners, 1 Supreme Court justice chair); five nominees to governor.")
src("brochure", "https://in.gov/counties/wabash/files/County-Govt-There-when-you-need-it-brochure.pdf", "Indiana county government brochure", "State of Indiana", "primary", "Garbled pdftotext extraction.")
src("boh", "https://www.in.gov/localhealth/stjosephcounty/board-of-health/meet-the-board/", "St. Joseph County Board of Health: meet the board (2026 roster)", "St. Joseph County Health Department", "primary")
src("mphpl", "https://www.mphpl.org/about/board-of-trustees", "Mishawaka-Penn-Harris Public Library board of trustees", "MPH Public Library", "primary")
src("libblog", "https://blog.library.in.gov/whos-in-charge-public-library-boards-in-indiana/", "Who's in charge? Public library boards in Indiana", "Indiana State Library", "primary")
src("mnc_lib", "https://www.953mnc.com/2024/12/13/st-joseph-county-community-concerns-about-new-library-board-nomination/", "St. Joseph County community concerns about new library board nomination", "95.3 MNC", "news")
src("wp_airport", "https://en.wikipedia.org/wiki/South_Bend_International_Airport", "South Bend International Airport (Airport Authority)", "Wikipedia", "secondary")
src("sb_rdc", "https://southbendin.gov/?p=139649", "City of South Bend Redevelopment Commission page", "City of South Bend", "primary", "Seen as a search snippet only.")
src("sb_council", "https://southbendin.gov/government/common-council/", "City of South Bend: Common Council", "City of South Bend", "primary")
src("sb_official", "https://southbendin.gov/official/", "City of South Bend: elected officials", "City of South Bend", "primary")
src("legalfix_bpw", "https://legalfix.com/statutes/state-codes/indiana/title-36/article-4/chapter-9/section-36-4-9-5", "IC 36-4-9-5 (board of public works and safety), older code text", "LegalFix (Indiana Code)", "statute", "Researcher flags text as possibly outdated.")
src("ic36496", "https://codes.findlaw.com/in/title-36-local-government/in-code-sect-36-4-9-6/", "IC 36-4-9-6 (executive appointments, second-class cities)", "FindLaw (Indiana Code)", "statute", "Text truncated in research; verify.")
src("ballotready", "https://www.ballotready.org/positions/indiana-st-joseph-county-union-township-trustee", "BallotReady township trustee/board position pages (pattern: indiana-st-joseph-county-{township}-township-trustee)", "BallotReady", "secondary", "Used only for the Union Township trustee (2022 race lines absent from the county summary).")
src("wp_township", "https://en.wikipedia.org/wiki/Civil_township", "Civil township (Indiana: trustee plus three-member board)", "Wikipedia", "secondary")
src("centre_tw", "https://centretownshipin.gov/", "Centre Township website", "Centre Township", "primary", "States a small part of the township lies in South Bend; board members listed.")
src("harris_tw", "https://harristwp.com/about", "Harris Township about page", "Harris Township", "primary")
src("wp_schools", "https://en.wikipedia.org/wiki/List_of_school_districts_in_Indiana", "List of school districts in Indiana (five corporations named for St. Joseph County)", "Wikipedia", "secondary")
src("abc57_sch24", "https://abc57.com/news/election-results-indiana-school-boards", "Election results: Indiana school boards (Nov 2024)", "ABC57", "news", "Source of the 'SBCSC at-large (2)' seat count.")
src("sea287", "https://news.ballotpedia.org/2025/06/10/indiana-to-become-10th-state-to-hold-partisan-school-board-elections/", "Indiana to become 10th state to hold partisan school board elections (SEA 287, 2025)", "Ballotpedia News", "news", "Fact-check: SEA 287 confirmed; party, independent or nonpartisan labels allowed; no primary.")
src("mish_sch", "https://en.wikipedia.org/wiki/School_City_of_Mishawaka", "School City of Mishawaka", "Wikipedia", "secondary", "Per research: 3 elected at-large plus 2 appointed (Common Council, mayor).")
src("sbcsc_wp", "https://en.wikipedia.org/wiki/South_Bend_Community_School_Corporation", "South Bend Community School Corporation", "Wikipedia", "secondary")
src("phm_wp", "https://en.wikipedia.org/wiki/Penn-Harris-Madison_School_Corporation", "Penn-Harris-Madison School Corporation", "Wikipedia", "secondary")

SIDS = {}
for i, k in enumerate(SRC_ORDER, 1):
    SIDS[k] = "GOV-%03d" % i
USED = set()
def sid(keys):
    if isinstance(keys, str): keys = [keys]
    out = []
    for k in keys:
        if k not in SIDS: raise KeyError(k)
        USED.add(k); out.append(SIDS[k])
    return ";".join(out)

STATUS_OF = {"k26g":"u","k26p":"o","k24":"s","k23":"o","k22":"o","k20":"o","k19":"s","k18":"s","k16":"s","k15":"s","k14":"s","k12":"s","k11":"s","k10":"s"}
STNAME = {"o":"official","u":"unofficial","s":"from_scan","x":"secondary","e":"single_source","c":"computed"}
CANV = set(STATUS_OF)

# ---------------------------------------------------------------- units
UNITS = []
def U(uid, utype, name, parents="", places="", web="", st="official", srcs=(), notes=""):
    UNITS.append([uid, utype, name, parents, places, web, st, sid(srcs), notes])

U("county","county","St. Joseph County","","","https://www.sjcindiana.gov","official",["k26g","wp_county"],"County seat and county offices are in South Bend. Executive = three-member Board of Commissioners; fiscal body = nine-member County Council.")
U("sjc-courts","court_system","St. Joseph County courts (Circuit, Probate, Superior)","county","","","official",["k24","k22","ic333371"],"Circuit and Probate judges are elected; Superior Court judges are chosen by merit selection and face retention votes.")
U("south-bend","city","City of South Bend","county","South Bend","https://southbendin.gov","official",["k23","sb_council"],"Second-class-city structure (6 district + 3 at-large council seats; IC 36-4-6-3). The 'second class' label itself was not directly confirmed in research; fact-check treats it as consistent with statute band.")
U("mishawaka","city","City of Mishawaka","county","","https://mishawaka.in.gov","official",["k23","mish_site"],"Mayor-council city; 9-member Common Council (6 district + 3 at-large) and elected City Clerk.")
for uid, nm, srcs, nt in [
    ("indian-village","Town of Indian Village",["r03"],"Named as a town in the research; no election, officer or governance data found."),
    ("lakeville","Town of Lakeville",["k11","k15"],"Appears in 2011 and 2015 canvasses (Clerk-Treasurer and at-large council); no recent data found."),
    ("new-carlisle","Town of New Carlisle",["k26g","k15","k11"],"Council is at-large; 2011 and 2015 canvasses show vote-for-3."),
    ("north-liberty","Town of North Liberty",["k26g","r03"],"Appears in the 2026 canvass (at-large council)."),
    ("osceola","Town of Osceola",["k23","k19","r03"],"Clerk-Treasurer plus council (wards in 2019; at-large in 2023)."),
    ("roseland","Town of Roseland",["k23","k22","k26g"],"Clerk-Treasurer plus at-large council."),
    ("walkerton","Town of Walkerton",["k26g","k23","k22"],"Clerk-Treasurer, Town Judge, four wards plus at-large council."),
]:
    U(uid,"town",nm,"county","","", "official" if uid!="indian-village" else "secondary", srcs, nt)
TOWNSHIPS = ["Centre","Clay","German","Greene","Harris","Liberty","Lincoln","Madison","Olive","Penn","Portage","Union","Warren"]
for t in TOWNSHIPS:
    tid = t.lower()+"-township"
    web=""; pl=""; nt="One elected trustee plus a three-member elected township board (partisan, four-year terms)."
    s=["k22","k26g","wp_township"]
    if t=="Centre": web="https://centretownshipin.gov"; pl="A small part lies within South Bend (per centretownshipin.gov)"; s.append("centre_tw")
    if t=="Harris": web="https://harristwp.com"; s.append("harris_tw")
    if t=="Union": pl="Township office is in Lakeville (per in.gov townships page cited in research)"; nt+=" 2022 trustee race lines are absent from the county summary text."
    if t=="Penn": nt+=" Penn Township also elects a township assessor."
    U(tid,"township",t+" Township","county",pl,web,"official",s,nt)
U("sbcsc","school_corporation","South Bend Community School Corporation","county","South Bend area","","official",["k26g","k24","sbcsc_wp","abc57_sch24"],"Seven-member board (5 district + 2 at-large per research; a 2016 canvass transcription shows 3 at-large winners; seat count conflict unresolved).")
U("phm","school_corporation","Penn-Harris-Madison School Corporation","county","Penn, Harris and Madison townships (per Wikipedia)","https://www.phmschools.org","official",["k26g","k24","phm_wp"],"Board seats elected at-large and from Harris, Madison and Penn townships; seat counts per township not fully determined.")
U("school-city-mishawaka","school_corporation","School City of Mishawaka","county","Mishawaka area","","official",["k26g","k24","mish_sch"],"Five trustees: three elected at-large plus two appointed (one by the Common Council, one by the mayor), per research.")
U("john-glenn","school_corporation","John Glenn School Corporation","county","","https://www.jgsc.k12.in.us","official",["k26g","k24","wp_schools"],"Township seats as printed on the county canvass: Johnson, Liberty, Lincoln, Polk.")
U("union-north","school_corporation","Union-North United School Corporation","county","","","official",["k24","k20","wp_schools"],"Seats: North Township, Union Township, at-large. Not on the 2022 or 2026 canvass summaries.")
U("new-prairie","school_corporation","New Prairie United School Corporation","county","","","official",["k26g","k24"],"Appears on the St. Joseph County canvass (at-large and districts 1-3); research notes the corporation is LaPorte County based (not confirmed).")
U("laville","school_corporation","LaVille School Corporation","county","","","official",["k26g"],"Appears only on the 2026 canvass (North and Union township seats). Relationship to Union-North United is not documented in the research; confirm whether this is a separate corporation.")
U("sjcpl","library","St. Joseph County Public Library","county","","","secondary",["r03","libblog","mnc_lib"],"Seven-member appointed board (not elected); trustees serve four-year terms. Taxing detail not verified in sources.")
U("mphpl","library","Mishawaka-Penn-Harris Public Library","county","","https://www.mphpl.org","official",["mphpl"],"Seven-member appointed board; appointers listed in appointed_boards.csv.")
U("transpo","transit","South Bend Public Transportation Corporation (Transpo)","south-bend","","","single_source",["r03"],"Appointing detail and levy not found in research.")
U("sjc-airport-authority","airport_authority","St. Joseph County Airport Authority (South Bend International Airport)","county","","","secondary",["wp_airport","r01"],"Four-member bipartisan board appointed by the County Commissioners (per Wikipedia; date unclear).")
U("sjc-board-of-health","health_board","St. Joseph County Board of Health","county","","https://www.in.gov/localhealth/stjosephcounty","official",["boh","r01"],"Appointed policy board for the county health department.")
U("south-bend-housing-authority","housing_authority","South Bend housing authority","south-bend","","","single_source",["r03"],"Named in research as an unresearched local unit ('not found'); legal name, board and appointing authority not sourced. Placeholder.")
U("mishawaka-housing-authority","housing_authority","Mishawaka housing authority","mishawaka","","","single_source",["r03"],"Named in research as an unresearched local unit ('not found'); legal name, board and appointing authority not sourced. Placeholder.")
U("in-house","state_chamber","Indiana House of Representatives","","Districts 5, 6, 7, 8 and 21 include part of the county","","secondary",["bp_house","fc"],"Per fact-check, county ballots 2020-2026 include HD 5, 6, 7, 8 and 21 (HD 20 and HD 9 never appear).")
U("in-senate","state_chamber","Indiana Senate","","Districts 8, 9, 10 and 11 include part of the county","","secondary",["bp_senate","fc"],"Per fact-check, county ballots 2020-2026 include SD 8, 9, 10 and 11.")

# ---------------------------------------------------------------- offices
OFFICES = {}
def O(oid, unit, otype, title, district="", seats="1", elected="yes", partisan="yes", term="4", nxt="", st="official", srcs=(), notes=""):
    assert oid not in OFFICES, oid
    OFFICES[oid] = [oid, unit, otype, title, district, seats, elected, partisan, term, nxt, st, sid(srcs), notes]

RULING = ("April 2026: ABC57 reported a judge ruled the district method of electing commissioners violates the Indiana Constitution's free-and-equal-elections clause; "
          "no judge or court is named, appeal status unknown, and the Nov 2026 election was held under the district system. No term limit.")
for n, nxt in ((1,"2030"),(2,"2028"),(3,"2028")):
    O("county-commissioner-d%d"%n,"county","county_commissioner","County Commissioner, District %d"%n,str(n),"1","yes","yes","4",nxt,"official",["k26g","k24","abc57_ruling","fc"],
      "Elected only by voters in the district. "+RULING)
for d, nxt in zip("ABCDEFGHI",("2030","2030","2030","2028","2030","2028","2028","2030","2028")):
    O("county-council-%s"%d.lower(),"county","county_council_member","County Council, District %s"%d,d,"1","yes","yes","4",nxt,"official",["k26g","k24","ic36234","ic36232","fc"],
      "Nine single-member districts (IC 36-2-3-4(c); fact-check CONFIRMED). Whether the county formally opted in under IC 36-2-2-4(c) is unverified, but practice is consistent. Council is the county fiscal body.")
O("county-auditor","county","county_auditor","County Auditor","","1","yes","yes","4","2030","official",["k26g","k22","const_a6","fc"],"8-in-12 term limit (Art. 6 sec. 2).")
O("county-treasurer","county","county_treasurer","County Treasurer","","1","yes","yes","4","2028","official",["k24","k20","const_a6","fc"],"8-in-12 term limit.")
O("county-recorder","county","county_recorder","County Recorder","","1","yes","yes","4","2028","official",["k24","k20","const_a6","fc"],"8-in-12 term limit.")
O("county-clerk","county","county_clerk","Clerk of the Circuit Court","","1","yes","yes","4","2030","official",["k26g","k22","const_a6","fc"],"8-in-12 term limit.")
O("county-sheriff","county","county_sheriff","County Sheriff","","1","yes","yes","4","2030","official",["k26g","k22","const_a6","fc"],"8-in-12 term limit (WVPE confirmed Redman term-limited).")
O("county-coroner","county","county_coroner","County Coroner","","1","yes","yes","4","2028","official",["k24","k20","const_a6","fc"],"8-in-12 term limit.")
O("county-surveyor","county","county_surveyor","County Surveyor","","1","yes","yes","4","2028","official",["k24","k20","fc"],"Constitutional office but NOT on the Art. 6 sec. 2 term-limit list (fact-check CONFLICT-RESOLVED).")
O("county-assessor","county","county_assessor","County Assessor","","1","yes","yes","4","2030","official",["k26g","k22","brochure"],"Statutory office; exempt from the term limit per the state brochure.")
O("county-prosecutor","county","county_prosecutor","Prosecuting Attorney (60th Judicial Circuit)","","1","yes","yes","4","2030","official",["k26g","k22","fc"],"Not term-limited (fact-check: Art. 6 sec. 2 limit does not cover the prosecutor; Dvorak 2003-14 and Cotter 2015-26 each served 12 years).")
O("circuit-court-judge","sjc-courts","circuit_court_judge","Judge of the Circuit Court","","1","yes","yes","6","2028","official",["k22","k16","fc"],"Six-year term. Last on the ballot in 2022 (Broden, uncontested), not 2024 (fact-check CORRECTED: 2024 had the Probate judge race).")
O("probate-court-judge","sjc-courts","probate_court_judge","Judge of the Probate Court","","1","yes","yes","6","2030","official",["k24","k18","k12","fc"],"Six-year term; elected 2012, 2018, 2024 per canvasses.")
SUP = [("manier","Jenny Pitts Manier"),("sanford","Jeffrey L. Sanford"),("reagan","Margot Fisher Reagan"),("chapleau","Chapleau (first name not in sources)"),
       ("marnocha","Marnocha (first name not in sources)"),("steele","Steele (first name not in sources)"),("telloyan","Telloyan (first name not in sources)"),("woods","Woods (first name not in sources)")]
for key, nm in SUP:
    O("superior-court-judge-"+key,"sjc-courts","superior_court_judge","Judge of the Superior Court (seat identified by incumbent surname: %s)"%key.title(),"","1","yes","no","6","","official",["k24","k20","k18","ic333371","fc"],
      "Merit selection, not partisan election: a nominating commission sends five nominees to the governor; judge then faces yes/no retention votes at the general election (IC 33-33-71-43). St. Joseph is one of FOUR merit-selection counties (Lake, St. Joseph, Allen, Marion; fact-check CONTRADICTED the research's 'two'). 2021 law HEA 1453 changed the Lake/St. Joseph commissions; current IC 33-33-71 text not re-checked. Seat is identified by the incumbent's surname because the canvass lists retention by judge name. No Superior Court retention appears on the 2026 ballot. Retention cycle for this seat not resolved.")

for city, cu, nxt in (("south-bend","south-bend","2027"),("mishawaka","mishawaka","2027")):
    nm = "South Bend" if city=="south-bend" else "Mishawaka"
    O(city+"-mayor",cu,"mayor","Mayor of "+nm,"","1","yes","yes","4",nxt,"official",["k23","ic36452"],"Four-year term beginning noon Jan 1 after the election (IC 36-4-5-2).")
    O(city+"-clerk",cu,"city_clerk","City Clerk of "+nm,"","1","yes","yes","4",nxt,"official",["k23","ic364102","ic3_13_11"],"Elected citywide, four-year term (IC 36-4-10-2). Vacancies filled by party caucus (IC 3-13-11).")
    for d in range(1,7):
        O("%s-council-d%d"%(city,d),cu,"city_council_district","%s Common Council, District %d"%(nm,d),str(d),"1","yes","yes","4",nxt,"official",["k23","ic36463","ic3_13_11"]+(["sb_official"] if city=="south-bend" else []),"Vacancies filled by party caucus (IC 3-13-11).")
    O(city+"-council-at-large",cu,"city_council_at_large","%s Common Council, At-Large"%nm,"at-large","3","yes","yes","4",nxt,"official",["k23","ic36463"],"Each voter may vote for up to three at-large candidates.")

TWNS_OFF = {}
for t in TOWNSHIPS:
    tid = t.lower()+"-township"
    O(tid+"-trustee",tid,"township_trustee",t+" Township Trustee","","1","yes","yes","4","2030","official",["k26g","k22","k18"],"Trustee delivers services (poor relief, etc.); the board mainly approves budgets (Harris Township page).")
    O(tid+"-board",tid,"township_board_member",t+" Township Board","","3","yes","yes","4","2030","official",["k26g","k22","k18","wp_township"],"Three-member board. Winners in this file are the top three vote-getters (computed).")
O("penn-township-assessor","penn-township","township_assessor","Penn Township Assessor","","1","yes","yes","4","2030","official",["k26g","k22","k18"],"Only Penn Township has a township assessor on the county canvasses.")

# towns
O("walkerton-clerk-treasurer","walkerton","town_clerk_treasurer","Walkerton Clerk-Treasurer","","1","yes","yes","4","2027","official",["k23"])
O("walkerton-town-judge","walkerton","town_judge","Walkerton Town Judge","","1","yes","yes","4","2027","official",["k23"])
for w, nxt in ((1,"2030"),(2,"2030"),(3,"2027"),(4,"2027")):
    O("walkerton-council-ward-%d"%w,"walkerton","town_council_ward","Walkerton Town Council, Ward %d"%w,"Ward %d"%w,"1","yes","yes","4",nxt,"official",["k26g","k23","k22"],"Wards 1-2 are on the 2022/2026 cycle and wards 3-4 on the 2023 cycle per the canvasses.")
O("walkerton-council-at-large","walkerton","town_council_at_large","Walkerton Town Council, At-Large","at-large","","yes","yes","4","2027","official",["k23","k15"],"Seat count not printed in sources.")
O("osceola-clerk-treasurer","osceola","town_clerk_treasurer","Osceola Clerk-Treasurer","","1","yes","yes","4","2027","official",["k23"])
O("osceola-council","osceola","town_council_at_large","Osceola Town Council, At-Large","at-large","3","yes","yes","4","2027","official",["k23","r03"],"Three seats per research (2023). Council was elected by ward (Wards 1-3) in the 2019 canvass.")
O("roseland-clerk-treasurer","roseland","town_clerk_treasurer","Roseland Clerk-Treasurer","","1","yes","yes","4","2027","official",["k23"])
O("roseland-council","roseland","town_council_at_large","Roseland Town Council, At-Large","at-large","","yes","yes","4","","official",["k26g","k23","k22"],"Total seat count not printed. Seats appear on both 2022/2026 and 2023 cycles (one seat in 2022, two in 2023 per research); next election depends on the seat.")
O("new-carlisle-council","new-carlisle","town_council_at_large","New Carlisle Town Council, At-Large","at-large","3","yes","yes","4","","from_scan",["k26g","k15","k11"],"Vote-for-3 in the 2011 and 2015 canvasses (inferred seat count). Elections also appear in 2018/2019 and 2026.")
O("new-carlisle-clerk-treasurer","new-carlisle","town_clerk_treasurer","New Carlisle Clerk-Treasurer","","1","yes","yes","4","","from_scan",["k19","k15","k11"],"Susan Moffitt unopposed 2011, 2015, 2019; not on the 2023 or 2026 summaries. No terms encoded.")
O("north-liberty-council","north-liberty","town_council_at_large","North Liberty Town Council, At-Large","at-large","","yes","yes","4","","unofficial",["k26g"],"Seat count not printed; appears on the 2026 canvass only.")
O("lakeville-council","lakeville","town_council_at_large","Lakeville Town Council, At-Large","at-large","","yes","yes","4","","from_scan",["k15","k11"],"Appears in the 2011 and 2015 canvasses only; no terms encoded (OCR partly illegible).")
O("lakeville-clerk-treasurer","lakeville","town_clerk_treasurer","Lakeville Clerk-Treasurer","","1","yes","yes","4","","from_scan",["k15","k11"],"Appears in the 2011 and 2015 canvasses only; no terms encoded.")

# school boards
def SB(oid, unit, title, district, seats, nxt, srcs, notes="", otype="school_board_district"):
    O(oid, unit, otype, title, district, seats, "yes", "no", "4", nxt, "official", list(srcs)+["sea287"],
      "Nonpartisan on the ballot (all 2026 candidates listed NP; SEA 287 of 2025 allows party/independent labels, no primary). "+notes)
SBN = ["k26g","k24","k22","k20"]
for d, nxt in ((1,"2030"),(2,"2030"),(3,"2028"),(4,"2028"),(5,"2030")):
    SB("sbcsc-board-d%d"%d,"sbcsc","South Bend Community School Board, District %d"%d,str(d),"1",nxt,SBN+["k18","k16"])
SB("sbcsc-board-at-large","sbcsc","South Bend Community School Board, At-Large","at-large","","2028",SBN+["k16","abc57_sch24"],
   "Seat count left blank because of a conflict: research and ABC57 (2024) say 2 at-large seats; the 2016 canvass transcription says 3 elected. Terms are low confidence.","school_board_at_large")
SB("phm-board-at-large","phm","Penn-Harris-Madison School Board, At-Large","at-large","1","2030",SBN+["k18"],"","school_board_at_large")
SB("phm-board-harris","phm","Penn-Harris-Madison School Board, Harris Township","Harris Township","2","2030",SBN+["k18","k16"],"Two seats inferred from two election cycles (2016/2020/2024 and 2018/2022/2026).")
SB("phm-board-madison","phm","Penn-Harris-Madison School Board, Madison Township","Madison Township","1","2030",["k26g","k22","k18"])
SB("phm-board-penn","phm","Penn-Harris-Madison School Board, Penn Township","Penn Township","","2030",SBN+["k18","k16","r03"],
   "Seat count unresolved: one seat on the 2018/2022/2026 cycle; the 2020/2024 cycle had one candidate pair in 2020 but two winners in 2024. A Nov 2025 WNDU headline reports the board filled the vacated seat of former member Matt Chaffee (appointee not sourced).")
SB("school-city-mishawaka-board","school-city-mishawaka","School City of Mishawaka Board of Trustees (elected seats)","at-large","3","2030",["k26g","k24","k22","k20","k18","k16","mish_sch"],
   "Three elected at-large seats per research (1 seat on the 2018/2022/2026 cycle, 2 on the 2016/2020/2024 cycle).","school_board_at_large")
O("school-city-mishawaka-board-appointed","school-city-mishawaka","school_board_appointed","School City of Mishawaka Board of Trustees (appointed seats)","","2","no","no","4","","secondary",["mish_sch","r03"],"Two of five seats are appointed: one by the Common Council and one by the mayor (research; Wikipedia/local report). Appointee names not sourced.")
for tw in ("johnson","liberty","lincoln","polk"):
    SB("john-glenn-board-"+tw,"john-glenn","John Glenn School Board, %s Township"%tw.title(),"%s Township"%tw.title(),"","", ["k26g","k24","k22","k20","k18"],"Township name as printed on the county canvass; seat count unresolved (Liberty and Lincoln show two election cycles).")
SB("union-north-board-at-large","union-north","Union-North United School Board, At-Large","at-large","1","2028",["k24","k20","k16"],"","school_board_at_large")
SB("union-north-board-north","union-north","Union-North United School Board, North Township","North Township","1","2028",["k24","k20","k16"])
SB("union-north-board-union","union-north","Union-North United School Board, Union Township","Union Township","","2028",["k24","k20","k18","k16"],"Two election cycles appear (2016/2020/2024 and 2018).")
SB("new-prairie-board-at-large","new-prairie","New Prairie School Board, At-Large","at-large","2","2030",["k26g","k24","k22","k20","k18"],"Two cycles (2018/2022/2026 and 2020/2024). The 2026 contest is printed as 'At-Large / District 2'.","school_board_at_large")
for d, nxt in ((1,"2028"),(2,"2030"),(3,"2028")):
    SB("new-prairie-board-d%d"%d,"new-prairie","New Prairie School Board, District %d"%d,str(d),"1",nxt,["k26g","k24","k22","k20","k18"])
SB("laville-board-north","laville","LaVille School Board, North Township","North Township","1","2030",["k26g"],"Appears on the 2026 canvass only.")
SB("laville-board-union","laville","LaVille School Board, Union Township","Union Township","1","2030",["k26g"],"Appears on the 2026 canvass only.")

# state legislature
for n, nxt in ((5,"2028"),(6,"2028"),(7,"2028"),(8,"2028"),(21,"2028")):
    O("state-house-%d"%n,"in-house","state_house","Indiana House, District %d"%n,str(n),"1","yes","yes","2",nxt,"secondary",["bp_house","k26g","fc","ic3_13_5","r09"],
      "Two-year term; Indiana legislative vacancies are filled by party caucus (IC 3-13-5). District extends outside St. Joseph County for HD7 (since 2022), HD21 and possibly others.")
for n, nxt in ((8,"2028"),(9,"2028"),(10,"2028"),(11,"2030")):
    O("state-senate-%d"%n,"in-senate","state_senate","Indiana Senate, District %d"%n,str(n),"1","yes","yes","4",nxt,"secondary",["bp_senate","k26g","fc"],
      "Four-year term; only part of the district lies in St. Joseph County.")

# ---------------------------------------------------------------- terms
ELECTS = []   # dicts
MANUAL = []   # fully-specified rows
def E(office, year, person, party, srcs, **kw):
    if isinstance(srcs, str): srcs = [srcs]
    d = dict(office=office, year=year, person=person, party=party, srcs=list(srcs), st=None, note="", first_by=None,
             start=None, end=None, conf="high", sel="election")
    d.update(kw)
    if d["st"] is None:
        sts = [STATUS_OF[s] for s in d["srcs"] if s in STATUS_OF]
        d["st"] = "u" if "u" in sts else ("s" if "s" in sts else "o") if sts else "x"
    ELECTS.append(d)

def M(office, person, party, start, end, sel, first, st, conf, srcs, note=""):
    if isinstance(srcs, str): srcs=[srcs]
    MANUAL.append(dict(office=office, person=person, party=party, start=start, end=end, sel=sel, first=first, st=st, conf=conf, srcs=list(srcs), note=note))

# ---- county commissioners
E("county-commissioner-d1",2010,"Andy Kostielney","R","k10",first_by="appointment",start="2009",conf="medium",note="Research (search snippets) says appointed 2009, elected 2010, 2014, 2018; 2009 appointment mechanism and date not confirmed.")
E("county-commissioner-d1",2014,"Andy Kostielney","R","k14")
E("county-commissioner-d1",2018,"Andy Kostielney","R",["k18","r01"],end="2022-08",note="Resigned for a private job; GOP caucus replaced him Aug 2022 (WVPE).")
E("county-commissioner-d1",2022,"Carl Baxmeyer","R",["k22","wvpe_bax"],first_by="caucus",start="2022-08",note="Chosen by GOP caucus Aug 2022 to finish Kostielney's term, then elected Nov 2022; lost Nov 2026 (unofficial).")
E("county-commissioner-d1",2026,"Bill Redman","D",["k26g","mnc26"],note="Sheriff 2019-2026 (term-limited). Unofficial.")
E("county-commissioner-d2",2012,"Dave Thomas","D","k12")
E("county-commissioner-d2",2016,"Dave Thomas","D","k16",note="Fact-check: D2 was Democratic 2013-2020 (Dave Thomas).")
E("county-commissioner-d2",2020,"Derek Dieter","R","k20",note="Elected Surveyor in 2024.")
E("county-commissioner-d2",2024,"Rafael Morton","D","k24",note="Uncontested. Previously County Council District D.")
E("county-commissioner-d3",2012,"Marsha McClure","R",["k12","fc"],end="2014-11",conf="low",note="Won 51.26% in 2012 (fact-check). First name from the ballot. End date inferred only from Fleming's stated Nov 2014 start; reason McClure left is not in the sources.")
E("county-commissioner-d3",2016,"Deb Fleming","R",["k16","fc"],first_by="unknown",start="2014-11",conf="low",note="Start 'Nov 2014' is from the fact-check summary; how Fleming first took the seat (D3 was elected in 2012/2016) is not sourced, so first_selected_by is unknown.")
E("county-commissioner-d3",2020,"Deb Fleming","R",["k20","fc"],end="2024-01-31",note="Retired effective Jan 31, 2024 (fact-check; WVPE).")
E("county-commissioner-d3",2024,"Tony Hazen","R",["k24","fc","wvpe_hazen"],first_by="caucus",start="2024-01-20",
  note="CORRECTED: chosen by GOP caucus on Jan 20, 2024 (research said 2022). Only candidate at the caucus; resigned his Mishawaka council seat. Took office after Fleming's retirement effective 2024-01-31 (exact swearing-in date not sourced). Won the 2024 general. OVERLAP_OK")

# ---- county council
def council(letter, rows):
    for y, p, party, s, kw in rows:
        E("county-council-"+letter, y, p, party, s, **kw)
council("a",[(2010,"Mike Hamann","D","k10",{}),(2014,"Bobby K. Kruszynski Jr.","D","k14",{"note":"2014 canvass prints 'Bobby K Kruszynski'."}),(2018,"Bobby K. Kruszynski Jr.","D","k18",{}),
             (2022,"Joe Thomas","R","k22",{"note":"Lost Nov 2026 (unofficial)."}),(2026,"Mike Hamann","D",["k26g","mnc26"],{"note":"Unofficial."})])
council("b",[(2010,"Corey Noland","D","k10",{}),(2014,"Corey Noland","D","k14",{}),(2018,"Corey Noland","D","k18",{}),
             (2022,"Amy Drake","R","k22",{"note":"Won by 35 votes in 2022 (fact-check CONFIRMED); lost Nov 2026 (unofficial)."}),(2026,"Ranjan Rohatgi","D",["k26g","mnc26"],{"note":"Unofficial."})])
council("c",[(2010,"Dale R. Devon","R","k10",{"conf":"medium","note":"Name as printed on the OCR'd 2010 canvass."}),(2014,"Jamie O'Brien","R","k14",{"note":"Ballot name James A. (Jamie) O'Brien."}),
             (2018,"Richard Pfeil","R","k18",{}),(2022,"Dan Schaetzle","R",["k22","r01"],{"note":"Spelled Schaetzel in some sources. Lost the May 2026 GOP primary to Jamie O'Brien, who lost in Nov 2026."}),
             (2026,"Jan Cervelli","D",["k26g","mnc26"],{"note":"Unofficial."})])
council("d",[(2012,"Rafael Morton","D","k12",{}),(2016,"Rafael Morton","D","k16",{}),(2020,"Rafael Morton","D","k20",{"note":"Moved to Commissioner District 2 after the 2024 election."}),(2024,"Jenn Shabazz","D","k24",{})])
council("e",[(2010,"Mike Kruk","D","k10",{}),(2014,"Diana Hess","D","k14",{}),(2018,"Diana Hess","D","k18",{}),(2022,"Diana Hess","D","k22",{"note":"Not running 2026 (research)."}),
             (2026,"Lori Camp","D",["k26g","k26p","mnc26"],{"note":"Uncontested in Nov 2026; won the May 2026 D primary. Unofficial."})])
council("f",[(2012,"Dan Herbster","R","k12",{}),(2016,"Mark Telloyan","R","k16",{"note":"Ballot name Mark Peter Telloyan."}),(2020,"Mark Telloyan","R","k20",{}),(2024,"Randy Figg","R","k24",{})])
council("g",[(2012,"Mark Catanzarite","D","k12",{}),(2016,"Mark Catanzarite","D","k16",{}),(2020,"Mark Catanzarite","D","k20",{}),(2024,"Mark Catanzarite","D","k24",{})])
council("h",[(2010,"Robert McCahill","D","k10",{}),(2014,"Robert McCahill","D","k14",{}),(2018,"Joe Canarecci","D","k18",{}),(2022,"Bryan Tanner","D","k22",{"note":"Council president from Jan 2025 (elected with some Republican votes); re-elected president 6-3 Jan 6, 2026 (ABC57 via research)."}),
             (2026,"Bryan Tanner","D",["k26g","mnc26"],{"note":"Uncontested in Nov 2026. Unofficial."})])
council("i",[(2012,"Mark Root","R","k12",{}),(2016,"Mark Root","R","k16",{}),(2020,"Mark Root","R","k20",{}),(2024,"Andy Rutten","R","k24",{})])

# ---- county row officers
def row(office, rows):
    for y, p, party, s, kw in rows:
        E(office, y, p, party, s, **kw)
row("county-auditor",[(2010,"Peter Mullen","D","k10",{}),(2014,"Mike Hamann","D","k14",{}),(2018,"Mike Hamann","D","k18",{}),
    (2022,"John Murphy","D","k22",{"note":"Won by 667 votes (official; fact-check CORRECTED the research's ~663)."}),(2026,"Autumn Kaylor","D",["k26g","mnc26"],{"note":"Unofficial."})])
row("county-treasurer",[(2012,"Mike Kruk","D","k12",{}),(2016,"Mike Kruk","D","k16",{}),(2020,"Tim Swager","D","k20",{"note":"Uncontested."}),
    (2024,"Mary Beth Wisniewski","D",["k24","fc"],{"note":"Won 50.68%. CORRECTED: research called this a re-election as Treasurer; she was Recorder 2017-2024 (elected 2016, 2020) and was first elected Treasurer in 2024."})])
row("county-recorder",[(2012,"Phil Dotson","D","k12",{"note":"Ballot name Phillip G. Dotson."}),(2016,"Mary Beth Wisniewski","D","k16",{}),(2020,"Mary Beth Wisniewski","D","k20",{"note":"Uncontested."}),
    (2024,"Candace Brown","R",["k24","fc"],{"note":"Won by 81 votes (54,038 vs 53,957; official, fact-check CORRECTED the election-night count)."})])
row("county-clerk",[(2010,"Terri Rethlake","D","k10",{"note":"Ballot name Terri J. Rethlake."}),(2014,"Terri Rethlake","D","k14",{}),(2018,"Rita Glenn","D","k18",{"note":"Uncontested."}),
    (2022,"Amy Rolfes","R","k22",{"note":"Lost Nov 2026 (unofficial)."}),(2026,"Stephanie Ball","D",["k26g","mnc26"],{"note":"Unofficial."})])
row("county-sheriff",[(2010,"Mike Grzegorek","D",["k10","fc"],{"note":"Fact-check CONFLICT-RESOLVED: Grzegorek elected 2010 (54.05% over Jim Fox) and 2014 (unopposed)."}),(2014,"Mike Grzegorek","D",["k14","fc"],{}),
    (2018,"Bill Redman","D",["k18","fc"],{"note":"Won with 61.47% (fact-check CORRECTED the research's ~59%)."}),(2022,"Bill Redman","D","k22",{"note":"Term-limited; ran for Commissioner D1 in 2026."}),
    (2026,"Scott Ruszkowski","D",["k26g","mnc26","wvpe_ruszk"],{"note":"Unofficial. Fact-check CORRECTED: Ruszkowski is the sitting (not former) South Bend police chief; reported he will retire as chief at the end of 2026."})])
row("county-coroner",[(2012,"Randy Magdalinski","D","k12",{"note":"Uncontested."}),(2016,"Michael McGann","D","k16",{}),(2020,"Patricia Jordan","R","k20",{}),(2024,"Patricia Jordan","R",["k24","fc"],{"note":"Won 52.76% to 47.24% (official; fact-check CORRECTED the election-night count)."})])
row("county-surveyor",[(2012,"John McNamara","D","k12",{"note":"Ballot name John R. McNamara."}),(2016,"John McNamara","D","k16",{"note":"Uncontested."}),(2020,"John McNamara","D","k20",{"note":"Uncontested."}),
    (2024,"Derek Dieter","R",["k24","fc"],{"note":"Won by 172 votes (54,375 vs 54,203; fact-check CORRECTED). Previously Commissioner District 2."})])
row("county-assessor",[(2010,"Rosemary Mandrici","D","k10",{"note":"Ballot name Rosemary R. Mandrici; 2010 vote total marked OCR-uncertain."}),(2014,"Rosemary Mandrici","D","k14",{}),(2018,"Rosemary Mandrici","D","k18",{"note":"Uncontested."}),
    (2022,"Mike Castellon","R",["k22","fc"],{"note":"Opponent was Ted Booker (D) per official canvass. Previously Penn Township Assessor. Lost Nov 2026 (unofficial)."}),(2026,"Victor Cummings","D",["k26g","mnc26"],{"note":"Unofficial."})])
E("county-prosecutor",2010,"Michael Dvorak","D",["k10","wp_mdvorak"],first_by="election",start="2003-01",end=None,conf="medium",note="Prosecutor Jan 2003-Jan 2015 per Wikipedia (07); defeated the Republican incumbent in 2002 (opponent named inconsistently in research). Only the 2010 canvass is sourced here.")
ELECTS[-1]["end"]="2015-01"
E("county-prosecutor",2014,"Ken Cotter","D",["k14","fc"],note="Defeated Jeff Sanford (R) 54.29%. Prosecutor is not term-limited (fact-check).")
E("county-prosecutor",2018,"Ken Cotter","D","k18",note="Unopposed.")
E("county-prosecutor",2022,"Ken Cotter","D",["k22","wndu_cotter"],note="Uncontested; announced retirement Jan 2026.")
E("county-prosecutor",2026,"Amy Cressy","D",["k26g","mnc26"],note="Unofficial. Cotter's chief deputy per research.")

# ---- judges (6-year terms)
E("circuit-court-judge",2010,"Michael Gotsch","D","k10",note="Ballot name Michael G. Gotsch; uncontested.")
E("circuit-court-judge",2016,"John Broden","D","k16",note="Defeated Doug Bernacchi (R) 54.93%.")
E("circuit-court-judge",2022,"John Broden","D",["k22","fc"],note="Uncontested.")
E("probate-court-judge",2012,"Jim Fox","R","k12",note="Ballot name James N. Fox.")
E("probate-court-judge",2018,"Jason Cichowicz","D","k18")
E("probate-court-judge",2024,"Loris Zappia","R",["k24","fc"],note="Ballot name Loris Patrick Zappia; defeated incumbent Cichowicz 54.05%.")
def retain(key, year, srcn, name, party="", extra=""):
    E("superior-court-judge-"+key,year,name,party or "NP",srcn,note=("Retained by yes/no vote (county canvass). Start date assumed Jan 1 after the vote; original appointment not sourced. "+extra).strip(),first_by="unknown",conf="medium" if not extra else "low")
retain("manier",2018,"k18","Jenny Pitts Manier"); retain("manier",2024,"k24","Jenny Pitts Manier")
retain("sanford",2018,"k18","Jeffrey L. Sanford"); retain("sanford",2024,"k24","Jeffrey L. Sanford")
retain("reagan",2018,"k18","Margot Fisher Reagan")
X="Retained 2020, so a six-year term would reach retention in 2026, but no Superior Court retention is on the 2026 ballot (fact-check); the end date is unresolved and scheduled_end here is only a six-year assumption."
retain("chapleau",2020,"k20","Chapleau (first name not in sources)",extra=X)
retain("marnocha",2020,"k20","Marnocha (first name not in sources)",extra=X)
retain("steele",2024,"k24","Steele (first name not in sources)")
retain("telloyan",2024,"k24","Telloyan (first name not in sources)")
retain("woods",2024,"k24","Woods (first name not in sources)")

# ---- state legislators (explicit rows)
def L(office, person, party, start, end, sel, first, st, conf, srcs, note=""):
    M(office, person, party, start, end, sel, first, st, conf, srcs, note)
L("state-house-5","Craig Fry","D","1988","2012","election","election","x","medium",["wp_fry","r07"],"Wikipedia: 1988-2012; succeeded by Dale DeVon (open seat 2012). Exact dates not checked.")
L("state-house-5","Dale DeVon","R","2012-11","2026-11","election","election","x","high",["bp_house","k24","k22","r04"],"Elected 2012, 2014 (unopposed), 2016 (unopposed), 2018, 2020, 2022, 2024; lost Nov 2026 (unofficial).")
L("state-house-5","Alex Wait","D","2026-11","2028-11","election","election","u","medium",["bp_house","k26g","fc"],"Unofficial. Won 52.46% in the county (HD5 lies wholly in the county). Ballotpedia lists 'assumed office Nov 4, 2026'; term start pending certification.")
L("state-house-6","B. Patrick Bauer","D","1970-11","2020-11","election","election","x","medium",["wp_bauer","r07"],"Wikipedia: Nov 1970-Nov 2020; Speaker 2003-05 and 2007-11 per 07 (fact-check: likely off by a year; unverified).")
L("state-house-6","Maureen Bauer","D","2020-11","2026-11","election","election","x","medium",["bp_house","wp_mbauer"],"Succeeded her father; elected 2020 (uncontested), 2022 (uncontested), 2024. Sources give Nov 4 and Nov 16, 2020 start dates.")
L("state-house-6","Maureen Bauer","D","2026-11","2028-11","election","election","u","medium",["bp_house","k26g"],"Unofficial; uncontested in Nov 2026.")
L("state-house-7","David Niezgodski","D","2006-11","2016-11","election","election","x","medium",["wp_niez","r04"],"HD7 Nov 2006-Nov 2016, then State Senate District 10. Predecessor Thomas Kromkowski (dates not sourced).")
L("state-house-7","Joe Taylor III","D","2016-11","2020-11","election","election","x","medium",["bp_house","k16"],"Won 2016 (48.14%) and 2018 (Ballotpedia).")
L("state-house-7","Jake Teshka","R","2020-11","2026-11","election","election","x","high",["bp_house","k20","k22","k24"],"Elected 2020, 2022, 2024 (unopposed). Previously South Bend Common Council District 5.")
L("state-house-7","Jake Teshka","R","2026-11","2028-11","election","election","u","low",["bp_house","k26g","fc"],"UNOFFICIAL and narrow: county portion Teshka 9,881 vs Oliver Davis 9,840 (50.10/49.90); HD7 extends outside the county so district totals are unverified (Ballotpedia 10,394-10,102; Wikipedia 10,460-10,213). Describe as leading narrowly.")
L("state-house-8","Michael Dvorak","D","1986-11","2002-11","election","election","x","medium",["wp_mdvorak","r07"],"Won 1986 by defeating a three-term Republican incumbent; later County Prosecutor.")
L("state-house-8","Ryan Dvorak","D","2002-11","2026-11","election","election","x","high",["bp_house","wp_rdvorak","r04"],"Succeeded his father in Nov 2002.")
L("state-house-8","Ryan Dvorak","D","2026-11","2028-11","election","election","u","medium",["bp_house","k26g"],"Unofficial; 66.45% in the county (research's 66.5 CORRECTED to 66.4/66.45).")
L("state-house-21","Jackie Walorski","R","2005-01","2010-11","election","election","x","medium",["wp_walorski","r07"],"Indiana House 21st district Jan 2005-Nov 2010; later U.S. Representative.")
L("state-house-21","Tim Wesco","R","2010-11","2026-11","election","election","x","high",["bp_house","k24","r04"],"First elected 2010. District includes only a small part of St. Joseph County.")
L("state-house-21","Tim Wesco","R","2026-11","2028-11","election","election","u","medium",["bp_house","k26g"],"Unofficial.")
L("state-senate-8","Jim Arnold","D","","2016-11","election","election","x","low",["bp_senate"],"Incumbent in 2012 (58.3%); did not seek re-election in 2016. Start date before 2012 not sourced.")
L("state-senate-8","Mike Bohacek","R","2016-11","2028-11","election","election","x","high",["bp_senate","k24","k20"],"Elected 2016, 2020, 2024; scheduled_end=2028-11.")
L("state-senate-9","Ryan Mishler","R","2004-11","2028-11","election","election","x","high",["bp_senate","wp_mishler","k24"],"Since 2004 per Wikipedia; unopposed 2012, 2016, 2024; scheduled_end=2028-11.")
L("state-senate-10","John Broden","D","","2016-11-09","election","election","x","low",["bp_senate","r04"],"Incumbent in 2012; did not seek re-election in 2016. Start date not sourced.")
L("state-senate-10","David Niezgodski","D","2016-11-09","2028-11","election","election","x","high",["bp_senate","wp_niez","k24"],"Senate since Nov 9, 2016; elected 2016, 2020, 2024; scheduled_end=2028-11.")
L("state-senate-11","Linda Rogers","R","2018-11","2026-11","election","election","x","medium",["bp_senate","r04"],"First elected 2018; re-elected 2022; lost the May 2026 GOP primary to Brian Schmutzler (county portion 55.75% to 44.25%). Pre-2018 holder not sourced.")
L("state-senate-11","Gabrianna Gratzol","D","2026-11","2030-11","election","election","u","medium",["bp_senate","k26g","fc"],"UNOFFICIAL; open seat. County portion 55.58%; district-wide 51.4% (19,450 to 18,381) per Ballotpedia.")

# ---- South Bend mayors (33; Wikipedia list; years as given)
SBM = [
 (1,"William G. George","1865","1868","R","unknown",""),(2,"Louis Humphreys","1868","1872","R","unknown",""),(3,"William Miller","1873","1876","R","unknown",""),
 (4,"Alexander N. Thomas","1877","1878","R","unknown",""),(5,"Lucius G. Tong","1878","1880","R","unknown",""),(6,"Levi J. Ham","1880","1884","D","unknown",""),
 (7,"George W. Loughman","1884","1888","R","unknown",""),(8,"William H. Longley","1888","1892","D","unknown","CONFLICT (low): list table says 1888-1892; sidebar says 1884-88."),
 (9,"David R. Leeper","1892","1894","D","unknown",""),(10,"D. B. J. Schafer","1894","1898","R","unknown",""),
 (11,"Schuyler Colfax III","1898","1902","R","unknown","Colfax article says 1898-1901; list says 1898-1902."),
 (12,"Edward J. Fogarty","1902","1910","D","unknown","Spelled 'Fogary' in the Wikipedia sidebar."),(13,"Charles L. Goetz","1910","1914","D","unknown",""),
 (14,"Fred W. Keller","1914","1918","I","unknown","Only Independent mayor in the list."),(15,"Franklin R. Carson","1918-01","1922","R","unknown",""),
 (16,"Eli F. Seebirt","1922","1926","R","unknown",""),(17,"Chester R. Montgomery","1926","1930","D","unknown",""),(18,"William Riley Hinkle","1930","1935","D","unknown",""),
 (19,"George W. Freyermuth","1935","1938","R","unknown",""),(20,"Jesse I. Pavey","1938","1945","D","unknown",""),(21,"F. Kenneth Dempsey","1945","1947","D","unknown",""),
 (22,"George A. Schock","1947","1952","D","unknown",""),(23,"John Alden Scott","1952","1956","R","unknown",""),
 (24,"Edward F. Voorde","1956-01-01","1960-09-02","D","unknown","Died in office Sep 2, 1960."),
 (25,"Frank J. Bruggner","1960-09","1964","D","unknown","Acting mayor after Voorde's death; how he was selected (council, caucus, succession rule) was not confirmed. Did not seek election in 1963. OVERLAP_OK (month-precision start; Voorde died Sep 2, 1960)."),
 (26,"Lloyd M. Allen","1964","1972","R","election","Elected 1963 and re-elected 1967 (58%). Last Republican mayor."),
 (27,"Jerry Miller","1972","1975","D","election","CONFLICT (low): table says 1972-1975; sidebar says 1972-85. Elections of Nov 1971 and Nov 1975 imply Miller served to Dec 1975."),
 (28,"Peter Nemeth","1976","1980","D","election","Elected 1975. Wikipedia table dates for Miller/Nemeth appear to overlap; Nov 1975 election implies Jan 1976 start."),
 (29,"Roger Parent","1980-01","1988-01-03","D","election","Elected 1979 and 1983."),
 (30,"Joe Kernan","1988-01-03","1997-01-03","D","election","Elected 1987, 1991, 1995; resigned after election as Lt. Governor in 1996. The 'Jan 3' take-office dates conflict with the normal noon-Jan-1 start (fact-check)."),
 (31,"Steve Luecke","1997-01-03","2012-01-01","D","appointment","CONFLICT (low): Wikipedia infobox/list say to Jan 1, 2012; body text says 'until 2011'. Council member since 1988; appointed unanimously by the council when Kernan became Lt. Governor (Wikipedia, single source; council-vs-caucus mechanism not confirmed by a second source). Then elected 1999, 2003, 2007."),
 (32,"Pete Buttigieg","2012-01-01","2020-01-01","D","election","Elected 2011 and 2015."),
 (33,"James Mueller","2020-01-01","","D","election","Elected 2019 and 2023; scheduled_end=2027-12-31."),
]
for n, nm, s, e, p, sel, nt in SBM:
    conf = "low" if ("CONFLICT" in nt or n in (24,25) or sel=="appointment") else ("medium" if n<=23 or n==26 else "high")
    first = sel if sel!="election" else "election"
    sr = ["wp_mayors"] + (["wp_mayoral"] if n>=26 else []) + (["wp_luecke","r02"] if n==31 else []) + (["k23","k19"] if n==33 else []) + (["k15","k11"] if n==32 else []) + (["fc"] if n in (31,30,33) else [])
    stx = "x"
    M("south-bend-mayor", nm, p, s, e, sel, first, stx, conf, sr, ("No. %d in the Wikipedia list. "%n)+nt)

# ---- South Bend clerk & council
E("south-bend-clerk",2011,"John Voorde","D","k11",note="Former city clerk and councilman (WNDU obituary Sep 2026 per research).")
E("south-bend-clerk",2015,"Kareemah Fowler","D","k15",end="2019-07",note="Resigned July 2019 after the filing deadlines; remained on the Nov 2019 ballot unopposed (10,660 votes, official canvass) but did not serve that term.")
M("south-bend-clerk","Dawn Jones","D","2019-08-15","2019-12-31","caucus","caucus","x","high",["abc57_jones"],"Chosen by Democratic precinct-chair special caucus Aug 15, 2019 (seven ballots; beat Lisa Plencer on the last ballot).")
M("south-bend-clerk","Dawn Jones","D","2020-01-01","2023-12-31","caucus","caucus","x","low",["abc57_tirado","r02"],"Research: a Jan 2020 caucus was to fill the new term (winner not confirmed), and Tirado coverage describes Jones as the 'previous clerk'. Encoded as continuing Jones; verify.")
E("south-bend-clerk",2023,"Bianca Tirado","D","k23",note="Elected 67.49%; took office Jan 1, 2024.")
sb = "south-bend-council-"
E(sb+"d1",2011,"Tim Scott","D","k11"); E(sb+"d1",2015,"Tim Scott","D","k15")
E(sb+"d1",2019,"Tim Scott","D","k19",end="2020",conf="low",note="CONFLICT (low): canvass shows Scott elected 2019 (term 2020-2023) but Wikipedia says Canneth Lee was 'elected 2020'; Scott's actual end date is unverified.")
E(sb+"d1",2023,"Canneth Lee","D",["k23","wp_sbcc","r02"],first_by="unknown",start="2020",conf="low",note="Wikipedia says elected 2020 (possibly mid-term replacement; mechanism not verified); uncontested in 2023. Council president per research.")
E(sb+"d2",2011,"Henry Davis Jr.","D","k11"); E(sb+"d2",2015,"Regina Preston","D","k15",note="Later Regina Williams-Preston.")
E(sb+"d2",2019,"Henry Davis Jr.","D","k19"); E(sb+"d2",2023,"Ophelia Gooden-Rodgers","D","k23")
E(sb+"d3",2011,"Valerie Schey","D","k11"); E(sb+"d3",2015,"Randy Kelly","D","k15")
E(sb+"d3",2019,"Sharon McBride","D","k19",conf="medium",note="Wikipedia (02) says first elected 2018; the canvass shows uncontested 2019. Earlier service unverified.")
E(sb+"d3",2023,"Sharon McBride","D","k23")
E(sb+"d4",2011,"Fred Ferlic","D","k11")
E(sb+"d4",2015,"Jo Broden","D","k15",conf="medium",note="Candidate line did not OCR; row inferred (unopposed Democratic primary nominee).")
E(sb+"d4",2019,"Troy Warner","D","k19",note="CONFLICT-RESOLVED: Warner won District 4 in 2019 (68.00%) and 2023 (uncontested); a 953mnc snippet mislabeled the seat at-large.")
E(sb+"d4",2023,"Troy Warner","D",["k23","wvpe_beid"],end="2026-05",note="Resigned in 2026 to become Mayor Mueller's chief of staff (exact date not sourced).")
M(sb+"d4","Heidi Beidinger","D","2026-05-20","","caucus","caucus","x","high",["wvpe_beid","wndu_beid","fc"],
  "CORRECTED: chosen May 20, 2026 by 4th District Democratic precinct chairs (7 voters, secret ballot) over Hodge Patel, Derrick Perry and Angela Smith; NOT elected in 2019 as the Wikipedia table says. Expected to serve through Dec 31, 2027; scheduled_end=2027-12-31. WNDU/Observer use 'Beidinger-Burnett'.")
E(sb+"d5",2011,"David Varner","R","k11"); E(sb+"d5",2015,"David Varner","R","k15")
E(sb+"d5",2019,"Jake Teshka","R","k19",end="2020",conf="low",note="Elected state representative (HD7) Nov 2020; council exit date not sourced (end year inferred).")
M(sb+"d5","Eli Wax","R","","2023-12-31","unknown","unknown","x","low",["r02","fc"],"Republican incumbent holding District 5 until his 2023 loss (fact-check: 'Eli Wax (R) later held D5'); how and when he took the seat is not sourced. OVERLAP_OK")
E(sb+"d5",2023,"Sherry Bolden-Simpson","D",["k23","fc"],note="Won by 38 votes (1,414 to 1,376; fact-check CORRECTED the research's 37). City page says first Democrat elected to the seat since 1962.")
E(sb+"d6",2011,"Oliver Davis","D","k11"); E(sb+"d6",2015,"Oliver Davis","D","k15")
E(sb+"d6",2019,"Sheila Niezgodski","D","k19"); E(sb+"d6",2023,"Sheila Niezgodski","D","k23")
al = sb+"at-large"
for y, ps, s in ((2011,[("Derek Dieter","D"),("Gavin Ferlic","D"),("Karen White","D")],"k11"),(2015,[("Gavin Ferlic","D"),("Karen White","D"),("John Voorde","D")],"k15"),
                 (2019,[("Karen White","D"),("Rachel Tomas Morgan","D"),("Lori Hamann","D")],"k19"),(2023,[("Karen White","D"),("Rachel Tomas Morgan","D"),("Oliver Davis","D")],"k23")):
    for p, party in ps:
        nt = ""
        if p=="Karen White": nt = "Wikipedia says first elected 1999; service 2000-2011 not verified, so the first sourced election (2011) is used."
        if y==2015 and p=="John Voorde": nt="Former city clerk (2012-2015)."
        E(al, y, p, party, s, note=nt)

# ---- Mishawaka
M("mishawaka-mayor","Joseph Canfield","","","1963","unknown","unknown","x","low",["mish_hist"],"Incumbent defeated in 1963 (city history page). Start and party not found.")
M("mishawaka-mayor","Margaret Prickett","R","1963","1979","election","election","x","low",["r03","r07","journal_prickett"],"'First woman mayor' is UNVERIFIED (research marks it unconfirmed). Elected 1963, four terms, lost 1979 to Bob Kovach; party presumed Republican (LOW-MED). Source range 1963-1979; Jan 1964 start inferred, not sourced.")
M("mishawaka-mayor","Bob Kovach","D","1980","1983","election","election","x","medium",["wndu_kovach","fc"],"CORRECTED/CONFLICT-RESOLVED: one term 1980-1983 (won 1979, did not seek re-election); the 'retired end of 2012' claim is wrong for the mayoralty. Also county commissioner and state senator.")
M("mishawaka-mayor","Bob Beutter","","1984","2003","election","election","x","medium",["wsbt_beutter","fc"],"CONFLICT-RESOLVED: 1984-2003 (five terms; city statement); ABC57's 1982 is impossible given Kovach served through 1983. Party still unconfirmed.")
M("mishawaka-mayor","Jeff Rea","","2004","2010","election","election","x","low",["wndu_wood","fc"],"Took office 2004 (fact-check); resigned in 2010 to lead the South Bend Regional Chamber. Party not confirmed.")
E("mishawaka-mayor",2011,"Dave Wood","R",["k11","wndu_wood"],first_by="unknown",start="2010",conf="medium",note="Finished Rea's term from 2010 (mechanism not sourced); described as the 21st mayor (single WNDU source, unverified). Elected 2011, 2015, 2019; unopposed 2023.")
E("mishawaka-mayor",2015,"Dave Wood","R","k15"); E("mishawaka-mayor",2019,"Dave Wood","R","k19"); E("mishawaka-mayor",2023,"Dave Wood","R","k23")
E("mishawaka-clerk",2011,"Debbie Ladyga-Block","D","k11",note="Research says 2023 was her 9th term (unverified); first sourced election 2011.")
for y, s in ((2015,"k15"),(2019,"k19"),(2023,"k23")): E("mishawaka-clerk",y,"Debbie Ladyga-Block","D",s)
mc = "mishawaka-council-"
E(mc+"d1",2011,"Woody Emmons","D","k11",note="Ballot name Dale (Woody) Emmons.")
for y, s in ((2015,"k15"),(2019,"k19"),(2023,"k23")): E(mc+"d1",y,"Woody Emmons","D",s)
E(mc+"d2",2011,"Mike Bellovich","R","k11"); E(mc+"d2",2015,"Mike Bellovich","R","k15"); E(mc+"d2",2019,"Mike Bellovich","R","k19")
E(mc+"d2",2023,"Matt Carroll","D","k23",note="Won 52.35% (591 to 538), unseating the Republican incumbent.")
E(mc+"d3",2011,"John Reisdorf","R","k11"); E(mc+"d3",2015,"Ross Deal","D","k15")
E(mc+"d3",2019,"Tony Hazen","R",["k19","k23","fc"],note="Re-elected uncontested in Nov 2023, then resigned his council seat in Jan 2024 on becoming county commissioner (fact-check).")
E(mc+"d3",2023,"Tony Hazen","R",["k23","fc"],end="2024-01")
MANUAL_FIX = True
M(mc+"d3","Lou Ann Hazen","R","2024-01","","caucus","caucus","x","medium",["fc","mish_council"],"CONFLICT-RESOLVED: Republican (fact-check). Seat vacated by a Republican is filled by an R caucus (IC 3-13-11); the caucus result itself was not found but the city roster lists her. Selection by caucus is inferred. She was the 2023 Republican candidate for Mishawaka clerk. scheduled_end=2027-12-31.")
E(mc+"d4",2011,"Marsha McClure","R","k11",conf="medium",note="Whether she left the council early after a Marsha McClure won commissioner District 3 in Nov 2012 is not sourced; scheduled term end used.")
E(mc+"d4",2015,"Kate Voelker","R","k15"); E(mc+"d4",2019,"Kate Voelker","R","k19")
E(mc+"d4",2023,"Kate Voelker","R","k23",note="Won 434 to 418 over Shelli Treely.")
E(mc+"d5",2011,"Mike Compton","D","k11"); E(mc+"d5",2015,"Mike Compton","D","k15"); E(mc+"d5",2019,"Mike Compton","D","k19")
E(mc+"d5",2023,"Tony Violi","D",["k23","fc"],note="Uncontested (607). Party resolved by fact-check (research had it unknown).")
E(mc+"d6",2011,"Ron Banicki","D","k11",note="Ballot name Ronald S. Banicki.")
for y, s in ((2015,"k15"),(2019,"k19")): E(mc+"d6",y,"Ron Banicki","D",s)
E(mc+"d6",2023,"Ron Banicki","D",["k23","fc"],note="Uncontested (286). Party resolved by fact-check.")
mal = "mishawaka-council-at-large"
for y, ps, s in ((2011,[("Dan Bilancio","R"),("Matt Mammolenti","D"),("John Roggeman","D")],"k11"),(2015,[("John Roggeman","D"),("Matt Mammolenti","D"),("Joe Canarecci","D")],"k15"),
                 (2019,[("Matt Mammolenti","D"),("Gregg Hixenbaugh","D"),("Maggie DeMaegd","R")],"k19"),(2023,[("Gregg Hixenbaugh","D"),("Matt Mammolenti","D"),("Lacy Hahn","D")],"k23")):
    for p, party in ps:
        nt = ""
        if p=="Matt Mammolenti" and y==2015: nt="Printed 'Mamolenti' in the OCR."
        if p=="Joe Canarecci" and y==2015: nt="Printed 'Camarecci' in the OCR."
        E(mal, y, p, party, s, note=nt)

# ---- towns
E("walkerton-council-ward-1",2018,"Tommi Weeks","R","k18",conf="medium")
E("walkerton-council-ward-1",2022,"Greg Payne","R","k22",note="Ballot names R Greg Payne (2022) and Robert Gregory Payne (2026).")
E("walkerton-council-ward-1",2026,"Greg Payne","R","k26g",note="Uncontested. Unofficial.")
E("walkerton-council-ward-2",2022,"Gene Reese","R","k22"); E("walkerton-council-ward-2",2026,"Christy Donlon","D","k26g",note="Defeated Rick Coffman (R) 56.40% to 43.60%. Unofficial.")
E("walkerton-council-ward-3",2023,"Joyce Joiner","R","k23",note="Uncontested.")
E("walkerton-council-ward-4",2023,"Karol Jackson","D","k23",note="Defeated Kyle Norris (R).")
E("walkerton-council-at-large",2023,"Jeff Fansler","R","k23",note="Uncontested; seat count not printed.")
E("walkerton-clerk-treasurer",2023,"Terri Buckmaster","D","k23",note="Uncontested.")
E("walkerton-town-judge",2023,"Daniel Chamberlin","R","k23",note="Uncontested.")
for p in ("Nicholas Hanlon","Joseph Nehls","Peter Quist"): E("osceola-council",2023,p,"R","k23")
E("osceola-clerk-treasurer",2023,"Tina Miller","R","k23",note="Ballot name Christina (Tina) Miller; defeated Denese Thornburg (D).")
E("roseland-council",2022,"Traci Newman","D","k22",conf="medium",note="Received 73 votes against a write-in (Mike Schalk, 31); seat count inferred as one.")
E("roseland-council",2023,"Mike Schalk","O","k23",note="Indiana Redemption Party (IRP). Two seats per research.")
E("roseland-council",2023,"Ryan Catanzarite","O","k23",note="Indiana Redemption Party (IRP).")
E("roseland-clerk-treasurer",2023,"Shane Williams-Inez","O","k23",note="Indiana Redemption Party (IRP); defeated Elizabeth McCombs (D) 55.70% to 44.30%.")
E("roseland-council",2026,"Julie Mudrovich","D","k26g",conf="low",note="Unofficial; 104 votes to Tom Clark (R) 59. Seat count not printed (assumed one; if two seats, Clark also wins).")
E("new-carlisle-council",2026,"Marcy Kauffman","D","k26g",conf="medium",note="Unofficial; top vote-getter (334). Three candidates; seat count not printed.")
E("new-carlisle-council",2026,"Dan Caruso","D","k26g",conf="low",note="Unofficial; 245 votes. Wins only if two or more seats were open; 2011/2015 canvasses show vote-for-3.")
E("new-carlisle-council",2026,"Marcel Lebbin","R","k26g",conf="low",note="Unofficial; 228 votes. Wins only if three seats were open; seat count not printed.")
E("north-liberty-council",2026,"Gerry Brown","R","k26g",conf="medium",note="Unofficial; 283 votes (two candidates; seat count not printed).")
E("north-liberty-council",2026,"Tom England","R","k26g",conf="low",note="Unofficial; 224 votes. Wins only if two or more seats were open.")

# ---- townships
TW = {
 "centre":   {"t":{2018:("Judith Galloway","R","k18"),2022:("Judith Galloway","R","k22"),2026:("Ron Baker","D","k26g")}},
 "clay":     {"t":{2018:("Mike Dobson","R","k18"),2022:("Sean O'Brien","D","k22"),2026:("Sean O'Brien","D","k26g")}},
 "german":   {"t":{2018:("Thomas McClanahan","D","k18"),2022:("Jennifer Robinson","D","k22"),2026:("Jennifer Robinson","D","k26g")}},
 "greene":   {"t":{2018:("Sandra Ort","R","k18"),2022:("Sandra Ort","R","k22"),2026:("Breanne Goodsell","R","k26g")}},
 "harris":   {"t":{2018:("Ken Lindsay","R","k18"),2022:("Ken Lindsay","R","k22"),2026:("Veronica Vos","D","k26g")}},
 "liberty":  {"t":{2018:("Sue Dittmar","R","k18"),2022:("Sue Dittmar","R","k22"),2026:("Emily Dittmar","R","k26g")}},
 "lincoln":  {"t":{2018:("John McGee","D","k18"),2022:("Charles Kulp","R","k22"),2026:("Charles Kulp","R","k26g")}},
 "madison":  {"t":{2018:("Scott Laidig","R","k18"),2022:("Scott Laidig","R","k22"),2026:("Terrie Bickel","R","k26g")}},
 "olive":    {"t":{2018:("Will Miller","R","k18"),2022:("Will Miller","R","k22"),2026:("Will Miller","R","k26g")}},
 "penn":     {"t":{2018:("Doris Portolese","R","k18"),2022:("Doris Portolese","R","k22"),2026:("Nancy Duncan","D","k26g")}},
 "portage":  {"t":{2018:("Sean Coleman","D","k18"),2022:("Jason Critchlow","D","k22"),2026:("Jason Critchlow","D","k26g")}},
 "union":    {"t":{2018:("Bill Stroup","R","k18"),2026:("Kelly Carrico","R","k26g")}},
 "warren":   {"t":{2018:("Steven Downey","D","k18"),2022:("Steven Downey","D","k22"),2026:("Anthony Vanoverberghe","D","k26g")}},
}
TNOTE = {("clay",2022):"Won by 19 votes (4,870 to 4,851).", ("penn",2026):"Defeated incumbent Doris Portolese. Unofficial.", ("centre",2026):"Defeated incumbent Judith Galloway. Unofficial.",
         ("harris",2026):"Defeated incumbent Ken Lindsay. Unofficial.", ("liberty",2026):"Uncontested; ballot name Emily Dittmar (previous trustee Sue A. Dittmar). Unofficial.",
         ("portage",2022):"Portage trustee in 2018 was Sean J. Coleman; why Critchlow rather than Coleman stood in 2022 is not in the sources."}
for tk, d in TW.items():
    for y, (p, party, s) in d["t"].items():
        E(tk+"-township-trustee", y, p, party, s, note=TNOTE.get((tk,y),""))
E("union-township-trustee",2022,"Kelly Carrico","R",["ballotready","r03"],st="x",conf="medium",
  note="2022 race lines absent from the county summary; Carrico is named as the sitting trustee (term ending 12/31/2026) by BallotReady via research; party from the uncontested 2026 canvass. Unofficial 2026 continuation below.")
# remove the 2018 Union 'Bill Stroup' -> remains; fix 2026 chain starts fresh
BOARD = {
 "centre": {2022:[("Thomas Lindenman","R"),("Dave Vandewalle","R"),("Richard Ziegler","R")], 2026:[("Christopher Bowman","D"),("Karla Kreczmer-Baker","D"),("Thomas Lindenman","R")]},
 "clay":   {2022:[("Mike Dobson","R"),("Michelle Shaw","D"),("Rob Thomas","R")], 2026:[("Michelle Shaw","D"),("Brett Maurer","D"),("Pat Richter","D")]},
 "german": {2022:[("Rudy Monterrosa","D"),("Kevin McClanahan","D"),("Mary Ellen McNeil","R")], 2026:[("Rudy Monterrosa","D"),("Thomas Zmyslo","D"),("Doloris Schosker","D")]},
 "greene": {2022:[("Todd Matthys","R"),("Kathryn Jaworski","R"),("Shane Whitmer","R")], 2026:[("Todd Matthys","R"),("Matthew Meert","R"),("Shane Whitmer","R")]},
 "harris": {2022:[("Karen Vargo","R"),("Bob Fox","R"),("Chuck Sulok","R")], 2026:[("Sharon Brinker","D"),("Ryan Callahan","D"),("Jacob Baska","D")]},
 "liberty":{2022:[("Tom McCormick","R"),("Bryan Albright","R"),("Joshua Albright","R")], 2026:[("Tom McCormick","R"),("Bryan Albright","R"),("Joshua Albright","R")]},
 "lincoln":{2022:[("James Christie","R"),("Kathleen Fox","R"),("Ethan Barden","R")], 2026:[("Christopher Winchell","R"),("Kelsi Sheaks","R"),("Ethan Barden","R")]},
 "madison":{2022:[("Kurt Laidig","R"),("Terrie Bickel","R"),("Richard Schmidt","R")], 2026:[("Sheila Laidig","R"),("Richard Schmidt","R"),("Kate Fischer","R")]},
 "olive":  {2022:[("Keith Batzel","R"),("Robert Middlebrook","D"),("Tim Creason","R")], 2026:[("Robert Middlebrook","D"),("Keith Batzel","R"),("Tim Creason","R")]},
 "penn":   {2022:[("Dave Schmidt","R"),("Kent Hizer","R"),("Kris Verash","R")], 2026:[("Joshua Lange","D"),("Doug Stutzman","R"),("Mark Voelker","R")]},
 "portage":{2022:[("Cheryl Ashe","D"),("Ryan Hill","D"),("Muhammad Shabazz II","D")], 2026:[("Cheryl Ashe","D"),("Muhammad Shabazz II","D"),("Ryan Hill","D")]},
 "union":  {2026:[("Harold Saunders","R"),("George Schafer","R"),("Ryan Schafer","R")]},
 "warren": {2022:[("Wendy Yuhasz","D"),("Eric Griffin","D"),("Anthony Marvel","D")], 2026:[("Scott Searfoss","D"),("Bobby Kruszynski","D"),("Wendy Yuhasz","D")]},
}
for tk, yrs in BOARD.items():
    for y, ps in yrs.items():
        s = "k26g" if y==2026 else "k22"
        for p, party in ps:
            E(tk+"-township-board", y, p, party, s, note="Top-three vote-getter (three seats); computed from the canvass.")
E("penn-township-assessor",2014,"Mike Castellon","R","k14",note="Penn Township Assessor; later County Assessor (2022).")
E("penn-township-assessor",2018,"Mike Castellon","R","k18")
E("penn-township-assessor",2022,"Cherie DeFreese","R","k22",note="Uncontested.")
E("penn-township-assessor",2026,"Cherie DeFreese","R","k26g",note="Uncontested. Unofficial.")

# ---- school boards
def sch(office, rows, base_note=""):
    for y, p, s, kw in rows:
        kw = dict(kw); kw.setdefault("party","NP"); kw.setdefault("conf","medium")
        E(office, y, p, kw.pop("party"), s, note=(kw.pop("note","") or base_note), **kw)
sch("sbcsc-board-d1",[(2018,"Ruth Warren","k18",{}),(2022,"Kate Lee","k22",{}),(2026,"Kevin Hawkins","k26g",{"note":"Unofficial; 58.04% in a three-way race."})])
sch("sbcsc-board-d2",[(2018,"Oletha Jones","k18",{}),(2022,"Mark Costello","k22",{}),(2026,"Mark Costello","k26g",{"note":"Uncontested. Unofficial."})])
sch("sbcsc-board-d3",[(2016,"Leslie Wesley","k16",{}),(2020,"Leslie Wesley","k20",{"note":"Won by 16 votes (6,064 to 6,048)."}),(2024,"Bill Sniadecki","k24",{"note":"Research reports a 2025 dispute over seating Sniadecki on the county library board (separate body)."})])
sch("sbcsc-board-d4",[(2016,"Dawn Jones","k16",{"note":"Uncontested."}),(2020,"Stephanie Ball","k20",{"note":"Won 43.32% to 43.04% (Annette Malone). Elected county Clerk (D) in 2026 (unofficial)."}),(2024,"Carlos Leyva","k24",{})])
sch("sbcsc-board-d5",[(2018,"Stuart Greene","k18",{"note":"Uncontested."}),(2022,"Stuart Greene","k22",{}),(2026,"John Paczesny","k26g",{"note":"Uncontested. Unofficial."})])
sch("sbcsc-board-at-large",[(2016,"Maritza Robles","k16",{"conf":"low","note":"2016 transcription shows 3 winners (seat-count conflict; see office row)."}),(2016,"John Anella","k16",{"conf":"low"}),
    (2016,"Jeanette McCullough","k16",{"conf":"low"}),(2020,"John Anella","k20",{"conf":"low"}),(2020,"Jeanette McCullough","k20",{"conf":"low"}),
    (2024,"Marcus Ellison","k24",{"conf":"low"}),(2024,"Jeanette McCullough","k24",{"conf":"low","note":"Board president as of Dec 2025 per research."})])
sch("phm-board-at-large",[(2018,"Chris Riley","k18",{}),(2022,"Dana Sullivan","k22",{}),(2026,"Dana Sullivan","k26g",{"note":"Uncontested. Unofficial."})])
sch("phm-board-harris",[(2016,"Gary Fox","k16",{"note":"Uncontested."}),(2018,"Angie Gates","k18",{"note":"Uncontested."}),(2020,"Clare Roach","k20",{"note":"Uncontested."}),(2022,"Chris Riley","k22",{}),
    (2024,"Gary Fox","k24",{}),(2026,"Chris Riley","k26g",{"note":"Uncontested. Unofficial. PHM board president per Wikipedia (date unclear)."})])
sch("phm-board-madison",[(2018,"Larry Beehler","k18",{}),(2022,"Larry Beehler","k22",{}),(2026,"Larry Beehler","k26g",{"note":"Uncontested. Unofficial."})])
sch("phm-board-penn",[(2016,"Jamie Woods","k16",{}),(2018,"Karyn Jaye Galloway","k18",{"note":"Uncontested."}),(2020,"Jamie Woods","k20",{}),(2022,"Matt Chaffee","k22",{"note":"Seat later vacated (WNDU Nov 2025: board filled the seat); successor not sourced."}),
    (2024,"Katie Bell","k24",{"note":"Ballot name Katie Inabnit Bell; one of two Penn winners in 2024."}),(2024,"Ryan McCullough","k24",{"note":"Incumbent per research; one of two Penn winners in 2024."}),
    (2026,"Jen Smoker","k26g",{"note":"Uncontested. Unofficial."})])
sch("school-city-mishawaka-board",[(2016,"Jeffery Emmons","k16",{}),(2018,"Holly Parks","k18",{"note":"Uncontested."}),(2020,"Angela Layman","k20",{}),(2020,"Mellissa Johnson","k20",{"note":"Ran unopposed in 2024 with Layman (research)."}),
    (2022,"Holly Parks","k22",{}),(2024,"Angela Layman","k24",{}),(2024,"Mellissa Johnson","k24",{}),(2026,"Holly Parks","k26g",{"note":"Uncontested. Unofficial."})])
sch("john-glenn-board-johnson",[(2020,"Ryan Knowlton","k20",{}),(2024,"Ryan Knowlton","k24",{})])
sch("john-glenn-board-liberty",[(2018,"William Groves","k18",{}),(2020,"Christian Mattix","k20",{}),(2022,"Christine Carson","k22",{}),(2024,"Christian Mattix","k24",{}),(2026,"Christine Carson","k26g",{"note":"Uncontested. Unofficial."})])
sch("john-glenn-board-lincoln",[(2018,"Daniel Drotar","k18",{}),(2020,"Robert Borlik","k20",{"note":"No Lincoln Township race on the 2024 canvass; successor not sourced."}),
    (2022,"Carissa Smith","k22",{"conf":"low","note":"Four candidates; top vote-getter (549). Seat count not printed; if two seats, Monica Kulp (469) also won."}),(2026,"Carissa Smith","k26g",{"note":"Unofficial."})])
sch("john-glenn-board-polk",[(2018,"Dennis Holland","k18",{}),(2020,"Jared Egger","k20",{}),(2022,"Todd McGaughey","k22",{}),(2024,"Jared Egger","k24",{}),(2026,"Todd McGaughey","k26g",{"note":"Uncontested. Unofficial."})])
sch("union-north-board-at-large",[(2016,"Daniel Zeiger","k16",{"conf":"low","note":"Name read with a (?) in the OCR."}),(2020,"Jared McQueen","k20",{}),(2024,"Jared McQueen","k24",{})])
sch("union-north-board-north",[(2016,"Thomas Smith","k16",{}),(2020,"Thomas Smith","k20",{}),(2024,"Andrew Doyle","k24",{})])
sch("union-north-board-union",[(2016,"Arden Balmer","k16",{}),(2018,"Karman Leash","k18",{}),(2020,"Arden Balmer","k20",{}),(2024,"Dawn Amor","k24",{"note":"Defeated incumbent Arden Balmer."})])
sch("new-prairie-board-at-large",[(2018,"Jason Demeyer","k18",{}),(2020,"Jill Smith","k20",{"conf":"low","note":"Three candidates; top vote-getter; seat count not printed."}),(2022,"Jason Demeyer","k22",{}),
    (2024,"Jill Smith","k24",{}),(2026,"Jason Demeyer","k26g",{"conf":"low","note":"Unofficial; contest printed as 'At-Large / District 2'."})])
sch("new-prairie-board-d1",[(2016,"Dale Groves","k16",{}),(2020,"Dale Groves","k20",{}),(2024,"Richard Shail","k24",{})])
sch("new-prairie-board-d2",[(2018,"Allen Williamson","k18",{}),(2022,"Richard Gadacz","k22",{}),(2026,"Richard Gadacz","k26g",{"note":"Uncontested. Unofficial."})])
sch("new-prairie-board-d3",[(2016,"Phillip King","k16",{}),(2020,"Phillip King","k20",{}),(2024,"Phillip King","k24",{})])
sch("laville-board-north",[(2026,"Thomas Strang","k26g",{"note":"Uncontested. Unofficial."})])
sch("laville-board-union",[(2026,"Bradley Sherman","k26g",{"note":"Unofficial; 60.67% to Arden Balmer."})])

# ---------------------------------------------------------------- stint builder
TERM_LEN = {}
for oid, o in OFFICES.items(): TERM_LEN[oid] = int(o[8])
NOV_MODE = {"state_house","state_senate"}

def term_dates(office, y_first, y_last):
    tl = TERM_LEN[office]
    return "%d-01-01" % (y_first+1), "%d-12-31" % (y_last+tl)

groups = defaultdict(list)
for e in ELECTS: groups[(e["office"], e["person"])].append(e)

TERMS = []
def worst(sts):
    if "u" in sts: return "unofficial"
    if "x" in sts: return "secondary"
    if "s" in sts: return "from_scan"
    return "official"
ORDER = {"low":0,"medium":1,"high":2}
for (office, person), rows in groups.items():
    rows.sort(key=lambda r: r["year"])
    tl = TERM_LEN[office]
    chains = []
    for r in rows:
        if chains:
            last = chains[-1][-1]
            if (r["year"] - last["year"] == tl and r["st"] != "u" and not r["start"] and last["st"] != "u" and not last["end"]):
                chains[-1].append(r); continue
        chains.append([r])
    for ch in chains:
        first, last = ch[0], ch[-1]
        s, e_sched = term_dates(office, first["year"], last["year"])
        start = first["start"] or s
        end = last["end"] or ""
        notes = []
        sched = None
        if not end:
            if e_sched > TODAY and last["st"] != "u":
                sched = e_sched; end = ""
            else:
                end = e_sched
        if last["st"] == "u": 
            # future term starting 2027-01-01
            pass
        yrs = ", ".join(str(r["year"]) for r in ch)
        notes.append("Elected %s." % yrs)
        if not first["start"] and not last["end"]:
            notes.append("Dates inferred from election year (standard Jan 1 start, %d-year term)." % tl)
        for r in ch:
            if r["note"] and r["note"] not in notes: notes.append(r["note"])
        if sched: notes.append("scheduled_end=%s" % sched)
        st = worst([r["st"] for r in ch])
        srcs = []
        for r in ch:
            for k in r["srcs"]:
                if k not in srcs: srcs.append(k)
        conf = min((r["conf"] for r in ch), key=lambda c: ORDER[c])
        TERMS.append(dict(office=office, person=person, party=first["party"] if all(r["party"]==first["party"] for r in ch) else last["party"],
                          start=start, end=end, sel=last["sel"], first=first["first_by"] or first["sel"], st=st, conf=conf, srcs=srcs, note=" ".join(notes)))

# legislators / mayors etc. (manual) -> add scheduled_end handling
for m in MANUAL:
    note = m["note"]
    TERMS.append(dict(office=m["office"], person=m["person"], party=m["party"], start=m["start"], end=m["end"], sel=m["sel"], first=m["first"],
                      st=STNAME.get(m["st"], m["st"]), conf=m["conf"], srcs=m["srcs"], note=note))

# State legislators: those whose scheduled end (YYYY-MM) is in the future should be 'current' (blank end)
for t in TERMS:
    if t["office"].startswith("state-") and t["end"] and t["st"] != "unofficial" and t["end"] > "2026-11" and "scheduled_end" in t["note"]:
        t["note"] = t["note"].replace("scheduled_end=%s" % t["end"], "").strip() + " scheduled_end=%s" % t["end"]
        t["end"] = ""
    elif t["office"].startswith("state-") and t["st"] == "unofficial":
        t["note"] += " scheduled_end=%s" % t["end"]
        # keep future-term end as scheduled
# unofficial rows: add 'unofficial' as-of note
for t in TERMS:
    if t["st"] == "unofficial" and "as of" not in t["note"]:
        t["note"] = t["note"].replace("Unofficial. ", "").replace(" Unofficial.", "").replace("Unofficial.", "")
        t["note"] += " Unofficial: based on 2026 general results as of 11/3/2026 9:07 PM EST (county summary); not certified as of 2026-11-07."
    t["note"] = re.sub(r"\s+", " ", t["note"]).strip()

# term_id
seen = defaultdict(int)
def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
def last_name(p):
    p = re.sub(r"\(.*?\)", "", p).strip()
    return slug(p.split()[-1] if p.split()[-1].lower() not in ("jr.","jr","ii","iii") else " ".join(p.split()[-2:]))
for t in TERMS:
    base = "%s__%s__%s" % (t["office"], last_name(t["person"]) or "unknown", (t["start"] or "unk")[:7])
    seen[base] += 1
    t["id"] = base if seen[base]==1 else "%s__%d" % (base, seen[base])

# ---------------------------------------------------------------- appointed boards
BOARDS = []
def B(bid, unit, name, decides, seats, appt, levies, st, srcs, notes=""):
    BOARDS.append([bid, unit, name, decides, seats, appt, levies, st, sid(srcs), notes])
B("sjc-board-of-health","sjc-board-of-health","St. Joseph County Board of Health","Sets policy for the county health department and appoints the county health officer.","9","7 seats appointed by the County Board of Commissioners; South Bend mayor (1 seat); Mishawaka mayor (1 seat)","","official",["boh","r01","r03"],
  "2026 roster: all 7 filled seats appointed by the Commissioners; the two mayor seats listed vacant. Commissioner appointments were criticized in 2022-23 WVPE reports. Taxing power not stated in sources.")
B("sjc-redevelopment-commission","county","St. Joseph County Redevelopment Authority / Commission","Redevelopment projects (detail not verified).","","County Board of Commissioners (members serve at its pleasure)","","single_source",["r01"],"From a search snippet only; membership size and legal form not verified.")
B("sjc-area-plan-commission","county","Area Plan Commission of St. Joseph County","County-wide zoning; approves redevelopment plans (per research).","","Not confirmed in sources","","single_source",["r01"],"Appointing authorities were not found.")
B("sjc-airport-authority","sjc-airport-authority","St. Joseph County Airport Authority","Runs South Bend International Airport.","4","County Board of Commissioners (all four members; bipartisan)","","secondary",["wp_airport","r01","r03"],"Taxing power not stated. A commissioner-appointed member (Kostielney) was named in 2022.")
B("sjcpl-board","sjcpl","St. Joseph County Public Library Board of Trustees","Governs the county public library.","7","County commissioners, county council and school corporations (e.g., SBCSC); exact split not found","","secondary",["libblog","mnc_lib","r03"],"Trustees serve four-year terms, up to four consecutive. A 2024-25 dispute over seating a nominee was reported. Library districts levy property tax in Indiana (not verified in sources).")
B("mphpl-board","mphpl","Mishawaka-Penn-Harris Public Library Board of Trustees","Governs the Mishawaka-Penn-Harris Public Library.","7","School City of Mishawaka board (2); County Council (2); County Commissioners (2); Penn-Harris-Madison school board (1)","","official",["mphpl"],"Taxing power not stated on the board page.")
B("transpo-board","transpo","Transpo (South Bend Public Transportation Corporation) board","Governs Transpo bus service.","","Not found (South Bend mayor/council historically, per research)","","single_source",["r03"],"Appointing detail and levy not found.")
B("south-bend-redevelopment-commission","south-bend","South Bend Redevelopment Commission","Redevelopment and tax-increment decisions for the city.","5 voting + 1 non-voting adviser","Mayor (3 voting members); Common Council (2 voting members); mayor appoints a non-voting school board adviser","","single_source",["sb_rdc"],"From a city-page snippet only (confidence medium).")
B("south-bend-board-public-works","south-bend","South Bend Board of Public Works and Safety","City works and public-safety administration (statutory board).","","Not in sources (IC 36-4-9-5: one board per city; a second-class city's council may split it into works and safety boards)","","secondary",["legalfix_bpw","ic36496"],"South Bend's actual setup and membership were not researched; statute text may be outdated.")
for bid, nm, dec, ap in [
    ("mishawaka-board-public-works","Mishawaka Board of Public Works and Safety (and Utility Board)","City public works and safety administration; utility oversight.","Not stated on city site"),
    ("mishawaka-plan-commission","Mishawaka Plan Commission","Land-use planning for the city.","Not fully stated; the Common Council has one appointee (Matt Carroll for 2026)"),
    ("mishawaka-redevelopment-commission","Mishawaka Redevelopment Commission","Redevelopment decisions.","Not stated on city site"),
    ("mishawaka-board-zoning-appeals","Mishawaka Board of Zoning Appeals","Zoning variances and appeals.","Not stated on city site"),
    ("mishawaka-parks-board","Mishawaka Parks and Recreation board","Parks and recreation.","Not stated on city site"),
    ("mishawaka-historic-preservation","Mishawaka Historic Preservation Commission","Historic preservation.","Not stated on city site"),
    ("mishawaka-traffic-commission","Mishawaka Traffic Commission","Traffic matters.","Not stated on city site")]:
    B(bid,"mishawaka",nm,dec,"",ap,"","official",["mish_site"],"City site lists the board but not its appointing authorities (a '2025 Appointing Authority Disclosures' document was not read).")
B("school-city-mishawaka-appointed","school-city-mishawaka","School City of Mishawaka appointed trustees (2 of 5 seats)","Two seats on the five-member school board.","2","Mishawaka Common Council (1); Mayor of Mishawaka (1)","","secondary",["mish_sch","r03"],"Reported by Wikipedia/local report in research.")

# ---------------------------------------------------------------- gaps
GAPS = [
 ["terms","County Council seat A-I membership before 2010 and commissioner/row-officer terms before 2010","Earliest sourced canvass is 2010; no pre-2010 county results in the research","Pull pre-2010 canvasses from the county Election Results page or Indiana SOS archive"],
 ["terms","County party control year by year 2004-2009","Not searched","Cross-check Wikipedia/IndyStar archives"],
 ["terms","Commissioner District 3 transition 2014: why Marsha McClure left and how Deb Fleming first took the seat (fact-check says 'served Nov 2014-Jan 31, 2024')","Not in any source read","WVPE/South Bend Tribune Nov 2014 coverage"],
 ["terms","Whether St. Joseph County formally opted in under IC 36-2-2-4(c) (nine-district council)","No resolution found; practice consistent","Commissioners' 2023 minutes"],
 ["terms","Exact swearing-in date for Tony Hazen (after Fleming's Jan 31, 2024 retirement)","Only the Jan 20, 2024 caucus date is sourced","Commissioners' minutes or WVPE Jan-Feb 2024"],
 ["terms","South Bend Common Council District 1: when Tim Scott left and how Canneth Lee took the seat (Wikipedia says 'elected 2020')","Conflict between canvass (Scott 2019) and Wikipedia (Lee 2020)","City Clerk records or South Bend Tribune 2020"],
 ["terms","South Bend Common Council District 5: how and when Eli Wax (R) succeeded Jake Teshka","Not sourced","City Clerk records"],
 ["terms","South Bend city clerk holder from Jan 2020 to Dec 2023 (Jan 2020 caucus winner)","Research could not confirm; encoded as Dawn Jones with low confidence","ABC57/WVPE Jan 2020 coverage; city clerk page"],
 ["terms","South Bend clerks before 2012 (Gammon, Blough, Duda, Roberts) and council members before 2012","Dates unreliable in snippets; no pre-2011 canvass for city offices","Wikipedia 1971-2007 sections; city archives"],
 ["terms","Mishawaka mayors: Manuel Fisher (first mayor after becoming a city, 1899) and Joseph Canfield start date; full list 1899-1963","Wikipedia has no list page; city history page is a fragment","Mishawaka-St. Joseph County Public Library history; city archives"],
 ["terms","Mishawaka mayors' parties (Beutter, Rea, Canfield) and Rea's exact dates","Not stated in sources","WSBT/Tribune obituaries; city records"],
 ["terms","Mishawaka council members before 2012; party of Marsha McClure's early departure","Earliest sourced canvass is 2011","County canvasses 2007 and earlier"],
 ["terms","Town officeholders: Lakeville, Indian Village, New Carlisle (clerk-treasurer and council 2018-2023), Osceola/Roseland/Walkerton before 2018, North Liberty before 2026","Canvass OCR partly illegible or towns absent; seat counts not printed","Town clerk-treasurers; county canvasses with seat counts"],
 ["terms","Winners of 2026 multi-seat town races (New Carlisle, North Liberty, Roseland): seat counts not printed","Canvass lists candidates without seat counts","Town clerk-treasurers; certified 2026 canvass"],
 ["terms","Union Township trustee 2022 race lines; Union township board 2022","Absent from the 2022 county summary text","Full 1,388-page 2022 canvass (doc 57716) or Indiana SOS archive"],
 ["terms","Township trustees and boards before 2018 (2014 and earlier); 2018 township boards","2018 board lists have uncaptured candidates; earlier years not encoded","Docs 60012/60006 re-read; Indiana SOS"],
 ["terms","School board members before 2016; PHM Penn Township seat count and the Nov 2025 appointee; SBCSC at-large seat count (2 vs 3); Mishawaka and John Glenn seat counts","Canvass shows candidates but not seats; conflicting transcriptions","School corporation board pages; Indiana DOE; county canvass headers"],
 ["terms","School City of Mishawaka appointed trustees (names, appointment dates)","Not sourced","School City of Mishawaka website"],
 ["terms","Superior Court judges: first names for Chapleau, Marnocha, Steele, Telloyan, Woods; identity of the single judge retained in 2022; why 2020-retained judges (Chapleau, Marnocha) do not appear on the 2026 ballot; whether Reagan is still serving; current number of judges (8 unverified)","Canvass lists surnames only; no judiciary roster read","courts.in.gov St. Joseph Superior Court roster and judicial selection page"],
 ["terms","Kromkowski (HD7 before 2006), Rogers' predecessor in SD11, pre-2012 incumbents in SD8 (Arnold) and SD10 (Broden); Superior start dates","Ballotpedia pages start in 2012","Indiana General Assembly archives"],
 ["terms","Official (certified) 2026 results for every 2026 row; HD7 and several town races are narrow","County canvass not yet posted as of 2026-11-07","Re-run after the county certifies the 2026 canvass (docs on sjcindiana.gov/2392/Election-Results)"],
 ["offices","Federal offices (U.S. House IN-2/IN-3 and Senate) are not encoded","Out of scope for this file; belongs with the federal/state edition data","Add to a separate federal terms file if wanted"],
 ["units","Housing authorities (South Bend, Mishawaka): legal names, boards, appointers","Research says 'not found'","HUD PHA database; city sites"],
 ["units","Transpo board appointers and levy; SJC Public Library appointer split; Area Plan Commission and Redevelopment Authority membership; Board of Public Works membership; county Election Board; Tax Adjustment/Property Tax Assessment Board of Appeals","Not researched or not found","County and city websites; Indiana Code"],
 ["units","Whether LaVille and Union-North United are separate corporations; New Prairie's county footprint; Indian Village governance","Not documented","IDOE school corporation list; Indiana Gateway unit directory"],
 ["units","Statutory class of South Bend and Mishawaka (second class) not directly confirmed against a city source","Research read only the 34,000 population band (IC 36-4-1-1)","City ordinance or IC 36-4-1-1 current text"],
 ["offices","Dates of the Apr 2026 ruling, court and appeal status on commissioner district elections","ABC57 names no judge or court; suit appears to originate in Marion County (fact-check)","Court docket; ABC57/IndyStar follow-ups"],
]

# ---------------------------------------------------------------- write
def w(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
        cw = csv.writer(f, lineterminator="\n"); cw.writerow(header); cw.writerows(rows)

w("units.csv", "unit_id,unit_type,name,parent_unit_ids,places_covered,website,status,source_ids,notes".split(","), UNITS)
w("offices.csv", "office_id,unit_id,office_type,title,district,seats,elected,partisan,term_years,next_election,status,source_ids,notes".split(","), list(OFFICES.values()))
rows = []
for t in sorted(TERMS, key=lambda t: (t["office"], t["start"] or "0", t["person"])):
    rows.append([t["id"], t["office"], t["person"], t["party"], t["start"], t["end"], t["sel"], t["first"], t["st"], t["conf"], sid(t["srcs"]), t["note"]])
w("terms.csv", "term_id,office_id,person,party,start,end,selected_by,first_selected_by,status,confidence,source_ids,notes".split(","), rows)
w("appointed_boards.csv", "board_id,unit_id,name,what_it_decides,seats,appointing_authorities,levies_tax,status,source_ids,notes".split(","), BOARDS)
w("gaps_gov.csv", "area,item,why_missing,how_to_fill".split(","), GAPS)
srows = [[SIDS[k], SRC[k][0], SRC[k][1], SRC[k][2], ACC, SRC[k][3], SRC[k][4]] for k in SRC_ORDER if k in USED]
# sources used by units/offices were registered through sid(); renumber stays stable since IDs assigned up-front
w("sources_gov.csv", "id,url,title,publisher,accessed,kind,notes".split(","), srows)
print("units", len(UNITS), "offices", len(OFFICES), "terms", len(rows), "boards", len(BOARDS), "gaps", len(GAPS), "sources", len(srows), "unused", [k for k in SRC_ORDER if k not in USED])
