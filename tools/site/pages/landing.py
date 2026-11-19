"""Home page (phase 6, 2026-11-18; planning/design-direction-2026-11-16.md section 0, "maps organize the home page").

Order, top to bottom:

1. What the guide is: the county counted from the data (governments, elected seats), one sentence, and a large search
   box that is a second copy of the header search (static/js/search.js binds both to the one search index).
2. "Your governments": with a saved place (localStorage "civic-place", static/js/here.js window.civicHere) a strip of
   the reader's governments that select them on the map; guide defaults never count as a choice. The place picker
   (civic/picker.py) sits in a fold under it (#pick, linked from Your place).
3. The county map as the way in. Layers: the county, cities and towns, townships, school corporations, county
   commissioner and council districts, city council districts, Indiana House and Senate districts. Built only from the
   boundary files (derived/map_shapes.json, derived/district_shapes.json) through the Offices hub's model
   (pages/offices.py hub_areas); the guide draws no boundary of its own. The .cmap contract of civic/map.py, so
   static/js/map.js gives the panel, hover, focus and the layer tabs; static/js/home.js makes a click (or Enter) select
   an area and open its links in the panel: its page and tabs, its offices with their holders (person pages through
   civic/people.py link_names), its elections and its money. A second click, or the panel's button, opens the page.
   With JavaScript off every area is a plain link to its government's or office's page.
4. Five doors (Governments, Offices, Elections, Money, Learn) with one line and example deep links each, the next
   election in the county, and the learning paths (#paths, the Learn menu's "Learning paths").
5. Every government and district as a plain list (#list): the no-JavaScript form of the map. It ships open and
   static/js/folds.js closes it when JavaScript runs.

Old ids of the earlier home page (the seat diagram, the counts, the context strip) forward through #moved-anchors to
where that content lives now (tools/tests/fixtures/anchors_before_home.json, tools/tests/test_phase6_home.py).
"""
from __future__ import annotations

import re
from collections import OrderedDict

from civic import election_pages as EP
from civic import governments as gm
from civic import offices as om
from civic import sitemap
from civic import tabs as T
from civic.components import name_with_party, term_party
from civic.html import Markup, h, join, json_script
from civic.layers import build_layers
from civic.picker import place_picker

# No place is preselected (a returning reader's saved place is restored by static/js/here.js).
# Kept for callers that still import it.
DEFAULT_PLACE = "south-bend"

# (layer id from pages/offices.py hub_areas, tab label, group). The default layer is the cities and towns.
# The county is not a layer (2026-11-18, owner: "Plain link above is fine"): one shape is no choice; it is the row above
# the map (_county_row).
HOME_LAYERS = [("cities", "Cities and towns", "gov"),
               ("townships", "Townships", "gov"), ("schools", "School corporations", "gov"),
               ("commissioners", "County commissioners", "district"), ("council", "County council", "district"),
               ("city-council", "City councils", "district"), ("house", "Indiana House", "district"),
               ("senate", "Indiana Senate", "district"),
               # 2026-11-18 (owner): the county map stays; choosing State or Federal shades the whole county and says
               # which view is shown (pages/offices.py level_item; the guide never draws Indiana or the U.S.)
               ("statewide", "Statewide", "level"), ("federal", "Federal", "level")]
LAYER_GROUPS = OrderedDict([("gov", "Governments"), ("district", "Election districts"), ("level", "State and federal")])
DEFAULT_LAYER = "cities"
DISTRICT_KIND = {"commissioners": "County commissioner district", "council": "County council district",
                 "city-council": "City council district", "house": "Indiana House district",
                 "senate": "Indiana Senate district"}
GOV_KIND = {"county": "County government", "city": "City", "town": "Town", "township": "Township",
            "school_corporation": "School corporation"}
HINT = ("Choose a layer, then point at or select an area. Its page, offices, elections and money open here. "
        "Select it again, or use the button, to go to its page.")
SEP = " · "

# ids of the earlier home page (before 2026-11-18) and where their content is now (site paths)
YOUR_PLACE = sitemap.YOUR_PLACE
LEARN_HUB = "learn/index.html"
MOVED = {"layers": YOUR_PLACE, "layers-h": YOUR_PLACE, "layers-showing": YOUR_PLACE, "layer-list": YOUR_PLACE,
"next-year": "elections/index.html#next", "next-dates": "elections/index.html#next",
         "next-offices": "elections/index.html#next", "ctx-h": "community/index.html",
         # the learning paths are on the Learn hub (learn/index.html#paths, phase 6 Learn step)
         "paths": f"{LEARN_HUB}#paths", "paths-h": f"{LEARN_HUB}#paths"}
MOVED_PREFIXES = {"layer-": YOUR_PLACE, "src-": "about/sources/index.html"}


# =========================================================================== kept for other modules
# The earlier home page's seat diagram helpers. The home page no longer draws the diagram, but Your place
# (pages/participate.py) and civic/picker.py import these; they are unchanged.

def _unknown_split(ed, L) -> tuple[int, int]:
    """(elected, appointed) counts of seat-count-unknown markers in a layer. The headline's
    'at least' qualifies elected seats, so an appointed board with no seat count must not trigger it."""
    appointed_titles = {b["name"] for b in ed.boards} | {o["title"] for o in ed.tables["offices"] if o.get("elected") == "no"}
    el = ap = 0
    for g in L.groups:
        u = g.kinds.count("unknown")
        if not u:
            continue
        if g.titles and all(t in appointed_titles for t in g.titles):
            ap += u
        else:
            el += u
    return el, ap


