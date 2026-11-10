"""Inline-SVG chart toolkit (Python -> SVG), following the dataviz rules:

* one axis, full available range, hairline solid grid, 2px lines,
  bars <= 24px thick with a 4px rounded data end and a square baseline end,
  2px surface gaps between touching marks, selective direct labels;
* colors only through CSS classes (m-accent, m-ink, m-party-D, m-party-R, m-party-other,
  m-nodata, m-low) so both themes work; text never wears a data color;
* every mark that carries a value has data-tv (value) / data-tl (label) for the app.js
  tooltip and is focusable; every chart has a <details> table view twin (works without JS).

Party colors are used ONLY by party_timeline() and results_bars(), always with text labels.
"""
from __future__ import annotations

import json
import math

from .components import data_table, party_label, status_badge
from .html import Markup, esc, h, join

FONT = 12          # px, chart text
CHAR_SANS = 0.56   # approx glyph width as a fraction of font size
CHAR_MONO = 0.62


def text_w(s: str, size: int = FONT, mono: bool = False) -> float:
    return len(str(s)) * size * (CHAR_MONO if mono else CHAR_SANS)


def nice_ticks(vmax: float, n: int = 4) -> list[float]:
    if vmax <= 0:
        return [0, 1]
    raw = vmax / n
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if step >= raw:
            break
    top = math.ceil(vmax / step) * step
    ticks, v = [], 0.0
    while v <= top + step * 1e-9:
        ticks.append(round(v, 10))
        v += step
    return ticks


def fmt_tick(v: float, vmax: float, money: bool = False) -> str:
    pre = "$" if money else ""
    if vmax >= 1e9:
        return f"{pre}{v / 1e9:g}B"
    if vmax >= 1e6:
        return f"{pre}{v / 1e6:g}M"
    if vmax >= 1e4:
        return f"{pre}{v / 1e3:g}K"
    return f"{pre}{v:,.0f}" if v == int(v) else f"{pre}{v:,.1f}"


def bar_path(x0: float, y0: float, x1: float, y1: float, orient: str, r: float = 4) -> str:
    """Rect with the data end rounded (r) and the baseline end square.
    orient 'right': baseline at x0, grows to x1. 'up': baseline at y1 (bottom), grows to y0."""
    if orient == "right":
        w = x1 - x0
        r = max(0, min(r, w / 2, (y1 - y0) / 2))
        return (f"M{x0:.1f},{y0:.1f}H{x1 - r:.1f}Q{x1:.1f},{y0:.1f} {x1:.1f},{y0 + r:.1f}"
                f"V{y1 - r:.1f}Q{x1:.1f},{y1:.1f} {x1 - r:.1f},{y1:.1f}H{x0:.1f}Z")
    hgt = y1 - y0
    r = max(0, min(r, hgt / 2, (x1 - x0) / 2))
    return (f"M{x0:.1f},{y1:.1f}V{y0 + r:.1f}Q{x0:.1f},{y0:.1f} {x0 + r:.1f},{y0:.1f}"
            f"H{x1 - r:.1f}Q{x1:.1f},{y0:.1f} {x1:.1f},{y0 + r:.1f}V{y1:.1f}Z")


def _svg(width: float, height: float, label: str, *children, cls: str = "chart-svg", extra: dict | None = None) -> Markup:
    a = {"class": cls, "viewBox": f"0 0 {width:.0f} {height:.0f}", "width": f"{width:.0f}",
         "height": f"{height:.0f}", "role": "img", "aria-label": label}
    if extra:
        a.update(extra)
    return h("svg", a, children)


def _txt(x, y, s, cls="ct", anchor="start", **kw) -> Markup:
    a = {"x": f"{x:.1f}", "y": f"{y:.1f}", "class": cls, "text-anchor": anchor}
    a.update(kw)
    return h("text", a, s)


def _wrap2(s: str, max_w: float) -> list[str]:
    """A label as one line, or two lines split at the space that best balances them when one line is wider than
    ``max_w`` (theme pass C, 2026-11-09: hbar labels past the label column were cut off at the SVG edge)."""
    s = str(s)
    if text_w(s) <= max_w or " " not in s:
        return [s]
    words = s.split(" ")
    best = min(((max(text_w(" ".join(words[:i])), text_w(" ".join(words[i:]))), i) for i in range(1, len(words))))
    return [" ".join(words[:best[1]]), " ".join(words[best[1]:])]


def figure(fid: str, title: str, subtitle: str | None, svg: Markup, headers: list, rows: list[list],
           note: Markup | str | None = None, numeric: tuple[int, ...] = (), status: str | None = None,
           page=None, legend: Markup | None = None, kind: str = "chart", extra: dict | None = None,
           scroll: bool = True, cite: Markup | None = None) -> Markup:
    """Wrap an SVG in the standard figure: caption, legend, body, note, table view."""
    a = {"class": f"chart chart-{kind}", "id": fid, "data-chart": kind}
    if extra:
        a.update(extra)
    return h("figure", a,
             h("figcaption", {"class": "chart-cap"},
               h("span", {"class": "chart-title"}, title, cite),
               status_badge(status, page) if status else None,
               h("span", {"class": "chart-sub"}, subtitle) if subtitle else None),
             legend,
             h("div", {"class": "chart-body" + (" chart-scroll" if scroll else "")}, svg),
             h("p", {"class": "chart-note"}, note) if note else None,
             h("details", {"class": "chart-table", "id": f"{fid}-details"},
               h("summary", {"class": "btn btn-small"}, "Show table"),
               data_table(f"{fid}-table", headers, rows, caption=title, numeric=numeric)))


