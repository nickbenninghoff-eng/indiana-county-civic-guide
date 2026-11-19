"""Parts the government pages share (phase 6 step 3, 2026-11-16): compact office rows, the small locator map, the
contact section, the community strip, the holders-over-time list and the Money tab. Used by pages/places.py (cities,
towns, townships, school corporations), pages/county.py and pages/governments.py (the hub, libraries and special
units). No figure is computed here: every number comes from the helpers the old pages used (pages/money.py
_unit_charts and later_debt_note, civic/spending.py money_in_out, civic/tax_base.py tax_base_line, civic/answers.py
latest_unit_rate, pages/places.py _context_rows and _audits_block).

Party tags appear only in office rows (as on the Offices hub); money charts use the accent and ink marks only; the
community strip is placed by the callers after neutral sections, never beside results or party-control visuals
(neutrality review F6).
"""
from __future__ import annotations

import re

from civic import governments as gm
from civic import offices as om
from civic import tabs as T
from civic.components import data_table, name_with_party, see_all_fold, status_badge, status_label, term_party
from civic.data import fmt_date, split_ids
from civic.holder_rows import NO_HOLDER
from civic.html import Markup, h, join


def union(*groups) -> str:
    out = []
    for g in groups:
        for r in (g if isinstance(g, list) else [g]):
            ids = split_ids(r.get("source_ids")) if isinstance(r, dict) else split_ids(r)
            out += [i for i in ids if i not in out]
    return ";".join(out)


def marks_href(page) -> str | None:
    e = page.entry
    if e is None or not e.thing:
        return None
    return "#marks" if e.tab == "sources" else page.rel(T.tab_path(e.thing, "sources")) + "#marks"


def mark(page, status, note=None):
    return T.status_mark(status, page, note, sources_href=marks_href(page))


# =========================================================================== office rows

def office_row(ed, page, o: dict, *, title: str | None = None, extra=None, conflict: dict | None = None) -> Markup:
    """One compact row: office (a link to its office page), holder with party tag, next election. The row keeps the
    old officeholder card's id (office-<office_id>), so old links and the district maps' panels land on it."""
    c = page.cites
    oid = o["office_id"]
    cur, inc = ed.current_terms(oid), ed.incoming_terms(oid)
    link = om.href(page, oid)
    name = title or o["title"]
    head = h("a", {"class": "gov-office-name", "href": link}, name) if link else h("span", {"class": "gov-office-name"}, name)
    if conflict:
        who = [h("span", {"class": "gov-office-vacant"}, "Current holder disputed between sources: "), conflict["title"],
               " ", mark(page, "unverified", "Sources disagree."),
               " ", h("a", {"href": f"#conflict-{oid}"}, "See the conflict")]
    elif cur:
        who = [join([h("span", None, name_with_party(t["person"], term_party(t),
                                                     t.get("confidence") if term_party(t) else None))
                     for t in cur], ", "), c.cite(union(cur))]
    else:
        who = [h("span", {"class": "gov-office-vacant"}, NO_HOLDER)]
    incoming = None
    if inc:
        same = {t["person"] for t in cur} == {t["person"] for t in inc}
        starts = sorted({fmt_date(t["start"]) for t in inc if t.get("start")})
        st = "unofficial" if any(t.get("status") == "unofficial" for t in inc) else inc[0].get("status")
        if same:
            incoming = h("span", {"class": "gov-office-inc"}, "Re-elected" + (f"; new term from {starts[0]}" if starts else ""),
                         " ", mark(page, st), c.cite(union(inc)))
        else:
            incoming = h("span", {"class": "gov-office-inc"}, f"Incoming{' ' + starts[0] if starts else ''}: ",
                         join([name_with_party(t["person"], term_party(t)) for t in inc], ", "), " ", mark(page, st),
                         c.cite(union(inc)))
    nxt = o.get("next_election")
    return h("li", {"class": "gov-office", "id": f"office-{oid}"},
             head,
             h("span", {"class": "gov-office-who"}, who, h("br") if incoming else None, incoming),
             h("span", {"class": "gov-office-next"}, f"Next election {nxt}" if nxt else
               ("Appointed" if o.get("elected") == "no" else "Next election not in the guide's data")),
             h("span", {"class": "gov-office-extra"}, extra) if extra else None)


