"""tools/check_results.py, check_gov.py and check_money.py: the rules added or changed for gap-fill round 2
(2026-11-18, planning/gapfill/merge/checker-changes.md).

Each test builds a small data tree in a temporary folder (data/editions/st-joseph/, data/indiana/), copies the real
checker into <tmp>/tools/ (every checker finds its data relative to its own file) and runs it end to end. A baseline
fixture passes with 0 errors; each case changes one thing and expects exactly the error the rule names, or still 0.

check_results: 2026g rows and the 2026g election row may be official only when they cite the official county canvass
(RES-048); an unofficial 2026g row must name the canvass and say why; source ids may come from any sources file (the 8
pre-existing false errors: ELX-008, GOV-044, IND-031); ballot_questions.csv keys, foreign keys, vocabulary, sources,
neutral wording.
check_gov: a 2027+ term may be official only when it cites RES-048; unit_contacts.csv and
appointed_board_members.csv keys, foreign keys, dates, vacant seats, single contact URL; personal-mailbox privacy rule;
the new files' source ids count as used.
check_money: no duplicate (unit, year, debt_type); totals = sum of classes; class rows need a total; whole-corporation
phrase; never-sum note.
Run:  python -P -E -m unittest discover -s tools/tests -p test_checkers_gapfill2.py
"""
from __future__ import annotations

import csv
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ED = Path("data") / "editions" / "st-joseph"
IND = Path("data") / "indiana"
SRC_HDR = ["id", "url", "title", "publisher", "accessed", "kind", "notes"]


def src(i):
    return {"id": i, "url": "https://example.gov/" + i, "title": i, "publisher": "p", "accessed": "2026-11-18",
            "kind": "primary", "notes": ""}


class Tree:
    """A temporary root with tools/<checker> and a data tree; files are {relative path: (header, rows)}."""

    def __init__(self, checker: str, files: dict):
        self.checker = checker
        self.files = files

    def run(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "tools").mkdir()
            shutil.copyfile(ROOT / "tools" / self.checker, root / "tools" / self.checker)
            (root / IND).mkdir(parents=True)
            (root / ED).mkdir(parents=True)
            for rel, spec in self.files.items():
                if spec is None:
                    continue
                hdr, rows = spec
                p = root / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                with open(p, "w", encoding="utf-8", newline="") as f:
                    w = csv.writer(f, lineterminator="\n")
                    w.writerow(hdr)
                    for r in rows:
                        w.writerow([r.get(h, "") for h in hdr])
            r = subprocess.run([sys.executable, "-I", str(root / "tools" / self.checker)], capture_output=True,
                               text=True, encoding="utf-8", cwd=root)
            self.stdout, self.stderr, self.code = r.stdout, r.stderr, r.returncode
            return self


# ===================================================================================================== check_results
RCOLS = ["election_id", "contest_id", "office_id", "contest_label", "district", "party_primary", "candidate", "party",
         "votes", "pct", "winner", "vote_for", "status", "confidence", "source_ids", "notes"]
ECOLS = ["election_id", "date", "type", "scope", "registered", "ballots_cast", "turnout_pct", "straight_party_d",
         "straight_party_r", "straight_party_other", "status", "source_doc", "source_ids", "notes"]
BCOLS = ["contest_id", "wording", "wording_kind", "status", "source_ids", "notes"]
OVCOLS = ["contest_id", "candidate", "candidate_in_source", "party", "overall_votes", "overall_pct", "overall_winner",
          "overall_total_votes", "derived", "electorate", "vote_for", "status", "confidence", "source_ids", "notes"]
CANV ="Official county canvass of 11/13/2026 (two independent readings agree)"
STATE = "County figures from the official county canvass of 11/13/2026; contest result awaits state certification"


def res_row(cid, cand, votes, pct, status="official", ids="RES-048", notes=CANV, winner=""):
    return {"election_id": cid.split("-")[0], "contest_id": cid, "contest_label": cid, "candidate": cand,
            "party": "" if cand in ("YES", "NO") else "D", "votes": votes, "pct": pct, "winner": winner,
            "vote_for": "1", "status": status, "confidence": "high", "source_ids": ids, "notes": notes}


