"""Tests for the place-page template (Wave B batch 3, 2026-11-09; site-ux-review-2026-11-09.md section 3.2):
the 22 city, town and township pages under places/<id>/.

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

import build  # noqa: E402
from civic import related  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site  # noqa: E402
from pages import places  # noqa: E402

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
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        site = Site(cls.ed, cls.out)
        build.discover_builders()
        cls.paths = sorted(p for p in build.BUILDERS if re.fullmatch(r"places/[a-z-]+/index\.html", p))
        for p in cls.paths:
            build.BUILDERS[p](site)
        site.write()
        cls.html = {p: (cls.out / p).read_text(encoding="utf-8") for p in cls.paths}
        targets = set()
        for p, h in cls.html.items():
            for href in cls._checked_hrefs(h):
                path = href.split("#")[0]
                if path:
                    targets.add(_norm((Path(p).parent / path).as_posix()))
        targets -= set(cls.paths)
        site2 = Site(cls.ed, cls.out)
        for t in sorted(targets):
            build.BUILDERS[t](site2)
        site2.write()
        cls.ids = {}
        for t in set(cls.paths) | targets:
            cls.ids[t] = set(ID_RE.findall((cls.out / t).read_text(encoding="utf-8")))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    @staticmethod
    def _checked_hrefs(html: str) -> list[str]:
        """Links in the rail, in the seat lines, and in the district map panels' JSON (map.js 'more' and 'href')."""
        out = []
        nav = re.search(r'<nav class="related".*?</nav>', html, re.S)
        if nav:
            out += re.findall(r'href="([^"]+)"', nav.group(0))
        for m in re.finditer(r'<span class="seat-links">.*?</a></span>', html, re.S):
            out += re.findall(r'href="([^"]+)"', m.group(0))
        data = re.search(r'id="cmap-data">(.*?)</script>', html, re.S)
        if data:
            for e in json.loads(data.group(1).replace("<\\/", "</")).values():
                out.append(e["href"])
                out += [m[1] for m in e.get("more", [])]
        return [_html.unescape(x) for x in out]

    def _lands(self, page: str, href: str) -> bool:
        path, _, frag = href.partition("#")
        target = page if not path else _norm((Path(page).parent / path).as_posix())
        return target in self.ids and (not frag or frag in self.ids[target])

    # ------------------------------------------------------------------ anchors
    def test_every_old_anchor_is_still_on_its_page(self):
        before = json.loads(FIXTURE.read_text(encoding="utf-8"))["ids"]
        self.assertEqual(sorted(before), self.paths)
        lost = [(p, i) for p, ids in before.items() for i in ids if i not in self.ids[p]]
        self.assertEqual(lost, [])

    def test_no_duplicate_ids(self):
        for p, h in self.html.items():
            ids = ID_RE.findall(h)
            dup = sorted({i for i in ids if ids.count(i) > 1})
            self.assertEqual(dup, [], p)

    # ------------------------------------------------------------------ order and dedupe
    def test_order(self):
        for p, h in self.html.items():
            secs = _sections(h)
            self.assertEqual(secs[0], "officeholders", p)
            self.assertEqual(secs, [s for s in places.PLACE_ORDER if s in secs], p)
            if "context" in secs:
                i = secs.index("context")
                self.assertNotIn(secs[i - 1], places.NOT_BESIDE_CONTEXT, p)
            # the old top-level sections that moved inside their topic keep their ids and headings
            for sub in ("what-townships-do", "places-inside", "townships", "mayor-results"):
                if f'id="{sub}"' in h:
                    self.assertRegex(h, rf'<div class="sub-block" id="{sub}">\s*<h3 id="{sub}-h"', p)

    def test_township_explainer_once(self):
        what = self.ed.unit_types["township"]["what_it_does"]
        key = _html.escape(what[:80], quote=False)
        for t in TOWNSHIPS:
            h = self.html[f"places/{t}-township/index.html"]
            self.assertEqual(h.count(key), 1, t)

    def test_one_row_per_body(self):
        sb = self.html["places/south-bend/index.html"]
        table = re.search(r'<table id="bodies-south-bend".*?</table>', sb, re.S).group(0)
        self.assertEqual(table.count("<tr") - 1, 3)                      # mayor, clerk, common council
        self.assertIn("9 (6 district seats, 3 at-large)", table)
        # every office row is still there, inside a See-all fold that ships open
        fold = re.search(r'<details class="fold-details see-all" id="offices-south-bend-all"[^>]*>', sb).group(0)
        self.assertIn(" open", fold)
        self.assertIn('<table id="offices-south-bend"', sb[sb.index('id="offices-south-bend-all"'):])
        wk = self.html["places/walkerton/index.html"]
        self.assertIn("5 (4 ward seats, 1 at-large)", wk)
        self.assertIn("2027 (Ward 3, Ward 4, at-large); 2030 (Ward 1, Ward 2)", wk)
        # a township's offices are already one row per body: the office table as it was, no fold
        penn = self.html["places/penn-township/index.html"]
        self.assertIn('<table id="offices-penn-township"', penn)
        self.assertNotIn('id="bodies-penn-township"', penn)

    # ------------------------------------------------------------------ rail and links
    def test_rail_on_every_place_page_with_campaign_money(self):
        for p, h in self.html.items():
            nav = re.search(r'<nav class="related" id="related".*?</nav>', h, re.S)
            self.assertIsNotNone(nav, p)
            uid = p.split("/")[1]
            self.assertIn(f'href="../../money/campaigns/{uid}/index.html"', nav.group(0), p)
            self.assertIn('data-related="run"', nav.group(0), p)          # how to get involved, on every page

    def test_every_rail_seat_and_panel_link_lands(self):
        bad, n = [], 0
        for p, h in self.html.items():
            for href in self._checked_hrefs(h):
                n += 1
                if not self._lands(p, href):
                    bad.append((p, href))
        self.assertEqual(bad, [])
        self.assertGreater(n, 300)          # the rails, about 80 seat lines and the 12 map panels were all read

    def test_seat_lines_link_result_and_campaign_money(self):
        sb = self.html["places/south-bend/index.html"]
        row = sb[sb.index('id="office-south-bend-council-d5"'):]
        row = row[:row.index("</details>")]
        self.assertIn('href="#res-2023g-south-bend-council-5"', row)
        self.assertIn("elections/results/index.html#contest-2023g-south-bend-council-5", row)
        self.assertIn("money/campaigns/south-bend/index.html#r-2023g-south-bend-council-5", row)

    # ------------------------------------------------------------------ district maps
    def _panel(self, page):
        h = self.html[page]
        return json.loads(re.search(r'id="cmap-data">(.*?)</script>', h, re.S).group(1).replace("<\\/", "</"))

    def test_city_district_maps(self):
        for uid in ("south-bend", "mishawaka"):
            h = self.html[f"places/{uid}/index.html"]
            m = re.search(r'<div class="cmap dmap[^"]*place-dmap.*?</svg>', h, re.S)
            self.assertIsNotNone(m, uid)
            svg = m.group(0)
            links = re.findall(r'<a href="#office-([a-z0-9-]+)" class="cmap-a"', svg)
            self.assertEqual(sorted(links), [f"{uid}-council-d{i}" for i in range(1, 7)], uid)
            self.assertNotRegex(svg, r'party-|m-party|cmap-shade')         # fills never encode party or a value
            panel = self._panel(f"places/{uid}/index.html")
            for k, e in panel.items():
                facts = dict(e["f"])
                self.assertIn("Council member", facts)
                self.assertIn("Next election", facts)
                labels = " ".join(x[0] for x in e["more"])
                self.assertIn("results explorer", labels)
                self.assertIn("campaign money", labels)
                self.assertTrue(e["cav"], k)
            # the map links choose the member's line (pick_one item keyed by office id)
            self.assertIn(f'data-one="{uid}-council-d1"', h)
        mi = self._panel("places/mishawaka/index.html")
        self.assertTrue(all(any("medium" in c for c in e["cav"]) for e in mi.values()))
        self.assertIn("Confidence: medium", self.html["places/mishawaka/index.html"])

    def test_walkerton_wards_listed_not_drawn(self):
        h = self.html["places/walkerton/index.html"]
        self.assertNotIn('class="cmap', h)
        self.assertIn('id="council-wards"', h)
        self.assertIn("street descriptions", h)
        for w in range(1, 5):
            self.assertIn(f'id="office-walkerton-council-ward-{w}"', h)

    def test_no_map_elsewhere(self):
        for p, h in self.html.items():
            if p.split("/")[1] not in ("south-bend", "mishawaka"):
                self.assertNotIn("place-dmap", h, p)

    # ------------------------------------------------------------------ results and progressive enhancement
    def test_results_summary_and_fold(self):
        for p, h in self.html.items():
            if 'id="results"' not in h or "results-summary-" not in h:
                continue
            uid = p.split("/")[1]
            table = re.search(rf'<table id="results-summary-{uid}".*?</table>', h, re.S).group(0)
            n_rows = table.count("<tr") - 1
            fold = h[h.index(f'id="results-charts-{uid}"'):]
            self.assertEqual(len(re.findall(r'<figure class="chart[^"]*" id="res-', fold)), n_rows, p)
            self.assertRegex(h, rf'<details class="fold-details see-all" id="results-charts-{uid}" open')

    def test_folds_ship_open(self):
        for p, h in self.html.items():
            for tag in re.findall(r'<details\b[^>]*data-(?:one|fold)="[^"]*"[^>]*>', h):
                if 'data-fold="gaps"' in tag or 'data-fold="sources"' in tag or "data-fold" in tag:
                    self.assertIn(" open", tag, (p, tag))

    def test_mayoral_table_folded_under_chart(self):
        for uid in ("south-bend", "mishawaka"):
            h = self.html[f"places/{uid}/index.html"]
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
