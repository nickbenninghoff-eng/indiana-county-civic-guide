"""Phase 6 step 4 (2026-11-16): election pages, the Elections hub, Compare, Find a result, forwarding pages.

- One tabbed page per row of elections.csv (elections/<id>/): Overview and Sources always, Contests when results.csv
  has a contest, Map only for the elections with precinct results (the map's races); the sitemap and the builder read
  the same keys.
- Contests: every contest of the election, with its #contest-<id> anchor, linked to its office's Elections tab;
  primaries grouped by party.
- Overview: turnout as printed with its base; the uncontested count is the Compare rule (612 since 2010 as of the 2026-11-18 data, summed over
  the election pages, the same figure Compare prints).
- Compare: three real-URL tabs carrying the old pages' content and ids; the old addresses are forwarding pages
  (title, one line, a plain link, canonical) whose #moved-anchors send every old id to a page that has it
  (tools/tests/fixtures/anchors_before_phase6_elections.json, taken from the built site before this step).
- Find a result: short, no explorer payload; its old #contest-<id> anchors stay (JS-off) and are forwarded by
  elections.js to the election page (#results-forward); old explorer and turnout ids are forwarded.
- Hub: next ballot from the calendar code with the saved-place slot, then every election (42) newest first, older
  years in a fold that ships open, then four doors. The Elections menu has at most 6 links and none to a moved page.
- Learning-path stops that pointed at moved sections resolve on their new pages.
- Map tab: the "How areas voted" layer limited to the election's races (civic/map.py election_votes).
- Search: elections and their tabs are indexed; forwarding pages are not.
Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import html as htmllib
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
from civic import election_pages as EP  # noqa: E402
from civic import offices as om  # noqa: E402
from civic import search, sitemap  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.map import election_votes, load_votes  # noqa: E402
from civic.shell import Site  # noqa: E402
from pages import elections_numbers as N  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "anchors_before_phase6_elections.json"
ID_RE = re.compile(r'\sid="([^"]+)"')
HUB, RES, CAL, JUDGES = ("elections/index.html", "elections/results/index.html", "elections/calendar/index.html",
                         "elections/judges-and-questions/index.html")
CMP = EP.COMPARE_PATH
OLD = list(EP.MOVED_TO)


def moved_map(page_html: str) -> dict:
    m = re.search(r'id="moved-anchors">(.*?)</script>', page_html)
    return json.loads(m.group(1).replace("<\\/", "</"))["a"] if m else {}


def resolve(page: str, rel: str) -> tuple[str, str]:
    path, _, frag = rel.partition("#")
    return posixpath.normpath(posixpath.join(posixpath.dirname(page), path)), frag


class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name)
        cls.site = site = Site(cls.ed, out)
        build.discover_builders()
        want = [HUB, RES, CAL, JUDGES, *CMP.values(), *OLD, "officeholders/index.html", "elections/how-it-works/index.html",
                "run/index.html"]
        want += [e.path for e in site.entries if e.path.startswith("elections/") and e.thing]
        for p in want:
            if p not in site.pages:
                build.BUILDERS[p](site)
        site.write()
        cls.paths = sorted(site.pages)
        cls._html = {p: (out / p).read_text(encoding="utf-8") for p in cls.paths}
        cls.ids = {p: set(ID_RE.findall(h)) for p, h in cls._html.items()}
        cls.index = json.loads((out / "assets" / "search-index.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def html(self, p):
        return self._html[p]

    def main(self, p):
        h = self.html(p)
        return h[h.index("<main"):h.index("</main>")]

    # ------------------------------------------------------------------ one page per election
    def test_every_election_has_its_tabs(self):
        self.assertEqual(len(self.ed.elections), 42)
        votes = load_votes(self.ed)
        mapped = {r["eid"] for r in votes["races"]}
        self.assertEqual(mapped, {"2020g", "2022g", "2024g"})
        for eid in self.ed.elections:
            keys = EP.election_tabs(self.ed, eid)
            self.assertEqual(keys[0], "overview")
            self.assertEqual(keys[-1], "sources")
            self.assertEqual("contests" in keys, bool(EP.contests(self.ed, eid)), eid)
            self.assertEqual("map" in keys, eid in mapped, eid)
            for k in ("overview", "contests", "map", "sources"):
                self.assertEqual(EP.path(eid, k) in self.site.by_path, k in keys, (eid, k))
                self.assertEqual(EP.path(eid, k) in self._html, k in keys, (eid, k))
            nav = self.html(EP.path(eid))
            tabs = nav[nav.index('<nav class="tabs"'):]
            tabs = tabs[:tabs.index("</nav>")]
            self.assertEqual(len(re.findall(r'class="tab-link"', tabs)), len(keys), eid)

    def test_titles_and_crumbs(self):
        e = self.ed.elections["2023p"]
        self.assertEqual(EP.title(e), "2023 municipal primary")
        self.assertEqual(EP.title(self.ed.elections["2013s"]), "2013 special election")
        self.assertEqual(sitemap.crumbs(self.site.by_path, EP.path("2024g", "map")),
                         [("Elections", HUB), ("2024 general election", "elections/2024g/index.html"), ("Map", None)])

    def test_contests_tab_lists_every_contest_and_links_its_office(self):
        for eid in ("2024g", "2019p", "2013s", "1963g", "2026g"):
            h = self.html(EP.path(eid, "contests"))
            for c in EP.contests(self.ed, eid):
                self.assertIn(f'id="contest-{c["contest_id"]}"', h, c["contest_id"])
                u = om.path(c["office_id"], "elections") if c["office_id"] else None
                if u and u in self.site.by_path:
                    li = h[h.index(f'id="contest-{c["contest_id"]}"'):]
                    li = li[:li.index("</li>")]
                    self.assertIn(f'../../../offices/{c["office_id"]}/elections/index.html', li, c["contest_id"])

    def test_primary_grouped_by_party(self):
        h = self.main(EP.path("2023p", "contests"))
        d, r = h.index('id="party-d"'), h.index('id="party-r"')
        self.assertLess(d, r)                                    # alphabetical by party name, never by result
        self.assertIn('id="party-none"', h)                      # the public question on every ballot
        for c in EP.contests(self.ed, "2023p"):
            sec = "party-" + (c["party_primary"].lower() or "none")
            start = h.index(f'id="{sec}"')
            self.assertGreater(h.index(f'id="contest-{c["contest_id"]}"'), start)

    def test_overview_turnout_and_base(self):
        for eid in ("2024g", "2023p"):
            e = self.ed.elections[eid]
            h = htmllib.unescape(re.sub(r"<[^>]+>", "", self.main(EP.path(eid))))
            self.assertIn(f"{float(e['turnout_pct']):.1f}% of registered voters cast a ballot", h)
            self.assertIn(f"{int(e['registered']):,} registered voters", h)
            self.assertIn(f"{int(e['ballots_cast']):,} ballots cast", h)
        h = self.main(EP.path("1963g"))
        self.assertIn("Turnout is not recorded", h)

    def test_uncontested_count_matches_compare(self):
        """612 races since 2010 had no contest: the Compare figure equals the sum of the election pages' counts."""
        races = N.margin_races(self.ed)
        unc = sum(1 for r in races if r["kind"] == "unc")
        # 612 since the gap-fill merges of 2026-11-18 (608 before): four races became measurable as uncontested from
        # the merged data (vote_for printed on the canvass; HD5/HD8 2026 primaries noted wholly in the county)
        self.assertEqual(unc, 612)
        per = 0
        for eid, e in self.ed.elections.items():
            rs = N.election_races(self.ed, eid)
            if e["date"] >= "2010":
                per += sum(1 for r in rs if r["kind"] == "unc")
                if rs:
                    n = sum(1 for r in rs if r["kind"] == "unc")
                    txt = htmllib.unescape(re.sub(r"<[^>]+>", "", self.main(EP.path(eid))))
                    self.assertIn(f"{n} of the {len(rs)} race", txt, eid)
        self.assertEqual(per, 612)
        lede = re.search(r'<p class="mg-lede">(.*?)</p>', self.html(CMP["margins"]), re.S).group(1)
        self.assertIn("612 of the", re.sub(r"<[^>]+>", "", lede))

    def test_closest_races_link_to_their_contest(self):
        h = self.main(EP.path("2024g"))
        sec = h[h.index('id="closest"'):h.index('id="around"')]
        links = re.findall(r'href="contests/index\.html#(contest-[a-z0-9-]+)"', sec)
        self.assertEqual(len(links), 3)
        for a in links:
            self.assertIn(a, self.ids[EP.path("2024g", "contests")])

    def test_2026_unofficial_marked(self):
        # since the county canvass of 11/13/2026 most 2026 figures are official: the notice is on a tab exactly when
        # the tab shows an unofficial figure (the Contests tab always does: 42 lines stay unofficial)
        for k in ("overview", "contests"):
            h = self.html(EP.path("2026g", k))
            shows = re.search(r'data-fmark="unofficial"|data-fscope="unofficial"', self.main(EP.path("2026g", k)))
            self.assertEqual('id="banner-2026-unofficial"' in h, bool(shows), k)
        self.assertRegex(self.main(EP.path("2026g", "contests")), r'data-fscope="unofficial"')
        # 2026-11-18: mixed official and unofficial since the county canvass; the word heads the tab
        self.assertIn('<p class="fscope-line fscope-unofficial"><strong>Unofficial</strong>',
                      self.main(EP.path("2026g", "contests")))
        self.assertNotIn('id="banner-2026-unofficial"', self.html(EP.path("2024g", "contests")))

    def test_neighbour_links(self):
        h = self.main(EP.path("2024g"))
        for eid in ("2024p", "2026p", "2022g", "2026g"):
            self.assertIn(f'href="../{eid}/index.html"', h)

    # ------------------------------------------------------------------ map tab
    def test_map_tab_is_this_elections_races(self):
        votes = load_votes(self.ed)
        for eid in ("2020g", "2022g", "2024g"):
            h = self.main(EP.path(eid, "map"))
            self.assertIn(f'data-vote-eid="{eid}"', h)
            ids = re.findall(r'id="race-([a-z0-9-]+)"', h)
            want = [r["id"] for r in votes["races"] if r["eid"] == eid]
            self.assertEqual(ids, want)
            self.assertNotIn('data-hash="off"', h)               # #race-<id> links open one race
        vv = election_votes(votes, "2022g")
        keys = {r["office"] for r in vv["races"]}
        self.assertEqual({o["key"] for o in vv["offices"]}, keys)
        for o in vv["offices"]:
            if o.get("districts"):
                have = {r["district"] for r in vv["races"] if r["office"] == o["key"]}
                self.assertEqual(set(o["districts"]), have)
        self.assertIsNone(election_votes(votes, "2023g"))

    def test_contest_map_links_resolve(self):
        h = self.main(EP.path("2024g", "contests"))
        for rid in re.findall(r'href="\.\./map/index\.html#race-([a-z0-9-]+)"', h):
            self.assertIn(f"race-{rid}", self.ids[EP.path("2024g", "map")])

    # ------------------------------------------------------------------ Compare and the forwarding pages
    def test_compare_tabs(self):
        for key, label, p in EP.COMPARE_TABS:
            h = self.html(p)
            bar = h[h.index('<nav class="tabs"'):]
            bar = bar[:bar.index("</nav>")]
            self.assertEqual(len(re.findall(r'class="tab-link"', bar)), 3)
            self.assertRegex(bar, rf'aria-current="page">{re.escape(htmllib.escape(label))}<')
            self.assertNotRegex(self.main(p), r'class="[^"]*m-party')   # accent/ink ramp only

    def test_old_pages_forward(self):
        for old, new in EP.MOVED_TO.items():
            h = self.html(old)
            self.assertIn(f'<link rel="canonical" href="{posixpath.relpath(new, posixpath.dirname(old))}">', h)
            self.assertRegex(h, r'<a href="[^"]+" id="moved-link" data-forward>')
            self.assertLess(len(h), 120_000, old)

    def test_every_old_anchor_resolves(self):
        """Every id the hub, landscape, margins, turnout and results pages had before this step is still on its page or
        forwarded by its #moved-anchors to a built page that has it (or keeps it, for a destination without #)."""
        before = json.loads(FIXTURE.read_text(encoding="utf-8"))["ids"]
        lost = []
        for page, ids in before.items():
            moved = moved_map(self.html(page))
            for i in ids:
                if i in self.ids[page]:
                    continue
                if i.startswith("banner-") and not re.search(
                        r'smark-is-unofficial|badge-unofficial|data-fmark="unofficial"|data-fscope="unofficial"',
                        self.main(page)):
                    continue        # the 2026 notice shows only on pages with unofficial 2026 figures
                dest = moved.get(i)
                if dest:
                    target, frag = resolve(page, dest)
                    if target in self.ids and (frag or i) in self.ids[target]:
                        continue
                lost.append((page, i, dest))
        self.assertEqual(lost, [])

    def test_moved_maps_name_only_ids_that_left(self):
        for page in [HUB, RES, *OLD]:
            for old, dest in moved_map(self.html(page)).items():
                self.assertNotIn(old, self.ids[page], (page, old))
                target, frag = resolve(page, dest)
                self.assertIn(target, self.ids, (page, old, dest))
                self.assertIn(frag or old, self.ids[target], (page, old, dest))

    # ------------------------------------------------------------------ Find a result
    def test_results_page_is_short_and_forwards_contests(self):
        h = self.html(RES)
        self.assertLess(len(h.encode("utf-8")), 700_000)
        self.assertNotIn('id="elx-data"', h)
        fwd = json.loads(re.search(r'id="results-forward">(.*?)</script>', h).group(1).replace("<\\/", "</"))
        for c in self.ed.contests.values():
            if c["election_id"] < "2010" or c["election_id"] not in self.ed.elections:
                continue
            self.assertIn(f'id="contest-{c["contest_id"]}"', h)      # JS off: the row is the result
            eid = fwd["x"].get(c["contest_id"]) or c["contest_id"][:5]
            target, _ = resolve(RES, fwd["e"][eid])
            self.assertIn(f'contest-{c["contest_id"]}', self.ids[target])
        for eid in self.ed.elections:
            self.assertIn(f'href="../{eid}/index.html"', h)

    # ------------------------------------------------------------------ hub
    def test_hub_order_and_timeline(self):
        h = self.main(HUB)
        self.assertLess(h.index('id="next"'), h.index('id="timeline"'))
        self.assertLess(h.index('id="timeline"'), h.index('id="pages"'))
        for eid in self.ed.elections:
            self.assertIn(f'href="{eid}/index.html"', h)
        fold = re.search(r'<details [^>]*id="timeline-earlier"[^>]*>', h).group(0)
        self.assertIn("data-fold", fold)
        self.assertIn(" open", fold)                            # JS off: a plain list
        newest = re.findall(r'id="el-([0-9a-z]+)"', h)
        self.assertEqual(newest[:2], ["2026g", "2026p"])
        self.assertIn('data-here-pre="explorer"', h)            # saved place: elections.js
        self.assertRegex(h, r'class="ehub-gov" data-here-unit="south-bend" data-here-layer="municipality:south-bend"')
        for cid in ("card-compare", "card-judges-and-questions", "card-how-it-works", "card-run"):
            self.assertIn(f'id="{cid}"', h)

    def test_elections_menu(self):
        item = next(i for i in sitemap.NAV if i["name"] == "Elections")
        self.assertLessEqual(len(item["links"]), sitemap.MAX_DROPDOWN)
        for p, _ in item["links"]:
            e = self.site.by_path[p.split("#")[0]]
            self.assertFalse(e.moved_to, p)
        self.assertIn("elections/compare/index.html", [p for p, _ in item["links"]])

    def test_learning_path_stops_resolve(self):
        for path in sitemap.PATHS:
            for s in path["stops"]:
                self.assertNotIn(s["page"], EP.MOVED_TO, s)
                if s["page"].startswith("elections/") and s["page"] in self.ids:
                    self.assertIn(s["anchor"], self.ids[s["page"]], s)

    # ------------------------------------------------------------------ search
    def test_search_indexes_elections_not_forwarders(self):
        items = self.index["items"]
        types = self.index["types"]
        labels = {(types[i[0]], i[1]): i[3] for i in items}
        self.assertEqual(labels[("Election", "2024 general election")], "elections/2024g/index.html")
        self.assertEqual(labels[("Election", "2024 general election › Map")], "elections/2024g/map/index.html")
        hrefs = {i[3] for i in items}
        for old in OLD:
            self.assertFalse([h for h in hrefs if h.split("#")[0] == old], old)


