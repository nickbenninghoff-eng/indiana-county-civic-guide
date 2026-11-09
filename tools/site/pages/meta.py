"""Meta pages: about/index.html (methods, neutrality, badges, author, corrections, changelog,
sources index), data/index.html (every dataset with full-CSV copy, how to pull it yourself)
and teach/index.html (lesson kit + path outlines).

Registered through PAGES (parallel-safe). Styles: static/css/meta.css. Script: static/js/meta.js
(copies a full dataset's CSV from an embedded JSON string; the preview table shows only 50 rows).
"""
from __future__ import annotations

import csv
import io
import re
from collections import Counter

from civic import sitemap
from civic.components import STATUS, callout, data_table, gaps_section, scope_badge, section, status_badge
from civic.data import fmt_date, fmt_int, split_ids
from civic.html import Markup, h, json_script, join
from civic.layers import COUNTING_RULES
from civic.neutrality import BANNED_TERMS
from civic.shell import about_looks_section

PREVIEW_ROWS = 50

# ============================================================================ shared helpers


def _people_criteria():
    """The people-selection rules, read from the people page's module so About prints the exact same text.
    Imported lazily: a broken sibling module must fail this page loudly at build time, not at import."""
    from pages.community_history import CRITERIA
    return CRITERIA


def _hero(page, eyebrow: str, h1: str, dek, scopes: list, toc: list[tuple[str, str]]):
    page.add(h("header", {"class": "page-hero"},
               h("p", {"class": "eyebrow mono"}, eyebrow),
               h("h1", None, h1),
               h("p", {"class": "dek"}, dek),
               h("p", {"class": "hero-badges"}, [[s, " "] for s in scopes]) if scopes else None,
               h("nav", {"class": "toc", "aria-label": "On this page"},
                 h("ol", None, [h("li", None, h("a", {"href": f"#{a}"}, t)) for a, t in toc]))))


CFL_TAB = re.compile(r'County tab "([^"]+)"')


def _source_item(ed, sid: str, number: int | None = None, aliases: list[str] | None = None) -> Markup:
    """One source entry, same fields as the shared per-page Sources list (title verbatim).

    aliases: other source IDs for the same document (same web address); each gets its own anchor
    inside this entry so citations to it still land here."""
    s = ed.sources.get(sid)
    if not s:
        return h("li", {"id": f"src-{sid}"}, h("span", {"class": "mono"}, sid),
                 " Source ID not found in the guide's source files.")
    title = s.get("title") or s.get("url") or sid
    t = h("cite", {"data-verbatim": "source-title"}, title)
    url = s.get("url", "")
    if url.startswith("http"):
        first = url.split(" ; ")[0].strip()
        link = h("a", {"href": first, "target": "_blank", "rel": "noopener"}, t)
    else:
        link = h("span", None, t, h("span", {"class": "muted"},
                                    f" (project file {url}, not published)" if url else " (no web address recorded)"))
    # county campaign-finance scans are titled with the filer's name only; say which posting each one is
    tab = CFL_TAB.search(s.get("notes", "")) if sid.startswith("CFL-") else None
    which = h("span", {"class": "muted"}, f" ({tab.group(1)}, county document {sid[4:]})") if tab else None
    meta = [x for x in (s.get("publisher"), f"accessed {fmt_date(s['accessed'])}" if s.get("accessed") else "") if x]
    also = None
    if aliases:
        also = h("span", {"class": "src-id mono"}, "Same document, also cited as ",
                 join([h("span", {"id": f"src-{a}"}, a) for a in aliases], ", "))
    return h("li", {"id": f"src-{sid}", "value": number},
             link, which, h("span", {"class": "src-meta"}, " · ".join(meta)),
             h("span", {"class": "src-id mono"}, f"{sid} · {s.get('kind', '')} · {s.get('_file', '')}.csv"), also)


def _union(rows, field: str = "source_ids") -> list[str]:
    seen: dict[str, None] = {}
    for r in rows:
        for s in split_ids(r.get(field)):
            seen.setdefault(s, None)
    return list(seen)


def _rule(ed, key: str) -> dict:
    return ed.rules.get(key, {})


def _rule_line(ed, page, key: str):
    """A rule's plain-language sentence with its citation and status badge (low confidence skipped)."""
    r = _rule(ed, key)
    if not r or not r.get("plain_language") or r.get("confidence") == "low":
        return None
    return h("li", None, r["plain_language"], page.cites.cite(r.get("source_ids")), " ",
             status_badge(r.get("status"), page))


def _status_mix(rows, page) -> Markup:
    c = Counter((r.get("status") or "").strip().lower() for r in rows)
    order = [k for k in STATUS if k in c] + sorted(k for k in c if k not in STATUS)
    items = [h("li", None, status_badge(k, page), h("span", {"class": "mix-n mono"}, fmt_int(c[k]))) for k in order]
    low = sum(1 for r in rows if r.get("confidence") == "low")
    if low:
        items.append(h("li", None, status_badge("low", page), h("span", {"class": "mix-n mono"}, fmt_int(low))))
    return h("ul", {"class": "status-mix", "aria-label": "Rows by status"}, items)


# ============================================================================ about


VERDICT_RE = re.compile(r"findings table, (\d+) rows.*?CONFIRMED (\d+) · CORRECTED (\d+) · CONTRADICTED (\d+) · "
                        r"CONFLICT-RESOLVED (\d+) · UNVERIFIABLE (\d+) · REMOVE (\d+)")
SPOT_RE = re.compile(r"(\d+) result rows were read straight from the county PDFs.*?\*\*Every one of the (\d+) matched", re.S)

# One entry per _corrections_applied file: what kind of correction it holds, written without
# names or private details. Counts are read from the file itself.
CORRECTION_FILES = [
    ("data/indiana/_corrections_applied_indiana.md", "Indiana-wide rules", "IND-027",
     "State election, legislative and tax rules were checked against statute and constitution text. "
     "Wrong thresholds, section numbers and effective dates were corrected; seat counts that could not be "
     "verified were left blank instead of guessed; claims with no source were dropped."),
    ("data/editions/st-joseph/_corrections_applied_results.md", "Election results", "RES-041",
     "Where a news report, Wikipedia or an election-night count differed from the county's official canvass, "
     "the canvass figure was used. A duplicate copy of one election was entered once, a rescheduled primary got "
     "its real date, ballot labels were corrected, and county tallies of multi-county races are not presented as "
     "district-wide results."),
    ("data/editions/st-joseph/_corrections_applied_gov.md", "Government structure and officeholders", "GOV-015",
     "Officeholder dates, districts and party labels were corrected against the canvasses; the county council's "
     "district structure and the term-limit list were corrected; characterizations that came from one outlet are "
     "not stated as fact."),
    ("data/editions/st-joseph/_corrections_applied_money.md", "Budgets, taxes and state campaign finance", "MON-023",
     "News characterizations are kept separate from documented state figures; a reporting change is shown as a "
     "series break instead of a budget cut; a download that repeated every row five times was de-duplicated; "
     "state campaign-finance totals were recomputed from the bulk files."),
    ("data/editions/st-joseph/_corrections_applied_community_people.md", "Community, people and timeline", "COM-030",
     "Items the fact-check marked for removal were left out entirely. Amounts and vote margins were corrected to "
     "official figures; claims that could not be verified were marked single-source or low confidence, or dropped; "
     "news-reported matters that are not official findings are not shown as findings."),
]

KIND_GROUPS = [
    ("primary", "Primary records", "Government documents: canvasses, filings, official pages."),
    ("statute", "Statutes and constitution", "Indiana Code and constitution text."),
    ("dataset", "Datasets", "Bulk data from government agencies."),
    ("news", "News reports", "Reporting by news outlets, attributed where used."),
    ("secondary", "Secondary references", "Encyclopedias and reference sites, used where no primary record was found."),
    ("derived", "Project files", "The guide's own research notes and fact-check, kept in the project and not published."),
]

