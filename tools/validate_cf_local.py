"""Validate the local campaign-finance tables.  Run:  python -P -E tools/validate_cf_local.py

Checks
 1. every row of cf_local / cf_large_contributions / cf_coverage / sources_cf_local parses
    (exact headers, money as plain numbers, ISO dates, enumerated fields);
 2. the form identities are re-checked from the adjudicated line-level file
    (research/cf/cf_lines_final.csv) and must agree with transcription_status, and the
    cf_local figures must equal those lines;
 3. no two cf_local rows share committee + office + period;
 4. every DocumentCenter doc in the manifests is accounted for (merged into cf_local,
    a CFA-11 notice, or a listed gap) and every CFL source id resolves;
 5. no phone numbers, e-mail addresses or street addresses in the published files.
Exits 1 on any failure.
"""
import csv, glob, os, re, sys, collections
from decimal import Decimal as D

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ED = os.path.join(ROOT, 'data', 'editions', 'st-joseph')
CF = os.path.join(ROOT, 'research', 'cf')
GAPS = {'66024': 'county list of committees that did not file 2024 annual reports (count only)'}
errors = []


def err(msg):
    errors.append(msg)


def read(path, header):
    with open(path, encoding='utf-8', newline='') as f:
        rd = csv.reader(f)
        h = next(rd)
        if h != header:
            err(f'{os.path.basename(path)}: header mismatch {h}')
        rows = []
        for i, rec in enumerate(rd, 2):
            if len(rec) != len(header):
                err(f'{os.path.basename(path)} line {i}: {len(rec)} fields, expected {len(header)}')
                continue
            rows.append(dict(zip(header, rec)))
        return rows


MONEY = re.compile(r'-?\d+\.\d{2}')
DATE = re.compile(r'\d{4}(-\d{2}(-\d{2})?)?')


def money(v, where):
    if v == '':
        return None
    if not MONEY.fullmatch(v):
        err(f'{where}: bad money {v!r}')
        return None
    return D(v)


CF_HDR = ['filing_id', 'doc_ids', 'committee', 'candidate', 'office', 'office_normalized', 'unit_id', 'party',
          'report_type', 'period_from', 'period_to', 'amended', 'receipts_period', 'expenditures_period',
          'cash_start_period', 'cash_end_period', 'receipts_ytd', 'expenditures_ytd', 'cash_jan1', 'cash_end_ytd',
          'debts_owed_by', 'transcription_status', 'double_entry', 'status', 'source_ids', 'notes']
FIG = {'receipts_period': 'l15cA', 'expenditures_period': 'l17cA', 'cash_start_period': 'l13A',
       'cash_end_period': 'l18A', 'receipts_ytd': 'l15cB', 'expenditures_ytd': 'l17cB', 'cash_jan1': 'l14B',
       'cash_end_ytd': 'l18B', 'debts_owed_by': 'l19'}
NUM = ['l13A', 'l14B', 'l15aA', 'l15bA', 'l15cA', 'l16A', 'l17aA', 'l17bA', 'l17cA', 'l18A',
       'l15aB', 'l15bB', 'l15cB', 'l16B', 'l17aB', 'l17bB', 'l17cB', 'l18B', 'l19', 'l20']


def identity_failures(L):
    v = {k: (D(L[k]) if L[k] else None) for k in NUM}
    out = []
    for c in 'AB':
        s = 'l13A' if c == 'A' else 'l14B'
        for res, a, b, sg in (('l15c' + c, 'l15a' + c, 'l15b' + c, 1), ('l17c' + c, 'l17a' + c, 'l17b' + c, 1),
                              ('l16' + c, s, 'l15c' + c, 1), ('l18' + c, 'l16' + c, 'l17c' + c, -1)):
            if v[res] is None or (v[a] is None and v[b] is None):
                continue
            if v[res] != (v[a] or 0) + sg * (v[b] or 0):
                out.append(res)
    if v['l18A'] is not None and v['l18B'] is not None and v['l18A'] != v['l18B']:
        out.append('18A=18B')
    pf, pt = L['period_from'], L['period_to']
    if pf.endswith('-01-01') and pt[:4] == pf[:4]:
        for a, b in (('l13A', 'l14B'), ('l15cA', 'l15cB'), ('l17cA', 'l17cB')):
            if v[a] is not None and v[b] is not None and v[a] != v[b]:
                out.append(f'same-span {a}/{b}')
    return out


