"""Elections by the numbers (Wave B batch 2, 2026-11-09; planning/qa/site-ux-review-2026-11-09.md §3.4).

The old one-page landscape (66 screens, 14 tables) is split by measure:

    elections/landscape/   overview: four summary cards (turnout, margins, up next, how officeholders took office)
    elections/margins/     "Margins: how close each race was": counts, small multiples by level, a map and a
                           list by area and seat to find a race, and every race as a table (see-all fold)
    elections/turnout/     turnout with its denominator, odd vs even years, and straight-party ballots
    officeholders/         every current elected officeholder by government, and how each first took office
    (the old "Up next" table is on elections/calendar/, pages/elections.py build_calendar)

Every old landscape id that is not on the overview is forwarded by its #moved-anchors map (static/js/moved.js);
tools/tests/test_wave_b_numbers.py pins them against tools/tests/fixtures/anchors_before_wave_b2.json.

Rules kept from the landscape page: the margin scope (no statewide offices, no legislative districts in years they
crossed the county line, no questions, retention or straight-party lines), the three numeric bands, no party filter,
groups in fixed office order, races ordered by margin or date only. Charts use the accent/ink ramp, never party colors.
"""
from __future__ import annotations

import re

from civic.charts import hbar, share_bars
from civic.components import (STATUS, data_table, filter_empty_note, party_label, section, see_all_table, status_badge,
                              table_filter)
from civic.data import PARTY_LABELS, SELECTED_BY_LABELS, fmt_date, fmt_int
from civic.district_map import district_map, district_set, load_district_shapes
from civic.html import Markup, h, json_script
from civic.map import load_shapes, load_votes, race_by_contest
from civic.pick_one import one_bar, one_fold
from civic.preselect import county_districts, here_attrs, here_slot
from civic.related import contest_href

from pages.elections import (BANDS, MUNICIPAL_TYPES, SCHOOLS, TOWNS, TYPE_LABEL, YEARS, _calendar_items, _district_of,
                             _election_name, _election_short, _elections, _gaps, _hero, _holders_now, _opts, _place_order,
                             _plabel, _rest, _rule_p, _search_text, _src, _straight_party_years, _turnout_chart,
                             _unit_attrs, _unit_controls, candidates, classify, contest_status, is_question,
                             is_writein_total, margin, moved_anchors, plain_badge, badge_key, first_by_text)

# contests that are in the guide's results but not races decided by this county's voters between candidates
SCOPE_OUT = ("Straight-party ballots", "Public questions", "Superior Court retention")
# office groups on the margins page, in fixed office order (county -> city/town -> township -> school -> legislature),
# never by value; each lands on its level in "Find a race"
MARGIN_GROUPS = [("County row offices", "county"), ("County commissioners", "county"), ("County council", "county"),
                 ("County courts", "county"), ("City offices", "city"), ("Town offices", "town"),
                 ("Township offices", "township"), ("School boards", "school"), ("State legislature", "legislature")]
AREA_LEVELS = [("county", "County"), ("city", "Cities"), ("town", "Towns"), ("township", "Townships"),
               ("school", "School boards"), ("legislature", "State legislature (districts wholly inside the county)")]
# school board contest ids start with these; the units are the school corporations of civic/data (LaVille's
# corporation is not a unit of the guide: it lies mostly in Marshall County)
SCHOOL_UNIT = {"south-bend-schools": "sbcsc", "mishawaka-schools": "school-city-mishawaka",
               "penn-harris-madison-schools": "phm", "john-glenn-schools": "john-glenn",
               "union-north-schools": "union-north", "new-prairie-schools": "new-prairie", "laville-schools": None}
# kinds of race, in the order of the share bars: uncontested first (the page's first fact), then the three bands,
# then the races that can't be measured. Marks: ink for "no contest", the accent ramp for the bands (darker = closer),
# the no-data mark for "not measurable". Never party colors (review decision Q10).
KINDS = [("unc", "Uncontested", "m-ink"), ("under-5", "Under 5 points", "m-share-0"), ("5-15", "5 to 15 points", "m-share-1"),
         ("over-15", "Over 15 points", "m-share-2"), ("nc", "Not measurable", "m-nodata")]
KIND_LABEL = {k: lab for k, lab, _ in KINDS}
TICK_MAX = 30.0   # the margin strip under each race runs from 0 to 30 points; wider margins sit at its right end

_ORDINAL = re.compile(r",\s*(\d+)(?:st|nd|rd|th)\b")
_WARD = re.compile(r"\bWard\s+(\w+)")


# =========================================================================== margins: the data

def seat_district(c, office) -> str:
    """'District 1', 'District A' or 'Ward 4' for a contest; '' for an at-large or single-district seat.
    The office's district comes first; then the contest name ("District 1", "Ward 4", "Commissioner, 2nd")."""
    d = (office or {}).get("district", "")
    if re.fullmatch(r"[0-9A-Z]{1,2}", d):
        return f"District {d}"
    if re.fullmatch(r"Ward \w+", d):
        return d
    label = c["label"]
    m = _district_of(label)
    if m:
        return m
    w = _WARD.search(label)
    if w:
        return f"Ward {w.group(1)}"
    o = _ORDINAL.search(label)
    return f"District {o.group(1)}" if o else ""


def area_of(c, group: str, office, district: str) -> str:
    """The area a race belongs to on the margins page's map and list: a township, city or town, school corporation,
    county or city council district, legislative district, or "countywide"."""
    rest = _rest(c)
    dk = district.split(" ", 1)[1].lower() if district.startswith("District ") else ""
    if group in ("County row offices", "County courts"):
        return "countywide"
    if group == "County commissioners":
        return f"commissioner-{dk}" if dk else "countywide"
    if group == "County council":
        return f"council-{dk}" if dk else "countywide"
    if group == "City offices":
        city = "south-bend" if rest.startswith("south-bend-") else "mishawaka"
        return f"{city}-council-{dk}" if dk and "council" in rest else city
    if group == "Town offices":
        return next(t for t in TOWNS if rest.startswith(t))
    if group == "Township offices":
        if office:
            return office["unit_id"]
        return rest[:rest.index("-township") + len("-township")]
    if group == "School boards":
        key = next(s for s in SCHOOLS if rest.startswith(s))
        return SCHOOL_UNIT.get(key) or key
    if group == "State legislature":
        return ("house-" if rest.startswith("state-house") else "senate-") + dk
    return "other"


def area_level(key: str) -> str:
    if key == "countywide" or key.startswith(("commissioner-", "council-")):
        return "county"
    if key.startswith(("south-bend", "mishawaka")) and key != "school-city-mishawaka":
        return "city"
    if key in TOWNS:
        return "town"
    if key.endswith("-township"):
        return "township"
    if key.startswith(("house-", "senate-")):
        return "legislature"
    return "school"


def area_name(ed, key: str, fallback: str = "") -> str:
    if key == "countywide":
        return "Countywide offices"
    m = re.fullmatch(r"(commissioner|council)-(\w+)", key)
    if m:
        return f"County {'Commissioner' if m.group(1) == 'commissioner' else 'Council'} District {m.group(2).upper()}"
    m = re.fullmatch(r"(south-bend|mishawaka)-council-(\w+)", key)
    if m:
        return f"{ed.units[m.group(1)]['name'].replace('City of ', '')} Common Council District {m.group(2).upper()}"
    if key in ("south-bend", "mishawaka"):
        return f"{ed.units[key]['name'].replace('City of ', '')}: citywide offices"
    m = re.fullmatch(r"(house|senate)-(\d+)", key)
    if m:
        return f"Indiana {'House' if m.group(1) == 'house' else 'Senate'} District {m.group(2)}"
    if key in ed.units:
        return ed.units[key]["name"]
    return fallback or key