def results_files():
    return {
        ED / "sources_results.csv": (SRC_HDR, [src("RES-001"), src("RES-048")]),
        ED / "sources_elections.csv": (SRC_HDR, [src("ELX-001"), src("ELX-008")]),
        ED / "sources_gov.csv": (SRC_HDR, [src("GOV-044")]),
        IND / "sources_indiana.csv": (SRC_HDR, [src("IND-031")]),
        ED / "elections.csv": (ECOLS, [
            {"election_id": "2026g", "date": "2026-11-03", "type": "general", "scope": "countywide",
             "registered": "1000", "ballots_cast": "400", "turnout_pct": "40.00", "status": "official",
             "source_ids": "RES-048", "notes": "Official Results dated 11/13/2026"},
            {"election_id": "2024g", "date": "2024-11-05", "type": "general", "scope": "countywide",
             "status": "official", "source_ids": "RES-001", "notes": "canvass"}]),
        ED / "results.csv": (RCOLS, [
            res_row("2026g-county-sheriff", "Ann A", "60", "60.00", winner="Y"),
            res_row("2026g-county-sheriff", "Bob B", "40", "40.00", winner="N"),
            res_row("2026g-state-treasurer", "Cy C", "70", "70.00", "unofficial", notes=STATE),
            res_row("2026g-state-treasurer", "Di D", "30", "30.00", "unofficial", notes=STATE),
            res_row("2026g-county-public-question-1", "YES", "55", "55.00"),
            res_row("2026g-county-public-question-1", "NO", "45", "45.00"),
            res_row("2024g-county-clerk", "Ed E", "100", "100.00", ids="RES-001", notes="canvass")]),
        ED / "ballot_questions.csv": (BCOLS, [
            {"contest_id": "2026g-county-public-question-1", "wording": "Shall the county do this?",
             "wording_kind": "sample_ballot", "status": "official", "source_ids": "ELX-001", "notes": ""}]),
        # required since the second 2026-11-18 merge (rules tested in test_checkers_overall.py); empty here
        ED / "overall_results.csv": (OVCOLS, []),
    }


