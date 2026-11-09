"""Data loader for one county edition plus the shared Indiana-wide data.

    ed = Edition.load(repo_root, "st-joseph")
    ed.units["county"]                      -> row dict
    ed.offices_for("county")                -> office rows of a unit, in file order
    ed.current_terms("county-auditor")      -> terms in office on ed.as_of
    ed.incoming_terms("county-auditor")     -> terms that start after ed.as_of
    ed.source("GOV-001")                    -> sources_*.csv row (all areas merged)
    ed.results_for_office("county-auditor") -> {election_id: [result rows]}
    ed.table("budgets")                     -> any CSV in the edition or Indiana folder

Every row is a plain dict of strings exactly as in the CSV. Helpers never rewrite data;
anything derived (dates, contest -> office links) is computed on the side.
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable

# --------------------------------------------------------------------------- vocab

PARTY_LABELS = {
    "D": "Democrat",
    "R": "Republican",
    "L": "Libertarian",
    "G": "Green",
    "I": "Independent / no party",
    "NP": "Nonpartisan ballot",
    "W": "Write-in",
    "O": "Other party",
}

SELECTED_BY_LABELS = {
    "election": "election",
    "caucus": "party caucus",
    "appointment": "appointment",
    "unknown": "not stated in sources",
    "": "not stated in sources",
}

# offices.csv uses finer office_type keys than office_types.csv. This maps them to the
# Indiana-wide row that explains them. Keys missing here AND in office_types.csv have no
# generic explanation yet (reported by build warnings).
OFFICE_TYPE_ALIASES = {
    "city_council_district": "city_council_member",
    "city_council_at_large": "city_council_member",
    "town_council_ward": "town_council_member",
    "town_council_at_large": "town_council_member",
    "school_board_district": "school_board_member",
    "school_board_at_large": "school_board_member",
    "school_board_appointed": "school_board_member",
    "state_house": "state_representative",
    "state_senate": "state_senator",
    "superior_court_judge": "superior_court_judge_merit",
}


def load_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def split_ids(value: str | None) -> list[str]:
    return [s.strip() for s in (value or "").split(";") if s.strip()]


_DATE_RE = re.compile(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$")


def parse_date(value: str | None, end: bool = False) -> date | None:
    """Parse YYYY, YYYY-MM or YYYY-MM-DD. ``end=True`` returns the last day of a
    partial period (so '2022-08' as an end date means through Aug 31)."""
    if not value:
        return None
    m = _DATE_RE.match(value.strip())
    if not m:
        return None
    y = int(m.group(1))
    mo = int(m.group(2)) if m.group(2) else None
    d = int(m.group(3)) if m.group(3) else None
    if d:
        return date(y, mo, d)
    if mo:
        if not end:
            return date(y, mo, 1)
        nxt = date(y + (mo == 12), mo % 12 + 1, 1)
        return date.fromordinal(nxt.toordinal() - 1)
    return date(y, 12, 31) if end else date(y, 1, 1)


def date_precision(value: str | None) -> str:
    if not value:
        return ""
    n = value.count("-")
    return {0: "year", 1: "month", 2: "day"}.get(n, "")


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_FULL = ["January", "February", "March", "April", "May", "June", "July", "August",
               "September", "October", "November", "December"]


def fmt_date(value: str | date | None, long: bool = False) -> str:
    """'2027-01-01' -> 'Jan 1, 2027'; '2022-08' -> 'Aug 2022'; '2009' -> '2009'."""
    if value is None or value == "":
        return ""
    names = MONTHS_FULL if long else MONTHS
    if isinstance(value, date):
        return f"{names[value.month - 1]} {value.day}, {value.year}"
    p = date_precision(value)
    d = parse_date(value)
    if d is None:
        return str(value)
    if p == "day":
        return f"{names[d.month - 1]} {d.day}, {d.year}"
    if p == "month":
        return f"{names[d.month - 1]} {d.year}"
    return str(d.year)


def nth_weekday_after(year: int, month: int) -> date:
    """First Tuesday after the first Monday of a month (Indiana primary/general rule)."""
    d = date(year, month, 1)
    while d.weekday() != 0:  # first Monday
        d = date.fromordinal(d.toordinal() + 1)
    return date.fromordinal(d.toordinal() + 1)


def fmt_int(value) -> str:
    try:
        return f"{int(float(value)):,}"
    except (TypeError, ValueError):
        return ""


def fmt_pct(value, places: int = 1) -> str:
    try:
        return f"{float(value):.{places}f}%"
    except (TypeError, ValueError):
        return ""


# --------------------------------------------------------------------------- edition

@dataclass
class Edition:
    root: Path
    edition_id: str
    config: dict
    tables: dict[str, list[dict]]
    counties_svg: dict
    warnings: list[str] = field(default_factory=list)

    # ---- construction -----------------------------------------------------------
    @classmethod
    def load(cls, root: Path, edition_id: str) -> "Edition":
        root = Path(root)
        ed_dir = root / "data" / "editions" / edition_id
        in_dir = root / "data" / "indiana"
        if not ed_dir.is_dir():
            raise SystemExit(f"No edition folder: {ed_dir}")
        config = json.loads((ed_dir / "edition.json").read_text(encoding="utf-8"))
        tables: dict[str, list[dict]] = {}
        for folder in (in_dir, ed_dir, ed_dir / "derived"):
            if not folder.is_dir():
                continue
            for p in sorted(folder.glob("*.csv")):
                key = p.stem if folder != ed_dir / "derived" else f"derived/{p.stem}"
                tables[key] = load_csv(p)
        svg = json.loads((in_dir / "counties_svg.json").read_text(encoding="utf-8"))
        ed = cls(root=root, edition_id=edition_id, config=config, tables=tables, counties_svg=svg)
        ed._index()
        return ed

    def _index(self) -> None:
        self.as_of: date = date.fromisoformat(self.config["data_as_of"])
        self.units = {r["unit_id"]: r for r in self.tables["units"]}
        self.offices = {r["office_id"]: r for r in self.tables["offices"]}
        self.office_types = {r["office_type"]: r for r in self.tables["office_types"]}
        self.unit_types = {r["unit_type"]: r for r in self.tables["unit_types"]}
        self.elections = {r["election_id"]: r for r in self.tables["elections"]}
        self.rules = {r["rule_key"]: r for r in self.tables["election_rules"]}
        self.local_rules = {r["topic"]: r for r in self.tables["state_local_rules"]}
        self.boards = self.tables["appointed_boards"]
        # sources: every sources_*.csv (edition + Indiana) merged by id
        self.sources: dict[str, dict] = {}
        for name, rows in self.tables.items():
            if name.startswith("sources_"):
                for r in rows:
                    r = dict(r, _file=name)
                    if r["id"] in self.sources:
                        self.warnings.append(f"duplicate source id {r['id']} in {name}")
                    self.sources[r["id"]] = r
        # gaps: every gaps*.csv
        self.gaps_rows: list[dict] = []
        for name, rows in self.tables.items():
            if name.startswith("gaps"):
                for r in rows:
                    self.gaps_rows.append(dict(r, _file=name))
        self._terms_by_office: dict[str, list[dict]] = {}
        for t in self.tables["terms"]:
            self._terms_by_office.setdefault(t["office_id"], []).append(t)
        for lst in self._terms_by_office.values():
            lst.sort(key=lambda t: (parse_date(t["start"]) or date.min))
        self._offices_by_unit: dict[str, list[dict]] = {}
        for o in self.tables["offices"]:
            self._offices_by_unit.setdefault(o["unit_id"], []).append(o)
        # results grouped by contest; each contest linked to an office (computed)
        self.contests: dict[str, dict] = {}
        for r in self.tables["results"]:
            c = self.contests.get(r["contest_id"])
            if c is None:
                c = {"contest_id": r["contest_id"], "election_id": r["election_id"],
                     "label": r["contest_label"], "district": r["district"],
                     "party_primary": r["party_primary"], "vote_for": r["vote_for"],
                     "office_id": r["office_id"] or self._contest_office(r), "rows": []}
                self.contests[r["contest_id"]] = c
            c["rows"].append(r)
        self._unit_alias = {r["alias_id"]: r["unit_id"] for r in self.tables.get("derived/unit_id_aliases", [])}
        self._check()

    # ---- generic access ---------------------------------------------------------
    def table(self, name: str) -> list[dict]:
        return self.tables.get(name, [])

    @property
    def county(self) -> str:
        return self.config["county"]

    @property
    def county_label(self) -> str:
        return f"{self.config['county']} County"

    def variant(self, key: str) -> dict | None:
        v = self.config.get("variants", {}).get(key)
        if v is None:
            return None
        if not isinstance(v, dict) or "value" not in v:
            return {"value": v, "verified": (v or {}).get("verified", False) if isinstance(v, dict) else False, "note": ""}
        return v

    def source(self, sid: str) -> dict | None:
        return self.sources.get(sid)

    def unit_alias(self, alias_id: str) -> str | None:
        """Map an id from the money files (e.g. 'city-south-bend') to units.csv."""
        if alias_id in self.units:
            return alias_id
        return self._unit_alias.get(alias_id) or None

    def office_type_row(self, office: dict) -> dict | None:
        key = office["office_type"]
        if key in self.office_types:
            return self.office_types[key]
        alias = OFFICE_TYPE_ALIASES.get(key)
        return self.office_types.get(alias) if alias else None

    def offices_for(self, unit_id: str) -> list[dict]:
        return list(self._offices_by_unit.get(unit_id, []))

    def gaps(self, files: Iterable[str] | None = None, pattern: str | None = None,
             areas: Iterable[str] | None = None) -> list[dict]:
        files = set(files) if files else None
        areas = set(areas) if areas else None
        rx = re.compile(pattern, re.I) if pattern else None
        out = []
        for g in self.gaps_rows:
            if files and g["_file"] not in files:
                continue
            if areas and g.get("area") not in areas:
                continue
            if rx and not rx.search(f"{g.get('item', '')} {g.get('why_missing', '')}"):
                continue
            out.append(g)
        return out

    # ---- terms ------------------------------------------------------------------
    def terms_for(self, office_id: str) -> list[dict]:
        return list(self._terms_by_office.get(office_id, []))

    @staticmethod
    def term_end(term: dict) -> date | None:
        """Effective end: the end column, else 'scheduled_end=' from notes, else None (open)."""
        if term.get("end"):
            return parse_date(term["end"], end=True)
        m = re.search(r"scheduled_end=([0-9-]+)", term.get("notes", ""))
        return parse_date(m.group(1), end=True) if m else None

    def terms_on(self, office_id: str, on: date) -> list[dict]:
        out = []
        for t in self._terms_by_office.get(office_id, []):
            start = parse_date(t["start"])
            if start is None or start > on:
                continue
            end = self.term_end(t)
            if end is not None and end < on:
                continue
            out.append(t)
        return out

    def current_terms(self, office_id: str) -> list[dict]:
        """Holders on the data date. A winner whose term row is still unofficial (e.g. a legislator whose term
        legally began the day after the Nov 2026 election) is not a second current holder while a settled
        holder's row is still running; pages show that person as incoming instead (see incoming_terms)."""
        terms = self.terms_on(office_id, self.as_of)
        settled = [t for t in terms if t.get("status") != "unofficial"]
        return settled or terms

    def incoming_terms(self, office_id: str) -> list[dict]:
        """Terms that start after the data date, plus unofficial terms already started that current_terms
        set aside in favour of a settled holder."""
        current = self.current_terms(office_id)
        started_unofficial = [t for t in self.terms_on(office_id, self.as_of) if t not in current]
        return started_unofficial + [t for t in self._terms_by_office.get(office_id, [])
                                     if (parse_date(t["start"]) or date.min) > self.as_of]


    # ---- results ----------------------------------------------------------------
    _ORD = re.compile(r"^(\d+)(?:st|nd|rd|th)$")

    def _contest_office(self, row: dict) -> str:
        """results.csv leaves office_id blank; derive it from contest_id.

        contest_id = <election_id>-<body>[-<party>] e.g. '2026g-county-council-a',
        '2024p-county-sheriff-d', '2018g-county-superior-court-retention-manier'.
        """
        cid = row["contest_id"]
        rest = cid[len(row["election_id"]) + 1:] if cid.startswith(row["election_id"] + "-") else cid
        if row.get("party_primary") and re.search(r"-[a-z]$", rest):
            rest = rest[:-2]
        candidates = [rest]
        m = re.match(r"^county-commissioner-(\w+)$", rest)
        if m:
            n = self._ORD.sub(r"\1", m.group(1))
            candidates.insert(0, f"county-commissioner-d{n}")
        m = re.match(r"^(south-bend|mishawaka)-council-(\d)$", rest)
        if m:
            candidates.insert(0, f"{m.group(1)}-council-d{m.group(2)}")
        if rest == "county-circuit-judge":
            candidates.insert(0, "circuit-court-judge")
        if rest == "county-probate-judge":
            candidates.insert(0, "probate-court-judge")
        m = re.match(r"^county-superior-court-retention-(.+)$", rest)
        if m:
            candidates.insert(0, "superior-court-judge-" + m.group(1).split("-")[-1])
        for c in candidates:
            if c in self.offices:
                return c
        return ""

    def contests_for_office(self, office_id: str, general_only: bool = True) -> list[dict]:
        out = [c for c in self.contests.values() if c["office_id"] == office_id
               and (not general_only or not c["party_primary"])]
        out.sort(key=lambda c: self.elections.get(c["election_id"], {}).get("date", ""))
        return out

    # ---- integrity checks (reported, never fatal) ---------------------------------
    def _check(self) -> None:
        w = self.warnings
        for o in self.tables["offices"]:
            if o["unit_id"] not in self.units:
                w.append(f"offices: {o['office_id']} has unknown unit_id {o['unit_id']}")
            if self.office_type_row(o) is None:
                w.append(f"offices: office_type '{o['office_type']}' ({o['office_id']}) has no row in office_types.csv")
            if not self._terms_by_office.get(o["office_id"]):
                w.append(f"offices: {o['office_id']} has no terms")
        for t in self.tables["terms"]:
            if t["office_id"] not in self.offices:
                w.append(f"terms: {t['term_id']} has unknown office_id")
        for name in ("budgets", "budget_breakdowns", "spending_breakdowns", "tax_rates", "debt"):
            bad = sorted({r["unit_id"] for r in self.table(name) if r["unit_id"] not in self.units})
            unmapped = [b for b in bad if not self.unit_alias(b)]
            if bad:
                w.append(f"{name}: {len(bad)} unit_ids use a different id scheme than units.csv "
                         f"(mapped via derived/unit_id_aliases.csv; unmapped: {', '.join(unmapped) or 'none'})")
        # spending_breakdowns.csv (tools/build_spending.py): money in and out by unit; views are fixed
        views = {"income", "income_excluded", "by_purpose", "by_type", "spending_excluded", "passthrough_detail",
                 "passthrough_in_detail"}
        bad_views = sorted({r["view"] for r in self.table("spending_breakdowns")} - views)
        if bad_views:
            w.append(f"spending_breakdowns: unknown view(s) {', '.join(bad_views)}")
        blank = sum(1 for r in self.tables["results"] if not r["office_id"])
        if blank:
            linked = sum(1 for c in self.contests.values() if c["office_id"])
            w.append(f"results: office_id blank on {blank} of {len(self.tables['results'])} rows; "
                     f"derived from contest_id for {linked} of {len(self.contests)} contests")
        for name, rows in self.tables.items():
            for r in rows:
                for sid in split_ids(r.get("source_ids")):
                    if sid not in self.sources:
                        w.append(f"{name}: unknown source id {sid}")
