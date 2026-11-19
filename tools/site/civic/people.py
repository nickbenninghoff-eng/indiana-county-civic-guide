"""Person pages: who is who, which people get a page, and their paths and tabs (phase 6, 2026-11-16;
planning/design-direction-2026-11-16.md sections 0 and 2). The data has no person ids, so identity is decided here, once,
from the name strings in terms.csv, results.csv, people.csv and the campaign-finance files, by one function
(``group_names``) that the sitemap, the pages, the search index and the name links all read.

    people/index.html                  the People hub (pages/people.py build_hub)
    people/<id>/index.html             Overview: offices held now and before, party as recorded, the notable-people card
    people/<id>/elections/             every contest the person ran in, newest first
    people/<id>/money/                 their committees' money (the campaign pages' own sums)
    people/<id>/sources/               citations and gaps

Identity rules (published on the hub, ``RULES``), conservative on purpose:

1. Two name strings are one person only when the full name agrees: the site's existing rule
   (civic/campaign_money.py ``same_person``, which money_history.holder_links and same_name_links use: the same
   surname, suffixes and initials set aside, a shared given name, a nickname written in quotes or parentheses counting
   as a given name), with the given names also compared through community_history's nickname table (Stephen/Steve).
   Notes in parentheses ("(write-in)", "(interim)", "(printed ...)") and titles (Dr., Rev., Hon.) are set aside first.
   A surname alone, or initials alone for a given name ("T. Brown"), never matches anything (``is_partial``).
2. Middle names or initials written on both strings must agree ("Amy S." and "Amy Suzanne" agree; "John A." and
   "John B." do not; a middle that is the other string's nickname, "Bobby K", is not a middle), and suffixes written on
   both must agree (Jr and Jr. agree; Jr and Sr do not). A suffix written on one string only ("Joe Taylor",
   "Joe Taylor III") joins only when both strings hold the same office (or, when one has no office, the same
   government), since it can name a parent and a child: Schuyler Colfax and Schuyler Colfax III stay apart.
3. Strings joined this way form a group; when two strings of a group disagree (rule 2), the group is not merged: the
   disagreeing strings are sides, and a string that would join several sides (a "bridge", "Tom McCormick") joins the
   one side it shares an office with if exactly one, else stands alone. The pages of such a family name each other as
   possibly the same person (``Person.maybe_same``).
4. A group whose records make one person unlikely (``implausible``: more than ``GAP_YEARS`` years between two
   stretches of records with no term spanning them, both stretches with a recorded party (not NP or W) and the two
   sharing neither a party nor a government) is kept as one page but marked "may be more than one person with this
   name". Nothing is merged on these grounds and nothing is split on a guess.

Nothing here edits a data file or changes a name: every string is shown as its record prints it.
"""
from __future__ import annotations

import re
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field

from . import tabs
from .campaign_money import SUFFIXES, given, same_person, surname

HUB = "people/index.html"
GROUP = "People"
GAP_YEARS = 20

# results.csv candidate strings that are not people: ballot-question answers, straight-party tallies, write-in totals
NOT_A_PERSON = re.compile(r"^(?:yes|no|write-?ins?|over ?votes?|under ?votes?|blank)\b|^write-ins? \(|/", re.I)
# contests that are not a race between people (the candidates are YES/NO or parties)
NON_PERSON_CONTEST = re.compile(r"straight-party|public-question|question|retention|referendum|constitutional")
# contests for statewide offices (the county's tally only): their candidates are listed on the hub without a page
STATEWIDE_CONTEST = re.compile(r"-state-(?!house|senate)")
WRITE_IN_MARK = re.compile(r"\s*\((?:write-?in)\)\s*$", re.I)


# ============================================================================ names

# a parenthesis that is a note on the record, not part of the name ("(write-in)", "(interim)", '(printed "Camarecci")')
NOTE_PAREN = re.compile(r"\s*\((?:write-?in|interim|printed\b[^)]*)\)", re.I)
HONORIFIC = re.compile(r"^(?:dr|rev|hon|mr|mrs|ms)\.?\s+", re.I)


def clean(name: str) -> str:
    """The name without a note in parentheses ("(write-in)", "(interim)"), a leading title ("Dr.") and extra spaces.
    Used only for matching; pages show the record's own string."""
    s = NOTE_PAREN.sub(" ", name or "")
    s = WRITE_IN_MARK.sub("", s)
    return HONORIFIC.sub("", re.sub(r"\s+", " ", s).strip())


def _strip_nicks(name: str) -> str:
    return re.sub(r'"[^"]*"|\([^)]*\)', " ", name or "")


def _tokens(name: str) -> list[str]:
    """Words of the name outside quotes and parentheses, without suffixes."""
    return [t for t in re.split(r"[\s,]+", _strip_nicks(clean(name))) if t and t.strip(".").lower() not in SUFFIXES]


