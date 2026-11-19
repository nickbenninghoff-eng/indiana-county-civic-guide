"""Election pages (phase 6 step 4, 2026-11-16; planning/design-direction-2026-11-16.md sections 2 to 5).

One tabbed page per row of elections.csv, with the tab template of civic/tabs.py (the model, paths and links are in
civic/election_pages.py):

    elections/<id>/index.html       Overview: the date and kind, turnout with its base and status, how many contests
                                    and how many had no contest, the closest races, the elections before and after
    elections/<id>/contests/        every contest on the ballot, by level of government (a primary by party first),
                                    each a compact result (winner, share, margin, status) linked to its office's
                                    Elections tab, with every candidate's result in a fold
    elections/<id>/map/             the map's "How areas voted" layer preset to this election's races (2020, 2022
                                    and 2024 generals: the years with precinct results; civic/map.py election_vote_map)
    elections/<id>/sources/         every source cited on the tabs, the gaps, what the marks mean

No figure is computed here beyond what the elections pages already compute and label: results are results.csv rows
(Edition.contests), turnout is elections.csv as printed, the margin is pages/elections.py margin() and the race scope
is pages/elections_numbers.py's (the same rule as Compare, which counts 2010 on). Candidates keep the source's order;
contests keep the canvass's order inside each level. Party colors appear only in the results bars, as everywhere.
"""
from __future__ import annotations

import csv
import re
from functools import partial
from pathlib import Path

from civic import election_pages as EP
from civic import offices as om
from civic import tabs as T
from civic.charts import results_bars
from civic.components import (FIGURE_MARKS, figure_mark, name_with_party, party_label, scope_attrs, scope_mark,
                              scope_note)
from civic.data import fmt_date, fmt_int, split_ids
from civic.html import h, join
from civic import overall as OV
from civic import results_status as RS
from civic.map import VOTE_CAVEAT, election_vote_map, load_shapes, race_by_contest

from .elections import (GROUP_ORDER, MUNICIPAL_TYPES, _question_outcome, _search_text, candidates, classify,
                        contest_status, is_question, is_writein_total, margin)
from .elections_numbers import _contested, _counts, _pts_text, _who, election_races

PARTY_WORD = {"D": "Democratic", "R": "Republican", "L": "Libertarian", "G": "Green"}
# Levels of government on the Contests tab, in office order (county first, then townships, cities, towns, schools,
# the legislature; decided-elsewhere and yes-or-no lines last). Each holds pages/elections.py classify() groups.
CONTEST_LEVELS = [
    ("county", "County", ("County row offices", "County commissioners", "County council", "County courts",
                          "Superior Court retention")),
    ("township", "Townships", ("Township offices",)),
    ("city", "Cities", ("City offices",)),
    ("town", "Towns", ("Town offices",)),
    ("school", "School boards", ("School boards",)),
    ("legislature", "State legislature", ("State legislature",)),
    ("state", "Statewide offices and courts", ("Statewide offices", "State court retention")),
    ("federal", "Federal offices", ("Federal offices",)),
    ("questions", "Public questions", ("Public questions",)),
    ("straight", "Straight-party ballots", ("Straight-party ballots",)),
    ("other", "Other contests", ("Other",)),
]
LEVEL_OF_GROUP = {g: k for k, _, gs in CONTEST_LEVELS for g in gs}
LEVEL_LABEL = {k: lab for k, lab, _ in CONTEST_LEVELS}
CLOSEST_N = 3
VOTE_SRC = ["MAP-005", "MAP-006", "MAP-007", "MAP-009", "MAP-008"]


# =========================================================================== small helpers

def _src(*groups) -> str:
    out: list[str] = []
    for g in groups:
        for x in (g if isinstance(g, list) else [g]):
            ids = split_ids(x.get("source_ids")) if isinstance(x, dict) else split_ids(x)
            out += [i for i in ids if i not in out]
    return ";".join(out)


def _num(v):
    try:
        return float(v) if v not in (None, "") else None
    except ValueError:
        return None


def _marks_href(page) -> str | None:
    base = page.entry.thing if page.entry is not None else ""
    if not base:
        return None
    return "#marks" if page.entry.tab == "sources" else page.rel(T.tab_path(base, "sources")) + "#marks"


def _mark(page, status, note=None):
    return T.status_mark(status, page, note, sources_href=_marks_href(page))


def cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def when_text(e: dict) -> str:
    """The date as recorded: 'November 5, 2024', or the year alone (rows before 2010 and the 2013 special)."""
    d = e.get("date") or ""
    return fmt_date(d, long=True) if d.count("-") == 2 else (d or e["election_id"][:4])


def level_of(c) -> str:
    return LEVEL_OF_GROUP.get(classify(c)[0], "other")


def party_title(code: str) -> str:
    if not code:
        return "On every primary ballot (no party)"
    return f"{PARTY_WORD.get(code, party_label(code))} primary"


def party_key(code: str) -> str:
    return f"party-{code.lower()}" if code else "party-none"


def _party_order(codes) -> list[str]:
    """Party primaries in alphabetical order of their names (never by result), the no-party lines last."""
    return sorted(codes, key=lambda p: (p == "", party_title(p)))


def head_for(ed, e) -> T.Head:
    eid = e["election_id"]
    cs = EP.contests(ed, eid)
    to = _num(e.get("turnout_pct"))
    facts = [when_text(e), cap(EP.TYPE_TITLE.get(e["type"], e["type"])),
             f"Turnout {to:.1f}%" if to is not None else "Turnout not recorded",
             f"{len(cs)} contest{'s' if len(cs) != 1 else ''} in the guide's results"]
    return T.Head(kind="Election", title=cap(EP.title(e)), facts=facts)


# =========================================================================== one contest, compact

def result_text(c, ed=None) -> object:
    """Who won and with what share, in ballot order: 'Elected: Name (D) 61.2%'. A count that is unofficial says
    'Ahead' (its mark, or its section's caption line, says the count is unofficial; 2026-11-18); a contest decided outside the county shows the county tally for every candidate; a
    question shows yes and no."""
    cands = candidates(c)
    st = contest_status(c["rows"])
    _g, _p, cross = classify(c)
    unoff = st == "unofficial"
    if ed is not None and not is_question(c):
        words = OV.result_words(ed, c)   # a multi-county contest: its overall result (2026-11-18)
        if words is not None:
            return h("span", None, words)
    if is_question(c):
        bits = [f"{x['name']} {x['pct']:.1f}%" for x in cands if x["pct"] is not None]
        sw = OV.question_statewide(ed, c) if ed is not None else None   # 2024 PQ1: "Statewide: Yes (ratified)"
        return h("span", None, h("strong", {"class": "ep-out"}, _question_outcome(cands, cross, unoff)),
                 (" · " + " · ".join(bits)) if bits else None, [" · ", h("strong", None, sw)] if sw else None)
    if cross or _g == "Straight-party ballots":
        bits = [h("span", {"class": "ep-cand"}, name_with_party(x["name"], x["party"]),
                  f" {x['pct']:.1f}%" if x["pct"] is not None else "") for x in cands]
        word = "Straight-party marks: " if _g == "Straight-party ballots" else "County tally: "
        return h("span", None, h("span", {"class": "ep-out"}, word), join(bits, ", "))
    named = [x for x in cands if not is_writein_total(x["row"])]
    wins = [x for x in cands if x["winner"] == "Y"]
    if not wins:
        if len(named) == 1:
            x = named[0]
            return h("span", None, h("span", {"class": "ep-out"}, "Only candidate: "), name_with_party(x["name"], x["party"]))
        return h("span", {"class": "muted"}, "Winner not recorded in the guide's data")
    word = "Ahead: " if unoff else ("Elected: " if len(wins) == 1 else f"Elected ({len(wins)}): ")
    bits = [h("span", {"class": "ep-cand"}, name_with_party(x["name"], x["party"]),
              f" {x['pct']:.1f}%" if x["pct"] is not None else "") for x in wins]
    return h("span", None, h("span", {"class": "ep-out"}, word), join(bits, ", "))


def margin_text(c, ed=None) -> str:
    if is_question(c):
        return "Yes or no"
    if ed is not None:
        words = OV.margin_words(ed, c)
        if words is not None:
            return words
    g, _p, cross = classify(c)
    if g == "Straight-party ballots":
        return "Not a race"
    if cross:
        return "County portion only"
    m = margin(c)
    if m is None:
        return "Uncontested"
    if "reason" in m:
        return f"No margin: {m['reason']}"
    if m["tie"]:
        return "Tied on votes"
    return f"Margin {m['pts']:.1f} points"


