"""Office pages and the Offices hub (phase 6 step 1, 2026-11-16; planning/design-direction-2026-11-16.md).

    offices/index.html                       every office, grouped by government, with its holder and next election
    offices/<office_id>/index.html           Overview: what it does, who holds it, term, seats, next election, how
                                             it is filled, how to run, its government
    offices/<office_id>/elections/           every contest for the office in results.csv, general and primary,
                                             newest first, each a compact result with margin and status
    offices/<office_id>/money/               campaign money by election: raised and spent per candidate on one
                                             scale, primary and general in separate labelled groups, then the table
    offices/<office_id>/history/             every holder in terms.csv and how each took office
    offices/<office_id>/sources/             the sources and gaps for the whole office

The tabs are civic/tabs.py's template; which ones an office has comes from civic/offices.py office_tabs (the sitemap
reads the same). No figure is computed here: results are the rows of results.csv through Edition.contests; campaign
money is the race model of the campaign pages (pages/campaigns.py cf_all: the same sums as the race cards on
money/campaigns/<area>/), the news-reported figures are money_history.reported() rows, state legislators' sums are
money_history.legislator_years(). Rules carried over: people in ballot order (results) or file order, never ranked by
money or party; party colors only in results bars; money charts use the accent and ink marks.
"""
from __future__ import annotations

import re
from collections import OrderedDict
from functools import partial
from pathlib import Path

from civic import campaign_money as cm
from civic import offices as om
from civic import tabs as T
from civic.charts import money_rows, period_money
from civic.components import (STATUS, data_table, name_with_party, party_breakdown, party_breakdown_text, party_label,
                              see_all_fold,
                              table_filter, term_party)
from civic.components import FIGURE_MARKS, figure_mark, scope_attrs, scope_mark, scope_note
from civic.data import SELECTED_BY_LABELS, fmt_date, parse_date, split_ids
from civic.holder_rows import NO_HOLDER
from civic.html import Markup, h, join, json_script
from civic.related import RUN_FOR_TYPE, RUN_INDEX, RUN_LABEL, contest_href, related_items

from . import money_history as mh

KIND_WORD = {"county": "County", "court_system": "Courts", "city": "City", "town": "Town", "township": "Township",
             "school_corporation": "School corporation", "state_chamber": "State legislature",
             "state": "Statewide", "federal_chamber": "Federal"}
# office types with no Run for office page in the guide (its run pages are for local office; 2026-11-18)
NON_LOCAL_TYPES = ("us_representative", "us_senator", "governor", "attorney_general", "secretary_of_state",
                   "state_treasurer", "superintendent_public_instruction", "supreme_court_justice",
                   "court_of_appeals_judge", "tax_court_judge")
PARTY_WORD = {"D": "Democratic", "R": "Republican", "L": "Libertarian", "G": "Green"}


# =========================================================================== small helpers

def _src(*groups) -> str:
    """Source ids of rows (or id strings), first-use order, no repeats."""
    out = []
    for g in groups:
        for x in (g if isinstance(g, list) else [g]):
            ids = split_ids(x.get("source_ids")) if isinstance(x, dict) else split_ids(x)
            out += [i for i in ids if i not in out]
    return ";".join(out)


def _mark(page, status, note=None):
    return T.status_mark(status, page, note, sources_href=_marks_href(page))


def _marks_href(page) -> str | None:
    base = page.entry.thing if page.entry is not None else ""
    if not base:
        return None
    return "#marks" if page.entry.tab == "sources" else page.rel(T.tab_path(base, "sources")) + "#marks"


def _seats(office) -> int | None:
    try:
        return int(office.get("seats") or "")
    except ValueError:
        return None


def _how_filled(ed, office) -> str:
    """How the seat is filled, in words, from offices.csv (elected, partisan, district)."""
    if office.get("elected") == "no":
        return "Appointed, not elected"
    if om.level(ed, office) in ("statewide", "federal"):
        if office["office_type"] == "us_representative":
            who = f"Elected by the voters of District {office.get('district') or '(not stated)'}"
        elif office.get("partisan") == "no":
            return "A yes-or-no retention vote, statewide (or by appellate district, as each ballot line says)"
        else:
            who = "Elected statewide"
        return who + (", on a party ballot" if office.get("partisan") == "yes" else "")
    d = (office.get("district") or "").strip()
    unit = ed.units.get(office["unit_id"]) or {}
    if office["office_type"] in om.STATE_TYPES:
        who = f"voters of District {d}" if d else "voters of the district"
    elif re.fullmatch(r"\d+|[A-I]", d):
        who = f"voters of District {d}"
    elif d.lower().startswith("ward"):
        who = f"voters of {d}"
    elif d and d.lower() != "at-large":
        who = f"voters of {d}"
    else:
        name = om.unit_name(ed, office["unit_id"])
        the = "the " if re.match(r"(City|Town|School City) of ", name) else ""
        who = f"all voters of {the}{name}" if unit else "all voters"
    ballot = {"yes": "on a party ballot", "no": "on a nonpartisan ballot"}.get(office.get("partisan"), "")
    return f"Elected by {who}" + (f", {ballot}" if ballot else "")


def _holders_line(ed, office, current) -> Markup | str:
    if not current:
        return NO_HOLDER
    n = _seats(office) or len(current)
    if len(current) == 1 and n <= 1:
        t = current[0]
        return h("span", None, "Held by ",
                 name_with_party(t["person"], term_party(t), t.get("confidence") if term_party(t) else None))
    return f"{n} seats {party_breakdown_text(current, n)}"


def _run_page(office) -> tuple[str, str] | None:
    if office.get("elected") == "no" or office["office_type"] in NON_LOCAL_TYPES:
        return None
    slug = RUN_FOR_TYPE.get(office["office_type"])
    if slug:
        return f"run/{slug}/index.html", f"Run for {RUN_LABEL[slug]}"
    if office["office_type"] in om.STATE_TYPES:
        return RUN_INDEX, "How to run for office"
    return RUN_INDEX, "How to run for local office"


def head_for(ed, office) -> T.Head:
    current = ed.current_terms(office["office_id"])
    facts = [om.unit_name(ed, office["unit_id"]), _holders_line(ed, office, current)]
    if office.get("term_years"):
        facts.append(f"{office['term_years']}-year term")
    facts.append(f"Next election {office['next_election']}" if office.get("next_election")
                 else "Next election not in the guide's data")
    return T.Head(kind="Office", title=office["title"], facts=facts)


def _election_words(ed, c) -> str:
    """'General election, Nov 7, 2023' / 'Democratic primary, May 2, 2023'."""
    el = ed.elections.get(c["election_id"]) or {}
    when = fmt_date(el.get("date")) or c["election_id"][:4]
    p = (c.get("party_primary") or "").strip()
    if p:
        return f"{PARTY_WORD.get(p, party_label(p))} primary, {when}"
    t = el.get("type", "")
    if t == "special":
        return f"Special election, {when}"
    return f"General election, {when}"


# =========================================================================== Overview

