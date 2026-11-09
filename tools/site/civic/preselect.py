"""Saved-place preselect (review pattern P4, Wave E batch 8, 2026-11-09).

A reader who has saved a place (static/js/here.js: localStorage "civic-place" = {"place", "township", "school"}, ids
only) sees some pages open on it: the calendar and officeholders lists filtered to their governments, the results
explorer on their areas, their tax district picked when the guide's data names it, their school corporation or county
districts opened, their questions first, their area selected on the community maps. The pages ship whole; the script
only filters, opens or reorders, and always says so in a visible "Showing: ..." line with a button that undoes it.

The build side is small and lives here:

    here_layer(ed, unit_id)         -> the saved-place layer key of a unit: "county", "state", "library",
                                       "municipality:<id>", "township:<id>", "school:<id>" (same keys as the layer rows
                                       of civic/layers.py and here.js renderLayers), or "" when the unit is none of them
    here_attrs(ed, unit_id)         -> {"data-here-layer": key} for a row, group or item (empty dict for "")
    here_slot(kind, target, ...)    -> the hidden placeholder <p> that static/js/preselect.js turns into the line
    county_districts(ed)            -> the commissioner and council district of each saved place, only where the guide's
                                       own precinct results show a single one (see the function)
    tax_district_choice(...)        -> the taxing district of a saved place, only when the guide's district data names
                                       exactly one (money/your-tax-bill/; static/js/money.js applies the same rule)

Nothing here reads or writes the reader's place: it never leaves the browser. With JavaScript off every placeholder
stays hidden and the pages are as they were.
"""
from __future__ import annotations

from .html import Markup, h

LAYER_TYPES = {"city": "municipality", "town": "municipality", "township": "township", "school_corporation": "school"}
SLOT_KINDS = ("filter", "first", "one", "map", "explorer", "taxbill")   # the last two: elections.js, money.js


def here_layer(ed, unit_id: str, _seen: frozenset = frozenset()) -> str:
    """The saved-place layer a unit belongs to. A unit under a city (a housing authority, the transit authority) belongs
    to that city's layer; one under the county (courts, airport authority, board of health) to the county's."""
    u = ed.units.get(unit_id or "")
    if not u or unit_id in _seen:
        return ""
    t = u.get("unit_type", "")
    if t in LAYER_TYPES:
        return f"{LAYER_TYPES[t]}:{unit_id}"
    if t in ("county", "court_system"):
        return "county"
    if t == "library":
        return "library"
    if t == "state_chamber":
        return "state"
    parent = (u.get("parent_unit_ids") or "").split(";")[0].strip()
    return here_layer(ed, parent, _seen | {unit_id}) if parent else ""


def here_attrs(ed, unit_id: str) -> dict:
    key = here_layer(ed, unit_id)
    return {"data-here-layer": key} if key else {}


def here_slot(kind: str, target: str | None = None, *, extra: dict | None = None) -> Markup:
    """The placeholder for the "Showing: ..." line. ``kind`` names the behaviour (static/js/preselect.js):
    filter (a table_filter list: rows of other governments hidden), first (groups of the reader's areas moved first),
    one (pick_one items opened), map (an area selected on the map); explorer (the results explorer, elections.js) and
    taxbill (the tax-bill district, money.js) are handled by their page scripts. ``target`` is the id of the list, container or map
    it acts on. Ships hidden and empty, so JavaScript off (or no saved place) shows nothing."""
    if kind not in SLOT_KINDS:
        raise ValueError(f"here_slot: unknown kind {kind!r}")
    a = {"class": "here-pre", "data-here-pre": kind, "data-here-for": target, "hidden": True}
    a.update(extra or {})
    return h("p", a)


# ------------------------------------------------------------------ county districts from precinct results

COUNTY_DISTRICT_OFFICES = (("county-commissioner", "county-commissioner-d{d}"), ("county-council", "county-council-{d}"))


