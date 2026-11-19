"""Money section: hub, budget primer, tax-bill split and budgets by unit.

    money/index.html                 hub with computed headline facts
    money/what-is-a-budget/          definitions primer (bases, adopted vs actual, Gateway/DLGF, nominal dollars)
    money/your-tax-bill/             one bill split among the units that tax a property (picker; money.js)
    money/budgets/                   every unit's budget 2012-2026, one basis per chart, breaks and flags drawn

The money files (budgets, budget_breakdowns, tax_rates, debt) use a type-prefixed id scheme
('city-south-bend'); ``ed.unit_alias()`` maps them to units.csv. Units with no units.csv row are
still shown, labelled with the name the state budget file uses (GATEWAY_LABELS).
money/campaigns/ is built by another module.
"""
from __future__ import annotations

import math
import re
from collections import OrderedDict

from civic.charts import columns, figure, fmt_tick, hbar, line, nice_ticks
from civic.components import callout, data_table, scope_badge, section, see_all_fold, status_badge, variant_slot
from civic.data import fmt_date, split_ids
from civic.html import Markup, h, join, json_script
from civic.layers import build_layers
from civic.spending import has_money_in_out, money_in_out
from civic.map import load_shapes
from civic import governments as gm
from civic import tabs as T
from civic import tax_base as tb
from civic.money_map import county_figure, method_note, money_map, money_map_data, money_map_tables
from civic.preselect import district_hints, here_slot
from civic.pick_one import (one_bar, one_chips, one_empty, one_fold, one_row, one_scope, one_summary,
                            one_wrap_see_all)

# Unit names as the state budget file (Gateway, MON-001) lists them; tools/build_money.py
# carries the same mapping. Used for units with no units.csv row and to match gaps_money items.
GATEWAY_LABELS = {
    "county-st-joseph": "St. Joseph County",
    "city-south-bend": "City of South Bend (civil city)",
    "city-mishawaka": "City of Mishawaka (civil city)",
    "town-indian-village": "Indian Village",
    "town-lakeville": "Town of Lakeville",
    "town-new-carlisle": "Town of New Carlisle",
    "town-north-liberty": "Town of North Liberty",
    "town-osceola": "Town of Osceola",
    "town-roseland": "Town of Roseland",
    "town-walkerton": "Town of Walkerton",
    "township-centre": "Centre Township (state data: Centre)",
    "township-clay": "Clay Township",
    "township-german": "German Township",
    "township-greene": "Greene Township",
    "township-harris": "Harris Township",
    "township-liberty": "Liberty Township",
    "township-lincoln": "Lincoln Township",
    "township-madison": "Madison Township",
    "township-olive": "Olive Township",
    "township-penn": "Penn Township",
    "township-portage": "Portage Township",
    "township-union": "Union Township",
    "township-warren": "Warren Township",
    "school-john-glenn": "John Glenn School Corporation",
    "school-mishawaka": "School City of Mishawaka",
    "school-phm": "Penn-Harris-Madison School Corporation",
    "school-sbcsc": "South Bend Community School Corporation",
    "school-union-north": "Union-North United School Corporation",
    "library-mishawaka": "Mishawaka-Penn-Harris Public Library (state data: Mishawaka Public Library)",
    "library-new-carlisle": "New Carlisle Public Library",
    "library-sjcpl": "St. Joseph County Public Library",
    "library-walkerton": "Walkerton Public Library",
    "special-sb-transpo": "South Bend Public Transportation Corporation",
    "special-airport": "St. Joseph County Airport Authority (state data: St. Joseph Airport)",
    "special-solid-waste": "St. Joseph County Solid Waste Management District",
    "special-sb-redevelopment": "South Bend Redevelopment Commission",
    "special-regional-water-sewer": "St. Joseph County Regional Water and Sewer District",
    "school-new-prairie": "New Prairie United School Corporation",
    "special-olive-new-carlisle-hudson-fpt": "Olive-New Carlisle-Hudson Fire Protection Territory",
    "special-redevelopment-authority": "St. Joseph Redevelopment Authority",
}


GROUPS = [("county", "County"), ("city", "Cities"), ("town", "Towns"), ("township", "Townships"),
          ("school", "School corporations"), ("library", "Public libraries"), ("special", "Special units")]

BASIS = {
    "general_fund": ("General fund", "One fund: the unit's General fund (Gateway fund 0101)."),
    "advertised_all_funds": ("All advertised funds",
                             "The sum of every fund the unit advertised to the state for that year."),
    "all_funds_incl_utilities": ("All funds including utilities",
                                 "Every fund, including water, sewer, trash and other enterprise funds."),
    "gateway_reported_funds": ("Funds Gateway lists from 2024 (10 funds)",
                               "Only the 10 property-tax-supported funds the state file lists for South Bend from 2024."),
}
# a one-off basis shown in tables only (never charted): the DLGF budget order total
BASIS["dlgf_certified"] = ("State-certified budget (DLGF budget order)",
                           "The total of the funds the state's Department of Local Government Finance certified in its budget order.")
# a one-off basis shown in tables only (never charted): the current amended budget from a later financial report
BASIS["amended_all_funds"] = ("Amended budget, all funds (later financial report)",
                              "The unit's current amended budget for every fund it controls, from a financial report "
                              "published after the budget was adopted.")
BASIS_ORDER = ["general_fund", "advertised_all_funds", "all_funds_incl_utilities", "gateway_reported_funds"]

JUMP_THRESHOLD = 0.40   # same rule as tools/check_money.py


# =================================================================== helpers

def usd(v) -> str:
    return f"${float(v):,.0f}"


def usd_short(v) -> str:
    v = float(v)
    a = abs(v)
    if a >= 1e9:
        return f"${v / 1e9:.2f}B"
    if a >= 1e7:
        return f"${v / 1e6:.1f}M"
    if a >= 1e6:
        return f"${v / 1e6:.2f}M"
    if a >= 1e4:
        return f"${v / 1e3:.0f}K"
    return f"${v:,.0f}"


def rate_fmt(v) -> str:
    return f"${float(v):.4f}"


