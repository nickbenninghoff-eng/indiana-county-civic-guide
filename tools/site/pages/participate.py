"""Participation pages: Run for office (+ six office pages), Who handles this?, Your place (your-governments/)."""
from __future__ import annotations

import re

from civic.components import (APPOINTED_NOTE, as_of_note, bodies_block, callout, data_table, entity_list, scope_badge,
                              section, see_all_table, status_badge)
from civic.data import fmt_date, split_ids
from civic.html import h, join, json_script
from civic.layers import build_layers, election_dates
from civic.picker import picker_state, place_page
from civic.related import related_items
from pages.elections import moved_anchors

CONFIRM = "Confirm with the county election office."
EB_PAGE = "https://www.sjcindiana.gov/2387/Election-BoardCandidate-Information"
PCP = "run/precinct-committeeperson/index.html"

OFFICES = {
    "city-council": dict(label="City council", ot="city_council_member",
                         types=["city_council_district", "city_council_at_large"], who="Cities"),
    "county-council": dict(label="County council", ot="county_council_member",
                           types=["county_council_member"], who="County"),
    "school-board": dict(label="School board", ot="school_board_member",
                         types=["school_board_district", "school_board_at_large", "school_board_appointed"], who="School corporations"),
    "township-board": dict(label="Township board", ot="township_board_member",
                           types=["township_board_member"], who="Townships"),
    "township-trustee": dict(label="Township trustee", ot="township_trustee",
                             types=["township_trustee"], who="Townships"),
}
ORDER = ["city-council", "county-council", "school-board", "township-board", "township-trustee",
         "precinct-committeeperson"]
LABELS = {k: v["label"] for k, v in OFFICES.items()}
LABELS["precinct-committeeperson"] = "Precinct committeeperson"


# ---------------------------------------------------------------- data helpers

def _seats(v):
    m = re.match(r"\s*(\d+)", v or "")
    return int(m.group(1)) if m else None


def _rows(ed, slug):
    """Per unit: (unit_id, unit name, seats text, {year: [district labels]}) for the office page."""
    spec = OFFICES[slug]
    by_unit: dict[str, list[dict]] = {}
    for o in ed.tables["offices"]:
        if o["office_type"] in spec["types"]:
            by_unit.setdefault(o["unit_id"], []).append(o)
    out = []
    for uid, offs in by_unit.items():
        seats = [_seats(o["seats"]) for o in offs]
        total = sum(s for s in seats if s)
        txt = f"{total}" + (" (some seat counts not in data)" if None in seats else "")
        years: dict[str, list[str]] = {}
        for o in offs:
            y = o.get("next_election") or ""
            years.setdefault(y or "not in data", []).append(o["district"] or o["title"])
        out.append((uid, ed.units[uid]["name"], txt, years))
    return out


def _years(ed, slug):
    return sorted({y for _, _, _, ys in _rows(ed, slug) for y in ys if y.isdigit()})


def _dates_text(ed, y):
    d = election_dates(ed, [y])[y]
    return f"Primary {fmt_date(d['primary'], True)} · General {fmt_date(d['general'], True)}"


def _year_label(ys: dict) -> str:
    parts = []
    for y in sorted(ys):
        d = ys[y]
        parts.append(y + (f" ({', '.join(d)})" if len(d) <= 9 and any(x for x in d) and len(ys) > 1 else ""))
    return "; ".join(parts)


def _unit_link(page, ed, uid, name):
    if ed.units[uid]["unit_type"] in ("city", "town", "township"):
        return h("a", {"href": page.rel(f"places/{uid}/index.html")}, name)
    if uid == "county":
        return h("a", {"href": page.rel("county/index.html")}, name)
    if ed.units[uid]["unit_type"] == "school_corporation":
        return h("a", {"href": page.rel("schools/index.html")}, name)
    return name


def _filing_note(page, years):
    """Filing deadline text for the years shown."""
    c = page.cites
    bits = []
    if "2027" in years:
        # Opening day and deadline: Indiana Election Division 2027 calendar brochure (IND-078), checked 2026-11-09.
        bits.append(h("span", None, "2027 city offices: file a declaration (CAN-42, with a CAN-12) with the county election board "
                      "from Wednesday, Jan 6, 2027 until ", h("strong", None, "noon on Friday, Feb 5, 2027"),
                      c.cite("IND-078;SVC-018"), "."))
    other = [y for y in years if y != "2027"]
    if other:
        bits.append(h("span", None, f"{', '.join(other)}: filing window not in the guide's data. ", CONFIRM))
    return bits


# ---------------------------------------------------------------- shared blocks

def _contacts(page, ed):
    c = page.cites
    return h("div", {"class": "contact-card"},
             h("h3", {"class": "card-title"}, "County Election Board and Voter Registration, St. Joseph County ",
               scope_badge("county", ed), " ", status_badge("official", page)),
             h("p", {"class": "contact-lines"},
               h("span", {"class": "mono"}, "County-City Building, 4th Floor, 227 W. Jefferson Blvd., South Bend, IN 46601"), h("br"),
               h("span", {"class": "mono"}, "Phone: 574-235-9635"), h("br"),
               h("span", {"class": "mono"}, "Email: voter@sjcindiana.gov"), c.cite("SVC-017")),
             h("p", None, "The election board takes candidate filings for county and city offices and publishes candidate information: ",
               h("a", {"href": EB_PAGE, "target": "_blank", "rel": "noopener"}, "county Election Board page"), c.cite("SVC-007"), ". "
               "State forms and rules are on the ",
               h("a", {"href": page.rel("elections/how-it-works/index.html#candidate-info")}, "candidate information section"), " of How Indiana elections work."))


PARTY_ORGS = {"D": "St. Joseph County Democratic Party", "L": "Libertarian Party of St. Joseph County",
              "R": "St. Joseph County Republican Party"}


