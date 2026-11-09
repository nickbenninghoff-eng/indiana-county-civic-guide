"""Election-district map: official district shapes as clickable areas with the boundary map's side panel.

    dshapes = load_district_shapes(ed, shapes)      # data/editions/<ed>/derived/district_shapes.json, or None
    rec = district_set(dshapes, "in-house-2021")    # one manifest set ({items: [...], notes, source_ids, ...}) or None
    district_map(page, ed, shapes, layers, default_layer, ...)  -> Markup (.cmap: tabs + <svg> + legend + panel)

Used by state/your-legislators/ (Indiana House and Senate) and county/ (commissioner and council districts).
Reuses the markup contract of civic/map.py (root .cmap, .cmap-tabs, .cmap-layer, a.cmap-a[data-uid], #cmap-panel,
#cmap-data), so static/js/map.js gives hover and focus, the panel that keeps the last area, touch
select-then-open and the layer tabs. Every district is an <a href> to its detail on the same page, so the map works
without JavaScript; static/js/pick_one.js opens that district's detail and collapses the others.

The districts are not shaded: the fills (static/css/district_map.css) only tell neighbors apart and never encode
party or any value. City and town outlines are drawn on top, without links, so a reader can find where they live.
Boundaries come only from the official files listed in sources/boundaries/districts/manifest.csv
(tools/build_district_shapes.py); the guide never draws or edits one.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .html import Markup, h, json_script
from .map import _label_boxes

N_FILLS = 4


def load_district_shapes(ed, shapes: dict | None) -> dict | None:
    """district_shapes.json, or None when it is missing or was projected for a different map frame."""
    p = Path(ed.root) / "data" / "editions" / ed.edition_id / "derived" / "district_shapes.json"
    if not p.is_file():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    if shapes and [round(float(v), 1) for v in data.get("viewBox", [])] != [round(float(v), 1) for v in shapes["viewBox"]]:
        ed.warnings.append("district map: district_shapes.json viewBox differs from map_shapes.json; district maps "
                           "left out (rerun tools/build_district_shapes.py)")
        return None
    return data


def district_set(dshapes: dict | None, set_id: str) -> dict | None:
    """One manifest set with at least one shape, else None."""
    rec = ((dshapes or {}).get("sets") or {}).get(set_id)
    return rec if rec and rec.get("items") else None


_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def _points(d: str) -> set:
    nums = _NUM.findall(d)
    return {(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)}


def neighbor_fills(items: list[dict]) -> dict:
    """{district: fill index 0..3}: neighbors (districts whose paths share at least two vertices, which the shared-arc
    simplification of build_district_shapes.py keeps identical) get different fills. Greedy, most neighbors first."""
    pts = {it["district"]: _points(it["d"]) for it in items}
    adj = {k: set() for k in pts}
    ks = list(pts)
    for i, a in enumerate(ks):
        for b in ks[i + 1:]:
            if len(pts[a] & pts[b]) >= 2:
                adj[a].add(b)
                adj[b].add(a)
    out = {}
    for k in sorted(ks, key=lambda k: (-len(adj[k]), ks.index(k))):
        used = {out[n] for n in adj[k] if n in out}
        out[k] = next((c for c in range(N_FILLS) if c not in used), ks.index(k) % N_FILLS)
    return out


def _box(x: float, y: float, w: float, fs: float, anchor: str) -> tuple:
    x0 = x - w / 2 if anchor == "middle" else (x if anchor == "start" else x - w)
    return (x0, y - fs, x0 + w, y + 2)


def _city_labels(spots, items) -> list:
    """City names (placed by civic/map.py _label_boxes), moved down a line at a time while they would cover one of
    this layer's district numbers. Drawn inside each layer, since the district numbers differ by layer."""
    taken = []
    for it in items:
        if it.get("label"):
            fs = 10.5 if it.get("label_r", 99) < 22 else 15
            w = len(it["text"]) * fs * 0.62 + 4
            taken.append(_box(it["label"][0], it["label"][1] + 4, w, fs, "middle"))
    out = []
    for it, x, y, anchor in spots:
        fs = 9.5
        w = len(it["short"]) * fs * 0.6
        for _ in range(6):
            b = _box(x, y, w, fs, anchor)
            if not any(b[0] < t[2] and t[0] < b[2] and b[1] < t[3] and t[1] < b[3] for t in taken):
                break
            y += fs + 3
        taken.append(_box(x, y, w, fs, anchor))
        out.append(h("text", {"x": x, "y": round(y, 1), "text-anchor": anchor, "class": "cmap-label dmap-city"}, it["short"]))
    return out


