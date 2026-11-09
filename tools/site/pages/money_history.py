"""Campaign money history (added 2026-11-09). Nick: "the campaign finance history of every candidate, race, office,
etc in St. Joseph county election history for what we can find ... the user will be able to see the history when
they drill down into a specific seat/candidate/race."

Two views, both built from the same filings model as the race cards (pages/campaigns.py cf_all), so every figure
matches the card it sits beside:

* committee history: every report one committee filed that the guide has, in date order, across every election
  cycle, with the cycle totals (counted by the same rules as the race cards) and a report-by-report chart. Each
  committee's history is drawn once, on its home page (the area page of its newest race; else the area page holding
  its other filings; else the party/PAC page), at the first place it appears there; everywhere else it appears
  (another race card, the other-reports list, the officeholders page) links to it.
* seat history: every election for one seat in the guide's results (back to 2010, and a few older mayoral races),
  each with its result and, where reports are on file, the money all candidates reported.

The county's posted local reports begin with the 2023 annual reports (research/campaign-finance-county-filings.md);
earlier elections say so instead of showing $0. When older filings are added to cf_local.csv, both views pick them up
(the cycle model in civic/campaign_money.py also needs the older cycles then)."""
from __future__ import annotations

import re
from collections import OrderedDict, defaultdict

from civic import campaign_money as cm
from civic.charts import period_money
from civic.components import data_table, name_with_form_party, name_with_party, status_badge
from civic.data import fmt_date
from civic.html import Markup, h

from . import campaigns as cf

POSTED_FROM = ("The county's posted reports begin with the 2023 annual reports; reports for earlier elections are not "
               "online, so the guide has no figures for them (not the same as $0).")
TYPE_SHORT = {"Annual": "Annual", "Final": "Final", "Pre-Primary": "Pre-primary", "Pre-Election": "Pre-election",
              "Pre-General": "Pre-general", "Supplemental": "Supplemental"}


# --------------------------------------------------------------------------- where each committee's history lives
def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "committee"


def index(ed) -> dict:
    """Built once per edition: rows by committee key, where each (key, cycle) is counted, each key's home page and
    anchor."""
    got = ed.__dict__.get("_money_history")
    if got is not None:
        return got
    d = cf.cf_all(ed)
    rows = defaultdict(list)
    for r in d["model"]["rows"]:
        rows[r["_key"]].append(r)
    for rs in rows.values():
        rs.sort(key=lambda r: (cm._pt(r) or "9999", cm._pf(r) or "", r["filing_id"]))
    claim: dict[tuple, tuple] = {}
    for race in d["races"]:
        for cand in race["candidates"]:
            for s in cand["committees"]:
                claim.setdefault((s["key"], race["cycle"]), (race, cand, s))
    other_area = {}
    for aid, a in d["areas"].items():
        for rs in a["other"].values():
            for r in rs:
                other_area[r["filing_id"]] = aid
    home, anchor, used = {}, {}, set()
    for k, rs in rows.items():
        raced = sorted((v[0] for (kk, _c), v in claim.items() if kk == k), key=lambda r: r["date"], reverse=True)
        if raced:
            home[k] = cm.area_path(raced[0]["area"])
        else:
            aids = [other_area[r["filing_id"]] for r in rs if r["filing_id"] in other_area]
            home[k] = cm.area_path(aids[-1]) if aids else cm.area_path(cm.OTHER_AREA)
        a = "mh-" + _slug(rs[0]["_label"])
        n = 2
        while a in used:
            a, n = f"mh-{_slug(rs[0]['_label'])}-{n}", n + 1
        used.add(a)
        anchor[k] = a
    got = {"rows": rows, "claim": claim, "other_area": other_area, "home": home, "anchor": anchor, "cf": d}
    ed.__dict__["_money_history"] = got
    return got


def href(ed, page, key: str) -> str | None:
    ix = index(ed)
    if key not in ix["home"]:
        return None
    if ix["home"][key] == page.path:
        return "#" + ix["anchor"][key]
    if ix["home"][key] not in page.site.by_path:
        return None
    return page.rel(ix["home"][key]) + "#" + ix["anchor"][key]


