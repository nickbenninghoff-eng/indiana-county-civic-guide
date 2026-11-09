"""Build the St. Joseph County local campaign-finance tables from the Phase B readings.

Run:  python -P -E tools/build_cf_local.py
Inputs (research/cf): visual-chunk-*.csv (first readings), verify-[1-4].csv (blind second
readings of a 152-doc sample), sources/cf/pdf/<batch>/manifest.csv.
Outputs:
  research/cf/cf_lines_final.csv                       adjudicated line-level readings (all docs)
  data/editions/st-joseph/cf_local.csv                 one row per committee per reporting period
  data/editions/st-joseph/sources_cf_local.csv         one CFL source per DocumentCenter doc
  data/editions/st-joseph/cf_large_contributions.csv   CFA-11 entries
  data/editions/st-joseph/cf_coverage.csv              office x cycle coverage matrix
Adjudication decisions are hard-coded below (see research/cf/adjudication.md for the why).
"""
import csv, glob, os, re, collections
from decimal import Decimal as D

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(ROOT, *p)
ED = R('data', 'editions', 'st-joseph')

NUM = ['l13A', 'l14B', 'l15aA', 'l15bA', 'l15cA', 'l16A', 'l17aA', 'l17bA', 'l17cA', 'l18A',
       'l15aB', 'l15bB', 'l15cB', 'l16B', 'l17aB', 'l17bB', 'l17cB', 'l18B', 'l19', 'l20']
HDR = ['doc_id', 'tab', 'committee', 'candidate', 'office', 'party', 'report_type', 'period_from',
       'period_to', 'amended'] + NUM + ['status', 'checks_passed', 'notes']


def load(pattern):
    out = {}
    for fn in sorted(glob.glob(R(*pattern.split('/')))):
        with open(fn, encoding='utf-8', newline='') as f:
            for r in csv.DictReader(f):
                out[r['doc_id']] = r
    return out


def num(x):
    x = (x or '').strip()
    return D(x) if re.fullmatch(r'-?\d+(\.\d+)?', x) else None


def fmt(v):
    if v is None:
        return ''
    return f'{v:.2f}'


# ----------------------------------------------------------------------------------------------
# 1. Adjudication: cell overrides (image checked), cells we treat as derived, extra docs
# ----------------------------------------------------------------------------------------------
# Cell values decided from the images (value '' = blank / not a number on the form).
CELL_OVERRIDES = {
    '61143': {'l17aB': '5654.60'},
    '65634': {'l15bB': '0', 'l19': '1315.67'},
    '68257': {'l18B': '336'},
    '69855': {'l15aA': '476038.38', 'l17bB': '0'},
    '60862': {'l20': '0'},
    '65615': {'l18B': ''},
    '65627': {'l17aA': '880.57'},
    '70545': {k: '' for k in ['l15aA', 'l15bA', 'l17aA', 'l17bA', 'l15aB', 'l15bB', 'l17aB', 'l17bB']},
    '68161': {'l19': '', 'l20': ''},
    '68230': {'l19': '', 'l20': ''},
    # cells blank / illegible / clipped on the form: cleared here so the identities fill them
    '71864': {'l16A': '', 'l16B': ''},
    '72879': {'l16A': '', 'l16B': ''},
    '72885': {'l15cA': '', 'l15cB': ''},
    '72776': {'l16B': ''},
    '64454': {'l16A': '', 'l16B': '', 'l18B': ''},
    '66200': {'l14B': ''},
    '68320': {'l14B': ''},
    '68441': {'l14B': ''},
    '73119': {'l16A': ''},
    '65637': {'l18B': ''},
}
# Cells whose written digits are illegible, overwritten, clipped or stamp-covered and whose
# value was settled by the identities (kept as read, counted as derived).
ILLEGIBLE = {
    '72865': ['l16B', 'l17aA', 'l17cA'],
    '72781': ['l15aB'],
    '60820': ['l13A'],
    '60889': ['l15aB'],
    '64477': ['l13A', 'l18A'],
    '65634': ['l13A', 'l15aA', 'l15cA', 'l15aB'],
    '65636': ['l15aB'],
    '65652': ['l17aA'],
    '65663': ['l18B', 'l15aB'],
    '65619': ['l16A', 'l16B'],
    '62637': ['l17aA', 'l17bA'],
    '68239': ['l17cA', 'l17cB'],
    '68228': ['l16A', 'l16B', 'l17aA', 'l17cA', 'l17aB', 'l17cB'],
    # non-sample docs whose first-reading notes describe overwritten/obscured/clipped digits
    '60824': ['unspecified overwritten digits'],
    '60845': ['l15bA'],
    '60878': ['l17cA', 'l18A'],
    '64466': ['l15aB'],
    '66218': ['l13A'],
    '65706': ['l17cB'],
    '68207': ['l15aB'],
}
WHY_CLEARED = {
    '71864': 'line 16 blank in both columns (identities give 0, read as nil)',
    '72879': 'line 16 blank in both columns',
    '72885': 'line 15c blank in both columns',
    '72776': 'line 16B blank',
    '64454': 'lines 16A, 16B and 18B blank',
    '66200': 'line 14B blank',
    '68320': 'line 14B blank',
    '68441': 'line 14B blank',
    '73119': 'line 16A handwritten entry scribbled out (a typed template 0.00 sits beside it); line 14B blank',
    '65637': 'line 18B clipped at the right edge (reads 2,800.1_)',
}

# Columns not transcribable (clipped off the scan): identities in that column are not applied.
INACTIVE_COLS = {'69855': 'B'}

# Doc 68321 (Eli Wax, 2025 annual) was posted as a PNG with a .bin extension and was not rendered
# in the first pass; transcribed during adjudication directly from the PNG (single reading).
EXTRA_DOCS = {
    '68321': dict(doc_id='68321', tab='2025-annual', committee='Eli Wax for South Bend Common Council',
                  candidate='Eliyahu A Wax', office='South Bend Common Council District 5',
                  party='Republican', report_type='Annual', period_from='2025-01-01',
                  period_to='2025-12-31', amended='No', l13A='1669.90', l14B='1669.90',
                  l15aA='0', l15bA='1.06', l15cA='1.06', l16A='1670.96', l17aA='0', l17bA='0',
                  l17cA='0', l18A='1670.96', l15aB='0', l15bB='1.06', l15cB='1.06', l16B='1670.96',
                  l17aB='0', l17bB='0', l17cB='0', l18B='1670.96', l19='0', l20='0',
                  status='verified', checks_passed='all',
                  notes='File posted as a PNG with a .bin extension; not rendered in the first pass. '
                        'Transcribed once during adjudication from the PNG (typed form). Line 19 zero '
                        'partly under the clerk stamp.'),
}

