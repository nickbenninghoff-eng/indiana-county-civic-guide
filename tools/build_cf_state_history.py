"""State-legislative campaign money before the guide's cf_state.csv years, and for past legislators (added 2026-11-09).

Nick, 2026-11-09: "the campaign finance history of every candidate, race, office, etc in St. Joseph county election
history for what we can find"; chose "State files 2000-2015".

cf_state.csv (tools/build_money.py, which this script does not touch or run) covers 13 committees, filing years
2016-2026. This script writes data/editions/st-joseph/cf_state_history.csv: the same filing-year sums (receipts = sum
of contribution rows, expenditures = sum of expenditure rows, from the Indiana Election Division bulk files
sources/money/cf/{YEAR}_{Contribution,Expenditure}Data.csv.zip, 2000-2026) for

* every state House or Senate candidate in the guide's results (results.csv, 2010-2026 ballots), matched by the
  filer's CandidateName (civic.campaign_money.same_person) on a Candidate committee whose name says it is for a state
  legislative office (State Rep..., Representative, Senate, Senator, House) - the bulk files have no office field for
  the committee itself (OfficeSought on expenditure rows is the payee's office); a committee whose name doesn't say
  the office is kept when it filed from two years before to one year after one of the person's ballot years (and the
  row's notes say so), which rules out a namesake's unrelated committee;
* every filing year of those committees except the (committee, year) pairs already in cf_state.csv.

Districts: each row keeps the chamber and district number(s) the candidate appeared under on the guide's ballots.
Lines were redrawn in 2011 and 2021, so a year's money is never shown under a district on the map; the state page
lists these rows by person.

Not covered: legislators who left office before 2010 (the guide's results start in 2010), and opponents whose
committees use no state-office word in their name (listed in the run log for review).

Run:  python -P -E tools/build_cf_state_history.py
"""
from __future__ import annotations

import collections
import csv
import io
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "site"))
from civic.campaign_money import same_person  # noqa: E402

SRC = ROOT / "sources" / "money" / "cf"
ED = ROOT / "data" / "editions" / "st-joseph"
YEARS = range(2000, 2027)
OFFICE_WORDS = re.compile(r"(?i)\b(state\s*rep|representative|senate|senator|house|legislat)")
SOURCE_IDS = "MON-079;MON-080;MON-020"


# ballot nicknames -> the legal given name filers use (this script only; civic.campaign_money is not changed)
NICK = {"jim": "james", "bill": "william", "bob": "robert", "joe": "joseph", "dave": "david", "mike": "michael",
        "tim": "timothy", "pat": "patrick", "dan": "daniel", "tom": "thomas", "ed": "edward", "ron": "ronald",
        "rick": "richard", "chuck": "charles", "charlie": "charles", "steve": "stephen", "andy": "andrew",
        "greg": "gregory", "ken": "kenneth", "jeff": "jeffrey", "matt": "matthew", "chris": "christopher"}


def legal(name: str) -> str:
    return " ".join(NICK.get(w.lower().strip(".,"), w) for w in name.split())


def money(x: float) -> str:
    x = round(x, 2)
    return str(int(round(x))) if abs(x - round(x)) < 0.005 else "%.2f" % x


