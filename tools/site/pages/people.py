"""Person pages and the People hub (phase 6, 2026-11-16; planning/design-direction-2026-11-16.md sections 0 and 2).

    people/index.html                  the People hub: a name box and filters, then everyone with a page, A to Z
    people/notable/index.html          the notable-people list (pages/community_history.py build_history_people)
    people/<id>/index.html             Overview: the same fields in the same order for everyone (offices now, offices
                                       before, races, party as recorded, campaign money, the notable-people list), then
                                       the offices held, the notable-people card (for the people the rules picked)
                                       and the names the records use
    people/<id>/elections/             every contest the person ran in, newest first, with its result bars
    people/<id>/money/                 their committees' money, from the campaign pages' own sums
    people/<id>/sources/               citations, gaps, and how the records were matched
    history/people/index.html          a forwarding page to people/notable/ (301 on Netlify)

Who is who, who gets a page and which tabs each person has come from civic/people.py (``registry``,
``person_tabs``); the sitemap and the search index read the same. Nothing here computes a figure: terms and results
are rows of terms.csv and results.csv, money is the race model of the campaign pages (pages/campaigns.py cf_all), the
committee histories of pages/money_history.py, the news figures of cf_reported.csv and the state filing-year sums of
money_history.legislator_years. Neutrality: every person gets the same fields in the same order, no adjectives,
nothing beyond what the records already on the site say; people are listed alphabetically, never by party or money.
"""
from __future__ import annotations

import re
from collections import OrderedDict
from collections.abc import Mapping
from functools import partial
from pathlib import Path

from civic import campaign_money as cm
from civic import election_pages as ep
from civic import offices as om
from civic import people as pm
from civic import tabs as T
from civic.charts import money_rows, period_money
from civic.components import (STATUS, data_table, name_with_party, party_label, see_all_fold, table_filter,
                              term_party)
from civic.data import SELECTED_BY_LABELS, fmt_date, split_ids
from civic.html import Markup, h, join, json_script

from . import money_history as mh
from civic.components import figure_mark, scope_attrs, scope_mark, scope_note
from .offices import PARTY_WORD, _contest_figure, _election_words, _fig, _filing_money_text, _mark, _src, year_head

LEVEL_WORD = {"county": "County and courts", "city": "Cities", "town": "Towns", "township": "Townships",
              "school": "School boards", "state": "State legislature"}
KIND_WORD = {"term": "officeholder records (terms.csv)", "result": "election results (results.csv)",
             "notable": "the notable-people profiles (people.csv)", "cf_local": "county campaign-finance reports",
             "cf_state": "state campaign-finance data", "cf_state_history": "state campaign-finance data",
             "cf_reported": "news-reported campaign figures"}


# =========================================================================== small helpers

def _plural(n: int, one: str, many: str | None = None) -> str:
    return f"{n} {one if n == 1 else (many or one + 's')}"


def _person(ed, pid):
    return pm.registry(ed).people[pid]


def _term_dates(ed, t) -> str:
    st = fmt_date(t["start"]) if t.get("start") else ""
    state = pm.term_state(ed, t)
    if state == "incoming":
        return f"Takes office {st}" if st else "Takes office (date not in sources)"
    end = ed.term_end(t)
    if state == "now":
        return (f"Since {st}" if st else "Start date not in sources") + "; in office"
    if t.get("end"):
        return f"{st or 'Start not in sources'} to {fmt_date(t['end'])}"
    if end:
        return f"{st or 'Start not in sources'} to {fmt_date(end.isoformat())} (scheduled end)"
    return f"From {st}" if st else "Dates not in sources"


def _how(t) -> str:
    how = SELECTED_BY_LABELS.get(t.get("selected_by", ""), t.get("selected_by") or "not stated in sources")
    first = SELECTED_BY_LABELS.get(t.get("first_selected_by", ""), t.get("first_selected_by") or "")
    if first and first != how:
        return f"By {how} (first chosen by {first})"
    return f"By {how}"


def _party_word(code: str) -> str:
    return party_label(code) if code else "Party not recorded"


def party_records(ed, pid) -> "OrderedDict[str, dict]":
    """Party as recorded, per kind of record: {code: {"terms": n, "ballots": n, "years": [..]}}, codes in first-seen
    order over time (oldest first). Never inferred: a blank party is its own entry ("")."""
    p = _person(ed, pid)
    out: OrderedDict = OrderedDict()
    recs = sorted([r for r in p.recs if r.kind in ("term", "result")], key=lambda r: (r.y0 or 0, r.kind))
    for r in recs:
        code = term_party(r.row) if r.kind == "term" else (r.party or "")
        d = out.setdefault(code, {"terms": 0, "ballots": 0, "years": []})
        d["terms" if r.kind == "term" else "ballots"] += 1
        if r.y0:
            d["years"].append(r.y0)
    return out


