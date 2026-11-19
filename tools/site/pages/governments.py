"""Government pages and the Governments hub (phase 6 step 3, 2026-11-16; planning/design-direction-2026-11-16.md).

    governments/index.html                  the boundary map (cities and towns, townships, school corporations; the
                                            panel links to each government's page and tabs), then every government
                                            grouped by type; opens on the reader's saved place (civic/preselect.py)
    governments/<id>/index.html ...         one tabbed page per government (civic/tabs.py; ids and tabs from
                                            civic/governments.py): Overview, Elections, Money, History, Sources

The tab bodies are rendered by the modules that built the old pages, reusing their blocks: pages/places.py
(place_renderers: cities, towns, townships; school_renderers: school corporations), pages/county.py (renderers) and,
for libraries and special units (which had no page, only a block on money/budgets/), this module. No figure is
computed here.

Old URLs keep working. places/<id>/, county/, places/index.html and schools/ are forwarding pages (forward_gov,
forward_hub, forward_schools): a title, one line, a plain link (works with JavaScript off), a canonical link, and
#moved-anchors (static/js/moved.js) with "to" (where the page went) and every old #anchor's new tab. The overview of
each moved government ships the same anchor map, so a Netlify 301 (tools/site/netlify_prep.py writes _redirects from
the forwarding pages' <meta name="civic-moved-to">) still lands an old #anchor on its tab.
"""
from __future__ import annotations

import re
from functools import partial
from pathlib import Path

from civic import governments as gm
from civic import offices as om
from civic import tabs as T
from civic.components import name_with_party, status_badge, term_party
from civic.data import split_ids
from civic.html import Markup, h, join, json_script
from civic.preselect import here_attrs, here_slot

from . import gov_parts as P

_ID_RE = re.compile(r'\sid="([^"]+)"')


# =========================================================================== header

def _seats_text(offices) -> str | None:
    elected = [o for o in offices if o.get("elected", "yes") != "no"]
    if not elected:
        return None
    n = sum(int(o["seats"]) if (o.get("seats") or "").isdigit() else 1 for o in elected)
    blank = any(not (o.get("seats") or "").isdigit() for o in elected)
    return f"{'at least ' if blank else ''}{n} elected seat{'s' if n != 1 else ''}"


def _next_year(offices) -> str | None:
    ys = sorted({o["next_election"] for o in offices if o.get("next_election")})
    return ys[0] if ys else None


def _board(ed, g) -> dict | None:
    return next((b for b in ed.boards if g.unit_id and b["unit_id"] == g.unit_id), None)


def head_for(ed, g) -> T.Head:
    offs = gm._offices(ed, g)
    facts = [gm.KIND_LABEL[g.kind] if g.kind != "county" else "County government"]
    seats = _seats_text(offs)
    if seats:
        facts.append(seats[:1].upper() + seats[1:])
    nxt = _next_year(offs)
    if nxt:
        facts.append(f"Next election {nxt}")
    if not offs and _board(ed, g):
        facts.append("Run by an appointed board")
    return T.Head(kind="Government", title=g.name, facts=facts)


# =========================================================================== libraries and special units

