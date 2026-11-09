"""Group records into contests, assign ids/labels, winners, status, confidence, notes."""
import re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import OrderedDict, defaultdict
from res_norm import *
import res_build as B
from res_rows import load_records, ASOF, LOW_CONF, MID_NOTE, DERIVED_NOTE_2024
from res_bp import parse_bp

PARTIAL_NOTE = 'county tally only (statewide result decided across all counties); winner left blank'
LEG_UNKNOWN_NOTE = 'county tally only (district-wide result not confirmed in the sources); winner left blank'
PCT_NOTE = 'pct computed from votes (not printed on the canvass)'


def parse_winner(w, eid):
    """returns (winner 'Y'/'N'/'', note, uncertain)"""
    if w is None:
        return None, '', False
    w0 = w.strip()
    unc = '?' in w0
    base = w0.replace('(?)', '').strip()
    note = ''
    if base.startswith('Y'):
        res = 'Y'
        if 'unopposed' in base:
            note = 'unopposed'
        if 'both nominated' in base:
            note = 'ballot is vote-for-up-to-2 in the primary; both nominated'
    elif base.startswith('N'):
        res = 'N'
    elif base == 'uncontested':
        res, note = 'Y', 'uncontested'
    elif base == 'passed':
        res = 'Y'
    elif base == 'county leader':
        res, note = '', 'leads within the St. Joseph County tally'
    else:
        res = ''
    return res, note, unc


def label_of(c):
    kind = c['kind']
    base = c['o_title']
    if c['eid'] == '2026g' and c['o_slug'].startswith('retention-justice-'):
        return 'Retention: %s (court not stated in the canvass)' % base.replace('Retention: Justice ', '')
    if kind in ('city', 'town', 'township', 'school'):
        base = '%s: %s' % (c['jname'], base)
    elif kind == 'county' and c['o_slug'] not in ('straight-party',) and not c['o_slug'].startswith(('superior', 'public')):
        if base.startswith('County '):
            base = 'St. Joseph County ' + base[len('County '):]
        else:
            base = 'St. Joseph County ' + base
    d = c['dist']
    if d:
        if re.fullmatch(r'\d+|[A-Z]', d):
            base += ', District ' + d
        else:
            base += ', ' + d
    if c['pb'] in ('R', 'D'):
        base += ' (%s primary)' % ('Republican' if c['pb'] == 'R' else 'Democratic')
    return base


def contest_id(c):
    scope = c['jslug'] if c['kind'] not in ('county', 'state') else c['kind']
    o_slug = c['o_slug']
    if c['eid'] == '2026g' and o_slug.startswith('retention-justice-'):
        o_slug = 'retention-' + o_slug[len('retention-justice-'):]
    parts = [c['eid'], scope, o_slug]
    if c['dist']:
        parts.append(slug(c['dist']))
    if c['pb'] in ('R', 'D'):
        parts.append(c['pb'].lower())
    return '-'.join(p for p in parts if p)


def vote_for_rule(c, flagged_y):
    """vote_for: explicit/statutory hint first; else the number of winners flagged in the source;
    else documented seat counts (city council, wards, numbered South Bend school districts)."""
    k, o, d = c['kind'], c['o_slug'], c['dist']
    if c['vf_hint'] is not None:
        return c['vf_hint'], 'hint'
    if flagged_y:
        return flagged_y, 'flagged'
    if k == 'city' and o == 'council':
        if d == 'At-Large':
            return 3, 'documented'
        return 1, 'documented'
    if k == 'town' and o == 'council' and re.match(r'^Ward \d+$', d):
        return 1, 'documented'
    if k == 'school' and o == 'board' and c['jslug'] == 'south-bend-schools' and re.fullmatch(r'\d+', d):
        return 1, 'documented'
    return None, ''


MISSING = {
    '2018g-clay-township-board': 'a further candidate (about 13.99% of votes) was not captured in the OCR transcription, so pct values sum to less than 100',
    '2018g-greene-township-board': 'a further candidate (about 22.5% of votes) was not captured in the OCR transcription, so pct values sum to less than 100',
    '2018g-penn-township-board': 'a further candidate (about 17.45% of votes; the research guesses Lacy Hahn, D) was not captured in the OCR transcription, so pct values sum to less than 100',
    '2018g-portage-township-board': 'a third candidate (about 34.16% of votes; the research guesses Cheryl Ashe, D) was not captured in the OCR transcription, so pct values sum to less than 100',
    '2015p-south-bend-council-at-large-d': 'printed percents sum to 90.68, so a candidate line (about 9.32%) appears to be missing from the transcription',
}