def office_list(ed, page, offices: list[dict], *, titles: dict | None = None, extras: dict | None = None,
                conflicts: dict | None = None) -> Markup:
    titles, extras, conflicts = titles or {}, extras or {}, conflicts or {}
    return h("ul", {"class": "gov-offices"},
             [office_row(ed, page, o, title=titles.get(o["office_id"]), extra=extras.get(o["office_id"]),
                         conflict=conflicts.get(o["office_id"])) for o in offices])


def office_list_first(ed, page, offices: list[dict], shown: int, fold_id: str, noun: str, *,
                      titles: dict | None = None) -> list:
    """office_list for a long list: the first ``shown`` rows, then the others in a "Show the other N" fold (ships open,
    so JavaScript off shows every row; folds.js closes it and opens it for a link to a row inside). Added
    2026-11-16 to bring the county Overview near 4 screens; every row and id stays on the page."""
    if len(offices) <= shown + 1:
        return [office_list(ed, page, offices, titles=titles)]
    rest = offices[shown:]
    return [office_list(ed, page, offices[:shown], titles=titles),
            see_all_fold(fold_id, len(rest), office_list(ed, page, rest, titles=titles),
                         label=f"Show the other {len(rest)} {noun}", hint=None)]


def offices_lead(ed) -> Markup:
    return h("p", {"class": "tsec-lead"},
             f"From the guide's terms data, as of {fmt_date(ed.as_of, long=True)}. One line per office, by office and "
             "district, never by party: who holds it and the next election. Each office's own page has what it does, "
             "every election, the campaign money on record and every holder.")


# =========================================================================== locator map

LAYER_FOR = {"city": "place", "town": "place", "township": "township", "school_corporation": "school"}


def locator_map(page, ed, g) -> Markup | None:
    """A small static map: the county outline with this government's area filled (the same Census shapes as the
    boundary map, civic/map.py; no new geometry). Not interactive and not a link; the Governments hub has the full
    map. Fills are type colors only, never party. None when the area has no shape (special units, libraries)."""
    from civic.map import load_shapes
    shapes = load_shapes(ed)
    if shapes is None:
        return None
    vb = shapes["viewBox"]
    if g.kind == "county":
        layer, me = "township", None
    else:
        layer = LAYER_FOR.get(g.kind)
        if not layer:
            return None
        me = next((it for it in shapes["layers"].get(layer, []) if it.get("id") == g.unit_id), None)
        if me is None:
            return None
    others = [h("path", {"d": it["d"], "class": "gov-loc-area"}) for it in shapes["layers"].get(layer, [])
              if it is not me]
    clip = h("defs", None, h("clipPath", {"id": "gov-loc-clip"}, h("path", {"d": shapes["county"]["d"]})))
    body = [h("g", {"clip-path": "url(#gov-loc-clip)"}, others)]
    if me is not None:
        body.append(h("g", {"clip-path": "url(#gov-loc-clip)"}, h("path", {"d": me["d"], "class": "gov-loc-me"})))
    county_cls = "gov-loc-county" + (" gov-loc-county-me" if g.kind == "county" else "")
    note = None
    if me is not None and me.get("share_inside") not in (None, "") and float(me["share_inside"]) < 0.97:
        note = (f"About {round(float(me['share_inside']) * 100)}% of the corporation's land area is inside the county; "
                "the map is cut at the county line.")
    where = "covers the whole county" if g.kind == "county" else f"in {ed.county_label}"
    label = f"Map: where {g.name} is {where}, shaded on the county outline."
    if g.kind == "county":
        label = f"Map: {ed.county_label}, with its townships outlined."
    svg = h("svg", {"class": "gov-loc-svg", "viewBox": f"{vb[0]} {vb[1]} {vb[2]} {vb[3]}", "role": "img",
                    "aria-label": label},
            clip, body, h("path", {"d": shapes["county"]["d"], "class": county_cls}))
    hub = page.rel(gm.HUB + "#map")
    return h("figure", {"class": "gov-loc"}, svg,
             h("figcaption", {"class": "gov-loc-cap"}, note + " " if note else "",
               h("a", {"href": hub}, "Every government on the map"),
               page.cites.cite_compact("MAP-001;MAP-002;MAP-003;MAP-004")))


