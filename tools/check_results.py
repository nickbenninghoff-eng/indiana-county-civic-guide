"""Validate the results data files. Run: python -P -E tools/check_results.py

The data folder is found relative to this file (data/editions/st-joseph/ beside tools/), so a copy of the checker in
<root>/tools/ checks <root>/data/ (the gap-fill merge and the unit tests rely on this).

2026 general (2026g), gap-fill round 2 (2026-11-18): every row carries the official county canvass of 11/13/2026
(OFFICIAL_CANVASS_2026). A 2026g result row, or the 2026g election row, may be official only if it cites that source;
an unofficial 2026g row must name the canvass and say why it is still unofficial. ballot_questions.csv (new) is
checked for keys, foreign keys, vocabulary, sources and neutral wording. Source ids may come from any edition
sources_*.csv or data/indiana/sources*.csv file (the site merges them by id), not only sources_results.csv.

overall_results.csv (second merge of 2026-11-18, planning/gapfill/overall/merge2/merge2.py): the overall
(district-wide, statewide or whole-corporation) result of a multi-county contest, shown beside the county portion in
results.csv. Checked: contest_id exists in results.csv; (contest_id, candidate) unique; whole-number votes and totals;
pct recomputes from overall_total_votes within rounding; `derived` lists only computed fields that are filled; vote_for
equals results.csv; exactly vote_for winners (fewer only when there are fewer rows than seats or the notes say "fewer
winners than seats"), and every winner has at least the votes of every non-winner; one total per contest, at least the
sum of its rows; sources resolve; no 2026g row may be official; overall_votes >= the county votes in results.csv for
the same candidate unless the notes say "county figure exceeds the overall"; neutral wording and never "certified".
"""
import csv, glob, os, re, sys
from collections import defaultdict, Counter
from decimal import Decimal

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'editions', 'st-joseph') + os.sep
IND = os.path.join(os.path.dirname(os.path.dirname(D.rstrip(os.sep))), 'indiana')
OFFICIAL_CANVASS_2026 = 'RES-048'
# why a 2026g row is still unofficial: one of these must appear in its notes
UNOFFICIAL_2026_REASON = re.compile(r'awaits state certification|recount|another county|court is confirmed')
BANNED = re.compile(r'(?i)\b(flip|sweep|landslide|seized|won back|wave|safe|target|vulnerable)\b')
QKINDS = {'official_record', 'dlgf_approved', 'sample_ballot', 'reconstructed'}
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
    if not os.path.exists(D + fn):
        err('%s: file missing' % fn)
        return []
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
# every id registered in any sources file (edition + Indiana-wide); results may cite these, as the site does
all_src_ids = set(src_ids)
for _p in sorted(glob.glob(D + 'sources_*.csv')) + sorted(glob.glob(os.path.join(IND, 'sources*.csv'))):
    with open(_p, newline='', encoding='utf-8-sig') as _f:
        all_src_ids |= {r['id'].strip() for r in csv.DictReader(_f) if r.get('id')}
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
        if s not in all_src_ids:
            err('election %s unknown source %s' % (e['election_id'], s))
    if e['registered'] and e['ballots_cast'] and e['turnout_pct']:
        calc = int(e['ballots_cast']) * 100.0 / int(e['registered'])
        if abs(calc - float(e['turnout_pct'])) > 0.02:
            warn('election %s turnout printed %s vs computed %.2f' % (e['election_id'], e['turnout_pct'], calc))
    if e['election_id'] == '2026g' and e['status'] not in ('official', 'unofficial'):
        err('2026g election status %r' % e['status'])
    if e['election_id'] == '2026g' and e['status'] == 'official' and \
            OFFICIAL_CANVASS_2026 not in e['source_ids'].split(';'):
        err('2026g is official but does not cite the official county canvass (%s)' % OFFICIAL_CANVASS_2026)
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
        if s not in all_src_ids:
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
    if r['election_id'] == '2026g' and r['status'] not in ('official', 'unofficial', 'from_scan'):
        err('results line %d: 2026g row status %s' % (i, r['status']))
    if r['election_id'] == '2026g' and r['status'] == 'official' and \
            OFFICIAL_CANVASS_2026 not in r['source_ids'].split(';'):
        err('results line %d: 2026g official row does not cite the official county canvass (%s)' %
            (i, OFFICIAL_CANVASS_2026))
    if r['election_id'] == '2026g' and r['status'] == 'unofficial':
        if not re.search(r'(?i)official county canvass of 11/13/2026', r['notes']):
            err('results line %d: 2026g unofficial row does not name the official county canvass' % i)
        if not UNOFFICIAL_2026_REASON.search(r['notes']):
            err('results line %d: 2026g unofficial row does not say why it is unofficial' % i)
    if r['status'] == 'from_scan' and r['confidence'] == 'high':
        err('results line %d: from_scan with high confidence' % i)
    key = (cid, r['candidate'], r['party'])
    if key in seen:
        err('results line %d: duplicate %s' % (i, key))
    seen.add(key)
    if BANNED.search(r['notes'] + r['contest_label']):
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

