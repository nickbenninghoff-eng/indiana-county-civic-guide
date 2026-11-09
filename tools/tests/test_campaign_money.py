"""Tests for whole-cycle campaign money (tools/site/civic/campaign_money.py) and the campaign-money map
(tools/site/civic/campaign_map.py).

Run:  python -P -E -m unittest discover -s tools/tests

The real-data tests recompute every displayed total independently from the raw cf_local.csv text with Decimal
(never through the module's own arithmetic), and check that every filing is placed exactly once.
"""
from __future__ import annotations

import csv
import sys
import unittest
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "site"))

from civic import campaign_money as cm  # noqa: E402

SPEC26 = cm.spec_for("2026", date(2026, 5, 5), date(2026, 11, 3))
SPEC24 = cm.spec_for("2024", date(2024, 5, 7), date(2024, 11, 5))
SPEC23 = cm.spec_for("2023 municipal", date(2023, 5, 2), date(2023, 11, 7))
N = 0


def r(rt, pf, pt, e="0.00", rc="0.00", cs="0.00", ce="0.00", ey="", ry="", amended="no", status="verified", key="k",
      notes=""):
    global N
    N += 1
    return {"filing_id": f"cfl-{N}", "doc_ids": str(70000 + N), "report_type": rt, "period_from": pf, "period_to": pt,
            "expenditures_period": e, "receipts_period": rc, "cash_start_period": cs, "cash_end_period": ce,
            "expenditures_ytd": ey, "receipts_ytd": ry, "amended": amended, "transcription_status": status,
            "_key": key, "party": "", "candidate": "A B", "notes": notes}


class Money(unittest.TestCase):
    def test_cents(self):
        self.assertEqual(cm.cents("1,234.56"), 123456)
        self.assertEqual(cm.cents("0.005"), 1)
        self.assertEqual(cm.cents("12"), 1200)
        self.assertIsNone(cm.cents(""))
        self.assertIsNone(cm.cents("n/a"))
        self.assertEqual(cm.usd(123456), "$1,234.56")
        self.assertEqual(cm.usd(-500), "-$5.00")
        self.assertEqual(cm.usd(None), "not on file")
        self.assertEqual(cm.usd_round(123450), "$1,235")


class Cycles(unittest.TestCase):
    def test_cycle_rule(self):
        self.assertEqual(cm.cycle_of({"period_to": "2023-12-31", "report_type": "Annual"}), "2023 municipal")
        self.assertEqual(cm.cycle_of({"period_to": "2025-02-10", "report_type": "Annual"}), "2024")
        self.assertEqual(cm.cycle_of({"period_to": "2025-02-10", "report_type": "Pre-Primary"}), "2026")
        self.assertEqual(cm.cycle_of({"period_to": "2025-12-31", "report_type": "Annual"}), "2026")
        self.assertEqual(cm.cycle_of({"period_to": "2026-01-15", "report_type": "Final"}), "2026")
        self.assertEqual(cm.cycle_of({"period_to": "2024-03-01", "report_type": ""}), "2023 municipal")
        self.assertEqual(cm.cycle_of({"period_to": "", "report_type": "Annual"}), "period unknown")

    def test_slots(self):
        self.assertEqual(cm.slot_of(r("Annual", "2025-01-01", "2025-12-31"), SPEC26), "prior-annual")
        self.assertEqual(cm.slot_of(r("Annual", "", "2026-01-20"), SPEC26), "prior-annual")
        self.assertEqual(cm.slot_of(r("Pre-Primary", "2026-01-01", "2026-04-10"), SPEC26), "pre-primary")
        self.assertEqual(cm.slot_of(r("Pre-Election", "2026-04-11", "2026-10-09"), SPEC26), "pre-election")
        self.assertEqual(cm.slot_of(r("Annual", "2024-10-12", "2024-12-31"), SPEC24), "year-end")
        self.assertEqual(cm.slot_of(r("Pre-Election", "2024-01-01", "2024-04-12"), SPEC24), "pre-primary")
        self.assertIsNone(cm.slot_of(r("Annual", "", ""), SPEC24))
        self.assertEqual(cm.slot_of(r("Final", "2024", "2024"), SPEC24), "year-end")


