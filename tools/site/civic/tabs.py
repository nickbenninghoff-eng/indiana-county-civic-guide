"""Tab template: "one thing, several short pages" (phase 6 step 1, 2026-11-16).

A *thing* (an office now; a government, an election or a person in later steps) has one home page and up to four
more tab pages, each a real URL so it works with JavaScript off, can be linked and is searchable:

    <base>index.html             Overview   (always)
    <base>elections/index.html   Elections
    <base>money/index.html       Money
    <base>history/index.html     History
    <base>sources/index.html     Sources    (citations and gaps for the whole thing; always last)

``base`` is the thing's folder ("offices/south-bend-mayor/"). A tab with nothing to show is neither generated nor
shown: the caller decides the keys from its data model, and the SAME keys go to the sitemap (``tab_entries``) and to
the builder (``build_tabs``), so a tab bar never links to a page that is not built.

Every tab page carries the same shared header: the breadcrumb, the title (display face, sentence case), a one-line
facts strip and the tab bar (``<nav class="tabs">`` with ``aria-current="page"``; it scrolls inside itself at phone
width, never the page). Citation numbers are shared across the thing's tabs: footnote 3 on the Money tab is item 3
on the Sources tab, and every footnote link points there. Only the Sources tab lists sources and gaps.

API (later steps use it unchanged):

    keys = ["overview", "elections", "money", "sources"]          # in TAB_ORDER, from the caller's model
    entries = tab_entries(base, title, description, keys, group="Offices", crumb=[...])   # sitemap.Entry objects
    head = Head(kind="Office", title="Mayor of South Bend", facts=["City of South Bend", "1 seat", ...])
    pages = build_tabs(site, base, keys, head, {"overview": fn, "elections": fn, ...})
        # fn(page) adds the tab's body; "sources" gets fn(page, gaps) via sources_tab(...) helpers below

Status marks (``status_mark``) are the small one-glyph form of components.status_badge for these pages: the wording
is in the mark's title and accessible name, and the Sources tab carries the key (``marks_key``).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .components import FIGURE_MARKS, STATUS, Citations, mark_symbol, status_badge
from .html import Markup, h, join

# "contests" and "map" added 2026-11-16 (phase 6 step 4): an election page's Contests and Map tabs
# (civic/election_pages.py). Office pages never use them, so their tabs and order are unchanged.
TAB_ORDER = ("overview", "contests", "map", "elections", "money", "history", "sources")
TAB_LABELS = {"overview": "Overview", "contests": "Contests", "map": "Map", "elections": "Elections", "money": "Money",
              "history": "History", "sources": "Sources"}


def tab_path(base: str, key: str) -> str:
    """Site path of one tab: the overview is the thing's own index.html."""
    if key not in TAB_LABELS:
        raise KeyError(f"unknown tab {key!r}")
    base = base if base.endswith("/") else base + "/"
    return f"{base}index.html" if key == "overview" else f"{base}{key}/index.html"


def ordered(keys) -> list[str]:
    """Keys in TAB_ORDER, with the overview always first and the sources tab always last; unknown keys raise."""
    keys = set(keys)
    bad = keys - set(TAB_ORDER)
    if bad:
        raise KeyError(f"unknown tab(s) {sorted(bad)}")
    return [k for k in TAB_ORDER if k in keys or k == "overview"]


@dataclass
class Head:
    """The header every tab of a thing repeats. ``facts`` are short strings or Markup (one line, joined by ' · ');
    ``kind`` names the kind of thing for the search list and the eyebrow ("Office")."""
    kind: str
    title: str
    facts: list = field(default_factory=list)
    note: Markup | str | None = None


def tab_entries(base: str, title: str, description: str, keys, *, group: str = "", scope: str = "county",
                crumb: list | None = None, tab_descriptions: dict | None = None) -> list:
    """Sitemap entries for one thing's tabs (overview first). Tab pages are titled "<title>: <Tab>". ``crumb`` is the
    breadcrumb [(label, site path or None)] every tab shows (sitemap.crumbs reads it)."""
    from .sitemap import Entry
    out = []
    for k in ordered(keys):
        t = title if k == "overview" else f"{title}: {TAB_LABELS[k]}"
        d = (tab_descriptions or {}).get(k) or description
        out.append(Entry(tab_path(base, k), t, TAB_LABELS[k] if k != "overview" else title, d, scope, group, [],
                         crumb=list(crumb or []), tab=k, thing=base))
    return out


