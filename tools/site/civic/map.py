"""Interactive boundary map: inline SVG, layer switcher, details panel, and an all-areas list.

    shapes = load_shapes(ed)                       # data/editions/<id>/derived/map_shapes.json, or None
    boundary_map(page, ed, shapes)                 -> Markup (switcher + <svg> + panel + legend)
    area_lists(page, ed, shapes)                   -> Markup (one table per layer, same links)

Built by tools/build_map.py. Colors come from CSS classes (static/css/map.css), never party colors.
Every shape is an <a href> around a <path>, so the map works without JavaScript; static/js/map.js
adds the hover/focus panel, touch select-then-open, and layer switching.
"""
from __future__ import annotations

import json
from pathlib import Path

from .answers import TOWN_CLERK_LABEL, budget_basis_text, place_budget_row
from .components import as_of_note, body_offices, body_state, data_table, name_party_text, party_breakdown_text, term_party
from .data import fmt_int
from .html import Markup, h, json_script

LAYERS = [  # (key in map_shapes.json, tab id, tab label, list heading)
    ("place", "cities", "Cities and towns", "Cities and towns"),
    ("township", "townships", "Townships", "Townships"),
    ("school", "schools", "School corporations", "School corporations"),
]
TYPE_LABEL = {"city": "City", "town": "Town", "township": "Township", "school_corporation": "School corporation"}
# Head office by unit type (same choice as the At a glance box, civic/answers.py). Towns are led by the Town Council,
# so for towns the council comes first and the clerk-treasurer is listed under TOWN_CLERK_LABEL.
TOP_OFFICE = {"city": "mayor", "town": "town_clerk_treasurer", "township": "township_trustee"}
BUDGET_HEAD = "Latest adopted budget"
NO_HOLDERS = "current holders not in the guide's data yet"


def precinct_view(ed) -> bool:
    """edition.json "map_precinct_view" (default true). False removes the Precincts button, the precinct drill-down,
    the precinct shapes and the precinct tables; selecting a township, city or town then lists its results for
    every race instead."""
    return bool(ed.config.get("map_precinct_view", True))


def load_shapes(ed) -> dict | None:
    p = Path(ed.root) / "data" / "editions" / ed.edition_id / "derived" / "map_shapes.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def unit_href(page, uid: str, unit: dict) -> str:
    if unit["unit_type"] == "school_corporation":
        return page.rel(f"schools/index.html#{uid}")
    return page.rel(f"places/{uid}/index.html")


def _pop_index(ed) -> dict:
    """{(geo_type, geo_name_lower): {indicator_id: {vintage: row}}} for population indicators."""
    idx = ed.__dict__.get("_cmap_pop")
    if idx is None:
        idx = {}
        for r in ed.table("indicator_values"):
            if r["indicator_id"] in ("pop_total", "pop_census_2020"):
                idx.setdefault((r["geo_type"], r["geo_name"].lower()), {}).setdefault(r["indicator_id"], {})[r["vintage"]] = r
        ed.__dict__["_cmap_pop"] = idx
    return idx


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _vyear(v: str) -> int:
    import re
    ys = re.findall(r"\d{4}", v)
    return int(ys[-1]) if ys else 0


SHAPE_GEO_TYPES = {"place": ("place", "town"), "township": ("county_subdivision",), "school": ("school_district",)}


def _shape_names(ed) -> dict:
    """{unit_id: (layer key, Census name)} from the map shapes (cached); {} when there are no shapes."""
    idx = ed.__dict__.get("_cmap_shape_names")
    if idx is None:
        idx = {}
        shapes = load_shapes(ed)
        for key, items in ((shapes or {}).get("layers") or {}).items():
            if key in SHAPE_GEO_TYPES:
                for it in items:
                    if it.get("id") and it.get("census_name"):
                        idx[it["id"]] = (key, it["census_name"])
        ed.__dict__["_cmap_shape_names"] = idx
    return idx


def population(ed, unit: dict) -> dict | None:
    """Latest ACS pop_total (with margin of error and CV) plus a 2020 Census count when the data has one.
    The geography is the unit's map shape's own Census name (exact, before the first comma) when the unit has a shape;
    otherwise it is matched by the unit's name. Nothing is hard-coded. (Matching only by unit name missed School City
    of Mishawaka and LaVille, whose unit names differ from their Census names.)"""
    import re
    name = unit["name"]
    t = unit["unit_type"]
    rows = None
    shape = _shape_names(ed).get(unit.get("unit_id"))
    if shape:
        types, want = SHAPE_GEO_TYPES[shape[0]], shape[1].strip().lower()
        for (gt, gname), v in _pop_index(ed).items():
            if gt in types and gname.split(",")[0].strip() == want:
                rows = v
                break
    if t == "township":
        base = re.sub(r" township$", "", name, flags=re.I).lower()
        want, types = f"{base} township", ("county_subdivision",)
    elif t == "school_corporation":
        want, types = name.lower(), ("school_district",)
    else:
        base = re.sub(r"^(city|town) of ", "", name, flags=re.I).lower()
        want, types = f"{base} {t}", ("town",) if t == "town" else ("place",)
    for (gt, gname), v in (_pop_index(ed).items() if rows is None else ()):
        if gt in types and gname.startswith(want):
            rows = v
            break
    if not rows:
        return None
    tot = rows.get("pop_total", {})
    acs = [v for v in tot if v.startswith("ACS")]
    est = tot[max(acs, key=_vyear)] if acs else None
    census = None
    for v, r in rows.get("pop_census_2020", {}).items():
        census = r
    if census is None:
        census = tot.get("Decennial census 2020")
    out = {"census": None, "acs": None}
    if census and _num(census["value"]) is not None:
        out["census"] = int(_num(census["value"]))
    if est and _num(est["value"]) is not None:
        val, moe = _num(est["value"]), _num(est["moe"])
        cv = (moe / 1.645 / val * 100) if (moe and val) else None
        out["acs"] = {"value": int(val), "moe": int(moe) if moe else None, "vintage": est["vintage"],
                      "cv": round(cv) if cv is not None else None, "low": bool(cv is not None and cv > 30)}
    return out if (out["census"] is not None or out["acs"]) else None


