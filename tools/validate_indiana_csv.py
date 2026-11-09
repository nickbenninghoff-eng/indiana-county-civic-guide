"""Validate data/indiana/*.csv: header matches SCHEMA.md, rows parse, field counts match,
status/confidence values are allowed, source_ids exist in sources_indiana.csv, no banned words.
Run: python -P -E tools/validate_indiana_csv.py
"""
import csv, os, re, sys

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'indiana')
HEADERS = {
    'unit_types.csv': 'unit_type,label,plural,what_it_does,elected_bodies,can_levy_tax,statute,status,source_ids',
    'office_types.csv': 'office_type,label,unit_type,term_years,cycle,partisan,term_limit,vacancy_rule,statute,what_it_does,status,source_ids',
    'election_rules.csv': 'topic,rule_key,plain_language,detail,effective_from,effective_to,statute,status,confidence,source_ids',
    'statewide_offices.csv': 'office,what_it_does,term_years,elected_or_appointed,status,source_ids',
    'statewide_terms.csv': 'person,office,party,start,end,selected_by,status,confidence,source_ids,notes',
    'general_assembly_control.csv': 'year,chamber,d_seats,r_seats,other_seats,total_seats,supermajority_party,status,source_ids,notes',
    'state_local_rules.csv': 'topic,plain_language,detail,statute,effective,status,confidence,source_ids',
    'sources_indiana.csv': 'id,url,title,publisher,accessed,kind,notes',
    'gaps_indiana.csv': 'area,item,why_missing,how_to_fill',
}
STATUS = {'official', 'unofficial', 'computed', 'from_scan', 'secondary', 'single_source', 'derived'}
CONF = {'high', 'medium', 'low'}
BANNED = re.compile(r"\b(flip(ped)?|sweep|landslide|seized|won back|wave|safe|target(ed)?|vulnerable)\b", re.I)

errors = []
src_ids = set()
with open(os.path.join(BASE, 'sources_indiana.csv'), encoding='utf-8', newline='') as f:
    for r in csv.DictReader(f):
        src_ids.add(r['id'])

for name, hdr in HEADERS.items():
    path = os.path.join(BASE, name)
    with open(path, encoding='utf-8', newline='') as f:
        rd = csv.reader(f)
        head = next(rd)
        if ','.join(head) != hdr:
            errors.append(f'{name}: header mismatch')
        n = 0
        for i, row in enumerate(rd, start=2):
            n += 1
            if len(row) != len(head):
                errors.append(f'{name}:{i}: {len(row)} fields, expected {len(head)}')
                continue
            d = dict(zip(head, row))
            if 'status' in d and d['status'] not in STATUS:
                errors.append(f'{name}:{i}: bad status {d["status"]!r}')
            if 'confidence' in d and d['confidence'] not in CONF:
                errors.append(f'{name}:{i}: bad confidence {d["confidence"]!r}')
            if 'source_ids' in d:
                if not d['source_ids']:
                    errors.append(f'{name}:{i}: empty source_ids')
                for s in d['source_ids'].split(';'):
                    if s not in src_ids:
                        errors.append(f'{name}:{i}: unknown source id {s}')
            if name not in ('sources_indiana.csv',):
                for k, v in d.items():
                    if BANNED.search(v):
                        errors.append(f'{name}:{i}: banned word in {k}: {BANNED.search(v).group(0)}')
        print(f'{name}: {n} rows')

if errors:
    print('\n'.join(errors))
    sys.exit(1)
print('All files OK')
