"""Checks a built edition against the hosting contract and the neutrality rules.

    python -P -E tools/site/check.py site/st-joseph

Checks:
  1. every internal link/src resolves to a file (and its #fragment to an id, except #path-* stops)
  2. every page has a non-empty <title>
  3. index.html has no doctype/html/head/body tags; every other page is a full document
     (doctype, <html lang>, <head>, meta charset, viewport, claude:viewport-fit-sides, <body>)
  4. no literal colors (hex / rgb() / hsl()) in CSS outside the TOKENS block, none in HTML style/fill attributes
  5. no banned terms in visible generated text (verbatim source titles marked data-verbatim are
     exempt but listed as NOTE lines)
  6. contract extras: no <a download>, no window.print/alert/confirm/prompt, external scripts/styles only from
     allowed hosts, reserved hash names unused
Exit code 0 = all passed.
"""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from civic.neutrality import find_banned  # noqa: E402

ALLOWED_STYLE_HOSTS = {"fonts.googleapis.com"}
ALLOWED_SCRIPT_HOSTS = {"cdnjs.cloudflare.com", "cdn.jsdelivr.net", "unpkg.com", "cdn.tailwindcss.com", "code.jquery.com"}
RESERVED_HASHES = {"settings", "sidebar", "customize", "upgrade", "downloads"}
COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []   # (attr, value)
        self.ids: set[str] = set()
        self.tags: list[str] = []
        self.title = ""
        self._in_title = False
        self._skip = 0
        self.text: list[str] = []
        self.has_lang = False
        self.meta: list[dict] = []
        self.downloads = 0
        self.color_attrs: list[str] = []
        self.ext: list[tuple[str, str]] = []
        self._verb: list[str] = []      # open tags that carry data-verbatim
        self.verbatim: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append(tag)
        if "id" in a and a["id"]:
            self.ids.add(a["id"])
        if tag == "html" and a.get("lang"):
            self.has_lang = True
        if tag == "meta":
            self.meta.append(a)
        if tag == "title":
            self._in_title = True
        if tag in ("script", "style"):
            self._skip += 1
        if "data-verbatim" in a:
            self._verb.append(tag)
            self.verbatim.append("")
        if tag == "a" and "download" in a:
            self.downloads += 1
        for k in ("href", "src"):
            if a.get(k):
                self.links.append((tag, a[k]))
        if tag == "link" and a.get("rel") == "stylesheet" and a.get("href", "").startswith("http"):
            self.ext.append(("style", a["href"]))
        if tag == "script" and a.get("src", "").startswith("http"):
            self.ext.append(("script", a["src"]))
        for k in ("style", "fill", "stroke", "color", "bgcolor"):
            if a.get(k) and COLOR_RE.search(a[k]):
                self.color_attrs.append(f"<{tag} {k}={a[k]!r}>")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag in ("script", "style"):
            self._skip -= 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
        if self._verb and self._verb[-1] == tag:
            self._verb.pop()

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._verb:
            self.verbatim[-1] += data
        elif not self._skip:
            self.text.append(data)

    def handle_decl(self, decl):
        self.tags.append("!" + decl.split()[0].lower())