def tab_bar(page, base: str, keys, current: str, label: str) -> Markup:
    """The tab bar: a nav of real links; the current tab is aria-current="page" (and not a link to itself, so a
    keyboard reader does not land on a link that goes nowhere). Scrolls inside itself when it is wider than the
    screen."""
    items = []
    for k in ordered(keys):
        if k == current:
            items.append(h("li", {"class": "tab is-current"},
                           h("a", {"class": "tab-link", "href": page.rel(tab_path(base, k)), "aria-current": "page"},
                             TAB_LABELS[k])))
        else:
            items.append(h("li", {"class": "tab"},
                           h("a", {"class": "tab-link", "href": page.rel(tab_path(base, k))}, TAB_LABELS[k])))
    return h("nav", {"class": "tabs", "aria-label": label, "id": "tabs"},
             h("ul", {"class": "tab-list"}, items))


def thing_header(page, head: Head, base: str, keys, current: str) -> Markup:
    """Breadcrumb, title, facts strip and tab bar, identical on every tab except the current-tab mark."""
    facts = [f for f in head.facts if f not in (None, "")]
    sep = h("span", {"class": "facts-sep", "aria-hidden": "true"}, " · ")
    return h("header", {"class": "thing-head"},
             page.crumb_nav(),
             h("h1", {"class": "thing-title"}, head.title,
               h("span", {"class": "visually-hidden"}, f": {TAB_LABELS[current]}") if current != "overview" else None),
             h("p", {"class": "thing-facts"}, join([h("span", {"class": "thing-fact"}, f) for f in facts], sep))
             if facts else None,
             h("p", {"class": "thing-note"}, head.note) if head.note else None,
             tab_bar(page, base, keys, current, f"{head.title}: sections"))


def build_tabs(site, base: str, keys, head: Head, render: dict[str, Callable]) -> dict:
    """Build every tab page of one thing, in TAB_ORDER with the Sources tab last, sharing one citation numbering.

    ``render[key](page)`` adds the tab's body (the header and tab bar are already on the page). The Sources tab's
    renderer runs after every other tab has cited, so its list is complete; it should call ``sources_body``.
    Returns {key: Page}. Every key must be a sitemap entry (``tab_entries``)."""
    keys = ordered(keys)
    missing = [k for k in keys if k not in render]
    if missing:
        raise KeyError(f"build_tabs: no renderer for tab(s) {missing}")
    shared = Citations(site.ed)          # one numbering for the whole thing
    pages = {}
    src_path = tab_path(base, "sources") if "sources" in keys else None
    for k in keys:
        page = site.page(tab_path(base, k), body_class="thing-page")
        page.cites.order = shared.order
        page.cites.unknown = shared.unknown
        if src_path and k != "sources":
            page.cites.href_base = page.rel(src_path)
        page.tab = k
        page.add(thing_header(page, head, base, keys, k))
        pages[k] = page
    for k in keys:
        render[k](pages[k])
    return pages


# ------------------------------------------------------------------ small parts the tab bodies share

def tab_section(sid: str, title: str, *children, lead=None) -> Markup:
    """A calm section: a small label and space, no heavy rule (the visual direction for tab pages)."""
    return h("section", {"class": "tsec", "id": sid, "aria-labelledby": f"{sid}-h"},
             h("h2", {"class": "tsec-h", "id": f"{sid}-h"}, title),
             h("p", {"class": "tsec-lead"}, lead) if lead else None, children)


# One mark per status: a shape (CSS) plus, for the two a reader must not miss, a short word.
MARK_WORD = {"unofficial": "Unofficial", "low": "Low confidence", "unverified": "Unverified"}


def status_mark(status: str, page=None, note: str | None = None, sources_href: str | None = None) -> Markup:
    """The status as one small mark beside the figure.

    Changed 2026-11-18 (phase 6, "About these figures"; same signature): this is now components.status_badge, the one
    system for the whole site. An official figure gets no mark; any other status is its symbol, linking to the page's
    "About these figures" note (which links on to the Sources tab), so ``sources_href`` is no longer used."""
    return status_badge(status, page, note)