def _parties(page):
    """Party and civic organizations, one format, alphabetical. Parties are listed mechanically: every
    party with a candidate on the county's two most recent general-election ballots in results.csv
    (neutrality review F9), plus the League of Women Voters as the nonpartisan civic organization."""
    ed = page.cites.ed
    gens = sorted((e for e in ed.elections.values() if e["type"] == "general"), key=lambda e: e["date"])[-2:]
    gen_ids = {e["election_id"] for e in gens}
    codes = sorted({r["party"] for r in ed.tables["results"] if r["election_id"] in gen_ids}
                   & {"D", "R", "L", "G"})
    orgs = [(PARTY_ORGS.get(cd, f"County organization of the {cd} party (name not in the guide's data)"),
             "Political party: runs its precinct committeepersons, nominations and vacancy caucuses.") for cd in codes]
    orgs.append(("League of Women Voters of the South Bend Area",
                 "Nonpartisan civic organization: voter registration, candidate forums and voter information."))
    orgs.sort(key=lambda o: o[0].replace("St. Joseph County ", "").replace("of St. Joseph County", "").replace("of the South Bend Area", ""))
    yrs = " and ".join(e["date"][:4] for e in gens)
    return h("div", {"class": "contact-card"},
             h("h3", {"class": "card-title"}, "Party and civic organizations"),
             h("p", None, f"Parties listed are those with candidates on the county's {yrs} general-election ballots in the guide's results data, "
                          "in alphabetical order. For filing questions, use the County Election Board above."),
             h("ul", {"class": "party-orgs"}, [h("li", None, h("strong", None, n), ". ", d) for n, d in orgs]),
             h("p", {"class": "muted"}, "No official web page for these organizations is sourced in the guide, so none is linked. "
               "The county election board can tell you how to reach each party."))


def _finance(page, ed):
    c = page.cites
    return [
        h("p", None, "Candidates for county, city, township and school board offices report their campaign money to the county, "
          "not to the state database: they file with the county election board", c.cite("SVC-021;IND-079"), ". ",
          status_badge("official", page)),
        h("p", None, "The county's Candidate Filings page posts scanned CFA-4 reports (the receipts and spending report) and CFA-11 "
          "notices (large contributions)", c.cite("SVC-019;SVC-020"), ". The reports it has posted include annual, pre-primary, "
          "pre-election and pre-general periods", c.cite("SVC-020"), "."),
        # 2027 dates: Indiana Election Division 2027 calendar brochure (IND-078); committee rule: 2026 Campaign Finance
        # Manual pp. 9-10 (IND-080). Checked 2026-11-09; replaces "Confirm" and a stale "no schedule yet" sentence.
        h("p", None, "2027 report deadlines for city candidates: pre-primary report due ", h("strong", None, "noon April 16, 2027"),
          " (period ends April 9); pre-election report due ", h("strong", None, "noon October 15, 2027"),
          " (period ends October 8); annual report for 2027 due noon January 19, 2028. Annual reports for 2026 are due noon "
          "January 20, 2027", c.cite("IND-078"), ". City and town candidates file the pre-primary and pre-election reports even "
          "if no primary or election is held for their office", c.cite("IND-080"), ". ", status_badge("official", page)),
        h("p", None, "For an office paying $5,000 a year or more, the candidate files a committee statement of organization (CFA-1) "
          "by noon 10 days after becoming a candidate (raising or spending more than $100) or noon 7 days after the filing "
          "deadline, whichever comes first. For school board, and for local offices paying "
          "under $5,000 a year, a committee is needed only after raising or spending more than $500", c.cite("IND-080"), ". "
          "Precinct committeeperson candidates file no campaign-finance reports", c.cite("IND-079;IND-080"), ". ",
          status_badge("official", page)),
        h("p", None, "Report due dates for 2028 and later: ", CONFIRM, " ",
          "State-level campaign data covers only state candidates and committees", c.cite("MON-020"), ". ",
          h("a", {"href": page.rel("money/campaigns/index.html#obligations")}, "Campaign-finance obligations")),
    ]


def _ballot_access(page, ed):
    c = page.cites
    r = ed.rules
    return [
        h("h3", None, "Party primary"),
        h("p", None, r["candidate_forms"]["plain_language"], c.cite(r["candidate_forms"]["source_ids"]), " ",
          r["candidate_forms"]["detail"], " ", status_badge(r["candidate_forms"]["status"], page)),
        # The declaration form changes with the election: CAN-2 is the 2026 (even-year) primary form; city and
        # town offices in 2027 use CAN-42 (Indiana Election Division calendar, Feb 5, 2027 entries).
        h("p", None, "Which declaration form: CAN-2 is the Declaration of Candidacy for Primary Nomination in 2026 (county, "
          "township, legislative and other even-year offices). For the 2027 city and town primary the form is CAN-42 "
          "(Declaration of Candidacy for Municipal Primary Nomination in 2027), filed with a CAN-12 Statement of Economic "
          "Interests", c.cite("SVC-018"), ". Towns under 3,500 people hold a major-party primary only if the town adopted an "
          "ordinance to do so", c.cite("SVC-018"), ". ", status_badge("official", page)),
        h("p", None, r["party_primaries"]["plain_language"], c.cite(r["party_primaries"]["source_ids"]),
          " ", status_badge(r["party_primaries"]["status"], page)),
        # IC 3-8-2-7(a)(4), read 2026-11-09 (IND-082; 2026 Candidate Guide p. 11, IND-079). The earlier sentence left out the
        # county chair's certification.
        h("p", None, "To run in a party's primary, a candidate's two most recent Indiana primary votes must have been in that "
          "party's primary, or the party's county chair must certify the candidate as a party member (the certification is "
          "attached to the declaration)", c.cite("IND-082;IND-079"), ". ", status_badge("official", page)),
        h("h3", None, "Petition (independent and minor-party candidates)"),
        h("p", None, r["independent_petitions"]["plain_language"], c.cite(r["independent_petitions"]["source_ids"]),
          " For 2027 city and town offices the petition form is CAN-44", c.cite("ELX-007"),
          ": file it with the county voter registration office for signature checks from Jan 6 until ",
          h("strong", None, "noon June 30, 2027"), ", then file the consent and the certified petition by noon July 15, 2027",
          c.cite("IND-078"), ". The petition needs signatures from voters of the district equal to 2% of the votes cast there "
          "at the last election for Secretary of State", c.cite("IND-069"), "; the count for each district: ", CONFIRM,
          " In 2026 the forms were CAN-19 (federal, state and legislative) and CAN-21 (other local offices), due at noon June 30 "
          "with the consent (CAN-20) at noon July 15; school board petitions (CAN-34) had their own window, May 19 to noon "
          "June 18, 2026", c.cite("IND-079"), ". Deadlines for 2028 and later: ", CONFIRM, " ",
          status_badge(r["independent_petitions"]["status"], page)),
        h("h3", None, "School board: party label instead of a primary"),
        h("p", None, r["partisan_school_board"]["plain_language"], c.cite(r["partisan_school_board"]["source_ids"]), " ",
          status_badge(r["partisan_school_board"]["status"], page)),
        _school_party_rule(page),
    ]


