"""Build the money-area data files for the St. Joseph County edition.

Reads only the downloaded raw data under sources/money/ (treated as data) and writes
data/editions/st-joseph/{budgets,budget_breakdowns,tax_rates,debt,cf_state}.csv,
sources_money.csv and gaps_money.csv.

Run:  python -P -E tools/build_money.py
"""
import csv, io, os, re, sys, zipfile, collections

ROOT = 'C:/Users/nickb/local-gov-guide/'
SRC = ROOT + 'sources/money/'
OUT = ROOT + 'data/editions/st-joseph/'
os.makedirs(OUT, exist_ok=True)


def write_csv(name, header, rows):
    with open(OUT + name, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(header)
        for r in rows:
            assert len(r) == len(header), (name, r)
            w.writerow(r)
    print('wrote', name, len(rows))


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def money(x):
    """plain dollars, no $ or commas, 2 decimals only when needed"""
    x = round(x, 2)
    if abs(x - round(x)) < 0.005:
        return str(int(round(x)))
    return '%.2f' % x


def rd_psv(fn):
    with open(SRC + fn, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='|'))


# ---------------------------------------------------------------- units
# Provisional unit ids (slug convention); map to units.csv ids when merged.
UNITS = {
    'ST. JOSEPH COUNTY': ('county-st-joseph', 'St. Joseph County'),
    'SOUTH BEND CIVIL CITY': ('city-south-bend', 'City of South Bend (civil city)'),
    'MISHAWAKA CIVIL CITY': ('city-mishawaka', 'City of Mishawaka (civil city)'),
    'INDIAN VILLAGE CIVIL TOWN': ('town-indian-village', 'Indian Village'),
    'LAKEVILLE CIVIL TOWN': ('town-lakeville', 'Town of Lakeville'),
    'NEW CARLISLE CIVIL TOWN': ('town-new-carlisle', 'Town of New Carlisle'),
    'NORTH LIBERTY CIVIL TOWN': ('town-north-liberty', 'Town of North Liberty'),
    'OSCEOLA CIVIL TOWN': ('town-osceola', 'Town of Osceola'),
    'ROSELAND CIVIL TOWN': ('town-roseland', 'Town of Roseland'),
    'WALKERTON CIVIL TOWN': ('town-walkerton', 'Town of Walkerton'),
    'CENTRE TOWNSHIP': ('township-centre', 'Centre Township (state data: Centre)'),
    'CLAY TOWNSHIP': ('township-clay', 'Clay Township'),
    'GERMAN TOWNSHIP': ('township-german', 'German Township'),
    'GREENE TOWNSHIP': ('township-greene', 'Greene Township'),
    'HARRIS TOWNSHIP': ('township-harris', 'Harris Township'),
    'LIBERTY TOWNSHIP': ('township-liberty', 'Liberty Township'),
    'LINCOLN TOWNSHIP': ('township-lincoln', 'Lincoln Township'),
    'MADISON TOWNSHIP': ('township-madison', 'Madison Township'),
    'OLIVE TOWNSHIP': ('township-olive', 'Olive Township'),
    'PENN TOWNSHIP': ('township-penn', 'Penn Township'),
    'PORTAGE TOWNSHIP': ('township-portage', 'Portage Township'),
    'UNION TOWNSHIP': ('township-union', 'Union Township'),
    'WARREN TOWNSHIP': ('township-warren', 'Warren Township'),
    'JOHN GLENN SCHOOL CORPORATION': ('school-john-glenn', 'John Glenn School Corporation'),
    'MISHAWAKA CITY SCHOOL CORPORATION': ('school-mishawaka', 'School City of Mishawaka'),
    'PENN-HARRIS-MADISON-SCHOOL CORPORATION': ('school-phm', 'Penn-Harris-Madison School Corporation'),
    'SOUTH BEND COMMUNITY SCHOOL CORPORATION': ('school-sbcsc', 'South Bend Community School Corporation'),
    'UNION-NORTH UNITED SCHOOL CORPORATION': ('school-union-north', 'Union-North United School Corporation'),
    'MISHAWAKA PUBLIC LIBRARY': ('library-mishawaka', 'Mishawaka-Penn-Harris Public Library (state data: Mishawaka Public Library)'),
    'NEW CARLISLE PUBLIC LIBRARY': ('library-new-carlisle', 'New Carlisle Public Library'),
    'ST. JOSEPH COUNTY PUBLIC LIBRARY': ('library-sjcpl', 'St. Joseph County Public Library'),
    'WALKERTON PUBLIC LIBRARY': ('library-walkerton', 'Walkerton Public Library'),
    'SOUTH BEND PUBLIC TRANSPORTATION': ('special-sb-transpo', 'South Bend Public Transportation Corporation'),
    'ST. JOSEPH AIRPORT': ('special-airport', 'St. Joseph County Airport Authority (state data: St. Joseph Airport)'),
    'ST. JOSEPH SOLID WASTE MANAGEMENT': ('special-solid-waste', 'St. Joseph County Solid Waste Management District'),
    'SOUTH BEND REDEVELOPMENT COMMISSION': ('special-sb-redevelopment', 'South Bend Redevelopment Commission'),
    'ST JOSEPH CO REGIONAL WATER SEWER': ('special-regional-water-sewer', 'St. Joseph County Regional Water and Sewer District'),
    'St. Joseph Redevelopment Authority': ('special-redevelopment-authority', 'St. Joseph Redevelopment Authority'),
}
UNITS_UPPER = {k.upper(): v for k, v in UNITS.items()}


def uid(name):
    return UNITS_UPPER[name.upper()][0]


COUNTY, SB, MISH = 'county-st-joseph', 'city-south-bend', 'city-mishawaka'

