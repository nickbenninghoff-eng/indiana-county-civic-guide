"""Map: who governs where (map/index.html). Boundary data comes from derived/map_shapes.json
(tools/build_map.py, Census TIGERweb). The component lives in civic/map.py. The "How areas voted" race data is
written next to the page's assets as assets/map-votes.json (civic/map.py VOTES_ASSET) and loaded by
static/js/map_votes.js, so the page itself stays small."""
from __future__ import annotations

import json

from civic.components import scope_badge, section
from civic.html import h
from civic.map import VOTES_ASSET, area_lists, boundary_map, load_shapes, load_votes, vote_tables, votes_asset

SRC = ["MAP-001", "MAP-002", "MAP-003", "MAP-004"]
VOTE_SRC = ["MAP-005", "MAP-006", "MAP-007", "MAP-009", "MAP-008"]


def write_votes_asset(site, payload) -> int:
    dest = site.out / VOTES_ASSET
    dest.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    dest.write_text(text, encoding="utf-8", newline="\n")
    return dest.stat().st_size


def build(site):
    ed = site.ed
    page = site.page("map/index.html", banners=False)
    c = page.cites
    shapes = load_shapes(ed)
    if shapes is None:
        page.add(h("header", {"class": "page-hero"}, h("h1", None, page.title),
                   h("p", {"class": "dek"}, "The boundary data for this map has not been built yet.")))
        page.finish(gaps=[{"item": "Boundary shapes", "why_missing": "derived/map_shapes.json is missing.",
                           "how_to_fill": "Run tools/build_map.py."}])
        return page
    votes = load_votes(ed) if "precinct" in shapes.get("layers", {}) else None
    if votes:
        write_votes_asset(site, votes_asset(votes, ed))
    vintage = shapes["vintage"].split(",", 1)[-1].strip()
    page.add(
        h("header", {"class": "page-hero"},
          h("p", {"class": "eyebrow mono"}, "Reference · Map"),
          h("h1", None, page.title),
          h("p", {"class": "dek"}, "Pick a layer, then point at an area to see which government it is and what the guide knows about it. "
                                   "Every area is a link to that government's page.", c.cite_compact(SRC)),
          h("p", {"class": "hero-badges"}, scope_badge("county", ed))),
        h("section", {"class": "block", "id": "map", "aria-labelledby": "map-h"},
          h("header", {"class": "block-head"}, h("h2", {"id": "map-h"}, "Boundary map")),
          boundary_map(page, ed, shapes, votes=votes),
          h("p", {"class": "muted cmap-caveat"},
            f"Boundaries are Census TIGER ({vintage}) and may differ slightly from county GIS. The guide does not place addresses: "
            "to find which governments cover yours, use ", h("a", {"href": page.rel("your-governments/index.html")}, "Find your governments"),
            ". In the government layers, color shows the type of government only. In the \"How areas voted\" layer, color shows the margin "
            "between the two leading parties in one past race.", c.cite_compact(SRC + (VOTE_SRC if votes else [])))),
        section("areas", 1, "All areas as a list",
                h("p", {"class": "lead"}, "The same areas as the map, with the same links. Each table works without the map."),
                area_lists(page, ed, shapes), vote_tables(page, ed, shapes, votes) if votes else None, scope="county", ed=ed))
    gaps = [
        {"item": "Unincorporated area is shown as the township background, not as its own government.",
         "why_missing": "Unincorporated land has no government of its own; the township and the county serve it.",
         "how_to_fill": ""},
        {"item": "Census designated places (for example Granger and Notre Dame) are not drawn.",
         "why_missing": "They are statistical areas without a government, so the guide has no page for them.",
         "how_to_fill": ""},
    ]
    if votes:
        gaps += [
            {"item": "Precinct boundaries are the Census 2020 voting districts. Precincts created or renumbered after 2020 have results but no shape.",
             "why_missing": "No post-2020 St. Joseph precinct boundary file was found. Such precincts are left out of every area total and map color, and are listed under the tables.",
             "how_to_fill": "Obtain the county's current precinct boundaries from the county GIS office."},
            {"item": "Town totals are approximate: each town is the sum of precincts with at least half their area inside the town.",
             "why_missing": "Precincts are not cut at town lines in the data, so votes cannot be split between a town and the land around it.",
             "how_to_fill": "Ward-level or address-level results from the county would allow exact town totals."},
            {"item": "District races (State Senate, State House, county commissioner, county council) and township and town races count a "
                     "township, city or town only through its precincts inside the district, township or town.",
             "why_missing": "An area split between districts is shown with the precincts on the selected district's ballot; the panel "
                            "says how many of its precincts that is. State legislative districts also extend past the county line, and "
                            "the guide has only the St. Joseph County part of their results.",
             "how_to_fill": ""},
            {"item": "Judicial retention votes, public questions and school board races are not mapped.",
             "why_missing": "Retention votes and public questions are yes-or-no questions with no candidates; school board races are "
                            "nonpartisan, so the map's rule (partisan races) leaves them out.",
             "how_to_fill": ""},
            {"item": "Township and town races are mapped for 2022 only, and city races not at all.",
             "why_missing": "Of the three ballots with precinct results, only 2022 had township and town offices; South Bend and "
                            "Mishawaka elect their officers in odd years (2023 most recently), for which the guide has no precinct results.",
             "how_to_fill": "Add the county's 2023 municipal precinct report and a reader for it in tools/build_precinct_results.py."},
            {"item": "Walkerton's two council wards cannot be drawn on the map.",
             "why_missing": "Both Walkerton precincts include voters from both wards, and precincts are not split at ward lines, so each "
                            "ward race shows the whole town, counting only that ward's voters.",
             "how_to_fill": "A Walkerton ward boundary file and ward-level results would allow it."},
            {"item": "Years before 2020 are not mapped.",
             "why_missing": "The guide has precinct results only for the 2020, 2022 and 2024 general elections.",
             "how_to_fill": "Add older precinct files (OpenElections or the county's precinct reports); the rule then adds their races automatically."},
        ]
        unchecked = [r for r in votes["races"] if not r.get("county_checked")]
        if unchecked:
            gaps.append({"item": "County totals not checked against an official county figure: " +
                                 "; ".join(r["label"] + (f" ({r['check_note']})" if r.get("check_note") else "") for r in unchecked) + ".",
                         "why_missing": "The guide has no official county figure for these races to compare with. These totals are "
                                        "sums of the precinct results. Every other mapped race's precinct sums match the official "
                                        "county canvass exactly.",
                         "how_to_fill": "Add the official county figure to results.csv and re-run tools/build_precinct_results.py."})
    for uid in shapes.get("units_without_shape", []):
        u = ed.units[uid]
        if u["unit_type"] == "school_corporation":
            gaps.append({"item": f"{u['name']} is not on the map.",
                         "why_missing": "No Census unified school district matched this name in the county. Its relationship to Union-North is not documented in the guide's data.",
                         "how_to_fill": "Confirm the corporation's boundary with the corporation or the county GIS office."})
    for line in shapes.get("unmatched", []):
        gaps.append({"item": f"Unmatched Census feature: {line}", "why_missing": "No unit in the guide has this name.",
                     "how_to_fill": "Add a unit or a name mapping."})
    page.finish(gaps=gaps)
    return page


PAGES = {"map/index.html": build}