def people() -> list[dict]:
    out: list[dict] = []
    with open(ED / "results.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            m = re.search(r"State (Senator|Representative),? District (\d+)", r["contest_label"])
            if not m or not r["candidate"] or r["candidate"].upper() in ("YES", "NO"):
                continue
            ch = "SD" if m.group(1) == "Senator" else "HD"
            dist, year = f"{ch}{m.group(2)}", int(r["election_id"][:4])
            p = next((x for x in out if same_person(x["name"], r["candidate"])), None)
            if p is None:
                p = {"name": r["candidate"], "names": set(), "party": collections.Counter(), "dists": collections.Counter(),
                     "years": set()}
                out.append(p)
            p["names"].add(r["candidate"])
            if legal(r["candidate"]) != r["candidate"]:
                p["names"].add(legal(r["candidate"]))
            if r["party"]:
                p["party"][r["party"]] += 1
            p["dists"][dist] += 1
            p["years"].add(year)
    for p in out:   # the fullest ballot spelling as the display name
        ballot = [n for n in p["names"] if n != legal(n) or n not in {legal(m) for m in p["names"] if m != n}]
        p["name"] = max(ballot or p["names"], key=lambda n: (len(n.split()), len(n)))
    return out


def main() -> int:
    ppl = people()
    have = set()
    with open(ED / "cf_state.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            have.add((r["committee"], int(r["year"])))
    agg: dict[tuple, dict] = {}
    review = collections.Counter()
    match: dict[str, dict | None] = {}
    spell: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for y in YEARS:
        for kind in ("Contribution", "Expenditure"):
            fn = SRC / f"{y}_{kind}Data.csv.zip"
            if not fn.exists():
                print("missing", fn.name)
                continue
            z = zipfile.ZipFile(fn)
            text = z.read(z.namelist()[0]).decode("latin1")
            for r in csv.DictReader(io.StringIO(text)):
                if r.get("CommitteeType") != "Candidate":
                    continue
                cand = (r.get("CandidateName") or "").strip()
                if not cand:
                    continue
                if cand not in match:   # one name test per distinct filer name (the files hold millions of rows)
                    match[cand] = next((x for x in ppl if same_person(x["name"], cand)
                                        or any(same_person(n, cand) for n in x["names"])), None)
                p = match[cand]
                if p is None:
                    continue
                # one committee = one state file number (its name is spelled several ways across years)
                com = (r.get("FileNumber") or "").strip() or (r.get("Committee") or "").strip()
                spell[com][(r.get("Committee") or "").strip()] += 1
                d = agg.setdefault((p["name"], com, y), {"C": 0.0, "E": 0.0, "nC": 0, "nE": 0, "amended": 0,
                                                         "types": collections.defaultdict(float), "filer": cand})
                amt = float(r.get("Amount") or 0)
                if kind == "Contribution":
                    d["C"] += amt
                    d["nC"] += 1
                    d["types"][(r.get("ContributorType") or "").strip() or "Unitemized (no contributor type)"] += amt
                else:
                    d["E"] += amt
                    d["nE"] += 1
                if r.get("Amended") == "1":
                    d["amended"] += 1
    rows = []
    byname = {p["name"]: p for p in ppl}
    # a committee whose name doesn't say the office is kept only when it filed around one of the person's races
    # (from two years before to one year after a ballot year), which rules out a namesake's unrelated committee
    years_of = collections.defaultdict(set)
    for (name, com, y) in agg:
        years_of[(name, com)].add(y)
    named = {k: spell[k].most_common(1)[0][0] for k in spell}
    named_by_office = {k for k in years_of if any(OFFICE_WORDS.search(n) for n in spell[k[1]])}
    near_race = {k for k, ys in years_of.items() if k not in named_by_office
                 and any(b - 2 <= y <= b + 1 for y in ys for b in byname[k[0]]["years"])}
    for k, ys in years_of.items():
        if k not in named_by_office and k not in near_race:
            review[(k[0], named[k[1]], f"{min(ys)}-{max(ys)}")] += 1
    agg = {k: v for k, v in agg.items() if (k[0], k[1]) in named_by_office | near_race}
    for (name, fileno, y), d in sorted(agg.items(), key=lambda kv: (kv[0][0], kv[0][2], named[kv[0][1]].casefold())):
        com = named[fileno]
        if d["C"] == 0 and d["E"] == 0:
            continue
        # already in cf_state.csv under any spelling of this committee's name
        if any(c.casefold() == n.casefold() and yy == y for n in spell[fileno] for c, yy in have):
            continue
        p = byname[name]
        party = p["party"].most_common(1)[0][0] if p["party"] else ""
        dists = "; ".join(f"{k} ({', '.join(str(x) for x in sorted({yy for yy in p['years']}))})" if len(p["dists"]) == 1
                          else k for k, _n in p["dists"].most_common())
        top = "; ".join(f"{k} {money(v)}" for k, v in sorted(d["types"].items(), key=lambda kv: -kv[1])[:3])
        notes = (f"Filing-year basis: totals of items on reports filed in calendar {y}, not an election-cycle total. "
                 f"Receipts = sum of contribution rows ({d['nC']} rows), expenditures = sum of expenditure rows "
                 f"({d['nE']} rows). State committee file number {fileno}. Cash on hand is not in the bulk data. Filer named {d['filer']!r}; matched to the "
                 f"guide's ballot name by name. Ballot districts are those of the guide's 2010-2026 results; lines were "
                 f"redrawn in 2011 and 2021.")
        if (name, fileno) in near_race:
            notes += (" The committee's name doesn't say the office; it is included because its filer's name matches "
                      "and it filed around the candidate's race(s).")
        if d["amended"]:
            notes += f" Includes {d['amended']} rows flagged Amended (a few may repeat an original row)."
        if y == 2026:
            notes += " 2026 is partial: data extracted 2026-11-07."
        rows.append([com, name, "; ".join(sorted({"State Senator" if k.startswith("SD") else "State Representative"
                                                  for k in p["dists"]})),
                     dists, party, y, money(d["C"]), money(d["E"]), "", top, "computed", SOURCE_IDS, notes])
    with open(ED / "cf_state_history.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["committee", "candidate", "office", "ballot_districts", "party", "year", "receipts", "expenditures",
                    "cash_end", "top_funder_types", "status", "source_ids", "notes"])
        w.writerows(rows)
    found = sorted({r[1] for r in rows})
    print(f"wrote cf_state_history.csv: {len(rows)} rows, {len(found)} people, "
          f"years {min((r[5] for r in rows), default='-')}-{max((r[5] for r in rows), default='-')}")
    print("no state-legislative committee found for:", ", ".join(sorted(p["name"] for p in ppl if p["name"] not in found
                                                                       and not any(c[1] == p["name"] for c in []))))
    print("left out (no state-office word and no filing near the person's races):")
    for (name, com, yrs), n in sorted(review.items()):
        print(f"  {name} | {com} | filing years {yrs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
