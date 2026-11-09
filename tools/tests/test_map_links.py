"""Tests for the Results page -> map race links (tools/site/civic/map.py results_contest_ids, race_by_contest).

Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "site"))

from civic.data import Edition  # noqa: E402
from civic.map import load_votes, race_by_contest, results_contest_ids  # noqa: E402


class ContestIds(unittest.TestCase):
    def test_bridges(self):
        self.assertIn("2024g-county-coroner", results_contest_ids("2024g", "county-coroner"))
        self.assertIn("2020g-state-governor", results_contest_ids("2020g", "governor"))
        self.assertIn("2022g-state-auditor-of-state", results_contest_ids("2022g", "auditor"))
        self.assertIn("2022g-clay-township-board", results_contest_ids("2022g", "township-board-clay"))
        self.assertIn("2022g-penn-township-assessor", results_contest_ids("2022g", "township-assessor-penn"))
        self.assertIn("2022g-walkerton-council-ward-2", results_contest_ids("2022g", "town-council-walkerton-ward-2"))
        self.assertNotIn("2022g-walkerton-ward-2-council-at-large",
                         results_contest_ids("2022g", "town-council-walkerton-ward-2"))
        self.assertIn("2022g-roseland-council-at-large", results_contest_ids("2022g", "town-council-roseland"))


class EditionLinks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.votes = load_votes(cls.ed)
        if not cls.votes:
            raise unittest.SkipTest("no map votes")
        cls.links = race_by_contest(cls.ed, cls.votes)

    def test_links_point_at_real_races_and_contests(self):
        races = {r["id"]: r for r in self.votes["races"]}
        have = {r["contest_id"] for r in self.ed.table("results")}
        self.assertTrue(self.links)
        for cid, rid in self.links.items():
            self.assertIn(cid, have)
            self.assertIn(rid, races)
            self.assertTrue(re.fullmatch(r"[A-Za-z0-9-]+", rid), rid)       # usable as #race-<id>
            self.assertTrue(cid.startswith(races[rid]["eid"] + "-"), (cid, rid))   # same election

    def test_one_race_per_contest(self):
        self.assertEqual(len(set(self.links.values())), len(self.links))

    def test_only_federal_races_unlinked(self):
        # federal races are not in results.csv; every other mapped race has its contest there
        linked = set(self.links.values())
        for r in self.votes["races"]:
            if r["id"] not in linked:
                self.assertEqual(r["level"], "federal", r["id"])


if __name__ == "__main__":
    unittest.main()
