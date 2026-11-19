"""Places (cities, towns, townships) and school corporations.

Since 2026-11-16 (phase 6 step 3) their pages are government pages with tabs, governments/<unit_id>/ (civic/governments.py,
pages/governments.py): this module renders the tabs of a city, town, township (place_renderers) and of a school
corporation (school_renderers). The old pages places/index.html, places/<unit_id>/index.html and schools/index.html
are forwarding pages: a title, one line, a plain link, a canonical link, and #moved-anchors sending every old #anchor
to the tab that now holds it (static/js/moved.js); Netlify 301s the path-level moves (tools/site/netlify_prep.py).

Optional edition data in derived/: township_places.csv (which places lie in which township),
place_conflicts.csv (offices whose sources disagree; shown as conflicts, never resolved).
"""
from __future__ import annotations

import math
import re
from functools import partial
from pathlib import Path

from civic.charts import columns, line, party_timeline, results_bars
from civic.components import (APPOINTED_NOTE, BODY_OF, as_of_note, bodies_block, body_state, body_with_breakdown, name_with_party, data_table,
                              officeholder_card, party_label, scope_badge, section, see_all_fold, status_badge, status_heading, status_label, callout)
from civic.data import fmt_date, fmt_int, parse_date, split_ids
from civic.answers import answer_box, place_budget_row
from civic.related import RelatedLink, contest_href, latest_contest, related_items, related_links, related_rail, seat_items
from civic import results_status as RS
from civic.html import Markup, h, join
from civic.spending import money_id_for, money_in_out
from civic.tax_base import money_id as tax_base_id, tax_base_line
from civic import school_stats
from civic.map import embedded_map, load_shapes
from civic.pick_one import one_bar, one_section
from civic.preselect import here_slot
from civic.district_map import district_map, district_set, load_district_shapes
from civic.holder_rows import holder_row, holder_state, seat_row
from civic.campaign_map import SET_NOTES
from civic import governments as gm
from civic import offices as om
from civic import tabs as T

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
    return h("span", {"class": f"pcov pcov-{level}"}, text or label)


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
            if r["geo_type"] in ("place", "town", "county_subdivision", "county"):
                idx[r["geo_id"]] = (r["geo_type"], r["geo_name"].lower())
        _cache(ed)["geo"] = idx
    if unit["unit_type"] == "county":
        # the county itself (added 2026-11-16, phase 6 step 3): its geography row in indicator_values
        want, typ = f"{ed.county.lower()} county", "county"
    elif unit["unit_type"] == "township":
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
                     h("span", None, status_label(o["status"], page), page.cites.cite(o["source_ids"]))])
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


def _mayor_block_contests(ed, uid) -> list[dict]:
    """The mayoral general-election contests of a city, oldest first (the mayoral results history)."""
    cs = [c for c in ed.contests.values() if not c["party_primary"] and c["contest_id"] == f"{c['election_id']}-{uid}-mayor"]
    return sorted(cs, key=lambda c: ed.elections[c["election_id"]]["date"])


def _mayor_block(ed, page, unit):
    uid = unit["unit_id"]
    cs = _mayor_block_contests(ed, uid)
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
                     h("span", None, status_label(st, page), page.cites.cite(";".join(dict.fromkeys(s for r in c["rows"] for s in split_ids(r["source_ids"])))))])
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
    return [chart, table, len(rows)]


def _boards_block(ed, page, unit):
    from . import gov_parts as P
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
                 h("span", None, status_label(b["status"], page), page.cites.cite(b["source_ids"]))] for b in bs]
        return data_table(tid, ["Board", "What it decides", "Seats", "Who appoints", "Status"], rows, caption=cap, min_width="44rem")
    parts = [h("p", None, "These bodies make decisions but their members are appointed, not elected. "
                          "Where the sources do not say who appoints, the table says so.")]
    # each table sits in a fold (closed with JavaScript on, so the Overview stays short; a link to a table opens it)
    if own:
        parts += [h("h3", None, f"Boards of {name} and its units"),
                  see_all_fold(f"boards-{uid}-all", len(own), table(own, f"boards-{uid}", f"Appointed boards: {name}"),
                               noun="board", label=f"Show the {len(own)} board{'s' if len(own) != 1 else ''}")]
        # who serves (appointed_board_members.csv, 2026-11-18): one fold per board with members on file
        parts += P.board_rosters(ed, page, own, f"Who serves on the boards of {name}")
    if other:
        parts += [h("h3", None, f"Other boards where {name} officials appoint a seat"),
                  see_all_fold(f"boards-other-{uid}-all", len(other),
                               table(other, f"boards-other-{uid}", f"Other boards with seats appointed by {name} officials"),
                               noun="board", label=f"Show the {len(other)} board{'s' if len(other) != 1 else ''}")]
    return parts


def _context_rows(ed, unit) -> list[dict]:
    """The fixed community indicators for a unit (CONTEXT_IDS, latest ACS 5-year vintage) and the population change
    since 2010, as plain rows: {label, value, moe_text, vintage, marks [(status, note)], source_ids, tail}. Shared by
    the table (_context_block) and the government Overview's community strip (pages/gov_parts.py), so both show the
    same figures. Split out of _context_block 2026-11-16 (phase 6 step 3); the figures are unchanged."""
    gid = _geo(ed, unit)
    if not gid:
        return []
    rows = []
    labels = {r["indicator_id"]: r["label"] for r in ed.table("indicators")}
    for iid in CONTEXT_IDS:
        vals = _ind(ed, gid, iid)
        new = _latest_acs(vals)
        if not new:
            continue
        label = labels.get(iid, iid)
        v, moe = _num(new["value"]), _num(new["moe"])
        if v is None:
            rows.append({"label": label, "value": "not published", "moe_text": "none published", "vintage": new["vintage"],
                         "marks": [("low", "The Census Bureau did not publish a usable estimate (insufficient sample).")],
                         "source_ids": new["source_ids"], "tail": ""})
            continue
        money = iid == "median_hh_income"
        fmt = (lambda x: f"${x:,.0f}") if money else (lambda x: f"{x:,.0f}") if iid == "pop_total" else (lambda x: f"{x:.1f}%")
        cv = (moe / 1.645 / v * 100) if (v and moe is not None) else None
        marks = [(new["status"], None)]
        if cv is not None and cv > 30:
            marks.append(("low", f"CV {cv:.0f}% (above 30%): treat as unreliable."))
        rows.append({"label": label, "value": fmt(v),
                     "moe_text": ("±0 (controlled total or rounds to zero)" if moe == 0 else f"±{fmt(moe)}")
                     if moe is not None else "none published",
                     "vintage": new["vintage"], "marks": marks, "source_ids": new["source_ids"], "tail": ""})
    # change since 2010 (ACS 2006-2010 -> latest ACS)
    pv = _ind(ed, gid, "pop_total")
    a, b = _earliest_acs(pv), _latest_acs(pv)
    # both counts published and the first one non-zero (an unpublished ACS estimate is blank: it is listed above as
    # "not published"; without this guard a blank crashed the whole place page into a stub; debug pass 2026-11-09)
    if a and b and a is not b and _num(a["value"]) and _num(b["value"]) is not None:
        x0, x1 = _num(a["value"]), _num(b["value"])
        m = math.sqrt((_num(a["moe"]) or 0) ** 2 + (_num(b["moe"]) or 0) ** 2)
        d = x1 - x0
        inside = abs(d) <= m
        rows.append({"label": "Population change since 2010", "value": f"{d:+,.0f} people ({d / x0 * 100:+.1f}%)",
                     "moe_text": f"±{m:,.0f} people", "vintage": f"{a['vintage']} to {b['vintage']}",
                     "marks": [("computed", "Difference of two ACS period estimates; margin of error combines both.")],
                     "source_ids": f"{a['source_ids']};{b['source_ids']}",
                     "tail": " within margin of error" if inside else ""})
    return rows


