"""County-named PACs and party groups that file with the state, 2010-2026 (added 2026-11-09).

Nick, 2026-11-09, chose "State-filed local PACs" after the campaign-money gap audit
(research/cf-gap-audit-2026-11-09.md, gap 9), and "focus on filling in gaps since [2010]".

Writes data/editions/st-joseph/cf_state_pacs.csv: for every non-candidate committee in the Indiana Election Division
bulk files (sources/money/cf/{YEAR}_{Contribution,Expenditure}Data.csv.zip, 2010-2026) whose name places it in the
county (South Bend, Mishawaka, St. Joseph / Saint Joseph / St. Joe), one row per filing year with the same sums as
cf_state.csv (receipts = contribution rows, expenditures = expenditure rows), plus the committee's five largest payees
over 2010-2026 summed by name as listed. A committee is one state file number (names are spelled several ways).
County-filed committees (cf_local.csv), for example the St. Joseph County Firefighters PAC, are separate filers.

Run:  python -P -E tools/build_cf_state_pacs.py
"""
from __future__ import annotations

import collections
import csv
import io
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "sources" / "money" / "cf"
OUT = ROOT / "data" / "editions" / "st-joseph" / "cf_state_pacs.csv"
YEARS = range(2010, 2027)
PLACE = re.compile(r"(?i)south bend|mishawaka|st\.? ?joseph|saint joseph|st\.? joe\b")
SOURCE_IDS = "MON-079;MON-080;MON-020"


def money(x: float) -> str:
    x = round(x, 2)
    return str(int(round(x))) if abs(x - round(x)) < 0.005 else "%.2f" % x


def main() -> int:
    years = collections.defaultdict(lambda: {"C": 0.0, "E": 0.0, "nC": 0, "nE": 0, "amended": 0})
    names = collections.defaultdict(collections.Counter)
    ctype = {}
    payees = collections.defaultdict(collections.Counter)
    for y in YEARS:
        for kind in ("Contribution", "Expenditure"):
            z = zipfile.ZipFile(SRC / f"{y}_{kind}Data.csv.zip")
            for r in csv.DictReader(io.StringIO(z.read(z.namelist()[0]).decode("latin1"))):
                com = (r.get("Committee") or "").strip()
                if r.get("CommitteeType") == "Candidate" or not PLACE.search(com):
                    continue
                fn = (r.get("FileNumber") or "").strip() or com
                ctype[fn] = r.get("CommitteeType") or ""
                names[fn][com] += 1
                amt = float(r.get("Amount") or 0)
                d = years[(fn, y)]
                if kind == "Contribution":
                    d["C"] += amt
                    d["nC"] += 1
                else:
                    d["E"] += amt
                    d["nE"] += 1
                    payee = re.sub(r"\s+", " ", (r.get("Name") or "").strip()) or "(no payee name)"
                    payees[fn][payee] += amt
                if r.get("Amended") == "1":
                    d["amended"] += 1
    rows = []
    for (fn, y), d in sorted(years.items(), key=lambda kv: (names[kv[0][0]].most_common(1)[0][0].casefold(), kv[0][1])):
        if d["C"] == 0 and d["E"] == 0:
            continue
        top = "; ".join(f"{k} {money(v)}" for k, v in payees[fn].most_common(5) if v > 0)
        notes = (f"Filing-year basis: totals of items on reports filed in calendar {y}. Receipts = sum of contribution "
                 f"rows ({d['nC']} rows), expenditures = sum of expenditure rows ({d['nE']} rows). State committee file "
                 f"number {fn}. Cash on hand is not in the bulk data.")
        if d["amended"]:
            notes += f" Includes {d['amended']} rows flagged Amended (a few may repeat an original row)."
        if y == 2026:
            notes += " 2026 is partial: data extracted 2026-11-07."
        rows.append([names[fn].most_common(1)[0][0], fn, ctype[fn], y, money(d["C"]), money(d["E"]), top, "computed",
                     SOURCE_IDS, notes])
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["committee", "file_number", "committee_type", "year", "receipts", "expenditures",
                    "top_payees_2010_2026", "status", "source_ids", "notes"])
        w.writerows(rows)
    print(f"wrote {OUT.name}: {len(rows)} rows, {len({r[1] for r in rows})} committees")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
