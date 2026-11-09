"""Convert the official election-district boundaries (sources/boundaries/districts/<set_id>.geojson, indexed by
sources/boundaries/districts/manifest.csv) into data/editions/<edition>/derived/district_shapes.json, the SVG-ready
district layers of the campaign-money map (tools/site/civic/campaign_map.py).

    python -P -E tools/build_district_shapes.py --edition st-joseph [--tolerance 0.25]

Stdlib only. Same projection, clipping and shared-arc Douglas-Peucker simplification as tools/build_map.py (the
functions are imported from it, and the projection is rebuilt from the same county outline and constants), so the
district paths sit exactly on the boundary map's viewBox; the output records that viewBox and the site build refuses
the file if it no longer matches derived/map_shapes.json. Districts reaching past the county (state legislative
districts) are clipped to the padded county rectangle here and to the county outline when drawn; each district's
share of the county's area is estimated by grid sampling, as build_map.py does.

Only manifest rows with a file are converted. Rows without one (no official polygon found) are recorded with their
status and notes, so the site can say why a set has no shapes. Boundaries are never drawn or edited here: every
coordinate comes from the official file.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_map as bm  # noqa: E402

ROOT = HERE.parent
DIST = ROOT / "sources" / "boundaries" / "districts"


def projection():
    """(proj, inside_county, viewBox, clip) exactly as build_map.main builds them."""
    county = json.load(open(bm.BOUNDS / "county.geojson", encoding="utf-8"))["features"][0]
    cgeom = county["geometry"]
    allpts = [p for poly in bm.polys(cgeom) for ring in poly for p in ring]
    lon0, lon1 = min(p[0] for p in allpts), max(p[0] for p in allpts)
    lat0, lat1 = min(p[1] for p in allpts), max(p[1] for p in allpts)
    kx = math.cos(math.radians((lat0 + lat1) / 2))
    scale = bm.VIEW_W / ((lon1 - lon0) * kx)
    W = bm.VIEW_W + 2 * bm.PAD
    H = (lat1 - lat0) * scale + 2 * bm.PAD

    def proj(p):
        return ((p[0] - lon0) * kx * scale + bm.PAD, (lat1 - p[1]) * scale + bm.PAD)
    px, py = (lon1 - lon0) * 0.02, (lat1 - lat0) * 0.02
    clip = (lon0 - px, lat0 - py, lon1 + px, lat1 + py)
    grid = []
    N = 110
    for i in range(N):
        for j in range(N):
            x, y = lon0 + (lon1 - lon0) * (i + .5) / N, lat0 + (lat1 - lat0) * (j + .5) / N
            if bm.inside_geom(x, y, cgeom):
                grid.append((x, y))
    return proj, grid, [0, 0, round(W, 1), round(H, 1)], clip


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--edition", default="st-joseph")
    ap.add_argument("--tolerance", type=float, default=0.25, help="Douglas-Peucker tolerance in SVG units")
    args = ap.parse_args(argv)
    edir = ROOT / "data" / "editions" / args.edition
    man = DIST / "manifest.csv"
    if not man.is_file():
        print(f"no {man}; nothing to do")
        return 0
    proj, grid, viewbox, clip = projection()
    sets = {}
    with open(man, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for m in rows:
        sid = m["set_id"].strip()
        rec = {k: (m.get(k) or "").strip() for k in ("office_pattern", "districts", "first_election", "last_election",
                                                     "adopted_by", "source_ids", "retrieved", "status", "notes")}
        rec["file"] = (m.get("file") or "").strip()
        rec["items"] = []
        if not rec["file"]:
            sets[sid] = rec
            continue
        path = DIST / rec["file"]
        if not path.is_file():
            rec["status"] = "file_missing"
            print(f"  {sid}: {rec['file']} not found; recorded without shapes")
            sets[sid] = rec
            continue
        feats = json.load(open(path, encoding="utf-8"))["features"]
        keep, share = {}, {}
        for f in feats:
            d = str(f["properties"].get("district", "")).strip()
            if not d:
                raise SystemExit(f"{path}: a feature has no 'district' property")
            if d in keep:
                raise SystemExit(f"{path}: district {d!r} appears twice")
            plist = []
            for poly in bm.polys(f["geometry"]):
                rings = []
                for k, ring in enumerate(poly):
                    c = bm.clip_ring(ring[:-1], *clip)
                    if c:
                        rings.append([proj(p) for p in c])
                    elif k == 0:
                        break
                if rings:
                    plist.append(rings)
            if not plist:
                print(f"  {sid}: district {d} lies outside the county's frame; left out")
                continue
            keep[d] = plist
            n_in = sum(bm.inside_geom(x, y, f["geometry"]) for x, y in grid)
            share[d] = round(n_in / len(grid), 4) if grid else None
        simp = bm.simplify_layer(keep, args.tolerance)
        for d, plist in simp.items():
            if not plist:
                continue
            lp, rad, bb = bm.label_point(plist)
            rec["items"].append({"district": d, "d": bm.path_d(plist), "label": [round(lp[0], 1), round(lp[1], 1)],
                                 "label_r": round(rad, 1), "bbox": [round(v, 1) for v in bb],
                                 "county_share": share.get(d)})
        rec["items"].sort(key=lambda it: (len(it["district"]), it["district"]))
        sets[sid] = rec
        print(f"  {sid}: {len(rec['items'])} districts, path bytes {sum(len(i['d']) for i in rec['items']):,}")
    shapes = edir / "derived" / "map_shapes.json"
    if shapes.is_file():
        vb = json.loads(shapes.read_text(encoding="utf-8"))["viewBox"]
        if [round(float(v), 1) for v in vb] != viewbox:
            raise SystemExit(f"viewBox {viewbox} differs from map_shapes.json {vb}: rerun tools/build_map.py first")
    data = {"note": "Official district boundaries from sources/boundaries/districts (manifest.csv); projected like "
                    "map_shapes.json by tools/build_district_shapes.py.",
            "viewBox": viewbox, "tolerance": args.tolerance, "sets": sets}
    dest = edir / "derived" / "district_shapes.json"
    dest.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"wrote {dest} ({dest.stat().st_size:,} bytes), viewBox {viewbox}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