# Header-field corrections (reader annotations moved to notes, or obvious reader slips).
FIELD_OVERRIDES = {
    '60873': {'committee': 'Committee to Elect Ophelia', 'candidate': 'Ophelia Gooden-Rodgers'},
    '68228': {'committee': 'Committee to Elect Ophelia'},
    '65663': {'committee': 'Committee to Elect Ophelia'},
    '68214': {'committee': 'Liberty Township'},
    '68170': {'committee': 'Janice Ann Cervelli'},
    '66174': {'committee': 'Committee to Elect John Murphy St. Joseph County Auditor',
              'office': 'St. Joseph County Auditor'},
    '68154': {'candidate': 'Mary C Willson'},
    '68199': {'office': 'None'},
    '60847': {'office': ''},
    '60872': {'office': 'St. Joseph County Commissioner, Dist 2'},
    '60842': {'office': 'P-H-M School Board Trustee, Penn Twp Seat 1'},
    '66168': {'office': 'Mishawaka Common Council at Large'},
    '65614': {'office': 'South Bend Common Council'},
    '65624': {'office': 'County Council - District i'},
    '68251': {'committee': 'Committe to elect Canneth Lee',
              'office': '1 sy District Common Council South Bend'},
    '60820': {'office': 'None (not seeking any office)'},
    '70515': {},
    '60862': {'party': 'Republican'},  # line 6 blank; line 8 (candidate party) reads Republican on the image
}
ANNOT = re.compile(r'\s*(\[[^\]]*\]|\((?:as written|as typed|handwritten|handwriting[^)]*|written [^)]*|nickname [^)]*|committee name[^)]*|[^)]*per committee name|in 20\d\d|20\d\d|district partly legible|office line blank[^)]*|St\. Joseph)\))', re.I)


def clean(s):
    return ANNOT.sub('', s or '').strip()


# ----------------------------------------------------------------------------------------------
# 2. Identity engine
# ----------------------------------------------------------------------------------------------
def idents(c):
    s = 'l13A' if c == 'A' else 'l14B'
    return [('15c' + c, 'l15c' + c, 'l15a' + c, 'l15b' + c, 1),
            ('17c' + c, 'l17c' + c, 'l17a' + c, 'l17b' + c, 1),
            ('16' + c, 'l16' + c, s, 'l15c' + c, 1),
            ('18' + c, 'l18' + c, 'l16' + c, 'l17c' + c, -1)]


IDS = idents('A') + idents('B')
COLCELLS = {'A': ['l15aA', 'l15bA', 'l15cA', 'l16A', 'l17aA', 'l17bA', 'l17cA', 'l18A'],
            'B': ['l15aB', 'l15bB', 'l15cB', 'l16B', 'l17aB', 'l17bB', 'l17cB', 'l18B']}


def evaluate(cells, period_from='', period_to='', inactive=''):
    """cells: dict of written values (Decimal or None).
    Returns (values, derived, nil, fails). Blank cells are filled only when the identities pin
    them (single step, never from a total that itself fails); a pinned value of 0 is 'nil'
    (blank read as none), a non-zero pinned value is 'derived'."""
    g = dict(cells)
    derived, nil = set(), set()
    active = {c: c not in inactive and any(g[k] is not None for k in COLCELLS[c]) for c in 'AB'}

    def bad():
        b = set()
        for name, res, a, x, sg in IDS:
            if None not in (g[res], g[a], g[x]) and g[res] != g[a] + sg * g[x]:
                b.add(res)
        return b

    def put(k, v):
        g[k] = v
        (derived if v != 0 else nil).add(k)

    for c in 'AB':
        if not active[c]:
            continue
        s = 'l13A' if c == 'A' else 'l14B'
        a15, b15, c15 = 'l15a' + c, 'l15b' + c, 'l15c' + c
        a17, b17, c17 = 'l17a' + c, 'l17b' + c, 'l17c' + c
        t16, t18 = 'l16' + c, 'l18' + c
        # subtotal from parts / one missing part from a written subtotal
        for a, b, t in ((a15, b15, c15), (a17, b17, c17)):
            if g[t] is None and (g[a] is not None or g[b] is not None):
                put(t, (g[a] or 0) + (g[b] or 0))
            elif g[t] is not None and (g[a] is None) != (g[b] is None):
                k = a if g[a] is None else b
                other = g[b] if k == a else g[a]
                put(k, g[t] - other)
        # an entirely blank receipts group under a written line 16 with a written start
        if g[c15] is None and g[a15] is None and g[b15] is None:
            if g[t16] is not None and g[s] is not None and t16 not in bad():
                put(c15, g[t16] - g[s])
            else:
                put(c15, D(0))
        if g[c17] is None and g[a17] is None and g[b17] is None:
            put(c17, D(0))
        # opening cash pinned by a written line 16
        if g[s] is None and g[t16] is not None:
            put(s, g[t16] - g[c15])
        # line 16 and line 18 from their inputs, unless an input is itself inconsistent
        if g[t16] is None:
            bb = bad()
            if c15 not in bb:
                put(t16, (g[s] or 0) + g[c15])
        if g[t18] is None and g[t16] is not None:
            bb = bad()
            if t16 not in bb and c17 not in bb:
                put(t18, g[t16] - g[c17])
    fails = []
    for name, res, a, x, sg in IDS:
        if None in (g[res], g[a], g[x]) or name[-1] in inactive:
            continue
        if g[res] != g[a] + sg * g[x]:
            fails.append(f'{name}: written {fmt(g[res])}, computed {fmt(g[a] + sg * g[x])}')
    if g['l18A'] is not None and g['l18B'] is not None and g['l18A'] != g['l18B'] and not inactive:
        fails.append(f'18A {fmt(g["l18A"])} != 18B {fmt(g["l18B"])}')
    # same-span identity: a period starting Jan 1 of its own year makes columns A and B the same span
    if (period_from or '').endswith('-01-01') and period_to[:4] == period_from[:4]:
        for a, b in (('l13A', 'l14B'), ('l15cA', 'l15cB'), ('l17cA', 'l17cB')):
            if a in nil or b in nil:
                continue
            if g[a] is not None and g[b] is not None and g[a] != g[b]:
                fails.append(f'period starts Jan 1 but {a[1:]} {fmt(g[a])} != {b[1:]} {fmt(g[b])}')
    return g, derived, nil, fails


# ----------------------------------------------------------------------------------------------
# 3. Normalisation helpers
# ----------------------------------------------------------------------------------------------
def norm_party(p, office_norm):
    s = (p or '').strip().lower()
    if not s:
        return '', ''
    if 'redemption' in s:
        return 'O', 'Party written as Indiana Redemption Party (label O = other).'
    if 'struck' in s:
        return 'D', 'Party field shows a struck-through D.'
    if re.search(r'non[- ]?partis', s):
        return 'NP', ''
    if s in ('n/a', 'none', 'n-a (line 6 blank)', 'n/a (non-partisan)'):
        if 'school board' in office_norm.lower() or 'non-candidate' in office_norm.lower() or not office_norm:
            return 'NP', f'Party written as "{p}".'
        return '', f'Party written as "{p}" on a partisan-office filing; left blank.'
    if s.startswith('libert'):
        return 'L', ''
    if s.startswith('independ'):
        return 'I', ''
    if re.match(r'(republican|rep\b|gop|r\b|r \(|reb)', s):
        return 'R', ''
    if re.match(r'(democrat|dem\b|dem\.|d\b)', s):
        return 'D', ''
    raise ValueError(f'unmapped party {p!r}')


def norm_report(t):
    s = (t or '').lower()
    if not s.strip() or 'none checked' in s or 'no box' in s:
        return ''
    parts = []
    if 'pre-primary' in s and ('annual' in s):
        return 'Pre-Primary; Annual'
    if 'annual' in s and 'final' in s:
        return 'Annual; Final'
    if 'final' in s:
        return 'Final'
    if s.startswith('pre-election'):
        return 'Pre-Election'
    if s.startswith('pre-primary'):
        return 'Pre-Primary'
    if s.startswith('annual'):
        return 'Annual'
    if 'outgoing' in s:
        return 'Outgoing Treasurer'
    if s.startswith('other'):
        return 'Other'
    raise ValueError(f'unmapped report type {t!r}')


