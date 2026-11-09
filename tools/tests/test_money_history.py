"""Campaign money history (added 2026-11-09; pages/money_history.py, charts.period_money).

Nick: "the campaign finance history of every candidate, race, office, etc in St. Joseph county election history for
what we can find ... the user will be able to see the history when they drill down into a specific
seat/candidate/race."

- Every committee in cf_local.csv gets exactly one history fold across the site, on its home page (the area page of
  its newest race; else the area page of its other filings; else the party/PAC page); every link to it resolves.
- A history counts each cycle by the same rules as the race card (the race's own summary when the cycle is in a race).
- A blank "this period" line on the first report of a year is read from its year-to-date columns, and says so.
- Every race card has "This seat over time": every general election for the seat in the results (back to 2010), money
  where reports are on file, "Reports not posted online" before 2023.
- The officeholders page links each holder to their own committees, the best office match first.
- State legislators (Nick chose "State files 2000-2015"): cf_state_history.csv (tools/build_cf_state_history.py) never
  repeats a (committee, year) of cf_state.csv; the state page has one history per person; district tables link to it.
- News-reported figures (cf_reported.csv) for pre-2023 local races show in the seat history with their badge.
- A race-card candidate with no report in the race's cycle links to their committee's history from another cycle or
  office (full-name match only; never a surname alone).
- County-named PACs and party groups filing with the state (cf_state_pacs.csv, tools/build_cf_state_pacs.py) appear on
  the party/PAC page, one fold per state file number, 2010-2026.
Run:  python -P -E -m unittest discover -s tools/tests -p "test_money_history.py"
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = ROOT / "tools" / "site"
sys.path.insert(0, str(SITE_DIR))

import build  # noqa: E402
from civic import campaign_money as cm  # noqa: E402
from civic.charts import period_money  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site  # noqa: E402
from pages import money_history as mh  # noqa: E402

PENN = "money/campaigns/penn-township/index.html"
SB = "money/campaigns/south-bend/index.html"
STATE = "money/campaigns/state-legislature/index.html"
OTHER = "money/campaigns/other-committees/index.html"
HOLDERS = "officeholders/index.html"


class Chart(unittest.TestCase):
    def test_marks_legend_and_none(self):
        pts = [{"x": "Annual", "x2": "Dec 2024", "raised": 400065, "spent": 245660, "cash": 630265},
               {"x": "Annual", "x2": "Dec 2025", "raised": None, "spent": 0, "cash": None, "tip": "t"}]
        out = str(period_money("f", "T", pts))
        self.assertEqual(out.count('class="mark"'), 2)
        self.assertIn("not on the form", out)
        self.assertEqual(out.count('class="legend"'), 1)
        self.assertIn("m-spent", out)            # spent is an outline (shape, not only tone)
        self.assertIn("$6,302.65", out)          # the last cash value is labelled

    def test_negative_cash_extends_axis(self):
        out = str(period_money("f", "T", [{"x": "A", "raised": 100, "spent": 50000, "cash": -120000}]))
        self.assertRegex(out, r">-\$\d")


class Index(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.ix = mh.index(cls.ed)

    def test_every_committee_has_a_home_and_unique_anchor(self):
        self.assertEqual(set(self.ix["rows"]), set(self.ix["home"]))
        self.assertEqual(len(set(self.ix["anchor"].values())), len(self.ix["anchor"]))

    def test_home_is_newest_race(self):
        k = next(k for k, rs in self.ix["rows"].items() if rs[0]["_label"] == "Portolese for Penn Township Trustee")
        self.assertEqual(self.ix["home"][k], PENN)

    def test_race_cycle_uses_race_summary(self):
        for (k, cyc), (race, cand, s) in self.ix["claim"].items():
            part = next(p for p in mh._parts(self.ed, k) if p["cycle"] == cyc and p["race"])
            self.assertIs(part["s"], s)

    def test_every_filing_in_exactly_one_part(self):
        for k, rs in self.ix["rows"].items():
            ids = [it["row"]["filing_id"] for p in mh._parts(self.ed, k) for it in p["s"]["items"]]
            self.assertEqual(sorted(ids), sorted(r["filing_id"] for r in rs), k)


class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.site = Site(cls.ed, Path(cls.tmp.name))
        build.discover_builders()
        cls.paths = [p for p in build.BUILDERS if p.startswith("money/campaigns/")] + [HOLDERS]
        for p in cls.paths:
            build.BUILDERS[p](cls.site)
        cls.site.write()
        cls.html = {p: (Path(cls.tmp.name) / p).read_text(encoding="utf-8") for p in cls.paths}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_one_fold_per_committee_and_links_resolve(self):
        folds = []
        ids = {p: set(re.findall(r'\sid="([^"]+)"', s)) for p, s in self.html.items()}
        for s in self.html.values():
            folds += re.findall(r'<details class="cf-history" id="(mh-[^"]+)"', s)   # lh-: legislators, below
        self.assertEqual(len(folds), len(set(folds)))
        self.assertEqual(set(folds), set(mh.index(self.ed)["anchor"].values()))
        n = 0
        for p, s in self.html.items():
            for hrf in re.findall(r'href="([^"]*#mh-[^"]+)"', s):
                path, frag = hrf.split("#", 1)
                tgt = p if not path else os.path.normpath(os.path.join(os.path.dirname(p), unquote(path))).replace("\\", "/")
                self.assertIn(frag, ids.get(tgt, set()), (p, hrf))
                n += 1
        self.assertGreater(n, 100)

    def test_portolese_history(self):
        s = self.html[PENN]
        i = s.index('id="mh-portolese-for-penn-township-trustee"')
        fold = s[i:s.index("</details>", s.index('class="chart-table"', i)) + 2000]
        for cyc in ("2023 municipal cycle", "2024 cycle", "2026 cycle"):
            self.assertIn(cyc, fold)
        self.assertIn("year-to-date column", fold)           # 2023 annual: period lines blank
        self.assertEqual(fold.count('class="mark"'), 4)

    def test_seat_history_on_every_card(self):
        for p, s in self.html.items():
            self.assertEqual(s.count('class="cf-race-card"'), s.count('class="cf-seat-history"'), p)
        s = self.html[PENN]
        i = s.index('id="sh-2026g-penn-township-trustee"')
        block = s[i:s.index("</details>", i)]
        self.assertIn("5 elections, 2010 to 2026", block)
        self.assertIn("this race", block)
        self.assertEqual(block.count("Reports not posted online"), 4)

    def test_officeholder_links_best_match_first(self):
        s = self.html[HOLDERS]
        row = next(r for r in re.findall(r'<li[^>]*class="oh-row".*?</li>', s, re.S) if "Bill Redman" in r)
        text = re.sub("<[^>]+>", "", re.search(r'<p class="oh-money">(.*?)</p>', row, re.S).group(1))
        self.assertLess(text.index("SHERIFF"), text.index("Commissioner"))
        self.assertGreater(s.count('class="oh-money"'), 50)


class StateHistory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")

    def test_no_overlap_with_cf_state(self):
        have = {(r["committee"].casefold(), r["year"]) for r in self.ed.table("cf_state")}
        rows = self.ed.table("cf_state_history")
        self.assertGreater(len(rows), 200)
        for r in rows:
            self.assertNotIn((r["committee"].casefold(), r["year"]), have, r["committee"])
            self.assertTrue(r["status"] and r["source_ids"])
            float(r["receipts"]), float(r["expenditures"])
        self.assertEqual(min(int(r["year"]) for r in rows), 2000)

    def test_everyone_was_on_a_legislative_ballot(self):
        names = {r["candidate"] for r in self.ed.table("results")
                 if re.search(r"State (Senator|Representative)", r["contest_label"])}
        for r in self.ed.table("cf_state_history"):
            self.assertTrue(any(cm.same_person(r["candidate"], n) for n in names), r["candidate"])

    def test_people_unique(self):
        ppl = mh.legislators(self.ed)
        self.assertEqual(len({p["anchor"] for p in ppl}), len(ppl))
        arnold = next(p for p in ppl if "Arnold" in p["name"])
        self.assertEqual(arnold["years"][0], 2007)

    def test_reported_rows_all_placed(self):
        rep = mh.reported(self.ed)
        n = sum(len(rs) for groups in rep.values() for _c, rs in groups)
        self.assertEqual(n, len(self.ed.table("cf_reported")))
        self.assertIn("2011g-south-bend-mayor", rep)          # a primary's figures sit on that year's general row


class CrossCycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")

    def test_state_pacs(self):
        pacs = mh.state_pacs(self.ed)
        self.assertGreaterEqual(len(pacs), 5)
        cand = {r["committee"].casefold() for r in self.ed.table("cf_state")}
        for p in pacs:
            self.assertNotIn(p["name"].casefold(), cand)
            self.assertGreaterEqual(min(p["years"]), 2010)
        self.assertEqual(len({p["anchor"] for p in pacs}), len(pacs))

    def test_same_name_only(self):
        class P:   # a page stub: same-page links only need path and site.by_path
            path = PENN
            site = type("S", (), {"by_path": {PENN: 1, SB: 1, OTHER: 1}})()
            def rel(self, x):
                return x
        got = mh.same_name_links(self.ed, P(), "Sonia Perez")
        self.assertTrue(any("Friends of Sonia Perez" in str(x) for x in got))
        self.assertFalse(any("Gary Fox" in str(x) for x in mh.same_name_links(self.ed, P(), "Bob Fox")))


class BuiltState(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.site = Site(cls.ed, Path(cls.tmp.name))
        build.discover_builders()
        for p in (STATE, SB, HOLDERS, OTHER):
            build.BUILDERS[p](cls.site)
        cls.site.write()
        cls.html = {p: (Path(cls.tmp.name) / p).read_text(encoding="utf-8") for p in (STATE, SB, HOLDERS, OTHER)}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_state_people_section(self):
        s = self.html[STATE]
        self.assertIn('id="people"', s)
        folds = re.findall(r'<details class="cf-history" id="(lh-[^"]+)"', s)
        self.assertEqual(len(folds), len(mh.legislators(self.ed)))
        for frag in re.findall(r'href="#(lh-[^"]+)"', s):
            self.assertIn(frag, folds)

    def test_news_figures_in_seat_history(self):
        s = self.html[SB]
        i = s.index('id="sh-2023g-south-bend-mayor"')
        block = s[i:s.index("</details>", i)]
        self.assertIn("$229,875.71", block)
        self.assertIn("SECONDARY", block)
        self.assertIn("$253,939,", block)                    # whole dollars as reported, no .00
        self.assertIn("nearly $245,000", block)              # a rounded figure keeps the source's words

    def test_pacs_on_other_page(self):
        s = self.html[OTHER]
        self.assertIn('id="state-filed"', s)
        self.assertEqual(len(re.findall(r'<details class="cf-history" id="sp-', s)), len(mh.state_pacs(self.ed)))

    def test_cross_cycle_link_on_card(self):
        self.assertIn("Filed in another cycle or for another office", self.html[SB])

    def test_legislators_link_from_officeholders(self):
        self.assertIn("Campaign money history (state filings)", self.html[HOLDERS])


if __name__ == "__main__":
    unittest.main()
