"""'More about <entity>' rail (review pattern P1) and links to one contest in the results explorer (P10).

    related_items(page, unit_id=None, office_id=None)  -> [RelatedLink(key, topic, text, href), ...]
    related_links(page, unit_id=None, office_id=None)  -> <nav class="related"> or None (nothing to link)
    contest_anchor(contest_id)                         -> 'contest-<id>' (the explorer's deep-link id)
    contest_href(page, contest_id)                     -> 'elections/results/index.html#contest-<id>' or None

The rail is a short row of links to the same entity on other topics: its place page, its latest result in the
explorer, how areas voted on the map, its campaign money page, its budget, its tax rate, community figures, the
run-for-office page for its seats and its year on the election calendar. Every link is read from data the target page
is built from, so a unit with no budget rows gets no budget link, a contest before the explorer's first year gets no
result link, and so on. The target ids are the ones those pages already print; build.py --check (check.py) fails the
build on any link here whose page or #id is not built, and tools/tests/test_wave_a_patterns.py pins the rules below
to the pages that make the ids.

Added 2026-11-09 (Wave A, batch 1). Shown first on South Bend's place page and the county page; batch 3 rolls it out
to every place page, batch 7 to county, schools and legislators, and the campaign area pages can use it to link back
to their place (the 'place' item).
"""
from __future__ import annotations

import re
from collections import namedtuple

from .html import Markup, h

RESULTS_PAGE = "elections/results/index.html"
# The explorer lists elections from this year on. Must equal pages/elections.py RESULTS_FROM (a test pins it).
RESULTS_FROM = "2010"
# Years with a card (id="y<year>") on the election calendar. Must equal pages/elections.py YEARS (a test pins it).
CALENDAR_YEARS = range(2026, 2031)
CALENDAR_PAGE = "elections/calendar/index.html"
BUDGETS_PAGE = "money/budgets/index.html"
TAX_BILL_PAGE = "money/your-tax-bill/index.html"
MAP_PAGE = "map/index.html"
PEOPLE_PAGE = "community/people/index.html"
RUN_INDEX = "run/index.html"

# offices.csv office types -> the run/<slug>/ page for that seat (elected seats only; pages/participate.py OFFICES
# lists the same types per page, a test pins it). Order: the first match names the unit's main run page.
RUN_FOR_TYPE = {
    "city_council_district": "city-council", "city_council_at_large": "city-council",
    "county_council_member": "county-council",
    "school_board_district": "school-board", "school_board_at_large": "school-board",
    "township_trustee": "township-trustee", "township_board_member": "township-board",
}
RUN_LABEL = {"city-council": "city council", "county-council": "county council", "school-board": "school board",
             "township-trustee": "township trustee", "township-board": "township board"}

# The office whose latest result the rail links to, by unit type (same head offices as civic/answers.py).
HEAD_TYPE = {"city": "mayor", "town": "town_clerk_treasurer", "township": "township_trustee"}

RelatedLink = namedtuple("RelatedLink", "key topic text href")
ORDER = ("place", "results", "map-votes", "campaigns", "budget", "tax-rate", "community", "run", "calendar")
_ID_OK = re.compile(r"[A-Za-z0-9-]+")


# ------------------------------------------------------------------ one contest in the results explorer (P10)

def contest_anchor(contest_id: str) -> str:
    """The id the results page gives a contest's row ('contest-2023g-south-bend-mayor'); static/js/elections.js opens
    the explorer on that one contest when the address ends in #contest-<id>."""
    if not _ID_OK.fullmatch(contest_id or ""):
        raise ValueError(f"contest id {contest_id!r} has characters other than letters, digits and hyphens")
    return f"contest-{contest_id}"


def in_results(ed, contest_id: str) -> bool:
    """True when the results explorer lists this contest (its election is in the guide and from RESULTS_FROM on)."""
    c = ed.contests.get(contest_id)
    if not c or not _ID_OK.fullmatch(contest_id):
        return False
    e = ed.elections.get(c["election_id"])
    return bool(e) and e["date"] >= RESULTS_FROM


def contest_href(page, contest_id: str) -> str | None:
    """Relative link from ``page`` to one contest in the results explorer, or None when the explorer doesn't list it.
    With JavaScript the explorer opens showing only that contest; without it the link lands on the contest's row in
    the 'every contest' table."""
    if not in_results(page.ed, contest_id):
        return None
    return page.rel(f"{RESULTS_PAGE}#{contest_anchor(contest_id)}")


