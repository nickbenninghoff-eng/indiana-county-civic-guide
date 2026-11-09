"""Seat-layer computation: which governments cover a place, and their seats.

Counts are computed from offices.csv, units.csv, appointed_boards.csv,
statewide_offices.csv and general_assembly_control.csv. Nothing is typed in.

Counting rules: see COUNTING_RULES below (also published on /about/#counting).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .data import nth_weekday_after

COUNTING_RULES = [
    "An office with a district (other than at-large) is one of a set of district seats. You vote for one "
    "district's seat; the other districts' seats are shown as elected by voters in other districts.",
    "Commissioners follow the edition setting for how commissioners are elected: elected by district uses the "
    "district rule; otherwise every commissioner counts as yours.",
    "At-large and single offices: you vote for every seat.",
    "Superior Court seats (merit selection) count as yours, because every county voter gets their yes-or-no "
    "retention questions.",
    "Offices that are not elected, and appointed boards, count as appointed seats.",
    "A blank seat count is shown as one question-mark marker, and the headline then says 'at least'.",
    "District seats with unequal or missing seat counts are shown as 'depends on your address'.",
    "Your two state legislators are counted; the rest of the General Assembly is noted but not drawn.",
    "Places are not matched to townships or school corporations by address. Defaults come from place names "
    "in the guide's data; pick yours to update the counts.",
]

GROUP_OF = {
    "county_commissioner": "Commissioners",
    "county_council_member": "County council",
    "county_auditor": "Row officers & prosecutor", "county_treasurer": "Row officers & prosecutor",
    "county_recorder": "Row officers & prosecutor", "county_clerk": "Row officers & prosecutor",
    "county_sheriff": "Row officers & prosecutor", "county_coroner": "Row officers & prosecutor",
    "county_surveyor": "Row officers & prosecutor", "county_assessor": "Row officers & prosecutor",
    "county_prosecutor": "Row officers & prosecutor",
    "circuit_court_judge": "Judges", "probate_court_judge": "Judges", "superior_court_judge": "Judges",
    "mayor": "Mayor & clerk", "city_clerk": "Mayor & clerk",
    "city_council_district": "Council districts", "city_council_at_large": "Council at-large",
    "township_trustee": "Trustee", "township_board_member": "Township board", "township_assessor": "Assessor",
    "town_clerk_treasurer": "Clerk-treasurer", "town_judge": "Town judge",
    "town_council_ward": "Council wards", "town_council_at_large": "Council at-large",
    "school_board_district": "District seats", "school_board_at_large": "At-large seats",
    "school_board_appointed": "Appointed seats",
    "state_house": "State representative", "state_senate": "State senator",
}

ELECTED_KINDS = ("vote", "other", "depends")


@dataclass
class Group:
    label: str
    kinds: list[str] = field(default_factory=list)
    titles: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)

    def summary(self) -> str:
        v = self.kinds.count("vote")
        o = self.kinds.count("other")
        d = self.kinds.count("depends")
        a = self.kinds.count("appointed")
        u = self.kinds.count("unknown")
        bits = []
        if v:
            bits.append(f"you vote for {v}")
        if o:
            bits.append(f"{o} elected by other districts")
        if d:
            bits.append(f"{d} district seats (yours depends on address)")
        if a:
            bits.append(f"{a} appointed")
        if u:
            bits.append("seat count not in data" if u == 1 else f"{u} seat counts not in data")
        return "; ".join(bits)


@dataclass
class Layer:
    key: str                 # state | county | township | municipality | school | library
    layer_id: str            # e.g. township:centre-township
    title: str
    groups: list[Group] = field(default_factory=list)
    note: str = ""
    government: bool = True
    next: dict = field(default_factory=dict)   # year -> [office labels]
    placeholder: bool = False
    offices: list = field(default_factory=list)   # offices behind the groups, for party breakdowns

    def count(self, kind: str) -> int:
        return sum(g.kinds.count(kind) for g in self.groups)

    @property
    def elected(self) -> int:
        return sum(self.count(k) for k in ELECTED_KINDS)

    @property
    def vote(self) -> int:
        return self.count("vote")

    @property
    def appointed(self) -> int:
        return self.count("appointed")

    @property
    def unknown(self) -> int:
        return self.count("unknown")


def _seats(value: str):
    m = re.match(r"\s*(\d+)", value or "")
    return int(m.group(1)) if m else None


def _is_district(o: dict) -> bool:
    d = (o.get("district") or "").strip().lower()
    return bool(d) and d != "at-large"


def _kinds_for_type(ed, office_type: str, offices: list[dict]) -> tuple[list[str], list[str]]:
    kinds, notes = [], []
    if all(o.get("elected") == "no" for o in offices):
        for o in offices:
            s = _seats(o["seats"])
            kinds += ["appointed"] * s if s else ["unknown"]
        return kinds, notes
    district = [o for o in offices if _is_district(o)]
    single = [o for o in offices if not _is_district(o)]
    by_district = True
    if office_type == "county_commissioner":
        v = ed.variant("commissioner_election") or {}
        by_district = v.get("value") == "by_district"
        notes.append("Elected by district per the edition settings" + ("" if v.get("verified") else " (not yet verified)")
                     if by_district else "Commissioners run in districts but every county voter votes for each")
    if district:
        seats = [_seats(o["seats"]) for o in district]
        if not by_district:
            for s in seats:
                kinds += ["vote"] * s if s else ["unknown"]
        elif all(seats) and len(set(seats)) == 1:
            s = seats[0]
            kinds += ["vote"] * s + ["other"] * (sum(seats) - s)
        else:
            known = sum(s for s in seats if s)
            kinds += ["depends"] * known + (["unknown"] if not all(seats) else [])
            notes.append("District seat counts differ or are missing, so the number you vote for depends on your address")
    for o in single:
        s = _seats(o["seats"])
        kinds += ["vote"] * s if s else ["unknown"]
    if office_type == "superior_court_judge":
        notes.append("Superior Court judges are chosen by merit selection; every county voter gets their yes/no retention questions")
    return kinds, notes


def office_groups(ed, offices: list[dict]) -> list[Group]:
    by_type: dict[str, list[dict]] = {}
    for o in offices:
        by_type.setdefault(o["office_type"], []).append(o)
    groups: dict[str, Group] = {}
    for otype, offs in by_type.items():
        label = GROUP_OF.get(otype, offs[0]["title"])
        g = groups.setdefault(label, Group(label))
        kinds, notes = _kinds_for_type(ed, otype, offs)
        g.kinds += kinds
        g.titles += [o["title"] for o in offs]
        g.notes += [n for n in notes if n not in g.notes]
        for o in offs:
            g.sources += [s for s in o["source_ids"].split(";") if s and s not in g.sources]
    return list(groups.values())


def board_groups(boards: list[dict]) -> list[Group]:
    out = []
    for b in boards:
        s = _seats(b.get("seats"))
        g = Group(b["name"], ["appointed"] * s if s else ["unknown"], [b["name"]],
                  [f"Appointed by: {b['appointing_authorities']}"] if b.get("appointing_authorities") else [],
                  [x for x in b["source_ids"].split(";") if x])
        out.append(g)
    return out


def _next(ed, offices: list[dict]) -> dict:
    out: dict[str, list[str]] = {}
    for o in offices:
        y = o.get("next_election", "")
        if not y.isdigit():
            continue
        yi = int(y)
        if yi < ed.as_of.year or (yi == ed.as_of.year and nth_weekday_after(yi, 11) <= ed.as_of):
            continue
        out.setdefault(y, [])
        label = GROUP_OF.get(o["office_type"], o["title"])
        if label not in out[y]:
            out[y].append(label)
    return out


def county_scope_boards(ed) -> list[dict]:
    """Boards of the county itself or of county-level special units (not cities/schools/libraries)."""
    out = []
    for b in ed.boards:
        u = ed.units.get(b["unit_id"], {})
        if b["unit_id"] == "county" or (u.get("parent_unit_ids") == "county" and
                                         u.get("unit_type") not in ("city", "town", "township", "school_corporation", "library")):
            out.append(b)
    return out


def build_layers(ed) -> dict:
    """All layers for every selectable unit, plus the place list. Returns a dict with
    'layers' (layer_id -> Layer), 'places' (list), 'townships', 'schools'."""
    units = ed.units
    layers: dict[str, Layer] = {}

    # --- state
    statewide = [r for r in ed.table("statewide_offices") if r.get("elected_or_appointed") == "elected"]
    st = Layer("state", "state", "State of Indiana")
    st.groups.append(Group("Governor & statewide officers", ["vote"] * len(statewide), [r["office"] for r in statewide],
                           [], sorted({s for r in statewide for s in r["source_ids"].split(";") if s})))
    ga = ed.table("general_assembly_control")
    latest = {}
    for r in ga:
        if r.get("total_seats", "").isdigit():
            if r["chamber"] not in latest or int(r["year"]) > int(latest[r["chamber"]]["year"]):
                latest[r["chamber"]] = r
    legis = Group("Your legislators", ["vote", "vote"], ["State representative", "State senator"])
    house = [o for o in ed.offices_for("in-house")]
    senate = [o for o in ed.offices_for("in-senate")]
    others = []
    if "House" in latest:
        others.append(f"{int(latest['House']['total_seats']) - 1} other representatives")
    if "Senate" in latest:
        others.append(f"{int(latest['Senate']['total_seats']) - 1} other senators")
    legis.notes.append("Plus " + " and ".join(others) + " elected statewide by other districts (not drawn)" if others else "")
    legis.notes.append("Districts that include part of the county: House " + ", ".join(o["district"] for o in house) +
                       "; Senate " + ", ".join(o["district"] for o in senate))
    legis.sources = sorted({s for r in latest.values() for s in r["source_ids"].split(";") if s} |
                           {s for o in house + senate for s in o["source_ids"].split(";") if s})
    st.groups.append(legis)
    # House seats are all on the same two-year cycle; Senate districts alternate, so the
    # senator's year depends on the district and is left out of 'next on your ballot'.
    st.next = _next(ed, house[:1])
    st.note = "Your House and Senate districts depend on your address; Senate seats alternate election years."
    layers[st.layer_id] = st

    # --- county (+ courts + county-level boards)
    co_offices = ed.offices_for("county") + ed.offices_for("sjc-courts")
    co = Layer("county", "county", units["county"]["name"])
    co.groups = office_groups(ed, co_offices) + board_groups(county_scope_boards(ed))
    co.next = _next(ed, co_offices)
    co.offices = co_offices
    layers[co.layer_id] = co

    # --- townships
    townships = [u for u in ed.tables["units"] if u["unit_type"] == "township"]
    for u in townships:
        offs = ed.offices_for(u["unit_id"])
        L = Layer("township", f"township:{u['unit_id']}", u["name"], office_groups(ed, offs))
        L.next = _next(ed, offs)
        L.offices = offs
        layers[L.layer_id] = L
    # generic township: office types every township has
    common = None
    for u in townships:
        types = {o["office_type"] for o in ed.offices_for(u["unit_id"])}
        common = types if common is None else common & types
    sample = ed.offices_for(townships[0]["unit_id"]) if townships else []
    extra = sorted({u["name"] for u in townships if {o["office_type"] for o in ed.offices_for(u["unit_id"])} - (common or set())})
    # The placeholder uses one township's offices only for their shared structure; titles are made
    # generic so no single township is presented as the default.
    sample_name = townships[0]["name"] if townships else ""
    generic = [dict(o, title=o["title"].replace(sample_name, "Township").strip())
               for o in sample if o["office_type"] in (common or set())]
    anyL = Layer("township", "township:any", "Your township (pick one above)",
                 office_groups(ed, generic), placeholder=True)
    anyL.note = ("Seats every township has. " + (f"{', '.join(extra)} also elect{'s' if len(extra) == 1 else ''} other offices." if extra else ""))
    anyL.next = _next(ed, [o for o in sample if o["office_type"] in (common or set())])
    layers[anyL.layer_id] = anyL

    # --- cities and towns
    munis = [u for u in ed.tables["units"] if u["unit_type"] in ("city", "town")]
    for u in munis:
        offs = ed.offices_for(u["unit_id"])
        boards = [b for b in ed.boards if b["unit_id"] == u["unit_id"] or
                  units.get(b["unit_id"], {}).get("parent_unit_ids") == u["unit_id"]]
        L = Layer("municipality", f"municipality:{u['unit_id']}", u["name"], office_groups(ed, offs) + board_groups(boards))
        if not offs:
            L.note = "No offices for this unit are in the guide's data yet."
        L.next = _next(ed, offs)
        L.offices = offs
        layers[L.layer_id] = L

    # --- school corporations (appointed seats come from offices.csv, not boards, to avoid double counting)
    schools = [u for u in ed.tables["units"] if u["unit_type"] == "school_corporation"]
    for u in schools:
        offs = ed.offices_for(u["unit_id"])
        L = Layer("school", f"school:{u['unit_id']}", u["name"], office_groups(ed, offs))
        L.next = _next(ed, offs)
        L.offices = offs
        L.note = ("Counts treat district seats as chosen by that district's voters; the guide hasn't confirmed "
                  "each corporation's method yet.") if any(_is_district(o) for o in offs) else ""
        layers[L.layer_id] = L
    sch_any = Layer("school", "school:any", "Your school corporation (pick one above)", [], placeholder=True)
    sch_any.note = "The guide doesn't map addresses to school corporations. Pick yours to see its board seats."
    layers[sch_any.layer_id] = sch_any

    # --- libraries: service areas are not mapped, so show the shared structure if all match
    libs = [u for u in ed.tables["units"] if u["unit_type"] == "library"]
    lib_boards = [b for b in ed.boards if b["unit_id"] in {u["unit_id"] for u in libs}]
    seats = {_seats(b["seats"]) for b in lib_boards}
    names = ", ".join(u["name"] for u in libs)
    lib = Layer("library", "library", "Public library")
    if len(seats) == 1 and None not in seats:
        s = seats.pop()
        g = Group("Library board", ["appointed"] * s, [b["name"] for b in lib_boards],
                  [f"Each library board in the guide's data has {s} appointed seats"],
                  sorted({x for b in lib_boards for x in b["source_ids"].split(";") if x}))
        lib.groups.append(g)
    else:
        lib.groups.append(Group("Library board", ["unknown"], [b["name"] for b in lib_boards]))
    lib.note = f"Which library district covers an address isn't mapped yet. Libraries in the guide's data: {names}."
    layers[lib.layer_id] = lib

    # --- places
    def short(name: str) -> str:
        return re.sub(r"^(City|Town) of |\s+Township$", "", name)

    # Which township(s) a city or town lies in comes from derived/township_places.csv. A place that
    # lies in exactly one township defaults to it; a place split across several (South Bend,
    # Mishawaka) or not mapped defaults to "pick one", so no township is preselected for it.
    in_towns: dict[str, set] = {}
    for r in ed.table("derived/township_places"):
        if r.get("place_unit_id"):
            in_towns.setdefault(r["place_unit_id"], set()).add(r["township_unit_id"])

    def default_township(unit_id: str):
        ts = in_towns.get(unit_id, set())
        return next(iter(ts)) if len(ts) == 1 else "any"

    def default_school(names: list[str]):
        for u in schools:
            hay = " ".join([u.get("places_covered") or ""] + [o.get("district") or "" for o in ed.offices_for(u["unit_id"])]).lower()
            for n in names:
                if n and re.search(r"\b" + re.escape(n.lower()) + r"\b", hay):
                    return u["unit_id"]
        return "any"

    places = []
    for u in munis:
        s = short(u["name"])
        t = default_township(u["unit_id"])
        places.append({"id": u["unit_id"], "label": u["name"], "kind": u["unit_type"],
                       "muni": u["unit_id"], "township": None, "township_default": t,
                       "school_default": default_school([s] + ([short(units[t]["name"])] if t != "any" else []))})
    for u in townships:
        s = short(u["name"])
        places.append({"id": f"unincorporated-{u['unit_id']}", "label": f"Unincorporated {u['name']}", "kind": "unincorporated",
                       "muni": None, "township": u["unit_id"], "township_default": u["unit_id"],
                       "school_default": default_school([s])})
    return {"layers": layers, "places": places, "townships": townships, "schools": schools}


def election_dates(ed, years) -> dict:
    """Primary and general dates computed from the Indiana calendar rules."""
    out = {}
    for y in years:
        yi = int(y)
        out[str(y)] = {"primary": nth_weekday_after(yi, 5), "general": nth_weekday_after(yi, 11)}
    return out