class Committee(unittest.TestCase):
    def test_full_2026_cycle_sums_periods(self):
        rows = [r("Annual", "2025-01-01", "2025-12-31", e="100.10", rc="50", cs="0", ce="-50.10", ey="100.10", ry="50"),
                r("Pre-Primary", "2026-01-01", "2026-04-10", e="20", rc="30", cs="-50.10", ce="-40.10", ey="20", ry="30"),
                r("Pre-Election", "2026-04-11", "2026-10-09", e="5", rc="0", cs="-40.10", ce="-45.10", ey="25", ry="30")]
        s = cm.committee_summary(rows, SPEC26, ["Annual", "Pre-Primary", "Pre-Election"])
        self.assertEqual(s["spent"], 12510)
        self.assertEqual(s["raised"], 8000)
        self.assertEqual(s["missing"], [])
        self.assertNotIn("ytd", s["flags"])

    def test_amendment_replaces_original(self):
        orig = r("Pre-Primary", "2026-01-01", "2026-04-10", e="100", ce="900")
        amd = r("Pre-Primary", "2026-01-01", "2026-04-10", e="300", ce="700", amended="yes")
        s = cm.committee_summary([orig, amd], SPEC26, ["Pre-Primary"])
        self.assertEqual(s["spent"], 30000)
        self.assertEqual([x["filing_id"] for x in s["counted"]], [amd["filing_id"]])
        it = next(i for i in s["items"] if i["row"] is orig)
        self.assertEqual(it["why"], "replaced")

    def test_contained_report_not_added_twice(self):
        pre = r("Pre-Primary", "2024-01-01", "2024-04-15", e="200", rc="300", cs="0", ce="623.27")
        fin = r("Final", "2024-01-01", "2024-12-31", e="900", rc="900", cs="0", ce="0", ey="900")
        s = cm.committee_summary([pre, fin], SPEC24, ["Pre-Primary", "Pre-Election", "Annual"])
        self.assertEqual(s["spent"], 90000)
        self.assertEqual(next(i for i in s["items"] if i["row"] is pre)["why"], "inside")
        self.assertEqual(s["drops"], [{"id": pre["filing_id"], "why": "inside", "by": fin["filing_id"]}])

    def test_contained_report_whose_money_the_outer_lacks_is_kept(self):
        # the Verash case (docs 62629 and 66176): a full-year final that reports $0 spent can't include a pre-primary
        # report's $4,945.21, so the pre-primary is not "inside" it; both count and the conflict is flagged
        pre = r("Pre-Primary", "2024-01-01", "2024-04-15", e="4945.21", rc="5568.48", cs="0", ce="623.27")
        fin = r("Final", "2024-01-01", "2024-12-31", e="0.00", rc="623.27", cs="0", ce="0", ey="0.00", ry="623.27")
        s = cm.committee_summary([pre, fin], SPEC24, ["Pre-Primary", "Pre-Election", "Annual"])
        self.assertEqual(s["spent"], 494521)
        self.assertEqual(s["drops"], [])
        self.assertIn("date-conflict", s["flags"])
        self.assertTrue(all(i["counted"] for i in s["items"]))

    def test_same_report_filed_twice_is_added_once(self):
        a = r("Pre-Primary", "2026-01-01", "2026-04-10", e="75", rc="80", cs="10", ce="15")
        b = r("Pre-Primary", "2026-01-01", "2026-04-10", e="75", rc="80", cs="10", ce="15")
        s = cm.committee_summary([a, b], SPEC26, ["Pre-Primary"])
        self.assertEqual(s["spent"], 7500)
        self.assertEqual([d["why"] for d in s["drops"]], ["duplicate"])

    # --- regression: the nested-period rule must never drop a real report (Eli Wax, docs 60837 and 66082)
    def test_wax_cash_chain_with_nested_dates_counts_both(self):
        # 60837: the real 2023 annual (start date blank). 66082: dated 1/1/2023-12/31/2023, but it opens with 60837's
        # closing cash. Without a transcription note naming the right year, both count, flagged; no YTD shortcut.
        a = r("Annual", "", "2023-12-31", e="30287.82", rc="24756.35", cs="7263.00", ce="1731.53", ey="30287.82",
              ry="24756.35")
        b = r("Annual", "2023-01-01", "2023-12-31", e="61.63", rc="0.00", cs="1731.53", ce="1669.90", ey="61.63", ry="0.00")
        s = cm.committee_summary([a, b], SPEC23, ["Annual"])
        self.assertEqual(s["spent"], 3028782 + 6163)
        self.assertEqual(s["raised"], 2475635)
        self.assertEqual(s["drops"], [])
        self.assertIn("date-conflict", s["flags"])
        self.assertTrue(all(i["counted"] for i in s["items"]))
        self.assertEqual({b_["how"] for b_ in s["basis"]}, {"periods"})
        self.assertTrue(any("opening cash equals" in n for i in s["items"] for n in i["notes"]))
        self.assertEqual(s["cash"], 166990)            # the end of the cash chain

    def test_wax_note_naming_the_year_moves_the_report(self):
        note = ("Owner check: the form states the period 1/1/2023-12/31/2023, but its opening cash (1,731.53) equals the "
                "closing cash on this committee's 2023 annual report (doc 60837) and the county stamped it Feb 2025 in "
                "the 2024 batch; the year is probably miswritten for 2024. Period shown as written.")
        b = r("Annual", "2023-01-01", "2023-12-31", e="61.63", cs="1731.53", ce="1669.90", ey="61.63", notes=note)
        self.assertEqual(cm.cycle_of(b), "2023 municipal")          # the coverage matrix keeps the date as written
        self.assertEqual(cm.money_cycle(b), "2024")
        self.assertEqual((cm._pf(b), cm._pt(b)), ("2024-01-01", "2024-12-31"))
        s = cm.committee_summary([b], SPEC24, ["Pre-Primary", "Pre-Election", "Annual"], "none")
        self.assertEqual(s["items"][0]["slot"], "year-end")
        self.assertIn("date-read", s["flags"])
        self.assertTrue(any("probably miswritten for 2024" in n for n in s["items"][0]["notes"]))

    def test_cash_chain_is_sequential_even_when_dates_nest(self):
        pre = r("Pre-Primary", "2024-01-01", "2024-04-15", e="100", rc="600", cs="0", ce="500")
        ann = r("Annual", "2024-01-01", "2024-12-31", e="50", rc="0", cs="500", ce="450", ey="50")   # 1/1 written for 4/16
        s = cm.committee_summary([pre, ann], SPEC24, ["Pre-Primary", "Annual"])
        self.assertEqual(s["spent"], 15000)
        self.assertEqual(s["drops"], [])
        self.assertIn("date-conflict", s["flags"])
        # reversed: the report dated later closes at the other's opening balance
        x = r("Pre-Election", "2024-04-16", "2024-10-11", e="30", cs="200", ce="170")
        y = r("Annual", "2024-01-01", "2024-12-31", e="40", cs="0", ce="200")
        s = cm.committee_summary([x, y], SPEC24, ["Pre-Election", "Annual"])
        self.assertEqual(s["spent"], 7000)
        self.assertEqual(s["drops"], [])
        # an ordinary chain whose start date overlaps a little is not a conflict
        f = r("Pre-Election", "2024-04-13", "2024-10-11", e="10", cs="0", ce="4329.58")
        g = r("Annual", "2024-10-01", "2024-12-31", e="20", cs="4329.58", ce="0")
        s = cm.committee_summary([f, g], SPEC24, ["Pre-Election", "Annual"])
        self.assertEqual(s["spent"], 3000)
        self.assertNotIn("date-conflict", s["flags"])

    def test_zero_balance_chain_with_nested_dates_drops_nothing(self):
        a = r("Pre-Election", "2024-08-28", "2024-10-11", e="2260.86", rc="2260.86", cs="0", ce="0")
        b = r("Annual", "2024-08-28", "2024-12-15", e="2260.86", rc="2035.13", cs="0", ce="0")
        s = cm.committee_summary([a, b], SPEC24, ["Pre-Election", "Annual"])
        self.assertEqual(s["spent"], 452172)
        self.assertEqual(s["drops"], [])
        self.assertIn("date-conflict", s["flags"])

    def test_blank_start_never_puts_a_report_inside_another(self):
        inner = r("Pre-Primary", "", "2024-04-15", e="200", cs="0", ce="90")
        outer = r("Annual", "2024-01-01", "2024-12-31", e="900", cs="5", ce="0", ey="900")
        self.assertFalse(cm._contains(outer, inner))
        self.assertFalse(cm._contains(inner, outer))
        s = cm.committee_summary([inner, outer], SPEC24, ["Pre-Primary", "Annual"])
        self.assertEqual(s["drops"], [])                 # never dropped; the known end date overlaps, so no total
        self.assertTrue(all(i["counted"] for i in s["items"]))
        self.assertIsNone(s["spent"])
        # a blank-start annual after a pre-election report: both counted, and the YTD shortcut only applies when it
        # is not below the reports on file
        pre = r("Pre-Election", "2023-04-01", "2023-10-13", e="300", cs="0", ce="40")
        ann = r("Annual", "", "2023-12-31", e="100", cs="45", ce="5", ey="250")
        s = cm.committee_summary([pre, ann], SPEC23, ["Annual"])
        self.assertEqual(s["drops"], [])
        self.assertEqual(s["spent"], 40000)
        self.assertIn("ytd-low", s["flags"])

    def test_ytd_below_the_reports_on_file_is_not_used(self):
        # the Dieter case (docs 64452 and 65634): the annual's YTD column repeats its own period figure
        pre = r("Pre-Election", "2024-04-13", "2024-10-11", e="45026.52", rc="46924.03", cs="51.70", ce="1949.21",
                ey="45026.52", ry="46924.03")
        ann = r("", "2024-10-12", "2024-12-31", e="1874.78", rc="1940.00", cs="1249.52", ce="1314.74", ey="1874.78",
                ry="1940.00", status="derived")
        s = cm.committee_summary([pre, ann], SPEC24, ["Pre-Primary", "Pre-Election", "Annual"])
        self.assertEqual(s["spent"], 4690130)
        self.assertEqual(s["raised"], 4886403)
        self.assertIn("ytd-low", s["flags"])

    def test_chained_dates_overlap_both_counted(self):
        a = r("Pre-Primary", "2024-01-01", "2024-04-19", e="10", cs="0", ce="90")
        b = r("Pre-Election", "2024-04-13", "2024-10-11", e="20", cs="90", ce="70")
        s = cm.committee_summary([a, b], SPEC24, ["Pre-Primary", "Pre-Election"])
        self.assertEqual(s["spent"], 3000)
        self.assertTrue(any("overlap" in n for n in s["items"][1]["notes"]))

    def test_tangled_overlap_gives_no_total(self):
        a = r("Pre-Primary", "2024-01-01", "2024-06-30", e="10", cs="0", ce="90")
        b = r("Pre-Election", "2024-04-01", "2024-10-11", e="20", cs="5", ce="70")
        s = cm.committee_summary([a, b], SPEC24, ["Pre-Primary", "Pre-Election"])
        self.assertIsNone(s["spent"])
        self.assertIn("overlap", s["flags"])

    def test_one_day_overlap_is_contiguous(self):
        a = r("Pre-Primary", "2026-01-01", "2026-04-10", e="10", cs="0", ce="90")
        b = r("Pre-Election", "2026-04-10", "2026-10-09", e="20", cs="91", ce="70")
        s = cm.committee_summary([a, b], SPEC26, ["Pre-Primary", "Pre-Election"])
        self.assertEqual(s["spent"], 3000)

    def test_year_to_date_used_when_year_not_covered(self):
        # 2023: the county posted only the annual report; its own period starts in the fall
        a = r("Annual", "", "2023-12-31", e="100", rc="10", ey="5000", ry="4000", status="verified")
        s = cm.committee_summary([a], SPEC23, ["Annual"])
        self.assertEqual(s["spent"], 500000)
        self.assertEqual(s["raised"], 400000)
        self.assertIn("ytd-used", s["flags"])
        self.assertEqual(s["basis"][0]["col"], "expenditures_ytd")

    def test_year_to_date_not_used_when_report_does_not_reconcile(self):
        # outside the years whose earlier reports the county never posted, a non-reconciling form's year-to-date
        # column is not trusted over the reports on file (doc 72826: it adds 2025 money already counted)
        pre = r("Pre-Election", "2024-04-13", "2024-10-11", e="100", ey="5000", status="filer-inconsistent")
        s = cm.committee_summary([pre], SPEC24, ["Pre-Primary", "Pre-Election"])
        self.assertEqual(s["spent"], 10000)
        self.assertIn("ytd", s["flags"])

    def test_bolden_simpson_2023_uses_the_filers_ytd_even_when_the_form_does_not_reconcile(self):
        # doc 60884: blank start, $9,354.38 this period, $24,607.97 year to date, opening cash $8,262.29 (earlier 2023
        # activity); the county posted no earlier 2023 reports, so the period column is known to fall short
        a = r("Annual", "", "2023-12-31", e="9354.38", rc="1700.00", cs="8262.29", ce="607.91", ey="24607.97",
              ry="24607.97", status="filer-inconsistent")
        s = cm.committee_summary([a], SPEC23, ["Annual"])
        self.assertEqual(s["spent"], 2460797)
        self.assertEqual(s["raised"], 2460797)
        self.assertIn("ytd-used", s["flags"])
        self.assertIn("ytd-unreconciled", s["flags"])
        self.assertIsNone(s["cash"])                       # cash still only from a reconciling report
        u = cm.ytd_uses([s])
        self.assertEqual([(x["year"], x["words"], x["clean"]) for x in u], [(2023, ["spent", "raised"], False)])
        line = cm.ytd_line(u[0])
        self.assertIn("year-to-date figure from the filer's annual report", line)
        self.assertIn("the county did not post earlier 2023 reports", line)

    def test_2023_reports_from_january_1_are_added_not_doubled_by_ytd(self):
        # the opposite failure: several 2023 reports that run from January 1 with no gap add their periods; the
        # latest one's year-to-date column (which repeats them) is checked, not added
        a = r("Pre-Primary", "2023-01-01", "2023-04-14", e="1000", cs="0", ce="500", ey="1000")
        b = r("Pre-Election", "2023-04-15", "2023-10-13", e="2000", cs="500", ce="300", ey="3000")
        c = r("Annual", "2023-10-14", "2023-12-31", e="500", cs="300", ce="100", ey="3500", status="filer-inconsistent")
        s = cm.committee_summary([a, b, c], SPEC23, ["Annual"])
        self.assertEqual(s["spent"], 350000)
        self.assertEqual({x["how"] for x in s["basis"]}, {"periods"})
        self.assertEqual(cm.ytd_uses([s]), [])

    def test_cumulative_ytd_is_not_added_to_an_earlier_year_already_counted(self):
        # doc 72826 (Laureys): the 2026 year-to-date column equals 2025's report plus both 2026 reports
        y25 = r("Pre-Primary", "2025-01-01", "2025-12-21", e="23861.39", cs="0", ce="16444.55")
        p26 = r("Pre-Primary", "2025-12-21", "2026-04-10", e="22103.17", cs="", ce="-2178.17", ey="45964.56")
        e26 = r("Pre-Election", "2026-04-11", "2026-10-09", e="44405.08", cs="11908.73", ce="1079.98", ey="90369.64")
        s = cm.committee_summary([y25, p26, e26], SPEC26, ["Pre-Primary", "Pre-Election"])
        self.assertEqual(s["spent"], 2386139 + 2210317 + 4440508)
        self.assertIn("ytd-cumulative", s["flags"])

    def test_covered_year_prefers_reports_over_wrong_ytd(self):
        a = r("Pre-Primary", "2024-01-01", "2024-03-31", e="40", cs="0", ce="0")
        b = r("Pre-Election", "2024-04-01", "2024-10-18", e="1000", cs="0", ce="0", ey="1000")
        c = r("Annual", "2024-10-19", "2024-12-31", e="5", cs="0", ce="0", ey="1005")
        s = cm.committee_summary([a, b, c], SPEC24, ["Pre-Primary", "Pre-Election", "Annual"])
        self.assertEqual(s["spent"], 104500)
        self.assertIn("ytd", s["flags"])

    def test_missing_pre_primary_uses_ytd_and_flags_missing(self):
        b = r("Pre-Election", "2026-04-11", "2026-10-09", e="80", cs="20", ce="0", ey="100", status="verified")
        s = cm.committee_summary([b], SPEC26, ["Annual", "Pre-Primary", "Pre-Election"])
        self.assertEqual(s["missing"], ["prior-annual", "pre-primary"])
        self.assertEqual(s["spent"], 10000)

    def test_expected_by_ballot_line(self):
        b = r("Pre-Election", "2026-04-11", "2026-10-09")
        exp = ["Annual", "Pre-Primary", "Pre-Election"]
        self.assertEqual(cm.committee_summary([b], SPEC26, exp, "general-only")["missing"], ["prior-annual"])
        p = r("Pre-Primary", "2026-01-01", "2026-04-10")
        self.assertEqual(cm.committee_summary([p], SPEC26, exp, "primary")["missing"], ["prior-annual"])
        self.assertEqual(cm.committee_summary([p], SPEC26, exp, "none")["missing"], ["prior-annual"])
        a = r("Annual", "2025-01-01", "2025-12-31")
        self.assertEqual(cm.committee_summary([a], SPEC26, exp, "none")["missing"], [])

    def test_nothing_expected_after_final(self):
        f = r("Final", "2024-01-01", "2024-04-30")
        s = cm.committee_summary([f], SPEC24, ["Pre-Primary", "Pre-Election", "Annual"])
        self.assertEqual(s["missing"], [])

    def test_blank_line_flagged(self):
        a = r("Pre-Primary", "2026-01-01", "2026-04-10", e="", ey="")
        s = cm.committee_summary([a], SPEC26, ["Pre-Primary"])
        self.assertIn("blank", s["flags"])
        self.assertEqual(s["spent"], 0)

    def test_cash_only_when_clean(self):
        a = r("Pre-Primary", "2026-01-01", "2026-04-10", ce="55", status="filer-inconsistent")
        s = cm.committee_summary([a], SPEC26, ["Pre-Primary"])
        self.assertIsNone(s["cash"])
        self.assertTrue(s["cash_why"])
        b = r("Pre-Primary", "2026-01-01", "2026-04-10", ce="55", status="derived")
        self.assertEqual(cm.committee_summary([b], SPEC26, ["Pre-Primary"])["cash"], 5500)