def _school_party_rule(page):
    """School board party label rule (2026 Candidate Guide p. 105, IND-079; IC 3-8-2.5-2.5 and -7). Replaces "a candidate's
    last two primary votes must match any party they list", which left out the county chair's certification and the
    minor-party, independent and no-party choices (checked 2026-11-09)."""
    return h("p", None, "To list the Democratic or Republican Party, a school board candidate's two most recent Indiana primary "
             "votes must have been in that party's primary, or the party's county chair must certify the candidate. Listing a "
             "minor party, independent or no party cannot be challenged on party grounds", page.cites.cite("IND-079"), ". ",
             status_badge("official", page))


def _vacancies(page, ed):
    c = page.cites
    r = ed.rules["local_vacancy_caucus"]
    return [
        h("p", None, r["plain_language"], c.cite(r["source_ids"]), " ", r["detail"], " ", status_badge(r["status"], page)),
        h("p", None, "Example: a party caucus filled a South Bend Common Council seat in May 2026", c.cite("GOV-027"), "."),
        h("p", None, "The way in is the party's ", h("a", {"href": page.rel(PCP)}, "precinct committeepersons"),
          ": they are the voters at a caucus."),
    ]


def _hero(page, ed, eyebrow, title, dek, scopes=("indiana", "county")):
    return h("header", {"class": "page-hero"}, h("p", {"class": "eyebrow mono"}, eyebrow), h("h1", None, title),
             h("p", {"class": "dek"}, dek),
             h("p", {"class": "hero-badges"}, [[scope_badge(s, ed), " "] for s in scopes]))


def _office_table(page, ed, slug, tid):
    rows = []
    for uid, name, seats, ys in _rows(ed, slug):
        rows.append([_unit_link(page, ed, uid, name), seats, _year_label(ys)])
    return data_table(tid, ["Government", "Seats", "Next regular election (seat or district)"], rows,
                      caption=f"{LABELS[slug]} seats in the guide's data", min_width="34rem")


# ---------------------------------------------------------------- run/<office>/

# Citation ids the six office pages carried before they were trimmed: those facts now live once on run/index, so the
# office page ships a moved-anchors map (static/js/moved.js) that sends an old #src-... link there.
RUN_SHARED_SOURCES = ("ELX-007", "GOV-027", "IND-026", "IND-038", "IND-041", "MON-020", "SVC-007", "SVC-017", "SVC-018",
                      "SVC-019", "SVC-020")


def moved_to_run_index():
    return json_script("moved-anchors", {"a": {f"src-{s}": "../index.html" for s in RUN_SHARED_SOURCES}})


def run_index_link(page, anchor, text="Run for office"):
    """Link to a shared step on run/index. The six office pages keep only their own facts and point here."""
    return h("a", {"href": page.rel(f"run/index.html#{anchor}")}, text)


def build_office(slug):
    spec = OFFICES.get(slug)

    def build(site):
        ed = site.ed
        path = f"run/{slug}/index.html"
        page = site.page(path)
        c = page.cites
        if slug == "precinct-committeeperson":
            return _build_pcp(site, page)
        ot = ed.office_types[spec["ot"]]
        page.add(_hero(page, ed, "Run for office", f"Run for {spec['label'].lower()}",
                       ot["what_it_does"].rstrip(".") + ".", ("indiana", "county")))
        # ---- role, term, next election
        years = _years(ed, slug)
        term = [h("p", None, f"Term: {ot['term_years']} years", c.cite(ot["source_ids"]), ". ", status_badge(ot["status"], page)),
                _office_table(page, ed, slug, f"tbl-{slug}")]
        for y in years:
            term.append(h("p", None, h("strong", None, y), ": ", _dates_text(ed, y), " ",
                          status_badge("computed", page, "Computed from the state calendar rule."),
                          c.cite(ed.rules["primary_date"]["source_ids"] + ";" + ed.rules["general_election_date"]["source_ids"])))
        if slug == "county-council":
            term.append(callout(h("p", None, "Council size and districts: ",
                                  h("span", None, "nine single-member districts, A to I in this edition's data ",
                                    status_badge("unverified", page, ed.variant("council_size")["note"]), c.cite("IND-053")))))
        if slug == "school-board":
            term.append(h("p", {"class": "muted"}, "Seat counts for some boards are blank in the data; district seats are shown as the data records them."))
        if slug == "township-board":
            term.append(h("p", None, "From 2027 a straight-party vote also counts for at-large offices such as the township board "
                          "unless the voter marks individual candidates", c.cite(ed.rules["straight_party_from_2027"]["source_ids"]), "."))
        page.add(section("term", 1, "What it does, term and next election", term, scope="county", ed=ed))
        # ---- eligibility and filing
        elig = []
        if slug == "township-trustee":
            elig.append(h("p", None, "A trustee must live in the township, and the term starts January 1 after the election",
                          c.cite("IND-013"), ". ", status_badge("official", page)))
        elig.append(h("p", None, "Age, length of residence and voter-registration rules for this office: ", CONFIRM))
        elig.append(h("p", None, "Filing window and deadline:"))
        elig.append(h("ul", None, [h("li", None, b) for b in _filing_note(page, years)]))
        page.add(section("eligibility", 2, "Eligibility and filing", elig, scope="mixed" if False else "indiana", ed=ed))
        r = ed.rules
        shared = run_index_link(page, "ballot-access")
        if slug == "school-board":
            # School board seats have no primary (SEA 287): every candidate files a petition of nomination. 2026 Candidate
            # Guide pp. 104-105 (IND-079), checked 2026-11-09; the generic "party primary or by petition" line was wrong here.
            ballot = [h("p", None, "School board candidates do not run in a party primary. Each files a petition of nomination "
                        "(CAN-34 in 2026) and a CAN-12 Statement of Economic Interests with the county election board of the "
                        "county holding most of the school corporation's people. In 2026 the window was May 19 to noon June 18",
                        c.cite("IND-079"), ". The 2028 window is not published yet. ", status_badge("official", page)),
                      h("p", None, r["partisan_school_board"]["plain_language"],
                        c.cite(r["partisan_school_board"]["source_ids"]), " ",
                        status_badge(r["partisan_school_board"]["status"], page)),
                      _school_party_rule(page),
                      h("p", None, "More on petitions and party labels: ", shared, ".")]
        else:
            ballot = [h("p", None, "Candidates reach the ballot through a party primary or by petition",
                        c.cite(r["candidate_forms"]["source_ids"] + ";" + r["independent_petitions"]["source_ids"]),
                        ". The forms, deadlines and party-label rules are the same for every office: ", shared, ".")]
        page.add(section("ballot-access", 3, "How you get on the ballot", ballot, scope="indiana", ed=ed))
        page.add(section("money", 4, "Campaign-finance duties",
                         h("p", None, "Candidates for this office report campaign money to the county, not to the state "
                                      "database", c.cite("SVC-021"), ". Reports and due dates: ", run_index_link(page, "money"), "."),
                         scope="county", ed=ed))
        page.add(section("vacancies", 5, "Vacancies and caucuses",
                         h("p", None, "A local vacancy is filled by the party caucus rule, which is the same for every office",
                           c.cite(r["local_vacancy_caucus"]["source_ids"]), ": ", run_index_link(page, "vacancies"), "."),
                         scope="indiana", ed=ed))
        page.add(section("contacts", 6, "Where to file locally",
                         h("p", None, "The County Election Board's address, phone, email and the party organizations are on ",
                           run_index_link(page, "contacts"), "."), scope="county", ed=ed))
        page.add(h("p", None, h("a", {"href": page.rel("run/index.html")}, "Back to Run for office")))
        page.add(moved_to_run_index())
        page.finish(gaps=ed.gaps(files=["gaps_services"], areas=["run"]))
        return page
    return build


