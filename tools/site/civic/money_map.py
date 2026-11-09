"""Money map for the budgets page: each area shaded by counted spending per resident.

    mm = money_map_data(ed, shapes)        -> dict (computed at build time; no hand-edited data)
    money_map(page, ed, shapes, mm)        -> Markup (tabs + <svg> + legends + panel + #cmap-data)
    money_map_tables(page, ed, mm, label)  -> Markup (every mapped area, then the units with no boundary)

Data: spending_breakdowns.csv (tools/build_spending.py) through the same year rules as civic/spending.py
(latest spending year; latest income year that is not held back), and the 2020 Census population of each
geography (indicator_values.csv, pop_census_2020, matched by name in civic/map.py population()).

Reuses the boundary map: civic/map.py government_layers draws the three layers, static/js/map.js gives the
hover/focus panel, the panel keeping the last area, touch select-then-open and the layer tabs. The money
fields of the panel (ranked bars, caveats, link label) are optional keys of the same #cmap-data entries.
Shading is one neutral teal ramp (static/css/money_map.css); breaks are computed per layer.
"""
from __future__ import annotations

import math

from .components import data_table, status_badge
from .data import fmt_int
from .html import Markup, h, json_script
from . import school_stats, tax_base
from .map import LAYERS, TYPE_LABEL, embedded_map, shade_defs
from .spending import OTHER, _f, _held, _kind, _pick_year, _rows, _year_label, money_id_for, usd, usd_short
from .data import split_ids
from .shading import (MAX_CLASSES, RAMP, class_breaks, legend_labels, money_text, ramp_positions,  # noqa: F401
                      round_between, shade_legend, step_of)

LAYER_TAB = {key: tab for key, tab, _l, _h in LAYERS}
STATUS_LINE = ("Computed: sums of the state's annual financial report lines, with pass-through money, transfers and "
               "borrowing left out by the guide's counting rule.")
NAMED_LINE = ("Exclusions reviewed fund by fund by name: this unit's funds don't follow an SBOA fund-number chart.")
SCHOOL_LINE = "The state's file lists school data under the year the school year begins."
NO_MONEY = ("Not in the guide's data: the guide's money in and money out figures (from the state's annual financial "
            "reports) have no rows for this unit.")
NO_POP = "No 2020 Census count for this area in the guide's data, so no per-resident figure."


# ------------------------------------------------------------------------------ one unit
def held_note_for(rows: list[dict], in_year: str | None) -> str:
    """The line civic/spending.py's income chart shows when a later receipts year is held back ('' when none)."""
    note = ""
    for y in sorted({r["year"] for r in rows if r["view"] == "income" and _held(r)}):
        if y > (in_year or ""):
            hr = next((r for r in rows if r["view"] == "income" and r["year"] == y), None)
            if hr:
                note = (hr["notes"].split("HELD (not charted): ", 1)[-1].split(" Receipt lines:")[0]
                        .split(" Folded into Other:")[0])
    return note


def summarize_rows(rows: list[dict], kind: str, top: int = 3) -> dict | None:
    """One unit's figures, with the year rules of civic/spending.py money_in_out. Pure: takes that unit's
    spending_breakdowns rows. None when the unit has no counted spending."""
    sp_year = _pick_year(rows, ("by_purpose",))
    if not sp_year:
        return None
    in_year = _pick_year(rows, ("income",))

    def sel(view, year):
        return [r for r in rows if r["view"] == view and r["year"] == year] if year else []

    def ranked(view_rows):
        tot = sum(_f(r["amount"]) for r in view_rows)
        named = sorted([r for r in view_rows if r["category"] != OTHER and _f(r["amount"]) > 0],
                       key=lambda r: -_f(r["amount"]))[:top]
        return [{"category": r["category"], "amount": _f(r["amount"]),
                 "share": (_f(r["amount"]) / tot * 100) if tot else 0.0} for r in named]

    purpose, income = sel("by_purpose", sp_year), sel("income", in_year)
    sp_excl, in_excl = sel("spending_excluded", sp_year), sel("income_excluded", in_year)
    srcs = dict.fromkeys(s for r in purpose + income + sp_excl + in_excl for s in split_ids(r["source_ids"]))
    return {
        "kind": kind,
        "spending_year": sp_year, "income_year": in_year,
        "spending_year_label": _year_label(kind, sp_year),
        "income_year_label": _year_label(kind, in_year) if in_year else "",
        "spending": sum(_f(r["amount"]) for r in purpose),
        "income": sum(_f(r["amount"]) for r in income) if income else None,
        "top_spending": ranked(purpose), "top_income": ranked(income),
        "passed_out": sum(_f(r["amount"]) for r in sp_excl),
        "passed_in": sum(_f(r["amount"]) for r in in_excl),
        "borrowed": sum(_f(r["amount"]) for r in in_excl if r["category"].startswith("Borrowed")),
        "held_note": held_note_for(rows, in_year),
        "named_review": any(r["basis"].removesuffix("_held").endswith("named_review") for r in purpose + income),
        "source_ids": ";".join(srcs),
    }


