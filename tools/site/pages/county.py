"""County government reference page (county/index.html)."""
from __future__ import annotations

import re
from datetime import date

from civic.charts import party_timeline, results_bars
from civic.components import (as_of_note, body_state, body_with_breakdown, bodies_block, callout, data_table, name_party_text,
                              party_label, scope_badge, section, see_all_fold, status_badge, variant_slot)
from civic.data import fmt_date, parse_date, split_ids
from civic.answers import answer_box
from civic.related import RelatedLink, contest_href, latest_contest, related_items, related_rail
from civic.html import Markup, h, join, json_script
from civic.layers import county_scope_boards
from civic.spending import has_money_in_out, money_in_out
from civic.tax_base import tax_base_line
from civic.district_map import district_map, district_set, load_district_shapes
from civic.holder_rows import holder_row, holder_state
from civic.map import load_shapes, load_votes
from civic.preselect import COUNTY_DISTRICT_OFFICES, county_districts, here_slot
from civic.pick_one import one_bar, one_fold, one_summary

ROW_TYPES = ("county_auditor", "county_treasurer", "county_recorder", "county_clerk", "county_sheriff",
             "county_coroner", "county_surveyor", "county_assessor", "county_prosecutor")

GAP_PATTERN = (r"County Council|commissioner|Superior Court|opted in|IC 36-2|Election Board|Area Plan|"
               r"Redevelopment Authority|Tax Adjustment|Board of Appeals|Airport|Board of Health|county party control|"
               r"2026 general: official canvass|2024 general: OCR|office labels for recorder|row offic|Probate|Circuit")


def _union_sources(rows) -> str:
    seen = []
    for r in rows:
        for s in split_ids(r.get("source_ids")):
            if s not in seen:
                seen.append(s)
    return ";".join(seen)


_ABBREV = re.compile(r"(?:\b(?:St|Mt|Ft|No|Nos|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|Ind|Dr|Mr|Mrs|Ms|Jr|Sr|Inc|Co|vs|v|al|art|sec)|(?<![A-Za-z])[A-Z]|\b(?:[A-Z]\.)+[A-Z])\.$")


def _sentences(text: str) -> list[str]:
    """Split prose into sentences at '. ' followed by a capital or digit, but not after common
    abbreviations ('St. Joseph', 'Apr. 21', 'U.S.') or initials."""
    out: list[str] = []
    for piece in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(\"'])", (text or "").strip()):
        if out and _ABBREV.search(out[-1]):
            out[-1] += " " + piece
        elif piece:
            out.append(piece)
    return out


def _sentences_matching(text: str, pattern: str) -> str:
    return " ".join(p for p in _sentences(text) if re.search(pattern, p))


# A term row's `confidence` covers the whole row: dates, how the holder took office, and party.
# The party-control charts need to know which of those is uncertain. Low confidence hides a
# seat's party only when the note says the party itself, or whether this person holds the seat
# at all, is not documented. Low confidence about dates or selection method keeps the party and
# marks the affected years instead (see control_by_year).
_PARTY_UNSURE = re.compile(r"party (?:presumed|unconfirmed|unverified|unknown|not (?:found|confirmed|sourced|documented|stated))"
                           r"|start and party not found", re.I)
_HOLDING_UNSURE = re.compile(r"wins only if|if two (?:or more )?seats|if three seats|seat count not printed", re.I)

CONTROL_METHOD = ("Each row shows the party label of the person holding each seat on January 2 of that year, from the "
                  "guide's terms data. Seats with no holder in the data are shown as 'no data'. A seat is left without a "
                  "party ('not shown') only when its holder's party, or whether that person holds the seat, is not "
                  "documented. Years marked † include a holder whose start or end date is uncertain in the sources; "
                  "the party shown is documented, but the exact year of a change may differ. Rows marked * use terms "
                  "that start after the 2026 election, whose results are unofficial.")


def sid_for_url(ed, fragment: str) -> str:
    """Source id whose URL contains `fragment`, or '' (lets a module cite a source row the main
    session adds later without hard-coding an id)."""
    for sid, r in ed.sources.items():
        if fragment and fragment in (r.get("url") or ""):
            return sid
    return ""


_PARTY_PLURAL = {"D": "Democrats", "R": "Republicans", "L": "Libertarians", "G": "Greens"}