def _area_sort(ed, key: str):
    m = re.search(r"-(\w+)$", key)
    tail = m.group(1) if m else ""
    num = (0, int(tail), "") if tail.isdigit() else (1, 0, tail)
    if key == "countywide":
        return (0, "", num)
    if key.startswith("commissioner-"):
        return (1, "", num)
    if key.startswith("council-"):
        return (2, "", num)
    if key in ("south-bend", "mishawaka"):
        return (3, key, (0, 0, ""))
    if "-council-" in key:
        return (3, key.split("-council-")[0], (1,) + num)
    if key.startswith("house-"):
        return (4, "", num)
    if key.startswith("senate-"):
        return (5, "", num)
    return (6, area_name(ed, key), num)


def _tail(label: str) -> str:
    m = re.search(r"\(([^()]*primary)\)\s*$", label, re.I)
    return m.group(1) if m else ""


def seat_name(label: str) -> str:
    """The seat as printed on the canvass, without the place prefix and the primary's party tail."""
    s = _search_text(label)
    return s.split(":", 1)[1].strip() if ":" in s else s


def margin_races(ed) -> list[dict]:
    """Every contest in the explorer's years (2010 on) that the county's voters decided between candidates, with its
    kind: "unc" (no more candidates than seats), a band id, or "nc" (not measurable: seat count not in the data or
    votes missing). Same scope as the old landscape page."""
    els = {e["election_id"]: e for e in _elections(ed)}
    out = []
    for c in ed.contests.values():
        e = els.get(c["election_id"])
        if not e:
            continue
        g, place, cross = classify(c)
        if cross or g in SCOPE_OUT or is_question(c):
            continue
        m = margin(c)
        kind = "unc" if m is None else (m["band"] if "pts" in m else "nc")
        o = ed.offices.get(c["office_id"]) if c.get("office_id") else None
        dist = seat_district(c, o)
        out.append({"c": c, "e": e, "g": g, "place": place or "(not stated)", "office": o, "district": dist,
                    "area": area_of(c, g, o, dist), "kind": kind, "m": m, "st": contest_status(c["rows"]),
                    "seat": c["office_id"] or _rest(c), "seat_name": seat_name(c["label"])})
    return out


def _counts(races) -> dict:
    out = {k: 0 for k, _, _ in KINDS}
    for r in races:
        out[r["kind"]] += 1
    return out


def _contested(counts) -> int:
    return sum(counts[b] for b, _, _, _ in BANDS)


def _closest(races):
    pool = [r for r in races if "pts" in (r["m"] or {})]
    return min(pool, key=lambda r: (r["m"]["pts"], r["e"]["date"])) if pool else None


def _when(r) -> str:
    """'Nov 6, 2018 · general election' or 'May 2, 2023 · Republican primary' (the canvass's own label)."""
    return f"{fmt_date(r['e']['date'])} · {_tail(r['c']['label']) or TYPE_LABEL.get(r['e']['type'], r['e']['type'])}"


def cand_name(x, primary: bool) -> str:
    """Name with the party code as printed; a primary's candidates carry no code (the primary names the party)."""
    if x["party"]:
        return f"{x['name']} ({x['party']})"
    return x["name"] if primary else f"{x['name']} (no party listed)"


def _cand(x, primary: bool) -> str:
    return f"{cand_name(x, primary)} {x['votes']:,}"


def _who(m, primary: bool = False) -> str:
    """The two candidates the margin compares, in words that claim nothing beyond the vote counts."""
    a, b = m["ahead"], m["next"]
    if m["tie"]:
        won = [x["name"] for x in (a, b) if x["winner"] == "Y"]
        t = f"Tied: {cand_name(a, primary)} and {cand_name(b, primary)}, {a['votes']:,} votes each. "
        if len(won) == 1:
            return t + f"The canvass marks {won[0]} as elected; how the tie was settled is not in the guide's data."
        return t + "The guide's data does not say how the tie was settled."
    if m["seats"] == 1:
        return f"Most votes: {_cand(a, primary)}. Next: {_cand(b, primary)}."
    return f"Last inside the {m['seats']} seats: {_cand(a, primary)}. Next: {_cand(b, primary)}."


def _pts_text(m) -> str:
    if m["tie"]:
        return "0 points · tied"
    return f"{m['pts']:.2f} points · {m['votes']:,} vote{'s' if m['votes'] != 1 else ''} apart"


# =========================================================================== margins: the page

