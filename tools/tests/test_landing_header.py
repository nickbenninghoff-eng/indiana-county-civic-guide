"""Home page header (Nick, 2026-11-09: "By the numbers"; the guide is a central reference for the county's government,
elections and money, not mainly an address lookup).

- The header counts the whole county from the data: governments and public bodies with a page (civic/governments.py
  count(), since 2026-11-18; was units minus the two state chambers) and the
  elected seats; never hard-coded.
- The "since" line names the first year with broad results and says what the older years hold.
- The per-address counts (here.js filled data-count) were retired with the seat diagram in the phase 6 home page
  (2026-11-18): the per-place counts are on Your place (your-governments/); the home page shows the reader's
  governments on the map instead (tools/tests/test_phase6_home.py).
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
        i = cls.html.index('<section class="home-intro"')
        cls.hero = cls.html[i:cls.html.index("</section>", i)]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_counts_from_data(self):
        # 2026-11-18: "elected local seats" leaves out the legislature and the statewide and federal offices
        state = {u["unit_id"] for u in self.ed.tables["units"]
                 if u["unit_type"] in ("state_chamber", "state", "federal_chamber")}
        # 2026-11-18: the governments count is the pages (civic/governments.py count), worded so it is true of each
        from civic import governments as gm
        n_gov = len(gm.governments(self.ed))
        n_seats = sum(int(o.get("seats") or 1) for o in self.ed.tables["offices"]
                      if o.get("elected") == "yes" and o["unit_id"] not in state)
        self.assertIn("One county.", self.hero)
        self.assertIn(f"{n_gov} governments and public bodies.", self.hero)
        self.assertIn(f"{n_seats} elected local seats.", self.hero)
        federal = sum(int(o.get("seats") or 1) for o in self.ed.tables["offices"]
                      if o["unit_id"] in ("us-house", "us-senate", "in-state"))
        self.assertGreater(federal, 0)   # the data has them; the count above must not include them
        self.assertNotIn("One address", self.html)

    def test_since_line(self):
        self.assertRegex(self.hero, r"[Ee]lection results from 20\d\d on \(South Bend mayor back to 19\d\d\)")

    def test_no_address_counts_left(self):
        self.assertNotIn("data-count", self.html)
        self.assertIn('id="your-govs"', self.html)


if __name__ == "__main__":
    unittest.main()
