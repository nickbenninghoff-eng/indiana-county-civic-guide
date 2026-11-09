"""Campaign-money map for money/campaigns/index.html: a race-type filter over boundary and district layers, shaded by
the spending reported for each area's latest election, with the side panel of the boundary map.

    dsets = district_sets(ed, races)                       # official district layers matched to races (manifest-driven)
    layers = map_layers(ed, shapes, dsets, areas, races, state)   # every layer: shapes, values, panel entries
    campaign_map(page, ed, shapes, layers)                 -> Markup (.cmap: type filter + tabs + <svg> + legend + panel)

Reuses the boundary map: the root, tab, layer, area-link and panel markup of civic/map.py, so static/js/map.js gives
hover, focus, touch select-then-open and the panel; static/js/campaigns_map.js adds the race-type row and filters the
summary list. Shading is the one neutral teal ramp of civic/shading.py (never party colour). District layers come from
data/editions/<ed>/derived/district_shapes.json (tools/build_district_shapes.py, driven by
sources/boundaries/districts/manifest.csv); a set with no file, or a race with no set, is listed under its government
instead, and the legend says so. Boundaries are never drawn by the guide.
"""
from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

from .campaign_money import STATE_AREA, TYPES, party_parts, usd, usd_round, ytd_uses
from .components import party_label
from .data import fmt_date, split_ids
from .html import Markup, h, json_script
from .map import _label_boxes, shade_defs
from .shading import classify, shade_class, shade_legend

AREA_LAYER = {"county": "county", "courts": "courts", "city": "place", "town": "place", "township": "township",
              "school": "school"}
# district sets: office pattern -> (sub-layer id, tab label). Both cities' council districts share one sub-layer.
SUBLAYER = {"County Commissioner District {d}": ("commissioners", "Commissioner districts"),
            "County Council District {d}": ("council", "Council districts"),
            "South Bend Common Council District {d}": ("council", "Council districts"),
            "Mishawaka Common Council District {d}": ("council", "Council districts"),
            "State Representative District {d}": ("house", "Indiana House districts"),
            "State Senator District {d}": ("senate", "Indiana Senate districts")}
AREA_TAB = {"county": "Countywide offices", "courts": "Whole county", "city": "Cities", "town": "Towns",
            "township": "Townships", "school": "School corporations"}
# what the guide knows about each district set, beyond the manifest (said on the legend and in the panel)
SET_NOTES = {
    "county-commissioner-2022": "County map: the amended districts adopted on March 1, 2022 (the redistricting "
                                "settlement), checked against the 2024 results by precinct; in use for 2022, 2024 and 2026.",
    "county-council-2022": "County map: the amended districts adopted on March 1, 2022 (the redistricting settlement), "
                           "checked against the 2024 results by precinct; in use for 2022, 2024 and 2026.",
    "south-bend-council-2022": "South Bend map: Ordinance 10906-22, which governed the 2023 election.",
    "mishawaka-council-2022": "Mishawaka map: the districts the city posts as its current boundaries (2023). Which "
                              "map applied in 2023 is not confirmed against an ordinance.",
    "in-house-2021": "Indiana House districts from the 2021 redistricting (2022 to 2030). Districts reach past the "
                     "county line; the map draws only the part inside the county.",
    "in-senate-2021": "Indiana Senate districts from the 2021 redistricting (2022 to 2030). Districts reach past the "
                      "county line; the map draws only the part inside the county.",
}
NO_SHAPES = {
    "school": "South Bend Community School Corporation board districts have no official boundary file the guide can "
              "use (the posted map is an image), so its district races are listed under the school corporation. "
              "Penn-Harris-Madison's township seats are residency seats elected by the whole corporation, so they "
              "are not separate shapes.",
    "town": "Walkerton's wards are defined by street descriptions; no official boundary file was found, so ward races "
            "are listed under the town.",
}
SUM_NOTE = "Sums of several reports are the guide's own arithmetic (COMPUTED)."
SUPPORT_NOTE = "Money reported is not a measure of support and says nothing about how people voted."