# =========================================================================== contact

def contact_section(ed, page, unit: dict | None, extra=None) -> Markup:
    """Contact and meetings. Since 2026-11-18 (gap-fill round 2): one block per body from unit_contacts.csv
    (contact_rows / contact_block: office contacts only, the meeting rule exactly as stored with its schedule year and
    "as of" date, never inferred), then the government's website from units.csv when no row gives one. With no
    unit_contacts.csv row the section says where to look, as before."""
    c = page.cites
    rows = contact_rows(ed, page, unit)
    items = [contact_block(ed, page, r, named=len(rows) > 1 or bool(r.get("_other_unit"))) for r in rows]
    site_url = (unit or {}).get("website")
    if site_url and not any((r.get("website") or "").strip() for r in rows):
        items.insert(0, h("p", None, h("strong", None, "Website: "), _ext_link(site_url), c.cite(unit.get("source_ids"))))
    if not rows:
        if not site_url:
            items.append(h("p", {"class": "muted"}, "No website for this government is in the guide's data."))
        items.append(h("p", None, "The guide has no meeting schedule for this government: check the government's own "
                                  "website or call its office. ",
                       h("a", {"href": page.rel("your-governments/index.html#meetings")}, "Every government's website")
                       if "your-governments/index.html" in page.site.by_path else None, "."))
    else:
        items.append(h("p", {"class": "muted"}, "Meeting schedules change; check the body's own page before you go. "
                                                "Only office contacts are listed, never personal ones."))
    return T.tab_section("contact", "Contact and meetings", items, extra)


# personal mailbox domains (tools/check_gov.py rejects them in the GOV files; the page never prints one either)
PERSONAL_MAIL = re.compile(r"@(gmail|yahoo|sbcglobal|aol|hotmail|outlook|icloud|comcast|msn|live|att)\.", re.I)
CONTACT_FIELDS = ("phone", "office_address", "contact_url", "website", "meeting_rule", "meeting_place",
                  "meeting_info_url", "notes")


def contact_rows(ed, page, unit: dict | None) -> list[dict]:
    """unit_contacts.csv rows for the government whose page this is: rows whose gov_id is the unit (or a money id
    that the aliases map to it, or this page's own government id), then rows of bodies without a page of their own
    whose parent unit is this one (the county Board of Health on the county page; marked ``_other_unit``). A row
    with a personal mailbox in any field is never shown (data warning)."""
    ids = set()
    if unit:
        ids.add(unit["unit_id"])
    thing = page.entry.thing if page.entry is not None else ""
    m = re.match(r"governments/([^/]+)/$", thing or "")
    if m:
        ids.add(m.group(1))
        g = gm.by_id(ed).get(m.group(1))
        if g is not None:
            ids.update(g.money_ids)
            if g.unit_id:
                ids.add(g.unit_id)
    if not ids:
        return []
    own, other = [], []
    for r in ed.table("unit_contacts"):
        gid = (r.get("gov_id") or "").strip()
        uid = ed.unit_alias(gid) or gid
        if PERSONAL_MAIL.search(" ".join(r.get(k) or "" for k in CONTACT_FIELDS)):
            msg = f"unit_contacts: {gid} / {r.get('body')} has a personal mailbox; not shown"
            if msg not in ed.warnings:
                ed.warnings.append(msg)
            continue
        if gid in ids or uid in ids:
            own.append(r)
            continue
        u = ed.units.get(uid) or {}
        parents = split_ids(u.get("parent_unit_ids"))
        if ids & set(parents) and gm.gov_for_unit(ed, uid) is None and gm.gov_for_money_id(ed, gid) is None:
            other.append(dict(r, _other_unit=u.get("name") or uid))
    return own + other


def _ext_link(url: str, text: str | None = None):
    """An outside link (new tab) for an http(s) address. A mailto: address is printed as the address, not linked (the
    site links no mailto:, tel: or script schemes; tools/site/check.py); anything else is printed as text."""
    url = (url or "").strip()
    if re.match(r"(?i)^https?://", url):
        return h("a", {"href": url, "target": "_blank", "rel": "noopener"}, text or url)
    if url.lower().startswith("mailto:"):
        return h("span", {"class": "mono"}, url[7:])
    return url


