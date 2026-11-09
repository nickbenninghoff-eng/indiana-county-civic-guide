"""Places (cities, towns, townships) and school corporations.

Pages: places/index.html, places/<unit_id>/index.html (one template per unit type; a new
edition gets its pages from its own units.csv), schools/index.html.

Optional edition data in derived/: township_places.csv (which places lie in which township),
place_conflicts.csv (offices whose sources disagree; shown as conflicts, never resolved).
"""
from __future__ import annotations

import math
import re
from functools import partial
from pathlib import Path

from civic.charts import columns, line, party_timeline, results_bars
from civic.components import (bodies_block, name_with_party, data_table, officeholder_card, party_label, scope_badge, section,
                              status_badge, callout)
from civic.data import fmt_date, fmt_int, parse_date, split_ids
from civic.answers import answer_box, place_budget_row
from civic.html import Markup, h, join
from civic.spending import money_id_for, money_in_out
from civic.tax_base import money_id as tax_base_id, tax_base_line
from civic import school_stats
from civic.map import embedded_map, load_shapes
from civic.pick_one import one_bar, one_section

from .county import CONTROL_METHOD, _contest_figure, ballot_order_note, control_by_year

KINDS = {"city": "City", "town": "Town", "township": "Township"}
PLURAL = {"city": "Cities", "town": "Towns", "township": "Townships"}
CONTEXT_IDS = ["pop_total", "median_hh_income", "poverty_pct", "owner_occupied_pct", "bachelors_plus_pct"]
BASIS = {"general_fund": "general fund", "advertised_all_funds": "all advertised funds",
         "all_funds_incl_utilities": "all funds including utilities", "gateway_reported_funds": "funds reported to Gateway"}

MEASURE = (" Order is by office and district, never by party.")


# ----------------------------------------------------------------------------- small helpers

def _short(unit) -> str:
    return re.sub(r"^(City|Town) of ", "", unit["name"])


def _union(*groups) -> str:
    seen = []
    for g in groups:
        for r in g:
            for s in split_ids(r.get("source_ids") if isinstance(r, dict) else r):
                if s not in seen:
                    seen.append(s)
    return ";".join(seen)


def _cov(level: str, text: str | None = None) -> Markup:
    label = {"covered": "Covered", "partial": "Partly covered", "none": "Not yet researched"}[level]
    return h("span", {"class": f"cov cov-{level}"}, text or label)


def _gap(item, why, how="") -> dict:
    return {"item": item, "why_missing": why, "how_to_fill": how}


def _years(d):
    p = parse_date(d)
    return p.year if p else None


def _cache(ed) -> dict:
    return ed.__dict__.setdefault("_places_cache", {})


def _conflicts(ed) -> dict:
    return {r["subject_id"]: r for r in ed.table("derived/place_conflicts")}


def _geo(ed, unit):
    """Indicator geography row (geo_id, geo_type) for a unit, matched by name; None if absent."""
    idx = _cache(ed).get("geo")
    if idx is None:
        idx = {}
        for r in ed.table("indicator_values"):
            if r["geo_type"] in ("place", "town", "county_subdivision"):
                idx[r["geo_id"]] = (r["geo_type"], r["geo_name"].lower())
        _cache(ed)["geo"] = idx
    if unit["unit_type"] == "township":
        base = re.sub(r" Township$", "", unit["name"]).lower()
        want, typ = f"{base} township", "county_subdivision"
    else:
        base = _short(unit).lower()
        # cities are geo_type "place"; incorporated towns are "town" (kept apart so community/people stays city-only)
        want, typ = f"{base} {unit['unit_type']}", ("town" if unit["unit_type"] == "town" else "place")
    for gid, (t, name) in idx.items():
        if t == typ and name.startswith(want):
            return gid
    return None


def _ind(ed, geo_id, ind_id):
    """{vintage: row} for one indicator and geography."""
    key = (geo_id, ind_id)
    m = _cache(ed).get("ind")
    if m is None:
        m = {}
        for r in ed.table("indicator_values"):
            m.setdefault((r["geo_id"], r["indicator_id"]), {})[r["vintage"]] = r
        _cache(ed)["ind"] = m
    return m.get(key, {})


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _vint_end(v):
    """Last four-digit year in a vintage label such as 'ACS 2020-2024 5-year'."""
    yrs = re.findall(r"\d{4}", v)
    return int(yrs[-1]) if yrs else 0


def _latest_acs(rows: dict):
    acs = [v for v in rows if v.startswith("ACS")]
    return rows[max(acs, key=_vint_end)] if acs else None


def _earliest_acs(rows: dict):
    acs = [v for v in rows if v.startswith("ACS")]
    return rows[min(acs, key=_vint_end)] if acs else None


def _population(ed, unit):
    gid = _geo(ed, unit)
    if not gid:
        return None
    return _latest_acs(_ind(ed, gid, "pop_total"))


def _budget_rows(ed, unit_id):
    out = []
    for r in ed.table("budgets"):
        if ed.unit_alias(r["unit_id"]) == unit_id and r.get("amount"):
            out.append(r)
    return sorted(out, key=lambda r: r["year"])


def _money(v) -> str:
    n = _num(v)
    return f"${n:,.0f}" if n is not None else ""


def _place_contests(ed, unit_id):
    """General-election contests whose id is <election>-<unit_id>-... (school contests excluded)."""
    out = []
    for c in ed.contests.values():
        if c["party_primary"]:
            continue
        rest = c["contest_id"][len(c["election_id"]) + 1:]
        if (rest == unit_id or rest.startswith(unit_id + "-")) and "-schools-" not in rest:
            out.append(c)
    return sorted(out, key=lambda c: (ed.elections[c["election_id"]]["date"], c["label"]))


def _tokens(s):
    return set(re.findall(r"[a-z0-9]+", s.lower()))


def _school_unit(ed, label):
    pre = label.split(":")[0]
    toks = _tokens(pre) - {"schools", "school"}
    best, score = None, 0
    for u in ed.units.values():
        if u["unit_type"] != "school_corporation":
            continue
        ut = _tokens(u["name"])
        if toks and toks <= ut and len(toks) > score:
            best, score = u["unit_id"], len(toks)
    return best


def _school_contests(ed, unit_id, general_only=False):
    out = []
    for c in ed.contests.values():
        if "-schools-" not in c["contest_id"]:
            continue
        if general_only and c["party_primary"]:
            continue
        if _school_unit(ed, c["label"]) == unit_id:
            out.append(c)
    return sorted(out, key=lambda c: (ed.elections[c["election_id"]]["date"], c["label"]))


def _conflict_panel(ed, page, row, extra=None) -> Markup:
    c = page.cites
    return h("aside", {"class": "callout callout-conflict", "id": f"conflict-{row['subject_id']}"},
             h("p", None, status_badge("unverified", page, "Sources disagree."), " ",
               h("strong", None, "Conflict in sources: "), row["title"]),
             h("ul", None,
               h("li", None, h("strong", None, "One source says: "), row["view_a"], c.cite(row["view_a_source_ids"])),
               h("li", None, h("strong", None, "Another source says: "), row["view_b"], c.cite(row["view_b_source_ids"]))),
             h("p", None, row["note"], c.cite(row.get("note_source_ids"))),
             h("p", {"class": "muted"}, "The guide shows both and does not pick one."), extra)


