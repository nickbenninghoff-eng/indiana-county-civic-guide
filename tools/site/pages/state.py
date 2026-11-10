"""State government pages: state/index.html, state/your-legislators/index.html,
state/how-the-state-shapes-local/index.html."""
from __future__ import annotations

import re
from collections import defaultdict

from civic.charts import columns, results_bars
from civic.components import (bodies_block, name_party_text, name_with_party, callout, data_table, officeholder_card,
                              party_label, scope_badge, section, see_all_fold, status_badge)
from civic.district_map import district_map, district_set, load_district_shapes
from civic.map import load_shapes
from civic.pick_one import one_bar, one_fold, one_summary
from civic.data import PARTY_LABELS, fmt_date, parse_date, split_ids
from civic.html import h, join
from civic.seat_split import seat_split
from civic.related import related_items, related_rail
from civic.campaign_money import STATE_AREA, area_path

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
        # one nowrap span per code (static/css/state.css .rule-code): lines break between codes, not at their hyphens
        codes = [c.strip() for c in r["statute"].split(";") if c.strip()]
        meta.append(h("span", None, "Statute: ",
                      join([h("span", {"class": "rule-code"}, c + (";" if i < len(codes) - 1 else ""))
                            for i, c in enumerate(codes)], " ")))
    if r.get("effective"):
        meta.append(h("span", {"class": "rule-code"}, f"Effective: {fmt_date(r['effective'])}"))
    det = _clean_detail(r.get("detail", "")) if detail else ""
    return h("div", {"class": "rule-block"},
             h("h3", None, heading) if heading else None,
             h("p", None, r["plain_language"], page.cites.cite(r["source_ids"]), " ",
               status_badge(r["status"], page), " ", status_badge("low", page) if r.get("confidence") == "low" else None),
             h("p", {"class": "muted"}, det) if det else None,
             extra,
             h("p", {"class": "rule-meta mono muted"}, join(meta, " · ")) if meta else None)


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


def _results_summary(page, key, by_year: dict, title: str):
    """One row per general election for one district: the candidates in the canvass's order with votes, share and
    the result as recorded, and what the votes cover (the county portion, unless the row says district-wide)."""
    c = page.cites
    rows = []
    for year in sorted(by_year, reverse=True):
        rs = by_year[year]
        bits = []
        for r in rs:
            scope = _result_scope(r)
            try:
                votes = f"{int(float(r['votes'])):,} votes"
            except ValueError:
                votes = "votes not recorded"
            share = f", {float(r['pct']):.1f}%" if r.get("pct") else ""
            res = _result_text(r, scope)
            bits.append(h("span", {"class": "res-cand"}, name_with_party(r["candidate"], r["party"]), f" {votes}{share}",
                          h("span", {"class": "muted"}, f" · {res[:1].lower() + res[1:]}") if res != "Not determined" else None))
        scopes = list(dict.fromkeys(_result_scope(r) for r in rs))
        sts = list(dict.fromkeys(r["status"] for r in rs))
        srcs = ";".join(dict.fromkeys(x for r in rs for x in split_ids(r["source_ids"])))
        rows.append([f"{year} general", h("span", None, join(bits, "; "),
                                          h("span", {"class": "muted"}, " Uncontested.") if len(rs) == 1 else None),
                     "; ".join(scopes), h("span", None, join([status_badge(x, page) for x in sts], " "), c.cite(srcs))])
    return data_table(f"results-{key[0]}-{key[1]}-summary", ["Election", "Candidates (canvass order)",
                                                              "What the votes cover", "Status"],
                      rows, caption=f"{title}: one row per general election", min_width="44rem")


CF_BASIS = ("Campaign money is by filing year: totals of the items on reports FILED in each calendar year, not "
            "election-cycle totals. One campaign spans two or more years, and the latest year is partial.")
CF_DOWNLOAD = "2026-11-07"
LEG_SETS = (("house", "in-house-2021", "Indiana House"), ("senate", "in-senate-2021", "Indiana Senate"))


def _same_person(a: str, b: str) -> bool:
    """Committee candidate names and terms names can differ ('Timothy Wesco', 'Tim Wesco'): same last name and
    same first initial."""
    pa = re.sub(r"[^a-z ]", "", (a or "").lower()).split()
    pb = re.sub(r"[^a-z ]", "", (b or "").lower()).split()
    if not pa or not pb:
        return False
    return pa[-1] == pb[-1] and pa[0][0] == pb[0][0]