# ballot_questions.csv (new 2026-11-18): the wording of a public question, one row per results.csv YES/NO contest
BCOLS = ['contest_id', 'wording', 'wording_kind', 'status', 'source_ids', 'notes']
bq = read('ballot_questions.csv', BCOLS)
bq_seen = set()
for q in bq:
    c = q['contest_id']
    if c in bq_seen:
        err('ballot_questions %s: duplicate contest_id' % c)
    bq_seen.add(c)
    if c not in by:
        err('ballot_questions %s: unknown contest_id' % c)
    elif not all(r['candidate'] in ('YES', 'NO') for r in by[c]):
        err('ballot_questions %s: contest is not a YES/NO question' % c)
    if not q['wording'].strip():
        err('ballot_questions %s: blank wording' % c)
    if q['wording_kind'] not in QKINDS:
        err('ballot_questions %s: wording_kind %r' % (c, q['wording_kind']))
    if q['status'] not in STATUS:
        err('ballot_questions %s: status %r' % (c, q['status']))
    q_ids = [x for x in q['source_ids'].split(';') if x]
    if not q_ids:
        err('ballot_questions %s: no source_ids' % c)
    for s in q_ids:
        if s not in all_src_ids:
            err('ballot_questions %s: unknown source %s' % (c, s))
    if BANNED.search(q['wording'] + ' ' + q['notes']):
        err('ballot_questions %s: non-neutral wording' % c)

# overall_results.csv (new 2026-11-18, merge2): overall result of a multi-county contest beside the county portion
OVCOLS = ['contest_id', 'candidate', 'candidate_in_source', 'party', 'overall_votes', 'overall_pct', 'overall_winner',
          'overall_total_votes', 'derived', 'electorate', 'vote_for', 'status', 'confidence', 'source_ids', 'notes']
OV_DERIVABLE = ('overall_pct', 'overall_winner', 'overall_total_votes')
OV_COUNTY_EXCEEDS = re.compile(r'(?i)county figure exceeds the overall')
OV_FEWER_WINNERS = re.compile(r'(?i)fewer winners than seats')
OV_CERTIFIED = re.compile(r'(?i)\bcertified\b')
ov = read('overall_results.csv', OVCOLS)
res_by_cand = defaultdict(list)
for r in res:
    res_by_cand[(r['contest_id'], r['candidate'])].append(r)
