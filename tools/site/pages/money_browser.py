"""Campaign money browser (phase 6 step 5, 2026-11-18; planning/design-direction-2026-11-16.md section 4).

Six real-URL views of the same campaign money, sharing one header and tab bar (``browser_head``):

    money/campaigns/index.html                     By office: every office with money on record, grouped by
                                                   government, a bar per office (its latest election on file), each
                                                   row linking to the office's Money tab (and its Primary / General
                                                   views); "How to read these reports" (#about, #obligations, #public,
                                                   #method stay here)
    money/campaigns/by-election/index.html         By election: the 2026, 2024 and 2023 cycles, every race of each on
                                                   one scale, then the earlier elections with news-reported figures
    money/campaigns/by-candidate/index.html        By candidate: every candidate and committee with money on record,
                                                   alphabetical (never ranked by money), linking to person pages
    money/campaigns/by-place/index.html            By place: the campaign-money map and every area (was the index's
                                                   #map and #areas; pages/campaign_pages.py map_section/_areas_list)
    money/campaigns/other-committees/index.html    Committees (pages/campaign_pages.py build_other, same content)
    money/campaigns/all-filings/index.html         Every filing (pages/campaigns.py build_all, same content)

Nothing here computes a new figure: office and race totals are the race model's own sums (pages/campaigns.py cf_all,
the same objects the race cards and the office Money tabs print); news-reported figures are never added up (rows link
to the office tab that shows them in their own words). Offices are ordered by what all their candidates reported
spending; people are never ranked by money (alphabetical), and money charts never use party colours.
"""
from __future__ import annotations

from collections import OrderedDict

from civic import campaign_money as cm
from civic import offices as om
from civic import people as pp
from civic.charts import money_rows
from civic.components import (callout, figure_mark, filter_empty_note, party_label, see_all_fold, status_badge,
                              table_filter)
from civic.data import fmt_date
from civic.html import Markup, h, join

from . import campaigns as cf
from .offices import PARTY_WORD

INDEX = cm.INDEX_PAGE
BY_ELECTION = "money/campaigns/by-election/index.html"
BY_CANDIDATE = "money/campaigns/by-candidate/index.html"
BY_PLACE = "money/campaigns/by-place/index.html"
COMMITTEES = cm.area_path(cm.OTHER_AREA)
FILINGS = cm.ALL_PAGE
TITLE = "Campaign money"
TABS = [(INDEX, "By office"), (BY_ELECTION, "By election"), (BY_CANDIDATE, "By candidate"), (BY_PLACE, "By place"),
        (COMMITTEES, "Committees"), (FILINGS, "Every filing")]
NOT_SUPPORT = ("Money is not a measure of support. These reports show what committees said they raised and spent; "
               "they don't show how many people back a candidate. Offices are ordered by what all their candidates "
               "reported spending; candidates are never ranked by money.")
SHOW_TOP = 10
SHOW_CYCLE = 6     # races shown per cycle before "Show the other N races"


# =========================================================================== shared header

def browser_head(page, current: str, facts=None, note=None) -> Markup:
    """Breadcrumb, title, one-line facts and the six-view tab bar (the same markup as civic/tabs.py tab bars, so it
    takes their styles in every look; it scrolls inside itself at phone width)."""
    items = []
    for path, label in TABS:
        if path not in page.site.by_path:
            continue
        cur = path == current
        items.append(h("li", {"class": "tab" + (" is-current" if cur else "")},
                       h("a", {"class": "tab-link", "href": page.rel(path), "aria-current": "page" if cur else None},
                         label)))
    bits = [f for f in (facts or []) if f]
    sep = h("span", {"class": "facts-sep", "aria-hidden": "true"}, " · ")
    return h("header", {"class": "thing-head cb-head"},
             page.crumb_nav(),
             h("h1", {"class": "thing-title"}, TITLE,
               h("span", {"class": "visually-hidden"}, f": {dict(TABS)[current]}") if current != INDEX else None),
             h("p", {"class": "thing-facts"}, join([h("span", {"class": "thing-fact"}, f) for f in bits], sep))
             if bits else None,
             h("p", {"class": "thing-note"}, note) if note else None,
             h("nav", {"class": "tabs", "aria-label": "Campaign money: views", "id": "tabs"},
               h("ul", {"class": "tab-list"}, items)))


# =========================================================================== the office model (no new figures)

