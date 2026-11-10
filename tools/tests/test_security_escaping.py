"""Security review 2026-11-09: data from the CSVs (text copied from public PDFs, news and web pages) must render
inert. Covers civic/html.py (h, attrs, safe_url, json_script), the Sources list and data tables, and a scan of
the built site (when site/st-joseph exists) for script-running URLs and broken JSON data blocks.

Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import html
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "site"))

from civic import html as H  # noqa: E402
from civic.components import Citations, data_table  # noqa: E402
from civic.html import Markup, h, json_script, safe_url  # noqa: E402

UNSAFE = [
    "javascript:alert(1)",
    "JaVaScRiPt:alert(1)",
    "  javascript:alert(1)",
    "\x01javascript:alert(1)",
    "java\tscript:alert(1)",
    "java\nscript:alert(1)",
    "vbscript:msgbox(1)",
    "data:text/html,<script>alert(1)</script>",
    "data:image/svg+xml;base64,PHN2Zz4=",
    "file:///C:/Windows/win.ini",
]
SAFE = [
    "https://www.sjcindiana.gov/DocumentCenter/View/70554",
    "http://example.org/a?b=1&c=2",
    "mailto:voter@sjcindiana.gov",
    "tel:+15742359999",
    "../county/index.html#boards",
    "#src-GOV-001",
    "index.html",
    "images/John_Brademas_2.jpg",
    "a/b:c",  # a colon after a slash is a path, not a scheme
]


def _quiet(fn):
    """Run fn with the html module's stderr warning silenced; return its result."""
    import io
    old = sys.stderr
    sys.stderr = io.StringIO()
    try:
        return fn()
    finally:
        sys.stderr = old


class SafeUrl(unittest.TestCase):
    def test_unsafe_schemes_rejected(self):
        for u in UNSAFE:
            self.assertIsNone(safe_url(u), u)

    def test_safe_urls_kept_verbatim(self):
        for u in SAFE:
            self.assertEqual(safe_url(u), u)

    def test_markup_entities_are_decoded_before_the_test(self):
        # Markup is not escaped again, so the browser would decode &#106; to "j"
        self.assertIsNone(safe_url(Markup("&#106;avascript:alert(1)")))
        # a plain string IS escaped (&amp;#106;...), so it stays a harmless relative URL
        self.assertEqual(safe_url("&#106;avascript:alert(1)"), "&#106;avascript:alert(1)")


class Attrs(unittest.TestCase):
    def test_unsafe_href_and_src_are_dropped(self):
        for u in UNSAFE:
            for tag, attr in (("a", "href"), ("img", "src"), ("form", "action"), ("use", "xlink:href")):
                out = _quiet(lambda: str(h(tag, {attr: u, "class": "x"}, "t" if tag != "img" else None)))
                self.assertNotIn(f"{attr}=", out, (tag, u, out))
                self.assertIn('class="x"', out)
                self.assertNotRegex(out.lower(), r"(java|vb)script:|data:")

    def test_dropped_urls_are_recorded(self):
        before = len(H.BLOCKED_URLS)
        _quiet(lambda: h("a", {"href": "javascript:alert(1)"}, "x"))
        self.assertEqual(H.BLOCKED_URLS[before:], ["javascript:alert(1)"])

    def test_safe_href_kept_and_escaped(self):
        out = str(h("a", {"href": 'https://x.org/?a=1&b="2"'}, "x"))
        self.assertEqual(out, '<a href="https://x.org/?a=1&amp;b=&quot;2&quot;">x</a>')

    def test_non_url_attributes_untouched(self):
        out = str(h("span", {"data-x": "javascript:alert(1)", "title": "data:x"}, "t"))
        self.assertIn('data-x="javascript:alert(1)"', out)  # inert text in a data attribute
        self.assertIn('title="data:x"', out)

    def test_attribute_quote_breakout_escaped(self):
        out = str(h("a", {"href": '" onmouseover="alert(1)', "title": "' onfocus='alert(1)"}, "x"))
        self.assertNotIn('" onmouseover', out)
        self.assertNotIn("' onfocus", out)
        self.assertIn("&quot; onmouseover=&quot;", out)
        self.assertIn("&#x27; onfocus=&#x27;", out)

    def test_text_is_escaped(self):
        out = str(h("p", None, "<script>alert(1)</script> & <img src=x onerror=alert(1)>"))
        self.assertEqual(out, "<p>&lt;script&gt;alert(1)&lt;/script&gt; &amp; &lt;img src=x onerror=alert(1)&gt;</p>")

    def test_markup_concat_escapes_plain_strings(self):
        out = Markup("<b>ok</b>") + "<script>"
        self.assertEqual(str(out), "<b>ok</b>&lt;script&gt;")


