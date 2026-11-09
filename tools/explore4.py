from res_raw import *
import re
a=[r for r in parse('results-2015-2019.md') if (r['h2'] or '').startswith('2020 PRIMARY')]
b=[r for r in parse('results-2020-2026.md') if (r['h2'] or '').startswith('2020 Primary')]
def key(d): 
    return (re.sub(r'[^a-z]','',d['candidate'].lower()), d['votes'].replace(',','').split()[0])
A={}
for r in a:
    d=dict(zip(r['hdr'],r['cells'])); A[key(d)]=d
B={}
for r in b:
    if 'votes' not in r['hdr']: continue
    d=dict(zip(r['hdr'],r['cells'])); B[key(d)]=d
print(len(A),len(B))
for k in A:
    if k not in B: print('only in 60003:',k,A[k]['office'],A[k]['district'])
cb={k[0] for k in B}
for k in B:
    if k not in A and k[0] in {x[0] for x in A}: print('vote differs',k)
print('B only candidates not in A:',len([k for k in B if k[0] not in {x[0] for x in A}]))