def _layer_row(page, L, visible: bool) -> Markup:
    from civic.charts import seat_dots
    from civic.components import APPOINTED_NOTE, bodies_block
    groups = []
    for g in L.groups:
        if not g.kinds:
            continue
        tip = f"{g.label}: {g.summary()}"
        notes = [n for n in g.notes if n]
        groups.append(h("div", {"class": "seat-group", "tabindex": "0", "data-tv": g.summary(), "data-tl": g.label
                                + (f" · {notes[0]}" if notes else "")},
                        seat_dots(g.kinds, tip),
                        h("span", {"class": "seat-group-label"}, g.label)))
    layer_sources = [x for g in L.groups for x in g.sources]
    counts = []
    if L.elected:
        counts.append(f"{L.elected} elected")
    if L.vote:
        counts.append(f"you vote for {L.vote}")
    if L.appointed:
        counts.append(f"{L.appointed} appointed")
    if L.unknown:
        counts.append("some seat counts not in data")
    summary = " · ".join(counts) if counts else "no seats in the guide's data yet"
    rid = L.layer_id.replace(":", "-")
    unk_el, unk_ap = _unknown_split(page.cites.ed, L)
    bodies = bodies_block(page.cites.ed, L.offices, note=False) if L.offices else None
    appointed_line = h("p", {"class": "party-asof muted"}, APPOINTED_NOTE) if L.appointed and not L.placeholder else None
    return h("div", {"class": "layer" + (" layer-placeholder" if L.placeholder else ""), "id": f"layer-{rid}",
                     "data-layer": L.layer_id, "data-key": L.key, "data-elected": L.elected, "data-vote": L.vote,
                     "data-appointed": L.appointed, "data-unknown": unk_el, "data-unknown-appointed": unk_ap, "data-gov": 1 if L.government else 0,
                     "data-next": _next_attr(L), "hidden": None if visible else True},
             h("div", {"class": "layer-head"},
               h("span", {"class": "layer-name"}, h("span", {"class": "layer-title"}, L.title), page.cites.cite_compact(layer_sources) if layer_sources else None),
               h("span", {"class": "layer-leader", "aria-hidden": "true"}),
               h("span", {"class": "layer-count mono"}, summary),
               h("button", {"type": "button", "class": "layer-toggle btn btn-small", "aria-expanded": "false",
                            "aria-controls": f"seats-{rid}", "id": f"toggle-{rid}"}, "Show seats")),
             h("div", {"class": "layer-seats", "id": f"seats-{rid}"}, groups, bodies, appointed_line,
               h("p", {"class": "layer-note"}, L.note) if L.note else None))


def _next_attr(L) -> str:
    import json
    return json.dumps(L.next, separators=(",", ":"))


# =========================================================================== small helpers

def _holders(ed, oid: str):
    cur = ed.current_terms(oid)
    if not cur:
        return h("span", {"class": "muted"}, "holder not in the guide's data")
    return join([name_with_party(t["person"], term_party(t), t.get("confidence") if term_party(t) else None)
                 for t in cur], ", ")


def _districted(o) -> bool:
    d = (o.get("district") or "").strip().lower()
    return bool(d) and d != "at-large"


def _links(items) -> Markup | None:
    """[(label, href or None)] -> the built ones joined with middle dots."""
    got = [h("a", {"href": u}, label) for label, u in items if u]
    return join(got, SEP) if got else None


def _gov_tab_links(page, gid: str, skip=("overview", "sources")) -> list:
    return [(T.TAB_LABELS[k], gm.href(page, gid, k)) for k in gm.gov_tabs(page.ed, gid) if k not in skip]


def _office_tab_links(page, oid: str) -> list:
    return [(T.TAB_LABELS[k], om.href(page, oid, k)) for k in om.office_tabs(page.ed, oid) if k != "sources"]


def _next_years(offices) -> str:
    ys = sorted({o["next_election"] for o in offices if o.get("next_election")})
    return ", ".join(ys)


def _last_election(page, oid: str):
    """The office's most recent contest's election page: ('2024 general election', href) or None."""
    for c in om.contests(page.ed, oid):
        u = EP.href(page, c["election_id"])
        if u:
            return EP.title(page.ed.elections[c["election_id"]]), u
    return None


# =========================================================================== the map

def _area_offices(ed, item) -> list[dict]:
    """The offices one map area's voters elect: a district its one office; the county its countywide offices
    (districted county seats are on the district layers; the courts are one line); a government all its offices."""
    if item["kind"] == "district":
        return [ed.offices[item["office"]]]
    if item["kind"] == "level":
        return [ed.offices[oid] for oid in item["offices"]]
    if item["unit"] == "county":
        return [o for o in ed.tables["offices"] if o["unit_id"] == "county" and not _districted(o)]
    return [o for o in ed.tables["offices"] if o["unit_id"] == item["unit"]]


def _layer_button(tab: str, label: str) -> Markup:
    """Inside a panel block (shown only with JavaScript): switches the map to another layer (home.js)."""
    return h("button", {"type": "button", "class": "btn btn-small hm-layer-btn", "data-hm-layer": tab}, label)


