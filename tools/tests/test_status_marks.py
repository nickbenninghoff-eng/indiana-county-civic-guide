"""Status marks: "About these figures" (phase 6, 2026-11-18; report planning/qa/phase6-status-marks-2026-11-18.md).

The owner asked for the inline status words and caveats ("Incomplete", OFFICIAL / COMPUTED / SECONDARY badges, ...) to
become one note at the bottom of the page. The system (civic/components.py FIGURE_MARKS):

- An official, complete figure carries no mark. An exception carries one small symbol right after it, one fixed symbol
  per kind on every page: * incomplete, † unofficial, ‡ secondary source, △ single source, ‖ computed by the guide,
  ¶ from a scan, ◊ low confidence, ? unverified, ≈ unreliable estimate, ° no sampling error published.
- Each symbol links to #fnote-<kind> (hyphens for underscores) in the page's "About these figures" note
  (shell.Page.render), which lists only the
  symbols that page uses, each meaning once. A tab page's note links on to the Sources tab. No marks, no note.
- A table, chart or section whose figures share one status says it once in its caption (scope_attrs + scope_note /
  scope_mark); the marks of that status inside it are dropped (drop_scoped). Unofficial results keep the word at the top.
- Status columns of tables keep their words (status_label), so Copy CSV keeps them; Copy CSV writes a symbol as its word.

The proof that nothing was lost: for a sample of 43 pages across every page type, every (figure, status) pair the page
showed before the change (fixtures/status_marks_before.json, taken from the build of 2026-11-18 before the change) is
still on the page after it, as a mark beside the same figure or as the status of the section that holds it.
Regenerate the fixture only when a page's content changes on purpose (status_marks_lib.occurrences on the new build).

Run:  python -P -E -m unittest discover -s tools/tests -p test_status_marks.py   (or the whole suite)
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = ROOT / "tools" / "site"
TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE_DIR))
sys.path.insert(0, str(TESTS))

import build  # noqa: E402
import status_marks_lib as L  # noqa: E402
from civic import components as C  # noqa: E402
from civic import tabs as T  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site, shows_unofficial  # noqa: E402
from pages import stubs  # noqa: E402

FIXTURE = TESTS / "fixtures" / "status_marks_before.json"
EXCEPTIONS = [k for k in C.FIGURE_MARKS]


# ====================================================================== helpers, no build
class Helpers(unittest.TestCase):
    def test_official_is_unmarked(self):
        self.assertEqual(str(C.status_badge("official")), "")
        self.assertEqual(str(C.status_badge("OFFICIAL ", object())), "")
        self.assertEqual(str(T.status_mark("official", None, "note", "#marks")), "")
        self.assertEqual(str(C.status_symbol("official")), "")
        self.assertEqual(str(C.scope_mark("official")), "")

    def test_one_fixed_symbol_per_kind(self):
        syms = [v[0] for v in C.FIGURE_MARKS.values()]
        self.assertEqual(len(syms), len(set(syms)), "two kinds share a symbol")
        self.assertEqual(syms[:5], ["*", "†", "‡", "△", "‖"])
        for k in ("incomplete", "unofficial", "secondary", "single_source", "computed"):
            self.assertIn(k, C.FIGURE_MARKS)

    def test_mark_is_a_named_link_to_the_note(self):
        for k, (sym, name, meaning) in C.FIGURE_MARKS.items():
            m = str(C.figure_mark(k))
            self.assertTrue(m.startswith(C.WORD_JOINER), f"{k}: no word joiner, the mark could wrap away")
            self.assertIn(f'href="#{C.note_id(k)}"', m)
            self.assertRegex(C.note_id(k), r"^[a-z0-9-]+$")
            self.assertIn(f'data-fmark="{k}"', m)
            self.assertRegex(m, rf'aria-label="{re.escape(str(C.esc(name)))}: ')     # full meaning, not the symbol
            self.assertRegex(m, r'title="[^"]{20,}"')
            self.assertTrue(m.endswith(f">{C.esc(sym)}</a>"), m)
            self.assertNotIn("party", m)                                                # never a party color
        # status_badge and status_mark give the same mark, with the figure's own note in the name
        self.assertEqual(str(C.status_badge("computed", None, "Sum.")), str(T.status_mark("computed", None, "Sum.")))
        self.assertIn("Sum.", str(C.status_badge("computed", None, "Sum.")))

    def test_mark_without_link_for_summaries(self):
        m = str(C.figure_mark("secondary", link=False))
        self.assertIn('<span class="fmark fmark-secondary"', m)
        self.assertIn('role="img"', m)
        self.assertIn('aria-label="Secondary source: ', m)

    def test_unknown_status_still_shows_its_word(self):
        self.assertIn("MYSTERY", str(C.status_badge("mystery")))
        self.assertIn("STATUS UNKNOWN", str(C.status_badge("")))

    def test_status_column_words(self):
        self.assertEqual(C.status_word("official"), "Official")
        self.assertEqual(C.status_word("single_source"), "Single source")
        self.assertEqual(C.status_word("incomplete"), "Incomplete")
        self.assertIn(">OFFICIAL</span>", str(C.status_label("official")))
        self.assertIn(">UNOFFICIAL</span>", str(C.status_label("unofficial")))

    def test_note_lists_only_what_is_used_in_fixed_order(self):
        self.assertEqual(str(C.figure_notes([])), "")
        self.assertEqual(str(C.figure_notes(["official", "nonsense"])), "")
        n = str(C.figure_notes(["computed", "incomplete", "computed"]))
        self.assertEqual(n.count("<li "), 2)
        self.assertLess(n.index('id="fnote-incomplete"'), n.index('id="fnote-computed"'))
        self.assertIn("About these figures", n)
        self.assertIn("<strong>Incomplete:</strong> at least one expected report is not on file, so this total is a "
                      "floor", n)

    def test_scope_drops_inner_marks_of_the_same_status_only(self):
        inner = C.h("ul", None,
                    C.h("li", None, "A 5", C.status_badge("unofficial"), C.status_badge("computed")),   # two statuses
                    C.h("li", None, C.h("img", {"src": "x.png", "alt": ""}), "B 6", C.status_badge("unofficial")))
        html = str(C.h("section", C.scope_attrs("unofficial"), C.scope_note("unofficial", "count"), inner))
        out = C.drop_scoped(html)
        self.assertEqual(out.count('data-fmark="unofficial"'), 1, "only the caption's mark stays")
        self.assertIn("fmark-scope", out)
        self.assertEqual(out.count('data-fmark="computed"'), 1, "another status is never dropped")
        self.assertIn("<strong>Unofficial: every count.</strong>", out)
        self.assertEqual(out.count(C.WORD_JOINER), 2)

    def test_nested_scope_keeps_one_caption_mark(self):
        li = C.h("li", C.scope_attrs("secondary"), "Result 1987", C.scope_mark("secondary"),
                 C.h("figure", C.scope_attrs("secondary"), C.h("figcaption", None, "Chart", C.scope_mark("secondary"))))
        out = C.drop_scoped(str(C.h("ul", None, li)))
        self.assertEqual(out.count('data-fmark="secondary"'), 1)       # the line's mark; the chart's is the repeat
        sec = C.drop_scoped(str(C.h("section", C.scope_attrs("secondary"), C.scope_note("secondary"), C.h("ul", None, li))))
        self.assertEqual(sec.count('data-fmark="secondary"'), 1)       # the section's caption only
        self.assertEqual(C.drop_scoped("<p>no scope 1" + str(C.status_badge("low")) + "</p>"),
                         "<p>no scope 1" + str(C.status_badge("low")) + "</p>")

    def test_unofficial_detection_follows_the_new_forms(self):
        self.assertTrue(shows_unofficial("<p>2026 x" + str(C.status_badge("unofficial")) + "</p>", "2026"))
        self.assertTrue(shows_unofficial('<section data-fscope="unofficial"><h2>2026</h2></section>', "2026"))
        self.assertFalse(shows_unofficial("<p>2026 x" + str(C.status_badge("computed")) + "</p>", "2026"))
        self.assertFalse(shows_unofficial(str(T.marks_key()) + "<p>2026</p>", "2026"))

    def test_css_uses_tokens_only(self):
        css = (SITE_DIR / "static" / "css" / "fmarks.css").read_text(encoding="utf-8")
        self.assertNotRegex(css, r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(", "literal color outside the token block")
        self.assertNotRegex(css, r"\.party|--party|m-party", "a mark styled with a party color")
        self.assertIn("white-space: nowrap", css)
        self.assertIn("@media print", css)

    def test_copy_csv_writes_the_word(self):
        js = (SITE_DIR / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn('querySelectorAll(".fmark")', js)
        self.assertIn('getAttribute("data-word")', js)


# ====================================================================== the built site
class Built(unittest.TestCase):
    """One full build into a temporary folder (the same loop as build.py)."""

    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        site = Site(cls.ed, cls.out)
        build.discover_builders()
        failed = []
        for entry in site.entries:
            fn = build.BUILDERS.get(entry.path)
            if fn:
                try:
                    fn(site)
                except Exception as e:   # noqa: BLE001 (reported below, never hidden)
                    failed.append(f"{entry.path}: {type(e).__name__}: {e}")
                    site.pages.pop(entry.path, None)
                    stubs.build_stub(site, entry)
            else:
                stubs.build_stub(site, entry)
        site.write()
        cls.failed = failed
        cls.paths = sorted(site.pages)
        cls._html = {}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def html(self, path: str) -> str:
        if path not in self._html:
            self._html[path] = (self.out / path).read_text(encoding="utf-8")
        return self._html[path]

    def main(self, path: str) -> str:
        m = re.search(r"<main\b[^>]*>(.*)</main>", self.html(path), re.S)
        return m.group(1) if m else ""

    def test_build_ok(self):
        self.assertEqual(self.failed, [])

    # ---- nothing lost
    def test_every_status_shown_before_is_still_on_the_page(self):
        fx = json.loads(FIXTURE.read_text(encoding="utf-8"))["pages"]
        self.assertGreaterEqual(len(fx), 30)
        kinds_seen, types = set(), set()
        lost = []
        for path, pairs in fx.items():
            self.assertIn(path, self.paths, f"{path} is no longer built")
            html = self.html(path)
            now = {(hashlib.sha1(c.encode()).hexdigest()[:16], k) for c, k in L.occurrences(html)}
            scoped = {hashlib.sha1(c.encode()).hexdigest()[:16]: ks for c, ks in L.scoped(html).items()}
            types.add(path.split("/")[0])
            for p in pairs:
                kinds_seen.add(p["k"])
                if (p["h"], p["k"]) not in now and p["k"] not in scoped.get(p["h"], set()):
                    lost.append(f"{path}: {p['k']} | {p['t']}")
        self.assertEqual(lost, [], f"{len(lost)} figure statuses lost")
        # the sample covers every kind the site uses and every page type
        self.assertTrue({"incomplete", "unofficial", "secondary", "single_source", "computed", "from_scan", "low",
                         "unreliable", "zero_moe"} <= kinds_seen, kinds_seen)
        self.assertTrue({"offices", "governments", "elections", "people", "state", "community", "money", "history",
                         "about", "index.html"} <= types, types)

    # ---- every symbol has its note entry, and vice versa, on every page
    def test_symbols_and_note_match_on_every_page(self):
        bad = []
        for path in self.paths:
            html = self.html(path)
            if "fmark" not in html and "figure-notes" not in html:
                continue
            used = {k for k, _s, _h in L.symbols(html)} | L.scope_kinds(html)
            notes = L.note_entries(html)
            if not used and not notes:
                continue                     # a legend only (the Sources tab's key): no figure marks, no note
            if used != set(notes):
                bad.append(f"{path}: marks {sorted(used)} note {sorted(notes)}")
                continue
            for k, sym, href in L.symbols(html):
                if sym != C.FIGURE_MARKS[k][0] or href not in ("", f"#{C.note_id(k)}"):
                    bad.append(f"{path}: {k} shown as {sym!r} -> {href!r}")
                    break
                # the link's target is on the page, and its id is letters, digits and hyphens (check.py's rule):
                # this is what failed for from_scan, single_source and zero_moe while the ids had underscores
                if href and (not re.fullmatch(r"#[a-z0-9-]+", href) or f'id="{href[1:]}"' not in html):
                    bad.append(f"{path}: {k} links to {href!r}, which is not a valid id on the page")
                    break
            for k, text in notes.items():
                sym, name, meaning = C.FIGURE_MARKS[k]
                if text != f"{sym} {name}: {meaning}":
                    bad.append(f"{path}: note for {k} reads {text!r}")
            main = self.main(path)
            if main.count('id="figure-notes"') != 1 or not main.rstrip().endswith("</aside>"):
                bad.append(f"{path}: the note is not the single last part of the page")
        self.assertEqual(bad, [], "\n".join(bad[:20]))

    def test_no_marks_no_note_and_no_old_badges_outside_status_columns(self):
        n_without = 0
        for path in self.paths:
            main = self.main(path)
            if 'data-fmark="' not in main and 'data-fscope="' not in main:
                n_without += 1
                self.assertNotIn("figure-notes", main, path)
            # the old one-glyph marks are gone everywhere
            self.assertNotIn('class="smark ', main, path)
        self.assertGreater(n_without, 0)

    def test_forwarding_pages_have_no_note(self):
        fwd = [p for p in self.paths if 'name="civic-moved-to"' in self.html(p)]
        self.assertTrue(fwd)
        for p in fwd:
            self.assertNotIn("figure-notes", self.html(p), p)

    def test_tab_note_links_to_sources_tab(self):
        main = self.main("offices/south-bend-mayor/money/index.html")
        note = main[main.index('id="figure-notes"'):]
        self.assertIn('href="../sources/index.html#marks"', note)
        self.assertIn('id="fnote-computed"', note)
        about = self.main("about/index.html")
        self.assertIn('id="badges"', about)

    # ---- unofficial results keep the word at the top of their section
    def test_unofficial_2026_labelled_in_words_at_section_top(self):
        main = self.main("elections/2026g/contests/index.html")
        first_contest = main.index('class="ep-contest"')
        line = re.search(r'<p class="fscope-line fscope-unofficial">(.*?)</p>', main, re.S)
        self.assertIsNotNone(line)
        self.assertLess(line.start(), first_contest)
        # 2026-11-18: the county canvass made most 2026 contests official, so the tab is mixed: the word at its top,
        # the split in words from the rows, and each unofficial contest keeps its own mark
        self.assertIn("<strong>Unofficial</strong>", line.group(1))
        self.assertIn("124 of the 166 result lines", line.group(1))
        from pages.elections import contest_status
        n_unoff = sum(1 for c in self.ed.contests.values()
                      if c["election_id"] == "2026g" and contest_status(c["rows"]) == "unofficial")
        self.assertEqual(len(re.findall(r'<li class="ep-contest"[^>]*data-fscope="unofficial"', main)), n_unoff)
        # an office's 2026 year: the word at the top of the year, not beside every contest
        sec = re.search(r'<section class="tsec er-year" id="y2026"[^>]*>(.*?)</section>',
                        self.main("offices/state-house-7/elections/index.html"), re.S)
        self.assertIsNotNone(sec)
        # 2026 there mixes the official primary and the unofficial general (recount window): the year opens with the
        # word, and the general's contest keeps its mark (a year whose contests are all unofficial says "every count
        # for 2026")
        self.assertIn("<strong>Unofficial</strong>", sec.group(1))
        self.assertIn('data-fscope="unofficial"', sec.group(1))
        self.assertTrue(any("<strong>Unofficial: every count for 2026.</strong>" in self.main(p)
                            for p in self.paths if p.startswith("offices/") and p.endswith("elections/index.html")))
        self.assertLess(sec.group(1).index("fscope-unofficial"), sec.group(1).index('class="er-item"'))
        # the banner keeps its word badge
        self.assertIn('class="badge badge-unofficial"', self.html("elections/2026g/contests/index.html"))

    def test_status_columns_keep_words(self):
        for path, tid in (("elections/calendar/index.html", "calendar-table"),
                          ("elections/compare/index.html", "close-races-table")):
            main = self.main(path)
            m = re.search(rf'<table id="{tid}".*?</table>', main, re.S)
            if m is None:
                continue
            self.assertRegex(m.group(0), r">(OFFICIAL|UNOFFICIAL|FROM SCAN|SECONDARY)<", f"{path} #{tid}")

    def test_incomplete_is_a_mark_not_a_sentence(self):
        for path in ("offices/south-bend-mayor/money/index.html", "people/james-mueller/money/index.html"):
            if path not in self.paths:
                continue
            main = self.main(path)
            self.assertNotIn("Incomplete: the total covers only the reports on file", main, path)
            self.assertNotIn("Complete: every expected report is on file", main, path)
        hits = [p for p in self.paths if p.startswith(("offices/", "people/")) and p.endswith("money/index.html")
                and 'data-fmark="incomplete"' in self.main(p)]
        self.assertTrue(hits, "no office or person Money tab marks an incomplete total")


if __name__ == "__main__":
    unittest.main()
