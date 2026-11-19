"""tools/check_results.py: the overall_results.csv rules added by the second merge of 2026-11-18
(planning/gapfill/overall/merge2/merge2.py).

overall_results.csv holds the overall (district-wide, statewide or whole-corporation) result of a multi-county contest,
shown beside the county portion in results.csv. Each test builds a small data tree in a temporary folder, copies the
real checker into <tmp>/tools/ and runs it end to end (same harness as test_checkers_gapfill2.py). A baseline fixture
passes with 0 errors; each case changes one thing and expects exactly the error the rule names, or still 0.

Rules: contest_id exists in results.csv; unique (contest_id, candidate); whole-number votes and totals; pct recomputes
from overall_total_votes within rounding; `derived` vocabulary and filled; vote_for equals results.csv; exactly vote_for
winners (fewer only with fewer rows than seats or a "fewer winners than seats" note) and winners have the most votes;
one total per contest, not less than the sum of its rows; sources resolve; no 2026g row may be official; overall_votes
>= county votes unless the notes say "county figure exceeds the overall"; neutral wording, never "certified"; missing
file is an error.
Run:  python -P -E -m unittest discover -s tools/tests -p test_checkers_overall.py
"""
from __future__ import annotations

import unittest

import test_checkers_gapfill2 as base   # module import: its TestCase classes are not collected again here

ED = base.ED
OVCOLS = base.OVCOLS
DER = "overall_pct;overall_winner;overall_total_votes"
NOTE = ("Official results as reported to the Secretary of State (Indiana Election Division historical results "
        "portal). Percent, winner and total are computed: share of votes for the candidates listed in the state's "
        "results.")


def ov_row(cid, cand, votes, pct, winner, total, vote_for="1", party="D", status="official", ids="RES-001",
           notes=NOTE, derived=DER):
    return {"contest_id": cid, "candidate": cand, "candidate_in_source": cand, "party": party, "overall_votes": votes,
            "overall_pct": pct, "overall_winner": winner, "overall_total_votes": total, "derived": derived,
            "electorate": "district-wide (all counties)", "vote_for": vote_for, "status": status,
            "confidence": "high", "source_ids": ids, "notes": notes}


def files():
    fs = base.results_files()
    res = fs[ED / "results.csv"][1]
    # a multi-county legislative contest (county part 600 / 400) and a retention (vote_for blank, as in results.csv)
    res.append(base.res_row("2024g-state-house-7", "Ann A", "600", "60.00", ids="RES-001", notes="county tally"))
    res.append(base.res_row("2024g-state-house-7", "Bob B", "400", "40.00", ids="RES-001", notes="county tally"))
    for cand, v, p in (("YES", "700", "70.00"), ("NO", "300", "30.00")):
        r = base.res_row("2024g-state-retention-judge-x", cand, v, p, ids="RES-001", notes="county tally")
        r["vote_for"] = ""
        res.append(r)
    fs[ED / "overall_results.csv"] = (OVCOLS, [
        ov_row("2024g-state-house-7", "Ann A", "1200", "60.00", "Y", "2000"),
        ov_row("2024g-state-house-7", "Bob B", "795", "39.75", "N", "2000", party="R"),
        # a declared write-in the state lists with no county row (overall-only line)
        ov_row("2024g-state-house-7", "Zed Z", "5", "0.25", "N", "2000", party="W"),
        ov_row("2024g-state-retention-judge-x", "YES", "70000", "70.00", "Y", "100000", vote_for="", party=""),
        ov_row("2024g-state-retention-judge-x", "NO", "30000", "30.00", "N", "100000", vote_for="", party=""),
    ])
    return fs


