"""Phase 6 step 5 (2026-11-18): the Money hub, the campaign money browser, the short campaign area pages, Compare
budgets, and the budget charts drawn as full-width HTML columns.

planning/design-direction-2026-11-16.md section 4 (money rows) and section 7 step 5; report
planning/qa/phase6-money-2026-11-18.md.

- The test case: Money hub -> Campaign money -> By office -> Mayor of South Bend's Money tab, with Primary / General
  links into its switch (#show=primary).
- Figures are the race model's own sums: Mayor of South Bend 2023 is $610,625.36 spent, $393,342.90 raised on the hub,
  the browser, the area page and the office tab; area totals equal the old pages' (fixed literals below).
- Nothing findable became unfindable: every id the old money pages had (fixtures/anchors_before_phase6_money.json,
  taken from the build before this step) is still on its page or forwarded by #moved-anchors to a page that has it
  (followed exactly as static/js/moved.js does, tools/tests/gov_moved.py).
- The budgets page's per-unit detail is on the government Money tabs: every budget chart id, the "other reported
  figures" tables and the other breakdowns (obrk-*), which had no other home before this step.
- Neutrality: money bars never use party colours; people are listed alphabetically, never by money.
Run:  python -P -E -m unittest tools.tests.test_phase6_money   (or discover -s tools/tests)
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
from civic import campaign_money as cm  # noqa: E402
from civic import governments as gm  # noqa: E402
from civic import offices as om  # noqa: E402
from civic import search  # noqa: E402
from civic import sitemap  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import ONPAGE_PAGES, Site  # noqa: E402
from gov_moved import follow  # noqa: E402

from anchor_fixtures import anchor_fixture  # noqa: E402  (old-anchor fixtures without retired data-block ids)
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "anchors_before_phase6_money.json"
ID_RE = re.compile(r'\sid="([^"]+)"')
HREF_RE = re.compile(r'href="([^"]*)"')
MAYOR = "south-bend-mayor"
HUB = "money/index.html"
INDEX = "money/campaigns/index.html"
VIEWS = ["money/campaigns/by-election/index.html", "money/campaigns/by-candidate/index.html",
         "money/campaigns/by-place/index.html", "money/campaigns/other-committees/index.html",
         "money/campaigns/all-filings/index.html"]
BUDGETS = "money/budgets/index.html"
# the old area pages' "Spent by all candidates" lines (build before this step), unchanged on the new pages
AREA_TOTALS = {"south-bend": ("$830,504.38", "$623,352.65"), "county": ("$1,421,980.97", "$1,678,684.47"),
               "mishawaka": ("$318,283.08", "$391,438.17"), "phm": ("$3,393.00", "$0.00"),
               "penn-township": ("$34,605.33", "$36,325.84")}
PARTY_CLASS = re.compile(r'class="[^"]*\b(?:m-party-[a-z]+|party-[dr]\b|m-d\b|m-r\b)')


def _text(src: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", src))


class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        cls.site = site = Site(cls.ed, cls.out)
        build.discover_builders()
        want = [e.path for e in site.entries if e.path.startswith(("money/", "governments/"))]
        want += [om.path(MAYOR, t) for t in om.office_tabs(cls.ed, MAYOR)]
        want += [om.path(o["office_id"], "money") for o in cls.ed.tables["offices"]
                 if "money" in om.office_tabs(cls.ed, o["office_id"])]     # every view link is checked on its tab
        want += ["about/sources/index.html"]
        for p in want:
            if p not in site.pages and p in build.BUILDERS:
                build.BUILDERS[p](site)
        site.write()
        cls.html = {p: (cls.out / p).read_text(encoding="utf-8") for p in site.pages}
        cls.ids = {p: set(ID_RE.findall(h)) for p, h in cls.html.items()}
        cls.index = json.loads((cls.out / "assets" / "search-index.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def links(self, path):
        import posixpath
        out = set()
        for href in HREF_RE.findall(self.html[path]):
            if href.startswith(("http", "mailto", "#")):
                continue
            target, _, frag = href.partition("#")
            out.add((posixpath.normpath(posixpath.join(posixpath.dirname(path), target)), frag))
        return out

    # ---------------------------------------------------------------- the test case
    def test_hub_two_doors_lead_to_the_browser_and_compare_budgets(self):
        h = self.html[HUB]
        for i in ("government", "campaign", "facts", "pages"):
            self.assertIn(f'id="{i}"', h)
        targets = {t for t, _f in self.links(HUB)}
        for p in (INDEX, BUDGETS, "money/your-tax-bill/index.html", "money/campaigns/by-election/index.html"):
            self.assertIn(p, targets)
        self.assertIn("$610,625.36", h)      # the campaign preview's first row: Mayor of South Bend 2023

    def test_by_office_leads_to_the_mayor_money_tab_and_its_primary_view(self):
        h = self.html[INDEX]
        mt = om.path(MAYOR, "money")
        got = self.links(INDEX)
        self.assertIn((mt, ""), got)
        # follow-up 2026-11-18: direct links into the tab's switch (check.py accepts this state fragment narrowly);
        # the mayor's Primary view is the news-reported primaries (Democratic 2011, 2015, 2019; Republican 2007)
        self.assertIn((mt, "show=primary"), got)
        self.assertIn((mt, "show=general"), got)
        self.assertRegex(self.html[mt], r'<figure[^>]*data-mt-phase="primary"')
        # Mayor of South Bend is the first row of the ranked chart, with the race card's own figures
        top = re.search(r'id="cb-top".*?</figure>', h, re.S).group(0)
        first = re.search(r'<li class="mrw-row".*?</li>', top, re.S).group(0)
        self.assertIn("Mayor of South Bend", first)
        self.assertIn("$610,625.36", first)
        self.assertIn("$393,342.90", first)
        self.assertIn("$610,625.36", self.html[mt])

    def test_view_links_only_where_the_view_shows_something(self):
        import posixpath
        offered = {}
        for href in HREF_RE.findall(self.html[INDEX]):
            m = re.match(r"(.*?)#show=(primary|general)$", href)
            if m:
                tab = posixpath.normpath(posixpath.join("money/campaigns", m.group(1)))
                offered.setdefault(tab, set()).add(m.group(2))
        self.assertGreater(len(offered), 10)
        for o in self.ed.tables["offices"]:
            oid = o["office_id"]
            if "money" not in om.office_tabs(self.ed, oid) or om.money_model(self.ed, oid)["state"]:
                continue
            tab = om.path(oid, "money")
            shown = set(re.findall(r'data-mt-phase="(primary|general)"', self.html[tab]))
            self.assertEqual(offered.get(tab, set()), shown, oid)
        # an office whose only election can't be split and has no news figures gets no view link
        self.assertTrue(any(not v for v in [offered.get(om.path(o["office_id"], "money")) for o in
                                            self.ed.tables["offices"] if "money" in om.office_tabs(self.ed, o["office_id"])]))

    def test_every_office_with_money_is_listed_once_and_no_other(self):
        h = self.html[INDEX]
        listed = re.findall(r'href="\.\./\.\./offices/([^/]+)/money/index\.html"', re.search(
            r'id="cb-offices".*?</div>\s*<p class="tnote">', h, re.S).group(0))
        with_money = [o["office_id"] for o in self.ed.tables["offices"] if "money" in om.office_tabs(self.ed, o["office_id"])]
        self.assertEqual(set(listed), set(with_money))
        self.assertEqual(len(re.findall(r'class="cb-gov"', h)) + 0 > 10, True)

    def test_views_share_one_tab_bar(self):
        for p in [INDEX] + VIEWS:
            h = self.html[p]
            nav = re.search(r'<nav class="tabs" aria-label="Campaign money: views".*?</nav>', h, re.S)
            self.assertIsNotNone(nav, p)
            self.assertEqual(nav.group(0).count('aria-current="page"'), 1, p)
            self.assertEqual(nav.group(0).count("<li"), 6, p)

    def test_by_election_ranks_races_on_one_scale_and_links_office_tabs(self):
        h = self.html["money/campaigns/by-election/index.html"]
        for y in ("2026", "2024", "2023"):
            self.assertIn(f'id="c-{y}"', h)
        self.assertIn("offices/south-bend-mayor/money/index.html#y2023", h)
        self.assertIn('id="earlier"', h)
        self.assertIn("offices/south-bend-mayor/money/index.html#y2019", h)
        # news figures are never added up on this page: no dollar figure in the earlier-elections list
        early = re.search(r'id="earlier".*?</section>', h, re.S).group(0)
        self.assertNotRegex(_text(early), r"\$\d")

    def test_every_race_is_on_by_election_with_its_own_total(self):
        h = _text(self.html["money/campaigns/by-election/index.html"])
        from pages.campaigns import cf_all
        for r in cf_all(self.ed)["races"]:
            self.assertIn(r["office"], h)
            if r["spent"] is not None:
                self.assertIn(cm.usd(r["spent"]), h, r["id"])

    def test_by_candidate_is_alphabetical_never_by_money(self):
        h = self.html["money/campaigns/by-candidate/index.html"]
        letters = re.findall(r'<details class="cb-letter" id="l-([a-z]+)"', h)
        self.assertEqual([x for x in letters if x != "other"], sorted(x for x in letters if x != "other"))
        self.assertIn("people/james-mueller/money/index.html", h)

    def test_no_party_colour_on_money_bars(self):
        for p in [HUB, INDEX, BUDGETS] + VIEWS[:2] + [cm.area_path("south-bend")]:
            for fig in re.findall(r'<figure class="chart chart-money-rows".*?</figure>', self.html[p], re.S):
                self.assertIsNone(PARTY_CLASS.search(fig), p)

    # ---------------------------------------------------------------- area pages
    def test_area_pages_open_on_office_totals_and_keep_their_totals(self):
        for aid, (spent, raised) in AREA_TOTALS.items():
            h = self.html[cm.area_path(aid)]
            t = _text(h)
            self.assertIn(f"Spent by all candidates, latest election: {spent}", t, aid)
            self.assertIn(f"raised {raised}", t, aid)
            # the offices chart comes before the folded detail
            self.assertLess(h.index('id="offices"'), h.index('id="detail"'), aid)
        sb = self.html[cm.area_path("south-bend")]
        self.assertIn("offices/south-bend-mayor/money/index.html#y2023", sb)
        self.assertRegex(sb, r'<details class="fold-details see-all" id="e-2023g-fold"[^>]*data-fold="see-all"')

    def test_area_without_races_says_so(self):
        h = _text(self.html[cm.area_path("lakeville")])
        self.assertIn("results have no race for Town of Lakeville", h)

    # ---------------------------------------------------------------- Compare budgets
    def test_compare_budgets_rows_link_government_money_tabs(self):
        h = self.html[BUDGETS]
        for i in ("money-map", "per-resident", "perres-af", "perres-gf", "perres-av", "rates", "rates-certified",
                  "debt", "debt-2024", "debt-classes", "tax-base", "over-time"):
            self.assertIn(f'id="{i}"', h, i)
        targets = {t for t, _f in self.links(BUDGETS)}
        self.assertIn(gm.path("south-bend", "money"), targets)
        self.assertIn(gm.path("penn-township", "money"), targets)
        # units with no budget rows are still listed, and say so
        self.assertIn("No adopted budget series in the guide's data", _text(html.unescape(h)))

    def test_budget_detail_is_on_government_money_tabs(self):
        old = anchor_fixture(FIXTURE)[BUDGETS]
        from pages.money import money
        mo = money(self.ed)
        for i in old:
            m = re.match(r"(bud|obrk|other)-(.+)$", i)
            if not m or i.endswith(("-copy", "-details", "-table")) and m.group(1) != "bud":
                continue
            mid = next((x for x in mo.unit_ids if m.group(2).startswith(x)), None)
            if mid is None:
                continue
            gov = gm.gov_for_money_id(self.ed, mid)
            self.assertIn(i, self.ids[gm.path(gov.gid, "money")], f"{i} not on {gov.gid}'s Money tab")

    def test_budget_charts_are_full_width_html(self):
        h = self.html[gm.path("south-bend", "money")]
        fig = re.search(r'<figure class="chart chart-columns"[^>]*id="bud-city-south-bend-general-fund".*?</figure>', h,
                        re.S).group(0)
        self.assertNotIn("<svg", fig)
        self.assertIn('class="fcol"', fig)
        cols = re.findall(r'class="fcol-c[ "]', fig)
        from pages.money import money
        mo = money(self.ed)
        self.assertEqual(len(cols), mo.y1 - mo.y0 + 1)
        self.assertRegex(fig, r'style="height:\d+\.\d\d%"')
        self.assertIn("data-tv=", fig)

    # ---------------------------------------------------------------- old URLs and anchors
    def test_every_old_anchor_resolves(self):
        old = anchor_fixture(FIXTURE)
        missing = []
        for page, ids in old.items():
            self.assertIn(page, self.html, f"{page} is no longer built")
            for i in ids:
                got = follow(self.html, self.ids, page, i)
                if not got or got[1] not in self.ids.get(got[0], set()):
                    missing.append(f"{page}#{i} -> {got}")
        self.assertEqual(missing, [], f"{len(missing)} old ids lost: {missing[:20]}")

    def test_moved_maps_name_only_ids_that_left_and_targets_that_exist(self):
        from gov_moved import join, moved_map
        for page in (INDEX, BUDGETS):
            m = moved_map(self.html[page])
            self.assertIsNotNone(m, page)
            for old, dest in m.get("a", {}).items():
                np, frag = join(page, dest)
                self.assertIn(np, self.html, f"{page}: {old} -> {dest}")
                if frag:
                    self.assertIn(frag, self.ids[np], f"{page}: {old} -> {dest}")

    # ---------------------------------------------------------------- search, sitemap, shell
    def test_search_words_find_the_money_pages(self):
        items = self.index["items"]
        by_label = {}
        for it in items:
            by_label.setdefault(it[1], set()).add(it[3])
        self.assertIn(INDEX, by_label.get("Campaign money", set()))
        self.assertIn(INDEX, by_label.get("Campaign finance", set()))
        self.assertIn(BUDGETS, by_label.get("Compare budgets", set()))
        self.assertIn("money/your-tax-bill/index.html", by_label.get("Your tax bill", set()))
        kw = {it[3]: it[5] for it in items if it[0] == search.T_PAGE and len(it) > 5}
        self.assertIn("budgets", kw.get(BUDGETS, ""))
        self.assertIn("campaign", kw.get(INDEX, ""))

    def test_short_pages_left_the_onpage_bar(self):
        for p in (BUDGETS, cm.area_path("county"), cm.area_path("south-bend")):
            self.assertNotIn(p, ONPAGE_PAGES)

    def test_nav_money_menu(self):
        money = next(n for n in sitemap.NAV if n["name"] == "Money")
        self.assertLessEqual(len(money["links"]), sitemap.MAX_DROPDOWN)
        self.assertIn(("money/budgets/index.html", "Compare budgets"), money["links"])


class RankRows(unittest.TestCase):
    """Edge cases of pages/money.py rank_rows and money_browser rows without a filed total."""

    def test_zero_and_missing_values_draw_no_bar(self):
        from pages.money import rank_rows
        out = str(rank_rows("x", "T", [{"name": "A", "value": 5.0, "text": "$5"},
                                       {"name": "B", "value": 0.0, "text": "$0"},
                                       {"name": "C", "value": None, "text": "not in the data"}]))
        self.assertEqual(out.count('class="mrw-bar m-'), 1)
        self.assertIn("not in the data", out)
        self.assertEqual(str(rank_rows("y", "T", [])).count("<li"), 0)


if __name__ == "__main__":
    unittest.main()