def ballot_order_note(ed, page, election_ids=None):
    """One line explaining candidate order in results tables (neutrality review N4). IC 3-11-2-6(a):
    parties are placed in order of their candidates' county vote for Secretary of State at the last
    election. With `election_ids`, also names the Secretary of State result that set the order for
    those ballots (computed from results.csv)."""
    c = page.cites
    parts = [h("span", None, "Indiana places parties on the county ballot in order of each party's county vote for Secretary of "
                             "State at the last election", c.cite(sid_for_url(ed, "in-code-sect-3-11-2-6") or "IND-056"),
               "; the county's reports follow that order, and the guide keeps it. ")]
    sos = sorted((x for x in ed.contests.values() if x["contest_id"].endswith("-state-secretary-of-state")
                  and not x["party_primary"]), key=lambda x: ed.elections[x["election_id"]]["date"])
    groups: dict[str, list[str]] = {}
    for eid in election_ids or []:
        d = ed.elections[eid]["date"]
        prior = [x for x in sos if ed.elections[x["election_id"]]["date"] < d]
        if prior:
            groups.setdefault(prior[-1]["contest_id"], []).append(d[:4])
    for cid, yrs in groups.items():
        x = ed.contests[cid]
        rows = sorted((r for r in x["rows"] if r["party"] in _PARTY_PLURAL and r["votes"]), key=lambda r: -float(r["votes"]))[:2]
        if len(rows) < 2:
            continue
        def nm(r):
            return r["candidate"].split()[-1] + f" ({r['party']})"
        y = ed.elections[x["election_id"]]["date"][:4]
        parts.append(h("span", None, f"On the {' and '.join(sorted(set(yrs)))} ballots {_PARTY_PLURAL[rows[0]['party']]} are listed "
                                     f"first: in {y}, {nm(rows[0])} received {int(float(rows[0]['votes'])):,} county votes for "
                                     f"Secretary of State and {nm(rows[1])} {int(float(rows[1]['votes'])):,}",
                       c.cite(";".join(dict.fromkeys(s for r in rows for s in split_ids(r["source_ids"])))), ". "))
    return h("span", None, parts)


def seat_code(t: dict) -> str:
    """Party code for a holder in the control charts, or 'low' when the party (or the holding itself)
    is not documented."""
    party = (t.get("party") or "").strip()
    if not party or party.lower() == "unknown":
        return "low"
    if t.get("confidence") == "low" and (_PARTY_UNSURE.search(t.get("notes", "")) or _HOLDING_UNSURE.search(t.get("notes", ""))):
        return "low"
    return party


def _date_uncertain_years(ed, t: dict) -> set[int]:
    """Years whose Jan-2 snapshot could change if a low-confidence term's dates were off:
    the year of its start or end and the year after (a change late in year Y shows on Jan 2 of Y+1)."""
    if t.get("confidence") != "low" or seat_code(t) == "low":
        return set()
    out = set()
    s, e = parse_date(t.get("start")), ed.term_end(t)
    for d in (s, e):
        if d:
            out |= {d.year, d.year + 1}
    return out


def control_by_year(ed, offices: list[dict]) -> list[dict]:
    """Seat holders' party on Jan 2 of each year, from the first year with a holder
    through the year after the data date when incoming terms exist.

    Each year: {year, label, seats, status, dates_uncertain}. `label` carries a † when a counted
    holder's dates are low confidence near that year (party still shown; see seat_code)."""
    starts = [parse_date(t["start"]) for o in offices for t in ed.terms_for(o["office_id"]) if parse_date(t["start"])]
    if not starts:
        return []
    first = min(starts).year
    last = ed.as_of.year + (1 if any(ed.incoming_terms(o["office_id"]) for o in offices) else 0)
    years = []
    for y in range(first, last + 1):
        on = date(y, 1, 2)
        seats, status, unsure = [], "", False
        for o in offices:
            n = int(o["seats"]) if o["seats"].isdigit() else 1
            holders = ed.terms_on(o["office_id"], on)
            if len(holders) > n:
                ed.warnings.append(f"control: {o['office_id']} has {len(holders)} holders on {on}; using latest start")
                holders = sorted(holders, key=lambda t: parse_date(t["start"]))[-n:]
            for t in holders:
                seats.append(seat_code(t))
                if y in _date_uncertain_years(ed, t):
                    unsure = True
                if t.get("status") == "unofficial":
                    status = "unofficial"
            seats += ["nodata"] * (n - len(holders))
        row = {"year": y, "seats": seats, "status": status, "dates_uncertain": unsure}
        if unsure:
            row["label"] = f"{y}†"
            if not status:
                row["status"] = "dates uncertain"
        years.append(row)
    return years


