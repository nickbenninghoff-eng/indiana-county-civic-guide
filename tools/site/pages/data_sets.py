"""Data pages: one page per dataset (data/<slug>/index.html), "how to pull it yourself" (data/pull/index.html).

data/index.html (pages/meta.py build_data) is the short index. Every id the old single data page carried
(ds-<name>-preview, -csv, -copy, indicator-defs, pull-*, src-<id>) is listed by ``moved_anchor_map``;
the index ships that map and static/js/moved.js forwards an old link to the page that holds the id now.
Copy CSV works as before: static/js/meta.js copies the JSON-embedded CSV on each dataset page.
"""
from __future__ import annotations

import re

from civic.components import data_table, scope_badge, section, see_all_fold
from civic.data import fmt_int
from civic.html import h
from civic.sitemap import DATA_PAGES

from pages.meta import (DATASETS, PREVIEW_ROWS, URL_RE, _dataset_block, _fill, _hero, _publish_rows, _union,
                        dataset_slug)

SPEC_BY_SLUG = {dataset_slug(s): s for s in DATASETS}


def _pull_body(site, page) -> None:
    ed = site.ed
    cfg = ed.config
    c = page.cites
    # ------------------------------------------------------------------ pull it yourself
    n = 1
    res_arch = ed.source("RES-030") or {}
    gw = ed.source("MON-001") or {}
    filings = ed.source("SVC-019") or {}
    cf_page = ed.source("MON-020") or {}
    cf_contrib = ed.source("MON-021") or {}
    cf_exp = ed.source("MON-022") or {}

    def year_pattern(u: str) -> str:
        return re.sub(r"/(\d{4})_", "/{YEAR}_", u)

    def ext(url: str, label: str | None = None):
        return h("a", {"href": url, "target": "_blank", "rel": "noopener"}, label or url)

    inds = ed.table("indicators")
    by_id = {r["indicator_id"]: r for r in inds}
    pop = by_id.get("pop_total", {})
    laus = by_id.get("unemployment_rate", {})
    qcew = by_id.get("qcew_jobs_all_ownerships", {})
    acs_urls = [_fill(u.rstrip(";"), ed) for u in URL_RE.findall(pop.get("source_dataset", ""))]
    places = sorted({(r["geo_name"], r["geo_id"]) for r in ed.table("indicator_values") if r["geo_type"] == "place"})
    place_codes = [(name, gid.split("US", 1)[-1][len(cfg.get("state_fips", "")):]) for name, gid in places if "US" in gid]
    ind_rows = [[r["indicator_id"], r["label"], r["universe"], h("code", None, _fill(r["table_variable"], ed)), r["moe_rule"]]
                for r in inds]
    com_src = "COM-001;COM-002;COM-003;COM-004"

    def pull_fold(pid, title, hint, *children):
        """One source's steps in a fold (ships open; folds.js closes it and reopens it for a link to any id inside,
        including the pull-* heading id the old data page's links use)."""
        kids = children[0] if len(children) == 1 and isinstance(children[0], (list, tuple)) else children
        return h("details", {"class": "fold-details see-all pull-fold", "open": True, "data-fold": "pull"},
                 h("summary", {"class": "fold-summary see-all-summary"},
                   h("h3", {"id": pid}, title), h("span", {"class": "see-all-hint"}, hint),
                   h("span", {"class": "fold-toggle", "aria-hidden": "true"})),
                 h("div", {"class": "fold-body see-all-body"}, kids))

    pull = section("pull", n, "How to pull it yourself",
                   h("p", {"class": "lead"}, "The guide's figures come from public sources you can open yourself. Here is "
                                             "where each one lives and how it was pulled."),
                   pull_fold("pull-results", "County election results archive", "PDF reports, one per election",
                   h("p", None, "The county election board posts a PDF report for each election on one page: ",
                     ext(res_arch.get("url", "")), c.cite("RES-030"),
                     " Check each report's header: an election-night report says Unofficial; the final canvass says Official. "
                     "Reports from 2010 to 2019 and the 2024 general election are scanned images, so their text has to be "
                     "read by text recognition.", c.cite("RES-001;RES-027")) if res_arch.get("url") else None,
                   ),
                   pull_fold("pull-filings", "County candidate filings", "Scanned local filings",
                   h("p", None, "Local candidates' campaign-finance reports, large-contribution notices and candidacy "
                                "filings are posted as scanned documents on the county's Candidate Filings page: ",
                     ext(filings.get("url", "")), c.cite("SVC-019"),
                     " Each document opens as its own PDF; the guide's local campaign-finance rows cite each one by its "
                     "document number.") if filings.get("url") else
                   h("p", None, "The guide's source files do not include the address of the county's candidate-filings page "
                                "yet, so it is not listed here. It is recorded under Gaps below."),
                   ),
                   pull_fold("pull-gateway", "Indiana Gateway (budgets, tax rates, debt)", "Bulk download, county code filter",
                   h("p", None, "Budgets, tax rates and debt come from the bulk download page of Indiana Gateway: ",
                     ext(gw.get("url", "")), c.cite("MON-001;MON-002;MON-004")),
                   h("ol", None,
                     h("li", None, "Choose the data set (Budget Data for budgets and tax rates; Annual Financial Report "
                                   "for spending, receipts and debt)."),
                     h("li", None, f"Filter to county code {cfg.get('gateway_county_code', '')} ({ed.county_label})."),
                     h("li", None, "Remove repeated rows before adding anything up. The download the guide used repeated "
                                   "every row five times.", c.cite("MON-001"))),
                   ),
                   pull_fold("pull-cf", "State campaign finance (bulk files)", "Yearly contribution and expenditure files",
                   h("p", None, "The Indiana Election Division lists its bulk files here: ", ext(cf_page.get("url", "")),
                     c.cite("MON-020"), " Each year has a contribution file and an expenditure file at a fixed address:"),
                   h("pre", {"class": "code-block"},
                     h("code", None, year_pattern(cf_contrib.get("url", "")) + "\n" + year_pattern(cf_exp.get("url", "")))),
                   h("p", None, "Replace {YEAR} with a four-digit year. Files are grouped by the year a report was filed, "
                                "not by election cycle, and they have no district or cash-on-hand field.",
                     c.cite("MON-020;MON-021;MON-022")),
                   ),
                   pull_fold("pull-census", "Census and Bureau of Labor Statistics queries", "Query patterns with this county's codes",
                   h("p", None, f"These are the query patterns the guide used, with {ed.county_label}'s codes filled in "
                                f"(state {cfg.get('state_fips', '')}, county {cfg.get('county_fips', '')}). "
                                "The official Census API needs a free key; put it where the query says {KEY}.",
                     c.cite(com_src)),
                   h("p", None, h("strong", None, "Census, American Community Survey (5-year):")),
                   h("pre", {"class": "code-block"}, h("code", None, "\n".join(acs_urls))) if acs_urls else None,
                   h("p", None, "City codes (PLACE_FIPS) used by the guide: ",
                     "; ".join(f"{nm} = {code}" for nm, code in place_codes), ".") if place_codes else None,
                   h("p", None, h("strong", None, "BLS, local unemployment (LAUS):")),
                   h("pre", {"class": "code-block"}, h("code", None, _fill(laus.get("table_variable", ""), ed))) if laus else None,
                   h("p", None, h("strong", None, "BLS, jobs located in the county (QCEW):")),
                   h("pre", {"class": "code-block"}, h("code", None, _fill(qcew.get("table_variable", ""), ed))) if qcew else None,
                   ),
                   h("p", None, "Every indicator, with its table and variable codes:"),
                   see_all_fold("indicator-defs-all", len(inds), data_table(
                       "indicator-defs", ["Indicator", "Label", "Universe", "Table and variables", "Margin of error"],
                       ind_rows, caption=f"Indicator definitions ({len(inds)}), data/indiana/indicators.csv",
                       min_width="56rem"), noun="indicator", label=f"See all {len(inds)} indicator definitions"),
                   scope="indiana", ed=ed)
    page.add(pull)




