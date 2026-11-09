"""Normalisation helpers for the results build (jurisdiction / office / district slugs)."""
import re

PARTY = {'DEM': 'D', 'D': 'D', 'REP': 'R', 'R': 'R', 'LIB': 'L', 'L': 'L', 'IND': 'I', 'I': 'I', 'NP': 'NP',
         'WI': 'W', 'W': 'W', 'write-in': 'W', 'WTP': 'O', 'IRP': 'O', 'LINC': 'O', 'LP': 'O', '': '', '-': ''}
PARTY_NOTE = {'WTP': 'party printed WTP (We The People)', 'IRP': 'party printed IRP (Indiana Redemption Party)',
              'LINC': 'party printed LINC (Lincoln Party)',
              'LP': 'party printed LP; meaning not stated in the canvass text'}


def slug(s):
    s = s.lower().replace('&', 'and')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def num(cell):
    """returns (value or None, uncertain flag, leftover note text)"""
    c = cell.strip()
    if not c:
        return None, False, ''
    unc = '?' in c
    m = re.match(r'^([0-9][0-9,\.]*)', c)
    val = None
    if m:
        t = m.group(1)
        if re.fullmatch(r'\d+\.\d{3}', t) and 'printed' in c:
            t = t.replace('.', '')
        val = float(t.replace(',', '')) if '.' in t else int(t.replace(',', ''))
        rest = c[m.end():]
    else:
        rest = c
    rest = rest.replace('(?)', '').replace('?', '').strip().strip('()').strip()
    return val, unc, rest.replace('"', "'")


TOWNS = {'lakeville': 'Lakeville', 'new carlisle': 'New Carlisle', 'north liberty': 'North Liberty',
         'osceola': 'Osceola', 'roseland': 'Roseland', 'walkerton': 'Walkerton'}
SCHOOLS = [('south bend community', 'south-bend-schools', 'South Bend Community Schools'),
           ('south bend schools', 'south-bend-schools', 'South Bend Community Schools'),
           ('penn-harris-madison', 'penn-harris-madison-schools', 'Penn-Harris-Madison schools'),
           ('mishawaka schools', 'mishawaka-schools', 'School City of Mishawaka'),
           ('mishawaka (school city)', 'mishawaka-schools', 'School City of Mishawaka'),
           ('school city of mishawaka', 'mishawaka-schools', 'School City of Mishawaka'),
           ('john glenn', 'john-glenn-schools', 'John Glenn schools'),
           ('new prairie', 'new-prairie-schools', 'New Prairie schools'),
           ('union-north', 'union-north-schools', 'Union-North United schools'),
           ('laville', 'laville-schools', 'LaVille schools')]


def jur_kind(j):
    jl = j.lower().strip()
    if jl in ('county', 'st. joseph county'):
        return ('county', 'county', 'St. Joseph County')
    if jl in ('indiana', 'state (as voted in county)', 'statewide (county tally)', 'state senate', 'state house'):
        return ('state', 'state', 'Indiana')
    if jl.startswith('retention ('):
        return ('state', 'state', 'Indiana (court not legible)')
    for k, s, n in SCHOOLS:
        if jl.startswith(k):
            return ('school', s, n)
    if jl.startswith('south bend') or jl == 'city of south bend':
        return ('city', 'south-bend', 'South Bend')
    if jl.startswith('mishawaka') or jl == 'city of mishawaka':
        return ('city', 'mishawaka', 'Mishawaka')
    t = re.sub(r'^town of ', '', jl)
    t = re.sub(r' \(town\)$| \(\?\)$', '', t)
    if t in TOWNS:
        return ('town', slug(TOWNS[t]), 'Town of ' + TOWNS[t])
    m = re.match(r'^(\w+) (township|twp)$', jl)
    if m:
        n = m.group(1).capitalize()
        return ('township', slug(n) + '-township', n + ' Township')
    raise ValueError('jurisdiction ' + j)


def norm_district(d):
    d = d.strip()
    if not d:
        return ''
    d = re.sub(r'^District\s+', '', d, flags=re.I)
    if d.lower() == 'at-large':
        return 'At-Large'
    return d