# ---------------------------------------------------------------- sources
SOURCES = [
    ('MON-001', 'https://gateway.ifionline.org/public/download.aspx', 'Indiana Gateway for Government Units: Budget Data download (Form 4B, 2012-2026, filtered to county code 71)', 'Indiana DLGF / Gateway (ifionline.org)', '2026-11-07', 'dataset',
     'Saved as sources/money/gateway_budget_county71_2012-2026.psv. The original download repeated every row 5 times; de-duplicated here (4,736 unique rows, no conflicting duplicates). Adopted column used.'),
    ('MON-002', 'https://gateway.ifionline.org/public/download.aspx', 'Indiana Gateway: Annual Financial Report, Disbursements by Fund and Department (2023, 2024; county code 71)', 'Indiana SBOA / Gateway (ifionline.org)', '2026-11-07', 'dataset',
     'Saved as sources/money/gateway_afr_disbursements_{2023,2024}_county71.psv.'),
    ('MON-003', 'https://gateway.ifionline.org/public/download.aspx', 'Indiana Gateway: Annual Financial Report, Detailed Receipts (2023, 2024; county code 71)', 'Indiana SBOA / Gateway (ifionline.org)', '2026-11-07', 'dataset',
     'Saved as sources/money/gateway_afr_receipts_{2023,2024}_county71.psv. Includes non-operating receipts (borrowings, transfers, pass-through collections).'),
    ('MON-004', 'https://gateway.ifionline.org/public/download.aspx', 'Indiana Gateway: Annual Financial Report, Debt (2024; county code 71)', 'Indiana SBOA / Gateway (ifionline.org)', '2026-11-07', 'dataset',
     'Saved as sources/money/gateway_afr_debt_2024_county71.psv. Year-end principal balance by debt class.'),
    ('MON-005', 'https://southbendin.gov/budget/', 'City of South Bend: Budget page (fetched 2026-11-07)', 'City of South Bend', '2026-11-07', 'primary',
     'States roughly $280.7M debt outstanding as of 2026-09-04; reserves about $22-23M; 2027 budget adopted 2026-10-12 (no dollar total stated); revenue shares (property tax about 25%, income taxes about 11%, charges for services about 30%).'),
    ('MON-006', 'https://docs.southbendin.gov/WebLink/0/edoc/367727/08-16-2023%202024%20Budget%20Hearing%20Overview%20Kick%20Off.pdf', 'South Bend 2024 Budget Hearing Overview Kick Off (2023-08-16)', 'City of South Bend', '2026-11-07', 'primary',
     'Revenue by source table (2020-2024) transcribed from PDF text extraction in research/05-budgets.md; row-to-label alignment was reconstructed from raw text order. PDF not re-read in this pass.'),
    ('MON-007', 'https://www.abc57.com/news/the-south-bend-common-council-approves-2025-budget', 'South Bend Common Council approves 2025 budget (2024-10-15)', 'ABC57', '2026-11-07', 'news',
     'All-funds totals: about $417M (2024), more than $424M (2025). Police over $60M; Fire just under $49M; transit $14M. Confirmed by fact-check report.'),
    ('MON-008', 'https://www.wndu.com/2025/09/10/st-joseph-county-council-discusses-2026-budget-public-hearing', 'St. Joseph County Council discusses 2026 budget public hearing', 'WNDU', '2026-11-07', 'news',
     '"just over $90 million" balanced budget; auditor: general fund $97 million, "39% of the total budget". Quotes confirmed exact; interpretation unverified (fact-check report).'),
    ('MON-009', 'https://www.wvpe.org/wvpe-news/2025-10-15/county-council-oks-2026-budget-with-directors-salary-increase', 'County council OKs 2026 budget with director\'s salary increase', 'WVPE', '2026-11-07', 'news',
     'County 2026 budget passed 5-4 on 2025-10-14.'),
    ('MON-010', 'https://mishawaka.in.gov/download/?wpdmdl=13302', 'City of Mishawaka 2026 budget book', 'City of Mishawaka', '2026-11-07', 'primary',
     'Summary for all funds 2024/2025/2026 approved (civil city, excludes utilities); general-fund department totals for Fire, Police and Controller re-checked against the book text in this pass.'),
    ('MON-011', 'https://mishawaka.in.gov/download/?wpdmdl=1274', 'City of Mishawaka 2022 budget book', 'City of Mishawaka', '2026-11-07', 'primary', 'Source of 2020-2022 general fund figures cited in research/05-budgets.md (not re-extracted in this pass).'),
    ('MON-012', 'https://mishawaka.in.gov/download/?wpdmdl=2737', 'City of Mishawaka 2021 budget book', 'City of Mishawaka', '2026-11-07', 'primary', 'Same use as MON-011.'),
    ('MON-013', 'https://www.wsbt.com/news/local/budget-set-approved-salaries-employees-city-elected-official-police-fire-government-common-council-mishawaka-indiana', 'Mishawaka Common Council approves 2025 Civil City budget', 'WSBT', '2026-11-07', 'news', '2025 Civil City budget "nearly $77 million"; matches Gateway $76,988,029.'),
    ('MON-014', 'https://www.abc57.com/news/local-leaders-discuss-sea-1-impacts-and-possible-solutions', 'Local leaders discuss SEA 1 impacts and possible solutions (2025-11-18)', 'ABC57', '2026-11-07', 'news',
     'Reporter\'s statement: Mishawaka expected to face about a 20 percent, or $15 million, budget cut by 2028. Not a quote from Mayor Wood and the article does not say "general fund" (fact-check report).'),
    ('MON-015', 'https://www.abc57.com/news/south-bend-schools-pass-2026-budget-includes-higher-teacher-salaries', 'South Bend schools pass 2026 budget (2025-11-04)', 'ABC57', '2026-11-07', 'news',
     'SBCSC board vote: $213,254,807 for 2026, up 3% from $206,329,944 (2025). Scope differs from the Gateway all-advertised-funds sum ($248.3M for 2026); reason not verified.'),
    ('MON-016', 'https://abc57.com/news/St-Joseph-County-Leaders-Begin-2027-Budget-Process', 'St. Joseph County leaders begin 2027 budget process', 'ABC57', '2026-11-07', 'news', 'Council budget meetings began 2026-07-20; no dollar total reported.'),
    ('MON-017', 'https://abc57.com/news/city-of-south-bend-kicks-off-2027-budget-hearing-sessions', 'City of South Bend kicks off 2027 budget hearing sessions', 'ABC57', '2026-11-07', 'news', 'Mayor Mueller described "a one percent increase across the board" at the 2026-09-02 kickoff.'),
    ('MON-018', 'https://indianacapitalchronicle.com/2026/03/23/delay-in-local-income-tax-changes-sets-up-more-legislative-debate-next-year/', 'Delay in local income tax changes sets up more legislative debate next year (HB 1210)', 'Indiana Capital Chronicle', '2026-03-23', 'news',
     'HB 1210 (signed 2026-03-12) delays the SEA 1 2028 local income tax changes to 2029. Cited via fact-check report; the "cities of 3,500+" detail is not confirmed.'),
    ('MON-020', 'https://campaignfinance.in.gov/PublicSite/Reporting/DataDownload.aspx', 'Indiana Election Division campaign finance bulk data download page', 'Indiana Election Division', '2026-11-07', 'dataset',
     'Files grouped by calendar year FILED, not election cycle; no district or cash-on-hand field. Page lists files with extraction time 2026-11-07 01:03.'),
    ('MON-021', 'https://campaignfinance.in.gov/PublicSite/Docs/BulkDataDownloads/2024_ContributionData.csv.zip', 'Indiana campaign finance bulk contribution files 2016-2026 ({YEAR}_ContributionData.csv.zip)', 'Indiana Election Division', '2026-11-07', 'dataset',
     'Re-downloaded for this pass and saved under sources/money/cf/. Same URL pattern for each year.'),
    ('MON-022', 'https://campaignfinance.in.gov/PublicSite/Docs/BulkDataDownloads/2024_ExpenditureData.csv.zip', 'Indiana campaign finance bulk expenditure files 2016-2026 ({YEAR}_ExpenditureData.csv.zip)', 'Indiana Election Division', '2026-11-07', 'dataset',
     'Re-downloaded for this pass and saved under sources/money/cf/. Same URL pattern for each year.'),
    ('MON-023', 'planning/fact-check-report.md', 'Fact-check report: St. Joseph County civic guide research files (2026-11-07)', 'Project fact-check pass', '2026-11-07', 'derived', 'Corrections applied are logged in data/editions/st-joseph/_corrections_applied_money.md.'),
    ('MON-024', 'research/05-budgets.md', 'Research notes: budgets and finances', 'Project research', '2026-11-07', 'derived', 'Secondary transcription of Gateway and city documents; Gateway figures were re-derived from the raw download in this pass.'),
    ('MON-025', 'research/06-campaign-finance.md', 'Research notes: campaign finance', 'Project research', '2026-11-07', 'derived', 'State-committee totals re-derived from the bulk files in this pass.'),
]