def build(site):
    ed = site.ed
    page = site.page("county/index.html", banners=True)
    cites = page.cites
    county = ed.county
    offices = ed.offices_for("county")
    court_offices = ed.offices_for("sjc-courts")
    comm = [o for o in offices if o["office_type"] == "county_commissioner"]
    council = [o for o in offices if o["office_type"] == "county_council_member"]
    row = [o for o in offices if o["office_type"] in ROW_TYPES]
    superior = [o for o in court_offices if o["office_type"] == "superior_court_judge"]
    other_courts = [o for o in court_offices if o["office_type"] != "superior_court_judge"]
    n_elected = len(comm) + len(council) + len(row) + len(court_offices)
    n_pros = sum(1 for o in row if o["office_type"] == "county_prosecutor")
    n_row_only = len(row) - n_pros

    # ------------------------------------------------------------------ hero
    toc = [("structure", "How it's organized"), ("officeholders", "Who holds office"), ("row-officers", "Row officers"),
           ("courts", "Courts"), ("boards", "Appointed boards"), ("control", "Party control over time"),
           ("results", "Recent results")] + ([("money", "Money in and out")] if has_money_in_out(ed, "county-st-joseph") else []) +           [("gaps", "Gaps"), ("sources", "Sources")]
    page.add(h("header", {"class": "page-hero"},
               h("p", {"class": "eyebrow mono"}, "Reference · County"),
               h("h1", None, "County government"),
               h("p", {"class": "dek"},
                 f"{ed.county_label} has a board of commissioners, a county council, elected row officers and a "
                 f"prosecutor, and county courts. The guide's data lists {len(comm)} commissioner seats, "
                 f"{len(council)} council seats, {n_row_only} row officers, {n_pros} prosecutor{'s' if n_pros != 1 else ''} and {len(court_offices)} judgeships: "
                 f"{n_elected} offices in all.", cites.cite(_union_sources(offices[:1] + court_offices[:1])), " ",
                 status_badge("computed", page, "Seat counts computed from the guide's office data.")),
               answer_box(ed, page, ed.units["county"], offices + court_offices, mark_here=False, links={
                   "who": "#officeholders",
                   "spend": ("money/what-is-a-budget/index.html#county-example", "Why county budget totals differ"),
                   "vote": ("elections/calendar/index.html#by-year", "Election calendar"),
                   "people": ("community/index.html", "Know your community")}),
               county_rail(page),
               h("p", {"class": "hero-badges"}, scope_badge("county", ed), " ", scope_badge("indiana", ed),
                 h("span", {"class": "muted"}, " marks rules that apply in every county.")),
               h("nav", {"class": "toc", "aria-label": "On this page"},
                 h("ol", None, [h("li", None, h("a", {"href": f"#{a}"}, t)) for a, t in toc]))))

    # ------------------------------------------------------------------ 1 structure
    split_rule = ed.local_rules.get("county_government_split", {})
    council_rule = ed.local_rules.get("county_council_structure", {})
    comm_type = ed.office_types.get("county_commissioner", {})
    council_type = ed.office_types.get("county_council_member", {})
    # Litigation over the county's election structure lives in the office notes (data), so each
    # sentence keeps the office's citations. Only sentences about the lawsuit or ruling are shown.
    lit_pat = r"(?i)lawsuit|\bsued\b|ruled|ruling|appeal|docket|judgment|court record|order's text|held under the district system"

    def lit_text(offs):
        notes = offs[0]["notes"] if offs else ""
        # the shared lawsuit text (same as the history timeline's 2026-04-22 entry) follows "Lawsuit:" in the notes
        return notes.split("Lawsuit:", 1)[1].strip() if "Lawsuit:" in notes else _sentences_matching(notes, lit_pat)

    # the commissioners' and the council's notes carry the same lawsuit text: it is printed once (under the
    # commissioners, with both offices' citations) in a fold, and the council's rule points to it
    same_suit = bool(lit_text(comm)) and lit_text(comm) == lit_text(council)

    def litigation(offs, fid, srcs):
        text = lit_text(offs)
        if not text:
            return None
        return see_all_fold(fid, 0, h("p", {"class": "litigation"},
                                      h("span", {"class": "mono"}, f"Litigation, as of {fmt_date(ed.as_of)}: "),
                                      text, cites.cite(srcs)),
                            label=f"Litigation over the district elections, as of {fmt_date(ed.as_of)}", hint="Case history")

    def council_litigation():
        if same_suit:
            return h("p", {"class": "litigation-ref"}, "The same lawsuit challenges the council's district elections: see ",
                     h("a", {"href": "#litigation"}, "Litigation over the district elections"), " above.")
        return litigation(council, "litigation-council", council[0]["source_ids"] if council else "")
    letters = ", ".join(o["district"] for o in council)
    v_size = ed.variant("council_size") or {}
    if v_size and str(v_size.get("value")) != str(len(council)):
        ed.warnings.append(f"variant council_size={v_size.get('value')} but offices.csv lists {len(council)} council seats")

    legislative = variant_slot(
        ed, "legislative_power", h("span", None, split_rule.get("plain_language", "")),
        {"council_full": h("p", None, "Under one state law, the county council, not the commissioners, is the legislative and "
                                      "fiscal body in the counties it covers. It covers counties of a set population range, and "
                                      "counties that opted in or adopted it by ordinance. ",
                           (f"{county} County's commissioners opted in by resolution in 2023, so this applies here. "
                            if (ed.variant("legislative_power") or {}).get("verified") else
                            f"The guide's research says this applies to {county} County, but the guide hasn't found the "
                            "county's opt-in record, so treat it as unconfirmed. "),
                           page.cites.cite((ed.variant("legislative_power") or {}).get("source_ids") or "IND-057"))},
        page, split_rule.get("source_ids"))
    commissioners = variant_slot(
        ed, "commissioner_election", h("span", None, comm_type.get("what_it_does", "")),
        {"by_district": h("div", None,
                          h("p", None, f"In {county} County, each of the {len(comm)} commissioners is elected only by voters "
                                       "in that commissioner's district.", cites.cite(_union_sources(comm))),
                          litigation(comm, "litigation", _union_sources(comm[:1] + (council[:1] if same_suit else [])))
                          if comm else None)},
        page, comm_type.get("source_ids"))
    council_v = variant_slot(
        ed, "council_size", h("span", None, council_rule.get("plain_language", "")),
        {v_size.get("value"): h("div", None,
                                h("p", None, f"{county} County's council has {len(council)} single-member districts "
                                             f"({letters}), one member each.", cites.cite(_union_sources(council))),
                                council_litigation())},
        page, council_rule.get("source_ids"))
    page.add(section("structure", 1, "How county government is organized",
                     h("h3", None, "Who passes county laws and budgets"), legislative,
                     h("h3", None, "How commissioners are elected"), commissioners,
                     h("h3", None, "How the council is elected"), council_v,
                     ed=ed,
                     lead="Indiana sets the basic structure for every county; some counties differ by statute. "
                          "Each rule below is shown with its county exception where one applies."))

    # ------------------------------------------------------------------ 2 officeholders
    def rows(offs):
        """One compact row per office (civic/holder_rows.py); each opens to the card's fields."""
        out = []
        for o in offs:
            note = None
            if o["office_type"] == "superior_court_judge":
                note = ("Merit-selection seat; the canvass identifies the seat by the judge's surname. The start date shown is "
                        "inferred from a retention vote in the guide's results (the January after the vote); the judge was already "
                        "serving before that vote. The date of first appointment is not in the guide's data.")
            # "Judge of the Superior Court (seat identified by incumbent surname: Manier)" -> "Superior Court, Manier seat"
            m = re.search(r"Superior Court \(seat identified by incumbent surname: ([^)]+)\)", o["title"])
            title = f"Superior Court judge, {m.group(1)} seat" if m else None
            out.append(holder_row(ed, page, o, ed.current_terms(o["office_id"]), ed.incoming_terms(o["office_id"]), note,
                                  title=title))
        return h("div", {"class": "one-list holder-rows"}, out)
    n_incoming = sum(len(ed.incoming_terms(o["office_id"])) for o in offices + court_offices)
    dmap = _district_map(ed, page, comm, council)
    page.add(section("officeholders", 2, "Who holds county offices now",
                     h("p", None, f"From the guide's terms data, as of {fmt_date(ed.as_of, long=True)}. Officeholders are listed "
                                  "by office and district, never by party. ",
                       f"{n_incoming} people elected on Nov 3, 2026 are shown as incoming; they take office Jan 1, 2027, "
                       "and those results are unofficial until the county certifies them." if n_incoming else ""),
                     h("p", None, "Commissioners and council members are each elected by one district. Find yours on the "
                                  "map; every office is also listed below, one line each. Open a line for how the holder "
                                  "was first chosen and the sources.") if dmap else
                     h("p", None, "Every office is listed below, one line each. Open a line for how the holder was first "
                                  "chosen and the sources."),
                     dmap,
                     _here_districts(ed),
                     one_bar("office", "offices", "Pick a district on the map, or open any office below."),
                     h("h3", None, body_with_breakdown("Board of Commissioners", *body_state(ed, comm))), rows(comm),
                     h("h3", None, body_with_breakdown("County Council", *body_state(ed, council))), rows(council),
                     as_of_note(ed),
                     h("h3", None, "Countywide officers: row officers and prosecutor"),
                     h("p", {"class": "muted"}, "Elected by the whole county, so they are not on the district map."),
                     rows(row),
                     h("h3", None, "Judges"), rows(other_courts + superior),
                     h("h3", None, "State legislators for the county"),
                     h("p", None, "These districts include part of the county, so the county's delegation is the set of legislators "
                                  "whose districts reach it. Listed by chamber and district number."),
                     bodies_block(ed, [], extra_bodies=_delegation(ed), note=False),
                     scope="county", ed=ed))

    # ------------------------------------------------------------------ 3 row officers
    trows = []
    for o in row:
        ot = ed.office_type_row(o) or {}
        trows.append([o["title"],
                      h("span", None, ot.get("what_it_does", "Description not yet in the guide's data."),
                        cites.cite(ot.get("source_ids")) if ot else None),
                      f"{o['term_years']} years" if o.get("term_years") else "",
                      ot.get("term_limit", ""),
                      o.get("next_election", "")])
    page.add(section("row-officers", 3, "Row officers and what they do",
                     h("p", None, "Indiana's county row officers are elected countywide in partisan races. "
                                  "Descriptions and term limits are the Indiana-wide rules; next-election years are this county's.",
                       cites.cite(ed.rules.get("county_row_office_term_limits", {}).get("source_ids"))),
                     data_table("row-officers-table", ["Office", "What it does", "Term", "Term limit", "Next regular election"],
                                trows, caption="County row officers", numeric=(4,), min_width="44rem"),
                     scope="indiana", ed=ed))

    # ------------------------------------------------------------------ 4 courts
    court_rule = ed.local_rules.get("court_structure", {})
    merit_rule = ed.rules.get("merit_selection_counties", {})
    ret_rule = ed.rules.get("superior_court_retention", {})
    sup_type = ed.office_types.get("superior_court_judge_merit", {})
    circ_type = ed.office_types.get("circuit_court_judge", {})
    superior_v = variant_slot(
        ed, "superior_court_selection",
        h("span", None, merit_rule.get("plain_language", ""), " ", ret_rule.get("plain_language", ""),
          cites.cite(ret_rule.get("source_ids"))),
        {"merit_retention": h("p", None, f"{county} County is one of these counties. The guide's data lists {len(superior)} "
                                         "Superior Court seats. How a seat is filled: ", sup_type.get("vacancy_rule", ""),
                              cites.cite(sup_type.get("source_ids")))},
        page, merit_rule.get("source_ids"))
    ret = []
    for c in sorted((c for c in ed.contests.values() if c["office_id"] in {o["office_id"] for o in superior}),
                    key=lambda c: (ed.elections[c["election_id"]]["date"], c["label"])):
        ret.append(c)
    latest_ret_eid = max((c["election_id"] for c in ret), key=lambda e: ed.elections[e]["date"], default=None)
    ret_figs = []
    for c in ret:
        if c["election_id"] != latest_ret_eid:
            continue
        ret_figs.append(_contest_figure(ed, page, c, question=True))
    page.add(section("courts", 4, "Courts",
                     h("p", None, court_rule.get("plain_language", ""), cites.cite(court_rule.get("source_ids")), " ",
                       circ_type.get("what_it_does", ""), cites.cite(circ_type.get("source_ids"))),
                     h("h3", None, "How Superior Court judges are chosen"), superior_v,
                     h("p", None, f"The Circuit Court and Probate Court judges are elected in partisan races "
                                  f"({', '.join(o['term_years'] + '-year terms' for o in other_courts[:1])}).",
                       cites.cite(_union_sources(other_courts))) if other_courts else None,
                     h("h3", None, f"Most recent retention votes ({ed.elections[latest_ret_eid]['date'][:4]})") if ret_figs else None,
                     h("div", {"class": "chart-grid"}, ret_figs) if ret_figs else None,
                     ed=ed))

    # ------------------------------------------------------------------ 5 boards
    boards = county_scope_boards(ed) + [b for b in ed.boards if ed.units.get(b["unit_id"], {}).get("unit_type") == "library"]
    brows = []
    for b in boards:
        brows.append([b["name"], b.get("what_it_decides", ""), b.get("seats") or "not in sources",
                      b.get("appointing_authorities") or "not in sources",
                      h("span", None, status_badge(b["status"], page), cites.cite(b["source_ids"]))])
    page.add(section("boards", 5, "Appointed boards and who appoints them",
                     h("p", None, "These bodies make county-level decisions but their members are appointed, not elected. "
                                  "The table lists every county-level board in the guide's data, including the two public "
                                  "library boards, with what the sources say about who appoints them."),
                     data_table("boards-table", ["Board", "What it decides", "Seats", "Who appoints", "Status"], brows,
                                caption="County-level appointed boards", min_width="44rem"),
                     scope="county", ed=ed))

    # ------------------------------------------------------------------ 6 party control
    council_years = control_by_year(ed, council)
    comm_years = control_by_year(ed, comm)
    method = CONTROL_METHOD
    charts = []
    if council_years:
        charts.append(party_timeline("control-council", "County Council seats by party", council_years, len(council),
                                     subtitle=f"{council_years[0]['year']} to {council_years[-1]['year']}, {len(council)} seats",
                                     note=method, page=page, cite=cites.cite(_union_sources(ed.terms_for(o["office_id"])[0] for o in council))))
    if comm_years:
        charts.append(party_timeline("control-commissioners", "Board of Commissioners seats by party", comm_years, len(comm),
                                     subtitle=f"{comm_years[0]['year']} to {comm_years[-1]['year']}, {len(comm)} seats",
                                     note=method, page=page, cite=cites.cite(_union_sources(ed.terms_for(o["office_id"])[0] for o in comm))))
    spans = [f"{label} {ys[0]['year']} to {ys[-1]['year']}" for label, ys in
             (("County Council", council_years), ("Board of Commissioners", comm_years)) if ys]
    page.add(section("control", 6, "Party control over time",
                     bodies_block(ed, comm + council),
                     h("p", None, "Two charts show the party label of each seat's holder on January 2 of every year in "
                                  "the guide's data, one row per year, with a table view each. ",
                       h("a", {"href": page.rel("history/index.html#control")}, "Party control of local bodies over time"),
                       " is on the History page.") if charts else None,
                     see_all_fold("control-charts", 0, charts,
                                  label="Seat-by-seat charts: " + "; ".join(spans), hint="Charts · tables")
                     if charts else None,
                     h("p", {"class": "muted"}, "The full range of the guide's data is shown. Earlier years are listed under Gaps."),
                     scope="county", ed=ed))

    # ------------------------------------------------------------------ 7 results
    # District seats (commissioners, council): one show-one item per seat, keyed like its officeholder line, so a
    # district picked on the map opens its result too. Countywide offices: one row per race, charts in a fold.
    gen = [e for e in ed.elections.values() if e["type"] == "general"]
    gen.sort(key=lambda e: e["date"], reverse=True)
    recent = [e["election_id"] for e in gen[:2]]
    page.add(section("results", 7, "Recent results for county offices",
                     *_results_body(ed, page, comm, council, row + other_courts, gen[:2]),
                     h("p", None, ballot_order_note(ed, page, recent), "Candidates appear in the order the source lists them. "
                                  "The bar scale is 0 to 100% for every race. Percentages are computed from the vote counts "
                                  "where the canvass doesn't print them. ",
                       h("a", {"href": page.rel("elections/results/index.html")}, "All results, 2010 to 2026")),
                     scope="county", ed=ed))

    flows = money_in_out(ed, page, "county-st-joseph", level=3, label="County government money in and money out")
    if flows:
        digest = _flows_digest(ed, "county-st-joseph")
        page.add(section("money", 8, "Money in and money out",
                         h("p", None, "What county government received and spent, from the annual financial report the "
                                      "county files with the state. ",
                           h("a", {"href": page.rel("money/budgets/index.html#county")}, "Budgets over time"),
                           " are on the budgets page."),
                         tax_base_line(ed, page, "county-st-joseph", county_label=ed.county_label,
                                       extra=" It covers all property in the county, inside the cities and towns too."),
                         # the state report's income and spending charts (3 screens) open from one line, as on the
                         # place pages; links into them (#sp-county-...) open the fold
                         see_all_fold("money-flows-county", 0, flows,
                                      label="Money in and money out, from the annual report to the state"
                                            + (f": {digest}" if digest else ""), hint="Charts · tables"),
                         scope="county", ed=ed))

    gaps = ed.gaps(files=["gaps_gov", "gaps_results"], pattern=GAP_PATTERN)
    page.finish(gaps=gaps)
    return page


