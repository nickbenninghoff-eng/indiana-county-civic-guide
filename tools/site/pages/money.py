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

from civic.charts import _svg, _txt, bar_path, figure, fmt_tick, hbar, line, nice_ticks, text_w
from civic.components import callout, data_table, scope_badge, section, status_badge, variant_slot
from civic.data import fmt_date, split_ids
from civic.html import Markup, h, join, json_script
from civic.layers import build_layers

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

# money ids with a units.csv row that derived/unit_id_aliases.csv doesn't map yet
EXTRA_UNIT_IDS = {"school-new-prairie": "new-prairie"}

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
    def label(self, mid: str) -> str:
        uid = self.ed.unit_alias(mid)
        if uid and uid in self.ed.units:
            return self.ed.units[uid]["name"]
        return GATEWAY_LABELS.get(mid, mid)

    def anchor(self, mid: str) -> str:
        return self.ed.unit_alias(mid) or mid

    def has_budget(self, mid: str) -> bool:
        return any(s["unit"] == mid for s in self.series.values())

    def in_units_csv(self, mid: str) -> bool:
        return bool(self.ed.unit_alias(mid))

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
    """Column chart for one budget basis. Like charts.columns, plus per-point marks, a legend,
    and flags: {index: text} draws a marker above the column ('unexplained change; see Gaps')."""
    flags = flags or {}
    vals = [p["value"] for p in points if p.get("value") is not None]
    vmax = max(vals) if vals else 1
    ticks = nice_ticks(vmax)
    top = ticks[-1]
    axis_w = max(text_w(fmt_tick(t, top, True), mono=True) for t in ticks) + 10
    n = max(len(points), 1)
    W = max(360, min(760, axis_w + n * 36 + 16))
    plot_l, plot_r, plot_t, plot_b = axis_w, W - 8, 34, 230
    H = plot_b + 30
    band = (plot_r - plot_l) / n
    cw = min(24, band * 0.62)
    y = lambda v: plot_b - (plot_b - plot_t) * (v / top)
    grid = [h("line", {"x1": plot_l, "x2": plot_r, "y1": f"{y(t):.1f}", "y2": f"{y(t):.1f}", "class": "grid" if t else "axis"}) for t in ticks]
    tl = [_txt(plot_l - 6, y(t) + 4, fmt_tick(t, top, True), "ct ct-axis", "end") for t in ticks]
    every = max(1, math.ceil(n / ((plot_r - plot_l) / 34)))
    labelled = set()
    if vals:
        idx = [i for i, p in enumerate(points) if p.get("value") is not None]
        last, peak = idx[-1], max(idx, key=lambda i: points[i]["value"])
        labelled = {last, peak} - set(flags)
        if peak != last and {peak, last} <= labelled:
            # two direct labels on nearby columns collide; keep the latest value only
            def _lw(i):
                return text_w(points[i].get("display") or usd_short(points[i]["value"]), mono=True)
            if abs(last - peak) * band < (_lw(last) + _lw(peak)) / 2 + 6:
                labelled.discard(peak)
    marks = []
    for i, p in enumerate(points):
        cx = plot_l + band * i + band / 2
        xl = _txt(cx, plot_b + 16, p["x"], "ct ct-axis", "middle") if (i % every == 0 or i == n - 1) else None
        if p.get("value") is None:
            marks.append(h("g", None, xl))
            continue
        disp = p.get("display") or usd_short(p["value"])
        y0 = y(p["value"])
        tipl = p.get("tip") or str(p["x"])
        if i in flags:
            tipl += " · " + flags[i]
        g = [h("rect", {"class": "hit", "x": f"{cx - band / 2:.1f}", "y": plot_t, "width": f"{band:.1f}", "height": plot_b - plot_t}),
             h("path", {"class": f"bar {p.get('mark', 'm-accent')}", "d": bar_path(cx - cw / 2, min(y0, plot_b - 1), cx + cw / 2, plot_b, "up")}),
             _txt(cx, y0 - 6, disp, "ct ct-val", "middle") if i in labelled else None, xl]
        if i in flags:
            fy = plot_t - 16
            g.append(h("line", {"class": "mn-flag-line", "x1": f"{cx:.1f}", "x2": f"{cx:.1f}", "y1": f"{fy + 6:.1f}", "y2": f"{y0 - 2:.1f}"}))
            g.append(h("path", {"class": "mn-flag", "d": f"M{cx:.1f},{fy - 6:.1f}L{cx + 6:.1f},{fy:.1f}L{cx:.1f},{fy + 6:.1f}L{cx - 6:.1f},{fy:.1f}Z"}))
            g.append(_txt(cx, fy + 3.5, "!", "ct mn-flag-t", "middle"))
        marks.append(h("g", {"class": "mark", "tabindex": "0", "data-tv": disp, "data-tl": tipl}, g))
    brk = []
    for b in breaks or []:
        bx = plot_l + band * (b["after"] + 1)
        right = bx + 4 + text_w(b["label"], 10.5) < plot_r
        brk.append(h("g", {"class": "mark break", "tabindex": "0", "data-tv": b["label"], "data-tl": b.get("tip", "")},
                     h("rect", {"class": "hit", "x": f"{bx - 8:.1f}", "y": plot_t - 30, "width": 16, "height": plot_b - plot_t + 30}),
                     h("line", {"class": "break-line mn-break", "x1": f"{bx:.1f}", "x2": f"{bx:.1f}", "y1": plot_t - 28, "y2": plot_b}),
                     _txt(bx + 4 if right else bx - 4, plot_t - 20, b["label"], "ct ct-muted ct-small", "start" if right else "end")))
    svg = _svg(W, H, f"{title}. Column chart; values in the table view.", grid, tl, marks, brk)
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
    return figure(fid, title, subtitle, svg, ["Year", "Amount", "Status", "Note"], rows, note=note, numeric=(1,),
                  status=status, page=page, legend=leg, kind="columns", cite=cite)


