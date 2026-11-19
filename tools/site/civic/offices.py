"""Office pages: paths, which tabs each office has, and the per-office data the tabs are drawn from (phase 6 step 1,
2026-11-16). One page per row of offices.csv (multi-seat bodies and district seats are modelled there, one office_id
each), with the tabs of civic/tabs.py:

    offices/index.html                   the Offices hub (pages/offices.py build_hub)
    offices/<office_id>/index.html       Overview
    offices/<office_id>/elections/       every contest for the office in results.csv, general and primary
    offices/<office_id>/money/           campaign money by election cycle (filings and news-reported figures)
    offices/<office_id>/history/         every holder in terms.csv
    offices/<office_id>/sources/         citations and gaps

Nothing here re-derives a figure. Contests come from Edition.contests (office_id derived from contest_id with
CONTEST_OFFICE_ALIASES, civic/data.py); campaign money comes from the race model the campaign pages are built from
(pages/campaigns.py cf_all, civic/campaign_money.py) and the news-reported figures from pages/money_history.py
reported(); state legislators' committees from money_history.legislators(). The sitemap, the search index and the
pages all read ``office_tabs`` so a tab bar never links to a tab that is not built.

``money_model`` imports the page modules lazily (they import civic modules at load time).
"""
from __future__ import annotations

import re
from collections import OrderedDict

from . import tabs

HUB = "offices/index.html"
GROUP = "Offices"

# level of government for the hub's filter and grouping, by units.csv unit_type (courts sit with the county)
# 2026-11-18 (gap-fill round 2): the statewide offices and appellate courts (unit in-state, unit_type "state") and the
# federal seats (us-house, us-senate: "federal_chamber") are levels of their own, after the legislature
LEVEL_OF_UNIT = {"county": "county", "court_system": "county", "city": "city", "town": "town",
                 "township": "township", "school_corporation": "school", "state_chamber": "state",
                 "state": "statewide", "federal_chamber": "federal"}
LEVELS = OrderedDict([("county", "County"), ("city", "Cities"), ("town", "Towns"), ("township", "Townships"),
                      ("school", "School boards"), ("state", "State legislature"),
                      ("statewide", "Statewide offices and courts"), ("federal", "Federal offices")])
LEVEL_IDS = {"county": "county", "city": "cities", "town": "towns", "township": "townships", "school": "schools",
             "state": "state", "statewide": "statewide", "federal": "federal"}
# unit types whose seats are not local: the landing page's "elected seats" count leaves them out
NON_LOCAL_UNIT_TYPES = ("state_chamber", "state", "federal_chamber")
STATE_TYPES = ("state_house", "state_senate")
UNIT_SHORT = {"sjc-courts": "St. Joseph County courts", "in-state": "State of Indiana",
              "us-house": "U.S. House of Representatives", "us-senate": "U.S. Senate"}
# the first year the county posts local campaign-finance reports online (research/campaign-finance-county-filings.md;
# pages/money_history.py POSTED_FROM): earlier elections have no filings in the guide
POSTED_FROM_YEAR = 2023


def base(office_id: str) -> str:
    return f"offices/{office_id}/"


def path(office_id: str, tab: str = "overview") -> str:
    return tabs.tab_path(base(office_id), tab)


def unit_name(ed, unit_id: str) -> str:
    u = ed.units.get(unit_id) or {}
    return UNIT_SHORT.get(unit_id, u.get("name", unit_id))


def short_title(ed, office: dict) -> str:
    """The office without its government's name, for the breadcrumb ("Mayor of South Bend" -> "Mayor",
    "Centre Township Trustee" -> "Trustee"); districts and seats are kept."""
    unit = ed.units.get(office["unit_id"]) or {}
    t = office["title"]
    names = [unit.get("name", ""), re.sub(r"^(City|Town) of ", "", unit.get("name", ""))]
    for n in sorted({n for n in names if n}, key=len, reverse=True):
        t2 = re.sub(rf"(^|\s)(of\s+)?{re.escape(n)}(\s|,|$)", r"\1\3", t).strip(" ,")
        if t2 and t2 != t:
            t = re.sub(r"\s{2,}", " ", t2)
            break
    return t[:1].upper() + t[1:]


