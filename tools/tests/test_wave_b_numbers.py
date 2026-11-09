"""Tests for Wave B batch 2 (2026-11-09): "Elections by the numbers" split into an overview (elections/landscape/),
elections/margins/, elections/turnout/ and officeholders/; "Up next" merged into elections/calendar/; the results page's
turnout table moved to elections/turnout/.

Pins every id the old pages had (tools/tests/fixtures/anchors_before_wave_b2.json, taken from the built site before
the batch): each is still on its page or forwarded by the page's #moved-anchors map (static/js/moved.js) to a page
that has the target id.

Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import html
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
from civic import sitemap  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site  # noqa: E402
from pages import elections as E  # noqa: E402
from pages import elections_numbers as N  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "anchors_before_wave_b2.json"
ID_RE = re.compile(r'\sid="([^"]+)"')
HREF_RE = re.compile(r'<a\b[^>]*\shref="([^"]+)"')
LAND, MARG, TURN, OFF, CAL, RES = ("elections/landscape/index.html", "elections/margins/index.html",
                                   "elections/turnout/index.html", "officeholders/index.html",
                                   "elections/calendar/index.html", "elections/results/index.html")
PAGES = [LAND, MARG, TURN, OFF, CAL, RES]


def moved_map(page_html: str) -> dict:
    m = re.search(r'id="moved-anchors">(.*?)</script>', page_html)
    return json.loads(m.group(1).replace("<\\/", "</"))["a"] if m else {}


def resolve(page: str, rel: str) -> tuple[str, str]:
    path, _, frag = rel.partition("#")
    return posixpath.normpath(posixpath.join(posixpath.dirname(page), path)), frag


class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name)
        site = Site(cls.ed, out)
        build.discover_builders()
        for p in PAGES:
            build.BUILDERS[p](site)
        site.write()
        cls.html = {p: (out / p).read_text(encoding="utf-8") for p in PAGES}
        cls.ids = {p: set(ID_RE.findall(h)) for p, h in cls.html.items()}
        cls.races = N.margin_races(cls.ed)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # ------------------------------------------------------------------ anchors
    def test_every_old_anchor_still_resolves(self):
        """Each old id is on its page, or the page's moved map sends it to a built page that has the target id."""
        before = json.loads(FIXTURE.read_text(encoding="utf-8"))["ids"]
        lost = []
        for page, ids in before.items():
            moved = moved_map(self.html[page])
            for i in ids:
                if i in self.ids[page]:
                    continue
                dest = moved.get(i)
                if dest:
                    target, frag = resolve(page, dest)
                    if target in self.ids and (frag or i) in self.ids[target]:
                        continue
                lost.append((page, i, dest))
        self.assertEqual(lost, [])

    def test_moved_maps_point_at_real_ids_only(self):
        for page in (LAND, RES):
            moved = moved_map(self.html[page])
            self.assertTrue(moved, page)
            for old, dest in moved.items():
                self.assertNotIn(old, self.ids[page], (page, old))          # only ids that left the page
                target, frag = resolve(page, dest)
                self.assertIn(target, self.ids, dest)
                self.assertIn(frag or old, self.ids[target], (page, old, dest))

    def test_overview_keeps_card_anchors(self):
        """Old links to the four measures still land on the overview's summary cards, with JS off too."""
        for a in ("turnout", "margins", "up-next", "how-took-office", "turnout-h", "margins-h", "up-next-h",
                  "how-took-office-h", "rules"):
            self.assertIn(a, self.ids[LAND])

    def test_calendar_keeps_its_ids(self):
        before = json.loads(FIXTURE.read_text(encoding="utf-8"))["ids"][CAL]
        self.assertEqual([i for i in before if i not in self.ids[CAL]], [])
        for y in E.YEARS:
            self.assertIn(f"year-{y}", self.ids[CAL])
            self.assertIn(f"y{y}", self.ids[CAL])           # strip cards (related.py links to #y<year>)

    def test_path_6_stops_land(self):
        p = next(x for x in sitemap.PATHS if x["id"] == "elections-by-the-numbers")
        for s in p["stops"]:
            if s["page"] in self.ids:
                self.assertIn(s["anchor"], self.ids[s["page"]], s)
        self.assertEqual([s["page"] for s in p["stops"][:4]], [TURN, MARG, CAL, OFF])

    def test_no_duplicate_ids(self):
        for p, h in self.html.items():
            ids = ID_RE.findall(h)
            dup = sorted({i for i in ids if ids.count(i) > 1})
            self.assertEqual(dup, [], p)

    # ------------------------------------------------------------------ margins page
    def test_counts_add_up_and_open_with_uncontested(self):
        h = self.html[MARG]
        n = {k: sum(1 for r in self.races if r["kind"] == k) for k in ("unc", "nc")}
        contested = len(self.races) - n["unc"] - n["nc"]
        lede = re.search(r'<p class="mg-lede">(.*?)</p>', h, re.S).group(1)
        self.assertIn(f"{n['unc']:,} of the {len(self.races):,} races", html.unescape(re.sub(r"<[^>]+>", "", lede)))
        self.assertIn("badge-computed", lede)                          # COMPUTED badge beside the first fact
        self.assertLess(h.index('class="mg-lede"'), h.index('id="by-level"'))
        self.assertIn(f"{len(self.races):,} = {n['unc']:,} uncontested + {contested:,} contested + {n['nc']:,} not measurable",
                      html.unescape(h))
        table = h[h.index('id="margins-table"'):]
        table = table[:table.index("</table>")]
        self.assertEqual(table.count("<tr data-margin="), contested)

    def test_every_race_is_in_the_find_list_and_links_to_its_result(self):
        h = self.html[MARG]
        find = h[h.index('id="mg-find"'):h.index('id="all-races"')]
        linked = set(re.findall(r'href="\.\./results/index\.html#contest-([A-Za-z0-9-]+)"', find))
        self.assertEqual(linked, {r["c"]["contest_id"] for r in self.races})
        for cid in linked:
            self.assertIn(f"contest-{cid}", self.ids[RES])

    def test_map_areas_link_to_open_folds(self):
        h = self.html[MARG]
        hrefs = re.findall(r'<a href="#(area-[a-z0-9-]+)" class="cmap-a"', h)
        self.assertGreater(len(hrefs), 40)
        for a in hrefs:
            self.assertIn(a, self.ids[MARG])
        folds = re.findall(r'<details class="fold-details one-fold mg-area-fold"[^>]*>', h)
        self.assertEqual(len(folds), len({r["area"] for r in self.races}))
        for f in folds:
            self.assertIn(" open", f)                                   # JS off: every area is open

    def test_no_party_colors_or_party_filter(self):
        for p in (MARG, LAND, TURN):
            h = self.html[p]
            self.assertNotRegex(h, r'class="[^"]*m-party', p)
            self.assertNotIn('data-tf-key="party"', h, p)
        self.assertNotRegex(self.html[MARG], r'data-tf-text="[^"]*primary\)')

    def test_find_filters_cover_office_place_district(self):
        h = self.html[MARG]
        bar = re.search(r'<div class="picker tf"[^>]*data-tf-table="mg-find"[^>]*>', h).group(0)
        self.assertIn(" hidden", bar)
        self.assertIn('data-tf-deep', h[h.index('id="mg-find"') - 80:h.index('id="mg-find"') + 80])
        for k in ("office", "place", "district"):
            sel = re.search(r'<select id="tf-mg-find-%s".*?</select>' % k, h, re.S).group(0)
            opts = {html.unescape(v) for v in re.findall(r'<option value="([^"]+)"', sel)}
            vals = {html.unescape(v) for v in re.findall(r'class="mg-seat" data-tf-row data-tf-office="[^"]*" '
                                                          r'data-tf-place="[^"]*" data-tf-district="([^"]*)"', h)} \
                if k == "district" else {html.unescape(v) for v in re.findall(r'class="mg-seat"[^>]*data-tf-%s="([^"]*)"' % k, h)}
            self.assertTrue(vals - {""} <= opts, (k, vals - opts))

    def test_bands_and_scope_unchanged(self):
        self.assertEqual([b[0] for b in E.BANDS], ["under-5", "5-15", "over-15"])
        self.assertEqual(N.SCOPE_OUT, ("Straight-party ballots", "Public questions", "Superior Court retention"))
        for r in self.races:
            g, _, cross = E.classify(r["c"])
            self.assertFalse(cross)
            self.assertNotIn(g, N.SCOPE_OUT)
        self.assertEqual([g for g, _ in N.MARGIN_GROUPS],
                         ["County row offices", "County commissioners", "County council", "County courts", "City offices",
                          "Town offices", "Township offices", "School boards", "State legislature"])

    # ------------------------------------------------------------------ other pages
    def test_turnout_page(self):
        h = self.html[TURN]
        els = E._elections(self.ed)
        table = h[h.index('id="turnout-denominators"'):]
        self.assertEqual(table[:table.index("</table>")].count("<tr>") - 1, len(els))   # header row + one per election
        self.assertIn('id="turnout-denominators-all"', h)
        for e in els:
            if e["type"] == "general" and int(e["date"][:4]) in E._straight_party_years(self.ed) and e.get("straight_party_d"):
                self.assertIn(f'id="straight-{e["election_id"]}"', h)

    def test_results_turnout_points_to_turnout_page(self):
        h = self.html[RES]
        sec = h[h.index('id="turnout"'):h.index('id="by-office"')]
        self.assertNotIn('id="turnout-table"', h)
        self.assertIn("../turnout/index.html", sec)
        self.assertIn('id="turnout-general"', sec)

    def test_officeholders_page(self):
        h = self.html[OFF]
        cur = N._current_holders(self.ed)
        self.assertEqual(len(re.findall(r'<li [^>]*class="oh-row"', h)), len(cur))
        table = h[h.index('id="took-office-list"'):]
        self.assertEqual(table[:table.index("</table>")].count("<tr data-tf-level"), len(cur))
        self.assertIn(f"{len(cur)} people holding elected offices", h)
        for f in re.findall(r'<details class="fold-details one-fold"[^>]*id="gov-[^"]*"[^>]*>', h):
            self.assertIn(" open", f)

    def test_calendar_up_next_rows(self):
        h = self.html[CAL]
        self.assertIn('id="up-next-table"', h)
        rows = h[h.index('id="up-next-table"'):]
        rows = rows[:rows.index("</table>")]
        years = re.findall(r'<tr [^>]*data-tf-year="(\d{4})"', rows)
        self.assertTrue(years and set(years) == {"2027", "2028"})
        y27 = h[h.index('id="year-2027"'):h.index('id="year-2028"')]
        self.assertIn("Now: ", y27)
        self.assertIn("Term limit: ", y27)
        y30 = h[h.index('id="year-2030"'):h.index('id="up-next-table-all"')]
        self.assertNotIn("Now: ", y30)                              # holders only for the next two ballots

    def test_b5_sentence(self):
        h = self.html[LAND]
        rules = h[h.index('id="rules"'):]
        self.assertNotIn("No precinct maps", rules)
        self.assertIn("map/index.html#list-votes", rules)
        self.assertIn("How areas voted", rules)