def contest_figure(page, c):
    """Every candidate's result (pages/county.py _contest_figure's form: the shared results bars, 0 to 100%). A contest
    the county tally does not decide shows no winner, as the results explorer did."""
    cands = candidates(c)
    st = contest_status(c["rows"])
    q = is_question(c)
    cross = classify(c)[2] or OV.info(page.ed, c)["basis"] in ("overall", "pending", "missing")
    notes = []
    if cross:
        notes.append("County tally only; voters outside the county also decide this contest, so no winner is marked "
                     "on these bars.")
    if any(x["computed"] for x in cands):
        notes.append("Shares computed from the vote counts.")
    if any(x["low"] for x in cands):
        notes.append("Some figures are low confidence.")
    rows = [{"name": x["name"], "party": "" if q else x["party"], "votes": x["votes"], "pct": x["pct"],
             "winner": "" if cross or classify(c)[0] == "Straight-party ballots" else x["winner"]} for x in cands]
    sub = f"Vote for {c['vote_for']}" if c.get("vote_for") and c["vote_for"] != "1" else None
    return OV.with_overall(page, c, results_bars(f"res-{c['contest_id']}", OV.figure_title(page.ed, c), rows,
                                                 subtitle=sub, status=st, note=" ".join(notes) or None, page=page,
                                                 question=q, cite=page.cites.cite(_src(*c["rows"]))))


def contest_item(page, c, hx: str, on_map: dict) -> object:
    """One contest: a line (name, result, margin, mark) that links to the office's Elections tab, then every
    candidate's result in a fold (ships open; static/js/folds.js closes it)."""
    ed = page.ed
    st = contest_status(c["rows"])
    oh = om.href(page, c["office_id"], "elections") if c.get("office_id") else None
    name = _search_text(c["label"]) if c.get("party_primary") else c["label"]
    links = []
    if oh:
        links.append(h("a", {"href": oh}, "Every election for this office"))
    rid = on_map.get(c["contest_id"])
    mh = EP.href(page, c["election_id"], "map")
    if rid and mh:
        links.append(h("a", {"href": f"{mh}#race-{rid}"}, "How areas voted"))
    q = is_question(c)
    # the line's mark speaks for the contest's chart and table too (scope), so the contest is marked once
    return h("li", {"class": "ep-contest", "id": EP.contest_anchor(c["contest_id"]), **scope_attrs(st)},
             h("div", {"class": "ep-line"},
               h(hx, {"class": "ep-what"}, h("a", {"href": oh}, name) if oh else name),
               h("span", {"class": "ep-result"}, result_text(c, ed), scope_mark(st)),
               h("span", {"class": "ep-margin"}, margin_text(c, ed))),
             h("details", {"class": "ep-fold", "data-fold": True, "open": True},
               h("summary", {"class": "ep-fold-sum"}, "Yes and no votes" if q else "Every candidate"),
               contest_figure(page, c),
               h("p", {"class": "ep-links"}, join(links, " · ")) if links else None))


# =========================================================================== Overview