def run(site_dir) -> int:
    site_dir = Path(site_dir).resolve()
    pages = sorted(site_dir.rglob("*.html"))
    problems: list[str] = []
    notes: list[str] = []
    parsed: dict[Path, PageParser] = {}
    raw: dict[Path, str] = {}
    for p in pages:
        src = p.read_text(encoding="utf-8")
        raw[p] = src
        pp = PageParser()
        pp.feed(src)
        parsed[p] = pp

    for p, pp in parsed.items():
        rel = p.relative_to(site_dir).as_posix()
        src = raw[p]
        # 2 title
        if not pp.title.strip():
            problems.append(f"{rel}: missing or empty <title>")
        # 3 index vs full document
        is_root_index = rel == "index.html"
        has_doctype = bool(re.match(r"\s*<!doctype html", src, re.I))
        if is_root_index:
            for t in ("html", "head", "body"):
                if re.search(rf"<{t}[\s>]", src, re.I) or re.search(rf"</{t}>", src, re.I):
                    problems.append(f"{rel}: root index.html must not contain <{t}>")
            if re.search(r"<!doctype", src, re.I):
                problems.append(f"{rel}: root index.html must not contain a doctype")
            if not src.lstrip().startswith("<title>"):
                problems.append(f"{rel}: root index.html should start with <title>")
        else:
            if not has_doctype:
                problems.append(f"{rel}: missing <!doctype html>")
            if not pp.has_lang:
                problems.append(f"{rel}: missing <html lang>")
            for t in ("head", "body"):
                if t not in pp.tags:
                    problems.append(f"{rel}: missing <{t}>")
            names = {(m.get("name") or "").lower() for m in pp.meta}
            if not any(m.get("charset") for m in pp.meta):
                problems.append(f"{rel}: missing <meta charset>")
            if "viewport" not in names:
                problems.append(f"{rel}: missing viewport meta")
        if not any((m.get("name") or "") == "claude:viewport-fit-sides" for m in pp.meta):
            problems.append(f"{rel}: missing claude:viewport-fit-sides meta")
        # 1 links
        for tag, url in pp.links:
            u = urlparse(url)
            if u.scheme in ("http", "https"):
                continue
            if u.scheme in ("mailto", "tel", "javascript", "data", "blob"):
                problems.append(f"{rel}: disallowed link scheme {url}")
                continue
            if url.startswith("/"):
                problems.append(f"{rel}: absolute path link {url} (must be relative)")
                continue
            if "?" in url:
                problems.append(f"{rel}: query string in link {url}")
            path, _, frag = url.partition("#")
            target = (p.parent / unquote(path)).resolve() if path else p
            if path and not target.is_file():
                problems.append(f"{rel}: broken link {url}")
                continue
            if frag:
                if frag in RESERVED_HASHES or frag.startswith("comment-"):
                    problems.append(f"{rel}: reserved hash #{frag}")
                if not re.fullmatch(r"[A-Za-z0-9-]+", frag):
                    problems.append(f"{rel}: hash #{frag} has characters other than letters, digits, hyphens")
                if frag.startswith("path-"):
                    continue
                if target.suffix == ".html":
                    tp = parsed.get(target)
                    if tp is not None and frag not in tp.ids:
                        problems.append(f"{rel}: link {url} points to a missing id")
        # 5 banned words
        text = " ".join(pp.text)
        for term in sorted(set(t.lower() for t in find_banned(text))):
            ctx = re.search(r".{0,40}\b" + re.escape(term) + r"\b.{0,40}", text, re.I | re.S)
            problems.append(f"{rel}: banned term '{term}' in text: ...{ctx.group(0).strip() if ctx else ''}...")
        for vt in pp.verbatim:
            for term in sorted(set(t.lower() for t in find_banned(vt))):
                notes.append(f"{rel}: '{term}' appears in a verbatim source title (exempt): {vt.strip()[:90]}")
        # 6 contract extras
        if pp.downloads:
            problems.append(f"{rel}: <a download> is inert on the host")
        for kind, url in pp.ext:
            host = urlparse(url).hostname or ""
            allowed = ALLOWED_STYLE_HOSTS if kind == "style" else ALLOWED_SCRIPT_HOSTS
            if host not in allowed:
                problems.append(f"{rel}: external {kind} from {host}")
        for c in pp.color_attrs:
            problems.append(f"{rel}: literal color in markup {c}")
        if re.search(r"<style[\s>]", src, re.I):
            for block in re.findall(r"<style[^>]*>(.*?)</style>", src, re.I | re.S):
                if COLOR_RE.search(block):
                    problems.append(f"{rel}: literal color in inline <style>")

    # 4 CSS
    for css in sorted(site_dir.rglob("*.css")):
        text = css.read_text(encoding="utf-8")
        rel = css.relative_to(site_dir).as_posix()
        stripped = re.sub(r"/\*\s*TOKENS:BEGIN\s*\*/.*?/\*\s*TOKENS:END\s*\*/", "", text, flags=re.S)
        if stripped == text:
            problems.append(f"{rel}: no TOKENS:BEGIN/END block found")
        stripped = re.sub(r"/\*.*?\*/", "", stripped, flags=re.S)
        for m in COLOR_RE.finditer(stripped):
            line = stripped[:m.start()].count("\n") + 1
            problems.append(f"{rel}: literal color '{m.group(0)}' outside the token block (line ~{line})")
        if "{{" in text:
            problems.append(f"{rel}: unfilled template placeholder")
        if "prefers-color-scheme: dark" not in text or ':root[data-theme="dark"]' not in text:
            problems.append(f"{rel}: dark tokens must be defined under prefers-color-scheme AND :root[data-theme=\"dark\"]")
    for js in sorted(site_dir.rglob("*.js")):
        text = js.read_text(encoding="utf-8")
        for bad in ("window.print(", "alert(", "confirm(", "prompt(", "innerHTML"):
            if bad in text:
                problems.append(f"{js.relative_to(site_dir).as_posix()}: uses {bad}")

    for n in sorted(set(notes)):
        print(f"NOTE {n}")
    print(f"Checked {len(pages)} pages, {len(list(site_dir.rglob('*.css')))} stylesheet(s).")
    if problems:
        print(f"FAILED: {len(problems)} problem(s)")
        for pr in problems:
            print(f"  - {pr}")
        return 1
    print("PASSED: links, titles, document structure, CSS tokens, neutrality terms, contract extras.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(run(sys.argv[1]))
