"""Tests for the place-page template (Wave B batch 3, 2026-11-09; site-ux-review-2026-11-09.md section 3.2):
the 22 city, town and township pages under places/<id>/. Since phase 6 step 3 (2026-11-16) they are government
pages with tabs (governments/<id>/; places/<id>/ forwards there), and the Built tests read those tabs.

  - every id the pages had before is still on the same page (fixtures/anchors_before_place_template.json)
  - order: Who holds office now first; the community figures never next to a results or party-control section
  - dedupe: the township explainer once per page; the organization table one row per body, every office in a fold
  - the "More about" rail on all 22 pages, with the campaign money area page; every rail, seat and panel link lands
  - South Bend and Mishawaka council district maps (no party fills, Mishawaka's medium-confidence caveat);
    Walkerton's wards listed, not drawn
  - results: a summary row per race, the charts in a "See all" fold that ships open (JavaScript off)

Builds the place pages and every page they link to from the rail, the seat lines and the map panels into a temporary
folder.  Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import html as _html
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "site"))
sys.path.insert(0, str(Path(__file__).resolve().parent))   # tests/gov_moved.py

import build  # noqa: E402
from civic import related  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site  # noqa: E402
from gov_moved import lands  # noqa: E402
from pages import places  # noqa: E402

from anchor_fixtures import anchor_fixture  # noqa: E402  (old-anchor fixtures without retired data-block ids)
FIXTURE = Path(__file__).parent / "fixtures" / "anchors_before_place_template.json"
ID_RE = re.compile(r'\sid="([^"]+)"')
TOWNSHIPS = ["centre", "clay", "german", "greene", "harris", "liberty", "lincoln", "madison", "olive", "penn",
             "portage", "union", "warren"]


def _norm(p: str) -> str:
    parts = []
    for seg in p.split("/"):
        if seg == "..":
            parts.pop()
        elif seg and seg != ".":
            parts.append(seg)
    return "/".join(parts)


def _sections(html: str) -> list[str]:
    main = html[html.index("<main"):]
    return re.findall(r'<section class="block[^"]*" id="([^"]+)"', main)


def banner_left(anchor: str, page_html: str) -> bool:
    """Phase 6 step 1 (2026-11-16): the 2026 UNOFFICIAL banner now shows only on pages that display unofficial 2026
    figures (civic/shell.py shows_unofficial), so its id may leave a page that has none. True only for a banner id on
    such a page; every other old id must still be there."""
    from civic.shell import shows_unofficial
    if not anchor.startswith("banner-"):
        return False
    main = page_html[page_html.index("<main"):page_html.index("</main>")]
    return not shows_unofficial(main, anchor[len("banner-"):][:4])


class PlaceOrderRule(unittest.TestCase):
    """_place_order: Context last, and never right after officeholders, results or party control."""

    def test_normal(self):
        got = places._place_order({"officeholders", "structure", "results", "control", "budget", "context"})
        self.assertEqual(got, ["officeholders", "structure", "results", "control", "budget", "context"])

    def test_audits_before_context(self):
        got = places._place_order({"officeholders", "structure", "results", "budget", "audits", "context"})
        self.assertEqual(got[-2:], ["audits", "context"])

    def test_no_budget_moves_context_between_neutral_sections(self):
        got = places._place_order({"officeholders", "structure", "unelected", "results", "control", "context"})
        self.assertEqual(got, ["structure", "context", "unelected", "officeholders", "results", "control"])
        got = places._place_order({"officeholders", "structure", "results", "context"})
        self.assertEqual(got, ["context", "structure", "officeholders", "results"])
        for g in (got,):
            i = g.index("context")
            self.assertTrue(i == len(g) - 1 or g[i + 1] not in places.NOT_BESIDE_CONTEXT)

    def test_without_context(self):
        self.assertEqual(places._place_order({"results", "officeholders"}), ["officeholders", "results"])


class Built(unittest.TestCase):
    """Phase 6 step 3 (2026-11-16): the 22 place pages became government pages with tabs (governments/<id>/, pages/
    places.py place_renderers) and places/<id>/ became forwarding pages. These tests now read each place's tabs; an
    old id must still land on an id that exists, through the #moved-anchors maps (tests/gov_moved.py)."""

    @classmethod
    def setUpClass(cls):
        from civic import governments as gm
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        site = Site(cls.ed, cls.out)
        build.discover_builders()
        cls.old_paths = sorted(p for p in build.BUILDERS if re.fullmatch(r"places/[a-z-]+/index\.html", p))
        cls.uids = [p.split("/")[1] for p in cls.old_paths]
        for p in cls.old_paths:
            build.BUILDERS[p](site)            # the forwarding page builds the government's tabs too
        site.write()
        cls.tabs = {u: [gm.path(u, k) for k in gm.gov_tabs(cls.ed, u)] for u in cls.uids}
        cls.paths = sorted(p for ps in cls.tabs.values() for p in ps)
        cls.overview = {u: gm.path(u) for u in cls.uids}
        built = set(cls.old_paths) | set(cls.paths)
        cls.html = {p: (cls.out / p).read_text(encoding="utf-8") for p in sorted(built)}
        targets = set()
        for p in cls.paths:
            for href in cls._checked_hrefs(cls.html[p]):
                path = href.split("#")[0]
                if path:
                    targets.add(_norm((Path(p).parent / path).as_posix()))
        targets -= built
        site2 = Site(cls.ed, cls.out)
        for t in sorted(targets):
            build.BUILDERS[t](site2)
        site2.write()
        cls.ids = {}
        for t in built | targets:
            cls.ids[t] = set(ID_RE.findall((cls.out / t).read_text(encoding="utf-8")))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def ov(self, uid: str) -> str:
        return self.html[self.overview[uid]]

    def tab(self, uid: str, key: str) -> str:
        from civic import governments as gm
        return self.html[gm.path(uid, key)]

    @staticmethod
    def _checked_hrefs(html: str) -> list[str]:
        """Links in the rail, in the office rows, and in the district map panels' JSON (map.js 'more' and 'href')."""
        out = []
        nav = re.search(r'<nav class="related".*?</nav>', html, re.S)
        if nav:
            out += re.findall(r'href="([^"]+)"', nav.group(0))
        for m in re.finditer(r'<li class="gov-office".*?</li>', html, re.S):
            out += [x for x in re.findall(r'href="([^"]+)"', m.group(0)) if "sources/index.html#src-" not in x]
        data = re.search(r'id="cmap-data">(.*?)</script>', html, re.S)
        if data:
            for e in json.loads(data.group(1).replace("<\\/", "</")).values():
                out.append(e["href"])
                out += [m[1] for m in e.get("more", [])]
        return [_html.unescape(x) for x in out]

    def _lands(self, page: str, href: str) -> bool:
        path, _, frag = href.partition("#")
        target = page if not path else _norm((Path(page).parent / path).as_posix())
        if target not in self.ids:
            return False
        if not frag or frag in self.ids[target]:
            return True
        return lands(self.html, self.ids, target, frag) if target in self.html else False

    # ------------------------------------------------------------------ anchors
    def test_every_old_anchor_lands(self):
        before = anchor_fixture(FIXTURE)["ids"]
        self.assertEqual(sorted(before), self.old_paths)
        lost = [(p, i) for p, ids in before.items() for i in ids
                if not lands(self.html, self.ids, p, i) and not i.startswith("banner-")]
        self.assertEqual(lost, [])

    def test_no_duplicate_ids(self):
        for p in self.paths:
            ids = ID_RE.findall(self.html[p])
            dup = sorted({i for i in ids if ids.count(i) > 1})
            self.assertEqual(dup, [], p)

    # ------------------------------------------------------------------ order and dedupe
    def test_order(self):
        """Overview: at a glance, where it is, how it's organised, offices, appointed boards, contact, then the
        community figures last (F6: never beside results or party control, which are on other tabs)."""
        want = ["where", "structure", "officeholders", "unelected", "contact", "context"]
        for u in self.uids:
            h = self.ov(u)
            secs = re.findall(r'<section class="tsec[^"]*" id="([^"]+)"', h[h.index("<main"):])
            self.assertEqual(secs, [s for s in want if s in secs], u)
            self.assertIn("officeholders", secs, u)
            if "context" in secs:
                self.assertEqual(secs[-1], "context", u)
            for k in ("elections", "history"):
                if self.overview[u].replace("index.html", f"{k}/index.html") in self.html:
                    self.assertNotIn('id="context"', self.tab(u, k), (u, k))
            # the old sub-blocks that moved inside their topic keep their ids and headings
            for sub in ("what-townships-do", "places-inside", "townships"):
                if f'id="{sub}"' in h:
                    self.assertRegex(h, rf'<div class="sub-block" id="{sub}">\s*<h3 id="{sub}-h"', u)

    def test_township_explainer_once(self):
        what = self.ed.unit_types["township"]["what_it_does"]
        key = _html.escape(what[:80], quote=False)
        for t in TOWNSHIPS:
            self.assertEqual(self.ov(f"{t}-township").count(key), 1, t)

    def test_one_row_per_body(self):
        sb = self.ov("south-bend")
        table = re.search(r'<table id="bodies-south-bend".*?</table>', sb, re.S).group(0)
        self.assertEqual(table.count("<tr") - 1, 3)                      # mayor, clerk, common council
        self.assertIn("9 (6 district seats, 3 at-large)", table)
        # the table sits in a fold that ships open (JavaScript off) and every office is one row below it
        fold = re.search(r'<details class="fold-details see-all" id="bodies-south-bend-all"[^>]*>', sb).group(0)
        self.assertIn(" open", fold)
        for oid in ("south-bend-mayor", "south-bend-clerk", "south-bend-council-d1", "south-bend-council-at-large"):
            self.assertRegex(sb, rf'<li class="gov-office[^"]*" id="office-{oid}"', oid)
        wk = self.ov("walkerton")
        self.assertIn("5 (4 ward seats, 1 at-large)", wk)
        self.assertIn("2027 (Ward 3, Ward 4, at-large); 2030 (Ward 1, Ward 2)", wk)
        penn = self.ov("penn-township")
        self.assertIn('id="office-penn-township-trustee"', penn)

    # ------------------------------------------------------------------ rail and links
    def test_rail_on_every_place_overview_with_campaign_money(self):
        for u in self.uids:
            nav = re.search(r'<nav class="related" id="related".*?</nav>', self.ov(u), re.S)
            self.assertIsNotNone(nav, u)
            self.assertIn(f'href="../../money/campaigns/{u}/index.html"', nav.group(0), u)
            self.assertIn('data-related="run"', nav.group(0), u)          # how to get involved, on every page

    def test_every_rail_office_and_panel_link_lands(self):
        bad, n = [], 0
        for p in self.paths:
            for href in self._checked_hrefs(self.html[p]):
                n += 1
                if not self._lands(p, href):
                    bad.append((p, href))
        self.assertEqual(bad, [])
        self.assertGreater(n, 200)          # the rails, about 80 office rows and the 12 map panels were all read

    def test_office_rows_link_the_office_page(self):
        sb = self.ov("south-bend")
        row = re.search(r'<li class="gov-office[^"]*" id="office-south-bend-council-d5">.*?</li>', sb, re.S).group(0)
        self.assertIn('href="../../offices/south-bend-council-d5/index.html"', row)
        self.assertIn("Next election 2027", row)

    # ------------------------------------------------------------------ district maps
    def _panel(self, uid):
        h = self.ov(uid)
        return json.loads(re.search(r'id="cmap-data">(.*?)</script>', h, re.S).group(1).replace("<\\/", "</"))

    def test_city_district_maps(self):
        for uid in ("south-bend", "mishawaka"):
            h = self.ov(uid)
            m = re.search(r'<div class="cmap dmap[^"]*place-dmap.*?</svg>', h, re.S)
            self.assertIsNotNone(m, uid)
            svg = m.group(0)
            links = re.findall(r'<a href="#office-([a-z0-9-]+)" class="cmap-a"', svg)
            self.assertEqual(sorted(links), [f"{uid}-council-d{i}" for i in range(1, 7)], uid)
            self.assertNotRegex(svg, r'party-|m-party|cmap-shade')         # fills never encode party or a value
            for k, e in self._panel(uid).items():
                facts = dict(e["f"])
                self.assertIn("Council member", facts)
                self.assertIn("Next election", facts)
                labels = " ".join(x[0] for x in e["more"])
                self.assertIn("campaign money", labels)
                self.assertTrue(e["cav"], k)
            # the map links choose the member's row
            self.assertIn(f'id="office-{uid}-council-d1"', h)
        mi = self._panel("mishawaka")
        self.assertTrue(all(any("medium" in c for c in e["cav"]) for e in mi.values()))
        self.assertIn("Confidence: medium", self.ov("mishawaka"))

    def test_walkerton_wards_listed_not_drawn(self):
        h = self.ov("walkerton")
        self.assertNotIn('class="cmap', h)
        self.assertIn('id="council-wards"', h)
        self.assertIn("street descriptions", h)
        for w in range(1, 5):
            self.assertIn(f'id="office-walkerton-council-ward-{w}"', h)

    def test_no_map_elsewhere(self):
        for u in self.uids:
            if u not in ("south-bend", "mishawaka"):
                self.assertNotIn("place-dmap", self.ov(u), u)

    # ------------------------------------------------------------------ results and progressive enhancement
    def test_results_summary_and_fold(self):
        n = 0
        for u in self.uids:
            p = self.overview[u].replace("index.html", "elections/index.html")
            if p not in self.html:
                continue
            h = self.html[p]
            if "results-summary-" not in h:
                continue
            n += 1
            table = re.search(rf'<table id="results-summary-{u}".*?</table>', h, re.S).group(0)
            n_rows = table.count("<tr") - 1
            fold = h[h.index(f'id="results-charts-{u}"'):]
            self.assertEqual(len(re.findall(r'<figure class="chart[^"]*" id="res-', fold)), n_rows, p)
            self.assertRegex(h, rf'<details class="fold-details see-all" id="results-charts-{u}" open')
        self.assertGreater(n, 10)

    def test_folds_ship_open(self):
        for p in self.paths:
            for tag in re.findall(r'<details\b[^>]*data-(?:one|fold)="[^"]*"[^>]*>', self.html[p]):
                self.assertIn(" open", tag, (p, tag))

    def test_mayoral_table_folded_under_chart(self):
        for uid in ("south-bend", "mishawaka"):
            h = self.tab(uid, "elections")
            sub = h[h.index('id="mayor-results"'):]
            self.assertLess(sub.index(f'id="mayor-results-{uid}"'), sub.index(f'id="mayor-table-{uid}-all"'))
            self.assertLess(sub.index(f'id="mayor-table-{uid}-all"'), sub.index(f'id="mayor-table-{uid}"'))


