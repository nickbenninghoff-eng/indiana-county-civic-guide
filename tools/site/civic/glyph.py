"""Indiana outline glyph (masthead) and the full 92-county map, from counties_svg.json.

Colors come from CSS classes only (.glyph-county, .glyph-edition, .map-county ...).
"""
from __future__ import annotations

import re

from .html import Markup, esc, h

_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def _round_path(d: str, places: int = 0) -> str:
    def r(m):
        v = round(float(m.group(0)), places)
        return str(int(v)) if places == 0 else f"{v:g}"
    return _NUM.sub(r, d)


GLYPH_ASSET = "assets/indiana-glyph.svg"


def glyph_asset_svg(ed) -> str:
    """assets/indiana-glyph.svg (2026-11-18, maps-cleanup brief part B item 2: the masthead drew the 92 county paths
    inline on every page, ~12 KB each): the other counties as one group (#in-rest) and the edition county
    (#in-edition). No colour in the file: each page's <use class="glyph-county|glyph-edition"> passes its CSS fill and
    stroke down (inherited), so every look and theme still colours it; vector-effect is not inherited, so it is here."""
    svg = ed.counties_svg
    fips = ed.config["fips"]
    rest = " ".join(_round_path(c["d"]) for c in svg["counties"] if c["fips"] != fips)
    mine = " ".join(_round_path(c["d"]) for c in svg["counties"] if c["fips"] == fips)
    # str(): esc() returns Markup, and Markup + str would escape the plain string (the whole file came out escaped)
    vb, rest, mine = str(esc(svg["viewBox"])), str(esc(rest)), str(esc(mine))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}"><defs>'
            f'<path id="in-rest" vector-effect="non-scaling-stroke" d="{rest}"/>'
            f'<path id="in-edition" vector-effect="non-scaling-stroke" d="{mine}"/>'
            '</defs></svg>\n')


def write_glyph_asset(site) -> int:
    dest = site.out / GLYPH_ASSET
    dest.parent.mkdir(parents=True, exist_ok=True)
    text = glyph_asset_svg(site.ed)
    dest.write_text(text, encoding="utf-8", newline="\n")
    return len(text.encode("utf-8"))


def indiana_glyph_use(ed, href: str, css_class: str = "glyph", title: str | None = None) -> Markup:
    """The masthead glyph from the shared asset (``href`` = the page's relative link to GLYPH_ASSET)."""
    t = title or f"Indiana, with {ed.county_label} filled in"
    return h("svg", {"class": css_class, "viewBox": ed.counties_svg["viewBox"], "role": "img", "aria-label": t,
                     "focusable": "false"}, h("title", None, t),
             h("use", {"class": "glyph-county", "href": f"{href}#in-rest"}),
             h("use", {"class": "glyph-edition", "href": f"{href}#in-edition"}))


def indiana_glyph(ed, css_class: str = "glyph", title: str | None = None) -> Markup:
    """Small locator glyph: faint county grid, edition county filled (inline paths)."""
    svg = ed.counties_svg
    fips = ed.config["fips"]
    paths = []
    for c in svg["counties"]:
        cls = "glyph-edition" if c["fips"] == fips else "glyph-county"
        paths.append(h("path", {"class": cls, "d": _round_path(c["d"])}))
    t = title or f"Indiana, with {ed.county_label} filled in"
    return h("svg", {"class": css_class, "viewBox": svg["viewBox"], "role": "img",
                     "aria-label": t, "focusable": "false"}, h("title", None, t), paths)


def county_map(ed, href_for) -> Markup:
    """Full map. ``href_for(county_row) -> str | None`` gives a link for built editions."""
    svg = ed.counties_svg
    parts = []
    for c in sorted(svg["counties"], key=lambda c: c["name"]):
        href = href_for(c)
        name = f"{c['name']} County"
        if href:
            tip_l = "Edition built: open the guide"
            shape = h("path", {"class": "map-county map-built", "d": c["d"]})
            words = c["name"].split()
            y0 = c["cy"] + 3 - 4.5 * (len(words) - 1)
            label = h("text", {"class": "map-label map-label-built", "x": c["cx"], "y": f"{y0:.1f}",
                               "text-anchor": "middle"},
                      [h("tspan", {"x": c["cx"], "dy": "0" if i == 0 else "9"}, w) for i, w in enumerate(words)])
            parts.append(h("a", {"href": href, "class": "map-link", "data-tv": name, "data-tl": tip_l,
                                 "aria-label": f"{name}: edition built, open the guide"}, shape, label))
        else:
            tip_l = "Edition not built yet; the Indiana-wide chapters still apply"
            parts.append(h("path", {"class": "map-county", "d": c["d"], "tabindex": "0", "data-tv": name,
                                    "data-tl": tip_l, "role": "img",
                                    "aria-label": f"{name}: edition not built yet"}))
    return h("svg", {"class": "county-map", "viewBox": svg["viewBox"], "role": "group",
                     "aria-label": "Map of Indiana's 92 counties"}, parts)
