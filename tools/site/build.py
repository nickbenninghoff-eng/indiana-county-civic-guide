"""Build one county edition of the Indiana County Civic Guide.

    python -P -E tools/site/build.py --edition st-joseph [--check]

Reads data/indiana/* and data/editions/<edition>/* and writes site/<edition>/.
Python 3 standard library only.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # -P drops the script dir from sys.path; add it back explicitly

from civic.data import Edition  # noqa: E402
from civic.shell import Site  # noqa: E402
import importlib  # noqa: E402
import pkgutil  # noqa: E402

import pages  # noqa: E402
from pages import county, indiana_map, landing, stubs  # noqa: E402

# Real page builders, by site path. Every other sitemap entry gets a stub.
BUILDERS = {
    "index.html": landing.build,
    "county/index.html": county.build,
    "indiana/index.html": indiana_map.build,
}


FAILED: list[str] = []


def discover_builders() -> None:
    """Parallel-safe page registration: any pages/<name>.py module that defines
    PAGES = {"site/path.html": build_function, ...} is registered automatically,
    so agents adding pages never need to edit this file."""
    for info in pkgutil.iter_modules(pages.__path__):
        if info.name in {"stubs"}:
            continue
        try:
            mod = importlib.import_module(f"pages.{info.name}")
        except Exception as e:  # another agent's module mid-edit must not break everyone's build
            print(f"ERROR: skipped pages/{info.name}.py (import failed: {type(e).__name__}: {e}); its pages build as stubs")
            FAILED.append(f"pages/{info.name}.py (import)")
            continue
        for path, fn in getattr(mod, "PAGES", {}).items():
            if path in BUILDERS and BUILDERS[path] is not fn:
                raise SystemExit(f"page {path} is registered twice (pages/{info.name}.py)")
            BUILDERS[path] = fn


def _concat(base: Path, partial_dir: Path, pattern: str) -> str:
    """The base file, then every partial in partial_dir (sorted by name), each tagged with its origin."""
    parts = [base.read_text(encoding="utf-8")]
    if partial_dir.is_dir():
        for p in sorted(partial_dir.glob(pattern)):
            parts.append(f"\n/* ---- {partial_dir.name}/{p.name} ---- */\n" + p.read_text(encoding="utf-8"))
    return "\n".join(parts)


def write_assets(ed, out: Path) -> None:
    """style.css = static/style.css + static/css/*.css; app.js = static/app.js + static/js/*.js.
    Area-specific styles and scripts go in their own partial files (parallel-safe)."""
    assets = out / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    color = ed.config["edition_color"]
    css = _concat(HERE / "static" / "style.css", HERE / "static" / "css", "*.css")
    css = css.replace("{{edition_light}}", color["light"]).replace("{{edition_dark}}", color["dark"])
    (assets / "style.css").write_text(css, encoding="utf-8", newline="\n")
    js = _concat(HERE / "static" / "app.js", HERE / "static" / "js", "*.js")
    (assets / "app.js").write_text(js, encoding="utf-8", newline="\n")
    # Licensed images (portraits, historic photos) ship as published files.
    img_src = repo_root() / "site" / "images"
    if img_src.is_dir():
        img_out = out / "images"
        img_out.mkdir(exist_ok=True)
        for f in img_src.iterdir():
            if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}:
                target = img_out / f.name
                if not target.exists() or target.stat().st_mtime < f.stat().st_mtime:
                    target.write_bytes(f.read_bytes())


def repo_root() -> Path:
    return HERE.parents[1]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--edition", required=True, help="folder name under data/editions/")
    ap.add_argument("--check", action="store_true", help="run check.py on the output afterwards")
    args = ap.parse_args(argv)

    repo = HERE.parents[1]
    ed = Edition.load(repo, args.edition)
    out = repo / "site" / args.edition
    site = Site(ed, out)
    discover_builders()

    for entry in site.entries:
        builder = BUILDERS.get(entry.path)
        if builder:
            try:
                builder(site)
            except Exception as e:  # a failing page becomes a stub; the error is reported, never hidden
                print(f"ERROR building {entry.path}: {type(e).__name__}: {e} (built as stub)")
                site.pages.pop(entry.path, None)
                stubs.build_stub(site, entry)
                FAILED.append(entry.path)
        else:
            stubs.build_stub(site, entry)

    # remove stale generated pages (only .html files this build no longer writes)
    keep = {(out / p).resolve() for p in site.pages}
    if out.is_dir():
        for old in out.rglob("*.html"):
            if old.resolve() not in keep:
                old.unlink()
    written = site.write()
    write_assets(ed, out)

    unknown = sorted({s for p in site.pages.values() for s in p.cites.unknown})
    warnings = list(dict.fromkeys(ed.warnings))
    if unknown:
        warnings.append(f"citations to unknown source ids: {', '.join(unknown)}")
    print(f"Built {len(written)} pages into {out}")
    if warnings:
        print(f"\nData warnings ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
    if FAILED:
        print(f"\nFAILED page builders ({len(FAILED)}): {', '.join(FAILED)}")
    rc = 0
    if args.check:
        import check
        rc = check.run(out)
    if FAILED:
        # Last line on purpose: a passing checker must not hide a page that built as a stub.
        print(f"BUILD FAILED: {len(FAILED)} page module(s)/builder(s) failed and were built as stubs: {', '.join(FAILED)}")
    return rc or (1 if FAILED else 0)


if __name__ == "__main__":
    raise SystemExit(main())