def norm_yesno(a):
    s = (a or '').strip().lower()
    return {'yes': 'yes', 'y': 'yes', 'no': 'no', 'n': 'no', '': ''}[s]


TOWNSHIPS = ['centre', 'clay', 'german', 'greene', 'green', 'harris', 'liberty', 'lincoln',
             'madison', 'olive', 'penn', 'portage', 'union', 'warren']
TOWNS = {'walkerton': 'walkerton', 'new carlisle': 'new-carlisle', 'north liberty': 'north-liberty',
         'roseland': 'roseland', 'lakeville': 'lakeville', 'osceola': 'osceola'}
COUNTY_OFFICES = [('assessor', 'County Assessor'), ('auditor', 'County Auditor'),
                  ('recorder', 'County Recorder'), ('treasurer', 'County Treasurer'),
                  ('surveyor', 'County Surveyor'), ('coroner', 'County Coroner'),
                  ('sheriff', 'County Sheriff'), ('prosecut', 'County Prosecutor')]


def dist_num(s):
    m = (re.search(r'(?:district|dist\.?|seat)\s*[#"]?\s*(\d)\b', s)
         or re.search(r'\b(\d)\s*(?:st|nd|rd|th|sy)?\s*district', s))
    if m:
        return m.group(1)
    for w, n in (('first', '1'), ('second', '2'), ('third', '3'), ('fourth', '4'), ('fifth', '5'), ('sixth', '6')):
        if re.search(rf'\b{w}\s+district', s):
            return n
    return None


def norm_office(o):
    """free text -> (label, unit_id) or (None, None) when the text does not identify an office."""
    s = re.sub(r'\s+', ' ', (o or '').lower()).strip()
    if not s or s in ('n/a', 'n-a') or s.startswith('none'):
        return None, None
    atl = bool(re.search(r'at[- ]large', s))
    # school boards
    if re.search(r'school|sbcsc|p-h-m|\bphm\b|penn ?harris|penn-harris', s):
        if 'school city of mishawaka' in s:
            return 'School City of Mishawaka School Board', 'school-city-mishawaka'
        if re.search(r'sbcsc|south bend', s):
            d = dist_num(s)
            if atl:
                return 'South Bend Community School Corporation Board At-Large', 'sbcsc'
            return (f'South Bend Community School Corporation Board District {d}' if d else
                    'South Bend Community School Corporation Board (seat not stated)'), 'sbcsc'
        if re.search(r'p-h-m|\bphm\b|penn ?harris|penn-harris', s) or 'penn township' in s:
            s2 = re.sub(r'penn[- ]?harris[- ]?madison|pennharris[- ]?madison|p-h-m|\bphm\b', ' ', s)
            for t in ('penn', 'harris', 'madison'):
                if re.search(rf'\b{t}\b', s2):
                    return f'Penn-Harris-Madison School Board, {t.title()} Township seat', 'phm'
            return 'Penn-Harris-Madison School Board (seat not stated)', 'phm'
        if atl:
            return None, None
        return None, None
    # townships
    m = re.search(r'\b(' + '|'.join(TOWNSHIPS) + r')\s+(?:township|twp)\b', s) or \
        re.search(r'(?:township|twp)\b.*?\b(' + '|'.join(TOWNSHIPS) + r')\b', s)
    if m and 'county' not in s.replace('st. joseph c', ''):
        t = m.group(1)
        t = 'greene' if t == 'green' else t
        if 'assessor' in s:
            return f'{t.title()} Township Assessor', f'{t}-township'
        if 'trustee' in s:
            return f'{t.title()} Township Trustee', f'{t}-township'
        if 'board' in s:
            return f'{t.title()} Township Board', f'{t}-township'
    # towns
    for tn, uid in TOWNS.items():
        if tn in s:
            if 'judge' in s or 'court' in s:
                return f'{tn.title()} Town Court Judge', uid
            w = re.search(r'ward\s*(\d)', s)
            if w:
                return f'{tn.title()} Town Council Ward {w.group(1)}', uid
            if atl:
                return f'{tn.title()} Town Council At-Large', uid
            return f'{tn.title()} Town Council', uid
    if re.search(r'clerk[- ]treasurer', s):
        return 'Town Clerk-Treasurer (town not stated)', None
    # circuit court clerk before judges/council
    if 'clerk' in s and 'circuit' in s:
        return 'Clerk of the Circuit Court', 'county'
    if 'probate' in s:
        return 'Probate Court Judge', 'sjc-courts'
    if 'circuit' in s and 'judge' in s:
        return 'Circuit Court Judge', 'sjc-courts'
    # cities
    if 'mishawaka' in s:
        if 'mayor' in s:
            return 'Mayor of Mishawaka', 'mishawaka'
        if 'clerk' in s:
            return 'Mishawaka City Clerk', 'mishawaka'
        if atl:
            return 'Mishawaka Common Council At-Large', 'mishawaka'
        d = dist_num(s)
        if d:
            return f'Mishawaka Common Council District {d}', 'mishawaka'
    if 'south bend' in s:
        if 'mayor' in s:
            return 'Mayor of South Bend', 'south-bend'
        if 'clerk' in s:
            return 'South Bend City Clerk', 'south-bend'
        if 'council' in s:
            if atl:
                return 'South Bend Common Council At-Large', 'south-bend'
            d = dist_num(s)
            if d:
                return f'South Bend Common Council District {d}', 'south-bend'
            return 'South Bend Common Council (district not stated)', 'south-bend'
    # county council / commissioners
    if 'commissioner' in s:
        d = dist_num(s)
        return (f'County Commissioner District {d}' if d else 'County Commissioner (district not stated)'), 'county'
    if 'council' in s and ('county' in s or re.search(r'council (?:-|,|;)?\s*(?:district|dist|seat)', s)):
        m = (re.search(r'(?:district|dist\.?|seat)\s*"?([a-i1])"?\b', s) or re.search(r'council\s+([a-i])$', s))
        if m:
            d = m.group(1).upper()
            d = 'I' if d == '1' else d
            return f'County Council District {d}', 'county'
        return 'County Council (district not stated)', 'county'
    for key, label in COUNTY_OFFICES:
        if key in s:
            return label, 'county'
    return None, None


# results-assisted resolution of offices whose text omits the unit (doc -> label, unit, why)
OFFICE_RESOLVE = {
    'Karen White': ('South Bend Common Council At-Large', 'south-bend',
                    'form says "Common Council At Large"; city from results.csv (2023 South Bend at-large ballot)'),
    'Bianca Tirado': ('South Bend City Clerk', 'south-bend',
                      'form says "City Clerk"; city from results.csv (2023 South Bend City Clerk ballot)'),
    'Desmont Upchurch': ('Mayor of South Bend', 'south-bend',
                         'form says "Mayor"; city from results.csv (2023 South Bend mayoral ballot)'),
    'Theresa (Terri) Buckmaster': ('Walkerton Clerk-Treasurer', 'walkerton',
                                   'form says "Clerk Treasurer"; town from results.csv (2023 Walkerton ballot)'),
    'Elizabeth J. McCombs': ('Roseland Clerk-Treasurer', 'roseland',
                             'form says "Clerk-Treasurer"; town from results.csv (2023 Roseland ballot)'),
    'Judith Galloway': ('Centre Township Trustee', 'centre-township',
                        'form says "Trustee"; township from results.csv (2022 and 2026 Centre Township Trustee ballots)'),
    'George L Jones': ('South Bend Community School Corporation Board At-Large', 'sbcsc',
                       'form says "School Board At Large"; corporation from results.csv (2024 SBCSC at-large ballot)'),
    'James Mueller': ('Mayor of South Bend', 'south-bend', 'form says "Mayor"; city from the committee name on the form'),
    'Sharon McBride': (None, None, ''),
}
# Results hints for filings with no office on the form (recorded in notes only; never used to fill office_normalized)
RESULTS_HINT = {
    '72875': 'results.csv lists Michelle M Shaw on the 2022 and 2026 Clay Township Board ballots',
    '60873': 'results.csv lists Ophelia Gooden-Rodgers on the 2023 South Bend Common Council District 2 ballot',
    '65663': 'results.csv lists Ophelia Gooden-Rodgers on the 2023 South Bend Common Council District 2 ballot',
    '68228': 'results.csv lists Ophelia Gooden-Rodgers on the 2023 South Bend Common Council District 2 ballot',
    '66028': 'results.csv lists Sonia Perez on the 2023 South Bend Common Council District 3 ballot',
    '60852': 'results.csv lists Joshua P Gobel on the 2022 Clay Township Board ballot',
    '66175': 'results.csv lists Joshua P Gobel on the 2022 Clay Township Board ballot',
}