def leg_state(ed, o: dict) -> dict:
    """Who holds a legislative seat now, who leads the unofficial 2026 count, and the words used for both.
    A seat with no settled holder is reported as having no current member (never guessed)."""
    terms = ed.terms_on(o["office_id"], ed.as_of)
    current = [t for t in terms if t["status"] != "unofficial"]
    incoming = [t for t in ed.terms_for(o["office_id"]) if t["status"] == "unofficial"]
    now = ", ".join(name_party_text(t["person"], t.get("party")) for t in current) or \
        "No current member in the guide's data"
    inc_txt = ""
    if incoming:
        same = {t["person"] for t in current} == {t["person"] for t in incoming}
        names = ", ".join(name_party_text(t["person"], t.get("party")) for t in incoming)
        inc_txt = ("Re-elected Nov 3, 2026 (unofficial)" if same else
                   f"{names} leads the unofficial Nov 3, 2026 count")
    since = ", ".join(fmt_date(t["start"]) or "start date not in sources" for t in current)
    return {"current": current, "incoming": incoming, "now": now, "incoming_text": inc_txt, "since": since}


def _committee_role(row: dict, st: dict, past: list[dict]) -> str:
    if any(_same_person(row["candidate"], t["person"]) for t in st["current"]):
        return "member"
    if any(_same_person(row["candidate"], t["person"]) for t in st["incoming"]):
        return "unofficial 2026 leader"
    if any(_same_person(row["candidate"], t["person"]) for t in past):
        return "former member"
    return "candidate"


ROLE_ORDER = {"member": 0, "unofficial 2026 leader": 1, "candidate": 2, "former member": 3}


def committees_for(ed, o: dict, st: dict, rows: list[dict]) -> list[tuple[str, str, list[dict]]]:
    """[(committee, role, rows by year)] for one district: the member first, then the 2026 leader, then the rest."""
    past = ed.terms_for(o["office_id"])
    by = {}
    for r in rows:
        by.setdefault(r["committee"], []).append(r)
    out = [(com, _committee_role(rs[0], st, past), sorted(rs, key=lambda r: int(r["year"]))) for com, rs in by.items()]
    return sorted(out, key=lambda t: (ROLE_ORDER[t[1]], t[0]))


def cf_years_text(rs: list[dict], last_year: int) -> str:
    """The committee's latest two filing years, e.g. '2025 filings: raised $1, spent $2; 2026 filings (partial, ...)'."""
    parts = []
    for r in rs[-2:]:
        y = int(r["year"])
        part = f" (partial, to {fmt_date(CF_DOWNLOAD)})" if y == last_year else ""
        parts.append(f"{y} filings{part}: raised {_money(float(r['receipts'] or 0))}, "
                     f"spent {_money(float(r['expenditures'] or 0))}")
    return "; ".join(parts)


def leg_entry(o: dict, st: dict, coms, cover: str, share, href: str, last_year: int) -> dict:
    """The map panel record for one district (static/js/map.js reads n, t, f, cav, href, open)."""
    facts = [["Member now", st["now"]]]
    if st["since"]:
        facts.append(["In office since", st["since"]])
    if st["incoming_text"]:
        facts.append(["Nov 3, 2026 election", st["incoming_text"]])
    nxt = o.get("next_election") or "not in the guide's data"
    facts.append(["Next election", f"{nxt} ({o['term_years']}-year term)" if o.get("term_years") else nxt])
    if coms:
        for com, role, rs in coms:
            r0 = rs[-1]
            facts.append([f"Campaign money: {name_party_text(r0['candidate'], r0['party'])}, {role}",
                          cf_years_text(rs, last_year)])
    else:
        facts.append(["Campaign money", "No committee for this district in the guide's state campaign-finance data"])
    cav = [CF_BASIS] if coms else []
    cav.append(cover)
    if share is not None:
        cav.append(f"About {share * 100:.0f}% of the county's land area is in this district (computed from the official "
                   "boundary). Only the part inside the county is drawn.")
    return {"n": o["title"], "t": "State legislature", "f": facts, "cav": cav, "note": "", "href": href,
            "open": "Show this district's details"}


