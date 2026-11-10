"""Prepare a built edition for Netlify (security review 2026-11-09). Run AFTER build.py:

    python -P -E tools/site/build.py --edition st-joseph --check
    python -P -E tools/site/netlify_prep.py site/st-joseph

What it does to the publish directory (and nothing else):
  1. index.html: the build writes the root page as a fragment for the claude.ai Artifact host, which wraps it.
     Netlify serves files as they are, so the fragment would render in quirks mode with no viewport (phone layout
     broken). The fragment gets a doctype, <html lang>, charset and viewport in front; head/body tags are optional
     in HTML, so the parser places the rest exactly as the host's wrapper did. Idempotent.
  2. Copies tools/site/netlify/_headers (security headers incl. Content-Security-Policy, caching).
  3. Writes 404.html from tools/site/netlify/404.html.
  4. Refuses (exit 1) when the output breaks the CSP: an executable inline <script> whose sha256 is not in
     _headers, an inline on*= event handler, or an inline <style> element.

Run the checker (build.py --check) BEFORE this step: check.py requires the Artifact-host form of index.html.
Python 3 standard library only.
"""
from __future__ import annotations

import base64
import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # -P drops the script dir from sys.path; add it back explicitly

from civic.shell import FONTS, LOOK_BOOT, rights_html  # noqa: E402

NETLIFY = HERE / "netlify"
DOC_START = ('<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n'
             '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n')
# an executable inline script: no src, and no type, or a JavaScript type
INLINE_SCRIPT = re.compile(r"<script\b(?![^>]*\bsrc=)([^>]*)>(.*?)</script>", re.S | re.I)
JS_TYPE = re.compile(r'\btype="(?:text/javascript|module|application/javascript)"', re.I)
EVENT_ATTR = re.compile(r"<[a-zA-Z][^<>]*?\son[a-z]+\s*=", re.S)
STYLE_EL = re.compile(r"<style\b", re.I)


def csp_hashes(headers_text: str) -> set[str]:
    m = re.search(r"Content-Security-Policy:([^\n]*)", headers_text)
    if not m:
        return set()
    script = re.search(r"script-src([^;]*)", m.group(1))
    return set(re.findall(r"'sha256-([A-Za-z0-9+/=]+)'", script.group(1) if script else ""))


def sha256_b64(text: str) -> str:
    return base64.b64encode(hashlib.sha256(text.encode("utf-8")).digest()).decode("ascii")


def full_root_document(text: str) -> str:
    """The Artifact-host fragment as a complete document; a page that already has a doctype is unchanged."""
    if re.match(r"\s*<!doctype", text, re.I):
        return text
    body = text.replace('<meta charset="utf-8">\n', "", 1)  # the new head carries it first
    return DOC_START + body


def page_404(ed_config: dict) -> str:
    t = (NETLIFY / "404.html").read_text(encoding="utf-8")
    from civic.html import esc
    return (t.replace("{{look_boot}}", LOOK_BOOT).replace("{{fonts}}", str(esc(FONTS)))
             .replace("{{rights}}", str(rights_html(ed_config)))
             .replace("{{series}}", str(esc(ed_config.get("series", "Civic Guide"))))
             .replace("{{edition}}", str(esc(ed_config.get("edition", "")))))


def csp_problems(out: Path, allowed: set[str]) -> list[str]:
    problems = []
    for p in sorted(out.rglob("*.html")):
        rel = p.relative_to(out).as_posix()
        src = p.read_text(encoding="utf-8")
        for attrs, body in INLINE_SCRIPT.findall(src):
            if "type=" in attrs and not JS_TYPE.search(attrs):
                continue  # a data block (application/json): never executed
            if sha256_b64(body) not in allowed:
                problems.append(f"{rel}: inline script not allowed by the CSP (sha256-{sha256_b64(body)})")
        if EVENT_ATTR.search(src):
            problems.append(f"{rel}: inline on*= event handler (blocked by the CSP)")
        if STYLE_EL.search(src):
            problems.append(f"{rel}: inline <style> element (blocked by the CSP)")
    return problems


def prepare(out: Path) -> int:
    import json
    out = Path(out)
    index = out / "index.html"
    if not index.is_file():
        print(f"netlify_prep: {index} not found; build the edition first")
        return 1
    index.write_text(full_root_document(index.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
    headers = (NETLIFY / "_headers").read_text(encoding="utf-8")
    (out / "_headers").write_text(headers, encoding="utf-8", newline="\n")
    cfg = {}
    for ed_json in (HERE.parents[1] / "data" / "editions" / out.name / "edition.json",):
        if ed_json.is_file():
            cfg = json.loads(ed_json.read_text(encoding="utf-8"))
    (out / "404.html").write_text(page_404(cfg), encoding="utf-8", newline="\n")
    problems = csp_problems(out, csp_hashes(headers))
    for pr in problems[:50]:
        print(f"CSP: {pr}")
    if problems:
        print(f"netlify_prep: FAILED, {len(problems)} CSP problem(s). Fix the page or add the hash to "
              f"tools/site/netlify/_headers.")
        return 1
    print(f"netlify_prep: {out} ready (full-document index.html, _headers, 404.html; CSP check passed)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -P -E tools/site/netlify_prep.py site/<edition>")
    raise SystemExit(prepare(Path(sys.argv[1])))
