"""Campaign money in local races (money/campaigns/index.html).

Built from the local campaign-finance transcriptions:

    data/editions/<ed>/cf_local.csv               one row per CFA-4 filing (summary sheet read by eye)
    data/editions/<ed>/cf_large_contributions.csv  CFA-11 large-contribution entries
    data/editions/<ed>/cf_coverage.csv            office x cycle coverage (used here as a cross-check)
    research/cf/_committee_keys.csv               filing -> committee identity (written by tools/build_cf_local.py)

Neutrality rules specific to this page (ux-review 6, page brief):
* default order is office, then district, then committee name; never party, never amount;
  readers may choose a column sort in the explorer;
* no rankings or "top" lists, no amounts in headings, no party colour anywhere on the page;
* the coverage matrix comes before any figure, so readers see how complete the record is first;
* sums of several reports are the guide's arithmetic and carry the COMPUTED badge;
* contributor names only (as filed): never addresses, phones or e-mails.

The all-filings table is rendered here, once per filing; static/js/campaigns.js filters and sorts its rows and
derives the per-committee list from them. Without JavaScript the page still shows the method, the coverage matrix, the race tables and
the large-contribution table (all rendered here).
"""
from __future__ import annotations

import csv
import re
from collections import Counter, OrderedDict, defaultdict
from datetime import date, timedelta

from civic.components import (RECORDS_MARK, callout, data_table, see_all_fold, name_with_form_party, party_label, scope_badge, section,
                              status_badge, term_party)
from civic.campaign_money import ALL_PAGE, HOW_PAGE, INDEX_PAGE, cycle_of, given as _given, surname as _surname
from civic.data import fmt_date, parse_date, split_ids
from civic.html import Markup, h, join, json_script

PAGE = HOW_PAGE
TITLE = "Campaign money in local races"

# Method sources (data/editions/<ed>/sources_cf_method.csv) and other ids used in prose.
SRC_FILINGS_PAGE = "SVC-019"      # county Candidate Filings page
SRC_INVENTORY = "SVC-020"         # research inventory of what the county posted
SRC_ADJ = "CFM-001"               # research/cf/adjudication.md
SRC_COVERAGE = "CFM-002"          # research/cf/coverage-notes.md
SRC_FORM = "CFM-003"              # research/cf/CF-VISUAL-BRIEF.md (CFA-4 layout)
SRC_STATE_BULK = "MON-020"        # Indiana Election Division bulk data (state committees)
SAMPLE_FORM = "CFL-60818"         # a typed CFA-4 summary sheet, for the form description
CFA11_FORM = "CFL-73114"          # a CFA-11 notice whose header text is quoted in the data
DOC_DELINQUENT = "CFL-66024"
DOC_REPULL = "CFL-70515"
DOC_UNREADABLE = "CFL-65627"
DOC_PERIOD = "CFL-66082"

# Double-entry facts from research/cf/adjudication.md (CFM-001) and research/cf/double-entry-diff.csv.
SAMPLE_DOCS = 152
SAMPLE_CELL_CONFLICT_DOCS = 17
SAMPLE_STATUS_DISAGREEMENTS = 28
SPOT_CHECK = (10, 10)

# Must mirror tools/build_cf_local.py (EXPECTED, cycle_of): the coverage matrix is cross-checked
# against cf_coverage.csv and any mismatch is reported as a build warning.
EXPECTED = {"2023 municipal": ["Annual"], "2024": ["Pre-Primary", "Pre-Election", "Annual"],
            "2026": ["Annual", "Pre-Primary", "Pre-Election"]}
CYCLES = [("2023 municipal", "2023"), ("2024", "2024"), ("2026", "2025-26"), ("period unknown", "Period not on form")]
CYCLE_LONG = {"2023 municipal": "2023 (city and town election year)",
              "2024": "2024 (county, township and school election year)",
              "2026": "2025 and 2026 (2026 election cycle)",
              "period unknown": "Period not written on the form"}
TYPE_LABEL = {("2026", "Annual"): "2025 Annual"}

GROUPS = [("county", "County offices"), ("courts", "Courts"), ("south-bend", "City of South Bend"),
          ("mishawaka", "City of Mishawaka"), ("towns", "Towns"), ("townships", "Townships"),
          ("schools", "School boards"), ("noncand", "Party, PAC and issue committees"),
          ("none", "Office not stated on the form")]
GROUP_INDEX = {g: i for i, (g, _) in enumerate(GROUPS)}
NO_OFFICE = "(no office stated on form)"

STATUS_CF = OrderedDict([
    ("verified", ("VERIFIED", "Every check of the form's own arithmetic holds as written; nothing had to be filled in.")),
    ("derived", ("DERIVED", "A cell was blank, illegible or clipped on the form, and the form's own arithmetic fixes its value. "
                            "The note names the cell.")),
    ("filer-inconsistent", ("FILER-INCONSISTENT", "The form's own numbers don't add up. Figures are shown exactly as filed, "
                                                  "with a note on what doesn't match.")),
    ("unreadable", ("UNREADABLE", "The scan is too degraded to read. No figures are shown.")),
])

# --------------------------------------------------------------------------- helpers

def _num(v: str):
    v = (v or "").strip()
    if not v:
        return None
    try:
        return round(float(v), 2)
    except ValueError:
        return None


def money(v) -> str:
    if v is None:
        return "blank on form"
    sign = "-" if v < 0 else ""
    return f"{sign}${abs(v):,.2f}"


def _natural(s: str) -> tuple:
    s = (s or "").replace(" (", " ~(")  # "(district not stated)" sorts after the numbered districts
    return tuple(int(t) if t.isdigit() else t.casefold() for t in re.split(r"(\d+)", s) if t)


def _types(row: dict) -> set[str]:
    """Report types a filing counts as for coverage (Final counts as Annual, as in the builder)."""
    return {"Annual" if t == "Final" else t for t in (row["report_type"] or "not marked").split("; ")}


def period_text(row: dict) -> str:
    f, t = row.get("period_from", ""), row.get("period_to", "")
    if not f and not t:
        return "Period not written on the form"
    return f"{fmt_date(f) if f else 'start not written'} to {fmt_date(t) if t else 'end not written'}"


def _clean_note(note: str) -> str:
    n = (note or "").split("First-reading notes:")[0].strip()
    n = n.replace("Second reading differed; see research/cf/adjudication.md.",
                  "A second reading differed; the difference was settled against the page image.")
    n = re.sub(r"Blank lines read as none: [^.]*\.\s*", "", n)
    n = n.replace("Owner check: ", "").replace("office_normalized: ", "Office: ")
    n = re.sub(r"\bl(\d{2}[a-c]?[AB]?)\b", r"line \1", n)
    return re.sub(r"\s+", " ", n).strip()


def cf_badge(status: str, page=None) -> Markup:
    label, definition = STATUS_CF.get(status, (status.upper() or "NOT RECORDED", "Transcription status not recorded."))
    inner = h("span", {"class": f"badge badge-cf badge-cf-{status or 'none'}", "title": definition}, label)
    if page is None:
        return inner
    return h("a", {"class": "badge-link", "href": page.rel(HOW_PAGE + "#method"), "aria-label": f"{label}: {definition}"},
             inner)


# --------------------------------------------------------------------------- model

def cf_badge_short(status: str, page) -> Markup:
    """cf_badge for long tables (area pages): the badge text links to the definitions on How it works, without
    repeating each definition in every row."""
    label = STATUS_CF.get(status, (status.upper() or "NOT RECORDED", ""))[0]
    return h("a", {"class": "badge-link", "href": page.rel(HOW_PAGE + "#method")},
             h("span", {"class": f"badge badge-cf badge-cf-{status or 'none'}"}, label))


def _group_of(row: dict, ed) -> str:
    off, uid = row["office_normalized"], row["unit_id"]
    if off.startswith("Non-candidate"):
        return "noncand"
    if not off or off.startswith("No office sought"):
        return "none"
    if off.startswith("Town Clerk-Treasurer"):
        return "towns"
    ut = ed.units.get(uid, {}).get("unit_type", "")
    g = {"county": "county", "court_system": "courts", "town": "towns", "township": "townships",
         "school_corporation": "schools"}.get(ut)
    if ut == "city":
        g = uid if uid in GROUP_INDEX else None
    if g is None:
        ed.warnings.append(f"campaigns: no office group for {row['filing_id']} ({off!r}, unit {uid!r})")
        return "none"
    return g


def _office_label(row: dict) -> str:
    off = row["office_normalized"]
    if not off:
        return "No office written on the form"
    if off.startswith("Non-candidate"):
        return "Non-candidate committee (party, PAC or issue)"
    return off


def _committee_keys(ed) -> dict[str, str]:
    path = ed.root / "research" / "cf" / "_committee_keys.csv"
    keys = {}
    if path.is_file():
        with open(path, encoding="utf-8-sig", newline="") as fh:
            keys = {r["filing_id"]: r["committee_key"] for r in csv.DictReader(fh)}
    else:
        ed.warnings.append("campaigns: research/cf/_committee_keys.csv missing; committees grouped by name as filed")
    return keys


