"""Which result lines of an election are official, and why the others are not (gap-fill round 2, 2026-11-18).

The 2026 general election became mostly official with the county canvass of 11/13/2026; the rest stays unofficial for
reasons the results.csv notes state (the recount window, a school corporation that also votes in another county, a
contest whose result awaits state certification). Pages used to hard-code "2026 is unofficial"; they now call these
helpers, so the wording follows the rows' own status.

Words: a county canvass is "official"; figures the state portal publishes are "official results as reported to the
Secretary of State" (STATE_PHRASE), never "certified" (the guide has no certification record for them).
"""
from __future__ import annotations

import re

from .data import fmt_date

STATE_PHRASE = "official results as reported to the Secretary of State"

# (key, words, test on a row's notes), in order: the first that matches gives the reason (a recount note also says
# the district result awaits state certification; the recount is the nearer step)
REASONS = (
    ("recount", "the recount window is still open", re.compile(r"recount", re.I)),
    ("other-county", "the school corporation also votes in another county, so the corporation-wide result is not in "
                     "the county canvass", re.compile(r"another county|other count(y|ies) (also )?vote", re.I)),
    ("state", "the contest result awaits state certification", re.compile(r"state certification|certif", re.I)),
)
OTHER_REASON = ("other", "the source marks the figures unofficial")
REASON_WORDS = dict((k, w) for k, w, _ in REASONS) | {OTHER_REASON[0]: OTHER_REASON[1]}
_CANVASS = re.compile(r"official county canvass of (\d{1,2})/(\d{1,2})/(\d{4})", re.I)


def _rows(ed, election_id: str) -> list[dict]:
    return [r for r in ed.tables.get("results", []) if r.get("election_id") == election_id]


def canvass_date(ed, election_id: str) -> str | None:
    """ISO date of the official county canvass the election's rows cite ("official county canvass of 11/13/2026"), or
    None when no row names one. The most frequent date wins (one canvass per election)."""
    seen: dict[str, int] = {}
    for r in _rows(ed, election_id):
        m = _CANVASS.search(r.get("notes") or "")
        if m:
            iso = f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
            seen[iso] = seen.get(iso, 0) + 1
    return max(seen, key=lambda k: (seen[k], k)) if seen else None


def row_reason(row: dict) -> str:
    """The reason key for one unofficial row (REASONS order), else "other"."""
    notes = row.get("notes") or ""
    for key, _w, rx in REASONS:
        if rx.search(notes):
            return key
    return OTHER_REASON[0]


def contest_reason(c: dict) -> str:
    """The reason key for an unofficial contest: the first REASONS key any of its unofficial rows gives."""
    keys = {row_reason(r) for r in c.get("rows", []) if (r.get("status") or "") == "unofficial"}
    for key, _w, _rx in REASONS:
        if key in keys:
            return key
    return OTHER_REASON[0] if keys else ""


def split(ed, election_id: str) -> dict:
    """{total, official, unofficial, other (rows of any other status), canvass (ISO or None), date (election date),
    by_reason: {key: {"rows": n, "contests": [contest dict, ...]}}} for one election's results rows."""
    rows = _rows(ed, election_id)
    out = {"total": len(rows), "official": 0, "unofficial": 0, "other": 0, "canvass": canvass_date(ed, election_id),
           "date": (ed.elections.get(election_id) or {}).get("date", ""), "by_reason": {}}
    for r in rows:
        st = (r.get("status") or "").strip()
        if st == "official":
            out["official"] += 1
        elif st == "unofficial":
            out["unofficial"] += 1
            key = row_reason(r)
            slot = out["by_reason"].setdefault(key, {"rows": 0, "contests": []})
            slot["rows"] += 1
            c = ed.contests.get(r["contest_id"])
            if c is not None and all(c is not x for x in slot["contests"]):
                slot["contests"].append(c)
        else:
            out["other"] += 1
    return out


def _canvass_words(iso: str | None) -> str:
    return f"the official county canvass of {fmt_date(iso, long=True)}" if iso else "the official county canvass"


def _official_paren(iso: str | None) -> str:
    """" (the official county canvass of November 13, 2026)" when the rows name the canvass, else nothing (an
    election whose rows cite other official records)."""
    return f" ({_canvass_words(iso)})" if iso else ""


def _reason_bits(by_reason: dict, name_limit: int = 3) -> list[str]:
    bits = []
    for key in [k for k, _w, _r in REASONS] + [OTHER_REASON[0]]:
        slot = by_reason.get(key)
        if not slot:
            continue
        n, cs = slot["rows"], slot["contests"]
        names = ""
        if cs and len(cs) <= name_limit:
            names = " (" + "; ".join(c["label"] for c in cs) + ")"
        bits.append(f"{n} line{'s' if n != 1 else ''} in {len(cs)} contest{'s' if len(cs) != 1 else ''} because "
                    f"{REASON_WORDS[key]}{names}")
    return bits