def district_map(page, ed, shapes: dict, layers: list[dict], default_layer: str, *, label: str, hint: str,
                 notes=None, extra_cls: str = "") -> Markup:
    """layers: [{"tab", "label", "items": [{"uid", "district", "d", "href", "aria", "entry", "text", "label",
    "label_r"}], "legend": Markup}]. Each entry is the panel record map.js reads (n, t, f, cav, note, href, open);
    its path is left out (map.js takes it from the shape for the highlight)."""
    vb = shapes["viewBox"]
    data, groups, tabs, legends = {}, [], [], []
    # cities and towns on top, outline only, no links: where a reader lives, not a layer of its own
    places = [it for it in shapes["layers"].get("place", []) if it.get("id") in ed.units]
    outline = [h("path", {"d": it["d"], "class": "dmap-place"}) for it in places]
    city_items = [dict(it, short=ed.units[it["id"]]["name"].replace("City of ", "")) for it in places
                  if ed.units[it["id"]]["unit_type"] == "city"]
    city_spots = _label_boxes(city_items, vb[2])
    city_groups = []
    for L in layers:
        on = L["tab"] == default_layer
        fills = neighbor_fills(L["items"])
        paths, labels = [], []
        for it in L["items"]:
            data[it["uid"]] = {k: v for k, v in it["entry"].items() if k != "d"}
            paths.append(h("a", {"href": it["href"], "class": "cmap-a", "data-uid": it["uid"], "aria-label": it["aria"]},
                           h("path", {"d": it["d"], "class": f"cmap-s dmap-s dmap-f{fills[it['district']]}"})))
            if it.get("label"):
                labels.append(h("text", {"x": it["label"][0], "y": it["label"][1] + 4, "text-anchor": "middle",
                                         "class": "cmap-label dmap-label" + (" dmap-label-sm" if it.get("label_r", 99) < 22 else "")},
                                it["text"]))
        groups.append(h("g", {"class": "cmap-layer" + (" is-on" if on else ""), "data-layer": L["tab"], "role": "group",
                              "aria-label": f"Layer: {L['label']}"},
                        h("g", {"clip-path": "url(#cmap-clip)"}, paths)))
        # district numbers and city names over the city lines; one set per layer (static/js/map.js shows the
        # [data-layer] that is on)
        city_groups.append(h("g", {"class": "cmap-layer dmap-over" + (" is-on" if on else ""), "data-layer": L["tab"],
                                   "aria-hidden": "true"}, labels, _city_labels(city_spots, L["items"])))
        tabs.append(h("button", {"type": "button", "class": "cmap-tab", "data-layer": L["tab"],
                                 "aria-pressed": "true" if on else "false"}, L["label"]))
        legends.append(h("div", {"class": "cmap-mlegend dmap-legend" + (" is-on" if on else ""), "data-layer": L["tab"]},
                         L.get("legend")))
    svg = h("svg", {"class": "cmap-svg", "viewBox": f"{vb[0]} {vb[1]} {vb[2]} {vb[3]}", "role": "group",
                    "aria-label": label},
            h("defs", None, h("clipPath", {"id": "cmap-clip"}, h("path", {"d": shapes["county"]["d"]}))),
            groups,
            h("g", {"class": "dmap-over", "aria-hidden": "true", "clip-path": "url(#cmap-clip)"}, outline),
            city_groups,
            h("path", {"d": shapes["county"]["d"], "class": "cmap-outline", "aria-hidden": "true"}),
            h("g", {"class": "cmap-hl-g", "aria-hidden": "true", "clip-path": "url(#cmap-clip)"}))
    panel = h("aside", {"class": "cmap-panel", "id": "cmap-panel", "aria-live": "polite", "aria-label": "Selected district"},
              h("p", {"class": "cmap-hint"}, hint))
    root = {"class": "cmap dmap" + (" cmap-single" if len(layers) == 1 else "") + (f" {extra_cls}" if extra_cls else ""),
            "data-default-layer": default_layer, "data-hash": "off"}
    return h("div", root,
             h("div", {"class": "cmap-bar"},
               h("div", {"class": "cmap-tabs", "role": "group", "aria-label": "Map layer", "hidden": True}, tabs)),
             h("div", {"class": "cmap-grid"},
               h("div", {"class": "cmap-stage"}, svg, legends,
                 h("p", {"class": "dmap-key muted"},
                   h("span", {"class": "dmap-key-line", "aria-hidden": "true"}), "City and town lines, for finding "
                   "where you live. Fills only tell neighboring districts apart; they show no party or amount.")),
               h("div", {"class": "dmap-side"}, panel, notes)),
             json_script("cmap-data", data))
