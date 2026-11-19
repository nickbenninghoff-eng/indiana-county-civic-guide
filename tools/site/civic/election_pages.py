"""Election pages: paths, which tabs each election has, and links to them (phase 6 step 4, 2026-11-16;
planning/design-direction-2026-11-16.md sections 2 to 4). One page per row of elections.csv, with the tabs of
civic/tabs.py:

    elections/index.html                    the Elections hub (pages/elections.py build_hub)
    elections/<election_id>/index.html      Overview: date, kind, turnout with its base, contests, uncontested seats,
                                            the closest races, the elections before and after
    elections/<election_id>/contests/       every contest on that ballot, by level of government (primaries by
                                            party first), each linked to its office's Elections tab
    elections/<election_id>/map/            "How areas voted" for this election's races (only elections with
                                            precinct results: civic/map.py election_vote_map)
    elections/<election_id>/sources/        citations and gaps
    elections/compare/                      Compare: close races, turnout, uncontested seats and overview (three
                                            real-URL tabs; pages/elections_numbers.py)

Nothing here computes a figure: contests come from Edition.contests, the map races from derived/map_votes.json
(civic/map.py load_votes, the same file and race rule as map/index.html). The sitemap, the search index and the pages
all read ``election_tabs`` so a tab bar never links to a tab that is not built.
"""
from __future__ import annotations

from . import tabs

HUB = "elections/index.html"
GROUP = "Elections"
COMPARE = "elections/compare/"
# Compare: (key, tab label, site path, short title). The first tab is the folder's own page.
COMPARE_TABS = [
    ("margins", "Close races", "elections/compare/index.html"),
    ("turnout", "Turnout", "elections/compare/turnout/index.html"),
    ("overview", "Uncontested seats and overview", "elections/compare/overview/index.html"),
]
COMPARE_PATH = {k: p for k, _, p in COMPARE_TABS}
# the pages Compare replaced (2026-11-16): each is now a short forwarding page (pages/elections_numbers.py
# build_moved), and tools/site/netlify/_redirects sends the path there with a 301
MOVED_TO = {"elections/margins/index.html": COMPARE_PATH["margins"],
            "elections/turnout/index.html": COMPARE_PATH["turnout"],
            "elections/landscape/index.html": COMPARE_PATH["overview"]}

TYPE_TITLE = {"general": "general election", "primary": "primary election",
              "municipal_general": "municipal general election", "municipal_primary": "municipal primary",
              "special": "special election"}
TYPE_SHORT = {"general": "General", "primary": "Primary", "municipal_general": "Municipal general",
              "municipal_primary": "Municipal primary", "special": "Special"}
PRIMARY_TYPES = ("primary", "municipal_primary")


def base(election_id: str) -> str:
    return f"elections/{election_id}/"


def path(election_id: str, tab: str = "overview") -> str:
    return tabs.tab_path(base(election_id), tab)


def year(e: dict) -> str:
    return (e.get("date") or e["election_id"])[:4]


def title(e: dict) -> str:
    """'2024 general election', '2023 municipal primary', '2013 special election'."""
    return f"{year(e)} {TYPE_TITLE.get(e['type'], e['type'])}"


def sort_key(e: dict):
    """Chronological: by date, and within a year whose rows carry no day (before 2010) the primary first."""
    return (e.get("date") or "", 0 if e["type"] in PRIMARY_TYPES else 1, e["election_id"])


def ordered(ed, newest_first: bool = False) -> list[dict]:
    return sorted(ed.elections.values(), key=sort_key, reverse=newest_first)


def contests(ed, election_id: str) -> list[dict]:
    """Every contest of one election, in results.csv order (the canvass's own order)."""
    cache = ed.__dict__.setdefault("_election_contests", None)
    if cache is None:
        cache = {}
        for c in ed.contests.values():
            cache.setdefault(c["election_id"], []).append(c)
        ed.__dict__["_election_contests"] = cache
    return list(cache.get(election_id, []))


def _votes(ed):
    """derived/map_votes.json when the map draws precincts (the same rule as map/index.html), else None."""
    if "_election_votes" not in ed.__dict__:
        from .map import load_shapes, load_votes
        shapes = load_shapes(ed)
        ed.__dict__["_election_votes"] = (load_votes(ed) if shapes and "precinct" in shapes.get("layers", {})
                                          else None)
    return ed.__dict__["_election_votes"]