def _overview(ed, office, page):
    c = page.cites
    oid = office["office_id"]
    ot = ed.office_type_row(office) or {}
    current, incoming = ed.current_terms(oid), ed.incoming_terms(oid)
    out = []

    # who holds it now
    rows = []
    for t in current:
        how = SELECTED_BY_LABELS.get(t.get("first_selected_by", ""), t.get("first_selected_by"))
        rows.append(h("li", {"class": "ovw-holder"},
                      h("span", {"class": "ovw-name"},
                        name_with_party(t["person"], term_party(t), t.get("confidence") if term_party(t) else None)),
                      c.cite(t.get("source_ids")),
                      h("span", {"class": "ovw-meta"}, f"In office since {fmt_date(t['start']) or 'a date not in sources'}"
                                                      f"; first chosen by {how}", " ", _mark(page, t.get("status")))))
    for t in incoming:
        rows.append(h("li", {"class": "ovw-holder ovw-incoming"},
                      h("span", {"class": "ovw-name"}, "Incoming: ",
                        name_with_party(t["person"], term_party(t), t.get("confidence") if term_party(t) else None)),
                      c.cite(t.get("source_ids")),
                      h("span", {"class": "ovw-meta"}, f"Takes office {fmt_date(t['start'])}", " ", _mark(page, t.get("status")))))
    if not rows:
        rows.append(h("li", {"class": "ovw-holder"}, NO_HOLDER + "."))
    out.append(T.tab_section("holder", "Who holds it now", h("ul", {"class": "ovw-holders"}, rows)))

    # what the office does
    does = []
    if ot.get("what_it_does"):
        does.append(h("p", None, ot["what_it_does"], c.cite(ot.get("source_ids"))))
    else:
        does.append(h("p", {"class": "muted"}, "A description of this office is not yet in the guide's data."))
    if ot.get("term_limit"):
        does.append(h("p", None, h("strong", None, "Term limit: "), ot["term_limit"], c.cite(ot.get("source_ids"))))
    if ot.get("vacancy_rule"):
        does.append(h("p", None, h("strong", None, "If the seat falls vacant: "), ot["vacancy_rule"],
                      c.cite(ot.get("source_ids"))))
    out.append(T.tab_section("does", "What the office does", does))

    # the facts
    gov = om.government_page(ed, office["unit_id"])
    gov_cell = (h("a", {"href": page.rel(gov[0])}, om.unit_name(ed, office["unit_id"]))
                if gov and gov[0].split("#")[0] in page.site.by_path else om.unit_name(ed, office["unit_id"]))
    seats = _seats(office)
    facts = [("Government", gov_cell),
             ("Seats", str(seats) if seats else "Not stated in sources"),
             ("Term", f"{office['term_years']} years" if office.get("term_years") else "Not stated in sources"),
             ("Next regular election", office.get("next_election") or "Not in the guide's data"),
             ("How it is filled", _how_filled(ed, office))]
    cov = om.office_coverage(ed, office)
    if cov:
        facts.append(("Who votes here", cov))
    if office.get("district") and office["district"].lower() != "at-large":
        facts.insert(1, ("District", office["district"]))
    dl = h("dl", {"class": "ovw-facts"},
           [[h("dt", None, k), h("dd", None, v)] for k, v in facts])
    out.append(T.tab_section("facts", "The office in brief", dl,
                             h("p", {"class": "ovw-src"}, "From the guide's list of offices ", _mark(page, office["status"]),
                               c.cite(office.get("source_ids")))))

    # where to go next
    links = []
    run = _run_page(office)
    if run and run[0] in page.site.by_path:
        links.append(h("li", None, h("a", {"href": page.rel(run[0])}, run[1])))
    if gov and gov[0].split("#")[0] in page.site.by_path:
        links.append(h("li", None, h("a", {"href": page.rel(gov[0])}, f"{gov[1]}: the government's page")))
    for i in related_items(page, office_id=oid):
        if i.key in ("place",):
            continue
        txt = i.text if i.text.lower().startswith(i.topic.split()[0].lower()) else f"{i.topic}: {i.text}"
        links.append(h("li", None, h("a", {"href": i.href}, txt)))
    if links:
        out.append(T.tab_section("next", "Elsewhere in the guide", h("ul", {"class": "ovw-links"}, links)))

    if office.get("notes"):
        out.append(h("details", {"class": "ovw-notes", "id": "notes-records"},
                     h("summary", None, "Notes from the records"),
                     h("p", None, office["notes"], c.cite(office.get("source_ids")))))
    page.add(*out)


# =========================================================================== Elections

def _result_text(c, ed=None) -> Markup:
    from .elections import candidates, is_question
    from civic import overall as OV
    if ed is not None:
        words = OV.result_words(ed, c)   # a multi-county contest: the overall result (2026-11-18)
        if words is not None:
            return h("span", None, words)
    cands = candidates(c)
    q = is_question(c)
    wins = [x for x in cands if x["winner"] == "Y"]
    if q:
        bits = [f"{x['name']} {x['pct']:.1f}%" for x in cands if x["pct"] is not None]
        return h("span", None, "; ".join(bits) or "votes not recorded")
    if not wins:
        return h("span", {"class": "muted"}, "Winner not recorded in the guide's data")
    out = []
    for x in wins:
        share = f" {x['pct']:.1f}%" if x["pct"] is not None else ""
        out.append(h("span", {"class": "er-win"}, name_with_party(x["name"], x["party"]), share))
    return join(out, ", ")


def _margin_text(c, ed=None) -> str:
    from .elections import is_question, margin
    from civic import overall as OV
    if is_question(c):
        return "Retention or public question"
    if ed is not None:
        words = OV.margin_words(ed, c)
        if words is not None:
            return words
    m = margin(c)
    if m is None:
        return "Uncontested"
    if "reason" in m:
        return f"Margin not measured ({m['reason']})"
    if m["tie"]:
        return "Tied on votes"
    return f"Margin {m['pts']:.1f} points"


def _contest_figure(ed, page, c, question: bool = False):
    """One contest's result as charts.results_rows (HTML bars across the content width). The figures, status and
    notes are prepared exactly as pages/county.py _contest_figure prepares them for results_bars (that module
    belongs to the government pages; this copy only changes the drawing), so the two never disagree on a number."""
    from civic.charts import results_rows
    from civic import overall as OV
    rows = c["rows"]
    status = rows[0]["status"] if len({r["status"] for r in rows}) == 1 else "from_scan" if any(
        r["status"] == "from_scan" for r in rows) else rows[0]["status"]
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
    # a multi-county contest (2026-11-18, civic/overall.py): "St. Joseph County portion" in the title; the overall
    # winner is in the county-vs-overall table that follows, never on the county bars
    clear = OV.clear_county_winner(ed, c)
    if clear:
        for x in cands:
            x["winner"] = ""
    notes = []
    if len(rows) == 1 and not is_q:
        notes.append("Uncontested.")
    if all(r["winner"] == "" for r in rows) and not is_q and not clear:
        notes.append("Winner not recorded in the guide's data.")
    if low:
        notes.append("Some figures are low confidence.")
    sub = f"Vote for {c['vote_for']}" if c.get("vote_for") and c["vote_for"] != "1" else None
    return OV.with_overall(page, c, results_rows(
        "res-" + c["contest_id"], OV.figure_title(ed, c), cands, subtitle=sub, status=status,
        note=" ".join(notes) or None, page=page, question=is_q,
        cite=page.cites.cite(";".join(dict.fromkeys(s for r in rows for s in split_ids(r["source_ids"]))))))


def _year_scope(statuses: set, n: int) -> str:
    """The one exception status every contest of a year shares, said once at the top of the year (2026-11-18): always
    for unofficial results (they are labelled in words at the top of their section), else when two or more share it."""
    if len(statuses) != 1:
        return ""
    st = next(iter(statuses))
    return st if st in FIGURE_MARKS and (st == "unofficial" or n > 1) else ""


def year_head(statuses: set, n: int, y) -> tuple[str, object]:
    """(scope status, caption line) for a year of contests (2026-11-18, "About these figures"). When every contest
    shares one exception status the line says it once (``scope_note``) and the contests carry no mark. When only some
    are unofficial, the line still says "Unofficial" in words at the top of the year, and those contests keep their
    mark."""
    st = _year_scope(statuses, n)
    if st:
        return st, scope_note(st, f"count for {y}")
    if "unofficial" in statuses:
        return "", h("p", {"class": "fscope-line fscope-unofficial"},
                     h("strong", None, "Unofficial"), figure_mark("unofficial", scope=True),
                     ": the counts marked so are not final yet (election-night figures, or a count that awaits a "
                     "recount window, another county's figures or state certification); they may change.")
    return "", None


def _elections(ed, office, page):
    from .elections import contest_status
    oid = office["office_id"]
    cs = om.contests(ed, oid)
    by_year: OrderedDict = OrderedDict()
    for c in cs:
        by_year.setdefault(om.contest_year(ed, c), []).append(c)
    years = list(by_year)
    span = years[0] if len(years) == 1 else f"{years[-1]} to {years[0]}"
    n_p = sum(1 for c in cs if c["party_primary"])
    intro = h("p", {"class": "tsec-lead"},
              f"{len(cs)} contest{'s' if len(cs) != 1 else ''} in the guide's results, {span}"
              + (f", {n_p} of them party primaries" if n_p else "") + ". Newest first; candidates in the order the "
              "source lists them (see Sources). The newest election's results are drawn; select any other row for "
              "its chart.")
    page.add(intro)
    first = True
    for y, ycs in by_year.items():
        items = []
        yscope, yline = year_head({contest_status(c["rows"]) for c in ycs}, len(ycs), y)
        for c in ycs:
            st = contest_status(c["rows"])
            ex = contest_href(page, c["contest_id"])
            fig = _contest_figure(ed, page, c)
            def cells(link=True, c=c, st=st):
                return [h("h3", {"class": "er-what"}, _election_words(ed, c)),
                        h("span", {"class": "er-result"}, _result_text(c, ed), scope_mark(st, link=link)),
                        h("span", {"class": "er-margin"}, _margin_text(c, ed))]
            more = h("p", {"class": "er-more"}, h("a", {"href": ex}, "This contest in the results explorer")) if ex else None
            # the line's mark speaks for the contest's chart and table too (scope_attrs on the item), so a contest
            # is marked once (2026-11-18, "About these figures")
            if first:
                body = [h("div", {"class": "er-line"}, cells()), fig, more]
            else:
                # the row itself is the fold's summary (no link inside it: the mark is a plain span with its title)
                # ships open (JS off: every result on the page, as the site's other folds); static/js/folds.js
                # closes it on load and reopens it when a link targets the contest
                body = [h("details", {"class": "er-fold", "open": True, "data-fold": "contest"},
                          h("summary", {"class": "er-line"}, cells(link=False),
                            h("span", {"class": "er-toggle"}, "Chart")),
                          fig, more)]
            items.append(h("li", {"class": "er-item", "id": f"c-{c['contest_id']}", **scope_attrs(st)}, body))
        page.add(h("section", {"class": "tsec er-year", "id": f"y{y}", "aria-labelledby": f"y{y}-h",
                               **scope_attrs(yscope)},
                   h("h2", {"class": "tsec-h", "id": f"y{y}-h"}, y),
                   yline,
                   h("ul", {"class": "er-list"}, items)))
        first = False
    if office.get("district") and office["district"].lower() != "at-large":
        page.add(h("p", {"class": "tnote"}, "District lines are redrawn after each census, so an older race under the "
                                             "same district name may have covered a different area."))