COUNTY_SETS = (("commissioners", "county-commissioner-2022", "Commissioner districts", "county_commissioner"),
               ("council", "county-council-2022", "Council districts", "county_council_member"))
COUNTY_SET_NOTE = ("Districts adopted March 1, 2022, when the commissioners and the council passed amended maps to settle "
                   "the redistricting lawsuit; in use for the 2022, 2024 and 2026 elections. The county's map layer matches "
                   "the 2024 results precinct by precinct; it was not separately checked against the 2022 results.")
COUNCIL_LAYER_NOTE = ("The county's council layer is named for 2025 (created February 2025) but matches the 2024 results; "
                      "whether it changed any 2022 line was not established.")
LAWSUIT_NOTE = ("A lawsuit filed in 2023 challenges the state laws that give the county district-only elections; see How "
                "county government is organized.")


def _district_map(ed, page, comm: list[dict], council: list[dict]):
    """Commissioner and council district map (civic/district_map.py): the panel names who represents the district and
    the next election; a click opens that office's row. None when the district shapes are missing."""
    shapes = load_shapes(ed)
    dshapes = load_district_shapes(ed, shapes) if shapes else None
    c = page.cites
    layers = []
    by_type = {"county_commissioner": comm, "county_council_member": council}
    for tab, set_id, label, otype in COUNTY_SETS:
        rec = district_set(dshapes, set_id)
        if not rec:
            continue
        offs = {o["district"]: o for o in by_type[otype]}
        items, seen = [], set()
        for it in rec["items"]:
            o = offs.get(it["district"])
            if not o:
                ed.warnings.append(f"county map: {set_id} district {it['district']} has no office in offices.csv; left off")
                continue
            seen.add(o["office_id"])
            cur, inc = ed.current_terms(o["office_id"]), ed.incoming_terms(o["office_id"])
            st = holder_state(ed, o, cur, inc)
            facts = [["Represented by", st["now"]]]
            if st["since"]:
                facts.append(["In office since", st["since"]])
            if st["how"]:
                facts.append(["First chosen by", st["how"]])
            if st["incoming"]:
                facts.append(["Nov 3, 2026 election", st["incoming"]])
            nxt = o.get("next_election") or "not in the guide's data"
            facts.append(["Next election", f"{nxt} ({o['term_years']}-year term)" if o.get("term_years") else nxt])
            cav = [COUNTY_SET_NOTE] + ([COUNCIL_LAYER_NOTE] if tab == "council" else [])
            if it.get("county_share") is not None:
                cav.append(f"About {it['county_share'] * 100:.0f}% of the county's land area is in this district "
                           "(computed from the official boundary).")
            cav.append(LAWSUIT_NOTE)
            href = f"#office-{o['office_id']}"
            entry = {"n": o["title"], "t": "County district", "f": facts, "cav": cav, "note": "", "href": href,
                     "open": "Show this seat's details"}
            items.append({"uid": o["office_id"], "district": it["district"], "d": it["d"], "href": href,
                          "aria": f"{o['title']}: {st['now']}. Next election {nxt}. Show this seat's details.",
                          "entry": entry, "text": it["district"], "label": it["label"], "label_r": it["label_r"]})
        missing = [o["title"] for o in by_type[otype] if o["office_id"] not in seen]
        legend = [h("p", None, COUNTY_SET_NOTE, c.cite_compact(rec.get("source_ids", ""))),
                  h("p", None, COUNCIL_LAYER_NOTE) if tab == "council" else None,
                  h("p", None, "Not on the map (no boundary in the guide's data): " + ", ".join(missing) + ".") if missing else None]
        layers.append({"tab": tab, "label": label, "items": items, "legend": legend})
    if not layers:
        return None
    return district_map(page, ed, shapes, layers, layers[0]["tab"],
                        label=f"Map of the county commissioner and county council districts of {ed.county_label}. Every "
                              "district is a link to its office below.",
                        hint="Hover, focus or tap a district to see who represents it and the next election. Select it "
                             "again, or use the link, to open its line below.",
                        notes=h("div", {"class": "dmap-notes"},
                                h("p", None, "Party labels are shown as the guide's sources print them. The map is not "
                                             "shaded by party.")))


