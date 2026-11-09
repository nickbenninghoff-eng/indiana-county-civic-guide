"""HTML escaping and a tiny tag builder.

Everything that comes from data is escaped by default. ``Markup`` marks a string that
is already safe HTML, so it is never escaped twice. Build markup with ``h()``:

    h("a", {"href": url, "class": "src"}, "Title & more")
    -> <a href="..." class="src">Title &amp; more</a>
"""
from __future__ import annotations

import html as _html
import json
from typing import Any, Iterable

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "source", "track", "wbr", "circle", "rect", "path", "line", "polyline", "polygon",
        "use", "stop", "ellipse"}
# SVG elements in VOID are self-closed with " />" only when they have no children.
SVG_SELF_CLOSE = {"circle", "rect", "path", "line", "polyline", "polygon", "use", "stop", "ellipse"}


class Markup(str):
    """A string that is already safe HTML."""

    def __html__(self) -> "Markup":
        return self

    def __add__(self, other: Any) -> "Markup":
        return Markup(str(self) + str(esc(other)))

    def __radd__(self, other: Any) -> "Markup":
        return Markup(str(esc(other)) + str(self))


def esc(value: Any) -> Markup:
    """Escape a value for HTML text or attribute context. Markup passes through."""
    if isinstance(value, Markup):
        return value
    if value is None:
        return Markup("")
    return Markup(_html.escape(str(value), quote=True))


def _attr_name(key: str) -> str:
    key = key.rstrip("_")  # class_ -> class
    return key.replace("_", "-") if key.startswith(("data_", "aria_")) else key


def attrs(mapping: dict | None) -> str:
    if not mapping:
        return ""
    out = []
    for key, val in mapping.items():
        if val is None or val is False:
            continue
        name = _attr_name(key)
        if val is True:
            out.append(f" {name}")
        else:
            out.append(f' {name}="{esc(val)}"')
    return "".join(out)


def _render_child(child: Any) -> str:
    if child is None or child is False:
        return ""
    if isinstance(child, (list, tuple)):
        return "".join(_render_child(c) for c in child)
    if isinstance(child, (int, float)) and not isinstance(child, bool):
        return str(child)
    return str(esc(child))


def h(tag: str, attributes: dict | None = None, *children: Any) -> Markup:
    """Build an element. Children may be strings (escaped), Markup, lists or None."""
    body = "".join(_render_child(c) for c in children)
    a = attrs(attributes)
    if tag in VOID and not body:
        if tag in SVG_SELF_CLOSE:
            return Markup(f"<{tag}{a} />")
        return Markup(f"<{tag}{a}>")
    return Markup(f"<{tag}{a}>{body}</{tag}>")


def join(items: Iterable[Any], sep: Any = "") -> Markup:
    sep_s = _render_child(sep)
    return Markup(sep_s.join(_render_child(i) for i in items))


def raw(s: str) -> Markup:
    """Trust a literal string written in this codebase (never data)."""
    return Markup(s)


def json_script(element_id: str, payload: Any) -> Markup:
    """Embed JSON for app.js. '</' is escaped so data can't close the script tag."""
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    text = text.replace("</", "<\\/").replace("<!--", "<\\!--")
    return Markup(f'<script type="application/json" id="{esc(element_id)}">{text}</script>')


def slug(text: str) -> str:
    out = []
    for ch in str(text).lower():
        if ch.isascii() and ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-")