# =========================================================================== Money

def _usd_whole(cents: int | None) -> str:
    """Dollars as money_history writes a news figure: whole dollars without cents."""
    if cents is None:
        return "not on file"
    return cm.usd(cents)[:-3] if cents % 100 == 0 else cm.usd(cents)


def _cand_sub(c: dict) -> str:
    p = (c.get("party") or "").strip()
    return party_label(p) if p else "Party not recorded"


def _filing_money_text(cand: dict, key: str) -> str:
    if not cand["committees"]:
        return "no reports on file"
    if cand[key] is None:
        return "not added up (overlapping reports)"
    return cm.usd(cand[key])


def _race_groups(ed, race) -> list[tuple[str, list[dict]]]:
    """The race's candidates in labelled groups, ballot order kept within each: the general-election ballot, each
    party's primary-only candidates, and committees that filed for the office with no ballot line."""
    groups: OrderedDict = OrderedDict()
    for cand in race["candidates"]:
        if cand["ballot"] == "general":
            key = ("general", "")
        elif cand["ballot"] == "primary":
            parties = {(ed.contests.get(cid) or {}).get("party_primary", "") for cid in cand["contests"]}
            parties.discard("")
            key = ("primary", sorted(parties)[0] if parties else cand.get("party", ""))
        else:
            key = ("none", "")
        groups.setdefault(key, []).append(cand)
    out = []
    order = sorted(groups, key=lambda k: ({"general": 0, "primary": 1, "none": 2}[k[0]], k[1]))
    for k in order:
        if k[0] == "general":
            label = "General-election candidates"
        elif k[0] == "primary":
            label = f"Lost in the {PARTY_WORD.get(k[1], party_label(k[1]) if k[1] else 'party')} primary"
        else:
            label = "Filed for this office, not on the ballot"
        out.append((label, groups[k]))
    return out


def _reported_groups(rows_by_contest) -> list[tuple[dict, OrderedDict]]:
    """[(contest, {candidate: [rows]})], the general election first, then primaries by party."""
    out = []
    for contest, rows in rows_by_contest:
        by: OrderedDict = OrderedDict()
        for r in rows:
            by.setdefault(r["candidate"], []).append(r)
        out.append((contest, by))
    out.sort(key=lambda x: (1 if x[0]["party_primary"] else 0, x[0]["party_primary"] or ""))
    return out


def _fig(rs, figure):
    """(cents, wording) for one figure of one candidate in the news rows; wording is the source's own when rounded."""
    r = next((x for x in rs if x["figure"] == figure), None)
    if r is None:
        return None, None, None
    cents = cm.cents(r["amount"])
    return cents, (r.get("as_reported") or _usd_whole(cents)), r


def money_scale(ed, model) -> int:
    """The largest raised or spent figure (cents) plotted anywhere on the office's Money tab: the shared scale."""
    vals = []
    for cyc in model["cycles"]:
        for race in cyc["races"]:
            for cand in race["candidates"]:
                vals += [cand[k] for k in ("raised", "spent") if cand["committees"] and cand.get(k) is not None]
        for _contest, rows in cyc["reported"]:
            vals += [cm.cents(r["amount"]) for r in rows if r["figure"] in ("raised", "spent") and cm.cents(r["amount"])]
    return max([v for v in vals if v] or [100])


def _pkey(party: str) -> str:
    """The party filter's key for a row: the party code, or "none" when no party is recorded."""
    p = (party or "").strip()
    return p if p else "none"


def _span_dates(isos) -> str:
    ds = sorted({d for d in isos if d})
    if not ds:
        return ""
    if len(ds) == 1:
        return f"period ending {fmt_date(ds[0])}"
    return f"periods ending {fmt_date(ds[0])} to {fmt_date(ds[-1])}"


def _primary_parties(ed, cand) -> list[str]:
    ps = {(ed.contests.get(cid) or {}).get("party_primary", "") for cid in cand.get("contests", [])}
    ps.discard("")
    return sorted(ps)


def _split_groups(ed, race, phase: str) -> list[tuple[str, list[dict]]]:
    """The race's candidates for one side of the split, ballot order kept within each group.
    primary: each party's primary candidates, then those on no primary ballot; general: as the whole-cycle groups."""
    if phase == "general":
        return _race_groups(ed, race)
    groups: OrderedDict = OrderedDict()
    for cand in race["candidates"]:
        ps = _primary_parties(ed, cand) if cand["ballot"] in ("general", "primary") else []
        key = ps[0] if ps else ("~none" if cand["ballot"] == "none" else "~general")
        groups.setdefault(key, []).append(cand)
    out = []
    for k in sorted(groups, key=lambda k: (k.startswith("~"), k)):
        label = {"~general": "General-election candidates with no primary contest",
                 "~none": "Filed for this office, not on the ballot"}.get(k)             or f"{PARTY_WORD.get(k, party_label(k))} primary candidates"
        out.append((label, groups[k]))
    return out


def money_controls(parties: list[str]) -> Markup:
    """The Money tab's two neutral controls (static/js/offices.js): Both / Primary / General, and a party filter
    (All parties, then each party on the page by code, then "Party not recorded"). Shipped hidden: with JavaScript off
    every chart shows. No party colors: plain buttons and a select."""
    opts = [h("option", {"value": ""}, "All parties")]
    for p in sorted([p for p in parties if p != "none"]):
        opts.append(h("option", {"value": p}, party_label(p)))
    if "none" in parties:
        opts.append(h("option", {"value": "none"}, "Party not recorded"))
    seg = [h("button", {"type": "button", "class": "mt-seg-b", "data-mt-show": k,
                        "aria-pressed": "true" if k == "both" else "false"}, lab)
           for k, lab in (("both", "Both"), ("primary", "Primary"), ("general", "General"))]
    return h("div", {"class": "mt-ctl", "id": "mt-ctl", "hidden": True, "role": "group",
                     "aria-label": "Choose which money to show"},
             h("div", {"class": "mt-ctl-f"},
               h("span", {"class": "mt-ctl-l", "id": "mt-show-l"}, "Election"),
               h("div", {"class": "mt-seg", "role": "group", "aria-labelledby": "mt-show-l"}, seg)),
             h("div", {"class": "mt-ctl-f"},
               h("label", {"class": "mt-ctl-l", "for": "mt-party"}, "Party"),
               h("select", {"id": "mt-party", "class": "mt-party"}, opts)),
             h("p", {"class": "mt-ctl-state", "id": "mt-ctl-state", "aria-live": "polite"}))