def load_district_shapes(ed, shapes: dict | None) -> dict | None:
    p = Path(ed.root) / "data" / "editions" / ed.edition_id / "derived" / "district_shapes.json"
    if not p.is_file():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    if shapes and [round(float(v), 1) for v in data.get("viewBox", [])] != [round(float(v), 1) for v in shapes["viewBox"]]:
        ed.warnings.append("campaigns map: district_shapes.json viewBox differs from map_shapes.json; district layers "
                           "left out (rerun tools/build_district_shapes.py)")
        return None
    return data


def _year(v) -> int | None:
    try:
        return int(str(v)[:4])
    except (TypeError, ValueError):
        return None


def district_sets(ed, races: list[dict], dshapes: dict | None) -> list[dict]:
    """Manifest sets with shapes, each matched to the races it draws: for every district, the latest race whose
    office is the set's office pattern for that district and whose election year is inside the set's years."""
    out = []
    if not dshapes:
        return out
    for sid, rec in dshapes.get("sets", {}).items():
        pat = rec.get("office_pattern", "")
        if not rec.get("items") or "{d}" not in pat:
            continue
        lo, hi = _year(rec.get("first_election")) or 0, _year(rec.get("last_election")) or 9999
        state = pat.startswith("State ")
        typ = "state" if state else None
        by_d = {}
        for r in races:
            if not r["district"] or not (lo <= r["date"].year <= hi):
                continue
            if r["office"] == pat.replace("{d}", r["district"]):
                cur = by_d.get(r["district"])
                if cur is None or r["date"] > cur["date"]:
                    by_d[r["district"]] = r
                typ = typ or r["type"]
        if typ is None:
            ed.warnings.append(f"campaigns map: district set {sid} matches no race; left off the map")
            continue
        sub, label = SUBLAYER.get(pat, (sid, f"{sid} districts"))
        out.append({"id": sid, "type": typ, "sub": sub, "sub_label": label, "rec": rec, "races": by_d,
                    "note": SET_NOTES.get(sid, rec.get("notes", "")), "source_ids": rec.get("source_ids", "")})
    return out


# ------------------------------------------------------------------------------------------- panel text
def _party_line(x: dict) -> str:
    """By-party sums of a race or an area, each with how many of the party's candidates it covers."""
    if not x["by_party"]:
        return ""
    return "; ".join(party_parts(x["by_party"], x["party_counts"], party_label))


DATE_WORDS = {"date-read": "a report's dates are read as its transcription note corrects them",
              "date-conflict": "the dates on two reports disagree with their figures or cash (both are counted)",
              "date-doubt": "a year on a report may be miswritten (kept as written)"}


def date_caveats(race: dict, ytd: bool = True) -> list[str]:
    """One caveat per candidate whose figures rest on a date the guide reads, doubts or finds in conflict."""
    out = []
    for c in race["candidates"]:
        why = [w for f, w in DATE_WORDS.items() if f in c.get("flags", set())]
        if why:
            out.append(f"{c['name']}: " + "; ".join(why) + ". Details on the page.")
    if not ytd:
        return out
    # year-to-date figures, grouped by reason, so a year-to-date figure is never shown without saying so
    groups: OrderedDict = OrderedDict()
    for c in race["candidates"]:
        for u in ytd_uses(c.get("committees", [])):
            g = groups.setdefault(u["why"], [])
            name = c["name"] + ("" if u["clean"] else " (form doesn't reconcile; as written)")
            if name not in g:
                g.append(name)
    for why, names in groups.items():
        out.append(f"Year-to-date figure from the filer's latest report for {', '.join(names)}: {why}.")
    return out


def _through(to: str) -> str:
    return f" (reports through {fmt_date(to)})" if to else ""


def _el_words(ed, eid: str) -> str:
    el = ed.elections.get(eid) or {}
    return f"{eid[:4]} general election ({fmt_date(el.get('date', ''))})" if el else eid


