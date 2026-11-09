"""Wave E, batch 9: sticky "On this page" navigation, one site-wide anchor-landing script, compact phone masthead.

- civic/shell.py ONPAGE_PAGES marks the long pages (data-onpage="1" on #site); each has a plain nav.toc whose links all
  point at ids on the page (that table of contents is what JS-off readers get, and what static/js/onpage.js builds from).
- static/js/anchor_landing.js is the only landing script; margins.js is gone; nothing else re-scrolls to the hash.
- onpage.css raises scroll-padding-top; masthead.css keeps every masthead control.
Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = ROOT / "tools" / "site"
sys.path.insert(0, str(SITE_DIR))

import build  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import ONPAGE_PAGES, Site  # noqa: E402

JS = SITE_DIR / "static" / "js"
CSS = SITE_DIR / "static" / "css"
ID_RE = re.compile(r'\sid="([^"]+)"')
OTHER = ["index.html", "elections/judges-and-questions/index.html", "teach/index.html"]


class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.site = Site(cls.ed, Path(cls.tmp.name))
        build.discover_builders()
        cls.pages = sorted(ONPAGE_PAGES) + OTHER
        for p in cls.pages:
            build.BUILDERS[p](cls.site)
        cls.site.write()
        cls.html = {p: (Path(cls.tmp.name) / p).read_text(encoding="utf-8") for p in cls.pages}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_marked_pages_have_a_toc_that_resolves(self):
        for p in sorted(ONPAGE_PAGES):
            html = self.html[p]
            self.assertIn(' data-onpage="1">', html, p)
            m = re.search(r'<nav class="toc" aria-label="On this page">(.*?)</nav>', html, re.S)
            self.assertIsNotNone(m, f"{p}: no table of contents")
            hrefs = re.findall(r'<a href="#([^"]+)"', m.group(1))
            self.assertGreaterEqual(len(hrefs), 3, p)
            ids = set(ID_RE.findall(html))
            for frag in hrefs:
                self.assertIn(frag, ids, f"{p}: toc link #{frag} has no target")

    def test_other_pages_are_not_marked(self):
        for p in OTHER:
            self.assertNotIn("data-onpage", self.html[p], p)

    def test_marked_pages_exist_in_the_sitemap(self):
        for p in ONPAGE_PAGES:
            self.assertIn(p, build.BUILDERS, p)

    def test_the_bar_is_added_by_script_not_shipped(self):
        # JS-off readers get the plain toc only: no bar, no "Back to top", in the shipped HTML
        for p in sorted(ONPAGE_PAGES):
            self.assertNotIn('class="onpage"', self.html[p], p)
            self.assertNotIn("to-top", self.html[p], p)


class Assets(unittest.TestCase):
    def test_one_landing_script(self):
        self.assertFalse((JS / "margins.js").exists(), "margins.js is replaced by anchor_landing.js")
        land = [f.name for f in JS.glob("*.js") if re.search(r'scrollIntoView\(\{\s*block:\s*"start",\s*behavior:\s*"instant"', f.read_text(encoding="utf-8"))]
        self.assertEqual(land, ["anchor_landing.js"])
        for f in JS.glob("*.js"):
            self.assertNotIn("mg-find", f.read_text(encoding="utf-8"), f.name)

    def test_landing_script_rules(self):
        s = (JS / "anchor_landing.js").read_text(encoding="utf-8")
        for needle in ("fonts.ready", "scrollPaddingTop", "scrollMarginTop", "reload", "back_forward", "wheel", "keydown"):
            self.assertIn(needle, s)

    def test_scripts_are_ascii(self):
        for name in ("anchor_landing.js", "onpage.js"):
            (JS / name).read_text(encoding="utf-8").encode("ascii")

    def test_scroll_padding_clears_nav_and_bar(self):
        css = (CSS / "onpage.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"html\.has-onpage\s*\{[^}]*scroll-padding-top:\s*calc\(var\(--nav-h[^)]*\) \+ var\(--onpage-h\)")
        self.assertIn("position: fixed", css)
        self.assertIn("@media print", css)

    def test_onpage_js_has_no_focus_trap(self):
        s = (JS / "onpage.js").read_text(encoding="utf-8")
        self.assertNotIn("keydown", s)
        self.assertNotIn("tabindex", s.replace('"tabindex", "-1"', ""))

    def test_masthead_keeps_every_control(self):
        css = (CSS / "masthead.css").read_text(encoding="utf-8")
        self.assertIn("max-width: 480px", css)
        self.assertNotRegex(css, r"display:\s*none")           # nothing is removed
        shell = (SITE_DIR / "civic" / "shell.py").read_text(encoding="utf-8")
        for needle in ('"theme-toggle"', "look_switch(\"head\")", "self._search()", "Not your county?"):
            self.assertIn(needle, shell)


if __name__ == "__main__":
    unittest.main()