def span_words(ed, key: str) -> str:
    """'5 reports, 2023 to 2026' for a committee."""
    rs = index(ed)["rows"].get(key, [])
    ys = sorted({y for y in (cm.money_year(r) for r in rs) if y})
    n = len(rs)
    when = (f", {ys[0]}" if len(ys) == 1 else f", {ys[0]} to {ys[-1]}") if ys else ""
    return f"{n} report{'s' if n != 1 else ''}{when}"


def link(ed, page, key: str, lead: str = "Money history") -> Markup | None:
    """A short link to the committee's history (on this page or another)."""
    u = href(ed, page, key)
    if not u:
        return None
    return h("a", {"class": "cf-mh-link", "href": u}, f"{lead}: {span_words(ed, key)}")


def render(ed, page, key: str) -> Markup | None:
    """The history fold the first time the committee appears on its home page; a link everywhere else."""
    ix = index(ed)
    done = page.__dict__.setdefault("_mh_done", set())
    if ix["home"].get(key) == page.path and key not in done:
        done.add(key)
        return block(ed, page, key)
    lk = link(ed, page, key, "This committee's money history")
    return h("p", {"class": "cf-sub cf-mh-elsewhere"}, lk) if lk else None


# --------------------------------------------------------------------------- one committee's history
def _parts(ed, key: str) -> list[dict]:
    """The committee's reports cut into the pieces the guide counts: per cycle, the part counted in a race (its
    summary is the race card's own) and any remainder (counted like the other-reports list)."""
    ix = index(ed)
    by_cyc = OrderedDict()
    for r in ix["rows"][key]:
        by_cyc.setdefault(cm.money_cycle(r), []).append(r)
    out = []
    for cyc, rs in by_cyc.items():
        spec = cm.cycle_spec(ed, cyc)
        got = ix["claim"].get((key, cyc))
        rest = rs
        if got:
            race, cand, s = got
            out.append({"cycle": cyc, "spec": race["spec"], "s": s, "race": race, "cand": cand})
            ids = {it["row"]["filing_id"] for it in s["items"]}
            rest = [r for r in rs if r["filing_id"] not in ids]
        if not rest:
            continue
        if spec is None:
            s = {"items": [{"row": r, "slot": None, "counted": False, "why": "no-period", "notes": []} for r in rest],
                 "basis": [], "spent": None, "raised": None, "cash": None, "cash_why": "", "notes": [],
                 "counted": [], "expected": [], "on_file": [], "missing": [], "flags": set()}
            out.append({"cycle": cyc, "spec": None, "s": s, "race": None, "cand": None})
            continue
        off = max(set(x["office_normalized"] for x in rest), key=[x["office_normalized"] for x in rest].count)
        s = cm.committee_summary(rest, spec, cm._expected_types(ed, off, rest[0]["unit_id"], cyc), "none")
        out.append({"cycle": cyc, "spec": spec, "s": s, "race": None, "cand": None,
                    "area": ix["other_area"].get(rest[0]["filing_id"])})
    out.sort(key=lambda p: (p["spec"] is None, p["spec"]["general"] if p["spec"] else None))
    return out


def _where(ed, page, p) -> Markup:
    if p["race"]:
        r = p["race"]
        path = cm.area_path(r["area"])
        u = f"#r-{r['id']}" if path == page.path else (page.rel(path) + f"#r-{r['id']}" if path in page.site.by_path else None)
        t = f"counted in the race for {r['office']}, {r['general_eid'][:4]}"
        return h("a", {"href": u}, t) if u else t
    if p["spec"] is None:
        return "not placed in a cycle: no period written on the form"
    aid = p.get("area")
    path = cm.area_path(aid) if aid else cm.area_path(cm.OTHER_AREA)
    t = "listed with the other reports" if aid else "listed with the party, PAC and other committees"
    if path == page.path:
        return t
    return h("a", {"href": page.rel(path)}, t) if path in page.site.by_path else t


def _x_labels(r: dict) -> tuple[str, str]:
    types = [TYPE_SHORT.get(t, t) for t in (r.get("report_type") or "").split("; ") if t]
    t1 = types[0] if types else "Report"
    if len(t1) > 12:
        t1 = t1[:11] + "."
    to = cm._pt(r)
    t2 = ""
    if to:
        try:
            y, m = int(to[:4]), int(to[5:7])
            t2 = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][m - 1] + f" {y}"
        except ValueError:
            t2 = to
    return t1, t2