def population_text(pop: dict | None) -> str:
    if not pop:
        return "not in the guide's data yet"
    parts = []
    if pop["census"] is not None:
        parts.append(f"{fmt_int(pop['census'])} (2020 Census count)")
    a = pop["acs"]
    if a:
        s = f"≈ {fmt_int(a['value'])}" + (f" (±{fmt_int(a['moe'])})" if a["moe"] else "") + f", {a['vintage']} estimate"
        if a["low"]:
            s += f"; low reliability (margin of error is large relative to the estimate, CV {a['cv']}%)"
        parts.append(s)
    return "; ".join(parts)


def unit_facts(ed, uid: str, shape: dict | None = None) -> dict:
    """Facts for the panel and the list: elected seats, top office-holder, budget, district note."""
    unit = ed.units[uid]
    offs = ed.offices_for(uid)
    elected = [o for o in offs if o.get("elected") == "yes"]
    seats = sum(int(o["seats"]) if o["seats"].isdigit() else 1 for o in elected)
    blank = any(not o["seats"].isdigit() for o in elected)
    seat_txt = (f"{'at least ' if blank else ''}{seats}" if elected else "none in the guide's data")
    is_town = unit["unit_type"] == "town"
    top = ""
    top_label = ""
    ot = TOP_OFFICE.get(unit["unit_type"])
    if ot:
        for o in offs:
            if o["office_type"] == ot:
                names = [name_party_text(t["person"], term_party(t), t.get("confidence") if term_party(t) else None)
                         for t in ed.current_terms(o["office_id"])]
                top_label = TOWN_CLERK_LABEL if is_town else o["title"].split(",")[0]
                top = ", ".join(names) if names else NO_HOLDERS
                break
    mix = []
    for bname, boffs in body_offices(offs).items():
        bterms, bseats = body_state(ed, boffs)
        gov = " (governing body)" if is_town and bname == "Town Council" else ""
        mix.append([f"{bname}{gov} by party", party_breakdown_text(bterms, bseats)[1:-1] if bterms else NO_HOLDERS])
    b = place_budget_row(ed, uid)
    budget = f"${float(b['amount']):,.0f} ({b['year']}, {budget_basis_text(b)})" if b else ""
    note = ""
    if shape and shape.get("share_inside") is not None and shape["share_inside"] < 0.97:
        note = (f"Partly outside the county: about {round(shape['share_inside'] * 100)}% of this district's land "
                "area is inside St. Joseph County (computed from Census boundaries).")
    pop = population(ed, unit)
    facts = [["Population", population_text(pop)], ["Elected seats", seat_txt]]
    head = [[top_label or "Top official", top]] if top else []
    # towns: the governing body first, then the clerk-treasurer; cities and townships: the head office first
    facts += (mix + head) if is_town else (head + mix)
    if budget:
        facts.append([BUDGET_HEAD, budget])
    mix_txt = "; ".join(f"{m[0].replace(' by party', '')}: {m[1]}" for m in mix)
    lead = "; ".join(f"{m[0].replace(' by party', '')}: {m[1]}" for m in mix if "(governing body)" in m[0]) if is_town else ""
    if top:
        lead = (lead + "; " if lead else "") + f"{top_label}: {top}"
    return {"mix": mix_txt, "facts": facts, "note": note, "pop": population_text(pop), "seats": seat_txt, "top": top,
            "top_label": top_label, "lead": lead, "budget": budget}


def _kind_class(unit: dict, index: int) -> str:
    t = unit["unit_type"]
    if t == "school_corporation":
        return f"cmap-school cmap-school-{index % 3}"
    return {"city": "cmap-city", "town": "cmap-town", "township": "cmap-township"}.get(t, "cmap-other")


def _label_boxes(items, vb_w):
    """Place labels: large areas centred, small ones beside the shape; nudge down on overlap."""
    placed = []
    out = []
    for it in sorted(items, key=lambda i: -i["label_r"]):
        name = it["short"]
        fs = 9.5
        w = len(name) * fs * 0.58
        x, y = it["label"]
        anchor = "middle"
        if it["label_r"] < w / 2 + 2 and it["label_r"] < 14:   # small shape: label beside it
            bx0, by0, bx1, by1 = it["bbox"]
            if bx1 + 4 + w < vb_w - 4:
                x, anchor = bx1 + 4, "start"
            else:
                x, anchor = bx0 - 4, "end"
            y = (by0 + by1) / 2
        def box(xx, yy):
            x0 = xx - w / 2 if anchor == "middle" else (xx if anchor == "start" else xx - w)
            return (x0, yy - fs, x0 + w, yy + 2)
        for _ in range(8):
            b = box(x, y)
            if not any(b[0] < p[2] and p[0] < b[2] and b[1] < p[3] and p[1] < b[3] for p in placed):
                break
            y += fs + 1
        placed.append(box(x, y))
        out.append((it, round(x, 1), round(y + fs * 0.35, 1), anchor))
    return out


# ------------------------------------------------------------------------------ "How areas voted" layer
# The race data (derived/map_votes.json, tools/build_map.py) is published as a separate file, assets/map-votes.json,
# that static/js/map_votes.js loads when the layer is opened; the page itself carries the controls for the default race,
# a table of every race's county (or district) total, and the default race by township and by city and town, so the
# layer's numbers are readable without JavaScript.
VOTES_ASSET = "assets/map-votes.json"
VOTE_GEOS = [("township", "Townships"), ("place", "Cities and towns"), ("precinct", "Precincts")]
VIDX = {"D": 0, "R": 1, "L": 2, "O": 3, "W": 4}
PARTY_NAME = {"D": "Democratic", "R": "Republican", "L": "Libertarian"}
# Legend rows: side A of the margin (alphabetically first of the race's two leading parties) first. The party letters
# and key colors are set per race by map_votes.js; the markup holds the default race (D and R).
VOTE_BANDS = [("a3", "+30 or more"), ("a2", "+15 to 30"), ("a1", "+5 to 15"), ("even", "Under 5 points either way"),
              ("b1", "+5 to 15"), ("b2", "+15 to 30"), ("b3", "+30 or more")]
VOTE_CAVEAT = ("Past results for this race only. They show how votes were cast here, not how any person or future election will go.")
AREA_NOTE = ("Colored land area is not the same as votes: a large rural township with few voters covers more of the map "
             "than a small city ward with many, so compare the vote totals, not the amount of color.")
