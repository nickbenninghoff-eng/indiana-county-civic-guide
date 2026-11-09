"""Whole-cycle campaign money for local races: the model behind money/campaigns/ (index map, area pages).

    spec = cycle_spec(ed, "2026")                       # election year, primary and general dates
    s = committee_summary(rows, spec, ["Annual", "Pre-Primary", "Pre-Election"])   # one committee, one cycle
    races = build_races(ed, rows)                       # every local race on the 2023, 2024 and 2026 ballots
    areas = build_areas(ed, rows, races)                # races grouped by government, plus every other filing

Input rows are cf_local.csv rows annotated by pages/campaigns.py build_model (_key = committee identity,
_cycle, _office, _group). Money is kept in integer cents, so every total is an exact sum of the rows it names.

Rules (each one is stated on the pages that show the figures):

* Cycle: from period_to as written (annual and final reports closing January to March count toward the year
  before; 2025 annual reports count in the 2026 cycle). Same rule as tools/build_cf_local.py and cf_coverage.csv,
  except that a transcription note naming the right date explicitly ("the year is probably miswritten for 2024")
  is followed (date_fix); the report says so on the page. A note that doubts a date without naming the right one
  keeps the date as written and flags the report.
* A report's place in the cycle (its "slot": prior-year annual, pre-primary, pre-election, year-end annual) comes
  from the period it covers, compared with the primary and general election dates. When the box marked on the form
  disagrees, the report is still counted by its period and a note says so.
* Whole-cycle figures add the "this period" column of every report counted for the committee in the cycle:
  - an amended report replaces the report it amends (same slot, overlapping period); the two are never both added;
  - a report filed twice (same period, same figures) is added once;
  - a report whose period lies wholly inside another report's period is not added again when that report's figures
    include its money; when they don't, both are counted and the date conflict is flagged;
  - two reports whose cash chains (one closes at the non-zero balance the other opens with) are two periods, whatever
    their written dates say: both are counted, and a date overlap is flagged. A blank start date never puts a report
    inside another;
  - two reports that overlap by more than a day without their cash chaining can't be separated, so the committee
    gets no total (None) and the race is marked incomplete;
  - each calendar year's figure is the sum of the "this period" columns when the reports cover the year from
    January 1; otherwise the latest report's year-to-date column as filed (flagged when the form doesn't
    reconcile), unless that figure is below the sum of the reports on file or two of the year's reports have
    conflicting dates (see year_figure). Whenever the year-to-date column is used, the candidate's line says so
    and why (ytd_reason).
  Every dropped report is listed in the summary's "drops" with the reason and the report that covers it.
* Expected reports: cf_coverage.csv's expected_report_types for the office and cycle. A candidate who was not on
  the general-election ballot is not expected to file the pre-election report, and nothing is expected after a
  final report. Any expected report not on file marks the race incomplete ("not on file", never "late").
"""
from __future__ import annotations

import re
from collections import Counter, OrderedDict, defaultdict
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from .data import fmt_date, parse_date, split_ids

# ------------------------------------------------------------------------------------------- money
def cents(v) -> int | None:
    """'1234.5' -> 123450. None for blank or unreadable cells."""
    if v is None:
        return None
    s = str(v).strip().replace(",", "").replace("$", "")
    if not s:
        return None
    try:
        d = Decimal(s)
    except InvalidOperation:
        return None
    return int((d * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def usd(c: int | None, none: str = "not on file") -> str:
    """Cents -> '$1,234.56' (negative '-$5.00'); none for None."""
    if c is None:
        return none
    sign = "-" if c < 0 else ""
    d, r = divmod(abs(int(c)), 100)
    return f"{sign}${d:,}.{r:02d}"


def usd_round(c: int | None, none: str = "not on file") -> str:
    """Cents -> whole dollars '$1,235' for compact places (the map panel bars); exact figures go elsewhere."""
    if c is None:
        return none
    sign = "-" if c < 0 else ""
    return f"{sign}${(abs(int(c)) + 50) // 100:,}"


# ------------------------------------------------------------------------------------------- cycles
CYCLE_ELECTIONS = OrderedDict([("2023 municipal", ("2023p", "2023g")), ("2024", ("2024p", "2024g")),
                               ("2026", ("2026p", "2026g"))])
PRIOR_ANNUAL = {"2026"}          # cycles whose "Annual" is the year before's annual report (2025 annual in 2026)
EXPECTED = {"2023 municipal": ["Annual"], "2024": ["Pre-Primary", "Pre-Election", "Annual"],
            "2026": ["Annual", "Pre-Primary", "Pre-Election"]}
CLEAN = ("verified", "derived")


def _year_of(period_to: str, report_type: str) -> int | None:
    pt = (period_to or "").strip()
    if re.fullmatch(r"\d{4}", pt):
        pt += "-12-31"
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", pt):
        return None
    y, m = int(pt[:4]), int(pt[5:7])
    rt = report_type or ""
    if m <= 3 and (any(t in rt for t in ("Annual", "Final", "Outgoing")) or not rt):
        y -= 1
    return y


def _cycle_for(y: int | None) -> str:
    if y is None:
        return "period unknown"
    if y <= 2023:
        return "2023 municipal"
    if y == 2024:
        return "2024"
    return "2026"


def effective_year(row: dict) -> int | None:
    """The calendar year a report counts toward by its period_to AS WRITTEN (None when no complete period end is
    written). The coverage matrix uses this, to match tools/build_cf_local.py; the money model uses money_year."""
    return _year_of(row.get("period_to"), row.get("report_type"))


def cycle_of(row: dict) -> str:
    """Same rule as tools/build_cf_local.py: the cycle comes from period_to as written."""
    return _cycle_for(effective_year(row))


def money_year(row: dict) -> int | None:
    """The calendar year the money model counts a report in: effective_year, but from the period as read when a
    transcription note explicitly corrects a miswritten date (see date_fix)."""
    return _year_of(_pt(row), row.get("report_type"))


def money_cycle(row: dict) -> str:
    """The cycle the money model counts a report in (cycle_of, with date_fix applied)."""
    return _cycle_for(money_year(row))


def election_cycle(eid: str) -> str | None:
    for cyc, (_p, g) in CYCLE_ELECTIONS.items():
        if g == eid:
            return cyc
    return None


def cycle_spec(ed, cycle: str) -> dict | None:
    p, g = CYCLE_ELECTIONS.get(cycle, (None, None))
    pe, ge = ed.elections.get(p), ed.elections.get(g)
    if not pe or not ge or not parse_date(pe["date"]) or not parse_date(ge["date"]):
        return None
    return spec_for(cycle, parse_date(pe["date"]), parse_date(ge["date"]))


def spec_for(cycle: str, primary: date, general: date) -> dict:
    return {"cycle": cycle, "year": general.year, "primary": primary, "general": general,
            "prior_annual": cycle in PRIOR_ANNUAL}


# ------------------------------------------------------------------------------------------- slots
SLOTS = ["earlier", "prior-annual", "pre-primary", "pre-election", "year-end", "later"]
SLOT_TYPE = {"prior-annual": "Annual", "pre-primary": "Pre-Primary", "pre-election": "Pre-Election",
             "year-end": "Annual"}


def slot_label(slot: str, spec: dict) -> str:
    y = spec["year"]
    return {"earlier": f"before {y - 1}" if spec["prior_annual"] else f"before {y}",
            "prior-annual": f"{y - 1} annual",
            "pre-primary": f"{y} pre-primary",
            "pre-election": f"{y} pre-election",
            "year-end": f"{y} annual" if not spec["prior_annual"] else f"after the {y} election",
            "later": f"after {y}"}[slot]


def expected_slots(spec: dict, expected_types: list[str]) -> list[str]:
    out = []
    for t in expected_types:
        if t == "Annual":
            out.append("prior-annual" if spec["prior_annual"] else "year-end")
        elif t == "Pre-Primary":
            out.append("pre-primary")
        elif t == "Pre-Election":
            out.append("pre-election")
    return sorted(dict.fromkeys(out), key=SLOTS.index)


def slot_of(row: dict, spec: dict) -> str | None:
    """Where a report sits in the cycle, by the period it covers. None when no full period end is written."""
    raw = _pt(row).strip()
    if re.fullmatch(r"\d{4}", raw):          # a year only: the end of that year, as in the cycle rule
        raw += "-12-31"
    pt = parse_date(raw) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw) else None
    y = money_year(row)
    if pt is None or y is None:
        return None
    Y = spec["year"]
    if y < Y:
        return "prior-annual" if spec["prior_annual"] and y == Y - 1 else "earlier"
    if y > Y:
        return "later"
    if pt < spec["primary"]:
        return "pre-primary"
    if pt <= spec["general"]:
        return "pre-election"
    return "year-end"


def marked_types(row: dict) -> set[str]:
    """Report types a filing counts as (a final report counts as the annual, as in cf_coverage.csv)."""
    return {"Annual" if t == "Final" else t for t in (row.get("report_type") or "").split("; ") if t}


def _is_final(row: dict) -> bool:
    return "Final" in (row.get("report_type") or "")


def _d(v):
    v = (v or "").strip()
    return parse_date(v) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) else None


