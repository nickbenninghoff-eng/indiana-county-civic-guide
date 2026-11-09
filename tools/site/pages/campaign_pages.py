"""Campaign money by place (money/campaigns/).

    money/campaigns/index.html                  short intro, the campaign-money map with a race-type filter, the list of
                                                every area, short "about these figures" notes (anchors #obligations,
                                                #public and #method stay here for inbound links)
    money/campaigns/<area>/index.html           one government: each race of the 2023, 2024 and 2026 ballots (newest
                                                election first), its candidates in ballot order with whole-campaign
                                                figures, every report behind them, the like-for-like pre-election
                                                comparison, other reports for its offices, its large contributions
    money/campaigns/state-legislature/index.html   state legislators' committees by filing year (a different basis)
    money/campaigns/other-committees/index.html    party, PAC and issue committees; filings naming no office or government

The how-it-works and every-filing pages are in pages/campaigns.py, which also builds the shared model (cf_all).
Figures come from civic/campaign_money.py (rules on money/campaigns/how-it-works/#adding); the map from
civic/campaign_map.py. Neutrality rules of the campaign pages apply: people in ballot order, never ranked by money,
no party colour beyond the guide's standard name tags, sums marked COMPUTED.
"""
from __future__ import annotations

import csv
import re
from collections import Counter, OrderedDict, defaultdict
from functools import partial
from pathlib import Path

from civic import campaign_money as cm
from civic.campaign_map import (NO_SHAPES, SET_NOTES, _same_page, area_campaign_map, area_layers, campaign_map,
                                district_sets, load_district_shapes, map_layers, office_tab, record_line,
                                state_campaign_map)
from civic.components import (callout, data_table, entity_list, name_with_form_party, name_with_party, party_label, scope_badge,
                              section, status_badge)
from civic.data import fmt_date, split_ids
from civic.holder_rows import holder_state
from civic.related import contest_href
from civic.html import Markup, h
from civic.map import load_shapes
from civic.preselect import here_attrs, here_slot

from . import campaigns as cf
from . import money_history as mh
from .elections import candidates as el_candidates, is_writein_total, margin as el_margin

MAP_SOURCES = "MAP-020;MAP-021;MAP-024;MAP-025;MAP-026;MAP-028;MAP-029;MAP-030;MAP-034"
BALLOT_WORDS = {"general": "General-election ballot", "primary": "Primary ballot only",
                "none": "Not on the ballot in the guide's results"}
WHY = {"replaced": "No: replaced by its amendment", "inside": "No: inside another report's period",
       "duplicate": "No: the same report filed twice", "no-period": "No: no period written"}


# --------------------------------------------------------------------------- small helpers
def _cycle_year(cycle: str) -> str:
    return cycle[:4]


def _cand_name(ed, c: dict, cycle: str) -> Markup:
    if c["party_from"] == "ballot":
        return name_with_party(c["name"], c["party"])
    return name_with_form_party(c["name"], c["party"] if c["party_from"] == "form" else "",
                                cf._records_party(ed, c["name"], _cycle_year(cycle)))


def _el_title(ed, eid: str) -> str:
    el = ed.elections.get(eid) or {}
    return f"{eid[:4]} general election" + (f" ({fmt_date(el['date'])})" if el.get("date") else "")


def _party_text(x: dict) -> str:
    """By-party sums of a race or an area, each with how many of the party's candidates it covers."""
    return "; ".join(cm.party_parts(x["by_party"], x["party_counts"], party_label))


def _cycle_words(spec: dict) -> str:
    names = [cm.slot_label(x, spec) for x in cm.expected_slots(spec, cm.EXPECTED.get(spec["cycle"], []))]
    return f"the {spec['cycle']} cycle" + (f" (expected: {', '.join(names)} reports)" if names else "")


def _in_totals(it: dict, s: dict) -> str:
    if not it["counted"]:
        return WHY.get(it["why"], "No")
    r = it["row"]
    if r.get("transcription_status") == "unreadable":
        return "No: can't be read"
    y = cm.money_year(r)
    b = next((b for b in s.get("basis", []) if b["year"] == y and b["word"] == "spent"), None)
    if s["spent"] is None:
        return "Not added up (overlapping reports)"
    if b is None:
        return "Yes"
    if b["how"] == "periods":
        return "Yes (this period)" if r["filing_id"] in b["ids"] else "No: line blank"
    if b["ids"] == [r["filing_id"]]:
        return f"Yes (its {y} year-to-date column)"
    return f"Covered by the {y} year-to-date figure"


def _reports_table(ed, page, tid: str, s: dict, spec: dict | None) -> Markup:
    rows = []
    for it in s["items"]:
        r = it["row"]
        slot = cm.slot_label(it["slot"], spec) if spec and it["slot"] else "Period not placed"
        rows.append([doc_or_type(r), slot, cf.period_text(r), cf.money(cf._num(r["receipts_period"])),
                     cf.money(cf._num(r["expenditures_period"])), cf.money(cf._num(r["receipts_ytd"])),
                     cf.money(cf._num(r["expenditures_ytd"])), cf.money(cf._num(r["cash_end_period"])),
                     cf.cf_badge_short(r["transcription_status"], page),
                     _in_totals(it, s), cf.doc_link(ed, r)])
    return data_table(tid, ["Report (box marked)", "Counts as", "Period", "Receipts this period",
                            "Expenditures this period", "Receipts year to date", "Expenditures year to date",
                            "Cash on hand at close", "Status", "In the totals", "Form"], rows,
                      caption=f"Reports on file: {s.get('label', '')}", numeric=(3, 4, 5, 6, 7), min_width="72rem",
                      copy=False)


def doc_or_type(r: dict) -> str:
    t = r["report_type"] or "No report type marked"
    return t + (" (amended)" if (r.get("amended") or "").lower() == "yes" else "")


def _notes(s: dict) -> Markup | None:
    lines = list(s["notes"])
    for it in s["items"]:
        for n in it["notes"]:
            lines.append(f"Doc {cm._doc(it['row'])}: {n}")
        cn = cf._clean_note(it["row"].get("notes", ""))
        if cn:
            lines.append(f"Doc {cm._doc(it['row'])}, transcription note: {cn}")
    if not lines:
        return None
    return h("ul", {"class": "cf-notes"}, [h("li", None, x) for x in lines])


def _on_file_text(s: dict, spec: dict) -> str:
    exp = s["expected"]
    got = [x for x in exp if x in s["on_file"]]
    n = len(s["items"])
    t = f"{n} report{'s' if n != 1 else ''} on file"
    if exp:
        t += f"; {len(got)} of {len(exp)} expected"
    if s["missing"]:
        t += " (not on file: " + ", ".join(cm.slot_label(m, spec) for m in s["missing"]) + ")"
    return t


