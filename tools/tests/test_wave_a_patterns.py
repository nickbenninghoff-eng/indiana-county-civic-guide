"""Tests for Wave A batch 1 (2026-11-09), the shared foundation patterns:

  P3  components.see_all_fold / see_all_table   "See all N rows" fold with filters and Copy CSV
  P5  components.entity_list                     one row per entity, each a pick_one one_fold, with a words box
  P7  charts.share_bars                          small multiples of 100% share bars, never party colors
  P1  related.related_items / related_links      "More about <entity>" rail (South Bend and county pages)
  P10 related.contest_anchor / contest_href      results explorer opens one contest at #contest-<id>

The built-page tests build the pages the rail links to into a temporary folder and check every link lands.
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
from civic import related  # noqa: E402
from civic.charts import share_bars  # noqa: E402
from civic.components import entity_list, see_all_fold, see_all_table  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.html import Markup, h  # noqa: E402
from civic.shell import Site  # noqa: E402

ID_RE = re.compile(r'\sid="([^"]+)"')
SB, COUNTY, RESULTS = "places/south-bend/index.html", "county/index.html", "elections/results/index.html"


def _tag(html: str, cls: str) -> str:
    m = re.search(r'<[a-z0-9]+\b[^>]*class="[^"]*\b' + re.escape(cls) + r'\b[^"]*"[^>]*>', html)
    return m.group(0) if m else ""


# ====================================================================== P3 see-all fold
class SeeAll(unittest.TestCase):
    def test_fold_ships_open_and_is_a_fold(self):
        out = see_all_fold("x-all", 1234, h("p", None, "body"))
        tag = _tag(out, "see-all")
        self.assertTrue(tag.startswith("<details"))
        self.assertIn(" open", tag)                       # JavaScript off: the rows are on the page
        self.assertIn('data-fold="see-all"', tag)         # folds.js closes it on load, opens it for #targets
        self.assertIn('id="x-all"', tag)
        self.assertIn("See all 1,234 rows", out)
        self.assertIn("Copy CSV", out)
        self.assertIn('class="fold-toggle"', out)

    def test_nouns_and_label(self):
        self.assertIn("See all 1 row<", see_all_fold("a", 1, ""))
        self.assertIn("See all 3 committees", see_all_fold("a", 3, "", noun="committee"))
        self.assertIn("See all 2 people", see_all_fold("a", 2, "", noun="person", plural="people"))
        self.assertIn(">Every row<", see_all_fold("a", 2, "", label="Every row"))
        self.assertNotIn("see-all-hint", see_all_fold("a", 2, "", hint=None))

    def test_table_with_filters(self):
        rows = [["2024", "A"], ["2022", "B"]]
        out = see_all_table("t1", ["Year", "Name"], rows, noun="race", row_attrs=[{"data-tf-year": "2024"}, {"data-tf-year": "2022"}],
                            controls=[{"key": "year", "label": "Year", "options": [("2024", "2024"), ("2022", "2022")]}],
                            search="Words")
        self.assertIn('id="t1-all"', out)
        self.assertIn('id="t1"', out)
        self.assertIn('id="t1-copy"', out)                # Copy CSV inside the fold
        self.assertIn('data-tf-table="t1"', out)          # the same table_filter bar
        self.assertIn('data-tf-empty="t1"', out)
        self.assertIn('data-tf-year="2024"', out)
        self.assertIn("Filters · Copy CSV", out)
        self.assertIn("See all 2 races", out)
        # the filter bar comes before the table, inside the fold
        self.assertLess(out.index('data-tf-table="t1"'), out.index('<table id="t1"'))

    def test_table_without_filters_has_no_bar(self):
        out = see_all_table("t2", ["A"], [["x"]], fold_id="f2", summary="All of it")
        self.assertIn('id="f2"', out)
        self.assertNotIn("data-tf-table", out)
        self.assertIn(">All of it<", out)


# ====================================================================== P5 entity list
class EntityList(unittest.TestCase):
    def setUp(self):
        self.items = [
            {"key": "a", "name": "Ann Example", "facts": ["Mayor 1980-1988", Markup("<em>R &amp; D</em>")],
             "status": "official", "body": h("p", None, "Card A"), "item_id": "person-a", "search": "alias words",
             "attrs": {"data-tf-era": "1980s"}},
            {"key": "b", "name": "Bo Example", "facts": [], "status": None, "body": "Card B"},
        ]

    def test_rows_are_one_folds(self):
        out = entity_list("people", self.items, noun="person", plural="people")
        self.assertEqual(out.count("<details"), 2)
        self.assertEqual(out.count('data-fold="one"'), 2)
        self.assertIn('data-one="a"', out)
        self.assertIn('id="person-a"', out)
        self.assertIn('data-one-name="Ann Example"', out)
        self.assertEqual(len(re.findall(r'<details[^>]*\sopen', out)), 2)   # ship open
        self.assertIn('<ul class="one-list ent-list" id="people"', out)
        self.assertIn('data-tf-era="1980s"', out)

    def test_summary_line(self):
        out = entity_list("people", self.items)
        summ = re.search(r"<summary.*?</summary>", out, re.S).group(0)
        self.assertIn('<h3 class="one-h ent-name">Ann Example</h3>', summ)
        self.assertIn("Mayor 1980-1988", summ)
        self.assertIn("<em>R &amp; D</em>", summ)
        self.assertIn("badge-official", summ)
        self.assertNotIn("<a ", summ)                     # no link inside <summary>
        self.assertNotIn("Card A", summ)

    def test_search_box_and_words(self):
        out = entity_list("people", self.items, search="Find a name", noun="person", plural="people")
        self.assertIn('data-tf-table="people"', out)
        self.assertIn('data-tf-empty="people"', out)
        self.assertIn("No people match", out)
        words = re.search(r'data-tf-text="([^"]*)"', out).group(1)
        self.assertIn("Ann Example", words)
        self.assertIn("R &amp; D", words)                 # escaped once in the attribute, plain text to the script
        self.assertNotIn("&amp;amp;", words)
        self.assertNotIn("<em>", words)
        self.assertIn("alias words", words)
        self.assertEqual(out.count("data-tf-row"), 2)

    def test_no_search_no_bar(self):
        out = entity_list("people", self.items)
        self.assertNotIn("data-tf-table", out)
        self.assertNotIn("data-tf-text", out)


# ====================================================================== P7 share bars
class ShareBars(unittest.TestCase):
    SERIES = [{"key": "u", "label": "Uncontested"}, {"key": "c", "label": "Under 5 points"},
              {"key": "s", "label": "5 points or more"}]

    def chart(self, **kw):
        groups = [{"label": "County", "counts": {"u": 3, "c": 1, "s": 4}, "href": "#county"},
                  {"label": "Township", "counts": {"u": 0, "c": 2, "s": 0}},
                  {"label": "Town", "counts": {}}]
        return share_bars("sb", "How close", groups, self.SERIES, noun=("race", "races"), **kw)

    def test_figure_contract(self):
        out = self.chart()
        self.assertTrue(out.startswith('<figure class="chart chart-share" id="sb"'))
        self.assertIn('<ul class="legend">', out)          # 2+ series: legend
        self.assertIn('id="sb-table"', out)                # table view
        self.assertIn('class="chart-table"', out)
        self.assertIn('<a href="#county">County</a>', out)  # drill-down link on the label
        self.assertIn("8 races", out)
        self.assertIn("2 races", out)
        self.assertIn("No races in the guide&#x27;s data.", out)

    def test_no_party_colors(self):
        out = self.chart()
        self.assertNotRegex(out, r"m-party|party-")
        self.assertIn("m-share-0", out)
        self.assertIn("m-share-a1", self.chart(ramp="alt"))

    def test_segments_and_counts(self):
        out = self.chart()
        county = re.search(r'<li class="shb-row".*?</li></ul></div></li>', out, re.S).group(0)
        self.assertEqual(re.findall(r"flex-grow: (\d+)", county), ["3", "1", "4"])
        self.assertIn('aria-hidden="true"', _tag(county, "shb-bar"))
        self.assertNotIn("tabindex", county)                # counts are text; segments are not tab stops
        self.assertIn(">3</span> Uncontested", county)
        self.assertIn("(38%)", county)                      # 3 of 8
        twp = out.split('<li class="shb-row"')[2]
        self.assertEqual(re.findall(r"flex-grow: (\d+)", twp), ["2"])   # a zero part draws nothing
        self.assertIn("shb-c-zero", twp)                    # ...but its 0 is still printed

    def test_table_rows(self):
        out = self.chart()
        table = re.search(r'<table id="sb-table".*?</table>', out, re.S).group(0)
        self.assertIn("<th scope=\"col\" class=\"num\">Total</th>", table)
        self.assertIn("3 (38%)", table)
        self.assertIn(">8<", table)

    def test_one_series_no_legend_and_limits(self):
        one = share_bars("s1", "T", [{"label": "A", "counts": {"x": 1}}], [{"key": "x", "label": "X"}])
        self.assertNotIn('class="legend"', one)
        with self.assertRaises(ValueError):
            share_bars("s2", "T", [], [{"key": str(i), "label": str(i)} for i in range(5)])
        with self.assertRaises(ValueError):
            share_bars("s3", "T", [], self.SERIES, ramp="party")
        self.assertIn("m-nodata", share_bars("s4", "T", [{"label": "A", "counts": {"x": 1}}],
                                             [{"key": "x", "label": "X", "mark": "m-nodata"}, {"key": "y", "label": "Y"}]))


# ====================================================================== P1 / P10 helpers (no build)
class RelatedRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.site = Site(cls.ed, Path(tempfile.gettempdir()) / "unused")

    def page(self, path):
        return self.site.page(path)

    def test_contest_anchor(self):
        self.assertEqual(related.contest_anchor("2023g-south-bend-mayor"), "contest-2023g-south-bend-mayor")
        with self.assertRaises(ValueError):
            related.contest_anchor("bad id")

    def test_contest_href_only_for_explorer_contests(self):
        p = self.page(SB)
        self.assertEqual(related.contest_href(p, "2023g-south-bend-mayor"),
                         "../../elections/results/index.html#contest-2023g-south-bend-mayor")
        self.assertIsNone(related.contest_href(p, "1963g-south-bend-mayor"))   # before the explorer's first year
        self.assertIsNone(related.contest_href(p, "no-such-contest"))

    def test_rules_match_the_pages_that_print_the_ids(self):
        from civic.answers import HEAD_OFFICE
        from pages import elections, participate
        self.assertEqual(related.RESULTS_FROM, elections.RESULTS_FROM)
        self.assertEqual(list(related.CALENDAR_YEARS), list(elections.YEARS))
        self.assertEqual(related.HEAD_TYPE, HEAD_OFFICE)
        for ot, slug in related.RUN_FOR_TYPE.items():
            self.assertIn(ot, participate.OFFICES[slug]["types"], ot)

    def test_south_bend_items(self):
        items = related.related_items(self.page(SB), "south-bend")
        keys = [i.key for i in items]
        self.assertNotIn("place", keys)                    # never a link to the page itself
        for k in ("results", "campaigns", "budget", "community", "run", "calendar"):
            self.assertIn(k, keys)
        self.assertEqual(keys, [k for k in related.ORDER if k in keys])
        res = next(i for i in items if i.key == "results")
        self.assertTrue(res.href.endswith("#contest-2023g-south-bend-mayor"))

    def test_other_page_links_back_to_the_place(self):
        items = related.related_items(self.page("money/campaigns/south-bend/index.html"), "south-bend")
        self.assertEqual(items[0].key, "place")
        self.assertEqual(items[0].href, "../../../places/south-bend/index.html")
        self.assertNotIn("campaigns", [i.key for i in items])

    def test_office_rail(self):
        keys = [i.key for i in related.related_items(self.page("state/your-legislators/index.html"), office_id="state-house-5")]
        self.assertIn("results", keys)
        self.assertIn("campaigns", keys)
        self.assertNotIn("budget", keys)
        with self.assertRaises(KeyError):
            related.related_items(self.page(SB), office_id="no-such-office")

    def test_only_what_exists(self):
        p = self.page(SB)
        units = [u for u, r in self.ed.units.items()
                 if r["unit_type"] in ("city", "town", "township", "county", "school_corporation")]
        # a unit with no money rows gets no budget or tax-rate link; one with no census rows no community link
        for uid in units:
            keys = [i.key for i in related.related_items(p, uid)]
            if not related._money_ids(self.ed, uid):
                self.assertNotIn("budget", keys, uid)
                self.assertNotIn("tax-rate", keys, uid)
            if related._community(self.ed, self.ed.units[uid]) is None:
                self.assertNotIn("community", keys, uid)
            for i in related.related_items(p, uid):
                path, _, frag = i.href.partition("#")
                self.assertNotIn("?", i.href)
                self.assertTrue(path.endswith(".html"), i.href)
                if frag:
                    self.assertRegex(frag, r"^[A-Za-z0-9-]+$")

    def test_rail_markup_and_exclude(self):
        p = self.page(SB)
        out = related.related_links(p, "south-bend")
        self.assertIn('<nav class="related" id="related" aria-labelledby="related-h">', out)
        self.assertIn(">More about South Bend</h2>", out)
        self.assertIn('data-related="budget"', out)
        self.assertNotIn('data-related="budget"', related.related_links(p, "south-bend", exclude=("budget",)))
        self.assertIsNone(related.related_links(p, "south-bend", exclude=related.ORDER))


# ====================================================================== built pages
class Built(unittest.TestCase):
    """Build the two rail pages, the results page and every page the rails link to; every rail link lands."""

    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        site = Site(cls.ed, cls.out)
        build.discover_builders()
        targets = {SB, COUNTY, RESULTS}
        probe = Site(cls.ed, cls.out)
        for path, uid in ((SB, "south-bend"), (COUNTY, "county")):
            for i in related.related_items(probe.page(path), uid):
                targets.add(i.href and (Path(path).parent / i.href.split("#")[0]).as_posix())
        # Wave C batch 7: the county rail adds links of its own (pages/county.py COUNTY_RAIL_EXTRA)
        from pages.county import COUNTY_RAIL_EXTRA
        targets.update(t.partition("#")[0] for *_, t in COUNTY_RAIL_EXTRA)
        cls.targets = sorted({cls._norm(t) for t in targets})
        for p in cls.targets:
            build.BUILDERS[p](site)
        site.write()
        cls.html = {p: (cls.out / p).read_text(encoding="utf-8") for p in cls.targets}

    @staticmethod
    def _norm(p: str) -> str:
        parts = []
        for seg in p.split("/"):
            if seg == "..":
                parts.pop()
            elif seg and seg != ".":
                parts.append(seg)
        return "/".join(parts)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_rail_link_lands(self):
        for page in (SB, COUNTY):
            html = self.html[page]
            nav = re.search(r'<nav class="related".*?</nav>', html, re.S)
            self.assertIsNotNone(nav, page)
            hrefs = re.findall(r'href="([^"]+)"', nav.group(0))
            self.assertGreaterEqual(len(hrefs), 5, page)
            for href in hrefs:
                path, _, frag = href.partition("#")
                target = self._norm((Path(page).parent / path).as_posix())
                self.assertIn(target, self.html, href)
                if frag:
                    self.assertIn(frag, ID_RE.findall(self.html[target]), href)

    def test_rail_sits_after_at_a_glance(self):
        for page in (SB, COUNTY):
            html = self.html[page]
            self.assertLess(html.index('id="glance"'), html.index('id="related"'))
            self.assertLess(html.index('id="related"'), html.index('class="toc"'))

    def test_results_rows_carry_contest_ids(self):
        html = self.html[RESULTS]
        raw = re.search(r'<script type="application/json" id="elx-data">(.*?)</script>', html, re.S).group(1)
        data = json.loads(raw.replace("<\\/", "</"))
        # the payload ships the id without its election prefix ("i"; "fi" = the whole id), elections.js rebuilds it
        ids = [c["i"] if c.get("fi") else f'{c["e"]}-{c["i"]}' for c in data["contests"]]
        self.assertEqual(len(ids), len(set(ids)))
        page_ids = ID_RE.findall(html)
        self.assertEqual(len(page_ids), len(set(page_ids)))
        rows = {i[len("contest-"):] for i in page_ids if i.startswith("contest-")}
        self.assertEqual(rows, set(ids))                    # every explorer contest has its row, and only those
        for cid in ids:
            self.assertTrue(related.in_results(self.ed, cid), cid)
        fold = _tag(html, "see-all")
        self.assertIn(" open", fold)
        self.assertIn('id="every-contest-all"', fold)
        self.assertIn('data-tf-table="every-contest"', html)
        self.assertIn('id="every-contest-copy"', html)

    def test_rail_never_uses_party_classes(self):
        for page in (SB, COUNTY):
            nav = re.search(r'<nav class="related".*?</nav>', self.html[page], re.S).group(0)
            self.assertNotIn("party", nav)


# ====================================================================== scripts and styles
class Static(unittest.TestCase):
    def read(self, rel):
        return (SITE_DIR / rel).read_text(encoding="utf-8")

    def test_scripts_ascii_no_innerhtml(self):
        for rel in ("static/js/elections.js", "static/js/tablefilter.js"):
            src = self.read(rel)
            self.assertTrue(all(ord(c) < 128 for c in src), rel)
            self.assertNotIn("innerHTML", src, rel)

    def test_contest_deep_link_handled(self):
        src = self.read("static/js/elections.js")
        self.assertIn("#contest-", src)
        self.assertIn("hashchange", src)
        self.assertIn("Show every contest in this election", src)
        # runs its landing step after folds.js (which comes later in app.js)
        self.assertIn("setTimeout(function () { showOne(first, true); }, 0)", src)

    def test_tablefilter_accepts_lists(self):
        self.assertIn('hasAttribute("data-tf-row")', self.read("static/js/tablefilter.js"))

    def test_css_tokens_only(self):
        css = self.read("static/css/patterns.css")
        self.assertNotRegex(css, r"#[0-9a-fA-F]{3,8}\b|rgb\(|hsl\(")
        self.assertNotRegex(css, r"party")


if __name__ == "__main__":
    unittest.main()