def union_sources(rows) -> str:
    seen = []
    for r in rows:
        for s in split_ids(r.get("source_ids")):
            if s not in seen:
                seen.append(s)
    return ";".join(seen)


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.])\s+(?=[A-Z(\"])", (text or "").strip()) if s]


# notes in the money files sometimes point to other rows by series id; readers see plain words instead
_SERIES_REFS = [
    (r"News figures are in series county-news-wndu-2026 and county-news-auditor-2026",
     "The news figures (WNDU, and the county auditor as quoted by WNDU) are listed in the table below the charts"),
    (r" \(see series county-gateway-general-fund\)", " (see the general fund chart)"),
    (r"for 2024-2025 use the news all-funds series sb-news-allfunds", "for 2024-2025 the chart shows news-reported all-funds totals"),
    (r"; see series sbcsc-news-board-vote\)", "; see the table below the chart)"),
    (r"see series sbcsc-news-board-vote", "see the table below the chart"),
    (r"the auditor quote in county-news-auditor-2026", "the auditor quote"),
]


def clean_note(text: str) -> str:
    for pat, rep in _SERIES_REFS:
        text = re.sub(pat, rep, text or "")
    return text


def join_text(*parts) -> str:
    return " ".join(p for p in parts if p)


def group_of(mid: str) -> str:
    return mid.split("-", 1)[0]


class Money:
    """The money files, indexed once per build (cached on the edition)."""

    def __init__(self, ed):
        self.ed = ed
        self.budgets = ed.table("budgets")
        self.breakdowns = ed.table("budget_breakdowns")
        self.rates = ed.table("tax_rates")
        self.debt = ed.table("debt")
        ids = []
        for t in (self.budgets, self.rates, self.debt, self.breakdowns):
            for r in t:
                if r["unit_id"] not in ids:
                    ids.append(r["unit_id"])
        for r in ed.table("derived/unit_id_aliases"):
            if r["unit_id"] and r["alias_id"] not in ids:
                ids.append(r["alias_id"])
        order = {g: i for i, (g, _) in enumerate(GROUPS)}
        self.unit_ids = sorted(ids, key=lambda m: (order.get(group_of(m), 99), self.label(m).lower()))
        # series
        self.series: "OrderedDict[str, dict]" = OrderedDict()
        for r in self.budgets:
            s = self.series.setdefault(r["series_id"], {"id": r["series_id"], "unit": r["unit_id"], "basis": r["basis"],
                                                         "rows": [], "breaks": []})
            if r["adopted_or_actual"] == "series_break":
                s["breaks"].append(r)
            else:
                s["rows"].append(r)
        for s in self.series.values():
            s["rows"].sort(key=lambda r: int(r["year"]))
            s["status"] = sorted({r["status"] for r in s["rows"]})
            s["kinds"] = sorted({r["adopted_or_actual"] for r in s["rows"]})
        years = [int(r["year"]) for r in self.budgets if r["amount"]]
        self.y0, self.y1 = min(years), max(years)
        self.jumps = self._jumps()
        # CPI-U annual averages (data/indiana/cpi_u.csv) for the constant-dollar view; base = latest year
        self.cpi = {int(r["year"]): float(r["cpi_u_annual_avg"]) for r in ed.table("cpi_u") if r.get("cpi_u_annual_avg")}
        self.cpi_base = max(self.cpi) if self.cpi else None
        self.cpi_src = ";".join(sorted({r["source_id"] for r in ed.table("cpi_u") if r.get("source_id")}))

    # ---- names and anchors ---------------------------------------------------
    def _uid(self, mid: str) -> str | None:
        """The units.csv id of a money id (derived/unit_id_aliases.csv)."""
        return self.ed.unit_alias(mid)

    def label(self, mid: str) -> str:
        uid = self._uid(mid)
        if uid and uid in self.ed.units:
            return self.ed.units[uid]["name"]
        return GATEWAY_LABELS.get(mid, mid)

    def anchor(self, mid: str) -> str:
        return self._uid(mid) or mid

    def has_budget(self, mid: str) -> bool:
        return any(s["unit"] == mid for s in self.series.values())

    def in_units_csv(self, mid: str) -> bool:
        return bool(self._uid(mid))

    # ---- year-over-year check (tools/check_money.py rule) -----------------------
    def _jumps(self) -> list[dict]:
        out = []
        for s in self.series.values():
            ys = {int(r["year"]): float(r["amount"]) for r in s["rows"] if r["amount"]}
            brk = {int(b["year"]) for b in s["breaks"]}
            for y in sorted(ys):
                if y - 1 in ys:
                    a, b = ys[y - 1], ys[y]
                    if a > 0 and abs(b / a - 1) > JUMP_THRESHOLD and y not in brk and (y - 1) not in brk:
                        out.append({"series": s["id"], "unit": s["unit"], "y0": y - 1, "y1": y, "a": a, "b": b,
                                    "pct": (b / a - 1) * 100})
        return out

    def jump_gap_rows(self) -> list[dict]:
        """gaps_money rows for flagged jumps, plus a computed row for each flag the file doesn't list."""
        listed = [g for g in self.ed.gaps(files=["gaps_money"]) if "unexplained budget jump" in g.get("item", "")]
        out = []
        for j in self.jumps:
            key = f"{GATEWAY_LABELS.get(j['unit'], j['unit'])} {j['y0']}-{j['y1']}"
            hit = next((g for g in listed if g["item"].startswith(key + ":")), None)
            if hit:
                # same label and number format as the computed rows: the guide's unit name, and
                # dollar amounts with thousands separators (the file writes them as raw digits)
                why = re.sub(r"\$(\d{4,})(?![\d,])", lambda m: usd(m.group(1)), hit.get("why_missing", ""))
                out.append(dict(hit, item=f"{self.label(j['unit'])} {j['y0']}-{j['y1']}: unexplained budget change",
                                why_missing=why))
            else:
                out.append({"item": f"{self.label(j['unit'])} {j['y0']}-{j['y1']}: unexplained budget change",
                            "why_missing": f"Adopted total moved {j['pct']:+.0f}% (from {usd(j['a'])} to {usd(j['b'])}) "
                                           "with no documented change in reporting basis. Flagged by the guide's "
                                           "year-over-year check; no reason is recorded in the guide's data.",
                            "how_to_fill": "Check the unit's budget notices or fund detail in Gateway for that year."})
        return out

    # ---- population (for per-resident figures) ---------------------------------
    def population(self, mid: str) -> dict | None:
        rows = [r for r in self.ed.table("indicator_values")
                if r["indicator_id"] == "pop_total" and r["vintage"].startswith("ACS 2020-2024")]
        g = group_of(mid)
        for r in rows:
            name = r["geo_name"].lower()
            if mid == "county-st-joseph" and r["geo_type"] == "county":
                return r
            if mid == "city-south-bend" and r["geo_type"] == "place" and name.startswith("south bend city"):
                return r
            if mid == "city-mishawaka" and r["geo_type"] == "place" and name.startswith("mishawaka city"):
                return r
            if g == "township" and r["geo_type"] == "county_subdivision":
                if name.startswith(mid.split("-", 1)[1] + " township"):
                    return r
        return None


def money(ed) -> Money:
    m = getattr(ed, "_money_cache", None)
    if m is None:
        m = Money(ed)
        ed._money_cache = m
    return m


def money_gaps(ed, pattern: str | None = None, exclude_cf: bool = True) -> list[dict]:
    rows = ed.gaps(files=["gaps_money"], pattern=pattern)
    if exclude_cf:
        rows = [g for g in rows if not re.search(r"campaign finance|party committee finances", g.get("item", ""), re.I)]
    return [g for g in rows if "unexplained budget jump" not in g.get("item", "")]


CPI_GAP = {"item": "Inflation-adjusted budget figures",
           "why_missing": "The guide's data has no consumer price index series, so every dollar figure is nominal "
                          "(the dollars of that year). An inflation-adjusted view is not offered.",
           "how_to_fill": "Add a sourced price-index series (for example the BLS CPI-U annual average) to the data folder."}


def cpi_gaps(mo) -> list[dict]:
    if not mo.cpi:
        return [CPI_GAP]
    return [{"item": f"Constant-dollar figures for {mo.cpi_base + 1}",
             "why_missing": f"The CPI-U annual average for {mo.cpi_base + 1} isn't published yet, so {mo.cpi_base + 1} "
                            "budgets are shown only in nominal dollars.",
             "how_to_fill": "Add the annual average to data/indiana/cpi_u.csv when the BLS publishes it."}]


def hero(page, eyebrow: str, title: str, dek, toc: list[tuple[str, str]], badges) -> Markup:
    return h("header", {"class": "page-hero"},
             h("p", {"class": "eyebrow mono"}, eyebrow),
             h("h1", None, title),
             h("p", {"class": "dek"}, dek),
             h("p", {"class": "hero-badges"}, badges),
             h("nav", {"class": "toc", "aria-label": "On this page"},
               h("ol", None, [h("li", None, h("a", {"href": f"#{a}"}, t)) for a, t in toc])))


# =================================================================== chart: annotated columns

def flag_columns(fid: str, title: str, points: list[dict], subtitle=None, breaks=None, flags=None,
                 legend_items=None, note=None, status=None, page=None, cite=None, gaps_href="#gaps") -> Markup:
    """Column chart for one budget basis, with per-point marks, a legend, series breaks and flags ({index: text}
    draws a marker above the column: 'unexplained change; see Gaps').

    Changed 2026-11-18 (phase 6 step 5): drawn as HTML instead of a fixed-width SVG, so the columns use the whole
    width of the column they sit in at any screen size (the SVG was at most 760 px wide, about half a government
    Money tab), while the labels stay real text at their normal size. Same signature, same figure id, same table
    view, same figures; heights and positions are inline percentages (style attributes are allowed by the CSP for
    chart positions). Each column is focusable and carries the shared tooltip attributes (data-tv / data-tl)."""
    flags = flags or {}
    vals = [p["value"] for p in points if p.get("value") is not None]
    vmax = max(vals) if vals else 1
    ticks = nice_ticks(vmax)
    top = ticks[-1] or 1
    n = max(len(points), 1)
    labelled = set()
    if vals:
        idx = [i for i, p in enumerate(points) if p.get("value") is not None]
        last, peak = idx[-1], max(idx, key=lambda i: points[i]["value"])
        labelled = {last, peak} - set(flags)
        if peak != last and abs(last - peak) < 3:
            labelled.discard(peak)     # two value labels on nearby columns collide; keep the latest value only
    pct = lambda v: max(0.0, min(100.0, 100.0 * v / top))
    grid = [h("span", {"class": "fcol-grid" + (" fcol-base" if not t else ""), "style": f"bottom:{pct(t):.2f}%"},
              h("span", {"class": "fcol-tick"}, fmt_tick(t, top, True))) for t in ticks]
    every = 1 if n <= 8 else 2
    cols, xs = [], []
    for i, p in enumerate(points):
        xl_cls = "fcol-xl" + ("" if (i % every == 0 or i == n - 1) else " fcol-xl-odd")
        xs.append(h("span", {"class": xl_cls}, str(p["x"])))
        if p.get("value") is None:
            cols.append(h("span", {"class": "fcol-c fcol-empty"},
                          h("span", {"class": "visually-hidden"}, f"{p['x']}: no figure")))
            continue
        disp = p.get("display") or usd_short(p["value"])
        tipl = p.get("tip") or str(p["x"])
        if i in flags:
            tipl += " · " + flags[i]
        hgt = pct(p["value"])
        kids = [h("span", {"class": f"fcol-bar {p.get('mark', 'm-accent')}", "style": f"height:{max(hgt, 0.4):.2f}%",
                           "aria-hidden": "true"})]
        if i in labelled:
            kids.append(h("span", {"class": "fcol-v", "style": f"bottom:{hgt:.2f}%", "aria-hidden": "true"}, disp))
        if i in flags:
            kids.append(h("span", {"class": "fcol-flagline", "style": f"bottom:{hgt:.2f}%", "aria-hidden": "true"}))
            kids.append(h("span", {"class": "fcol-flag mn-flag-key", "aria-hidden": "true"}, "!"))
        cols.append(h("span", {"class": "fcol-c mark", "tabindex": "0", "data-tv": disp, "data-tl": tipl,
                               "aria-label": f"{p['x']}: {disp}" + (f". {flags[i]}" if i in flags else "")}, kids))
    brk = []
    for b in breaks or []:
        left = 100.0 * (b["after"] + 1) / n
        brk.append(h("span", {"class": "fcol-break mark" + (" fcol-break-r" if left > 70 else ""),
                              "style": f"left:{left:.2f}%", "tabindex": "0", "data-tv": b["label"],
                              "data-tl": b.get("tip", ""), "aria-label": b["label"]},
                     h("span", {"class": "fcol-break-l"}, b["label"])))
    body = h("div", {"class": "fcol", "role": "group", "aria-label": f"{title}. Column chart; values in the table view."},
             h("div", {"class": "fcol-plot"},
               h("div", {"class": "fcol-area"}, grid, h("div", {"class": "fcol-cols"}, cols), brk)),
             h("div", {"class": "fcol-x", "aria-hidden": "true"}, xs))
    items = []
    for cls, lab in legend_items or []:
        items.append(h("li", None, h("span", {"class": f"key key-rect {cls}", "aria-hidden": "true"}), lab))
    if flags:
        items.append(h("li", None, h("span", {"class": "mn-flag-key", "aria-hidden": "true"}, "!"),
                       "Unexplained change of more than 40% from the year before; ", h("a", {"href": gaps_href}, "see Gaps")))
    if breaks:
        items.append(h("li", None, h("span", {"class": "mn-break-key", "aria-hidden": "true"}),
                       "Series break: the reporting basis changes"))
    leg = h("ul", {"class": "legend"}, items) if items else None
    rows = []
    for i, p in enumerate(points):
        if p.get("value") is None and not p.get("row_note"):
            rows.append([p["x"], "no data", "", ""])
            continue
        notes = [x for x in (flags.get(i), p.get("row_note")) if x]
        rows.append([p["x"], usd(p["value"]) if p.get("value") is not None else "no data",
                     status_badge(p["status"], page) if p.get("status") else "", " ".join(notes)])
    return figure(fid, title, subtitle, body, ["Year", "Amount", "Status", "Note"], rows, note=note, numeric=(1,),
                  status=status, page=page, legend=leg, kind="columns", cite=cite, scroll=False)


# =================================================================== budgets page

def _unit_charts(mo: Money, page, mid: str, gap_flags: dict, gaps_href: str = "#gaps") -> tuple[list, list]:
    """Charts for one unit (one per basis) and table rows for figures kept out of the charts. ``gaps_href``: where the
    flags' "see Gaps" links go (a government page's Money tab sends them to its Sources tab; phase 6 step 3)."""
    ed = mo.ed
    c = page.cites
    years = list(range(mo.y0, mo.y1 + 1))
    unit_series = [s for s in mo.series.values() if s["unit"] == mid]
    charts, others = [], []
    for basis in BASIS_ORDER:
        group = [s for s in unit_series if s["basis"] == basis]
        primary = [s for s in group if "adopted" in s["kinds"] and set(s["status"]) <= {"official", "computed"}]
        if not primary:
            continue
        prim_years = {int(r["year"]) for s in primary for r in s["rows"]}
        in_chart = list(primary)
        for s in group:
            if s in primary:
                continue
            sy = {int(r["year"]) for r in s["rows"]}
            # a secondary multi-year series of the same basis joins the chart only where the
            # primary has no figures (a continuation after a break); otherwise it goes in the table
            if _series_charted(s, unit_series):
                in_chart.append(s)
        by_year = {}
        for s in in_chart:
            secondary = s not in primary
            for r in s["rows"]:
                by_year[int(r["year"])] = (s, r, secondary)
        # each primary series' shared first sentence goes once under the chart, not on every row
        commons = {}
        for s in primary:
            # the whole-corporation phrase is shown once per page (whole_corporation_note), not under each chart
            notes = [strip_whole_corp(r["notes"]) for r in s["rows"]]
            first = sentences(notes[0])[:1] if notes else []
            commons[s["id"]] = first[0] if first and all(n.startswith(first[0]) for n in notes) else None
        points, flags = [], {}
        for i, yv in enumerate(years):
            if yv not in by_year:
                points.append({"x": yv, "value": None})
                continue
            s, r, secondary = by_year[yv]
            common = commons.get(s["id"])
            rn = strip_whole_corp(r["notes"])
            extra = rn[len(common):].strip() if common and rn.startswith(common) else rn
            extra = clean_note(extra)
            src_label = "news report (secondary)" if secondary else _source_label(s)
            points.append({"x": yv, "value": float(r["amount"]), "status": r["status"],
                           "mark": "m-ink" if secondary else "m-accent",
                           "tip": f"{yv} · {BASIS[basis][0]} · {src_label}",
                           "row_note": extra if (secondary or extra) else ""})
        for j in mo.jumps:
            if any(j["series"] == s["id"] for s in in_chart):
                flags[years.index(j["y1"])] = (f"Unexplained change: {j['pct']:+.0f}% from {j['y0']} "
                                                f"({usd_short(j['a'])} to {usd_short(j['b'])}); see Gaps")
        breaks, break_notes = [], []
        seen = set()
        for s in in_chart:
            for b in s["breaks"]:
                yb = int(b["year"])
                if yb in seen or yb not in years:
                    continue
                seen.add(yb)
                ss = sentences(clean_note(b["notes"]))
                breaks.append({"after": years.index(yb) - 1, "label": f"Basis changes in {yb}",
                               "tip": " ".join(ss[1:3])})
                break_notes.append(h("span", None, h("strong", None, f"Series break, {yb}: "), " ".join(ss[1:]),
                                     c.cite(b["source_ids"])))
        legend_items = []
        if len(in_chart) > 1:
            # the solid columns are every primary (official) series; name each one's real source and years
            prim_labels = [f"{_source_label(s)}, {_year_span(s)}" for s in primary]
            legend_items = [("m-accent", "Adopted: " + "; ".join(prim_labels))]
            if any(s not in primary for s in in_chart):
                legend_items.append(("m-ink", "News report, rounded (secondary)"))
        status = "official" if all(s["status"] == ["official"] for s in primary) else "computed"
        name = mo.label(mid)
        title = f"{name}: {BASIS[basis][0].lower()}, adopted" if basis != "gateway_reported_funds" else f"{name}: {BASIS[basis][0]}"
        n_years = len([p for p in points if p.get("value") is not None])
        sub = f"{BASIS[basis][1]} {n_years} years with figures, {years[0]} to {years[-1]}. Nominal dollars."
        note_parts = []
        for s in primary:
            if commons.get(s["id"]):
                lead = f"{_source_label(s)[0].upper()}{_source_label(s)[1:]}, {_year_span(s)}: " if len(primary) > 1 else ""
                note_parts.append(h("span", None, lead, commons[s["id"]], " "))
        note_parts += break_notes
        src = union_sources(r for s in in_chart for r in s["rows"])
        fid = f"bud-{mid}-{basis.replace('_', '-')}"
        nominal = flag_columns(fid, title, points, subtitle=sub, breaks=breaks,
                               flags=flags, legend_items=legend_items, note=join(note_parts, " ") if note_parts else None,
                               status=status, page=page, cite=c.cite(src), gaps_href=gaps_href)
        cpi = mo.cpi
        if not cpi:
            charts.append(nominal)
            continue
        real_pts = []
        for p in points:
            q = dict(p)
            if p.get("value") is not None:
                if p["x"] in cpi and p["x"] <= mo.cpi_base:
                    q["value"] = p["value"] * cpi[mo.cpi_base] / cpi[p["x"]]
                    q["display"] = None
                    q["status"] = "computed"
                    q["row_note"] = join_text(f"Nominal {usd(p['value'])}.", p.get("row_note"))
                else:
                    q["value"] = None
                    q["status"] = ""
                    q["row_note"] = join_text(f"Not adjusted: no annual CPI-U for {p['x']} yet (nominal {usd(p['value'])}).",
                                              p.get("row_note"))
            real_pts.append(q)
        real_flags = {i: t.replace("Unexplained change:", "Unexplained change (nominal dollars):") for i, t in flags.items()}
        real_sub = (f"{BASIS[basis][1]} Constant {mo.cpi_base} dollars: each year's amount times the CPI-U ratio "
                    f"({mo.cpi_base} annual average / that year's). {mo.cpi_base + 1} onward not adjusted.")
        real = flag_columns(fid + "-real", f"{title}, in {mo.cpi_base} dollars", real_pts, subtitle=real_sub, breaks=breaks,
                            flags=real_flags, legend_items=legend_items,
                            note=join(note_parts, " ") if note_parts else None,
                            status="computed", page=page, cite=c.cite(src + ";" + mo.cpi_src), gaps_href=gaps_href)
        charts.append(h("div", {"class": "mn-dollars-block", "data-dollars": "nominal"}, nominal))
        charts.append(h("div", {"class": "mn-dollars-block", "data-dollars": "real", "hidden": True}, real))
    # non-adopted or one-off figures (proposed totals, news quotes, other scopes) go in a table, never a chart
    for s in unit_series:
        is_primary = s["basis"] in BASIS_ORDER and "adopted" in s["kinds"] and set(s["status"]) <= {"official", "computed"}
        if not is_primary and not _series_charted(s, unit_series):
            others.extend((s, r) for r in s["rows"])
    return charts, others


def _dollars_toggle(mo: Money, page):
    """The nominal / constant-dollar switch for the budget charts (hidden until money.js shows it)."""
    if not mo.cpi:
        return None
    c = page.cites
    return h("div", None,
             h("fieldset", {"class": "mn-dollars-toggle", "id": "mn-dollars-toggle", "hidden": True},
               h("legend", None, "Dollars shown in the budget charts"),
               h("label", {"for": "mn-dollars-nominal"},
                 h("input", {"type": "radio", "name": "mn-dollars", "id": "mn-dollars-nominal", "value": "nominal",
                             "checked": True}), "Nominal (as reported)"),
               h("label", {"for": "mn-dollars-real"},
                 h("input", {"type": "radio", "name": "mn-dollars", "id": "mn-dollars-real", "value": "real"}),
                 f"Constant {mo.cpi_base} dollars")),
             h("p", {"class": "muted"},
               f"Constant {mo.cpi_base} dollars multiply each year's amount by the {mo.cpi_base} annual average of the "
               "Consumer Price Index for All Urban Consumers (U.S. city average) divided by that year's average. ",
               c.cite(mo.cpi_src), " ", status_badge("computed", page, "Constant-dollar amounts are the guide's arithmetic."),
               f" It is a national index, not a local one. {mo.cpi_base + 1} budgets are not adjusted because that year's "
               "annual average isn't published yet. The switch changes the budget-over-time charts only; tax rates and "
               "the single-year charts further down are never adjusted. It needs JavaScript; without it every chart is "
               "nominal."))


def _source_label(s) -> str:
    """Plain name of where a budget series comes from: the state's Gateway budget file (MON-001), a council
    budget ordinance, or (otherwise) the unit's own official document."""
    firsts = {split_ids(r["source_ids"])[0] for r in s["rows"] if split_ids(r.get("source_ids"))}
    if firsts == {"MON-001"}:
        return "Gateway state budget file"
    if "ordinance" in s["id"]:
        return "council budget ordinance"
    return "the unit's own budget document"


def _year_span(s) -> str:
    ys = sorted({int(r["year"]) for r in s["rows"]})
    if not ys:
        return ""
    return f"{ys[0]}" if ys[0] == ys[-1] else f"{ys[0]}-{ys[-1]}"


def _series_charted(s, unit_series) -> bool:
    """True when a secondary series was drawn as a continuation on a chart (see _unit_charts)."""
    group = [x for x in unit_series if x["basis"] == s["basis"]]
    primary = [x for x in group if "adopted" in x["kinds"] and set(x["status"]) <= {"official", "computed"}]
    if not primary:
        return False
    prim_years = {int(r["year"]) for x in primary for r in x["rows"]}
    sy = {int(r["year"]) for r in s["rows"]}
    return len(sy) > 1 and not (sy & prim_years) and s["kinds"] == ["adopted"] and any(x["breaks"] for x in primary)


def rank_rows(fid: str, title: str, rows: list[dict], subtitle=None, note=None, status=None, page=None, cite=None,
              headers=None, word: str = "Amount", vmax: float | None = None) -> Markup:
    """A ranked list of governments drawn as full-width HTML bars (phase 6 step 5, 2026-11-18), in the office money
    charts' row markup (charts.money_rows classes, so it takes their styles in every look): one accent bar per row on
    one scale, the value printed after the bar, the row's name a link. rows: [{name, sub, value, text, tip}] in the
    caller's order (callers rank governments, never people). Table view: name, value."""
    vals = [r["value"] for r in rows if r.get("value") is not None]
    top_v = vmax or max(vals, default=1) or 1
    ticks = nice_ticks(top_v, 4)
    top = ticks[-1] or 1
    items = []
    for r in rows:
        v = r.get("value")
        kids = [h("span", {"class": "visually-hidden"}, f"{word}: ")]
        if v is not None and v > 0:
            kids.append(h("span", {"class": "mrw-bar m-accent", "style": f"width:{max(0.4, min(100.0, 100.0 * v / top)):.2f}%",
                               "aria-hidden": "true"}))
            kids.append(h("span", {"class": "mrw-v"}, r["text"]))
        else:
            kids.append(h("span", {"class": "mrw-v mrw-none"}, r["text"]))
        items.append(h("li", {"class": "mrw-row rk-row", "title": r.get("tip") or None},
                       h("span", {"class": "mrw-who"}, h("span", {"class": "mrw-name"}, r["name"]),
                         h("span", {"class": "mrw-sub"}, r.get("sub")) if r.get("sub") else None),
                       h("span", {"class": "mrw-bars"}, h("span", {"class": "mrw-line"}, kids))))
    axis = h("div", {"class": "mrw-axis", "aria-hidden": "true"}, h("span", {"class": "mrw-axis-spacer"}),
             h("span", {"class": "mrw-axis-scale"}, h("span", None, "0"), h("span", None, r_fmt_top(rows, top))))
    body = h("div", {"class": "mrw rk"}, h("ul", {"class": "mrw-list", "aria-label": f"{title}: ranked, bars on one scale"},
                                          items), axis)
    trows = [[r.get("plain") or r.get("label") or "", r["text"]] for r in rows]
    return figure(fid, title, subtitle, body, headers or ["Government", word], trows, note=note, numeric=(1,),
                  status=status, page=page, kind="money-rows", scroll=False, cite=cite)


RANK_TOP = 10    # rows a ranked list shows before "Show all N"


def ranked(fid: str, title: str, rows: list[dict], top: int = RANK_TOP, **kw) -> list:
    """rank_rows for the first ``top`` rows, then the rest in a "Show all N" fold on the same scale (one ranking)."""
    vmax = max((r["value"] for r in rows if r.get("value") is not None), default=None)
    if len(rows) <= top + 2:
        return [rank_rows(fid, title, rows, vmax=vmax, **kw)]
    rest_kw = {k: v for k, v in kw.items() if k in ("page", "headers", "word")}
    return [rank_rows(fid, title + f" (top {top} of {len(rows)})", rows[:top], vmax=vmax, **kw),
            see_all_fold(f"{fid}-rest", len(rows) - top,
                         rank_rows(f"{fid}-more", title + f": the other {len(rows) - top}", rows[top:], vmax=vmax,
                                   **rest_kw),
                         hint=None, label=f"Show the other {len(rows) - top}")]


def r_fmt_top(rows, top) -> str:
    fmt = rows[0].get("fmt") if rows else None
    return fmt(top) if fmt else f"{top:,.0f}"


def _gov_row(mo: Money, page, mid: str, value: float, text: str, frag: str, sub: str = "", tip: str = "") -> dict:
    """One ranked row: the government's name linked to its Money tab (#frag)."""
    label = re.sub(r" \(state data: .*\)$", "", mo.label(mid))
    gov = gm.gov_for_money_id(mo.ed, mid)
    u = gm.href(page, gov.gid, "money", frag) if gov else None
    return {"name": h("a", {"href": u}, label) if u else label, "plain": label, "value": value, "text": text,
            "sub": sub or None, "tip": tip or None}


def per_resident_rows(mo: Money, ids, basis: str, year: int) -> tuple[list, str]:
    """[(mid, row, population row, per-resident value)] for an adopted basis and year (the comparison the budgets page
    has drawn since Wave A: the adopted amount divided by the ACS 2020-2024 population estimate), and the sources."""
    out, srcs = [], []
    for mid in ids:
        s = next((s for s in mo.series.values() if s["unit"] == mid and s["basis"] == basis
                  and s["status"] in (["official"], ["computed"]) and s["kinds"] == ["adopted"]), None)
        pop = mo.population(mid)
        if not s or not pop:
            continue
        r = next((r for r in s["rows"] if int(r["year"]) == year), None)
        # a blank amount or a blank / zero population has no per-resident figure
        if not r or not (r["amount"] or "").strip() or not ((pop.get("value") or "").strip() and float(pop["value"]) > 0):
            continue
        out.append((mid, r, pop, float(r["amount"]) / float(pop["value"])))
        srcs += [r, pop]
    return out, union_sources(srcs)


def _pop_tip(r, pop) -> str:
    return (f"{usd(r['amount'])} / {int(float(pop['value'])):,} residents"
            + (f" (MOE ±{int(float(pop['moe'])):,})" if pop.get("moe") else ""))


def build_budgets(site):
    """Compare budgets (phase 6 step 5, 2026-11-18; replaces the 182-fold "Budgets by unit"). Each government's own
    budget history, breakdowns, debt and money in and out are on its government page's Money tab
    (pages/gov_parts.py); this page compares governments: the money map, budget per resident, the certified tax rate,
    debt and the tax base, each a ranked list whose rows link to that government's Money tab, then every government
    with its latest adopted budget. Old ids forward through #moved-anchors (budgets_moved)."""
    from civic.answers import latest_unit_rate
    ed = site.ed
    mo = money(ed)
    page = site.page("money/budgets/index.html", title="Compare budgets", banners=False, body_class="thing-page")
    c = page.cites
    n_units = len({r["unit_id"] for r in mo.budgets})
    govs = gm.governments(ed)
    page.add(h("header", {"class": "thing-head cb-head"},
               page.crumb_nav(),
               h("h1", {"class": "thing-title"}, "Compare budgets"),
               h("p", {"class": "thing-facts"},
                 join([h("span", {"class": "thing-fact"}, f) for f in (
                     f"{n_units} local units with budget figures, {mo.y0} to {mo.y1}",
                     "each government's full history is on its Money tab")],
                      h("span", {"class": "facts-sep", "aria-hidden": "true"}, " · "))),
               h("p", {"class": "cf-quick"},
                 h("a", {"href": page.rel("money/what-is-a-budget/index.html")}, "What counts as a budget?"), " · ",
                 h("a", {"href": page.rel("money/your-tax-bill/index.html")}, "Your tax bill"), " · ",
                 h("a", {"href": page.rel(gm.HUB)}, "Every government"))))
    page.add(h("p", {"class": "cb-lead"}, "Governments differ in size and in what their budgets count, so this page "
                                          "compares them per resident and on one basis at a time. A list never mixes "
                                          "two ways of totaling a budget. Select a government for its own charts.",
               c.cite("MON-001"), " ", status_badge("computed", page, "Per-resident figures divide by Census estimates.")))

    # ---- 1 money map (counted spending per resident), every area linking to its government's Money tab
    page.add(_money_map_compare(mo, page))

    # ---- 2 budget per resident
    gf_ids = ["county-st-joseph", "city-south-bend", "city-mishawaka"]
    tw_ids = ["county-st-joseph", "city-mishawaka"] + [m for m in mo.unit_ids if group_of(m) == "township"]
    pr_year = comparison_year(mo, gf_ids + tw_ids, ("general_fund", "advertised_all_funds"))
    pop_note = ("Computed: the adopted amount divided by the Census Bureau's American Community Survey 2020-2024 5-year "
                "population estimate. The estimate is a five-year average, so per-resident figures are approximate.")
    fmt = lambda v: f"${v:,.0f}"
    charts = []
    for fid, basis, ids, title, sub, extra in (
            ("perres-af", "advertised_all_funds", tw_ids, f"All advertised funds per resident, {pr_year}",
             "County, Mishawaka (civil city) and the townships",
             " Township populations include residents of cities and towns inside the township. South Bend is left "
             "out: from 2024 the state file lists only 10 of its funds."),
            ("perres-gf", "general_fund", gf_ids, f"General fund per resident, {pr_year}", "County and the two cities",
             " The county's figure is divided by the whole county's population, which includes city residents.")):
        got, src = per_resident_rows(mo, ids, basis, pr_year)
        got.sort(key=lambda t: -t[3])
        rows = [dict(_gov_row(mo, page, mid, v, fmt(v), "budget", tip=_pop_tip(r, pop)), fmt=fmt)
                for mid, r, pop, v in got]
        if rows:
            charts.append(h("div", {"class": "cb-cell"},
                            ranked(fid, title, rows, subtitle=sub, note=pop_note + extra, status="computed",
                                   page=page, cite=c.cite(src), headers=["Government", "Per resident"],
                                   word="Per resident")))
    pr_at = len(page.parts)     # the per-resident section goes here once the tax base per resident is known

    # ---- 3 certified tax rate and 4 debt, side by side on a wide screen
    pair = []
    rates = []
    for g in govs:
        r = latest_unit_rate(ed, g.unit_id) if g.unit_id else None
        if r:
            rates.append((g, r))
    if rates:
        ry = max(r["year"] for _g, r in rates)
        rates = sorted([(g, r) for g, r in rates if r["year"] == ry], key=lambda t: -float(t[1]["rate_per_100"]))
        rfmt = lambda v: f"${v:.4f}"
        rows = []
        for g, r in rates:
            u = gm.href(page, g.gid, "money", "tax-base")
            v = float(r["rate_per_100"])
            rows.append({"name": h("a", {"href": u}, g.name) if u else g.name, "plain": g.name, "value": v,
                         "text": rfmt(v), "fmt": lambda t: f"${t:.2f}"})
        pair.append(T.tab_section("rates", f"Certified property-tax rate, taxes payable in {ry}",
                               *ranked("rates-certified", f"Each government's own certified rate per $100 of assessed "
                                                            f"value, {ry}", rows,
                                         subtitle="One government's own rate; a tax bill adds the rates of every "
                                                  "government that taxes the property.",
                                         status="official" if all(r["status"] == "official" for _g, r in rates)
                                         else "computed", page=page,
                                         cite=c.cite(union_sources(r for _g, r in rates)),
                                         headers=["Government", "Rate per $100"], word="Rate per $100"),
                               h("p", {"class": "tnote"}, "How one bill is split among these governments: ",
                                 h("a", {"href": page.rel("money/your-tax-bill/index.html")}, "Your tax bill"), ".")))

    # ---- 4 debt (2026-11-18: the state files 2022-2025; the ranking keeps its id debt-2024 and shows the latest year)
    dyears = debt_years(mo)
    dy = dyears[-1] if dyears else None
    tot = [r for r in mo.debt if r["debt_type"].startswith(DEBT_TOTAL) and (r.get("amount") or "").strip()
           and r["year"] == dy]
    tot.sort(key=lambda r: -float(r["amount"]))
    drows = [dict(_gov_row(mo, page, r["unit_id"], float(r["amount"]), usd_short(r["amount"]), "debt",
                           tip=f"{mo.label(r['unit_id'])}: {usd(r['amount'])} at the end of {r['year']}"),
                  fmt=usd_short) for r in tot]
    cls_rows = []
    for r in sorted(mo.debt, key=lambda r: (mo.unit_ids.index(r["unit_id"]), r["year"], r["debt_type"])):
        cls_rows.append([mo.label(r["unit_id"]), r["year"], r["debt_type"], usd(r["amount"]),
                         h("span", None, status_badge(r["status"], page), c.cite(r["source_ids"])),
                         strip_whole_corp(r["notes"])])
    all_tot = [r for r in mo.debt if r["debt_type"].startswith(DEBT_TOTAL) and (r.get("amount") or "").strip()]
    by_year = debt_by_year_table(mo, page, set(mo.unit_ids))
    if dy:
        pair.append(T.tab_section(
            "debt", f"Debt outstanding, end of {dy}",
            *ranked("debt-2024", f"Total principal still owed at the end of {dy}, all debt classes", drows,
                      subtitle=f"{len(tot)} units report debt in the state's {dy} file. Totals include utility debt where "
                               "a unit has utilities. Each unit separately; never add two units' totals.",
                      note="Computed: the sum of each unit's debt-class rows in the state's annual financial report debt "
                           "file.", status="computed", page=page, cite=c.cite(union_sources(tot)),
                      headers=["Government", "Principal"], word="Principal"),
            see_all_fold("debt-by-year-all", 0, by_year,
                         label=f"Show debt by year, {dyears[0]} to {dyears[-1]}, for every unit", hint=None)
            if by_year is not None and len(dyears) > 1 else None,
            debt_notes_block(mo, page, all_tot if by_year is not None and len(dyears) > 1 else tot),
            whole_corporation_note(mo, page, {r["unit_id"] for r in all_tot}),
            see_all_fold("debt-classes-all", len(cls_rows),
                         data_table("debt-classes", ["Unit", "Year", "Debt type", "Amount", "Status", "Note"], cls_rows,
                                    caption="Debt by class and unit", numeric=(3,), min_width="54rem"),
                         label=f"Show the table: every debt row by class and unit ({len(cls_rows)})")))
    page.add(h("div", {"class": "cb-two cb-two-sec"}, pair))

    # ---- 5 tax base per resident, then the whole tax-base section (a learning-path stop, #tax-base) in a fold
    av_ids = gf_ids + [m for m in mo.unit_ids if group_of(m) == "township"]
    av_got = []
    for mid in av_ids:
        r, pop = tb.latest_certified(ed, mid), mo.population(mid)
        if not r or not pop or tb.part_only(r):
            continue
        v = tb.av_per_resident(tb.av_value(r), pop["value"])
        if v is not None:
            av_got.append((mid, r, pop, v))
    av_parts = []    # the tax base per resident, drawn beside the general fund per resident
    if av_got:
        av_year = max(r["year"] for _m, r, _p, _v in av_got)
        av_got = sorted([t for t in av_got if t[1]["year"] == av_year], key=lambda t: -t[3])
        rows = [dict(_gov_row(mo, page, mid, v, fmt(v), "tax-base",
                              tip=f"{usd(tb.av_value(r))} / {int(float(pop['value'])):,} residents"), fmt=fmt)
                for mid, r, pop, v in av_got]
        av_parts.extend(ranked(
            "perres-av", f"Certified assessed value per resident, {av_year}", rows,
            subtitle="County, the two cities and the townships",
            note=("Computed: the state-certified net assessed value (the tax base property taxes are levied on) divided "
                  "by the 2020-2024 population estimate. The county's value covers everyone in the county, city "
                  "residents included. A township's value includes the cities and towns inside it, as its population "
                  "does."), status="computed", page=page,
            cite=c.cite(union_sources(x for _m, r, pop, _v in av_got for x in (r, pop))),
            headers=["Government", "Per resident"], word="Per resident"))
    if len(charts) > 1:
        charts[-1] = h("div", {"class": "cb-cell"}, charts[-1], av_parts)
    else:
        charts.append(h("div", {"class": "cb-cell"}, av_parts))
    page.parts.insert(pr_at, T.tab_section(
        "per-resident", f"Per resident, {pr_year}", h("div", {"class": "cb-two"}, charts),
        lead=f"Each government's {pr_year} adopted budget, and its tax base, divided by its population; one basis per "
             "list."))
    av_parts = []
    av_parts.append(see_all_fold("tax-base-all", 0, _tax_base(mo, page), hint=None,
                                 label="Show how the tax base shapes budgets: rates over time, assessed value, "
                                       "property-tax receipts"))
    page.add(T.tab_section("tax-base-sec", "How the tax base shapes budgets", av_parts))

    # ---- 6 every government (id over-time: the learning path's "Budgets over time" stop lands here)
    nodata_gaps = []
    for mid in mo.unit_ids:
        if not (mo.has_budget(mid) or mo.in_units_csv(mid)):
            continue
        if not mo.has_budget(mid):
            nodata_gaps.append({"item": f"{mo.label(mid)}: budget figures",
                                "why_missing": "The guide's budget file has no adopted budget rows for this unit "
                                               "(the state budget download used for the guide has none for it).",
                                "how_to_fill": "Check the unit's Gateway budget pages, or its own budget documents."})
    blocks = []
    # every government with a page (civic/governments.py: units.csv governments, and every library and special unit
    # with money figures), so a unit with only money in and out (no budget) is listed too
    by_group: OrderedDict = OrderedDict((k, []) for k in gm.GROUPS)
    for g in govs:
        by_group[g.group].append(g)
    for key, label in gm.GROUPS.items():
        items = []
        for g in by_group[key]:
            bud = [m for m in g.money_ids if mo.has_budget(m)]
            u = (gm.href(page, g.gid, "money", "budget" if bud else "") or gm.href(page, g.gid))
            if bud:
                digest = _unit_digest(mo, bud[0])
            elif any(has_money_in_out(ed, m) for m in g.money_ids):
                m = next(m for m in g.money_ids if has_money_in_out(ed, m))
                digest = "No adopted budget series in the guide's data; " + _flows_digest(ed, m)[:1].lower() +                          _flows_digest(ed, m)[1:]
            else:
                digest = "No adopted budget series in the guide's data"
            items.append(h("li", {"class": "cb-srow"}, h("a", {"href": u}, g.name) if u else g.name,
                           h("span", {"class": "cb-srow-sub"}, digest)))
        if items:
            blocks.append(h("div", {"class": "cb-level"}, h("h3", {"class": "cb-level-h"}, label),
                            h("ul", {"class": "cb-slist cb-slist-grid"}, items)))
    n_govs = sum(len(v) for v in by_group.values())
    page.add(T.tab_section("over-time", "Every government's budget over time",
                           see_all_fold("over-time-all", n_govs, blocks, noun="government", hint=None,
                                        label=f"Show all {n_govs} governments and their latest adopted totals"),
                           lead="Each government's Money tab has its adopted budget for every year the state file has "
                                "it, one chart per way of totaling, with changes in reporting drawn on the chart; then its "
                                "tax base, debt, money in and out, and breakdowns. The line under each name is its latest "
                                "adopted total."))
    page.add(_budgets_moved_script(mo, page))
    page.finish(gaps=nodata_gaps + money_gaps(ed) + cpi_gaps(mo),
                gaps_intro=("What the guide looked for and hasn't found or confirmed yet. Each government's flagged "
                            "budget changes are listed on its Sources tab."))
    return page


def _money_map_compare(mo: Money, page) -> Markup | None:
    """The money map (civic/money_map.py): every city, town, township and school corporation shaded by counted spending
    per resident; every area links to its government's Money tab. The county as one figure, then every figure as
    tables (folded)."""
    ed = mo.ed
    shapes = load_shapes(ed)
    if shapes is None or not ed.table("spending_breakdowns"):
        return None
    mm = money_map_data(ed, shapes)
    label = lambda m: re.sub(r" \(state data: .*\)$", "", mo.label(m))
    return T.tab_section(
        "money-map", "Spending per resident: the money map",
        h("p", {"class": "tsec-lead"}, "Each area is shaded by how much its government spent per resident in its latest "
                                       "year in the state's annual financial reports. Point at an area (or tap it, or "
                                       "move to it with Tab) to see where its money came from and how it was spent; "
                                       "select it again, or press Enter, to open its government's Money tab. Pick "
                                       "cities and towns, townships or school corporations with the buttons above the "
                                       "map."),
        county_figure(page, ed, mm),
        money_map(page, ed, shapes, mm),
        method_note(page, ed),
        see_all_fold("money-map-tables", 0, money_map_tables(page, ed, mm, label), hint="Copy CSV",
                     label="Show the table: every figure on the map"))


def budgets_moved(mo: Money, page) -> dict:
    """Where the old budgets page's ids are now (static/js/moved.js): each unit's block, charts, other figures,
    breakdowns and money in and out moved to its government's Money tab, which keeps the chart and table ids."""
    ed = mo.ed
    a, p = {}, {}
    for mid in mo.unit_ids:
        gov = gm.gov_for_money_id(ed, mid)
        anchor = mo.anchor(mid)
        if gov is None or gm.path(gov.gid, "money") not in page.site.by_path:
            # no Money tab (no figure at all): the unit's line in this page's list says so
            a[anchor] = a[mid] = "#over-time"
            continue
        tab = page.rel(gm.path(gov.gid, "money"))
        a[anchor] = a[mid] = f"{tab}#budget" if mo.has_budget(mid) else f"{tab}#tabs"
        if any(r["unit_id"] == mid and r["basis"].startswith("afr_2024") for r in mo.breakdowns):
            a[f"breakdown-{anchor}"] = f"{tab}#breakdowns"
        if has_money_in_out(ed, mid):
            a[f"flows-{anchor}"] = f"{tab}#money-in-out"
        for pre in (f"bud-{mid}-", f"other-{mid}", f"brk-{mid}-", f"obrk-{mid}-", f"sp-{anchor}-", f"sp-{mid}-",
                    f"money-{anchor}", f"av-2026-{mid}"):
            p[pre] = tab
    for old, new in (("mn-dollars-toggle", "over-time"), ("mn-dollars-nominal", "over-time"),
                     ("mn-dollars-real", "over-time"), ("breakdowns", "over-time"), ("breakdowns-h", "over-time"),
                     ("money-in-out", "over-time"), ("money-in-out-h", "over-time"), ("over-time-h", "over-time"),
                     ("money-map-others", "money-map-tables"), ("cmap-mhatch", "money-map"),
                     ("debt-h", "debt"), ("per-resident-h", "per-resident"), ("money-map-h", "money-map")):
        a[old] = f"#{new}"
    # the old page's per-group budget figures for the cities, townships and schools on the assessed-value charts
    p["av-2026-"] = "#tax-base"
    p["mm-table-"] = "#money-map-tables"
    p["src-"] = page.rel("about/sources/index.html")
    return {"a": a, "p": p}


def _budgets_moved_script(mo: Money, page) -> Markup:
    import json
    data = budgets_moved(mo, page)
    return Markup('<script type="application/json" id="moved-anchors">'
                  + json.dumps(data, sort_keys=True).replace("</", "<\\/") + "</script>")


def other_breakdown_parts(mo: Money, page, mid: str) -> list:
    """One unit's other breakdowns (phase 6 step 5): proposed figures, a later budget year and news-reported
    department amounts (the budgets page's "Other breakdowns in the guide's data"), as tables with the same ids
    (obrk-<mid>-<basis>), for the unit's government Money tab. Each has its own scope, so none is charted."""
    c = page.cites
    groups = OrderedDict()
    for r in mo.breakdowns:
        if r["unit_id"] == mid and not r["basis"].startswith("afr_2024"):
            groups.setdefault((r["year"], r["basis"]), []).append(r)
    out = []
    for (year, basis), rows in groups.items():
        total = sum(float(r["amount"]) for r in rows)
        trows = [[r["category"], usd(r["amount"]), h("span", None, status_badge(r["status"], page), c.cite(r["source_ids"]))]
                 for r in rows]
        out.append(h("div", {"class": "mn-other-breakdown"},
                     h("p", {"class": "mn-others-h"}, h("strong", None, f"{year}: {rows[0]['kind']}. "), rows[0]["notes"]),
                     data_table(f"obrk-{mid}-{basis.replace('_', '-')}", ["Category", "Amount", "Status"], trows,
                                caption=f"{mo.label(mid)} {year}: {basis.replace('_', ' ')} (rows total {usd(total)})",
                                numeric=(1,), min_width="30rem")))
    return out


def comparison_year(mo: Money, ids, bases) -> int:
    """The latest budget year that the most of these units have an adopted figure for (on any of the bases), so one
    unit's early figures (South Bend adopts next year's budget before the state file lists it) don't empty the
    comparison."""
    have = {}
    for s in mo.series.values():
        if s["unit"] in ids and s["basis"] in bases and s["kinds"] == ["adopted"]:
            for r in s["rows"]:
                if r["amount"]:
                    have.setdefault(int(r["year"]), set()).add(s["unit"])
    if not have:
        return mo.y1
    return max(have, key=lambda y: (len(have[y]), y))


def av_per_resident_rows(mo: Money, ids) -> tuple[list, str, str | None]:
    """hbar rows of certified net assessed value divided by Money.population (ACS 2020-2024), for the latest
    certified year. Units whose value covers only the county's part of the unit are left out."""
    picked = []
    for mid in ids:
        r, pop = tb.latest_certified(mo.ed, mid), mo.population(mid)
        if not r or not pop or tb.part_only(r):
            continue
        v = tb.av_per_resident(tb.av_value(r), pop["value"])
        if v is not None:
            picked.append((mid, r, pop, v))
    if not picked:
        return [], "", None
    year = max(r["year"] for _, r, _, _ in picked)
    picked = [t for t in picked if t[1]["year"] == year]
    rows = [{"label": re.sub(r" \(state data: .*\)$", "", mo.label(mid)), "value": v, "display": f"${v:,.0f}",
             "tip": f"{usd(tb.av_value(r))} / {int(float(pop['value'])):,} residents"
                    + (f" (MOE ±{int(float(pop['moe'])):,})" if pop.get("moe") else "")}
            for mid, r, pop, v in picked]
    return rows, union_sources(x for _, r, pop, _ in picked for x in (r, pop)), year


DEBT_TOTAL = "Total end-of-year principal"
DEBT_DUE = "Principal due within one year"
DEBT_CLASS = "End-of-year principal outstanding: "
# sentences in debt.csv notes that every total or due row repeats (how the guide built the row): not shown as notes
_DEBT_GENERIC = re.compile(r"^(Sum of the class rows for this unit\.|Sum of principal amounts due within 1 year[^.]*\.|"
                           r"Gateway Annual Financial Report \d{4}, sum of debt entries in this class\.|"
                           r"Entity in parentheses as filed\.)$")
# budgets.csv / debt.csv notes of a cross-county school corporation open with this phrase (tools/check_money.py
# requires it); a page shows it once (whole_corporation_note), never on every row (2026-11-18)
WHOLE_CORP = re.compile(r"Whole corporation \(([^()]*(?:\([^()]*\))?[^()]*)\)\.?\s*")


def strip_whole_corp(text: str) -> str:
    return WHOLE_CORP.sub("", text or "").strip()


def debt_totals(mo: Money, mid: str) -> dict[str, dict]:
    """{year: total row} of one unit's end-of-year principal (state annual-report debt file), rows with an amount."""
    return {r["year"]: r for r in mo.debt
            if r["unit_id"] == mid and r["debt_type"].startswith(DEBT_TOTAL) and (r.get("amount") or "").strip()}


def debt_years(mo: Money) -> list[str]:
    return sorted({r["year"] for r in mo.debt if r["debt_type"].startswith(DEBT_TOTAL) and (r.get("amount") or "").strip()})


def debt_note_text(note: str) -> str:
    """A debt row's stored note without the generic "how the row was built" sentences and the whole-corporation phrase
    (shown once per page): what is left is a reader's caveat (the never-sum note, the utility note, an unexplained
    line)."""
    keep = [s for s in sentences(strip_whole_corp(note)) if not _DEBT_GENERIC.match(s.strip())]
    return " ".join(keep).strip()


def debt_notes_block(mo: Money, page, rows: list[dict]) -> Markup | None:
    """The stored caveats of the debt rows a chart or table shows, each once, with the units and years it is stored
    on: "St. Joseph County (2024, 2025); St. Joseph Redevelopment Authority (2024, 2025): Same $50,000,000 ...; never
    add the two totals." Shown wherever those totals appear."""
    c = page.cites
    groups: dict[str, dict] = OrderedDict()
    for r in rows:
        # one entry per stored sentence, so a caveat repeated on several years is listed once with its years
        for t in sentences(debt_note_text(r.get("notes") or "")):
            g = groups.setdefault(t, {"units": OrderedDict(), "rows": []})
            g["units"].setdefault(r["unit_id"], []).append(r["year"])
            g["rows"].append(r)
    if not groups:
        return None
    items = []
    for text, g in groups.items():
        who = "; ".join(f"{re.sub(r' [(]state data: .*[)]$', '', mo.label(m))} ({', '.join(sorted(set(ys)))})"
                        for m, ys in g["units"].items())
        items.append(h("li", None, h("strong", None, who + ": "), text, c.cite(union_sources(g["rows"]))))
    return h("div", {"class": "mn-debt-notes"}, h("p", {"class": "mn-debt-notes-h"}, "Notes stored with these totals:"),
             h("ul", None, items))


def whole_corporation_note(mo: Money, page, mids) -> Markup | None:
    """Once per page: the cross-county school corporations whose budget and debt figures cover the whole corporation,
    with the stored phrase ("Whole corporation (principal county: LaPorte, Gateway county 46)"). None when no unit of
    `mids` carries the phrase."""
    found: dict[str, str] = OrderedDict()
    srcs = []
    for r in list(mo.budgets) + list(mo.debt):
        if r["unit_id"] in mids and r["unit_id"] not in found:
            m = WHOLE_CORP.search(r.get("notes") or "")
            if m:
                found[r["unit_id"]] = m.group(0).strip().rstrip(".")
                srcs.append(r)
    if not found:
        return None
    bits = [h("li", None, h("strong", None, re.sub(r" [(]state data: .*[)]$", "", mo.label(m)) + ": "), phrase + ".")
            for m, phrase in found.items()]
    return h("div", {"class": "fscope-line mn-whole-corp", "id": "whole-corporation"},
             h("p", None, h("strong", None, "Whole corporation. "),
               ("These school corporations also cover land outside St. Joseph County. Their budget and debt figures "
                "here are" if len(found) > 1 else "This school corporation also covers land outside St. Joseph County. "
                "Its budget and debt figures here are")
               + " for the whole corporation, as filed with the state, not a St. Joseph County share.",
               page.cites.cite(union_sources(srcs))),
             h("ul", None, bits))


def debt_by_year_rows(mo: Money, mids) -> tuple[list[str], list[tuple[str, dict]]]:
    """(years, [(mid, {year: total row})]) for the units with at least one total, in mo.unit_ids order."""
    years = debt_years(mo)
    out = []
    for mid in mo.unit_ids:
        if mid in mids:
            t = debt_totals(mo, mid)
            if t:
                out.append((mid, t))
    return years, out


def debt_by_year_table(mo: Money, page, mids, tid: str = "debt-by-year") -> Markup | None:
    """Every unit's total principal at the end of each year in the state file (2022-2025), one row per unit, one
    column per year; a blank cell says the unit filed no debt in that year's file. Never a sum across units."""
    c = page.cites
    years, got = debt_by_year_rows(mo, mids)
    if not got:
        return None
    rows = []
    for mid, t in got:
        gov = gm.gov_for_money_id(mo.ed, mid)
        u = gm.href(page, gov.gid, "money", "debt") if gov else None
        label = re.sub(r" \(state data: .*\)$", "", mo.label(mid))
        rows.append([h("a", {"href": u}, label) if u else label]
                    + [usd(t[y]["amount"]) if y in t else h("span", {"class": "muted"}, "none filed") for y in years]
                    + [h("span", None, c.cite(union_sources(t.values())))])
    return data_table(tid, ["Government"] + [f"End of {y}" for y in years] + ["Sources"], rows,
                      caption="Total principal still owed at the end of each year, as each unit reported it to the state",
                      numeric=tuple(range(1, len(years) + 1)), min_width="44rem")


def unit_debt_years_chart(mo: Money, page, mid: str) -> Markup | None:
    """Columns: one unit's total principal at the end of each year in the state file (accent marks, never party
    colors), with the principal due within one year in each tooltip. None with fewer than two years."""
    tots = debt_totals(mo, mid)
    years = debt_years(mo)
    if len(tots) < 2:
        return None
    due = {r["year"]: r for r in mo.debt if r["unit_id"] == mid and r["debt_type"].startswith(DEBT_DUE)
           and (r.get("amount") or "").strip()}
    pts = []
    for y in years:
        r = tots.get(y)
        if r is None:
            pts.append({"x": y, "value": None})
            continue
        d = due.get(y)
        pts.append({"x": y, "value": float(r["amount"]), "display": usd_short(r["amount"]), "status": r["status"],
                    "tip": f"End of {y}: {usd(r['amount'])}" + (f"; {usd(d['amount'])} due within one year" if d else "")})
    st = "official" if all(r["status"] == "official" for r in tots.values()) else "computed"
    return columns(f"debt-years-{mo.anchor(mid)}", f"{re.sub(r' [(]state data: .*[)]$', '', mo.label(mid))}: debt "
                   f"outstanding at the end of each year", pts, subtitle=f"Total principal, {years[0]} to {years[-1]}, as "
                   "reported to the state. Nominal dollars.", money=True, value_fmt=usd_short, status=st, page=page,
                   headers=["Year", "Principal"], cite=page.cites.cite(union_sources(tots.values())))


_DEBT_AS_OF = re.compile(r"^Total debt outstanding as of (\d{4}-\d{2}-\d{2})\s*(?:\((.*)\))?\s*$")


def later_debt_rows(mo: Money, mid: str) -> list[tuple[str, str, dict]]:
    """The unit's own later debt totals: rows whose debt_type reads "Total debt outstanding as of <date> (<source>)",
    as [(ISO date, source words, row)], oldest date first."""
    found = []
    for r in mo.debt:
        m = _DEBT_AS_OF.match(r["debt_type"]) if r["unit_id"] == mid else None
        if m and r["amount"]:
            found.append((m.group(1), (m.group(2) or "").strip(), r))
    return sorted(found, key=lambda t: t[0])


def later_debt_note(mo: Money, page, mid: str) -> Markup | None:
    """One paragraph with every later_debt_rows figure. They are different dates and sources from the state file
    (and from each other), so they are never charted or added together."""
    c = page.cites
    found = later_debt_rows(mo, mid)
    if not found:
        return None
    parts = []
    for i, (d, where, r) in enumerate(found):
        rounded = "rounded" in (r.get("notes") or "").lower()
        parts += ["; " if i else "", ("roughly " if rounded else "") + usd_short(r["amount"]),
                  f" as of {fmt_date(d, long=True)}", f" ({where})" if where else "",
                  c.cite(r["source_ids"]), " ", status_badge(r["status"], page)]
    name = re.sub(r" \(.*\)$", "", mo.label(mid))
    if len(found) > 1:
        lead = f"{name}'s own reports give later figures: "
        tail = (". They are different dates and sources from the state file and from each other, so they are not on "
                "the chart and are not added together.")
    else:
        lead = f"{name}'s own report gives a later figure: "
        tail = ". It is a different date and source, so it is not on the chart."
    return h("p", None, lead, *parts, tail)


def _money_map_section(mo: Money, page) -> Markup | None:
    """Section 1: every city, town, township and school corporation shaded by counted spending per resident
    (civic/money_map.py), the county as one figure, and tables with every figure (the no-JavaScript view)."""
    ed = mo.ed
    shapes = load_shapes(ed)
    if shapes is None or not ed.table("spending_breakdowns"):
        return None
    mm = money_map_data(ed, shapes)
    label = lambda m: re.sub(r" \(state data: .*\)$", "", mo.label(m))
    # a click shows the unit's own budget block below (section 2, id = mo.anchor) instead of leaving the page
    blocks = {mo.anchor(m) for m in mo.unit_ids if mo.has_budget(m) or mo.in_units_csv(m)}

    def in_page(uid):
        return f"#{uid}" if uid in blocks else None
    return section("money-map", 1, "Money map: spending per resident",
                   h("p", None, "Each area is shaded by how much its government spent per resident in its latest year in "
                                "the state's annual financial reports. Point at an area (or tap it, or move to it with Tab) "
                                "to see where its money came from and how it was spent; select it again, or press Enter, "
                                "to show its budget history, breakdown and debt below, with the other units folded away. Pick cities and towns, townships or school corporations with "
                                "the buttons above the map."),
                   county_figure(page, ed, mm),
                   money_map(page, ed, shapes, mm, in_page=in_page),
                   _no_boundary_chips(mo, page),
                   method_note(page, ed),
                   h("details", {"class": "fold-details mn-map-tables", "open": True, "data-fold": "tables"},
                     h("summary", {"class": "fold-summary"},
                       h("h3", {"class": "one-h"}, "Every figure on the map, as tables"),
                       h("span", {"class": "fold-toggle", "aria-hidden": "true"})),
                     h("div", {"class": "fold-body"}, money_map_tables(page, ed, mm, label))),
                   scope="county", ed=ed)


def _flows_section(mo: Money, page) -> Markup:
    """Section 6: income and spending charts for the libraries and special units (they have no pages of their own).
    The county, cities, towns, townships and schools show the same block on their own pages."""
    ed = mo.ed
    c = page.cites
    ids = _flow_ids(mo)
    blocks = []
    for m in ids:
        name = re.sub(r" \(state data: .*\)$", "", mo.label(m))
        blocks.append(h("article", {"class": "mn-unit", "aria-label": mo.label(m), "id": f"flows-{mo.anchor(m)}",
                                    "data-one-for": mo.anchor(m)},
                        one_fold(mo.anchor(m), mo.label(m), one_summary("h3", name, _flows_digest(ed, m)),
                                 money_in_out(ed, page, m, level=4, label=name))))
    links = [x for x in (gm.href(page, "county", "money", "money-in-out"),) if x]
    links = [h("a", {"href": links[0]}, "the county")] if links else []
    if gm.HUB in page.site.by_path:
        for frag, lab in (("cities", "each city, town and township"), ("schools", "each school corporation")):
            links.append(h("a", {"href": page.rel(f"{gm.HUB}#{frag}")}, lab))
    return section("money-in-out", 7, "Money in and out: libraries and special units",
                   h("p", None, "Where each library and special unit's money came from and how it was spent, from the "
                                "annual financial reports they file with the state, with money that only passes through "
                                "their books or moves between their own funds shown separately. The same charts for ",
                     join(links, ", "), " are on their own pages.", c.cite("MON-060;MON-063")),
                   h("div", one_scope("Money in and out for {name} is not in this section, which covers the libraries "
                                      "and special units; it is on the unit's own page."),
                     one_empty(), h("div", {"class": "one-list"}, blocks)),
                   scope="county", ed=ed)


NO_BOUNDARY_GROUPS = ("library", "special")


def no_boundary_units(mo: Money) -> list[tuple[str, str]]:
    """[(money id, in-page target id)] for the county and every library and special unit with a block on the budgets
    page: their budget item (id = Money.anchor) when they have one, else their money-in-and-out item (flows-<anchor>).
    The map draws none of them (the county is the whole map), so they are chosen from chips instead."""
    blocks = [m for m in mo.unit_ids if mo.has_budget(m) or mo.in_units_csv(m)]
    out = [(m, mo.anchor(m)) for m in blocks if group_of(m) == "county"]
    out += [(m, mo.anchor(m)) for m in blocks if group_of(m) in NO_BOUNDARY_GROUPS]
    for m in _flow_ids(mo):
        if m not in blocks:
            out.append((m, f"flows-{mo.anchor(m)}"))
    return out


def _no_boundary_chips(mo: Money, page) -> Markup | None:
    chips = [(f"#{t}", re.sub(r" \(state data: .*\)$", "", mo.label(m)) + (" (the whole county)" if group_of(m) == "county" else ""))
             for m, t in no_boundary_units(mo)]
    return one_chips(f"No boundary on the map ({len(chips)}): pick one here", chips,
                     note="The county covers the whole map; the libraries and special units serve areas the map does not "
                          "draw. Picking one shows its budget history, debt and money in and out below, as a map click does.",
                     cls="mn-chips")


def _flow_ids(mo: Money) -> list[str]:
    """The libraries and special units in Money in and out (section 7), in its order."""
    ed = mo.ed
    ids = [m for m in mo.unit_ids if group_of(m) in NO_BOUNDARY_GROUPS and has_money_in_out(ed, m)]
    ids += sorted(m for m in {r["unit_id"] for r in ed.table("spending_breakdowns")}
                  if group_of(m) in NO_BOUNDARY_GROUPS and m not in ids)
    return ids


def _flows_target(mo: Money, page, mid: str) -> tuple[str, str] | None:
    """(href, text) of the unit's full money-in-and-out charts: its own page's block (county, places, schools) or
    its item in section 7 on this page (libraries, special units). None when the unit has no such charts."""
    ed = mo.ed
    if not has_money_in_out(ed, mid):
        return None
    # every unit with a government page (phase 6 step 3): its Money tab's money-in-and-out block (id money-<anchor>,
    # civic/spending.py money_in_out)
    gov = gm.gov_for_money_id(ed, mid)
    own = gm.href(page, gov.gid, "money", f"money-{ed.unit_alias(mid) or mid}") if gov else None
    if own and page.path != gm.path(gov.gid, "money"):
        return own, f"{gov.short} government page"
    if group_of(mid) in NO_BOUNDARY_GROUPS and mid in _flow_ids(mo):
        return f"#flows-{mo.anchor(mid)}", "Money in and out, below"
    return None


def _unit_flows_line(mo: Money, page, mid: str) -> Markup | None:
    """One line in a unit's budget item: its counted money in and out from the state's annual report, with a link to
    the full charts (the budget totals above and these report figures have different scopes)."""
    tgt = _flows_target(mo, page, mid)
    if not tgt:
        return None
    return h("p", {"class": "mn-flows-line"}, h("strong", None, "Money in and out: "),
             _flows_digest(mo.ed, mid)[:1].lower() + _flows_digest(mo.ed, mid)[1:],
             " (actual figures from the state's annual report, a different scope from the adopted budgets above). ",
             h("a", {"href": tgt[0]}, tgt[1] if tgt[0].startswith("#") else f"Full charts on the {tgt[1]}"), ".")


def _scope_note(rows) -> str:
    """Sentences every row's note shares (the file's scope statement)."""
    lists = [sentences(r["notes"]) for r in rows]
    if not lists:
        return ""
    common = [s for s in lists[0] if all(s in l for l in lists[1:])]
    return " ".join(common)


def _unit_digest(mo: Money, mid: str) -> str:
    """The line under a unit's collapsed name: its latest adopted total on the first basis it has, else why none."""
    for basis in BASIS_ORDER:
        rows = [r for s in mo.series.values() if s["unit"] == mid and s["basis"] == basis
                and "adopted" in s["kinds"] and set(s["status"]) <= {"official", "computed"}
                for r in s["rows"] if r["amount"] and r["adopted_or_actual"] == "adopted"]
        if rows:
            r = max(rows, key=lambda r: int(r["year"]))
            return f"Latest adopted: {usd_short(r['amount'])} in {r['year']} ({BASIS[basis][0].lower()})"
    return "No adopted budget series in the guide's data" if not mo.has_budget(mid) else "Other reported figures only"


def _flows_digest(ed, mid: str) -> str:
    from civic.money_map import summarize_rows
    from civic.spending import _kind, _rows
    s = summarize_rows(_rows(ed, mid), _kind(ed, mid))
    if not s:
        return "No counted money in or out in the guide's data"
    inc = f"; counted income {usd_short(s['income'])}" if s["income"] is not None else ""
    return f"Counted spending {usd_short(s['spending'])} in {s['spending_year_label']}{inc}"


def _breakdown_block(mo: Money, page, mid: str) -> Markup:
    name = mo.label(mid).replace(" (civil city)", "")
    out, shown = _breakdown_content(mo, page, mid)
    anchor = mo.anchor(mid)
    digest = ("2024 actual: " + "; ".join(shown)) if shown else "No 2024 breakdown rows"
    return h("div", {"class": "mn-breakdown", "id": f"breakdown-{anchor}", "data-one-for": anchor},
             one_fold(anchor, mo.label(mid), one_summary("h3", name, digest), out))


def breakdown_parts(mo: Money, page, mid: str) -> list:
    """One unit's 2024 spending and revenue breakdown charts and tables (the content of its item on the budgets
    page's section 4), for the unit's government page (phase 6 step 3). Same figures, same ids."""
    return _breakdown_content(mo, page, mid)[0]


def unit_debt_parts(mo: Money, page, mid: str) -> list:
    """One unit's debt (the government page's Money tab). Since 2026-11-18 (gap-fill round 2: the state files for
    2022, 2023 and 2025 joined 2024): its total principal at the end of each year as columns (unit_debt_years_chart),
    the latest year's total and the part due within one year, the latest year's rows by class (the chart keeps its id
    debt-<anchor>), every class row of every year behind "Show the table", the notes stored with the totals (never-sum,
    utility) and the unit's own later totals (later_debt_note; never charted or added to the state figures)."""
    c = page.cites
    rows = [r for r in mo.debt if r["unit_id"] == mid and r.get("amount")]
    if not rows:
        return []
    tots = debt_totals(mo, mid)
    due = {r["year"]: r for r in rows if r["debt_type"].startswith(DEBT_DUE)}
    classes = [r for r in rows if r["debt_type"].startswith(DEBT_CLASS)]
    out = []
    chart = unit_debt_years_chart(mo, page, mid)
    if chart is not None:
        out.append(chart)
    if tots:
        y = max(tots)
        r = tots[y]
        d = due.get(y)
        out.append(h("p", None, f"Principal still owed at the end of {y}, as {mo.label(mid)} reported it to the "
                                f"state: {usd(r['amount'])}", c.cite(r["source_ids"]),
                     (f"; {usd(d['amount'])} of it due within one year" if d else ""),
                     c.cite(d["source_ids"]) if d else None, ". ", status_badge(r["status"], page),
                     " Totals include utility debt where a unit has utilities."))
    if classes:
        ly = max(r["year"] for r in classes)
        latest = [r for r in classes if r["year"] == ly]
        hr = [{"label": r["debt_type"].replace(DEBT_CLASS, "")[:46], "value": float(r["amount"]),
               "display": usd_short(r["amount"]),
               "tip": f"{r['debt_type']}: {usd(r['amount'])} at the end of {r['year']}"}
              for r in sorted(latest, key=lambda r: r["debt_type"])]
        out.append(hbar(f"debt-{mo.anchor(mid)}", f"Debt by class, end of {ly}", hr,
                        subtitle="Principal outstanding, as reported to the state", money=True, value_fmt=usd_short,
                        status="official" if all(r["status"] == "official" for r in latest) else "computed",
                        page=page, headers=["Debt type", "Principal"], cite=c.cite(union_sources(latest))))
        trs = [[r["year"], r["debt_type"].replace(DEBT_CLASS, ""), usd(r["amount"]),
                h("span", None, status_badge(r["status"], page), c.cite(r["source_ids"]))]
               for r in sorted(classes + list(due.values()), key=lambda r: (r["year"], r["debt_type"]))]
        out.append(see_all_fold(f"debt-classes-{mo.anchor(mid)}-all", len(trs),
                                data_table(f"debt-classes-{mo.anchor(mid)}", ["Year", "Debt type", "Amount", "Status"],
                                           trs, caption=f"{mo.label(mid)}: debt by class and year", numeric=(2,),
                                           min_width="36rem"),
                                label=f"Show the table: every debt row by class and year ({len(trs)})"))
    notes = debt_notes_block(mo, page, list(tots.values()))
    if notes is not None:
        out.append(notes)
    note = later_debt_note(mo, page, mid)
    if note:
        out.append(note)
    return out


def _breakdown_content(mo: Money, page, mid: str) -> tuple[list, list]:
    c = page.cites
    out = []
    groups = OrderedDict()
    for r in mo.breakdowns:
        if r["unit_id"] == mid and r["year"] == "2024" and r["basis"].startswith("afr_2024"):
            groups.setdefault(r["basis"], []).append(r)
    titles = {"afr_2024_actual_by_department": ("spending", "Spending by department, 2024 actual"),
              "afr_2024_actual_by_expense_class": ("spending", "Spending by kind of expense, 2024 actual"),
              "afr_2024_actual_receipts_by_class": ("revenue", "Receipts by class, 2024 actual"),
              "afr_2024_actual_receipts_by_line": ("revenue", "Receipts by line, 2024 actual")}
    figs, tables = [], []
    for basis, (kind, t) in titles.items():
        rows = groups.get(basis)
        if not rows:
            continue
        total = sum(float(r["amount"]) for r in rows)
        status = rows[0]["status"]
        note = _scope_note(rows)
        if basis == "afr_2024_actual_receipts_by_line":
            trows = [[r["category"], usd(r["amount"]), f"{float(r['amount']) / total * 100:.1f}%"] for r in rows]
            tables.append(h("div", None, h("p", {"class": "mn-others-h"}, f"{t} (table): {note}", c.cite(union_sources(rows))),
                            data_table(f"brk-{mid}-lines", ["Receipt line", "Amount", "Share of file total"], trows,
                                       caption=f"{mo.label(mid)}: {t.lower()}", numeric=(1, 2), min_width="36rem")))
            continue
        hr = [{"label": r["category"][:46], "value": float(r["amount"]), "display": usd_short(r["amount"]),
               "tip": f"{r['category']} · {float(r['amount']) / total * 100:.1f}% of {usd_short(total)}"} for r in rows]
        figs.append(hbar(f"brk-{mid}-{basis.replace('_', '-')}", t, hr, subtitle=f"File total {usd(total)}",
                         money=True, value_fmt=usd_short, status=status, page=page, headers=["Category", "Amount"],
                         note=note, cite=c.cite(union_sources(rows))))
    out.append(h("div", {"class": "chart-grid mn-chart-grid"}, figs))
    out += tables
    own = _flows_target(mo, page, mid)
    if own:
        out.append(h("p", {"class": "mn-unit-note"}, "Its money in and money out (income by source and spending by "
                                                       "purpose, the state's annual report): ",
                     h("a", {"href": own[0]}, own[1]), "."))
    shown = [titles[b][1].replace(", 2024 actual", "").lower() for b in titles if groups.get(b)]
    return out, shown


def _other_breakdowns(mo: Money, page) -> Markup:
    c = page.cites
    groups = OrderedDict()
    for r in mo.breakdowns:
        if not r["basis"].startswith("afr_2024"):
            groups.setdefault((r["unit_id"], r["year"], r["basis"]), []).append(r)
    blocks = []
    for (mid, year, basis), rows in groups.items():
        total = sum(float(r["amount"]) for r in rows)
        trows = [[r["category"], usd(r["amount"]), h("span", None, status_badge(r["status"], page), c.cite(r["source_ids"]))]
                 for r in rows]
        blocks.append(h("div", {"class": "mn-other-breakdown"},
                        one_fold(mo.anchor(mid), mo.label(mid),
                                 one_summary("h4", f"{mo.label(mid)}, {year}", f"{rows[0]['kind']}; rows total {usd(total)}"),
                                 [h("p", {"class": "mn-others-h"}, rows[0]["notes"]),
                                  data_table(f"obrk-{mid}-{basis.replace('_', '-')}", ["Category", "Amount", "Status"], trows,
                                             caption=f"{mo.label(mid)} {year}: {basis.replace('_', ' ')} (rows total {usd(total)})",
                                             numeric=(1,), min_width="30rem")])))
    return h("div", None, h("h3", None, "Other breakdowns in the guide's data"),
             h("p", {"class": "muted"}, "Proposed figures, a later budget year, and news-reported department amounts. "
                                        "Shown as tables because each has a different scope from the 2024 actuals."),
             h("div", {"class": "one-list"}, blocks))


AV_GROUPS = [("County and cities", ("county", "city")), ("Towns", ("town",)), ("Townships", ("township",)),
             ("School corporations, libraries and special units", ("school", "library", "special"))]


def chart_label(mo: Money, mid: str) -> str:
    """A unit's name, short enough for a bar label (the bar's tip keeps the full name)."""
    name = re.sub(r" \(.*\)$", "", mo.label(mid))
    name = name.replace(" Corporation", " Corp.").replace(" Fire Protection Territory", " Fire Territory")
    if group_of(mid) == "special":
        name = re.sub(r"^St\. Joseph County ", "", name)
    if group_of(mid) == "library":
        name = name.replace(" Public Library", " Library") if len(name) > 30 else name
    return name


def _assessed_value_block(mo: Money, page) -> Markup | None:
    """The tax base: certified net assessed value (dlgf_certified rows only) over time for the county and the two
    cities, and by unit for the latest certified year. The units' own Gateway estimates are never charted."""
    ed = mo.ed
    c = page.cites
    series, srcs = [], []
    for mid, mark in (("county-st-joseph", "m-accent"), ("city-south-bend", "m-ink"), ("city-mishawaka", "mn-m3")):
        rows = tb.certified(ed, mid)
        if rows:
            series.append({"name": mo.label(mid).replace(" (civil city)", ""), "mark": mark,
                           "points": [(int(y), tb.av_value(rows[y])) for y in sorted(rows)]})
            srcs += [rows[y] for y in sorted(rows)]
    latest = {mid: tb.latest_certified(ed, mid) for mid in mo.unit_ids}
    latest = {m: r for m, r in latest.items() if r}
    if not series and not latest:
        return None
    year = max(r["year"] for r in latest.values()) if latest else None
    latest = {m: r for m, r in latest.items() if r["year"] == year}
    years = sorted({x for s in series for x, _ in s["points"]})
    # units that levy on exactly the same value as another unit (the same area): say so in the tip
    by_value = {}
    for m, r in latest.items():
        by_value.setdefault(r["net_assessed_value"], []).append(m)
    figs, part_units = [], []
    for title, groups in AV_GROUPS:
        ids = [m for m in mo.unit_ids if m in latest and group_of(m) in groups]
        if not ids:
            continue
        rows = []
        for m in ids:
            r = latest[m]
            v = tb.av_value(r)
            part = tb.part_only(r)
            if part:
                part_units.append(m)
            same = [mo.label(x) for x in by_value[r["net_assessed_value"]] if x != m]
            tip = f"{mo.label(m)}: {usd(v)}, fund {r['fund']}"
            if part:
                tip += "; St. Joseph County part only"
            if same:
                tip += "; same value as " + ", ".join(same)
            rows.append({"label": chart_label(mo, m) + (" *" if part else ""), "value": v,
                         "display": usd_short(v), "tip": tip})
        note = ["Each unit's value is read from its General fund (Operations for school corporations; the "
                "unit's own fund for special units) in the state's certified budget order."]
        if any(tb.part_only(latest[m]) for m in ids):
            note.append(" * St. Joseph County part only: the corporation also lies in another county, and the "
                        "other county's part is not included.")
        figs.append(hbar(f"av-{year}-{groups[0]}", f"{title}: certified net assessed value, {year}", rows,
                         money=True, value_fmt=usd_short, status="official", page=page,
                         headers=["Unit", "Net assessed value"], note="".join(note),
                         cite=c.cite(union_sources(latest[m] for m in ids))))
    lead = h("p", None, "The tax base is the net assessed value of the property a government can tax: the assessed "
                        "value after deductions and exemptions. Each year the state's Department of Local Government "
                        "Finance certifies it for every unit, in the same budget order that certifies the budget and the "
                        "rates. A unit's levy is its tax rate times this value. The values overlap: the county's value "
                        "includes every city, town and township in it, and a township's includes the cities and towns "
                        "inside it, so they are never added together.", c.cite(union_sources(latest.values())))
    est = h("p", {"class": "muted"}, "The state's budget file also has a figure each unit entered with its budget, "
                                     "back to 2012. Those are the units' own estimates, made before the value is "
                                     "certified, so the guide does not chart them with the certified values.",
            c.cite("MON-001"))
    over_time = (line("av-over-time", "Certified net assessed value", series,
                      subtitle=f"County and the two cities, {years[0]} to {years[-1]}", money=True,
                      value_fmt=usd_short, status="official", page=page,
                      note=("From each year's certified budget order (General fund). The county's value includes both "
                            "cities. Nominal dollars."),
                      cite=c.cite(union_sources(srcs))) if series else None)
    return h("div", None, h("h3", None, "The tax base: certified assessed value"), lead,
             h("div", {"class": "chart-grid chart-grid-wide mn-chart-grid"}, over_time) if over_time else None,
             h("div", {"class": "chart-grid mn-chart-grid"}, figs) if figs else None, est)


def _tax_base(mo: Money, page) -> Markup:
    ed = mo.ed
    c = page.cites
    levy = ed.local_rules.get("levy_controls", {})
    caps = ed.local_rules.get("property_tax_caps", {})
    series = []
    flagged = []
    for mid, mark in (("county-st-joseph", "m-accent"), ("city-south-bend", "m-ink"), ("city-mishawaka", "m-accent")):
        rows = sorted((r for r in mo.rates if r["unit_id"] == mid and r["rate_kind"] == "sum_of_fund_net_rates"),
                      key=lambda r: int(r["year"]))
        series.append({"name": mo.label(mid).replace(" (civil city)", ""), "mark": mark,
                       "points": [(int(r["year"]), float(r["rate_per_100"])) for r in rows]})
        flagged += [r for r in rows if "reason not found" in r["notes"]]
    # two series share m-accent would be ambiguous; give each its own class
    series[2]["mark"] = "mn-m3"
    ptax = [r for r in mo.breakdowns if r["category"] == "General Property Taxes" and r["year"] == "2024"]
    prow = [[mo.label(r["unit_id"]), usd(r["amount"]), h("span", None, status_badge(r["status"], page), c.cite(r["source_ids"]))]
            for r in ptax]
    flag_txt = "; ".join(f"{mo.label(r['unit_id'])} {r['year']}: " + re.search(r"Changed [^;]+", r["notes"]).group(0)
                         for r in flagged)
    rate_years = sorted({x for s in series for x, _ in s["points"]})
    return section("tax-base", 6, "How the tax base shapes budgets",
                   h("p", None, levy.get("plain_language", ""), c.cite(levy.get("source_ids")), " ",
                     caps.get("plain_language", ""), c.cite(caps.get("source_ids")), " ", scope_badge("indiana", ed)),
                   h("p", None, "The state's budget file lists an adopted tax rate for each fund a government levies, in "
                                "dollars per $100 of assessed value. The chart adds those up for each government: its own rate, "
                                "before any other government's rate is added. These are the rates the government adopted; the "
                                "state's Department of Local Government Finance certifies the final rates, which can be lower. The "
                                "certified rates, and the combined rate for each taxing district, are on ",
                     h("a", {"href": page.rel("money/your-tax-bill/index.html")}, "Your tax bill"), ".",
                     c.cite("MON-001")),
                   line("rates-over-time", "Unit-wide adopted property-tax rate, per $100 of assessed value", series,
                        subtitle=(f"County and the two cities' civil governments, {rate_years[0]} to {rate_years[-1]}"
                                  if rate_years else "County and the two cities' civil governments"),
                        value_fmt=lambda v: f"${v:.2f}", status="computed", page=page,
                        note=h("span", None, "Computed: the sum of the adopted net tax rate of every fund the unit levies. "
                                             "This is not the rate on a tax bill: the rates of overlapping units (township, "
                                             "school, library) are not added. ",
                               f"Changes of more than 40% with no reason found in the state data: {flag_txt}." if flag_txt else ""),
                        cite=c.cite("MON-001")),
                   _assessed_value_block(mo, page),
                   h("p", None, "General property taxes received in 2024, from the annual financial report receipts:"),
                   data_table("ptax-2024", ["Unit", "General property taxes, 2024", "Status"], prow,
                              caption="Property-tax receipts, 2024 actual", numeric=(1,)),
                   h("p", None, "The guide does not yet have certified assessed values before 2020, or the dollar amount of "
                                "tax-cap credits each unit loses (see ", h("a", {"href": "#gaps"}, "Gaps"), "). See ",
                     h("a", {"href": page.rel("money/your-tax-bill/index.html")}, "Your tax bill"), " for how one bill is split, and ",
                     h("a", {"href": page.rel("community/housing-and-education/index.html")}, "Housing and education"),
                     " for home values."),
                   scope="county", ed=ed)


# =================================================================== tax bill page

CERT_SRC = {"2026": "MON-026", "2025": "MON-027"}   # DLGF certified budget orders


def _district_rows(mo: Money) -> "OrderedDict[str, dict]":
    """Certified taxing-district rates: {code: {code, name, rates: {year: rate}, sources}} in code order."""
    out: "OrderedDict[str, dict]" = OrderedDict()
    for r in sorted((r for r in mo.rates if r["rate_kind"] == "certified_district_rate"),
                    key=lambda r: r["taxing_district"]):
        m = re.match(r"taxing district (\d{3}) (.+)$", r["taxing_district"])
        if not m:
            mo.ed.warnings.append(f"money: unreadable taxing district {r['taxing_district']!r}")
            continue
        d = out.setdefault(m.group(1), {"code": m.group(1), "name": m.group(2).strip(), "rates": {}, "src": {}})
        d["rates"][r["year"]] = float(r["rate_per_100"])
        d["src"][r["year"]] = r["source_ids"]
    return OrderedDict(sorted(out.items()))


ROLE = {"county": "County", "city": "City or town", "town": "City or town", "township": "Township",
        "school": "School corporation", "library": "Library", "special": "Special unit"}


def _district_units(mo: Money) -> tuple[dict, list[str]]:
    """The state's per-district breakdown (rate_kind certified_district_unit_rate): {code: {year: [[unit, rate]]}},
    units in the guide's unit order, and the source ids used. Empty when the rows are absent."""
    out: dict = {}
    srcs: set = set()
    for r in (r for r in mo.rates if r["rate_kind"] == "certified_district_unit_rate"):
        m = re.match(r"taxing district (\d{3}) ", r["taxing_district"])
        if not m:
            mo.ed.warnings.append(f"money: unreadable taxing district {r['taxing_district']!r}")
            continue
        out.setdefault(m.group(1), {}).setdefault(r["year"], []).append([r["unit_id"], float(r["rate_per_100"])])
        srcs.update(split_ids(r["source_ids"]))
    order = {m: i for i, m in enumerate(mo.unit_ids)}
    for years in out.values():
        for lst in years.values():
            lst.sort(key=lambda p: (order.get(p[0], len(order)), p[0]))
    return out, sorted(srcs)


def _district_prefill(name: str, places: list[dict]) -> dict:
    """Units a district's name states outright (city or town, township, school). Nothing is guessed: a
    part the name doesn't state is left for the reader to pick."""
    n = re.sub(r"\s+", " ", name.replace("-", " - ")).strip()
    pre = {"place": "", "township": "", "school": ""}
    by_label = {p["label"].lower(): p for p in places}
    m = re.match(r"^(\w+) Township$", n)
    if m:
        p = by_label.get(f"unincorporated {m.group(1).lower()} township")
        if p:
            pre.update(place=p["id"], township=f"township-{m.group(1).lower()}")
        return pre
    m = re.match(r"^(\w+) Township - Mishawaka Schools$", n)
    if m:
        p = by_label.get(f"unincorporated {m.group(1).lower()} township")
        pre.update(place=p["id"] if p else "", township=f"township-{m.group(1).lower()}", school="school-mishawaka")
        return pre
    m = re.match(r"^(South Bend|Mishawaka)(?: - | )(.+)$", n)
    if m:
        city = m.group(1).lower().replace(" ", "-")
        rest = m.group(2)
        pre["place"] = city
        if rest.lower() == "phm school":
            pre.update(township="township-penn", school="school-phm")
        else:
            pre["township"] = f"township-{rest.split()[0].lower()}"
        return pre
    p = by_label.get(f"town of {n.lower()}")
    if p:
        pre["place"] = p["id"]
    return pre


def _rate_compare_text(total: float, n_rates: int, district: float | None, year: str) -> str:
    """Same wording as money.js (rateCompare): never forces the units to match the district rate."""
    if district is None:
        return f"The guide has no certified rate for this taxing district in {year}."
    if not n_rates:
        return "Pick the units that tax the property to see how the district's rate is shared among them."
    diff = total - district
    if abs(diff) < 0.00005:
        return (f"The certified rates of the units picked add up to the district's certified rate "
                f"(${district:.4f}).")
    return (f"The unit-wide certified rates of the units picked add up to ${total:.4f}, which is ${abs(diff):.4f} "
            f"{'more' if diff > 0 else 'less'} than the district's certified rate of ${district:.4f}. The guide doesn't "
            f"have the state's breakdown of each unit's rate within this district for {year}.")


def _composition_text(total: float, district: float | None, differ: list) -> list[str]:
    """Same wording as money.js (compositionText). `differ`: [(label, rate here, unit-wide rate)]."""
    out = []
    if district is not None and abs(total - district) < 0.00005:
        out.append(f"These unit rates add up to the district's certified rate (${district:.4f}).")
    elif district is not None:
        out.append(f"These unit rates add up to ${total:.4f}; the district's certified rate is ${district:.4f}.")
    if differ:
        out.append("In this district the state lists some units at a rate other than their unit-wide certified rate: "
                   + "; ".join(f"{lab} ${here:.4f} here (${wide:.4f} unit-wide)" for lab, here, wide in differ)
                   + ". A unit's rate in a district is the sum of the funds it levies there.")
    return out


def build_tax_bill(site):
    ed = site.ed
    mo = money(ed)
    page = site.page("money/your-tax-bill/index.html", banners=False)
    c = page.cites
    adopted = [r for r in mo.rates if r["rate_kind"] == "sum_of_fund_net_rates"]
    adopted_years = sorted({int(r["year"]) for r in adopted})
    certified = [r for r in mo.rates if r["rate_kind"] == "certified_unit_rate"]
    cert_years = sorted({r["year"] for r in certified}, reverse=True)
    districts = _district_rows(mo)
    comp, comp_src = _district_units(mo)
    y_last = cert_years[0] if cert_years else ""
    units = OrderedDict()
    for mid in mo.unit_ids:
        cert = {r["year"]: float(r["rate_per_100"]) for r in certified if r["unit_id"] == mid}
        adop = {str(r["year"]): float(r["rate_per_100"]) for r in adopted if r["unit_id"] == mid}
        units[mid] = {"label": re.sub(r" \(state data: .*\)$", "", mo.label(mid)), "group": group_of(mid),
                      "role": ROLE.get(group_of(mid), "Unit"),
                      "uid": ed.unit_alias(mid) or "", "cert": cert, "adopted": adop}
    rev = {v["uid"]: k for k, v in units.items() if v["uid"]}
    lay = build_layers(ed)
    places = []
    for p in lay["places"]:
        places.append({"id": p["id"], "label": p["label"], "muni": rev.get(p["muni"] or "", "") if p["muni"] else "",
                       "township": rev.get(p["township"] or "", ""), "school": rev.get(p["school_default"] or "", "")})
    dlist = []
    for code, d in districts.items():
        parts = {y: [p for p in lst if p[0] in units] for y, lst in comp.get(code, {}).items()}
        for y, lst in comp.get(code, {}).items():
            for p in lst:
                if p[0] not in units:
                    ed.warnings.append(f"money: district {code} {y} unit {p[0]!r} not in the money units")
            if y in d["rates"] and abs(sum(p[1] for p in parts[y]) - d["rates"][y]) >= 0.00005:
                ed.warnings.append(f"money: district {code} {y} unit rates add up to "
                                   f"{sum(p[1] for p in parts[y]):.4f}, not the certified {d['rates'][y]:.4f}")
        dlist.append({"code": code, "name": d["name"], "rates": d["rates"], "units": parts,
                      "pre": _district_prefill(d["name"], places)})
    for code in sorted(set(comp) - set(districts)):
        ed.warnings.append(f"money: district {code} has unit rates but no certified district rate")
    default = next((d for d in dlist if d["name"] == "South Bend - Portage"), dlist[0] if dlist else None)

    by_group = lambda g: [(m, u) for m, u in units.items() if u["group"] == g]
    townships = by_group("township")
    libs = [(m, u) for m, u in by_group("library") if u["cert"]]
    specials = [(m, u) for m, u in by_group("special") if u["cert"]]
    school_units = [u for u in ed.tables["units"] if u["unit_type"] == "school_corporation"]
    school_opts = [("", "Not chosen")]
    for su in school_units:
        mid = rev.get(su["unit_id"])
        school_opts.append((mid or f"none:{su['unit_id']}",
                            su["name"] + ("" if mid and units[mid]["cert"] else " (no certified rate in the guide's data)")))

    def select(sid, label, opts, value, groups=None):
        body = [h("option", {"value": v, "selected": v == value}, t) for v, t in opts]
        if groups:
            body += [h("optgroup", {"label": gl}, [h("option", {"value": v, "selected": v == value}, t) for v, t in items])
                     for gl, items in groups.items() if items]
        return h("div", {"class": "field", "id": f"{sid}-field"}, h("label", {"for": sid}, label),
                 h("select", {"id": sid, "name": sid}, body))

    pre = default["pre"] if default else {"place": "", "township": "", "school": ""}
    sel = {"district": default["code"] if default else "", "year": y_last, "place": pre["place"],
           "township": pre["township"], "school": pre["school"], "library": ""}
    place_obj = next((p for p in places if p["id"] == sel["place"]), None)
    if place_obj and not sel["school"]:
        sel["school"] = place_obj["school"]
    pgroups = OrderedDict([("Cities", []), ("Towns", []), ("Unincorporated areas", [])])
    for p in lay["places"]:
        key = {"city": "Cities", "town": "Towns"}.get(p["kind"], "Unincorporated areas")
        pgroups[key].append((p["id"], p["label"]))
    district_picker = h("form", {"class": "picker mn-picker", "id": "tb-district-picker", "aria-label": "Choose a taxing district"},
                        h("p", {"class": "picker-head mono"}, "Taxing district"),
                        select("tb-district", "Taxing district", [(d["code"], f"{d['code']} {d['name']}") for d in dlist],
                               sel["district"]),
                        select("tb-year", "Tax year (payable)", [(y, y) for y in cert_years], sel["year"]),
                        h("p", {"class": "picker-help"},
                          "Every property sits in one taxing district: the set of governments that tax it. Your tax bill "
                          "names the district. The guide doesn't match addresses to districts."))
    default_comp = (default["units"].get(sel["year"]) or None) if default else None
    unit_picker = h("form", {"class": "picker mn-picker", "id": "tb-picker", "aria-label": "Choose the units that tax a property",
                             "hidden": bool(default_comp)},
                    h("p", {"class": "picker-head mono"}, "Units in the district"),
                    select("tb-place", "City, town or unincorporated area", [("", "Not chosen")], sel["place"],
                           pgroups),
                    select("tb-township", "Township", [("", "Not chosen")] + [(m, u["label"]) for m, u in townships],
                           sel["township"]),
                    select("tb-school", "School corporation", school_opts, sel["school"]),
                    select("tb-library", "Library", [("", "Not chosen")] + [(m, u["label"]) for m, u in libs], sel["library"]),
                    h("fieldset", {"class": "mn-specials", "id": "tb-specials"},
                      h("legend", None, "Special units (add if they tax the property)"),
                      [h("label", {"class": "mn-check", "for": f"tb-sp-{m}"},
                         h("input", {"type": "checkbox", "id": f"tb-sp-{m}", "value": m, "data-special": m}), u["label"])
                       for m, u in specials]),
                    h("p", {"class": "picker-help"},
                      "Choosing a district fills in the city or town, township and school its name states. Anything the "
                      "name doesn't state is left for you to pick."))
    dist_rate = default["rates"].get(sel["year"]) if default else None
    chosen = [("county-st-joseph", "County")]
    if place_obj and place_obj["muni"]:
        chosen.append((place_obj["muni"], "City or town"))
    chosen += [(sel["township"], "Township"), (sel["school"], "School corporation"), (sel["library"], "Library")]
    payload = {"units": {m: {"label": u["label"], "role": u["role"], "cert": u["cert"]} for m, u in units.items()},
               "places": places, "districts": dlist, "years": cert_years, "default": sel,
               # units.csv id -> money id, so static/js/money.js can start from the saved place (civic-place)
               "uidmap": {uid: mid for uid, mid in rev.items() if uid}}
    # saved-place preselect (Wave E batch 8): the township and school each district fits, in the saved place's ids
    # (civic/preselect.py district_hints; money.js picks a district only when exactly one fits)
    payload["hints"] = district_hints(dlist, payload["uidmap"])
    caps = ed.local_rules.get("property_tax_caps", {})
    cap_detail = sentences(caps.get("detail", ""))
    credit_sents = [s for s in cap_detail if re.search(r"credit|referendum|first due", s)]
    hc = ed.local_rules.get("sea1_homestead_credit", {})
    cert_src = ";".join(CERT_SRC[y] for y in cert_years if y in CERT_SRC)
    toc = [("district", "Your district's tax rate"), ("split", "How the rate is shared"), ("all-rates", "Every unit's rate"),
           ("caps", "Tax caps and credits"), ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(hero(page, "Reference · Money", page.title,
                  h("span", None, "One property-tax bill carries the rates of several governments: the county, a township, "
                                  "a school corporation, and for many properties a city or town, a library or another unit. "
                                  "The state certifies one combined rate for each taxing district. Pick a district to see its "
                                  f"certified rate ({' and '.join(reversed(cert_years))}) and how it is shared among the units "
                                  "that levy it.", c.cite(cert_src)),
                  toc, [scope_badge("county", ed), " ", scope_badge("indiana", ed),
                        h("span", {"class": "muted"}, " marks rules that apply in every county.")]))

    # ------------------------------------------------------------------ 1 district rate
    page.add(section("district", 1, "Your district's tax rate",
                     h("p", None, "The Department of Local Government Finance reviews every unit's budget and certifies the "
                                  "rates that are actually levied. Its yearly budget order for the county lists the combined "
                                  "rate for each taxing district: the rate on the bill before any credits.",
                       c.cite(cert_src), " ", status_badge("official", page)),
                     district_picker,
                     here_slot("taxbill", "tb-district"),
                     h("div", {"class": "mn-tb", "id": "tb-district-out", "aria-live": "polite"},
                       _render_district(default, sel["year"])),
                     h("p", {"class": "muted"}, "Rates are dollars per $100 of assessed value. The marks at $1, $2 and $3 "
                                                "show the tax caps written as rates: 1% of assessed value is $1 per $100. "
                                                "Whether a cap credit applies depends on the property's own assessment and "
                                                "deductions, which the guide can't compute."),
                     scope="county", ed=ed))

    # ------------------------------------------------------------------ 2 split
    comp_years = sorted({y for d in dlist for y, lst in d["units"].items() if lst}, reverse=True)
    if comp_years:
        split_intro = h("p", None, "For each taxing district, the state publishes the rate each unit levies there, fund "
                                   f"by fund ({' and '.join(reversed(comp_years))}). Choosing a district lists those units "
                                   "and their rates, which add up to the district's rate. Each unit's share is the guide's "
                                   "arithmetic: its rate divided by the district's rate. Where the guide doesn't have that "
                                   "breakdown, you pick the units and the guide adds up their unit-wide certified rates "
                                   "from the budget order.",
                        c.cite(";".join([cert_src, *comp_src])), " ",
                        status_badge("official", page, "Unit rates: DLGF certified."), " ",
                        status_badge("computed", page, "Shares and totals are the guide's arithmetic."))
    else:
        split_intro = h("p", None, "Each unit's certified rate is from the same budget order. The share of each unit is the "
                                   "guide's arithmetic: its rate divided by the total of the units picked.",
                        c.cite(cert_src), " ", status_badge("official", page, "Unit rates: DLGF certified."), " ",
                        status_badge("computed", page, "Shares and the total of the units picked are the guide's arithmetic."))
    page.add(section("split", 2, "How the rate is shared among units",
                     split_intro,
                     unit_picker,
                     h("div", {"class": "mn-tb", "id": "tb-out", "aria-live": "polite"},
                       _render_composition(units, default, sel["year"]) if default_comp
                       else _render_units(units, chosen, sel["year"], dist_rate)),
                     json_script("taxbill-data", payload),
                     scope="county", ed=ed))

    # ------------------------------------------------------------------ 3 every unit
    latest = [{"label": u["label"], "value": u["cert"][y_last], "display": rate_fmt(u["cert"][y_last])}
              for m, u in units.items() if y_last in u["cert"]]
    cert_rows = [[u["label"]] + [f"{u['cert'][y]:.4f}" if y in u["cert"] else "" for y in reversed(cert_years)]
                 for m, u in units.items() if u["cert"]]
    drows = [[f"{d['code']} {d['name']}"] + [f"{d['rates'][y]:.4f}" if y in d["rates"] else "" for y in reversed(cert_years)]
             for d in dlist]
    hdr = ["Unit"] + [str(y) for y in adopted_years]
    trows = [[u["label"]] + [f"{u['adopted'][str(y)]:.4f}" if str(y) in u["adopted"] else "" for y in adopted_years]
             for m, u in units.items() if u["adopted"]]
    flagged = [r for r in adopted if "reason not found" in r["notes"]]
    page.add(section("all-rates", 3, "Every unit's rate",
                     hbar("rates-latest", f"Certified unit-wide property-tax rate, {y_last}", latest,
                          subtitle="Dollars per $100 of assessed value, as certified by the state", value_fmt=rate_fmt,
                          status="official", page=page, headers=["Unit", "Rate per $100"],
                          note="Units in the order used across the guide. Each unit's rate applies where it levies; a "
                               "bill adds the rates of every unit in the district (see above).",
                          cite=c.cite(CERT_SRC.get(y_last, cert_src))),
                     data_table("rates-certified", ["Unit"] + list(reversed(cert_years)), cert_rows,
                                caption="Certified unit rates, dollars per $100 of assessed value",
                                numeric=tuple(range(1, len(cert_years) + 1))),
                     data_table("rates-districts", ["Taxing district"] + list(reversed(cert_years)), drows,
                                caption="Certified taxing-district rates (all units combined, before credits)",
                                numeric=tuple(range(1, len(cert_years) + 1))),
                     h("h3", {"id": "adopted-rates"}, "What each unit asked for, before state certification"),
                     h("p", None, "Each unit's budget filing states the rate it adopted. The state's budget file lists those "
                                  "adopted rates fund by fund; the guide adds them up for each unit. The state then certifies "
                                  "the final rate, which is often lower, for example when assessed values rose or a levy limit "
                                  "applied. These adopted rates are not what was levied.",
                       c.cite("MON-001"), " ", status_badge("computed", page, "Sums of the adopted fund rates.")),
                     data_table("rates-all-years", hdr, trows,
                                caption="Adopted unit-wide rates by year (before certification), dollars per $100 of assessed value",
                                numeric=tuple(range(1, len(hdr))), min_width="80rem"),
                     h("p", {"class": "muted"}, f"{len(flagged)} unit-years of adopted rates changed by more than 40% from "
                                                "the year before with no reason found in the state data; they are listed "
                                                "under Gaps.", c.cite("MON-001")),
                     scope="county", ed=ed))
    page.add(section("caps", 4, "Tax caps and credits",
                     h("p", None, caps.get("plain_language", ""), c.cite(caps.get("source_ids"))),
                     h("p", None, " ".join(credit_sents), c.cite(caps.get("source_ids"))) if credit_sents else None,
                     h("p", None, "These credits are often called circuit-breaker credits. The guide doesn't yet have the "
                                  "dollar amount of credits for each unit (see Gaps).", c.cite("MON-024")),
                     h("p", None, hc.get("plain_language", ""), c.cite(hc.get("source_ids")), " ",
                       status_badge(hc.get("status", ""), page)) if hc else None,
                     h("p", None, "More on state limits: ",
                       h("a", {"href": page.rel("state/how-the-state-shapes-local/index.html")}, "How the state shapes local government"), "."),
                     scope="indiana", ed=ed))
    rate_gaps = [{"item": f"{mo.label(r['unit_id'])} {r['year']} adopted unit-wide rate: unexplained change",
                  "why_missing": re.search(r"Changed [^;]+; reason not found", r["notes"]).group(0) + ".",
                  "how_to_fill": "Check the unit's fund rates in the Gateway budget file for that year."} for r in flagged]
    lacks = lambda u: [y for y in reversed(cert_years) if y in u["adopted"] and y not in u["cert"]]
    missing_cert = [u["label"] for m, u in units.items() if lacks(u)]
    extra = []
    if missing_cert:
        extra.append({"item": "Certified unit rates missing for some units or years",
                      "why_missing": "The unit adopted a rate, but the guide has no certified rate for: " + "; ".join(
                          f"{u['label']} ({', '.join(lacks(u))})" for m, u in units.items() if lacks(u)) + ".",
                      "how_to_fill": "Read the unit's page in the DLGF budget order for that year."})
    no_comp = [f"{d['code']} {d['name']} ({', '.join(y for y in reversed(cert_years) if y in d['rates'] and not d['units'].get(y))})"
               for d in dlist if any(y in d["rates"] and not d["units"].get(y) for y in cert_years)]
    if no_comp:
        extra.append({"item": "Unit rates within " + ("some taxing districts" if comp else "each taxing district"),
                      "why_missing": ("The guide has the district's certified rate but not the state's breakdown of each "
                                      "unit's rate within it for: " + "; ".join(no_comp) + ".") if comp else
                                     ("The guide has each district's certified rate but not the state's breakdown of each "
                                      "unit's rate within it, so section 2 adds up unit-wide rates instead."),
                      "how_to_fill": "DLGF report: certified tax rates by taxing district and unit, for that year."})
    page.finish(gaps=money_gaps(ed, r"tax-district|assessed|Circuit|SEA 1|HB 1210|Indian Village") + extra + rate_gaps)
    return page


SEG_CLASSES = 6


def _cap_marks(scale: float) -> list:
    return [h("span", {"class": "mn-tb-cap", "style": f"left: {v / scale * 100:.2f}%"}, h("span", {"class": "mn-tb-cap-l mono"}, lab))
            for v, lab in ((1, "1% cap"), (2, "2%"), (3, "3%"))]


def _render_district(d: dict | None, year: str) -> Markup:
    """Static version of what money.js draws for the district: the certified rate and the cap marks."""
    if not d:
        return h("p", None, "The guide has no certified taxing-district rates.")
    r = d["rates"].get(year)
    if r is None:
        return h("p", {"class": "mn-tb-total"}, f"No certified rate in the guide's data for district {d['code']} in {year}.")
    scale = max(3.0, math.ceil(r * 2) / 2 + 0.5)
    other = [(y, v) for y, v in sorted(d["rates"].items(), reverse=True) if y != year]
    return join([
        h("p", {"class": "mn-tb-total"}, h("span", {"class": "mono"}, f"{year} certified rate, district {d['code']} {d['name']}: "),
          h("strong", {"class": "mn-tb-sum"}, f"${r:.4f}"), " per $100 of assessed value"),
        h("div", {"class": "mn-tb-bar", "role": "img",
                  "aria-label": f"Bar: certified district rate ${r:.4f} per $100, with the 1%, 2% and 3% cap marks"},
          h("span", {"class": "mn-tb-seg mn-seg-0", "style": f"width: {r / scale * 100:.2f}%"}), _cap_marks(scale)),
        h("p", {"class": "muted mn-tb-other"}, "; ".join(f"{y}: ${v:.4f}" for y, v in other)) if other else None])


def _render_composition(units, d: dict, year: str) -> Markup:
    """Static version of what money.js draws when the state's per-district breakdown exists: every unit that taxes
    the district, its rate there, and its share of the district's rate."""
    parts = d["units"].get(year) or []
    district = d["rates"].get(year)
    total = sum(r for _, r in parts)
    scale = max(3.0, math.ceil(max(total, district or 0) * 2) / 2 + 0.5)
    segs, lis, differ = [], [], []
    for k, (mid, r) in enumerate(parts):
        u = units[mid]
        share = r / total * 100 if total else 0
        cls = f"mn-seg-{k % SEG_CLASSES}"
        segs.append(h("span", {"class": f"mn-tb-seg {cls}", "style": f"width: {r / scale * 100:.2f}%",
                               "title": f"{u['label']}: ${r:.4f} per $100 ({share:.1f}% of the district's rate)"}))
        lis.append(h("li", {"class": "mn-tb-item"}, h("span", {"class": f"mn-tb-key {cls}", "aria-hidden": "true"}),
                     h("span", {"class": "mn-tb-role mono"}, u["role"]), h("span", {"class": "mn-tb-name"}, u["label"]),
                     h("span", {"class": "mn-tb-val mono"}, f"${r:.4f} · {share:.1f}%")))
        wide = u["cert"].get(year)
        if wide is not None and abs(wide - r) >= 0.00005:
            differ.append((u["label"], r, wide))
    return join([
        h("p", {"class": "mn-tb-total"}, h("span", {"class": "mono"}, f"{year} certified rates of the units that tax district "
                                                                       f"{d['code']} {d['name']}: "),
          h("strong", {"class": "mn-tb-sum"}, f"${total:.4f}"), " per $100 of assessed value"),
        h("div", {"class": "mn-tb-bar", "role": "img",
                  "aria-label": f"Stacked bar: district {d['code']} units total ${total:.4f} per $100, split among the units listed below"},
          segs, _cap_marks(scale)),
        h("ul", {"class": "mn-tb-list"}, lis),
        [h("p", {"class": "mn-tb-compare"}, t) for t in _composition_text(total, district, differ)]])


def _render_units(units, chosen, year, district_rate) -> Markup:
    """Static version of what money.js draws for the units: certified rates, computed shares, comparison."""
    items, total, n = [], 0.0, 0
    for mid, role in chosen:
        if not mid or mid.startswith("none:"):
            items.append((role, None, None, "Not chosen" if not mid else "No certified rate in the guide's data"))
            continue
        u = units[mid]
        r = u["cert"].get(year)
        items.append((role, u["label"], r, None if r is not None else f"No certified rate in the guide's data for {year}"))
        if r is not None:
            total += r
            n += 1
    scale = max(3.0, math.ceil(max(total, district_rate or 0) * 2) / 2 + 0.5)
    segs, lis = [], []
    k = 0
    for role, label, r, missing in items:
        if r is None:
            lis.append(h("li", {"class": "mn-tb-item mn-tb-missing"}, h("span", {"class": "mn-tb-key mn-tb-key-none", "aria-hidden": "true"}),
                         h("span", {"class": "mn-tb-role mono"}, role),
                         h("span", {"class": "mn-tb-name"}, label or missing), h("span", {"class": "mn-tb-val"}, missing if label else "")))
            continue
        share = r / total * 100 if total else 0
        cls = f"mn-seg-{k % SEG_CLASSES}"
        segs.append(h("span", {"class": f"mn-tb-seg {cls}", "style": f"width: {r / scale * 100:.2f}%",
                               "title": f"{label}: ${r:.4f} per $100 ({share:.1f}% of the units picked)"}))
        lis.append(h("li", {"class": "mn-tb-item"}, h("span", {"class": f"mn-tb-key {cls}", "aria-hidden": "true"}),
                     h("span", {"class": "mn-tb-role mono"}, role), h("span", {"class": "mn-tb-name"}, label),
                     h("span", {"class": "mn-tb-val mono"}, f"${r:.4f} · {share:.1f}%")))
        k += 1
    return join([
        h("p", {"class": "mn-tb-total"}, h("span", {"class": "mono"}, f"{year} certified rates of the units picked: "),
          h("strong", {"class": "mn-tb-sum"}, f"${total:.4f}"), " per $100 of assessed value"),
        h("div", {"class": "mn-tb-bar", "role": "img",
                  "aria-label": f"Stacked bar: units picked total ${total:.4f} per $100, split among the units listed below"},
          segs, _cap_marks(scale)),
        h("ul", {"class": "mn-tb-list"}, lis),
        h("p", {"class": "mn-tb-compare"}, _rate_compare_text(total, n, district_rate, year))])


# =================================================================== primer

def build_primer(site):
    ed = site.ed
    mo = money(ed)
    page = site.page("money/what-is-a-budget/index.html", banners=False)
    c = page.cites
    dlgf = ed.local_rules.get("dlgf_role", {})
    split = ed.local_rules.get("county_government_split", {})
    town = ed.local_rules.get("township_role", {})
    levy = ed.local_rules.get("levy_controls", {})

    def amount(series_id, year):
        s = mo.series.get(series_id)
        r = next((r for r in s["rows"] if int(r["year"]) == year), None) if s else None
        return r

    gf26 = amount("county-gateway-general-fund", 2026)
    af26 = amount("county-st-joseph-gateway-advertised-funds", 2026)
    af24 = amount("county-st-joseph-gateway-advertised-funds", 2024)
    wndu = amount("county-news-wndu-2026", 2026)
    aud = amount("county-news-auditor-2026", 2026)
    mish_funds = [r for r in mo.breakdowns if r["basis"] == "mishawaka_2026_approved_by_fund"]
    mish_gf = next((r for r in mish_funds if r["category"] == "General"), None)
    mish_tot = sum(float(r["amount"]) for r in mish_funds)
    sb23 = amount("sb-gateway-allfunds-2012-2023", 2023)
    sb24 = amount("sb-gateway-10funds-2024-2026", 2024)
    sbp = amount("sb-cityoverview-proposed-expenditures", 2024)
    sbnews = amount("sb-news-allfunds", 2024)
    afr_cty = [r for r in mo.breakdowns if r["unit_id"] == "county-st-joseph" and r["basis"] == "afr_2024_actual_by_department"]
    afr_tot = sum(float(r["amount"]) for r in afr_cty)

    toc = [("basics", "What counts as a budget"), ("bases", "Three ways to total a budget"), ("county-example", "$90M, $136M or $248M?"),
           ("adopted-actual", "Adopted, proposed and actual"), ("gateway", "Gateway and the DLGF"),
           ("breaks", "When reporting changes"), ("dollars", "Nominal and constant dollars"), ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(hero(page, "Reference · Money · Start here", page.title,
                  "A budget total depends on which funds are counted. This page explains the terms the guide uses, so the "
                  "numbers on the other money pages can be read correctly.",
                  toc, [scope_badge("indiana", ed), " ", scope_badge("county", ed),
                        h("span", {"class": "muted"}, " marks this county's examples.")]))

    page.add(section("basics", 1, "What counts as a budget",
                     h("p", None, "A budget is the spending plan a local government adopts for a year, fund by fund.",
                       c.cite("MON-001;MON-024"), " Who adopts it depends on the government."),
                     variant_slot(ed, "legislative_power", h("span", None, split.get("plain_language", "")),
                                  {"council_full": h("p", None, "In the counties covered by Indiana Code 36-2-3.5, the county "
                                                                "council is \"the county legislative body as well as the county "
                                                                "fiscal body\", and the commissioners are the executive "
                                                                "(IC 36-2-3.5-3).", c.cite("IND-057"),
                                                     " The chapter covers counties of 450,000 to 700,000 people, counties of "
                                                     "185,000 to 300,000 that opted in under IC 36-2-2-4(c), and any other "
                                                     f"county that adopts it by ordinance. The guide's research reports that "
                                                     f"{ed.county} County is covered; the opt-in record itself has not been "
                                                     "found yet. See ", h("a", {"href": page.rel("governments/county/index.html#structure")},
                                                                         "County government"), ".")},
                                  page, split.get("source_ids")),
                     h("p", None, town.get("plain_language", ""), c.cite(town.get("source_ids"))),
                     h("p", None, dlgf.get("plain_language", ""), c.cite(dlgf.get("source_ids")), " ",
                       levy.get("plain_language", ""), c.cite(levy.get("source_ids"))),
                     h("p", None, "A budget is split into funds. The state's budget file lists each government's budget fund "
                                  "by fund.", c.cite("MON-001;MON-024")),
                     h("p", None, f"For example, Mishawaka's 2026 civil-city budget has {len(mish_funds)} funds that add up to "
                                  f"{usd(mish_tot)}. The General fund is {usd(mish_gf['amount'])} of that, or "
                                  f"{float(mish_gf['amount']) / mish_tot * 100:.0f}%. The rest is in funds such as parks, "
                                  "streets, and police and fire pensions.", c.cite(mish_gf["source_ids"]), " ",
                       status_badge("official", page, "The fund amounts are from the city's budget book."), " ",
                       status_badge("computed", page, "The total and the share are the guide's arithmetic."), " ",
                       scope_badge("county", ed)) if mish_gf else None,
                     scope="indiana", ed=ed))

    # bases table, counted from the data
    counts = {}
    for s in mo.series.values():
        if s["kinds"] == ["adopted"] and set(s["status"]) <= {"official", "computed"}:
            counts[s["basis"]] = counts.get(s["basis"], 0) + 1
    brow = []
    examples = {"general_fund": "County 2026: " + (usd_short(gf26["amount"]) if gf26 else ""),
                "advertised_all_funds": "County 2026: " + (usd_short(af26["amount"]) if af26 else ""),
                "all_funds_incl_utilities": "South Bend 2023: " + (usd_short(sb23["amount"]) if sb23 else ""),
                "gateway_reported_funds": "South Bend 2024: " + (usd_short(sb24["amount"]) if sb24 else "")}
    for b in BASIS_ORDER:
        brow.append([BASIS[b][0], BASIS[b][1], examples[b], str(counts.get(b, 0))])
    page.add(section("bases", 2, "Three ways to total a budget",
                     h("p", None, "News stories and official files total budgets in different ways. They are not "
                                  "interchangeable, so the guide never puts two of them in one chart line.", c.cite("MON-024")),
                     h("dl", {"class": "mn-defs"},
                       h("dt", None, "General fund"),
                       h("dd", None, "One fund, listed as fund 0101 (General) in the state file. It is one of the measures "
                                     "that appear in news reports.", c.cite("MON-001;MON-024")),
                       h("dt", None, "All advertised funds"),
                       h("dd", None, "Every fund a government advertised to the state for the year, added up. Mishawaka's "
                                     "civil-city total leaves out its electric, water and wastewater utilities.",
                         c.cite("MON-001;MON-010")),
                       h("dt", None, "All funds including utilities"),
                       h("dd", None, "Every fund, including water, sewer, trash and other enterprise funds. South Bend's "
                                     "figures through 2023 are on this basis, and so are news reports of its total budget.",
                         c.cite("MON-001;MON-007"))),
                     h("p", None, "The table has a fourth row. It is not a way of totaling a budget but a gap in the state "
                                  "file: from 2024 the file lists only 10 of South Bend's funds, so that series is kept apart "
                                  "(see When reporting changes, below).", c.cite("MON-001")),
                     data_table("bases-table", ["Basis", "What it includes", "Example", "Series in the guide"], brow,
                                caption="Budget bases used in the guide", numeric=(3,), min_width="40rem"),
                     h("p", {"class": "muted"}, "Series counts are computed from the guide's budget data. ",
                       status_badge("computed", page)),
                     scope="indiana", ed=ed))

    ex = []
    cb26 = amount("county-dlgf-certified-2026", 2026)
    if gf26 and af26:
        share = float(gf26["amount"]) / float(af26["amount"]) * 100
        bars = [{"label": "General fund", "value": float(gf26["amount"]), "display": usd_short(gf26["amount"]),
                 "tip": f"{usd(gf26['amount'])}, Gateway fund 0101, adopted"}]
        if cb26:
            bars.append({"label": "Certified by the state", "value": float(cb26["amount"]), "display": usd_short(cb26["amount"]),
                         "tip": f"{usd(cb26['amount'])}, total of the funds in the DLGF budget order"})
        bars.append({"label": "All advertised funds", "value": float(af26["amount"]), "display": usd_short(af26["amount"]),
                     "tip": f"{usd(af26['amount'])}, sum of every fund, adopted"})
        ex.append(h("dl", {"class": "mn-defs"},
                    h("dt", None, f"General fund: {usd_short(gf26['amount'])}"),
                    h("dd", None, "One fund, the county's main operating fund (fund 0101 in the state file). The state certified "
                                  "the same amount.", c.cite("MON-001" + (";" + cb26["source_ids"] if cb26 else ""))),
                    [h("dt", None, f"State-certified budget: {usd_short(cb26['amount'])}"),
                     h("dd", None, "The total of the county funds listed in the Department of Local Government Finance's 2026 "
                                   "budget order, the funds whose budgets, levies and rates the state reviewed and certified.",
                       c.cite(cb26["source_ids"]))] if cb26 else None,
                    h("dt", None, f"All advertised funds: {usd_short(af26['amount'])}"),
                    h("dd", None, "The sum of every fund the county advertised in its budget filing to the state, including funds "
                                  "the budget order doesn't list.", c.cite("MON-001"))))
        ex.append(hbar("county-2026-bases", "St. Joseph County 2026 budget, three ways", bars,
                       subtitle="Adopted and certified figures for the same year", money=True, value_fmt=usd_short,
                       status="computed", page=page, headers=["Basis", "Amount"],
                       note="The general fund and certified figures are official totals; the all-funds figure is the guide's "
                            "sum of every fund line in the state's budget file.",
                       cite=c.cite("MON-001" + (";" + cb26["source_ids"] if cb26 else ""))))
        qrows = []
        for r in (wndu, aud):
            if r:
                qrows.append([r["series_id"].replace("county-news-", "").replace("-2026", "").upper(), usd(r["amount"]),
                              h("span", None, status_badge(r["status"], page), c.cite(r["source_ids"])), clean_note(r["notes"])])
        ex.append(h("p", None, "All three numbers are true; they count different funds. The general fund "
                               f"({usd(gf26['amount'])}) is {share:.1f}% of all advertised funds ({usd(af26['amount'])})"
                               + (f" and {float(gf26['amount']) / float(cb26['amount']) * 100:.1f}% of the state-certified budget "
                                  f"({usd(cb26['amount'])})." if cb26 else "."),
                    c.cite("MON-001" + (";" + cb26["source_ids"] if cb26 else "")), " ", status_badge("computed", page)))
        ex.append(h("p", None, "News reports used different figures. WNDU called \"just over $90 million\" the balanced 2026 "
                               "budget, which matches the general fund line. The county auditor was quoted as saying the "
                               "general fund is $97 million, \"39% of the total budget\". The guide could not confirm which "
                               "totals the quote used, so both are shown as quoted, and the state's files are the documented "
                               "numbers.", c.cite("MON-008;MON-023")))
        ex.append(data_table("county-2026-news", ["Report", "Amount", "Status", "Note"], qrows,
                             caption="County 2026 budget as reported in the news", numeric=(1,), min_width="44rem"))
    page.add(section("county-example", 3, "$90 million, $136 million or $248 million?", ex, scope="county", ed=ed))

    page.add(section("adopted-actual", 4, "Adopted, proposed and actual",
                     h("dl", {"class": "mn-defs"},
                       h("dt", None, "Proposed"),
                       h("dd", None, "The plan before the fiscal body votes. ",
                         f"Example: South Bend's 2024 budget overview proposed {usd_short(sbp['amount'])} in spending; news "
                         f"reports later gave about {usd_short(sbnews['amount'])} as the 2024 budget." if sbp and sbnews else "",
                         c.cite("MON-006;MON-007")),
                       h("dt", None, "Adopted"),
                       h("dd", None, "The budget the fiscal body approves. The guide's budget charts use the adopted column "
                                     "of the state's budget file.", c.cite("MON-001;MON-024")),
                       h("dt", None, "Actual"),
                       h("dd", None, "What was really spent or received, reported after the year ends in each unit's annual "
                                     "financial report.", c.cite("MON-002;MON-003"))),
                     h("p", None, f"Actual files have their own scope too. The county's 2024 department spending file covers "
                                  f"{usd_short(afr_tot)} of disbursements, while its 2024 all-funds budget was "
                                  f"{usd_short(af24['amount'])}. So the file is not total county spending.",
                       c.cite("MON-002;MON-001"), " ", status_badge("computed", page)) if afr_cty and af24 else None,
                     scope="indiana", ed=ed))

    page.add(section("gateway", 5, "Gateway and the DLGF",
                     h("p", None, dlgf.get("plain_language", ""), c.cite(dlgf.get("source_ids"))),
                     h("p", None, "The guide's budget totals and tax rates come from the Gateway budget data download "
                                  f"(budget years {mo.y0} to {mo.y1}). Spending, receipts and debt come from the annual "
                                  "financial report files on the same site, which list the State Board of Accounts as publisher.",
                       c.cite("MON-001;MON-002;MON-003;MON-004")),
                     h("p", None, "One correction the guide made: the downloaded budget file repeated every row five times, so "
                                  "the guide removed the duplicates before adding anything up.", c.cite("MON-001")),
                     scope="indiana", ed=ed))

    page.add(section("breaks", 6, "When reporting changes: series breaks",
                     h("p", None, f"Sometimes a government's figures change because of what is reported, not what is spent. "
                                  f"From 2012 through 2023 the state file lists between 62 and 83 South Bend funds with a budget "
                                  f"each year, including water, sewer "
                                  f"and trash ({usd_short(sb23['amount'])} in 2023). From 2024 it lists only 10 "
                                  f"property-tax-supported funds ({usd_short(sb24['amount'])} in 2024). The drop is a change in "
                                  "reporting, so the guide draws a break and never connects the two." if sb23 and sb24 else "",
                       c.cite("MON-001;MON-007")),
                     h("p", None, "See it on the chart: ",
                       h("a", {"href": page.rel("governments/south-bend/money/index.html#budget")}, "South Bend's Money tab"), "."),
                     scope="county", ed=ed))

    page.add(section("dollars", 7, "Nominal and constant dollars",
                     h("p", None, "Unless a chart says otherwise, every dollar figure in the guide is nominal: the amount in that "
                                  "year's dollars, as the government reported it.", c.cite("MON-024")),
                     h("p", None, "Comparing 2012 and 2026 fairly means restating older amounts with a price index. "
                                  f"The budget charts on each government's Money tab can switch to constant {mo.cpi_base} dollars, using the "
                                  "national Consumer Price Index for All Urban Consumers (CPI-U). Tax rates are never adjusted.",
                       c.cite(mo.cpi_src), " ",
                       h("a", {"href": page.rel("money/budgets/index.html#over-time")}, "Every government's budget over time"))
                     if mo.cpi else
                     h("p", None, "Comparing 2012 and 2026 fairly would mean restating older amounts with a price index. "
                                  "The guide doesn't have a sourced price index yet, so it doesn't offer inflation-adjusted "
                                  "figures (see Gaps)."),
                     scope="indiana", ed=ed))
    page.finish(gaps=money_gaps(ed, r"South Bend 2026|SBCSC|County spending|2027|zero totals|Mishawaka civil-city|Mishawaka utilities")
                + cpi_gaps(mo))
    return page


# =================================================================== hub

def build_hub(site):
    """The Money hub (phase 6 step 5, 2026-11-18): two doors, Government money and Campaign money, each with one line,
    its best entry points and a small ranked preview (figures the doors' pages already show, linking on), then the
    headline figures as a compact list. Ids facts, pages, gaps and sources are kept."""
    from . import money_browser as mb
    ed = site.ed
    mo = money(ed)
    page = site.page("money/index.html", banners=False, body_class="thing-page")
    c = page.cites

    def latest(series_id):
        s = mo.series.get(series_id)
        return s["rows"][-1] if s and s["rows"] else None

    page.add(h("header", {"class": "thing-head cb-head"},
               page.crumb_nav(),
               h("h1", {"class": "thing-title"}, "Money"),
               h("p", {"class": "thing-facts"},
                 "Two kinds of local money: what governments budget, tax and owe, and what candidates' campaigns "
                 "raise and spend. Every figure says how it was totaled.")))

    # ---- door 1: government money; preview = all advertised funds per resident (the Compare budgets ranking)
    tw_ids = ["county-st-joseph", "city-mishawaka"] + [m for m in mo.unit_ids if group_of(m) == "township"]
    pr_year = comparison_year(mo, ["county-st-joseph", "city-south-bend", "city-mishawaka"] + tw_ids,
                              ("general_fund", "advertised_all_funds"))
    got, src = per_resident_rows(mo, tw_ids, "advertised_all_funds", pr_year)
    got.sort(key=lambda t: -t[3])
    fmt = lambda v: f"${v:,.0f}"
    gov_rows = [dict(_gov_row(mo, page, mid, v, fmt(v), "budget", tip=_pop_tip(r, pop)), fmt=fmt)
                for mid, r, pop, v in got[:5]]
    gov_links = [("money/budgets/index.html", "Compare budgets", "per resident, tax rates, debt, the money map"),
                 ("money/your-tax-bill/index.html", "Your tax bill", "how one bill is split among the units that tax you"),
                 (gm.HUB, "Each government's Money tab", "budget over time, tax base, debt, money in and out"),
                 ("money/what-is-a-budget/index.html", "What counts as a budget", "why one budget can have several totals")]
    gov_door = h("section", {"class": "tsec mh-door", "id": "government", "aria-labelledby": "government-h"},
                 h("h2", {"class": "mh-door-h", "id": "government-h"},
                   h("a", {"href": page.rel("money/budgets/index.html")}, "Government money")),
                 h("p", {"class": "mh-door-d"}, "What each county, city, town, township, school corporation and special "
                                                "unit budgets, taxes and owes, from the state's files.", c.cite("MON-001")),
                 _door_links(page, gov_links),
                 rank_rows("mh-gov-preview", f"All advertised funds per resident, {pr_year}: the top 5", gov_rows,
                           subtitle="County, Mishawaka and the townships; the full list is on Compare budgets.",
                           status="computed", page=page, cite=c.cite(src), headers=["Government", "Per resident"],
                           word="Per resident") if gov_rows else None)

    # ---- door 2: campaign money; preview = the five offices with the most spending (the By office ranking)
    rows = mb._rank([r for r in mb.office_rows(ed) if not r["state"]])[:5]
    vmax = mb._scale(rows)
    camp_links = [(mb.INDEX, "By office",
                   "every office's money, linking to its Money tab and its Primary / General switch"),
                  (mb.BY_ELECTION, "By election", "every race of the 2026, 2024 and 2023 cycles on one scale"),
                  (mb.BY_CANDIDATE, "By candidate", "every candidate and committee, alphabetical"),
                  (cm_how(), "How campaign reporting works", "who files, what is public, how the guide adds it up")]
    camp_door = h("section", {"class": "tsec mh-door", "id": "campaign", "aria-labelledby": "campaign-h"},
                  h("h2", {"class": "mh-door-h", "id": "campaign-h"},
                    h("a", {"href": page.rel(mb.INDEX)}, "Campaign money")),
                  h("p", {"class": "mh-door-d"}, "What local candidates' committees reported raising and spending, "
                                                 "election by election; earlier mayoral races as news coverage "
                                                 "reported them. Money is not a measure of support."),
                  _door_links(page, camp_links),
                  mb._legend(),
                  mb.money_rows("mh-camp-preview", "The five offices whose candidates reported the most spending",
                                [mb._office_money_row(page, r) for r in rows], vmax=vmax, page=page,
                                subtitle="Latest election on file, all candidates, whole cycle; an incomplete total "
                                         "is a floor.",
                                status="computed", cite=c.cite("CFM-010"), headers=["Office", "Raised", "Spent"]))
    page.add(h("div", {"class": "cb-two mh-doors", "id": "pages"}, gov_door, camp_door))

    # ---- headline figures, as one compact list
    facts = []

    def fact(value, label, row_or_src, status):
        src = row_or_src if isinstance(row_or_src, str) else row_or_src["source_ids"]
        facts.append(h("li", {"class": "mh-fact"}, h("span", {"class": "mh-fact-v"}, value),
                       h("span", {"class": "mh-fact-l"}, label, c.cite(src), " ", T.status_mark(status, page))))

    n_units = len({r["unit_id"] for r in mo.budgets})
    fact(str(n_units), f"local units with budget figures in the guide, {mo.y0} to {mo.y1}", "MON-001", "computed")
    gf = latest("county-gateway-general-fund")
    af = latest("county-st-joseph-gateway-advertised-funds")
    if gf:
        fact(usd_short(gf["amount"]), f"St. Joseph County general fund, {gf['year']} adopted", gf, "official")
    if af:
        fact(usd_short(af["amount"]), f"St. Joseph County, all advertised funds, {af['year']} adopted", af, "computed")
    cb = latest("county-dlgf-certified-2026")
    if cb:
        fact(usd_short(cb["amount"]), f"St. Joseph County budget certified by the state, {cb['year']} (the funds in the "
                                      "state's budget order)", cb, "official")
    sb = latest("sb-gateway-general-fund")
    if sb:
        fact(usd_short(sb["amount"]), f"South Bend general fund, {sb['year']} adopted", sb, "official")
    mi = latest("city-mishawaka-gateway-advertised-funds")
    if mi:
        fact(usd_short(mi["amount"]), f"Mishawaka civil city, all advertised funds, {mi['year']} adopted (excludes "
                                      "utilities)", mi, "computed")
    cert = [r for r in mo.rates if r["unit_id"] == "county-st-joseph" and r["rate_kind"] == "certified_unit_rate"]
    cr = max(cert, key=lambda r: int(r["year"])) if cert else None
    if cr:
        fact(f"${float(cr['rate_per_100']):.4f}", f"county's own property-tax rate per $100 of assessed value, "
                                                   f"{cr['year']}, as certified by the state", cr, "official")
    cdt = debt_totals(mo, "county-st-joseph")
    cd = cdt[max(cdt)] if cdt else None
    if cd:
        # the stored caveat travels with the total (2026-11-18: the never-sum note on the 2024 and 2025 county totals)
        caveat = debt_note_text(cd.get("notes") or "")
        fact(usd_short(cd["amount"]), f"county debt outstanding, end of {cd['year']}" + (f". {caveat}" if caveat else ""),
             cd, "computed")
    fact(str(len(mo.jumps)), "year-over-year budget changes over 40% with no recorded explanation, flagged on each "
                             "government's charts", "MON-001", "computed")
    page.add(T.tab_section("facts", "Headline figures", h("ul", {"class": "mh-facts"}, facts),
                           lead=h("span", None, "Budget totals depend on which funds are counted; ",
                                  h("a", {"href": page.rel("money/what-is-a-budget/index.html")}, "read the primer"),
                                  " before comparing them. Learning path: ",
                                  h("a", {"href": page.rel("money/what-is-a-budget/index.html#path-follow-the-money-1")},
                                    "Follow the money"), ", five stops.")))
    # a source the hub no longer cites (2026-11-18: MON-004, the 2024 debt file; the debt fact now gives the latest
    # year) keeps its #src-<id> link: it lands on the sources index, which lists every source
    page.add(mb.moved_anchors_script({"a": {"pages-h": "#pages"}, "p": {"src-": page.rel("about/sources/index.html")}}))
    page.finish(gaps=money_gaps(ed, r"South Bend 2026|tax-district|assessed|Circuit|Debt before") + cpi_gaps(mo),
                gaps_intro="The largest gaps in the money data. Each money page lists the gaps that affect it.")
    return page


def cm_how() -> str:
    from civic.campaign_money import HOW_PAGE
    return HOW_PAGE


def _door_links(page, links) -> Markup:
    return h("ul", {"class": "mh-links"},
             [h("li", None, h("a", {"href": page.rel(p)}, t), h("span", {"class": "mh-link-d"}, d))
              for p, t, d in links if p.split("#")[0] in page.site.by_path])


PAGES = {
    "money/index.html": build_hub,
    "money/what-is-a-budget/index.html": build_primer,
    "money/your-tax-bill/index.html": build_tax_bill,
    "money/budgets/index.html": build_budgets,
}