def latest_contest(ed, office_id: str) -> dict | None:
    """The office's most recent general-election contest that the explorer lists (None when it has none)."""
    shown = [c for c in ed.contests_for_office(office_id) if in_results(ed, c["contest_id"])]
    return shown[-1] if shown else None


# ------------------------------------------------------------------ data the rail reads

def _year(ed, c) -> str:
    return (ed.elections.get(c["election_id"], {}).get("date") or "")[:4]


def _map_races(ed) -> dict:
    """{results contest_id: map race id} for races on the map's "How areas voted" layer (cached per build)."""
    got = ed.__dict__.get("_related_map_races")
    if got is None:
        from .map import load_shapes, load_votes, race_by_contest
        shapes = load_shapes(ed)
        got = race_by_contest(ed, load_votes(ed)) if shapes and "precinct" in shapes.get("layers", {}) else {}
        ed.__dict__["_related_map_races"] = got
    return got


def _money_ids(ed, uid: str) -> list[str]:
    """Money-file ids ('city-south-bend') that pages/money.py files under this units.csv id."""
    ids = []
    for t in ("budgets", "tax_rates", "debt", "budget_breakdowns", "derived/unit_id_aliases"):
        for r in ed.table(t):
            mid = r.get("alias_id") if t == "derived/unit_id_aliases" else r.get("unit_id")
            if not mid or mid in ids:
                continue
            if t == "derived/unit_id_aliases" and not r.get("unit_id"):
                continue
            if ed.unit_alias(mid) == uid:
                ids.append(mid)
    return ids


def _has_rate(ed, mids: list[str]) -> bool:
    return any(r.get("unit_id") in mids for r in ed.table("tax_rates"))


def _community(ed, unit: dict) -> tuple[str, str] | None:
    """(target, text) on Who lives here: the cities and the county are in its population tables, the townships in
    its Townships section. Only when the guide has the unit's census figures."""
    from .answers import population_rows
    census, acs = population_rows(ed, unit)
    if not (census or acs):
        return None
    t = unit["unit_type"]
    if t in ("city", "county"):
        return f"{PEOPLE_PAGE}#who", "Who lives here"
    if t == "township":
        return f"{PEOPLE_PAGE}#townships", "Who lives here, by township"
    return None


def _next_year(ed, offices: list[dict]) -> int | None:
    from .layers import _next
    nxt = _next(ed, [o for o in offices if o.get("elected", "yes") != "no"])
    return int(min(nxt)) if nxt else None


def _place_target(unit: dict) -> tuple[str, str] | None:
    t, uid = unit["unit_type"], unit["unit_id"]
    if t in ("city", "town", "township"):
        return f"places/{uid}/index.html", unit["name"]
    if t == "county":
        return "county/index.html", "County government"
    if t == "school_corporation":
        return f"schools/index.html#{uid}", unit["name"]
    return None


def _short(unit: dict) -> str:
    return re.sub(r"^(City|Town) of ", "", unit["name"])


def _office_name(ed, office: dict, unit: dict, exact: bool) -> str:
    """The office as the rail names it: the full title for one office; on a unit's rail the title without the unit's
    name ('Mayor', 'Treasurer') and without a district (the link is about the unit, not one district)."""
    title = office["title"]
    if exact:
        return title
    t = re.sub(r",? ?(District|Ward) .*|, At-Large.*", "", title)
    for n in (unit["name"], _short(unit), "St. Joseph County", "County"):
        t = re.sub(rf"(^|\s)(of\s+)?{re.escape(n)}(\s|$)", " ", t).strip()
    return t[:1].upper() + t[1:] if t else title


# ------------------------------------------------------------------ the rail

