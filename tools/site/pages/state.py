"""State government pages: state/index.html, state/your-legislators/index.html,
state/how-the-state-shapes-local/index.html."""
from __future__ import annotations

import re
from collections import defaultdict

from civic.charts import columns, results_bars
from civic.components import (bodies_block, name_with_party, callout, data_table, officeholder_card, party_label, scope_badge, section,
                              status_badge)
from civic.data import PARTY_LABELS, fmt_date, parse_date, split_ids
from civic.html import h, join
from civic.seat_split import seat_split

IGA_URL = "https://iga.in.gov/"
CONTEST_RX = re.compile(r"^(\d{4})g-state-(house|senate)-(\d+)$")
SELECTED_EXTRA = {"succession": "succeeded after a death in office"}


# ---------------------------------------------------------------------------- helpers

def _plabel(code: str) -> str:
    return party_label(code) if (code or "") in PARTY_LABELS else "No party listed"


def _hero(page, eyebrow: str, h1: str, dek, scopes: list, toc: list[tuple[str, str]]):
    page.add(h("header", {"class": "page-hero"},
               h("p", {"class": "eyebrow mono"}, eyebrow),
               h("h1", None, h1),
               h("p", {"class": "dek"}, dek),
               h("p", {"class": "hero-badges"}, [[s, " "] for s in scopes]),
               h("nav", {"class": "toc", "aria-label": "On this page"},
                 h("ol", None, [h("li", None, h("a", {"href": f"#{a}"}, t)) for a, t in toc]))))


ABBREV_END = re.compile(r"(\b(sec|Sec|Art|Ind|No|Ct|App|Gov|Rep|Sen|St|Jan|Feb|Mar|Apr|Aug|Sept|Oct|Nov|Dec|v|vs)|U\.S|P\.L)\.$")


def _sentences(text: str) -> list[str]:
    """Whole sentences: split after a period followed by a capital, but not after an abbreviation such as
    'Art.' or 'sec.', so a dropped sentence never leaves a fragment behind."""
    out = []
    for part in re.split(r"(?<=\.)\s+(?=[A-Z0-9])", text or ""):
        if out and ABBREV_END.search(out[-1]):
            out[-1] += " " + part
        else:
            out.append(part)
    return [p.strip() for p in out if p.strip()]


def _clean_detail(text: str) -> str:
    """Drop sentences that talk about the guide's own research process; keep the caveats about the law."""
    keep = [s for s in _sentences(text) if not re.search(r"\bthe research\b|research'?s?\b", s, re.I)]
    out = " ".join(keep).strip()
    if out.endswith(";"):
        out = out[:-1] + "."
    return out


def _money(v: float) -> str:
    return f"${v:,.0f}"


def _holder_line(page, t: dict, show_when: bool = True):
    low = t.get("confidence") == "low"
    return h("div", {"class": "state-holder"},
             h("strong", None, t["person"]), " ", h("span", {"class": "mono muted"}, _plabel(t.get("party"))),
             page.cites.cite(t.get("source_ids")), " ",
             status_badge(t.get("status"), page), " ", status_badge("low", page) if low else None)


def _rule_block(page, ed, key: str, heading: str | None = None, detail: bool = True, extra=None):
    r = ed.local_rules[key]
    meta = []
    if r.get("statute"):
        meta.append(f"Statute: {r['statute']}")
    if r.get("effective"):
        meta.append(f"Effective: {fmt_date(r['effective'])}")
    det = _clean_detail(r.get("detail", "")) if detail else ""
    return h("div", {"class": "rule-block"},
             h("h3", None, heading) if heading else None,
             h("p", None, r["plain_language"], page.cites.cite(r["source_ids"]), " ",
               status_badge(r["status"], page), " ", status_badge("low", page) if r.get("confidence") == "low" else None),
             h("p", {"class": "muted"}, det) if det else None,
             extra,
             h("p", {"class": "rule-meta mono muted"}, " · ".join(meta)) if meta else None)


# ============================================================================ state/index.html

def _office_key(name: str) -> str:
    """statewide_offices and statewide_terms name the same office slightly differently, e.g. 'State Comptroller
    (formerly Auditor of State)' vs 'State Comptroller (Auditor of State)': compare without the parenthetical."""
    return re.sub(r"\s*\(.*?\)", "", name or "").strip().lower()


def _statewide_split(ed, office: str):
    cur, inc = [], []
    for t in ed.table("statewide_terms"):
        if _office_key(t["office"]) != _office_key(office):
            continue
        start = parse_date(t["start"])
        end = parse_date(t["end"], end=True) if t["end"] else None
        if t["status"] == "unofficial" or (start and start > ed.as_of):
            inc.append(t)
        elif start and start <= ed.as_of and (end is None or end >= ed.as_of):
            cur.append(t)
    return cur, inc