def _race_year(race) -> str:
    return race["general_eid"][:4]


def _has_primary(race) -> bool:
    return om.race_split(race)["any"]


def office_rows(ed) -> list[dict]:
    """Every office with a Money tab, offices.csv order: {office, unit, level, state, race (the latest race with a
    report on file, or None), years (every year with money on record, newest first), news (years whose figures come
    from news reports), primary (the Money tab has primary figures)}. Cached per build."""
    got = ed.__dict__.get("_cb_offices")
    if got is not None:
        return got
    out = []
    for o in ed.tables["offices"]:
        oid = o["office_id"]
        if "money" not in om.office_tabs(ed, oid):
            continue
        m = om.money_model(ed, oid)
        race = next((r for c in m["cycles"] for r in c["races"]), None)
        news = [c["year"] for c in m["cycles"] if c["reported"]]
        # the Money tab's Primary / General views show something only where a race's filings can be cut at the
        # pre-primary report (both views) or the news reported that contest (pages/offices.py money tab, data-mt-phase)
        split = any(_has_primary(r) for c in m["cycles"] for r in c["races"])
        contests = [contest for c in m["cycles"] for contest, _rows in _contests_of(c["reported"])]
        primary = split or any(x["party_primary"] for x in contests)
        general = split or any(not x["party_primary"] for x in contests)
        out.append({"office": o, "id": oid, "unit": o["unit_id"], "level": om.level(ed, o), "state": m["state"],
                    "race": race, "years": [c["year"] for c in m["cycles"]], "news": news, "primary": primary,
                    "general": general,
                    "legislators": m["legislators"]})
    ed.__dict__["_cb_offices"] = out
    return out


def _contests_of(reported_rows) -> list:
    """[(contest, rows)] of a cycle's news-reported rows (the office model keeps (contest, rows) pairs)."""
    out = []
    for x in reported_rows or []:
        if isinstance(x, tuple):
            out.append(x)
    return out


def _years_text(years: list[str], news: list[str]) -> str:
    if not years:
        return ""
    bits = [y + (" (news reports)" if y in news else "") for y in years]
    return "Money on record: " + ", ".join(bits)


def _office_name_link(page, row, frag: str = "") -> Markup:
    u = om.href(page, row["id"], "money")
    t = row["office"]["title"]
    return h("a", {"class": "cb-office", "href": u + frag}, t) if u else h("span", {"class": "cb-office"}, t)


def view_links(page, row) -> Markup | None:
    """"Primary · General": links into the office Money tab's switch (#show=primary, static/js/offices.js), each only
    when that view shows something on that tab. With JavaScript off the link opens the tab with every chart shown."""
    u = om.href(page, row["id"], "money")
    if not u:
        return None
    links = [h("a", {"class": "cb-view", "href": f"{u}#show={v}",
                     "aria-label": f"{row['office']['title']}: {v} election money"}, v.capitalize())
             for v in ("primary", "general") if row[v]]
    return join(links, " · ") if links else None


def _office_money_row(page, row, *, sub_extra=None) -> dict:
    race = row["race"]
    rec = ""
    if race is not None:
        # 2026-11-18 ("About these figures"): an incomplete record is the * mark (its meaning is in the page's note);
        # a complete one, the normal case, carries no word
        rec = join([_race_year(race), None if race["complete"] else figure_mark("incomplete")])
    elif row["news"]:
        rec = "news reports only"
    years = [y for y in row["years"] if not race or y != _race_year(race)]
    sub = [rec]
    if years:
        news = [y for y in years if y in row["news"]]
        sub.append("also " + ", ".join(years) + (" (news)" if news and len(news) == len(years) else
                                                   f" ({', '.join(news)} from news)" if news else ""))
    views = view_links(page, row)
    if views is not None:
        sub.append(views)
    words = join([s for s in sub if s], " · ")   # join: the record may carry a mark (markup)
    attrs = {"data-tf-row": True, "data-tf-text": f"{row['office']['title']} {om.unit_name(page.ed, row['unit'])} "
                                                   + " ".join(row["years"])}
    if race is None:
        return {"name": _office_name_link(page, row), "sub": words,
                "raised": None, "spent": None, "raised_text": "see the office's Money tab",
                "spent_text": "see the office's Money tab", "attrs": attrs,
                "tip": row["office"]["title"]}
    return {"name": _office_name_link(page, row), "sub": words,
            "raised": race["raised"], "spent": race["spent"],
            "raised_text": cm.usd(race["raised"], "no reports on file"),
            "spent_text": cm.usd(race["spent"], "no reports on file"), "attrs": attrs,
            "tip": f"{row['office']['title']}: all candidates, whole {race['spec']['cycle']} cycle"}