# Sources whose own notes say they back only research notes the guide does not publish
# (for example a news-reported matter that is not an official finding).
UNPUBLISHED_NOTE = re.compile(r"^Used only in notes", re.I)


def _unpublished_sources(ed) -> set[str]:
    return {sid for sid, s in ed.sources.items() if UNPUBLISHED_NOTE.search(s.get("notes", ""))}


def _cf_local_gap(ed) -> dict:
    """Shown only while cf_local.csv is absent."""
    return {"item": "Local campaign-finance figures",
            "why_missing": "Scanned county reports are still in the double-entry check.",
            "how_to_fill": "Publish once the check and merge are complete."}


def _count_findings(text: str) -> int:
    """Rows in the findings table(s) under the 'findings applied' heading of a corrections file."""
    n, on = 0, False
    for line in text.splitlines():
        if line.startswith("## "):
            on = "finding" in line.lower() or "timeline" in line.lower() or "people" in line.lower()
            continue
        if on and line.startswith("|") and not re.match(r"^\|\s*-", line):
            n += 1
    # subtract one header row per table
    tables = len(re.findall(r"\n\|[^\n]*\|\n\|\s*-", "\n" + text))
    return max(0, n - tables)


def build_about(site):
    ed = site.ed
    cfg = ed.config
    page = site.page("about/index.html")
    c = page.cites
    toc = [("author", "Who made this"), ("methods", "How it was made"), ("neutrality", "Neutrality policy"),
           ("badges", "Badges"), ("counting", "Seat counting"), ("corrections", "Corrections"),
           ("changelog", "Changelog"), ("looks", "Choose a look"), ("gaps", "Gaps"), ("sources", "Sources index")]
    _hero(page, "About", "About and methods",
          "Who made this guide, how it was made, the rules it follows to stay neutral, what the badges mean, "
          "and every source it uses.",
          [scope_badge("indiana", ed), scope_badge("county", ed)], toc)

    # ------------------------------------------------------------------ author
    disclosure = cfg.get("author_disclosure", "")
    pending = not disclosure or disclosure.strip().startswith("[")
    if pending:
        disc = h("aside", {"class": "disclosure disclosure-pending", "id": "disclosure", "aria-label": "Author disclosure"},
                 h("p", {"class": "disclosure-label mono"}, "Disclosure: to be written by the author"),
                 h("p", None, "Before this guide is published, the author will state here any ties to a political party, "
                              "campaign or advocacy group, or that there are none."),
                 h("p", {"class": "muted"}, "Until then, this placeholder stays visible on purpose."))
    else:
        disc = h("aside", {"class": "disclosure", "id": "disclosure", "aria-label": "Author disclosure"},
                 h("p", {"class": "disclosure-label mono"}, "Disclosure"),
                 h("p", None, h("q", None, disclosure), f" — {cfg.get('author', '')}"),
                 h("p", {"class": "muted"},
                   "What the guide does about it: who appears on the people page, and in what order lists appear, "
                   "is decided by written rules applied the same way to every party, and party colors appear only on "
                   "party data. Before publishing, AI review agents were told to read every page as a skeptical "
                   "Republican and as a skeptical Democrat; what they found and what changed is summarized under ",
                   h("a", {"href": "#neutrality-checked"}, "How neutrality was checked"), ". See the ",
                   h("a", {"href": "#neutrality"}, "neutrality policy"), "."))
    page.add(section("author", 1, "Who made this",
                     h("p", None, h("strong", None, cfg.get("author", "")), f" made this guide. It is the {cfg['edition']} "
                                  f"of the {cfg['series']}: a guide to local and state government built from public records, "
                                  "one county at a time."),
                     disc,
                     h("h3", None, "Why it exists"),
                     h("p", None, "To put one county's governments in one place: how they are organized, who holds each "
                                  "office, how past elections came out and where the money goes, with a source behind every "
                                  "figure, written so a high-school student can follow it."),
                     h("ul", None,
                       h("li", None, "No ads, no endorsements, no donations tied to issues, no candidate scorecards."),
                       h("li", None, "It does not tell anyone how to vote."),
                       h("li", None, "What the guide looked for and could not find is listed openly at the end of each page.")),
                     scope="county", ed=ed))

    # ------------------------------------------------------------------ methods
    fc_path = ed.root / "planning" / "fact-check-report.md"
    fc_text = fc_path.read_text(encoding="utf-8") if fc_path.is_file() else ""
    vm = VERDICT_RE.search(fc_text)
    sm = SPOT_RE.search(fc_text)
    fc_line = None
    if vm:
        total, conf, corr, contra, conflict, unver, remove = vm.groups()
        fc_line = h("p", None,
                    f"The fact-check reviewed {total} claims from the research files. It confirmed {conf}, corrected {corr}, "
                    f"found {contra} contradicted by a primary source, settled {conflict} conflicts between sources, could not "
                    f"settle {unver}, and marked {remove} for removal. Every correction was applied to the data before any page "
                    "was built, and the removed items appear nowhere in the guide.", c.cite("RES-041"), " ",
                    status_badge("computed", page, "Counts taken from the fact-check report's summary."))
    spot = None
    if sm and sm.group(1) == sm.group(2):
        spot = h("p", None, f"As a spot check, the fact-check read {sm.group(1)} result rows directly from the county's "
                            "election PDFs. All of them matched the guide's transcriptions.", c.cite("RES-041"))
    page.add(section("methods", 2, "How it was made",
                     h("p", {"class": "lead"}, "AI tools did much of the research and transcription, under the author's "
                                               "direction. That is why every figure links to its source: you can check any "
                                               "of it yourself."),
                     h("h3", None, "1. Research by AI agents, directed by a person"),
                     h("p", None, "AI research agents (Claude models made by Anthropic) gathered the records: county election "
                                  "reports, state law, budget filings, census tables and news coverage. The author chose the "
                                  "topics, set the rules in this page and reviewed the results. Each data row records its "
                                  "sources and a status badge saying how solid it is."),
                     h("h3", None, "2. Official county records first"),
                     h("p", None, "Election results come from the county election board's official canvass reports wherever "
                                  "they exist.", c.cite("RES-030"), " Older reports (2010 to 2019) and the 2024 general "
                                  "election report are scanned images, so they were read with text recognition; rows that were "
                                  "hard to read are marked FROM SCAN.", c.cite("RES-001;RES-027"),
                       " News reports, Wikipedia and Ballotpedia fill in only where no county record was found, and those rows "
                       "are marked SECONDARY."),
                     h("p", None, "Budgets and tax rates come from Indiana Gateway, the state's local-government finance "
                                  "database.", c.cite("MON-001"), " State legislators' campaign money comes from the state's "
                                  "campaign-finance bulk files.", c.cite("MON-020"), " Community figures come from the Census "
                                  "Bureau and the Bureau of Labor Statistics.", c.cite("COM-001;COM-003;COM-004")),
                     h("h3", None, "3. An adversarial fact-check"),
                     h("p", None, "A separate AI agent was told to try to prove the research wrong. It checked claims against "
                                  "the county's election PDFs, statute text and news reports, and compared the research files "
                                  "with each other.", c.cite("RES-041")),
                     fc_line, spot,
                     h("h3", None, "4. Blind double entry for scanned campaign-finance forms"),
                     h("p", None, "Local candidates file campaign-finance reports on paper, and the county posts them as scans. "
                                  "Each summary sheet was transcribed once and checked against the form's own arithmetic "
                                  "(subtotals, and opening cash plus receipts minus expenditures equals closing cash). A sample "
                                  "of the forms was transcribed again by a different agent that could not see the first answer. "
                                  "The two versions were compared cell by cell, and every disagreement was settled by a third "
                                  "reviewer looking at the page image. Forms outside the sample rest on one reading plus the "
                                  "arithmetic check, and a random spot check of them against their images. The Campaign "
                                  "finance page gives the counts and marks every filing with its check status. ",
                       h("a", {"href": page.rel("money/campaigns/index.html#method")}, "Campaign finance")),
                     h("h3", None, "5. What the guide leaves out"),
                     h("ul", None,
                       h("li", None, "Private people's addresses, phone numbers and e-mail addresses."),
                       h("li", None, "Voter-file data (who is registered or voted) and donor contact details. Precinct results are "
                                     "shown on the map because they are public election records."),
                       h("li", None, "Forecasts, predictions and advice to campaigns."),
                       h("li", None, "Anything the fact-check marked for removal, and any claim it found wrong that could not "
                                     "be corrected from a source.")),
                     h("p", None, "Every page ends with a list of its sources and a list of gaps: things the guide looked for "
                                  "and has not found or confirmed yet. ",
                       h("a", {"href": page.rel("data/index.html")}, "All the data, with copyable CSV")),
                     ed=ed))

    # ------------------------------------------------------------------ neutrality
    also_avoided = ["safe", "toss-up", "pickup", "flippable", "blue wave", "red wave", "targeted",
                    "anchor (for employers)", "engine", "struggling", "base (for voters)", "voting bloc"]
    swatches = h("ul", {"class": "swatch-list"},
                 h("li", None, h("span", {"class": "swatch m-party-D", "aria-hidden": "true"}), "Democrat (D)"),
                 h("li", None, h("span", {"class": "swatch m-party-R", "aria-hidden": "true"}), "Republican (R)"),
                 h("li", None, h("span", {"class": "swatch m-party-other", "aria-hidden": "true"}),
                   "Every other party, independent and nonpartisan: gray"),
                 h("li", None, h("span", {"class": "swatch swatch-accent", "aria-hidden": "true"}),
                   "Charts that are not about parties: the edition color or plain ink"))
    people_gaps = ed.gaps(files=["gaps_community_people"], pattern=r"^Distribution by|No Republican in")
    page.add(section("neutrality", 3, "Neutrality policy",
                     h("p", {"class": "lead"}, "The rules below apply to every page, every chart and every party. "
                                               "A build check enforces the word list automatically."),
                     h("h3", None, "Wording"),
                     h("ul", None,
                       h("li", None, "No loaded election words in headings, chart titles or explanations. Say what changed "
                                     "(for example, which party held a seat before and after), or nothing."),
                       h("li", None, "Characterizations are attributed to whoever made them. Where sources disagree, both "
                                     "are shown."),
                       h("li", None, "Disputes are described by each side's stated position, attributed. The guide never "
                                     "guesses at motives."),
                       h("li", None, "No claims about why people voted the way they did."),
                       h("li", None, "The same nouns and the same party labels everywhere: Democrat (D), Republican (R), "
                                     "Libertarian (L), Independent / no party."),
                       h("li", None, "No praise or criticism adjectives for people, places or employers.")),
                     h("h3", None, "Banned and avoided terms"),
                     h("p", None, "The build fails if any of these appear in the guide's own text:"),
                     h("ul", {"class": "term-list", "data-verbatim": "banned-term-list"},
                       [h("li", None, h("code", None, t)) for t in BANNED_TERMS]),
                     h("p", None, "Also avoided in writing (some have ordinary meanings, so they are checked by a person):"),
                     h("ul", {"class": "term-list", "data-verbatim": "avoided-term-list"},
                       [h("li", None, h("code", None, t)) for t in also_avoided]),
                     h("p", {"class": "muted"}, "Source titles are quoted exactly as the publisher wrote them, so a "
                                                "headline in a source list may use one of these words."),
                     h("h3", None, "Order"),
                     h("ul", None,
                       h("li", None, "Officeholders are listed by office, then district. Candidates keep the order the ballot "
                                     "or canvass lists them."),
                       h("li", None, "Lists are never ordered by party or by vote share, except in a results table you sort "
                                     "yourself."),
                       h("li", None, "Charts show the full range of years the guide has, not a chosen starting point. Changes "
                                     "in how something was reported are marked on the chart as series breaks.")),
                     h("h3", None, "Party colors"),
                     h("p", None, "Party colors appear only on party data, and every colored mark also has a text label."),
                     swatches,
                     h("h3", None, "Equal treatment"),
                     h("ul", None,
                       h("li", None, "Every entry in a set gets the same card size, the same fields and the same prominence."),
                       h("li", None, "Photos: within a set, everyone gets one or no one does. Officeholder directories are "
                                     "text only."),
                       h("li", None, "Elections by the numbers uses the same measures for every race and every party: margin, "
                                     "turnout with its denominator, open seat or incumbent, and how the incumbent first took "
                                     "office. It looks backward only.")),
                     h("h3", {"id": "neutrality-checked"}, "How neutrality was checked"),
                     h("p", None, "Two review passes were made in November 2026 by AI review agents, not by people. Each agent "
                                  "was told to read the built pages twice: once as a skeptical Republican looking for a "
                                  "Democratic slant, and once as a skeptical Democrat looking for a Republican slant, and to "
                                  "list every finding with the exact text and a suggested neutral fix."),
                     h("ul", None,
                       h("li", None, "The first pass covered the people page rules, the party-control charts, the history "
                                     "timeline and the place pages. Changes that followed include correcting the "
                                     "party-control charts, moving community data away from election results on place pages, "
                                     "and explaining why one party is listed first on the ballot."),
                       h("li", None, "The second pass covered the map's \"How areas voted\" layer, party tags, the At a glance "
                                     "boxes and the county lawsuit text. Changes that followed: the map's races are now chosen "
                                     "by a written rule (at the time, every partisan statewide and federal race in each mapped "
                                     "year; later widened to every partisan state-legislative, county, township and town race "
                                     "with precinct results, picked by level, office and year) and the first race shown is the top of the "
                                     "latest ballot; each race shows its county-wide total, checked against the official "
                                     "canvass; map colors for types of government avoid the party red and blue; towns list "
                                     "their council first; one budget basis is shown per place, named; the lawsuit text names "
                                     "the defendants and their filings; and campaign-finance names show a party from county "
                                     "election records, marked as such, when the form leaves it blank.")),

                     h("h3", None, "People who shaped local government"),
                     h("p", None, "A person is included only if the sources document at least one of these, and the same "
                                  "rules are applied to everyone in the data:"),
                     # One source of truth: the people page's own rule text (neutrality B2), so the two can't drift.
                     h("dl", {"class": "criteria"},
                       [[h("dt", {"class": "mono"}, k), h("dd", None, v)] for k, v in _people_criteria().items()]),
                     h("p", None, "Tenure, Higher office and Turning point are computed by the build. First and Family are "
                                  "taken from the sources as recorded."),
                     h("ul", None,
                       h("li", None, "People currently in office are included under the same rules, with the same fields and "
                                     "an in-office label."),
                       h("li", None, "Controversies appear only as documented official findings (a court ruling, censure, "
                                     "investigation report or settlement), applied to every entry by the same rule. A news report "
                                     "of a dispute is not enough."),
                       h("li", None, "The guide publishes how the selected people split by party and era, and says where its "
                                     "research is thin.")),
                     h("ul", {"class": "gaps-list"}, [h("li", None, h("strong", None, g["item"]),
                                                       h("span", {"class": "gap-why"}, g.get("why_missing", "")))
                                                     for g in people_gaps]) if people_gaps else None,
                     h("p", None, h("a", {"href": page.rel("history/people/index.html")}, "People who shaped local government")),
                     h("h3", None, "Community data"),
                     h("ul", None,
                       h("li", None, "The same indicators for every place, with Census category names as published, the "
                                     "survey years, and margins of error."),
                       h("li", None, "Community data is never placed on or next to election results in the guide's own charts, "
                                     "and the guide computes no correlations between them."),
                       h("li", None, "Links between place and voting come only from published studies, attributed, with their "
                                     "method and limits. Patterns about places do not describe the people in them."),
                       h("li", None, "Comparisons are to Indiana and the United States only, never to hand-picked counties.")),
                     ed=ed))

    # ------------------------------------------------------------------ badges (foundation definitions kept)
    page.add(section("badges", 4, "Status and scope badges",
                     h("p", None, "Every figure carries a status badge. Tap or hover a badge anywhere in the guide to see its "
                                  "meaning; each one links here."),
                     h("dl", {"class": "badge-defs"},
                       [[h("dt", None, status_badge(k)), h("dd", None, v[1])] for k, v in STATUS.items()] +
                       [[h("dt", None, scope_badge(s, ed)), h("dd", None, t)] for s, t in (
                           ("indiana", "Applies to every Indiana county."),
                           ("county", f"Data or rules specific to {ed.county_label}."),
                           ("exception", f"Where state law treats {ed.county_label} differently from most counties."))]),
                     h("h3", None, "Two more labels"),
                     h("ul", None,
                       h("li", None, h("strong", None, "Takes office Jan 1, 2027 (results unofficial). "),
                         "People elected on Nov 3, 2026 are listed as incoming. Their results stay unofficial until the county "
                         "certifies them."),
                       h("li", None, h("strong", None, "Confidence. "),
                         "Many rows also record high, medium or low confidence. Low-confidence values stay in tables, "
                         "flagged, and are never used in headings, chart titles or summaries.")),
                     ed=ed))

    # ------------------------------------------------------------------ counting (foundation rules kept)
    page.add(section("counting", 5, "How the layer diagram counts seats",
                     h("p", None, "How the landing page's layer diagram counts seats:"),
                     h("ul", None, [h("li", None, r) for r in COUNTING_RULES]),
                     ed=ed))

    # ------------------------------------------------------------------ corrections
    log_rows = []
    for path, area, sid, summary in CORRECTION_FILES:
        f = ed.root / path
        n = _count_findings(f.read_text(encoding="utf-8")) if f.is_file() else 0
        log_rows.append([area, h("span", None, summary, c.cite(sid)), fmt_int(n) if n else "not counted",
                         h("code", None, path.rsplit("/", 1)[-1])])
    page.add(section("corrections", 6, "Corrections",
                     h("p", None, "Every accepted correction is logged below with its date. Corrections are made in the data, "
                                  "so every page that uses the figure changes at once."),
                     h("h3", None, "Corrections log"),
                     h("p", None, h("strong", None, f"{fmt_date(cfg['data_as_of'], long=True)}: fact-check corrections applied "
                                                    "before the first draft. "),
                       "The fact-check findings were applied to the data in five areas. The project keeps a full record of each "
                       "one; the table summarizes what kind of corrections each area needed."),
                     data_table("corrections-log", ["Area", "What was corrected", "Findings logged", "Project record"], log_rows,
                                caption="Fact-check corrections applied, by area", numeric=(2,), min_width="40rem"),
                     h("p", None, "Corrections reported by readers after release: none yet."),
                     ed=ed))

    # ------------------------------------------------------------------ changelog
    page.add(section("changelog", 7, "Changelog",
                     h("dl", {"class": "changelog"},
                       h("dt", None, h("span", {"class": "mono"}, f"v{cfg.get('version', '')}"), " ",
                         h("time", {"datetime": cfg["data_as_of"]}, fmt_date(cfg["data_as_of"], long=True))),
                       h("dd", None,
                         h("p", None, f"First draft of the {cfg['edition']}, with data as of "
                                      f"{fmt_date(cfg['data_as_of'], long=True)}. Not yet published publicly."),
                         h("ul", None,
                           h("li", None, "Research, fact-check and data conversion complete; corrections applied."),
                           h("li", None, "2026 general-election figures are unofficial until the county certifies them."),
                           h("li", None, "Local campaign-finance figures are on the Campaign finance page, each with its "
                                         "check status (arithmetic check on every form, second reading on a sample)."),
                           h("li", None, "Author disclosure published.")))),
                     ed=ed))

    # ------------------------------------------------------------------ looks (reader-selectable skins)
    page.add(about_looks_section(ed, 8))

    # ------------------------------------------------------------------ gaps + sources index (index is this page's Sources list)
    gaps = ([] if not pending else [
        {"item": "Author disclosure statement", "why_missing": "To be written by the author before publication.",
         "how_to_fill": "The author adds it to the edition settings (author_disclosure)."}]) + [
    ]
    if not ed.table("cf_local"):
        gaps.append(_cf_local_gap(ed))
    unpublished = _unpublished_sources(ed)
    page.add(callout(h("p", None, "Superscript numbers on this page link to the matching entry in the index below."), kind="note"))
    # No page.finish(): the sources index below is this page's Sources list (citations link into it).
    page.add(gaps_section(gaps, page))
    groups = []
    by_kind: dict[str, list[str]] = {}
    # The source files were written per research area, so one document can carry several IDs (a canvass
    # cited by the results, government and community files). List each web address once, with its other
    # IDs as anchors inside the entry. Different datasets behind one download form (all kind "dataset")
    # stay separate entries.
    sort_key = lambda i: (i.split("-")[0], i)
    by_url: dict[str, list[str]] = {}
    for sid, s in ed.sources.items():
        url = (s.get("url") or "").split(" ; ")[0].strip()
        if sid not in unpublished and url.startswith("http"):
            by_url.setdefault(url, []).append(sid)
    aliases: dict[str, list[str]] = {}
    hidden: set[str] = set()
    for url, ids in by_url.items():
        if len(ids) < 2 or all(ed.sources[i].get("kind") == "dataset" for i in ids):
            continue
        ids = sorted(ids, key=sort_key)
        aliases[ids[0]] = ids[1:]
        hidden.update(ids[1:])
    for sid, s in ed.sources.items():
        if sid in unpublished or sid in hidden:
            continue
        by_kind.setdefault(s.get("kind", "") or "other", []).append(sid)
    kind_groups = list(KIND_GROUPS)
    known = [k for k, _, _ in kind_groups]
    for k in sorted(by_kind):
        if k not in known:
            kind_groups.append((k, k.title(), ""))
    total = 0
    for kind, label, blurb in kind_groups:
        ids = sorted(by_kind.get(kind, []), key=sort_key)
        if not ids:
            continue
        total += len(ids)
        gid = f"sources-{kind}"
        groups.append(h("section", {"class": "src-group", "id": gid, "aria-labelledby": f"{gid}-h"},
                        h("h3", {"id": f"{gid}-h"}, label, " ", h("span", {"class": "muted mono"}, f"({len(ids)})")),
                        h("p", {"class": "muted"}, blurb) if blurb else None,
                        h("ul", {"class": "source-list source-index"},
                          [_source_item(ed, i, aliases=aliases.get(i)) for i in ids])))
    for sid in c.order:  # every citation on this page must land in the index
        if sid not in ed.sources or sid in unpublished:
            ed.warnings.append(f"about: cited source {sid} is not in the sources index")
    files = sorted({s.get("_file", "") for s in ed.sources.values()})
    page.add(h("section", {"class": "sources", "id": "sources", "aria-labelledby": "sources-h"},
               h("h2", {"id": "sources-h"}, "Sources index"),
               h("p", None, f"Every source behind the guide: {total} entries from {len(files)} source files "
                            f"({', '.join(f + '.csv' for f in files)}), grouped by kind. The ID after each entry is the one "
                            "data rows cite."
                            + (f" {sum(len(v) for v in aliases.values())} more IDs point to a document "
                               "already listed; each such entry names its other IDs." if aliases else "")),
               h("p", {"class": "muted"}, f"{len(unpublished)} source used only for internal research notes, which the guide "
                                          "does not publish, is not listed." if len(unpublished) == 1 else
                 f"{len(unpublished)} sources used only for internal research notes, which the guide does not publish, are not listed.")
               if unpublished else None,
               h("nav", {"class": "src-jump", "aria-label": "Source kinds"},
                 h("ul", None, [h("li", None, h("a", {"href": f"#sources-{k}"}, lbl))
                                for k, lbl, _ in kind_groups if by_kind.get(k)])),
               groups))
    return page