# ----------------------------------------------------------------------------------------------
# 4. Committee identity
# ----------------------------------------------------------------------------------------------
KEY_OVERRIDE = {
    # candidate committees whose candidate line is blank, odd, or spelled variously
    '66185': 'reese-gene', '68070': 'reese-gene',
    '68154': 'voelker-kate', '60856': 'voelker-kate', '65648': 'voelker-kate',
    '60887': 'mccormick-tom', '62640': 'mccormick-tom', '64479': 'mccormick-tom', '65616': 'mccormick-tom',
    '67984': 'mccormick-tom', '68121': 'mccormick-tom', '70521': 'mccormick-tom',
    '68162': 'mccullough-ryan', '64472': 'mccullough-ryan', '65671': 'mccullough-ryan',
    '66066': 'swager-tim', '68248': 'brown-julie', '66568': 'brown-julie',
    '68081': 'groves-william', '68156': 'middlebrook-robert', '66028': 'perez-sonia',
    '60873': 'gooden-rodgers-ophelia', '65663': 'gooden-rodgers-ophelia', '68228': 'gooden-rodgers-ophelia',
    '68214': 'dittmar-emily', '72951': 'rolfes-amy',
    # same candidate, separate committees
    '65622': 'drake-amy-exploratory', '67909': 'drake-amy-exploratory', '68150': 'drake-amy-exploratory',
    '65662': 'davis-oliver-council', '68226': 'davis-oliver-council',
    '60872': 'davis-oliver-commissioner', '65661': 'davis-oliver-commissioner', '68227': 'davis-oliver-commissioner',
}
NOTES_EXTRA = {
    '66082': 'Owner check: the form states the period 1/1/2023-12/31/2023, but its opening cash (1,731.53) equals the closing cash on '
             'this committee\'s 2023 annual report (doc 60837) and the county stamped it Feb 2025 in the 2024 batch; the year is '
             'probably miswritten for 2024. Period shown as written.',
    '60834': 'Undated amended report (no period on the form) with the same 51.70 cash as doc 63665 (marked Pre-Primary); kept as separate filings because the report types differ.',
    '63665': 'Undated amended report (no period on the form) with the same 51.70 cash as doc 60834 (marked Annual); kept as separate filings because the report types differ.',
    '68014': 'Period written as 1/1/2026-12/31/2026 although posted with the 2025 annual reports; shown as written.',
    '65634': 'Low confidence: very rough handwriting. 15a reads like 1,240 and 13A like 1,244.52; both readers took 1,940 and 1,249.52 (4/9 and 2/9 ambiguity) because only those tie to line 16 (3,189.52). Line 19 (1,315.67, last digit partly cut) sits where line 18 would be expected and may be a misplaced cash figure.',
    '65645': 'Line 15bA is blank but 15cA (597.92) exceeds 15aA (247.92) by 350.00; the identities fix 15bA at 350.00 (both readers had called this filer-inconsistent).',
    '68259': 'Expenditure lines and line 18 blank; cash at close derived as 284.35 by reading the blank lines as none. Opening cash 13A 284.35 differs from 14B 1,526.86 although the period starts 12/31/2024.',
    '67923': 'Scan is upside down.',
    '68263': 'Pre-Election box marked on a full-year 2025 report.',
}
NONCAND = {  # committee-name fragment -> key
    'democratic central': 'party-sjc-democratic-central-committee',
    'republican party': 'party-sjc-republican-party',
    'young republican': 'pac-sjc-young-republicans',
    "drake and o'brien pac": 'pac-drake-and-obrien',
    'save our schools': 'pac-save-our-schools',
    'our phm': 'pac-our-phm',
    'indiana redemption party': 'party-indiana-redemption-party',
    'mishawaka republican city committee': 'party-mishawaka-republican-city-committee',
    'firefighters political': 'pac-sjc-firefighters',
}


def cand_key(cand):
    s = re.sub(r'"[^"]*"|\([^)]*\)|\[[^\]]*\]', ' ', cand or '')
    s = re.sub(r',?\s*aka\b.*$', '', s, flags=re.I)
    s = re.sub(r'\b(jr|sr|ii|iii|md|dr)\b\.?', ' ', s, flags=re.I)
    toks = [t for t in re.split(r'[\s,]+', s) if t and not re.fullmatch(r'[A-Za-z]\.?', t)]
    if not toks:
        return None
    sur = re.sub(r'[^a-z\-]', '', toks[-1].lower())
    sur = {'kostielny': 'kostielney', 'deiter': 'dieter', 'goodin-rodgers': 'gooden-rodgers',
           'mammolenti': 'mammolent', 'ladfyga-block': 'ladyga-block', 'willson': 'voelker',
           'lement': 'lement'}.get(sur, sur)
    first = re.sub(r'[^a-z]', '', toks[0].lower())
    nick = {'matthew': 'matt', 'michael': 'mike', 'anthony': 'tony', 'robert': 'bobby', 'randall': 'randy',
            'kathryn': 'kate', 'jason': 'jason', 'rodolfo': 'rudy', 'ronald': 'ron', 'andrew': 'andy',
            'james': 'jamie', 'jacob': 'jake', 'joshua': 'josh', 'tamara': 'tami', 'kristian': 'kris',
            'daniel': 'dan', 'david': 'dave', 'deborah': 'deb', 'william': 'bill', 'christopher': 'chris',
            'patricia': 'patti', 'candance': 'candace', 'abigail': 'abby', 'edward': 'ed', 'janice': 'jan',
            'loris': 'loris', 'victor': 'vic', 'sheila': 'sheila', 'shelia': 'sheila', 'louann': 'lou',
            'lou': 'lou', 'eliyahu': 'eli', 'theresa': 'terri', 'elizabeth': 'elizabeth', 'dale': 'dale',
            'kenneth': 'ken', 'gregg': 'gregg', 'roderick': 'rod', 'rodney': 'rod', 'patric': 'pat',
            'earl': 'earl', 'charles': 'charles', 'marcellus': 'marcel', 'maggie': 'maggie', 'muhammad': 'muhammad',
            'joseph': 'joe', 'thomas': 'tom', 'scott': 'scott', 'carl': 'carl', 's': 's'}.get(first, first)
    return f'{sur}-{nick}'