def legend(items: list[tuple[str, str]], shape: str = "rect") -> Markup:
    """items: (css mark class, label). shape mirrors the mark: rect | line | dot | ring | square."""
    lis = []
    for cls, label in items:
        lis.append(h("li", None, h("span", {"class": f"key key-{shape} {cls}", "aria-hidden": "true"}), label))
    return h("ul", {"class": "legend"}, lis)


# ------------------------------------------------------------------ horizontal bar

def hbar(fid: str, title: str, rows: list[dict], subtitle: str | None = None, mark: str = "m-accent",
         value_fmt=lambda v: f"{v:,.0f}", money: bool = False, note=None, status=None, page=None,
         headers: list | None = None, cite=None) -> Markup:
    """rows: [{label, value, display?, tip?}] in the order given (sort before calling)."""
    vals = [r["value"] for r in rows if r.get("value") is not None]
    vmax = max(vals) if vals else 1
    ticks = nice_ticks(vmax)
    top = ticks[-1]
    label_w = min(230, max([text_w(r["label"]) for r in rows] + [40]) + 12)
    # a label wider than the 230 px column wraps onto two lines in a column of up to 300 px (it was cut off)
    lines = {i: _wrap2(r["label"], 218) for i, r in enumerate(rows)}
    if any(len(v) > 1 for v in lines.values()):
        label_w = min(300, max(text_w(x) for v in lines.values() for x in v) + 12)
    value_w = max([text_w(r.get("display") or value_fmt(r["value"]), mono=True) for r in rows if r.get("value") is not None] + [30]) + 14
    W = 620
    plot_w = W - label_w - value_w
    row_h, bar_h, pad_t = 30, 16, 8
    H = pad_t + row_h * len(rows) + 26
    x = lambda v: label_w + plot_w * (v / top)
    grid = [h("line", {"x1": f"{x(t):.1f}", "x2": f"{x(t):.1f}", "y1": pad_t, "y2": H - 22, "class": "grid"}) for t in ticks]
    tl = [_txt(x(t), H - 8, fmt_tick(t, top, money), "ct ct-axis", "middle") for t in ticks]
    marks = []
    for i, r in enumerate(rows):
        y0 = pad_t + i * row_h + (row_h - bar_h) / 2
        disp = r.get("display") or (value_fmt(r["value"]) if r.get("value") is not None else "no data")
        lab = _txt(label_w - 8, y0 + bar_h - 4, r["label"], "ct", "end")
        if len(lines[i]) > 1:
            lab = h("text", {"x": f"{label_w - 8:.1f}", "y": f"{y0 + 5:.1f}", "class": "ct ct-small", "text-anchor": "end"},
                    h("tspan", {"x": f"{label_w - 8:.1f}", "y": f"{y0 + 5:.1f}"}, lines[i][0]),
                    h("tspan", {"x": f"{label_w - 8:.1f}", "y": f"{y0 + 17:.1f}"}, lines[i][1]))
        if r.get("value") is None:
            marks.append(h("g", None, lab, _txt(label_w + 4, y0 + bar_h - 4, "no data", "ct ct-muted")))
            continue
        x1 = max(x(r["value"]), label_w + 1)
        marks.append(h("g", {"class": "mark", "tabindex": "0", "data-tv": disp, "data-tl": r.get("tip") or r["label"]},
                       h("rect", {"class": "hit", "x": 0, "y": f"{pad_t + i * row_h:.1f}", "width": W, "height": row_h}),
                       lab,
                       h("path", {"class": f"bar {r.get('mark', mark)}", "d": bar_path(label_w, y0, x1, y0 + bar_h, "right")}),
                       _txt(x1 + 6, y0 + bar_h - 4, disp, "ct ct-val")))
    base = h("line", {"x1": label_w, "x2": label_w, "y1": pad_t, "y2": H - 22, "class": "axis"})
    svg = _svg(W, H, f"{title}. Bar chart; values in the table view.", grid, tl, base, marks)
    hdr = headers or ["Item", "Value"]
    trows = [[r["label"], r.get("display") or (value_fmt(r["value"]) if r.get("value") is not None else "no data")] for r in rows]
    return figure(fid, title, subtitle, svg, hdr, trows, note=note, numeric=(1,), status=status, page=page,
                  kind="hbar", cite=cite)


# ------------------------------------------------------------------ vertical columns