PARTY_ORDER = (("D", 0, "Democratic"), ("L", 2, "Libertarian"), ("R", 1, "Republican"))   # alphabetical, never by result


def band_class(party: str, step) -> str:
    """CSS class of a margin band: Democratic and Republican shades, and one neutral gray scale shared by every other
    party (Libertarian, independents and others), which never wins an area in the mapped data but could."""
    side = {"D": "d", "R": "r"}.get(party, "o")
    return f"cmap-vb-{side}{step}"


def pair_sides(r: dict):
    """(A, B): the race's two leading parties, alphabetical (D before L before R); B is None when uncontested."""
    pair = sorted(r["pair"], key=lambda p: (p == "O", p))
    return (pair[0], pair[1] if len(pair) > 1 else None)


def vote_geos(ed):
    return [g for g in VOTE_GEOS if g[0] != "precinct" or precinct_view(ed)]


def party_label(r: dict, p: str) -> str:
    if p == "O":
        return r.get("oparty") or "Other party"
    return PARTY_NAME.get(p, p)


def scope_text(r: dict) -> str:
    if not r.get("district"):
        return "County total"
    if r.get("partial"):
        return "St. Joseph County part of the district"
    return {"township": "Township total", "town": "Town total", "ward": "Ward total"}.get(r.get("unit"), "District total")


def _names(lst) -> str:
    return ", ".join(f"{nm} ({p})" for nm, p in lst)


def seats_text(r: dict) -> str:
    """Multi-seat races (vote for 2 or 3): how shares are counted, and the winners. '' for single-seat races."""
    seats = r.get("seats", 1)
    if seats < 2:
        return ""
    w = r["winners"]
    n = sum(r["ncand"].values())
    head = f"Vote for {seats}: shares are of all votes cast for each party's candidates; "
    if not r["uncontested"]:
        out = head + f"the winners are the top {seats} candidates: {_names(w)}."
    elif n == 1:
        out = head + f"one candidate ran for {seats} seats and was elected: {_names(w)}."
    else:
        out = head + f"{n} candidates ran for {seats} seats and all were elected: {_names(w)}."
    counts = r["ncand"]
    if len(counts) > 1 and len(set(counts.values())) > 1:
        out += (" The parties ran different numbers of candidates (" +
                ", ".join(f"{p} {counts[p]}" for p in sorted(counts, key=lambda x: (x == "O", x))) +
                "), so their combined votes partly reflect how many candidates each ran.")
    return out


def area_note(r: dict) -> str:
    """Town and ward races: who votes in them, since a precinct's result counts only those voters."""
    if r.get("unit") == "ward":
        return ("Only voters who live in this ward of the town vote in this race; each precinct's figures count only "
                "them. Precincts are not split at ward lines, so the map cannot show the ward itself.")
    if r.get("unit") == "town":
        return "Only voters who live in the town vote in this race; each precinct's figures count only them."
    return ""


def uncontested_text(r: dict) -> str:
    """The legend note for an uncontested race ('' when contested)."""
    if not r.get("uncontested"):
        return ""
    a, b = pair_sides(r)
    seats = r.get("seats", 1)
    if seats < 2:
        who = r.get("cand", {}).get(a) or "one candidate"
        return (f"Uncontested: {who} ({party_label(r, a)}) was the only candidate on the ballot, so every area where "
                "this race was on the ballot has the same, darkest shade. The vote totals still differ from place to place.")
    n = sum(r["ncand"].values())
    lead = (f"Uncontested: {n} candidate{'s' if n != 1 else ''} for {seats} seats, so "
            f"{'all were' if n != 1 else 'the candidate was'} elected. ")
    if b is None:
        return lead + ("Every area where this race was on the ballot has the same, darkest shade of the only party on "
                       "it. The vote totals still differ from place to place.")
    return lead + "The colors still compare the parties' combined votes."


def margin_text(d: int, r: int) -> str:
    """Two-party margin in points, e.g. 'D +12.3' or 'R +4.0' ('Even' when under 0.05 points)."""
    return pair_margin_text({"D": d, "R": r}, "D", "R")


def pair_margin_text(v: dict, a: str, b: str) -> str:
    """Margin between two parties in points, '<leader> +x.x'; party codes O print as 'Other'."""
    va, vb = v.get(a, 0), v.get(b, 0)
    if va + vb == 0:
        return "no votes for either"
    pts = (va - vb) / (va + vb) * 100
    if abs(pts) < 0.05:
        return "Even"
    lead = a if pts > 0 else b
    return f"{'Other' if lead == 'O' else lead} +{abs(pts):.1f}"


def margin_phrase(r: dict, v) -> str:
    """How the margin of race r reads for vote vector v (D, R, L, O, W)."""
    a, b = pair_sides(r)
    seats = r.get("seats", 1)
    if b is None:
        if seats > 1:
            n = sum(r["ncand"].values())
            return (f"uncontested: {n} {party_label(r, a)} candidate{'s' if n != 1 else ''} for {seats} seats, "
                    "the only ones on the ballot" if n != 1 else
                    f"uncontested: one {party_label(r, a)} candidate for {seats} seats, the only one on the ballot")
        return f"uncontested: the {party_label(r, a)} candidate was the only one on the ballot"
    vv = {p: v[i] for p, i in VIDX.items()}
    pre = ""
    if seats > 1 and r.get("uncontested"):
        pre = f"uncontested ({sum(r['ncand'].values())} candidates for {seats} seats); "
    of = " of combined votes" if seats > 1 else ""
    if {a, b} == {"D", "R"}:
        return f"{pre}two-party margin{of} {pair_margin_text(vv, a, b)}"
    names = " and ".join(party_label(r, x) if x == "O" else x for x in (a, b))
    return f"{pre}margin{of} between the two leading parties ({names}) {pair_margin_text(vv, a, b)}"


def share(part: int, tot: int) -> str:
    """Share of all votes, one decimal; a share that rounds to 0.0 but is not zero prints as 'under 0.1%'."""
    x = part / tot * 100 if tot else 0
    return "under 0.1%" if 0 < x < 0.05 else f"{x:.1f}%"


