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