class Margin(unittest.TestCase):
    """margin(): an unnamed write-in total is not a candidate; ties; uncontested before missing votes."""

    @staticmethod
    def contest(rows, vote_for="1"):
        out = []
        for name, votes, win in rows:
            out.append({"candidate": name, "party": "" if name.startswith("Write") else "X", "votes": votes, "pct": "",
                        "winner": win, "confidence": "high", "notes": "", "status": "official"})
        return {"rows": out, "vote_for": vote_for, "contest_id": "t", "election_id": "2012g", "label": "T"}

    def test_writein_total_is_not_a_candidate(self):
        self.assertIsNone(E.margin(self.contest([("Jane Doe", "1428", "Y"), ("Write-in", "21", "")])))
        self.assertTrue(E.is_writein_total({"candidate": "Write-ins"}))
        self.assertFalse(E.is_writein_total({"candidate": "Michael Schalk (write-in)"}))

    def test_named_writein_is_a_candidate(self):
        m = E.margin(self.contest([("Traci Newman", "73", "Y"), ("Michael Schalk (write-in)", "31", "N")]))
        self.assertAlmostEqual(m["pts"], 100 * 42 / 104)

    def test_writein_votes_count_in_the_total(self):
        m = E.margin(self.contest([("A", "60", "Y"), ("B", "30", "N"), ("Write-in", "10", "")]))
        self.assertAlmostEqual(m["pts"], 30.0)
        self.assertTrue(m["writein"])

    def test_tie(self):
        m = E.margin(self.contest([("Kyle Norris", "55", "Y"), ("Bryan Vandall", "55", "N")]))
        self.assertTrue(m["tie"])
        self.assertEqual(m["pts"], 0)
        self.assertIn("Tied", N._who(m, True))
        self.assertIn("marks Kyle Norris as elected", N._who(m, True))

    def test_multi_seat(self):
        m = E.margin(self.contest([("A", "50", "Y"), ("B", "40", "Y"), ("C", "35", "N")], vote_for="2"))
        self.assertEqual((m["ahead"]["name"], m["next"]["name"]), ("B", "C"))
        self.assertIn("Last inside the 2 seats", N._who(m))

    def test_uncontested_even_with_missing_votes(self):
        self.assertIsNone(E.margin(self.contest([("A", "", "Y"), ("B", "", "Y")], vote_for="2")))
        self.assertEqual(E.margin(self.contest([("A", "", "Y"), ("B", "5", "N")]))["reason"], "votes missing")
        self.assertEqual(E.margin(self.contest([("A", "5", "Y"), ("B", "4", "N")], vote_for=""))["reason"],
                         "seat count not in data")
        self.assertIsNone(E.margin(self.contest([("A", "5", "Y")], vote_for="")))