def _how_elected(o):
    t, d = o["office_type"], o["district"]
    if t == "school_board_appointed":
        return "Appointed, not elected"
    if t == "school_board_at_large" or d.lower().startswith("at-large"):
        return "All voters in the corporation"
    if re.fullmatch(r"\d+", d):
        return f"Voters in District {d}"
    return f"Voters in {d}" if d else "Not stated in sources"


# ----------------------------------------------------------------------------- shared blocks

def _offices_table(ed, page, unit, offices):
    rows = []
    for o in offices:
        ot = ed.office_type_row(o) or {}
        rows.append([o["title"],
                     h("span", None, ot.get("what_it_does", "Description not yet in the guide's data."),
                       page.cites.cite(ot.get("source_ids")) if ot else None),
                     o["seats"] or "not stated in sources",
                     f"{o['term_years']} years" if o.get("term_years") else "",
                     o.get("next_election") or "not in sources",
                     h("span", None, status_badge(o["status"], page), page.cites.cite(o["source_ids"]))])
    return data_table(f"offices-{unit['unit_id']}", ["Office", "What it does", "Seats", "Term", "Next regular election", "Status"],
                      rows, caption=f"Elected offices of {unit['name']}", numeric=(2,), min_width="48rem")


def _cards(ed, page, offices, conflicts):
    out = []
    for o in offices:
        cur, inc = ed.current_terms(o["office_id"]), ed.incoming_terms(o["office_id"])
        row = conflicts.get(o["office_id"])
        if row:
            out.append(h("article", {"class": "card holder-card card-conflict", "id": f"office-{o['office_id']}"},
                         h("h3", {"class": "card-title"}, o["title"]),
                         h("p", {"class": "holder-none"}, "Current holder disputed between sources."),
                         h("p", {"class": "holder-name"}, "Listed: ", _names(row)),
                         h("p", {"class": "holder-badges"}, status_badge("unverified", page, "Sources disagree.")),
                         h("p", {"class": "card-note"}, h("a", {"href": f"#conflict-{o['office_id']}"}, "See the conflict below"))))
        else:
            out.append(officeholder_card(ed, page, o, cur, inc))
    return h("div", {"class": "card-grid"}, out)


def _names(row):
    return row["title"]


def _control_chart(ed, page, offices, title, fid):
    legislators = [o for o in offices if o["seats"].isdigit()]
    if not offices or len(legislators) != len(offices):
        return None, "seat counts not stated in sources"
    years = control_by_year(ed, offices)
    if len(years) < 2:
        return None, "fewer than two years of officeholder data"
    total = sum(int(o["seats"]) for o in offices)
    method = CONTROL_METHOD
    src = _union(*[ed.terms_for(o["office_id"]) for o in offices])
    return party_timeline(fid, title, years, total, subtitle=f"{years[0]['year']} to {years[-1]['year']}, {total} seats",
                          note=method, page=page, cite=page.cites.cite_compact(src)), None


def _mayor_block(ed, page, unit):
    uid = unit["unit_id"]
    cs = [c for c in ed.contests.values() if not c["party_primary"] and c["contest_id"] == f"{c['election_id']}-{uid}-mayor"]
    cs.sort(key=lambda c: ed.elections[c["election_id"]]["date"])
    if not cs:
        return None
    pts, rows, statuses = [], [], []
    for c in cs:
        year = _years(ed.elections[c["election_id"]]["date"])
        win = next((r for r in c["rows"] if r["winner"] == "Y"), None)
        pct = _num(win["pct"]) if win else None
        st = win["status"] if win else c["rows"][0]["status"]
        statuses.append(st)
        label = f"{year}: {win['candidate']} ({win['party'] or 'no party'})" if win else f"{year}: winner not recorded"
        pts.append({"x": str(year), "value": pct, "tip": label + (f", {pct:.1f}%" if pct is not None else ", vote share not in source"),
                    "display": f"{pct:.1f}%" if pct is not None else None})
        cands = h("span", None, join([h("span", None, name_with_party(r["candidate"], r["party"]), " ",
                                        (f"{_num(r['pct']):.1f}%" if _num(r["pct"]) is not None else "share not in source"))
                                      for r in c["rows"]], "; "))
        rows.append([str(year),
                     (name_with_party(win["candidate"], win["party"]) if win else "not recorded"),
                     fmt_int(win["votes"]) if win and win["votes"] else "not in source",
                     f"{pct:.1f}%" if pct is not None else "not in source",
                     cands,
                     h("span", None, status_badge(st, page), page.cites.cite(";".join(dict.fromkeys(s for r in c["rows"] for s in split_ids(r["source_ids"])))))])
    breaks = [{"after": i, "label": "Source changes", "tip": "The data source changes here (secondary source before, county canvass after)."}
              for i in range(len(cs) - 1) if statuses[i] != statuses[i + 1] and "secondary" in (statuses[i], statuses[i + 1])]
    miss = [p["x"] for p in pts if p["value"] is None]
    note = ("Bars show the winning candidate's share of the vote in each mayoral general election; party and every other "
            "candidate are in the table. An uncontested race shows 100%." +
            (f" No vote share is in the source for {', '.join(miss)}; those years have no bar." if miss else "") +
            (" Years before 2011 come from a secondary source." if any(s == "secondary" for s in statuses) else ""))
    chart = columns(f"mayor-results-{uid}", f"{_short(unit)} mayor: winner's share of the vote", pts,
                    subtitle=f"{pts[0]['x']} to {pts[-1]['x']}, general elections", mark="m-ink", breaks=breaks,
                    value_fmt=lambda v: f"{v:.1f}%", note=note, page=page, headers=["Year", "Winner's share"])
    table = data_table(f"mayor-table-{uid}", ["Year", "Winner", "Winner's votes", "Share", "All candidates (ballot order)", "Status"],
                       rows, caption=f"{_short(unit)} mayoral general elections", numeric=(2, 3), min_width="46rem")
    return [chart, table]


def _boards_block(ed, page, unit):
    uid = unit["unit_id"]
    kids = {u["unit_id"] for u in ed.units.values() if uid in split_ids(u["parent_unit_ids"].replace(",", ";"))}
    own = [b for b in ed.boards if b["unit_id"] in kids | {uid}]
    name = _short(unit)
    other = [b for b in ed.boards if b not in own and unit["unit_type"] == "city" and re.search(re.escape(name), b["appointing_authorities"], re.I)]
    if not own and not other:
        return None

    def table(bs, tid, cap):
        rows = [[b["name"], b["what_it_decides"], b["seats"] or "not in sources",
                 b["appointing_authorities"] or "not in sources",
                 h("span", None, status_badge(b["status"], page), page.cites.cite(b["source_ids"]))] for b in bs]
        return data_table(tid, ["Board", "What it decides", "Seats", "Who appoints", "Status"], rows, caption=cap, min_width="44rem")
    parts = [h("p", None, "These bodies make decisions but their members are appointed, not elected. "
                          "Where the sources do not say who appoints, the table says so.")]
    if own:
        parts += [h("h3", None, f"Boards of {name} and its units"), table(own, f"boards-{uid}", f"Appointed boards: {name}")]
    if other:
        parts += [h("h3", None, f"Other boards where {name} officials appoint a seat"), table(other, f"boards-other-{uid}", f"Other boards with seats appointed by {name} officials")]
    return parts


