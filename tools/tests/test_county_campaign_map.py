"""County campaign-money page map (added 2026-11-09): money/campaigns/county/ gets its own map.

- Race types: countywide offices (one single-shape layer per office, its latest race), commissioner districts,
  council districts, townships (Nick, 2026-11-09; each township links to its own page); the commissioner layer is the
  default (it is what JS-off readers see).
- The box adds who holds the seat now and the race's result with its margin, plus a results-explorer link.
- Every other area page with a race and an outline gets the same kind of map (area_layers); the state-legislature page
  gets House and Senate layers.
- Every shape and every panel link points at a race card on the same page (a bare #r-<id> fragment, no reload).
- Countywide-office layers share one set of shading steps; each legend marks "this office" exactly once.
- static/js/campaigns_map.js shows a one-shape layer's figures at once, only on a map marked data-cf-auto-one.
- The main campaigns map (money/campaigns/) is unchanged: no auto-one, the race types of campaign_money.TYPES.
Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = ROOT / "tools" / "site"
sys.path.insert(0, str(SITE_DIR))

import build  # noqa: E402
from civic.campaign_map import COUNTY_DEFAULT, COUNTY_TYPES, office_tab  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site  # noqa: E402

COUNTY = "money/campaigns/county/index.html"
INDEX = "money/campaigns/index.html"
JS = SITE_DIR / "static" / "js" / "campaigns_map.js"
ID_RE = re.compile(r'\sid="([^"]+)"')


class OfficeTab(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(office_tab("County Sheriff"), "Sheriff")
        self.assertEqual(office_tab("Clerk of the Circuit Court"), "Clerk")
        self.assertEqual(office_tab("Prosecuting Attorney"), "Prosecuting Attorney")
        self.assertEqual(office_tab("Mayor of South Bend", ("South Bend",)), "Mayor")
        self.assertEqual(office_tab("Centre Township Trustee", ("Centre Township",)), "Trustee")
        self.assertEqual(office_tab("John Glenn School Board, Liberty Township", ("John Glenn",)), "Liberty Township")
        self.assertEqual(office_tab("Walkerton Town Council Ward 1", ("Walkerton",)), "Council Ward 1")


class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.site = Site(cls.ed, Path(cls.tmp.name))
        build.discover_builders()
        for p in (COUNTY, INDEX):
            build.BUILDERS[p](cls.site)
        cls.site.write()
        cls.html = {p: (Path(cls.tmp.name) / p).read_text(encoding="utf-8") for p in (COUNTY, INDEX)}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _root(self, page):
        m = re.search(r'<div class="cmap cmap-money cf-map"[^>]*>', self.html[page])
        self.assertIsNotNone(m, page)
        return m.group(0)

    def _tabs(self, page):
        return re.findall(r'<button type="button" class="cmap-tab" data-layer="([^"]+)" data-cf-type="([^"]+)" '
                          r'aria-pressed="(true|false)">([^<]*)</button>', self.html[page])

    def test_section_and_toc(self):
        html = self.html[COUNTY]
        self.assertIn('id="map"', html)
        self.assertRegex(html, r'<nav class="toc"[^>]*>.*?href="#map"', )
        self.assertLess(html.index('id="map"'), html.index('id="e-2026g"'))

    def test_types_and_default(self):
        tabs = self._tabs(COUNTY)
        types = {t for _, t, _, _ in tabs}
        self.assertEqual(types, set(COUNTY_TYPES) | {"townships"})
        pressed = [lid for lid, _, p, _ in tabs if p == "true"]
        self.assertEqual(pressed, [COUNTY_DEFAULT])
        self.assertIn(f'data-default-layer="{COUNTY_DEFAULT}"', self._root(COUNTY))
        self.assertIn('data-cf-auto-one="on"', self._root(COUNTY))
        offices = [lab for _, t, _, lab in tabs if t == "countywide"]
        self.assertEqual(len(offices), len(set(offices)))
        for want in ("Clerk", "Sheriff", "Prosecutor", "Treasurer"):
            self.assertIn(want, offices)

    def test_layers_shapes_and_links(self):
        html = self.html[COUNTY]
        ids = set(ID_RE.findall(html))
        data = json.loads(re.search(r'<script type="application/json" id="cmap-data">(.*?)</script>', html, re.S).group(1))
        for lid, typ, _, _ in self._tabs(COUNTY):
            g = re.search(r'<g class="cmap-layer[^"]*" data-layer="%s"[^>]*>(.*?)</g><g class="cmap-layer|'
                          r'<g class="cmap-layer[^"]*" data-layer="%s"[^>]*>(.*?)<path d="[^"]*" class="cmap-outline"'
                          % (re.escape(lid), re.escape(lid)), html, re.S)
            self.assertIsNotNone(g, lid)
            body = g.group(1) or g.group(2)
            links = re.findall(r'<a href="([^"]+)" class="cmap-a" data-uid="([^"]+)"', body)
            self.assertTrue(links, lid)
            if typ == "countywide":
                self.assertEqual(len(links), 1, lid)
            for href, uid in links:
                self.assertEqual(data[uid]["href"], href)
                if typ == "townships":
                    self.assertRegex(href, r"^\.\./[a-z-]+-township/index\.html$")
                    self.assertTrue(any(f[0] == "Trustee now" for f in data[uid]["f"]), uid)
                    continue
                self.assertTrue(href.startswith("#r-"), (lid, href))
                self.assertIn(href[1:], ids, (lid, href))
                labels = [f[0] for f in data[uid]["f"]]
                self.assertIn("Result", labels, uid)
                self.assertLess(labels.index("Election"), labels.index("Result"), uid)
        self.assertEqual(sum(1 for _, t, _, _ in self._tabs(COUNTY) if t == "council"), 1)

    def test_shared_legend_marks_this_office_once(self):
        html = self.html[COUNTY]
        for lid, typ, _, _ in self._tabs(COUNTY):
            if typ != "countywide":
                continue
            m = re.search(r'<div class="cmap-mlegend[^"]*" data-layer="%s">(.*?)</div>' % re.escape(lid), html, re.S)
            self.assertIsNotNone(m, lid)
            self.assertEqual(m.group(1).count("this office"), 2, lid)  # the list item and the note's wording
            self.assertEqual(m.group(1).count(" · this office"), 1, lid)

    def test_index_map_unchanged(self):
        root = self._root(INDEX)
        self.assertNotIn("data-cf-auto-one", root)
        self.assertIn('data-default-layer="county"', root)
        self.assertNotIn('data-cf-type="countywide"', self.html[INDEX])

    def test_js_auto_one_is_gated(self):
        js = JS.read_text(encoding="utf-8")
        self.assertIn('getAttribute("data-cf-auto-one") !== "on"', js)
        self.assertIn('"cmap-select"', js)
        self.assertTrue(all(ord(ch) < 128 for ch in js))
        self.assertNotIn("innerHTML", js)


class AreaPages(unittest.TestCase):
    """Every campaigns location page: a map when the area has a race and an outline, links that land on the page."""

    SKIP = {"money/campaigns/index.html", "money/campaigns/all-filings/index.html",
            "money/campaigns/how-it-works/index.html", "money/campaigns/other-committees/index.html"}

    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.site = Site(cls.ed, Path(cls.tmp.name))
        build.discover_builders()
        cls.pages = sorted(p for p in build.BUILDERS if p.startswith("money/campaigns/") and p not in cls.SKIP)
        for p in cls.pages:
            build.BUILDERS[p](cls.site)
        cls.site.write()
        cls.html = {p: (Path(cls.tmp.name) / p).read_text(encoding="utf-8") for p in cls.pages}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_maps_where_expected(self):
        no_map = {p for p in self.pages if 'class="cmap cmap-money cf-map' not in self.html[p]}
        # Indian Village and Lakeville: no race in the guide's 2023 to 2026 results
        self.assertEqual(no_map, {"money/campaigns/indian-village/index.html", "money/campaigns/lakeville/index.html"})

    def test_links_land_on_the_page(self):
        for p, html in self.html.items():
            if "cf-map" not in html:
                continue
            ids = set(ID_RE.findall(html))
            data = json.loads(re.search(r'id="cmap-data">(.*?)</script>', html, re.S).group(1))
            for href, uid in re.findall(r'<a href="([^"]+)" class="cmap-a" data-uid="([^"]+)"', html):
                self.assertEqual(data[uid]["href"], href, (p, uid))
                if href.startswith("#"):
                    self.assertIn(href[1:], ids, (p, href))
                else:  # only the county page's township layer leaves the page
                    self.assertTrue(p.endswith("/county/index.html") and uid.startswith("township:"), (p, href))

    def test_frames_and_one_type_rows(self):
        sb = self.html["money/campaigns/south-bend/index.html"]
        self.assertRegex(sb, r'class="cmap cmap-money cf-map cf-amap cf-amap-z\d"')
        self.assertIn('data-cf-type="council"', sb)
        self.assertIn('data-cf-type="whole"', sb)
        twp = self.html["money/campaigns/centre-township/index.html"]
        self.assertEqual(re.findall(r'class="cf-type" data-cf-type="([^"]+)"', twp), ["whole"])
        self.assertIn('typeBtns.length < 2', JS.read_text(encoding="utf-8"))

    def test_nodraw_districts_say_so(self):
        html = self.html["money/campaigns/sbcsc/index.html"]
        data = json.loads(re.search(r'id="cmap-data">(.*?)</script>', html, re.S).group(1))
        nd = [v for k, v in data.items() if any("boundary isn't in the guide" in c for c in v.get("cav", []))]
        self.assertGreaterEqual(len(nd), 5)

    def test_state_map(self):
        html = self.html["money/campaigns/state-legislature/index.html"]
        self.assertIn('data-cf-type="house"', html)
        self.assertIn('data-cf-type="senate"', html)
        self.assertLess(html.index('id="map"'), html.index('id="districts"'))


if __name__ == "__main__":
    unittest.main()