def _overview(ed, e, page):
    c = page.cites
    eid = e["election_id"]
    cs = EP.contests(ed, eid)
    primary = e["type"] in EP.PRIMARY_TYPES
    out = []

    # ---- turnout, always with its base
    to = _num(e.get("turnout_pct"))
    who = (e.get("scope") or "").strip()
    if to is not None:
        body = [h("p", {"class": "ep-big"}, h("strong", {"class": "ep-fig"}, f"{to:.1f}%"),
                  " of registered voters cast a ballot", c.cite(e.get("source_ids")), " ", _mark(page, e["status"])),
                h("p", None, f"{fmt_int(e['ballots_cast']) or 'Ballots not printed'} ballots cast, of "
                             f"{fmt_int(e['registered']) or 'a number not printed'} registered voters. "
                             f"Who could vote: {who or 'not recorded'}.")]
    else:
        body = [h("p", None, "Turnout is not recorded in the guide's source for this election.",
                  c.cite(e.get("source_ids")), " ", _mark(page, e["status"])),
                h("p", None, f"Who could vote: {who}.") if who else None]
    if e["type"] in MUNICIPAL_TYPES:
        body.append(h("p", {"class": "tsec-lead"},
                      "Only voters in the area holding the election could vote, so this turnout is measured on a "
                      "smaller base than a countywide election's. Compare it with other elections of the same kind."))
    cmp_t = page.rel(EP.COMPARE_PATH["turnout"])
    body.append(h("p", {"class": "ep-more"}, h("a", {"href": f"{cmp_t}#turnout-denominators-all"},
                                               "Turnout in every election, each with its base")))
    out.append(T.tab_section("turnout", "Turnout", body))

    # ---- what was on the ballot
    if cs:
        by_level: dict[str, int] = {}
        for x in cs:
            by_level[level_of(x)] = by_level.get(level_of(x), 0) + 1
        ch = EP.href(page, eid, "contests")
        items = []
        for k, lab, _gs in CONTEST_LEVELS:
            if k in by_level:
                n = by_level[k]
                txt = f"{lab}: {n} contest{'s' if n != 1 else ''}"
                target = f"{ch}#lvl-{k}" if ch and not primary else ch
                items.append(h("li", None, h("a", {"href": target}, txt) if target else txt))
        lines = [h("p", None, f"{len(cs)} contest{'s' if len(cs) != 1 else ''} on this ballot in the guide's results"
                              + (", in " + " and ".join(party_title(p).replace(' primary', '') for p in
                                                       _party_order({x['party_primary'] for x in cs} - {""}))
                                 + " primaries" if primary and any(x["party_primary"] for x in cs) else "") + ".",
                   c.cite_compact(_src(*[x["rows"][0] for x in cs]))),
                 h("ul", {"class": "ep-levels"}, items)]
        races = election_races(ed, eid)
        if races:
            cnt = _counts(races)
            lines.append(h("p", None,
                           h("strong", None, f"{cnt['unc']} of the {len(races)} race{'s' if len(races) != 1 else ''}"),
                           " for local office decided inside the county had no contest: no more candidates on the "
                           f"ballot than seats to fill. {_contested(cnt)} were contested"
                           + (f" and {cnt['nc']} can't be measured (a seat count or a vote count is missing)"
                              if cnt["nc"] else "") + ". ",
                           _mark(page, "computed", "Counted from results.csv vote and seat counts, by the same rule "
                                                   "as Compare elections."),
                           " ", h("a", {"href": page.rel(EP.COMPARE_PATH["margins"])}, "Every election compared")))
        out.append(T.tab_section("ballot", "On the ballot", lines))

        # ---- the closest races
        close = sorted([r for r in races if "pts" in (r["m"] or {})], key=lambda r: (r["m"]["pts"], r["c"]["contest_id"]))
        if close:
            lis = []
            for r in close[:CLOSEST_N]:
                cc = r["c"]
                u = EP.contest_href(page, cc["contest_id"])
                nm = _search_text(cc["label"]) if cc.get("party_primary") else cc["label"]
                lis.append(h("li", {"class": "ep-close"},
                             h("p", {"class": "ep-close-h"}, h("a", {"href": u}, nm) if u else nm,
                               h("span", {"class": "ep-close-pts"}, " · " + _pts_text(r["m"]))),
                             h("p", {"class": "ep-close-who"}, _who(r["m"], bool(cc.get("party_primary"))), " ",
                               _mark(page, r["st"]))))
            out.append(T.tab_section("closest", "Closest races", h("ol", {"class": "ep-closest"}, lis),
                                     lead="Margin in points: the votes between the last candidate inside the seats and "
                                          "the next one, divided by all votes cast in the contest."))

    # ---- before and after
    nb = EP.neighbours(ed, eid)
    links = []
    for key, word in (("before", "Before"), ("after", "After")):
        x = nb[key]
        if x:
            links.append(h("li", None, h("span", {"class": "ep-nb-k"}, f"{word}: "),
                           h("a", {"href": page.rel(EP.path(x['election_id']))}, cap(EP.title(x))),
                           f" ({when_text(x)})"))
    for key, word in (("same_before", "Previous"), ("same_after", "Next")):
        x = nb[key]
        if x and x not in (nb["before"], nb["after"]):
            links.append(h("li", None, h("span", {"class": "ep-nb-k"},
                                         f"{word} {EP.TYPE_TITLE.get(e['type'], e['type'])}: "),
                           h("a", {"href": page.rel(EP.path(x['election_id']))}, cap(EP.title(x))),
                           f" ({when_text(x)})"))
    links.append(h("li", None, h("a", {"href": page.rel(EP.HUB + "#timeline")}, "Every election")))
    out.append(T.tab_section("around", "Elections before and after", h("ul", {"class": "ep-around"}, links)))

    if e.get("notes"):
        out.append(h("details", {"class": "ovw-notes ep-notes", "id": "notes-records"},
                     h("summary", None, "Notes from the records"),
                     h("p", None, e["notes"], c.cite(e.get("source_ids")))))
    page.add(*out)


