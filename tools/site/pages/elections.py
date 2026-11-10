"""Elections section: the elections hub (elections/index.html), how elections work (elections/how-it-works/), calendar,
results explorer, judges and public questions. The elections-by-the-numbers pages (landscape overview, margins, turnout, officeholders) are
pages/elections_numbers.py; it shares the helpers here (classify, margin, the turnout chart).

Every figure comes from data/indiana/election_rules.csv, data/editions/<ed>/elections.csv,
results.csv, offices.csv, terms.csv and the source files. Computed values (margins, turnout
comparisons, calendar years, term-limit status) carry the COMPUTED badge and say how they
were computed.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

from civic.charts import columns, hbar, legend, results_bars
from civic.components import (STATUS, callout, data_table, entity_list, filter_empty_note, see_all_table, table_filter, party_label, scope_badge, section, status_badge,
                              variant_slot)
from civic.data import (PARTY_LABELS, SELECTED_BY_LABELS, fmt_date, fmt_int, nth_weekday_after, parse_date,
                        split_ids)
from civic.html import Markup, h, json_script
from civic.related import contest_anchor, contest_href
from civic.map import load_shapes, load_votes, race_by_contest
from civic.preselect import here_layer, here_slot

YEARS = list(range(2026, 2031))
UP_NEXT_YEARS = (2027, 2028)   # calendar rows that show the holder now and the term-limit status
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


def _statute_codes(text: str) -> list:
    """A statute field ("IC 3-11-2-10; 3-11-2-9") as one nowrap span per code (static/css/elections.css .elx-code), so a
    line breaks between codes, never at the hyphens inside one."""
    parts = [p.strip() for p in text.split(";") if p.strip()]
    out = []
    for i, part in enumerate(parts):
        out.append(h("span", {"class": "elx-code"}, part + (";" if i < len(parts) - 1 else "")))
        if i < len(parts) - 1:
            out.append(" ")
    return out


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
             " " if r.get("statute") else None,
             h("span", {"class": "elx-statute mono"}, _statute_codes(r["statute"])) if r.get("statute") else None)


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


SHORT_TYPE = {"general": "general", "primary": "primary", "municipal_general": "municipal general",
              "municipal_primary": "municipal primary", "special": "special"}


def _election_short(e) -> str:
    """'Nov 3, 2026 general': the election's date and kind in a few words (tables with many rows)."""
    return f"{fmt_date(e['date'])} {SHORT_TYPE.get(e['type'], e['type'])}"


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


SCHOOL_UNITS = {"south-bend-schools": "sbcsc", "mishawaka-schools": "school-city-mishawaka",
                "penn-harris-madison-schools": "phm", "john-glenn-schools": "john-glenn",
                "union-north-schools": "union-north", "new-prairie-schools": "new-prairie"}


def contest_layer(ed, c) -> str:
    """The saved-place layer (civic/preselect.py here_layer) of the voters who decide a contest: "state" for statewide,
    appellate and legislative contests, "county" for county-wide ones, else the city, town, township or school
    corporation from the contest id. "" when none fits (LaVille schools: no unit in the guide's data), and then the
    preselect never hides the contest. Added 2026-11-09 (Wave E batch 8)."""
    group, place, _ = classify(c)
    if place.startswith(("Statewide", "Legislative district")):
        return "state"
    rest = _rest(c)
    for prefix, uid in SCHOOL_UNITS.items():
        if rest.startswith(prefix):
            return here_layer(ed, uid)
    if rest.startswith(SCHOOLS):
        return ""
    if place == "St. Joseph County" or rest.startswith("county-"):
        return "county"
    m = re.match(r"([a-z]+)-township-", rest)
    if m and f"{m.group(1)}-township" in ed.units:
        return here_layer(ed, f"{m.group(1)}-township")
    for uid in ("south-bend", "mishawaka") + TOWNS:
        if rest.startswith(uid + "-"):
            return here_layer(ed, uid)
    return ""


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


_WRITEIN_TOTAL = re.compile(r"write[- ]?ins?(?: votes?| total)?", re.I)


def is_writein_total(row) -> bool:
    """An unnamed "Write-in" line: the canvass's total of every write-in vote, not one candidate. A named write-in
    candidate ("Michael Schalk (write-in)") is a candidate like any other."""
    return bool(_WRITEIN_TOTAL.fullmatch((row.get("candidate") or "").strip()))


def margin(c) -> dict | None:
    """Margin in points between the last candidate inside the seats and the next candidate, by votes.

    None = uncontested: no more candidates than seats. An unnamed "Write-in" total is not a candidate, so a race with
    one named candidate for one seat is uncontested whatever the write-in total; its votes still count in the total
    of votes cast. Otherwise a dict: {"reason"} when the margin can't be computed (seat count not in the data, a
    candidate's votes missing, no votes recorded), else the margin with its band. ``tie`` is True when the two
    candidates compared have the same votes (who is "inside" is then the ballot order, not a result)."""
    cands = candidates(c)
    named = [x for x in cands if not is_writein_total(x["row"])]
    n = int(c["vote_for"]) if (c.get("vote_for") or "").isdigit() else None
    if n is not None and len(named) <= n:
        return None  # uncontested
    if len(named) <= 1:
        return None  # one candidate (seat count not in the data): nobody ran against them
    if n is None:
        return {"reason": "seat count not in data"}
    if any(x["votes"] is None for x in named):
        return {"reason": "votes missing"}
    total = sum(x["votes"] for x in cands if x["votes"] is not None)
    if not total:
        return {"reason": "no votes recorded"}
    ranked = sorted(named, key=lambda x: -x["votes"])
    a, b = ranked[n - 1], ranked[n]
    pts = 100.0 * (a["votes"] - b["votes"]) / total
    band = next(bid for bid, _, lo, hi in BANDS if lo <= pts < hi)
    return {"pts": pts, "votes": a["votes"] - b["votes"], "ahead": a, "next": b, "band": band, "seats": n,
            "low": any(x["low"] for x in cands), "tie": a["votes"] == b["votes"], "total": total,
            "writein": len(named) < len(cands)}


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


def plain_badge(status: str, low: bool = False) -> Markup:
    """A status label as text, without the link and tooltip of status_badge (long lists and tables: hundreds of badge
    links would double a page). Each section that uses it links once to the definitions (badge_key)."""
    label = STATUS.get(status, ((status or "").upper() or "STATUS UNKNOWN",))[0]
    b = h("span", {"class": f"badge badge-{status or 'none'}"}, label)
    return h("span", None, b, " ", h("span", {"class": "badge badge-low"}, STATUS["low"][0])) if low else b


def badge_key(page, extra=None) -> Markup:
    return h("p", {"class": "muted badge-key"}, "Status labels (OFFICIAL, UNOFFICIAL, FROM SCAN, SECONDARY, LOW "
             "CONFIDENCE and the others) are defined in ", h("a", {"href": page.rel("about/index.html#badges")},
                                                              "About: status badges"), ".", extra)


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


