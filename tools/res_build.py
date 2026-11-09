"""Build elections.csv / results.csv for the St. Joseph County edition from the
research transcriptions. Mechanical transcription: see planning/fact-check-report.md
for the corrections applied (logged in data/editions/st-joseph/_corrections_applied_results.md).
Run with plain `python` (needs res_raw.py beside it)."""
import re, csv, sys, os
from collections import OrderedDict, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from res_raw import parse

OUT = 'C:/Users/nickb/local-gov-guide/data/editions/st-joseph/'
DC = 'https://www.sjcindiana.gov/DocumentCenter/View/'

# ---------------------------------------------------------------- sources
SOURCES = [  # (key, url, title, publisher, kind, notes)
 ('60020', DC+'60020', '2010 Primary Election summary report (May 4, 2010)', 'St. Joseph County Election Board', 'primary', 'Scanned PDF read by OCR; summary pages 1-7. No official/unofficial stamp legible; run date 05/14/10.'),
 ('60019', DC+'60019', '2010 General Election summary report (Nov 2, 2010)', 'St. Joseph County Election Board', 'primary', 'Scanned PDF read by OCR; OFFICIAL RESULTS stamp; run date 11/16/10.'),
 ('60018', DC+'60018', '2011 Municipal Primary summary report (May 3, 2011)', 'St. Joseph County Election Board', 'primary', 'Scanned PDF read by OCR; no official/unofficial stamp legible; run date 05/17/11.'),
 ('60017', DC+'60017', '2011 Municipal General summary report (Nov 8, 2011)', 'St. Joseph County Election Board', 'primary', 'Scanned PDF read by OCR; run date 11/18/11; stamp not recorded.'),
 ('60016', DC+'60016', '2012 Primary Election summary report (May 8, 2012)', 'St. Joseph County Election Board', 'primary', 'Scanned PDF read by OCR; pages stamped Unofficial Results; run date 05/21/12.'),
 ('60015', DC+'60015', '2012 General Election summary report (Nov 6, 2012)', 'St. Joseph County Election Board', 'primary', 'Scanned PDF read by OCR; page 1 stamped OFFICIAL RESULTS, pages 2-4 stamped UNOFFICIAL RESULTS; run date 11/16/12.'),
 ('60014', DC+'60014', 'Official Precinct Tally Sheet, Mishawaka-area public question (2013)', 'St. Joseph County Election Board', 'primary', 'Scanned single page read by OCR; election date and question wording not printed; only the TOTALS row recorded.'),
 ('60013', DC+'60013', '2014 Primary Election summary report (May 6, 2014)', 'St. Joseph County Election Board', 'primary', 'Scanned PDF read by OCR; pages stamped Unofficial Results; run date 05/19/14.'),
 ('60012', DC+'60012', '2014 General Election summary report (Nov 4, 2014)', 'St. Joseph County Election Board', 'primary', 'Scanned PDF read by OCR; OFFICIAL RESULTS stamp; run date 12/09/14.'),
 ('60011', DC+'60011', '2015 Municipal Primary reports (May 5, 2015)', 'St. Joseph County Election Board', 'primary', 'Scanned PDF read by OCR; printed header reads UNOFFICIAL REPORTS; run date 05/15/15; countywide totals not on summary pages.'),
 ('60010', DC+'60010', '2015 Municipal General summary report (Nov 3, 2015)', 'St. Joseph County Election Board', 'primary', 'Scanned PDF read by OCR; run date 11/03/15 (election night).'),
 ('60009', DC+'60009', '2016 Primary Election results (May 3, 2016)', 'St. Joseph County Election Board', 'primary', 'Scanned PDF read by OCR; Official Results; run 05/13/16.'),
 ('60008', DC+'60008', '2016 General Election results (Nov 8, 2016)', 'St. Joseph County Election Board', 'primary', 'Scanned PDF read by OCR; Official Report; run 11/18/16.'),
 ('60007', DC+'60007', '2018 Primary Election Official Results (May 8, 2018)', 'St. Joseph County Election Board', 'primary', 'Scanned PDF read by OCR; stamped Official Results; run 05/18/18 02:04 PM. Numbers transcribed from this file.'),
 ('14947', DC+'14947', '2018 Primary results, second copy (May 8, 2018)', 'St. Joseph County Election Board', 'primary', 'Same run date/time as 60007 and same numbers where compared, but every page header reads UNOFFICIAL RESULTS. Used only as a cross-check.'),
 ('60006', DC+'60006', '2018 General Election Official Results (Nov 6, 2018)', 'St. Joseph County Election Board', 'primary', 'Scanned PDF read by OCR; Official Results; run 11/16/18.'),
 ('60005', DC+'60005', '2019 Municipal Primary Official Results (May 7, 2019)', 'St. Joseph County Election Board', 'primary', 'Scanned PDF read by OCR; Official Results; run 05/17/19.'),
 ('60004', DC+'60004', '2019 Municipal General Official Results (Nov 5, 2019)', 'St. Joseph County Election Board', 'primary', 'Scanned PDF read by OCR; Official Results; run 11/15/2019.'),
 ('37457', DC+'37457', '2020 Primary Election Official Results (held June 2, 2020)', 'St. Joseph County Election Board', 'primary', 'Text-layer PDF; Official Results dated 6/12/2020. Header prints "MAY 5, 2020"; election was held 2020-06-02 (fact-check D).'),
 ('60003', DC+'60003', 'SignedOfficialElectionResults (same 2020 primary as 37457)', 'St. Joseph County Election Board', 'primary', 'Scanned 96-page signed copy of the same 2020 primary canvass as 37457 (same registered/ballots/run date). Not encoded separately; one value differs (Teshka 2,651 here vs 2,650 in 37457).'),
 ('42820', DC+'42820', '2020 General Election Official Results (Nov 3, 2020)', 'St. Joseph County Election Board', 'primary', 'Text-layer PDF; Official Results dated 11/13/2020.'),
 ('60001', DC+'60001', '2022 Primary Election Official Results (May 3, 2022)', 'St. Joseph County Election Board', 'primary', 'Text-layer PDF; marked Official, dated 5/13/2022; footer shows 211 of 215 precincts.'),
 ('57716', DC+'57716', '2022 General Election Official Results (Nov 8, 2022)', 'St. Joseph County Election Board', 'primary', 'Text-layer PDF (OCR-quality text); Official Results dated 11/18/2022; summary pages 1-9 of 1,388.'),
 ('59108', DC+'59108', '2023 Municipal Primary Official Results (May 2, 2023)', 'St. Joseph County Election Board', 'primary', 'Text-layer PDF; Official Results dated 5/12/2023.'),
 ('60569', DC+'60569', '2023 Municipal General Official Results (Nov 7, 2023)', 'St. Joseph County Election Board', 'primary', 'Text-layer PDF; Official Results dated 11/17/2023.'),
 ('62697', DC+'62697', '2024 Primary results (May 7, 2024)', 'St. Joseph County Election Board', 'primary', 'Linked on the county page as Official but header reads "Unofficial Results for All Absentee and All Vote Centers", dated 5/7/2024 8:01 PM (election night).'),
 ('64951', DC+'64951', '2024 General Election FINAL Official Results (Nov 5, 2024)', 'St. Joseph County Election Board', 'primary', 'Scanned image PDF read by OCR; FINAL Official Results (Central Count) dated 11/15/2024.'),
 ('71640', DC+'71640', '2026 Primary Election Official Results (May 5, 2026)', 'St. Joseph County Election Board', 'primary', 'Text-layer PDF; Official Results dated 5/15/2026 (Central Count).'),
 ('73081', DC+'73081', '2026 General Election results (Nov 3, 2026), UNOFFICIAL', 'St. Joseph County Election Board', 'primary', 'Text-layer PDF; header "Unofficial Results 11/3/2026 9:07:47 PM"; official canvass not posted as of 2026-11-07.'),
 ('page2392', 'https://www.sjcindiana.gov/2392/Election-Results', 'Election Results (County Election Board page listing the canvass PDFs)', 'St. Joseph County Election Board', 'primary', 'Index page the DocumentCenter files were taken from.'),
 ('wp-sb', 'https://en.wikipedia.org/wiki/Mayoral_elections_in_South_Bend,_Indiana', 'Mayoral elections in South Bend, Indiana', 'Wikipedia', 'secondary', 'Source of pre-2010 South Bend mayoral general and primary results (via research/02-south-bend.md section 4). Wikipedia cites the Indiana Election Division and newspapers; figures not checked against a primary record.'),
 ('bp-hd5', 'https://ballotpedia.org/Indiana_House_of_Representatives_District_5', 'Indiana House of Representatives District 5', 'Ballotpedia', 'secondary', 'District-wide totals (research/09).'),
 ('bp-hd6', 'https://ballotpedia.org/Indiana_House_of_Representatives_District_6', 'Indiana House of Representatives District 6', 'Ballotpedia', 'secondary', 'District-wide totals (research/09).'),
 ('bp-hd7', 'https://ballotpedia.org/Indiana_House_of_Representatives_District_7', 'Indiana House of Representatives District 7', 'Ballotpedia', 'secondary', 'District-wide totals (research/09).'),
 ('bp-hd8', 'https://ballotpedia.org/Indiana_House_of_Representatives_District_8', 'Indiana House of Representatives District 8', 'Ballotpedia', 'secondary', 'District-wide totals (research/09).'),
 ('bp-hd21', 'https://ballotpedia.org/Indiana_House_of_Representatives_District_21', 'Indiana House of Representatives District 21', 'Ballotpedia', 'secondary', 'District-wide totals (research/09).'),
 ('bp-sd8', 'https://ballotpedia.org/Indiana_State_Senate_District_8', 'Indiana State Senate District 8', 'Ballotpedia', 'secondary', 'District-wide totals (research/09).'),
 ('bp-sd9', 'https://ballotpedia.org/Indiana_State_Senate_District_9', 'Indiana State Senate District 9', 'Ballotpedia', 'secondary', 'District-wide totals (research/09).'),
 ('bp-sd10', 'https://ballotpedia.org/Indiana_State_Senate_District_10', 'Indiana State Senate District 10', 'Ballotpedia', 'secondary', 'District-wide totals (research/09).'),
 ('bp-sd11', 'https://ballotpedia.org/Indiana_State_Senate_District_11', 'Indiana State Senate District 11', 'Ballotpedia', 'secondary', 'District-wide totals (research/09).'),
 ('factcheck', 'planning/fact-check-report.md', 'Fact-check report: St. Joseph County civic guide research files (2026-11-07)', 'Project fact-check pass (internal)', 'derived', 'Adversarial check of the results transcriptions against the county PDFs; source of the corrections logged in _corrections_applied_results.md.'),
]
SRC = OrderedDict()
for i, s in enumerate(SOURCES, 1):
    SRC[s[0]] = 'RES-%03d' % i