def main():
    # ---- manifests and sources
    manifest = {}
    for fn in glob.glob(os.path.join(ROOT, 'sources', 'cf', 'pdf', '*', 'manifest.csv')):
        with open(fn, encoding='utf-8', newline='') as f:
            # the browser export wrote JSON-style \" inside quoted fields (same reader as build_cf_local.py)
            for r in csv.DictReader(f, escapechar='\\', doublequote=False):
                manifest[r['id']] = r
    src = read(os.path.join(ED, 'sources_cf_local.csv'), ['id', 'url', 'title', 'publisher', 'accessed', 'kind', 'notes'])
    src_ids = {s['id'] for s in src}
    for s in src:
        d = s['id'][4:]
        if not s['id'].startswith('CFL-') or d not in manifest:
            err(f'source {s["id"]} not a manifest doc')
        if s['url'] != f'https://www.sjcindiana.gov/DocumentCenter/View/{d}':
            err(f'source {s["id"]} url {s["url"]}')
        if s['title'] != manifest.get(d, {}).get('title'):
            err(f'source {s["id"]} title differs from the posted title')
    if len(src) != len(manifest):
        err(f'{len(src)} sources for {len(manifest)} manifest docs')

    lines = {r['doc_id']: r for r in csv.DictReader(open(os.path.join(CF, 'cf_lines_final.csv'), encoding='utf-8'))}
    keys = {r['filing_id']: r['committee_key'] for r in csv.DictReader(open(os.path.join(CF, '_committee_keys.csv'), encoding='utf-8'))}

    # ---- cf_local
    rows = read(os.path.join(ED, 'cf_local.csv'), CF_HDR)
    units = {r['unit_id'] for r in csv.DictReader(open(os.path.join(ED, 'units.csv'), encoding='utf-8'))}
    merged = collections.Counter()
    seen = {}
    for r in rows:
        fid = r['filing_id']
        docs = r['doc_ids'].split(';')
        primary = fid.replace('cfl-', '')
        if primary not in docs:
            err(f'{fid}: primary doc not in doc_ids')
        for d in docs:
            merged[d] += 1
        for k in FIG:
            money(r[k], f'{fid}.{k}')
        for k in ('period_from', 'period_to'):
            if r[k] and not DATE.fullmatch(r[k]):
                err(f'{fid}: bad {k} {r[k]!r}')
        if r['party'] not in ('D', 'R', 'L', 'I', 'NP', 'O', ''):
            err(f'{fid}: party {r["party"]}')
        if r['party'] == 'O' and 'other' not in r['notes'].lower():
            err(f'{fid}: party O without a note')
        if r['amended'] not in ('yes', 'no', ''):
            err(f'{fid}: amended {r["amended"]}')
        if r['status'] != 'from_scan':
            err(f'{fid}: status {r["status"]}')
        if r['double_entry'] not in ('agreed', 'adjudicated', 'single'):
            err(f'{fid}: double_entry {r["double_entry"]}')
        if r['unit_id'] and r['unit_id'] not in units:
            err(f'{fid}: unit_id {r["unit_id"]} not in units.csv')
        for s in r['source_ids'].split(';'):
            if s not in src_ids:
                err(f'{fid}: source {s} missing')
        if sorted(r['source_ids'].split(';')) != sorted(f'CFL-{d}' for d in docs):
            err(f'{fid}: source_ids do not match doc_ids')
        L = lines.get(primary)
        if L is None:
            err(f'{fid}: no line-level reading')
            continue
        ts = r['transcription_status']
        if ts != L['final_status']:
            err(f'{fid}: status {ts} differs from line file {L["final_status"]}')
        if ts == 'unreadable':
            if any(r[k] for k in FIG):
                err(f'{fid}: unreadable row carries figures')
        else:
            for k, c in FIG.items():
                if r[k] != L[c]:
                    err(f'{fid}: {k}={r[k]!r} but line {c}={L[c]!r}')
            fails = identity_failures(L)
            if ts == 'verified' and (fails or L['derived_cells']):
                err(f'{fid}: verified but fails={fails} derived={L["derived_cells"]}')
            elif ts == 'derived' and (fails or not L['derived_cells']):
                err(f'{fid}: derived but fails={fails} derived={L["derived_cells"]!r}')
            elif ts == 'filer-inconsistent' and not fails:
                err(f'{fid}: filer-inconsistent but every identity holds')
            elif ts not in ('verified', 'derived', 'filer-inconsistent'):
                err(f'{fid}: transcription_status {ts}')
        # duplicates
        k = (keys.get(fid), r['office_normalized'], r['period_from'], r['period_to'],
             r['report_type'] if not r['period_to'] else '')
        if k in seen:
            err(f'duplicate committee+period: {fid} and {seen[k]} {k}')
        seen[k] = fid
    for d, n in merged.items():
        if n > 1:
            err(f'doc {d} merged into {n} rows')

    # ---- CFA-11
    lc = read(os.path.join(ED, 'cf_large_contributions.csv'),
              ['doc_id', 'candidate', 'committee', 'contributor', 'amount', 'date', 'status', 'source_ids', 'notes'])
    cfa11 = set()
    for r in lc:
        cfa11.add(r['doc_id'])
        money(r['amount'], f'CFA-11 {r["doc_id"]}')
        if not DATE.fullmatch(r['date']):
            err(f'CFA-11 {r["doc_id"]}: date {r["date"]}')
        if r['source_ids'] != f'CFL-{r["doc_id"]}' or r['source_ids'] not in src_ids:
            err(f'CFA-11 {r["doc_id"]}: source_ids {r["source_ids"]}')
        if not r['contributor']:
            err(f'CFA-11 {r["doc_id"]}: no contributor')
        if lines[r['doc_id']]['final_status'] != 'not-summary':
            err(f'CFA-11 {r["doc_id"]} is a summary sheet')

    # ---- coverage
    cov = read(os.path.join(ED, 'cf_coverage.csv'),
               ['office_normalized', 'unit_id', 'cycle', 'committees', 'filings', 'report_types', 'periods_covered',
                'expected_report_types', 'committees_with_all_expected', 'transcription_statuses', 'status',
                'source_ids', 'notes'])
    if sum(int(c['filings']) for c in cov) != len(rows):
        err('coverage filings do not sum to the cf_local row count')
    notes_md = open(os.path.join(CF, 'coverage-notes.md'), encoding='utf-8').read()
    for g in GAPS:
        if g not in notes_md:
            err(f'gap doc {g} not listed in coverage-notes.md')

    # ---- every doc accounted for
    for d in manifest:
        where = [w for w, ok in (('cf_local', d in merged), ('CFA-11', d in cfa11), ('gap', d in GAPS)) if ok]
        if len(where) != 1:
            err(f'doc {d} accounted for {where or "nowhere"}')

    # ---- no contact details
    pii = [re.compile(r'\(?\b\d{3}\)?[ .-]?\d{3}[ .-]\d{4}\b'), re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+'),
           re.compile(r'\b\d{2,6}\s+(?:[NSEW]\.?\s+)?[A-Z][a-z]+\s+(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ct|Court|Ln|Lane|Blvd|Way|Pl|Place)\b'),
           re.compile(r'\bP\.?\s?O\.?\s+Box\b', re.I), re.compile(r'\bIN\s+4\d{4}\b')]
    for fn in ('cf_local.csv', 'cf_large_contributions.csv', 'cf_coverage.csv', 'sources_cf_local.csv'):
        txt = open(os.path.join(ED, fn), encoding='utf-8').read()
        for p in pii:
            for m in p.finditer(txt):
                err(f'{fn}: possible contact detail {m.group(0)!r}')

    print(f'cf_local rows {len(rows)}; CFA-11 entries {len(lc)} from {len(cfa11)} notices; coverage rows {len(cov)}; '
          f'sources {len(src)}; manifest docs {len(manifest)}; gaps {len(GAPS)}')
    print('transcription_status', dict(collections.Counter(r['transcription_status'] for r in rows)))
    if errors:
        print(f'{len(errors)} problem(s):')
        for e in errors:
            print('  ' + e)
        sys.exit(1)
    print('OK')


if __name__ == '__main__':
    main()