def columns(fid: str, title: str, points: list[dict], subtitle: str | None = None, mark: str = "m-accent",
            breaks: list[dict] | None = None, value_fmt=lambda v: f"{v:,.0f}", money: bool = False,
            note=None, status=None, page=None, headers: list | None = None, cite=None) -> Markup:
    """points: [{x, value, display?, tip?, status?}] in x order.
    breaks: [{after: index, label, tip}] draws a series-break marker between columns."""
    vals = [p["value"] for p in points if p.get("value") is not None]
    vmax = max(vals) if vals else 1
    ticks = nice_ticks(vmax)
    top = ticks[-1]
    axis_w = max(text_w(fmt_tick(t, top, money), mono=True) for t in ticks) + 10
    n = max(len(points), 1)
    W = max(360, min(760, axis_w + n * 36 + 16))
    plot_l, plot_r, plot_t, plot_b = axis_w, W - 8, 24, 220
    H = plot_b + 30
    band = (plot_r - plot_l) / n
    cw = min(24, band * 0.62)
    y = lambda v: plot_b - (plot_b - plot_t) * (v / top)
    grid = [h("line", {"x1": plot_l, "x2": plot_r, "y1": f"{y(t):.1f}", "y2": f"{y(t):.1f}", "class": "grid" if t else "axis"}) for t in ticks]
    tl = [_txt(plot_l - 6, y(t) + 4, fmt_tick(t, top, money), "ct ct-axis", "end") for t in ticks]
    every = max(1, math.ceil(n / ((plot_r - plot_l) / 34)))
    labelled = set()
    if vals:
        idx = [i for i, p in enumerate(points) if p.get("value") is not None]
        labelled = {idx[-1], max(idx, key=lambda i: points[i]["value"])}
    marks = []
    for i, p in enumerate(points):
        cx = plot_l + band * i + band / 2
        xl = _txt(cx, plot_b + 16, p["x"], "ct ct-axis", "middle") if (i % every == 0 or i == n - 1) else None
        if p.get("value") is None:
            marks.append(h("g", None, xl))
            continue
        disp = p.get("display") or value_fmt(p["value"])
        y0 = y(p["value"])
        marks.append(h("g", {"class": "mark", "tabindex": "0", "data-tv": disp, "data-tl": p.get("tip") or str(p["x"])},
                       h("rect", {"class": "hit", "x": f"{cx - band / 2:.1f}", "y": plot_t, "width": f"{band:.1f}", "height": plot_b - plot_t}),
                       h("path", {"class": f"bar {p.get('mark', mark)}", "d": bar_path(cx - cw / 2, min(y0, plot_b - 1), cx + cw / 2, plot_b, "up")}),
                       _txt(cx, y0 - 6, disp, "ct ct-val", "middle") if i in labelled else None, xl))
    brk = []
    for b in breaks or []:
        bx = plot_l + band * (b["after"] + 1)
        brk.append(h("g", {"class": "mark break", "tabindex": "0", "data-tv": b.get("label", "Series break"),
                           "data-tl": b.get("tip", "The reporting basis changes here")},
                      h("rect", {"class": "hit", "x": f"{bx - 8:.1f}", "y": plot_t - 18, "width": 16, "height": plot_b - plot_t + 18}),
                      h("line", {"class": "break-line", "x1": f"{bx:.1f}", "x2": f"{bx:.1f}", "y1": plot_t - 14, "y2": plot_b}),
                      _txt(bx + 4, plot_t - 6, b.get("label", "Basis changes"), "ct ct-muted ct-small")))
    svg = _svg(W, H, f"{title}. Column chart; values in the table view.", grid, tl, marks, brk)
    hdr = headers or ["Year", "Value"]
    trows = [[p["x"], p.get("display") or (value_fmt(p["value"]) if p.get("value") is not None else "no data")] for p in points]
    return figure(fid, title, subtitle, svg, hdr, trows, note=note, numeric=(1,), status=status, page=page,
                  kind="columns", cite=cite)


# ------------------------------------------------------------------ line / time series