def special_overview(ed, page, g):
    from pages import money as M
    from civic.spending import has_money_in_out
    mo = M.money(ed)
    c = page.cites
    unit = ed.units.get(g.unit_id) if g.unit_id else None
    rows = [("Kind", gm.KIND_LABEL[g.kind])]
    b = _board(ed, g)
    if b:
        rows.append(("Governed by", h("span", None, f"{b['name']}: {b['seats'] or 'seat count not in sources'} seats, "
                                                    f"appointed by {b['appointing_authorities'] or 'appointers not in sources'}. ",
                                      status_badge(b["status"], page), c.cite(b["source_ids"]))))
    for mid in g.money_ids:
        if mo.has_budget(mid):
            rows.append(("Budget", M._unit_digest(mo, mid)))
        if has_money_in_out(ed, mid):
            rows.append(("Money in and out", M._flows_digest(ed, mid)))
    page.add(T.tab_section("glance", "At a glance",
                           h("dl", {"class": "gov-glance"}, [[h("dt", None, k), h("dd", None, v)] for k, v in rows]),
                           # who serves on its board (appointed_board_members.csv, 2026-11-18)
                           P.board_roster(ed, page, b) if b else None))
    what = []
    if b and b.get("what_it_decides"):
        what.append(h("p", None, b["what_it_decides"], c.cite(b["source_ids"])))
    if not unit:
        what.append(h("p", {"class": "muted"}, "Named as in the state budget file. This unit has no entry in the guide's "
                                               "list of governments yet, so the guide has only its money figures."))
    if what:
        page.add(T.tab_section("structure", "What it does", what))
    page.add(P.contact_section(ed, page, unit))
    more = [x for x in (gm.href(page, g.gid, "money"),) if x]
    if more:
        page.add(h("p", {"class": "tnote"}, "Its budget over time, money in and out and debt are on the ",
                   h("a", {"href": more[0]}, "Money tab"), "."))


def special_money(ed, page, g):
    P.money_tab(ed, page, g)


def special_sources(ed, page, g):
    gaps = P.money_gaps(ed, g)
    if not g.unit_id:
        gaps = [{"item": f"{g.name}: entry in the guide's list of governments",
                 "why_missing": "The unit appears only in the state's money files; the guide has no units.csv row for it "
                                "(its board, website and what it does).",
                 "how_to_fill": "Add the unit to units.csv from its own documents or the county's records."}] + gaps
    page.add(*T.sources_body(page, gaps, title=g.name))


def special_renderers(ed, g) -> dict:
    return {"overview": partial(special_overview, ed, g=g), "money": partial(special_money, ed, g=g),
            "sources": partial(special_sources, ed, g=g)}


# =========================================================================== one government

def _renderers(site, g) -> dict:
    ed = site.ed
    if g.kind == "county":
        from . import county
        return county.renderers(site)
    from . import places
    if g.kind in ("city", "town", "township"):
        return places.place_renderers(ed, g)
    if g.kind == "school_corporation":
        return places.school_renderers(ed, g)
    return special_renderers(ed, g)


def build_gov(gid: str, site, tab: str = "overview"):
    """Builds every tab of a government the first time any of its paths is asked for (they share one citation list),
    then returns the asked tab's page. The overview also gets the anchor map of the old page (for a Netlify 301)."""
    ed = site.ed
    done = site.__dict__.setdefault("_gov_pages", {})
    if gid not in done:
        g = gm.by_id(ed)[gid]
        keys = gm.gov_tabs(ed, gid)
        render = _renderers(site, g)
        pages = T.build_tabs(site, gm.base(gid), keys, head_for(ed, g), {k: render[k] for k in keys})
        done[gid] = pages
        if moved_from(ed, gid):
            ov = pages["overview"]
            ov.add(json_script("moved-anchors", _anchor_map(site, gid, ov)))
    pages = done[gid]
    if tab not in pages:
        raise KeyError(f"{gid} has no {tab} tab")
    for p in pages.values():
        site.pages.setdefault(p.path, p)
    return pages[tab]


def tab_ids(site, gid: str) -> dict[str, set]:
    """{tab: ids on that tab's content} of a built government (header and tab bodies; the shell's ids are on every
    page anyway)."""
    pages = site.__dict__["_gov_pages"][gid]
    cache = site.__dict__.setdefault("_gov_ids", {})
    if gid not in cache:
        cache[gid] = {k: set(_ID_RE.findall(str(join(p.parts)))) for k, p in pages.items()}
    return cache[gid]


# =========================================================================== old ids -> new tabs