def per_resident(amount, residents) -> float | None:
    """Dollars per resident; None when either figure is missing or the population is not positive."""
    if amount is None or residents is None:
        return None
    try:
        a, p = float(amount), float(residents)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(a) or not math.isfinite(p) or p <= 0:
        return None
    return a / p


# ------------------------------------------------------------------------------ the whole map
def _target(uid: str, unit: dict | None, has_money: bool) -> str:
    """Site-relative link for an area: its Money in and money out block (civic/spending.py id money-<uid>)."""
    if unit and unit["unit_type"] == "school_corporation":
        return f"schools/index.html#{'money-' + uid if has_money else uid}"
    return f"places/{uid}/index.html" + (f"#money-{uid}" if has_money else "")


def county_population(ed) -> int | None:
    for r in ed.table("indicator_values"):
        if r["indicator_id"] == "pop_census_2020" and r["geo_type"] == "county":
            try:
                return int(float(r["value"]))
            except (TypeError, ValueError):
                return None
    return None


def county_population_source(ed) -> str:
    return next((r["source_ids"] for r in ed.table("indicator_values")
                 if r["indicator_id"] == "pop_census_2020" and r["geo_type"] == "county"), "")


def pop_source_ids(ed) -> str:
    return ";".join(sorted({s for r in ed.table("indicator_values") if r["indicator_id"] == "pop_census_2020"
                            for s in split_ids(r["source_ids"])}))


GEO_TYPES = {"place": ("place", "town"), "township": ("county_subdivision",), "school": ("school_district",)}


def census_population(ed, census_name: str | None, layer_key: str) -> int | None:
    """2020 Census count (indicator pop_census_2020) for a map shape, matched on the shape's own Census name
    ('Mishawaka city', 'Centre township', 'Mishawaka School City') against the indicator's geo_name
    ('Mishawaka city, Indiana', ...). Exact name before the first comma; None when there is no such row."""
    if not census_name:
        return None
    want = census_name.strip().lower()
    for r in ed.table("indicator_values"):
        if (r["indicator_id"] == "pop_census_2020" and r["geo_type"] in GEO_TYPES.get(layer_key, ())
                and r["geo_name"].split(",")[0].strip().lower() == want):
            try:
                return int(float(r["value"]))
            except (TypeError, ValueError):
                return None
    return None


def area_record(ed, uid: str, layer_key: str, census_name: str | None = None) -> dict:
    unit = ed.units.get(uid)
    mid = money_id_for(ed, uid) if unit else None
    summ = summarize_rows(_rows(ed, mid), _kind(ed, mid)) if mid else None
    residents = census_population(ed, census_name, layer_key)
    pr = per_resident(summ["spending"], residents) if summ else None
    # facts from other files for the panel: the certified tax base, and a school corporation's enrollment and
    # spending per student (plain-text [label, value] pairs)
    extra = tax_base.panel_facts(ed, mid or tax_base.money_id(ed, uid), residents) if unit else []
    if unit and unit["unit_type"] == "school_corporation":
        extra += school_stats.panel_facts(ed, uid)
    return {"uid": uid, "layer": layer_key, "mid": mid if summ else None, "summary": summ, "residents": residents,
            "per_resident": pr, "target": _target(uid, unit, bool(summ)), "extra_facts": extra}