# ============================================================================ data


DATASETS = [
    # key, anchor, title, scope, description, preview columns
    ("results", "ds-results", "Election results", "county",
     "Every contest and candidate the guide has from 1963 to 2026: votes, percent, winner flag, primary ballot, "
     "and the vote-for count. Percentages from 2020 on are computed from the vote counts. Public questions use YES and NO "
     "as the candidate.",
     ["election_id", "contest_label", "district", "party_primary", "candidate", "party", "votes", "pct", "winner",
      "status", "confidence", "source_ids"]),
    ("elections", "ds-elections", "Elections", "county",
     "One row per election: date, type, which voters it covered, registered voters, ballots cast, turnout and "
     "straight-party ballots. Municipal elections cover only city and town voters, so their turnout uses a smaller "
     "denominator.",
     ["election_id", "date", "type", "scope", "registered", "ballots_cast", "turnout_pct", "straight_party_d",
      "straight_party_r", "straight_party_other", "status", "source_ids"]),
    ("terms", "ds-terms", "Terms of office", "county",
     "Who held each seat and when: one row per person per continuous stretch in a seat, with party, start and end dates "
     "and how they were chosen (election, caucus or appointment). Terms starting Jan 1, 2027 come from the unofficial "
     "2026 results.",
     ["office_id", "person", "party", "start", "end", "selected_by", "first_selected_by", "status", "confidence", "source_ids"]),
    ("offices", "ds-offices", "Offices", "county",
     "Every elected (and some appointed) office in the county: which government it belongs to, its district, seat count, "
     "whether the race is partisan, term length and next regular election.",
     ["office_id", "unit_id", "title", "district", "seats", "elected", "partisan", "term_years", "next_election",
      "status", "source_ids"]),
    ("units", "ds-units", "Units of government", "county",
     "The county, cities, towns, townships, school corporations, libraries and special districts, with the places each "
     "covers and its website.",
     ["unit_id", "unit_type", "name", "places_covered", "website", "status", "source_ids"]),
    ("budgets", "ds-budgets", "Budgets", "county",
     "Budget totals by unit and year, 2012 to 2026, each tagged with its reporting basis and series. Rows marked "
     "series_break have no amount: they mark where the way a budget was reported changed.",
     ["unit_id", "year", "basis", "amount", "adopted_or_actual", "series_id", "status", "source_ids"]),
    ("tax_rates", "ds-tax-rates", "Property tax rates", "county",
     "Tax rates per $100 of assessed value, by unit, taxing district and year.",
     ["unit_id", "taxing_district", "year", "rate_per_100", "rate_kind", "status", "source_ids"]),
    ("debt", "ds-debt", "Debt", "county",
     "Year-end principal owed by each unit, by type of debt, from the state's annual financial reports.",
     ["unit_id", "year", "debt_type", "amount", "status", "source_ids"]),
    ("cf_state", "ds-cf-state", "State campaign finance", "county",
     "Receipts and spending by the campaign committees of state legislators whose districts include part of the county, "
     "by the calendar year reports were filed (not by election cycle), with the largest types of contributors.",
     ["committee", "candidate", "office", "district", "party", "year", "receipts", "expenditures", "top_funder_types",
      "status", "source_ids"]),
    ("cf_local", "ds-cf-local", "Local campaign finance", "county",
     "One row per campaign-finance report filed with the county by local candidates' committees and posted as scanned "
     "forms: report type and period, receipts, spending, cash on hand and debts as written on the form. Every row says "
     "how its transcription checked out (see the key below) and whether it was entered twice.",
     ["candidate", "committee", "office", "party", "report_type", "period_to", "receipts_period", "expenditures_period",
      "cash_end_period", "transcription_status", "double_entry", "status", "source_ids"]),
    ("cf_large_contributions", "ds-cf-large", "Local large contributions", "county",
     "Contributions of $1,000 or more reported on the county's supplemental large-contribution forms (CFA-11): "
     "candidate, committee, contributor, amount and date, as written on the form.",
     ["candidate", "committee", "contributor", "amount", "date", "status", "source_ids"]),
    ("indicator_values", "ds-indicators", "Community indicators", "county",
     "Census and Bureau of Labor Statistics figures for the county, its cities, its townships, Indiana and the United "
     "States, with margins of error and survey years.",
     ["geo_type", "geo_name", "indicator_id", "value", "moe", "vintage", "status", "source_ids"]),
    ("people", "ds-people", "People who shaped local government", "county",
     "People selected by the published rules (see the neutrality policy on About), with the offices they held, the "
     "criteria they meet and any documented official findings.",
     ["name", "offices_summary", "parties", "criteria", "in_office_now", "documented_findings", "status", "confidence",
      "source_ids"]),
]

