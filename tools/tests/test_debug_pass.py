"""Debug pass 2026-11-09 (research/debug-pass-2026-11-09.md): regressions for the functional bugs it fixed.

- Builds are deterministic: pages/money_history.py picked a committee's candidate name (and party, and office) with
  max(set(values), key=values.count), whose tie-break follows set order, which changes with Python's per-process string
  hashing. Two builds wrote "Dr. Oliver J. Davis, Jr." and "Oliver J. Davis" on the same page. Now Counter order
  (first seen wins a tie). Checked here by building the campaign area pages under two hash seeds.
- A blank cell the real data already has in that column never turns a page into a stub:
    indicator_values.value / moe (an ACS estimate the Census Bureau did not publish, a suppressed QCEW count) on the
    place pages, schools, budgets, community and history pages; a 2026 state legislative result with blank votes;
    a retention vote recorded 0 yes / 0 no; an election with straight-party counts and a blank ballots_cast.
- static/js stays ASCII (README rule; map_votes.js and search.js had literal middle dots and combining marks).
- Browser checks (skipped without Playwright): Back from #contest-<id> on the results explorer leaves the one-contest
  view; the map's "How areas voted" layer keeps #race-<id> in the address after a trip to another layer.

Run:  python -P -E -m unittest discover -s tools/tests -p "test_debug_pass.py"
"""
from __future__ import annotations

import functools
import http.server
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = ROOT / "tools" / "site"
sys.path.insert(0, str(SITE_DIR))

import build  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site  # noqa: E402
from pages import elections as el  # noqa: E402
from pages import elections_numbers as en  # noqa: E402
from pages import money_history as mh  # noqa: E402


def _build(ed, paths):
    """Run the builders for these pages into a temp site; returns {path: error text} for the ones that raised."""
    tmp = tempfile.TemporaryDirectory()
    site = Site(ed, Path(tmp.name))
    build.discover_builders()
    errors = {}
    for p in paths:
        try:
            build.BUILDERS[p](site)
        except Exception as e:  # noqa: BLE001 - the test reports which page failed and why
            errors[p] = f"{type(e).__name__}: {e}"
    tmp.cleanup()
    return errors


class MostCommonTieBreak(unittest.TestCase):
    def test_first_seen_wins_a_tie(self):
        self.assertEqual(mh._most_common(["Oliver J. Davis", "Dr. Oliver J. Davis, Jr.", "Dr. Oliver J. Davis, Jr.",
                                          "Oliver J. Davis"]), "Oliver J. Davis")
        self.assertEqual(mh._most_common(["b", "a", "a"]), "a")

    def test_no_set_order_tie_breaks_left(self):
        """No max(set(...), key=...) call in the page modules or helpers (code only, not the docstrings)."""
        import ast
        hits = []
        for p in sorted((SITE_DIR / "pages").glob("*.py")) + sorted((SITE_DIR / "civic").glob("*.py")):
            for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("max", "min")
                        and node.args and isinstance(node.args[0], ast.Call)
                        and isinstance(node.args[0].func, ast.Name) and node.args[0].func.id == "set"
                        and any(k.arg == "key" for k in node.keywords)):
                    hits.append(f"{p.name}:{node.lineno}")
        self.assertEqual(hits, [])


# a small script that builds the campaign area pages and prints a hash of each (run under two hash seeds)
_DETERMINISM = r"""
import hashlib, sys, tempfile
from pathlib import Path
sys.path.insert(0, {site!r})
import build
from civic.data import Edition
from civic.shell import Site
ed = Edition.load(Path({root!r}), "st-joseph")
tmp = tempfile.TemporaryDirectory()
site = Site(ed, Path(tmp.name))
build.discover_builders()
paths = sorted(p for p in build.BUILDERS if p.startswith("money/campaigns/"))
for p in paths:
    build.BUILDERS[p](site)
site.write()
for p in paths:
    print(p, hashlib.sha256((Path(tmp.name) / p).read_bytes()).hexdigest())
"""