def suffix(name: str) -> str:
    """'jr', 'sr', 'ii', 'iii', 'iv' or '' ("Jr" and "Jr." are the same suffix)."""
    for t in re.split(r"[\s,]+", _strip_nicks(clean(name))):
        if t.strip(".").lower() in SUFFIXES:
            return t.strip(".").lower()
    return ""


def nick_phrases(name: str) -> list[str]:
    """Nicknames written in quotes or parentheses, lower-case words: 'Robert L. "Bobby K" Kruszynski' -> ['bobby k'].
    A parenthesis that is a note rather than a name ("(given name unconfirmed ...)", "(write-in)") is not one."""
    out = []
    for m in re.findall(r'"([^"]+)"|\(([^)]+)\)', clean(name)):
        part = (m[0] or m[1]).strip()
        words = re.findall(r"[A-Za-z][A-Za-z'\-]*", part)
        if part and len(words) <= 2 and not re.search(r"[:;]|given name|unconfirmed|unknown|write", part, re.I):
            out.append(" ".join(w.lower() for w in words))
    return out


def is_partial(name: str) -> bool:
    """True when the string has no given name: a surname alone ("Carter"), initials only ("T. Brown", "J. J. Kata"),
    or a record that says its given name is unknown ("Pfeifer (given name unconfirmed ...)"). A nickname written in
    quotes counts as a given name ('"Bobby K" Kruszynski'). Such a string is never merged with another."""
    if re.search(r"(?i)\(given name|unconfirmed|unknown\)", name or ""):
        return True
    toks = _tokens(name)
    if not toks:
        return True
    words = [t for t in toks[:-1] if len(t.strip(".")) > 1]
    nick = [w for ph in nick_phrases(name) for w in ph.split() if len(w) > 1]
    return not words and not nick


def middles(name: str) -> list[str]:
    """Middle names or initials, lower-case, without dots: 'Robert L. "Bobby K" Kruszynski Jr.' -> ['l']."""
    toks = _tokens(name)
    return [t.strip(".").lower() for t in toks[1:-1] if t.strip(".")]


def _middles_vs(a: str, b: str) -> list[str]:
    """a's middle names, leaving out words that b writes as a nickname ("Bobby K Kruszynski" against
    'Robert L. "Bobby K" Kruszynski': the K is part of the nickname "Bobby K", not a middle initial)."""
    toks = [t.strip(".").lower() for t in _tokens(a)[:-1]]
    for ph in nick_phrases(b) + nick_phrases(a):
        w = ph.split()
        if len(w) > 1 and toks[:len(w)] == w:
            return toks[len(w):]
    return middles(a)


def compatible(a: str, b: str) -> bool:
    """Rule 2: written suffixes agree, and written middle names or initials agree (an initial agrees with a name that
    starts with it)."""
    sa, sb = suffix(a), suffix(b)
    if sa and sb and sa != sb:
        return False
    ma, mb = _middles_vs(a, b), _middles_vs(b, a)
    if ma and mb:
        x, y = ma[0], mb[0]
        if x[0] != y[0]:
            return False
        if len(x) > 1 and len(y) > 1 and x != y:
            return False
    return True


_CANON: dict | None = None


def _canon_table() -> dict:
    """Nickname pairs the site already applies, as one table: civic/campaign_money.py NICKNAMES (the money pages:
    'william' -> 'bill') and pages/community_history.py NICKNAMES (the notable-people list: 'steve' -> 'stephen').
    Each name maps to one representative of its pair group."""
    global _CANON
    if _CANON is None:
        from .campaign_money import NICKNAMES as A
        try:
            from pages.community_history import NICKNAMES as B
        except ImportError:      # civic used without the page modules (never in a build)
            B = {}
        parent: dict = {}

        def find(x):
            parent.setdefault(x, x)
            while parent[x] != x:
                x = parent[x]
            return x
        for k, v in list(A.items()) + list(B.items()):
            ra, rb = find(k), find(v)
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
        _CANON = {k: find(k) for k in parent}
    return _CANON


def given_names(name: str) -> set:
    """civic/campaign_money.py given() (the given name and any nickname in quotes or parentheses), each name mapped
    through both nickname tables (``_canon_table``)."""
    t = _canon_table()
    return {t.get(g, g) for g in given(clean(name))}


def same_name(a: str, b: str) -> bool:
    """Rule 1: campaign_money.same_person (same surname, a shared given name) with the site's two nickname tables."""
    if same_person(clean(a), clean(b)):
        return True
    sa = surname(clean(a))
    return bool(sa) and sa == surname(clean(b)) and bool(given_names(a) & given_names(b))