def moved_anchors(page, moved: dict[str, str], prefixes: dict[str, str] | None = None) -> Markup:
    """The page's #moved-anchors map for static/js/moved.js: an old id that is no longer on this page -> where it lives
    now, given as a site-root path with the new #id ("elections/turnout/index.html#turnout-denominators"). The script
    reads the paths relative to this page, so they are written with page.rel.
    ``prefixes`` (added 2026-11-09, Wave D batch 6): {id prefix: site-root path}, for families of ids such as the
    "src-<source id>" citations, forwarded with the same id when the page no longer has them."""
    out = {"a": {k: page.rel(v) for k, v in sorted(moved.items())}}
    if prefixes:
        out["p"] = {k: page.rel(v) for k, v in sorted(prefixes.items())}
    return json_script("moved-anchors", out)


def _gaps(ed, area, extra_files=(), pattern=None):
    rows = ed.gaps(areas=[area]) if area else []
    if extra_files:
        rows += ed.gaps(files=list(extra_files), pattern=pattern)
    return rows


def _row_office_name(ed, c):
    o = ed.offices.get(c["office_id"]) if c.get("office_id") else None
    return o["title"] if o else c["label"]


# =========================================================================== 0. the elections hub
# Wave D batch 6 (review 3.4, P8): elections/index.html is the hub of the Elections topic. The explainer that used to be
# this page moved verbatim to elections/how-it-works/; every id it had is forwarded by static/js/moved.js (the hub's
# #moved-anchors map: the ids below, plus every src-<id> citation by prefix). tools/tests/test_wave_d_nav.py pins the
# list to the ids the page had before (tools/tests/fixtures/anchors_before_wave_d6.json).

HOW_IT_WORKS = "elections/how-it-works/index.html"
HOW_IT_WORKS_IDS = (
    "offices", "offices-h", "office-cycles", "office-cycles-copy",
    "primaries", "primaries-h", "primaries-low", "primaries-low-copy",
    "general", "general-h", "straight-party-rules", "straight-party-rules-copy",
    "voting", "voting-h", "county", "county-h", "election-contacts", "election-contacts-copy",
    "vacancies", "vacancies-h", "vacancies-low", "vacancies-low-copy", "caucus-incumbents", "caucus-incumbents-copy",
    "school-boards", "school-boards-h", "questions", "questions-h", "candidate-info", "candidate-info-h",
    "gaps", "gaps-h",
)

# The hub's cards, in the review's order (3.4): (page, one line about what is there)
HUB_CARDS = [
    ("elections/calendar/index.html", "What is on the ballot each year from 2026 to 2030, the deadlines, and every seat by year."),
    ("elections/results/index.html", "Every race by office and year, each marked official, unofficial or from scan."),
    ("elections/landscape/index.html", "Four measures for every race and every party, looking back: turnout, how close "
                                       "races were, the seats up next and how officeholders first took office."),
    ("elections/margins/index.html", "How many races had no contest, and how close the others were, by level of "
                                     "government and on a map."),
    ("elections/turnout/index.html", "Turnout in every election with its denominator, odd and even years, and "
                                     "straight-party ballots."),
    ("elections/judges-and-questions/index.html", "Judicial retention votes and the public questions on the county's "
                                                  "ballots, with their wording and results."),
    (HOW_IT_WORKS, "Offices and cycles, primaries and getting on the ballot, how to vote and ID, vacancies and "
                   "caucuses, school-board labels."),
    ("run/index.html", "Eligibility, filing, petitions, caucuses and campaign-finance duties, with a page for each of "
                       "six local offices."),
]


def _hub_next(page, ed):
    """(year, line) for the next election in the county: the earliest next_election year of any office (civic/layers.py
    rules), with the dates computed from the state calendar rule."""
    from civic.layers import build_layers, election_dates
    layers = [L for L in build_layers(ed)["layers"].values() if not L.placeholder]
    years = sorted({y for L in layers for y in L.next})
    if not years:
        return None, None
    y = years[0]
    d = election_dates(ed, [y])[y]
    govs = [L.title for L in layers if y in L.next]
    offs = [o for L in layers if y in L.next for o in L.offices if o.get("next_election") == y]
    rp, rg = ed.rules.get("primary_date", {}), ed.rules.get("general_election_date", {})
    line = h("p", {"class": "ehub-next-body"},
             h("strong", {"class": "fig"}, y), " ",
             f"Primary {fmt_date(d['primary'])} · General {fmt_date(d['general'])}",
             page.cites.cite(_src(rp, rg)), " ",
             status_badge("computed", page, "Dates computed from the state calendar rule (first Tuesday after the first "
                                            "Monday)."))
    who = h("p", {"class": "ehub-next-who"}, "Governments with seats on that ballot: ", ", ".join(govs), ".",
            page.cites.cite_compact(_src(*offs)) if offs else None)
    return y, [line, who]


