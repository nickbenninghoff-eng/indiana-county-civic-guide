"""Community (social and economic context) and History pages.

community/index.html                      hub + fixed indicators vs Indiana and U.S.
community/people/index.html               population over time, age, race/ethnicity, foreign-born
community/income-and-work/index.html      income, poverty, unemployment, jobs by industry, employers
community/housing-and-education/index.html tenure, values, rents, rent burden, attainment
community/research-on-voting/index.html   attributed published analyses only + ecological-fallacy callout
history/index.html                        party-control timelines, mayors, turning points, population
history/people/index.html                 people who shaped local government (rule-based cards)

Framing rules (planning/ux-review.md 3.5 and 6): demographics are never placed next to or
overlaid on election results; comparisons are to Indiana and the U.S. only; Census category
names are verbatim; every ACS estimate shows its MOE and vintage, and estimates with a
coefficient of variation above 30% are greyed and never used in headings or charts.
"""
from __future__ import annotations

import re
from collections import Counter, OrderedDict

from civic.charts import (_svg, _txt, bar_path, columns, figure, hbar, legend, line,
                          party_mark, party_timeline)
from civic.components import (callout, data_table, entity_list, name_with_party, party_label, section, see_all_fold, see_all_table, status_badge)
from civic.data import PARTY_LABELS, SELECTED_BY_LABELS, fmt_date, parse_date, split_ids
from civic.html import Markup, h, join, json_script
from civic.pick_one import one_bar
from civic.preselect import here_slot
from civic.map import LAYERS, TYPE_LABEL, embedded_map, load_shapes, shade_defs
from civic.shading import classify, shade_class, shade_legend

CV_LIMIT = 0.30            # display rule in data/indiana/indicators.csv
Z90 = 1.645                # ACS MOEs are published at 90% confidence

MONEY = {"median_hh_income", "per_capita_income", "median_home_value", "median_gross_rent"}
COUNTS = {"pop_total", "emp_ind_employed_total"}

RACE_IDS = ["race_white_nh_pct", "race_black_nh_pct", "race_aian_nh_pct", "race_asian_nh_pct",
            "race_nhpi_nh_pct", "race_other_nh_pct", "race_two_or_more_nh_pct", "race_hispanic_pct"]
EMP_IDS = ["emp_ind_agri_mining_pct", "emp_ind_construction_pct", "emp_ind_manufacturing_pct",
           "emp_ind_wholesale_pct", "emp_ind_retail_pct", "emp_ind_transport_utilities_pct",
           "emp_ind_information_pct", "emp_ind_finance_real_estate_pct", "emp_ind_professional_admin_pct",
           "emp_ind_education_health_pct", "emp_ind_arts_food_accom_pct", "emp_ind_other_services_pct",
           "emp_ind_public_admin_pct"]
QCEW_OWN = ["qcew_jobs_all_ownerships", "qcew_jobs_private", "qcew_jobs_federal_gov",
            "qcew_jobs_state_gov", "qcew_jobs_local_gov"]

# The fixed context set from ux-review 3.5 (same indicators for every unit).
CONTEXT_IDS = ["pop_total", "median_hh_income", "poverty_pct", "owner_occupied_pct", "bachelors_plus_pct"]

CATEGORY_LABELS = OrderedDict([("political", "Political"), ("government", "Government"), ("legal", "Legal"),
                               ("economic", "Economic"), ("population", "Population")])

CRITERIA = OrderedDict([
    ("TENURE", "Held elected seats in one government (St. Joseph County, one city, or the Indiana General Assembly) "
               "for 16 or more years in total. Years are counted as the last year minus the first year of each "
               "documented term, with overlapping terms counted once; a term still running counts to 2026."),
    ("FIRST", "Is documented, with a source, as the first person to hold an office or the first of a group to hold it."),
    ("HIGHER", "Held a statewide Indiana office or a federal office, elected or appointed, as documented in the sources."),
    ("FAMILY", "Two or more members of the same family held elected office here, as documented in the sources."),
    ("TURNING_POINT", "Is named in the title of a political, government or legal event in the guide's sourced "
                      "timeline of turning points (History, section 3)."),
])
# TENURE, HIGHER and TURNING_POINT are computed by the build from the office, term and timeline data. FIRST and
# FAMILY are facts about a person that only a source can establish, so they are taken from people.csv as recorded
# from the cited sources.
COMPUTED_RULES = ("TENURE", "HIGHER", "TURNING_POINT")
# Sources about news-reported allegations (not official findings). The guide shows only official
# findings (people.csv documented_findings, attributed), so these are never cited or rendered.
EXCLUDED_PEOPLE_SOURCES = {"PPL-033"}
ALLEGATION_RE = re.compile(r"allegation|alleged|complaint|harass", re.I)


def _people_sources(p) -> str:
    return ";".join(s for s in split_ids(p.get("source_ids")) if s not in EXCLUDED_PEOPLE_SOURCES)


def _safe_note(p) -> str:
    """people.csv notes are shown only in the low-confidence table, and never when they describe
    news-reported allegations."""
    n = p.get("notes") or ""
    return "" if ALLEGATION_RE.search(n) else n


CRITERIA_LABELS = {"TENURE": "Tenure", "FIRST": "First", "HIGHER": "Higher office", "FAMILY": "Family",
                   "TURNING_POINT": "Turning point"}


# =============================================================================== data helpers

def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _union(rows) -> str:
    seen = []
    for r in rows:
        if not r:
            continue
        for s in split_ids(r.get("source_ids")):
            if s not in seen:
                seen.append(s)
    return ";".join(seen)


class IV:
    """Index over indicator_values.csv and indicators.csv."""

    def __init__(self, ed):
        self.ed = ed
        self.rows = ed.table("indicator_values")
        self.defs = {r["indicator_id"]: r for r in ed.table("indicators")}
        self.idx = {}
        for r in self.rows:
            self.idx[(r["geo_id"], r["indicator_id"], r["vintage"])] = r
        geos = OrderedDict()
        for r in self.rows:
            geos.setdefault(r["geo_id"], r)
        self.geo = {g: r for g, r in geos.items()}
        by_type = {}
        for g, r in geos.items():
            by_type.setdefault(r["geo_type"], []).append(g)
        name = lambda g: self.geo[g]["geo_name"]
        self.county = (by_type.get("county") or [None])[0]
        self.places = sorted(by_type.get("place", []), key=name)
        self.townships = sorted(by_type.get("county_subdivision", []), key=name)
        self.state = (by_type.get("state") or [None])[0]
        self.nation = (by_type.get("nation") or [None])[0]
        acs = sorted({r["vintage"] for r in self.rows if r["vintage"].startswith("ACS ")},
                     key=lambda v: [int(x) for x in re.findall(r"\d{4}", v)])
        self.acs_then = acs[0] if acs else None
        self.acs_now = acs[-1] if acs else None

    def get(self, geo, ind, vintage):
        return self.idx.get((geo, ind, vintage))

    def label(self, ind):
        return self.defs.get(ind, {}).get("label", ind)

    def short_name(self, geo):
        r = self.geo.get(geo)
        if not r:
            return geo
        n = r["geo_name"]
        t = r["geo_type"]
        if t == "county":
            return n.split(",")[0]
        if t == "place":
            return re.sub(r"\s+(city|town)$", "", n.split(",")[0])
        if t == "county_subdivision":
            return n.split(",")[0].replace(" township", " Township")
        return n

    def series(self, geo, ind, prefix):
        """[(year, row)] for vintages like 'BLS LAUS annual average 2009' or 'QCEW 2001 annual'."""
        out = []
        for r in self.rows:
            if r["geo_id"] == geo and r["indicator_id"] == ind and r["vintage"].startswith(prefix):
                m = re.search(r"(\d{4})", r["vintage"])
                if m:
                    out.append((int(m.group(1)), r))
        out.sort(key=lambda t: t[0])
        return out


def cv_of(row):
    """Coefficient of variation (0-1) or None when no MOE is published. A zero estimate with a
    nonzero MOE has no defined CV and is treated as unreliable."""
    v, m = _f(row.get("value")), _f(row.get("moe"))
    if m is None or v is None:
        return None
    if v == 0:
        return float("inf") if m > 0 else None
    return m / Z90 / abs(v)


def unreliable(row) -> bool:
    if not row:
        return False
    c = cv_of(row)
    return (c is not None and c > CV_LIMIT) or "CV>30%" in (row.get("notes") or "")


def fmt_value(ind, v) -> str:
    if v is None:
        return ""
    if ind in MONEY:
        return f"${v:,.0f}"
    if ind in COUNTS or ind.startswith("qcew_"):
        return f"{v:,.0f}"
    if ind == "median_age":
        return f"{v:.1f}"
    return f"{v:.1f}%"


def fmt_moe(ind, m) -> str:
    if ind in MONEY:
        return f"${m:,.0f}"
    if ind in COUNTS:
        return f"{m:,.0f}"
    return f"{m:.2f}" if m < 0.1 else f"{m:.1f}"


def est_cell(ind, row) -> Markup:
    """Estimate with its MOE; greyed and marked when CV > 30%."""
    if not row or _f(row.get("value")) is None:
        return h("span", {"class": "muted"}, "not in data")
    v, m = _f(row["value"]), _f(row.get("moe"))
    moe = h("span", {"class": "moe"}, f" ± {fmt_moe(ind, m)}") if m is not None and m > 0 else None
    if unreliable(row):
        c = cv_of(row)
        cvs = "undefined (estimate is zero)" if c == float("inf") else f"{c * 100:.0f}%"
        return h("span", {"class": "est est-unreliable",
                          "title": f"Coefficient of variation {cvs}: above 30%, so treat as unreliable."},
                 fmt_value(ind, v), moe, h("sup", {"class": "cv-mark", "aria-label": "unreliable estimate"}, "†"))
    return h("span", {"class": "est"}, fmt_value(ind, v), moe)


def status_badges(rows, page):
    sts = []
    for r in rows:
        if r and r.get("status") and r["status"] not in sts:
            sts.append(r["status"])
    return join([status_badge(s, page) for s in sts], " ")


def cv_legend() -> Markup:
    return h("p", {"class": "cv-legend muted"},
             h("span", {"class": "est est-unreliable"}, "Grey", h("sup", {"class": "cv-mark"}, "†")),
             " = the margin of error is large compared with the estimate (coefficient of variation above 30%, "
             "computed as MOE ÷ 1.645 ÷ estimate). Treat it as unreliable. Such estimates are never used in "
             "headings or charts. ± is the published 90% margin of error.")


def matrix_table(page, iv, tid, caption, geos, inds, vintage, geo_header="Place", min_width=None):
    """Rows = geographies, columns = indicators, one vintage."""
    rows, used = [], []
    for g in geos:
        cells = [iv.short_name(g)]
        for ind in inds:
            r = iv.get(g, ind, vintage)
            used.append(r)
            cells.append(est_cell(ind, r))
        rows.append(cells)
    headers = [geo_header] + [iv.label(i) for i in inds]
    tbl = data_table(tid, headers, rows, caption=f"{caption} ({vintage})", numeric=tuple(range(1, len(inds) + 1)),
                     min_width=min_width)
    return tbl, used


def transpose_table(page, iv, tid, caption, inds, cols, label_fn=None, min_width=None, first="Indicator"):
    """Rows = indicators, columns = (header, geo, vintage)."""
    rows, used = [], []
    for ind in inds:
        cells = [label_fn(ind) if label_fn else iv.label(ind)]
        for _, g, vint in cols:
            r = iv.get(g, ind, vint)
            used.append(r)
            cells.append(est_cell(ind, r))
        rows.append(cells)
    headers = [first] + [c[0] for c in cols]
    tbl = data_table(tid, headers, rows, caption=caption, numeric=tuple(range(1, len(cols) + 1)), min_width=min_width)
    return tbl, used


def dollar_basis(iv, ind, vintage) -> str:
    r = iv.get(iv.county, ind, vintage) if iv.county else None
    m = re.search(r"(\d{4}) inflation-adjusted dollars", (r or {}).get("notes", ""))
    return f"{m.group(1)} dollars" if m else ""