def _build_pcp(site, page):
    ed = site.ed
    c = page.cites
    ot = ed.office_types["precinct_committeeperson"]
    page.add(_hero(page, ed, "Run for office", "Run for precinct committeeperson",
                   "The party office that takes part in caucuses.", ("indiana", "county")))
    role = [
        h("p", None, ot["what_it_does"], c.cite(ot["source_ids"]), " ", status_badge(ot["status"], page)),
        h("p", None, ed.rules["precinct_committeepersons"]["plain_language"], c.cite(ed.rules["precinct_committeepersons"]["source_ids"]),
          " ", status_badge("low", page, "The county-chair rule comes from an unsourced note.")),
        # IC 3-10-1-4.5 and 4.6 (IND-081) and the 2026 Candidate Guide pp. 3, 133 (IND-079), checked 2026-11-09: the two major
        # parties elect committeepersons in different years.
        h("p", None, "Committeepersons are elected at the primary every four years, in different years for each major party: "
          "Democratic Party committeepersons were elected in May 2026 and are next elected in ", h("strong", None, "May 2030"),
          "; Republican Party committeepersons were elected in May 2024 and are next elected in ", h("strong", None, "May 2028"),
          c.cite("IND-081;IND-079"), ". Who may run is set by each party's rules", c.cite("IND-079"), ". ",
          status_badge("official", page)),
        h("p", None, "Precinct committeepersons run in the party primary and file a separate form, CAN-37 (precinct committee or delegate)",
          c.cite(ed.rules["candidate_forms"]["source_ids"]), ". They file no Statement of Economic Interests (CAN-12) and no "
          "campaign-finance reports", c.cite("IND-079"), ". The county posts these filings on its Candidate Filings page: "
          "225 documents for 2026 and 60 for 2024 (document counts, not offices)", c.cite("SVC-019"), "."),
        h("p", None, "Filing window and deadline: ", CONFIRM),
    ]
    page.add(section("role", 1, "What the office does", role, scope="indiana", ed=ed))
    page.add(section("vacancies", 2, "Why it matters: caucuses",
                     h("p", None, "A party caucus fills a local vacancy, and the precinct committeepersons are the voters at it",
                       c.cite(ed.rules["local_vacancy_caucus"]["source_ids"]), ". The rule and an example are on ",
                       run_index_link(page, "vacancies"), "."),
                     h("p", None, "A legislative vacancy is filled by a caucus of the departing member's party precinct committeepersons from "
                       "that district", c.cite(ed.rules["legislative_vacancy_caucus"]["source_ids"]), "."), scope="indiana", ed=ed))
    page.add(section("contacts", 3, "Where to file locally",
                     h("p", None, "The County Election Board's address, phone, email and the party organizations are on ",
                       run_index_link(page, "contacts"), "."), scope="county", ed=ed))
    page.add(h("p", None, h("a", {"href": page.rel("run/index.html")}, "Back to Run for office")))
    page.add(moved_to_run_index())
    page.finish(gaps=ed.gaps(files=["gaps_services"], areas=["run"]))
    return page


# ---------------------------------------------------------------- run/index

