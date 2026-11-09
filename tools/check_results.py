"""Validate the results data files. Run: python -P -E check_results.py"""
import csv, re, sys
from collections import defaultdict, Counter

D = 'C:/Users/nickb/local-gov-guide/data/editions/st-joseph/'
STATUS = {'official', 'unofficial', 'computed', 'from_scan', 'secondary', 'single_source'}
CONF = {'high', 'medium', 'low'}
PARTIES = {'D', 'R', 'L', 'I', 'G', 'NP', 'W', 'O', ''}
RCOLS = ['election_id', 'contest_id', 'office_id', 'contest_label', 'district', 'party_primary', 'candidate', 'party',
         'votes', 'pct', 'winner', 'vote_for', 'status', 'confidence', 'source_ids', 'notes']
ECOLS = ['election_id', 'date', 'type', 'scope', 'registered', 'ballots_cast', 'turnout_pct', 'straight_party_d',
         'straight_party_r', 'straight_party_other', 'status', 'source_doc', 'source_ids', 'notes']
SCOLS = ['id', 'url', 'title', 'publisher', 'accessed', 'kind', 'notes']
ETYPES = {'primary', 'general', 'special', 'municipal_primary', 'municipal_general'}
errs, warns = [], []


def err(m):
    errs.append(m)


def warn(m):
    warns.append(m)


def read(fn, cols):
    with open(D + fn, newline='', encoding='utf-8') as f:
        rd = csv.reader(f)
        hdr = next(rd)
        if hdr != cols:
            err('%s header mismatch: %s' % (fn, hdr))
        rows = []
        for i, r in enumerate(rd, 2):
            if len(r) != len(cols):
                err('%s line %d: %d fields (expected %d)' % (fn, i, len(r), len(cols)))
                continue
            rows.append(dict(zip(cols, r)))
    return rows


src = read('sources_results.csv', SCOLS)
src_ids = {s['id'] for s in src}
if len(src_ids) != len(src):
    err('duplicate source ids')
for s in src:
    if not re.fullmatch(r'RES-\d{3}', s['id']):
        err('bad source id ' + s['id'])
    if not s['url'] or s['kind'] not in ('primary', 'news', 'secondary', 'statute', 'dataset', 'derived'):
        err('bad source row ' + s['id'])

els = read('elections.csv', ECOLS)
eids = {e['election_id'] for e in els}
if len(eids) != len(els):
    err('duplicate election ids')
for e in els:
    if e['status'] not in STATUS:
        err('election %s status %r' % (e['election_id'], e['status']))
    if e['type'] not in ETYPES:
        err('election %s type %r' % (e['election_id'], e['type']))
    if not re.fullmatch(r'\d{4}(-\d{2}-\d{2})?', e['date']):
        err('election %s date %r' % (e['election_id'], e['date']))
    if not e['source_ids']:
        err('election %s no source_ids' % e['election_id'])
    for s in e['source_ids'].split(';'):
        if s not in src_ids:
            err('election %s unknown source %s' % (e['election_id'], s))
    if e['registered'] and e['ballots_cast'] and e['turnout_pct']:
        calc = int(e['ballots_cast']) * 100.0 / int(e['registered'])
        if abs(calc - float(e['turnout_pct'])) > 0.02:
            warn('election %s turnout printed %s vs computed %.2f' % (e['election_id'], e['turnout_pct'], calc))
    if e['election_id'] == '2026g' and e['status'] != 'unofficial':
        err('2026g must be unofficial')
    if e['election_id'] == '2020p' and e['date'] != '2020-06-02':
        err('2020p date')
    if e['status'] in ('unofficial',) and not re.search(r'(?i)unofficial|as of|run date|election night|election-night', e['notes']):
        err('election %s unofficial without as-of note' % e['election_id'])

