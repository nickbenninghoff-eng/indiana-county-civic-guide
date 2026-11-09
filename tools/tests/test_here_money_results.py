"""Saved place on the campaign-money and close-races pages (Nick, 2026-11-09: "add that to the campaign money and
results pages").

- money/campaigns/index.html: the area list has a "rows" slot, and every area row names its layer
  (municipality:/township:/school:/county/...) so preselect.js can move the reader's rows to the top.
- elections/margins/index.html: a "one" slot whose JSON gives, per saved place, fold keys that exist on the page
  (countywide plus the single commissioner/council district where the precinct results show one); the page script
  adds the place's city or town, township and school folds (data-here-also).
- Clearing the saved place: the slot is hidden by default and the page shows everything, as before.
Run:  python -P -E -m unittest discover -s tools/tests -p "test_here_money_results.py"
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = ROOT / "tools" / "site"
sys.path.insert(0, str(SITE_DIR))

import build  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site  # noqa: E402

CAMPAIGNS = "money/campaigns/index.html"
MARGINS = "elections/margins/index.html"
LAYER = re.compile(r"^(county|state|library|(municipality|township|school):[a-z0-9-]+)$")


class HereMoneyResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.site = Site(cls.ed, Path(cls.tmp.name))
        build.discover_builders()
        for p in (CAMPAIGNS, MARGINS):
            build.BUILDERS[p](cls.site)
        cls.site.write()
        cls.html = {p: (Path(cls.tmp.name) / p).read_text(encoding="utf-8") for p in (CAMPAIGNS, MARGINS)}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_campaigns_rows_slot_and_layers(self):
        s = self.html[CAMPAIGNS]
        self.assertRegex(s, r'<p class="here-pre" data-here-pre="rows" data-here-for="areas" hidden')
        rows = re.findall(r'<tr data-here-layer="([^"]*)" data-here-name="([^"]+)"', s)
        self.assertGreater(len(rows), 10)
        for layer, name in rows:
            self.assertRegex(layer, LAYER, name)
        layers = {l for l, _ in rows}
        self.assertIn("municipality:south-bend", layers)
        self.assertTrue(any(l.startswith("township:") for l in layers))
        self.assertTrue(any(l.startswith("school:") for l in layers))

    def test_margins_slot_keys_exist(self):
        s = self.html[MARGINS]
        self.assertIn('data-here-pre="one" data-here-for="areas" hidden', s)
        self.assertIn('data-here-also="muni township school"', s)
        m = re.search(r'<script[^>]*id="here-margin-areas"[^>]*>(.*?)</script>', s, re.S)
        self.assertIsNotNone(m)
        data = json.loads(m.group(1))
        folds = set(re.findall(r'<details[^>]*data-one="([^"]+)"', s))
        self.assertEqual(set(data["places"]), set(self.site.here_data["places"]))
        for pid, d in data["places"].items():
            self.assertEqual(d["keys"][0], "countywide", pid)
            self.assertLessEqual(set(d["keys"]), folds, pid)
            self.assertLessEqual(sum(k.startswith("commissioner-") for k in d["keys"]), 1, pid)
            self.assertLessEqual(sum(k.startswith("council-") for k in d["keys"]), 1, pid)
        for alias in data["alias"].values():
            self.assertLessEqual(set(alias), folds)
        # the city ids the script adds through data-here-also are fold keys here
        for pid in ("south-bend", "mishawaka", "penn-township", "sbcsc"):
            self.assertIn(pid, folds)


if __name__ == "__main__":
    unittest.main()