def _cell(v, from_ytd: bool) -> str:
    if v is None:
        return "blank on the form"
    return cm.usd(v) + (" (year-to-date column)" if from_ytd else "")


def block(ed, page, key: str) -> Markup:
    from .campaign_pages import _in_totals, doc_or_type   # page helpers (imported here: campaign_pages imports this)
    ix = index(ed)
    rs = ix["rows"][key]
    label = rs[0]["_label"]
    names = [r["candidate"] for r in rs if r["candidate"]]
    parties = [r["party"] for r in rs if r["party"]]
    who = name_with_form_party(max(set(names), key=names.count), max(set(parties), key=parties.count) if parties else "",
                               cf._records_party(ed, max(set(names), key=names.count), "2026")) if names else None
    parts = _parts(ed, key)
    lines, points, trows = [], [], []
    # the first counted report of each calendar year: its year-to-date columns cover the same span as its period,
    # so a blank "this period" line can be read from them (the cycle totals do the same)
    firsts = {}
    for p in parts:
        for it in p["s"]["items"]:
            if it.get("counted"):
                y = cm.money_year(it["row"])
                if y and (y not in firsts or (cm._pt(it["row"]) or "") < (cm._pt(firsts[y]) or "")):
                    firsts[y] = it["row"]

    def fig(r, col, ycol):
        v = cm.cents(r[col])
        if v is None and firsts.get(cm.money_year(r)) is r and cm.cents(r[ycol]) is not None:
            return cm.cents(r[ycol]), True
        return v, False
    for p in parts:
        s, spec = p["s"], p["spec"]
        if spec is not None:
            spent = cm.usd(s["spent"]) if s["spent"] is not None else "not added up (overlapping reports)"
            raised = cm.usd(s["raised"]) if s["raised"] is not None else "not added up"
            cash = cm.usd(s["cash"]) if s["cash"] is not None else (s.get("cash_why") or "not shown")
            n = len(s["items"])
            lines.append(h("li", None, h("strong", None, f"{spec['cycle']} cycle: "),
                           f"{spent} spent, {raised} raised; cash on hand at the latest report {cash}. "
                           f"{n} report{'s' if n != 1 else ''}; ", _where(ed, page, p), "."))
        else:
            lines.append(h("li", None, h("strong", None, "Period not written: "),
                           f"{len(s['items'])} report(s) not placed in a cycle."))
        for it in s["items"]:
            r = it["row"]
            t1, t2 = _x_labels(r)
            per = cf.period_text(r)
            counted = bool(it.get("counted")) and r.get("transcription_status") != "unreadable"
            (rv, ry), (sv, sy), (cv, cy) = (fig(r, "receipts_period", "receipts_ytd"),
                                            fig(r, "expenditures_period", "expenditures_ytd"),
                                            fig(r, "cash_end_period", "cash_end_ytd"))
            from_ytd = ry or sy or cy
            if counted:
                points.append({"x": t1, "x2": t2, "raised": rv, "spent": sv, "cash": cv,
                               "tip": f"{doc_or_type(r)}, {per}" + (" (period lines blank; read from the year-to-date "
                                                                     "columns)" if from_ytd else ""),
                               "_sort": (cm._pt(r) or "9999", cm._pf(r) or "")})
            trows.append((cm._pt(r) or "9999", [spec["cycle"] if spec else "not placed", doc_or_type(r), per,
                          _cell(rv, ry), _cell(sv, sy), _cell(cv, cy), cf.cf_badge_short(r["transcription_status"], page),
                          ("In the chart; " if counted else "Not in the chart; ") + (_in_totals(it, s) if spec else "No: no period written"),
                          cf.doc_link(ed, r)]))
    points.sort(key=lambda p: p.pop("_sort"))
    trows = [r for _k, r in sorted(trows, key=lambda x: x[0])]
    aid = index(ed)["anchor"][key]
    headers = ["Cycle", "Report (box marked)", "Period", "Raised in the period", "Spent in the period",
               "Cash on hand at close", "Status", "In the chart and totals", "Form"]
    if points:
        chart = period_money(f"{aid}-chart", f"{label}: money report by report", points,
                             subtitle="Each report's own figures as written on it, in date order. Hover or focus a "
                                      "report for its numbers.",
                             note="Columns are each report's “this period” lines as written (when those are blank on the first "
                                  "report of a year, its year-to-date columns, which cover the same span). The cycle totals above "
                                  "follow the guide's adding rules (an amendment replaces the report it amends; some "
                                  "years use a year-to-date figure), so the columns may not add up to them exactly. "
                                  "Reports left out of the totals are not drawn; the table lists every report.",
                             page=page, headers=headers, rows=trows, numeric=(3, 4, 5))
    else:
        chart = data_table(f"{aid}-table", headers, trows, caption=f"{label}: every report on file",
                           numeric=(3, 4, 5), min_width="64rem", copy=False)
    return h("details", {"class": "cf-history", "id": aid},
             h("summary", None, f"Money history: {label} ({span_words(ed, key)})"),
             h("div", {"class": "cf-history-body"},
               h("p", {"class": "cf-sub"}, "Candidate: ", who) if who else None,
               h("p", None, "Every report this committee filed that the guide has, across every election cycle. ",
                 status_badge("computed", page, "Cycle totals are sums of the reports, by the same rules as the race "
                                                "cards."), " ", POSTED_FROM),
               h("ul", {"class": "cf-history-cycles"}, lines), chart))