class Dates(unittest.TestCase):
    def test_date_fix_reads_only_explicit_corrections(self):
        x = r("Pre-Election", "2024-04-11", "2026-10-09",
              notes="From date handwritten 4/11/2024 (likely typo for 2026; last digit reads 4).")
        self.assertEqual(cm.date_fix(x)["kind"], "from")
        self.assertEqual(cm._pf(x), "2026-04-11")
        # the CSV already holds the corrected date: nothing to do
        y = r("Annual", "", "2023-12-31", notes="Period-through written as 12/31/24 (likely typo for 12/31/23).")
        self.assertIsNone(cm.date_fix(y))
        z = r("Pre-Primary", "2026-01-01", "2026-04-10", notes="Period-through written 04/10/2062 (evident typo for 2026)")
        self.assertIsNone(cm.date_fix(z))
        # a doubt without the right year: dates kept, report flagged
        w = r("Annual", "2026-01-01", "2026-12-31", notes="filed in 2025 annual batch; likely year typo")
        self.assertEqual(cm.date_fix(w)["kind"], "doubt")
        self.assertEqual(cm._pt(w), "2026-12-31")
        s = cm.committee_summary([w], SPEC26, ["Annual"], "none", today=date(2026, 11, 9))
        self.assertIn("date-doubt", s["flags"])
        self.assertIsNone(cm.date_fix(r("Annual", "2025-01-01", "2025-12-31", notes="Filer typo in 16B (469 vs 689)")))


