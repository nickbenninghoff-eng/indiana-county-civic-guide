"""Answer-first summary box for place pages (cities, towns, townships) and the county page.

    answer_box(ed, page, unit, offices, links=...)  -> Markup

Four plain answers, each from the guide's data with its citation and status badge, and each linking
to the section below that has the detail:

* Who's in charge: elected seat count, the head office's current holder with a party tag
  (components.name_with_party) and each elected body's party breakdown.
* What it spends: the latest adopted budget (year and basis) and the certified unit tax rate.
* When you vote: the next regular election for the unit's offices (dates computed from the
  state calendar rule) in a `hl-callout`, the looks' "when you vote" treatment.
* How many people live here: the 2020 Census count first, then the latest ACS estimate with its
  margin of error and the low-reliability badge when the CV is above 30%.

Anything missing says "not in the guide's data yet". Nothing is typed in.
"""
from __future__ import annotations

import re

from .components import body_offices, body_state, body_with_breakdown, name_with_party, status_badge, term_party
from .data import fmt_date, fmt_int
from .html import Markup, h
from .layers import _next, election_dates

# The office the box names as the unit's head, by unit type (same choice as the boundary map's panel).
# Towns have no single head: the Town Council is the governing body, so for towns the council breakdown comes
# first and the clerk-treasurer follows under TOWN_CLERK_LABEL (office_types.csv: keeps records, handles money).
HEAD_OFFICE = {"city": "mayor", "town": "town_clerk_treasurer", "township": "township_trustee"}
TOWN_CLERK_LABEL = "Clerk-Treasurer (records and finances)"
BASIS = {"advertised_all_funds": "all advertised funds", "gateway_reported_funds": "funds reported to Gateway",
         "general_fund": "general fund", "all_funds_incl_utilities": "all funds including utilities",
         "dlgf_certified": "as certified by the state"}
BASIS_ORDER = ["advertised_all_funds", "gateway_reported_funds", "general_fund", "all_funds_incl_utilities", "dlgf_certified"]
KIND_WORD = {"county": "county", "city": "city", "town": "town", "township": "township"}
MISSING = "Not in the guide's data yet."


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _vyear(v: str) -> int:
    ys = re.findall(r"\d{4}", v or "")
    return int(ys[-1]) if ys else 0


def _money_big(v: float) -> str:
    if v >= 1e9:
        return f"${v / 1e9:.2f} billion"
    if v >= 1e6:
        return f"${v / 1e6:.2f} million"
    return f"${v:,.0f}"


def latest_budget(ed, uid: str) -> dict | None:
    """Latest adopted budget row for a unit; within that year, the broadest basis first."""
    rows = [r for r in ed.table("budgets") if ed.unit_alias(r["unit_id"]) == uid and r.get("adopted_or_actual") == "adopted"
            and _num(r.get("amount")) is not None and r.get("year", "").isdigit()]
    if not rows:
        return None
    y = max(r["year"] for r in rows)
    rows = [r for r in rows if r["year"] == y]
    rows.sort(key=lambda r: BASIS_ORDER.index(r["basis"]) if r["basis"] in BASIS_ORDER else len(BASIS_ORDER))
    return rows[0]


def place_budget_row(ed, uid: str) -> dict | None:
    """The budget row a place page's At a glance box and Budget section show (and the boundary map's panel):
    the unit's rows with an amount, ordered by year (data order within a year), last adopted one."""
    rows = sorted((r for r in ed.table("budgets") if ed.unit_alias(r["unit_id"]) == uid and r.get("amount")),
                  key=lambda r: r["year"])
    return next((r for r in reversed(rows) if r.get("adopted_or_actual") == "adopted"), None)


def budget_basis_text(row: dict) -> str:
    """Plain name of a budget row's basis, e.g. 'general fund'."""
    return BASIS.get(row["basis"], row["basis"].replace("_", " "))


def latest_unit_rate(ed, uid: str) -> dict | None:
    rows = [r for r in ed.table("tax_rates") if r["rate_kind"] == "certified_unit_rate" and ed.unit_alias(r["unit_id"]) == uid
            and _num(r.get("rate_per_100")) is not None]
    return max(rows, key=lambda r: r["year"]) if rows else None