def build_hub(site):
    from pages.elections_numbers import _contested, _counts, margin_races   # elections_numbers imports this module
    ed = site.ed
    page = site.page("elections/index.html", banners=True)
    cites = page.cites
    els = _elections(ed)
    span = f"{els[0]['date'][:4]} to {els[-1]['date'][:4]}"
    computed = lambda why: status_badge("computed", page, why)

    # one live fact per card, each with its source
    facts: dict[str, Markup] = {}
    ny, next_lines = _hub_next(page, ed)
    if ny:
        facts["elections/calendar/index.html"] = h("span", None, f"Next election: {ny}. ", "The seats are listed by year.")
    latest = els[-1]
    in_explorer = [c for c in ed.contests.values() if c["election_id"] in {e["election_id"] for e in els}]
    facts["elections/results/index.html"] = h(
        "span", None, f"{len(in_explorer):,} contests, {span}. Latest: {_election_name(latest)}",
        cites.cite(latest.get("source_ids")), " ", status_badge(latest["status"], page))
    races = margin_races(ed)
    cnt = _counts(races)
    facts["elections/margins/index.html"] = h(
        "span", None, f"{cnt['unc']:,} of {len(races):,} local races had no contest; {_contested(cnt):,} were contested, "
                      f"{cnt['under-5']:,} of them by under 5 points. ",
        computed("Counted from results.csv vote counts and seat counts."),
        cites.cite_compact(_src(*[r["c"]["rows"][0] for r in races])))
    gen = [e for e in els if e["type"] == "general" and e.get("turnout_pct") and e["status"] == "official"]
    if gen:
        g = gen[-1]
        facts["elections/turnout/index.html"] = h(
            "span", None, f"{_election_name(g)}: ", h("strong", {"class": "fig"}, f"{float(g['turnout_pct']):.1f}%"),
            " of registered voters cast a ballot", cites.cite(g.get("source_ids")), " ", status_badge(g["status"], page))
    qs = [c for c in in_explorer if classify(c)[0] == "Public questions"]
    ret = [c for c in in_explorer if classify(c)[0] in ("Superior Court retention", "State court retention")]
    if qs or ret:
        facts["elections/judges-and-questions/index.html"] = h(
            "span", None, f"{len(qs)} public questions and {len(ret)} retention votes on the county's ballots, {span}. ",
            computed("Counted from results.csv."), cites.cite_compact(_src(*[c["rows"][0] for c in qs + ret])))
    run_pages = [e for e in site.entries if e.path.startswith("run/") and e.path != "run/index.html"]
    facts["run/index.html"] = h("span", None, f"Office pages: {', '.join(e.nav.lower() for e in run_pages)}.")

    page.add(_hero(page, "Elections",
                   "Start here for elections in the county. The calendar says what is on each ballot; the results and "
                   "the numbers look back at every race since 2010; how elections work and run for office explain the "
                   "rules. Every page is sourced, and the results say which counts are official.",
                   ["county", "indiana"], [("next", "Next election"), ("pages", "Election pages"),
                                           ("sources", "Sources")]))
    if next_lines:
        page.add(h("section", {"class": "next-strip ehub-next", "id": "next", "aria-labelledby": "next-h"},
                   h("h2", {"id": "next-h", "class": "next-h mono"}, "Next election in the county"),
                   next_lines,
                   h("p", {"class": "next-link"},
                     h("a", {"href": page.rel("elections/calendar/index.html#next")}, "What's on your next ballot"))))
    cards = []
    for path, what in HUB_CARDS:
        e = site.by_path[path]
        cards.append(h("article", {"class": "card ehub-card", "id": "card-" + path.split("/")[-2]},
                       h("h3", {"class": "card-title"}, h("a", {"href": page.rel(path)}, e.nav)),
                       h("p", None, what),
                       h("p", {"class": "ehub-fact"}, facts[path]) if path in facts else None))
    page.add(section("pages", None, "Election pages", h("div", {"class": "card-grid ehub-grid elx-hub-grid"}, cards),
                     h("p", None, "Learning path: ",
                       h("a", {"href": page.rel(PATHS_FIRST["vote-smarter"])}, "Vote smarter"), ". ",
                       "Another path, ", h("a", {"href": page.rel(PATHS_FIRST["elections-by-the-numbers"])},
                                           "Elections by the numbers"), ", goes through the measures one at a time.")))
    page.add(moved_anchors(page, {i: f"{HOW_IT_WORKS}#{i}" for i in HOW_IT_WORKS_IDS}, prefixes={"src-": HOW_IT_WORKS}))
    page.finish()
    return page


def _paths_first() -> dict:
    from civic.sitemap import PATHS
    return {p["id"]: f"{p['stops'][0]['page']}#path-{p['id']}-1" for p in PATHS}


PATHS_FIRST = _paths_first()


# =========================================================================== 1. how elections work

def build_how_it_works(site):
    """The explainer (moved verbatim from elections/index.html in Wave D batch 6; same section ids)."""
    ed = site.ed
    page = site.page(HOW_IT_WORKS, banners=False)
    cites = page.cites
    R = ed.rules
    toc = [("offices", "Which offices, which years"), ("primaries", "Primaries and the ballot"),
           ("general", "The general election and straight-ticket voting"), ("voting", "How to vote"),
           ("county", "Voting in the county"), ("vacancies", "Vacancies and caucuses"),
           ("school-boards", "School-board party labels"), ("questions", "No citizen initiative"),
           ("candidate-info", "Where to find candidate information"), ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(_hero(page, "Elections",
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
                       h("a", {"href": page.rel("elections/turnout/index.html#straight-party")}, "Turnout and how ballots were cast"), ")."),
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
                       " ", h("a", {"href": page.rel("officeholders/index.html#every")}, "How every incumbent took office")),
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
                       h("ul", {"class": "elx-lvls"}, lines) if lines else None,
                       h("p", {"class": "elx-yr-note"}, h("a", {"href": f"#year-{y}"}, f"Every seat in {y}")) if items[y] else None))
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
                     h("div", {"class": "card-grid elx-next-grid"}, blocks),
                     h("p", {"data-here-uninc": True}, f"If you live outside every city and town, your next regular election in the guide's data is "
                                  f"the primary on {fmt_date(p28, long=True)}, then the general on {fmt_date(g28, long=True)}. "
                                  f"Everyone in the county votes then, including on {len(county_28)} county offices.",
                       " ", status_badge("computed", page, "Dates from the statutory rule."), cites.cite(src28)),
                     h("p", {"class": "muted"}, "Which district seats you vote for depends on your address. ",
                       h("a", {"href": page.rel("your-governments/index.html")}, "Your place")),
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
    trows, tattrs = [], []
    for y in YEARS:
        for it in items[y]:
            o = it["office"]
            gov = ed.units.get(o["unit_id"], {}).get("name", "") if o else "Indiana"
            tattrs.append({"data-tf-year": str(y), "data-tf-level": LEVEL_LABEL.get(it["level"], it["level"]),
                           "data-tf-government": gov, "data-tf-text": it["label"]})
            trows.append([str(y), LEVEL_LABEL.get(it["level"], it["level"]),
                          ed.units.get(o["unit_id"], {}).get("name", "") if o else "Indiana",
                          it["label"], str(it["seats"]) if it["seats"] else "not in data",
                          f"{o['term_years']} years" if o and o.get("term_years") else "",
                          h("span", None, plain_badge(it["status"]), cites.cite_compact(it["src"]))])
    check = _check_2026(ed, items)
    def why(o):
        parts = re.split(r"(?<=[.;])\s+", o.get("notes", ""))
        keep = [x for x in parts if re.search(r"cycle|next election|not printed|depends|seat count|No terms|appear", x, re.I)]
        return " ".join(keep or parts[:1]) or "Not stated in the office notes."
    unsched_rows = [[o["title"], ed.units.get(o["unit_id"], {}).get("name", ""), why(o),
                     cites.cite_compact(o["source_ids"])] for o in unscheduled]
    t_levels = [lab for _, lab in LEVELS if any(a["data-tf-level"] == lab for a in tattrs)]
    t_govs = {}
    for a, it in zip(tattrs, [it for y in YEARS for it in items[y]]):
        o = it["office"]
        t_govs[a["data-tf-government"]] = _place_order(ed, o) if o else (99, "")
    controls = lambda: [{"key": "year", "label": "Year", "all": "All years", "options": _opts([str(y) for y in YEARS])},
                        {"key": "level", "label": "Level", "all": "All levels", "options": _opts(t_levels)},
                        {"key": "government", "label": "Government", "all": "All governments",
                         "options": _opts(sorted(t_govs, key=lambda g: (t_govs[g], g)))}]
    years_list, n_seat_rows = _year_lists(page, ed, items, tattrs)
    urows, uattrs, uoffices = _up_next_rows(page, ed, items)
    page.add(section("by-year", 4, "Every seat, by year",
                     h("p", None, "Each year lists its seats by government. Open a government to see its seats. For the next "
                                  "two regular ballots, 2027 and 2028, each seat also shows the person holding it now, how "
                                  "they first took the office, and the term-limit rule for the office (see How this is "
                                  "computed). Announced retirements and declared candidates are not collected."),
                     h("nav", {"class": "cal-jump", "aria-label": "Jump to a year"},
                       h("ul", None, [h("li", None, h("a", {"href": f"#year-{y}"}, str(y))) for y in YEARS])),
                     badge_key(page),
                     table_filter("cal-years", controls(), n_seat_rows, noun="seat",
                                  search="Words in the office or a holder's name", label="Filter the seats in every year"),
                     here_slot("filter", "cal-years", extra={"data-here-noun": "seats"}),
                     filter_empty_note("cal-years"),
                     years_list,
                     see_all_table("up-next-table", ["Year", "Seat", "Holder now", "Party", "In office since",
                                                     "First took office by", "Term-limit status", "Status"], urows,
                                   noun="seat", caption="Seats on the 2027 and 2028 ballots", min_width="60rem",
                                   row_attrs=uattrs,
                                   controls=[{"key": "year", "label": "Year", "all": "Both years",
                                              "options": [("2027", "2027"), ("2028", "2028")]}] + _unit_controls(ed, uoffices),
                                   search="Seat or holder name", filter_label="Filter the up-next table",
                                   summary=f"Up next: the {len(urows)} seats on the 2027 and 2028 ballots, with who holds them, as a table"),
                     see_all_table("calendar-table", ["Year", "Level", "Government", "Office", "Seats", "Term", "Status"], trows,
                                   noun="seat", caption="Offices on the ballot, 2026 to 2030 (computed)", numeric=(0, 4),
                                   min_width="46rem", row_attrs=tattrs, controls=controls(),
                                   search="Words in the office name", filter_label="Filter the every-seat table",
                                   summary=f"Every year: all {len(trows)} seats, 2026 to 2030, as a table"),
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
                     h("p", None, check, " ", status_badge("computed", page)),
                     h("h3", {"id": "term-limits"}, "Holders and term limits for 2027 and 2028"),
                     h("p", None, "The holder shown for a seat is the person holding it on the guide's as-of date, "
                                  f"{fmt_date(ed.as_of, long=True)}, from the terms data."),
                     _rule_p(page, ed, "county_row_office_term_limits", detail=True),
                     h("p", {"class": "muted"}, "Term-limit status is computed only for the six offices on the 8-in-12 list, "
                                                "from the guide's terms data; service chosen by caucus to fill a vacancy is not "
                                                "counted, as the rule says. Listed by year and office, never by party.")))
    page.finish(gaps=_gaps(ed, "elections-calendar")
                + [g for g in _gaps(ed, "elections-landscape") if re.search(r"retirement|declared", g.get("item", ""), re.I)])
    return page