# =========================================================================== Contests

def _on_map(ed) -> dict:
    got = ed.__dict__.get("_election_on_map")
    if got is None:
        got = race_by_contest(ed, EP._votes(ed))
        ed.__dict__["_election_on_map"] = got
    return got


def _level_blocks(page, cs, on_map, prefix: str, hx_level: str, hx_contest: str) -> list:
    groups: dict[str, list] = {}
    for x in cs:
        groups.setdefault(level_of(x), []).append(x)
    out = []
    order = {k: i for i, (k, _, _) in enumerate(CONTEST_LEVELS)}
    for k in sorted(groups, key=lambda k: order[k]):
        xs = sorted(groups[k], key=lambda x: GROUP_ORDER.get(classify(x)[0], 99))   # stable: canvass order inside
        sid = f"{prefix}lvl-{k}"
        n = len(xs)
        out.append(h("section", {"class": "ep-level", "id": sid, "aria-labelledby": f"{sid}-h"},
                     h(hx_level, {"class": "ep-level-h", "id": f"{sid}-h"}, LEVEL_LABEL[k],
                       h("span", {"class": "ep-level-n"}, f" · {n} contest{'s' if n != 1 else ''}")),
                     h("ul", {"class": "ep-list"}, [contest_item(page, x, hx_contest, on_map) for x in xs])))
    return out


def _contests(ed, e, page):
    eid = e["election_id"]
    cs = EP.contests(ed, eid)
    on_map = _on_map(ed)
    primary = e["type"] in EP.PRIMARY_TYPES
    n_off = sum(1 for x in cs if om.href(page, x["office_id"], "elections"))
    page.add(h("p", {"class": "tsec-lead"},
               f"{len(cs)} contest{'s' if len(cs) != 1 else ''} on this ballot in the guide's results, "
               + ("by party, then " if primary else "") + "by level of government. Candidates are in the order the "
               "source lists them. Each line shows who won and the margin; ",
               f"{n_off} contest{'s link' if n_off != 1 else ' links'} to every election for its office. "
               "Shares are of all votes cast in the contest."))
    # one status for every contest on the tab (the 2026 general: all unofficial): said once at the top, in words, and
    # not beside each contest (2026-11-18, "About these figures"; components.scope_note, drop_scoped)
    sts = {contest_status(x["rows"]) for x in cs}
    one = next(iter(sts)) if len(sts) == 1 and next(iter(sts)) in FIGURE_MARKS else None
    scope = scope_attrs(one) if one else {}
    if one:
        page.add(scope_note(one, "count on this tab"))
    elif "unofficial" in sts:
        # mixed (the 2026 general since the county canvass of 11/13/2026): the word at the top of the tab, the
        # status split in words from the rows (civic/results_status.py), and the unofficial contests keep their mark
        page.add(h("p", {"class": "fscope-line fscope-unofficial"},
                   h("strong", None, "Unofficial"), figure_mark("unofficial", scope=True),
                   ": the contests marked so are not final yet. ", RS.summary(ed, eid)))
    if primary:
        parties = _party_order({x["party_primary"] for x in cs})
        for p in parties:
            xs = [x for x in cs if x["party_primary"] == p]
            pk = party_key(p)
            page.add(h("section", {"class": "tsec ep-party", "id": pk, "aria-labelledby": f"{pk}-h", **scope},
                       h("h2", {"class": "tsec-h ep-party-h", "id": f"{pk}-h"}, party_title(p),
                         h("span", {"class": "ep-level-n"}, f" · {len(xs)} contest{'s' if len(xs) != 1 else ''}")),
                       _level_blocks(page, xs, on_map, f"{pk}-", "h3", "h4")))
    else:
        page.add(h("div", {"class": "ep-levels-all", **scope}, _level_blocks(page, cs, on_map, "", "h2", "h3")))
    page.add(h("p", {"class": "tnote"}, "Candidate order: Indiana places parties on the county ballot in order of each "
                                         "party's county vote for Secretary of State at the last election, and the "
                                         "county's reports follow that order.", page.cites.cite("IND-056"),
               " A contest decided by voters outside the county too (statewide offices and questions, state courts, "
               "legislative districts that cross the county line) shows the St. Joseph County tally, with the overall "
               "result beside it where the guide has it."))


# =========================================================================== Map