# --------------------------------------------------------------------------- one seat across elections
def seat_key(info: dict) -> tuple:
    return (info["unit"], info["office"], info["district"])


def seat_contests(ed) -> dict:
    """seat key -> [general-election contests for that seat, newest first], from every election in the results."""
    got = ed.__dict__.get("_seat_contests")
    if got is not None:
        return got
    out = defaultdict(list)
    for c in ed.contests.values():
        el = ed.elections.get(c["election_id"]) or {}
        if not c["election_id"].endswith("g"):
            continue
        info = cm.contest_race(c["label"])
        if info is None:
            continue
        out[seat_key(info)].append((el.get("date") or c["election_id"][:4], c))
    got = {k: [c for _d, c in sorted(v, key=lambda x: x[0], reverse=True)] for k, v in out.items()}
    ed.__dict__["_seat_contests"] = got
    return got


def reported(ed) -> dict:
    """cf_reported.csv (added 2026-11-09): campaign figures for pre-2023 local races as reported in the news, checked
    against the article or digest text. general contest id -> [(contest, [rows])], a primary's rows under the same
    seat's general election that year."""
    got = ed.__dict__.get("_cf_reported")
    if got is not None:
        return got
    sc = seat_contests(ed)
    out: dict[str, OrderedDict] = defaultdict(OrderedDict)
    for r in ed.table("cf_reported"):
        c = ed.contests.get(r["contest_id"])
        if not c:
            ed.warnings.append(f"cf_reported: unknown contest {r['contest_id']}")
            continue
        info = cm.contest_race(c["label"])
        gen = c
        if info and not c["election_id"].endswith("g"):
            gen = next((g for g in sc.get(seat_key(info), []) if g["election_id"][:4] == c["election_id"][:4]), None)
        if gen is None:
            ed.warnings.append(f"cf_reported: no general election row for {r['contest_id']}")
            continue
        out[gen["contest_id"]].setdefault(c["contest_id"], (c, []))[1].append(r)
    got = {k: list(v.values()) for k, v in out.items()}
    ed.__dict__["_cf_reported"] = got
    return got


def _reported_cell(ed, page, groups) -> Markup:
    c = page.cites
    parts = []
    for contest, rows in groups:
        which = "primary" if not contest["election_id"].endswith("g") else "general election"
        party = (contest.get("party_primary") or "").strip()
        head = f"{contest['election_id'][:4]} {('Democratic ' if party == 'D' else 'Republican ' if party == 'R' else '')}{which}"
        by: dict[str, list] = OrderedDict()
        for r in rows:
            by.setdefault(r["candidate"], []).append(r)
        items = []
        for cand, rs in by.items():
            party_txt = f" ({rs[0]['party']})" if rs[0]["party"] else ""
            figs = []
            for r in rs:
                if r["figure"] == "no report":
                    figs.append("did not file a report (per the article)")
                else:
                    cents = cm.cents(r["amount"])
                    amt = cm.usd(cents)[:-3] if cents is not None and cents % 100 == 0 else cm.usd(cents)
                    # a rounded figure keeps the source's own words ("nearly $245,000"), and its note
                    amt = r.get("as_reported") or amt
                    figs.append(f"{r['figure']} {amt}, {r['covers']}"
                                + (f" ({r['notes'].rstrip('.')})" if r.get("as_reported") and r.get("notes") else ""))
            items.append(h("li", None, f"{cand}{party_txt}: " + "; ".join(figs) + ". ",
                           status_badge(rs[0]["status"], page), c.cite(rs[0]["source_ids"])))
        parts.append(h("p", {"class": "cf-sub"}, h("strong", None, f"Reported in the news, {head}:")))
        parts.append(h("ul", {"class": "cf-reported"}, items))
    return h("div", None, h("span", None, "Reports not posted online."), parts)