def _doc(row: dict) -> str:
    ids = split_ids((row.get("doc_ids") or "").replace(",", ";"))
    return ids[-1] if ids else row.get("filing_id", "")


def period_words(row: dict) -> str:
    """The period as written on the form."""
    f, t = row.get("period_from", ""), row.get("period_to", "")
    if not f and not t:
        return "period not written"
    return f"{fmt_date(f) if f else 'start not written'} to {fmt_date(t) if t else 'end not written'}"


# ------------------------------------------------------------------------------------------- dates as read
# A transcription note that says a date on the form is miswritten. The data keeps the date as written (the CSVs are
# not edited); the money model reads the corrected date only when the note names it explicitly:
#   "the year is probably miswritten for 2024"                -> the whole period moves to 2024 (its cycle with it)
#   "From date handwritten 4/11/2024 (likely typo for 2026"   -> that one date reads 4/11/2026
# A note that doubts a date without naming the right one ("likely year typo") keeps the dates and flags the report.
# A note describing a slip the transcriber already corrected in the CSV (the stored date is not the one the note
# says was written) changes nothing.
_YEAR_FIX = re.compile(r"(?i)\byear is (?:probably|likely|evidently) miswritten for (\d{4})\b")
_FIELD_FIX = re.compile(r"(?i)\b(from date|period-from|from|period-through|through date|through|to date)\s+"
                        r"(?:hand)?written(?: as)?\s+(\d{1,2}/\d{1,2}/\d{2,4})\s*\((?:likely|probable|probably|evident|"
                        r"evidently) typo for (\d{1,2}/\d{1,2}/\d{2,4}|\d{4})\b")
_DATE_DOUBT = re.compile(r"(?i)\b(?:likely|probable|possible|evident) year typo\b|\byear (?:is )?(?:probably |likely )?"
                         r"miswritten\b(?! for \d)")


def _mdy(s: str) -> date | None:
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})", s)
    if not m:
        return None
    y = int(m.group(3))
    y = y + 2000 if y < 100 else y
    try:
        return date(y, int(m.group(1)), int(m.group(2)))
    except ValueError:
        return None


def _shift_year(d: date, y: int) -> date:
    try:
        return d.replace(year=y)
    except ValueError:                     # February 29 in a year without one
        return d.replace(year=y, day=28)


def date_fix(row: dict) -> dict | None:
    """How the money model reads a report's period when a transcription note says a date is miswritten.

    Returns None (dates as written); {"kind": "year" | "from" | "to", "from", "to" (ISO strings as read), "note"}
    for an explicit correction; or {"kind": "doubt", "note"} when the note doubts a date without naming the right
    one (the dates are kept as written and the report is flagged)."""
    notes = row.get("notes") or ""
    if not notes:
        return None
    pf, pt = (row.get("period_from") or "").strip(), (row.get("period_to") or "").strip()
    m = _YEAR_FIX.search(notes)
    if m and _d(pt):
        want, have = int(m.group(1)), effective_year(row)
        if have is not None and want != have:
            dy = want - have
            f, t = _d(pf), _d(pt)
            return {"kind": "year", "year": want,
                    "from": _shift_year(f, f.year + dy).isoformat() if f else pf,
                    "to": _shift_year(t, t.year + dy).isoformat(),
                    "note": f"the year is probably miswritten for {want}"}
    for m in _FIELD_FIX.finditer(notes):
        field = "from" if "from" in m.group(1).lower() else "to"
        written, read = _mdy(m.group(2)), m.group(3)
        stored = _d(pf if field == "from" else pt)
        if not written or stored != written:
            continue                       # the CSV already holds the corrected date
        new = _shift_year(written, int(read)) if re.fullmatch(r"\d{4}", read) else _mdy(read)
        if not new:
            continue
        return {"kind": field, "from": new.isoformat() if field == "from" else pf,
                "to": new.isoformat() if field == "to" else pt,
                "note": f"the {'start' if field == 'from' else 'end'} date is written {fmt_date(written.isoformat())}, "
                        f"likely a slip for {fmt_date(new.isoformat())}"}
    if _DATE_DOUBT.search(notes):
        return {"kind": "doubt", "note": "the transcription note says a year on the form may be miswritten"}
    return None


def _pf(row: dict) -> str:
    """period_from as the money model reads it."""
    fx = date_fix(row)
    return fx["from"] if fx and "from" in fx else (row.get("period_from") or "")


def _pt(row: dict) -> str:
    """period_to as the money model reads it."""
    fx = date_fix(row)
    return fx["to"] if fx and "to" in fx else (row.get("period_to") or "")