class RelatedAdditions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.site = Site(cls.ed, Path(tempfile.gettempdir()) / "unused")

    def test_towns_get_the_general_run_page(self):
        keys = {i.key: i for i in related.related_items(self.site.page("places/lakeville/index.html"), "lakeville")}
        self.assertTrue(keys["run"].href.endswith("run/index.html"))
        sb = {i.key: i for i in related.related_items(self.site.page("places/south-bend/index.html"), "south-bend")}
        self.assertTrue(sb["run"].href.endswith("run/city-council/index.html"))

    def test_seat_items(self):
        p = self.site.page("places/south-bend/index.html")
        items = related.seat_items(p, "south-bend-council-d1", campaign_races={"2023g-south-bend-council-1"},
                                   on_page=["2023g-south-bend-council-1"])
        self.assertEqual([i.key for i in items], ["on-page", "results", "campaigns"])
        self.assertEqual(items[0].href, "#res-2023g-south-bend-council-1")
        self.assertTrue(items[2].href.endswith("money/campaigns/south-bend/index.html#r-2023g-south-bend-council-1"))
        # nothing invented: no campaign race given, no on-page contest
        self.assertEqual([i.key for i in related.seat_items(p, "south-bend-council-d1")], ["results"])
        with self.assertRaises(KeyError):
            related.seat_items(p, "no-such-office")
        with self.assertRaises(ValueError):
            related.campaign_race_anchor("bad id")


if __name__ == "__main__":
    unittest.main()
