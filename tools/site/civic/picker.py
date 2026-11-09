"""Place picker + layer rows, shared by the landing page and the Find-your-governments page,
and the small place-names payload every page carries for the "You are here" bar.

The picker is a set of visible choice lists (looks.css styles `.choice-list` / `.choice`):

* Without JavaScript every choice is a plain link to that place's own page (cities and towns,
  townships, school corporations), so nothing depends on a script.
* static/js/here.js turns each link into a `<button type="button" class="choice" aria-pressed>`,
  restores the reader's saved place (localStorage `civic-place`, ids only) and keeps the layer rows,
  counts and "next on your ballot" strip in step. No place is preselected on a first visit.

Defaults follow the existing rules in civic/layers.py: a town that lies in one township gets that
township; a city split across townships (South Bend, Mishawaka) asks which one; the school
corporation default comes from place names in the guide's data and can be changed.
"""
from __future__ import annotations

import re

from .html import Markup, h

NO_PLACE_VISIBLE = {"state", "county", "township:any", "school:any", "library"}


def picker_state(data: dict, default_place: str | None):
    """Selected place, township, school and the set of visible layer ids (same rules as the landing page).
    ``default_place=None`` means no place is chosen: only the layers everyone has are shown, with the
    'pick one' placeholders for township and school corporation."""
    if not default_place:
        return None, "any", "any", set(NO_PLACE_VISIBLE)
    place = next(p for p in data["places"] if p["id"] == default_place)
    sel_town = place["township"] or place["township_default"]
    sel_school = place["school_default"]
    visible = {"state", "county", f"township:{sel_town}", f"school:{sel_school}", "library"}
    if place["muni"]:
        visible.add(f"municipality:{place['muni']}")
    return place, sel_town, sel_school, visible


def _short_place(name: str) -> str:
    return re.sub(r"^(City|Town) of |\s+Township$", "", name)


def _in_townships(ed) -> dict[str, list[str]]:
    """place unit id -> township unit ids it lies in (derived/township_places.csv), in unit order."""
    order = [u["unit_id"] for u in ed.tables["units"] if u["unit_type"] == "township"]
    out: dict[str, set] = {}
    for r in ed.table("derived/township_places"):
        if r.get("place_unit_id"):
            out.setdefault(r["place_unit_id"], set()).add(r["township_unit_id"])
    return {k: [t for t in order if t in v] for k, v in out.items()}


def place_page(p: dict) -> str:
    """Site path of a picker place's own page (a city or town, or the township for unincorporated areas)."""
    return f"places/{p['muni'] or p['township']}/index.html"


def here_payload(ed, data: dict) -> dict:
    """Names and default rules for every pickable place, township and school corporation (ids only are
    stored in the browser; names come from here). Small enough to ship on every page."""
    inside = _in_townships(ed)
    places = {}
    for p in data["places"]:
        places[p["id"]] = {"n": p["label"], "s": _short_place(p["label"].replace("Unincorporated ", "")), "k": p["kind"],
                           "m": p["muni"] or "", "t": p["township"] or "", "td": p["township_default"],
                           "sd": p["school_default"], "it": inside.get(p["muni"], []) if p["muni"] else [],
                           "u": place_page(p)}
    return {"places": places,
            "townships": {u["unit_id"]: u["name"] for u in data["townships"]},
            "schools": {u["unit_id"]: u["name"] for u in data["schools"]}}


def _choice(page, kind: str, value: str, label: str, href: str | None) -> Markup:
    """One choice. With a page to go to it is a link (the no-JS form); here.js swaps it for a button."""
    attrs = {"class": "choice", "data-pick": kind, "data-value": value}
    if href:
        return h("li", None, h("a", dict(attrs, href=page.rel(href)), label))
    return h("li", {"data-js-only": True, "hidden": True},
             h("button", dict(attrs, type="button", **{"aria-pressed": "false"}), label))