def population_rows(ed, unit: dict) -> tuple[dict | None, dict | None]:
    """(2020 Census count row, latest ACS pop_total row) for a unit, matched by geography name."""
    t = unit["unit_type"]
    if t == "county":
        fips = str(ed.config.get("fips", ""))
        match = lambda r: r["geo_type"] == "county" and fips and r["geo_id"].endswith(fips)
    else:
        if t == "township":
            want, gtype = re.sub(r" township$", "", unit["name"], flags=re.I).lower() + " township", "county_subdivision"
        else:
            want = re.sub(r"^(city|town) of ", "", unit["name"], flags=re.I).lower() + f" {t}"
            gtype = "town" if t == "town" else "place"
        match = lambda r: r["geo_type"] == gtype and r["geo_name"].lower().startswith(want)
    census, acs = None, None
    for r in ed.table("indicator_values"):
        if not match(r) or _num(r.get("value")) is None:
            continue
        if r["indicator_id"] == "pop_census_2020":
            census = r
        elif r["indicator_id"] == "pop_total" and r["vintage"].startswith("ACS"):
            if acs is None or _vyear(r["vintage"]) > _vyear(acs["vintage"]):
                acs = r
    return census, acs


def _link(page, target: str | None, text: str):
    if not target:
        return None
    return h("p", {"class": "answer-more"}, h("a", {"href": target if target.startswith("#") else page.rel(target)}, text))


def _answer(q: str, big, lines, more, cls: str = "") -> Markup:
    return h("div", {"class": "answer" + (f" {cls}" if cls else "")},
             h("h3", {"class": "answer-q"}, q),
             h("p", {"class": "answer-big"}, big),
             [h("p", {"class": "answer-line"}, ln) for ln in lines if ln],
             more)


def _who(ed, page, unit, offices, link):
    c = page.cites
    elected = [o for o in offices if o.get("elected", "yes") != "no"]
    if not elected:
        return _answer("Who's in charge", "Not in the guide's data yet", [], link)
    n = sum(int(o["seats"]) if (o.get("seats") or "").isdigit() else 1 for o in elected)
    blank = any(not (o.get("seats") or "").isdigit() for o in elected)
    big = f"{'At least ' if blank else ''}{n} elected seat{'s' if n != 1 else ''}"
    lines = []
    is_town = unit["unit_type"] == "town"
    head = HEAD_OFFICE.get(unit["unit_type"])
    if head:
        for o in elected:
            if o["office_type"] != head:
                continue
            terms = ed.current_terms(o["office_id"])
            label = re.sub(r"^.*?(Mayor|Clerk-Treasurer|Trustee)$", r"\1", o["title"].split(",")[0])
            if is_town:
                label = TOWN_CLERK_LABEL
            if terms:
                names = []
                for t in terms:
                    party = term_party(t)
                    names.append(h("span", None, name_with_party(t["person"], party, t.get("confidence") if party else None),
                                   c.cite(t.get("source_ids"))))
                lines.append(h("span", None, f"{label}: ", names))
            else:
                lines.append(f"{label}: current holder not in the guide's data yet.")
            break
    head_lines, lines = lines, []
    for name, offs in body_offices(elected).items():
        terms, seats = body_state(ed, offs)
        gov = "; the town's governing body" if is_town and name == "Town Council" else ""
        if terms:
            lines.append(h("span", None, body_with_breakdown(name, terms, seats),
                           f", {seats} seats" if seats else ", seat count not stated", gov))
        else:
            lines.append(f"{name}{gov}: current holders not in the guide's data yet.")
    # towns: the governing body first, then the clerk-treasurer; cities and townships: the head office first
    lines = lines + head_lines if is_town else head_lines + lines
    if any(o["office_type"] in ("county_commissioner", "county_council_member") for o in elected) or len(lines) > 1:
        lines.append(h("span", {"class": "muted"}, "Party counts are current holders, by party as recorded."))
    return _answer("Who's in charge", big, lines, link)


def _spend(ed, page, unit, link, budget_row=None):
    c = page.cites
    uid = unit["unit_id"]
    b = budget_row or latest_budget(ed, uid)
    r = latest_unit_rate(ed, uid)
    lines = []
    if b:
        big = _money_big(_num(b["amount"]))
        lines.append(h("span", None, f"{b['year']} adopted budget ({BASIS.get(b['basis'], b['basis'].replace('_', ' '))}): "
                                     f"${_num(b['amount']):,.0f}. ", status_badge(b["status"], page), c.cite(b["source_ids"])))
    else:
        big = "Budget not in the guide's data yet"
    word = KIND_WORD.get(unit["unit_type"], "unit")
    if r:
        lines.append(h("span", None, f"Certified {word} tax rate for taxes payable in {r['year']}: "
                                     f"${_num(r['rate_per_100']):.4f} per $100 of assessed value. ",
                       status_badge(r["status"], page), c.cite(r["source_ids"])))
    else:
        lines.append(f"Certified {word} tax rate: not in the guide's data yet.")
    return _answer("What it spends", big, lines, link)


