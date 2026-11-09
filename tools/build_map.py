"""Convert Census TIGERweb GeoJSON (sources/boundaries/*.geojson) into the compact SVG-ready
data/editions/<edition>/derived/map_shapes.json used by tools/site/civic/map.py.

    python -P -E tools/build_map.py --edition st-joseph [--tolerance 0.45] [--export-svg planning/map-preview.svg]

Stdlib only. Steps: pick the features that really overlap the county (grid sampling inside
the county polygon, so features that only touch the border are dropped and reported), clip to a
padded county rectangle, project (equirectangular, cos(lat) scaling), simplify with
Douglas-Peucker on SHARED ARCS (neighbours keep identical edges, so no gaps open between them),
map each feature to the guide's unit_id, and write one path string per feature.
Unmatched features are listed and written to the file under "unmatched"; nothing is dropped silently.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOUNDS = ROOT / "sources" / "boundaries"
VIEW_W = 640.0           # county width in SVG units
PAD = 6.0                # margin around the county
VINTAGE = "TIGERweb Current, January 1, 2026 vintage"

# layer key -> (geojson file, TIGERweb layer id, TIGERweb layer name)
LAYERS = {
    "township": ("townships.geojson", 22, "County Subdivisions"),
    "place": ("places_incorporated.geojson", 28, "Incorporated Places"),
    "school": ("school_districts_unified.geojson", 14, "Unified School Districts"),
}

# Census name -> guide unit_id for school districts (names differ from the guide's; checked by hand).
SCHOOL_UNITS = {
    "South Bend Community School Corporation": "sbcsc",
    "Penn-Harris-Madison School Corporation": "phm",
    "Mishawaka School City": "school-city-mishawaka",
    "John Glenn School Corporation": "john-glenn",
    "Union-North United School Corporation": "union-north",
    "New Prairie United School Corporation": "new-prairie",
    "LaVille Junior-Senior High School": "laville",
    "LaVille School Corporation": "laville",
}


# ------------------------------------------------------------------ geometry helpers
def polys(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return geom["coordinates"]
    raise ValueError(geom["type"])


def pip(x, y, ring):
    inside, j = False, len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


_BB = {}


def _bbox(poly):
    k = id(poly[0])
    if k not in _BB:
        _BB[k] = (min(p[0] for p in poly[0]), min(p[1] for p in poly[0]),
                  max(p[0] for p in poly[0]), max(p[1] for p in poly[0]))
    return _BB[k]


def inside_geom(x, y, geom):
    for poly in polys(geom):
        b = _bbox(poly)
        if x < b[0] or x > b[2] or y < b[1] or y > b[3]:
            continue
        if pip(x, y, poly[0]) and not any(pip(x, y, hole) for hole in poly[1:]):
            return True
    return False


def clip_ring(ring, xmin, ymin, xmax, ymax):
    """Sutherland-Hodgman against an axis-aligned rectangle (exact for convex clip)."""
    def edge(pts, inside, inter):
        out = []
        for i, p in enumerate(pts):
            q = pts[i - 1]
            if inside(p):
                if not inside(q):
                    out.append(inter(q, p))
                out.append(p)
            elif inside(q):
                out.append(inter(q, p))
        return out

    def ix(xv):
        return lambda a, b: (xv, a[1] + (b[1] - a[1]) * (xv - a[0]) / (b[0] - a[0]))

    def iy(yv):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (yv - a[1]) / (b[1] - a[1]), yv)

    pts = [tuple(p[:2]) for p in ring]
    for inside, inter in ((lambda p: p[0] >= xmin, ix(xmin)), (lambda p: p[0] <= xmax, ix(xmax)),
                          (lambda p: p[1] >= ymin, iy(ymin)), (lambda p: p[1] <= ymax, iy(ymax))):
        if not pts:
            break
        pts = edge(pts, inside, inter)
    return pts if len(pts) >= 3 else []


def dp(pts, tol):
    """Douglas-Peucker on an open polyline (endpoints kept)."""
    if len(pts) < 3:
        return list(pts)
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (ax, ay), (bx, by) = pts[a], pts[b]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        best, bi = -1.0, -1
        for i in range(a + 1, b):
            px, py = pts[i]
            d = math.hypot(px - ax, py - ay) if L == 0 else abs(dy * (px - ax) - dx * (py - ay)) / L
            if d > best:
                best, bi = d, i
        if best > tol:
            keep[bi] = True
            stack += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]


def ring_area(ring):
    s = 0.0
    for i in range(len(ring)):
        x1, y1 = ring[i - 1]
        x2, y2 = ring[i]
        s += x1 * y2 - x2 * y1
    return s / 2


# ------------------------------------------------------------------ shared-arc simplification
def simplify_layer(shapes, tol):
    """shapes: {fid: [[ring, ...], ...]} in projected coords (list of polygons -> list of rings).
    Returns {fid: [[simplified ring, ...], ...]} with shared edges simplified identically."""
    key = lambda p: (round(p[0], 4), round(p[1], 4))
    owners = {}
    for fid, plist in shapes.items():
        for poly in plist:
            for ring in poly:
                for i in range(len(ring)):
                    a, b = key(ring[i - 1]), key(ring[i])
                    owners.setdefault(frozenset((a, b)), set()).add(fid)
    cache = {}

    def simp_arc(arc):
        k = tuple(key(p) for p in arc)
        kr = k[::-1]
        if k in cache:
            return cache[k]
        if kr in cache:
            return cache[kr][::-1]
        out = dp(arc, tol)
        cache[k] = out
        return out

    result = {}
    for fid, plist in shapes.items():
        res_polys = []
        for poly in plist:
            res_rings = []
            for ring in poly:
                n = len(ring)
                own = [frozenset(owners[frozenset((key(ring[i - 1]), key(ring[i])))]) for i in range(n)]  # edge i-1 -> i
                brk = [i for i in range(n) if own[i] != own[(i + 1) % n]]  # vertex i is where edge ending at i differs from next edge
                # vertex i joins edge (i-1->i) and edge (i->i+1); break when owner sets differ
                if len(brk) < 2:
                    # one arc round the ring: split at two far-apart vertices so DP is well defined
                    far = max(range(n), key=lambda i: math.hypot(ring[i][0] - ring[0][0], ring[i][1] - ring[0][1]))
                    brk = sorted({0, far})
                arcs = []
                for bi in range(len(brk)):
                    s, e = brk[bi], brk[(bi + 1) % len(brk)]
                    idx = [s]
                    i = s
                    while i != e:
                        i = (i + 1) % n
                        idx.append(i)
                    arcs.append([ring[i] for i in idx])
                out = []
                for arc in arcs:
                    sa = simp_arc(arc)
                    out.extend(sa[:-1])
                if len(out) >= 3 and abs(ring_area(out)) > 0.05:
                    res_rings.append(out)
            if res_rings:
                res_polys.append(res_rings)
        result[fid] = res_polys
    return result


def path_d(plist):
    parts = []
    for poly in plist:
        for ring in poly:
            pts = []
            last = None
            for x, y in ring:
                q = (round(x, 1), round(y, 1))
                if q != last:
                    pts.append(q)
                last = q
            if len(pts) < 3:
                continue
            f = lambda v: f"{v:.1f}".rstrip("0").rstrip(".") if "." in f"{v:.1f}" else f"{v:.1f}"
            parts.append("M" + " ".join(f"{f(x)} {f(y)}" for x, y in pts) + "Z")
    return "".join(parts)


def label_point(plist):
    """Visual centre: best interior grid point of the largest polygon (max distance to its boundary)."""
    big = max(plist, key=lambda p: abs(ring_area(p[0])))
    outer = big[0]
    xs = [p[0] for p in outer]
    ys = [p[1] for p in outer]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    segs = [(outer[i - 1], outer[i]) for i in range(len(outer))]

    def dist(px, py):
        best = 1e18
        for (ax, ay), (bx, by) in segs:
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
            best = min(best, math.hypot(px - ax - t * dx, py - ay - t * dy))
        return best

    best, bp = -1.0, ((x0 + x1) / 2, (y0 + y1) / 2)
    n = 24
    for i in range(1, n):
        for j in range(1, n):
            px, py = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * j / n
            if pip(px, py, outer) and not any(pip(px, py, h) for h in big[1:]):
                d = dist(px, py)
                if d > best:
                    best, bp = d, (px, py)
    return bp, best, (x0, y0, x1, y1)


# ------------------------------------------------------------------ main
def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edition", default="st-joseph")
    ap.add_argument("--tolerance", type=float, default=0.25, help="Douglas-Peucker tolerance in SVG units")
    ap.add_argument("--export-svg", default=None, help="write a standalone townships+towns preview SVG")
    args = ap.parse_args()

    edir = ROOT / "data" / "editions" / args.edition
    units = {}
    with open(edir / "units.csv", encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            units[r["unit_id"]] = r

    county = json.load(open(BOUNDS / "county.geojson", encoding="utf-8"))["features"][0]
    cgeom = county["geometry"]
    allpts = [p for poly in polys(cgeom) for ring in poly for p in ring]
    lon0, lon1 = min(p[0] for p in allpts), max(p[0] for p in allpts)
    lat0, lat1 = min(p[1] for p in allpts), max(p[1] for p in allpts)
    kx = math.cos(math.radians((lat0 + lat1) / 2))
    scale = VIEW_W / ((lon1 - lon0) * kx)
    W = VIEW_W + 2 * PAD
    H = (lat1 - lat0) * scale + 2 * PAD

    def proj(p):
        return ((p[0] - lon0) * kx * scale + PAD, (lat1 - p[1]) * scale + PAD)

    # grid of sample points inside the county (for overlap tests)
    grid = []
    N = 110
    for i in range(N):
        for j in range(N):
            x, y = lon0 + (lon1 - lon0) * (i + .5) / N, lat0 + (lat1 - lat0) * (j + .5) / N
            if inside_geom(x, y, cgeom):
                grid.append((x, y))
    # padded clip rectangle (degrees)
    px, py = (lon1 - lon0) * 0.02, (lat1 - lat0) * 0.02
    clip = (lon0 - px, lat0 - py, lon1 + px, lat1 + py)

    report = {"vintage": VINTAGE, "layers": {}, "dropped": [], "unmatched": []}
    out_layers = {}
    ccount = len(grid)

    # county outline (simplified on its own arcs)
    cshape = {"county": [[[proj(p) for p in ring[:-1] if True] for ring in poly] for poly in polys(cgeom)]}
    cs = simplify_layer(cshape, args.tolerance)
    county_d = path_d(cs["county"])

    for layer, (fname, lid, lname) in LAYERS.items():
        feats = json.load(open(BOUNDS / fname, encoding="utf-8"))["features"]
        keep = {}
        info = {}
        for f in feats:
            pr = f["properties"]
            name = pr["NAME"]
            n_in = sum(inside_geom(x, y, f["geometry"]) for x, y in grid)
            if n_in == 0:
                # small feature that fell between grid points: count its own vertices inside the county
                vs = [p for poly in polys(f["geometry"]) for p in poly[0]]
                vin = sum(inside_geom(p[0], p[1], cgeom) for p in vs)
                if vin >= max(3, 0.2 * len(vs)):
                    n_in = max(1, int(ccount * pr["AREALAND"] / max(1, county["properties"]["AREALAND"])))
            if n_in == 0:
                report["dropped"].append(f"{layer}: {name} (GEOID {pr['GEOID']}) only touches or lies outside the county")
                continue
            clipped = []
            for poly in polys(f["geometry"]):
                rings = []
                for k, ring in enumerate(poly):
                    c = clip_ring(ring[:-1], *clip)
                    if c:
                        rings.append([proj(p) for p in c])
                    elif k == 0:
                        break
                if rings:
                    clipped.append(rings)
            fid = pr["GEOID"]
            keep[fid] = clipped
            info[fid] = (pr, n_in / ccount)
        simp = simplify_layer(keep, args.tolerance)
        items = []
        for fid, plist in simp.items():
            pr, frac = info[fid]
            name = pr["NAME"]
            base = pr.get("BASENAME", name)
            if layer == "township":
                uid = slugify(base) + "-township"
            elif layer == "place":
                uid = slugify(base)
            else:
                uid = SCHOOL_UNITS.get(name)
            matched = uid in units
            # share of the feature's land area that lies inside the county (area-based estimate)
            share_in = None
            if layer == "school":
                inside_km2 = frac * county["properties"]["AREALAND"] / 1e6
                total_km2 = pr["AREALAND"] / 1e6
                share_in = round(min(1.0, inside_km2 / total_km2), 3)
            lp, rad, bb = label_point(plist)
            item = {"id": uid if matched else None, "geoid": fid, "census_name": name, "d": path_d(plist),
                    "label": [round(lp[0], 1), round(lp[1], 1)], "label_r": round(rad, 1),
                    "bbox": [round(v, 1) for v in bb], "county_share": round(frac, 4)}
            if share_in is not None:
                item["share_inside"] = share_in
            if not matched:
                report["unmatched"].append(f"{layer}: {name} (GEOID {pr['GEOID']}) -> no unit_id (tried {uid!r})")
            items.append(item)
        items.sort(key=lambda it: (it["id"] is None, it["census_name"]))
        out_layers[layer] = items
        report["layers"][layer] = {"tigerweb_layer": lid, "tigerweb_name": lname, "features": len(items),
                                   "matched": sum(1 for i in items if i.get("id"))}

    # ---- precinct layer (Census 2020 voting districts), simplified on shared arcs like the others
    vtd_path = ROOT / "sources" / "precincts" / "tigerweb-vtd2020" / "vtd.json"
    if vtd_path.exists():
        vfeats = json.load(open(vtd_path, encoding="utf-8"))["features"]
        vkeep = {}
        for f in vfeats:
            code = f["properties"]["NAME"].split()[0]
            plist = []
            for poly in polys(f["geometry"]):
                rings = [[proj(p) for p in ring[:-1]] for ring in poly]
                plist.append(rings)
            vkeep[code] = plist
        vsimp = simplify_layer(vkeep, args.tolerance)
        out_layers["precinct"] = [{"code": c, "d": path_d(pl)} for c, pl in sorted(vsimp.items()) if path_d(pl)]
        report["layers"]["precinct"] = {"tigerweb_layer": "Census2020 58", "tigerweb_name": "Voting Districts",
                                        "features": len(out_layers["precinct"]), "matched": len(out_layers["precinct"])}

    covered = {i["id"] for items in out_layers.values() for i in items if i.get("id")}
    want = {u for u, r in units.items() if r["unit_type"] in ("city", "town", "township", "school_corporation")}
    report["units_without_shape"] = sorted(want - covered)

    data = {"vintage": VINTAGE, "source_note": "U.S. Census Bureau TIGERweb, Current (2026) WMS; "
            "layers 22 County Subdivisions, 28 Incorporated Places, 14 Unified School Districts, 82 Counties.",
            "viewBox": [0, 0, round(W, 1), round(H, 1)], "tolerance": args.tolerance,
            "county": {"geoid": county["properties"]["GEOID"], "d": county_d},
            "layers": out_layers, "unmatched": report["unmatched"],
            "units_without_shape": report["units_without_shape"]}
    dest = edir / "derived" / "map_shapes.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False), encoding="utf-8", newline="\n")

    print(f"wrote {dest} ({dest.stat().st_size:,} bytes), viewBox {data['viewBox']}")
    for k, v in report["layers"].items():
        sz = sum(len(i["d"]) for i in out_layers[k])
        print(f"  {k}: {v['features']} features, {v['matched']} matched to unit_id, path bytes {sz:,}")
    for line in report["dropped"]:
        print("  dropped:", line)
    write_votes(edir, units, data)
    for line in report["unmatched"]:
        print("  UNMATCHED:", line)
    print("  units with no TIGER shape:", ", ".join(report["units_without_shape"]) or "none")

    if args.export_svg:
        export_svg(Path(args.export_svg), data)


# Which races the "How areas voted" layer shows is a written rule, applied here mechanically; nothing is picked by hand.
# RULE: every partisan race for a federal, state, county, township or town office on the county's general-election
# ballot in each year the guide has precinct results for (2020, 2022, 2024). tools/build_precinct_results.py reads every
# such race in each source (its RULE comment lists them, what is left out, and which years have township and town
# races: only 2022); this file takes whatever precinct_results.csv holds, so a race cannot be left off here, and stops
# if the file holds a contest it cannot place in ballot order.
# ORDER: level (federal, state, county, township and town), then the order of offices on the ballot (IC 3-11-2-12,
# sources IND-064 and MAP-010; township offices in the order the county's 2022 report prints them: assessor, trustee,
# board), then district, township or town; years newest first. DEFAULT: the top race on the most recent ballot
# (President 2024), so the choice does not depend on who won.
# MULTI-SEAT RACES (township board, vote for 3; town council at-large, vote for 2): a party's votes are the votes for all
# of its candidates, so map colors and shares compare parties' combined votes; the winners are listed separately.
RACE_RULE = ("The map has every partisan race for a federal, state, county, township or town office on the county's "
             "general-election ballots in 2020, 2022 and 2024, the years with precinct results in the guide: President, "
             "Congress, statewide offices, the State Senate and State House districts that include part of the county, "
             "county offices and judges elected on a party ballot, the county commissioner and county council districts, "
             "and, on the 2022 ballot (the only one of the three with them), township trustee, township board and "
             "township assessor races and town council races. No city office was on these ballots: South Bend and "
             "Mishawaka elect theirs in odd years. Races with no more candidates than seats are included and marked "
             "uncontested. In races electing several members (vote for 2 or 3), each party's share is of all votes cast "
             "for that party's candidates, and the winners are listed. Left out: judicial retention votes and public "
             "questions (yes-or-no questions with no candidates) and school board races (nonpartisan). Offices are "
             "listed in the order they appear on the ballot under Indiana law. The race shown first is the top race on "
             "the most recent ballot, so the choice does not depend on who won.")
LEVELS = (("federal", "Federal"), ("state", "State"), ("county", "County"), ("local", "Township & town"))
# (office key, level, label, district label or None) in ballot order, IC 3-11-2-12: federal and state offices
# (President, U.S. Senator, Governor, Secretary of State, Auditor/Comptroller, Treasurer, Attorney General,
# U.S. Representative; a same-day vacancy election follows the regular one), legislative offices (State Senator,
# State Representative), circuit and county judicial offices (circuit judge, superior judge, probate judge,
# prosecuting attorney, circuit court clerk), county offices (auditor, recorder, treasurer, sheriff, coroner, surveyor,
# assessor, commissioner, council member).
OFFICES = (
    ("president", "federal", "President", None),
    ("us-senate", "federal", "U.S. Senate", None),
    ("us-house", "federal", "U.S. House, 2nd District", None),
    ("us-house-special", "federal", "U.S. House, 2nd District (special election)", None),
    ("governor", "state", "Governor", None),
    ("secretary-of-state", "state", "Secretary of State", None),
    ("auditor", "state", "Auditor of State", None),
    ("treasurer", "state", "Treasurer of State", None),
    ("attorney-general", "state", "Attorney General", None),
    ("state-senate", "state", "State Senate", "District"),
    ("state-house", "state", "State House", "District"),
    ("county-circuit-judge", "county", "Judge of the Circuit Court", None),
    ("county-probate-judge", "county", "Judge of the Probate Court", None),
    ("county-prosecutor", "county", "Prosecuting Attorney", None),
    ("county-clerk", "county", "Clerk of the Circuit Court", None),
    ("county-auditor", "county", "County Auditor", None),
    ("county-recorder", "county", "County Recorder", None),
    ("county-treasurer", "county", "County Treasurer", None),
    ("county-sheriff", "county", "County Sheriff", None),
    ("county-coroner", "county", "County Coroner", None),
    ("county-surveyor", "county", "County Surveyor", None),
    ("county-assessor", "county", "County Assessor", None),
    ("county-commissioner", "county", "County Commissioner", "District"),
    ("county-council", "county", "County Council", "District"),
    ("township-assessor", "local", "Township Assessor", "Township"),
    ("township-trustee", "local", "Township Trustee", "Township"),
    ("township-board", "local", "Township Board", "Township"),
    ("town-council", "local", "Town Council", "Town"),
)
OFFICE = {o[0]: o for o in OFFICES}
LOCAL_OFFICES = ("township-assessor", "township-trustee", "township-board", "town-council")
# State legislative districts cross the county line; the guide has only the St. Joseph County part of their results.
PARTIAL_DISTRICT = ("state-senate", "state-house")
SRC_BY = {"MAP-005", "MAP-006", "MAP-007", "MAP-009"}
PARTY_NAME = {"D": "Democratic", "R": "Republican", "L": "Libertarian"}
# Ballot party codes of other parties and independents in the sources (OpenElections, county reports).
OTHER_PARTY = {"IND": "Independent", "IRP": "Indiana Redemption Party", "WTP": "We the People"}
# Ticket races in the 2024 OpenElections file run both names together ("Mike Braun Micah Beckwith"), title-cased from the
# ballot's capitals. Shown as "Governor / Lieutenant Governor"; "Jd" is the title-casing of the ballot's "JD".
TICKETS = {
    "Kamala D. Harris Tim Walz": "Kamala D. Harris / Tim Walz",
    "Donald J. Trump Jd Vance": "Donald J. Trump / JD Vance",
    "Chase Oliver Mike Ter Maat": "Chase Oliver / Mike Ter Maat",
    "Robert F. Kennedy Jr. Nicole Shanahan": "Robert F. Kennedy Jr. / Nicole Shanahan",
    "Jennifer G. Mccormick Terry Goodin": "Jennifer G. McCormick / Terry Goodin",
    "Mike Braun Micah Beckwith": "Mike Braun / Micah Beckwith",
    "Donald Rainwater Tonya Hudson": "Donald Rainwater / Tonya Hudson",
}
VIDX = {"D": 0, "R": 1, "L": 2, "O": 3, "W": 4}   # vote vector order: D, R, L, other party, write-ins


def split_contest(contest):
    """'state-senate-8' -> ('state-senate', '8'); 'president' -> ('president', None)."""
    if contest in OFFICE:
        return contest, None
    for key, _lv, _lab, dl in OFFICES:
        if dl and contest.startswith(key + "-"):
            d = contest[len(key) + 1:]
            # township and town races keep their slug ('centre', 'walkerton-ward-1'); district letters are capitals
            return key, (d if key in LOCAL_OFFICES else d.upper())
    raise SystemExit(f"precinct_results.csv contest {contest!r} has no ballot-order position (add it to OFFICES)")


def district_sort(d):
    return (0, int(d), "") if d.isdigit() else (1, 0, d)


def district_info(office_key, district):
    """(name in the picker and race label, area named in 'outside ...' and 'part of ...' messages, scope noun).
    'state-senate', '8' -> ('District 8', 'State Senate, District 8', 'district');
    'township-board', 'centre' -> ('Centre Township', 'Centre Township', 'township');
    'town-council', 'walkerton-ward-1' -> ('Walkerton Ward 1', 'the town of Walkerton', 'ward');
    'town-council', 'roseland' -> ('Roseland at-large', 'the town of Roseland', 'town')."""
    if office_key.startswith("township-"):
        nm = district.replace("-", " ").title() + " Township"
        return nm, nm, "township"
    if office_key == "town-council":
        m = re.fullmatch(r"([a-z-]+?)-ward-(\d+)", district)
        town = (m.group(1) if m else district).replace("-", " ").title()
        if m:
            return f"{town} Ward {m.group(2)}", f"the town of {town}", "ward"
        return f"{town} at-large", f"the town of {town}", "town"
    return f"District {district}", f"{OFFICE[office_key][2]}, District {district}", "district"


def race_label(office_key, district, year):
    lab = OFFICE[office_key][2]
    return f"{lab}{', ' + district_info(office_key, district)[0] if district else ''}, {year}"


def races_by_rule(rows):
    """[(id, label, eid, contest, office, district)] for every (election, contest) in precinct_results.csv, in rule order."""
    present = sorted({(r["election_id"], r["contest"]) for r in rows})
    out = []
    for eid, contest in present:
        office, district = split_contest(contest)
        out.append((f"{contest}-{eid[:4]}", race_label(office, district, eid[:4]), eid, contest, office, district))
    order = [o[0] for o in OFFICES]
    out.sort(key=lambda r: (order.index(r[4]), district_sort(r[5] or ""), -int(r[2][:4])))
    return out


def write_votes(edir, units, shapes):
    """derived/map_votes.json: per-race totals by precinct, township and place, from precinct_results.csv."""
    import re as _re
    res_path = edir / "precinct_results.csv"
    areas_path = edir / "derived" / "precinct_areas.json"
    if not res_path.exists() or not areas_path.exists():
        print("  (no precinct_results.csv / precinct_areas.json: votes file not written)")
        return
    adoc = json.load(open(areas_path, encoding="utf-8"))
    areas = adoc["areas"]
    checks = adoc.get("county_check", {})
    rows = list(csv.DictReader(open(res_path, encoding="utf-8")))
    RACES = races_by_rule(rows)
    rid_of = {(eid, contest): rid for rid, _l, eid, contest, _o, _d in RACES}
    name_by = {}
    cand = {}       # rid -> party -> {candidate: votes}
    oparty = {}     # rid -> set of ballot party codes for O
    srcs = {}       # rid -> set of source ids
    tot = {}        # (race, code) -> [D, R, L, O, W]
    county = {rid: [0, 0, 0, 0, 0] for rid, *_ in RACES}   # every precinct in the race, placed or not
    existed = defaultdict(set)                              # eid -> precinct codes with any result that year
    seats = {}      # rid -> number of seats (the ballot's "Vote For")
    for r in rows:
        rid = rid_of[(r["election_id"], r["contest"])]
        vf = int(r["vote_for"])
        if seats.setdefault(rid, vf) != vf:
            raise SystemExit(f"{rid}: precinct rows disagree on the number of seats")
        if r["party"] != "W" and not r["candidate"] and r["contest"].startswith(LOCAL_OFFICES):
            raise SystemExit(f"{rid}: precinct {r['precinct_code']} has a {r['party']} row without a candidate name")
        code = r["precinct_code"]
        name_by[(r["election_id"], code)] = r["precinct_name"]
        existed[r["election_id"]].add(code)
        v = int(r["votes"])
        i = VIDX[r["party"]]
        t = tot.setdefault((rid, code), [0, 0, 0, 0, 0])
        t[i] += v
        county[rid][i] += v
        srcs.setdefault(rid, set()).add(r["source_id"])
        if r["party"] != "W" and r["candidate"]:
            cand.setdefault(rid, {}).setdefault(r["party"], defaultdict(int))[r["candidate"]] += v
        if r["party"] == "O":
            oparty.setdefault(rid, set()).add(r["ballot_party"])

    def fix(n):
        n = TICKETS.get(n, n)
        return _re.sub(r"\bMc([a-z])", lambda m: "Mc" + m.group(1).upper(), n)
    for rid, _l, eid, contest, _o, _d in RACES:
        if eid == "2024g" and contest in ("president", "governor"):
            for p, names in cand.get(rid, {}).items():
                for nm in names:
                    if nm not in TICKETS:
                        raise SystemExit(f"{rid}: ticket name {nm!r} has no display form in TICKETS")
    races = []
    for rid, label, eid, contest, office, district in RACES:
        chk = checks.get(f"{eid}|{contest}", {})
        cv = county[rid]
        parties = [p for p in ("D", "R", "L", "O") if cv[VIDX[p]] or p in cand.get(rid, {})]
        ballot = sorted(parties, key=lambda p: -cv[VIDX[p]])
        pair = ballot[:2] if len(ballot) >= 2 else ballot
        if set(pair) != {"D", "R"} and len(pair) == 2 and "D" in ballot and "R" in ballot:
            raise SystemExit(f"{rid}: Democratic and Republican candidates are not the two leading parties")
        cands = {p: "; ".join(fix(n) for n in sorted(names, key=lambda n: -names[n])) for p, names in cand.get(rid, {}).items()}
        op = sorted(oparty.get(rid, set()))
        unknown = [c for c in op if c not in OTHER_PARTY]
        if unknown:
            raise SystemExit(f"{rid}: other-party code(s) {unknown} have no name in OTHER_PARTY")
        src = sorted(srcs[rid] & SRC_BY)
        ns = seats[rid]
        if chk and chk.get("seats", ns) != ns:
            raise SystemExit(f"{rid}: seats {ns} in precinct_results.csv but {chk['seats']} in the county check")
        ncand = {p: len(names) for p, names in cand.get(rid, {}).items()}
        # uncontested: no more candidates on the ballot than seats (write-ins are not on the ballot); for single-seat
        # races whose sources carry no candidate names this is "one party on the ballot", as before
        uncontested = len(ballot) == 1 if ns == 1 else sum(ncand.values()) <= ns
        rec = {"id": rid, "label": label, "eid": eid, "year": int(eid[:4]), "contest": contest,
               "level": OFFICE[office][1], "office": office, "district": district,
               "partial": office in PARTIAL_DISTRICT, "cand": cands,
               "oparty": " / ".join(OTHER_PARTY[c] for c in op) if op else "",
               "pair": pair, "uncontested": uncontested,
               "src": src, "county": cv, "county_checked": chk.get("match", False),
               "check_note": chk.get("note", "")}
        if district:
            dname, area, unit = district_info(office, district)
            rec.update({"dname": dname, "area": area, "unit": unit})
        if ns > 1:
            raw = chk.get("winners", [])
            if not raw or len(raw) > ns:
                raise SystemExit(f"{rid}: vote for {ns} but no winners list in the county check")
            for nm, p in raw:
                if nm not in cand.get(rid, {}).get(p, {}):
                    raise SystemExit(f"{rid}: winner {nm} ({p}) is not among the precinct results' candidates")
            winners = [[fix(nm), p] for nm, p in raw]
            rec.update({"seats": ns, "winners": winners, "ncand": ncand})
        races.append(rec)
    tw_uid = lambda name: slugify(name) + "-township"
    precinct, township, place = {}, {}, {}
    unplaced = {rid: [] for rid, *_ in RACES}
    eid_of = {rid: e for rid, _l, e, *_x in RACES}

    def uids(code):
        a = areas.get(code)
        if a is None:
            return None, None
        tuid = tw_uid(a["township"]) if a["township"] else None
        puid = slugify(a["place"]) if a["place"] else None
        return (tuid if tuid in units else None), (puid if puid in units else None)
    for (rid, code), t in sorted(tot.items()):
        a = areas.get(code)
        eid = eid_of[rid]
        if a is None:
            unplaced[rid].append({"code": code, "name": name_by.get((eid, code), code), "votes": sum(t)})
            continue
        tuid, puid = uids(code)
        pe = precinct.setdefault(code, {"n": name_by.get((eid, code), code), "t": tuid, "p": puid,
                                        "ps": a["place_share"], "e": [], "v": {}})
        pe["v"][rid] = t
        for uid, store in ((tuid, township), (puid, place)):
            if uid:
                e = store.setdefault(uid, {"n": {}, "v": {}})
                cur = e["v"].setdefault(rid, [0, 0, 0, 0, 0, 0])
                for i in range(5):
                    cur[i] += t[i]
                cur[5] += 1
    # precincts each area had in each election (any race), so a district race can say how much of the area it covers
    for eid, codes in existed.items():
        for code in codes:
            if code not in precinct:
                continue
            precinct[code]["e"].append(int(eid[:4]))
            tuid, puid = uids(code)
            for uid, store in ((tuid, township), (puid, place)):
                if uid and uid in store:
                    store[uid]["n"][eid[:4]] = store[uid]["n"].get(eid[:4], 0) + 1
    for pe in precinct.values():
        pe["e"].sort()
    for code, pe in precinct.items():
        if pe["p"]:
            place[pe["p"]]["approx"] = place[pe["p"]].get("approx", False) or pe["ps"] < 0.97
    for e in place.values():
        e.setdefault("approx", False)
    offices = []
    for key, level, label, dlabel in OFFICES:
        rs = [r for r in races if r["office"] == key]
        if not rs:
            continue
        ds = sorted({r["district"] for r in rs if r["district"]}, key=district_sort) if dlabel else None
        o = {"key": key, "level": level, "label": label, "dlabel": dlabel, "districts": ds}
        if ds:
            o["dnames"] = {d: district_info(key, d)[0] for d in ds}
        offices.append(o)
    default = next(r["id"] for r in races if r["office"] == "president" and r["year"] == max(x["year"] for x in races))
    out = {"races": races, "default": default, "rule": RACE_RULE, "bands": [5, 15, 30],
           "levels": [{"key": k, "label": lab} for k, lab in LEVELS if any(o["level"] == k for o in offices)],
           "offices": offices,
           "precinct": precinct, "township": township, "place": place, "unplaced": unplaced,
           "note": "Races and their order follow RACE_RULE in tools/build_map.py. Vote vectors are D, R, L, other party, "
                   "write-ins; for townships and places a sixth number counts the precincts summed, and 'n' counts the "
                   "precincts each area had in each election year (any race). 'pair' is the two parties with the most "
                   "votes in the race (the margin's two sides). 'county' sums every precinct in the race (for district "
                   "races: every precinct in the district inside the county), including precincts with no Census 2020 "
                   "boundary. Built by tools/build_map.py from precinct_results.csv."}
    dest = edir / "derived" / "map_votes.json"
    dest.write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"wrote {dest} ({dest.stat().st_size:,} bytes): {len(races)} races, {len(precinct)} precincts, "
          f"{len(township)} townships, {len(place)} places")
    for lv, _lab in LEVELS:
        rs = [r for r in races if r["level"] == lv]
        print(f"  {lv}: {len(rs)} races: " + ", ".join(
            r["label"] + (" [uncontested]" if r["uncontested"] else "") +
            (f" [vote for {r['seats']}]" if r.get("seats") else "") +
            ("" if r["county_checked"] else " [county sum not checked]") for r in rs))
    for rid, lst in unplaced.items():
        if lst:
            print(f"  unplaced in {rid} (no Census 2020 boundary): " + ", ".join(f"{u['code']} ({u['votes']} votes)" for u in lst))


def export_svg(dest: Path, data):
    vb = data["viewBox"]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vb[2]} {vb[3]}" width="{vb[2]}" height="{vb[3]}" '
             f'role="img" aria-label="Townships and incorporated places of St. Joseph County, Indiana">',
             "<title>St. Joseph County, Indiana: townships and towns (Census TIGER 2026)</title>",
             f"<!-- Source: {data['source_note']} Boundaries are Census TIGER and may differ from county GIS. -->",
             '<rect width="100%" height="100%" fill="#ffffff"/>',
             '<g fill="#e8ebea" stroke="#ffffff" stroke-width="1" stroke-linejoin="round">']
    for it in data["layers"]["township"]:
        parts.append(f'<path id="{it["id"]}" d="{it["d"]}"><title>{it["census_name"]}</title></path>')
    parts.append("</g>")
    parts.append('<g fill="#9fd3c7" stroke="#2b6f63" stroke-width=".8" stroke-linejoin="round">')
    for it in data["layers"]["place"]:
        parts.append(f'<path id="{it["id"]}" d="{it["d"]}"><title>{it["census_name"]}</title></path>')
    parts.append("</g>")
    parts.append(f'<path d="{data["county"]["d"]}" fill="none" stroke="#59636a" stroke-width="1.4" stroke-linejoin="round"/>')
    parts.append('<g font-family="system-ui,sans-serif" font-size="8" fill="#15191b" text-anchor="middle" '
                 'paint-order="stroke" stroke="#ffffff" stroke-width="2.5">')
    for it in data["layers"]["township"]:
        parts.append(f'<text x="{it["label"][0]}" y="{it["label"][1]}" fill="#59636a" font-size="9">'
                     f'{it["census_name"].replace(" township", "")}</text>')
    for it in data["layers"]["place"]:
        parts.append(f'<text x="{it["label"][0]}" y="{it["label"][1]}" font-weight="700">'
                     f'{it["census_name"].rsplit(" ", 1)[0]}</text>')
    parts.append("</g></svg>")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(parts), encoding="utf-8", newline="\n")
    print(f"wrote {dest} ({dest.stat().st_size:,} bytes)")


if __name__ == "__main__":
    sys.exit(main())
