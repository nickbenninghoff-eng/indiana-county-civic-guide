"""Reusable page components: badges, citations, gaps, variants, tables, cards.

All take data rows as-is and escape everything. Components that cite sources take the
page's ``Citations`` object (``page.cites``) so the per-page Sources list stays in sync.
"""
from __future__ import annotations

import html as _html
import re

from .data import PARTY_LABELS, SELECTED_BY_LABELS, fmt_date, split_ids
from .html import Markup, esc, h, join

# ----------------------------------------------------------------------- badges

STATUS = {
    "official": ("OFFICIAL", "Certified or official government record."),
    "unofficial": ("UNOFFICIAL", "Not final yet: election-night figures, or a count that awaits a later step (a recount "
                                 "window, another county's figures or state certification); may change."),
    "computed": ("COMPUTED", "The guide's own arithmetic from other sourced figures."),
    "from_scan": ("FROM SCAN", "Transcribed from a scanned image of an official document."),
    "secondary": ("SECONDARY", "A reliable secondary source; no primary record found yet."),
    "single_source": ("SINGLE SOURCE", "Only one secondary source, not yet corroborated."),
    "unverified": ("UNVERIFIED", "Recorded in the guide's configuration but not yet verified against a primary source."),
    "low": ("LOW CONFIDENCE", "Kept for completeness; not used in headings or charts."),
}


def status_badge(status: str, page=None, note: str | None = None) -> Markup:
    """The status of a figure, as the page shows it beside the figure.

    Changed 2026-11-18 (phase 6, "About these figures"; same signature): an official figure is the normal case and gets
    no mark (empty markup); every other known status is one small symbol (``figure_mark``) that links to the page's
    "About these figures" note. An unknown status still shows its word (``status_label``), so nothing is hidden."""
    key = (status or "").strip().lower()
    if key == "official":
        return Markup("")
    if key in FIGURE_MARKS:
        return figure_mark(key, note)
    return status_label(status, page, note)


def status_label(status: str, page=None, note: str | None = None) -> Markup:
    """The status as a word badge (the form status_badge had until 2026-11-18). For the few places where the word
    itself must show: the 2026 UNOFFICIAL banner, a section's top line, the definitions on /about/#badges."""
    key = (status or "").strip().lower()
    label, definition = STATUS.get(key, (key.upper() or "STATUS UNKNOWN", "Status not recorded."))
    title = definition + (f" {note}" if note else "")
    inner = h("span", {"class": f"badge badge-{key or 'none'}", "title": title}, label)
    if page is not None:
        return h("a", {"class": "badge-link", "href": page.rel("about/index.html#badges"),
                       "aria-label": f"{label}: {definition}"}, inner)
    return inner


def status_word(status: str) -> str:
    """The status as plain text ("Official", "Computed", "Incomplete") for a Status column of a table: a column is not
    clutter, and the words keep the table's Copy CSV text readable."""
    key = (status or "").strip().lower()
    if key in STATUS:
        return STATUS[key][0].capitalize()
    if key in FIGURE_MARKS:
        return FIGURE_MARKS[key][1]
    return (status or "").strip() or "Not recorded"


# ----------------------------------------------------------------------- figure marks
# "About these figures" (added 2026-11-18, phase 6; the owner's request of 2026-11-18 and the design direction's
# "Confidence without clutter"). The normal case, a figure that is official and complete, carries no mark. An exception
# carries one small symbol right after the figure: one fixed symbol per kind, the same on every page, for every party,
# candidate and government. Each symbol links to the page's "About these figures" note, which shell.Page.render adds at
# the bottom of the page listing only the symbols that page uses. Where a whole table, chart or section shares one
# status, the section says it once (``scope_line`` + ``scope_attrs``) instead of marking every row.
# kind: (symbol, name, plain-language meaning). The note lists them in this order. (Single source is a triangle, not
# §, because the Ballot & Ink look numbers its sections with §.)
FIGURE_MARKS = {
    "incomplete": ("*", "Incomplete",
                   "at least one expected report is not on file, so this total is a floor (the full amount may be "
                   "higher)."),
    "unofficial": ("†", "Unofficial",
                   "not final yet: election-night figures, or a count that awaits a later step (a recount window, "
                   "another county's figures or state certification); they may change."),
    "secondary": ("‡", "Secondary source",
                  "from a news report or another reliable secondary source; no primary record has been found yet."),
    "single_source": ("△", "Single source",
                      "only one news report or other secondary source gives this; not yet corroborated."),
    "computed": ("‖", "Computed by the guide",
                 "the guide's own arithmetic (a sum, share or conversion) from other sourced figures."),
    "from_scan": ("¶", "From a scan", "transcribed from a scanned image of an official document."),
    "low": ("◊", "Low confidence", "kept for completeness; not used in headings or charts."),
    "unverified": ("?", "Unverified",
                   "recorded in the guide's configuration but not yet checked against a primary source."),
    "unreliable": ("≈", "Unreliable estimate",
                   "the margin of error is large compared with the estimate (coefficient of variation above 30%, "
                   "computed as MOE ÷ 1.645 ÷ estimate), so treat it as unreliable; such estimates are shown in grey "
                   "and never used in headings or charts."),
    "zero_moe": ("°", "No sampling error published",
                 "the Census Bureau controls this total to its official population estimates (county, state and U.S. "
                 "population and Hispanic or Latino origin), or the margin of error rounds to zero."),
}
# A word joiner before every symbol: the symbol never wraps away from its figure, even after a space.
WORD_JOINER = "⁠"


def note_id(kind: str) -> str:
    """The id of a kind's entry in the page's note (letters, digits and hyphens only: fnote-from-scan)."""
    return "fnote-" + kind.replace("_", "-")


def figure_mark(kind: str, note: str | None = None, *, scope: bool = False, link: bool = True) -> Markup:
    """One exception symbol, right after a figure: a link to the page's note (#fnote-<kind>), with the full meaning as
    its accessible name and tooltip (``note`` adds a figure-specific sentence). ``data-word`` is the word Copy CSV
    writes for it (static/app.js), so copied tables keep their status words. ``scope`` marks the symbol of a section's
    caption line (``scope_line``), which stays when the marks of the same kind inside that section are dropped.
    ``link=False`` gives the same symbol as a plain span (role img, same name and tooltip) for a place where a link
    must not go, such as inside a fold's <summary>; the note at the bottom of the page still defines it."""
    sym, name, meaning = FIGURE_MARKS[kind]
    words = f"{name}: {meaning}" + (f" {note}" if note else "")
    word = STATUS[kind][0] if kind in STATUS else name.upper()
    cls = f"fmark fmark-{kind}" + (" fmark-scope" if scope else "")
    if not link:
        return Markup(WORD_JOINER) + h("span", {"class": cls, "data-fmark": kind, "data-word": word, "role": "img",
                                                "title": words, "aria-label": words}, sym)
    return Markup(WORD_JOINER) + h("a", {"class": cls, "data-fmark": kind, "data-word": word,
                                         "href": f"#{note_id(kind)}", "title": words, "aria-label": words}, sym)