def map_races(ed, election_id: str) -> list[dict]:
    """The races of one election on the map's "How areas voted" layer, in the map file's order."""
    v = _votes(ed)
    return [r for r in (v or {}).get("races", []) if r.get("eid") == election_id]


def election_tabs(ed, election_id: str) -> list[str]:
    """Overview and Sources always; Contests when results.csv has a contest; Map when the map has its races."""
    cache = ed.__dict__.setdefault("_election_tabs", {})
    if election_id in cache:
        return cache[election_id]
    keys = ["overview"]
    if contests(ed, election_id):
        keys.append("contests")
    if map_races(ed, election_id):
        keys.append("map")
    keys.append("sources")
    cache[election_id] = tabs.ordered(keys)
    return cache[election_id]


def crumb(ed, e: dict) -> list:
    return [("Elections", HUB), (title(e)[:1].upper() + title(e)[1:], None)]


def election_entries(ed) -> list:
    """Sitemap entries: every election's tabs, newest first, then the three Compare tabs."""
    from .sitemap import Entry
    out = []
    for e in ordered(ed, newest_first=True):
        eid = e["election_id"]
        keys = election_tabs(ed, eid)
        t = title(e)
        T = t[:1].upper() + t[1:]
        desc = {"overview": f"{T}: the date, turnout with the number of registered voters, how many contests were on "
                            "the ballot, how many had no contest and the closest races.",
                "contests": f"{T}: every contest on the ballot in the guide's results, by level of government, each "
                            "with the winner, the share, the margin and its status.",
                "map": f"{T}: how areas voted in this election's races, by township, city or town and precinct.",
                "sources": f"{T}: every source behind these pages, and what the guide has not found."}
        out += tabs.tab_entries(base(eid), T, desc["overview"], keys, group=GROUP, crumb=crumb(ed, e),
                                tab_descriptions=desc)
    sections = {
        "margins": [("short-answer", "The short answer"), ("by-level", "By level of government"),
                    ("find", "Find a race"), ("all-races", "All races as a table")],
        "turnout": [("turnout", "Turnout: odd vs even years"), ("straight-party", "Straight-party ballots")],
        "overview": [("turnout", "Turnout"), ("margins", "How close were the races?"), ("up-next", "Up next"),
                     ("how-took-office", "How officeholders first took office")],
    }
    descs = {
        "margins": "Every race decided inside the county since 2010: how many had no contest, how close the others "
                   "were, by level of government and on a map.",
        "turnout": "Turnout in every election since 2010 with its denominator, odd and even years, and straight-party "
                   "ballots.",
        "overview": "Four measures for every race and every party, looking back: how many seats had no contest, how "
                    "close races were, turnout, the seats on the next ballots and how officeholders first took office.",
    }
    for key, label, p in COMPARE_TABS:
        page_title = "Compare elections" if key == "margins" else f"Compare elections: {label.lower()}"
        nav = "Compare" if key == "margins" else label
        out.append(Entry(p, page_title, nav, descs[key], "county", GROUP, list(sections[key])))
    return out


def href(page, election_id: str, tab: str = "overview") -> str | None:
    """Relative link from ``page`` to an election tab, or None when that page is not in this build."""
    if not election_id or election_id not in page.ed.elections:
        return None
    p = path(election_id, tab)
    return page.rel(p) if p in page.site.by_path else None


def contest_anchor(contest_id: str) -> str:
    return f"contest-{contest_id}"


def contest_href(page, contest_id: str) -> str | None:
    """One contest on its election's Contests tab (elections/<id>/contests/#contest-<contest id>), or None."""
    c = page.ed.contests.get(contest_id)
    if not c:
        return None
    u = href(page, c["election_id"], "contests")
    return f"{u}#{contest_anchor(contest_id)}" if u else None


def neighbours(ed, election_id: str) -> dict:
    """The elections before and after this one (any kind), and the previous and next of the same kind."""
    els = ordered(ed)
    i = next(k for k, e in enumerate(els) if e["election_id"] == election_id)
    e = els[i]
    same = [x for x in els if x["type"] == e["type"]]
    j = next(k for k, x in enumerate(same) if x["election_id"] == election_id)
    return {"before": els[i - 1] if i else None, "after": els[i + 1] if i + 1 < len(els) else None,
            "same_before": same[j - 1] if j else None, "same_after": same[j + 1] if j + 1 < len(same) else None}
