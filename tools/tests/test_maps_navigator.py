"""Maps on every major page (2026-11-18; planning/maps-cleanup-brief-2026-11-18.md part A): the map navigator
(tools/site/civic/navmap.py, static/js/navmap.js, static/css/navmap.css) and its per-page coverage.
Report: planning/qa/phase6-maps-cleanup-2026-11-18.md.

- One shared asset: assets/navmap.svg holds every area path once (copied unchanged from the boundary files), with no
  colour, class or fill; pages reference it with <use>, never inline a path.
- Every covered page carries the navigator: a link (or a selectable element) per area that works with JavaScript off,
  the layer bar hidden until the script runs, a polite live status line, the full list on the page with every row
  tagged with area keys, and every key a row uses reachable on the map or in the chips beside it.
- Fills only tell kinds of government or neighbouring districts apart (never party classes).
- Hubs ship the map open; long browse pages ship it in a closed "Show map" fold.
- Deliberate exclusions carry no navigator.
- Edge cases: an unknown office id gives no key; a court belongs to the county too; a unit with no boundary file and a
  money-only government are chips; a page with no tagged row gets no navigator; the checker catches a <use> that
  points at a missing shape.
Run:  python -P -E -m unittest discover -s tools/tests -p "test_maps_navigator.py"
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = ROOT / "tools" / "site"
sys.path.insert(0, str(SITE_DIR))

import build  # noqa: E402
import check  # noqa: E402
from civic import governments as gm  # noqa: E402
from civic import navmap as nm  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.html import h  # noqa: E402
from civic.shell import Site  # noqa: E402

# page -> (folded by default, a key that must have rows on it)
COVERED = {
    "money/index.html": (False, "u:south-bend"),
    "money/campaigns/index.html": (True, "u:south-bend"),
    "money/campaigns/by-election/index.html": (True, "u:mishawaka"),
    "money/campaigns/by-candidate/index.html": (True, "u:south-bend"),
    "money/campaigns/all-filings/index.html": (True, "u:south-bend"),
    "elections/index.html": (False, "u:walkerton"),
    "elections/results/index.html": (False, "u:mishawaka"),
    "elections/calendar/index.html": (True, "u:penn-township"),
    "elections/judges-and-questions/index.html": (True, "u:mishawaka"),
    "elections/2024g/contests/index.html": (True, "u:county"),
    "elections/2023p/contests/index.html": (True, "u:south-bend"),
    "people/index.html": (False, "u:south-bend"),
    "officeholders/index.html": (False, "u:south-bend"),
    "community/index.html": (False, "u:penn-township"),
}
# deliberate exclusions (the report gives each reason)
EXCLUDED = ["learn/index.html", "about/index.html", "about/sources/index.html", "data/index.html",
            "offices/south-bend-mayor/index.html", "money/campaigns/other-committees/index.html",
            "elections/compare/turnout/index.html", "money/what-is-a-budget/index.html"]
FILLS = re.compile(r"^cmap-s (?:cmap-(?:city|town|township)|cmap-school cmap-school-[0-2]|dmap-s dmap-f[0-3])$")


class _Uses(HTMLParser):
    """Collects the navigator's parts from one page."""

    def __init__(self):
        super().__init__()
        self.depth = 0          # inside div.nm
        self.uses, self.areas, self.rows, self.paths_in_nm = [], [], [], 0
        self.ids = set()
        self.root = None
        self.status = None
        self.bar_hidden = None
        self.fold = None
        self.layers = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        cls = (a.get("class") or "").split()
        if tag == "div" and "nm" in cls and self.root is None:
            self.root = a
            self.depth = 1
            return
        if a.get("data-nm") is not None:
            self.rows.append(a["data-nm"])
        if not self.depth:
            return
        if tag not in ("use", "path", "circle", "input", "img", "br"):
            self.depth += 1
        if tag == "use":
            self.uses.append(a)
        if tag == "path":
            self.paths_in_nm += 1
        if a.get("data-nm-key"):
            self.areas.append((tag, a))
        if "nm-status" in cls:
            self.status = a
        if "nm-bar" in cls:
            self.bar_hidden = "hidden" in a
        if tag == "details" and "nm-fold" in cls:
            self.fold = a
        if tag == "g" and "nm-layer" in cls:
            self.layers.append(a)

    def handle_startendtag(self, tag, attrs):
        a = dict(attrs)
        if self.depth and tag == "use":
            self.uses.append(a)
        if a.get("data-nm") is not None:
            self.rows.append(a["data-nm"])

    def handle_endtag(self, tag):
        if self.depth and tag not in ("use", "path", "circle"):
            self.depth -= 1