def sid(*keys):
    return ';'.join(SRC[k] for k in keys)

# ---------------------------------------------------------------- elections
# id: (h2 prefix for section lookup, date, type, scope, doc key, [extra source keys], status, registered, ballots, turnout, notes)
EL = OrderedDict()
def add_el(eid, date, typ, scope, doc, extra, status, reg, bal, turn, notes):
    EL[eid] = dict(election_id=eid, date=date, type=typ, scope=scope, doc=doc, extra=extra,
                   status=status, registered=reg, ballots_cast=bal, turnout_pct=turn, notes=notes)

add_el('2010p','2010-05-04','primary','countywide','60020',[], 'official',197007,30023,15.24,
  'Run date 05/14/10; no official/unofficial stamp legible on the scan (treated as the county canvass). Ballots cast excludes 43 paper ballots printed separately. 227 of 227 precincts. Federal races and precinct-committee races not encoded.')
add_el('2010g','2010-11-02','general','countywide','60019',[], 'official',194453,80580,41.44,
  'OFFICIAL RESULTS stamp, run date 11/16/10. 230 of 230 precincts. Federal races not encoded; over/under-vote lines not recorded. Court headings above four judicial retention lines and the final public question did not OCR.')
add_el('2011p','2011-05-03','municipal_primary','South Bend and Mishawaka (141 precincts)','60018',[], 'official',112004,18026,16.09,
  'Report EL45, run date 05/17/11; no official/unofficial stamp legible. Registered voters and ballots are for the municipal electorate. Ballots cast by party not printed.')