def county_districts(ed, votes: dict | None, first_year: int = 2022) -> dict:
    """{saved place id: {"keys": [office ids], "names": [...], "precincts": n}} for the places whose county commissioner
    district and county council district are each a single one in the guide's own data, and nothing for the rest.

    The data is the precinct results of derived/map_votes.json: each precinct's votes in the commissioner and council
    races held under the current lines (from ``first_year``; every district had a race in 2022 or 2024), and the area
    each precinct was placed in (township, and the city or town holding at least half of it). A place gets a district
    only when every precinct that could hold part of it voted in the same district's race:
      - its own precincts (that township, and that city or town, or no city or town for an unincorporated area);
      - every precinct in the township that straddles a city or town line (place share between 3% and 97%), since part
        of it may lie in the place;
      - every precinct the map could not place that names the city or town; for an unincorporated area, every one that
        names a city or town lying in the same township; and every one naming no place the guide knows.
    A place with no such precinct, or with precincts in more than one district, gets nothing: the county page then opens
    nothing, as before. No boundary is drawn or intersected here."""
    out: dict = {}
    if not votes:
        return out
    races = {r["id"]: r for r in votes.get("races", [])}
    precincts = votes.get("precinct", {})
    unplaced = votes.get("unplaced", {})
    names = {p.get("p") for p in precincts.values() if p.get("p")}

    def straddles(p) -> bool:
        return 0.03 < float(p.get("ps") or 0) < 0.97

    def districts_by_precinct(office: str) -> dict:
        per: dict = {}
        for code, p in precincts.items():
            for rid in p.get("v", {}):
                r = races.get(rid)
                if r and r.get("office") == office and int(r.get("year") or 0) >= first_year and r.get("district"):
                    per.setdefault(code, set()).add(str(r["district"]))
        return per

    town_of = {}   # city or town -> the townships its placed precincts are in
    for p in precincts.values():
        if p.get("p"):
            town_of.setdefault(p["p"], set()).add(p.get("t"))

    def unplaced_districts(office: str, place: str | None, townships: list[str]) -> set:
        """Districts of the precincts the map could not place that may hold part of the place: one naming the place
        itself; for an unincorporated area, one naming a city or town in the same township (its edge may lie outside
        the city); and one naming no known place at all."""
        ds = set()
        for rid, lst in unplaced.items():
            r = races.get(rid)
            if not (r and r.get("office") == office and int(r.get("year") or 0) >= first_year and r.get("district")):
                continue
            for u in lst or []:
                nm = (u.get("name") or "").lower().replace(" ", "-")
                if nm not in names or nm == place or (place is None and town_of.get(nm, set()) & set(townships)):
                    ds.add(str(r["district"]))
        return ds

    from .layers import build_layers   # local import: layers imports nothing from here, but keep the module light
    places = build_layers(ed)["places"]
    per = {office: districts_by_precinct(office) for office, _ in COUNTY_DISTRICT_OFFICES}
    for pl in places:
        muni = pl.get("muni") or None
        townships = [pl["township"]] if pl.get("township") else []
        if muni:
            # a city or town: every township the guide's precincts place it in (it may cross township lines)
            townships = sorted({p["t"] for p in precincts.values() if p.get("p") == muni})
        if not townships:
            continue
        keys, labels, n_prec = [], [], 0
        for office, pattern in COUNTY_DISTRICT_OFFICES:
            ds, own = set(), 0
            for code, p in precincts.items():
                if p.get("t") not in townships:
                    continue
                mine = (p.get("p") or None) == muni
                if mine or straddles(p):
                    ds |= per[office].get(code, set())
                    own += 1 if mine and code in per[office] else 0
            ds |= unplaced_districts(office, muni, townships)
            if own == 0 or len(ds) != 1:
                keys = []
                break
            d = ds.pop()
            oid = pattern.format(d=d.lower())
            if oid not in ed.offices:
                keys = []
                break
            keys.append(oid)
            labels.append(ed.offices[oid]["title"])
            n_prec = max(n_prec, own)
        if keys:
            out[pl["id"]] = {"keys": keys, "names": labels, "precincts": n_prec}
    return out