def _control_rows(ed, chamber: str):
    out = []
    for r in ed.table("general_assembly_control"):
        if r["chamber"] != chamber:
            continue
        y = int(r["year"])
        num = lambda k: int(r[k]) if r.get(k, "").strip() != "" else None
        out.append({"label": f"{y}-{str(y + 1)[2:]}", "d": num("d_seats"), "r": num("r_seats"),
                    "other": num("other_seats"), "status": r["status"], "super_party": r["supermajority_party"],
                    "source_ids": r["source_ids"], "notes": r["notes"], "year": y})
    out.sort(key=lambda x: x["year"])
    return out


def build_state(site):
    ed = site.ed
    page = site.page("state/index.html", banners=True)
    c = page.cites
    offices = ed.table("statewide_offices")
    n_elected = sum(1 for o in offices if o["elected_or_appointed"] == "elected")
    toc = [("offices", "Statewide offices"), ("governors", "Governors"), ("assembly", "General Assembly"),
           ("control", "Party control over time"), ("bills", "How a bill becomes law"), ("next", "Where to go next"),
           ("gaps", "Gaps"), ("sources", "Sources")]
    _hero(page, "Reference · State", "State government",
          f"Indiana elects {n_elected} statewide officers and a 150-member General Assembly. This page shows who "
          "holds each office, how the legislature is organized, and how party control of each chamber has changed.",
          [scope_badge("indiana", ed), scope_badge("county", ed)], toc)

    # ---------------------------------------------------------------- 1 offices
    rows = []
    for o in offices:
        cur, inc = _statewide_split(ed, o["office"])
        cur_cell = [_holder_line(page, t) for t in cur] or [h("span", {"class": "muted"}, "No holder in the guide's data")]
        inc_cell = []
        for t in inc:
            inc_cell.append(h("div", {"class": "state-holder"}, _holder_line(page, t),
                              h("div", {"class": "muted"}, f"Takes office {fmt_date(t['start'])} (results unofficial)")))
        term_note = re.search(r"term ends (?:[A-Za-z]+ )?(\d{4})", (cur[0]["notes"] if cur else ""), re.I)
        if not inc_cell:
            if o["elected_or_appointed"] != "elected":
                msg = "Not elected (appointed)"
            elif term_note and int(term_note.group(1)) > 2027:
                msg = "Not on the 2026 ballot"
            else:
                msg = "No 2026 winner in the guide's data"
            inc_cell = [h("span", {"class": "muted"}, msg)]
        rows.append([o["office"],
                     h("span", None, o["what_it_does"], c.cite(o["source_ids"]), " ", status_badge(o["status"], page)),
                     f"{o['term_years']}" + (f". Current term ends {term_note.group(0)[10:].strip()}." if term_note else ""),
                     "Elected" if o["elected_or_appointed"] == "elected" else "Appointed by the Governor",
                     h("div", None, cur_cell), h("div", None, inc_cell)])
    page.add(section("offices", 1, "Statewide offices and who holds them",
                     h("p", None, "Statewide officers are chosen by voters in every county. Officeholders are listed by office, "
                                  "not by party. Winners of the Nov 3, 2026 general election are marked unofficial until the "
                                  "state certifies results; their terms start in January 2027."),
                     data_table("statewide-offices", ["Office", "What it does", "Term (years)", "How filled", "Holder now",
                                                      "Elected 2026 (takes office 2027)"],
                                rows, caption="Indiana statewide offices", min_width="56rem"),
                     scope="indiana", ed=ed))

    # ---------------------------------------------------------------- 2 governors
    gov = [t for t in ed.table("statewide_terms") if t["office"] == "Governor"]
    gov.sort(key=lambda t: parse_date(t["start"]) or parse_date("1900"))
    grows = []
    for t in gov:
        year_only = len(t["start"]) == 4
        basis = "Start and end years only; no primary source cited" if year_only else "Exact start date"
        extra = re.sub(r"Start year only is sourced; exact inauguration date not recorded\.\s*", "", t["notes"]).strip()
        if t["end"] == "":
            m = re.search(r"Term ends [A-Za-z]+ \d{4}\.", t["notes"])
            extra = m.group(0) if m else ""
        sel = SELECTED_EXTRA.get(t["selected_by"], t["selected_by"])
        grows.append([h("span", None, t["person"], c.cite(t["source_ids"])), _plabel(t["party"]),
                      f"{fmt_date(t['start'])} to {fmt_date(t['end']) if t['end'] else 'present'}",
                      sel.capitalize(), basis, extra,
                      status_badge(t["status"], page)])
    page.add(section("governors", 2, "Governors since 1945",
                     h("p", None, "The list starts at 1945, the earliest year the guide sourced. For every governor before "
                                  "2025 only the start and end years are recorded. A cross-check against the standard "
                                  "record (the fact-check pass) matched these years, but the check was not tied to a "
                                  "primary source, so the rows are marked secondary and the dates are shown as years. ",
                       "The Governor serves a four-year term and may serve no more than 8 years in any 12.",
                       c.cite("IND-008;IND-020;IND-027")),
                     data_table("governors", ["Governor", "Party", "Years", "How took office", "Date basis", "Notes", "Status"],
                                grows, caption="Indiana governors, 1945 to present", min_width="50rem"),
                     scope="indiana", ed=ed))

    # ---------------------------------------------------------------- 3 assembly
    rule_keys = ["size_and_terms", "session_length", "organization_day", "quorum_two_thirds", "veto_override",
                 "legislative_vacancy_caucus"]
    arows = []
    for k in rule_keys:
        r = ed.rules[k]
        det = _clean_detail(r["detail"])
        arows.append([r["rule_key"].replace("_", " ").capitalize(),
                      h("span", None, r["plain_language"], c.cite(r["source_ids"])),
                      det, status_badge(r["status"], page)])
    page.add(section("assembly", 3, "How the General Assembly is organized",
                     h("p", None, "Indiana's legislature has two chambers. Members in both are elected from single-member "
                                  "districts drawn by the state."),
                     data_table("assembly-rules", ["Rule", "What it says", "Details and caveats", "Status"], arows,
                                caption="General Assembly structure and rules", min_width="48rem"),
                     h("p", None, "Five House districts (5, 6, 7, 8 and 21) and four Senate districts (8, 9, 10 and 11) "
                                  "include part of St. Joseph County. ",
                       h("a", {"href": page.rel("state/your-legislators/index.html")}, "See who holds them"), "."),
                     scope="indiana", ed=ed))

    # ---------------------------------------------------------------- 4 control
    house, senate = _control_rows(ed, "House"), _control_rows(ed, "Senate")
    figs = []
    for chamber, rws, total, two_thirds, sids in (("House", house, 100, 67, "IND-034;IND-027"),
                                                  ("Senate", senate, 50, 34, "IND-035;IND-027")):
        notes = [f"{r['label']}: {r['notes']}" for r in rws if r["notes"] and r["d"] is None]
        figs.append(seat_split(f"control-{chamber.lower()}", f"Indiana {chamber}: seats by party",
                               rws, total, two_thirds,
                               subtitle=f"{rws[0]['label']} to {rws[-1]['label']}, {total} seats. Counts are as of the start of each period.",
                               note="* The 2027 counts are blank on purpose: results are unofficial and the guide's sources "
                                    "disagree. They will be filled in from certified results.",
                               page=page, cite=c.cite(sids)))
    page.add(section("control", 4, "Party control over time", figs,
                     h("p", None, "Each bar shows seats by party at the start of a two-year period. The line marks two-thirds "
                                  "of the chamber (67 of 100 in the House, 34 of 50 in the Senate)."),
                     h("p", None, "For the 2027 period, the Indiana Capital Chronicle reported on Nov 3, 2026 that Republicans "
                                  "fell below 67 House seats in the 2026 election, and that Democrats gained at least four Senate "
                                  "seats. Both statements are unofficial.", c.cite("IND-028;IND-027"), " ",
                       status_badge("unofficial", page)),
                     h("p", {"class": "muted"}, "In the 2025-26 House row the count is the one at the start of the period. "
                                                "By November 2026 the source's roster lists 69 Republicans, 30 Democrats and "
                                                "1 independent. The 2023-24 Senate source table is garbled (39 or 40 Republicans); "
                                                "either count is above 34.", c.cite("IND-034;IND-035")),
                     scope="indiana", ed=ed))

    # ---------------------------------------------------------------- 5 bills
    page.add(section("bills", 5, "How a bill becomes law",
                     h("p", None, "A bill passes both chambers and goes to the Governor, who can sign or veto it. "
                                  "The Governor's veto can be overridden by a majority of all members elected to each chamber.",
                       c.cite(ed.rules["veto_override"]["source_ids"]), " ",
                       "The step-by-step process, with current bills and committee schedules, is on the General Assembly's "
                       "own website: ",
                       h("a", {"href": IGA_URL, "target": "_blank", "rel": "noopener"}, "iga.in.gov"), "."),
                     scope="indiana", ed=ed))

    page.add(section("next", 6, "Where to go next",
                     h("ul", None,
                       h("li", None, h("a", {"href": page.rel("state/your-legislators/index.html")}, "Your legislators"),
                         ": the House and Senate districts that include part of the county."),
                       h("li", None, h("a", {"href": page.rel("state/how-the-state-shapes-local/index.html")},
                                       "How the state shapes local government"),
                         ": home rule, property tax caps, SEA 1 and local income tax changes.")),
                     ed=ed))

    gaps = ed.gaps(files=["gaps_indiana"], pattern=r"statewide|Jenner|Speaker|2026 statewide|2027 House|Composition tables|inauguration|Duties of the Lieutenant")
    gaps += ed.gaps(files=["gaps_indiana"], pattern=r"Legislative-day limits|Art\. 5 sec\. 14|Art\. 6 sec\. 2|convention nominees")
    page.finish(gaps=_dedupe(gaps))
    return page