def status_symbol(status: str, note: str | None = None) -> Markup:
    """status_badge's mark as a plain span, not a link (inside a <summary>): empty for an official figure."""
    key = (status or "").strip().lower()
    if key == "official":
        return Markup("")
    if key in FIGURE_MARKS:
        return figure_mark(key, note, link=False)
    return status_label(status, None, note)


def status_heading(status: str, page=None, note: str | None = None) -> Markup:
    """The status beside the heading of a section that shows election results: unofficial results say the word there
    ("Unofficial" and the symbol), so they are labelled at the top of their section, not only by a symbol; any other
    status is the plain mark (none when official)."""
    if (status or "").strip().lower() == "unofficial":
        return h("span", {"class": "fword fword-unofficial"}, "Unofficial") + figure_mark("unofficial", note)
    return status_badge(status, page, note)


def scope_mark(status: str, link: bool = True) -> Markup:
    """The mark of a one-line caption that speaks for its whole element (a contest's result line: the chart and table
    below it carry no mark of their own); use with ``scope_attrs(status)`` on that element. Empty when official."""
    key = (status or "").strip().lower()
    if key == "official":
        return Markup("")
    if key in FIGURE_MARKS:
        return figure_mark(key, scope=True, link=link)
    return status_label(status)


def mark_symbol(kind: str) -> Markup:
    """The bare symbol of a kind, for legends that define the marks (not a figure: no link, not counted in the note)."""
    return h("span", {"class": f"fmark-sym fmark-{kind}", "aria-hidden": "true"}, FIGURE_MARKS[kind][0])


def scope_attrs(*kinds: str) -> dict:
    """Attributes for a table, chart or section whose rows all share the statuses ``kinds``: the section's caption line
    (``scope_line``) says it once, and shell.Page.render drops every mark of those kinds inside it (``drop_scoped``),
    so the rows carry no mark of their own."""
    ks = [k for k in FIGURE_MARKS if k in set(kinds)]
    return {"data-fscope": " ".join(ks)} if ks else {}


def scope_line(kinds, text, cls: str = "fscope-line") -> Markup:
    """One short caption line stating the status of a whole table, chart or section once: ``text`` then the marks
    (caption marks, ``scope=True``). Put ``scope_attrs`` on the element the line speaks for (the section, the list
    item); the line goes inside it, or just before it when it speaks for several."""
    ks = [k for k in FIGURE_MARKS if k in set(kinds)]
    return h("p", {"class": cls}, text, [figure_mark(k, scope=True) for k in ks])