def _seat_holder_rows(page, ed, o, y) -> list[dict]:
    """The holders of office ``o`` now, with the term-limit status for the seat's election in year ``y``
    (the former Up next table on elections/landscape/). [] when the guide's data has no current holder."""
    out = []
    for t in _holders_now(ed, o["office_id"]):
        tl = _term_limit(ed, o, t, y)
        out.append({"t": t, "limit": tl[0], "limit_note": tl[1]})
    return out


def _holder_badges(page, t):
    return h("span", None, plain_badge(t["status"], t.get("confidence") == "low"), page.cites.cite_compact(t["source_ids"]))


def first_by_text(t) -> str:
    k = t.get("first_selected_by") or ""
    if k in ("election", "caucus", "appointment"):
        return f"first took office by {SELECTED_BY_LABELS[k]}"
    return "how they first took office is not stated in sources"


def _up_next_rows(page, ed, items):
    """Rows of the up-next table (moved from elections/landscape/ #up-next-table, every column kept)."""
    cites = page.cites
    urows, uattrs, uoffices = [], [], []
    for y in UP_NEXT_YEARS:
        for it in items[y]:
            o = it["office"]
            if not o:
                continue
            holders = _seat_holder_rows(page, ed, o, y)
            ot = ed.office_type_row(o) or {}
            if not holders:
                urows.append([str(y), o["title"], "No current officeholder in the guide's data", "", "", "",
                              ot.get("term_limit") or "Not in the guide's data", h("span", None, cites.cite(o["source_ids"]))])
                uattrs.append({**_unit_attrs(ed, o), "data-tf-year": str(y), "data-tf-text": o["title"]})
                uoffices.append(o)
                continue
            for x in holders:
                t = x["t"]
                uattrs.append({**_unit_attrs(ed, o), "data-tf-year": str(y), "data-tf-text": f"{o['title']} {t['person']}"})
                uoffices.append(o)
                urows.append([str(y), o["title"], t["person"], _plabel(t.get("party")), fmt_date(t["start"]) or "not in sources",
                              SELECTED_BY_LABELS.get(t.get("first_selected_by", ""), t.get("first_selected_by")),
                              h("span", None, x["limit"], " ",
                                status_badge("computed", None, x["limit_note"]) if x["limit_note"] else None),
                              _holder_badges(page, t)])
    return urows, uattrs, uoffices


