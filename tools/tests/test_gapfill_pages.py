"""Gap-fill round 2 pages (2026-11-18, planning/gapfill/PAGES-BRIEF.md): the site shows the merged data.

- Unclassified contests: a contest pages/elections.py classify() cannot place is counted in a neutral "Other contests"
  group on Compare, never a crash (the U.S. House contest crashed it with KeyError 'Other'); U.S. House and Senate
  contests are classified as federal and multi-county.
- 2026 wording follows the rows' status (civic/results_status.py): 124 of 166 lines official on the county canvass of
  Nov 13, 2026; 42 unofficial, each with its reason; no "until the county certifies" sentence is left.
- Ballot question wording comes from ballot_questions.csv.
- Contacts (unit_contacts.csv): office contacts only, the meeting rule as stored with its schedule year and "as of"
  date, a blank rule points to the body's site; a personal mailbox or a non-web link is never printed.
- Board rosters (appointed_board_members.csv): vacant and holdover marked, appointer shown, no party or contact;
  South Bend's Board of Public Safety lists 3 members and never 5 filled seats.
- Debt by year 2022-2025 (debt-2024 keeps its id), the stored never-sum and utility notes wherever those totals appear,
  no party colors; the whole-corporation note once per page for New Prairie and Union-North.
- Federal and statewide: offices and pages, Offices hub levels, the home map's State and Federal layers (the county
  outline, a label, no new geometry), and the landing count of local seats only.
- County vote beside the overall result (civic/overall.py): the winner is the overall winner and a different county
  leader is "received the most votes in St. Joseph County"; wholly-in-county, pending (2026) and missing cases; a
  vote-for-N case; 2024 question 1 "Statewide: Yes (ratified)"; margins never rank a county portion.
Run:  python -P -E -m unittest discover -s tools/tests -p test_gapfill_pages.py
"""
from __future__ import annotations

import copy
import html as htmllib
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = ROOT / "tools" / "site"
sys.path.insert(0, str(SITE_DIR))

import build  # noqa: E402
from civic import offices as om  # noqa: E402
from civic import overall as OV  # noqa: E402
from civic import results_status as RS  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site  # noqa: E402
from pages import elections as E  # noqa: E402
from pages import elections_numbers as N  # noqa: E402
from pages import gov_parts as P  # noqa: E402

PAGES = ["index.html", "offices/index.html", "about/index.html", "elections/calendar/index.html",
         "governments/county/index.html", "governments/county/money/index.html",
         "governments/south-bend/index.html", "governments/transpo/index.html",
         "governments/greene-township/index.html", "governments/mishawaka/money/index.html",
         "governments/new-prairie/money/index.html", "governments/union-north/money/index.html",
         "governments/special-redevelopment-authority/money/index.html", "money/budgets/index.html",
         "money/index.html", "offices/us-house-2/index.html", "offices/us-senate-class-1/index.html",
         "offices/state-governor/index.html", "offices/state-governor/elections/index.html",
         "elections/2016g/contests/index.html", "elections/2026g/contests/index.html",
         "elections/judges-and-questions/index.html", "elections/compare/index.html",
         "governments/john-glenn/elections/index.html"]


def text(html: str) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", html)))


