"""Phase 6 step 1 (2026-11-16): tab template, office pages, Offices hub, header nav, search by tab, cross-links.

planning/design-direction-2026-11-16.md section 0; report planning/qa/phase6-step1-2026-11-16.md.

- Tabs are real pages; an empty tab is neither generated nor shown; every tab repeats one header and tab bar.
- Office Money tab reuses the campaign-page sums: Mayor of South Bend 2023 equals money/campaigns/south-bend/.
- Offices hub works as a plain grouped list with JavaScript off.
- Every sitemap page is within two clicks of the header and footer (hub pages count).
- Search: "mayor money", "mayor primary", "campaign finance mayor", "sheriff results" land on the office tab first;
  party tags are never matched.
- The 2026 UNOFFICIAL banner shows only on pages that display 2026 unofficial figures.
Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import html as htmllib
import json
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = ROOT / "tools" / "site"
sys.path.insert(0, str(SITE_DIR))

import build  # noqa: E402
from civic import campaign_money as cm  # noqa: E402
from civic import offices as om  # noqa: E402
from civic import search, sitemap  # noqa: E402
from civic import tabs as T  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site  # noqa: E402
from pages import stubs  # noqa: E402

HREF_RE = re.compile(r'href="([^"#?]*)(?:#[^"]*)?"')
MAYOR = "south-bend-mayor"
NO_ELECTIONS = "indian-village-clerk-treasurer"


def _resolve(page: str, href: str) -> str:
    if not href or href.startswith(("http:", "https:", "mailto:")):
        return ""
    return posixpath.normpath(posixpath.join(posixpath.dirname(page), href))


# ====================================================================== model and template (no build)
class Model(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.site = Site(cls.ed, Path(tempfile.gettempdir()) / "unused-phase6")

    def test_tab_paths_and_order(self):
        self.assertEqual(T.tab_path("offices/x/", "overview"), "offices/x/index.html")
        self.assertEqual(T.tab_path("offices/x", "money"), "offices/x/money/index.html")
        self.assertEqual(T.ordered(["sources", "money"]), ["overview", "money", "sources"])   # overview always
        self.assertEqual(T.ordered(["history", "elections", "overview", "sources"]),
                         ["overview", "elections", "history", "sources"])
        with self.assertRaises(KeyError):
            T.ordered(["overview", "people"])
        with self.assertRaises(KeyError):
            T.tab_path("offices/x/", "people")

    def test_tab_entries(self):
        es = T.tab_entries("offices/x/", "Mayor of X", "d", ["sources", "money"], group="Offices",
                           crumb=[("Offices", "offices/index.html"), ("X", None)])
        self.assertEqual([e.path for e in es], ["offices/x/index.html", "offices/x/money/index.html",
                                                "offices/x/sources/index.html"])
        self.assertEqual([e.title for e in es], ["Mayor of X", "Mayor of X: Money", "Mayor of X: Sources"])
        self.assertEqual({e.thing for e in es}, {"offices/x/"})

    def test_every_office_has_exactly_its_tabs_in_the_sitemap(self):
        by_path = self.site.by_path
        self.assertIn(om.HUB, by_path)
        # 2026-11-18 (gap-fill round 2): 127 + 3 federal + 8 statewide/appellate = 138 (State House 48 removed)
        self.assertEqual(len(self.ed.tables["offices"]), 138)
        for o in self.ed.tables["offices"]:
            oid = o["office_id"]
            keys = om.office_tabs(self.ed, oid)
            self.assertEqual(keys[0], "overview", oid)
            self.assertEqual(keys[-1], "sources", oid)
            for k in T.TAB_ORDER:
                self.assertEqual(om.path(oid, k) in by_path, k in keys, f"{oid} {k}")
            # a tab is there exactly when its data is
            self.assertEqual("elections" in keys, bool(om.contests(self.ed, oid)), oid)
            self.assertEqual("history" in keys, bool(self.ed.terms_for(oid)) or any(
                t["office_id"] == oid for t in self.ed.tables["terms"]), oid)

    def test_some_offices_have_no_elections_or_money_tab(self):
        self.assertNotIn("elections", om.office_tabs(self.ed, NO_ELECTIONS))
        no_money = [o["office_id"] for o in self.ed.tables["offices"] if "money" not in om.office_tabs(self.ed, o["office_id"])]
        self.assertTrue(no_money)
        self.assertEqual(om.office_tabs(self.ed, MAYOR), ["overview", "elections", "money", "history", "sources"])

    def test_office_crumb(self):
        e = self.site.by_path[om.path(MAYOR, "money")]
        self.assertEqual(sitemap.crumbs(self.site.by_path, e.path),
                         [("Offices", om.HUB), ("City of South Bend", f"{om.HUB}#g-south-bend"),
                          ("Mayor", om.path(MAYOR)), ("Money", None)])
        self.assertEqual(sitemap.crumbs(self.site.by_path, om.path(MAYOR))[-1], ("Mayor", None))

    def test_nav_dropdowns_are_short_and_built(self):
        self.assertEqual([i["name"] for i in sitemap.NAV], ["Governments", "Offices", "Elections", "Money", "Learn"])
        for item in sitemap.NAV:
            self.assertIn(item["hub"], self.site.by_path)
            self.assertLessEqual(len(item["links"]), sitemap.MAX_DROPDOWN, item["name"])
            for target, _label in item["links"]:
                self.assertIn(target.split("#")[0], self.site.by_path, target)
        for target, _label in sitemap.FOOTER:
            self.assertIn(target.split("#")[0], self.site.by_path, target)

    def test_tab_keywords(self):
        kw = {k: set(v.split()) for k, v in search.TAB_KEYWORDS.items()}
        for w in ("money", "finance", "campaign", "spent", "raised", "donations"):
            self.assertIn(w, kw["money"])
        for w in ("results", "election", "primary", "votes", "margin"):
            self.assertIn(w, kw["elections"])
        for w in ("history", "past", "former"):
            self.assertIn(w, kw["history"])
        for words in kw.values():   # party words are never search keys
            self.assertFalse(words & {"democrat", "democratic", "republican", "d", "r", "party"})


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
        cls.paths = sorted(site.pages)
        cls._html = {}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def html(self, path: str) -> str:
        if path not in self._html:
            self._html[path] = (self.out / path).read_text(encoding="utf-8")
        return self._html[path]

    def links(self, path: str, fragment: str | None = None) -> set[str]:
        src = fragment if fragment is not None else self.html(path)
        return {p for p in (_resolve(path, h) for h in HREF_RE.findall(src)) if p}

    # ------------------------------------------------------------------ build
    def test_no_builder_failed(self):
        self.assertEqual(self.failed, [])
        for o in self.ed.tables["offices"]:
            for k in om.office_tabs(self.ed, o["office_id"]):
                self.assertTrue((self.out / om.path(o["office_id"], k)).is_file(), (o["office_id"], k))

    # ------------------------------------------------------------------ tabs
    def tabs_nav(self, path: str) -> str:
        h = self.html(path)
        i = h.index('<nav class="tabs"')
        return h[i:h.index("</nav>", i)]

    def test_tab_bar_on_every_tab(self):
        for oid in (MAYOR, "centre-township-board", "state-house-5", NO_ELECTIONS):
            keys = om.office_tabs(self.ed, oid)
            facts = set()
            for k in keys:
                p = om.path(oid, k)
                nav = self.tabs_nav(p)
                targets = [_resolve(p, x) for x in re.findall(r'href="([^"]+)"', nav)]
                self.assertEqual(targets, [om.path(oid, x) for x in keys], p)          # every tab, in order, no more
                cur = re.findall(r'<a class="tab-link" href="([^"]+)" aria-current="page">([^<]+)</a>', nav)
                self.assertEqual(len(cur), 1, p)
                self.assertEqual(_resolve(p, cur[0][0]), p)
                self.assertEqual(cur[0][1], T.TAB_LABELS[k])
                m = re.search(r'<p class="thing-facts">(.*?)</p>', self.html(p), re.S)
                facts.add(re.sub(r'href="[^"]*"', "", m.group(1)))
                self.assertEqual(self.html(p).count('<h1 class="thing-title">'), 1, p)
            self.assertEqual(len(facts), 1, oid)                                         # one shared header

    def test_omitted_tab_is_not_built_or_linked(self):
        self.assertFalse((self.out / om.path(NO_ELECTIONS, "elections")).exists())
        for k in om.office_tabs(self.ed, NO_ELECTIONS):
            self.assertNotIn("elections/index.html", self.tabs_nav(om.path(NO_ELECTIONS, k)))

    def test_footnotes_point_to_the_sources_tab(self):
        src = om.path(MAYOR, "sources")
        ids = set(re.findall(r'\sid="(src-[^"]+)"', self.html(src)))
        self.assertTrue(ids)
        for k in ("overview", "elections", "money", "history"):
            p = om.path(MAYOR, k)
            notes = re.findall(r'<sup[^>]*>.*?</sup>', self.html(p), re.S)
            self.assertTrue(notes, p)
            for href in re.findall(r'href="([^"]+#src-[^"]+)"', "".join(notes)):
                path, _, frag = href.partition("#")
                self.assertEqual(_resolve(p, path), src, href)
                self.assertIn(frag, ids, href)

    def test_tab_bar_scrolls_inside_itself(self):
        css = (SITE_DIR / "static" / "css" / "tabs.css").read_text(encoding="utf-8")
        rule = re.search(r"\n\.tabs \{([^}]*)\}", css).group(1)
        self.assertIn("overflow-x: auto", rule)
        self.assertIn("max-width: 100%", rule)
        self.assertIn("flex-wrap: nowrap", re.search(r"\n\.tab-list \{([^}]*)\}", css).group(1))

    # ------------------------------------------------------------------ money: one computation
    def test_mayor_2023_totals_equal_the_campaign_page(self):
        from pages.campaigns import cf_all
        race = next(r for r in cf_all(self.ed)["races"] if r["id"] == "2023g-south-bend-mayor")
        want = f"{cm.usd(race['spent'])} spent, {cm.usd(race['raised'])} raised"
        office = re.search(r'<span class="mt-total-figs" data-race="2023g-south-bend-mayor">([^<]+)</span>',
                           self.html(om.path(MAYOR, "money"))).group(1)
        card = self.html("money/campaigns/south-bend/index.html")
        card = card[card.index('id="r-2023g-south-bend-mayor"'):]
        total = re.search(r'<p class="cf-race-total"><strong>All candidates: </strong>([^<]+)', card).group(1)
        self.assertEqual(htmllib.unescape(office), want)
        self.assertTrue(htmllib.unescape(total).startswith(want), total)
        self.assertEqual(want, "$610,625.36 spent, $393,342.90 raised")

    def test_rounded_news_figures_keep_their_words(self):
        h = htmllib.unescape(self.html(om.path(MAYOR, "money")))
        self.assertIn("nearly $245,000", h)
        self.assertNotIn("$245,000.00", h)
        self.assertIn("as reported in the news", h)
        self.assertIn('data-fmark="single_source"', self.html(om.path(MAYOR, "money")))   # the § mark (2026-11-18)
        self.assertIn("reports not posted online", h)

    def test_money_charts_never_use_party_colors(self):
        for oid in (MAYOR, "state-house-5"):
            if "money" in om.office_tabs(self.ed, oid):
                h = self.html(om.path(oid, "money"))
                figs = re.findall(r'<figure class="chart[^"]*".*?</figure>', h, re.S)
                self.assertTrue(figs, oid)
                for f in figs:
                    self.assertNotRegex(f, r"m-party-", oid)

    def test_state_district_money_says_different_basis(self):
        h = self.html(om.path("state-house-5", "money"))
        self.assertIn("A different basis from the local races.", h)

    # ------------------------------------------------------------------ hub
    def test_hub_is_a_plain_grouped_list_with_js_off(self):
        h = self.html(om.HUB)
        for lid in om.LEVEL_IDS.values():
            self.assertIn(f'id="{lid}"', h)
        rows = re.findall(r'<li class="ofh-row"[^>]*>.*?</li>', h, re.S)
        self.assertEqual(len(rows), len(self.ed.tables["offices"]))
        for r in rows:
            self.assertNotIn(" hidden", r.split(">")[0])
        linked = {_resolve(om.HUB, x) for x in re.findall(r'<a class="ofh-office" href="([^"]+)"', h)}
        self.assertEqual(linked, {om.path(o["office_id"]) for o in self.ed.tables["offices"]})
        for o in self.ed.tables["offices"]:
            self.assertIn(f'id="g-{o["unit_id"]}"', h)
        self.assertIn("data-tf-deep", h)
        self.assertIn("(up next)", h)

    # ------------------------------------------------------------------ header and reachability
    def chrome(self, path: str) -> str:
        h = self.html(path)
        head = h[h.index('<header class="masthead site-head"'):h.index("</header>", h.index('<header class="masthead'))]
        foot = h[h.index("<footer"):h.index("</footer>")]
        return head + foot

    def test_header_is_one_row_of_the_new_controls(self):
        h = self.chrome("index.html")
        names = re.findall(r'<a class="nav-top"[^>]*>([^<]+)</a>', h)
        self.assertEqual(names, ["Governments", "Offices", "Elections", "Money", "Learn"])
        for needed in ('id="site-search-input"', 'id="here-bar"', 'id="display-menu"', 'id="theme-toggle"',
                       'id="look-switch-head"', 'id="menu-btn"', 'href="#primary-nav"'):
            self.assertIn(needed, h)
        foot = h[h.index("<footer"):]
        for label in ("About and methods", "Data downloads", "Sources index", "Corrections log", "Not your county?"):
            self.assertIn(f">{label}<", foot)
        self.assertIn("footer-stamp", foot)
        # hub pages mark themselves current
        self.assertRegex(self.chrome(om.HUB), r'<a class="nav-top" href="index.html" aria-current="page">Offices</a>')

    def test_every_page_within_two_clicks(self):
        first = self.links("index.html", self.chrome("index.html"))
        two = set(first)
        for p in first:
            if p in self.site.pages:
                two |= self.links(p)
        missing = []
        for e in self.site.entries:
            if e.thing and e.tab != "overview":
                continue       # an office's other tabs are one more click, from its overview's tab bar
            if e.moved_to:
                continue       # a forwarding page (phase 6 step 4: elections/margins/ etc.); its content is linked
            if e.path != "index.html" and e.path not in two:
                missing.append(e.path)
        self.assertEqual(missing, [])

    # ------------------------------------------------------------------ banner
    def test_unofficial_banner_only_with_2026_unofficial_figures(self):
        bid = 'id="banner-2026-unofficial"'
        # 2026-11-18: elections/results/ (the finder) showed the banner only because its "how to read" legend printed
        # an UNOFFICIAL badge; it shows no 2026 figure, and the legend is now symbols, so it no longer gets the notice.
        # The 2026 Contests tab shows them.
        self.assertIn(bid, self.html("elections/2026g/contests/index.html"))
        self.assertNotIn(bid, self.html("elections/results/index.html"))
        self.assertNotIn(bid, self.html(om.path(MAYOR, "elections")))   # 2015 figures are unofficial, not 2026
        self.assertNotIn(bid, self.html(om.path(MAYOR, "money")))
        self.assertNotIn(bid, self.html("about/index.html"))
        for p in self.paths:
            h = self.html(p)
            if bid in h:
                main = h[h.index("<main"):h.index("</main>")]
                main = re.sub(r'<(dl|ul) class="(?:badge-defs|marks-key)"[^>]*>.*?</\1>', "", main, flags=re.S)
                # 2026-11-18: the unofficial symbol or a section stating it once (test_status_marks.py)
                self.assertRegex(main, r'class="(badge badge-unofficial|smark smark-is-unofficial)"'
                                       r'|data-fmark="unofficial"|data-fscope="unofficial"', p)
                self.assertIn("2026", re.sub(r"<[^>]+>", " ", main), p)

    # ------------------------------------------------------------------ cross-links
    def test_cross_links_to_office_pages(self):
        card = self.html("money/campaigns/south-bend/index.html")
        card = card[card.index('id="r-2023g-south-bend-mayor"'):]
        card = card[:card.index("</article>")]
        self.assertIn(om.path(MAYOR, "money"), self.links("money/campaigns/south-bend/index.html", card))
        # phase 6 step 3 (2026-11-16): the place page is now governments/south-bend/ (places/south-bend/ forwards)
        self.assertIn(om.path(MAYOR), self.links("governments/south-bend/index.html"))
        res = self.html("elections/results/index.html")
        row = res[res.index('id="contest-2023g-south-bend-mayor"'):]
        row = row[:row.index("</tr>")]
        self.assertIn(om.path(MAYOR, "elections"), self.links("elections/results/index.html", row))
        # phase 6 step 4 (2026-11-16): the explorer payload that also carried the office links is gone; the election
        # page's contest links its office (tools/tests/test_phase6_elections.py)
        self.assertNotIn('id="elx-data"', res)

    def test_related_rail_offers_the_office_page(self):
        from civic import related
        probe = Site(self.ed, self.out)
        items = {i.key: i for i in related.related_items(probe.page("state/your-legislators/index.html"),
                                                         office_id="state-house-5")}
        self.assertTrue(items["office"].href.endswith("offices/state-house-5/index.html"))
        items = {i.key: i for i in related.related_items(probe.page("places/south-bend/index.html"), "south-bend")}
        self.assertTrue(items["offices"].href.endswith("offices/index.html#g-south-bend"))
        keys = [k for k in related.ORDER if k in items]
        self.assertEqual(list(items), keys)

    # ------------------------------------------------------------------ search
    def index(self) -> dict:
        return json.loads((self.out / "assets" / "search-index.json").read_text(encoding="utf-8"))

    def test_index_has_a_tab_item_per_office_tab(self):
        d = self.index()
        self.assertEqual(d["v"], 2)
        tab_items = {i[3] for i in d["items"] if i[0] == search.T_TAB}
        for o in self.ed.tables["offices"]:
            for k in om.office_tabs(self.ed, o["office_id"]):
                if k != "overview":
                    self.assertIn(om.path(o["office_id"], k), tab_items)
        for it in d["items"]:            # party tags sit in the display-only tag field, never in keywords
            if len(it) > 5:
                self.assertNotRegex(it[5], r"\b(democrat|republican|libertarian)\b")

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_search_keyword_queries_land_on_the_tab(self):
        js = (SITE_DIR / "static" / "js" / "search.js").read_text(encoding="utf-8")
        core = js[:js.index('if (typeof window !== "undefined")')]
        queries = ["mayor money", "mayor primary", "campaign finance mayor", "sheriff results", "democrat",
                   "republican", "mueller"]
        prog = core + """
