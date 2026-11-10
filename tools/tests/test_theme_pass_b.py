"""Theme pass B (2026-11-09): elections, data and state pages.
- Statute citations render one nowrap span per code, so a line breaks between codes and never at the hyphens inside one
  (elections rule paragraphs: .elx-code; state rule meta lines: .rule-code).
- Full-width list rows on the margins, officeholders and calendar pages: style.css caps `.block li` at the reading
  measure (specificity 0,1,1), so a bare `.mg-area { max-width: none }` (0,1,0) lost and the rows stopped at ~70ch while
  their group rules ran full width. The rows are now selected as `parent > child` (0,2,0).
Run:  python -P -E -m unittest discover -s tools/tests
"""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "site"))

import build  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.html import join  # noqa: E402
from civic.shell import Site  # noqa: E402
from pages import elections as E  # noqa: E402

CSS = ROOT / "tools" / "site" / "static" / "css"
STATE_PAGE = "state/how-the-state-shapes-local/index.html"
HOW_PAGE = "elections/how-it-works/index.html"


class StatuteCodes(unittest.TestCase):
    def test_one_span_per_code_keeps_separators(self):
        html = str(join(E._statute_codes("IC 3-11-2-10; 3-11-2-9;3-11-13-11")))
        self.assertEqual(re.findall(r'<span class="elx-code">([^<]*)</span>', html),
                         ["IC 3-11-2-10;", "3-11-2-9;", "3-11-13-11"])
        self.assertNotIn(";;", html)

    def test_single_code_and_escaping(self):
        html = str(join(E._statute_codes("Ind. Const. Art. 6 <sec. 2>")))
        self.assertEqual(html.count('class="elx-code"'), 1)
        self.assertIn("&lt;sec. 2&gt;", html)

    def test_blank_parts_dropped(self):
        self.assertEqual(E._statute_codes(" ; ;"), [])


class BuiltPages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        site = Site(ed, Path(cls.tmp.name))
        build.discover_builders()
        for p in (STATE_PAGE, HOW_PAGE):
            build.BUILDERS[p](site)
        site.write()
        cls.state = (Path(cls.tmp.name) / STATE_PAGE).read_text(encoding="utf-8")
        cls.how = (Path(cls.tmp.name) / HOW_PAGE).read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_state_rule_meta_wraps_each_code(self):
        metas = re.findall(r'<p class="rule-meta mono muted">(.*?)</p>', self.state)
        self.assertTrue(metas)
        for m in metas:
            if "Statute:" in m:
                self.assertIn('class="rule-code"', m)
                # no code text sits outside a nowrap span except the label and separators
                bare = re.sub(r'<span class="rule-code">[^<]*</span>', "", m)
                self.assertNotRegex(re.sub(r"<[^>]+>", "", bare), r"\d-\d")

    def test_elections_statute_spans(self):
        for span in re.findall(r'<span class="elx-statute mono">(.*?)</span>(?=[^<]*</p>)', self.how):
            self.assertIn('class="elx-code"', span)
        self.assertIn('class="elx-code"', self.how)


class ListRowSpecificity(unittest.TestCase):
    def test_full_width_rows_beat_block_li(self):
        css = (CSS / "elections.css").read_text(encoding="utf-8")
        for sel in (".mg-areas > .mg-area", ".mg-races > .mg-race", ".mg-tiles > .mg-tile", ".oh-list > .oh-gov",
                    ".oh-rows > .oh-row", ".cal-seats > .cal-seat"):
            self.assertRegex(css, re.escape(sel) + r"\s*\{[^}]*max-width:\s*none", sel)

    def test_block_li_still_caps_at_measure(self):
        # the rule the selectors above must outrank; if it changes, revisit them
        style = (ROOT / "tools" / "site" / "static" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".block p, .block li, .block dd { max-width: var(--measure); }", style)


if __name__ == "__main__":
    unittest.main()
