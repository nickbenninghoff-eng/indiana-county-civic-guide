from res_raw import *
from collections import Counter
c=Counter()
for fn in FILES:
    for r in parse(fn):
        h=r['hdr']
        if 'votes' not in h: continue
        d=dict(zip(h,r['cells']))
        off=d.get('office',d.get('measure',''))
        c[(d['jurisdiction'],off,d.get('district',''))]+=1
import collections
juris=collections.defaultdict(set)
for (j,o,dd),n in c.items(): juris[j].add(o)
for j in sorted(juris): print(j,'::',sorted(juris[j]))