def _gov_block(page, item, offices, drawn, labels) -> Markup:
    ed = page.ed
    uid = item["unit"]
    g = gm.gov_for_unit(ed, uid)
    parts = []
    tabs_ = _links(_gov_tab_links(page, g.gid, skip=("sources",))) if g else None
    if tabs_:
        parts.append(h("p", {"class": "hm-row hm-tabs"}, h("span", {"class": "hm-k"}, "Its page"), " ", tabs_))
    rows = []
    for o in offices:
        oid = o["office_id"]
        title = om.short_title(ed, o) if uid != "county" else o["title"]
        link = om.href(page, oid)
        rows.append(h("li", {"class": "hm-office"},
                      h("a", {"href": link}, title) if link else h("span", None, title),
                      h("span", {"class": "hm-who"}, " ", _holders(ed, oid))))
    if rows:
        parts.append(h("p", {"class": "hm-k hm-sub"}, f"{len(offices)} office{'s' if len(offices) != 1 else ''} "
                                                    "elected here"))
        parts.append(h("ul", {"class": "hm-offices"}, rows))
    else:
        parts.append(h("p", {"class": "hm-row muted"}, "No elected office in the guide's list for this area."))
    if uid == "county":
        courts = [o for o in ed.tables["offices"] if o["unit_id"] == "sjc-courts"]
        if courts:
            seats = sum(int(o["seats"]) if (o.get("seats") or "").isdigit() else 1 for o in courts)
            u = gm.href(page, "county", "overview", "courts")
            parts.append(h("p", {"class": "hm-row"}, f"Courts: {seats} judgeships, elected or retained countywide. ",
                           h("a", {"href": u}, "The courts") if u else None))
        parts.append(h("p", {"class": "hm-row hm-note"}, "Commissioners and council members are elected by district: ",
                       _layer_button("commissioners", labels["commissioners"]), " ",
                       _layer_button("council", labels["council"])))
    else:
        other = sorted({drawn[o["office_id"]] for o in offices if _districted(o) and o["office_id"] in drawn})
        if other:
            parts.append(h("p", {"class": "hm-row hm-note"}, "District seats on the map: ",
                           join([_layer_button(t, labels[t]) for t in other], " ")))
        nod = [o for o in offices if _districted(o) and o["office_id"] not in drawn]
        if nod:
            parts.append(h("p", {"class": "hm-row hm-note muted"},
                           f"{len(nod)} seat{'s are' if len(nod) != 1 else ' is'} elected by district, ward or township "
                           "with no official boundary file in the guide, so not drawn."))
    nxt = _next_years(offices)
    if nxt:
        parts.append(h("p", {"class": "hm-row hm-next"}, h("span", {"class": "hm-k"}, "Next election"), " ", nxt))
    return h("div", {"class": "hm-block", "data-hm-uid": item["uid"]}, parts)


def _district_block(page, item) -> Markup:
    ed = page.ed
    oid = item["office"]
    o = ed.offices[oid]
    parts = [h("p", {"class": "hm-row hm-holder"}, h("span", {"class": "hm-k"}, "Held by"), " ", _holders(ed, oid))]
    tabs_ = _links(_office_tab_links(page, oid))
    if tabs_:
        parts.append(h("p", {"class": "hm-row hm-tabs"}, h("span", {"class": "hm-k"}, "Office page"), " ", tabs_))
    last = _last_election(page, oid)
    if last:
        parts.append(h("p", {"class": "hm-row"}, h("span", {"class": "hm-k"}, "Last on the ballot"), " ",
                       h("a", {"href": last[1]}, last[0])))
    if o.get("next_election"):
        parts.append(h("p", {"class": "hm-row hm-next"}, h("span", {"class": "hm-k"}, "Next election"), " ",
                       o["next_election"]))
    gov = om.government_page(ed, o["unit_id"])
    if gov and gov[0].split("#")[0] in page.site.by_path:
        parts.append(h("p", {"class": "hm-row"}, h("span", {"class": "hm-k"}, "Part of"), " ",
                       h("a", {"href": page.rel(gov[0])}, gov[1])))
    return h("div", {"class": "hm-block", "data-hm-uid": item["uid"]}, parts)


def _level_block(page, item, offices) -> Markup:
    """The panel of a State or Federal layer: what the level covers in the county (the same words as the label under
    the map), then each office with its holder and a link to its page."""
    ed = page.ed
    rows = []
    for o in offices:
        link = om.href(page, o["office_id"])
        rows.append(h("li", {"class": "hm-office"},
                      h("a", {"href": link}, o["title"]) if link else h("span", None, o["title"]),
                      h("span", {"class": "hm-who"}, " ", _holders(ed, o["office_id"]))))
    parts = [h("p", {"class": "hm-row hm-level-note"}, item["note"]) if item.get("note") else None,
             h("p", {"class": "hm-k hm-sub"}, f"{len(offices)} office{'s' if len(offices) != 1 else ''}"),
             h("ul", {"class": "hm-offices"}, rows)]
    nxt = _next_years(offices)
    if nxt:
        parts.append(h("p", {"class": "hm-row hm-next"}, h("span", {"class": "hm-k"}, "Next election"), " ", nxt))
    return h("div", {"class": "hm-block", "data-hm-uid": item["uid"]}, parts)