class JsonScript(unittest.TestCase):
    PAYLOAD = {"t": "</script><script>alert(1)</script>", "c": "<!-- <script>", "u": "a\u2028b\u2029c",
               "amp": "Parks & Rec", "n": [1, 2.5, None, True]}

    def _inner(self, out: str) -> str:
        m = re.fullmatch(r'<script type="application/json" id="d">(.*)</script>', out, re.S)
        self.assertIsNotNone(m, out)
        return m.group(1)

    def test_no_breakout_and_round_trip(self):
        inner = self._inner(str(json_script("d", self.PAYLOAD)))
        self.assertNotIn("<", inner)
        self.assertNotIn("\u2028", inner)
        self.assertNotIn("\u2029", inner)
        self.assertEqual(json.loads(inner), self.PAYLOAD)

    def test_html_comment_opener_is_valid_json(self):
        # the earlier '<\\!--' replacement was not valid JSON: JSON.parse threw and the feature broke
        inner = self._inner(str(json_script("d", {"x": "a <!-- b"})))
        self.assertEqual(json.loads(inner), {"x": "a <!-- b"})

    def test_element_id_escaped(self):
        out = str(json_script('d" onload="x', {}))
        self.assertIn('id="d&quot; onload=&quot;x"', out)


class _FakeEd:
    def __init__(self, sources):
        self.sources = sources


class SourcesList(unittest.TestCase):
    def test_hostile_source_row_renders_inert(self):
        ed = _FakeEd({
            "BAD-001": {"title": "<img src=x onerror=alert(1)>", "url": "javascript:alert(1)",
                        "publisher": "<b>Pub</b>", "kind": "\"><script>alert(1)</script>"},
            "BAD-002": {"title": "Quote \" breakout", "url": 'https://x.org/" onmouseover="alert(1)', "kind": "web"},
            "BAD-003": {"title": "", "url": "data:text/html,<script>alert(1)</script>", "kind": "web"},
        })
        c = Citations(ed)
        for sid in ed.sources:
            c.cite(sid)
        out = _quiet(lambda: str(c.render()))
        self.assertNotIn("<img", out)
        self.assertNotIn("<script", out)
        self.assertNotIn("<b>Pub", out)
        self.assertNotRegex(out, r'href="(javascript|data):')
        self.assertNotIn('" onmouseover="', out)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", out)


class DataTable(unittest.TestCase):
    def test_cells_and_caption_escaped(self):
        out = str(data_table("t1", ["<th>"], [["<script>alert(1)</script>", "a\" onclick=\"x"]],
                             caption="</caption><script>"))
        self.assertNotIn("<script", out)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", out)
        self.assertNotIn("</caption><script>", out)


OUT = ROOT / "site" / "st-joseph"
URL_ATTR_RE = re.compile(r'\s(href|src|xlink:href|action|formaction|poster)="([^"]*)"', re.I)
DATA_BLOCK_RE = re.compile(r'<script type="application/json" id="([^"]+)">(.*?)</script>', re.S)
EVENT_ATTR_RE = re.compile(r"<[a-zA-Z][^>]*\son[a-z]+\s*=", re.S)


@unittest.skipUnless((OUT / "index.html").is_file(), "site/st-joseph not built")
class BuiltSite(unittest.TestCase):
    """The rendered output: no script-running URL anywhere, every JSON data block parses and cannot break out,
    no inline event-handler attributes (the Content-Security-Policy in netlify.toml forbids them)."""

    @classmethod
    def setUpClass(cls):
        cls.pages = {p.relative_to(OUT).as_posix(): p.read_text(encoding="utf-8") for p in OUT.rglob("*.html")}

    def test_no_unsafe_url_attributes(self):
        bad = []
        for path, text in self.pages.items():
            for name, val in URL_ATTR_RE.findall(text):
                if safe_url(Markup(val)) is None:  # attribute text as the browser decodes it
                    bad.append((path, name, val[:80]))
        self.assertEqual(bad, [])

    def test_json_blocks_parse_and_stay_closed(self):
        bad = []
        for path, text in self.pages.items():
            for bid, inner in DATA_BLOCK_RE.findall(text):
                if "<!--" in inner or "<script" in inner.lower():
                    bad.append((path, bid, "html-parser state change"))
                try:
                    json.loads(inner)
                except ValueError as e:
                    bad.append((path, bid, str(e)[:80]))
        self.assertEqual(bad, [])

    def test_no_inline_event_handlers(self):
        bad = [p for p, t in self.pages.items() if EVENT_ATTR_RE.search(t)]
        self.assertEqual(bad, [])

    def test_only_the_look_boot_inline_script(self):
        # exactly one executable inline script per page (shell.LOOK_BOOT); its hash is in the CSP
        from civic.shell import LOOK_BOOT
        boot = html.unescape(LOOK_BOOT)
        for path, text in self.pages.items():
            inline = [m for m in re.findall(r"<script(?![^>]*\b(?:src|type)=)[^>]*>(.*?)</script>", text, re.S)]
            self.assertEqual(len(inline), 1, path)
            self.assertIn(inline[0], boot, path)


if __name__ == "__main__":
    unittest.main()