def meeting_text(r: dict) -> list:
    """The meeting rule exactly as stored, then when it was printed for and read ("2026 schedule · as of
    November 18, 2026"); with no stored rule, where the schedule is (never inferred from a list of dates)."""
    rule = (r.get("meeting_rule") or "").strip()
    when = []
    if (r.get("schedule_year") or "").strip():
        when.append(f"{r['schedule_year'].strip()} schedule")
    if (r.get("as_of") or "").strip():
        when.append(f"as of {fmt_date(r['as_of'].strip(), long=True)}")
    tail = h("span", {"class": "gov-contact-when muted"}, " (" + " · ".join(when) + ")") if when else None
    info = (r.get("meeting_info_url") or "").strip()
    where = info or (r.get("website") or "").strip()
    if rule:
        more = [" ", _ext_link(info, "Meeting page")] if info else []
        return [h("span", {"class": "gov-contact-rule"}, rule), tail, more]
    if where:
        return [h("span", None, "No stated meeting rule in the guide's data; the schedule is on the body's site: "),
                _ext_link(where), tail]
    return [h("span", {"class": "muted"}, "No meeting rule or schedule page in the guide's data."), tail]


def contact_block(ed, page, r: dict, named: bool = True) -> Markup:
    """One body's office contacts and meetings, as a short definition list (no box)."""
    c = page.cites
    body = (r.get("body") or "").strip()
    title = body or r.get("_other_unit") or ""
    if r.get("_other_unit") and body and r["_other_unit"] not in body:
        title = f"{body} ({r['_other_unit']})"
    rows = []
    if (r.get("phone") or "").strip():
        rows.append(("Office phone", r["phone"].strip()))
    if (r.get("office_address") or "").strip():
        rows.append(("Office", r["office_address"].strip()))
    if (r.get("contact_url") or "").strip():
        url = r["contact_url"].strip()
        rows.append(("Office email" if url.lower().startswith("mailto:") else "Contact", _ext_link(url, "Contact page")))
    if (r.get("website") or "").strip():
        rows.append(("Website", _ext_link(r["website"])))
    rows.append(("Meetings", meeting_text(r)))
    if (r.get("meeting_place") or "").strip():
        rows.append(("Where", r["meeting_place"].strip()))
    if (r.get("notes") or "").strip():
        rows.append(("Note", r["notes"].strip()))
    flags = [mark(page, r.get("status"))]
    if (r.get("confidence") or "").strip().lower() == "low":
        flags.append(mark(page, "low"))
    return h("div", {"class": "gov-contact", "id": f"contact-{_slug(title or r.get('gov_id', ''))}"},
             h("h3", {"class": "gov-contact-h"}, title) if named and title else None,
             h("dl", {"class": "gov-contact-dl"}, [[h("dt", None, k), h("dd", None, v)] for k, v in rows]),
             h("p", {"class": "gov-contact-src muted"}, "Office contacts", flags, c.cite(r.get("source_ids"))))


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-") or "body"


# =========================================================================== community strip

