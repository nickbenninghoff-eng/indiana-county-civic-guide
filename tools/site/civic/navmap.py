"""Map navigator: the county map as a way to browse any hub or list page (2026-11-18, maps on every major page).

One shared component for every hub, browse and landing page that lists things by area (planning/maps-cleanup-brief-
2026-11-18.md, part A). The reader chooses a layer, points at or selects an area, and the page's own list filters to
that area (static/js/navmap.js); selecting the same area again, or the "Open" link, opens the area's page. The saved
place (here.js window.civicHere) is the starting selection where one is saved and the page has no saved-place line
of its own.

Geometry is never inlined. Every area path lives once in a shared asset, ``assets/navmap.svg`` (written by
``write_asset`` from the boundary files the Offices hub already draws: derived/map_shapes.json and
derived/district_shapes.json through pages/offices.py hub_areas; no new geometry), and each page carries one small
``<a href><use href="…assets/navmap.svg#nm-<uid>"/></a>`` per area. So the map renders and every area is a link
with JavaScript off, keyboard focus works on the links, and the shapes are one cached file shared by every page.
(The CSP allows it: an external ``<use>`` is an image-like same-origin load, ``img-src 'self'``.)

Areas are keys:
  ``u:<unit_id>``     a government (city, town, township, school corporation, county, a unit with no boundary file)
  ``o:<office_id>``   one office's district (county commissioner and council, city council, Indiana House/Senate)
  ``lvl:statewide`` / ``lvl:federal``   the offices every voter in the county votes on (no shape: a chip)
  ``g:<gid>``         a library or special unit that is only in the money files (a Governments hub page; a chip)
Rows of a page's list carry ``data-nm="<keys>"`` (``Tags.office`` / ``Tags.unit`` build the value and remember which
keys the page uses); the navigator draws only the layers that hold at least one of those keys, and lists the rest
(the county, the state and federal levels, units with no boundary file) as plain links beside the map.

Neutral: fills only tell kinds of government or neighbouring districts apart (the boundary map's tokens,
static/css/map.css and district_map.css); never party, never an amount. The guide draws only the county.
"""
from __future__ import annotations

import re
from collections import OrderedDict

from .html import Markup, h, join

ASSET = "assets/navmap.svg"
ASSET_ID = "nm-"           # id prefix of every shape in the asset

# (layer tab of pages/offices.py hub_areas, label, group)
LAYERS = [("cities", "Cities and towns", "gov"), ("townships", "Townships", "gov"),
          ("schools", "School corporations", "gov"),
          ("commissioners", "County commissioners", "district"), ("council", "County council", "district"),
          ("city-council", "City councils", "district"), ("house", "Indiana House", "district"),
          ("senate", "Indiana Senate", "district")]
GROUPS = OrderedDict([("gov", "Governments"), ("district", "Election districts")])
LEVEL_NAMES = {"statewide": "Statewide (every voter in the county)", "federal": "Federal (every voter in the county)"}
NO_SHAPE_NOTE = "No boundary file in the guide, so not drawn: choose it here."
KEY_NOTE = ("Fills only tell kinds of government or neighboring districts apart; they never show party or an amount. "
            "The guide draws only official boundary files.")


def unit_key(unit_id: str) -> str:
    return f"u:{unit_id}"


def office_key(office_id: str) -> str:
    return f"o:{office_id}"


def level_key(level: str) -> str:
    return f"lvl:{level}"


def _districted(office: dict) -> bool:
    d = (office.get("district") or "").strip().lower()
    return bool(d) and d != "at-large"