# ---------------------------------------------------------------- Gateway budget data
raw = rd_psv('gateway_budget_county71_2012-2026.psv')
seen, G = set(), []
for r in raw:
    k = (r['year'], r['unit_code'], r['unit_name'], r['fund_cd'])
    if k in seen:
        continue
    seen.add(k)
    G.append(r)
YEARS = list(range(2012, 2027))

tot = collections.defaultdict(float)       # (unit_name, year) -> adopted sum
nrows = collections.Counter()
rate = collections.defaultdict(float)      # (unit_name, year) -> sum of net tax rates
ratecnt = collections.Counter()
fundamt = collections.defaultdict(float)   # (unit_name, year, fund_cd, desc)
funds = {}                                 # (unit_name, year, fund_cd) -> row
for r in G:
    n, y = r['unit_name'], int(r['year'])
    a = fnum(r['Total budget estimate_adopted'])
    nrows[(n, y)] += 1
    if a is not None:
        tot[(n, y)] += a
    t = fnum(r['Net Tax Rate_adopted'])
    if t is not None and t > 0:
        rate[(n, y)] += t
        ratecnt[(n, y)] += 1
    funds[(n, y, r['fund_cd'])] = r

# South Bend: confirm the pre-2024 totals include the water/sewer utility funds
for y in range(2012, 2024):
    util = [fc for (n, yy, fc), r in funds.items() if n == 'SOUTH BEND CIVIL CITY' and yy == y and re.search(r'WATER|SEWAGE|SEWER', r['fund_description'], re.I)]
    assert util, ('SB utility funds missing in', y)
for y in range(2024, 2027):
    util = [fc for (n, yy, fc), r in funds.items() if n == 'SOUTH BEND CIVIL CITY' and yy == y and re.search(r'WATER|SEWAGE', r['fund_description'], re.I)]
    assert not util, ('SB utility funds present in', y)

B = []   # budgets rows


def brow(unit, year, basis, amount, aoa, series, status, src, notes=''):
    B.append([unit, year, basis, '' if amount is None else money(amount), aoa, series, status, src, notes])


GW_NOTE = 'Sum of the adopted "Total budget estimate" across all funds Gateway lists for this unit.'
for name, (u, label) in UNITS.items():
    if name == 'SOUTH BEND CIVIL CITY':
        continue
    if name in ('ST JOSEPH CO REGIONAL WATER SEWER', 'St. Joseph Redevelopment Authority', 'UNION-NORTH UNITED SCHOOL CORPORATION'):
        continue   # AFR/debt only, no Form 4B budget rows
    for y in YEARS:
        if nrows[(name, y)] == 0:
            continue
        a = tot[(name, y)]
        if a == 0:
            continue   # reported as zero (likely not filed); recorded in gaps
        notes = GW_NOTE
        if name == 'MISHAWAKA CIVIL CITY':
            notes += ' Civil city only: excludes the electric, water and wastewater utilities.'
        if name == 'ST. JOSEPH COUNTY' and y == 2021:
            notes += ' The 2021 dip may reflect fund reclassification (not verified).'
        if name == 'ST. JOSEPH COUNTY' and y == 2026:
            notes += ' Council passed the 2026 budget 5-4 on 2025-10-14. The general fund alone is $90,704,400 (see series county-gateway-general-fund). News figures are in series county-news-wndu-2026 and county-news-auditor-2026.'
        if name == 'MISHAWAKA CIVIL CITY' and y == 2025:
            notes += ' WSBT reported "nearly $77 million" (MON-013).'
        if name == 'SOUTH BEND COMMUNITY SCHOOL CORPORATION' and y == 2026:
            notes += ' Board vote reported by ABC57 is $213,254,807 (different or unverified scope; see series sbcsc-news-board-vote).'
        src = 'MON-001'
        if name == 'MISHAWAKA CIVIL CITY' and y == 2026:
            src += ';MON-010'
            notes += ' Matches the city 2026 budget book total of $77,919,352. ABC57 (MON-014) reports Mishawaka expects about a 20 percent, or $15 million, budget cut by 2028 from SEA 1; that is the reporter\'s characterization, not a quote from Mayor Wood.'
        if name == 'MISHAWAKA CIVIL CITY' and y == 2024:
            src += ';MON-010'
            notes += ' The city 2026 budget book shows $70,250,671 approved for 2024 (Gateway sum differs by about $17,000).'
        series = u + '-gateway-advertised-funds'
        basis = 'advertised_all_funds'
        brow(u, y, basis, a, 'adopted', series, 'computed', src, notes)

# South Bend: Gateway series with explicit break in 2024
for y in range(2012, 2024):
    brow(SB, y, 'all_funds_incl_utilities', tot[('SOUTH BEND CIVIL CITY', y)], 'adopted', 'sb-gateway-allfunds-2012-2023', 'computed', 'MON-001',
         GW_NOTE + ' Includes water works, sewage works, trash and other enterprise funds.' + (' City overview lists 2023 adopted revenue of $440.4M (see budget_breakdowns).' if y == 2023 else ''))
BREAK_NOTE = ('Reporting basis changes in 2024. Through 2023 Gateway lists about 60-70 South Bend funds, including water works, sewage works, trash and other enterprise funds (2023 sum $427.2M). '
              'From 2024 Gateway lists only 10 property-tax-supported funds (2024 sum $166.2M). Do not compare across the break; for 2024-2025 use the news all-funds series sb-news-allfunds.')
brow(SB, 2024, 'all_funds_incl_utilities', None, 'series_break', 'sb-gateway-allfunds-2012-2023', 'computed', 'MON-001;MON-007', 'Series ends. ' + BREAK_NOTE)
brow(SB, 2024, 'gateway_reported_funds', None, 'series_break', 'sb-gateway-10funds-2024-2026', 'computed', 'MON-001;MON-007', 'Series starts. ' + BREAK_NOTE)
for y in range(2024, 2027):
    brow(SB, y, 'gateway_reported_funds', tot[('SOUTH BEND CIVIL CITY', y)], 'adopted', 'sb-gateway-10funds-2024-2026', 'computed', 'MON-001',
         GW_NOTE + ' Only 10 property-tax-supported funds (General, fire and police pensions, local road and street, motor vehicle highway, major moves, park and recreation, park bond, two cumulative funds). Narrower than the pre-2024 basis.')