class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name)
        cls.site = site = Site(cls.ed, out)
        build.discover_builders()
        for p in PAGES:
            if p not in site.pages:
                build.BUILDERS[p](site)
        site.write()
        cls._html = {p: (out / p).read_text(encoding="utf-8") for p in site.pages}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def main(self, path: str) -> str:
        h = self._html[path]
        i = h.find("<main")
        return h[i:h.index("</main>", i)] if i >= 0 else h

    def sec(self, path: str, sid: str) -> str:
        m = self.main(path)
        i = m.index(f'id="{sid}"')
        j = m.find("<section", i + 1)
        return m[i:j if j > 0 else len(m)]

    # ------------------------------------------------------------------ 2026 wording
    def test_no_hard_coded_unofficial_2026_sentence_left(self):
        for p, h in self._html.items():
            for bad in ("until the county certifies", "Results are unofficial until certified",
                        "2026 results are unofficial", "results are unofficial until certified"):
                self.assertNotIn(bad, h, f"{p}: {bad}")

    def test_split_wording_from_rows(self):
        s = RS.split(self.ed, "2026g")
        self.assertEqual((s["total"], s["official"], s["unofficial"]), (166, 124, 42))
        self.assertEqual(s["canvass"], "2026-11-13")
        self.assertEqual(sum(v["rows"] for v in s["by_reason"].values()), 42)
        self.assertEqual(s["by_reason"]["recount"]["rows"], 5)
        self.assertEqual(s["by_reason"]["other-county"]["rows"], 10)
        about = text(self.main("about/index.html"))
        self.assertIn("124 of 166 result lines are official (the official county canvass of November 13, 2026)", about)
        self.assertIn("official results as reported to the Secretary of State", about)
        cal = text(self.main("elections/calendar/index.html"))
        self.assertIn("Held on Nov 3, 2026. 124 of 166 result lines are official", cal)
        county = text(self.main("governments/county/index.html"))
        self.assertRegex(county, r"\d+ people elected on Nov 3, 2026 are shown as incoming")
        self.assertIn("official (the official county canvass of November 13, 2026)", county)

    def test_split_wording_edge_cases(self):
        ed = self.ed
        self.assertEqual(RS.summary(ed, "no-such-election"), "")
        self.assertEqual(RS.brief(ed, "no-such-election"), "")
        self.assertIsNone(RS.incoming_note(ed, []))
        self.assertTrue(RS.brief(ed, "2024g").startswith("Every result line is official"))
        self.assertEqual(RS.row_reason({"notes": "kept unofficial until the recount window closes"}), "recount")
        self.assertEqual(RS.row_reason({"notes": ""}), "other")

    def test_fronk_francisco_are_superior_court_retentions(self):
        for cid, oid in (("2026g-state-retention-christopher-c-fronk", "superior-court-judge-reagan"),
                         ("2026g-state-retention-david-l-francisco", "superior-court-judge-marnocha")):
            c = self.ed.contests[cid]
            self.assertEqual(c["office_id"], oid)
            self.assertEqual(E.classify(c), ("Superior Court retention", "St. Joseph County", False))

    # ------------------------------------------------------------------ ballot questions
    def test_question_wording_from_ballot_questions(self):
        main = self.main("elections/judges-and-questions/index.html")
        self.assertNotIn("[number not read]", main)
        self.assertIn("Article 1, Section 17", main)
        self.assertIn("Statewide: Yes (ratified)", text(main))
        wording = E.question_wordings(self.ed)
        self.assertEqual(len(wording), len(self.ed.table("ballot_questions")))

    # ------------------------------------------------------------------ contacts
    def test_contacts_rendered_with_meeting_rule_as_stored(self):
        c = self.sec("governments/county/index.html", "contact")
        row = next(r for r in self.ed.table("unit_contacts") if r["gov_id"] == "county"
                   and r["body"] == "Board of Commissioners")
        self.assertIn(row["phone"], c)
        t = text(c)
        self.assertIn("2026 schedule · as of November 18, 2026", t)
        self.assertIn(re.sub(r"\s+", " ", row["meeting_rule"]).split(" (")[0], t.replace("&amp;", "&"))
        # the county Board of Health has no page of its own: its contact sits on the county page, named
        self.assertIn("St. Joseph County Board of Health", c)

    def test_office_email_printed_never_linked(self):
        c = self.sec("governments/county/index.html", "contact")
        self.assertNotIn("mailto:", c)
        ed = copy.copy(self.ed)
        ed.tables = dict(self.ed.tables)
        ed.warnings = []
        ed.tables["unit_contacts"] = [dict(self.ed.table("unit_contacts")[0], contact_url="mailto:clerk@example.gov")]
        page = Site(ed, Path(self.tmp.name) / "mail").page("governments/county/index.html")
        out = str(P.contact_section(ed, page, ed.units["county"]))
        self.assertIn("Office email", out)
        self.assertIn("clerk@example.gov", out)
        self.assertNotIn('href="mailto:', out)

    def test_blank_meeting_rule_points_to_the_site(self):
        c = text(self.sec("governments/greene-township/index.html", "contact"))
        self.assertIn("No stated meeting rule in the guide's data; the schedule is on the body's site", c)
        self.assertNotIn("Office phone", c)   # the owner chose not to publish Greene's phone

    def test_contacts_privacy_guard(self):
        ed = copy.copy(self.ed)
        ed.tables = dict(self.ed.tables)
        ed.warnings = []
        bad = dict(self.ed.table("unit_contacts")[0], body="Test body", phone="", contact_url="mailto:someone@gmail.com")
        js = dict(self.ed.table("unit_contacts")[0], body="Script body", contact_url="javascript:alert(1)",
                  website="ftp://example.org")
        ed.tables["unit_contacts"] = [bad, js]
        site = Site(ed, Path(self.tmp.name) / "priv")
        page = site.page("governments/county/index.html")
        out = str(P.contact_section(ed, page, ed.units["county"]))
        self.assertNotIn("gmail", out)
        self.assertTrue(any("personal mailbox" in w for w in ed.warnings))
        self.assertNotIn('href="javascript:', out)
        self.assertNotIn('href="ftp:', out)
        self.assertNotIn('href="mailto:', out)
        self.assertIn("javascript:alert(1)", out)   # printed as text, never as a link

    # ------------------------------------------------------------------ board rosters
    def test_board_of_public_safety_lists_three_never_five(self):
        m = self.main("governments/south-bend/index.html")
        i = m.index('id="roster-south-bend-board-public-safety"')
        fold = m[i:m.index("</details>", i)]
        self.assertEqual(len(re.findall(r'<li class="gov-member"', fold)), 3)
        self.assertIn("3 members listed", fold)
        self.assertNotRegex(text(fold), r"\b5 (members|filled)")
        self.assertIn("appointed by Mayor of South Bend", fold)

    def test_roster_vacant_holdover_and_no_contact(self):
        county = self.main("governments/county/index.html")
        i = county.index('id="roster-sjc-board-of-health"')
        fold = county[i:county.index("</details>", i)]
        self.assertEqual(fold.count("gov-member-vacant"), 2)
        self.assertIn("2 vacant seats", fold)
        transpo = self.main("governments/transpo/index.html")
        self.assertIn("Holdover: printed term ended; still serving as of Oct 19, 2026", text(transpo))
        for path in ("governments/county/index.html", "governments/south-bend/index.html"):
            for r in re.findall(r'<li class="gov-member[^"]*".*?</li>', self.main(path), re.S):
                self.assertNotRegex(r, r"\((D|R|L)\)|@|\(\d{3}\)")

    # ------------------------------------------------------------------ debt
    def test_debt_by_year_chart_and_kept_id(self):
        money = self.main("governments/county/money/index.html")
        i = money.index('id="debt-years-county"')
        fig = money[i:money.index("</figure>", i)]
        for y in ("2022", "2023", "2024", "2025"):
            self.assertIn(y, fig)
        self.assertNotRegex(fig, r"party-|m-d\b|m-r\b")
        budgets = self.main("money/budgets/index.html")
        self.assertIn('id="debt-2024"', budgets)
        self.assertIn('id="debt-by-year"', budgets)
        self.assertNotRegex(budgets[budgets.index('id="debt-2024"'):budgets.index('id="debt-by-year"')], r"party-")

    def test_never_sum_and_utility_notes_follow_the_totals(self):
        for path in ("governments/county/money/index.html",
                     "governments/special-redevelopment-authority/money/index.html", "money/budgets/index.html",
                     "money/index.html"):
            self.assertIn("never add the two totals", self.main(path), path)
        for path in ("governments/mishawaka/money/index.html", "money/budgets/index.html"):
            self.assertIn("Includes utility (water, wastewater, electric) debt.", self.main(path), path)

    def test_whole_corporation_note_once_per_page(self):
        for path in ("governments/new-prairie/money/index.html", "governments/union-north/money/index.html",
                     "money/budgets/index.html"):
            m = self.main(path)
            self.assertEqual(m.count('id="whole-corporation"'), 1, path)
            self.assertEqual(len(re.findall(r"Whole corporation \(principal county", m)),
                             len(re.findall(r'<li><strong>[^<]*School Corporation[^<]*: </strong>Whole corporation', m)),
                             f"{path}: the phrase appears outside the one note")

    # ------------------------------------------------------------------ federal and statewide
    def test_federal_and_statewide_offices_have_pages_and_hub_levels(self):
        for oid in ("us-house-2", "us-senate-class-1", "us-senate-class-3", "state-governor", "state-treasurer"):
            self.assertIn(oid, self.ed.offices)
            self.assertIn(om.level(self.ed, self.ed.offices[oid]), ("statewide", "federal"))
        hub = self.main("offices/index.html")
        self.assertIn('id="statewide"', hub)
        self.assertIn('id="federal"', hub)
        house = text(self.main("offices/us-house-2/index.html"))
        self.assertIn("U.S. House District 2 includes all of St. Joseph County", house)
        senate = text(self.main("offices/us-senate-class-1/index.html"))
        self.assertIn("Statewide: every voter in St. Joseph County votes on this office", senate)
        self.assertNotIn("How to run for local office", house)

    def test_home_map_state_and_federal_layers_keep_the_county(self):
        from civic.map import load_shapes
        home = self._html["index.html"]
        county_d = load_shapes(self.ed)["county"]["d"]
        for tab, label in (("statewide", "Statewide offices"), ("federal", "Federal offices")):
            m = re.search(rf'<g class="cmap-layer[^"]*" data-layer="{tab}".*?</text></g></g>', home, re.S)
            self.assertIsNotNone(m, tab)
            layer = m.group(0)
            self.assertEqual(re.findall(r'<path d="([^"]+)"', layer), [county_d], f"{tab}: only the county outline")
            self.assertIn(label, layer)
            self.assertRegex(home, rf'hm-layer-note[^"]*" data-layer="{tab}"')
        self.assertIn("U.S. House District 2: includes all of St. Joseph County.", home)
        self.assertIn("Statewide offices: every voter in St. Joseph County votes on these", home)
        hub = self._html["offices/index.html"]
        self.assertRegex(hub, r'class="cmap-level-note muted" data-layer="federal"')

    def test_level_note_partial_house_district(self):
        ed = copy.copy(self.ed)
        ed.units = dict(self.ed.units)
        ed.units["us-house"] = dict(self.ed.units["us-house"], places_covered="Part of the county")
        self.assertIn("includes part of St. Joseph County", om.level_note(ed, "federal"))
        self.assertFalse(om.level_covers_county(ed, "federal"))
        self.assertTrue(om.level_covers_county(ed, "statewide"))
        self.assertIsNone(om.level_note(ed, "county"))

    # ------------------------------------------------------------------ county vs overall
    def test_overall_winner_differs_from_county_leader(self):
        c = self.ed.contests["2016g-state-governor"]
        inf = OV.info(self.ed, c)
        self.assertEqual(inf["basis"], "overall")
        self.assertEqual(inf["winners"], ["Eric Holcomb"])
        self.assertEqual(OV.county_leaders(c), ["John R. Gregg"])
        m = self.main("elections/2016g/contests/index.html")
        i = m.index('id="cvo-2016g-state-governor"')
        fig = m[i:m.index("</figure>", i)]
        self.assertIn("received the most votes in St. Joseph County", text(fig))
        gregg = re.search(r"<tr><th scope=\"row\">.*?John R\. Gregg.*?</tr>", fig, re.S).group(0)
        self.assertNotIn("Won", gregg)
        holcomb = re.search(r"<tr><th scope=\"row\">.*?Eric Holcomb.*?</tr>", fig, re.S).group(0)
        self.assertIn("Won", holcomb)
        self.assertIn('data-fmark="computed"', holcomb)   # share and winner are the guide's arithmetic
        self.assertIn("Statewide (all counties).", text(fig))
        self.assertNotIn("Statewide: statewide", text(fig))
        self.assertIn("St. Joseph County portion", m[m.index('id="res-2016g-state-governor"'):i])
        self.assertNotIn("certified", text(fig).lower())

    def test_wholly_pending_and_missing_cases(self):
        ed = self.ed
        self.assertEqual(OV.info(ed, ed.contests["2026g-state-house-6"])["basis"], "wholly")
        self.assertEqual(OV.info(ed, ed.contests["2026g-state-house-7"])["basis"], "pending")
        self.assertEqual(OV.info(ed, ed.contests["2010g-state-house-6"])["basis"], "missing")   # pre-2011 plan: held
        self.assertEqual(OV.info(ed, ed.contests["2012p-state-house-5-d"])["basis"], "wholly")  # same plan, noted
        self.assertEqual(OV.info(ed, ed.contests["2024g-county-commissioner-a" if "2024g-county-commissioner-a" in
                                                ed.contests else next(iter(ed.contests))])["basis"], "local")
        m = text(self.main("elections/2026g/contests/index.html"))
        self.assertIn(OV.WHOLLY_SENTENCE, m)
        self.assertIn("St. Joseph County portion. " + OV.PENDING_SENTENCE, m)
        self.assertEqual(sum(1 for c in ed.contests.values() if OV.info(ed, c)["basis"] == "wholly"), 69)

    def test_vote_for_n_school_case(self):
        ed = copy.copy(self.ed)
        ed.__dict__ = dict(self.ed.__dict__)
        ed.contests = dict(self.ed.contests)
        # a synthetic vote-for-2 board of a cross-county corporation (no such contest has overall rows in the data yet)
        cid = "2018g-new-prairie-schools-board-at-large"
        base = dict(ed.contests[cid]["rows"][0])
        names = ["First Candidate", "Second Candidate", "Third Candidate"]
        c = dict(ed.contests[cid], vote_for="2",
                 rows=[dict(base, candidate=n, party="", votes=str(v), pct="", vote_for="2", winner="")
                       for n, v in zip(names, (900, 800, 700))])
        ed.contests[cid] = c
        rows = [{"contest_id": cid, "candidate": n, "party": "", "overall_votes": str(v), "overall_pct": "",
                 "overall_winner": w, "overall_total_votes": "3000", "derived": "overall_winner;overall_total_votes",
                 "electorate": "NEW PRAIRIE UNITED SCHOOL CORPORATION", "vote_for": "2", "status": "official",
                 "source_ids": "RES-047", "notes": ""}
                for n, v, w in zip(names, (1100, 1000, 900), ("Y", "Y", "N"))]
        ed.__dict__["_overall_by_contest"] = {cid: rows}
        ed.warnings = []
        inf = OV.info(ed, c)
        self.assertEqual(inf["label"], "Whole school corporation")
        self.assertEqual(sorted(inf["winners"]), sorted(names[:2]))
        self.assertEqual(OV.county_leaders(c), names[:2])
        m = OV.overall_margin(ed, c)
        self.assertEqual((m["seats"], m["votes"]), (2, 100))
        site = Site(ed, Path(self.tmp.name) / "vfn")
        page = site.page("elections/compare/index.html")
        fig = str(OV.cvo_figure(page, c))
        self.assertEqual(fig.count(">Won<"), 2)
        self.assertNotRegex(fig, r"\d+\.\d%</span>\s*<span[^>]*>Won")   # no overall share printed for schools
        self.assertIn("Whole school corporation", fig)

    def test_margins_never_rank_a_county_portion(self):
        for r in N.margin_races(self.ed):
            if r["basis"] == "portion":
                self.assertEqual(r["kind"], "nc", r["c"]["contest_id"])
                self.assertEqual(r["m"], {"reason": N.PORTION_REASON})
            if r["basis"] == "overall" and "pts" in (r["m"] or {}):
                self.assertEqual(r["m"]["basis"], "overall")
        table = self.main("elections/compare/index.html")
        self.assertIn("Margin from", table)

    # ------------------------------------------------------------------ old links after the merge
    def test_superseded_source_keeps_its_anchor_on_the_replacement(self):
        from civic.components import superseded_by
        self.assertEqual(sorted(superseded_by(self.ed)["RES-048"]), ["GOV-001", "RES-029"])
        cal = self.main("elections/calendar/index.html")
        i = cal.index('id="src-RES-048"')
        entry = cal[i:cal.index("</li>", i)]
        self.assertIn('id="src-RES-029"', entry)
        self.assertIn("Replaces", entry)
        # a page citing the old id itself keeps its own entry and gets no second anchor
        self.assertEqual(cal.count('id="src-RES-029"'), 1)

    def test_calendar_places_statewide_and_federal_offices_once(self):
        items, _un = E._calendar_items(self.ed)
        for y in (2026, 2028, 2030):
            labels = [i["label"] for i in items[y] if i["level"] in ("statewide", "federal")]
            self.assertEqual(len(labels), len(set(labels)), y)
            self.assertFalse(any(i["level"] in ("state", "federal_chamber") for i in items[y]), y)
        self.assertEqual(sum(1 for i in items[2028] if i["label"].startswith("Governor")), 1)
        self.assertTrue(any(i["label"].startswith("U.S. Senator") for i in items[2030]))

    def test_question_layer_follows_the_ballot_line(self):
        c = self.ed.contests["2016g-mishawaka-public-question"]
        self.assertEqual(E.contest_layer(self.ed, c), "school:school-city-mishawaka")
        self.assertEqual(E.contest_layer(self.ed, self.ed.contests["2011g-mishawaka-public-question"]),
                         "municipality:mishawaka")

    # ------------------------------------------------------------------ unclassified contests
    def test_federal_contests_classified(self):
        c = self.ed.contests["2026g-us-house-2"]
        self.assertEqual(E.classify(c), ("Federal offices", "Congressional district (county portion)", True))
        self.assertEqual(c["office_id"], "us-house-2")

    def test_unclassified_contest_is_counted_never_a_crash(self):
        ed = copy.copy(self.ed)
        ed.__dict__ = dict(self.ed.__dict__)
        ed.contests = dict(self.ed.contests)
        ed.warnings = []
        row = {"election_id": "2024g", "contest_id": "2024g-mystery-board-x", "office_id": "", "contest_label":
               "Mystery Board X", "district": "", "party_primary": "", "candidate": "A Person", "party": "",
               "votes": "10", "pct": "", "winner": "", "vote_for": "1", "status": "official", "confidence": "high",
               "source_ids": "RES-001", "notes": ""}
        row2 = dict(row, candidate="B Person", votes="8")
        ed.contests["2024g-mystery-board-x"] = {"contest_id": "2024g-mystery-board-x", "election_id": "2024g",
                                                "label": "Mystery Board X", "district": "", "party_primary": "",
                                                "vote_for": "1", "office_id": "", "rows": [row, row2]}
        self.assertEqual(E.classify(ed.contests["2024g-mystery-board-x"])[0], "Other")
        races = N.margin_races(ed)
        r = next(r for r in races if r["c"]["contest_id"] == "2024g-mystery-board-x")
        self.assertEqual((r["g"], r["area"]), ("Other contests", "other"))
        self.assertEqual(N.area_level("other"), "other")
        self.assertIn(N.OTHER_GROUP, N.margin_groups(races))
        site = Site(ed, Path(self.tmp.name) / "other")
        page = N.build_margins(site)
        html = str(page._main())
        self.assertIn("Other contests", html)


if __name__ == "__main__":
    unittest.main()