class CheckOverall(unittest.TestCase):
    def run_with(self, change=None):
        fs = files()
        if change:
            change(fs)
        t = base.Tree("check_results.py", fs).run()
        self.assertEqual(t.stderr, "", t.stderr)
        return [ln[len("  ERR "):] for ln in t.stdout.splitlines() if ln.startswith("  ERR ")], t

    def o(self, fs, i=0):
        return fs[ED / "overall_results.csv"][1][i]

    def rows(self, fs):
        return fs[ED / "overall_results.csv"][1]

    def assertOnly(self, errs, fragment, n=1):
        self.assertEqual(len(errs), n, errs)
        self.assertTrue(all(fragment in e for e in errs), errs)

    def assertPasses(self, change):
        errs, t = self.run_with(change)
        self.assertEqual(errs, [])
        self.assertEqual(t.code, 0)

    # baseline and file presence ------------------------------------------------------------------------------------
    def test_baseline_passes(self):
        errs, t = self.run_with()
        self.assertEqual(errs, [])
        self.assertEqual(t.code, 0)
        self.assertIn("overall rows: 5 overall contests: 2", t.stdout)

    def test_missing_file_is_an_error(self):
        def f(fs):
            fs[ED / "overall_results.csv"] = None
        errs, t = self.run_with(f)
        self.assertOnly(errs, "overall_results.csv: file missing")
        self.assertEqual(t.code, 1)

    def test_header_must_match(self):
        def f(fs):
            fs[ED / "overall_results.csv"] = (OVCOLS[:-1] + ["note"], [])
        self.assertOnly(self.run_with(f)[0], "overall_results.csv header mismatch")

    # keys --------------------------------------------------------------------------------------------------------
    def test_contest_must_exist_in_results(self):
        def f(fs):
            for r in self.rows(fs)[3:]:
                r["contest_id"] = "2024g-state-retention-judge-y"
        errs = self.run_with(f)[0]
        self.assertEqual(len(errs), 2, errs)
        self.assertTrue(all("contest_id not in results.csv" in e for e in errs), errs)

    def test_candidate_unique_per_contest(self):
        # Bob B's row renamed to Zed Z: two Zed Z rows (Zed has no county row, so only the key rule fires)
        self.assertOnly(self.run_with(lambda fs: self.o(fs, 1).update(candidate="Zed Z", party="W"))[0],
                        "duplicate contest_id + candidate")

    def test_overall_only_candidate_is_allowed(self):
        # baseline row "Zed Z" has no results.csv row; also an overall row for a candidate whose county row exists
        self.assertPasses(lambda fs: self.o(fs, 2).update(candidate="Zed Zebra"))

    # numbers -----------------------------------------------------------------------------------------------------
    def test_votes_must_be_whole_numbers(self):
        for bad in ("", "1,200", "1200.0", "n/a"):
            def f(fs, bad=bad):
                self.o(fs, 0)["overall_votes"] = bad
                self.o(fs, 0)["overall_pct"] = ""
                self.o(fs, 0)["derived"] = "overall_winner;overall_total_votes"
            self.assertOnly(self.run_with(f)[0], "overall_votes", 1)

    def test_total_must_be_a_whole_number(self):
        def f(fs):
            for r in self.rows(fs)[:3]:
                r["overall_total_votes"] = "2,000"
                r["overall_pct"] = ""
                r["derived"] = "overall_winner;overall_total_votes"
        errs = self.run_with(f)[0]
        self.assertEqual(len(errs), 3, errs)
        self.assertTrue(all("overall_total_votes '2,000' is not a whole number" in e for e in errs), errs)

    def test_pct_must_recompute(self):
        self.assertOnly(self.run_with(lambda fs: self.o(fs, 0).update(overall_pct="61.00"))[0],
                        "overall_pct 61.00 does not recompute")

    def test_pct_within_rounding_passes(self):
        # 1000 of 3000 = 33.333...: 33.33 is the rounded value; 2000 of 3000 = 66.666...: 66.67
        def f(fs):
            rs = self.rows(fs)
            rs[3].update(overall_votes="2000", overall_pct="66.67", overall_total_votes="3000")
            rs[4].update(overall_votes="1000", overall_pct="33.33", overall_total_votes="3000")
        self.assertPasses(f)

    def test_pct_off_by_more_than_rounding_fails(self):
        def f(fs):
            rs = self.rows(fs)
            rs[3].update(overall_votes="2000", overall_pct="66.66", overall_total_votes="3000")
            rs[4].update(overall_votes="1000", overall_pct="33.33", overall_total_votes="3000")
        self.assertOnly(self.run_with(f)[0], "overall_pct 66.66 does not recompute")

    def test_blank_pct_is_allowed_when_not_listed_as_derived(self):
        def f(fs):
            for r in self.rows(fs)[:3]:
                r["overall_pct"] = ""
                r["derived"] = "overall_winner;overall_total_votes"
        self.assertPasses(f)

    def test_one_total_per_contest(self):
        def f(fs):
            self.o(fs, 2).update(overall_total_votes="2001", overall_pct="")
            self.o(fs, 2)["derived"] = "overall_winner;overall_total_votes"
        self.assertOnly(self.run_with(f)[0], "several overall_total_votes")

    def test_rows_may_not_sum_above_the_total(self):
        def f(fs):
            self.o(fs, 2).update(overall_votes="50", overall_pct="2.50")
        self.assertOnly(self.run_with(f)[0], "rows sum to more than overall_total_votes")

    # derived -----------------------------------------------------------------------------------------------------
    def test_derived_vocabulary(self):
        self.assertOnly(self.run_with(lambda fs: self.o(fs, 0).update(derived=DER + ";overall_votes"))[0],
                        "derived lists 'overall_votes'")

    def test_derived_field_must_be_filled(self):
        self.assertOnly(self.run_with(lambda fs: self.o(fs, 0).update(overall_pct=""))[0],
                        "derived lists overall_pct but it is blank")

    # winners and vote_for ----------------------------------------------------------------------------------------
    def test_too_many_winners(self):
        self.assertOnly(self.run_with(lambda fs: self.o(fs, 1).update(overall_winner="Y"))[0],
                        "2 winners but 1 seats")

    def test_no_winner_needs_a_note(self):
        self.assertOnly(self.run_with(lambda fs: self.o(fs, 0).update(overall_winner="N"))[0],
                        "0 winners for 1 seats")

    def test_fewer_winners_with_a_note_passes(self):
        def f(fs):
            self.o(fs, 0).update(overall_winner="")
            self.o(fs, 0)["derived"] = "overall_pct;overall_total_votes"
            self.o(fs, 0)["notes"] = NOTE + " Fewer winners than seats: the state lists no winner."
        self.assertPasses(f)

    def test_fewer_rows_than_seats_needs_no_note(self):
        def f(fs):
            fs[ED / "results.csv"][1][-4]["vote_for"] = "3"   # Ann A
            fs[ED / "results.csv"][1][-3]["vote_for"] = "3"   # Bob B
            for r in self.rows(fs)[:3]:
                r["vote_for"] = "3"
                r["overall_winner"] = "Y"
        self.assertPasses(f)

    def test_winner_must_have_the_most_votes(self):
        def f(fs):
            self.o(fs, 0)["overall_winner"] = "N"
            self.o(fs, 1)["overall_winner"] = "Y"
        self.assertOnly(self.run_with(f)[0], "a winner has fewer votes than a non-winner")

    def test_yes_no_contest_with_blank_vote_for_has_one_winner(self):
        self.assertOnly(self.run_with(lambda fs: self.o(fs, 4).update(overall_winner="Y"))[0],
                        "2 winners but 1 seats")

    def test_vote_for_must_equal_results(self):
        def f(fs):
            for r in self.rows(fs)[:3]:
                r["vote_for"] = "2"
        errs = self.run_with(f)[0]
        # three rows differ from results.csv; with 2 seats the single winner also needs a note
        self.assertEqual(len(errs), 4, errs)
        self.assertEqual(sum("vote_for '2' differs from results.csv '1'" in e for e in errs), 3, errs)
        self.assertTrue(any("1 winners for 2 seats" in e for e in errs), errs)

    # vocabulary, sources ------------------------------------------------------------------------------------------
    def test_vocabulary(self):
        cases = [("status", "certified", "status 'certified'"), ("confidence", "sure", "confidence 'sure'"),
                 ("party", "Democratic", "party 'Democratic'"), ("overall_winner", "yes", "overall_winner 'yes'")]
        for col, val, frag in cases:
            errs = self.run_with(lambda fs, col=col, val=val: self.o(fs, 0).update({col: val}))[0]
            # a bad winner value also leaves the contest with no winner
            self.assertTrue(any(frag in e for e in errs), (col, errs))
            self.assertEqual(len(errs), 2 if col == "overall_winner" else 1, errs)

    def test_sources_must_resolve(self):
        self.assertOnly(self.run_with(lambda fs: self.o(fs, 0).update(source_ids="RES-001;RES-999"))[0],
                        "unknown source RES-999")
        self.assertOnly(self.run_with(lambda fs: self.o(fs, 0).update(source_ids=""))[0], "no source_ids")

    def test_sources_from_other_files_resolve(self):
        self.assertPasses(lambda fs: self.o(fs, 0).update(source_ids="RES-001;GOV-044;IND-031"))

    # 2026 general --------------------------------------------------------------------------------------------------
    def tre(self, fs, status):
        # base fixture: 2026g-state-treasurer county rows Cy C 70 / Di D 30 (unofficial)
        fs[ED / "overall_results.csv"][1].extend([
            ov_row("2026g-state-treasurer", "Cy C", "700", "70.00", "Y", "1000", status=status,
                   notes="Unofficial state figure."),
            ov_row("2026g-state-treasurer", "Di D", "300", "30.00", "N", "1000", status=status,
                   notes="Unofficial state figure.")])

    def test_no_2026g_row_may_be_official(self):
        errs = self.run_with(lambda fs: self.tre(fs, "official"))[0]
        self.assertEqual(len(errs), 2, errs)
        self.assertTrue(all("no 2026g overall row may be official" in e for e in errs), errs)

    def test_unofficial_2026g_row_passes(self):
        self.assertPasses(lambda fs: self.tre(fs, "unofficial"))

    # county vs overall ------------------------------------------------------------------------------------------------
    def test_overall_below_county_fails(self):
        def f(fs):
            rs = self.rows(fs)
            rs[0].update(overall_votes="590", overall_pct="74.68", overall_total_votes="790")
            rs[1].update(overall_votes="195", overall_pct="24.68", overall_total_votes="790")
            rs[2].update(overall_votes="5", overall_pct="0.63", overall_total_votes="790")
        errs = self.run_with(f)[0]
        self.assertEqual(len(errs), 2, errs)
        self.assertTrue(all("< county votes" in e for e in errs), errs)

    def test_overall_below_county_with_explained_note_passes(self):
        def f(fs):
            self.o(fs, 3).update(overall_votes="699", overall_pct="69.90", overall_total_votes="1000")
            self.o(fs, 4).update(overall_votes="301", overall_pct="30.10", overall_total_votes="1000")
            self.o(fs, 3)["notes"] = NOTE + " County figure exceeds the overall: the county canvass prints 700."
        self.assertPasses(f)

    def test_overall_equal_to_county_passes(self):
        def f(fs):
            self.o(fs, 3).update(overall_votes="700", overall_pct="70.00", overall_total_votes="1000")
            self.o(fs, 4).update(overall_votes="300", overall_pct="30.00", overall_total_votes="1000")
        self.assertPasses(f)

    # wording ----------------------------------------------------------------------------------------------------------
    def test_never_certified(self):
        self.assertOnly(self.run_with(lambda fs: self.o(fs, 0).update(notes="Certified statewide totals."))[0],
                        'says "certified"')

    def test_non_neutral_wording(self):
        self.assertOnly(self.run_with(lambda fs: self.o(fs, 0).update(electorate="a safe district"))[0],
                        "non-neutral wording")


if __name__ == "__main__":
    unittest.main()
