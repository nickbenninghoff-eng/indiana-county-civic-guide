"""Landing page (ux-review section 4): computed layer diagram with a place picker,
'next on your ballot' strip, five primary + two secondary path cards, context strip."""
from __future__ import annotations

from civic import sitemap
from civic.charts import DOT_KINDS, seat_dots
from civic.components import APPOINTED_NOTE, as_of_note, bodies_block, scope_badge, status_badge
from civic.data import fmt_date, fmt_int, fmt_pct
from civic.html import Markup, h, join, json_script
from civic.layers import build_layers, election_dates
from civic.map import boundary_map, load_shapes
from civic.picker import picker_state, place_picker

# No place is preselected (a returning reader's saved place is restored by static/js/here.js).
# Kept for callers that still import it.
DEFAULT_PLACE = "south-bend"


def _unknown_split(ed, L) -> tuple[int, int]:
    """(elected, appointed) counts of seat-count-unknown markers in a layer. The headline's
    'at least' qualifies elected seats, so an appointed board with no seat count must not trigger it."""
    appointed_titles = {b["name"] for b in ed.boards} | {o["title"] for o in ed.tables["offices"] if o.get("elected") == "no"}
    el = ap = 0
    for g in L.groups:
        u = g.kinds.count("unknown")
        if not u:
            continue
        if g.titles and all(t in appointed_titles for t in g.titles):
            ap += u
        else:
            el += u
    return el, ap


def _layer_row(page, L, visible: bool) -> Markup:
    groups = []
    for g in L.groups:
        if not g.kinds:
            continue
        tip = f"{g.label}: {g.summary()}"
        notes = [n for n in g.notes if n]
        groups.append(h("div", {"class": "seat-group", "tabindex": "0", "data-tv": g.summary(), "data-tl": g.label
                                + (f" · {notes[0]}" if notes else "")},
                        seat_dots(g.kinds, tip),
                        h("span", {"class": "seat-group-label"}, g.label)))
    layer_sources = [x for g in L.groups for x in g.sources]
    counts = []
    if L.elected:
        counts.append(f"{L.elected} elected")
    if L.vote:
        counts.append(f"you vote for {L.vote}")
    if L.appointed:
        counts.append(f"{L.appointed} appointed")
    if L.unknown:
        counts.append("some seat counts not in data")
    summary = " · ".join(counts) if counts else "no seats in the guide's data yet"
    rid = L.layer_id.replace(":", "-")
    unk_el, unk_ap = _unknown_split(page.cites.ed, L)
    bodies = bodies_block(page.cites.ed, L.offices, note=False) if L.offices else None
    appointed_line = h("p", {"class": "party-asof muted"}, APPOINTED_NOTE) if L.appointed and not L.placeholder else None
    return h("div", {"class": "layer" + (" layer-placeholder" if L.placeholder else ""), "id": f"layer-{rid}",
                     "data-layer": L.layer_id, "data-key": L.key, "data-elected": L.elected, "data-vote": L.vote,
                     "data-appointed": L.appointed, "data-unknown": unk_el, "data-unknown-appointed": unk_ap, "data-gov": 1 if L.government else 0,
                     "data-next": _next_attr(L), "hidden": None if visible else True},
             h("div", {"class": "layer-head"},
               h("span", {"class": "layer-name"}, h("span", {"class": "layer-title"}, L.title), page.cites.cite_compact(layer_sources) if layer_sources else None),
               h("span", {"class": "layer-leader", "aria-hidden": "true"}),
               h("span", {"class": "layer-count mono"}, summary),
               h("button", {"type": "button", "class": "layer-toggle btn btn-small", "aria-expanded": "false",
                            "aria-controls": f"seats-{rid}", "id": f"toggle-{rid}"}, "Show seats")),
             h("div", {"class": "layer-seats", "id": f"seats-{rid}"}, groups, bodies, appointed_line,
               h("p", {"class": "layer-note"}, L.note) if L.note else None))


def _next_attr(L) -> str:
    import json
    return json.dumps(L.next, separators=(",", ":"))


def _select(sel_id: str, label: str, options: list[tuple[str, str]], selected: str, groups: dict | None = None) -> Markup:
    if groups:
        opts = []
        for gl, items in groups.items():
            opts.append(h("optgroup", {"label": gl}, [h("option", {"value": v, "selected": v == selected}, t) for v, t in items]))
    else:
        opts = [h("option", {"value": v, "selected": v == selected}, t) for v, t in options]
    return h("div", {"class": "field", "id": f"{sel_id}-field"},
             h("label", {"for": sel_id}, label), h("select", {"id": sel_id, "name": sel_id}, opts))