def county_line(r: dict) -> str:
    """'County total, President, 2024: D 49.8% · L 0.6% · R 48.4% · other party 0.8% · write-ins 0.4% (110,823 votes);
    two-party margin D +1.5. ...' Same format for every race. Shares are of all votes cast in the race."""
    v = r["county"]
    tot = sum(v)
    head = f"{scope_text(r)}, {r['label']}"
    if not tot:
        return f"{head}: no votes in the guide's data."
    bits = []
    for code, i, _name in PARTY_ORDER:
        if v[i] or code in r.get("cand", {}):
            bits.append(f"{code} {share(v[i], tot)}")
    if v[3]:
        bits.append(f"{party_label(r, 'O')} {share(v[3], tot)}")
    if v[4]:
        bits.append(f"write-ins {share(v[4], tot)}")
    if r.get("county_checked"):
        basis = "matches the county's official canvass"
    elif r.get("check_note"):
        basis = "county sum not checked: " + r["check_note"]
    else:
        basis = "county sum not checked: the guide has no official county figure for this race to check it against"
    unit = {"township": "township", "town": "town", "ward": "town"}.get(r.get("unit"), "district")
    counted = f"Every precinct in the {unit} counted" if r.get("district") else "Every precinct counted"
    st = seats_text(r)
    return (f"{head}: " + " · ".join(bits) + f" ({fmt_int(tot)} votes); {margin_phrase(r, v)}. {counted} ({basis})." +
            (" " + st if st else ""))


def load_votes(ed) -> dict | None:
    p = Path(ed.root) / "data" / "editions" / ed.edition_id / "derived" / "map_votes.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def votes_asset(votes: dict, ed) -> dict:
    """The payload written to assets/map-votes.json (pages/map.py) and read by static/js/map_votes.js."""
    pv = precinct_view(ed)
    races = []
    for r in votes["races"]:
        x = dict(r, line=county_line(r))
        for k, t in (("snote", seats_text(r)), ("anote", area_note(r)), ("unote", uncontested_text(r))):
            if t:
                x[k] = t
        races.append(x)
    return {"races": races, "default": votes["default"], "bands": votes["bands"], "levels": votes["levels"],
            "offices": votes["offices"], "township": votes["township"], "place": votes["place"], "pview": pv,
            "precinct": votes["precinct"] if pv else {}}


def _vote_cells(r: dict, v):
    d, rr, l, o, w = v[0], v[1], v[2], v[3], v[4]
    return [fmt_int(d), fmt_int(l), fmt_int(rr), fmt_int(o + w), fmt_int(d + rr + l + o + w), margin_cell(r, v)]


def margin_cell(r: dict, v) -> str:
    a, b = pair_sides(r)
    if b is None:
        return "uncontested"
    return pair_margin_text({p: v[i] for p, i in VIDX.items()}, a, b)


# Race ids in map_votes.json (tools/build_map.py) use the precinct file's contest keys; results.csv names the same contests
# differently for statewide offices, townships and towns. These rules bridge the two id schemes.
STATE_CONTEST = {"governor": "state-governor", "attorney-general": "state-attorney-general",
                 "secretary-of-state": "state-secretary-of-state", "auditor": "state-auditor-of-state",
                 "treasurer": "state-treasurer-of-state"}


def results_contest_ids(eid: str, contest: str) -> list[str]:
    """Candidate results.csv contest_ids for a map race (election id, precinct-file contest key), most direct first."""
    import re
    out = [f"{eid}-{contest}"]
    if contest in STATE_CONTEST:
        out.append(f"{eid}-{STATE_CONTEST[contest]}")
    m = re.fullmatch(r"township-(trustee|board|assessor)-([a-z0-9-]+)", contest)
    if m:
        out.append(f"{eid}-{m.group(2)}-township-{m.group(1)}")
    m = re.fullmatch(r"town-council-([a-z0-9-]+?)-ward-(\d+)", contest)
    if m:
        out.append(f"{eid}-{m.group(1)}-council-ward-{m.group(2)}")
    elif contest.startswith("town-council-"):
        out.append(f"{eid}-{contest[len('town-council-'):]}-council-at-large")
    return out


def race_by_contest(ed, votes: dict | None) -> dict:
    """{results.csv contest_id: map race id} for every race on the "How areas voted" layer that the results file has."""
    if not votes:
        return {}
    have = {r["contest_id"] for r in ed.table("results")}
    out = {}
    for r in votes["races"]:
        hit = next((c for c in results_contest_ids(r["eid"], r["contest"]) if c in have), None)
        if hit:
            out[hit] = r["id"]
    return out


def vote_layer_group(page, ed, shapes, votes):
    """SVG sub-groups for the layer: townships, cities and towns, precincts."""
    uni = ed.units
    tw_items = [it for it in shapes["layers"]["township"] if it["id"] in uni]
    pl_items = [it for it in shapes["layers"]["place"] if it["id"] in uni]
    g_t, g_p, g_pr = [], [], []
    for it in tw_items:
        u = uni[it["id"]]
        g_t.append(h("a", {"href": unit_href(page, it["id"], u), "class": "cmap-a cmap-va", "data-vgeo": "township", "data-vkey": it["id"],
                           "aria-label": f"{u['name']}: how this area voted. Open its page."},
                     h("path", {"d": it["d"], "class": "cmap-s cmap-v"})))
    g_p.append(h("g", {"aria-hidden": "true"}, [h("path", {"d": it["d"], "class": "cmap-s cmap-v cmap-vb-bg"}) for it in shapes["layers"]["township"]]))
    for it in pl_items:
        u = uni[it["id"]]
        kids = [h("path", {"d": it["d"], "class": "cmap-s cmap-v"})]
        if it["label_r"] < 6:
            kids.append(h("circle", {"cx": it["label"][0], "cy": it["label"][1], "r": 5, "class": "cmap-dot cmap-v-dot"}))
        g_p.append(h("a", {"href": unit_href(page, it["id"], u), "class": "cmap-a cmap-va", "data-vgeo": "place", "data-vkey": it["id"],
                           "aria-label": f"{u['name']}: how this area voted. Open its page."}, kids))
    for it in (shapes["layers"].get("precinct", []) if precinct_view(ed) else []):
        code = it["code"]
        pe = votes["precinct"].get(code)
        if pe is None:
            g_pr.append(h("path", {"d": it["d"], "class": "cmap-s cmap-v cmap-vb-none", "aria-hidden": "true"}))
            continue
        g_pr.append(h("a", {"href": "#list-votes", "class": "cmap-a cmap-va", "data-vgeo": "precinct", "data-vkey": code,
                            "data-t": pe["t"] or "", "data-p": pe["p"] or "",
                            "aria-label": f"Precinct {pe['n']} ({code}): how this precinct voted."},
                      h("path", {"d": it["d"], "class": "cmap-s cmap-v"})))
    return [h("g", {"class": "cmap-vg is-on", "data-vsub": "township"}, g_t),
            h("g", {"class": "cmap-vg", "data-vsub": "place"}, g_p),
            h("g", {"class": "cmap-vg", "data-vsub": "precinct"}, g_pr) if precinct_view(ed) else None]


