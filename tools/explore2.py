from res_raw import *
from collections import OrderedDict
rows=parse('results-2020-2026.md')
g=OrderedDict()
for r in rows:
    h=r['hdr']
    if 'winner' not in h: continue
    d=dict(zip(h,r['cells']))
    if not r['h2'][:4].isdigit(): continue
    k=(d['year'],d['election'],d['jurisdiction'],d['office'],d['district'])
    g.setdefault(k,[]).append((d['candidate'],d['party'],d['votes'],d['winner']))
for k,v in g.items():
    ws=[x[3] for x in v]
    if any(w in('multi-seat','n/a','') for w in ws) and not (k[3].startswith('Township Board') or k[3]=='Township Board') :
        print(k[0],k[1][:4],k[2],'|',k[3],'|',k[4],'| n=',len(v),set(ws))