def _rank(rows: list[dict]) -> list[dict]:
    """Offices by what all their candidates reported spending (latest election on file), most first; offices with no
    filed total after them, in their list order. Never applied to people."""
    have = [r for r in rows if r["race"] is not None and r["race"]["spent"] is not None]
    rest = [r for r in rows if r not in have]
    return sorted(have, key=lambda r: -r["race"]["spent"]) + rest


def _scale(rows) -> int:
    vals = [r["race"][k] for r in rows if r["race"] is not None for k in ("raised", "spent")
            if r["race"][k] is not None]
    return max(vals, default=100)


def _legend() -> Markup:
    return h("ul", {"class": "legend cb-legend"},
             h("li", None, h("span", {"class": "key key-rect m-accent", "aria-hidden": "true"}), "Raised"),
             h("li", None, h("span", {"class": "key key-rect m-spent", "aria-hidden": "true"}), "Spent"))


def _about(ed, page, num_word: str = "about") -> Markup:
    """The index's short "How to read these reports" (ids about, obligations, public, method kept for inbound links).
    Retitled 2026-11-18 from "About these figures", now the name of the page-bottom marks note (shell.Page.render)."""
    c = page.cites
    return h("section", {"class": "tsec cb-about", "id": num_word, "aria-labelledby": f"{num_word}-h"},
             h("h2", {"class": "tsec-h", "id": f"{num_word}-h"}, "How to read these reports"),
             h("h3", {"id": "obligations"}, "Who reports, and when"),
             h("p", None, "Committees for county, city, town, township and school-board candidates, and the county party "
                          "committees, report on the state's CFA-4 form; the county posts the scans.",
               c.cite(cf.SRC_FILINGS_PAGE), " State legislators file with the Indiana Election Division instead.",
               c.cite(cf.SRC_STATE_BULK), " ", h("a", {"href": page.rel(cm.HOW_PAGE + "#obligations")},
                                                "How campaign finance reporting works")),
             h("h3", {"id": "public"}, "What's public"),
             h("p", None, "The guide transcribed each report's one-page summary sheet: cash, receipts, expenditures and "
                          "debts. It never copies addresses or contact details. Nothing from 2022 or earlier is posted; "
                          "figures for earlier elections are as news coverage reported them.",
               c.cite(f"{cf.SRC_FORM};{cf.SRC_INVENTORY}"), " ",
               h("a", {"href": page.rel(cm.HOW_PAGE + "#public")}, "What's public and what isn't")),
             h("h3", {"id": "method"}, "How the forms were read and added up"),
             h("p", None, "Every figure was read by eye from a scan and checked with the form's own arithmetic; each "
                          "report carries a status mark.", c.cite(cf.SRC_ADJ), " Whole-campaign figures are the "
                          "guide's sums, by published rules.", c.cite("CFM-010"), " ",
               status_badge("computed", page, "Sums of the reports on file."), " ",
               h("a", {"href": page.rel(cm.HOW_PAGE + "#method")}, "How the guide read the forms"), " · ",
               h("a", {"href": page.rel(cm.HOW_PAGE + "#adding")}, "How it adds up a campaign"), " · ",
               h("a", {"href": page.rel(cm.HOW_PAGE + "#coverage")}, "How complete the record is")))


def _gaps(ed):
    from .campaign_pages import _short_gaps
    return _short_gaps(ed, cf.cf_all(ed)["model"])


# =========================================================================== By office (the index)

GROUP_LABEL = {"county": "County and courts", "city": "Cities", "town": "Towns", "township": "Townships",
               "school": "School boards", "state": "State legislature"}


