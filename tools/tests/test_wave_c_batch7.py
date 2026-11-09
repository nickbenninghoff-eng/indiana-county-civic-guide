"""Tests for Wave C batch 7 (2026-11-09), "After the map work": county/, schools/, state/your-legislators/ and
money/budgets/ (planning/qa/wave-c-batch7-2026-11-09.md).

  - every id the four pages had before the batch is still on its page (fixtures/anchors_before_batch7.json), no
    duplicate ids, and every fold and show-one item ships open (JavaScript off: everything visible);
  - county: the rail drops the arbitrary map race and adds the county-wide links; recent results are one show-one
    item per district seat with the same key as its officeholder line and map district; the lawsuit is printed once;
  - legislators: one results row per election and every old table inside a See-all fold; the all-district matrix is
    kept, in a fold; a rail per district;
  - budgets: chips for every unit with no boundary, each landing on that unit's item; the debt table is a See-all
    fold that still opens for the chosen unit;
  - schools: the seat list says who votes, from the guide's own results (no "Voters in <X> Township"); SBCSC's
    districts are listed as voting districts with no boundary file; a rail per corporation;
  - data: school-new-prairie is in derived/unit_id_aliases.csv and the code workaround is gone.

Builds the four pages into a temporary folder.
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

import build  # noqa: E402
from civic.components import see_all_fold  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.html import h  # noqa: E402
from civic.pick_one import one_wrap_see_all  # noqa: E402
from civic.shell import Site  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "anchors_before_batch7.json"
ID_RE = re.compile(r'\sid="([^"]+)"')
LEG, COUNTY, BUDGETS, SCHOOLS = ("state/your-legislators/index.html", "county/index.html",
                                 "money/budgets/index.html", "schools/index.html")
PAGES = [COUNTY, SCHOOLS, LEG, BUDGETS]


def _tag_with_id(html: str, i: str) -> str:
    m = re.search(r'<[a-z0-9]+\b[^>]*\sid="' + re.escape(i) + r'"[^>]*>', html)
    return m.group(0) if m else ""


def _section(html: str, sid: str) -> str:
    m = re.search(r'<section[^>]*\sid="' + re.escape(sid) + r'".*?</section>', html, re.S)
    return m.group(0) if m else ""


def _enclosing_details(html: str, i: str) -> list[str]:
    """Opening tags of the <details> elements that contain the element with id ``i`` (innermost last)."""
    pos = html.index(f' id="{i}"')
    stack = []
    for m in re.finditer(r"<details\b[^>]*>|</details>", html[:pos]):
        if m.group(0).startswith("</"):
            stack.pop()
        else:
            stack.append(m.group(0))
    return stack


class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name)
        site = Site(cls.ed, out)
        build.discover_builders()
        for p in PAGES:
            build.BUILDERS[p](site)
        site.write()
        cls.html = {p: (out / p).read_text(encoding="utf-8") for p in PAGES}
        cls.ids = {p: ID_RE.findall(x) for p, x in cls.html.items()}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # ------------------------------------------------------------ anchors, progressive enhancement
    def test_every_old_anchor_still_on_its_page(self):
        before = json.loads(FIXTURE.read_text(encoding="utf-8"))["ids"]
        lost = [(p, i) for p, ids in before.items() for i in ids if i not in set(self.ids[p])]
        self.assertEqual(lost, [])

    def test_no_duplicate_ids(self):
        for p, ids in self.ids.items():
            self.assertEqual(sorted({i for i in ids if ids.count(i) > 1}), [], p)

    def test_every_fold_ships_open(self):
        for p, html in self.html.items():
            for tag in re.findall(r"<details\b[^>]*>", html):
                if "data-fold" in tag or "data-one=" in tag:
                    self.assertIn(" open", tag, (p, tag[:120]))

    # ------------------------------------------------------------ county
    def test_county_rail(self):
        rail = re.search(r'<nav class="related" id="related".*?</nav>', self.html[COUNTY], re.S).group(0)
        keys = re.findall(r'data-related="([^"]+)"', rail)
        self.assertNotIn("map-votes", keys)          # the arbitrary "latest county race" link is gone
        for k in ("campaigns", "campaigns-courts", "legislators", "schools", "history", "run"):
            self.assertIn(k, keys)
        self.assertIn("history/index.html#control", rail)

    def test_county_results_one_item_per_district_seat(self):
        html = self.html[COUNTY]
        offices = self.ed.offices_for("county")
        seats = [o for o in offices if o["office_type"] in ("county_commissioner", "county_council_member")]
        sec = _section(html, "results")
        for o in seats:
            tag = _tag_with_id(sec, f"results-{o['office_id']}")
            self.assertIn(f'data-one="{o["office_id"]}"', tag, o["office_id"])
            # the same key as its officeholder line, so a map click opens both
            self.assertIn(f'data-one="{o["office_id"]}"', _tag_with_id(html, f"office-{o['office_id']}"))
        map_uids = set(re.findall(r'class="cmap-a" data-uid="([^"]+)"', html))
        self.assertEqual(map_uids, {o["office_id"] for o in seats})

    def test_county_countywide_rows_match_charts(self):
        sec = _section(self.html[COUNTY], "results")
        table = re.search(r'<table id="results-countywide".*?</table>', sec, re.S).group(0)
        n_rows = len(re.findall(r"<tr\b", table.split("<tbody>", 1)[1]))
        fold = sec[sec.index('id="results-charts-county"'):]
        n_charts = len(re.findall(r'<figure[^>]*\sid="res-', fold))
        self.assertGreater(n_rows, 0)
        self.assertEqual(n_rows, n_charts)
        self.assertIn('data-fold="see-all"', _tag_with_id(sec, "results-charts-county"))

    def test_county_lawsuit_once_and_folded(self):
        html = self.html[COUNTY]
        self.assertEqual(html.count('class="litigation"'), 1)
        self.assertIn('data-fold="see-all"', _tag_with_id(html, "litigation"))
        self.assertIn('href="#litigation"', html)

    def test_county_money_and_control_folded(self):
        html = self.html[COUNTY]
        self.assertIn('data-fold="see-all"', _tag_with_id(html, "money-flows-county"))
        self.assertIn('data-fold="see-all"', _tag_with_id(html, "control-charts"))
        for fid in ("control-council", "control-commissioners"):
            self.assertTrue(any("control-charts" in t for t in _enclosing_details(html, fid)))

    # ------------------------------------------------------------ legislators
    def test_legislators_results_summary_and_folds(self):
        html = self.html[LEG]
        for o in self.ed.offices_for("in-house") + self.ed.offices_for("in-senate"):
            ch = "house" if o["office_type"] == "state_house" else "senate"
            k = f"{ch}-{o['district']}"
            if f'id="results-{k}-table"' not in html:
                continue
            self.assertTrue(any(f'id="results-{k}-all"' in t for t in _enclosing_details(html, f"results-{k}-table")))
            summary = re.search(rf'<table id="results-{k}-summary".*?</table>', html, re.S).group(0)
            years = {int(m.group(1)) for c in self.ed.contests.values()
                     if (m := re.match(rf"^(\d{{4}})g-state-{ch}-{o['district']}$", c["contest_id"]))
                     and 2012 <= int(m.group(1)) <= 2026}
            self.assertEqual(len(re.findall(r"<tr\b", summary.split("<tbody>", 1)[1])), len(years), k)
            rail = re.search(rf'<nav class="related" id="related-{k}".*?</nav>', html, re.S)
            self.assertIsNotNone(rail, k)
            self.assertNotIn('data-related="campaigns"', rail.group(0))

    def test_legislators_matrix_kept_in_fold(self):
        html = self.html[LEG]
        for tid, fold in (("cf-matrix", "cf-matrix-all"), ("cf-long", "cf-long-all")):
            self.assertTrue(any(f'id="{fold}"' in t and "data-fold" in t for t in _enclosing_details(html, tid)), tid)
        n = len({(r["committee"], r["candidate"], r["district"]) for r in self.ed.table("cf_state")})
        self.assertIn(f"See all {n} committees", html)

    # ------------------------------------------------------------ budgets
    def test_budget_chips_choose_their_unit(self):
        from pages.money import money, no_boundary_units
        html = self.html[BUDGETS]
        chips = re.findall(r'<a class="one-chip" href="#([^"]+)"', html)
        self.assertEqual(len(chips), len(no_boundary_units(money(self.ed))))
        self.assertGreaterEqual(len(chips), 10)
        keys = set(re.findall(r'data-one="([^"]+)"', html))
        for t in chips:
            tag = _tag_with_id(html, t)
            self.assertTrue(tag, t)
            m = re.search(r'data-one(?:-for)?="([^"]+)"', tag)
            self.assertTrue(m and m.group(1) in keys, t)

    def test_debt_table_in_see_all_wrap(self):
        tags = _enclosing_details(self.html[BUDGETS], "debt-classes")
        self.assertTrue(any('id="debt-classes-all"' in t and "data-one-wrap" in t and 'data-fold="see-all"' in t
                            for t in tags))
        self.assertIn("data-one-all", self.html[BUDGETS])   # "Show all units" kept

    def test_unit_flows_lines(self):
        html = self.html[BUDGETS]
        self.assertIn("county/index.html#money", html)
        self.assertIn("places/south-bend/index.html#money-south-bend", html)
        self.assertIn('href="#flows-sjcpl"', html)

    # ------------------------------------------------------------ schools
    def test_school_seat_wording(self):
        html = self.html[SCHOOLS]
        self.assertNotRegex(html, r"Voters in [A-Z][a-z]+ Township")
        for town in ("Harris", "Madison", "Penn"):
            self.assertIn(f"All voters in the corporation; the member must live in {town} Township", html)
        for d in range(1, 6):
            self.assertIn(f"Voters in District {d}", html)
        self.assertIn("SB1 to SB5", html)

    def test_school_seat_rows(self):
        html = self.html[SCHOOLS]
        for o in self.ed.offices_for("phm"):
            tag = _tag_with_id(html, f"office-{o['office_id']}")
            self.assertIn("seat-row", tag)
            self.assertNotIn("data-one=", tag)      # nested in the corporation's item, not a second key
            self.assertTrue(any('data-one="phm"' in t for t in _enclosing_details(html, f"office-{o['office_id']}")))
        for uid in ("sbcsc", "phm"):
            self.assertTrue(any(f'id="seats-{uid}-all"' in t for t in _enclosing_details(html, f"seats-{uid}")))
            self.assertRegex(html, rf'<nav class="related" id="related-{uid}"[^>]*>\s*<h3')

    def test_residency_evidence(self):
        from pages.places import _residency_evidence
        ev = _residency_evidence(self.ed, "phm")
        self.assertTrue(any("Madison Township" in e["text"] for e in ev))
        self.assertEqual(_residency_evidence(self.ed, "sbcsc"), [])
        jg = " ".join(e["text"] for e in _residency_evidence(self.ed, "john-glenn"))
        self.assertIn("outside", jg)


class Units(unittest.TestCase):
    def test_new_prairie_alias(self):
        ed = Edition.load(ROOT, "st-joseph")
        self.assertEqual(ed.unit_alias("school-new-prairie"), "new-prairie")
        for f in list((ROOT / "tools" / "site" / "civic").glob("*.py")) + list((ROOT / "tools" / "site" / "pages").glob("*.py")):
            self.assertNotIn("EXTRA_UNIT_IDS", f.read_text(encoding="utf-8"), f.name)

    def test_one_wrap_see_all_matches_see_all_fold(self):
        body = h("p", None, "x")
        a = str(one_wrap_see_all("f", "See all 3 rows", body))
        b = str(see_all_fold("f", 3, body))
        self.assertEqual(a.replace(" data-one-wrap", ""), b)