def build_run(site):
    ed = site.ed
    page = site.page("run/index.html")
    c = page.cites
    page.add(_hero(page, ed, "Run for office · Elections & running", page.title,
                   "Six offices you could seek, with the rules that apply across Indiana and the places to file in St. Joseph County.",
                   ("indiana", "county")))
    # pick: one card per office (the six office pages keep only the facts specific to their office)
    cards = []
    for slug in ORDER:
        href = page.rel(f"run/{slug}/index.html")
        if slug == "precinct-committeeperson":
            # IC 3-10-1-4.5 / 4.6 (IND-081), checked 2026-11-09; the office page cites it.
            facts = [("Seats", "Not in data"), ("Term", "Local party office"),
                     ("Next", "2028 (Republican), 2030 (Democratic)")]
        else:
            spec = OFFICES[slug]
            ot = ed.office_types[spec["ot"]]
            rs = _rows(ed, slug)
            total = sum(_seats(s.split(" ")[0]) or 0 for _, _, s, _ in rs)
            ys = _years(ed, slug)
            facts = [("Seats", f"{total}+ across {len(rs)} government{'s' if len(rs) != 1 else ''}"),
                     ("Term", f"{ot['term_years']} years"),
                     ("Next", ", ".join(ys) or "Not in the guide's data")]
        cards.append(h("li", {"class": "card run-card"},
                       h("h3", {"class": "card-title"}, h("a", {"href": href}, LABELS[slug])),
                       h("dl", {"class": "run-facts"}, [[h("dt", None, k), h("dd", None, v)] for k, v in facts]),
                       h("p", {"class": "run-more"}, h("a", {"href": href, "aria-label": f"{LABELS[slug]}: seats and rules"}, "Seats and rules"))))
    page.add(section("pick", 1, "Pick an office", h("p", None, "Seat counts and years come from the guide's office data", c.cite("GOV-001"),
                                                  ". The steps below are the same for every office; each office page "
                                                  "keeps only what is specific to it."),
                     h("ul", {"class": "card-grid run-cards", "id": "tbl-run-pick", "aria-label": "Offices you could run for"}, cards),
                     scope="county", ed=ed))
    # eligibility
    all_years = sorted({y for s in OFFICES for y in _years(ed, s)})
    # The rules table has had the registration and residency rules since 2026-11-08; the old sentence said the trustee rule
    # was the only one (checked against the 2026 Candidate Guide pp. 7, 81, 103 and FindLaw IC 3-8-1-21, -26, -27 on 2026-11-09).
    reg, res = ed.rules["local_candidate_registration"], ed.rules["local_residency_requirements"]
    el = [h("p", None, reg["plain_language"], c.cite(reg["source_ids"] + ";IND-079"), " ", res["plain_language"],
            c.cite(res["source_ids"] + ";IND-079"), " A township trustee must live in the township", c.cite("IND-013"), ". ",
            status_badge("official", page)),
          h("p", None, "Minimum age and the residence rules for other offices: ", CONFIRM),
          h("ul", None, [h("li", None, b) for b in _filing_note(page, all_years)]),
          h("p", None, "The state sets the municipal calendar: primary and general dates are computed from the calendar rule",
            c.cite(ed.rules["municipal_cycle"]["source_ids"]), ". 2027: ", _dates_text(ed, "2027"), " ",
            status_badge("computed", page)),
          h("p", None, "Each office page lists its term, seats and next election.")]
    page.add(section("eligibility", 2, "Eligibility, term and next election", el, scope="mixed" if False else "indiana", ed=ed))
    page.add(section("ballot-access", 3, "Getting on the ballot", _ballot_access(page, ed), scope="indiana", ed=ed))
    page.add(section("money", 4, "Campaign-finance duties", _finance(page, ed), scope="county", ed=ed))
    page.add(section("vacancies", 5, "Vacancies and caucuses", _vacancies(page, ed), scope="indiana", ed=ed))
    page.add(section("contacts", 6, "Contacts", _contacts(page, ed), _parties(page), scope="county", ed=ed))
    page.finish(gaps=ed.gaps(files=["gaps_services"], areas=["run"]))
    return page


# ---------------------------------------------------------------- who-handles-this

SPECIAL_UNITS = {"indot": "Indiana Department of Transportation (INDOT)"}


def build_who(site):
    ed = site.ed
    page = site.page("who-handles-this/index.html")
    c = page.cites
    page.add(_hero(page, ed, "Reference · Your governments", page.title,
                   "Match a common service to the government that runs it and the official who answers for it.", ("county",)))

    def unit_cell(uid):
        if uid in SPECIAL_UNITS:
            return SPECIAL_UNITS[uid]
        u = ed.units.get(uid)
        return _unit_link(page, ed, uid, u["name"]) if u else uid

    def office_cell(oid):
        o = ed.offices.get(oid)
        if not o:
            return oid
        if o["unit_id"] == "county":
            return h("a", {"href": page.rel("county/index.html")}, o["title"])
        if ed.units[o["unit_id"]]["unit_type"] in ("city", "town", "township"):
            return h("a", {"href": page.rel(f"places/{o['unit_id']}/index.html")}, o["title"])
        return o["title"]

    def listing(items, fn):
        if not items:
            return h("span", {"class": "muted"}, "Not in the guide's data")
        return h("ul", {"class": "plain-list"}, [h("li", None, fn(i)) for i in items])

    def unit_names(r):
        out = []
        for uid in split_ids(r["responsible_unit_ids"]):
            out.append(SPECIAL_UNITS.get(uid) or (ed.units[uid]["name"] if uid in ed.units else uid))
        return out

    def office_titles(r):
        return [ed.offices[o]["title"] if o in ed.offices else o for o in split_ids(r["accountable_office_ids"])]

    rows = []
    for r in ed.table("services"):
        rows.append([
            r["service"],
            listing(split_ids(r["responsible_unit_ids"]), unit_cell),
            listing(split_ids(r["accountable_office_ids"]), office_cell),
            [r["how_it_depends"], c.cite(r["source_ids"]), " ", status_badge(r["status"], page),
             " " if r["confidence"] != "low" else "", status_badge("low", page) if r["confidence"] == "low" else None],
            r["contact"] or h("span", {"class": "muted"}, "Not in the guide's data"),
        ])
    srows = list(ed.table("services"))
    tbl = see_all_table("tbl-services", ["Service", "Responsible government(s)", "Accountable elected official(s)",
                                         "How it depends", "Contact"], rows, noun="service",
                        caption="Services and who handles them (sourced rows only)", min_width="60rem",
                        intro=h("p", {"class": "muted"}, "The same rows as the list above, one table, ready to copy."))
    items = []
    for i, r in enumerate(srows):
        units, offs = unit_names(r), office_titles(r)
        none = "not in the guide's data"
        items.append({"key": f"svc-{i}", "name": r["service"], "item_id": f"service-{i + 1}",
                      "facts": [", ".join(units) if units else "Government: " + none,
                                ("Official: " + "; ".join(offs)) if offs else "Official: " + none],
                      "status": r["status"],
                      "search": r["how_it_depends"] + " " + (r["contact"] or ""),
                      "body": h("dl", {"class": "svc-fields"},
                                h("dt", None, "Responsible government(s)"),
                                h("dd", None, listing(split_ids(r["responsible_unit_ids"]), unit_cell)),
                                h("dt", None, "Accountable elected official(s)"),
                                h("dd", None, listing(split_ids(r["accountable_office_ids"]), office_cell)),
                                h("dt", None, "How it depends"),
                                h("dd", None, r["how_it_depends"], c.cite(r["source_ids"]), " ", status_badge(r["status"], page),
                                  " ", status_badge("low", page) if r["confidence"] == "low" else None),
                                h("dt", None, "Contact"),
                                h("dd", None, r["contact"] or h("span", {"class": "muted"}, "Not in the guide's data")))})
    svc_list = entity_list("services-list", items, noun="service", search="Find a service, government or official",
                           label="Services and who handles them")
    roads = callout(h("p", None, h("strong", None, "Roads are a three-way split. "),
                      "The owner of the road decides who fixes it: the county for county roads, the city for city streets, "
                      "and INDOT for state routes, even inside a city", c.cite("SVC-001;SVC-002"), "."))
    page.add(section("services", 1, "Services and who handles them", roads, svc_list, tbl,
                     h("p", {"class": "muted"}, "Services the guide could not source are listed under Gaps rather than guessed. "
                       "Accountable officials come from the guide's office data; where the sources do not say which official or board "
                       "supervises a department, the cell says so."), scope="county", ed=ed))
    page.finish(gaps=ed.gaps(files=["gaps_services"], areas=["services"]))
    return page