class Navigator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        cls.site = Site(cls.ed, cls.out)
        build.discover_builders()
        for p in list(COVERED) + EXCLUDED:
            build.BUILDERS[p](cls.site)
        cls.site.write()
        cls.asset = (cls.out / nm.ASSET).read_text(encoding="utf-8")
        cls.asset_ids = set(re.findall(r'\bid="([^"]+)"', cls.asset))
        cls.parsed = {}
        for p in COVERED:
            u = _Uses()
            # row keys are written compactly (navmap.compact_row_keys); read them back as full keys
            u.feed(nm.expand_row_keys((cls.out / p).read_text(encoding="utf-8")))
            cls.parsed[p] = u

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # ------------------------------------------------------------------ the shared asset
    def test_asset_is_the_boundary_files_unchanged(self):
        from civic.district_map import load_district_shapes
        from civic.map import load_shapes
        shapes = load_shapes(self.ed)
        dshapes = load_district_shapes(self.ed, shapes)
        official = {shapes["county"]["d"]}
        official |= {it["d"] for L in shapes["layers"].values() for it in L}
        official |= {it["d"] for s in (dshapes or {}).get("sets", {}).values() for it in s.get("items", [])}
        ds = re.findall(r'<path [^>]*\bd="([^"]+)"', self.asset)
        self.assertGreater(len(ds), 60)
        for d in ds:
            self.assertIn(d, official, "a navigator shape is not one of the boundary files' paths")
        m = nm.model(self.ed)
        for L in m["layers"].values():
            for it in L["items"]:
                self.assertIn(nm.ASSET_ID + it["uid"], self.asset_ids)
        self.assertIn(nm.ASSET_ID + "county", self.asset_ids)

    def test_asset_carries_no_colour_class_or_fill(self):
        self.assertNotRegex(self.asset, r'\b(?:fill|stroke|class|style|color)=')
        self.assertIsNone(check.COLOR_RE.search(self.asset))

    def test_pages_never_inline_geometry(self):
        for p, u in self.parsed.items():
            self.assertEqual(u.paths_in_nm, 0, f"{p}: a <path> inside the navigator (geometry must come from the asset)")
            self.assertTrue(u.uses, p)
            for a in u.uses:
                href = a.get("href", "")
                file, _, frag = href.partition("#")
                self.assertTrue(file.endswith(nm.ASSET), f"{p}: {href}")
                self.assertIn(frag, self.asset_ids, f"{p}: {href} names no shape")

    # ------------------------------------------------------------------ every covered page
    def test_every_covered_page_has_the_navigator(self):
        for p, (folded, key) in COVERED.items():
            u = self.parsed[p]
            with self.subTest(page=p):
                self.assertIsNotNone(u.root, f"{p}: no navigator")
                for tid in u.root["data-nm-target"].split():
                    self.assertIn(tid, u.ids, f"{p}: target #{tid} is not on the page")
                self.assertTrue(u.root.get("data-nm-noun") and u.root.get("data-nm-plural"))
                # status: a polite live region
                self.assertEqual(u.status.get("role"), "status")
                self.assertEqual(u.status.get("aria-live"), "polite")
                # no JavaScript: the layer bar is hidden (it needs the script), one layer is drawn
                if u.layers:
                    self.assertTrue(u.bar_hidden, f"{p}: layer bar must ship hidden")
                    self.assertEqual(sum("is-on" in (g.get("class") or "") for g in u.layers), 1)
                    self.assertEqual(u.layers[0].get("data-nm-layer"), u.root.get("data-nm-default"))
                # folded on browse pages, open on hubs
                if folded:
                    self.assertIsNotNone(u.fold, f"{p}: should be in a Show map fold")
                    self.assertNotIn("open", u.fold)
                else:
                    self.assertIsNone(u.fold, f"{p}: a hub's map ships open")
                self.assertIn(key, " ".join(u.rows).split(), f"{p}: no row for {key}")

    def test_every_area_works_without_javascript_and_by_keyboard(self):
        for p, u in self.parsed.items():
            for tag, a in u.areas:
                with self.subTest(page=p, key=a["data-nm-key"]):
                    if "href" in a:
                        self.assertTrue(a["href"] and not a["href"].startswith("#"), a)
                    else:   # no page to open: still focusable and announced as a button
                        self.assertEqual(a.get("tabindex"), "0")
                        self.assertEqual(a.get("role"), "button")
                    self.assertTrue(a.get("aria-label") or a.get("data-nm-name"), "an area needs its name")

    def test_every_row_key_is_reachable(self):
        """A key a row uses is an area on the map or a chip beside it, or an office key whose government is (a
        district with no boundary file is reached through its government)."""
        for p, u in self.parsed.items():
            reach = {a["data-nm-key"] for _t, a in u.areas}
            for row in u.rows:
                keys = row.split()
                if not keys:        # a row the build could not place: hidden while an area is chosen, never mis-filed
                    continue
                with self.subTest(page=p, row=row):
                    self.assertTrue(any(k in reach for k in keys), f"{p}: row {row!r} cannot be reached")

    def test_fills_are_neutral(self):
        for p, u in self.parsed.items():
            for a in u.uses:
                cls = a.get("class") or ""
                if not cls or "nm-" in cls or "cmap-outline" in cls or "cmap-back-s" in cls:
                    continue
                self.assertRegex(cls, FILLS, f"{p}: {cls}")
                self.assertNotIn("party", cls)

    def test_rows_carry_the_right_keys(self):
        html = nm.expand_row_keys((self.out / "money/campaigns/index.html").read_text(encoding="utf-8"))
        row = re.search(r'<li[^>]*data-nm="([^"]*)"[^>]*>(?:(?!</li>).)*South Bend Common Council, District 1<', html, re.S)
        self.assertIsNotNone(row)
        self.assertEqual(set(row.group(1).split()), {"u:south-bend", "o:south-bend-council-d1"})
        people = nm.expand_row_keys((self.out / "people/index.html").read_text(encoding="utf-8"))
        mayor = next(t["person"] for t in self.ed.current_terms("south-bend-mayor"))
        surname = mayor.split()[-1]
        m = re.search(r'<li class="pph-row"[^>]*data-nm="([^"]*)"[^>]*>(?:(?!</li>).)*' + re.escape(surname), people, re.S)
        self.assertIsNotNone(m)
        self.assertIn("o:south-bend-mayor", m.group(1).split())

    def test_excluded_pages_have_no_navigator(self):
        for p in EXCLUDED:
            html = (self.out / p).read_text(encoding="utf-8")
            self.assertNotIn('class="nm', html, p)

    # ------------------------------------------------------------------ the parts
    def test_tags_edge_cases(self):
        t = nm.Tags(self.ed)
        self.assertEqual(t.office("no-such-office"), "")
        self.assertEqual(t.unit("no-such-unit"), "")
        court = next(o["office_id"] for o in self.ed.tables["offices"] if o["unit_id"] == "sjc-courts")
        self.assertEqual(set(t.office(court).split()) & {"u:county", "u:sjc-courts"}, {"u:county", "u:sjc-courts"})
        statewide = next(o["office_id"] for o in self.ed.tables["offices"] if o["unit_id"] == "in-state")
        self.assertIn("lvl:statewide", t.office(statewide).split())
        money_only = next(g for g in gm.governments(self.ed) if not g.unit_id)
        self.assertEqual(t.gov(money_only), f"g:{money_only.gid}")
        self.assertIn(f"g:{money_only.gid}", t.used)

    def test_navigator_edge_cases(self):
        page = self.site.page("learn/index.html")
        empty = nm.Tags(self.ed)
        self.assertIsNone(nm.navigator(page, empty, "x", noun="row", plural="rows"), "no tagged row: no map")
        t = nm.Tags(self.ed)
        t.unit("sjcpl")                          # a library: no boundary file
        money_only = next(g for g in gm.governments(self.ed) if not g.unit_id)
        t.gov(money_only)
        out = str(nm.navigator(page, t, "x", noun="row", plural="rows"))
        self.assertIn('data-nm-key="u:sjcpl"', out)
        self.assertIn(f'data-nm-key="g:{money_only.gid}"', out)
        # no drawn area used: no map, only the chips, under a plain heading, and no word about layers
        self.assertNotIn("<svg", out)
        self.assertIn('<p class="nm-others-h">Areas</p>', out)
        self.assertNotIn("Not on the map", out)
        self.assertNotIn("layer", out)
        t.unit("south-bend")
        out = str(nm.navigator(page, t, "x", noun="row", plural="rows", folded=True))
        self.assertIn("<svg", out)
        self.assertIn("Not on the map", out)
        self.assertIn('<details class="nm-fold"', out)
        self.assertNotIn('nm-fold" open', out)

    def test_row_keys_are_written_once_per_page(self):
        raw = (self.out / "elections/results/index.html").read_text(encoding="utf-8")
        self.assertIn("data-nm-dict=", raw)
        self.assertNotRegex(raw, r' data-nm="[^"]*:', "no full key on a row")
        self.assertLess(len(raw.encode("utf-8")), 700_000)
        # round trip, and a page with no navigator is untouched
        html = '<div class="nm" id="nm" data-nm-target="x"></div><li data-nm="u:a o:b"></li><li data-nm="o:b"></li>'
        small = nm.compact_row_keys(html)
        self.assertIn('data-nm-dict="u:a o:b" data-nm-target="x"', small)
        folded = nm.compact_row_keys('<div class="nm nm-folded" data-nm-target="x"></div><li data-nm="u:a"></li>')
        self.assertIn('<div class="nm nm-folded" data-nm-dict="u:a" data-nm-target="x">', folded)
        for p in ("money/campaigns/all-filings/index.html", "elections/calendar/index.html"):   # folded pages
            self.assertIn("data-nm-dict=", (self.out / p).read_text(encoding="utf-8"), p)
        self.assertIn('<li data-nm="0 1">', small)
        self.assertIn('<li data-nm="1">', small)
        self.assertEqual(nm.expand_row_keys(small).replace(' data-nm-dict="u:a o:b"', ""), html)
        self.assertEqual(nm.compact_row_keys('<li data-nm="u:a"></li>'), '<li data-nm="u:a"></li>')
        self.assertEqual(nm._b36(0), "0")
        self.assertEqual(nm._b36(36), "10")

    def test_script_contract(self):
        js = (SITE_DIR / "static" / "js" / "navmap.js").read_text(encoding="utf-8")
        self.assertTrue(js.isascii())
        self.assertNotIn("innerHTML", js)
        self.assertNotIn("localStorage", js, "the saved place is read only through civicHere")
        for needle in ("civicHere", "hashWins", "data-here-pre", "tf-scope", "nm-scope", "aria-current"):
            self.assertIn(needle, js)
        # "Show every ..." hides itself: focus goes back to the area that was selected, never to the page top
        # (found in the keyboard walk-through, 2026-11-18)
        self.assertIn("back.focus()", js)
        self.assertIn('getAttribute("data-nm-dict")', js)
        css = (SITE_DIR / "static" / "css" / "navmap.css").read_text(encoding="utf-8")
        self.assertIsNone(check.COLOR_RE.search(re.sub(r"/\*.*?\*/", "", css, flags=re.S)), "navmap.css: literal colour")

    def test_checker_catches_a_use_that_names_no_shape(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "assets").mkdir()
            (d / "assets" / "navmap.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><path id="nm-a" d="M0 0Z"/></svg>',
                                                     encoding="utf-8")
            (d / "assets" / "style.css").write_text('/* TOKENS:BEGIN */ /* TOKENS:END */ @media (prefers-color-scheme: dark) {} :root[data-theme="dark"] {}',
                                                    encoding="utf-8")
            (d / "index.html").write_text('<title>t</title><svg><use href="assets/navmap.svg#nm-a"/>'
                                          '<use href="assets/navmap.svg#nm-missing"/></svg>', encoding="utf-8")
            import contextlib
            import io
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = check.run(d)
            self.assertEqual(rc, 1)
            self.assertIn("nm-missing points to a missing id in the SVG file", buf.getvalue())
            self.assertNotIn("#nm-a points", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
