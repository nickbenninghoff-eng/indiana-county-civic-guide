"""Government pages: which governments have a page, their paths and tabs (phase 6 step 3, 2026-11-16;
planning/design-direction-2026-11-16.md sections 2 to 4). One home per government, with the tabs of civic/tabs.py:

    governments/index.html                  the Governments hub (pages/governments.py build_hub): the boundary map,
                                            then every government grouped by type
    governments/<id>/index.html             Overview: at a glance, how it is organised, its offices, appointed boards,
                                            contact, the community strip
    governments/<id>/elections/             recent results for its offices
    governments/<id>/money/                 budget over time, money in and out, tax base, debt, state audits
    governments/<id>/history/               party control over time, holders over time (links to office History tabs)
    governments/<id>/sources/               citations and gaps

Which governments: the county, every city, town, township and school corporation in units.csv, and every library and
special unit with figures in the money files (budgets, debt, tax rates, the state's annual-report income and spending,
certified assessed value). A unit in units.csv keeps its unit_id as its page id ("south-bend", "phm", "sjcpl"); a unit
that is only in the money files uses its money id ("library-walkerton"). The county is "county".

Which tabs a government has is decided here, from the data alone, and the sitemap, the builder and the search index
all read ``gov_tabs``, so a tab bar never links to a page that is not built. Nothing here renders or computes a figure;
the pages reuse the rendering functions of pages/places.py, pages/county.py and pages/money.py.
"""
from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass, field

from . import tabs

HUB = "governments/index.html"
GROUP = "Governments"

# hub groups, in the order of the list (ids are the hub's section ids; old places/index.html ids cities, towns and
# townships land on them)
GROUPS = OrderedDict([("county", "County"), ("cities", "Cities"), ("towns", "Towns"), ("townships", "Townships"),
                      ("schools", "School corporations"), ("special", "Libraries and special units")])
GROUP_OF_TYPE = {"county": "county", "city": "cities", "town": "towns", "township": "townships",
                 "school_corporation": "schools"}
KIND_LABEL = {"county": "County", "city": "City", "town": "Town", "township": "Township",
              "school_corporation": "School corporation", "library": "Public library", "special": "Special unit"}
# unit types (units.csv) that sit in the hub's "Libraries and special units" group when they have money figures
SPECIAL_TYPES = ("library", "transit", "airport_authority", "health_board", "housing_authority")
MONEY_SPECIAL_GROUPS = ("library", "special")     # money-id prefixes (pages/money.py GROUPS)


@dataclass
class Gov:
    gid: str                   # page id (governments/<gid>/)
    name: str
    kind: str                  # county | city | town | township | school_corporation | library | special
    group: str                 # hub group id (GROUPS)
    unit_id: str | None = None          # units.csv id, when the unit is in units.csv
    money_ids: list = field(default_factory=list)   # ids in the money files (budgets.csv, debt.csv, ...)

    @property
    def short(self) -> str:
        return re.sub(r"^(City|Town) of ", "", self.name)


def _clean_label(label: str) -> str:
    return re.sub(r" \(state data: .*\)$", "", label)


def _money_ids_by_unit(ed) -> dict:
    """units.csv id -> [money ids], and money-only ids -> [themselves] (pages/money.py Money.unit_ids order)."""
    from pages.money import money
    mo = money(ed)
    out: dict = {}
    for mid in mo.unit_ids:
        uid = ed.unit_alias(mid) or None
        out.setdefault(uid or mid, []).append(mid)
    return out


def _has_money_data(ed, mids: list[str]) -> bool:
    from pages.money import money
    from .spending import has_money_in_out
    from .tax_base import latest_certified
    mo = money(ed)
    for mid in mids:
        if mo.has_budget(mid) or has_money_in_out(ed, mid) or latest_certified(ed, mid):
            return True
        if any(r["unit_id"] == mid for r in mo.debt) or any(r["unit_id"] == mid for r in mo.rates):
            return True
        if any(r["unit_id"] == mid for r in mo.breakdowns):
            return True
    return False