# old section ids whose content moved to another tab or was renamed (the rest keep their id on some tab)
SECTION_ALIASES = {
    "glance": ("overview", "glance"), "officeholders": ("overview", "officeholders"),
    "structure": ("overview", "structure"), "unelected": ("overview", "unelected"), "context": ("overview", "context"),
    "related": ("overview", "related"), "boards": ("overview", "boards"), "courts": ("overview", "courts"),
    "row-officers": ("overview", "row-officers"), "council-map": ("overview", "officeholders"),
    "results": ("elections", "results"), "mayor-results": ("elections", "mayor-results"),
    "control": ("history", "control"), "control-charts": ("history", "control"),
    "budget": ("money", "budget"), "money": ("money", "money-in-out"), "audits": ("money", "audits"),
    "gaps": ("sources", "gaps"), "sources": ("sources", "sources"),
}
# id prefixes -> (tab, section): ids of blocks that were folded, renamed or dropped land on the section that holds
# their content now. An exact id on any tab always wins (moved.js reads "a" before "p").
PREFIX_ALIASES = [
    ("src-", "sources", "sources"), ("gaps-", "sources", "gaps"),
    ("res-", "elections", "results"), ("results-", "elections", "results"), ("mayor-", "elections", "mayor-results"),
    ("control-", "history", "control"),
    ("money-flows-", "money", "money-in-out"), ("money-", "money", "money-in-out"), ("sp-", "money", "money-in-out"),
    ("bud-", "money", "budget"), ("other-", "money", "budget"), ("brk-", "money", "breakdowns"),
    ("breakdown-", "money", "breakdowns"), ("debt-", "money", "debt"), ("audits-", "money", "audits"),
    ("office-", "overview", "officeholders"), ("offices-", "overview", "officeholders"),
    ("bodies-", "overview", "structure"), ("boards-", "overview", "unelected"), ("context-", "overview", "context"),
    ("litigation", "overview", "structure"), ("row-officers", "overview", "row-officers"),
]
TAB_WORDS = {"elections": "recent results", "money": "budget, money in and out, debt",
             "history": "party control and past holders"}


def moved_from(ed, gid: str) -> str | None:
    """The old page a government had to itself (places/<id>/, county/), or None (school corporations shared
    schools/; libraries and special units had no page)."""
    g = gm.by_id(ed).get(gid)
    if g is None:
        return None
    if g.kind == "county":
        return "county/index.html"
    if g.kind in ("city", "town", "township"):
        return f"places/{gid}/index.html"
    return None


def _resolve(site, gid: str, tab: str, sec: str) -> str | None:
    """Site path#id for a (tab, section) of a government, falling back to the overview's same section, then the
    tab's (or the overview's) top."""
    ids = tab_ids(site, gid)
    for t, s in ((tab, sec), ("overview", sec)):
        if t in ids and s in ids[t]:
            return f"{gm.path(gid, t)}#{s}"
    t = tab if tab in ids else "overview"
    return f"{gm.path(gid, t)}#main"


def anchor_targets(site, gid: str, extra: dict | None = None) -> tuple[dict, dict]:
    """({old id: site path#id}, {id prefix: site path#id}) for one government: every id on a tab other than the
    overview (ids on the overview need no entry: the forwarding page's "to" keeps the id), the section aliases whose id
    is on no tab, the page's own renamed ids (``extra``), and the prefix rules."""
    ids = tab_ids(site, gid)
    ov = ids.get("overview", set())
    a = {}
    for k in T.TAB_ORDER:
        if k == "overview" or k not in ids:
            continue
        for i in sorted(ids[k]):
            if i not in ov and i not in a:
                a[i] = f"{gm.path(gid, k)}#{i}"
    # an id the overview has keeps it, even when a prefix rule below would match it (an office row office-<id>, the
    # community table context-<id>); so do the ids every page's shell carries (the menus: money-menu, offices-menu)
    pres = tuple(pre for pre, _t, _s in PREFIX_ALIASES)
    for i in sorted(ov | shell_ids(site, gid)):
        if i.startswith(pres) and i not in a:
            a[i] = f"{gm.path(gid)}#{i}"
    every = set().union(*ids.values())
    for old, (tab, sec) in SECTION_ALIASES.items():
        if old not in every:
            a[old] = _resolve(site, gid, tab, sec)
    for old, (tab, sec) in (extra or {}).items():
        a[old] = _resolve(site, gid, tab, sec)
    # the edition's status banners (the 2026 UNOFFICIAL notice) are shell ids: they go to the first tab that shows one
    pages = site.__dict__["_gov_pages"][gid]
    for b in site.ed.config.get("status_banners", []):
        bid = f"banner-{b['id']}"
        m = re.match(r"(\d{4})", b.get("id", ""))
        tab = next((k for k in T.TAB_ORDER if k in pages and pages[k].shows_unofficial(year=m.group(1) if m else None)),
                   None)
        a.setdefault(bid, f"{gm.path(gid, tab)}#{bid}" if tab else f"{gm.path(gid)}#main")
    p = {pre: _resolve(site, gid, tab, sec) for pre, tab, sec in PREFIX_ALIASES}
    return a, p