def build(site):
    ed = site.ed
    page = site.page("index.html", banners=True, body_class="is-landing")
    cfg = ed.config
    data = build_layers(ed)
    layers = data["layers"]
    places = data["places"]
    place, sel_town, sel_school, visible_ids = picker_state(data, None)
    vis = [L for L in layers.values() if L.layer_id in visible_ids]
    n_gov = sum(1 for L in vis if L.government)
    n_elected = sum(L.elected for L in vis)
    n_vote = sum(L.vote for L in vis)
    n_app = sum(L.appointed for L in vis)
    n_unknown = sum(_unknown_split(ed, L)[0] for L in vis)
    n_unknown_app = sum(_unknown_split(ed, L)[1] for L in vis)

    # ---------------------------------------------------------------- hero
    elections = ed.elections
    def latest_official(kind):
        rows = [e for e in elections.values() if e["type"] == kind and e["status"] == "official" and e.get("turnout_pct")]
        return max(rows, key=lambda e: e["date"]) if rows else None
    prim, mprim = latest_official("primary"), latest_official("municipal_primary")
    turnout = []
    if prim:
        turnout.append(h("span", None, f"In the {prim['date'][:4]} primary, ",
                         h("strong", {"class": "fig"}, fmt_pct(prim["turnout_pct"])),
                         " of registered voters in the county cast a ballot", page.cites.cite(prim["source_ids"]), ". "))
    if mprim:
        turnout.append(h("span", None, f"In the {mprim['date'][:4]} city and town primary, ",
                         h("strong", {"class": "fig"}, fmt_pct(mprim["turnout_pct"])),
                         " did (registered voters in the cities and towns only)", page.cites.cite(mprim["source_ids"]), ". "))
    township_rule = ed.unit_types.get("township", {})
    # Header (Nick, 2026-11-09: "By the numbers"): the whole county, not one address. The guide is a central reference
    # for the county's governments, elections and money; the per-address counts live with the picker below.
    state_units = {u["unit_id"] for u in ed.tables["units"] if u["unit_type"] == "state_chamber"}
    n_local_gov = sum(1 for u in ed.tables["units"] if u["unit_id"] not in state_units)
    elected_offices = [o for o in ed.tables["offices"] if o.get("elected") == "yes"]
    n_local_seats = sum(int(o.get("seats") or 1) for o in elected_offices if o["unit_id"] not in state_units)
    n_state_seats = sum(int(o.get("seats") or 1) for o in elected_offices if o["unit_id"] in state_units)
    broad = sorted(e[:4] for e, el in elections.items()
                   if sum(1 for c in ed.contests.values() if c["election_id"] == e) >= 10)
    first_all = broad[0] if broad else None
    first_any = min(e[:4] for e in elections) if elections else None

    def go(path, label):
        return h("a", {"href": page.rel(path)}, label) if path in site.by_path else None
    jumps = [x for x in (go("officeholders/index.html", "Who holds every seat"),
                         go("elections/results/index.html", "Results"),
                         go("elections/margins/index.html", "Close races"),
                         go("money/campaigns/index.html", "Campaign money"),
                         go("elections/calendar/index.html", "What's on the next ballot")) if x]
    since = (f"Election results from {first_all} on" + (f" (South Bend mayor back to {first_any})"
                                                        if first_any and first_any < first_all else "")
             if first_all else "Election results")
    hero = h("section", {"class": "hero", "aria-labelledby": "hero-h"},
             h("h1", {"id": "hero-h", "class": "hero-h"},
               h("span", {"class": "hl-line"}, "One county."),
               h("span", {"class": "hl-line"}, f"{n_local_gov} local governments."),
               h("span", {"class": "hl-line"}, f"{n_local_seats} elected seats.")),
             h("p", {"class": "hero-dek"},
               f"{since}, who holds every seat now, and the campaign money behind them: one sourced reference for "
               f"{ed.county_label}'s governments and elections. Voters here also help elect {n_state_seats} state "
               "legislators. ",
               status_badge("computed", page, "Counted from the guide's units and offices tables.")),
             h("p", {"class": "hero-turnout"}, turnout, status_badge("official", page)),
             h("p", {"class": "hero-cta"}, [[" · " if i else "", x] for i, x in enumerate(jumps)]),
             h("p", {"class": "hero-cta hero-cta-place"}, "Looking for what covers one address? ",
               h("a", {"href": "#pick"}, "Pick your place"), " or ", h("a", {"href": "#paths"}, "pick where to start"), "."))
    # the per-address counts (here.js fills data-count): moved from the old header to the picker
    place_counts = h("div", {"class": "pick-counts"},
        h("p", {"class": "pick-counts-h"},
          h("span", {"data-count": "atleast-gov", "hidden": None if place is None else True}, "At least "),
          h("strong", {"data-count": "gov"}, n_gov), " governments and ",
          h("span", {"data-count": "atleast", "hidden": None if (n_unknown or place is None) else True}, "at least "),
          h("strong", {"data-count": "elected"}, n_elected), " elected seats cover ",
          h("span", {"data-count": "noplace", "hidden": None if place is None else True}, "every address. "),
          h("span", {"data-count": "noplace-alt", "hidden": True if place is None else None}, "this place. ")),
        h("p", {"class": "muted"},
          f"Everyone in {ed.county_label} lives under the state, the county, a township", page.cites.cite(township_rule.get("source_ids")),
          " and a school corporation, and many also live in a city or town. Each has its own officials, and its seats come up "
          "in different years. ", h("span", {"data-count": "noplace", "hidden": None if place is None else True},
            "Pick your place to count yours. "),
          "You vote for ", h("strong", {"data-count": "vote"}, n_vote), " of the elected seats shown below; ",
          h("span", {"data-count": "atleast-appointed", "hidden": None if n_unknown_app else True}, "at least "),
          h("span", {"data-count": "appointed"}, n_app), " more seats are appointed",
          h("span", {"data-count": "appointed-unknown-note", "hidden": None if n_unknown_app else True},
            " (some appointed boards' seat counts are not in the guide's data)"), "."))

    # ---------------------------------------------------------------- picker: the map is the front door
    shapes = load_shapes(ed)
    cmap = boundary_map(page, ed, shapes) if shapes else None
    pick = h("section", {"class": "pick", "id": "pick", "aria-labelledby": "pick-h"},
             h("h2", {"id": "pick-h", "class": "section-h pick-title"},
               "Pick your place on the map or below" if cmap else "Pick your place"),
             place_counts,
             h("div", {"class": "pick-grid" + ("" if cmap else " pick-grid-solo")},
               h("div", {"class": "pick-map"},
                 h("p", {"class": "pick-step mono"}, "On the map"),
                 cmap,
                 h("p", {"class": "muted pick-map-note"},
                   "Choose a city, town or township on the map (switch to Townships or School corporations with the buttons "
                   "above it). Shading shows the type of government only, never party. ",
                   h("a", {"href": page.rel("map/index.html")}, "Full-size map with every area listed"), ".",
                   page.cites.cite_compact("MAP-001;MAP-002;MAP-003;MAP-004"))) if cmap else None,
               place_picker(page, data, intro=h("p", {"class": "pick-step mono"}, "Or choose from the lists"))))

    order = ["state", "county", "township", "municipality", "school", "library"]
    rows = []
    for key in order:
        for L in layers.values():
            if L.key == key:
                rows.append(_layer_row(page, L, L.layer_id in visible_ids))
    legend = h("ul", {"class": "dot-legend"},
               [h("li", None, seat_dots([k], v), v) for k, v in DOT_KINDS.items()])
    diagram = h("section", {"class": "layers-block", "id": "layers", "aria-labelledby": "layers-h"},
                h("h2", {"id": "layers-h", "class": "visually-hidden"}, "Governments and seats for the chosen place"),
                h("p", {"class": "picker-head mono layers-showing", "id": "layers-showing"},
                  "Showing: ", h("span", {"data-here-text": True}, "the governments everyone in the county has (no place picked yet)")),
                h("div", {"class": "layers", "id": "layer-list"}, rows),
                legend,
                h("p", {"class": "layers-foot"}, status_badge("computed", page),
                  " Counts computed from the guide's office, unit and board data. ",
                  h("a", {"href": page.rel("about/index.html#counting")}, "How we count")),
                h("p", {"class": "layers-more"},
                  h("a", {"href": page.rel(sitemap.YOUR_PLACE)}, "Your place"),
                  ": what each of these governments' offices decide, who holds the seats and how to reach them."),
                as_of_note(ed))

    # ---------------------------------------------------------------- next on your ballot
    years = sorted({y for L in layers.values() for y in L.next})
    dates = election_dates(ed, years)
    dpay = {y: {"primary": fmt_date(d["primary"]), "general": fmt_date(d["general"])} for y, d in dates.items()}
    nxt = {}
    for L in vis:
        for y, labels in L.next.items():
            nxt.setdefault(y, [])
            nxt[y] += [f"{lab} ({L.title})" for lab in labels]
    ny = min(nxt) if nxt else None
    rule_p, rule_g = ed.rules.get("primary_date", {}), ed.rules.get("general_election_date", {})
    strip = h("section", {"class": "next-strip", "id": "next-ballot", "aria-labelledby": "next-h"},
              h("h2", {"id": "next-h", "class": "next-h mono"}, "Next on your ballot"),
              h("p", {"class": "next-body"},
                h("strong", {"id": "next-year", "class": "fig"}, ny or "Not in data"), " ",
                h("span", {"id": "next-dates"}, f"Primary {dpay[ny]['primary']} · General {dpay[ny]['general']}" if ny else ""),
                page.cites.cite((rule_p.get("source_ids", "") + ";" + rule_g.get("source_ids", ""))),
                " ", status_badge("computed", page, "Dates computed from the state calendar rule (first Tuesday after the first Monday).")),
              h("p", {"class": "next-offices", "id": "next-offices"}, "; ".join(nxt.get(ny, [])) if ny else ""),
              h("p", {"class": "next-link"}, h("a", {"href": page.rel("elections/calendar/index.html")}, "Full election calendar")))

    # ---------------------------------------------------------------- paths
    def card(p, idx, small=False):
        first = p["stops"][0]
        href = page.rel(first["page"]) + f"#path-{p['id']}-1"
        return h("li", {"class": "path-card" + (" path-card-small" if small else "")},
                 h("a", {"href": href, "class": "path-link"},
                   h("span", {"class": "path-num mono"}, f"{idx:02d}"),
                   h("span", {"class": "path-title"}, p["title"]),
                   h("span", {"class": "path-blurb"}, p["blurb"]),
                   h("span", {"class": "path-meta mono"}, f"{len(p['stops'])} stops · about {p['minutes']} min")))
    prim_paths = [p for p in sitemap.PATHS if p["primary"]]
    sec_paths = [p for p in sitemap.PATHS if not p["primary"]]
    paths = h("section", {"class": "paths", "id": "paths", "aria-labelledby": "paths-h"},
              h("h2", {"id": "paths-h", "class": "section-h"}, "Where do you want to start?"),
              h("ol", {"class": "path-grid"}, [card(p, i + 1) for i, p in enumerate(prim_paths)]),
              h("ul", {"class": "path-grid path-grid-small"}, [card(p, len(prim_paths) + i + 1, True) for i, p in enumerate(sec_paths)]),
              h("p", {"class": "teach-link"}, "Teaching or leading a group? ",
                h("a", {"href": page.rel("teach/index.html")}, "Lesson kits")))

    # ---------------------------------------------------------------- context strip (no election data nearby)
    iv = [r for r in ed.table("indicator_values") if r["geo_type"] == "county" and r["geo_id"] == cfg["fips"]] or \
         [r for r in ed.table("indicator_values") if r["geo_type"] == "county"]
    def latest(ind, prefix):
        rows = [r for r in iv if r["indicator_id"] == ind and r["vintage"].startswith(prefix) and r["value"]]
        return max(rows, key=lambda r: r["vintage"]) if rows else None
    pop = latest("pop_total", "ACS")
    jobs = latest("qcew_jobs_all_ownerships", "QCEW")
    # Employers: the published lists disagree in date, method and coverage, and the only one with counts is
    # the oldest (2017, via Wikipedia). Naming three from any one of them would be a selection, so the strip
    # names none and links to the page that shows every list with its rule and date (neutrality review N8).
    emp_lists = {}
    for e in ed.table("employers"):
        emp_lists.setdefault(e["selection_rule"], e.get("as_of", "")[:4])
    bits = []
    if pop:
        bits.append(h("span", None, h("strong", {"class": "fig"}, fmt_int(pop["value"])), " people",
                      h("span", {"class": "muted"}, f" ({pop['vintage']})"), page.cites.cite(pop["source_ids"])))
    if jobs:
        bits.append(h("span", None, h("strong", {"class": "fig"}, fmt_int(jobs["value"])), " jobs",
                      h("span", {"class": "muted"}, f" ({jobs['vintage']})"), page.cites.cite(jobs["source_ids"])))
    if emp_lists:
        yrs = sorted(y for y in emp_lists.values() if y)
        span = f"{yrs[0]} to {yrs[-1]}" if yrs and yrs[0] != yrs[-1] else (yrs[0] if yrs else "")
        bits.append(h("span", None, "Largest employers: ",
                      h("a", {"href": page.rel("community/income-and-work/index.html#employers")},
                        f"{len(emp_lists)} published lists"),
                      h("span", {"class": "muted"}, f" ({span}), each with its source and rule")))
    context = h("section", {"class": "context-strip", "aria-labelledby": "ctx-h"},
                h("h2", {"id": "ctx-h", "class": "mono ctx-h"}, ed.county_label.upper()),
                h("p", None, join(bits, h("span", {"class": "sep", "aria-hidden": "true"}, " · "))),
                h("p", None, h("a", {"href": page.rel("community/index.html")}, "Know your community")))

    payload = {"places": places,
               "dates": dpay}
    page.add(hero, pick, diagram, strip, paths, context, json_script("layer-data", payload))
    page.finish()
    return page