def _party_text(ed, pid) -> Markup | str:
    recs = party_records(ed, pid)
    if not recs:
        p = _person(ed, pid)
        if p.notable and p.notable.get("parties"):
            from .community_history import _parties
            return _parties(p.notable) + " (from the notable-people profile)"
        return "No party in the guide's records"
    parts = []
    for code, d in recs.items():
        bits = []
        if d["terms"]:
            bits.append(_plural(d["terms"], "term"))
        if d["ballots"]:
            bits.append(_plural(d["ballots"], "ballot line"))
        ys = sorted(d["years"])
        span = f", {pm.years_text(ys[0], ys[-1])}" if ys else ""
        parts.append(f"{_party_word(code)}: {' and '.join(bits)}{span}")
    if len(parts) == 1:
        return parts[0].split(":")[0] + " in every record (" + parts[0].split(": ", 1)[1] + ")"
    return h("span", None, "Recorded differently across records, each shown as recorded: ",
             h("ul", {"class": "pp-parties"}, [h("li", None, x) for x in parts]))


# =========================================================================== header

def head_for(ed, p) -> T.Head:
    cs = pm.contests(ed, p.pid)
    ts = pm.terms(ed, p.pid)
    facts = [pm.one_line(ed, p)]
    facts.append(_plural(len(ts), "term") + " in the officeholder records" if ts else "No term in the officeholder records")
    facts.append(_plural(len(cs), "contest") + " in the results" if cs else "No contest in the results")
    note = None
    if p.flags or p.maybe_same:
        note = "May be more than one person with this name: see Names in the records below."
    return T.Head(kind="Person", title=p.name, facts=facts, note=note)


# =========================================================================== Overview

def _office_cell(page, ed, oid, fallback=""):
    title = pm.office_title(ed, oid, fallback)
    u = om.href(page, oid)
    return h("a", {"href": u}, title) if u else title


def _overview(ed, pid, page):
    c = page.cites
    p = _person(ed, pid)
    keys = pm.person_tabs(ed, pid)
    ts = pm.terms(ed, pid)
    cs = pm.contests(ed, pid)
    now = [t for t in ts if pm.term_state(ed, t) in ("now", "incoming")]
    before = [t for t in ts if pm.term_state(ed, t) == "before"]

    def office_list(rows):
        if not rows:
            return "None in the guide's officeholder records"
        return join([h("span", {"class": "pp-off"}, _office_cell(page, ed, t["office_id"]),
                       f" ({_term_dates(ed, t)})") for t in rows], "; ")

    if cs:
        ys = sorted({x["contest"]["election_id"][:4] for x in cs})
        races = h("span", None, f"{_plural(len(cs), 'contest')}, {pm.years_text(ys[0], ys[-1])}. ",
                  h("a", {"href": page.rel(pm.path(pid, "elections"))}, "Every contest"))
    else:
        races = "None in the guide's results"
    m = pm.money_model(ed, pid)
    if "money" in keys:
        n_el = len({r["general_eid"][:4] for r, cand in m["races"] if cand["committees"]}
                   | {x[0]["election_id"][:4] for x in m["reported"]})
        bits = []
        if n_el:
            bits.append(_plural(n_el, "election") + " with local figures")
        if m["state"]:
            bits.append("state committee filings")
        if m["other"] and not n_el:
            bits.append("committee reports outside a race")
        money = h("span", None, ("; ".join(bits) or "Reports on file") + ". ",
                  h("a", {"href": page.rel(pm.path(pid, "money"))}, "Campaign money"))
    else:
        money = "None on record (no report, filing or news figure in the guide's files)"
    if p.notable is not None:
        from .community_history import CRITERIA_LABELS
        notable = h("span", None, "Picked by the published rules: ",
                    ", ".join(CRITERIA_LABELS.get(k, k) for k in p.notable["_crit"]), ". ",
                    h("a", {"href": page.rel(pm.NOTABLE)}, "The notable-people list"))
    else:
        notable = "Not picked by the published rules"
    fields = [("Offices now", office_list(now)), ("Offices before", office_list(before)),
              ("Races in the results", races), ("Party as recorded", _party_text(ed, pid)),
              ("Campaign money on record", money), ("Notable-people list", notable)]
    page.add(T.tab_section("summary", "In the guide's records",
                           h("dl", {"class": "ovw-facts pp-facts"}, [[h("dt", None, k), h("dd", None, v)]
                                                                     for k, v in fields])))

    if ts:
        rows = []
        for t in ts:
            rows.append(h("li", {"class": "pp-term"},
                          h("span", {"class": "pp-term-office"}, _office_cell(page, ed, t["office_id"])),
                          h("span", {"class": "pp-term-meta"}, _term_dates(ed, t), " · ", _how(t), " · ",
                            "Party as recorded: ", _party_word(term_party(t)), " ", _mark(page, t.get("status")),
                            _mark(page, "low") if t.get("confidence") == "low" else None),
                          c.cite(t.get("source_ids"))))
        page.add(T.tab_section("offices", "Offices held", h("ul", {"class": "pp-terms"}, rows),
                               lead="Newest first, as the guide's officeholder records give them."))

    if p.notable is not None:
        page.add(_card(ed, page, p))

    page.add(_names_section(ed, page, p))


