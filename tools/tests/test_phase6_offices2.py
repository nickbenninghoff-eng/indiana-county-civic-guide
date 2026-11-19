"""Phase 6, office pages part 2 (2026-11-16): Money tab controls and the primary/general split, HTML charts, the
Offices hub map and collapsed groups, older contests shipping open, one data date in the footer, the unmatched-contest
audit. Report: planning/qa/phase6-offices2-2026-11-16.md.

- The split at the pre-primary report uses only whole reports chosen by campaign_money.committee_summary; the two parts
  add up exactly to the whole-cycle figure; nothing is split where the filings don't allow it (2023: no pre-primary
  reports posted; a year-to-date basis; conflicting dates; overlapping reports).
- Money tab: controls ship hidden (JS off shows every chart); every chart says its phase; rows carry their party for
  the filter; never party colors.
- Hub: a map using the existing boundary files only, each area with its office list; offices with no boundary file are
  said to have none; groups ship open (folds.js closes them); JS off still lists all 127 offices.
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
SITE_DIR = ROOT / "tools" / "site"
sys.path.insert(0, str(SITE_DIR))

from civic import campaign_money as cm  # noqa: E402
from civic import offices as om  # noqa: E402
from civic.charts import money_rows, results_rows  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site  # noqa: E402


def _races(ed):
    from pages.campaigns import cf_all
    return cf_all(ed)["races"]


def _cand(ed, office_id, surname, cycle):
    for r in _races(ed):
        if r["cycle"] == cycle and om.race_office_id(ed, r) == office_id:
            for c in r["candidates"]:
                if cm.surname(c["name"]) == surname.lower():
                    return r, c
    raise AssertionError(f"no {surname} in {office_id} {cycle}")


# ====================================================================== the split (model)
class Split(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")

    def test_real_figures_through_the_pre_primary_report(self):
        # each figure is the "this period" column of the one pre-primary report in cf_local.csv (checked by hand)
        cases = [("county-recorder", "Banicki", "cfl-62638", 819331, 613281, "2024-04-19"),
                 ("county-commissioner-d3", "Hazen", "cfl-62641", 8635084, 7550904, "2024-04-12"),
                 ("county-council-f", "Figg", "cfl-62637", 1628427, 1258315, "2024-04-12"),
                 ("county-council-i", "Hizer", "cfl-62628", 2484869, 1837582, "2024-04-12"),
                 ("probate-court-judge", "Cichowicz", "cfl-62625", 507380, 401618, "2024-03-31")]
        for oid, name, doc, raised, spent, through in cases:
            _race, c = _cand(self.ed, oid, name, "2024")
            sp = om.candidate_split(c)
            self.assertTrue(sp["ok"], (oid, name, sp))
            self.assertEqual((sp["pre"]["raised"], sp["pre"]["spent"]), (raised, spent), (oid, name))
            self.assertEqual(sp["docs"], [doc])
            self.assertEqual(sp["through"], through)

    def test_after_the_pre_primary_report_is_the_later_reports(self):
        # Figg: pre-election cfl-64471 (250.00 / 3,917.19) + year-end annual cfl-65668 (500.00 / 0.00)
        _race, c = _cand(self.ed, "county-council-f", "Figg", "2024")
        sp = om.candidate_split(c)
        self.assertEqual(sp["post"], {"raised": 75000, "spent": 391719})
        # Hizer: his final report cfl-66179 (148.25 / 8,543.80)
        _race, c = _cand(self.ed, "county-council-i", "Hizer", "2024")
        self.assertEqual(om.candidate_split(c)["post"], {"raised": 14825, "spent": 854380})

    def test_parts_add_up_to_the_whole_cycle_for_every_split(self):
        n = 0
        for r in _races(self.ed):
            for c in r["candidates"]:
                sp = om.candidate_split(c)
                if sp["ok"]:
                    n += 1
                    for k in ("raised", "spent"):
                        self.assertEqual(sp["pre"][k] + sp["post"][k], c[k], (r["id"], c["name"], k))
        self.assertGreaterEqual(n, 40)

    def test_2023_is_never_split_and_says_why(self):
        for r in _races(self.ed):
            if r["cycle"] != "2023 municipal":
                continue
            rs = om.race_split(r)
            self.assertFalse(rs["any"], r["id"])
            if any(c["committees"] for c in r["candidates"]):
                self.assertEqual(rs["why"], "the county posted no 2023 pre-primary reports")

    def test_no_split_without_a_clean_cut(self):
        row = {"row": {"transcription_status": "verified", "receipts_period": "10", "expenditures_period": "5",
                       "period_to": "2024-04-12", "filing_id": "x"}, "slot": "pre-primary", "counted": True,
               "conflict": False}
        base = {"items": [row], "flags": set(), "spent": 500, "raised": 1000,
                "basis": [{"how": "periods"}, {"how": "periods"}]}
        self.assertTrue(om.committee_split(base)["ok"])
        self.assertIn("year-to-date", om.committee_split({**base, "basis": [{"how": "ytd"}]})["why"])
        self.assertIn("overlap", om.committee_split({**base, "flags": {"overlap"}, "spent": None})["why"])
        self.assertIn("disagree", om.committee_split({**base, "items": [{**row, "conflict": True}]})["why"])
        self.assertIn("miswritten", om.committee_split({**base, "flags": {"date-doubt"}})["why"])
        self.assertEqual(om.committee_split({**base, "items": [{**row, "slot": "pre-election"}]})["why"],
                         "no pre-primary report on file")
        self.assertIn("included in a later report",
                      om.committee_split({**base, "items": [{**row, "counted": False}]})["why"])
        # a split that would not add up is refused, never shown
        self.assertIn("don't add up", om.committee_split({**base, "raised": 999})["why"])


# ====================================================================== HTML charts
class Charts(unittest.TestCase):
    def test_money_rows_scale_words_and_party_attribute(self):
        rows = [{"name": "A", "sub": "Democrat (D)", "raised": 50000, "spent": None, "raised_text": "$500.00",
                 "spent_text": "not on file", "attrs": {"data-party": "D"}},
                {"name": "B", "sub": "Republican (R)", "raised": 100000, "spent": 25000, "attrs": {"data-party": "R"}}]
        f = str(money_rows("t", "T", rows, vmax=100000, extra={"data-mt-phase": "whole"}))
        self.assertIn('data-mt-phase="whole"', f)
        self.assertEqual(f.count('class="mrw-row'), 2)
        self.assertIn('data-party="D"', f)
        self.assertIn("width:50.00%", f)          # 500 of a 1,000 scale
        self.assertIn("width:100.00%", f)
        self.assertIn("not on file", f)
        self.assertNotRegex(f, r"m-party-")
        self.assertIn("<details", f)              # the table view

    def test_results_rows_fixed_scale(self):
        f = str(results_rows("r", "R", [{"name": "A", "party": "D", "pct": 72.8, "votes": 7878, "winner": "Y"},
                                        {"name": "B", "party": "R", "pct": None, "votes": None, "winner": ""}]))
        self.assertIn("width:72.80%", f)
        self.assertIn("votes not recorded", f)
        self.assertIn("Democrat (D) · Elected", f)


# ====================================================================== built pages
class Pages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.out = Path(tempfile.mkdtemp(prefix="phase6-offices2-"))
        cls.site = Site(cls.ed, cls.out)
        from pages import offices as po
        cls.po = po
        cls.pages = {}
        for oid, tab in (("south-bend-mayor", "money"), ("county-recorder", "money"), ("state-house-5", "money"),
                         ("south-bend-mayor", "elections")):
            cls.pages[(oid, tab)] = str(po.build_office(oid, cls.site, tab).render())
        cls.hub = str(po.build_hub(cls.site).render())

    def money(self, oid):
        return self.pages[(oid, "money")]

    def test_controls_ship_hidden_and_every_chart_says_its_phase(self):
        for oid in ("south-bend-mayor", "county-recorder", "state-house-5"):
            h = self.money(oid)
            self.assertRegex(h, r'<div class="mt-ctl" id="mt-ctl" hidden')
            for k in ("both", "primary", "general"):
                self.assertIn(f'data-mt-show="{k}"', h)
            self.assertIn('<select id="mt-party"', h)
            # JS off: no chart, election or candidate is hidden
            self.assertNotRegex(h, r'<(figure|section)[^>]*\shidden')
        figs = re.findall(r'<figure class="chart chart-money-rows"[^>]*>', self.money("south-bend-mayor"))
        self.assertTrue(figs)
        for f in figs:
            self.assertRegex(f, r'data-mt-phase="(whole|primary|general)"')

    def test_party_filter_options_are_the_parties_on_the_page(self):
        h = self.money("south-bend-mayor")
        sel = h[h.index('<select id="mt-party"'):h.index("</select>", h.index('<select id="mt-party"'))]
        self.assertEqual(re.findall(r'<option value="([^"]*)"', sel), ["", "D", "R"])
        rows = re.findall(r'<li class="mrw-row"[^>]*data-party="([^"]+)"', h)
        self.assertTrue(rows)
        self.assertEqual(set(rows), {"D", "R"})

    def test_recorder_2024_is_split_and_mayor_2023_says_why_not(self):
        h = self.money("county-recorder")
        self.assertIn('data-mt-split="1"', h)
        self.assertIn("Democratic primary candidates: through the pre-primary report", h)
        self.assertIn("$8,193.31", h)              # Banicki, cfl-62638
        m = self.money("south-bend-mayor")
        self.assertNotIn('data-mt-split="1"', m)
        self.assertIn("Not split into primary and general: the county posted no 2023 pre-primary reports.", m)
        self.assertIn('data-mt-why-primary="whole-cycle figures only', m)

    def test_money_charts_never_use_party_colors(self):
        for oid in ("south-bend-mayor", "county-recorder"):
            for f in re.findall(r'<figure class="chart[^"]*".*?</figure>', self.money(oid), re.S):
                self.assertNotRegex(f, r"m-party-")

    def test_older_contests_ship_open(self):
        h = self.pages[("south-bend-mayor", "elections")]
        folds = re.findall(r'<details class="er-fold"[^>]*>', h)
        self.assertGreater(len(folds), 10)
        for f in folds:
            self.assertIn(" open", f)
            self.assertIn('data-fold="contest"', f)

    # ------------------------------------------------------------------ hub
    def test_hub_map_layers_and_panel_lists(self):
        h = self.hub
        self.assertIn('id="offices-map"', h)
        for tab, _label in self.po.HUB_LAYERS:
            self.assertIn(f'data-layer="{tab}"', h)
        data = json.loads(re.search(r'<script type="application/json" id="cmap-data">(.*?)</script>', h, re.S).group(1))
        hrefs = [d["href"] for d in data.values()]
        self.assertEqual(len(hrefs), len(set(hrefs)))          # offices.js finds the area from its link
        blocks = dict(re.findall(r'<div class="ofm-block" data-ofm-uid="([^"]+)">(.*?)</ul></div>', h, re.S))
        self.assertEqual(set(blocks), set(data))
        listed = set()
        for b in blocks.values():
            listed |= set(re.findall(r'class="ofm-office" href="([a-z0-9-]+)/index.html"', b))
        # 2026-11-18: Indiana House District 48 is a district of the 2001-2011 map (contests 2010 only); it has no area
        # on today's map, so no panel lists it; it stays in the list below the map like every office
        old_plan = {o["office_id"] for o in self.ed.tables["offices"]
                    if o["unit_id"] in ("in-house", "in-senate") and "2001-2011 map" in o["title"]}
        self.assertEqual(old_plan, {"state-house-48"})
        self.assertEqual(listed, {o["office_id"] for o in self.ed.tables["offices"]} - old_plan)
        self.assertRegex(h, r'<li class="ofh-row"[^>]*>.*?state-house-48/index\.html')
        # seats with no boundary file are said to have none; drawn districts point to their layer
        self.assertIn("No drawn boundary in the guide", blocks["walkerton"])
        self.assertIn("No drawn boundary in the guide", blocks["sbcsc"])
        self.assertIn("Drawn on the map layer", blocks["south-bend"])
        self.assertIn("county-council-a", "".join(data))

    def test_hub_groups_ship_open_and_list_every_office(self):
        h = self.hub
        groups = re.findall(r'<details class="ofh-gov"[^>]*>', h)
        self.assertEqual(len(groups), len({o["unit_id"] for o in self.ed.tables["offices"]}))
        for g in groups:
            self.assertIn(" open", g)
            self.assertIn('data-fold="gov"', g)
            self.assertIn("data-tf-group", g)
        rows = re.findall(r'<li class="ofh-row"[^>]*>', h)
        self.assertEqual(len(rows), len(self.ed.tables["offices"]))   # 139 since 2026-11-18
        self.assertTrue(all("data-here-layer" in r for r in rows))
        self.assertRegex(h, r'<p class="here-pre ofh-pre" id="ofh-pre" hidden')

    def test_footer_states_the_data_date_once(self):
        foot = self.hub[self.hub.index("<footer"):]
        self.assertEqual(foot.count("Data as of"), 1)


# ====================================================================== scripts and audit
class Static(unittest.TestCase):
    def test_offices_js_is_ascii(self):
        (SITE_DIR / "static" / "js" / "offices.js").read_bytes().decode("ascii")

    def test_no_control_or_stray_bytes_in_offices_assets(self):
        # 2026-11-16: a NUL byte written into offices.css (a botched "\00b7" escape) showed as a replacement glyph
        # and "b7" between the holder and "Next election" in the hub map panel
        for name in ("css/offices.css", "js/offices.js"):
            b = (SITE_DIR / "static" / name).read_bytes()
            b.decode("ascii")
            self.assertNotRegex(b.decode("ascii"), r"[\x00-\x08\x0b\x0c\x0e-\x1f]", name)
        css = (SITE_DIR / "static" / "css" / "offices.css").read_text(encoding="ascii")
        self.assertIn('.ofm-next::before { content: " \\B7  "; }', css)

    def test_built_hub_has_no_replacement_glyph(self):
        ed = Edition.load(ROOT, "st-joseph")
        site = Site(ed, Path(tempfile.mkdtemp(prefix="phase6-offices2-hub-")))
        from pages import offices as po
        h = str(po.build_hub(site).render())
        self.assertNotIn("�", h)
        self.assertNotIn("\x00", h)
        self.assertNotRegex(h, r"\bb7 Next election")
        built = ROOT / "site" / "st-joseph" / "offices" / "index.html"
        if built.is_file():
            bh = built.read_text(encoding="utf-8")
            self.assertNotIn("�", bh)
            self.assertNotRegex(bh, r"\bb7 Next election")

    def test_unmatched_audit_lists_every_unmatched_contest(self):
        ed = Edition.load(ROOT, "st-joseph")
        doc = (ROOT / "planning" / "qa" / "phase6-unmatched-contests-2026-11-16.md").read_text(encoding="utf-8")
        unmatched = [c["contest_id"] for c in ed.contests.values() if not c["office_id"]]
        listed = re.findall(r"^\| \d+ \| `([^`]+)`", doc, re.M)
        # every contest still unmatched is in the audit
        self.assertEqual(sorted(set(unmatched) - set(listed)), [])
        # 2026-11-18 (gap-fill round 2): the audit's contests that now have an office are matched to the offices that
        # round added (State House 48, the statewide offices and appellate courts, U.S. House) or to the two Superior
        # Court seats whose 2026 retentions the canvass printed under a state line (civic/data.py _state_aliases)
        new_units = {"in-house", "in-state", "us-house", "us-senate", "sjc-courts"}
        for cid in sorted(set(listed) - set(unmatched)):
            oid = ed.contests[cid]["office_id"]
            self.assertIn(ed.offices[oid]["unit_id"], new_units, cid)


if __name__ == "__main__":
    unittest.main()
