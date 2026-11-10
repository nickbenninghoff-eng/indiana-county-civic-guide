"""Ownership watermark and release stamp (Nick, 2026-11-09).

- "add my name Nick Benninghoff; Phenomogen LLC as a watermark in the code for every page": every page's head carries
  an HTML comment plus author/copyright metas, the shared style.css and app.js start with a /*! */ banner, and the
  Netlify 404 page carries the same head lines. Holder and year come from edition.json.
- The notice text can never close or open a comment (an edition config with "--" or "*/" in it stays inert).
- The masthead stamp is the release version, not a draft; the home description is the county-wide reference.
Run:  python -P -E -m unittest discover -s tools/tests -p "test_rights_watermark.py"
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = ROOT / "tools" / "site"
sys.path.insert(0, str(SITE_DIR))

import build  # noqa: E402
import netlify_prep as N  # noqa: E402
from civic import sitemap  # noqa: E402
from civic.data import Edition  # noqa: E402
from civic.shell import Site, rights_banner, rights_html, rights_notice  # noqa: E402

NOTICE = "Copyright 2026 Nick Benninghoff; Phenomogen LLC."


class Notice(unittest.TestCase):
    def test_text_from_config(self):
        cfg = {"rights_holder": "Nick Benninghoff; Phenomogen LLC", "rights_year": "2026",
               "series": "Indiana County Civic Guide", "edition": "St. Joseph County Edition"}
        self.assertEqual(rights_notice(cfg), "Copyright 2026 Nick Benninghoff; Phenomogen LLC. "
                                             "Indiana County Civic Guide, St. Joseph County Edition.")

    def test_cannot_break_out_of_a_comment(self):
        cfg = {"rights_holder": "A --> <script>x</script> */ /* B", "rights_year": "2026", "series": "S",
               "edition": "E"}
        text = rights_notice(cfg)
        for bad in ("--", "*/", "/*", "<", ">"):
            self.assertNotIn(bad, text)
        html = str(rights_html(cfg))
        self.assertEqual(html.count("<!--"), 1)
        self.assertEqual(html.count("-->"), 1)
        self.assertNotIn("<script", html)
        banner = rights_banner(cfg)
        self.assertTrue(banner.startswith("/*! ") and banner.endswith(" */\n"))
        self.assertEqual(banner.count("*/"), 1)


class BuiltPages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ed = Edition.load(ROOT, "st-joseph")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        site = Site(cls.ed, cls.out)
        build.discover_builders()
        for path in ("index.html", "county/index.html"):
            build.BUILDERS[path](site)
        site.write()
        build.write_assets(cls.ed, cls.out)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_edition_config(self):
        self.assertEqual(self.ed.config["rights_holder"], "Nick Benninghoff; Phenomogen LLC")
        self.assertNotIn("draft", self.ed.config["version"])

    def test_every_page_head_is_watermarked(self):
        for path in ("index.html", "county/index.html"):
            html = (self.out / path).read_text(encoding="utf-8")
            head = html[:html.index("</title>") + 400]
            self.assertIn(f"<!-- {NOTICE}", head, path)
            self.assertIn('<meta name="author" content="Nick Benninghoff; Phenomogen LLC">', head, path)
            self.assertIn('<meta name="copyright" content="Copyright 2026', head, path)

    def test_root_fragment_still_starts_with_title(self):
        # the Artifact host's contract: index.html is a fragment that begins with <title>
        self.assertTrue((self.out / "index.html").read_text(encoding="utf-8").startswith("<title>"))

    def test_bundles_are_watermarked(self):
        for name in ("style.css", "app.js"):
            first = (self.out / "assets" / name).read_text(encoding="utf-8").split("\n", 1)[0]
            self.assertTrue(first.startswith(f"/*! {NOTICE}"), name)

    def test_masthead_stamp_is_release(self):
        html = (self.out / "index.html").read_text(encoding="utf-8")
        self.assertIn('<span class="stamp-ver">v1.0</span>', html)
        self.assertNotIn("draft", html.split('class="stamp-ver"', 1)[1][:30])

    def test_404_is_watermarked(self):
        page = N.page_404(self.ed.config)
        self.assertNotIn("{{", page)
        self.assertIn(f"<!-- {NOTICE}", page)
        self.assertIn('<meta name="author" content="Nick Benninghoff; Phenomogen LLC">', page)

    def test_home_description_is_the_county_reference(self):
        home = next(e for e in sitemap.entries(self.ed) if e.path == "index.html")
        self.assertNotIn("one address", home.description)
        self.assertIn("St. Joseph County", home.description)


if __name__ == "__main__":
    unittest.main()