def _seg(group_attrs, buttons):
    return h("div", dict({"class": "cmap-seg"}, **group_attrs), buttons)


def vote_controls(page, ed, votes):
    """Race picker: Level (buttons) -> Office (select) -> District (select, district offices only) -> Year (buttons,
    only years with results for that office). The markup shows the default race; map_votes.js keeps it in step."""
    races = votes["races"]
    first = next(r for r in races if r["id"] == votes["default"])
    offices = [o for o in votes["offices"] if o["level"] == first["level"]]
    years = sorted({r["year"] for r in races if r["office"] == first["office"] and r["district"] == first["district"]},
                   reverse=True)
    lv_btns = [h("button", {"type": "button", "class": "cmap-chip", "data-level": lv["key"],
                            "aria-pressed": "true" if lv["key"] == first["level"] else "false"}, lv["label"])
               for lv in votes["levels"]]
    office_opts = [h("option", {"value": o["key"], "selected": o["key"] == first["office"] or None}, o["label"]) for o in offices]
    yr_btns = []
    for y in years:
        r = next(x for x in races if x["office"] == first["office"] and x["district"] == first["district"] and x["year"] == y)
        yr_btns.append(h("button", {"type": "button", "class": "cmap-chip", "data-year": str(y),
                                    "aria-pressed": "true" if y == first["year"] else "false"},
                         str(y), h("span", {"class": "cmap-tag"}, " uncontested") if r["uncontested"] else None))
    geos = [h("button", {"type": "button", "class": "cmap-chip", "data-vgeo-btn": k,
                         "aria-pressed": "true" if k == "township" else "false"}, lab) for k, lab in vote_geos(ed)]
    return h("div", {"class": "cmap-vctl", "data-for": "votes", "hidden": True, "data-src": page.rel(VOTES_ASSET)},
             h("div", {"class": "cmap-vsel"},
               h("fieldset", {"class": "cmap-vf cmap-vf-level"}, h("legend", {"class": "cmap-chips-l"}, "Level"),
                 _seg({"data-role": "level"}, lv_btns)),
               h("div", {"class": "cmap-vf cmap-vf-office"},
                 h("label", {"class": "cmap-chips-l", "for": "cmap-office"}, "Office"),
                 h("select", {"id": "cmap-office", "class": "cmap-select"}, office_opts)),
               h("div", {"class": "cmap-vf cmap-vf-district", "hidden": True},
                 h("label", {"class": "cmap-chips-l", "for": "cmap-district"}, "District"),
                 h("select", {"id": "cmap-district", "class": "cmap-select"})),
               h("fieldset", {"class": "cmap-vf cmap-vf-year"}, h("legend", {"class": "cmap-chips-l"}, "Year"),
                 _seg({"data-role": "year"}, yr_btns))),
             h("p", {"class": "cmap-vcounty", "aria-live": "polite"}, county_line(first)),
             h("fieldset", {"class": "cmap-vf cmap-vf-geo"}, h("legend", {"class": "cmap-chips-l"}, "Show by"),
               _seg({"data-role": "geo"}, geos)),
             h("details", {"class": "cmap-vrule-d"}, h("summary", None, "Which races are on this map"),
               h("p", {"class": "cmap-vrule muted"}, votes["rule"], page.cites.cite_compact(["IND-064", "MAP-010"]))),
             h("p", {"class": "cmap-vrule muted"}, AREA_NOTE))


def vote_legend(votes):
    first = next(r for r in votes["races"] if r["id"] == votes["default"])
    a, b = pair_sides(first)
    items = []
    for key, txt in VOTE_BANDS:
        if key == "even":
            items.append(h("li", {"data-band": key}, h("span", {"class": "cmap-key cmap-vb-even", "aria-hidden": "true"}),
                           h("span", {"class": "cmap-lg-t"}, txt)))
            continue
        party = a if key[0] == "a" else b
        items.append(h("li", {"data-band": key},
                       h("span", {"class": f"cmap-key {band_class(party, key[1])}", "aria-hidden": "true"}),
                       h("span", {"class": "cmap-lg-t"}, f"{party} {txt}")))
    items.append(h("li", {"data-band": "off", "hidden": True},
                   h("span", {"class": "cmap-key cmap-vb-off", "aria-hidden": "true"}),
                   h("span", {"class": "cmap-lg-t"}, "Not on this ballot (outside the district, township or town)")))
    items.append(h("li", {"data-band": "none"}, h("span", {"class": "cmap-key cmap-vb-none", "aria-hidden": "true"}),
                   h("span", {"class": "cmap-lg-t"}, "No results for this race")))
    return [h("ul", {"class": "cmap-legend", "data-layer": "votes", "aria-label": "Legend: margin"}, items),
            h("p", {"class": "cmap-vnote cmap-vunc muted", "data-layer": "votes", "hidden": True}),
            h("p", {"class": "cmap-vnote muted", "data-layer": "votes"},
              "Color shows the margin between the two parties with the most votes in the race: for most races the "
              "Democratic and Republican candidates, (D minus R) divided by (D plus R). In a race without both, the two "
              "leading parties are compared the same way; other parties share one gray scale. Bands start at 5 and 15 "
              "points, the same edges as the margin bands on the Elections by the numbers page; a 30-point band is added "
              "to show wider gaps. The same widths apply to every party. In an uncontested race every area where the race "
              "was on the ballot gets the darkest shade of the only party on it. In a race electing several members (vote "
              "for 2 or 3, such as a township board), a party's votes are all the votes cast for its candidates, and the "
              "winners are listed with the race. Color does not show how many people voted, "
              "so a small area can look as strong as a large one: check the total votes in the panel or the tables. Votes "
              "for other candidates and write-ins count in the totals and shares but not in the margin. Because this map "
              "uses the two-party margin, an area can fall in a different band than the same race on Elections by the "
              "numbers, which measures the margin over all votes cast. Parties appear in alphabetical order of their "
              "codes (D, L, R), then other parties and write-ins, everywhere on this map.")]