def committee_key(r):
    d = r['doc_id']
    if d in KEY_OVERRIDE:
        return KEY_OVERRIDE[d]
    cm = (r['committee'] or '').lower()
    for frag, k in NONCAND.items():
        if frag in cm:
            return k
    c = r['candidate']
    if c and c.strip().upper() not in ('N/A', 'NONE'):
        return cand_key(c)
    return 'cmte-' + re.sub(r'[^a-z0-9]+', '-', cm).strip('-')


# Committees that are the same candidate but separate committees (keep apart)
SPLIT_BY_COMMITTEE = {'drake-amy', 'davis-oliver', 'morton-rafael', 'redman-bill', 'demaegd-maggie',
                      'kruszynski-bobby', 'hazen-tony', 'banicki-sharon', 'castellon-mike'}


def final_key(k, office_label, committee):
    """Published committee key. Candidate-level keys are kept for office inference (a candidate's
    other forms fill a blank office line), but candidates in SPLIT_BY_COMMITTEE ran separate
    committees for separate races, so their published key is split by the office sought
    (or by the committee name when the form states no office)."""
    if k not in SPLIT_BY_COMMITTEE:
        return k
    part = office_label if office_label and 'not stated' not in office_label else committee
    return k + '--' + re.sub(r'[^a-z0-9]+', '-', (part or '').lower()).strip('-')


# ----------------------------------------------------------------------------------------------
# 5. Duplicate / amendment groups (decided by hand after listing same-committee same-period docs)
# ----------------------------------------------------------------------------------------------
DUP_GROUPS = [
    # (kept doc, [all docs], note)
    ('68223', ['67916', '68223'], 'The county posted the same final report twice (docs 67916 and 68223, identical figures); later posting kept.'),
    ('70547', ['70548', '70547'], 'Doc 70547 is marked as an amendment of the same pre-primary report as doc 70548 (file 76-16-14) with different figures (15a 3,600 vs 1,600; 17a 6,643.21 vs 8,643.21); amended figures shown.'),
    ('73125', ['72816', '73113', '73125'], 'Three postings of the 2026 pre-election report: docs 72816 and 73113 (not amended) and 73125 (amendment); same closing cash. Amendment shown.'),
    ('68124', ['67982', '68124'], 'Doc 68124 is an amendment of doc 67982 (same figures); amendment shown.'),
    ('72778', ['71298', '72778'], 'Doc 72778 is an amended pre-primary report (period through 04/10/2026) replacing doc 71298 (period through 04/14/2026; closing cash 5,853.04 vs 6,013.89); amendment shown.'),
    ('68127', ['68071', '68127'], 'Docs 68071 and 68127 carry the same figures; 68127 is a handwritten re-filing on the newer form (county title says Amended, but the form\'s amendment box is No). Later re-filing kept.'),
    ('73116', ['72861', '73116'], 'Doc 73116 is an amendment of doc 72861 (closing cash 24,982.74 vs 5,982.74); amendment shown.'),
    ('68210', ['68084', '68210'], 'The county posted the same 2025 annual report twice (docs 68084 and 68210, identical figures); later posting kept.'),
    ('68171', ['67912', '68171'], 'The county posted the same 2025 annual report twice (docs 67912 and 68171, identical figures; 68171 has no report-type box checked); later posting kept.'),
    ('68125', ['67922', '68125'], 'Docs 67922 and 68125 carry the same figures (county title of 68125 says Amended; the form\'s amendment box is No); later posting kept.'),
    ('68172', ['67915', '68172'], 'Doc 68172 is an amendment of doc 67915 (same figures; report-type boxes differ); amendment shown.'),
    ('68150', ['67909', '68150'], 'Doc 68150 is an amendment of doc 67909 (same figures); amendment shown.'),
    ('68230', ['68161', '68230'], 'The county posted the same 2025 annual report twice (docs 68161 and 68230); later posting kept.'),
    ('64481', ['64481', '64486'], 'The county posted the same pre-election report twice (doc 64481 in the pre-election tab, doc 64486 in the pre-primary tab; identical figures); pre-election-tab copy kept.'),
    ('65667', ['65643', '65667'], 'The county posted the same 2024 annual report twice (docs 65643 and 65667, identical figures); later posting kept.'),
    ('68148', ['68075', '68148'], 'The county posted the same 2025 annual report twice (docs 68075 and 68148, identical figures); later posting kept.'),
    ('60871', ['60870', '60871'], 'The county posted the 2023 annual report twice (doc 60870 "2023 Annual" and doc 60871 "2023 Signed Summary", identical figures); signed copy kept.'),
    ('68152', ['67911', '67919', '68152'], 'Three postings of the 2025 annual report: doc 67911 (original) and docs 67919 and 68152 (both marked amendments; identical figures). Latest amendment kept.'),
    ('68183', ['68184', '68183'], 'Doc 68183 is an amendment of doc 68184 (same figures); amendment shown.'),
    ('72952', ['72950', '72952'], 'Doc 72952 is an amendment of doc 72950 (closing cash 231,769.97 vs 197,513.19); amendment shown.'),
    ('64476', ['64475', '64476'], 'The county posted the same pre-election report twice (docs 64475 and 64476, identical figures); later posting kept.'),
    ('68277', ['68122', '68277'], 'Doc 68277 is an amendment of doc 68122 (closing cash 21,336.61 vs 20,836.61); amendment shown.'),
    ('68330', ['65624', '68330'], 'The county posted the 2024 annual report (period 10/12/2024-12/31/2024) twice: doc 65624 in the 2024 tab and doc 68330 in the 2025 tab, identical figures; later posting kept.'),
    ('68235', ['67917', '68235'], 'Doc 68235 is an amendment of doc 67917 (same figures; amendment Yes and No boxes both marked); amendment shown.'),
    ('68121', ['67984', '68121'], 'Doc 68121 is an amendment of doc 67984 (same figures); amendment shown.'),
    ('64459', ['64458', '64459'], 'The county posted the same pre-election report twice (docs 64458 and 64459, identical figures); later posting kept.'),
    ('68155', ['67914', '68155'], 'Doc 68155 is an amendment of doc 67914 (same figures); amendment shown.'),
    ('68229', ['68051', '68229'], 'Doc 68229 is an amendment of doc 68051 (same figures); amendment shown.'),
    ('68257', ['65649', '68257'], 'Doc 68257 is an amendment of doc 65649 (expenditures raised by 1,800.00; closing cash 352.22 vs 2,152.22); amendment shown.'),
    ('70539', ['70533', '70539'], 'The county posted the same pre-primary report twice (doc 70539, and doc 70533 whose county title reads "Jacob Jake Baska" although the form is the Josh Lange committee); identical figures; later posting kept.'),
]