def _shares_seat(a: str, b: str, seats: dict) -> bool:
    """The two strings' records name the same office; or, when one of them names no office (a filing or a
    people.csv row), the same government."""
    sa, sb = seats.get(a, set()), seats.get(b, set())
    oa, ob = {x for x in sa if not x.startswith("unit:")}, {x for x in sb if not x.startswith("unit:")}
    if oa & ob:
        return True
    if not oa or not ob:
        return bool({x for x in sa if x.startswith("unit:")} & {x for x in sb if x.startswith("unit:")})
    return False


def match(a: str, b: str, seats: dict | None = None) -> bool:
    """Rules 1 and 2 for one pair of strings. A suffix written on one string only ("Schuyler Colfax" and "Schuyler
    Colfax III", "Joe Taylor" and "Joe Taylor III") may name a parent and child, so such a pair matches only when
    ``seats`` shows the two records name the same office (or, for a record with no office, the same government)."""
    if a == b:
        return True
    if is_partial(a) or is_partial(b):
        return False
    if not (same_name(a, b) and compatible(a, b)):
        return False
    if bool(suffix(a)) != bool(suffix(b)):
        return _shares_seat(a, b, seats or {})
    return True


def norm_key(name: str) -> str:
    """The comparison form of one string: case, dots, commas, quotes and spacing set aside."""
    return re.sub(r"[^a-z0-9]+", " ", clean(name).lower()).strip()


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "person"


def short_slug(name: str) -> str:
    """The page id of a name: given name and surname (plus a written suffix), without middle initials, nicknames or
    punctuation: 'Robert L. "Bobby K" Kruszynski Jr.' -> 'robert-kruszynski-jr'."""
    toks = _tokens(name)
    if is_partial(name) or len(toks) < 2:
        return slug(_strip_nicks(clean(name)) or name)
    first = next((t for t in toks[:-1] if len(t.strip(".")) > 1), toks[0])
    parts = [first, toks[-1]] + ([suffix(name)] if suffix(name) else [])
    return slug(" ".join(parts))


def identity_groups(names, seats: dict | None = None) -> tuple[list[list[str]], list[list[list[str]]]]:
    """``group_names`` and, for each joined group that rule 3 split, the parts it was split into (each part's page
    names the others as possibly the same person)."""
    names = sorted(set(n for n in names if (n or "").strip()))
    seats = seats or {}
    by_sur: dict = defaultdict(list)
    for n in names:
        by_sur[surname(clean(n)) if not is_partial(n) else "~partial~" + n].append(n)
    groups, families = [], []
    for _s, ns in sorted(by_sur.items()):
        parent = {n: n for n in ns}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        for i, a in enumerate(ns):
            for b in ns[i + 1:]:
                if match(a, b, seats):
                    ra, rb = find(a), find(b)
                    if ra != rb:
                        parent[max(ra, rb)] = min(ra, rb)
        comp: dict = OrderedDict()
        for n in ns:
            comp.setdefault(find(n), []).append(n)
        for members in comp.values():
            parts = _resolve(members, seats)
            groups += parts
            if len(parts) > 1:
                families.append(parts)
    groups.sort(key=lambda g: (surname(clean(g[0])), g[0]))
    return groups, families


def group_names(names, seats: dict | None = None) -> list[list[str]]:
    """THE identity function: name strings -> groups of strings that are one person (rules 1 to 3). ``seats`` (optional)
    maps a string to the offices (and "unit:<government>") its records name; it decides only a pair whose suffix is
    written on one string, and where a string goes that would join two groups that disagree. Each group is sorted;
    groups come in a fixed order (by surname, then first string). Deterministic for the same input."""
    return identity_groups(names, seats)[0]


def _fits(n: str, g: list[str], seats: dict) -> bool:
    return any(match(n, x, seats) for x in g) and all(compatible(n, x) for x in g)


def _resolve(members: list[str], seats: dict) -> list[list[str]]:
    """Rule 3. A joined group whose strings all agree pair by pair stays one group. Otherwise the strings that disagree
    with another ("Thomas L. McCormick", "Tom E. McCormick") form the sides: each joins a side it matches and agrees
    with entirely ("Tom E McCormick" joins "Tom E. McCormick"), else starts one. Every other string ("Tom McCormick")
    agrees with more than one side: it joins the one side whose records name the same office, when exactly one does;
    otherwise it stays on its own (the page then names the other strings as possibly the same person)."""
    if all(compatible(a, b) for i, a in enumerate(members) for b in members[i + 1:]):
        return [sorted(members)]
    clash = sorted({a for a in members for b in members if a != b and not compatible(a, b)},
                   key=lambda n: (-len(middles(n)), n))
    sides: list[list[str]] = []
    for n in clash:
        home = [g for g in sides if _fits(n, g, seats)]
        if len(home) == 1:
            home[0].append(n)
        else:
            sides.append([n])
    alone = []
    for n in sorted(set(members) - set(clash)):
        home = [g for g in sides if _fits(n, g, seats)]
        if len(home) > 1:
            mine = seats.get(n, set())
            home = [g for g in home if mine & set().union(*(seats.get(x, set()) for x in g))]
        if len(home) == 1:
            home[0].append(n)
        else:
            alone.append([n])
    return [sorted(g) for g in sides + alone]