def _delegation(ed) -> dict:
    """The state House and Senate seats whose districts include part of the county, keyed by display name."""
    out = {}
    house, senate = ed.offices_for("in-house"), ed.offices_for("in-senate")
    if house:
        out["State House members"] = house
    if senate:
        out["State Senate members"] = senate
    return out


def _contest_figure(ed, page, c, question: bool = False):
    rows = c["rows"]
    status = rows[0]["status"] if len({r["status"] for r in rows}) == 1 else "from_scan" if any(r["status"] == "from_scan" for r in rows) else rows[0]["status"]
    low = [r for r in rows if r.get("confidence") == "low"]
    cands = []
    is_q = question or all(r["candidate"] in ("YES", "NO") for r in rows)
    for r in rows:
        try:
            pct = float(r["pct"]) if r["pct"] else None
        except ValueError:
            pct = None
        try:
            votes = int(float(r["votes"])) if r["votes"] else None
        except ValueError:
            votes = None
        cands.append({"name": r["candidate"].title() if r["candidate"] in ("YES", "NO") else r["candidate"],
                      "party": r["party"], "votes": votes, "pct": pct, "winner": r["winner"]})
    notes = []
    if len(rows) == 1 and not is_q:
        notes.append("Uncontested.")
    if all(r["winner"] == "" for r in rows) and not is_q:
        notes.append("Winner not recorded in the guide's data.")
    if low:
        notes.append("Some figures are low confidence.")
    sub = f"Vote for {c['vote_for']}" if c.get("vote_for") and c["vote_for"] != "1" else None
    fid = "res-" + c["contest_id"]
    return results_bars(fid, c["label"], cands, subtitle=sub, status=status, note=" ".join(notes) or None,
                        page=page, question=is_q, cite=page.cites.cite(";".join(dict.fromkeys(s for r in rows for s in split_ids(r["source_ids"])))))


