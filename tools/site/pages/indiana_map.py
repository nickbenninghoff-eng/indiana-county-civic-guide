"""'Not your county?' page: Indiana's 92 counties, built editions linked."""
from __future__ import annotations

import json

from civic.components import scope_badge
from civic.glyph import county_map
from civic.html import h


def built_editions(ed) -> dict:
    """fips -> edition id for every data/editions/<id>/edition.json."""
    out = {}
    for p in sorted((ed.root / "data" / "editions").glob("*/edition.json")):
        try:
            cfg = json.loads(p.read_text(encoding="utf-8"))
            out[cfg["fips"]] = p.parent.name
        except (OSError, ValueError, KeyError):
            ed.warnings.append(f"could not read {p}")
    return out


def build(site):
    ed = site.ed
    page = site.page("indiana/index.html")
    editions = built_editions(ed)

    def href_for(c):
        eid = editions.get(c["fips"])
        if eid is None:
            return None
        if eid == ed.edition_id:
            return page.rel("index.html")
        return None  # other editions publish separately; link added when they exist in this artifact

    indiana_pages = [e for e in site.entries if e.scope == "indiana" and e.path != page.path]
    names = sorted(ed.counties_svg["counties"], key=lambda c: c["name"])
    items = []
    for c in names:
        built = c["fips"] in editions
        label = f"{c['name']} County"
        if built and editions[c["fips"]] == ed.edition_id:
            items.append(h("li", {"class": "county-built"}, h("a", {"href": page.rel("index.html")}, label),
                           h("span", {"class": "mono county-status"}, "Edition built")))
        else:
            items.append(h("li", None, label, h("span", {"class": "mono county-status"}, "Edition not built yet")))
    page.add(
        h("header", {"class": "page-hero"},
          h("p", {"class": "eyebrow mono"}, "Indiana County Civic Guide · Series"),
          h("h1", None, "Indiana's 92 counties"),
          h("p", {"class": "dek"}, f"The guide is built one county edition at a time. {len(editions)} of "
                                   f"{len(names)} county editions {'is' if len(editions) == 1 else 'are'} built so far. For every other county the edition is "
                                   "not built yet, but the Indiana-wide chapters still apply."),
          h("p", None, scope_badge("indiana", ed))),
        h("section", {"class": "block map-block", "aria-labelledby": "map-h"},
          h("h2", {"id": "map-h", "class": "visually-hidden"}, "Map"),
          h("div", {"class": "map-layout"},
            h("div", {"class": "map-wrap"}, county_map(ed, href_for)),
            h("div", {"class": "map-side"},
              h("h2", None, "Chapters that apply in every county"),
              h("ul", {"class": "link-list"}, [h("li", None, h("a", {"href": page.rel(e.path)}, e.title)) for e in indiana_pages]),
              h("p", {"class": "muted"}, "Hover or tab to a county on the map for its status. The full list is below.")))),
        h("section", {"class": "block", "id": "all-counties", "aria-labelledby": "all-h"},
          h("h2", {"id": "all-h"}, "All counties"),
          h("ul", {"class": "county-list"}, items)))
    page.finish()
    return page