# =================================================================== budgets page

def _unit_charts(mo: Money, page, mid: str, gap_flags: dict) -> tuple[list, list]:
    """Charts for one unit (one per basis) and table rows for figures kept out of the charts."""
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
        common = None
        for s in primary:
            notes = [r["notes"] for r in s["rows"]]
            first = sentences(notes[0])[:1] if notes else []
            common = first[0] if first and all(n.startswith(first[0]) for n in notes) else None
        points, flags = [], {}
        for i, yv in enumerate(years):
            if yv not in by_year:
                points.append({"x": yv, "value": None})
                continue
            s, r, secondary = by_year[yv]
            extra = r["notes"][len(common):].strip() if common and r["notes"].startswith(common) else r["notes"]
            extra = clean_note(extra)
            points.append({"x": yv, "value": float(r["amount"]), "status": r["status"],
                           "mark": "m-ink" if secondary else "m-accent",
                           "tip": f"{yv} · {'news report (secondary)' if secondary else BASIS[basis][0]}",
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
            legend_items = [("m-accent", "Gateway (state budget file), adopted"),
                            ("m-ink", "News report, rounded (secondary)")]
        status = "official" if all(s["status"] == ["official"] for s in primary) else "computed"
        name = mo.label(mid)
        title = f"{name}: {BASIS[basis][0].lower()}, adopted" if basis != "gateway_reported_funds" else f"{name}: {BASIS[basis][0]}"
        n_years = len([p for p in points if p.get("value") is not None])
        sub = f"{BASIS[basis][1]} {n_years} years with figures, {years[0]} to {years[-1]}. Nominal dollars."
        note_parts = []
        if common:
            note_parts.append(h("span", None, common, " "))
        note_parts += break_notes
        src = union_sources(r for s in in_chart for r in s["rows"])
        fid = f"bud-{mid}-{basis.replace('_', '-')}"
        nominal = flag_columns(fid, title, points, subtitle=sub, breaks=breaks,
                               flags=flags, legend_items=legend_items, note=join(note_parts, " ") if note_parts else None,
                               status=status, page=page, cite=c.cite(src))
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
                            status="computed", page=page, cite=c.cite(src + ";" + mo.cpi_src))
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


def _series_charted(s, unit_series) -> bool:
    """True when a secondary series was drawn as a continuation on a chart (see _unit_charts)."""
    group = [x for x in unit_series if x["basis"] == s["basis"]]
    primary = [x for x in group if "adopted" in x["kinds"] and set(x["status"]) <= {"official", "computed"}]
    if not primary:
        return False
    prim_years = {int(r["year"]) for x in primary for r in x["rows"]}
    sy = {int(r["year"]) for r in s["rows"]}
    return len(sy) > 1 and not (sy & prim_years) and s["kinds"] == ["adopted"] and any(x["breaks"] for x in primary)


def build_budgets(site):
    ed = site.ed
    mo = money(ed)
    page = site.page("money/budgets/index.html", banners=False)
    c = page.cites
    toc = [("over-time", "Budgets over time"), ("per-resident", "Per resident"), ("breakdowns", "2024 spending and revenue"),
           ("debt", "Debt"), ("tax-base", "How the tax base shapes budgets"), ("gaps", "Gaps"), ("sources", "Sources")]
    n_units = len({r["unit_id"] for r in mo.budgets})
    page.add(hero(page, "Reference · Money", page.title,
                  h("span", None, f"Adopted budgets for {n_units} local units in {ed.county_label}, {mo.y0} to {mo.y1}, "
                                  "from the state's budget file. Each chart uses one way of totaling a budget, and changes "
                                  "in how a unit reports are drawn on the chart.", c.cite("MON-001"), " ",
                    status_badge("computed", page, "Totals are sums of fund lines; per-resident figures divide by Census estimates.")),
                  toc, [scope_badge("county", ed), " ", h("a", {"href": page.rel("money/what-is-a-budget/index.html")},
                                                          "What counts as a budget?")]))

    # ------------------------------------------------------------------ 1 over time
    n_flags = len(mo.jumps)
    nav = []
    for g, glabel in GROUPS:
        ids = [m for m in mo.unit_ids if group_of(m) == g and (mo.has_budget(m) or mo.in_units_csv(m))]
        if ids:
            nav.append(h("li", None, h("span", {"class": "mn-unitnav-h mono"}, glabel),
                         h("span", {"class": "mn-unitnav-links"},
                           join([h("a", {"href": f"#{mo.anchor(m)}"}, mo.label(m)) for m in ids], " · "))))
    blocks, nodata_gaps = [], []
    for g, glabel in GROUPS:
        ids = [m for m in mo.unit_ids if group_of(m) == g and (mo.has_budget(m) or mo.in_units_csv(m))]
        if not ids:
            continue
        blocks.append(h("h3", {"class": "mn-group-h"}, glabel))
        for mid in ids:
            charts, others = _unit_charts(mo, page, mid, {})
            if not mo.has_budget(mid):
                nodata_gaps.append({"item": f"{mo.label(mid)}: budget figures",
                                    "why_missing": "The guide's budget file has no adopted budget rows for this unit "
                                                   "(the state budget download used for the guide has none for it).",
                                    "how_to_fill": "Check the unit's Gateway budget pages, or its own budget documents."})
            anchor = mo.anchor(mid)
            alias = h("span", {"id": mid, "class": "mn-alias"}) if anchor != mid else None
            uid = ed.unit_alias(mid)
            place_link = None
            for path in (f"places/{uid}/index.html",) if uid else ():
                if path in site.by_path:
                    place_link = h("a", {"href": page.rel(path)}, "Place page")
            if mid == "county-st-joseph":
                place_link = h("a", {"href": page.rel("county/index.html")}, "County government page")
            head_bits = [h("h4", {"class": "mn-unit-h"}, mo.label(mid))]
            if not mo.in_units_csv(mid):
                head_bits.append(h("p", {"class": "mn-unit-note"},
                                   "Named as in the state budget file. This unit has no entry in the guide's list of governments yet."))
            if place_link:
                head_bits.append(h("p", {"class": "mn-unit-note"}, place_link))
            other_tbl = None
            if others:
                orow = []
                for s, r in sorted(others, key=lambda t: (t[1]["year"], t[0]["id"])):
                    orow.append([r["year"], usd(r["amount"]), BASIS.get(r["basis"], (r["basis"],))[0],
                                 r["adopted_or_actual"], h("span", None, status_badge(r["status"], page), c.cite(r["source_ids"])),
                                 clean_note(r["notes"])])
                other_tbl = h("div", {"class": "mn-others"},
                              h("p", {"class": "mn-others-h"}, "Other reported figures, not charted (different scope, proposed, or one news report):"),
                              data_table(f"other-{mid}", ["Year", "Amount", "Basis", "Kind", "Status", "Note"], orow,
                                         caption=f"{mo.label(mid)}: other reported budget figures", numeric=(1,), min_width="48rem"))
            blocks.append(h("article", {"class": "mn-unit", "id": anchor, "aria-label": mo.label(mid)},
                            alias, h("header", {"class": "mn-unit-head"}, head_bits),
                            h("div", {"class": "chart-grid"}, charts) if charts else
                            h("p", {"class": "mn-nodata"}, "No budget data for this unit in the guide's data."
                              if not mo.has_budget(mid) else "No adopted multi-year series for this unit in the guide's data."),
                            other_tbl))
    page.add(section("over-time", 1, "Budgets over time",
                     h("p", None, "Each unit's adopted budget for every year the state file has it. A chart never mixes two ways "
                                  "of totaling a budget. Where a unit changed how it reports, the chart shows a break line, and "
                                  "the years on either side should not be compared.", c.cite("MON-001;MON-023")),
                     h("p", None, f"The guide's year-over-year check found {n_flags} changes of more than 40% from one year "
                                  "to the next that no recorded change in reporting explains. They are marked on the charts "
                                  "with ", h("span", {"class": "mn-flag-key", "aria-hidden": "true"}, "!"),
                       " and listed under ", h("a", {"href": "#gaps"}, "Gaps"), ". They are shown as reported, not smoothed. ",
                       status_badge("computed", page, "Flags come from the guide's own year-over-year comparison.")),
                     h("p", {"class": "muted"}, "Amounts are shown in nominal dollars (the dollars of each year) unless you "
                                                "switch to constant dollars below. Years with no usable total in the state file "
                                                "are left empty."),
                     _dollars_toggle(mo, page),
                     h("ul", {"class": "mn-unitnav", "aria-label": "Jump to a unit"}, nav),
                     blocks, scope="county", ed=ed))

    # ------------------------------------------------------------------ 2 per resident
    def per_res_rows(ids, basis):
        rows, srcs = [], []
        for mid in ids:
            s = next((s for s in mo.series.values() if s["unit"] == mid and s["basis"] == basis
                      and s["status"] in (["official"], ["computed"]) and s["kinds"] == ["adopted"]), None)
            pop = mo.population(mid)
            if not s or not pop:
                continue
            r = next((r for r in s["rows"] if int(r["year"]) == mo.y1), None)
            if not r:
                continue
            v = float(r["amount"]) / float(pop["value"])
            rows.append({"label": re.sub(r" \(state data: .*\)$", "", mo.label(mid)), "value": v, "display": f"${v:,.0f}",
                         "tip": f"{usd(r['amount'])} / {int(float(pop['value'])):,} residents"
                                + (f" (MOE ±{int(float(pop['moe'])):,})" if pop.get("moe") else "")})
            srcs += [r, pop]
        return rows, union_sources(srcs)
    gf_rows, gf_src = per_res_rows(["county-st-joseph", "city-south-bend", "city-mishawaka"], "general_fund")
    tw_ids = ["county-st-joseph", "city-mishawaka"] + [m for m in mo.unit_ids if group_of(m) == "township"]
    af_rows, af_src = per_res_rows(tw_ids, "advertised_all_funds")
    pop_note = ("Computed: the adopted amount divided by the Census Bureau's American Community Survey 2020-2024 5-year "
                "population estimate. The estimate is a five-year average, so per-resident figures are approximate.")
    page.add(section("per-resident", 2, f"Comparing units: {mo.y1} budgets per resident",
                     h("p", None, "Units differ in size, so totals alone don't compare well. These charts divide each unit's "
                                  f"{mo.y1} adopted budget by its population. Each chart uses one basis."),
                     h("div", {"class": "chart-grid"},
                       hbar("perres-gf", f"General fund per resident, {mo.y1}", gf_rows, subtitle="County and the two cities",
                            money=True, value_fmt=lambda v: f"${v:,.0f}", status="computed", page=page,
                            note=pop_note + " The county's figure is divided by the whole county's population, which includes city residents.",
                            headers=["Unit", "Per resident"], cite=c.cite(gf_src)),
                       hbar("perres-af", f"All advertised funds per resident, {mo.y1}", af_rows,
                            subtitle="County, Mishawaka (civil city) and the townships", money=True,
                            value_fmt=lambda v: f"${v:,.0f}", status="computed", page=page,
                            note=pop_note + " Township populations include residents of cities and towns inside the township. "
                                            "South Bend is left out: from 2024 the state file lists only 10 of its funds.",
                            headers=["Unit", "Per resident"], cite=c.cite(af_src))),
                     scope="county", ed=ed))

    # ------------------------------------------------------------------ 3 breakdowns
    page.add(section("breakdowns", 3, "2024 spending and revenue: county, South Bend, Mishawaka",
                     h("p", None, "What each government actually spent and received in 2024, from the annual financial reports "
                                  "units file with the state. These files have their own scope: each chart's note says what it "
                                  "covers. They are not the same as the budget totals above.", c.cite("MON-002;MON-003")),
                     [_breakdown_block(mo, page, mid) for mid in ("county-st-joseph", "city-south-bend", "city-mishawaka")],
                     _other_breakdowns(mo, page),
                     scope="county", ed=ed))

    # ------------------------------------------------------------------ 4 debt
    tot = [r for r in mo.debt if r["debt_type"].startswith("Total end-of-year principal")]
    drows = [{"label": re.sub(r" \(state data: .*\)$", "", mo.label(r["unit_id"])), "value": float(r["amount"]),
              "display": usd_short(r["amount"]), "tip": f"{usd(r['amount'])} at the end of {r['year']}"}
             for r in sorted(tot, key=lambda r: mo.unit_ids.index(r["unit_id"]))]
    cls_rows = []
    for r in sorted(mo.debt, key=lambda r: (mo.unit_ids.index(r["unit_id"]), r["year"], r["debt_type"])):
        cls_rows.append([mo.label(r["unit_id"]), r["year"], r["debt_type"], usd(r["amount"]),
                         h("span", None, status_badge(r["status"], page), c.cite(r["source_ids"])), r["notes"]])
    sb_city = next((r for r in mo.debt if r["unit_id"] == "city-south-bend" and r["year"] != "2024"), None)
    page.add(section("debt", 4, "Debt",
                     h("p", None, f"Principal still owed at the end of 2024, as each unit reported it to the state. "
                                  f"{len(tot)} units report debt in the file. Totals include utility debt where a unit has utilities.",
                       c.cite("MON-004")),
                     hbar("debt-2024", "Debt outstanding, end of 2024", drows, subtitle="Total principal, all debt classes",
                          money=True, value_fmt=usd_short, status="computed", page=page, headers=["Unit", "Principal"],
                          note="Computed: the sum of each unit's debt-class rows in the state's 2024 annual financial report "
                               "debt file. Units in the order used across the guide (county, cities, towns, townships, schools, "
                               "libraries, special units).", cite=c.cite("MON-004")),
                     h("p", None, f"South Bend's own budget page gave a different, later figure: roughly "
                                  f"{usd_short(sb_city['amount'])} outstanding as of {fmt_date(sb_city['year'] if False else '2026-09-04')}. "
                                  "It is a different date and source, so it is not on the chart.",
                       c.cite(sb_city["source_ids"]), " ", status_badge(sb_city["status"], page)) if sb_city else None,
                     data_table("debt-classes", ["Unit", "Year", "Debt type", "Amount", "Status", "Note"], cls_rows,
                                caption="Debt by class and unit", numeric=(3,), min_width="54rem"),
                     scope="county", ed=ed))

    # ------------------------------------------------------------------ 5 tax base
    page.add(_tax_base(mo, page))

    gaps = mo.jump_gap_rows() + nodata_gaps + money_gaps(ed) + cpi_gaps(mo)
    page.finish(gaps=gaps, gaps_intro=("What the guide looked for and hasn't found or confirmed yet. The first "
                                       f"{len(mo.jumps)} items are the year-over-year changes flagged on the charts."))
    return page


def _scope_note(rows) -> str:
    """Sentences every row's note shares (the file's scope statement)."""
    lists = [sentences(r["notes"]) for r in rows]
    if not lists:
        return ""
    common = [s for s in lists[0] if all(s in l for l in lists[1:])]
    return " ".join(common)


def _breakdown_block(mo: Money, page, mid: str) -> Markup:
    c = page.cites
    out = [h("h3", None, mo.label(mid).replace(" (civil city)", ""))]
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
    out.append(h("div", {"class": "chart-grid"}, figs))
    out += tables
    return h("div", {"class": "mn-breakdown", "id": f"breakdown-{mo.anchor(mid)}"}, out)


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
                        h("p", {"class": "mn-others-h"}, f"{mo.label(mid)}, {year} ({rows[0]['kind']}): ", rows[0]["notes"]),
                        data_table(f"obrk-{mid}-{basis.replace('_', '-')}", ["Category", "Amount", "Status"], trows,
                                   caption=f"{mo.label(mid)} {year}: {basis.replace('_', ' ')} (rows total {usd(total)})",
                                   numeric=(1,), min_width="30rem")))
    return h("div", None, h("h3", None, "Other breakdowns in the guide's data"),
             h("p", {"class": "muted"}, "Proposed figures, a later budget year, and news-reported department amounts. "
                                        "Shown as tables because each has a different scope from the 2024 actuals."),
             blocks)


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
    return section("tax-base", 5, "How the tax base shapes budgets",
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
                        subtitle=f"County and the two cities' civil governments, {mo.y0} to {mo.y1}",
                        value_fmt=lambda v: f"${v:.2f}", status="computed", page=page,
                        note=h("span", None, "Computed: the sum of the adopted net tax rate of every fund the unit levies. "
                                             "This is not the rate on a tax bill: the rates of overlapping units (township, "
                                             "school, library) are not added. ",
                               f"Changes of more than 40% with no reason found in the state data: {flag_txt}." if flag_txt else ""),
                        cite=c.cite("MON-001")),
                   h("p", None, "General property taxes received in 2024, from the annual financial report receipts:"),
                   data_table("ptax-2024", ["Unit", "General property taxes, 2024", "Status"], prow,
                              caption="Property-tax receipts, 2024 actual", numeric=(1,)),
                   h("p", None, "The guide does not yet have reliable assessed values by unit, or the dollar amount of "
                                "tax-cap credits each unit loses (see Gaps). See ",
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
                      "uid": ed.unit_alias(mid) or EXTRA_UNIT_IDS.get(mid, ""), "cert": cert, "adopted": adop}
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
                                                     "found yet. See ", h("a", {"href": page.rel("county/index.html#structure")},
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
                       h("a", {"href": page.rel("money/budgets/index.html#south-bend")}, "South Bend budgets"), "."),
                     scope="county", ed=ed))

    page.add(section("dollars", 7, "Nominal and constant dollars",
                     h("p", None, "Unless a chart says otherwise, every dollar figure in the guide is nominal: the amount in that "
                                  "year's dollars, as the government reported it.", c.cite("MON-024")),
                     h("p", None, "Comparing 2012 and 2026 fairly means restating older amounts with a price index. "
                                  f"The budget charts on the Budgets page can switch to constant {mo.cpi_base} dollars, using the "
                                  "national Consumer Price Index for All Urban Consumers (CPI-U). Tax rates are never adjusted.",
                       c.cite(mo.cpi_src), " ",
                       h("a", {"href": page.rel("money/budgets/index.html#over-time")}, "Budgets over time"))
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
    ed = site.ed
    mo = money(ed)
    page = site.page("money/index.html", banners=False)
    c = page.cites

    def latest(series_id):
        s = mo.series.get(series_id)
        return s["rows"][-1] if s and s["rows"] else None

    facts = []

    def fact(value, label, row_or_src, status):
        src = row_or_src if isinstance(row_or_src, str) else row_or_src["source_ids"]
        facts.append(h("div", {"class": "mn-fact"},
                       h("p", {"class": "mn-fact-v mono"}, value),
                       h("p", {"class": "mn-fact-l"}, label, c.cite(src)),
                       h("p", {"class": "mn-fact-b"}, status_badge(status, page))))

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
        fact(usd_short(cb["amount"]), f"St. Joseph County budget certified by the state, {cb['year']} (the funds in the state's "
                                      "budget order)", cb, "official")
    sb = latest("sb-gateway-general-fund")
    if sb:
        fact(usd_short(sb["amount"]), f"South Bend general fund, {sb['year']} adopted", sb, "official")
    mi = latest("city-mishawaka-gateway-advertised-funds")
    if mi:
        fact(usd_short(mi["amount"]), f"Mishawaka civil city, all advertised funds, {mi['year']} adopted (excludes utilities)", mi, "computed")
    cert = [r for r in mo.rates if r["unit_id"] == "county-st-joseph" and r["rate_kind"] == "certified_unit_rate"]
    cr = max(cert, key=lambda r: int(r["year"])) if cert else None
    if cr:
        fact(f"${float(cr['rate_per_100']):.4f}", f"county's own property-tax rate per $100 of assessed value, {cr['year']}, "
                                                   "as certified by the state", cr, "official")
    cd = next((r for r in mo.debt if r["unit_id"] == "county-st-joseph" and r["debt_type"].startswith("Total end-of-year")), None)
    if cd:
        fact(usd_short(cd["amount"]), f"county debt outstanding, end of {cd['year']}", cd, "computed")
    fact(str(len(mo.jumps)), "year-over-year budget changes over 40% with no recorded explanation, flagged on the charts",
         "MON-001", "computed")

    cards = [("money/what-is-a-budget/index.html", "What counts as a budget",
              "General fund, all funds, adopted and actual: why one budget can have several totals."),
             ("money/your-tax-bill/index.html", "Your tax bill",
              "Pick a taxing district to see its certified tax rate and how it is shared among the units that levy it."),
             ("money/budgets/index.html", "Budgets by unit",
              f"Every unit's adopted budget, {mo.y0} to {mo.y1}, plus 2024 spending, revenue and debt."),
             ("money/campaigns/index.html", "Campaign finance",
              "How campaign-finance reporting works and what is public.")]
    toc = [("facts", "Headline figures"), ("pages", "Money pages"), ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(hero(page, "Reference · Money", page.title,
                  h("span", None, "Where local money comes from and where it goes: budgets for every unit, how a property-tax "
                                  "bill is split, and debt. Every figure says how it was totaled.", c.cite("MON-001")),
                  toc, [scope_badge("county", ed), " ", scope_badge("indiana", ed)]))
    page.add(section("facts", 1, "Headline figures",
                     h("p", {"class": "muted"}, "Computed from the guide's money data. Budget totals depend on which funds are "
                                                "counted; ", h("a", {"href": page.rel("money/what-is-a-budget/index.html")},
                                                               "read the primer"), " before comparing them."),
                     h("div", {"class": "mn-facts"}, facts), scope="county", ed=ed))
    page.add(section("pages", 2, "Money pages",
                     h("div", {"class": "card-grid"},
                       [h("article", {"class": "card"}, h("h3", {"class": "card-title"}, h("a", {"href": page.rel(p)}, t)),
                          h("p", None, d)) for p, t, d in cards]),
                     h("p", None, "Learning path: ", h("a", {"href": page.rel("money/what-is-a-budget/index.html#path-follow-the-money-1")},
                                                       "Follow the money"), ", five stops, about 35 minutes.")))
    page.finish(gaps=money_gaps(ed, r"South Bend 2026|tax-district|assessed|Circuit|Debt before") + cpi_gaps(mo),
                gaps_intro="The largest gaps in the money data. Each money page lists the gaps that affect it.")
    return page


PAGES = {
    "money/index.html": build_hub,
    "money/what-is-a-budget/index.html": build_primer,
    "money/your-tax-bill/index.html": build_tax_bill,
    "money/budgets/index.html": build_budgets,
}