def seat_block(ed, page, race: dict) -> Markup | None:
    """'This seat over time' on a race card: every general election for the seat in the guide's results, its result,
    and the money all candidates reported where reports are on file."""
    from .campaign_pages import _el_title, _result_words
    contests = seat_contests(ed).get(seat_key(race), [])
    if not contests:
        return None
    by_id = {r["id"]: r for r in index(ed)["cf"]["races"]}
    news = reported(ed)
    rows, n_money = [], 0
    for c in contests:
        r = by_id.get(c["contest_id"])
        title = _el_title(ed, c["election_id"])
        if r and r["id"] == race["id"]:
            el = h("span", None, title, h("span", {"class": "cf-sub"}, "this race"))
        elif r:
            el = h("a", {"href": f"#r-{r['id']}"}, title)
        else:
            el = title
        if r and r["spent"] is not None:
            n_money += 1
            money = (f"{cm.usd(r['spent'])} spent, {cm.usd(r['raised'])} raised by all candidates"
                     + ("" if r["complete"] else " (incomplete: a floor)"))
        elif r:
            money = "No reports on file for any candidate (not the same as $0)"
        elif c["contest_id"] in news:
            n_money += 1
            money = _reported_cell(ed, page, news[c["contest_id"]])
        else:
            money = "Reports not posted online"
        rows.append([el, _result_words(ed, c), money])
    years = [c["election_id"][:4] for c in contests]
    span = years[0] if len(years) == 1 else f"{years[-1]} to {years[0]}"
    notes = [POSTED_FROM.replace("so the guide has no figures for them (not the same as $0).",
                                 "so the guide has no figures for them (not the same as $0) except where news coverage "
                                 "reported them, which are marked with their source.")
             if any(c["contest_id"] in news for c in contests) else POSTED_FROM]
    if race["district"] or "District" in race["office"]:
        notes.append("District lines are redrawn after each census, so an older race under the same district name may "
                     "have covered a different area.")
    tid = f"sh-{race['id']}"
    return h("details", {"class": "cf-seat-history", "id": tid},
             h("summary", None, f"This seat over time: {len(contests)} election{'s' if len(contests) != 1 else ''}, "
                                f"{span}" + (f"; money on file or reported for {n_money}" if n_money else "")),
             data_table(f"{tid}-t", ["Election", "Result", "Money reported"], rows,
                        caption=f"{race['office']}: every general election in the guide's results", copy=False,
                        min_width="44rem"),
             h("p", {"class": "cf-sub"}, " ".join(notes)))


# --------------------------------------------------------------------------- officeholders
def holder_links(ed, page, unit_id: str, person: str, office_title: str = "") -> list[tuple[str, str]]:
    """[(committee name, href)] for an officeholder's own campaign committees, matched by name inside the office's
    government (the committee's filings name that government, or a race for it lists the committee under the
    person). A person can have several (William Redman: a sheriff committee and a 2026 commissioner committee), so all
    are returned: the ones whose office shares the most words with the office held first, then the newest."""
    ix = index(ed)
    aid = cm.area_id(unit_id)
    keys = set()
    for race in ix["cf"]["races"]:
        if race["area"] != aid:
            continue
        for cand in race["candidates"]:
            if cm.same_person(cand["name"], person):
                keys.update(s["key"] for s in cand["committees"])
    for k, rs in ix["rows"].items():
        if any(r["unit_id"] and cm.area_id(r["unit_id"]) == aid and r["candidate"] and cm.same_person(r["candidate"], person)
               for r in rs):
            keys.add(k)
    want = set(re.findall(r"[a-z]+", office_title.lower()))

    def rank(k):
        offs = {r["office_normalized"] for r in ix["rows"][k]}
        overlap = max((len(want & set(re.findall(r"[a-z]+", o.lower()))) for o in offs), default=0)
        return (-overlap, "".join(chr(0x10FFFF - ord(c)) for c in max(cm._pt(r) or "" for r in ix["rows"][k])))
    out = []
    for k in sorted(keys, key=rank):
        u = href(ed, page, k)
        if u:
            out.append((ix["rows"][k][0]["_label"], u))
    return out