def community_strip(ed, page, rows: list[dict], more: tuple[str, str] | None, name: str) -> Markup | None:
    """The fixed community indicators (pages/places.py _context_rows: the same five ACS indicators and the change in
    population since 2010 that the place pages showed, each with its margin of error), as one short list, then the
    full table behind "Show the table"."""
    if not rows:
        return None
    c = page.cites
    items, trs = [], []
    for r in rows:
        flags = [mark(page, s, n) for s, n in r["marks"]]
        items.append(h("li", {"class": "gov-ctx-item"},
                       h("span", {"class": "gov-ctx-label"}, r["label"]),
                       h("span", {"class": "gov-ctx-value"}, r["value"]),
                       h("span", {"class": "gov-ctx-moe"}, r["moe_text"]),
                       h("span", {"class": "gov-ctx-vintage"}, r["vintage"], " ", flags, c.cite(r["source_ids"]),
                         r.get("tail") or "")))
        trs.append([r["label"], r["value"], r["moe_text"], r["vintage"],
                    h("span", None, join([status_label(s, page, n) for s, n in r["marks"]], " "), r.get("tail") or "")])
    from civic.components import see_all_fold
    table = see_all_fold(f"context-{name}-table", len(trs),
                         data_table(f"context-{name}", ["Indicator", "Estimate", "Margin of error", "Vintage", "Status"],
                                    trs, caption="Community context", numeric=(1, 2), min_width="40rem"),
                         noun="indicator", label="Show the table")
    links = []
    if more and more[0].split("#")[0] in page.site.by_path:
        links.append(h("a", {"href": page.rel(more[0])}, more[1]))
    if "community/index.html" in page.site.by_path:
        links.append(h("a", {"href": page.rel("community/index.html")}, "The community: every indicator, every place"))
    return T.tab_section("context", "The community", h("ul", {"class": "gov-ctx"}, items),
                         h("p", {"class": "tnote gov-ctx-note"},
                           "American Community Survey 5-year estimates: period estimates with a margin of error, not "
                           "point-in-time counts. Dollar figures are in the vintage's final-year dollars. ",
                           join(links, " · ") if links else None),
                         table)


# =========================================================================== holders over time

def holders_section(ed, page, offices: list[dict], lead: str | None = None) -> Markup | None:
    """Holders over time: one line per office with a History tab, linking to it (the full holder tables live on the
    office pages)."""
    rows = []
    for o in offices:
        terms = ed.terms_for(o["office_id"])
        u = om.href(page, o["office_id"], "history")
        if not terms or not u:
            continue
        people = len({t["person"] for t in terms})
        years = sorted(t["start"][:4] for t in terms if (t.get("start") or "")[:4].isdigit())
        span = f", from {years[0]}" if years else ""
        rows.append(h("li", None, h("a", {"href": u}, f"{o['title']}: every holder"),
                      h("span", {"class": "muted"}, f" · {len(terms)} term{'s' if len(terms) != 1 else ''}, "
                                                    f"{people} {'people' if people != 1 else 'person'}{span}")))
    if not rows:
        return None
    return T.tab_section("holders", "Holders over time", h("ul", {"class": "gov-holders"}, rows),
                         lead=lead or "Every holder in the guide's records is on each office's History tab. The "
                                      "officeholder records mostly begin in 2010.")


# =========================================================================== Money tab

def _money_ids(ed, g) -> list[str]:
    return list(g.money_ids)


def budget_section(ed, page, g, latest=None) -> Markup | None:
    """Budget over time: the budgets page's own charts for the unit (pages/money.py _unit_charts, one per reporting
    basis, with series breaks and flagged changes), each with its table behind "Show the table"; figures kept out of
    the charts in a table; the nominal / constant-dollar switch."""
    from pages import money as M
    mo = M.money(ed)
    c = page.cites
    charts, others = [], []
    src = page.entry.thing if page.entry is not None else ""
    gaps_href = page.rel(T.tab_path(src, "sources")) + "#gaps" if src else "#gaps"
    for mid in _money_ids(ed, g):
        ch, ot = M._unit_charts(mo, page, mid, {}, gaps_href=gaps_href)
        charts += ch
        others += ot
    if not charts and not others and latest is None:
        return None
    parts = []
    if latest is not None:
        parts.append(latest)
    if charts:
        parts.append(M._dollars_toggle(mo, page))
        parts.append(h("div", {"class": "chart-grid gov-wide"}, charts))
        if any(j["unit"] in g.money_ids for j in mo.jumps):
            parts.append(h("p", {"class": "tnote"}, "A ", h("span", {"class": "mn-flag-key", "aria-hidden": "true"}, "!"),
                           " marks a change of more than 40% from one year to the next that no recorded change in "
                           "reporting explains; it is listed under Gaps on the Sources tab. ",
                           mark(page, "computed", "Flags come from the guide's own year-over-year comparison.")))
    if others:
        orow = []
        for s, r in sorted(others, key=lambda t: (t[1]["year"], t[0]["id"])):
            orow.append([r["year"], M.usd(r["amount"]), M.BASIS.get(r["basis"], (r["basis"],))[0],
                         r["adopted_or_actual"], h("span", None, status_label(r["status"], page), c.cite(r["source_ids"])),
                         M.clean_note(M.strip_whole_corp(r["notes"]))])
        mid0 = g.money_ids[0] if g.money_ids else g.gid
        parts.append(h("div", {"class": "mn-others"},
                       h("p", {"class": "mn-others-h"}, "Other reported figures, not charted (different scope, proposed, "
                                                       "or one news report):"),
                       data_table(f"other-{mid0}", ["Year", "Amount", "Basis", "Kind", "Status", "Note"], orow,
                                  caption=f"{g.name}: other reported budget figures", numeric=(1,), min_width="48rem")))
    compare = page.rel("money/budgets/index.html") if "money/budgets/index.html" in page.site.by_path else None
    parts.append(h("p", {"class": "tnote"}, "Nominal dollars unless switched. A chart never mixes two ways of totaling "
                                            "a budget. ",
                   h("a", {"href": compare}, "Compare every unit's budget") if compare else None,
                   " · " if compare else None,
                   h("a", {"href": page.rel("money/what-is-a-budget/index.html")}, "What counts as a budget?")
                   if "money/what-is-a-budget/index.html" in page.site.by_path else None))
    return T.tab_section("budget", "Budget over time", parts)


