"""Cleanup round (2026-11-18; planning/maps-cleanup-brief-2026-11-18.md part B). Report:
planning/qa/phase6-maps-cleanup-2026-11-18.md.

1. Learn hub cards: a hairline border from the tokens, in every look.
2. Page weight: the saved-place data and the learning paths are one shared script (assets/site-data.js, read through
   window.civicData), and the masthead's Indiana glyph is one shared SVG (assets/indiana-glyph.svg) drawn with <use>;
   no page inlines either any more.
3. Sources tabs: the sources grouped by kind in folds with their counts; every cited source keeps its id src-<id> and
   its footnote number; a long gaps list and the marks key are folds; every fold ships open (JavaScript off).
4. Campaign pages: an incomplete record is the * symbol of the status-marks system in map labels, bars and panels,
   never the word; the legend carries the linked mark and the page note defines it.
5. "Computed" is said once per page: no computed symbol beside a figure; each computed figure keeps a hidden marker
   (so its status is still recorded, and Copy CSV writes the word); the page note says it once.
6. The footer link reads "What the marks mean".
7. Compare budgets: shorter (three per-resident lists side by side, six rows a list before its fold, the map's notes
   beside the map, the debt notes folded) with every row, figure and old id still on the page.
Run:  python -P -E -m unittest discover -s tools/tests -p "test_maps_cleanup.py"
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
SITE_DIR = ROOT / "tools" / "site"
sys.path.insert(0, str(SITE_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import build  # noqa: E402
import status_marks_lib as L  # noqa: E402
from civic import campaign_map as cmap  # noqa: E402
from civic import components as C  # noqa: E402
from civic import glyph  # noqa: E402
from civic import shell  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site  # noqa: E402

BUILD = ["index.html", "learn/index.html", "offices/south-bend-mayor/index.html", "governments/south-bend/index.html",
         "money/budgets/index.html", "money/campaigns/index.html", "money/campaigns/county/index.html",
         "money/campaigns/south-bend/index.html", "elections/2016g/contests/index.html", "about/index.html"]
GOV_SOURCES = "governments/south-bend/sources/index.html"
GOV_MONEY = "governments/south-bend/money/index.html"
BUDGETS = "money/budgets/index.html"


class Cleanup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        cls.site = Site(cls.ed, cls.out)
        build.discover_builders()
        for p in BUILD:
            build.BUILDERS[p](cls.site)
        cls.site.write()
        cls.paths = sorted(cls.site.pages)
        cls._html = {}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def html(self, path: str) -> str:
        if path not in self._html:
            self._html[path] = (self.out / path).read_text(encoding="utf-8")
        return self._html[path]

    def main(self, path: str) -> str:
        m = re.search(r"<main\b[^>]*>(.*)</main>", self.html(path), re.S)
        return m.group(1) if m else ""

    # ------------------------------------------------------------------ 1 Learn cards
    def test_learn_cards_have_a_hairline_border_from_tokens(self):
        css = (SITE_DIR / "static" / "css" / "learn.css").read_text(encoding="utf-8")
        rule = re.search(r":root\[data-look\] \.card\.learn-card \{([^}]*)\}", css)
        self.assertIsNotNone(rule)
        self.assertIn("1px solid var(--line)", rule.group(1))
        self.assertNotRegex(css, r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")

    # ------------------------------------------------------------------ 2 page weight
    def test_no_page_inlines_the_shared_data_or_the_glyph(self):
        for p in self.paths:
            s = self.html(p)
            self.assertNotIn('id="here-data"', s, p)
            self.assertNotIn('id="paths-data"', s, p)
            self.assertNotIn('class="glyph-county" d=', s, p)
            if 'class="masthead' in s:
                self.assertIn("indiana-glyph.svg#in-rest", s, p)
                self.assertIn("indiana-glyph.svg#in-edition", s, p)
            # the shared data loads before app.js (both deferred: they run in document order)
            if "assets/app.js" in s:
                self.assertLess(s.index("assets/site-data.js"), s.index("assets/app.js"), p)

    def test_shared_data_asset_matches_the_site(self):
        js = (self.out / shell.SITE_DATA).read_text(encoding="utf-8")
        self.assertTrue(js.rstrip().endswith(";"))
        body = js[js.index("window.civicData = ") + len("window.civicData = "):js.rindex(";")]
        self.assertNotIn("<", body)
        self.assertNotIn(" ", body)
        data = json.loads(body)
        self.assertEqual(data["here"], json.loads(json.dumps(self.site.here_data)))
        from civic import sitemap
        self.assertEqual([p["id"] for p in data["paths"]["paths"]], [p["id"] for p in sitemap.PATHS])
        for p in data["paths"]["paths"]:
            for s in p["stops"]:
                self.assertFalse(s["page"].startswith(("/", ".")), s["page"])   # site-relative; scripts add data-root

    def test_glyph_asset_has_no_colour_and_resolves(self):
        svg = (self.out / glyph.GLYPH_ASSET).read_text(encoding="utf-8")
        self.assertTrue(svg.startswith("<svg xmlns="), "written as markup, not escaped")
        self.assertEqual(set(re.findall(r'\bid="([^"]+)"', svg)), {"in-rest", "in-edition"})
        self.assertNotRegex(svg, r"\bfill=|\bclass=|\bstyle=|#[0-9a-fA-F]{3,6}\b")
        self.assertEqual(svg.count('vector-effect="non-scaling-stroke"'), 2)

    def test_scripts_read_the_shared_data(self):
        for f, key in (("static/app.js", "paths"), ("static/js/community.js", "paths"), ("static/js/moved.js", "paths"),
                       ("static/js/here.js", "here"), ("static/js/your_place.js", "here")):
            src = (SITE_DIR / f).read_text(encoding="utf-8")
            self.assertIn(f"window.civicData.{key}", src, f)
            self.assertNotIn('"here-data"', src, f)
            self.assertNotIn('"paths-data"', src, f)
            self.assertTrue(all(ord(c) < 128 for c in src), f)

    def test_typical_page_is_less_than_half_its_old_weight(self):
        # offices/south-bend-mayor/ was 43,929 bytes before (planning/qa report); the glyph and the two JSON blocks
        # were 24 KB of it
        self.assertLess(len(self.html("offices/south-bend-mayor/index.html").encode("utf-8")), 26_000)

    # ------------------------------------------------------------------ 3 Sources tabs
    def test_sources_grouped_by_kind_with_every_anchor_and_number(self):
        page = self.site.pages[GOV_SOURCES]
        order = page.cites.order
        self.assertGreaterEqual(len(order), C.Citations.GROUP_FROM)
        main = self.main(GOV_SOURCES)
        groups = re.findall(r'<details class="fold-details src-group" id="src-kind-([a-z]+)" data-fold="sources" open>'
                            r'<summary[^>]*><span class="src-group-name">([^<]+)</span> '
                            r'<span class="fold-count">\((\d+)\)</span>', main)
        self.assertGreaterEqual(len(groups), 2)
        items = re.findall(r'<li value="(\d+)" id="src-([^"]+)"', main)
        self.assertEqual(sum(int(n) for _k, _l, n in groups), len(items))
        got = {sid: int(v) for v, sid in items}
        self.assertEqual(set(got), set(order), "every cited source is on the tab")
        self.assertEqual(got, {sid: i for i, sid in enumerate(order, 1)}, "footnote numbers unchanged")
        # a footnote on another tab lands on the same number
        for sid, n in re.findall(r'href="\.\./sources/index\.html#src-([^"]+)"[^>]*>(\d+)</a>', self.main(GOV_MONEY)):
            self.assertEqual(got.get(sid), int(n), sid)
        # each group holds only its kind
        for kind, _label, _n in groups:
            sec = re.search(rf'id="src-kind-{kind}".*?</details>', main, re.S).group(0)
            labels = dict(C.Citations.KIND_GROUPS)
            for sid in re.findall(r'<li value="\d+" id="src-([^"]+)"', sec):
                k = (self.ed.sources.get(sid) or {}).get("kind", "")
                self.assertEqual(k if k in labels else "other", kind, sid)

    def test_sources_tab_folds_ship_open_and_keep_ids(self):
        main = self.main(GOV_SOURCES)
        for i in ('id="sources"', 'id="marks"', 'id="marks-sec"', 'id="gaps"'):
            self.assertIn(i, main)
        self.assertIn('id="marks-fold" data-fold="sources" open', main)
        if 'id="gaps-fold"' in main:
            self.assertIn('id="gaps-fold" data-fold="sources" open', main)
        for d in re.findall(r"<details\b[^>]*>", main):
            if "data-fold" in d and ("src-group" in d or "tab-fold" in d):
                self.assertIn(" open", d)

    def test_short_source_list_stays_one_plain_list(self):
        class FakeEd:
            sources = {f"X-{i}": {"title": f"T{i}", "kind": "primary"} for i in range(3)}
        c = C.Citations(FakeEd())
        for sid in FakeEd.sources:
            c.cite(sid)
        out = str(c.render_grouped())
        self.assertNotIn("src-group", out)
        self.assertEqual(out.count('<li id="src-'), 3)

    # ------------------------------------------------------------------ 4 campaign pages
    def test_campaign_labels_use_the_symbol_not_the_word(self):
        sym = C.FIGURE_MARKS["incomplete"][0]
        race = {"office": "Mayor", "complete": False, "spent": 100, "reasons": ["A.", "B.", "C."]}
        done = {"office": "Clerk", "complete": True, "spent": 50, "reasons": []}
        bars = cmap.race_bars([race, done])
        self.assertEqual(bars[0][0], f"Mayor {sym}")
        self.assertEqual(bars[1][0], "Clerk")
        self.assertTrue(cmap.record_line([race]).startswith(sym + " A. B."))
        self.assertEqual(cmap.record_line([race, done]), f"{sym} 1 of 2 races are missing at least one expected report")
        self.assertNotIn("omplete", cmap.record_line([done]))
        cand = {"name": "A", "party": "", "committees": [1], "spent": 10, "missing": ["x"]}
        self.assertIn(sym, cmap.candidate_bars({"spent": 10, "candidates": [cand]})[0][0])
        self.assertNotIn("incomplete", cmap.candidate_bars({"spent": 10, "candidates": [cand]})[0][0])
        # the screen-reader name keeps the word once (a bare symbol reads as "star")
        self.assertIn("incomplete record", cmap._aria("X", 100, "2024", False))
        self.assertNotIn("omplete", cmap._aria("X", 100, "2024", True))

    def test_campaign_pages_have_no_incomplete_word_outside_verbatim_notes(self):
        for p in ("money/campaigns/index.html", "money/campaigns/county/index.html",
                  "money/campaigns/south-bend/index.html"):
            m = self.main(p)
            m = re.sub(r'<(a|span) class="fmark[^"]*"[^>]*>', "<x>", m)          # a mark's own accessible name
            m = re.sub(r'<aside class="fnotes".*?</aside>', "", m, flags=re.S)  # the note defines the mark once
            m = re.sub(r'aria-label="[^"]*"', "", m)                             # map areas' screen-reader names
            m = m.replace("office line blank or incomplete", "")                 # verbatim transcription notes
            self.assertNotRegex(m, r"(?i)\bincomplete\b", p)
            self.assertNotIn("(incomplete)", m, p)
            if 'data-fmark="incomplete"' in m:
                self.assertIn('id="fnote-incomplete"', self.main(p), p)

    # ------------------------------------------------------------------ 5 computed once
    def test_computed_said_once_per_page(self):
        n_quiet = 0
        for p in self.paths:
            main = self.main(p)
            self.assertNotIn('data-fmark="computed"', main, p)
            self.assertNotIn('class="fmark fmark-computed', main, p)
            if 'data-fquiet="computed"' in main:
                n_quiet += 1
                self.assertEqual(main.count('id="fnote-computed"'), 1, p)
                self.assertEqual(html.unescape(main).count(shell.COMPUTED_ONCE), 1, p)
                # the marker carries the word Copy CSV writes, and is hidden
                self.assertIn('<span class="fquiet" data-fquiet="computed" data-word="COMPUTED" hidden></span>', main)
            self.assertEqual(L.quiet_kinds(self.html(p)) - {"computed"}, set(), p)
        self.assertGreater(n_quiet, 3)

    def test_quiet_marker_keeps_the_status_on_its_row(self):
        row = str(C.h("ul", None, C.h("li", None, "Share 52%", C.figure_mark("computed"))))
        out = shell._COMPUTED_MARK.sub(shell._QUIET_COMPUTED, row)
        self.assertNotIn("‖", out)
        self.assertNotIn("⁠", out)
        self.assertEqual(L.occurrences("<main>" + out + "</main>"), {("share52%", "computed")})
        # another status beside it is untouched
        both = str(C.figure_mark("computed")) + str(C.figure_mark("unofficial"))
        self.assertIn('data-fmark="unofficial"', shell._COMPUTED_MARK.sub(shell._QUIET_COMPUTED, both))

    def test_copy_csv_writes_the_quiet_word(self):
        js = (SITE_DIR / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn('querySelectorAll(".fmark, .fquiet")', js)

    # ------------------------------------------------------------------ 6 footer
    def test_footer_says_marks_not_badges(self):
        s = self.html("index.html")
        foot = s[s.index("<footer"):s.index("</footer>")]
        words = re.sub(r"<[^>]+>", " ", foot)                              # the link text, not its #badges href
        self.assertIn("What the marks mean", words)
        self.assertNotIn("badges", words)
        self.assertIn('href="about/index.html#badges">What the marks mean<', foot)
        self.assertIn('id="badges"', self.html("about/index.html"))        # the old anchor still lands

    # ------------------------------------------------------------------ 7 Compare budgets
    def test_compare_budgets_shorter_with_every_row(self):
        from pages import money as M
        main = self.main(BUDGETS)
        self.assertIn('class="cb-two cb-three"', main)
        for fid in ("perres-af", "perres-av", "rates-certified", "debt-2024"):
            fig = re.search(rf'<figure[^>]*id="{fid}".*?</figure>', main, re.S)
            self.assertIsNotNone(fig, fid)
            shown = len(re.findall(r'class="mrw-row', fig.group(0)))
            rest = re.search(rf'id="{fid}-rest".*?</details>', main, re.S)
            if rest is not None:
                self.assertEqual(shown, M.BUDGETS_TOP, fid)
                m = re.search(r"\(top (\d+) of (\d+)\)", fig.group(0))
                self.assertEqual(int(m.group(1)), M.BUDGETS_TOP)
                more = len(re.findall(r'class="mrw-row', rest.group(0)))
                self.assertEqual(shown + more, int(m.group(2)), f"{fid}: every row is on the page")
        # the map's notes sit in its side column; the debt notes and whole-corporation note are folds that ship open
        side = re.search(r'<div class="cmap-side">.*?</aside>(.*?)</div></div>', main, re.S)
        self.assertIsNotNone(side)
        self.assertIn('class="cmap-mcounty"', side.group(1))
        self.assertIn('class="muted cmap-mnote"', side.group(1))
        for fid in ("debt-notes-fold", "whole-corporation-fold"):
            self.assertRegex(main, rf'<details class="fold-details see-all" id="{fid}" open')
        self.assertIn('id="whole-corporation"', main)
        self.assertIn("Notes stored with these totals:", main)


if __name__ == "__main__":
    unittest.main()