add_el('2011g','2011-11-08','municipal_general','South Bend, Mishawaka and towns (144 precincts)','60017',[], 'official',115258,24228,21.02,
  'Report EL45, run date 11/18/11; stamp not recorded. Registered voters and ballots are for the municipal electorate. Two straight-party blocks (50-precinct Mishawaka-area and 94-precinct South Bend) are encoded as separate contests; the Mishawaka-area label is inferred from the precinct page header. Straight-party columns left blank for that reason. Ballot name of the 2011 South Bend Republican mayoral nominee is Wayne Curry (fact-check D).')
add_el('2012p','2012-05-08','primary','countywide','60016',[], 'unofficial',200917,32729,16.29,
  'Pages stamped Unofficial Results, run date 05/21/12. Republican ballots 19,082 (58.30%), Democratic 13,647 (41.70%). 222 of 222 precincts. No township, municipal, school or public-question contests in this summary.')
add_el('2012g','2012-11-06','general','countywide','60015',[], 'unofficial',198046,111622,56.36,
  'Run date 11/16/12 (REPORT-EL45). Page 1 is stamped OFFICIAL RESULTS and pages 2-4 UNOFFICIAL RESULTS in the same report; the page of each row was not recorded, so every 2012 general row is labelled unofficial (conservative). 222 of 222 precincts. Federal races not encoded.')