class Party(unittest.TestCase):
    def test_party_line_says_how_many_candidates_it_covers(self):
        def cand(party, spent, committees=True):
            return {"party": party, "spent": spent, "committees": [{}] if committees else []}
        cands = [cand("R", 6163), cand("R", None, False), cand("R", None, False), cand("R", None, False),
                 cand("D", 100), cand("D", None), cand("L", None, False)]
        counts = cm.count_parties(cands)
        parts = cm.party_parts({"D": 100, "R": 6163}, counts, lambda p: {"R": "Republican (R)", "D": "Democrat (D)",
                                                                         "L": "Libertarian (L)"}[p])
        self.assertEqual(parts, ["Democrat (D) $1.00: 1 of 2 candidates with reports (1 more with reports that can't "
                                 "be added up)",
                                 "Libertarian (L): no reports added for its 1 candidate",
                                 "Republican (R) $61.63: 1 of 4 candidates with reports"])


class Names(unittest.TestCase):
    def test_matching(self):
        self.assertTrue(cm.same_person("Bill Redman", "William Redman"))
        self.assertTrue(cm.same_person('Dale Douglas Chaffee "Doug Chaffee"', "Doug Chaffee"))
        self.assertFalse(cm.same_person("Bryan L Albright", "Joshua A Albright"))
        self.assertTrue(cm._edit1("mammolent", "mammolenti"))
        self.assertFalse(cm._edit1("hazen", "hazen"))
        self.assertTrue(cm._reordered("McCormick Thomas Eric, aka Tom", "Tom E McCormick"))

    def test_contest_mapping(self):
        x = cm.contest_race("St. Joseph County Council, District B (Republican primary)")
        self.assertEqual((x["unit"], x["office"], x["district"]), ("county", "County Council District B", "B"))
        x = cm.contest_race("South Bend: Common Council, District 3")
        self.assertEqual((x["unit"], x["district"]), ("south-bend", "3"))
        x = cm.contest_race("Town of Walkerton: Town Council, Ward 2")
        self.assertEqual((x["unit"], x["office"], x["district"]), ("walkerton", "Walkerton Town Council Ward 2", "Ward 2"))
        self.assertEqual(cm.contest_race("St. Joseph County Judge of the Probate Court")["type"], "courts")
        self.assertIsNone(cm.contest_race("Straight-party ballots"))


