"""Tests for the budgets page's money map (tools/site/civic/money_map.py).

Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "site"))

from civic import money_map as mmod  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.map import load_shapes  # noqa: E402


def row(view, year, category, amount, basis="afr_{y}_actual_all_funds_sboa_chart", src="MON-060", notes=""):
    return {"unit_id": "x", "year": year, "view": view, "category": category, "amount": str(amount), "share": "",
            "basis": basis.format(y=year), "status": "computed", "source_ids": src, "notes": notes}


class PerResident(unittest.TestCase):
    def test_divides(self):
        self.assertAlmostEqual(mmod.per_resident(1_000_000, 4_000), 250.0)

    def test_missing_or_bad_population(self):
        for pop in (None, 0, -5, "", "n/a", float("nan")):
            self.assertIsNone(mmod.per_resident(1000, pop), pop)
        self.assertIsNone(mmod.per_resident(None, 100))


class Breaks(unittest.TestCase):
    def check_valid(self, vals, breaks):
        self.assertEqual(breaks, sorted(breaks))
        self.assertEqual(len(set(breaks)), len(breaks))
        lo, hi = min(vals), max(vals)
        for b in breaks:
            self.assertGreater(b, lo)
            self.assertLessEqual(b, hi)
            self.assertTrue(float(b).is_integer(), b)
        steps = [mmod.step_of(v, breaks) for v in vals]
        # every class has at least one value
        self.assertEqual(sorted(set(steps)), list(range(len(breaks) + 1)))

    def test_layer_sized_inputs(self):
        cases = {
            "towns": [459, 820, 1299, 1644, 4035, 4216, 5330, 5950, 7877],
            "townships": [24, 46.6, 46.8, 64, 87, 112, 217, 265, 310, 372, 388, 447, 905],
            "schools": [1741, 2263, 2627, 2836, 2885],
        }
        for name, vals in cases.items():
            b = mmod.class_breaks(vals)
            self.check_valid(vals, b)
            self.assertLessEqual(len(b) + 1, 5, name)
            self.assertGreaterEqual(len(b) + 1, 4, name)

    def test_known_breaks_are_round(self):
        self.assertEqual(mmod.class_breaks([459, 820, 1299, 1644, 4035, 4216, 5330, 5950, 7877]),
                         [1000, 3000, 5000, 7000])

    def test_round_between(self):
        self.assertEqual(mmod.round_between(820, 1299), 1000)
        self.assertEqual(mmod.round_between(2627, 2836), 2750)
        self.assertIsNone(mmod.round_between(46.6, 46.8))   # no whole dollar in the gap
        self.assertIsNone(mmod.round_between(10, 10))
        self.assertEqual(mmod.round_between(0.2, 3), 2)

    def test_small_and_empty(self):
        self.assertEqual(mmod.class_breaks([]), [])
        self.assertEqual(mmod.class_breaks([None, None]), [])
        self.assertEqual(mmod.class_breaks([500]), [])
        self.assertEqual(mmod.class_breaks([500, 500, 500]), [])
        b = mmod.class_breaks([100, 900])
        self.check_valid([100, 900], b)
        self.assertEqual(len(b), 1)

    def test_none_values_ignored(self):
        vals = [None, 459, 820, None, 1299, 1644, 4035, 4216, 5330, 5950, 7877]
        self.assertEqual(mmod.class_breaks(vals), mmod.class_breaks([v for v in vals if v is not None]))
        self.assertIsNone(mmod.step_of(None, [1, 2]))

    def test_value_on_break_goes_up(self):
        self.assertEqual(mmod.step_of(1000, [1000, 3000]), 1)
        self.assertEqual(mmod.step_of(999.99, [1000, 3000]), 0)

    def test_ramp_positions_spread(self):
        self.assertEqual(mmod.ramp_positions(5), [1, 2, 3, 4, 5])
        self.assertEqual(mmod.ramp_positions(4), [1, 2, 4, 5])
        self.assertEqual(mmod.ramp_positions(3), [1, 3, 5])
        self.assertEqual(mmod.ramp_positions(2), [1, 5])
        self.assertEqual(mmod.ramp_positions(1), [3])

    def test_legend_labels(self):
        self.assertEqual(mmod.legend_labels([80, 200]), ["Under $80", "$80 to $200", "$200 or more"])
        self.assertEqual(len(mmod.legend_labels([])), 1)


class Summary(unittest.TestCase):
    def test_years_and_totals(self):
        rows = [row("by_purpose", "2024", "A", 50), row("by_purpose", "2025", "A", 70), row("by_purpose", "2025", "Other", 30),
                row("income", "2025", "Taxes", 80, basis="afr_{y}_receipts_all_funds_sboa_chart"),
                row("income", "2025", "Other", 20, basis="afr_{y}_receipts_all_funds_sboa_chart"),
                row("income_excluded", "2025", "Borrowed (bond and loan proceeds)", 9),
                row("spending_excluded", "2025", "Moved between the unit's own funds (transfers, loans, investments)", 4)]
        s = mmod.summarize_rows(rows, "city")
        self.assertEqual((s["spending_year"], s["income_year"]), ("2025", "2025"))
        self.assertEqual(s["spending"], 100)
        self.assertEqual(s["income"], 100)
        self.assertEqual([b["category"] for b in s["top_spending"]], ["A"])   # Other never ranks
        self.assertAlmostEqual(s["top_spending"][0]["share"], 70)
        self.assertEqual((s["passed_in"], s["passed_out"], s["borrowed"]), (9, 4, 9))

    def test_held_income_year_falls_back(self):
        rows = [row("by_purpose", "2025", "A", 10),
                row("income", "2024", "Taxes", 5, basis="afr_{y}_receipts_all_funds_sboa_chart"),
                row("income", "2025", "Taxes", 99, basis="afr_{y}_receipts_all_funds_sboa_chart_held",
                    notes="HELD (not charted): The 2025 line is being checked. Receipt lines: x")]
        s = mmod.summarize_rows(rows, "school")
        self.assertEqual(s["income_year"], "2024")
        self.assertEqual(s["income"], 5)
        self.assertEqual(s["held_note"], "The 2025 line is being checked.")
        self.assertEqual(s["income_year_label"], "2024-25 school year")
        cav = mmod.caveats(s)
        self.assertTrue(any("Income shown: 2024-25 school year" in c for c in cav))

    def test_no_spending_rows(self):
        self.assertIsNone(mmod.summarize_rows([], "city"))
        self.assertIsNone(mmod.summarize_rows([row("income", "2025", "Taxes", 5)], "city"))


class EditionMap(unittest.TestCase):
    """Against the real St. Joseph data."""

    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.shapes = load_shapes(cls.ed)
        if cls.shapes is None:
            raise unittest.SkipTest("no map shapes")
        cls.mm = mmod.money_map_data(cls.ed, cls.shapes)

    def test_every_area_resolves(self):
        for tab, L in self.mm["layers"].items():
            self.assertEqual(len(L["areas"]), len(self.shapes["layers"][L["key"]]))
            for a in L["areas"]:
                self.assertIn(a["uid"], self.ed.units, a)
                if a["mid"]:
                    self.assertIsNotNone(a["summary"])
                    self.assertEqual(self.ed.unit_alias(a["mid"]), a["uid"])
                    self.assertIn(f"#money-{a['uid']}", a["target"])
                else:
                    self.assertIsNone(a["summary"])
                    self.assertIsNone(a["step"])          # drawn as "no data"
                if a["per_resident"] is None:
                    self.assertIsNone(a["shade"])
                else:
                    self.assertIn(a["shade"], range(1, mmod.RAMP + 1))

    def test_population_is_census_2020_for_every_mapped_area(self):
        for tab, L in self.mm["layers"].items():
            for a in L["areas"]:
                self.assertIsNotNone(a["residents"], a["uid"])
                self.assertGreater(a["residents"], 0)

    def test_per_resident_math_on_real_rows(self):
        a = next(a for a in self.mm["layers"]["cities"]["areas"] if a["uid"] == "south-bend")
        self.assertAlmostEqual(a["per_resident"], a["summary"]["spending"] / a["residents"])

    def test_breaks_per_layer(self):
        for tab, L in self.mm["layers"].items():
            vals = [a["per_resident"] for a in L["areas"] if a["per_resident"] is not None]
            self.assertEqual(L["breaks"], mmod.class_breaks(vals))
            self.assertIn(L["classes"], (4, 5), tab)
            self.assertEqual(sum(L["counts"]), len(vals))
            self.assertTrue(all(c > 0 for c in L["counts"]), tab)

    def test_others_cover_every_unmapped_money_unit(self):
        mapped = {a["mid"] for L in self.mm["layers"].values() for a in L["areas"] if a["mid"]}
        others = {o["mid"] for o in self.mm["others"]}
        every = {r["unit_id"] for r in self.ed.table("spending_breakdowns")}
        self.assertEqual(mapped | others, every)
        self.assertFalse(mapped & others)
        self.assertIsNotNone(self.mm["county"])
        self.assertIsNotNone(self.mm["county"]["per_resident"])


if __name__ == "__main__":
    unittest.main()