# ============================================================================ records and people

@dataclass
class Rec:
    """One record that names a person: a term, a ballot line, a people.csv row, a campaign-finance row."""
    kind: str          # term | result | notable | cf_local | cf_state | cf_state_history | cf_reported
    name: str          # the string as the record prints it
    y0: int | None
    y1: int | None
    unit: str          # government (units.csv id; "state" for the General Assembly and statewide; "" unknown)
    party: str
    row: dict


@dataclass
class Person:
    pid: str
    name: str                      # the display string (see display_name)
    names: list                    # every string in the group
    recs: list = field(default_factory=list)
    flags: list = field(default_factory=list)       # "may be more than one person" reasons (rule 4)
    page: bool = False
    why_page: str = ""             # which threshold rule gives the page
    notable: dict | None = None    # the notable-people row (pages/community_history.py notable_rows), if any
    maybe_same: list = field(default_factory=list)   # pids split from this one by rule 3

    def of(self, *kinds) -> list:
        return [r for r in self.recs if r.kind in kinds]


def _year(s) -> int | None:
    m = re.match(r"(\d{4})", s or "")
    return int(m.group(1)) if m else None


def _records(ed) -> list[Rec]:
    """Every record that names a person, from the edition's tables (never edited)."""
    from .data import parse_date
    out: list[Rec] = []
    now = ed.as_of.year
    for t in ed.tables["terms"]:
        o = ed.offices.get(t["office_id"]) or {}
        unit = o.get("unit_id", "")
        if unit.startswith("state-"):
            unit = "state"
        end = ed.term_end(t)
        st = parse_date(t["start"])
        y0 = st.year if st else None
        y1 = end.year if end else (now if y0 else None)
        out.append(Rec("term", t["person"], y0, y1, unit, (t.get("party") or "").strip(), t))
    for c in ed.contests.values():
        if NON_PERSON_CONTEST.search(c["contest_id"]):
            continue
        o = ed.offices.get(c["office_id"]) or {}
        unit = o.get("unit_id", "")
        if not unit:
            unit = "state" if "-state-" in c["contest_id"] else c["label"].split(":")[0].strip()
        if unit.startswith("state-"):
            unit = "state"
        y = _year((ed.elections.get(c["election_id"]) or {}).get("date")) or _year(c["election_id"])
        for r in c["rows"]:
            if NOT_A_PERSON.search(r["candidate"].strip()):
                continue
            out.append(Rec("result", r["candidate"], y, y, unit, (r.get("party") or "").strip(), dict(r, _contest=c)))
    for p in ed.table("people"):
        ys = [int(y) for y in re.findall(r"\b(1[789]\d\d|20\d\d)\b", p.get("offices_summary", ""))]
        out.append(Rec("notable", p["name"], min(ys) if ys else None, max(ys) if ys else None, "",
                       (p.get("parties") or "").split(";")[-1].strip(), p))
    from .campaign_money import money_year
    for r in ed.table("cf_local"):
        if r.get("candidate"):
            y = money_year(r)
            out.append(Rec("cf_local", r["candidate"], y, y, r.get("unit_id") or "", (r.get("party") or "").strip(), r))
    for f in ("cf_state", "cf_state_history"):
        for r in ed.table(f):
            if r.get("candidate"):
                y = _year(r.get("year"))
                out.append(Rec(f, r["candidate"], y, y, "state", (r.get("party") or "").strip(), r))
    for r in ed.table("cf_reported"):
        c = ed.contests.get(r["contest_id"]) or {}
        o = ed.offices.get(c.get("office_id", "")) or {}
        y = _year(r["contest_id"])
        out.append(Rec("cf_reported", r["candidate"], y, y, o.get("unit_id", ""), (r.get("party") or "").strip(), r))
    return out


def implausible(recs: list[Rec]) -> list[str]:
    """Rule 4: the reasons one person is unlikely, or []. Two stretches of records more than GAP_YEARS apart with no
    term spanning the gap, sharing neither a recorded party nor a government."""
    dated = sorted((r for r in recs if r.y0 is not None), key=lambda r: (r.y0, r.y1 or r.y0))
    if len(dated) < 2:
        return []
    out = []
    reach = dated[0].y1 or dated[0].y0
    for i in range(1, len(dated)):
        r = dated[i]
        if r.y0 - reach > GAP_YEARS:
            before, after = dated[:i], dated[i:]
            pb = {x.party for x in before if x.party and x.party not in ("NP", "W")}
            pa = {x.party for x in after if x.party and x.party not in ("NP", "W")}
            ub = {x.unit for x in before if x.unit}
            ua = {x.unit for x in after if x.unit}
            if pb and pa and not (pb & pa) and not (ub & ua):
                out.append(f"the records fall {r.y0 - reach} years apart ({reach} and {r.y0}) with no term in "
                           "between, and the two periods share neither a recorded party nor a government")
        reach = max(reach, r.y1 or r.y0)
    return out


