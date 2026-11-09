"""Build-time search index for the header search box (static/js/search.js).

Written by Site.write() to assets/search-index.json after every page has been rendered, so the
index only ever points at pages and anchors that exist in this build. Contents:

* every page (title) and its section headings (h2 with an id, linked to the section),
* every place: the county, each city, town, township and school corporation,
* every office in offices.csv (linked to its officeholder card when a page has one),
* every current officeholder, with the party tag as display text only,
* the notable people cards on history/people/.

Matching and ranking happen in the browser. Party tags are stored in their own field and are not
searchable, so typing a party letter never filters people, and ranking never depends on party.

Format: {"v": 1, "types": [...], "items": [[type_index, label, sub, href, tag], ...]} with every
href relative to the edition root.
"""
from __future__ import annotations

import html as _html
import json
import re

from .components import name_party_text, term_party

TYPES = ["Place", "Office", "Officeholder", "Person", "Page", "Section"]
T_PLACE, T_OFFICE, T_HOLDER, T_PERSON, T_PAGE, T_SECTION = range(6)

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

    def add(t, label, sub, href, tag=""):
        key = (t, label, sub, href)
        if not label or key in seen:
            return
        seen.add(key)
        items.append([t, label, sub, href, tag] if tag else [t, label, sub, href])

    ids = {path: set(_ID_RE.findall(src)) for path, src in rendered.items()}

    # ---- pages and their sections
    for path, page in site.pages.items():
        group = page.entry.group if page.entry is not None and getattr(page.entry, "group", "") else ""
        add(T_PAGE, page.title, group or "Page", path)
        src = rendered[path]
        for hid, inner in _H2_RE.findall(src):
            sid = hid[:-2] if hid.endswith("-h") and hid[:-2] in ids[path] else hid
            if sid in SKIP_SECTIONS or sid.startswith("gaps") or sid.startswith("sources"):
                continue
            title = _text(inner)
            if title and title != page.title:
                add(T_SECTION, title, page.title, f"{path}#{sid}")

    # ---- places
    kind_label = {"county": "County", "city": "City", "town": "Town", "township": "Township",
                  "school_corporation": "School corporation"}
    unit_href: dict[str, str] = {}
    for u in ed.tables["units"]:
        t, uid = u["unit_type"], u["unit_id"]
        if t == "county":
            href = "county/index.html"
        elif t in ("city", "town", "township"):
            href = f"places/{uid}/index.html"
        elif t == "school_corporation":
            href = f"schools/index.html#{uid}" if uid in ids.get("schools/index.html", set()) else "schools/index.html"
        else:
            continue
        if href.split("#")[0] not in rendered:
            continue
        unit_href[uid] = href
        add(T_PLACE, u["name"], kind_label[t], href)

    # ---- offices and current officeholders
    def office_href(o) -> str | None:
        anchor = f"office-{o['office_id']}"
        home = unit_href.get(o["unit_id"], "")
        home_page = home.split("#")[0]
        if home_page and anchor in ids.get(home_page, set()):
            return f"{home_page}#{anchor}"
        for path in sorted(rendered):
            if anchor in ids[path]:
                return f"{path}#{anchor}"
        return home or None

    for o in ed.tables["offices"]:
        href = office_href(o)
        if not href:
            continue
        unit = ed.units.get(o["unit_id"], {})
        uname = unit.get("name", "")
        add(T_OFFICE, o["title"], uname, href)
        for term in ed.current_terms(o["office_id"]):
            name = (term.get("person") or "").strip()
            if not name:
                continue
            party = term_party(term)
            tag = name_party_text(name, party, term.get("confidence") if party else None)[len(name):].strip()
            short = re.sub(r"^(City|Town) of ", "", uname)
            sub = o["title"] if not uname or short.lower() in o["title"].lower() else f"{o['title']}, {uname}"
            add(T_HOLDER, name, sub, href, tag)

    # ---- notable people (history/people/)
    ppath = "history/people/index.html"
    if ppath in rendered:
        for pid, inner in _PERSON_RE.findall(rendered[ppath]):
            tags = [_text(t) for t in _ABBR_RE.findall(inner)]
            name = _text(_ABBR_RE.sub("", inner))
            if name:
                add(T_PERSON, name, "Notable people", f"{ppath}#{pid}", " ".join(t for t in tags if t))

    order = {T_PLACE: 0, T_OFFICE: 1, T_HOLDER: 2, T_PERSON: 3, T_PAGE: 4, T_SECTION: 5}
    items.sort(key=lambda r: (order[r[0]], r[1].lower(), r[2].lower()))
    return {"v": 1, "types": TYPES, "items": items}


def write_index(site, rendered: dict[str, str]) -> int:
    """Write assets/search-index.json; returns its size in bytes."""
    payload = build_index(site, rendered)
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    dest = site.out / "assets" / "search-index.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8", newline="\n")
    return len(text.encode("utf-8"))