def money_map_data(ed, shapes: dict) -> dict:
    """Everything the money map and its tables show. Per layer: areas (shape order), breaks, class count, the
    ramp shade of each class and the year labels used. Plus the county and every money unit with no boundary."""
    layers = {}
    mapped = set()
    for key, tab, label, _heading in LAYERS:
        areas = []
        for it in shapes["layers"].get(key, []):
            uid = it.get("id")
            if not uid or uid not in ed.units:
                areas.append({"uid": uid, "layer": key, "mid": None, "summary": None, "residents": None,
                              "per_resident": None, "target": None, "census_name": it.get("census_name")})
                continue
            a = area_record(ed, uid, key, it.get("census_name"))
            areas.append(a)
            if a["mid"]:
                mapped.add(a["mid"])
        breaks = class_breaks([a["per_resident"] for a in areas])
        k = len(breaks) + 1
        pos = ramp_positions(k)
        for a in areas:
            st = step_of(a["per_resident"], breaks)
            a["step"] = st
            a["shade"] = pos[st] if st is not None else None
        years = sorted({a["summary"]["spending_year_label"] for a in areas if a["summary"]})
        layers[tab] = {"key": key, "label": label, "areas": areas, "breaks": breaks, "classes": k, "shades": pos,
                       "years": years, "counts": [sum(1 for a in areas if a["step"] == i) for i in range(k)]}
    all_mids = list(dict.fromkeys(r["unit_id"] for r in ed.table("spending_breakdowns")))
    others = []
    county = None
    for mid in all_mids:
        if mid in mapped:
            continue
        kind = _kind(ed, mid)
        summ = summarize_rows(_rows(ed, mid), kind)
        if not summ:
            continue
        rec = {"mid": mid, "kind": kind, "summary": summ, "residents": None, "per_resident": None,
               "anchor": f"money-{ed.unit_alias(mid) or mid}"}
        if kind == "county":
            rec["residents"] = county_population(ed)
            rec["per_resident"] = per_resident(summ["spending"], rec["residents"])
            rec["target"] = f"county/index.html#{rec['anchor']}"
            county = rec
        else:
            rec["target"] = f"money/budgets/index.html#{rec['anchor']}"
        others.append(rec)
    return {"layers": layers, "county": county, "others": others}


# ------------------------------------------------------------------------------ rendering
def _year_text(s: dict) -> str:
    if s["income_year"] and s["income_year"] != s["spending_year"]:
        return f"Spending: {s['spending_year_label']}; income: {s['income_year_label']}"
    return s["spending_year_label"]


def _per_res_text(a: dict) -> str:
    if a["per_resident"] is None:
        return NO_POP if a["summary"] else "not in the guide's data"
    return (f"{money_text(a['per_resident'])} (counted spending divided by {fmt_int(a['residents'])} residents, "
            "2020 Census count)")


def caveats(s: dict) -> list[str]:
    """The year's notes that civic/spending.py shows with the charts, as short lines for the panel."""
    out = []
    if s["held_note"]:
        out.append(s["held_note"] + f" Income shown: {s['income_year_label']}.")
    if s["kind"] == "school":
        out.append(SCHOOL_LINE)
    if s["named_review"]:
        out.append(NAMED_LINE)
    if s["borrowed"]:
        yl = s["income_year_label"]
        out.append(f"Also borrowed {usd(s['borrowed'])} in {'the ' if s['kind'] == 'school' else ''}{yl} "
                   "(not counted as income).")
    return out


def _bars(title: str, items: list[dict]):
    return [title, [[b["category"], f"{b['share']:.0f}%", round(b["share"], 1), usd_short(b["amount"])] for b in items]]