# ------------------------------------------------------------------ taxing district from the saved place

def district_hints(dlist: list[dict], uidmap: dict) -> dict:
    """{district code: {"tw": [township ids], "sc": [school ids]}} in units.csv ids (the saved place's ids): the
    township and school corporation each district is consistent with. A district whose name states a township or school
    (money.py _district_prefill) has that one; otherwise the units the state's own per-district breakdown lists for its
    latest year. Empty when the data names none (then that part does not narrow the choice)."""
    rev = {mid: uid for uid, mid in uidmap.items()}
    out = {}
    for d in dlist:
        pre = d.get("pre") or {}
        years = sorted(d.get("units") or {}, reverse=True)
        comp = [p[0] for p in (d["units"][years[0]] if years else [])]
        tw = [pre["township"]] if pre.get("township") else [m for m in comp if m.startswith("township-")]
        sc = [pre["school"]] if pre.get("school") else [m for m in comp if m.startswith("school-")]
        out[d["code"]] = {"tw": sorted(rev[m] for m in tw if m in rev), "sc": sorted(rev[m] for m in sc if m in rev)}
    return out


def tax_district_choice(dlist: list[dict], hints: dict, place: str, township: str = "any", school: str = "any") -> dict:
    """The taxing district of a saved place (ids as stored by here.js), never guessed:
      {"code": c}                       exactly one district fits the place, township and school;
      {"choices": [codes], "why": w}    more than one fits (w = "township" or "school": what would tell them apart),
                                        or none fits the school saved with the place (w = "conflict": choices are the
                                        districts that fit the place and township);
      {}                                no district names the place.
    static/js/money.js applies the same rule (tools/tests/test_wave_e_preselect.py pins the cases)."""
    cands = [d["code"] for d in dlist if (d.get("pre") or {}).get("place") == place]
    if not cands:
        return {}
    known_t = bool(township) and township != "any"
    known_s = bool(school) and school != "any"
    if known_t:
        cands = [c for c in cands if not hints[c]["tw"] or township in hints[c]["tw"]]
        if not cands:
            return {}
    if known_s:
        fit = [c for c in cands if not hints[c]["sc"] or school in hints[c]["sc"]]
        if not fit:
            return {"choices": cands, "why": "conflict"}
        cands = fit
    if len(cands) == 1:
        return {"code": cands[0]}
    tws = {tuple(hints[c]["tw"]) for c in cands}
    return {"choices": cands, "why": "township" if len(tws) > 1 and not known_t else "school"}


def tax_district_for_saved(dlist: list[dict], hints: dict, place: str, township: str = "any", school: str = "any",
                           default_township: str = "", default_school: str = "") -> dict:
    """tax_district_choice with only what the reader chose (``township`` / ``school``: "any" when not chosen; added
    Wave E batch 8 part 2). The guide's defaults stored with the place (here.js fills a city's usual school corporation
    and a town's township when the place is chosen) never cause a pick: they only order the choices, those that fit
    the defaults first, listed in "fit_default". static/js/money.js fromPlace applies the same rule."""
    r = tax_district_choice(dlist, hints, place, township, school)
    if "choices" not in r:
        return r
    if r["why"] == "conflict":
        return {**r, "fit_default": []}
    def fits(c):
        h = hints[c]
        return ((not default_township or not h["tw"] or default_township in h["tw"]) and
                (not default_school or not h["sc"] or default_school in h["sc"]))
    fit = [c for c in r["choices"] if fits(c)] if (default_township or default_school) else []
    if len(fit) == len(r["choices"]):
        fit = []
    return {**r, "choices": fit + [c for c in r["choices"] if c not in fit], "fit_default": fit}
