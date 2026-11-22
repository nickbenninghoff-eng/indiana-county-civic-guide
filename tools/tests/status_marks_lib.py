"""Reads the status of figures out of built pages (shared by tools/tests/test_status_marks.py and the inventory script).

Added 2026-11-18 (phase 6, "About these figures"): the owner asked for the inline status words and caveats ("Incomplete",
OFFICIAL / COMPUTED / SECONDARY badges, ...) to become one small symbol beside the figure plus one note at the bottom of
the page. This module reads both the old forms and the new ones, so a test can prove nothing was lost:

- ``occurrences(html)``: every (context, kind) pair on a page. The context is the text of the nearest row-like element
  (table row, list item, paragraph, caption, heading) around the status, with every status word, badge and symbol taken
  out, so the same figure has the same context before and after the change.
- ``scoped(html)``: {context: kinds} for every row-like element that sits inside a section whose caption states one
  status for all of it (``data-fscope="secondary"`` on the section; the new system's "say it once" form).
- ``symbols(html)`` / ``note_entries(html)``: the symbol marks on a page and the entries of its "About these figures"
  note, to check that every symbol has its note entry and vice versa.

Pure stdlib (html.parser); it reads only the page's <main>.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

# Exceptions a reader must be able to see. OFFICIAL is the normal case and is not tracked.
EXCEPTION_KINDS = ("incomplete", "unofficial", "secondary", "single_source", "computed", "from_scan", "low",
                   "unverified", "unreliable", "zero_moe")
_BADGE_KINDS = {"official", "unofficial", "computed", "from_scan", "secondary", "single_source", "unverified", "low"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
ROWLIKE = ("tr", "li", "p", "dt", "dd", "caption", "figcaption", "h1", "h2", "h3", "h4", "h5", "h6", "summary")
# legends that show every status to define it are not figures
LEGEND_CLASSES = ("badge-defs", "marks-key", "fnotes", "cv-legend")
LEGEND_IDS = ("figure-notes",)
# caveat wording attached to a figure in the old form (taken out of the context text; the kind is recorded)
CAVEATS = [
    (re.compile(r"incomplete: the total covers only the reports on file, so it is a floor\.?", re.I), "incomplete"),
    (re.compile(r"\(?incomplete: a floor\)?", re.I), "incomplete"),
    (re.compile(r"complete: every expected report is on file\.?", re.I), None),
    (re.compile(r"\(unofficial count\)", re.I), None),
    (re.compile(r"unofficial count\.", re.I), None),
]
# a bare status word next to a figure, e.g. "2 of 3 with reports · incomplete", "4 incomplete", a "Incomplete" cell
_WORD_INCOMPLETE = re.compile(r"\bincomplete\b", re.I)
_SPACE = re.compile(r"\s+")
_PUNCT = re.compile(r"[^0-9a-z$%]+")
_STRIP = re.compile(r"[⁠ *†‡§¶‖◊?≈°·]")


class Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.children, self.parent = tag, attrs, [], parent

    @property
    def classes(self) -> set:
        return set((self.attrs.get("class") or "").split())

    def ancestors(self):
        n = self.parent
        while n is not None:
            yield n
            n = n.parent

    def iter(self):
        yield self
        for c in self.children:
            if isinstance(c, Node):
                yield from c.iter()


class _Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, {k: (v or "") for k, v in attrs}, self.cur)
        self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, {k: (v or "") for k, v in attrs}, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def main_tree(html: str) -> Node:
    m = re.search(r"<main\b[^>]*>(.*)</main>", html, re.S)
    p = _Tree()
    p.feed(m.group(1) if m else "")
    p.close()
    return p.root


def mark_kind(n: Node) -> str | None:
    """The status a status element shows (old badge, old mark, new symbol mark, community reliability mark)."""
    c = n.classes
    if "fmark" in c and n.attrs.get("data-fmark"):
        return n.attrs["data-fmark"]
    if "fquiet" in c and n.attrs.get("data-fquiet"):
        # 2026-11-18 (maps-cleanup brief, part B item 5): "computed" is said once per page in its note; each computed
        # figure keeps a hidden marker (civic/shell.py _QUIET_COMPUTED), so its status is still read on its row
        return n.attrs["data-fquiet"]
    if "fword" in c:                       # the word beside a results heading (components.status_heading)
        return next((x[6:] for x in c if x.startswith("fword-")), None)
    if "badge" in c:
        for k in _BADGE_KINDS:
            if f"badge-{k}" in c:
                return k
    if "smark" in c:
        for k in _BADGE_KINDS:
            if f"smark-is-{k}" in c:
                return k
    if "cv-mark" in c:
        t = text(n)
        return "unreliable" if "†" in t else "zero_moe" if "‡" in t else None
    return None


def _is_legend(n: Node) -> bool:
    for a in [n, *n.ancestors()]:
        if a.classes & set(LEGEND_CLASSES) or a.attrs.get("id") in LEGEND_IDS:
            return True
    return False


def text(n, skip_marks: bool = False) -> str:
    out = []
    for c in n.children:
        if isinstance(c, str):
            out.append(c)
        elif c.tag in ("script", "style", "template"):
            continue
        elif skip_marks and mark_kind(c):
            continue
        else:
            # a space at element edges keeps word boundaries ("2023" + "incomplete"); norm() drops spaces anyway
            out.append(" " + text(c, skip_marks) + " ")
    return "".join(out)


def context(n: Node) -> tuple[str, Node | None]:
    """Normalized text of the nearest row-like element around ``n`` (letters, digits, $ and % only)."""
    row = next((a for a in [n, *n.ancestors()] if a.tag in ROWLIKE), None)
    if row is None:
        return "", None
    return norm(text(row, skip_marks=True)), row


def norm(t: str) -> str:
    for rx, _ in CAVEATS:
        t = rx.sub(" ", t)
    t = _WORD_INCOMPLETE.sub(" ", t)
    # letters, digits, $ and % only: spacing and punctuation around a mark differ between the old and new forms
    return _PUNCT.sub("", _STRIP.sub("", t).lower())


def occurrences(html: str) -> set[tuple[str, str]]:
    """{(context, kind)} for every exception status shown on the page, old form or new."""
    root = main_tree(html)
    out = set()
    for n in root.iter():
        if n is root:
            continue
        k = mark_kind(n)
        if k and k in EXCEPTION_KINDS and not _is_legend(n):
            ctx, _ = context(n)
            out.add((ctx, k))
        # caveat words in running text
        for c in n.children:
            if isinstance(c, str) and _WORD_INCOMPLETE.search(c) and not _is_legend(n) and not mark_kind(n):
                ctx, _ = context(n)
                out.add((ctx, "incomplete"))
    return out


def scoped(html: str) -> dict[str, set]:
    """{context: kinds} for every row-like element inside a section whose caption states its status once."""
    root = main_tree(html)
    out: dict[str, set] = {}
    for n in root.iter():
        if n.tag not in ROWLIKE:
            continue
        kinds = set()
        for a in n.ancestors():
            kinds |= set((a.attrs.get("data-fscope") or "").split())
        if kinds:
            out.setdefault(norm(text(n, skip_marks=True)), set()).update(kinds)
    return out


def symbols(html: str) -> list[tuple[str, str, str]]:
    """[(kind, symbol, href)] for every new-style symbol mark on the page (not counting the note itself)."""
    root = main_tree(html)
    return [(n.attrs["data-fmark"], text(n).replace("⁠", "").strip(), n.attrs.get("href", ""))
            for n in root.iter() if "fmark" in n.classes and n.attrs.get("data-fmark") and not _is_legend(n)]


def quiet_kinds(html: str) -> set:
    """The kinds of the quiet markers on the page (statuses said once in the note, not beside each figure)."""
    root = main_tree(html)
    return {n.attrs["data-fquiet"] for n in root.iter() if "fquiet" in n.classes and n.attrs.get("data-fquiet")}


def scope_kinds(html: str) -> set:
    root = main_tree(html)
    out = set()
    for n in root.iter():
        out |= set((n.attrs.get("data-fscope") or "").split())
    return out


def note_entries(html: str) -> dict[str, str]:
    """{kind: entry text} of the page's "About these figures" note (id="figure-notes")."""
    root = main_tree(html)
    note = next((n for n in root.iter() if n.attrs.get("id") == "figure-notes"), None)
    if note is None:
        return {}
    return {n.attrs["data-fnote"]: _SPACE.sub(" ", text(n)).strip() for n in note.iter() if n.attrs.get("data-fnote")}
