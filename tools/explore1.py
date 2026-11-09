from res_raw import *
from collections import Counter
import re
allrows=[]
for fn in FILES: allrows+=parse(fn)
# unusual
wc=Counter(); pc=Counter()
for r in allrows:
    h=r['hdr']; c=r['cells']
    if 'votes' not in h: continue
    d=dict(zip(h,c))
    v=d['votes']; 
    if not re.fullmatch(r'[\d,]+',v): print('VOTES',r['file'][8:17],r['line'],repr(v),d.get('candidate'))
    p=d.get('percent',d.get('pct'))
    if p is not None and not re.fullmatch(r'\d+(\.\d+)?',p): print('PCT',r['file'][8:17],r['line'],repr(p)[:100],d.get('candidate'))
    w=d.get('winner')
    if w is not None: wc[w]+=1
    if d.get('party') is not None: pc[d['party']]+=1
    if len(c)!=len(h): print('LEN',r['file'],r['line'],len(c),len(h))
print(wc); print(pc)