def _doc_url(ed, row: dict) -> str:
    for sid in split_ids(row.get("source_ids")):
        s = ed.sources.get(sid)
        if s and s.get("url", "").startswith("http"):
            return s["url"]
    return ""


def build_model(ed) -> dict:
    # work on copies: the edition caches tables, and the data page publishes cf_local.csv as filed
    rows = [dict(r) for r in ed.table("cf_local")]
    keys = _committee_keys(ed)
    for r in rows:
        r["_key"] = keys.get(r["filing_id"]) or "cmte-" + re.sub(r"[^a-z0-9]+", "-", r["committee"].lower()).strip("-")
    # The builder keys committees by candidate, so one candidate's separately named committees for different
    # offices share a key (e.g. a sheriff committee and a later commissioner committee). Keep those apart:
    # split a key by committee name when its filings carry more than one name AND more than one office.
    # (Spelling variants of one committee for one office stay together.)
    norm = lambda n: re.sub(r"[^a-z0-9]", "", (n or "").lower())
    grouped = defaultdict(list)
    for r in rows:
        grouped[r["_key"]].append(r)
    for k, rs in grouped.items():
        if len({norm(r["committee"]) for r in rs}) > 1 and len({r["office_normalized"] for r in rs}) > 1:
            for r in rs:
                r["_key"] = f"{k}~{norm(r['committee'])}"
    for r in rows:
        r["_cycle"] = cycle_of(r)
        r["_group"] = _group_of(r, ed)
        r["_office"] = _office_label(r)
        for f in ("receipts_period", "expenditures_period", "cash_start_period", "cash_end_period"):
            r["_" + f] = _num(r[f])
    # a stable display label per committee: the name it used most often, then its latest
    by_key = defaultdict(list)
    for r in rows:
        by_key[r["_key"]].append(r)
    labels = {}
    for k, rs in by_key.items():
        names = Counter(r["committee"] for r in rs)
        latest = max(rs, key=lambda r: r["period_to"] or "")["committee"]
        top = max(names.values())
        labels[k] = latest if names[latest] == top else sorted(n for n, c in names.items() if c == top)[0]
    for r in rows:
        r["_label"] = labels[r["_key"]]

    def order(r):
        return (GROUP_INDEX[r["_group"]], _natural(r["_office"]), r["_label"].casefold(), r["_key"],
                r["period_to"] or "9999", r["filing_id"])
    rows_sorted = sorted(rows, key=order)
    return {"rows": rows_sorted, "by_key": by_key, "labels": labels,
            "coverage": _coverage(ed, rows), "totals": _totals(rows), "races": _races(ed, rows),
            "large": _large(ed, rows)}


# --------------------------------------------------------------------------- coverage

def _coverage(ed, rows) -> dict:
    cells = defaultdict(list)
    for r in rows:
        cells[(r["office_normalized"] or NO_OFFICE, r["unit_id"], r["_cycle"])].append(r)
    offices = {}
    for (off, uid, cyc), rs in cells.items():
        o = offices.setdefault((off, uid), {"office": off, "unit": uid, "group": rs[0]["_group"],
                                            "label": rs[0]["_office"] if off != NO_OFFICE else "No office written on the form",
                                            "cycles": {}})
        comms = defaultdict(set)
        unread = defaultdict(set)
        for r in rs:
            for t in _types(r):
                comms[r["_key"]].add(t)
                if r["transcription_status"] == "unreadable":
                    unread[t].add(r["_key"])
        exp = EXPECTED.get(cyc, [])
        o["cycles"][cyc] = {
            "committees": len(comms), "filings": len(rs),
            "types": {t: sum(1 for ts in comms.values() if t in ts) for t in exp},
            "unreadable": {t: len(v) for t, v in unread.items()},
            "full": sum(1 for ts in comms.values() if exp and all(e in ts for e in exp)),
            "keys": set(comms)}
    # cross-check against the published coverage file
    published = {(c["office_normalized"], c["unit_id"], c["cycle"]): c for c in ed.table("cf_coverage")}
    for (off, uid), o in offices.items():
        for cyc, c in o["cycles"].items():
            p = published.get((off, uid, cyc))
            if p is None:
                ed.warnings.append(f"campaigns: coverage cell {off} / {cyc} not in cf_coverage.csv")
                continue
            want = (int(p["committees"]), int(p["filings"]), int(p["committees_with_all_expected"] or 0))
            got = (c["committees"], c["filings"], c["full"] if EXPECTED.get(cyc) else 0)
            if want != got:
                ed.warnings.append(f"campaigns: coverage {off} / {cyc}: page {got} vs cf_coverage {want}")
    if len(published) != sum(len(o["cycles"]) for o in offices.values()):
        ed.warnings.append("campaigns: cf_coverage.csv row count differs from the page's coverage cells")
    ordered = sorted(offices.values(), key=lambda o: (GROUP_INDEX[o["group"]], _natural(o["label"]), o["unit"]))
    # cycle totals add up the office cells (as cf_coverage.csv and the coverage notes do), so a committee that
    # filed under two offices in one cycle counts once under each
    summary = {}
    for cyc, _ in CYCLES:
        cs = [o["cycles"][cyc] for o in offices.values() if cyc in o["cycles"]]
        summary[cyc] = {"committees": sum(x["committees"] for x in cs), "filings": sum(x["filings"] for x in cs),
                        "full": sum(x["full"] for x in cs),
                        "unique": len({k for x in cs for k in x["keys"]})}
    return {"offices": ordered, "summary": summary}


# --------------------------------------------------------------------------- per-committee totals

def _totals(rows) -> dict:
    """Committee x cycle sums of the 'this period' columns, only when the reports' periods run
    back to back (no gap, no overlap) and every report reconciles (verified or derived)."""
    out = {}
    groups = defaultdict(list)
    for r in rows:
        if r["_cycle"] != "period unknown":
            groups[(r["_key"], r["_cycle"])].append(r)
    for (k, cyc), rs in groups.items():
        rs = sorted(rs, key=lambda r: (r["period_to"], r["period_from"]))
        why = None
        if len(rs) == 1:
            why = "Only one report in this cycle, so there is nothing to add up."
        elif any(r["transcription_status"] not in ("verified", "derived") for r in rs):
            why = "At least one report doesn't reconcile or can't be read, so the guide doesn't add them up."
        elif any(not parse_date(r["period_from"]) or not parse_date(r["period_to"]) for r in rs):
            why = "At least one report has no complete period written on it, so the guide can't check that the periods fit together."
        elif any(r["_receipts_period"] is None or r["_expenditures_period"] is None for r in rs):
            why = "At least one report leaves the receipts or expenditures line blank."
        else:
            for a, b in zip(rs, rs[1:]):
                if parse_date(b["period_from"]) != parse_date(a["period_to"]) + timedelta(days=1):
                    why = ("The reports' periods leave a gap or overlap, so adding them up would miss or double-count "
                           "money. The reports are shown one by one instead.")
                    break
                if a["_cash_end_period"] is None or b["_cash_start_period"] is None or                         abs(a["_cash_end_period"] - b["_cash_start_period"]) > 0.005:
                    why = ("One report's opening cash doesn't match the closing cash on the report before it, so the "
                           "guide doesn't add them up.")
                    break
        if why:
            out[(k, cyc)] = {"why": why, "n": len(rs)}
        else:
            out[(k, cyc)] = {"n": len(rs), "from": rs[0]["period_from"], "to": rs[-1]["period_to"],
                             "r": round(sum(r["_receipts_period"] for r in rs), 2),
                             "e": round(sum(r["_expenditures_period"] for r in rs), 2),
                             "cash": rs[-1]["_cash_end_period"]}
    return out


# --------------------------------------------------------------------------- races

def _contest_offices(label: str) -> list[str]:
    m = re.match(r"^St\. Joseph County (Auditor|Sheriff|Assessor|Recorder|Treasurer|Coroner|Surveyor)$", label)
    if m:
        return [f"County {m.group(1)}"]
    if label == "St. Joseph County Prosecuting Attorney":
        return ["County Prosecutor"]
    if label == "St. Joseph County Clerk of the Circuit Court":
        return ["Clerk of the Circuit Court"]
    if label == "St. Joseph County Judge of the Probate Court":
        return ["Probate Court Judge"]
    m = re.match(r"^St\. Joseph County Commissioner, District (\d)$", label)
    if m:
        return [f"County Commissioner District {m.group(1)}", "County Commissioner (district not stated)"]
    m = re.match(r"^St\. Joseph County Council, District ([A-I])$", label)
    if m:
        return [f"County Council District {m.group(1)}", "County Council (district not stated)"]
    m = re.match(r"^(\w+) Township: Township (Trustee|Board|Assessor)$", label)
    if m:
        return [f"{m.group(1)} Township {m.group(2)}"]
    m = re.match(r"^Town of ([\w ]+): Town Council, (.+)$", label)
    if m:
        return [f"{m.group(1)} Town Council {m.group(2)}", f"{m.group(1)} Town Council"]
    m = re.match(r"^South Bend Community Schools: School Board, (?:District )?(\d|At-Large)$", label)
    if m:
        return [f"South Bend Community School Corporation Board {('District ' + m.group(1)) if m.group(1).isdigit() else 'At-Large'}"]
    m = re.match(r"^Penn-Harris-Madison schools: School Board, (\w+) Township$", label)
    if m:
        return [f"Penn-Harris-Madison School Board, {m.group(1)} Township seat", "Penn-Harris-Madison School Board (seat not stated)"]
    if label.startswith("School City of Mishawaka: School Board"):
        return ["School City of Mishawaka School Board"]
    return []