# ------------------------------------------------------------------ "More about" rail (Wave C batch 7, 2026-11-09)

# Links the county rail adds after related_items' own (each only when the page is built). The map link to "the
# latest county race" is left out: the county has no head office, so that race (Treasurer, 2024) stood for nothing.
COUNTY_RAIL_EXTRA = (
    ("campaigns-courts", "Campaign money", "Judges' races", "money/campaigns/courts/index.html"),
    ("legislators", "Also in the county", "Your state legislators", "state/your-legislators/index.html"),
    ("schools", "Also in the county", "School boards", "schools/index.html"),
    ("history", "History", "Party control over time", "history/index.html#control"),
)
COUNTY_RAIL_ORDER = ("campaigns", "campaigns-courts", "budget", "tax-rate", "community", "legislators", "schools",
                     "history", "run", "calendar")


def county_rail(page) -> Markup | None:
    """The county page's rail: related_items for the county without its arbitrary map race, plus the county's
    judges' campaign money, its legislators and school boards, and the History page's party-control chart."""
    items = {i.key: i for i in related_items(page, "county") if i.key != "map-votes"}
    built = page.site.by_path
    for key, topic, text, target in COUNTY_RAIL_EXTRA:
        if target.partition("#")[0] in built:
            items[key] = RelatedLink(key, topic, text, page.rel(target))
    return related_rail([items[k] for k in COUNTY_RAIL_ORDER if k in items] +
                        [i for k, i in items.items() if k not in COUNTY_RAIL_ORDER],
                        name="county government")


