"""Wave B, batch 4 ("Lists instead of stacks"): history/people, other-committees, all-filings, who-handles-this,
the run pages, data/pull and income-and-work.

Builds those pages into a temporary folder and checks that every id the pages carried before the batch
(tests/fixtures/anchors_before_batch4.json) is still there, or is forwarded (static/js/moved.js), and that
the new lists hold every entity.
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

FIXTURE = Path(__file__).parent / "fixtures" / "anchors_before_batch4.json"
ID_RE = re.compile(r'\sid="([^"]+)"')
OFFICES = ["township-trustee", "township-board", "school-board", "city-council", "county-council",
           "precinct-committeeperson"]
PAGES = ["history/people/index.html", "money/campaigns/other-committees/index.html",
         "money/campaigns/all-filings/index.html", "who-handles-this/index.html", "run/index.html",
         "data/pull/index.html", "community/income-and-work/index.html"] + [f"run/{o}/index.html" for o in OFFICES]


class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        site = Site(cls.ed, cls.out)
        build.discover_builders()
        for p in PAGES:
            build.BUILDERS[p](site)
        site.write()
        cls.html = {p: (cls.out / p).read_text(encoding="utf-8") for p in PAGES}
        cls.ids = {p: set(ID_RE.findall(h)) for p, h in cls.html.items()}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # ---------------------------------------------------------------- anchors
    def test_every_old_id_still_resolves_or_is_forwarded(self):
        before = json.loads(FIXTURE.read_text(encoding="utf-8"))["ids"]
        lost = []
        for page, ids in before.items():
            for i in ids:
                if i in self.ids[page]:
                    continue
                # run/<office>/: a #src-... citation id of a fact that now lives once on run/index.html is forwarded
                # by static/js/moved.js to run/index.html
                if page.startswith("run/") and page != "run/index.html" and i.startswith("src-") \
                        and i in self.ids["run/index.html"]:
                    continue
                # the old "Pick an office" table became the cards; its copy button went with it
                if page == "run/index.html" and i == "tbl-run-pick-copy":
                    continue
                lost.append((page, i))
        self.assertEqual(lost, [])

    def test_office_pages_ship_the_forwarding_map(self):
        """An old #src-... link on a trimmed office page is sent to run/index.html by static/js/moved.js, which reads
        the page's #moved-anchors; every forwarded id exists on run/index."""
        for o in OFFICES:
            h = self.html[f"run/{o}/index.html"]
            m = json.loads(re.search(r'id="moved-anchors">(.*?)</script>', h).group(1))
            self.assertTrue(m["a"], o)
            for i, dest in m["a"].items():
                self.assertEqual(dest, "../index.html")
                self.assertIn(i, self.ids["run/index.html"], (o, i))

    def test_no_duplicate_ids(self):
        for p, h in self.html.items():
            ids = ID_RE.findall(h)
            self.assertEqual({i for i in ids if ids.count(i) > 1}, set(), p)

    # ---------------------------------------------------------------- history/people
    def test_every_person_card_is_a_row_with_its_anchor(self):
        h = self.html["history/people/index.html"]
        before = [i for i in json.loads(FIXTURE.read_text(encoding="utf-8"))["ids"]["history/people/index.html"]
                  if i.startswith("person-")]
        self.assertGreaterEqual(len(before), 30)
        rows = re.findall(r'<li class="ent-row"', h)
        self.assertEqual(len(rows), len(before))
        for i in before:
            self.assertRegex(h, rf'<details[^>]*\sid="{re.escape(i)}"')
        self.assertEqual(h.count('class="card person-card"'), len(before))
        self.assertNotIn("&lt;span", h)

    def test_people_rows_show_party_as_text_and_no_party_filter(self):
        h = self.html["history/people/index.html"]
        self.assertNotIn('data-tf-key="party"', h)
        self.assertIn('data-tf-key="era"', h)

    # ---------------------------------------------------------------- campaigns
    def test_other_committees_one_row_per_committee(self):
        h = self.html["money/campaigns/other-committees/index.html"]
        n_tables = len(re.findall(r"<table[ >]", h))
        n_rows = len(re.findall(r'<li class="ent-row"', h))
        self.assertGreater(n_rows, 10)
        self.assertGreaterEqual(n_tables, n_rows)  # every committee keeps at least one reports table
        self.assertEqual(h.count('class="cf-committee-block"'), n_rows)

    def test_all_filings_has_the_list_and_the_see_all_fold(self):
        h = self.html["money/campaigns/all-filings/index.html"]
        for i in ("cf-list", "cf-list-block", "cf-all-fold", "cf-table", "cf-table-copy", "cf-count", "cf-totals",
                  "cf-controls", "cf-data"):
            self.assertIn(f'id="{i}"', h)
        self.assertIn('data-fold="see-all"', h)
        data = json.loads(re.search(r'id="cf-data"[^>]*>(.*?)</script>', h, re.S).group(1).replace("<\\/", "</"))
        # JS off: every filing is a row in the HTML, once (the script derives the committee list from them)
        self.assertEqual(len(re.findall(r'<tr data-ci="', h)), 479)
        self.assertNotIn("rows", data)

    # ---------------------------------------------------------------- who handles this
    def test_services_list_has_every_service_and_the_table_fold(self):
        h = self.html["who-handles-this/index.html"]
        n = len(list(self.ed.table("services")))
        self.assertEqual(len(re.findall(r'<li class="ent-row"', h)), n)
        self.assertIn('id="tbl-services"', h)
        self.assertIn('id="tbl-services-all"', h)
        self.assertEqual(len(re.findall(r"<tbody>.*?</tbody>", h, re.S)[0].split("<tr>")) - 1, n)

    # ---------------------------------------------------------------- run pages
    def test_run_index_has_office_cards(self):
        h = self.html["run/index.html"]
        self.assertEqual(h.count('class="card run-card"'), 6)
        for o in OFFICES:
            self.assertIn(f'href="{o}/index.html"', h)

    def test_office_pages_are_short_and_link_to_the_shared_steps(self):
        idx = self.html["run/index.html"]
        for o in OFFICES:
            h = self.html[f"run/{o}/index.html"]
            self.assertLess(len(h), len(idx), o)
            for a in ("money", "vacancies", "contacts"):
                if a == "money" and o == "precinct-committeeperson":
                    continue  # that office has no campaign-finance section
                self.assertIn(f'href="../index.html#{a}"', h, (o, a))
            for a in ("money", "vacancies", "contacts"):
                self.assertIn(f'id="{a}"', idx)
            # shared prose lives once: the contact card and the party list are only on run/index
            self.assertNotIn("County-City Building", h, o)
            self.assertNotIn("party-orgs", h, o)
        self.assertIn("County-City Building", idx)

    # ---------------------------------------------------------------- data/pull, income-and-work
    def test_pull_sources_are_folds_and_keep_their_heading_ids(self):
        h = self.html["data/pull/index.html"]
        for i in ("pull-results", "pull-filings", "pull-gateway", "pull-cf", "pull-census", "indicator-defs"):
            self.assertIn(f'id="{i}"', h)
        self.assertEqual(h.count('class="fold-details see-all pull-fold"'), 5)
        self.assertIn('id="indicator-defs-all"', h)

    def test_employer_tables_are_in_folds(self):
        h = self.html["community/income-and-work/index.html"]
        self.assertGreaterEqual(h.count('data-fold="see-all"'), 2)
        self.assertIn('id="employers-single-all"', h)


if __name__ == "__main__":
    unittest.main()