def _date_subs(s: dict) -> list:
    """Visible lines in the candidate's row for any report whose dates the guide reads differently from the form,
    doubts, or finds in conflict with the figures (the full notes are under the reports table)."""
    out = []
    for x in s.get("moved_out", []):
        out.append(f"Doc {cm._doc(x)} is counted in the {cm.money_cycle(x)} cycle: its transcription note says "
                   f"{cm.date_fix(x)['note']}.")
    for it in s["items"]:
        fx = cm.date_fix(it["row"])
        if fx and fx["kind"] in ("year", "from", "to"):
            out.append(f"Doc {cm._doc(it['row'])}: dates read as its transcription note says ({fx['note']}).")
    out += [cm.ytd_line(u) for u in cm.ytd_uses([s])]
    if "date-conflict" in s["flags"]:
        ids = [cm._doc(it["row"]) for it in s["items"] if it["conflict"]]
        out.append(f"Docs {', '.join(ids)}: the written dates disagree with the figures or cash; both are counted.")
    if "date-doubt" in s["flags"]:
        ids = [cm._doc(it["row"]) for it in s["items"] if (cm.date_fix(it["row"]) or {}).get("kind") == "doubt"]
        out.append(f"Doc {', '.join(ids)}: a year on the form may be miswritten; dates kept as written.")
    return [h("span", {"class": "cf-sub cf-date-note"}, x) for x in out]


def _money_cell(v, s_list, word) -> str:
    if not s_list:
        return "no reports on file"
    if v is None:
        return "not added up (overlapping reports)"
    ytd = any(b["how"] == "ytd" and b.get("differs") and b["word"] == word for s in s_list for b in s.get("basis", []))
    return cm.usd(v) + (" (uses a year-to-date figure)" if ytd else "")


# --------------------------------------------------------------------------- one race
def race_block(ed, page, race: dict) -> Markup:
    c = page.cites
    spec = race["spec"]
    meta = [_el_title(ed, race["general_eid"])]
    if not race["on_general"]:
        meta.append("primary only (no general-election contest in the guide's results)")
    if race["vote_for"] > 1:
        meta.append(f"vote for {race['vote_for']}")
    if race["uncontested"]:
        meta.append("uncontested on the general-election ballot")
    if race["district"]:
        meta.append(f"district {race['district']}")
    rows = []
    for cand in race["candidates"]:
        cs = cand["committees"]
        if cs:
            reports = [h("span", {"class": "cf-sub cf-sub-strong"}, s["label"]) for s in cs]
            reports = [[r, h("span", {"class": "cf-sub"}, _on_file_text(s, spec)), _date_subs(s),
                        h("span", {"class": "cf-sub"}, mh.link(ed, page, s["key"]))]
                       for r, s in zip(reports, cs)]
        else:
            reports = ["No reports on file" + (f" for this office. Reports under another office ({cand['elsewhere']}) "
                                               "count in that race." if cand["elsewhere"] else ".")]
            other = mh.same_name_links(ed, page, cand["name"])
            if other:
                reports.append(h("span", {"class": "cf-sub"}, "Filed in another cycle or for another office: ",
                                 [[", " if i else "", x] for i, x in enumerate(other)]))
        if cand.get("spelled"):
            reports.append(h("span", {"class": "cf-sub"}, f"Name on the form: {cand['spelled']}"))
        cash = cm.usd(cand["cash"]) if cand["cash"] is not None else (
            "; ".join(s["cash_why"] for s in cs if s["cash_why"]) or "not shown") if cs else "no reports on file"
        rows.append([_cand_name(ed, cand, race["cycle"]), BALLOT_WORDS[cand["ballot"]], reports,
                     _money_cell(cand["spent"], cs, "spent"), _money_cell(cand["raised"], cs, "raised"), cash])
    tid = f"rt-{race['id']}"
    table = data_table(tid, ["Candidate (ballot order)", "Ballot", "Committee and reports", "Spent in the cycle",
                             "Raised in the cycle", "Cash on hand, latest report"], rows,
                       caption=f"{race['office']}: whole-campaign figures by candidate", numeric=(3, 4, 5),
                       min_width="58rem")
    if race["spent"] is not None:
        total = h("p", {"class": "cf-race-total"}, h("strong", None, "All candidates: "),
                  f"{cm.usd(race['spent'])} spent, {cm.usd(race['raised'])} raised"
                  + (f", reports through {fmt_date(race['latest_to'])}" if race["latest_to"] else "") + ". ",
                  status_badge("computed", page, "Sums of the reports in the tables below, by the rules on How "
                                                 "campaign finance reporting works."), c.cite("CFM-010"),
                  h("span", {"class": "cf-sub"}, "By party: " + _party_text(race)) if race["by_party"] else None)
    else:
        total = h("p", {"class": "cf-race-total"}, h("strong", None, "No reports on file "),
                  "for any candidate in this race. That is not the same as $0.")
    if race["complete"]:
        rec = h("p", {"class": "cf-record cf-record-ok"}, "Complete: every expected report is on file for every candidate.")
    else:
        rec = h("div", {"class": "cf-record"},
                h("p", None, h("strong", None, "Incomplete. "), "The total covers only the reports on file, so it is a "
                                                                "floor, not a final figure."),
                h("ul", None, [h("li", None, x) for x in race["reasons"]]) if race["reasons"] else None)
    details = []
    for i, cand in enumerate(race["candidates"]):
        for j, s in enumerate(cand["committees"]):
            details.append(mh.render(ed, page, s["key"]))
            details.append(h("details", {"class": "cf-reports"},
                             h("summary", None, f"Reports: {cand['name']}, {s['label']} ({len(s['items'])})"),
                             _reports_table(ed, page, f"{tid}-c{i}-{j}", s, spec), _notes(s)))
    return h("article", {"class": "cf-race-card", "id": f"r-{race['id']}"},
             h("h3", None, race["office"]),
             h("p", {"class": "cf-race-meta mono"}, " · ".join(meta)),
             h("p", {"class": "cf-race-meta"}, f"Counts every report of {_cycle_words(spec)}."),
             total, rec, mh.seat_block(ed, page, race), table, details)


