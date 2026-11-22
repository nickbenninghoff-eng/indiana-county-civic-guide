"""Wave D, batch 6: navigation and hubs.

- Nav bar (rewritten 2026-11-16, phase 6 step 1): Governments · Offices · Elections · Money · Learn, each linking to its
  hub with a short JS-off <details> dropdown; Your place is the header chip, About is in the footer.
- Renames (review 1.4): Topics, Community & history, Learn, Who lives here, People in local history,
  Judges & ballot questions, Your place, nav label "By the numbers"; the hero breadcrumb comes from the sitemap.
- elections/index.html is the Elections hub; the explainer moved to elections/how-it-works/ and every old id is
  forwarded (tests/fixtures/anchors_before_wave_d6.json, taken from the built site before the batch).
- your-governments/ is "Your place": no picker, no seat diagram; one card per government; old ids kept or forwarded.
Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import html
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

import build  # noqa: E402
from civic import sitemap  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.layers import build_layers  # noqa: E402
from civic.shell import Site  # noqa: E402
from pages import elections as E  # noqa: E402

from anchor_fixtures import anchor_fixture  # noqa: E402  (old-anchor fixtures without retired data-block ids)
FIXTURE = Path(__file__).parent / "fixtures" / "anchors_before_wave_d6.json"
ID_RE = re.compile(r'\sid="([^"]+)"')
HUB, HOW, YP, HOME = "elections/index.html", "elections/how-it-works/index.html", "your-governments/index.html", "index.html"
SAMPLE = ["elections/calendar/index.html", "money/budgets/index.html", "people/notable/index.html", "teach/index.html",
          "learn/index.html",
          "about/sources/index.html", "data/results/index.html", "run/school-board/index.html"]
PAGES = [HUB, HOW, YP, HOME] + SAMPLE


def moved_map(html: str) -> dict:
    m = re.search(r'<script type="application/json" id="moved-anchors">(.*?)</script>', html, re.S)
    return json.loads(m.group(1)) if m else {}


def banner_left(anchor: str, page_html: str) -> bool:
    """Phase 6 step 1 (2026-11-16): the 2026 UNOFFICIAL banner now shows only on pages that display unofficial 2026
    figures (civic/shell.py shows_unofficial), so its id may leave a page that has none. True only for a banner id on
    such a page; every other old id must still be there."""
    from civic.shell import shows_unofficial
    if not anchor.startswith("banner-"):
        return False
    main = page_html[page_html.index("<main"):page_html.index("</main>")]
    return not shows_unofficial(main, anchor[len("banner-"):][:4])


class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.site = Site(cls.ed, Path(cls.tmp.name))
        build.discover_builders()
        for p in PAGES:
            build.BUILDERS[p](cls.site)
        cls.site.write()
        cls.html = {p: (Path(cls.tmp.name) / p).read_text(encoding="utf-8") for p in PAGES}
        cls.ids = {p: set(ID_RE.findall(h)) for p, h in cls.html.items()}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def nav(self, page):
        h = self.html[page]
        return h[h.index('<nav class="nav"'):h.index('</nav>', h.index('<nav class="nav"'))]

    def resolve(self, page, href):
        path, _, frag = href.partition("#")
        return posixpath.normpath(posixpath.join(posixpath.dirname(page), path)), frag

    # ------------------------------------------------------------------ nav bar
    # Rewritten 2026-11-16 (phase 6 step 1, planning/design-direction-2026-11-16.md D1): the Wave D bar
    # "Your place · Topics · Learn · About" became Governments · Offices · Elections · Money · Learn, each a link to its
    # hub plus a short <details> dropdown; Your place is the header's "My place" chip and About sits in the footer.
    # The same guarantees are kept: one bar on every page, hubs linked, renamed labels, JS-off menus, current page
    # marked, every page reachable (tools/tests/test_phase6_offices.py checks two clicks for every sitemap page).
    def header(self, page):
        h = self.html[page]
        i = h.index('<header class="masthead site-head"')
        return h[i:h.index("</header>", i)]

    def footer(self, page):
        h = self.html[page]
        return h[h.index("<footer"):h.index("</footer>")]

    def test_nav_bar_is_governments_offices_elections_money_learn(self):
        names = [i["name"] for i in sitemap.NAV]
        self.assertEqual(names, ["Governments", "Offices", "Elections", "Money", "Learn"])
        for p in PAGES:
            nav = self.nav(p)
            self.assertTrue(nav.startswith('<nav class="nav" aria-label="Primary"><ul class="nav-list">'), p)
            self.assertEqual(re.findall(r'<a class="nav-top" href="[^"]*"(?: aria-current="page")?>([^<]+)</a>', nav),
                             names, p)
            self.assertEqual(re.findall(r'<span class="visually-hidden">More in ([^<]+)</span>', nav), names, p)
            for item in sitemap.NAV:
                self.assertIn(f'id="{item["menu_id"]}"', nav)
                menu = nav[nav.index(f'id="{item["menu_id"]}"'):]
                menu = menu[:menu.index("</details>")]
                self.assertLessEqual(len(re.findall(r"<li>", menu)), sitemap.MAX_DROPDOWN, (p, item["name"]))
            self.assertIn('id="ref-menu"', nav)          # kept: older fixtures and app.js use it
            self.assertIn('id="learn-menu"', nav)
            for old in (">Topics<", ">Reference<", ">Paths<", "Find your governments", "Judges &amp; questions",
                        ">For teachers<", ">About &amp; methods<", 'class="nav-place"'):
                self.assertNotIn(old, nav, p)
            # Your place is the chip; About and the rest of the old About menu are in the footer
            self.assertIn('id="here-bar"', self.header(p))
            for label in ("About and methods", "Data downloads", "Sources index", "Corrections log", "Not your county?"):
                self.assertIn(f">{label}<", self.footer(p), p)

    def test_each_nav_item_links_to_its_hub(self):
        nav = self.nav(HUB)
        tops = re.findall(r'<a class="nav-top" href="([^"]+)"', nav)
        self.assertEqual([self.resolve(HUB, x)[0] for x in tops], [i["hub"] for i in sitemap.NAV])

    def test_section_hubs_reachable_from_the_header(self):
        chrome = self.header(HUB) + self.footer(HUB)
        targets = {self.resolve(HUB, h)[0] for h in re.findall(r'href="([^"]+)"', chrome)}
        for hub in ("governments/index.html", "offices/index.html", "elections/index.html", "money/index.html",
                    "community/index.html", "history/index.html", "data/index.html", "your-governments/index.html",
                    "learn/index.html", "about/index.html"):
            self.assertIn(hub, targets)

    def test_menu_labels_follow_the_renames(self):
        nav = self.nav(HUB)
        # phase 6 step 4 (2026-11-16): "By the numbers" became "Compare elections"
        for label in ("Judges &amp; ballot questions", "What counts as a budget", "Compare elections",
                      "How elections work", "Learning paths"):
            self.assertIn(f">{label}<", nav)
        # phase 6 people (2026-11-16): "People" is now the person hub in the Offices menu; the notable list keeps its
        # renamed label, so a bare "People" link never opens the notable list
        self.assertEqual(re.findall(r'href="([^"]+)">People<', nav), ["../people/index.html"])
        # the Wave D labels that left the dropdowns (6 links at most) keep their wording where the pages are listed
        hub = self.html["elections/index.html"] + self.html[HOME]
        self.assertIn("Close races", hub)

    def test_every_menu_leaf_is_a_page(self):
        for t in sitemap.TOPICS:
            self.assertIn(t["hub"], self.site.by_path)
            for leaf in t["leaves"]:
                for p in (leaf if isinstance(leaf, tuple) else (leaf,)):
                    self.assertIn(p.split("#")[0], self.site.by_path, p)
        for item in sitemap.NAV:
            self.assertIn(item["hub"], self.site.by_path)
            for target, _ in item["links"]:
                self.assertIn(target.split("#")[0], self.site.by_path, target)

    def test_learn_leads_to_every_path_with_its_first_stop(self):
        nav = self.nav(HOME)
        self.assertIn('href="learn/index.html#paths"', nav)   # Learn > Learning paths: the Learn hub's list (2026-11-18)
        hub = self.html["learn/index.html"]      # the list moved from the home page to the Learn hub
        self.assertIn('id="paths"', hub)
        for p in sitemap.PATHS:
            self.assertIn(f'href="../{p["stops"][0]["page"]}#path-{p["id"]}-1"', hub)

    def test_current_page_marked(self):
        self.assertRegex(self.nav(HUB), r'<a class="nav-top" href="index.html" aria-current="page">Elections</a>')
        self.assertRegex(self.nav("elections/calendar/index.html"),
                         r'<li class="nav-item is-current"><a class="nav-top" href="../index.html">Elections</a>')
        # phase 6 (2026-11-18): the Learn hub is learn/index.html; teach/ (lesson kits) sits under it
        self.assertRegex(self.nav("learn/index.html"),
                         r'<li class="nav-item is-current"><a class="nav-top" href="index.html" aria-current="page">Learn</a>')
        self.assertRegex(self.nav("teach/index.html"),
                         r'<li class="nav-item is-current"><a class="nav-top" href="../learn/index.html">Learn</a>')
        self.assertRegex(self.nav(YP), r'<li class="nav-item is-current"><a class="nav-top" href="../governments/index.html">'
                                       r'Governments</a>')
        self.assertEqual(self.nav("about/sources/index.html").count("is-current"), 0)

    # ------------------------------------------------------------------ breadcrumbs
    def test_breadcrumbs_come_from_the_sitemap(self):
        for p in PAGES:
            if p == HOME:
                continue
            h = self.html[p]
            self.assertNotRegex(h, r'<p class="eyebrow mono">(Reference|Context)', p)
            self.assertIn('<nav class="crumbs eyebrow mono" aria-label="Breadcrumb">', h, p)
        cal = self.html["elections/calendar/index.html"]
        self.assertRegex(cal, r'<ol><li><a href="../index.html">Elections</a></li><li><span class="crumb-sep" '
                              r'aria-hidden="true"> › </span><span aria-current="page">Calendar</span></li></ol>')
        # phase 6 (2026-11-16): the notable-people list is now people/notable/, under People
        ppl = self.html["people/notable/index.html"]
        self.assertIn('<a href="../index.html">People</a>', ppl)
        self.assertIn('<span aria-current="page">Notable people</span>', ppl)

    def test_crumbs_rules(self):
        bp = self.site.by_path
        self.assertEqual(sitemap.crumbs(bp, "index.html"), [])
        self.assertEqual(sitemap.crumbs(bp, "indiana/index.html"), [])
        self.assertEqual(sitemap.crumbs(bp, "money/campaigns/how-it-works/index.html"),
                         [("Money", "money/index.html"), ("Campaign money", "money/campaigns/index.html"),
                          ("How reporting works", None)])
        self.assertEqual(sitemap.crumbs(bp, "teach/index.html"), [("Learn", "learn/index.html"), ("For teachers", None)])
        self.assertEqual(sitemap.crumbs(bp, "data/results/index.html"),
                         [("Data", "data/index.html"), ("Election results", None)])
        self.assertEqual(sitemap.crumbs(bp, "elections/index.html"), [("Elections", None)])
        self.assertEqual(sitemap.crumbs(bp, "offices/index.html"), [("Offices", None)])
        self.assertEqual(sitemap.crumbs(bp, "offices/south-bend-mayor/money/index.html"),
                         [("Offices", "offices/index.html"), ("City of South Bend", "offices/index.html#g-south-bend"),
                          ("Mayor", "offices/south-bend-mayor/index.html"), ("Money", None)])
        for e in self.site.entries:   # every topic page names its topic, and the hub the crumb links to exists
            t = sitemap.topic_of(e.path)
            if t is not None:
                self.assertIn(t["hub"], bp)
                self.assertEqual(e.group, t["name"], e.path)
            for _label, target in sitemap.crumbs(bp, e.path):
                if target:
                    self.assertIn(target.split("#")[0], bp, e.path)

    # ------------------------------------------------------------------ elections hub + how-it-works
    def test_every_old_elections_index_id_resolves(self):
        before = anchor_fixture(FIXTURE)["ids"][HUB]
        mm = moved_map(self.html[HUB])
        lost = []
        for i in before:
            if i in self.ids[HUB]:
                continue
            dest = mm.get("a", {}).get(i) or next((v for k, v in mm.get("p", {}).items() if i.startswith(k)), None)
            if not dest:
                lost.append(i)
                continue
            path, frag = self.resolve(HUB, dest)
            self.assertEqual(path, HOW, i)
            self.assertIn(frag or i, self.ids[HOW], i)
        self.assertEqual(lost, [])

    def test_moved_map_points_at_ids_that_left(self):
        mm = moved_map(self.html[HUB])
        for k in mm["a"]:
            self.assertNotIn(k, self.ids[HUB], k)
        self.assertEqual(mm["p"], {"src-": "how-it-works/index.html"})

    def test_how_it_works_keeps_every_section(self):
        for sid in ("offices", "primaries", "general", "voting", "county", "vacancies", "school-boards", "questions",
                    "candidate-info"):
            self.assertIn(sid, self.ids[HOW])
            self.assertIn(f"{sid}-h", self.ids[HOW])
        self.assertIn("<h1>How Indiana elections work</h1>", self.html[HOW])

    def test_hub_cards(self):
        h = self.html[HUB]
        cards = re.findall(r'<article class="card ehub-card"[^>]*><h3 class="card-title"><a href="([^"]+)">', h)
        # phase 6 step 4 (2026-11-16): the hub leads with the next election and every election; four doors follow
        self.assertEqual([self.resolve(HUB, c)[0] for c in cards], [p for p, _, _ in E.HUB_DOORS])
        self.assertEqual(len(cards), 4)
        self.assertIn('<h1 class="thing-title">Elections</h1>', h)
        self.assertIn('id="next"', h)
        self.assertNotIn("Reference", h[h.index('<main'):])

    def test_vote_smarter_stop_moved_with_the_explainer(self):
        stop = next(p for p in sitemap.PATHS if p["id"] == "vote-smarter")["stops"][4]
        self.assertEqual((stop["page"], stop["anchor"]), (HOW, "candidate-info"))
        self.assertIn("candidate-info", self.ids[HOW])

    # ------------------------------------------------------------------ your place
    def test_your_place_has_no_picker_and_no_diagram(self):
        h = self.html[YP]
        self.assertNotIn("data-picker", h)
        self.assertNotIn('class="layer ', h)
        self.assertNotIn('class="seat-group"', h)
        self.assertIn("<h1>Your place</h1>", h)

    def test_your_place_card_per_government_with_every_seat_fact(self):
        h = self.html[YP]
        layers = build_layers(self.ed)["layers"]
        for L in layers.values():
            rid = L.layer_id.replace(":", "-")
            start = h.index(f'id="layer-{rid}"')
            start = h.rindex("<li ", 0, start)
            nxt = [i for i in (h.find('<li class="gov-item yp-card', start + 5), h.find('<div class="yp-group"', start),
                               h.find("</section>", start)) if i > 0]
            card = h[start:min(nxt)]
            self.assertIn(f'data-elected="{L.elected}"', card)
            self.assertIn(f'data-vote="{L.vote}"', card)
            self.assertIn(f'data-appointed="{L.appointed}"', card)
            self.assertNotIn(" hidden", card[:card.index(">")])   # JS off: every card shows
            text = html.unescape(re.sub(r"<[^>]+>", "", card))
            for g in L.groups:
                if g.kinds:
                    self.assertIn(f"{g.label}: {g.summary()}", text, rid)
                    for n in g.notes:
                        if n:
                            self.assertIn(n, text, rid)
            if L.note:
                self.assertIn(L.note, text, rid)

    def test_your_place_inline_place_list_links_every_place(self):
        h = self.html[YP]
        places = build_layers(self.ed)["places"]
        links = re.findall(r'<a class="yp-choice" href="([^"]+)" data-yp-place="([^"]+)"', h)
        self.assertEqual(sorted(i for _, i in links), sorted(p["id"] for p in places))
        for href, pid in links:
            self.assertIn(self.resolve(YP, href)[0], self.site.by_path, pid)

    def test_your_place_old_ids_kept_or_forwarded(self):
        before = anchor_fixture(FIXTURE)["ids"][YP]
        mm = moved_map(self.html[YP])["a"]
        lost = []
        for i in before:
            if i in self.ids[YP] or i.startswith("src-") or banner_left(i, self.html[YP]):
                continue
            if i not in mm:
                lost.append(i)
                continue
            path, frag = self.resolve(YP, mm[i])
            self.assertIn(frag or i, self.ids[path], i)
        self.assertEqual(lost, [])
        # citation ids: every source the old page cited is still cited (cards keep the layer and office sources), or,
        # when the data no longer cites it on this page (2026-11-18: GOV-072/073, after the board data was merged),
        # forwarded by the "src-" prefix to the sources index, which lists every source
        old_src = {i for i in before if i.startswith("src-")}
        pre = moved_map(self.html[YP]).get("p", {}).get("src-")
        self.assertIsNotNone(pre)
        path, _frag = self.resolve(YP, pre)
        for i in sorted(old_src - self.ids[YP]):
            self.assertIn(i, self.ids[path], i)

    def test_your_place_path_stops_and_meetings(self):
        for sid in ("find", "offices", "meetings", "tbl-office-types"):
            self.assertIn(sid, self.ids[YP])
        h = self.html[YP]
        sites = re.findall(r'<li class="gov-site" data-layer="([^"]+)"', h)
        self.assertGreaterEqual(len(sites), 30)          # no server-side hidden: JS off lists every government
        self.assertNotIn('class="gov-site" data-layer="state" hidden', h)

    def test_home_links_to_your_place(self):
        # phase 6 home (2026-11-18): the seat diagram's "Your place" line became a link in the "Your governments" strip
        self.assertRegex(self.html[HOME], r'<a class="home-mine-yp" href="your-governments/index.html">Your place')

    # ------------------------------------------------------------------ scripts
    def test_scripts_ascii_no_innerhtml(self):
        for name in ("nav.js", "your_place.js", "moved.js"):
            src = (SITE_DIR / "static" / "js" / name).read_text(encoding="utf-8")
            src.encode("ascii")
            self.assertNotIn("innerHTML", src)
        self.assertIn("map.p", (SITE_DIR / "static" / "js" / "moved.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