def _county_row(page) -> Markup | None:
    """The county government above the map: it covers every address, so it is a plain row of links, not a map layer.
    Its page and tabs, its countywide offices (the Offices hub's county group) and the courts."""
    ed = page.ed
    g = gm.gov_for_unit(ed, "county")
    if not g:
        return None
    countywide = [o for o in ed.tables["offices"] if o["unit_id"] == "county" and not _districted(o)]
    links = [(T.TAB_LABELS[k], gm.href(page, g.gid, k)) for k in gm.gov_tabs(ed, g.gid) if k not in ("overview", "sources")]
    hub = om.HUB + "#county"
    if om.HUB in page.site.by_path and countywide:
        links.append((f"{len(countywide)} countywide offices", page.rel(hub)))
    links.append(("The courts", gm.href(page, g.gid, "overview", "courts")))
    return h("p", {"class": "hm-county-row", "id": "county-row"},
             h("span", {"class": "hm-k"}, "Every address"), " ",
             h("a", {"class": "hm-county-name", "href": gm.href(page, g.gid)}, f"{g.name} government"), " ",
             h("span", {"class": "hm-county-links"}, _links(links)),
             h("span", {"class": "hm-county-note muted"},
               " Commissioners and council members are elected by district: see those layers on the map."))


def _natural(text: str):
    """Sort key: words, with numbers compared as numbers (District 2 before District 10)."""
    return [(0, int(t), "") if t.isdigit() else (1, 0, t.lower()) for t in re.findall(r"\d+|\D+", text)]


def _start_panel(start: dict, labels: dict) -> Markup:
    """What the panel shows before an area is chosen: how to use the map, then the shown layer's areas as a list in
    alphabetical (natural) order, each linking to its page, so the panel is a way in too. One list per layer; the
    default layer's ships shown, home.js shows the current layer's. map.js keeps this whole block (the panel's first
    element) and puts it back whenever no area is chosen. No area is preselected: every one gets the same treatment."""
    lists = []
    for tab, items in start.items():
        rows = [h("li", None, h("a", {"href": href, "data-hm-pick": uid}, name))
                for name, href, uid in sorted(items, key=lambda x: _natural(x[0]))]
        lists.append(h("div", {"class": "hm-start-list" + (" is-on" if tab == DEFAULT_LAYER else ""),
                               "data-hm-list": tab},
                       h("p", {"class": "hm-k hm-start-h"}, f"{labels[tab]} on the map ({len(items)})"),
                       h("ul", {"class": "hm-start-ul"}, rows)))
    return h("div", {"class": "cmap-hint hm-start"}, h("p", {"class": "hm-start-hint"}, HINT), lists)


