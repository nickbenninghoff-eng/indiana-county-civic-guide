"""Tests for the 2026-11-09 page-organization fixes: the data page split, the sources index page, the
shared table filters and the collapsible Gaps / Sources sections.

Builds the affected pages into a temporary folder (no dependence on other pages' builders).
Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import html
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "site"))

import build  # noqa: E402
from civic import sitemap  # noqa: E402
from civic.components import Citations, fold_section, gaps_section, table_filter  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "anchors_before_page_split.json"
ID_RE = re.compile(r'\sid="([^"]+)"')
HREF_RE = re.compile(r'<a\b[^>]*\shref="([^"]+)"')

PAGES = ["data/index.html", "data/pull/index.html", "about/index.html", "about/sources/index.html",
         "elections/landscape/index.html", "elections/calendar/index.html"] + \
        [f"data/{slug}/index.html" for slug, _, _ in sitemap.DATA_PAGES]


class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        site = Site(cls.ed, cls.out)
        build.discover_builders()
        for p in PAGES:
            build.BUILDERS[p](site)
        site.write()
        cls.html = {p: (cls.out / p).read_text(encoding="utf-8") for p in PAGES}
        cls.ids = {p: set(ID_RE.findall(h)) for p, h in cls.html.items()}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # ---------------------------------------------------------------- anchors
    def test_every_old_anchor_still_resolves(self):
        """Each id the old pages carried is still on its page, or is forwarded: data ids by the moved-anchors map
        (static/js/moved.js), about source ids by the about/ -> about/sources/ rule."""
        before = json.loads(FIXTURE.read_text(encoding="utf-8"))["ids"]
        moved = json.loads(re.search(r'id="moved-anchors">(.*?)</script>', self.html["data/index.html"]).group(1).replace("<\\/", "</"))
        lost = []
        for page, ids in before.items():
            if page in ("elections/landscape/index.html",):
                continue  # only the five obsolete filter controls (mg-*) changed; see test_old_margin_controls
            for i in ids:
                if i in self.ids[page]:
                    continue
                if page == "data/index.html":
                    dest = moved["a"].get(i) or (moved["src"].get(i[4:]) if i.startswith("src-") else None)
                    if dest and i in self.ids["data/" + dest]:
                        continue
                elif page == "about/index.html" and re.match(r"(src-|sources-)", i) and i in self.ids["about/sources/index.html"]:
                    continue
                lost.append((page, i))
        self.assertEqual(lost, [])

    def test_calendar_ids_unchanged(self):
        before = json.loads(FIXTURE.read_text(encoding="utf-8"))["ids"]["elections/calendar/index.html"]
        self.assertEqual([i for i in before if i not in self.ids["elections/calendar/index.html"]], [])

    def test_old_margin_controls_replaced(self):
        before = set(json.loads(FIXTURE.read_text(encoding="utf-8"))["ids"]["elections/landscape/index.html"])
        gone = before - self.ids["elections/landscape/index.html"]
        self.assertEqual(gone, {"mg-year", "mg-type", "mg-band", "mg-sort", "mg-count"})
        for suffix in ("year", "type", "band", "office", "place", "district", "q", "sort"):
            self.assertIn(f"tf-margins-table-{suffix}", self.ids["elections/landscape/index.html"])

    def test_path_stop_anchors(self):
        for p in sitemap.PATHS:
            for s in p["stops"]:
                if s["page"] in self.ids:
                    self.assertIn(s["anchor"], self.ids[s["page"]], (p["id"], s))

    def test_index_keeps_dataset_anchors(self):
        for spec in __import__("pages.meta", fromlist=["DATASETS"]).DATASETS:
            self.assertIn(spec[1], self.ids["data/index.html"])
            self.assertIn(f"{spec[1]}-h", self.ids["data/index.html"])

    def test_no_duplicate_ids_on_changed_pages(self):
        for p, h in self.html.items():
            ids = ID_RE.findall(h)
            dup = {i for i in ids if ids.count(i) > 1}
            self.assertEqual(dup, set(), p)

    # ---------------------------------------------------------------- data split
    def test_one_page_per_dataset_with_copy_csv(self):
        from pages.meta import DATASETS, _publish_rows
        for spec in DATASETS:
            slug = spec[1][3:]
            h = self.html[f"data/{slug}/index.html"]
            cols, rows, _ = _publish_rows(self.ed, spec[0])
            if not rows:
                continue
            self.assertIn(f'data-copy-csv="{spec[1]}-csv"', h, slug)
            self.assertIn(f'id="{spec[1]}-csv"', h, slug)
            self.assertIn(f"{len(rows):,} rows", h, slug)
            self.assertIn(f'href="../index.html#tables"', h, slug)

    def test_index_is_small_and_lists_every_dataset(self):
        h = self.html["data/index.html"]
        self.assertLess(len(h), 150_000)
        self.assertNotIn("data-copy-csv", h)
        for slug, _, _ in sitemap.DATA_PAGES:
            self.assertIn(f'href="{slug}/index.html"', h)
        self.assertIn('id="sources"', h)
        self.assertIn('id="pull"', h)

    def test_dataset_slugs_match_sitemap(self):
        from pages.meta import DATASETS
        self.assertEqual([s[1][3:] for s in DATASETS], [s for s, _, _ in sitemap.DATA_PAGES])

    # ---------------------------------------------------------------- sources index
    def test_sources_page_has_full_list_and_search(self):
        h = self.html["about/sources/index.html"]
        n = len(re.findall(r'<li id="src-', h))
        self.assertGreater(n, 800)
        self.assertIn("data-src-search", h)
        self.assertRegex(h, r'<div class="picker tf srcq"[^>]*\bhidden\b')   # shown by script only
        self.assertIn(f"{n} of {n} sources shown", h)

    def test_about_citations_land_on_sources_page(self):
        h = self.html["about/index.html"]
        cites = re.findall(r'<sup class="cite"><a href="([^"]+)"', h)
        self.assertTrue(cites)
        for href in cites:
            page, _, frag = href.partition("#")
            self.assertEqual(page, "sources/index.html")
            self.assertIn(frag, self.ids["about/sources/index.html"])
        self.assertNotIn('id="src-', h)

    def test_about_keeps_sources_pointer(self):
        self.assertIn("sources", self.ids["about/index.html"])
        self.assertIn('href="sources/index.html"', self.html["about/index.html"])
        self.assertLess(len(self.html["about/index.html"]), 150_000)

    # ---------------------------------------------------------------- folds
    def test_fold_markup(self):
        c = Citations(self.ed)
        c.cite("RES-001;RES-002")
        h = str(c.render())
        self.assertIn('<details class="fold-details" open data-fold="sources">', h)
        self.assertRegex(h, r'<h2 id="sources-h">Sources on this page <span class="fold-count">\(2\)</span></h2>')
        g = str(gaps_section([{"item": "x", "why_missing": "y", "how_to_fill": "z"}]))
        self.assertRegex(g, r'Gaps on this page <span class="fold-count">\(1\)</span>')
        self.assertIn('id="gaps"', g)
        self.assertIn("(0)", str(gaps_section([])))
        self.assertIn('id="x-h"', str(fold_section("sources", "x", "X", 3, None, "body")))

    def test_citation_links_resolve_in_fold(self):
        """Every in-page #src- link lands on an id that exists on the page (inside the fold)."""
        for p in ("elections/landscape/index.html", "elections/calendar/index.html", "data/results/index.html"):
            h = self.html[p]
            for frag in HREF_RE.findall(h):
                if frag.startswith("#src-"):
                    self.assertIn(frag[1:], self.ids[p], (p, frag))
            self.assertRegex(h, r'<section class="sources fold" id="sources"')

    def test_citation_base(self):
        c = Citations(self.ed)
        c.href_base = "sources/index.html"
        self.assertIn('href="sources/index.html#src-RES-001"', str(c.cite("RES-001")))

    # ---------------------------------------------------------------- table filters
    def _check_filter(self, page, table_id, keys):
        h = self.html[page]
        bar = re.search(r'<div class="picker tf"[^>]*data-tf-table="%s"[^>]*>' % table_id, h)
        self.assertTrue(bar, table_id)
        self.assertIn(" hidden", bar.group(0))
        rows = re.findall(r"<tr(?: [^>]*)?data-tf-[^>]*>", h[h.index(f'id="{table_id}"'):])
        total = int(re.search(r'data-tf-total="(\d+)"', bar.group(0)).group(1))
        self.assertEqual(len(rows) >= total, True)
        rows = rows[:total]
        self.assertEqual(len(rows), total)
        for k in keys:
            vals = {m.group(1) for r in rows for m in [re.search(r'data-tf-%s="([^"]*)"' % k, r)] if m}
            self.assertTrue(vals, (table_id, k))
            sel = re.search(r'<select id="tf-%s-%s".*?</select>' % (table_id, k), h, re.S).group(0)
            opts = {html.unescape(v) for v in re.findall(r'<option value="([^"]+)"', sel)}
            for v in {html.unescape(x) for x in vals} - {""}:
                self.assertIn(v, opts, (table_id, k, v))
        self.assertIn(f'data-tf-empty="{table_id}"', h)

    def test_margins_filters_have_office_place_district(self):
        self._check_filter("elections/landscape/index.html", "margins-table",
                           ["year", "type", "band", "office", "place", "district"])

    def test_up_next_and_officeholders_filters(self):
        self._check_filter("elections/landscape/index.html", "up-next-table", ["year", "level", "government"])
        self._check_filter("elections/landscape/index.html", "took-office-list", ["level", "government", "how"])

    def test_calendar_every_seat_filters(self):
        self._check_filter("elections/calendar/index.html", "calendar-table", ["year", "level", "government"])

    def test_search_text_does_not_carry_party_primary_label(self):
        from pages.elections import _search_text
        self.assertEqual(_search_text("St. Joseph County Council, District H (Democratic primary)"),
                         "St. Joseph County Council, District H")
        h = self.html["elections/landscape/index.html"]
        self.assertNotRegex(h, r'data-tf-text="[^"]*primary\)')

    def test_table_filter_helper(self):
        h = str(table_filter("t", [{"key": "a", "label": "A", "options": [("1", "one")]}], 5, noun="seat",
                             search="Words", sort=[("x", "X", "n:asc:n")]))
        self.assertIn("5 of 5 seats shown.", h)
        self.assertIn(" hidden", h)
        self.assertIn('data-tf-reset', h)
        self.assertIn('for="tf-t-a"', h)


if __name__ == "__main__":
    unittest.main()