def _vote(ed, page, unit, offices, link):
    c = page.cites
    nxt = _next(ed, [o for o in offices if o.get("elected", "yes") != "no"])
    if not nxt:
        return _answer("When you vote", "Not in the guide's data yet", [], link, "hl-callout")
    y = min(nxt)
    d = election_dates(ed, [y])[str(y)]
    rule_p, rule_g = ed.rules.get("primary_date", {}), ed.rules.get("general_election_date", {})
    src = ";".join(x for x in (rule_p.get("source_ids", ""), rule_g.get("source_ids", "")) if x)
    odd = int(y) % 2 == 1
    kind = "municipal " if odd else ""
    name = re.sub(r"^(City|Town) of ", "", unit["name"])
    lines = [h("span", None, f"Next regular {kind}general election for {name}'s offices: {', '.join(nxt[y])}. "
                             f"{'Municipal primary' if odd else 'Primary'}: {fmt_date(d['primary'])}. ",
               status_badge("computed", page, "Dates computed from the state calendar rule (first Tuesday after the first Monday)."),
               c.cite(src))]
    return _answer("When you vote", fmt_date(d["general"]), lines, link, "hl-callout")


def _people(ed, page, unit, link):
    c = page.cites
    census, acs = population_rows(ed, unit)
    lines = []
    big = None
    if census:
        big = fmt_int(census["value"])
        lines.append(h("span", None, "2020 Census count. ", status_badge(census["status"], page), c.cite(census["source_ids"])))
    if acs:
        v, moe = _num(acs["value"]), _num(acs.get("moe"))
        cv = (moe / 1.645 / v * 100) if (v and moe) else None
        flags = [status_badge(acs["status"], page)]
        if cv is not None and cv > 30:
            flags.append(" ")
            flags.append(status_badge("low", page, f"CV {cv:.0f}% (above 30%): treat as unreliable."))
        est = (f"≈ {fmt_int(v)} (±{fmt_int(moe)})" if moe else f"≈ {fmt_int(v)} (no margin of error published)")
        lines.append(h("span", None, f"{acs['vintage']} estimate: {est}. ", flags, c.cite(acs["source_ids"])))
        if big is None:
            big = f"≈ {fmt_int(v)}"
    if big is None:
        return _answer("How many people live here", "Not in the guide's data yet", [], link)
    return _answer("How many people live here", big, lines, link)


def answer_box(ed, page, unit: dict, offices: list[dict], links: dict | None = None, mark_here: bool = True,
               budget_row: dict | None = None) -> Markup:
    """The four-answer box. ``links`` maps who/spend/vote/people to an in-page '#id' or a site path, or a
    (target, text) pair (None = no link). ``mark_here`` adds data-here-unit so static/js/here.js can mark
    the reader's place. ``budget_row`` overrides the budget shown, so the box matches a page's own budget
    section."""
    links = links or {}
    lk = {"who": "Who holds office now", "spend": "Budget details", "vote": "Every office and its next election",
          "people": "More about who lives here"}
    texts = {k: (v[1] if isinstance(v, tuple) else lk[k]) for k, v in links.items() if v}
    targets = {k: (v[0] if isinstance(v, tuple) else v) for k, v in links.items() if v}
    ln = {k: _link(page, targets.get(k), texts.get(k, lk[k])) for k in lk}
    return h("section", {"class": "answers", "id": "glance", "aria-labelledby": "glance-h",
                         "data-here-unit": unit["unit_id"] if mark_here else None},
             h("h2", {"class": "answers-h", "id": "glance-h"}, "At a glance"),
             h("div", {"class": "answer-grid"},
               _who(ed, page, unit, offices, ln["who"]),
               _spend(ed, page, unit, ln["spend"], budget_row),
               _vote(ed, page, unit, offices, ln["vote"]),
               _people(ed, page, unit, ln["people"])))