# SB news all-funds series (secondary)
brow(SB, 2024, 'all_funds_incl_utilities', 417000000, 'adopted', 'sb-news-allfunds', 'secondary', 'MON-007',
     'ABC57 reports about $417 million as the 2024 budget (stated as the prior-year figure in the 2025 article). Rounded news figure, all funds including utilities, grants and enterprise funds.')
brow(SB, 2025, 'all_funds_incl_utilities', 424000000, 'adopted', 'sb-news-allfunds', 'secondary', 'MON-007',
     'ABC57 (2024-10-15) reports "more than $424 million". Amount is the stated floor, not an exact total. Police over $60M, Fire just under $49M, transit $14M.')
brow(SB, 2024, 'all_funds_incl_utilities', 447200000, 'proposed', 'sb-cityoverview-proposed-expenditures', 'official', 'MON-006',
     'City 2024 budget overview (2023-08-16): proposed 2024 expenditures of $447.2M against proposed revenue of $420.6M, a net deficit of $26.7M. Proposed, not adopted. The research notes say PDF text extraction left some of these labels ambiguous.')

# county news series (secondary), quoted as published; the two figures conflict
brow(COUNTY, 2026, 'general_fund', 90000000, 'adopted', 'county-news-wndu-2026', 'secondary', 'MON-008;MON-009',
     'WNDU (2025-09-10) calls "just over $90 million" the balanced 2026 budget. Amount entered is the stated floor. It matches the Gateway General fund ($90,704,400), not the all-funds total. Conflicts with the auditor quote in county-news-auditor-2026; present both as quoted.')
brow(COUNTY, 2026, 'general_fund', 97000000, 'adopted', 'county-news-auditor-2026', 'secondary', 'MON-008',
     'County auditor, quoted by WNDU: "a balanced general fund budget at $97 million, which is 39% of the total budget". $97M does not match the Gateway General fund ($90.7M); $97M / 0.39 is about $249M, close to the Gateway all-funds sum ($248.2M). WNDU also gives "increase of more than $1,400, 1% up", which is internally inconsistent (probably $1.4 million). Interpretation unverified.')
# SBCSC news (secondary)
brow('school-sbcsc', 2025, 'advertised_all_funds', 206329944, 'adopted', 'sbcsc-news-board-vote', 'secondary', 'MON-015',
     'ABC57: 2025 budget of $206,329,944 as the base for the 3% increase. Scope not verified; the Gateway sum for 2025 is $220.0M.')
brow('school-sbcsc', 2026, 'advertised_all_funds', 213254807, 'adopted', 'sbcsc-news-board-vote', 'secondary', 'MON-015',
     'Board vote reported by ABC57 on 2025-11-04. Scope not verified; the Gateway sum for 2026 is $248.3M. Basis label is a placeholder for "as reported by the board".')

# general-fund series (single Gateway fund, fund code 0101)
for name, series in (('ST. JOSEPH COUNTY', 'county-gateway-general-fund'), ('SOUTH BEND CIVIL CITY', 'sb-gateway-general-fund'), ('MISHAWAKA CIVIL CITY', 'mishawaka-gateway-general-fund')):
    u = uid(name)
    for y in YEARS:
        r = funds.get((name, y, '0101'))
        if not r:
            continue
        a = fnum(r['Total budget estimate_adopted'])
        notes = 'Gateway fund 0101 (General), adopted column.'
        if name == 'ST. JOSEPH COUNTY' and y == 2026:
            notes += ' Published (advertised) figure was $91,954,399. WNDU reported "just over $90 million".'
        if name == 'MISHAWAKA CIVIL CITY' and y in (2024, 2025, 2026):
            notes += ' Matches the 2026 city budget book general fund.'
        if name == 'MISHAWAKA CIVIL CITY' and y == 2020:
            notes += ' The research notes cite $35.27M for 2020 from the city 2021/2022 budget books (MON-011, MON-012); that book figure was not re-extracted and differs from this Gateway figure.'
        if name == 'MISHAWAKA CIVIL CITY' and y == 2021:
            notes += ' Equals the $36.64M the research notes cite from the city budget books.'
        if name == 'MISHAWAKA CIVIL CITY' and y == 2022:
            notes += ' The research notes cite $37.92M from the city 2022 budget book (MON-011), not re-extracted; differs from this Gateway figure by about $0.12M.'
        brow(u, y, 'general_fund', a, 'adopted', series, 'official', 'MON-001' + (';MON-010' if name == 'MISHAWAKA CIVIL CITY' and y >= 2024 else ''), notes)

# ---------------------------------------------------------------- tax rates
T = []
for name, (u, label) in UNITS.items():
    for y in YEARS:
        if ratecnt[(name, y)] == 0:
            continue
        T.append([u, 'unit-wide (sum of this unit\'s fund net rates)', y, '%.4f' % rate[(name, y)], 'sum_of_fund_net_rates', 'computed', 'MON-001',
                  'Sum of the adopted "Net Tax Rate" of every fund the unit levies, dollars per $100 assessed value. This is not the combined rate on a tax bill (overlapping units not added).'])
for name, code, kind, desc in (('ST. JOSEPH COUNTY', '0101', 'general_fund_net_rate', 'County General fund'),
                               ('SOUTH BEND CIVIL CITY', '0101', 'general_fund_net_rate', 'City General fund'),
                               ('SOUTH BEND CIVIL CITY', '1301', 'park_fund_net_rate', 'City Park and Recreation fund'),
                               ('MISHAWAKA CIVIL CITY', '0101', 'general_fund_net_rate', 'City General fund')):
    for y in YEARS:
        r = funds.get((name, y, code))
        if not r:
            continue
        v = fnum(r['Net Tax Rate_adopted'])
        if v is None or v == 0:
            continue
        T.append([uid(name), desc, y, '%.4f' % v, kind, 'official', 'MON-001', 'Gateway adopted net tax rate for this single fund, dollars per $100 assessed value.'])
# annotate large year-over-year swings in the sums (reason not found)
bykey = {(t[0], t[1], t[4], t[2]): t for t in T}
for t in T:
    prev = bykey.get((t[0], t[1], t[4], t[2] - 1))
    if prev and float(prev[3]) > 0:
        ch = float(t[3]) / float(prev[3]) - 1
        if abs(ch) > 0.4:
            t[7] += ' Changed %+.0f%% from the prior year in the state data; reason not found.' % (ch * 100)

# ---------------------------------------------------------------- AFR: spending, revenue, debt
disb = rd_psv('gateway_afr_disbursements_2024_county71.psv')
rcpt = rd_psv('gateway_afr_receipts_2024_county71.psv')
debt = rd_psv('gateway_afr_debt_2024_county71.psv')

BD = []


