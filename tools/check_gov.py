#!/usr/bin/env python
"""Validate the GOV-area CSVs in data/editions/st-joseph/.

Run:  python -P -E tools/check_gov.py

Checks: headers; unique ids; terms.office_id -> offices; offices.unit_id -> units;
appointed_boards.unit_id -> units; every row has status + source_ids and every
source id exists in sources_gov.csv; enum values; date formats; overlapping terms
for the same seat (single-seat offices strict; multi-seat offices by seat count;
rows with notes containing OVERLAP_OK are exempt; blank start is skipped; blank
end = current, using scheduled_end=... from notes when present);
2027+ starts must be unofficial; the South Bend mayors list has 33 entries.
"""
import csv, os, re, sys, datetime

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "editions", "st-joseph")
HEAD = {
 "units.csv": "unit_id,unit_type,name,parent_unit_ids,places_covered,website,status,source_ids,notes",
 "offices.csv": "office_id,unit_id,office_type,title,district,seats,elected,partisan,term_years,next_election,status,source_ids,notes",
 "terms.csv": "term_id,office_id,person,party,start,end,selected_by,first_selected_by,status,confidence,source_ids,notes",
 "appointed_boards.csv": "board_id,unit_id,name,what_it_decides,seats,appointing_authorities,levies_tax,status,source_ids,notes",
 "sources_gov.csv": "id,url,title,publisher,accessed,kind,notes",
 "gaps_gov.csv": "area,item,why_missing,how_to_fill",
}
STATUS = {"official","unofficial","computed","from_scan","secondary","single_source"}
KIND = {"primary","news","secondary","statute","dataset","derived"}
PARTY = {"", "D","R","L","I","G","NP","W","O"}
SEL = {"election","caucus","appointment","unknown"}
CONF = {"high","medium","low"}

errs, warns = [], []
def err(m): errs.append(m)

def load(name):
    p = os.path.join(D, name)
    with open(p, encoding="utf-8", newline="") as f:
        r = csv.reader(f)
        h = next(r)
        if ",".join(h) != HEAD[name]:
            err("%s: header mismatch: %s" % (name, ",".join(h)))
        rows = []
        for i, row in enumerate(r, 2):
            if len(row) != len(h):
                err("%s line %d: %d fields, expected %d" % (name, i, len(row), len(h))); continue
            rows.append(dict(zip(h, row)))
    return rows

data = {n: load(n) for n in HEAD}
units, offices, terms, boards, sources, gaps = (data[k] for k in ("units.csv","offices.csv","terms.csv","appointed_boards.csv","sources_gov.csv","gaps_gov.csv"))

def uniq(rows, key, name):
    seen = set()
    for r in rows:
        if r[key] in seen: err("%s: duplicate %s %s" % (name, key, r[key]))
        seen.add(r[key])
    return seen
