"""Tests for the tax base (civic/tax_base.py), school enrollment and spending per student (civic/school_stats.py),
the map population match (civic/map.py population) and the budgets-page helpers that use them (pages/money.py).

Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "site"))

from civic import school_stats as ss  # noqa: E402
from civic import tax_base as tb  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.map import _shape_names, population  # noqa: E402

ED = None


def ed():
    global ED
    if ED is None:
        ED = Edition.load(ROOT, "st-joseph")
    return ED


class FakePage:
    class Cites:
        def cite(self, ids):
            return f"[{ids}]"
    cites = Cites()

    def rel(self, path):
        return "../" + path


# ----------------------------------------------------------------------------- tax base: pure helpers

class TaxBaseHelpers(unittest.TestCase):
    def test_av_per_resident(self):
        self.assertAlmostEqual(tb.av_per_resident(1_000_000, 4), 250_000)
        for pop in (None, 0, -1, "", "x", float("nan")):
            self.assertIsNone(tb.av_per_resident(1000, pop), pop)
        self.assertIsNone(tb.av_per_resident(None, 10))

    def test_part_only(self):
        self.assertTrue(tb.part_only({"notes": "Fund 3300. St. Joseph County part only; the corporation also lies in another county."}))
        self.assertFalse(tb.part_only({"notes": "Fund 0101 General."}))
        self.assertFalse(tb.part_only(None))

    def test_usd_short(self):
        self.assertEqual(tb.usd_short(14_611_493_562), "$14.61 billion")
        self.assertEqual(tb.usd_short(22_500_000), "$22.5 million")
        self.assertEqual(tb.usd_short(950), "$950")


# ----------------------------------------------------------------------------- tax base: on the edition's data

class TaxBaseData(unittest.TestCase):
    def test_only_certified_rows(self):
        e = ed()
        for mid, years in tb._index(e).items():
            for y, r in years.items():
                self.assertEqual(r["basis"], tb.CERTIFIED, (mid, y))
        # the Gateway estimates go back to 2012; the certified values start in 2020
        self.assertEqual(min(tb.certified(e, "county-st-joseph")), "2020")

    def test_latest_and_line(self):
        e = ed()
        r = tb.latest_certified(e, "city-south-bend")
        self.assertEqual(r["year"], max(tb.certified(e, "city-south-bend")))
        line = str(tb.tax_base_line(e, FakePage(), "city-south-bend"))
        self.assertIn("Tax base: ", line)
        self.assertIn(tb.usd(tb.av_value(r)), line)
        self.assertNotIn("part only", line)
        # both the latest year's and the first year's sources are cited
        first = tb.certified(e, "city-south-bend")["2020"]
        self.assertIn(first["source_ids"], line)
        self.assertIn(r["source_ids"], line)
        self.assertIsNone(tb.tax_base_line(e, FakePage(), "no-such-unit"))
        self.assertIsNone(tb.tax_base_line(e, FakePage(), None))

    def test_cross_county_schools_say_part_only(self):
        e = ed()
        for mid in ("school-phm", "school-john-glenn", "school-union-north", "school-new-prairie"):
            self.assertTrue(tb.part_only(tb.latest_certified(e, mid)), mid)
            self.assertIn("part only", str(tb.tax_base_line(e, FakePage(), mid, county_label="St. Joseph County")), mid)
            facts = dict(tb.panel_facts(e, mid, 50_000))
            self.assertNotIn("Tax base per resident", facts, mid)   # no per-resident figure for a county part
        self.assertFalse(tb.part_only(tb.latest_certified(e, "school-sbcsc")))

    def test_panel_facts(self):
        e = ed()
        facts = dict(tb.panel_facts(e, "city-mishawaka", 51_063))
        self.assertIn("Tax base (certified net assessed value)", facts)
        self.assertIn("residents, 2020 Census count", facts["Tax base per resident"])
        self.assertEqual(len(tb.panel_facts(e, "city-mishawaka", None)), 1)
        self.assertEqual(tb.panel_facts(e, "no-such-unit", 10), [])

    def test_money_id(self):
        e = ed()
        self.assertEqual(tb.money_id(e, "south-bend"), "city-south-bend")
        self.assertEqual(tb.money_id(e, "new-prairie"), "school-new-prairie")   # alias row added 2026-11-09 (Wave C batch 7)
        self.assertIsNone(tb.money_id(e, "no-such-unit"))


# ----------------------------------------------------------------------------- school stats

class SchoolStats(unittest.TestCase):
    def test_text_helpers(self):
        down = [("2011-12", 20156, {}), ("2025-26", 12851, {})]
        self.assertEqual(ss.enrollment_text(down), "12,851 in school year 2025-26, down 36% from 20,156 in 2011-12")
        up = [("2011-12", 100, {}), ("2025-26", 150, {})]
        self.assertIn("up 50% from 100", ss.enrollment_text(up))
        same = [("2011-12", 2822, {}), ("2025-26", 2819, {})]
        self.assertIn("about the same as in 2011-12 (2,822)", ss.enrollment_text(same))
        self.assertEqual(ss.enrollment_text([]), "")
        self.assertEqual(ss.per_student_text(None, None), "")
        row = {"value": "24600.56", "vintage": "DLGF per-student expenditure, calendar year 2025"}
        med = {"value": "17286.94", "vintage": row["vintage"]}
        self.assertEqual(ss.per_student_text(row, med), "$24,601 in calendar year 2025 (state median $17,287)")
        self.assertEqual(ss.per_student_text(row, None), "$24,601 in calendar year 2025")

    def test_every_corporation(self):
        e = ed()
        corps = [u["unit_id"] for u in e.units.values() if u["unit_type"] == "school_corporation"]
        self.assertTrue(corps)
        for uid in corps:
            series = ss.enrollment(e, uid)
            self.assertTrue(series, uid)
            labels = [y for y, _, _ in series]
            self.assertEqual(labels, sorted(labels), uid)
            self.assertRegex(labels[-1], r"^\d{4}-\d{2}$")
            row, med = ss.per_student(e, uid)
            self.assertIsNotNone(row, uid)
            self.assertIsNotNone(med, uid)
            self.assertEqual(row["vintage"], med["vintage"], uid)       # median from the same calendar year
            facts = dict(ss.panel_facts(e, uid))
            label = next(k for k in facts if k.startswith("Spending per student"))
            self.assertIn(ss.PER_STUDENT_CAPTION, facts[label])
            self.assertIn("calendar year", label)

    def test_no_geo(self):
        self.assertEqual(ss.enrollment(ed(), "no-such-unit"), [])
        self.assertEqual(ss.per_student(ed(), "no-such-unit"), (None, None))


# ----------------------------------------------------------------------------- map population (shape Census names)

class MapPopulation(unittest.TestCase):
    def test_every_mapped_area_has_population(self):
        e = ed()
        names = _shape_names(e)
        self.assertTrue(names)
        for uid, (layer, cname) in names.items():
            unit = e.units.get(uid)
            if not unit:
                continue
            pop = population(e, unit)
            self.assertIsNotNone(pop, uid)
            self.assertIsNotNone(pop["census"], f"{uid}: no 2020 Census count")
            self.assertTrue(pop["acs"], f"{uid}: no ACS estimate")

    def test_names_that_differ_from_census(self):
        # School City of Mishawaka and LaVille have unit names that differ from their Census names
        e = ed()
        for uid in ("school-city-mishawaka", "union-north"):
            if uid in e.units and uid in _shape_names(e):
                pop = population(e, e.units[uid])
                self.assertIsNotNone(pop and pop["census"], uid)


# ----------------------------------------------------------------------------- budgets page helpers

class BudgetsPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from pages import money as m
        cls.m = m
        cls.mo = m.money(ed())

    def test_amended_basis_label(self):
        self.assertIn("amended_all_funds", self.m.BASIS)
        self.assertNotIn("amended_all_funds", self.m.BASIS_ORDER)   # table only, never charted

    def test_source_labels(self):
        s = self.mo.series
        self.assertEqual(self.m._source_label(s["sb-gateway-allfunds-2012-2023"]), "Gateway state budget file")
        self.assertEqual(self.m._source_label(s["sb-ordinance-adopted-appropriations"]), "council budget ordinance")
        self.assertEqual(self.m._year_span(s["sb-gateway-allfunds-2012-2023"]), "2012-2023")

    def test_comparison_year_ignores_one_early_unit(self):
        # South Bend's 2027 ordinance is the only 2027 figure: the per-resident comparison must not use 2027
        ids = ["county-st-joseph", "city-south-bend", "city-mishawaka"]
        y = self.m.comparison_year(self.mo, ids, ("general_fund", "advertised_all_funds"))
        have = [mid for mid in ids if any(s["unit"] == mid and any(int(r["year"]) == y for r in s["rows"])
                                          for s in self.mo.series.values() if s["basis"] == "general_fund")]
        self.assertEqual(sorted(have), sorted(ids))

    def test_av_per_resident_rows(self):
        ids = ["county-st-joseph", "city-south-bend", "school-phm"]
        rows, src, year = self.m.av_per_resident_rows(self.mo, ids)
        labels = [r["label"] for r in rows]
        self.assertEqual(len(rows), 2)                                 # the county part of PHM is left out
        self.assertFalse(any("Penn-Harris" in x for x in labels))
        self.assertEqual(year, tb.latest_certified(ed(), "county-st-joseph")["year"])
        self.assertTrue(src)

    def test_later_debt_rows_by_type_and_date(self):
        rows = self.m.later_debt_rows(self.mo, "city-south-bend")
        dates = [d for d, _, _ in rows]
        self.assertEqual(dates, sorted(dates))
        self.assertGreaterEqual(len(rows), 2)
        for _, _, r in rows:
            self.assertTrue(r["debt_type"].startswith("Total debt outstanding as of"))
        self.assertEqual(self.m.later_debt_rows(self.mo, "county-st-joseph"), [])


if __name__ == "__main__":
    unittest.main()
