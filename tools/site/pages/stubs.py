"""Stub pages: every sitemap entry without a real builder gets one, so links never 404
and the next agents have a file (and the path-stop anchors) to fill."""
from __future__ import annotations

from civic.components import STATUS, scope_badge, status_badge
from civic.html import h
from civic.layers import COUNTING_RULES


def build_stub(site, entry):
    ed = site.ed
    page = site.page(entry.path)
    scope = {"indiana": [scope_badge("indiana", ed)], "county": [scope_badge("county", ed)],
             "mixed": [scope_badge("indiana", ed), " ", scope_badge("county", ed)]}.get(entry.scope, [])
    page.add(h("header", {"class": "page-hero"},
               h("p", {"class": "eyebrow mono"}, "Reference" if entry.group else "Guide"),
               h("h1", None, entry.title),
               h("p", {"class": "dek"}, entry.description),
               h("p", None, scope)),
             h("div", {"class": "callout callout-note stub-note", "role": "note"},
               h("p", None, h("strong", None, "This page is being built. "),
                 "It will contain: ", entry.description[0].lower() + entry.description[1:])))
    for anchor, title in entry.sections:
        body = [h("p", {"class": "muted"}, "Coming in a later build.")]
        if entry.path == "about/index.html" and anchor == "badges":
            body = [h("dl", {"class": "badge-defs"},
                      [[h("dt", None, status_badge(k)), h("dd", None, v[1])] for k, v in STATUS.items()] +
                      [[h("dt", None, scope_badge(s, ed)), h("dd", None, t)] for s, t in (
                          ("indiana", "Applies to every Indiana county."),
                          ("county", f"Data or rules specific to {ed.county_label}."),
                          ("exception", f"Where state law treats {ed.county_label} differently from most counties."))])]
        if entry.path == "about/index.html" and anchor == "counting":
            body = [h("p", None, "How the landing page's layer diagram counts seats:"),
                    h("ul", None, [h("li", None, r) for r in COUNTING_RULES])]
        page.add(h("section", {"class": "block", "id": anchor, "aria-labelledby": f"{anchor}-h"},
                   h("header", {"class": "block-head"}, h("h2", {"id": f"{anchor}-h"}, title)), body))
    page.finish()
    return page