def governments(ed) -> list[Gov]:
    """Every government with a page, in the hub's order: the county, cities, towns, townships, school corporations
    (units.csv order within each), then the libraries and special units with money figures (money-file order)."""
    got = ed.__dict__.get("_governments")
    if got is not None:
        return got
    by_unit = _money_ids_by_unit(ed)
    out: list[Gov] = []
    for u in ed.tables["units"]:
        t = u["unit_type"]
        if t in GROUP_OF_TYPE:
            out.append(Gov(u["unit_id"], u["name"], t, GROUP_OF_TYPE[t], u["unit_id"], by_unit.get(u["unit_id"], [])))
    from pages.money import GATEWAY_LABELS, group_of, money
    mo = money(ed)
    from .spending import _rows
    _rows(ed, "")    # fills ed._spending_cache (the annual-report ids)
    spending_ids = list(getattr(ed, "_spending_cache", {}) or {})
    special_mids = [m for m in mo.unit_ids if group_of(m) in MONEY_SPECIAL_GROUPS]
    special_mids += [m for m in spending_ids if group_of(m) in MONEY_SPECIAL_GROUPS and m not in special_mids]
    seen = set()
    for mid in special_mids:
        uid = ed.unit_alias(mid) or None
        gid = uid or mid
        if gid in seen:
            continue
        mids = by_unit.get(gid, [mid])
        if mid not in mids:
            mids = mids + [mid]
        if not _has_money_data(ed, mids):
            continue
        seen.add(gid)
        if uid and uid in ed.units:
            name = ed.units[uid]["name"]
            kind = "library" if ed.units[uid]["unit_type"] == "library" else "special"
        else:
            name = _clean_label(mo.label(mid) if mid in mo.unit_ids else GATEWAY_LABELS.get(mid, mid))
            kind = "library" if group_of(mid) == "library" else "special"
        out.append(Gov(gid, name, kind, "special", uid, mids))
    ed.__dict__["_governments"] = out
    return out


def by_id(ed) -> dict:
    return {g.gid: g for g in governments(ed)}


def gov_for_unit(ed, unit_id: str) -> Gov | None:
    """The government page for a units.csv id. The county courts' page is the county's (courts are a section of its
    Overview)."""
    if unit_id == "sjc-courts" or (ed.units.get(unit_id) or {}).get("unit_type") == "court_system":
        unit_id = "county"
    return by_id(ed).get(unit_id)


def gov_for_money_id(ed, mid: str) -> Gov | None:
    for g in governments(ed):
        if mid in g.money_ids:
            return g
    return None


def base(gid: str) -> str:
    return f"governments/{gid}/"


def path(gid: str, tab: str = "overview") -> str:
    return tabs.tab_path(base(gid), tab)


# ------------------------------------------------------------------ which tabs

def _offices(ed, g: Gov) -> list[dict]:
    if not g.unit_id:
        return []
    offs = list(ed.offices_for(g.unit_id))
    if g.kind == "county":
        offs += ed.offices_for("sjc-courts")
    return offs


def has_elections(ed, g: Gov) -> bool:
    if g.kind in ("city", "town", "township"):
        from pages.places import _mayor_block_contests, _place_contests
        return bool(_place_contests(ed, g.unit_id)) or bool(_mayor_block_contests(ed, g.unit_id))
    if g.kind == "school_corporation":
        from pages.places import _school_contests
        return bool(_school_contests(ed, g.unit_id))
    if g.kind == "county":
        return any(ed.contests_for_office(o["office_id"]) for o in _offices(ed, g))
    return False


def has_money(ed, g: Gov) -> bool:
    if g.unit_id and any(r["unit_id"] == g.unit_id for r in ed.table("audits")):
        return True
    return _has_money_data(ed, g.money_ids)


def has_history(ed, g: Gov) -> bool:
    """History: party control over time (needs two years of holders) or any office whose History tab exists."""
    return any(ed.terms_for(o["office_id"]) for o in _offices(ed, g))


def gov_tabs(ed, gid: str) -> list[str]:
    cache = ed.__dict__.setdefault("_gov_tabs", {})
    if gid in cache:
        return cache[gid]
    g = by_id(ed)[gid]
    keys = ["overview"]
    if has_elections(ed, g):
        keys.append("elections")
    if has_money(ed, g):
        keys.append("money")
    if has_history(ed, g):
        keys.append("history")
    keys.append("sources")
    cache[gid] = tabs.ordered(keys)
    return cache[gid]


# ------------------------------------------------------------------ sitemap

def crumb(ed, g: Gov) -> list:
    """Governments › <group> › <government>."""
    label = GROUPS[g.group]
    if g.group == "county":
        return [("Governments", HUB), (g.name, None)]
    return [("Governments", HUB), (label, f"{HUB}#{g.group}"), (g.name, None)]


def _descriptions(g: Gov) -> dict:
    n = g.name
    return {"overview": f"{n}: how it is organised, its offices and who holds them, appointed boards and how to "
                        "reach it.",
            "elections": f"{n}: recent election results for its offices.",
            "money": f"{n}: budget over time, money in and money out, tax base and debt"
                     + (", and state audits." if g.kind == "town" else "."),
            "history": f"{n}: party control over time and every office's holders.",
            "sources": f"{n}: every source behind these pages, and what the guide has not found."}


