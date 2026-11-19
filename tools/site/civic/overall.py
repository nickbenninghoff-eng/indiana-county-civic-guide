"""A multi-county contest's St. Joseph County vote beside its overall result (gap-fill round 2, 2026-11-18; owner: "for
offices that are inter-county or state or federal races, show what the vote breakdown was for both just St. Joseph
county and what their overall results were").

Data: overall_results.csv (data/SCHEMA.md), joined to results.csv on (contest_id, candidate). Its ``derived`` column
names the fields that are the guide's arithmetic (share, winner, total): they carry the computed mark. Its ``status``
"official" means official results as reported to the Secretary of State (results_status.STATE_PHRASE), never
"certified".

Every contest gets one basis (``info``):

    local     not multi-county: the county result is the result (nothing extra is shown)
    wholly    a legislative district that lies entirely in the county, as the data establishes it: its own rows'
              notes say so, or another contest of the same chamber, district and district plan says so and no
              contest of that plan has an overall row (the 2010 contests, on the plan before 2011, are never inferred)
    overall   overall rows exist: two columns, "St. Joseph County" and "Whole district" / "Statewide" /
              "Whole school corporation"; the winner shown is the overall winner
    pending   multi-county, no overall row, a 2026 general contest: "Overall result awaits state reporting"
    missing   multi-county, no overall row: "Overall result not in the guide yet"

A county leader who is not the overall winner is described as having "received the most votes in St. Joseph County",
never as the winner. Party appears only as the display tag beside a name; no party colors (accent and ink bars).
"""
from __future__ import annotations

import re

from .components import name_with_party, status_badge
from .html import Markup, h, join

CROSS_SCHOOLS = ("john-glenn-schools", "union-north-schools", "laville-schools", "new-prairie-schools")
WHOLLY_NOTE = re.compile(r"district lies wholly in the county|no other county reports votes in this district"
                         r"|St\. Joseph County voters only", re.I)
OTHER_COUNTY_NOTE = re.compile(r"also votes in another county|multi-county question|(LaPorte|Marshall|Starke|Elkhart) "
                               r"County also voted", re.I)
COMPUTED_WORDS = "share of votes for the candidates listed in the state's results; computed"
PENDING_ELECTION = "2026g"
LABELS = {"statewide": "Statewide", "district": "Whole district", "school": "Whole school corporation",
          "appellate": "Whole appellate district", "other": "Whole electorate"}
WHOLLY_SENTENCE = "This district lies entirely in St. Joseph County, so the county result is the full result."
PENDING_SENTENCE = "Overall result awaits state reporting."
MISSING_SENTENCE = "Overall result not in the guide yet."


def _num(v):
    try:
        return float(v) if (v or "").strip() != "" else None
    except (TypeError, ValueError):
        return None


def _rest(c) -> str:
    cid, eid = c["contest_id"], c["election_id"]
    rest = cid[len(eid) + 1:] if cid.startswith(eid + "-") else cid
    if c.get("party_primary") and re.search(r"-[a-z]$", rest):
        rest = rest[:-2]
    return rest


def by_contest(ed) -> dict[str, list[dict]]:
    """{contest_id: overall rows} (cached on the edition). A row whose contest is not in results.csv is skipped with
    a data warning (tools/check_results.py rejects it too)."""
    got = ed.__dict__.get("_overall_by_contest")
    if got is not None:
        return got
    out: dict[str, list[dict]] = {}
    for r in ed.tables.get("overall_results", []):
        cid = (r.get("contest_id") or "").strip()
        if cid not in ed.contests:
            ed.warnings.append(f"overall_results: {cid} is not a contest in results.csv; not shown")
            continue
        out.setdefault(cid, []).append(r)
    ed.__dict__["_overall_by_contest"] = out
    return out


def _legislative_key(c):
    """(chamber, district, plan) of a state legislative contest, else None. Plans: 2001 (contests to 2011), 2011
    (2012-2020), 2021 (2022 on)."""
    m = re.match(r"state-(house|senate)-(\d+)$", _rest(c))
    if not m:
        return None
    y = int(c["election_id"][:4])
    plan = "2001" if y <= 2011 else "2011" if y <= 2021 else "2021"
    return (m.group(1), m.group(2), plan)


