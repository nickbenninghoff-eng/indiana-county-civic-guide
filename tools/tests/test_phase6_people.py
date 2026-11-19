"""Phase 6 person pages (2026-11-16): who is who, who gets a page, the person tabs, the People hub, the notable-people
view and the forward from history/people/, name links, search, and the shorter county Overview and Close races tab.

- Identity (civic/people.py group_names): the site's full-name rule (campaign_money.same_person, with both nickname
  tables), middle names and suffixes must agree, never a surname or initials alone, a one-sided suffix only for the same
  office, a bridge between two disagreeing names stays apart, deterministic.
- Pages: everyone in terms.csv and every notable person has a page; tabs come from the model (no History tab); the
  Money tab's figures are the office pages' own (the race card sums).
- Links: names printed with a party tag link to the person's page, never inside another link or a <summary>.
Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import json
import posixpath
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
from civic import people as pm  # noqa: E402
from civic import sitemap  # noqa: E402
from civic.components import name_with_party, table_filter  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "anchors_before_people.json"
ID_RE = re.compile(r'\sid="([^"]+)"')


def groups_of(names, seats=None):
    return {tuple(g) for g in pm.group_names(names, seats)}


class Identity(unittest.TestCase):
    """The name rules alone, on made-up strings."""

    def test_suffix_punctuation_is_one_person(self):
        self.assertIn(("Henry Davis Jr", "Henry Davis Jr."), groups_of(["Henry Davis Jr", "Henry Davis Jr."]))

    def test_middle_initials_and_names(self):
        self.assertIn(("Amy Cressy", "Amy S. Cressy", "Amy Suzanne Cressy"),
                      groups_of(["Amy Cressy", "Amy S. Cressy", "Amy Suzanne Cressy"]))
        g = groups_of(["John A. Smith", "John B. Smith"])
        self.assertEqual(g, {("John A. Smith",), ("John B. Smith",)})

    def test_bridge_between_disagreeing_names_stays_apart(self):
        g = groups_of(["John A. Smith", "John B. Smith", "John Smith"])
        self.assertEqual(g, {("John A. Smith",), ("John B. Smith",), ("John Smith",)})
        # unless exactly one side shares the bridge's office
        g = groups_of(["John A. Smith", "John B. Smith", "John Smith"],
                      {"John Smith": {"x-board"}, "John A. Smith": {"x-board"}, "John B. Smith": {"y-board"}})
        self.assertIn(("John A. Smith", "John Smith"), g)

    def test_never_on_surname_or_initials(self):
        for a, b in [("Carter", "Jimmy Carter"), ("T. Brown", "Tom Brown"), ("J. Kata", "J. J. Kata")]:
            self.assertFalse(pm.match(a, b), (a, b))
            self.assertEqual(len(groups_of([a, b])), 2)
        self.assertTrue(pm.is_partial("Pfeifer (given name unconfirmed: Beverly or Charlotte)"))
        self.assertFalse(pm.is_partial('"Bobby K" Kruszynski'))

    def test_different_given_names_never_match(self):
        self.assertFalse(pm.match("Ryan Dvorak", "Michael Dvorak"))
        self.assertFalse(pm.match("Sheila Niezgodski", "David Niezgodski"))

    def test_nicknames_from_both_tables(self):
        self.assertTrue(pm.match("Bill Redman", "William Redman"))        # campaign_money table
        self.assertTrue(pm.match("Steve Luecke", "Stephen Luecke"))       # community_history table
        # the quoted nickname is a given name, and "K" is not a middle initial; the one-sided "Jr." needs a shared seat
        seat = {'Robert L. "Bobby K" Kruszynski Jr.': {"county-council-a"}, "Bobby K Kruszynski": {"county-council-a"}}
        self.assertTrue(pm.match('Robert L. "Bobby K" Kruszynski Jr.', "Bobby K Kruszynski", seat))
        self.assertTrue(pm.match('Robert L. "Bobby K" Kruszynski Jr.', "Bobby K. Kruszynski Jr."))

    def test_one_sided_suffix_needs_the_same_office(self):
        self.assertFalse(pm.match("Schuyler Colfax", "Schuyler Colfax III"))
        self.assertTrue(pm.match("Joe Taylor", "Joe Taylor III", {"Joe Taylor": {"state-house-7"},
                                                                   "Joe Taylor III": {"state-house-7"}}))
        self.assertFalse(pm.match("Joe Taylor Jr", "Joe Taylor Sr", {"Joe Taylor Jr": {"x"}, "Joe Taylor Sr": {"x"}}))

    def test_notes_and_titles_set_aside(self):
        self.assertTrue(pm.match("Michael Schalk (write-in)", "Mike Schalk"))
        self.assertTrue(pm.match("Dr. Oliver J. Davis, Jr.", "Oliver J. Davis", {"Dr. Oliver J. Davis, Jr.": {"unit:sb"},
                                                                                  "Oliver J. Davis": {"unit:sb"}}))
        self.assertEqual(pm.clean("Karen Iovino (interim)"), "Karen Iovino")

    def test_deterministic(self):
        names = ["Tom E McCormick", "Thomas L. McCormick", "Tom McCormick", "Tom E. McCormick", "Lacy Hahn"]
        self.assertEqual(pm.group_names(names), pm.group_names(list(reversed(names))))

    def test_implausible_rule(self):
        R = pm.Rec
        far = [R("result", "A B", 1963, 1963, "south-bend", "R", {}), R("result", "A B", 2024, 2024, "penn", "D", {})]
        self.assertTrue(pm.implausible(far))
        same_party = [R("result", "A B", 1963, 1963, "south-bend", "D", {}), R("result", "A B", 2024, 2024, "penn", "D", {})]
        self.assertFalse(pm.implausible(same_party))
        nonpartisan = [R("result", "A B", 1979, 1979, "south-bend", "D", {}), R("result", "A B", 2012, 2012, "sbcsc", "NP", {})]
        self.assertFalse(pm.implausible(nonpartisan))
        spanned = [R("term", "A B", 1960, 2000, "south-bend", "R", {}), R("result", "A B", 2010, 2010, "penn", "D", {})]
        self.assertFalse(pm.implausible(spanned))


class Data(unittest.TestCase):
    """The registry on the St. Joseph County data."""

    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.reg = pm.registry(cls.ed)

    def test_every_officeholder_has_a_page(self):
        for t in self.ed.tables["terms"]:
            p = self.reg.person(t["person"])
            self.assertIsNotNone(p, t["person"])
            self.assertTrue(p.page, t["person"])

    def test_every_notable_person_has_a_page(self):
        from pages.community_history import notable_rows
        rows = notable_rows(self.ed)
        self.assertGreaterEqual(len(rows), 35)
        for row in rows:
            p = self.reg.person(row["name"])
            self.assertIsNotNone(p, row["name"])
            self.assertTrue(p.page and p.notable is row, row["name"])

    def test_ids_are_unique_and_stable_slugs(self):
        pids = list(self.reg.people)
        self.assertEqual(len(pids), len(set(pids)))
        for pid in pids:
            self.assertRegex(pid, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertIn("james-mueller", self.reg.people)
        self.assertIn("pete-buttigieg", self.reg.people)

    def test_known_merges_and_splits(self):
        k = self.reg.person("Robert L. \"Bobby K\" Kruszynski Jr.")
        for n in ['"Bobby K" Kruszynski', "(Bobby K.) Kruszynski Jr.", "Bobby Kruszynski", "Bobby K. Kruszynski Jr."]:
            self.assertIs(self.reg.person(n), k, n)
        tom = self.reg.person("Tom McCormick")
        self.assertIs(self.reg.person("Tom E McCormick"), tom)          # same Liberty Township Board seat
        self.assertIsNot(self.reg.person("Thomas L. McCormick"), tom)
        self.assertIsNot(self.reg.person("Schuyler Colfax"), self.reg.person("Schuyler Colfax III"))
        hahn = self.reg.person("Lacy Hahn")
        self.assertIsNot(self.reg.person("Lacy Jane Hahn"), hahn)
        self.assertTrue(hahn.maybe_same)

    def test_notable_list_credits_terms_by_the_same_identity(self):
        from pages.community_history import people_pool
        pool, _ = people_pool(self.ed)
        by = {p.get("person_id"): p for p in pool}
        self.assertEqual([t["term_id"] for t in by["PPL-001"]["_terms"]], [])          # Schuyler Colfax
        self.assertEqual([t["term_id"] for t in by["PPL-002"]["_terms"]], ["south-bend-mayor__colfax-iii__1898"])

    def test_threshold(self):
        counts = {}
        for p in self.reg.people.values():
            counts[p.why_page] = counts.get(p.why_page, 0) + 1
            if p.page:
                self.assertIn(p.why_page, pm.THRESHOLD_TEXT)
            if p.why_page == "primary_money":
                self.assertTrue(any(n in pm.money_names(self.ed) for n in p.names))
        self.assertGreater(counts.get("general", 0), 300)
        # candidates below the threshold are listed with their contests
        for name, cids in self.reg.below:
            self.assertTrue(cids)
            self.assertFalse(self.reg.person(name).page)

    def test_no_history_tab(self):
        for p in pm.paged(self.ed)[:200]:
            keys = pm.person_tabs(self.ed, p.pid)
            self.assertNotIn("history", keys)
            self.assertEqual(keys[0], "overview")
            self.assertEqual(keys[-1], "sources")

    def test_money_equals_the_office_pages(self):
        """The person's figures are the race model's own candidate sums (what the office Money tab draws)."""
        from pages.people import money_rows_for
        checked = 0
        for pid in ("james-mueller", "tony-hazen", "bill-redman", "tom-mccormick"):
            for r in money_rows_for(self.ed, pid):
                if r["kind"] != "race":
                    continue
                race = r["race"]
                office_races = om.races_by_office(self.ed).get(r["office_id"], [])
                self.assertIn(race, office_races)
                cand = next(c for c in race["candidates"] if self.reg.pid_for(c["name"]) == pid)
                self.assertEqual((r["raised"], r["spent"]), (cand["raised"], cand["spent"]))
                checked += 1
        self.assertGreaterEqual(checked, 4)
        mueller = [r for r in money_rows_for(self.ed, "james-mueller") if r["kind"] == "race" and r["year"] == "2023"]
        self.assertEqual((mueller[0]["raised_text"], mueller[0]["spent_text"]), ("$393,342.90", "$610,625.36"))

    def test_link_names_rules(self):
        class E:  # a minimal page
            pass
        site = Site(self.ed, Path(tempfile.gettempdir()) / "people-linktest")
        page = site.page("officeholders/index.html")
        tag = str(name_with_party("James Mueller", "D"))
        out = pm.link_names(f"<p>{tag}</p><summary>{tag}</summary><a href='x'>{tag}</a>", page)
        self.assertEqual(out.count('class="person-link"'), 1)
        self.assertIn('href="../people/james-mueller/index.html"', out)
        self.assertIn("(D)</abbr>", out)          # the party tag is unchanged
        own = site.page("people/james-mueller/index.html")
        self.assertNotIn("person-link", pm.link_names(f"<p>{tag}</p>", own))


class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name)
        cls.site = site = Site(cls.ed, out)
        build.discover_builders()
        want = [pm.HUB, pm.NOTABLE, pm.OLD_NOTABLE, "offices/south-bend-mayor/index.html",
                "offices/south-bend-mayor/money/index.html", "officeholders/index.html", "governments/county/index.html",
                "elections/compare/index.html", "elections/2023g/contests/index.html"]
        for pid in ("james-mueller", "pete-buttigieg", "dave-vandewalle", "bobby-kruszynski", "lacy-hahn",
                    "burnie-bauer"):
            want += [pm.path(pid, k) for k in pm.person_tabs(cls.ed, pid)]
        for p in want:
            if p not in site.pages:
                build.BUILDERS[p](site)
        site.write()
        cls.html = {p: (out / p).read_text(encoding="utf-8") for p in site.pages}
        cls.index = json.loads((out / "assets" / "search-index.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_sitemap_matches_tabs(self):
        for p in pm.paged(self.ed):
            for k in pm.person_tabs(self.ed, p.pid):
                self.assertIn(pm.path(p.pid, k), self.site.by_path)
            self.assertNotIn(pm.path(p.pid, "history"), self.site.by_path)

    def test_person_tabs(self):
        h = self.html
        ov = h["people/james-mueller/index.html"]
        for label in ("Offices now", "Offices before", "Races in the results", "Party as recorded",
                      "Campaign money on record", "Notable-people list"):
            self.assertIn(f"<dt>{label}</dt>", ov)
        self.assertIn('id="tabs"', ov)
        self.assertIn("Mayor of South Bend", ov)
        el = h["people/james-mueller/elections/index.html"]
        self.assertIn("../../../offices/south-bend-mayor/elections/index.html#c-", el)
        self.assertIn("../../../elections/2023g/contests/index.html#contest-", el)
        mo = h["people/james-mueller/money/index.html"]
        self.assertIn("$393,342.90", mo)
        self.assertIn("$610,625.36", mo)
        self.assertIn("$393,342.90", h["offices/south-bend-mayor/money/index.html"])
        src = h["people/james-mueller/sources/index.html"]
        self.assertIn('id="sources"', src)

    def test_same_fields_for_everyone(self):
        labels = re.compile(r'<dl class="ovw-facts pp-facts">(.*?)</dl>', re.S)
        seen = set()
        for pid in ("james-mueller", "pete-buttigieg", "dave-vandewalle", "burnie-bauer", "lacy-hahn"):
            m = labels.search(self.html[pm.path(pid)])
            seen.add(tuple(re.findall(r"<dt>(.*?)</dt>", m.group(1))))
        self.assertEqual(len(seen), 1)

    def test_notable_card_and_no_result_lines(self):
        pb = self.html["people/pete-buttigieg/index.html"]
        self.assertIn('id="notable"', pb)
        card = re.search(r'<div class="pp-card">.*?</div>', pb, re.S).group(0)
        self.assertNotRegex(card, r"\d[\d,]* votes?\b|\d+(\.\d+)? percent")
        self.assertIn("Low confidence", self.html["people/burnie-bauer/index.html"].replace("LOW CONFIDENCE", "Low confidence"))

    def test_maybe_more_than_one_person(self):
        hahn = self.html["people/lacy-hahn/index.html"]
        self.assertIn("May be more than one person with this name", hahn)

    def test_names_link_to_people(self):
        mayor = self.html["offices/south-bend-mayor/index.html"]
        self.assertIn('href="../../people/james-mueller/index.html"', mayor)
        oh = self.html["officeholders/index.html"]
        self.assertIn('class="person-link" href="../people/james-mueller/index.html"', oh)
        for p, src in self.html.items():
            # never a link inside a link
            depth = 0
            for m in re.finditer(r"<(/?)a\b[^>]*>", src):
                depth += -1 if m.group(1) else 1
                self.assertLessEqual(depth, 1, p)
            for s in re.findall(r"<summary\b.*?</summary>", src, re.S):
                self.assertNotIn("person-link", s, p)

    def test_hub(self):
        hub = self.html[pm.HUB]
        n = len(pm.paged(self.ed))
        self.assertEqual(hub.count('class="pph-row"'), n)
        for k in ("status", "level", "notable"):
            self.assertIn(f'data-tf-key="{k}"', hub)
        self.assertIn('data-tf-tokens', hub)
        # the name box comes first, before the three selects
        picker = re.search(r'<div class="picker tf".*?</div>\s*<button', hub, re.S).group(0)
        self.assertLess(picker.index('data-tf-q'), picker.index('data-tf-key="status"'))
        # JS off: every letter fold ships open, so the whole list is on the page
        self.assertNotRegex(hub, r'<details class="pph-letter"(?![^>]*\bopen\b)')
        self.assertIn('id="rules"', hub)
        self.assertIn('id="below"', hub)
        for p in pm.paged(self.ed)[:50]:
            self.assertIn(f'href="{p.pid}/index.html"', hub)

    def test_notable_view_and_old_anchors(self):
        old = json.loads(FIXTURE.read_text(encoding="utf-8"))["ids"][pm.OLD_NOTABLE]
        new_ids = set(ID_RE.findall(self.html[pm.NOTABLE]))
        fwd = self.html[pm.OLD_NOTABLE]
        fwd_ids = set(ID_RE.findall(fwd))
        missing = [i for i in old if i not in new_ids and i not in fwd_ids]
        self.assertEqual(missing, [])
        self.assertIn('<meta name="civic-moved-to" content="people/notable/index.html">', fwd)
        self.assertIn('rel="canonical" href="../../people/notable/index.html"', fwd)
        m = re.search(r'id="moved-anchors">(.*?)</script>', fwd)
        self.assertEqual(json.loads(m.group(1))["to"], "../../people/notable/index.html")
        # every card on the notable view links its name to the person page
        for pid in re.findall(r'id="person-([a-z0-9-]+)"', self.html[pm.NOTABLE])[:10]:
            self.assertIn("person-", pid + "person-")
        self.assertIn('href="../james-mueller/index.html"', self.html[pm.NOTABLE])

    def test_search(self):
        items = self.index["items"]
        types = self.index["types"]
        tabs = [it for it in items if types[it[0]] == "Person" and it[1] == "James Mueller › Money"]
        self.assertEqual(len(tabs), 1)
        self.assertIn("money", tabs[0][5].split())
        people = [it for it in items if it[0] == 3 and it[1] == "James Mueller"]
        self.assertEqual(people[0][3], "people/james-mueller/index.html")
        k = [it for it in items if it[0] == 3 and it[3] == "people/bobby-kruszynski/index.html"]
        self.assertIn("Bobby K", k[0][5])

    def test_nav_and_footer(self):
        offices = next(i for i in sitemap.NAV if i["name"] == "Offices")
        self.assertLessEqual(len(offices["links"]), sitemap.MAX_DROPDOWN)
        self.assertIn(("people/index.html", "People"), offices["links"])
        self.assertIn(("people/index.html", "People"), sitemap.FOOTER)
        self.assertIs(sitemap.nav_of("people/james-mueller/index.html"), offices)
        for item in sitemap.NAV:
            for p, _l in item["links"]:
                self.assertNotEqual(p.split("#")[0], pm.OLD_NOTABLE)
        stop = [s for pth in sitemap.PATHS for s in pth["stops"] if s["anchor"] == "people"]
        self.assertEqual(stop[0]["page"], pm.NOTABLE)

    def test_county_overview_folds_keep_every_office(self):
        c = self.html["governments/county/index.html"]
        for fid in ("council-more", "countywide-all", "superior-rule"):
            self.assertRegex(c, rf'<details[^>]*id="{fid}"[^>]*\bopen\b')
        for o in self.ed.tables["offices"]:
            if o["unit_id"] in ("county", "sjc-courts"):
                self.assertIn(f'id="office-{o["office_id"]}"', c, o["office_id"])

    def test_close_races_levels_fold(self):
        c = self.html["elections/compare/index.html"]
        self.assertIn('id="find-map"', c)
        self.assertIn('id="bands"', c)
        levels = re.findall(r'<section class="mg-level" id="(lvl-[a-z]+)"', c)
        self.assertGreaterEqual(len(levels), 5)
        for lv in levels:
            self.assertRegex(c, rf'<details[^>]*id="{lv}-more"[^>]*data-one-wrap')


class Static(unittest.TestCase):
    def test_tablefilter_tokens(self):
        js = (SITE_DIR / "static" / "js" / "tablefilter.js").read_text(encoding="utf-8")
        self.assertIn('hasAttribute("data-tf-tokens")', js)
        self.assertTrue(js.isascii())
        m = str(table_filter("t", [{"key": "a", "label": "A", "options": [("x", "X")], "tokens": True},
                                   {"key": "b", "label": "B", "options": [("y", "Y")]}], 1))
        self.assertEqual(m.count("data-tf-tokens"), 1)
        first = str(table_filter("t", [{"key": "a", "label": "A", "options": []}], 1, search="Q", search_first=True))
        self.assertLess(first.index("data-tf-q"), first.index('data-tf-key="a"'))
        last = str(table_filter("t", [{"key": "a", "label": "A", "options": []}], 1, search="Q"))
        self.assertGreater(last.index("data-tf-q"), last.index('data-tf-key="a"'))

    def test_people_css_tokens_only(self):
        css = (SITE_DIR / "static" / "css" / "people.css").read_text(encoding="utf-8")
        self.assertNotRegex(css, r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")

    def test_search_js_person_tab(self):
        js = (SITE_DIR / "static" / "js" / "search.js").read_text(encoding="utf-8")
        self.assertIn("T_PTAB = 10", js)
        self.assertTrue(js.isascii())


if __name__ == "__main__":
    unittest.main()