def _card(ed, page, p) -> Markup:
    """The notable-people card's content, field for field as on the notable-people list (no vote counts or shares:
    community_history._card_summary leaves those sentences out)."""
    from civic.components import status_badge
    from .community_history import CRITERIA, CRITERIA_LABELS, _card_summary, _parties, _people_sources, _photo
    c = page.cites
    row = p.notable
    images = {r["image_id"]: r for r in ed.table("images")}
    summary = _card_summary(row)
    findings = row.get("documented_findings") or ""
    rules = h("ul", {"class": "pp-rules"},
              [h("li", None, h("span", {"class": "crit-tag mono"}, CRITERIA_LABELS.get(k, k)), " ", CRITERIA.get(k, ""))
               for k in row["_crit"]])
    body = h("div", {"class": "pp-card"},
             _photo(ed, page, row, images),
             h("dl", {"class": "person-fields"},
               h("dt", None, "Offices"), h("dd", None, row.get("offices_summary") or ""),
               h("dt", None, "Party"), h("dd", None, _parties(row) or "Party not documented in the sources"),
               h("dt", None, "Rules met"), h("dd", None, rules),
               h("dt", None, "Summary"),
               h("dd", None, summary if summary else h("span", {"class": "muted"},
                                                       "No profile written yet; offices and dates are from the "
                                                       "guide's officeholder records.")),
               h("dt", None, "Official findings"),
               h("dd", None, findings if findings else h("span", {"class": "muted"}, "None documented in the sources."))),
             h("p", {"class": "holder-badges"}, status_badge(row.get("status") or "secondary", page),
               c.cite(_people_sources(row))))
    if row.get("confidence") == "low":
        # the list shows a low-confidence person only as a flagged table row (no summary or findings): the same here
        from .community_history import _safe_note
        body = h("div", {"class": "pp-card pp-card-low"},
                 h("dl", {"class": "person-fields"},
                   h("dt", None, "Offices"), h("dd", None, row.get("offices_summary") or ""),
                   h("dt", None, "Party"), h("dd", None, _parties(row) or "Party not documented"),
                   h("dt", None, "Rules met"), h("dd", None, rules),
                   h("dt", None, "Why low confidence"), h("dd", None, _safe_note(row) or "See the cited sources.")),
                 h("p", {"class": "holder-badges"}, status_badge(row.get("status") or "secondary", page),
                   status_badge("low", page), c.cite(_people_sources(row))))
        return T.tab_section("notable", "On the notable-people list", body,
                             lead=h("span", None, "Recorded with low confidence, as in ",
                                    h("a", {"href": page.rel(pm.NOTABLE) + "#low-confidence"},
                                      "the notable-people list's flagged table"),
                                    ": the record behind the rule is thin. Being listed is not praise or criticism."))
    anchor = row["person_id"].lower() if row.get("person_id") else pm.slug(row["name"])
    return T.tab_section("notable", "On the notable-people list", body,
                         lead=h("span", None, "The same card as on ",
                                h("a", {"href": page.rel(pm.NOTABLE) + f"#person-{anchor}"}, "the notable-people list"),
                                ", where the rules are applied to everyone in the guide's data. Being listed is not "
                                "praise or criticism."))


def _names_section(ed, page, p) -> Markup:
    by = OrderedDict()
    for r in p.recs:
        by.setdefault(r.name, set()).add(KIND_WORD.get(r.kind, r.kind))
    items = [h("li", None, h("span", {"class": "pp-name"}, n), ": ", ", ".join(sorted(k))) for n, k in by.items()]
    notes = []
    for f in p.flags:
        notes.append(h("p", {"class": "pp-maybe"}, h("strong", None, "May be more than one person with this name. "),
                       f"The guide keeps these records on one page but {f}."))
    if p.maybe_same:
        reg = pm.registry(ed)
        links = []
        for oid in p.maybe_same:
            o = reg.people[oid]
            u = pm.href(page, oid) if o.page else None
            links.append(h("a", {"href": u}, o.name) if u else h("span", None, o.name + " (no page)"))
        notes.append(h("p", {"class": "pp-maybe"}, h("strong", None, "May be more than one person with this name. "),
                       "Other records name a person with the same surname and given name but a different middle name, "
                       "initial or suffix, so the guide does not join them: ", join(links, ", "), "."))
    lead = ("The name as each kind of record writes it. Records are joined only by the published matching rules "
            "(full name; middle names, initials and suffixes must agree); ")
    return T.tab_section("names", "Names in the records", notes, h("ul", {"class": "pp-names"}, items),
                         lead=h("span", None, lead, h("a", {"href": page.rel(pm.HUB) + "#rules"}, "how names are matched"),
                                "."))


# =========================================================================== Elections