def multi_seat_list(races):
    """Races electing several members, with how their shares are counted and the winners (None when there are none)."""
    multi = [h("li", None, f"{r['label']}: {seats_text(r)}") for r in races if r.get("seats", 1) > 1]
    if not multi:
        return None
    return h("details", {"class": "cmap-vd"},
             h("summary", None, "Races electing several members: how shares are counted, and the winners"),
             h("ul", None, multi))


def vote_tables(page, ed, shapes, votes):
    """Under the map: every race's county (or district) total, and the default race by area. Without JavaScript these
    are the layer's numbers; with it, map_votes.js swaps the default race's area tables for the selected race's."""
    c = page.cites
    uni = ed.units
    races = votes["races"]
    first = next(r for r in races if r["id"] == votes["default"])
    lv_label = {lv["key"]: lv["label"] for lv in votes["levels"]}
    heads_area = ["Area", "Democratic", "Libertarian", "Republican", "Other parties and write-ins", "Total votes",
                  "Margin", "Precincts"]
    sum_rows = []
    for r in races:
        a, b = pair_sides(r)
        # id race-<race id>: the Results page links here (map/index.html#race-<id>); map.js opens the layer on that race
        sum_rows.append([h("span", {"id": f"race-{r['id']}"}, r["label"]), lv_label[r["level"]], scope_text(r)] + _vote_cells(r, r["county"]) +
                        ["matches the official canvass" if r["county_checked"] else "not checked"])
    summary = h("div", {"class": "cmap-vt"},
                h("h4", None, "Every race on the map: county or district totals"),
                h("p", {"class": "muted"}, "Margins compare the two parties with the most votes in each race; for state "
                                           "legislative districts the totals are the St. Joseph County part only."),
                data_table("cmap-v-races", ["Race", "Level", "Total for", "Democratic", "Libertarian", "Republican",
                                            "Other parties and write-ins", "Total votes", "Margin", "County sum check"],
                           sum_rows, caption="Every race on the map with its county or district total", copy=True,
                           min_width="52rem"),
                multi_seat_list(races))
    tables = []
    for geo, glabel in vote_geos(ed):
        if geo == "precinct":
            continue
        rows = []
        for uid, e in sorted(votes[geo].items(), key=lambda kv: uni[kv[0]]["name"]):
            v = e["v"].get(first["id"])
            if v:
                nm = uni[uid]["name"] + (" (approximate)" if e.get("approx") else "")
                rows.append([h("a", {"href": unit_href(page, uid, uni[uid])}, nm)] + _vote_cells(first, v) + [str(v[5])])
        tables.append(h("div", {"class": "cmap-vt"}, h("h4", None, f"{first['label']} by {glabel.lower()}",
                                                        [c.cite(s) for s in first["src"]]),
                        data_table(f"cmap-v-{geo}-{first['id']}", heads_area, rows,
                                   caption=f"{first['label']} by {glabel.lower()}", copy=False, min_width="40rem")))
    unp = []
    for r in races:
        lst = votes["unplaced"].get(r["id"], [])
        if lst and precinct_view(ed):
            unp.append(h("li", None, f"{r['label']}: " + ", ".join(f"{u['name']} ({u['code']}, {fmt_int(u['votes'])} votes)" for u in lst)))
        elif lst:
            unp.append(h("li", None, f"{r['label']}: {len(lst)} precinct{'s' if len(lst) != 1 else ''}, "
                                     f"{fmt_int(sum(u['votes'] for u in lst))} votes"))
    return h("div", {"class": "cmap-list", "data-layer": "votes", "id": "list-votes"},
             h("h3", None, "How areas voted"),
             h("p", {"class": "muted"}, "Votes cast in past general elections, summed from precinct results. " + VOTE_CAVEAT,
               c.cite_compact(["MAP-005", "MAP-006", "MAP-007", "MAP-009", "MAP-008"])),
             h("p", {"class": "muted"}, votes["rule"], c.cite_compact(["IND-064", "MAP-010"])),
             h("p", {"class": "muted"}, AREA_NOTE),
             summary,
             h("div", {"class": "cmap-nojs"},
               h("p", {"class": "muted"}, f"Below: {first['label']} by area. The map's race picker needs JavaScript; "
                                          "every race's county or district total is in the table above."),
               tables),
             h("div", {"class": "cmap-vjs", "hidden": True, "aria-live": "polite"}),
             h("p", {"class": "muted"}, "Precincts with results but no matching Census 2020 boundary are left out of every area total and the map, "
                                          "but counted in the county and district totals:") if unp else None,
             h("details", {"class": "cmap-vd"}, h("summary", None, "Precincts with no boundary, by race"),
               h("ul", None, unp)) if unp else None)