def government_page(ed, unit_id: str) -> tuple[str, str] | None:
    """(site path, label) of the page about the office's government."""
    u = ed.units.get(unit_id)
    if not u:
        return None
    t = u["unit_type"]
    # phase 6 step 3: governments have their own pages (civic/governments.py); the old places/county/schools paths
    # are forwarding pages. Imported here because governments.py is built on the same tab helper.
    from . import governments as gm
    if t == "court_system":
        p = gm.unit_page(ed, "county")
        return (p + "#courts", "County courts") if p else None
    if t in ("city", "town", "township", "county", "school_corporation"):
        p = gm.unit_page(ed, unit_id)
        if p:
            return p, ("County government" if t == "county" else u["name"])
        return None
    if t == "state_chamber":
        return "state/your-legislators/index.html", "Your legislators"
    if t == "state":
        return "state/index.html", "State government"
    return None


def level(ed, office: dict) -> str:
    return LEVEL_OF_UNIT.get((ed.units.get(office["unit_id"]) or {}).get("unit_type", ""), "county")


def level_note(ed, lvl: str) -> str | None:
    """What a statewide or federal level covers in this county, in words built from units.csv and offices.csv, for
    the maps' State and Federal layers (2026-11-18, owner: keep the county map, say which view is shown, never draw
    Indiana or the U.S.). "statewide": every voter in the county votes on these. "federal": the U.S. Senate seats are
    statewide; a U.S. House district "includes all of" the county only when units.csv says the county lies wholly in
    it (otherwise "includes part of", and the map draws no part, having no boundary for it). None for other levels or
    when the edition has no such office."""
    county = ed.county_label
    offs = [o for o in ed.tables["offices"] if level(ed, o) == lvl]
    if not offs:
        return None
    if lvl == "statewide":
        return (f"Statewide offices: every voter in {county} votes on these, with the voters of every other county. "
                f"The map shows {county} only.")
    if lvl != "federal":
        return None
    parts = []
    senate = [o for o in offs if ed.units.get(o["unit_id"], {}).get("unit_id") == "us-senate"
              or o["office_type"] == "us_senator"]
    if senate:
        parts.append(f"U.S. Senate: every voter in {county} votes for Indiana's {len(senate)} senator"
                     f"{'s' if len(senate) != 1 else ''}, statewide.")
    for o in offs:
        if o["office_type"] != "us_representative":
            continue
        cov = (ed.units.get(o["unit_id"]) or {}).get("places_covered", "")
        d = o.get("district") or "?"
        if re.search(r"wholly", cov, re.I):
            parts.append(f"U.S. House District {d}: includes all of {county}.")
        else:
            parts.append(f"U.S. House District {d}: includes part of {county}; the guide has no boundary for that "
                         "part, so none is drawn.")
    parts.append(f"The map shows {county} only.")
    return " ".join(parts)


def office_coverage(ed, office: dict) -> str | None:
    """Who in the county votes for one statewide or federal office, in one sentence (level_note's words for that
    office); None for a local or legislative office."""
    lvl = level(ed, office)
    county = ed.county_label
    if lvl == "statewide" or (lvl == "federal" and office["office_type"] == "us_senator"):
        return f"Statewide: every voter in {county} votes on this office, with the voters of every other Indiana county."
    if lvl == "federal" and office["office_type"] == "us_representative":
        cov = (ed.units.get(office["unit_id"]) or {}).get("places_covered", "")
        d = office.get("district") or "?"
        if re.search(r"wholly", cov, re.I):
            return f"U.S. House District {d} includes all of {county}, and voters in other counties too."
        return f"U.S. House District {d} includes part of {county}; the guide has no boundary for that part."
    return None


def level_covers_county(ed, lvl: str) -> bool:
    """True when every office of a statewide or federal level is voted on by the whole county (the map may then shade
    the county outline for that level). A House district not stated to hold the whole county makes it False."""
    offs = [o for o in ed.tables["offices"] if level(ed, o) == lvl]
    if not offs or lvl not in ("statewide", "federal"):
        return False
    for o in offs:
        if o["office_type"] == "us_representative" and not re.search(
                r"wholly", (ed.units.get(o["unit_id"]) or {}).get("places_covered", ""), re.I):
            return False
    return True


# ------------------------------------------------------------------ contests