def build_by_office(site):
    ed = site.ed
    page = site.page(INDEX, title=TITLE, body_class="thing-page")
    c = page.cites
    rows = office_rows(ed)
    local = [r for r in rows if not r["state"]]
    state = [r for r in rows if r["state"]]
    vmax = _scale(local)
    d = cf.cf_all(ed)
    n_off = len(ed.tables["offices"])
    page.add(browser_head(page, INDEX, [f"{len(rows)} of the county's {n_off} offices have campaign money on record",
                                        "2023 to 2026 from the reports the county posts; earlier years as news coverage "
                                        "reported them"]))
    page.add(h("p", {"class": "cb-lead"}, NOT_SUPPORT, c.cite(cf.SRC_FILINGS_PAGE)))
    # ---- the ten offices with the most money (latest election on file), the test case's first stop
    top = _rank(local)[:SHOW_TOP]
    page.add(h("section", {"class": "tsec", "id": "most", "aria-labelledby": "most-h"},
               h("h2", {"class": "tsec-h", "id": "most-h"}, "Most campaign money, latest election on file"),
               _legend(),
               money_rows("cb-top", f"The {len(top)} offices whose candidates reported the most spending",
                          [_office_money_row(page, r) for r in top], vmax=vmax,
                          subtitle="All candidates, whole election cycle, from the reports on file; an incomplete total is a floor. One scale for every "
                                   "chart on this page. Select an office for every election's money, primary and "
                                   "general.",
                          page=page, cite=c.cite("CFM-010"), status="computed",
                          headers=["Office", "Raised", "Spent"])))
    # ---- every office, by government (folds ship open; JS closes them; a filter opens the groups that match)
    groups: OrderedDict = OrderedDict()
    for r in local:
        groups.setdefault(r["level"], OrderedDict()).setdefault(r["unit"], []).append(r)
    blocks = []
    n_rows = 0
    for lv in om.LEVELS:
        if lv not in groups:
            continue
        govs = []
        for uid, offs in groups[lv].items():
            n_rows += len(offs)
            name = om.unit_name(ed, uid)
            area = cm.area_path(cm.area_id(uid))
            area_link = (h("p", {"class": "cb-area-link"}, h("a", {"href": page.rel(area)},
                                                              f"{name}: every race and report"))
                         if area in page.site.by_path else None)
            govs.append(h("details", {"class": "cb-gov", "id": f"g-{uid}", "data-tf-group": True, "data-fold": "gov",
                                      "open": True},
                          h("summary", {"class": "cb-gov-sum"},
                            h("span", {"class": "cb-gov-name"}, name), " ",
                            h("span", {"class": "cb-gov-n"}, f"{len(offs)} office{'s' if len(offs) != 1 else ''}"),
                            h("span", {"class": "fold-toggle", "aria-hidden": "true"})),
                          money_rows(f"cb-g-{uid}", f"{name}: offices", [_office_money_row(page, r)
                                                                          for r in _rank(offs)],
                                     vmax=vmax, page=page, headers=["Office", "Raised", "Spent"]),
                          area_link))
        blocks.append(h("div", {"class": "cb-level", "id": om.LEVEL_IDS[lv], "data-tf-group": True},
                        h("h3", {"class": "cb-level-h"}, GROUP_LABEL.get(lv, om.LEVELS[lv])),
                        h("div", {"class": "cb-govs"}, govs)))
    if state:
        n_rows += len(state)
        items = []
        for r in state:
            u = om.href(page, r["id"], "money")
            ppl = ", ".join(p["name"] for p in r["legislators"])
            items.append(h("li", {"class": "cb-srow", "data-tf-row": True,
                                  "data-tf-text": f"{r['office']['title']} state legislature {ppl}"},
                           h("a", {"href": u}, r["office"]["title"]) if u else r["office"]["title"]))
        blocks.append(h("div", {"class": "cb-level", "id": "state", "data-tf-group": True},
                        h("h3", {"class": "cb-level-h"}, "State legislature"),
                        h("p", {"class": "tnote"}, "Candidates' committees file with the state by calendar year, a "
                                                   "different basis from the local races, so they have no bars here.",
                          c.cite("MON-020"), " ",
                          h("a", {"href": page.rel(cm.area_path(cm.STATE_AREA))},
                            "Every district's committees, by filing year")
                          if cm.area_path(cm.STATE_AREA) in page.site.by_path else None),
                        h("ul", {"class": "cb-slist cb-slist-grid"}, items)))
    filt = table_filter("cb-offices", [], n_rows, noun="office", search="Office or place",
                        label="Filter the offices")
    page.add(h("section", {"class": "tsec", "id": "offices", "aria-labelledby": "offices-h"},
               h("h2", {"class": "tsec-h", "id": "offices-h"}, "Every office with money on record, by government"),
               h("p", {"class": "tsec-lead"}, "Open a government, or type an office or place. Each bar is the office's "
                                              "latest election on file; the office's Money tab has every election, "
                                              "with a Primary / General switch and a party filter."),
               filt, filter_empty_note("cb-offices"),
               h("div", {"class": "cb-all", "id": "cb-offices", "data-tf-deep": True}, blocks),
               h("p", {"class": "tnote"}, f"{n_off - len(rows)} offices have no campaign money on record (no report "
                                          "on file, or an election before 2023 with no news figures); ",
                 h("a", {"href": page.rel(om.HUB)}, "every office is on the Offices page"), ".")))
    page.add(_doors(page))
    page.add(_about(ed, page))
    page.add(moved_anchors_script(_index_moved(page)))
    page.finish(gaps=_gaps(ed), gaps_intro=None)
    return page