def place_picker(page, data: dict, intro=None, heading_level: str = "h3") -> Markup:
    """The visible place picker (see module docstring). ``intro`` goes above the lists."""
    ed = page.ed
    hx = heading_level
    munis = [p for p in data["places"] if p["muni"]]
    uninc = [p for p in data["places"] if not p["muni"]]
    cities = [p for p in munis if p["kind"] == "city"] + [p for p in munis if p["kind"] != "city"]

    def group(gid, title, items, note=None, js_only=False):
        return h("div", {"class": "pick-group", "id": f"pick-{gid}", "role": "group", "aria-labelledby": f"pick-{gid}-h",
                         "data-js-only": True if js_only else None, "hidden": True if js_only else None},
                 h(hx, {"class": "pick-h", "id": f"pick-{gid}-h"}, title),
                 h("p", {"class": "pick-note muted", "id": f"pick-{gid}-note"}, note) if note is not None else None,
                 h("ul", {"class": "choice-list"}, items))

    place_items = [_choice(page, "place", p["id"], _short_place(p["label"]), place_page(p)) for p in cities]
    uninc_items = [_choice(page, "place", p["id"], _short_place(p["label"].replace("Unincorporated ", "")), place_page(p))
                   for p in uninc]
    # Which township, for a city or town: buttons only (the no-JS township list is the group above).
    town_items = [_choice(page, "township", u["unit_id"], _short_place(u["name"]), None) for u in data["townships"]]
    town_items.append(_choice(page, "township", "any", "Not sure", None))
    school_items = [_choice(page, "school", u["unit_id"], u["name"], f"schools/index.html#{u['unit_id']}") for u in data["schools"]]
    school_items.append(_choice(page, "school", "any", "Not sure", None))

    return h("div", {"class": "pick-lists", "id": "place-picker", "data-picker": True},
             intro,
             h("p", {"class": "pick-nojs muted"},
               "Each name below opens that place's page. With JavaScript on, choosing one here also shows its "
               "governments and seats on this page and remembers it on this device."),
             h("div", {"class": "pick-status", "id": "pick-status", "role": "status", "aria-live": "polite",
                       "data-js-only": True, "hidden": True},
               h("p", {"class": "pick-status-line"}, h("span", {"class": "pick-status-label"}, "Showing: "),
                 h("span", {"id": "pick-status-text"}, "No place picked yet")),
               h("button", {"type": "button", "class": "btn btn-small pick-clear", "id": "pick-clear", "hidden": True},
                 "Clear my place")),
             group("places", "Cities and towns", place_items),
             group("uninc", "Outside a city or town? Pick your township", uninc_items),
             group("township", "Which township is your address in?", town_items, note="", js_only=True),
             group("school", "School corporation", school_items,
                   note="Picked for you from place names in the guide's data when the guide has a match. Change it if yours is different."),
             h("p", {"class": "picker-help"},
               "The guide doesn't match addresses to districts. Defaults come from place names in the guide's data. "
               "To look up your exact districts, use the ",
               h("a", {"href": "https://indianavoters.in.gov/", "target": "_blank", "rel": "noopener"},
                 "Indiana Voter Portal"), "."),
             h("p", {"class": "pick-privacy muted", "data-js-only": True, "hidden": True},
               "Your choice is saved only in this browser, as place codes. It is never sent anywhere."))


def picker_form(data: dict, place: dict | None, sel_town: str, sel_school: str, page=None):
    """Kept for callers of the old dropdown form: renders the visible picker (``page`` is required now,
    because the no-JS choices are links)."""
    if page is None:
        raise TypeError("picker_form now needs page= (the picker's no-JS choices are links)")
    return place_picker(page, data)


def layer_rows(page, layers: dict, visible: set):
    from pages.landing import _layer_row  # the landing page's own layer row builder
    order = ["state", "county", "township", "municipality", "school", "library"]
    return [_layer_row(page, L, L.layer_id in visible) for key in order for L in layers.values() if L.key == key]