# --------------------------------------------------------------------------- state legislators (filing years)
STATE_PAGE = cm.area_path(cm.STATE_AREA)


def legislators(ed) -> list[dict]:
    """Every state House and Senate candidate with a committee in cf_state.csv (13 committees, 2016-2026) or
    cf_state_history.csv (tools/build_cf_state_history.py: 2000-2026 for every legislative candidate on the guide's
    ballots), one entry per person: name, party, districts, rows (each with its file), anchor."""
    got = ed.__dict__.get("_legislators")
    if got is not None:
        return got
    people: list[dict] = []
    for name, rows in (("cf_state", ed.table("cf_state")), ("cf_state_history", ed.table("cf_state_history"))):
        for r in rows:
            p = next((x for x in people if cm.same_person(x["name"], r["candidate"])), None)
            if p is None:
                p = {"name": r["candidate"], "party": r["party"], "now": "", "ballot": "", "rows": []}
                people.append(p)
            if name == "cf_state":
                p["name"], p["now"] = r["candidate"], r["district"]
            elif not p["ballot"]:
                p["ballot"] = r.get("ballot_districts", "")
            p["party"] = p["party"] or r["party"]
            p["rows"].append({**r, "_file": name})
    used = set()
    for p in people:
        p["rows"].sort(key=lambda r: (int(r["year"]), r["committee"].casefold()))
        p["years"] = sorted({int(r["year"]) for r in p["rows"]})
        a = "lh-" + _slug(p["name"])
        while a in used:
            a += "-2"
        used.add(a)
        p["anchor"] = a
    people.sort(key=lambda p: (-p["years"][-1], cm.surname(p["name"]), p["name"]))
    ed.__dict__["_legislators"] = people
    return people


def legislator_href(ed, page, person: str) -> str | None:
    p = next((x for x in legislators(ed) if cm.same_person(x["name"], person)), None)
    if not p or STATE_PAGE not in page.site.by_path:
        return None
    return ("" if page.path == STATE_PAGE else page.rel(STATE_PAGE)) + "#" + p["anchor"]


def legislator_block(ed, page, p: dict) -> Markup:
    by_year: dict[int, dict] = OrderedDict()
    trows = []
    for r in p["rows"]:
        y = int(r["year"])
        d = by_year.setdefault(y, {"r": 0, "e": 0, "re": False, "ee": False})
        rc, ec = cm.cents(r["receipts"]), cm.cents(r["expenditures"])
        if rc is not None:
            d["r"] += rc
            d["re"] = True
        if ec is not None:
            d["e"] += ec
            d["ee"] = True
        trows.append([str(y), r["committee"], cm.usd(rc), cm.usd(ec, "not in the data"),
                      "cf_state.csv" if r["_file"] == "cf_state" else "cf_state_history.csv",
                      status_badge(r["status"], page)])
    points = [{"x": str(y), "raised": d["r"] if d["re"] else None, "spent": d["e"] if d["ee"] else None,
               "tip": f"Filed in {y}"} for y, d in by_year.items()]
    span = f"{p['years'][0]}" if len(p["years"]) == 1 else f"{p['years'][0]} to {p['years'][-1]}"
    where = []
    if p["now"]:
        where.append(f"committee listed under {p['now']}")
    if p["ballot"]:
        where.append(f"on the guide's ballots: {p['ballot']}")
    chart = period_money(f"{p['anchor']}-chart", f"{p['name']}: receipts and expenditures by filing year", points,
                         subtitle="Sums of the items on reports filed in each calendar year (all of the person's "
                                  "committees), not election cycles.",
                         words={"raised": "Receipts in the year", "spent": "Expenditures in the year",
                                "missing": "not in the data", "tip_raised": "Receipts", "tip_spent": "Expenditures"},
                         note="District lines were redrawn in 2011 and 2021, so years are listed by person, never under "
                              "a district.", page=page, headers=["Filing year", "Committee", "Receipts", "Expenditures",
                                                                  "File", "Status"], rows=trows, numeric=(2, 3))
    return h("details", {"class": "cf-history", "id": p["anchor"]},
             h("summary", None, name_with_party(p["name"], p["party"]),
               f" ({len(p['years'])} filing year{'s' if len(p['years']) != 1 else ''}, {span})"),
             h("div", {"class": "cf-history-body"},
               h("p", {"class": "cf-sub"}, "; ".join(where) + ".") if where else None, chart))