def build_contests():
    recs, skipped = load_records()
    bp = parse_bp()
    groups = OrderedDict()
    for r in recs:
        r['pb'] = r['pb']
        cid = contest_id(r)
        r['cid'] = cid
        groups.setdefault(cid, []).append(r)
    # canvass legislative totals for "wholly in county" test
    can = {}
    for r in recs:
        if r['kind'] == 'state' and r['o_slug'] in ('senate', 'house') and r['eid'].endswith('g'):
            can.setdefault((int(r['eid'][:4]), r['o_slug'], r['dist']), {})[r['cand'].lower().split()[-1]] = r['votes']
    whole = set()
    for k, v in can.items():
        b = bp.get(k)
        if not b:
            continue
        bv = {c['name'].lower().split()[-1]: c['votes'] for c in b if c['votes'] is not None}
        if bv and all(n in v and v[n] == vv for n, vv in bv.items()):
            whole.add(k)

    out = []          # result rows
    contests = OrderedDict()
    for cid, rs in groups.items():
        c0 = rs[0]
        eid = c0['eid']
        yr = int(eid[:4])
        # labels differing within group?
        leg = c0['kind'] == 'state' and c0['o_slug'] in ('senate', 'house')
        partial = c0['kind'] == 'state'
        wholly = False
        if leg and eid.endswith('g') and (yr, c0['o_slug'], c0['dist']) in whole:
            partial = False; wholly = True
        # source winner flags
        pw = [parse_winner(r['wraw'], eid) for r in rs]
        has_flags = any(p[0] in ('Y', 'N') for p in pw)
        n_y = sum(1 for p in pw if p[0] == 'Y')
        vf, vf_src = vote_for_rule(c0, n_y)
        if all(r['cand'].upper() in ('YES', 'NO') for r in rs):
            vf = None
        # derive winners if none flagged and seat count documented
        derived = {}
        incomplete = cid in MISSING or any(r['votes'] is None or re.search(r'not captured|not clear|name not', r['cnote'] + ' ' + r['pnote2'] + ' ' + r['vnote'] + ' ' + r['cand']) for r in rs)
        pcts = [r['pct'] for r in rs]
        pct_ok = all(p is not None for p in pcts) and abs(sum(pcts) - 100) <= 1.0 + 0.05 * len(rs)
        if not partial and not has_flags and vf and not incomplete and pct_ok:
            ranked = sorted([i for i, r in enumerate(rs) if r['votes'] is not None], key=lambda i: -rs[i]['votes'])
            for pos, i in enumerate(ranked):
                derived[i] = 'Y' if pos < vf else 'N'
        fallback = {}
        if not partial and not has_flags and not derived and not incomplete and pct_ok and c0['o_slug'] != 'straight-party':
            names = [r['cand'].upper() for r in rs]
            if all(n in ('YES', 'NO') for n in names) and len(rs) == 2 and all(r['votes'] is not None for r in rs):
                top = max(range(2), key=lambda i: rs[i]['votes'])
                for i in range(2):
                    fallback[i] = ('Y' if i == top else 'N', 'winner derived: leading side')
            elif len(rs) == 1 and c0['kind'] in ('city', 'town', 'township', 'school', 'county'):
                fallback[0] = ('Y', 'winner derived: only candidate listed')
        # pct sanity: contest cids with unknown/partial caps
        for i, r in enumerate(rs):
            winner, wnote, wunc = pw[i]
            if winner is None:
                winner = ''
            notes = []
            status = B.EL[eid]['status']
            conf = 'high'
            # votes / pct
            if r['vnote']:
                notes.append('votes: ' + r['vnote'])
            if r['pnote2']:
                notes.append('pct: ' + r['pnote2'])
            if r['cnote']:
                notes.append(r['cnote'])
            if r['pnote']:
                notes.append(r['pnote'])
            unc = r['vunc'] or r['punc'] or r['puncert'] or wunc or ('name' in r['cnote'] and 'uncertain' in r['cnote'])
            if unc:
                status = 'from_scan'
                conf = 'medium'
                if r['vunc']:
                    notes.append('votes OCR-uncertain in the scan')
                if wunc:
                    notes.append('winner flag uncertain in the scan')
                if r['punc']:
                    notes.append('pct OCR-uncertain in the scan')
            for (e, sub), t in LOW_CONF.items():
                if e == eid and sub in r['cand']:
                    status, conf = 'from_scan', 'low'; notes.append(t)
            for (e, sub), t in MID_NOTE.items():
                if e == eid and sub in r['cand'] and t not in notes:
                    notes.append(t)
            if r['votes'] is None:
                status, conf = 'from_scan', 'low'
                notes.append('vote count not captured; pct only' if r['pct'] is not None else 'vote count not captured')
            if r['cand'] == '(name not captured)' or r['cand'] == '(name not read)':
                status, conf = 'from_scan', 'low'
            if eid == '2024g':
                for sub, t in DERIVED_NOTE_2024.items():
                    if t and sub in r['cand'] and r['jslug'] in ('new-prairie-schools',) and sub == 'Yacullo':
                        notes.append(t); status, conf = 'from_scan', 'low'
                    elif t and sub in r['cand'] and sub in ('Cichowicz', 'Zappia'):
                        notes.append(t); status, conf = 'from_scan', 'medium'
                if r['jslug'] == 'new-prairie-schools' and r['cand'].endswith('Smith') and cid.endswith('board-at-large'):
                    notes.append(DERIVED_NOTE_2024['Yacullo']); status, conf = 'from_scan', 'low'
            if eid == '2022g' and ((r['jslug'] == 'john-glenn-schools' and 'Liberty' in c0['dist'] and r['cand'].split()[-1] in ('Carson', 'Elia')) or
                                    (r['jslug'] == 'mishawaka-schools' and r['cand'].split()[-1] in ("O'Connell", 'Parks'))):
                notes.append('candidate votes do not sum to the printed race total (see research OCR-uncertain list); shown as printed')
                conf = 'medium'
            if eid == '2020p' and r['cand'].startswith('Jake Teshka'):
                notes.append('60003 (scan) reads 2,651; text layer of 37457 reads 2,650 (preferred)')
            if eid == '2011g' and r['cand'] == 'Wayne Curry':
                notes.append("ballot name per county canvass; Wikipedia lists 'Norris Curry Jr.' (fact-check D)")
            if eid == '2019g' and cid == '2019g-south-bend-mayor':
                notes.append('official canvass; Wikipedia gives 9,437 / 5,445 (fact-check D)')
            # winner logic
            w_final = winner
            if wunc and not winner.startswith(('Y', 'N')):
                w_final = ''
            if partial:
                if c0['jname'].startswith('Indiana (court'):
                    notes.append('court heading not legible, so the scope of this retention vote is unknown; winner left blank')
                else:
                    notes.append(LEG_UNKNOWN_NOTE if leg else PARTIAL_NOTE)
                if winner == 'Y':
                    notes.append('leads within the St. Joseph County tally')
                w_final = ''
            elif wholly and winner in ('Y', 'N'):
                notes.append('district lies wholly in the county (county totals equal Ballotpedia district totals)')
            else:
                if wnote and wnote not in notes:
                    notes.append(wnote)
            if i in derived and not partial:
                w_final = derived[i]
                why = ('township board = 3 seats' if c0['kind'] == 'township' and vf == 3 else
                       ('at-large council = 3 seats' if (c0['kind'] == 'city' and c0['o_slug'] == 'council' and c0['dist'] == 'At-Large') else
                        ('single-seat contest' if vf == 1 else 'seat count from the research')))
                notes.append('winner derived: top %d by votes (%s)' % (vf, why))
            if i in fallback:
                w_final = fallback[i][0]
                notes.append(fallback[i][1])
            if eid == '2013s':
                notes.append('pct computed from the TOTALS row (share of YES+NO); the sheet prints turnout only')
            if cid in MISSING:
                notes.append(MISSING[cid])
            if eid in ASOF:
                notes.append(ASOF[eid])
            if eid[:4] >= '2020' and eid not in B.EL.get('_x', {}) and eid[:4] in ('2020', '2022', '2023', '2024', '2026'):
                if r['fn'] == 'results-2020-2026.md':
                    notes.append(PCT_NOTE)
            if r['party'] and r['party'] != r['party']:
                pass
            if c0['o_slug'].startswith('retention-') and eid == '2026g':
                notes.append("canvass prints RETAIN JUSTICE but does not name the court; fact-check A says this judge does not sit on the Indiana Supreme Court")
            # normalise yes/no
            cand = r['cand']
            if c0['o_slug'].startswith(('retention', 'public-question', 'constitutional', 'state-question', 'superior-court-retention', 'question-')) or \
                    'public-question' in c0['o_slug'] or cand in ('Yes', 'No', 'YES', 'NO'):
                if cand.upper() in ('YES', 'NO'):
                    cand = cand.upper()
            row = dict(election_id=eid, contest_id=cid, office_id='', contest_label=None, district=c0['dist'],
                       party_primary=c0['pb'], candidate=cand, party=r['party'], votes=r['votes'], pct=r['pct'],
                       winner=w_final, vote_for=vf if vf else '', status=status, confidence=conf, notes=notes,
                       _src=B.EL[eid]['doc'], _eid=eid, _fn=r['fn'], _line=r['line'])
            out.append(row)
        contests[cid] = rs
    for row in out:
        c0 = contests[row['contest_id']][0]
        row['contest_label'] = label_of(c0)
        # normalise district text for output
    return out, contests, skipped, bp, can, whole


if __name__ == '__main__':
    out, contests, sk, bp, can, whole = build_contests()
    print(len(out), 'rows;', len(contests), 'contests')
    from collections import Counter
    if len(sys.argv) > 1:
        for cid, rs in contests.items():
            if cid.startswith(sys.argv[1]):
                print(cid, '|', label_of(rs[0]), '| n=', len(rs))