class CheckResults(unittest.TestCase):
    def run_with(self, change=None):
        files = results_files()
        if change:
            change(files)
        t = Tree("check_results.py", files).run()
        self.assertEqual(t.stderr, "", t.stderr)
        return [ln[len("  ERR "):] for ln in t.stdout.splitlines() if ln.startswith("  ERR ")], t

    def rows(self, files, rel="results.csv"):
        return files[ED / rel][1]

    def assertOnly(self, errs, fragment, n=1):
        self.assertEqual(len(errs), n, errs)
        self.assertTrue(all(fragment in e for e in errs), errs)

    def test_baseline_passes(self):
        errs, t = self.run_with()
        self.assertEqual(errs, [])
        self.assertEqual(t.code, 0)

    # 2026g result rows ------------------------------------------------------------------------------------------
    def test_official_2026g_row_must_cite_the_canvass(self):
        def f(files):
            self.rows(files)[0]["source_ids"] = "RES-001"
        errs, t = self.run_with(f)
        self.assertOnly(errs, "2026g official row does not cite the official county canvass (RES-048)")
        self.assertEqual(t.code, 1)

    def test_official_2026g_row_may_cite_the_canvass_with_other_sources(self):
        def f(files):
            self.rows(files)[0]["source_ids"] = "RES-001;RES-048"
        self.assertEqual(self.run_with(f)[0], [])

    def test_unofficial_2026g_row_must_name_the_canvass(self):
        def f(files):
            self.rows(files)[2]["notes"] = "Unofficial as of 2026-11-03 21:07 EST; awaits state certification"
        self.assertOnly(self.run_with(f)[0], "does not name the official county canvass")

    def test_unofficial_2026g_row_must_say_why(self):
        def f(files):
            self.rows(files)[2]["notes"] = "County figures from the official county canvass of 11/13/2026"
        self.assertOnly(self.run_with(f)[0], "does not say why it is unofficial")

    def test_each_unofficial_reason_is_accepted(self):
        for reason in ("contest result awaits state certification", "re-check for recount petitions",
                       "the school corporation also votes in another county",
                       "status kept unofficial until the court is confirmed"):
            def f(files, reason=reason):
                self.rows(files)[2]["notes"] = "County figures from the official county canvass of 11/13/2026; " + reason
            self.assertEqual(self.run_with(f)[0], [], reason)

    def test_other_2026g_statuses_still_fail(self):
        def f(files):
            self.rows(files)[0]["status"] = "secondary"
        self.assertOnly(self.run_with(f)[0], "2026g row status secondary")

    def test_rules_do_not_touch_other_elections(self):
        def f(files):
            self.rows(files)[6]["status"] = "unofficial"
            self.rows(files)[6]["notes"] = "Unofficial as of election night"
        self.assertEqual(self.run_with(f)[0], [])

    # 2026g election row ------------------------------------------------------------------------------------------
    def test_official_2026g_election_must_cite_the_canvass(self):
        def f(files):
            files[ED / "elections.csv"][1][0]["source_ids"] = "RES-001"
        self.assertOnly(self.run_with(f)[0], "2026g is official but does not cite the official county canvass")

    def test_unofficial_2026g_election_still_allowed(self):
        def f(files):
            e = files[ED / "elections.csv"][1][0]
            e["status"], e["notes"] = "unofficial", "Unofficial as of 2026-11-03"
        self.assertEqual(self.run_with(f)[0], [])

    # source ids across sources files (the 8 pre-existing errors) --------------------------------------------------
    def test_ids_from_other_sources_files_are_accepted(self):
        def f(files):
            self.rows(files)[6]["source_ids"] = "RES-001;GOV-044"
            self.rows(files)[0]["source_ids"] = "RES-048;IND-031"
            files[ED / "elections.csv"][1][1]["source_ids"] = "RES-001;ELX-008"
        self.assertEqual(self.run_with(f)[0], [])

    def test_unknown_ids_still_fail(self):
        def f(files):
            self.rows(files)[6]["source_ids"] = "RES-001;GOV-999"
            files[ED / "elections.csv"][1][1]["source_ids"] = "ELX-999"
        errs = self.run_with(f)[0]
        self.assertEqual(len(errs), 2, errs)
        self.assertTrue(any("unknown source GOV-999" in e for e in errs), errs)
        self.assertTrue(any("unknown source ELX-999" in e for e in errs), errs)

    # ballot_questions.csv -----------------------------------------------------------------------------------------
    def q(self, files):
        return files[ED / "ballot_questions.csv"][1][0]

    def test_ballot_question_rules(self):
        cases = [
            (lambda fs: fs[ED / "ballot_questions.csv"][1].append(dict(self.q(fs))), "duplicate contest_id"),
            (lambda fs: self.q(fs).update(contest_id="2026g-county-public-question-9"), "unknown contest_id"),
            (lambda fs: self.q(fs).update(contest_id="2026g-county-sheriff"), "not a YES/NO question"),
            (lambda fs: self.q(fs).update(wording="  "), "blank wording"),
            (lambda fs: self.q(fs).update(wording_kind="guess"), "wording_kind"),
            (lambda fs: self.q(fs).update(status="final"), "status"),
            (lambda fs: self.q(fs).update(source_ids=""), "no source_ids"),
            (lambda fs: self.q(fs).update(source_ids="ELX-404"), "unknown source ELX-404"),
            (lambda fs: self.q(fs).update(notes="a landslide"), "non-neutral wording"),
        ]
        for change, frag in cases:
            self.assertOnly(self.run_with(change)[0], frag)

    def test_ballot_question_may_cite_results_sources(self):
        self.assertEqual(self.run_with(lambda fs: self.q(fs).update(source_ids="RES-048;ELX-001"))[0], [])

    def test_missing_ballot_questions_file_is_an_error(self):
        def f(files):
            files[ED / "ballot_questions.csv"] = None
        self.assertOnly(self.run_with(f)[0], "ballot_questions.csv: file missing")


# ======================================================================================================== check_gov
UCOLS = "unit_id,unit_type,name,parent_unit_ids,places_covered,website,status,source_ids,notes".split(",")
OCOLS = ("office_id,unit_id,office_type,title,district,seats,elected,partisan,term_years,next_election,status,"
         "source_ids,notes").split(",")