def _map(ed, e, page):
    eid = e["election_id"]
    shapes = ed.__dict__.get("_election_shapes")
    if shapes is None:
        shapes = load_shapes(ed)
        ed.__dict__["_election_shapes"] = shapes
    got = election_vote_map(page, ed, shapes, EP._votes(ed), eid)
    races = EP.map_races(ed, eid)
    if not got:
        page.add(h("p", None, "The map has no race of this election."))
        return
    mp, tables = got
    vintage = (shapes.get("vintage") or "").split(",", 1)[-1].strip()
    page.add(T.tab_section("areas-voted", "How areas voted",
                           h("p", {"class": "tsec-lead"},
                             f"The {len(races)} partisan races of the {EP.title(e)} on the map, by township, city or "
                             "town and precinct. Pick a race above the map. " + VOTE_CAVEAT,
                             page.cites.cite_compact(VOTE_SRC)),
                           mp,
                           h("p", {"class": "muted cmap-caveat"},
                             f"Boundaries are Census TIGER ({vintage}) and the Census 2020 voting districts. Color "
                             "shows the margin between the two leading parties in one past race, never a forecast. ",
                             h("a", {"href": page.rel(f"map/index.html#race-{races[0]['id']}")}, "Every year on the full map"), ".")))
    # the tables are the layer's numbers without JavaScript; with it they fold away under the map (folds.js)
    page.add(h("details", {"class": "fold-details ep-tables", "id": "map-tables", "data-fold": True, "open": True},
               h("summary", {"class": "fold-summary ep-tables-sum"}, "The numbers behind the map, as tables",
                 h("span", {"class": "fold-toggle", "aria-hidden": "true"})), tables))


# =========================================================================== Sources

def election_gaps(ed, e) -> list[dict]:
    """Gaps whose wording names this election's year, from the results and elections gap files; before 2010, the
    "results before 2010" gaps."""
    y = EP.year(e)
    out = ed.gaps(files=["gaps_results", "gaps_elections"], pattern=rf"\b{re.escape(y)}\b")
    if int(y) < 2010:
        out += [g for g in ed.gaps(files=["gaps_results", "gaps_elections"], pattern=r"before 2010|pre-2010|1963")
                if g not in out]
    return out


def _sources(ed, e, page):
    keys = EP.election_tabs(ed, e["election_id"])
    notes = ["Results are as the county's canvass or the cited source prints them, each with its status mark. Turnout "
             "is ballots cast divided by registered voters, as printed in the county's report."]
    if "contests" in keys:
        notes.append("A margin is the votes between the last candidate inside the seats and the next candidate, "
                     "divided by all votes cast in the contest; a race is uncontested when no more candidates than "
                     "seats were on the ballot. The same rule counts the races on Compare elections.")
    if "map" in keys:
        notes.append("The map's race rule and caveats are the full map's: partisan races on the general-election "
                     "ballots with precinct results, colored by the margin between the two leading parties.")
    page.add(*T.sources_body(page, election_gaps(ed, e), notes=notes, title=cap(EP.title(e))))


# =========================================================================== one election

def build_election(election_id: str, site, tab: str = "overview"):
    """Builds every tab of the election the first time any of its paths is asked for (one citation list), then
    returns the asked tab's page."""
    ed = site.ed
    done = site.__dict__.setdefault("_election_pages", {})
    if election_id not in done:
        e = ed.elections[election_id]
        keys = EP.election_tabs(ed, election_id)
        render = {"overview": partial(_overview, ed, e), "contests": partial(_contests, ed, e),
                  "map": partial(_map, ed, e), "sources": partial(_sources, ed, e)}
        done[election_id] = T.build_tabs(site, EP.base(election_id), keys, head_for(ed, e),
                                         {k: render[k] for k in keys})
    pages = done[election_id]
    if tab not in pages:
        raise KeyError(f"{election_id} has no {tab} tab")
    for p in pages.values():
        site.pages.setdefault(p.path, p)
    return pages[tab]


def _election_ids_all_editions() -> list[str]:
    root = Path(__file__).resolve().parents[3] / "data" / "editions"
    ids: list[str] = []
    for f in sorted(root.glob("*/elections.csv")):
        with open(f, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                if r["election_id"] not in ids:
                    ids.append(r["election_id"])
    return ids


PAGES = {}
for _eid in _election_ids_all_editions():
    for _k in ("overview", "contests", "map", "sources"):
        PAGES[EP.path(_eid, _k)] = partial(build_election, _eid, tab=_k)