# ------------------------------------------------------------------------------------------- one committee
def committee_summary(rows: list[dict], spec: dict, expected_types: list[str], ballot: str = "general",
                      today: date | None = None) -> dict:
    """One committee's reports in one cycle, counted by the rules in the module docstring.

    ballot: 'general' (general-election ballot, after a primary), 'general-only' (general ballot, no primary line),
    'primary' (primary only) or 'none' (no ballot line found).
    Returns items (every report with slot, counted flag, reason and notes), spent/raised in cents (None when the
    reports can't be added), cash at the latest counted report when that report reconciles, expected and missing
    slots, flags and committee-level notes."""
    items = []
    notes: list[str] = []
    flags: set[str] = set()
    drops: list[dict] = []
    for r in sorted(rows, key=lambda r: (_pt(r) or "9999", _pf(r), r["filing_id"])):
        it = {"row": r, "slot": slot_of(r, spec), "counted": True, "why": "", "notes": [], "conflict": False}
        fx = date_fix(r)
        if fx and fx["kind"] == "year":
            flags.add("date-read")
            it["notes"].append(f"The form gives the period as {period_words(r)}, but the transcription note says "
                               f"{fx['note']}, so the guide counts it as a {fx['year']} report, in the "
                               f"{money_cycle(r)} cycle.")
        elif fx and fx["kind"] in ("from", "to"):
            flags.add("date-read")
            it["notes"].append(f"The transcription note says {fx['note']}; the guide reads the period as "
                               f"{fmt_date(_pf(r)) if _pf(r) else 'start not written'} to {fmt_date(_pt(r))}.")
        elif fx:
            flags.add("date-doubt")
            it["notes"].append(f"The transcription note says a year on this form may be miswritten; the guide keeps "
                               f"the dates as written ({period_words(r)}). Check the form.")
        items.append(it)

    def drop(it, why, by, note):
        it["counted"], it["why"] = False, why
        it["notes"].append(note)
        drops.append({"id": it["row"]["filing_id"], "why": why, "by": by["row"]["filing_id"] if by else ""})

    def conflict(a, b, note):
        a["conflict"] = b["conflict"] = True
        flags.add("date-conflict")
        b["notes"].append(note)

    # 1. amendments replace the report they amend (same slot, overlapping period)
    by_slot = defaultdict(list)
    for it in items:
        by_slot[it["slot"]].append(it)
    for slot, its in by_slot.items():
        if len(its) < 2:
            continue
        amended = [it for it in its if (it["row"].get("amended") or "").lower() == "yes"]
        if not amended:
            continue
        keep = max(amended, key=lambda it: (_pt(it["row"]), _doc_num(it["row"])))
        for it in its:
            if it is keep or not _overlaps(it["row"], keep["row"]):
                continue
            if _sequential_cash(it["row"], keep["row"]) or _sequential_cash(keep["row"], it["row"]):
                continue          # one closes where the other opens: two periods, not a report and its amendment
            drop(it, "replaced", keep, f"Replaced by the amended report (doc {_doc(keep['row'])}), so it is not added.")

    # 2. periods: back to back, the same report twice, contained, or overlapping. A report is dropped only when it is
    #    truly redundant: filed twice (same period, same figures) or wholly inside a report whose figures include its
    #    money. Two reports whose cash chains (one closes where the other opens, at a balance other than zero) are
    #    two periods whatever their written dates say; both are counted and the conflict is flagged. A blank start
    #    date never puts a report inside another.
    stack: list[dict] = []
    overlap = False
    for it in items:
        if not it["counted"]:
            continue
        r = it["row"]
        if it["slot"] is None:
            drop(it, "no-period", None, "No complete period is written on this report, so the guide can't place it "
                                        "in the cycle; it is listed but not added.")
            continue
        while stack:
            top = stack[-1]
            prev = top["row"]
            od = _overlap_days(prev, r)
            nested = _contains(r, prev) or _contains(prev, r)
            if _same_period(prev, r) and _same_figures(prev, r):
                drop(it, "duplicate", top, f"Same period and same figures as doc {_doc(prev)}: the same report filed "
                                           "twice, so it is not added again.")
                break
            if _chained(prev, r) and (nested or (od > 1 and not _ends_later(r, prev))):
                where = (f"overlap doc {_doc(prev)} ({period_words(prev)}) by {od} days" if od > 1 and not nested else
                         f"nest with doc {_doc(prev)} ({period_words(prev)})")
                if _sequential_cash(prev, r):
                    conflict(top, it, f"Its dates as written ({period_words(r)}) {where}, but its opening cash equals "
                                      "that report's closing cash, so they are two periods and both are counted. One of "
                                      "the dates on the forms is probably wrong.")
                else:          # both balances zero: the cash says nothing either way, and no report is dropped on a guess
                    conflict(top, it, f"Its dates as written ({period_words(r)}) {where}. Both reports open and close "
                                      "with no cash, so the guide can't tell whether this one repeats that report's money; "
                                      "both are counted. Check the forms.")
                break
            if _sequential_cash(r, prev) and (od > 1 or nested):
                conflict(top, it, f"Its dates as written ({period_words(r)}) "
                                  + (f"overlap doc {_doc(prev)} ({period_words(prev)}) by {od} days" if od > 1 else
                                     f"nest with doc {_doc(prev)} ({period_words(prev)})")
                                  + ", but its closing cash equals that report's opening cash, so it probably comes "
                                  "before that report; both are counted. One of the dates on the forms is probably wrong.")
                break
            if _chained(prev, r) and not nested:
                if od > 1:
                    it["notes"].append(f"Its dates as written overlap the report before it by {od} days, but its opening "
                                       "cash equals that report's closing cash, so the two are counted back to back.")
                break
            if _contains(r, prev):
                if _covers(r, prev):
                    drop(top, "inside", it, f"Its period lies inside the period of a later report on file (doc {_doc(r)}, "
                                            f"{period_words(r)}), whose figures include its money, so it is not added again.")
                    stack.pop()
                    continue
                if _contains(prev, r) and _covers(prev, r):      # the same period: the larger report includes this one
                    drop(it, "inside", top, f"Its period is the same as an earlier report on file (doc {_doc(prev)}), "
                                            "whose figures include its money, so it is not added again.")
                    break
                conflict(top, it, f"Its period as written ({period_words(r)}) contains doc {_doc(prev)}'s "
                                  f"({period_words(prev)}), but its figures don't include that report's money, so both "
                                  "are counted. The dates on one of the forms are probably wrong.")
                break
            if _contains(prev, r):
                if _covers(prev, r):
                    drop(it, "inside", top, f"Its period lies inside the period of an earlier report on file (doc "
                                            f"{_doc(prev)}, {period_words(prev)}), whose figures include its money, so it "
                                            "is not added again.")
                    break
                conflict(top, it, f"Its period as written ({period_words(r)}) lies inside doc {_doc(prev)}'s "
                                  f"({period_words(prev)}), but that report's figures don't include its money, so both "
                                  "are counted. The dates on one of the forms are probably wrong.")
                break
            if od > 1:
                overlap = True
                it["notes"].append(f"Its period overlaps the report before it (doc {_doc(prev)}) by {od} days and its "
                                   "opening cash doesn't match that report's closing cash, so the guide can't tell "
                                   "which money is counted twice.")
                break
            ce, cs = cents(prev.get("cash_end_period")), cents(r.get("cash_start_period"))
            if ce is not None and cs is not None and ce != cs:
                it["notes"].append(f"Its opening cash ({usd(cs)}) doesn't match the closing cash of the report before it "
                                   f"({usd(ce)}).")
            gap = _gap_days(prev, r)
            if gap > 0:
                it["notes"].append(f"{gap} day{'s' if gap != 1 else ''} between this report and the one before it "
                                   "{} covered by any report on file.".format("is not" if gap == 1 else "are not"))
            break
        if it["counted"]:
            stack.append(it)

    counted = [it for it in items if it["counted"]]
    # 3. the box marked on the form vs the slot its period puts it in
    for it in items:
        s = it["slot"]
        if s in SLOT_TYPE and SLOT_TYPE[s] not in marked_types(it["row"]):
            marked = it["row"].get("report_type") or "no report type"
            it["notes"].append(f"Marked {marked} on the form; by its period ({period_words(it['row'])}) it is the "
                               f"{slot_label(s, spec)} report.")
    # 4. expected reports on file
    exp = expected_slots(spec, expected_types)
    if ballot == "general-only":       # nominated without a primary (convention, caucus, independent, school board)
        exp = [s for s in exp if s != "pre-primary"]
    elif ballot == "primary":          # lost or left after the primary: no pre-election report
        exp = [s for s in exp if s != "pre-election"]
    elif ballot == "none":             # no ballot line found: only the annual report every committee files
        exp = [s for s in exp if s in ("prior-annual", "year-end")]
    finals = [it for it in items if _is_final(it["row"]) and it["slot"] in SLOTS]
    if finals:
        last_final = max(SLOTS.index(it["slot"]) for it in finals)
        if any(SLOTS.index(s) > last_final for s in exp):
            exp = [s for s in exp if SLOTS.index(s) <= last_final]
            notes.append("The committee filed a final report, so no later report is expected.")
    on_file = OrderedDict((s, [it["row"] for it in items if it["slot"] == s]) for s in SLOTS
                          if any(it["slot"] == s for it in items))
    missing = [s for s in exp if s not in on_file]
    # 5. whole-cycle figures, one calendar year at a time (see year_figure)
    for it in counted:
        st = it["row"].get("transcription_status")
        if st == "unreadable":
            flags.add("unreadable")
            it["notes"].append("The scan can't be read, so it adds nothing to the totals.")
        elif st == "filer-inconsistent":
            flags.add("inconsistent")
    basis = []
    spent = raised = 0
    if overlap:
        flags.add("overlap")
        spent = raised = None
        notes.append("Two of this committee's reports overlap in a way the guide can't untangle, so its reports are "
                     "listed but not added up.")
    else:
        by_year = defaultdict(list)
        for it in counted:
            y = money_year(it["row"])
            if y is not None and it["row"].get("transcription_status") != "unreadable":
                by_year[y].append(it["row"])
        conflicted = {it["row"]["filing_id"] for it in items if it["conflict"]}
        for y, rs in sorted(by_year.items()):
            missing_y = any(_slot_year(s, spec) == y for s in missing)
            for col, ycol, word in (("expenditures_period", "expenditures_ytd", "spent"),
                                    ("receipts_period", "receipts_ytd", "raised")):
                prior = [cents(x.get(col)) for yy, xs in by_year.items() if yy < y for x in xs]
                prior = [v for v in prior if v is not None]
                b = year_figure(rs, y, col, ycol, word, missing_y, conflicted, sum(prior) if prior else None)
                basis.append(b)
                flags.update(b["flags"])
                notes.extend(b["notes"])
                if word == "spent":
                    spent += b["value"]
                else:
                    raised += b["value"]
    # a period that ends after today can't have been reported yet: the date is a slip on the form
    today = today or date.today()
    for it in items:
        pt = _d(_pt(it["row"]))
        if pt and pt > today:
            flags.add("future-date")
            it["notes"].append(f"Its period is written as ending {fmt_date(it['row']['period_to'])}, after the date the "
                               "guide's data was built, so the date is probably miswritten. Its figures are shown as filed.")
    real_to = [_pt(it["row"]) for it in counted if _d(_pt(it["row"])) and _d(_pt(it["row"])) <= today]
    # 7. cash on hand at the latest counted report, only when that report reconciles. The latest is the last by date,
    #    unless its closing cash is another counted report's opening cash: then the cash chain runs on to that one.
    latest = max(counted, key=lambda it: (_pt(it["row"]), _pf(it["row"])))["row"] if counted else None
    seen = set()
    while latest is not None and latest["filing_id"] not in seen:
        seen.add(latest["filing_id"])
        nxt = [it["row"] for it in counted if it["row"] is not latest and it["row"]["filing_id"] not in seen
               and _sequential_cash(latest, it["row"])]
        if len(nxt) != 1:
            break
        latest = nxt[0]
    cash, cash_why = None, ""
    if latest is not None:
        cv = cents(latest.get("cash_end_period"))
        if latest.get("transcription_status") not in CLEAN:
            cash_why = "not shown: the latest report's own numbers don't add up or can't be read"
        elif cv is None:
            cash_why = "not shown: blank on the latest report"
        else:
            cash = cv
    return {"key": rows[0]["_key"] if rows else "", "items": items, "counted": [it["row"] for it in counted],
            "spent": spent, "raised": raised, "cash": cash, "cash_why": cash_why, "latest": latest,
            "expected": exp, "on_file": on_file, "missing": missing, "flags": flags, "notes": notes,
            "ballot": ballot, "basis": basis, "latest_to": max(real_to, default=""), "drops": drops}


