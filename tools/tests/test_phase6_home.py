"""Phase 6, the home page (2026-11-18): the county map as the way in. Report: planning/qa/phase6-home-2026-11-18.md.

- The map is built only from the boundary files (derived/map_shapes.json, derived/district_shapes.json): every path on
  it is one of theirs. Layers: the county, cities and towns, townships, school corporations, county commissioner and
  council districts, city council districts, Indiana House and Senate. Fills never use party colors.
- Every area is a link with JavaScript off (to its government's or office's page) and has a panel block with its links:
  a government's tabs and offices (each to its office page) and next election; a district's holder, office tabs, last
  election page and its government.
- With JavaScript off the page still lists every government (by type) and every drawn district, in a fold that ships
  open.
- Five doors with example deep links that resolve; the next election; the learning paths at #paths.
- The home search is a second copy of the header search (same index, one script); home.js reads the saved place only
  through civicHere and inserts text with textContent.
- Every id of the earlier home page still resolves: on the page, or through #moved-anchors.
Run:  python -P -E -m unittest tools.tests.test_phase6_home   (or discover -s tools/tests -p "test_phase6_home.py")
"""
from __future__ import annotations

import json
import posixpath
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
from civic import governments as gm  # noqa: E402
from civic import sitemap  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site  # noqa: E402

from anchor_fixtures import anchor_fixture  # noqa: E402  (old-anchor fixtures without retired data-block ids)
FIXTURE = ROOT / "tools" / "tests" / "fixtures" / "anchors_before_home.json"
# the home page's size budget (bytes). The page before the redesign was 261,570 bytes with three map layers; the new
# one carries nine layers and every area's links, about 286 kB at the 2026-11-18 build.
SIZE_BUDGET = 310_000