def build_pull(site):
    page = site.page("data/pull/index.html")
    _hero(page, "Reference · Context · Data", "How to pull the data yourself",
          page.description, [scope_badge("indiana", site.ed)], [("pull", "How to pull it yourself"), ("sources", "Sources")])
    _pull_body(site, page)
    page.add(h("p", None, h("a", {"href": page.rel("data/index.html")}, "Back to all datasets")))
    page.finish()
    return page


def _dataset_builder(slug: str):
    spec = SPEC_BY_SLUG[slug]

    def build(site):
        ed = site.ed
        path = f"data/{slug}/index.html"
        page = site.page(path)
        key, anchor, title, scope, desc, pcols = spec
        _hero(page, "Reference · Context · Data", title, desc, [scope_badge(scope, ed)],
              [(anchor, "The table"), ("sources", "Sources")])
        page.add(h("p", {"class": "back-link"}, h("a", {"href": page.rel("data/index.html#tables")}, "All datasets")))
        page.add(_dataset_block(ed, page, None, spec))
        page.finish()
        return page

    build.__name__ = f"build_data_{slug.replace('-', '_')}"
    return build


def moved_anchor_map(ed) -> dict:
    """Where each id of the old one-page data viewer lives now. ``a``: id -> path from the data folder
    (``results/index.html``); ``src``: source entry id (without ``src-``) -> the page whose Sources list has it."""
    from civic.shell import Page

    a: dict[str, str] = {}
    src: dict[str, str] = {}
    for spec in DATASETS:
        slug = dataset_slug(spec)
        anchor = spec[1]
        for suffix in ("preview", "csv", "copy"):
            a[f"{anchor}-{suffix}"] = f"{slug}/index.html"
        _, rows, _ = _publish_rows(ed, spec[0])
        for sid in _union(rows):
            src.setdefault(sid, f"{slug}/index.html")
    for pid in ("pull-results", "pull-filings", "pull-gateway", "pull-cf", "pull-census", "indicator-defs",
                "indicator-defs-copy"):
        a[pid] = "pull/index.html"
    # the pull page's citations: build its body on a scratch page that is never registered
    scratch_site = type("S", (), {"ed": ed})()
    scratch = Page(scratch_site, "data/pull/index.html", "", "")
    _pull_body(scratch_site, scratch)
    for sid in scratch.cites.order:
        src.setdefault(sid, "pull/index.html")
    return {"a": a, "src": src}


PAGES = {"data/pull/index.html": build_pull}
for _slug in SPEC_BY_SLUG:
    PAGES[f"data/{_slug}/index.html"] = _dataset_builder(_slug)