class Static(unittest.TestCase):
    def read(self, rel):
        return (SITE_DIR / rel).read_text(encoding="utf-8")

    def test_scripts_ascii_no_innerhtml(self):
        for rel in ("static/js/moved.js", "static/js/tablefilter.js", "static/js/elections.js"):
            src = self.read(rel)
            self.assertTrue(all(ord(c) < 128 for c in src), rel)
            self.assertNotIn("innerHTML", src, rel)

    def test_moved_js_handles_new_ids_and_path_stops(self):
        src = self.read("static/js/moved.js")
        self.assertIn('dest.indexOf("#") >= 0', src)
        self.assertIn("paths-data", src)

    def test_tablefilter_deep_mode(self):
        src = self.read("static/js/tablefilter.js")
        self.assertIn('hasAttribute("data-tf-deep")', src)
        self.assertIn("[data-tf-group]", src)

    def test_area_helpers(self):
        self.assertEqual(N.area_level("countywide"), "county")
        self.assertEqual(N.area_level("south-bend-council-3"), "city")
        self.assertEqual(N.area_level("school-city-mishawaka"), "school")
        self.assertEqual(N.area_level("clay-township"), "township")
        self.assertEqual(N.area_level("house-5"), "legislature")
        self.assertEqual(N.seat_district({"label": "St. Joseph County Commissioner, 2nd (Democratic primary)"}, None),
                         "District 2")
        self.assertEqual(N.seat_district({"label": "Town of Osceola: Town Council, Ward 1"}, None), "Ward 1")


if __name__ == "__main__":
    unittest.main()