def display_name(group: list[str], recs: list[Rec]) -> str:
    """The string a person's page is titled with: the newest term's spelling, else the people.csv name, else the
    newest ballot's spelling, else the newest filing's. A record's own string, never a composed one."""
    for kinds in (("term",), ("notable",), ("result",), ("cf_reported",), ("cf_local", "cf_state", "cf_state_history")):
        rs = [r for r in recs if r.kind in kinds]
        if rs:
            rs.sort(key=lambda r: (r.y0 or 0, r.y1 or 0, r.name))
            return rs[-1].name
    return group[0]


@dataclass
class Registry:
    people: "OrderedDict[str, Person]"
    by_string: dict                     # name string -> pid (every string of every group)
    below: list = field(default_factory=list)   # [(name, [contest ids])]: candidates with no page (hub list)

    def pid_for(self, name: str) -> str | None:
        return self.by_string.get(name) or self.by_string.get(clean(name))

    def person(self, name: str) -> "Person | None":
        pid = self.pid_for(name)
        return self.people.get(pid) if pid else None


def money_names(ed) -> set:
    """Name strings with campaign money on record (a committee filing, a state filing year or a news figure)."""
    out = set()
    for f in ("cf_local", "cf_state", "cf_state_history", "cf_reported"):
        out |= {r["candidate"] for r in ed.table(f) if r.get("candidate")}
    return out


def identity(ed) -> Registry:
    """Every person in the edition's records: the groups of ``group_names`` with their records, display names, page
    ids and rule-4 flags. No page decisions (``registry`` adds them). Cached on the edition; the notable-people list
    (pages/community_history.py people_pool) reads it too, so the site has one answer to who is who."""
    got = ed.__dict__.get("_people_identity")
    if got is not None:
        return got
    recs = _records(ed)
    by_name: dict = defaultdict(list)
    for r in recs:
        by_name[r.name].append(r)
    seats: dict = defaultdict(set)
    for r in recs:
        oid = r.row.get("office_id") if r.kind == "term" else (r.row["_contest"]["office_id"] if r.kind == "result" else "")
        if oid:
            seats[r.name].add(oid)
        if r.unit:
            seats[r.name].add("unit:" + r.unit)
    groups, families = identity_groups(by_name, seats)
    people: OrderedDict = OrderedDict()
    by_string: dict = {}
    staged = []
    for g in groups:
        rs = [r for n in g for r in by_name[n]]
        disp = display_name(g, rs)
        staged.append((g, rs, disp, short_slug(disp)))
    count: dict = defaultdict(int)
    for _g, _rs, _d, sl in staged:
        count[sl] += 1
    used: set = set()
    for g, rs, disp, sl in staged:
        pid = sl if count[sl] == 1 else slug(_strip_nicks(clean(disp)))
        n, base_ = 2, pid
        while pid in used:
            pid, n = f"{base_}-{n}", n + 1
        used.add(pid)
        p = Person(pid, disp, list(g), rs)
        p.flags = implausible(rs)
        people[pid] = p
        for x in g:
            by_string[x] = pid
    # rule 3's split groups name each other ("possibly the same person as")
    for fam in families:
        pids = [by_string[g[0]] for g in fam]
        for pid in pids:
            people[pid].maybe_same = [x for x in pids if x != pid]
    got = Registry(people, by_string)
    ed.__dict__["_people_identity"] = got
    return got


def registry(ed) -> Registry:
    """``identity`` plus who gets a page (``THRESHOLD``), the notable-people rows and the hub's list of candidates
    without a page. Built once per edition (cached on it)."""
    got = ed.__dict__.get("_people_registry")
    if got is not None:
        return got
    from pages.community_history import notable_rows
    ident = identity(ed)
    with_money = money_names(ed)
    for row in notable_rows(ed):
        pid = ident.pid_for(row["name"])
        if pid:
            ident.people[pid].notable = row
    below = []
    for p in ident.people.values():
        p.page, p.why_page = _gets_page(p, with_money)
        if not p.page:
            cids = list(dict.fromkeys(r.row["_contest"]["contest_id"] for r in p.of("result")))
            if cids:
                below.append((p.name, cids))
    got = Registry(ident.people, ident.by_string, below)
    ed.__dict__["_people_registry"] = got
    return got


