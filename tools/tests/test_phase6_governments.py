"""Phase 6 step 3 (2026-11-16): the government pages (governments/<id>/, tabs Overview, Elections, Money, History,
Sources), the Governments hub, and the forwarding pages that replaced places/, places/<id>/, county/ and schools/.

planning/design-direction-2026-11-16.md section 6 step 3; report planning/qa/phase6-governments-2026-11-16.md.

- Which governments: the county, 2 cities, 7 towns, 13 townships, 6 school corporations, and the libraries and
  special units that have money figures. An empty tab is neither built nor linked.
- Figures are reused, never re-derived: the South Bend budget tables (2027 adopted, all funds) and the county's
  counted spending equal the budgets page's.
- Every id the old pages had (fixtures/anchors_before_governments.json) still lands on an id that exists, following
  the forwarding pages' and the overviews' #moved-anchors maps exactly as static/js/moved.js does.
- Neutrality (F6): the community figures are on the Overview only, after the officeholders and Contact; never on the
  Elections or History tab. Money charts carry no party colour.
- The hub: map first, then every government grouped by type; it works as a plain list without JavaScript.
- Netlify 301s are generated for the one-to-one moves (not for schools/, which was split).
Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import json
import posixpath
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = ROOT / "tools" / "site"
sys.path.insert(0, str(SITE_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))   # tests/gov_moved.py

import build  # noqa: E402
import netlify_prep  # noqa: E402
from civic import governments as gm  # noqa: E402
from civic import sitemap  # noqa: E402
from civic import tabs as T  # noqa: E402
from civic.answers import place_budget_row  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site  # noqa: E402
from gov_moved import follow  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "anchors_before_governments.json"
ID_RE = re.compile(r'\sid="([^"]+)"')
HREF_RE = re.compile(r'href="([^"]*)"')
DOLLARS = re.compile(r"\$[\d,]+(?:\.\d+)?")
TABLE_RE = r'<table[^>]*\sid="{tid}"[^>]*>(.*?)</table>'
OLD_PAGES = ["places/index.html", "county/index.html", "schools/index.html"]


def _join(frm: str, rel: str) -> tuple[str, str]:
    path, _, frag = rel.partition("#")
    if not path:
        return frm, frag
    return posixpath.normpath(posixpath.join(posixpath.dirname(frm), path)), frag


class Model(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")

    def test_which_governments(self):
        kinds = [g.kind for g in gm.governments(self.ed)]
        self.assertEqual(kinds.count("county"), 1)
        self.assertEqual(kinds.count("city"), 2)
        self.assertEqual(kinds.count("town"), 7)
        self.assertEqual(kinds.count("township"), 13)
        self.assertEqual(kinds.count("school_corporation"), 6)
        special = [g for g in gm.governments(self.ed) if g.group == "special"]
        self.assertTrue(special, "libraries and special units with money figures")
        for g in special:
            self.assertTrue(g.money_ids, f"{g.gid}: a special unit is listed only when it has money figures")

    def test_tabs_are_omitted_when_empty(self):
        for g in gm.governments(self.ed):
            keys = gm.gov_tabs(self.ed, g.gid)
            self.assertEqual(keys[0], "overview")
            self.assertIn("sources", keys)
            self.assertEqual(list(keys), [k for k in T.TAB_ORDER if k in keys], g.gid)
        self.assertNotIn("elections", gm.gov_tabs(self.ed, "sjcpl"))
        self.assertNotIn("history", gm.gov_tabs(self.ed, "sjcpl"))
        for gid in ("south-bend", "county", "phm", "penn-township"):
            self.assertIn("money", gm.gov_tabs(self.ed, gid), gid)
            self.assertIn("elections", gm.gov_tabs(self.ed, gid), gid)

    def test_nav_points_at_the_hub(self):
        nav = {n["name"]: n for n in sitemap.NAV}
        self.assertEqual(nav["Governments"]["hub"], gm.HUB)
        self.assertLessEqual(len(nav["Governments"]["links"]), 6)
        self.assertEqual(sitemap.nav_of("governments/south-bend/money/index.html")["name"], "Governments")
        flat = json.dumps(sitemap.PATHS)
        self.assertNotIn('"county/index.html"', flat, "PATHS stops point at the government pages")
        self.assertIn("governments/county/index.html", flat)


class Built(unittest.TestCase):
    """The government pages, the hub, the forwarding pages and the budgets page, built into a temporary folder."""

    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        cls.site = site = Site(cls.ed, cls.out)
        build.discover_builders()
        want = [e.path for e in site.entries if e.path.startswith("governments/")]
        want += [p for p in gm.moved_pages(cls.ed)] + ["money/budgets/index.html"]
        for p in want:
            if p not in site.pages:
                build.BUILDERS[p](site)
        site.write()
        cls.paths = sorted(site.pages)
        cls.html = {p: (cls.out / p).read_text(encoding="utf-8") for p in cls.paths}
        cls.ids = {p: set(ID_RE.findall(h)) for p, h in cls.html.items()}
        cls.index = json.loads((cls.out / "assets" / "search-index.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # ---------------------------------------------------------------- pages and tabs
    def test_every_tab_is_built_and_only_built_tabs_are_linked(self):
        for g in gm.governments(self.ed):
            keys = gm.gov_tabs(self.ed, g.gid)
            for k in T.TAB_ORDER:
                p = gm.path(g.gid, k)
                if k in keys:
                    self.assertIn(p, self.html, p)
                else:
                    self.assertNotIn(p, self.html, p)
            ov = gm.path(g.gid)
            for href in HREF_RE.findall(self.html[ov]):
                if href.startswith(("http:", "https:", "mailto:")):
                    continue
                target, _ = _join(ov, href)
                if target.startswith(gm.base(g.gid)):
                    self.assertTrue(target in self.html, f"{ov} links a tab that was not built: {href}")

    # ---------------------------------------------------------------- figures equal the old pages'
    def _table_dollars(self, page: str, tid: str) -> list[str]:
        m = re.search(TABLE_RE.format(tid=re.escape(tid)), self.html[page], re.S)
        self.assertIsNotNone(m, f"{page}: table #{tid}")
        return DOLLARS.findall(re.sub(r"<[^>]+>", " ", m.group(1)))

    def test_south_bend_budget_equals_the_budgets_page(self):
        gov, old = "governments/south-bend/money/index.html", "money/budgets/index.html"
        tables = [i for i in self.ids[gov] if i.startswith("bud-city-south-bend-") and i.endswith("-table")]
        self.assertTrue(tables)
        # phase 6 step 5 (2026-11-18): money/budgets/ is Compare budgets; the unit's charts and tables live only on
        # its Money tab (pages/money.py _unit_charts, the same renderer), and the budgets page forwards their ids there
        for tid in tables:
            self.assertTrue(self._table_dollars(gov, tid), tid)
            self.assertEqual(follow(self.html, self.ids, old, tid), (gov, tid))
        # the 2027 adopted budget (all funds): the same figure in the glance box, the Money tab and the budgets page
        row = place_budget_row(self.ed, "south-bend")
        self.assertEqual(row["year"], "2027")
        fig = f"${int(float(row['amount'])):,}"
        self.assertIn(fig, re.sub(r"<[^>]+>", "", self.html[gov]))

    def test_county_counted_spending_equals_the_budgets_page(self):
        gov = re.sub(r"<[^>]+>", "", self.html["governments/county/money/index.html"])
        old = re.sub(r"<[^>]+>", "", self.html["money/budgets/index.html"])
        m_old = re.search(r"County government: counted spending (\$[\d,]+)", old)
        m_gov = re.search(r"Counted spending (\$[\d,]+)", gov)
        self.assertIsNotNone(m_old)
        self.assertIsNotNone(m_gov)
        self.assertEqual(m_gov.group(1), m_old.group(1))
        for tid in ("sp-county-income-table", "sp-county-purpose-table"):
            self.assertIn(tid, self.ids["governments/county/money/index.html"])

    # ---------------------------------------------------------------- old URLs and anchors
    def _resolve(self, page: str, i: str):
        """Where an old link lands, following #moved-anchors as static/js/moved.js does (tests/gov_moved.py)."""
        return follow(self.html, self.ids, page, i)

    def test_every_old_anchor_resolves(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))["ids"]
        self.assertIn("places/south-bend/index.html", fixture)
        bad = []
        for page, ids in fixture.items():
            self.assertTrue(page in self.html, f"{page} still exists (as a forwarding page)")
            for i in ids:
                r = self._resolve(page, i)
                if r is None or r[1] not in self.ids[r[0]]:
                    bad.append(f"{page}#{i} -> {r}")
        self.assertEqual(bad, [])

    def test_key_old_anchors_land_on_the_right_tab(self):
        cases = {("places/south-bend/index.html", "budget"): "governments/south-bend/money/index.html",
                 ("places/south-bend/index.html", "control"): "governments/south-bend/history/index.html",
                 ("places/south-bend/index.html", "results"): "governments/south-bend/elections/index.html",
                 ("places/south-bend/index.html", "office-south-bend-mayor"): "governments/south-bend/index.html",
                 ("county/index.html", "boards"): "governments/county/index.html",
                 ("county/index.html", "money-county"): "governments/county/money/index.html",
                 ("schools/index.html", "office-phm-board-penn"): "governments/phm/index.html",
                 ("places/index.html", "townships"): gm.HUB}
        for (page, i), want in cases.items():
            r = self._resolve(page, i)
            self.assertIsNotNone(r, f"{page}#{i}")
            self.assertEqual(r[0], want, f"{page}#{i}")

    def test_forwarding_pages(self):
        for old, new in gm.moved_pages(self.ed).items():
            src = self.html[old]
            self.assertIn('rel="canonical"', src, old)
            self.assertIn('class="forward-link"', src, old)   # a plain link: works with JavaScript off
            self.assertIn('id="moved-anchors"', src, old)
            if old == "schools/index.html":
                self.assertNotIn("civic-moved-to", src, "schools/ was split: no single 301 target")
            else:
                self.assertIn(f'<meta name="civic-moved-to" content="{new.split("#")[0]}">', src, old)

    def test_redirects_are_generated(self):
        red = netlify_prep.moved_redirects(self.out)
        self.assertIn("/places/south-bend/  /governments/south-bend/  301!", red)
        self.assertIn("/county/index.html  /governments/county/index.html  301!", red)
        self.assertIn("/places/  /governments/  301!", red)
        self.assertNotIn("/schools/", red)

    # ---------------------------------------------------------------- neutrality
    def test_community_figures_only_on_the_overview_after_contact(self):
        for g in gm.governments(self.ed):
            for k in gm.gov_tabs(self.ed, g.gid):
                src = self.html[gm.path(g.gid, k)]
                if k in ("elections", "history"):
                    self.assertNotIn('id="context"', src, f"{g.gid}/{k}: F6")
                    self.assertNotIn("gov-ctx", src, f"{g.gid}/{k}: F6")
            ov = self.html[gm.path(g.gid)]
            if 'id="context"' in ov:
                self.assertLess(ov.index('id="contact"'), ov.index('id="context"'), g.gid)
                if 'id="officeholders"' in ov:
                    self.assertLess(ov.index('id="officeholders"'), ov.index('id="context"'), g.gid)

    def test_money_tab_uses_no_party_colours(self):
        for g in gm.governments(self.ed):
            if "money" not in gm.gov_tabs(self.ed, g.gid):
                continue
            src = self.html[gm.path(g.gid, "money")]
            for svg in re.findall(r"<svg\b.*?</svg>", src, re.S):
                self.assertNotRegex(svg, r"party-[dro]\b|--party-", f"{g.gid} money chart")

    # ---------------------------------------------------------------- the hub
    def test_hub_lists_every_government_by_group(self):
        hub = self.html[gm.HUB]
        self.assertLess(hub.index('id="map"'), hub.index('id="county"' if 'id="county"' in hub else 'id="cities"'))
        for key in gm.GROUPS:
            if key != "county":
                self.assertIn(f'id="{key}"', hub, key)
        links = {_join(gm.HUB, h)[0] for h in HREF_RE.findall(hub)}
        for g in gm.governments(self.ed):
            self.assertIn(gm.path(g.gid), links, g.gid)
        for p in ("map/index.html", "officeholders/index.html", "your-governments/index.html",
                  "who-handles-this/index.html"):
            self.assertIn(p, links, p)
        # without JavaScript the list is all there: every row is a plain link, nothing hidden
        self.assertNotRegex(hub.split('id="cities"')[1].split("</section>")[0], r"\shidden[\s>=]")

    def test_search_finds_government_tabs(self):
        items = self.index["items"]
        tabs = {r[1]: r for r in items if r[0] == self.index["types"].index("Government")}
        sb = tabs.get("City of South Bend › Money")
        self.assertIsNotNone(sb)
        self.assertEqual(sb[3], "governments/south-bend/money/index.html")
        self.assertIn("budget", sb[5])
        places = {r[1]: r[3] for r in items if r[0] == 0}
        self.assertEqual(places.get("City of South Bend"), "governments/south-bend/index.html")
        stale = [r[3] for r in items if r[3].split("#")[0] in gm.moved_pages(self.ed)]
        self.assertEqual(stale[:5], [], "forwarding pages are not in the search index")


if __name__ == "__main__":
    unittest.main()
