"""Build simplified SVG paths for Indiana's 92 counties from the US counties GeoJSON.

Usage: python -P -E tools/make_indiana_map.py
Input:  sources/geo/us-counties-fips.geojson  (Census-derived county boundaries, plotly/datasets)
Output: data/indiana/counties_svg.json  {viewBox, counties: [{fips, name, d, cx, cy}]}
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "sources" / "geo" / "us-counties-fips.geojson"
OUT = ROOT / "data" / "indiana" / "counties_svg.json"
WIDTH = 300.0  # viewBox width; height follows the state's aspect ratio


def rings(geom):
    if geom["type"] == "Polygon":
        yield from geom["coordinates"]
    elif geom["type"] == "MultiPolygon":
        for poly in geom["coordinates"]:
            yield from poly


def main() -> None:
    gj = json.loads(SRC.read_text(encoding="utf-8"))
    feats = [f for f in gj["features"] if f["properties"]["STATE"] == "18"]
    assert len(feats) == 92, f"expected 92 Indiana counties, got {len(feats)}"
    pts = [p for f in feats for r in rings(f["geometry"]) for p in r]
    lon0, lon1 = min(p[0] for p in pts), max(p[0] for p in pts)
    lat0, lat1 = min(p[1] for p in pts), max(p[1] for p in pts)
    k = math.cos(math.radians((lat0 + lat1) / 2))  # equirectangular, scaled at mid-latitude
    sx = WIDTH / ((lon1 - lon0) * k)
    height = (lat1 - lat0) * sx

    def proj(p):
        return ((p[0] - lon0) * k * sx, (lat1 - p[1]) * sx)

    counties = []
    for f in feats:
        parts, xs, ys = [], [], []
        for r in rings(f["geometry"]):
            q = [proj(p) for p in r]
            # light simplification: drop points closer than 0.4 units to the previous kept point
            kept = [q[0]]
            for x, y in q[1:]:
                if math.hypot(x - kept[-1][0], y - kept[-1][1]) >= 0.4:
                    kept.append((x, y))
            if len(kept) < 3:
                continue
            parts.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in kept) + "Z")
            xs += [x for x, _ in kept]
            ys += [y for _, y in kept]
        counties.append({
            "fips": "18" + f["properties"]["COUNTY"],
            "name": f["properties"]["NAME"],
            "d": "".join(parts),
            "cx": round(sum(xs) / len(xs), 1),
            "cy": round(sum(ys) / len(ys), 1),
        })
    counties.sort(key=lambda c: c["name"])
    OUT.write_text(json.dumps({"viewBox": f"0 0 {WIDTH:.0f} {height:.0f}", "counties": counties}), encoding="utf-8")
    print(f"wrote {OUT} ({len(counties)} counties, viewBox 0 0 {WIDTH:.0f} {height:.0f}, {OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