def _own_result(ed, c, row) -> str:
    w = row.get("winner")
    prim = bool(c["party_primary"])
    try:
        pct = float(row["pct"]) if row.get("pct") else None
    except ValueError:
        pct = None
    share = f", {pct:.1f}%" if pct is not None else ""
    # a multi-county contest (2026-11-18, civic/overall.py): the result is the overall one; the county share is
    # labelled as the county's, and leading the county is never called winning
    from civic import overall as OV
    inf = OV.info(ed, c)
    county = ed.county_label
    if inf["basis"] == "overall":
        orow = inf["by"].get(row["candidate"])
        if orow is None or not inf["winners"]:
            return f"Overall result for this candidate not in the guide's data; {county} portion{share}"
        opct = OV._num(orow.get("overall_pct"))
        won = (orow.get("overall_winner") or "").upper() == "Y"
        head = (("Won the primary" if prim else "Elected") if won else
                ("Did not win the primary" if prim else "Not elected"))
        txt = f"{head} ({inf['label'].lower()}" + (f", {opct:.1f}%" if opct is not None else "") + ")"
        txt += f"; {county}: {pct:.1f}%" if pct is not None else ""
        if not won and row["candidate"] in OV.county_leaders(c):
            txt += f"; received the most votes in {county}"
        return txt
    if inf["basis"] in ("pending", "missing"):
        return (f"{county} portion{share}. "
                + (OV.PENDING_SENTENCE if inf["basis"] == "pending" else OV.MISSING_SENTENCE))
    if w == "Y":
        return ("Won the primary" if prim else "Elected") + share
    if w == "N":
        return ("Did not win the primary" if prim else "Not elected") + share
    return "Result not recorded in the guide's data" + share


def _elections(ed, pid, page):
    from .elections import contest_status
    p = _person(ed, pid)
    cs = pm.contests(ed, pid)
    by_year: OrderedDict = OrderedDict()
    for x in cs:
        by_year.setdefault(om.contest_year(ed, x["contest"]), []).append(x)
    years = list(by_year)
    span = years[0] if len(years) == 1 else f"{years[-1]} to {years[0]}"
    page.add(h("p", {"class": "tsec-lead"},
               f"{_plural(len(cs), 'contest')} in the guide's results, {span}. Newest first; candidates in the order "
               "the source lists them. The newest year's results are drawn; select any other row for its chart."))
    first = True
    for y, xs in by_year.items():
        items = []
        yscope, yline = year_head({contest_status(x["contest"]["rows"]) for x in xs}, len(xs), y)
        for x in xs:
            c, row = x["contest"], x["row"]
            st = contest_status(c["rows"])
            what = f"{_election_words(ed, c)} · {pm.contest_office_title(ed, c)}"
            mine = h("span", None, name_with_party(row["candidate"], row["party"]), ": ",
                     _own_result(ed, c, row))
            links = []
            ou = om.href(page, c.get("office_id") or "", "elections")
            if ou:
                links.append(h("a", {"href": f"{ou}#c-{c['contest_id']}"}, "The office's elections"))
            eu = ep.contest_href(page, c["contest_id"])
            if eu:
                links.append(h("a", {"href": eu}, "This contest on the election's page"))
            more = h("p", {"class": "er-more"}, join(links, " · ")) if links else None
            fig = _contest_figure(ed, page, c)
            # one mark per contest: the line's mark speaks for its chart and table (2026-11-18)
            if first:
                body = [h("div", {"class": "er-line"}, h("h3", {"class": "er-what"}, what),
                          h("span", {"class": "er-result"}, mine, scope_mark(st))),
                        fig, more]
            else:
                body = [h("details", {"class": "er-fold", "open": True, "data-fold": "contest"},
                          h("summary", {"class": "er-line"}, h("h3", {"class": "er-what"}, what),
                            h("span", {"class": "er-result"}, mine, scope_mark(st, link=False)),
                            h("span", {"class": "er-toggle"}, "Chart")),
                          fig, more)]
            items.append(h("li", {"class": "er-item", "id": f"c-{c['contest_id']}", **scope_attrs(st)}, body))
        page.add(h("section", {"class": "tsec er-year", "id": f"y{y}", "aria-labelledby": f"y{y}-h",
                               **scope_attrs(yscope)},
                   h("h2", {"class": "tsec-h", "id": f"y{y}-h"}, y),
                   yline,
                   h("ul", {"class": "er-list"}, items)))
        first = False
    if any(x["contest"].get("district") for x in cs):
        page.add(h("p", {"class": "tnote"}, "District lines are redrawn after each census, so an older race under the "
                                             "same district name may have covered a different area."))
    if p.maybe_same:
        page.add(h("p", {"class": "tnote"}, "Some records under a similar name are on other pages; see Names in the "
                                             "records on the Overview."))


# =========================================================================== Money

def _race_label(ed, race) -> str:
    oid = om.race_office_id(ed, race)
    return pm.office_title(ed, oid, race.get("office") or "")