def _doors(page) -> Markup:
    """The other ways in: one line each."""
    links = [(BY_ELECTION, "By election", "every race of each cycle on one scale"),
             (BY_CANDIDATE, "By candidate", "every candidate and committee, alphabetical"),
             (BY_PLACE, "By place", "the map, and each government's races and reports"),
             (COMMITTEES, "Committees", "party, PAC and issue committees"),
             (FILINGS, "Every filing", "all reports and the large-contribution notices"),
             (cm.HOW_PAGE, "How campaign reporting works", "who files, what is public, how the guide adds it up")]
    return h("section", {"class": "tsec", "id": "more", "aria-labelledby": "more-h"},
             h("h2", {"class": "tsec-h", "id": "more-h"}, "Other ways in"),
             h("ul", {"class": "cb-doors"},
               [h("li", None, h("a", {"href": page.rel(p)}, t), h("span", {"class": "cb-door-d"}, d))
                for p, t, d in links if p in page.site.by_path]))


def moved_anchors_script(data: dict) -> Markup | None:
    """``#moved-anchors`` for static/js/moved.js: {"a": {old id: "relative/path.html#new"}, "p": {prefix: path}}."""
    import json
    if not data.get("a") and not data.get("p"):
        return None
    return Markup('<script type="application/json" id="moved-anchors">'
                  + json.dumps(data, sort_keys=True).replace("</", "<\\/") + "</script>")


def _index_moved(page) -> dict:
    """The index's old map and area list now live on By place (same ids)."""
    to = page.rel(BY_PLACE)
    a = {k: f"{to}#{k}" for k in ("map", "map-h", "areas", "areas-h", "cf-back", "cf-filter-h", "cf-list-tools",
                                  "cf-list-state", "cf-list-all")}
    p = {pre: to for pre in ("cf-areas-", "cmap-", "src-MAP-")}
    return {"a": a, "p": p}


# =========================================================================== By election

