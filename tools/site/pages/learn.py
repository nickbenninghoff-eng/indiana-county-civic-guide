"""The Learn hub (phase 6, 2026-11-18): learn/index.html, the page the header's "Learn" item opens.

One short page: the guides as cards (a title link and the guide's own sitemap description, nothing new), then the learning
paths in order, then the lesson kits. It organizes and links; it states no facts of its own, so it carries no citations.
A guide whose page is not in the sitemap is left out (nothing links to a page that is not built).

Not here: a "school board rules" guide. The governments step (planning/qa/phase6-governments-2026-11-16.md) split schools/
into one page per corporation and did not write that guide; its closest existing pages are the "Run for school board" page
(linked under the Run for office card) and each school corporation's page under Governments.
Learning paths: sitemap.PATHS; the hub links each path's first stop (``<page>#path-<id>-1``, which opens the path bar).
"""
from __future__ import annotations

from civic.html import h

HUB = "learn/index.html"

# (group heading or "" for none, [(path, card title)]). One group today, so the cards flow in one grid; a card whose page
# is not built is dropped.
GUIDES = [
    ("", [("elections/how-it-works/index.html", "How elections work"),
          ("money/what-is-a-budget/index.html", "What counts as a budget"),
          ("money/campaigns/how-it-works/index.html", "How campaign money works"),
          ("who-handles-this/index.html", "Who handles this?"),
          ("run/index.html", "Run for office"),
          ("state/how-the-state-shapes-local/index.html", "How the state shapes local government"),
          ("history/index.html", "History and turning points"),
          ("people/notable/index.html", "People in local history"),
          ("community/index.html", "Community profile"),
          ("teach/index.html", "Lesson kits for teachers")]),
]


def _card(page, site, path, title):
    e = site.by_path[path]
    extra = None
    if path == "run/index.html":
        # the office pages under run/ (one link each), the same labels the Run for office page uses
        subs = [x for x in site.entries if x.path.startswith("run/") and x.path != path and not x.moved_to]
        extra = h("p", {"class": "learn-sub"}, "By office: ",
                  [[h("a", {"href": page.rel(x.path)}, x.nav.lower()), ", " if i < len(subs) - 1 else ""]
                   for i, x in enumerate(subs)]) if subs else None
    return h("article", {"class": "card learn-card", "id": "g-" + path.removesuffix("/index.html").replace("/", "-")},
             h("h3", {"class": "card-title"}, h("a", {"href": page.rel(path)}, title)),
             h("p", {"class": "learn-desc"}, e.description), extra)


def _path_rows(page, site):
    from civic import sitemap
    rows = []
    for p in sitemap.PATHS:
        first = p["stops"][0]
        rows.append(h("li", {"class": "learn-path", "id": f"lp-{p['id']}"},
                      h("a", {"class": "learn-path-title", "href": page.rel(first["page"]) + f"#path-{p['id']}-1"}, p["title"]),
                      h("span", {"class": "learn-path-meta mono"}, f"{len(p['stops'])} stops · about {p['minutes']} min"),
                      h("span", {"class": "learn-path-blurb"}, p["blurb"])))
    return rows


def build(site):
    page = site.page(HUB, banners=False, body_class="learn-page")
    page.add(h("header", {"class": "thing-head hub-head"},
               page.crumb_nav(),
               h("h1", {"class": "thing-title"}, "Learn"),
               h("p", {"class": "thing-facts"},
                 "The guides that explain how local government, elections and money work, then the learning paths that "
                 "put them in order.")))
    groups = []
    for heading, items in GUIDES:
        cards = [_card(page, site, p, t) for p, t in items if p in site.by_path and not site.by_path[p].moved_to]
        if cards:
            groups.append(h("div", {"class": "learn-group"}, h("h3", {"class": "learn-group-h"}, heading) if heading else None,
                            h("div", {"class": "card-grid learn-grid"}, cards)))
    page.add(h("section", {"class": "block learn-sec", "id": "guides", "aria-labelledby": "guides-h"},
               h("header", {"class": "block-head"}, h("h2", {"id": "guides-h"}, "Guides")), groups))
    page.add(h("section", {"class": "block learn-sec", "id": "paths", "aria-labelledby": "paths-h"},
               h("header", {"class": "block-head"}, h("h2", {"id": "paths-h"}, "Learning paths")),
               h("p", {"class": "learn-paths-lead"},
                 "Each path is a short list of stops through the guide, in a teaching order. A bar at the top of the page "
                 "shows where you are and offers Next and Previous."),
               h("ol", {"class": "learn-paths"}, _path_rows(page, site))))
    page.finish()
    return page


PAGES = {HUB: build}