def _wholly_keys(ed) -> tuple[set, set]:
    """(keys with a contest whose own rows say the district lies wholly in the county, keys with any overall row)."""
    got = ed.__dict__.get("_overall_wholly_keys")
    if got is not None:
        return got
    noted, with_overall = set(), set()
    ov = by_contest(ed)
    for c in ed.contests.values():
        k = _legislative_key(c)
        if k is None:
            continue
        if c["rows"] and all(WHOLLY_NOTE.search(r.get("notes") or "") for r in c["rows"]):
            noted.add(k)
        if c["contest_id"] in ov:
            with_overall.add(k)
    ed.__dict__["_overall_wholly_keys"] = (noted, with_overall)
    return noted, with_overall


def is_wholly(ed, c) -> bool:
    """True when the data establishes that the contest's electorate lies entirely in the county (module docstring)."""
    if c["contest_id"] in by_contest(ed):
        return False
    if c["rows"] and all(WHOLLY_NOTE.search(r.get("notes") or "") for r in c["rows"]):
        return True
    k = _legislative_key(c)
    if k is None or k[2] == "2001":
        return False
    noted, with_overall = _wholly_keys(ed)
    return k in noted and k not in with_overall


def is_multi_county(ed, c) -> bool:
    """A contest whose voters are not only this county's: statewide, federal, appellate and legislative contests (the
    results explorer's classify() "crosses the county line"), cross-county school corporations, a question the notes
    say other counties voted on, and any contest with an overall row."""
    if c["contest_id"] in by_contest(ed):
        return True
    from pages.elections import classify
    if classify(c)[2]:
        return True
    rest = _rest(c)
    if rest.startswith(CROSS_SCHOOLS):
        return True
    return any(OTHER_COUNTY_NOTE.search(r.get("notes") or "") for r in c["rows"])


def _label(c, rows) -> str:
    rest = _rest(c)
    el = " ".join((r.get("electorate") or "") for r in rows).lower()
    if rest.startswith(CROSS_SCHOOLS) or "school" in el or "sch corp" in el:
        return LABELS["school"]
    if el.startswith("statewide") or "statewide" in el:
        return LABELS["statewide"]
    if "district" in el and rest.startswith("state-retention"):
        return LABELS["appellate"]
    if "district" in el or rest.startswith(("state-house", "state-senate", "us-house")):
        return LABELS["district"]
    if re.search(r"(allen|lake|marshall|laporte).*,", el):
        return LABELS["district"]
    return LABELS["other"]


def info(ed, c) -> dict:
    """The contest's basis and, for "overall", the joined rows (module docstring)."""
    rows = by_contest(ed).get(c["contest_id"], [])
    if rows:
        derived = set()
        for r in rows:
            derived |= {x.strip() for x in (r.get("derived") or "").split(";") if x.strip()}
        winners = [r["candidate"] for r in rows if (r.get("overall_winner") or "").strip().upper() == "Y"]
        sids = []
        for r in rows:
            for s in (r.get("source_ids") or "").split(";"):
                if s.strip() and s.strip() not in sids:
                    sids.append(s.strip())
        notes = []
        for r in rows:
            n = (r.get("notes") or "").strip()
            if n and n not in notes:
                notes.append(n)
        return {"basis": "overall", "rows": rows, "by": {r["candidate"]: r for r in rows}, "winners": winners,
                "label": _label(c, rows), "electorate": (rows[0].get("electorate") or "").strip(),
                "derived": derived, "source_ids": ";".join(sids), "notes": notes,
                "total": _num(rows[0].get("overall_total_votes"))}
    if is_wholly(ed, c):
        return {"basis": "wholly"}
    if not is_multi_county(ed, c):
        return {"basis": "local"}
    return {"basis": "pending" if c["election_id"] == PENDING_ELECTION else "missing", "label": _label(c, [])}


def county_leaders(c) -> list[str]:
    """The candidates with the most votes in the county's tally, as many as there are seats (named candidates only)."""
    from pages.elections import candidates, is_writein_total
    named = [x for x in candidates(c) if not is_writein_total(x["row"]) and x["votes"] is not None]
    n = int(c["vote_for"]) if (c.get("vote_for") or "").isdigit() else 1
    ranked = sorted(named, key=lambda x: -x["votes"])
    if len(ranked) > n and ranked[n - 1]["votes"] == ranked[n]["votes"]:
        return []   # a tie at the edge: no leader is named
    return [x["row"]["candidate"] for x in ranked[:n]]