def build_by_election(site):
    ed = site.ed
    page = site.page(BY_ELECTION, body_class="thing-page")
    c = page.cites
    d = cf.cf_all(ed)
    races = d["races"]
    vmax = max((r[k] for r in races for k in ("raised", "spent") if r[k] is not None), default=100)
    page.add(browser_head(page, BY_ELECTION, ["Every local race of the 2026, 2024 and 2023 election cycles on one scale",
                                              "earlier elections as news coverage reported them"]))
    page.add(h("p", {"class": "cb-lead"}, NOT_SUPPORT))
    page.add(_legend())
    for cycle in reversed(list(cm.CYCLE_ELECTIONS)):
        pid, gid = cm.CYCLE_ELECTIONS[cycle]
        rs = [r for r in races if r["cycle"] == cycle]
        if not rs:
            continue
        spec = rs[0]["spec"]
        have = sorted([r for r in rs if r["spent"] is not None], key=lambda r: -r["spent"])
        none = sorted([r for r in rs if r["spent"] is None], key=lambda r: cm.natural(r["office"]))
        ordered = have + none
        rows = [_race_row(page, r) for r in ordered]
        sid = f"c-{cycle[:4]}"
        el_links = [h("a", {"href": page.rel(f"elections/{e}/index.html")}, lab)
                    for e, lab in ((pid, f"{cycle[:4]} primary"), (gid, f"{cycle[:4]} general election"))
                    if f"elections/{e}/index.html" in page.site.by_path]
        dates = f"primary {fmt_date(spec['primary'].isoformat())}, general {fmt_date(spec['general'].isoformat())}"
        body = [h("p", {"class": "tsec-lead"}, f"{len(rs)} races ({dates}); {len(have)} with reports on file. ",
                  "Election pages: " if el_links else None, join(el_links, " · ") if el_links else None)]
        title = f"{cycle[:4]} cycle: every race"
        if len(rows) > SHOW_CYCLE + 2:
            body.append(money_rows(f"cb-{sid}", f"{cycle[:4]}: the {SHOW_CYCLE} races with the most spending",
                                   rows[:SHOW_CYCLE], vmax=vmax, page=page, cite=c.cite("CFM-010"), status="computed",
                                   subtitle="All candidates, whole cycle. One scale for every chart on this page.",
                                   headers=["Race", "Raised", "Spent"]))
            body.append(see_all_fold(f"{sid}-all", len(rows), money_rows(
                f"cb-{sid}-rest", f"{cycle[:4]}: the other {len(rows) - SHOW_CYCLE} races", rows[SHOW_CYCLE:],
                vmax=vmax, page=page, headers=["Race", "Raised", "Spent"]),
                noun="race", hint=None, label=f"Show the other {len(rows) - SHOW_CYCLE} races"))
        else:
            body.append(money_rows(f"cb-{sid}", f"{cycle[:4]}: every race", rows, vmax=vmax, page=page,
                                   cite=c.cite("CFM-010"), status="computed",
                                   subtitle="All candidates, whole cycle. One scale for every chart on this page.",
                                   headers=["Race", "Raised", "Spent"]))
        page.add(h("section", {"class": "tsec", "id": sid, "aria-labelledby": f"{sid}-h"},
                   h("h2", {"class": "tsec-h", "id": f"{sid}-h"}, title), body))
    # ---- earlier elections: news reports (never added up here)
    by_year: OrderedDict = OrderedDict()
    for row in office_rows(ed):
        if row["state"]:
            continue
        m = om.money_model(ed, row["id"])
        for cyc in m["cycles"]:
            if cyc["reported"]:
                by_year.setdefault(cyc["year"], []).append((row, cyc))
    if by_year:
        items = []
        for y in sorted(by_year, reverse=True):
            for row, cyc in by_year[y]:
                kinds = []
                for contest, _rs in _contests_of(cyc["reported"]):
                    w = (f"{PARTY_WORD.get(contest['party_primary'], party_label(contest['party_primary']))} primary"
                         if contest["party_primary"] else "general election")
                    kinds.append(w)
                u = om.href(page, row["id"], "money")
                items.append(h("li", {"class": "cb-srow"},
                               h("span", {"class": "cb-year"}, y), " ",
                               h("a", {"href": f"{u}#y{y}"}, row["office"]["title"]) if u else row["office"]["title"],
                               h("span", {"class": "cb-srow-sub"},
                                 (", ".join(dict.fromkeys(kinds)) + ": " if kinds else "")
                                 + "figures as the articles reported them, rounded where they were")))
        page.add(h("section", {"class": "tsec", "id": "earlier", "aria-labelledby": "earlier-h"},
                   h("h2", {"class": "tsec-h", "id": "earlier-h"}, "Earlier elections: figures from news reports"),
                   h("p", {"class": "tsec-lead"}, "The county's posted reports begin with 2023. For earlier elections the "
                                                  "guide has only what news coverage reported; each office's Money tab "
                                                  "shows those figures in the articles' own words, on the same scale "
                                                  "as the filed ones. They are not added up here.", c.cite("CFM-002")),
                   h("ul", {"class": "cb-slist"}, items)))
    page.finish(gaps=_gaps(ed), gaps_intro=None)
    return page


def year_frag(ed, oid: str, year: str) -> str:
    """'#y<year>' when the office's Money tab has a section for that year (an election with money on record), else ''."""
    m = om.money_model(ed, oid) if oid else None
    return f"#y{year}" if m and any(c["year"] == year for c in m["cycles"]) else ""