# --------------------------------------------------------------------------- other filings (no race)
def committee_cycles(ed, page, rows: list[dict], tid: str, as_items: bool = False) -> list:
    """Reports grouped by committee, then cycle, each cycle with the same whole-cycle figures as a race (expected:
    the annual report only, since these committees have no ballot line in the guide's results).
    ``as_items=True`` returns ``entity_list`` items instead (one per committee: name, candidate and party as written,
    reports on file and status mix on the line; the cycle blocks inside)."""
    out = []
    by_key = OrderedDict()
    for r in sorted(rows, key=lambda r: (r["_label"].casefold(), r["_key"], r.get("period_to") or "")):
        by_key.setdefault(r["_key"], []).append(r)
    for k, krows in by_key.items():
        cand = Counter(x["candidate"] for x in krows if x["candidate"]).most_common(1)
        party = Counter(x["party"] for x in krows if x["party"]).most_common(1)
        who = name_with_form_party(cand[0][0], party[0][0] if party else "",
                                   cf._records_party(ed, cand[0][0], "2026")) if cand else "No candidate named"
        blocks = []
        by_cyc = OrderedDict()
        for r in krows:
            by_cyc.setdefault(cm.money_cycle(r), []).append(r)
        for cyc, crows in sorted(by_cyc.items(), key=lambda kv: kv[0]):
            spec = cm.cycle_spec(ed, cyc)
            n = len(blocks)
            if spec is None:
                s = {"items": [{"row": r, "slot": None, "counted": False, "why": "no-period", "notes": []} for r in crows],
                     "label": krows[0]["_label"], "basis": [], "spent": None, "notes": []}
                blocks.append(h("div", {"class": "cf-cycle"},
                                h("p", {"class": "cf-race-meta"}, "Period not written on the form: not placed in a cycle."),
                                _reports_table(ed, page, f"{tid}-{k}-{n}", s, None), _notes(s)))
                continue
            off = Counter(x["office_normalized"] for x in crows).most_common(1)[0][0]
            s = cm.committee_summary(crows, spec, cm._expected_types(ed, off, crows[0]["unit_id"], cyc), "none")
            s["label"] = krows[0]["_label"]
            line = (f"{spec['cycle']} cycle: {_money_cell(s['spent'], [s], 'spent')} spent, "
                    f"{_money_cell(s['raised'], [s], 'raised')} raised; cash on hand at the latest report "
                    f"{cm.usd(s['cash']) if s['cash'] is not None else s['cash_why'] or 'not shown'}. "
                    + _on_file_text(s, spec) + ".")
            blocks.append(h("div", {"class": "cf-cycle"},
                            h("p", {"class": "cf-race-meta"}, line, " ",
                              status_badge("computed", page, "Sum of the reports in the table, by the guide's rules.")),
                            _reports_table(ed, page, f"{tid}-{k}-{n}", s, spec), _notes(s)))
        blocks.append(mh.render(ed, page, k))
        if as_items:
            mix = Counter(x["transcription_status"] for x in krows)
            mix_text = ", ".join(f"{n} {cf.STATUS_CF.get(st, (st.upper(),))[0]}" for st, n in mix.most_common())
            cycles = sorted({cm.money_cycle(x) for x in krows})
            slug = re.sub(r"[^a-z0-9]+", "-", f"{tid}-{k}".lower()).strip("-")
            out.append({"key": slug, "name": krows[0]["_label"], "item_id": f"cmte-{slug}",
                        "facts": [who if cand else "No candidate named",
                                  f"{len(krows)} report{'s' if len(krows) != 1 else ''}, "
                                  f"{len(cycles)} cycle{'s' if len(cycles) != 1 else ''}",
                                  mix_text],
                        "search": " ".join(cycles) + " " + (cand[0][0] if cand else ""),
                        "body": h("div", {"class": "cf-committee-block"},
                                  h("p", {"class": "cf-sub"}, "Candidate: ", who), blocks)})
            continue
        out.append(h("div", {"class": "cf-committee-block"},
                     h("h4", None, krows[0]["_label"], h("span", {"class": "cf-sub"}, "Candidate: ", who)), blocks))
    return out