def same_name_links(ed, page, name: str, exclude: set | None = None) -> list:
    """Links to the money history of every committee whose filings name this person in full (civic.campaign_money
    same_person: same surname and a shared given name; a surname alone never matches), for a race card whose
    candidate has no report in the race's own cycle but filed in another cycle or for another office (added
    2026-11-09: e.g. Sonia Perez, 2023 council, whose committee's reports are 2024 annuals)."""
    ix = index(ed)
    out = []
    for k, rs in ix["rows"].items():
        if exclude and k in exclude:
            continue
        if any(r["candidate"] and cm.same_person(r["candidate"], name) for r in rs):
            lk = link(ed, page, k, rs[0]["_label"])
            if lk:
                out.append(lk)
    return out


# --------------------------------------------------------------------------- county PACs filing with the state
def state_pacs(ed) -> list[dict]:
    """cf_state_pacs.csv (tools/build_cf_state_pacs.py, added 2026-11-09): county-named PACs and party groups that file
    with the state, 2010-2026, one entry per state file number."""
    by: dict[str, dict] = OrderedDict()
    for r in ed.table("cf_state_pacs"):
        p = by.setdefault(r["file_number"], {"name": r["committee"], "type": r["committee_type"], "rows": [],
                                              "payees": r.get("top_payees_2010_2026", ""),
                                              "anchor": "sp-" + _slug(r["committee"])})
        p["rows"].append(r)
    out = list(by.values())
    for p in out:
        p["years"] = sorted(int(r["year"]) for r in p["rows"])
    out.sort(key=lambda p: (-sum(cm.cents(r["receipts"]) or 0 for r in p["rows"]), p["name"].casefold()))
    return out


def state_pac_block(ed, page, p: dict) -> Markup:
    points, trows = [], []
    for r in sorted(p["rows"], key=lambda r: int(r["year"])):
        rc, ec = cm.cents(r["receipts"]), cm.cents(r["expenditures"])
        points.append({"x": r["year"], "raised": rc, "spent": ec, "tip": f"Filed in {r['year']}"})
        trows.append([r["year"], cm.usd(rc), cm.usd(ec), status_badge(r["status"], page)])
    span = f"{p['years'][0]}" if len(p["years"]) == 1 else f"{p['years'][0]} to {p['years'][-1]}"
    payees = [x.rsplit(" ", 1) for x in p["payees"].split("; ") if x.strip()]
    chart = period_money(f"{p['anchor']}-chart", f"{p['name']}: receipts and expenditures by filing year", points,
                         subtitle="Sums of the items on reports filed in each calendar year, from the state's bulk data.",
                         words={"raised": "Receipts in the year", "spent": "Expenditures in the year",
                                "missing": "not in the data", "tip_raised": "Receipts", "tip_spent": "Expenditures"},
                         page=page, headers=["Filing year", "Receipts", "Expenditures", "Status"], rows=trows,
                         numeric=(1, 2))
    return h("details", {"class": "cf-history", "id": p["anchor"]},
             h("summary", None, p["name"], f" ({p['type'].lower()} committee; {len(p['years'])} filing year"
                                           f"{'s' if len(p['years']) != 1 else ''}, {span})"),
             h("div", {"class": "cf-history-body"},
               chart,
               h("p", {"class": "cf-sub"}, h("strong", None, "Largest payees, 2010 to 2026 (summed by name as listed): "),
                 "; ".join(f"{n} {cm.usd(cm.cents(v))}" for n, v in payees) + ".") if payees else None))
