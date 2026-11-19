"""Phase 6 step 6 (2026-11-18): the Learn hub, the learning paths, the footer columns and the stale-link ratchet.

planning/design-direction-2026-11-16.md section 3 (Learn, Footer) and section 7 row 6; report
planning/qa/phase6-learn-2026-11-18.md.

- No learning-path stop, no Learn dropdown link, no Learn hub link and no footer link resolves to a forwarding page
  (an Entry with moved_to, or a page carrying <meta name="civic-moved-to">).
- The Learn dropdown has at most MAX_DROPDOWN links; the hub does the rest.
- The footer is four short labeled columns; the data date appears once; every FOOTER link is in a column.
- Links from content pages to forwarding pages can only go down: STALE_BASELINE is the count measured on 2026-11-18.
Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import html as htmllib
import posixpath
import re
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = ROOT / "tools" / "site"
sys.path.insert(0, str(SITE_DIR))

import build  # noqa: E402
from civic import sitemap  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site  # noqa: E402
from pages import learn, stubs  # noqa: E402

HREF_RE = re.compile(r'href="([^"]*)"')
MOVED_META = '<meta name="civic-moved-to"'
# Links from pages that are not forwarding pages to forwarding pages, counted on the built site on 2026-11-18 (see the
# report). Lower it when generating code is re-pointed; it must never go up. A link to a forwarding page still works
# (it lands on the page that forwards), so this is a tidiness ratchet, not a correctness check.
STALE_BASELINE = 0


def _resolve(page: str, href: str) -> str:
    if not href or href.startswith(("http:", "https:", "mailto:", "#", "javascript:")):
        return ""
    path = href.split("#")[0].split("?")[0]
    return posixpath.normpath(posixpath.join(posixpath.dirname(page), path)) if path else ""


def _live(by_path: dict, target: str) -> tuple[bool, str]:
    p = target.split("#")[0]
    e = by_path.get(p)
    if e is None:
        return False, f"{p} is not in the sitemap"
    if e.moved_to:
        return False, f"{p} is a forwarding page (moved to {e.moved_to})"
    return True, ""


# ====================================================================== model (no build)
class Model(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.site = Site(cls.ed, Path(tempfile.gettempdir()) / "unused-phase6-learn")
        cls.by_path = cls.site.by_path

    def test_every_path_stop_points_at_a_live_page(self):
        bad = []
        for p in sitemap.PATHS:
            for i, s in enumerate(p["stops"], 1):
                ok, why = _live(self.by_path, s["page"])
                if not ok:
                    bad.append(f"{p['id']} stop {i} ({s['title']}): {why}")
        self.assertEqual(bad, [], "re-point these learning-path stops at the page that teaches the same thing "
                                  "(civic/sitemap.py PATHS):\n" + "\n".join(bad))

    def test_path_stop_anchors_are_attached_to_their_pages(self):
        for p in sitemap.PATHS:
            for s in p["stops"]:
                e = self.by_path[s["page"]]
                self.assertIn(s["anchor"], {a for a, _ in e.sections}, (p["id"], s["page"], s["anchor"]))

    def test_learn_dropdown_is_short_and_live(self):
        learn_item = next(i for i in sitemap.NAV if i["name"] == "Learn")
        self.assertEqual(learn_item["hub"], learn.HUB)
        self.assertLessEqual(len(learn_item["links"]), sitemap.MAX_DROPDOWN)
        self.assertIn(("learn/index.html#paths", "Learning paths"), learn_item["links"])
        for path, _label in learn_item["links"]:
            ok, why = _live(self.by_path, path)
            self.assertTrue(ok, why)

    def test_learn_hub_is_the_learn_nav_item(self):
        learn_item = next(i for i in sitemap.NAV if i["name"] == "Learn")
        for path in (learn.HUB, "teach/index.html", "community/index.html"):
            self.assertIn(path, self.by_path)
        self.assertIs(sitemap.nav_of(learn.HUB), learn_item)
        self.assertIs(sitemap.nav_of("teach/index.html"), learn_item)
        self.assertEqual(sitemap.crumbs(self.by_path, learn.HUB), [("Learn", None)])
        self.assertEqual(sitemap.crumbs(self.by_path, "teach/index.html")[0], ("Learn", learn.HUB))

    def test_every_guide_card_points_at_a_live_page_or_is_skipped(self):
        for _heading, items in learn.GUIDES:
            for path, _title in items:
                if path in self.by_path:
                    ok, why = _live(self.by_path, path)
                    self.assertTrue(ok, why)

    def test_footer_links_are_in_columns_and_live(self):
        cols = sitemap.FOOTER_COLUMNS
        self.assertGreaterEqual(len(cols), 3)
        self.assertLessEqual(len(cols), 4)
        flat = {(p, label) for _h, items in cols for p, label in items}
        for item in sitemap.FOOTER:
            self.assertIn(item, flat)
        for p, _l in flat:
            ok, why = _live(self.by_path, p)
            self.assertTrue(ok, why)
        for _h, items in cols:
            self.assertLessEqual(len(items), 6)

    def test_new_css_has_no_literal_colors(self):
        for name in ("footer.css", "learn.css"):
            css = (SITE_DIR / "static" / "css" / name).read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(", css), name)


# ====================================================================== the built site
class Built(unittest.TestCase):
    """One full build into a temporary folder (the same loop as build.py)."""

    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        site = Site(cls.ed, cls.out)
        build.discover_builders()
        failed = []
        for entry in site.entries:
            fn = build.BUILDERS.get(entry.path)
            if fn:
                try:
                    fn(site)
                except Exception as e:   # noqa: BLE001 (reported below, never hidden)
                    failed.append(f"{entry.path}: {type(e).__name__}: {e}")
                    site.pages.pop(entry.path, None)
                    stubs.build_stub(site, entry)
            else:
                stubs.build_stub(site, entry)
        site.write()
        cls.site = site
        cls.failed = failed
        cls._html = {}
        cls.forwarding = {p for p, e in site.by_path.items() if e.moved_to}
        for p in site.pages:
            if MOVED_META in cls.html_of(p):
                cls.forwarding.add(p)

    @classmethod
    def html_of(cls, path):
        if path not in cls._html:
            cls._html[path] = (cls.out / path).read_text(encoding="utf-8")
        return cls._html[path]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def targets(self, path, fragment=None):
        src = fragment if fragment is not None else self.html_of(path)
        return [t for t in (_resolve(path, h) for h in HREF_RE.findall(src)) if t]

    @staticmethod
    def _between(h, start, end):
        i = h.index(start)
        return h[i:h.index(end, i)]

    def main_of(self, path):
        return self._between(self.html_of(path), "<main", "</main>")

    def test_no_builder_failed(self):
        self.assertEqual(self.failed, [])

    # ------------------------------------------------------------------ the hub
    def test_hub_links_resolve_to_built_live_pages(self):
        for t in self.targets(learn.HUB, self.main_of(learn.HUB)):
            self.assertTrue((self.out / t).is_file(), t)
            self.assertNotIn(t, self.forwarding, f"Learn hub links to the forwarding page {t}")

    def test_hub_has_a_card_for_each_guide_and_a_row_for_each_path(self):
        h = self.html_of(learn.HUB)
        for want in ("elections/how-it-works/index.html", "money/what-is-a-budget/index.html",
                     "who-handles-this/index.html", "run/index.html", "state/how-the-state-shapes-local/index.html",
                     "history/index.html", "community/index.html", "teach/index.html"):
            self.assertIn(f'href="../{want}"', h, want)
        for p in sitemap.PATHS:
            self.assertIn(f'href="../{p["stops"][0]["page"]}#path-{p["id"]}-1"', h, p["id"])
        self.assertGreaterEqual(h.count('class="card learn-card"'), 8)

    def test_hub_is_short(self):
        main = self.main_of(learn.HUB)
        self.assertLess(len(re.findall(r"<a ", main)), 45)
        self.assertEqual(main.count("<h1"), 1)

    def test_card_text_is_the_sitemap_description(self):
        # the hub states nothing of its own: each card's line is the linked page's sitemap description
        cards = re.findall(r'<p class="learn-desc">([^<]*)</p>', self.main_of(learn.HUB))
        descs = {e.description for e in self.site.entries}
        self.assertTrue(cards)
        for c in cards:
            self.assertIn(htmllib.unescape(c), descs, c)

    def test_run_card_links_each_office_page(self):
        main = self.main_of(learn.HUB)
        for e in self.site.entries:
            if e.path.startswith("run/") and e.path != "run/index.html":
                self.assertIn(f'href="../{e.path}"', main, e.path)

    # ------------------------------------------------------------------ paths
    def test_path_stop_pages_are_built_not_forwarding_and_carry_the_anchor(self):
        for p in sitemap.PATHS:
            for s in p["stops"]:
                self.assertNotIn(s["page"], self.forwarding, (p["id"], s["page"]))
                self.assertTrue((self.out / s["page"]).is_file(), s["page"])
                self.assertRegex(self.html_of(s["page"]), rf'id="{re.escape(s["anchor"])}"',
                                 (p["id"], s["page"], s["anchor"]))

    # ------------------------------------------------------------------ footer
    SAMPLE = ["index.html", "learn/index.html", "offices/south-bend-mayor/index.html",
              "governments/south-bend/index.html", "elections/index.html", "about/index.html", "data/index.html"]

    def foot(self, path):
        return self._between(self.html_of(path), "<footer", "</footer>")

    def test_footer_is_labeled_columns_with_every_required_link(self):
        for p in self.SAMPLE:
            f = self.foot(p)
            self.assertEqual(f.count('class="foot-col"'), len(sitemap.FOOTER_COLUMNS), p)
            self.assertEqual(f.count('class="foot-h mono"'), len(sitemap.FOOTER_COLUMNS), p)
            for label in ("About and methods", "Data downloads", "Sources index", "Corrections log", "Community profile",
                          "People", "Not your county?"):
                self.assertEqual(f.count(f">{label}<"), 1, (p, label))
            self.assertIn('id="browse"', f)

    def test_footer_states_the_data_date_once(self):
        for p in self.SAMPLE:
            f = self.foot(p)
            self.assertEqual(f.count("Data as of"), 1, p)
            self.assertEqual(f.count(f'datetime="{self.ed.config["data_as_of"]}"'), 1, p)

    def test_footer_links_resolve_to_live_pages(self):
        for p in self.SAMPLE:
            for t in self.targets(p, self.foot(p)):
                self.assertTrue((self.out / t).is_file(), (p, t))
                self.assertNotIn(t, self.forwarding, (p, t))

    def test_header_links_are_live(self):
        h = self.html_of("index.html")
        head = self._between(h, '<header class="masthead site-head"', "</header>")
        for t in self.targets("index.html", head):
            self.assertNotIn(t, self.forwarding, t)

    def test_the_hub_reaches_the_guides_and_the_school_board_page(self):
        first = set(self.targets("index.html", self.foot("index.html"))) | set(self.targets(learn.HUB))
        for want in ("teach/index.html", "who-handles-this/index.html", "state/how-the-state-shapes-local/index.html",
                     "run/school-board/index.html"):
            self.assertIn(want, first, want)

    # ------------------------------------------------------------------ stale links
    def test_links_to_forwarding_pages_only_go_down(self):
        count = Counter()
        for p in self.site.pages:
            if p in self.forwarding:
                continue
            for t in self.targets(p):
                if t in self.forwarding:
                    count[t] += 1
        total = sum(count.values())
        self.assertLessEqual(total, STALE_BASELINE,
                             f"{total} links from content pages to forwarding pages (baseline {STALE_BASELINE}); "
                             f"re-point the generating code at the final page: {count.most_common(8)}")


if __name__ == "__main__":
    unittest.main()