# --------------------------------------------------------------------------- index
def build_index(site):
    ed = site.ed
    page = site.page(cm.INDEX_PAGE, title=cf.TITLE, banners=False)
    c = page.cites
    d = cf.cf_all(ed)
    areas, races = d["areas"], d["races"]
    shapes = load_shapes(ed)
    dsets = district_sets(ed, races, load_district_shapes(ed, shapes))
    toc = [("map", "Map by place"), ("areas", "Every area"), ("about", "About these figures"), ("gaps", "Gaps"),
           ("sources", "Sources")]
    page.add(h("header", {"class": "page-hero"},
               h("p", {"class": "eyebrow mono"}, "Reference · Money"),
               h("h1", None, cf.TITLE),
               h("p", {"class": "dek"}, "What local candidates' committees reported spending and raising, race by race, "
                                        "read from the scanned forms the county posts. Pick a kind of race, then a "
                                        "place.", c.cite(cf.SRC_FILINGS_PAGE)),
               callout(h("p", None, h("strong", None, "Money is not a measure of support. "),
                         "These reports show what committees said they raised and spent. They don't show how many people "
                         "back a candidate, and the guide doesn't use them to predict results. Nothing here is ranked "
                         "by money."), kind="note"),
               h("p", {"class": "cf-quick"},
                 h("a", {"class": "btn btn-small", "href": page.rel(cm.HOW_PAGE)}, "How reporting works"), " ",
                 h("a", {"class": "btn btn-small", "href": page.rel(cm.ALL_PAGE)}, "Every filing"), " ",
                 h("a", {"class": "btn btn-small", "href": page.rel(cm.ALL_PAGE + "#large")}, "Large contributions"), " ",
                 h("a", {"class": "btn btn-small", "href": page.rel(cm.HOW_PAGE + "#delinquent")}, "Delinquent filers")),
               h("nav", {"class": "toc", "aria-label": "On this page"},
                 h("ol", None, [h("li", None, h("a", {"href": f"#{a}"}, t)) for a, t in toc]))))
    # ---- map
    if shapes:
        layers = map_layers(ed, page, shapes, dsets, areas, ed.table("cf_state"))
        mp = campaign_map(page, ed, shapes, layers, "county")
        set_src = ";".join(dict.fromkeys(sid for s in dsets for sid in split_ids(s["source_ids"])))
        page.add(section(
            "map", 1, "Map by place",
            h("p", None, "Choose a kind of race. Each area is shaded by what all its candidates reported spending over "
                         "the whole campaign for its latest election, from the reports on file. Hover, focus or tap an "
                         "area for the figures; select it again to open its races and every report.", c.cite("CFM-010"),
              " ", status_badge("computed", page, "Whole-campaign sums of cf_local.csv rows.")),
            mp,
            h("p", {"class": "muted cmap-mnote"},
              "How the shading is figured: for each area, the spending all candidates reported for its latest election "
              "in the guide's results (2026 for county and township offices on that ballot, 2024 for the rest of the "
              "county offices and some school seats, 2023 for city offices and most town offices), added up over every "
              "report of that election's cycle. Breaks are set separately for each layer; compare shades only within a "
              "layer. A figure equal to a break falls in the higher step. Hatched areas have no reports on file, or no "
              "race in the guide's results: not $0. Most races are marked incomplete, so read the totals as floors. "
              "District boundaries are the official files the guide downloaded; no boundary is drawn by the guide. ",
              c.cite_compact(set_src or MAP_SOURCES)),
            scope="county", ed=ed))
    else:
        page.add(section("map", 1, "Map by place", h("p", None, "The map's boundary file isn't in this edition yet; the "
                                                                "list below has every area."), scope="county", ed=ed))
    # ---- every area
    page.add(section("areas", 2, "Every area", *_areas_list(ed, page, areas), scope="county", ed=ed,
                     lead="Each government's latest election, with links to its races, candidates and reports."))
    # ---- about (short; anchors kept for inbound links)
    page.add(section(
        "about", 3, "About these figures",
        h("h3", {"id": "obligations"}, "Who reports, and when"),
        h("p", None, "Committees for county, city, town, township and school-board candidates, and the county party "
                     "committees, report on the state's CFA-4 form; the county posts the scans.", c.cite(cf.SRC_FILINGS_PAGE),
          " State legislators file with the Indiana Election Division instead.", c.cite(cf.SRC_STATE_BULK), " ",
          h("a", {"href": page.rel(cm.HOW_PAGE + "#obligations")}, "How campaign finance reporting works")),
        h("h3", {"id": "public"}, "What's public"),
        h("p", None, "The guide transcribed each report's one-page summary sheet: cash, receipts, expenditures and debts. "
                     "It never copies addresses or contact details. Nothing from 2022 or earlier is posted.",
          c.cite(f"{cf.SRC_FORM};{cf.SRC_INVENTORY}"), " ",
          h("a", {"href": page.rel(cm.HOW_PAGE + "#public")}, "What's public and what isn't")),
        h("h3", {"id": "method"}, "How the forms were read and added up"),
        h("p", None, "Every figure was read by eye from a scan and checked with the form's own arithmetic; each report "
                     "carries a status badge.", c.cite(cf.SRC_ADJ), " Whole-campaign figures are the guide's sums, by "
                     "published rules.", c.cite("CFM-010"), " ",
          h("a", {"href": page.rel(cm.HOW_PAGE + "#method")}, "How the guide read the forms"), " · ",
          h("a", {"href": page.rel(cm.HOW_PAGE + "#adding")}, "How it adds up a campaign"), " · ",
          h("a", {"href": page.rel(cm.HOW_PAGE + "#coverage")}, "How complete the record is")),
        scope="county", ed=ed))
    page.add(h("p", {"class": "cf-related"}, "Related: ",
               h("a", {"href": page.rel("state/your-legislators/index.html#money")}, "State legislators' campaign money"),
               " · ", h("a", {"href": page.rel("money/budgets/index.html")}, "Budgets by unit"), " · ",
               h("a", {"href": page.rel("run/index.html")}, "Run for office")))
    page.finish(gaps=_short_gaps(ed, d["model"]), gaps_intro=None)
    return page


def _short_gaps(ed, model) -> list[dict]:
    g = cf._gaps(ed, None, model)
    keep = ("Campaign-finance reports from 2022", "2023 pre-primary", "Reports after mid-October", "Itemized")
    return [x for x in g if x["item"].startswith(keep)]


TYPE_GROUP_NOTE = {
    "county": "Countywide offices, the commissioners and the county council.",
    "courts": "Judges elected countywide.",
    "school": "Penn-Harris-Madison's township seats are residency seats elected by the whole corporation.",
}


def _areas_list(ed, page, areas) -> list:
    # saved place (added 2026-11-09): the reader's city or town, township and school rows go first (preselect "rows")
    out = [here_slot("rows", "areas"),
           h("p", {"class": "cf-list-tools", "hidden": True, "id": "cf-list-tools"},
             h("span", {"id": "cf-list-state", "aria-live": "polite"}), " ",
             h("button", {"type": "button", "class": "btn btn-small", "id": "cf-list-all"}, "Show every race type"))]
    for typ, label in cm.TYPES.items():
        if typ == "state":
            st = ed.table("cf_state")
            dists = sorted({r["district"] for r in st}, key=lambda d: (d[:2], int(d[2:])))
            body = data_table("cf-areas-state", ["Area", "Basis", "Districts", "Committees in the data", "Figures"],
                              [[h("a", {"href": page.rel(cm.area_path(cm.STATE_AREA))}, "State legislature"),
                                "Filing year (not a race total)", len(dists), len({r["committee"] for r in st}),
                                "By committee and filing year"]],
                              caption="State legislative districts in the county", copy=False, min_width="40rem")
            out.append(h("div", {"class": "cf-group", "data-cf-type": typ}, h("h3", None, label),
                         h("p", {"class": "muted"}, "State legislators' committees report to the state by filing year, a "
                                                    "different basis from the local races, so they are not added up as "
                                                    "races."), body))
            continue
        rows, attrs = [], []
        for a in areas.values():
            if a["type"] != typ:
                continue
            attrs.append({**here_attrs(ed, cm.area_unit(a["id"])), "data-here-name": a["name"]})
            latest = a["latest_races"]
            name = a["name"]
            if typ == "county":
                name = f"{a['name']} (countywide offices, commissioners and council)"
            rows.append([h("a", {"href": page.rel(cm.area_path(a["id"]))}, name),
                         _el_title(ed, a["latest"]).split(" (")[0] if a["latest"] else "No race in the 2023-2026 results",
                         len(latest), f"{a['n_with']} of {a['n_candidates']}" if latest else "",
                         cm.usd(a["spent"]) if a["spent"] is not None else ("No reports on file" if latest else ""),
                         ("Complete" if a["complete"] else "Incomplete") if latest else ""])
        body = data_table(f"cf-areas-{typ}", ["Area", "Latest election", "Races", "Candidates with reports on file",
                                              "Spent, all candidates (latest election)", "Record"], rows,
                          caption=f"{label}: latest election by area", numeric=(2, 4), copy=False, min_width="46rem",
                          row_attrs=attrs)
        out.append(h("div", {"class": "cf-group", "data-cf-type": typ}, h("h3", None, label),
                     h("p", {"class": "muted"}, TYPE_GROUP_NOTE[typ]) if typ in TYPE_GROUP_NOTE else None, body))
    out.append(h("p", None, h("strong", None, "Not tied to one race: "),
                 h("a", {"href": page.rel(cm.area_path(cm.OTHER_AREA))}, "party, PAC and issue committees"),
                 ", and filings that name no office or no government."))
    out.append(h("p", {"class": "muted"}, "“Spent” is the whole campaign for the area's latest election: every candidate, "
                                          "every report of that election's cycle. “Incomplete” means at least one "
                                          "expected report is not on file. ", status_badge("computed", page)))
    return out