def _money(ed, office, page):
    c = page.cites
    oid = office["office_id"]
    model = om.money_model(ed, oid)
    if model["state"]:
        return _money_state(ed, office, page, model)
    vmax = money_scale(ed, model)
    parties: set = set()
    page.add(h("div", {"class": "mt-key"},
               h("ul", {"class": "legend"},
                 h("li", None, h("span", {"class": "key key-rect m-accent", "aria-hidden": "true"}), "Raised"),
                 h("li", None, h("span", {"class": "key key-rect m-spent", "aria-hidden": "true"}), "Spent")),
               h("p", {"class": "tsec-lead"},
                 "One scale for every election on this page, so years compare. From 2023 on, the figures are the "
                 "guide's sums of the reports the county posts; earlier figures are as news coverage reported them. "
                 "Candidates are in ballot order.")))
    controls_at = len(page.parts)
    table = []

    def row(cand, raised, spent, rtext, stext, tip):
        parties.add(_pkey(cand.get("party")))
        return {"name": cand["name"], "sub": _cand_sub(cand), "raised": raised, "spent": spent,
                "raised_text": rtext, "spent_text": stext, "tip": tip,
                "attrs": {"data-party": _pkey(cand.get("party"))}}

    for cyc in model["cycles"]:
        y = cyc["year"]
        parts = []
        phases: set = set()
        whys = []
        for race in cyc["races"]:
            spec = race["spec"]
            split = om.race_split(race)
            parts.append(h("p", {"class": "mt-total", "data-mt-phase": "whole"},
                           h("strong", None, "All candidates, whole cycle: "),
                           h("span", {"class": "mt-total-figs", "data-race": race["id"]},
                             f"{cm.usd(race['spent'])} spent, {cm.usd(race['raised'])} raised"),
                           # 2026-11-18 ("About these figures"): an incomplete total is marked * right after the
                           # figures (the note at the bottom says it is a floor); a complete one, the normal case,
                           # carries no sentence
                           None if race["complete"] else figure_mark("incomplete"),
                           _mark(page, "computed", "Sums of the reports on file, by the rules on How campaign finance "
                                                   "reporting works."),
                           (f", reports through {fmt_date(race['latest_to'])}" if race["latest_to"] else ""), ".",
                           c.cite("CFM-010")))
            phases.add("whole")
            for gi, (label, cands) in enumerate(_race_groups(ed, race)):
                rows = []
                for cand in cands:
                    rows.append(row(cand, cand["raised"] if cand["committees"] else None,
                                    cand["spent"] if cand["committees"] else None,
                                    _filing_money_text(cand, "raised"), _filing_money_text(cand, "spent"),
                                    f"{cand['name']}, {spec['cycle']} cycle"))
                    table.append([y, f"{label}, whole cycle", cand["name"], _cand_sub(cand),
                                  _filing_money_text(cand, "raised"), _filing_money_text(cand, "spent"),
                                  cm.usd(cand["cash"]) if cand.get("cash") is not None else "",
                                  "Sum of the reports on file", "Computed"])
                parts.append(money_rows(f"mt-{race['id']}-{gi}", label, rows, vmax=vmax,
                                        subtitle=f"Whole {spec['cycle']} cycle: each committee's reports, primary and "
                                                 "general together", page=page,
                                        extra={"data-mt-phase": "whole"}))
            if split["any"]:
                parts.append(h("p", {"class": "mt-split-hint", "data-mt-hint": True, "data-mt-phase": "whole"},
                               "These filings can also be split at each committee's pre-primary report: the charts "
                               "headed “through the pre-primary report” and “after the pre-primary "
                               "report” show the two parts. Each part is a sum of whole reports; nothing is "
                               "estimated."))
                for phase in ("primary", "general"):
                    phases.add(phase)
                    unsplit = []
                    for gi, (label, cands) in enumerate(_split_groups(ed, race, phase)):
                        if not any(split["by"][x["name"]]["ok"] for x in cands):
                            # no one in this group can be split: no empty chart, just the line below
                            unsplit += [f"{x['name']} ({split['by'][x['name']]['why']})" for x in cands]
                            continue
                        rows, cant, throughs = [], [], []
                        for cand in cands:
                            sp = split["by"][cand["name"]]
                            if sp["ok"]:
                                part = sp["pre" if phase == "primary" else "post"]
                                throughs.append(sp["through"])
                                rows.append(row(cand, part["raised"], part["spent"], cm.usd(part["raised"]),
                                                cm.usd(part["spent"]), f"{cand['name']}, {spec['cycle']} cycle"))
                                basis = ("Reports through the pre-primary report (" + _span_dates([sp["through"]]) + ")"
                                         if phase == "primary" else "Reports after the pre-primary report")
                                table.append([y, label + (", through the pre-primary report" if phase == "primary"
                                                          else ", after the pre-primary report"),
                                              cand["name"], _cand_sub(cand), cm.usd(part["raised"]),
                                              cm.usd(part["spent"]), "", basis, "Computed"])
                            elif sp.get("none"):
                                rows.append(row(cand, None, None, "no reports on file", "no reports on file",
                                                cand["name"]))
                            else:
                                rows.append(row(cand, None, None, "can't be split", "can't be split", cand["name"]))
                                cant.append(f"{cand['name']} ({sp['why']})")
                        if phase == "primary":
                            title = f"{label}: through the pre-primary report"
                            sub = (f"From the start of the {spec['cycle']} cycle through each committee's pre-primary "
                                   f"report ({_span_dates(throughs) or 'none on file'}), before the "
                                   f"{fmt_date(spec['primary'].isoformat())} primary")
                        else:
                            title = f"{label}: after the pre-primary report"
                            sub = (f"The {spec['cycle']} cycle's reports after each committee's pre-primary report "
                                   "(pre-election, annual and later reports), through "
                                   + (fmt_date(race["latest_to"]) if race["latest_to"] else "the latest report on file"))
                        note = ("Can't be split, so shown only in the whole-cycle chart: " + "; ".join(cant) + ".") \
                            if cant else None
                        parts.append(money_rows(f"mt-{race['id']}-{phase[0]}{gi}", title, rows, vmax=vmax,
                                                subtitle=sub, note=note, page=page,
                                                extra={"data-mt-phase": phase, "data-mt-split": "1"}))
                    if unsplit:
                        parts.append(h("p", {"class": "mt-nosplit", "data-mt-phase": phase, "data-mt-split": "1"},
                                       "Not split, so only in the whole-cycle chart: " + "; ".join(unsplit) + "."))
            else:
                whys.append(split["why"])
                parts.append(h("p", {"class": "mt-nosplit"},
                               "Not split into primary and general: " + split["why"] + "."))
            area = cm.area_path(race["area"])
            links = []
            if area in page.site.by_path:
                links.append(h("a", {"href": page.rel(area) + f"#r-{race['id']}"},
                               "Every report behind these figures (the race card)"))
            for cand in race["candidates"]:
                for s in cand["committees"]:
                    lk = mh.link(ed, page, s["key"], f"{s['label']}, money history")
                    if lk:
                        links.append(lk)
            if links:
                parts.append(h("p", {"class": "mt-links"}, join(links, " · ")))
        for contest, by in _reported_groups(cyc["reported"]):
            phase = "primary" if contest["party_primary"] else "general"
            phases.add(phase)
            which = (f"{PARTY_WORD.get(contest['party_primary'], 'Party')} primary" if contest["party_primary"]
                     else "General election")
            rows, statuses, srcs = [], [], []
            for cand, rs in by.items():
                rc, rw, rr = _fig(rs, "raised")
                sc, sw, sr = _fig(rs, "spent")
                cc, cw, _cr = _fig(rs, "cash on hand")
                no = next((x for x in rs if x["figure"] == "no report"), None)
                party = rs[0]["party"]
                sub = party_label(party) if party else "Party not recorded"
                parties.add(_pkey(party))
                rows.append({"name": cand, "sub": sub, "raised": rc, "spent": sc,
                             "raised_text": rw or ("did not file a report (per the article)" if no else "not reported"),
                             "spent_text": sw or ("did not file a report (per the article)" if no else "not reported"),
                             "tip": f"{cand}: {(rr or sr or no or rs[0])['covers']}",
                             "attrs": {"data-party": _pkey(party)}})
                statuses += [x["status"] for x in rs]
                srcs += [x for x in rs]
                covers = "; ".join(dict.fromkeys(x["covers"] for x in rs if x["figure"] != "cash on hand"))
                notes = "; ".join(dict.fromkeys(x["notes"].rstrip(".") for x in rs if x.get("notes")))
                table.append([y, f"{which} (news report)", cand, sub, rw or ("no report" if no else "not reported"),
                              sw or ("no report" if no else "not reported"), cw or "",
                              "As reported: " + covers + (f" ({notes})" if notes else ""),
                              STATUS.get(rs[0]["status"], (rs[0]["status"],))[0].capitalize()])
            st = statuses[0] if len(set(statuses)) == 1 else "single_source" if "single_source" in statuses else statuses[0]
            rounded = [f"{cand} ({x['figure']}: {x['as_reported']})" for cand, rs in by.items() for x in rs
                       if x.get("as_reported") and x["figure"] in ("raised", "spent")]
            covers_all = sorted({x["covers"] for x in srcs if x["figure"] in ("raised", "spent")})
            parts.append(money_rows(
                f"mt-{contest['contest_id']}", f"{which}, as reported in the news", rows, vmax=vmax,
                subtitle="Periods as the articles give them: " + "; ".join(covers_all) if covers_all else None,
                note=("Rounded in the article, so shown in its own words and not an exact amount: "
                      + "; ".join(rounded) + ".") if rounded else None,
                page=page, cite=join([c.cite(_src(srcs)), " ", _mark(page, st)]),
                extra={"data-mt-phase": phase}))
        label = f"{y}" + (" (city and town election year)" if any(r["cycle"] == "2023 municipal" for r in cyc["races"])
                          else "")
        page.add(h("section", {"class": "tsec mt-year", "id": f"y{y}", "aria-labelledby": f"y{y}-h",
                               "data-mt-year": y,
                               "data-mt-why-primary": _phase_why(phases, "primary", whys),
                               "data-mt-why-general": _phase_why(phases, "general", whys)},
                   h("h2", {"class": "tsec-h", "id": f"y{y}-h"}, label), parts))
    page.parts.insert(controls_at, money_controls(sorted(parties)))
    lines = []
    if model["no_reports"]:
        lines.append(h("li", None, h("strong", None, ", ".join(model["no_reports"]) + ": "),
                       "no reports on file for any candidate (not the same as $0)."))
    if model["not_posted"]:
        lines.append(h("li", None, h("strong", None, _years_words(model["not_posted"]) + ": "),
                       "reports not posted online.", c.cite("CFM-002")))
    if lines:
        page.add(T.tab_section("no-money", "Elections with no money on record", h("ul", {"class": "mt-none"}, lines)))
    headers = ["Year", "Election and group", "Candidate", "Party", "Raised", "Spent", "Cash on hand", "Basis", "Status"]
    page.add(see_all_fold("money-table", len(table),
                          data_table("money-figures", headers, table, caption=f"{office['title']}: every money figure",
                                     numeric=(4, 5, 6), min_width="60rem"),
                          noun="figure", label="Show the table: every figure on this page"))