def build_margins(site):
    ed = site.ed
    page = site.page("elections/margins/index.html", banners=True)
    cites = page.cites
    els = _elections(ed)
    span = f"{els[0]['date'][:4]} to {els[-1]['date'][:4]}"
    races = margin_races(ed)
    counts = _counts(races)
    n_all, n_unc, n_nc, n_con = len(races), counts["unc"], counts["nc"], _contested(counts)
    src_votes = _src(*[r["c"]["rows"][0] for r in races])
    computed = status_badge("computed", page, "Counted from results.csv vote counts and seat counts.")
    toc = [("short-answer", "The short answer"), ("by-level", "By level of government"), ("find", "Find a race"),
           ("all-races", "All races as a table"), ("rules", "What this page does not do"), ("gaps", "Gaps"),
           ("sources", "Sources")]
    page.add(_hero(page, "Reference · Elections · By the numbers",
                   f"Every race for local office decided inside the county from {span}: how many had no contest, and "
                   "how close the others were. Past results only; the bands say nothing about future races.",
                   ["county"], toc))

    # ---- §1 the short answer
    tiles = [("unc", n_unc, "had no contest", "No more candidates on the ballot than seats to fill."),
             ("con", n_con, "were contested", "More candidates than seats, with every vote count recorded."),
             ("nc", n_nc, "can't be measured", "The seat count is not in the data, or a vote count is missing."),
             ("all", n_all, f"races in all, {span}", "Decided by voters inside the county (scope below).")]
    page.add(section("short-answer", 1, "The short answer",
                     h("p", {"class": "mg-lede"},
                       h("strong", None, f"{n_unc:,} of the {n_all:,} races"), f" for local office decided inside the county "
                       f"from {span} had no contest: no more candidates on the ballot than seats to fill. ",
                       computed, cites.cite_compact(src_votes)),
                     h("ul", {"class": "mg-tiles"},
                       [h("li", {"class": f"mg-tile mg-tile-{k}"}, h("span", {"class": "mg-tile-n mono"}, f"{n:,}"),
                          h("span", {"class": "mg-tile-l"}, lab), h("span", {"class": "mg-tile-d"}, d)) for k, n, lab, d in tiles]),
                     h("p", {"class": "muted"}, f"{n_all:,} = {n_unc:,} uncontested + {n_con:,} contested + {n_nc:,} not "
                                                "measurable. ", computed),
                     share_bars("margin-bands", "How close were local races?",
                                [{"label": f"All races, {span}", "counts": counts}],
                                [{"key": k, "label": lab, "mark": mk} for k, lab, mk in KINDS],
                                subtitle=f"{n_all:,} races decided inside the county; primaries and generals together",
                                noun=("race", "races"), ramp="alt", status="computed", page=page, group_header="Races",
                                cite=cites.cite_compact(src_votes),
                                note="Uncontested races are in ink; the three margin bands in the accent color, darker for "
                                     "closer races. Colors never stand for a party."),
                     h("div", {"class": "callout elx-def", "id": "bands"},
                       h("p", None, h("strong", None, "How the margin is measured. "),
                         "Margin in points = the votes of the last candidate inside the seats minus the votes of the next "
                         "candidate, divided by all votes cast in that contest. In a one-seat race that is the winner and "
                         "the runner-up. In a race that fills several seats (vote for 3, for example) it compares the "
                         "candidates just inside and just outside the seats. Places are ranked by votes."),
                       h("p", None, h("strong", None, "Bands. "), "Under 5 points; 5 to 15 points; over 15 points. Each race "
                         "is put in a band by its margin alone. The bands describe past results and say nothing about future races."),
                       h("p", None, h("strong", None, "Uncontested. "), "No more candidates than seats. A canvass line that "
                         "totals all write-in votes is not a candidate, so a race with one named candidate for one seat is "
                         "uncontested whatever its write-in total; a write-in candidate the canvass names is a candidate.")),
                     h("p", None, f"{n_con} races are contested, whatever party finished ahead. "
                                  f"{n_unc} uncontested races (no more candidates than seats) and {n_nc} races with missing vote "
                                  "counts or no recorded seat count have no margin. Statewide offices, and legislative districts in "
                                  "years when they extended outside the county, are left out because the county tally doesn't "
                                  "decide them. Retention votes and public questions "
                                  "are yes-or-no votes, not races between candidates; they are on ",
                       h("a", {"href": page.rel("elections/judges-and-questions/index.html")}, "Judges and public questions"),
                       ". ", status_badge("computed", page, "Margins computed from results.csv vote counts.")),
                     scope="county", ed=ed))

    # ---- §2 by level of government (small multiples)
    groups = []
    for g, lvl in MARGIN_GROUPS:
        rs = [r for r in races if r["g"] == g]
        cg = _counts(rs)
        groups.append({"label": g, "counts": cg, "href": f"#lvl-{lvl}",
                       "tip": f"{len(rs)} races: {_contested(cg)} contested, {cg['unc']} uncontested"})
    page.add(section("by-level", 2, "By level of government",
                     h("p", None, "One bar per group of offices, in office order, never by value. Each bar is every race of "
                                  "that group, so a share is always shown with its base. Open a group's races under Find a "
                                  "race."),
                     share_bars("margin-levels", "How close races were, by level of government", groups,
                                [{"key": k, "label": lab, "mark": mk} for k, lab, mk in KINDS],
                                subtitle=f"{n_all:,} races decided inside the county, {span}", noun=("race", "races"),
                                ramp="alt", status="computed", page=page, group_header="Office group",
                                cite=cites.cite_compact(src_votes)),
                     scope="county", ed=ed))

    # ---- §3 find a race: the map, then every area's races by seat
    on_map = _map_races(ed)
    by_area: dict[str, list] = {}
    for r in races:
        by_area.setdefault(r["area"], []).append(r)
    shapes = load_shapes(ed)
    dshapes = load_district_shapes(ed, shapes) if shapes else None
    lines_from = _lines_from(dshapes)
    dmap = _find_map(page, ed, shapes, dshapes, by_area, lines_from)
    g_ix = {g: str(i) for i, (g, _) in enumerate(MARGIN_GROUPS)}
    places = sorted({r["place"] for r in races})
    p_ix = {p: str(i) for i, p in enumerate(places)}
    dists = sorted({r["district"] for r in races} - {""}, key=_dist_key)
    levels, n_seats = [], 0
    for lvl, lvl_name in AREA_LEVELS:
        keys = sorted([k for k in by_area if area_level(k) == lvl], key=lambda k: _area_sort(ed, k))
        items = []
        for k in keys:
            body, ns = _area_body(page, ed, k, by_area[k], on_map, lines_from, g_ix, p_ix)
            n_seats += ns
            items.append(h("li", {"class": "mg-area", "data-tf-group": True},
                           one_fold(k, area_name(ed, k, by_area[k][0]["place"]),
                                    [h("h4", {"class": "one-h mg-area-h"}, area_name(ed, k, by_area[k][0]["place"])),
                                     h("span", {"class": "one-digest"}, _digest(_counts(by_area[k])))],
                                    body, item_id=f"area-{k}", cls="mg-area-fold")))
        if items:
            levels.append(h("section", {"class": "mg-level", "id": f"lvl-{lvl}", "aria-labelledby": f"lvl-{lvl}-h",
                                        "data-tf-group": True},
                            h("h3", {"class": "mg-level-h", "id": f"lvl-{lvl}-h"}, lvl_name),
                            h("ul", {"class": "mg-areas one-list"}, items)))
    no_shape = [k for k in by_area if not _has_shape(k, shapes, dshapes)]
    finder = table_filter("mg-find", [
        {"key": "office", "label": "Office", "all": "All offices", "options": [(g_ix[g], g) for g, _ in MARGIN_GROUPS
                                                                                if any(r["g"] == g for r in races)]},
        {"key": "place", "label": "Place", "all": "All places", "options": [(p_ix[p], p) for p in places]},
        {"key": "district", "label": "District", "all": "Any district", "options": _opts(dists)}],
        n_seats, noun="seat", search="Words in the seat or a candidate's name", label="Filter the races by seat")
    page.add(section("find", 3, "Find a race",
                     h("p", None, "Pick an area on the map, or open any area below. Each area lists its seats, each seat its "
                                  "races, newest first, with the margin and the two candidates it compares. Every race links "
                                  "to its full result. Filters narrow the list to the seats of one office group, place or "
                                  "district."),
                     dmap,
                     h("p", {"class": "muted"}, "Not on the map: ",
                       "; ".join(area_name(ed, k, by_area[k][0]["place"]) for k in sorted(no_shape, key=lambda k: _area_sort(ed, k))),
                       ". They are in the list below.") if no_shape else None,
                     badge_key(page, [" The strip under each race runs from 0 to 30 points; its marks at 5 and 15 are the band "
                                      "edges, and a race over 30 points sits at its right end. Vote counts come from the county "
                                      "canvass files listed under Sources.", cites.cite_compact(src_votes)]),
                     finder, filter_empty_note("mg-find"),
                     one_bar("area", "areas", "Pick an area on the map, or open any area below."),
                     _here_margin_areas(page, ed),
                     h("div", {"class": "mg-find", "id": "mg-find", "data-tf-deep": True}, levels),
                     scope="county", ed=ed))

    # ---- §4 every contested race as one table (the old landscape table: same id, filters and order)
    contested = sorted([r for r in races if "pts" in (r["m"] or {})], key=lambda r: (r["m"]["pts"], r["e"]["date"]))
    trows, tattrs = [], []
    for r in contested:
        m, e, c = r["m"], r["e"], r["c"]
        href = contest_href(page, c["contest_id"])
        a, b = m["ahead"], m["next"]
        lab = h("a", {"href": href}, c["label"]) if href else c["label"]
        trows.append([h("span", None, lab, h("span", {"class": "elx-sub muted"}, f" · {m['seats']} seats") if m["seats"] > 1 else None),
                      _election_short(e), f"{m['pts']:.2f}", f"{m['votes']:,}" + (" (tied)" if m["tie"] else ""),
                      KIND_LABEL[r["kind"]], _cand(a, bool(c.get("party_primary"))), _cand(b, bool(c.get("party_primary"))),
                      plain_badge(r["st"], m["low"])])
        tattrs.append({"data-margin": f"{m['pts']:.4f}", "data-date": e["date"], "data-tf-year": e["date"][:4],
                       "data-tf-type": "primary" if "primary" in e["type"] else "general", "data-tf-band": r["kind"],
                       "data-tf-office": g_ix[r["g"]], "data-tf-place": p_ix[r["place"]],
                       "data-tf-district": r["district"], "data-tf-text": _search_text(c["label"])})
    years = sorted({e["date"][:4] for e in els if any(r["e"] is e for r in contested)}, reverse=True)
    table = see_all_table(
        "margins-table", ["Contest", "Election", "Margin (points)", "Votes apart", "Band", "Last candidate inside the seats",
                          "Next candidate", "Status"], trows,
        noun="race", caption="Margins in every race decided inside the county, closest first", numeric=(2, 3),
        min_width="60rem", row_attrs=tattrs,
        controls=[{"key": "year", "label": "Year", "all": "All years", "options": _opts(years)},
                  {"key": "type", "label": "Election", "all": "All elections",
                   "options": [("general", "General elections"), ("primary", "Primaries")]},
                  {"key": "band", "label": "Band", "all": "All bands", "options": [(bid, lab) for bid, lab, _, _ in BANDS]},
                  {"key": "office", "label": "Office", "all": "All offices",
                   "options": [(g_ix[g], g) for g, _ in MARGIN_GROUPS if any(r["g"] == g for r in contested)]},
                  {"key": "place", "label": "Place", "all": "All places",
                   "options": [(p_ix[p], p) for p in places if any(r["place"] == p for r in contested)]},
                  {"key": "district", "label": "District", "all": "Any district",
                   "options": _opts(sorted({r["district"] for r in contested} - {""}, key=_dist_key))}],
        search="Words in the contest name",
        sort=[("margin", "Closest first", "margin:asc:n"), ("date", "Newest first", "date:desc:s,margin:asc:n")],
        filter_label="Filter the margins table", fold_id="margins-table-all",
        summary=f"See all {len(contested)} contested races as one table",
        intro=h("p", None, "Every contested race, closest first, whatever party finished ahead; the same races as the list "
                           "above. Copy CSV copies the rows the filters leave shown."))
    page.add(section("all-races", 4, "All races as a table",
                     h("p", None, "For researchers: one row per contested race, with filters by year, election, band, office, "
                                  "place and district, and Copy CSV. Uncontested races are listed under each seat above."),
                     table,
                     h("p", {"class": "muted"}, "Party codes: ", "; ".join(f"{k} = {v}" for k, v in PARTY_LABELS.items()), "."),
                     scope="county", ed=ed))
    page.add(_rules_section(page, ["forecast", "party", "colors", "votes-map"]))
    page.finish(gaps=_gaps(ed, None, ["gaps_elections"], r"margin|seat count")
                + _gaps(ed, None, ["gaps_results"], r"winner|seat count|multi-seat|2026 general"))
    return page