def _results_block(ed, page, unit, latest_only=False):
    cs = _place_contests(ed, unit["unit_id"])
    if not cs:
        return None
    by = {}
    for c in cs:
        by.setdefault(c["election_id"], []).append(c)
    eids = sorted(by, key=lambda e: ed.elections[e]["date"], reverse=True)
    eids = [e for e in eids if ed.elections[e]["type"] in ("general", "municipal_general")][: 1 if latest_only else 2]
    blocks = []
    for e in eids:
        el = ed.elections[e]
        figs = [_contest_figure(ed, page, c) for c in by[e]]
        blocks.append(h("div", {"class": "results-year"},
                        h("h3", None, f"{fmt_date(el['date'], long=True)} general election ", status_badge(el["status"], page)),
                        h("div", {"class": "chart-grid"}, figs)))
    if not blocks:
        return None
    body = [h("p", None, ballot_order_note(ed, page, eids), "Candidates appear in the order the source lists them. The bar scale is 0 to 100% for every race. "
                         "Winners marked 'computed' in the data are the top vote-getters for the seats up. ",
             h("a", {"href": page.rel("elections/results/index.html")}, "All results, 2010 to 2026")), blocks]
    if latest_only:
        return [h("details", {"class": "more"}, h("summary", {"class": "btn btn-small"}, "Show most recent results"), body)]
    return body


def _context_block(ed, page, unit):
    gid = _geo(ed, unit)
    if not gid:
        return None
    rows, srcs = [], []
    for iid in CONTEXT_IDS:
        vals = _ind(ed, gid, iid)
        new = _latest_acs(vals)
        if not new:
            continue
        label = ed.table("indicators") and next((r["label"] for r in ed.table("indicators") if r["indicator_id"] == iid), iid)
        v, moe = _num(new["value"]), _num(new["moe"])
        if v is None:
            rows.append([label, "not published", "none published", new["vintage"],
                         h("span", None, status_badge("low", page, "The Census Bureau did not publish a usable estimate (insufficient sample)."),
                           page.cites.cite(new["source_ids"]))])
            srcs.append(new["source_ids"])
            continue
        money = iid == "median_hh_income"
        fmt = (lambda x: f"${x:,.0f}") if money else (lambda x: f"{x:,.0f}") if iid == "pop_total" else (lambda x: f"{x:.1f}%")
        cv = (moe / 1.645 / v * 100) if (v and moe is not None) else None
        flags = [status_badge(new["status"], page)]
        if cv is not None and cv > 30:
            flags.append(status_badge("low", page, f"CV {cv:.0f}% (above 30%): treat as unreliable."))
        rows.append([label, fmt(v), f"±{fmt(moe)}" if moe is not None else "none published",
                     new["vintage"], h("span", None, join(flags, " "), page.cites.cite(new["source_ids"]))])
        srcs.append(new["source_ids"])
    # change since 2010 (ACS 2006-2010 -> latest ACS)
    pv = _ind(ed, gid, "pop_total")
    a, b = _earliest_acs(pv), _latest_acs(pv)
    if a and b and a is not b:
        x0, x1 = _num(a["value"]), _num(b["value"])
        m = math.sqrt((_num(a["moe"]) or 0) ** 2 + (_num(b["moe"]) or 0) ** 2)
        d = x1 - x0
        inside = abs(d) <= m
        rows.append(["Population change since 2010", f"{d:+,.0f} people ({d / x0 * 100:+.1f}%)", f"±{m:,.0f} people",
                     f"{a['vintage']} to {b['vintage']}",
                     h("span", None, status_badge("computed", page, "Difference of two ACS period estimates; margin of error combines both."),
                       " within margin of error" if inside else "", page.cites.cite(f"{a['source_ids']};{b['source_ids']}"))])
    if not rows:
        return None
    return [h("p", None, "Fixed set of community indicators from the American Community Survey (ACS) 5-year estimates. "
                         "These are period estimates with a margin of error, not point-in-time counts. Dollar figures are in the vintage's final-year dollars."),
            h("div", {"class": "card ctx-card"}, data_table(f"context-{unit['unit_id']}", ["Indicator", "Estimate", "Margin of error", "Vintage", "Status"],
                                                           rows, caption=f"Community context: {unit['name']}", numeric=(1, 2), min_width="40rem"))]


def _budget_block(ed, page, unit):
    uid = unit["unit_id"]
    rows = _budget_rows(ed, uid)
    link = h("a", {"href": page.rel(f"money/budgets/index.html#{uid}")}, f"Budget section for {_short(unit)}")
    mid = money_id_for(ed, uid)
    flows = money_in_out(ed, page, mid, level=3) if mid else None
    base = tax_base_line(ed, page, mid or tax_base_id(ed, uid), county_label=ed.county_label)
    if not rows:
        return [x for x in (base, flows) if x] or None
    last = rows[-1]
    return [h("p", None, f"The guide has {len(rows)} budget-year rows for {_short(unit)}, {rows[0]['year']} to {rows[-1]['year']}. "
                         f"Latest: {_money(last['amount'])} for {last['year']} ({last['adopted_or_actual']}, "
                         f"{BASIS.get(last['basis'], last['basis'])}). ", status_badge(last["status"], page),
              page.cites.cite(last["source_ids"]),
              " Reporting bases differ between series, so compare only within one basis."),
            h("p", None, link, " on the budgets page shows every year and series breaks."),
            base,
            flows]


def _audits_block(ed, page, unit):
    """State Board of Accounts reports for this unit (audits.csv), newest first. Every report on file is listed the
    same way; a summary paragraph appears only where the guide has read the report's findings in full."""
    rows = [r for r in ed.table("audits") if r["unit_id"] == unit["unit_id"]]
    if not rows:
        return None
    rows.sort(key=lambda r: (r["filed"], r["report_no"]), reverse=True)
    has_charges = any(r.get("amount_charged") for r in rows)
    intro = [h("p", None, f"The Indiana State Board of Accounts (SBOA) examines the books of every local government; small units get "
                          f"compliance reviews, larger ones financial audits (some contracted to CPA firms), and complaints can lead to a "
                          f"special investigation. The guide has {len(rows)} report{'s' if len(rows) != 1 else ''} for {_short(unit)}, newest "
                          f"first. Findings are quoted from each report's headings; the full reports are linked.")]
    if has_charges:
        intro.append(callout(h("strong", None, "About SBOA charges. "),
                             "When the SBOA finds money spent without a documented public purpose, it \"charges\" the official responsible "
                             "with repaying it, plus the investigation's cost, and forwards the report to the Indiana Attorney General and "
                             "the local prosecutor. These are repayment demands in an audit report, not criminal charges or a court finding."))
    cards = []
    for r in rows:
        period = f"{fmt_date(r['period_start'])} to {fmt_date(r['period_end'])}"
        meta = [f"Report {r['report_no']}", f"filed {fmt_date(r['filed'])}"]
        if r.get("auditor"):
            meta.append(r["auditor"])
        body = [h("h3", None, f"{r['report_type']}, {period}"),
                h("p", {"class": "muted mono"}, " · ".join(meta), " ", status_badge(r["status"], page), page.cites.cite(r["source_ids"]))]
        if r.get("summary"):
            body.append(h("p", None, r["summary"]))
        money = []
        cents = lambda v: f"${float(v):,.2f}"
        if r.get("amount_charged"):
            money.append(f"charged to the official: {cents(r['amount_charged'])}")
        if r.get("amount_questioned"):
            money.append(f"questioned costs: {cents(r['amount_questioned'])}")
        if money:
            body.append(h("p", None, h("strong", None, "Amounts in the report: "), "; ".join(money), "."))
        if r.get("referred_to"):
            body.append(h("p", None, h("strong", None, "Forwarded to: "), r["referred_to"], "."))
        findings = [f.strip() for f in r.get("findings", "").split(";") if f.strip()]
        if findings:
            body.append(h("p", None, h("strong", None, "Findings, as headed in the report:")))
            body.append(h("ul", None, [h("li", None, f) for f in findings]))
        if r.get("notes"):
            body.append(h("p", {"class": "muted"}, r["notes"]))
        cards.append(h("article", {"class": "card"}, body))
    return intro + cards