def _phase_why(phases: set, phase: str, whys: list[str]) -> str | None:
    """Why an election shows nothing under Primary (or General): said in the hidden-elections line."""
    if phase in phases:
        return None
    if "whole" in phases:
        return "whole-cycle figures only: " + (whys[0] if whys else "the filings can't be split")
    return "news reports of the general election only" if phase == "primary" else "news reports of the primaries only"


def _years_words(years: list[str]) -> str:
    """'2019, 2015, 2011' or, for a long run of years, '1963 to 2019 (12 elections)'."""
    if len(years) <= 6:
        return ", ".join(years)
    ys = sorted(years)
    return f"{ys[0]} to {ys[-1]} ({len(ys)} elections)"


def _money_state(ed, office, page, model):
    c = page.cites
    ppl = model["legislators"]
    page.add(h("aside", {"class": "callout callout-note mt-basis"},
               h("p", None, h("strong", None, "A different basis from the local races. "),
                 "These are the receipts and expenditures on the reports each candidate's committees filed with the "
                 "state in each calendar year (all of the person's committees, for any office or district), not "
                 "election-cycle totals; the latest year is partial. District lines were redrawn in 2011 and 2021.",
                 c.cite("MON-020;MON-021;MON-022"))))
    table, people = [], []
    for p in ppl:
        by_year = mh.legislator_years(p)
        points = [{"x": str(y), "raised": d["r"] if d["re"] else None, "spent": d["e"] if d["ee"] else None,
                   "tip": f"Filed in {y}"} for y, d in by_year.items()]
        for y, d in by_year.items():
            table.append([p["name"], party_label(p["party"]) if p["party"] else "Party not recorded", str(y),
                          cm.usd(d["r"]) if d["re"] else "not in the data", cm.usd(d["e"]) if d["ee"] else "not in the data"])
        span = f"{p['years'][0]}" if len(p["years"]) == 1 else f"{p['years'][0]} to {p['years'][-1]}"
        srcs = _src(p["rows"])
        chart = period_money(f"mt-{p['anchor']}", f"{p['name']}: receipts and expenditures by filing year", points,
                             subtitle=f"{len(p['years'])} filing year{'s' if len(p['years']) != 1 else ''}, {span}",
                             words={"raised": "Receipts in the year", "spent": "Expenditures in the year",
                                    "missing": "not in the data", "tip_raised": "Receipts", "tip_spent": "Expenditures"},
                             page=page, cite=c.cite_compact(srcs))
        more = mh.legislator_href(ed, page, p["name"])
        people.append(h("section", {"class": "tsec mt-person", "id": p["anchor"], "aria-labelledby": f"{p['anchor']}-h",
                                    "data-party": _pkey(p["party"]), "data-mt-phase": "whole"},
                         h("h2", {"class": "tsec-h", "id": f"{p['anchor']}-h"},
                           name_with_party(p["name"], p["party"]), " ",
                           _mark(page, "computed", "Sums of the state's bulk-data rows by filing year.")),
                         chart,
                         h("p", {"class": "mt-links"}, h("a", {"href": more}, "Every committee row (state legislators' page)"))
                         if more else None))
    # each person on their own scale (filing years, not cycles, so no shared axis), two to a row on a wide screen.
    # The same two controls as the local races: the party filter applies; these are filing-year figures, so Primary
    # or General hides them and the line under the controls says why (data-mt-why-*).
    page.add(money_controls(sorted({_pkey(p["party"]) for p in ppl})))
    why = "filing-year figures for each candidate's committees, not split by election"
    page.add(h("div", {"class": "mt-people", "data-mt-group": "people", "data-mt-why-primary": why,
                       "data-mt-why-general": why}, people))
    page.add(see_all_fold("money-table", len(table),
                          data_table("money-figures", ["Candidate", "Party", "Filing year", "Receipts", "Expenditures"],
                                     table, caption=f"{office['title']}: candidates' committee money by filing year",
                                     numeric=(3, 4), min_width="40rem"),
                          noun="figure", label="Show the table: every figure on this page"))


# =========================================================================== History

def _history(ed, office, page):
    from .community_history import _clean_note, _mayor_table
    c = page.cites
    oid = office["office_id"]
    if office["office_type"] == "mayor":
        tbl, terms = _mayor_table(ed, page, oid, f"holders-{oid}")
        first = next((t for t in terms if parse_date(t["start"])), None)
        lead = [h("p", {"class": "tsec-lead"},
                  f"{len(terms)} mayors in the guide's records" + (f", since {first['start'][:4]}" if first else "")
                  + ", in order of taking office.")]
        if oid == "south-bend-mayor":
            inc = next((t for t in ed.table("timeline") if t["date"].startswith("1865-05")), None)
            if inc:
                lead.append(h("p", None, inc["description"], c.cite(inc["source_ids"]), " ", _mark(page, inc["status"])))
            lead.append(h("p", None, f"The list has {len(terms)} mayors, in the order of a secondary source that the "
                                     "fact-check matched row for row. Dates there conflict in a few places; rows marked "
                                     "low confidence carry the conflict in their notes.", c.cite("GOV-023;COM-030")))
        elif oid == "mishawaka-mayor":
            lead.append(h("p", None, "The guide has Mishawaka's mayors only from the 1960s on, and some dates and "
                                     "parties are missing. Earlier mayors are listed under Gaps on the Sources tab."))
        page.add(T.tab_section("holders", "Every mayor", lead, tbl))
        return
    terms = ed.terms_for(oid)
    no_start = [t for t in ed.tables["terms"] if t["office_id"] == oid and not parse_date(t["start"])]
    terms = no_start + [t for t in terms if t not in no_start]
    rows = []
    for i, t in enumerate(terms, 1):
        if t.get("end"):
            left = fmt_date(t["end"])
        elif t in ed.current_terms(oid):
            left = "In office"
        elif (parse_date(t["start"]) or ed.as_of) > ed.as_of:
            left = "Takes office " + fmt_date(t["start"])
        else:
            end = ed.term_end(t)
            left = (f"Term scheduled to end {fmt_date(end)}" if end else "")
        how = SELECTED_BY_LABELS.get(t.get("selected_by", ""), t.get("selected_by"))
        first = SELECTED_BY_LABELS.get(t.get("first_selected_by", ""), t.get("first_selected_by"))
        rows.append([str(i), t["person"], party_label(t["party"]) if t["party"] else "Party not in sources",
                     fmt_date(t["start"]) or "not in sources", left or "not in sources",
                     how if how == first else f"{how} (first chosen by {first})",
                     h("span", {"class": "badge-row"}, _mark(page, t["status"]),
                       _mark(page, "low") if t.get("confidence") == "low" else None, c.cite(t["source_ids"])),
                     _clean_note(t.get("notes"))])
    tbl = data_table(f"holders-{oid}", ["#", "Holder", "Party", "Took office", "Left office", "How chosen", "Status",
                                        "Notes"], rows, caption=f"{office['title']}, in order of taking office",
                     numeric=(0,), min_width="64rem")
    n = len({t["person"] for t in terms})
    first = next((t for t in terms if parse_date(t["start"])), None)
    page.add(T.tab_section("holders", "Every holder in the guide's records",
                           h("p", {"class": "tsec-lead"},
                             f"{len(terms)} term{'s' if len(terms) != 1 else ''} held by {n} "
                             f"{'people' if n != 1 else 'person'}" + (f", from {first['start'][:4]}" if first else "")
                             + ". The guide's officeholder records mostly begin in 2010."),
                           tbl))


# =========================================================================== Sources