def _context_block(ed, page, unit):
    rows = []
    for r in _context_rows(ed, unit):
        rows.append([r["label"], r["value"], r["moe_text"], r["vintage"],
                     h("span", None, join([status_label(st, page, n) for st, n in r["marks"]], " "), r["tail"],
                       page.cites.cite(r["source_ids"]))])
    if not rows:
        return None
    return [h("p", None, "Fixed set of community indicators from the American Community Survey (ACS) 5-year estimates. "
                         "These are period estimates with a margin of error, not point-in-time counts. Dollar figures are in the vintage's final-year dollars."),
            h("div", {"class": "ctx-card"}, data_table(f"context-{unit['unit_id']}", ["Indicator", "Estimate", "Margin of error", "Vintage", "Status"],
                                                           rows, caption=f"Community context: {unit['name']}", numeric=(1, 2), min_width="40rem"))]


def _budget_block(ed, page, unit):
    uid = unit["unit_id"]
    rows = _budget_rows(ed, uid)
    link = h("a", {"href": page.rel(f"money/budgets/index.html#{uid}")}, f"Budget section for {_short(unit)}")
    mid = money_id_for(ed, uid)
    flows = money_in_out(ed, page, mid, level=3) if mid else None
    if flows:
        # the state report's income and spending charts (2+ screens) open from one line; #money-<uid> still lands
        flows = see_all_fold(f"money-flows-{uid}", 0, flows, label="Money in and money out, from the annual report "
                             "to the state: where the money comes from and what it pays for", hint="Charts · tables")
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
    n = len(rows)
    return intro + [see_all_fold(f"audits-{unit['unit_id']}-all", n, cards, noun="report",
                                 label=f"See {'the' if n == 1 else 'all ' + str(n)} report{'s' if n != 1 else ''}, newest "
                                       "first, with the findings as headed", hint=None)]


# ----------------------------------------------------------------------------- place page
# Template rebuilt 2026-11-09 (Wave B batch 3; planning/qa/site-ux-review-2026-11-09.md section 3.2).
# Order: At a glance -> "More about" rail -> Who holds office now -> How it's organized -> (appointed boards) ->
# Recent results -> Party control -> Budget -> (State audits) -> Context -> Gaps -> Sources.
# The review proposed Budget before Party control; Party control comes first here so that the community figures
# (Context) never sit next to a results or party-control visual (neutrality review F6). Nothing left the page:
# the township explainer appears once (it was printed twice), the organization table has one row per body with every
# office in a "See all" fold, results open with a one-row-per-race summary and the charts sit in a fold, and the
# location lists and the mayoral history moved inside the sections they belong to, keeping their ids.

# council district maps on city pages: unit id -> district_shapes.json set id
PLACE_DISTRICT_SETS = {"south-bend": "south-bend-council-2022", "mishawaka": "mishawaka-council-2022"}
# extra caveat per set, from the district-maps research (planning/qa/district-maps-2026-11-09.md section 4)
PLACE_SET_CONFIDENCE = {
    "mishawaka-council-2022": ("Confidence: medium. The city posts these six districts as its current boundaries "
                               "(2023), but no ordinance or precinct list was found to confirm that this is the map "
                               "the 2023 election used."),
}
# towns whose ward seats have no boundary file (sources/boundaries/districts/manifest.csv status not_found)
PLACE_NO_SHAPES = {"walkerton": "walkerton-wards"}
DISTRICT_TYPES = ("city_council_district", "town_council_ward")


def _township_places(ed, unit):
    uid = unit["unit_id"]
    return [r for r in ed.table("derived/township_places") if r["township_unit_id"] == uid]


def _in_townships(ed, unit):
    uid = unit["unit_id"]
    return [r for r in ed.table("derived/township_places") if r["place_unit_id"] == uid]


def _district_name(o) -> str:
    d = o["district"] or ""
    if re.fullmatch(r"\d+", d):
        return f"District {d}"
    if d.lower().startswith("at-large"):
        return "at-large"
    return d


def _body_title(o) -> str:
    return re.sub(r",? ?(District|Ward) .*|, At-Large.*", "", o["title"])


def _groups(offices):
    """[(body title or None, [offices])]: offices that are no elected body's seat first (mayor, clerk, trustee), then
    each elected body (components.BODY_OF) in data order."""
    lone, bodies = [], {}
    for o in offices:
        b = BODY_OF.get(o["office_type"]) if o.get("elected", "yes") != "no" else None
        if b:
            bodies.setdefault(b, []).append(o)
        else:
            lone.append(o)
    return ([(None, lone)] if lone else []) + [(_body_title(v[0]), v) for v in bodies.values()]


def _seats_text(offs) -> str:
    """'9 (6 district seats, 3 at-large)' for a body of several office rows; the seat count alone for one office."""
    if len(offs) == 1:
        return offs[0]["seats"] or "not stated in sources"
    n = sum(int(o["seats"]) if o["seats"].isdigit() else 1 for o in offs)
    blank = any(not o["seats"].isdigit() for o in offs)
    dist = [o for o in offs if o["office_type"] in DISTRICT_TYPES]
    at = [o for o in offs if o not in dist]
    word = "ward" if any(o["office_type"] == "town_council_ward" for o in dist) else "district"
    nd = sum(int(o["seats"]) if o["seats"].isdigit() else 1 for o in dist)
    na = sum(int(o["seats"]) if o["seats"].isdigit() else 1 for o in at)
    parts = ([f"{nd} {word} seat{'s' if nd != 1 else ''}"] if dist else []) + ([f"{na} at-large"] if at else [])
    return f"{'at least ' if blank else ''}{n} ({', '.join(parts)})"


def _next_text(offs) -> str:
    """'2027', or '2027 (Ward 3, Ward 4, at-large); 2030 (Ward 1, Ward 2)' when a body's seats are up in different
    years."""
    yrs = {}
    for o in offs:
        yrs.setdefault(o.get("next_election") or "not in sources", []).append(o)
    if len(yrs) == 1:
        return next(iter(yrs))
    return "; ".join(f"{y} ({', '.join(_district_name(o) or o['title'] for o in os_)})" for y, os_ in sorted(yrs.items()))


def _org_table(ed, page, unit, offices) -> list:
    """How it's organized: one row per body ('South Bend Common Council · 9 (6 district seats, 3 at-large)') with every
    office row in a 'See all' fold under it (the old table, same id). When no body has more than one office row the
    office table is already one row per body and is shown as it is."""
    groups = _groups(offices)
    rows_by = [(None, [o]) for t, os_ in groups if t is None for o in os_] + [(t, os_) for t, os_ in groups if t is not None]
    if all(len(os_) == 1 for _, os_ in rows_by):
        return [_offices_table(ed, page, unit, offices)]
    c = page.cites
    rows = []
    for title, os_ in rows_by:
        o = os_[0]
        whats = list(dict.fromkeys((ed.office_type_row(x) or {}).get("what_it_does", "") for x in os_))
        srcs = ";".join(dict.fromkeys(s for x in os_ for s in split_ids((ed.office_type_row(x) or {}).get("source_ids"))))
        terms = sorted({x["term_years"] for x in os_ if x.get("term_years")})
        statuses = list(dict.fromkeys(x["status"] for x in os_))
        rows.append([title or o["title"],
                     h("span", None, " ".join(w for w in whats if w) or "Description not yet in the guide's data.",
                       c.cite(srcs) if srcs else None),
                     _seats_text(os_),
                     ", ".join(f"{t} years" for t in terms),
                     _next_text(os_),
                     h("span", None, join([status_label(s, page) for s in statuses], " "), c.cite(_union(os_)))])
    n = len(offices)
    return [data_table(f"bodies-{unit['unit_id']}", ["Office or body", "What it does", "Seats", "Term",
                                                     "Next regular election", "Status"],
                       rows, caption=f"Elected offices and bodies of {unit['name']}, one row each", min_width="48rem"),
            see_all_fold(f"offices-{unit['unit_id']}-all", n, _offices_table(ed, page, unit, offices),
                         noun="office", label=f"See all {n} offices, one row per seat or district", hint="Copy CSV")]


