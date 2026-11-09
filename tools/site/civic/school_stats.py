"""School corporation enrollment and spending per student (indicator_values.csv, hand-added rows; see data/SCHEMA.md).

    enrollment(ed, uid)          -> [(label "2025-26", count, row)] oldest first ([] when none)
    per_student(ed, uid)         -> (row, state median row) for the latest calendar year, or (None, None)
    PER_STUDENT_CAPTION          -> the caption every display of spending per student carries

The corporation is the indicator's school_district geography, matched by the unit's map shape Census name (the same
match as the map's population, civic/map.py), else by the unit's name. Never divide a budget by enrollment: the
enrollment count includes pre-K and adult students and differs from the average daily membership (ADM) the state uses.
"""
from __future__ import annotations

import math
import re

from .map import _shape_names

ENROLL = "school_enrollment_total"
PER_STUDENT = "school_spending_per_student"
MEDIAN = "school_spending_per_student_median"
PER_STUDENT_CAPTION = ("total spending divided by average daily membership; not classroom spending; calendar year, "
                       "not school year")


def _f(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _rows(ed) -> dict:
    """{geo_id: {indicator_id: [rows]}} for the school indicators, plus "_state" for the state medians (cached)."""
    idx = ed.__dict__.get("_school_stats_idx")
    if idx is None:
        idx = {}
        for r in ed.table("indicator_values"):
            if r["indicator_id"] in (ENROLL, PER_STUDENT, MEDIAN):
                key = "_state" if r["indicator_id"] == MEDIAN else r["geo_id"]
                idx.setdefault(key, {}).setdefault(r["indicator_id"], []).append(r)
        ed.__dict__["_school_stats_idx"] = idx
    return idx


def school_geo(ed, uid: str) -> str | None:
    """geo_id of the corporation's school_district rows."""
    unit = ed.units.get(uid)
    if not unit:
        return None
    shape = _shape_names(ed).get(uid)
    names = [shape[1].strip().lower()] if shape else []
    names.append(unit["name"].strip().lower())
    for want in names:
        for r in ed.table("indicator_values"):
            if r["geo_type"] == "school_district" and r["geo_name"].split(",")[0].strip().lower() == want:
                return r["geo_id"]
    return None


def _year_of(vintage: str) -> str:
    m = re.search(r"(\d{4}-\d{2})\s*$", vintage) or re.search(r"(\d{4})\s*$", vintage)
    return m.group(1) if m else vintage


def enrollment(ed, uid: str) -> list[tuple[str, int, dict]]:
    g = school_geo(ed, uid)
    out = []
    for r in _rows(ed).get(g, {}).get(ENROLL, []):
        v = _f(r["value"])
        if v is not None:
            out.append((_year_of(r["vintage"]), int(v), r))
    return sorted(out, key=lambda t: t[0])


def per_student(ed, uid: str):
    """(the corporation's latest spending-per-student row, the state median row for the same vintage)."""
    g = school_geo(ed, uid)
    rows = [r for r in _rows(ed).get(g, {}).get(PER_STUDENT, []) if _f(r["value"]) is not None]
    if not rows:
        return None, None
    row = max(rows, key=lambda r: _year_of(r["vintage"]))
    med = next((m for m in _rows(ed).get("_state", {}).get(MEDIAN, []) if m["vintage"] == row["vintage"]), None)
    return row, med


def calendar_year(row: dict) -> str:
    return _year_of(row["vintage"])


def enrollment_text(series) -> str:
    """'12,851 in school year 2025-26, down 36% from 20,156 in 2011-12' ('' when none)."""
    if not series:
        return ""
    y1, v1, _ = series[-1]
    s = f"{v1:,} in school year {y1}"
    if len(series) > 1:
        y0, v0, _ = series[0]
        if v0:
            pct = (v1 / v0 - 1) * 100
            word = "up" if pct > 0 else "down"
            s += f", {word} {abs(pct):.0f}% from {v0:,} in {y0}" if round(pct) else f", about the same as in {y0} ({v0:,})"
    return s


def per_student_text(row, med) -> str:
    if not row:
        return ""
    s = f"${_f(row['value']):,.0f} in calendar year {calendar_year(row)}"
    if med:
        s += f" (state median ${_f(med['value']):,.0f})"
    return s


def panel_facts(ed, uid: str) -> list[list[str]]:
    """Map panel facts (plain text): latest enrollment and spending per student with the state median."""
    out = []
    series = enrollment(ed, uid)
    if series:
        y, v, _ = series[-1]
        out.append([f"Enrollment, school year {y}", f"{v:,} (whole corporation, pre-K through adult)"])
    row, med = per_student(ed, uid)
    if row:
        val = f"${_f(row['value']):,.0f}" + (f" (state median ${_f(med['value']):,.0f})" if med else "")
        out.append([f"Spending per student, calendar year {calendar_year(row)}", f"{val}; {PER_STUDENT_CAPTION}"])
    return out
