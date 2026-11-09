"""Tests for tools/build_assessed_values.py (net assessed value by unit and year).

Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import csv
import sys
import unittest
from collections import Counter
from decimal import Decimal
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

import build_assessed_values as bav  # noqa: E402

# Certified AV of the unit's General (or Operations) fund in the DLGF 2026 budget order (MON-026), read off
# the PDF page by hand on 2026-11-08. These are independent of the builder's parser.
HAND_2026 = {
    "county-st-joseph": 14611493562,     # p.5
    "city-south-bend": 4396041441,       # p.21 (rendered page checked visually)
    "city-mishawaka": 2126759474,        # p.23
    "township-penn": 3316256356,         # p.16
    "township-portage": 3260758257,      # p.17
    "school-sbcsc": 7720180896,          # p.37, Operations
    "school-phm": 4328152992,            # p.35, Operations
    "library-sjcpl": 8499391190,         # p.42
}
# The research proposal's 37 values for 2026 (planning/qa/gapfill-2026-11-08-D-money-edits.csv); the builder
# must reproduce every one.
D_2026 = {
    "county-st-joseph": 14611493562, "township-centre": 911441999, "township-clay": 2274712395,
    "township-german": 747132678, "township-greene": 239544481, "township-harris": 1980639220,
    "township-liberty": 285580467, "township-lincoln": 168665223, "township-madison": 203358004,
    "township-olive": 443183569, "township-penn": 3316256356, "township-portage": 3260758257,
    "township-union": 254085346, "township-warren": 526135567, "city-south-bend": 4396041441,
    "city-mishawaka": 2126759474, "town-lakeville": 38303170, "town-new-carlisle": 183031503,
    "town-north-liberty": 85010552, "town-osceola": 152736751, "town-roseland": 79235294,
    "town-walkerton": 103219422, "town-indian-village": 10052186, "school-new-prairie": 443183569,
    "school-john-glenn": 693790171, "school-phm": 4328152992, "school-mishawaka": 1172100588,
    "school-sbcsc": 7720180896, "school-union-north": 254085346, "library-mishawaka": 5296895576,
    "library-new-carlisle": 443183569, "library-walkerton": 168665223, "library-sjcpl": 8499391190,
    "special-airport": 14611493562, "special-sb-transpo": 6522800915,
    "special-olive-new-carlisle-hudson-fpt": 443183569, "special-solid-waste": 14611493562,
}


class AssessedValueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.info = bav.build(verbose=False)
        cls.cert = cls.info["certified"]
        cls.gw = cls.info["gateway"]

    def test_dedupe_drops_exact_repeats(self):
        raw = bav.gateway_rows_raw()
        dd = bav.dedupe(raw)
        self.assertLess(len(dd), len(raw))
        # the download repeats every fund row exactly five times
        counts = Counter(tuple(r.items()) for r in raw)
        self.assertEqual(set(counts.values()), {5})
        self.assertEqual(len(dd), len(counts))
        keys = [(r["year"], r["unit_type"], r["unit_code"], r["fund_cd"]) for r in dd]
        self.assertEqual(len(keys), len(set(keys)), "one row per year, unit and fund after de-duplication")

    def test_dedupe_rejects_conflicting_values(self):
        a = {"year": "2026", "unit_type": "3", "unit_code": "0103", "fund_cd": "0101", "Net Assessed Valuation": "1"}
        b = dict(a, **{"Net Assessed Valuation": "2"})
        with self.assertRaises(SystemExit):
            bav.dedupe([a, b])

    def test_one_row_per_unit_year_basis(self):
        keys = Counter((r["unit_id"], r["year"], r["basis"]) for r in self.rows)
        self.assertEqual([k for k, n in keys.items() if n > 1], [])
        self.assertEqual({r["basis"] for r in self.rows}, {"dlgf_certified", "gateway_budget_estimate"})

    def test_2026_certified_matches_budget_order(self):
        got = {m: int(r["net_assessed_value"]) for (m, y), r in self.cert.items() if y == 2026}
        self.assertEqual(set(got), set(D_2026), "the 2026 order has 37 units")
        for mid, v in D_2026.items():
            self.assertLessEqual(abs(got[mid] - v), 1, mid)
        for mid, v in HAND_2026.items():
            self.assertLessEqual(abs(got[mid] - v), 1, mid)

    def test_gateway_2026_difference_documented(self):
        """2026 Gateway estimates differ from the certified values; each row must say by how much."""
        for (mid, y), g in self.gw.items():
            c = self.cert.get((mid, y))
            if not c:
                continue
            diff = abs(Decimal(g["net_assessed_value"]) - int(c["net_assessed_value"]))
            if diff <= 1:
                self.assertIn("Equals the certified value", g["notes"], (mid, y))
            else:
                self.assertIn("Differs from the certified", g["notes"], (mid, y))
                self.assertIn(f"${int(c['net_assessed_value']):,}", g["notes"], (mid, y))

    def test_gateway_rows_are_positive_and_marked_estimate(self):
        for r in self.gw.values():
            self.assertGreater(Decimal(r["net_assessed_value"]), 0)
            self.assertTrue(r["notes"].startswith("Estimate, not the certified value"))
            self.assertEqual(r["source_ids"], "MON-001")

    def test_general_fund_used(self):
        for (mid, y), r in self.cert.items():
            if mid.startswith("school-"):
                self.assertTrue(r["fund"].startswith("3300"), (mid, y, r["fund"]))
            elif not mid.startswith("special-"):
                self.assertTrue(r["fund"].startswith("0101"), (mid, y, r["fund"]))

    def test_written_file_matches_build(self):
        if not bav.OUT.exists():
            self.skipTest("assessed_values.csv not written yet")
        with open(bav.OUT, newline="", encoding="utf-8") as f:
            raw = f.read()
        self.assertTrue(raw.startswith(",".join(bav.HEADER) + "\n"))
        self.assertNotIn("\r", raw, "LF line endings, as .gitattributes asks for data CSVs")
        with open(bav.OUT, newline="", encoding="utf-8") as f:
            on_disk = list(csv.DictReader(f))
        self.assertEqual(on_disk, [{h: r[h] for h in bav.HEADER} for r in self.rows],
                         "assessed_values.csv is stale: re-run tools/build_assessed_values.py")


if __name__ == "__main__":
    unittest.main()