def flows_section(ed, page, g) -> Markup | None:
    """Money in and money out: the state annual-report charts (civic/spending.py money_in_out), the same block the
    place, school and county pages showed in a fold, now open: income by source, spending by purpose and by type,
    and the money that only passes through, each chart with its table."""
    from civic.spending import has_money_in_out, money_in_out
    blocks = [money_in_out(ed, page, mid, level=3, label="Money in and money out")
              for mid in _money_ids(ed, g) if has_money_in_out(ed, mid)]
    blocks = [b for b in blocks if b]
    if not blocks:
        return None
    # in a fold (closed with JavaScript on; open without it, and a link into it opens it) so the tab stays short
    return T.tab_section("money-in-out", "Money in and money out",
                         see_all_fold("money-in-out-all", 0, blocks, label="Show money in and money out: income by "
                                      "source, spending by purpose and type", hint=None),
                         lead="Actual figures from the annual financial report the unit files with the state: a "
                              "different scope from the adopted budgets above.")


def tax_section(ed, page, g, extra: str = "") -> Markup | None:
    """The tax base (certified net assessed value) and the unit's certified tax rate."""
    from civic.answers import _num, latest_unit_rate
    from civic.tax_base import money_id as tax_base_id, tax_base_line
    c = page.cites
    parts = []
    mid = next((m for m in g.money_ids), None)
    base = tax_base_line(ed, page, mid or (tax_base_id(ed, g.unit_id) if g.unit_id else None),
                         county_label=ed.county_label, extra=extra)
    if base:
        parts.append(base)
    r = latest_unit_rate(ed, g.unit_id) if g.unit_id else None
    if r:
        parts.append(h("p", None, f"Certified tax rate for taxes payable in {r['year']}: "
                                  f"${_num(r['rate_per_100']):.4f} per $100 of assessed value. ",
                       status_badge(r["status"], page), c.cite(r["source_ids"]), " ",
                       h("a", {"href": page.rel("money/your-tax-bill/index.html#all-rates")}, "Every unit's rate and your tax bill")
                       if "money/your-tax-bill/index.html" in page.site.by_path else None))
    if not parts:
        return None
    return T.tab_section("tax-base", "Tax base and tax rate", parts)


def debt_section(ed, page, g) -> Markup | None:
    """Debt: the unit's rows in the state's 2024 debt file (pages/money.py unit_debt_parts: total, then by class) and
    the unit's own later totals, which are never charted with them."""
    from pages import money as M
    mo = M.money(ed)
    parts = []
    for mid in _money_ids(ed, g):
        parts += M.unit_debt_parts(mo, page, mid)
    if not parts:
        return None
    return T.tab_section("debt", "Debt", parts)