# ----------------------------------------------------------------------------- place page

def _township_places(ed, unit):
    uid = unit["unit_id"]
    return [r for r in ed.table("derived/township_places") if r["township_unit_id"] == uid]


def _in_townships(ed, unit):
    uid = unit["unit_id"]
    return [r for r in ed.table("derived/township_places") if r["place_unit_id"] == uid]


def build_place(uid, site):
    ed = site.ed
    unit = ed.units[uid]
    kind = unit["unit_type"]
    page = site.page(f"places/{uid}/index.html", banners=True)
    c = page.cites
    short = _short(unit)
    ut = ed.unit_types.get(kind, {})
    offices = ed.offices_for(uid)
    conflicts = _conflicts(ed)
    gaps_extra = []
    blocks = []   # (id, title, content, scope)

    # ---- structure
    if offices:
        cls = (ed.config.get("variants", {}).get("city_classes") or {}).get(uid)
        cls_verified = (ed.config.get("variants", {}).get("city_classes") or {}).get("verified", False)
        parts = [h("div", {"class": "generic"}, scope_badge("indiana", ed), " ", ut.get("what_it_does", ""), c.cite(ut.get("source_ids"))),
                 h("p", None, f"In {short}, the guide's data lists {_seat_phrase(offices)}{_office_summary(offices)}.", c.cite_compact(_union(offices)))]
        if cls and kind == "city":
            parts.append(h("p", None, f"City class on file: {'second' if cls == '2' else cls}. ",
                           None if cls_verified else status_badge("unverified", page, "Class is not yet confirmed against a city source.")))
        parts.append(_offices_table(ed, page, unit, offices))
        blocks.append(("structure", "How it's organized", parts, "county"))
    else:
        gaps_extra.append(_gap(f"{short}: elected offices and structure", "No offices are recorded for this place in offices.csv.",
                               "Research the town's officers on the Indiana Gateway or county canvass."))

    # ---- officeholders
    has_terms = any(ed.terms_for(o["office_id"]) for o in offices)
    if offices and has_terms:
        n_inc = sum(len(ed.incoming_terms(o["office_id"])) for o in offices)
        intro = [h("p", None, f"From the guide's terms data, as of {fmt_date(ed.as_of, long=True)}. Cards follow the order of offices in the data, never party. ",
                   f"{n_inc} people elected on Nov 3, 2026 are shown as incoming; they take office Jan 1, 2027, and those results are unofficial until certified." if n_inc else "")]
        if kind == "city":
            intro.append(h("p", None, "Only the current mayor appears here. ", h("a", {"href": page.rel("history/index.html#mayors")}, "The full mayors timeline is on the history page"), "."))
        bb = bodies_block(ed, offices, boards=[b for b in ed.boards if b["unit_id"] == uid])
        if bb:
            intro.append(h("h3", None, "Boards and councils by party"))
            intro.append(bb)
        cards = _cards(ed, page, offices, conflicts)
        panels = [_conflict_panel(ed, page, conflicts[o["office_id"]]) for o in offices if o["office_id"] in conflicts]
        blocks.append(("officeholders", "Who holds office now", intro + [cards] + panels, "county"))
    elif offices:
        gaps_extra.append(_gap(f"{short}: current officeholders", "Offices are listed but no terms are recorded for them.", "Add terms from the canvass."))

    # ---- party control
    councils = [o for o in offices if o["office_type"] in ("city_council_district", "city_council_at_large", "town_council_ward",
                                                         "town_council_at_large", "township_board_member")]
    if councils:
        ttl = "Township board seats by party" if kind == "township" else "Council seats by party"
        chart, why = _control_chart(ed, page, councils, f"{short}: {ttl.lower()}", f"control-{uid}")
        if chart:
            blocks.append(("control", "Party control over time",
                           [chart, h("p", {"class": "muted"}, "The chart covers the full range of the guide's data. Earlier years are listed under Gaps.")], "county"))
        else:
            gaps_extra.append(_gap(f"{short}: party composition over time", f"Not charted: {why}.", "Collect seat counts and officeholders by year."))

    # ---- mayor results (cities)
    if kind == "city":
        m = _mayor_block(ed, page, unit)
        if m:
            blocks.append(("mayor-results", "Mayoral results history", m, "county"))
        else:
            gaps_extra.append(_gap(f"{short}: mayoral results", "No mayoral general-election results are in results.csv.", ""))

    # ---- township specifics
    if kind == "township":
        tr = ed.office_types.get("township_trustee", {})
        tb = ed.office_types.get("township_board_member", {})
        blocks.insert(0, ("what-townships-do", "What townships do", [
            h("div", {"class": "generic"}, ut.get("what_it_does", ""), c.cite(ut.get("source_ids"))),
            h("ul", None, h("li", None, h("strong", None, "Trustee. "), tr.get("what_it_does", ""), c.cite(tr.get("source_ids"))),
              h("li", None, h("strong", None, "Board. "), tb.get("what_it_does", ""), c.cite(tb.get("source_ids"))))], "indiana"))
        inside = _township_places(ed, unit)
        if inside:
            items = []
            for r in inside:
                nm = (h("a", {"href": page.rel(f"places/{r['place_unit_id']}/index.html")}, r["place_name"])
                      if r["place_unit_id"] in ed.units else r["place_name"])
                items.append(h("li", None, nm, f" ({'census-designated place, not a government' if r['place_kind'] == 'cdp' else r['place_kind']}; "
                               f"{'part of it lies in this township' if r['coverage'] == 'partial' else 'listed for this township'}) ",
                               status_badge(r["status"], page), c.cite(r["source_ids"])))
            blocks.append(("places-inside", "Cities and towns in this township", [
                h("ul", None, items),
                h("p", {"class": "muted"}, "Cities can cross township lines. This list is from a secondary source and has not been checked against county GIS.")], "county"))
        else:
            gaps_extra.append(_gap(f"{short}: cities and towns inside", "No municipality is listed for this township in the guide's data.", "Check county GIS."))
    else:
        inn = _in_townships(ed, unit)
        if inn:
            blocks.append(("townships", "Township location", [h("ul", None, [
                h("li", None, h("a", {"href": page.rel(f"places/{r['township_unit_id']}/index.html")}, ed.units[r["township_unit_id"]]["name"]),
                  f" ({'part of ' + short + ' lies here' if r['coverage'] == 'partial' else 'listed for this township'}) ",
                  status_badge(r["status"], page), c.cite(r["source_ids"])) for r in inn])], "county"))

    # ---- boards
    bb = _boards_block(ed, page, unit) if kind != "township" else None
    if bb:
        blocks.append(("unelected", "Unelected but powerful", bb, "county"))
    elif kind != "township":
        gaps_extra.append(_gap(f"{short}: appointed boards", "No appointed boards are recorded for this place.", "Check the place's website."))

    # ---- results
    rb = _results_block(ed, page, unit, latest_only=(kind == "city"))
    if rb:
        blocks.append(("results", "Recent results", rb, "county"))
    else:
        gaps_extra.append(_gap(f"{short}: election results", "No general-election contests for this place are in results.csv.", ""))

    # ---- budget
    bg = _budget_block(ed, page, unit)
    if bg:
        blocks.append(("budget", "Budget", bg, "county"))
    else:
        gaps_extra.append(_gap(f"{short}: budget", "No budget rows map to this place in budgets.csv.", ""))

    # ---- state audits (State Board of Accounts reports); listed only when audits.csv has rows for this unit
    ab = _audits_block(ed, page, unit)
    if ab:
        blocks.append(("audits", "State audits", ab, "county"))

    # ---- context
    # Community figures are never placed next to results or party-control visuals (ux-review section 6;
    # neutrality review F6). With a budget block they follow it; without one they go right after
    # "How it's organized", ahead of officeholders, control charts and results.
    cb = _context_block(ed, page, unit)
    if cb:
        ctx = ("context", "Context", cb, "county")
        if bg:
            blocks.append(ctx)
        else:
            ids = [b[0] for b in blocks]
            at = ids.index("structure") + 1 if "structure" in ids else (1 if ids[:1] == ["what-townships-do"] else 0)
            blocks.insert(at, ctx)
    else:
        gaps_extra.append(_gap(f"{short}: community context (population, income, poverty, homeownership, education)",
                               "No census figures for this place are in indicator_values.csv.", "Pull ACS place-level tables."))

    # ---- coverage strip
    cur_n = sum(1 for o in offices if ed.current_terms(o["office_id"]))
    lvl = "none" if not offices or not has_terms else ("covered" if cur_n == len(offices) else "partial")
    present = {b[0] for b in blocks}
    cov = [("Officeholders", lvl, f"{cur_n} of {len(offices)} offices have a current holder" if offices else None),
           ("Results", "covered" if "results" in present else "none", None),
           ("Appointed boards", "covered" if "unelected" in present else ("none" if kind != "township" else None), None),
           ("Context", "covered" if "context" in present else "none", None),
           ("Budget", "covered" if "budget" in present else "none", None)]
    strip = h("ul", {"class": "cov-strip", "aria-label": "What the guide covers for this place"},
              [h("li", None, h("span", {"class": "cov-name"}, n), _cov(l, t if t and l != "none" else None)) for n, l, t in cov if l])

    # ---- assemble
    toc = [(b[0], b[1]) for b in blocks] + [("gaps", "Gaps"), ("sources", "Sources")]
    desc_bits = []
    if offices:
        desc_bits.append(f"The guide's data lists {_seat_phrase(offices)} for {short}.")
    else:
        desc_bits.append(f"The guide has no election data for {short} yet.")
    page.add(h("header", {"class": "page-hero"},
               h("p", {"class": "eyebrow mono"}, f"Places · {KINDS[kind]}"),
               h("h1", None, unit["name"]),
               h("p", {"class": "dek"}, " ".join(desc_bits), c.cite(unit["source_ids"]), " ", status_badge(unit["status"], page)),
               answer_box(ed, page, unit, offices, links={
                   "who": "#officeholders" if "officeholders" in present else ("#structure" if "structure" in present else None),
                   "spend": "#budget" if "budget" in present else ("money/your-tax-bill/index.html#all-rates", "Every unit's tax rate"),
                   "vote": "#structure" if "structure" in present else ("elections/calendar/index.html#by-year", "Election calendar"),
                   "people": "#context" if "context" in present else None},
                   # same row as this page's Budget section ("Latest: ..."), so the two never disagree
                   budget_row=place_budget_row(ed, uid)),
               h("p", {"class": "hero-badges"}, scope_badge("county", ed), " ", scope_badge("indiana", ed),
                 h("span", {"class": "muted"}, " marks rules that apply in every county.")),
               strip,
               h("nav", {"class": "toc", "aria-label": "On this page"},
                 h("ol", None, [h("li", None, h("a", {"href": f"#{a}"}, t)) for a, t in toc]))))
    for i, (sid, title, content, scope) in enumerate(blocks, 1):
        content = content if isinstance(content, list) else [content]
        page.add(section(sid, i, title, *content, scope=scope, ed=ed))

    pat = rf"{re.escape(short)}|Township trustees and boards|place-to-township|Township-level" if kind == "township" else \
          rf"{re.escape(short)}|Town officeholders" if kind == "town" else rf"{re.escape(short)}"
    gaps = ed.gaps(files=["gaps_gov", "gaps_results", "gaps_money", "gaps_community_people"], pattern=pat)
    page.finish(gaps=gaps_extra + gaps, gaps_intro="Blocks with no data are hidden and listed here, with what the guide looked for and did not find.")
    return page


