"""Compare first readings (visual-chunk-*.csv) with blind second readings (verify-*.csv), cell by cell.
Usage: python -P -E tools/cf_double_entry_diff.py   (run from research/cf)
Writes double-entry-diff.csv (one row per disagreeing cell) and prints a summary."""
import csv, glob
NUM = ['l13A','l14B','l15aA','l15bA','l15cA','l16A','l17aA','l17bA','l17cA','l18A',
       'l15aB','l15bB','l15cB','l16B','l17aB','l17bB','l17cB','l18B','l19','l20']
def load(pattern):
    out = {}
    for f in sorted(glob.glob(pattern)):
        for r in csv.DictReader(open(f, encoding='utf-8')):
            out[r['doc_id'].strip()] = r
    return out
def num(v):
    v = (v or '').strip().replace(',', '').replace('$', '')
    if v in ('', '-', 'N/A', 'n/a'): return None
    try: return round(float(v), 2)
    except ValueError: return v
first, second = load('visual-chunk-*.csv'), load('verify-[0-9].csv')
diffs, agree_docs, status_disagree = [], 0, []
for doc, b in second.items():
    a = first.get(doc)
    if a is None: continue
    cells = [(c, num(a.get(c)), num(b.get(c))) for c in NUM if num(a.get(c)) != num(b.get(c))]
    if not cells: agree_docs += 1
    for c, x, y in cells:
        diffs.append({'doc_id': doc, 'tab': a['tab'], 'cell': c, 'first': x, 'second': y,
                      'first_status': a['status'], 'second_status': b['status']})
    if a['status'] != b['status']: status_disagree.append((doc, a['status'], b['status']))
with open('double-entry-diff.csv', 'w', newline='', encoding='utf-8') as o:
    w = csv.DictWriter(o, fieldnames=['doc_id','tab','cell','first','second','first_status','second_status'])
    w.writeheader(); w.writerows(diffs)
docs_with_diff = sorted({d['doc_id'] for d in diffs})
total_cells = len(second) * len(NUM)
print(f"compared {len(second)} docs; {agree_docs} agree on every numeric cell; {len(docs_with_diff)} docs have {len(diffs)} differing cells (of {total_cells} cells = {100*len(diffs)/total_cells:.1f}%)")
print(f"status disagreements: {len(status_disagree)}")
blank_vs_value = sum(1 for d in diffs if d['first'] is None or d['second'] is None)
print(f"  of differing cells, {blank_vs_value} are blank-vs-value (often 'blank vs 0' or a derived fill)")