def office_gaps(ed, office) -> list[dict]:
    """Gaps whose wording names this office: its full title, its title without the district, or (mayors) the city
    with "mayor"."""
    title = office["title"]
    base = re.sub(r",? ?(District|Ward) .*|, At-Large.*", "", title).strip()
    pats = [re.escape(title), re.escape(base)]
    if office["office_type"] == "mayor":
        city = re.sub(r"^Mayor of ", "", title)
        pats.append(rf"{re.escape(city)}(?:'s)? mayor")
    rx = re.compile("|".join(f"(?:{p})" for p in pats if p), re.I)
    out = []
    for g in ed.gaps_rows:
        if rx.search(f"{g.get('item', '')} {g.get('why_missing', '')}"):
            out.append(g)
    return out


def _sources(ed, office, page):
    oid = office["office_id"]
    keys = om.office_tabs(ed, oid)
    notes = []
    if "money" in keys and not om.money_model(ed, oid)["state"]:
        notes.append(mh.POSTED_FROM.replace("so the guide has no figures for them (not the same as $0).",
                                            "so the guide has no figures for them (not the same as $0) except where "
                                            "news coverage reported them; those are marked with their source and "
                                            "status, and a rounded figure keeps the article's own words."))
    if "elections" in keys:
        from .county import ballot_order_note
        cs = om.contests(ed, oid)
        eids = list(dict.fromkeys(c["election_id"] for c in cs if c["election_id"] in ed.elections))
        notes.append(h("span", None, "Results are as the county's canvass or the cited source prints them; the "
                                     "Elections tab draws each contest on the same 0 to 100% scale. Candidate order: ",
                       ballot_order_note(ed, page, eids)))
    page.add(*T.sources_body(page, office_gaps(ed, office), notes=notes, title=office["title"]))


# =========================================================================== one office

def build_office(office_id: str, site, tab: str = "overview"):
    """Builds every tab of the office the first time any of its paths is asked for (they share one citation list),
    then returns the asked tab's page."""
    ed = site.ed
    done = site.__dict__.setdefault("_office_pages", {})
    if office_id not in done:
        office = ed.offices[office_id]
        keys = om.office_tabs(ed, office_id)
        render = {"overview": partial(_overview, ed, office), "elections": partial(_elections, ed, office),
                  "money": partial(_money, ed, office), "history": partial(_history, ed, office),
                  "sources": partial(_sources, ed, office)}
        done[office_id] = T.build_tabs(site, om.base(office_id), keys, head_for(ed, office),
                                       {k: render[k] for k in keys})
    pages = done[office_id]
    if tab not in pages:
        raise KeyError(f"{office_id} has no {tab} tab")
    # build.py rebuilds a page as a stub when its builder fails; make sure every tab is registered (a stub pass for
    # another tab cannot have replaced it, since every tab has this builder)
    for k, p in pages.items():
        site.pages.setdefault(p.path, p)
    return pages[tab]


# =========================================================================== hub

HUB_LAYERS = [  # (tab id, tab label)
    ("countywide", "Countywide"), ("cities", "Cities and towns"), ("townships", "Townships"),
    ("schools", "School corporations"), ("commissioners", "Commissioners"),
    ("council", "County council"), ("city-council", "City councils"),
    ("house", "Indiana House"), ("senate", "Indiana Senate"), ("statewide", "Statewide"), ("federal", "Federal")]
# 2026-11-18 (owner): the State and Federal layers keep the county map: the whole county outline is the area (every
# voter in the county votes on these offices), with a label saying which view is shown. The guide never draws Indiana
# or the U.S. (civic/offices.py level_note / level_covers_county)
LEVEL_LAYERS = {"statewide": ("Statewide offices", "Statewide"), "federal": ("Federal offices", "Federal")}
# the kind of area a district layer draws (panel type line, "Drawn on the ... layer")
HUB_DISTRICT_WORD = {"commissioners": "County commissioner district", "council": "County council district",
                     "city-council": "City council district", "house": "Indiana House district",
                     "senate": "Indiana Senate district"}
HUB_DEFAULT_LAYER = "cities"
# district shape sets drawn on the hub map: set id -> (layer tab, office id for a district code)
HUB_SETS = OrderedDict([
    ("county-commissioner-2022", ("commissioners", lambda d: f"county-commissioner-d{d.lower()}")),
    ("county-council-2022", ("council", lambda d: f"county-council-{d.lower()}")),
    ("south-bend-council-2022", ("city-council", lambda d: f"south-bend-council-d{d.lower()}")),
    ("mishawaka-council-2022", ("city-council", lambda d: f"mishawaka-council-d{d.lower()}")),
    ("in-house-2021", ("house", lambda d: f"state-house-{re.sub(r'^HD', '', d)}")),
    ("in-senate-2021", ("senate", lambda d: f"state-senate-{re.sub(r'^SD', '', d)}")),
])
HUB_LAYER_TYPES = {"cities": ("city", "town"), "townships": ("township",), "schools": ("school_corporation",)}
HUB_SHAPE_KEY = {"cities": "place", "townships": "township", "schools": "school"}
NO_DRAWN = "No drawn boundary in the guide"
HUB_HINT = ("Point at, focus or tap an area to list the offices its voters elect. Select it again, or use the link, "
            "to open it. Every office is also in the list below the map.")


def _districted(office) -> bool:
    d = (office.get("district") or "").strip().lower()
    return bool(d) and d != "at-large"


def hub_areas(ed, shapes: dict | None, dshapes: dict | None) -> dict:
    """The hub map's model, from the boundary files only (no geometry is made here):

    {"layers": [{tab, label, items: [{uid, d, kind ("gov" | "district"), unit or office, label point...}]}],
     "drawn": {office_id: layer tab} for every office with its own district shape}
    A district set whose shapes name an office not in offices.csv is skipped with a data warning."""
    from civic.district_map import district_set
    layers = OrderedDict((t, {"tab": t, "label": lab, "items": []}) for t, lab in HUB_LAYERS)
    drawn: dict = {}
    sources: list = []
    if shapes:
        layers["countywide"]["items"].append({"uid": "county", "d": shapes["county"]["d"], "kind": "gov",
                                              "unit": "county"})
        for tab, types in HUB_LAYER_TYPES.items():
            for n, it in enumerate(shapes["layers"].get(HUB_SHAPE_KEY[tab], [])):
                u = ed.units.get(it.get("id") or "")
                if not u or u["unit_type"] not in types:
                    continue
                layers[tab]["items"].append({"uid": it["id"], "d": it["d"], "kind": "gov", "unit": it["id"], "n": n,
                                             "label": it.get("label"), "label_r": it.get("label_r", 99),
                                             "bbox": it.get("bbox")})
    for sid, (tab, oid_of) in HUB_SETS.items():
        rec = district_set(dshapes, sid)
        if not rec:
            continue
        for it in rec["items"]:
            oid = oid_of(it["district"])
            if oid not in ed.offices:
                ed.warnings.append(f"offices hub map: district {it['district']} of {sid} names no office ({oid}); "
                                   "left off the map")
                continue
            layers[tab]["items"].append({"uid": f"d-{oid}", "d": it["d"], "kind": "district", "office": oid,
                                         "set": sid, "district": it["district"], "label": it.get("label"),
                                         "label_r": it.get("label_r", 99),
                                         "text": re.sub(r"^(HD|SD)", "", it["district"])})
            drawn[oid] = tab
        if rec.get("source_ids"):
            sources.append(rec["source_ids"])
    if shapes:
        for tab in LEVEL_LAYERS:
            offs = [o["office_id"] for o in ed.tables["offices"] if om.level(ed, o) == tab]
            if offs and om.level_covers_county(ed, tab):
                layers[tab]["items"].append(level_item(ed, shapes, tab, offs))
                for oid in offs:   # a district seat whose district holds the whole county is drawn: the outline
                    if _districted(ed.offices[oid]):
                        drawn[oid] = tab
    return {"layers": [L for L in layers.values() if L["items"]], "drawn": drawn, "sources": sources}


def level_item(ed, shapes: dict, tab: str, office_ids: list[str]) -> dict:
    """The one area of a State or Federal layer: the county outline (no other geometry), its offices, the note that
    says what the level covers, and a label point at the middle of the map's viewBox."""
    vb = [float(v) for v in (shapes["viewBox"].split() if isinstance(shapes["viewBox"], str) else shapes["viewBox"])]
    return {"uid": f"lvl-{tab}", "d": shapes["county"]["d"], "kind": "level", "level": tab, "offices": office_ids,
            "note": om.level_note(ed, tab) or "", "center": (vb[0] + vb[2] / 2, vb[1] + vb[3] / 2)}


def level_label(item) -> Markup:
    """The text drawn on a State or Federal layer: two short lines in the middle of the county."""
    x, y = item["center"]
    first = LEVEL_LAYERS[item["level"]][0]
    second = "Every voter in the county votes" if item["level"] == "statewide" else "The whole county votes"
    return h("text", {"x": f"{x:.1f}", "y": f"{y:.1f}", "text-anchor": "middle", "class": "cmap-label cmap-level-label"},
             h("tspan", {"x": f"{x:.1f}", "dy": "-4"}, first),
             h("tspan", {"x": f"{x:.1f}", "dy": "22", "class": "cmap-level-sub"}, second))


