"""Tax base: certified net assessed value by unit (assessed_values.csv, tools/build_assessed_values.py).

Only basis == "dlgf_certified" rows (the "Certified AV" in the county's DLGF budget orders, 2020-2026) are shown as
the tax base. The gateway_budget_estimate rows are the units' own estimates entered with their budgets: they are
never charted with the certified values.

    money_id(ed, unit_id)              -> the file's id for a units.csv id
    certified(ed, mid)                 -> {year: row} (dlgf_certified only)
    latest_certified(ed, mid)          -> row or None (the latest year)
    part_only(row)                     -> True when the row covers only the county's part of a cross-county unit
    tax_base_line(ed, page, mid, ...)  -> Markup "Tax base: $X certified net assessed value for 2026 ..." or None
    av_per_resident(av, residents)     -> float or None
"""
from __future__ import annotations

import math
import re

from .components import status_badge
from .html import Markup, h

CERTIFIED = "dlgf_certified"
PART_RE = re.compile(r"County part only", re.I)


def _f(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _index(ed) -> dict:
    idx = ed.__dict__.get("_tax_base_idx")
    if idx is None:
        idx = {}
        for r in ed.table("assessed_values"):
            if r.get("basis") == CERTIFIED and _f(r.get("net_assessed_value")) is not None:
                idx.setdefault(r["unit_id"], {})[r["year"]] = r
        ed.__dict__["_tax_base_idx"] = idx
    return idx


def certified(ed, mid: str | None) -> dict:
    """{year: row} of certified net assessed value for a money-file id ({} when none)."""
    return dict(_index(ed).get(mid, {})) if mid else {}


def money_id(ed, unit_id: str) -> str | None:
    """The assessed_values.csv id for a units.csv id ('south-bend' -> 'city-south-bend'), or None."""
    for mid in _index(ed):
        if ed.unit_alias(mid) == unit_id:
            return mid
    return None


def latest_certified(ed, mid: str | None) -> dict | None:
    rows = certified(ed, mid)
    return rows[max(rows)] if rows else None


def part_only(row: dict | None) -> bool:
    """True when the certified value covers only the county's part of a unit that crosses the county line."""
    return bool(row and PART_RE.search(row.get("notes") or ""))


def av_value(row: dict | None) -> float | None:
    return _f(row.get("net_assessed_value")) if row else None


def av_per_resident(av, residents) -> float | None:
    a, p = _f(av), _f(residents)
    if a is None or p is None or p <= 0:
        return None
    return a / p


def usd(v) -> str:
    return f"${float(v):,.0f}"


def usd_short(v) -> str:
    v = float(v)
    if abs(v) >= 1e9:
        return f"${v / 1e9:.2f} billion"
    if abs(v) >= 1e6:
        return f"${v / 1e6:.1f} million"
    return f"${v:,.0f}"


def tax_base_line(ed, page, mid: str | None, county_label: str | None = None, extra: str = "") -> Markup | None:
    """One paragraph for a unit page: the latest certified net assessed value, the fund it is read from, the
    county-part caveat for cross-county units, the status badge and the source."""
    row = latest_certified(ed, mid)
    if row is None:
        return None
    rows = certified(ed, mid)
    first = min(rows)
    trend = ""
    if first != row["year"]:
        a, b = av_value(rows[first]), av_value(row)
        if a:
            trend = f" ({usd_short(a)} in {first}, {((b / a) - 1) * 100:+.0f}%)"
    part = (f" This is the {county_label or 'county'} part only: the unit also lies in another county."
            if part_only(row) else "")
    return h("p", {"class": "tax-base-line"},
             h("strong", None, "Tax base: "),
             f"{usd(av_value(row))} certified net assessed value for {row['year']}{trend}, from the state's certified "
             f"budget order (fund {row['fund']}). Property taxes are levied on this value.{part}{extra} ",
             status_badge(row["status"], page),
             page.cites.cite(";".join(dict.fromkeys(row["source_ids"].split(";") + rows[first]["source_ids"].split(";")))))


def panel_facts(ed, mid: str | None, residents=None, residents_label: str = "2020 Census count") -> list[list[str]]:
    """Map panel facts (plain text): the latest certified net assessed value and, when the value covers the whole
    unit and a resident count is given, the value per resident. [] when the unit has no certified value."""
    row = latest_certified(ed, mid)
    if row is None:
        return []
    v = av_value(row)
    part = part_only(row)
    val = f"{usd(v)} for {row['year']} (state budget order, fund {row['fund']})"
    if part:
        val += "; St. Joseph County part only, the unit also lies in another county"
    out = [["Tax base (certified net assessed value)", val]]
    per = None if part else av_per_resident(v, residents)
    if per is not None:
        out.append(["Tax base per resident", f"{usd(per)} (divided by {int(float(residents)):,} residents, {residents_label})"])
    return out