def bdrow(unit, year, kind, cat, amt, basis, status, src, notes=''):
    BD.append([unit, year, kind, cat, money(amt), basis, status, src, notes])


def top_with_balance(d, total, limit, minshare):
    items = sorted(d.items(), key=lambda kv: -kv[1])
    keep, other = [], 0.0
    for i, (k, v) in enumerate(items):
        if i < limit and v / total >= minshare:
            keep.append((k, v))
        else:
            other += v
    return keep, other


scope_note = {
    COUNTY: 'AFR scope: $92.65M of 2024 disbursements, mostly general-government and public-safety funds. Not total county spending (the all-funds budget is about $225.9M for 2024). Department coding changes between years, so do not compare departments across years.',
    SB: 'AFR scope: $110.25M of 2024 disbursements, general-type funds only. Excludes bonds paid from debt funds and the sewer, water and street-type funds. Not total city spending.',
    MISH: 'AFR scope: $42.5M of 2024 disbursements from governmental funds; utilities are outside this file.',
}
for name, u, limit, minshare in (('ST. JOSEPH COUNTY', COUNTY, 20, 0.02), ('SOUTH BEND CIVIL CITY', SB, 20, 0.0), ('MISHAWAKA CIVIL CITY', MISH, 12, 0.02)):
    rows = [r for r in disb if r['unit_name'] == name]
    total = sum(float(r['amount']) for r in rows)
    bydept = collections.defaultdict(float)
    bycls = collections.defaultdict(float)
    for r in rows:
        bydept[r['department_name'].strip()] += float(r['amount'])
        bycls[r['disburse_class_name'].strip()] += float(r['amount'])
    keep, other = top_with_balance(bydept, total, limit, minshare)
    for k, v in keep:
        bdrow(u, 2024, 'spending', k, v, 'afr_2024_actual_by_department', 'computed', 'MON-002',
              'Sum of 2024 actual disbursements for this department across funds (%.1f%% of the file total of $%s). %s' % (v / total * 100, money(total), scope_note[u]))
    if other > 0:
        bdrow(u, 2024, 'spending', 'All other departments (balance)', other, 'afr_2024_actual_by_department', 'computed', 'MON-002',
              'File total of $%s minus the departments listed above. %s' % (money(total), scope_note[u]))
    for k, v in sorted(bycls.items(), key=lambda kv: -kv[1]):
        bdrow(u, 2024, 'spending', k, v, 'afr_2024_actual_by_expense_class', 'computed', 'MON-002',
              '%.1f%% of the 2024 disbursements in this file ($%s). %s' % (v / total * 100, money(total), scope_note[u]))

rev_note = ('Gateway Annual Financial Report 2024 actual receipts, summed by receipt line. Includes non-operating receipts (borrowing proceeds, transfers between funds, '
            'benefit-plan contributions, pass-through collections), so the total is not operating revenue.')
for name, u in (('ST. JOSEPH COUNTY', COUNTY), ('SOUTH BEND CIVIL CITY', SB), ('MISHAWAKA CIVIL CITY', MISH)):
    rows = [r for r in rcpt if r['unit_name'] == name]
    total = sum(float(r['amount']) for r in rows)
    byline = collections.defaultdict(float)
    byclass = collections.defaultdict(float)
    lineclass = {}
    for r in rows:
        lab = re.sub(r'\s+', ' ', r['receipt_name']).strip()
        byline[lab] += float(r['amount'])
        lineclass[lab] = r['Receipt_Class_Name']
        byclass[r['Receipt_Class_Name']] += float(r['amount'])
    keep, other = top_with_balance(byline, total, 25, 0.005)
    for k, v in keep:
        bdrow(u, 2024, 'revenue', k, v, 'afr_2024_actual_receipts_by_line', 'computed', 'MON-003',
              'Gateway receipt class: %s. %.1f%% of all 2024 receipts in the file ($%s). %s' % (lineclass[k], v / total * 100, money(total), rev_note))
    if other > 0:
        bdrow(u, 2024, 'revenue', 'All other receipt lines (balance)', other, 'afr_2024_actual_receipts_by_line', 'computed', 'MON-003',
              'File total of $%s minus the lines listed above. %s' % (money(total), rev_note))
    for k, v in sorted(byclass.items(), key=lambda kv: -kv[1]):
        bdrow(u, 2024, 'revenue', k, v, 'afr_2024_actual_receipts_by_class', 'computed', 'MON-003',
              '%.1f%% of all 2024 receipts in the file ($%s). %s' % (v / total * 100, money(total), rev_note))

# South Bend city overview (proposed 2024 revenue by source; 2024 only)
SBREV = [('Property taxes', 94996997), ('Local income taxes', 35136116), ('Charges for services', 123481642), ('Debt proceeds', 11928500),
         ('Donations', 9720560), ('Fines, forfeitures, fees', 744420), ('Interest earnings', 3586248), ('Interfund allocation reimbursement', 31507592),
         ('Interfund transfers in', 62297371), ('Intergovernmental / grants', 4332568), ('Intergovernmental / shared revenues', 31800200),
         ('Licenses and permits', 1930707), ('Other income', 3108272), ('PILOT', 6024186)]
assert sum(v for _, v in SBREV) == 420595379, sum(v for _, v in SBREV)
for k, v in SBREV:
    bdrow(SB, 2024, 'revenue', k, v, 'city_overview_2024_proposed_all_funds', 'official', 'MON-006',
          'City-prepared 2024 PROPOSED revenue, all funds (total $420,595,379; the rows sum to that total). Row-to-label alignment was reconstructed from PDF text order in the research notes; labels are plausible but not re-confirmed against the PDF. City page (MON-005) gives roughly property taxes 25%, income taxes 11%, charges for services 30% of revenue.')

# Mishawaka 2026 approved by fund and by category (civil city, all funds)
MFUND = [('General', 49604404), ('CEDIT', 7401000), ('Cumulative Capital Development', 800000), ('Cumulative Capital Improvement', 313000), ('Cumulative Sewer', 175000),
         ('EMS', 720000), ('Law Enforcement Continuing Education', 186200), ('Local Road & Street', 1065000), ('Motor Vehicle Highway', 3225519),
         ('Motor Vehicle Highway - Restricted', 1000000), ('Park and Recreation', 5830729), ('Park and Recreation - Non-Reverting', 467000),
         ('Public Safety LIT', 3673500), ('Fire Pension', 2150000), ('Police Pension', 1308000)]
MCAT = [('Personal Services', 54925002), ('Supplies', 3567550), ('Other Services & Charges', 12796600), ('Capital Outlays', 6630200)]
assert sum(v for _, v in MFUND) == 77919352, sum(v for _, v in MFUND)
assert sum(v for _, v in MCAT) == 77919352
for k, v in MFUND:
    bdrow(MISH, 2026, 'spending', k, v, 'mishawaka_2026_approved_by_fund', 'official', 'MON-010',
          'Mishawaka 2026 approved budget, civil city (excludes electric, water and wastewater utilities). Total $77,919,352 (rows sum to it). Read from the budget book "Summary for all funds"; the research notes mislabeled the $1,000,000 line as Local Road & Street (the book shows Local Road & Street $1,065,000 and Motor Vehicle Highway - Restricted $1,000,000).')