# ------------------------------------------------------------------ results by district (Wave C batch 7)

def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _result_digest(ed, c) -> str:
    """'Nov 3, 2026 (unofficial): Bill Redman (D) 58.4%, Carl H Baxmeyer (R) 41.6%', in ballot order."""
    el = ed.elections[c["election_id"]]
    rows = c["rows"]
    total = sum(_num(r["votes"]) or 0 for r in rows)
    bits = []
    for r in rows:
        pct = _num(r["pct"])
        if pct is None and total and _num(r["votes"]) is not None:
            pct = _num(r["votes"]) / total * 100
        bits.append(name_party_text(r["candidate"], r["party"]) + (f" {pct:.1f}%" if pct is not None and len(rows) > 1 else "")
                    + (" elected" if r.get("winner") == "Y" and len(rows) > 1 else ""))
    st = " (unofficial)" if any(r["status"] == "unofficial" for r in rows) else ""
    return f"{fmt_date(el['date'])}{st}: " + ", ".join(bits) + (", uncontested" if len(rows) == 1 else "")


def _race_links(ed, page, c, races) -> list:
    out = []
    ex = contest_href(page, c["contest_id"])
    if ex:
        out.append(h("a", {"href": ex}, "In the results explorer"))
    if c["contest_id"] in races:
        out.append(h("a", {"href": page.rel(f"map/index.html#race-{races[c['contest_id']]}")}, "On the map, by precinct"))
    return out


