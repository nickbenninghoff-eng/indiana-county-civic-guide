"""tools/site/check.py: the office Money tab's switch state (#show=primary&party=D, static/js/offices.js) is the one
fragment allowed outside the letters/digits/hyphens rule, and only narrowly (phase 6 step 5 follow-up, 2026-11-18).

Accepted: show=primary|general|both, optionally &party=<a code in that page's #mt-party>, on a page that ships the
switch (#mt-ctl with that button, app.js). Rejected: any other key, order or value; a party the page doesn't offer; a
state fragment on a page without the switch. The checker is run end to end on a two-page temporary site.
Run:  python -P -E -m unittest discover -s tools/tests -p test_check_state_fragments.py
"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "site"))

import check  # noqa: E402

HEAD = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{t}</title>'
        '<meta name="viewport" content="width=device-width">'
        '<meta name="claude:viewport-fit-sides" content="x"></head><body>{b}'
        '<script src="../assets/app.js" defer></script></body></html>')
SWITCH = ('<div id="mt-ctl"><button data-mt-show="both">Both</button><button data-mt-show="primary">Primary</button>'
          '<button data-mt-show="general">General</button><select id="mt-party" class="mt-party">'
          '<option value="">All parties</option><option value="D">D</option><option value="R">R</option></select></div>'
          '<section id="y2023"></section>')
TAB = "tab/index.html"
PLAIN = "plain/index.html"


def problems(frags: list[str], target: str = TAB) -> list[str]:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "tab").mkdir()
        (root / "plain").mkdir()
        (root / "assets").mkdir()
        (root / "assets" / "app.js").write_text("", encoding="utf-8")
        (root / TAB).write_text(HEAD.format(t="Tab", b=SWITCH), encoding="utf-8")
        links = "".join(f'<a href="../{target}#{f}">x</a>' for f in frags)
        (root / PLAIN).write_text(HEAD.format(t="Plain", b='<p id="here">' + links + "</p>"), encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            check.run(root)
        return [ln[4:] for ln in out.getvalue().splitlines() if ln.startswith("  - " + PLAIN)]


class Pure(unittest.TestCase):
    """money_tab_state_problems on its own."""
    SRC = HEAD.format(t="Tab", b=SWITCH)

    def ok(self, frag):
        self.assertEqual(check.money_tab_state_problems(frag, self.SRC), [], frag)

    def bad(self, frag, src=None):
        self.assertTrue(check.money_tab_state_problems(frag, self.SRC if src is None else src), frag)

    def test_accepts_the_grammar_offices_js_parses(self):
        for f in ("show=primary", "show=general", "show=both", "show=primary&party=D", "show=general&party=R"):
            self.ok(f)

    def test_rejects_everything_else(self):
        for f in ("show=runoff", "show=Primary", "party=D", "party=D&show=primary", "show=primary&party=L",
                  "show=primary&party=", "show=primary&year=2023", "show=primary&party=D&party=R",
                  "show=primary&show=general", "y=2023", "show="):
            self.bad(f)

    def test_rejects_a_page_without_the_switch(self):
        self.bad("show=primary", HEAD.format(t="Plain", b="<p>no switch</p>"))
        self.bad("show=primary", SWITCH)    # the switch markup but no app.js (offices.js) loaded


class EndToEnd(unittest.TestCase):
    def test_valid_state_links_pass_and_invalid_fail(self):
        self.assertEqual(problems(["show=primary", "show=general&party=D", "y2023"]), [])
        bad = problems(["show=runoff", "show=primary&party=L", "sort=asc"])
        self.assertEqual(len(bad), 3, bad)

    def test_state_link_to_a_page_without_the_switch_fails(self):
        bad = problems(["show=primary"], target=PLAIN)
        self.assertTrue(any("without the Money-tab switch" in p for p in bad), bad)

    def test_other_fragments_keep_the_old_rule(self):
        bad = problems(["not_an_id"])
        self.assertTrue(any("letters, digits, hyphens" in p for p in bad), bad)


if __name__ == "__main__":
    unittest.main()