def _dedupe(rows):
    seen, out = set(), []
    for r in rows:
        key = (r.get("area"), r.get("item"))
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


# ============================================================================ your-legislators

def _district_sort(key):
    chamber, num = key
    return (0 if chamber == "house" else 1, int(num))


def _result_scope(r: dict) -> str:
    n = r.get("notes", "")
    if "district lies wholly in the county" in n:
        return "Whole district (county totals equal Ballotpedia's district totals)"
    if "Ballotpedia district-wide" in n:
        return "District-wide total from Ballotpedia, not the county tally"
    return "County portion only"


def _result_text(r: dict, scope: str) -> str:
    n = r.get("notes", "")
    w = r.get("winner", "")
    if scope.startswith("County portion"):
        if w == "Y" and "leads within" in n:
            return "Led the county tally"
        if w == "N" and "winner derived" in n:
            return "Trailed in the county tally"
        return "Not determined"
    if r.get("status") == "unofficial":
        return {"Y": "Leads (unofficial)", "N": "Trails (unofficial)"}.get(w, "Not recorded")
    return {"Y": "Elected", "N": "Not elected"}.get(w, "Not recorded")


def build_legislators(site):
    ed = site.ed
    page = site.page("state/your-legislators/index.html", banners=True)
    c = page.cites
    county = ed.county_label
    hos = [o for o in ed.offices_for("in-house")]
    sos = [o for o in ed.offices_for("in-senate")]
    toc = [("districts", "Districts"), ("members", "Who holds them"), ("results", "Results, 2012 to 2026"),
           ("money", "Campaign money"), ("gaps", "Gaps"), ("sources", "Sources")]
    _hero(page, "Reference · State", "Your legislators",
          f"{len(hos)} Indiana House districts and {len(sos)} Indiana Senate districts include part of {county}. "
          "Districts are drawn by the state. Some lie wholly inside the county and some cross into neighboring counties.",
          [scope_badge("county", ed), scope_badge("indiana", ed)], toc)

    # coverage derived from the results notes
    contests = defaultdict(lambda: defaultdict(list))   # (chamber, num) -> year -> rows
    whole_years = defaultdict(set)
    for ct in ed.contests.values():
        m = CONTEST_RX.match(ct["contest_id"])
        if not m or not (2012 <= int(m.group(1)) <= 2026):
            continue
        key = (m.group(2), m.group(3))
        contests[key][int(m.group(1))] = ct["rows"]
        if all("district lies wholly in the county" in r.get("notes", "") for r in ct["rows"]):
            whole_years[key].add(int(m.group(1)))

    def office_for(key):
        return ed.offices.get(f"state-{key[0]}-{key[1]}")

    keys = sorted({(("house" if o["office_type"] == "state_house" else "senate"), o["district"]) for o in hos + sos},
                  key=_district_sort)

    # ---------------------------------------------------------------- 1 districts
    drows = []
    for key in keys:
        o = office_for(key)
        yrs = sorted(whole_years.get(key, []))
        if yrs:
            cover = ("The county's totals equal the district totals for " +
                     ", ".join(str(y) for y in yrs) + ". In the other years shown, the guide has only the county's tally.")
        else:
            cover = "Only the county portion of the district's results is known in every year shown."
        drows.append([o["title"], f"{o['term_years']} years", o.get("next_election", ""),
                      h("span", None, cover, c.cite(o["source_ids"]))])
    page.add(section("districts", 1, f"Districts that include part of {county}",
                     callout(h("p", None, h("strong", None, "Districts cross county lines. "),
                               "Indiana's House and Senate districts are not drawn along county borders. A district can "
                               "include part of one county and part of another. Results below are the county portion only "
                               "unless a row says it is a whole-district total, so a county tally is not the district's "
                               "winner by itself."), kind="note"),
                     h("p", None, "The table shows, for each district, the years in which the county's own totals equal "
                                  "Ballotpedia's district-wide totals. In those years the district lay wholly inside the "
                                  "county and the county tally is the district result. In other years the guide has only "
                                  "the county's tally.",
                       c.cite("GOV-044;GOV-045")),
                     data_table("districts-table", ["District", "Term", "Next election", "What is known about the district's extent"],
                                drows, caption="Legislative districts that include part of the county", min_width="44rem"),
                     scope="county", ed=ed))

    # ---------------------------------------------------------------- 2 members
    cards = []
    for key in keys:
        o = office_for(key)
        terms = ed.terms_on(o["office_id"], ed.as_of)
        current = [t for t in terms if t["status"] != "unofficial"]
        incoming = [t for t in ed.terms_for(o["office_id"]) if t["status"] == "unofficial"]
        note = None
        if incoming:
            same = {t["person"] for t in current} == {t["person"] for t in incoming}
            note = ("Re-elected Nov 3, 2026 (unofficial)." if same else
                    "A different person leads the unofficial Nov 3, 2026 count.") + \
                   (" A legislator's term begins the day after the general election (Ballotpedia lists the 2026 "
                    "winners as taking office Nov 4, 2026); results are unofficial until certified.")
        cards.append(officeholder_card(ed, page, o, current, incoming, note))
    # One rule for every 2026 race in a district that crosses the county line: the county tally, then the
    # district-wide count where the terms notes record one.
    xrows = []
    for key in keys:
        ct = ed.contests.get(f"2026g-state-{key[0]}-{key[1]}")
        if not ct or _result_scope(ct["rows"][0]).startswith("Whole district") or                 any(y >= 2022 for y in whole_years.get(key, ())):
            continue  # wholly inside the county on the 2021 map (used from 2022)
        o = office_for(key)
        inc = [t for t in ed.terms_for(o["office_id"]) if t["status"] == "unofficial"]
        wide = None
        for t in inc:
            m = re.search(r"district-wide[^;]*?\(([\d,]+) to ([\d,]+)\)", t.get("notes", ""))
            if m:
                wide = (t, m)
        county = h("span", None, join([h("span", None, name_with_party(r["candidate"], r["party"]), f" {int(float(r['votes'])):,}")
                                       for r in ct["rows"]], "; "))
        xrows.append([o["title"], county,
                      (f"{wide[1].group(1)} to {wide[1].group(2)}, led by {wide[0]['person']} (Ballotpedia)"
                       if wide else "Not in the guide's data"),
                      h("span", None, status_badge("unofficial", page), c.cite(ct["rows"][0]["source_ids"] + ";GOV-044;GOV-045"))])
    hd7_note = h("div", None,
                 h("p", None, "For districts that cross the county line, the county tally does not decide the race. The same "
                              "fields are shown for each of them:"),
                 data_table("cross-county-2026", ["District", "County tally (unofficial)", "District-wide count (unofficial)",
                                                  "Status"], xrows,
                            caption="2026 races in districts that extend outside the county", min_width="44rem")) if xrows else None
    page.add(section("members", 2, "Who holds these seats",
                     h("p", None, f"From the guide's terms data, as of {fmt_date(ed.as_of, long=True)}. Seats are listed by "
                                  "chamber and district number, not by party. Members elected on Nov 3, 2026 are unofficial "
                                  "until results are certified."),
                     h("h3", None, "The county's delegation by party"),
                     bodies_block(ed, [], extra_bodies={"State House members": hos, "State Senate members": sos}),
                     h("div", {"class": "card-grid"}, cards), hd7_note,
                     scope="county", ed=ed))

    # ---------------------------------------------------------------- 3 results
    blocks = []
    for key in keys:
        o = office_for(key)
        trs = []
        for year in sorted(contests[key]):
            for r in contests[key][year]:
                scope = _result_scope(r)
                try:
                    votes = f"{int(float(r['votes'])):,}"
                except ValueError:
                    votes = "not recorded"
                trs.append([f"{year} general", r["candidate"], party_label(r["party"]), votes,
                            f"{float(r['pct']):.2f}%" if r.get("pct") else "",
                            _result_text(r, scope), scope,
                            h("span", None, status_badge(r["status"], page), c.cite(r["source_ids"]))])
        blocks.append(h("div", {"class": "results-district"},
                        h("h3", {"id": f"results-{key[0]}-{key[1]}"}, o["title"]),
                        data_table(f"results-{key[0]}-{key[1]}-table",
                                   ["Election", "Candidate", "Party", "Votes", "Share", "Result as recorded", "What the votes cover", "Status"],
                                   trs, caption=f"{o['title']}: general election results, 2012 to 2026",
                                   numeric=(3, 4), min_width="60rem")))
    figs = []
    for key in keys:
        ct = ed.contests.get(f"2026g-state-{key[0]}-{key[1]}")
        if not ct:
            continue
        cands = []
        for r in ct["rows"]:
            cands.append({"name": r["candidate"], "party": r["party"], "votes": int(float(r["votes"])),
                          "pct": float(r["pct"]), "winner": ""})
        figs.append(results_bars(f"res26-{key[0]}-{key[1]}", f"{office_for(key)['title']}, county portion",
                                 cands, subtitle="Nov 3, 2026", status="unofficial",
                                 note="County portion only unless the table below says the totals match the district.",
                                 page=page, cite=c.cite(ct["rows"][0]["source_ids"])))
    page.add(section("results", 3, "Results, 2012 to 2026",
                     h("p", None, "These are the county's own canvass tallies for each general election, in the order the "
                                  "canvass lists the candidates. Indiana law orders the parties on the ballot by their vote "
                                  "for Secretary of State in the county at the last election; in 2022 Wells (D) received "
                                  "34,746 and Morales (R) 33,748, so Democrats are listed first on the 2024 and 2026 county "
                                  "ballots.", c.cite("IND-056;RES-023"), " They are the county portion of each race unless the "
                                  "\"What the votes cover\" column says otherwise. Only one row, the 2018 House District 8 "
                                  "result, is a district-wide total, taken from Ballotpedia because the county line could not "
                                  "be read from the scan; it is labeled district-wide and is not the county tally."),
                     h("h3", None, "2026, county portion (unofficial)"),
                     h("div", {"class": "chart-grid"}, figs),
                     h("p", {"class": "muted"}, "The 2026 charts mark no winner: the figures are unofficial, and for most "
                                                "districts the county portion is not the district result."),
                     h("h3", None, "Every general election in the data, by district"), blocks,
                     scope="county", ed=ed))

    # ---------------------------------------------------------------- 4 money
    cf = ed.table("cf_state")
    cf_src = ";".join(dict.fromkeys(s for r in cf for s in split_ids(r["source_ids"])))
    years = sorted({int(r["year"]) for r in cf})
    totals, counts = {}, {}
    for y in years:
        ys = [r for r in cf if int(r["year"]) == y]
        totals[y] = sum(float(r["receipts"] or 0) for r in ys)
        counts[y] = len(ys)
    pts = [{"x": str(y), "value": totals[y], "display": _money(totals[y]),
            "tip": f"{y}: {counts[y]} committees in the data"} for y in years]
    last_full = years.index(max(years)) - 1
    chart = columns("cf-state-receipts", "Receipts reported by the listed committees, by filing year", pts,
                    subtitle=f"{years[0]} to {years[-1]}. All committees in the guide's data added together.",
                    money=True, value_fmt=_money,
                    breaks=[{"after": last_full, "label": "Partial", "tip": f"{years[-1]} includes only filings up to the data download (2026-11-07)"}],
                    note="Filing-year basis: each bar adds up the items on reports filed in that calendar year, not an election "
                         "cycle. The number of committees changes by year (some began later), so a rise or fall can reflect "
                         "which committees are in the data.",
                    status="computed", page=page, headers=["Filing year", "Receipts, all listed committees"],
                    cite=c.cite(cf_src))

    def ck(r):
        d = r["district"]
        return (0 if d.startswith("HD") else 1, int(re.sub(r"\D", "", d)), r["committee"])
    committees = sorted({(r["committee"], r["candidate"], r["district"]) for r in cf}, key=lambda t: ck({"district": t[2], "committee": t[0]}))
    matrix = []
    for com, cand, dist in committees:
        by = {int(r["year"]): r for r in cf if r["committee"] == com}
        matrix.append([h("span", None, com, h("span", {"class": "muted"}, f" ({dist})"))] +
                      [(_money(float(by[y]["receipts"] or 0)) if y in by else "—") for y in years])
    long_rows = []
    for r in sorted(cf, key=lambda r: (ck(r), int(r["year"]))):
        long_rows.append([r["committee"], r["district"], r["year"], _money(float(r["receipts"] or 0)),
                          _money(float(r["expenditures"] or 0)), r["top_funder_types"].replace(";", ";  "),
                          status_badge(r["status"], page)])
    cavs = [r for r in ed.gaps(files=["gaps_money"], pattern=r"State campaign finance")]
    page.add(section("money", 4, "Campaign money, by filing year",
                     h("p", None, "Legislators and candidates file campaign-finance reports with the Indiana Election Division. "
                                  "The guide totals the state's bulk data for the committees of members and 2026 candidates "
                                  "in these districts."),
                     callout(h("p", None, h("strong", None, "Read these totals carefully. "),
                               "(1) They are by calendar year filed, not by election cycle, so one campaign spans two or more "
                               "rows. (2) Contributors were typed in by name and spellings vary, so name-level totals would "
                               "be understated; the guide shows only the contributor type codes as filed. (3) The data has no "
                               "cash-on-hand figure. (4) Only committees for the members and 2026 candidates listed here are "
                               "included, not every opponent.", c.cite("MON-020;MON-021;MON-022")), kind="note"),
                     chart,
                     h("h3", None, "Receipts by committee and filing year"),
                     data_table("cf-matrix", ["Committee (district)"] + [str(y) for y in years], matrix,
                                caption="Receipts by committee and filing year (a dash means no committee data for that year)",
                                numeric=tuple(range(1, len(years) + 1)), min_width="64rem"),
                     h("details", {"class": "state-details"},
                       h("summary", {"class": "btn btn-small"}, "Show every row: receipts, expenditures and top contributor types"),
                       data_table("cf-long", ["Committee", "District", "Filing year", "Receipts", "Expenditures",
                                              "Top contributor types (amount, as filed)", "Status"],
                                  long_rows, caption="State legislative committees, receipts and expenditures by filing year",
                                  numeric=(2, 3, 4), min_width="60rem")),
                     scope="county", ed=ed))

    gaps = ed.gaps(files=["gaps_results"], pattern=r"legislative district|State Representative District 8|statewide and multi-county")
    gaps += cavs
    gaps.append({"item": "Which districts lie wholly inside the county, from the statute text",
                 "why_missing": "The guide infers it from county totals that equal Ballotpedia's district totals. For Senate "
                                "District 10 a copy of IC 2-1-15-10 (2021 plan) lists only St. Joseph County townships, but "
                                "the statute was not read on iga.in.gov, and the House district sections were not read.",
                 "how_to_fill": "Read IC 2-1-14 and IC 2-1-15 (2021 plans) on iga.in.gov."})
    gaps.append({"item": "Certified 2026 district-wide counts",
                 "why_missing": "District-wide 2026 counts come from Ballotpedia's unofficial figures, recorded in the terms "
                                "notes; the Indiana Election Division has not certified them.",
                 "how_to_fill": "Replace with the Election Division's certified results."})
    page.finish(gaps=_dedupe(gaps))
    return page