# --------------------------------------------------------------------------- one area
def build_area(aid: str, site):
    ed = site.ed
    page = site.page(cm.area_path(aid), banners=False)
    c = page.cites
    d = cf.cf_all(ed)
    a = d["areas"][aid]
    model = d["model"]
    toc = [(f"e-{eid}", _el_title(ed, eid).split(" (")[0]) for eid in a["elections"]]
    mapped = _area_map(ed, page, d, aid) if a["races"] else None
    if mapped:
        toc.insert(0, ("map", "Map"))
    compare = [r for r in model["races"] if _contest_area(r["contest"]) == aid]
    large = [x for x in model["large"] if x["row"] and x["row"]["unit_id"] and cm.area_id(x["row"]["unit_id"]) == aid
             and x["row"]["_group"] not in ("noncand", "none")]
    if compare:
        toc.append(("compare", "Same report, same period"))
    if a["other"]:
        toc.append(("other", "Other reports"))
    if large:
        toc.append(("large", "Large contributions"))
    toc += [("gaps", "Gaps"), ("sources", "Sources")]
    latest = a["latest_races"]
    summary = None
    if latest:
        summary = h("div", {"class": "cf-summary"},
                    h("p", None, h("strong", None, f"Latest election: {_el_title(ed, a['latest'])}. "),
                      f"{len(latest)} race{'s' if len(latest) != 1 else ''}, {a['n_candidates']} candidates and "
                      f"committees, {a['n_with']} with reports on file."),
                    h("p", None, h("strong", None, "Spent by all candidates: "),
                      (cm.usd(a["spent"]) + (f" (reports through {fmt_date(a['latest_to'])})" if a["latest_to"] else "")
                       + "; raised " + cm.usd(a["raised"]) + ". ") if a["spent"] is not None else
                      "no reports on file for any candidate (not the same as $0). ",
                      status_badge("computed", page, "Sum of the races below."), c.cite("CFM-010")),
                    h("p", None, "By party: " + _party_text(a)) if a["by_party"] else None,
                    h("p", None, record_line(latest) + "."))
    notes = []
    if a["type"] in NO_SHAPES and any(r["district"] for r in a["races"]):
        notes.append(h("p", {"class": "muted"}, NO_SHAPES[a["type"]], " ", c.cite("MAP-031;MAP-032;MAP-033;MAP-036")))
    if aid == "phm":
        notes.append(h("p", {"class": "muted"}, "Penn-Harris-Madison's township seats are held by residents of each "
                                                "township and elected by voters across the whole school corporation.",
                       c.cite("MAP-033")))
    u = ed.units.get(aid)
    if aid == "county":
        notes.append(h("p", {"class": "muted"}, "The county's other facts: ",
                       h("a", {"href": page.rel("county/index.html")}, "St. Joseph County, the county page"), "."))
    elif u and u["unit_type"] in ("city", "town", "township"):
        notes.append(h("p", {"class": "muted"}, "Everything else the guide has about this place: ",
                       h("a", {"href": page.rel(f"places/{aid}/index.html")}, u["name"]), "."))
    page.add(h("header", {"class": "page-hero"},
               cf.crumbs(page, (a["name"], None)),
               h("p", {"class": "eyebrow mono"}, "Reference · Money · Campaign finance"),
               h("h1", None, page.title),
               h("p", {"class": "dek"}, f"Every race for {a['name']} on the 2023, 2024 and 2026 ballots in the guide's "
                                        "results, each candidate's whole-campaign figures, and every report behind them, "
                                        "read from the county's scans.", c.cite(cf.SRC_FILINGS_PAGE)),
               summary, notes,
               h("p", {"class": "cf-quick"},
                 h("a", {"href": page.rel(cm.INDEX_PAGE + "#map")}, "Back to the map"), " · ",
                 h("a", {"href": page.rel(cm.HOW_PAGE + "#adding")}, "How the guide adds up a campaign"), " · ",
                 h("a", {"href": page.rel(cm.ALL_PAGE)}, "Every filing")),
               h("nav", {"class": "toc", "aria-label": "On this page"},
                 h("ol", None, [h("li", None, h("a", {"href": f"#{x}"}, t)) for x, t in toc]))))
    n = 0
    if mapped:
        n += 1
        page.add(_area_map_section(ed, page, a, mapped, n))
    if not a["races"]:
        n += 1
        page.add(section("races", n, "Races", h("p", None, f"The guide's 2023 to 2026 election results have no race for "
                                                          f"{a['name']}."), scope="county", ed=ed))
    for eid, rs in a["elections"].items():
        n += 1
        page.add(section(f"e-{eid}", n, _el_title(ed, eid), cf._ballot_order_note(ed, page) if eid != "2023g" else None,
                         [race_block(ed, page, r) for r in rs], scope="county", ed=ed,
                         lead="Candidates in ballot order, then committees for the office with no ballot line."))
    if compare:
        n += 1
        page.add(section("compare", n, "Same report, same period: pre-election reports",
                         *cf._races_block(ed, page, model, compare), scope="county", ed=ed))
    if a["other"]:
        n += 1
        blocks = []
        for i, (off, rows) in enumerate(a["other"].items()):
            blocks.append(h("details", {"class": "cf-reports cf-other"},
                            h("summary", None, f"{cf._office_label(rows[0])} ({len(rows)} report{'s' if len(rows) != 1 else ''})"),
                            committee_cycles(ed, page, rows, f"o{i}")))
        page.add(section("other", n, "Other reports for these offices", h("p", None,
                         "Reports filed for these offices in a cycle that isn't the office's race above (for example, "
                         "an annual report in a year the seat isn't on the ballot), or for an office with no race in the "
                         "guide's 2023 to 2026 results."), *blocks, scope="county", ed=ed))
    if large:
        n += 1
        page.add(section("large", n, "Large contributions (CFA-11 notices)", *_large_rows(ed, page, large),
                         scope="county", ed=ed))
    page.finish(gaps=_short_gaps(ed, model))
    return page


