"""Compact officeholder rows: one line per office (office, holder with party, since, next election) that opens to
the same fields as civic/components.py officeholder_card. Used on county/ in place of 33 cards in a row.

    holder_row(ed, page, office, current, incoming, note=None) -> <details data-one=office_id id="office-<id>">
    holder_state(ed, office, current, incoming) -> dict (the plain-text words the row and the map panel share)

The row is a static/js/pick_one.js item (civic/pick_one.py one_fold): it ships open, so with JavaScript off every
holder's full fields are on the page; folds.js closes the rows on load and the district map opens one. The row keeps
the card's id (office-<office_id>), so old links still land on it.
"""
from __future__ import annotations

from .components import _holder, name_party_text, name_with_party, term_party
from .data import SELECTED_BY_LABELS, fmt_date
from .html import Markup, h, join
from .pick_one import one_fold

NO_HOLDER = "No current officeholder in the guide's data"


def holder_state(ed, office: dict, current: list[dict], incoming: list[dict]) -> dict:
    """now: 'Name (D)' list or NO_HOLDER; since; how (first chosen, when not by election); incoming: the 2026 line."""
    now = ", ".join(name_party_text(t["person"], term_party(t), t.get("confidence") if term_party(t) else None)
                    for t in current) or NO_HOLDER
    since = ", ".join(fmt_date(t["start"]) or "start date not in sources" for t in current)
    # the summary names only an unusual way in (a caucus or an appointment); the opened row shows every holder's
    hows = sorted({t.get("first_selected_by") or "" for t in current} - {"election", "", "unknown"})
    how = "; ".join(SELECTED_BY_LABELS.get(x, x) for x in hows)
    inc = ""
    if incoming:
        same = {t["person"] for t in current} == {t["person"] for t in incoming}
        starts = sorted({fmt_date(t["start"]) for t in incoming if t.get("start")})
        unoff = any(t.get("status") == "unofficial" for t in incoming)
        if same:
            inc = "Re-elected" + (" (results unofficial)" if unoff else "") + (f"; new term from {starts[0]}" if starts else "")
        else:
            names = ", ".join(name_party_text(t["person"], term_party(t)) for t in incoming)
            inc = f"Incoming{' ' + starts[0] if starts else ''}: {names}" + (" (results unofficial)" if unoff else "")
    return {"now": now, "since": since, "how": how, "incoming": inc, "vacant": not current}


def holder_row(ed, page, office: dict, current: list[dict], incoming: list[dict], note=None,
               title: str | None = None) -> Markup:
    st = holder_state(ed, office, current, incoming)
    title = title or office["title"]
    if current:
        who = join([name_with_party(t["person"], term_party(t), t.get("confidence") if term_party(t) else None)
                    for t in current], ", ")
    else:
        who = h("span", {"class": "hr-vacant"}, NO_HOLDER)
    meta = []
    if st["since"]:
        meta.append(f"Since {st['since']}")
    if st["how"]:
        meta.append(f"first chosen by {st['how']}")
    if office.get("next_election"):
        meta.append(f"next election {office['next_election']}")
    summary = [h("h4", {"class": "one-h hr-office"}, title),
               h("span", {"class": "hr-who"}, who),
               h("span", {"class": "hr-meta"}, "; ".join(meta)[:1].upper() + "; ".join(meta)[1:] if meta else None,
                 h("span", {"class": "hr-inc"}, st["incoming"]) if st["incoming"] else None)]
    body = []
    if title != office["title"]:
        body.append(h("p", {"class": "hr-term muted"}, f"Office as listed: {office['title']}."))
    if not current:
        body.append(h("p", {"class": "holder holder-none"}, NO_HOLDER + "."))
    body += [_holder(ed, page, t, kind="current") for t in current]
    body += [_holder(ed, page, t, kind="incoming") for t in incoming]
    terms = f"{office['term_years']}-year term" if office.get("term_years") else ""
    nxt = f"Next regular election: {office['next_election']}" if office.get("next_election") else ""
    if terms or nxt:
        body.append(h("p", {"class": "hr-term muted"}, "; ".join(x for x in (nxt, terms) if x) + "."))
    if note:
        body.append(h("p", {"class": "card-note"}, note))
    return one_fold(office["office_id"], title, summary, h("div", {"class": "hr-card"}, body),
                    item_id=f"office-{office['office_id']}", cls="holder-row")


# ------------------------------------------------------------------ seat rows (added 2026-11-09, Wave C batch 7)

def term_end_text(ed, current: list[dict]) -> str:
    """'Dec 31, 2028' (or several, comma-separated) for the current holders' terms; '' when no end is known."""
    ends = []
    for t in current:
        e = ed.term_end(t)
        txt = fmt_date(e) if e else ""
        if txt and txt not in ends:
            ends.append(txt)
    return ", ".join(ends)


def seat_row(ed, page, office: dict, current: list[dict], incoming: list[dict], *, title: str, votes: str,
             note=None, extra=None) -> Markup:
    """One board seat as a compact line: seat · who votes · holder (party) · term end, opening to the same fields as
    holder_row. Unlike holder_row it is not a pick_one item (no data-one): it sits inside an area's item (a school
    corporation on schools/), so choosing the corporation opens the list and the seat lines stay one click away.
    The <details> ships open (JavaScript off: everything visible); static/js/folds.js closes it on load and opens it
    when the address or a link points inside it. Keeps the card id office-<office_id>. ``extra`` is appended to the
    opened body (evidence notes, seat links)."""
    st = holder_state(ed, office, current, incoming)
    if current:
        who = join([name_with_party(t["person"], term_party(t), t.get("confidence") if term_party(t) else None)
                    for t in current], ", ")
    else:
        who = h("span", {"class": "hr-vacant"}, NO_HOLDER)
    end = term_end_text(ed, current)
    meta = [f"Term ends {end}" if end else None,
            f"next election {office['next_election']}" if office.get("next_election") else None]
    meta = "; ".join(m for m in meta if m)
    summary = [h("h4", {"class": "one-h hr-office"}, title),
               h("span", {"class": "hr-votes"}, votes),
               h("span", {"class": "hr-who"}, who),
               h("span", {"class": "hr-meta"}, meta[:1].upper() + meta[1:] if meta else None,
                 h("span", {"class": "hr-inc"}, st["incoming"]) if st["incoming"] else None),
               h("span", {"class": "fold-toggle", "aria-hidden": "true"})]
    body = [h("p", {"class": "hr-term muted"}, f"Office as listed: {office['title']}.") if title != office["title"] else None,
            h("p", {"class": "hr-term"}, h("strong", None, "Who votes: "), votes, ".")]
    if not current:
        body.append(h("p", {"class": "holder holder-none"}, NO_HOLDER + "."))
    body += [_holder(ed, page, t, kind="current") for t in current]
    body += [_holder(ed, page, t, kind="incoming") for t in incoming]
    terms = f"{office['term_years']}-year term" if office.get("term_years") else ""
    nxt = f"Next regular election: {office['next_election']}" if office.get("next_election") else ""
    if terms or nxt:
        body.append(h("p", {"class": "hr-term muted"}, "; ".join(x for x in (nxt, terms) if x) + "."))
    if note:
        body.append(h("p", {"class": "card-note"}, note))
    if extra:
        body.append(extra)
    return h("details", {"class": "fold-details one-fold holder-row seat-row", "open": True, "data-fold": "seat",
                         "id": f"office-{office['office_id']}"},
             h("summary", {"class": "fold-summary one-summary"}, summary),
             h("div", {"class": "fold-body one-body"}, h("div", {"class": "hr-card"}, body)))