def shell_ids(site, gid: str) -> set:
    """Ids the page shell (header, footer, data blocks) gives a government's overview, outside its content."""
    cache = site.__dict__.setdefault("_gov_shell_ids", {})
    if gid not in cache:
        ov = site.__dict__["_gov_pages"][gid]["overview"]
        cache[gid] = set(_ID_RE.findall(ov.render())) - tab_ids(site, gid)["overview"]
    return cache[gid]


def _extra_moves(gid: str) -> dict:
    if gid == "county":
        from .county import COUNTY_MOVED
        return COUNTY_MOVED
    return {}


def _rel_map(page, a: dict, p: dict, to: str | None = None) -> dict:
    out = {}
    if to:
        out["to"] = page.rel(to)
    out["a"] = {k: page.rel(v) for k, v in a.items()}
    out["p"] = {k: page.rel(v) for k, v in p.items()}
    return out


def _anchor_map(site, gid: str, page) -> dict:
    a, p = anchor_targets(site, gid, _extra_moves(gid))
    return _rel_map(page, a, p)


# =========================================================================== forwarding pages

def forward_page(site, old_path: str, dest: str, dest_label: str, moved, *, redirect: bool = True,
                 parts: list | None = None):
    """A small page in place of one that moved: its title, one line with a plain link (works with JavaScript off), a
    canonical link, and the #moved-anchors map static/js/moved.js reads ("to": where the page went; "a"/"p": old ids
    that went elsewhere; ``moved(page)`` returns it, so its paths are relative to the page). ``redirect``: the move is
    one path to one path, so netlify_prep.py writes a 301 for it (<meta name="civic-moved-to">); a page split into
    several (schools/) is forwarded by the script only.

    ``parts`` [(old id, label, site path#id)]: "Where each part is now", one line per old section and office, each
    carrying its old id. With JavaScript off an old link such as county/index.html#office-county-sheriff lands on its
    line here, which links to the new place; with it, moved.js has already gone on."""
    page = site.page(old_path, body_class="thing-page forward-page")
    page.canonical = dest.split("#")[0]
    if redirect:
        page.head_extra.append(h("meta", {"name": "civic-moved-to", "content": dest.split("#")[0]}))
    page.add(h("header", {"class": "thing-head forward-head"},
               page.crumb_nav(),
               h("h1", {"class": "thing-title"}, page.title),
               h("p", {"class": "thing-facts forward-line"}, "This page has moved to ",
                 h("a", {"class": "forward-link", "href": page.rel(dest)}, dest_label), ".")))
    if parts:
        seen, lis = set(), []
        for oid, label, target in parts:
            if oid in seen:
                continue
            seen.add(oid)
            lis.append(h("li", {"id": oid}, h("a", {"href": page.rel(target)}, label)))
        page.add(T.tab_section("moved-parts", "Where each part of the old page is now", h("ul", {"class": "forward-list"}, lis)))
    page.add(json_script("moved-anchors", moved(page)))
    return page