def summary(ed, election_id: str) -> str:
    """One or two sentences on the election's status, from its rows. Empty when it has no results rows."""
    s = split(ed, election_id)
    if not s["total"]:
        return ""
    when = fmt_date(s["date"]) if s["date"] else election_id
    if s["unofficial"] == 0 and s["other"] == 0:
        return f"Every result line of the {when} election is official{_official_paren(s['canvass'])}."
    if s["official"] == 0:
        head = f"The {when} results in the guide are unofficial"
        bits = _reason_bits(s["by_reason"])
        return head + (": " + "; ".join(bits) + "." if bits else ".")
    text = (f"{s['official']:,} of the {s['total']:,} result lines of the {when} election "
            f"{'is' if s['official'] == 1 else 'are'} official{_official_paren(s['canvass'])}.")
    if s["unofficial"]:
        text += f" {s['unofficial']:,} stay unofficial: " + "; ".join(_reason_bits(s["by_reason"])) + "."
    if s["other"]:
        text += f" {s['other']:,} carry another status mark (shown beside them)."
    return text


def incoming_note(ed, office_ids, election_id: str = "2026g") -> str | None:
    """The sentence under "who holds office" about people elected at `election_id` who take office later, driven by
    their terms' status. None when no office has an incoming term."""
    inc = [t for oid in office_ids for t in ed.incoming_terms(oid)]
    if not inc:
        return None
    e = ed.elections.get(election_id) or {}
    when = fmt_date(e.get("date", ""), long=False) if e.get("date") else "the last election"
    starts = sorted({t.get("start") or "" for t in inc})
    take = (f"they take office {fmt_date(starts[0])}" if len(starts) == 1 and starts[0].count("-") == 2
            else "each takes office on the date shown")
    n = len(inc)
    head = f"{n} {'people' if n != 1 else 'person'} elected on {when} {'are' if n != 1 else 'is'} shown as incoming; {take}."
    unoff = [t for t in inc if (t.get("status") or "") == "unofficial"]
    iso = canvass_date(ed, election_id)
    if not unoff:
        return head + f" {'Their results are' if n != 1 else 'The result is'} official{_official_paren(iso)}."
    keys: list[str] = []
    for t in unoff:
        k = _term_reason(ed, t, election_id)
        if k not in keys:
            keys.append(k)
    why = "; ".join(REASON_WORDS[k] for k in keys)
    k = len(unoff)
    if k == n:
        return head + f" {'Their results stay' if n != 1 else 'The result stays'} unofficial ({why})."
    return head + (f" {n - k} of these results {'is' if n - k == 1 else 'are'} official{_official_paren(iso)}; "
                   f"{k} stay{'s' if k == 1 else ''} unofficial, "
                   f"marked beside the name ({why}).")


def _term_reason(ed, term: dict, election_id: str) -> str:
    """The reason an incoming term is unofficial: its office's contest in that election, else the term's own notes."""
    for c in ed.contests.values():
        if c["election_id"] == election_id and c.get("office_id") == term.get("office_id"):
            k = contest_reason(c)
            if k:
                return k
    return row_reason(term)


def brief(ed, election_id: str) -> str:
    """A short status line: "124 of 166 result lines are official (the official county canvass of November 13, 2026);
    42 are still unofficial." Empty when the election has no results rows."""
    s = split(ed, election_id)
    if not s["total"]:
        return ""
    if s["unofficial"] == 0 and s["other"] == 0:
        return f"Every result line is official{_official_paren(s['canvass'])}."
    if s["official"] == 0:
        return "The results in the guide are unofficial."
    out = (f"{s['official']:,} of {s['total']:,} result lines {'is' if s['official'] == 1 else 'are'} "
           f"official{_official_paren(s['canvass'])}")
    if s["unofficial"]:
        out += f"; {s['unofficial']:,} are still unofficial, each marked"
    return out + "."


def office_reason(ed, office_id: str, election_id: str = "2026g") -> str:
    """The reason key why an office's result in `election_id` is unofficial (its contest's notes, else its incoming
    terms' notes); "other" when nothing on file says."""
    for c in ed.contests.values():
        if c["election_id"] == election_id and c.get("office_id") == office_id:
            k = contest_reason(c)
            if k:
                return k
    for t in ed.incoming_terms(office_id):
        if (t.get("status") or "") == "unofficial":
            return row_reason(t)
    return OTHER_REASON[0]