def _dist_key(d: str):
    kind, _, k = d.partition(" ")
    return (kind, (0, int(k), "") if k.isdigit() else (1, 0, k))


def _digest(cnt) -> str:
    parts = [f"{_contested(cnt)} contested"]
    if cnt["under-5"]:
        parts.append(f"{cnt['under-5']} under 5 points")
    parts.append(f"{cnt['unc']} uncontested")
    if cnt["nc"]:
        parts.append(f"{cnt['nc']} not measurable")
    return " · ".join(parts)


def _map_races(ed) -> dict:
    shapes = load_shapes(ed)
    if not (shapes and "precinct" in shapes.get("layers", {})):
        return {}
    return race_by_contest(ed, load_votes(ed))


def _lines_from(dshapes) -> dict:
    """{area key prefix: first election year of the district lines on the map} for the district layers."""
    out = {}
    for set_id, prefix in (("county-commissioner-2022", "commissioner-"), ("county-council-2022", "council-"),
                           ("south-bend-council-2022", "south-bend-council-"), ("mishawaka-council-2022", "mishawaka-council-"),
                           ("in-house-2021", "house-"), ("in-senate-2021", "senate-")):
        rec = district_set(dshapes, set_id)
        if rec and (rec.get("first_election") or "").isdigit():
            out[prefix] = int(rec["first_election"])
    return out


def _lines_year(key: str, lines_from: dict) -> int | None:
    for prefix, y in lines_from.items():
        if key.startswith(prefix):
            return y
    return None


def _race_row(page, r, on_map, lines_year) -> Markup:
    c, m, e = r["c"], r["m"], r["e"]
    href = contest_href(page, c["contest_id"])
    links = [h("a", {"href": href}, "Full result") if href else None]
    if c["contest_id"] in on_map:
        links.append(h("a", {"href": page.rel(f"map/index.html#race-{on_map[c['contest_id']]}")}, "How areas voted"))
    links = [x for x in links if x]
    seats = f" · {m['seats']} seats" if m and m.get("seats", 1) > 1 else ""
    earlier = (h("p", {"class": "mg-note"}, f"Held under the district lines in use before {lines_year}, not the ones on the map.")
               if lines_year and int(e["date"][:4]) < lines_year else None)
    foot = h("p", {"class": "mg-ft"}, plain_badge(r["st"], bool(m and m.get("low"))),
             [[" ", x] for x in links])
    if r["kind"] == "nc":
        reason = {"seat count not in data": "the seat count is not in the guide's data",
                  "votes missing": "a candidate's vote count is missing",
                  "no votes recorded": "no votes are recorded"}.get(m["reason"], m["reason"])
        names = ", ".join(x["name"] for x in candidates(c))
        return h("li", {"class": "mg-race mg-nc"},
                 h("p", {"class": "mg-rh"}, h("span", {"class": "mg-pts"}, "Not measurable"), " ",
                   h("span", {"class": "mg-when"}, _when(r) + seats)),
                 h("p", {"class": "mg-who"}, f"No margin: {reason}. Candidates: {names}."), earlier, foot)
    x = min(m["pts"], TICK_MAX) / TICK_MAX * 100
    return h("li", {"class": "mg-race"},
             h("p", {"class": "mg-rh"}, h("span", {"class": "mg-pts"}, _pts_text(m)), " ",
               h("span", {"class": "mg-band"}, KIND_LABEL[r["kind"]]), " ",
               h("span", {"class": "mg-when"}, _when(r) + seats)),
             h("span", {"class": "mg-tick", "style": f"--x: {x:.1f}%", "aria-hidden": "true"}),
             h("p", {"class": "mg-who"}, _who(m, bool(c.get("party_primary")))), earlier, foot)


def _unc_line(page, rs) -> Markup | None:
    if not rs:
        return None
    bits = []
    for r in sorted(rs, key=lambda r: r["e"]["date"], reverse=True):
        c = r["c"]
        named = [x for x in candidates(c) if not is_writein_total(x["row"])]
        who = (", ".join(cand_name(x, bool(c.get("party_primary"))) for x in named) if 0 < len(named) <= 2 else
               f"{len(named)} candidates for {c['vote_for']} seats" if named else "no candidate named")
        href = contest_href(page, c["contest_id"])
        when = _when(r)
        bits.append(h("li", None, h("a", {"href": href}, when) if href else when, f": {who}"))
    return h("div", {"class": "mg-unc"}, h("p", {"class": "mg-unc-h"}, f"Uncontested ({len(rs)})"),
             h("ul", {"class": "mg-unc-list"}, bits))


def _here_margin_areas(page, ed) -> list:
    """Saved place (added 2026-11-09, preselect "one"): open the reader's areas. Every place gets the countywide
    offices, plus its commissioner and council district folds where the guide's precinct results show a single one
    (civic/preselect.py county_districts, as on the county page); the page script adds the reader's city or town, and
    the township and school corporation when the reader chose them (data-here-also). "union-north" is the saved-place id
    of LaVille's schools, whose races sit under both of its names here."""
    votes = load_votes(ed)
    dist = county_districts(ed, votes)
    places = {}
    for pid in page.site.here_data.get("places", {}):
        keys = ["countywide"]
        for k in dist.get(pid, {}).get("keys", []):
            if k.startswith("county-commissioner-d"):
                keys.append("commissioner-" + k.rsplit("-d", 1)[1])
            elif k.startswith("county-council-"):
                keys.append("council-" + k.rsplit("-", 1)[1])
        places[pid] = {"keys": keys, "names": []}
    return [here_slot("one", "areas", extra={
                "data-here-keys": "json:here-margin-areas", "data-here-also": "muni township school",
                "data-here-undo": "Close them", "data-here-apply": "Open them",
                "data-here-why": " Your saved place's areas (kept on this device only): its city or town, the township "
                                 "and school corporation if you chose them, the countywide offices, and its county "
                                 "districts where the guide's precinct results show a single one."}),
            json_script("here-margin-areas", {"places": places, "alias": {"union-north": ["union-north", "laville-schools"]}})]


