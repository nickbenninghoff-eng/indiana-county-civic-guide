"""Build-time search index for the header search box (static/js/search.js).

Written by Site.write() to assets/search-index.json after every page has been rendered, so the
index only ever points at pages and anchors that exist in this build. Contents:

* every page (title) and its section headings (h2 with an id, linked to the section),
* every place: the county, each city, town, township and school corporation,
* every office in offices.csv, linked to its office page (offices/<id>/; before phase 6 the officeholder card),
* every tab of every office page ("Mayor of South Bend › Money"), with plain keywords for the tab (TAB_KEYWORDS:
  "money", "finance", "campaign", "spent"... find the Money tab; "results", "primary", "votes"... the Elections tab;
  "history", "past", "former" the History tab), so "mayor money" or "sheriff results" lands on the right tab,
* every current officeholder, with the party tag as display text only (linked to the office page),
* every person page (civic/people.py) and its tabs, with the other spellings of the name as keywords.

Matching and ranking happen in the browser (static/js/search.js). Party tags are stored in their own field and are
not searchable, so typing a party letter never filters people, and ranking never depends on party.

Format: {"v": 2, "types": [...], "items": [[type_index, label, sub, href, tag, keywords], ...]} with every href
relative to the edition root; ``tag`` and ``keywords`` are left off when empty. Keywords (a space-separated string)
are matched like the label but never shown. Items come in a fixed order the browser keeps for ties: by kind, then
offices and their tabs in offices.csv order, everything else alphabetically.
"""
from __future__ import annotations

import html as _html
import json
import re

from .components import name_party_text, term_party
from .data import fmt_date

TYPES = ["Place", "Office", "Officeholder", "Person", "Page", "Section", "Office", "Election", "Election", "Government",
         "Person"]
T_PLACE, T_OFFICE, T_HOLDER, T_PERSON, T_PAGE, T_SECTION, T_TAB = range(7)
# added 2026-11-16 (phase 6 step 4): an election page (elections/<id>/) and its tabs ("2024 general election › Map")
T_ELECTION, T_ETAB = 7, 8
# added 2026-11-16 (phase 6 step 3): a government page's tab ("City of South Bend › Money")
T_GTAB = 9
# added 2026-11-16 (person pages): a person page's tab ("James Mueller › Money")
T_PTAB = 10

# Plain words that find an office's tab (phase 6 step 1). Each also matches as a prefix ("finance" finds "financ").
TAB_KEYWORDS = {
    "elections": "elections election results result primary primaries votes vote margin margins general race races "
                 "winner won ballot",
    "money": "money finance financing campaign campaigns spent spending raised donations donors contributions "
             "fundraising cash",
    "history": "history past former previous holders timeline",
    "sources": "sources source citations gaps",
}

# Plain words that find an election page and its tabs (phase 6 step 4)
ELECTION_KEYWORDS = "election elections results result turnout ballot ballots vote votes voters"
ELECTION_TAB_KEYWORDS = {
    "contests": "contests contest results result winners winner won races race candidates margin margins",
    "map": "map maps precinct precincts areas area township townships voted",
    "sources": "sources source citations gaps",
}

# Plain words that find a government's tab (phase 6 step 3, 2026-11-16): "south bend budget" or "penn township
# debt" lands on the Money tab, "mishawaka results" on Elections, "county party control" on History.
GOV_TAB_KEYWORDS = {
    "elections": TAB_KEYWORDS["elections"],
    "money": "money budget budgets spending spent finance finances revenue income taxes tax levy debt bonds audit "
             "audits assessed",
    "history": "history past former previous holders timeline party control",
    "sources": TAB_KEYWORDS["sources"],
}

# Plain words and other names that find a page (phase 6 step 5, 2026-11-18): the money pages. Keywords are matched
# like the label but never shown; an alias is one more "Page" item with that label, so a reader's own words ("campaign
# finance", "budgets", "property tax") rank the page first.
PAGE_KEYWORDS = {
    "money/index.html": "money finance finances budget budgets spending campaign campaigns taxes",
    "money/campaigns/index.html": "campaign campaigns money finance financing contributions donations donors raised "
                                  "spent spending fundraising candidates office offices mayor council",
    "money/campaigns/by-election/index.html": "campaign money finance election elections cycle primary primaries "
                                              "general races",
    "money/campaigns/by-candidate/index.html": "campaign money finance candidate candidates committee committees "
                                               "people person",
    "money/campaigns/by-place/index.html": "campaign money finance map place places area areas",
    "money/campaigns/other-committees/index.html": "campaign money committees party pac pacs issue",
    "money/campaigns/all-filings/index.html": "campaign money filings reports cfa-4 large contributions",
    "money/budgets/index.html": "budget budgets compare comparison per resident debt tax rate rates levy spending",
    "money/your-tax-bill/index.html": "tax bill taxes property rate rates levy assessed",
    "money/what-is-a-budget/index.html": "budget budgets general fund all funds what counts",
}
PAGE_ALIASES = {
    "money/campaigns/index.html": ["Campaign finance", "Campaign money by office"],
    "money/budgets/index.html": ["Budgets", "Budgets compared"],
    "money/your-tax-bill/index.html": ["Property tax bill"],
}