def main():
    first = load('research/cf/visual-chunk-*.csv')
    second = load('research/cf/verify-[1-4].csv')
    manifest = {}
    for fn in sorted(glob.glob(R('sources', 'cf', 'pdf', '*', 'manifest.csv'))):
        batch = os.path.basename(os.path.dirname(fn))
        with open(fn, encoding='utf-8', newline='') as f:
            # the browser export wrote JSON-style \" inside quoted fields, not CSV-style ""
            for r in csv.DictReader(f, escapechar='\\', doublequote=False):
                r['batch'] = batch
                manifest[r['id']] = r
    for d, row in EXTRA_DOCS.items():
        first[d] = dict(row)

    # ---------------- line-level final readings ----------------
    lines = {}
    for d, r in first.items():
        r = dict(r)
        for k, v in CELL_OVERRIDES.get(d, {}).items():
            r[k] = v
        for k, v in FIELD_OVERRIDES.get(d, {}).items():
            r[k] = v
        for k in ('committee', 'candidate', 'office'):
            r[k] = clean(r[k])
        if r['status'] in ('not-summary', 'unreadable'):
            r['final_status'] = r['status']
            r['derived_cells'] = ''
            r['fails'] = ''
            r['nil_cells'] = ''
            lines[d] = r
            continue
        cells = {k: num(r[k]) for k in NUM}
        g, der, nil, fails = evaluate(cells, r['period_from'], r['period_to'], INACTIVE_COLS.get(d, ''))
        der = sorted(der) + [c for c in ILLEGIBLE.get(d, []) if c not in der]
        for k in NUM:
            r[k] = fmt(g[k]) if (g[k] is not None and (k in der or k not in nil or cells[k] is not None)) else ''
        st = 'filer-inconsistent' if fails else ('derived' if der else 'verified')
        r['final_status'] = st
        r['derived_cells'] = ';'.join(der)
        r['nil_cells'] = ';'.join(sorted(k for k in nil if cells[k] is None))
        r['fails'] = ' | '.join(fails)
        lines[d] = r

    # ---------------- double-entry classification ----------------
    def de_class(d):
        if d not in second:
            return 'single'
        a, b = first[d], second[d]
        diff = [k for k in NUM if num(a[k]) != num(b[k])]
        if diff or a['status'] != b['status']:
            return 'adjudicated'
        return 'agreed'

    # ---------------- write line-level file ----------------
    LHDR = ['doc_id', 'tab', 'committee', 'candidate', 'office', 'party', 'report_type', 'period_from',
            'period_to', 'amended'] + NUM + ['first_status', 'final_status', 'derived_cells', 'nil_cells',
                                            'identity_failures', 'double_entry', 'notes']
    with open(R('research', 'cf', 'cf_lines_final.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(LHDR)
        for d in sorted(lines, key=int):
            r = lines[d]
            w.writerow([r['doc_id'], r['tab'], r['committee'], r['candidate'], r['office'], r['party'],
                        r['report_type'], r['period_from'], r['period_to'], r['amended']] +
                       [r[k] for k in NUM] + [first[d]['status'], r['final_status'], r['derived_cells'],
                                              r['nil_cells'], r['fails'], de_class(d), first[d]['notes']])

    # ---------------- sources ----------------
    with open(R('data', 'editions', 'st-joseph', 'sources_cf_local.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['id', 'url', 'title', 'publisher', 'accessed', 'kind', 'notes'])
        for d in sorted(manifest, key=int):
            m = manifest[d]
            note = f'County tab "{m["tab"]}" (local batch {m["batch"]}); {m["orig_pages"] or "?"} page(s).'
            if m['ext'] != 'pdf':
                note += f' Served as a {m["ext"]} file (PNG image).'
            w.writerow([f'CFL-{d}', f'https://www.sjcindiana.gov/DocumentCenter/View/{d}', m['title'],
                        'St. Joseph County, Indiana (county website DocumentCenter)', '2026-11-07', 'primary', note])

    # ---------------- filings ----------------
    summ = {d: r for d, r in lines.items() if r['final_status'] != 'not-summary'}
    keyof = {d: committee_key(r) for d, r in summ.items()}
    officeof = {}
    for d, r in summ.items():
        lab, uid = norm_office(r['office'])
        officeof[d] = (lab, uid, '')
    # resolve via named-candidate rules
    for d, r in summ.items():
        for cand, (lab, uid, why) in OFFICE_RESOLVE.items():
            toks = re.findall(r'[a-z]+', cand.lower())
            ctoks = re.findall(r'[a-z]+', (r['candidate'] or '').lower())
            if lab and toks[0] in ctoks and toks[-1] in ctoks and (
                    officeof[d][0] is None or 'not stated' in (officeof[d][0] or '') or
                    re.fullmatch(r'(mayor|city clerk|trustee|clerk[- ]treasurer|common council at large|school board at large)',
                                 (r['office'] or '').strip().lower())):
                officeof[d] = (lab, uid, why)
    # resolve via the committee name on the form, then the same committee's other forms
    by_key = collections.defaultdict(list)
    for d in summ:
        by_key[keyof[d]].append(d)
    for d, r in lines.items():  # CFA-11 notices are forms of the same candidate committees
        if r['final_status'] == 'not-summary' and r['candidate'] and d not in ('66024', '70515'):
            k = committee_key(r)
            lab, uid = norm_office(r['office'])
            officeof[d] = (lab, uid, '')
            keyof[d] = k
            by_key[k].append(d)
    for d, r in summ.items():
        lab, uid, why = officeof[d]
        if lab is None or 'not stated' in lab:
            l2, u2 = norm_office(r['committee'] + ' ' + r['office'])
            if l2 and (lab is None or 'not stated' not in l2):
                officeof[d] = (l2, u2, 'office line blank or incomplete; office taken from the committee name on the form')
                lab = l2
        if lab is None or 'not stated' in (lab or ''):
            prefix = (lab or '').split(' (')[0]
            others = {officeof[o][0] for o in by_key[keyof[d]] if o != d and officeof[o][0] and 'not stated' not in officeof[o][0]
                      and officeof[o][0].startswith(prefix)}
            if len(others) == 1:
                lab2 = others.pop()
                uid2 = next(officeof[o][1] for o in by_key[keyof[d]] if officeof[o][0] == lab2)
                src = ','.join(sorted(o for o in by_key[keyof[d]] if officeof[o][0] == lab2))
                officeof[d] = (lab2, uid2, f'office not (fully) stated on this form; taken from the same committee\'s other filing(s): doc {src}')
    for d, r in summ.items():
        if keyof[d].startswith(('party-', 'pac-')) or (not r['candidate'] and keyof[d].startswith('cmte-') and officeof[d][0] is None
                                                       and re.search(r'pac|party|committee$', r['committee'], re.I)):
            officeof[d] = ('Non-candidate committee (party/PAC/issue)', '', '')
        if r['office'].lower().startswith('none') and officeof[d][0] is None:
            officeof[d] = ('No office sought (stated on form)', '', '')

    kept_of = {}
    group_note = {}
    group_docs = {}
    for kept, docs, note in DUP_GROUPS:
        for x in docs:
            kept_of[x] = kept
        group_note[kept] = note
        group_docs[kept] = docs
    rows = []
    for d in sorted(summ, key=int):
        if kept_of.get(d, d) != d:
            continue
        r = summ[d]
        docs = group_docs.get(d, [d])
        lab, uid, owhy = officeof[d]
        party, pnote = norm_party(r['party'], lab or '')
        rt = norm_report(r['report_type'])
        notes = []
        if group_note.get(d):
            notes.append(group_note[d])
        raw_rt = (r['report_type'] or '').strip()
        if raw_rt and raw_rt not in ('Annual', 'Pre-Election', 'Pre-Primary', 'Final/Disbands', 'Other'):
            notes.append(f'Report type as marked: {raw_rt}.')
        if owhy:
            notes.append(f'office_normalized: {owhy}.')
        if (lab or '') == 'County Council District I' and re.search(r'\b1\b', r['office']):
            notes.append('Office written with district "1"; County Council districts are lettered A-I, so read as District I.')
        if not lab:
            hint = RESULTS_HINT.get(d)
            notes.append('No office on the form; office_normalized left blank' + (f' ({hint}).' if hint else '.'))
        if pnote:
            notes.append(pnote)
        for x in docs:
            if x in NOTES_EXTRA:
                notes.append(NOTES_EXTRA[x])
        st = r['final_status']
        if st == 'unreadable':
            notes.append('Scan too degraded to transcribe; legible cells only: 13A 1,841.86; 14B 2,720.21; 15aA 1,500.00 (faint); '
                         '17aA and 17aB 880.57; 18A 2,720.01 (faint). These do not reconcile. Needs a better copy.')
        if st == 'derived':
            why = WHY_CLEARED.get(d, '')
            notes.append('Derived cells (blank, illegible or clipped on the form; values fixed by the form identities): '
                         + r['derived_cells'] + (f' ({why})' if why else '') + '.')
        if st == 'filer-inconsistent':
            notes.append('Figures shown as filed; the form\'s own numbers do not reconcile: ' + r['fails'] + '.')
        if r['nil_cells'] and st != 'unreadable':
            notes.append('Blank lines read as none: ' + r['nil_cells'].replace('l', '') + '.')
        de = de_class(d)
        if de == 'adjudicated':
            notes.append('Second reading differed; see research/cf/adjudication.md.')
        notes.append('First-reading notes: ' + re.sub(r'\s+', ' ', first[d]['notes']).strip())
        fig = (lambda k: '' if st == 'unreadable' else r[k])
        rows.append(dict(
            filing_id=f'cfl-{d}', doc_ids=';'.join(sorted(docs, key=int)), committee=r['committee'],
            candidate=r['candidate'] if r['candidate'].upper() not in ('N/A', 'NONE') else '',
            office=r['office'], office_normalized=lab or '', unit_id=uid or '', party=party,
            report_type=rt, period_from=r['period_from'], period_to=r['period_to'],
            amended=norm_yesno(r['amended']),
            receipts_period=fig('l15cA'), expenditures_period=fig('l17cA'), cash_start_period=fig('l13A'),
            cash_end_period=fig('l18A'), receipts_ytd=fig('l15cB'), expenditures_ytd=fig('l17cB'),
            cash_jan1=fig('l14B'), cash_end_ytd=fig('l18B'), debts_owed_by=fig('l19'),
            transcription_status=st, double_entry=de, status='from_scan',
            source_ids=';'.join(f'CFL-{x}' for x in sorted(docs, key=int)),
            notes=' '.join(notes), _key=final_key(keyof[d], lab, r['committee'])))
    CF_HDR = ['filing_id', 'doc_ids', 'committee', 'candidate', 'office', 'office_normalized', 'unit_id', 'party',
              'report_type', 'period_from', 'period_to', 'amended', 'receipts_period', 'expenditures_period',
              'cash_start_period', 'cash_end_period', 'receipts_ytd', 'expenditures_ytd', 'cash_jan1', 'cash_end_ytd',
              'debts_owed_by', 'transcription_status', 'double_entry', 'status', 'source_ids', 'notes']
    with open(os.path.join(ED, 'cf_local.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, CF_HDR, extrasaction='ignore')
        w.writeheader()
        for row in rows:
            w.writerow(row)
    with open(R('research', 'cf', '_committee_keys.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['filing_id', 'committee_key'])
        for row in rows:
            w.writerow([row['filing_id'], row['_key']])
    return rows, lines, first, second


# ----------------------------------------------------------------------------------------------
# 6. CFA-11 large-contribution notices (entries read from the images during adjudication;
#    contributor names as printed, no addresses or occupations)
# ----------------------------------------------------------------------------------------------
CFA11 = [
    # doc, contributor, amount, date, contribution type / note
    ('73114', 'Mishler for State Senate', '2000.00', '2026-11-02', 'Direct; classification OTHER.'),
    ('72953', "James O'Brien", '2500.00', '2026-10-20', 'Direct; individual.'),
    ('73124', "Indiana Realtor's PAC", '1000.00', '2026-10-27', 'Direct; PAC.'),
    ('73120', "Drake and O'Brien PAC", '1500.00', '2026-10-23', 'Direct; PAC.'),
    ('72951', 'Phil Krause', '1000.00', '2026-10-16', 'Direct; individual. Period-from written 10/16/2016 (year slip); candidate line holds the committee name.'),
    ('73123', 'Indiana Realtors PAC', '1000.00', '2026-10-27', 'Direct; PAC.'),
    ('72802', 'Mary Beth Baker', '1000.00', '2026-10-19', 'Direct.'),
    ('72859', 'Doug Hunt', '7500.00', '2026-10-13', 'Direct.'),
    ('73115', 'John Maciejczyk', '1000.00', '2026-10-27', 'From the candidate himself; Direct and Loan boxes both marked (photographed page).'),
    ('72954', 'John Maciejczyk', '1000.00', '2026-10-20', 'From the candidate himself; direct.'),
    ('73111', 'Richard J. Pfeil', '6000.00', '2026-10-28', 'Direct; individual.'),
    ('73112', 'Indiana Realtors PAC', '2000.00', '2026-10-28', 'Direct; PAC. Notice marked as an amendment.'),
    ('73112', 'Industrial Equity Partners LLC', '1000.00', '2026-10-28', 'Direct; classification OTHER. Notice marked as an amendment.'),
    ('73112', 'Mishler For State Senate', '2000.00', '2026-10-31', 'Direct; PAC. Notice marked as an amendment.'),
    ('73121', 'Richard J Pfeil', '8000.00', '2026-04-22', 'Direct; individual. Received in April although posted with the pre-general notices.'),
    ('73117', 'Robert Price', '1066.49', '2026-10-14', 'From the candidate himself; direct. Notice marked as an amendment.'),
    ('72882', 'IBEW PAC Voluntary Fund', '1500.00', '2026-10-13', 'Direct; PAC.'),
    ('73122', "Tony's Mobile Service Inc.", '2000.00', '2026-10-29', 'Direct; corporation.'),
    ('73118', 'Robert Wozny', '11500.00', '2026-10-26', 'Direct; individual.'),
    ('72841', 'Nandi Corporation', '2000.00', '2026-10-15', 'Direct.'),
    ('72841', 'Central Indiana Construction PAC', '2500.00', '2026-10-15', 'Direct.'),
    ('71873', 'Richard Pfeil', '5000.00', '2026-04-15', 'Direct; individual. Period-from written 04/11/2016 (year slip).'),
    ('71875', 'Niezgodski for State Senator District 10', '1000.00', '2026-05-28', 'Direct. Received after the May 5 primary as printed.'),
    ('71875', 'Mueller for South Bend', '2500.00', '2026-05-28', 'Direct.'),
    ('71875', 'Alan Hogan', '1000.00', '2026-05-28', 'In-kind (event sponsor).'),
    ('71874', "Drake and O'Brien PAC", '132.50', '2026-04-29', 'In-kind (advertising); below $1,000 on its own. Mirror entry of doc 71869.'),
    ('71874', "Drake and O'Brien PAC", '466.00', '2026-04-15', 'In-kind (half of a Senior Life ad); below $1,000 on its own.'),
    ('71874', "Drake and O'Brien PAC", '2690.00', '2026-04-20', 'In-kind (half of a television commercial placement).'),
    ('71869', "Drake and O'Brien PAC", '132.50', '2026-04-29', 'In-kind (advertising); below $1,000 on its own. Same contribution as the doc 71874 entry seen from the other committee.'),
    ('71870', 'Doug Hunt', '10000.00', '2026-05-02', 'Direct; classification General Business.'),
    ('71871', 'International Brotherhood Electrical Workers', '5000.00', '2026-04-13', 'Direct; labor organization.'),
    ('71871', 'Iron Workers Local 292', '1000.00', '2026-04-20', 'Direct; labor organization.'),
    ('71871', 'Plumbers and Pipefitters, Local 172', '5000.00', '2026-04-20', 'Direct; labor organization.'),
    ('71871', 'Central Midwest Carpenters Union Local 413', '2500.00', '2026-04-24', 'Direct; labor organization (page 2).'),
    ('71872', 'Ashok Narang', '1000.00', '2026-04-24', 'Direct; individual.'),
    ('70540', 'IBEW PAC Voluntary Fund', '1530.00', '2026-04-07', 'Direct; PAC.'),
]
THRESHOLD_NOTE = ('Threshold confirmed from the form text: the CFA-11 header reads "Supplemental Large Contribution Report by a '
                  'Candidate\'s Committee ($1,000 contributions or more)", citing IC 3-9-5-20.1 and 3-9-5-22. The filing window '
                  '(contributions received shortly before an election) is not printed on the rendered page and is unverified here.')


def build_cfa11(rows, lines):
    comm_by_key = {}
    keys = {}
    with open(R('research', 'cf', '_committee_keys.csv'), encoding='utf-8') as f:
        for r in csv.DictReader(f):
            keys[r['filing_id']] = r['committee_key']
    key_years = collections.defaultdict(set)
    for row in sorted(rows, key=lambda x: x['period_to']):
        k = keys[row['filing_id']]
        if not k.startswith('drake-amy-exploratory'):
            comm_by_key[k] = row['committee']
            key_years[k].add(row['period_to'][:4])

    def split_lookup(k, date):
        """A CFA-11 names the candidate, often without the district. For candidates whose committees
        are split by race, use the one split committee that filed a CFA-4 in the notice's year;
        if none or several did, leave the committee blank rather than guess."""
        if k in comm_by_key:
            return k
        base = k.split('--')[0]
        hits = [kk for kk in comm_by_key if kk.startswith(base + '--') and date[:4] in key_years[kk]]
        return hits[0] if len(hits) == 1 else k

    out = []
    for d, contributor, amt, date, note in CFA11:
        r = lines[d]
        assert r['final_status'] == 'not-summary', d
        k = committee_key(r)
        if k in SPLIT_BY_COMMITTEE:
            k = split_lookup(final_key(k, norm_office(r['office'])[0], r['committee']), date)
        cand = r['candidate']
        if d == '72951':
            cand = 'Amy Rolfes'
        if d in ('73122', '73118'):
            cand = 'Scott Ruszkowski'
        if d in ('73112', '73121'):
            cand = 'Michael Castellon "Mike"'
        if d == '73117':
            cand = 'Robert L. "Bob" Price'
        if d == '72882':
            cand = 'Robert L. "Bobby K" Kruszynski Jr.'
        if d == '72841':
            cand = 'William Redman'
        comm = comm_by_key.get(k, '')
        n = note + (' Committee taken from the candidate\'s CFA-4 filings (the CFA-11 names only the candidate).' if comm else
                    ' No CFA-4 from this candidate committee is posted; committee left blank.')
        out.append(dict(doc_id=d, candidate=cand, committee=comm, contributor=contributor, amount=amt, date=date,
                        status='from_scan', source_ids=f'CFL-{d}', notes=n + ' ' + THRESHOLD_NOTE))
    with open(os.path.join(ED, 'cf_large_contributions.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, ['doc_id', 'candidate', 'committee', 'contributor', 'amount', 'date', 'status',
                               'source_ids', 'notes'])
        w.writeheader()
        for o in out:
            w.writerow(o)
    return out


# ----------------------------------------------------------------------------------------------
# 7. Coverage matrix
# ----------------------------------------------------------------------------------------------
EXPECTED = {'2023 municipal': ['Annual'], '2024': ['Pre-Primary', 'Pre-Election', 'Annual'],
            '2026': ['Annual', 'Pre-Primary', 'Pre-Election']}


def cycle_of(row):
    pt = row['period_to']
    if re.fullmatch(r'\d{4}', pt or ''):
        pt = pt + '-12-31'
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', pt or ''):
        return 'period unknown'
    y, m = int(pt[:4]), int(pt[5:7])
    if m <= 3 and any(t in row['report_type'] for t in ('Annual', 'Final', 'Outgoing')) or (m <= 3 and not row['report_type']):
        y -= 1  # an annual/final report closing in Jan-Mar covers the previous year
    if y <= 2023:
        return '2023 municipal'
    if y == 2024:
        return '2024'
    return '2026'


def build_coverage(rows):
    keys = {}
    with open(R('research', 'cf', '_committee_keys.csv'), encoding='utf-8') as f:
        for r in csv.DictReader(f):
            keys[r['filing_id']] = r['committee_key']
    cells = collections.defaultdict(list)
    for row in rows:
        cells[(row['office_normalized'] or '(no office stated on form)', row['unit_id'], cycle_of(row))].append(row)
    out = []
    order = {'2023 municipal': 0, '2024': 1, '2026': 2, 'period unknown': 3}
    for (off, uid, cyc), rs in sorted(cells.items(), key=lambda x: (x[0][0], order[x[0][2]])):
        comms = collections.defaultdict(set)
        for r in rs:
            for t in (r['report_type'] or 'not marked').split('; '):
                comms[keys[r['filing_id']]].add('Annual' if t == 'Final' else t)
        types = collections.Counter(r['report_type'] or 'not marked' for r in rs)
        froms = sorted(r['period_from'] for r in rs if r['period_from'])
        tos = sorted(r['period_to'] for r in rs if r['period_to'])
        exp = EXPECTED.get(cyc, [])
        full = sum(1 for k, ts in comms.items() if exp and all(e in ts for e in exp))
        st_counts = collections.Counter(r['transcription_status'] for r in rs)
        out.append(dict(
            office_normalized=off, unit_id=uid, cycle=cyc, committees=len(comms), filings=len(rs),
            report_types='; '.join(f'{t} ({n})' for t, n in sorted(types.items())),
            periods_covered=(f'{froms[0] if froms else "?"} to {tos[-1]}' if tos else ''),
            expected_report_types='; '.join(exp),
            committees_with_all_expected=(full if exp else ''),
            transcription_statuses='; '.join(f'{t} ({n})' for t, n in sorted(st_counts.items())),
            status='computed', source_ids=';'.join(sorted({s for r in rs for s in r['source_ids'].split(';')})),
            notes=('Cycle assigned from period_to (annual/final reports closing Jan-Mar count toward the prior year); '
                   '2025 annual reports are counted in the 2026 cycle.' +
                   (' Municipal offices are next elected in 2027, so their 2025 annual reports are off-cycle.'
                    if cyc == '2026' and uid in ('south-bend', 'mishawaka', 'walkerton', 'new-carlisle', 'north-liberty', 'roseland') and 'Town' not in off and 'Clerk-Treasurer' not in off else ''))))
    with open(os.path.join(ED, 'cf_coverage.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, ['office_normalized', 'unit_id', 'cycle', 'committees', 'filings', 'report_types',
                               'periods_covered', 'expected_report_types', 'committees_with_all_expected',
                               'transcription_statuses', 'status', 'source_ids', 'notes'])
        w.writeheader()
        for o in out:
            w.writerow(o)
    return out


if __name__ == '__main__':
    rows, lines, first, second = main()
    c = collections.Counter(r['transcription_status'] for r in rows)
    print(len(rows), 'filings', dict(c))
    lc = build_cfa11(rows, lines)
    print(len(lc), 'CFA-11 entries from', len({x['doc_id'] for x in lc}), 'notices')
    cov = build_coverage(rows)
    print(len(cov), 'coverage rows')