def leaders_differ(ed, c, inf: dict | None = None) -> bool:
    inf = inf or info(ed, c)
    if inf["basis"] != "overall" or not inf["winners"]:
        return False
    return set(county_leaders(c)) != set(inf["winners"])


def overall_margin(ed, c) -> dict | None:
    """The contest margin computed on the overall votes (same rule as pages/elections.py margin(): the last candidate
    inside the seats against the next, over every vote listed), or None when the contest has no overall row, too few
    candidates, or a missing figure."""
    inf = info(ed, c)
    if inf["basis"] != "overall":
        return None
    from pages.elections import BANDS, is_writein_total
    rows = [r for r in inf["rows"] if not is_writein_total({"candidate": r["candidate"]})]
    n = int(c["vote_for"]) if (c.get("vote_for") or "").isdigit() else (1 if len(rows) > 1 else None)
    vals = [(r, _num(r.get("overall_votes"))) for r in rows]
    if n is None or len(vals) <= n or any(v is None for _r, v in vals):
        return None
    total = inf["total"] or sum(v for _r, v in vals)
    if not total:
        return None
    ranked = sorted(vals, key=lambda t: -t[1])
    (a, av), (b, bv) = ranked[n - 1], ranked[n]
    pts = 100.0 * (av - bv) / total
    band = next(bid for bid, _, lo, hi in BANDS if lo <= pts < hi)
    return {"pts": pts, "votes": int(av - bv), "seats": n, "band": band, "tie": av == bv, "total": int(total),
            "ahead": {"name": a["candidate"], "party": a.get("party", ""), "votes": int(av), "winner": "Y" if a.get("overall_winner") == "Y" else ""},
            "next": {"name": b["candidate"], "party": b.get("party", ""), "votes": int(bv), "winner": ""},
            "low": False, "writein": False, "basis": "overall"}


# ------------------------------------------------------------------ rendering

def basis_sentence(ed, c, inf: dict | None = None) -> str | None:
    inf = inf or info(ed, c)
    return {"wholly": WHOLLY_SENTENCE, "pending": PENDING_SENTENCE, "missing": MISSING_SENTENCE}.get(inf["basis"])


def _computed(page, field: str, inf: dict):
    if field in inf.get("derived", set()):
        return status_badge("computed", page, COMPUTED_WORDS.capitalize() + ".")
    return None


def winner_words(ed, c, inf: dict | None = None) -> list:
    """'Won: Name (P), the overall result (statewide).' plus, when the county's leader differs, 'Name (P) received
    the most votes in St. Joseph County.' (plain parts for an h() call; the party tag is display-only)."""
    inf = inf or info(ed, c)
    if inf["basis"] != "overall":
        return []
    from pages.elections import is_question
    q = is_question(c)
    county = ed.county_label
    out = []
    win = inf["winners"]
    if win:
        who = join([(w.title() if q else name_with_party(w, (inf["by"][w].get("party") or "")))
                    for w in win], ", ")
        out += [h("strong", None, "Overall: " if q else "Won: "), who, f" ({inf['label'].lower()})"]
    lead = county_leaders(c)
    if lead and win and set(lead) != set(win):
        by_name = {r["candidate"]: r for r in c["rows"]}
        names = join([(x.title() if q else name_with_party(x, by_name.get(x, {}).get("party", ""))) for x in lead],
                     ", ")
        out += [". ", names, f" received the most votes in {county}" if not q else f" received more votes in {county}"]
    return out