def contests(ed, office_id: str) -> list[dict]:
    """Every contest for the office in results.csv, general and primary, newest election first (ties: the general
    election, then primaries in party order)."""
    out = [c for c in ed.contests.values() if c["office_id"] == office_id]

    def key(c):
        d = (ed.elections.get(c["election_id"]) or {}).get("date") or c["election_id"][:4]
        return (d, 0 if c["party_primary"] else 1, c["party_primary"] or "")
    # newest date first; within a date the general first; primaries D before R (ballot order is the county's, the
    # order here only needs to be stable)
    out.sort(key=lambda c: key(c)[0], reverse=True)
    by_date: OrderedDict = OrderedDict()
    for c in out:
        by_date.setdefault(key(c)[0], []).append(c)
    res = []
    for d, cs in by_date.items():
        res += sorted(cs, key=lambda c: (0 if not c["party_primary"] else 1, c["party_primary"] or "", c["contest_id"]))
    return res


def contest_year(ed, c: dict) -> str:
    return ((ed.elections.get(c["election_id"]) or {}).get("date") or c["election_id"])[:4]


# ------------------------------------------------------------------ campaign money

def race_office_id(ed, race: dict) -> str:
    """The office a campaign-money race (civic/campaign_money.py build_races) is for: its general-election contest's
    office, else the office of any primary contest its candidates ran in."""
    c = ed.contests.get(race["id"])
    if c and c["office_id"]:
        return c["office_id"]
    for cand in race.get("candidates", []):
        for cid in cand.get("contests", []):
            c = ed.contests.get(cid)
            if c and c["office_id"]:
                return c["office_id"]
    return ""


def races_by_office(ed) -> dict:
    """office_id -> [campaign races], newest cycle first (cached per build)."""
    got = ed.__dict__.get("_office_races")
    if got is not None:
        return got
    from pages.campaigns import cf_all
    out: dict = {}
    for r in sorted(cf_all(ed)["races"], key=lambda r: r["date"], reverse=True):
        oid = race_office_id(ed, r)
        if oid:
            out.setdefault(oid, []).append(r)
    ed.__dict__["_office_races"] = out
    return out


def money_model(ed, office_id: str) -> dict:
    """Everything the Money tab shows, by election year (newest first):

    cycles: [{year, races: [races with any report on file], empty_races: [races with none], reported: [(contest,
             [cf_reported rows])]}] for years with money on record
    not_posted: years with contests but before the county posted reports (and no news figures)
    no_reports: years in the posted era whose races have no report on file for any candidate
    legislators: state House/Senate candidates of this office's contests with committees in cf_state(_history)
    """
    cache = ed.__dict__.setdefault("_office_money", {})
    if office_id in cache:
        return cache[office_id]
    from pages import money_history as mh
    from .campaign_money import same_person
    office = ed.offices[office_id]
    cs = contests(ed, office_id)
    years = sorted({contest_year(ed, c) for c in cs}, reverse=True)
    model = {"cycles": [], "not_posted": [], "no_reports": [], "legislators": [], "state": False}
    if office["office_type"] in STATE_TYPES:
        model["state"] = True
        names = {r["candidate"] for c in cs for r in c["rows"]}
        model["legislators"] = [p for p in mh.legislators(ed) if any(same_person(p["name"], n) for n in names)]
        cache[office_id] = model
        return model
    races = races_by_office(ed).get(office_id, [])
    rep = mh.reported(ed)
    by_year: OrderedDict = OrderedDict()
    for y in years:
        by_year[y] = {"year": y, "races": [], "empty_races": [], "reported": []}
    for r in races:
        y = r["general_eid"][:4]
        slot = by_year.setdefault(y, {"year": y, "races": [], "empty_races": [], "reported": []})
        (slot["races"] if r["n_with"] else slot["empty_races"]).append(r)
    for c in cs:
        if c["election_id"].endswith("g") and c["contest_id"] in rep:
            y = contest_year(ed, c)
            by_year.setdefault(y, {"year": y, "races": [], "empty_races": [], "reported": []})["reported"] += rep[c["contest_id"]]
    for y in sorted(by_year, reverse=True):
        s = by_year[y]
        if s["races"] or s["reported"]:
            model["cycles"].append(s)
        elif s["empty_races"]:
            model["no_reports"].append(y)
        elif int(y) < POSTED_FROM_YEAR:
            model["not_posted"].append(y)
        else:
            # a posted-era year with a contest but no race in the campaign model (left off the campaign pages)
            model["no_reports"].append(y)
    cache[office_id] = model
    return model


def has_money(ed, office_id: str) -> bool:
    m = money_model(ed, office_id)
    return bool(m["cycles"] or m["legislators"])


# ------------------------------------------------------------------ which tabs