RACE_ELECTIONS = (("2024g", "2024"), ("2026g", "2026"))
SKIP_CONTEST = re.compile(r"-state-|straight-party|public-question|retention")


def _races(ed, rows) -> list[dict]:
    """Contested local general-election races of 2024 and 2026. For each ballot candidate, the
    comparable report is the committee's Pre-Election report in the same cycle."""
    out = []
    for eid, cyc in RACE_ELECTIONS:
        el = ed.elections.get(eid)
        prim = ed.elections.get(eid[:-1] + "p")
        if not el or not prim:
            ed.warnings.append(f"campaigns: election {eid} or its primary missing; race tables skipped")
            continue
        lo, hi = parse_date(prim["date"]), parse_date(el["date"])
        for c in ed.contests.values():
            if c["election_id"] != eid or SKIP_CONTEST.search(c["contest_id"]):
                continue
            cands = [r for r in c["rows"] if r["candidate"] not in ("YES", "NO")]
            if len(cands) < 2:
                continue
            offices = _contest_offices(c["label"])
            if not offices and not re.search(r"schools?: School Board", c["label"]):
                ed.warnings.append(f"campaigns: race {c['contest_id']} has no office mapping; left out of the race tables")
                continue
            # school corporations with no filings at all have no office mapping: every candidate shows as not posted
            pool = [r for r in rows if r["_cycle"] == cyc and r["office_normalized"] in offices]
            entries = []
            for cand in cands:
                sur, given = _surname(cand["candidate"]), _given(cand["candidate"])
                keys = sorted({r["_key"] for r in pool if _surname(r["candidate"]) == sur})
                if len(keys) > 1:
                    keys = sorted({r["_key"] for r in pool if _surname(r["candidate"]) == sur and _given(r["candidate"]) & given})
                e = {"name": cand["candidate"], "party": cand["party"], "state": "none", "row": None, "elsewhere": ""}
                if len(keys) > 1:
                    e["state"] = "ambiguous"
                    ed.warnings.append(f"campaigns: race {c['contest_id']}: {cand['candidate']} matches several committees {keys}")
                elif keys:
                    # the pre-election report for THIS general election: marked Pre-Election and closing between
                    # the primary and the general (some filers marked the box on a pre-primary or annual period)
                    pre = [r for r in pool if r["_key"] == keys[0] and r["report_type"] == "Pre-Election"
                           and parse_date(r["period_to"]) and lo < parse_date(r["period_to"]) <= hi]
                    e["committee"] = rows_label(pool, keys[0])
                    if len(pre) > 1:
                        e["state"] = "ambiguous"
                        ed.warnings.append(f"campaigns: race {c['contest_id']}: {cand['candidate']} has {len(pre)} pre-election reports")
                    elif pre:
                        e["row"] = pre[0]
                        e["state"] = "unreadable" if pre[0]["transcription_status"] == "unreadable" else "posted"
                    else:
                        e["state"] = "no-pre"
                else:
                    other = sorted({r["_office"] for r in rows if r["_cycle"] == cyc and _surname(r["candidate"]) == sur
                                    and _given(r["candidate"]) & given and r["office_normalized"] not in offices})
                    if other:
                        e["elsewhere"] = "; ".join(other)
                        ed.warnings.append(f"campaigns: race {c['contest_id']}: {cand['candidate']} only matches filings "
                                           f"under another office ({e['elsewhere']}); shown as not posted for this office")
                entries.append(e)
            posted = [e for e in entries if e["state"] == "posted"]
            periods = {(e["row"]["period_from"], e["row"]["period_to"]) for e in posted}
            complete = len(posted) == len(entries) and len(periods) == 1
            reason = ""
            if not complete:
                if len(posted) == len(entries):
                    reason = "The candidates' pre-election reports cover different periods."
                elif posted:
                    reason = "At least one candidate's pre-election report is not posted or can't be read."
                else:
                    reason = "No candidate's pre-election report is posted for this office."
            out.append({"contest": c, "election": el, "cycle": cyc, "entries": entries, "complete": complete,
                        "reason": reason, "period": next(iter(periods)) if complete else None,
                        "any_filing": any(e["state"] != "none" for e in entries)})
    out.sort(key=lambda x: (x["election"]["date"], _race_order(x["contest"])))
    return out


BALLOT_ORDER_LAW = "IND-056"   # IC 3-11-2-6


def _ballot_order_note(ed, page):
    """Why one party is listed first: Indiana orders party columns by each party's county vote for
    Secretary of State at the last election (IC 3-11-2-6(a)). The county figures come from the results data."""
    c = page.cites
    sos = []
    for ct in ed.contests.values():
        el = ed.elections.get(ct["election_id"])
        if el and ct["contest_id"].endswith("-state-secretary-of-state") and el["date"] < "2024-01-01":
            sos.append((el["date"], ct))
    if not sos:
        return None
    date_, ct = max(sos, key=lambda x: x[0])
    rows = sorted((r for r in ct["rows"] if r.get("party") in ("D", "R") and r.get("votes")),
                  key=lambda r: -float(r["votes"]))
    if len(rows) < 2:
        return None
    name = {"D": "Democrat (D)", "R": "Republican (R)"}
    first, second = rows[0], rows[1]
    return h("p", None, "Why one party comes first: Indiana law lists the parties on a county's ballot in order of the "
                        "votes their candidates for Secretary of State received in that county at the last election "
                        "(IC 3-11-2-6).", c.cite(BALLOT_ORDER_LAW), " In "
             f"{ed.county_label}, the {name[first['party']]} candidate received more votes in {date_[:4]} "
             f"({int(float(first['votes'])):,} to {int(float(second['votes'])):,}), so {name[first['party']]} candidates are "
             "listed first on the 2024 and 2026 ballots. The guide keeps that order.",
             c.cite(";".join(sorted({s for r in rows[:2] for s in split_ids(r.get("source_ids"))}))))


def rows_label(pool, key) -> str:
    names = [r["committee"] for r in pool if r["_key"] == key]
    return Counter(names).most_common(1)[0][0] if names else ""


def _race_order(c) -> tuple:
    cid = c["contest_id"]
    kind = 0 if "-county-" in cid else 1 if "township" in cid and "schools" not in cid else 2 if "council" in cid else 3
    return (kind, _natural(c["label"]))


# --------------------------------------------------------------------------- large contributions

_BOILER = re.compile(r"\s*(Committee taken from the candidate's CFA-4 filings[^.]*\.|Threshold confirmed from the form text:.*$)", re.S)


def _records_party(ed, name: str, cycle: str) -> str:
    """The party the guide's county election records give this person, for a form that leaves party blank.
    First the results rows of the same cycle's elections (primary or general), then officeholder terms. A name
    matches on surname plus a shared given name or nickname; more than one party found means no answer ('')."""
    sur, given = _surname(name), _given(name)
    if not sur:
        return ""

    def pick(codes):
        codes = {c for c in codes if c and c not in ("NP", "W")}
        return next(iter(codes)) if len(codes) == 1 else ""
    found = pick(r["party"].strip() for r in ed.table("results")
                 if r["election_id"].startswith(cycle) and _surname(r["candidate"]) == sur and _given(r["candidate"]) & given)
    if found:
        return found
    return pick(term_party(t) for t in ed.table("terms") if _surname(t["person"]) == sur and _given(t["person"]) & given)


def _form_party_text(ed, form_party: str, name: str, cycle: str) -> str:
    """Plain text of the same rule for the explorer's committee list: 'D', 'D, from election records' or
    'no party on the form'."""
    if (form_party or "").strip():
        return form_party
    rec = _records_party(ed, name, cycle)
    return f"{rec}, {RECORDS_MARK}" if rec else "no party on the form"


FORM_PARTY_NOTE = ("When a form leaves the candidate's party blank, the candidate's name shows the party from the county "
                   "election records in this guide (results or officeholder data), marked \"from election records\". With no "
                   "record, it says \"no party on the form\". The same rule applies to every candidate.")


def _large(ed, rows) -> list[dict]:
    by_committee = {}
    by_surname = defaultdict(set)
    for r in rows:
        by_committee.setdefault(r["committee"].casefold(), r)
        by_surname[_surname(r["candidate"])].add(r["_key"])
    out = []
    for e in ed.table("cf_large_contributions"):
        match = by_committee.get((e["committee"] or "").casefold())
        if match is None:
            sur = _surname(e["candidate"])
            cands = [r for r in rows if _surname(r["candidate"]) == sur and _given(r["candidate"]) & _given(e["candidate"])
                     and r["_cycle"] == "2026"]
            keys = {r["_key"] for r in cands}
            match = cands[0] if len(keys) == 1 else None
        note = _BOILER.sub("", e.get("notes", "")).strip()
        out.append({"e": e, "row": match, "note": note,
                    "order": (GROUP_INDEX[match["_group"]], _natural(match["_office"])) if match else (len(GROUPS), ()),
                    "office": match["_office"] if match else "Office not matched to a CFA-4 filing"})
    out.sort(key=lambda x: (x["order"], (x["e"]["committee"] or x["e"]["candidate"]).casefold(), x["e"]["date"], x["e"]["doc_id"]))
    return out