def _area_map(ed, page, d, aid):
    """(shapes, layers, types, default, district sets) for an area page's map, or None (no outline or no race)."""
    shapes = load_shapes(ed)
    if not shapes:
        return None
    dsets = district_sets(ed, d["races"], load_district_shapes(ed, shapes))
    got = area_layers(ed, page, shapes, dsets, d["areas"], ed.table("cf_state"), aid)
    if not got:
        return None
    layers, types, default = got
    for L in layers:
        for sh in L["shapes"]:
            if sh["href"].startswith("#r-"):
                _add_seat_facts(ed, page, sh["entry"], sh["href"][3:])
    if aid == "county":
        # Nick, 2026-11-09: a Townships layer on the county's page, each township linking to its own page
        tw = next((L for L in map_layers(ed, page, shapes, [], d["areas"], ed.table("cf_state"))
                   if L["id"] == "township"), None)
        if tw:
            tw["type"] = "townships"
            for sh in tw["shapes"]:
                a = next((x for x in d["areas"].values() if f"township:{x['id']}" == sh["uid"]), None)
                if a:
                    _add_township_holders(ed, sh["entry"], a)
            layers.append(tw)
            types["townships"] = "Townships"
    return shapes, layers, types, default, dsets


def _seat_words(ed, office_id: str) -> tuple[str, str]:
    """('Name (D), since Jan 1, 2019' or the holders' names, and the incoming line or '') for one office."""
    office = ed.offices.get(office_id)
    if not office:
        return "", ""
    st = holder_state(ed, office, ed.current_terms(office_id), ed.incoming_terms(office_id))
    now = st["now"]
    if st["since"] and len(ed.current_terms(office_id)) == 1:
        now += f", since {st['since']}"
    return now, st["incoming"]


def _result_words(ed, contest: dict) -> str:
    """'Won: Scott Ruszkowski (D) 62.6%; margin 25.2 points (19,277 votes) (results unofficial)', or 'Uncontested:
    ...', from the results (the margin is pages/elections.py margin(): last winner over the next candidate)."""
    cands = el_candidates(contest)
    named = [x for x in cands if not is_writein_total(x["row"])]
    won = sorted([x for x in named if (x["row"].get("winner") or "").upper() == "Y"],
                 key=lambda x: -(x["votes"] or 0))
    unoff = any(r.get("status") == "unofficial" for r in contest["rows"])
    def who(x):
        pct = f" {x['pct']:.1f}%" if x.get("pct") is not None else ""
        return f"{x['name']}{' (' + x['party'] + ')' if x.get('party') else ''}{pct}"
    m = el_margin(contest)
    if m is None:
        txt = "Uncontested: " + (", ".join(x["name"] + (f" ({x['party']})" if x.get("party") else "") for x in named)
                                 or "no named candidate")
    elif "reason" in m:
        txt = ("Elected: " + ", ".join(who(x) for x in won) + "; " if won else "") + f"margin not computed ({m['reason']})"
    else:
        lead = "Elected: " if m["seats"] > 1 else "Won: "
        gap = "tie on the votes" if m["tie"] else (
            f"margin {'for the last seat ' if m['seats'] > 1 else ''}{m['pts']:.1f} points ({m['votes']:,} votes)")
        txt = (lead + ", ".join(who(x) for x in won) + "; " if won else "") + gap
    return txt + (" (results unofficial)" if unoff else "")


def _add_seat_facts(ed, page, entry: dict, race_id: str) -> None:
    """Nick, 2026-11-09 (the box shows holder + result + money): after the race's Election line, who holds the seat
    now (and who comes in), then the race's result with its margin, and a link to it in the results explorer."""
    contest = ed.contests.get(race_id)
    if not contest:
        return
    add = []
    now, inc = _seat_words(ed, contest.get("office_id") or "")
    if now:
        add.append(["Holds the seat now", now])
    if inc:
        add.append(["After the election", inc])
    add.append(["Result", _result_words(ed, contest)])
    entry["f"] = entry["f"][:1] + add + entry["f"][1:]
    href = contest_href(page, race_id)
    if href:
        entry["more"] = [["See the result in the results explorer", href]]


def _add_township_holders(ed, entry: dict, area: dict) -> None:
    """A township on the county page's map: who holds its offices now, before the money lines."""
    add = []
    for r in area["latest_races"]:
        contest = ed.contests.get(r["id"])
        now, _ = _seat_words(ed, (contest or {}).get("office_id") or "")
        if now:
            add.append([f"{office_tab(r['office'], (area['name'],))} now", now])
    entry["f"] = add + entry["f"]


def _area_map_section(ed, page, a, mapped, n) -> Markup:
    """An area page's map (added 2026-11-09, first for the county, then every area): offices one at a time, then the
    government's district layers, each with the same panel figures as the race cards below. Without JavaScript the
    default layer shows and every shape links to its race card."""
    c = page.cites
    shapes, layers, types, default, dsets = mapped
    used = {s["id"] for L in layers for s in L.get("sets", [])}
    set_src = ";".join(dict.fromkeys(sid for s in dsets if s["id"] in used for sid in split_ids(s["source_ids"])))
    kinds = " or ".join(t.lower() for t in types.values()) if len(types) > 1 else None
    years = sorted({L["shapes"][0]["year"] for L in layers if L["kind"] == "office" and L["shapes"][0].get("year")}
                   | {s["year"] for L in layers if L["kind"] == "district" for s in L["shapes"] if s.get("year")},
                   reverse=True)
    lead = (f"Choose {kinds}, then an office or a district. " if kinds else
            ("Choose an office. " if len(layers) > 1 else ""))
    nodraw = "nodraw" in types
    shared = any(L["kind"] == "office" for L in layers) and sum(1 for L in layers if L["kind"] == "office") > 1
    return section(
        "map", n, "Map",
        h("p", None, lead + "The box beside the map shows what every candidate in that race reported spending over "
                     "the whole campaign, by party and by candidate, and whether every expected report is on file. "
                     "The same figures are in the race cards below.", c.cite("CFM-010"), " ",
          status_badge("computed", page, "Whole-campaign sums of cf_local.csv rows.")),
        area_campaign_map(page, ed, shapes, a, layers, types, default),
        h("p", {"class": "muted cmap-mnote"},
          "How the shading is figured: each office or district shows its latest election in the guide's results"
          + (f" ({' or '.join(years)}; the box says which). " if len(years) > 1 else ". ")
          + ("Offices share one set of steps, so their shades compare offices. " if shared else "")
          + ("District steps are set for each district layer. " if any(L["kind"] == "district" for L in layers)
             else "")
          + ("A district with no official boundary file is shown on the whole outline, and its box says so. "
             if nodraw else "")
          + "A figure equal to a break falls in the higher step. Hatched means no reports on file: not $0. Read "
          "incomplete totals as floors. Boundaries are official files the guide downloaded; no boundary is drawn by "
          "the guide. ", c.cite_compact(set_src or MAP_SOURCES)),
        scope="county", ed=ed)