def _hub_offices_for(ed, item) -> list[dict]:
    """The offices the voters of one map area elect, as offices.csv rows: a government's every office (the county's
    countywide area: its offices with no district, and the courts); a district shape: its one office."""
    if item["kind"] == "district":
        return [ed.offices[item["office"]]]
    if item["kind"] == "level":
        return [ed.offices[oid] for oid in item["offices"]]
    if item["unit"] == "county":
        return [o for o in ed.tables["offices"] if o["unit_id"] in ("county", "sjc-courts") and not _districted(o)]
    return [o for o in ed.tables["offices"] if o["unit_id"] == item["unit"]]


def _holder_cell(ed, o):
    cur = ed.current_terms(o["office_id"])
    if not cur:
        return h("span", {"class": "muted"}, NO_HOLDER)
    return join([name_with_party(t["person"], term_party(t), t.get("confidence") if term_party(t) else None)
                 for t in cur], ", ")


def _panel_block(ed, page, uid, offices, drawn, layer_tab) -> Markup:
    """One area's office list for the map panel: shipped once, hidden, in #ofm-lists; static/js/offices.js copies it
    into the panel that static/js/map.js draws (links, holders with their party tags, next election)."""
    items = []
    for o in offices:
        oid = o["office_id"]
        link = om.href(page, oid)
        nxt = o.get("next_election") or ""
        where = None
        if _districted(o):
            tab = drawn.get(oid)
            if tab and tab != layer_tab:
                where = h("span", {"class": "ofm-where"}, f"Drawn on the map layer “{dict(HUB_LAYERS)[tab]}”")
            elif not tab:
                where = h("span", {"class": "ofm-where ofm-nodraw"}, NO_DRAWN + " (elected by district or ward)")
        items.append(h("li", {"class": "ofm-item"},
                       h("a", {"class": "ofm-office", "href": link}, o["title"]) if link else
                       h("span", {"class": "ofm-office"}, o["title"]),
                       h("span", {"class": "ofm-who"}, _holder_cell(ed, o)),
                       h("span", {"class": "ofm-next"}, f"Next election {nxt}" if nxt
                         else "Next election not in the guide's data"),
                       where))
    return h("div", {"class": "ofm-block", "data-ofm-uid": uid},
             h("p", {"class": "ofm-count"}, f"{len(offices)} office{'s' if len(offices) != 1 else ''} elected here"
               if offices else "No office in the guide's list for this area"),
             h("ul", {"class": "ofm-list"}, items))


def hub_map(page, ed, shapes, model) -> Markup | None:
    """The Offices hub map: the .cmap contract of civic/map.py and civic/district_map.py (root, tabs, layers, area
    links, #cmap-panel, #cmap-data), so static/js/map.js gives hover, focus, the panel that keeps the last area, touch
    select-then-open and the layer tabs; static/js/offices.js adds each area's office list to the panel. Fills only
    tell kinds of government or neighboring districts apart, never party. Every area is a link (JS off): a government
    to its group in the list below, a district to its office page."""
    from civic.campaign_map import SET_NOTES
    from civic.district_map import neighbor_fills
    from civic.map import _kind_class, _label_boxes
    if not shapes or not model["layers"]:
        return None
    vb = shapes["viewBox"]
    data, groups, tabs_, blocks = {}, [], [], []
    labels_of = dict(HUB_LAYERS)
    county_back = [h("path", {"d": t["d"], "class": "cmap-s cmap-township cmap-back-s"})
                   for t in shapes["layers"].get("township", [])]
    for L in model["layers"]:
        tab = L["tab"]
        on = tab == HUB_DEFAULT_LAYER
        fills = neighbor_fills([{"district": it["uid"], "d": it["d"]} for it in L["items"]]) \
            if L["items"][0]["kind"] == "district" else {}
        paths, texts, place_items = [], [], []
        for it in L["items"]:
            offs = _hub_offices_for(ed, it)
            if it["kind"] == "level":
                name = LEVEL_LAYERS[it["level"]][0]
                href = f"#{om.LEVEL_IDS[it['level']]}"
                cls = "cmap-s cmap-level"
                typ = f"{LEVEL_LAYERS[it['level']][1]} level: the whole county"
                entry = {"n": name, "t": typ, "f": [], "cav": [it["note"]] if it["note"] else [], "note": "",
                         "href": href, "open": "Show these offices in the list below", "l": tab}
                aria = f"{name}: {len(offs)} office{'s' if len(offs) != 1 else ''}. {it['note']} Show in the list."
                texts.append(level_label(it))
            elif it["kind"] == "gov":
                u = ed.units[it["unit"]]
                name = "St. Joseph County: countywide offices" if it["unit"] == "county" else u["name"]
                href = f"#g-{it['unit']}"
                cls = "cmap-s cmap-township" if it["unit"] == "county" else f"cmap-s {_kind_class(u, it.get('n', 0))}"
                typ = {"county": "Elected by the whole county", "city": "City", "town": "Town", "township": "Township",
                       "school_corporation": "School corporation"}.get("county" if it["unit"] == "county"
                                                                       else u["unit_type"], "")
                cav = []
                if it["unit"] == "county":
                    cav.append("County commissioners and council members are elected by district: see the "
                               "Commissioners and County council map layers. Judges are listed here "
                               "because the whole county elects or retains them.")
                nod = [o for o in offs if _districted(o) and o["office_id"] not in model["drawn"]]
                if nod:
                    cav.append(f"{len(nod)} of these seats {'are' if len(nod) != 1 else 'is'} elected by district or "
                               "ward, or tied to a township, and the guide has no official boundary file for "
                               f"{'them' if len(nod) != 1 else 'it'}, so they are not drawn.")
                entry = {"n": name, "t": typ, "f": [], "cav": cav, "note": "", "href": href,
                         "open": "Show its offices in the list below", "l": tab}
                aria = f"{name}: {len(offs)} office{'s' if len(offs) != 1 else ''}. Show in the list."
                if tab == "cities" and it.get("label") and it.get("bbox"):
                    place_items.append(dict(label=it["label"], label_r=it["label_r"], bbox=it["bbox"],
                                            short=u["name"].replace("City of ", "").replace("Town of ", "")))
                if tab == "townships" and it.get("label"):
                    texts.append(h("text", {"x": it["label"][0], "y": it["label"][1] + 3, "text-anchor": "middle",
                                            "class": "cmap-label cmap-label-township"},
                                   u["name"].replace(" Township", "")))
            else:
                o = ed.offices[it["office"]]
                name = o["title"]
                href = page.rel(om.path(it["office"]))
                cls = f"cmap-s dmap-s dmap-f{fills.get(it['uid'], 0)}"
                typ = HUB_DISTRICT_WORD[tab]
                entry = {"n": name, "t": typ, "f": [], "cav": [SET_NOTES.get(it["set"], "")] if SET_NOTES.get(it["set"])
                         else [], "note": "", "href": href, "open": "Open the office page", "l": tab}
                aria = f"{name}. Open the office page."
                if it.get("label"):
                    texts.append(h("text", {"x": it["label"][0], "y": it["label"][1] + 4, "text-anchor": "middle",
                                            "class": "cmap-label dmap-label" + (" dmap-label-sm" if it["label_r"] < 22
                                                                               else "")}, it["text"]))
            data[it["uid"]] = entry
            kids = [h("path", {"d": it["d"], "class": cls})]
            if tab == "cities" and it.get("label_r", 99) < 6 and it.get("label"):
                kids.append(h("circle", {"cx": it["label"][0], "cy": it["label"][1], "r": 5, "class": "cmap-dot"}))
            paths.append(h("a", {"href": href, "class": "cmap-a", "data-uid": it["uid"], "aria-label": aria}, kids))
            blocks.append(_panel_block(ed, page, it["uid"], offs, model["drawn"], tab))
        for pi, x, y, anchor in _label_boxes(place_items, vb[2]):
            texts.append(h("text", {"x": x, "y": y, "text-anchor": anchor, "class": "cmap-label cmap-label-place"},
                           pi["short"]))
        back = h("g", {"class": "cmap-back", "aria-hidden": "true"}, county_back) \
            if tab in ("cities", "city-council") else None
        groups.append(h("g", {"class": "cmap-layer" + (" is-on" if on else ""), "data-layer": tab, "role": "group",
                              "aria-label": f"Layer: {labels_of[tab]}"},
                        back, h("g", {"clip-path": "url(#cmap-clip)"}, paths),
                        h("g", {"class": "dmap-over", "aria-hidden": "true"}, texts)))
        tabs_.append(h("button", {"type": "button", "class": "cmap-tab", "data-layer": tab,
                                  "aria-pressed": "true" if on else "false"}, labels_of[tab]))
    svg = h("svg", {"class": "cmap-svg", "viewBox": f"{vb[0]} {vb[1]} {vb[2]} {vb[3]}", "role": "group",
                    "aria-label": f"Map of {ed.county_label}'s elected offices by area. Every area is a link; the list "
                                  "after the map has every office."},
            h("defs", None, h("clipPath", {"id": "cmap-clip"}, h("path", {"d": shapes["county"]["d"]}))),
            groups,
            h("path", {"d": shapes["county"]["d"], "class": "cmap-outline", "aria-hidden": "true"}),
            h("g", {"class": "cmap-hl-g", "aria-hidden": "true", "clip-path": "url(#cmap-clip)"}))
    panel = h("aside", {"class": "cmap-panel", "id": "cmap-panel", "aria-live": "polite",
                        "aria-label": "Offices of the selected area"}, h("p", {"class": "cmap-hint"}, HUB_HINT))
    nodraw = sorted({om.unit_name(ed, o["unit_id"]) for o in ed.tables["offices"]
                     if _districted(o) and o["office_id"] not in model["drawn"]})
    return h("div", {"class": "cmap dmap ofm", "id": "offices-map", "data-default-layer": HUB_DEFAULT_LAYER,
                     "data-hash": "off"},
             h("div", {"class": "cmap-bar"},
               h("div", {"class": "cmap-tabs", "role": "group", "aria-label": "Map layer", "hidden": True}, tabs_)),
             h("div", {"class": "cmap-grid"},
               h("div", {"class": "cmap-stage"}, svg,
                 h("p", {"class": "dmap-key muted ofm-key"},
                   "Fills only tell kinds of government or neighboring districts apart; they show no party or amount. "
                   f"District and ward seats with no official boundary file ({len(nodraw)} governments) are listed "
                   "under their government, marked “no drawn boundary”.")),
               h("div", {"class": "dmap-side"}, panel)),
             [h("p", {"class": "cmap-level-note muted", "data-layer": it["level"]}, it["note"])
              for L in model["layers"] for it in L["items"] if it["kind"] == "level" and it["note"]],
             h("div", {"id": "ofm-lists", "hidden": True}, blocks),
             json_script("cmap-data", data))