def home_map(page, ed, shapes, model) -> Markup | None:
    """The home map (see the module docstring). Returns None when the edition has no boundary file."""
    from civic.campaign_map import SET_NOTES
    from civic.district_map import neighbor_fills
    from civic.map import _kind_class, _label_boxes
    if not shapes or not model["layers"]:
        return None
    vb = shapes["viewBox"]
    labels = {t: lab for t, lab, _g in HOME_LAYERS}
    group_of = {t: g for t, _l, g in HOME_LAYERS}
    by_tab = {L["tab"]: L for L in model["layers"]}
    county_back = [h("path", {"d": t["d"], "class": "cmap-s cmap-township cmap-back-s"})
                   for t in shapes["layers"].get("township", [])]
    data, groups, blocks = {}, [], []
    set_notes: dict = {}     # layer -> the district sets' notes, shown under the map while that layer is on
    start: dict = OrderedDict()   # layer -> [(short name, href, uid)]: the panel's list before an area is chosen
    tab_buttons: dict = OrderedDict((g, []) for g in LAYER_GROUPS)
    for tab, label, _grp in HOME_LAYERS:
        L = by_tab.get(tab)
        if not L or not L["items"]:
            continue
        on = tab == DEFAULT_LAYER
        fills = neighbor_fills([{"district": it["uid"], "d": it["d"]} for it in L["items"]]) \
            if L["items"][0]["kind"] == "district" else {}
        paths, texts, place_items = [], [], []
        for it in L["items"]:
            offs = _area_offices(ed, it)
            if it["kind"] == "level":
                from pages.offices import LEVEL_LAYERS, level_label
                name = LEVEL_LAYERS[it["level"]][0]
                href = om.href(page, offs[0]["office_id"]) if len(offs) == 1 else (page.rel(om.HUB) + "#"
                                                                                   + om.LEVEL_IDS[it["level"]])
                cls = "cmap-s cmap-level"
                typ = f"{LEVEL_LAYERS[it['level']][1]} level: the whole county"
                entry = {"n": name, "t": typ, "f": [], "cav": [], "note": "", "href": href,
                         "open": "Open these offices on the Offices page", "l": tab}
                aria = f"{name}: {len(offs)} office{'s' if len(offs) != 1 else ''}. Show its links."
                texts.append(level_label(it))
                blocks.append(_level_block(page, it, offs))
                if it.get("note"):
                    set_notes.setdefault(tab, [])
                    if it["note"] not in set_notes[tab]:
                        set_notes[tab].append(it["note"])
            elif it["kind"] == "gov":
                u = ed.units[it["unit"]]
                name = u["name"]
                href = gm.unit_href(page, it["unit"]) or "#list"
                cls = ("cmap-s cmap-township hm-county" if it["unit"] == "county"
                       else f"cmap-s {_kind_class(u, it.get('n', 0))}")
                typ = GOV_KIND.get(u["unit_type"], u["unit_type"])
                short = re.sub(r"^(City|Town) of ", "", name)
                entry = {"n": name, "t": typ, "f": [], "cav": [], "note": "", "href": href,
                         "open": f"Open the {short} page" if it["unit"] != "county" else "Open the county's page",
                         "l": tab}
                if it.get("share_inside") is not None and it["share_inside"] < 0.97:
                    entry["cav"].append(f"Partly outside the county: about {round(it['share_inside'] * 100)}% of "
                                        "its land area is inside the county (computed from Census boundaries).")
                aria = f"{name}, {typ.lower()}: {len(offs)} office{'s' if len(offs) != 1 else ''}. Show its links."
                if tab == "cities" and it.get("label") and it.get("bbox"):
                    place_items.append(dict(label=it["label"], label_r=it["label_r"], bbox=it["bbox"], short=short))
                if tab == "townships" and it.get("label"):
                    texts.append(h("text", {"x": it["label"][0], "y": it["label"][1] + 3, "text-anchor": "middle",
                                            "class": "cmap-label cmap-label-township"}, name.replace(" Township", "")))
                blocks.append(_gov_block(page, it, offs, model["drawn"], labels))
            else:
                o = ed.offices[it["office"]]
                name = o["title"]
                href = om.href(page, it["office"]) or "#list"
                cls = f"cmap-s dmap-s dmap-f{fills.get(it['uid'], 0)}"
                typ = DISTRICT_KIND[tab]
                entry = {"n": name, "t": typ, "f": [], "cav": [], "note": "", "href": href,
                         "open": "Open the office page", "l": tab}
                aria = f"{name}. Show its links."
                if it.get("label"):
                    texts.append(h("text", {"x": it["label"][0], "y": it["label"][1] + 4, "text-anchor": "middle",
                                            "class": "cmap-label dmap-label" + (" dmap-label-sm" if it["label_r"] < 22
                                                                               else "")}, it["text"]))
                blocks.append(_district_block(page, it))
                if SET_NOTES.get(it["set"]):
                    set_notes.setdefault(tab, [])
                    if SET_NOTES[it["set"]] not in set_notes[tab]:
                        set_notes[tab].append(SET_NOTES[it["set"]])
            data[it["uid"]] = entry
            start.setdefault(tab, []).append((re.sub(r"^(City|Town) of ", "", name), href, it["uid"]))
            kids = [h("path", {"d": it["d"], "class": cls})]
            if tab == "cities" and it.get("label_r", 99) < 6 and it.get("label"):
                kids.append(h("circle", {"cx": it["label"][0], "cy": it["label"][1], "r": 5, "class": "cmap-dot"}))
            paths.append(h("a", {"href": href, "class": "cmap-a", "data-uid": it["uid"], "aria-label": aria}, kids))
        for pi, x, y, anchor in _label_boxes(place_items, vb[2]):
            texts.append(h("text", {"x": x, "y": y, "text-anchor": anchor, "class": "cmap-label cmap-label-place"},
                           pi["short"]))
        back = h("g", {"class": "cmap-back", "aria-hidden": "true"}, county_back) \
            if tab in ("cities", "city-council") else None
        groups.append(h("g", {"class": "cmap-layer" + (" is-on" if on else ""), "data-layer": tab, "role": "group",
                              "aria-label": f"Layer: {label}"},
                        back, h("g", {"clip-path": "url(#cmap-clip)"}, paths),
                        h("g", {"class": "dmap-over", "aria-hidden": "true"}, texts)))
        tab_buttons[group_of[tab]].append(h("button", {"type": "button", "class": "cmap-tab", "data-layer": tab,
                                                       "aria-pressed": "true" if on else "false"}, label))
    tabbar = h("div", {"class": "cmap-tabs hm-tabs-bar", "role": "group", "aria-label": "Map layer", "hidden": True},
               [h("div", {"class": "hm-tabgroup", "role": "group", "aria-labelledby": f"hm-tg-{g}"},
                  h("span", {"class": "hm-tg-h", "id": f"hm-tg-{g}"}, LAYER_GROUPS[g]),
                  h("span", {"class": "hm-seg"}, btns))
                for g, btns in tab_buttons.items() if btns])
    svg = h("svg", {"class": "cmap-svg", "viewBox": f"{vb[0]} {vb[1]} {vb[2]} {vb[3]}", "role": "group",
                    "aria-label": f"Map of {ed.county_label}: its governments and election districts. Every area is "
                                  "a link; the same governments and districts are listed after the map."},
            h("defs", None, h("clipPath", {"id": "cmap-clip"}, h("path", {"d": shapes["county"]["d"]}))),
            groups,
            h("path", {"d": shapes["county"]["d"], "class": "cmap-outline", "aria-hidden": "true"}),
            h("g", {"class": "cmap-hl-g", "aria-hidden": "true", "clip-path": "url(#cmap-clip)"}))
    panel = h("aside", {"class": "cmap-panel hm-panel", "id": "cmap-panel", "aria-live": "polite",
                        "aria-label": "The selected area's links"}, _start_panel(start, labels))
    return h("div", {"class": "cmap dmap hm", "id": "home-map", "data-default-layer": DEFAULT_LAYER, "data-hash": "off"},
             h("div", {"class": "cmap-bar"}, tabbar),
             h("div", {"class": "cmap-grid"},
               h("div", {"class": "cmap-stage"}, svg,
                 h("p", {"class": "dmap-key muted hm-key"},
                   "Fills only tell kinds of government or neighboring districts apart; they never show party or an "
                   "amount. Boundaries are the official files the guide lists; it draws none of its own.",
                   page.cites.cite_compact(";".join(["MAP-001;MAP-002;MAP-003;MAP-004"] + model["sources"]))),
                 [h("p", {"class": "hm-layer-note muted" + (" is-on" if t == DEFAULT_LAYER else "")
                         + (" hm-layer-note-level" if group_of.get(t) == "level" else ""), "data-layer": t},
                    " ".join(notes)) for t, notes in set_notes.items()]),
               h("div", {"class": "dmap-side"}, panel)),
             h("div", {"id": "layer-data", "class": "hm-blocks", "hidden": True}, blocks),
             json_script("cmap-data", data))


