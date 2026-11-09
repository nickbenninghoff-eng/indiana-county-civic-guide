import re,sys,json
R='C:/Users/nickb/local-gov-guide/research/'
FILES=['results-2010-2014.md','results-2015-2019.md','results-2020-2026.md']
def split_row(line):
    s=line.strip()
    assert s.startswith('|')
    s=s[1:]
    if s.endswith('|'): s=s[:-1]
    return [c.strip() for c in s.split('|')]
def parse(fn):
    rows=[]; h2=None; h3=None; hdr=None; lineno=0
    lines=open(R+fn,encoding='utf-8').read().split('\n')
    for i,l in enumerate(lines,1):
        if l.startswith('## '): h2=l[3:].strip(); h3=None; hdr=None; continue
        if l.startswith('### '): h3=l[4:].strip(); hdr=None; continue
        if l.startswith('|'):
            c=split_row(l)
            if hdr is None:
                hdr=[x.lower() for x in c]; continue
            if set(''.join(c))<=set('-: '): continue
            rows.append(dict(file=fn,line=i,h2=h2,h3=h3,hdr=hdr,cells=c))
        else:
            if hdr is not None and l.strip()=='' : pass
            if not l.startswith('|'): hdr=hdr if l.strip()=='' else None
    return rows
if __name__=='__main__':
    for fn in FILES:
        rows=parse(fn)
        from collections import Counter
        cnt=Counter((r['h2'],r['h3'],tuple(r['hdr'])) for r in rows)
        for k,v in cnt.items(): print(fn[8:17],v,k)