def money_rows_for(ed, pid) -> list[dict]:
    """The rows of the person's money chart, newest first: one per race candidacy with reports (the race card's own
    sums), one per news-reported contest, one per committee cycle that no race counts. Each row: {year, label, kind,
    raised, spent, raised_text, spent_text, basis, status, sources, office_id, race}."""
    m = pm.money_model(ed, pid)
    out = []
    for race, cand in m["races"]:
        if not cand["committees"]:
            continue
        y = race["general_eid"][:4]
        out.append({"year": y, "label": f"{y} · {_race_label(ed, race)}", "kind": "race",
                    "sub": f"{race['spec']['cycle']} cycle, whole cycle",
                    "raised": cand["raised"], "spent": cand["spent"],
                    "raised_text": _filing_money_text(cand, "raised"), "spent_text": _filing_money_text(cand, "spent"),
                    "basis": "Sum of the reports on file (the race card's total)", "status": "computed",
                    "sources": "CFM-010", "office_id": om.race_office_id(ed, race), "race": race, "cand": cand})
    for contest, rows in m["reported"]:
        y = om.contest_year(ed, contest)
        rc, rw, _rr = _fig(rows, "raised")
        sc, sw, _sr = _fig(rows, "spent")
        no = next((x for x in rows if x["figure"] == "no report"), None)
        which = (f"{PARTY_WORD.get(contest['party_primary'], party_label(contest['party_primary']))} primary"
                 if contest["party_primary"]
                 else "general election")
        st = rows[0]["status"]
        out.append({"year": y, "label": f"{y} · {pm.contest_office_title(ed, contest)}", "kind": "reported",
                    "sub": f"{which}, as reported in the news",
                    "raised": rc, "spent": sc,
                    "raised_text": rw or ("did not file a report (per the article)" if no else "not reported"),
                    "spent_text": sw or ("did not file a report (per the article)" if no else "not reported"),
                    "basis": "As reported: " + "; ".join(dict.fromkeys(x["covers"] for x in rows)), "status": st,
                    "sources": _src(rows), "office_id": contest.get("office_id") or "", "race": None, "contest": contest})
    for key, part in m["other"]:
        s = part["s"]
        if part["spec"] is None:
            continue
        label = mh.index(ed)["rows"][key][0]["_label"]
        out.append({"year": part["cycle"][:4], "label": f"{part['cycle'][:4]} · {label}", "kind": "other",
                    "sub": f"{part['cycle']} cycle; reports not counted in any race",
                    "raised": s["raised"], "spent": s["spent"],
                    "raised_text": cm.usd(s["raised"]) if s["raised"] is not None else "not added up",
                    "spent_text": cm.usd(s["spent"]) if s["spent"] is not None else "not added up",
                    "basis": "Sum of the committee's other reports, by the same rules", "status": "computed",
                    "sources": "CFM-010", "office_id": "", "race": None, "key": key})
    out.sort(key=lambda r: (r["year"], {"race": 2, "reported": 1, "other": 0}[r["kind"]]), reverse=True)
    return out