TCOLS = ("term_id,office_id,person,party,start,end,selected_by,first_selected_by,status,confidence,source_ids,"
         "notes").split(",")
BDCOLS = "board_id,unit_id,name,what_it_decides,seats,appointing_authorities,levies_tax,status,source_ids,notes".split(",")
CCOLS = ("gov_id,body,phone,office_address,contact_url,website,meeting_rule,meeting_place,meeting_info_url,"
         "schedule_year,as_of,status,confidence,source_ids,notes").split(",")
MCOLS = ("member_id,board_id,person,role,appointed_by,term_start,term_end,holdover,as_of,status,confidence,source_ids,"
         "notes").split(",")


def gov_files():
    mayors = [{"term_id": f"south-bend-mayor__m{i}", "office_id": "south-bend-mayor", "person": f"Mayor {i}",
               "party": "D", "start": f"{1800 + 4 * i}-01-01", "end": f"{1804 + 4 * i}-01-01",
               "selected_by": "election", "first_selected_by": "election", "status": "official",
               "confidence": "high", "source_ids": "GOV-001"} for i in range(33)]
    council = {"term_id": "county-council__new__2027-01", "office_id": "county-council", "person": "New Member",
               "party": "R", "start": "2027-01-01", "end": "", "selected_by": "election",
               "first_selected_by": "election", "status": "official", "confidence": "high",
               "source_ids": "RES-048", "notes": "Official: county canvass of 11/13/2026 (RES-048)."}
    return {
        ED / "units.csv": (UCOLS, [
            {"unit_id": "county", "unit_type": "county", "name": "County", "status": "official", "source_ids": "GOV-001"},
            {"unit_id": "south-bend", "unit_type": "city", "name": "South Bend", "status": "official",
             "source_ids": "GOV-001"}]),
        ED / "offices.csv": (OCOLS, [
            {"office_id": "south-bend-mayor", "unit_id": "south-bend", "office_type": "mayor", "title": "Mayor",
             "seats": "1", "status": "official", "source_ids": "GOV-001"},
            {"office_id": "county-council", "unit_id": "county", "office_type": "council", "title": "Council",
             "seats": "9", "status": "official", "source_ids": "GOV-001"}]),
        ED / "terms.csv": (TCOLS, mayors + [council]),
        ED / "appointed_boards.csv": (BDCOLS, [
            {"board_id": "sb-board", "unit_id": "south-bend", "name": "Board", "status": "official",
             "source_ids": "GOV-001"}]),
        ED / "sources_gov.csv": (SRC_HDR, [src("GOV-001"), src("GOV-002"), src("GOV-003")]),
        ED / "gaps_gov.csv": (["area", "item", "why_missing", "how_to_fill"], []),
        ED / "sources_results.csv": (SRC_HDR, [src("RES-048")]),
        IND / "sources_indiana.csv": (SRC_HDR, []),
        ED / "derived" / "unit_id_aliases.csv": (["alias_id", "unit_id", "notes"], [
            {"alias_id": "library-x", "unit_id": ""}, {"alias_id": "city-south-bend", "unit_id": "south-bend"}]),
        ED / "unit_contacts.csv": (CCOLS, [
            {"gov_id": "south-bend", "body": "Common Council", "phone": "574-555-0100",
             "contact_url": "mailto:council@city.gov", "website": "https://city.gov", "schedule_year": "2026",
             "as_of": "2026-11-18", "status": "official", "confidence": "high", "source_ids": "GOV-002"},
            {"gov_id": "library-x", "body": "Board", "as_of": "2026-11-18", "status": "official",
             "confidence": "medium", "source_ids": "GOV-002"}]),
        ED / "appointed_board_members.csv": (MCOLS, [
            {"member_id": "sb-board__ann-a", "board_id": "sb-board", "person": "Ann A", "role": "Member",
             "appointed_by": "Mayor", "term_start": "2026-01-01", "term_end": "2026-12-31", "as_of": "2026-11-10",
             "status": "official", "confidence": "high", "source_ids": "GOV-003"},
            {"member_id": "sb-board__vacant-1", "board_id": "sb-board", "person": "", "role": "Member",
             "as_of": "2026-11-18", "status": "official", "confidence": "high", "source_ids": "GOV-003",
             "notes": "Vacant seat (listed as Vacant on the board page)."}]),
    }