res = read('results.csv', RCOLS)
by = defaultdict(list)
seen = set()
for i, r in enumerate(res, 2):
    cid = r['contest_id']
    by[cid].append(r)
    if r['election_id'] not in eids:
        err('results line %d: election %s not in elections' % (i, r['election_id']))
    if not cid.startswith(r['election_id'] + '-'):
        err('results line %d: contest_id %s does not start with election id' % (i, cid))
    if r['status'] not in STATUS:
        err('results line %d: status %r' % (i, r['status']))
    if r['confidence'] not in CONF:
        err('results line %d: confidence %r' % (i, r['confidence']))
    if not r['source_ids']:
        err('results line %d: no source_ids' % i)
    for s in r['source_ids'].split(';'):
        if s not in src_ids:
            err('results line %d: unknown source %s' % (i, s))
    if r['party'] not in PARTIES:
        err('results line %d: party %r' % (i, r['party']))
    if r['party_primary'] not in ('', 'D', 'R'):
        err('results line %d: party_primary %r' % (i, r['party_primary']))
    if r['votes'] and not re.fullmatch(r'\d+', r['votes']):
        err('results line %d: votes %r' % (i, r['votes']))
    if r['pct'] and not re.fullmatch(r'\d{1,3}(\.\d{1,2})?', r['pct']):
        err('results line %d: pct %r' % (i, r['pct']))
    if r['pct'] and float(r['pct']) > 100.0:
        err('results line %d: pct > 100' % i)
    if r['winner'] not in ('', 'Y', 'N'):
        err('results line %d: winner %r' % (i, r['winner']))
    if not r['candidate']:
        err('results line %d: empty candidate' % i)
    if r['vote_for'] and not re.fullmatch(r'\d+', r['vote_for']):
        err('results line %d: vote_for %r' % (i, r['vote_for']))
    if r['election_id'] == '2026g' and r['status'] not in ('unofficial', 'from_scan'):
        err('results line %d: 2026g row status %s' % (i, r['status']))
    if r['election_id'] == '2026g' and r['status'] == 'unofficial' and 'Unofficial as of 2026-11-03' not in r['notes']:
        err('results line %d: 2026g row missing as-of note' % i)
    if r['status'] == 'from_scan' and r['confidence'] == 'high':
        err('results line %d: from_scan with high confidence' % i)
    key = (cid, r['candidate'], r['party'])
    if key in seen:
        err('results line %d: duplicate %s' % (i, key))
    seen.add(key)
    if re.search(r'(?i)\b(flip|sweep|landslide|seized|won back|wave|safe|target|vulnerable)\b', r['notes'] + r['contest_label']):
        err('results line %d: non-neutral wording' % i)

pct_checked = 0
for cid, rs in by.items():
    labels = {r['contest_label'] for r in rs}
    if len(labels) > 1:
        err('contest %s has several labels %s' % (cid, labels))
    if all(r['pct'] for r in rs) and not all(r['pct'] in ('100.00', '100') for r in rs) and not any(re.search(r'not captured|not listed|not read|not clear|appears to be missing', r['notes']) for r in rs):
        s = sum(float(r['pct']) for r in rs)
        pct_checked += 1
        if abs(s - 100) > 0.6 + 0.05 * len(rs):
            warn('contest %s pct sum %.2f (n=%d)' % (cid, s, len(rs)))
    wins = sum(1 for r in rs if r['winner'] == 'Y')
    vf = {r['vote_for'] for r in rs if r['vote_for']}
    if len(vf) > 1:
        err('contest %s inconsistent vote_for %s' % (cid, vf))
    if vf and wins > int(list(vf)[0]):
        warn('contest %s has %d winners but vote_for %s' % (cid, wins, vf))

print('elections:', len(els), 'results:', len(res), 'contests:', len(by), 'sources:', len(src),
      'pct-sum contests checked:', pct_checked)
print('status counts:', dict(Counter(r['status'] for r in res)))
print('ERRORS:', len(errs))
for e in errs[:80]:
    print('  ERR', e)
print('WARNINGS:', len(warns))
for w in warns[:120]:
    print('  WARN', w)
sys.exit(1 if errs else 0)