# =========================================================================== the plain list (no JavaScript)

def _gov_list(page, model) -> Markup:
    ed = page.ed
    gs = gm.governments(ed)
    groups = []
    for gid_, label in gm.GROUPS.items():
        rows = []
        for g in [x for x in gs if x.group == gid_]:
            tabs_ = _links(_gov_tab_links(page, g.gid))
            rows.append(h("li", {"class": "hl-row"},
                          h("a", {"class": "hl-name", "href": gm.href(page, g.gid)}, g.name),
                          h("span", {"class": "hl-tabs"}, " ", tabs_) if tabs_ else None))
        if rows:
            groups.append(h("div", {"class": "hl-group"}, h("h3", {"class": "hl-h"}, label),
                            h("ul", {"class": "hl-list"}, rows)))
    labels = {t: lab for t, lab, _g in HOME_LAYERS}
    for L in model["layers"]:
        items = [it for it in L["items"] if it["kind"] == "district"]
        if not items:
            continue
        links = []
        for it in items:
            u = om.href(page, it["office"])
            o = ed.offices[it["office"]]
            links.append(h("li", None, h("a", {"href": u}, o["title"]) if u else o["title"]))
        groups.append(h("div", {"class": "hl-group hl-districts"}, h("h3", {"class": "hl-h"}, labels[L["tab"]]),
                        h("ul", {"class": "hl-list hl-inline"}, links)))
    return h("details", {"class": "home-list", "id": "list", "data-fold": "home-list", "open": True},
             h("summary", {"class": "home-list-sum"},
               h("span", {"class": "home-list-title"}, "Every government and district, as a list"),
               h("span", {"class": "muted"}, " {n} {noun}, each with its page".format(**gm.count(ed)))),
             h("div", {"class": "hl-cols"}, groups))


# =========================================================================== doors

def _door_examples(page) -> dict:
    """Two or three deep links per door, chosen from the data (each only when its page is built)."""
    ed = page.ed
    by_path = page.site.by_path
    out: dict = {k: [] for k in ("governments", "offices", "elections", "money", "learn")}
    gs = gm.governments(ed)

    def first(kind):
        return next((g for g in gs if g.kind == kind), None)
    city, twp, school = first("city"), first("township"), first("school_corporation")
    if city:
        out["governments"].append((f"{city.name} › Money", gm.href(page, city.gid, "money")))
    if twp:
        out["governments"].append((twp.name, gm.href(page, twp.gid)))
    if school:
        out["governments"].append((f"{school.name} › Elections", gm.href(page, school.gid, "elections")))
    offs = ed.tables["offices"]
    mayor = next((o for o in offs if o["office_type"] == "mayor"), None)
    sheriff = next((o for o in offs if o["office_type"] in ("sheriff", "county_sheriff")), None) or \
        next((o for o in offs if "Sheriff" in o["title"]), None)
    if mayor:
        out["offices"].append((f"{mayor['title']} › Money", om.href(page, mayor["office_id"], "money")))
    if sheriff:
        out["offices"].append((f"{sheriff['title']} › Elections", om.href(page, sheriff["office_id"], "elections")))
    if "people/index.html" in by_path:
        out["offices"].append(("People: officeholders and candidates", page.rel("people/index.html")))
    els = [e for e in EP.ordered(ed, newest_first=True) if EP.href(page, e["election_id"])]
    gen = next((e for e in els if e["type"] == "general"), None)
    prim = next((e for e in els if e["type"] in EP.PRIMARY_TYPES), None)
    for e in (gen, prim):
        if e:
            out["elections"].append((EP.title(e)[:1].upper() + EP.title(e)[1:], EP.href(page, e["election_id"])))
    if EP.COMPARE_PATH["margins"] in by_path:
        out["elections"].append(("Close races", page.rel(EP.COMPARE_PATH["margins"])))
    for p, t in (("money/budgets/index.html", "Budgets compared"), ("money/your-tax-bill/index.html", "Your tax bill"),
                 ("money/campaigns/index.html", "Campaign money")):
        if p in by_path:
            out["money"].append((t, page.rel(p)))
    for p, t in ((f"{LEARN_HUB}#paths", "Learning paths: short guided tours"),
                 ("elections/how-it-works/index.html", "How elections work"),
                 ("who-handles-this/index.html", "Who handles this?")):
        if p.split("#")[0] in by_path:
            out["learn"].append((t, page.rel(p)))
    return {k: [(t, u) for t, u in v if u][:3] for k, v in out.items()}