for k, v in MCAT:
    bdrow(MISH, 2026, 'spending', k, v, 'mishawaka_2026_approved_by_category', 'official', 'MON-010',
          'Mishawaka 2026 approved budget by category, civil city, all funds. Total $77,919,352 (rows sum to it).')
for k, v in (('Fire Department', 20482149), ('Police Department', 17343945), ('Controller', 5960348)):
    bdrow(MISH, 2026, 'spending', k, v, 'mishawaka_2026_approved_general_fund_selected_departments', 'official', 'MON-010',
          'Mishawaka 2026 approved General fund ($49,604,404), selected departments only (the three largest, re-checked against department detail in the book). The other General fund departments are not listed here.')
for k, v in (('Police (adopted 2025)', 60000000), ('Fire (adopted 2025)', 49000000), ('South Bend Public Transportation Corporation (adopted 2025)', 14000000)):
    bdrow(SB, 2025, 'spending', k, v, 'abc57_2025_adopted_selected_departments', 'secondary', 'MON-007',
          'ABC57 (2024-10-15) reports "over $60 million" for Police, "just under $49 million" for Fire and $14 million for transit in the 2025 budget. Amounts here are the rounded figures (Police is a floor, Fire is a ceiling).')

# ---------------------------------------------------------------- debt
D = []
dtot = collections.defaultdict(float)
ddue = collections.defaultdict(float)
dcls = collections.defaultdict(float)
for r in debt:
    n = r['unit_name']
    if n.upper() not in UNITS_UPPER:
        continue
    ent = (r['ent_name'] or '').strip() or 'Governmental Activities'
    cls = '%s (%s)' % (r['debt_class_name'].strip(), ent)
    v = fnum(r['end_principal_bal']) or 0
    dcls[(uid(n), cls)] += v
    dtot[uid(n)] += v
    ddue[uid(n)] += fnum(r['principal_amt_due_1yr']) or 0
names_by_id = {v[0]: v[1] for v in UNITS.values()}
for (u, cls), v in sorted(dcls.items()):
    if v == 0:
        continue
    D.append([u, 2024, 'End-of-year principal outstanding: ' + cls, money(v), 'official', 'MON-004',
              'Gateway Annual Financial Report 2024, sum of debt entries in this class. Entity in parentheses as filed.'])
for u in sorted(dtot):
    if dtot[u] == 0:
        continue
    extra = ''
    if u == MISH:
        extra = ' Includes utility (water, wastewater, electric) debt.'
    D.append([u, 2024, 'Total end-of-year principal outstanding (all debt)', money(dtot[u]), 'computed', 'MON-004', 'Sum of the class rows for this unit.' + extra])
    D.append([u, 2024, 'Principal due within one year (all debt)', money(ddue[u]), 'computed', 'MON-004', 'Sum of principal amounts due within 1 year across this unit\'s debt entries.'])
D.append([SB, 2026, 'Total debt outstanding as of 2026-09-04 (city budget page)', '280700000', 'official', 'MON-005',
          'City budget page states "roughly $280.7 million" outstanding as of 2026-09-04; rounded. Same page gives cash reserves of about $22-23 million (reserves are not debt). Compare with the 2024 Gateway figure above, which is a different date.'])

# ---------------------------------------------------------------- campaign finance (state bulk data)
CF_COMMITTEES = [
    # committee name as filed, candidate, office, district, party, note
    ('David Niezgodski for Senate District 10', 'David Niezgodski', 'State Senator', 'SD10', 'D', ''),
    ('Committee to Elect Jake Teshka', 'Jake Teshka', 'State Representative', 'HD7', 'R', 'Bulk data shows no committee of this name before 2020; a 2018 committee "Friends of Jake Teshka" was mentioned in the research notes but was not found in the 2016-2026 files under that candidate name.'),
    ('Ryan Dvorak for State Representative', 'Ryan Dvorak', 'State Representative', 'HD8', 'D', ''),
    ('Dale DeVon for State Rep', 'Dale DeVon', 'State Representative', 'HD5', 'R', ''),
    ('Maureen Bauer for State Representative', 'Maureen Bauer', 'State Representative', 'HD6', 'D', 'Committee appears in the bulk data from 2020.'),
    ('Wesco Victory Committee', 'Timothy Wesco', 'State Representative', 'HD21', 'R', ''),
    ('Mishler for State Senate', 'Ryan Mishler', 'State Senator', 'SD9', 'R', ''),
    ('Committee to Elect Bohacek for Senate', 'Mike Bohacek', 'State Senator', 'SD8', 'R', ''),
    ('Linda Rogers for State Senate', 'Linda Rogers', 'State Senator', 'SD11', 'R', 'Lost the May 2026 Republican primary for SD11 (county portion Schmutzler 55.75%, Rogers 44.25%; fact-check report).'),
    ('Friends of Gabrianna Gratzol', 'Gabrianna Gratzol', 'State Senator', 'SD11', 'D', 'SD11 Democratic nominee 2026; general election result unofficial as of 2026-11-07.'),
    ('Dr. Brian Schmutzler for Indiana Senate', 'Brian Schmutzler', 'State Senator', 'SD11', 'R', 'SD11 Republican nominee 2026.'),
    ('Friends of Alex Wait', 'Alex Wait', 'State Representative', 'HD5', 'D', 'HD5 Democratic nominee 2026; general election result unofficial as of 2026-11-07.'),
    ('Pat Bauer for Indiana', 'B. Patrick Bauer', 'State Representative (former)', 'HD6', 'D', 'Residual committee of the former HD6 representative; district and party per the research notes, not re-checked.'),
]
CFY = range(2016, 2027)
cf_by = {}   # (committee, year) -> dict
want = {c[0] for c in CF_COMMITTEES}
for y in CFY:
    for kind in ('Contribution', 'Expenditure'):
        z = zipfile.ZipFile('%scf/%d_%sData.csv.zip' % (SRC, y, kind))
        text = z.read(z.namelist()[0]).decode('latin1')
        for r in csv.DictReader(io.StringIO(text)):
            c = r.get('Committee')
            if c not in want:
                continue
            d = cf_by.setdefault((c, y), {'C': 0.0, 'E': 0.0, 'types': collections.defaultdict(float), 'amended': 0, 'nC': 0, 'nE': 0})
            amt = fnum(r['Amount']) or 0
            if kind == 'Contribution':
                d['C'] += amt
                d['nC'] += 1
                t = (r['ContributorType'] or '').strip() or 'Unitemized (no contributor type)'
                d['types'][t] += amt
            else:
                d['E'] += amt
                d['nE'] += 1
            if r['Amended'] == '1':
                d['amended'] += 1
