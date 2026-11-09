"""OCR the county's scanned 2020 general-election Precinct Summary Report into a layout text file.

    python -P -E tools/ocr_2020_precinct_report.py [--pages 1-590] [--zoom 3] [--out FILE]

Input : sources/precincts/openelections-sources-in/2020-GE-St-Joseph-Precinct.pdf  (MAP-009; 590 scanned pages,
        12/9/2020, archived by OpenElections). The PDF has no text layer.
Output: sources/precincts/openelections-sources-in/2020-GE-St-Joseph-Precinct.ocr.txt (default)

The build uses three independent reads at different render sizes, made with
    python -P -E tools/ocr_2020_precinct_report.py
    python -P -E tools/ocr_2020_precinct_report.py --zoom 4 --out sources/precincts/openelections-sources-in/2020-GE-St-Joseph-Precinct.ocr-4x.txt
    python -P -E tools/ocr_2020_precinct_report.py --zoom 2.5 --out sources/precincts/openelections-sources-in/2020-GE-St-Joseph-Precinct.ocr-2.5x.txt
(about 3 minutes each). OCR drops a number now and then; a race box only needs to pass every check in one read, and
every read that passes must agree (tools/precinct_report_2020.py).

Each page is rendered with PyMuPDF (grayscale, --zoom x 72 dpi) and read by the built-in Windows OCR engine
(tools/winocr_words.ps1, word boxes). Words are then put back on their printed rows: the report prints a header,
then two columns of boxed races, so every page is written as

    #### PAGE 12
    <header rows>
    ## LEFT
    <rows of the left column, top to bottom>
    ## RIGHT
    <rows of the right column>

with two or more spaces wherever the printed row has a column gap (name | votes | percent). The text is raw OCR:
tools/build_precinct_results.py parses it and accepts a race in a precinct only when the candidate votes add up to the
printed Total Votes and every printed percentage equals votes / Total Votes, then checks the county or district
sums against the official canvass. Needs Windows 10/11 (Windows.Media.Ocr) and PyMuPDF (fitz).
"""
from __future__ import annotations

import argparse
import re
import statistics
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "sources" / "precincts" / "openelections-sources-in" / "2020-GE-St-Joseph-Precinct.pdf"
OUT = PDF.with_suffix(".ocr.txt")
PS1 = ROOT / "tools" / "winocr_words.ps1"


def page_range(spec: str, n: int):
    out = []
    for part in spec.split(","):
        a, _, b = part.partition("-")
        lo, hi = int(a), int(b or a)
        out += list(range(max(1, lo), min(n, hi) + 1))
    return out


def rows_of(words):
    """Group words (x, y, w, h, text) into printed rows by vertical centre; return [[words sorted by x], ...]."""
    if not words:
        return []
    hmed = statistics.median(w[3] for w in words)
    rows = []
    for w in sorted(words, key=lambda w: w[1] + w[3] / 2):
        yc = w[1] + w[3] / 2
        if rows and abs(yc - rows[-1][0]) <= 0.45 * hmed:
            r = rows[-1]
            r[1].append(w)
            r[0] = sum(v[1] + v[3] / 2 for v in r[1]) / len(r[1])
        else:
            rows.append([yc, [w]])
    return [sorted(r[1], key=lambda w: w[0]) for r in rows]


def row_text(row):
    hmed = statistics.median(w[3] for w in row)
    parts = [row[0][4]]
    for prev, w in zip(row, row[1:]):
        gap = w[0] - (prev[0] + prev[2])
        parts.append(("    " if gap > 1.6 * hmed else " ") + w[4])
    return "".join(parts)


def layout(words, width):
    """Header rows, left-column rows, right-column rows for one page."""
    # The header ends at the 'Registered Voters ... Total Ballots' row; the two columns start below it.
    reg = [w for w in words if w[4].lower().startswith("registered")]
    top = (reg[0][1] + reg[0][3] * 1.5) if reg else 0.17 * max(w[1] + w[3] for w in words)
    head = [w for w in words if w[1] + w[3] / 2 <= top]
    body = [w for w in words if w[1] + w[3] / 2 > top]
    mid = width / 2
    left = [w for w in body if w[0] + w[2] / 2 < mid]
    right = [w for w in body if w[0] + w[2] / 2 >= mid]
    return [row_text(r) for r in rows_of(head)], [row_text(r) for r in rows_of(left)], [row_text(r) for r in rows_of(right)]


def main():
    import fitz  # PyMuPDF
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default=None, help="e.g. 1-590 (default: all)")
    ap.add_argument("--zoom", type=float, default=3.0)
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    doc = fitz.open(PDF)
    pages = page_range(args.pages, doc.page_count) if args.pages else list(range(1, doc.page_count + 1))
    widths = {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for p in pages:
            pix = doc[p - 1].get_pixmap(matrix=fitz.Matrix(args.zoom, args.zoom), colorspace=fitz.csGRAY)
            pix.save(tmp / f"p{p:04d}.png")
            widths[p] = pix.width
        tsv = tmp / "words.tsv"
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PS1),
                        "-Dir", str(tmp), "-OutFile", str(tsv)], check=True)
        words = defaultdict(list)
        for line in tsv.read_text(encoding="utf-8-sig").splitlines():
            f = line.split("\t")
            if len(f) < 7:
                continue
            p = int(re.match(r"p(\d+)\.png", f[0]).group(1))
            words[p].append((int(f[2]), int(f[3]), int(f[4]), int(f[5]), f[6]))
    out = [f"# OCR of {PDF.name} (county 2020 general Precinct Summary Report, source MAP-009) by "
           f"tools/ocr_2020_precinct_report.py: PyMuPDF render at {args.zoom:g}x, Windows.Media.Ocr. Raw OCR, not corrected."]
    for p in pages:
        head, left, right = layout(words.get(p, []), widths[p]) if words.get(p) else ([], [], [])
        out.append(f"#### PAGE {p}")
        out += head
        out.append("## LEFT")
        out += left
        out.append("## RIGHT")
        out += right
    Path(args.out).write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {args.out}: {len(pages)} pages")


if __name__ == "__main__":
    sys.exit(main())
