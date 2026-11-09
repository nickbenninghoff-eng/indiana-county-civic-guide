"""Wave B fix-ups: entity_list passes a ready-made badge through, contests resolve to their offices through the
documented alias table, and money/campaigns/all-filings ships every filing in the HTML (JavaScript off).
Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "site"))

from civic.components import entity_list, status_badge  # noqa: E402
from civic.data import CONTEST_OFFICE_ALIASES, Edition  # noqa: E402
from civic.html import Markup, h  # noqa: E402


class EntityListStatus(unittest.TestCase):
    def _item(self, status):
        return {"key": "a", "name": "Ada", "status": status, "body": h("p", None, "body")}

    def test_markup_status_is_not_escaped_again(self):
        badge = status_badge("official")
        out = str(entity_list("l", [self._item(badge)]))
        self.assertIn(str(badge), out)
        self.assertNotIn("&lt;span", out)

    def test_plain_key_goes_through_status_badge(self):
        out = str(entity_list("l", [self._item("official")]))
        self.assertIn(str(status_badge("official")), out)

    def test_markup_other_than_a_badge_passes_unchanged(self):
        out = str(entity_list("l", [self._item(Markup("<em>custom</em>"))]))
        self.assertIn('<span class="ent-status"><em>custom</em></span>', out)

    def test_no_status_no_badge_span(self):
        self.assertNotIn("ent-status", str(entity_list("l", [self._item(None)])))


class ContestOffices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")

    def test_walkerton_judge_contests_link_to_the_office(self):
        for cid in ("2015g-walkerton-judge", "2023p-walkerton-judge-r", "2023g-walkerton-judge"):
            self.assertEqual(self.ed.contests[cid]["office_id"], "walkerton-town-judge", cid)
        got = {c["contest_id"] for c in self.ed.contests_for_office("walkerton-town-judge", general_only=False)}
        self.assertEqual(got, {"2015g-walkerton-judge", "2023p-walkerton-judge-r", "2023g-walkerton-judge"})

    def test_every_alias_targets_a_real_office(self):
        for stem, oid in CONTEST_OFFICE_ALIASES.items():
            self.assertIn(oid, self.ed.offices, stem)

    def test_unmatched_contests_are_only_the_reviewed_kinds(self):
        """Contests with no office: state offices, retention votes, questions, straight-party counts, plus the
        reviewed ambiguous ones. A new unmatched contest of another kind should be looked at, not silently added."""
        seen = {}
        for r in self.ed.tables["results"]:
            seen.setdefault(r["contest_id"], r)
        odd = [cid for cid, r in seen.items() if not self.ed._contest_office(r)
               and not re.search(r"-(state|straight-party|public-question|retention|question)", cid)
               and "superior-court-retention" not in cid]
        self.assertEqual(sorted(odd), sorted([
            "2011g-osceola-council-ward-1", "2011g-osceola-council-ward-2", "2011g-osceola-council-ward-3",
            "2019g-osceola-unknown-office", "2019g-osceola-council-ward-1", "2019g-osceola-council-ward-2",
            "2019g-osceola-council-ward-3", "2026g-new-prairie-schools-board-at-large-district-2"]))


if __name__ == "__main__":
    unittest.main()