unit_ids = uniq(units, "unit_id", "units")
office_ids = uniq(offices, "office_id", "offices")
uniq(terms, "term_id", "terms"); uniq(boards, "board_id", "appointed_boards"); src_ids = uniq(sources, "id", "sources")
# GOV rows may also cite sources registered in the edition's other source files (results, community, money, ...)
# and in the statewide registry, as the site build does; ids are checked for existence there, not re-validated.
gov_src_ids = set(src_ids)
_other = [os.path.join(D, n) for n in sorted(os.listdir(D)) if n.startswith("sources_") and n.endswith(".csv") and n != "sources_gov.csv"]
_ind = os.path.join(os.path.dirname(os.path.dirname(D)), "indiana")
_other += [os.path.join(_ind, n) for n in sorted(os.listdir(_ind)) if n.startswith("sources") and n.endswith(".csv")]
all_src_ids = set(src_ids)
for p in _other:
    with open(p, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("id"):
                all_src_ids.add(r["id"].strip())

used_src = set()
def chk_status_src(rows, name, key):
    for r in rows:
        if r["status"] not in STATUS: err("%s %s: bad status %r" % (name, r[key], r["status"]))
        if not r["source_ids"].strip(): err("%s %s: missing source_ids" % (name, r[key]))
        for s in r["source_ids"].split(";"):
            s = s.strip()
            if s and s not in all_src_ids: err("%s %s: unknown source id %s" % (name, r[key], s))
            used_src.add(s)
for rows, name, key in ((units,"units","unit_id"),(offices,"offices","office_id"),(terms,"terms","term_id"),(boards,"appointed_boards","board_id")):
    chk_status_src(rows, name, key)
for r in sources:
    if r["kind"] not in KIND: err("sources %s: bad kind %r" % (r["id"], r["kind"]))
    if not re.fullmatch(r"GOV-\d{3}", r["id"]): err("sources: bad id %s" % r["id"])
for s in src_ids - used_src:
    warns.append("source %s is not referenced by any row" % s)

for r in units:
    for p in [x for x in r["parent_unit_ids"].split(";") if x]:
        if p not in unit_ids: err("units %s: unknown parent %s" % (r["unit_id"], p))
for r in offices:
    if r["unit_id"] not in unit_ids: err("offices %s: unknown unit_id %s" % (r["office_id"], r["unit_id"]))
    if r["seats"] and not r["seats"].isdigit(): err("offices %s: seats %r" % (r["office_id"], r["seats"]))
for r in boards:
    if r["unit_id"] not in unit_ids: err("appointed_boards %s: unknown unit_id %s" % (r["board_id"], r["unit_id"]))

DATE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
def parse(s, default=None):
    if not s: return default
    p = [int(x) for x in s.split("-")]
    while len(p) < 3: p.append(1)
    return datetime.date(*p)

for r in terms:
    t = r["term_id"]
    if r["office_id"] not in office_ids: err("terms %s: unknown office_id %s" % (t, r["office_id"]))
    if r["party"] not in PARTY: err("terms %s: bad party %r" % (t, r["party"]))
    if r["selected_by"] not in SEL: err("terms %s: bad selected_by %r" % (t, r["selected_by"]))
    if r["first_selected_by"] not in SEL: err("terms %s: bad first_selected_by %r" % (t, r["first_selected_by"]))
    if r["confidence"] not in CONF: err("terms %s: bad confidence %r" % (t, r["confidence"]))
    if not r["person"].strip(): err("terms %s: blank person" % t)
    for f in ("start","end"):
        if r[f] and not DATE.match(r[f]): err("terms %s: bad %s %r" % (t, f, r[f]))
    if not r["start"] and "Wax" not in r["person"] and "Arnold" not in r["person"] and "Broden" not in r["person"] and "Canfield" not in r["person"]:
        warns.append("terms %s: blank start" % t)
    if r["start"] and r["start"] >= "2027" and r["status"] != "unofficial":
        err("terms %s: starts %s but status is %s (2026-result terms must be unofficial)" % (t, r["start"], r["status"]))
    if r["status"] == "unofficial" and "Unofficial" not in r["notes"] and "UNOFFICIAL" not in r["notes"]:
        err("terms %s: unofficial row without an 'as of' note" % t)
    if r["start"] and r["end"] and parse(r["end"]) < parse(r["start"]):
        err("terms %s: end before start" % t)

# overlaps
seats = {o["office_id"]: o["seats"] for o in offices}
by_office = {}
for r in terms:
    by_office.setdefault(r["office_id"], []).append(r)
FAR = datetime.date(9999, 1, 1)
for oid, rows in by_office.items():
    iv = []
    for r in rows:
        if not r["start"] or "OVERLAP_OK" in r["notes"]: continue
        s = parse(r["start"])
        if r["end"]: e = parse(r["end"])
        else:
            m = re.search(r"scheduled_end=(\d{4}(?:-\d{2}(?:-\d{2})?)?)", r["notes"])
            e = parse(m.group(1)) if m else FAR
        iv.append((s, e, r["term_id"]))
    sc = seats.get(oid, "")
    if not sc: continue          # unknown seat count: cannot test
    n = int(sc)
    for s, e, t in iv:
        # count intervals active at the start instant of this interval
        active = [x for x in iv if x[0] <= s < x[1]]
        if len(active) > n:
            err("overlap in %s at %s: %d terms for %d seat(s): %s" % (oid, s, len(active), n, ", ".join(a[2] for a in active)))
            break

mayors = [r for r in terms if r["office_id"] == "south-bend-mayor"]
if len(mayors) != 33: err("south-bend-mayor: %d rows, expected 33" % len(mayors))

for w in warns: print("WARN:", w)
for e in errs: print("ERROR:", e)
print("units=%d offices=%d terms=%d appointed_boards=%d sources=%d gaps=%d | errors=%d warnings=%d" %
      (len(units), len(offices), len(terms), len(boards), len(sources), len(gaps), len(errs), len(warns)))
sys.exit(1 if errs else 0)