CF = []
for c, cand, office, dist, party, note in CF_COMMITTEES:
    for y in CFY:
        d = cf_by.get((c, y))
        if not d or (d['C'] == 0 and d['E'] == 0):
            continue
        top = sorted(d['types'].items(), key=lambda kv: -kv[1])[:3]
        tops = '; '.join('%s %s' % (k, money(v)) for k, v in top)
        notes = ('Filing-year basis: totals of items on reports filed in calendar %d, not an election-cycle total. Receipts = sum of contribution rows (%d rows), expenditures = sum of expenditure rows (%d rows). '
                 'Cash on hand is not in the bulk data (blank). Top contributor types are summed by the type code as filed, largest three by amount.' % (y, d['nC'], d['nE']))
        if d['amended']:
            notes += ' Includes %d rows flagged Amended (a few may repeat an original row).' % d['amended']
        if y == 2026:
            notes += ' 2026 is partial: data extracted 2026-11-07.'
        if note:
            notes += ' ' + note
        CF.append([c, cand, office, dist, party, y, money(d['C']), money(d['E']), '', tops, 'computed', 'MON-021;MON-022;MON-020', notes])

# ---------------------------------------------------------------- gaps
GAPS = [
    ('money', 'South Bend 2026 and 2027 all-funds budget totals', 'Gateway lists only 10 funds from 2024; no all-funds 2026 total was found. The city page says council adopted the 2027 budget on 2026-10-12 but gives no dollar total.', 'South Bend 2027 budget documents (docs.southbendin.gov WebLink folder 409325; needs a browser session) or Common Council minutes.'),
    ('money', 'County, Mishawaka, township, school, library 2027 adopted budgets', 'Gateway had no 2027 budget-year column as of 2026-11-07; county council meetings began 2026-07-20 with no total reported.', 'Re-pull the Gateway Budget Data file after DLGF certifies 2027 budgets.'),
    ('money', 'County spending and revenue breakdown on an all-funds basis', 'The AFR disbursement file covers only $92.65M of the $225.9M all-funds budget, and the receipts file ($1.08B) includes large pass-through and borrowing items.', 'Use the county annual financial report or budget book; add a clean operating-revenue table.'),
    ('money', 'Mishawaka civil-city revenue by source (2026 budget)', 'Text extraction of the budget book revenue pages was unclear. Only 2024 AFR actuals are in budget_breakdowns.', 'Extract from the 2026 budget book (MON-010) with a PDF table tool.'),
    ('money', 'Mishawaka utilities (electric, water, wastewater) as a time series', 'Gateway civil-city rows exclude utilities. 2026 approved: electric revenue $63.9M / expense $63.8M; water $16.8M / $16.8M; wastewater $25.4M / $25.3M (research notes, not re-extracted).', 'Extract utility budgets from each Mishawaka budget book.'),
    ('money', 'Combined tax-district rates (South Bend-Portage, Mishawaka-Penn, Centre, etc.)', 'tax_rates.csv holds only the sum of each unit\'s own fund rates; overlapping units are not added and the full bill rate was not found.', 'DLGF Certified Tax Rate / "Tax Bill" parcel data from Gateway.'),
    ('money', 'Net assessed valuation by unit', 'The Gateway Net Assessed Valuation field holds round placeholder values (for example $15.00B for the county in 2024-2026) and is not reliable.', 'DLGF Net Assessed Value Abstract.'),
    ('money', 'Circuit-breaker (property tax cap) credits and losses by unit and year', 'Only Mishawaka 2021-2022 ($8.2M each year, from city books) and a 2016 county cumulative figure from search snippets were found.', 'Gateway "Tax Bill" parcel file or DLGF circuit breaker reports.'),
    ('money', 'Dollar impact of SEA 1 (2025) on the county, South Bend, schools', 'Only news characterizations. Mishawaka: ABC57 reports an expected cut of about 20% or $15M by 2028 (reporter\'s characterization, not Mayor Wood\'s quote). South Bend 2026: proposed 15% Public Works program reduction.', 'DLGF SEA 1 fiscal impact estimates by unit.'),
    ('money', 'HB 1210 (2026) details', 'Signed 2026-03-12 and delays the SEA 1 local income tax changes from 2028 to 2029 (fact-check confirmed). The "cities of 3,500+ can adopt their own LIT rate" detail is not confirmed.', 'Read the enrolled act on iga.in.gov.'),
    ('money', 'School enrollment and spending per student', 'No authoritative source reached; aggregators conflict.', 'IDOE enrollment and Gateway/IDOE per-pupil data.'),
    ('money', 'SBCSC 2026 budget scope', 'Board vote $213.25M (ABC57) vs Gateway sum $248.3M; reason not verified.', 'SBCSC board budget documents.'),
    ('money', 'Gateway budget years with zero totals (omitted from budgets.csv)', 'Madison Township 2016, Olive Township 2016-2017, Indian Village 2023, and units absent from some early years (schools and libraries before 2013, South Bend Public Transportation 2012, Roseland 2012, Walkerton Library 2012-2013, New Carlisle Library 2012) have no usable adopted total in the Gateway file.', 'Check the Gateway unit pages or DLGF archives for those years.'),
    ('money', 'South Bend Redevelopment Commission budget', 'Only 2013-2017 appear in Gateway (about $1.27M a year), none after; TIF and redevelopment finances were not searched.', 'City redevelopment commission reports.'),
    ('money', 'Debt before 2024 and reserves', 'Only the 2024 AFR debt file was pulled. Reserves found only for South Bend (about $22-23M, city page 2026-09).', 'Pull Gateway AFR Debt for other years; county and Mishawaka reserve figures from annual financial reports.'),
    ('money', 'County jail construction cost and funding', 'No source found.', 'County council and commissioner minutes.'),
    ('money', 'State campaign finance: cash on hand, election-cycle totals, opponents', 'Bulk files are keyed by calendar year filed, hold no cash balance and no district field. Totals are by filing year, so an election cycle spans two or more rows.', 'campaignfinance.in.gov report views (PoliticalRaceSearch) or per-report CFA-4s.'),
    ('money', 'State campaign finance: top-funder name totals', 'Funders were typed in by name and spellings vary (research notes found, for example, "LAWPAC of Indiana" in two spellings), so name-level totals are understated. cf_state.csv gives funder TYPE totals only.', 'Name-matching pass over contributor names.'),
    ('money', 'State campaign finance: committees for Devon Wellington, Joe Zakas and others', 'Committees exist in the bulk files, but their county district is unconfirmed (Wellington, 2026) or office and dates are unverified (Zakas: "Joe Zakas for State Senator", 2016 and 2018). Left out of cf_state.csv.', 'Confirm districts and dates from the Indiana Election Division race search.'),
    ('money', 'State campaign finance: Friends of Jim Pressel (HD20) committee', 'Left out: the fact-check report found House District 20 (Pressel) and House District 9 (Novak) never appear on St. Joseph County ballots 2020-2026.', 'None needed unless district lines change.'),
    ('money', 'State campaign finance: Teshka 2018 committee', 'Research notes mention a 2018 "Friends of Jake Teshka"; no matching committee turned up in the bulk files under his candidate name for 2016-2026 apart from the 2020+ committee.', 'Search the Election Division committee list for earlier committee names.'),
    ('money', 'County Democratic and Republican party committee finances', 'Not in the state bulk data. The county posts them locally (St. Joseph County Democratic Central Committee, St. Joseph County Republican Party) per the fact-check report.', 'County Voter Registration/Election Board filings (cf_local.csv, later phase).'),
    ('money', 'Local campaign finance (mayors, councils, county offices, school boards, townships)', 'Not in the state database; filed with the county. Out of scope for cf_state.csv.', 'cf_local.csv from research/cf/ (Phase B).'),
]

