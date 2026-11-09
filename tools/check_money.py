"""Validate the money-area data files.

Run:  python -P -E tools/check_money.py
Exit status 1 if any check fails. Prints each unit's budget series and flags
year-over-year jumps over 40% that are not explained by a series_break row.
"""
import csv, collections, sys

D = 'C:/Users/nickb/local-gov-guide/data/editions/st-joseph/'
STATUS = {'official', 'unofficial', 'computed', 'from_scan', 'secondary', 'single_source'}
BASES = {'general_fund', 'advertised_all_funds', 'all_funds_incl_utilities', 'gateway_reported_funds'}
AOA = {'adopted', 'actual', 'proposed', 'series_break'}
HEADERS = {
    'budgets.csv': 'unit_id,year,basis,amount,adopted_or_actual,series_id,status,source_ids,notes',
    'budget_breakdowns.csv': 'unit_id,year,kind,category,amount,basis,status,source_ids,notes',
    'tax_rates.csv': 'unit_id,taxing_district,year,rate_per_100,rate_kind,status,source_ids,notes',
    'debt.csv': 'unit_id,year,debt_type,amount,status,source_ids,notes',
    'cf_state.csv': 'committee,candidate,office,district,party,year,receipts,expenditures,cash_end,top_funder_types,status,source_ids,notes',
    'sources_money.csv': 'id,url,title,publisher,accessed,kind,notes',
    'gaps_money.csv': 'area,item,why_missing,how_to_fill',
}
errors = []


def err(msg):
    errors.append(msg)


def load(fn):
    with open(D + fn, encoding='utf-8', newline='') as f:
        rows = list(csv.reader(f))
    if ','.join(rows[0]) != HEADERS[fn]:
        err('%s: header mismatch: %s' % (fn, ','.join(rows[0])))
    out = []
    for i, r in enumerate(rows[1:], start=2):
        if len(r) != len(rows[0]):
            err('%s line %d: %d fields, expected %d' % (fn, i, len(r), len(rows[0])))
            continue
        out.append((i, dict(zip(rows[0], r))))
    return out


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


src_ids = {r['id'] for _, r in load('sources_money.csv')}
if len(src_ids) != len(load('sources_money.csv')):
    err('sources_money.csv: duplicate ids')
for _, r in load('sources_money.csv'):
    if not r['id'].startswith('MON-') or r['kind'] not in {'primary', 'news', 'secondary', 'statute', 'dataset', 'derived'} or not r['url']:
        err('sources_money.csv: bad row %s' % r['id'])


def common(fn, rows, amount_cols):
    for i, r in rows:
        if r['status'] not in STATUS:
            err('%s line %d: bad status %r' % (fn, i, r['status']))
        ids = [x for x in r['source_ids'].split(';') if x]
        if not ids:
            err('%s line %d: no source_ids' % (fn, i))
        for x in ids:
            if x not in src_ids:
                err('%s line %d: unknown source id %s' % (fn, i, x))
        for c in amount_cols:
            if num(r[c]) is None:
                err('%s line %d: non-numeric %s=%r' % (fn, i, c, r[c]))
        if 'year' in r and not (r['year'].isdigit() and 2000 <= int(r['year']) <= 2030):
            err('%s line %d: bad year %r' % (fn, i, r['year']))


# ------------------------------------------------------------- budgets
B = load('budgets.csv')
for i, r in B:
    brk = r['adopted_or_actual'] == 'series_break'
    if r['basis'] not in BASES:
        err('budgets line %d: bad basis %r' % (i, r['basis']))
    if r['adopted_or_actual'] not in AOA:
        err('budgets line %d: bad adopted_or_actual %r' % (i, r['adopted_or_actual']))
    if brk:
        if r['amount'] != '':
            err('budgets line %d: series_break row must have blank amount' % i)
        if not r['notes']:
            err('budgets line %d: series_break row needs an explanation in notes' % i)
    else:
        if num(r['amount']) is None:
            err('budgets line %d: non-numeric amount %r' % (i, r['amount']))
        elif num(r['amount']) < 0:
            err('budgets line %d: negative amount' % i)
        if not (r['year'].isdigit() and 2012 <= int(r['year']) <= 2026):
            err('budgets line %d: year outside 2012-2026: %r' % (i, r['year']))
    if not r['series_id'] or not r['basis']:
        err('budgets line %d: missing series_id/basis' % i)
common('budgets.csv', [(i, r) for i, r in B], [])
# no series mixes bases; one amount per series-year
bases_by_series = collections.defaultdict(set)
seen = set()
for i, r in B:
    bases_by_series[r['series_id']].add(r['basis'])
    if r['adopted_or_actual'] != 'series_break':
        k = (r['series_id'], r['year'])
        if k in seen:
            err('budgets line %d: duplicate series-year %s' % (i, k))
        seen.add(k)