def government_layers(page, ed, shapes: dict, default_layer: str, area, back_cls: str = "cmap-s cmap-township cmap-back-s",
                      only: tuple | None = None):
    """The three government layers (cities and towns, townships, school corporations) as SVG groups, plus the layer
    tabs. Shared by boundary_map and the budgets page's money map (civic/money_map.py).

    area(key, tab, n, it, uid, unit) -> (path_class, href, aria_label, data_entry, dot_class) for each shape with a
    unit; data_entry goes into the #cmap-data blob that static/js/map.js reads. Returns (groups, tabs, data)."""
    vb = shapes["viewBox"]
    units = ed.units
    data = {}
    groups = []
    tabs = []
    for key, tab, label, _heading in LAYERS:
        if only is not None and tab not in only:
            continue
        items = shapes["layers"].get(key, [])
        paths, texts = [], []
        for n, it in enumerate(items):
            uid = it["id"]
            unit = units.get(uid) if uid else None
            if unit is None:
                paths.append(h("path", {"d": it["d"], "class": "cmap-s cmap-nolink", "data-tv": it["census_name"],
                                        "data-tl": "No page for this area in the guide yet"}))
                continue
            path_cls, href, aria, entry, dot_cls = area(key, tab, n, it, uid, unit)
            data[uid] = entry
            kids = [h("path", {"d": it["d"], "class": path_cls})]
            if key == "place" and it["label_r"] < 6:   # tiny places get a tappable dot
                kids.append(h("circle", {"cx": it["label"][0], "cy": it["label"][1], "r": 5, "class": dot_cls}))
            paths.append(h("a", {"href": href, "class": "cmap-a", "data-uid": uid, "aria-label": aria}, kids))
            it["short"] = unit["name"].replace("City of ", "").replace("Town of ", "").replace(" Township", "").replace(" School Corporation", "")
            if key == "place" or key == "township":
                texts.append(it)
        labels = []
        if key == "place":
            for it, x, y, anchor in _label_boxes(texts, vb[2]):
                labels.append(h("text", {"x": x, "y": y, "text-anchor": anchor, "class": "cmap-label cmap-label-place"}, it["short"]))
        elif key == "township":
            for it in texts:
                labels.append(h("text", {"x": it["label"][0], "y": it["label"][1] + 3, "text-anchor": "middle",
                                         "class": "cmap-label cmap-label-township"}, it["short"]))
        if key == "place":
            back = h("g", {"class": "cmap-back", "aria-hidden": "true"},
                     [h("path", {"d": t["d"], "class": back_cls}) for t in shapes["layers"]["township"]])
            body = [back, paths, labels]
        elif key == "school":
            body = [h("g", {"clip-path": "url(#cmap-clip)"}, paths)]
        else:
            body = [paths, labels]
        on = tab == default_layer
        groups.append(h("g", {"class": "cmap-layer" + (" is-on" if on else ""), "data-layer": tab,
                              "role": "group", "aria-label": f"Layer: {label}"}, body))
        tabs.append(h("button", {"type": "button", "class": "cmap-tab", "data-layer": tab,
                                 "aria-pressed": "true" if on else "false"}, label))
    return groups, tabs, data


def facts_area(page, ed):
    """The boundary map's area callback for government_layers: type colors, unit_facts panel, link to the unit's page."""
    def area(key, tab, n, it, uid, unit):
        f = unit_facts(ed, uid, it)
        href = unit_href(page, uid, unit)
        tlabel = TYPE_LABEL.get(unit["unit_type"], unit["unit_type"])
        entry = {"n": unit["name"], "t": tlabel, "f": f["facts"], "note": f["note"], "href": href, "l": tab, "d": it["d"]}
        name_for_aria = f"{unit['name']}, {tlabel.lower()}"
        aria = f"{name_for_aria}. Open page." + (f" {f['note']}" if f["note"] else "")
        return f"cmap-s {_kind_class(unit, n)}", href, aria, entry, "cmap-dot"
    return area


LEGEND_ITEMS = {
    "cities": [("cmap-city", "City"), ("cmap-town", "Town"), ("cmap-township cmap-back-s", "Unincorporated area (township background)")],
    "townships": [("cmap-township", "Township")],
    "schools": [("cmap-school cmap-school-0", "School corporation (shading only separates neighbors)")],
}


def boundary_map(page, ed, shapes: dict, default_layer: str = "cities", votes: dict | None = None) -> Markup:
    vb = shapes["viewBox"]
    layer_groups, tabs, data = government_layers(page, ed, shapes, default_layer, facts_area(page, ed))
    legends = [(tab, key) for key, tab, _label, _heading in LAYERS]

    if votes:
        layer_groups.append(h("g", {"class": "cmap-layer", "data-layer": "votes", "role": "group", "aria-label": "Layer: How areas voted"},
                              vote_layer_group(page, ed, shapes, votes)))
        tabs.append(h("button", {"type": "button", "class": "cmap-tab", "data-layer": "votes", "aria-pressed": "false"}, "How areas voted"))

    legend_items = LEGEND_ITEMS
    legend = [h("ul", {"class": "cmap-legend" + (" is-on" if tab == default_layer else ""), "data-layer": tab},
                [h("li", None, h("span", {"class": f"cmap-key {cls}", "aria-hidden": "true"}), txt) for cls, txt in legend_items[tab]])
              for tab, _k in legends]

    if votes:
        legend = legend + vote_legend(votes)
    svg = h("svg", {"class": "cmap-svg", "viewBox": f"{vb[0]} {vb[1]} {vb[2]} {vb[3]}", "role": "group",
                    "aria-label": f"Boundary map of {ed.county_label}. Every area is a link; a full list follows the map."},
            h("defs", None, h("clipPath", {"id": "cmap-clip"}, h("path", {"d": shapes["county"]["d"]})),
              # hatch for "not on this ballot" (district races); colors come from CSS tokens (map_votes.css)
              h("pattern", {"id": "cmap-hatch", "patternUnits": "userSpaceOnUse", "width": 6, "height": 6,
                            "patternTransform": "rotate(45)"},
                h("rect", {"width": 6, "height": 6, "class": "cmap-hatch-bg"}),
                h("line", {"x1": 0, "y1": 0, "x2": 0, "y2": 6, "class": "cmap-hatch-ln"})) if votes else None),
            layer_groups,
            h("path", {"d": shapes["county"]["d"], "class": "cmap-outline", "aria-hidden": "true"}),
            h("g", {"class": "cmap-hl-g", "aria-hidden": "true"}))
    panel = h("aside", {"class": "cmap-panel", "id": "cmap-panel", "aria-live": "polite", "aria-label": "Selected area"},
              h("p", {"class": "cmap-hint"}, "Hover, focus or tap an area to see details here. Select it again, or use the "
                                               "link, to open its page."))
    return h("div", {"class": "cmap", "data-default-layer": default_layer},
             h("div", {"class": "cmap-bar"},
               h("div", {"class": "cmap-tabs", "role": "group", "aria-label": "Map layer", "hidden": True}, tabs),
               vote_controls(page, ed, votes) if votes else None),
             h("div", {"class": "cmap-grid"},
               h("div", {"class": "cmap-stage"}, svg, legend,
                 h("div", {"class": "cmap-drill", "hidden": True}) if votes and precinct_view(ed) else None),
               panel),
             json_script("cmap-data", data))


