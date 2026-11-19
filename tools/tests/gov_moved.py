"""Test helper (phase 6 step 3, 2026-11-16): follow an old link through the #moved-anchors maps the way
static/js/moved.js does, over built pages held in memory. Used by test_phase6_governments.py and by the older tests
whose pages (places/<id>/, county/, places/, schools/) became forwarding pages.

``follow(html, ids, page, anchor)`` returns (page, id) where the reader lands, or None when no map sends the id on.
``html`` {site path: page source}; ``ids`` {site path: set of ids}. A page with "to" always forwards (an "a" entry,
then the first matching "p" prefix, then "to" keeping the id); a page without it keeps an id it has, else uses "a",
then "p"."""
from __future__ import annotations

import json
import posixpath
import re

MOVED_RE = re.compile(r'<script type="application/json" id="moved-anchors">(.*?)</script>', re.S)


def join(frm: str, rel: str) -> tuple[str, str]:
    path, _, frag = rel.partition("#")
    if not path:
        return frm, frag
    return posixpath.normpath(posixpath.join(posixpath.dirname(frm), path)), frag


def moved_map(src: str) -> dict | None:
    m = MOVED_RE.search(src or "")
    return json.loads(m.group(1)) if m else None


def follow(html: dict, ids: dict, page: str, anchor: str, hops: int = 0):
    if hops > 3 or page not in html:
        return None
    m = moved_map(html[page])
    to = m.get("to") if m else None
    if not to and anchor in ids[page]:
        return page, anchor
    dest = ""
    if m:
        dest = m.get("a", {}).get(anchor, "")
        if not dest:
            dest = next((d for pre, d in m.get("p", {}).items() if pre and anchor.startswith(pre)), "")
        dest = dest or to or ""
    if not dest:
        return None
    np, frag = join(page, dest)
    return follow(html, ids, np, frag or anchor, hops + 1)


def lands(html: dict, ids: dict, page: str, anchor: str) -> bool:
    r = follow(html, ids, page, anchor)
    return bool(r) and r[1] in ids.get(r[0], set())