def _money(ed, pid, page):
    c = page.cites
    p = _person(ed, pid)
    m = pm.money_model(ed, pid)
    rows = money_rows_for(ed, pid)
    table = []
    if rows:
        vals = [v for r in rows for v in (r["raised"], r["spent"]) if v]
        vmax = max(vals or [100])
        page.add(h("div", {"class": "mt-key"},
                   h("ul", {"class": "legend"},
                     h("li", None, h("span", {"class": "key key-rect m-accent", "aria-hidden": "true"}), "Raised"),
                     h("li", None, h("span", {"class": "key key-rect m-spent", "aria-hidden": "true"}), "Spent")),
                   h("p", {"class": "tsec-lead"},
                     "One bar pair per election, on one scale, newest first. From 2023 on, the figures are the "
                     "guide's sums of the reports the county posts (the same totals as the office's Money tab and "
                     "the race card); earlier figures are as news coverage reported them.")))
        chart_rows = [{"name": r["label"], "sub": r["sub"], "raised": r["raised"], "spent": r["spent"],
                       "raised_text": r["raised_text"], "spent_text": r["spent_text"], "tip": r["basis"]}
                      for r in rows]
        page.add(T.tab_section("by-election", "Campaign money by election",
                               money_rows("pp-money", f"{p.name}: campaign money by election", chart_rows, vmax=vmax,
                                          subtitle="Raised and spent, as on the office pages", page=page,
                                          cite=c.cite_compact(";".join(dict.fromkeys(
                                              s for r in rows for s in split_ids(r["sources"])))))))
        details = []
        for r in rows:
            links = []
            # 2026-11-18 ("About these figures"): a figure that is a floor is marked * right after it: this person's own
            # figures when one of their expected reports is not on file, else the race card's total (all candidates)
            own_floor = bool(r["race"] is not None and (r["cand"].get("missing") or []))
            race_floor = bool(r["race"] is not None and not r["race"]["complete"] and not own_floor)
            if r["office_id"]:
                u = om.href(page, r["office_id"], "money")
                if u:
                    links.append(h("a", {"href": f"{u}#y{r['year']}"}, "The office's Money tab"))
            if r["race"] is not None:
                area = cm.area_path(r["race"]["area"])
                if area in page.site.by_path:
                    links.append(h("span", None, h("a", {"href": page.rel(area) + f"#r-{r['race']['id']}"},
                                                    "The race card"),
                                   figure_mark("incomplete", "The race's total, all candidates together, covers only "
                                                             "the reports on file.") if race_floor else None))
                elif race_floor:
                    links.append(h("span", None, "The race's total, all candidates",
                                   figure_mark("incomplete", "It covers only the reports on file.")))
                for s in r["cand"]["committees"]:
                    lk = mh.link(ed, page, s["key"], f"{s['label']}, money history")
                    if lk:
                        links.append(lk)
            if r["kind"] == "other":
                lk = mh.link(ed, page, r["key"], "This committee's money history")
                if lk:
                    links.append(lk)
            details.append(h("li", None, h("strong", None, r["label"]), f" ({r['sub']}): ",
                             f"raised {r['raised_text']}, spent {r['spent_text']}",
                             figure_mark("incomplete") if own_floor else None, ". ", _mark(page, r["status"]),
                             c.cite(r["sources"]), h("br", None) if links else None, join(links, " · ")))
            table.append([r["year"], r["label"].split(" · ", 1)[1], r["sub"], r["raised_text"], r["spent_text"],
                          r["basis"], STATUS.get(r["status"], (r["status"],))[0].capitalize()])
        page.add(T.tab_section("each", "Each election's figures and where they come from",
                               h("ul", {"class": "pp-money-list"}, details)))
    none = [(race, cand) for race, cand in m["races"] if not cand["committees"]]
    if none:
        page.add(T.tab_section("no-reports", "Races with no report on file",
                               h("ul", {"class": "mt-none"},
                                 [h("li", None, f"{race['general_eid'][:4]} · {_race_label(ed, race)}: no reports on file "
                                                "for this candidate (not the same as $0).") for race, _c in none])))
    for lp in m["state"]:
        by_year = mh.legislator_years(lp)
        points = [{"x": str(y), "raised": d["r"] if d["re"] else None, "spent": d["e"] if d["ee"] else None,
                   "tip": f"Filed in {y}"} for y, d in by_year.items()]
        for y, d in by_year.items():
            table.append([str(y), "State committees", "filing year (state data)",
                          cm.usd(d["r"]) if d["re"] else "not in the data", cm.usd(d["e"]) if d["ee"] else "not in the data",
                          "Sum of the state's bulk-data rows filed that year", "Computed"])
        more = mh.legislator_href(ed, page, lp["name"])
        page.add(T.tab_section(
            "state", "Committees filing with the state",
            h("aside", {"class": "callout callout-note mt-basis"},
              h("p", None, h("strong", None, "A different basis from the local races. "),
                "Receipts and expenditures on the reports the person's committees filed with the state in each calendar "
                "year (all of their committees), not election-cycle totals; the latest year is partial.",
                c.cite("MON-020;MON-021;MON-022"))),
            period_money(f"pp-{lp['anchor']}", f"{lp['name']}: receipts and expenditures by filing year", points,
                         subtitle=f"{_plural(len(lp['years']), 'filing year')}, "
                                  f"{pm.years_text(lp['years'][0], lp['years'][-1])}",
                         words={"raised": "Receipts in the year", "spent": "Expenditures in the year",
                                "missing": "not in the data", "tip_raised": "Receipts", "tip_spent": "Expenditures"},
                         page=page, cite=c.cite_compact(_src(lp["rows"]))),
            h("p", {"class": "mt-links"}, h("a", {"href": more}, "Every committee row (state legislators' page)"))
            if more else None))
    if table:
        page.add(see_all_fold("money-table", len(table),
                              data_table("money-figures", ["Year", "Office or committee", "Election", "Raised",
                                                           "Spent", "Basis", "Status"], table,
                                         caption=f"{p.name}: every money figure", numeric=(3, 4), min_width="56rem"),
                              noun="figure", label="Show the table: every figure on this page"))


# =========================================================================== Sources

def person_gaps(ed, p) -> list[dict]:
    """Gaps whose wording names this person in full (any of the strings the records use)."""
    names = [n for n in p.names if not pm.is_partial(n)]
    if not names:
        return []
    rx = re.compile("|".join(rf"\b{re.escape(pm.clean(n))}\b" for n in names), re.I)
    return [g for g in ed.gaps_rows if rx.search(f"{g.get('item', '')} {g.get('why_missing', '')}")]


def _sources(ed, pid, page):
    p = _person(ed, pid)
    notes = [h("span", None, "This page joins the records that name ", _plural(len(p.names), "spelling") + ": ",
               "; ".join(p.names), ". Records are joined only by the published matching rules (",
               h("a", {"href": page.rel(pm.HUB) + "#rules"}, "how names are matched"), ").")]
    if "money" in pm.person_tabs(ed, pid):
        notes.append(mh.POSTED_FROM)
    page.add(*T.sources_body(page, person_gaps(ed, p), notes=notes, title=p.name))


# =========================================================================== one person