def panel_entry(a: dict, unit: dict, tab: str, d: str, href: str) -> dict:
    s = a["summary"]
    tlabel = TYPE_LABEL.get(unit["unit_type"], unit["unit_type"])
    if not s:
        return {"n": unit["name"], "t": tlabel, "f": [["Money in and money out", NO_MONEY]] + a.get("extra_facts", []),
                "note": "", "href": href, "l": tab, "d": d, "open": "Open its section"}
    facts = [["Year", _year_text(s)],
             ["Counted income", usd(s["income"]) if s["income"] is not None else "not in the guide's data"],
             ["Counted spending", usd(s["spending"])],
             ["Spending per resident", _per_res_text(a)],
             ["Passed through or moved between funds",
              f"{usd(s['passed_in'])} in, {usd(s['passed_out'])} out (not counted above)"],
             ["Data status", STATUS_LINE]] + a.get("extra_facts", [])
    bars = []
    if s["top_income"]:
        bars.append(_bars("Largest income sources (share of counted income)", s["top_income"]))
    if s["top_spending"]:
        bars.append(_bars("Largest spending purposes (share of counted spending)", s["top_spending"]))
    return {"n": unit["name"], "t": tlabel, "f": facts, "note": "", "cav": caveats(s), "bars": bars,
            "href": href, "l": tab, "d": d, "open": "See the full breakdown"}


def _aria(a: dict, unit: dict) -> str:
    tlabel = TYPE_LABEL.get(unit["unit_type"], unit["unit_type"]).lower()
    if not a["summary"]:
        return f"{unit['name']}, {tlabel}: no money data in the guide. Open its section."
    pr = money_text(a["per_resident"]) if a["per_resident"] is not None else "no per-resident figure"
    return (f"{unit['name']}, {tlabel}: counted spending {usd_short(a['summary']['spending'])}, {pr} per resident, "
            f"{a['summary']['spending_year_label']}. Open its money in and money out section.")


def _shade_cls(a: dict) -> str:
    return f"cmap-mm-{a['shade']}" if a.get("shade") else "cmap-mm-none"


def legend_title(layer: dict) -> str:
    yrs = layer["years"]
    yr = yrs[0] if len(yrs) == 1 else "latest year for each"
    return f"Counted spending per resident, {yr}"


def money_map(page, ed, shapes: dict, mm: dict, default_layer: str = "cities") -> Markup:
    by_uid = {a["uid"]: a for L in mm["layers"].values() for a in L["areas"] if a["uid"]}

    def area(key, tab, n, it, uid, unit):
        a = by_uid[uid]
        href = page.rel(a["target"])
        cls = _shade_cls(a)
        return (f"cmap-s cmap-mm {cls}", href, _aria(a, unit), panel_entry(a, unit, tab, it["d"], href),
                f"cmap-dot cmap-mm-dot {cls}")

    legends = []
    for key, tab, label, _heading in LAYERS:
        L = mm["layers"][tab]
        cls = {"breaks": L["breaks"], "shades": L["shades"], "counts": L["counts"],
               "none": sum(1 for a in L["areas"] if a["step"] is None)}
        extra = [("cmap-mm-back", "Outside any city or town (not shaded)")] if key == "place" else []
        legends.append(shade_legend(legend_title(L), cls, extra=extra,
                                    attrs={"class": "cmap-mlegend" + (" is-on" if tab == default_layer else ""),
                                           "data-layer": tab}))
    # data-hash="off" (embedded_map): the budgets page keeps its own #anchors
    return embedded_map(page, ed, shapes, ("cities", "townships", "schools"), default_layer, area=area,
                        label=f"Money map of {ed.county_label}: counted spending per resident. Every area is a link; "
                              "tables with every figure follow the map.",
                        hint="Hover, focus or tap an area to see its money here. Select it again, or use the link, to "
                             "open its full breakdown.",
                        legend=legends, defs=shade_defs(), extra_cls="cmap-money", back_cls="cmap-s cmap-mm-back")


def county_figure(page, ed, mm: dict) -> Markup | None:
    rec = mm["county"]
    if not rec:
        return None
    s = rec["summary"]
    c = page.cites
    pr = (f", or {money_text(rec['per_resident'])} per resident ({fmt_int(rec['residents'])} residents, 2020 Census count)"
          if rec["per_resident"] is not None else "")
    inc = f" Counted income: {usd(s['income'])} ({s['income_year_label']})." if s["income"] is not None else ""
    return h("p", {"class": "cmap-mcounty"},
             h("strong", None, "County government: "),
             f"counted spending {usd(s['spending'])} in {s['spending_year_label']}{pr}.{inc} The county serves everyone in "
             "the county, so it is one figure here, not a map layer. ",
             h("a", {"href": page.rel(rec["target"])}, "County breakdown"), ". ",
             status_badge("computed", page, STATUS_LINE), c.cite(s["source_ids"] + ";" + county_population_source(ed)))