add_el('2013s','2013','special','Mishawaka-area public question (29 precincts listed)','60014',[], 'official',22222,4129,18.58,
  'Official Precinct Tally Sheet. Date not printed on the page; the year 2013 comes from the file series, not the sheet. Question wording not printed. Registered voters cover Mishawaka precincts and two Penn Township precincts only. Only the TOTALS row is recorded; percent is share of YES+NO computed from the totals.')
add_el('2014p','2014-05-06','primary','countywide','60013',[], 'unofficial',199357,12930,6.49,
  'Pages stamped Unofficial Results, run date 05/19/14. Republican ballots 4,550 (35.19%), Democratic 8,380 (64.81%). 222 of 222 precincts. Federal race not encoded.')
add_el('2014g','2014-11-04','general','countywide','60012',[], 'official',202025,58825,29.12,
  'OFFICIAL RESULTS (REPORT-EL45) stamp, run date 12/09/14. 222 of 222 precincts. Straight-party Democratic and Libertarian counts were garbled by OCR and derived from printed percentages. Federal race not encoded.')
add_el('2015p','2015-05-05','municipal_primary','South Bend and Mishawaka','60011',[], 'unofficial','','','',
  'Printed header reads UNOFFICIAL REPORTS, run date 05/15/15, although the county lists the file as the primary result. Countywide registered voters, ballots cast and turnout are not on the summary pages (per-precinct statistics only).')
add_el('2015g','2015-11-03','municipal_general','South Bend, Mishawaka and towns (131 precincts)','60010',[], 'unofficial',116309,15937,13.70,
  'Run date 11/03/15 (election night); stamp not recorded, so labelled unofficial. Registered voters printed as "116.309" (normalized). Straight-party counts are for the municipal ballot area.')
add_el('2016p','2016-05-03','primary','countywide','60009',[], 'official',207841,70919,34.12,
  'Official Results, run 05/13/16, 224 of 224 precincts. Republican ballots 37,816 (53.32%), Democratic 33,093 (46.66%), nonpartisan 12 (0.02%, OCR-uncertain). Federal and presidential races not encoded.')
add_el('2016g','2016-11-08','general','countywide','60008',[], 'official',212720,113070,53.15,
  'Official Report, run 11/18/16, 224 of 224 precincts. Federal races not encoded. For statewide and multi-county contests winner is left blank: the county tally cannot decide them.')
add_el('2018p','2018-05-08','primary','countywide','60007',['14947'], 'official',170853,35945,21.04,
  'Transcribed from 60007 (stamped Official Results, run 05/18/18 02:04 PM); 14947 has the same run time and numbers but every page header reads UNOFFICIAL RESULTS. Republican ballots 12,572 (34.98%), Democratic 23,373 (65.02%). 225 of 225 precincts. Precinct-committee contests and federal races not encoded.')
add_el('2018g','2018-11-06','general','countywide','60006',[], 'official',193482,94199,48.69,
  'Official Results, run 11/16/18, 225 of 225 precincts. Federal races not encoded. Township board = vote for up to 3.')
add_el('2019p','2019-05-07','municipal_primary','South Bend and Mishawaka (130 precincts)','60005',[], 'official',97316,14646,15.05,
  'Official Results, run 05/17/19. Registered voters and ballots are for the municipal electorate. Republican ballots 1,678 (11.46%), Democratic 12,968 (88.54%).')