# ---------------------------------------------------------------- your-governments

DEFAULT_PLACE = "south-bend"
RUN_FOR = {"city_council_member": "city-council", "county_council_member": "county-council",
           "school_board_member": "school-board", "township_board_member": "township-board",
           "township_trustee": "township-trustee", "precinct_committeeperson": "precinct-committeeperson"}


def _layer_href(page, ed, L):
    kind, _, uid = L.layer_id.partition(":")
    if kind == "state":
        return page.rel("state/index.html")
    if kind == "county":
        return page.rel("county/index.html")
    if kind in ("township", "municipality") and uid in ed.units and uid != "any":
        return page.rel(f"places/{uid}/index.html")
    if kind == "school":
        return page.rel("schools/index.html")
    return None


def _layer_unit(L):
    kind, _, uid = L.layer_id.partition(":")
    return {"county": "county"}.get(kind, uid if kind in ("township", "municipality", "school") else "")


def build_governments(site):
    """Your place (Wave D batch 6, review 3.1; was "Find your governments"). The result for the reader's saved place:
    one card per government that covers it, in layer order. The place picker and the seat diagram are the home page's
    (index.html#pick); this page no longer repeats them. With no saved place, an inline list of places (Q9): links to
    each place's page, which static/js/your_place.js turns into buttons that save the place and show its cards here.
    With JavaScript off every card is on the page. The path-stop ids #find, #offices and #meetings stay; the old
    picker and diagram ids are forwarded (YP_MOVED)."""
    ed = site.ed
    page = site.page("your-governments/index.html", banners=True)
    c = page.cites
    data = build_layers(ed)
    layers = data["layers"]
    # No place preselected (the reader's saved place is restored by static/js/your_place.js and here.js)
    place, sel_town, sel_school, visible = picker_state(data, None)
    vis = [L for L in layers.values() if L.layer_id in visible]
    n_gov = sum(1 for L in vis if L.government)
    n_el = sum(L.elected for L in vis)
    n_vote = sum(L.vote for L in vis)
    n_ap = sum(L.appointed for L in vis)
    from pages.landing import _unknown_split  # same rule as the landing hero: only elected unknowns make "at least"
    n_unknown = sum(_unknown_split(ed, L)[0] for L in vis)
    n_unknown_ap = sum(_unknown_split(ed, L)[1] for L in vis)
    pick = page.rel("index.html#pick")
    page.add(h("header", {"class": "page-hero"}, h("p", {"class": "eyebrow mono"}, "Your governments"),
               h("h1", None, page.title),
               h("p", {"class": "yp-showing", "id": "yp-showing", "tabindex": "-1", "data-js-only": True, "hidden": True},
                 h("span", {"class": "yp-showing-label mono"}, "Showing"), " ",
                 h("span", {"id": "yp-names"}, "no place picked yet"), " ",
                 h("a", {"class": "yp-change", "href": pick}, "Change place",
                   h("span", {"class": "visually-hidden"}, " on the home page picker"))),
               h("p", {"class": "dek", "id": "yp-dek"},
                 h("span", {"data-yp": "lead-none"}, "Everyone in the county lives under "),
                 h("span", {"data-yp": "lead-place", "hidden": True}, "Your place has "),
                 h("span", {"data-yp": "atleast-gov"}, "at least "),
                 h("strong", {"data-yp": "gov"}, n_gov), " governments, with ",
                 h("span", {"data-yp": "atleast", "hidden": None if (n_unknown or place is None) else True}, "at least "),
                 h("strong", {"data-yp": "elected"}, n_el), " elected seats (you vote for ",
                 h("strong", {"data-yp": "vote"}, n_vote), ") and ",
                 h("span", {"data-yp": "atleast-appointed", "hidden": None if n_unknown_ap else True}, "at least "),
                 h("strong", {"data-yp": "appointed"}, n_ap), " appointed seats. ",
                 status_badge("computed", page, "Counts computed from the guide's office, unit and board data."),
                 " ", h("a", {"href": page.rel("about/index.html#counting")}, "How we count")),
               h("p", {"class": "hero-badges"}, scope_badge("county", ed))))

    # ---- 1. your governments: the place list (no saved place), then one card per government
    munis = [p for p in data["places"] if p["muni"]]
    cities = [p for p in munis if p["kind"] == "city"] + [p for p in munis if p["kind"] != "city"]
    uninc = [p for p in data["places"] if not p["muni"]]

    def choice(p, label):
        return h("li", None, h("a", {"class": "yp-choice", "href": page.rel(place_page(p)), "data-yp-place": p["id"]},
                               label))

    choose = h("div", {"class": "yp-choose", "id": "place-picker", "data-yp-choose": True},
               h("p", {"class": "yp-choose-lead"},
                 h("span", {"class": "yp-nojs"},
                   "Each name opens that place's page. With JavaScript on, choosing a name here shows that place's "
                   "governments on this page and remembers it on this device."),
                 h("span", {"class": "yp-js", "hidden": True},
                   "No place is saved on this device yet. Choose yours to see the governments that cover it.")),
               h("div", {"class": "yp-pick-group", "id": "pick-places", "role": "group", "aria-labelledby": "pick-places-h"},
                 h("h3", {"class": "pick-h", "id": "pick-places-h"}, "Cities and towns"),
                 h("ul", {"class": "yp-choices"}, [choice(p, _short_place(p["label"])) for p in cities])),
               h("div", {"class": "yp-pick-group", "id": "pick-uninc", "role": "group", "aria-labelledby": "pick-uninc-h"},
                 h("h3", {"class": "pick-h", "id": "pick-uninc-h"}, "Outside a city or town? Your township"),
                 h("ul", {"class": "yp-choices"},
                   [choice(p, _short_place(p["label"].replace("Unincorporated ", ""))) for p in uninc])),
               h("p", {"class": "muted yp-choose-more"},
                 "To pick your township inside a city, or your school corporation, use the ",
                 h("a", {"href": pick}, "map and lists on the home page"), "."))
    from pages.elections_numbers import _current_holders   # officeholders/ has one fold (gov-<unit id>) per unit
    holder_units = {o["unit_id"] for o, _ in _current_holders(ed)}
    groups = [("everyone", "Every address in the county", ["state", "county", "library"]),
              ("townships", "Townships", ["township"]),
              ("munis", "Cities and towns", ["municipality"]),
              ("schools", "School corporations", ["school"])]
    blocks = []
    for gid, title, keys in groups:
        cards = [_gov_card(page, ed, L, holder_units) for k in keys for L in _ordered(layers) if L.key == k]
        blocks.append(h("div", {"class": "yp-group", "id": f"yp-{gid}", "data-yp-group": True},
                        h("h3", {"class": "yp-group-h", "id": f"yp-{gid}-h"}, title),
                        h("ul", {"class": "gov-list yp-cards", "aria-labelledby": f"yp-{gid}-h"}, cards)))
    page.add(section(
        "find", 1, "Your governments",
        choose,
        h("p", {"class": "yp-again", "data-js-only": True, "hidden": True},
          h("button", {"type": "button", "class": "btn btn-small", "id": "yp-again", "aria-controls": "place-picker",
                       "aria-expanded": "false"}, "Choose a different place here")),
        h("p", {"class": "muted yp-nojs"},
          "Without JavaScript this page lists every government in the county, grouped by kind. Each card names its "
          "seats, what its offices decide and where to read more."),
        h("p", {"class": "muted yp-js yp-none-note", "hidden": True},
          "Shown: the governments every address has, and the seats every township has. Choose your place above to "
          "add your township, city or town, and school corporation."),
        h("div", {"class": "yp-layers", "id": "layers"},
          h("div", {"id": "layer-list"}, blocks)),
        as_of_note(ed),
        callout(h("p", None, "For your exact districts, check the ",
                  h("a", {"href": "https://indianavoters.in.gov/", "target": "_blank", "rel": "noopener"}, "Indiana Voter Portal"),
                  ". The guide does not match addresses to districts."), kind="note"),
        h("p", {"class": "yp-browse"}, "Every government in the county: ",
          join([h("a", {"href": page.rel(p)}, t) for p, t in YP_BROWSE], h("span", {"aria-hidden": "true"}, " · ")), "."),
        scope="county", ed=ed))

    # ---- 2. offices: the full table (each card above lists its own offices)
    rows = []
    for o, row in _office_types(ed):
        slug = RUN_FOR.get(row["office_type"])
        cell = h("a", {"href": page.rel(f"run/{slug}/index.html")}, row["label"]) if slug else row["label"]
        ut = ed.unit_types.get(row["unit_type"], {}).get("label", row["unit_type"])
        rows.append([cell, ut, [row["what_it_does"], c.cite(row["source_ids"])],
                     f"{row['term_years']} years" if row["term_years"] else "Not in data"])
    page.add(section("offices", 2, "What each office controls",
                     h("p", None, "Each card above says what its own offices decide. Here is every office type in the "
                                  "guide's data in one table; offices with a Run for office page are linked."),
                     see_all_table("tbl-office-types", ["Office", "Level", "What it does", "Term"], rows,
                                   caption="Office types in the guide's data (offices with a Run for office page are linked)",
                                   noun="office type", min_width="44rem"),
                     scope="indiana", ed=ed))
    # ---- 3. meetings (static/js/here.js shows the saved place's governments; without JavaScript, all of them)
    items = []
    for L in _ordered(layers):
        if L.placeholder:
            continue
        uid = _layer_unit(L)
        u = ed.units.get(uid)
        site_url = (u or {}).get("website")
        if L.layer_id == "state":
            body = h("a", {"href": page.rel("state/your-legislators/index.html")}, "Your legislators")
        elif site_url:
            body = h("a", {"href": site_url, "target": "_blank", "rel": "noopener"}, site_url)
        else:
            body = h("span", {"class": "muted"}, "No website in the guide's data")
        items.append(h("li", {"class": "gov-site", "data-layer": L.layer_id}, h("strong", None, L.title), ": ", body))
    page.add(section("meetings", 3, "How to contact or attend a meeting",
                     h("p", None, "Start with the government's own website. Meeting times and places change, so the guide does not list them (see Gaps)."),
                     h("ul", {"class": "gov-sites"}, items), scope="county", ed=ed))
    page.add(moved_anchors(page, _yp_moved(layers)))
    page.finish(gaps=ed.gaps(files=["gaps_services"], areas=["governments"]))
    return page


