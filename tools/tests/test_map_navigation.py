"""Tests for the 2026-11-09 map-navigation batch: the district maps on state/your-legislators/ and county/, the
"show one" items (civic/pick_one.py, static/js/pick_one.js) on those pages, the budgets page below its money map
and the Schools page, and the anchors those pages had before.

Since phase 6 step 3 (2026-11-16) county/ and schools/ are forwarding pages: the county checks read
governments/county/ and the schools checks the Governments hub.

Builds the four pages (and the pages they forward to) into a temporary folder.
Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

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
from civic.data import Edition  # noqa: E402
from civic.district_map import neighbor_fills  # noqa: E402
from civic.holder_rows import NO_HOLDER, holder_state  # noqa: E402
from civic.shell import Site  # noqa: E402
from gov_moved import follow, lands  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "anchors_before_map_batch.json"
ID_RE = re.compile(r'\sid="([^"]+)"')
LEG, COUNTY, BUDGETS, SCHOOLS = ("state/your-legislators/index.html", "county/index.html",
                                 "money/budgets/index.html", "schools/index.html")
PAGES = [LEG, COUNTY, BUDGETS, SCHOOLS]
# phase 6 step 3 (2026-11-16): county/ and schools/ forward to the government pages; the county's district map and
# office rows are on its Overview, its results (still show-one items) on its Elections tab, and the school
# corporations are on the Governments hub's map, each linking to its own page
GOV_COUNTY, GOV_COUNTY_EL, HUB = ("governments/county/index.html", "governments/county/elections/index.html",
                                  "governments/index.html")


def _svg(html: str) -> str:
    return re.search(r'<svg class="cmap-svg".*?</svg>', html, re.S).group(0)


def _areas(html: str) -> list[tuple[str, str]]:
    """(href, data-uid) of every clickable map area."""
    return re.findall(r'<a href="([^"]+)" class="cmap-a" data-uid="([^"]+)"', _svg(html))


def _panel_data(html: str) -> dict:
    raw = re.search(r'<script type="application/json" id="cmap-data">(.*?)</script>', html, re.S).group(1)
    return json.loads(raw.replace("<\\/", "</"))


def _tag_with_id(html: str, i: str) -> str:
    m = re.search(r'<[a-z0-9]+\b[^>]*\sid="' + re.escape(i) + r'"[^>]*>', html)
    return m.group(0) if m else ""



def _forwarded_here(html: str, old_id: str, ids: set) -> bool:
    """An id the page dropped on purpose is forwarded by its #moved-anchors map (static/js/moved.js) to an id that is on
    this same page, e.g. the merged Superior Court 6 office (2026-11-09: #office-superior-court-judge-chapleau ->
    #office-superior-court-judge-woods). Ids forwarded to another page are not accepted here."""
    m = re.search(r'id="moved-anchors">(.*?)</script>', html, re.S)
    if not m:
        return False
    dest = json.loads(m.group(1)).get("a", {}).get(old_id, "")
    return "#" in dest and dest.split("#", 1)[0] in ("", "index.html") and dest.split("#", 1)[1] in ids

class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name)
        site = Site(cls.ed, out)
        build.discover_builders()
        for p in PAGES + ["about/sources/index.html"]:   # phase 6 step 5: old #src- ids of the budgets page land there
            build.BUILDERS[p](site)
        # phase 6 step 5 (2026-11-18): money/budgets/ is Compare budgets; each unit's old block is on its government's
        # Money tab, so every government page is built for the old-anchor checks
        for e in site.entries:
            if e.path.startswith("governments/") and e.path not in site.pages and e.path in build.BUILDERS:
                build.BUILDERS[e.path](site)
        site.write()
        cls.html = {p: (out / p).read_text(encoding="utf-8") for p in sorted(site.pages)}
        cls.ids = {p: ID_RE.findall(h) for p, h in cls.html.items()}
        cls.idset = {p: set(v) for p, v in cls.ids.items()}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # ------------------------------------------------------------ anchors and progressive enhancement
    def test_every_old_anchor_still_on_its_page(self):
        before = json.loads(FIXTURE.read_text(encoding="utf-8"))["ids"]
        lost = [(p, i) for p, ids in before.items() for i in ids
                if not lands(self.html, self.idset, p, i) and not (
                    i in self.idset[p] or _forwarded_here(self.html[p], i, self.idset[p]))]
        self.assertEqual(lost, [])

    def test_no_duplicate_ids(self):
        for p, ids in self.ids.items():
            dup = sorted({i for i in ids if ids.count(i) > 1})
            self.assertEqual(dup, [], p)

    def test_items_ship_open(self):
        """With JavaScript off every area's detail is on the page: each show-one item is written open."""
        for p in (LEG, GOV_COUNTY_EL):   # phase 6 step 5: Compare budgets has no show-one items
            html = self.html[p]
            items = re.findall(r"<details\b[^>]*\bdata-one=\"[^\"]+\"[^>]*>", html)
            self.assertTrue(items, p)
            for tag in items:
                self.assertIn(" open", tag, (p, tag[:120]))
                self.assertIn('data-fold="one"', tag, (p, tag[:120]))

    def test_old_unit_and_district_ids_choose_their_item(self):
        """An old #id of a unit or district section is on, or inside, an element that names its item (data-one or
        data-one-for), so static/js/pick_one.js opens that item when the address points at it."""
        checks = {LEG: ["office-state-house-5", "results-house-7", "res26-house-5", "cf-senate-8"]}
        # phase 6 step 5 (2026-11-18): an old budgets-page unit id lands on that government's Money tab
        for uid in ("county", "south-bend", "mishawaka", "phm", "centre-township", "walkerton"):
            got = follow(self.html, self.idset, BUDGETS, uid)
            self.assertEqual(got, (f"governments/{uid}/money/index.html", "budget"), uid)
        # phase 6 step 3: an old schools/ or county/ id lands on the corporation's page or on the county's office row
        for uid in ("sbcsc", "phm", "school-city-mishawaka", "john-glenn", "union-north", "new-prairie"):
            self.assertEqual(follow(self.html, self.idset, SCHOOLS, uid)[0], f"governments/{uid}/index.html", uid)
        for i in ("office-county-council-a", "office-county-commissioner-d1", "office-county-sheriff"):
            self.assertEqual(follow(self.html, self.idset, COUNTY, i), (GOV_COUNTY, i))
        for p, ids in checks.items():
            html = self.html[p]
            for i in ids:
                pos = html.find(f' id="{i}"')
                self.assertGreater(pos, 0, (p, i))
                tag = _tag_with_id(html, i)
                if "data-one" in tag:
                    continue
                # otherwise it must sit inside an open <details data-one> (nearest unclosed one before it)
                before = html[:pos]
                opened = [m.start() for m in re.finditer(r"<details\b[^>]*data-one=", before)]
                closed = before.count("</details>")
                self.assertTrue(opened, (p, i))
                self.assertGreater(len(re.findall(r"<details\b", before)), closed, (p, i))

    # ------------------------------------------------------------ legislators
    def test_legislator_map_links_each_district_to_its_item(self):
        html = self.html[LEG]
        areas = _areas(html)
        self.assertEqual(len(areas), 9)
        for href, uid in areas:
            self.assertTrue(href.startswith("#district-"), href)
            self.assertIn(f'data-one="{uid}"', _tag_with_id(html, href[1:]))

    def test_legislator_panel_labels_filing_year_basis(self):
        data = _panel_data(self.html[LEG])
        self.assertEqual(len(data), 9)
        for uid, e in data.items():
            labels = [f[0] for f in e["f"]]
            self.assertIn("Member now", labels, uid)
            self.assertIn("Next election", labels, uid)
            if any(l.startswith("Campaign money:") for l in labels):
                self.assertTrue(any("FILED in each calendar year" in c and "not election-cycle totals" in c
                                    for c in e["cav"]), uid)
            for l, v in e["f"]:
                if l.startswith("Campaign money:"):
                    self.assertIn("filings", v)

    def test_legislator_tables_all_reachable(self):
        html = self.html[LEG]
        for chamber, num in (("house", "5"), ("house", "6"), ("house", "7"), ("house", "8"), ("house", "21"),
                             ("senate", "8"), ("senate", "9"), ("senate", "10"), ("senate", "11")):
            self.assertIn(f'id="results-{chamber}-{num}-table"', html)
            self.assertIn(f'id="cf-{chamber}-{num}"', html)
        for t in ("districts-table", "cf-matrix", "cf-long", "cross-county-2026"):
            self.assertIn(f'id="{t}"', html)

    # ------------------------------------------------------------ county
    def test_county_map_covers_every_district_seat(self):
        html = self.html[GOV_COUNTY]
        areas = _areas(html)
        seats = [o for o in self.ed.offices_for("county")
                 if o["office_type"] in ("county_commissioner", "county_council_member")]
        self.assertEqual(sorted(u for _, u in areas), sorted(o["office_id"] for o in seats))
        data = _panel_data(html)
        for href, uid in areas:
            self.assertEqual(href, f"#office-{uid}")
            self.assertIn('class="gov-office', _tag_with_id(html, href[1:]))      # the seat's row on the Overview
            labels = [f[0] for f in data[uid]["f"]]
            self.assertEqual(labels[0], "Represented by")
            self.assertIn("Next election", labels)

    def test_county_every_office_is_one_row(self):
        html = self.html[GOV_COUNTY]
        offices = self.ed.offices_for("county") + self.ed.offices_for("sjc-courts")
        for o in offices:
            tag = _tag_with_id(html, f"office-{o['office_id']}")
            self.assertTrue(tag.startswith("<li"), o["office_id"])
            self.assertIn("gov-office", tag)
        self.assertNotIn("holder-card", html.split('id="officeholders"', 1)[1].split('id="row-officers"', 1)[0])

    # ------------------------------------------------------------ budgets
    def test_budget_map_clicks_open_the_government_money_tab(self):
        # phase 6 step 5 (2026-11-18): the budgets page no longer holds each unit's block; a map click opens the
        # government's Money tab (its money in and money out block, or its page)
        import posixpath
        html = self.html[BUDGETS]
        areas = _areas(html)
        self.assertGreater(len(areas), 20)
        for href, uid in areas:
            target = posixpath.normpath(posixpath.join("money/budgets", href.split("#")[0]))
            self.assertTrue(target.startswith("governments/"), (uid, href))
            self.assertIn(target, self.html, (uid, href))

    def test_budget_units_without_boundary_are_in_the_list(self):
        html = self.html[BUDGETS]
        lst = re.search(r'<section[^>]*id="over-time".*?</section>', html, re.S).group(0)
        for label in ("Library", "Airport"):
            self.assertIn(label, lst)

    def test_debt_rows_keyed_and_wrapped(self):
        html = self.html[BUDGETS]
        table = re.search(r'<table id="debt-classes".*?</table>', html, re.S).group(0)
        rows = re.findall(r"<tr\b[^>]*>", table.split("<tbody>", 1)[1])
        self.assertTrue(rows)
        # phase 6 step 5: one plain "Show the table" fold (no show-one keys: the page has no unit items)
        self.assertRegex(html, r'<details[^>]*id="debt-classes-all"[^>]*data-fold="see-all"')

    def test_all_unit_comparison_charts_kept(self):
        html = self.html[BUDGETS]
        for fid in ("perres-gf", "perres-af", "debt-2024"):
            self.assertIn(f'id="{fid}', html)
        per_res = html.split('id="per-resident"', 1)[1].split('id="rates"', 1)[0]
        self.assertNotIn("data-one=", per_res)

    # ------------------------------------------------------------ schools
    def test_schools_are_rows_and_the_hub_map_links_their_pages(self):
        html = self.html[HUB]
        corps = [u["unit_id"] for u in self.ed.units.values() if u["unit_type"] == "school_corporation"]
        areas = dict((uid, href) for href, uid in _areas(html))
        for uid in corps:
            self.assertIn("gov-hub-row", _tag_with_id(html, uid), uid)
            self.assertEqual(areas.get(uid), f"{uid}/index.html", uid)

    # ------------------------------------------------------------ neutrality
    def test_district_maps_not_shaded_by_party(self):
        for p in (LEG, GOV_COUNTY):
            svg = _svg(self.html[p])
            classes = set(re.findall(r'class="([^"]+)"', svg))
            self.assertFalse([c for c in classes if re.search(r"party|cmap-vb-|cmap-mm-\d", c)], p)
            fills = set(re.findall(r"dmap-f\d", svg))
            self.assertTrue(fills <= {"dmap-f0", "dmap-f1", "dmap-f2", "dmap-f3"}, fills)