_TAG = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9-]*)((?:[^>\"']|\"[^\"]*\"|'[^']*')*)>")
_VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
_SCOPE_ATTR = re.compile(r'\sdata-fscope="([^"]*)"')
_MARK_OPEN = re.compile(r'^\s+class="fmark fmark-([a-z_]+)(?: fmark-scope)?"')
_MARK_TAGS = ("a", "span")


def drop_scoped(html: str) -> str:
    """Remove every mark (with its word joiner) that sits inside an element whose ``data-fscope`` already states the
    same status. A caption mark (``scope=True``) speaks for its own scoped element, so it is removed only when an outer
    element states the same status too (a contest's mark inside a tab that says "every count is unofficial" once).
    The status is not lost: the section says it once."""
    if "data-fscope=" not in html:
        return html
    out, pos, stack, skip_to = [], 0, [], None
    for m in _TAG.finditer(html):
        if skip_to is not None:
            if m.group(1) and m.group(2).lower() == skip_to:
                pos, skip_to = m.end(), None
            continue
        close, tag, attrs = m.group(1), m.group(2).lower(), m.group(3)
        if close:
            while stack:
                t, _ = stack.pop()
                if t == tag:
                    break
            continue
        mk = _MARK_OPEN.match(attrs) if tag in _MARK_TAGS else None
        n_scoped = sum(1 for _, ks in stack if mk.group(1) in ks) if mk else 0
        if mk and n_scoped > (1 if "fmark-scope" in attrs else 0):
            start = m.start()
            if html[start - 1:start] == WORD_JOINER:
                start -= 1
            out.append(html[pos:start])
            skip_to = tag
            continue
        if tag not in _VOID_TAGS and not attrs.rstrip().endswith("/"):
            sc = _SCOPE_ATTR.search(attrs)
            stack.append((tag, set(sc.group(1).split()) if sc else set()))
    out.append(html[pos:])
    return "".join(out)


def scope_note(kind: str, what: str = "figure in this section") -> Markup:
    """The caption line of a section whose figures all share one exception status, in the same words everywhere:
    "Unofficial: every count on this tab. Election-night or uncertified figures; ...†". The word comes first, so an
    unofficial section is labelled in words at its top, not only by the symbol."""
    _sym, name, meaning = FIGURE_MARKS[kind]
    return scope_line([kind], [h("strong", None, f"{name}: every {what}."), f" {meaning[:1].upper()}{meaning[1:]}"],
                      cls="fscope-line" + (" fscope-unofficial" if kind == "unofficial" else ""))


def figure_notes(kinds, more: Markup | str | None = None) -> Markup:
    """The page-bottom "About these figures" note: one entry per symbol the page uses, in FIGURE_MARKS order, each
    with its meaning once (id fnote-<kind>, the target of every mark). Empty when the page uses none."""
    ks = [k for k in FIGURE_MARKS if k in set(kinds)]
    if not ks:
        return Markup("")
    items = [h("li", {"id": note_id(k), "data-fnote": k},
               h("span", {"class": "fnote-sym", "aria-hidden": "true"}, FIGURE_MARKS[k][0]), " ",
               h("strong", None, f"{FIGURE_MARKS[k][1]}:"), f" {FIGURE_MARKS[k][2]}") for k in ks]
    return h("aside", {"class": "fnotes", "id": "figure-notes", "aria-labelledby": "figure-notes-h"},
             h("h2", {"class": "fnotes-h", "id": "figure-notes-h"}, "About these figures"),
             h("ul", {"class": "fnotes-list"}, items),
             h("p", {"class": "fnotes-more"}, more) if more else None)


def scope_badge(scope: str, ed) -> Markup:
    """INDIANA-WIDE (gray) / <COUNTY> COUNTY (edition color) / <COUNTY> EXCEPTION."""
    county = ed.county.upper()
    labels = {
        "indiana": ("INDIANA-WIDE", "Applies to every Indiana county."),
        "county": (f"{county} COUNTY", f"Data or rules specific to {ed.county_label}."),
        "exception": (f"{county} EXCEPTION", f"Where state law treats {ed.county_label} differently from most counties."),
    }
    label, title = labels.get(scope, labels["county"])
    return h("span", {"class": f"scope scope-{scope}", "title": title}, label)


def party_label(code: str, short: bool = False) -> str:
    code = (code or "").strip()
    if not code:
        return "Party not recorded"
    name = PARTY_LABELS.get(code, code)
    return code if short else f"{name} ({code})"


# ------------------------------------------------------------------ party tags
# Compact "(R)" tags next to people and "(5 D, 4 R)" breakdowns next to bodies. Rules: codes in a
# breakdown are in alphabetical order of the code (never by count or party), blank parties are
# said plainly, and the dot color (party.css) is always paired with the text.

PARTY_TITLES = {
    "D": "Democratic", "R": "Republican", "L": "Libertarian", "G": "Green",
    "I": "Independent / no party", "NP": "Nonpartisan ballot", "W": "Write-in", "O": "Other party",
}
PARTY_SPOKEN = {
    "D": "Democratic", "R": "Republican", "L": "Libertarian", "G": "Green",
    "I": "independent", "W": "write-in", "O": "other-party",
}
# A low-confidence term row hides its party only when the row's note says the party itself is unsure.
_PARTY_UNSURE = re.compile(r"party (?:presumed|unconfirmed|unverified|unknown|not (?:found|confirmed|sourced|documented|stated))"
                           r"|start and party not found", re.I)


def _party_codes(party) -> list[str]:
    """Split a party field into codes in recorded order. people.csv uses 'O;R'; terms.csv one code."""
    if party is None:
        return []
    raw = [str(x) for x in party] if isinstance(party, (list, tuple)) else re.split(r"[;,/]", str(party))
    return [c.strip() for c in raw if c.strip() and c.strip().lower() not in ("unknown", "none")]


def _tag_class(code: str) -> str:
    return "party-tag party-" + (re.sub(r"[^A-Za-z]", "", code) or "other")


def _tag_parts(party, confidence=None, labels=None) -> tuple[str, str, str]:
    """(visible text, title, css class) of a party tag."""
    titles = {**PARTY_TITLES, **(labels or {})}
    codes = _party_codes(party)
    low = (confidence or "").strip().lower() == "low"
    if not codes:
        return "(party not recorded)", "No party recorded in the guide's sources", "party-tag party-none"
    if codes == ["NP"]:
        return "(nonpartisan ballot)", "Nonpartisan ballot: no party label on the ballot", "party-tag party-NP"
    shown = ", ".join(c if i == 0 else f"later {c}" for i, c in enumerate(codes))
    full = ", ".join(titles.get(c, c) if i == 0 else f"later {titles.get(c, c)}" for i, c in enumerate(codes))
    if low:
        shown, full = shown + "?", full + ", low confidence"
    return f"({shown})", full, _tag_class(codes[0]) + (" party-low" if low else "")


def name_with_party(name, party, confidence: str | None = None, labels: dict | None = None) -> Markup:
    """Name followed by a compact party tag, e.g. 'Jane Doe (D)'.

    Blank party -> '(party not recorded)'; 'NP' -> '(nonpartisan ballot)'; low confidence -> '(R?)'
    (title says 'low confidence'); several parties over a career ('O;R') -> '(O, later R)' in recorded order.
    ``labels`` optionally overrides the title text per code (people.csv notes name what 'O' stands for).
    """
    text, title, cls = _tag_parts(party, confidence, labels)
    return h("span", {"class": "name-party"}, name, " ", h("abbr", {"class": cls, "title": title}, text))


def name_party_text(name: str, party, confidence: str | None = None) -> str:
    """Plain-text form of name_with_party for JSON payloads, tables sorted as text, aria labels: 'Jane Doe (D)'."""
    return f"{name} {_tag_parts(party, confidence)[0]}"


RECORDS_MARK = "from election records"


def form_party_parts(form_party: str, records_party: str = "") -> tuple[str, str, str]:
    """(visible text, title, css class) for a candidate named on a filing form. The form's own party wins; when the
    form leaves it blank, a party from the guide's county election records (results or terms data) is shown with
    RECORDS_MARK; with neither, '(no party on the form)'. The same rule applies to every candidate."""
    if (form_party or "").strip():
        return _tag_parts(form_party)
    code = (records_party or "").strip()
    if code and code != "NP":
        text, title, cls = _tag_parts(code)
        return (f"({text[1:-1]}, {RECORDS_MARK})",
                f"{title}. The form leaves party blank; this party is from the county election records in the guide "
                "(results or officeholder data), not from the form.", cls)
    return ("(no party on the form)", "The form leaves party blank, and the guide's election records list no party "
            "for this name.", "party-tag party-none")


def name_with_form_party(name, form_party: str, records_party: str = "") -> Markup:
    """name_with_party for a candidate named on a filing form (see form_party_parts)."""
    text, title, cls = form_party_parts(form_party, records_party)
    return h("span", {"class": "name-party"}, name, " ", h("abbr", {"class": cls, "title": title}, text))


def term_party(t: dict) -> str:
    """The party code to count/label for a term row ('' when blank or the row's note says the party itself is unsure)."""
    party = (t.get("party") or "").strip()
    if not party or party.lower() == "unknown":
        return ""
    if t.get("confidence") == "low" and _PARTY_UNSURE.search(t.get("notes") or ""):
        return ""
    return party


def name_for_term(t: dict, name: str | None = None) -> Markup:
    """name_with_party for a terms.csv row (applies the low-confidence party rule)."""
    code = term_party(t)
    return name_with_party(t.get("person", "") if name is None else name, code, t.get("confidence") if code else None)


class Breakdown(Markup):
    """Markup for a party breakdown; ``.text`` is the same thing as plain text (tables, aria-labels)."""
    text: str = ""
    summary: str = ""


def breakdown_parts(terms: list[dict], seats: int | None = None) -> list[tuple[str, int, str]]:
    """[(key, count, plain)] in fixed order: party codes A-Z, 'not recorded', 'nonpartisan', 'vacant'."""
    counts: dict[str, int] = {}
    missing = nonpartisan = 0
    for t in terms:
        code = term_party(t)
        if not code:
            missing += 1
        elif code == "NP":
            nonpartisan += 1
        else:
            counts[code] = counts.get(code, 0) + 1
    parts = [(c, counts[c], f"{counts[c]} {c}") for c in sorted(counts)]
    if missing:
        parts.append(("none", missing, f"{missing} not recorded"))
    if nonpartisan:
        parts.append(("NP", nonpartisan, f"{nonpartisan} nonpartisan"))
    if seats and seats > len(terms):
        parts.append(("vacant", seats - len(terms), f"{seats - len(terms)} holder not listed" if seats - len(terms) == 1 else f"{seats - len(terms)} holders not listed"))
    return parts


def party_breakdown_text(terms: list[dict], seats: int | None = None) -> str:
    """Plain text like '(5 D, 4 R)'. No holders and no seat count -> '(no holder data)'."""
    parts = breakdown_parts(terms, seats)
    return "(" + ", ".join(p[2] for p in parts) + ")" if parts else "(no holder data)"


def party_breakdown(terms: list[dict], seats: int | None = None) -> Breakdown:
    """'(5 D, 4 R)' as Markup. Codes alphabetical by code (a fixed rule, never by count), then
    'N not recorded', 'N nonpartisan', 'N vacant' (seats known and larger than holders)."""
    parts = breakdown_parts(terms, seats)
    text = party_breakdown_text(terms, seats)
    if not parts:
        out, summary = h("span", {"class": "party-breakdown party-breakdown-none"}, text), "no holder data"
    else:
        spoken, bits = [], []
        for i, (key, n, plain) in enumerate(parts):
            if key == "none":
                spoken.append(f"{n} with no party recorded")
            elif key in ("NP", "vacant"):
                spoken.append(f"{n} nonpartisan" if key == 'NP' else (f"{n} seat whose holder is not in the guide's data" if n == 1 else f"{n} seats whose holders are not in the guide's data"))
            else:
                spoken.append(f"{n} {PARTY_SPOKEN.get(key, key)}")
            cls = {"none": "party-tag party-none", "NP": "party-tag party-NP", "vacant": "party-tag party-vacant"}.get(key, _tag_class(key))
            bits.append(h("span", {"class": cls}, plain))
            if i < len(parts) - 1:
                bits.append(", ")
        summary = ", ".join(spoken)
        out = h("span", {"class": "party-breakdown", "title": summary}, "(", bits, ")")
    b = Breakdown(out)
    b.text, b.summary = text, summary
    return b


def body_with_breakdown(title: str, terms: list[dict], seats: int | None = None) -> Markup:
    """'County Council (5 D, 4 R)'."""
    return h("span", {"class": "body-party"}, title, " ", party_breakdown(terms, seats))


# Office types that make up a multi-seat elected body, and the body's display name.
BODY_OF = {
    "county_council_member": "County Council",
    "county_commissioner": "Board of Commissioners",
    "city_council_district": "City Council", "city_council_at_large": "City Council",
    "town_council_ward": "Town Council", "town_council_at_large": "Town Council",
    "township_board_member": "Township board",
    "school_board_district": "School board", "school_board_at_large": "School board",
    "state_house": "State House members", "state_senate": "State Senate members",
}


def _seat_n(value) -> int | None:
    m = re.match(r"\s*(\d+)", str(value or ""))
    return int(m.group(1)) if m else None


def body_offices(offices: list[dict]) -> dict[str, list[dict]]:
    """Group elected body offices by body name (first-seen order of the data)."""
    out: dict[str, list[dict]] = {}
    for o in offices:
        body = BODY_OF.get(o.get("office_type", ""))
        if body and o.get("elected", "yes") != "no":
            out.setdefault(body, []).append(o)
    return out


def body_state(ed, offices: list[dict]) -> tuple[list[dict], int | None]:
    """(current holders, known seat count) for the offices of one body. Unofficial incoming terms are not
    counted (ed.current_terms keeps settled holders). Seats is None if any office lacks a count."""
    terms: list[dict] = []
    total, known = 0, True
    for o in offices:
        terms += ed.current_terms(o["office_id"])
        n = _seat_n(o.get("seats"))
        if n is None:
            known = False
        else:
            total += n
    return terms, (total if known else None)


def body_breakdown(ed, offices: list[dict]) -> Breakdown | None:
    """Breakdown for the body made of ``offices`` as of ed.as_of, or None when the guide holds no term data
    for it (callers then show nothing rather than a row of 'not recorded')."""
    terms, seats = body_state(ed, offices)
    if not terms:
        return None
    return party_breakdown(terms, seats)


def as_of_note(ed) -> Markup:
    """One line per section where breakdowns appear."""
    return h("p", {"class": "party-asof muted"},
             f"Party counts are for current holders as of {fmt_date(ed.as_of, long=True)}. "
             "Election winners who have not taken office yet are not counted. "
             "\"Holder not listed\" means the guide's data has fewer current holders than seats: the seat may be filled "
             "by someone the sources didn't name, or vacant. "
             "D Democratic, R Republican, L Libertarian, G Green, I independent, NP nonpartisan ballot, O other party.")


APPOINTED_NOTE = "Party is not tracked for appointed boards."


def bodies_block(ed, offices: list[dict], boards: list[dict] | None = None, appointed_offices: list[dict] | None = None,
                 note: bool = True, extra_bodies: dict | None = None) -> Markup | None:
    """List of multi-seat elected bodies with their party breakdowns, e.g. 'County Council (4 D, 5 R) · 9 seats'.

    ``offices``: offices of the unit(s); only multi-seat elected bodies (BODY_OF) are listed.
    ``boards``: appointed boards (appointed_boards.csv rows): seat counts only, plus one line saying party is not tracked.
    ``extra_bodies``: {name: [offices]} for bodies not in BODY_OF (for example the county's state delegation).
    The 'as of' note appears once. Returns None when there is nothing to list."""
    bodies = body_offices(offices)
    for k, v in (extra_bodies or {}).items():
        bodies[k] = v
    items = []
    for name, offs in bodies.items():
        terms, seats = body_state(ed, offs)
        seat_txt = f"{seats} seat{'s' if seats != 1 else ''}" if seats else "seat count not stated"
        if terms:
            items.append(h("li", None, h("strong", None, name), " ", party_breakdown(terms, seats), h("span", {"class": "muted"}, f" · {seat_txt}")))
        else:
            items.append(h("li", None, h("strong", None, name), h("span", {"class": "muted"}, f" · {seat_txt} · current holders not in the guide's data yet")))
    shown_any = bool(items)
    appointed = []
    for b in boards or []:
        n = _seat_n(b.get("seats"))
        appointed.append(h("li", None, h("strong", None, b["name"]), h("span", {"class": "muted"}, f" · {n} appointed seat{'s' if n != 1 else ''}" if n else " · appointed; seat count not stated")))
    for o in appointed_offices or []:
        n = _seat_n(o.get("seats"))
        appointed.append(h("li", None, h("strong", None, o["title"]), h("span", {"class": "muted"}, f" · {n} appointed seat{'s' if n != 1 else ''}" if n else " · appointed; seat count not stated")))
    if not items and not appointed:
        return None
    out = []
    if items:
        out.append(h("ul", {"class": "body-list"}, items))
    if appointed:
        out.append(h("ul", {"class": "body-list"}, appointed))
        out.append(h("p", {"class": "party-asof muted"}, APPOINTED_NOTE))
    if note and shown_any:
        out.append(as_of_note(ed))
    return h("div", {"class": "body-breakdowns"}, out)


# -------------------------------------------------------------------- folds

def fold_section(kind: str, sid: str, heading: str, count: int, intro, body) -> Markup:
    """A page-end section (Gaps, Sources) that starts collapsed.

    The <details> is written ``open`` so that with JavaScript off every row is on the page and every
    citation link works. static/js/folds.js closes it on load (unless the URL points inside it), reopens it
    when a link or the address bar targets something inside, and opens it for printing. The summary holds
    the h2 and the count, so the closed state still says what is inside.
    ``kind`` is the CSS class ("gaps" or "sources"); ``sid`` is the section id (h2 id is ``<sid>-h``)."""
    return h("section", {"class": f"{kind} fold", "id": sid, "aria-labelledby": f"{sid}-h"},
             h("details", {"class": "fold-details", "open": True, "data-fold": kind},
               h("summary", {"class": "fold-summary"},
                 h("h2", {"id": f"{sid}-h"}, f"{heading} ", h("span", {"class": "fold-count"}, f"({count})")),
                 h("span", {"class": "fold-toggle", "aria-hidden": "true"})),
               h("div", {"class": "fold-body"}, intro, body)))


# -------------------------------------------------------------------- citations

class Citations:
    """Inline superscript citations numbered in order of first use on a page."""

    def __init__(self, ed):
        self.ed = ed
        self.order: list[str] = []
        self.unknown: set[str] = set()
        # Where the entries live when they are not in this page's own Sources list: a relative page
        # URL (e.g. "sources/index.html") that citation links point into. "" = this page.
        self.href_base = ""

    def cite(self, ids, label: str | None = None) -> Markup:
        ids = split_ids(ids) if isinstance(ids, str) else [i for i in ids if i]
        if not ids:
            return Markup("")
        links = []
        for sid in dict.fromkeys(ids):
            if sid not in self.order:
                self.order.append(sid)
            if sid not in self.ed.sources:
                self.unknown.add(sid)
            n = self.order.index(sid) + 1
            src = self.ed.sources.get(sid, {})
            links.append(h("a", {"href": f"{self.href_base}#src-{sid}", "title": src.get("title", sid),
                                 "aria-label": f"Source {n}: {src.get('title', sid)}"}, n))
        return h("sup", {"class": "cite"}, join(links, ","))

    def cite_compact(self, ids) -> Markup:
        """One link for many sources (e.g. a whole layer): shows '12 +6'. Every id is still
        registered in the page's Sources list; the accessible label names all numbers."""
        ids = list(dict.fromkeys(split_ids(ids) if isinstance(ids, str) else [i for i in ids if i]))
        if len(ids) <= 2:
            return self.cite(ids)
        for sid in ids:
            if sid not in self.order:
                self.order.append(sid)
            if sid not in self.ed.sources:
                self.unknown.add(sid)
        nums = [self.order.index(s) + 1 for s in ids]
        label = "Sources " + ", ".join(str(n) for n in nums)
        return h("sup", {"class": "cite cite-compact"},
                 h("a", {"href": f"{self.href_base}#src-{ids[0]}", "title": label, "aria-label": label}, f"{nums[0]} +{len(nums) - 1}"))

    def render(self, heading: str = "Sources on this page") -> Markup:
        items = self._items()
        if not items:
            return Markup("")
        return fold_section("sources", "sources", heading, len(items), None,
                            h("ol", {"class": "source-list"}, items))

    def render_list(self) -> Markup:
        """The numbered source list alone (<ol class="source-list">, items id="src-<id>"), not folded: for a page
        whose content is the list (civic/tabs.py Sources tab). Added 2026-11-16 (phase 6 step 1)."""
        items = self._items()
        if not items:
            return h("p", None, "No sources are cited on these pages.")
        return h("ol", {"class": "source-list"}, items)

    def _items(self) -> list:
        items = []
        cited = set(self.order)
        for sid in self.order:
            s = self.ed.sources.get(sid)
            if not s:
                items.append(h("li", {"id": f"src-{sid}"}, h("span", {"class": "mono"}, sid),
                               " Source ID not found in the guide's source files."))
                continue
            title = s.get("title") or s.get("url") or sid
            # Source titles are verbatim (publishers' own headlines); the neutrality lint exempts
            # data-verbatim text but lists it, so a loaded headline is visible to reviewers.
            # The publisher leads and the title sits in quotation marks, so a cropped source line
            # reads as someone else's headline, never as the guide's own words (neutrality N7).
            t = h("cite", {"data-verbatim": "source-title"}, f"“{title}”" if s.get("title") else title)
            link = h("a", {"href": s["url"], "target": "_blank", "rel": "noopener"}, t) if s.get("url", "").startswith("http") else t
            pub = h("span", {"class": "src-pub"}, f"{s['publisher']}: ") if s.get("publisher") else None
            meta = [f"accessed {fmt_date(s['accessed'])}"] if s.get("accessed") else []
            # a source this one superseded (its notes say "Superseded ... by <sid>") keeps its old #src-<id> link on
            # this page when the page no longer cites it: the link lands on the record that replaced it (2026-11-18:
            # RES-029, the unofficial 2026 count, -> RES-048, the official canvass at the same address)
            old = [o for o in superseded_by(self.ed).get(sid, ()) if o not in cited]
            replaces = (h("span", {"class": "src-id mono"}, "Replaces ",
                           join([h("span", {"id": f"src-{o}"}, o) for o in old], ", "))
                        if old else None)
            items.append(h("li", {"id": f"src-{sid}"}, pub, link,
                           h("span", {"class": "src-meta"}, " · ".join(meta)),
                           h("span", {"class": "src-id mono"}, f"{sid} · {s.get('kind', '')}"), replaces))
        return items


SUPERSEDED = re.compile(r"\bSuperseded\b[^.]*?\bby ([A-Z]+-\d+)\b")


def superseded_by(ed) -> dict[str, list[str]]:
    """{new source id: [older source ids it replaced]}, from the older sources' notes ("Superseded 2026-11-18 by
    RES-048: ..."). A note naming an id not in the sources is ignored (the citation check reports unknown ids)."""
    got = ed.__dict__.get("_superseded_by")
    if got is None:
        got = {}
        for sid, s in ed.sources.items():
            m = SUPERSEDED.search(s.get("notes") or "")
            if m and m.group(1) in ed.sources and m.group(1) != sid:
                got.setdefault(m.group(1), []).append(sid)
        ed.__dict__["_superseded_by"] = got
    return got


# ---------------------------------------------------------------------- gaps

def gaps_section(rows: list[dict], page=None, intro: str | None = None) -> Markup:
    """'Gaps on this page': what the guide looked for and did not find, shown openly."""
    lead = intro or ("What the guide looked for and hasn't found or confirmed yet. "
                     "Gaps are listed so readers can see what is missing.")
    if not rows:
        body = h("p", None, "No open gaps are recorded for this page.")
    else:
        body = h("ul", {"class": "gaps-list"}, [
            h("li", None, h("strong", None, g.get("item", "")),
              h("span", {"class": "gap-why"}, f"Why missing: {g.get('why_missing', '')}") if g.get("why_missing") else None,
              h("span", {"class": "gap-how"}, f"How to fill: {g.get('how_to_fill', '')}") if g.get("how_to_fill") else None)
            for g in rows])
    return fold_section("gaps", "gaps", "Gaps on this page", len(rows), h("p", {"class": "muted"}, lead), body)


# ---------------------------------------------------------------------- variants

def variant_slot(ed, key: str, generic: Markup, exceptions: dict, page,
                 generic_sources: str | None = None) -> Markup:
    """Generic Indiana text plus a county-exception slot driven by edition.json.

    ``exceptions`` maps a variant value to Markup (or a callable(variant) -> Markup).
    If this edition's value has no entry, only the generic text shows, so a county
    that follows the default needs no exception callout at all.
    """
    v = ed.variant(key)
    parts = [h("div", {"class": "generic"}, scope_badge("indiana", ed), " ", generic,
               page.cites.cite(generic_sources) if generic_sources else None)]
    if v is not None:
        text = exceptions.get(v.get("value"))
        if callable(text):
            text = text(v)
        if text:
            verified = v.get("verified", False)
            note = v.get("note", "")
            parts.append(h("div", {"class": "exception" + ("" if verified else " exception-unverified")},
                           h("div", {"class": "exception-tags"}, scope_badge("exception", ed),
                             None if verified else status_badge("unverified", page)),
                           h("div", {"class": "exception-body"}, text),
                           None if verified or not note else h(
                               "p", {"class": "exception-note"},
                               h("span", {"class": "mono"}, "Why unverified: "), note)))
    return h("div", {"class": "variant", "data-variant": key}, parts)


# ---------------------------------------------------------------------- tables

def data_table(table_id: str, headers: list, rows: list[list], caption: str | None = None,
               numeric: tuple[int, ...] = (), copy: bool = True, label: str | None = None,
               min_width: str | None = None, row_attrs: list[dict] | None = None) -> Markup:
    """A scrollable table with an optional Copy CSV button (app.js builds the CSV).
    ``min_width`` (e.g. '44rem') keeps wide tables readable on phones; the wrapper scrolls.
    ``row_attrs`` (one dict per row, e.g. ``{"data-tf-year": "2027"}``) puts attributes on each <tr>;
    ``table_filter`` uses them."""
    thead = h("thead", None, h("tr", None, [h("th", {"scope": "col", "class": "num" if i in numeric else None}, c)
                                            for i, c in enumerate(headers)]))
    body = []
    for n, r in enumerate(rows):
        cells = []
        for i, c in enumerate(r):
            tag = "th" if i == 0 else "td"
            cells.append(h(tag, {"scope": "row" if i == 0 else None, "class": "num" if i in numeric else None}, c))
        body.append(h("tr", row_attrs[n] if row_attrs else None, cells))
    table = h("table", {"id": table_id, "class": "data", "style": f"min-width: {min_width}" if min_width else None},
              h("caption", None, caption) if caption else None, thead, h("tbody", None, body))
    tools = h("div", {"class": "table-tools"},
              h("button", {"type": "button", "class": "btn btn-small", "data-copy-table": table_id,
                           "id": f"{table_id}-copy"}, "Copy CSV")) if copy else None
    return h("div", {"class": "table-block"},
             h("div", {"class": "table-wrap", "role": "region", "tabindex": "0",
                       "aria-label": label or caption or "Data table"}, table), tools)


# ---------------------------------------------------------------------- table filters

def table_filter(table_id: str, controls: list[dict], total: int, noun: str = "row",
                 search: str | None = None, sort: list[tuple[str, str, str]] | None = None,
                 label: str | None = None, *, search_first: bool = False) -> Markup:
    """One row of labelled controls above a table (static/js/tablefilter.js wires it).

    Rows opt in with ``data-tf-<key>="<value>"`` attributes (see ``data_table(row_attrs=...)``).
    controls: ``[{"key": "year", "label": "Year", "all": "All years", "options": [(value, text), ...]}]``;
    a row shows when, for every select, its ``data-tf-<key>`` equals the chosen value (a control with ``"tokens": True``
    matches when the value is one of the row's space-separated values; added 2026-11-16).
    search: label of a text box that matches the words typed against the row's text (``None`` = no box).
    sort: ``[(value, text, spec)]`` where spec is ``"attr:dir:kind[,attr:dir:kind]"`` (kind ``n`` = number,
    ``s`` = string; attr is a ``data-`` attribute of the row); the first option is the default order.
    search_first (keyword only, added 2026-11-16 for the People hub): put the text box before the selects.
    The bar is ``hidden`` until the script runs, so with JavaScript off the table is simply whole.
    Filtering only hides rows; the count line says how many of the total are shown."""
    fields = []
    for c in controls:
        cid = f"tf-{table_id}-{c['key']}"
        fields.append(h("div", {"class": "field"},
                        h("label", {"for": cid}, c["label"]),
                        h("select", {"id": cid, "data-tf-key": c["key"], "data-tf-tokens": True if c.get("tokens") else None},
                          h("option", {"value": ""}, c.get("all", "All")),
                          [h("option", {"value": v}, t) for v, t in c["options"]])))
    if search:
        sid = f"tf-{table_id}-q"
        box = h("div", {"class": "field field-search"},
                h("label", {"for": sid}, search),
                h("input", {"id": sid, "type": "search", "data-tf-q": True, "autocomplete": "off",
                            "spellcheck": "false"}))
        if search_first:
            fields.insert(0, box)
        else:
            fields.append(box)
    if sort:
        sid = f"tf-{table_id}-sort"
        fields.append(h("div", {"class": "field"},
                        h("label", {"for": sid}, "Sort"),
                        h("select", {"id": sid, "data-tf-sort": True},
                          [h("option", {"value": v, "data-spec": spec}, t) for v, t, spec in sort])))
    plural = noun + ("s" if not noun.endswith("s") else "")
    return h("div", {"class": "picker tf", "role": "group", "aria-label": label or "Filter the table below",
                     "data-tf-table": table_id, "data-tf-total": total, "data-tf-noun": noun,
                     "data-tf-plural": plural, "hidden": True},
             fields,
             h("button", {"type": "button", "class": "btn btn-small tf-reset", "data-tf-reset": True}, "Reset filters"),
             h("p", {"class": "picker-help tf-count", "data-tf-count": True, "aria-live": "polite"},
               f"{total} of {total} {plural} shown."))


def filter_empty_note(table_id: str) -> Markup:
    """The message shown when no row matches (hidden until then)."""
    return h("p", {"class": "tf-empty muted", "data-tf-empty": table_id, "hidden": True, "role": "status"},
             "No rows match these filters. Use Reset filters to see them all.")


# ---------------------------------------------------------------------- layout bits

def section(sid: str, num: int | None, title: str, *children, scope: str | None = None, ed=None,
            lead: str | None = None) -> Markup:
    kicker = h("span", {"class": "kicker"}, f"§ {num:02d}") if num is not None else None
    badge = scope_badge(scope, ed) if scope and ed is not None else None
    return h("section", {"class": "block", "id": sid, "aria-labelledby": f"{sid}-h"},
             h("header", {"class": "block-head"}, kicker,
               h("h2", {"id": f"{sid}-h"}, title), badge),
             h("p", {"class": "lead"}, lead) if lead else None, children)


def callout(*children, kind: str = "note") -> Markup:
    return h("aside", {"class": f"callout callout-{kind}"}, children)


def officeholder_card(ed, page, office: dict, current: list[dict], incoming: list[dict],
                      note: Markup | None = None) -> Markup:
    """Text-only card. Same fields for every office (ux-review 6: equal cards, no photos)."""
    rows = []
    if not current:
        rows.append(h("p", {"class": "holder holder-none"}, "No current officeholder in the guide's data."))
    for t in current:
        rows.append(_holder(ed, page, t, kind="current"))
    for t in incoming:
        rows.append(_holder(ed, page, t, kind="incoming"))
    return h("article", {"class": "card holder-card", "id": f"office-{office['office_id']}"},
             h("h3", {"class": "card-title"}, office["title"]), rows,
             h("p", {"class": "card-note"}, note) if note else None)


def _holder(ed, page, t: dict, kind: str) -> Markup:
    low = t.get("confidence") == "low"
    if kind == "incoming":
        when = h("p", {"class": "holder-when"},
                 f"Takes office {fmt_date(t['start'])}",
                 " (results unofficial)" if t.get("status") == "unofficial" else "")
    else:
        since = fmt_date(t["start"]) or "start date not in sources"
        when = h("p", {"class": "holder-when"}, f"In office since {since}")
    first = SELECTED_BY_LABELS.get(t.get("first_selected_by", ""), t.get("first_selected_by"))
    return h("div", {"class": f"holder holder-{kind}"},
             h("p", {"class": "holder-kind mono"}, "Current" if kind == "current" else "Incoming"),
             h("p", {"class": "holder-name"}, t["person"], page.cites.cite(t.get("source_ids"))),
             h("p", {"class": "holder-party mono"}, party_label(t.get("party"))),
             when,
             h("p", {"class": "holder-how"}, f"How first chosen: {first}"),
             h("p", {"class": "holder-badges"}, status_badge(t.get("status"), page),
               status_badge("low", page) if low else None))



# ---------------------------------------------------------------------- "See all rows" fold (P3)
# Added 2026-11-09 (Wave A, batch 1). When a chart or list above already summarizes a table, the full table moves
# into a fold under it: "See all 163 rows" with the table's filters and Copy CSV inside. Same progressive-enhancement
# contract as fold_section: the <details> ships open (JavaScript off: every row is on the page), static/js/folds.js
# closes it on load unless the address points inside it (a row id), reopens it when a link targets something inside,
# and opens it for printing. Filters are the shared table_filter (static/js/tablefilter.js); Copy CSV copies only
# the rows the filters leave shown (static/app.js, "rows-filtered").

def _plural(noun: str, n: int, plural: str | None = None) -> str:
    if n == 1:
        return noun
    return plural or (noun if noun.endswith("s") else noun + "s")


def see_all_fold(fold_id: str, count: int, body, noun: str = "row", plural: str | None = None,
                 hint: str | None = "Copy CSV", label: str | None = None, cls: str = "") -> Markup:
    """A closed-by-default fold holding a full table (or any long list) that a chart or list above summarizes.

    Markup: ``<details class="fold-details see-all" id=fold_id data-fold="see-all" open>`` whose summary reads
    "See all 163 rows" (``label`` replaces that text) and a muted ``hint`` ("Filters · Copy CSV"); ``body`` is the
    content. Every id inside stays reachable: a link or address pointing at a row opens the fold first."""
    text = label or f"See all {count:,} {_plural(noun, count, plural)}"
    return h("details", {"class": "fold-details see-all" + (f" {cls}" if cls else ""), "id": fold_id, "open": True,
                         "data-fold": "see-all"},
             h("summary", {"class": "fold-summary see-all-summary"},
               h("span", {"class": "see-all-label"}, text),
               h("span", {"class": "see-all-hint"}, hint) if hint else None,
               h("span", {"class": "fold-toggle", "aria-hidden": "true"})),
             h("div", {"class": "fold-body see-all-body"}, body))


def see_all_table(table_id: str, headers: list, rows: list[list], *, noun: str = "row", plural: str | None = None,
                  caption: str | None = None, numeric: tuple[int, ...] = (), label: str | None = None,
                  min_width: str | None = None, row_attrs: list[dict] | None = None,
                  controls: list[dict] | None = None, search: str | None = None,
                  sort: list[tuple[str, str, str]] | None = None, filter_label: str | None = None,
                  intro=None, fold_id: str | None = None, summary: str | None = None) -> Markup:
    """``data_table`` (with Copy CSV) inside ``see_all_fold``, with the same ``table_filter`` bar the table would have
    outside a fold. ``controls``/``search``/``sort`` are table_filter's arguments (rows opt in through ``row_attrs``,
    e.g. ``{"data-tf-year": "2024"}``); with none of them there is no filter bar. ``fold_id`` defaults to
    ``<table_id>-all``; ``summary`` replaces "See all N rows". The table keeps ``table_id`` and its Copy button
    ``<table_id>-copy``."""
    n = len(rows)
    filters = bool(controls or search or sort)
    body = [intro,
            table_filter(table_id, controls or [], n, noun=noun, search=search, sort=sort, label=filter_label)
            if filters else None,
            filter_empty_note(table_id) if filters else None,
            data_table(table_id, headers, rows, caption=caption, numeric=numeric,
                       label=label or caption or f"All {_plural(noun, 2, plural)}",
                       min_width=min_width, row_attrs=row_attrs)]
    return see_all_fold(fold_id or f"{table_id}-all", n, body, noun=noun, plural=plural,
                        hint="Filters · Copy CSV" if filters else "Copy CSV", label=summary)


# ---------------------------------------------------------------------- entity list (P5)
# Added 2026-11-09 (Wave A, batch 1). One row per entity (a person, a committee, a ballot question, an office): name,
# two or three key facts and a status badge on the always-visible line; the full card or table inside. Each row is
# civic/pick_one.py's one_fold (<details data-one=KEY data-fold="one" open>), so the pick_one contract applies:
# JavaScript off, every row ships open; folds.js closes them on load unless the address points inside one; a link
# or #anchor to anything inside a row opens that row (and, through pick_one.js, folds the others). An optional words
# box is table_filter's search, pointed at the list instead of a table (tablefilter.js accepts any container whose
# direct children carry data-tf-row).

_TAGS = re.compile(r"<[^>]+>")


def entity_list(list_id: str, items: list[dict], *, noun: str = "item", plural: str | None = None,
                search: str | None = None, controls: list[dict] | None = None,
                sort: list[tuple[str, str, str]] | None = None, filter_label: str | None = None,
                heading_tag: str = "h3", label: str | None = None) -> Markup:
    """A compact list of entities, each row a <details> holding its full detail.

    items: ``[{key, name, facts?: [str|Markup, ...] (2-3), status?: status_badge key (str) or Markup, body,
    item_id?: id of the <details>, heading_id?: id of the row's heading, search?: extra words a reader may type,
    attrs?: {"data-tf-<key>": value, ...} for filters and sort}]``, in the order given (callers sort; people by office
    and district, never by party or vote share).
    ``search`` is the words box's label (None = no box); ``controls``/``sort`` are table_filter's. The status badge on
    the summary line is a plain span (a link inside <summary> would hijack the toggle); put the linked badge in
    ``body`` when the definitions link matters. Words typed match the row's name, facts and ``search`` text."""
    rows = []
    for it in items:
        facts = [f for f in (it.get("facts") or []) if f not in (None, "")]
        st = it.get("status")
        # Markup is a str subclass: test it first so a ready-made badge is passed through, not escaped again
        # (2026-11-18: the status is its symbol, as a plain span, not a link: status_symbol; official shows none)
        badge = st if isinstance(st, Markup) else (status_symbol(st) if isinstance(st, str) and st else st)
        sep = h("span", {"class": "ent-sep", "aria-hidden": "true"}, " · ")
        summary = [h(heading_tag, {"class": "one-h ent-name", "id": it.get("heading_id")}, it["name"]),
                   h("span", {"class": "one-digest ent-facts"},
                     join([h("span", {"class": "ent-fact"}, f) for f in facts], sep)) if facts else None,
                   h("span", {"class": "ent-status"}, badge) if badge else None]
        words = " ".join([_plain(it["name"]), *[_plain(f) for f in facts], _plain(it.get("search") or "")])
        li_attrs = {"class": "ent-row", "data-tf-row": True,
                    "data-tf-text": re.sub(r"\s+", " ", words).strip() if _filters_on(search, controls, sort) else None}
        li_attrs.update(it.get("attrs") or {})
        rows.append(h("li", li_attrs, _one_fold()(it["key"], str(it["name"]), summary, it.get("body"),
                                                  item_id=it.get("item_id"), cls="ent-item")))
    filters = _filters_on(search, controls, sort)
    return h("div", {"class": "ent-block"},
             table_filter(list_id, controls or [], len(items), noun=noun, search=search, sort=sort,
                          label=filter_label or f"Find a {noun}") if filters else None,
             h("p", {"class": "tf-empty muted", "data-tf-empty": list_id, "hidden": True, "role": "status"},
               f"No {_plural(noun, 2, plural)} match. Use Reset filters to see them all.") if filters else None,
             h("ul", {"class": "one-list ent-list", "id": list_id, "aria-label": label}, rows))


def _filters_on(search, controls, sort) -> bool:
    return bool(search or controls or sort)


def _plain(v) -> str:
    """Text of a value for the words box: Markup loses its tags and entities, plain text stays as it is."""
    if isinstance(v, Markup):
        return _html.unescape(_TAGS.sub(" ", str(v)))
    return str(v)


def _one_fold():
    from .pick_one import one_fold   # pick_one imports only .html; imported here so components stays first to load
    return one_fold