def _race_row(page, race) -> dict:
    """One race as a bar row: linked to the office's Money tab at that year, else the area page's race card."""
    ed = page.ed
    oid = om.race_office_id(ed, race)
    u = om.href(page, oid, "money") if oid else None
    y = _race_year(race)
    if u:
        link = h("a", {"class": "cb-office", "href": u + year_frag(ed, oid, y)}, race["office"])
    else:
        area = cm.area_path(race["area"])
        link = (h("a", {"class": "cb-office", "href": page.rel(area) + f"#r-{race['id']}"}, race["office"])
                if area in page.site.by_path else h("span", {"class": "cb-office"}, race["office"]))
    n = len(race["candidates"])
    # 2026-11-18: incomplete is the * mark; complete, the normal case, carries no word
    sub = join([f"{race['n_with']} of {n} with reports", None if race["complete"] else figure_mark("incomplete")])
    return {"name": link, "sub": sub, "raised": race["raised"], "spent": race["spent"],
            "raised_text": cm.usd(race["raised"], "no reports on file"),
            "spent_text": cm.usd(race["spent"], "no reports on file"),
            "tip": f"{race['office']}: all candidates, whole {race['spec']['cycle']} cycle"}


# =========================================================================== By candidate

def candidate_model(ed) -> list[dict]:
    """Everyone with campaign money on record, one entry per person (people registry) or per name as recorded:
    {key, name, pid, items: [(year, words, (office id | None, year) | race)]}. Figures are the race model's own."""
    from . import money_history as mh
    reg = pp.registry(ed)
    people: OrderedDict = OrderedDict()

    def slot(name):
        p = reg.person(name)
        key = p.pid if p is not None else "n:" + name
        e = people.setdefault(key, {"key": key, "name": p.name if p is not None and p.page else name,
                                    "pid": p.pid if p is not None and p.page else None, "races": [], "news": [],
                                    "state": [], "party": set()})
        return e
    for race in sorted(cf.cf_all(ed)["races"], key=lambda r: r["date"], reverse=True):
        for cand in race["candidates"]:
            if not cand["committees"]:
                continue
            e = slot(cand["name"])
            e["races"].append((race, cand))
            if cand.get("party"):
                e["party"].add(cand["party"])
    for r in ed.table("cf_reported"):
        c = ed.contests.get(r["contest_id"])
        if c is None:
            continue
        e = slot(r["candidate"])
        if (c["contest_id"], c) not in [(x[0], x[1]) for x in e["news"]]:
            e["news"].append((c["contest_id"], c))
        if r.get("party"):
            e["party"].add(r["party"])
    for lp in mh.legislators(ed):
        e = slot(lp["name"])
        e["state"].append(lp)
        if lp.get("party"):
            e["party"].add(lp["party"])
    out = list(people.values())
    out.sort(key=lambda e: (cm.surname(e["name"]) or e["name"].lower(), e["name"].lower()))
    return out


def build_by_candidate(site):
    ed = site.ed
    page = site.page(BY_CANDIDATE, body_class="thing-page")
    c = page.cites
    model = candidate_model(ed)
    page.add(browser_head(page, BY_CANDIDATE, [f"{len(model)} candidates and committees with money on record",
                                               "alphabetical by surname, never ranked by money"]))
    page.add(h("p", {"class": "cb-lead"}, "Each name links to the person's page (Money tab) where the guide has one, "
                                          "otherwise to the office's Money tab. Figures are each candidate's whole-cycle "
                                          "sums from the reports on file; party as the records give it.",
               c.cite("CFM-010"), " ", status_badge("computed", page, "Sums of the reports on file.")))
    letters: OrderedDict = OrderedDict()
    for e in model:
        k = (cm.surname(e["name"])[:1] or e["name"][:1] or "#").upper()
        letters.setdefault(k if k.isalpha() else "#", []).append(e)
    blocks = []
    for L, es in letters.items():
        items = [_cand_item(page, e) for e in es]
        blocks.append(h("details", {"class": "cb-letter", "id": f"l-{L.lower() if L != '#' else 'other'}",
                                    "data-tf-group": True, "data-fold": "letter", "open": True},
                        h("summary", {"class": "cb-gov-sum"}, h("span", {"class": "cb-gov-name"}, L), " ",
                          h("span", {"class": "cb-gov-n"}, f"{len(es)}"),
                          h("span", {"class": "fold-toggle", "aria-hidden": "true"})),
                        h("ul", {"class": "cb-clist"}, items)))
    jump = h("p", {"class": "cb-jump"}, "Jump to: ",
             join([h("a", {"href": f"#l-{L.lower() if L != '#' else 'other'}"}, L) for L in letters], " "))
    page.add(h("section", {"class": "tsec", "id": "people", "aria-labelledby": "people-h"},
               h("h2", {"class": "tsec-h", "id": "people-h"}, "Every candidate and committee"),
               table_filter("cb-people", [], len(model), noun="name", search="Name or office",
                            label="Filter the names"),
               filter_empty_note("cb-people"), jump,
               h("div", {"class": "cb-all", "id": "cb-people", "data-tf-deep": True},
                 h("div", {"class": "cb-govs cb-letters"}, blocks))))
    page.add(h("p", {"class": "tnote"}, "Party, PAC and issue committees are on ",
               h("a", {"href": page.rel(COMMITTEES)}, "Committees"), "; every report is on ",
               h("a", {"href": page.rel(FILINGS)}, "Every filing"), ". The rules that join the same person's records "
               "are on the ", h("a", {"href": page.rel(pp.HUB)}, "People page"), "."))
    page.finish(gaps=_gaps(ed), gaps_intro=None)
    return page