# ---------------------------------------------------------------------------------------- real data
class RealData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from civic.data import Edition
        from pages import campaigns as cf
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.d = cf.cf_all(cls.ed)
        with open(ROOT / "data" / "editions" / "st-joseph" / "cf_local.csv", encoding="utf-8-sig", newline="") as fh:
            cls.raw = {x["filing_id"]: x for x in csv.DictReader(fh)}

    def dec(self, fid, col) -> Decimal:
        return Decimal(self.raw[fid][col].strip())

    def test_every_total_is_the_sum_of_its_rows(self):
        for race in self.d["races"]:
            total = Decimal(0)
            n_with = 0
            by_party = defaultdict(Decimal)
            for c in race["candidates"]:
                if not c["committees"]:
                    self.assertIsNone(c["spent"])
                    continue
                n_with += 1
                cand = Decimal(0)
                for s in c["committees"]:
                    if s["spent"] is None:
                        cand = None
                        break
                    com = Decimal(0)
                    for b in s["basis"]:
                        if b["word"] != "spent":
                            continue
                        for fid in b["ids"]:
                            self.assertIn(fid, race["counted_ids"])
                            com += self.dec(fid, b["col"])
                    self.assertEqual(com * 100, s["spent"], (race["id"], c["name"]))
                    cand += com
                if cand is None:
                    self.assertIsNone(c["spent"])
                    continue
                self.assertEqual(cand * 100, c["spent"], (race["id"], c["name"]))
                total += cand
                by_party[c["party"]] += cand
            if n_with:
                self.assertEqual(total * 100, race["spent"], race["id"])
                self.assertEqual({k: v * 100 for k, v in by_party.items()}, dict(race["by_party"]), race["id"])
            else:
                self.assertIsNone(race["spent"])

    def test_area_totals_add_the_latest_races(self):
        for a in self.d["areas"].values():
            latest = [r for r in a["races"] if r["general_eid"] == a["latest"]]
            self.assertEqual(latest, a["latest_races"])
            spent = [r["spent"] for r in latest if r["spent"] is not None]
            self.assertEqual(a["spent"], sum(spent) if spent else None, a["id"])

    def test_each_filing_placed_once_and_counted_in_one_race(self):
        placed = [f for r in self.d["races"] for f in r["listed_ids"]]
        placed += [x["filing_id"] for a in self.d["areas"].values() for rows in a["other"].values() for x in rows]
        placed += [x["filing_id"] for x in self.d["other"]]
        self.assertEqual(sorted(placed), sorted(self.raw))
        counted = [f for r in self.d["races"] for f in r["counted_ids"]]
        self.assertEqual(len(counted), len(set(counted)))

    def test_amended_rows_are_not_double_counted(self):
        # no counted filing shares committee, slot and overlapping period with another counted filing
        for race in self.d["races"]:
            for c in race["candidates"]:
                for s in c["committees"]:
                    seen = defaultdict(list)
                    for it in s["items"]:
                        if it["counted"]:
                            seen[it["slot"]].append(it["row"])
                    conflicted = {it["row"]["filing_id"] for it in s["items"] if it["conflict"]}
                    for rows in seen.values():
                        for i, a in enumerate(rows):
                            for b in rows[i + 1:]:
                                if {a["filing_id"], b["filing_id"]} <= conflicted:
                                    continue          # counted both on purpose, flagged on the page
                                self.assertFalse(cm._contains(a, b) or cm._contains(b, a), (a["filing_id"], b["filing_id"]))

    def test_cycles_follow_the_rule(self):
        for race in self.d["races"]:
            for fid in race["listed_ids"]:
                row = self.raw[fid]
                self.assertEqual(cm.money_cycle(row), race["cycle"], fid)
                if cm.cycle_of(row) != race["cycle"]:
                    self.assertEqual(cm.date_fix(row)["kind"], "year", fid)

    def test_bolden_simpson_counts_her_2023_ytd(self):
        race = next(r for r in self.d["races"] if r["id"] == "2023g-south-bend-council-5")
        sbs = next(c for c in race["candidates"] if c["name"].startswith("Sherry"))
        self.assertEqual(sbs["spent"], 2460797)
        self.assertEqual(race["spent"], 2460797 + 3028782)
        self.assertEqual(race["by_party"]["D"], 2460797)

    def test_every_2023_annual_with_a_larger_ytd_uses_it(self):
        # Nick's decision 3: the county posted no earlier 2023 reports, so each 2023 annual or final report whose
        # year-to-date spending exceeds its period spending is counted at its year-to-date figure
        n = 0
        for race in self.d["races"]:
            for c in race["candidates"]:
                for s in c["committees"]:
                    for x in s["counted"]:
                        if cm.money_year(x) != 2023 or not any(t in x["report_type"] for t in ("Annual", "Final")):
                            continue
                        e, ey = cm.cents(x["expenditures_period"]) or 0, cm.cents(x["expenditures_ytd"])
                        if ey is None or ey <= e:
                            continue
                        n += 1
                        b = next(b for b in s["basis"] if b["year"] == 2023 and b["word"] == "spent")
                        self.assertEqual((b["how"], b["ids"], b["value"]), ("ytd", [x["filing_id"]], ey), x["filing_id"])
        self.assertGreaterEqual(n, 19)

    def test_wax_counts_his_2023_annual(self):
        race = next(r for r in self.d["races"] if r["id"] == "2023g-south-bend-council-5")
        wax = next(c for c in race["candidates"] if c["name"] == "Eli Wax")
        self.assertEqual(wax["spent"], 3028782)
        self.assertEqual(wax["raised"], 2475635)
        self.assertEqual(wax["cash"], 173153)
        self.assertEqual(race["by_party"]["R"], 3028782)
        self.assertEqual(race["party_counts"]["R"], {"with": 1, "listed": 0, "of": 1})
        self.assertIn("cfl-60837", race["counted_ids"])
        self.assertNotIn("cfl-66082", race["listed_ids"])
        sb = [x["filing_id"] for rows in self.d["areas"]["south-bend"]["other"].values() for x in rows]
        self.assertIn("cfl-66082", sb)
        self.assertEqual([x["filing_id"] for x in wax["committees"][0]["moved_out"]], ["cfl-66082"])

    def test_no_real_report_dropped_or_erased_by_a_ytd_figure(self):
        for race in self.d["races"]:
            for c in race["candidates"]:
                for s in c["committees"]:
                    ids = {it["row"]["filing_id"]: it for it in s["items"]}
                    for d in s["drops"]:
                        self.assertIn(d["why"], ("replaced", "inside", "duplicate", "no-period"), d)
                        if d["why"] == "inside":
                            self.assertTrue(cm._covers(ids[d["by"]]["row"], ids[d["id"]]["row"]), d)
                    for it in s["items"]:
                        if not it["counted"]:
                            self.assertIn(it["row"]["filing_id"], [d["id"] for d in s["drops"]])
                    for b in s["basis"]:
                        if b["how"] != "ytd":
                            continue
                        col = "expenditures_period" if b["word"] == "spent" else "receipts_period"
                        rows = [it["row"] for it in s["items"] if it["counted"] and cm.money_year(it["row"]) == b["year"]
                                and it["row"].get("transcription_status") != "unreadable"]
                        psum = sum(Decimal(x[col]) for x in rows if x[col].strip())
                        self.assertGreaterEqual(Decimal(b["value"]) / 100, psum, (race["id"], c["name"], b["year"]))

    def test_party_counts_cover_every_candidate(self):
        for race in self.d["races"]:
            self.assertEqual(sum(k["of"] for k in race["party_counts"].values()), len(race["candidates"]), race["id"])
            for p, v in race["by_party"].items():
                k = race["party_counts"][p]
                n = sum(1 for c in race["candidates"] if c["party"] == p and c["committees"] and c["spent"] is not None)
                self.assertEqual(k["with"], n, race["id"])

    def test_no_reports_is_not_zero(self):
        empty = [r for r in self.d["races"] if r["n_with"] == 0]
        self.assertTrue(empty)
        for r in empty:
            self.assertIsNone(r["spent"])
            self.assertFalse(r["complete"])

    def test_map_panel_shows_the_model_totals(self):
        from civic.campaign_map import district_sets, load_district_shapes, map_layers
        from civic.map import load_shapes

        class P:
            def rel(self, x):
                return x
        shapes = load_shapes(self.ed)
        dsets = district_sets(self.ed, self.d["races"], load_district_shapes(self.ed, shapes))
        self.assertTrue(any(s["type"] == "county" for s in dsets))
        layers = map_layers(self.ed, P(), shapes, dsets, self.d["areas"], self.ed.table("cf_state"))
        by_id = {r["id"]: r for r in self.d["races"]}
        uids = set()
        seen_area = 0
        for L in layers:
            for s in L["shapes"]:
                self.assertNotIn(s["uid"], uids)
                uids.add(s["uid"])
                f = dict(tuple(x) for x in s["entry"]["f"])
                if "#r-" in s["href"]:
                    race = by_id[s["href"].split("#r-")[1]]
                    want = cm.usd(race["spent"]) if race["spent"] is not None else "No reports on file"
                    self.assertTrue(f["Spent, all candidates"].startswith(want), s["uid"])
                    self.assertEqual(s["value"], race["spent"] / 100 if race["spent"] is not None else None)
                elif L["kind"] == "area":
                    seen_area += 1
                    aid = s["href"].split("/")[2]
                    a = self.d["areas"][aid]
                    if a["latest"] and a["spent"] is not None:
                        self.assertTrue(f["Spent, all candidates"].startswith(cm.usd(a["spent"])), aid)
                if s.get("plain"):
                    self.assertIsNone(s.get("shade"))
        self.assertGreater(seen_area, 20)
        # no party colour: shapes carry only ramp, no-data or neutral classes
        for L in layers:
            for s in L["shapes"]:
                self.assertIn(s.get("shade"), (None, 1, 2, 3, 4, 5))

    def test_district_layers_degrade_without_shapes(self):
        from civic.campaign_map import district_sets
        self.assertEqual(district_sets(self.ed, self.d["races"], None), [])
        self.assertEqual(district_sets(self.ed, self.d["races"], {"sets": {"x": {"office_pattern": "Nope {d}",
                                                                                  "items": []}}}), [])


if __name__ == "__main__":
    unittest.main()