# ------------------------------------------------------------------------------ indicator map
# The boundary map (civic/map.py embedded_map) shaded by one indicator at a time, with the shared sequential ramp and
# rounded natural breaks (civic/shading.py), computed separately for each indicator and each layer. The indicators are
# the ones in the page's own township and place tables. Estimates with a CV above 30% are never shaded (the page's
# rule: unreliable estimates are not used in charts); they show in the panel, greyed text, with their CV.
# static/js/indicator_map.js switches the indicator.
MAP_GEO_TYPES = {"place": ("place", "town"), "township": ("county_subdivision",)}
MAP_LAYERS = ("cities", "townships")
OVERLAP_NOTE = ("Areas overlap: every city and town lies inside a township, and its residents are counted in both. "
                "Don't add areas together, and compare shades only within one layer.")


def _geo_for_shape(iv, census_name, layer_key):
    """indicator geo_id for a map shape: same geography type, same Census name before the first comma."""
    want = (census_name or "").strip().lower()
    for g, r in iv.geo.items():
        if r["geo_type"] in MAP_GEO_TYPES.get(layer_key, ()) and r["geo_name"].split(",")[0].strip().lower() == want:
            return g
    return None


def _break_text(ind, v) -> str:
    """Legend figure for a break: whole or one-decimal, in the indicator's unit."""
    s = f"{v:,.0f}" if float(v).is_integer() else f"{v:,.1f}"
    if ind in MONEY:
        return "$" + s
    if ind in COUNTS or ind == "median_age":
        return s
    return s + "%"


def _fact_text(ind, row) -> str:
    if not row or _f(row.get("value")) is None:
        return "not in data"
    v, m = _f(row["value"]), _f(row.get("moe"))
    s = fmt_value(ind, v) + (f" ± {fmt_moe(ind, m)}" if m is not None and m > 0 else "")
    if unreliable(row):
        c = cv_of(row)
        cvs = "undefined, the estimate is zero" if c == float("inf") else f"CV {c * 100:.0f}%"
        s += f" (unreliable: margin of error large compared with the estimate, {cvs}; not shaded)"
    return s


def indicator_map_section(page, ed, iv, inds, vintage, sid, num, title):
    """A section with the indicator map: indicator picker, map (cities and towns, townships), legend per indicator
    and layer, panel with the area's whole row (estimate ± MOE, CV flag), method and overlap notes. None without
    map shapes."""
    shapes = load_shapes(ed)
    if shapes is None or not inds:
        return None
    c = page.cites
    labels = {i: iv.label(i) for i in inds}
    geo_of, used = {}, []
    for key, tab, _l, _h in LAYERS:
        if tab not in MAP_LAYERS:
            continue
        for it in shapes["layers"].get(key, []):
            if it.get("id") in ed.units:
                geo_of[it["id"]] = (key, tab, _geo_for_shape(iv, it.get("census_name"), key))
    # shade per indicator and layer (reliable estimates only)
    shade, legends = {}, []
    for ind in inds:
        shade[ind] = {}
        for key, tab, _l, _h in LAYERS:
            if tab not in MAP_LAYERS:
                continue
            vals = {}
            for uid, (k2, t2, g) in geo_of.items():
                if t2 != tab:
                    continue
                r = iv.get(g, ind, vintage) if g else None
                used.append(r)
                vals[uid] = _f(r["value"]) if r and not unreliable(r) and _f(r.get("value")) is not None else None
            min_unit = 1 if (ind in MONEY or ind in COUNTS) else 0.1
            cls = classify(vals, min_unit=min_unit)
            shade[ind].update({uid: s or 0 for uid, s in cls["shade"].items()})
            extra = [("cmap-mm-back", "Outside any city or town (not shaded)")] if key == "place" else []
            on = ind == inds[0]
            legends.append(shade_legend(
                f"{labels[ind]}, {vintage}", cls, fmt=lambda v, ind=ind: _break_text(ind, v),
                none_label="Not shaded: no estimate, or margin of error too large (CV above 30%)", extra=extra,
                attrs={"class": "cmap-mlegend" + (" is-on" if tab == "cities" else ""), "data-layer": tab,
                       "data-ind": ind, "hidden": None if on else True}))

    first = inds[0]

    def area(key, tab, n, it, uid, unit):
        g = geo_of[uid][2]
        rows = [iv.get(g, ind, vintage) if g else None for ind in inds]
        facts = [[labels[ind], _fact_text(ind, r)] for ind, r in zip(inds, rows)]
        href = page.rel(f"places/{uid}/index.html#context")
        tl = TYPE_LABEL.get(unit["unit_type"], unit["unit_type"])
        entry = {"n": unit["name"], "t": tl, "f": facts, "fk": list(inds),
                 "note": (f"American Community Survey {vintage} estimates for the Census area "
                          f"{iv.geo[g]['geo_name'].split(',')[0]}. ± is the 90% margin of error." if g else
                          "No survey estimates for this area in the guide's data."),
                 "href": href, "l": tab, "d": it["d"], "open": "Open its page"}
        cls = shade_class(shade[first].get(uid) or None)
        return (f"cmap-s cmap-mm {cls}", href, f"{unit['name']}, {tl.lower()}. Open its page.", entry,
                f"cmap-dot cmap-mm-dot {cls}")

    picker = h("div", {"class": "cmap-ind", "hidden": True},
               h("label", {"class": "cmap-chips-l", "for": f"cmap-ind-{sid}"}, "Shade by"),
               h("select", {"id": f"cmap-ind-{sid}", "class": "cmap-select cmap-ind-select"},
                 [h("option", {"value": i, "selected": i == first or None}, labels[i]) for i in inds]))
    cmap = embedded_map(page, ed, shapes, MAP_LAYERS, "cities", area=area,
                        label=f"Map of {ed.county_label}'s cities, towns and townships shaded by one survey estimate. "
                              "Every area is a link to its page; the tables on this page have every figure.",
                        hint="Hover, focus or tap an area to see all of its estimates here. Select it again, or use "
                             "the link, to open its page.",
                        legend=legends, defs=shade_defs(), extra_cls="cmap-indmap", controls=picker,
                        back_cls="cmap-s cmap-mm-back", attrs={"data-lead": first},
                        extra=json_script("cmap-shade", shade))
    src = _union(used)
    return section(sid, num, title,
                   h("p", None, f"Each area shaded by one estimate from the {vintage} survey: pick it above the map. "
                                "Point at an area (or tap it, or move to it with Tab) to see all of its estimates with "
                                "their margins of error.", c.cite(src) if src else None, " ", status_badges(used, page)),
                   here_slot("map", sid),
                   cmap,
                   h("p", {"class": "muted cmap-mnote"},
                     "Shading uses natural breaks rounded to readable figures, set separately for each estimate and "
                     "each layer; a figure equal to a break falls in the higher step. Estimates with a coefficient of "
                     "variation above 30% are not shaded (hatched) and are marked unreliable in the panel, the same "
                     "rule as the tables. Towns are small, so most of their estimates are unreliable."),
                   cv_legend(),
                   h("p", {"class": "muted cmap-mnote"}, OVERLAP_NOTE),
                   scope="county", ed=ed)


def hero(page, eyebrow, toc, dek=None):
    return h("header", {"class": "page-hero"},
             h("p", {"class": "eyebrow mono"}, eyebrow),
             h("h1", None, page.title),
             h("p", {"class": "dek"}, dek or page.description),
             h("nav", {"class": "toc", "aria-label": "On this page"},
               h("ol", None, [h("li", None, h("a", {"href": f"#{a}"}, t)) for a, t in toc])))


def page_gap(item, why, how=""):
    return {"item": item, "why_missing": why, "how_to_fill": how, "_file": "page"}


def community_gaps(ed, pattern):
    return ed.gaps(files=["gaps_community_people"], areas=["community"], pattern=pattern)


def bench_bars(page, iv, fid, ind, vintage, title=None):
    """County vs Indiana vs U.S. for one indicator (county in edition color, benchmarks in ink).
    Unreliable estimates are left out of the chart (they stay in the table)."""
    rows, used = [], []
    for g, mark in ((iv.county, "m-accent"), (iv.state, "m-ink"), (iv.nation, "m-ink")):
        r = iv.get(g, ind, vintage)
        if not r or _f(r["value"]) is None or unreliable(r):
            continue
        used.append(r)
        v = _f(r["value"])
        m = _f(r.get("moe"))
        rows.append({"label": iv.short_name(g), "value": v, "display": fmt_value(ind, v), "mark": mark,
                     "tip": iv.short_name(g) + (f" (± {fmt_moe(ind, m)})" if m else "")})
    if not rows:
        return None
    return hbar(fid, title or iv.label(ind), rows, subtitle=vintage, money=ind in MONEY,
                value_fmt=lambda v: fmt_value(ind, v), status=rows and used[0]["status"], page=page,
                headers=["Place", iv.label(ind)], cite=page.cites.cite(_union(used)),
                note="The county is shown in the edition color; Indiana and the U.S. are fixed benchmarks.")


# =============================================================================== community/index

