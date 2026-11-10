"""Netlify readiness (security review 2026-11-09): tools/site/netlify_prep.py and tools/site/netlify/_headers.

- the CSP allows exactly the inline head script the shell writes (LOOK_BOOT) by its sha256, so a change to that
  script fails here instead of silently breaking the look/theme on the public host;
- the security headers are present and strict (no 'unsafe-inline' / 'unsafe-eval' for scripts, no wildcard hosts);
- the Artifact-host fragment index.html becomes a full document; prep refuses pages the CSP would break.
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

import netlify_prep as N  # noqa: E402
from civic.shell import LOOK_BOOT  # noqa: E402

HEADERS = (ROOT / "tools" / "site" / "netlify" / "_headers").read_text(encoding="utf-8")


def _csp() -> str:
    return re.search(r"Content-Security-Policy:([^\n]*)", HEADERS).group(1)


def _directives() -> dict[str, list[str]]:
    out = {}
    for part in _csp().split(";"):
        bits = part.split()
        if bits:
            out[bits[0]] = bits[1:]
    return out


class Headers(unittest.TestCase):
    def test_look_boot_hash_is_allowed(self):
        body = re.fullmatch(r"<script>(.*)</script>", LOOK_BOOT, re.S).group(1)
        self.assertIn(N.sha256_b64(body), N.csp_hashes(HEADERS),
                      "civic/shell.py LOOK_BOOT changed: put its new sha256 in tools/site/netlify/_headers script-src")

    def test_csp_is_strict(self):
        d = _directives()
        self.assertEqual(d["default-src"], ["'none'"])
        for name in ("script-src", "style-src", "img-src", "connect-src", "font-src"):
            self.assertNotIn("'unsafe-inline'", d[name], name)
            self.assertNotIn("'unsafe-eval'", d[name], name)
            self.assertFalse([s for s in d[name] if s in ("*", "https:", "http:", "data:") or "*" in s], name)
        self.assertEqual(d["frame-ancestors"], ["'none'"])
        self.assertEqual(d["object-src"], ["'none'"])
        self.assertEqual(d["base-uri"], ["'none'"])

    def test_other_security_headers(self):
        for line in ("X-Content-Type-Options: nosniff", "Referrer-Policy: strict-origin-when-cross-origin",
                     "X-Frame-Options: DENY", "Strict-Transport-Security: max-age=31536000"):
            self.assertIn(line, HEADERS)
        self.assertRegex(HEADERS, r"Permissions-Policy: [^\n]*geolocation=\(\)")
        self.assertRegex(HEADERS, r"Permissions-Policy: [^\n]*camera=\(\)")


class Prep(unittest.TestCase):
    FRAGMENT = ('<title>Civic Guide</title>\n<meta charset="utf-8">\n<meta name="description" content="x">\n'
                + LOOK_BOOT + '\n<a class="skip-link" href="#main">Skip</a>\n<div id="site"></div>\n'
                '<script type="application/json" id="here-data">{"a":1}</script>\n'
                '<script src="assets/app.js" defer></script>\n')

    def test_full_root_document(self):
        out = N.full_root_document(self.FRAGMENT)
        self.assertTrue(out.startswith("<!doctype html>\n<html lang=\"en\">\n<meta charset=\"utf-8\">\n"))
        self.assertIn('name="viewport"', out)
        self.assertEqual(out.count('<meta charset="utf-8">'), 1)
        self.assertEqual(N.full_root_document(out), out)  # idempotent

    def _site(self, extra_page: str | None = None) -> Path:
        d = Path(tempfile.mkdtemp()) / "st-joseph"
        d.mkdir()
        (d / "index.html").write_text(self.FRAGMENT, encoding="utf-8")
        if extra_page is not None:
            (d / "p").mkdir()
            (d / "p" / "index.html").write_text(extra_page, encoding="utf-8")
        return d

    def _quiet(self, fn):
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            return fn()

    def test_prepare_writes_files_and_passes(self):
        d = self._site()
        self.assertEqual(self._quiet(lambda: N.prepare(d)), 0)
        self.assertTrue((d / "index.html").read_text(encoding="utf-8").startswith("<!doctype html>"))
        self.assertEqual((d / "_headers").read_text(encoding="utf-8"), HEADERS)
        page404 = (d / "404.html").read_text(encoding="utf-8")
        self.assertTrue(page404.startswith("<!doctype html>"))
        self.assertNotIn("{{", page404)
        self.assertIn(LOOK_BOOT, page404)

    def test_prepare_refuses_csp_breakers(self):
        for bad in ('<!doctype html><script>alert(1)</script>',
                    '<!doctype html><button onclick="x()">x</button>',
                    '<!doctype html><style>p{}</style>',
                    '<!doctype html><script type="module">import x from "./x.js"</script>'):
            d = self._site(bad)
            self.assertEqual(self._quiet(lambda: N.prepare(d)), 1, bad)

    def test_json_data_blocks_are_not_flagged(self):
        d = self._site('<!doctype html><script type="application/json" id="x">{"onload=":"<b>"}</script>')
        self.assertEqual(self._quiet(lambda: N.prepare(d)), 0)


if __name__ == "__main__":
    unittest.main()