def _campaign_races(ed, uid) -> set:
    """Race ids the unit's campaign area page prints as #r-<id> (read from the same model pages/campaign_pages.py
    builds the page from, so a link here is never to a card that is not there)."""
    from civic.campaign_money import area_id
    from .campaigns import cf_all
    a = cf_all(ed)["areas"].get(area_id(uid))
    return {r["id"] for rs in (a or {}).get("elections", {}).values() for r in rs}


def _seat_note(items) -> Markup | None:
    if not items:
        return None
    return h("span", {"class": "seat-links"}, h("span", {"class": "seat-links-h"}, "This seat: "),
             join([h("a", {"href": i.href}, i.text) for i in items], " · "))


def _holder_rows(ed, page, offs, conflicts, notes) -> Markup:
    out = []
    for o in offs:
        if o["office_id"] in conflicts:
            out.append(_cards(ed, page, [o], conflicts))
        else:
            out.append(holder_row(ed, page, o, ed.current_terms(o["office_id"]), ed.incoming_terms(o["office_id"]),
                                  note=notes.get(o["office_id"])))
    return h("div", {"class": "one-list holder-rows place-holders"}, out)


def _crop(shapes, rec) -> tuple[dict, int]:
    """The boundary-map frame cut to the set's districts (padded), and a zoom step 1-4 for the label sizes."""
    xs = [v for it in rec["items"] for v in (it["bbox"][0], it["bbox"][2])]
    ys = [v for it in rec["items"] for v in (it["bbox"][1], it["bbox"][3])]
    pad = 0.06 * max(max(xs) - min(xs), max(ys) - min(ys))
    vb = [float(v) for v in shapes["viewBox"]]
    x0, y0 = max(vb[0], min(xs) - pad), max(vb[1], min(ys) - pad)
    w = min(vb[0] + vb[2] - x0, max(xs) - min(xs) + 2 * pad)
    hh = min(vb[1] + vb[3] - y0, max(ys) - min(ys) + 2 * pad)
    zoom = max(1, min(4, round(vb[2] / w)))
    return dict(shapes, viewBox=[round(x0, 1), round(y0, 1), round(w, 1), round(hh, 1)]), zoom


def _place_map(ed, page, unit, offices, seat_links) -> list | None:
    """Council district map for a city with official district shapes (civic/district_map.py). The panel names the
    member, the next election and links to the seat's result and campaign money; a click opens the member's line."""
    set_id = PLACE_DISTRICT_SETS.get(unit["unit_id"])
    shapes = load_shapes(ed) if set_id else None
    dshapes = load_district_shapes(ed, shapes) if shapes else None
    rec = district_set(dshapes, set_id) if dshapes else None
    if not rec:
        return None
    c = page.cites
    by_d = {o["district"]: o for o in offices if o["office_type"] in DISTRICT_TYPES}
    caveats = [x for x in (SET_NOTES.get(set_id, ""), PLACE_SET_CONFIDENCE.get(set_id, "")) if x]
    items = []
    for it in rec["items"]:
        o = by_d.get(it["district"])
        if not o:
            ed.warnings.append(f"place map: {set_id} district {it['district']} has no office in offices.csv; left off")
            continue
        st = holder_state(ed, o, ed.current_terms(o["office_id"]), ed.incoming_terms(o["office_id"]))
        facts = [["Council member", st["now"]]]
        if st["since"]:
            facts.append(["In office since", st["since"]])
        if st["how"]:
            facts.append(["First chosen by", st["how"]])
        if st["incoming"]:
            facts.append(["Nov 3, 2026 election", st["incoming"]])
        nxt = o.get("next_election") or "not in the guide's data"
        facts.append(["Next election", f"{nxt} ({o['term_years']}-year term)" if o.get("term_years") else nxt])
        more = [[i.text[:1].upper() + i.text[1:], i.href] for i in seat_links.get(o["office_id"], [])
                if i.key in ("on-page", "results", "campaigns")]
        href = f"#office-{o['office_id']}"
        entry = {"n": o["title"], "t": "Council district", "f": facts, "cav": caveats, "note": "",
                 "href": href, "open": "Show this member's details", "more": more}
        items.append({"uid": o["office_id"], "district": it["district"], "d": it["d"], "href": href,
                      "aria": f"{o['title']}: {st['now']}. Next election {nxt}. Show this member's details.",
                      "entry": entry, "text": it["district"], "label": it["label"], "label_r": it["label_r"]})
    if not items:
        return None
    at_large = [o for o in offices if o["office_type"] == "city_council_at_large"]
    n_at = sum(int(o["seats"]) for o in at_large if o["seats"].isdigit())
    legend = [h("p", None, SET_NOTES.get(set_id, ""), " Adopted by: ", rec.get("adopted_by") or "not stated", ".",
                c.cite_compact(rec.get("source_ids", ""))),
              h("p", None, PLACE_SET_CONFIDENCE[set_id]) if set_id in PLACE_SET_CONFIDENCE else None,
              h("p", None, f"The {n_at or ''} at-large seats are elected by the whole city, so they are not on the map."
                .replace("The  ", "The ")) if at_large else None]
    crop, zoom = _crop(load_shapes(ed), rec)
    m = district_map(page, ed, crop, [{"tab": "council", "label": "Council districts", "items": items, "legend": legend}],
                     "council", label=f"Map of the {len(items)} council districts of {_short(unit)}. Every district is "
                                      "a link to its council member's line below.",
                     hint="Hover, focus or tap a district to see its council member and the next election. Select it "
                          "again, or use the link, to open the member's line below.",
                     notes=h("div", {"class": "dmap-notes"},
                             h("p", None, "Party labels are shown as the guide's sources print them. The map is not "
                                          "shaded by party.")),
                     extra_cls=f"place-dmap place-dmap-z{zoom}")
    return [h("h3", {"id": "council-map"}, "Find your council district"), m]


def _no_shapes_note(ed, page, unit) -> list | None:
    """Wards with no boundary file (Walkerton): named, not drawn."""
    if unit["unit_id"] not in PLACE_NO_SHAPES:
        return None
    from civic.campaign_map import NO_SHAPES
    offs = ed.offices_for(unit["unit_id"])
    wards = [o for o in offs if o["office_type"] == "town_council_ward"]
    at = [o for o in offs if o["office_type"] == "town_council_at_large"]
    return [h("h3", {"id": "council-wards"}, "Council wards"),
            h("p", None, f"{_short(unit)}'s council has {len(wards)} ward seats" + (" and one at-large seat" if len(at) == 1 else
                                                                                   f" and {len(at)} at-large seats" if at else "")
              + ". " + NO_SHAPES["town"] + " The town code says the written description controls over the map, which "
              "is on file with the Clerk-Treasurer. Each ward's member is listed below, under the council.",
              page.cites.cite("MAP-036"))]


def _result_cell(c) -> Markup:
    """Candidates in ballot order with votes and share, winners marked (never re-sorted)."""
    bits = []
    for r in c["rows"]:
        pct, votes = _num(r["pct"]), _num(r["votes"])
        val = ", ".join(x for x in ((f"{votes:,.0f} votes" if votes is not None else ""),
                                    (f"{pct:.1f}%" if pct is not None else "")) if x) or "votes not in source"
        bits.append(h("span", {"class": "res-cand"}, name_with_party(r["candidate"], r["party"]), " ", val,
                      h("span", {"class": "res-won"}, " · elected") if r["winner"] == "Y" else None))
    return h("span", None, join(bits, "; "), h("span", {"class": "muted"}, " Uncontested.") if len(c["rows"]) == 1 else None)