def year_covered(rs: list[dict], y: int) -> bool:
    """True when the year's reports on file run from January 1 with no gap: their "this period" columns then
    account for the whole year so far."""
    if not rs or _d(_pf(rs[0])) != date(y, 1, 1):
        return False
    for a, b in zip(rs, rs[1:]):
        if not _chained(a, b) and (_gap_days(a, b) > 0 or _overlap_days(a, b) > 1 or not _d(_pf(b))):
            return False
    return True


def year_figure(rs: list[dict], y: int, col: str, ycol: str, word: str, missing_y: bool,
                conflicted: set | frozenset = frozenset(), earlier: int | None = None) -> dict:
    """One committee's figure for one calendar year and one column (spent or raised), and the rows it comes from.

    * The reports on file cover the year from January 1 with no gap: the sum of their "this period" columns
      (a different year-to-date figure on the latest report is noted, not used).
    * Otherwise, when the latest report of the year has a year-to-date figure: that figure, as filed, which
      covers the parts of the year whose reports aren't on file (the 2023 annual reports are the main case: the
      county posted no 2023 pre-primary or pre-election reports, so the annual report's own period starts in the
      fall). It is used even when the form's arithmetic doesn't reconcile, because the "this period" columns are
      then known to fall short; the flag "ytd-unreconciled" and a note say so. Never when that figure is smaller
      than the reports on file add up to
      (it would drop money a report on file shows), and never when the dates of two of the year's reports
      conflict (the "latest" report is then not known).
      Never, either, when the committee has reports of an earlier year in the same cycle (earlier = their "this
      period" sum) and the year-to-date figure reaches the reports of both years together: it may then be a
      cumulative figure that includes the earlier year's money, which is already counted.
    * Otherwise the sum of the "this period" columns on file, with a note."""
    rs = sorted(rs, key=lambda r: (_pt(r), _pf(r)))
    last = rs[-1]
    vals = [(r, cents(r.get(col))) for r in rs]
    blanks = [r for r, v in vals if v is None]
    psum = sum(v for _r, v in vals if v is not None)
    ytd = cents(last.get(ycol))
    flags, notes = set(), []
    ids = [r["filing_id"] for r, v in vals if v is not None]
    clash = [r for r in rs if r["filing_id"] in conflicted]
    if clash:
        how, value = "periods", psum
        flags.add("date-conflict")
        notes.append(f"{y}: the dates on docs {', '.join(_doc(r) for r in clash)} disagree with their figures or cash (see "
                     f"the notes on those reports), so the guide adds the \"this period\" columns of every {y} report on file ({usd(psum)} {word}) rather than "
                     "trusting a year-to-date column."
                     + (f" The latest one's year-to-date column (doc {_doc(last)}) says {usd(ytd)}." if ytd is not None
                        and ytd != psum else ""))
        if blanks:
            flags.add("blank" if word == "spent" else "blank-receipts")
    elif year_covered(rs, y) and not blanks:
        how, value = "periods", psum
        if ytd is not None and ytd != psum:
            flags.add("ytd")
            notes.append(f"{y}: the reports on file cover the year from January 1 and add up to {usd(psum)} {word}; the "
                         f"year-to-date column of the latest one (doc {_doc(last)}) says {usd(ytd)}. The guide uses the "
                         "sum of the reports.")
    elif ytd is not None and earlier and ytd >= psum + earlier:
        how, value = "periods", psum
        flags.add("ytd-cumulative")
        notes.append(f"{y}: the year-to-date column of the latest report (doc {_doc(last)}) says {usd(ytd)} {word}, at "
                     f"least the {y} reports ({usd(psum)}) and the committee's earlier reports in this cycle "
                     f"({usd(earlier)}) together, so it may include money already counted; the guide adds the reports.")
        if blanks:
            flags.add("blank" if word == "spent" else "blank-receipts")
    elif ytd is not None and ytd < psum:
        how, value = "periods", psum
        flags.add("ytd-low")
        notes.append(f"{y}: the year-to-date column of the latest report (doc {_doc(last)}) says {usd(ytd)} {word}, less "
                     f"than the {usd(psum)} the {y} reports on file add up to, so the guide uses the sum of the reports (a "
                     "report's period can start before January 1, and that money is still part of the campaign).")
        if blanks:
            flags.add("blank" if word == "spent" else "blank-receipts")
    elif ytd is not None and (last.get("transcription_status") in CLEAN or y in NOT_POSTED):
        # The reports on file don't account for the whole year, so their "this period" columns are known to fall
        # short; the filer's year-to-date column is the only whole-year figure on file. It is used as filed even
        # when the form's arithmetic elsewhere doesn't reconcile (the guide shows every figure as filed), and the
        # page says so.
        how, value, ids = "ytd", ytd, [last["filing_id"]]
        why = ytd_reason(rs, y, missing_y)
        if ytd != psum or blanks:
            flags.add("ytd-used")
            notes.append(f"{y}: {usd(ytd)} {word}, from the year-to-date column of the latest report (doc {_doc(last)}, "
                         f"through {fmt_date(_pt(last))}), because {why}. The \"this period\" columns of "
                         f"the {y} reports on file add up to {usd(psum)}.")
        if last.get("transcription_status") not in CLEAN:
            flags.add("ytd-unreconciled")
            notes.append(f"{y}: doc {_doc(last)}'s own numbers don't reconcile (see its transcription note), so its "
                         f"year-to-date {word} figure is the filer's, as written.")
        return {"year": y, "word": word, "col": ycol, "how": how, "ids": ids, "value": value, "flags": flags,
                "notes": notes, "why": why, "doc": _doc(last), "report_type": last.get("report_type") or "",
                "clean": last.get("transcription_status") in CLEAN, "differs": ytd != psum or bool(blanks)}
    else:
        how, value = "periods", psum
        if blanks:
            flags.add("blank" if word == "spent" else "blank-receipts")
            line = "expenditures" if word == "spent" else "receipts"
            notes.append(f"{y}: {len(blanks)} report{'s leave' if len(blanks) > 1 else ' leaves'} the {line} line blank, so "
                         "the total covers only the lines filled in.")
        if ytd is not None and ytd != psum:
            flags.add("ytd")
            notes.append(f"{y}: the year-to-date column of the latest report (doc {_doc(last)}) says {usd(ytd)} {word}, "
                         f"but that report's own numbers don't add up, so the guide adds the reports on file: {usd(psum)}.")
    return {"year": y, "word": word, "col": col if how == "periods" else ycol, "how": how, "ids": ids,
            "value": value, "flags": flags, "notes": notes}


