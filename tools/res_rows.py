"""Turn the research markdown tables into normalised result records."""
import re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import OrderedDict, defaultdict
from res_raw import parse
from res_norm import *
import res_build as B

ASOF = {  # unofficial elections: as-of text used in row notes
    '2012p': 'Unofficial; report run 2012-05-21',
    '2012g': 'Unofficial label (page stamps mixed); report run 2012-11-16',
    '2014p': 'Unofficial; report run 2014-05-19',
    '2015p': 'Unofficial; report run 2015-05-15',
    '2015g': 'Unofficial (election-night run 2015-11-03)',
    '2024p': 'Unofficial as of 2024-05-07 20:01 (election-night header)',
    '2026g': 'Unofficial as of 2026-11-03 21:07 EST',
}
PRINTED_PCT = {'2010p', '2010g', '2011p', '2011g', '2012p', '2012g', '2013s', '2014p', '2014g', '2015p', '2015g',
               '2016p', '2016g', '2018p', '2018g', '2019p', '2019g'}  # percent printed on the report (2013s computed)
LOW_CONF = {  # (eid, candidate substring) -> note for values derived without a direct read
    ('2010g', 'Gregory Bock'): 'votes unreadable (faint print); derived from printed 55.17/44.83 split with a partial read of about 10,092',
    ('2010g', 'Michael Castellon'): 'votes unreadable (faint print); derived from printed 55.17/44.83 split',
    ('2010g', 'Jay Caponigro'): 'count unreadable; derived as remainder of the total implied by Hutchinson 818 at 13.66%',
    ('2014g', 'Democratic'): 'OCR garbled; derived from printed percentage and the Republican count',
    ('2014g', 'Libertarian'): 'OCR garbled; derived from printed percentage and the Republican count',
}
MID_NOTE = {
    ('2010g', 'Eric Knipe'): 'OCR-uncertain',
    ('2010g', 'Mike Kruk'): 'OCR read 4,857; printed 56.86% implies 4,457',
    ('2010g', 'Jeffrey M. Dean'): 'read as 10,056 in two passes and 10,100 in a third',
    ('2011g', 'Michelle L. Hektor'): 'OCR read 19; corrected to 79 from printed 24.84% (matches Karen Iovino 79 at 24.84%)',
    ('2012g', 'Craig Clark'): 'OCR-uncertain',
    ('2014g', 'Frank W. Creighton'): 'OCR read 502; printed 24.08% implies about 593',
    ('2014g', 'Jeffrey L. Sanford'): 'OCR partial 26,19x; derived from printed percentage (fact-check D: 26,201 checks out)',
    ('2014g', 'Elizabeth "Beth" White'): 'corrected from garbled OCR using printed percentage',
    ('2014g', 'Karl Tatgenhorst'): 'corrected from garbled OCR using printed percentage',
}
DERIVED_NOTE_2024 = {
    'Cichowicz': 'candidate votes (49,793 + 58,560 = 108,353) differ from OCR-read printed total 108,363 by 10; one digit probably misread',
    'Zappia': 'candidate votes (49,793 + 58,560 = 108,353) differ from OCR-read printed total 108,363 by 10; one digit probably misread',
    'Yacullo': 'candidate votes (1,177 + 877 = 2,054) differ from OCR-read printed total 1,854 by 200; Smith may be 977 or Yacullo 677',
    'Smith': None,
}


def clean_name(c):
    note = ''
    n = c.strip()
    m = re.search(r'\s*\(name OCR-uncertain\)', n)
    if m:
        n = n.replace(m.group(0), ''); note = 'candidate name OCR-uncertain'
    if '(?)' in n:
        n = n.replace('(?)', '').strip(); note = (note + '; ' if note else '') + 'candidate name uncertain in scan'
    n = re.sub(r'\s+', ' ', n).strip()
    return n, note


def party_of(raw):
    p = raw.replace('(?)', '').strip()
    note = PARTY_NOTE.get(p, '')
    return PARTY.get(p, 'O'), note, ('?' in raw)


def eid_of(h2):
    for k, v in SEC_EID.items():
        if h2.startswith(k):
            return v
    return None

SEC_EID = {  # h2 prefix -> eid
    '2010 Primary': '2010p', '2010 General': '2010g', '2011 Primary': '2011p', '2011 General': '2011g',
    '2012 Primary': '2012p', '2012 General': '2012g', '2013 Special': '2013s', '2014 Primary': '2014p',
    '2014 General': '2014g', '2015 MUNICIPAL PRIMARY': '2015p', '2015 MUNICIPAL GENERAL': '2015g',
    '2019 MUNICIPAL PRIMARY': '2019p', '2019 MUNICIPAL GENERAL': '2019g', '2016 PRIMARY': '2016p',
    '2016 GENERAL': '2016g', '2018 PRIMARY': '2018p', '2018 GENERAL': '2018g', '2020 Primary': '2020p',
    '2020 General': '2020g', '2022 Primary': '2022p', '2022 General': '2022g', '2023 Municipal Primary': '2023p',
    '2023 Municipal General': '2023g', '2024 Primary': '2024p', '2024 General': '2024g', '2026 Primary': '2026p',
    '2026 General': '2026g'}