def _results_section(ed, page, unit, latest_only=False, contests=None):
    """Recent results: one row per race (candidates in ballot order with votes and share, status, links to the chart,
    the office's Elections tab, the results explorer and the map), then every race's chart in a 'See all' fold.
    ``contests`` (school boards) replaces the place's own general-election contests. Returns (content, contest ids)."""
    cs = _place_contests(ed, unit["unit_id"]) if contests is None else contests
    by = {}
    for c in cs:
        by.setdefault(c["election_id"], []).append(c)
    eids = sorted(by, key=lambda e: ed.elections[e]["date"], reverse=True)
    eids = [e for e in eids if ed.elections[e]["type"] in ("general", "municipal_general")][: 1 if latest_only else 2]
    if not eids:
        return None, []
    from civic.map import load_votes, race_by_contest
    shapes = load_shapes(ed)
    races = race_by_contest(ed, load_votes(ed)) if shapes and "precinct" in shapes.get("layers", {}) else {}
    # by office and district, in the order of the unit's offices (never by party or vote share)
    rank = {o["office_id"]: i for i, o in enumerate(ed.offices_for(unit["unit_id"]))}
    for e in eids:
        by[e].sort(key=lambda c: (rank.get(c.get("office_id"), len(rank)), c["label"]))
    rows, blocks, shown = [], [], []
    for e in eids:
        el = ed.elections[e]
        for c in by[e]:
            shown.append(c["contest_id"])
            links = [h("a", {"href": f"#res-{c['contest_id']}"}, "Chart")]
            oh = om.href(page, c.get("office_id") or "", "elections")
            if oh:
                links.append(h("a", {"href": oh}, "Office"))
            ex = contest_href(page, c["contest_id"])
            if ex:
                links.append(h("a", {"href": ex}, "Explorer"))
            if c["contest_id"] in races:
                links.append(h("a", {"href": page.rel(f"map/index.html#race-{races[c['contest_id']]}")}, "Map"))
            srcs = ";".join(dict.fromkeys(s for r in c["rows"] for s in split_ids(r["source_ids"])))
            sts = list(dict.fromkeys(r["status"] for r in c["rows"]))
            rows.append([fmt_date(el["date"]), c["label"], _result_cell(c),
                         h("span", None, join([status_label(s, page) for s in sts], " "), page.cites.cite(srcs)),
                         join(links, " · ")])
        blocks.append(h("div", {"class": "results-year"},
                        h("h3", None, f"{fmt_date(el['date'], long=True)} general election ", status_heading(el["status"], page)),
                        h("div", {"class": "chart-grid"}, [_contest_figure(ed, page, c) for c in by[e]])))
    uid, n = unit["unit_id"], len(shown)
    body = [h("p", None, ballot_order_note(ed, page, eids), "Candidates appear in the order the source lists them. "
                         "Winners marked 'computed' in the data are the top vote-getters for the seats up. Each race's "
                         "Office link opens every election for that office, primaries included. ",
              h("a", {"href": page.rel("elections/results/index.html")}, "All results, 2010 to 2026")),
            data_table(f"results-summary-{uid}", ["Election", "Race", "Candidates (ballot order)", "Status", "Full result"],
                       rows, caption=f"Recent general-election races for {_short(unit)}, one row each", min_width="46rem"),
            see_all_fold(f"results-charts-{uid}", n,
                         [h("p", {"class": "muted"}, "The bar scale is 0 to 100% for every race. Each chart has a "
                                                     "table view with Copy CSV."), blocks],
                         noun="result chart", hint="Charts · tables")]
    return body, shown


def _mayor_sub(ed, page, unit) -> Markup | None:
    """Mayoral results history: the chart, then its full table (every candidate) in a 'See all' fold."""
    m = _mayor_block(ed, page, unit)
    if not m:
        return None
    chart, table, n = m
    uid = unit["unit_id"]
    return h("div", {"class": "sub-block", "id": "mayor-results"},
             h("h3", {"id": "mayor-results-h"}, "Mayoral results history"),
             chart,
             see_all_fold(f"mayor-table-{uid}-all", n, table, noun="mayoral election",
                          label=f"See all {n} mayoral elections, with every candidate"))


PLACE_ORDER = ("officeholders", "structure", "unelected", "results", "control", "budget", "audits", "context")
# sections the community figures never follow directly (neutrality review F6: no census figures next to results or
# party-control visuals; the officeholder lines carry party labels and links to results)
NOT_BESIDE_CONTEXT = ("officeholders", "results", "control")


def _place_order(present) -> list[str]:
    """Section ids in PLACE_ORDER, Context last. Only when the section before it would be one of NOT_BESIDE_CONTEXT
    (a place with no budget and no audit section; none in the St. Joseph edition) do the neutral sections (How it's
    organized, appointed boards) move up to sit between the community figures and the officeholders and results."""
    ids = [s for s in PLACE_ORDER if s in present]
    if "context" not in ids:
        return ids
    ids.remove("context")
    if not ids or ids[-1] not in NOT_BESIDE_CONTEXT:
        return ids + ["context"]
    neutral = [s for s in ids if s not in NOT_BESIDE_CONTEXT]
    visual = [s for s in ids if s in NOT_BESIDE_CONTEXT]
    if len(neutral) >= 2:
        return [neutral[0], "context", *neutral[1:], *visual]
    if neutral:
        return ["context", *neutral, *visual]
    return ids + ["context"]   # nothing neutral on the page to put between them


# ----------------------------------------------------------------------------- government tabs (phase 6 step 3)
# Since 2026-11-16 a city, town or township has its home at governments/<unit_id>/ with real-URL tabs
# (civic/governments.py, pages/governments.py); places/<unit_id>/ is a forwarding page. The tabs below reuse the old
# page's blocks and keep their ids, so old #anchors land on them (pages/governments.py moved maps):
#   Overview   At a glance, where it is, how it's organized, offices and who holds them (council district map), appointed
#              boards, contact, the community strip (Context), the "More about" rail
#   Elections  recent results (one row per race, charts in a fold, each race linked to its office's Elections tab),
#              the mayoral results history
#   Money      budget over time (the budgets page's charts), money in and out, tax base and rate, debt, state audits
#   History    party control over time, holders over time (links to each office's History tab)
#   Sources    every citation and gap
# The community strip is the Overview's last section after the neutral Contact section, so it never sits beside the
# officeholder lines (party labels), results or party-control charts (neutrality review F6); results and party control
# are on other tabs.

def _structure_parts(ed, page, unit, offices) -> list:
    c = page.cites
    uid, kind, short = unit["unit_id"], unit["unit_type"], _short(unit)
    ut = ed.unit_types.get(kind, {})
    parts = []
    if offices:
        cls = (ed.config.get("variants", {}).get("city_classes") or {}).get(uid)
        cls_verified = (ed.config.get("variants", {}).get("city_classes") or {}).get("verified", False)
        if kind == "township":
            tr = ed.office_types.get("township_trustee", {})
            tb_ = ed.office_types.get("township_board_member", {})
            parts.append(h("div", {"class": "sub-block", "id": "what-townships-do"},
                           h("h3", {"id": "what-townships-do-h"}, "What townships do"),
                           h("div", {"class": "generic"}, scope_badge("indiana", ed), " ", ut.get("what_it_does", ""), c.cite(ut.get("source_ids"))),
                           h("ul", None, h("li", None, h("strong", None, "Trustee. "), tr.get("what_it_does", ""), c.cite(tr.get("source_ids"))),
                             h("li", None, h("strong", None, "Board. "), tb_.get("what_it_does", ""), c.cite(tb_.get("source_ids"))))))
        else:
            parts.append(h("div", {"class": "generic"}, scope_badge("indiana", ed), " ", ut.get("what_it_does", ""), c.cite(ut.get("source_ids"))))
        parts.append(h("p", None, f"In {short}, the guide's data lists {_seat_phrase(offices)}{_office_summary(offices)}.", c.cite_compact(_union(offices))))
        if cls and kind == "city":
            parts.append(h("p", None, f"City class on file: {'second' if cls == '2' else cls}. ",
                           None if cls_verified else status_badge("unverified", page, "Class is not yet confirmed against a city source.")))
        # one row per body (the offices themselves are listed under Offices below), folded: the Overview stays short
        parts.append(see_all_fold(f"bodies-{uid}-all", 0, _org_table(ed, page, unit, offices)[0],
                                  label="Show the table: each elected office or body, its term and next election"))
    return parts