# Years for which the county posted no report before the annual one (cf_coverage.csv; stated on how-it-works).
NOT_POSTED = {2023: "the county did not post earlier 2023 reports"}


def ytd_reason(rs: list[dict], y: int, missing_y: bool) -> str:
    """Why the year's "this period" columns fall short, so the year-to-date column is used."""
    if missing_y:
        return f"an earlier {y} report expected for this office is not on file"
    if y in NOT_POSTED:
        return NOT_POSTED[y]
    if _d(_pf(rs[0])):
        return f"the reports on file don't cover {y} from January 1"
    return "the reports on file don't say when their periods start"


def ytd_uses(committees: list[dict]) -> list[dict]:
    """Each (committee, year) whose spent or raised figure is a year-to-date column that differs from the reports'
    own "this period" sum: {year, words, doc, report_type, why, clean}. Drives the candidate's line on the page and
    the map caveat, so a year-to-date figure is never shown without saying so."""
    out = []
    for s in committees:
        by_year: OrderedDict = OrderedDict()
        for b in s.get("basis", []):
            if b["how"] == "ytd" and b.get("differs"):
                u = by_year.setdefault(b["year"], {"year": b["year"], "words": [], "doc": b["doc"],
                                                   "report_type": b["report_type"], "why": b["why"], "clean": b["clean"]})
                u["words"].append(b["word"])
        out.extend(by_year.values())
    return out


def ytd_line(u: dict) -> str:
    rt = (u["report_type"] or "").split(";")[0].strip().lower()
    what = " and ".join(u["words"])
    t = (f"{u['year']} {what}: year-to-date figure from the filer's {rt + ' ' if rt else ''}report (doc {u['doc']}); "
         f"{u['why']}.")
    if not u["clean"]:
        t += " That form's own numbers don't reconcile; the figure is as written."
    return t


def _slot_year(slot: str, spec: dict) -> int:
    return spec["year"] - 1 if slot == "prior-annual" else spec["year"]


def _doc_num(row: dict) -> int:
    try:
        return int(re.sub(r"\D", "", _doc(row)) or 0)
    except ValueError:
        return 0


def _overlaps(a: dict, b: dict) -> bool:
    af, at, bf, bt = _d(_pf(a)), _d(_pt(a)), _d(_pf(b)), _d(_pt(b))
    if not (af and at and bf and bt):
        return True          # same slot and a period end missing: treat as the same report
    return not (at < bf or bt < af)


def _chained(prev: dict, cur: dict) -> bool:
    ce, cs = cents(prev.get("cash_end_period")), cents(cur.get("cash_start_period"))
    return ce is not None and cs is not None and ce == cs


def _sequential_cash(prev: dict, cur: dict) -> bool:
    """prev closes at the cash balance cur opens with, and the balance is not zero. A zero balance proves nothing
    (every report of a committee with no money chains to every other), so only a real balance overrides the dates."""
    ce, cs = cents(prev.get("cash_end_period")), cents(cur.get("cash_start_period"))
    return ce is not None and cs is not None and ce == cs and ce != 0


def _ends_later(cur: dict, prev: dict) -> bool:
    """cur's period, as read, ends after prev's: a report that follows prev by cash can then simply overlap it a
    little (a sloppy start date); one that doesn't end later can't follow it as written."""
    ct, pt = _d(_pt(cur)), _d(_pt(prev))
    return bool(ct and pt and ct > pt)


def _same_period(a: dict, b: dict) -> bool:
    return bool(_d(_pt(a))) and _pt(a) == _pt(b) and _pf(a) == _pf(b)


FIGURES = ("receipts_period", "expenditures_period", "cash_start_period", "cash_end_period")


def _same_figures(a: dict, b: dict) -> bool:
    return all(cents(a.get(f)) == cents(b.get(f)) for f in FIGURES)


def _covers(outer: dict, inner: dict) -> bool:
    """The outer report's figures can include the inner one's money: at least as much raised and spent (a blank
    line on the inner report adds nothing; a blank line on the outer report can't include a filled one)."""
    for f in ("receipts_period", "expenditures_period"):
        o, i = cents(outer.get(f)), cents(inner.get(f))
        if i is None or i == 0:
            continue
        if o is None or o < i:
            return False
    return True


def _contains(outer: dict, inner: dict) -> bool:
    of, ot, inf, int_ = _d(_pf(outer)), _d(_pt(outer)), _d(_pf(inner)), _d(_pt(inner))
    if not (of and ot and inf and int_):
        return False
    return of <= inf and ot >= int_      # identical periods count as contained: the same money twice


def _overlap_days(prev: dict, cur: dict) -> int:
    pt, cf = _d(_pt(prev)), _d(_pf(cur))
    if not pt or not cf or cf > pt:
        return 0
    return (pt - cf).days + 1


def _gap_days(prev: dict, cur: dict) -> int:
    pt, cf = _d(_pt(prev)), _d(_pf(cur))
    if not pt or not cf:
        return 0
    return max(0, (cf - pt).days - 1)


# ------------------------------------------------------------------------------------------- names
SUFFIXES = {"jr", "sr", "ii", "iii", "iv"}
NICKNAMES = {"abigail": "abby", "matthew": "matt", "michael": "mike", "william": "bill", "james": "jamie",
             "janice": "jan", "robert": "bob", "joshua": "josh", "anthony": "tony", "kenneth": "ken",
             "patric": "pat", "eliyahu": "eli", "marcellus": "marcel", "daniel": "dan", "andrew": "andy",
             "christopher": "chris", "thomas": "tom", "randall": "randy", "gerald": "gerry", "kimberly": "kim",
             "theresa": "terri", "katelyn": "katie"}


def surname(name: str) -> str:
    s = re.sub(r'"[^"]*"|\([^)]*\)', " ", name or "")
    toks = [t for t in re.split(r"[\s,]+", s) if t and t.strip(".").lower() not in SUFFIXES]
    toks = [t for t in toks if not re.fullmatch(r"[A-Za-z]\.?", t)]
    return re.sub(r"[^a-z\-']", "", toks[-1].lower()) if toks else ""


def given(name: str) -> set[str]:
    """Given name and any nickname in quotes or parentheses, lower-case, nicknames normalised."""
    out = set()
    for m in re.findall(r'"([^"]+)"|\(([^)]+)\)', name or ""):
        for part in m:
            if part:
                out.add(part.split()[0].lower().strip("."))
    s = re.sub(r'"[^"]*"|\([^)]*\)', " ", name or "")
    toks = [t for t in re.split(r"[\s,]+", s) if t]
    if toks:
        out.add(toks[0].lower().strip("."))
    return {NICKNAMES.get(t, t) for t in out}


def same_person(a: str, b: str) -> bool:
    return bool(surname(a)) and surname(a) == surname(b) and bool(given(a) & given(b))