def breakdown_section(ed, page, g) -> Markup | None:
    from pages import money as M
    mo = M.money(ed)
    parts = []
    for mid in _money_ids(ed, g):
        if any(r["unit_id"] == mid and r["year"] == "2024" and r["basis"].startswith("afr_2024") for r in mo.breakdowns):
            parts += M.breakdown_parts(mo, page, mid)
    if not parts:
        return None
    return T.tab_section("breakdowns", "2024 spending and revenue, by department and class",
                         see_all_fold("breakdowns-all", 0, parts, label="Show the 2024 breakdowns", hint=None),
                         lead="From the annual financial report units file with the state. These files have their own "
                              "scope (each chart's note says what it covers); they are not the budget totals above.")


def other_breakdowns_section(ed, page, g) -> Markup | None:
    """Other breakdowns (added 2026-11-18, phase 6 step 5, when money/budgets/ became Compare budgets): proposed
    figures, a later budget year and news-reported department amounts, as tables (pages/money.py
    other_breakdown_parts; the same ids the budgets page had). Folded, after the 2024 breakdowns."""
    from pages import money as M
    mo = M.money(ed)
    parts = []
    for mid in _money_ids(ed, g):
        parts += M.other_breakdown_parts(mo, page, mid)
    if not parts:
        return None
    return T.tab_section("other-breakdowns", "Other breakdowns: proposed, later years, news reports",
                         see_all_fold("other-breakdowns-all", 0, parts, label="Show the other breakdowns", hint=None),
                         lead="Each has its own scope, so they are tables, not charts, and are not the totals above.")


def money_tab(ed, page, g, *, latest=None, before=None, after=None, tax_extra: str = "") -> None:
    """The Money tab: budget over time first (chart, then the table behind "Show the table"), then the tax base and rate, debt,
    money out (folded), the 2024 breakdowns (folded), and the caller's extra sections (state audits). A cross-county
    school corporation's tab opens with the whole-corporation note, once (2026-11-18; pages/money.py
    whole_corporation_note)."""
    from pages import money as M
    page.add(*[x for x in (M.whole_corporation_note(M.money(ed), page, set(_money_ids(ed, g))), before) if x])
    # the short sections (tax base, debt) come before the two long folded ones
    page.add(*[x for x in (budget_section(ed, page, g, latest), tax_section(ed, page, g, tax_extra),
                            debt_section(ed, page, g), flows_section(ed, page, g),
                            breakdown_section(ed, page, g), other_breakdowns_section(ed, page, g)) if x])
    page.add(*[x for x in (after or []) if x])


def money_gaps(ed, g) -> list[dict]:
    """The budgets page's gaps that are about this unit: its flagged year-over-year changes, and the money gaps whose
    wording names it."""
    from pages import money as M
    mo = M.money(ed)
    rows: list[dict] = []
    for m in g.money_ids:
        lab = mo.label(m)
        rows += [r for r in mo.jump_gap_rows() if r["item"].startswith(lab + " ")]
    names = {g.name, g.short} | {re.sub(r" \(.*\)$", "", mo.label(m)) for m in g.money_ids}
    pat = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True) if n)
    if pat:
        rows += [r for r in M.money_gaps(ed, pat) if r not in rows]
    return rows


# =========================================================================== appointed board rosters (2026-11-18)

def board_members(ed, board_id: str) -> list[dict]:
    """appointed_board_members.csv rows of one board, in file order (the board page's own order)."""
    return [r for r in ed.table("appointed_board_members") if (r.get("board_id") or "").strip() == board_id]


def _member_term(r: dict) -> str:
    """'Feb 13, 2026 to Dec 31, 2026', 'Term ends Dec 31, 2026', 'Since Feb 13, 2026', or the notes' "Term: ..."
    words; '' when nothing is printed."""
    s, e = (r.get("term_start") or "").strip(), (r.get("term_end") or "").strip()
    fs, fe = (fmt_date(s) or s) if s else "", (fmt_date(e) or e) if e else ""
    m = re.search(r"\bTerm:\s*([^.;]+)", r.get("notes") or "")
    words = f"Term {m.group(1).strip()}" if m else ""
    if s and e:
        out = f"{fs} to {fe}"
    elif e:
        out = f"Term ends {fe}"
    elif s:
        out = f"Since {fs}"
    else:
        out = ""
    return "; ".join(x for x in (out, words) if x)