class Tags:
    """Builds the ``data-nm`` value of a page's rows and remembers every key used, so the navigator draws only the
    layers and chips that hold something on this page.

        tags = Tags(ed)
        attrs["data-nm"] = tags.office(office_id)        # "u:south-bend o:south-bend-mayor"
        attrs["data-nm"] = tags.unit(unit_id)            # "u:penn-township"
        attrs["data-nm"] = tags.join(a, b)               # a row that belongs to several areas

    The county courts belong to the county too (the whole county elects or retains its judges); a statewide or federal
    office also carries its level key. An office id the edition does not know gives "" (the row is never filtered
    into an area it may not belong to; with a filter on it is hidden like any row of another area)."""

    def __init__(self, ed):
        self.ed = ed
        self.used: set = set()

    def _add(self, keys: list[str]) -> str:
        keys = list(dict.fromkeys(k for k in keys if k))
        self.used.update(keys)
        return " ".join(keys)

    def unit_keys(self, unit_id: str) -> list[str]:
        if not unit_id or unit_id not in self.ed.units:
            return []
        keys = [unit_key(unit_id)]
        if self.ed.units[unit_id]["unit_type"] == "court_system":
            keys.append(unit_key("county"))
        return keys

    def office_keys(self, office_id: str) -> list[str]:
        o = self.ed.offices.get(office_id or "")
        if not o:
            return []
        from . import offices as om
        keys = self.unit_keys(o["unit_id"]) + [office_key(office_id)]
        lv = om.level(self.ed, o)
        if lv in LEVEL_NAMES:
            keys.append(level_key(lv))
        return keys

    def unit(self, unit_id: str) -> str:
        return self._add(self.unit_keys(unit_id))

    def office(self, office_id: str) -> str:
        return self._add(self.office_keys(office_id))

    def gov(self, g) -> str:
        """A government of the Governments hub (civic/governments.py Gov): its unit key, or ``g:<gid>`` for a
        library or special unit that is only in the money files."""
        if g.unit_id and g.unit_id in self.ed.units:
            return self.unit(g.unit_id)
        return self._add([f"g:{g.gid}"])

    def join(self, *values: str) -> str:
        return self._add([k for v in values for k in (v or "").split()])


def tags_for(page) -> Tags:
    """The page's one Tags collector (made on first use), so row builders deep in a page module can tag rows without
    passing it around; the page's navigator then reads the same keys."""
    t = getattr(page, "_navmap_tags", None)
    if t is None:
        t = page._navmap_tags = Tags(page.ed)
    return t


# ----------------------------------------------------------------------------------------------- the model

def model(ed) -> dict | None:
    """The navigator's areas, cached on the edition: {"layers": OrderedDict tab -> {"label", "group", "items"}, "vb",
    "county_d", "back": [township paths]}. Items: {"uid", "key", "kind", "unit"|"office", "name", "short", "d",
    label fields}. None when the edition has no boundary file."""
    cached = getattr(ed, "_navmap_model", False)
    if cached is not False:
        return cached
    from .district_map import load_district_shapes
    from .map import load_shapes
    from pages.offices import hub_areas
    shapes = load_shapes(ed)
    if not shapes:
        ed._navmap_model = None
        return None
    hub = hub_areas(ed, shapes, load_district_shapes(ed, shapes))
    by_tab = {L["tab"]: L for L in hub["layers"]}
    layers: OrderedDict = OrderedDict()
    for tab, label, group in LAYERS:
        L = by_tab.get(tab)
        if not L:
            continue
        items = []
        for it in L["items"]:
            if it["kind"] == "gov":
                u = ed.units[it["unit"]]
                name = u["name"]
                items.append(dict(it, key=unit_key(it["unit"]), name=name,
                                  short=re.sub(r"^(City|Town) of ", "", name)))
            elif it["kind"] == "district":
                o = ed.offices[it["office"]]
                items.append(dict(it, key=office_key(it["office"]), name=o["title"], short=it.get("text") or ""))
        if items:
            layers[tab] = {"label": label, "group": group, "items": items}
    vb = shapes["viewBox"]
    vb = [float(v) for v in (vb.split() if isinstance(vb, str) else vb)]
    out = {"layers": layers, "vb": vb, "county_d": shapes["county"]["d"],
           "back": [(t.get("id") or f"t{n}", t["d"]) for n, t in enumerate(shapes["layers"].get("township", []))],
           "sources": hub.get("sources", [])}
    ed._navmap_model = out
    return out


def drawn_keys(ed) -> set:
    """Every area key that has a shape in the asset."""
    m = model(ed)
    return {it["key"] for L in (m["layers"].values() if m else []) for it in L["items"]}


# ----------------------------------------------------------------------------------------------- the asset