# The published threshold (shown on the hub). Order matters only for the "why" line.
THRESHOLD = [
    ("term", "Has held, holds or is about to take an office in the guide's officeholder records."),
    ("notable", "Is one of the notable people picked by the published rules (History: people who shaped local "
                "government)."),
    ("general", "Was a candidate on a general-election or special-election ballot for a county, township, city, town, "
                "school-board or state-legislative seat."),
    ("primary_money", "Ran in a party primary for one of those seats and has campaign money on record (a committee "
                      "report, a state filing year or a figure reported in the news)."),
]
THRESHOLD_TEXT = dict(THRESHOLD)
# the identity rules in words (the hub's "how names are matched"), the same rules as the module docstring
RULES_TEXT = [
    "Two records are one person only when the full name agrees: the same surname (suffixes and initials set aside) "
    "and the same given name, where a nickname written in quotes or parentheses counts and the guide's two published "
    "nickname tables apply (William and Bill, Stephen and Steve). A surname alone, or initials alone, never joins "
    "anything.",
    "Middle names or initials written on both records must agree (“Amy S.” and “Amy Suzanne” "
    "agree; “John A.” and “John B.” do not), and so must suffixes written on both (Jr and Jr. "
    "agree; Jr and Sr do not). A suffix on one record only (“Joe Taylor”, “Joe Taylor III”) "
    "joins only when both records are for the same office, since it can name a parent and a child.",
    "When a name would join two records that disagree, it is not merged: each stays on its own page, and the pages "
    "name each other as possibly the same person.",
    f"When one name's records are more than {GAP_YEARS} years apart with no term in between, and the two periods share "
    "neither a recorded party nor a government, the page is marked “may be more than one person with this "
    "name”. Nothing is merged or split on a guess, and no data file is changed to make names match.",
]


def _local_race(c: dict) -> bool:
    return not NON_PERSON_CONTEST.search(c["contest_id"]) and not STATEWIDE_CONTEST.search(c["contest_id"])


def _gets_page(p: Person, with_money: set) -> tuple[bool, str]:
    if p.of("term"):
        return True, "term"
    if p.notable is not None:
        return True, "notable"
    if all(is_partial(n) for n in p.names):
        return False, ""          # a surname or initials only: listed on the hub with its contests, no page
    races = [r.row["_contest"] for r in p.of("result") if _local_race(r.row["_contest"])]
    if any(not c["party_primary"] for c in races):
        return True, "general"
    if races and any(n in with_money for n in p.names):
        return True, "primary_money"
    return False, ""


# ============================================================================ paths and tabs

def base(pid: str) -> str:
    return f"people/{pid}/"


def path(pid: str, tab: str = "overview") -> str:
    return tabs.tab_path(base(pid), tab)


NOTABLE = "people/notable/index.html"
OLD_NOTABLE = "history/people/index.html"


def contests(ed, pid: str) -> list[dict]:
    """Every contest the person's ballot lines are in (results.csv), newest first; ties: the general election, then
    primaries by party. Each item: {"contest", "row"} (the person's own line)."""
    p = registry(ed).people[pid]
    seen, out = set(), []
    for r in p.of("result"):
        c = r.row["_contest"]
        if c["contest_id"] in seen:
            continue
        seen.add(c["contest_id"])
        out.append({"contest": c, "row": r.row})

    def key(x):
        c = x["contest"]
        d = (ed.elections.get(c["election_id"]) or {}).get("date") or c["election_id"][:4]
        return (d, 1 if not c["party_primary"] else 0, c["contest_id"])
    out.sort(key=key, reverse=True)
    return out


def terms(ed, pid: str) -> list[dict]:
    """The person's terms in terms.csv, newest start first (a term with no start date last)."""
    from datetime import date
    from .data import parse_date
    p = registry(ed).people[pid]
    rows = [r.row for r in p.of("term")]
    return sorted(rows, key=lambda t: (parse_date(t["start"]) or date.min, t["term_id"]), reverse=True)