NUMERIC_COLS = {"votes", "pct", "registered", "ballots_cast", "turnout_pct", "straight_party_d", "straight_party_r",
                "straight_party_other", "amount", "rate_per_100", "receipts", "expenditures", "value", "moe",
                "seats", "term_years", "year", "receipts_period", "expenditures_period", "cash_end_period"}

TRANSCRIPTION = {
    "verified": "Every total on the form adds up, to the cent, with the lines it summarizes.",
    "derived": "One unclear cell was filled in from the form's own totals; the notes say which.",
    "filer-inconsistent": "Transcribed as written, but the filer's own numbers do not add up; the notes describe how.",
    "unreadable": "The scan could not be read; the notes say what is missing.",
}
DOUBLE_ENTRY = {
    "single": "Entered once.",
    "agreed": "Entered twice, blind; both entries matched.",
    "adjudicated": "Entered twice, blind; a reviewer settled the differences.",
}


def _publish_rows(ed, key: str) -> tuple[list[str], list[dict], str | None]:
    """Columns and rows as published. people.csv drops its internal research-notes column and
    source ids used only by those notes (see the neutrality policy: official findings only)."""
    rows = ed.table(key)
    # only the file's own columns: page modules may cache working fields ("_" prefix) on shared rows
    cols = [k for k in rows[0].keys() if not k.startswith("_")] if rows else []
    if key != "people":
        return cols, rows, None
    hide = _unpublished_sources(ed)
    cols = [k for k in cols if k != "notes"]
    out = []
    for r in rows:
        r2 = {k: r[k] for k in cols}
        r2["source_ids"] = ";".join(s for s in split_ids(r.get("source_ids")) if s not in hide)
        out.append(r2)
    return cols, out, ("The people file's research-notes column is not published: the guide shows only documented "
                       "official findings about people.")