DOORS = [("governments", "Governments", "governments/index.html",
          "The county, cities, towns, townships and school corporations, each with its own page."),
         ("offices", "Offices", "offices/index.html",
          "Every elected office: who holds it, every election and the campaign money on record."),
         ("elections", "Elections", "elections/index.html",
          "Every election in the guide, each with its results, and the next one on the calendar."),
         ("money", "Money", "money/index.html",
          "Budgets, tax bills and debt, and the money raised and spent by campaigns."),
         ("learn", "Learn", "learn/index.html",
          "Plain guides to how local government, elections and budgets work.")]


def _doors(page) -> Markup:
    ex = _door_examples(page)
    cards = []
    for key, label, hub, line in DOORS:
        if key == "learn" and hub not in page.site.by_path:
            hub = "teach/index.html"           # an edition without the Learn hub: the lesson kits
        if hub not in page.site.by_path:
            continue
        cards.append(h("li", {"class": "door", "id": f"door-{key}"},
                       h("h3", {"class": "door-h"}, h("a", {"href": page.rel(hub)}, label)),
                       h("p", {"class": "door-line"}, line),
                       h("ul", {"class": "door-ex"}, [h("li", None, h("a", {"href": u}, t)) for t, u in ex[key]])
                       if ex[key] else None))
    return h("section", {"class": "home-sec", "id": "doors", "aria-labelledby": "doors-h"},
             h("h2", {"class": "home-sec-h", "id": "doors-h"}, "Or start from a kind of record"),
             h("ul", {"class": "doors"}, cards))


def _next_ballot(page) -> Markup | None:
    from .elections import _hub_next
    ny, lines = _hub_next(page, page.ed)
    if not lines:
        return None
    return h("section", {"class": "home-next", "id": "next-ballot", "aria-labelledby": "next-h"},
             h("h2", {"class": "home-sec-h", "id": "next-h"}, "Next on the ballot"),
             lines[0], lines[1],
             h("p", {"class": "home-next-link"},
               h("a", {"href": page.rel("elections/index.html#next")}, "What is on that ballot"), SEP,
               h("a", {"href": page.rel("elections/calendar/index.html")}, "Election calendar")))


def _paths(page) -> Markup:
    items = []
    for i, p in enumerate(sitemap.PATHS, 1):
        first = p["stops"][0]
        items.append(h("li", {"class": "hp-item"},
                       h("a", {"href": page.rel(first["page"]) + f"#path-{p['id']}-1"},
                         h("span", {"class": "hp-num mono"}, f"{i:02d}"), " ",
                         h("span", {"class": "hp-title"}, p["title"])),
                       h("span", {"class": "hp-meta muted"},
                         f" {p['blurb']} {len(p['stops'])} stops, about {p['minutes']} min.")))
    return h("section", {"class": "home-sec", "id": "paths", "aria-labelledby": "paths-h"},
             h("h2", {"class": "home-sec-h", "id": "paths-h"}, "Learning paths"),
             h("p", {"class": "home-lead muted"}, "Short guided tours, a few pages each. Teaching or leading a group? ",
               h("a", {"href": page.rel("teach/index.html")}, "Lesson kits"), "."),
             h("ol", {"class": "home-paths"}, items))


# =========================================================================== the page

def _search_box(page) -> Markup:
    """A second copy of the header search (same index, same script: static/js/search.js binds both)."""
    return h("div", {"class": "home-search", "id": "home-search"},
             h("p", {"class": "search-nojs muted"}, "Search needs JavaScript. Every page is in ",
               h("a", {"href": "#browse"}, "Browse everything"), " at the foot of the page, and every government in ",
               h("a", {"href": "#list"}, "the list below the map"), "."),
             h("form", {"class": "search-form home-search-form", "id": "home-search-form", "role": "search",
                        "aria-label": "Search the guide (home)", "hidden": True,
                        "data-index": page.rel("assets/search-index.json")},
               h("label", {"class": "home-search-label", "for": "home-search-input"}, "Search the guide"),
               h("span", {"class": "home-search-field"},
                 h("span", {"class": "search-icon", "aria-hidden": "true"}),
                 h("input", {"type": "text", "id": "home-search-input", "name": "q", "class": "search-input",
                             "placeholder": "An office, a place, a person, or “mayor money”", "autocomplete": "off",
                             "spellcheck": "false", "role": "combobox", "aria-expanded": "false",
                             "aria-controls": "home-search-list", "aria-autocomplete": "list",
                             "aria-describedby": "home-search-help"}),
                 h("span", {"class": "visually-hidden", "id": "home-search-help"},
                   "Type two or more letters. Up and down arrows move through the results, Enter opens one, "
                   "Escape closes the list."),
                 h("div", {"class": "search-pop", "id": "home-search-pop", "hidden": True},
                   h("p", {"class": "search-status", "id": "home-search-status", "role": "status",
                           "aria-live": "polite"}),
                   h("ul", {"class": "search-list", "id": "home-search-list", "role": "listbox",
                            "aria-label": "Search results"}),
                   h("p", {"class": "search-foot"}, h("a", {"href": "#browse"}, "Browse everything"))))))