class BuildIsDeterministic(unittest.TestCase):
    def test_campaign_pages_same_under_two_hash_seeds(self):
        code = _DETERMINISM.format(site=str(SITE_DIR), root=str(ROOT))
        outs = []
        for seed in ("1", "3"):   # seeds 1 and 3 order {"Oliver J. Davis", "Dr. Oliver J. Davis, Jr."} differently
            env = dict(os.environ, PYTHONHASHSEED=seed)
            # no -E here: the child must see PYTHONHASHSEED (-P keeps the cwd off sys.path)
            r = subprocess.run([sys.executable, "-P", "-c", code], cwd=str(ROOT), env=env, capture_output=True,
                               text=True, encoding="utf-8", timeout=600)
            self.assertEqual(r.returncode, 0, r.stderr[-2000:])
            outs.append(r.stdout)
        self.assertTrue(outs[0].strip())
        diff = [a for a, b in zip(outs[0].splitlines(), outs[1].splitlines()) if a != b]
        self.assertEqual(diff, [], "pages differ between two builds")


class BlankIndicatorValues(unittest.TestCase):
    """Every other indicator_values row loses its value, and every row flagged "CV>30%" in its notes loses its margin
    of error: the pages that read them still build."""

    PAGES = (["schools/index.html", "money/budgets/index.html", "history/index.html", "community/people/index.html",
              "community/income-and-work/index.html", "community/housing-and-education/index.html"])

    def test_pages_build(self):
        ed = Edition.load(ROOT, "st-joseph")
        for i, r in enumerate(ed.table("indicator_values")):
            if i % 2:
                r["value"] = ""
            r["notes"] = (r.get("notes") or "") + " CV>30%"
            if i % 3 == 0:
                r["moe"] = ""
        build.discover_builders()
        places = sorted(p for p in build.BUILDERS if p.startswith("places/"))
        self.assertTrue(places)
        self.assertEqual(_build(ed, places + self.PAGES), {})


class BlankResults(unittest.TestCase):
    def test_state_2026_blank_votes(self):
        ed = Edition.load(ROOT, "st-joseph")
        hit = 0
        for cid, c in ed.contests.items():
            if cid.startswith("2026g-state-"):
                for r in c["rows"]:
                    r["votes"], r["pct"] = "", ""
                    hit += 1
        self.assertGreater(hit, 0)
        self.assertEqual(_build(ed, ["state/your-legislators/index.html"]), {})

    def test_retention_zero_zero(self):
        ed = Edition.load(ROOT, "st-joseph")
        sup = [c for c in ed.contests.values() if el.classify(c)[0] == "Superior Court retention"]
        self.assertTrue(sup)
        for r in sup[0]["rows"]:
            if r["candidate"].upper() in ("YES", "NO"):
                r["votes"], r["pct"] = "0", ""
        self.assertEqual(_build(ed, ["elections/judges-and-questions/index.html"]), {})

    def test_straight_party_blank_ballots(self):
        ed = Edition.load(ROOT, "st-joseph")
        rows = [e for e in ed.table("elections") if e.get("straight_party_d")]
        self.assertTrue(rows)
        rows[-1]["ballots_cast"] = ""
        rows[0]["ballots_cast"] = "0"
        self.assertNotIn(rows[-1], en.straight_elections(ed, ed.table("elections")))
        self.assertEqual(_build(ed, ["elections/turnout/index.html", "elections/landscape/index.html"]), {})


class StaticJsIsAscii(unittest.TestCase):
    def test_ascii(self):
        bad = []
        for p in sorted((SITE_DIR / "static" / "js").glob("*.js")) + [SITE_DIR / "static" / "app.js"]:
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if any(ord(ch) > 127 for ch in line):
                    bad.append(f"{p.name}:{n}")
        self.assertEqual(bad, [], "non-ASCII characters in static JS (use \\u escapes or String.fromCharCode)")


