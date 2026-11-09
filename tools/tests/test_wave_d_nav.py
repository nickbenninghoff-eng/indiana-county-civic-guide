"""Wave D, batch 6: navigation and hubs.

- Nav bar: Your place · Topics ▾ · Learn ▾ · About; each Topics group heading links to its hub; JS-off <details> menus.
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

FIXTURE = Path(__file__).parent / "fixtures" / "anchors_before_wave_d6.json"
ID_RE = re.compile(r'\sid="([^"]+)"')
HUB, HOW, YP, HOME = "elections/index.html", "elections/how-it-works/index.html", "your-governments/index.html", "index.html"
SAMPLE = ["elections/calendar/index.html", "money/budgets/index.html", "history/people/index.html", "teach/index.html",
          "about/sources/index.html", "data/results/index.html", "run/school-board/index.html"]
PAGES = [HUB, HOW, YP, HOME] + SAMPLE


def moved_map(html: str) -> dict:
    m = re.search(r'<script type="application/json" id="moved-anchors">(.*?)</script>', html, re.S)
    return json.loads(m.group(1)) if m else {}


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
    def test_nav_bar_is_your_place_topics_learn_about(self):
        for p in PAGES:
            nav = self.nav(p)
            self.assertRegex(nav, r'^<nav class="nav" aria-label="Primary"><ul class="nav-list"><li><a href="[^"]*" '
                                  r'(aria-current="page" )?class="nav-place">Your place</a></li>')
            self.assertEqual(re.findall(r'<summary[^>]*>([^<]+)</summary>', nav), ["Topics", "Learn"])
            self.assertRegex(nav, r'</details></li><li><a href="[^"]*index.html"[^>]*>About</a></li></ul>$')
            self.assertIn('id="ref-menu"', nav)          # kept: older fixtures and app.js use it
            self.assertIn('id="learn-menu"', nav)
            for old in (">Reference<", ">Paths<", "Find your governments", "Judges &amp; questions", ">For teachers<",
                        ">About &amp; methods<"):
                self.assertNotIn(old, nav, p)

    def test_each_topic_heading_links_to_its_hub(self):
        nav = self.nav(HUB)
        heads = re.findall(r'<p class="menu-head" id="nav-topic-[a-z-]+"><a class="menu-hub" href="([^"]+)"[^>]*>([^<]+)<', nav)
        self.assertEqual([html.unescape(t) for _, t in heads], [t["name"] for t in sitemap.TOPICS])
        self.assertEqual([self.resolve(HUB, h)[0] for h, _ in heads], [t["hub"] for t in sitemap.TOPICS])

    def test_section_hubs_reachable_from_the_topics_menu(self):
        nav = self.nav(HUB)
        targets = {self.resolve(HUB, h)[0] for h in re.findall(r'href="([^"]+)"', nav)}
        for hub in ("places/index.html", "elections/index.html", "money/index.html", "community/index.html",
                    "history/index.html", "data/index.html", "your-governments/index.html"):
            self.assertIn(hub, targets)

    def test_menu_labels_follow_the_renames(self):
        nav = self.nav(HUB)
        for label in ("Judges &amp; ballot questions", "Who lives here", "People in local history", "By the numbers",
                      "Close races (margins)", "How elections work", "Community &amp; history", "For teachers and groups",
                      "Learning paths"):
            self.assertIn(f">{label}<", nav)
        self.assertNotIn(">People<", nav)

    def test_every_menu_leaf_is_a_page(self):
        for t in sitemap.TOPICS:
            self.assertIn(t["hub"], self.site.by_path)
            for leaf in t["leaves"]:
                for p in (leaf if isinstance(leaf, tuple) else (leaf,)):
                    self.assertIn(p.split("#")[0], self.site.by_path, p)

    def test_learn_lists_every_path_with_its_first_stop(self):
        nav = self.nav(HOME)
        for p in sitemap.PATHS:
            href = f'{p["stops"][0]["page"]}#path-{p["id"]}-1'
            self.assertIn(f'href="{href}"', nav)
            self.assertIn(f">{p['title']}<", nav)

    def test_current_page_marked(self):
        self.assertRegex(self.nav(YP), r'<a href="index.html" aria-current="page" class="nav-place">Your place</a>')
        self.assertRegex(self.nav("elections/calendar/index.html"), r'<summary class="is-current">Topics</summary>')
        self.assertRegex(self.nav("teach/index.html"), r'<summary class="is-current">Learn</summary>')
        self.assertRegex(self.nav(HUB), r'<a class="menu-hub" href="index.html" aria-current="page">Elections')

    # ------------------------------------------------------------------ breadcrumbs
    def test_breadcrumbs_come_from_the_sitemap(self):
        for p in PAGES:
            if p == HOME:
                continue
            h = self.html[p]
            self.assertNotRegex(h, r'<p class="eyebrow mono">(Reference|Context)', p)
            self.assertIn('<nav class="crumbs eyebrow mono" aria-label="Breadcrumb">', h, p)
        cal = self.html["elections/calendar/index.html"]
        self.assertRegex(cal, r'<li><span>Topics</span></li><li><span class="crumb-sep" aria-hidden="true"> · </span>'
                              r'<a href="../index.html">Elections</a></li>.*?<span aria-current="page">Calendar</span>')
        ppl = self.html["history/people/index.html"]
        self.assertIn('<a href="../../community/index.html">Community &amp; history</a>', ppl)
        self.assertIn('<span aria-current="page">People in local history</span>', ppl)

    def test_crumbs_rules(self):
        bp = self.site.by_path
        self.assertEqual(sitemap.crumbs(bp, "index.html"), [])
        self.assertEqual(sitemap.crumbs(bp, "indiana/index.html"), [])
        self.assertEqual(sitemap.crumbs(bp, "money/campaigns/how-it-works/index.html"),
                         [("Topics", None), ("Money", "money/index.html"), ("Campaign finance", "money/campaigns/index.html"),
                          ("How reporting works", None)])
        self.assertEqual(sitemap.crumbs(bp, "teach/index.html"), [("Learn", None), ("For teachers", None)])
        self.assertEqual(sitemap.crumbs(bp, "data/results/index.html")[-1], ("Election results", None))
        for e in self.site.entries:   # every topic page names its topic, and the hub the crumb links to exists
            t = sitemap.topic_of(e.path)
            if t is not None:
                self.assertIn(t["hub"], bp)
                self.assertEqual(e.group, t["name"], e.path)

    # ------------------------------------------------------------------ elections hub + how-it-works
    def test_every_old_elections_index_id_resolves(self):
        before = json.loads(FIXTURE.read_text(encoding="utf-8"))["ids"][HUB]
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
        self.assertEqual([self.resolve(HUB, c)[0] for c in cards], [p for p, _ in E.HUB_CARDS])
        self.assertEqual(len(cards), 8)
        self.assertIn("<h1>Elections</h1>", h)
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
        before = json.loads(FIXTURE.read_text(encoding="utf-8"))["ids"][YP]
        mm = moved_map(self.html[YP])["a"]
        lost = []
        for i in before:
            if i in self.ids[YP] or i.startswith("src-"):
                continue
            if i not in mm:
                lost.append(i)
                continue
            path, frag = self.resolve(YP, mm[i])
            self.assertIn(frag or i, self.ids[path], i)
        self.assertEqual(lost, [])
        # citation ids: every source the old page cited is still cited (cards keep the layer and office sources)
        old_src = {i for i in before if i.startswith("src-")}
        self.assertEqual(sorted(old_src - self.ids[YP]), [])

    def test_your_place_path_stops_and_meetings(self):
        for sid in ("find", "offices", "meetings", "tbl-office-types"):
            self.assertIn(sid, self.ids[YP])
        h = self.html[YP]
        sites = re.findall(r'<li class="gov-site" data-layer="([^"]+)"', h)
        self.assertGreaterEqual(len(sites), 30)          # no server-side hidden: JS off lists every government
        self.assertNotIn('class="gov-site" data-layer="state" hidden', h)

    def test_home_links_to_your_place(self):
        self.assertIn('<p class="layers-more"><a href="your-governments/index.html">Your place</a>', self.html[HOME])

    # ------------------------------------------------------------------ scripts
    def test_scripts_ascii_no_innerhtml(self):
        for name in ("nav.js", "your_place.js", "moved.js"):
            src = (SITE_DIR / "static" / "js" / name).read_text(encoding="utf-8")
            src.encode("ascii")
            self.assertNotIn("innerHTML", src)
        self.assertIn("map.p", (SITE_DIR / "static" / "js" / "moved.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