def cvo_figure(page, c, fid: str | None = None) -> Markup | None:
    """The county vote beside the overall result, one row per candidate (county ballot order, then any candidate
    only the state lists): votes and share in St. Joseph County, votes and share overall, with a bar for each share
    (accent for the county, ink for the overall; never party colors). The winner is the overall winner. None when
    the contest has no overall row."""
    from pages.elections import candidates, is_question
    ed = page.ed
    inf = info(ed, c)
    if inf["basis"] != "overall":
        return None
    q = is_question(c)
    county = ed.county_label
    cands = candidates(c)
    seen = set()
    rows = []
    for x in cands:
        name = x["row"]["candidate"]
        seen.add(name)
        rows.append((name, x["party"], x, inf["by"].get(name)))
    for r in inf["rows"]:
        if r["candidate"] not in seen:
            rows.append((r["candidate"], r.get("party", ""), None, r))
    body = []
    for name, party, cx, orow in rows:
        disp = name.title() if q else None
        who = disp or name_with_party(name, party)
        won = orow is not None and (orow.get("overall_winner") or "").upper() == "Y"
        c_cell = (h("span", {"class": "cvo-v"},
                    h("span", {"class": "cvo-bar cvo-bar-c", "style": f"--w: {min(cx['pct'], 100):.1f}%",
                               "aria-hidden": "true"}) if cx and cx["pct"] is not None else None,
                    f"{cx['votes']:,}" if cx and cx["votes"] is not None else "not recorded",
                    f" · {cx['pct']:.1f}%" if cx and cx["pct"] is not None else "")
                  if cx else h("span", {"class": "muted"}, "not on the county's ballot lines"))
        if orow is not None:
            pct = _num(orow.get("overall_pct"))
            v = _num(orow.get("overall_votes"))
            o_cell = h("span", {"class": "cvo-v"},
                       h("span", {"class": "cvo-bar cvo-bar-o", "style": f"--w: {min(pct, 100):.1f}%",
                                  "aria-hidden": "true"}) if pct is not None else None,
                       f"{int(v):,}" if v is not None else "not recorded",
                       [f" · {pct:.1f}%", _computed(page, "overall_pct", inf)] if pct is not None else None,
                       [" ", h("strong", {"class": "cvo-won"}, "Won" if not q else "Majority"),
                        _computed(page, "overall_winner", inf)] if won else None)
        else:
            o_cell = h("span", {"class": "muted"}, "not in the state's results")
        body.append(h("tr", None, h("th", {"scope": "row"}, who), h("td", None, c_cell), h("td", None, o_cell)))
    total = inf["total"]
    foot = [h("p", {"class": "cvo-note"}, winner_words(ed, c, inf), "." if inf["winners"] else None)
            if inf["winners"] else None]
    foot.append(h("p", {"class": "cvo-note muted"},
                  _electorate_words(inf),
                  f"Overall figures are official results as reported to the Secretary of State"
                  + (f"; {int(total):,} votes for the candidates the state lists" if total else "") + ".",
                  _computed(page, "overall_total_votes", inf) if total else None,
                  " The overall comes from a different record than the county canvass, so it need not contain "
                  "exactly the county figure shown.", page.cites.cite(inf["source_ids"])))
    notes = [n for n in inf["notes"] if not n.startswith("Official results as reported to the Secretary of State")]
    if notes:
        foot.append(h("p", {"class": "cvo-note muted"}, "Notes: ", " ".join(notes[:3])))
    fid = fid or f"cvo-{c['contest_id']}"
    return h("figure", {"class": "cvo", "id": fid},
             h("figcaption", {"class": "cvo-cap"}, f"{c['label']}: {county} and {inf['label'].lower()}"),
             h("div", {"class": "cvo-scroll"},
               h("table", {"class": "cvo-table"},
                 h("thead", None, h("tr", None, h("th", {"scope": "col"}, "Option" if q else "Candidate"),
                                    h("th", {"scope": "col"}, county),
                                    h("th", {"scope": "col"}, inf["label"]))),
                 h("tbody", None, body))),
             foot)


def basis_note(page, c) -> Markup | None:
    """The one line for a contest with no overall figure: wholly in the county, awaiting state reporting, or not in
    the guide yet (then the county figure is labelled "St. Joseph County portion")."""
    ed = page.ed
    inf = info(ed, c)
    s = basis_sentence(ed, c, inf)
    if not s:
        return None
    if inf["basis"] in ("pending", "missing"):
        return h("p", {"class": "cvo-basis"}, h("strong", None, f"{ed.county_label} portion. "), s,
                 " The figures above are only this county's part of the vote.")
    return h("p", {"class": "cvo-basis"}, s)


def portion_label(ed, c) -> str:
    """The title words for a county figure: "St. Joseph County portion" when the contest is multi-county with no
    overall row or with one (its full result is elsewhere), else ""."""
    inf = info(ed, c)
    return f"{ed.county_label} portion" if inf["basis"] in ("overall", "pending", "missing") else ""


