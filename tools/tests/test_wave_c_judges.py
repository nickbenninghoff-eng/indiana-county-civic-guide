"""Wave C, batch 5: elections/judges-and-questions/ as lists. Every id the page carried before
(tests/fixtures/anchors_before_wave_c5.json) is still there, every question is a row, retention tables are in folds.
Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "site"))

import build  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site  # noqa: E402
from pages import elections as E  # noqa: E402

PAGE = "elections/judges-and-questions/index.html"
FIXTURE = Path(__file__).parent / "fixtures" / "anchors_before_wave_c5.json"


class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        site = Site(cls.ed, Path(cls.tmp.name))
        build.discover_builders()
        for p in (PAGE, "elections/results/index.html"):
            build.BUILDERS[p](site)
        site.write()
        cls.html = (Path(cls.tmp.name) / PAGE).read_text(encoding="utf-8")
        cls.ids = set(re.findall(r'\sid="([^"]+)"', cls.html))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_old_id_still_resolves(self):
        before = json.loads(FIXTURE.read_text(encoding="utf-8"))["ids"][PAGE]
        self.assertEqual([i for i in before if i not in self.ids], [])

    def test_every_question_is_a_row_with_its_wording_or_gap_and_figure(self):
        qs = [c for c in self.ed.contests.values() if E.classify(c)[0] == "Public questions"]
        self.assertGreaterEqual(len(qs), 14)
        self.assertEqual(len(re.findall(r'<li class="ent-row"', self.html)), len(qs))
        for c in qs:
            self.assertRegex(self.html, rf'<details[^>]*\sid="q-{re.escape(c["contest_id"])}"')
            self.assertIn(f'id="qbar-{c["contest_id"]}"', self.html)
        self.assertEqual(self.html.count('class="elx-wording"') + self.html.count('class="elx-gapline"'), len(qs))

    def test_questions_grouped_by_jurisdiction_statewide_first(self):
        groups = re.findall(r'class="elx-qgroup-h">([^<]+)<', self.html)
        self.assertEqual(groups[0], "Statewide")
        self.assertEqual(groups[1:], sorted(groups[1:], key=str.lower))

    def test_rows_show_year_outcome_and_key_number(self):
        for row in re.findall(r'<summary class="fold-summary one-summary">(.*?)</summary>', self.html, re.S)[:14]:
            self.assertRegex(row, r"Yes \d+\.\d%")
            self.assertRegex(row, r"(Passed|Failed|County voted|Unofficial|Tied)")

    def test_retention_tables_in_folds_with_contest_links(self):
        for t in ("retention-table", "state-retention-table"):
            self.assertRegex(self.html, rf'<details[^>]*id="{t}-all"[^>]*data-fold="see-all"')
            self.assertIn(f'id="{t}"', self.html)
        self.assertIn("results/index.html#contest-", self.html)

    def test_explainer_first_and_nonpartisan(self):
        self.assertLess(self.html.index('id="how"'), self.html.index('id="retention"'))
        self.assertIn("How questions get on the ballot", self.html)
        self.assertNotRegex(self.html, r"party-(rep|dem)")
