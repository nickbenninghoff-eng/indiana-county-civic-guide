"""The checker fails when two area stylesheets define the same bare class selector."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "site"))
import check  # noqa: E402


def _dir(files: dict[str, str]) -> Path:
    d = Path(tempfile.mkdtemp())
    for name, css in files.items():
        (d / name).write_text(css, encoding="utf-8")
    return d


class CssDuplicateTests(unittest.TestCase):
    def test_same_bare_class_in_two_files_is_flagged(self):
        d = _dir({"places.css": ".cov { display: inline-block; }", "campaigns.css": "table.x td.y { }\n.cov, .other { color: red; }"})
        self.assertEqual(check.css_duplicate_bare_classes(d, {}), [("cov", ["campaigns.css", "places.css"])])

    def test_scoped_or_compound_selectors_and_comments_do_not_collide(self):
        d = _dir({"a.css": ".cov { color: red; }", "b.css": "table.cf td.cov { x: y }\n.cov-strip .cov { x: y }\n/* .cov { } */\n.cov:hover { x: y }"})
        self.assertEqual(check.css_duplicate_bare_classes(d, {}), [])

    def test_inside_media_block_and_same_file_repeat(self):
        d = _dir({"a.css": ".k { a: b }\n.k { c: d }", "b.css": "@media (max-width: 400px) {\n  .k { e: f }\n}"})
        self.assertEqual(check.css_duplicate_bare_classes(d, {}), [("k", ["a.css", "b.css"])])

    def test_allowlist_exempts(self):
        d = _dir({"a.css": ".k { a: b }", "b.css": ".k { e: f }"})
        self.assertEqual(check.css_duplicate_bare_classes(d, {"k": "harmless"}), [])

    def test_real_stylesheets_have_no_duplicates(self):
        self.assertEqual(check.css_duplicate_bare_classes(), [])


if __name__ == "__main__":
    unittest.main()