def _seat_total(offices):
    return sum(int(o["seats"]) if o["seats"].isdigit() else 1 for o in offices)


def _office_summary(offices):
    from collections import Counter
    cnt = Counter()
    for o in offices:
        n = int(o["seats"]) if o["seats"].isdigit() else None
        cnt[re.sub(r",? ?(District|Ward) .*|, At-Large.*", "", o["title"])] += n or 1
    blank = any(not o["seats"].isdigit() for o in offices)
    return (" (" + "; ".join(f"{t}: {n}" for t, n in cnt.items())
            + ("; a seat count not stated in the sources is counted as 1" if blank else "") + ")") if cnt else ""


def _seat_phrase(offices) -> str:
    """'11 elected seats', or 'at least 6 elected seats' when a seat count is blank (counted as 1)."""
    n = _seat_total(offices)
    blank = any(not o["seats"].isdigit() for o in offices)
    return f"{'at least ' if blank else ''}{n} elected seat{'s' if n != 1 else ''}"


# ----------------------------------------------------------------------------- places index

def _serving(ed, unit):
    kind, short = unit["unit_type"], _short(unit)
    out = [("County", ed.county_label)]
    if kind != "township":
        for r in ed.table("derived/township_places"):
            if r["place_unit_id"] == unit["unit_id"]:
                out.append(("Township", ed.units[r["township_unit_id"]]["name"] + (" (part)" if r["coverage"] == "partial" else "")))
    schools = []
    base = re.sub(r" Township$", "", unit["name"])
    for u in ed.units.values():
        if u["unit_type"] != "school_corporation":
            continue
        hit = False
        if kind == "township":
            hit = any(o["district"].lower() in (unit["name"].lower(), f"{base.lower()} twp") for o in ed.offices_for(u["unit_id"])) \
                or bool(re.search(rf"\b{re.escape(base)}\b", u["places_covered"]) and "township" in u["places_covered"].lower())
        else:
            hit = bool(re.search(rf"\b{re.escape(short)}\b", u["places_covered"], re.I))
        if hit:
            schools.append(u["name"])
    out += [("School corporation", s) for s in schools]
    return out