def cand_label(c: dict) -> str:
    p = c["party"]
    return f"{c['name']} ({p})" if p else c["name"]


def candidate_bars(race: dict) -> list:
    """Each candidate's whole-cycle spending as a share of the race total, in ballot order (never by amount)."""
    tot = race["spent"] or 0
    out = []
    for c in race["candidates"]:
        if not c["committees"]:
            out.append([cand_label(c), "no reports on file", 0, ""])
        elif c["spent"] is None:
            out.append([cand_label(c), "reports can't be added up", 0, ""])
        else:
            share = c["spent"] / tot * 100 if tot else 0.0
            tag = "" if not c["missing"] else ", incomplete"
            out.append([cand_label(c) + tag, f"{share:.0f}%", round(share, 1), usd_round(c["spent"])])
    return out


def race_bars(races: list[dict]) -> list:
    tot = sum(r["spent"] or 0 for r in races)
    out = []
    for r in races:
        lab = r["office"] + ("" if r["complete"] else " (incomplete)")
        if r["spent"] is None:
            out.append([lab, "no reports on file", 0, ""])
        else:
            share = r["spent"] / tot * 100 if tot else 0.0
            out.append([lab, f"{share:.0f}%", round(share, 1), usd_round(r["spent"])])
    return out


def record_line(races: list[dict]) -> str:
    inc = [r for r in races if not r["complete"]]
    if not races:
        return "No race in the guide's 2023 to 2026 results"
    if not inc:
        return "Complete: every expected report is on file for every candidate"
    if len(races) == 1:
        return "Incomplete: " + " ".join(races[0]["reasons"][:2]) + (" More on the page." if len(races[0]["reasons"]) > 2 else "")
    return f"Incomplete: {len(inc)} of {len(races)} races are missing at least one expected report"


def race_entry(ed, page, race: dict, href: str, d: str, layer: str, extra_cav=()) -> dict:
    facts = [["Election", _el_words(ed, race["general_eid"])],
             ["Spent, all candidates", (usd(race["spent"]) + _through(race["latest_to"])) if race["spent"] is not None
              else "No reports on file for any candidate"]]
    if race["by_party"]:
        facts.append(["By party", _party_line(race)])
    if race["raised"] is not None:
        facts.append(["Raised, all candidates", usd(race["raised"])])
    facts.append(["Record", record_line([race])])
    cav = list(extra_cav) + date_caveats(race)
    return {"n": race["office"], "t": f"{TYPES[race['type']]} race" + (" · uncontested" if race["uncontested"] else ""),
            "f": facts, "bars": [["Spending by candidate (ballot order; share of the race total)", candidate_bars(race)]],
            "cav": cav, "note": "", "href": href, "l": layer, "d": d,
            "open": "See the candidates and their reports"}


def area_entry(ed, page, area: dict, href: str, d: str, layer: str, extra_cav=()) -> dict:
    latest = area["latest_races"]
    facts = []
    if not latest:
        facts.append(["Latest election", "No race for this government in the guide's 2023 to 2026 results"])
    else:
        facts.append(["Latest election", f"{_el_words(ed, area['latest'])}: {len(latest)} race{'s' if len(latest) != 1 else ''}"])
        facts.append(["Spent, all candidates", (usd(area["spent"]) + _through(area["latest_to"])) if area["spent"] is not None
                      else "No reports on file for any candidate"])
        if area["by_party"]:
            facts.append(["By party", _party_line(area)])
        if area["raised"] is not None:
            facts.append(["Raised, all candidates", usd(area["raised"])])
        facts.append(["Record", record_line(latest)])
    older = [r for r in area["races"] if r["general_eid"] != area["latest"]]
    if len(latest) == 1:
        cav = list(extra_cav) + date_caveats(latest[0])
    else:
        cav = list(extra_cav) + [x for r in latest for x in date_caveats(r, ytd=False)]
        n = sum(1 for r in latest for c in r["candidates"] if ytd_uses(c.get("committees", [])))
        if n:
            cav.append(f"{n} candidate{'s' if n != 1 else ''}' figures use the year-to-date column of the filer's latest "
                       "report, because earlier reports of the year aren't on file; the page says which.")
    if older:
        yrs = sorted({r["general_eid"][:4] for r in older}, reverse=True)
        cav.append(f"Also on its page: {len(older)} race{'s' if len(older) != 1 else ''} last held in {', '.join(yrs)}.")
    bars = []
    if len(latest) == 1:
        bars = [["Spending by candidate (ballot order; share of the race total)", candidate_bars(latest[0])]]
    elif latest:
        bars = [["Spending by race (share of the total)", race_bars(latest)]]
    return {"n": area["name"], "t": TYPES[area["type"]] + (f" · {area['latest'][:4]}" if area["latest"] else ""),
            "f": facts, "bars": bars, "cav": cav, "note": "", "href": href, "l": layer,
            "d": d, "open": "See every race and report"}