class CheckGov(unittest.TestCase):
    def run_with(self, change=None):
        files = gov_files()
        if change:
            change(files)
        t = Tree("check_gov.py", files).run()
        self.assertEqual(t.stderr, "", t.stderr)
        errs = [ln[len("ERROR: "):] for ln in t.stdout.splitlines() if ln.startswith("ERROR: ")]
        warns = [ln for ln in t.stdout.splitlines() if ln.startswith("WARN: ")]
        return errs, warns, t

    def rows(self, files, name):
        return files[ED / name][1]

    def assertOnly(self, errs, fragment):
        self.assertEqual(len(errs), 1, errs)
        self.assertIn(fragment, errs[0])

    def test_baseline_passes_and_new_files_count_their_sources_as_used(self):
        errs, warns, t = self.run_with()
        self.assertEqual(errs, [])
        self.assertEqual(t.code, 0)
        self.assertFalse([w for w in warns if "GOV-002" in w or "GOV-003" in w], warns)

    # 2027+ terms ------------------------------------------------------------------------------------------------------
    def council(self, files):
        return self.rows(files, "terms.csv")[-1]

    def test_official_2027_term_must_cite_the_canvass(self):
        errs = self.run_with(lambda fs: self.council(fs).update(source_ids="GOV-001"))[0]
        self.assertOnly(errs, "official only on the official county canvass, RES-048")

    def test_2027_term_other_than_official_or_unofficial_fails_even_with_the_canvass(self):
        errs = self.run_with(lambda fs: self.council(fs).update(status="secondary"))[0]
        self.assertOnly(errs, "starts 2027-01-01 but status is secondary")

    def test_unofficial_2027_term_still_passes(self):
        errs = self.run_with(lambda fs: self.council(fs).update(status="unofficial", notes="Unofficial: x"))[0]
        self.assertEqual(errs, [])

    # unit_contacts.csv ------------------------------------------------------------------------------------------------
    def c(self, files, i=0):
        return self.rows(files, "unit_contacts.csv")[i]

    def test_contact_rules(self):
        cases = [
            (lambda fs: self.c(fs, 1).update(gov_id="south-bend", body="Common Council"), "duplicate (gov_id, body)"),
            (lambda fs: self.c(fs).update(gov_id="nowhere"), "unknown gov_id"),
            (lambda fs: self.c(fs).update(confidence="certain"), "bad confidence"),
            (lambda fs: self.c(fs).update(as_of="Nov 18"), "bad as_of"),
            (lambda fs: self.c(fs).update(as_of=""), "bad as_of"),
            (lambda fs: self.c(fs).update(schedule_year="current page"), "bad schedule_year"),
            (lambda fs: self.c(fs).update(contact_url="https://a.gov/; council email x@a.gov"), "not one URL"),
            (lambda fs: self.c(fs).update(contact_url="mailto:clerk@gmail.com"), "personal e-mail address"),
            (lambda fs: self.c(fs).update(notes="write to trustee@Yahoo.com"), "personal e-mail address"),
            (lambda fs: self.c(fs).update(source_ids="GOV-404"), "unknown source id GOV-404"),
            (lambda fs: self.c(fs).update(source_ids=""), "missing source_ids"),
            (lambda fs: self.c(fs).update(status="final"), "bad status"),
        ]
        for change, frag in cases:
            self.assertOnly(self.run_with(change)[0], frag)

    def test_contact_values_that_pass(self):
        for change in (lambda fs: self.c(fs).update(schedule_year="2026-2027"),
                       lambda fs: self.c(fs).update(schedule_year=""),
                       lambda fs: self.c(fs).update(contact_url="https://city.gov/contact"),
                       lambda fs: self.c(fs).update(gov_id="city-south-bend"),       # alias id
                       lambda fs: self.c(fs).update(source_ids="GOV-002;RES-048")):  # other sources file
            self.assertEqual(self.run_with(change)[0], [])

    def test_missing_new_file_is_an_error(self):
        def f(files):
            files[ED / "unit_contacts.csv"] = None
        self.assertOnly(self.run_with(f)[0], "unit_contacts.csv: file missing")

    # appointed_board_members.csv --------------------------------------------------------------------------------------
    def m(self, files, i=0):
        return self.rows(files, "appointed_board_members.csv")[i]

    def test_member_rules(self):
        cases = [
            (lambda fs: self.m(fs, 1).update(member_id="sb-board__ann-a"), "duplicate member_id"),
            (lambda fs: self.m(fs).update(board_id="no-board", member_id="no-board__ann-a"), "unknown board_id"),
            (lambda fs: self.m(fs).update(member_id="other__ann-a"), "does not start with its board_id"),
            (lambda fs: self.m(fs).update(confidence="sure"), "bad confidence"),
            (lambda fs: self.m(fs).update(holdover="no"), "bad holdover"),
            (lambda fs: self.m(fs).update(term_end="12/31/2026"), "bad term_end"),
            (lambda fs: self.m(fs).update(as_of=""), "blank as_of"),
            (lambda fs: self.m(fs).update(term_start="2027-01-01"), "term_end before term_start"),
            (lambda fs: self.m(fs, 1).update(notes=""), "blank person without a vacant-seat note"),
            (lambda fs: self.m(fs).update(notes="home: a@hotmail.com"), "personal e-mail address"),
            (lambda fs: self.m(fs).update(source_ids="GOV-404"), "unknown source id GOV-404"),
        ]
        for change, frag in cases:
            self.assertOnly(self.run_with(change)[0], frag)

    def test_member_values_that_pass(self):
        for change in (lambda fs: self.m(fs).update(holdover="yes"),
                       lambda fs: self.m(fs).update(term_start="", term_end="", notes="Term: indefinite."),
                       lambda fs: self.m(fs).update(term_end="2026-12"),
                       lambda fs: self.m(fs).update(term_end="2029")):
            self.assertEqual(self.run_with(change)[0], [])

    def test_privacy_rule_covers_the_older_gov_files(self):
        errs = self.run_with(lambda fs: self.rows(fs, "units.csv")[0].update(notes="clerk: x@sbcglobal.net"))[0]
        self.assertOnly(errs, "units.csv: personal e-mail address")
        errs = self.run_with(lambda fs: self.rows(fs, "units.csv")[0].update(notes="office: clerk@county.gov"))[0]
        self.assertEqual(errs, [])