def build_legislators(site):
    ed = site.ed
    page = site.page("state/your-legislators/index.html", banners=True)
    c = page.cites
    county = ed.county_label
    hos = [o for o in ed.offices_for("in-house")]
    sos = [o for o in ed.offices_for("in-senate")]
    toc = [("districts", "Find your district"), ("members", "Each district"), ("results", "Results, 2012 to 2026"),
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

    def did(key):
        return f"district-{key[0]}-{key[1]}"

    def cover_text(key):
        yrs = sorted(whole_years.get(key, []))
        if yrs:
            return ("The county's totals equal the district totals for " +
                    ", ".join(str(y) for y in yrs) + ". In the other years shown, the guide has only the county's tally.")
        return "Only the county portion of the district's results is known in every year shown."

    cf = ed.table("cf_state")
    cf_years = sorted({int(r["year"]) for r in cf})
    last_cf = cf_years[-1] if cf_years else 0
    states = {key: leg_state(ed, office_for(key)) for key in keys}

    def cf_rows_for(key):
        code = ("HD" if key[0] == "house" else "SD") + key[1]
        return [r for r in cf if r["district"] == code]

    # ---------------------------------------------------------------- 1 find your district: map + table
    shapes = load_shapes(ed)
    dshapes = load_district_shapes(ed, shapes) if shapes else None
    layers, mapped = [], set()
    for chamber, set_id, label in LEG_SETS:
        rec = district_set(dshapes, set_id)
        if not rec:
            continue
        items = []
        for it in rec["items"]:
            num = re.sub(r"\D", "", it["district"])
            key = (chamber, num)
            o = office_for(key)
            if not o or key not in keys:
                ed.warnings.append(f"legislators map: {set_id} district {it['district']} has no office in offices.csv; left off")
                continue
            mapped.add(key)
            entry = leg_entry(o, states[key], committees_for(ed, o, states[key], cf_rows_for(key)), cover_text(key),
                              it.get("county_share"), f"#{did(key)}", last_cf)
            items.append({"uid": f"{chamber}-{num}", "district": it["district"], "d": it["d"], "href": f"#{did(key)}",
                          "aria": f"{o['title']}: {states[key]['now']}. Show this district's details.",
                          "entry": entry, "text": num, "label": it["label"], "label_r": it["label_r"]})
        missing = [office_for(k)["title"] for k in keys if k[0] == chamber and k not in mapped]
        chamber_word = "House" if chamber == "house" else "Senate"
        legend = [h("p", None, f"Indiana {chamber_word} districts from the 2021 redistricting, used for the 2022 to 2030 "
                               "elections. They reach past the county line; only the part inside the county is drawn.",
                    c.cite_compact(rec.get("source_ids", ""))),
                  h("p", None, "Not on the map (no boundary in the guide's data): " + ", ".join(missing) + ".")
                  if missing else None]
        layers.append({"tab": chamber, "label": label, "items": items, "legend": legend})
    dmap = None
    if layers:
        dmap = district_map(page, ed, shapes, layers, layers[0]["tab"],
                            label=f"Map of the Indiana House and Senate districts that include part of {county}. Every "
                                  "district is a link to its details; the table below lists the same districts.",
                            hint="Hover, focus or tap a district to see its member, the next election and their campaign "
                                 "money here. Select it again, or use the link, to show its details below.",
                            notes=h("div", {"class": "dmap-notes"},
                                    h("p", None, CF_BASIS, c.cite_compact("MON-020;MON-021;MON-022")),
                                    h("p", None, "Party labels are shown as the guide's sources print them. The map is "
                                                 "not shaded by party or by money.")))
    drows = []
    for key in keys:
        o = office_for(key)
        drows.append([h("a", {"href": f"#{did(key)}"}, o["title"]), states[key]["now"],
                      f"{o['term_years']} years", o.get("next_election", ""),
                      h("span", None, cover_text(key), c.cite(o["source_ids"]))])
    page.add(section("districts", 1, "Find your district",
                     h("p", None, f"{len(keys)} districts include part of {county}. "
                                  + ("Pick one on the map or in the table to see who holds it, its results and its "
                                     "campaign money; the other districts fold away." if dmap else
                                     "Pick one in the table to see who holds it, its results and its campaign money.")),
                     dmap,
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
                     data_table("districts-table", ["District", "Member now", "Term", "Next election",
                                                    "What is known about the district's extent"],
                                drows, caption="Legislative districts that include part of the county", min_width="52rem"),
                     scope="county", ed=ed))

    # ---------------------------------------------------------------- 2 each district (one fold per district)
    xrows = []
    for key in keys:
        ct = ed.contests.get(f"2026g-state-{key[0]}-{key[1]}")
        if not ct or _result_scope(ct["rows"][0]).startswith("Whole district") or \
                any(y >= 2022 for y in whole_years.get(key, ())):
            continue  # wholly inside the county on the 2021 map (used from 2022)
        o = office_for(key)
        inc = [t for t in ed.terms_for(o["office_id"]) if t["status"] == "unofficial"]
        wide = None
        for t in inc:
            m = re.search(r"district-wide[^;]*?\(([\d,]+) to ([\d,]+)\)", t.get("notes", ""))
            if m:
                wide = (t, m)
        # a blank vote count says so (it crashed the page; debug pass 2026-11-09)
        tally = h("span", None, join([h("span", None, name_with_party(r["candidate"], r["party"]),
                                        f" {int(float(r['votes'])):,}" if (r["votes"] or "").strip() else " (votes not in the data)")
                                      for r in ct["rows"]], "; "))
        xrows.append([h("a", {"href": f"#{did(key)}"}, o["title"]), tally,
                      (f"{wide[1].group(1)} to {wide[1].group(2)}, led by {wide[0]['person']} (Ballotpedia)"
                       if wide else "Not in the guide's data"),
                      h("span", None, status_badge("unofficial", page),
                        c.cite(ct["rows"][0]["source_ids"] + ";GOV-044;GOV-045"))])
    hd7_note = h("div", None,
                 h("h3", None, "2026 races in districts that extend outside the county"),
                 h("p", None, "For districts that cross the county line, the county tally does not decide the race. The same "
                              "fields are shown for each of them:"),
                 data_table("cross-county-2026", ["District", "County tally (unofficial)", "District-wide count (unofficial)",
                                                  "Status"], xrows,
                            caption="2026 races in districts that extend outside the county", min_width="44rem")) \
        if xrows else None

    folds = []
    for key in keys:
        o = office_for(key)
        st = states[key]
        note = None
        if st["incoming"]:
            same = {t["person"] for t in st["current"]} == {t["person"] for t in st["incoming"]}
            note = ("Re-elected Nov 3, 2026 (unofficial)." if same else
                    "A different person leads the unofficial Nov 3, 2026 count.") + \
                   (" A legislator's term begins the day after the general election (Ballotpedia lists the 2026 "
                    "winners as taking office Nov 4, 2026); results are unofficial until certified.")
        card = officeholder_card(ed, page, o, st["current"], st["incoming"], note)
        fig = None
        ct = ed.contests.get(f"2026g-state-{key[0]}-{key[1]}")
        if ct:
            # blank votes or share: results_bars prints "votes not recorded" (int(float("")) crashed the page)
            cands = [{"name": r["candidate"], "party": r["party"],
                      "votes": int(float(r["votes"])) if (r["votes"] or "").strip() else None,
                      "pct": float(r["pct"]) if (r["pct"] or "").strip() else None, "winner": ""} for r in ct["rows"]]
            fig = results_bars(f"res26-{key[0]}-{key[1]}", f"{o['title']}, county portion", cands,
                               subtitle="Nov 3, 2026", status="unofficial",
                               note="County portion only unless the table below says the totals match the district. "
                                    "No winner is marked: the figures are unofficial.",
                               page=page, cite=c.cite(ct["rows"][0]["source_ids"]))
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
        # results: one row per election (candidates in ballot order, what the votes cover); every row in a fold
        n_res = len(trs)
        results = [h("h4", {"id": f"results-{key[0]}-{key[1]}"}, f"{o['title']}: results, 2012 to 2026"),
                   _results_summary(page, key, contests[key], o["title"]) if trs else None,
                   see_all_fold(f"results-{key[0]}-{key[1]}-all", n_res,
                                data_table(f"results-{key[0]}-{key[1]}-table",
                                           ["Election", "Candidate", "Party", "Votes", "Share", "Result as recorded",
                                            "What the votes cover", "Status"],
                                           trs, caption=f"{o['title']}: general election results, 2012 to 2026",
                                           numeric=(3, 4), min_width="60rem"),
                                noun="result row", label=f"See all {n_res} result rows, one per candidate",
                                hint="Party · share · Copy CSV") if trs else
                   h("p", {"class": "muted"}, "No general election results for this district in the guide's data.")]
        coms = committees_for(ed, o, st, cf_rows_for(key))
        crow = []
        for com, role, rs in coms:
            for r in rs:
                crow.append([r["committee"], role, r["year"] + (" (partial)" if int(r["year"]) == last_cf else ""),
                             _money(float(r["receipts"] or 0)), _money(float(r["expenditures"] or 0)),
                             h("span", None, status_badge(r["status"], page), c.cite(r["source_ids"]))])
        sl = area_path(STATE_AREA)
        sl_link = (h("a", {"href": page.rel(sl)}, "State legislators' committees on the campaign money pages")
                   if sl in page.site.by_path else None)
        if crow:
            money_block = [h("h4", {"id": f"cf-{key[0]}-{key[1]}-h"}, "Campaign money, by filing year"),
                           h("p", {"class": "muted"}, CF_BASIS + " Only the committees of members and 2026 candidates in "
                                                      "the guide's data are included. ",
                             h("a", {"href": "#money"}, "Every district's committees"),
                             [" · ", sl_link] if sl_link else None),
                           h("ul", {"class": "leg-cf"},
                             [h("li", None, h("strong", None, com), f" ({role}): ", cf_years_text(rs, last_cf), ". ",
                                status_badge(rs[-1]["status"], page),
                                c.cite(";".join(dict.fromkeys(x for r in rs for x in split_ids(r["source_ids"])))))
                              for com, role, rs in coms]),
                           see_all_fold(f"cf-{key[0]}-{key[1]}-all", len(crow),
                                        data_table(f"cf-{key[0]}-{key[1]}", ["Committee", "Whose", "Filing year", "Receipts",
                                                                             "Expenditures", "Status"],
                                                   crow, caption=f"{o['title']}: campaign committees by filing year (not election cycles)",
                                                   numeric=(3, 4), min_width="44rem"),
                                        noun="filing-year row", label=f"See all {len(crow)} filing-year rows: receipts and "
                                                                      "expenditures")]
        else:
            money_block = [h("p", {"class": "muted"}, "No campaign committee for this district is in the guide's state "
                                                      "campaign-finance data.", [" ", sl_link] if sl_link else None)]
        rail = related_rail([i for i in related_items(page, office_id=o["office_id"]) if i.key != "campaigns"],
                            name=o["title"], rail_id=f"related-{key[0]}-{key[1]}", heading_tag="h4")
        digest = [f"Member now: {st['now']}",
                  f" · {st['incoming_text']}" if st["incoming_text"] else "",
                  f" · Next election {o['next_election']}" if o.get("next_election") else ""]
        body = [h("p", {"class": "muted"}, cover_text(key), c.cite(o["source_ids"])),
                h("div", {"class": "card-grid leg-grid"}, card, fig),
                rail, results, money_block]
        folds.append(one_fold(f"{key[0]}-{key[1]}", o["title"], one_summary("h3", o["title"], digest), body,
                              item_id=did(key)))
    page.add(section("members", 2, "Each district: who holds it, results and campaign money",
                     h("p", None, f"From the guide's terms data, as of {fmt_date(ed.as_of, long=True)}. Seats are listed by "
                                  "chamber and district number, not by party. Members elected on Nov 3, 2026 are unofficial "
                                  "until results are certified. Open a district to see its member, every general election "
                                  "since 2012 and its campaign committees."),
                     h("h3", None, "The county's delegation by party"),
                     bodies_block(ed, [], extra_bodies={"State House members": hos, "State Senate members": sos}),
                     one_bar("district", "districts", "Pick a district on the map or in the table above. Every district "
                                                      "is listed below; open any of them."),
                     h("div", {"class": "one-list"}, folds),
                     hd7_note,
                     scope="county", ed=ed))

    # ---------------------------------------------------------------- 3 results: how to read them
    page.add(section("results", 3, "Results, 2012 to 2026",
                     h("p", None, "These are the county's own canvass tallies for each general election, in the order the "
                                  "canvass lists the candidates. Indiana law orders the parties on the ballot by their vote "
                                  "for Secretary of State in the county at the last election; in 2022 Wells (D) received "
                                  "34,746 and Morales (R) 33,748, so Democrats are listed first on the 2024 and 2026 county "
                                  "ballots.", c.cite("IND-056;RES-023"), " They are the county portion of each race unless the "
                                  "\"What the votes cover\" column says otherwise. Only one row, the 2018 House District 8 "
                                  "result, is a district-wide total, taken from Ballotpedia because the county line could not "
                                  "be read from the scan; it is labeled district-wide and is not the county tally."),
                     h("p", {"class": "muted"}, "The 2026 charts mark no winner: the figures are unofficial, and for most "
                                                "districts the county portion is not the district result."),
                     h("h3", None, "Every general election in the data, by district"),
                     h("p", None, "Each district's results table is in its section above:"),
                     h("ul", {"class": "leg-jump"},
                       [h("li", None, h("a", {"href": f"#results-{k[0]}-{k[1]}"}, office_for(k)["title"])) for k in keys]),
                     scope="county", ed=ed))

    # ---------------------------------------------------------------- 4 money: every district, compared
    cf_src = ";".join(dict.fromkeys(s for r in cf for s in split_ids(r["source_ids"])))
    years = cf_years
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
                    breaks=[{"after": last_full, "label": "Partial",
                             "tip": f"{years[-1]} includes only filings up to the data download ({CF_DOWNLOAD})"}],
                    note="Filing-year basis: each bar adds up the items on reports filed in that calendar year, not an election "
                         "cycle. The number of committees changes by year (some began later), so a rise or fall can reflect "
                         "which committees are in the data.",
                    status="computed", page=page, headers=["Filing year", "Receipts, all listed committees"],
                    cite=c.cite(cf_src))

    def ck(r):
        d = r["district"]
        return (0 if d.startswith("HD") else 1, int(re.sub(r"\D", "", d)), r["committee"])
    committees = sorted({(r["committee"], r["candidate"], r["district"]) for r in cf},
                        key=lambda t: ck({"district": t[2], "committee": t[0]}))
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
                                  "in these districts. Each district's own committees are also in its section above."),
                     callout(h("p", None, h("strong", None, "Read these totals carefully. "),
                               "(1) They are by calendar year filed, not by election cycle, so one campaign spans two or more "
                               "rows. (2) Contributors were typed in by name and spellings vary, so name-level totals would "
                               "be understated; the guide shows only the contributor type codes as filed. (3) The data has no "
                               "cash-on-hand figure. (4) Only committees for the members and 2026 candidates listed here are "
                               "included, not every opponent.", c.cite("MON-020;MON-021;MON-022")), kind="note"),
                     chart,
                     h("p", None, "Each district's own committees are summarized in its item above. The tables below "
                                  "list every committee in the data: receipts by filing year, then every row with "
                                  "expenditures and the top contributor types as filed."),
                     see_all_fold("cf-matrix-all", len(matrix),
                                  data_table("cf-matrix", ["Committee (district)"] + [str(y) for y in years], matrix,
                                             caption="Receipts by committee and filing year (a dash means no committee data for that year)",
                                             numeric=tuple(range(1, len(years) + 1)), min_width="64rem"),
                                  noun="committee", label=f"See all {len(matrix)} committees: receipts by committee and "
                                                          "filing year"),
                     see_all_fold("cf-long-all", len(long_rows),
                                  data_table("cf-long", ["Committee", "District", "Filing year", "Receipts", "Expenditures",
                                                         "Top contributor types (amount, as filed)", "Status"],
                                             long_rows, caption="State legislative committees, receipts and expenditures by filing year",
                                             numeric=(2, 3, 4), min_width="60rem"),
                                  noun="row", label=f"See all {len(long_rows)} rows: receipts, expenditures and top "
                                                    "contributor types"),
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
    if layers:
        gaps.append({"item": "Legislative district map: the 2022 vintage was not compared",
                     "why_missing": "The map uses the Census TIGERweb 2026-vintage House and Senate layers for the 2021 "
                                    "redistricting plan. They should be the shapes used since 2022, but the 2022 vintage "
                                    "was not compared.",
                     "how_to_fill": "Compare against the Census TIGER 2022 state legislative district files."})
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