def _where_parts(ed, page, unit) -> list:
    """Where it is: the cities and towns inside a township, or the townships a city or town lies in (the old page's
    'places-inside' and 'townships' sub-blocks, same ids)."""
    c = page.cites
    short = _short(unit)
    out = []
    if unit["unit_type"] == "township":
        inside = _township_places(ed, unit)
        if inside:
            items = []
            for r in inside:
                href = gm.unit_href(page, r["place_unit_id"]) if r["place_unit_id"] in ed.units else None
                nm = h("a", {"href": href}, r["place_name"]) if href else r["place_name"]
                items.append(h("li", None, nm, f" ({'census-designated place, not a government' if r['place_kind'] == 'cdp' else r['place_kind']}; "
                               f"{'part of it lies in this township' if r['coverage'] == 'partial' else 'listed for this township'}) ",
                               status_badge(r["status"], page), c.cite(r["source_ids"])))
            out.append(h("div", {"class": "sub-block", "id": "places-inside"},
                         h("h3", {"id": "places-inside-h"}, "Cities and towns in this township"),
                         h("ul", None, items),
                         h("p", {"class": "muted"}, "Cities can cross township lines. This list is from a secondary source and has not been checked against county GIS.")))
    else:
        inn = _in_townships(ed, unit)
        if inn:
            out.append(h("div", {"class": "sub-block", "id": "townships"},
                         h("h3", {"id": "townships-h"}, "Township location"),
                         h("ul", None, [
                             h("li", None, h("a", {"href": gm.unit_href(page, r["township_unit_id"])}, ed.units[r["township_unit_id"]]["name"]),
                               f" ({'part of ' + short + ' lies here' if r['coverage'] == 'partial' else 'listed for this township'}) ",
                               status_badge(r["status"], page), c.cite(r["source_ids"])) for r in inn])))
    return out


def place_gaps(ed, unit) -> list[dict]:
    """What the guide looked for and did not find for a place (the old page's hidden blocks), then the gap rows whose
    wording names it."""
    from civic.spending import money_id_for as _mid
    uid, kind, short = unit["unit_id"], unit["unit_type"], _short(unit)
    offices = ed.offices_for(uid)
    out = []
    if kind == "city" and not _mayor_block_contests(ed, uid):
        out.append(_gap(f"{short}: mayoral results", "No mayoral general-election results are in results.csv.", ""))
    if not _place_contests(ed, uid):
        out.append(_gap(f"{short}: election results", "No general-election contests for this place are in results.csv.", ""))
    if offices and not any(ed.terms_for(o["office_id"]) for o in offices):
        out.append(_gap(f"{short}: current officeholders", "Offices are listed but no terms are recorded for them.", "Add terms from the canvass."))
    if not offices:
        out.append(_gap(f"{short}: elected offices and structure", "No offices are recorded for this place in offices.csv.",
                        "Research the town's officers on the Indiana Gateway or county canvass."))
    if kind == "township" and not _township_places(ed, unit):
        out.append(_gap(f"{short}: cities and towns inside", "No municipality is listed for this township in the guide's data.", "Check county GIS."))
    if kind != "township" and not _boards_rows(ed, unit):
        out.append(_gap(f"{short}: appointed boards", "No appointed boards are recorded for this place.", "Check the place's website."))
    councils = [o for o in offices if o["office_type"] in COUNCIL_TYPES]
    if councils:
        why = _control_why(ed, councils)
        if why:
            out.append(_gap(f"{short}: party composition over time", f"Not charted: {why}.", "Collect seat counts and officeholders by year."))
    if not _budget_rows(ed, uid):
        out.append(_gap(f"{short}: budget", "No budget rows map to this place in budgets.csv.", ""))
    if not _context_rows(ed, unit):
        out.append(_gap(f"{short}: community context (population, income, poverty, homeownership, education)",
                        "No census figures for this place are in indicator_values.csv.", "Pull ACS place-level tables."))
    pat = rf"{re.escape(short)}|Township trustees and boards|place-to-township|Township-level" if kind == "township" else \
          rf"{re.escape(short)}|Town officeholders" if kind == "town" else rf"{re.escape(short)}"
    return out + ed.gaps(files=["gaps_gov", "gaps_results", "gaps_money", "gaps_community_people"], pattern=pat)


COUNCIL_TYPES = ("city_council_district", "city_council_at_large", "town_council_ward", "town_council_at_large",
                 "township_board_member")


def _control_why(ed, offices) -> str | None:
    """Why a body's party-control chart cannot be drawn (the same tests as _control_chart), or None."""
    if not offices or any(not o["seats"].isdigit() for o in offices):
        return "seat counts not stated in sources"
    if len(control_by_year(ed, offices)) < 2:
        return "fewer than two years of officeholder data"
    return None


def _boards_rows(ed, unit) -> list[dict]:
    uid = unit["unit_id"]
    kids = {u["unit_id"] for u in ed.units.values() if uid in split_ids(u["parent_unit_ids"].replace(",", ";"))}
    own = [b for b in ed.boards if b["unit_id"] in kids | {uid}]
    name = _short(unit)
    other = [b for b in ed.boards if b not in own and unit["unit_type"] == "city" and re.search(re.escape(name), b["appointing_authorities"], re.I)]
    return own + other


def place_overview(ed, page, g):
    from . import gov_parts as P
    unit = ed.units[g.unit_id]
    uid, kind, short = unit["unit_id"], unit["unit_type"], _short(unit)
    c = page.cites
    offices = ed.offices_for(uid)
    conflicts = _conflicts(ed)
    keys = gm.gov_tabs(ed, g.gid)
    ctx = _context_rows(ed, unit)
    page.add(answer_box(ed, page, unit, offices, links={
        "who": "#officeholders" if offices else None,
        "spend": (gm.path(g.gid, "money"), "Budget, money in and out, debt") if "money" in keys else
                 ("money/your-tax-bill/index.html#all-rates", "Every unit's tax rate"),
        "vote": "#officeholders" if offices else ("elections/calendar/index.html#by-year", "Election calendar"),
        "people": "#context" if ctx else None},
        # same row as the Money tab's latest line, so the two never disagree
        budget_row=place_budget_row(ed, uid)))

    # where it is: the locator map, the township location or the places inside
    loc = P.locator_map(page, ed, g)
    where = _where_parts(ed, page, unit)
    if loc or where:
        page.add(T.tab_section("where", "Where it is", h("div", {"class": "gov-where"}, loc, h("div", None, where))))

    # how it's organized
    sp = _structure_parts(ed, page, unit, offices)
    if sp:
        page.add(T.tab_section("structure", "How it's organized", sp))

    # offices and who holds them
    if offices:
        n_inc = sum(len(ed.incoming_terms(o["office_id"])) for o in offices)
        seat_links = {o["office_id"]: seat_items(page, o["office_id"], campaign_races=_campaign_races(ed, uid))
                      for o in offices}
        dmap = _place_map(ed, page, unit, offices, seat_links)
        parts = [P.offices_lead(ed)]
        if n_inc:
            parts.append(h("p", None, RS.incoming_note(ed, [o["office_id"] for o in offices])))
        parts += (dmap or []) + (_no_shapes_note(ed, page, unit) or [])
        for title, offs in _groups(offices):
            if title is None:
                parts.append(h("h3", None, f"{KINDS[kind]} officers"))
            else:
                terms, seats = body_state(ed, offs)
                parts.append(h("h3", None, body_with_breakdown(title, terms, seats),
                               h("span", {"class": "body-seats"}, f" · {seats} seats" if seats else " · seat count not stated")))
            parts.append(P.office_list(ed, page, offs, conflicts={o["office_id"]: conflicts[o["office_id"]]
                                                                  for o in offs if o["office_id"] in conflicts}))
        if any(t is not None for t, _ in _groups(offices)):
            parts.append(as_of_note(ed))
        own_boards = [b for b in ed.boards if b["unit_id"] == uid]
        if own_boards and kind == "township":   # cities and towns list their boards under "Unelected but powerful"
            parts += [h("h3", None, "Appointed boards"), bodies_block(ed, [], boards=own_boards)]
        parts += [_conflict_panel(ed, page, conflicts[o["office_id"]]) for o in offices if o["office_id"] in conflicts]
        page.add(T.tab_section("officeholders", "Offices and who holds them", parts))

    # appointed boards
    bb = _boards_block(ed, page, unit) if kind != "township" else None
    if bb:
        page.add(T.tab_section("unelected", "Unelected but powerful: appointed boards", bb))

    page.add(P.contact_section(ed, page, unit))
    # the community strip: last, after the neutral Contact section (F6)
    page.add(P.community_strip(ed, page, ctx, _community_target(ed, unit), uid))
    page.add(related_links(page, uid, exclude=("place", "budget")))