def line(fid: str, title: str, series: list[dict], subtitle: str | None = None,
         value_fmt=lambda v: f"{v:,.0f}", money: bool = False, note=None, status=None, page=None,
         x_fmt=str, cite=None) -> Markup:
    """series: [{name, mark (css class), points: [(x number, y number|None), ...]}].
    The x domain is the full range of all series. Hover shows every series at the X."""
    xs = sorted({p[0] for s in series for p in s["points"]})
    ys = [p[1] for s in series for p in s["points"] if p[1] is not None]
    vmax = max(ys) if ys else 1
    ticks = nice_ticks(vmax)
    top = ticks[-1]
    axis_w = max(text_w(fmt_tick(t, top, money), mono=True) for t in ticks) + 10
    end_w = max([text_w(value_fmt(s["points"][-1][1]), mono=True) for s in series if s["points"] and s["points"][-1][1] is not None] + [20]) + 14
    W, plot_t, plot_b = 640, 16, 220
    plot_l, plot_r = axis_w, W - end_w
    H = plot_b + 30
    x0, x1 = (xs[0], xs[-1]) if xs else (0, 1)
    span = (x1 - x0) or 1
    X = lambda v: plot_l + (plot_r - plot_l) * ((v - x0) / span)
    Y = lambda v: plot_b - (plot_b - plot_t) * (v / top)
    grid = [h("line", {"x1": plot_l, "x2": plot_r, "y1": f"{Y(t):.1f}", "y2": f"{Y(t):.1f}", "class": "grid" if t else "axis"}) for t in ticks]
    tl = [_txt(plot_l - 6, Y(t) + 4, fmt_tick(t, top, money), "ct ct-axis", "end") for t in ticks]
    n_lab = max(2, int((plot_r - plot_l) // 56))
    step = max(1, math.ceil(len(xs) / n_lab))
    xl_idx = [i for i in range(len(xs)) if i % step == 0 or i == len(xs) - 1]
    # the last year is always labeled; a stepped label just before it would print on top of it ("20242025")
    if len(xl_idx) > 1 and X(xs[xl_idx[-1]]) - X(xs[xl_idx[-2]]) < 36:
        del xl_idx[-2]
    xl = [_txt(X(xs[i]), plot_b + 16, x_fmt(xs[i]), "ct ct-axis", "middle") for i in xl_idx]
    paths, ends, end_labels = [], [], []
    for s in series:
        segs, cur = [], []
        for xv, yv in s["points"]:
            if yv is None:
                if cur:
                    segs.append(cur)
                cur = []
            else:
                cur.append((X(xv), Y(yv)))
        if cur:
            segs.append(cur)
        for seg in segs:
            d = "M" + "L".join(f"{a:.1f},{b:.1f}" for a, b in seg)
            paths.append(h("path", {"class": f"line {s.get('mark', 'm-accent')}", "d": d}))
        last = next(((xv, yv) for xv, yv in reversed(s["points"]) if yv is not None), None)
        if last:
            ends.append(h("circle", {"class": f"dot {s.get('mark', 'm-accent')}", "cx": f"{X(last[0]):.1f}", "cy": f"{Y(last[1]):.1f}", "r": 4}))
            end_labels.append([Y(last[1]) + 4, X(last[0]) + 8, value_fmt(last[1])])
    # end values that land close together are spread 12 px apart so they don't print over each other
    end_labels.sort()
    for k in range(1, len(end_labels)):
        end_labels[k][0] = max(end_labels[k][0], end_labels[k - 1][0] + 12)
    over = (end_labels[-1][0] - (H - 2)) if end_labels else 0
    for lab in end_labels:
        ends.append(_txt(lab[1], lab[0] - max(0, over), lab[2], "ct ct-val"))
    payload = {"x": [X(v) for v in xs], "labels": [x_fmt(v) for v in xs],
               "series": [{"name": s["name"], "mark": s.get("mark", "m-accent"),
                           "values": [next((value_fmt(p[1]) for p in s["points"] if p[0] == v and p[1] is not None), "no data") for v in xs]}
                          for s in series],
               "top": plot_t, "bottom": plot_b}
    overlay = h("rect", {"class": "crosshair-hit", "x": plot_l, "y": plot_t, "width": plot_r - plot_l, "height": plot_b - plot_t,
                         "tabindex": "0", "aria-label": "Move along the chart to read values"})
    cross = h("line", {"class": "crosshair", "x1": 0, "x2": 0, "y1": plot_t, "y2": plot_b, "visibility": "hidden"})
    svg = _svg(W, H, f"{title}. Line chart; values in the table view.", grid, tl, xl, paths, ends, cross, overlay,
               extra={"data-line": json.dumps(payload, separators=(",", ":"))})
    leg = legend([(s.get("mark", "m-accent"), s["name"]) for s in series], "line") if len(series) > 1 else None
    hdr = ["Year"] + [s["name"] for s in series]
    trows = [[x_fmt(v)] + [next((value_fmt(p[1]) for p in s["points"] if p[0] == v and p[1] is not None), "no data") for s in series] for v in xs]
    return figure(fid, title, subtitle, svg, hdr, trows, note=note, numeric=tuple(range(1, len(hdr))),
                  status=status, page=page, legend=leg, kind="line", cite=cite)


# ------------------------------------------------------------------ party control

PARTY_ORDER = ["D", "R", "L", "G", "I", "NP", "O", "W"]


def party_mark(code: str) -> str:
    return {"D": "m-party-D", "R": "m-party-R", "nodata": "m-nodata", "low": "m-low"}.get(code, "m-party-other")


def party_timeline(fid: str, title: str, years: list[dict], seats_total: int, subtitle: str | None = None,
                   note=None, page=None, cite=None) -> Markup:
    """Seats held by party in each year. years: [{year, seats: [code...], status, label?}],
    seat codes are party codes or 'nodata' / 'low'. One block per seat, grouped by party."""
    majority = seats_total // 2 + 1
    bw, gap, row_h, bh = 18, 2, 26, 16
    lab_w = 64
    blocks_w = seats_total * (bw + gap)
    sum_w = 210
    W = lab_w + blocks_w + sum_w
    pad_t = 22
    H = pad_t + row_h * len(years) + 8
    order = {c: i for i, c in enumerate(PARTY_ORDER)}
    rows = []
    mx = lab_w + majority * (bw + gap) - gap / 2
    rows.append(h("line", {"class": "majority-line", "x1": f"{mx:.1f}", "x2": f"{mx:.1f}", "y1": pad_t - 6, "y2": H - 6}))
    rows.append(_txt(mx, pad_t - 10, f"Majority: {majority} of {seats_total}", "ct ct-muted ct-small", "middle"))
    for i, yr in enumerate(years):
        y0 = pad_t + i * row_h + (row_h - bh) / 2
        seats = sorted(yr["seats"], key=lambda c: (c in ("low", "nodata"), c == "nodata", order.get(c, 50), c))
        counts: dict[str, int] = {}
        for c in seats:
            counts[c] = counts.get(c, 0) + 1
        parts = [f"{counts[c]} {c}" for c in sorted(counts, key=lambda c: order.get(c, 50)) if c not in ("low", "nodata")]
        if counts.get("low"):
            parts.append(f"{counts['low']} not shown")
        if counts.get("nodata"):
            parts.append(f"{counts['nodata']} no data")
        summary = " · ".join(parts)
        unoff = yr.get("status") == "unofficial"
        g = [h("rect", {"class": "hit", "x": 0, "y": f"{pad_t + i * row_h:.1f}", "width": W, "height": row_h}),
             _txt(lab_w - 10, y0 + bh - 3, f"{yr.get('label', yr['year'])}{'*' if unoff else ''}", "ct ct-mono", "end")]
        for j, c in enumerate(seats):
            x0 = lab_w + j * (bw + gap)
            g.append(h("rect", {"class": f"seat {party_mark(c)}", "x": f"{x0:.1f}", "y": f"{y0:.1f}", "width": bw, "height": bh, "rx": 2}))
        g.append(_txt(lab_w + blocks_w + 8, y0 + bh - 3, summary + (" (unofficial)" if unoff else ""), "ct"))
        tip = f"{yr.get('label', yr['year'])}: {summary}" + (" · based on unofficial results" if unoff else "")
        rows.append(h("g", {"class": "mark", "tabindex": "0", "data-tv": summary, "data-tl": tip}, g))
    svg = _svg(W, H, f"{title}. Seats by party for each year; values in the table view.", rows)
    present = []
    codes = {c for yr in years for c in yr["seats"]}
    for c in PARTY_ORDER:
        if c in codes:
            present.append((party_mark(c), party_label(c)))
    if "low" in codes:
        present.append(("m-low", "Holder recorded with low confidence (not shown)"))
    if "nodata" in codes:
        present.append(("m-nodata", "No holder in the guide's data"))
    hdr = ["Year"] + [party_label(c) for c in PARTY_ORDER if c in codes] + (["Low confidence"] if "low" in codes else []) + (["No data"] if "nodata" in codes else []) + ["Status"]
    trows = []
    for yr in years:
        row = [str(yr.get("label", yr["year"]))]
        for c in PARTY_ORDER:
            if c in codes:
                row.append(str(yr["seats"].count(c)))
        if "low" in codes:
            row.append(str(yr["seats"].count("low")))
        if "nodata" in codes:
            row.append(str(yr["seats"].count("nodata")))
        row.append(yr.get("status", ""))
        trows.append(row)
    return figure(fid, title, subtitle, svg, hdr, trows, note=note, numeric=tuple(range(1, len(hdr) - 1)),
                  page=page, legend=legend(present, "rect"), kind="party", cite=cite)


# ------------------------------------------------------------------ results bars

def results_bars(fid: str, title: str, candidates: list[dict], subtitle: str | None = None, status: str | None = None,
                 note=None, page=None, question: bool = False, cite=None) -> Markup:
    """One contest. candidates: [{name, party, votes, pct, winner}] in ballot order (never re-sorted).
    Scale is fixed 0-100% so contests compare honestly. Party marks carry text labels."""
    # narrow on purpose: the SVG scales down on phones, so a smaller width keeps text legible.
    # The label column fits the longest name or party line (mono, 10.5px) so nothing clips.
    def _sub(c):
        p = c.get("party") or ""
        base = "" if question else (party_label(p) if p else "No party listed")
        return base + (" · Elected" if c.get("winner") == "Y" and not question else "")
    val_w = 112
    lab_w = max([text_w(c["name"], 12) for c in candidates] + [text_w(_sub(c), 10.5, mono=True) for c in candidates] + [60]) + 14
    W = lab_w + 200 + val_w
    plot_w = W - lab_w - val_w
    row_h, bh, pad_t = 42, 14, 6
    H = pad_t + row_h * len(candidates) + 22
    X = lambda p: lab_w + plot_w * (p / 100.0)
    grid = [h("line", {"class": "grid" if t else "axis", "x1": f"{X(t):.1f}", "x2": f"{X(t):.1f}", "y1": pad_t, "y2": H - 18}) for t in (0, 25, 50, 75, 100)]
    tl = [_txt(X(t), H - 5, f"{t}%", "ct ct-axis", "middle") for t in (0, 50, 100)]
    marks = []
    for i, c in enumerate(candidates):
        y = pad_t + i * row_h
        pct = c.get("pct")
        party = c.get("party") or ""
        mark = "m-ink" if question else party_mark(party) if party else "m-party-other"
        name_line = _txt(lab_w - 10, y + 16, c["name"], "ct ct-strong", "end")
        sub = ("" if question else party_label(party) if party else "No party listed")
        if c.get("winner") == "Y":
            sub = (sub + " · " if sub else "") + ("Majority" if question else "Elected")
        sub_line = _txt(lab_w - 10, y + 31, sub, "ct ct-mono ct-small", "end")
        if pct is None:
            marks.append(h("g", None, name_line, sub_line, _txt(lab_w + 4, y + 24, "votes not recorded", "ct ct-muted")))
            continue
        votes = c.get("votes")
        disp = f"{pct:.1f}%" + (f" · {votes:,}" if votes is not None else "")
        x1 = max(X(pct), lab_w + 2)
        yb = y + (row_h - bh) / 2 - 2
        marks.append(h("g", {"class": "mark", "tabindex": "0", "data-tv": disp,
                             "data-tl": f"{c['name']}" + ("" if question else f" · {sub}")},
                       h("rect", {"class": "hit", "x": 0, "y": y, "width": W, "height": row_h}),
                       name_line, sub_line,
                       h("path", {"class": f"bar {mark}", "d": bar_path(lab_w, yb, x1, yb + bh, "right")}),
                       _txt(x1 + 6, yb + bh - 2, disp, "ct ct-val")))
    svg = _svg(W, H, f"{title}. Share of votes for each {'option' if question else 'candidate'}; values in the table view.", grid, tl, marks)
    hdr = ["Option" if question else "Candidate"] + ([] if question else ["Party"]) + ["Votes", "Share", "Result"]
    trows = []
    for c in candidates:
        row = [c["name"]]
        if not question:
            row.append(party_label(c.get("party")) if c.get("party") else "No party listed")
        row += [f"{c['votes']:,}" if c.get("votes") is not None else "not recorded",
                f"{c['pct']:.2f}%" if c.get("pct") is not None else "",
                ("Majority" if question else "Elected") if c.get("winner") == "Y" else ("" if c.get("winner") == "" else "")]
        trows.append(row)
    nums = (1, 2) if question else (2, 3)
    return figure(fid, title, subtitle, svg, hdr, trows, note=note, numeric=nums, status=status, page=page,
                  kind="results", cite=cite)


# ------------------------------------------------------------------ seat dots

DOT_KINDS = {
    "vote": "You vote for this seat",
    "other": "Elected by voters in other districts",
    "depends": "Elected; which of these you vote for depends on your address",
    "appointed": "Appointed, not elected",
    "unknown": "Seat count not yet in the guide's data",
}


def seat_dots(kinds: list[str], label: str, per_row: int = 12) -> Markup:
    """Small inline SVG of seat marks for one body (layer diagram on the landing page)."""
    d, r = 16, 6
    n = len(kinds)
    cols = min(n, per_row) or 1
    rows = math.ceil(n / per_row) or 1
    W, H = cols * d, rows * d
    marks = []
    for i, k in enumerate(kinds):
        cx = (i % per_row) * d + d / 2
        cy = (i // per_row) * d + d / 2
        if k == "appointed":
            marks.append(h("rect", {"class": "sd sd-appointed", "x": f"{cx - r + 0.5:.1f}", "y": f"{cy - r + 0.5:.1f}", "width": 2 * r - 1, "height": 2 * r - 1, "rx": 1.5}))
        elif k == "unknown":
            marks.append(h("circle", {"class": "sd sd-unknown", "cx": f"{cx:.1f}", "cy": f"{cy:.1f}", "r": r - 0.5}))
            marks.append(h("text", {"class": "sd-q", "x": f"{cx:.1f}", "y": f"{cy + 3.5:.1f}", "text-anchor": "middle"}, "?"))
        else:
            marks.append(h("circle", {"class": f"sd sd-{k}", "cx": f"{cx:.1f}", "cy": f"{cy:.1f}", "r": r - (0.75 if k != "vote" else 0)}))
    return h("svg", {"class": "seat-dots", "viewBox": f"0 0 {W} {H}", "width": W, "height": H,
                     "role": "img", "aria-label": label}, marks)


# ------------------------------------------------------------------ share bars (small multiples)
# Added 2026-11-09 (Wave A, batch 1; review pattern P7). One 100% bar per group (office level, year, unit), split
# into the shares of a few categories, with the counts printed as text under each bar. Never colored by party: the
# marks are the accent ramp (ordered categories) or the accent/ink alternation (unordered ones), from
# static/css/patterns.css. HTML, not SVG, so the rows and their count lines reflow at phone width.

SHARE_RAMPS = {
    # ordered categories (closest to safest margin, say): accent, then lighter steps of it
    "seq": ["m-share-0", "m-share-1", "m-share-2", "m-share-3"],
    # unordered categories: accent and ink alternating, as in the tax-bill split
    "alt": ["m-share-a0", "m-share-a1", "m-share-a2", "m-share-a3", "m-share-a4", "m-share-a5"],
}


def _pct(n: int, total: int) -> str:
    if not total:
        return ""
    p = 100.0 * n / total
    return "<1%" if 0 < p < 1 else f"{p:.0f}%"


def share_bars(fid: str, title: str, groups: list[dict], series: list[dict], subtitle: str | None = None,
               noun: str | tuple[str, str] = ("item", "items"), ramp: str = "seq", note=None, status=None, page=None,
               group_header: str = "Group", cite=None, show_zero: bool = True) -> Markup:
    """Small multiples of 100% stacked bars.

    groups: ``[{label, counts: {series key: int}, href?: drill-down link (shown on the label), tip?: str}]`` in the
    order given (office levels top-down, years in order; never sorted by a party's share).
    series: ``[{key, label, mark?}]`` in stack and legend order; ``mark`` overrides the ramp's class (``m-nodata``
    for "not in the data", ``m-ink``). At most 4 series on the "seq" ramp and 6 on "alt"; more raise ValueError
    (fold a tail into "Other" first).
    noun: (singular, plural) of what is counted ("race", "races"). Each row prints its total and every category's
    count and share as text, so the bar is drawn for the eye only (aria-hidden) and the segments are not tab stops;
    pointer hover still shows each segment's tooltip. The table view repeats every count."""
    marks = SHARE_RAMPS.get(ramp)
    if marks is None:
        raise ValueError(f"share_bars: unknown ramp {ramp!r}")
    if len(series) > len(marks):
        raise ValueError(f"share_bars: {len(series)} series; the {ramp} ramp has {len(marks)} steps")
    one, many = (noun, noun + "s") if isinstance(noun, str) else noun
    keys = [s["key"] for s in series]
    mark_of = {s["key"]: s.get("mark") or marks[i] for i, s in enumerate(series)}
    rows = []
    for gi, g in enumerate(groups):
        counts = {k: int(g.get("counts", {}).get(k) or 0) for k in keys}
        total = sum(counts.values())
        label = h("a", {"href": g["href"]}, g["label"]) if g.get("href") else g["label"]
        segs, texts = [], []
        for s in series:
            n = counts[s["key"]]
            share = _pct(n, total)
            if n:
                segs.append(h("span", {"class": f"shb-seg {mark_of[s['key']]}", "style": f"flex-grow: {n}",
                                       "data-tv": f"{n:,} of {total:,} ({share})",
                                       "data-tl": f"{g['label']} · {s['label']}"}))
            if n or show_zero:
                texts.append(h("li", {"class": "shb-c" + ("" if n else " shb-c-zero")},
                               h("span", {"class": f"key key-rect {mark_of[s['key']]}", "aria-hidden": "true"}),
                               h("span", {"class": "shb-cn mono"}, f"{n:,}"), " ", s["label"],
                               h("span", {"class": "shb-cp"}, f" ({share})") if n else None))
        tot_txt = f"{total:,} {one if total == 1 else many}"
        bar = (h("div", {"class": "shb-bar", "aria-hidden": "true"}, segs) if total else
               h("div", {"class": "shb-bar shb-bar-empty", "aria-hidden": "true"}))
        rows.append(h("li", {"class": "shb-row", "title": g.get("tip")},
                      h("p", {"class": "shb-label"}, h("span", {"class": "shb-name"}, label),
                        h("span", {"class": "shb-total mono"}, tot_txt)),
                      h("div", {"class": "shb-track"}, bar,
                        h("ul", {"class": "shb-counts", "aria-label": f"{g['label']}: {tot_txt}"}, texts) if total else
                        h("p", {"class": "shb-counts shb-none"}, f"No {many} in the guide's data."))))
    axis = h("div", {"class": "shb-axis", "aria-hidden": "true"},
             h("span", None, "0%"), h("span", None, "50%"), h("span", None, "100%"))
    body = h("div", {"class": "shb", "role": "group", "aria-label": f"{title}. Share of {many} in each group; "
                                                                   "counts are listed under each bar."},
             h("ol", {"class": "shb-rows"}, rows), axis)
    hdr = [group_header] + [s["label"] for s in series] + ["Total"]
    trows = []
    for g in groups:
        counts = {k: int(g.get("counts", {}).get(k) or 0) for k in keys}
        total = sum(counts.values())
        trows.append([g["label"]] + [f"{counts[k]:,} ({_pct(counts[k], total)})" if total else "0" for k in keys]
                     + [f"{total:,}"])
    leg = legend([(mark_of[s["key"]], s["label"]) for s in series]) if len(series) >= 2 else None
    return figure(fid, title, subtitle, body, hdr, trows, note=note, numeric=tuple(range(1, len(hdr))), status=status,
                  page=page, legend=leg, kind="share", scroll=False, cite=cite)


# ------------------------------------------------------------------ money report by report (added 2026-11-09)

def _signed_ticks(lo: float, hi: float, n: int = 4) -> list[float]:
    """Ticks covering lo..hi (lo may be below 0) with one step size, always including 0."""
    span = max(hi, 0) - min(lo, 0)
    if span <= 0:
        return [0, 1]
    step = nice_ticks(span, n)[1]
    start = math.floor(min(lo, 0) / step) * step
    stop = math.ceil(max(hi, 0) / step) * step
    out, v = [], start
    while v <= stop + step * 1e-9:
        out.append(round(v, 10))
        v += step
    return out


def period_money(fid: str, title: str, points: list[dict], subtitle: str | None = None, note=None, status=None,
                 page=None, headers: list | None = None, rows: list[list] | None = None, numeric: tuple = (),
                 cite=None, words: dict | None = None) -> Markup:
    """One committee's money, report by report, in date order: two columns per report (raised, filled accent; spent,
    an ink outline, so the pair differs by shape for color-blind readers; both in the report's own period, as written) and cash on hand at the close of each report as a dashed line with ring
    markers. All three are dollars, so they share one axis. Cash on hand can be below zero (the axis then extends).

    points: ``[{x: first label line, x2: second label line, raised, spent, cash (cents or None each), tip}]``.
    A None value draws nothing for that mark and says "not on the form" in the tooltip.
    headers/rows: the table view (defaults to one row per point). Each report is one focusable mark whose tooltip
    lists all three figures. ``words`` overrides the labels: raised, spent, cash (legend and tooltip) and missing (a
    None value); the cash line and its legend entry are left out when no point has cash."""
    w = {"raised": "Raised in the period", "spent": "Spent in the period", "cash": "Cash on hand at close",
         "missing": "not on the form", "tip_raised": "Raised", "tip_spent": "Spent", "tip_cash": "Cash at close"}
    w.update(words or {})
    has_cash = any(p.get("cash") is not None for p in points)
    def d(c):
        return None if c is None else c / 100.0
    vals = [d(p.get(k)) for p in points for k in ("raised", "spent", "cash")]
    vals = [v for v in vals if v is not None]
    ticks = _signed_ticks(min(vals, default=0), max(vals, default=1))
    lo, top = ticks[0], ticks[-1]
    axis_w = max(text_w(fmt_tick(abs(t), max(abs(lo), top), True), mono=True) + (6 if t < 0 else 0) for t in ticks) + 10
    n = max(len(points), 1)
    band_w = 84
    last_cash = next((p.get("cash") for p in reversed(points) if p.get("cash") is not None), None)
    lab_w = text_w(("-$" if (last_cash or 0) < 0 else "$") + f"{abs(last_cash or 0) / 100:,.2f}", mono=True)
    right = max(12, lab_w + 18 + 10 - band_w / 2) if last_cash is not None else 12   # label sits past the columns
    W = max(320, axis_w + n * band_w + right)
    plot_l, plot_r, plot_t, plot_b = axis_w, W - right, 18, 196
    H = plot_b + 36
    band = (plot_r - plot_l) / n
    bw = min(18, (band - 18) / 2)
    Y = lambda v: plot_b - (plot_b - plot_t) * ((v - lo) / ((top - lo) or 1))
    zero = Y(0)

    def tick_text(t):
        s = fmt_tick(abs(t), max(abs(lo), top), True)
        return ("-" + s) if t < 0 else s
    grid = [h("line", {"x1": plot_l, "x2": plot_r, "y1": f"{Y(t):.1f}", "y2": f"{Y(t):.1f}",
                       "class": "axis" if t == 0 else "grid"}) for t in ticks]
    tl = [_txt(plot_l - 6, Y(t) + 4, tick_text(t), "ct ct-axis", "end") for t in ticks]

    def money(c):
        if c is None:
            return w["missing"]
        v = c / 100.0
        return ("-$" if v < 0 else "$") + f"{abs(v):,.2f}"

    def bar(x0, x1, c, mark):
        if c is None or c == 0:
            return None
        y = Y(d(c))
        if c > 0:
            return h("path", {"class": f"bar {mark}", "d": bar_path(x0, min(y, zero - 1), x1, zero, "up")})
        # spending can't be negative on the form; a negative figure (a refund written as minus) hangs below the axis
        return h("rect", {"class": f"bar {mark}", "x": f"{x0:.1f}", "y": f"{zero:.1f}", "width": f"{x1 - x0:.1f}",
                          "height": f"{max(y - zero, 1):.1f}"})
    marks, cash_pts = [], []
    for i, p in enumerate(points):
        cx = plot_l + band * i + band / 2
        tv = f"{w['tip_raised']} {money(p.get('raised'))} · {w['tip_spent']} {money(p.get('spent'))}" + (
            f" · {w['tip_cash']} {money(p.get('cash'))}" if has_cash else "")
        marks.append(h("g", {"class": "mark", "tabindex": "0", "data-tv": tv, "data-tl": p.get("tip") or p["x"]},
                       h("rect", {"class": "hit", "x": f"{cx - band / 2:.1f}", "y": plot_t,
                                  "width": f"{band:.1f}", "height": plot_b - plot_t}),
                       bar(cx - bw - 1, cx - 1, p.get("raised"), "m-accent"),
                       bar(cx + 1, cx + bw + 1, p.get("spent"), "m-spent"),
                       _txt(cx, plot_b + 15, p["x"], "ct ct-axis", "middle"),
                       _txt(cx, plot_b + 28, p.get("x2", ""), "ct ct-axis", "middle") if p.get("x2") else None))
        if p.get("cash") is not None:
            cash_pts.append((cx, Y(d(p["cash"])), p["cash"]))
        else:
            cash_pts.append(None)
    lines, segs, cur = [], [], []
    for c in cash_pts:
        if c is None:
            if cur:
                segs.append(cur)
            cur = []
        else:
            cur.append(c)
    if cur:
        segs.append(cur)
    for seg in segs:
        if len(seg) > 1:
            lines.append(h("path", {"class": "line m-cash", "d": "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y, _ in seg)}))
    for c in cash_pts:
        if c:
            lines.append(h("circle", {"class": "dot-ring m-cash", "cx": f"{c[0]:.1f}", "cy": f"{c[1]:.1f}", "r": 4}))
    last = next((c for c in reversed(cash_pts) if c), None)
    if last:
        lab = money(last[2])
        lines.append(_txt(last[0] + bw + 6, last[1] + 4, lab, "ct ct-val"))
    svg = _svg(W, H, f"{title}. Columns for {w['raised'].lower()} and {w['spent'].lower()}"
                     + (f", and a line for {w['cash'].lower()}" if has_cash else "") + "; the figures are in the table "
                     "view.", grid, tl, marks, lines)
    leg = h("ul", {"class": "legend"},
            h("li", None, h("span", {"class": "key key-rect m-accent", "aria-hidden": "true"}), w["raised"]),
            h("li", None, h("span", {"class": "key key-rect m-spent", "aria-hidden": "true"}), w["spent"]),
            h("li", None, h("span", {"class": "key key-line m-cash", "aria-hidden": "true"}), w["cash"]) if has_cash else None)
    hdr = headers or (["Report", w["raised"], w["spent"]] + ([w["cash"]] if has_cash else []))
    trows = rows if rows is not None else [[f"{p['x']} {p.get('x2', '')}".strip(), money(p.get("raised")),
                                            money(p.get("spent"))] + ([money(p.get("cash"))] if has_cash else [])
                                           for p in points]
    return figure(fid, title, subtitle, svg, hdr, trows, note=note, numeric=numeric or tuple(range(1, len(hdr))),
                  status=status, page=page, legend=leg, kind="period-money", cite=cite)