def build_index(site):
    ed = site.ed
    page = site.page("places/index.html", banners=False)
    c = page.cites
    units = {k: sorted([u for u in ed.units.values() if u["unit_type"] == k], key=lambda u: _short(u).lower()) for k in KINDS}
    toc = ([("map", "Map")] if load_shapes(ed) is not None else []) + \
          [(f"{k}s", PLURAL[k]) for k in KINDS if units[k]] + [("gaps", "Gaps"), ("sources", "Sources")]
    page.add(h("header", {"class": "page-hero"},
               h("p", {"class": "eyebrow mono"}, "Reference · Places"),
               h("h1", None, page.title),
               h("p", {"class": "dek"}, f"{ed.county_label} has {len(units['city'])} cities, {len(units['town'])} towns and "
                                        f"{len(units['township'])} townships in the guide's data. Each page shows who is elected, how, and what the guide does not know yet.",
                 c.cite_compact(_union(*[units[k] for k in KINDS]))),
               h("p", None, h("a", {"href": page.rel("map/index.html")}, "See every city, town, township and school corporation on the map")),
               h("p", {"class": "hero-badges"}, scope_badge("county", ed)),
               h("nav", {"class": "toc", "aria-label": "On this page"}, h("ol", None, [h("li", None, h("a", {"href": f"#{a}"}, t)) for a, t in toc]))))
    shapes = load_shapes(ed)
    if shapes is not None:
        page.add(section("map", None, "On the map",
                         embedded_map(page, ed, shapes, ("cities", "townships"), "cities",
                                      label=f"Map of the cities, towns and townships of {ed.county_label}. Every area is a "
                                            "link to its page; the same places are listed below."),
                         h("p", {"class": "muted cmap-embed-note"},
                           "Color shows the type of government only, never party. Townships cover the whole county, so "
                           "every city and town also lies in a township. ",
                           h("a", {"href": page.rel("map/index.html")}, "Full map with school corporations and past votes"),
                           ".", c.cite_compact("MAP-001;MAP-002;MAP-003;MAP-004")),
                         scope="county", ed=ed))
    n = 0
    for kind in KINDS:
        if not units[kind]:
            continue
        cards = []
        for u in units[kind]:
            offs = ed.offices_for(u["unit_id"])
            cur = sum(1 for o in offs if ed.current_terms(o["office_id"]))
            lvl = "none" if not offs or not any(ed.terms_for(o["office_id"]) for o in offs) else ("covered" if cur == len(offs) else "partial")
            pop = _population(ed, u)
            popline = (f"{fmt_int(pop['value'])} (±{fmt_int(pop['moe'])}), {pop['vintage']}" if pop and pop["moe"] else
                       f"{fmt_int(pop['value'])}, {pop['vintage']}" if pop else "Not in the guide's data yet")
            cards.append(h("article", {"class": "card place-card", "id": u["unit_id"]},
                           h("h3", {"class": "card-title"}, h("a", {"href": page.rel(f"places/{u['unit_id']}/index.html")}, u["name"])),
                           h("dl", {"class": "place-dl"},
                             h("dt", None, "Population"), h("dd", None, popline, c.cite(pop["source_ids"]) if pop else None),
                             h("dt", None, "Governments that serve it"),
                             h("dd", None, h("ul", {"class": "plain"}, [h("li", None, f"{k}: {v}") for k, v in _serving(ed, u)]), c.cite(u["source_ids"])),
                             h("dt", None, "Elected offices"), h("dd", None, f"{len(offs)} in the guide's data " if offs else "None recorded ", _cov(lvl)))))
            n += 1
        page.add(section(f"{kind}s", list(KINDS).index(kind) + 1, PLURAL[kind], h("div", {"class": "card-grid"}, cards),
                         h("p", {"class": "muted"}, "Alphabetical. Population is an ACS 5-year estimate with its margin of error; "
                                                    "governments listed come from the guide's units, township and school-board data."), scope="county", ed=ed))
    gaps = ed.gaps(files=["gaps_gov", "gaps_community_people"], pattern=r"Town officeholders|Indian Village|place-to-township|Township trustees and boards before")
    page.finish(gaps=gaps)
    return page


# ----------------------------------------------------------------------------- schools

def _label_counts(ed, unit_id, year):
    tally = {}
    for c in _school_contests(ed, unit_id, general_only=True):
        if ed.elections[c["election_id"]]["date"][:4] != year or "question" in c["contest_id"]:
            continue
        for r in c["rows"]:
            tally[r["party"] or "none listed"] = tally.get(r["party"] or "none listed", 0) + 1
    return tally


def _school_board_facts(ed, uid):
    """Panel facts for one school corporation on the Schools page map: seats, how they are elected, current members in
    the guide's data, next election. Same counts as the 'Corporations at a glance' table."""
    offs = ed.offices_for(uid)
    if not offs:
        return [["Board seats", "not in the guide's data"]]
    seats = [o["seats"] for o in offs]
    total = sum(int(s) for s in seats if s.isdigit())
    known = all(s.isdigit() for s in seats)
    groups = {}
    for o in offs:
        how = _how_elected(o)
        key = "By district (voters in each district)" if how.startswith("Voters in District") else how
        n = int(o["seats"]) if o["seats"].isdigit() else None
        cnt, unknown = groups.get(key, (0, False))
        groups[key] = (cnt + (n or 0), unknown or n is None)
    how_txt = "; ".join(f"{k}: {'at least ' if unk else ''}{n} seat{'s' if n != 1 else ''}" for k, (n, unk) in groups.items())
    n_cur = sum(len(ed.current_terms(o["office_id"])) for o in offs)
    nxt = ", ".join(sorted({o["next_election"] for o in offs if o["next_election"]})) or "not in sources"
    return [["Board seats", f"{total}{'' if known else '+ (not all stated in sources)'}"],
            ["How they are chosen", how_txt],
            ["Current members in the guide's data", str(n_cur)],
            ["Next election", nxt]] + school_stats.panel_facts(ed, uid)