for s, b in bases_by_series.items():
    if len(b) > 1:
        err('series %s mixes bases %s' % (s, sorted(b)))
units_by_series = collections.defaultdict(set)
for i, r in B:
    units_by_series[r['series_id']].add(r['unit_id'])
for s, u in units_by_series.items():
    if len(u) > 1:
        err('series %s spans several units %s' % (s, sorted(u)))

# year-over-year check and sanity table
by_series = collections.defaultdict(dict)
breaks = collections.defaultdict(set)
for i, r in B:
    if r['adopted_or_actual'] == 'series_break':
        breaks[r['series_id']].add(int(r['year']))
    else:
        by_series[r['series_id']][int(r['year'])] = (float(r['amount']), r['unit_id'], r['basis'], r['status'])
flags = []
for s, ys in by_series.items():
    for y in sorted(ys):
        if y - 1 in ys:
            a, b = ys[y - 1][0], ys[y][0]
            if a > 0 and abs(b / a - 1) > 0.4 and y not in breaks[s] and (y - 1) not in breaks[s]:
                flags.append((s, y - 1, y, a, b))

print('=== budget series ($ millions; adopted/actual per series; * = status other than computed/official) ===')
by_unit = collections.defaultdict(list)
for s, ys in by_series.items():
    unit = next(iter(ys.values()))[1]
    by_unit[unit].append(s)
for unit in sorted(by_unit):
    print('\n%s' % unit)
    for s in sorted(by_unit[unit]):
        ys = by_series[s]
        basis, status = next(iter(ys.values()))[2:4]
        cells = ' '.join('%d:%.2f' % (y, ys[y][0] / 1e6) for y in sorted(ys))
        brk = (' [break at %s]' % sorted(breaks[s])) if breaks.get(s) else ''
        print('  %s [%s, %s]%s\n    %s' % (s, basis, status, brk, cells))
print('\n=== year-over-year jumps over 40%% not explained by a series_break: %d ===' % len(flags))
for s, y0, y1, a, b in sorted(flags):
    print('  %-48s %d->%d  %12.0f -> %12.0f  (%+.0f%%)' % (s, y0, y1, a, b, (b / a - 1) * 100))

# ------------------------------------------------------------- other files
BD = load('budget_breakdowns.csv')
common('budget_breakdowns.csv', BD, ['amount'])
for i, r in BD:
    if r['kind'] not in ('spending', 'revenue'):
        err('budget_breakdowns line %d: bad kind' % i)
# each (unit, year, basis) group of full-coverage breakdowns should be internally consistent in kind
kinds = collections.defaultdict(set)
for i, r in BD:
    kinds[(r['unit_id'], r['year'], r['basis'])].add(r['kind'])
for k, v in kinds.items():
    if len(v) > 1:
        err('budget_breakdowns: basis group %s mixes kinds' % (k,))

TR = load('tax_rates.csv')
common('tax_rates.csv', TR, ['rate_per_100'])
for i, r in TR:
    if num(r['rate_per_100']) is not None and not (0 < num(r['rate_per_100']) < 20):
        err('tax_rates line %d: implausible rate %s' % (i, r['rate_per_100']))
    if r['rate_kind'] not in ('sum_of_fund_net_rates', 'general_fund_net_rate', 'park_fund_net_rate'):
        err('tax_rates line %d: bad rate_kind' % i)
seen_t = set()
for i, r in TR:
    k = (r['unit_id'], r['taxing_district'], r['year'], r['rate_kind'])
    if k in seen_t:
        err('tax_rates line %d: duplicate %s' % (i, k))
    seen_t.add(k)

DB = load('debt.csv')
common('debt.csv', DB, ['amount'])

CF = load('cf_state.csv')
common('cf_state.csv', CF, ['receipts', 'expenditures'])
for i, r in CF:
    if r['cash_end'] != '' and num(r['cash_end']) is None:
        err('cf_state line %d: non-numeric cash_end' % i)
    if r['party'] not in {'D', 'R', 'L', 'I', 'G', 'NP', 'W', 'O'}:
        err('cf_state line %d: bad party' % i)
    if not (2016 <= int(r['year']) <= 2026):
        err('cf_state line %d: year outside 2016-2026' % i)
seen_c = set()
for i, r in CF:
    k = (r['committee'], r['year'])
    if k in seen_c:
        err('cf_state line %d: duplicate %s' % (i, k))
    seen_c.add(k)

load('gaps_money.csv')

print('\nrows: budgets %d, breakdowns %d, tax_rates %d, debt %d, cf_state %d' % (len(B), len(BD), len(TR), len(DB), len(CF)))
if errors:
    print('\nFAILED: %d error(s)' % len(errors))
    for e in errors[:60]:
        print('  ', e)
    sys.exit(1)
print('\nOK: all rows parse; no series mixes bases; amounts numeric; every row has status and source_ids.')