def shade_defs():
    """SVG <pattern> for the shaded maps' "no data" hatch (static/css/money_map.css .cmap-mm-none)."""
    return h("pattern", {"id": "cmap-mhatch", "patternUnits": "userSpaceOnUse", "width": 6, "height": 6,
                         "patternTransform": "rotate(45)"},
             h("rect", {"width": 6, "height": 6, "class": "cmap-mhatch-bg"}),
             h("line", {"x1": 0, "y1": 0, "x2": 0, "y2": 6, "class": "cmap-mhatch-ln"}))


def embedded_map(page, ed, shapes: dict, layers: tuple, default_layer: str, area=None, label: str | None = None,
                 hint: str | None = None, legend=None, defs=None, extra_cls: str = "", controls=None,
                 back_cls: str = "cmap-s cmap-township cmap-back-s", attrs: dict | None = None, extra=None) -> Markup:
    """The boundary map limited to some layers, for embedding in another page (places index, Schools page). Same
    component as boundary_map: static/js/map.js gives the panel, touch select-then-open and the tabs. It never reads or
    writes the URL hash (data-hash="off"), so the host page's own #anchors keep working. With one layer the tab bar is
    hidden (cmap-single). area: a government_layers callback (default: the boundary map's facts panel).
    Shaded maps (civic/shading.py) pass their own legend blocks, the hatch defs, controls for the bar above the map,
    the township background class for the places layer, wrapper attrs and extra markup (JSON blobs) after the map."""
    vb = shapes["viewBox"]
    groups, tabs, data = government_layers(page, ed, shapes, default_layer, area or facts_area(page, ed), back_cls=back_cls,
                                           only=layers)
    shown = [tab for _k, tab, _l, _h in LAYERS if tab in layers]
    legend = legend if legend is not None else [h("ul", {"class": "cmap-legend" + (" is-on" if tab == default_layer else ""), "data-layer": tab},
                [h("li", None, h("span", {"class": f"cmap-key {cls}", "aria-hidden": "true"}), txt) for cls, txt in LEGEND_ITEMS[tab]])
              for tab in shown]
    svg = h("svg", {"class": "cmap-svg", "viewBox": f"{vb[0]} {vb[1]} {vb[2]} {vb[3]}", "role": "group",
                    "aria-label": label or f"Boundary map of {ed.county_label}. Every area is a link."},
            h("defs", None, h("clipPath", {"id": "cmap-clip"}, h("path", {"d": shapes["county"]["d"]})), defs),
            groups,
            h("path", {"d": shapes["county"]["d"], "class": "cmap-outline", "aria-hidden": "true"}),
            h("g", {"class": "cmap-hl-g", "aria-hidden": "true"}))
    panel = h("aside", {"class": "cmap-panel", "id": "cmap-panel", "aria-live": "polite", "aria-label": "Selected area"},
              h("p", {"class": "cmap-hint"}, hint or "Hover, focus or tap an area to see details here. Select it again, "
                                                     "or use the link, to open its page."))
    root = {"class": "cmap" + (" cmap-single" if len(shown) == 1 else "") + (f" {extra_cls}" if extra_cls else ""),
            "data-default-layer": default_layer, "data-hash": "off"}
    root.update(attrs or {})
    return h("div", root,
             h("div", {"class": "cmap-bar"},
               h("div", {"class": "cmap-tabs", "role": "group", "aria-label": "Map layer", "hidden": True}, tabs),
               controls),
             h("div", {"class": "cmap-grid"}, h("div", {"class": "cmap-stage"}, svg, legend), panel),
             json_script("cmap-data", data), extra)


def area_lists(page, ed, shapes: dict) -> Markup:
    """One table per layer: the no-JS and screen-reader alternative, with the same links."""
    c = page.cites
    out = []
    for key, tab, label, heading in LAYERS:
        rows = []
        for it in shapes["layers"].get(key, []):
            uid = it["id"]
            if not uid or uid not in ed.units:
                rows.append([it["census_name"], "", "", "No page in the guide yet", "", "", "", ""])
                continue
            u = ed.units[uid]
            f = unit_facts(ed, uid, it)
            name_cell = h("span", None, h("a", {"href": unit_href(page, uid, u)}, u["name"]), c.cite(u["source_ids"]))
            row = [name_cell, TYPE_LABEL.get(u["unit_type"], ""), f["pop"], f["seats"], f["lead"] or "No elected head office in the guide's data",
                   f["mix"] or "No elected board in the guide's data", f["budget"] or "not in the guide's data yet"]
            if key == "school":
                row.append(f["note"] or ("Inside the county" if it.get("share_inside", 1) >= 0.97 else ""))
            rows.append(row)
        rows.sort(key=lambda r: str(r[0]).lower() if not isinstance(r[0], Markup) else "")
        # sort by name text regardless of Markup
        rows.sort(key=lambda r: _plain(r[0]))
        heads = ["Area", "Type", "Population", "Elected seats", "Who leads it now (towns: Town Council first)",
                 "Party mix (current holders)", f"{BUDGET_HEAD} (year, basis)"]
        if key == "school":
            heads.append("Boundary note")
            missing = [uid for uid in shapes.get("units_without_shape", []) if ed.units[uid]["unit_type"] == "school_corporation"]
            for uid in missing:
                u = ed.units[uid]
                rows.append([h("span", None, h("a", {"href": unit_href(page, uid, u)}, u["name"]), c.cite(u["source_ids"])),
                             "School corporation", unit_facts(ed, uid)["pop"], unit_facts(ed, uid)["seats"], "", "", "",
                             "Not on the map: no matching Census school district was found."])
        out.append(h("div", {"class": "cmap-list is-on" if tab == "cities" else "cmap-list", "data-layer": tab, "id": f"list-{tab}"},
                     h("h3", None, heading),
                     data_table(f"cmap-table-{tab}", heads, rows, caption=f"{heading}: every area on the map, with links",
                                numeric=(), min_width="40rem")))
    return h("div", {"class": "cmap-lists"}, out,
             h("p", {"class": "muted"}, "Budgets are the same row each place's page shows in its At a glance box: the latest "
                                        "adopted budget in the guide's data, with its basis. Bases differ (general fund, all "
                                        "advertised funds, funds reported to Gateway), so compare amounts only when the basis "
                                        "matches."),
             as_of_note(ed))


def _plain(cell) -> str:
    import re
    return re.sub(r"<[^>]+>", "", str(cell)).lower()