class _Ids(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k == "id" and v:
                self.ids.add(v)


def _between(html: str, start: str, end: str) -> str:
    i = html.index(start)
    return html[i:html.index(end, i)]


class Home(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        cls.site = Site(cls.ed, cls.out)
        build.discover_builders()
        build.BUILDERS["index.html"](cls.site)
        build.BUILDERS[gm.HUB](cls.site)
        cls.site.write()
        cls.html = (cls.out / "index.html").read_text(encoding="utf-8")
        p = _Ids()
        p.feed(cls.html)
        cls.ids = p.ids
        cls.data = json.loads(_between(cls.html, '<script type="application/json" id="cmap-data">', "</script>")
                              .split(">", 1)[1])
        cls.svg = _between(cls.html, '<svg class="cmap-svg"', "</svg>")
        cls.blocks = _between(cls.html, '<div id="layer-data" class="hm-blocks"', '<script type="application/json" id="cmap-data">')

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def built(self, href: str) -> bool:
        """A link written on the home page (relative to the site root) names a page in the sitemap."""
        path = posixpath.normpath(href.split("#")[0])
        return path in self.site.by_path

    # ------------------------------------------------------------------ the map
    def test_layers(self):
        tabs = re.findall(r'<button type="button" class="cmap-tab" data-layer="([a-z-]+)"', self.html)
        # 2026-11-18: + Statewide and Federal (the county outline with a label; no new geometry)
        self.assertEqual(tabs, ["cities", "townships", "schools", "commissioners", "council",
                                "city-council", "house", "senate", "statewide", "federal"])
        self.assertIn('id="home-map"', self.html)
        self.assertRegex(self.html, r'class="cmap dmap hm" id="home-map" data-default-layer="cities" data-hash="off"')
        self.assertEqual(self.html.count('class="cmap '), 1, "map.js drives the first .cmap on a page: only one")

    def test_no_new_geometry(self):
        shapes = json.loads((ROOT / "data/editions/st-joseph/derived/map_shapes.json").read_text(encoding="utf-8"))
        dshapes = json.loads((ROOT / "data/editions/st-joseph/derived/district_shapes.json").read_text(encoding="utf-8"))
        known = {shapes["county"]["d"]}
        for items in shapes["layers"].values():
            known |= {it["d"] for it in items}
        for rec in dshapes["sets"].values():
            known |= {it["d"] for it in rec["items"]}
        ds = re.findall(r'<path d="([^"]+)"', self.svg)
        self.assertGreater(len(ds), 60)
        for d in ds:
            self.assertIn(d, known, "every path on the home map comes from the boundary files")

    def test_never_party_colors(self):
        self.assertNotRegex(self.svg, r"party-|--party")
        for cls in re.findall(r'<path d="[^"]+" class="([^"]+)"', self.svg):
            for c in cls.split():
                self.assertTrue(c.startswith(("cmap-", "dmap-", "hm-")), c)

    def test_every_area_is_a_link_with_a_panel_block(self):
        areas = re.findall(r'<a href="([^"]+)" class="cmap-a" data-uid="([^"]+)"', self.svg)
        self.assertEqual(len(areas), len(self.data))
        self.assertGreater(len(areas), 60)
        for href, uid in areas:
            self.assertTrue(self.built(href), f"{uid}: {href}")
            self.assertEqual(self.data[uid]["href"], href)
            self.assertIn(f'data-hm-uid="{uid}"', self.blocks, uid)
        # the panel's button href is how home.js finds an area's block: unique per area
        hrefs = [e["href"] for e in self.data.values()]
        self.assertEqual(len(hrefs), len(set(hrefs)))

    def test_government_blocks(self):
        sb = _between(self.blocks, 'data-hm-uid="south-bend"', "</div>")
        for k in gm.gov_tabs(self.ed, "south-bend"):
            if k not in ("overview", "sources"):
                self.assertIn(f'href="governments/south-bend/{k}/index.html"', sb)
        self.assertIn('href="offices/south-bend-mayor/index.html"', sb)
        self.assertIn('class="name-party"', sb)                       # holders with their party tag
        self.assertIn('data-hm-layer="city-council"', sb)              # its district seats' layer
        self.assertIn("Next election", sb)

    def test_county_is_a_row_above_the_map_not_a_layer(self):
        # owner, 2026-11-18: "Plain link above is fine"
        self.assertNotIn('data-layer="countywide"', self.html)
        self.assertNotIn('"county"', json.dumps(list(self.data)))
        row = _between(self.html, '<p class="hm-county-row" id="county-row">', "</p>")
        self.assertIn('href="governments/county/index.html"', row)
        for k in gm.gov_tabs(self.ed, "county"):
            if k not in ("overview", "sources"):
                self.assertIn(f'href="governments/county/{k}/index.html"', row)
        self.assertIn('href="offices/index.html#county"', row)
        self.assertIn('href="governments/county/index.html#courts"', row)
        self.assertLess(self.html.index('id="county-row"'), self.html.index('id="home-map"'))

    def test_panel_start_state_lists_the_layer_areas(self):
        """Before an area is chosen the panel says how to use the map and lists every area of the shown layer,
        alphabetically (numbers in order), each a link; no area is preselected."""
        panel = _between(self.html, '<aside class="cmap-panel hm-panel"', "</aside>")
        self.assertNotIn("cmap-open", panel)
        lists = re.findall(r'<div class="hm-start-list( is-on)?" data-hm-list="([a-z-]+)">(.*?)</ul></div>', panel)
        self.assertEqual([t for _on, t, _b in lists], ["cities", "townships", "schools", "commissioners", "council",
                                                       "city-council", "house", "senate", "statewide", "federal"])
        self.assertEqual([t for on, t, _b in lists if on], ["cities"])
        for _on, tab, body in lists:
            picks = re.findall(r'<a href="([^"]+)" data-hm-pick="([^"]+)">([^<]+)</a>', body)
            on_layer = [u for u, e in self.data.items() if e["l"] == tab]
            self.assertEqual(sorted(p[1] for p in picks), sorted(on_layer), tab)
            for href, uid, _name in picks:
                self.assertEqual(href, self.data[uid]["href"])
        cities = re.findall(r'data-hm-pick="[^"]+">([^<]+)<', lists[0][2])
        self.assertEqual(cities, sorted(cities, key=str.lower))
        from pages.landing import _natural
        for _on, tab, body in lists:            # districts: numbers in numeric order (District 2 before District 10)
            names = re.findall(r'data-hm-pick="[^"]+">([^<]+)<', body)
            self.assertEqual(names, sorted(names, key=_natural), tab)
        self.assertEqual(_natural("District 2") < _natural("District 10"), True)

    def test_one_count_everywhere(self):
        """The headline, the home list and the Governments hub give the same number with the same words
        (civic/governments.py count)."""
        c = gm.count(self.ed)
        self.assertEqual(c["n"], len(gm.governments(self.ed)))
        phrase = f'{c["n"]} {c["noun"]}'
        hero = _between(self.html, '<h1 id="hero-h"', "</h1>")
        self.assertIn(phrase + ".", hero)
        self.assertIn(phrase + ", each with its page", _between(self.html, '<details class="home-list"', "</summary>"))
        hub = (self.out / gm.HUB).read_text(encoding="utf-8")
        self.assertIn(phrase + " in ", _between(hub, '<p class="thing-facts">', "</p>"))
        self.assertIn(c["parts"], hub)
        self.assertIn(c["parts"], self.html)
        # what is counted: every government page; never the courts, the board of health or the housing authorities
        ids = {g.gid for g in gm.governments(self.ed)}
        for out in ("sjc-courts", "sjc-board-of-health", "south-bend-housing-authority", "in-house"):
            self.assertNotIn(out, ids)

    def test_district_blocks(self):
        b = _between(self.blocks, 'data-hm-uid="d-county-council-a"', "</div>")
        self.assertIn("Held by", b)
        self.assertIn('href="offices/county-council-a/elections/index.html"', b)
        self.assertIn('href="offices/county-council-a/money/index.html"', b)
        self.assertRegex(b, r'href="elections/[^"/]+/index.html"')    # its last election's page
        self.assertIn('href="governments/county/index.html"', b)
        for href in re.findall(r'href="([^"]+)"', self.blocks):
            self.assertTrue(self.built(href), href)

    # ------------------------------------------------------------------ without JavaScript
    def test_plain_list_of_every_government(self):
        lst = _between(self.html, '<details class="home-list" id="list"', "</details>")
        self.assertIn("open", lst[:120])
        self.assertIn('data-fold="home-list"', lst[:120])
        for g in gm.governments(self.ed):
            self.assertIn(f'href="governments/{g.gid}/index.html"', lst, g.gid)
        for uid, e in self.data.items():
            if uid.startswith("d-"):
                self.assertIn(f'href="{e["href"]}"', lst, uid)

    def test_js_only_parts_ship_hidden(self):
        self.assertRegex(self.html, r'<div class="cmap-tabs hm-tabs-bar" role="group" aria-label="Map layer" hidden>')
        self.assertRegex(self.html, r'<form class="search-form home-search-form" id="home-search-form"[^>]* hidden')
        self.assertRegex(self.html, r'<div id="layer-data" class="hm-blocks" hidden>')

    # ------------------------------------------------------------------ doors, next ballot, paths
    def test_doors(self):
        doors = _between(self.html, 'id="doors"', "</section>")
        for key in ("governments", "offices", "elections", "money", "learn"):
            self.assertIn(f'id="door-{key}"', doors)
        hrefs = re.findall(r'href="([^"]+)"', doors)
        self.assertGreaterEqual(len(hrefs), 5 + 10)
        for href in hrefs:
            self.assertTrue(self.built(href), href)
        self.assertIn("Mayor of South Bend › Money", doors)

    def test_next_ballot_and_paths(self):
        self.assertIn('id="next-ballot"', self.html)
        if "learn/index.html" in self.site.by_path:
            # the learning paths live on the Learn hub; the old #paths forwards there and the Learn door links them
            self.assertNotIn('id="paths"', self.html)
            self.assertIn('href="learn/index.html#paths"', _between(self.html, 'id="door-learn"', "</li></ul></li>"))
        else:
            self.assertIn('id="paths"', self.html)
            for p in sitemap.PATHS:
                self.assertIn(f'href="{p["stops"][0]["page"]}#path-{p["id"]}-1"', self.html)

    def test_links_to_your_place(self):
        self.assertIn('href="your-governments/index.html"', _between(self.html, 'id="your-govs"', "</details>"))

    def test_picker_kept_for_old_links(self):
        # Your place links here (index.html#pick) to choose a place; here.js drives the picker
        self.assertRegex(self.html, r'<details class="home-pick" id="pick">')
        self.assertIn("data-picker", self.html)

    def test_search_box(self):
        for i in ("home-search-input", "home-search-pop", "home-search-list", "home-search-status"):
            self.assertIn(f'id="{i}"', self.html)
        self.assertIn('data-index="assets/search-index.json"', _between(self.html, 'id="home-search"', "</form>"))
        js = (SITE_DIR / "static" / "js" / "search.js").read_text(encoding="utf-8")
        self.assertIn('form: "home-search-form"', js)
        self.assertIn('form: "search-form"', js)
        self.assertEqual(js.count("window.fetch(url)"), 1, "one load of the index for every box")

    # ------------------------------------------------------------------ old ids
    def test_every_old_anchor_resolves(self):
        old = anchor_fixture(FIXTURE)["ids"]
        moved = json.loads(_between(self.html, '<script type="application/json" id="moved-anchors">', "</script>")
                           .split(">", 1)[1])
        missing = []
        for i in old:
            if i in self.ids:
                continue
            dest = moved["a"].get(i) or next((v for k, v in moved.get("p", {}).items() if i.startswith(k)), None)
            if not dest:
                missing.append(i)
                continue
            self.assertTrue(self.built(dest), f"{i} -> {dest}")
        self.assertEqual(missing, [])

    def test_size_budget(self):
        self.assertLess(len(self.html.encode("utf-8")), SIZE_BUDGET)


class Static(unittest.TestCase):
    def test_home_js(self):
        src = (SITE_DIR / "static" / "js" / "home.js").read_text(encoding="utf-8")
        self.assertTrue(src.isascii())
        self.assertNotIn("innerHTML", src)
        self.assertNotIn("localStorage", src, "the saved place is read through civicHere only")
        for s in ("civicHere.mine()", '"cmap-select"', '"civic:place"', "data-hm-uid", '"layer-data"', '"Escape"'):
            self.assertIn(s, src)

    def test_home_css_tokens_only(self):
        css = (SITE_DIR / "static" / "css" / "home.css").read_text(encoding="utf-8")
        self.assertTrue(css.isascii())
        self.assertNotRegex(css, r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")


if __name__ == "__main__":
    unittest.main()