def related_items(page, unit_id: str | None = None, office_id: str | None = None) -> list[RelatedLink]:
    """The rail's links for a unit (a city, town, township, the county, a school corporation) or one office, in the
    fixed ORDER. With only ``office_id`` the unit is the office's. Links to the page itself are left out; so is any
    topic whose data the guide doesn't hold. Hrefs are relative to ``page``."""
    ed = page.ed
    built = page.site.by_path
    office = ed.offices.get(office_id) if office_id else None
    if office_id and office is None:
        raise KeyError(f"related_items: unknown office_id {office_id!r}")
    uid = unit_id or (office["unit_id"] if office else None)
    unit = ed.units.get(uid) if uid else None
    if unit is None:
        raise KeyError(f"related_items: unknown unit_id {uid!r}")
    offices = [office] if office else [o for o in ed.offices_for(uid) if o.get("elected", "yes") != "no"]
    out: dict[str, RelatedLink] = {}

    def add(key, topic, text, target):
        path, _, frag = target.partition("#")
        if path == page.path or path not in built:
            return
        if frag and not _ID_OK.fullmatch(frag):
            return
        out[key] = RelatedLink(key, topic, text, page.rel(target))

    pt = _place_target(unit)
    if pt and not office:
        add("place", "Place" if unit["unit_type"] in ("city", "town", "township") else "Government", pt[1], pt[0])
    elif pt:
        add("place", "Government", pt[1], pt[0])

    # latest result in the explorer, and the same race on the map when it is there
    head = office or next((o for o in offices if o["office_type"] == HEAD_TYPE.get(unit["unit_type"])), None)
    c = latest_contest(ed, head["office_id"]) if head else None
    if c:
        add("results", "Latest result", f"{_office_name(ed, head, unit, bool(office))}, {_year(ed, c)}",
            f"{RESULTS_PAGE}#{contest_anchor(c['contest_id'])}")
    # the head office's latest race on the map's "How areas voted" layer, else the unit's latest race there
    races = _map_races(ed)
    on_map = [(o, c) for o in offices for c in ed.contests_for_office(o["office_id"]) if c["contest_id"] in races]
    if on_map:
        pick = [x for x in on_map if head and x[0]["office_id"] == head["office_id"]] or on_map
        o, last = max(pick, key=lambda x: (_year(ed, x[1]), x[1]["contest_id"]))
        add("map-votes", "On the map", f"{_office_name(ed, o, unit, bool(office))}, {_year(ed, last)}, by precinct",
            f"{MAP_PAGE}#race-{races[last['contest_id']]}")

    # campaign money
    from .campaign_money import STATE_AREA, area_id, area_path
    if office and office["office_type"] in ("state_house", "state_senate"):
        add("campaigns", "Campaign money", "State legislators' committees", area_path(STATE_AREA))
    elif unit["unit_type"] in ("city", "town", "township", "county", "school_corporation"):
        add("campaigns", "Campaign money", "County races" if unit["unit_type"] == "county" else
            "School board races" if unit["unit_type"] == "school_corporation" else f"{_short(unit)} races",
            area_path(area_id(uid)))

    # money
    mids = _money_ids(ed, uid)
    if mids:
        add("budget", "Budget", "Budget history and breakdown", f"{BUDGETS_PAGE}#{uid}")
    if _has_rate(ed, mids):
        add("tax-rate", "Tax rate", "Certified rate, every unit", f"{TAX_BILL_PAGE}#all-rates")

    # community figures
    cm = _community(ed, unit) if not office else None
    if cm:
        add("community", "Community", cm[1], cm[0])

    # run for this seat; a city, town or township with elected seats but no seat-specific run page (the towns) gets
    # the general run page (added 2026-11-09, Wave B batch 3: every place page answers "how do I get involved")
    slug = next((RUN_FOR_TYPE[o["office_type"]] for o in offices if o["office_type"] in RUN_FOR_TYPE), None)
    if slug:
        add("run", "Run for office", f"Run for {RUN_LABEL[slug]}", f"run/{slug}/index.html")
    elif not office and offices and unit["unit_type"] in ("city", "town", "township"):
        add("run", "Run for office", "How to run for local office", RUN_INDEX)

    # its year on the election calendar
    y = _next_year(ed, offices)
    if y in CALENDAR_YEARS:
        add("calendar", "Next election", f"{y} on the calendar", f"{CALENDAR_PAGE}#y{y}")
    return [out[k] for k in ORDER if k in out]


def related_links(page, unit_id: str | None = None, office_id: str | None = None, *, name: str | None = None,
                  exclude: tuple[str, ...] | list[str] = (), rail_id: str = "related") -> Markup | None:
    """The rail: ``<nav class="related" id=rail_id aria-labelledby=rail_id-h>`` with an h2 "More about <name>" and a
    ``<ul class="related-list">`` of ``<a class="related-link">`` (a small topic line, then the link text). ``exclude``
    drops item keys (see ORDER) a page already links prominently. Returns None when no link is left. Put it right
    after the page's "At a glance" box (or under the hero)."""
    items = [i for i in related_items(page, unit_id, office_id) if i.key not in set(exclude)]
    if not items:
        return None
    ed = page.ed
    if name is None:
        unit = ed.units.get(unit_id) if unit_id else ed.units.get(ed.offices[office_id]["unit_id"])
        name = ed.offices[office_id]["title"] if office_id and not unit_id else (
            "county government" if unit["unit_type"] == "county" else _short(unit))
    return related_rail(items, name=name, rail_id=rail_id)