def state_entry(ed, page, district: str, rows: list[dict], share, href: str, d: str, layer: str) -> dict:
    years = sorted({r["year"] for r in rows}, reverse=True)[:2]
    facts = []
    for com in OrderedDict((r["committee"], None) for r in sorted(rows, key=lambda r: r["candidate"])):
        rs = {r["year"]: r for r in rows if r["committee"] == com}
        any_r = next(iter(rs.values()))
        parts = []
        for y in years:
            r = rs.get(y)
            parts.append(f"{y} filings: raised {usd(_c(r['receipts']))}, spent {usd(_c(r['expenditures']))}" if r
                         else f"{y} filings: none in the data")
        facts.append([f"{any_r['candidate']} ({any_r['party']})", "; ".join(parts)])
    office = "Indiana House" if district.startswith("HD") else "Indiana Senate"
    cav = ["Filing-year basis: each figure adds up the items on reports filed in that calendar year. It is not a race "
           "or election-cycle total, and the latest year is partial.",
           "Only the committees of the district's members and 2026 candidates in the guide's data are included, not "
           "every opponent, so the figures are not added up for the district."]
    if share is not None:
        cav.append(f"About {share * 100:.0f}% of the county's area is in this district; the district reaches past the "
                   "county line, and only the part inside the county is drawn.")
    return {"n": f"{office} District {district[2:]}", "t": "State legislature · filing-year basis", "f": facts or
            [["Committees", "None in the guide's data"]], "cav": cav, "note": "", "href": href, "l": layer, "d": d,
            "open": "See the district's committees"}


def _c(v):
    from .campaign_money import cents
    return cents(v)