def _community_target(ed, unit):
    from civic.related import _community
    return _community(ed, unit)


def place_elections(ed, page, g):
    unit = ed.units[g.unit_id]
    rb, _shown = _results_section(ed, page, unit, latest_only=(unit["unit_type"] == "city"))
    mayor = _mayor_sub(ed, page, unit) if unit["unit_type"] == "city" else None
    page.add(T.tab_section("results", "Recent results", rb or [h("p", {"class": "muted"},
                                                                  "No general-election contests for this place are in the guide's results.")],
                           mayor))


def _budget_latest(ed, page, unit) -> Markup | None:
    """The old Budget section's first line: how many budget-year rows the guide has and the latest one (the same row
    the At a glance box shows, answers.place_budget_row)."""
    rows = _budget_rows(ed, unit["unit_id"])
    if not rows:
        return None
    last = rows[-1]
    short = _short(unit)
    return h("p", {"class": "gov-latest"},
             f"The guide has {len(rows)} budget-year rows for {short}, {rows[0]['year']} to {rows[-1]['year']}. "
             f"Latest: {_money(last['amount'])} for {last['year']} ({last['adopted_or_actual']}, "
             f"{BASIS.get(last['basis'], last['basis'])}). ", status_badge(last["status"], page),
             page.cites.cite(last["source_ids"]),
             " Reporting bases differ between series, so compare only within one basis.")


def place_money(ed, page, g):
    from . import gov_parts as P
    unit = ed.units[g.unit_id]
    ab = _audits_block(ed, page, unit)
    P.money_tab(ed, page, g, latest=_budget_latest(ed, page, unit),
                after=[T.tab_section("audits", "State audits", ab) if ab else None])


def place_history(ed, page, g):
    from . import gov_parts as P
    unit = ed.units[g.unit_id]
    uid, kind, short = unit["unit_id"], unit["unit_type"], _short(unit)
    offices = ed.offices_for(uid)
    councils = [o for o in offices if o["office_type"] in COUNCIL_TYPES]
    if councils:
        ttl = "Township board seats by party" if kind == "township" else "Council seats by party"
        chart, _why = _control_chart(ed, page, councils, f"{short}: {ttl.lower()}", f"control-{uid}")
        if chart:
            page.add(T.tab_section("control", "Party control over time", chart,
                                   h("p", {"class": "muted"}, "The chart covers the full range of the guide's data. "
                                                              "Earlier years are listed under Gaps on the Sources tab. ",
                                     h("a", {"href": page.rel("history/index.html#control")},
                                       "Party control of every local body"), ".")))
    lead = None
    if kind == "city":
        lead = "Every holder in the guide's records is on each office's History tab; the mayor's has every mayor."
    page.add(P.holders_section(ed, page, offices, lead=lead))


def place_sources(ed, page, g):
    unit = ed.units[g.unit_id]
    notes = []
    if "elections" in gm.gov_tabs(ed, g.gid):
        notes.append(h("span", None, "Results are as the county's canvass or the cited source prints them; every result "
                                     "chart uses the same 0 to 100% scale. "))
    if "history" in gm.gov_tabs(ed, g.gid):
        notes.append(h("span", None, "Party control: ", CONTROL_METHOD))
    page.add(*T.sources_body(page, place_gaps(ed, unit), notes=notes, title=unit["name"]))


def place_renderers(ed, g) -> dict:
    """{tab: fn(page)} for civic/tabs.py build_tabs."""
    return {k: partial(fn, ed, g=g) for k, fn in (("overview", place_overview), ("elections", place_elections),
                                                  ("money", place_money), ("history", place_history),
                                                  ("sources", place_sources))}


def build_place(uid, site):
    """places/<unit_id>/: a forwarding page to governments/<unit_id>/ (phase 6 step 3). Every id the old page had is
    sent to the tab that now holds it (pages/governments.py forward_gov)."""
    from .governments import forward_gov
    return forward_gov(site, f"places/{uid}/index.html", uid)


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
    """places/index.html: a forwarding page to the Governments hub (phase 6 step 3), which leads with the same map and
    lists every city, town and township (its rows keep the old cards' ids)."""
    from .governments import forward_hub
    return forward_hub(site, "places/index.html")


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
    ev = _residency_evidence(ed, uid)
    for o in offs:
        key = SEAT_KIND_LABEL[_seat_kind(ed, uid, o, ev)]
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


# ----------------------------------------------------------------------------- school corporation tabs (phase 6 step 3)
# Since 2026-11-16 each school corporation has its home at governments/<unit_id>/ (it was one item on schools/,
# which is now a forwarding page). Overview: at a glance, where it is, how the board is organized (with the state's
# school-board rules), board seats and members, appointed boards, students and spending per student, contact, the
# "More about" rail. Elections: the board results of the last two general elections and the referenda. Money: the
# budgets page's charts, money in and out, tax base, debt. History: the seats' holders over time. Sources.

# words that name each corporation in the gap files (the old Schools page listed every school gap on one page)
SCHOOL_GAP_NAMES = {"sbcsc": r"SBCSC|South Bend Community School", "phm": r"PHM|Penn-Harris-Madison",
                    "school-city-mishawaka": r"School City of Mishawaka|Mishawaka school",
                    "john-glenn": r"John Glenn", "union-north": r"LaVille|Union-North", "new-prairie": r"New Prairie"}
SCHOOL_GAP_ALL = r"School|SBCSC|LaVille|Union-North|New Prairie|PHM|enrollment|school"


def _school_names_rx(ed, uid) -> str:
    return SCHOOL_GAP_NAMES.get(uid) or re.escape(re.sub(r" School Corporation$| Community Schools.*$", "", ed.units[uid]["name"]))


def school_gaps(ed, uid) -> list[dict]:
    """Gaps for one corporation: those that name it, and the school gaps that name no corporation (they apply to every
    corporation); a gap about another corporation is left to its page."""
    mine = re.compile(_school_names_rx(ed, uid), re.I)
    others = [re.compile(_school_names_rx(ed, u["unit_id"]), re.I) for u in ed.units.values()
              if u["unit_type"] == "school_corporation" and u["unit_id"] != uid]
    out = [_gap(f"Superintendent of {ed.units[uid]['name']}", "No superintendent data is in the guide.",
                "Add from the district's website or IDOE.")]
    if _residency_evidence(ed, uid):
        out.append(_gap("Who votes for the named board seats",
                        "The guide infers from its own vote counts that these seats are voted on across the whole "
                        "corporation, with the member required to live in the township or district the seat is named "
                        "for. The statute sections and the corporation's board plan were not read.",
                        "Read the corporation's plan under IC 20-23-4 (or its own statute) and the county election "
                        "board's ballot instructions."))
    for g in ed.gaps(files=["gaps_gov", "gaps_money", "gaps_results"], pattern=SCHOOL_GAP_ALL):
        text = f"{g.get('item', '')} {g.get('why_missing', '')}"
        if mine.search(text) or not any(o.search(text) for o in others):
            out.append(g)
    return out


def _school_rules(ed, page) -> Markup:
    """The state's rules for school boards (the old Schools page's first section, id "rules"): party labels on the
    ballot (SEA 287), ballot order, vacancies."""
    c = page.cites
    rule = ed.rules.get("partisan_school_board", {})
    order = ed.rules.get("school_board_ballot_order", {})
    vac = ed.rules.get("local_vacancy_caucus", {})
    return h("div", {"class": "sub-block", "id": "rules"},
             h("h3", {"id": "rules-h"}, "State rules for school boards"),
             h("p", None, scope_badge("indiana", ed), " ", h("strong", None, "Party labels on school board ballots (SEA 287). "),
               rule.get("plain_language", ""), c.cite(rule.get("source_ids"))),
             h("p", None, rule.get("detail", "")) if rule.get("detail") else None,
             h("p", None, order.get("plain_language", ""), c.cite(order.get("source_ids"))) if order else None,
             h("p", None, vac.get("plain_language", ""), c.cite(vac.get("source_ids"))) if vac else None)