# unexplained year-over-year jumps in budget series (also printed by tools/check_money.py)
series_rows = collections.defaultdict(list)
for r in B:
    if r[4] == 'series_break':
        continue
    series_rows[r[5]].append(r)
name_by_id = {v[0]: k for k, v in UNITS.items()}
for s, rows in series_rows.items():
    rows.sort(key=lambda r: r[1])
    for a, b in zip(rows, rows[1:]):
        if b[1] != a[1] + 1:
            continue
        pa, pb = float(a[3]), float(b[3])
        if pa > 0 and abs(pb / pa - 1) > 0.4 and abs(pb - pa) >= 500000 and 'gateway' in s and not s.startswith('sb-gateway-allfunds') and not s.startswith('sb-gateway-10funds'):
            nm = name_by_id.get(b[0])
            deltas = []
            fcs = {fc for (n, yy, fc) in funds if n == nm and yy in (b[1], b[1] - 1)}
            for fc in fcs:
                cur = funds.get((nm, b[1], fc))
                prev = funds.get((nm, b[1] - 1, fc))
                d = ((fnum(cur['Total budget estimate_adopted']) or 0) if cur else 0) - ((fnum(prev['Total budget estimate_adopted']) or 0) if prev else 0)
                deltas.append((abs(d), d, (cur or prev)['fund_description'].strip()))
            deltas.sort(reverse=True)
            top = deltas[0] if deltas and not s.endswith('general-fund') else None
            why = 'Adopted total moved %+.0f%% (from $%s to $%s) with no documented change in reporting basis; reason not found.' % ((pb / pa - 1) * 100, money(pa), money(pb))
            if top:
                why += ' Largest single-fund change in the Gateway data: %s (%+.1fM).' % (top[2], top[1] / 1e6)
            elif s.endswith('general-fund'):
                why += ' This series is the single General fund.'
            GAPS.append(('money', '%s %d-%d: unexplained budget jump' % (names_by_id[b[0]], a[1], b[1]), why, 'Check the unit\'s budget notices or fund detail in Gateway for that year.'))

# ---------------------------------------------------------------- write
write_csv('budgets.csv', ['unit_id', 'year', 'basis', 'amount', 'adopted_or_actual', 'series_id', 'status', 'source_ids', 'notes'], sorted(B, key=lambda r: (r[0], r[5], r[1], r[4] == 'series_break')))
write_csv('budget_breakdowns.csv', ['unit_id', 'year', 'kind', 'category', 'amount', 'basis', 'status', 'source_ids', 'notes'], BD)
write_csv('tax_rates.csv', ['unit_id', 'taxing_district', 'year', 'rate_per_100', 'rate_kind', 'status', 'source_ids', 'notes'], T)
write_csv('debt.csv', ['unit_id', 'year', 'debt_type', 'amount', 'status', 'source_ids', 'notes'], D)
write_csv('cf_state.csv', ['committee', 'candidate', 'office', 'district', 'party', 'year', 'receipts', 'expenditures', 'cash_end', 'top_funder_types', 'status', 'source_ids', 'notes'], CF)
write_csv('sources_money.csv', ['id', 'url', 'title', 'publisher', 'accessed', 'kind', 'notes'], [list(s) for s in SOURCES])
write_csv('gaps_money.csv', ['area', 'item', 'why_missing', 'how_to_fill'], [list(g) for g in GAPS])

# comparison with the research tables (printed, used for the corrections log)
if '--compare' in sys.argv:
    txt = open(ROOT + 'research/06-campaign-finance.md', encoding='utf-8').read()
    cur, mism, n = None, [], 0
    mapname = {'David Niezgodski': 'David Niezgodski for Senate District 10', 'Committee to Elect Jake Teshka': 'Committee to Elect Jake Teshka',
               'Ryan Dvorak': 'Ryan Dvorak for State Representative', 'Dale DeVon': 'Dale DeVon for State Rep', 'Maureen Bauer': 'Maureen Bauer for State Representative',
               'Wesco Victory': 'Wesco Victory Committee', 'Mishler for State Senate': 'Mishler for State Senate', 'Committee to Elect Bohacek': 'Committee to Elect Bohacek for Senate',
               'Linda Rogers': 'Linda Rogers for State Senate'}
    for line in txt.split('## 3b')[0].split('### 3a')[1].splitlines():
        p = [x.strip() for x in line.strip('|').split('|')]
        if len(p) != 4 or not re.match(r'\d{4}', p[1]):
            continue
        if not p[0].startswith('same'):
            cur = None
            for k, v in mapname.items():
                if p[0].startswith(k) or p[0].startswith('UNCONFIRMED') and False:
                    cur = v
        if cur is None:
            continue
        y = int(p[1][:4])
        d = cf_by.get((cur, y), {'C': 0, 'E': 0})
        c0, e0 = int(p[2].replace(',', '')), int(p[3].replace(',', ''))
        n += 1
        if abs(round(d['C']) - c0) > 1 or abs(round(d['E']) - e0) > 1:
            mism.append((cur, y, c0, e0, round(d['C']), round(d['E'])))
    print('research 3a rows compared:', n, 'mismatches:', len(mism))
    for m in mism:
        print('  ', m)
    # budget tables
    print('--- budget sums vs research 05 (county, SB, Mishawaka)')
    rc = {'county': [90.9, 91.8, 97.2, 105.9, 115.7, 131.9, 136.6, 150.2, 172.2, 152.3, 191.4, 208.8, 225.9, 238.9, 248.2]}
    for i, y in enumerate(YEARS):
        v = tot[('ST. JOSEPH COUNTY', y)] / 1e6
        if abs(v - rc['county'][i]) > 0.06:
            print('county mismatch', y, v)
omitted = [(n, y) for n in UNITS if any(nrows[(n, yy)] for yy in YEARS) for y in YEARS if tot[(n, y)] == 0 and n != 'SOUTH BEND CIVIL CITY']
print('omitted unit-years:', omitted)
print('rows: budgets', len(B), 'breakdowns', len(BD), 'tax', len(T), 'debt', len(D), 'cf', len(CF), 'gaps', len(GAPS))