def _words(name: str) -> set[str]:
    return {NICKNAMES.get(w, w) for w in re.findall(r"[a-z][a-z'\-]+", (name or "").lower())} - {"aka"}


def _reordered(filed: str, ballot: str) -> bool:
    """A form that writes the name surname first ('McCormick Thomas Eric, aka Tom'): the ballot surname and a
    ballot given name both appear among its words."""
    w = _words(filed)
    return bool(surname(ballot)) and surname(ballot) in w and bool(given(ballot) & w)


def _edit1(a: str, b: str) -> bool:
    """True when a and b (both 4+ letters) differ by one inserted, deleted or changed letter."""
    if a == b or min(len(a), len(b)) < 4 or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    if len(a) > len(b):
        a, b = b, a
    return any(b[:i] + b[i + 1:] == a for i in range(len(b)))


def natural(s: str) -> tuple:
    s = (s or "").replace(" (", " ~(")
    return tuple((0, int(t), "") if t.isdigit() else (1, 0, t.casefold()) for t in re.split(r"(\d+)", s) if t)


# ------------------------------------------------------------------------------------------- race types
TYPES = OrderedDict([("county", "County"), ("city", "City"), ("town", "Town"), ("township", "Township"),
                     ("school", "School board"), ("courts", "Courts"), ("state", "State legislature")])
UNIT_TYPE_RACE = {"county": "county", "court_system": "courts", "city": "city", "town": "town",
                  "township": "township", "school_corporation": "school"}
SCHOOL_PREFIX = {"South Bend Community Schools": "sbcsc", "Penn-Harris-Madison schools": "phm",
                 "School City of Mishawaka": "school-city-mishawaka", "John Glenn schools": "john-glenn",
                 "New Prairie schools": "new-prairie", "Union-North United schools": "union-north",
                 "LaVille schools": "union-north"}
SKIP_CONTEST = re.compile(r"-state-|-federal-|-us-|straight-party|public-question|retention|question|referendum")
COUNTY_ROW = {"Auditor": "County Auditor", "Sheriff": "County Sheriff", "Assessor": "County Assessor",
              "Recorder": "County Recorder", "Treasurer": "County Treasurer", "Coroner": "County Coroner",
              "Surveyor": "County Surveyor", "Prosecuting Attorney": "County Prosecutor",
              "Clerk of the Circuit Court": "Clerk of the Circuit Court"}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def contest_race(label: str) -> dict | None:
    """Ballot contest label -> the race's government, type and the office names filings use for it.
    offices: exact office_normalized values; loose: '(not stated)' variants, claimed only by a name match;
    district: the district label as filings and district maps write it ('1', 'A', 'Ward 2'), '' for none."""
    label = re.sub(r" \((?:\w+ )?primary\)$", "", label or "").strip()

    def r(unit, typ, office, loose=(), district=""):
        return {"unit": unit, "type": typ, "office": office, "offices": [office], "loose": list(loose),
                "district": district}
    m = re.match(r"^St\. Joseph County (.+)$", label)
    if m:
        rest = m.group(1)
        if rest in COUNTY_ROW:
            return r("county", "county", COUNTY_ROW[rest])
        if rest == "Judge of the Probate Court":
            return r("sjc-courts", "courts", "Probate Court Judge")
        m2 = re.match(r"^Commissioner, District (\d)$", rest)
        if m2:
            return r("county", "county", f"County Commissioner District {m2.group(1)}",
                     ["County Commissioner (district not stated)"], m2.group(1))
        m2 = re.match(r"^Council, District ([A-I])$", rest)
        if m2:
            return r("county", "county", f"County Council District {m2.group(1)}",
                     ["County Council (district not stated)"], m2.group(1))
        return None
    m = re.match(r"^(\w+) Township: Township (Trustee|Board|Assessor)$", label)
    if m:
        return r(f"{m.group(1).lower()}-township", "township", f"{m.group(1)} Township {m.group(2)}")
    m = re.match(r"^(South Bend|Mishawaka): (.+)$", label)
    if m:
        city, rest = m.group(1), m.group(2)
        uid = _slug(city)
        if rest == "Mayor":
            return r(uid, "city", f"Mayor of {city}")
        if rest == "City Clerk":
            return r(uid, "city", f"{city} City Clerk")
        m2 = re.match(r"^Common Council, (?:District (\d)|(At-Large))$", rest)
        if m2:
            if m2.group(1):
                return r(uid, "city", f"{city} Common Council District {m2.group(1)}", district=m2.group(1))
            return r(uid, "city", f"{city} Common Council At-Large")
        return None
    m = re.match(r"^Town of ([\w ]+): (.+)$", label)
    if m:
        town, rest = m.group(1), m.group(2)
        uid = _slug(town)
        if rest == "Clerk-Treasurer":
            return r(uid, "town", f"{town} Clerk-Treasurer", ["Town Clerk-Treasurer (town not stated)"])
        if rest == "Town Judge":
            return r(uid, "town", f"{town} Town Court Judge")
        m2 = re.match(r"^Town Council, (.+)$", rest)
        if m2:
            seat = m2.group(1)
            return r(uid, "town", f"{town} Town Council {seat}", [f"{town} Town Council"],
                     seat if seat.startswith("Ward ") else "")
        return None
    for prefix, uid in SCHOOL_PREFIX.items():
        if label.startswith(prefix + ": School Board"):
            seat = label.split("School Board", 1)[1].lstrip(", ").strip()
            if uid == "sbcsc":
                m2 = re.match(r"^(?:District )?(\d)$", seat)
                if m2:
                    return r(uid, "school", f"South Bend Community School Corporation Board District {m2.group(1)}",
                             district=m2.group(1))
                return r(uid, "school", "South Bend Community School Corporation Board At-Large")
            if uid == "phm":
                m2 = re.match(r"^(\w+) Township$", seat)
                name = f"Penn-Harris-Madison School Board, {m2.group(1)} Township seat" if m2 else \
                    f"Penn-Harris-Madison School Board, {seat} seat"
                return r(uid, "school", name, ["Penn-Harris-Madison School Board (seat not stated)"])
            if uid == "school-city-mishawaka":
                return r(uid, "school", "School City of Mishawaka School Board")
            return r(uid, "school", f"{prefix.replace(' schools', '')} School Board, {seat}")
    return None


# ------------------------------------------------------------------------------------------- races
def _expected_types(ed, office: str, unit: str, cycle: str) -> list[str]:
    for c in ed.table("cf_coverage"):
        if c["office_normalized"] == office and c["unit_id"] == unit and c["cycle"] == cycle:
            return [t.strip() for t in (c.get("expected_report_types") or "").split(";") if t.strip()]
    return list(EXPECTED.get(cycle, []))


def _int(v, default=1) -> int:
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return default


def build_races(ed, rows: list[dict]) -> list[dict]:
    """Every local race on the 2023, 2024 and 2026 ballots (general election, and primaries for the same office),
    with each candidate's committees and whole-cycle figures. Each committee's cycle is counted in one race only."""
    out = []
    claimed: dict[tuple, str] = {}
    for cycle, (pid, gid) in CYCLE_ELECTIONS.items():
        spec = cycle_spec(ed, cycle)
        if not spec:
            ed.warnings.append(f"campaigns map: election {gid} or {pid} missing; its races are left out")
            continue
        generals, prims = OrderedDict(), OrderedDict()
        for c in ed.contests.values():
            if c["election_id"] == gid:
                generals[c["contest_id"][len(gid) + 1:]] = c
            elif c["election_id"] == pid:
                prims.setdefault(re.sub(r"-(d|r|l|o)$", "", c["contest_id"][len(pid) + 1:]), []).append(c)
        bases = list(generals) + [b for b in prims if b not in generals]
        for base in bases:
            g, ps = generals.get(base), prims.get(base, [])
            lead = g or ps[0]
            info = contest_race(lead["label"])
            if info is None:
                if not SKIP_CONTEST.search(lead["contest_id"]):
                    ed.warnings.append(f"campaigns map: contest {lead['contest_id']} ({lead['label']!r}) has no race "
                                       "mapping; left off the map and area pages")
                continue
            if info["unit"] not in ed.units:
                ed.warnings.append(f"campaigns map: contest {lead['contest_id']} maps to unknown unit {info['unit']}")
                continue
            out.append(_race(ed, rows, spec, info, g, ps, gid, pid, base, claimed))
    return out