def school_overview(ed, page, g):
    from . import gov_parts as P
    uid = g.unit_id
    u = ed.units[uid]
    c = page.cites
    offs = ed.offices_for(uid)
    conflicts = _conflicts(ed)
    ut = ed.unit_types.get("school_corporation", {})
    sbt = ed.office_types.get("school_board_member", {})
    # at a glance: the board facts the Schools map panel showed (same counts), then the latest budget
    facts = _school_board_facts(ed, uid)
    page.add(T.tab_section("glance", "At a glance",
                           h("dl", {"class": "gov-glance"}, [[h("dt", None, k), h("dd", None, v)] for k, v in facts]),
                           h("p", {"class": "tnote"}, "Board figures from the guide's list of offices and its terms "
                                                      "records", c.cite_compact(P.union(offs)) if offs else None,
                             "; enrollment and spending per student under Students below.")))
    loc = P.locator_map(page, ed, g)
    area = h("p", None, (f"Area: {u['places_covered']}. " if u["places_covered"] else "Area served: not stated in the guide's data. "),
             c.cite(u["source_ids"]), " ", status_badge(u["status"], page))
    page.add(T.tab_section("where", "Where it is", h("div", {"class": "gov-where"}, loc, h("div", None, area))))

    ev = _residency_evidence(ed, uid)
    total = (str(sum(int(o["seats"]) for o in offs)) if offs and all(o["seats"].isdigit() for o in offs)
             else "not fully stated in sources")
    struct = [h("div", {"class": "generic"}, scope_badge("indiana", ed), " ", ut.get("what_it_does", ""), c.cite(ut.get("source_ids"))),
              h("p", None, sbt.get("what_it_does", ""), c.cite(sbt.get("source_ids")), f" Total seats: {total}.") if offs else None,
              _seat_basis_note(ed, page, uid, offs, ev) if offs else None,
              bodies_block(ed, offs, appointed_offices=[o for o in offs if o["office_type"] == "school_board_appointed"]) if offs else None,
              _school_rules(ed, page)]
    page.add(T.tab_section("structure", "How the board is organized", struct))

    parts = []
    if offs:
        parts.append(P.offices_lead(ed))
        parts.append(P.office_list(ed, page, offs,
                                   titles={o["office_id"]: f"{_seat_title(o, with_count=True)}" for o in offs},
                                   extras={o["office_id"]: _who_votes(ed, uid, o, ev) for o in offs},
                                   conflicts={o["office_id"]: conflicts[o["office_id"]] for o in offs if o["office_id"] in conflicts}))
        for o in offs:
            if o["office_id"] in conflicts:
                ats = []
                for cc in _school_contests(ed, uid, general_only=True):
                    if cc["district"].lower().startswith("at-large") and "question" not in cc["contest_id"]:
                        ats.append([ed.elections[cc["election_id"]]["date"][:4], cc["vote_for"] or "not stated",
                                    str(sum(1 for r in cc["rows"] if r["winner"] == "Y")) if any(r["winner"] for r in cc["rows"]) else "not marked",
                                    h("span", None, status_label(cc["rows"][0]["status"], page), c.cite(cc["rows"][0]["source_ids"]))])
                tbl = data_table(f"atlarge-{uid}", ["Year", "Vote for (per canvass)", "Marked elected", "Status"], ats,
                                 caption="At-large contests as recorded in results.csv", numeric=(1, 2)) if ats else None
                parts.append(_conflict_panel(ed, page, conflicts[o["office_id"]], tbl))
    else:
        parts.append(h("p", None, _cov("none"), " No board seats are recorded for this corporation in offices.csv."))
    page.add(T.tab_section("officeholders", "Board seats and members", parts))

    ab = [b for b in ed.boards if b["unit_id"] == uid]
    if ab:
        page.add(T.tab_section("unelected", "Appointed boards",
                               [h("p", None, h("strong", None, b["name"] + ": "), b["what_it_decides"], " Appointed by: ",
                                  b["appointing_authorities"], ". ", status_badge(b["status"], page), c.cite(b["source_ids"]))
                                for b in ab] + P.board_rosters(ed, page, ab, None)))
    stat_items, enroll_fig = _school_stats_block(ed, page, uid)
    page.add(T.tab_section("students", "Students and spending per student",
                           h("ul", None, h("li", None, h("strong", None, "Superintendent: "), _cov("none", "Not in the guide's data yet")),
                             *stat_items), enroll_fig))
    page.add(P.contact_section(ed, page, u))
    page.add(_school_rail(ed, page, uid))


def school_elections(ed, page, g):
    uid = g.unit_id
    unit = ed.units[uid]
    c = page.cites
    cs = [cc for cc in _school_contests(ed, uid, general_only=True)
          if "question" not in cc["contest_id"] and "referend" not in cc["contest_id"]]
    rb, _shown = _results_section(ed, page, unit, contests=cs)
    tally = _label_counts(ed, uid, "2026")
    labels = (h("p", {"id": "labels"}, "2026 candidate lines by party label (SEA 287 put party labels on the school "
                                       "board ballot from 2026): ",
                ", ".join(f"{party_label(k) if k != 'none listed' else 'no party listed'}: {v}" for k, v in sorted(tally.items())),
                ". ", status_badge("unofficial", page), c.cite("GOV-001")) if tally else None)
    page.add(T.tab_section("results", "Recent board results",
                           rb or [h("p", {"class": "muted"}, "No board contests for this corporation are in the guide's results.")],
                           labels))
    refs = [cc for cc in _school_contests(ed, uid) if "question" in cc["contest_id"] or "referend" in cc["contest_id"]]
    if refs:
        page.add(T.tab_section("referenda", "Referenda and public questions",
                               h("div", {"class": "chart-grid"}, [_contest_figure(ed, page, cc, question=True) for cc in refs])))


def school_money(ed, page, g):
    from . import gov_parts as P
    unit = ed.units[g.unit_id]
    P.money_tab(ed, page, g, latest=_budget_latest(ed, page, unit))


def school_history(ed, page, g):
    from . import gov_parts as P
    page.add(P.holders_section(ed, page, ed.offices_for(g.unit_id)))


def school_sources(ed, page, g):
    unit = ed.units[g.unit_id]
    notes = [h("span", None, "Results are as the county's canvass or the cited source prints them; every result chart "
                             "uses the same 0 to 100% scale.")] if "elections" in gm.gov_tabs(ed, g.gid) else []
    page.add(*T.sources_body(page, school_gaps(ed, g.unit_id), notes=notes, title=unit["name"]))


def school_renderers(ed, g) -> dict:
    return {k: partial(fn, ed, g=g) for k, fn in (("overview", school_overview), ("elections", school_elections),
                                                  ("money", school_money), ("history", school_history),
                                                  ("sources", school_sources))}


def build_schools(site):
    """schools/: a forwarding page (phase 6 step 3). Its six corporations each have a government page; every old id
    goes to the corporation page that holds it (pages/governments.py forward_schools)."""
    from .governments import forward_schools
    return forward_schools(site)


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


# ---- who votes for a board seat (Wave C batch 7, 2026-11-09)
# offices.csv names township seats by township ("Harris Township") and the old page read that as "Voters in Harris
# Township". The guide's own results say otherwise for every corporation with such seats (see _residency_evidence):
# they are residency seats voted across the corporation. SBCSC's numbered districts are voting districts (MAP-031:
# five members elected by district, two at large).
VOTING_DISTRICTS = {"sbcsc": "MAP-031"}
# sources that name the seats by residency (cited in the evidence note)
RESIDENCY_SOURCES = {"phm": "MAP-033;MAP-037"}
SEAT_KIND_LABEL = {"appointed": "Appointed, not elected", "at-large": "All voters in the corporation",
                   "district": "By district (voters in each district)",
                   "residency": "All voters in the corporation, from residency seats",
                   "unknown": "Who votes not stated in sources"}