add_el('2019g','2019-11-05','municipal_general','South Bend, Mishawaka and towns (127 precincts)','60004',[], 'official',106860,20816,19.48,
  'Official Results, run 11/15/2019. Registered voters and ballots are for the municipal electorate. South Bend mayor: official canvass 9,406 / 5,429 (total 14,835), replacing the Wikipedia figures 9,437 / 5,445 (fact-check D). Straight-party counts are for the municipal ballot area.')
add_el('2020p','2020-06-02','primary','countywide','37457',['60003'], 'official',191025,37445,19.60,
  'Held 2020-06-02 (rescheduled from May 5 by the Governor\'s March 20, 2020 order); the PDF header still prints May 5, 2020. Official canvass dated 6/12/2020. Docs 37457 and 60003 are the same election and are encoded once, from 37457. Party distribution of ballots: public question only 519 (1.39%), Republican 11,424 (30.51%), Democratic 25,502 (68.11%). Page 2 and 5 of 60003 print turnout 18.60 / 19.60; arithmetic gives 19.60.')
add_el('2020g','2020-11-03','general','countywide','42820',[], 'official',197179,116688,59.18,
  'Official Results dated 11/13/2020. Turnout percent computed (ballots/registered); header percent was cut off in extraction. Office labels for recorder, treasurer, coroner, surveyor, commissioner 2/3 and council D/F/G/I were inferred from page order in the transcription.')
add_el('2022p','2022-05-03','primary','countywide','60001',[], 'official',194268,14483,7.46,
  'Marked Official, dated 5/13/2022, but the footer shows 211 of 215 precincts reporting. Turnout computed. Democratic ballots 7,439, Republican 7,044. Republican state-convention delegate and Democratic precinct-committee races not encoded.')
add_el('2022g','2022-11-08','general','countywide','57716',[], 'official',196917,72678,36.91,
  'Official Results dated 11/18/2022 (summary pages 1-9 of a 1,388-page file; text layer is OCR-quality). Union Township Trustee and New Carlisle Town Council At-Large headings have no captured vote lines.')
add_el('2023p','2023-05-02','municipal_primary','South Bend, Mishawaka and towns','59108',[], 'official',114089,10408,9.12,
  'Official Results dated 5/12/2023. Registered voters = municipal electorate only (114,089), so turnout is not comparable with countywide elections. Turnout computed. Ballots: nonpartisan 86, Democratic 8,380, Republican 1,942.')
add_el('2023g','2023-11-07','municipal_general','South Bend, Mishawaka and towns','60569',[], 'official',115191,17139,14.88,
  'Official Results dated 11/17/2023. Registered voters = municipal electorate only. Official South Bend mayor 7,878 / 2,939 (news reports gave 7,877 / 2,938) and clerk Tirado 7,323 (fact-check D).')
add_el('2024p','2024-05-07','primary','countywide','62697',[], 'unofficial',201540,23843,11.83,
  'Linked on the county page as Official, but the file header reads "Unofficial Results for All Absentee and All Vote Centers", dated 5/7/2024 8:01 PM (election night); no separate official summary was found. Unofficial as of 2024-05-07 20:01. Democratic ballots 9,852, Republican 13,991. Precinct-committee and Republican state-convention delegate races not encoded.')
add_el('2024g','2024-11-05','general','countywide','64951',[], 'official',205991,112329,54.53,
  'FINAL Official Results (Central Count) dated 11/15/2024; scanned image read by OCR. Race totals were cross-checked against candidate sums except the items flagged in row notes. Write-in candidates for president were not encoded (federal).')
add_el('2026p','2026-05-05','primary','countywide','71640',[], 'official',191552,26598,13.89,
  'Official Results dated 5/15/2026 (Central Count). Republican ballots 11,668, Democratic 14,930. Republican state-convention delegate and Democratic precinct-committee races not encoded.')
add_el('2026g','2026-11-03','general','countywide','73081',[], 'unofficial',193942,77909,40.17,
  'UNOFFICIAL as of 2026-11-03 21:07 EST (header "Unofficial Results 11/3/2026 9:07:47 PM", Central Count, all absentee and all vote centers). All values may change; the official canvass was not posted as of 2026-11-07. Public question wording not captured.')