def _race(ed, rows, spec, info, g, ps, gid, pid, base, claimed) -> dict:
    cycle = spec["cycle"]
    rid = g["contest_id"] if g else f"{pid}-{base}"
    cands: list[dict] = []

    def add(name, party, ballot, contest_id):
        for c in cands:
            if same_person(c["name"], name):
                c["contests"].append(contest_id)
                if ballot == "general" and c["ballot"] != "general":
                    c["ballot"], c["name"], c["party"] = "general", name, party or c["party"]
                return
        cands.append({"name": name, "party": (party or "").strip(), "party_from": "ballot" if party else "",
                      "ballot": ballot, "contests": [contest_id], "keys": [], "elsewhere": ""})
    for r in (g["rows"] if g else []):
        if r["candidate"] not in ("YES", "NO"):
            add(r["candidate"], r["party"], "general", g["contest_id"])
    for p in ps:
        for r in p["rows"]:
            if r["candidate"] not in ("YES", "NO"):
                add(r["candidate"], r["party"] or p.get("party_primary", ""), "primary", p["contest_id"])
    exact, loose = set(info["offices"]), set(info["loose"])
    pool = [r for r in rows if money_cycle(r) == cycle and r["office_normalized"] in exact | loose]
    keys: OrderedDict = OrderedDict()
    for r in sorted(pool, key=lambda r: (r["_label"].casefold(), r["_key"], r.get("period_to") or "")):
        keys.setdefault(r["_key"], []).append(r)
    taken: set[str] = set()
    for c in cands:
        sur, giv = surname(c["name"]), given(c["name"])
        ks = [k for k, rs in keys.items() if k not in taken and any(surname(x["candidate"]) == sur for x in rs)]
        if len(ks) > 1:
            ks = [k for k in ks if any(given(x["candidate"]) & giv for x in keys[k])]
        # a filing that names no district or seat joins a race only on a full name match
        ks = [k for k in ks if any(x["office_normalized"] in exact for x in keys[k])
              or any(given(x["candidate"]) & giv for x in keys[k])]
        c["keys"] = ks
        taken.update(ks)
        if not ks:
            other = sorted({x["_office"] for x in rows if money_cycle(x) == cycle and same_person(x["candidate"], c["name"])
                            and x["office_normalized"] not in exact | loose})
            c["elsewhere"] = "; ".join(other)
    # a surname one letter off (a slip on the form or the ballot), same given name, filed for exactly this office
    for c in cands:
        if c["keys"]:
            continue
        near = [k for k, rs in keys.items() if k not in taken and any(
            x["office_normalized"] in exact
            and (given(x["candidate"]) & given(c["name"]) and _edit1(surname(x["candidate"]), surname(c["name"]))
                 or _reordered(x["candidate"], c["name"]))
            for x in rs)]
        if len(near) == 1:
            c["keys"] = near
            c["elsewhere"] = ""
            c["spelled"] = Counter(x["candidate"] for x in keys[near[0]]).most_common(1)[0][0]
            taken.update(near)
    for k, rs in keys.items():
        if k in taken or not any(x["office_normalized"] in exact for x in rs):
            continue
        name = Counter(x["candidate"] for x in rs if x["candidate"]).most_common(1)
        party = Counter(x["party"] for x in rs if x["party"]).most_common(1)
        cands.append({"name": name[0][0] if name else rs[0]["_label"], "party": party[0][0] if party else "",
                      "party_from": "form" if party else "", "ballot": "none", "contests": [], "keys": [k],
                      "elsewhere": ""})
        taken.add(k)
    total = raised = 0
    by_party: dict = defaultdict(int)
    reasons: list[str] = []
    counted_ids: list[str] = []
    listed_ids: list[str] = []
    n_with = 0
    for c in cands:
        c["committees"] = []
        for k in c["keys"]:
            krows = keys[k]
            if (k, cycle) in claimed and claimed[(k, cycle)] != rid:
                ed.warnings.append(f"campaigns map: committee {k} ({cycle}) matched to {claimed[(k, cycle)]} and {rid}; "
                                   "counted only in the first")
                continue
            claimed[(k, cycle)] = rid
            off = Counter(x["office_normalized"] for x in krows).most_common(1)[0][0]
            unit = next((x["unit_id"] for x in krows if x["unit_id"]), info["unit"])
            in_primary = any(cid.startswith(pid + "-") for cid in c["contests"])
            ballot = "general-only" if c["ballot"] == "general" and not in_primary else c["ballot"]
            s = committee_summary(krows, spec, _expected_types(ed, off, unit, cycle), ballot)
            s["label"] = krows[0]["_label"]
            s["moved_out"] = moved_out(rows, k, cycle)
            for x in s["moved_out"]:
                s["flags"].add("date-read")
                s["notes"].append(f"Doc {_doc(x)} is dated {period_words(x)}, which would put it in this cycle, but the "
                                  f"transcription note says {date_fix(x)['note']}, so it is counted in the "
                                  f"{money_cycle(x)} cycle instead.")
            c["committees"].append(s)
            counted_ids += [x["filing_id"] for x in s["counted"]]
            listed_ids += [x["filing_id"] for x in krows]
        cs = c["committees"]
        c["spent"] = None if not cs or any(s["spent"] is None for s in cs) else sum(s["spent"] for s in cs)
        c["raised"] = None if not cs or any(s["raised"] is None for s in cs) else sum(s["raised"] for s in cs)
        c["missing"] = [m for s in cs for m in s["missing"]]
        c["flags"] = set().union(*(s["flags"] for s in cs)) if cs else set()
        c["latest_to"] = max((s["latest_to"] for s in cs), default="")
        c["cash"] = sum(s["cash"] for s in cs) if cs and all(s["cash"] is not None for s in cs) else None
        if not c["party"] and cs:
            fp = Counter(x["party"] for s in cs for x in s["counted"] if x["party"]).most_common(1)
            if fp:
                c["party"], c["party_from"] = fp[0][0], "form"
        if cs:
            n_with += 1
        if c["spent"] is not None:
            total += c["spent"]
            by_party[c["party"]] += c["spent"]
        if c["raised"] is not None:
            raised += c["raised"]
        who = c["name"]
        if not cs:
            if c["ballot"] != "none":
                reasons.append(f"No reports on file for {who}" + (" under this office" if c["elsewhere"] else "") + ".")
        else:
            if c["missing"]:
                reasons.append(f"{who}: " + ", ".join(slot_label(m, spec) for m in c["missing"]) + " report"
                               + ("s" if len(c["missing"]) > 1 else "") + " not on file.")
            if c["spent"] is None:
                reasons.append(f"{who}: reports overlap, so they aren't added up.")
            if "blank" in c["flags"]:
                reasons.append(f"{who}: a report leaves the expenditures line blank.")
            if "unreadable" in c["flags"]:
                reasons.append(f"{who}: a report can't be read.")
            if "date-conflict" in c["flags"]:
                reasons.append(f"{who}: the dates on two reports disagree with their figures or cash; both are "
                               "counted (see the notes on the reports).")
            if "date-doubt" in c["flags"]:
                reasons.append(f"{who}: a date on a report may be miswritten (see the notes on the reports).")
    general = [c for c in cands if c["ballot"] == "general"]
    vote_for = _int(g.get("vote_for"), 1) if g else 1
    party_counts = count_parties(cands)
    latest_to = max((c["latest_to"] for c in cands), default="")
    return {"id": rid, "eid": gid if g else pid, "general_eid": gid, "cycle": cycle, "spec": spec,
            "date": spec["general"], "unit": info["unit"], "area": area_id(info["unit"]), "type": info["type"],
            "office": info["office"], "offices": info["offices"], "loose": info["loose"], "district": info["district"],
            "candidates": cands, "spent": total if n_with else None, "raised": raised if n_with else None,
            "by_party": OrderedDict(sorted(by_party.items(), key=lambda kv: (kv[0] == "", kv[0]))),
            "party_counts": party_counts,
            "complete": not reasons and n_with > 0, "reasons": reasons, "n_with": n_with,
            "counted_ids": counted_ids, "listed_ids": listed_ids, "vote_for": vote_for,
            "uncontested": bool(g) and len(general) <= vote_for, "on_general": bool(g), "latest_to": latest_to}