# Links under the cards: every government page in the county, so this page is the hub of "Your governments"
YP_BROWSE = [("places/index.html", "Places"), ("county/index.html", "County"), ("schools/index.html", "Schools"),
             ("state/index.html", "State"), ("state/your-legislators/index.html", "Your legislators"),
             ("officeholders/index.html", "Who holds office now"), ("who-handles-this/index.html", "Who handles this?"),
             ("map/index.html", "Map")]

# officeholders/ fold ids per layer kind (pages/elections_numbers.py build_officeholders: gov-<unit id>)
_HOLDER_FOLDS = {"county": ["county", "sjc-courts"], "state": ["in-house", "in-senate"]}


def _office_types(ed):
    """(first office, office_types row) per office type, local governments only, in level then title order."""
    seen, out = set(), []
    order = {k: i for i, k in enumerate(["county", "city", "town", "township", "school_corporation", "library"])}
    for o in sorted(ed.tables["offices"], key=lambda o: (order.get(ed.units[o["unit_id"]]["unit_type"], 9), o["title"])):
        row = ed.office_type_row(o)
        if not row or row["office_type"] in seen or row["unit_type"] in ("state",):
            continue
        seen.add(row["office_type"])
        out.append((o, row))
    return out


def _yp_moved(layers) -> dict:
    """Ids the page had before Wave D batch 6 that are gone: the picker's township/school/status parts (on the home
    page's picker now), the diagram's per-layer toggle buttons (the card has the layer's id) and the layer payload."""
    moved = {i: f"index.html#{i}" for i in (
        "pick-township", "pick-township-h", "pick-township-note", "pick-school", "pick-school-h", "pick-school-note",
        "pick-status", "pick-status-text", "pick-clear", "layer-data")}
    for L in layers.values():
        rid = L.layer_id.replace(":", "-")
        moved[f"toggle-{rid}"] = f"your-governments/index.html#layer-{rid}"
    return moved