def build_office(kind, off, dist):
    """returns (office_slug, title, district, vote_for_hint, party_ballot_hint)"""
    o = off.strip()
    pp = ''
    m = re.search(r'\s*\(primary,\s*([^)]*)\)', o)
    if m:
        pp = m.group(1).strip()
        o = (o[:m.start()] + o[m.end():]).strip()
    vf = None
    m = re.search(r'\s*\((?:nominate\s+)?(\d)\)$', o)
    if m:
        vf = int(m.group(1))
        o = o[:m.start()].strip()
    m = re.search(r'\s*\(at-large, (\d) seats\)$', o)
    if m:
        vf = int(m.group(1))
        o = o[:m.start()].strip() + ' (at-large)'
    ol = o.lower()
    d = norm_district(dist)
    m = re.match(r'^(town council|city council|common council|council) (ward \d+)$', ol)
    if m and not d:
        ol = m.group(1)
        d = m.group(2).title()
    m = re.match(r'^(town council|city council|common council|council) at-large$', ol)
    if m and not d:
        ol = m.group(1)
        d = 'At-Large'

    if kind == 'county':
        simple = {'assessor': 'assessor', 'auditor': 'auditor', 'coroner': 'coroner', 'recorder': 'recorder',
                  'sheriff': 'sheriff', 'surveyor': 'surveyor', 'treasurer': 'treasurer'}
        if ol in simple:
            return simple[ol], o, d, 1, pp
        if ol in ('circuit court clerk', 'clerk of the circuit court'):
            return 'clerk', 'Clerk of the Circuit Court', d, 1, pp
        if ol.startswith('prosecuting attorney'):
            return 'prosecutor', 'Prosecuting Attorney', d, 1, pp
        if ol == 'commissioner':
            return 'commissioner', 'County Commissioner', d, 1, pp
        if ol in ('council', 'county council'):
            return 'council', 'County Council', d, 1, pp
        if ol in ('judge of the circuit court', 'circuit court judge'):
            return 'circuit-judge', 'Judge of the Circuit Court', d, 1, pp
        if ol in ('judge of probate court', 'judge of the probate court'):
            return 'probate-judge', 'Judge of the Probate Court', d, 1, pp
        if ol in ('straight party', 'straight ticket', 'straight ticket selection'):
            return 'straight-party', 'Straight-party ballots', d, None, pp
        if ol.startswith('judicial retention (st. joseph county)'):
            return ('superior-court-retention',
                    'Superior Court retention (St. Joseph County; judge names not captured)', d, None, pp)
        m = re.match(r'^(?:judicial retention|retention: superior court|superior court) - (.+?)(?: \(st\. joseph superior court\))?$', ol)
        if m:
            nm = re.sub(r'\bjudge\b', '', m.group(1)).strip()
            nm_t = re.sub(r'^(.*)$', lambda x: x.group(1).title(), nm)
            return 'superior-court-retention-' + slug(nm), 'Superior Court retention: ' + nm_t, d, None, pp
        m = re.match(r'^public question #(\d)', ol)
        if m:
            return ('public-question-' + m.group(1),
                    'Public Question #%s (wording not captured)' % m.group(1), d, None, pp)
    if kind == 'state':
        if ol == 'state senator':
            return 'senate', 'State Senator', d, 1, pp
        if ol == 'state representative':
            return 'house', 'State Representative', d, 1, pp
        if ol.startswith('governor'):
            return 'governor', 'Governor' + (' and Lt. Governor' if 'lt.' in ol else ''), d, 1, pp
        simple = {'attorney general': 'attorney-general', 'secretary of state': 'secretary-of-state',
                  'auditor of state': 'auditor-of-state', 'treasurer of state': 'treasurer-of-state',
                  'superintendent of public instruction': 'superintendent'}
        if ol in simple:
            return simple[ol], o, d, 1, pp
        if ol.startswith('state comptroller'):
            return 'auditor-of-state', 'State Comptroller (Auditor of State)', d, 1, pp
        if ol.startswith('constitutional amendment'):
            return 'constitutional-amendment', 'Constitutional amendment', d, None, pp
        if ol.startswith('state question'):
            return 'state-question', 'State question', d, None, pp
        if ol.startswith('public question'):
            return 'public-question', 'Public question (wording not on summary page)', d, None, pp
        if ol.startswith('judicial retention'):
            nm = o.split('-', 1)[1].strip()
            return 'retention-' + slug(nm), 'Retention: ' + nm + ' (court heading not legible)', d, None, pp
        if ol.startswith('retention'):
            t = re.sub(r'^retention\s*[:\-]\s*', '', o, flags=re.I).strip()
            return 'retention-' + slug(t), 'Retention: ' + t, d, None, pp
        if ol.startswith('court of appeals') or ol.startswith('supreme court'):
            return 'retention-' + slug(o), 'Retention: ' + o, d, None, pp
    if kind == 'city':
        if ol == 'mayor':
            return 'mayor', 'Mayor', d, 1, pp
        if ol in ('city clerk', 'clerk'):
            return 'clerk', 'City Clerk', d, 1, pp
        if ol in ('city council', 'common council', 'council'):
            return 'council', 'Common Council', d or 'At-Large', None, pp
        if ol.startswith('straight'):
            return 'straight-party', 'Straight-party ballots', d, None, pp
        if 'levy' in ol:
            return 'public-question-fund-levy', o.replace('"', "'"), d, None, pp
        if 'public question' in ol:
            return 'public-question', o.replace('"', "'"), d, None, pp
    if kind == 'town':
        if ol == 'clerk-treasurer':
            return 'clerk-treasurer', 'Clerk-Treasurer', d, 1, pp
        if ol == 'town judge':
            return 'judge', 'Town Judge', d, 1, pp
        if ol == 'town council':
            return 'council', 'Town Council', d, None, pp
        if ol.startswith('town office'):
            return 'unknown-office', 'Town office (header not read)', d, None, pp
    if kind == 'township':
        if ol in ('trustee', 'township trustee'):
            return 'trustee', 'Township Trustee', d, 1, pp
        if ol in ('board', 'township board'):
            return 'board', 'Township Board', d, 3, pp
        if ol in ('assessor', 'township assessor'):
            return 'assessor', 'Township Assessor', d, 1, pp
    if kind == 'school':
        if 'question' in ol or 'referendum' in ol:
            nm = re.sub(r'\s*\([^)]*\)', '', o).strip()
            return 'question-' + slug(nm), nm, d, None, pp
        if ol.startswith('board') or ol == 'school board':
            if vf is None and 'at-large' in ol and ', 3' in off.lower():
                vf = 3
            if not d and 'at-large' in ol:
                d = 'At-Large'
            return 'board', 'School Board', d, vf, pp
    raise ValueError('office %r kind=%s' % (off, kind))
