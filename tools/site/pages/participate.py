"""Participation pages: Run for office (+ six office pages), Who handles this?, Find your governments."""
from __future__ import annotations

import re

from civic.components import as_of_note, bodies_block, callout, data_table, scope_badge, section, status_badge
from civic.data import fmt_date, split_ids
from civic.html import h, json_script
from civic.layers import build_layers, election_dates
from civic.picker import layer_rows, picker_state, place_picker

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
        bits.append(h("span", None, "2027 city offices: file a declaration by ", h("strong", None, "noon on Friday, Feb 5, 2027"),
                      " with the county election board", c.cite("SVC-018"), ". Opening day: ", CONFIRM))
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
               h("a", {"href": page.rel("elections/index.html#candidate-info")}, "candidate information section"), " of the elections page."))


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
          "not to the state database", c.cite("SVC-021"), ". ", status_badge("secondary", page,
                                                                         "Research summary; not checked against statute text.")),
        h("p", None, "The county's Candidate Filings page posts scanned CFA-4 reports (the receipts and spending report) and CFA-11 "
          "notices (large contributions)", c.cite("SVC-019;SVC-020"), ". The reports it has posted include annual, pre-primary, "
          "pre-election and pre-general periods", c.cite("SVC-020"), "."),
        h("p", None, "Due dates for each report: ", CONFIRM, " The guide's rules table has no campaign-finance schedule yet (see Gaps). ",
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
          " A candidate's two most recent primary votes must match the party they run under. ", status_badge(r["party_primaries"]["status"], page)),
        h("h3", None, "Petition (independent and minor-party candidates)"),
        h("p", None, r["independent_petitions"]["plain_language"], c.cite(r["independent_petitions"]["source_ids"]),
          " Petition forms for 2026: CAN-19 (state and legislative), CAN-21 (local), CAN-34 (school board); in 2026 petitions were due "
          "at noon on June 30, with the consent form at noon on July 15. For 2027 city and town offices the petition form is CAN-44",
          c.cite("ELX-007"), ". Deadlines for other years and the number of signatures: ", CONFIRM, " ",
          status_badge(r["independent_petitions"]["status"], page)),
        h("h3", None, "School board: party label instead of a primary"),
        h("p", None, r["partisan_school_board"]["plain_language"], c.cite(r["partisan_school_board"]["source_ids"]), " ",
          "A candidate's last two primary votes must match any party they list. ", status_badge(r["partisan_school_board"]["status"], page)),
    ]


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
        page.add(section("ballot-access", 3, "How you get on the ballot", _ballot_access(page, ed), scope="indiana", ed=ed))
        page.add(section("money", 4, "Campaign-finance duties", _finance(page, ed), scope="county", ed=ed))
        page.add(section("vacancies", 5, "Vacancies and caucuses", _vacancies(page, ed), scope="indiana", ed=ed))
        page.add(section("contacts", 6, "Where to file locally", _contacts(page, ed), _parties(page), scope="county", ed=ed))
        page.add(h("p", None, h("a", {"href": page.rel("run/index.html")}, "Back to Run for office")))
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
          " ", status_badge("low", page, "The four-year term and the county-chair rule come from an unsourced note.")),
        h("p", None, "Term length and next election year: ", CONFIRM),
        h("p", None, "Precinct committeepersons run in the party primary and file a separate form, CAN-37 (precinct committee or delegate)",
          c.cite(ed.rules["candidate_forms"]["source_ids"]), ". The county posts these filings on its Candidate Filings page: "
          "225 documents for 2026 and 60 for 2024 (document counts, not offices)", c.cite("SVC-019"), "."),
        h("p", None, "Filing window and deadline: ", CONFIRM),
    ]
    page.add(section("role", 1, "What the office does", role, scope="indiana", ed=ed))
    page.add(section("vacancies", 2, "Why it matters: caucuses", _vacancies(page, ed),
                     h("p", None, "A legislative vacancy is filled by a caucus of the departing member's party precinct committeepersons from "
                       "that district", c.cite(ed.rules["legislative_vacancy_caucus"]["source_ids"]), "."), scope="indiana", ed=ed))
    page.add(section("contacts", 3, "Where to file locally", _contacts(page, ed), _parties(page), scope="county", ed=ed))
    page.add(h("p", None, h("a", {"href": page.rel("run/index.html")}, "Back to Run for office")))
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
    # pick
    rows = []
    for slug in ORDER:
        link = h("a", {"href": page.rel(f"run/{slug}/index.html")}, LABELS[slug])
        if slug == "precinct-committeeperson":
            ot = ed.office_types[slug.replace("-", "_")]
            rows.append([link, "Not in data", "Local party office", "Confirm with the county election office"])
            continue
        spec = OFFICES[slug]
        ot = ed.office_types[spec["ot"]]
        rs = _rows(ed, slug)
        total = sum(_seats(s.split(" ")[0]) or 0 for _, _, s, _ in rs)
        ys = _years(ed, slug)
        rows.append([link, f"{total}+ across {len(rs)} government{'s' if len(rs) != 1 else ''}", f"{ot['term_years']} years", ", ".join(ys)])
    page.add(section("pick", 1, "Pick an office", h("p", None, "Seat counts and years come from the guide's office data", c.cite("GOV-001"), "."),
                     data_table("tbl-run-pick", ["Office", "Seats in the county", "Term", "Next regular election year(s)"], rows,
                                caption="Offices you could run for", numeric=(), min_width="36rem"), scope="county", ed=ed))
    # eligibility
    all_years = sorted({y for s in OFFICES for y in _years(ed, s)})
    el = [h("p", None, "Age, residence and registration rules differ by office: ", CONFIRM,
            " The only residence rule in the guide's data is that a township trustee must live in the township", c.cite("IND-013"), "."),
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
    tbl = data_table("tbl-services", ["Service", "Responsible government(s)", "Accountable elected official(s)",
                                      "How it depends", "Contact"], rows,
                     caption="Services and who handles them (sourced rows only)", min_width="60rem")
    roads = callout(h("p", None, h("strong", None, "Roads are a three-way split. "),
                      "The owner of the road decides who fixes it: the county for county roads, the city for city streets, "
                      "and INDOT for state routes, even inside a city", c.cite("SVC-001;SVC-002"), "."))
    page.add(section("services", 1, "Services and who handles them", roads, tbl,
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
    ed = site.ed
    page = site.page("your-governments/index.html", banners=True)
    c = page.cites
    data = build_layers(ed)
    layers = data["layers"]
    # No place preselected; static/js/here.js restores a returning reader's saved place.
    place, sel_town, sel_school, visible = picker_state(data, None)
    vis = [L for L in layers.values() if L.layer_id in visible]
    n_gov = sum(1 for L in vis if L.government)
    n_el = sum(L.elected for L in vis)
    n_ap = sum(L.appointed for L in vis)
    from pages.landing import _unknown_split  # same rule as the landing hero: only elected unknowns make "at least"
    n_unknown = sum(_unknown_split(ed, L)[0] for L in vis)
    page.add(h("header", {"class": "page-hero"}, h("p", {"class": "eyebrow mono"}, "Reference · Your governments"),
               h("h1", None, page.title),
               h("p", {"class": "dek"}, "For the place you pick: ",
                 h("span", {"data-count": "atleast-gov", "hidden": None if place is None else True}, "at least "),
                 h("strong", {"data-count": "gov"}, n_gov),
                 " governments, ", h("span", {"data-count": "atleast", "hidden": None if (n_unknown or place is None) else True}, "at least "),
                 h("strong", {"data-count": "elected"}, n_el), " elected seats and ", h("strong", {"data-count": "appointed"}, n_ap),
                 " appointed seats. ", status_badge("computed", page, "Counts computed from the guide's office, unit and board data."),
                 " ", h("a", {"href": page.rel("about/index.html#counting")}, "How we count")),
               h("p", {"class": "hero-badges"}, scope_badge("county", ed))))
    # ---- find
    page.add(section(
        "find", 1, "Find your governments",
        h("section", {"class": "layers-block", "id": "layers", "aria-label": "Governments and seats for the chosen place"},
          place_picker(page, data, heading_level="h4"),
          h("div", {"class": "layers", "id": "layer-list"}, layer_rows(page, layers, visible)),
          as_of_note(ed)),
        h("h3", None, "Links to each government and its seats"),
        h("p", {"class": "muted"}, "The list follows your choices above."),
        h("ul", {"class": "gov-list"}, [_gov_item(page, ed, L, L.layer_id in visible) for L in _ordered(layers)]),
        callout(h("p", None, "For your exact districts, check the ",
                  h("a", {"href": "https://indianavoters.in.gov/", "target": "_blank", "rel": "noopener"}, "Indiana Voter Portal"),
                  ". The guide does not match addresses to districts."), kind="note"),
        scope="county", ed=ed))
    # ---- offices
    seen, rows = set(), []
    order = {k: i for i, k in enumerate(["county", "city", "town", "township", "school_corporation", "library"])}
    for o in sorted(ed.tables["offices"], key=lambda o: (order.get(ed.units[o["unit_id"]]["unit_type"], 9), o["title"])):
        row = ed.office_type_row(o)
        if not row or row["office_type"] in seen or row["unit_type"] in ("state",):
            continue
        seen.add(row["office_type"])
        label = row["label"]
        slug = RUN_FOR.get(row["office_type"])
        cell = h("a", {"href": page.rel(f"run/{slug}/index.html")}, label) if slug else label
        ut = ed.unit_types.get(row["unit_type"], {}).get("label", row["unit_type"])
        rows.append([cell, ut, [row["what_it_does"], c.cite(row["source_ids"])], f"{row['term_years']} years" if row["term_years"] else "Not in data"])
    page.add(section("offices", 2, "What each office controls", data_table(
        "tbl-office-types", ["Office", "Level", "What it does", "Term"], rows,
        caption="Office types in the guide's data (offices with a Run for office page are linked)", min_width="44rem"),
        scope="indiana", ed=ed))
    # ---- meetings
    items = []
    for L in _ordered(layers):
        uid = _layer_unit(L)
        u = ed.units.get(uid)
        site_url = (u or {}).get("website")
        if L.layer_id == "state":
            body = h("a", {"href": page.rel("state/your-legislators/index.html")}, "Your legislators")
        elif site_url:
            body = h("a", {"href": site_url, "target": "_blank", "rel": "noopener"}, site_url)
        else:
            body = h("span", {"class": "muted"}, "No website in the guide's data")
        items.append(h("li", {"class": "gov-site", "data-layer": L.layer_id, "hidden": None if L.layer_id in visible else True},
                       h("strong", None, L.title), ": ", body))
    page.add(section("meetings", 3, "How to contact or attend a meeting",
                     h("p", None, "Start with the government's own website. Meeting times and places change, so the guide does not list them (see Gaps)."),
                     h("ul", {"class": "gov-sites"}, items), scope="county", ed=ed))
    dates = election_dates(ed, sorted({y for L in layers.values() for y in L.next}))
    payload = {"places": data["places"],
               "dates": {y: {"primary": fmt_date(d["primary"]), "general": fmt_date(d["general"])} for y, d in dates.items()}}
    page.add(json_script("layer-data", payload))
    page.finish(gaps=ed.gaps(files=["gaps_services"], areas=["governments"]))
    return page


def _ordered(layers):
    order = ["state", "county", "township", "municipality", "school", "library"]
    return [L for k in order for L in layers.values() if L.key == k]


def _gov_item(page, ed, L, is_visible):
    href = _layer_href(page, ed, L)
    name = h("a", {"href": href}, L.title) if href else L.title
    groups = []
    for g in L.groups:
        if not g.kinds:
            continue
        titles = [t for t in g.titles if t]
        body = h("details", {"class": "gov-seats"}, h("summary", None, f"{g.label}: {g.summary()}"),
                 h("ul", None, [h("li", None, t) for t in titles])) if titles and len(titles) > 1 else \
            h("p", {"class": "gov-seat"}, f"{g.label}: {g.summary()}" + (f" ({titles[0]})" if titles else ""))
        groups.append(body)
    return h("li", {"class": "gov-item", "data-layer": L.layer_id, "hidden": None if is_visible else True},
             h("h4", {"class": "gov-name"}, name), groups,
             bodies_block(ed, L.offices, note=False) if L.offices else None,
             h("p", {"class": "muted"}, L.note) if L.note else None)


PAGES = {"run/index.html": build_run,
         "who-handles-this/index.html": build_who,
         "your-governments/index.html": build_governments,
         **{f"run/{s}/index.html": build_office(s) for s in ORDER}}
