import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from res_rows import *
from res_bp import parse_bp
recs,_=load_records()
bp=parse_bp()
can={}
for r in recs:
    if r['kind']=='state' and r['o_slug'] in('senate','house') and r['eid'].endswith('g'):
        can.setdefault((int(r['eid'][:4]),r['o_slug'],r['dist']),[]).append((r['cand'],r['party'],r['votes']))
for k in sorted(can,key=lambda x:(x[1],int(x[2]),x[0])): print('CANVASS',k,can[k])
print()
for k in sorted(bp,key=lambda x:(x[1],int(x[2]),x[0])):
    if k not in can: print('BP-only',k,[(c['name'],c['votes']) for c in bp[k]])