def _area_body(page, ed, key, rs, on_map, lines_from, g_ix, p_ix):
    """One area's races, by seat (in office order), each seat's races newest first. Returns (markup, seats)."""
    seats: dict[str, list] = {}
    for r in rs:
        seats.setdefault(r["seat"], []).append(r)
    office_order = {o["office_id"]: i for i, o in enumerate(ed.tables["offices"])}
    order = sorted(seats, key=lambda s: (office_order.get(s, len(office_order)), seat_name_of(seats[s])))
    lines_year = _lines_year(key, lines_from)
    blocks = []
    for s in order:
        srs = sorted(seats[s], key=lambda r: (r["e"]["date"], r["c"]["contest_id"]), reverse=True)
        cnt = _counts(srs)
        top = srs[0]
        words = {_search_text(r["c"]["label"]) for r in srs}
        names = {x["name"] for r in srs for x in candidates(r["c"])}
        n_seat = max(((r["m"] or {}).get("seats") or 0) for r in srs) or None
        rows = [_race_row(page, r, on_map, lines_year) for r in srs if r["kind"] != "unc"]
        close = _closest(srs)
        summary = [f"{_contested(cnt)} contested", f"{cnt['unc']} uncontested"]
        if close:
            summary.append(f"closest {close['m']['pts']:.2f} points ({close['e']['date'][:4]})")
        blocks.append(h("div", {"class": "mg-seat", "data-tf-row": True, "data-tf-office": g_ix[top["g"]],
                                "data-tf-place": p_ix[top["place"]], "data-tf-district": top["district"],
                                "data-tf-text": " ".join(sorted(words) + sorted(names))},
                        h("h5", {"class": "mg-seat-h"}, seat_name_of(srs),
                          h("span", {"class": "mg-seat-n"}, f" · {n_seat} seats") if n_seat and n_seat > 1 else None),
                        h("p", {"class": "mg-seat-sum"}, " · ".join(summary)),
                        h("ol", {"class": "mg-races"}, rows) if rows else None,
                        _unc_line(page, [r for r in srs if r["kind"] == "unc"])))
    return h("div", {"class": "mg-seats"}, blocks), len(blocks)


def seat_name_of(srs) -> str:
    """The seat's name as the newest race printed it."""
    return max(srs, key=lambda r: r["e"]["date"])["seat_name"]


# ---- the map

FIND_LAYERS = [  # (tab, label, source): map_shapes.json layer or district_shapes.json sets
    ("township", "Townships", ("map", "township")),
    ("place", "Cities and towns", ("map", "place")),
    ("school", "School corporations", ("map", "school")),
    ("commissioner", "Commissioner districts", ("set", ("county-commissioner-2022",))),
    ("council", "County council districts", ("set", ("county-council-2022",))),
    ("city-council", "City council districts", ("set", ("south-bend-council-2022", "mishawaka-council-2022"))),
    ("house", "Indiana House", ("set", ("in-house-2021",))),
    ("senate", "Indiana Senate", ("set", ("in-senate-2021",))),
]
SET_KEY = {"county-commissioner-2022": lambda d: f"commissioner-{d.lower()}",
           "county-council-2022": lambda d: f"council-{d.lower()}",
           "south-bend-council-2022": lambda d: f"south-bend-council-{d.lower()}",
           "mishawaka-council-2022": lambda d: f"mishawaka-council-{d.lower()}",
           "in-house-2021": lambda d: f"house-{d.lstrip('HD')}",
           "in-senate-2021": lambda d: f"senate-{d.lstrip('SD')}"}


def _shape_items(ed, shapes, dshapes, src):
    """[(area key, shape item, set record or None)] for one map layer."""
    kind, what = src
    if kind == "map":
        return [(it["id"], it, None) for it in (shapes or {}).get("layers", {}).get(what, []) if it.get("id")]
    out = []
    for set_id in what:
        rec = district_set(dshapes, set_id)
        for it in (rec or {}).get("items", []):
            out.append((SET_KEY[set_id](it["district"]), it, rec))
    return out


def _has_shape(key, shapes, dshapes) -> bool:
    return any(k == key for _, _, src in FIND_LAYERS for k, _, _ in _shape_items(None, shapes, dshapes, src))


def _find_map(page, ed, shapes, dshapes, by_area, lines_from):
    if not shapes:
        return None
    layers = []
    for tab, label, src in FIND_LAYERS:
        items, none = [], []
        recs = []
        for key, it, rec in _shape_items(ed, shapes, dshapes, src):
            if rec is not None and rec not in recs:
                recs.append(rec)
            rs = by_area.get(key)
            if not rs:
                none.append(area_name(ed, key))
                continue
            name = area_name(ed, key, rs[0]["place"])
            cnt = _counts(rs)
            facts = [["Contested races", f"{_contested(cnt)} since {min(r['e']['date'][:4] for r in rs)}"],
                     ["Under 5 points", str(cnt["under-5"])], ["5 to 15 points", str(cnt["5-15"])],
                     ["Over 15 points", str(cnt["over-15"])], ["Uncontested", str(cnt["unc"])]]
            if cnt["nc"]:
                facts.append(["Not measurable", str(cnt["nc"])])
            close = _closest(rs)
            if close:
                facts.append(["Closest", f"{close['seat_name']}, {_election_short(close['e'])}: {_pts_text(close['m'])}"])
            cav = []
            ly = _lines_year(key, lines_from)
            if ly:
                cav.append(f"The lines drawn are the ones used from {ly}. Races before {ly} were held under earlier lines, "
                           "so they are listed under this district's number but covered a different area.")
            href = f"#area-{key}"
            text = it.get("district") if rec is not None else (name.replace(" Township", "") if tab == "township" else None)
            if tab == "city-council":
                text = it["district"]
            items.append({"uid": f"mg-{key}", "district": key, "d": it["d"], "href": href,
                          "aria": f"{name}: {_digest(cnt)}. Show these races.",
                          "entry": {"n": name, "t": label, "f": facts, "cav": cav, "note": "", "href": href,
                                    "open": "Show these races"},
                          "text": (text or "").lstrip("HDS") if rec is not None and tab in ("house", "senate") else text,
                          "label": it.get("label") if text else None, "label_r": it.get("label_r", 99)})
        if not items:
            continue
        leg = [h("p", None, "No races in the guide's data: " + ", ".join(none) + ".") if none else None]
        for rec in recs:
            leg.append(h("p", None, f"District lines used from {rec.get('first_election', 'a year not recorded')}.",
                         page.cites.cite_compact(rec.get("source_ids", ""))))
        layers.append({"tab": tab, "label": label, "items": items, "legend": leg})
    if not layers:
        return None
    return district_map(page, ed, shapes, layers, layers[0]["tab"],
                        label="Map of the areas whose races the county's voters decided: townships, cities and towns, "
                              "school corporations, and county, city council and legislative districts. Every area is a "
                              "link to its races below.",
                        hint="Hover, focus or tap an area to see how close its races were. Select it again, or use the "
                             "link, to show its races below.",
                        notes=h("div", {"class": "dmap-notes"},
                                h("p", None, "The map is not shaded by party or by margin. Pick a layer for the kind of "
                                             "office: township races are on Townships, school boards on School "
                                             "corporations, and so on.")))


# =========================================================================== turnout

