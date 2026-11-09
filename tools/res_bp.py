"""Parse the Ballotpedia district tables in research/09 into {(year, chamber, district): [(name, party, pct, votes), ...]}."""
import re, os, sys
R = 'C:/Users/nickb/local-gov-guide/research/09-gap-fill-ballotpedia-statutes.md'
SEG = re.compile(r'^\s*(?P<name>[^()]+?)\s*\((?P<party>[A-Z])(?:,\s*[^)]*)?\)\s*(?P<rest>.*)$')


def parse_bp():
    out = {}
    chamber = dist = None
    for line in open(R, encoding='utf-8'):
        line = line.rstrip('\n')
        m = re.match(r'^### (House|Senate) District (\d+)', line)
        if m:
            chamber = 'house' if m.group(1) == 'House' else 'senate'; dist = m.group(2); continue
        if line.startswith('## '):
            chamber = None
        if chamber and line.startswith('| 20'):
            cells = [c.strip() for c in line.strip('|').split('|')]
            if not re.fullmatch(r'20\d\d', cells[0]):
                continue
            year = int(cells[0])
            body = ' ; '.join(cells[1:])
            body = re.sub(r'\s*\((?:total|Teshka|page prints)[^)]*\)', '', body)
            body = re.sub(r'\s*\.\s*Incumbent .*$', '', body)
            body = re.sub(r'\b\d{1,3}(,\d{3})+\s*$', lambda mm: mm.group(0), body)
            cands = []
            for seg in re.split(r'\s*;\s*', body):
                seg = seg.strip()
                if not seg or re.fullmatch(r'[\d,]+', seg):
                    continue
                mm = SEG.match(seg)
                if not mm:
                    continue
                rest = mm.group('rest')
                pm = re.search(r'(\d+(?:\.\d+)?)%', rest)
                vm = [x for x in re.findall(r'\d[\d,]*', re.sub(r'\d+(?:\.\d+)?%', '', rest)) if x.strip(',')]
                votes = int(vm[-1].replace(',', '')) if vm else None
                name = re.sub(r'^Incumbent\s+', '', mm.group('name')).strip()
                cands.append(dict(name=name, party=mm.group('party'), pct=float(pm.group(1)) if pm else None,
                                  votes=votes, unopposed='unopposed' in rest.lower(),
                                  incumbent='incumbent' in seg.lower()))
            out[(year, chamber, dist)] = cands
    return out


if __name__ == '__main__':
    for k, v in sorted(parse_bp().items(), key=lambda x: (x[0][1], int(x[0][2]), x[0][0])):
        print(k, [(c['name'], c['party'], c['pct'], c['votes'], 'U' if c['unopposed'] else '') for c in v])
