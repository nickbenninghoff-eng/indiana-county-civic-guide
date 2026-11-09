"""Sequential shading for the boundary map (one neutral teal ramp, static/css/money_map.css cmap-mm-1..5): rounded
natural breaks per layer, the shade of each class, legend labels, and the legend markup. Used by the budgets page's
money map (civic/money_map.py) and the community pages' indicator maps (pages/community_history.py).

    breaks = class_breaks(values)            # rounded natural breaks; [] for 0 or 1 distinct values
    step_of(v, breaks) -> class index        # a value equal to a break is in the higher class
    ramp_positions(k) -> shades 1..RAMP      # spread out when there are fewer than RAMP classes
    shade_legend(...) -> Markup              # one legend block (title, steps with counts, no data, extras)
"""
from __future__ import annotations

import math

from .html import h

RAMP = 5            # shades in static/css/money_map.css (cmap-mm-1 .. cmap-mm-5)
MAX_CLASSES = 5


def _jenks(vals: list[float], k: int) -> list[int]:
    """Fisher's exact optimal grouping of sorted values into k classes (least within-class squared deviation).
    Returns the start index of every class after the first."""
    n = len(vals)
    pre, pre2 = [0.0], [0.0]
    for v in vals:
        pre.append(pre[-1] + v)
        pre2.append(pre2[-1] + v * v)

    def sse(i, j):   # vals[i:j]
        s, s2, m = pre[j] - pre[i], pre2[j] - pre2[i], j - i
        return s2 - s * s / m

    inf = float("inf")
    cost = [[inf] * (n + 1) for _ in range(k + 1)]
    back = [[0] * (n + 1) for _ in range(k + 1)]
    cost[0][0] = 0.0
    for c in range(1, k + 1):
        for j in range(c, n + 1):
            for i in range(c - 1, j):
                if cost[c - 1][i] == inf:
                    continue
                v = cost[c - 1][i] + sse(i, j)
                if v < cost[c][j] - 1e-9:
                    cost[c][j], back[c][j] = v, i
    starts, j = [], n
    for c in range(k, 0, -1):
        i = back[c][j]
        if c > 1:
            starts.append(i)
        j = i
    return sorted(starts)


def round_between(lo: float, hi: float, min_unit: float = 1) -> float | None:
    """The roundest figure b with lo < b <= hi (nearest the middle of the gap among equally round ones), never finer
    than min_unit: with the default (whole units) a break reads as $50, $1,000 or $2,750, never $46.70; percentages
    and ages pass min_unit=0.1. None when no such figure fits in the gap."""
    if not (hi > lo) or hi < min_unit:
        return None
    lo_exp = int(round(math.log10(min_unit)))
    e = int(math.floor(math.log10(hi)))
    units = []
    for p in range(e, lo_exp - 1, -1):
        for m in (10, 5, 2.5, 2):
            u = round(m * 10 ** (p - 1), 10)
            ok = u >= min_unit - 1e-12 and abs(u / min_unit - round(u / min_unit)) < 1e-9
            if ok and u not in units:
                units.append(u)
    if min_unit not in units:
        units.append(min_unit)
    mid = (lo + hi) / 2
    for u in units:
        first = (math.floor(lo / u + 1e-9) + 1) * u
        if first > hi + 1e-9:
            continue
        cands = []
        i = 0
        while first + i * u <= hi + 1e-9:
            cands.append(round(first + i * u, 10))
            i += 1
        return float(min(cands, key=lambda c: (abs(c - mid), c)))
    return None