def board_roster(ed, page, board: dict, fold_id: str | None = None) -> Markup | None:
    """Who sits on one appointed board, from appointed_board_members.csv, in a fold that ships open (folds.js closes
    it): name, role, who appointed them and the printed term. A vacant seat says so; a holdover (printed term ended,
    a later official record shows the person still serving) is marked with the date of that record. The count is of
    the people listed, never of the seats the law allows: South Bend's Board of Public Safety lists three members, so
    the fold says three (data/SCHEMA.md). Never party, address or contact details. None when no member row exists."""
    rows = board_members(ed, board["board_id"])
    if not rows:
        return None
    c = page.cites
    people = [r for r in rows if (r.get("person") or "").strip()]
    vacant = [r for r in rows if not (r.get("person") or "").strip()]
    items = []
    for r in rows:
        who = (r.get("person") or "").strip()
        bits = []
        if (r.get("role") or "").strip():
            bits.append(r["role"].strip())
        if (r.get("appointed_by") or "").strip():
            bits.append(f"appointed by {r['appointed_by'].strip()}")
        term = _member_term(r)
        if term:
            bits.append(term)
        hold = (r.get("holdover") or "").strip().lower() == "yes"
        note = (r.get("notes") or "").strip()
        flags = [mark(page, r.get("status"))]
        if (r.get("confidence") or "").strip().lower() == "low":
            flags.append(mark(page, "low"))
        items.append(h("li", {"class": "gov-member" + (" gov-member-vacant" if not who else ""),
                              "id": f"m-{r['member_id']}" if re.fullmatch(r"[A-Za-z0-9-_]+", r.get("member_id") or "") else None},
                       h("span", {"class": "gov-member-name"}, who or "Vacant seat"),
                       h("span", {"class": "gov-member-meta"}, " · ".join(bits)) if bits else None,
                       h("span", {"class": "gov-member-hold"},
                         f"Holdover: printed term ended; still serving as of {fmt_date(r.get('as_of') or '') or 'a later record'}")
                       if hold else None,
                       h("span", {"class": "gov-member-note muted"}, note) if note and not re.fullmatch(r"Term:[^.;]*\.?", note) else None,
                       flags, c.cite(r.get("source_ids"))))
    n, nv = len(people), len(vacant)
    count = f"{n} member{'s' if n != 1 else ''} listed" + (f", {nv} vacant seat{'s' if nv != 1 else ''}" if nv else "")
    as_of = max((r.get("as_of") or "") for r in rows)
    seats = (board.get("seats") or "").strip()
    lead = [f"Seats: {seats}. " if seats else "Seat count not in the guide's sources. ",
            f"The guide lists the {count.replace(' listed', '')} its sources name"
            + (f", as of {fmt_date(as_of, long=True)}" if as_of else "") + "."]
    if seats.isdigit() and n + nv < int(seats):
        lead.append(f" The other {int(seats) - n - nv} seat{'s are' if int(seats) - n - nv != 1 else ' is'} not in "
                    "the guide's sources, so they are not shown as filled or vacant.")
    fid = fold_id or f"roster-{board['board_id']}"
    return h("details", {"class": "fold-details gov-roster", "id": fid, "data-fold": True, "open": True},
             h("summary", {"class": "fold-summary gov-roster-sum"},
               h("span", {"class": "gov-roster-name"}, board.get("name") or board["board_id"]),
               h("span", {"class": "gov-roster-n"}, f" · {count}"),
               h("span", {"class": "fold-toggle", "aria-hidden": "true"})),
             h("div", {"class": "gov-roster-body"},
               h("p", {"class": "gov-roster-lead muted"}, lead),
               h("ul", {"class": "gov-members"}, items)))


def board_rosters(ed, page, boards: list[dict], heading: str | None = "Who serves on them") -> list:
    """Every board's roster fold (board_roster), under one small heading; [] when no board has members on file."""
    folds = [x for x in (board_roster(ed, page, b) for b in boards) if x is not None]
    if not folds:
        return []
    return ([h("h3", {"class": "gov-roster-h"}, heading)] if heading else []) + [
        h("div", {"class": "gov-rosters"}, folds),
        h("p", {"class": "muted gov-roster-foot"}, "Members as each board's own page or minutes list them. The guide "
                                                    "records no party, address or contact details for appointees.")]