# ------------------------------------------------------------------------------------------- layers
def map_layers(ed, page, shapes: dict, dsets: list[dict], areas: OrderedDict, cf_state: list[dict]) -> list[dict]:
    """Every map layer in TYPES order: the government layer of each race type, then its district layers.
    Each layer: id, type, label, shapes [{uid, d, href, aria, entry, value, label point}], legend data."""
    layers = []
    by_unit = {a["unit"]: a for a in areas.values()}
    units = ed.units
    for typ in TYPES:
        if typ in AREA_LAYER:
            items = []
            key = AREA_LAYER[typ]
            if key in ("county", "courts"):
                a = areas["county" if typ == "county" else "courts"]
                items.append(_area_item(ed, page, a, shapes["county"]["d"], typ, None))
            else:
                for it in shapes["layers"].get(key, []):
                    uid = it.get("id")
                    u = units.get(uid) if uid else None
                    if not u or u["unit_type"] not in {"city": ("city",), "town": ("town",), "township": ("township",),
                                                       "school": ("school_corporation",)}[typ]:
                        continue
                    items.append(_area_item(ed, page, by_unit[uid], it["d"], typ, it))
            layers.append(_finish_layer(typ, typ, AREA_TAB[typ], items, "area"))
        for ds in [s for s in dsets if s["type"] == typ]:
            lid = f"{typ}-{ds['sub']}"
            existing = next((L for L in layers if L["id"] == lid), None)
            items = []
            for it in ds["rec"]["items"]:
                dist = it["district"]
                uid = f"{lid}:{ds['id']}:{dist}"
                if typ == "state":
                    rows = [r for r in cf_state if r["district"] == dist]
                    href = page.rel(f"money/campaigns/{STATE_AREA}/index.html#{dist.lower()}")
                    entry = state_entry(ed, page, dist, rows, it.get("county_share"), href, it["d"], lid)
                    aria = f"{entry['n']}: {len(rows) and len({r['committee'] for r in rows})} committees in the data, filing-year basis. Open."
                    items.append({"uid": uid, "d": it["d"], "href": href, "aria": aria, "entry": entry, "value": None,
                                  "plain": True, "label": it["label"], "text": dist, "label_r": it["label_r"]})
                    continue
                race = ds["races"].get(dist)
                if race is None:
                    href = page.rel(f"money/campaigns/{_area_of_set(ds, areas)}/index.html")
                    entry = {"n": ds["rec"]["office_pattern"].replace("{d}", dist), "t": "No race", "f": [
                        ["Race", "No race for this district in the guide's 2023 to 2026 results"]], "cav": [ds["note"]],
                        "note": "", "href": href, "l": lid, "d": it["d"], "open": "Open the government's page"}
                    items.append({"uid": uid, "d": it["d"], "href": href, "aria": f"{entry['n']}: no race. Open.",
                                  "entry": entry, "value": None, "label": it["label"], "text": dist,
                                  "label_r": it["label_r"]})
                    continue
                href = page.rel(f"money/campaigns/{race['area']}/index.html#r-{race['id']}")
                entry = race_entry(ed, page, race, href, it["d"], lid, extra_cav=[ds["note"]])
                items.append({"uid": uid, "d": it["d"], "href": href, "entry": entry, "label": it["label"],
                              "text": dist, "label_r": it["label_r"],
                              "value": race["spent"] / 100 if race["spent"] is not None else None,
                              "complete": race["complete"], "year": race["general_eid"][:4],
                              "aria": _aria(race["office"], race["spent"], race["general_eid"][:4], race["complete"])})
            if existing:
                existing["shapes"] += items
                existing["sets"].append(ds)
                _shade(existing)
            else:
                L = _finish_layer(lid, typ, ds["sub_label"], items, "district")
                L["sets"] = [ds]
                layers.append(L)
    return layers


def _area_of_set(ds, areas) -> str:
    r = next(iter(ds["races"].values()), None)
    return r["area"] if r else "county"


def _aria(name, spent, year, complete) -> str:
    if spent is None:
        return f"{name}: no reports on file for the {year} election. Open its page."
    return (f"{name}: {usd(spent)} spent by all candidates for the {year} election, "
            f"{'complete' if complete else 'incomplete'} record. Open its page.")


def _area_item(ed, page, a, d, typ, it) -> dict:
    href = page.rel(f"money/campaigns/{a['id']}/index.html")
    entry = area_entry(ed, page, a, href, d, typ, extra_cav=[NO_SHAPES[typ]] if typ in NO_SHAPES and any(
        r["district"] for r in a["races"]) else [])
    year = a["latest"][:4] if a["latest"] else ""
    short = a["name"].replace("City of ", "").replace("Town of ", "").replace(" Township", "")
    return {"uid": f"{typ}:{a['id']}", "d": d, "href": href, "entry": entry,
            "value": a["spent"] / 100 if a["spent"] is not None else None, "complete": a["complete"], "year": year,
            "aria": _aria(a["name"], a["spent"], year, a["complete"]) if a["latest"] else
            f"{a['name']}: no race in the guide's 2023 to 2026 results. Open its page.",
            "label": it["label"] if it else None, "label_r": it["label_r"] if it else 99,
            "bbox": it.get("bbox") if it else None, "text": short}


