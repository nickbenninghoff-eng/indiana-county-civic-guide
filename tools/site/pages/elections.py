"""Elections section: how elections work, calendar, results explorer, judges and
public questions, and the elections-by-the-numbers landscape.

Every figure comes from data/indiana/election_rules.csv, data/editions/<ed>/elections.csv,
results.csv, offices.csv, terms.csv and the source files. Computed values (margins, turnout
comparisons, calendar years, term-limit status) carry the COMPUTED badge and say how they
were computed.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

from civic.charts import columns, hbar, legend, results_bars
from civic.components import (callout, data_table, party_label, scope_badge, section, status_badge,
                              variant_slot)
from civic.data import (PARTY_LABELS, SELECTED_BY_LABELS, fmt_date, fmt_int, nth_weekday_after, parse_date,
                        split_ids)
from civic.html import Markup, h, json_script

YEARS = list(range(2026, 2031))
RESULTS_FROM = "2010"
TYPE_LABEL = {"general": "general election", "primary": "primary election",
              "municipal_general": "municipal general election", "municipal_primary": "municipal primary",
              "special": "special election"}
MUNICIPAL_TYPES = ("municipal_general", "municipal_primary", "special")
# Indiana Const. Art. 6 sec. 2 list (election_rules.csv county_row_office_term_limits)
LIMIT_8_IN_12 = {"county_auditor", "county_clerk", "county_recorder", "county_treasurer", "county_sheriff",
                 "county_coroner"}
LEVELS = [("county", "County offices"), ("court_system", "County courts"), ("township", "Townships"),
          ("city", "Cities"), ("town", "Towns"), ("school_corporation", "School boards"),
          ("state_chamber", "State legislature"), ("statewide", "Statewide offices"), ("federal", "Federal")]
LEVEL_LABEL = dict(LEVELS)
LEVEL_ORDER = {k: i for i, (k, _) in enumerate(LEVELS)}

GROUPS = ["County row offices", "County commissioners", "County council", "County courts",
          "Superior Court retention", "Township offices", "City offices", "Town offices", "School boards",
          "State legislature", "Statewide offices", "State court retention", "Public questions",
          "Straight-party ballots"]
GROUP_ORDER = {g: i for i, g in enumerate(GROUPS)}
TOWNS = ("lakeville", "new-carlisle", "north-liberty", "osceola", "roseland", "walkerton", "indian-village")
SCHOOLS = ("south-bend-schools", "mishawaka-schools", "penn-harris-madison-schools", "john-glenn-schools",
           "union-north-schools", "new-prairie-schools", "laville-schools")
# statewide constitutional questions printed on the county ballot under a county label
STATEWIDE_QUESTIONS = {"2024g-county-public-question-1", "2026g-county-public-question-1",
                       "2026g-county-public-question-2"}
BANDS = [("under-5", "Under 5 points", 0, 5), ("5-15", "5 to 15 points", 5, 15), ("over-15", "Over 15 points", 15, 1000)]


# =========================================================================== shared helpers

def _src(*rows_or_ids) -> str:
    out: list[str] = []
    for x in rows_or_ids:
        ids = split_ids(x.get("source_ids")) if isinstance(x, dict) else split_ids(x)
        for i in ids:
            if i not in out:
                out.append(i)
    return ";".join(out)


def _hero(page, eyebrow, dek, scopes, toc):
    ed = page.ed
    return h("header", {"class": "page-hero"},
             h("p", {"class": "eyebrow mono"}, eyebrow),
             h("h1", None, page.title),
             h("p", {"class": "dek"}, dek),
             h("p", {"class": "hero-badges"}, [[scope_badge(s, ed), " "] for s in scopes]),
             h("nav", {"class": "toc", "aria-label": "On this page"},
               h("ol", None, [h("li", None, h("a", {"href": f"#{a}"}, t)) for a, t in toc])))


def _rule_p(page, ed, key, detail=False, extra=None):
    """One Indiana rule as a paragraph: plain language (+ detail), citation, status badge.
    Low-confidence rules return None (they appear only in the flagged table)."""
    r = ed.rules.get(key)
    if not r:
        ed.warnings.append(f"elections: rule {key} not in election_rules.csv")
        return None
    if r.get("confidence") == "low":
        return None
    det = re.sub(r"\s*\(see [a-z_]+\)", "", r["detail"]) if detail and r.get("detail") else None
    return h("p", {"class": "elx-rule"}, r["plain_language"], " ", det,
             extra, page.cites.cite(r["source_ids"]), " ", status_badge(r["status"], page),
             h("span", {"class": "elx-statute mono"}, f" {r['statute']}") if r.get("statute") else None)


def _low_rules_table(page, ed, keys, tid):
    rows = []
    for k in keys:
        r = ed.rules.get(k)
        if r and r.get("confidence") == "low":
            rows.append([r["plain_language"], r.get("detail", ""),
                         h("span", None, status_badge(r["status"], page), " ", status_badge("low", page),
                           page.cites.cite(r["source_ids"]))])
    if not rows:
        return None
    return h("div", {"class": "elx-low"},
             h("p", {"class": "muted"}, "Less certain rules, kept for completeness and not used elsewhere on this page:"),
             data_table(tid, ["Rule as recorded", "Detail", "Status"], rows, caption="Low-confidence rules",
                        min_width="36rem"))


def _elections(ed, since=RESULTS_FROM):
    out = [e for e in ed.elections.values() if e["date"] >= since]
    out.sort(key=lambda e: e["date"])
    return out


def _election_name(e) -> str:
    d = e["date"]
    when = fmt_date(d, long=True) if d.count("-") == 2 else d
    return f"{when} {TYPE_LABEL.get(e['type'], e['type'])}"


def _num(v):
    try:
        return float(v) if v not in (None, "") else None
    except ValueError:
        return None


def _rest(c) -> str:
    cid, eid = c["contest_id"], c["election_id"]
    rest = cid[len(eid) + 1:] if cid.startswith(eid + "-") else cid
    if c.get("party_primary") and re.search(r"-[a-z]$", rest):
        rest = rest[:-2]
    return rest


def classify(c) -> tuple[str, str, bool]:
    """(office group, place, crosses the county line) from contest_id and label."""
    rest = _rest(c)
    label = c["label"]
    place = label.split(":")[0].strip() if ":" in label else ""
    q = "question" in rest or "amendment" in rest
    if "straight-party" in rest:
        return "Straight-party ballots", place or "St. Joseph County", False
    if c["contest_id"] in STATEWIDE_QUESTIONS:
        return "Public questions", "Statewide", True
    if rest.startswith("state-house") or rest.startswith("state-senate"):
        # a district that lay wholly inside the county (county totals equal the district totals) is decided here
        if c["rows"] and all("district lies wholly in the county" in (r.get("notes") or "") for r in c["rows"]):
            return "State legislature", "Legislative district (wholly in the county)", False
        return "State legislature", "Legislative district (county portion)", True
    if rest.startswith("state-retention"):
        return "State court retention", "Statewide or appellate district", True
    if rest.startswith("state-"):
        return ("Public questions" if q else "Statewide offices"), "Statewide", True
    if rest.startswith(SCHOOLS):
        return ("Public questions" if q else "School boards"), place or "School corporation", False
    if q:
        return "Public questions", place or "St. Joseph County", False
    if rest.startswith("county-superior-court"):
        return "Superior Court retention", "St. Joseph County", False
    if rest.startswith(("county-circuit", "county-probate")):
        return "County courts", "St. Joseph County", False
    if rest.startswith("county-commissioner"):
        return "County commissioners", "St. Joseph County", False
    if rest.startswith("county-council"):
        return "County council", "St. Joseph County", False
    if rest.startswith("county-"):
        return "County row offices", "St. Joseph County", False
    if "-township-" in rest:
        return "Township offices", place, False
    if rest.startswith(("south-bend-", "mishawaka-")):
        return "City offices", place, False
    if rest.startswith(TOWNS):
        return "Town offices", place, False
    return "Other", place or "", False


def contest_status(rows) -> str:
    st = {r["status"] for r in rows}
    for s in ("unofficial", "from_scan", "secondary", "single_source"):
        if s in st:
            return s
    return rows[0]["status"]


def candidates(c) -> list[dict]:
    """Ballot-order candidates with votes and share (share computed from votes if not printed)."""
    rows = c["rows"]
    votes = [_num(r["votes"]) for r in rows]
    total = sum(v for v in votes if v is not None)
    out = []
    for r, v in zip(rows, votes):
        pct = _num(r["pct"])
        computed = False
        if pct is None and v is not None and total:
            pct, computed = 100.0 * v / total, True
        out.append({"name": r["candidate"].title() if r["candidate"] in ("YES", "NO") else r["candidate"],
                    "party": r["party"], "votes": int(v) if v is not None else None, "pct": pct,
                    "winner": r["winner"], "low": r.get("confidence") == "low", "computed": computed,
                    "row": r})
    return out


def is_question(c) -> bool:
    return all(r["candidate"] in ("YES", "NO") for r in c["rows"])


def margin(c) -> dict | None:
    """Margin in points between the last seat won and the next candidate, by votes.
    Returns None when not computable (single candidate, missing votes, unknown seat count)."""
    cands = candidates(c)
    if any(x["votes"] is None for x in cands):
        return {"reason": "votes missing"} if len(cands) > 1 else None
    n = int(c["vote_for"]) if (c.get("vote_for") or "").isdigit() else None
    if n is None:
        return {"reason": "seat count not in data"} if len(cands) > 1 else None
    if len(cands) <= n:
        return None  # uncontested
    total = sum(x["votes"] for x in cands)
    if not total:
        return None
    ranked = sorted(cands, key=lambda x: -x["votes"])
    a, b = ranked[n - 1], ranked[n]
    pts = 100.0 * (a["votes"] - b["votes"]) / total
    band = next(bid for bid, _, lo, hi in BANDS if lo <= pts < hi)
    return {"pts": pts, "votes": a["votes"] - b["votes"], "ahead": a, "next": b, "band": band, "seats": n,
            "low": any(x["low"] for x in cands)}


def _place_order(ed, office):
    u = ed.units.get(office["unit_id"], {})
    return (LEVEL_ORDER.get(u.get("unit_type"), 99), office["unit_id"])


def years_on_ballot(office) -> list[int]:
    ny, ty = office.get("next_election", ""), office.get("term_years", "")
    if not (ny.isdigit() and ty.isdigit()):
        return []
    n, t = int(ny), int(ty)
    return [y for y in YEARS if (y - n) % t == 0]


def _seats(office):
    s = office.get("seats", "")
    return int(s) if s.isdigit() else None


def _plabel(code):
    return party_label(code) if code else "Party not recorded"


def _holder_text(t):
    return f"{t['person']} ({t['party']})" if t.get("party") else t["person"]


def _holders_now(ed, office_id):
    """Holders on the as-of date, one per seat: a 2026 winner whose term row is still unofficial is an
    incoming member, not a second current holder, while the pre-election holder's row is still current."""
    terms = ed.current_terms(office_id)
    settled = [t for t in terms if t.get("status") != "unofficial"]
    return settled or terms