def related_rail(items: list[RelatedLink], *, name: str, rail_id: str = "related", heading_tag: str = "h2") -> Markup | None:
    """The rail's markup for a list of links the caller has already chosen (related_items output, reordered or with
    page-specific RelatedLink rows added; every href must be a static link to a built page so check.py checks it).
    Same markup as related_links. Added 2026-11-09 (Wave C batch 7: the county rail adds links to other governments
    in the county; the schools page puts one rail inside each corporation, with an h3)."""
    if not items:
        return None
    return h("nav", {"class": "related", "id": rail_id, "aria-labelledby": f"{rail_id}-h"},
             h(heading_tag, {"class": "related-h", "id": f"{rail_id}-h"}, f"More about {name}"),
             h("ul", {"class": "related-list"},
               [h("li", {"data-related": i.key},
                  h("a", {"class": "related-link", "href": i.href},
                    h("span", {"class": "related-topic"}, i.topic),
                    h("span", {"class": "related-text"}, i.text))) for i in items]))


# ------------------------------------------------------------------ one seat (added 2026-11-09, Wave B batch 3)

def campaign_race_anchor(contest_id: str) -> str:
    """The id a campaign area page gives one race's card ('r-2023g-south-bend-council-1'; pages/campaign_pages.py
    race_block)."""
    if not _ID_OK.fullmatch(contest_id or ""):
        raise ValueError(f"contest id {contest_id!r} has characters other than letters, digits and hyphens")
    return f"r-{contest_id}"


def seat_items(page, office_id: str, campaign_races=(), on_page=()) -> list[RelatedLink]:
    """Links for one seat on its own government's page (a holder row, a district map panel), in this order:

      'on-page'    its latest contest on this page (#res-<contest id>), when ``on_page`` lists that contest
      'results'    its latest contest in the results explorer (#contest-<id>), when the explorer lists one
      'map-votes'  its latest race on the map's "How areas voted" layer
      'campaigns'  the race card on its campaign area page (#r-<contest id>): only for a contest in
                   ``campaign_races``, the race ids the area page prints (the caller reads them from the same model
                   the area page is built from), newest first

    Nothing is linked that the guide does not build; an unknown office raises KeyError. Hrefs are relative to
    ``page``; texts name the year ("2023 result")."""
    ed = page.ed
    office = ed.offices.get(office_id)
    if office is None:
        raise KeyError(f"seat_items: unknown office_id {office_id!r}")
    built = page.site.by_path
    out: list[RelatedLink] = []

    def add(key, topic, text, target):
        path, _, frag = target.partition("#")
        if path and (path == page.path or path not in built):
            return
        if frag and not _ID_OK.fullmatch(frag):
            return
        out.append(RelatedLink(key, topic, text, page.rel(target) if path else target))

    contests = ed.contests_for_office(office_id)
    shown = [c for c in contests if c["contest_id"] in set(on_page)]
    if shown:
        c = shown[-1]
        add("on-page", "On this page", f"{_year(ed, c)} result on this page", f"#res-{c['contest_id']}")
    c = latest_contest(ed, office_id)
    if c:
        add("results", "Results explorer", f"{_year(ed, c)} in the results explorer",
            f"{RESULTS_PAGE}#{contest_anchor(c['contest_id'])}")
    races = _map_races(ed)
    on_map = [c for c in contests if c["contest_id"] in races]
    if on_map:
        last = max(on_map, key=lambda c: (_year(ed, c), c["contest_id"]))
        add("map-votes", "On the map", f"{_year(ed, last)} on the map, by precinct", f"{MAP_PAGE}#race-{races[last['contest_id']]}")
    from .campaign_money import area_id, area_path
    money = [c for c in contests if c["contest_id"] in set(campaign_races) and _ID_OK.fullmatch(c["contest_id"])]
    if money:
        c = money[-1]
        add("campaigns", "Campaign money", f"{_year(ed, c)} campaign money",
            f"{area_path(area_id(office['unit_id']))}#{campaign_race_anchor(c['contest_id'])}")
    return out