def _school_stats_block(ed, page, uid):
    """Schools page: enrollment (latest, trend chart) and spending per student beside the state median."""
    c = page.cites
    series = school_stats.enrollment(ed, uid)
    row, med = school_stats.per_student(ed, uid)
    items, fig = [], None
    if series:
        last = series[-1][2]
        srcs = ";".join(dict.fromkeys(x for _, _, r in series for x in split_ids(r["source_ids"])))
        items.append(h("li", None, h("strong", None, "Enrollment: "),
                       school_stats.enrollment_text(series),
                       ". Whole corporation, pre-kindergarten through grade 12 plus adult students, as reported to the "
                       "Indiana Department of Education. ", status_badge(last["status"], page), c.cite(srcs)))
        if len(series) > 1:
            pts = [(int(y[:4]), v) for y, v, _ in series]
            fig = line(f"enroll-{uid}", "Students enrolled, by school year",
                       [{"name": "Students enrolled", "mark": "m-accent", "points": pts}],
                       subtitle=f"Whole corporation, school years {series[0][0]} to {series[-1][0]}",
                       value_fmt=lambda v: f"{v:,.0f}", status=last["status"], page=page,
                       x_fmt=lambda x: f"{x}-{(x + 1) % 100:02d}",
                       note=("Total enrollment from the Indiana Department of Education, including pre-kindergarten and "
                             "adult students and any part of the corporation outside the county. It is a count of "
                             "students, not the average daily membership the state uses for funding."),
                       cite=c.cite(srcs))
    else:
        items.append(h("li", None, h("strong", None, "Enrollment: "), _cov("none", "Not in the guide's data yet")))
    if row:
        srcs = ";".join(dict.fromkeys(split_ids(row["source_ids"]) + (split_ids(med["source_ids"]) if med else [])))
        items.append(h("li", None, h("strong", None, "Spending per student: "),
                       school_stats.per_student_text(row, med), ". ",
                       school_stats.PER_STUDENT_CAPTION[0].upper() + school_stats.PER_STUDENT_CAPTION[1:], ". ",
                       status_badge(row["status"], page), c.cite(srcs)))
    else:
        items.append(h("li", None, h("strong", None, "Spending per student: "), _cov("none", "Not in the guide's data yet")))
    return items, fig


def _school_map_area(ed):
    """government_layers callback for the Schools page map: board facts in the panel; a click goes to the district's
    section on this page (#<unit_id>)."""
    def area(key, tab, n, it, uid, unit):
        note = ""
        if it.get("share_inside") is not None and it["share_inside"] < 0.97:
            note = (f"Partly outside the county: about {round(it['share_inside'] * 100)}% of this district's land area is "
                    f"inside {ed.county_label} (computed from Census boundaries).")
        entry = {"n": unit["name"], "t": "School corporation", "f": _school_board_facts(ed, uid), "note": note,
                 "href": f"#{uid}", "l": tab, "d": it["d"], "open": "Go to its section"}
        return (f"cmap-s cmap-school cmap-school-{n % 3}", f"#{uid}",
                f"{unit['name']}, school corporation. Go to its section on this page.", entry, "cmap-dot")
    return area