# the old pages' sections: (old id, label, new tab, new section id)
PLACE_PARTS = [("glance", "At a glance", "overview", "glance"),
               ("officeholders", "Who holds office now", "overview", "officeholders"),
               ("structure", "How it's organized", "overview", "structure"),
               ("unelected", "Unelected but powerful", "overview", "unelected"),
               ("results", "Recent results", "elections", "results"),
               ("mayor-results", "Mayoral results history", "elections", "mayor-results"),
               ("control", "Party control over time", "history", "control"),
               ("budget", "Budget", "money", "budget"),
               ("audits", "State audits", "money", "audits"),
               ("context", "Context: the community", "overview", "context"),
               ("gaps", "Gaps", "sources", "gaps"), ("sources", "Sources", "sources", "sources")]
COUNTY_PARTS = [("glance", "At a glance", "overview", "glance"),
                ("structure", "How county government is organized", "overview", "structure"),
                ("officeholders", "Who holds county offices now", "overview", "officeholders"),
                ("row-officers", "Row officers and what they do", "overview", "row-officers"),
                ("courts", "Courts", "overview", "courts"),
                ("boards", "Appointed boards and who appoints them", "overview", "boards"),
                ("control", "Party control over time", "history", "control"),
                ("results", "Recent results for county offices", "elections", "results"),
                ("money", "Money in and money out", "money", "money-in-out"),
                ("gaps", "Gaps", "sources", "gaps"), ("sources", "Sources", "sources", "sources")]


def _office_parts(site, gid: str, offices: list[dict]) -> list:
    """One line per office: its old card id (office-<id>), linked to its row on the government's Overview."""
    return [(f"office-{o['office_id']}", o["title"], _resolve(site, gid, "overview", f"office-{o['office_id']}"))
            for o in offices]


def _section_parts(site, gid: str, table) -> list:
    out = []
    ids = tab_ids(site, gid)
    for old, label, tab, sec in table:
        if tab in ids and sec in ids[tab]:
            out.append((old, label, f"{gm.path(gid, tab)}#{sec}"))
    return out


def forward_gov(site, old_path: str, gid: str):
    """The forwarding page of a government that had one page (places/<id>/, county/)."""
    build_gov(gid, site)
    ed = site.ed
    g = gm.by_id(ed)[gid]
    dest = gm.path(gid)
    a, p = anchor_targets(site, gid, _extra_moves(gid))
    parts = _section_parts(site, gid, COUNTY_PARTS if g.kind == "county" else PLACE_PARTS)
    mid_anchor = f"money-{gid}"
    if mid_anchor in tab_ids(site, gid).get("money", set()):
        parts.append((mid_anchor, "Money in and money out, from the annual report to the state",
                      f"{gm.path(gid, 'money')}#{mid_anchor}"))
    parts += _office_parts(site, gid, gm._offices(ed, g))
    return forward_page(site, old_path, dest, f"{g.name}: its government page",
                        lambda page: _rel_map(page, a, p, to=dest), parts=parts)


def forward_hub(site, old_path: str):
    """places/index.html: the hub leads with the same map and lists every city, town and township (rows keep the old
    cards' ids, the groups the old section ids)."""
    build_hub(site)
    ed = site.ed
    parts = [("map", "On the map", f"{gm.HUB}#map")]
    for key in ("cities", "towns", "townships"):
        parts.append((key, gm.GROUPS[key], f"{gm.HUB}#{key}"))
    for g in gm.governments(ed):
        if g.kind in ("city", "town", "township"):
            parts.append((g.gid, g.name, f"{gm.HUB}#{g.gid}"))
    return forward_page(site, old_path, gm.HUB, "Governments: every government on one map and in one list",
                        # the old page's city section was id "citys" (f"{kind}s"); its citations go to the hub's list
                        lambda page: {"to": page.rel(gm.HUB),
                                      "a": {"citys": page.rel(f"{gm.HUB}#cities"), "citys-h": page.rel(f"{gm.HUB}#cities")},
                                      "p": {"src-": page.rel(f"{gm.HUB}#sources")}}, parts=parts)


