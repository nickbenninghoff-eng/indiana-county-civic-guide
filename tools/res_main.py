"""Write the results data files. Run: python res_main.py"""
import csv, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import OrderedDict, defaultdict
import res_build as B
import res_contests as C
from res_bp import parse_bp

OUT = B.OUT
os.makedirs(OUT, exist_ok=True)


def fpct(v, whole=False):
    if v is None:
        return ''
    if whole:
        return str(int(round(v)))
    return '%.2f' % v


def main():
    rows, contests, skipped, bp, can, whole = C.build_contests()
    final = []
    gaps = []

    # ---- compute pct where missing
    by_cid = defaultdict(list)
    for r in rows:
        by_cid[r['contest_id']].append(r)
    for cid, rs in by_cid.items():
        tot = sum(r['votes'] for r in rs if r['votes'] is not None)
        for r in rs:
            if r['pct'] is None and r['votes'] is not None and tot > 0:
                r['pct'] = round(r['votes'] * 100.0 / tot, 2)
                r['notes'].append('pct computed from votes (not printed)')

    for r in rows:
        eid = r['election_id']
        srcs = [B.EL[eid]['doc']] + B.EL[eid]['extra']
        # extra (cross-check) doc is only listed on the election row; rows cite the transcribed doc
        sid_row = B.sid(B.EL[eid]['doc'])
        if r['status'] == 'from_scan' or True:
            pass
        final.append(OrderedDict(
            election_id=eid, contest_id=r['contest_id'], office_id='', contest_label=r['contest_label'],
            district=r['district'], party_primary=r['party_primary'], candidate=r['candidate'], party=r['party'],
            votes='' if r['votes'] is None else r['votes'], pct=fpct(r['pct']), winner=r['winner'],
            vote_for=r['vote_for'], status=r['status'], confidence=r['confidence'], source_ids=sid_row,
            notes='; '.join(dict.fromkeys(n.strip().rstrip('.;') for n in r['notes'] if n and n.strip()))))

    # ---- Ballotpedia district totals for state-legislative contests absent from the county canvass
    for (yr, ch, dist), cands in sorted(bp.items(), key=lambda x: (x[0][1], int(x[0][2]), x[0][0])):
        if (yr, ch, dist) in can or yr < 2012:
            continue
        have = [c for c in cands if c['votes'] is not None]
        if not have:
            gaps.append(('Election results: state legislature', 'Ballotpedia %s District %s %d' % (ch, dist, yr),
                         'Ballotpedia page shows no vote count (uncontested or not captured) and the race is not on the county canvass.',
                         'Check the county canvass / Indiana Election Division results.'))
            continue
        eid = '%dg' % yr
        total = sum(c['votes'] for c in have)
        cid = '%s-state-%s-%s' % (eid, ch, dist)
        for c in have:
            pct = c['pct'] if c['pct'] is not None else round(c['votes'] * 100.0 / total, 2)
            notes = ['Ballotpedia district-wide total; district may include other counties, so this is not the St. Joseph County tally',
                     'race not on the county canvass transcription (research/results-2015-2019.md notes the Dvorak line was not captured)' if (yr, ch, dist) == (2018, 'house', '8') else 'race not on the county canvass transcription']
            if c['pct'] is None:
                notes.append('pct computed from votes (not printed)')
            if c['unopposed']:
                notes.append('unopposed')
            final.append(OrderedDict(
                election_id=eid, contest_id=cid, office_id='',
                contest_label='State %s, District %s (district-wide, Ballotpedia)' % ('Representative' if ch == 'house' else 'Senator', dist),
                district=dist, party_primary='', candidate=c['name'], party=c['party'], votes=c['votes'], pct=fpct(pct),
                winner='Y' if c is max(have, key=lambda x: x['votes']) else 'N', vote_for=1, status='secondary', confidence='medium',
                source_ids=B.sid('bp-%s%s' % ('hd' if ch == 'house' else 'sd', dist)),
                notes='; '.join(notes)))

    # ---- pre-2010 South Bend mayor
    for yr, cands, note in B.PRE:
        eid = '%dg' % yr
        cid = '%s-south-bend-mayor' % eid
        w = max(range(len(cands)), key=lambda i: (cands[i][2] or 0))
        if all(c[2] is None for c in cands):
            w = 0 if yr in (1963, 1971, 1979) else w
        # winners recorded in the source table: 1963 Allen, 1971 Miller, 1979 Parent
        for i, (nm, pty, v, p) in enumerate(cands):
            whole = (yr in (1967, 1987))
            notes = [note] if i == 0 else []
            if v is None:
                notes.append('vote count not found in the source')
            if yr == 1967:
                notes.append('other candidates not listed (6% combined)')
            final.append(OrderedDict(
                election_id=eid, contest_id=cid, office_id='', contest_label='South Bend: Mayor', district='', party_primary='',
                candidate=nm, party=pty, votes='' if v is None else v, pct=fpct(p, whole and p is not None and p == int(p)),
                winner='Y' if i == w else 'N', vote_for=1, status='secondary', confidence='medium',
                source_ids=B.sid('wp-sb'), notes='; '.join(n.rstrip('.') for n in notes if n)))
    for yr, pty, cands, note in B.PRE_PRIM:
        eid = '%dp' % yr
        cid = '%s-south-bend-mayor-%s' % (eid, pty.lower())
        for i, (nm, v, p) in enumerate(cands):
            final.append(OrderedDict(
                election_id=eid, contest_id=cid, office_id='',
                contest_label='South Bend: Mayor (%s primary)' % ('Democratic' if pty == 'D' else 'Republican'),
                district='', party_primary=pty, candidate=nm, party=pty, votes=v, pct=fpct(p),
                winner='Y' if i == 0 else 'N', vote_for=1, status='secondary', confidence='medium',
                source_ids=B.sid('wp-sb'), notes=note if i == 0 else ''))

    # ---- write results.csv
    cols = ['election_id', 'contest_id', 'office_id', 'contest_label', 'district', 'party_primary', 'candidate', 'party',
            'votes', 'pct', 'winner', 'vote_for', 'status', 'confidence', 'source_ids', 'notes']
    final.sort(key=lambda r: (r['election_id'][:4], 'psg'.index(r['election_id'][4])))  # stable: keep order within election
    with open(OUT + 'results.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator='\n')
        w.writeheader()
        for r in final:
            w.writerow(r)

    # ---- elections.csv
    sp = defaultdict(lambda: [None, None, 0])
    for r in final:
        if r['contest_id'].endswith('county-straight-party') and r['contest_id'].split('-')[0] != '2011g':
            e = r['election_id']
            v = r['votes']
            if r['party'] == 'D':
                sp[e][0] = v
            elif r['party'] == 'R':
                sp[e][1] = v
            else:
                sp[e][2] += v
    ecols = ['election_id', 'date', 'type', 'scope', 'registered', 'ballots_cast', 'turnout_pct', 'straight_party_d',
             'straight_party_r', 'straight_party_other', 'status', 'source_doc', 'source_ids', 'notes']
    order = sorted(B.EL.values(), key=lambda e: (e['election_id'][:4], 'psg'.index(e['election_id'][4])))
    with open(OUT + 'elections.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=ecols, lineterminator='\n')
        w.writeheader()
        for e in order:
            eid = e['election_id']
            s = sp.get(eid)
            doc = B.SRC[e['doc']]
            srcrow = [x for x in B.SOURCES if x[0] == e['doc']][0]
            row = OrderedDict(election_id=eid, date=e['date'], type=e['type'], scope=e['scope'],
                              registered=e['registered'], ballots_cast=e['ballots_cast'],
                              turnout_pct=('%.2f' % e['turnout_pct']) if e['turnout_pct'] != '' else '',
                              straight_party_d='' if not s or s[0] is None else s[0],
                              straight_party_r='' if not s or s[1] is None else s[1],
                              straight_party_other='' if (not s or s[2] == 0) else s[2],
                              status=e['status'], source_doc=srcrow[1],
                              source_ids=';'.join([doc] + [B.SRC[x] for x in e['extra']]), notes=e['notes'])
            w.writerow(row)

    # ---- sources
    with open(OUT + 'sources_results.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['id', 'url', 'title', 'publisher', 'accessed', 'kind', 'notes'])
        for key, url, title, pub, kind, notes in B.SOURCES:
            acc = '2026-11-07'
            w.writerow([B.SRC[key], url, title, pub, acc, kind, notes])

    # ---- gaps
    for fn, line, why in skipped:
        if 'precinct committee' in why or why.startswith('placeholder'):
            continue
        gaps.append(('Election results', 'research/%s line %d' % (fn, line),
                     'Row not encoded: ' + why + '. Candidate line was not captured in the OCR transcription.',
                     'Re-read the scanned county PDF page.'))
    from res_gaps import STATIC_GAPS
    gaps += STATIC_GAPS
    with open(OUT + 'gaps_results.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['area', 'item', 'why_missing', 'how_to_fill'])
        for g in gaps:
            w.writerow(g)
    return final, gaps


if __name__ == '__main__':
    final, gaps = main()
    print(len(final), 'result rows;', len(gaps), 'gaps (partial)')
