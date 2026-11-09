"""Show one: map-click (or list) navigation that keeps one area's detail open and collapses the others.

    one_fold(key, name, summary, body, ...)        -> <details data-one=key> (a collapsible item for one area)
    one_section(sid, num, title, key, digest, ...)  -> a page <section> whose body is one area's collapsible item
    one_bar(noun, plural, hint)                    -> the state line + Show all / Collapse all buttons (JS only)
    one_scope(attrs, empty)                        -> attrs for a container that says when the chosen area has nothing in it
    one_row(key)                                   -> attrs for a table row (or any non-<details> block) of one area

How it works (static/js/pick_one.js):
- Every area's detail is a ``<details data-one="<key>" data-fold="one" open>``. The HTML ships them open, so with
  JavaScript off every area's full content is on the page. static/js/folds.js closes every data-fold on load
  (unless the address points inside one) and opens one when a link targets something inside it.
- Choosing an area (a map shape, a list link, the table of contents, an old #anchor in the address, back/forward)
  opens every item with that key, closes the items of every other key, and leaves everything else alone. Nothing is
  removed; a reader can still open any other area by its summary line.
- Rows or blocks marked ``data-one="<key>"`` that are not <details> (e.g. the rows of an all-units table) are
  hidden while some areas are open and theirs is not; they all show when no area or every area is open. A table
  whose rows are hidden this way announces it, so Copy CSV copies only the rows shown (static/app.js).
- An element whose id is the area's anchor but that is not inside its <details> (a <section id="sbcsc"> around it)
  carries ``data-one-for="<key>"`` so the anchor still chooses the area.
Text is inserted with textContent only; keys are the ids already used on the page (unit ids, office ids).
"""
from __future__ import annotations

from .html import Markup, h


def one_fold(key: str, name: str, summary, body, *, item_id: str | None = None, cls: str = "",
             attrs: dict | None = None, summary_cls: str = "") -> Markup:
    """One area's collapsible item. ``summary`` is the always-visible line (a heading and a short digest);
    ``body`` is everything else. ``item_id`` (optional) is the id of the <details> itself."""
    a = {"class": "fold-details one-fold" + (f" {cls}" if cls else ""), "open": True, "data-fold": "one",
         "data-one": key, "data-one-name": name, "id": item_id}
    a.update(attrs or {})
    return h("details", a,
             h("summary", {"class": "fold-summary one-summary" + (f" {summary_cls}" if summary_cls else "")}, summary,
               h("span", {"class": "fold-toggle", "aria-hidden": "true"})),
             h("div", {"class": "fold-body one-body"}, body))


def one_summary(heading_tag: str, heading, digest=None, heading_id: str | None = None, kicker: str | None = None) -> list:
    """The usual summary line: optional kicker, a heading, then a muted digest that wraps under it on phones."""
    return [h("span", {"class": "kicker"}, kicker) if kicker else None,
            h(heading_tag, {"class": "one-h", "id": heading_id}, heading),
            h("span", {"class": "one-digest"}, digest) if digest else None]


def one_section(sid: str, num: int | None, title: str, key: str, digest, *children, scope_badge=None) -> Markup:
    """A page section (``<section class="block" id=sid>``) that is one area's item: its h2 and digest are the summary,
    the rest of the section collapses. The section keeps its id, so old #sid links and the table of contents still
    land on it (data-one-for makes them choose the area too)."""
    return h("section", {"class": "block one-section", "id": sid, "aria-labelledby": f"{sid}-h", "data-one-for": key},
             one_fold(key, title,
                      [h("span", {"class": "one-headrow"},
                         h("span", {"class": "kicker"}, f"§ {num:02d}") if num is not None else None,
                         h("h2", {"id": f"{sid}-h", "class": "one-h"}, title)),
                       h("span", {"class": "one-digest"}, digest) if digest else None],
                      [h("p", {"class": "one-scope-badge"}, scope_badge) if scope_badge else None, children],
                      summary_cls="block-head"))


def one_bar(noun: str, plural: str, hint: str, label: str | None = None) -> Markup:
    """The JS-only state line: what is open now, with Show all and Collapse all. Hidden without JavaScript (then every
    item is open anyway). ``hint`` is the line shown while nothing is chosen."""
    return h("div", {"class": "one-bar", "data-one-bar": True, "data-one-noun": noun, "data-one-plural": plural,
                     "data-one-hint": hint, "role": "group", "aria-label": label or f"Which {plural} are shown",
                     "hidden": True},
             h("p", {"class": "one-state", "data-one-state": True, "aria-live": "polite"}, hint),
             h("span", {"class": "one-btns"},
               h("button", {"type": "button", "class": "btn btn-small", "data-one-all": True}, f"Show all {plural}"),
               h("button", {"type": "button", "class": "btn btn-small", "data-one-none": True}, "Collapse all")))


def one_scope(empty: str) -> dict:
    """Attributes for a container (a section) whose chosen area may have nothing in it. ``empty`` is the sentence
    shown then; ``{name}`` is replaced with the chosen area's name. Put ``one_empty()`` inside the container."""
    return {"data-one-scope": True, "data-one-empty-text": empty}


def one_empty() -> Markup:
    return h("p", {"class": "one-empty muted", "data-one-empty": True, "hidden": True, "role": "status"})


def one_row(key: str) -> dict:
    """Attributes for a row (or any block that is not a <details>) belonging to one area."""
    return {"data-one": key}


def one_wrap_attrs() -> dict:
    """Attributes for a <details> that holds rows of every area (an all-units table): opened when an area with rows
    in it is chosen, and by Show all; closed by Collapse all."""
    return {"data-one-wrap": True}


# ------------------------------------------------------------------ added 2026-11-09 (Wave C batch 7)

def one_wrap_see_all(fold_id: str, label: str, body, hint: str | None = "Copy CSV") -> Markup:
    """components.see_all_fold's markup (a "See all N rows" fold that ships open) that is also a one_wrap_attrs
    wrapper: choosing an area that has rows inside opens it (only that area's rows show, and Copy CSV copies them);
    Show all opens it, Collapse all closes it. Used for the budgets debt table. tools/tests/test_wave_c_batch7.py
    checks the markup stays the same as see_all_fold's apart from data-one-wrap."""
    return h("details", {"class": "fold-details see-all", "id": fold_id, "open": True, "data-fold": "see-all",
                         **one_wrap_attrs()},
             h("summary", {"class": "fold-summary see-all-summary"},
               h("span", {"class": "see-all-label"}, label),
               h("span", {"class": "see-all-hint"}, hint) if hint else None,
               h("span", {"class": "fold-toggle", "aria-hidden": "true"})),
             h("div", {"class": "fold-body see-all-body"}, body))


def one_chips(label: str, chips: list[tuple[str, str]], note=None, cls: str = "") -> Markup | None:
    """A row of chip links that choose an area, for areas a map cannot draw (units with no boundary). ``chips`` is
    [(href '#anchor', text)]; every href lands on an element of that area's item, so it works without JavaScript
    (it is a plain in-page link) and with it (pick_one.js chooses the area on click)."""
    if not chips:
        return None
    return h("div", {"class": "one-chips" + (f" {cls}" if cls else "")},
             h("p", {"class": "one-chips-h"}, label),
             h("ul", {"class": "one-chips-list"},
               [h("li", None, h("a", {"class": "one-chip", "href": href}, text)) for href, text in chips]),
             h("p", {"class": "one-chips-note muted"}, note) if note else None)