def _shade(L: dict) -> None:
    vals = {s["uid"]: s.get("value") for s in L["shapes"] if not s.get("plain")}
    cls = classify(vals)
    for s in L["shapes"]:
        s["shade"] = None if s.get("plain") else cls["shade"][s["uid"]]
    L["classes"] = cls


def _finish_layer(lid, typ, label, items, kind) -> dict:
    L = {"id": lid, "type": typ, "label": label, "shapes": items, "kind": kind, "sets": []}
    _shade(L)
    return L


# ------------------------------------------------------------------------------------------- markup
def _legend(L: dict, ed, on: bool) -> Markup:
    plain = all(s.get("plain") for s in L["shapes"])
    attrs = {"class": "cmap-mlegend" + (" is-on" if on else ""), "data-layer": L["id"]}
    if plain:
        return h("div", attrs, h("p", {"class": "cmap-mlegend-h"}, "Not shaded"),
                 h("p", {"class": "cf-legend-note"}, "State legislative figures are by filing year for each listed "
                                                     "committee, not race totals, so the districts are not shaded or "
                                                     "compared."),
                 [h("p", {"class": "cf-legend-note"}, s["note"]) for s in L["sets"]])
    years = sorted({s["year"] for s in L["shapes"] if s.get("year")}, reverse=True)
    title = "Spent by all candidates, latest election" + (f" ({' or '.join(years)})" if years else "")
    n = sum(1 for s in L["shapes"] if s.get("value") is not None)
    inc = sum(1 for s in L["shapes"] if s.get("value") is not None and not s.get("complete"))
    notes = []
    if n:
        notes.append(h("p", {"class": "cf-legend-note"},
                       f"{inc} of {n} shaded {'areas have' if n != 1 else 'area has'} an incomplete record: at least one "
                       "expected report is not on file, so the figure is a floor, not a final total. The panel says "
                       "which." if inc else "Every shaded area has every expected report on file."))
    notes += [h("p", {"class": "cf-legend-note"}, s["note"]) for s in L["sets"]]
    if L["kind"] == "area" and L["type"] in NO_SHAPES:
        notes.append(h("p", {"class": "cf-legend-note"}, NO_SHAPES[L["type"]]))
    return h("div", attrs, shade_legend(title, L["classes"], none_label="No reports on file, or no race",
                                        attrs={"class": "cf-lg-inner"}), notes)