def build_person(pid: str, site, tab: str = "overview"):
    ed = site.ed
    done = site.__dict__.setdefault("_person_pages", {})
    if pid not in done:
        p = _person(ed, pid)
        keys = pm.person_tabs(ed, pid)
        render = {"overview": partial(_overview, ed, pid), "elections": partial(_elections, ed, pid),
                  "money": partial(_money, ed, pid), "sources": partial(_sources, ed, pid)}
        done[pid] = T.build_tabs(site, pm.base(pid), keys, head_for(ed, p), {k: render[k] for k in keys})
    pages = done[pid]
    if tab not in pages:
        raise KeyError(f"{pid} has no {tab} tab")
    for _k, pg in pages.items():
        site.pages.setdefault(pg.path, pg)
    return pages[tab]


# =========================================================================== hub

def _letter(p) -> str:
    s = cm.surname(pm.clean(p.name)) or pm.clean(p.name).lower()
    ch = (s[:1] or "#").upper()
    return ch if ch.isalpha() else "#"


def build_hub(site):
    ed = site.ed
    reg = pm.registry(ed)
    page = site.page(pm.HUB, body_class="thing-page")
    c = page.cites
    people = pm.paged(ed)
    n_now = sum(1 for p in people if "now" in pm.status_tokens(ed, p).split())
    page.add(h("header", {"class": "thing-head hub-head"},
               page.crumb_nav(),
               h("h1", {"class": "thing-title"}, "People"),
               h("p", {"class": "thing-facts"},
                 f"{len(people)} people with a page: everyone in the guide's officeholder records and the candidates "
                 f"who meet the published threshold ({n_now} hold an office now). Alphabetical by surname. "
                 f"{len(reg.below)} more candidates are listed below without a page.")))
    letters: OrderedDict = OrderedDict()
    for p in people:
        letters.setdefault(_letter(p), []).append(p)
    filt = table_filter("people-all",
                        [{"key": "status", "label": "Office", "all": "Everyone", "tokens": True,
                          "options": [("now", "Holds office now"), ("held", "Has held office"),
                                      ("candidate", "Candidate (no office in the records)")]},
                         {"key": "level", "label": "Level", "all": "Every level", "tokens": True,
                          "options": [(k, v) for k, v in LEVEL_WORD.items()]},
                         {"key": "notable", "label": "Notable (by the published rules)", "all": "Either",
                          "options": [("yes", "On the notable-people list"), ("no", "Not on it")]}],
                        len(people), noun="name", search="Name", label="Find a person",
                        search_first=True)
    page.add(h("section", {"class": "tsec pph-find", "id": "find", "aria-labelledby": "find-h"},
               h("h2", {"class": "tsec-h visually-hidden", "id": "find-h"}, "Find a person"),
               filt,
               h("nav", {"class": "pph-letters", "aria-label": "Surnames by first letter"},
                 h("ul", None, [h("li", None, h("a", {"href": f"#letter-{k.lower() if k != '#' else 'other'}"}, k))
                                for k in letters]))))
    groups = []
    for k, ps in letters.items():
        lid = f"letter-{k.lower() if k != '#' else 'other'}"
        items = []
        for p in ps:
            st = pm.status_tokens(ed, p)
            items.append(h("li", {"class": "pph-row", "data-tf-row": True, "data-tf-status": st,
                                  "data-tf-level": pm.level_tokens(ed, p),
                                  "data-tf-notable": "yes" if p.notable is not None else "no",
                                  "data-tf-text": " ".join([p.name] + [n for n in p.names if n != p.name])},
                           h("a", {"class": "pph-name", "href": page.rel(pm.path(p.pid))}, p.name),
                           h("span", {"class": "pph-sub"}, pm.one_line(ed, p))))
        groups.append(h("details", {"class": "pph-letter", "id": lid, "data-tf-group": True, "data-fold": "letter",
                                    "open": True},
                        h("summary", {"class": "pph-letter-sum"},
                          h("span", {"class": "pph-letter-k"}, k), h("span", {"class": "pph-letter-n"},
                                                                       _plural(len(ps), "person", "people"))),
                        h("ul", {"class": "pph-list"}, items)))
    page.add(h("section", {"class": "tsec pph-all-sec", "id": "list", "aria-labelledby": "list-h"},
               h("h2", {"class": "tsec-h", "id": "list-h"}, "Everyone with a page, A to Z"),
               h("p", {"class": "tf-empty muted", "data-tf-empty": "people-all", "hidden": True, "role": "status"},
                 "No one matches. Use Reset filters to see everyone."),
               h("div", {"class": "pph-all", "id": "people-all", "data-tf-deep": True}, groups)))

    # candidates without a page
    below = sorted(reg.below, key=lambda x: (cm.surname(pm.clean(x[0])) or x[0].lower(), x[0]))
    lis = []
    for name, cids in below:
        links = []
        for cid in cids:
            cc = ed.contests.get(cid)
            u = ep.contest_href(page, cid)
            label = f"{cid[:4]} {pm.contest_office_title(ed, cc)}" if cc else cid
            links.append(h("a", {"href": u}, label) if u else label)
        lis.append(h("li", None, h("span", {"class": "pph-name"}, name), ": ", join(links, "; ")))
    page.add(h("details", {"class": "fold-details see-all pph-below", "id": "below", "open": True, "data-fold": "see-all"},
               h("summary", {"class": "fold-summary see-all-summary"},
                 h("span", {"class": "see-all-label"}, f"Candidates without a page ({len(below)})"),
                 h("span", {"class": "fold-toggle", "aria-hidden": "true"})),
               h("div", {"class": "fold-body"},
                 h("p", None, "Candidates in the guide's results who are below the threshold: on a primary ballot only "
                              "with no campaign money on record, on a statewide ballot (the county's tally only), or "
                              "named in the record by a surname or initials alone. Each links to the contest."),
                 h("ul", {"class": "pph-below-list"}, lis))))

    # the rules
    thr = h("ol", {"class": "pph-rules"}, [h("li", None, t) for _k, t in pm.THRESHOLD])
    ident = h("ol", {"class": "pph-rules"}, [h("li", None, t) for t in pm.RULES_TEXT])
    page.add(T.tab_section("rules", "Who gets a page, and how names are matched",
                           h("p", None, "A person gets a page when the guide's records show at least one of these:"),
                           thr,
                           h("p", None, "The records carry no person ids, so the guide decides who is who from the "
                                        "names alone, the same way for everyone:"),
                           ident,
                           h("p", None, "Every page shows the same fields in the same order, and nothing beyond what "
                                        "the records on this site say. The ",
                             h("a", {"href": page.rel(pm.NOTABLE)}, "notable-people list"),
                             " has its own published rules."),
                           h("p", {"class": "tnote"}, "Names from the officeholder records, the election results, the "
                                                      "notable-people profiles and the campaign-finance files.",
                             c.cite_compact(";".join(dict.fromkeys(
                                 s for t in ed.tables["terms"] for s in split_ids(t.get("source_ids")))))
                             if ed.tables["terms"] else None)))
    page.finish(gaps=None)
    return page