def build_community_index(site):
    ed = site.ed
    iv = IV(ed)
    page = site.page("community/index.html")
    c = page.cites
    now, then = iv.acs_now, iv.acs_then
    toc = [("benchmarks", "County, Indiana and U.S."), ("explore", "Explore the community pages"),
           ("definitions", "What the indicators mean"), ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(hero(page, "Reference · Community", toc,
                  "Social and economic context for the county: the same fixed indicators every time, compared only "
                  "with Indiana and the United States, with margins of error and the survey years printed."))

    # ---- 1 benchmarks
    cols = [(iv.short_name(g), g, now) for g in (iv.county, iv.state, iv.nation)]
    rows, used = [], []
    for ind in CONTEXT_IDS:
        cells = [iv.label(ind)]
        for _, g, vint in cols:
            r = iv.get(g, ind, vint)
            used.append(r)
            cells.append(est_cell(ind, r))
        rows.append(cells)
    # population change since 2010: computed from the two ACS 5-year vintages
    chg = ["Population change since 2006–2010 (computed)"]
    chg_rows = []
    for _, g, _v in cols:
        a, b = iv.get(g, "pop_total", then), iv.get(g, "pop_total", now)
        chg_rows += [a, b]
        if a and b and _f(a["value"]) and _f(b["value"]) is not None:
            pct = (_f(b["value"]) - _f(a["value"])) / _f(a["value"]) * 100
            chg.append(h("span", {"class": "est"}, f"{pct:+.1f}%"))
        else:
            chg.append(h("span", {"class": "muted"}, "not in data"))
    rows.append(chg)
    tbl = data_table("benchmarks-table", ["Indicator"] + [x[0] for x in cols], rows,
                     caption=f"Fixed context indicators ({now})", numeric=(1, 2, 3), min_width="36rem")
    charts = [bench_bars(page, iv, f"bench-{i.replace('_', '-')}", i, now)
              for i in ("median_hh_income", "poverty_pct", "owner_occupied_pct", "bachelors_plus_pct")]
    page.add(section("benchmarks", 1, "St. Joseph County compared with Indiana and the U.S.",
                     h("p", None, f"These are the guide's fixed context indicators. Every place page uses the same set. "
                                  f"Figures are Census Bureau estimates from the American Community Survey (ACS), {now}.", c.cite(_union(used)), " ", status_badges(used, page)),
                     tbl,
                     h("p", {"class": "muted"},
                       f"Population change compares the {then} and {now} estimates. It is the guide's own "
                       "arithmetic, and no margin of error is computed for it. The county's ACS population total is a "
                       "controlled figure with no published margin of error.", c.cite(_union(chg_rows)), " ",
                       status_badge("computed", page, "Percent change between two ACS 5-year estimates.")),
                     cv_legend(),
                     h("div", {"class": "chart-grid"}, [x for x in charts if x]),
                     h("p", {"class": "muted"}, "Comparisons are only to Indiana and the U.S. The guide does not pick "
                                                "\"peer\" counties, because choosing which places to compare with is "
                                                "itself a framing choice."),
                     scope="county", ed=ed,
                     lead="Six indicators, the same for every unit, with the county shown against two fixed benchmarks."))

    # ---- 2 hub
    hub = []
    for path, blurb_extra in (("community/people/index.html", "Population since 1850, age, race and ethnicity, foreign-born residents."),
                              ("community/income-and-work/index.html", "Income, poverty, unemployment since 2000, jobs by industry, published employer lists."),
                              ("community/housing-and-education/index.html", "Owners and renters, home values, rents, rent burden, college degrees."),
                              ("community/research-on-voting/index.html", "The only place in the guide that discusses place and voting, through published analyses.")):
        e = site.by_path[path]
        hub.append(h("a", {"class": "card hub-card", "href": page.rel(path)},
                     h("span", {"class": "card-title hub-title"}, e.title),
                     h("span", {"class": "hub-desc"}, blurb_extra)))
    page.add(section("explore", 2, "Explore the community pages", h("div", {"class": "hub-grid"}, hub),
                     h("p", {"class": "muted"}, "History of the local economy (for example, the end of Studebaker "
                                                "production in South Bend in 1963) is on the ",
                       h("a", {"href": page.rel("history/index.html#turning-points")}, "History page"), ".")))

    # ---- 3 definitions
    drows = []
    for ind in CONTEXT_IDS:
        d = iv.defs.get(ind, {})
        drows.append([d.get("label", ind), d.get("definition", ""), d.get("universe", ""),
                      h("span", {"class": "mono"}, d.get("table_variable", "")), d.get("moe_rule", "")])
    pop_rule = iv.defs.get("pop_total", {}).get("display_rule", "")
    page.add(section("definitions", 3, "What the indicators mean",
                     h("p", None, "The ACS is a survey, not a full count, so each figure is an estimate with a margin of "
                                  "error. The guide's display rule for every ACS indicator: ", h("q", None, pop_rule)),
                     data_table("definitions-table", ["Indicator", "Definition", "Universe", "Census table / variable",
                                                      "Margin of error"], drows,
                                caption="Indicator definitions (Indiana-wide, shared by every edition)", min_width="52rem"),
                     h("p", None, "To pull the same figures yourself, the query for each indicator is on ",
                       h("a", {"href": page.rel("data/index.html")}, "Data and sources"), "."),
                     scope="indiana", ed=ed))

    gaps = community_gaps(ed, r"ACS 2006-2010|small townships|Cities cross|Decennial population|Income comparison")
    page.finish(gaps=gaps)
    return page


# =============================================================================== community/people

def build_people(site):
    ed = site.ed
    iv = IV(ed)
    page = site.page("community/people/index.html")
    c = page.cites
    now, then = iv.acs_now, iv.acs_then
    main_geos = [iv.county] + iv.places + [iv.state, iv.nation]
    toc = [("who", "Population over time"), ("age", "Age"), ("race", "Race and ethnicity"),
           ("foreign-born", "Born in another country"), ("households", "Households"),
           ("townships", "Townships"), *([("map", "On the map")] if load_shapes(ed) else []), ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(hero(page, "Reference · Community", toc))

    # ---- 1 population over time
    def dec_points(geo):
        pts, rows = [], []
        for r in iv.rows:
            if r["geo_id"] == geo and r["indicator_id"] == "pop_total" and re.fullmatch(r"Decennial census \d{4}", r["vintage"]):
                pts.append((int(r["vintage"][-4:]), _f(r["value"])))
                rows.append(r)
        pts.sort()
        return pts, rows
    cp, crow = dec_points(iv.county)
    city_series, city_rows = [], []
    for g, mark in zip(iv.places, ("m-ink", "m-accent")):
        pts, rows = dec_points(g)
        city_rows += rows
        city_series.append({"name": iv.short_name(g), "mark": mark, "points": pts})
    sb_geo = next((g for g in iv.places if "South Bend" in iv.geo[g]["geo_name"]), None)
    figs = []
    if cp:
        figs.append(line("pop-county", f"{iv.short_name(iv.county)} population, {cp[0][0]} to {cp[-1][0]}",
                         [{"name": iv.short_name(iv.county), "mark": "m-accent", "points": cp}],
                         subtitle="Decennial census counts", status=crow[0]["status"], page=page,
                         cite=c.cite(_union(crow)), note=crow[0].get("notes")))
    if city_series:
        first = min(p[0] for s in city_series for p in s["points"])
        last = max(p[0] for s in city_series for p in s["points"])
        figs.append(line("pop-cities", f"City populations, {first} to {last}", city_series,
                         subtitle="Decennial census counts; Mishawaka counts in the guide start in 1930",
                         status=city_rows[0]["status"], page=page, cite=c.cite(_union(city_rows)),
                         note=city_rows[0].get("notes")))
    peak = next((t for t in ed.table("timeline") if t["category"] == "population" and t["confidence"] == "high"
                 and "peak" in t["title"].lower()), None)
    latest_rows = []
    lrows = []
    for g in [iv.county] + iv.places:
        r1, r2 = iv.get(g, "pop_total", then), iv.get(g, "pop_total", now)
        latest_rows += [r1, r2]
        est = [r for (y, r) in iv.series(g, "pop_total", "Census population estimate")]
        latest_rows += est
        lrows.append([iv.short_name(g), est_cell("pop_total", r1), est_cell("pop_total", r2),
                      h("span", None, fmt_value("pop_total", _f(est[-1]["value"])), " (", est[-1]["vintage"], ") ",
                        status_badge(est[-1]["status"], page)) if est else h("span", {"class": "muted"}, "not in data")])
    page.add(section("who", 1, "Population over time",
                     h("p", None, "Census counts every ten years, from the earliest year the guide has for each place. "
                                  "These historical counts come from a secondary table that cites the Census Bureau.",
                       c.cite(_union(crow + city_rows)), " ", status_badges(crow + city_rows, page)),
                     h("p", None, peak["description"], c.cite(peak["source_ids"]), " ", status_badge(peak["status"], page))
                     if peak else None,
                     h("div", {"class": "chart-grid chart-grid-wide"}, figs),
                     h("h3", None, "Latest estimates"),
                     h("p", None, "Survey estimates are period averages, not counts, so they are listed here rather than "
                                  "added to the census lines above.", c.cite(_union(latest_rows))),
                     data_table("pop-latest", ["Place", f"{then}", f"{now}", "Census population estimate"], lrows,
                                caption="Population estimates", numeric=(1, 2, 3), min_width="36rem"),
                     scope="county", ed=ed))

    # ---- 2 age
    cols_now = [(iv.short_name(g), g, now) for g in main_geos]
    t1, u1 = matrix_table(page, iv, "age-table", "Median age", main_geos, ["median_age"], now)
    t2, u2 = matrix_table(page, iv, "age-table-then", "Median age", main_geos, ["median_age"], then)
    page.add(section("age", 2, "Age",
                     h("p", None, "Median age means half of residents are younger and half are older.",
                       c.cite(_union(u1 + u2)), " ", status_badges(u1 + u2, page)),
                     h("div", {"class": "pair-tables"}, t1, t2),
                     h("p", {"class": "muted"}, "Age groups (for example, the share under 18 or 65 and older) are not "
                                                "in the guide's data yet. See Gaps."),
                     scope="county", ed=ed))

    # ---- 3 race and ethnicity
    race_cols = [(iv.short_name(g), g, now) for g in main_geos]
    rt, ru = transpose_table(page, iv, "race-table", f"Race and Hispanic or Latino origin ({now})", RACE_IDS, race_cols,
                             min_width="52rem")
    race_then_cols = [(iv.short_name(g), g, then) for g in main_geos]
    rt2, ru2 = transpose_table(page, iv, "race-table-then", f"Race and Hispanic or Latino origin ({then})", RACE_IDS,
                               race_then_cols, min_width="52rem")
    dec = sorted({r["vintage"] for r in iv.rows if r["indicator_id"].startswith("race_") and r["vintage"].startswith("Decennial")})
    dec_cols = [(f"{iv.short_name(g)}, {v[17:21]}", g, v) for g in [iv.county] + iv.places for v in dec
                if any(iv.get(g, i, v) for i in RACE_IDS)]
    dec_inds = [i for i in RACE_IDS if any(iv.get(g, i, v) for _, g, v in dec_cols)]
    rt3, ru3 = transpose_table(page, iv, "race-table-census", "Race and Hispanic or Latino origin, decennial census",
                               dec_inds, dec_cols, min_width="40rem") if dec_cols else (None, [])
    bar_rows = []
    for ind in RACE_IDS:
        r = iv.get(iv.county, ind, now)
        if r and _f(r["value"]) is not None and not unreliable(r):
            bar_rows.append({"label": iv.label(ind).split(" (percent")[0], "value": _f(r["value"]),
                             "display": fmt_value(ind, _f(r["value"])), "tip": f"± {fmt_moe(ind, _f(r['moe']) or 0)} points"})
    race_fig = hbar("race-county", f"{iv.short_name(iv.county)}: race and Hispanic or Latino origin", bar_rows,
                    subtitle=f"{now}; percent of total population; Census table order",
                    value_fmt=lambda v: f"{v:.1f}%", status="computed", page=page,
                    headers=["Census category", "Percent"], cite=c.cite(_union(ru)),
                    note="Percentages are computed from the published Census counts (table B03002). Categories are "
                         "listed in the Census table's order, not by size.") if bar_rows else None
    page.add(section("race", 3, "Race and Hispanic or Latino origin",
                     h("p", None, "Category names are the Census Bureau's own, word for word. In Census data, Hispanic or "
                                  "Latino is an origin, not a race, so these categories count each person once: Hispanic or "
                                  "Latino people of any race, then non-Hispanic people by race.",
                       c.cite(_union(ru)), " ", status_badges(ru, page)),
                     race_fig, rt, cv_legend(),
                     h("h3", None, f"Earlier survey: {then}"), rt2,
                     h("h3", None, "Census counts, 2010 and 2020") if rt3 else None,
                     h("p", None, ru3[0]["notes"] if ru3 and ru3[0] else "", c.cite(_union(ru3)), " ",
                       status_badges(ru3, page)) if rt3 else None,
                     rt3,
                     scope="county", ed=ed))

    # ---- 4 foreign-born
    fb_cols = [(iv.short_name(g), g) for g in main_geos]
    fbrows, fbu = [], []
    for name, g in fb_cols:
        a, b = iv.get(g, "foreign_born_pct", then), iv.get(g, "foreign_born_pct", now)
        fbu += [a, b]
        fbrows.append([name, est_cell("foreign_born_pct", a), est_cell("foreign_born_pct", b)])
    page.add(section("foreign-born", 4, "Residents born in another country",
                     h("p", None, iv.defs.get("foreign_born_pct", {}).get("definition", ""),
                       c.cite(_union(fbu)), " ", status_badges(fbu, page)),
                     data_table("foreign-born-table", ["Place", then, now], fbrows,
                                caption="Foreign-born population (percent)", numeric=(1, 2), min_width="30rem"),
                     scope="county", ed=ed))

    # ---- 5 households
    page.add(section("households", 5, "Households",
                     h("p", None, "Household counts, household size and household types are not in the guide's data yet. "
                                  "They are listed under Gaps rather than estimated here."),
                     scope="county", ed=ed))

    # ---- 6 townships
    tt, tu = matrix_table(page, iv, "townships-people", "Townships: population, age, foreign-born",
                          iv.townships, ["pop_total", "median_age", "foreign_born_pct"], now, "Township", "40rem")
    tr, tru = matrix_table(page, iv, "townships-race", "Townships: race and Hispanic or Latino origin (percent)",
                           iv.townships, RACE_IDS, now, "Township", "80rem")
    page.add(section("townships", 6, "Townships",
                     h("p", None, "Indiana townships are Census county subdivisions, so the survey publishes estimates "
                                  "for each one. Samples in small townships are small, so many estimates have wide "
                                  "margins of error.", c.cite(_union(tu + tru)), " ", status_badges(tu + tru, page)),
                     cv_legend(), tt, tr,
                     h("p", {"class": "muted"}, "Cities cross township lines, so city and township figures overlap. "
                                                "Don't add them together."),
                     scope="county", ed=ed))
    # Race and Hispanic-origin shares stay in the page's tables only, not as map shading or panel rows (Nick,
    # 2026-11-08: "table only").
    page.add(indicator_map_section(page, ed, iv, ["pop_total", "median_age", "foreign_born_pct"], now,
                                   "map", 7, "On the map: townships, cities and towns"))

    gaps = community_gaps(ed, r"small townships|Cities cross|Decennial population|Township decennial|ACS 2006-2010")
    gaps += [page_gap("Households: number of households, household size and household types",
                      "Not pulled into indicator_values.csv (no households indicator in data/indiana/indicators.csv).",
                      "Add ACS tables B11001 / B25010 to indicators.csv and re-run the community fetch."),
             page_gap("Age groups (under 18, 18-64, 65 and older)",
                      "Only median age is in indicator_values.csv.",
                      "Add ACS table B01001 age groups to indicators.csv and re-run the fetch.")]
    page.finish(gaps=gaps)
    return page


# =============================================================================== community/income-and-work

def build_income_work(site):
    ed = site.ed
    iv = IV(ed)
    page = site.page("community/income-and-work/index.html")
    c = page.cites
    now, then = iv.acs_now, iv.acs_then
    main_geos = [iv.county] + iv.places + [iv.state, iv.nation]
    toc = [("work", "Income and poverty"), ("unemployment", "Unemployment"), ("industries", "Jobs by industry"),
           ("residents-work", "What residents do"), ("employers", "Employer lists"), *([("map", "On the map")] if load_shapes(ed) else []),
           ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(hero(page, "Reference · Community", toc))

    # ---- 1 income and poverty
    inds = ["median_hh_income", "per_capita_income", "poverty_pct", "child_poverty_pct"]
    t_now, u_now = matrix_table(page, iv, "income-now", "Income and poverty", main_geos, inds, now, min_width="48rem")
    t_then, u_then = matrix_table(page, iv, "income-then", "Income and poverty", main_geos, inds, then, min_width="48rem")
    pov = bench_bars(page, iv, "bench-poverty", "poverty_pct", now)
    inc = bench_bars(page, iv, "bench-income", "median_hh_income", now)
    page.add(section("work", 1, "Income and poverty",
                     h("p", None, f"Household income and poverty from the {now} survey. Dollar figures are in "
                                  f"{dollar_basis(iv, 'median_hh_income', now)}.", c.cite(_union(u_now)), " ",
                       status_badges(u_now, page)),
                     h("div", {"class": "chart-grid"}, [x for x in (inc, pov) if x]),
                     t_now, cv_legend(),
                     h("h3", None, f"Earlier survey: {then}"),
                     h("p", None, f"Dollar figures here are in {dollar_basis(iv, 'median_hh_income', then)}. The guide has "
                                  "not adjusted them for inflation, so don't compare the dollar amounts in the two tables "
                                  "directly. Poverty rates can be compared, within their margins of error.",
                       c.cite(_union(u_then))),
                     t_then,
                     scope="county", ed=ed))

    # ---- 2 unemployment
    def laus(g):
        return iv.series(g, "unemployment_rate", "BLS LAUS")
    bench = []
    for g, mark in ((iv.county, "m-accent"), (iv.state, "m-ink"), (iv.nation, "m-ink-dash")):
        s = laus(g)
        if s:
            bench.append(({"name": iv.short_name(g), "mark": mark, "points": [(y, _f(r["value"])) for y, r in s]}, s))
    cities = []
    for g, mark in [(iv.county, "m-accent")] + list(zip(iv.places, ("m-ink", "m-ink-dash"))):
        s = laus(g)
        if s:
            cities.append(({"name": iv.short_name(g), "mark": mark, "points": [(y, _f(r["value"])) for y, r in s]}, s))
    all_rows = [r for _, s in bench + cities for _, r in s]
    last_note = next((r["notes"] for _, s in bench for y, r in s if "partial" in r.get("notes", "")), "")
    ue = iv.defs.get("unemployment_rate", {})
    fig1 = line("unemployment-bench", "Unemployment rate, annual average",
                [x[0] for x in bench],
                subtitle=f"{min(p[0] for x in bench for p in x[0]['points'])} to {max(p[0] for x in bench for p in x[0]['points'])}; "
                         "Indiana and U.S. series in the guide start in 2006",
                value_fmt=lambda v: f"{v:.1f}%", status="official", page=page,
                cite=c.cite(_union(r for _, s in bench for _, r in s)),
                note=last_note.split("; ")[-1] if last_note else None) if bench else None
    fig2 = line("unemployment-cities", "Unemployment rate: county and cities", [x[0] for x in cities],
                subtitle="City series in the guide start in 2006", value_fmt=lambda v: f"{v:.1f}%", status="official",
                page=page, cite=c.cite(_union(r for _, s in cities for _, r in s))) if cities else None
    page.add(section("unemployment", 2, "Unemployment, 2000 to 2025",
                     h("p", None, "The share of people in the labor force who are looking for work and don't have a job, "
                                  "averaged over each year. ", ue.get("moe_rule", ""), " ", ue.get("display_rule", ""),
                       c.cite(_union(all_rows)), " ", status_badges(all_rows, page)),
                     fig1, fig2,
                     h("p", {"class": "muted"}, "Dashed and solid gray lines are both benchmarks; the legend and the "
                                                "table under each chart name every line."),
                     scope="county", ed=ed))

    # ---- 3 jobs by industry (QCEW)
    qcew_ids = QCEW_OWN + [k for k in iv.defs if k.startswith("qcew_jobs_naics_")]
    tot = iv.series(iv.county, "qcew_jobs_all_ownerships", "QCEW")
    years = [y for y, _ in tot]
    brk_after = years.index(2013) if 2013 in years else None
    total_fig = columns("jobs-total", "Jobs located in the county, all employers",
                        [{"x": y, "value": _f(r["value"]), "display": fmt_value("qcew_x", _f(r["value"]))} for y, r in tot],
                        subtitle=f"{years[0]} to {years[-1]}; annual average" if years else None,
                        breaks=[{"after": brk_after, "label": "Source file changes",
                                 "tip": "2001-2013 from the bulk annual files; 2014 on from the open-data API"}]
                        if brk_after is not None else None,
                        status="official", page=page, cite=c.cite(_union(r for _, r in tot)),
                        note="QCEW counts jobs at workplaces in the county, wherever the workers live. Per the source "
                             "record, 2001-2013 come from BLS bulk annual files and 2014 on from the BLS open-data API, "
                             "so the chart marks a break between 2013 and 2014.") if tot else None
    periods = [(2001, 2013), (2014, 2024)]
    qrows, qused = [], []

    def qval(ind, y):
        r = iv.get(iv.county, ind, f"QCEW {y} annual")
        qused.append(r)
        return r, (_f(r["value"]) if r else None)

    for ind in qcew_ids:
        lab = iv.label(ind).replace("Jobs in the county, ", "")
        lab = re.sub(r"^private, NAICS [\d_-]+ ", "", lab)
        lab = lab[0].upper() + lab[1:]
        cells = [lab]
        for a, b in periods:
            ra, va = qval(ind, a)
            rb, vb = qval(ind, b)
            def cell(r, v):
                if r is None:
                    return h("span", {"class": "muted"}, "not in data")
                if v is None:
                    return h("span", {"class": "muted"}, "suppressed")
                return fmt_value("qcew_x", v)
            cells += [cell(ra, va), cell(rb, vb),
                      (f"{vb - va:+,.0f}" if va is not None and vb is not None else h("span", {"class": "muted"}, "n/a"))]
        qrows.append(cells)
    qhdr = ["Employer type or industry"]
    for a, b in periods:
        qhdr += [str(a), str(b), f"Change {a}–{b}"]
    qtbl = data_table("jobs-industry", qhdr, qrows, caption="Jobs located in the county by industry, then and now (QCEW)",
                      numeric=tuple(range(1, len(qhdr))), min_width="56rem")
    page.add(section("industries", 3, "Jobs located in the county, by industry",
                     h("p", None, "The Quarterly Census of Employment and Wages (QCEW) counts jobs covered by "
                                  "unemployment insurance at workplaces in the county. It has no margin of error.",
                       c.cite("COM-004"), " ", status_badge("official", page)),
                     total_fig,
                     h("h3", None, "Then and now"),
                     h("p", None, "Each pair of years comes from one source file, so the guide compares 2001 with 2013 "
                                  "and 2014 with 2024, and doesn't compare across the break. Industry definitions (NAICS) "
                                  "were revised in 2002, 2007, 2012 and 2017, which also limits comparisons. Cells withheld "
                                  "by BLS to protect employer confidentiality are shown as suppressed.",
                       c.cite(_union(qused)), " ", status_badge("computed", page, "Changes are the guide's subtraction.")),
                     qtbl,
                     scope="county", ed=ed))

    # ---- 4 what residents do (ACS by place of residence)
    rcols = [(f"{iv.short_name(iv.county)}, {then}", iv.county, then), (f"{iv.short_name(iv.county)}, {now}", iv.county, now),
             (f"{iv.short_name(iv.state)}, {now}", iv.state, now), (f"{iv.short_name(iv.nation)}, {now}", iv.nation, now)]
    et, eu = transpose_table(page, iv, "residents-industry", "Employed residents by industry (percent)",
                             EMP_IDS + ["emp_ind_employed_total"], rcols,
                             label_fn=lambda i: iv.label(i).replace("Employed residents in: ", "").replace(" (percent)", ""),
                             min_width="52rem", first="Industry")
    page.add(section("residents-work", 4, "What residents do for work",
                     h("p", None, "This survey table counts employed residents by the industry they work in, wherever their "
                                  "job is. That is different from the QCEW table above, which counts jobs located in the "
                                  "county. Categories are the Census Bureau's.", c.cite(_union(eu)), " ",
                       status_badges(eu, page)),
                     et, cv_legend(),
                     scope="county", ed=ed))

    # ---- 5 employers
    emps = ed.table("employers")
    groups = OrderedDict()
    for e in emps:
        groups.setdefault((e["selection_rule"], e["as_of"], e["source_ids"]), []).append(e)
    blocks = []
    order = sorted(groups.items(), key=lambda kv: ({"official": 0, "secondary": 1, "single_source": 2}.get(kv[1][0]["status"], 3),
                                                   -int(re.match(r"\d{4}", kv[0][1]).group(0)) if re.match(r"\d{4}", kv[0][1]) else 0))
    singles = []
    n = 0
    for (rule, as_of, sids), rows in order:
        if len(rows) == 1:
            singles.append(rows[0])
            continue
        n += 1
        has_counts = any(r["employees"] for r in rows)
        trs = []
        for i, r in enumerate(rows, 1):
            row = [str(i), r["name"], r["sector"]]
            if has_counts:
                row.append(fmt_value("qcew_x", _f(r["employees"])) if r["employees"] else "not stated")
            trs.append(row)
        hdr = ["Order in source", "Name as printed", "Sector"] + (["Employees"] if has_counts else [])
        blocks.append(h("div", {"class": "employer-list"},
                        h("h3", None, f"List {n}: {(ed.source(split_ids(sids)[0]) or {}).get('publisher', '')}, "
                                      f"dated {fmt_date(as_of)}"),
                        h("p", None, h("strong", None, "Rule: "), rule, ". ", c.cite(sids), " ",
                          status_badge(rows[0]["status"], page)),
                        h("p", {"class": "muted"}, rows[0]["notes"]),
                        see_all_fold(f"employers-{n}-all", len(trs),
                                     data_table(f"employers-{n}", hdr, trs, caption=f"Employers named: {rule}",
                                                numeric=(0, 3) if has_counts else (0,), min_width="30rem"),
                                     noun="employer")))
    if singles:
        srows = [[r["name"], r["sector"], fmt_value("qcew_x", _f(r["employees"])) if r["employees"] else "not stated",
                  fmt_date(r["as_of"]), r["selection_rule"], r["notes"],
                  h("span", None, status_badge(r["status"], page), c.cite(r["source_ids"]))] for r in singles]
        blocks.append(h("div", {"class": "employer-list"},
                        h("h3", None, "Single counts published by one organization"),
                        h("p", None, "Each of these is one organization's own figure for itself, not part of a list. "
                                     "Definitions of an employee differ."),
                        see_all_fold("employers-single-all", len(srows),
                                     data_table("employers-single", ["Name", "Sector", "Count", "As of", "What the count is",
                                                                     "Notes", "Status"], srows,
                                                caption="Single published counts", numeric=(2,), min_width="56rem"),
                                     noun="count")))
    page.add(section("employers", 5, "Employer lists, as published",
                     callout(h("p", None, h("strong", None, "Selection rule. "),
                               "The guide lists employers only as they appear in a named, published list, in the order the "
                               "source prints them, with that source's own rule and date. It doesn't rank employers itself, "
                               "combine lists, or describe any employer. Lists are shown official sources first, then "
                               "newest first. Names and sectors are as the data records them.")),
                     blocks,
                     scope="county", ed=ed))
    page.add(indicator_map_section(page, ed, iv, inds, now, "map", 6, "On the map: townships, cities and towns"))

    gaps = community_gaps(ed, r"Unemployment rate for 2025|QCEW|employer|ACS 2006-2010|small townships|Income comparison")
    page.finish(gaps=gaps)
    return page


# =============================================================================== community/housing-and-education

def build_housing(site):
    ed = site.ed
    iv = IV(ed)
    page = site.page("community/housing-and-education/index.html")
    c = page.cites
    now, then = iv.acs_now, iv.acs_then
    main_geos = [iv.county] + iv.places + [iv.state, iv.nation]
    toc = [("housing", "Housing"), ("education", "Education"), ("townships", "Townships"), *([("map", "On the map")] if load_shapes(ed) else []),
           ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(hero(page, "Reference · Community", toc))
    hinds = ["owner_occupied_pct", "median_home_value", "median_gross_rent", "rent_burdened_pct"]
    t_now, u_now = matrix_table(page, iv, "housing-now", "Housing", main_geos, hinds, now, min_width="48rem")
    t_then, u_then = matrix_table(page, iv, "housing-then", "Housing", main_geos, hinds, then, min_width="48rem")
    own = bench_bars(page, iv, "bench-owner", "owner_occupied_pct", now)
    burden = bench_bars(page, iv, "bench-burden", "rent_burdened_pct", now)
    defs = "; ".join(f"{iv.label(i)}: {iv.defs.get(i, {}).get('universe', '')}" for i in hinds)
    page.add(section("housing", 1, "Housing: owners, renters, values and rents",
                     h("p", None, "Every occupied home is either owner-occupied or renter-occupied, so the renter share is "
                                  "100% minus the owner share. Home values and rents are medians: half are higher and half "
                                  f"lower. Dollar figures are in {dollar_basis(iv, 'median_home_value', now)}.",
                       c.cite(_union(u_now)), " ", status_badges(u_now, page)),
                     h("p", {"class": "muted"}, "Who each figure covers. ", defs, "."),
                     h("div", {"class": "chart-grid"}, [x for x in (own, burden) if x]),
                     t_now, cv_legend(),
                     h("h3", None, f"Earlier survey: {then}"),
                     h("p", None, f"Dollar figures here are in {dollar_basis(iv, 'median_home_value', then)}, not adjusted "
                                  "for inflation, so don't compare dollar amounts across the two tables directly.",
                       c.cite(_union(u_then))),
                     t_then,
                     scope="county", ed=ed))
    ecols = [(f"{iv.short_name(g)}", g) for g in main_geos]
    erows, eu = [], []
    for name, g in ecols:
        a, b = iv.get(g, "bachelors_plus_pct", then), iv.get(g, "bachelors_plus_pct", now)
        eu += [a, b]
        erows.append([name, est_cell("bachelors_plus_pct", a), est_cell("bachelors_plus_pct", b)])
    ba = bench_bars(page, iv, "bench-bachelors", "bachelors_plus_pct", now)
    note_then = (iv.get(iv.county, "bachelors_plus_pct", then) or {}).get("notes", "")
    page.add(section("education", 2, "Education: college degrees",
                     h("p", None, "The share of adults 25 and older with a bachelor's degree or higher.",
                       c.cite(_union(eu)), " ", status_badges(eu, page)),
                     ba,
                     data_table("bachelors-table", ["Place", then, now], erows,
                                caption=iv.label("bachelors_plus_pct"), numeric=(1, 2), min_width="30rem"),
                     h("p", {"class": "muted"}, f"How the {then} figure was built: {note_then}") if note_then else None,
                     h("p", {"class": "muted"}, "Other attainment levels (high school, some college) are not in the "
                                                "guide's data yet. Each school corporation's enrollment and spending per "
                                                "student are on the ", h("a", {"href": page.rel("schools/index.html")}, "Schools page"), "."),
                     scope="county", ed=ed))
    tt, tu = matrix_table(page, iv, "townships-housing", "Townships: housing and degrees", iv.townships,
                          hinds + ["bachelors_plus_pct"], now, "Township", "64rem")
    page.add(section("townships", 3, "Townships",
                     h("p", None, "Survey estimates for each township. Small townships have small samples, so check the "
                                  "margins of error.", c.cite(_union(tu)), " ", status_badges(tu, page)),
                     cv_legend(), tt,
                     h("p", {"class": "muted"}, "Cities cross township lines, so city and township figures overlap."),
                     scope="county", ed=ed))
    page.add(indicator_map_section(page, ed, iv, hinds + ["bachelors_plus_pct"], now, "map", 4,
                                   "On the map: townships, cities and towns"))
    gaps = community_gaps(ed, r"ACS 2006-2010|small townships|Cities cross")
    gaps += [page_gap("Educational attainment below the bachelor's level, and the survey count of residents in school",
                      "Only bachelor's-or-higher is in indicator_values.csv. The school corporations' own enrollment "
                      "counts (Indiana Department of Education) are on the Schools page; the survey's count of residents "
                      "enrolled in school is a different measure and is not in the data.",
                      "Add ACS tables B15003 (all levels) and B14001 (enrollment) to indicators.csv and re-run the fetch."),
             page_gap("SAIPE school-district poverty estimates",
                      "The survey (ACS) indicators for each school district are in indicator_values.csv, but the Census "
                      "Bureau's SAIPE model estimates of school-age poverty by school district are not.",
                      "Pull the SAIPE school district estimates for the county's school corporations.")]
    page.finish(gaps=gaps)
    return page


# =============================================================================== community/research-on-voting

def build_research(site):
    ed = site.ed
    page = site.page("community/research-on-voting/index.html")
    c = page.cites
    studies = ed.table("research_on_voting")
    by_url = {}
    for sid, s in ed.sources.items():
        for u in (s.get("url") or "").split(" ; "):
            by_url[u.strip()] = sid
    toc = [("fallacy", "Places are not people"), ("rule", "What this page includes"), ("studies", "Published analyses"),
           ("data", "Study it yourself"), ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(hero(page, "Reference · Community", toc))
    page.add(h("aside", {"class": "callout callout-fallacy", "id": "fallacy", "aria-labelledby": "fallacy-h"},
               h("p", {"class": "fallacy-kicker mono"}, "Read this first"),
               h("h2", {"id": "fallacy-h", "class": "fallacy-h"}, "Patterns describe places, not people"),
               h("p", None, "Election results are counted by place: a precinct, a township, a county. So any pattern "
                            "between a place's results and its income, age or other traits is a fact about the place. "
                            "It does not tell you how any person voted. A township where incomes are higher and that "
                            "voted more for one party does not tell you how any higher-income person there voted."),
               h("p", None, "Reading individual behavior from area totals is a known error called the ",
                 h("strong", None, "ecological fallacy"), ". The guide never puts demographic data next to election "
                 "results in its own charts or tables, and it doesn't compute its own correlations between them.")))
    page.add(section("rule", 1, "What this page includes",
                     h("p", None, "The guide includes a published analysis only if it names its authors, outlet and date, "
                                  "describes its method, is published by a news organization, academic body or government "
                                  "agency, and covers St. Joseph County or a place in it. Each one is shown with the same fields: "
                                  "geography, period, method, what it reports and its stated limits. Summaries are "
                                  "attributed to their authors. The guide adds no interpretation."),
                     h("p", None, h("strong", None, f"Little local research exists. "),
                       f"The guide's search found {len(studies)} pieces that meet the rule. "
                       f"{'Neither' if len(studies) == 2 else 'None of them'} links votes to income, "
                       "race or any other demographic data. The guide found no published study of township- or "
                       "precinct-level voting differences in the county (see Gaps).")))
    cards = []
    for s in sorted(studies, key=lambda s: s["date"]):
        sid = by_url.get(s["url"].strip(), "")
        fields = [("Authors", s["authors"]), ("Outlet", s["outlet"]), ("Published", fmt_date(s["date"], long=True)),
                  ("Geography", s["geography"]), ("Period covered", s["period"]), ("Method", s["method"]),
                  ("What it reports (the authors' account)", s["finding_summary"]), ("Stated or evident limits", s["limits"])]
        cards.append(h("article", {"class": "card study-card", "id": f"study-{s['study_id'].lower()}"},
                       h("h3", {"class": "card-title"},
                         h("a", {"href": s["url"], "target": "_blank", "rel": "noopener"},
                           h("cite", {"data-verbatim": "source-title"}, s["title"])), c.cite(sid) if sid else None),
                       h("dl", {"class": "study-fields"}, [[h("dt", None, k), h("dd", None, v)] for k, v in fields]),
                       h("p", {"class": "holder-badges"}, status_badge(s["status"], page))))
    gap_wish = next((g for g in ed.gaps(files=["gaps_community_people"], areas=["research_on_voting"], pattern=r"WISH")), None)
    page.add(section("studies", 2, "Published analyses", h("div", {"class": "study-grid"}, cards),
                     h("p", {"class": "muted"}, "Note on the WISH-TV figures: the article names no data source. Its "
                                                "governor shares for the county match the county's official 2024 canvass "
                                                "after rounding; its presidential shares were not checked against the "
                                                "canvass (see Gaps).", c.cite("RES-027")) if gap_wish else None,
                     h("p", None, "Official county vote totals are on the ",
                       h("a", {"href": page.rel("elections/results/index.html")}, "results pages"),
                       ". They are kept apart from this page on purpose."),
                     scope="county", ed=ed))
    links = []
    for sid in ("COM-L01", "COM-L02", "COM-L03"):
        s = ed.source(sid)
        if not s:
            continue
        links.append(h("li", None, h("a", {"href": s["url"], "target": "_blank", "rel": "noopener"},
                                     h("cite", {"data-verbatim": "source-title"}, s["title"])),
                       f" ({s['publisher']})", c.cite(sid),
                       h("span", {"class": "muted"}, " ", s["notes"].split(". ")[0].rstrip(".") + ".")))
    page.add(section("data", 3, "Study it yourself: raw datasets",
                     h("p", None, "Anyone who wants to study place and voting here can start from these public datasets. "
                                  "The guide links them but has not used them for any figure, chart or claim."),
                     h("ul", {"class": "link-list"}, links),
                     h("p", None, "Census and BLS figures for the same places, and how to pull them, are on ",
                       h("a", {"href": page.rel("data/index.html")}, "Data and sources"), ". Precincts are not Census "
                       "geographies, so matching the two takes allocation methods that add their own error."),
                     ))
    gaps = ed.gaps(files=["gaps_community_people"], areas=["research_on_voting"])
    page.finish(gaps=gaps)
    return page


# =============================================================================== history/index

def _chamber_chart(fid, title, rows, page, cite=None, note=None):
    """Seats by party per period for a large chamber: one stacked bar per period on a 0-to-total
    scale, majority line, text summary. Party colors on party data only, always with text labels."""
    W, lab_w, sum_w = 620, 92, 170
    plot_w = W - lab_w - sum_w
    row_h, bh, pad_t = 28, 16, 22
    H = pad_t + row_h * len(rows) + 8
    marks = []
    total = max(int(r["total"]) for r in rows)
    mx = lab_w + plot_w * ((total // 2 + 1) / total)
    marks.append(h("line", {"class": "majority-line", "x1": f"{mx:.1f}", "x2": f"{mx:.1f}", "y1": pad_t - 6, "y2": H - 4}))
    marks.append(_txt(mx, pad_t - 10, f"Majority: {total // 2 + 1} of {total}", "ct ct-muted ct-small", "middle"))
    present = []
    for i, r in enumerate(rows):
        y0 = pad_t + i * row_h + (row_h - bh) / 2
        g = [h("rect", {"class": "hit", "x": 0, "y": f"{pad_t + i * row_h:.1f}", "width": W, "height": row_h}),
             _txt(lab_w - 8, y0 + bh - 3, r["label"] + ("*" if r.get("unofficial") else ""), "ct ct-mono", "end")]
        parts = [(k, r[k]) for k in ("D", "R", "O") if r.get(k)]
        if not parts:
            g.append(_txt(lab_w + 4, y0 + bh - 3, "Seat totals not in the guide's data", "ct ct-muted"))
            summary = "no seat totals"
        else:
            x = lab_w
            for k, n in parts:
                w = plot_w * n / r["total"]
                g.append(h("rect", {"class": f"seat {party_mark(k)}", "x": f"{x:.1f}", "y": f"{y0:.1f}",
                                    "width": f"{max(w - 1, 1):.1f}", "height": bh, "rx": 1}))
                x += w
                if k not in present:
                    present.append(k)
            summary = " · ".join(f"{n} {k}" for k, n in parts)
            g.append(_txt(lab_w + plot_w + 8, y0 + bh - 3, summary, "ct"))
        marks.append(h("g", {"class": "mark", "tabindex": "0", "data-tv": summary, "data-tl": f"{title}, {r['label']}"}, g))
    svg = _svg(W, H, f"{title}. Seats by party for each two-year period; values in the table view.", marks)
    leg = legend([(party_mark(k), party_label(k) if k != "O" else "Other or independent") for k in present], "rect")
    trows = [[r["label"], str(r.get("D", "")), str(r.get("R", "")), str(r.get("O", "")), str(r["total"]),
              r.get("super", ""), r.get("status", "")] for r in rows]
    return figure(fid, title, f"{rows[0]['label']} to {rows[-1]['label']}, {total} seats", svg,
                  ["Period", party_label("D"), party_label("R"), "Other", "Total seats", "Two-thirds held by", "Status"],
                  trows, note=note, numeric=(1, 2, 3, 4), page=page, legend=leg, kind="party", cite=cite)


def _clean_note(t):
    t = re.sub(r"^No\. \d+ in the Wikipedia list\.\s*", "", t or "")
    t = re.sub(r";?\s*scheduled_end=\S+", "", t)
    return t.strip()


def _mayor_table(ed, page, office_id, tid):
    terms = ed.terms_for(office_id)
    no_start = [t for t in ed.tables["terms"] if t["office_id"] == office_id and not parse_date(t["start"])]
    terms = no_start + [t for t in terms if t not in no_start]
    rows = []
    for i, t in enumerate(terms, 1):
        if t.get("end"):
            left = fmt_date(t["end"])
        elif i == len(terms) and parse_date(t["start"]) and parse_date(t["start"]) <= ed.as_of:
            left = "In office"
        else:
            left = ""
        badges = [status_badge(t["status"], page)]
        if t.get("confidence") == "low":
            badges.append(status_badge("low", page))
        rows.append([str(i), t["person"], party_label(t["party"]) if t["party"] else "Party not in sources",
                     fmt_date(t["start"]) or "not in sources", left or "not in sources",
                     SELECTED_BY_LABELS.get(t.get("first_selected_by", ""), t.get("first_selected_by")),
                     h("span", {"class": "badge-row"}, badges, page.cites.cite(t["source_ids"])),
                     _clean_note(t.get("notes"))])
    return data_table(tid, ["#", "Mayor", "Party", "Took office", "Left office", "How chosen", "Status", "Notes"], rows,
                      caption=ed.offices[office_id]["title"] + ", in order of taking office", numeric=(0,),
                      min_width="64rem"), terms


def build_history(site):
    ed = site.ed
    iv = IV(ed)
    from pages.county import CONTROL_METHOD, control_by_year  # shared seat-holder-by-year logic and its method text
    page = site.page("history/index.html", banners=True)
    c = page.cites
    toc = [("control", "Party control over time"), ("mayors", "Mayors"), ("turning-points", "Turning points"),
           ("population", "South Bend's population"), ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(hero(page, "Reference · History", toc,
                  "Which party held each elected body year by year, every mayor in the sources, and dated political, "
                  "economic and legal events, each with its source."))

    # ---- 1 party control
    method = CONTROL_METHOD
    bodies = [("county", "county_council_member", "control-council", "County Council"),
              ("county", "county_commissioner", "control-commissioners", "Board of Commissioners")]
    for unit in ed.config.get("places", {}).get("cities", []):
        council = [o for o in ed.offices_for(unit) if o["office_type"].startswith("city_council")]
        if council:
            bodies.append((unit, "city_council", f"control-{unit}-council", council[0]["title"].split(",")[0]))
    charts = []
    for unit, otype, fid, label in bodies:
        offs = [o for o in ed.offices_for(unit) if o["office_type"] == otype or
                (otype == "city_council" and o["office_type"] in ("city_council_district", "city_council_at_large"))]
        if not offs:
            continue
        yrs = control_by_year(ed, offs)
        if not yrs:
            continue
        seats = sum(int(o["seats"]) if o["seats"].isdigit() else 1 for o in offs)
        first_terms = [t for o in offs for t in ed.terms_for(o["office_id"])]
        charts.append(party_timeline(fid, f"{label} seats by party", yrs, seats,
                                     subtitle=f"{yrs[0]['year']} to {yrs[-1]['year']}, {seats} seats",
                                     note=method, page=page, cite=c.cite_compact(_union(first_terms))))
    ga_rows = ed.table("general_assembly_control")
    ga_figs = []
    for chamber in ("House", "Senate"):
        rows = []
        src = []
        for r in sorted((r for r in ga_rows if r["chamber"] == chamber), key=lambda r: int(r["year"])):
            src.append(r)
            y = int(r["year"])
            rows.append({"label": f"{y}–{str(y + 1)[2:]}", "D": int(r["d_seats"]) if r["d_seats"] else 0,
                         "R": int(r["r_seats"]) if r["r_seats"] else 0, "O": int(r["other_seats"]) if r["other_seats"] else 0,
                         "total": int(r["total_seats"]), "super": r["supermajority_party"],
                         "status": r["status"], "unofficial": r["status"] == "unofficial"})
        if rows:
            ga_figs.append(_chamber_chart(f"control-ga-{chamber.lower()}", f"Indiana {chamber} seats by party", rows,
                                          page, cite=c.cite(_union(src)),
                                          note="Seat counts at the start of each two-year period. * The 2027 seat totals "
                                               "are not in the guide's data; 2026 results are unofficial. Two-thirds is "
                                               "the quorum threshold in the Indiana Constitution (Art. 4 sec. 11), per "
                                               "the source notes."))
    page.add(section("control", 1, "Party control over time",
                     h("p", None, "One chart per elected body with year-by-year data in the guide. The full range of the "
                                  "guide's data is shown for each; earlier years are listed under Gaps."),
                     h("h3", None, "Local bodies"), charts,
                     h("h3", None, "Indiana General Assembly (statewide)"),
                     h("p", None, "The General Assembly is the state legislature. Its whole membership is shown, not only "
                                  "the members from this county.", " ", status_badges(ga_rows, page)),
                     ga_figs,
                     scope="county", ed=ed))

    # ---- 2 mayors
    sb_tbl, sb_terms = _mayor_table(ed, page, "south-bend-mayor", "mayors-south-bend")
    m_tbl, m_terms = _mayor_table(ed, page, "mishawaka-mayor", "mayors-mishawaka")
    sb_first = next((t for t in sb_terms if parse_date(t["start"])), None)
    inc = next((t for t in ed.table("timeline") if t["date"].startswith("1865-05")), None)
    page.add(section("mayors", 2, "Mayors",
                     h("h3", None, f"South Bend: {len(sb_terms)} mayors since {sb_first['start'][:4] if sb_first else ''}"),
                     h("p", None, inc["description"], c.cite(inc["source_ids"]), " ", status_badge(inc["status"], page))
                     if inc else None,
                     h("p", None, f"The list has {len(sb_terms)} mayors, in the order of a secondary source that the "
                                  "fact-check matched row for row. Dates there conflict in a few places; rows marked low "
                                  "confidence carry the conflict in their notes.",
                       c.cite("GOV-023;COM-030")),
                     sb_tbl,
                     h("h3", None, f"Mishawaka: {len(m_terms)} mayors in the sources"),
                     h("p", None, "The guide has Mishawaka's mayors only from the 1960s on, and some dates and parties are "
                                  "missing. Earlier mayors are listed under Gaps."),
                     m_tbl,
                     scope="county", ed=ed))

    # ---- 3 turning points
    tl = [t for t in ed.table("timeline") if t.get("confidence") != "low"]
    tl.sort(key=lambda t: t["date"])
    items = []
    counts = Counter(t["category"] for t in tl)
    for t in tl:
        items.append(h("li", {"class": "tp-item", "data-cat": t["category"]},
                       h("p", {"class": "tp-meta mono"},
                         h("time", {"datetime": t["date"]}, fmt_date(t["date"], long=True)), " · ",
                         h("span", {"class": "tp-cat"}, CATEGORY_LABELS.get(t["category"], t["category"]))),
                       h("h3", {"class": "tp-title"}, t["title"]),
                       h("p", {"class": "tp-desc"}, t["description"], c.cite(t["source_ids"])),
                       h("p", {"class": "holder-badges"}, status_badge(t["status"], page))))
    keys = []
    for cat, blurb in (("political", "Political: elections, party control, mayors and vacancies."),
                       ("economic", "Economic: employers, plants, jobs and investment.")):
        keys.append(h("div", {"class": "tp-key", "id": cat},
                      h("p", None, blurb, f" {counts.get(cat, 0)} events."),
                      h("button", {"type": "button", "class": "btn btn-small", "data-tp-filter": cat,
                                   "id": f"tp-only-{cat}"}, f"Show only {CATEGORY_LABELS[cat].lower()} events")))
    filt = h("div", {"class": "tp-filter", "role": "group", "aria-label": "Filter turning points"},
             h("span", {"class": "mono muted"}, "Show: "),
             h("button", {"type": "button", "class": "btn btn-small", "data-tp-filter": "all", "aria-pressed": "true",
                          "id": "tp-all"}, f"All ({len(tl)})"),
             [h("button", {"type": "button", "class": "btn btn-small", "data-tp-filter": k, "aria-pressed": "false",
                           "id": f"tp-{k}"}, f"{v} ({counts.get(k, 0)})") for k, v in CATEGORY_LABELS.items() if counts.get(k)])
    page.add(section("turning-points", 3, "Turning points: political, economic and legal",
                     h("p", None, "Dated events from the guide's timeline, oldest first, mixing politics, government, "
                                  "court cases, the economy and population. Each is a sourced fact. Where an event's effect "
                                  "is described, it is in the words of the cited source; the guide doesn't add its own "
                                  "account of causes or effects. Events recorded with low confidence are left out and "
                                  "listed under Gaps."),
                     h("div", {"class": "tp-keys"}, keys), filt,
                     h("ol", {"class": "tp-list", "id": "tp-list"}, items),
                     scope="county", ed=ed))

    # ---- 4 population
    sb = next((g for g in iv.places if "South Bend" in iv.geo[g]["geo_name"]), None)
    pop_fig, pr = None, []
    if sb:
        for r in iv.rows:
            if r["geo_id"] == sb and r["indicator_id"] == "pop_total" and re.fullmatch(r"Decennial census \d{4}", r["vintage"]):
                pr.append(r)
        pr.sort(key=lambda r: r["vintage"])
        pop_fig = columns("history-sb-pop", f"South Bend population, {pr[0]['vintage'][-4:]} to {pr[-1]['vintage'][-4:]}",
                          [{"x": r["vintage"][-4:], "value": _f(r["value"]), "display": f"{_f(r['value']):,.0f}"} for r in pr],
                          subtitle="Decennial census counts", status=pr[0]["status"], page=page,
                          cite=c.cite(_union(pr)), note=pr[0]["notes"]) if pr else None
    peak = next((t for t in ed.table("timeline") if t["category"] == "population" and "peak" in t["title"].lower()), None)
    page.add(section("population", 4, "South Bend's population since 1850",
                     h("p", None, peak["description"], c.cite(peak["source_ids"]), " ", status_badge(peak["status"], page))
                     if peak else None,
                     pop_fig,
                     h("p", None, "More population figures, including the county and Mishawaka, are on ",
                       h("a", {"href": page.rel("community/people/index.html#who")}, "Who lives here"), "."),
                     scope="county", ed=ed))

    low = [t for t in ed.table("timeline") if t.get("confidence") == "low"]
    gaps = [page_gap(f"Pending verification: {t['title']} ({fmt_date(t['date'])})",
                     "Recorded with low confidence in timeline.csv, so it is not shown in the timeline. " + t["description"],
                     "Find a historian's or primary source and raise the confidence.") for t in low]
    gaps += ed.gaps(files=["gaps_gov"], pattern=r"party control|Mishawaka mayors|before 2010|before 2012|commissioner")
    gaps += ed.gaps(files=["gaps_indiana"], areas=["general_assembly_control"])
    gaps += community_gaps(ed, r"Economic history|AWS|UAW|Decennial population")
    gaps += ed.gaps(files=["gaps_results"], pattern=r"Pre-2010 South Bend mayor")
    page.finish(gaps=gaps)
    return page


# =============================================================================== history/people

def _parties(p) -> str:
    """Party labels; people.csv notes may name what a generic code stands for ('Party code O = Whig')."""
    named = {m.group(1): m.group(2).strip() for m in
             re.finditer(r"\b([A-Z]{1,2}) = ([A-Z][A-Za-z ]+?)(?=[;,.(]|$)", p.get("notes") or "")}
    return "; ".join(f"{named[x]} ({x})" if x in named else party_label(x) for x in split_ids(p.get("parties")))


def _person_tag(p) -> Markup:
    """Name plus party tag for a people.csv row. Falls back to the parties on the person's term rows; a note
    like 'Party code O = Whig' names what a generic code stands for."""
    codes = split_ids(p.get("parties"))
    if not codes:
        for t in p.get("_terms", []):
            if t.get("party") and t["party"] not in codes:
                codes.append(t["party"])
    named = {m.group(1): m.group(2).strip() for m in
             re.finditer(r"\b([A-Z]{1,2}) = ([A-Z][A-Za-z ]+?)(?=[;,.(]|$)", p.get("notes") or "")}
    return name_with_party(p["name"], ";".join(codes), labels=named)


def _first_year(p):
    m = re.search(r"\b(1[89]\d\d|20\d\d)\b", p.get("offices_summary", ""))
    return int(m.group(1)) if m else None


def _era(y):
    if y is None:
        return "unknown"
    if y < 1950:
        return "pre-1950"
    if y < 1980:
        return "1950-1979"
    if y < 2000:
        return "1980-1999"
    return "2000-present"


def _last_party(p):
    codes = split_ids(p.get("parties"))
    return codes[-1] if codes else ""


def _photo(ed, page, p, images):
    img = images.get(p.get("image_id") or "")
    if img:
        thumb = f"thumb_{img['image_id']}.jpg"
        has_thumb = (ed.root / "site" / "images" / thumb).is_file()
        local = img.get("local_file", "").replace("site/images/", "")
        src = page.rel("images/" + (thumb if has_thumb else local))
        cap_note = img["notes"].split(";")[0] if re.search(r"\b\d{4}\b", img.get("notes", "").split(";")[0]) else ""
        return h("figure", {"class": "person-photo"},
                 h("img", {"src": src, "alt": f"Photo of {p['name']}", "width": 320, "height": 400, "loading": "lazy",
                           "decoding": "async"}),
                 h("figcaption", {"class": "photo-credit"},
                   (cap_note + ". ") if cap_note else "", "Photo: ", img["credit"], ". ", img["license"], ". ",
                   h("a", {"href": img["file_page_url"], "target": "_blank", "rel": "noopener"}, "File page"),
                   page.cites.cite("PPL-035")))
    return h("figure", {"class": "person-photo person-photo-none"},
             h("div", {"class": "no-photo", "role": "img", "aria-label": "No licensed photo"},
               h("span", {"class": "no-photo-initials", "aria-hidden": "true"},
                 "".join(w[0] for w in re.findall(r"[A-Z][a-z]+", p["name"])[-2:]) or "?")),
             h("figcaption", {"class": "photo-credit"}, "No licensed photo in the guide's files."))


# ---- mechanical selection (TENURE, HIGHER, TURNING_POINT) -------------------------------------------

NICKNAMES = {"bob": "robert", "steve": "stephen", "pat": "patrick", "joe": "joseph", "mike": "michael",
             "tim": "timothy", "dave": "david", "pete": "peter", "jim": "james", "tony": "anthony",
             "jackie": "jacqueline", "rudy": "rudolph"}
HIGHER_RX = re.compile(r"U\.S\. (Representative|Senator|Secretary|Ambassador)|Vice President of the United States|"
                       r"Speaker of the U\.S\. House|Governor of Indiana|Attorney General of Indiana|"
                       r"Indiana Secretary of State|Treasurer of State|State Comptroller|Auditor of State|"
                       r"Secretary of Education|Superintendent of Public Instruction")
GA_RX = re.compile(r"\bIndiana (House|Senate)\b|state representative|state senator", re.I)
CITY_SEAT_RX = re.compile(r"^(?:Mayor of (South Bend|Mishawaka)|(South Bend|Mishawaka) (?:Common )?Council\b|"
                          r"(South Bend|Mishawaka) City Clerk|City Clerk of (South Bend|Mishawaka))")
COUNTY_SEAT_RX = re.compile(r"^St\. Joseph County (Prosecutor|Council|Commissioner|Sheriff|Auditor|Treasurer|Recorder|"
                            r"Clerk|Assessor|Coroner|Surveyor)|^(Judge of the )?(Circuit|Probate) Court")
TP_CATEGORIES = ("political", "government", "legal")
RESULT_SENTENCE_RX = re.compile(r"\d[\d,]* votes?\b|\d+(\.\d+)? percent|\breturns\b|\bvotes? to\b", re.I)


def _name_key(name: str):
    """(surname, given name) with initials dropped and common nicknames expanded, so 'Steve Luecke' and
    'Stephen Luecke' are the same person and 'B. Patrick Bauer' is not 'Burnie Bauer'."""
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z'-]*\.?", re.sub(r"\(.*?\)", "", name or ""))
             if not re.fullmatch(r"[A-Z]\.?", w) and w.lower().rstrip(".") not in ("jr", "sr", "ii", "iii", "dr")]
    if not words:
        return ("", "")
    given = words[0].lower().rstrip(".") if len(words) > 1 else ""
    return (words[-1].lower().rstrip("."), NICKNAMES.get(given, given))


def _office_segments(summary: str):
    """Split an offices_summary into (office text, parenthetical) pairs at top-level semicolons."""
    out, depth, cur = [], 0, ""
    for ch in summary or "":
        depth += ch == "("
        depth -= ch == ")"
        if ch == ";" and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    segs = []
    for seg in (x.strip() for x in out if x.strip()):
        m = re.match(r"^(.*?)\s*\((.*)\)\s*$", seg)
        segs.append((m.group(1), m.group(2)) if m else (seg, ""))
    return segs


def _seg_years(paren: str, now_year: int):
    years = [int(y) for y in re.findall(r"\b(1[89]\d\d|20\d\d)\b", paren)]
    if not years:
        return None
    if re.search(r"present|\bsince\b|first elected", paren):
        return years[0], now_year
    return (years[0], years[1]) if len(years) > 1 else None


def _government(office_text: str):
    if GA_RX.search(office_text):
        return "General Assembly"
    m = CITY_SEAT_RX.search(office_text)
    if m:
        return next(g for g in m.groups() if g)
    if COUNTY_SEAT_RX.search(office_text):
        return "St. Joseph County"
    return None


def _term_government(office_id: str):
    if office_id.startswith(("state-house", "state-senate")):
        return "General Assembly"
    if office_id.startswith("south-bend-") and not office_id.startswith("south-bend-schools"):
        return "South Bend"
    if office_id.startswith("mishawaka-"):
        return "Mishawaka"
    if office_id.startswith(("county-", "circuit-court", "probate-court", "superior-court")):
        return "St. Joseph County"
    return None


def _merged_years(spans):
    total, last = 0, None
    for a, b in sorted(spans):
        if last is None or a > last[1]:
            if last:
                total += last[1] - last[0]
            last = [a, b]
        else:
            last[1] = max(last[1], b)
    if last:
        total += last[1] - last[0]
    return total


def people_pool(ed):
    """Everyone in people.csv plus everyone in terms.csv, with TENURE, HIGHER and TURNING_POINT computed
    from the data and FIRST/FAMILY as recorded in people.csv. Returns (pool, tp_map): the people who meet
    at least one rule, and each timeline event with the people named in its title."""
    now_year = ed.as_of.year
    people = [dict(p) for p in ed.table("people")]
    by_key = {}
    for p in people:
        p["_terms"] = []
        by_key.setdefault(_name_key(p["name"]), p)
    offices = ed.offices
    for t in ed.table("terms"):
        o = offices.get(t["office_id"], {})
        if o.get("elected") != "yes" or t.get("status") == "unofficial":
            continue
        k = _name_key(t["person"])
        p = by_key.get(k)
        if p is None:
            p = {"person_id": "", "name": t["person"], "offices_summary": "", "parties": "", "criteria": "",
                 "in_office_now": "false", "summary": "", "documented_findings": "", "image_id": "",
                 "status": "", "confidence": "", "source_ids": "", "notes": "", "_terms": [], "_from_terms": True}
            by_key[k] = p
            people.append(p)
        p["_terms"].append(t)

    def term_span(t):
        st = parse_date(t["start"])
        en = parse_date(t["end"], end=True) if t.get("end") else None
        if st is None:
            return None
        return st.year, (en.year if en else now_year)

    for p in people:
        spans = {}
        for off, paren in _office_segments(p.get("offices_summary", "")):
            g, yrs = _government(off), _seg_years(paren, now_year)
            if g and yrs:
                spans.setdefault(g, []).append(yrs)
        for t in p["_terms"]:
            g, yrs = _term_government(t["office_id"]), term_span(t)
            if g and yrs:
                spans.setdefault(g, []).append(yrs)
        p["_tenure"] = {g: _merged_years(v) for g, v in spans.items()}
        if not p.get("parties") and p["_terms"]:
            # one party value per person across pages: a profile with no party takes the officeholder records' party
            p["parties"] = ";".join(dict.fromkeys(t["party"] for t in p["_terms"] if t.get("party")))
        crit = [k for k in split_ids(p.get("criteria")) if k not in COMPUTED_RULES]
        if any(v >= 16 for v in p["_tenure"].values()):
            crit.append("TENURE")
        if HIGHER_RX.search(p.get("offices_summary", "")):
            crit.append("HIGHER")
        p["_crit"] = crit

    # TURNING_POINT: named in a timeline title by surname, plus the given name when the surname is shared
    surnames = Counter(_name_key(p["name"])[0] for p in people)
    tp_map = []
    for ev in ed.table("timeline"):
        if ev.get("confidence") == "low" or ev.get("category") not in TP_CATEGORIES:
            continue
        words = {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z'-]*", ev["title"])}
        title_given = {NICKNAMES.get(w, w) for w in words}
        named = []
        for p in people:
            sur, given = _name_key(p["name"])
            if not sur or sur not in words:
                continue
            if surnames[sur] > 1 and given not in title_given:
                continue
            named.append(p)
        if named:
            tp_map.append((ev, named))
            for p in named:
                if "TURNING_POINT" not in p["_crit"]:
                    p["_crit"].append("TURNING_POINT")
    order = list(CRITERIA)
    for p in people:
        p["_crit"] = sorted(dict.fromkeys(p["_crit"]), key=order.index)
        if p.get("_from_terms"):
            _fill_from_terms(ed, p)
    pool = [p for p in people if p["_crit"]]
    return pool, tp_map


def _fill_from_terms(ed, p):
    """Card fields for someone who is in the officeholder records but has no research profile."""
    terms = sorted(p["_terms"], key=lambda t: parse_date(t["start"]) or parse_date("1800"))
    segs, parties = [], []
    for t in terms:
        title = ed.offices.get(t["office_id"], {}).get("title", t["office_id"])
        st = parse_date(t["start"])
        en = parse_date(t["end"], end=True) if t.get("end") else None
        yrs = f"{st.year}-{en.year}" if (st and en) else f"since {st.year}" if st else "dates not in sources"
        segs.append(f"{title} ({yrs})")
        if t.get("party") and t["party"] not in parties:
            parties.append(t["party"])
    p["offices_summary"] = "; ".join(dict.fromkeys(segs))
    p["parties"] = ";".join(parties)
    p["in_office_now"] = "true" if any(t in ed.current_terms(t["office_id"]) for t in terms) else "false"
    conf_rank = {"low": 0, "medium": 1, "high": 2}
    p["confidence"] = min((t.get("confidence") or "low" for t in terms), key=lambda c: conf_rank.get(c, 0))
    st_rank = ["official", "from_scan", "secondary", "single_source"]
    p["status"] = max((t.get("status") or "secondary" for t in terms),
                      key=lambda x: st_rank.index(x) if x in st_rank else len(st_rank))
    p["source_ids"] = _union(terms)
    p["summary"] = ""
    p["notes"] = "Offices and dates are from the guide's officeholder records; no profile has been written."


def _card_summary(p) -> str:
    """Cards carry no vote counts or vote shares: sentences that report them are left out (results are on the
    results and legislators pages)."""
    keep = [x for x in re.split(r"(?<=[.])\s+", p.get("summary") or "") if x and not RESULT_SENTENCE_RX.search(x)]
    return " ".join(keep)


def build_history_people(site):
    ed = site.ed
    page = site.page("history/people/index.html")
    c = page.cites
    people, tp_map = people_pool(ed)
    images = {r["image_id"]: r for r in ed.table("images")}
    toc = [("rules", "Selection rules"), ("people", "The people"), ("low-confidence", "Recorded with low confidence"),
           ("turning-points", "Turning-point names"), ("distribution", "Who the rules picked"), ("gaps", "Gaps"),
           ("sources", "Sources")]
    page.add(hero(page, "Reference · History", toc,
                  "People chosen by five published rules, applied the same way to everyone in the guide's data. "
                  "Being listed is not praise or criticism."))

    rules = h("dl", {"class": "rule-list"},
              [[h("dt", None, h("span", {"class": "crit-tag mono"}, CRITERIA_LABELS[k])), h("dd", None, v)]
               for k, v in CRITERIA.items()])
    page.add(section("rules", 1, "Selection rules",
                     h("p", None, "A person is included if the guide's data shows at least one of these. Tenure, Higher "
                                  "office and Turning point are computed by the build from the office, term and timeline "
                                  "records, for everyone in them; First and Family are taken from the cited sources as "
                                  "recorded. Nobody is added or left out by judgment."),
                     rules,
                     h("p", None, "Current officeholders are included when they meet a rule; their cards carry an ",
                       h("span", {"class": "badge badge-inoffice"}, "IN OFFICE"), " badge. Cards are ordered by the "
                       "first year of documented service, then by name, never by party. Every card has the same "
                       "fields, and no card reports vote counts or vote shares. Official findings (court rulings, "
                       "investigations, settlements) appear only when documented, and are attributed to the reporting "
                       "source."),
                     h("p", None, "Photos appear only where the license allows reuse, with a credit line; everyone else "
                                  "gets the same no-photo panel.")))

    def is_low(p):
        return p.get("confidence") == "low"
    crit = lambda p: p["_crit"]
    pending = [p for p in people if is_low(p) and set(crit(p)) <= {"FIRST"}]
    low_table = [p for p in people if is_low(p) and p not in pending]
    shown = [p for p in people if not is_low(p)]
    shown.sort(key=lambda p: (_first_year(p) or 9999, p["name"]))
    low_table.sort(key=lambda p: (_first_year(p) or 9999, p["name"]))

    items = []
    for p in shown:
        in_office = p.get("in_office_now") == "true"
        parties = _parties(p) or "Party not documented in the sources"
        findings = p.get("documented_findings") or ""
        summary = _card_summary(p)
        badges = [status_badge(p["status"], page)]
        anchor = p["person_id"].lower() if p.get("person_id") else re.sub(r"[^a-z0-9]+", "-", p["name"].lower()).strip("-")
        card = h("article", {"class": "card person-card"},
                 _photo(ed, page, p, images),
                 h("div", {"class": "person-body"},
                   h("p", {"class": "person-flags"},
                     h("span", {"class": "badge badge-inoffice"}, "IN OFFICE") if in_office else
                     h("span", {"class": "badge badge-former"}, "NOT IN OFFICE")),
                   h("p", {"class": "card-title person-name"}, _person_tag(p), c.cite(_people_sources(p))),
                   h("dl", {"class": "person-fields"},
                     h("dt", None, "Offices"), h("dd", None, p["offices_summary"]),
                     h("dt", None, "Party"), h("dd", None, parties),
                     h("dt", None, "Rules met"), h("dd", None, join([h("span", {"class": "crit-tag mono"},
                                                                        CRITERIA_LABELS.get(k, k)) for k in crit(p)], " ")),
                     h("dt", None, "Summary"),
                     h("dd", None, summary if summary else h("span", {"class": "muted"},
                                                             "No profile written yet; offices and dates are from "
                                                             "the guide's officeholder records.")),
                     h("dt", None, "Official findings"),
                     h("dd", None, findings if findings else h("span", {"class": "muted"}, "None documented in the sources."))),
                   h("p", {"class": "holder-badges"}, badges)))
        segs = _office_segments(p["offices_summary"])
        first = segs[0][0] if segs else p["offices_summary"]
        if len(segs) > 1:
            first += f" and {len(segs) - 1} more"
        yrs = [int(y) for y in re.findall(r"\b(1[89]\d\d|20\d\d)\b", p["offices_summary"])]
        span = ""
        if yrs:
            end = "present" if in_office else str(max(yrs))
            span = f"{min(yrs)}–{end}" if end != str(min(yrs)) else str(min(yrs))
        rules = ", ".join(CRITERIA_LABELS.get(k, k) for k in crit(p))
        items.append({"key": anchor, "name": p["name"], "item_id": f"person-{anchor}",
                      "facts": [f"{first}, {span}" if span else first, _parties(p) or "Party not documented", f"Rule: {rules}"],
                      "status": p["status"],
                      "search": p["offices_summary"] + " " + rules,
                      "attrs": {"data-tf-era": _era(_first_year(p)),
                                "data-tf-office": "now" if in_office else "former"},
                      "body": card})
    era_opts = [(e, e.replace("-", "–") if e != "unknown" else "Year not documented")
                for e in ["pre-1950", "1950-1979", "1980-1999", "2000-present", "unknown"]
                if any(i["attrs"]["data-tf-era"] == e for i in items)]
    page.add(section("people", 2, f"The people ({len(shown)})",
                     h("p", None, f"{len(shown)} people meet a rule with medium or high confidence in the data. "
                                  f"{len(low_table)} more are listed in the table below with a low-confidence flag, and "
                                  f"{len(pending)} whose only qualifying claim is an unverified first are listed under "
                                  "Gaps as pending verification. Each row opens to the full card: photo and credit, "
                                  "offices, party, rules met, summary, findings and sources. Rows run by first year of "
                                  "documented service, then name, never by party."),
                     one_bar("person", "people", "Pick a person to open the card."),
                     entity_list("people-list", items, noun="person", plural="people",
                                 search="Find a name, office or rule",
                                 controls=[{"key": "era", "label": "First documented service", "all": "All eras",
                                            "options": era_opts},
                                           {"key": "office", "label": "Holds office now", "all": "Either",
                                            "options": [("now", "In office now"), ("former", "Not in office")]}],
                                 label="People the rules picked"),
                     scope="county", ed=ed))

    lrows = []
    for p in low_table:
        lrows.append([_person_tag(p), p["offices_summary"],
                      _parties(p) or "Party not documented",
                      ", ".join(CRITERIA_LABELS.get(k, k) for k in crit(p)),
                      "Yes" if p.get("in_office_now") == "true" else "No",
                      _safe_note(p) or "See the cited sources.",
                      h("span", {"class": "badge-row"}, status_badge(p["status"], page), status_badge("low", page),
                        c.cite(_people_sources(p)))])
    page.add(section("low-confidence", 3, "Recorded with low confidence",
                     h("p", None, "These people meet a rule in the guide's data, but the record behind it is thin (for "
                                  "example, dates or party not documented, or one search summary). They are kept for "
                                  "completeness and shown only here, flagged."),
                     data_table("people-low", ["Name", "Offices", "Party", "Rules met", "In office", "Why low confidence",
                                               "Status"], lrows, caption="People recorded with low confidence",
                                min_width="60rem") if lrows else h("p", None, "None."),
                     scope="county", ed=ed))

    # ---- the event-to-person mapping behind TURNING_POINT, published so the rule can be checked
    tprows = [[fmt_date(ev["date"]), ev["title"], join([_person_tag(p) for p in named], ", "),
               h("span", None, status_badge(ev["status"], page), c.cite(ev["source_ids"]))] for ev, named in tp_map]
    page.add(section("turning-points", 4, "Turning-point names",
                     h("p", None, "Every political, government or legal event in the timeline whose title names a person "
                                  "in the guide's data, and the person it names. A shared surname counts only with the "
                                  "given name. ", status_badge("computed", page, "Matched by the build from timeline.csv titles.")),
                     data_table("people-turning-points", ["Date", "Event", "Person named", "Status"], tprows,
                                caption="Timeline events and the people named in their titles", min_width="40rem")
                     if tprows else h("p", None, "None."),
                     scope="county", ed=ed))

    # ---- distribution (everyone the rules picked: shown, flagged and pending)
    party_n = Counter(_last_party(p) or "unknown" for p in people)
    era_n = Counter(_era(_first_year(p)) for p in people)
    eras = ["pre-1950", "1950-1979", "1980-1999", "2000-present", "unknown"]
    parties = [k for k in ("D", "R", "L", "O", "I", "NP") if party_n.get(k)] + (["unknown"] if party_n.get("unknown") else [])
    plabel = lambda k: "Not documented" if k == "unknown" else party_label(k)
    cross = Counter((_era(_first_year(p)), _last_party(p) or "unknown") for p in people)
    xrows = [[e.replace("-", "–") if e != "unknown" else "Year not documented"] +
             [str(cross.get((e, k), 0)) for k in parties] + [str(era_n.get(e, 0))] for e in eras]
    xrows.append(["All eras"] + [str(party_n.get(k, 0)) for k in parties] + [str(len(people))])
    office_n = Counter(("In office" if p.get("in_office_now") == "true" else "Not in office", _last_party(p) or "unknown")
                       for p in people)
    orows = [[g] + [str(office_n.get((g, k), 0)) for k in parties] +
             [str(sum(office_n.get((g, k), 0) for k in parties))] for g in ("In office", "Not in office")]
    # the hand-counted skew rows in gaps_community_people.csv predate the computed selection, so they are not shown
    stale = ed.gaps(files=["gaps_community_people"], areas=["people"],
                    pattern=r"^Distribution|No Republican|^Excluded because no criterion")
    skew_items = [h("li", None, f"{party_n.get('D', 0)} last held office as Democrats, {party_n.get('R', 0)} as "
                                f"Republicans and {party_n.get('unknown', 0)} have no documented party."),
                  h("li", None, "Republican officeholders of 1980-2012 in county and city government, General Assembly "
                                "members before 2010, and Mishawaka's mayors before 1963 were not fully researched; the "
                                "rules can only pick up people who are in the guide's data."),
                  h("li", None, f"{era_n.get('pre-1950', 0)} people first served before 1950; coverage of 1870-1950 "
                                "is thin.")]
    page.add(section("distribution", 5, "Who the rules picked, by party and era",
                     h("p", None, f"Counts cover all {len(people)} people the rules picked, including the flagged and "
                                  "pending ones. Party is the last party documented; era is the first documented year "
                                  "of service. ",
                       status_badge("computed", page, "Counted by the guide from the selection above.")),
                     data_table("people-distribution", ["First documented service"] + [plabel(k) for k in parties] + ["Total"],
                                xrows, caption="People by era and last documented party",
                                numeric=tuple(range(1, len(parties) + 2)), min_width="36rem"),
                     data_table("people-in-office", ["Now"] + [plabel(k) for k in parties] + ["Total"], orows,
                                caption="People by whether they hold office now and last documented party",
                                numeric=tuple(range(1, len(parties) + 2)), min_width="36rem"),
                     callout(h("p", None, h("strong", None, "Why the counts skew. "),
                               "The counts reflect what the research found, not who mattered more."),
                             h("ul", None, skew_items)),
                     scope="county", ed=ed))

    gaps = [page_gap(f"Pending verification: {p['name']}",
                     f"Only qualifying claim is a 'first' recorded with low confidence ({p['status'].replace('_', ' ')}): "
                     f"{p['offices_summary']}. Not shown until re-sourced.",
                     "Read the cited source in full or find a second source, then raise the confidence.") for p in pending]
    gaps += [g for g in ed.gaps(files=["gaps_community_people"], areas=["people", "images"]) if g not in stale]
    gaps.append(page_gap("Legislators and county and city officeholders before the guide's term records begin",
                         "Tenure is computed only from the terms the guide holds. General Assembly members for the "
                         "districts touching the county before 2010 (for example Joe Zakas, Senate District 11, and Bob "
                         "Kovach, Senate District 11 in 1974-1978) and county officeholders before about 2010 are mostly "
                         "not in terms.csv, so people who would meet the Tenure rule may be missing, in every party.",
                         "Fill terms.csv from iga.in.gov rosters and Ballotpedia for 1970-2026; the rules then pick them up."))
    page.finish(gaps=gaps)
    return page


PAGES = {
    "community/index.html": build_community_index,
    "community/people/index.html": build_people,
    "community/income-and-work/index.html": build_income_work,
    "community/housing-and-education/index.html": build_housing,
    "community/research-on-voting/index.html": build_research,
    "history/index.html": build_history,
    "history/people/index.html": build_history_people,
}