def _gov_card(page, ed, L, holder_units: set):
    """One government as a card: its seats, party breakdowns of its elected bodies, what its offices decide (a fold
    that ships open), and links to its page, its officeholders and the same unit on other topics. The card carries the
    layer's seat counts for your_place.js (the hero sums the cards shown)."""
    rid = L.layer_id.replace(":", "-")
    href = page.rel("index.html#pick") if L.placeholder else _layer_href(page, ed, L)
    title = {"township:any": "Your township (not picked yet)",
             "school:any": "Your school corporation (not picked yet)"}.get(L.layer_id, L.title)
    srcs = [x for g in L.groups for x in g.sources]
    counts = []
    if L.elected:
        counts.append(f"{L.elected} elected")
    if L.vote:
        counts.append(f"you vote for {L.vote}")
    if L.appointed:
        counts.append(f"{L.appointed} appointed")
    if L.unknown:
        counts.append("some seat counts not in data")
    seats = []
    for g in L.groups:
        if not g.kinds:
            continue
        titles = [t for t in g.titles if t]
        notes = [n for n in g.notes if n]
        line = [h("strong", None, g.label), f": {g.summary()}",
                h("span", {"class": "muted"}, f" ({'; '.join(notes)})") if notes else None]
        if len(titles) > 1:
            line.append(h("details", {"class": "gov-seats", "data-fold": "seats", "open": True},
                          h("summary", None, f"The {len(titles)} offices"),
                          h("ul", None, [h("li", None, t) for t in titles])))
        elif titles and titles[0] != g.label:
            line.append(h("span", {"class": "muted"}, f" ({titles[0]})"))
        seats.append(h("li", None, line))
    decide = []
    seen = set()
    for o in L.offices:
        row = ed.office_type_row(o)
        if not row or row["office_type"] in seen:
            continue
        seen.add(row["office_type"])
        slug = RUN_FOR.get(row["office_type"])
        decide.append(h("li", None, h("strong", None, row["label"]),
                        f" ({row['term_years']}-year term)" if row.get("term_years") else None, ": ",
                        row["what_it_does"], page.cites.cite(row["source_ids"]),
                        [" ", h("a", {"href": page.rel(f"run/{slug}/index.html")}, f"Run for {row['label'].lower()}")]
                        if slug else None))
    more = []   # the card's heading already links to the government's own page
    kind, _, uid = L.layer_id.partition(":")
    folds = _HOLDER_FOLDS.get(kind) or ([uid] if uid and uid != "any" else [])
    holders = [f for f in folds if f in holder_units]
    if holders:
        more.append((page.rel(f"officeholders/index.html#gov-{holders[0]}"), "Who holds these seats now"))
    unit = _layer_unit(L)
    if unit and unit in ed.units and not L.placeholder:
        for item in related_items(page, unit_id=unit):
            if item.key in ("results", "campaigns", "budget", "calendar"):
                more.append((item.href, f"{item.topic}: {item.text}"))
    if L.layer_id == "state":
        more.append((page.rel("state/your-legislators/index.html"), "Your legislators"))
    return h("li", {"class": "gov-item yp-card" + (" yp-placeholder" if L.placeholder else ""), "id": f"layer-{rid}",
                    "data-layer": L.layer_id, "data-gov": 1 if L.government else 0, "data-elected": L.elected,
                    "data-vote": L.vote, "data-appointed": L.appointed, "data-unknown": _unknown_split(ed, L)[0],
                    "data-unknown-appointed": _unknown_split(ed, L)[1]},
             h("h4", {"class": "gov-name yp-name"}, h("a", {"href": href}, title) if href else title,
               page.cites.cite_compact(srcs) if srcs else None),
             h("p", {"class": "yp-count mono"}, " · ".join(counts) if counts else "no seats in the guide's data yet"),
             h("div", {"class": "yp-body", "id": f"seats-{rid}"},
             h("ul", {"class": "yp-seats"}, seats) if seats else None,
             bodies_block(ed, L.offices, note=False) if L.offices else None,
             h("p", {"class": "party-asof muted"}, APPOINTED_NOTE) if L.appointed and not L.placeholder else None,
             h("p", {"class": "muted"}, L.note) if L.note else None,
             h("details", {"class": "yp-decide", "data-fold": "decide", "open": True},
               h("summary", None, f"What these offices decide ({len(decide)})"),
               h("ul", None, decide)) if decide else None,
             h("p", {"class": "yp-more"},
               join([h("a", {"href": u}, t) for u, t in more], h("span", {"class": "yp-sep", "aria-hidden": "true"}, " · ")))
             if more else None))


def _unknown_split(ed, L):
    from pages.landing import _unknown_split as split
    return split(ed, L)


def _short_place(name: str) -> str:
    return re.sub(r"^(City|Town) of |\s+Township$", "", name)



def _ordered(layers):
    order = ["state", "county", "township", "municipality", "school", "library"]
    return [L for k in order for L in layers.values() if L.key == k]


PAGES = {"run/index.html": build_run,
         "who-handles-this/index.html": build_who,
         "your-governments/index.html": build_governments,
         **{f"run/{s}/index.html": build_office(s) for s in ORDER}}