# --------------------------------------------------------------------------- page

def _delinquent_block(ed, page, c) -> list:
    """The county's undated 'Annual CFA 4 NOT Completed' list (doc 66024), names exactly as printed, in alphabetical
    order by the last word of each name, with any later report covering 2024 found among the posted filings."""
    rows = ed.table("cf_delinquent")
    if not rows:
        return [h("p", None, "The county posted a list of candidates whose 2024 annual reports were not completed; "
                             "the guide hasn't transcribed it.", c.cite(DOC_DELINQUENT))]

    def sort_key(r):
        parts = [p for p in r["name_as_printed"].replace(".", "").split() if p.lower() not in ("jr", "sr", "ii", "iii")]
        return (parts[-1].lower(), r["name_as_printed"].lower())

    table_rows = []
    for r in sorted(rows, key=sort_key):
        if r.get("later_filing_id"):
            later = [r["notes"], c.cite(r["source_ids"])]
        else:
            later = ["Not found among the posted filings the guide read."]
        table_rows.append([r["name_as_printed"], later])
    return [
        h("p", None, "The county posted a one-page typed list headed “Annual CFA 4 NOT Completed” under its "
                     "“2024 DELINQUENT ANNUAL CFA-4” tab. It names 18 people. The list has no date, and it doesn't say "
                     "whether any of them filed later.", c.cite(DOC_DELINQUENT)),
        h("p", None, "Names are shown exactly as the county typed them, including its spelling, sorted by last name. "
                     "For each, the guide looked for a later report covering 2024 among the county's posted filings. "
                     "Being on this list means a report was missing when the list was made. It is not a finding of "
                     "wrongdoing.", " ", status_badge("from_scan", page, "Names read from the county's posted list.")),
        data_table("cf-delinquent", ["Name as printed by the county", "Later report covering 2024 among posted filings"],
                   table_rows, label="2024 annual reports not completed (county list, undated)"),
    ]