def method_note(page, ed) -> Markup:
    return h("p", {"class": "muted cmap-mnote"},
             "How the shading is figured: each government's counted spending in its latest year in the state's annual "
             "financial reports (money passed through to other governments, moved between its own funds or borrowed is "
             "left out), divided by the 2020 Census count of people living in its area. Township government serves "
             "everyone in the township, including residents of cities and towns inside it, so a township's figure is "
             "divided by the whole township's population; a school corporation's by everyone living in its district "
             "(residents, not students; districts that extend past the county line count their whole population, "
             "because their spending covers the whole district). Breaks are set separately for each layer, because a "
             "city spends far more per resident than a township, so compare shades only within a layer. A figure equal "
             "to a break falls in the higher step. ", page.cites.cite_compact(pop_source_ids(ed) + ";MON-060;MON-061"))


def _row(page, ed, name_cell, type_label, s, residents, pr, target, link_text):
    if not s:
        return [name_cell, type_label, "", "", "", fmt_int(residents) if residents else "", "", "No data"]
    return [name_cell, type_label, _year_text(s),
            usd(s["income"]) if s["income"] is not None else "not in the guide's data",
            usd(s["spending"]), fmt_int(residents) if residents else "no population figure",
            money_text(pr) if pr is not None else "",
            h("a", {"href": page.rel(target)}, link_text) if target else ""]


HEADS = ["Area", "Type", "Year", "Counted income", "Counted spending", "Residents (2020 Census)",
         "Spending per resident", "Breakdown"]


def money_map_tables(page, ed, mm: dict, label) -> Markup:
    """Every mapped area by layer, then the units with no boundary on the map. Present with or without JavaScript."""
    out = []
    for key, tab, lab, heading in LAYERS:
        L = mm["layers"][tab]
        rows = []
        for a in sorted(L["areas"], key=lambda a: (ed.units[a["uid"]]["name"] if a["uid"] in ed.units else a.get("census_name") or "").lower()):
            if not a["uid"] or a["uid"] not in ed.units:
                rows.append([a.get("census_name") or "", "", "", "", "", "", "", "No page in the guide yet"])
                continue
            u = ed.units[a["uid"]]
            rows.append(_row(page, ed, u["name"], TYPE_LABEL.get(u["unit_type"], ""), a["summary"], a["residents"],
                             a["per_resident"], a["target"], "Full breakdown" if a["summary"] else "Its section"))
        out.append(h("h4", None, heading))
        out.append(data_table(f"mm-table-{tab}", HEADS, rows, caption=f"{heading}: money in, money out and spending per "
                                                                        "resident", numeric=(3, 4, 5, 6), min_width="52rem"))
    rows = []
    for rec in mm["others"]:
        s = rec["summary"]
        typ = {"county": "County", "library": "Library", "special": "Special unit"}.get(rec["kind"], rec["kind"].title())
        rows.append(_row(page, ed, label(rec["mid"]), typ, s, rec["residents"], rec["per_resident"], rec["target"],
                         "Full breakdown"))
    out.append(h("h4", {"id": "money-map-others"}, "Governments with no boundary on the map"))
    out.append(h("p", {"class": "muted"}, "The county, the libraries and the special units (such as the airport, Transpo, "
                                          "solid waste and redevelopment) serve areas the map doesn't draw, so they are "
                                          "listed here. A per-resident figure is given only where the guide has a "
                                          "population for the area served (the county)."))
    out.append(data_table("mm-table-others", HEADS, rows, caption="Governments with no boundary on the map: money in and "
                                                                  "money out", numeric=(3, 4, 5, 6), min_width="52rem"))
    return h("div", {"class": "cmap-mtables"}, out)