def asset_svg(ed) -> str | None:
    """assets/navmap.svg: every area path once, by id (nm-<uid>), plus the county outline (nm-county) and the
    township backdrop (nm-back-<id>). No fill, stroke colour or class: a page's <use> gives those through CSS
    inheritance, so the shapes follow every look and theme. Shapes are copied from the boundary files unchanged."""
    m = model(ed)
    if not m:
        return None
    vb = " ".join(f"{v:g}" for v in m["vb"])
    seen: set = set()
    paths = [f'<path id="{ASSET_ID}county" d="{m["county_d"]}"/>']
    seen.add("county")
    for bid, d in m["back"]:
        paths.append(f'<path id="{ASSET_ID}back-{bid}" d="{d}"/>')
    for L in m["layers"].values():
        for it in L["items"]:
            if it["uid"] in seen:
                continue
            seen.add(it["uid"])
            paths.append(f'<path id="{ASSET_ID}{it["uid"]}" d="{it["d"]}"/>')
    # vector-effect is not inherited, so each path carries it (and the line join) as a presentation attribute,
    # which travels with the referenced element into the page's <use>
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="' + vb + '">\n'
            '<!-- Indiana County Civic Guide: boundary shapes for the map navigator (civic/navmap.py). Copied unchanged '
            'from the official boundary files the guide lists; see about/sources. -->\n'
            '<defs>\n' + "\n".join(p.replace("<path ", '<path vector-effect="non-scaling-stroke" '
                                             'stroke-linejoin="round" ') for p in paths) +
            '\n</defs>\n</svg>\n')


def write_asset(site) -> int:
    """Write assets/navmap.svg (called by Site.write); returns its size in bytes (0 when there is no boundary file)."""
    svg = asset_svg(site.ed)
    if not svg:
        return 0
    dest = site.out / ASSET
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(svg, encoding="utf-8", newline="\n")
    return len(svg.encode("utf-8"))


# ----------------------------------------------------------------------------------------------- the component

def _natural(text: str):
    return [(0, int(t), "") if t.isdigit() else (1, 0, t.lower()) for t in re.findall(r"\d+|\D+", text)]


_ROW_KEYS = re.compile(r'( data-nm=")([^"]*)(")')


def _b36(n: int) -> str:
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    out = ""
    while True:
        n, r = divmod(n, 36)
        out = digits[r] + out
        if not n:
            return out


def compact_row_keys(html: str) -> str:
    """Write each row's area keys (data-nm) as base-36 numbers into one key list, data-nm-dict on every navigator root
    of the page (2026-11-18: the results page's 1,259 rows carried 57 KB of repeated keys, which took it over its
    700 KB budget). static/js/navmap.js reads them back. A page without a navigator is left as it is."""
    if "data-nm-target=" not in html or ' data-nm="' not in html:
        return html
    index: dict = {}

    def enc(m):
        toks = []
        for k in m.group(2).split():
            if k not in index:
                index[k] = _b36(len(index))
            toks.append(index[k])
        return m.group(1) + " ".join(toks) + m.group(3)

    html = _ROW_KEYS.sub(enc, html)
    keys = " ".join(index)          # in index order: position i is the key numbered i
    # on every navigator root (the only element with data-nm-target), open or folded ("nm nm-folded")
    return html.replace(' data-nm-target="', f' data-nm-dict="{keys}" data-nm-target="')


def expand_row_keys(html: str) -> str:
    """The inverse of compact_row_keys, for tests and tools that read the keys from a built page."""
    m = re.search(r'data-nm-dict="([^"]*)"', html)
    if not m:
        return html
    keys = m.group(1).split()
    return _ROW_KEYS.sub(lambda r: r.group(1) + " ".join(keys[int(t, 36)] for t in r.group(2).split()) + r.group(3),
                         html)


def default_href(page, key: str) -> str | None:
    """An area's own page: a government's page, an office's page, the Offices hub's level group."""
    from . import governments as gm
    from . import offices as om
    kind, _, ident = key.partition(":")
    if kind == "u":
        return gm.unit_href(page, ident)
    if kind == "o":
        return om.href(page, ident)
    if kind == "g":
        return gm.href(page, ident)
    if kind == "lvl" and om.HUB in page.site.by_path:
        return page.rel(om.HUB) + "#" + om.LEVEL_IDS[ident]
    return None


def _kind_class(ed, it) -> str:
    from .map import _kind_class as kc
    if it["kind"] == "gov":
        return "cmap-s " + kc(ed.units[it["unit"]], it.get("n", 0))
    return "cmap-s dmap-s dmap-f{}"