def marks_key(keys=("official", "unofficial", "computed", "from_scan", "secondary", "single_source", "low")) -> Markup:
    """What the marks mean (on the Sources tab, id="marks"): every symbol of the site, with "no mark" for an official
    figure. Changed 2026-11-18: lists the symbols (components.FIGURE_MARKS), whatever ``keys`` asks for first."""
    rows = []
    if "official" in keys:
        rows.append(h("li", None, h("span", {"class": "fmark-sym fmark-none", "aria-hidden": "true"}, "–"), " ",
                      h("strong", None, "No mark"), ": an official or certified record, complete as far as the guide "
                                                    "knows. This is the normal case."))
    for k in FIGURE_MARKS:
        sym, name, meaning = FIGURE_MARKS[k]
        rows.append(h("li", None, mark_symbol(k), " ", h("strong", None, name), ": ", meaning))
    return h("ul", {"class": "marks-key", "id": "marks"}, rows)


def _gaps_body(rows: list[dict], what: str) -> Markup:
    if not rows:
        return h("p", None, f"No open gaps are recorded for {what}.")
    return h("ul", {"class": "gaps-list"}, [
        h("li", None, h("strong", None, g.get("item", "")),
          h("span", {"class": "gap-why"}, f"Why missing: {g.get('why_missing', '')}") if g.get("why_missing") else None,
          h("span", {"class": "gap-how"}, f"How to fill: {g.get('how_to_fill', '')}") if g.get("how_to_fill") else None)
        for g in rows])


def gaps_list(rows: list[dict], what: str) -> Markup:
    """The gaps as a plain, always-open section (id="gaps")."""
    return tab_section("gaps", f"Gaps ({len(rows)})", _gaps_body(rows, what),
                       lead=f"What the guide looked for about {what} and hasn't found or confirmed yet.")


GAPS_FOLD_FROM = 4     # a Sources tab's gaps list this long or longer sits in a fold


def _fold(fid: str, label: str, count: int | None, body) -> Markup:
    """A fold on a Sources tab: ships open (JavaScript off: everything is on the page); static/js/folds.js closes it
    on load and opens it when a link or the address points inside (#src-<id>, #marks, #gaps)."""
    return h("details", {"class": "fold-details tab-fold", "id": fid, "data-fold": "sources", "open": True},
             h("summary", {"class": "fold-summary"}, h("span", None, label),
               (" ", h("span", {"class": "fold-count"}, f"({count})")) if count is not None else None,
               h("span", {"class": "fold-toggle", "aria-hidden": "true"})),
             body)


def sources_body(page, gaps: list[dict] | None, *, notes: list | None = None, title: str = "") -> list:
    """The Sources tab's body: notes on the figures, the gaps, every source the thing's tabs cite (numbered as the
    footnotes on every tab; ids src-<id>, so every footnote link lands on its row) and what the marks mean.
    Changed 2026-11-18 (maps-cleanup brief, part B item 3: these tabs ran 4 to 8 screens): the sources are grouped by
    kind in folds with their counts (Citations.render_grouped), a long gaps list and the marks key are folds too.
    Every fold ships open and folds.js opens the one a link points into, so every #src-, #gaps and #marks link lands."""
    out = []
    if notes:
        out.append(tab_section("notes", "Notes on these figures", h("ul", {"class": "tnotes"},
                                                                 [h("li", None, n) for n in notes])))
    if gaps is not None:
        what = title or "this"
        if len(gaps) >= GAPS_FOLD_FROM:
            out.append(tab_section("gaps", f"Gaps ({len(gaps)})",
                                   _fold("gaps-fold", "Show every gap", len(gaps), _gaps_body(gaps, what)),
                                   lead=f"What the guide looked for about {what} and hasn't found or confirmed yet."))
        else:
            out.append(gaps_list(gaps, what))
    n = len(page.cites.order)
    out.append(tab_section("sources", f"Sources ({n})", page.cites.render_grouped(),
                           lead=f"Every source cited on the tabs for {title or 'this page'}, numbered as the footnotes "
                                "are" + (", grouped by kind: open a group to see its sources." if n >= page.cites.GROUP_FROM
                                         else ".")))
    out.append(tab_section("marks-sec", "What the marks mean", _fold("marks-fold", "Show every mark", None,
                                                                     marks_key())))
    return out
