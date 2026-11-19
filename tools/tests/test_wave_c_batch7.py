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

Since phase 6 step 3 (2026-11-16) county/ and schools/ forward to the government pages (governments/county/ and one
page per school corporation); the county and schools checks read those pages.

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
sys.path.insert(0, str(Path(__file__).resolve().parent))   # tests/gov_moved.py

import build  # noqa: E402
from civic.components import see_all_fold  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.html import h  # noqa: E402
from civic.pick_one import one_wrap_see_all  # noqa: E402
from civic.shell import Site  # noqa: E402
from gov_moved import lands  # noqa: E402

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
    """Phase 6 step 3 (2026-11-16): county/ and schools/ became forwarding pages; the county's content is on
    governments/county/ (Overview, Elections, Money, History, Sources) and each school corporation has its own
    governments/<id>/. The county and schools checks now read those tabs; an old id must land on an id that exists,
    through the #moved-anchors maps (tests/gov_moved.py)."""

    @classmethod
    def setUpClass(cls):
        from civic import governments as gm
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name)
        site = Site(cls.ed, out)
        build.discover_builders()
        for p in PAGES + ["about/sources/index.html"]:   # phase 6 step 5: the budgets page's old #src- ids land there
            build.BUILDERS[p](site)            # county/ and schools/ build the government pages they forward to
        # phase 6 step 5 (2026-11-18): money/budgets/ is Compare budgets; each unit's old block forwards to its
        # government's Money tab, so every government page is built for the old-anchor check
        for e in site.entries:
            if e.path.startswith("governments/") and e.path not in site.pages and e.path in build.BUILDERS:
                build.BUILDERS[e.path](site)
        site.write()
        cls.html = {p: (out / p).read_text(encoding="utf-8") for p in sorted(site.pages)}
        cls.ids = {p: ID_RE.findall(x) for p, x in cls.html.items()}
        cls.idset = {p: set(v) for p, v in cls.ids.items()}
        cls.county = {k: gm.path("county", k) for k in gm.gov_tabs(cls.ed, "county")}
        cls.schools = [g.gid for g in gm.governments(cls.ed) if g.kind == "school_corporation"]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def c(self, tab: str) -> str:
        return self.html[self.county[tab]]

    # ------------------------------------------------------------ anchors, progressive enhancement
    def test_every_old_anchor_lands(self):
        before = json.loads(FIXTURE.read_text(encoding="utf-8"))["ids"]
        lost = [(p, i) for p, ids in before.items() for i in ids if not lands(self.html, self.idset, p, i)]
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
        rail = re.search(r'<nav class="related" id="related".*?</nav>', self.c("overview"), re.S).group(0)
        keys = re.findall(r'data-related="([^"]+)"', rail)
        self.assertNotIn("map-votes", keys)          # the arbitrary "latest county race" link is gone
        for k in ("campaigns", "campaigns-courts", "legislators", "schools", "history", "run"):
            self.assertIn(k, keys)
        self.assertIn("history/index.html#control", rail)

    def test_county_results_one_item_per_district_seat(self):
        offices = self.ed.offices_for("county")
        seats = [o for o in offices if o["office_type"] in ("county_commissioner", "county_council_member")]
        sec = _section(self.c("elections"), "results")
        ov = self.c("overview")
        for o in seats:
            tag = _tag_with_id(sec, f"results-{o['office_id']}")
            self.assertIn(f'data-one="{o["office_id"]}"', tag, o["office_id"])
            self.assertTrue(_tag_with_id(ov, f"office-{o['office_id']}"), o["office_id"])   # its row on the Overview
        map_uids = set(re.findall(r'class="cmap-a" data-uid="([^"]+)"', ov))
        self.assertEqual(map_uids, {o["office_id"] for o in seats})

    def test_county_countywide_rows_match_charts(self):
        sec = _section(self.c("elections"), "results")
        table = re.search(r'<table id="results-countywide".*?</table>', sec, re.S).group(0)
        n_rows = len(re.findall(r"<tr\b", table.split("<tbody>", 1)[1]))
        fold = sec[sec.index('id="results-charts-county"'):]
        n_charts = len(re.findall(r'<figure[^>]*\sid="res-', fold))
        self.assertGreater(n_rows, 0)
        self.assertEqual(n_rows, n_charts)
        self.assertIn('data-fold="see-all"', _tag_with_id(sec, "results-charts-county"))

    def test_county_lawsuit_once_and_folded(self):
        html = self.c("overview")
        self.assertEqual(html.count('class="litigation"'), 1)
        self.assertIn('data-fold="see-all"', _tag_with_id(html, "litigation"))
        self.assertIn('href="#litigation"', html)

    def test_county_money_folded_and_control_on_history(self):
        money = self.c("money")
        self.assertTrue(any('id="money-in-out-all"' in t for t in _enclosing_details(money, "money-county")))
        hist = self.c("history")
        for fid in ("control-charts", "control-council", "control-commissioners"):
            self.assertIn(f'id="{fid}"', hist)

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
    def test_budget_units_without_a_boundary_are_listed(self):
        # phase 6 step 5 (2026-11-18): the chips that chose a unit's block are gone with the blocks; every unit the
        # map cannot draw (the county, libraries, special units) is in Compare budgets' list of every government,
        # linking to its government page's Money tab
        from civic import governments as gm
        from pages.money import money, no_boundary_units
        html = self.html[BUDGETS]
        units = no_boundary_units(money(self.ed))
        self.assertGreaterEqual(len(units), 10)
        lst = re.search(r'<section[^>]*id="over-time".*?</section>', html, re.S).group(0)
        for mid, _t in units:
            g = gm.gov_for_money_id(self.ed, mid)
            self.assertIn(f"governments/{g.gid}/", lst, mid)

    def test_debt_table_in_see_all_wrap(self):
        tags = _enclosing_details(self.html[BUDGETS], "debt-classes")
        self.assertTrue(any('id="debt-classes-all"' in t and 'data-fold="see-all"' in t for t in tags))

    def test_unit_flows_lines(self):
        # phase 6 step 3: each unit's money in and money out is on its government page's Money tab
        html = self.html[BUDGETS]
        self.assertIn("governments/county/money/index.html#money-county", html)
        self.assertIn("governments/south-bend/money/index.html#money-south-bend", html)
        self.assertIn("governments/sjcpl/money/index.html#money-sjcpl", html)

    # ------------------------------------------------------------ schools
    def _schools(self) -> str:
        from civic import governments as gm
        return "".join(self.html[gm.path(u)] for u in self.schools)

    def test_school_seat_wording(self):
        html = self._schools()
        self.assertNotRegex(html, r"Voters in [A-Z][a-z]+ Township")
        for town in ("Harris", "Madison", "Penn"):
            self.assertIn(f"All voters in the corporation; the member must live in {town} Township", html)
        for d in range(1, 6):
            self.assertIn(f"Voters in District {d}", html)
        self.assertIn("SB1 to SB5", html)

    def test_school_seat_rows(self):
        from civic import governments as gm
        for u in ("phm", "sbcsc"):
            html = self.html[gm.path(u)]
            for o in self.ed.offices_for(u):
                self.assertIn('class="gov-office', _tag_with_id(html, f"office-{o['office_id']}"), o["office_id"])
            self.assertRegex(html, rf'<nav class="related" id="related-{u}"[^>]*>\s*<h3')

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