def class_breaks(values, max_classes: int = MAX_CLASSES, min_unit: float = 1) -> list[float]:
    """Rounded break points for one layer's values: natural breaks (Jenks) into up to max_classes classes, each break
    moved to the roundest figure in the gap between the classes. A value equal to a break is in the higher class.
    5 or more distinct values: one class fewer than the distinct count, at most max_classes; fewer: one class each.
    Missing values (None) are ignored. Returns [] for 0 or 1 distinct values (one class)."""
    vals = sorted(float(v) for v in values if v is not None and math.isfinite(float(v)))
    distinct = sorted(set(vals))
    nd = len(distinct)
    if nd <= 1:
        return []
    k = min(max_classes, nd - 1) if nd >= 5 else nd
    starts = _jenks(vals, k)
    out = []
    for s in starts:
        b = round_between(vals[s - 1], vals[s], min_unit)
        if b is not None and (not out or b > out[-1]):
            out.append(b)
    return out


def step_of(value: float | None, breaks: list[float]) -> int | None:
    """Class index 0..len(breaks) of a value (None for a missing value)."""
    if value is None:
        return None
    return sum(1 for b in breaks if value >= b)


def ramp_positions(k: int) -> list[int]:
    """Which of the RAMP shades (1..RAMP) each of k classes uses, spread to keep neighbors far apart."""
    if k <= 1:
        return [3]
    return [1 + round(i * (RAMP - 1) / (k - 1)) for i in range(k)]


def money_text(v: float) -> str:
    return f"${v:,.0f}"


def legend_labels(breaks: list[float], fmt=money_text) -> list[str]:
    """'Under X', 'X to Y', ..., 'Z or more' with fmt for each figure (default whole dollars)."""
    if not breaks:
        return ["Every area with a figure"]
    out = [f"Under {fmt(breaks[0])}"]
    for a, b in zip(breaks, breaks[1:]):
        out.append(f"{fmt(a)} to {fmt(b)}")
    out.append(f"{fmt(breaks[-1])} or more")
    return out


def shade_class(shade: int | None) -> str:
    """CSS class of a shade (1..RAMP), or the hatched no-data class."""
    return f"cmap-mm-{shade}" if shade else "cmap-mm-none"


def classify(values: dict, max_classes: int = MAX_CLASSES, min_unit: float = 1) -> dict:
    """{key: value or None} -> breaks, class count, shades per class, shade per key (None = no figure), counts."""
    breaks = class_breaks(list(values.values()), max_classes, min_unit)
    k = len(breaks) + 1
    pos = ramp_positions(k)
    steps = {key: step_of(v, breaks) for key, v in values.items()}
    return {"breaks": breaks, "classes": k, "shades": pos,
            "shade": {key: (pos[s] if s is not None else None) for key, s in steps.items()},
            "counts": [sum(1 for s in steps.values() if s == i) for i in range(k)],
            "none": sum(1 for s in steps.values() if s is None)}


def shade_legend(title: str, cls: dict, fmt=money_text, none_label: str = "No data", extra=(), attrs=None):
    """One legend block: a title, then each step with its area count, the no-data hatch when any area has no
    figure, and extra (key class, text) rows. attrs go on the wrapper (data-layer, data-ind, class additions)."""
    def n_txt(n):
        return h("span", {"class": "cmap-lg-n"}, f" ({n} area{'s' if n != 1 else ''})")
    items = [h("li", None, h("span", {"class": f"cmap-key {shade_class(pos)}", "aria-hidden": "true"}),
               h("span", {"class": "cmap-lg-t"}, txt, n_txt(cnt)))
             for pos, txt, cnt in zip(cls["shades"], legend_labels(cls["breaks"], fmt), cls["counts"])]
    if cls["none"]:
        items.append(h("li", None, h("span", {"class": "cmap-key cmap-mm-none", "aria-hidden": "true"}),
                       h("span", {"class": "cmap-lg-t"}, none_label, n_txt(cls["none"]))))
    for key_cls, txt in extra:
        items.append(h("li", None, h("span", {"class": f"cmap-key {key_cls}", "aria-hidden": "true"}),
                       h("span", {"class": "cmap-lg-t"}, txt)))
    a = {"class": "cmap-mlegend"}
    a.update(attrs or {})
    return h("div", a, h("p", {"class": "cmap-mlegend-h"}, title),
             h("ul", {"class": "cmap-legend is-on", "aria-label": f"Legend: {title}"}, items))