def government_entries(ed) -> list:
    """Sitemap entries: the hub, then every government's tabs."""
    from .sitemap import Entry
    gs = governments(ed)
    out = [Entry(HUB, "Governments", "Governments",
                 f"Every local government in the county on one map and in one list: the county, {sum(1 for g in gs if g.kind == 'city')} "
                 f"cities, {sum(1 for g in gs if g.kind == 'town')} towns, {sum(1 for g in gs if g.kind == 'township')} "
                 f"townships, {sum(1 for g in gs if g.kind == 'school_corporation')} school corporations and the "
                 "libraries and special units. Each has its own page.", "county", GROUP, [])]
    for g in gs:
        keys = gov_tabs(ed, g.gid)
        d = _descriptions(g)
        out += tabs.tab_entries(base(g.gid), g.name, d["overview"], keys, group=GROUP, crumb=crumb(ed, g),
                                tab_descriptions=d)
    return out


def moved_pages(ed) -> dict:
    """{old site path: new site path} for the pages whose content moved to the government pages (sitemap
    Entry.moved_to; the search index leaves forwarding pages out). schools/ was split into one page per corporation,
    so it points at the hub's School corporations group."""
    out = {"places/index.html": HUB, "county/index.html": path("county"), "schools/index.html": f"{HUB}#schools"}
    for g in governments(ed):
        if g.kind in ("city", "town", "township"):
            out[f"places/{g.gid}/index.html"] = path(g.gid)
    return out


# ------------------------------------------------------------------ links in

def href(page, gid: str | None, tab: str = "overview", frag: str = "") -> str | None:
    """Relative link from ``page`` to a government tab (with an optional #fragment), or None when that page is not in
    this build."""
    if not gid:
        return None
    p = path(gid, tab)
    if p not in page.site.by_path:
        return None
    return page.rel(p + (f"#{frag}" if frag else ""))


def unit_href(page, unit_id: str, tab: str = "overview", frag: str = "") -> str | None:
    g = gov_for_unit(page.ed, unit_id)
    return href(page, g.gid if g else None, tab, frag)


def unit_page(ed, unit_id: str, tab: str = "overview") -> str | None:
    """Site path of a unit's government page (or one tab), for callers that link by site path (page.rel later);
    None when the unit has no government page. For civic/offices.py government_page and the related rail."""
    g = gov_for_unit(ed, unit_id)
    if not g:
        return None
    if tab != "overview" and tab not in gov_tabs(ed, g.gid):
        return None
    return path(g.gid, tab)


def gov_link(page, gid: str, tab: str = "overview", text: str | None = None, cls: str = "gov-link"):
    from .html import h
    from .tabs import TAB_LABELS
    u = href(page, gid, tab)
    if not u:
        return None
    g = by_id(page.ed)[gid]
    if text is None:
        text = g.name if tab == "overview" else f"{g.name}: {TAB_LABELS[tab].lower()}"
    return h("a", {"class": cls, "href": u}, text)


# ------------------------------------------------------------------ the count (added 2026-11-18, phase 6 home follow-up)
# One number for "how many governments", used by the home page headline, the home page's list and the Governments hub,
# so they always agree. It counts the pages: every unit in governments() (the county, cities, towns, townships, school
# corporations, and the libraries and special units with figures in the state's money files). Not every one of them is
# a separate unit of government (the South Bend Redevelopment Commission is a board of the city; a fire protection
# territory is run through the budgets of the units in it), so the wording is "governments and public bodies", which is
# true of each, and the breakdown says what is counted. Not counted, because they have no page: the county courts and the
# board of health (part of the county government), the two housing authorities, and the state chambers.
COUNT_NOUN = "governments and public bodies"
_KIND_WORDS = [("county", "the county", "the county"), ("city", "city", "cities"), ("town", "town", "towns"),
               ("township", "township", "townships"), ("school_corporation", "school corporation",
                                                       "school corporations"),
               ("library", "public library", "public libraries"), ("special", "special unit", "special units")]


def count(ed) -> dict:
    """{"n": 40, "noun": "governments and public bodies", "by_kind": {kind: n}, "parts": "the county, 2 cities, ...",
    "special": [names of the special units]}."""
    gs = governments(ed)
    by_kind = {k: sum(1 for g in gs if g.kind == k) for k, _s, _p in _KIND_WORDS}
    parts = []
    for k, sing, plur in _KIND_WORDS:
        n = by_kind[k]
        if not n:
            continue
        parts.append(sing if k == "county" else f"{n} {sing if n == 1 else plur}")
    text = ", ".join(parts[:-1]) + (" and " if len(parts) > 1 else "") + parts[-1] if parts else ""
    return {"n": len(gs), "noun": COUNT_NOUN, "by_kind": by_kind, "parts": text,
            "special": [g.name for g in gs if g.kind == "special"]}