def build_how(site):
    ed = site.ed
    page = site.page(HOW_PAGE, banners=False)
    c = page.cites
    model = cf_all(ed)["model"]
    rows = model["rows"]
    st = Counter(r["transcription_status"] for r in rows)
    de = Counter(r["double_entry"] for r in rows)
    n_docs = len({d for r in rows for d in split_ids(r["doc_ids"])})
    computed = lambda note: status_badge("computed", page, note)

    toc = [("obligations", "How reporting works"), ("public", "What's public"), ("method", "How the guide read the forms"),
           ("adding", "How the guide adds up a campaign"), ("coverage", "How complete the record is"),
           ("delinquent", "Delinquent filers"), ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(h("header", {"class": "page-hero"},
               h("p", {"class": "eyebrow mono"}, "Reference · Money · Campaign finance"),
               h("h1", None, page.title),
               h("p", {"class": "dek"},
                 "How local campaign committees report what they raise and spend, what the county posts, how the guide "
                 "read the scanned forms, and how it adds up a whole campaign.", c.cite(SRC_FILINGS_PAGE)),
               callout(h("p", None, h("strong", None, "Money is not a measure of support. "),
                         "These reports show what committees said they raised and spent. They don't show how many people "
                         "back a candidate, and the guide doesn't use them to predict results. The page never ranks "
                         "committees by money."), kind="note"),
               h("p", {"class": "hero-badges"}, scope_badge("county", ed), " ", scope_badge("indiana", ed),
                 h("span", {"class": "muted"}, " marks the parts that apply in every county."), " ",
                 status_badge("from_scan", page), h("span", {"class": "muted"}, " every figure was read from a scanned form.")),
               h("nav", {"class": "toc", "aria-label": "On this page"},
                 h("ol", None, [h("li", None, h("a", {"href": f"#{a}"}, t)) for a, t in toc]))))

    # ------------------------------------------------------------------ 1 obligations
    rt = Counter(r["report_type"] or "No report type marked" for r in rows)
    rt_rows = [[t, n] for t, n in sorted(rt.items(), key=lambda x: (_RT_ORDER.get(x[0], 9), x[0]))]
    lg = [r for r in ed.table("cf_large_contributions")]
    n_notices = len({e["doc_id"] for e in lg})
    page.add(section(
        "obligations", 1, "How campaign finance reporting works locally",
        h("h3", None, "Who files where"),
        h("p", None, "Committees for county, city, town, township and school-board candidates, and the county party "
                     "committees, have their reports posted by St. Joseph County on its Candidate Filings page.",
          c.cite(SRC_FILINGS_PAGE), " State legislators' committees file with the Indiana Election Division instead.",
          c.cite(SRC_STATE_BULK), " Their money is on ",
          h("a", {"href": page.rel("state/your-legislators/index.html#money")}, "Your legislators"), "."),
        h("p", None, "The county's page holds about 1,021 documents in 16 tabs. They include campaign-finance reports, "
                     "large-contribution notices and candidacy filings, all as scanned images.", c.cite(SRC_FILINGS_PAGE),
          " The earliest campaign-finance tab is the 2023 annual report. Nothing from 2022 or earlier is posted.",
          c.cite(SRC_INVENTORY), " Older reports would take a public records request; see Gaps."),
        h("h3", None, "The CFA-4 summary sheet"),
        h("p", None, scope_badge("indiana", ed), " Each report starts with a one-page summary on Indiana's CFA-4 form. "
                     "It has two columns: this period, and year to date.", c.cite(f"{SRC_FORM};{SAMPLE_FORM}")),
        h("ul", None,
          h("li", None, "Cash on hand at the start of the period (and on January 1)."),
          h("li", None, "Receipts: money taken in, itemized and not itemized, with a subtotal."),
          h("li", None, "Expenditures: money spent, itemized and not itemized, with a subtotal."),
          h("li", None, "Cash on hand at the close of the period, which should equal the start, plus receipts, minus expenditures."),
          h("li", None, "Debts owed by and to the committee.")),
        h("p", None, "The header names the committee, the candidate and party, the office sought, the report type and "
                     "the period, and says whether it amends an earlier report.", c.cite(SRC_FORM)),
        h("h3", None, "Report types"),
        h("p", None, "The form has boxes for Pre-Primary, Pre-Election, Annual, Supplemental and Other reports.",
          c.cite(SRC_FORM), " Some filings are marked Final or Outgoing Treasurer instead. This table counts the report "
                            "types marked on the filings the guide read.", c.cite(SRC_COVERAGE), " ",
          computed("Counts of cf_local.csv rows by the report-type box marked on the form.")),
        data_table("cf-report-types", ["Report type marked on the form", "Filings"], rt_rows,
                   caption="Report types in the filings read", numeric=(1,)),
        h("p", None, "The guide hasn't yet confirmed the due dates for each report type against state law or the "
                     "Election Division's guide. They are listed under Gaps."),
        h("h3", None, "Large contributions: the CFA-11 notice"),
        h("p", None, "A separate one-page notice reports single large contributions. Its header reads "
                     "“Supplemental Large Contribution Report by a Candidate's Committee ($1,000 contributions or "
                     "more)” and cites Indiana Code 3-9-5-20.1 and 3-9-5-22.", c.cite(CFA11_FORM),
          f" The county posted {n_notices} of these notices in 2026, with {len(lg)} contribution entries in all.",
          c.cite(SRC_COVERAGE), " ", computed("Counted from cf_large_contributions.csv.")),
        h("p", None, status_badge("unverified", page), " When a contribution has to be reported this way (how close "
                     "to an election) is not printed on the notice, and the guide hasn't confirmed it yet.",
          c.cite(CFA11_FORM)),
        ed=ed,
        lead="Local campaign committees report what they raise and spend on state forms. "
             "The county posts the scanned forms online."))

    # ------------------------------------------------------------------ 2 public
    page.add(section(
        "public", 2, "What's public and what isn't",
        h("ul", None,
          h("li", None, "The summary sheet gives totals: cash, receipts, expenditures and debts. The guide transcribed "
                        "only these summary sheets.", c.cite(SRC_FORM)),
          h("li", None, "Many posted reports also include schedule pages that list contributions and expenditures one by "
                        "one. The guide hasn't transcribed those, so it can't say who gave to a committee except through "
                        "the large-contribution notices.", c.cite(f"{SRC_INVENTORY};{SRC_FORM}")),
          h("li", None, "The forms carry addresses and other contact details. The guide never copies addresses, phone "
                        "numbers or e-mail addresses, only names, offices, parties and dollar figures.", c.cite(SRC_FORM)),
          h("li", None, "Reports made after the latest posted period aren't here yet. Most of the newest regular "
                        "reports end in October 2026, and the 2026 annual reports (through Dec 31, 2026) can't have been "
                        "filed yet.", c.cite(SRC_COVERAGE)),
          h("li", None, "A report the county didn't post can't be shown. The coverage matrix below shows where reports "
                        "are not posted.")),
        scope="county", ed=ed))

    # ------------------------------------------------------------------ 3 method
    status_rows = [[cf_badge(k, page), STATUS_CF[k][1], st.get(k, 0)] for k in STATUS_CF]
    page.add(section(
        "method", 3, "How the guide read these forms",
        h("div", {"class": "callout cf-method"},
          h("p", None, h("strong", None, "Read by eye, checked by arithmetic. "),
            f"The county posts scans, not data. Every figure on this page was read by eye from the scanned forms "
            f"({n_docs} summary-sheet documents, making {len(rows)} filings once duplicates and amendments are merged).",
            c.cite(f"{SRC_COVERAGE};{SRC_ADJ}"), " ", computed("Counts from cf_local.csv.")),
          h("p", None, "Every summary sheet was checked with the form's own arithmetic: receipts and expenditures must add "
                       "up to their subtotals, and the closing cash must equal the opening cash plus receipts minus "
                       "expenditures, in both columns.", c.cite(SRC_ADJ)),
          h("p", None, f"A sample of {SAMPLE_DOCS} documents was read a second time by a separate reader who didn't see "
                       f"the first reading. {SAMPLE_DOCS - SAMPLE_CELL_CONFLICT_DOCS} of {SAMPLE_DOCS} matched on every "
                       f"cell. In the other {SAMPLE_CELL_CONFLICT_DOCS}, and in {SAMPLE_STATUS_DISAGREEMENTS} documents "
                       "where the readers gave a different status, each disagreement was settled by looking at the page "
                       "image again.", c.cite(SRC_ADJ)),
          h("p", None, f"Another {SPOT_CHECK[1]} documents read only once were picked at random and compared with their "
                       f"images cell by cell; {SPOT_CHECK[0]} of {SPOT_CHECK[1]} matched.", c.cite(SRC_ADJ),
            f" In all, {de.get('single', 0)} filings rest on one reading, {de.get('agreed', 0)} on two readings that "
            f"agreed, and {de.get('adjudicated', 0)} on two readings settled against the image.", " ",
            computed("Counts of cf_local.csv rows by double_entry."))),
        h("h3", None, "What each status badge means"),
        data_table("cf-status-defs", ["Badge", "Meaning", "Filings"], status_rows,
                   caption="Transcription status of each filing", numeric=(2,)),
        h("p", None, "Every filing also carries ", status_badge("from_scan", page), " because it was typed in from an "
                     "image. Sums of several reports are the guide's own arithmetic and carry ",
          status_badge("computed", page), "."),
        h("p", {"class": "muted"}, "A FILER-INCONSISTENT badge means the form's own numbers don't add up. It says "
                                   "nothing about why, and the guide doesn't guess."),
        scope="county", ed=ed))

    # ------------------------------------------------------------------ 4 adding up
    page.add(section("adding", 4, "How the guide adds up a campaign", *_adding_block(ed, page, model), scope="county",
                     ed=ed, lead="The map and the area pages show what each candidate spent over a whole campaign. "
                                 "This is how those figures are put together."))

    # ------------------------------------------------------------------ 5 coverage
    page.add(section("coverage", 5, "How complete the record is", *_coverage_block(ed, page, model), scope="county", ed=ed,
                     lead="Before any figures: which reports the county has posted for each office, and which it hasn't."))

    # ------------------------------------------------------------------ 8 delinquent
    page.add(section(
        "delinquent", 6, "Delinquent filers",
        *_delinquent_block(ed, page, c),
        scope="county", ed=ed))

    # ------------------------------------------------------------------ related
    page.add(h("p", {"class": "cf-related"}, "Related: ",
               h("a", {"href": page.rel(INDEX_PAGE)}, "Campaign money by place"), " · ",
               h("a", {"href": page.rel(ALL_PAGE)}, "Every filing"), " · ",
               h("a", {"href": page.rel("money/budgets/index.html")}, "Budgets by unit"), " · ",
               h("a", {"href": page.rel("state/your-legislators/index.html#money")}, "State legislators' campaign money"), " · ",
               h("a", {"href": page.rel("run/index.html")}, "Run for office")))

    page.finish(gaps=_gaps(ed, page, model))
    return page


_RT_ORDER = {"Pre-Primary": 0, "Pre-Election": 1, "Annual": 2, "Final": 3, "Annual; Final": 4, "Pre-Primary; Annual": 5,
             "Outgoing Treasurer": 6, "Other": 7, "No report type marked": 8}


# --------------------------------------------------------------------------- blocks

def _coverage_block(ed, page, model) -> list:
    c = page.cites
    cov = model["coverage"]
    s = cov["summary"]
    sum_rows = []
    for cyc, short in CYCLES:
        if cyc == "period unknown":
            continue
        exp = EXPECTED[cyc]
        sum_rows.append([CYCLE_LONG[cyc], ", ".join(TYPE_LABEL.get((cyc, t), t) for t in exp),
                         s[cyc]["committees"], s[cyc]["filings"], s[cyc]["full"]])
    summary = data_table("cf-cycles", ["Cycle", "Reports the county posted for the cycle", "Committees with any report",
                                       "Filings", "Committees with every report"], sum_rows,
                         caption="Filings by election cycle", numeric=(2, 3, 4), min_width="40rem")
    dup = {cyc: s[cyc]["committees"] - s[cyc]["unique"] for cyc, _ in CYCLES if cyc != "period unknown"}
    cols = [(cyc, t) for cyc, _ in CYCLES if cyc != "period unknown" for t in EXPECTED[cyc]]
    head = ["Office"] + [f"{short}: {TYPE_LABEL.get((cyc, t), t)}" for cyc, short in CYCLES if cyc != "period unknown"
                         for t in EXPECTED[cyc]] + ["Period not on form"]
    trs = []
    last_group = None
    for o in cov["offices"]:
        if o["group"] != last_group:
            last_group = o["group"]
            trs.append(h("tr", {"class": "cf-group-row"},
                         h("th", {"scope": "colgroup", "colspan": len(head)}, dict(GROUPS)[o["group"]])))
        cells = [h("th", {"scope": "row"}, o["label"])]
        for cyc, t in cols:
            cc = o["cycles"].get(cyc)
            if not cc:
                cells.append(h("td", {"class": "cov cov-na"}, "–"))
                continue
            n, k = cc["committees"], cc["types"].get(t, 0)
            un = cc["unreadable"].get(t, 0)
            cls = "cov-all" if k == n else "cov-none" if k == 0 else "cov-some"
            missing = n - k
            sep = h("span", {"class": "visually-hidden"}, ", ")
            cells.append(h("td", {"class": f"cov {cls}"}, h("b", {"class": "cov-k"}, f"{k} of {n}"),
                           [sep, h("span", {"class": "cov-sub"}, f"{missing} not posted")] if missing else None,
                           [sep, h("span", {"class": "cov-sub"}, f"{un} unreadable")] if un else None))
        pu = o["cycles"].get("period unknown")
        cells.append(h("td", {"class": "cov cov-na" if not pu else "cov"}, f"{pu['filings']} filing{'s' if pu['filings'] != 1 else ''}" if pu else "–"))
        trs.append(h("tr", None, cells))
    thead = h("thead", None, h("tr", None, [h("th", {"scope": "col"}, x) for x in head]))
    table = h("div", {"class": "table-block"},
              h("div", {"class": "table-wrap", "role": "region", "tabindex": "0", "aria-label": "Coverage matrix"},
                h("table", {"class": "data cf-coverage", "id": "cf-coverage-table", "style": "min-width: 62rem"},
                  h("caption", None, "Reports posted, by office, cycle and report type"), thead, h("tbody", None, trs))),
              h("div", {"class": "table-tools"},
                h("button", {"type": "button", "class": "btn btn-small", "data-copy-table": "cf-coverage-table",
                             "id": "cf-coverage-table-copy"}, "Copy CSV")))
    return [
        h("p", None, "Each cell counts committees for that office that filed anything in the cycle, and how many of them "
                     "have that report posted. “1 of 3” means three committees filed something for the office "
                     "that cycle, and only one of their reports of that type is on the county's page.",
          c.cite(SRC_COVERAGE), " ", status_badge("computed", page, "Counted from cf_local.csv; cross-checked against cf_coverage.csv.")),
        h("p", None, "“Not posted” means only that the county's page has no such report from that committee. The "
                     "guide doesn't know whether each committee had to file each report, so it doesn't call any of "
                     "them late or missing. A committee that filed nothing at all in a cycle can't be counted here."),
        h("ul", None,
          h("li", None, "Cycles follow the period written on each form. Annual or final reports that close in January "
                        "to March count toward the year before. The 2025 annual reports count in the 2026 cycle.",
            c.cite(SRC_COVERAGE)),
          h("li", None, "2023: the county posted only annual reports. There are no 2023 pre-primary or pre-election "
                        "reports on its page.", c.cite(f"{SRC_COVERAGE};{SRC_INVENTORY}")),
          h("li", None, "City offices weren't on the 2024 ballot, and they are next elected in 2027, so most city "
                        "committees have only annual reports in 2024 and 2025.", c.cite(SRC_COVERAGE)),
          h("li", None, "A final report is counted as the annual report for its year, as in the guide's coverage file.",
            c.cite(SRC_COVERAGE))),
        summary,
        h("p", {"class": "muted"}, "Committees are counted under each office they filed for. ",
          "; ".join(f"In {CYCLE_LONG[k].split(' (')[0]}, {v} committee{'s' if v != 1 else ''} filed under two offices"
                    for k, v in dup.items() if v) + "." if any(dup.values()) else "",
          " ", status_badge("computed", page, "Counted from cf_local.csv.")),
        table,
        h("p", {"class": "muted"}, "Offices are listed by government, then alphabetically, with districts in number "
                                   "order. A dash means no committee for that office filed anything posted in that cycle."),
    ]


def _filing_row(ed, page, r, ci, oi, gi, url_prefix) -> Markup:
    """One filing as a table row, rendered once in the HTML. campaigns.js reads its data-* attributes to filter and
    sort, and clones the row into the per-committee view; it never creates filings."""
    unread = r["transcription_status"] == "unreadable"
    attrs = {"data-ci": str(ci), "data-oi": str(oi), "data-gi": str(gi),
             "data-cy": str([x for x, _ in CYCLES].index(r["_cycle"])), "data-pt": r["period_to"] or None,
             "data-st": r["transcription_status"] or "none"}
    for k, f in (("rec", "_receipts_period"), ("exp", "_expenditures_period"), ("cash", "_cash_end_period")):
        attrs["data-" + k] = None if r[f] is None else f"{r[f]:.2f}"
    who = [x for x in (r["candidate"], party_label(r["party"]) if r["party"] else "No party written on the form") if x]
    note = _clean_note(r["notes"])
    url = _doc_url(ed, r)
    doc = f"doc {r['doc_ids'].replace(';', ', ')}"
    return h("tr", attrs,
             h("th", {"scope": "row"},
               h("span", {"class": "cf-committee"}, r["committee"] or "Committee name not written"),
               h("span", {"class": "cf-sub"}, " · ".join(who)),
               h("span", {"class": "cf-sub cf-office-sub"}, r["_office"])),
             h("td", None, (r["report_type"] or "No report type marked") + (" (amended)" if r["amended"] == "yes" else "")),
             h("td", None, period_text(r)),
             [h("td", {"class": "num"}, "not readable" if unread else money(r[f]))
              for f in ("_receipts_period", "_expenditures_period", "_cash_end_period")],
             h("td", {"class": "cf-status"}, cf_badge_short(r["transcription_status"], page),
               h("details", {"class": "cf-note-details"}, h("summary", None, "Note"), h("p", {"class": "cf-note"}, note))
               if note else None),
             h("td", None, h("a", {"href": url, "target": "_blank", "rel": "noopener"}, doc) if url else doc))


def _explorer_block(ed, page, model) -> list:
    c = page.cites
    rows = model["rows"]
    labels = model["labels"]
    offices, office_ix = [], {}
    comms, comm_ix = [], {}
    trs = []
    vocab: dict[str, list] = {"why": []}

    def ix(kind, value):
        lst = vocab[kind]
        if value not in lst:
            lst.append(value)
        return lst.index(value)
    url_prefix = "https://www.sjcindiana.gov/DocumentCenter/View/"
    last = None
    for r in rows:
        if r["_office"] not in office_ix:
            office_ix[r["_office"]] = len(offices)
            offices.append(r["_office"])
        if r["_key"] not in comm_ix:
            comm_ix[r["_key"]] = len(comms)
            cand = Counter(x["candidate"] for x in model["by_key"][r["_key"]]).most_common(1)[0][0]
            pcode = Counter(x["party"] for x in model["by_key"][r["_key"]] if x["party"]).most_common(1)
            comms.append({"n": labels[r["_key"]], "c": cand,
                          "p": _form_party_text(ed, pcode[0][0] if pcode else "", cand, r["_cycle"]) if cand else ""})
        ci = comm_ix[r["_key"]]
        gi = GROUP_INDEX[r["_group"]]
        oi = office_ix[r["_office"]]
        if (gi, oi) != last:
            if gi != (last or (None,))[0]:
                trs.append(h("tr", {"class": "cf-group-row", "data-hk": f"g{gi}"},
                             h("th", {"scope": "colgroup", "colspan": "8"}, GROUPS[gi][1])))
            trs.append(h("tr", {"class": "cf-office-row", "data-hk": f"o{gi}-{oi}"},
                         h("th", {"scope": "colgroup", "colspan": "8"}, r["_office"])))
            last = (gi, oi)
        trs.append(_filing_row(ed, page, r, ci, oi, gi, url_prefix))
    totals = {}
    for (k, cyc), t in model["totals"].items():
        ci = comm_ix[k]
        rec = {"n": t["n"]}
        if "why" in t:
            rec["why"] = ix("why", t["why"])
        else:
            rec.update({"p": f"{fmt_date(t['from'])} to {fmt_date(t['to'])}", "r": t["r"], "e": t["e"], "cash": t["cash"]})
        totals.setdefault(str(ci), {})[str([x for x, _ in CYCLES].index(cyc))] = rec
    payload = {"groups": [g for _, g in GROUPS], "cycles": [CYCLE_LONG[x] for x, _ in CYCLES], "offices": offices,
               "committees": comms, "totals": totals, "whys": vocab["why"],
               "status": {k: [v[0], v[1]] for k, v in STATUS_CF.items()}}

    def field(fid, label, options):
        return h("div", {"class": "field"}, h("label", {"for": fid}, label),
                 h("select", {"id": fid}, [h("option", {"value": v}, t) for v, t in options]))
    controls = h("div", {"class": "picker cf-picker", "id": "cf-controls", "hidden": True},
                 field("cf-cycle", "Election cycle", [("", "All cycles")] + [(str(i), CYCLE_LONG[x]) for i, (x, _) in enumerate(CYCLES)]),
                 field("cf-group", "Office group", [("", "All offices")] + [(str(i), g) for i, (_, g) in enumerate(GROUPS)]),
                 field("cf-committee", "Committee", [("", "All committees")]),
                 field("cf-sort", "Order", [("office", "Office, district, committee (default)"),
                                            ("committee", "Committee name, A to Z"),
                                            ("date", "Period end date, oldest first"),
                                            ("receipts-desc", "Receipts this period, high to low"),
                                            ("receipts-asc", "Receipts this period, low to high"),
                                            ("spent-desc", "Expenditures this period, high to low"),
                                            ("spent-asc", "Expenditures this period, low to high"),
                                            ("cash-desc", "Cash on hand at close, high to low"),
                                            ("cash-asc", "Cash on hand at close, low to high")]),
                 h("p", {"class": "picker-help"}, "Sorting by an amount is your choice; the page never orders committees "
                                                  "by money on its own."))
    thead = h("thead", None, h("tr", None, [h("th", {"scope": "col", "class": "num" if i in (3, 4, 5) else None}, x) for i, x in enumerate(
        ["Committee", "Report", "Period", "Receipts this period", "Expenditures this period", "Cash on hand at close",
         "Status", "Form"])]))
    table = h("div", {"class": "table-block cf-explorer", "id": "cf-explorer-block"},
              h("div", {"class": "table-wrap", "role": "region", "tabindex": "0", "aria-label": "Filings explorer"},
                h("table", {"class": "data cf-table cf-grouped", "id": "cf-table", "style": "min-width: 60rem"},
                  h("caption", None, "Local campaign-finance filings"), thead, h("tbody", {"id": "cf-tbody"}, trs))),
              h("div", {"class": "table-tools"},
                h("button", {"type": "button", "class": "btn btn-small", "data-copy-table": "cf-table", "id": "cf-table-copy"},
                  "Copy CSV of the rows shown")))
    return [
        h("p", None, f"All {len(rows)} filings, filtered by cycle, office group or committee. Each row is one report: the "
                     "period it covers, receipts and expenditures during that period, and cash on hand at its close, "
                     "as written in the form's “this period” column.", c.cite(SRC_COVERAGE), " ",
          status_badge("from_scan", page), " The Form column links to the county's scan of each report."),
        h("p", None, "Party is shown as written on each form, as text. Party labels never set the order. " + FORM_PARTY_NOTE),
        controls,
        h("div", {"id": "cf-list-block", "hidden": True},
          h("p", {"class": "cf-count", "id": "cf-count", "aria-live": "polite"}),
          h("div", {"id": "cf-totals", "class": "cf-totals", "hidden": True}),
          h("p", {"class": "cf-sub"}, "One row per committee, in the order the filters and Order box give. Each row opens "
                                      "to that committee's reports."),
          h("div", {"id": "cf-list", "class": "cf-list"})),
        see_all_fold("cf-all-fold", len(rows), table, noun="filing", hint="Copy CSV",
                     label=f"See all {len(rows)} filings as one table"),
        json_script("cf-data", payload),
    ]


def _cell_money(v):
    return money(v)


def _races_block(ed, page, model, races=None) -> list:
    c = page.cites
    races = model["races"] if races is None else races
    complete = [r for r in races if r["complete"]]
    partial = [r for r in races if not r["complete"] and r["any_filing"]]
    empty = [r for r in races if not r["any_filing"]]
    out = [
        h("p", None, "Contested county, township, town and school-board races on the 2024 and 2026 general-election "
                     "ballots. For each race, the guide looks for every candidate's pre-election report: the report "
                     "marked Pre-Election whose period ends between the primary and the general election. Figures are "
                     "put side by side only when every candidate's report is posted and all of them cover exactly the "
                     "same period.", c.cite(SRC_COVERAGE)),
        h("p", None, "Candidates are listed in ballot order. Election results are on the ",
          h("a", {"href": page.rel("elections/results/index.html")}, "results page"),
          ", not here, because money reported before an election doesn't explain how people voted."),
        _ballot_order_note(ed, page),
    ]
    by_year = OrderedDict()
    for r in complete:
        by_year.setdefault(r["election"]["date"][:4], []).append(r)
    if not complete:
        out.append(h("p", None, "No race has every candidate's comparable report posted yet."))
    for year, rs in by_year.items():
        out.append(h("h3", None, f"{year} general election: pre-election reports"))
        for r in rs:
            pf, pt = r["period"]
            trs = []
            for e in r["entries"]:
                row = e["row"]
                trs.append([h("span", None, e["name"], h("span", {"class": "cf-sub"}, party_label(e["party"]))),
                            h("span", None, row["committee"], c.cite(row["source_ids"])),
                            money(row["_receipts_period"]), money(row["_expenditures_period"]), money(row["_cash_end_period"]),
                            h("span", {"class": "cf-badges"}, cf_badge(row["transcription_status"], page), " ",
                              status_badge("from_scan", page))])
            cid = r["contest"]["contest_id"]
            note = [e for e in r["entries"] if e["row"]["transcription_status"] == "filer-inconsistent"]
            out.append(h("div", {"class": "cf-race", "id": f"race-{cid}"},
                         h("h4", None, _race_title(r["contest"])),
                         h("p", {"class": "cf-race-meta mono"}, f"Pre-Election report, {fmt_date(pf)} to {fmt_date(pt)}"),
                         data_table(f"race-{cid}-table", ["Candidate (ballot order)", "Committee", "Receipts this period",
                                                          "Expenditures this period", "Cash on hand at close", "Status"],
                                    trs, caption=f"{_race_title(r['contest'])}: pre-election reports",
                                    numeric=(2, 3, 4), copy=False, min_width="46rem"),
                         h("p", {"class": "muted cf-race-note"},
                           "At least one report's own numbers don't add up; it is shown as filed. The note is with the race.")
                         if note else None))
    if partial:
        prow = []
        for r in partial:
            for i, e in enumerate(r["entries"]):
                prow.append([_race_title(r["contest"]) + f" ({r['election']['date'][:4]})" if i == 0 else "",
                             h("span", None, e["name"], h("span", {"class": "cf-sub"}, party_label(e["party"]))),
                             _entry_state(e, r)])
        out += [h("h3", None, "Races without a like-for-like set"),
                h("p", None, "In these races at least one candidate's pre-election report is not posted, can't be read, or "
                             "covers a different period, so the figures are not set side by side. Each candidate's "
                             "posted reports are listed with the race."),
                data_table("cf-races-partial", ["Race", "Candidate (ballot order)", "Pre-election report for this race"], prow,
                           caption="Contested races with an incomplete set of pre-election reports", copy=False,
                           min_width="40rem")]
    if empty:
        out.append(h("details", {"class": "cf-details"},
                     h("summary", None, f"{len(empty)} other contested races with no pre-election report posted for any candidate"),
                     h("ul", {"class": "cf-empty-races"},
                       [h("li", None, f"{_race_title(r['contest'])} ({r['election']['date'][:4]})") for r in empty])))
    out.append(h("p", {"class": "muted"}, "How a candidate is matched to a committee: the surname (and, where needed, "
                                         "the first name) on the ballot is matched to the candidate named on filings for "
                                         "the same office in the same cycle. A candidate with no such filing is shown as "
                                         "not posted."))
    return out


def _race_title(contest) -> str:
    return re.sub(r"^St\. Joseph County ", "County ", contest["label"])


def _entry_state(e, race) -> str:
    st = e["state"]
    if st == "posted":
        if race["complete"]:
            return "Posted"
        return f"Posted ({period_text(e['row'])})"
    if st == "unreadable":
        return "Posted, but the scan can't be read"
    if st == "no-pre":
        return "Not posted (the committee has other reports in this cycle)"
    if st == "ambiguous":
        return "Not compared: more than one matching report or committee"
    if e.get("elsewhere"):
        return f"Not posted for this office (a filing under “{e['elsewhere']}” may be this candidate's)"
    return "Not posted"


def _large_block(ed, page, model) -> list:
    c = page.cites
    large = model["large"]
    dates = sorted(x["e"]["date"] for x in large if parse_date(x["e"]["date"]))
    pre_close = Counter(r["period_to"] for r in model["rows"]
                        if r["report_type"] == "Pre-Election" and r["_cycle"] == "2026" and r["period_to"]).most_common(1)
    close = parse_date(pre_close[0][0]) if pre_close else None
    late = sum(1 for d in dates if close and parse_date(d) > close)
    trs = []
    for x in large:
        e = x["e"]
        trs.append([e["contributor"], money(_num(e["amount"])), fmt_date(e["date"]),
                    h("span", None, e["committee"] or "Committee not named on the notice",
                      h("span", {"class": "cf-sub"}, "Candidate: ",
                        name_with_form_party(e["candidate"], x["row"]["party"] if x["row"] else "",
                                             _records_party(ed, e["candidate"], x["row"]["_cycle"] if x["row"] else "2026"))),
                      h("span", {"class": "cf-sub"}, x["office"])),
                    h("span", {"class": "cf-lnote"}, x["note"]),
                    h("span", None, f"doc {e['doc_id']} ", c.cite(e["source_ids"]))])
    return [
        h("p", None, f"This table lists the {len(large)} contribution entries on the county's {len({x['e']['doc_id'] for x in large})} "
                     "posted CFA-11 notices, with the contributor's name as filed.", c.cite(SRC_COVERAGE), " ",
          status_badge("from_scan", page), f" The dates run from {fmt_date(min(dates))} to {fmt_date(max(dates))}. ",
          (f"Of these, {late} are dated after {fmt_date(close)}, when most 2026 pre-election reports close, so they "
           "cover part of the time before election day that no regular report covers yet." if close else ""), " ",
          status_badge("computed", page, "Dates counted from cf_large_contributions.csv.")),
        h("p", None, "Listed by the recipient's office, then committee name, then date. Never by amount. Notes say "
                     "where the notice marks the money as in-kind, as the candidate's own money, or as an amount under "
                     "$1,000 reported alongside a larger one. " + FORM_PARTY_NOTE),
        data_table("cf-large-table", ["Contributor (as filed)", "Amount", "Date received", "Recipient committee",
                                      "Note on the notice", "Form"], trs,
                   caption="Large contributions reported on CFA-11 notices", numeric=(1,), min_width="56rem"),
    ]


def _gaps(ed, page, model) -> list[dict]:
    rows = model["rows"]
    single = sum(1 for r in rows if r["double_entry"] == "single")
    gaps = [
        {"item": "Campaign-finance reports from 2022 and earlier",
         "why_missing": "The county's Candidate Filings page starts with the 2023 annual reports.",
         "how_to_fill": "A public records request to the county election office for every CFA-4 filed, including reports never posted online."},
        {"item": "2023 pre-primary and pre-election reports",
         "why_missing": "The county posted only 2023 annual reports.",
         "how_to_fill": "The same records request."},
        {"item": "Reports after mid-October 2026",
         "why_missing": "The newest posted regular reports end in October 2026; the 2026 annual reports cover through Dec 31, 2026.",
         "how_to_fill": "Re-pull the county page after the annual reports are posted."},
        {"item": "Doc 70515 (Sharon Brinker, 2026 pre-primary tab): summary sheet not read",
         "why_missing": "The pages rendered were a Schedule B and the form instructions; the summary sheet is further into the 8-page file.",
         "how_to_fill": "Re-pull the full document and read the summary sheet. Her 2026 pre-election report (doc 72776) is included."},
        {"item": "Doc 65627 (Canneth Lee, 2024 annual): unreadable",
         "why_missing": "The scan is washed out; the few legible cells don't reconcile.",
         "how_to_fill": "A better copy from the county."},
        {"item": "12 filings with no office written on the form",
         "why_missing": "Neither the form nor any other filing by the same committee names an office. The guide doesn't fill it in from ballots.",
         "how_to_fill": "Ask the committees or the county election office."},
        {"item": "Report periods that look miswritten (shown as written)",
         "why_missing": "Doc 66082 (Eli Wax) gives 2023 as its period, but its opening cash matches his 2023 closing cash and it was posted "
                        "with the 2024 reports, so it is probably the 2024 report; the campaign totals follow that note and count it "
                        "in the 2024 cycle, not in his 2023 race. Doc 72875 (Michelle M. Shaw) writes 2024 for 2026 in its start "
                        "date; the totals read 2026. Doc 68014 gives a 2026 period in the 2025 batch (kept as written, flagged); "
                        "CFA-11 docs 72951 and 71873 write 2016 for 2026.",
         "how_to_fill": "Confirm with the filers or the county."},
        {"item": "Reports whose dates disagree with their figures (both counted, flagged)",
         "why_missing": "Doc 66176 (Kris Verash, 2024 final) is dated the whole of 2024 but reports $0 spent, so it can't include "
                        "his pre-primary report's $4,945.21 (doc 62629). Doc 65671 (Ryan McCullough, 2024 annual) starts on the "
                        "same day as his pre-election report (doc 64472) and repeats its $2,260.86 spent; with no cash on either "
                        "report the guide can't tell whether it is cumulative. Doc 65634 (Derek D. Dieter, 2024 annual) gives a "
                        "year-to-date figure equal to its own period, below his pre-election report's; the guide adds the reports.",
         "how_to_fill": "Read the forms again, or ask the committees which period each report covers."},
        {"item": "Date of the 2024 delinquent-filer list (doc 66024), and whether each person later filed",
         "why_missing": "The posted list has no date. The guide checked only the county's posted filings it read for a later "
                        "report covering 2024; a report filed but not posted would not be found.",
         "how_to_fill": "Ask the county election office for the list's date and each committee's current filing status."},
        {"item": "Itemized contributions and expenditures (schedule pages)",
         "why_missing": "Only the one-page summary sheets were transcribed.",
         "how_to_fill": "Read the Schedule A and B pages of each report."},
        {"item": f"Second reading of the remaining filings ({single} filings rest on one reading)",
         "why_missing": f"Only a {SAMPLE_DOCS}-document sample was read twice; a random spot-check of {SPOT_CHECK[1]} single-read documents matched.",
         "how_to_fill": "Read the rest a second time."},
    ]
    gaps += ed.gaps(files=["gaps_services"], pattern=r"Campaign-finance reporting schedule")
    return gaps


# --------------------------------------------------------------------------- shared by the campaign pages

def cf_all(ed) -> dict:
    """The filings model, the races and the areas, built once per edition (every campaign page shares them)."""
    got = ed.__dict__.get("_cf_all")
    if got is None:
        from civic import campaign_money as cm
        model = build_model(ed)
        races = cm.build_races(ed, model["rows"])
        areas, other = cm.build_areas(ed, model["rows"], races)
        got = {"model": model, "races": races, "areas": areas, "other": other}
        ed.__dict__["_cf_all"] = got
    return got


def doc_link(ed, r: dict) -> Markup:
    url = _doc_url(ed, r)
    label = "doc " + r["doc_ids"].replace(";", ", ")
    return h("a", {"href": url}, label) if url else h("span", None, label)


def _adding_block(ed, page, model) -> list:
    c = page.cites
    m = "CFM-010"
    return [
        h("p", None, "For each race, the guide adds up what every candidate's committee reported over the whole campaign: "
                     "every report on file for the race's election cycle, not just one report.", c.cite(m), " ",
          status_badge("computed", page, "Sums of reports from cf_local.csv by the rules below.")),
        h("ul", None,
          h("li", None, h("strong", None, "Cycle. "), "A report belongs to the cycle of the period written on it. Annual "
                        "or final reports that close January to March count toward the year before, and the 2025 annual "
                        "reports count in the 2026 cycle.", c.cite(SRC_COVERAGE), " When a transcription note names the "
                        "right date for a miswritten one (doc 66082: “the year is probably miswritten for 2024”), the "
                        "guide follows the note and says so next to the candidate; when a note only doubts a date, the "
                        "date is kept as written and flagged. City and town offices were last on "
                        "the ballot in 2023; most county and township offices in 2026; some county offices and school "
                        "boards in 2024. Each race uses the cycle of its own latest election."),
          h("li", None, h("strong", None, "Which report is which. "), "Each report is placed by the dates it covers, "
                        "compared with the primary and general election dates: the year-before annual (2026 cycle "
                        "only), pre-primary, pre-election and year-end annual. When the box marked on the form disagrees "
                        "with the dates, the dates decide and the report's note says so.", c.cite(m)),
          h("li", None, h("strong", None, "Amendments. "), "An amended report replaces the report it amends. The two are "
                        "never both added.", c.cite(m)),
          h("li", None, h("strong", None, "No double counting, and no real report dropped. "), "A report is left out "
                        "only when it is truly covered by another: the same report filed twice, or a report whose period "
                        "lies wholly inside another report's period when that report's figures include its money. When "
                        "one report opens with the cash another closed with, the two are separate periods and both are "
                        "added, whatever their written dates say; if the dates overlap or nest, both are still added and "
                        "the conflict is noted next to the candidate. A report with no start date written is never "
                        "treated as inside another. When two reports overlap in a way that can't be untangled, the "
                        "committee gets no total and its reports are listed one by one.", c.cite(m)),
          h("li", None, h("strong", None, "One year at a time. "), "When the reports on file cover a calendar year from "
                        "January 1 with no gap, the guide adds their “this period” columns. When they don't (most often "
                        "because an earlier report isn't on file: the county posted no 2023 pre-primary or pre-election "
                        "reports), it uses the year-to-date column of the year's latest report, as the filer wrote it, "
                        "and the candidate's line says so. That holds even when the form's own arithmetic doesn't add "
                        "up (marked next to the candidate), because the reports on file are then known to fall short. "
                        "It doesn't when that figure is less than the reports on file add up to, or the dates of two of "
                        "the year's reports conflict: then the guide adds the reports. Either way the other figure is "
                        "checked, and any difference is noted next to the candidate.", c.cite(f"{m};{SRC_COVERAGE}")),
          h("li", None, h("strong", None, "Expected reports. "), "The reports expected for each office and cycle are the "
                        "ones in the guide's coverage file (2023: the annual report; 2024: pre-primary, pre-election and "
                        "annual; 2026: the 2025 annual, pre-primary and pre-election).", c.cite(SRC_COVERAGE),
            " A candidate nominated without a primary isn't expected to file a pre-primary report, one who was in the "
            "primary only isn't expected to file a pre-election report, a committee with no line on the ballot is "
            "expected to file only its annual report, and nothing is expected after a final report.", c.cite(m)),
          h("li", None, h("strong", None, "Incomplete. "), "A race is marked incomplete whenever any expected report of "
                        "any of its candidates is not on the county's page, a report can't be read or leaves a line "
                        "blank, or a candidate has no reports on file at all. Its total then covers only what is on "
                        "file: a floor, not a final figure. “Not on file” means only that the county's page has no such "
                        "report. The guide doesn't know whether each committee had to file it, and doesn't call any "
                        "report late.", c.cite(m)),
          h("li", None, h("strong", None, "Cash on hand "), "is the closing cash of the candidate's latest report, shown "
                        "only when that report's own arithmetic holds (VERIFIED or DERIVED).", c.cite(m)),
          h("li", None, h("strong", None, "Matching candidates to committees. "), "A ballot candidate is matched to "
                        "committees that filed for the same office in the same cycle by surname and first name or "
                        "nickname (a surname one letter off, or written surname first, also matches when it is the "
                        "only candidate). A filing that names no district or seat joins a race only on a full name "
                        "match. Each committee's reports count in one race only. A committee for the office that matches "
                        "no ballot candidate is listed in the race as “not on the ballot in the guide's results”.",
            c.cite(m))),
        h("p", None, "By-party sums use the party on the ballot, or, for a committee with no ballot line, the party "
                     "written on its form. Each party's sum says how many of that party's candidates it covers (for "
                     "example “1 of 4 candidates with reports”), so a party total never reads as complete when "
                     "candidates have no reports on file. Party labels never set the order: candidates are listed in "
                     "ballot order, then committees with no ballot line by name."),
    ]


def build_all(site):
    ed = site.ed
    page = site.page(ALL_PAGE, banners=False)
    c = page.cites
    cf = cf_all(ed)
    model = cf["model"]
    toc = [("explorer", "Every filing"), ("large", "Large contributions"), ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(h("header", {"class": "page-hero"},
               h("p", {"class": "eyebrow mono"}, "Reference · Money · Campaign finance"),
               h("h1", None, page.title),
               h("p", {"class": "dek"}, f"All {len(model['rows'])} local campaign-finance reports the guide read from the "
                                        "county's scans, and every large-contribution notice.", c.cite(SRC_FILINGS_PAGE)),
               h("p", None, "Looking for one place or race? Start from the ",
                 h("a", {"href": page.rel(INDEX_PAGE)}, "map and list by place"), ". How the forms were read: ",
                 h("a", {"href": page.rel(HOW_PAGE + "#method")}, "How campaign finance reporting works"), "."),
               h("nav", {"class": "toc", "aria-label": "On this page"},
                 h("ol", None, [h("li", None, h("a", {"href": f"#{a}"}, t)) for a, t in toc]))))
    page.add(section("explorer", 1, "Every filing, by office and committee", *_explorer_block(ed, page, model),
                     scope="county", ed=ed))
    page.add(section("large", 2, "Large contributions (CFA-11 notices)", *_large_block(ed, page, model),
                     scope="county", ed=ed))
    page.finish(gaps=_gaps(ed, page, model))
    return page


PAGES = {HOW_PAGE: build_how, ALL_PAGE: build_all}