class Units(unittest.TestCase):
    def test_neighbor_fills_differ_for_shared_edges(self):
        def sq(x, y):
            return f"M{x},{y}L{x + 10},{y}L{x + 10},{y + 10}L{x},{y + 10}Z"
        items = [{"district": "A", "d": sq(0, 0)}, {"district": "B", "d": sq(10, 0)}, {"district": "C", "d": sq(0, 10)},
                 {"district": "D", "d": sq(10, 10)}, {"district": "E", "d": sq(40, 40)}]
        f = neighbor_fills(items)
        for a, b in (("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")):
            self.assertNotEqual(f[a], f[b], (a, b))   # squares sharing an edge share two vertices
        # squares touching only at a corner share one vertex: not neighbors, so they may share a fill
        self.assertTrue(all(0 <= v < 4 for v in f.values()))

    def test_holder_state_vacant_incoming_reelected(self):
        o = {"office_id": "x", "title": "Seat", "next_election": "2028", "term_years": "4"}
        self.assertEqual(holder_state(None, o, [], [])["now"], NO_HOLDER)
        cur = [{"person": "Ann Lee", "party": "D", "start": "2023-01-01", "first_selected_by": "caucus",
                "confidence": "high"}]
        new = [{"person": "Bo Ray", "party": "R", "start": "2027-01-01", "status": "unofficial", "confidence": "high"}]
        st = holder_state(None, o, cur, new)
        self.assertEqual(st["now"], "Ann Lee (D)")
        self.assertEqual(st["how"], "party caucus")
        self.assertIn("Bo Ray (R)", st["incoming"])
        self.assertIn("unofficial", st["incoming"])
        same = [dict(cur[0], start="2027-01-01", status="unofficial")]
        self.assertTrue(holder_state(None, o, cur, same)["incoming"].startswith("Re-elected"))

    def test_same_person_matching(self):
        from pages.state import _same_person
        self.assertTrue(_same_person("Timothy Wesco", "Tim Wesco"))
        self.assertTrue(_same_person("B. Patrick Bauer", "B. Patrick Bauer"))
        self.assertFalse(_same_person("Maureen Bauer", "B. Patrick Bauer"))
        self.assertFalse(_same_person("", "Tim Wesco"))