def forward_schools(site):
    """schools/: split into one government page per school corporation, so it is forwarded by the script only (no
    single path to 301 to). Each old id goes to the corporation page that now holds it; the page's own sections go to
    the hub's School corporations group."""
    build_hub(site)   # its sections go to the hub's School corporations group
    ed = site.ed
    old = "schools/index.html"
    corps = [g for g in gm.governments(ed) if g.kind == "school_corporation"]
    a, p = {}, {}
    for g in corps:
        build_gov(g.gid, site)
        ids = tab_ids(site, g.gid)
        for k in T.TAB_ORDER:
            for i in sorted(ids.get(k, ())):
                if i.startswith(("src-", "tabs", "marks", "gaps", "sources", "notes")) or i in a:
                    continue
                if i in ("glance", "glance-h", "where", "where-h", "structure", "structure-h", "officeholders",
                         "officeholders-h", "students", "students-h", "contact", "contact-h", "results", "results-h",
                         "budget", "budget-h", "money-in-out", "money-in-out-h", "tax-base", "tax-base-h", "debt",
                         "debt-h", "holders", "holders-h", "rules", "rules-h", "unelected", "unelected-h",
                         "referenda", "referenda-h", "labels", "breakdowns", "breakdowns-h", "mn-dollars-toggle",
                         "mn-dollars-nominal", "mn-dollars-real"):
                    continue    # section ids every corporation page has: not one corporation's
                a[i] = f"{gm.path(g.gid, k)}#{i}"
        a[g.gid] = f"{gm.path(g.gid)}#main"
        a[f"{g.gid}-h"] = f"{gm.path(g.gid)}#main"
        for pre, tab, sec in (("seats-", "overview", "officeholders"), ("money-flows-", "money", "money-in-out"),
                              ("related-", "overview", "related-" + g.gid), ("atlarge-", "overview", "officeholders"),
                              ("enroll-", "overview", "students"), ("conflict-", "overview", "officeholders"),
                              ("money-", "money", "money-in-out"), ("sp-", "money", "money-in-out"),
                              ("one-", "overview", "main")):
            p[f"{pre}{g.gid}"] = _resolve(site, g.gid, tab, sec)
    for k in ("rules", "rules-h", "overview", "overview-h", "schools-overview", "schools-overview-copy", "gaps", "gaps-h",
              "sources", "sources-h"):
        a.setdefault(k, f"{gm.HUB}#schools")
    p["src-"] = f"{gm.HUB}#schools"
    p["res-"] = f"{gm.HUB}#schools"
    parts = [("rules", "State rules for school boards (on each corporation's page)", _resolve(site, corps[0].gid, "overview", "rules")),
             ("overview", "Corporations at a glance", f"{gm.HUB}#schools")]
    for g in corps:
        parts.append((g.gid, g.name, gm.path(g.gid)))
        mid_anchor = f"money-{g.gid}"
        if mid_anchor in tab_ids(site, g.gid).get("money", set()):
            parts.append((mid_anchor, f"{g.name}: money in and money out", f"{gm.path(g.gid, 'money')}#{mid_anchor}"))
        parts += _office_parts(site, g.gid, gm._offices(ed, g))
    return forward_page(site, old, f"{gm.HUB}#schools", "Governments: the school corporations, each with its own page",
                        lambda page: _rel_map(page, a, p, to=f"{gm.HUB}#schools"), redirect=False, parts=parts)


# =========================================================================== hub

def _row_line(ed, g) -> str:
    offs = gm._offices(ed, g)
    if g.kind == "county":
        return f"{len(offs)} elected offices, the courts and appointed boards"
    bits = []
    seats = _seats_text(offs)
    if seats:
        bits.append(seats if g.kind != "school_corporation" else seats.replace("elected seat", "board seat"))
    nxt = _next_year(offs)
    if nxt:
        bits.append(f"next election {nxt}")
    if not bits:
        bits.append(gm.KIND_LABEL[g.kind] + (", appointed board" if _board(ed, g) else ""))
    return " · ".join(bits)