def office_tabs(ed, office_id: str) -> list[str]:
    """The tabs this office has, in TAB_ORDER. Overview and Sources always; Elections when results.csv has a contest
    for it; Money when any money is on record; History when terms.csv has a holder."""
    cache = ed.__dict__.setdefault("_office_tabs", {})
    if office_id in cache:
        return cache[office_id]
    keys = ["overview"]
    if contests(ed, office_id):
        keys.append("elections")
    if has_money(ed, office_id):
        keys.append("money")
    if ed.terms_for(office_id):
        keys.append("history")
    keys.append("sources")
    cache[office_id] = tabs.ordered(keys)
    return cache[office_id]


def crumb(ed, office: dict) -> list:
    """Offices › <government> › <office>: the hub, the government's group on the hub, the office."""
    return [("Offices", HUB), (unit_name(ed, office["unit_id"]), f"{HUB}#g-{office['unit_id']}"),
            (short_title(ed, office), None)]


def office_entries(ed) -> list:
    """Sitemap entries: the hub, then every office's tabs (offices.csv order)."""
    from .sitemap import Entry
    out = [Entry(HUB, "Offices", "Offices",
                 "Every elected office in the county, grouped by government, with who holds it now and the next "
                 "election. Each office has its own page: what it does, every election, the campaign money on "
                 "record and every holder.", "county", GROUP, [])]
    for o in ed.tables["offices"]:
        oid = o["office_id"]
        keys = office_tabs(ed, oid)
        desc = {"overview": f"{o['title']}: what the office does, who holds it, the term and the next election.",
                "elections": f"{o['title']}: every election for the office in the guide's results, general and primary.",
                "money": f"{o['title']}: campaign money on record for each election, by candidate.",
                "history": f"{o['title']}: every holder in the guide's records and how each took office.",
                "sources": f"{o['title']}: every source behind these pages, and what the guide has not found."}
        out += tabs.tab_entries(base(oid), o["title"], desc["overview"], keys, group=GROUP,
                                crumb=crumb(ed, o), tab_descriptions=desc)
    return out


def href(page, office_id: str, tab: str = "overview") -> str | None:
    """Relative link from ``page`` to an office tab, or None when that page is not in this build (an office with no
    such tab, or an office id that is not in offices.csv)."""
    if not office_id or office_id not in page.ed.offices:
        return None
    p = path(office_id, tab)
    return page.rel(p) if p in page.site.by_path else None


def best_tab_href(page, office_id: str, prefer: tuple = ("money", "elections", "overview")) -> str | None:
    for t in prefer:
        u = href(page, office_id, t)
        if u:
            return u
    return None


def office_link(page, office_id: str, tab: str = "overview", text: str | None = None, cls: str = "office-link"):
    """A link from ``page`` to an office's page (or one of its tabs) for cross-links from race cards, holder rows and
    rails; None when that page is not in the build. The default text names the office and the tab."""
    from .html import h
    from .tabs import TAB_LABELS
    u = href(page, office_id, tab)
    if not u:
        return None
    title = page.ed.offices[office_id]["title"]
    if text is None:
        text = f"{title}: office page" if tab == "overview" else f"{title}: {TAB_LABELS[tab].lower()} on the office page"
    return h("a", {"class": cls, "href": u}, text)


# ------------------------------------------------------------------ primary and general (added 2026-11-16, step 2)
# A cycle's filed money is split at the pre-primary report only where the filings themselves draw that line: the
# committee's counted reports up to and including its pre-primary report ("through the pre-primary report", the
# primary period) and the counted reports after it (pre-election, year-end and later). Both parts are sums of whole
# reports chosen by civic/campaign_money.py committee_summary (amendments, duplicates, nested and chained reports are
# already resolved there), so they add up exactly to the whole-cycle figure. Nothing is estimated or apportioned: when
# the reports can't be cut cleanly at the pre-primary report, the committee keeps its whole-cycle figure only and the
# page says why.
PRE_SLOTS = ("earlier", "prior-annual", "pre-primary")
POST_SLOTS = ("pre-election", "year-end", "later")
SPLIT_COLS = (("raised", "receipts_period"), ("spent", "expenditures_period"))