def navigator(page, tags: Tags, target: str, *, noun: str, plural: str, href_of=None, what: str | None = None,
              open_label: str = "Open its page", folded: bool = False, nm_id: str = "nm",
              layers: tuple | None = None, extra_chips: list | None = None, title: str = "Find by area",
              count_in: str | None = None) -> Markup | None:
    """The map navigator for one page. ``target`` is the id (or space-separated ids) of the container(s) whose
    ``[data-nm]`` rows it filters; ``noun``/``plural`` name a row ("office", "offices"); ``href_of(key)`` gives the
    page an area opens (None falls back to ``default_href``; an area with no page at all is a plain selectable area);
    ``what`` is the sentence under the title (what selecting does on this page). ``folded``: the map sits in a
    "Show map" fold that ships closed (long browse pages); otherwise it ships open (hubs).

    Returns None when the edition has no boundary file, or the page uses no area key (nothing to filter)."""
    from .district_map import neighbor_fills
    from .map import _label_boxes
    ed = page.ed
    m = model(ed)
    used = tags.used
    if not m or not used:
        return None
    asset = page.rel(ASSET)
    vb = m["vb"]

    def href(key):
        u = href_of(key) if href_of else None
        return u if u is not None else default_href(page, key)

    groups, buttons = [], OrderedDict((g, []) for g in GROUPS)
    shown_tabs = []
    for tab, L in m["layers"].items():
        if layers is not None and tab not in layers:
            continue
        if not any(it["key"] in used for it in L["items"]):
            continue
        shown_tabs.append(tab)
    if not shown_tabs and not used:
        return None
    default = shown_tabs[0] if shown_tabs else None
    for tab in shown_tabs:
        L = m["layers"][tab]
        on = tab == default
        fills = neighbor_fills([{"district": it["uid"], "d": it["d"]} for it in L["items"]]) \
            if L["group"] == "district" else {}
        shapes, texts, place_items = [], [], []
        for it in sorted(L["items"], key=lambda x: _natural(x["name"])):
            cls = _kind_class(ed, it)
            if it["kind"] == "district":
                cls = cls.format(fills.get(it["uid"], 0))
            u = href(it["key"])
            a = {"class": "cmap-a nm-a", "data-nm-key": it["key"], "aria-label": it["name"]}
            if u:
                a["href"] = u
            else:   # no page to open: still a focusable, selectable area
                a.update({"tabindex": "0", "role": "button"})
            kids = [h("use", {"href": f"{asset}#{ASSET_ID}{it['uid']}", "class": cls})]
            if tab == "cities" and it.get("label_r", 99) < 6 and it.get("label"):
                kids.append(h("circle", {"cx": it["label"][0], "cy": it["label"][1], "r": 5, "class": "cmap-dot"}))
            shapes.append(h("a", a, kids))
            if tab == "cities" and it.get("label") and it.get("bbox"):
                place_items.append(dict(label=it["label"], label_r=it["label_r"], bbox=it["bbox"], short=it["short"]))
            elif tab == "townships" and it.get("label"):
                texts.append(h("text", {"x": it["label"][0], "y": it["label"][1] + 3, "text-anchor": "middle",
                                        "class": "cmap-label cmap-label-township"},
                               it["name"].replace(" Township", "")))
            elif it["kind"] == "district" and it.get("label"):
                texts.append(h("text", {"x": it["label"][0], "y": it["label"][1] + 4, "text-anchor": "middle",
                                        "class": "cmap-label dmap-label" + (" dmap-label-sm" if it.get("label_r", 99) < 22
                                                                           else "")}, it["short"]))
        for pi, x, y, anchor in _label_boxes(place_items, vb[2]):
            texts.append(h("text", {"x": x, "y": y, "text-anchor": anchor, "class": "cmap-label cmap-label-place"},
                           pi["short"]))
        back = None
        if tab in ("cities", "city-council"):
            back = h("g", {"class": "nm-back", "aria-hidden": "true"},
                     [h("use", {"href": f"{asset}#{ASSET_ID}back-{bid}", "class": "cmap-s cmap-township cmap-back-s"})
                      for bid, _d in m["back"]])
        groups.append(h("g", {"class": "nm-layer" + (" is-on" if on else ""), "data-nm-layer": tab, "role": "group",
                              "aria-label": f"Layer: {L['label']}"},
                        back, h("g", {"clip-path": f"url(#{nm_id}-clip)", "class": "nm-shapes"}, shapes),
                        h("g", {"class": "dmap-over", "aria-hidden": "true"}, texts)))
        buttons[L["group"]].append(h("button", {"type": "button", "class": "cmap-tab nm-tab", "data-nm-layer": tab,
                                                "aria-pressed": "true" if on else "false"}, L["label"]))
    # areas with no shape on this map: the county, the levels, units with no boundary file (only those the page uses)
    drawn = {it["key"] for tab in shown_tabs for it in m["layers"][tab]["items"]}
    chips = []

    def chip(key, name, note=None):
        u = href(key)
        attrs = {"class": "nm-chip", "data-nm-key": key, "data-nm-name": name}
        if u:
            attrs["href"] = u
        else:
            attrs.update({"tabindex": "0", "role": "button"})
        chips.append(h("li", None, h("a", attrs, name), h("span", {"class": "nm-chip-note muted"}, note) if note else None))
    if unit_key("county") in used:
        chip(unit_key("county"), f"{ed.county_label} (every address)")
    for lv, name in LEVEL_NAMES.items():
        if level_key(lv) in used:
            chip(level_key(lv), name)
    others = []
    for key in sorted(used):
        kind, _, ident = key.partition(":")
        if kind == "g":
            from . import governments as gm
            g = gm.by_id(ed).get(ident)
            if g:
                others.append((g.name, key))
            continue
        if kind != "u" or key in drawn or ident in ("county",):
            continue
        u = ed.units.get(ident)
        if not u or u["unit_type"] in ("state", "state_chamber", "federal_chamber"):
            continue
        others.append((u["name"], key))
    for name, key in sorted(others, key=lambda x: _natural(x[0])):
        chip(key, name)
    for key, name in extra_chips or []:
        chip(key, name)
    if not shown_tabs and not chips:
        return None
    tabbar = h("div", {"class": "nm-bar", "role": "group", "aria-label": "Map layer", "hidden": True},
               [h("div", {"class": "nm-tabgroup", "role": "group", "aria-labelledby": f"{nm_id}-tg-{g}"},
                  h("span", {"class": "nm-tg-h", "id": f"{nm_id}-tg-{g}"}, GROUPS[g]),
                  h("span", {"class": "cmap-tabs nm-seg"}, btns))
                for g, btns in buttons.items() if btns]) if shown_tabs else None
    svg = h("svg", {"class": "nm-svg", "viewBox": " ".join(f"{v:g}" for v in vb), "role": "group",
                    "aria-label": f"Map of {ed.county_label}. Every area is a link; the same areas and every "
                                  f"{noun} are in the list on this page."},
            h("defs", None, h("clipPath", {"id": f"{nm_id}-clip"}, h("use", {"href": f"{asset}#{ASSET_ID}county"}))),
            groups,
            h("use", {"href": f"{asset}#{ASSET_ID}county", "class": "cmap-outline nm-outline", "aria-hidden": "true"})) \
        if shown_tabs else None
    side = h("div", {"class": "nm-side"},
             h("p", {"class": "nm-status", "id": f"{nm_id}-status", "role": "status", "aria-live": "polite"},
               what or (f"Choose a layer, then select an area to list only its {plural}. Select it again to open "
                        "its page." if shown_tabs else
                        f"Select an area to list only its {plural}. Select it again to open its page.")),
             h("p", {"class": "nm-peek muted", "aria-hidden": "true"}),
             h("p", {"class": "nm-actions", "hidden": True},
               h("a", {"class": "btn btn-small nm-open", "href": "#"}, open_label), " ",
               h("button", {"type": "button", "class": "btn btn-small nm-all"}, f"Show every {noun}")),
             h("div", {"class": "nm-others"},
               h("p", {"class": "nm-others-h"}, "Not on the map" if shown_tabs else "Areas"),
               h("ul", {"class": "nm-chips"}, chips)) if chips else None)
    body = h("div", {"class": "nm-grid" + ("" if shown_tabs else " nm-grid-nomap")},
             h("div", {"class": "nm-stage"}, svg,
               h("p", {"class": "nm-key muted"}, KEY_NOTE) if svg else None) if svg else None,
             side)
    root_attrs = {"class": "nm" + (" nm-folded" if folded else ""), "id": nm_id, "data-nm-target": target,
                  "data-nm-noun": noun, "data-nm-plural": plural}
    if default:
        root_attrs["data-nm-default"] = default
    if count_in:            # the status counts only the rows inside this element (one of the targets)
        root_attrs["data-nm-count"] = count_in
    inner = [tabbar, body]
    if folded:
        return h("div", root_attrs,
                 h("details", {"class": "nm-fold", "id": f"{nm_id}-fold"},
                   h("summary", {"class": "nm-fold-sum"}, h("span", {"class": "nm-fold-t"}, f"Show map: {title.lower()}"),
                     h("span", {"class": "fold-toggle", "aria-hidden": "true"})),
                   inner))
    return h("div", root_attrs, inner)