ov_by = defaultdict(list)
ov_seen = set()
for i, o in enumerate(ov, 2):
    c, cand = o['contest_id'], o['candidate']
    w = 'overall_results line %d (%s | %s)' % (i, c, cand)
    ov_by[c].append(o)
    if c not in by:
        err(w + ': contest_id not in results.csv')
    if not cand.strip():
        err(w + ': empty candidate')
    if (c, cand) in ov_seen:
        err(w + ': duplicate contest_id + candidate')
    ov_seen.add((c, cand))
    nums_ok = True
    for col in ('overall_votes', 'overall_total_votes'):
        if not re.fullmatch(r'\d+', o[col]):
            err(w + ': %s %r is not a whole number' % (col, o[col]))
            nums_ok = False
    if nums_ok and int(o['overall_votes']) > int(o['overall_total_votes']):
        err(w + ': overall_votes exceeds overall_total_votes')
    if o['overall_pct']:
        if not re.fullmatch(r'\d{1,3}(\.\d{1,2})?', o['overall_pct']):
            err(w + ': overall_pct %r' % o['overall_pct'])
        elif nums_ok and int(o['overall_total_votes']) > 0:
            calc = Decimal(int(o['overall_votes']) * 100) / Decimal(int(o['overall_total_votes']))
            if abs(Decimal(o['overall_pct']) - calc) > Decimal('0.005'):
                err(w + ': overall_pct %s does not recompute from overall_total_votes (%.4f)' % (o['overall_pct'], calc))
    if o['overall_winner'] not in ('', 'Y', 'N'):
        err(w + ': overall_winner %r' % o['overall_winner'])
    der = [x for x in o['derived'].split(';') if x]
    for x in der:
        if x not in OV_DERIVABLE:
            err(w + ': derived lists %r (allowed: %s)' % (x, ', '.join(OV_DERIVABLE)))
        elif not o[x]:
            err(w + ': derived lists %s but it is blank' % x)
    if len(der) != len(set(der)):
        err(w + ': derived repeats a field')
    if o['vote_for'] and not re.fullmatch(r'\d+', o['vote_for']):
        err(w + ': vote_for %r' % o['vote_for'])
    if c in by:
        rvf = {r['vote_for'] for r in by[c]}
        if len(rvf) == 1 and o['vote_for'] != list(rvf)[0]:
            err(w + ': vote_for %r differs from results.csv %r' % (o['vote_for'], list(rvf)[0]))
    if o['status'] not in STATUS:
        err(w + ': status %r' % o['status'])
    if o['confidence'] not in CONF:
        err(w + ': confidence %r' % o['confidence'])
    if o['party'] not in PARTIES:
        err(w + ': party %r' % o['party'])
    o_ids = [x for x in o['source_ids'].split(';') if x]
    if not o_ids:
        err(w + ': no source_ids')
    for s in o_ids:
        if s not in all_src_ids:
            err(w + ': unknown source %s' % s)
    if c.startswith('2026g') and o['status'] == 'official':
        err(w + ': no 2026g overall row may be official (the state has not reported the 2026 general)')
    text = o['notes'] + ' ' + o['electorate']
    if BANNED.search(text):
        err(w + ': non-neutral wording')
    if OV_CERTIFIED.search(text):
        err(w + ': says "certified" (the state figures are official results as reported, not a certification)')
    if re.fullmatch(r'\d+', o['overall_votes']):
        for r in res_by_cand.get((c, cand), []):
            if re.fullmatch(r'\d+', r['votes']) and int(o['overall_votes']) < int(r['votes']) and \
                    not OV_COUNTY_EXCEEDS.search(o['notes']):
                err(w + ': overall_votes %s < county votes %s in results.csv (no "county figure exceeds the overall" '
                        'note)' % (o['overall_votes'], r['votes']))
for c, os_ in ov_by.items():
    tots = {o['overall_total_votes'] for o in os_}
    if len(tots) > 1:
        err('overall_results %s: several overall_total_votes %s' % (c, sorted(tots)))
    elif all(re.fullmatch(r'\d+', o['overall_votes']) for o in os_) and re.fullmatch(r'\d+', list(tots)[0]) and \
            sum(int(o['overall_votes']) for o in os_) > int(list(tots)[0]):
        err('overall_results %s: rows sum to more than overall_total_votes' % c)
    vfs = {o['vote_for'] for o in os_}
    if len(vfs) > 1:
        err('overall_results %s: inconsistent vote_for %s' % (c, sorted(vfs)))
        continue
    vf = list(vfs)[0]
    is_q = all(o['candidate'].upper() in ('YES', 'NO') for o in os_)
    seats = int(vf) if vf else (1 if is_q else None)
    wins = [o for o in os_ if o['overall_winner'] == 'Y']
    if seats is None:
        warn('overall_results %s: no vote_for, winners not checked' % c)
    elif len(wins) > seats:
        err('overall_results %s: %d winners but %d seats' % (c, len(wins), seats))
    elif len(wins) < min(seats, len(os_)) and not any(OV_FEWER_WINNERS.search(o['notes']) for o in os_):
        err('overall_results %s: %d winners for %d seats (no "fewer winners than seats" note)' % (c, len(wins), seats))
    if all(re.fullmatch(r'\d+', o['overall_votes']) for o in os_):
        losers = [int(o['overall_votes']) for o in os_ if o['overall_winner'] != 'Y']
        if wins and losers and min(int(o['overall_votes']) for o in wins) < max(losers):
            err('overall_results %s: a winner has fewer votes than a non-winner' % c)

print('elections:', len(els), 'results:', len(res), 'contests:', len(by), 'sources:', len(src),
      'ballot questions:', len(bq), 'overall rows:', len(ov), 'overall contests:', len(ov_by),
      'pct-sum contests checked:', pct_checked)
print('status counts:', dict(Counter(r['status'] for r in res)))
print('ERRORS:', len(errs))
for e in errs[:80]:
    print('  ERR', e)
print('WARNINGS:', len(warns))
for w in warns[:120]:
    print('  WARN', w)
sys.exit(1 if errs else 0)