def _hub_area(page, ed):
    """The hub map's government_layers callback: the boundary map's panel facts (civic/map.py unit_facts; school
    corporations the Schools page's board facts), the government page as the open link and its tabs as more links."""
    from civic.map import TYPE_LABEL, _kind_class, unit_facts
    from .places import _school_board_facts

    def area(key, tab, n, it, uid, unit):
        g = gm.gov_for_unit(ed, uid)
        href = gm.unit_href(page, uid) or "#list"
        note = ""
        if unit["unit_type"] == "school_corporation":
            facts = _school_board_facts(ed, uid)
            if it.get("share_inside") is not None and it["share_inside"] < 0.97:
                note = (f"Partly outside the county: about {round(it['share_inside'] * 100)}% of this district's land "
                        f"area is inside {ed.county_label} (computed from Census boundaries).")
        else:
            f = unit_facts(ed, uid, it)
            facts, note = f["facts"], f["note"]
        more = []
        if g:
            for k in gm.gov_tabs(ed, g.gid):
                if k in ("overview", "sources"):
                    continue
                u = gm.href(page, g.gid, k)
                if u:
                    more.append([f"{T.TAB_LABELS[k]}: {TAB_WORDS[k]}", u])
        tlabel = TYPE_LABEL.get(unit["unit_type"], unit["unit_type"])
        entry = {"n": unit["name"], "t": tlabel, "f": facts, "note": note, "href": href, "l": tab, "d": it["d"],
                 "open": "Open its page", "more": more}
        aria = f"{unit['name']}, {tlabel.lower()}. Open its page." + (f" {note}" if note else "")
        return f"cmap-s {_kind_class(unit, n)}", href, aria, entry, "cmap-dot"
    return area