def _gaps(ed, area, extra_files=(), pattern=None):
    rows = ed.gaps(areas=[area]) if area else []
    if extra_files:
        rows += ed.gaps(files=list(extra_files), pattern=pattern)
    return rows


def _row_office_name(ed, c):
    o = ed.offices.get(c["office_id"]) if c.get("office_id") else None
    return o["title"] if o else c["label"]


# =========================================================================== 1. how elections work

def build_index(site):
    ed = site.ed
    page = site.page("elections/index.html", banners=False)
    cites = page.cites
    R = ed.rules
    toc = [("offices", "Which offices, which years"), ("primaries", "Primaries and the ballot"),
           ("general", "The general election and straight-ticket voting"), ("voting", "How to vote"),
           ("county", "Voting in the county"), ("vacancies", "Vacancies and caucuses"),
           ("school-boards", "School-board party labels"), ("questions", "No citizen initiative"),
           ("candidate-info", "Where to find candidate information"), ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(_hero(page, "Reference · Elections",
                   "The rules on this page come from Indiana law and apply in every county. The St. Joseph County "
                   "section adds the county's own offices and contacts.", ["indiana", "county"], toc))

    # ---- offices and cycles
    otrows = []
    for ot in ed.table("office_types"):
        if ot["unit_type"] in ("state",) or not ot.get("cycle"):
            continue
        cyc = {"even": "Even years", "odd": "Odd years", "municipal": "Odd years (municipal)",
               "n/a": "Not elected"}.get(ot["cycle"], ot["cycle"])
        part = {"yes": "Party label", "no": "No party label", "optional": "Optional label (since 2025)"}.get(ot["partisan"], ot["partisan"])
        otrows.append([ot["label"], cyc, f"{ot['term_years']} years" if ot.get("term_years") else "not in data", part,
                       h("span", None, status_badge(ot["status"], page), cites.cite(ot["source_ids"]))])
    page.add(section("offices", 1, "Which offices are on the ballot, and when",
                     _rule_p(page, ed, "even_year_offices", detail=True),
                     _rule_p(page, ed, "municipal_cycle", detail=True),
                     _rule_p(page, ed, "primary_date", detail=True),
                     h("p", None, "The table lists each local office type with its cycle and term, as recorded in the guide's "
                                  "Indiana-wide office data. ",
                       h("a", {"href": page.rel("elections/calendar/index.html")}, "See the 2026 to 2030 calendar"),
                       " for the seats in this county."),
                     data_table("office-cycles", ["Office", "Cycle", "Term", "Ballot label", "Status"], otrows,
                                caption="Office types, cycles and terms", min_width="40rem"),
                     scope="indiana", ed=ed))

    # ---- primaries
    page.add(section("primaries", 2, "Primaries and getting on the ballot",
                     _rule_p(page, ed, "party_primaries", detail=True),
                     _rule_p(page, ed, "party_nominees_at_convention", detail=True),
                     _rule_p(page, ed, "candidate_forms", detail=True),
                     _rule_p(page, ed, "independent_petitions", detail=True),
                     _low_rules_table(page, ed, ["independent_signature_example"], "primaries-low"),
                     scope="indiana", ed=ed))

    # ---- general + straight ticket
    st_rows = []
    for k in ("straight_party_through_2026", "straight_party_2016_history", "straight_party_from_2027"):
        r = R.get(k)
        if not r:
            continue
        frm = r["effective_from"][:4] if r.get("effective_from") else ""
        if r.get("effective_to"):
            period = f"{frm or 'Start not recorded'} to {r['effective_to'][:4]}"
        else:
            period = f"From {frm} on" if frm else "Start not recorded, still in force"
        badges = h("span", None, status_badge(r["status"], page),
                   (" ", status_badge("low", page)) if r.get("confidence") == "low" else None, cites.cite(r["source_ids"]))
        st_rows.append([period, r["plain_language"], r.get("statute", ""), badges])
    page.add(section("general", 3, "The general election and straight-ticket voting",
                     _rule_p(page, ed, "general_election_date", detail=True),
                     h("h3", None, "Straight-ticket (straight-party) voting"),
                     _rule_p(page, ed, "straight_party_through_2026"),
                     _rule_p(page, ed, "straight_party_from_2027", detail=True),
                     data_table("straight-party-rules", ["Period", "What a straight-party mark covers", "Statute", "Status"],
                                st_rows, caption="Straight-party rule by period", min_width="40rem"),
                     h("p", {"class": "muted"}, "The low-confidence row is kept for completeness; it is why the guide shows "
                                                "straight-party shares only for years whose rule is sourced (",
                       h("a", {"href": page.rel("elections/landscape/index.html#straight-party")}, "Elections by the numbers"), ")."),
                     scope="indiana", ed=ed))

    # ---- voting
    page.add(section("voting", 4, "How to vote: registration, early voting, mail ballots and ID",
                     h("h3", None, "Registering"), _rule_p(page, ed, "voter_registration_deadline", detail=True),
                     h("h3", None, "Early voting in person"), _rule_p(page, ed, "early_voting_period", detail=True),
                     h("h3", None, "Voting by mail"), _rule_p(page, ed, "absentee_by_mail_reasons", detail=True),
                     _rule_p(page, ed, "absentee_application_deadline", detail=True),
                     _rule_p(page, ed, "absentee_application_id", detail=True),
                     h("h3", None, "Photo ID at the polls"), _rule_p(page, ed, "photo_id_at_polls", detail=True),
                     h("h3", None, "How votes are counted"), _rule_p(page, ed, "ranked_choice_ban", detail=True),
                     scope="indiana", ed=ed))

    # ---- county specifics
    e24p, e26g = ed.elections.get("2024p", {}), ed.elections.get("2026g", {})
    contact = ed.source("SVC-017") or {}
    contact_rows = [
        ["Voter registration and Election Board office",
         h("span", {"class": "elx-select"}, "County-City Building, 4th Floor, 227 W. Jefferson Blvd., South Bend, IN 46601"),
         cites.cite("SVC-017")],
        ["Phone", h("span", {"class": "elx-select mono"}, "574-235-9635"), cites.cite("SVC-017")],
        ["Email", h("span", {"class": "elx-select mono"}, "voter@sjcindiana.gov"), cites.cite("SVC-017")],
        ["Candidate questions (Election Board)", h("span", {"class": "elx-select mono"}, "574-235-9635 ext. 7013"),
         cites.cite("SVC-022")],
    ]
    page.add(section("county", 5, "Voting in St. Joseph County",
                     h("p", None, "The county's election-night result files for the May 2024 primary and the November 2026 "
                                  "general are headed as counts of “all absentee and all vote centers.”",
                       cites.cite(_src(e24p, e26g)), " ", status_badge("official", page, "Header text of the county's own files.")),
                     h("p", None, "News reports cited in the guide's research describe about 41 vote centers in November 2024 "
                                  "and a vote-center plan with satellite absentee offices at the County-City Building in South "
                                  "Bend and the County Service Building in Mishawaka, approved by the Election Board on "
                                  "Feb 25, 2026.", cites.cite("ELX-005;ELX-006;IND-022"), " ", status_badge("secondary", page),
                       " Check the current list of sites with the county before you go."),
                     h("p", None, "The County Election Board has three members: one Democrat, one Republican, and the County "
                                  "Clerk as secretary. It runs county and municipal elections, including candidate filings.",
                       cites.cite("SVC-007;SVC-022"), " ", status_badge("official", page)),
                     h("h3", None, "Election office contacts"),
                     h("p", {"class": "muted"}, "Shown as text you can select and copy."),
                     data_table("election-contacts", ["What", "Contact", "Source"], contact_rows,
                                caption="County election office", copy=True),
                     scope="county", ed=ed))

    # ---- vacancies
    current = []
    for o in ed.tables["offices"]:
        if o.get("elected") != "yes":
            continue
        for t in _holders_now(ed, o["office_id"]):
            current.append((o, t))
    by = {}
    for o, t in current:
        by.setdefault(t.get("first_selected_by") or "unknown", []).append((o, t))
    n_all = len(current)
    n_cau = len(by.get("caucus", []))
    n_app = len(by.get("appointment", []))
    vac_rows = []
    for o, t in sorted(by.get("caucus", []) + by.get("appointment", []), key=lambda x: (_place_order(ed, x[0]), x[0]["office_id"])):
        vac_rows.append([o["title"], t["person"], _plabel(t.get("party")),
                         SELECTED_BY_LABELS.get(t["first_selected_by"], t["first_selected_by"]),
                         fmt_date(t["start"]), SELECTED_BY_LABELS.get(t["selected_by"], t["selected_by"]),
                         h("span", None, status_badge(t["status"], page),
                           (" ", status_badge("low", page)) if t.get("confidence") == "low" else None, cites.cite_compact(t["source_ids"]))])
    page.add(section("vacancies", 6, "How vacancies are filled, and why it matters",
                     _rule_p(page, ed, "local_vacancy_caucus", detail=True),
                     _rule_p(page, ed, "legislative_vacancy_caucus", detail=True),
                     _low_rules_table(page, ed, ["precinct_committeepersons"], "vacancies-low"),
                     h("h3", None, "Why it matters"),
                     h("p", None, "A caucus fills a seat between elections without a public vote: the choice is made by the "
                                  "departing official's party committeepersons. The person chosen can then run as the incumbent. "
                                  f"Of the {n_all} current holders of elected offices in the guide's data on "
                                  f"{fmt_date(ed.as_of, long=True)}, {n_cau} first took that office through a party caucus and "
                                  f"{n_app} by appointment. ", status_badge("computed", page, "Counted from terms.csv first_selected_by."),
                       " ", h("a", {"href": page.rel("elections/landscape/index.html#how-took-office")}, "How every incumbent took office")),
                     data_table("caucus-incumbents", ["Office", "Holder", "Party", "First took office by", "Since",
                                                      "Current term by", "Status"], vac_rows,
                                caption="Current officeholders who first took office by caucus or appointment",
                                min_width="46rem"),
                     h("p", {"class": "muted"}, "Listed by office, not by party."),
                     scope="indiana", ed=ed))

    # ---- school boards
    page.add(section("school-boards", 7, "School-board party labels (SEA 287)",
                     _rule_p(page, ed, "partisan_school_board", detail=True),
                     _rule_p(page, ed, "school_board_ballot_order", detail=True),
                     h("p", None, "Straight-party marks do not count for school board races, before or after the 2027 change.",
                       cites.cite(_src(R.get("straight_party_through_2026", {}), R.get("straight_party_from_2027", {})))),
                     h("p", {"class": "muted"}, "The guide does not yet count the labels used on this county's 2026 ballot: its "
                                                "results data and its research notes disagree (see Gaps)."),
                     scope="indiana", ed=ed))

    # ---- direct democracy
    page.add(section("questions", 8, "No citizen initiative or recall",
                     _rule_p(page, ed, "no_citizen_initiative", detail=True),
                     _rule_p(page, ed, "school_and_local_referendums", detail=True),
                     h("p", None, h("a", {"href": page.rel("elections/judges-and-questions/index.html#questions")},
                                    "Every public question on this county's ballots, 2010 to 2026")),
                     scope="indiana", ed=ed))

    # ---- candidate info
    links = [("SVC-019", "County Candidate Filings page: declarations, precinct-committee filings and local campaign-finance reports."),
             ("SVC-007", "County Election Board candidate information."),
             ("ELX-002", "County sample ballots for the November 2026 election, by precinct."),
             ("RES-030", "County election results archive (the canvass files this guide uses)."),
             ("ELX-007", "Indiana Secretary of State candidate information and forms.")]
    items = []
    for sid, what in links:
        s = ed.source(sid) or {}
        items.append(h("li", None, h("a", {"href": s.get("url", "#"), "target": "_blank", "rel": "noopener"}, s.get("title", sid)),
                       " ", h("span", {"class": "muted"}, what), cites.cite(sid)))
    page.add(section("candidate-info", 9, "Where to find candidate information",
                     h("p", None, "These are official places to look up who filed to run and what will be on your ballot. "
                                  "The guide does not list candidates for future elections."),
                     h("ul", {"class": "link-list"}, items),
                     scope="county", ed=ed))

    page.finish(gaps=_gaps(ed, "elections-how") + _gaps(ed, "elections-schools")
                + _gaps(ed, None, ["gaps_indiana"], r"filing|petition|precinct|initiative|referend|signature"))
    return page


def _school_labels(ed):
    counts: dict[str, int] = {}
    for c in ed.contests.values():
        if c["election_id"] != "2026g":
            continue
        g, _, _ = classify(c)
        if g != "School boards":
            continue
        for r in c["rows"]:
            k = r["party"] or "none"
            counts[k] = counts.get(k, 0) + 1
    return counts


def _school_label_table(page, ed, counts):
    if not counts:
        return None
    order = ["D", "R", "L", "I", "NP", "none"]
    keys = [k for k in order if k in counts] + sorted(k for k in counts if k not in order)
    total = sum(counts.values())
    rows = [[{"none": "No label recorded"}.get(k, party_label(k)), str(counts[k]), f"{100 * counts[k] / total:.0f}%"] for k in keys]
    src = _src(*[r for c in ed.contests.values() if c["election_id"] == "2026g" for r in c["rows"][:1]
                 if classify(c)[0] == "School boards"])
    return h("div", None,
             h("p", None, f"On the 2026 general ballot in this county, {total} school-board candidate lines carried these labels. ",
               status_badge("computed", page, "Counted from results.csv."), " ", status_badge("unofficial", page),
               page.cites.cite_compact(src)),
             data_table("school-labels-2026", ["Label on the ballot", "Candidates", "Share"], rows,
                        caption="2026 school-board candidates by ballot label", numeric=(1, 2)))


# =========================================================================== 2. calendar

def _calendar_items(ed):
    """{year: [item]} where item = {level, label, seats, office, src, status}."""
    items = {y: [] for y in YEARS}
    unscheduled = []
    for o in ed.tables["offices"]:
        if o.get("elected") != "yes":
            continue
        unit = ed.units.get(o["unit_id"], {})
        level = unit.get("unit_type", "")
        ys = years_on_ballot(o)
        if not ys:
            unscheduled.append(o)
        for y in ys:
            items[y].append({"level": level, "label": o["title"], "seats": _seats(o), "office": o,
                             "src": o["source_ids"], "status": o["status"]})
    rule = ed.rules.get("even_year_offices", {})
    gen = ed.rules.get("general_election_date", {})
    for y in YEARS:
        if y % 2:
            continue
        if y % 4 == 0:
            for lab in ("Governor", "Attorney General"):
                items[y].append({"level": "statewide", "label": lab, "seats": 1, "office": None,
                                 "src": rule.get("source_ids", ""), "status": rule.get("status", "")})
            items[y].append({"level": "federal", "label": "Presidential electors", "seats": None, "office": None,
                             "src": gen.get("source_ids", ""), "status": gen.get("status", "")})
        else:
            for lab in ("Secretary of State", "Treasurer of State", "State Comptroller"):
                items[y].append({"level": "statewide", "label": lab, "seats": 1, "office": None,
                                 "src": rule.get("source_ids", ""), "status": rule.get("status", "")})
    for y in items:
        items[y].sort(key=lambda i: (LEVEL_ORDER.get(i["level"], 99), i["office"]["unit_id"] if i["office"] else "",
                                     i["label"]))
    return items, unscheduled


def _dates(ed, y):
    """(primary, general, how) for a year; known dates from data/sources, others computed from the rule."""
    if y % 2 == 0:
        p = next((e for e in ed.elections.values() if e["date"].startswith(str(y)) and e["type"] == "primary"), None)
        g = next((e for e in ed.elections.values() if e["date"].startswith(str(y)) and e["type"] == "general"), None)
        if p and g:
            return parse_date(p["date"]), parse_date(g["date"]), "data", _src(p, g)
        return (nth_weekday_after(y, 5), nth_weekday_after(y, 11), "computed",
                _src(ed.rules.get("primary_date", {}), ed.rules.get("general_election_date", {})))
    if y == 2027:
        return date(2027, 5, 4), date(2027, 11, 2), "source", "SVC-018"
    return None, None, "none", ""


def build_calendar(site):
    ed = site.ed
    page = site.page("elections/calendar/index.html", banners=False)
    cites = page.cites
    items, unscheduled = _calendar_items(ed)
    toc = [("strip", "Year by year"), ("next", "What's on your next ballot"), ("deadlines", "Deadlines"),
           ("by-year", "Every seat, by year"), ("method", "How this is computed"), ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(_hero(page, "Reference · Elections · Calendar",
                   "Which seats in St. Joseph County are on the ballot in each year from 2026 to 2030. The years are "
                   "computed from each office's next election and term length in the guide's data.",
                   ["county", "indiana"], toc))

    # ---- strip
    cards = []
    for y in YEARS:
        p, g, how, src = _dates(ed, y)
        lv: dict[str, list] = {}
        for it in items[y]:
            lv.setdefault(it["level"], []).append(it)
        lines = []
        for k, lab in LEVELS:
            if k in lv:
                seats = [i["seats"] for i in lv[k]]
                known = sum(s for s in seats if s)
                unk = sum(1 for s in seats if not s)
                n = f"{known} seat{'s' if known != 1 else ''}" if known else ""
                if unk:
                    n = (n + " + " if n else "") + f"{unk} office{'s' if unk != 1 else ''} with seat count not in data"
                if k in ("statewide", "federal"):
                    n = ", ".join(i["label"] for i in lv[k])
                lines.append(h("li", None, h("span", {"class": "elx-lv"}, lab), h("span", {"class": "elx-n mono"}, n)))
        when = []
        if p:
            pre = "Municipal " if y % 2 else ""
            when.append(h("li", None, h("span", {"class": "mono"}, pre + ("primary " if pre else "Primary ")), fmt_date(p)))
            when.append(h("li", None, h("span", {"class": "mono"}, pre + ("general " if pre else "General ")), fmt_date(g)))
        badge = None
        if how == "computed":
            badge = status_badge("computed", page, "Dates from the statutory rule: first Tuesday after the first Monday in May and November.")
        elif how == "source":
            badge = status_badge("official", page, "Indiana Election Division calendar.")
        note = None
        if y == 2026:
            note = h("p", {"class": "elx-yr-note"}, "Held. Results are unofficial until certified. ",
                     h("a", {"href": page.rel("elections/results/index.html")}, "Results"))
        elif y % 2:
            note = h("p", {"class": "elx-yr-note"}, "City and town offices only." if items[y] else
                     "No regular election for any office in the guide's data.")
        cards.append(h("article", {"class": "elx-year" + (" elx-year-past" if y < 2027 else "") + (" elx-year-odd" if y % 2 else ""),
                                   "id": f"y{y}"},
                       h("h3", {"class": "elx-yr"}, str(y)),
                       h("ul", {"class": "elx-when"}, when, cites.cite(src) if src else None, " ", badge) if when else None,
                       note,
                       h("ul", {"class": "elx-lvls"}, lines) if lines else None))
    page.add(section("strip", 1, "Year by year, 2026 to 2030",
                     h("div", {"class": "elx-strip"}, cards),
                     h("p", None, "Seat counts are ", status_badge("computed", page, "From offices.csv next_election and term_years."),
                       ". Statewide and federal lines follow the Indiana-wide cycle rules.",
                       cites.cite(_src(ed.rules.get("even_year_offices", {}), ed.rules.get("general_election_date", {})))),
                     scope="county", ed=ed))

    # ---- next ballot
    nxt = items[2027]
    by_unit: dict[str, list] = {}
    for it in nxt:
        by_unit.setdefault(it["office"]["unit_id"], []).append(it)
    blocks = []
    for uid in sorted(by_unit, key=lambda u: (LEVEL_ORDER.get(ed.units[u]["unit_type"], 99), ed.units[u]["name"])):
        offs = by_unit[uid]
        blocks.append(h("div", {"class": "card elx-next-card", "data-here-unit": uid},
                        h("h3", {"class": "card-title"}, ed.units[uid]["name"]),
                        h("ul", None, [h("li", None, i["label"],
                                         h("span", {"class": "muted"}, f" · {i['seats']} seats") if (i["seats"] or 1) > 1 else None,
                                         cites.cite(i["src"])) for i in offs])))
    p28, g28, _, src28 = _dates(ed, 2028)
    county_28 = [i for i in items[2028] if i["level"] in ("county", "court_system")]
    page.add(section("next", 2, "What's on your next ballot",
                     h("p", None, "The next regular elections are the municipal primary on Tuesday, May 4, 2027 and the "
                                  "municipal general on Tuesday, Nov 2, 2027. Only voters who live in a city or town vote in "
                                  "them.", cites.cite("SVC-018;" + ed.rules.get("municipal_cycle", {}).get("source_ids", ""))),
                     # static/js/here.js fills this from the reader's saved place and marks the matching card
                     h("p", {"class": "here-note", "data-here-note": True, "hidden": True}),
                     h("p", None, "If you live in one of these places, these offices are on your 2027 ballot:",
                       " ", status_badge("computed", page)),
                     h("div", {"class": "card-grid"}, blocks),
                     h("p", {"data-here-uninc": True}, f"If you live outside every city and town, your next regular election in the guide's data is "
                                  f"the primary on {fmt_date(p28, long=True)}, then the general on {fmt_date(g28, long=True)}. "
                                  f"Everyone in the county votes then, including on {len(county_28)} county offices.",
                       " ", status_badge("computed", page, "Dates from the statutory rule."), cites.cite(src28)),
                     h("p", {"class": "muted"}, "Which district seats you vote for depends on your address. ",
                       h("a", {"href": page.rel("your-governments/index.html")}, "Find your governments")),
                     scope="county", ed=ed))

    # ---- deadlines
    reg = ed.rules.get("voter_registration_deadline", {})
    early = ed.rules.get("early_voting_period", {})
    mail = ed.rules.get("absentee_application_deadline", {})
    drows = []
    for y in (2027, 2028, 2030):
        p, g, how, _ = _dates(ed, y)
        for kind, d in (("Primary", p), ("General", g)):
            if not d:
                continue
            drows.append([f"{kind} {fmt_date(d)}", fmt_date(d - timedelta(days=29)), fmt_date(d - timedelta(days=28)),
                          fmt_date(d - timedelta(days=12))])
    rules_src = _src(reg, early, mail)
    page.add(section("deadlines", 3, "Deadlines",
                     h("p", None, "Candidate filing for 2027: a declaration of candidacy (form CAN-42, with a Statement of "
                                  "Economic Interests, CAN-12) for a major-party nomination to a city office, or a town office "
                                  "in a town of 3,500 or more, is due to the county election board by noon on Friday, "
                                  "Feb 5, 2027.", cites.cite("SVC-018"), " ", status_badge("official", page)),
                     h("p", None, "Voter deadlines below are computed from the state rules: registration closes 29 days before "
                                  "an election, early voting in person starts 28 days before, and a mail-ballot application "
                                  "must arrive by 11:59 pm 12 days before.", cites.cite(rules_src), " ",
                       status_badge("computed", page, "Dates counted back from each election day.")),
                     data_table("voter-deadlines", ["Election", "Registration closes", "Early voting starts",
                                                    "Mail application due"], drows,
                                caption="Voter deadlines, computed", min_width="34rem"),
                     callout(h("p", None, "Computed dates can shift when a deadline falls on a weekend or holiday. Confirm with "
                                          "the county election office before relying on them.")),
                     scope="indiana", ed=ed))

    # ---- full table
    trows = []
    for y in YEARS:
        for it in items[y]:
            o = it["office"]
            trows.append([str(y), LEVEL_LABEL.get(it["level"], it["level"]),
                          ed.units.get(o["unit_id"], {}).get("name", "") if o else "Indiana",
                          it["label"], str(it["seats"]) if it["seats"] else "not in data",
                          f"{o['term_years']} years" if o and o.get("term_years") else "",
                          h("span", None, status_badge(it["status"], page), cites.cite_compact(it["src"]))])
    check = _check_2026(ed, items)
    def why(o):
        parts = re.split(r"(?<=[.;])\s+", o.get("notes", ""))
        keep = [x for x in parts if re.search(r"cycle|next election|not printed|depends|seat count|No terms|appear", x, re.I)]
        return " ".join(keep or parts[:1]) or "Not stated in the office notes."
    unsched_rows = [[o["title"], ed.units.get(o["unit_id"], {}).get("name", ""), why(o),
                     cites.cite_compact(o["source_ids"])] for o in unscheduled]
    page.add(section("by-year", 4, "Every seat, by year",
                     data_table("calendar-table", ["Year", "Level", "Government", "Office", "Seats", "Term", "Status"], trows,
                                caption="Offices on the ballot, 2026 to 2030 (computed)", numeric=(0, 4), min_width="46rem"),
                     h("h3", None, "Elected offices without a computed year"),
                     h("p", None, "These offices have no next-election year or term length in the guide's data, so they are "
                                  "not placed on the calendar. Superior Court judges face yes-or-no retention votes instead of "
                                  "races; see ", h("a", {"href": page.rel("elections/judges-and-questions/index.html#retention")},
                                                   "Judges and public questions"), "."),
                     data_table("calendar-unscheduled", ["Office", "Government", "Why (from the office notes)", "Source"],
                                unsched_rows, caption="Not placed on the calendar", min_width="40rem"),
                     scope="county", ed=ed))
    page.add(section("method", 5, "How this is computed",
                     h("p", None, "An office is placed in a year when the year is its recorded next election, or differs from it "
                                  "by a whole number of terms. Example: an office with a next election of 2030 and a four-year "
                                  "term was also on the 2026 ballot."),
                     h("p", None, check, " ", status_badge("computed", page))))
    page.finish(gaps=_gaps(ed, "elections-calendar"))
    return page


def _check_2026(ed, items):
    oids = {i["office"]["office_id"] for i in items[2026] if i["office"]}
    held = {c["office_id"] for c in ed.contests.values() if c["election_id"] == "2026g" and c["office_id"]}
    both = oids & held
    rest = sorted(ed.offices[o]["title"] for o in oids - held)
    return (f"Check against the 2026 results: of {len(oids)} offices the method places in 2026, {len(both)} have a "
            f"2026 general-election contest linked to them in the guide's results data. "
            + (f"The other {len(rest)} have no linked contest: {'; '.join(rest)}. The link from a contest to an office is "
               "derived from the contest name, so an unlinked contest is not necessarily a missing one." if rest else ""))


# =========================================================================== 3. results explorer

def _contest_payload(ed, c):
    group, place, cross = classify(c)
    cands = candidates(c)
    st = contest_status(c["rows"])
    flags = []
    if any(x["low"] for x in cands):
        flags.append("low")
    if any(x["computed"] for x in cands) or any("pct computed" in (r.get("notes") or "") for r in c["rows"]):
        flags.append("pctc")
    notes = "; ".join(dict.fromkeys(r["notes"] for r in c["rows"] if r.get("notes")))[:300]
    return {"id": c["contest_id"], "e": c["election_id"], "l": c["label"], "g": group, "p": place,
            "o": c["office_id"], "vf": c["vote_for"], "pp": c["party_primary"], "s": st, "x": 1 if cross else 0,
            "q": 1 if is_question(c) else 0, "f": flags, "n": notes,
            "c": [[x["name"], x["party"], x["votes"], round(x["pct"], 2) if x["pct"] is not None else None,
                   x["winner"], 1 if x["low"] else 0] for x in cands],
            "src": _src(*c["rows"])}


def build_results(site):
    ed = site.ed
    page = site.page("elections/results/index.html", banners=True)
    cites = page.cites
    els = _elections(ed)
    eids = {e["election_id"] for e in els}
    contests = [c for c in ed.contests.values() if c["election_id"] in eids]
    toc = [("turnout", "Turnout first"), ("by-office", "Results explorer"), ("how-to-read", "How to read the results"),
           ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(_hero(page, "Reference · Elections · Results",
                   f"Every contest in the guide's data from {els[0]['date'][:4]} to {els[-1]['date'][:4]}: "
                   f"{len(els)} elections and {len(contests)} contests from the county's canvass files.",
                   ["county"], toc))

    # ---- turnout
    trows = []
    for e in reversed(els):
        trows.append([_election_name(e), e["scope"], fmt_int(e["registered"]) or "not printed",
                      fmt_int(e["ballots_cast"]) or "not printed",
                      f"{float(e['turnout_pct']):.2f}%" if e.get("turnout_pct") else "not printed",
                      h("span", None, status_badge(e["status"], page), cites.cite(e["source_ids"]))])
    page.add(section("turnout", 1, "Turnout first",
                     h("p", None, "How many registered voters cast a ballot in each election. Municipal elections count only "
                                  "voters in the cities and towns that held them, so their turnout is not on the same base as "
                                  "countywide elections."),
                     data_table("turnout-table", ["Election", "Who could vote", "Registered", "Ballots cast", "Turnout", "Status"],
                                trows, caption="Turnout by election", numeric=(2, 3, 4), min_width="46rem"),
                     h("p", None, h("a", {"href": page.rel("elections/landscape/index.html#turnout")},
                                    "Turnout chart: odd-year municipal vs even-year elections")),
                     scope="county", ed=ed))

    # ---- explorer
    payload_c = [_contest_payload(ed, c) for c in contests]
    payload_c.sort(key=lambda x: (x["e"], GROUP_ORDER.get(x["g"], 99), x["p"], x["l"]))
    src_ids = sorted({s for x in payload_c for s in split_ids(x["src"])})
    num = {sid: i for i, sid in enumerate(src_ids)}
    # compact: repeated strings (notes, groups, places) become indexes into lookup lists
    notes = sorted({x["n"] for x in payload_c if x["n"]})
    places = sorted({x["p"] for x in payload_c})
    n_ix, p_ix = {n: i for i, n in enumerate(notes)}, {p: i for i, p in enumerate(places)}
    for x in payload_c:
        x["src"] = [num[s] for s in split_ids(x["src"])]
        x["g"] = GROUP_ORDER.get(x["g"], len(GROUPS))
        x["p"] = p_ix[x["p"]]
        for k in ("id", "o"):
            del x[k]
        if x["n"]:
            x["n"] = n_ix[x["n"]]
        else:
            del x["n"]
        if not x["f"]:
            del x["f"]
        for k in ("pp", "x", "q"):
            if not x[k]:
                del x[k]
    # register every source so the per-page list carries them; the explorer links to these anchors
    cites.cite_compact(src_ids)
    payload = {
        "elections": [{"id": e["election_id"], "name": _election_name(e), "y": e["date"][:4], "t": e["type"],
                       "s": e["status"], "reg": e["registered"], "bal": e["ballots_cast"], "to": e["turnout_pct"]}
                      for e in els],
        "groups": GROUPS + ["Other"], "places": places, "notes": notes, "contests": payload_c, "parties": PARTY_LABELS,
        "src": [{"id": s, "t": (ed.source(s) or {}).get("title", s)} for s in src_ids],
        "links": {"legislature": page.rel("state/your-legislators/index.html"), "state": page.rel("state/index.html"),
                  "about": page.rel("about/index.html#badges")},
    }
    latest = els[-1]
    years = sorted({e["date"][:4] for e in els}, reverse=True)
    sel = lambda fid, label, opts: h("div", {"class": "field"}, h("label", {"for": fid}, label),
                                     h("select", {"id": fid}, [h("option", {"value": v, "selected": s or None}, t) for v, t, s in opts]))
    picker = h("div", {"class": "picker elx-picker", "role": "group", "aria-label": "Filter results"},
               sel("elx-year", "Year", [("", "All years", False)] + [(y, y, y == latest["date"][:4]) for y in years]),
               sel("elx-election", "Election", [("", "All elections in the year", False)]),
               sel("elx-group", "Office group", [("", "All offices", False)] + [(str(i), g, False) for i, g in enumerate(GROUPS)]),
               sel("elx-place", "Place", [("", "All places", False)]),
               h("p", {"class": "picker-help", "id": "elx-count", "aria-live": "polite"}, ""))
    page.add(section("by-office", 2, "Results explorer",
                     h("p", None, "Pick a year, an election, a group of offices or a place. Candidates appear in ballot order. "
                                  "Every bar uses the same 0 to 100% scale."),
                     picker,
                     h("div", {"id": "elx-results", "class": "elx-results", "data-root": page.rel("index.html")},
                       h("noscript", None, h("p", None, "The explorer needs JavaScript. The county canvass files it is built from are "
                                                        "listed under Sources below, and the guide's tables are on ",
                                                        h("a", {"href": page.rel("data/index.html")}, "Data and sources"), "."))),
                     h("p", {"class": "elx-more-wrap"}, h("button", {"type": "button", "class": "btn", "id": "elx-more", "hidden": True},
                                                          "Show more contests")),
                     json_script("elx-data", payload),
                     scope="county", ed=ed))

    # ---- how to read
    n_linked = sum(1 for c in contests if c["office_id"])
    page.add(section("how-to-read", 3, "How to read the results",
                     h("ul", None,
                       h("li", None, "Status badges: ", status_badge("official", page), " certified or official canvass; ",
                         status_badge("unofficial", page), " election-night or uncertified figures; ",
                         status_badge("from_scan", page), " transcribed from a scanned page; ",
                         status_badge("low", page), " a figure the guide is unsure of."),
                       h("li", None, "Shares marked computed were calculated from the vote counts because the canvass did not "
                                     "print them. ", status_badge("computed", page)),
                       h("li", None, "COUNTY PORTION ONLY: statewide offices, statewide questions, state court retention and "
                                     "legislative districts that extend outside the county. The county tally does not decide them, "
                                     "so no winner is shown, and each links to the guide's state pages. A legislative race in a "
                                     "year when the district lay wholly inside the county (its totals equal the published "
                                     "district totals) is decided by the county tally and is shown like a local race."),
                       h("li", None, "Ballot order: Indiana law orders the parties on the ballot by their vote for Secretary of "
                                     "State in the county at the last election. In 2022 Wells (D) received 34,746 votes and "
                                     "Morales (R) 33,748, so Democrats are listed first on the 2024 and 2026 county ballots.",
                         page.cites.cite("IND-056;RES-023")),
                       h("li", None, "“Elected” and “Majority” come from the source's winner mark. Where the "
                                     "source marks no winner (most multi-seat races with no printed seat count), none is shown."),
                       h("li", None, f"{n_linked} of {len(contests)} contests are linked to an office in the guide's office list; "
                                     "the others are shown by the name printed on the canvass. ",
                         status_badge("computed", page, "The link is derived from the contest id.")),
                       h("li", None, "Federal races and precinct-committee races are not in the guide's data.")),
                     ))
    page.finish(gaps=_gaps(ed, "elections-results", ["gaps_results"]))
    return page


# =========================================================================== 4. judges and questions

def build_judges(site):
    ed = site.ed
    page = site.page("elections/judges-and-questions/index.html", banners=True)
    cites = page.cites
    toc = [("retention", "Judicial retention votes"), ("state-retention", "State court retention"),
           ("questions", "Public questions"), ("school-labels", "School-board party labels"), ("gaps", "Gaps"),
           ("sources", "Sources")]
    page.add(_hero(page, "Reference · Elections · Judges and questions",
                   "The yes-or-no lines at the end of the ballot: whether judges keep their seats, and public questions.",
                   ["indiana", "exception", "county"], toc))

    merit = ed.rules.get("merit_selection_counties", {})
    ret = ed.rules.get("superior_court_retention", {})
    sup_type = ed.office_types.get("superior_court_judge_merit", {})
    supv = variant_slot(
        ed, "superior_court_selection",
        h("span", None, "In most Indiana counties, judges are elected in partisan races. ", merit.get("plain_language", "")),
        {"merit_retention": h("div", None,
                              h("p", None, f"{ed.county_label} is one of these four counties. A nominating commission screens "
                                           "applicants and sends the Governor a short list; the Governor appoints.",
                                cites.cite(merit.get("source_ids"))),
                              h("p", None, ret.get("plain_language", ""), " ", ret.get("detail", ""), cites.cite(ret.get("source_ids")),
                                " ", status_badge(ret.get("status", ""), page)),
                              h("p", None, "How a seat is filled: ", sup_type.get("vacancy_rule", ""),
                                cites.cite(sup_type.get("source_ids"))) if sup_type.get("vacancy_rule") else None)},
        page, merit.get("source_ids"))

    sup = [c for c in ed.contests.values() if classify(c)[0] == "Superior Court retention"]
    sup.sort(key=lambda c: (ed.elections[c["election_id"]]["date"], c["label"]))
    bar_rows, trows = [], []
    for c in sup:
        cands = {x["name"].upper(): x for x in candidates(c)}
        y, n = cands.get("YES"), cands.get("NO")
        if not (y and n and y["votes"] is not None and n["votes"] is not None):
            continue
        tot = y["votes"] + n["votes"]
        share = 100.0 * y["votes"] / tot
        st = contest_status(c["rows"])
        low = y["low"] or n["low"]
        yr = ed.elections[c["election_id"]]["date"][:4]
        who = c["label"].replace("Superior Court retention", "").strip(" :") or "judge not named"
        who = re.sub(r"^\(|\)$", "", who)
        if "names not captured" in who:
            who = "judge names not captured"
        if not low:
            bar_rows.append({"label": f"{yr} · {who[:34]}", "value": share, "display": f"{share:.1f}% yes",
                             "tip": f"{yr} {who}: {y['votes']:,} yes, {n['votes']:,} no ({st})"})
        trows.append([yr, who, fmt_int(y["votes"]), fmt_int(n["votes"]), f"{share:.1f}%",
                      h("span", None, status_badge(st, page), (" ", status_badge("low", page)) if low else None,
                        cites.cite(_src(*c["rows"])))])
    fig = hbar("retention-yes", "Yes share in Superior Court retention votes", bar_rows,
               subtitle=f"Every retention vote in the guide's data, {trows[0][0]} to {trows[-1][0]}" if trows else None,
               note="Yes votes as a share of yes plus no votes. 2012 figures are labelled unofficial in the source; the 2012 "
                    "Manier line is from a scan. Low-confidence lines are left out of the chart and kept in the table.",
               page=page, headers=["Vote", "Yes share"], status="computed") if bar_rows else None
    page.add(section("retention", 1, "Judicial retention votes",
                     h("h3", None, "How Superior Court judges are chosen and kept"), supv,
                     h("h3", None, "Superior Court retention results"),
                     h("p", None, f"{len(trows)} Superior Court retention votes appear on the county's ballots in the guide's "
                                  f"data. In every one, a majority voted yes.", " ",
                       status_badge("computed", page, "Counted from results.csv.")) if trows and all(float(r[4][:-1]) > 50 for r in trows) else None,
                     fig,
                     data_table("retention-table", ["Year", "Judge", "Yes", "No", "Yes share", "Status"], trows,
                                caption="Superior Court retention votes", numeric=(2, 3, 4), min_width="36rem"),
                     scope="county", ed=ed))

    # ---- state retention
    stc = [c for c in ed.contests.values() if classify(c)[0] == "State court retention"]
    stc.sort(key=lambda c: (ed.elections[c["election_id"]]["date"], c["label"]))
    srows = []
    for c in stc:
        cands = {x["name"].upper(): x for x in candidates(c)}
        y, n = cands.get("YES"), cands.get("NO")
        share = (100.0 * y["votes"] / (y["votes"] + n["votes"])) if y and n and y["votes"] and n["votes"] is not None else None
        srows.append([ed.elections[c["election_id"]]["date"][:4], c["label"].replace("Retention: ", ""),
                      fmt_int(y["votes"]) if y else "", fmt_int(n["votes"]) if n else "",
                      f"{share:.1f}%" if share is not None else "",
                      h("span", None, status_badge(contest_status(c["rows"]), page), cites.cite(_src(*c["rows"])))])
    rl = ed.rules.get("retain_justice_labels", {})
    page.add(section("state-retention", 2, "Retention votes for state courts (county portion only)",
                     h("p", None, rl.get("plain_language", ""), " ", rl.get("detail", ""), cites.cite(rl.get("source_ids")), " ",
                       status_badge(rl.get("status", ""), page)),
                     h("p", None, "These votes are decided statewide or across an appellate district, so the county tally below "
                                  "does not show who was retained. Names and courts are as printed on the canvass. ",
                       h("a", {"href": page.rel("state/index.html")}, "State government")),
                     data_table("state-retention-table", ["Year", "Ballot line", "Yes", "No", "Yes share (county)", "Status"],
                                srows, caption="State court retention, St. Joseph County tally", numeric=(2, 3, 4),
                                min_width="40rem"),
                     scope="indiana", ed=ed))

    # ---- public questions
    wording = {
        "2026g-county-public-question-1": (
            "Currently under the Constitution of the State of Indiana a person charged with murder or treason is not "
            "entitled to be released on bail if the proof is evident or the presumption strong. Shall the Constitution of "
            "the State of Indiana be amended to provide that a person charged with an offense other than murder or treason "
            "is not entitled to bail if the proof is evident or the presumption strong and the state proves by clear and "
            "convincing evidence that no release conditions will reasonably protect the safety of any other person or the "
            "community? This question concerns Article [number not read] Section [number not read] of the Constitution of "
            "the State of Indiana.", "ELX-001;ELX-004",
            "From the county's 2026 sample ballot (precinct 010001). The PDF text was decoded; the article and section "
            "numbers could not be read. Ballotpedia names it the Bailable Offenses and Substantial Risk Standard Amendment.",
            "official"),
        "2026g-county-public-question-2": (
            "Shall the Constitution of the State of Indiana be amended to permit the judge of a city or town court to reside "
            "in the county in which the court is located or the bordering county closest to the city or town in which the "
            "court is located? This question concerns Article [number not read] Section [number not read] of the "
            "Constitution of the State of Indiana.", "ELX-001",
            "From the county's 2026 sample ballot (precinct 010001). The PDF text was decoded; the article and section "
            "numbers could not be read.", "official"),
        "2024g-county-public-question-1": (
            "Shall the Constitution of the State of Indiana be amended to remove the state superintendent of public "
            "instruction from the list of officeholders who shall discharge the powers and duties of the governor if the "
            "office of the governor and lieutenant governor are both vacant?", "ELX-003",
            "Statewide wording quoted by the Daily Journal; the county's 2024 sample ballot was not found.", "secondary"),
    }
    qs = [c for c in ed.contests.values() if classify(c)[0] == "Public questions"]
    qs.sort(key=lambda c: (ed.elections[c["election_id"]]["date"], c["label"]), reverse=True)
    qblocks = []
    for c in qs:
        e = ed.elections[c["election_id"]]
        cross = classify(c)[2]
        w = wording.get(c["contest_id"])
        st = contest_status(c["rows"])
        fig = _question_fig(page, c)
        if w:
            words = h("blockquote", {"class": "elx-wording"}, h("p", None, w[0]),
                      h("footer", None, status_badge(w[3], page), " ", w[2], cites.cite(w[1])))
        else:
            words = h("p", {"class": "elx-gapline"}, h("span", {"class": "mono"}, "GAP · "),
                      "The wording of this question is not in the guide's data.")
        qblocks.append(h("article", {"class": "elx-question", "id": f"q-{c['contest_id']}"},
                         h("h3", None, f"{_election_name(e)}: "
                                       f"{re.sub(r' *[(](wording|text) not [^)]*[)]', '', c['label']) if w else c['label']}"),
                         h("p", {"class": "elx-tags"}, status_badge(st, page), " ",
                           h("span", {"class": "elx-xc mono"}, "STATEWIDE · COUNTY PORTION ONLY") if cross else
                           h("span", {"class": "elx-xc mono"}, classify(c)[1].upper())),
                         words, fig))
    page.add(section("questions", 3, "Public questions",
                     h("p", None, f"Every public question on ballots in the county in the guide's data, {len(qs)} in all, newest "
                                  "first. Statewide questions show the county tally only; the statewide result is decided by "
                                  "all counties."),
                     qblocks, scope="county", ed=ed))

    # ---- school labels
    page.add(section("school-labels", 4, "School-board party labels",
                     _rule_p(page, ed, "partisan_school_board"),
                     h("p", {"class": "muted"}, "Labels used on this county's 2026 ballot are not counted yet: the guide's "
                                                "results data and research notes disagree (see Gaps)."),
                     h("p", None, h("a", {"href": page.rel("elections/index.html#school-boards")}, "More on the 2025 change")),
                     scope="indiana", ed=ed))
    page.finish(gaps=_gaps(ed, "elections-judges") + _gaps(ed, "elections-schools") + _gaps(ed, None, ["gaps_results", "gaps_indiana"], r"question|retention|RETAIN|IC 33-33"))
    return page


def _question_fig(page, c):
    cands = candidates(c)
    unoff = contest_status(c["rows"]) == "unofficial"
    notes = []
    if classify(c)[2]:
        notes.append("County tally only; the statewide result is decided by all counties.")
    if any(x["computed"] for x in cands):
        notes.append("Shares computed from the vote counts.")
    for x in cands:
        if x["winner"] == "Y" and unoff:
            x["winner"] = ""
    if unoff:
        notes.append("Unofficial count; no result is marked until certification.")
    return results_bars(f"qbar-{c['contest_id']}", c["label"],
                        [{"name": x["name"], "party": "", "votes": x["votes"], "pct": x["pct"], "winner": x["winner"]} for x in cands],
                        status=contest_status(c["rows"]), note=" ".join(notes) or None, page=page, question=True,
                        cite=page.cites.cite(_src(*c["rows"])))


# =========================================================================== 5. landscape

def _turnout_chart(page, ed, kinds, fid, title, cite):
    els = [e for e in _elections(ed) if e["type"] in kinds]
    pts = []
    for e in els:
        to = _num(e.get("turnout_pct"))
        muni = e["type"] in MUNICIPAL_TYPES
        star = "*" if e["status"] == "unofficial" else ""
        pts.append({"x": e["date"][:4] + star + (" M" if muni and e["type"] != "special" else " S" if e["type"] == "special" else ""),
                    "value": to, "display": f"{to:.1f}%" if to is not None else None,
                    "mark": "m-ink" if muni else "m-accent",
                    "tip": f"{_election_name(e)}: {fmt_int(e['ballots_cast'])} of {fmt_int(e['registered'])} registered"
                           f"{' (unofficial)' if star else ''}" if to is not None else f"{_election_name(e)}: turnout not printed"})
    fig = columns(fid, title, pts, value_fmt=lambda v: f"{v:.0f}%",
                  subtitle=f"{els[0]['date'][:4]} to {els[-1]['date'][:4]}, every election in the guide's data",
                  note="M = odd-year municipal election (only city and town registrants can vote). S = special election "
                       "(one area only). * = unofficial figures. Gray columns are on a smaller base than teal columns, "
                       "so compare them with care.",
                  page=page, headers=["Election", "Turnout"], cite=cite)
    leg = legend([("m-accent", "Even year, countywide (all registered voters)"),
                  ("m-ink", "Odd year or special (only voters in the places voting)")])
    return Markup(str(fig).replace("</figcaption>", "</figcaption>" + str(leg), 1))


def build_landscape(site):
    ed = site.ed
    page = site.page("elections/landscape/index.html", banners=True)
    cites = page.cites
    els = _elections(ed)
    toc = [("turnout", "Turnout: odd vs even years"), ("margins", "Margins in every race"),
           ("up-next", "Up next"), ("how-took-office", "How incumbents took office"),
           ("straight-party", "Straight-party share"), ("rules", "What this page does not do"), ("gaps", "Gaps"),
           ("sources", "Sources")]
    page.add(_hero(page, "Reference · Elections · By the numbers",
                   "The same measures for every race and every party, looking back only: turnout with its base, margins, "
                   "the seats on the next ballots and how each incumbent took office.", ["county"], toc))

    # ---- turnout
    src_all = _src(*els)
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
    page.add(section("turnout", 1, "Turnout: odd vs even years",
                     h("p", None, "Turnout is ballots cast divided by registered voters. In odd years only city and town "
                                  "residents vote, so the base is smaller: about "
                                  f"{fmt_int(min(int(e['registered']) for e in mu if e['registered']))} to "
                                  f"{fmt_int(max(int(e['registered']) for e in mu if e['registered']))} registered voters in the "
                                  "municipal generals, compared with about "
                                  f"{fmt_int(min(int(e['registered']) for e in ev if e['registered']))} to "
                                  f"{fmt_int(max(int(e['registered']) for e in ev if e['registered']))} countywide.",
                       cites.cite_compact(_src(*(ev + mu))), " ", status_badge("computed", page, "Ranges from elections.csv.")),
                     h("div", {"class": "chart-grid elx-charts"}, g_chart, p_chart),
                     data_table("turnout-denominators", ["Election", "Kind", "Who could vote", "Registered", "Ballots cast",
                                                         "Turnout", "Status"], den_rows,
                                caption="Turnout with its denominator", numeric=(3, 4, 5), min_width="50rem"),
                     scope="county", ed=ed))

    # ---- margins
    eids = {e["election_id"] for e in els}
    mrows, n_unc, n_nc, band_n = [], 0, 0, {b[0]: 0 for b in BANDS}
    for c in ed.contests.values():
        if c["election_id"] not in eids:
            continue
        g, place, cross = classify(c)
        if cross or g in ("Straight-party ballots", "Public questions", "Superior Court retention") or is_question(c):
            continue
        m = margin(c)
        if m is None:
            n_unc += 1
            continue
        if "pts" not in m:
            n_nc += 1
            continue
        e = ed.elections[c["election_id"]]
        band_n[m["band"]] += 1
        st = contest_status(c["rows"])
        mrows.append((m["pts"], e["date"], c, m, e, st, g))
    mrows.sort(key=lambda x: (x[0], x[1]))
    trs = []
    for pts, d, c, m, e, st, g in mrows:
        a, b = m["ahead"], m["next"]
        band_label = next(lab for bid, lab, _, _ in BANDS if bid == m["band"])
        attrs = {"data-year": d[:4], "data-type": "primary" if "primary" in e["type"] else "general",
                 "data-band": m["band"], "data-margin": f"{pts:.4f}", "data-date": d}
        cells = [
            h("th", {"scope": "row"}, c["label"],
              h("span", {"class": "elx-sub muted"}, f" · {m['seats']} seats") if m["seats"] > 1 else None),
            h("td", None, _election_name(e)),
            h("td", {"class": "num"}, f"{pts:.2f}"),
            h("td", {"class": "num"}, f"{m['votes']:,}"),
            h("td", None, band_label),
            h("td", None, f"{a['name']} ({a['party'] or 'no party'}) {a['votes']:,}"),
            h("td", None, f"{b['name']} ({b['party'] or 'no party'}) {b['votes']:,}"),
            h("td", None, status_badge(st, page), (" ", status_badge("low", page)) if m["low"] else None),
        ]
        trs.append(h("tr", attrs, cells))
    hdr = ["Contest", "Election", "Margin (points)", "Votes apart", "Band", "Last candidate inside the seats", "Next candidate", "Status"]
    table = h("div", {"class": "table-block"},
              h("div", {"class": "table-wrap", "role": "region", "tabindex": "0", "aria-label": "Margins in every race"},
                h("table", {"id": "margins-table", "class": "data", "style": "min-width: 60rem"},
                  h("caption", None, "Margins in every race decided inside the county, closest first"),
                  h("thead", None, h("tr", None, [h("th", {"scope": "col", "class": "num" if i in (2, 3) else None}, x)
                                                  for i, x in enumerate(hdr)])),
                  h("tbody", None, trs))),
              h("div", {"class": "table-tools"}, h("button", {"type": "button", "class": "btn btn-small",
                                                              "data-copy-table": "margins-table", "id": "margins-table-copy"},
                                                   "Copy CSV")))
    years = sorted({x[1][:4] for x in mrows}, reverse=True)
    picker = h("div", {"class": "picker", "role": "group", "aria-label": "Filter margins"},
               h("div", {"class": "field"}, h("label", {"for": "mg-year"}, "Year"),
                 h("select", {"id": "mg-year"}, h("option", {"value": ""}, "All years"), [h("option", {"value": y}, y) for y in years])),
               h("div", {"class": "field"}, h("label", {"for": "mg-type"}, "Election"),
                 h("select", {"id": "mg-type"}, h("option", {"value": ""}, "Primaries and generals"),
                   h("option", {"value": "general"}, "General elections"), h("option", {"value": "primary"}, "Primaries"))),
               h("div", {"class": "field"}, h("label", {"for": "mg-band"}, "Band"),
                 h("select", {"id": "mg-band"}, h("option", {"value": ""}, "All bands"),
                   [h("option", {"value": bid}, lab) for bid, lab, _, _ in BANDS])),
               h("div", {"class": "field"}, h("label", {"for": "mg-sort"}, "Sort"),
                 h("select", {"id": "mg-sort"}, h("option", {"value": "margin"}, "Closest first"),
                   h("option", {"value": "date"}, "Newest first"))),
               h("p", {"class": "picker-help", "id": "mg-count", "aria-live": "polite"}, f"{len(mrows)} races shown."))
    band_chart = hbar("margin-bands", "Races by margin band", [
        {"label": lab, "value": band_n[bid], "display": f"{band_n[bid]} races"} for bid, lab, _, _ in BANDS],
        subtitle=f"{len(mrows)} contested races, {els[0]['date'][:4]} to {els[-1]['date'][:4]}", page=page,
        headers=["Band", "Races"], status="computed",
        note="Primaries and generals together. Bands are defined above and applied to every race the same way.")
    page.add(section("margins", 2, "Margins in every race",
                     h("div", {"class": "callout elx-def", "id": "bands"},
                       h("p", None, h("strong", None, "How the margin is measured. "),
                         "Margin in points = the votes of the last candidate inside the seats minus the votes of the next "
                         "candidate, divided by all votes cast in that contest. In a one-seat race that is the winner and "
                         "the runner-up. In a race that fills several seats (vote for 3, for example) it compares the "
                         "candidates just inside and just outside the seats. Places are ranked by votes."),
                       h("p", None, h("strong", None, "Bands. "), "Under 5 points; 5 to 15 points; over 15 points. Each race "
                         "is put in a band by its margin alone. The bands describe past results and say nothing about future races.")),
                     h("p", None, f"{len(mrows)} races are listed, closest first, whatever party finished ahead. "
                                  f"{n_unc} uncontested races (no more candidates than seats) and {n_nc} races with missing vote "
                                  "counts or no recorded seat count are not listed. Statewide offices, and legislative districts in "
                                  "years when they extended outside the county, are left out because the county tally doesn't "
                                  "decide them. Retention votes and public questions "
                                  "are yes-or-no votes, not races between candidates; they are on ",
                       h("a", {"href": page.rel("elections/judges-and-questions/index.html")}, "Judges and public questions"),
                       ". ",
                       status_badge("computed", page, "Margins computed from results.csv vote counts.")),
                     band_chart, picker,
                     h("p", {"class": "muted"}, "Vote counts in this table come from the county canvass files listed under Sources.",
                       cites.cite_compact(_src(*[r for x in mrows for r in x[2]["rows"][:1]]))),
                     table,
                     h("p", {"class": "muted"}, "Party codes: ", "; ".join(f"{k} = {v}" for k, v in PARTY_LABELS.items()), "."),
                     scope="county", ed=ed))

    # ---- up next
    items, _ = _calendar_items(ed)
    urows = []
    for y in (2027, 2028):
        for it in items[y]:
            o = it["office"]
            if not o:
                continue
            holders = _holders_now(ed, o["office_id"])
            ot = ed.office_type_row(o) or {}
            if not holders:
                urows.append([str(y), o["title"], "No current officeholder in the guide's data", "", "", "",
                              ot.get("term_limit") or "Not in the guide's data", h("span", None, cites.cite(o["source_ids"]))])
                continue
            for t in holders:
                tl = _term_limit(ed, o, t, y)
                urows.append([str(y), o["title"], t["person"], _plabel(t.get("party")), fmt_date(t["start"]) or "not in sources",
                              SELECTED_BY_LABELS.get(t.get("first_selected_by", ""), t.get("first_selected_by")),
                              h("span", None, tl[0], " ", status_badge("computed", page, tl[1]) if tl[1] else None),
                              h("span", None, status_badge(t["status"], page),
                                (" ", status_badge("low", page)) if t.get("confidence") == "low" else None,
                                cites.cite_compact(t["source_ids"]))])
    page.add(section("up-next", 3, "Up next: seats on the 2027 and 2028 ballots",
                     h("p", None, "Each seat on the next two regular ballots, with the person holding it now, how they first took "
                                  "the office, and the term-limit rule for the office. The years are computed from the office "
                                  "data (", h("a", {"href": page.rel("elections/calendar/index.html")}, "Election calendar"),
                       "). Announced retirements and declared candidates are not collected."),
                     _rule_p(page, ed, "county_row_office_term_limits", detail=True),
                     data_table("up-next-table", ["Year", "Seat", "Holder now", "Party", "In office since",
                                                  "First took office by", "Term-limit status", "Status"], urows,
                                caption="Seats on the 2027 and 2028 ballots", min_width="60rem"),
                     h("p", {"class": "muted"}, "Term-limit status is computed only for the six offices on the 8-in-12 list, "
                                                "from the guide's terms data; service chosen by caucus to fill a vacancy is not "
                                                "counted, as the rule says. Listed by year and office, never by party."),
                     scope="county", ed=ed))

    # ---- how took office
    cur = []
    for o in ed.tables["offices"]:
        if o.get("elected") != "yes":
            continue
        for t in _holders_now(ed, o["office_id"]):
            cur.append((o, t))
    cur.sort(key=lambda x: (_place_order(ed, x[0]), x[0]["office_id"]))
    cnt: dict[str, int] = {}
    hrows = []
    for o, t in cur:
        k = t.get("first_selected_by") or "unknown"
        cnt[k] = cnt.get(k, 0) + 1
        hrows.append([o["title"], t["person"], _plabel(t.get("party")), SELECTED_BY_LABELS.get(k, k),
                      SELECTED_BY_LABELS.get(t.get("selected_by") or "unknown", t.get("selected_by")),
                      fmt_date(t["start"]) or "not in sources",
                      h("span", None, status_badge(t["status"], page),
                        (" ", status_badge("low", page)) if t.get("confidence") == "low" else None, cites.cite_compact(t["source_ids"]))])
    order = ["election", "caucus", "appointment", "unknown"]
    hb = hbar("took-office", "How current officeholders first took office",
              [{"label": SELECTED_BY_LABELS[k].capitalize(), "value": cnt.get(k, 0), "display": f"{cnt.get(k, 0)} people"}
               for k in order],
              subtitle=f"{len(cur)} people holding elected offices in the guide's data on {fmt_date(ed.as_of)}",
              headers=["How first chosen", "People"], status="computed", page=page,
              note="Counted from the first_selected_by field of each current term. 'Not stated in sources' means the "
                   "sources don't say how the person first took the office.")
    page.add(section("how-took-office", 4, "How incumbents took office",
                     h("p", None, "Every current officeholder, by office, with how they first took the office (election, party "
                                  "caucus or appointment) and how they got their current term. The same field is shown for "
                                  "everyone."),
                     hb,
                     data_table("took-office-table", ["Office", "Holder", "Party", "First took office by", "Current term by",
                                                      "Since", "Status"], hrows,
                                caption="Current officeholders and how they took office", min_width="52rem"),
                     scope="county", ed=ed))

    # ---- straight party
    sourced = _straight_party_years(ed)
    sp_rows = []
    for e in els:
        if e["type"] != "general" or not e.get("straight_party_d"):
            continue
        y = int(e["date"][:4])
        if y not in sourced:
            continue
        bal = int(e["ballots_cast"])
        d, r, o = (int(e[k] or 0) for k in ("straight_party_d", "straight_party_r", "straight_party_other"))
        tot = d + r + o
        sp_rows.append((e, bal, d, r, o, tot))
    blocks = []
    for e, bal, d, r, o, tot in sp_rows:
        blocks.append(h("div", None,
                        h("p", None, f"In the {_election_name(e)}, {tot:,} of {bal:,} ballots ({100 * tot / bal:.1f}%) used a "
                                     "straight-party mark.", cites.cite(e["source_ids"]), " ", status_badge(e["status"], page), " ",
                          status_badge("computed", page, "Straight-party ballots divided by ballots cast.")),
                        data_table(f"straight-{e['election_id']}", ["Straight-party mark", "Ballots", "Share of all ballots"],
                                   [[party_label("D"), f"{d:,}", f"{100 * d / bal:.1f}%"],
                                    [party_label("R"), f"{r:,}", f"{100 * r / bal:.1f}%"],
                                    ["Other parties", f"{o:,}", f"{100 * o / bal:.1f}%"]],
                                   caption=f"Straight-party ballots, {e['date'][:4]}", numeric=(1, 2))))
    page.add(section("straight-party", 5, "Straight-party share",
                     h("p", None, "A share is shown only for years where the guide has a sourced rule for what a straight-party "
                                  "mark covered. ", f"Years with a sourced rule: {', '.join(map(str, sorted(sourced))) or 'none'}. ",
                       "The rule in force through 2026 comes from the statute text read in 2026; the year it began is low "
                       "confidence, so earlier years are not shown even though the county printed their totals. ",
                       h("a", {"href": page.rel("elections/index.html#general")}, "The straight-party rules")),
                     blocks,
                     h("p", {"class": "muted"},
                       "The county also printed straight-party totals for the general elections of " +
                       ", ".join(sorted({e["date"][:4] for e in els if e["type"] == "general" and e.get("straight_party_d")
                                         and int(e["date"][:4]) not in sourced})) +
                       ". They are in the guide's data files and will be shown here once the rule for those years is sourced."),
                     scope="county", ed=ed))

    page.add(section("rules", 6, "What this page does not do",
                     h("ul", None,
                       h("li", None, "No forecasts and no labels about future races. Everything here describes past results and "
                                     "current rules."),
                       h("li", None, "No party filter. Every view covers every party the same way."),
                       h("li", None, "No precinct maps, voter-file data or donor details. Precinct files are linked on ",
                         h("a", {"href": page.rel("data/index.html")}, "Data and sources"), "."))))
    page.finish(gaps=_gaps(ed, "elections-landscape", ["gaps_results"], r"winner|seat count|multi-seat|2026 general"))
    return page


def _straight_party_years(ed) -> set[int]:
    """Years Y for which a straight-party rule row (not low confidence) is sourced: effective_from <= Y <= effective_to.
    A blank effective_from means the start isn't known, so the rule counts only for the year it was read."""
    out = set()
    for r in ed.table("election_rules"):
        if r["topic"] != "straight_party" or r.get("confidence") == "low":
            continue
        start = int(r["effective_from"][:4]) if r.get("effective_from") else ed.as_of.year
        end = int(r["effective_to"][:4]) if r.get("effective_to") else ed.as_of.year
        for y in range(start, min(end, ed.as_of.year) + 1):
            out.add(y)
    return out


def _term_limit(ed, office, term, year) -> tuple[str, str]:
    """(text, computed-note). Applies the 8-in-12 rule mechanically from terms.csv."""
    ot = ed.office_type_row(office) or {}
    if office["office_type"] not in LIMIT_8_IN_12:
        return (ot.get("term_limit") or "Not in the guide's data"), ""
    w_end = date(year, 12, 31)
    w_start = date(year - 11, 1, 1)
    all_terms = ed.terms_for(office["office_id"])
    first = min((parse_date(t["start"]) for t in all_terms if parse_date(t["start"])), default=None)
    if first is None or first > w_start:
        return (f"Can't compute: the guide's terms for this office start in {first.year if first else 'an unknown year'}",
                "Needs terms covering the 12 years before the seat's next election.")
    days = 0
    for t in all_terms:
        if t["person"] != term["person"] or t.get("selected_by") == "caucus":
            continue
        s = parse_date(t["start"])
        e = ed.term_end(t) or w_end
        lo, hi = max(s, w_start), min(e, w_end)
        if hi >= lo:
            days += (hi - lo).days + 1
    yrs = days / 365.25
    if yrs >= 7.9:
        return (f"Will have served 8 of the 12 years {w_start.year} to {year} when this term ends, the most the rule allows",
                "8-in-12 rule applied to the terms data.")
    return (f"About {yrs:.0f} of 8 years served in {w_start.year} to {year} by the end of this term",
            "8-in-12 rule applied to the terms data.")


PAGES = {
    "elections/index.html": build_index,
    "elections/calendar/index.html": build_calendar,
    "elections/results/index.html": build_results,
    "elections/judges-and-questions/index.html": build_judges,
    "elections/landscape/index.html": build_landscape,
}
