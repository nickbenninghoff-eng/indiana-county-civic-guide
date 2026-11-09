"""Tests for Wave E batch 8 (2026-11-09): pages open on the reader's saved place (review pattern P4;
planning/qa/wave-e-batch8-2026-11-09.md).

  - civic/preselect.py: layer keys for every unit, the hidden placeholder, the county districts derived from the
    guide's precinct results (only where a single district is certain), and the taxing district of a saved place
    (only when exactly one district fits, never guessed);
  - the eight pages ship the placeholder hidden and empty (JavaScript off: nothing changes) and expose the keys the
    script needs (rows, groups, payloads), all valid;
  - static/js: the saved place is never written into the address or sent anywhere; money.js stores the tax-bill
    choice only when the reader changes it; the JS district rule gives the same answers as the Python one (run with
    node when it is installed).

Builds the pages into a temporary folder.
Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "site"))

import build  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.map import load_votes  # noqa: E402
from civic.preselect import (county_districts, district_hints, here_layer, here_slot,  # noqa: E402
                             tax_district_choice, tax_district_for_saved)
from civic.shell import Site  # noqa: E402

JS = ROOT / "tools" / "site" / "static" / "js"
CAL, OH, RES, JQ, TAX, COUNTY, SCHOOLS, PEOPLE = (
    "elections/calendar/index.html", "officeholders/index.html", "elections/results/index.html",
    "elections/judges-and-questions/index.html", "money/your-tax-bill/index.html", "county/index.html",
    "schools/index.html", "community/people/index.html")
PAGES = [CAL, OH, RES, JQ, TAX, COUNTY, SCHOOLS, PEOPLE]
SLOT_RE = re.compile(r'<p class="here-pre"([^>]*)>(.*?)</p>', re.S)


def _json(html: str, sid: str):
    m = re.search(r'<script type="application/json" id="' + re.escape(sid) + r'">(.*?)</script>', html, re.S)
    return json.loads(m.group(1)) if m else None


class PreselectTests(unittest.TestCase):
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
        cls.votes = load_votes(cls.ed)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # ------------------------------------------------------------------ helpers in civic/preselect.py
    def valid_layers(self):
        ok = {"county", "state", "library"}
        for u in self.ed.units.values():
            if u["unit_type"] in ("city", "town"):
                ok.add(f"municipality:{u['unit_id']}")
            elif u["unit_type"] == "township":
                ok.add(f"township:{u['unit_id']}")
            elif u["unit_type"] == "school_corporation":
                ok.add(f"school:{u['unit_id']}")
        return ok

    def test_here_layer(self):
        ed = self.ed
        self.assertEqual(here_layer(ed, "county"), "county")
        self.assertEqual(here_layer(ed, "sjc-courts"), "county")
        self.assertEqual(here_layer(ed, "sjc-airport-authority"), "county")
        self.assertEqual(here_layer(ed, "south-bend"), "municipality:south-bend")
        self.assertEqual(here_layer(ed, "south-bend-housing-authority"), "municipality:south-bend")
        self.assertEqual(here_layer(ed, "penn-township"), "township:penn-township")
        self.assertEqual(here_layer(ed, "phm"), "school:phm")
        self.assertEqual(here_layer(ed, "sjcpl"), "library")
        self.assertEqual(here_layer(ed, "in-house"), "state")
        self.assertEqual(here_layer(ed, "no-such-unit"), "")
        for uid in ed.units:
            self.assertIn(here_layer(ed, uid), self.valid_layers() | {""}, uid)

    def test_slot_ships_hidden_and_empty(self):
        s = str(here_slot("filter", "cal-years"))
        self.assertIn(" hidden", s)
        self.assertRegex(s, r'^<p class="here-pre" data-here-pre="filter" data-here-for="cal-years" hidden></p>$')
        with self.assertRaises(ValueError):
            here_slot("tabs", "x")

    def test_county_districts_only_where_certain(self):
        d = county_districts(self.ed, self.votes)
        self.assertEqual(d["unincorporated-greene-township"]["keys"], ["county-commissioner-d1", "county-council-a"])
        self.assertEqual(d["walkerton"]["keys"], ["county-commissioner-d3", "county-council-f"])
        # places that cross district lines in the precinct results get nothing
        for pid in ("south-bend", "mishawaka", "unincorporated-penn-township", "unincorporated-centre-township",
                    "unincorporated-clay-township", "unincorporated-portage-township"):
            self.assertNotIn(pid, d, pid)
        for v in d.values():
            self.assertEqual(len(v["keys"]), 2)
            for k in v["keys"]:
                self.assertIn(k, self.ed.offices)
            self.assertGreater(v["precincts"], 0)

    def test_county_districts_conservative_on_unplaced_and_straddlers(self):
        votes = copy.deepcopy(self.votes)
        race = next(r for r in votes["races"] if r["office"] == "county-commissioner" and r["district"] == "1"
                    and r["year"] >= 2022)
        # an unplaced precinct naming Walkerton in another district's race: Walkerton is no longer certain
        other = next(r for r in votes["races"] if r["office"] == "county-commissioner" and r["district"] == "2"
                     and r["year"] >= 2022)
        votes["unplaced"].setdefault(other["id"], []).append({"code": "999999", "name": "Walkerton", "votes": 5})
        d = county_districts(self.ed, votes)
        self.assertNotIn("walkerton", d)
        # a straddling precinct in Greene Township voting in another district: Greene is no longer certain
        votes = copy.deepcopy(self.votes)
        votes["precinct"]["999998"] = {"n": "test", "t": "greene-township", "p": "south-bend", "ps": 0.5, "e": [2024],
                                       "v": {other["id"]: [1, 1, 0, 0, 0]}}
        self.assertNotIn("unincorporated-greene-township", county_districts(self.ed, votes))
        self.assertIn("unincorporated-greene-township", county_districts(self.ed, self.votes))
        self.assertTrue(race)
        self.assertEqual(county_districts(self.ed, None), {})

    def test_county_page_ships_the_same_map(self):
        data = _json(self.html[COUNTY], "here-districts")
        self.assertEqual(data["places"], json.loads(json.dumps(county_districts(self.ed, self.votes))))
        self.assertEqual(data["years"], "2022 and 2024")

    # ------------------------------------------------------------------ taxing district
    def tax(self):
        data = _json(self.html[TAX], "taxbill-data")
        return data, data["districts"], data["hints"]

    def test_tax_district_cases(self):
        data, dl, hints = self.tax()
        self.assertEqual(hints, district_hints(dl, data["uidmap"]))
        T = lambda *a: tax_district_choice(dl, hints, *a)
        self.assertEqual(T("unincorporated-penn-township", "penn-township", "phm"), {"code": "031"})
        self.assertEqual(T("unincorporated-penn-township", "penn-township", "any"),
                         {"choices": ["031", "032"], "why": "school"})
        self.assertEqual(T("mishawaka", "penn-township", "phm"), {"code": "022"})
        self.assertEqual(T("mishawaka", "penn-township", "school-city-mishawaka"), {"code": "023"})
        self.assertEqual(T("south-bend", "any", "sbcsc"),
                         {"choices": ["002", "004", "009", "026", "037"], "why": "township"})
        # South Bend in Penn Township is PHM in the state's listing: a saved SBCSC is a conflict, not a guess
        self.assertEqual(T("south-bend", "penn-township", "sbcsc"), {"choices": ["033"], "why": "conflict"})
        self.assertEqual(T("walkerton", "lincoln-township", "john-glenn"), {"code": "015"})
        self.assertEqual(T("unincorporated-greene-township", "greene-township", "any"), {"code": "010"})
        self.assertEqual(T("no-such-place", "any", "any"), {})

    def saved_cases(self):
        """Every saved place the picker can store, as (place id, place, township, school, township chosen, school
        chosen): township and school either chosen by the reader ("set") or filled in by here.js as the guide's
        defaults (not in "set"), or "any"."""
        H = _json(self.html[TAX], "here-data")
        out = []
        for pid, p in H["places"].items():
            towns = [p["t"]] if p["t"] else ["any"] + list(p["it"] or H["townships"])
            for t in towns:
                for s in ["any"] + list(H["schools"]):
                    t_opts = [False] if (p["t"] or t == "any") else [False, True]
                    s_opts = [False] if s == "any" else [False, True]
                    for te in t_opts:
                        for se in s_opts:
                            out.append((pid, p, t, s, te, se))
        return out

    @staticmethod
    def explicit(p, t, s, te, se):
        """What the preselect may rely on: an unincorporated place's own township, and what the reader chose; the
        rest are defaults."""
        et = p["t"] or (t if te else "any")
        es = s if se else "any"
        dt = "" if (p["t"] or te or t == "any") else t
        ds = "" if (se or s == "any") else s
        return et, es, dt, ds

    def test_tax_district_never_guesses(self):
        """A district is picked only when it is the only district the place's name gives that fits the township and
        school the reader CHOSE. Defaults filled in by here.js never cause a pick: they only order the choices."""
        data, dl, hints = self.tax()
        for pid, p, t, s, te, se in self.saved_cases():
            et, es, dt, ds = self.explicit(p, t, s, te, se)
            r = tax_district_for_saved(dl, hints, pid, et, es, dt, ds)
            fit = [d["code"] for d in dl if d["pre"]["place"] == pid
                   and (et == "any" or not hints[d["code"]]["tw"] or et in hints[d["code"]]["tw"])
                   and (es == "any" or not hints[d["code"]]["sc"] or es in hints[d["code"]]["sc"])]
            if "code" in r:
                self.assertEqual(fit, [r["code"]], (pid, t, s, te, se))
            elif "choices" in r and r["why"] != "conflict":
                self.assertEqual(sorted(r["choices"]), sorted(fit), (pid, t, s, te, se))
                self.assertEqual(r["choices"][:len(r["fit_default"])], r["fit_default"])
            # the same saved place with the defaults dropped gives the same decision
            r0 = tax_district_for_saved(dl, hints, pid, et, es)
            self.assertEqual(r.get("code"), r0.get("code"), (pid, t, s, te, se))

    def test_mishawaka_default_vs_explicit_school(self):
        data, dl, hints = self.tax()
        # Mishawaka chosen, school left at the city's usual one (a default): choices, School City's 023 listed first
        r = tax_district_for_saved(dl, hints, "mishawaka", "any", "any", "", "school-city-mishawaka")
        self.assertNotIn("code", r)
        self.assertEqual(sorted(r["choices"]), ["005", "022", "023", "036"])
        self.assertEqual(r["choices"][0], "023")
        self.assertEqual(r["fit_default"], ["023"])
        # the reader chose School City of Mishawaka: only 023 fits in the state's listing
        self.assertEqual(tax_district_for_saved(dl, hints, "mishawaka", "any", "school-city-mishawaka"), {"code": "023"})
        # the reader chose PHM: 022 (Penn) and 036 (Harris) both fit -> choices, never a pick
        r = tax_district_for_saved(dl, hints, "mishawaka", "any", "phm")
        self.assertEqual(sorted(r["choices"]), ["022", "036"])
        self.assertEqual(r["why"], "township")
        self.assertEqual(tax_district_for_saved(dl, hints, "mishawaka", "penn-township", "phm"), {"code": "022"})

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_js_rule_matches_python(self):
        data, dl, hints = self.tax()
        src = (JS / "money.js").read_text(encoding="utf-8")
        m = re.search(r"  function fromPlace\(m\) \{.*?\n  \}\n", src, re.S)
        self.assertIsNotNone(m)
        cases, want = [], []
        for pid, p, t, s, te, se in self.saved_cases():
            et, es, dt, ds = self.explicit(p, t, s, te, se)
            cases.append({"place": pid, "township": "" if et == "any" else et, "school": "" if es == "any" else es,
                          "defaults": {"township": dt, "school": ds}})
            want.append(tax_district_for_saved(dl, hints, pid, et, es, dt, ds) or None)
        script = ("var data = " + json.dumps(data) + ";\n" + m.group(0) +
                  "\nvar cases = " + json.dumps(cases) + ";\nconsole.log(JSON.stringify(cases.map(fromPlace)));\n")
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "rule.js"
            f.write_text(script, encoding="utf-8")
            got = json.loads(subprocess.run(["node", str(f)], capture_output=True, text=True, check=True).stdout)
        self.assertEqual(len(got), len(want))
        for c, g, w in zip(cases, got, want):
            self.assertEqual(g, w, c)

    def test_here_js_keeps_explicit_choices_apart(self):
        src = (JS / "here.js").read_text(encoding="utf-8")
        self.assertIn('set: chosen("township")', src)
        self.assertIn('set: chosen("school")', src)
        self.assertIn("set: st.set || []", src)
        # fresh(): a newly chosen place stores no explicit township or school
        k = src.index("function fresh(id)")
        self.assertNotIn("set:", src[k:k + 250])
        mine = src[src.index("function mine()"):src.index("function hashWins()")]
        self.assertIn('set.indexOf("school") >= 0', mine)
        self.assertIn('set.indexOf("township") >= 0', mine)
        # the question groups never carry a school marker (here.js would call a default "Your school corporation")
        self.assertNotRegex(self.html[JQ], r'data-here-unit="(sbcsc|phm|school-city-mishawaka|new-prairie)"')

    def test_calendar_years_stay_as_link_targets(self):
        html = self.html[CAL]
        for y in range(2026, 2031):
            tag = re.search(r'<section class="cal-year" id="year-' + str(y) + r'"[^>]*>', html).group(0)
            self.assertIn("data-tf-keep", tag)
        n = re.search(r'<p class="cal-year-empty muted"[^>]*data-here-empty="2027: ([^"]*)"', html)
        self.assertIsNotNone(n)
        self.assertIn("city and town offices only", n.group(1))
        self.assertIn("data-tf-group-empty", (JS / "tablefilter.js").read_text(encoding="utf-8"))

    # ------------------------------------------------------------------ the pages
    def test_every_page_has_a_hidden_empty_slot(self):
        kinds = {CAL: "filter", OH: "filter", RES: "explorer", JQ: "first", TAX: "taxbill", COUNTY: "one",
                 SCHOOLS: "one", PEOPLE: "map"}
        for pg, kind in kinds.items():
            slots = SLOT_RE.findall(self.html[pg])
            self.assertEqual(len(slots), 1, pg)
            attrs, body = slots[0]
            self.assertIn(f'data-here-pre="{kind}"', attrs, pg)
            self.assertIn(" hidden", attrs, pg)
            self.assertEqual(body, "", pg)
            target = re.search(r'data-here-for="([^"]+)"', attrs).group(1)
            self.assertIn(f'id="{target}"', self.html[pg], pg)

    def test_rows_carry_valid_layers(self):
        ok = self.valid_layers()
        for pg, cls in ((CAL, "cal-seat"), (OH, "oh-row")):
            rows = re.findall(r'<li [^>]*class="' + cls + r'"[^>]*>', self.html[pg])
            self.assertTrue(rows, pg)
            for r in rows:
                m = re.search(r'data-here-layer="([^"]*)"', r)
                self.assertIsNotNone(m, (pg, r[:120]))
                self.assertIn(m.group(1), ok, pg)
        # every officeholder layer is one of the governments the page lists
        self.assertIn('data-here-layer="state"', self.html[OH])
        self.assertIn('data-here-layer="state"', self.html[CAL])

    def test_results_payload_layers(self):
        data = _json(self.html[RES], "elx-data")
        self.assertEqual(len(data["pl"]), len(data["places"]))
        pl = dict(zip(data["places"], data["pl"]))
        self.assertEqual(pl["St. Joseph County"], "county")
        self.assertEqual(pl["Statewide"], "state")
        self.assertEqual(pl["South Bend"], "municipality:south-bend")
        self.assertEqual(pl["Penn Township"], "township:penn-township")
        self.assertEqual(pl["Penn-Harris-Madison schools"], "school:phm")
        self.assertEqual(pl["Town of Walkerton"], "municipality:walkerton")
        for v in data["pl"]:
            self.assertIn(v, self.valid_layers() | {""})

    def test_question_groups(self):
        html = self.html[JQ]
        box = re.search(r'<div class="elx-qgroups" id="q-groups">', html)
        self.assertIsNotNone(box)
        groups = re.findall(r'<div class="elx-qgroup" id="q-group-([^"]+)"([^>]*)>', html)
        self.assertEqual(len(groups), 5)
        lay = {g: re.search(r'data-here-layer="([^"]*)"', a).group(1) for g, a in groups}
        self.assertEqual(lay["statewide"], "state")
        self.assertEqual(lay["mishawaka"], "municipality:mishawaka")
        self.assertEqual(lay["school-city-of-mishawaka"], "school:school-city-mishawaka")
        self.assertEqual(lay["south-bend-community-schools"], "school:sbcsc")
        self.assertEqual(lay["new-prairie-schools"], "school:new-prairie")
        # old anchors kept
        for i in ("q-group-statewide", "q-2016g-mishawaka-public-question"):
            self.assertIn(f'id="{i}"', html)

    def test_slot_targets_match_page_keys(self):
        self.assertIn('data-here-keys="school"', self.html[SCHOOLS])
        for uid in ("sbcsc", "phm", "john-glenn"):
            self.assertIn(f'data-one="{uid}"', self.html[SCHOOLS])
        for k in ("county-commissioner-d1", "county-council-a", "county-council-f"):
            self.assertIn(f'data-one="{k}"', self.html[COUNTY])
        self.assertRegex(self.html[PEOPLE], r'id="[^"]+"[^>]*>(?:(?!</section>).)*data-here-pre="map"')

    # ------------------------------------------------------------------ scripts
    def test_scripts_ascii_textcontent_and_private(self):
        for name in ("preselect.js", "here.js", "elections.js", "money.js", "tablefilter.js", "pick_one.js", "map.js"):
            src = (JS / name).read_text(encoding="utf-8")
            src.encode("ascii")
            self.assertNotIn("innerHTML", src, name)
        pre = (JS / "preselect.js").read_text(encoding="utf-8")
        here = (JS / "here.js").read_text(encoding="utf-8")
        part = here[here.index("saved-place preselect"):]
        for src in (pre, part):
            for bad in ("history.", "location.hash =", "location.href =", "location.assign", "fetch(", "XMLHttpRequest",
                        "sendBeacon", "localStorage.setItem"):
                self.assertNotIn(bad, src)
        # the address is only read, at load, before map scripts rewrite it
        self.assertIn("var HASH0 = window.location.hash;", here)

    def test_tax_choice_saved_only_by_the_reader(self):
        src = (JS / "money.js").read_text(encoding="utf-8")
        self.assertIn('var TB_KEY = "civic-taxbill-v3";', src)
        body = src[src.index("function renderUnits()"):src.index("function render()")]
        self.assertNotIn("saveState()", body)
        self.assertNotIn("civic-taxbill-v2", src)

    def test_shared_scripts_hooks(self):
        self.assertIn('bar.addEventListener("tf-scope"', (JS / "tablefilter.js").read_text(encoding="utf-8"))
        self.assertIn('"tf-scope-cleared"', (JS / "tablefilter.js").read_text(encoding="utf-8"))
        po = (JS / "pick_one.js").read_text(encoding="utf-8")
        self.assertIn('doc.addEventListener("one:choose"', po)
        self.assertIn('doc.addEventListener("one:all"', po)
        self.assertIn('root.addEventListener("cmap-select"', (JS / "map.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