def build_hub(site):
    ed = site.ed
    if gm.HUB in site.__dict__.setdefault("_gov_hub", {}):
        return site._gov_hub[gm.HUB]
    from civic.map import embedded_map, load_shapes
    page = site.page(gm.HUB, body_class="thing-page")
    site._gov_hub[gm.HUB] = page
    c = page.cites
    gs = gm.governments(ed)
    n = {k: sum(1 for g in gs if g.kind == k) for k in gm.KIND_LABEL}
    page.add(h("header", {"class": "thing-head hub-head"},
               page.crumb_nav(),
               h("h1", {"class": "thing-title"}, "Governments"),
               h("p", {"class": "thing-facts"},
                 # the count and its wording: civic/governments.py count(), shared with the home page (2026-11-18)
                 "{n} {noun} in ".format(**gm.count(ed)) + f"{ed.county_label} have a page in the guide: "
                 f"{gm.count(ed)['parts']}. Each page has its offices, elections, money and history on tabs.")))
    shapes = load_shapes(ed)
    if shapes is not None:
        m = embedded_map(page, ed, shapes, ("cities", "townships", "schools"), "cities", area=_hub_area(page, ed),
                         label=f"Map of the cities, towns, townships and school corporations of {ed.county_label}. "
                               "Every area is a link to its government's page; the same governments are listed below.",
                         hint="Hover, focus or tap an area to see who runs it here, with links to its page and tabs. "
                              "Select it again, or use the link, to open its page.")
        page.add(T.tab_section("map", "On the map",
                               here_slot("map", "gov-map"),
                               h("div", {"id": "gov-map", "class": "gov-hub-map"}, m),
                               h("p", {"class": "tnote cmap-embed-note"},
                                 "Color shows the type of government only, never party. Townships cover the whole county, "
                                 "so every city and town also lies in a township; school corporations are a separate "
                                 "layer. The county, the libraries and the special units have no area of their own on "
                                 "the map: they are in the list. ",
                                 h("a", {"href": page.rel("map/index.html")}, "The full map, with how areas voted"),
                                 ".", c.cite_compact("MAP-001;MAP-002;MAP-003;MAP-004"))))
    groups = []
    for gid_, label in gm.GROUPS.items():
        rows = []
        for g in [x for x in gs if x.group == gid_]:
            attrs = {"class": "gov-hub-row"}
            if g.kind != "county":
                attrs["id"] = g.gid
            if g.unit_id:
                attrs.update(here_attrs(ed, g.unit_id))
            rows.append(h("li", attrs,
                          h("a", {"class": "gov-hub-name", "href": gm.href(page, g.gid)}, g.name),
                          h("span", {"class": "gov-hub-line"}, _row_line(ed, g))))
        if not rows:
            continue
        note = None
        if gid_ == "county":
            note = h("p", {"class": "tnote"}, "The county's page has the courts and the county's appointed boards. ",
                     h("a", {"href": page.rel("state/index.html")}, "State government")
                     if "state/index.html" in page.site.by_path else None,
                     " and " if "state/your-legislators/index.html" in page.site.by_path else None,
                     h("a", {"href": page.rel("state/your-legislators/index.html")}, "your state legislators")
                     if "state/your-legislators/index.html" in page.site.by_path else None, ".")
        elif gid_ == "schools":
            note = h("p", {"class": "tnote"}, "Indiana's rules for school boards (party labels on the ballot from 2026, "
                                              "ballot order, vacancies) are on each corporation's page.")
        elif gid_ == "special":
            note = h("p", {"class": "tnote"}, "Units with figures in the state's money files. Units named only there "
                                              "(not yet in the guide's list of governments) have money figures only.")
        groups.append(h("section", {"class": "tsec gov-hub-group", "id": gid_, "aria-labelledby": f"{gid_}-h"},
                        h("h2", {"class": "tsec-h", "id": f"{gid_}-h"}, label),
                        h("ul", {"class": "gov-hub-list"}, rows), note))
    page.add(h("div", {"class": "gov-hub-groups", "id": "list"}, groups))
    also = [("offices/index.html", "Offices: every elected office and who holds it"),
            ("your-governments/index.html", "Your place: the governments that cover your address"),
            ("officeholders/index.html", "Who holds office now"),
            ("who-handles-this/index.html", "Who handles this? Services and the government responsible"),
            ("map/index.html", "Map: who governs where, and how areas voted")]
    page.add(T.tab_section("also", "Also", h("ul", {"class": "gov-hub-also"},
                                             [h("li", None, h("a", {"href": page.rel(p)}, t)) for p, t in also
                                              if p in page.site.by_path])))
    page.add(h("p", {"class": "tnote"}, "Governments from the guide's list of units; libraries and special units from "
                                        "the state's money files.", c.cite_compact(P.union(
                                            [ed.units[g.unit_id] for g in gs if g.unit_id]))))
    page.finish(gaps=ed.gaps(files=["gaps_gov", "gaps_community_people"],
                             pattern=r"Town officeholders|Indian Village|place-to-township|Township trustees and boards before"))
    return page


# =========================================================================== registration

def _ids_all_editions() -> list[str]:
    """Every possible government id in every edition (units.csv ids, money-file ids): build.py only builds the ones in
    the edition's sitemap."""
    import csv
    root = Path(__file__).resolve().parents[3] / "data" / "editions"
    ids: list[str] = []
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        for name, col in (("units.csv", "unit_id"), ("budgets.csv", "unit_id"), ("debt.csv", "unit_id"),
                          ("tax_rates.csv", "unit_id"), ("budget_breakdowns.csv", "unit_id"),
                          ("spending_breakdowns.csv", "unit_id"), ("assessed_values.csv", "unit_id")):
            f = d / name
            if not f.is_file():
                continue
            with open(f, encoding="utf-8-sig", newline="") as fh:
                for r in csv.DictReader(fh):
                    v = (r.get(col) or "").strip()
                    if v and v not in ids:
                        ids.append(v)
    return ids


PAGES = {gm.HUB: build_hub}
for _gid in _ids_all_editions():
    for _k in T.TAB_ORDER:
        PAGES[gm.path(_gid, _k)] = partial(build_gov, _gid, tab=_k)