def _gov_summary(ed, offs) -> Markup:
    """'11 offices · 15 seats (12 D, 3 R)': the group's one line, with the party breakdown the site shows for bodies."""
    terms = [t for o in offs for t in ed.current_terms(o["office_id"])]
    seats = [_seats(o) for o in offs]
    n_seats = sum(seats) if all(s is not None for s in seats) else None
    bd = party_breakdown(terms, n_seats)
    seat_txt = (f"{n_seats} seat{'s' if n_seats != 1 else ''} " if n_seats is not None else "")
    return h("span", {"class": "ofh-gov-n"},
             f"{len(offs)} office{'s' if len(offs) != 1 else ''} · {seat_txt}", bd)


def build_hub(site):
    from civic.district_map import load_district_shapes
    from civic.map import load_shapes
    from civic.preselect import here_attrs
    ed = site.ed
    page = site.page(om.HUB, body_class="thing-page")
    c = page.cites
    page.add(h("header", {"class": "thing-head hub-head"},
               page.crumb_nav(),
               h("h1", {"class": "thing-title"}, "Offices"),
               h("p", {"class": "thing-facts"},
                 f"{len(ed.tables['offices'])} offices in the guide, by government. Each has its own page: what it "
                 "does, who holds it, every election and the campaign money on record.")))
    shapes = load_shapes(ed)
    model = hub_areas(ed, shapes, load_district_shapes(ed, shapes))
    m = hub_map(page, ed, shapes, model)
    page.add(h("p", {"class": "here-pre ofh-pre", "id": "ofh-pre", "hidden": True}))
    if m is not None:
        page.add(T.tab_section("by-area", "Who your area elects", m))
    groups: OrderedDict = OrderedDict((k, OrderedDict()) for k in om.LEVELS)
    for o in ed.tables["offices"]:
        groups[om.level(ed, o)].setdefault(o["unit_id"], []).append(o)
    years = sorted({o["next_election"] for o in ed.tables["offices"] if o.get("next_election")})
    up_next = years[0] if years else None
    sections = []
    n_rows = 0
    for lv, units in groups.items():
        if not units:
            continue
        blocks = []
        for uid, offs in units.items():
            items = []
            here = here_attrs(ed, uid)
            for o in offs:
                oid = o["office_id"]
                cur = ed.current_terms(oid)
                nxt = o.get("next_election") or ""
                link = om.href(page, oid)
                attrs = {"class": "ofh-row", "data-tf-row": True, "data-tf-level": lv, "data-tf-next": nxt or "none",
                         "data-tf-text": f"{o['title']} {om.unit_name(ed, uid)} " + " ".join(t["person"] for t in cur)}
                attrs.update(here)
                nodraw = _districted(o) and oid not in model["drawn"]
                items.append(h("li", attrs,
                               h("a", {"class": "ofh-office", "href": link}, o["title"]) if link else
                               h("span", {"class": "ofh-office"}, o["title"]),
                               h("span", {"class": "ofh-who"}, _holder_cell(ed, o)),
                               h("span", {"class": "ofh-next"},
                                 f"Next election {nxt}" + (" (up next)" if nxt and nxt == up_next else "")
                                 if nxt else "Next election not in the guide's data",
                                 h("span", {"class": "ofh-nodraw"}, " · no drawn boundary in the guide")
                                 if nodraw else None)))
                n_rows += 1
            gov = om.government_page(ed, uid)
            gov_link = (h("p", {"class": "ofh-gov-link"}, h("a", {"href": page.rel(gov[0])}, f"{gov[1]}: government page"))
                        if gov and gov[0].split("#")[0] in page.site.by_path else None)
            blocks.append(h("details", {"class": "ofh-gov", "id": f"g-{uid}", "data-tf-group": True,
                                        "data-fold": "gov", "open": True},
                            h("summary", {"class": "ofh-gov-sum"},
                              h("span", {"class": "ofh-gov-name"}, om.unit_name(ed, uid)), " ", _gov_summary(ed, offs)),
                            gov_link,
                            h("ul", {"class": "ofh-list"}, items)))
        sections.append(h("section", {"class": "tsec ofh-level", "id": om.LEVEL_IDS[lv], "data-tf-group": True,
                                      "aria-labelledby": f"{om.LEVEL_IDS[lv]}-h"},
                          h("h2", {"class": "tsec-h", "id": f"{om.LEVEL_IDS[lv]}-h"},
                            "County and courts" if lv == "county" else om.LEVELS[lv]),
                          h("div", {"class": "ofh-govs"}, blocks)))
    filt = table_filter("offices-all",
                        [{"key": "level", "label": "Level", "all": "Every level",
                          "options": [(k, "County and courts" if k == "county" else v) for k, v in om.LEVELS.items()
                                      if groups[k]]},
                         {"key": "next", "label": "Next election", "all": "Any year",
                          "options": [(y, f"{y} (up next)" if y == up_next else y) for y in years]
                                     + [("none", "Not in the guide's data")]}],
                        n_rows, noun="office", search="Office, place or person", label="Filter the offices")
    page.add(h("section", {"class": "tsec ofh-all-sec", "id": "list", "aria-labelledby": "list-h"},
               h("h2", {"class": "tsec-h", "id": "list-h"}, "Every office, by government"),
               h("p", {"class": "ofh-lead"}, "Open a government to see its offices, or filter the list. Also: ",
                 h("a", {"href": page.rel("officeholders/index.html")}, "Who holds office now"),
                 " (every officeholder with how each first took office) and ",
                 h("a", {"href": page.rel("elections/calendar/index.html")}, "the election calendar"), "."),
               filt,
               h("p", {"class": "tf-empty muted", "data-tf-empty": "offices-all", "hidden": True, "role": "status"},
                 "No offices match. Use Reset filters to see them all."),
               h("div", {"class": "ofh-all", "id": "offices-all", "data-tf-deep": True}, sections)))
    srcs = _src(ed.tables["offices"], *model["sources"])
    page.add(h("p", {"class": "tnote"}, "Offices and seats from the guide's list of offices; holders from its terms "
                                        "records; boundaries from the official files listed on the map pages "
                                        "(the guide draws none of its own).", c.cite_compact(srcs)))
    page.finish(gaps=None)
    return page


# =========================================================================== registration

def _office_ids_all_editions() -> list[str]:
    import csv
    root = Path(__file__).resolve().parents[3] / "data" / "editions"
    ids = []
    for f in sorted(root.glob("*/offices.csv")):
        with open(f, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                if r["office_id"] not in ids:
                    ids.append(r["office_id"])
    return ids


PAGES = {om.HUB: build_hub}
for _oid in _office_ids_all_editions():
    for _k in T.TAB_ORDER:
        PAGES[om.path(_oid, _k)] = partial(build_office, _oid, tab=_k)