def _csv_text(cols: list[str], rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


def _cell(page, col: str, val: str):
    if col == "status":
        return status_badge(val, page)
    if col == "confidence":
        return h("span", None, val, " ", status_badge("low", page)) if val == "low" else val
    if col == "source_ids":
        return h("span", {"class": "mono ids"}, val, page.cites.cite(val))
    if col == "website" and val.startswith("http"):
        return h("a", {"href": val, "target": "_blank", "rel": "noopener"}, val)
    return val


def _transcription_key(rows) -> Markup:
    """Counts and meanings of the campaign-finance transcription checks (from the transcription brief)."""
    tc = Counter(r.get("transcription_status", "") for r in rows)
    dc = Counter(r.get("double_entry", "") for r in rows)
    def dl(counter, labels, head):
        keys = [k for k in labels if counter.get(k)] + sorted(k for k in counter if k not in labels)
        return [h("p", {"class": "outline-h"}, head),
                h("dl", {"class": "criteria"},
                  [[h("dt", {"class": "mono"}, f"{k or 'blank'} ({fmt_int(counter[k])})"),
                    h("dd", None, labels.get(k, "Not defined in the transcription brief."))] for k in keys])]
    return h("div", {"class": "cf-key"}, dl(tc, TRANSCRIPTION, "Transcription check (transcription_status)"),
             dl(dc, DOUBLE_ENTRY, "Entered how many times (double_entry)"))


def _dataset_block(ed, page, n: int, spec) -> Markup:
    key, anchor, title, scope, desc, pcols = spec
    cols, rows, note = _publish_rows(ed, key)
    if not rows:
        return section(anchor, n, title, h("p", None, "This file has no rows yet."), scope=scope, ed=ed)
    folder = "data/indiana" if key in ("indicators",) else f"data/editions/{ed.edition_id}"
    pcols = [p for p in pcols if p in cols]
    shown = rows[:PREVIEW_ROWS]
    trows = [[_cell(page, col, r.get(col, "")) for col in pcols] for r in shown]
    numeric = tuple(i for i, col in enumerate(pcols) if col in NUMERIC_COLS)
    preview = data_table(f"{anchor}-preview", pcols, trows, copy=False,
                         caption=(f"{title}: first {len(shown)} of {fmt_int(len(rows))} rows" if len(shown) < len(rows)
                                  else f"{title}: all {fmt_int(len(rows))} rows"),
                         numeric=numeric, min_width=f"{max(32, len(pcols) * 6)}rem")
    csv_id = f"{anchor}-csv"
    left_out = [col for col in cols if col not in pcols]
    tools = h("div", {"class": "table-tools ds-tools"},
              h("button", {"type": "button", "class": "btn btn-small", "data-copy-csv": csv_id, "data-rows": len(rows), "id": f"{anchor}-copy"},
                "Copy CSV"),
              h("span", {"class": "ds-copy-note muted"},
                f"Copies all {fmt_int(len(rows))} rows and all {len(cols)} columns."))
    return section(anchor, n, title,
                   h("p", None, desc),
                   h("p", {"class": "ds-meta mono"}, f"{fmt_int(len(rows))} rows · {len(cols)} columns · {folder}/{key}.csv"),
                   _status_mix(rows, page),
                   _transcription_key(rows) if "transcription_status" in cols else None,
                   h("p", {"class": "ds-sources"}, "Sources used by these rows:", page.cites.cite_compact(_union(rows))),
                   h("p", {"class": "muted"}, f"The preview leaves out: {', '.join(left_out)}. Copy CSV includes them."
                     if left_out else "The preview shows every column.", " " + note if note else ""),
                   preview, tools, json_script(csv_id, _csv_text(cols, rows)),
                   scope=scope, ed=ed)


def _fill(text: str, ed) -> str:
    return (text.replace("{STATE_FIPS}", ed.config.get("state_fips", "{STATE_FIPS}"))
                .replace("{COUNTY_FIPS}", ed.config.get("county_fips", "{COUNTY_FIPS}"))
                .replace("{STATE_NAME}", ed.config.get("state", "{STATE_NAME}")))


URL_RE = re.compile(r"https?://[^\s\"']+")


def build_data(site):
    ed = site.ed
    cfg = ed.config
    page = site.page("data/index.html")
    c = page.cites
    toc = [("datasets", "Datasets")] + [(s[1], s[2]) for s in DATASETS] + \
          [("pull", "Pull it yourself"), ("gaps", "Gaps"), ("sources", "Where the data comes from")]
    _hero(page, "Reference · Context", "Data and sources",
          "Every main table behind the guide. Each one has a preview and a Copy CSV button that copies the whole "
          "table, so you can paste it into a spreadsheet.",
          [scope_badge("county", ed), scope_badge("indiana", ed)], toc)

    page.add(section("datasets", None, "How to use these tables",
                     h("ul", None,
                       h("li", None, "This viewer can't download files, so each dataset has a Copy CSV button. Paste the "
                                     "result into a spreadsheet or a text file."),
                       h("li", None, f"Large tables show only their first {PREVIEW_ROWS} rows here, in file order. "
                                     "Copy CSV always copies every row."),
                       h("li", None, "Every row has a status (what kind of source it rests on) and source IDs. The IDs match "
                                     "the source lists on each page and the ",
                         h("a", {"href": page.rel("about/index.html#sources")}, "sources index"), "."),
                       h("li", None, "Rows marked LOW CONFIDENCE are kept for completeness. Check them before relying on them.")),
                     ed=ed))
    for i, spec in enumerate(DATASETS, start=1):
        page.add(_dataset_block(ed, page, i, spec))

    # ------------------------------------------------------------------ pull it yourself
    n = len(DATASETS) + 1
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

    pull = section("pull", n, "How to pull it yourself",
                   h("p", {"class": "lead"}, "The guide's figures come from public sources you can open yourself. Here is "
                                             "where each one lives and how it was pulled."),
                   h("h3", {"id": "pull-results"}, "County election results archive"),
                   h("p", None, "The county election board posts a PDF report for each election on one page: ",
                     ext(res_arch.get("url", "")), c.cite("RES-030"),
                     " Check each report's header: an election-night report says Unofficial; the final canvass says Official. "
                     "Reports from 2010 to 2019 and the 2024 general election are scanned images, so their text has to be "
                     "read by text recognition.", c.cite("RES-001;RES-027")) if res_arch.get("url") else None,
                   h("h3", {"id": "pull-filings"}, "County candidate filings"),
                   h("p", None, "Local candidates' campaign-finance reports, large-contribution notices and candidacy "
                                "filings are posted as scanned documents on the county's Candidate Filings page: ",
                     ext(filings.get("url", "")), c.cite("SVC-019"),
                     " Each document opens as its own PDF; the guide's local campaign-finance rows cite each one by its "
                     "document number.") if filings.get("url") else
                   h("p", None, "The guide's source files do not include the address of the county's candidate-filings page "
                                "yet, so it is not listed here. It is recorded under Gaps below."),
                   h("h3", {"id": "pull-gateway"}, "Indiana Gateway (budgets, tax rates, debt)"),
                   h("p", None, "Budgets, tax rates and debt come from the bulk download page of Indiana Gateway: ",
                     ext(gw.get("url", "")), c.cite("MON-001;MON-002;MON-004")),
                   h("ol", None,
                     h("li", None, "Choose the data set (Budget Data for budgets and tax rates; Annual Financial Report "
                                   "for spending, receipts and debt)."),
                     h("li", None, f"Filter to county code {cfg.get('gateway_county_code', '')} ({ed.county_label})."),
                     h("li", None, "Remove repeated rows before adding anything up. The download the guide used repeated "
                                   "every row five times.", c.cite("MON-001"))),
                   h("h3", {"id": "pull-cf"}, "State campaign finance (bulk files)"),
                   h("p", None, "The Indiana Election Division lists its bulk files here: ", ext(cf_page.get("url", "")),
                     c.cite("MON-020"), " Each year has a contribution file and an expenditure file at a fixed address:"),
                   h("pre", {"class": "code-block"},
                     h("code", None, year_pattern(cf_contrib.get("url", "")) + "\n" + year_pattern(cf_exp.get("url", "")))),
                   h("p", None, "Replace {YEAR} with a four-digit year. Files are grouped by the year a report was filed, "
                                "not by election cycle, and they have no district or cash-on-hand field.",
                     c.cite("MON-020;MON-021;MON-022")),
                   h("h3", {"id": "pull-census"}, "Census and Bureau of Labor Statistics queries"),
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
                   h("p", None, "Every indicator, with its table and variable codes:"),
                   data_table("indicator-defs", ["Indicator", "Label", "Universe", "Table and variables", "Margin of error"],
                              ind_rows, caption=f"Indicator definitions ({len(inds)}), data/indiana/indicators.csv",
                              min_width="56rem"),
                   scope="indiana", ed=ed)
    page.add(pull)

    # ------------------------------------------------------------------ gaps + sources ("Where the data comes from")
    gaps = []
    if not filings.get("url"):
        gaps.append({"item": "Address of the county's candidate-filings page", "why_missing": "Not in the guide's source files.",
                     "how_to_fill": "Find the page on the county election board's site and add it to the sources files."})
    if not ed.table("cf_local"):
        gaps.append(_cf_local_gap(ed))
    gaps += ed.gaps(files=["gaps_gov"], pattern=r"Official \(certified\) 2026")
    gaps += ed.gaps(files=["gaps_money"], pattern=r"cash on hand")
    gaps += ed.gaps(files=["gaps_community_people"], pattern=r"Decennial population rows|Precinct datasets identified")
    page.add(gaps_section(gaps, page))
    page.add(h("section", {"class": "sources", "id": "sources", "aria-labelledby": "sources-h"},
               h("h2", {"id": "sources-h"}, "Where the data comes from"),
               h("p", None, f"The {len(c.order)} sources cited on this page, numbered as in the superscripts. The ",
                 h("a", {"href": page.rel("about/index.html#sources")}, "sources index"),
                 " on About lists every source the guide uses, grouped by kind."),
               h("ol", {"class": "source-list"}, [_source_item(ed, sid) for sid in c.order])))
    return page


# ============================================================================ teach


OTHER_PATH_NOTES = {
    "who-does-what": ("Students can name the governments that cover one address and say which one to contact for a "
                      "given service.",
                      ["Pick one everyday service (trash pickup, a pothole, a school bus). Which government handles it, "
                       "and how could you reach the people responsible?",
                       "Some boards are appointed, not elected. What are the trade-offs of each way of choosing members?"]),
    "run": ("Students can describe the steps to get on the ballot for one local office and what a candidate must report.",
            ["Choose an office from the guide. What would someone need to do, and by when, to run for it?",
             "Why might a state require candidates to report campaign money? What does the public learn from the reports?"]),
    "follow-the-money": ("Students can explain why budget totals depend on which funds are counted and how one tax bill "
                         "is split among governments.",
                         ["Two news stories give different totals for the same budget. What questions would you ask to "
                          "find out why?",
                          "Look at a budget chart with a series break. What would a reader get wrong if the break were "
                          "not marked?"]),
    "how-we-got-here": ("Students can read a party-control timeline and place sourced events in order.",
                        ["Pick one dated turning point. What do the sources say happened, and what do they not say?",
                         "Why does the guide attribute descriptions of events to the outlet that made them?"]),
    "elections-by-the-numbers": ("Students can compare turnout across election types using the right denominator.",
                                 ["Odd-year city elections and even-year county elections have different electorates. "
                                  "How should you compare their turnout fairly?",
                                  "What does a margin tell you about a past race, and what can it not tell you about the "
                                  "next one?"]),
    "know-your-community": ("Students can read a census estimate with its margin of error and compare it to Indiana and "
                            "the United States.",
                            ["An estimate for a small town has a large margin of error. How confident should you be in "
                             "comparing it with another town?",
                             "How could the size of the local tax base affect what a government can afford?"]),
}


def _path(pid: str) -> dict:
    return next(p for p in sitemap.PATHS if p["id"] == pid)


def _stop_link(page, p: dict, n: int) -> str:
    stop = p["stops"][n - 1]
    return page.rel(stop["page"]) + f"#path-{p['id']}-{n}"


def build_teach(site):
    ed = site.ed
    cfg = ed.config
    page = site.page("teach/index.html", body_class="teach-page")
    c = page.cites
    vs = _path("vote-smarter")
    toc = [("kit", "Lesson kit: Vote smarter"), ("plan", "45-minute plan"), ("facts", "Facts to use"),
           ("prompts", "Discussion prompts"), ("handout", "Handout"), ("outlines", "Other paths"),
           ("prompt-rules", "How prompts are written"), ("gaps", "Gaps")]
    _hero(page, "For teachers and groups", "For teachers and group leaders",
          "Ready-to-use lessons built on the guide's learning paths. Each lesson uses only facts that are on the "
          "reference pages, with their sources.",
          [scope_badge("indiana", ed), scope_badge("county", ed)], toc)

    # ------------------------------------------------------------------ kit overview
    start = _stop_link(page, vs, 1)
    page.add(section("kit", 1, "Lesson kit: Vote smarter in your next election",
                     h("dl", {"class": "kit-facts"},
                       h("dt", None, "For"), h("dd", None, "High school classes, adult education and community groups"),
                       h("dt", None, "Time"), h("dd", None, "45 minutes"),
                       h("dt", None, "Path"), h("dd", None, h("a", {"href": start}, f"{vs['title']} ({len(vs['stops'])} stops, "
                                                                                   f"about {vs['minutes']} minutes)")),
                       h("dt", None, "You need"), h("dd", None, "A screen or projector, one device per group, the handout below")),
                     h("h3", None, "Learning objectives"),
                     h("p", None, "By the end, participants can:"),
                     h("ol", None,
                       h("li", None, "Say which offices appear on their next ballot and what each one decides."),
                       h("li", None, "Explain why turnout differs between election years, and name the denominator behind "
                                     "a turnout figure."),
                       h("li", None, "Describe what a judicial retention vote and a public question ask."),
                       h("li", None, "Find official information about candidates and check a figure against its source."),
                       h("li", None, "Tell the difference between a pattern about places and a claim about people.")),
                     ed=ed))

    # ------------------------------------------------------------------ plan
    plan = [
        ("0-5", "Opening question: \"What will be on your next ballot besides the top race?\" Collect guesses.", None),
        ("5-12", "Stop 1: What's on your next ballot. Groups list the seats up next where they live.", 1),
        ("12-20", "Stop 2: What each office controls. Each group picks one office and reports what it decides.", 2),
        ("20-28", "Stop 3: Results history, turnout first. Compare turnout in odd and even years using the table below.", 3),
        ("28-33", "Stop 4: Judges and public questions. Read one retention line and one question aloud.", 4),
        ("33-38", "Stop 5: Where to find candidate information. Show the official places to look.", 5),
        ("38-43", "Discussion: two or three prompts from the list below, including the places-and-people prompt.", None),
        ("43-45", "Exit ticket: handout question 5.", None),
    ]
    prow = []
    for t, what, n in plan:
        link = h("a", {"href": _stop_link(page, vs, n)}, vs["stops"][n - 1]["title"]) if n else ""
        prow.append([h("span", {"class": "mono"}, t), what, link])
    page.add(section("plan", 2, "45-minute plan",
                     data_table("plan-table", ["Minutes", "Activity", "Page"], prow, caption="Lesson plan, 45 minutes",
                                copy=False, min_width="36rem"),
                     h("p", {"class": "muted"}, "Each page link opens that stop of the path, with Next and Previous buttons."),
                     ed=ed))

    # ------------------------------------------------------------------ facts (sourced)
    rules = [_rule_line(ed, page, k) for k in ("general_election_date", "primary_date", "municipal_cycle",
                                                 "even_year_offices", "voter_registration_deadline",
                                                 "early_voting_period", "photo_id_at_polls", "superior_court_retention")]
    rules = [r for r in rules if r is not None]
    els = [e for e in ed.elections.values() if e["type"] in ("general", "municipal_general")
           and e["date"] >= "2010" and e.get("turnout_pct")]
    els.sort(key=lambda e: e["date"])
    erows = [[e["date"][:4], "Even-year general" if e["type"] == "general" else "Odd-year city and town",
              e["scope"], fmt_int(e["registered"]), fmt_int(e["ballots_cast"]), f"{e['turnout_pct']}%",
              h("span", None, status_badge(e["status"], page), c.cite(e["source_ids"]))] for e in els]
    page.add(section("facts", 3, "Facts to use in this lesson",
                     h("p", None, "These come straight from the guide's data, with sources. Use them instead of facts from "
                                  "memory."),
                     h("h3", None, "Indiana election rules ", scope_badge("indiana", ed)),
                     h("ul", {"class": "fact-list"}, rules),
                     h("h3", None, f"Turnout in {ed.county_label} general elections"),
                     h("p", None, "Turnout is ballots cast divided by registered voters. Odd-year elections cover only city "
                                  "and town voters, so they have fewer registered voters. Compare like with like."),
                     data_table("turnout-lesson", ["Year", "Election", "Who could vote", "Registered", "Ballots cast",
                                                   "Turnout", "Status"], erows,
                                caption=f"General-election turnout, {els[0]['date'][:4]} to {els[-1]['date'][:4]}" if els else None,
                                numeric=(3, 4, 5), min_width="44rem") if erows else None,
                     h("p", {"class": "muted"}, "Rows marked UNOFFICIAL may change when the county certifies the results."),
                     scope="county", ed=ed))

    # ------------------------------------------------------------------ prompts
    rv_link = h("a", {"href": page.rel("community/research-on-voting/index.html")}, "Research on place and voting")
    page.add(section("prompts", 4, "Discussion prompts",
                     h("ol", {"class": "prompt-list"},
                       h("li", None, "Which office on your next ballot affects your daily life the most? What evidence from the "
                                     "guide supports your answer?"),
                       h("li", None, "Why do you think fewer people vote in odd-year city elections? List possible reasons, "
                                     "then say what evidence would be needed to test each one."),
                       h("li", None, "A judge's name appears with only YES and NO. What would you want to know before voting, "
                                     "and where could you find it?"),
                       h("li", {"class": "prompt-key"},
                         h("strong", None, "Places and people. "),
                         "Suppose a township where incomes are higher also gave more of its votes to one party. Does that "
                         "tell you how any one higher-income person there voted? Why or why not?",
                         h("div", {"class": "teacher-note"},
                           h("p", {"class": "mono"}, "Teacher note"),
                           h("p", None, "This is the ecological fallacy: a pattern measured across places does not tell you "
                                        "how the individuals in those places behaved. The township could contain many "
                                        "higher-income voters who chose the other party, and the pattern could come from "
                                        "other differences between places. Ask what kind of evidence would describe "
                                        "individuals (a survey of voters, with its margin of error) and why the guide never "
                                        "puts community data on its election charts."),
                           h("p", None, "Follow-up: ", rv_link, " shows how published studies state their geography, "
                                        "method and limits."))),
                       h("li", None, "Two sources report different numbers for the same result. Which would you trust, and "
                                     "why? Check the status badges."),
                       h("li", None, "What is one question about your local government you could not answer today? Where "
                                     "would you look next?")),
                     ed=ed))

    # ------------------------------------------------------------------ handout
    blank = h("span", {"class": "fill-line", "aria-hidden": "true"})
    qs = [
        ("What year is your next election, and name two offices on that ballot.", vs["stops"][0]),
        ("Pick one of those offices. Write one thing it decides.", vs["stops"][1]),
        ("Write the turnout for one even-year and one odd-year election. Which had more registered voters?", vs["stops"][2]),
        ("What does a YES vote on a judge's retention mean?", vs["stops"][3]),
        ("Name one official place to find information about candidates, and one thing you learned today.", vs["stops"][4]),
    ]
    page.add(h("section", {"class": "block", "id": "handout", "aria-labelledby": "handout-h"},
               h("header", {"class": "block-head"}, h("span", {"class": "kicker"}, "§ 05"),
                 h("h2", {"id": "handout-h"}, "Handout")),
               h("p", {"class": "muted screen-only"}, "This sheet is laid out for printing once the guide has a public host. "
                                                      "In this viewer, copy the questions or show them on screen."),
               h("article", {"class": "handout", "aria-label": "Student handout"},
                 h("header", {"class": "handout-head"},
                   h("p", {"class": "handout-series mono"}, f"{cfg['series']} · {cfg['edition']}"),
                   h("h3", {"class": "handout-title"}, "Vote smarter in your next election"),
                   h("p", {"class": "handout-name"}, "Name ", blank, " Date ", blank)),
                 h("ol", {"class": "handout-qs"},
                   [h("li", None, h("p", None, q), h("p", {"class": "handout-where mono"}, f"Look in: {stop['title']}"),
                      h("span", {"class": "fill-line fill-wide", "aria-hidden": "true"}),
                      h("span", {"class": "fill-line fill-wide", "aria-hidden": "true"})) for q, stop in qs]),
                 h("p", {"class": "handout-check"}, "Check every answer against the source link next to the figure in the guide."),
                 h("p", {"class": "handout-foot mono"}, f"Data as of {fmt_date(cfg['data_as_of'], long=True)} · "
                                                        f"v{cfg.get('version', '')} · teach/index.html"))))

    # ------------------------------------------------------------------ other paths
    cards = []
    for p in sitemap.PATHS:
        if p["id"] == "vote-smarter":
            continue
        objective, prompts = OTHER_PATH_NOTES.get(p["id"], ("", []))
        cards.append(h("article", {"class": "card outline-card", "id": f"outline-{p['id']}"},
                       h("h3", {"class": "card-title"}, p["title"]),
                       h("p", {"class": "path-meta mono"}, f"{len(p['stops'])} stops · about {p['minutes']} min"),
                       h("p", None, p["blurb"]),
                       h("p", None, h("strong", None, "Objective: "), objective) if objective else None,
                       h("p", {"class": "outline-h"}, "Stops"),
                       h("ol", {"class": "outline-stops"},
                         [h("li", None, h("a", {"href": _stop_link(page, p, i + 1)}, s["title"]))
                          for i, s in enumerate(p["stops"])]),
                       h("p", {"class": "outline-h"}, "Prompts") if prompts else None,
                       h("ul", None, [h("li", None, q) for q in prompts]) if prompts else None,
                       h("p", None, h("a", {"class": "btn btn-small", "href": _stop_link(page, p, 1)}, "Start this path"))))
    page.add(section("outlines", 6, "Short outlines for the other paths",
                     h("p", None, "Full kits for these paths will follow the same format. Until then, each outline gives an "
                                  "objective, the stops and two prompts."),
                     h("div", {"class": "card-grid outline-grid"}, cards),
                     ed=ed))

    # ------------------------------------------------------------------ prompt rules
    page.add(section("prompt-rules", 7, "How prompts are written",
                     h("ul", None,
                       h("li", None, "No prompt asks which party, candidate or side is right."),
                       h("li", None, "Prompts ask for evidence: what the guide shows, what it does not show, and where to "
                                     "look next."),
                       h("li", None, "Prompts about community data talk about places, never about groups of people as voters."),
                       h("li", None, "Facts in a lesson come from the guide's pages, with their sources and badges. "
                                     "The ", h("a", {"href": page.rel("about/index.html#neutrality")}, "neutrality policy"),
                         " applies to lessons too.")),
                     ed=ed))

    gaps = [{"item": "Full lesson kits for six of the seven paths",
             "why_missing": "The first release ships one complete kit to prove the format; the others are outlines.",
             "how_to_fill": "Write kits in the same format, using only facts on the reference pages."}]
    gaps += ed.gaps(files=["gaps_community_people"], pattern=r"No published analysis found of township")
    page.finish(gaps=gaps)
    return page


PAGES = {
    "about/index.html": build_about,
    "data/index.html": build_data,
    "teach/index.html": build_teach,
}