def campaign_map(page, ed, shapes: dict, layers: list[dict], default_layer: str) -> Markup:
    vb = shapes["viewBox"]
    data, groups, tabs, legends = {}, [], [], []
    # township background (behind cities, towns and council districts): drawn once in <defs>, reused with <use>
    back_def = h("g", {"id": "cf-back"}, [h("path", {"d": t["d"], "class": "cmap-s cmap-mm-back"})
                                          for t in shapes["layers"]["township"]])
    for L in layers:
        on = L["id"] == default_layer
        paths, labels = [], []
        for s in L["shapes"]:
            # the panel entry leaves out the path: static/js/map.js reads it from the shape for the highlight
            data[s["uid"]] = {k: v for k, v in s["entry"].items() if k != "d"}
            cls = "cmap-s cf-plain" if s.get("plain") else f"cmap-s cmap-mm {shade_class(s.get('shade'))}"
            kids = [h("path", {"d": s["d"], "class": cls})]
            if s.get("label_r", 99) < 6 and s.get("label"):
                kids.append(h("circle", {"cx": s["label"][0], "cy": s["label"][1], "r": 5,
                                         "class": "cmap-dot cmap-mm-dot " + ("cf-plain" if s.get("plain") else shade_class(s.get("shade")))}))
            paths.append(h("a", {"href": s["href"], "class": "cmap-a", "data-uid": s["uid"], "aria-label": s["aria"]}, kids))
        if L["kind"] == "district":
            for s in L["shapes"]:
                if s.get("label"):
                    labels.append(h("text", {"x": s["label"][0], "y": s["label"][1] + 3, "text-anchor": "middle",
                                             "class": "cmap-label cf-dlabel"}, s["text"]))
        elif L["id"] in ("city", "town"):
            items = [dict(label=s["label"], label_r=s["label_r"], bbox=s["bbox"], short=s["text"]) for s in L["shapes"]
                     if s.get("label") and s.get("bbox")]
            for it, x, y, anchor in _label_boxes(items, vb[2]):
                labels.append(h("text", {"x": x, "y": y, "text-anchor": anchor, "class": "cmap-label cmap-label-place"},
                                it["short"]))
        elif L["id"] == "township":
            for s in L["shapes"]:
                labels.append(h("text", {"x": s["label"][0], "y": s["label"][1] + 3, "text-anchor": "middle",
                                         "class": "cmap-label cmap-label-township"}, s["text"]))
        back = h("g", {"class": "cmap-back", "aria-hidden": "true"}, h("use", {"href": "#cf-back"})) \
            if L["id"] in ("city", "town") or L["id"].startswith("city-") else None
        body = [back, h("g", {"clip-path": "url(#cmap-clip)"}, paths), labels]
        groups.append(h("g", {"class": "cmap-layer" + (" is-on" if on else ""), "data-layer": L["id"], "role": "group",
                              "aria-label": f"Layer: {TYPES[L['type']]}, {L['label']}"}, body))
        tabs.append(h("button", {"type": "button", "class": "cmap-tab", "data-layer": L["id"], "data-cf-type": L["type"],
                                 "aria-pressed": "true" if on else "false"}, L["label"]))
        legends.append(_legend(L, ed, on))
    types_row = h("div", {"class": "cf-types", "role": "group", "aria-label": "Race type", "hidden": True},
                  [h("button", {"type": "button", "class": "cf-type", "data-cf-type": t,
                                "aria-pressed": "true" if any(L["id"] == default_layer and L["type"] == t for L in layers)
                                else "false"}, lab)
                   for t, lab in TYPES.items() if any(L["type"] == t for L in layers)])
    svg = h("svg", {"class": "cmap-svg", "viewBox": f"{vb[0]} {vb[1]} {vb[2]} {vb[3]}", "role": "group",
                    "aria-label": f"Campaign money map of {ed.county_label}. Every area is a link to its races; the list "
                                  "after the map has every area."},
            h("defs", None, h("clipPath", {"id": "cmap-clip"}, h("path", {"d": shapes["county"]["d"]})), shade_defs(),
              back_def),
            groups,
            h("path", {"d": shapes["county"]["d"], "class": "cmap-outline", "aria-hidden": "true"}),
            h("g", {"class": "cmap-hl-g", "aria-hidden": "true", "clip-path": "url(#cmap-clip)"}))
    panel = h("aside", {"class": "cmap-panel", "id": "cmap-panel", "aria-live": "polite", "aria-label": "Selected area"},
              h("p", {"class": "cmap-hint"}, "Hover, focus or tap an area to see its campaign money here. Select it "
                                             "again, or use the link, to open its races and reports."))
    return h("div", {"class": "cmap cmap-money cf-map", "data-default-layer": default_layer, "data-hash": "off"},
             h("div", {"class": "cmap-bar cf-bar"},
               h("p", {"class": "cf-filter-h", "id": "cf-filter-h", "hidden": True}, "Show races for"),
               types_row,
               h("div", {"class": "cmap-tabs", "role": "group", "aria-label": "Map layer", "hidden": True}, tabs)),
             h("div", {"class": "cmap-grid"}, h("div", {"class": "cmap-stage"}, svg, legends),
               h("div", {"class": "cf-side"}, panel,
                 h("p", {"class": "cf-legend-note"}, SUM_NOTE + " " + SUPPORT_NOTE))),
             json_script("cmap-data", data))