class Scripts(unittest.TestCase):
    """Static checks of the browser scripts (behavior is checked in the browser; see the batch report)."""

    def test_copy_csv_copies_only_shown_rows_of_a_filtered_table(self):
        app = (ROOT / "tools" / "site" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn('table.hasAttribute("data-rows-filtered")', app)
        self.assertIn('"Copy " + shown + " shown row"', app)
        tf = (ROOT / "tools" / "site" / "static" / "js" / "tablefilter.js").read_text(encoding="utf-8")
        self.assertIn('new CustomEvent("rows-filtered"', tf)
        po = (ROOT / "tools" / "site" / "static" / "js" / "pick_one.js").read_text(encoding="utf-8")
        self.assertIn('new CustomEvent("rows-filtered"', po)

    def test_scripts_ascii_and_no_innerhtml(self):
        for name in ("pick_one.js", "map.js", "tablefilter.js"):
            src = (ROOT / "tools" / "site" / "static" / "js" / name).read_text(encoding="utf-8")
            self.assertTrue(src.isascii(), name)
            self.assertNotIn("innerHTML", src, name)

    def test_pick_one_runs_after_folds(self):
        """build.py concatenates static/js/*.js in name order; pick_one.js must come after folds.js, which closes the
        folds on load."""
        names = sorted(p.name for p in (ROOT / "tools" / "site" / "static" / "js").glob("*.js"))
        self.assertLess(names.index("folds.js"), names.index("pick_one.js"))


if __name__ == "__main__":
    unittest.main()