def _turnout_section(page, ed, els):
    cites = page.cites
    g_chart = _turnout_chart(page, ed, ("general", "municipal_general"), "turnout-general",
                             "Turnout in general elections", cites.cite_compact(_src(*[e for e in els if "general" in e["type"]])))
    p_chart = _turnout_chart(page, ed, ("primary", "municipal_primary", "special"), "turnout-primary",
                             "Turnout in primaries and special elections",
                             cites.cite_compact(_src(*[e for e in els if "general" not in e["type"]])))
    den_rows = []
    for e in els:
        den_rows.append([_election_name(e), "Special (one area)" if e["type"] == "special" else
                         "Odd-year municipal" if e["type"] in MUNICIPAL_TYPES else "Countywide",
                         e["scope"], fmt_int(e["registered"]) or "not printed", fmt_int(e["ballots_cast"]) or "not printed",
                         f"{float(e['turnout_pct']):.2f}%" if e.get("turnout_pct") else "not printed",
                         h("span", None, status_badge(e["status"], page), cites.cite(e["source_ids"]))])
    ev = [e for e in els if e["type"] == "general"]
    mu = [e for e in els if e["type"] == "municipal_general"]
    return section("turnout", 1, "Turnout: odd vs even years",
                   h("p", None, "Turnout is ballots cast divided by registered voters. In odd years only city and town "
                                "residents vote, so the base is smaller: about "
                                f"{fmt_int(min(int(e['registered']) for e in mu if e['registered']))} to "
                                f"{fmt_int(max(int(e['registered']) for e in mu if e['registered']))} registered voters in the "
                                "municipal generals, compared with about "
                                f"{fmt_int(min(int(e['registered']) for e in ev if e['registered']))} to "
                                f"{fmt_int(max(int(e['registered']) for e in ev if e['registered']))} countywide.",
                     cites.cite_compact(_src(*(ev + mu))), " ", status_badge("computed", page, "Ranges from elections.csv.")),
                   h("div", {"class": "chart-grid elx-charts"}, g_chart, p_chart),
                   see_all_table("turnout-denominators", ["Election", "Kind", "Who could vote", "Registered", "Ballots cast",
                                                          "Turnout", "Status"], den_rows, noun="election",
                                 caption="Turnout with its denominator", numeric=(3, 4, 5), min_width="50rem",
                                 summary=f"See all {len(den_rows)} elections: turnout with its denominator"),
                   scope="county", ed=ed)


def straight_elections(ed, els) -> list[dict]:
    """General elections whose straight-party share is shown: printed by the county, in a year with a sourced rule."""
    sourced = _straight_party_years(ed)
    # the share needs the ballots cast as its base: a blank or zero count is left out (it crashed the page; debug pass
    # 2026-11-09)
    return [e for e in els if e["type"] == "general" and e.get("straight_party_d") and int(e["date"][:4]) in sourced
            and (e.get("ballots_cast") or "").strip().isdigit() and int(e["ballots_cast"]) > 0]


def _straight_section(page, ed, els):
    cites = page.cites
    sourced = _straight_party_years(ed)
    blocks = []
    for e in straight_elections(ed, els):
        bal = int(e["ballots_cast"])
        d, r, o = (int(e[k] or 0) for k in ("straight_party_d", "straight_party_r", "straight_party_other"))
        tot = d + r + o
        blocks.append(h("div", None,
                        h("p", None, f"In the {_election_name(e)}, {tot:,} of {bal:,} ballots ({100 * tot / bal:.1f}%) used a "
                                     "straight-party mark.", cites.cite(e["source_ids"]), " ", status_badge(e["status"], page), " ",
                          status_badge("computed", page, "Straight-party ballots divided by ballots cast.")),
                        data_table(f"straight-{e['election_id']}", ["Straight-party mark", "Ballots", "Share of all ballots"],
                                   [[party_label("D"), f"{d:,}", f"{100 * d / bal:.1f}%"],
                                    [party_label("R"), f"{r:,}", f"{100 * r / bal:.1f}%"],
                                    ["Other parties", f"{o:,}", f"{100 * o / bal:.1f}%"]],
                                   caption=f"Straight-party ballots, {e['date'][:4]}", numeric=(1, 2))))
    printed = sorted({e["date"][:4] for e in els if e["type"] == "general" and e.get("straight_party_d")
                      and int(e["date"][:4]) not in sourced})
    return section("straight-party", 2, "Straight-party ballots",
                   h("p", None, "A share is shown only for years where the guide has a sourced rule for what a straight-party "
                                "mark covered. ", f"Years with a sourced rule: {', '.join(map(str, sorted(sourced))) or 'none'}. ",
                     "The rule in force through 2026 comes from the statute text read in 2026; the year it began is low "
                     "confidence, so earlier years are not shown even though the county printed their totals. ",
                     h("a", {"href": page.rel("elections/how-it-works/index.html#general")}, "The straight-party rules")),
                   blocks,
                   h("p", {"class": "muted"},
                     "The county also printed straight-party totals for the general elections of " + ", ".join(printed) +
                     ". They are in the guide's data files and will be shown here once the rule for those years is sourced.")
                   if printed else None,
                   scope="county", ed=ed)