# =========================================================================== history/people/ (moved)

def build_old_notable(site):
    """history/people/ moved to people/notable/ (2026-11-16): a forwarding page. Every old id is on the new page with
    the same id (the cards keep person-<id>, the sections rules, people, low-confidence, turning-points, distribution,
    gaps, sources), so the map sends each one there unchanged."""
    from .governments import forward_page
    ed = site.ed
    parts = [("rules", "Selection rules", pm.NOTABLE + "#rules"), ("people", "The people", pm.NOTABLE + "#people"),
             ("low-confidence", "Recorded with low confidence", pm.NOTABLE + "#low-confidence"),
             ("turning-points", "Turning-point names", pm.NOTABLE + "#turning-points"),
             ("distribution", "Who the rules picked, by party and era", pm.NOTABLE + "#distribution")]
    reg = pm.registry(ed)
    from .community_history import notable_rows
    for row in notable_rows(ed):
        anchor = row["person_id"].lower() if row.get("person_id") else pm.slug(row["name"])
        p = reg.person(row["name"])
        if p is not None and p.page:
            parts.append((f"person-{anchor}", row["name"], pm.path(p.pid)))

    def moved(page):
        return {"to": page.rel(pm.NOTABLE)}
    return forward_page(site, pm.OLD_NOTABLE, pm.NOTABLE, "Notable people", moved, parts=parts)


def build_notable(site):
    from .community_history import build_history_people
    return build_history_people(site)


# =========================================================================== registration

class _PersonPages(Mapping):
    """PAGES for build.py: the hub, the notable-people view, the forwarding page and every person tab. Person ids come
    from civic/people.py, which needs an edition: they are read from the editions whose sitemap was built in this
    process (Site() builds it before build.py discovers the page modules), else from every edition on disk."""

    _fns: dict = {}       # one builder object per path, so registering twice finds the same function

    def _all(self) -> dict:
        out = {pm.HUB: build_hub, pm.NOTABLE: build_notable, pm.OLD_NOTABLE: build_old_notable}
        for pid in sorted(_ids()):
            for k in T.TAB_ORDER:
                path = pm.path(pid, k)
                if path not in self._fns:
                    self._fns[path] = partial(build_person, pid, tab=k)
                out[path] = self._fns[path]
        return out

    def __getitem__(self, key):
        return self._all()[key]

    def __iter__(self):
        return iter(self._all())

    def __len__(self):
        return len(self._all())

    def items(self):
        return self._all().items()


def _ids() -> set:
    if pm.KNOWN_IDS:
        return set(pm.KNOWN_IDS)
    from civic.data import Edition
    root = Path(__file__).resolve().parents[3]
    ids = set()
    for d in sorted((root / "data" / "editions").glob("*/edition.json")):
        ed = Edition.load(root, d.parent.name)
        ids |= {p.pid for p in pm.paged(ed)}
    return ids


PAGES = _PersonPages()