def money_model(ed, pid: str) -> dict:
    """The person's campaign money, from the guide's existing computations only (cached):

    races: [(race, cand)]: the campaign pages' race model (pages/campaigns.py cf_all) entries whose candidate is this
           person; cand["raised"]/["spent"] are the race card's own sums (the office Money tab shows the same)
    other: [(committee key, part)]: money_history._parts pieces of this person's committees that no race counts
    committees: every committee key whose filings name this person, or that a race counts for them
    reported: [(contest, [cf_reported rows])]: figures reported in the news
    state: [money_history.legislators entry]: committees filing with the state (filing-year sums)
    """
    cache = ed.__dict__.setdefault("_person_money", {})
    if pid in cache:
        return cache[pid]
    from pages import money_history as mh
    from pages.campaigns import cf_all
    reg = registry(ed)
    races = []
    for race in sorted(cf_all(ed)["races"], key=lambda r: r["date"], reverse=True):
        for cand in race["candidates"]:
            if reg.pid_for(cand["name"]) == pid:
                races.append((race, cand))
    ix = mh.index(ed)
    own = [k for k, rs in ix["rows"].items() if any(r["candidate"] and reg.pid_for(r["candidate"]) == pid for r in rs)]
    committees = list(dict.fromkeys([s["key"] for _r, c in races for s in c["committees"]] + own))
    other = []
    for k in own:
        for part in mh._parts(ed, k):
            if part["race"] is None:
                other.append((k, part))
    reported: OrderedDict = OrderedDict()
    for r in ed.table("cf_reported"):
        if reg.pid_for(r["candidate"]) == pid:
            c = ed.contests.get(r["contest_id"])
            if c:
                reported.setdefault(c["contest_id"], (c, []))[1].append(r)
    state = [lp for lp in mh.legislators(ed)
             if reg.pid_for(lp["name"]) == pid or any(reg.pid_for(r["candidate"]) == pid for r in lp["rows"])]
    got = {"races": races, "other": other, "committees": committees, "reported": list(reported.values()),
           "state": state}
    cache[pid] = got
    return got


def has_money(ed, pid: str) -> bool:
    m = money_model(ed, pid)
    return bool(any(c["committees"] for _r, c in m["races"]) or m["other"] or m["reported"] or m["state"])


def person_tabs(ed, pid: str) -> list[str]:
    """Overview and Sources always; Elections when the person has a ballot line; Money when money is on record.
    No History tab: a person's past offices are on the Overview, so a History tab would repeat it."""
    cache = ed.__dict__.setdefault("_person_tabs", {})
    if pid in cache:
        return cache[pid]
    keys = ["overview"]
    if contests(ed, pid):
        keys.append("elections")
    if has_money(ed, pid):
        keys.append("money")
    keys.append("sources")
    cache[pid] = tabs.ordered(keys)
    return cache[pid]


def sort_key(p: Person):
    """Alphabetical by surname, then the whole name (never by party or office)."""
    return (surname(clean(p.name)) or clean(p.name).lower(), clean(p.name).lower(), p.pid)


def paged(ed) -> list[Person]:
    """The people with a page, alphabetical."""
    return sorted((p for p in registry(ed).people.values() if p.page), key=sort_key)


def crumb(p: Person) -> list:
    return [("People", HUB), (p.name, None)]


# person ids whose sitemap entries were built in this process (pages/people.py registers their builders)
KNOWN_IDS: set = set()


def people_entries(ed) -> list:
    """Sitemap entries: the hub, the notable-people view, then every person's tabs (alphabetical)."""
    from .sitemap import Entry
    out = [Entry(HUB, "People", "People",
                 "Everyone in the guide who has held an elected office, and the candidates who meet a published "
                 "threshold: offices held, every race run and the campaign money on record.", "county", GROUP, [],
                 crumb=[("People", None)]),
           Entry(NOTABLE, "Notable people", "Notable people",
                 "People who shaped local government, picked by five published rules applied the same way to everyone "
                 "in the guide's data, with the rules shown.", "county", GROUP,
                 [("rules", "Selection rules"), ("people", "The people")],
                 crumb=[("People", HUB), ("Notable people", None)])]
    for p in paged(ed):
        KNOWN_IDS.add(p.pid)
        keys = person_tabs(ed, p.pid)
        desc = {"overview": f"{p.name}: offices held in the guide's records, party as recorded, and every race run.",
                "elections": f"{p.name}: every contest in the guide's results, newest first.",
                "money": f"{p.name}: campaign money on record, by election, from the reports the guide holds.",
                "sources": f"{p.name}: every source behind these pages, and how the records were matched."}
        out += tabs.tab_entries(base(p.pid), p.name, desc["overview"], keys, group=GROUP, crumb=crumb(p),
                                tab_descriptions=desc)
    return out


def href(page, pid: str | None, tab: str = "overview", frag: str = "") -> str | None:
    """Relative link from ``page`` to a person's tab, or None when that page is not in this build."""
    if not pid:
        return None
    p = path(pid, tab)
    if p not in page.site.by_path:
        return None
    return page.rel(p) + (f"#{frag}" if frag else "")


def href_for_name(page, name: str, tab: str = "overview") -> str | None:
    """The person page of a name string as a record prints it, or None (no page, or not in this build)."""
    p = registry(page.ed).person(name)
    return href(page, p.pid, tab) if p is not None and p.page else None


# ============================================================================ name links (every page)

# A name the site prints with a party tag (components.name_with_party / name_with_form_party) and a candidate's name
# in a results or money chart (charts.results_rows / money_rows) become links to the person's page, here, once, for
# every page (civic/shell.py Page.render). The party tag itself is not touched. Never inside another link, a <summary>
# (a click there opens the fold), a button, a label, an option or a textarea, and never on the person's own pages.
_LINK_SCAN = re.compile(r'<(/?)(a|summary|button|label|option|textarea)\b[^>]*>'
                        r'|<span class="name-party">([^<]+?) (?=<abbr )'
                        r'|<span class="mrw-name">([^<]+)</span>')
