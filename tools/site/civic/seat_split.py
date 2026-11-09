"""Seat-share chart for a legislative chamber: one horizontal stacked bar per period.

Added for pages/state.py (new function only; nothing existing is changed). Party colors are used
with text labels in the legend, the row summary and the table view. The scale is fixed
(0 to the chamber size) so every period compares honestly, and a line marks the two-thirds
threshold. A period with no published counts is drawn as text ("pending"), not as a bar.
"""
from __future__ import annotations

from .charts import _svg, _txt, figure, legend, party_mark
from .components import party_label
from .html import Markup, h


def seat_split(fid: str, title: str, rows: list[dict], total: int, two_thirds: int,
               subtitle: str | None = None, note=None, page=None, cite: Markup | None = None,
               pending_text: str = "pending certified results") -> Markup:
    """rows: [{label, d, r, other, status, super_party, tip?}] with d/r/other ints or None when
    not published. Rows are drawn in the order given."""
    lab_w, bar_w, sum_w = 74, 300, 150
    W = lab_w + bar_w + sum_w
    row_h, bh, pad_t = 30, 16, 26
    H = pad_t + row_h * len(rows) + 6
    X = lambda n: lab_w + bar_w * (n / total)
    parts = [h("line", {"class": "majority-line", "x1": f"{X(two_thirds):.1f}", "x2": f"{X(two_thirds):.1f}",
                        "y1": pad_t - 6, "y2": H - 4}),
             _txt(X(two_thirds), pad_t - 12, f"Two-thirds: {two_thirds} of {total}", "ct ct-muted ct-small", "middle")]
    trows = []
    for i, r in enumerate(rows):
        y0 = pad_t + i * row_h + (row_h - bh) / 2
        unoff = r.get("status") == "unofficial"
        label = r["label"] + ("*" if unoff else "")
        pending = r.get("d") is None
        g = [h("rect", {"class": "hit", "x": 0, "y": f"{pad_t + i * row_h:.1f}", "width": W, "height": row_h}),
             _txt(lab_w - 8, y0 + bh - 3, label, "ct ct-mono", "end")]
        if pending:
            g.append(_txt(lab_w + 4, y0 + bh - 3, pending_text, "ct ct-muted"))
            summary = pending_text
            trows.append([r["label"], "pending", "pending", "pending", "not published", r.get("status", "")])
        else:
            x = lab_w
            segs = [("D", r["d"]), ("R", r["r"]), ("O", r.get("other") or 0)]
            for code, n in segs:
                if not n:
                    continue
                w = bar_w * n / total
                g.append(h("rect", {"class": f"seat {party_mark(code)}", "x": f"{x:.1f}", "y": f"{y0:.1f}",
                                    "width": f"{max(w - 1.5, 1):.1f}", "height": bh, "rx": 1}))
                x += w
            summary = f"{r['d']} D · {r['r']} R" + (f" · {r['other']} other" if r.get("other") else "")
            g.append(_txt(lab_w + bar_w + 8, y0 + bh - 3, summary, "ct"))
            sp = r.get("super_party") or "none"
            trows.append([r["label"], str(r["d"]), str(r["r"]), str(r.get("other") or 0),
                          party_label(sp) if sp not in ("none", "") else "no party", r.get("status", "")])
        parts.append(h("g", {"class": "mark", "tabindex": "0", "data-tv": summary,
                             "data-tl": r.get("tip") or r["label"]}, g))
    svg = _svg(W, H, f"{title}. Seats by party for each period; values in the table view.", parts)
    leg = legend([(party_mark("D"), party_label("D")), (party_mark("R"), party_label("R")),
                  (party_mark("O"), "Other / independent")], "rect")
    hdr = ["Period", "D seats", "R seats", "Other seats", "Holds two-thirds", "Status"]
    return figure(fid, title, subtitle, svg, hdr, trows, note=note, numeric=(1, 2, 3), page=page,
                  legend=leg, kind="party", cite=cite)