def _contest_area(contest) -> str | None:
    info = cm.contest_race(contest["label"])
    return cm.area_id(info["unit"]) if info else None


def _large_rows(ed, page, large) -> list:
    c = page.cites
    trs = []
    for x in large:
        e = x["e"]
        trs.append([e["contributor"], cf.money(cf._num(e["amount"])), fmt_date(e["date"]),
                    h("span", None, e["committee"] or "Committee not named on the notice",
                      h("span", {"class": "cf-sub"}, x["office"])),
                    h("span", {"class": "cf-lnote"}, x["note"]), h("span", None, f"doc {e['doc_id']} ", c.cite(e["source_ids"]))])
    return [h("p", None, "Single contributions of $1,000 or more reported on the county's CFA-11 notices for these "
                         "offices, with the contributor's name as filed, by office, committee and date (never by "
                         "amount). ", status_badge("from_scan", page), " ",
              h("a", {"href": page.rel(cm.ALL_PAGE + "#large")}, "Every notice")),
            data_table("cf-area-large", ["Contributor (as filed)", "Amount", "Date received", "Recipient committee",
                                         "Note on the notice", "Form"], trs,
                       caption="Large contributions reported on CFA-11 notices", numeric=(1,), min_width="52rem")]


# --------------------------------------------------------------------------- state legislature
def build_state(site):
    ed = site.ed
    page = site.page(cm.area_path(cm.STATE_AREA), banners=False)
    c = page.cites
    st = ed.table("cf_state")
    src = ";".join(dict.fromkeys(s for r in st for s in split_ids(r["source_ids"])))
    dists = sorted({r["district"] for r in st}, key=lambda d: (0 if d.startswith("HD") else 1, int(d[2:])))
    page.add(h("header", {"class": "page-hero"},
               cf.crumbs(page, ("State legislature", None)),
               h("p", {"class": "eyebrow mono"}, "Reference · Money · Campaign finance"),
               h("h1", None, page.title),
               h("p", {"class": "dek"}, "Receipts and spending of the campaign committees of state legislators and 2026 "
                                        "candidates in the House and Senate districts that include part of the county, "
                                        "from the Indiana Election Division's bulk data.", c.cite(src)),
               callout(h("p", None, h("strong", None, "A different basis from the local races. "),
                         "These totals add up the items on reports filed in each calendar year, not an election cycle, "
                         "and the latest year is partial. Only the listed committees are included, not every opponent, "
                         "so the guide doesn't add them up by district or compare them with the local race totals.",
                         c.cite("MON-020;MON-021;MON-022")), kind="note"),
               h("p", None, "Districts, members and results: ",
                 h("a", {"href": page.rel("state/your-legislators/index.html#money")}, "Your legislators"), ".")))
    blocks = []
    for dist in dists:
        rs = sorted([r for r in st if r["district"] == dist], key=lambda r: (r["candidate"], r["year"]))
        trs = [[h("a", {"href": mh.legislator_href(ed, page, r["candidate"])}, name_with_party(r["candidate"], r["party"]))
                if mh.legislator_href(ed, page, r["candidate"]) else name_with_party(r["candidate"], r["party"]),
                r["committee"], r["year"],
                cm.usd(cm.cents(r["receipts"])), cm.usd(cm.cents(r["expenditures"]), "not in the data"),
                status_badge(r["status"], page)] for r in rs]
        office = "Indiana House" if dist.startswith("HD") else "Indiana Senate"
        blocks.append(h("div", {"class": "cf-state-d", "id": dist.lower()},
                        h("h3", None, f"{office} District {dist[2:]}"),
                        data_table(f"cf-state-{dist.lower()}", ["Candidate", "Committee", "Filing year", "Receipts",
                                                                "Expenditures", "Status"], trs,
                                   caption=f"{office} District {dist[2:]}: committees by filing year", numeric=(2, 3, 4),
                                   min_width="44rem")))
    mp = _state_map_section(ed, page)
    if mp:
        page.add(mp)
    page.add(section("districts", 2 if mp else 1, "By district", h("p", None, "Each committee's receipts and expenditures by the "
                                                                   "calendar year its reports were filed.", c.cite(src),
                                                      " ", status_badge("computed", page, "Sums of the state's bulk-data "
                                                                                          "rows by filing year.")),
                     blocks, scope="county", ed=ed))
    ppl = mh.legislators(ed)
    if ppl:
        hist = ed.table("cf_state_history")
        hsrc = ";".join(dict.fromkeys(s for r in hist for s in split_ids(r["source_ids"])))
        page.add(section("people", (2 if mp else 1) + 1, "Each candidate over time",
                         h("p", None, f"Every state House and Senate candidate on the guide's ballots (2010 to 2026) "
                                      f"whose committee files with the state, {len(ppl)} people, with every filing year "
                                      "in the state's bulk data from 2000. Newest first. ", c.cite(hsrc or src), " ",
                           status_badge("computed", page, "Sums of the state's bulk-data rows by filing year.")),
                         h("p", {"class": "muted"}, "A committee whose name doesn't say the office is included only "
                                                    "when it filed around the candidate's race (its notes say so). "
                                                    "Legislators who left office before 2010 aren't listed: the guide's "
                                                    "results start in 2010."),
                         [mh.legislator_block(ed, page, p) for p in ppl], scope="county", ed=ed))
    page.finish(gaps=ed.gaps(files=["gaps_money"], pattern=r"State campaign finance"))
    return page


STATE_TYPES = OrderedDict([("house", "Indiana House districts"), ("senate", "Indiana Senate districts")])