# ====================================================================================================== check_money
MONEY_HDRS = {
    "budgets.csv": "unit_id,year,basis,amount,adopted_or_actual,series_id,status,source_ids,notes",
    "budget_breakdowns.csv": "unit_id,year,kind,category,amount,basis,status,source_ids,notes",
    "tax_rates.csv": "unit_id,taxing_district,year,rate_per_100,rate_kind,status,source_ids,notes",
    "debt.csv": "unit_id,year,debt_type,amount,status,source_ids,notes",
    "cf_state.csv": ("committee,candidate,office,district,party,year,receipts,expenditures,cash_end,top_funder_types,"
                     "status,source_ids,notes"),
    "sources_money.csv": "id,url,title,publisher,accessed,kind,notes",
    "gaps_money.csv": "area,item,why_missing,how_to_fill",
}
CLS = "End-of-year principal outstanding: "
TOT = "Total end-of-year principal outstanding (all debt)"
NEVER = "Same bonds reported by both; never add the two totals."
WHOLE = "Whole corporation (principal county: LaPorte, Gateway county 46)."


def debt(unit, year, kind, amount, notes=""):
    return {"unit_id": unit, "year": year, "debt_type": kind, "amount": amount, "status": "official",
            "source_ids": "MON-001", "notes": notes}


