"""Parse the OCR layout text of the county's 2020 Precinct Summary Report (MAP-009).

    from precinct_report_2020 import parse_reads
    accepted, failed, names, pages, log = parse_reads([read1, read2, ...], want, known_codes)

`want(title)` returns a contest id for the race titles to read (None skips the box). The layout files are written by
tools/ocr_2020_precinct_report.py, one file per OCR read (different render zooms). Each page has a header with the
precinct name and 6-digit code, then two columns of race boxes:

    ST. JOSEPH COUNTY CORONER
    Vote For 1
    Total Votes    775
    MICHAEL J MCGANN (DEM)    276    35.61%
    PATRICIA JORDAN (REP)    499    64.39%

A box is ACCEPTED for a precinct only when, in one OCR read,
  * the printed Total Votes was read,
  * every candidate row has a party tag, a vote count and a printed percentage (all read, none inferred),
  * the candidate votes add up to the printed Total Votes, and
  * every printed percentage equals votes / Total Votes x 100 rounded to two decimals (the report's rounding).
Every read that passes must give the same numbers, or the box is rejected. Which precinct a page belongs to is decided
from all reads together (page_codes); the caller then confirms each precinct's identity against an independent source. Nothing is filled in or guessed: a box
that fails in every read is reported and left out (the caller's county-sum check then fails loudly).
Stdlib only.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

PARTY_TAGS = {"DEM": "D", "REP": "R", "LIB": "L", "W": "W", "IND": "O", "NP": "NP"}
# OCR spellings of the party tags in this report; anything not listed fails the box.
TAG_FIX = {"LB": "LIB", "UB": "LIB", "LIS": "LIB", "DEN": "DEM", "OEM": "DEM", "REF": "REP", "RFP": "REP", "VV": "W"}
TAG_RE = re.compile(r"\((" + "|".join(sorted(set(PARTY_TAGS) | set(TAG_FIX), key=len, reverse=True)) + r")\)")
TOTAL_RE = re.compile(r"^To\w{2,3}\s+[Vv]o\w{2,3}\b(.*)$")
VOTEFOR_RE = re.compile(r"^Vote\s+For\b", re.I)
CODE_RE = re.compile(r"(?<![\dA-Za-z])([0-9OoIlgS]{6})\s*$")
PAGE_RE = re.compile(r"Page\s+([1-5lI])\s*[/1lI|]\s*([1-5])\b")   # 'Page 1/2' (OCR also gives 'Page 112')
# printed percentages: '35.61%'; OCR sometimes reads '%' as '0/0' or 'o/o'
PCT_RE = re.compile(r"^(\d{1,3})(?:[.,](\d{2}))?\s?(?:%|0/0|o/o)[^\w]*$")
DIGIT_FIX = str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1", "|": "1"})
CODE_FIX = str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1", "g": "9", "S": "5"})


def to_int(tok: str):
    """'1,005' / '1 ,005' -> 1005; OCR letters O/I/l read as digits; None when it is not a whole number."""
    t = re.sub(r"\s*,\s*", ",", tok.strip().rstrip(".")).translate(DIGIT_FIX)
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+|\d+", t):
        return int(t.replace(",", ""))
    return None


def pages_of(path: Path):
    """[(page_no, header_lines, left_lines, right_lines)]"""
    out = []
    cur = None
    part = None
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        if ln.startswith("#### PAGE "):
            cur = [int(ln.split()[2]), [], [], []]
            out.append(cur)
            part = 1
        elif cur is None or ln.startswith("# "):
            continue
        elif ln == "## LEFT":
            part = 2
        elif ln == "## RIGHT":
            part = 3
        else:
            cur[part].append(ln)
    return out


def header_info(head, known):
    """(code or None, name, page k, of m). The code is the 6-digit number ending the precinct-name row and must be a
    known precinct code."""
    code, name = None, ""
    for ln in head:
        if "Registered" in ln or "Date" in ln or "Page" in ln:
            continue
        m = CODE_RE.search(ln)
        if m and re.search(r"[A-Za-z]{3}", ln[:m.start()]):
            c = m.group(1).translate(CODE_FIX)
            name = ln[:m.start()].strip()
            code = c if c in known else None
    k = of = None
    for ln in head:
        pm = PAGE_RE.search(ln)
        if pm:
            k, of = int(pm.group(1).translate(DIGIT_FIX)), int(pm.group(2))
    return code, name, k, of


def row_numbers(s: str):
    """(name, votes, pct_text) for a candidate row 'NAME (TAG)    276    35.61%'; votes None when not such a row."""
    segs = [x for x in re.split(r"\s{2,}", s.strip()) if x]
    if len(segs) >= 3 and PCT_RE.match(segs[-1].replace(" ", "")):
        v = to_int(segs[-2])
        if v is not None:
            return " ".join(segs[:-2]), v, segs[-1]
    return s, None, None


def pct_ok(votes, total, pct_text):
    m = PCT_RE.match(pct_text.replace(" ", ""))
    if not m or total == 0:
        return False
    whole, frac = int(m.group(1)), m.group(2)
    if frac is None:           # the report prints '0%' for a candidate with no votes
        return votes == 0 and whole == 0
    return abs(round(votes / total * 100 + 1e-9, 2) - (whole + int(frac) / 100)) < 0.0051


def boxes(lines):
    """Split one column into race boxes: [(title, text after 'Total Votes', lines below it)]."""
    idx = [i for i, ln in enumerate(lines) if TOTAL_RE.match(ln.strip())]
    out = []
    for n, i in enumerate(idx):
        # title: the lines above Total Votes (skipping 'Vote For'), back to the box above's last candidate row
        j, title = i - 1, []
        prev = idx[n - 1] if n else -1
        while j > prev:
            s = lines[j].strip()
            if not VOTEFOR_RE.match(s):
                if row_numbers(s)[1] is not None or TAG_RE.search(s):
                    break
                title.insert(0, s)
            j -= 1
        nxt = idx[n + 1] if n + 1 < len(idx) else len(lines)
        out.append((" ".join(title), TOTAL_RE.match(lines[i].strip()).group(1), lines[i + 1:nxt]))
    return out


def parse_box(total_text, body):
    """-> ([(party, name, votes)], None) or (None, reason)."""
    toks = [t for t in re.split(r"\s{2,}", total_text.strip()) if t]
    total = to_int(toks[0]) if toks else None
    if total is None:
        return None, f"Total Votes not read ({total_text.strip()!r})"
    cands = []   # [name, tag, votes, pct]
    for k, s in enumerate(body):
        s = s.strip()
        name, v, pct = row_numbers(s)
        tm = TAG_RE.search(s)
        if v is not None:
            cands.append([name, tm.group(1) if tm else None, v, pct])
            continue
        if VOTEFOR_RE.match(s):
            continue
        if tm and cands and cands[-1][1] is None and not re.search(r"\d", s):
            cands[-1][1] = tm.group(1)             # wrapped name: the tag is on the next printed line
            continue
        if tm or any(PCT_RE.match(x.replace(" ", "")) for x in re.split(r"\s{2,}", s)):
            return None, f"candidate row not fully read: {s!r}"
        if cands and cands[-1][1] is None and k + 1 < len(body) and TAG_RE.search(body[k + 1]) \
                and not re.search(r"\d", body[k + 1]):
            continue                               # middle line of a three-line name
        break                                      # the next box's title
    if not cands:
        return None, "no candidate rows read"
    out = []
    for name, tag, v, pct in cands:
        if tag is None:
            return None, f"no party tag read for {name!r}"
        p = PARTY_TAGS[TAG_FIX.get(tag, tag)]
        if not pct_ok(v, total, pct):
            return None, f"{name!r}: {v} of {total} votes is not the printed {pct}"
        out.append((p, TAG_RE.sub("", name).strip(), v))
    if sum(v for _p, _n, v in out) != total:
        return None, f"candidate sum {sum(v for _p, _n, v in out)} != Total Votes {total}"
    return out, None




def page_codes(reads, known, name_code, problems):
    """{page_no: code}. Every read sees the same physical pages, so the code of each page is decided from ALL reads
    together. Each precinct's pages are printed as a run 'Page 1/m' ... 'Page m/m'; a run's code is the one most of
    its header reads give (the code implied by a township precinct's name, e.g. 'PENN TWP 6' -> 110006, counts as
    one more read). A run with no clear majority is skipped; a code given to two runs stops the parse."""
    pnos = sorted({pno for plist, _info in reads for pno, *_ in plist})
    by_page = defaultdict(list)          # page -> [(code, name, k, of)] one per read
    for plist, info in reads:
        for (pno, *_rest), inf in zip(plist, info):
            by_page[pno].append(inf)

    def most(vals):
        vals = [v for v in vals if v is not None]
        return Counter(vals).most_common(1)[0][0] if vals else None
    kof = {p: (most(i[2] for i in by_page[p]), most(i[3] for i in by_page[p])) for p in pnos}
    runs, cur = [], []
    for p in pnos:
        k, of = kof[p]
        start_of = next((kof[q][1] for q in cur if kof[q][1]), None)
        if cur and (k == 1 or (k is not None and kof[cur[-1]][0] is not None and k != kof[cur[-1]][0] + 1)
                    or (start_of is not None and len(cur) >= start_of)):
            runs.append(cur)
            cur = []
        cur.append(p)
    if cur:
        runs.append(cur)
    codes, owner = {}, {}
    for run in runs:
        votes = Counter()
        for p in run:
            for c, nm, _k, _of in by_page[p]:
                for v in (c, name_code(nm) if nm else None):
                    if v in known:
                        votes[v] += 1
        ranked = votes.most_common()
        if not ranked or (len(ranked) > 1 and ranked[0][1] == ranked[1][1]):
            problems.append(f"pages {run}: precinct code unclear (header reads {dict(votes)}); pages skipped")
            continue
        code = ranked[0][0]
        if code in owner:
            raise SystemExit(f"2020 report: precinct {code} assigned to pages {owner[code]} and {run}")
        owner[code] = run
        if len(ranked) > 1:
            problems.append(f"pages {run}: precinct {code} (header reads {dict(votes)})")
        for p in run:
            codes[p] = code
    return codes


def parse_reads(paths, want, known, name_code=lambda nm: None):
    """Combine OCR reads -> (accepted {(code, contest): rows}, failed {(code, contest): reason}, names,
    pages {(code, contest): page}, log)."""
    log = []
    raw = []
    for path in paths:
        plist = pages_of(Path(path))
        raw.append((Path(path).name, plist, [header_info(head, known) for _p, head, _l, _r in plist]))
    codes = page_codes([(pl, inf) for _f, pl, inf in raw], known, name_code, log)
    reads = []
    names = {}
    for fname, plist, info in raw:
        ok, bad, pages = {}, {}, {}
        for (pno, _head, left, right), (_c, nm, _k, _of) in zip(plist, info):
            code = codes.get(pno)
            if code is None:
                continue
            if nm and re.fullmatch(r"[A-Z][A-Z .]+", nm):
                names.setdefault(code, nm)
            for col in (left, right):
                for title, ttext, body in boxes(col):
                    contest = want(title)
                    if not contest:
                        continue
                    key = (code, contest)
                    res, why = parse_box(ttext, body)
                    if res is None:
                        bad.setdefault(key, f"page {pno}: {why}")
                    elif key in ok and [(p, v) for p, _n, v in ok[key]] != [(p, v) for p, _n, v in res]:
                        bad[key] = f"page {pno}: the race appears twice with different numbers"
                    else:
                        ok[key] = res
                        pages[key] = pno
        for key in list(ok):
            if key in bad and "appears twice" in bad[key]:
                del ok[key]
            else:
                bad.pop(key, None)
        reads.append((fname, ok, bad, pages))
    keys = set()
    for _f, ok, bad, _pg in reads:
        keys |= set(ok) | set(bad)
    accepted, failed, pages = {}, {}, {}
    for key in sorted(keys):
        vals = [(f, ok[key], pg[key]) for f, ok, _b, pg in reads if key in ok]
        if not vals:
            failed[key] = "; ".join(f"{f}: {bad.get(key, 'box not found')}" for f, _ok, bad, _pg in reads)
        elif any([(p, n) for p, _nm, n in v[1]] != [(p, n) for p, _nm, n in vals[0][1]] for v in vals):
            # names are OCR text and may differ in a letter between reads; parties and votes must be identical
            failed[key] = "OCR reads pass every check but disagree: " + "; ".join(f"{f}: {v}" for f, v, _p in vals)
        else:
            accepted[key] = vals[0][1]
            pages[key] = vals[0][2]
    return accepted, failed, names, pages, log