def question_statewide(ed, c) -> str | None:
    """'Statewide: Yes (ratified)' for a statewide question with overall rows: the notes' own words when they say
    it, else the overall majority."""
    inf = info(ed, c)
    if inf["basis"] != "overall":
        return None
    for n in inf["notes"]:
        m = re.search(r"Statewide: (Yes|No)(?: \(([^)]+)\))?", n)
        if m:
            return f"Statewide: {m.group(1)}" + (f" ({m.group(2)})" if m.group(2) else "")
    if inf["winners"]:
        return f"{inf['label']}: {inf['winners'][0].title()}"
    return None


def figure_title(ed, c, title: str | None = None) -> str:
    """A county results chart's title: the contest label, plus ": St. Joseph County portion" for a multi-county
    contest (never a county portion that looks like the full result)."""
    t = title or c["label"]
    p = portion_label(ed, c)
    return f"{t}: {p}" if p else t


def clear_county_winner(ed, c) -> bool:
    """True when the county chart must mark no winner: the contest has an overall result, whose winner is shown in
    the county-vs-overall table instead."""
    return info(ed, c)["basis"] == "overall"


def _electorate_words(inf: dict) -> str:
    """'Whole school corporation: NEW PRAIRIE ... (counties: ...). ' as stored; an electorate that only repeats the
    label ('Statewide: statewide (all counties)') is said once: 'Statewide (all counties). '"""
    el = inf["electorate"]
    if not el:
        return ""
    if el.lower().startswith(inf["label"].lower()):
        return f"{inf['label']}{el[len(inf['label']):]}. "
    return f"{inf['label']}: {el}. "


def after_figure(page, c) -> Markup:
    """What follows a contest's county chart: the county-vs-overall table, or the one basis line; empty for a local
    contest. The wholly-in-county sentence is said once per page and district (an office's Elections tab lists the
    same district many times; an election page says it once for each district)."""
    got = cvo_figure(page, c)
    if got is None:
        inf = info(page.ed, c)
        if inf["basis"] == "wholly":
            k = _legislative_key(c) or (c["contest_id"],)
            said = page.__dict__.setdefault("_overall_wholly_said", set())
            if k[:2] in said:
                return Markup("")
            said.add(k[:2])
        got = basis_note(page, c)
    return got if got is not None else Markup("")


def with_overall(page, c, fig) -> Markup:
    """The county chart followed by after_figure (one Markup, so callers can drop it where the chart went)."""
    return Markup(str(fig) + str(after_figure(page, c)))


def result_words(ed, c) -> list | None:
    """The one-line result for a multi-county contest (election and office rows): the overall winner with the
    overall share, and the county leader when different; or the basis words when there is no overall figure.
    None for a local contest (the caller's own words)."""
    from pages.elections import is_question
    inf = info(ed, c)
    county = ed.county_label
    if inf["basis"] == "overall":
        q = is_question(c)
        if not inf["winners"]:
            return [h("span", {"class": "muted"}, "Overall winner not in the guide's data")]
        bits = []
        for w in inf["winners"]:
            r = inf["by"][w]
            pct = _num(r.get("overall_pct"))
            bits.append(h("span", {"class": "er-win"}, w.title() if q else name_with_party(w, r.get("party", "")),
                          f" {pct:.1f}%" if pct is not None else ""))
        out = [h("span", {"class": "ep-out"}, f"{inf['label']}: "), join(bits, ", ")]
        lead = county_leaders(c)
        if lead and set(lead) != set(inf["winners"]):
            by_name = {r["candidate"]: r for r in c["rows"]}
            out += [h("span", {"class": "cvo-lead"}, f" · most votes in {county}: ",
                      join([x.title() if q else name_with_party(x, by_name.get(x, {}).get("party", "")) for x in lead],
                           ", "))]
        return out
    if inf["basis"] in ("pending", "missing"):
        return [h("span", {"class": "ep-out"}, f"{county} portion only. "),
                h("span", {"class": "muted"}, PENDING_SENTENCE if inf["basis"] == "pending" else MISSING_SENTENCE)]
    return None


def margin_words(ed, c) -> str | None:
    """Margin words for a multi-county contest: the overall margin (and its basis), "County portion only" when
    there is no overall figure; None for a local or wholly-in-county contest."""
    inf = info(ed, c)
    if inf["basis"] == "overall":
        m = overall_margin(ed, c)
        if m is None:
            return "Overall margin not measured"
        if m["tie"]:
            return "Tied on overall votes"
        return f"Margin {m['pts']:.1f} points ({inf['label'].lower()})"
    if inf["basis"] in ("pending", "missing"):
        return "County portion only"
    return None