def _results_body(ed, page, comm, council, countywide, elections) -> list:
    """Recent results: (1) one item per commissioner and council seat (pick_one key = the office id, the same key as
    its officeholder line and its map district), holding that seat's races in the last two general elections;
    (2) the countywide offices as one row per race, with every countywide chart in a 'See all' fold."""
    from civic.map import load_votes, race_by_contest
    from .places import _result_cell
    c = page.cites
    shapes = load_shapes(ed)
    races = race_by_contest(ed, load_votes(ed)) if shapes and "precinct" in shapes.get("layers", {}) else {}
    eids = [e["election_id"] for e in elections]
    years = " and ".join(sorted(e["date"][:4] for e in elections))
    turnout = [h("li", None, f"{fmt_date(e['date'], long=True)} general election: turnout {e['turnout_pct']}% of "
                             f"{int(e['registered']):,} registered voters. ", status_badge(e["status"], page),
                 c.cite(e["source_ids"]))
               for e in elections if e.get("turnout_pct") and e.get("registered")]
    out = [h("p", None, f"County offices on the {years} general-election ballots. Commissioners and council members are "
                        "elected by district: pick a district on the ", h("a", {"href": "#officeholders"}, "map"),
             " and its result opens here too, beside its officeholder line."),
           h("ul", {"class": "results-turnout"}, turnout) if turnout else None]

    # 1 district seats
    items = []
    for o in comm + council:
        cs = sorted((x for x in ed.contests_for_office(o["office_id"]) if x["election_id"] in eids),
                    key=lambda x: ed.elections[x["election_id"]]["date"], reverse=True)
        if cs:
            digest = _result_digest(ed, cs[0])
            body = []
            for x in cs:
                links = _race_links(ed, page, x, races)
                body.append(h("div", {"class": "res-seat"}, _contest_figure(ed, page, x),
                              h("p", {"class": "res-seat-links"}, join(links, " · ")) if links else None))
        else:
            last = latest_contest(ed, o["office_id"])
            nxt = o.get("next_election") or "not in the guide's data"
            digest = f"Not on the {years} ballots; next election {nxt}"
            href = contest_href(page, last["contest_id"]) if last else None
            body = [h("p", None, f"This seat was not on the ballot in {years}. Next regular election: {nxt}. ",
                      h("a", {"href": href}, f"Its {ed.elections[last['election_id']]['date'][:4]} result in the results "
                                             "explorer") if href else "The results explorer has no earlier race for it.")]
        items.append(one_fold(o["office_id"], o["title"], one_summary("h4", o["title"], digest), body,
                              item_id=f"results-{o['office_id']}"))
    out += [h("h3", None, "Commissioner and council districts"),
            one_bar("office", "offices", "Pick a district on the map, or open any seat below."),
            h("div", {"class": "one-list results-seats"}, items)]

    # 2 countywide offices
    rank = {o["office_id"]: i for i, o in enumerate(countywide)}
    rows, blocks, n = [], [], 0
    for e in elections:
        cs = sorted((x for o in countywide for x in ed.contests_for_office(o["office_id"])
                     if x["election_id"] == e["election_id"]),
                    key=lambda x: (rank.get(x.get("office_id"), len(rank)), x["label"]))
        if not cs:
            continue
        for x in cs:
            links = [h("a", {"href": f"#res-{x['contest_id']}"}, "Chart")] + _race_links(ed, page, x, races)
            srcs = ";".join(dict.fromkeys(sid for r in x["rows"] for sid in split_ids(r["source_ids"])))
            sts = list(dict.fromkeys(r["status"] for r in x["rows"]))
            rows.append([fmt_date(e["date"]), x["label"], _result_cell(x),
                         h("span", None, join([status_badge(st, page) for st in sts], " "), c.cite(srcs)),
                         join(links, " · ")])
        n += len(cs)
        blocks.append(h("div", {"class": "results-year"},
                        h("h3", None, f"{fmt_date(e['date'], long=True)} general election ", status_badge(e["status"], page)),
                        h("div", {"class": "chart-grid"}, [_contest_figure(ed, page, x) for x in cs])))
    if rows:
        out += [h("h3", None, "Countywide offices: row officers, prosecutor and judges"),
                h("p", {"class": "muted"}, "Elected by the whole county. One row per race; the chart, the results explorer "
                                           "and the precinct map are linked from each row."),
                data_table("results-countywide", ["Election", "Race", "Candidates (ballot order)", "Status", "Full result"],
                           rows, caption="Recent general-election races for countywide county offices, one row each",
                           min_width="46rem"),
                see_all_fold("results-charts-county", n, blocks, noun="countywide result chart", hint="Charts · tables")]
    return out


def _flows_digest(ed, mid: str) -> str:
    """'counted spending $272M in 2025; counted income $289M' (the fold line above the money charts), or ''."""
    from civic.money_map import summarize_rows
    from civic.spending import _kind, _rows, usd_short
    sm = summarize_rows(_rows(ed, mid), _kind(ed, mid))
    if not sm:
        return ""
    inc = f"; counted income {usd_short(sm['income'])}" if sm.get("income") is not None else ""
    return f"counted spending {usd_short(sm['spending'])} in {sm['spending_year_label']}{inc}"


def _here_districts(ed) -> list:
    """Saved-place preselect (Wave E batch 8, static/js/preselect.js "one"): the hidden line slot and, for each saved
    place whose commissioner and council districts the guide's precinct results show as single ones
    (civic/preselect.py county_districts), the office keys to open. Places not in the map open nothing."""
    votes = load_votes(ed)
    offices = {o for o, _ in COUNTY_DISTRICT_OFFICES}
    years = sorted({int(r["year"]) for r in (votes or {}).get("races", [])
                    if r.get("office") in offices and int(r.get("year") or 0) >= 2022})
    when = " and ".join(str(y) for y in years) if years else ""
    return [here_slot("one", "officeholders", extra={"data-here-keys": "json:here-districts",
                                                     "data-here-undo": "Show all offices",
                                                     "data-here-apply": "Open them"}),
            json_script("here-districts", {"places": county_districts(ed, votes), "years": when})]

