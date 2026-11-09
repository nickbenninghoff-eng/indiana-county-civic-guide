"""Tests for tools/build_spending.py (money in and money out by unit).

Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import csv
import sys
import unittest
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

import build_spending as bs  # noqa: E402

ZERO = Decimal("0.00")


def D(s) -> Decimal:
    return Decimal(s).quantize(bs.CENT)


class SpendingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.info = bs.build(verbose=False)
        cls.res = cls.info["results"]
        cls.rec = cls.info["receipts"]
        cls.by = defaultdict(list)
        for r in cls.rows:
            cls.by[(r[0], r[1], r[2])].append(r)
        cls.unit_map = bs.load_unit_map()
        cls.raw = {}
        for y in bs.YEARS:
            for receipts in (False, True):
                totals = defaultdict(Decimal)
                for line in bs.read_lines(y, receipts=receipts):
                    mid = cls.unit_map.get(line["unit_name"].strip().upper())
                    if mid:
                        totals[mid] += bs.money(line["amount"])
                cls.raw[(y, receipts)] = totals

    def view_sum(self, mid, year, view):
        return sum((D(r[4]) for r in self.by[(mid, str(year), view)]), ZERO)

    def fund(self, mid, kind, number, name="x", ent="Governmental Activities"):
        line = {"unit_fund_number": str(number), "Fund_code": str(number), "fund_name": name, "ent_name": ent}
        return bs.fund_decision(mid, kind, bs.fund_info(mid, kind, line))[0]

    # ---------------------------------------------------------------- exclusion rule
    def test_known_county_funds(self):
        c = "county-st-joseph"
        self.assertEqual(self.fund(c, "county", 6000, "Settlement Fund"), bs.G_SETTLE)
        self.assertEqual(self.fund(c, "county", 7330, "LIT Certified Shares"), bs.G_SETTLE)
        self.assertEqual(self.fund(c, "county", 6203, "LIT - Property Tax Replacement"), bs.G_SETTLE)
        self.assertEqual(self.fund(c, "county", 5353, "Federal Tax Withholding"), bs.G_PAYROLL)
        self.assertEqual(self.fund(c, "county", 5354, "FICA Tax Withholding"), bs.G_PAYROLL)
        self.assertEqual(self.fund(c, "county", 4700, "County Health Insurance"), bs.G_INTERNAL)
        self.assertEqual(self.fund(c, "county", 1205, "Tax Sale Surplus"), bs.G_TRUST)
        self.assertEqual(self.fund(c, "county", 11, "Clerk Odyssey Fund"), bs.G_TRUST)
        self.assertIsNone(self.fund(c, "county", 1000, "General Fund"))
        self.assertIsNone(self.fund(c, "county", 1176, "County Highway (MVH)"))
        self.assertIsNone(self.fund(c, "county", 8950, "American Rescue Plan"))

    def test_known_other_unit_funds(self):
        self.assertEqual(self.fund("city-mishawaka", "city", 7704, "Self-Insurance"), bs.G_INTERNAL)
        self.assertEqual(self.fund("city-mishawaka", "city", 8801, "Fire Pension"), bs.G_TRUST)
        self.assertEqual(self.fund("town-roseland", "town", 8901, "PAYROLL"), bs.G_PAYROLL)
        self.assertIsNone(self.fund("city-mishawaka", "city", 6301, "Electric Utility Operating", "ELECTRIC"))
        self.assertEqual(self.fund("city-south-bend", "city", 711, "Self-Funded Employee Benefits"), bs.G_INTERNAL)
        self.assertEqual(self.fund("school-sbcsc", "school", 9100, "PAYROLL"), bs.G_PAYROLL)
        self.assertEqual(self.fund("school-sbcsc", "school", 1100, "INSURANCE"), bs.G_INTERNAL)
        self.assertIsNone(self.fund("school-sbcsc", "school", 101, "EDUCATION"))
        self.assertEqual(self.fund("library-sjcpl", "library", 802, "PAYROLL"), bs.G_PAYROLL)
        self.assertEqual(self.fund("library-sjcpl", "library", 700, "SELF INSURANCE RESERVE FUND"), bs.G_INTERNAL)
        self.assertEqual(self.fund("township-clay", "township", 9999, "PAYROLL DEDUCTIONS"), bs.G_PAYROLL)

    def test_transfer_lines_excluded(self):
        base = {"section": "0", "disburse_code": "D312"}
        self.assertIsNone(bs.line_excluded(base))
        for code in ("D704", "D705", "D706", "D900"):
            self.assertIsNotNone(bs.line_excluded(dict(base, disburse_code=code)), code)
        self.assertIsNotNone(bs.line_excluded({"section": "4", "disburse_code": "60100"}))  # Transfers Out

    def test_settlement_fund_amount(self):
        rows = self.by[("county-st-joseph", "2025", "passthrough_detail")]
        settle = next(r for r in rows if r[3].startswith("Settlement Fund"))
        self.assertEqual(D(settle[4]), D("391747406.11"))

    # ---------------------------------------------------------------- reconciliation
    def test_spending_reconciles_to_the_cent(self):
        for (mid, y), a in self.res.items():
            file_total = self.raw[(y, False)][mid]
            self.assertEqual(a["included"] + a["excluded_total"], file_total, (mid, y))
            self.assertEqual(self.view_sum(mid, y, "by_purpose") + self.view_sum(mid, y, "spending_excluded"), file_total,
                             (mid, y))
            if a["kind"] != "school":
                self.assertEqual(self.view_sum(mid, y, "by_type"), self.view_sum(mid, y, "by_purpose"), (mid, y))

    def test_income_reconciles_to_the_cent(self):
        for (mid, y), a in self.rec.items():
            file_total = self.raw[(y, True)][mid]
            self.assertEqual(a["included"] + a["excluded_total"], file_total, (mid, y))
            self.assertEqual(self.view_sum(mid, y, "income") + self.view_sum(mid, y, "income_excluded"), file_total,
                             (mid, y))

    def test_detail_rows_sum_to_their_group(self):
        for (mid, y, view), rows in list(self.by.items()):
            if view not in ("passthrough_detail", "passthrough_in_detail"):
                continue
            parent = "spending_excluded" if view == "passthrough_detail" else "income_excluded"
            group = [r for r in self.by[(mid, y, parent)] if r[3] == bs.G_SETTLE]
            self.assertEqual(len(group), 1, (mid, y, view))
            self.assertEqual(sum((D(r[4]) for r in rows), ZERO), D(group[0][4]), (mid, y, view))
            self.assertLessEqual(len([r for r in rows if r[3] != bs.OTHER]), bs.TOP_N + 1)

    def test_excluded_block_categories_sum(self):
        for (mid, y), a in self.res.items():
            self.assertEqual(self.view_sum(mid, y, "spending_excluded"), a["excluded_total"], (mid, y))
            for r in self.by[(mid, str(y), "spending_excluded")]:
                self.assertIn(r[3], bs.EXCLUDED_ORDER)
                self.assertNotEqual(D(r[4]), ZERO)
        for (mid, y), a in self.rec.items():
            self.assertEqual(self.view_sum(mid, y, "income_excluded"), a["excluded_total"], (mid, y))
            for r in self.by[(mid, str(y), "income_excluded")]:
                self.assertIn(r[3], bs.INCOME_EXCLUDED_ORDER)

    def test_written_file_is_current(self):
        with open(bs.OUT, encoding="utf-8", newline="") as fh:
            on_disk = list(csv.reader(fh))
        self.assertEqual(on_disk[0], bs.HEADER)
        self.assertEqual(on_disk[1:], self.rows, "spending_breakdowns.csv is stale: run tools/build_spending.py")

    # ---------------------------------------------------------------- exclusion parity and borrowing
    def test_fund_rule_identical_for_income_and_spending(self):
        for (mid, y), sp in self.res.items():
            rc = self.rec.get((mid, y))
            if not rc:
                continue
            spend = {fk: fl["group"] for fk, fl in sp["funds"].items()}
            for fk, fl in rc["funds"].items():
                if fk in spend:
                    self.assertEqual(fl["group"], spend[fk], (mid, y, fk))

    def test_debt_proceeds_never_income(self):
        for y in bs.YEARS:
            units, _ = bs.group_units(bs.read_lines(y, receipts=True), self.unit_map)
            for mid, u in units.items():
                for line in u["lines"]:
                    is_debt = (line["receipt_class_code"].strip() == "8" if u["kind"] == "school"
                               else line["Receipt_Code"].strip() in ("R903", "R904"))
                    if is_debt and bs.money(line["amount"]):
                        self.assertIsNotNone(bs.income_line_excluded(u["kind"], line), (mid, y, line["fund_name"]))
                        self.assertEqual(bs.income_line_excluded(u["kind"], line)[0], bs.G_BORROW)
        self.assertGreater(self.rec[("county-st-joseph", 2025)]["excluded"].get(bs.G_BORROW, ZERO), ZERO)
        self.assertNotIn(bs.G_BORROW, self.rec[("county-st-joseph", 2025)]["income"])

    def test_transfers_in_never_income(self):
        line = {"Receipt_Code": "R910", "receipt_name": "Transfers In - Transferred from Another Fund",
                "receipt_class_code": "900", "section": "0"}
        self.assertEqual(bs.income_line_excluded("city", line)[0], bs.G_TRANSFER)
        school = {"Receipt_Code": "5200", "receipt_name": "Transfers from One Fund to Another",
                  "receipt_class_code": "10", "section": "3"}
        self.assertEqual(bs.income_line_excluded("school", school)[0], bs.G_TRANSFER)

    def test_sbcsc_2025_source_error_left_out(self):
        """The one impossible SBCSC 2025 line ($251,840,353.20 'property taxes' in the Education Fund) is left out in
        its own group; everything else in 2025 is counted, so the year is no longer held back."""
        rec = self.rec[("school-sbcsc", 2025)]
        self.assertEqual(rec["excluded"].get(bs.G_SOURCE_ERROR), D("251840353.20"))
        self.assertLess(rec["income"].get(bs.I_PROP, ZERO), D("95794532"))   # under the 2025 certified levy
        self.assertGreater(rec["income"].get(bs.I_PROP, ZERO), D("75000000"))
        self.assertNotIn(("school-sbcsc", 2025), bs.HELD_INCOME)
        for (mid, y), r in self.rec.items():   # nothing else is caught by the error list
            if (mid, y) != ("school-sbcsc", 2025):
                self.assertNotIn(bs.G_SOURCE_ERROR, r["excluded"], (mid, y))

    def test_development_area_reimbursements_labelled(self):
        """R906 refunds/reimbursements paid into a development-area (TIF) fund get their own label, not the
        generic refunds one (the county's 2025 New Carlisle Dev Area receipts were $61.2M of $71.0M)."""
        dev = {"Receipt_Code": "R906", "receipt_name": "Refunds and Reimbursements", "fund_name": "New Carlisle Dev Area #1",
               "receipt_class_code": "900", "section": "0"}
        self.assertEqual(bs.income_category("county", dev), bs.I_DEVREIMB)
        plain = dict(dev, fund_name="General Fund")
        self.assertEqual(bs.income_category("county", plain), bs.I_REFUND)
        inc = self.rec[("county-st-joseph", 2025)]["income"]
        self.assertGreater(inc.get(bs.I_DEVREIMB, ZERO), D("60000000"))
        self.assertLess(inc.get(bs.I_REFUND, ZERO), D("15000000"))

    # ---------------------------------------------------------------- categories
    def test_every_counted_fund_categorised(self):
        purposes = {p for p, _, _ in bs.PURPOSE_RULES}
        for (mid, y), a in self.res.items():
            if a["kind"] == "school":
                continue
            for fk, fl in a["funds"].items():
                self.assertIn(fl["purpose"], purposes, (mid, y, fk))
        self.assertEqual(bs.purpose_of(bs.fund_info("town-x", "town", {"unit_fund_number": "2599", "Fund_code": "",
                                                                         "fund_name": "ZZZ", "ent_name": ""}))[0], bs.OTHER)

    def test_some_known_purposes(self):
        info = lambda n, name, ent="Governmental Activities": bs.fund_info(
            "county-st-joseph", "county", {"unit_fund_number": str(n), "Fund_code": "", "fund_name": name, "ent_name": ent})
        self.assertEqual(bs.purpose_of(info(1000, "General Fund"))[0], bs.P_GENERAL)
        self.assertEqual(bs.purpose_of(info(1176, "County Highway (MVH)"))[0], bs.P_ROADS)
        self.assertEqual(bs.purpose_of(info(4930, "Dispatch Operating"))[0], bs.P_SAFETY)
        self.assertEqual(bs.purpose_of(info(4302, "New Carlisle Dev Area #1"))[0], bs.P_ECON)
        self.assertEqual(bs.purpose_of(info(4932, "2014 Dispatch Bond Fund"))[0], bs.P_DEBT)

    def test_fold_top(self):
        cats = {f"c{i}": D(str(100 - i)) for i in range(9)}
        out = bs.fold_top(cats)
        self.assertEqual(len(out), bs.TOP_N + 1)
        self.assertEqual(out[-1][0], bs.OTHER)
        self.assertEqual(out[-1][1], D("94") + D("93") + D("92"))
        self.assertEqual(sum((v for _, v, _ in out), ZERO), sum(cats.values(), ZERO))
        self.assertEqual([k for k, _, _ in out[:-1]], [f"c{i}" for i in range(6)])     # largest first
        seven = {f"c{i}": D(str(10 + i)) for i in range(7)}                              # one leftover, no Other
        self.assertEqual(len(bs.fold_top(seven)), 7)
        self.assertNotIn(bs.OTHER, [k for k, _, _ in bs.fold_top(seven)])
        with_other = {"a": D("5"), bs.OTHER: D("50"), "b": D("7")}
        self.assertEqual([k for k, _, _ in bs.fold_top(with_other)], ["b", "a", bs.OTHER])  # Other always last
        for (mid, y, view), rows in self.by.items():
            if view in ("by_purpose", "by_type", "income"):
                self.assertLessEqual(len(rows), bs.TOP_N + 1, (mid, y, view))
                named = [D(r[4]) for r in rows if r[3] != bs.OTHER]
                self.assertEqual(named, sorted(named, reverse=True), (mid, y, view))

    def test_schools(self):
        schools = [m for (m, y) in self.res if m.startswith("school-")]
        self.assertIn("school-union-north", schools)
        for (mid, y), a in self.res.items():
            if a["kind"] != "school":
                continue
            self.assertEqual(self.by[(mid, str(y), "by_type")], [], mid)
            self.assertTrue(set(a["purpose"]) <= set(bs.SCHOOL_PURPOSE.values()), mid)
        self.assertEqual(bs.year_label("school", 2025), "2025-26 school year (state file year 2025)")

    def test_skipped_units(self):
        skipped = {k.upper() for k in self.info["skipped"]}
        self.assertIn("MICHIANA AREA COUNCIL OF GOVERNMENT (6-30)", skipped)
        self.assertFalse(any(r[0].startswith("special-macog") for r in self.rows))


if __name__ == "__main__":
    unittest.main()