# ---- pre-2010 South Bend mayor (research/02-south-bend.md section 4)
PRE = [  # year, [(candidate, party, votes, pct)], total note
 (1963, [('Lloyd M. Allen','R',None,None),('Paul Krueper','D',None,None)], 'Vote counts not found.'),
 (1967, [('Lloyd M. Allen','R',None,58.0),('Eugene Pajakowki','D',None,36.0)], 'Percentages as rounded integers on the source; votes not found; remaining 6% is independent/other candidates; margin about 10,500 votes. Lloyd M. Allen was the incumbent.'),
 (1971, [('Jerry Miller','D',None,None),('Janet Allen','R',None,None)], 'Vote counts not found; over 48,000 voted; margin about 10,500.'),
 (1975, [('Peter Nemeth','D',23689,68.89),('John Slafkosky','R',9804,28.51),('R. Kronewittier','I',893,2.60)], 'Total votes 34,386.'),
 (1979, [('Roger Parent','D',None,None),('H. Chris Overgaard','R',None,None)], 'Vote counts not found; source describes roughly a 2-to-1 margin; total 29,196 (lowest since 1925).'),
 (1983, [('Roger Parent','D',20734,61.54),('Howard Goodhew','R',11995,35.70),('K. Brookins','O',962,2.86)], 'Total votes 33,691. Percentages as listed on the source; they sum to 100.1 from rounding. Brookins ran for the American Party. Roger Parent was the incumbent.'),
 (1987, [('Joe Kernan','D',17030,53.0),('Carl Baxmeyer','R',15104,47.0)], 'Total votes 32,134. Source gives percentages as whole numbers (53 / 47).'),
 (1991, [('Joe Kernan','D',16134,76.49),('Sylvia Shelton','R',4958,23.51)], 'Total votes 21,092. Joe Kernan was the incumbent.'),
 (1995, [('Joe Kernan','D',14309,82.17),('Mike Waite','R',3106,17.84)], 'Total votes 17,415. Percentages as listed on the source; they sum to 100.01. Joe Kernan was the incumbent.'),
 (1999, [('Stephen Luecke','D',13678,68.39),('Steven Bradley','R',6321,31.61)], 'Total votes 19,999. Stephen Luecke was the incumbent.'),
 (2003, [('Stephen Luecke','D',10598,71.68),('Thomas Schmidt','R',4188,28.32)], 'Total votes 14,786. Stephen Luecke was the incumbent.'),
 (2007, [('Stephen Luecke','D',12355,62.14),('Juan Manigault','R',7471,37.57),('T. Brown','O',58,0.29)], 'Total votes 19,884. T. Brown was a write-in candidate (Green). Stephen Luecke was the incumbent. Percentages as listed on the source; they sum to 100.00 only with 37.57.'),
]
PRE_PRIM = [  # year, party, [(cand, votes, pct)]
 (1999,'D',[('Stephen J. Luecke',8265,61.49),('John Voorde',4214,31.35),('Kevin C. Horton',855,6.36),('Zbigniew "Ziggy" Borowski',108,0.80)],'Total 13,442. Stephen Luecke was the incumbent.'),
 (1999,'R',[('Steven Clark Bradley',1195,81.18),('Marvin Townsend',277,18.82)],'Total 1,472.'),
 (2003,'D',[('Stephen J. Luecke',7480,100.0)],'Unopposed.'),
 (2003,'R',[('Thomas R. Schmidt',1497,100.0)],'Unopposed.'),
 (2007,'D',[('Stephen J. Luecke',4781,79.12),('William F. Davis',1262,20.88)],'Stephen Luecke was the incumbent.'),
 (2007,'R',[('Juan Manigault',1690,66.77),('Terry Miller',841,33.23)],''),
]
for yr,_,_ in PRE:
    add_el('%dg'%yr, str(yr), 'municipal_general', 'South Bend (mayor only in the source)', 'wp-sb', [], 'secondary','','','',
           'Date not in the source (year only). Only the South Bend mayoral race was recorded for this election; turnout and registration not recorded. Source: Wikipedia, which cites the Indiana Election Division and newspapers.')
for yr in (1999,2003,2007):
    add_el('%dp'%yr, str(yr), 'municipal_primary', 'South Bend (mayor only in the source)', 'wp-sb', [], 'secondary','','','',
           'Date not in the source (year only). Only the South Bend mayoral primaries were recorded for this election; turnout and registration not recorded. Source: Wikipedia.')