def _year_lists(page, ed, items, tattrs):
    """§4 of the calendar: one section per year (#year-<y>), seats grouped by government in folds that ship open
    (static/js/folds.js closes them), each seat one row; 2027 and 2028 rows add the holder now. The filter bar
    (table_filter "cal-years", tablefilter.js deep mode) filters the seat rows across every year and government."""
    cites = page.cites
    attrs_by = iter(tattrs)
    secs, n_rows = [], 0
    for y in YEARS:
        p, g, how, src = _dates(ed, y)
        groups: dict[str, dict] = {}
        known = 0
        for it in items[y]:
            a = next(attrs_by)
            o = it["office"]
            gov = a["data-tf-government"]
            grp = groups.setdefault(gov, {"order": _place_order(ed, o) if o else (99, ""), "rows": [], "seats": 0})
            seats = it["seats"]
            if o:
                known += seats or 0   # local seats; the statewide and federal lines are listed under Indiana
            grp["seats"] += seats or 0
            meta = [f"{seats} seats" if seats and seats > 1 else ("1 seat" if seats else "seat count not in data")]
            if o and o.get("term_years"):
                meta.append(f"{o['term_years']}-year term")
            holder_ul, words = None, [it["label"]]
            if o and y in UP_NEXT_YEARS:
                hs = _seat_holder_rows(page, ed, o, y)
                lis = []
                for x in hs:
                    t = x["t"]
                    words.append(t["person"])
                    lis.append(h("li", None, h("span", {"class": "cal-now"}, "Now: "), t["person"],
                                 f" · {_plabel(t.get('party'))}",
                                 f" · since {fmt_date(t['start'])}" if t.get("start") else " · start not in sources",
                                 f" · {first_by_text(t)}",
                                 h("span", {"class": "cal-limit"}, " · Term limit: ", x["limit"], " ",
                                   status_badge("computed", None, x["limit_note"]) if x["limit_note"] else None),
                                 " ", _holder_badges(page, t)))
                if not hs:
                    lis.append(h("li", {"class": "muted"}, "No current officeholder in the guide's data."))
                holder_ul = h("ul", {"class": "cal-holders"}, lis)
            row_attrs = {k: v for k, v in a.items() if k != "data-tf-text"}
            row_attrs.update({"class": "cal-seat", "data-tf-row": True, "data-tf-text": " ".join(words),
                              # saved-place preselect (static/js/preselect.js): statewide and federal lines are "state"
                              "data-here-layer": here_layer(ed, o["unit_id"]) if o else "state"})
            grp["rows"].append(h("li", row_attrs,
                                 h("p", {"class": "cal-seat-h"}, h("span", {"class": "cal-office"}, it["label"]),
                                   h("span", {"class": "cal-meta"}, " · " + " · ".join(meta)), " ",
                                   plain_badge(it["status"]), cites.cite_compact(it["src"])),
                                 holder_ul))
            n_rows += 1
        folds = []
        for gov in sorted(groups, key=lambda k: (groups[k]["order"], k)):
            grp = groups[gov]
            n = len(grp["rows"])
            digest = f"{grp['seats']} seat{'s' if grp['seats'] != 1 else ''}" if grp["seats"] else f"{n} office{'s' if n != 1 else ''}"
            folds.append(h("details", {"class": "fold-details cal-gov", "data-fold": "cal", "data-tf-group": True, "open": True},
                           h("summary", {"class": "fold-summary cal-gov-sum"},
                             h("h4", {"class": "cal-gov-h"}, gov), h("span", {"class": "cal-gov-n"}, digest),
                             h("span", {"class": "fold-toggle", "aria-hidden": "true"})),
                           h("ul", {"class": "cal-seats"}, grp["rows"])))
        when = []
        if p:
            pre = "Municipal primary" if y % 2 else "Primary"
            when = [f"{pre} {fmt_date(p)}", f"General {fmt_date(g)}"]
        head = " · ".join([str(y)] + when + [f"{known} local seats" if known else "no local seats in the guide's data"])
        note = None
        if y == 2026:
            note = h("p", {"class": "muted"}, "Held on Nov 3, 2026. Results are unofficial until certified. ",
                     h("a", {"href": page.rel("elections/results/index.html")}, "Results"))
        elif y % 2:
            note = h("p", {"class": "muted"}, "City and town offices only." if items[y] else
                     "No regular election for any office in the guide's data.")
        # kept on the page while filtered (a #year-<y> link target): its note says why it is empty; the saved-place
        # preselect (static/js/preselect.js) swaps in data-here-empty and a Show all button (Wave E batch 8 part 2)
        why = " (that ballot has city and town offices only)" if y % 2 and items[y] else ""
        empty = h("p", {"class": "cal-year-empty muted", "data-tf-group-empty": True, "hidden": True,
                        "data-here-empty": f"{y}: no seats for your saved place's governments{why}."},
                  f"{y}: no seats match the filters.")
        secs.append(h("section", {"class": "cal-year", "id": f"year-{y}", "aria-labelledby": f"year-{y}-h",
                                  "data-tf-group": True, "data-tf-keep": True},
                      h("h3", {"class": "cal-year-h", "id": f"year-{y}-h"}, head),
                      note, empty, folds or h("p", {"class": "muted"}, "No seats.")))
    return h("div", {"class": "cal-years", "id": "cal-years", "data-tf-deep": True}, secs), n_rows


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
    q = is_question(c)
    return {"id": c["contest_id"], "e": c["election_id"], "l": c["label"], "g": group, "p": place,
            "o": c["office_id"], "vf": c["vote_for"], "pp": c["party_primary"], "s": st, "x": 1 if cross else 0,
            "q": 1 if q else 0, "u": 1 if not q and margin(c) is None else 0, "f": flags, "n": notes,
            "c": [[x["name"], x["party"], x["votes"], round(x["pct"], 2) if x["pct"] is not None else None,
                   x["winner"], 1 if x["low"] else 0] for x in cands],
            "src": _src(*c["rows"])}