def money_files():
    rows = {n: [] for n in MONEY_HDRS}
    rows["sources_money.csv"] = [src("MON-001")]
    rows["budgets.csv"] = [
        {"unit_id": "school-new-prairie", "year": str(y), "basis": "gateway_reported_funds", "amount": a,
         "adopted_or_actual": "adopted", "series_id": "school-new-prairie-gateway-advertised-funds",
         "status": "official", "source_ids": "MON-001", "notes": WHOLE + " Gateway budget."}
        for y, a in ((2025, "1000000"), (2026, "1100000"))]
    rows["debt.csv"] = [
        debt("city-x", "2024", CLS + "Bonds (City X)", "300.50"),
        debt("city-x", "2024", CLS + "Leases (City X)", "200"),
        debt("city-x", "2024", TOT, "500.50"),
        debt("county-st-joseph", "2024", CLS + "Revenue Bonds", "50000000"),
        debt("county-st-joseph", "2024", TOT, "50000000", NEVER),
        debt("special-redevelopment-authority", "2025", CLS + "General Obligation Bonds", "50000000"),
        debt("special-redevelopment-authority", "2025", TOT, "50000000", NEVER),
        debt("school-new-prairie", "2024", CLS + "Bonds", "10"),
        debt("school-new-prairie", "2024", TOT, "10", WHOLE),
    ]
    rows["debt.csv"][7]["notes"] = WHOLE
    return {ED / n: (MONEY_HDRS[n].split(","), rows[n]) for n in MONEY_HDRS}


class CheckMoney(unittest.TestCase):
    def run_with(self, change=None):
        files = money_files()
        if change:
            change(files)
        t = Tree("check_money.py", files).run()
        self.assertEqual(t.stderr, "", t.stderr)
        lines = t.stdout.splitlines()
        i = next((k for k, ln in enumerate(lines) if ln.startswith("FAILED:")), None)
        return ([ln.strip() for ln in lines[i + 1:]] if i is not None else []), t

    def d(self, files):
        return files[ED / "debt.csv"][1]

    def assertOnly(self, errs, fragment):
        self.assertEqual(len(errs), 1, errs)
        self.assertIn(fragment, errs[0])

    def test_baseline_passes(self):
        errs, t = self.run_with()
        self.assertEqual(errs, [])
        self.assertEqual(t.code, 0)

    def test_duplicate_debt_row_fails(self):
        def f(fs):
            self.d(fs).append(dict(self.d(fs)[1]))
            self.d(fs)[2]["amount"] = "700.50"    # keep the total equal to the classes, so only the duplicate fails
        self.assertOnly(self.run_with(f)[0], "duplicate (unit, year, debt_type)")

    def test_total_must_equal_sum_of_classes(self):
        self.assertOnly(self.run_with(lambda fs: self.d(fs)[2].update(amount="500.49"))[0],
                        "total 500.49 != sum of classes 500.50")

    def test_classes_need_a_total(self):
        self.assertOnly(self.run_with(lambda fs: self.d(fs).pop(2))[0], "city-x 2024: class rows without a total row")

    def test_total_without_classes_is_allowed(self):
        # a unit that reports only a total (no class rows) is not a contradiction
        self.assertEqual(self.run_with(lambda fs: self.d(fs).append(debt("town-y", "2023", TOT, "5")))[0], [])

    def test_whole_corporation_phrase_required_in_budgets_and_debt(self):
        self.assertOnly(self.run_with(lambda fs: fs[ED / "budgets.csv"][1][0].update(notes="Gateway budget."))[0],
                        "budgets.csv line 2: school-new-prairie row without the whole-corporation phrase")
        self.assertOnly(self.run_with(lambda fs: self.d(fs)[8].update(notes=""))[0],
                        "debt.csv line 10: school-new-prairie row without the whole-corporation phrase")

    def test_whole_corporation_phrase_not_required_for_other_units(self):
        self.assertEqual(self.run_with(lambda fs: self.d(fs)[0].update(notes="no phrase"))[0], [])

    def test_never_sum_note_required_on_county_and_authority_totals(self):
        self.assertOnly(self.run_with(lambda fs: self.d(fs)[4].update(notes=""))[0],
                        "county-st-joseph 2024 total without the never-sum note")
        self.assertOnly(self.run_with(lambda fs: self.d(fs)[6].update(notes=""))[0],
                        "special-redevelopment-authority 2025 total without the never-sum note")

    def test_never_sum_note_not_required_in_other_years(self):
        def f(fs):
            self.d(fs).extend([debt("county-st-joseph", "2023", CLS + "Revenue Bonds", "7"),
                               debt("county-st-joseph", "2023", TOT, "7")])
        self.assertEqual(self.run_with(f)[0], [])


if __name__ == "__main__":
    unittest.main()