# --------------------------------------------------------------------------- browser checks (optional)
try:
    from playwright.sync_api import sync_playwright  # noqa: E402
except ImportError:  # pragma: no cover - the stdlib-only suite still runs
    sync_playwright = None


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):  # noqa: D401 - silence the test output
        pass


@unittest.skipIf(sync_playwright is None, "Playwright is not installed")
class BrowserRegressions(unittest.TestCase):
    PAGES = ["elections/results/index.html", "map/index.html"]

    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name)
        site = Site(cls.ed, out)
        build.discover_builders()
        for p in cls.PAGES:
            build.BUILDERS[p](site)
        site.write()
        build.write_assets(cls.ed, out)
        # map-votes.json is written by the map page's builder into the edition's assets; copy the built one if absent
        mv = out / "assets" / "map-votes.json"
        if not mv.exists():
            src = ROOT / "site" / "st-joseph" / "assets" / "map-votes.json"
            if src.exists():
                mv.write_bytes(src.read_bytes())
        handler = functools.partial(_Quiet, directory=str(out))
        cls.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}/"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        cls.pw = sync_playwright().start()
        try:
            cls.browser = cls.pw.chromium.launch()
        except Exception as e:  # noqa: BLE001 - browsers not installed
            cls.pw.stop()
            cls.httpd.shutdown()
            raise unittest.SkipTest(f"Chromium not available: {e}")

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.httpd.shutdown()
        cls.tmp.cleanup()

    def test_back_from_one_contest_shows_the_list(self):
        p = self.browser.new_page()
        errors = []
        p.on("pageerror", lambda e: errors.append(str(e)))
        p.goto(self.base + "elections/results/index.html")
        p.wait_for_timeout(300)
        p.query_selector_all("#elx-results .elx-permalink a")[1].click()
        p.wait_for_timeout(300)
        self.assertIn("Showing one contest", p.text_content("#elx-count"))
        p.go_back()
        p.wait_for_timeout(300)
        self.assertNotIn("#contest-", p.url)
        self.assertNotIn("Showing one contest", p.text_content("#elx-count"))
        self.assertGreater(len(p.query_selector_all("#elx-results [data-contest]")), 1)
        self.assertEqual(errors, [])
        p.close()

    def test_tab_from_a_map_shape_reaches_the_panel_link(self):
        """Tab from the last area of the map moves into the panel's "Open page" link; focus used to fall back to the
        page because the panel was redrawn (and the link removed) as focus left the shape. On every page with a map."""
        p = self.browser.new_page()
        p.goto(self.base + "map/index.html")
        p.wait_for_timeout(300)
        shapes = [s for s in p.query_selector_all(".cmap-a") if s.is_visible()]
        self.assertTrue(shapes)
        shapes[-1].focus()
        p.keyboard.press("Tab")
        self.assertTrue(p.evaluate("document.activeElement !== document.body && "
                                   "document.getElementById('cmap-panel').contains(document.activeElement)"),
                        p.evaluate("document.activeElement.outerHTML.slice(0, 120)"))
        p.close()

    def test_votes_layer_keeps_its_race_in_the_address(self):
        if not (Path(self.tmp.name) / "assets" / "map-votes.json").exists():
            self.skipTest("assets/map-votes.json not built")
        p = self.browser.new_page()
        p.goto(self.base + "map/index.html#votes")
        p.wait_for_timeout(800)
        levels = p.query_selector_all("[data-level]")
        levels[-1].click()
        p.wait_for_timeout(200)
        chosen = p.url.split("#", 1)[1]
        self.assertTrue(chosen.startswith("race-"), p.url)
        p.click(".cmap-tab[data-layer=cities]")
        p.wait_for_timeout(100)
        p.click(".cmap-tab[data-layer=votes]")
        p.wait_for_timeout(300)
        self.assertEqual(p.url.split("#", 1)[1], chosen)
        p.close()


if __name__ == "__main__":
    unittest.main()