def _every_contest_table(page, ed, payload_c):
    """Every explorer contest as one table in a closed "See all" fold (components.see_all_table), each row's first cell
    carrying id="contest-<id>" (civic/related.py contest_anchor). Links from other pages land here: with JavaScript
    static/js/elections.js shows that one contest in the explorer instead; without it this row is the result."""
    els = {e["election_id"]: e for e in _elections(ed)}
    places = sorted({x["p"] for x in payload_c})
    p_ix = {p: str(i) for i, p in enumerate(places)}
    rows, attrs = [], []
    for x in payload_c:
        e = els[x["e"]]
        c = ed.contests[x["id"]]
        bits = []
        for k in candidates(c):
            party = "" if x["q"] else f" ({k['party'] or 'no party listed'})"
            val = "votes not recorded" if k["pct"] is None else (
                f"{k['votes']:,} · {k['pct']:.1f}%" if k["votes"] is not None else f"{k['pct']:.1f}%")
            # "(unofficial)" is not repeated after "Elected": the Status cell of the same row says UNOFFICIAL
            won = (" · " + ("Majority" if x["q"] else "Elected")) if k["winner"] == "Y" and not x["x"] else ""
            bits.append(f"{k['name']}{party} {val}{won}")
        # size (2026-11-09, Wave B batch 2): the short election name ("Nov 3, 2026 general") and the place filter by
        # index keep 1,225 rows smaller; the full election name is in the explorer and on the Data pages
        rows.append([h("span", {"id": contest_anchor(x["id"])}, x["l"]), _election_short(e), x["g"], x["p"],
                     "; ".join(bits) + (" (county portion only)" if x["x"] else ""),
                     STATUS.get(x["s"], (x["s"].upper(),))[0]])   # plain label: 1,200 badge tooltips would double the table
        attrs.append({"data-tf-year": e["date"][:4], "data-tf-group": str(GROUP_ORDER.get(x["g"], len(GROUPS))),
                      "data-tf-place": p_ix[x["p"]]})
    years = sorted({a["data-tf-year"] for a in attrs}, reverse=True)
    groups = [(str(i), g) for i, g in enumerate(GROUPS + ["Other"]) if any(a["data-tf-group"] == str(i) for a in attrs)]
    return see_all_table(
        "every-contest", ["Contest", "Election", "Office group", "Place", "Candidates in ballot order: votes, share", "Status"],
        rows, noun="contest", caption="Every contest in the explorer", min_width="60rem", row_attrs=attrs,
        controls=[{"key": "year", "label": "Year", "all": "All years", "options": [(y, y) for y in years]},
                  {"key": "group", "label": "Office group", "all": "All offices", "options": groups},
                  {"key": "place", "label": "Place", "all": "All places", "options": [(p_ix[p], p) for p in places]}],
        search="Words in the contest or a name", filter_label="Filter every contest",
        intro=h("p", None, "The same contests as the explorer, as one table, by year and election, then office group; "
                           "candidates in ballot order. Status labels are defined under How to read the results. Links from other pages to one contest land "
                           "on its row here when JavaScript is off."))


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

    # ---- turnout: one chart and a link; every election's turnout with its denominator is on elections/turnout/
    # (the table that was here, #turnout-table, moved there as #turnout-denominators; static/js/moved.js forwards it)
    g_chart = _turnout_chart(page, ed, ("general", "municipal_general"), "turnout-general",
                             "Turnout in general elections", cites.cite_compact(_src(*[e for e in els if "general" in e["type"]])))
    page.add(section("turnout", 1, "Turnout first",
                     h("p", None, "How many registered voters cast a ballot in each election. Municipal elections count only "
                                  "voters in the cities and towns that held them, so their turnout is not on the same base as "
                                  "countywide elections."),
                     g_chart,
                     h("p", None, h("a", {"href": page.rel("elections/turnout/index.html#turnout-denominators-all")},
                                    "Every election's turnout with its denominator, and primaries and special elections"),
                       ", on ", h("a", {"href": page.rel("elections/turnout/index.html")}, "Turnout and how ballots were cast"), "."),
                     moved_anchors(page, {"turnout-table": "elections/turnout/index.html#turnout-denominators",
                                          "turnout-table-copy": "elections/turnout/index.html#turnout-denominators-copy"}),
                     scope="county", ed=ed))

    # ---- explorer
    payload_c = [_contest_payload(ed, c) for c in contests]
    # contests on the map's "How areas voted" layer get a link that opens the map on that race (map/index.html#race-<id>)
    shapes = load_shapes(ed)
    on_map = race_by_contest(ed, load_votes(ed)) if shapes and "precinct" in shapes.get("layers", {}) else {}
    for x in payload_c:
        if x["id"] in on_map:
            x["m"] = on_map[x["id"]]
    payload_c.sort(key=lambda x: (x["e"], GROUP_ORDER.get(x["g"], 99), x["p"], x["l"]))
    every = _every_contest_table(page, ed, payload_c)   # #contest-<id> rows (P10 deep links; the no-JavaScript view)
    src_ids = sorted({s for x in payload_c for s in split_ids(x["src"])})
    num = {sid: i for i, sid in enumerate(src_ids)}
    # compact: repeated strings (notes, groups, places) become indexes into lookup lists
    notes = sorted({x["n"] for x in payload_c if x["n"]})
    places = sorted({x["p"] for x in payload_c})
    # saved-place preselect (static/js/elections.js): the layer of each place, "" when its contests mix layers
    p_layers: dict[str, set] = {}
    for x in payload_c:
        p_layers.setdefault(x["p"], set()).add(contest_layer(ed, ed.contests[x["id"]]))
    place_layers = [next(iter(p_layers[p])) if len(p_layers[p]) == 1 else "" for p in places]
    n_ix, p_ix = {n: i for i, n in enumerate(notes)}, {p: i for i, p in enumerate(places)}
    for x in payload_c:
        x["src"] = [num[s] for s in split_ids(x["src"])]
        x["g"] = GROUP_ORDER.get(x["g"], len(GROUPS))
        x["p"] = p_ix[x["p"]]
        del x["o"]
        # the contest id is "<election id>-<rest>": only the rest ("i") is shipped, elections.js rebuilds the id
        # (static/js/elections.js opens the explorer on #contest-<id>)
        cid = x.pop("id")
        x["i"] = cid[len(x["e"]) + 1:] if cid.startswith(x["e"] + "-") else cid
        if x["i"] == cid:
            x["fi"] = 1   # full id shipped (does not start with its election id)
        # the most common values are left out; elections.js fills them in ("official", vote for 1)
        if x["s"] == "official":
            del x["s"]
        if x["vf"] == "1":
            del x["vf"]
        if x["n"]:
            x["n"] = n_ix[x["n"]]
        else:
            del x["n"]
        if not x["f"]:
            del x["f"]
        for k in ("pp", "x", "q", "u"):
            if not x[k]:
                del x[k]
    # register every source so the per-page list carries them; the explorer links to these anchors
    cites.cite_compact(src_ids)
    payload = {
        "elections": [{"id": e["election_id"], "name": _election_name(e), "y": e["date"][:4], "t": e["type"],
                       "s": e["status"], "reg": e["registered"], "bal": e["ballots_cast"], "to": e["turnout_pct"]}
                      for e in els],
        "groups": GROUPS + ["Other"], "places": places, "pl": place_layers, "notes": notes, "contests": payload_c, "parties": PARTY_LABELS,
        "src": [{"id": s, "t": (ed.source(s) or {}).get("title", s)} for s in src_ids],
        "links": {"legislature": page.rel("state/your-legislators/index.html"), "state": page.rel("state/index.html"),
                  "about": page.rel("about/index.html#badges"),
                  "map": page.rel("map/index.html") if on_map else ""},
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
                     here_slot("explorer", "elx-place"),
                     h("div", {"id": "elx-results", "class": "elx-results", "data-root": page.rel("index.html")},
                       h("noscript", None, h("p", None, "The explorer needs JavaScript. Every contest is also in the table "
                                                        "below. The county canvass files it is built from are "
                                                        "listed under Sources below, and the guide's tables are on ",
                                                        h("a", {"href": page.rel("data/index.html")}, "Data and sources"), "."))),
                     h("p", {"class": "elx-more-wrap"}, h("button", {"type": "button", "class": "btn", "id": "elx-more", "hidden": True},
                                                          "Show more contests")),
                     json_script("elx-data", payload),
                     every,
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

def _retention_row(page, ed, c, y, n, who):
    """One retention vote as table cells: year, who, yes, no, yes share, status, link to the full result."""
    tot = y["votes"] + n["votes"]
    share = 100.0 * y["votes"] / tot
    st = contest_status(c["rows"])
    low = y["low"] or n["low"]
    href = contest_href(page, c["contest_id"])
    return share, low, st, [ed.elections[c["election_id"]]["date"][:4], who, fmt_int(y["votes"]), fmt_int(n["votes"]),
                            f"{share:.1f}%",
                            h("span", None, status_badge(st, page), (" ", status_badge("low", page)) if low else None,
                              page.cites.cite(_src(*c["rows"]))),
                            h("a", {"href": href}, "Full result") if href else h("span", {"class": "muted"}, "Not in explorer")]


# short titles for questions whose label does not say what was asked; each comes from the wording quoted on the page
QUESTION_TITLES = {
    "2026g-county-public-question-1": "Bail for offenses other than murder or treason",
    "2026g-county-public-question-2": "Where a city or town court judge may live",
    "2024g-county-public-question-1": "State superintendent and the governor's line of succession",
}
_Q_PLACE = re.compile(r"^(?:Mishawaka|New Prairie schools|South Bend Community Schools|School City of Mishawaka): ")
_Q_NUM = re.compile(r"^Public [Qq]uestion #\d+: ")
_Q_NOTE = re.compile(r"\s*[(](?:wording|text|header) [^)]*[)]\s*$")


def _question_title(c):
    if c["contest_id"] in QUESTION_TITLES:
        return QUESTION_TITLES[c["contest_id"]]
    t = _Q_NOTE.sub("", _Q_NUM.sub("", _Q_PLACE.sub("", c["label"]))).strip()
    return t[:1].upper() + t[1:]


def _question_outcome(cands, cross, unoff):
    """Outcome in words from the printed result: a local question passed or failed; a statewide one shows how the county voted."""
    y = next((x for x in cands if x["name"].upper() == "YES"), None)
    n = next((x for x in cands if x["name"].upper() == "NO"), None)
    if not (y and n and y["votes"] is not None and n["votes"] is not None):
        return "Result not in the data"
    if y["votes"] == n["votes"]:
        return "Tied in the county"
    lead = "yes" if y["votes"] > n["votes"] else "no"
    if cross:
        return f"County voted {lead}" + (" (unofficial)" if unoff else "")
    if unoff:
        return f"Unofficial: {lead} ahead"
    return "Passed" if lead == "yes" else "Failed"


def build_judges(site):
    ed = site.ed
    page = site.page("elections/judges-and-questions/index.html", banners=True)
    cites = page.cites
    toc = [("how", "How retention and questions work"), ("retention", "Judicial retention votes"),
           ("state-retention", "State court retention"), ("questions", "Public questions"),
           ("school-labels", "School-board party labels"), ("gaps", "Gaps"), ("sources", "Sources")]
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
    page.add(section("how", 1, "How retention and questions work",
                     h("h3", None, "How Superior Court judges are chosen and kept"), supv,
                     h("h3", None, "How questions get on the ballot"),
                     _rule_p(page, ed, "no_citizen_initiative", detail=True),
                     _rule_p(page, ed, "school_and_local_referendums", detail=True),
                     h("p", {"class": "muted"}, "The petition and threshold rules for local questions were not collected "
                                                "(see Gaps). A judge's retention vote and a public question are both a plain "
                                                "yes or no, and neither has a party."),
                     scope="indiana", ed=ed))

    sup = [c for c in ed.contests.values() if classify(c)[0] == "Superior Court retention"]
    sup.sort(key=lambda c: (ed.elections[c["election_id"]]["date"], c["label"]))
    bar_rows, trows = [], []
    for c in sup:
        cands = {x["name"].upper(): x for x in candidates(c)}
        y, n = cands.get("YES"), cands.get("NO")
        # no yes or no votes recorded (blank, or 0 and 0): no share to compute (a 0-0 row divided by zero and turned
        # the whole page into a stub; debug pass 2026-11-09)
        if not (y and n and y["votes"] is not None and n["votes"] is not None and y["votes"] + n["votes"] > 0):
            continue
        yr = ed.elections[c["election_id"]]["date"][:4]
        who = c["label"].replace("Superior Court retention", "").strip(" :") or "judge not named"
        who = re.sub(r"^\(|\)$", "", who)
        if "names not captured" in who:
            who = "judge names not captured"
        share, low, st, row = _retention_row(page, ed, c, y, n, who)
        if not low:
            bar_rows.append({"label": f"{yr} · {who[:34]}", "value": share, "display": f"{share:.1f}% yes",
                             "tip": f"{yr} {who}: {y['votes']:,} yes, {n['votes']:,} no ({st})"})
        trows.append(row)
    fig = hbar("retention-yes", "Yes share in Superior Court retention votes", bar_rows,
               subtitle=f"Every retention vote in the guide's data, {trows[0][0]} to {trows[-1][0]}" if trows else None,
               note="Yes votes as a share of yes plus no votes. 2012 figures are labelled unofficial in the source; the 2012 "
                    "Manier line is from a scan. Low-confidence lines are left out of the chart and kept in the table.",
               page=page, headers=["Vote", "Yes share"], status="computed") if bar_rows else None
    page.add(section("retention", 2, "Judicial retention votes",
                     h("p", None, f"{len(trows)} Superior Court retention votes appear on the county's ballots in the guide's "
                                  f"data. In every one, a majority voted yes.", " ",
                       status_badge("computed", page, "Counted from results.csv.")) if trows and all(float(r[4][:-1]) > 50 for r in trows) else None,
                     fig,
                     see_all_table("retention-table", ["Year", "Judge", "Yes", "No", "Yes share", "Status", "Result"], trows,
                                   noun="vote", caption="Superior Court retention votes", numeric=(2, 3, 4), min_width="40rem",
                                   summary=f"See all {len(trows)} retention votes"),
                     scope="county", ed=ed))

    # ---- state retention
    stc = [c for c in ed.contests.values() if classify(c)[0] == "State court retention"]
    stc.sort(key=lambda c: (ed.elections[c["election_id"]]["date"], c["label"]))
    srows = []
    for c in stc:
        cands = {x["name"].upper(): x for x in candidates(c)}
        y, n = cands.get("YES"), cands.get("NO")
        share = (100.0 * y["votes"] / (y["votes"] + n["votes"])) if y and n and y["votes"] and n["votes"] is not None else None
        href = contest_href(page, c["contest_id"])
        srows.append([ed.elections[c["election_id"]]["date"][:4], c["label"].replace("Retention: ", ""),
                      fmt_int(y["votes"]) if y else "", fmt_int(n["votes"]) if n else "",
                      f"{share:.1f}%" if share is not None else "",
                      h("span", None, status_badge(contest_status(c["rows"]), page), cites.cite(_src(*c["rows"]))),
                      h("a", {"href": href}, "Full result") if href else h("span", {"class": "muted"}, "Not in explorer")])
    rl = ed.rules.get("retain_justice_labels", {})
    page.add(section("state-retention", 3, "Retention votes for state courts (county portion only)",
                     h("p", None, rl.get("plain_language", ""), " ", rl.get("detail", ""), cites.cite(rl.get("source_ids")), " ",
                       status_badge(rl.get("status", ""), page)),
                     h("p", None, "These votes are decided statewide or across an appellate district, so the county tally below "
                                  "does not show who was retained. Names and courts are as printed on the canvass. ",
                       h("a", {"href": page.rel("state/index.html")}, "State government")),
                     see_all_table("state-retention-table",
                                   ["Year", "Ballot line", "Yes", "No", "Yes share (county)", "Status", "Result"],
                                   srows, noun="vote", caption="State court retention, St. Joseph County tally",
                                   numeric=(2, 3, 4), min_width="44rem",
                                   summary=f"See all {len(srows)} state court retention votes"),
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
    groups: dict[str, list] = {}
    for c in qs:
        groups.setdefault(classify(c)[1], []).append(c)
    blocks = []
    for gi, jur in enumerate(sorted(groups, key=lambda g: (g != "Statewide", g.lower()))):
        items = []
        for c in groups[jur]:
            e = ed.elections[c["election_id"]]
            cross = classify(c)[2]
            w = wording.get(c["contest_id"])
            st = contest_status(c["rows"])
            unoff = st == "unofficial"
            cands = candidates(c)
            yes = next((x for x in cands if x["name"].upper() == "YES"), None)
            no = next((x for x in cands if x["name"].upper() == "NO"), None)
            key_num = (f"Yes {yes['pct']:.1f}% · No {no['pct']:.1f}%" if yes and no and yes["pct"] is not None
                       and no["pct"] is not None else None)
            if w:
                words = h("blockquote", {"class": "elx-wording"}, h("p", None, w[0]),
                          h("footer", None, status_badge(w[3], page), " ", w[2], cites.cite(w[1])))
            else:
                words = h("p", {"class": "elx-gapline"}, h("span", {"class": "mono"}, "GAP · "),
                          "The wording of this question is not in the guide's data.")
            href = contest_href(page, c["contest_id"])
            title = _question_title(c)
            items.append({
                "key": c["contest_id"], "name": title, "item_id": f"q-{c['contest_id']}",
                "facts": [e["date"][:4], _question_outcome(cands, cross, unoff), key_num], "status": st,
                "search": f"{jur} {c['label']} {_election_name(e)}",
                "body": [h("p", {"class": "elx-tags"}, status_badge(st, page), " ",
                           h("span", {"class": "elx-xc mono"}, "STATEWIDE · COUNTY PORTION ONLY") if cross else
                           h("span", {"class": "elx-xc mono"}, jur.upper()), " ",
                           h("span", None, _election_name(e))),
                         h("p", {"class": "elx-label muted"}, "Ballot line: ", c["label"]),
                         words, _question_fig(page, c),
                         h("p", None, h("a", {"href": href}, "Full result in the results explorer")) if href else None]})
        n = len(items)
        # saved-place preselect (static/js/preselect.js "first"): the group's layer when all its questions share one,
        # and the unit for here.js's "Your place" marker
        lays = {contest_layer(ed, c) for c in groups[jur]}
        lay = next(iter(lays)) if len(lays) == 1 else ""
        # only a city or town: here.js's marker would call a default school corporation "Your school corporation"
        unit = lay.split(":", 1)[1] if lay.startswith("municipality:") else None
        blocks.append(h("div", {"class": "elx-qgroup", "id": f"q-group-{_slug(jur)}", "data-here-layer": lay or None,
                                "data-here-name": jur if lay else None, "data-here-unit": unit},
                        h("h3", {"class": "elx-qgroup-h"}, jur, h("span", {"class": "elx-qgroup-n muted"},
                                                                  f" · {n} question{'s' if n != 1 else ''}")),
                        h("p", {"class": "muted elx-qgroup-note"},
                          "The county tally only; the statewide result is decided by all counties."
                          if jur == "Statewide" else "Decided by voters in this area."),
                        entity_list(f"q-list-{_slug(jur)}", items, noun="question", heading_tag="h4",
                                    label=f"{jur} questions, newest first")))
    page.add(section("questions", 4, "Public questions",
                     h("p", None, f"Every public question on ballots in the county in the guide's data, {len(qs)} in all, "
                                  "grouped by who voted on it and newest first. Each row shows the year, the outcome and the "
                                  "yes and no shares, and opens to the question's wording and result. Statewide questions "
                                  "show the county tally only."),
                     here_slot("first", "q-groups"),
                     h("div", {"class": "elx-qgroups", "id": "q-groups"}, blocks), scope="county", ed=ed))

    # ---- school labels
    page.add(section("school-labels", 5, "School-board party labels",
                     _rule_p(page, ed, "partisan_school_board"),
                     h("p", {"class": "muted"}, "Labels used on this county's 2026 ballot are not counted yet: the guide's "
                                                "results data and research notes disagree (see Gaps)."),
                     h("p", None, h("a", {"href": page.rel("elections/how-it-works/index.html#school-boards")}, "More on the 2025 change")),
                     scope="indiana", ed=ed))
    page.finish(gaps=_gaps(ed, "elections-judges") + _gaps(ed, "elections-schools") + _gaps(ed, None, ["gaps_results", "gaps_indiana"], r"question|retention|RETAIN|IC 33-33"))
    return page


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


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


# =========================================================================== 5. shared with pages/elections_numbers.py (turnout chart, margin filters)

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


_PRIMARY_TAIL = re.compile(r"\s*\([^()]*primary\)\s*$", re.I)
_DISTRICT = re.compile(r"\bDistrict\s+(\w+)")


def _search_text(label: str) -> str:
    """What a reader's typed words match for a contest: its name without the primary's party label
    (the page has no party filter, so a search must not act as one)."""
    return _PRIMARY_TAIL.sub("", label)


def _district_of(label: str) -> str:
    m = _DISTRICT.search(label)
    return f"District {m.group(1)}" if m else ""


def _district_key(d: str):
    k = d.split(" ", 1)[1]
    return (0, int(k), "") if k.isdigit() else (1, 0, k)


def _opts(values) -> list[tuple[str, str]]:
    return [(v, v) for v in values]


def _unit_attrs(ed, office) -> dict:
    """Level and government (place or body) of an office, for the table filters."""
    u = ed.units.get(office["unit_id"], {})
    return {"data-tf-level": LEVEL_LABEL.get(u.get("unit_type"), u.get("unit_type", "")),
            "data-tf-government": u.get("name", "")}


def _unit_controls(ed, offices) -> list[dict]:
    attrs = [_unit_attrs(ed, o) for o in offices]
    levels = sorted({a["data-tf-level"] for a in attrs}, key=lambda x: next((i for i, (_, lab) in enumerate(LEVELS) if lab == x), 99))
    gov = {}
    for o, a in zip(offices, attrs):
        gov[a["data-tf-government"]] = _place_order(ed, o)
    return [{"key": "level", "label": "Level", "all": "All levels", "options": _opts(levels)},
            {"key": "government", "label": "Government", "all": "All governments",
             "options": _opts(sorted(gov, key=lambda g: (gov[g], g)))}]


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
    "elections/index.html": build_hub,
    HOW_IT_WORKS: build_how_it_works,
    "elections/calendar/index.html": build_calendar,
    "elections/results/index.html": build_results,
    "elections/judges-and-questions/index.html": build_judges,
    # elections/landscape/ (overview), margins/, turnout/ and officeholders/ are built by pages/elections_numbers.py
}