def build_schools(site):
    ed = site.ed
    page = site.page("schools/index.html", banners=True)
    c = page.cites
    corps = [u for u in ed.units.values() if u["unit_type"] == "school_corporation"]
    conflicts = _conflicts(ed)
    ut = ed.unit_types.get("school_corporation", {})
    sbt = ed.office_types.get("school_board_member", {})
    rule = ed.rules.get("partisan_school_board", {})
    order = ed.rules.get("school_board_ballot_order", {})
    vac = ed.rules.get("local_vacancy_caucus", {})
    toc = [("rules", "State rules for school boards"), ("overview", "Corporations at a glance")] + \
          [(u["unit_id"], re.sub(r" School Corporation$", "", u["name"])) for u in corps] + [("gaps", "Gaps"), ("sources", "Sources")]
    page.add(h("header", {"class": "page-hero"},
               h("p", {"class": "eyebrow mono"}, "Reference · Schools"),
               h("h1", None, page.title),
               h("p", {"class": "dek"}, f"{len(corps)} school corporations appear in the guide's data for {ed.county_label}. "
                                        "Each has a board; most seats are elected, some are appointed.", c.cite_compact(_union(corps))),
               h("p", {"class": "hero-badges"}, scope_badge("indiana", ed), " ", scope_badge("county", ed)),
               h("nav", {"class": "toc", "aria-label": "On this page"}, h("ol", None, [h("li", None, h("a", {"href": f"#{a}"}, t)) for a, t in toc]))))

    all_2026 = {}
    for u in corps:
        for k, v in _label_counts(ed, u["unit_id"], "2026").items():
            all_2026[k] = all_2026.get(k, 0) + v
    lab = ", ".join(f"{party_label(k) if k != 'none listed' else 'no party listed'}: {v}" for k, v in sorted(all_2026.items()))
    page.add(section("rules", 1, "State rules for school boards",
                     h("div", {"class": "generic"}, scope_badge("indiana", ed), " ", ut.get("what_it_does", ""), c.cite(ut.get("source_ids"))),
                     h("h3", None, "Party labels on school board ballots (SEA 287)"),
                     h("p", None, rule.get("plain_language", ""), c.cite(rule.get("source_ids"))),
                     h("p", None, rule.get("detail", "")),
                     h("p", None, order.get("plain_language", ""), c.cite(order.get("source_ids"))) if order else None,
                     h("p", None, vac.get("plain_language", ""), c.cite(vac.get("source_ids"))) if vac else None,
                     h("h3", None, "What the guide's 2026 results show"),
                     h("p", None, f"Candidate lines in the 2026 school board contests in this guide, by party label as printed: {lab}. ",
                       status_badge("unofficial", page), c.cite("GOV-001")) if all_2026 else
                     h("p", None, "No 2026 school board results are in the guide's data."),
                     scope="indiana", ed=ed,
                     lead="The state sets how school boards work. The county's boards are listed below."))

    # overview
    rows = []
    for u in corps:
        offs = ed.offices_for(u["unit_id"])
        seats = [o["seats"] for o in offs]
        total = sum(int(s) for s in seats if s.isdigit())
        known = all(s.isdigit() for s in seats) and bool(seats)
        n_cur = sum(len(ed.current_terms(o["office_id"])) for o in offs)
        rows.append([h("a", {"href": f"#{u['unit_id']}"}, u["name"]), f"{total}{'' if known else '+ (not all stated)'}" if offs else "not in sources",
                     f"{sum(1 for o in offs if o['office_type'] != 'school_board_appointed' and not o['district'].lower().startswith('at-large'))} district, "
                     f"{sum(1 for o in offs if o['district'].lower().startswith('at-large'))} at-large seat group(s)" if offs else "",
                     str(n_cur) if offs else "0", ", ".join(sorted({o["next_election"] for o in offs if o["next_election"]})) or "not in sources"])
    shapes = load_shapes(ed)
    smap = None
    if shapes is not None:
        smap = [embedded_map(page, ed, shapes, ("schools",), "schools", area=_school_map_area(ed),
                             label=f"Map of the school corporations in {ed.county_label}. Every district is a link to its "
                                   "section on this page.",
                             hint="Hover, focus or tap a district to see its board here. Select it again, or use the link, "
                                  "to go to its section below."),
                h("p", {"class": "muted cmap-embed-note"},
                  "Shading only separates neighboring districts. Districts that extend past the county line are cut at it. "
                  "Board figures are the same as the table below.", c.cite_compact("MAP-001;MAP-002;MAP-003;MAP-004"))]
    page.add(section("overview", 2, "Corporations at a glance",
                     smap,
                     data_table("schools-overview", ["Corporation", "Board seats stated", "Seat groups", "Current members in data", "Next elections"], rows,
                                caption="School corporations", numeric=(1, 3), min_width="42rem"),
                     one_bar("corporation", "corporations", "Pick a corporation on the map or in the table to show its board, "
                                                            "budget and results. Each corporation is listed below; open any of them."),
                     scope="county", ed=ed))

    for i, u in enumerate(corps, 3):
        uid = u["unit_id"]
        offs = ed.offices_for(uid)
        parts = []
        meta = [u["places_covered"]] if u["places_covered"] else []
        parts.append(h("p", None, (f"Area: {u['places_covered']}. " if u["places_covered"] else "Area served: not stated in the guide's data. "),
                       h("a", {"href": u["website"], "target": "_blank", "rel": "noopener"}, "District website") if u["website"] else "",
                       c.cite(u["source_ids"]), " ", status_badge(u["status"], page)))
        # conflicts
        for o in offs:
            if o["office_id"] in conflicts:
                ats = []
                for cc in _school_contests(ed, uid, general_only=True):
                    if cc["district"].lower().startswith("at-large") and "question" not in cc["contest_id"]:
                        ats.append([ed.elections[cc["election_id"]]["date"][:4], cc["vote_for"] or "not stated",
                                    str(sum(1 for r in cc["rows"] if r["winner"] == "Y")) if any(r["winner"] for r in cc["rows"]) else "not marked",
                                    h("span", None, status_badge(cc["rows"][0]["status"], page), c.cite(cc["rows"][0]["source_ids"]))])
                tbl = data_table(f"atlarge-{uid}", ["Year", "Vote for (per canvass)", "Marked elected", "Status"], ats,
                                 caption="At-large contests as recorded in results.csv", numeric=(1, 2)) if ats else None
                parts.append(_conflict_panel(ed, page, conflicts[o["office_id"]], tbl))
        ab_boards = [b for b in ed.boards if b["unit_id"] == uid]
        # seats
        if offs:
            seat_rows = []
            for o in offs:
                seat_rows.append([o["title"] if False else (o["district"] and (f"District {o['district']}" if re.fullmatch(r"\d+", o["district"]) else o["district"]) or "Appointed seat(s)"),
                                  _how_elected(o), o["seats"] or "not stated in sources", f"{o['term_years']} years" if o["term_years"] else "",
                                  o["next_election"] or "not in sources", h("span", None, status_badge(o["status"], page), c.cite(o["source_ids"]))])
            parts += [h("h3", None, "Board seats and how they are elected"),
                      h("p", None, sbt.get("what_it_does", ""), c.cite(sbt.get("source_ids")), " ",
                        "Total seats: ", (str(sum(int(o["seats"]) for o in offs)) if all(o["seats"].isdigit() for o in offs) else "not fully stated in sources"), "."),
                      data_table(f"seats-{uid}", ["Seat", "Who votes", "Seats", "Term", "Next election", "Status"], seat_rows,
                                 caption=f"Board seats: {u['name']}", numeric=(2,), min_width="44rem")]
            bb = bodies_block(ed, offs, appointed_offices=[o for o in offs if o["office_type"] == "school_board_appointed"])
            parts += [h("h3", None, "Current and incoming members")] + ([bb] if bb else []) + [_cards(ed, page, offs, conflicts)]
            tally = _label_counts(ed, uid, "2026")
            if tally:
                parts.append(h("p", None, "2026 candidate lines by party label: ",
                               ", ".join(f"{party_label(k) if k != 'none listed' else 'no party listed'}: {v}" for k, v in sorted(tally.items())),
                               ". ", status_badge("unofficial", page), c.cite("GOV-001")))
        else:
            parts.append(h("p", None, _cov("none"), " No board seats are recorded for this corporation in offices.csv."))
        ab = [b for b in ed.boards if b["unit_id"] == uid]
        for b in ab:
            parts.append(h("p", None, h("strong", None, b["name"] + ": "), b["what_it_decides"], " Appointed by: ", b["appointing_authorities"], ". ",
                           status_badge(b["status"], page), c.cite(b["source_ids"])))
        stat_items, enroll_fig = _school_stats_block(ed, page, uid)
        smid = money_id_for(ed, uid)
        parts += [h("h3", None, "Superintendent, budget and enrollment"),
                  h("ul", None,
                    h("li", None, h("strong", None, "Superintendent: "), _cov("none", "Not in the guide's data yet")),
                    *stat_items,
                    h("li", None, h("strong", None, "Budget: "), *(_sch_budget(ed, page, uid)))),
                  tax_base_line(ed, page, smid or tax_base_id(ed, uid), county_label=ed.county_label),
                  enroll_fig]
        sflows = money_in_out(ed, page, smid, level=3) if smid else None
        if sflows:
            parts.append(sflows)
        refs = [cc for cc in _school_contests(ed, uid) if "question" in cc["contest_id"] or "referend" in cc["contest_id"]]
        if refs:
            parts += [h("h3", None, "Referenda and public questions"), h("div", {"class": "chart-grid"}, [_contest_figure(ed, page, cc, question=True) for cc in refs])]
        else:
            parts.append(h("p", {"class": "muted"}, "No referendum or public-question results for this corporation are in results.csv."))
        page.add(one_section(uid, i, u["name"], uid, _school_digest(ed, uid), *parts, scope_badge=scope_badge("county", ed)))

    gaps = ed.gaps(files=["gaps_gov", "gaps_money"], pattern=r"School|SBCSC|LaVille|Union-North|New Prairie|PHM|enrollment|school")
    page.finish(gaps=[_gap("Superintendents of every school corporation", "No superintendent data is in the guide.", "Add from each district's website or IDOE.")] + gaps)
    return page


def _school_digest(ed, uid) -> str:
    """The one-line summary under a corporation's collapsed heading: board seats, next election, enrollment."""
    offs = ed.offices_for(uid)
    bits = []
    if offs:
        seats = [o["seats"] for o in offs]
        total = sum(int(x) for x in seats if x.isdigit())
        bits.append(f"{total}{'' if all(x.isdigit() for x in seats) else '+'} board seats")
        nxt = sorted({o["next_election"] for o in offs if o["next_election"]})
        if nxt:
            bits.append("next election " + ", ".join(nxt))
    else:
        bits.append("board seats not in the guide's data")
    series = school_stats.enrollment(ed, uid)
    if series:
        y, v, _r = series[-1]
        bits.append(f"{fmt_int(v)} students enrolled ({y})")
    return " · ".join(bits)


def _sch_budget(ed, page, uid):
    rows = _budget_rows(ed, uid)
    if not rows:
        return ["not in the guide's data yet."]
    last = rows[-1]
    return [f"{_money(last['amount'])} for {last['year']} ({last['adopted_or_actual']}, {BASIS.get(last['basis'], last['basis'])}). ",
            status_badge(last["status"], page), page.cites.cite(last["source_ids"]), " ",
            h("a", {"href": page.rel(f"money/budgets/index.html#{uid}")}, "Full series on the budgets page")]


# ----------------------------------------------------------------------------- registration

def _all_place_ids():
    root = Path(__file__).resolve().parents[3] / "data" / "editions"
    ids = set()
    for f in root.glob("*/units.csv"):
        import csv
        with open(f, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                if r["unit_type"] in KINDS:
                    ids.add(r["unit_id"])
    return sorted(ids)


PAGES = {"places/index.html": build_index, "schools/index.html": build_schools}
for _uid in _all_place_ids():
    PAGES[f"places/{_uid}/index.html"] = partial(build_place, _uid)