class Static(unittest.TestCase):
    def read(self, rel):
        return (SITE_DIR / rel).read_text(encoding="utf-8")

    def test_scripts_ascii_textcontent_only(self):
        for rel in ("static/js/elections.js", "static/js/map_votes.js", "static/js/search.js"):
            src = self.read(rel)
            self.assertTrue(all(ord(c) < 128 for c in src), rel)
            self.assertNotIn("innerHTML", src, rel)

    def test_elections_js_contracts(self):
        src = self.read("static/js/elections.js")
        for s in ('"results-forward"', "a[data-forward]", "civicHere.mine()", "m.sure(", "hashWins()", "safe(dest)"):
            self.assertIn(s, src)
        self.assertIn('getAttribute("data-vote-eid")', self.read("static/js/map_votes.js"))

    def test_netlify_redirects(self):
        import netlify_prep
        text = self.read("netlify/_redirects")
        for old, new in EP.MOVED_TO.items():
            o, n = "/" + old[:-len("index.html")], "/" + new[:-len("index.html")]
            self.assertRegex(text, rf"(?m)^{re.escape(o)}\s+{re.escape(n)}\s+301!$")
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "st-joseph"
            out.mkdir()
            (out / "index.html").write_text("<title>t</title>\n<p>x</p>\n", encoding="utf-8")
            self.assertEqual(netlify_prep.prepare(out), 0)
            self.assertEqual((out / "_redirects").read_text(encoding="utf-8"), text)

    def test_tabs_keys_added_not_changed(self):
        from civic import tabs as T
        self.assertEqual([k for k in T.TAB_ORDER if k not in ("contests", "map")],
                         ["overview", "elections", "money", "history", "sources"])
        self.assertEqual(T.tab_path("elections/2024g/", "contests"), "elections/2024g/contests/index.html")


if __name__ == "__main__":
    unittest.main()