def _state_map_section(ed, page) -> Markup | None:
    """The state-legislature page's map (added 2026-11-09): the House and Senate district layers of the main campaigns
    map, linked to the district blocks on this page. Not shaded: these are filing-year sums of listed committees, not
    race totals (the legend says so)."""
    shapes = load_shapes(ed)
    if not shapes:
        return None
    d = cf.cf_all(ed)
    dsets = [s for s in district_sets(ed, d["races"], load_district_shapes(ed, shapes)) if s["type"] == "state"]
    if not dsets:
        return None
    layers = []
    for L in map_layers(ed, page, shapes, dsets, d["areas"], ed.table("cf_state")):
        if L["kind"] != "district" or L["type"] != "state":
            continue
        L["type"] = L["id"].split("-", 1)[1]
        if L["type"] not in STATE_TYPES:
            continue
        for s in L["shapes"]:
            s["href"] = s["entry"]["href"] = _same_page(s["href"], page)
        layers.append(L)
    if not layers:
        return None
    c = page.cites
    src = ";".join(dict.fromkeys(sid for s in dsets for sid in split_ids(s["source_ids"])))
    return section(
        "map", 1, "Map",
        h("p", None, "Choose House or Senate districts. The box beside the map lists each committee's receipts and "
                     "spending by filing year, the same figures as the tables below. Districts reach past the county "
                     "line; the map draws only the part inside the county."),
        state_campaign_map(page, ed, shapes, layers, STATE_TYPES),
        h("p", {"class": "muted cmap-mnote"}, "Not shaded: filing-year sums of the listed committees aren't race totals, "
                                              "so districts aren't compared. Boundaries are official files the guide "
                                              "downloaded; no boundary is drawn by the guide. ", c.cite_compact(src)),
        scope="county", ed=ed)


# --------------------------------------------------------------------------- other committees
OTHER_GROUPS = [("noncand", "Party, PAC and issue committees", "Committees that back no single candidate: county party "
                 "committees, political action committees and issue committees."),
                ("no-office", "No office written on the form", "Neither the form nor any other filing by the same "
                 "committee names an office. The guide doesn't fill it in from ballots."),
                ("no-office-sought", "No office sought", "The form says no office is sought."),
                ("no-unit", "Office written, government not named", "The form names an office but not which government "
                 "(for example, a town clerk-treasurer with no town).")]


def _other_group(r) -> str:
    if r["_group"] == "noncand":
        return "noncand"
    off = r["office_normalized"]
    if not off:
        return "no-office"
    if off.startswith("No office sought"):
        return "no-office-sought"
    return "no-unit"


def build_other(site):
    ed = site.ed
    page = site.page(cm.area_path(cm.OTHER_AREA), banners=False)
    c = page.cites
    d = cf.cf_all(ed)
    rows = d["other"]
    groups = OrderedDict((g, []) for g, _t, _n in OTHER_GROUPS)
    for r in rows:
        groups[_other_group(r)].append(r)
    large = [x for x in d["model"]["large"] if not x["row"] or x["row"]["_group"] in ("noncand", "none")
             or not x["row"]["unit_id"]]
    toc = [(g, t) for g, t, _n in OTHER_GROUPS if groups[g]] +         ([("state-filed", "Committees that file with the state")] if ed.table("cf_state_pacs") else []) +         ([("large", "Large contributions")] if large else []) + \
        [("gaps", "Gaps"), ("sources", "Sources")]
    page.add(h("header", {"class": "page-hero"},
               cf.crumbs(page, ("Party, PAC and other committees", None)),
               h("p", {"class": "eyebrow mono"}, "Reference · Money · Campaign finance"),
               h("h1", None, page.title),
               h("p", {"class": "dek"}, f"{len(rows)} filings that belong to no single race: party, PAC and issue "
                                        "committees, and candidate committees whose forms name no office or no "
                                        "government.", c.cite(cf.SRC_FILINGS_PAGE), " ",
                 status_badge("computed", page, "Counted from cf_local.csv.")),
               h("nav", {"class": "toc", "aria-label": "On this page"},
                 h("ol", None, [h("li", None, h("a", {"href": f"#{x}"}, t)) for x, t in toc]))))
    n = 0
    for g, title, note in OTHER_GROUPS:
        if not groups[g]:
            continue
        n += 1
        items = committee_cycles(ed, page, groups[g], g, as_items=True)
        page.add(section(g, n, title, h("p", None, note, c.cite(cf.SRC_COVERAGE)),
                         h("p", {"class": "muted"}, f"{len(items)} committee{'s' if len(items) != 1 else ''}, by name. "
                           "Each row opens to the committee's reports, by cycle, with the cycle totals and notes."),
                         entity_list(f"{g}-list", items, noun="committee", search="Find a committee or candidate",
                                     label=title) if len(items) > 4 else entity_list(f"{g}-list", items, noun="committee",
                                                                                      label=title),
                         scope="county", ed=ed))
    pacs = mh.state_pacs(ed)
    if pacs:
        n += 1
        psrc = ";".join(dict.fromkeys(s for r in ed.table("cf_state_pacs") for s in split_ids(r["source_ids"])))
        page.add(section("state-filed", n, "County committees that file with the state",
                         h("p", None, f"{len(pacs)} political action and party committees whose names place them in the "
                                      "county file their reports with the Indiana Election Division, not the county, so "
                                      "they are not in the county's postings above. Receipts and expenditures by the "
                                      "calendar year the reports were filed, 2010 to 2026, from the state's bulk data. ",
                           c.cite(psrc), " ", status_badge("computed", page, "Sums of the state's bulk-data rows by "
                                                                             "filing year.")),
                         h("p", {"class": "muted"}, "Committees are found by name (South Bend, Mishawaka, St. Joseph), "
                                                    "so a county group whose name doesn't say where it is isn't listed. "
                                                    "Largest payees are summed by name as typed on the reports."),
                         [mh.state_pac_block(ed, page, p) for p in pacs], scope="county", ed=ed))
    if large:
        n += 1
        page.add(section("large", n, "Large contributions (CFA-11 notices)", *_large_rows(ed, page, large),
                         scope="county", ed=ed))
    page.finish(gaps=_short_gaps(ed, d["model"]))
    return page


# --------------------------------------------------------------------------- registration
def _area_ids_all_editions() -> list[str]:
    root = Path(__file__).resolve().parents[3] / "data" / "editions"
    ids = []
    for f in sorted(root.glob("*/units.csv")):
        with open(f, encoding="utf-8-sig", newline="") as fh:
            for aid in cm.area_ids(list(csv.DictReader(fh))):
                if aid not in ids:
                    ids.append(aid)
    return ids


PAGES = {cm.INDEX_PAGE: build_index}
for _aid in _area_ids_all_editions():
    if _aid == cm.STATE_AREA:
        PAGES[cm.area_path(_aid)] = build_state
    elif _aid == cm.OTHER_AREA:
        PAGES[cm.area_path(_aid)] = build_other
    else:
        PAGES[cm.area_path(_aid)] = partial(build_area, _aid)