_TWP = re.compile(r"^(.+?) Township$")
_TWPS_IN = re.compile(r"\(([^)]*?)\s*Townships?\)")


def _seat_kind(ed, uid, o, ev) -> str:
    t, d = o["office_type"], o["district"] or ""
    if t == "school_board_appointed":
        return "appointed"
    if t == "school_board_at_large" or d.lower().startswith("at-large"):
        return "at-large"
    if uid in VOTING_DISTRICTS and re.fullmatch(r"\d+", d):
        return "district"
    if ev:
        return "residency"
    return "unknown"


def _seat_title(o, with_count: bool = False) -> str:
    d = o["district"] or ""
    if o["office_type"] == "school_board_appointed":
        name = "Appointed seats"
    elif re.fullmatch(r"\d+", d):
        name = f"District {d}"
    elif d.lower().startswith("at-large"):
        name = "At-large"
    else:
        name = d or o["title"]
    n = o["seats"]
    return name + (f" ({n} seats)" if with_count and n.isdigit() and int(n) > 1 else "")


def _who_votes(ed, uid, o, ev) -> str:
    kind = _seat_kind(ed, uid, o, ev)
    d = o["district"] or ""
    place = f"District {d}" if re.fullmatch(r"\d+", d) else d
    if kind == "appointed":
        return "Appointed, not elected"
    if kind == "at-large":
        return "All voters in the corporation"
    if kind == "district":
        return f"Voters in District {d}"
    if kind == "residency":
        return f"All voters in the corporation; the member must live in {place}"
    return f"Not stated in the guide's sources (the seat is named for {place})" if place else "Not stated in sources"


def _township_names(ed) -> set:
    return {u["name"].replace(" Township", "") for u in ed.units.values() if u["unit_type"] == "township"}


def _township_pop(ed, name: str) -> dict | None:
    for r in ed.table("indicator_values"):
        if (r["indicator_id"] == "pop_total" and r["geo_type"] == "county_subdivision"
                and r["vintage"].startswith("ACS 2020-2024") and r["geo_name"].lower().startswith(name.lower() + " township")):
            return r
    return None


def _residency_evidence(ed, uid) -> list[dict]:
    """Facts in the guide's own data showing that a corporation's named seats are voted across the corporation, not
    only by the residents of the township or district they are named for. Each: {text, sources, office_id}.
      - outside: the seat is named for townships outside the county (its name, or its contest's ballot label), yet
        the county's canvass counts votes for it, so voters who do not live there vote for it;
      - more votes than residents: the seat drew more votes per seat than the township it is named for has people.
    Empty for SBCSC (VOTING_DISTRICTS) and for corporations with no district seats."""
    if uid in VOTING_DISTRICTS:
        return []
    cache = ed.__dict__.setdefault("_residency_ev", {})
    if uid in cache:
        return cache[uid]
    in_county = _township_names(ed)
    out = []
    for o in ed.offices_for(uid):
        if o["office_type"] != "school_board_district":
            continue
        for ct in reversed(ed.contests_for_office(o["office_id"])):
            el = ed.elections.get(ct["election_id"], {})
            if el.get("type") != "general" or not ct["rows"]:
                continue
            votes = sum(float(r["votes"] or 0) for r in ct["rows"])
            if not votes:
                continue
            m = _TWP.match(o["district"] or "")
            names = [m.group(1)] if m else []
            m2 = _TWPS_IN.search(ct.get("district") or "")
            if m2:
                names = [x.strip() for x in re.split(r",|\band\b", m2.group(1)) if x.strip()]
            srcs = ";".join(dict.fromkeys(x for r in ct["rows"] for x in split_ids(r["source_ids"])))
            year = el["date"][:4]
            label = ct.get("district") or o["district"]
            if names and all(n not in in_county for n in names):
                where = " and ".join(f"{n}" for n in names) + (" Townships" if len(names) > 1 else " Township")
                out.append({"office_id": o["office_id"], "sources": srcs,
                            "text": f"the seat on the ballot as \"{label}\" is named for {where}, outside "
                                    f"{ed.county_label}, yet the county's {year} canvass counts {votes:,.0f} votes for it"})
                break
            if names and len(names) == 1:
                pop = _township_pop(ed, names[0])
                seats = int(o["seats"]) if o["seats"].isdigit() else 1
                if pop and _num(pop["value"]) is not None and votes / seats > float(pop["value"]):
                    out.append({"office_id": o["office_id"], "sources": srcs + ";" + pop["source_ids"],
                                "text": f"the {names[0]} Township seat drew {votes:,.0f} votes in {year}"
                                        + (f" for {seats} seats" if seats > 1 else "")
                                        + f", more than the {float(pop['value']):,.0f} people who live in {names[0]} "
                                          f"Township ({pop['vintage']} estimate)"})
                    break
    cache[uid] = out
    return out


def _seat_basis_note(ed, page, uid, offs, ev) -> Markup | None:
    """Why the seat list says who votes: SBCSC's districts are voting districts with no boundary file (listed, not
    drawn); elsewhere, the residency evidence; when there is none, that the sources don't say."""
    c = page.cites
    dist = [o for o in offs if o["office_type"] == "school_board_district"]
    if not dist:
        return None
    if uid in VOTING_DISTRICTS:
        names = ", ".join(_seat_title(o) for o in dist)
        return h("p", {"class": "seat-basis"}, f"The {len(dist)} board districts ({names}) are voting districts: each is "
                                               "elected by the voters who live in it, and the at-large seats by the whole "
                                               "corporation. They are listed, not drawn: the corporation publishes its "
                                               "district map only as an image of voter precincts (labelled SB1 to SB5), with "
                                               "no boundary file, and the guide never traces one by hand.",
                 c.cite(VOTING_DISTRICTS[uid] + ";MAP-032"))
    if not ev:
        return h("p", {"class": "seat-basis muted"}, "The guide's sources name these seats but do not say who votes for "
                                                     "them, so the list says so.")
    facts = join([h("span", None, e["text"], c.cite(e["sources"])) for e in ev], "; ")
    named = c.cite(RESIDENCY_SOURCES[uid]) if uid in RESIDENCY_SOURCES else None
    return h("p", {"class": "seat-basis"},
             "These are residency seats: the member must live in the township or district the seat is named for", named,
             ", but each seat is voted on by the whole corporation, not only by the people who live there. The guide "
             "infers this from its own results: ", facts, ". It applies the finding to every named seat of the "
             "corporation. ", status_badge("computed", page, "Inferred from the vote counts in the guide's results; the "
                                                             "statute section and the corporation's plan were not read."))


def _school_rail(ed, page, uid) -> Markup | None:
    """'More about' rail for one corporation (inside its item, so an h3): its latest board result in the explorer,
    campaign money, budget, tax rate, public questions (when it has any), run for school board, next election."""
    items = {i.key: i for i in related_items(page, uid)}
    built = page.site.by_path
    latest = [x for x in (latest_contest(ed, o["office_id"]) for o in ed.offices_for(uid)) if x]
    if latest and "results" not in items:
        x = max(latest, key=lambda x: (ed.elections[x["election_id"]]["date"], x["contest_id"]))
        href = contest_href(page, x["contest_id"])
        if href:
            items["results"] = RelatedLink("results", "Latest result",
                                           f"School board, {ed.elections[x['election_id']]['date'][:4]}", href)
    if any("question" in cc["contest_id"] for cc in _school_contests(ed, uid)) and \
            "elections/judges-and-questions/index.html" in built:
        items["questions"] = RelatedLink("questions", "Public questions", "Referenda, by jurisdiction",
                                         page.rel("elections/judges-and-questions/index.html#questions"))
    order = ("results", "map-votes", "campaigns", "budget", "tax-rate", "questions", "run", "calendar")
    unit = ed.units[uid]
    return related_rail([items[k] for k in order if k in items],
                        name=re.sub(r" School Corporation$| Community Schools.*$", "", unit["name"]),
                        rail_id=f"related-{uid}", heading_tag="h3")


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