def moved_out(rows: list[dict], key: str, cycle: str) -> list[dict]:
    """A committee's reports whose written dates put them in this cycle but which the money model counts in another
    (date_fix)."""
    return [r for r in rows if r["_key"] == key and cycle_of(r) == cycle and money_cycle(r) != cycle]


def _party_key(p: str) -> tuple:
    return (p == "", p)


def count_parties(cands: list[dict]) -> OrderedDict:
    """party code -> {"with": candidates whose spending is in the party's sum, "listed": candidates with reports
    on file that can't be added up, "of": every candidate of the party in the race}."""
    out: dict = {}
    for c in cands:
        k = out.setdefault(c["party"], {"with": 0, "listed": 0, "of": 0})
        k["of"] += 1
        if c["committees"] and c["spent"] is not None:
            k["with"] += 1
        elif c["committees"]:
            k["listed"] += 1
    return OrderedDict(sorted(out.items(), key=lambda kv: _party_key(kv[0])))


def party_parts(by_party: dict, counts: dict, label) -> list[str]:
    """One phrase per party: its sum and how many of its candidates the sum covers, so a party total never reads
    as complete when filers are missing. label(code) gives the party's display name."""
    out = []
    for p, k in counts.items():
        name = label(p) if p else "Party not recorded"
        of = f"{k['of']} candidate{'s' if k['of'] != 1 else ''}"
        if p in by_party:
            t = f"{name} {usd(by_party[p])}: {k['with']} of {of} with reports"
        else:
            t = f"{name}: no reports added for its {of}"
        if k["listed"]:
            t += f" ({k['listed']} more with reports that can't be added up)"
        out.append(t)
    return out


# ------------------------------------------------------------------------------------------- areas
SPECIAL_AREAS = {"county": "county", "sjc-courts": "courts"}
OTHER_AREA = "other-committees"
STATE_AREA = "state-legislature"


def area_id(unit_id: str) -> str:
    return SPECIAL_AREAS.get(unit_id, unit_id)


def area_unit(aid: str) -> str:
    return {v: k for k, v in SPECIAL_AREAS.items()}.get(aid, aid)


def area_ids(tables_units: list[dict]) -> list[str]:
    """Every area page id, in TYPES order then name. Takes the units table (the sitemap calls it before the
    Edition indexes are built)."""
    out = []
    for typ in TYPES:
        if typ == "state":
            out.append(STATE_AREA)
            continue
        units = [u for u in tables_units if UNIT_TYPE_RACE.get(u["unit_type"]) == typ]
        for u in sorted(units, key=lambda u: natural(u["name"])):
            out.append(area_id(u["unit_id"]))
    out.append(OTHER_AREA)
    return out


def race_sort(r: dict) -> tuple:
    return (-r["date"].toordinal(), 1 if r["district"] else 0, natural(r["office"]))


def build_areas(ed, rows: list[dict], races: list[dict]):
    """(areas, other_rows). areas: area id -> {name, type, races (newest election first), latest-election totals,
    other: office -> rows not in a race}. Every cf_local row is placed exactly once: in a race (counted, or listed
    with the reason it isn't added), in its area's other filings (another cycle, or an office with no race in the
    guide's results), or in other_rows (party, PAC and issue committees, and filings naming no office or government)."""
    areas = OrderedDict()
    for aid in area_ids(ed.tables["units"]):
        if aid in (OTHER_AREA, STATE_AREA):
            continue
        u = ed.units[area_unit(aid)]
        areas[aid] = {"id": aid, "unit": u["unit_id"], "name": u["name"], "type": UNIT_TYPE_RACE[u["unit_type"]],
                      "races": [], "other": OrderedDict()}
    for r in sorted(races, key=race_sort):
        areas[r["area"]]["races"].append(r)
    placed = {fid for r in races for fid in r["listed_ids"]}
    other_rows = []
    for row in rows:
        if row["filing_id"] in placed:
            continue
        aid = area_id(row["unit_id"]) if row["unit_id"] else ""
        if aid in areas and row["_group"] not in ("noncand", "none"):
            areas[aid]["other"].setdefault(row["office_normalized"], []).append(row)
        else:
            other_rows.append(row)
    for a in areas.values():
        a["other"] = OrderedDict(sorted(a["other"].items(), key=lambda kv: natural(kv[0])))
        el = OrderedDict()
        for r in a["races"]:
            el.setdefault(r["general_eid"], []).append(r)
        a["elections"] = el
        latest = next(iter(el.values()), [])
        a["latest"] = next(iter(el), None)
        a["latest_races"] = latest
        withr = [r for r in latest if r["spent"] is not None]
        a["spent"] = sum(r["spent"] for r in withr) if withr else None
        a["raised"] = sum(r["raised"] for r in withr if r["raised"] is not None) if withr else None
        bp: dict = defaultdict(int)
        for r in withr:
            for p, v in r["by_party"].items():
                bp[p] += v
        a["by_party"] = OrderedDict(sorted(bp.items(), key=lambda kv: (kv[0] == "", kv[0])))
        pc: dict = {}
        for r in latest:
            for p, k in r["party_counts"].items():
                d = pc.setdefault(p, {"with": 0, "listed": 0, "of": 0})
                for f in d:
                    d[f] += k[f]
        a["party_counts"] = OrderedDict(sorted(pc.items(), key=lambda kv: _party_key(kv[0])))
        a["complete"] = bool(latest) and all(r["complete"] for r in latest)
        a["n_candidates"] = sum(len(r["candidates"]) for r in latest)
        a["n_with"] = sum(r["n_with"] for r in latest)
        a["latest_to"] = max((r["latest_to"] for r in latest), default="")
    return areas, other_rows


# ------------------------------------------------------------------------------------------- pages
HOW_PAGE = "money/campaigns/how-it-works/index.html"
ALL_PAGE = "money/campaigns/all-filings/index.html"
INDEX_PAGE = "money/campaigns/index.html"


def area_path(aid: str) -> str:
    return f"money/campaigns/{aid}/index.html"


def area_title(aid: str, units: dict) -> str:
    if aid == STATE_AREA:
        return "State legislature"
    if aid == OTHER_AREA:
        return "Party, PAC and other committees"
    u = units.get(area_unit(aid))
    return u["name"] if u else aid


def campaign_entries(units_rows: list[dict]) -> list[tuple]:
    """Sitemap Entry arguments for the campaign pages other than the index (civic/sitemap.py adds them)."""
    units = {u["unit_id"]: u for u in units_rows}
    out = [(HOW_PAGE, "How campaign finance reporting works", "How reporting works",
            "Who files, the CFA-4 form, how the guide read the scans, how complete the record is, and how it adds up a "
            "campaign.", "mixed", "", [("obligations", "Campaign-finance obligations"),
                                         ("public", "What's public and what isn't")]),
           (ALL_PAGE, "Every local campaign filing", "All filings",
            "Every local campaign-finance report read from the county's scans, filterable, with Copy CSV, and the "
            "large-contribution notices.", "county", "", [])]
    for aid in area_ids(units_rows):
        name = area_title(aid, units)
        if aid == STATE_AREA:
            desc = ("State legislators' campaign committees for districts in the county, by filing year (not race totals).")
        elif aid == OTHER_AREA:
            desc = "Party, PAC and issue committees, and filings that name no office or no government."
        else:
            desc = f"Campaign money in {name} races: each race, its candidates and every report on file."
        out.append((area_path(aid), f"Campaign money: {name}", name, desc, "county", "", []))
    return out