var d = JSON.parse(require("fs").readFileSync(process.argv[2], "utf8"));
var items = civicSearchCore.prepare(d);
var out = {};
JSON.parse(process.argv[3]).forEach(function (q) {
  out[q] = civicSearchCore.rank(items, q).slice(0, 5).map(function (x) { return x[1].href; });
});
process.stdout.write(JSON.stringify(out));
"""
        f = self.out / "search-test.js"
        f.write_text(prog, encoding="utf-8")
        r = subprocess.run(["node", str(f), str(self.out / "assets" / "search-index.json"), json.dumps(queries)],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        got = json.loads(r.stdout)
        self.assertEqual(got["mayor money"][0], om.path(MAYOR, "money"))
        self.assertEqual(got["mayor primary"][0], om.path(MAYOR, "elections"))
        self.assertEqual(got["campaign finance mayor"][0], om.path(MAYOR, "money"))
        self.assertEqual(got["sheriff results"][0], om.path("county-sheriff", "elections"))
        # party tags are display-only: a party word finds no officeholder by their tag
        holders = {i[3] for i in self.index()["items"] if i[0] == search.T_HOLDER}
        for q in ("democrat", "republican"):
            for href in got[q]:
                self.assertNotIn(href, holders, q)
        self.assertTrue(got["mueller"])


if __name__ == "__main__":
    unittest.main()