SKIP_SECTIONS = {"sources", "gaps", "glance"}
_ID_RE = re.compile(r'\sid="([^"]+)"')
_H2_RE = re.compile(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>', re.S)
_PERSON_RE = re.compile(r'id="(person-[^"]+)".*?<h3[^>]*>(.*?)</h3>', re.S)
_TAG_RE = re.compile(r"<[^>]+>")
_SUP_RE = re.compile(r"<sup\b.*?</sup>", re.S)          # citation numbers
_ABBR_RE = re.compile(r"<abbr\b[^>]*>(.*?)</abbr>", re.S)  # party tag from name_with_party


def _text(fragment: str) -> str:
    fragment = _SUP_RE.sub("", fragment)
    return re.sub(r"\s+", " ", _html.unescape(_TAG_RE.sub("", fragment))).strip()


def build_index(site, rendered: dict[str, str]) -> dict:
    ed = site.ed
    items: list[list] = []
    seen: set = set()
    ranks: dict = {}

    def add(t, label, sub, href, tag="", kw="", rank=None):
        key = (t, label, sub, href)
        if not label or key in seen:
            return
        seen.add(key)
        row = [t, label, sub, href, tag, kw] if kw else ([t, label, sub, href, tag] if tag else [t, label, sub, href])
        items.append(row)
        ranks[id(row)] = rank

    ids = {path: set(_ID_RE.findall(src)) for path, src in rendered.items()}

    # ---- pages and their sections
    for path, page in site.pages.items():
        if page.entry is not None and getattr(page.entry, "thing", ""):
            continue   # a tabbed thing's pages are listed below, with their tab keywords
        if page.entry is not None and getattr(page.entry, "moved_to", ""):
            continue   # a forwarding page (its content is on the page it names)
        group = page.entry.group if page.entry is not None and getattr(page.entry, "group", "") else ""
        add(T_PAGE, page.title, group or "Page", path, kw=PAGE_KEYWORDS.get(path, ""))
        for alias in PAGE_ALIASES.get(path, []):
            add(T_PAGE, alias, page.title, path, kw=PAGE_KEYWORDS.get(path, ""))
        src = rendered[path]
        for hid, inner in _H2_RE.findall(src):
            sid = hid[:-2] if hid.endswith("-h") and hid[:-2] in ids[path] else hid
            if sid in SKIP_SECTIONS or sid.startswith("gaps") or sid.startswith("sources"):
                continue
            title = _text(inner)
            if title and title != page.title:
                add(T_SECTION, title, page.title, f"{path}#{sid}")

    # ---- places: every government page (phase 6 step 3, civic/governments.py; before it the place pages, county/ and
    # schools/#<id>), and each of its tabs with plain keywords (GOV_TAB_KEYWORDS)
    from . import governments as gm
    from .tabs import TAB_LABELS as _TL
    moved = gm.moved_pages(ed)
    unit_href: dict[str, str] = {}
    for g in gm.governments(ed):
        href = gm.path(g.gid)
        if href not in rendered:
            continue
        if g.unit_id:
            unit_href[g.unit_id] = href
        add(T_PLACE, g.name, gm.KIND_LABEL[g.kind], href)
        for key in gm.gov_tabs(ed, g.gid):
            tp = gm.path(g.gid, key)
            if key == "overview" or tp not in rendered:
                continue
            add(T_GTAB, f"{g.name} › {_TL[key]}", gm.KIND_LABEL[g.kind], tp, kw=GOV_TAB_KEYWORDS.get(key, ""))

    # ---- offices and current officeholders
    def office_href(o) -> str | None:
        anchor = f"office-{o['office_id']}"
        home = unit_href.get(o["unit_id"], "")
        if not home:   # the county courts' offices are on the county's government page (phase 6 step 3)
            hg = gm.gov_for_unit(ed, o["unit_id"])
            home = unit_href.get(hg.unit_id, "") if hg else ""
        home_page = home.split("#")[0]
        if home_page and anchor in ids.get(home_page, set()):
            return f"{home_page}#{anchor}"
        for path in sorted(rendered):
            if path in moved:
                continue   # a forwarding page lists the old ids only to send readers on
            if anchor in ids[path]:
                return f"{path}#{anchor}"
        return home or None

    from . import offices as om
    from .tabs import TAB_LABELS
    for oi, o in enumerate(ed.tables["offices"]):
        oid = o["office_id"]
        own = om.path(oid)
        href = own if own in rendered else office_href(o)
        if not href:
            continue
        unit = ed.units.get(o["unit_id"], {})
        uname = om.unit_name(ed, o["unit_id"]) if unit else ""
        add(T_OFFICE, o["title"], uname, href, rank=(oi, 0))
        if own in rendered:
            for ti, key in enumerate(om.office_tabs(ed, oid)):
                tp = om.path(oid, key)
                if key == "overview" or tp not in rendered:
                    continue
                add(T_TAB, f"{o['title']} › {TAB_LABELS[key]}", uname, tp, kw=TAB_KEYWORDS.get(key, ""),
                    rank=(oi, ti))
        for term in ed.current_terms(oid):
            name = (term.get("person") or "").strip()
            if not name:
                continue
            party = term_party(term)
            tag = name_party_text(name, party, term.get("confidence") if party else None)[len(name):].strip()
            short = re.sub(r"^(City|Town) of ", "", uname)
            sub = o["title"] if not uname or short.lower() in o["title"].lower() else f"{o['title']}, {uname}"
            add(T_HOLDER, name, sub, href, tag)

    # ---- elections (phase 6 step 4): each election page, newest first, then its tabs
    from . import election_pages as ep
    for ei, e in enumerate(ep.ordered(ed, newest_first=True)):
        eid = e["election_id"]
        own = ep.path(eid)
        if own not in rendered:
            continue
        n = len(ep.contests(ed, eid))
        when = e.get("date") or ""
        sub = (fmt_date(when, long=True) if when.count("-") == 2 else when) + (f" · {n} contest{'s' if n != 1 else ''}"
                                                                               if n else "")
        label = ep.title(e)
        label = label[:1].upper() + label[1:]
        add(T_ELECTION, label, sub, own, kw=ELECTION_KEYWORDS, rank=(ei, 0))
        for ti, key in enumerate(ep.election_tabs(ed, eid)):
            tp = ep.path(eid, key)
            if key == "overview" or tp not in rendered:
                continue
            add(T_ETAB, f"{label} › {TAB_LABELS[key]}", sub, tp, kw=ELECTION_TAB_KEYWORDS.get(key, ""), rank=(ei, ti))

    # ---- people (2026-11-16, civic/people.py): every person page, alphabetical, and each of its tabs with the office
    # tabs' plain keywords ("mueller money" -> "James Mueller › Money"). The other spellings of the name in the records
    # are keywords, so "Bobby K" finds Bobby K. Kruszynski Jr. (Before, the notable-people cards on history/people/.)
    from . import people as pm
    for p in pm.paged(ed):
        own = pm.path(p.pid)
        if own not in rendered:
            continue
        alt = " ".join(n for n in p.names if n != p.name)
        add(T_PERSON, p.name, pm.one_line(ed, p), own, kw=alt)
        for key in pm.person_tabs(ed, p.pid):
            tp = pm.path(p.pid, key)
            if key == "overview" or tp not in rendered:
                continue
            add(T_PTAB, f"{p.name} › {TAB_LABELS[key]}", "Person", tp, kw=(TAB_KEYWORDS.get(key, "") + " " + alt).strip())

    order = {T_PLACE: 0, T_OFFICE: 1, T_TAB: 2, T_HOLDER: 3, T_PERSON: 4, T_PAGE: 5, T_SECTION: 6, T_ELECTION: 7,
             T_ETAB: 8, T_GTAB: 9, T_PTAB: 10}

    def sort_key(r):
        rk = ranks.get(id(r))
        # offices and their tabs keep offices.csv order (the county's own listing order: county, courts, cities...);
        # everything else is alphabetical
        return (order[r[0]], rk if rk is not None else (10 ** 6, 0), r[1].lower(), r[2].lower())
    items.sort(key=sort_key)
    return {"v": 2, "types": TYPES, "items": items}


def write_index(site, rendered: dict[str, str]) -> int:
    """Write assets/search-index.json; returns its size in bytes."""
    payload = build_index(site, rendered)
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    dest = site.out / "assets" / "search-index.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8", newline="\n")
    return len(text.encode("utf-8"))