# ============================================================================ how the state shapes local

def build_shapes(site):
    ed = site.ed
    page = site.page("state/how-the-state-shapes-local/index.html", banners=False)
    c = page.cites
    lr = ed.local_rules
    toc = [("home-rule", "Home rule"), ("caps", "Property tax caps and levy limits"), ("income-tax", "Local income tax"),
           ("sea1", "SEA 1 (2025)"), ("hb1210", "HEA 1210 (2026)"), ("timeline", "What changes and when"),
           ("schools", "School funding"), ("townships", "Township consolidation"), ("local-effects", "Effects reported locally"),
           ("gaps", "Gaps"), ("sources", "Sources")]
    _hero(page, "Reference · State", "How the state shapes local government",
          "Cities, towns, townships, counties and schools run their own affairs, but state law sets how much they can "
          "raise and spend. This page covers the main rules and the 2025 and 2026 laws that changed them.",
          [scope_badge("indiana", ed), scope_badge("county", ed)], toc)

    page.add(section("home-rule", 1, "Home rule and its limits", _rule_block(page, ed, "home_rule"),
                     scope="indiana", ed=ed))

    cap_rows = [["Principal residence (homestead)", "1%"],
                ["Other residential property and farmland", "2%"],
                ["Other real property and business personal property", "3%"]]
    cap_table = data_table("cap-table", ["Kind of property", "Cap on the tax bill (share of assessed value)"], cap_rows,
                           caption="Constitutional caps on property tax bills", numeric=(1,), copy=False)
    page.add(section("caps", 2, "Property tax caps and levy limits",
                     _rule_block(page, ed, "property_tax_caps", "The 1%, 2% and 3% caps", extra=cap_table),
                     _rule_block(page, ed, "levy_controls", "Limits on how fast a levy can grow"),
                     _rule_block(page, ed, "dlgf_role", "Who checks local budgets: the DLGF"),
                     scope="indiana", ed=ed))

    page.add(section("income-tax", 3, "Local income tax",
                     _rule_block(page, ed, "local_income_tax"),
                     scope="indiana", ed=ed))

    ded = lr["sea1_deductions_schedule"]
    ded_table = data_table("sea1-deductions", ["Item", "What the sources say", "Status"],
                           [["Deductions schedule", h("span", None, ded["plain_language"], " ", _clean_detail(ded["detail"]),
                                                      c.cite(ded["source_ids"])),
                             h("span", None, status_badge(ded["status"], page), " ", status_badge("low", page))]],
                           caption="Where sources disagree (low confidence)", copy=False, min_width="36rem")
    page.add(section("sea1", 4, "SEA 1 (2025)",
                     _rule_block(page, ed, "sea1_overview", "What it did"),
                     _rule_block(page, ed, "sea1_homestead_credit", "Homestead credit"),
                     _rule_block(page, ed, "sea1_business_personal_property", "Business personal property exemption"),
                     h("h3", None, "Deductions: the sources disagree"),
                     h("p", None, "The standard homestead deduction schedule is not stated here as fact. The row below is "
                                  "kept for completeness and flagged low confidence."),
                     ded_table,
                     scope="indiana", ed=ed))

    page.add(section("hb1210", 5, "HEA 1210 (2026)", _rule_block(page, ed, "hea1210_2026"),
                     scope="indiana", ed=ed))

    tl = [("2025", "SEA 1 becomes law", lr["sea1_overview"]),
          ("Jan 1, 2026", "Homestead credit (10% of the bill, up to $300) and the business personal property exemption "
                          "($2 million) start", lr["sea1_homestead_credit"]),
          ("Mar 5, 2026", "SEA 270 township consolidation law takes effect", lr["township_mergers"]),
          ("Mar 12, 2026", "HEA 1210 signed: SEA 1's local income tax changes delayed from 2028 to 2029", lr["hea1210_2026"]),
          ("Jul 1, 2027", "Local income tax councils end; the county fiscal body sets the local income tax. "
                          "New notice-publication rules from HEA 1210 also start", lr["local_income_tax"]),
          ("2027 and 2028", "Some townships must consolidate or merge", lr["township_mergers"]),
          ("2029", "Local income tax rate changes (total cap of 2.9%), delayed from 2028", lr["local_income_tax"])]
    page.add(section("timeline", 6, "What changes and when",
                     h("p", None, "Dates are as stated in the guide's data. Dates for the 2025 and 2026 laws came from "
                                  "secondary sources and FindLaw, which can lag; see the Gaps list."),
                     data_table("law-timeline", ["When", "What changes", "Status"],
                                [[w, h("span", None, t, c.cite(r["source_ids"])), status_badge(r["status"], page)] for w, t, r in tl],
                                caption="Timeline of the 2025 and 2026 laws that affect local governments", min_width="40rem"),
                     scope="indiana", ed=ed))

    page.add(section("schools", 7, "School funding basics",
                     _rule_block(page, ed, "school_funding_basics", detail=True),
                     _rule_block(page, ed, "school_levy_sharing", "Levy sharing with charter schools"),
                     scope="indiana", ed=ed))

    page.add(section("townships", 8, "Township consolidation (2026)", _rule_block(page, ed, "township_mergers"),
                     scope="indiana", ed=ed))

    # ---- local effects, sourced and attributed
    msrc = ed.sources.get("MON-014", {})
    effects = [
        ["Mishawaka (city)",
         h("span", None, "ABC57 reported on Nov 18, 2025 that Mishawaka expected a budget cut of about 20 percent, or $15 million, "
                         "by 2028 because of SEA 1. This is the reporter's statement, not a quote from the mayor, and the "
                         "article does not say which fund the cut applies to.", c.cite("MON-014")),
         "News report, not an official estimate"],
        ["School City of Mishawaka",
         h("span", None, "ABC57 reported in December 2025 that the school corporation could lose more than $1 million by 2028, "
                         "because operating levy revenue must be shared with charter schools.", c.cite(lr["school_levy_sharing"]["source_ids"])),
         "News report, not an official estimate"]]
    page.add(section("local-effects", 9, "Effects reported locally",
                     h("p", None, "The state has not published a dollar estimate for each unit in this guide's data. These are the "
                                  "figures local news outlets reported, attributed to the reporting. Statewide, ABC57 summarized "
                                  "SEA 1 as $1.3 billion in property tax relief to homeowners over three years, and the Capital "
                                  "Chronicle reported an estimated $1.4 billion in lost local revenue over 2026-2028; no "
                                  "homeowner-savings figure for this county is in the guide's sources.", c.cite("IND-046;IND-024;IND-033")),
                     data_table("local-effects-table", ["Unit", "What was reported", "Kind of figure"], effects,
                                caption="Effects of SEA 1 reported by local officials and news outlets", min_width="40rem"),
                     scope="county", ed=ed))

    gaps = [{"item": "2025 and 2026 laws (SEA 1, HEA 1210, SEA 270) need re-checking against iga.in.gov",
             "why_missing": "Statute texts came from FindLaw and secondary reporting, which may lag the enrolled acts.",
             "how_to_fill": "Read the enrolled text of each act on iga.in.gov and confirm dates, rates and amounts."}]
    gaps += ed.gaps(files=["gaps_indiana"], areas=["state_local_rules"])
    gaps += ed.gaps(files=["gaps_money"], pattern=r"SEA 1|HB 1210")
    page.finish(gaps=_dedupe(gaps))
    return page


PAGES = {
    "state/index.html": build_state,
    "state/your-legislators/index.html": build_legislators,
    "state/how-the-state-shapes-local/index.html": build_shapes,
}
