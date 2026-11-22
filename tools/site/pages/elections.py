"""Elections section: the elections hub (elections/index.html), how elections work (elections/how-it-works/), calendar,
find a result (elections/results/; the explorer until phase 6 step 4), judges and public questions. The election pages
(elections/<id>/) are pages/election_pages.py. The elections-by-the-numbers pages (landscape overview, margins, turnout, officeholders) are
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
from civic.components import (STATUS, status_heading, callout, data_table, entity_list, filter_empty_note, see_all_table, table_filter, party_label, scope_badge, section, status_badge, status_label, mark_symbol,
                              variant_slot)
from civic.data import (PARTY_LABELS, SELECTED_BY_LABELS, fmt_date, fmt_int, nth_weekday_after, parse_date,
                        split_ids)
from civic import election_pages as EP
from civic import overall as OV
from civic import results_status as RS
from civic.html import Markup, h, join, json_script
from civic.offices import href as office_href
from civic.related import contest_anchor
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
# the statewide and federal offices of offices.csv (2026-11-18) sit with the rule-made statewide and federal rows
CALENDAR_LEVEL = {"state": "statewide", "federal_chamber": "federal"}
LEVEL_ORDER = {k: i for i, (k, _) in enumerate(LEVELS)}

GROUPS = ["County row offices", "County commissioners", "County council", "County courts",
          "Superior Court retention", "Township offices", "City offices", "Town offices", "School boards",
          "State legislature", "Statewide offices", "State court retention", "Federal offices", "Public questions",
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


def _low_rules(ed, keys) -> list[dict]:
    """The rules among ``keys`` held at low confidence (the "-low" tables print only these)."""
    return [r for k in keys for r in [ed.rules.get(k)] if r and r.get("confidence") == "low"]


# the explainer's low-confidence tables (id -> its rule keys and the section that holds it)
LOW_TABLES = {"primaries-low": (["independent_signature_example"], "primaries"),
              "vacancies-low": (["precinct_committeepersons"], "vacancies")}


def how_it_works_moved(ed) -> dict:
    """The hub's forwarding map for the explainer's old ids. A low-confidence table is printed only while its rule is
    held at low confidence; when it is not, its old id goes to its section (phase 6 step 4 fix: it pointed at an id
    that was no longer on the page)."""
    out = {}
    for i in HOW_IT_WORKS_IDS:
        base = i[:-len("-copy")] if i.endswith("-copy") else i
        if base in LOW_TABLES and not _low_rules(ed, LOW_TABLES[base][0]):
            out[i] = f"{HOW_IT_WORKS}#{LOW_TABLES[base][1]}"
        else:
            out[i] = f"{HOW_IT_WORKS}#{i}"
    return out


def _low_rules_table(page, ed, keys, tid):
    rows = []
    for k in keys:
        r = ed.rules.get(k)
        if r and r.get("confidence") == "low":
            rows.append([r["plain_language"], r.get("detail", ""),
                         h("span", None, status_label(r["status"], page), " ", status_label("low", page),
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
    if rest.startswith(("us-house", "us-representative")):
        # 2026-11-18: the U.S. House district reaches beyond the county (the canvass prints the county part only)
        return "Federal offices", "Congressional district (county portion)", True
    if rest.startswith(("us-senate", "us-president", "president")):
        return "Federal offices", "Statewide", True
    if rest.startswith("state-retention"):
        # a retention vote for a St. Joseph Superior Court judge that the canvass files under a state line (2026
        # Fronk, Francisco): civic/data.py CONTEST_OFFICE_ALIASES links it to its Superior Court seat, so it is decided
        # by this county's voters alone
        if (c.get("office_id") or "").startswith("superior-court-judge-"):
            return "Superior Court retention", "St. Joseph County", False
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


PAGE_JQ = "elections/judges-and-questions/index.html"
# question-group ids before the 2026-11-18 merge -> the group's name now
OLD_QUESTION_GROUPS = {"new-prairie-schools": "New Prairie United School Corporation",
                       "south-bend-community-schools": "South Bend Community School Corporation"}


def contest_layer(ed, c) -> str:
    """The saved-place layer (civic/preselect.py here_layer) of the voters who decide a contest: "state" for statewide,
    appellate and legislative contests, "county" for county-wide ones, else the city, town, township or school
    corporation from the contest id. "" when none fits (LaVille schools: no unit in the guide's data), and then the
    preselect never hides the contest. Added 2026-11-09 (Wave E batch 8)."""
    group, place, _ = classify(c)
    if place.startswith(("Statewide", "Legislative district", "Congressional district")):
        return "state"
    if group == "Public questions":
        # the ballot line names the government that put the question (2026-11-18: the 2013 and 2016 "mishawaka"
        # questions were the School City of Mishawaka's, as the merged canvass labels say); its name decides
        named = [uid for uid, u in ed.units.items() if (u.get("name") or "").strip() == place]
        if len(named) == 1:
            return here_layer(ed, named[0])
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


def _nav(page, target: str, noun: str, plural: str, tab: str = "elections", folded: bool = False, what=None,
         count_in: str | None = None):
    """The map navigator on an Elections page (civic/navmap.py): selecting an area again opens its government's or
    office's ``tab`` (Elections by default), else its page."""
    from civic import governments as gm
    from civic import navmap as nm
    from civic import offices as om

    def href_of(key):
        kind, _, ident = key.partition(":")
        if kind == "u":
            return gm.unit_href(page, ident, tab) or gm.unit_href(page, ident)
        if kind == "o":
            return om.href(page, ident, tab) or om.href(page, ident)
        return None
    return nm.navigator(page, nm.tags_for(page), target, noun=noun, plural=plural, href_of=href_of, folded=folded,
                        open_label="Open its elections", what=what, count_in=count_in)


def contest_keys(page, c, offices_only_districts: bool = False) -> str:
    """A contest's area keys for the map navigator (civic/navmap.py; 2026-11-18): its office's keys when the contest
    is linked to an office, else the government whose voters decide it (contest_layer: a city, town, township, school
    corporation, the county) or the statewide level. "" when nothing fits (never filtered into an area it may not
    belong to). ``offices_only_districts``: keep the office key only for a district seat (the Elections hub's
    election rows name governments, plus the districts a reader can pick on the map)."""
    from civic import navmap as nm
    t = nm.tags_for(page)
    oid = c.get("office_id") or ""
    if oid and oid in page.ed.offices:
        o = page.ed.offices[oid]
        keys = t.office_keys(oid)
        if offices_only_districts and not nm._districted(o):
            keys = [k for k in keys if not k.startswith("o:")]
        return t.join(" ".join(keys))
    lay = contest_layer(page.ed, c)
    if lay == "state":
        return t.join(nm.level_key("statewide"))
    if lay == "county":
        return t.unit("county")
    if ":" in lay:
        return t.unit(lay.split(":", 1)[1])
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
    """Changed 2026-11-18 ("About these figures"): the line that pointed to the badge definitions is gone; every page
    now ends with a note that defines the marks it uses. ``extra`` (a section's own short note) is still shown."""
    return h("p", {"class": "muted badge-key"}, extra) if extra else Markup("")


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
# Phase 6 step 4 (2026-11-16; design direction section 3): the hub leads with the next election in the county and what
# is on its ballot (from the calendar code; with a saved place it opens on the reader's governments, elections.js),
# then every election in elections.csv, newest first, one row each linking to its page (civic/election_pages.py),
# the latest years open and the older ones in a fold (ships open: without JavaScript a plain list), then four doors.
# Wave D batch 6: the explainer that used to be this page moved verbatim to elections/how-it-works/; every id it had is
# forwarded by static/js/moved.js (the hub's #moved-anchors map: the ids below, plus every src-<id> citation by
# prefix). tools/tests/test_wave_d_nav.py pins the list to the ids the page had before
# (tools/tests/fixtures/anchors_before_wave_d6.json); the hub's own old card ids are forwarded too (HUB_MOVED).

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
TIMELINE_OPEN_YEARS = 3      # the newest years with an election, listed open; older years sit in one fold
# the hub's four doors, in the design direction's order: (page, card id, one line about what is there)
HUB_DOORS = [
    ("elections/compare/index.html", "card-compare",
     "Every election since 2010 on the same measures: how close the races were, turnout with its base, and how many "
     "seats had no contest."),
    ("elections/judges-and-questions/index.html", "card-judges-and-questions",
     "Judicial retention votes and the public questions on the county's ballots, with their wording and results."),
    (HOW_IT_WORKS, "card-how-it-works",
     "Offices and cycles, primaries and getting on the ballot, how to vote and ID, vacancies and caucuses, "
     "school-board labels."),
    ("run/index.html", "card-run",
     "Eligibility, filing, petitions, caucuses and campaign-finance duties, with a page for each of six local offices."),
]
# the hub's cards before phase 6 step 4 -> where their pages are now
HUB_MOVED = {"card-calendar": "elections/index.html#next", "card-results": "elections/results/index.html#main",
             "card-landscape": "elections/compare/overview/index.html#main",
             "card-margins": "elections/compare/index.html#main",
             "card-turnout": "elections/compare/turnout/index.html#main"}


def _hub_next(page, ed):
    """(year, [line, who]) for the next election in the county: the earliest next_election year of any office
    (civic/layers.py rules), with the dates computed from the state calendar rule."""
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


def _hub_ballot(page, ed, y):
    """What is on the next ballot, one card per government (the calendar's "What's on your next ballot" items, with each
    office linked to its page). Cards carry the saved-place keys (data-here-layer, data-here-unit): elections.js shows
    the reader's governments first and alone, with a "Show all" button; here.js marks the reader's card."""
    from civic.preselect import here_layer
    cites = page.cites
    items, _ = _calendar_items(ed)
    if y not in items:
        return None
    by_unit: dict[str, list] = {}
    for it in items[y]:
        if it["office"]:
            by_unit.setdefault(it["office"]["unit_id"], []).append(it)
    cards = []
    for uid in sorted(by_unit, key=lambda u: (LEVEL_ORDER.get(ed.units[u]["unit_type"], 99), ed.units[u]["name"])):
        name = ed.units[uid]["name"]
        lis = []
        for it in by_unit[uid]:
            o = it["office"]
            oh = office_href(page, o["office_id"])
            label = h("a", {"href": oh}, it["label"]) if oh else it["label"]
            lis.append(h("li", None, label,
                         h("span", {"class": "muted"}, f" · {it['seats']} seats") if (it["seats"] or 1) > 1 else None,
                         cites.cite_compact(it["src"])))
        from civic import navmap as nm
        cards.append(h("div", {"class": "ehub-gov", "data-here-unit": uid, "data-here-layer": here_layer(ed, uid) or None,
                               "data-here-name": name, "data-nm": nm.tags_for(page).unit(uid) or None},
                       h("h3", {"class": "ehub-gov-h"}, name), h("ul", {"class": "ehub-gov-list"}, lis)))
    if not cards:
        return None
    later = [yy for yy in YEARS if yy > y and any(i["level"] in ("county", "court_system") for i in items[yy])]
    out = [h("p", None, f"If you live in one of these places, these offices are on your {y} ballot:", " ",
             status_badge("computed", page, "From offices.csv next_election and term_years.")),
           here_slot("explorer", "ehub-ballot", extra={"data-here-hub": "1"}),
           # the offices fold away under the places' names (folds.js; JS off it is a plain list); with a saved place
           # elections.js opens it on that place's offices alone
           h("details", {"class": "fold-details ehub-ballot-fold", "id": "ballot-offices", "data-fold": True,
                         "open": True},
             h("summary", {"class": "fold-summary ehub-ballot-sum"},
               f"Offices on the {y} ballot, place by place ({len(cards)} places, "
               f"{sum(len(v) for v in by_unit.values())} offices): ",
               h("span", {"class": "ehub-ballot-places"}, join([ed.units[u]["name"] for u in sorted(
                   by_unit, key=lambda u: (LEVEL_ORDER.get(ed.units[u]["unit_type"], 99), ed.units[u]["name"]))], ", ")),
               h("span", {"class": "fold-toggle", "aria-hidden": "true"})),
             h("div", {"class": "ehub-govs", "id": "ehub-ballot"}, cards))]
    if later and y % 2:
        p_after, g_after, _, src = _dates(ed, later[0])
        if p_after:
            out.append(h("p", {"data-here-uninc": True, "class": "ehub-uninc"},
                         f"If you live outside every city and town, your next regular election in the guide's data is "
                         f"the primary on {fmt_date(p_after, long=True)}, then the general on "
                         f"{fmt_date(g_after, long=True)}. ", status_badge("computed", page, "Dates from the statutory rule."),
                         cites.cite(src)))
    return out


def _timeline_row(page, ed, e):
    from civic import election_pages as EP
    from civic.tabs import status_mark
    eid = e["election_id"]
    n = len(EP.contests(ed, eid))
    to = _num(e.get("turnout_pct"))
    d = e.get("date") or ""
    when = fmt_date(d) if d.count("-") == 2 else d
    kind = EP.TYPE_TITLE.get(e["type"], e["type"])
    href = page.rel(EP.path(eid)) if EP.path(eid) in page.site.by_path else None
    name = kind[:1].upper() + kind[1:]
    keys = " ".join(contest_keys(page, c, offices_only_districts=True) for c in EP.contests(ed, eid))
    return h("li", {"class": "ehub-el", "id": f"el-{eid}", "data-nm": " ".join(dict.fromkeys(keys.split())) or None},
             h("span", {"class": "ehub-el-what"}, h("a", {"href": href}, name) if href else name),
             h("span", {"class": "ehub-el-when"}, when),
             h("span", {"class": "ehub-el-to"}, f"{to:.1f}% turnout" if to is not None else "Turnout not recorded",
               page.cites.cite_compact(e.get("source_ids"))),
             h("span", {"class": "ehub-el-n"}, f"{n} contest{'s' if n != 1 else ''}"),
             status_heading(e["status"], page))


def _timeline(page, ed):
    """Every election in elections.csv, newest first, grouped by year: the newest TIMELINE_OPEN_YEARS years open, the
    rest in a fold that ships open (folds.js closes it; a link into it opens it)."""
    from civic import election_pages as EP
    els = EP.ordered(ed, newest_first=True)
    by_year: dict[str, list] = {}
    for e in els:
        by_year.setdefault(EP.year(e), []).append(e)
    blocks = []
    for y, es in by_year.items():
        blocks.append(h("section", {"class": "ehub-year", "id": f"y{y}", "aria-labelledby": f"y{y}-h", "data-nm-group": True},
                        h("h3", {"class": "ehub-year-h", "id": f"y{y}-h"}, y),
                        h("ul", {"class": "ehub-els"}, [_timeline_row(page, ed, e) for e in es])))
    recent, older = blocks[:TIMELINE_OPEN_YEARS], blocks[TIMELINE_OPEN_YEARS:]
    years = list(by_year)
    n_old = sum(len(by_year[y]) for y in years[TIMELINE_OPEN_YEARS:])
    fold = h("details", {"class": "fold-details ehub-older", "id": "timeline-earlier", "data-fold": True, "open": True},
             h("summary", {"class": "fold-summary ehub-older-sum"},
               f"Earlier elections, {years[TIMELINE_OPEN_YEARS]} back to {years[-1]} ({n_old})",
               h("span", {"class": "fold-toggle", "aria-hidden": "true"})),
             older) if older else None
    pre = [e for e in els if int(EP.year(e)) < 2010]
    return section("timeline", None, "Every election",
                   h("p", None, f"{len(els)} elections in the guide's records, {years[-1]} to {years[0]}, newest first. "
                                "Each has its own page: turnout with its base, every contest on the ballot and, for "
                                "the 2020, 2022 and 2024 generals, how areas voted. Municipal elections count only the "
                                "voters of the places that held them, so their turnout is on a smaller base."),
                   h("p", {"class": "muted"}, f"Before 2010 the guide has only South Bend's mayoral races "
                                              f"({len(pre)} elections), from a secondary source.") if pre else None,
                   h("div", {"class": "ehub-timeline"}, recent, fold),
                   scope="county", ed=page.ed)


def build_hub(site):
    from pages.elections_numbers import _contested, _counts, margin_races   # elections_numbers imports this module
    from civic import election_pages as EP
    ed = site.ed
    page = site.page("elections/index.html", banners=True, body_class="ehub-page")
    cites = page.cites
    els = _elections(ed)
    span = f"{els[0]['date'][:4]} to {els[-1]['date'][:4]}"
    computed = lambda why: status_badge("computed", page, why)
    all_els = EP.ordered(ed)
    page.add(h("header", {"class": "thing-head hub-head"},
               page.crumb_nav(),
               h("h1", {"class": "thing-title"}, "Elections"),
               h("p", {"class": "thing-facts"},
                 f"The next election in the county, then every election in the guide's records "
                 f"({len(all_els)}, {EP.year(all_els[0])} to {EP.year(all_els[-1])}), each with its own page.")))

    # ---- next election and what is on its ballot
    ny, next_lines = _hub_next(page, ed)
    if next_lines:
        ballot = _hub_ballot(page, ed, int(ny)) if str(ny).isdigit() else None
        # the highlighted strip is the "when you vote" callout (looks.css); the ballot's cards follow it, unboxed
        page.add(h("section", {"class": "ehub-next-sec", "id": "next", "aria-labelledby": "next-h"},
                   h("div", {"class": "next-strip ehub-next"},
                     h("h2", {"id": "next-h", "class": "next-h mono"}, "Next election in the county"),
                     next_lines[0],
                     h("p", {"class": "next-link"},
                       h("a", {"href": page.rel("elections/calendar/index.html")}, "Election calendar"))),
                   ballot if ballot else next_lines[1],
                   h("p", {"class": "ehub-cal"}, "On the calendar: ",
                     h("a", {"href": page.rel("elections/calendar/index.html#next")}, "What's on your next ballot"), " · ",
                     h("a", {"href": page.rel("elections/calendar/index.html#deadlines")}, "Deadlines"), " · ",
                     h("a", {"href": page.rel("elections/calendar/index.html#by-year")}, "Every seat, 2026 to 2030"))))

    # ---- every election
    timeline = _timeline(page, ed)
    # ---- the map navigator (civic/navmap.py; maps on every major page, 2026-11-18): an area's seats on the next
    # ballot and the elections that had its contests
    nav = _nav(page, "ehub-ballot timeline", "election", "elections", count_in="timeline",
               what="Choose a layer, then select an area: the list of elections keeps only those with its contests "
                    "and the next ballot only its offices. Select it again to open its elections.")
    if nav is not None:
        from civic.tabs import tab_section
        page.add(tab_section("by-area", "Elections by area", nav))
    page.add(timeline)

    # ---- four doors, one sourced fact each
    facts: dict[str, Markup] = {}
    races = margin_races(ed)
    cnt = _counts(races)
    facts["elections/compare/index.html"] = h(
        "span", None, f"{cnt['unc']:,} of {len(races):,} local races had no contest; {_contested(cnt):,} were contested, "
                      f"{cnt['under-5']:,} of them by under 5 points. ",
        computed("Counted from results.csv vote counts and seat counts."),
        cites.cite_compact(_src(*[r["c"]["rows"][0] for r in races])))
    in_years = [c for c in ed.contests.values() if c["election_id"] in {e["election_id"] for e in els}]
    qs = [c for c in in_years if classify(c)[0] == "Public questions"]
    ret = [c for c in in_years if classify(c)[0] in ("Superior Court retention", "State court retention")]
    if qs or ret:
        facts["elections/judges-and-questions/index.html"] = h(
            "span", None, f"{len(qs)} public questions and {len(ret)} retention votes on the county's ballots, {span}. ",
            computed("Counted from results.csv."), cites.cite_compact(_src(*[c["rows"][0] for c in qs + ret])))
    run_pages = [e for e in site.entries if e.path.startswith("run/") and e.path != "run/index.html"]
    facts["run/index.html"] = h("span", None, f"Office pages: {', '.join(e.nav.lower() for e in run_pages)}.")
    cards = []
    for path, cid, what in HUB_DOORS:
        e = site.by_path[path]
        label = "Compare elections" if path == "elections/compare/index.html" else e.nav
        cards.append(h("article", {"class": "card ehub-card", "id": cid},
                       h("h3", {"class": "card-title"}, h("a", {"href": page.rel(path)}, label)),
                       h("p", None, what),
                       h("p", {"class": "ehub-fact"}, facts[path]) if path in facts else None))
    page.add(section("pages", None, "More about elections", h("div", {"class": "card-grid ehub-grid"}, cards),
                     h("p", None, "Looking for one result? ",
                       h("a", {"href": page.rel("elections/results/index.html")}, "Find a result"),
                       " by election or by office. Learning path: ",
                       h("a", {"href": page.rel(PATHS_FIRST["vote-smarter"])}, "Vote smarter"), ". ",
                       "Another path, ", h("a", {"href": page.rel(PATHS_FIRST["elections-by-the-numbers"])},
                                           "Elections by the numbers"), ", goes through the measures one at a time.")))
    page.add(moved_anchors(page, {**how_it_works_moved(ed), **HUB_MOVED}, prefixes={"src-": HOW_IT_WORKS}))
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
                       h("span", None, status_label(ot["status"], page), cites.cite(ot["source_ids"]))])
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
                     _low_rules_table(page, ed, LOW_TABLES["primaries-low"][0], "primaries-low"),
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
        badges = h("span", None, status_label(r["status"], page),
                   (" ", status_label("low", page)) if r.get("confidence") == "low" else None, cites.cite(r["source_ids"]))
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
                       h("a", {"href": page.rel("elections/compare/turnout/index.html#straight-party")}, "Turnout and how ballots were cast"), ")."),
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
                         h("span", None, status_label(t["status"], page),
                           (" ", status_label("low", page)) if t.get("confidence") == "low" else None, cites.cite_compact(t["source_ids"]))])
    page.add(section("vacancies", 6, "How vacancies are filled, and why it matters",
                     _rule_p(page, ed, "local_vacancy_caucus", detail=True),
                     _rule_p(page, ed, "legislative_vacancy_caucus", detail=True),
                     _low_rules_table(page, ed, LOW_TABLES["vacancies-low"][0], "vacancies-low"),
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
        level = CALENDAR_LEVEL.get(unit.get("unit_type", ""), unit.get("unit_type", ""))
        ys = years_on_ballot(o)
        if not ys:
            unscheduled.append(o)
        for y in ys:
            items[y].append({"level": level, "label": o["title"], "seats": _seats(o), "office": o,
                             "src": o["source_ids"], "status": o["status"]})
    rule = ed.rules.get("even_year_offices", {})
    gen = ed.rules.get("general_election_date", {})
    def has_office(y, lab):
        # a statewide office in offices.csv (2026-11-18) is placed from its own row; the rule's row is not repeated
        return any(i["level"] == "statewide" and i["office"] is not None and i["label"].startswith(lab)
                   for i in items[y])
    for y in YEARS:
        if y % 2:
            continue
        if y % 4 == 0:
            for lab in ("Governor", "Attorney General"):
                if has_office(y, lab):
                    continue
                items[y].append({"level": "statewide", "label": lab, "seats": 1, "office": None,
                                 "src": rule.get("source_ids", ""), "status": rule.get("status", "")})
            items[y].append({"level": "federal", "label": "Presidential electors", "seats": None, "office": None,
                             "src": gen.get("source_ids", ""), "status": gen.get("status", "")})
        else:
            for lab in ("Secretary of State", "Treasurer of State", "State Comptroller"):
                if has_office(y, lab):
                    continue
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
            note = h("p", {"class": "elx-yr-note"}, "Held. ", RS.brief(ed, "2026g"), " ",
                     h("a", {"href": EP.href(page, "2026g") or page.rel("elections/results/index.html")},
                       "The 2026 general election"))
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
                     _nav(page, "cal-years", "seat", "seats", "elections", folded=True,
                          what="Choose a layer, then select an area to list only its seats in every year. Select it "
                               "again to open its page."),
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


def _cal_keys(page, it) -> str:
    from civic import navmap as nm
    t = nm.tags_for(page)
    if it["office"]:
        return t.office(it["office"]["office_id"])
    return t.join(nm.level_key(it["level"])) if it["level"] in nm.LEVEL_NAMES else ""


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
                              "data-here-layer": here_layer(ed, o["unit_id"]) if o else "state",
                              # the map navigator (civic/navmap.py): the seat's area, or the level of a state line
                              "data-nm": _cal_keys(page, it)})
            grp["rows"].append(h("li", row_attrs,
                                 h("p", {"class": "cal-seat-h"}, h("span", {"class": "cal-office"}, it["label"]),
                                   h("span", {"class": "cal-meta"}, " · " + " · ".join(meta)), " ",
                                   status_badge(it["status"], page), cites.cite_compact(it["src"])),
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
            note = h("p", {"class": "muted"}, "Held on Nov 3, 2026. ", RS.brief(ed, "2026g"), " ",
                     h("a", {"href": EP.href(page, "2026g") or page.rel("elections/results/index.html")},
                       "The 2026 general election"))
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
        # the contest's office page (phase 6 step 1): its Elections tab lists every contest for the office
        oh = office_href(page, x["o"], "elections") if x["o"] else None
        label = [h("span", {"id": contest_anchor(x["id"])}, x["l"]),
                 [" ", h("a", {"class": "ec-office", "href": oh}, "Office")] if oh else None]
        rows.append([label, _election_short(e), x["g"], x["p"],
                     "; ".join(bits) + (" (county portion only)" if x["x"] else ""),
                     STATUS.get(x["s"], (x["s"].upper(),))[0]])   # plain label: 1,200 badge tooltips would double the table
        attrs.append({"data-tf-year": e["date"][:4], "data-tf-group": str(GROUP_ORDER.get(x["g"], len(GROUPS))),
                      "data-tf-place": p_ix[x["p"]], "data-nm": contest_keys(page, c) or None})
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
    """Find a result (elections/results/index.html). Phase 6 step 4 (2026-11-16): the explorer's job is done by the
    election pages (elections/<id>/contests/) and the office pages' Elections tabs, so this page is short: pick an
    election or an office (links), then the every-contest table in a fold (the no-JavaScript landing of an old
    #contest-<id> link; with JavaScript static/js/elections.js forwards that link to the contest on its election's
    page). The explorer's controls and its data are gone; their ids and the old turnout ids are forwarded
    (#moved-anchors)."""
    from civic import election_pages as EP
    from civic import offices as om
    from pages.elections_numbers import RESULTS_MOVED
    ed = site.ed
    page = site.page("elections/results/index.html", banners=True)
    cites = page.cites
    els = _elections(ed)
    eids = {e["election_id"] for e in els}
    contests = [c for c in ed.contests.values() if c["election_id"] in eids]
    from civic import navmap as nm
    toc = ([("by-area", "Results by area")] if nm.model(ed) else []) + [
           ("by-election", "Pick an election"), ("by-office", "Pick an office"),
           ("every", "Every contest in one table"),
           ("how-to-read", "How to read the results"), ("gaps", "Gaps"), ("sources", "Sources")]
    page.add(_hero(page, "Reference · Elections · Results",
                   "Every election and every office has its own page of results. Pick one below, or search every "
                   f"contest from {els[0]['date'][:4]} to {els[-1]['date'][:4]} in one table.",
                   ["county"], toc))

    # ---- pick an election: every row of elections.csv, by year, newest first
    by_year: dict[str, list] = {}
    for e in EP.ordered(ed, newest_first=True):
        by_year.setdefault(EP.year(e), []).append(e)
    rows = []
    for y, es in by_year.items():
        links = []
        for e in es:
            u = EP.href(page, e["election_id"])
            kind = EP.TYPE_TITLE.get(e["type"], e["type"])
            links.append(h("a", {"href": u}, kind[:1].upper() + kind[1:]) if u else kind)
        rows.append(h("li", {"class": "fr-year"}, h("span", {"class": "fr-y"}, y), " ", join(links, " · ")))
    page.add(section("by-election", 1, "Pick an election",
                     h("p", None, f"{len(ed.elections)} elections, newest first. Each page has the turnout, every "
                                  "contest on the ballot and, for the 2020, 2022 and 2024 generals, how areas voted."),
                     h("ul", {"class": "fr-years"}, rows),
                     scope="county", ed=ed))

    # ---- pick an office: every office with an Elections tab, by level and government
    groups: dict[str, dict[str, list]] = {}
    for o in ed.tables["offices"]:
        u = om.href(page, o["office_id"], "elections")
        if not u:
            continue
        groups.setdefault(om.level(ed, o), {}).setdefault(o["unit_id"], []).append((o, u))
    blocks = []
    for lvl, lvl_label in om.LEVELS.items():
        if lvl not in groups:
            continue
        govs = []
        for uid, offs in groups[lvl].items():
            from civic import navmap as nm
            t = nm.tags_for(page)
            govs.append(h("li", {"class": "fr-gov", "data-nm": t.join(*[t.office(o["office_id"]) for o, _u in offs])},
                          h("span", {"class": "fr-gov-n"}, om.unit_name(ed, uid)), ": ",
                          join([h("a", {"href": u}, om.short_title(ed, o)) for o, u in offs], " · ")))
        blocks.append(h("div", {"class": "fr-level", "data-nm-group": True}, h("h3", {"class": "fr-level-h"}, lvl_label),
                        h("ul", {"class": "fr-govs"}, govs)))
    n_off = sum(len(v) for g in groups.values() for v in g.values())
    page.add(section("by-office", 2, "Pick an office",
                     h("p", None, f"{n_off} offices with results in the guide. Each office's Elections tab lists every "
                                  "contest for it, general and primary, newest first."),
                     blocks, scope="county", ed=ed))

    # ---- every contest, one table (the old explorer's table: same ids, filters and rows)
    payload_c = [_contest_payload(ed, c) for c in contests]
    payload_c.sort(key=lambda x: (x["e"], GROUP_ORDER.get(x["g"], 99), x["p"], x["l"]))
    every = _every_contest_table(page, ed, payload_c)   # #contest-<id> rows (P10 deep links; the no-JavaScript view)
    cites.cite_compact(sorted({s for x in payload_c for s in split_ids(x["src"])}))
    # an old #contest-<id> link: elections.js sends it to the contest on its election's page (the election id is the
    # contest id's first part; the few contests whose id does not start with it are listed)
    fwd = {"e": {eid: page.rel(EP.path(eid, "contests")) for eid in sorted(ed.elections)
                 if EP.path(eid, "contests") in site.by_path},
           "x": {c["contest_id"]: c["election_id"] for c in ed.contests.values()
                 if not c["contest_id"].startswith(c["election_id"] + "-")}}
    page.add(section("every", 3, "Every contest in one table",
                     h("p", None, "Every contest since 2010 as one table, with filters and Copy CSV. Each contest is also "
                                  "on its election's page, with every candidate's result drawn."),
                     every, json_script("results-forward", fwd), scope="county", ed=ed))
    # the map navigator (civic/navmap.py; 2026-11-18): an area's offices in "Pick an office" and its contests in the
    # every-contest table; it goes right after the hero, once every row is tagged
    nav = _nav(page, "by-office every-contest", "contest", "contests", count_in="every-contest",
               what="Choose a layer, then select an area: Pick an office keeps only its offices and the every-contest "
                    "table only its contests. Select it again to open its elections.")
    if nav is not None:
        page.parts.insert(1, section("by-area", None, "Results by area", nav))

    # ---- how to read
    n_linked = sum(1 for c in contests if c["office_id"])
    page.add(section("how-to-read", 4, "How to read the results",
                     h("ul", None,
                       # 2026-11-18 ("About these figures"): a certified result carries no mark; the symbols of the
                       # exceptions are listed, each meaning once, in the note at the bottom of the page
                       h("li", None, "Marks: a certified or official result carries none. ", mark_symbol("unofficial"),
                         " unofficial, ", mark_symbol("from_scan"), " from a scanned page, ", mark_symbol("low"),
                         " low confidence, ", mark_symbol("computed"), " a share the guide calculated from the vote counts "
                         "because the canvass did not print it. The note at the bottom of the page says what each means."),
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
    # ids that left this page (phase 6 step 4): the turnout chart is on Compare: Turnout, the explorer's controls are
    # replaced by the pick lists
    t = EP.COMPARE_PATH["turnout"]
    moved = {**RESULTS_MOVED, "turnout": f"{t}#turnout", "turnout-h": f"{t}#turnout-h",
             **{f"turnout-general{x}": f"{t}#turnout-general{x}" for x in ("", "-details", "-table", "-table-copy")},
             **{i: "elections/results/index.html#by-election" for i in
                ("elx-year", "elx-election", "elx-group", "elx-place", "elx-count", "elx-results", "elx-more", "elx-data")}}
    page.add(moved_anchors(page, moved))
    page.finish(gaps=_gaps(ed, "elections-results", ["gaps_results"]))
    return page


# =========================================================================== 4. judges and questions

def _retention_row(page, ed, c, y, n, who):
    """One retention vote as table cells: year, who, yes, no, yes share, status, link to the full result."""
    tot = y["votes"] + n["votes"]
    share = 100.0 * y["votes"] / tot
    st = contest_status(c["rows"])
    low = y["low"] or n["low"]
    href = EP.contest_href(page, c["contest_id"])
    return share, low, st, [ed.elections[c["election_id"]]["date"][:4], who, fmt_int(y["votes"]), fmt_int(n["votes"]),
                            f"{share:.1f}%",
                            h("span", None, status_label(st, page), (" ", status_label("low", page)) if low else None,
                              page.cites.cite(_src(*c["rows"]))),
                            h("a", {"href": href}, "Full result") if href else h("span", {"class": "muted"}, "Not on an election page")]


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
        href = EP.contest_href(page, c["contest_id"])
        inf = OV.info(ed, c)   # the overall (statewide or appellate district) result beside the county tally
        if inf["basis"] == "overall":
            oy, on_ = OV._num((inf["by"].get("YES") or {}).get("overall_votes")), OV._num((inf["by"].get("NO") or {}).get("overall_votes"))
            ocell = (h("span", None, f"{100 * oy / (oy + on_):.1f}% yes", OV._computed(page, "overall_pct", inf),
                       f" · {'retained' if oy > on_ else 'not retained'}" if oy != on_ else " · tied",
                       OV._computed(page, "overall_winner", inf), cites.cite(inf["source_ids"]))
                     if oy is not None and on_ is not None and oy + on_ > 0 else "not recorded")
        else:
            ocell = h("span", {"class": "muted"}, OV.basis_sentence(ed, c, inf) or "")
        srows.append([ed.elections[c["election_id"]]["date"][:4], c["label"].replace("Retention: ", ""),
                      fmt_int(y["votes"]) if y else "", fmt_int(n["votes"]) if n else "",
                      f"{share:.1f}%" if share is not None else "", ocell,
                      h("span", None, status_label(contest_status(c["rows"]), page), cites.cite(_src(*c["rows"]))),
                      h("a", {"href": href}, "Full result") if href else h("span", {"class": "muted"}, "Not on an election page")])
    rl = ed.rules.get("retain_justice_labels", {})
    page.add(section("state-retention", 3, "Retention votes for state courts (county portion only)",
                     h("p", None, rl.get("plain_language", ""), " ", rl.get("detail", ""), cites.cite(rl.get("source_ids")), " ",
                       status_badge(rl.get("status", ""), page)),
                     h("p", None, "These votes are decided statewide or across an appellate district, so the county tally below "
                                  "does not show who was retained; the Overall result column does, where the guide has "
                                  f"it ({RS.STATE_PHRASE}). Names and courts are as printed on the canvass. ",
                       h("a", {"href": page.rel("state/index.html")}, "State government")),
                     see_all_table("state-retention-table",
                                   ["Year", "Ballot line", "Yes", "No", "Yes share (county)", "Overall result", "Status",
                                    "Result"],
                                   srows, noun="vote", caption="State court retention: St. Joseph County tally and the "
                                                               "overall result",
                                   numeric=(2, 3, 4), min_width="54rem",
                                   summary=f"See all {len(srows)} state court retention votes"),
                     scope="indiana", ed=ed))

    # ---- public questions (wording from ballot_questions.csv, 2026-11-18; was a dict in this file)
    wording = question_wordings(ed)
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
                words = wording_block(page, w)
            else:
                words = h("p", {"class": "elx-gapline"}, h("span", {"class": "mono"}, "GAP · "),
                          "The wording of this question is not in the guide's data.")
            href = EP.contest_href(page, c["contest_id"])
            title = _question_title(c)
            sw = OV.question_statewide(ed, c)   # a statewide question's overall result (2024: "Statewide: Yes (ratified)")
            items.append({
                "attrs": {"data-nm": contest_keys(page, c) or None},
                "key": c["contest_id"], "name": title, "item_id": f"q-{c['contest_id']}",
                "facts": [e["date"][:4], _question_outcome(cands, cross, unoff), key_num, sw], "status": st,
                "search": f"{jur} {c['label']} {_election_name(e)}",
                "body": [h("p", {"class": "elx-tags"}, status_badge(st, page), " ",
                           h("span", {"class": "elx-xc mono"}, "STATEWIDE · COUNTY PORTION ONLY") if cross else
                           h("span", {"class": "elx-xc mono"}, jur.upper()), " ",
                           h("span", None, _election_name(e))),
                         h("p", {"class": "elx-label muted"}, "Ballot line: ", c["label"]),
                         words, _question_fig(page, c), OV.after_figure(page, c),
                         h("p", None, h("a", {"href": href}, "Full result on the election's page")) if href else None]})
        n = len(items)
        # saved-place preselect (static/js/preselect.js "first"): the group's layer when all its questions share one,
        # and the unit for here.js's "Your place" marker
        lays = {contest_layer(ed, c) for c in groups[jur]}
        lay = next(iter(lays)) if len(lays) == 1 else ""
        # only a city or town: here.js's marker would call a default school corporation "Your school corporation"
        unit = lay.split(":", 1)[1] if lay.startswith("municipality:") else None
        blocks.append(h("div", {"class": "elx-qgroup", "id": f"q-group-{_slug(jur)}", "data-here-layer": lay or None,
                                "data-nm-group": True,
                                "data-here-name": jur if lay else None, "data-here-unit": unit},
                        h("h3", {"class": "elx-qgroup-h"}, jur, h("span", {"class": "elx-qgroup-n muted"},
                                                                  f" · {n} question{'s' if n != 1 else ''}")),
                        h("p", {"class": "muted elx-qgroup-note"},
                          "The St. Joseph County tally. The statewide result is decided by all counties and is shown with the "
                          "question where the guide has it."
                          if jur == "Statewide" else "Decided by voters in this area."),
                        entity_list(f"q-list-{_slug(jur)}", items, noun="question", heading_tag="h4",
                                    label=f"{jur} questions, newest first")))
    page.add(section("questions", 4, "Public questions",
                     h("p", None, f"Every public question on ballots in the county in the guide's data, {len(qs)} in all, "
                                  "grouped by who voted on it and newest first. Each row shows the year, the outcome and the "
                                  "yes and no shares, and opens to the question's wording and result. Statewide questions "
                                  "show the St. Joseph County tally, with the statewide result where the guide has it."),
                     # the map navigator (civic/navmap.py; 2026-11-18): an area's own questions
                     _nav(page, "q-groups", "question", "questions", folded=True,
                          what="Choose a layer, then select an area to list only the questions its voters decided "
                               "(statewide questions: Statewide, beside the map). Select it again "
                               "to open its elections."),
                     here_slot("first", "q-groups"),
                     h("div", {"class": "elx-qgroups", "id": "q-groups"}, blocks), scope="county", ed=ed))

    # ---- school labels
    page.add(section("school-labels", 5, "School-board party labels",
                     _rule_p(page, ed, "partisan_school_board"),
                     h("p", {"class": "muted"}, "Labels used on this county's 2026 ballot are not counted yet: the guide's "
                                                "results data and research notes disagree (see Gaps)."),
                     h("p", None, h("a", {"href": page.rel("elections/how-it-works/index.html#school-boards")}, "More on the 2025 change")),
                     scope="indiana", ed=ed))
    # a source this page no longer cites (2026-11-18: the question wordings moved to ballot_questions.csv, and the
    # canvass RES-029 was superseded by RES-048) keeps its old #src-<id> link working: it lands on the sources index
    # question groups are named from the ballot lines; the merged canvass labels (2026-11-18) give the corporations'
    # full names, so the old group ids forward to the new ones
    moved_q = {f"q-group-{old}": f"{PAGE_JQ}#q-group-{_slug(new)}" for old, new in OLD_QUESTION_GROUPS.items()
               if new in groups}
    page.add(moved_anchors(page, moved_q, prefixes={"src-": "about/sources/index.html"}))
    page.finish(gaps=_gaps(ed, "elections-judges") + _gaps(ed, "elections-schools") + _gaps(ed, None, ["gaps_results", "gaps_indiana"], r"question|retention|RETAIN|IC 33-33"))
    return page


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# how each ballot_questions.csv wording was obtained (data/SCHEMA.md wording_kind), said under the quotation
WORDING_KIND = {
    "official_record": "The state or county record of the question as voted.",
    "dlgf_approved": "Wording the Department of Local Government Finance approved; the printed ballot was not seen.",
    "sample_ballot": "From the county's sample ballot.",
    "reconstructed": "Reconstructed from partial records; not the printed text.",
}


def question_wordings(ed) -> dict[str, dict]:
    """{contest_id: ballot_questions.csv row} for rows with wording (added 2026-11-18). A row whose contest is not in
    results.csv is skipped with a data warning (tools/check_results.py rejects it too); a duplicate keeps the first."""
    out: dict[str, dict] = {}
    for r in ed.table("ballot_questions"):
        cid = (r.get("contest_id") or "").strip()
        if not cid or not (r.get("wording") or "").strip():
            continue
        if cid not in ed.contests:
            ed.warnings.append(f"ballot_questions: {cid} is not a contest in results.csv")
            continue
        if cid in out:
            ed.warnings.append(f"ballot_questions: duplicate wording for {cid}; the first is shown")
            continue
        out[cid] = r
    return out


def wording_block(page, w: dict):
    """The question as worded (verbatim), then how the wording was obtained, its notes, mark and sources."""
    kind = WORDING_KIND.get((w.get("wording_kind") or "").strip())
    if kind is None:
        page.ed.warnings.append(f"ballot_questions: {w.get('contest_id')} has an unknown wording_kind")
        kind = "How this wording was obtained is not recorded."
    notes = (w.get("notes") or "").strip()
    return h("blockquote", {"class": "elx-wording"}, h("p", {"data-verbatim": True}, w["wording"].strip()),
             h("footer", None, status_badge(w.get("status") or "", page), " ", kind,
               (" " + notes) if notes else None, page.cites.cite(w.get("source_ids"))))


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
        notes.append("Unofficial count; no result is marked until it is final.")
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