def build_turnout(site):
    ed = site.ed
    page = site.page("elections/turnout/index.html", banners=True)
    els = _elections(ed)
    toc = [("turnout", "Turnout: odd vs even years"), ("straight-party", "Straight-party ballots"),
           ("rules", "What this page does not do"), ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(_hero(page, "Reference · Elections · By the numbers",
                   f"Turnout in every election in the guide's data from {els[0]['date'][:4]} to {els[-1]['date'][:4]}, "
                   "always with the number of registered voters it is measured against, and how many ballots used a "
                   "straight-party mark.", ["county"], toc))
    page.add(_turnout_section(page, ed, els))
    page.add(_straight_section(page, ed, els))
    page.add(_rules_section(page, ["forecast", "party", "votes-map"]))
    page.finish(gaps=[g for g in _gaps(ed, "elections-landscape") if re.search(r"straight", g.get("item", ""), re.I)]
                + _gaps(ed, None, ["gaps_results"], r"turnout|registered|status of the election row"))
    return page


# =========================================================================== officeholders

def _current_holders(ed):
    cur = []
    for o in ed.tables["offices"]:
        if o.get("elected") != "yes":
            continue
        for t in _holders_now(ed, o["office_id"]):
            cur.append((o, t))
    cur.sort(key=lambda x: (_place_order(ed, x[0]), x[0]["office_id"]))
    return cur


TOOK_ORDER = ["election", "caucus", "appointment", "unknown"]


def _took_chart(page, ed, cur, fid):
    cnt: dict[str, int] = {}
    for _, t in cur:
        k = t.get("first_selected_by") or "unknown"
        cnt[k] = cnt.get(k, 0) + 1
    return hbar(fid, "How current officeholders first took office",
                [{"label": SELECTED_BY_LABELS[k].capitalize(), "value": cnt.get(k, 0), "display": f"{cnt.get(k, 0)} people"}
                 for k in TOOK_ORDER],
                subtitle=f"{len(cur)} people holding elected offices in the guide's data on {fmt_date(ed.as_of)}",
                headers=["How first chosen", "People"], status="computed", page=page,
                note="Counted from the first_selected_by field of each current term. 'Not stated in sources' means the "
                     "sources don't say how the person first took the office."), cnt


def office_card_href(page, ed, o) -> str | None:
    """The officeholder card of an office on its government's page (the card ids are office-<office id>)."""
    u = ed.units.get(o["unit_id"], {})
    ut = u.get("unit_type")
    if ut in ("city", "town", "township"):
        path = f"places/{o['unit_id']}/index.html"
    elif o["unit_id"] in ("county", "sjc-courts"):
        path = "county/index.html"
    elif ut == "school_corporation":
        path = "schools/index.html"
    elif o["unit_id"] in ("in-house", "in-senate"):
        path = "state/your-legislators/index.html"
    else:
        return None
    if path not in page.site.by_path:
        return None
    return page.rel(f"{path}#office-{o['office_id']}")


def _money_line(page, ed, o, t):
    """Links to the holder's own campaign committees' money history (added 2026-11-09), when any match by name in the
    office's government (cf_local.csv); for state legislators, their history on the state legislature campaigns page
    (cf_state.csv and cf_state_history.csv)."""
    from pages.money_history import holder_links, legislator_href
    if o["unit_id"] in ("in-house", "in-senate"):
        u = legislator_href(ed, page, t["person"])
        return h("p", {"class": "oh-money"}, h("a", {"href": u}, "Campaign money history (state filings)")) if u else None
    got = holder_links(ed, page, o["unit_id"], t["person"], o["title"])
    if not got:
        return None
    parts = []
    for i, (label, u) in enumerate(got):
        parts += ([", "] if i else []) + [h("a", {"href": u}, label)]
    return h("p", {"class": "oh-money"}, "Campaign money history: ", parts)


def build_officeholders(site):
    ed = site.ed
    page = site.page("officeholders/index.html", banners=True)
    cites = page.cites
    cur = _current_holders(ed)
    toc = [("how-took-office", "How they first took office"), ("every", "Every officeholder, by government"),
           ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(_hero(page, "Reference · Your governments",
                   f"Every person holding an elected office in the county in the guide's data on "
                   f"{fmt_date(ed.as_of, long=True)}, by government, and how each first took the office: by election, "
                   "by party caucus or by appointment.", ["county"], toc))
    chart, cnt = _took_chart(page, ed, cur, "took-office")
    n_cau, n_app = cnt.get("caucus", 0), cnt.get("appointment", 0)
    page.add(section("how-took-office", 1, "How they first took office",
                     h("p", None, "Every current officeholder, by office, with how they first took the office (election, party "
                                  "caucus or appointment) and how they got their current term. The same field is shown for "
                                  "everyone."),
                     chart,
                     h("p", None, f"{n_cau} of the {len(cur)} first took the office through a party caucus and {n_app} by "
                                  "appointment. ", status_badge("computed", page, "Counted from terms.csv first_selected_by.")),
                     h("h3", None, "Why this matters"),
                     _rule_p(page, ed, "local_vacancy_caucus"),
                     h("p", None, h("a", {"href": page.rel("elections/how-it-works/index.html#vacancies")}, "How vacancies are filled")),
                     scope="county", ed=ed))

    # ---- every officeholder: one fold per government, rows filtered by level, government and how
    by_gov: dict[str, list] = {}
    for o, t in cur:
        by_gov.setdefault(o["unit_id"], []).append((o, t))
    hrows, hattrs = [], []
    folds = []
    for uid in sorted(by_gov, key=lambda u: _place_order(ed, by_gov[u][0][0])):
        lis = []
        n_c = 0
        for o, t in by_gov[uid]:
            k = t.get("first_selected_by") or "unknown"
            how = SELECTED_BY_LABELS.get(k, k)
            now = SELECTED_BY_LABELS.get(t.get("selected_by") or "unknown", t.get("selected_by"))
            n_c += k in ("caucus", "appointment")
            a = {**_unit_attrs(ed, o), "data-tf-how": how, "data-tf-text": f"{o['title']} {t['person']}"}
            hattrs.append(a)
            badges = h("span", None, plain_badge(t["status"], t.get("confidence") == "low"),
                       cites.cite_compact(t["source_ids"]))
            since = fmt_date(t["start"]) or "not in sources"
            hrows.append([o["title"], t["person"], _plabel(t.get("party")), how, now, since, badges])
            card = office_card_href(page, ed, o)
            lis.append(h("li", {**a, **here_attrs(ed, o["unit_id"]), "class": "oh-row", "data-tf-row": True},
                         h("p", {"class": "oh-office"}, h("a", {"href": card}, o["title"]) if card else o["title"]),
                         h("p", {"class": "oh-who"}, h("strong", None, t["person"]), f" · {_plabel(t.get('party'))}",
                           f" · since {since}"),
                         h("p", {"class": "oh-how"}, first_by_text(t)[0].upper() + first_by_text(t)[1:],
                           f"; current term by {now}. ", badges),
                         _money_line(page, ed, o, t)))
        name = ed.units.get(uid, {}).get("name", uid)
        digest = f"{len(lis)} officeholder{'s' if len(lis) != 1 else ''}" + (f" · {n_c} first by caucus or appointment" if n_c else "")
        folds.append(h("li", {"class": "oh-gov", "data-tf-group": True},
                       one_fold(uid, name, [h("h3", {"class": "one-h"}, name), h("span", {"class": "one-digest"}, digest)],
                                h("ul", {"class": "oh-rows"}, lis), item_id=f"gov-{uid}")))
    how_opts = _opts([SELECTED_BY_LABELS.get(k, k) for k in TOOK_ORDER if cnt.get(k)])
    page.add(section("every", 2, "Every officeholder, by government",
                     h("p", None, "Governments in the guide's order (county, courts, townships, cities, towns, school boards, "
                                  "legislature); inside each, offices in office order, never by party. Each office links to "
                                  "its card on the government's page."),
                     table_filter("oh-list", _unit_controls(ed, [o for o, _ in cur])
                                  + [{"key": "how", "label": "First took office by", "all": "Any way", "options": how_opts}],
                                  len(cur), noun="officeholder", search="Office or holder name",
                                  label="Filter the officeholders"),
                     badge_key(page),
                     here_slot("filter", "oh-list", extra={"data-here-noun": "officeholders"}),
                     filter_empty_note("oh-list"),
                     one_bar("government", "governments", "Open a government to see its officeholders."),
                     h("ul", {"class": "oh-list one-list", "id": "oh-list", "data-tf-deep": True}, folds),
                     see_all_table("took-office-list", ["Office", "Holder", "Party", "First took office by", "Current term by",
                                                        "Since", "Status"], hrows,
                                   noun="officeholder", caption="Current officeholders and how they took office",
                                   min_width="52rem", row_attrs=hattrs,
                                   controls=_unit_controls(ed, [o for o, _ in cur])
                                   + [{"key": "how", "label": "First took office by", "all": "Any way", "options": how_opts}],
                                   search="Office or holder name", filter_label="Filter the officeholders table"),
                     scope="county", ed=ed))
    page.finish(gaps=ed.gaps(areas=["terms"]))
    return page


# =========================================================================== overview (elections/landscape/)

RULES = {
    "forecast": ("No forecasts and no labels about future races. Everything here describes past results and current rules.",),
    "party": ("No party filter. Every view covers every party the same way.",),
    "colors": ("Charts never use party colors: uncontested races are in ink, the margin bands in the accent color.",),
    "votes-map": None,   # built per page (links)
}


def _rules_section(page, keys, num=None):
    ed = page.ed
    items = []
    for k in keys:
        if k == "votes-map":
            items.append(_votes_map_item(page, ed))
        else:
            items.append(h("li", None, RULES[k][0]))
    return section("rules", num, "What this page does not do", h("ul", None, items))


def _votes_map_item(page, ed):
    """B5 (review §0): precinct results are on the map's "How areas voted" layer; say which years, from its data."""
    votes = load_votes(ed)
    years = sorted({r["year"] for r in (votes or {}).get("races", [])}) if votes else []
    if years:
        yrs = ", ".join(str(y) for y in years[:-1]) + (f" and {years[-1]}" if len(years) > 1 else str(years[0]))
        return h("li", None, "No voter-file data or donor details. Precinct results for the ", yrs, " general elections "
                             "are on the map, in its ",
                 h("a", {"href": page.rel("map/index.html#list-votes")}, "How areas voted"), " layer; precinct files "
                 "are linked on ", h("a", {"href": page.rel("data/index.html")}, "Data and sources"), ".")
    return h("li", None, "No precinct maps, voter-file data or donor details. Precinct files are linked on ",
             h("a", {"href": page.rel("data/index.html")}, "Data and sources"), ".")


def _card_links(*links):
    return h("ul", {"class": "ov-links"}, [h("li", None, h("a", {"href": href}, text)) for href, text in links])


LANDSCAPE_MOVED = {  # old elections/landscape/ id -> its new home (site-root path#id)
    "bands": "elections/margins/index.html#bands",
    "margin-bands": "elections/margins/index.html#margin-bands",
    "margin-bands-details": "elections/margins/index.html#margin-bands-details",
    "margin-bands-table": "elections/margins/index.html#margin-bands-table",
    "margin-bands-table-copy": "elections/margins/index.html#margin-bands-table-copy",
    "margins-table": "elections/margins/index.html#margins-table",
    "margins-table-copy": "elections/margins/index.html#margins-table-copy",
    **{f"tf-margins-table-{k}": f"elections/margins/index.html#tf-margins-table-{k}"
       for k in ("year", "type", "band", "office", "place", "district", "q", "sort")},
    "turnout-denominators": "elections/turnout/index.html#turnout-denominators",
    "turnout-denominators-copy": "elections/turnout/index.html#turnout-denominators-copy",
    **{f"turnout-{k}{s}": f"elections/turnout/index.html#turnout-{k}{s}"
       for k in ("general", "primary") for s in ("", "-details", "-table", "-table-copy")},
    "straight-party": "elections/turnout/index.html#straight-party",
    "straight-party-h": "elections/turnout/index.html#straight-party-h",
    "up-next-table": "elections/calendar/index.html#up-next-table",
    "up-next-table-copy": "elections/calendar/index.html#up-next-table-copy",
    **{f"tf-up-next-table-{k}": f"elections/calendar/index.html#tf-up-next-table-{k}"
       for k in ("year", "level", "government", "q")},
    "took-office": "officeholders/index.html#took-office",
    "took-office-details": "officeholders/index.html#took-office-details",
    "took-office-table": "officeholders/index.html#took-office-table",
    "took-office-table-copy": "officeholders/index.html#took-office-table-copy",
    "took-office-list": "officeholders/index.html#took-office-list",
    "took-office-list-copy": "officeholders/index.html#took-office-list-copy",
    **{f"tf-took-office-list-{k}": f"officeholders/index.html#tf-took-office-list-{k}"
       for k in ("level", "government", "how", "q")},
}


def build_landscape(site):
    ed = site.ed
    page = site.page("elections/landscape/index.html", banners=True)
    cites = page.cites
    els = _elections(ed)
    span = f"{els[0]['date'][:4]} to {els[-1]['date'][:4]}"
    toc = [("turnout", "Turnout"), ("margins", "How close were the races?"), ("up-next", "Up next"),
           ("how-took-office", "How officeholders first took office"), ("rules", "What this page does not do"),
           ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(_hero(page, "Reference · Elections · By the numbers",
                   "Four measures, the same for every race and every party, looking back only: turnout with its base, how "
                   "close each race was, the seats on the next ballots, and how today's officeholders first took office. "
                   "Each card leads to the full page.", ["county"], toc))

    # ---- turnout card
    gen = [e for e in els if e["type"] == "general" and e.get("turnout_pct")]
    mun = [e for e in els if e["type"] == "municipal_general" and e.get("turnout_pct")]
    rng = lambda es: f"{min(float(e['turnout_pct']) for e in es):.0f}% to {max(float(e['turnout_pct']) for e in es):.0f}%"
    t_chart = _turnout_chart(page, ed, ("general", "municipal_general"), "ov-turnout", "Turnout in general elections",
                             cites.cite_compact(_src(*[e for e in els if "general" in e["type"]])))
    turnout = section("turnout", None, "Turnout",
                      h("p", None, f"Even-year general elections, countywide: {rng(gen)} of registered voters. Odd-year "
                                   f"municipal generals, where only city and town voters vote: {rng(mun)}. ",
                        status_badge("computed", page, "Ranges from elections.csv turnout_pct."),
                        cites.cite_compact(_src(*(gen + mun)))) if gen and mun else None,
                      t_chart,
                      _card_links((page.rel("elections/turnout/index.html"), "Turnout with its denominator, and straight-party ballots")))

    # ---- margins card
    races = margin_races(ed)
    counts = _counts(races)
    close = _closest(races)
    src_votes = _src(*[r["c"]["rows"][0] for r in races])
    close_p = None
    if close:
        href = contest_href(page, close["c"]["contest_id"])
        what = f"{close['c']['label']}, {_election_short(close['e'])}"
        close_p = h("p", None, "Closest: ", h("a", {"href": href}, what) if href else what, f", {_pts_text(close['m'])}. ",
                    status_badge("computed", page))
    margins = section("margins", None, "How close were the races?",
                      h("p", None, f"{counts['unc']:,} of the {len(races):,} races for local office decided inside the county "
                                   f"from {span} had no contest: no more candidates than seats. ",
                        status_badge("computed", page, "Counted from results.csv vote counts and seat counts."),
                        cites.cite_compact(src_votes)),
                      share_bars("ov-margins", "Races by margin", [{"label": f"All races, {span}", "counts": counts}],
                                 [{"key": k, "label": lab, "mark": mk} for k, lab, mk in KINDS], noun=("race", "races"),
                                 ramp="alt", page=page, group_header="Races"),
                      close_p,
                      _card_links((page.rel("elections/margins/index.html"), "Margins: how close each race was"),
                                  (page.rel("elections/margins/index.html#find"), "Find a race on the map")))

    # ---- up next card
    items, _ = _calendar_items(ed)
    rows = []
    for y in YEARS:
        local = [i for i in items[y] if i["office"]]
        known = sum(i["seats"] or 0 for i in local)
        unk = sum(1 for i in local if not i["seats"])
        rows.append({"label": str(y), "value": known,
                     "display": f"{known} seats" + (f" + {unk} with no seat count" if unk else "")})
    up_next = section("up-next", None, "Up next",
                      h("p", None, "Odd years elect city and town offices only; even years elect county, township, school-board "
                                   "and legislative seats. The years come from each office's next election and term length.",
                        " ", status_badge("computed", page, "From offices.csv next_election and term_years."),
                        cites.cite(_src(ed.rules.get("municipal_cycle", {}), ed.rules.get("even_year_offices", {})))),
                      hbar("ov-seats", "Local seats on each year's ballot", rows, subtitle=f"{YEARS[0]} to {YEARS[-1]}",
                           headers=["Year", "Seats"], status="computed", page=page),
                      _card_links((page.rel("elections/calendar/index.html#year-2027"), "Up next: 2027 and 2028 seats, who holds them and term limits"),
                                  (page.rel("elections/calendar/index.html#by-year"), "Every seat, by year")))

    # ---- officeholders card
    cur = _current_holders(ed)
    chart, cnt = _took_chart(page, ed, cur, "ov-took-office")
    took = section("how-took-office", None, "How officeholders first took office",
                   h("p", None, f"{cnt.get('caucus', 0)} of the {len(cur)} people holding elected offices first took the office "
                                f"through a party caucus and {cnt.get('appointment', 0)} by appointment, not by election. ",
                     status_badge("computed", page, "Counted from terms.csv first_selected_by.")),
                   chart,
                   _card_links((page.rel("officeholders/index.html"), "Who holds office now: every officeholder"),
                               (page.rel("elections/how-it-works/index.html#vacancies"), "How vacancies are filled")))
    page.add(h("div", {"class": "ov-grid"}, turnout, margins, up_next, took))
    page.add(_rules_section(page, ["forecast", "party", "votes-map"]))
    straight = {f"straight-{e['election_id']}{x}": f"elections/turnout/index.html#straight-{e['election_id']}{x}"
                for e in straight_elections(ed, els) for x in ("", "-copy")}
    page.add(moved_anchors(page, {**LANDSCAPE_MOVED, **straight}))
    page.finish(gaps=_gaps(ed, "elections-landscape", ["gaps_results"], r"winner|seat count|multi-seat|2026 general"))
    return page


PAGES = {
    "elections/landscape/index.html": build_landscape,
    "elections/margins/index.html": build_margins,
    "elections/turnout/index.html": build_turnout,
    "officeholders/index.html": build_officeholders,
}