def _cand_item(page, e) -> Markup:
    ed = page.ed
    lines = []
    texts = [e["name"]]
    for race, cand in e["races"]:
        oid = om.race_office_id(ed, race)
        u = om.href(page, oid, "money") if oid else None
        where = (h("a", {"href": u + year_frag(ed, oid, _race_year(race))}, race["office"]) if u else race["office"])
        lines.append(h("li", None, h("span", {"class": "cb-year"}, _race_year(race)), " ", where, ": ",
                       h("span", {"class": "cb-fig"}, f"{cm.usd(cand['spent'], 'not on file')} spent, "
                                                      f"{cm.usd(cand['raised'], 'not on file')} raised")))
        texts.append(race["office"])
    for cid, contest in e["news"]:
        oid = contest.get("office_id") or ""
        u = om.href(page, oid, "money") if oid else None
        y = om.contest_year(ed, contest)
        lab = contest.get("label") or cid
        lines.append(h("li", None, h("span", {"class": "cb-year"}, y), " ",
                       h("a", {"href": u + year_frag(ed, oid, y)}, lab) if u else lab, ": as reported in the news"))
        texts.append(lab)
    for lp in e["state"]:
        span = f"{lp['years'][0]}" if len(lp["years"]) == 1 else f"{lp['years'][0]} to {lp['years'][-1]}"
        lines.append(h("li", None, h("span", {"class": "cb-year"}, span), " ",
                       "State legislative committees, by filing year (a different basis)"))
        texts.append("state legislature")
    u = pp.href(page, e["pid"], "money") if e["pid"] else None
    if u is None and e["races"]:
        oid = om.race_office_id(ed, e["races"][0][0])
        u = om.href(page, oid, "money") if oid else None
    party = " · ".join(party_label(p) for p in sorted(e["party"]))
    return h("li", {"class": "cb-crow", "data-tf-row": True, "data-tf-text": " ".join(texts)},
             h("span", {"class": "cb-cname"}, h("a", {"href": u}, e["name"]) if u else e["name"],
               h("span", {"class": "cb-cparty"}, party) if party else None),
             h("ul", {"class": "cb-cfacts"}, lines))


# =========================================================================== By place

def build_by_place(site):
    from .campaign_pages import _areas_list, map_section
    ed = site.ed
    page = site.page(BY_PLACE, body_class="thing-page")
    d = cf.cf_all(ed)
    page.add(browser_head(page, BY_PLACE, ["Pick a kind of race, then a place",
                                           "each area's latest election, from the reports on file"]))
    page.add(map_section(ed, page, d))
    page.add(h("section", {"class": "tsec", "id": "areas", "aria-labelledby": "areas-h"},
               h("h2", {"class": "tsec-h", "id": "areas-h"}, "Every area"),
               h("p", {"class": "tsec-lead"}, "Each government's latest election, with links to its races, candidates "
                                              "and reports."),
               see_all_fold("areas-all", len(d["areas"]), _areas_list(ed, page, d["areas"]), noun="area", hint=None,
                            label=f"Show every area as a table ({len(d['areas']) + 1} areas, with the state legislature)")))
    page.finish(gaps=_gaps(ed), gaps_intro=None)
    return page


PAGES = {INDEX: build_by_office, BY_ELECTION: build_by_election, BY_CANDIDATE: build_by_candidate,
         BY_PLACE: build_by_place}
