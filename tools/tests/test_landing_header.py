"""Home page header (Nick, 2026-11-09: "By the numbers"; the guide is a central reference for the county's government,
elections and money, not mainly an address lookup).

- The header counts the whole county from the data: local governments (units, not the two state chambers) and their
  elected seats; never hard-coded.
- The "since" line names the first year with broad results and says what the older years hold.
- The per-address counts (here.js fills data-count) moved under "Pick your place"; none are left in the header.
Run:  python -P -E -m unittest discover -s tools/tests -p "test_landing_header.py"
"""
from __future__ import annotations

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


class Header(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        site = Site(cls.ed, Path(cls.tmp.name))
        build.discover_builders()
        build.BUILDERS["index.html"](site)
        site.write()
        cls.html = (Path(cls.tmp.name) / "index.html").read_text(encoding="utf-8")
        i = cls.html.index('<section class="hero"')
        cls.hero = cls.html[i:cls.html.index("</section>", i)]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_counts_from_data(self):
        state = {u["unit_id"] for u in self.ed.tables["units"] if u["unit_type"] == "state_chamber"}
        n_gov = sum(1 for u in self.ed.tables["units"] if u["unit_id"] not in state)
        n_seats = sum(int(o.get("seats") or 1) for o in self.ed.tables["offices"]
                      if o.get("elected") == "yes" and o["unit_id"] not in state)
        self.assertIn("One county.", self.hero)
        self.assertIn(f"{n_gov} local governments.", self.hero)
        self.assertIn(f"{n_seats} elected seats.", self.hero)
        self.assertNotIn("One address", self.html)

    def test_since_line(self):
        self.assertRegex(self.hero, r"Election results from 20\d\d on \(South Bend mayor back to 19\d\d\)")

    def test_address_counts_moved_to_picker(self):
        self.assertNotIn("data-count", self.hero)
        i = self.html.index('class="pick-counts"')
        block = self.html[i:i + 4000]
        for key in ("gov", "elected", "vote", "appointed", "noplace", "noplace-alt"):
            self.assertIn(f'data-count="{key}"', block, key)


if __name__ == "__main__":
    unittest.main()