def load_records():
    recs = []
    skipped = []
    for fn in ['results-2010-2014.md', 'results-2015-2019.md', 'results-2020-2026.md']:
        for r in parse(fn):
            h = r['hdr']
            if 'votes' not in h or r['h2'] is None:
                continue
            if r['h2'].startswith('2020 PRIMARY (document 60003)'):
                continue  # same election as 37457 (fact-check D)
            eid = eid_of(r['h2'])
            if eid is None:
                continue
            d = dict(zip(h, r['cells']))
            if len(r['cells']) != len(h):
                raise ValueError('cell count %s:%s' % (fn, r['line']))
            office_raw = d.get('office', d.get('measure', ''))
            cand_raw = d.get('candidate', d.get('choice', ''))
            if re.search(r'precinct committee|delegate', office_raw, re.I):
                skipped.append((fn, r['line'], 'precinct committee/delegate')); continue
            if office_raw == '' and d.get('district', '') == '':
                office_raw = ''  # John Glenn / New Prairie school rows with 2018 'district' col
            # 2018 school board tables have columns jurisdiction,district (no office)
            if 'office' not in h and 'measure' not in h and 'district' in h:
                office_raw = 'Board'
            pct_cell = d.get('percent', d.get('pct', ''))
            votes_cell = d['votes']
            if not votes_cell.strip() and not pct_cell.strip():
                skipped.append((fn, r['line'], 'no votes or pct: ' + cand_raw[:80])); continue
            if 'No Democrat filed' in cand_raw:
                skipped.append((fn, r['line'], 'placeholder: ' + cand_raw)); continue
            jur_raw = d['jurisdiction']
            kind, jslug, jname = jur_kind(jur_raw)
            # party ballot for primaries
            h3 = r['h3'] or ''
            pb = ''
            if eid.endswith('p'):
                if eid in ('2015p', '2016p', '2018p', '2019p'):
                    if h3.startswith('Republican'): pb = 'R'
                    elif h3.startswith('Democratic'): pb = 'D'
            o_slug, o_title, dist, vf_hint, pp = build_office(kind, office_raw, d.get('district', ''))
            if pp in ('R', 'D'): pb = pp
            party_raw = d.get('party', '')
            party, pnote, puncert = party_of(party_raw)
            if eid in ('2010p', '2011p', '2012p', '2014p'):
                # 2010-2014 primaries: party column is the ballot
                if party in ('R', 'D'): pb = party
                else: pb = pb
            # scope / state-leg handling
            if jur_raw in ('State Senate', 'State House'):
                kind = 'state'
            votes, vunc, vnote = num(votes_cell)
            pct, punc, pnote2 = num(pct_cell)
            if votes is None and pct is None:
                skipped.append((fn, r['line'], 'no readable votes or pct: ' + cand_raw[:80])); continue
            cand, cnote = clean_name(cand_raw)
            if cand_raw.startswith("(candidate line not OCR'd"):
                cand, cnote = '(name not captured)', 'candidate name not read in the scan; no Republican candidate; total 166'
            if cand.startswith('(opponent line not captured'):
                cand, cnote = '(name not captured)', 'candidate line not captured; ' + cand_raw.strip('()')
            if cand_raw.startswith('(REP name not read)'):
                cand, cnote = '(name not read)', 'Republican candidate name not read in the scan (60003)'
            if cand_raw.startswith('(first name unclear)'):
                cand, cnote = cand_raw.replace('(first name unclear)', '').strip(), 'first name unclear in scan'
            wraw = d.get('winner', None)
            recs.append(dict(eid=eid, fn=fn, line=r['line'], kind=kind, jslug=jslug, jname=jname, jur_raw=jur_raw,
                             o_slug=o_slug, o_title=o_title, dist=dist, vf_hint=vf_hint, pb=pb, cand=cand,
                             cnote=cnote, party=party, pnote=pnote, puncert=puncert, votes=votes, vunc=vunc, vnote=vnote,
                             pct=pct, punc=punc, pnote2=pnote2, wraw=wraw, h3=h3, office_raw=office_raw))
    return recs, skipped


if __name__ == '__main__':
    recs, sk = load_records()
    print(len(recs), 'records;', len(sk), 'skipped')
    for s in sk: print(s)