def _counts(ed) -> dict:
    # "elected seats" counts local seats only: the state legislature is counted apart, and statewide and federal
    # offices (units of type state / federal_chamber, 2026-11-18) are not counted (civic/offices.py NON_LOCAL_UNIT_TYPES)
    state_units = {u["unit_id"] for u in ed.tables["units"] if u["unit_type"] == "state_chamber"}
    non_local = {u["unit_id"] for u in ed.tables["units"] if u["unit_type"] in om.NON_LOCAL_UNIT_TYPES}
    elected = [o for o in ed.tables["offices"] if o.get("elected") == "yes"]
    elections = ed.elections
    broad = sorted(e[:4] for e in elections
                   if sum(1 for c in ed.contests.values() if c["election_id"] == e) >= 10)
    # the governments count is civic/governments.py count(): the same number the home list and the Governments hub show
    return {"gov": gm.count(ed),
            "seats": sum(int(o.get("seats") or 1) for o in elected if o["unit_id"] not in non_local),
            "state": sum(int(o.get("seats") or 1) for o in elected if o["unit_id"] in state_units),
            "first_all": broad[0] if broad else None,
            "first_any": min(e[:4] for e in elections) if elections else None}


def _intro(page) -> Markup:
    ed = page.ed
    n = _counts(ed)
    since = (f"Election results from {n['first_all']} on"
             + (f" (South Bend mayor back to {n['first_any']})"
                if n["first_any"] and n["first_all"] and n["first_any"] < n["first_all"] else "")
             if n["first_all"] else "Election results")
    return h("section", {"class": "home-intro", "aria-labelledby": "hero-h"},
             h("h1", {"id": "hero-h", "class": "home-h1"},
               h("span", {"class": "hl-line"}, "One county."), " ",
               h("span", {"class": "hl-line"}, f"{n['gov']['n']} {n['gov']['noun']}."), " ",
               h("span", {"class": "hl-line"}, f"{n['seats']} elected local seats.")),
             h("p", {"class": "home-dek"},
               f"Who holds every seat now, {since[0].lower() + since[1:]}, and the money behind them: one sourced, "
               f"nonpartisan reference for {ed.county_label}'s governments. Voters here also help elect "
               f"{n['state']} state legislators. ",
               T.status_mark("computed", page, "Counted from the guide's units and offices tables.")),
             h("p", {"class": "home-count"}, f"Counted: {n['gov']['parts']}, each with its own page in the guide."),
             _search_box(page))


def _mine(page, data) -> Markup:
    """"Your governments": filled by static/js/home.js from the saved place; the picker in a fold (#pick)."""
    return h("section", {"class": "home-mine", "id": "your-govs", "aria-label": "Your governments"},
             h("p", {"class": "home-mine-line", "id": "home-mine"},
               h("span", {"class": "home-mine-k"}, "Your place"), " ",
               h("span", {"id": "home-mine-text"},
                 "Choose your city, town or township once, and the map opens on your governments."),
               h("a", {"class": "home-mine-yp", "href": page.rel(YOUR_PLACE)}, "Your place: what each government does")
               if YOUR_PLACE in page.site.by_path else None),
             h("details", {"class": "home-pick", "id": "pick"},
               h("summary", {"class": "home-pick-sum"}, h("span", {"id": "pick-h"}, "Choose your place")),
               place_picker(page, data)))


def build(site):
    from civic.district_map import load_district_shapes
    from civic.map import load_shapes
    from .elections import moved_anchors
    from .offices import hub_areas
    ed = site.ed
    page = site.page("index.html", banners=True, body_class="is-home")
    data = build_layers(ed)
    shapes = load_shapes(ed)
    model = hub_areas(ed, shapes, load_district_shapes(ed, shapes)) if shapes else {"layers": [], "drawn": {},
                                                                                    "sources": []}
    page.add(_intro(page), _mine(page, data))
    m = home_map(page, ed, shapes, model)
    if m is not None:
        page.add(h("section", {"class": "home-sec home-map-sec", "id": "map", "aria-labelledby": "map-h"},
                   h("h2", {"class": "home-sec-h", "id": "map-h"}, "Start on the map"),
                   _county_row(page), m))
    page.add(_doors(page), _next_ballot(page))
    if LEARN_HUB not in site.by_path:      # an edition without the Learn hub keeps the paths here (#paths)
        page.add(_paths(page))
    page.add(_gov_list(page, model))
    # the earlier home page's ids (seat diagram, counts, context strip): forwarded to where that content is now
    layer_ids = {}
    for L in data["layers"].values():
        rid = L.layer_id.replace(":", "-")
        for pre in ("seats-", "toggle-"):
            layer_ids[f"{pre}{rid}"] = f"{YOUR_PLACE}#layer-{rid}"
    page.add(moved_anchors(page, {**MOVED, **layer_ids}, prefixes=MOVED_PREFIXES))
    page.finish()
    return page