_BLOCKING = ("a", "summary", "button", "label", "option", "textarea")


def link_names(html: str, page) -> str:
    """``html`` with every person name (see above) linked to the person's page when one is built."""
    import html as _html
    if 'class="name-party"' not in html and 'class="mrw-name"' not in html:
        return html
    if "_people_registry" not in page.ed.__dict__ and not page.ed.tables.get("terms"):
        return html
    reg = registry(page.ed)
    own = getattr(page.entry, "thing", "") if page.entry is not None else ""
    depth = dict.fromkeys(_BLOCKING, 0)
    out, last = [], 0
    for m in _LINK_SCAN.finditer(html):
        if m.group(2):
            tag = m.group(2).lower()
            depth[tag] = max(0, depth[tag] + (-1 if m.group(1) else 1))
            continue
        if any(depth.values()):
            continue
        raw = m.group(3) if m.group(3) is not None else m.group(4)
        p = reg.person(_html.unescape(raw))
        if p is None or not p.page or base(p.pid) == own:
            continue
        u = href(page, p.pid)
        if not u:
            continue
        a = f'<a class="person-link" href="{_html.escape(u)}">{raw}</a>'
        rep = f'<span class="name-party">{a} ' if m.group(3) is not None else f'<span class="mrw-name">{a}</span>'
        out.append(html[last:m.start()])
        out.append(rep)
        last = m.end()
    if not out:
        return html
    out.append(html[last:])
    return "".join(out)


# ============================================================================ short facts (hub, search, header)

def term_state(ed, t: dict) -> str:
    """'now' (in office on the data date), 'incoming' (takes office later), or 'before'."""
    if t in ed.current_terms(t["office_id"]):
        return "now"
    if t in ed.incoming_terms(t["office_id"]):
        return "incoming"
    return "before"


def office_title(ed, office_id: str, fallback: str = "") -> str:
    return (ed.offices.get(office_id) or {}).get("title") or fallback or office_id


def contest_office_title(ed, c: dict) -> str:
    """The office a contest is for: its office's title, else the contest's own label without the primary's party."""
    if c.get("office_id") and c["office_id"] in ed.offices:
        return ed.offices[c["office_id"]]["title"]
    return re.sub(r"\s*\((?:Democratic|Republican|Libertarian)[^)]*primary\)$", "", c["label"])


def years_text(a, b) -> str:
    if a and b and a != b:
        return f"{a} to {b}"
    return str(a or b or "")


def one_line(ed, p: Person) -> str:
    """One neutral line about a person, the same shape for everyone: the office held now, else the latest office held,
    else the latest race, else the notable-people list."""
    ts = terms(ed, p.pid)
    now = [t for t in ts if term_state(ed, t) == "now"]
    if now:
        return "; ".join(dict.fromkeys(office_title(ed, t["office_id"]) for t in now)) + ", in office"
    inc = [t for t in ts if term_state(ed, t) == "incoming"]
    if inc:
        return f"Takes office {inc[0]['start'][:4]}: " + office_title(ed, inc[0]["office_id"])
    if ts:
        t = ts[0]
        end = ed.term_end(t)
        return f"{office_title(ed, t['office_id'])}, " + years_text(t["start"][:4], end.year if end else "")
    cs = contests(ed, p.pid)
    if cs:
        c = cs[0]["contest"]
        return f"Candidate: {contest_office_title(ed, c)}, {c['election_id'][:4]}"
    return "On the notable-people list"


def status_tokens(ed, p: Person) -> str:
    """The hub's "Office" filter values: 'now' and 'held' for a current officeholder, 'held' for a former one (and
    for an incoming one: 'incoming held'), 'candidate' for someone with no term in the records."""
    states = {term_state(ed, t) for t in terms(ed, p.pid)}
    out = []
    if "now" in states:
        out.append("now")
    if "incoming" in states:
        out.append("incoming")
    if states:
        out.append("held")
    else:
        out.append("candidate")
    return " ".join(out)


def level_tokens(ed, p: Person) -> str:
    """The hub's "Level" filter values: the levels of government (civic/offices.py LEVELS keys) of every office the
    person held or ran for."""
    from .offices import level
    lv = set()
    for t in terms(ed, p.pid):
        o = ed.offices.get(t["office_id"])
        if o:
            lv.add(level(ed, o))
    for x in contests(ed, p.pid):
        o = ed.offices.get(x["contest"].get("office_id") or "")
        if o:
            lv.add(level(ed, o))
    from .offices import LEVELS
    return " ".join(k for k in LEVELS if k in lv)