def committee_split(s: dict) -> dict:
    """One committee's cycle (a committee_summary result) cut at its pre-primary report.

    {"ok": True, "pre": {"raised", "spent"}, "post": {...}, "through": ISO date the pre-primary report's period ends,
     "docs": [filing ids of the counted pre-primary reports]}
    or {"ok": False, "why": "..."} (a reason a reader can follow)."""
    from .campaign_money import _pt, cents
    items = s.get("items", [])
    if "overlap" in s.get("flags", set()) or s.get("spent") is None or s.get("raised") is None:
        return {"ok": False, "why": "its reports overlap, so they are not added up at all"}
    pp_all = [it for it in items if it["slot"] == "pre-primary"]
    pp = [it for it in pp_all if it["counted"]]
    if not pp_all:
        return {"ok": False, "why": "no pre-primary report on file"}
    if not pp:
        return {"ok": False, "why": "its pre-primary report's money is included in a later report that covers both "
                                    "periods"}
    if any(it["row"].get("transcription_status") == "unreadable" for it in pp):
        return {"ok": False, "why": "its pre-primary report can't be read"}
    if "date-doubt" in s.get("flags", set()):
        return {"ok": False, "why": "a date on one of its reports may be miswritten, so the guide can't say which "
                                    "side of the primary the report falls on"}
    if any(it["conflict"] for it in items if it["counted"]):
        return {"ok": False, "why": "the dates of two of its reports disagree with their figures or cash"}
    if any(b.get("how") != "periods" for b in s.get("basis", [])):
        return {"ok": False, "why": "its whole-cycle figure uses a year-to-date column, which can't be cut at the "
                                    "pre-primary report"}
    out = {"ok": True, "pre": {}, "post": {}}
    readable = [it for it in items if it["counted"] and it["row"].get("transcription_status") != "unreadable"]
    if any(it["slot"] not in PRE_SLOTS + POST_SLOTS for it in readable):
        return {"ok": False, "why": "one of its counted reports has no place in the cycle"}
    for key, col in SPLIT_COLS:
        pre = sum(cents(it["row"].get(col)) or 0 for it in readable if it["slot"] in PRE_SLOTS)
        post = sum(cents(it["row"].get(col)) or 0 for it in readable if it["slot"] in POST_SLOTS)
        if pre + post != s[key]:
            # cannot happen while every year is a sum of its reports; never show a split that doesn't add up
            return {"ok": False, "why": "its reports don't add up to the whole-cycle figure when cut at the "
                                        "pre-primary report"}
        out["pre"][key], out["post"][key] = pre, post
    out["through"] = max(_pt(it["row"]) for it in pp)
    out["docs"] = [it["row"]["filing_id"] for it in pp]
    return out


def candidate_split(cand: dict) -> dict:
    """committee_split summed over a candidate's committees (a race candidate of campaign_money.build_races): ok only
    when every committee can be cut. {"ok", "pre", "post", "through", "docs"} or {"ok": False, "why", "none": bool}."""
    cs = cand.get("committees") or []
    if not cs:
        return {"ok": False, "why": "no reports on file", "none": True}
    parts = [committee_split(s) for s in cs]
    bad = [(s, p) for s, p in zip(cs, parts) if not p["ok"]]
    if bad:
        s, p = bad[0]
        who = f"{s.get('label', 'its committee')}: " if len(cs) > 1 else ""
        return {"ok": False, "why": who + p["why"], "none": False}
    return {"ok": True,
            "pre": {k: sum(p["pre"][k] for p in parts) for k, _c in SPLIT_COLS},
            "post": {k: sum(p["post"][k] for p in parts) for k, _c in SPLIT_COLS},
            "through": max(p["through"] for p in parts), "docs": [d for p in parts for d in p["docs"]]}


def race_split(race: dict) -> dict:
    """{"any": True when at least one candidate's money can be cut at the pre-primary report, "by": {candidate name:
    candidate_split}, "why": the cycle-level reason when no one's can}."""
    from .campaign_money import NOT_POSTED
    by = {c["name"]: candidate_split(c) for c in race["candidates"]}
    ok = any(v["ok"] for v in by.values())
    why = ""
    if not ok:
        y = race["spec"]["year"]
        if y in NOT_POSTED:
            why = f"the county posted no {y} pre-primary reports"
        elif not any(c.get("committees") for c in race["candidates"]):
            why = "no reports on file"
        else:
            why = ("no candidate's reports can be cut at a pre-primary report ("
                   + "; ".join(sorted({v["why"] for v in by.values() if not v.get("none")})) + ")")
    return {"any": ok, "by": by, "why": why}
