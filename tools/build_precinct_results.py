"""Build data/editions/<edition>/precinct_results.csv and derived/precinct_areas.json.

    python -X utf8 -P -E tools/build_precinct_results.py --edition st-joseph

Inputs (sources/precincts/):
  openelections-in/*.csv         2020 and 2024 general precinct results (OpenElections, MIT)
  sjc-county/57716.txt           pdftotext -layout of the county's 2022 "Signed Official Report with precincts"
  openelections-sources-in/2020-GE-St-Joseph-Precinct.ocr*.txt
                                 OCR reads of the county's scanned 2020 Precinct Summary Report (MAP-009), written by
                                 tools/ocr_2020_precinct_report.py and parsed by tools/precinct_report_2020.py
  tigerweb-vtd2020/vtd.json      Census 2020 voting districts (NAME = 6-digit county precinct code)
  ../boundaries/*.geojson        townships, incorporated places

Every precinct/race is verified before it is written: candidate votes must equal the race's printed "Total Votes"
(2022 report, 2020 report), and county (or district) sums must equal the official canvass figures (checks below).
A precinct that fails a check is left out of that race and logged, never guessed; a race whose sum then differs from
the official figure stops the build (exit 1). Stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # -P drops the script dir; precinct_report_2020 lives here
from precinct_report_2020 import parse_reads  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "sources" / "precincts"

# RULE (published on the map page; tools/build_map.py RACE_RULE says the same in plain words):
# every PARTISAN race (candidates run with a party label, or as independents, on the general-election ballot) for a
# FEDERAL, STATE (statewide and state legislative), COUNTY (county-wide offices, county judges elected on a party
# ballot, county commissioner and county council districts), TOWNSHIP (trustee, board, assessor) or TOWN/CITY office
# (council, clerk-treasurer, mayor) on the county's 2020, 2022 and 2024 general-election ballots, where the guide has
# precinct results. Uncontested races are included and labelled; races electing several members (vote for 2 or 3)
# are included and labelled with the number of seats.
# Left out, and why: judicial retention votes and public questions (yes/no questions, no candidates); school board
# races (nonpartisan by law); the straight-party tally (a ballot option, not an office).
# Township and town offices found: only on the 2022 ballot (2022 report: trustee and board in all 13 townships, Penn
# Township assessor, town council in New Carlisle, North Liberty and Roseland (at-large) and Walkerton (wards 1 and 2)).
# The 2020 report's race titles have none; the 2024 OpenElections file's office list has none. No city office is on any
# of the three ballots (South Bend and Mishawaka elect their officers in odd years).
# Each source's office list was read in full: OpenElections 2020 (President, Governor, Attorney General, U.S. House 2nd,
# State Senate 8/9/10, State Representative 5/6/7/8/21; no county offices, so 2020 county races come from the county's
# own 2020 report), OpenElections 2024 (President, U.S. Senate, Governor, U.S. House 2nd, Attorney General, State Senate
# 8/9/10, State Representative 5/6/7/8/21, Judge of the Probate Court, Recorder, Treasurer, Coroner, Surveyor,
# Commissioner 2 and 3, Council D/F/G/I), the county's 2022 report (U.S. Senate, Secretary of State, Auditor, Treasurer,
# U.S. House 2nd and its special election, State Senator 11, State Representative 5/6/7/8/21, Judge of the Circuit
# Court, Prosecuting Attorney, Clerk, County Auditor, Sheriff, Assessor, Commissioner 1, Council A/B/C/E/H), and the
# county's 2020 report for its county offices (Recorder, Treasurer, Coroner, Surveyor, Commissioner 2 and 3, Council
# D/F/G/I). OFFICE_IGNORED lists every office read and left out under the rule.
FEDERAL = ("president", "us-senate", "us-house", "us-house-special")
STATEWIDE = ("governor", "secretary-of-state", "auditor", "treasurer", "attorney-general")
COUNTYWIDE_COUNTY = ("county-circuit-judge", "county-probate-judge", "county-prosecutor", "county-clerk",
                     "county-auditor", "county-recorder", "county-treasurer", "county-sheriff", "county-coroner",
                     "county-surveyor", "county-assessor")
DISTRICT_FAMILIES = ("state-senate", "state-house", "county-commissioner", "county-council",
                     "township-assessor", "township-trustee", "township-board", "town-council")
LOCAL_FAMILIES = ("township-assessor", "township-trustee", "township-board", "town-council")
SOURCE_IDS = {"2020g": "MAP-005", "2024g": "MAP-006", "2022g": "MAP-007"}
OCR_SOURCE = "MAP-009"


def district_family(contest: str):
    for f in DISTRICT_FAMILIES:
        if contest.startswith(f + "-"):
            return f
    return None


def countywide(contest: str) -> bool:
    return contest in FEDERAL or contest in STATEWIDE or contest in COUNTYWIDE_COUNTY


def known_contest(contest: str) -> bool:
    return countywide(contest) or (district_family(contest) is not None)


# ---- OpenElections (2020, 2024) ----------------------------------------------------------
OE_OFFICE = {
    "Governor And Lieutenant Governor": "governor", "Governor": "governor",
    "President Of The United States": "president", "President": "president",
    "U.S. Senate": "us-senate",
    "Attorney General": "attorney-general",
    "U.S. House": "us-house", "United States Representative": "us-house",
    "County Coroner": "county-coroner", "County Recorder": "county-recorder", "County Surveyor": "county-surveyor",
    "County Treasurer": "county-treasurer", "Judge Of Probate Court": "county-probate-judge",
}
# Offices in the OpenElections files that are not races under the rule (each one checked by name, so a new office in
# an updated file stops the build instead of being dropped silently).
OFFICE_IGNORED = re.compile(r"^(Ballots Cast|Registered Voters|Straight Party|Public Question #\d+|.*Judicial Retention|"
                            r"Retain (Justice|Judge) .*|.*School Board.*|.*School Corporation.*)$")
OE_PARTY = {"DEM": "D", "REP": "R", "LIB": "L"}
NO_CANDIDATE = "No Candidate Filed"   # ballot placeholder (IC 3-11-2-12(b)); always 0 votes, not a candidate

# Official canvass figures used to verify the county sums (transcribed from the county's
# summary pages / canvass; the script fails loudly if the precinct data does not add up to them).
CANVASS_2020_GOV = {"D": 48610, "R": 60696, "L": 5387}
CANVASS_2024_GOV = {"D": 54911, "R": 52056, "L": 3375}
# 2022 county summary pages 1-2 of 57716.pdf (candidate totals, "Official Results").
CANVASS_2022 = {
    "us-senate": {"D": 33013, "R": 37276, "L": 1327},
    "secretary-of-state": {"D": 34746, "R": 33748, "L": 2654},
    "auditor": {"D": 32336, "R": 36810, "L": 1909},
    "treasurer": {"D": 34451, "R": 36474},
    # summary page 1 (regular) and page 2 (special); candidate votes x 100 / Total Votes match the printed percentages
    "us-house": {"D": 32743, "R": 36869, "L": 1962},
    "us-house-special": {"D": 32638, "R": 36908, "L": 1968},
}
# Federal races: candidate totals from the county's official summary reports (results.csv leaves federal races out).
# 2020: doc 42820 "Official Results" 11/13/2020, text layer, page 1. 2024: doc 64951 "FINAL Official Results"
# 11/15/2024, scanned, pages 1-2 read from the image; every block's candidate votes add up to its printed Total Votes.
# W = write-ins combined; O = other ballot party (2024 President: Kennedy/Shanahan, We the People, 939).
CANVASS_FEDERAL = {
    ("2020g", "president"): {"D": 59896, "R": 53164, "L": 1925, "W": 253},
    ("2020g", "us-house"): {"D": 58882, "R": 55705},
    ("2024g", "president"): {"D": 55215, "R": 53585, "L": 680, "O": 939, "W": 404},
    ("2024g", "us-senate"): {"D": 53253, "R": 54590, "L": 2210, "W": 13},
    ("2024g", "us-house"): {"D": 52015, "R": 54489, "L": 2433, "W": 6},
}
# Transcription errors in the OpenElections 2020 file, corrected from the county's own 2020 Precinct Summary Report
# (12/9/2020, scanned, archived by OpenElections; MAP-009). Found because the 2020 U.S. House Democratic sum was 88
# below the canvass; every precinct's House box was then OCR'd and compared (219 equal, these 2 differ; each
# corrected box adds up to its printed Total Votes). With both fixes the county sum equals the canvass exactly.
# The script refuses to run if the OpenElections value is no longer the one corrected here (re-check if upstream changes).
OE_CORRECTIONS = {
    # (election, precinct code, contest, party): (OpenElections value, county report value, where)
    ("2020g", "100001", "us-house", "D"): (16, 106, "Olive Twp 1, report page 263: Hackett 106 + Walorski 213 = 319"),
    ("2020g", "040002", "us-house", "D"): (158, 156, "Greene Twp 2, report page 81: Hackett 156 + Walorski 372 = 528"),
}
# Rows filed under the wrong office in the OpenElections 2020 file. South Bend 130111 has no State Senate race on its
# ballot (Senate District 11 was not up in 2020); its State Representative District 8 result (Dvorak 79, Jaycox 34) is
# filed as "State Senate, district 8". Found because the State Senate 8 sums were D +79 / R +34 above the official
# canvass and State Representative 8 the same amount below; the county report (MAP-009, page 366, checked on the page
# image) shows the House 8 box "Dvorak 79 + Jaycox 34 = 113" and no Senate box. With the fix both races equal the canvass.
OE_OFFICE_CORRECTIONS = {
    # (election, precinct code, OE office, OE district): (office, district, where)
    ("2020g", "130111", "State Senate", "8"): ("State Representative", "8",
                                              "South Bend 130111, report page 366: State Representative District 8, "
                                              "Dvorak 79 + Jaycox 34 = 113; no State Senate box"),
}
CORRECTION_SOURCE = "MAP-009"
# Races checked against the guide's own official county totals (results.csv, rows with status "official"), party by
# party; a mismatch stops the build. The contest id is "<election>-<contest>" for state-legislative and county races
# (e.g. 2022g-county-sheriff, 2020g-state-senate-8); statewide races are listed here. Federal races have no rows in
# results.csv; they are checked against CANVASS_FEDERAL and CANVASS_2022 instead.
OFFICIAL_ID = {
    "governor": "state-governor", "attorney-general": "state-attorney-general",
    "secretary-of-state": "state-secretary-of-state", "auditor": "state-auditor-of-state",
    "treasurer": "state-treasurer-of-state",
}

CODE_PREFIX = {"CENTRE": 1, "CLAY": 2, "GERMAN": 3, "GREENE": 4, "HARRIS": 5, "LIBERTY": 6, "LINCOLN": 7,
               "MADISON": 8, "OLIVE": 10, "PENN": 11, "PORTAGE": 12, "UNION": 14, "WARREN": 15}


# 2022 township and town races checked against the 2022 report's summary pages ("Official Results", 11/18/2022), read
# from the page images (the text layer of those pages is incomplete and misreads digits). Each block's candidate votes
# add up to its printed Total Votes and match its printed percentages.
CANVASS_2022_LOCAL = {
    "township-trustee-union": {"Kelly Carrico": ("R", 726), "Debra A Watts": ("O", 480)},
    "township-board-union": {"Trisha N Carrico": ("R", 700), "Ryan Schafer": ("R", 767), "Mike Wozny": ("R", 692)},
    "town-council-new-carlisle": {"Marcy Kauffman": ("D", 358)},
    "town-council-north-liberty": {"Gerry E Brown": ("R", 287), "Thomas England": ("R", 250)},
    # summary page 8/10 image: "GENE REESE (REP) 438 100.00%", Total Votes 438
    "town-council-walkerton-ward-2": {"Gene Reese": ("R", 438)},
}

# results.csv rows known to disagree with a summary-page image: {(election, contest): ({party: results.csv votes}, note)}.
# While an entry's figure is still in results.csv, the race is checked against the image instead. Empty since
# 2026-11-08, when the one entry (Walkerton Ward 2: text-layer misread 436, image and precinct pages 438) was corrected
# in results.csv, together with the same page's School City of Mishawaka misread (Parks 3,276 -> 3,278).
RESULTS_CSV_MISREADS: dict = {}


def official_id(eid: str, contest: str):
    """results.csv contest id for a mapped race (None for federal races, which results.csv leaves out)."""
    if contest in FEDERAL:
        return None
    m = re.fullmatch(r"township-(assessor|trustee|board)-([a-z-]+)", contest)
    if m:
        return f"{eid}-{m.group(2)}-township-{m.group(1)}"
    m = re.fullmatch(r"town-council-([a-z-]+?)(?:-(ward-\d+))?", contest)
    if m:
        return f"{eid}-{m.group(1)}-council-{m.group(2) or 'at-large'}"
    return f"{eid}-{OFFICIAL_ID.get(contest, contest)}"


def name_to_code_2020(name: str):
    """'Centre Twp 1' -> 010001; 'Mishawaka 12' -> 090012; 'South Bend 5' -> 130005."""
    m = re.match(r"^(.*?)\s+(?:Twp\s+)?(\d+)$", name.strip(), re.I)
    if not m:
        return None
    base, n = m.group(1).upper().replace("TWP", "").strip(), int(m.group(2))
    if base == "MISHAWAKA":
        p = 9
    elif base == "SOUTH BEND":
        p = 13
    else:
        p = CODE_PREFIX.get(base)
    return f"{p:02d}{n:04d}" if p else None


def oe_contest(office: str, district: str, cand: str, senate_by_name: dict):
    """Contest id for one OpenElections row, None for an office outside the rule. Unknown offices stop the build."""
    if office in OE_OFFICE:
        return OE_OFFICE[office]
    if office == "State Representative" and district:
        return f"state-house-{int(district)}"
    if office == "State Senate":
        if district:
            return f"state-senate-{int(district)}"
        d = senate_by_name.get(cand.split()[-1].lower()) if cand.strip() else None
        if d is None:
            raise SystemExit(f"State Senate row without a district for {cand!r}: no 2024 State Senate candidate in "
                             "results.csv has this surname")
        return f"state-senate-{d}"
    m = re.fullmatch(r"County Commissioner District (\d+)", office)
    if m:
        return f"county-commissioner-{m.group(1)}"
    m = re.fullmatch(r"County Council District ([A-I])", office)
    if m:
        return f"county-council-{m.group(1).lower()}"
    if OFFICE_IGNORED.match(office):
        return None
    raise SystemExit(f"OpenElections office {office!r} is not classified (add it to OE_OFFICE or OFFICE_IGNORED)")


def read_oe(path: Path, eid: str, log, senate_by_name=None, used_office_fix=None):
    """code -> contest -> [(party, candidate, votes, printed party)], names"""
    rows = defaultdict(lambda: defaultdict(list))
    names = {}
    unmatched = set()
    for r in csv.DictReader(open(path, encoding="utf-8")):
        pname = r["precinct"].strip()
        m = re.search(r"\b(\d{6})$", pname)
        code = m.group(1) if m else name_to_code_2020(pname)
        office, district = r["office"].strip(), r["district"].strip()
        if code and (eid, code, office, district) in OE_OFFICE_CORRECTIONS:
            office, district, where = OE_OFFICE_CORRECTIONS[(eid, code, office, district)]
            if used_office_fix is not None:
                used_office_fix[(eid, code, r["office"].strip(), r["district"].strip())] = where
        cand = r["candidate"].strip()
        if cand == NO_CANDIDATE:
            if int(r["votes"] or 0):
                raise SystemExit(f"{eid} {pname} {office}: '{NO_CANDIDATE}' row has votes")
            continue
        contest = oe_contest(office, district, cand, senate_by_name or {})
        if not contest:
            continue
        if not code:
            unmatched.add(pname)
            continue
        names[code] = re.sub(r"\s+\d{6}$", "", pname).title()
        party = OE_PARTY.get(r["party"], "")
        if r["party"] in ("WI", "") or "(W)" in cand:
            party = "W"
        elif not party:
            party = "O"
        rows[code][contest].append((party, cand, int(r["votes"] or 0), r["party"] or "W"))
    if unmatched:
        log.append(f"{eid}: {len(unmatched)} precinct names did not convert to a code: {sorted(unmatched)}")
    return rows, names


# ---- 2022 county report (text layer of a scanned PDF) --------------------------------------
TITLES = [  # (regex, contest or function of the match)
    (re.compile(r"UNITED STATES SENATOR"), "us-senate"),
    (re.compile(r"SECRETARY OF STATE"), "secretary-of-state"),
    (re.compile(r"AUDITOR OF STATE"), "auditor"),
    (re.compile(r"TREASURER OF STATE"), "treasurer"),
    (re.compile(r"UNITED STATES REPRESENTATIVE 2ND DISTRICT(?!.*SPECIAL)"), "us-house"),
    (re.compile(r"UNITED STATES REPRESENTATIVE 2ND DISTRICT\s*-\s*SPECIAL"), "us-house-special"),
    (re.compile(r"^\s*STATE SENATOR DISTRICT (\d+)\b"), lambda m: f"state-senate-{int(m.group(1))}"),
    (re.compile(r"^\s*STATE REPRESENTATIVE DISTRICT (\d+)\b"), lambda m: f"state-house-{int(m.group(1))}"),
    (re.compile(r"^\s*JUDGE OF THE CIRCUIT COURT\b"), "county-circuit-judge"),
    (re.compile(r"^\s*PROSECUTING ATTORNEY\b"), "county-prosecutor"),
    (re.compile(r"^\s*CLERK OF THE CIRCUIT COURT\b"), "county-clerk"),
    (re.compile(r"^\s*COUNTY AUDITOR\b"), "county-auditor"),
    (re.compile(r"^\s*COUNTY SHERIFF\b"), "county-sheriff"),
    (re.compile(r"^\s*COUNTY ASSESSOR\b"), "county-assessor"),
    (re.compile(r"^\s*COUNTY COMMISSIONER DISTRICT (\d+)\b"), lambda m: f"county-commissioner-{int(m.group(1))}"),
    (re.compile(r"^\s*COUNTY COUNCIL MEMBER DISTRICT ([A-I])\b"), lambda m: f"county-council-{m.group(1).lower()}"),
    (re.compile(r"^\s*(" + "|".join(CODE_PREFIX) + r") TOWNSHIP (TRUSTEE|ASSESSOR|BOARD MEMBERS)\b"),
     lambda m: f"township-{m.group(2).split()[0].lower()}-{m.group(1).lower()}"),
    (re.compile(r"^\s*([A-Z][A-Z ]*?[A-Z]) TOWN COUNCIL (AT-LARGE|WARD \d+)\b"),
     lambda m: "town-council-" + m.group(1).lower().replace(" ", "-") +
     ("" if m.group(2) == "AT-LARGE" else "-" + m.group(2).lower().replace(" ", "-"))),
]
# Every precinct votes in these 2022 races (checked: a precinct missing one is logged as a failure of that race).
COUNTYWIDE_2022 = ("us-senate", "secretary-of-state", "auditor", "treasurer", "us-house", "us-house-special",
                   "county-circuit-judge", "county-prosecutor", "county-clerk", "county-auditor", "county-sheriff",
                   "county-assessor")
HEADER = re.compile(r"^\s*([A-Z][A-Z .\-]*?(?:\s+\d+)?)\s+(\d{6})(?:\s+\d+)?\s*$")
TAG = re.compile(r"\((DEM|REP|LIB|W|IND|NP|WTP)\)")
INT = re.compile(r"^\d{1,3}(?:,\d{3})*$|^\d+$")
SKIP = re.compile(r"^\s*(Registered Voters|Precinct Detail|ST\. JOSEPH|2022 GENERAL|NOVEMBER|St\. Joseph County|Official Results|Election Summary)", re.I)


def title_contest(line: str):
    for rx, c in TITLES:
        m = rx.search(line)
        if m:
            return c(m) if callable(c) else c
    return None


def parse_2022(txt_path: Path, log):
    lines = txt_path.read_text(encoding="utf-8", errors="replace").splitlines()
    # precinct segments
    seg = []  # (code, name, start, end)
    cur = None
    for i, ln in enumerate(lines):
        m = HEADER.match(ln)
        if m and not ln.strip().startswith(("Total", "Vote")):
            code = m.group(2)
            if cur is None or cur[0] != code:
                if cur:
                    seg.append((cur[0], cur[1], cur[2], i))
                cur = (code, m.group(1).strip(), i)
    if cur:
        seg.append((cur[0], cur[1], cur[2], len(lines)))
    res = {}
    fails = {}
    seats_all = {}
    for code, name, a, b in seg:
        seats_of = seats_all
        chunk = lines[a:b]
        # block starts at each "Vote For" line (retention questions have none and are never read)
        starts = [i for i, ln in enumerate(chunk) if re.match(r"^\s*Vote For\s*\d+", ln)]
        found = {}
        for k, s in enumerate(starts):
            e = starts[k + 1] if k + 1 < len(starts) else len(chunk)
            prev = starts[k - 1] if k else 0
            # title: the last title line between the previous block start and this one (inclusive)
            contest = None
            for ln in chunk[prev + 1 if k else 0:s + 1]:
                c = title_contest(ln)
                if c:
                    contest = c
            if contest is None:
                continue
            block = chunk[s:e]
            seats = int(re.match(r"^\s*Vote For\s*(\d+)", chunk[s]).group(1))
            tm = None
            tags = []
            ints = []
            for ln in block:
                if SKIP.match(ln):
                    continue
                m2 = re.search(r"Total Votes\s+(\d{1,3}(?:,\d{3})*|\d+)", ln)
                rest = ln
                if m2 and tm is None:
                    tm = int(m2.group(1).replace(",", ""))
                    rest = ln[:m2.start()] + " " + ln[m2.end():]
                elif re.match(r"^\s*Vote For", ln):
                    continue
                tags += TAG.findall(rest)
                toks = rest.split()
                nums = [t for t in toks if INT.match(t)]
                if len(nums) >= 3:
                    ints.append(int(nums[0].replace(",", "")))
            if contest in found:
                fails[(code, contest)] = "race block found twice"
                continue
            if tm is None:
                fails[(code, contest)] = "no Total Votes line"
                continue
            n = len(tags)
            if n == 0 or len(ints) < n:
                fails[(code, contest)] = f"{n} candidates but {len(ints)} totals"
                continue
            cvotes = ints[:n]
            if sum(cvotes) != tm:
                fails[(code, contest)] = f"candidate sum {sum(cvotes)} != Total Votes {tm}"
                continue
            found[contest] = list(zip(tags, cvotes, block_names(block, n)))
            seats_of[contest] = seats
        for c in list(found):
            if (code, c) in fails:      # a second block of the same race failed: drop both
                del found[c]
        res[code] = (name, found)
    return res, fails, seats_all


def block_names(block, n):
    """The candidate names of one race block, in printed order, as written before each party tag (the text layer
    puts names, tags and numbers on shifted lines; numbers, column heads and Undervote/Overvote are dropped).
    Returns n names, or [''] * n when the names cannot be lined up with the tags."""
    words = []
    for ln in block:
        if SKIP.match(ln) or re.match(r"^\s*Vote For", ln) or "Total Votes" in ln or re.search(r"\bED\s+A\s+EV\b", ln):
            continue
        for tok in ln.split():
            if tok in ("Undervote", "Overvote", "EV", "ED", "Total") or re.fullmatch(r"[\d,.%]+", tok):
                continue
            words.append(tok)
    out, cur = [], []
    for tok in words:
        m = TAG.fullmatch(tok)
        if m:
            out.append(" ".join(cur))
            cur = []
        else:
            cur.append(tok)
    return out if len(out) == n else [""] * n


# Candidate names for the 2022 statewide and federal races (printed on the county report's summary pages; each is
# checked against the text below). Other 2022 races take their names from the guide's results.csv (same contest).
CAND_2022 = {
    "us-senate": {"D": "THOMAS M MCDERMOTT JR", "R": "TODD YOUNG", "L": "JAMES M SCENIAK"},
    "secretary-of-state": {"D": "DESTINY WELLS", "R": "DIEGO MORALES", "L": "JEFFREY MAURER"},
    "auditor": {"D": "ZENAI BROOKS", "R": "TERA K KLUTZ", "L": "JOHN ANDREW SCHICK"},
    "treasurer": {"D": "JESSICA MCCLELLAN", "R": "DANIEL ELLIOTT"},
    "us-house": {"D": "PAUL D STEURY", "R": "RUDOLPH (RUDY) YAKYM III", "L": "WILLIAM E HENRY"},
    "us-house-special": {"D": "PAUL STEURY", "R": "RUDOLPH (RUDY) YAKYM III", "L": "WILLIAM E HENRY"},
}


def pretty_name(n: str) -> str:
    t = n.title()
    t = re.sub(r"\bMc([a-z])", lambda m: "Mc" + m.group(1).upper(), t)
    t = t.replace(" Jr", " Jr.")
    return t[:-4] + " III" if t.endswith(" Iii") else (t[:-3] + " II" if t.endswith(" Ii") else t)


def norm_party_2022(tag):
    return {"DEM": "D", "REP": "R", "LIB": "L", "W": "W"}.get(tag, "O")


# ---- 2020 county report (OCR) ----------------------------------------------------------------
OCR_2020 = sorted((SRC / "openelections-sources-in").glob("2020-GE-St-Joseph-Precinct.ocr*.txt"))


def want_2020(title: str):
    """Race titles read from the 2020 report: its county offices (the rule's 2020 county races) and, as a cross-check
    of the OpenElections file only, the state legislative races."""
    t = re.sub(r"\s+", " ", title.upper()).strip()
    m = re.search(r"ST\. ?JOSEPH COUNTY (CORONER|SURVEYOR|RECORDER|TREASURER)$", t)
    if m:
        return "county-" + m.group(1).lower()
    m = re.search(r"ST\. ?JOSEPH COUNTY COMMISSIONER DISTRICT (\d)$", t)
    if m:
        return "county-commissioner-" + m.group(1)
    # council districts are letters A-I; OCR reads a lone 'I' as T, L, 1, | or ! (no district uses those letters)
    m = re.search(r"ST\. ?JOSEPH COUNTY COUNCIL DISTRICT ([A-I]|[TL1|!])$", t)
    if m:
        return "county-council-" + ("i" if m.group(1) in "TL1|!" else m.group(1).lower())
    # page-1 races, read only to confirm which precinct a page run belongs to (compared with OpenElections)
    if t == "UNITED STATES PRESIDENT & VICE PRESIDENT":
        return "president"
    if t == "GOVERNOR & LT. GOVERNOR":
        return "governor"
    if t == "ATTORNEY GENERAL":
        return "attorney-general"
    if re.fullmatch(r"UNITED STATES HOUSE OF REPRESENTATIVE 2ND DISTRICT", t):
        return "us-house"
    m = re.search(r"^STATE SENATOR DISTRICT (\d+)$", t)
    if m:
        return "state-senate-" + m.group(1)
    m = re.search(r"^STATE REPRES\w* DISTRICT (\d+)$", t)
    if m:
        return "state-house-" + m.group(1)
    return None


# ---- geometry ------------------------------------------------------------------------------
def polys(g):
    return [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]


def pip(x, y, ring):
    c, j = False, len(ring) - 1
    for i in range(len(ring)):
        xi, yi, xj, yj = ring[i][0], ring[i][1], ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def inside(x, y, g):
    for poly in polys(g):
        xs = [p[0] for p in poly[0]]
        ys = [p[1] for p in poly[0]]
        if x < min(xs) or x > max(xs) or y < min(ys) or y > max(ys):
            continue
        if pip(x, y, poly[0]) and not any(pip(x, y, h) for h in poly[1:]):
            return True
    return False


def sample_points(g, n=14):
    pts = []
    allp = [p for poly in polys(g) for p in poly[0]]
    x0, x1 = min(p[0] for p in allp), max(p[0] for p in allp)
    y0, y1 = min(p[1] for p in allp), max(p[1] for p in allp)
    for i in range(n):
        for j in range(n):
            x, y = x0 + (x1 - x0) * (i + .5) / n, y0 + (y1 - y0) * (j + .5) / n
            if inside(x, y, g):
                pts.append((x, y))
    if not pts:  # tiny polygon: use its vertex mean
        pts = [(sum(p[0] for p in allp) / len(allp), sum(p[1] for p in allp) / len(allp))]
    return pts


# ---- official totals (results.csv) ------------------------------------------------------------
def load_official(edir: Path):
    """{contest_id: {"status": set, "parties": {party: votes}, "names": {party: [names]}}}. Parties are the guide's
    codes, folded the way the precinct data is: D, R, L, W kept; I and other ballot parties -> O."""
    out = {}
    for r in csv.DictReader(open(edir / "results.csv", encoding="utf-8-sig")):
        if not r["votes"].strip() or r["party"] in ("", "NP"):
            continue
        p = r["party"] if r["party"] in ("D", "R", "L", "W") else "O"
        e = out.setdefault(r["contest_id"], {"status": set(), "parties": defaultdict(int), "names": defaultdict(list),
                                             "cands": {}, "winners": [], "vote_for": r["vote_for"]})
        e["status"].add(r["status"])
        e["parties"][p] += int(r["votes"])
        if p != "W":
            e["names"][p].append(r["candidate"])
            e["cands"][r["candidate"]] = (p, int(r["votes"]))
        if r["winner"] == "Y":
            e["winners"].append((r["candidate"], p))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edition", default="st-joseph")
    args = ap.parse_args()
    edir = ROOT / "data" / "editions" / args.edition
    log = []
    out_rows = []          # (election_id, code, name, contest, party, ballot party, candidate, votes, source)
    precinct_names = {}
    have = defaultdict(lambda: defaultdict(set))   # eid -> contest -> codes
    race_sums = {}                                 # (eid, contest) -> {party: county sum}
    corrected = set()                              # (eid, code, contest, party) rows fixed from the county report
    failures = []                                  # (eid, code, contest, reason): precinct left out of that race
    official = load_official(edir)

    def display_name(eid, contest, party, source_name):
        """Candidate name shown on the map: the guide's results.csv spelling when the race has an official row for
        that party (one candidate per party), else the source's own spelling."""
        if contest in FEDERAL or contest in STATEWIDE:
            return source_name
        e = official.get(official_id(eid, contest))
        if e and len(e["names"].get(party, [])) == 1:
            return e["names"][party][0]
        return source_name

    def official_cands(eid, contest):
        """{name: (party, votes)} from results.csv (official rows) or CANVASS_2022_LOCAL; None when neither has it."""
        if eid == "2022g" and contest in CANVASS_2022_LOCAL:
            return dict(CANVASS_2022_LOCAL[contest])
        e = official.get(official_id(eid, contest))
        return dict(e["cands"]) if e and e["status"] == {"official"} else None

    def local_name(contest, party, printed):
        """Township and town races can have several candidates of one party: the name printed in the precinct
        report is matched to the official candidate list (same party, most shared name words, one best match)."""
        cands = official_cands("2022g", contest)
        if party == "W":    # write-ins are not on the official candidate lists
            return pretty_name(printed) if printed else ""
        if not printed or not cands:
            return pretty_name(printed) if printed else ""
        words = set(re.findall(r"[A-Z]{2,}", printed.upper()))
        scored = sorted(((len(words & set(re.findall(r"[A-Z]{2,}", nm.upper()))), nm) for nm, (pp, _v) in cands.items()
                         if pp == party), reverse=True)
        if scored and scored[0][0] > 0 and (len(scored) == 1 or scored[1][0] < scored[0][0]):
            return scored[0][1]
        name_misses.append(f"2022g {contest}: printed name {printed!r} ({party}) not matched to {sorted(cands)}")
        return pretty_name(printed)

    name_misses = []

    # 2024 State Senate rows carry no district in the OpenElections file: the district is the one whose results.csv
    # candidates include the surname (each surname is unique among the 2024 State Senate candidates; checked).
    senate_by_name = {}
    for cid, e in official.items():
        m = re.fullmatch(r"2024g-state-senate-(\d+)", cid)
        if m:
            for nm_list in e["names"].values():
                for nm in nm_list:
                    sn = nm.split()[-1].lower()
                    if senate_by_name.get(sn, m.group(1)) != m.group(1):
                        raise SystemExit(f"2024 State Senate surname {sn} is in two districts")
                    senate_by_name[sn] = m.group(1)

    # ---------------- 2024 and 2020 (OpenElections)
    used_office_fix = {}
    oe_2020 = None
    for eid, fn, canv in (("2024g", "20241105__in__general__st_joseph__precinct.csv", CANVASS_2024_GOV),
                          ("2020g", "20201103__in__general__st_joseph__precinct.csv", CANVASS_2020_GOV)):
        rows, names = read_oe(SRC / "openelections-in" / fn, eid, log,
                              senate_by_name if eid == "2024g" else None, used_office_fix)
        for (ceid, code, contest, party), (was, now, where) in OE_CORRECTIONS.items():
            if ceid != eid:
                continue
            lst = rows[code][contest]
            hits = [i for i, row in enumerate(lst) if row[0] == party]
            if len(hits) != 1 or lst[hits[0]][2] != was:
                raise SystemExit(f"OE correction {ceid} {code} {contest} {party}: expected OpenElections value {was}, "
                                 f"found {[lst[i][2] for i in hits]}; re-check against the county report")
            p, c, _v, bp = lst[hits[0]]
            lst[hits[0]] = (p, c, now, bp)
            corrected.add((eid, code, contest, party))
            log.append(f"{eid} {code} {contest} {party}: OpenElections {was} corrected to {now} ({where})")
        for (ceid, code, office, dist), (o2, d2, where) in OE_OFFICE_CORRECTIONS.items():
            if ceid != eid:
                continue
            if (ceid, code, office, dist) not in used_office_fix:
                raise SystemExit(f"OE office correction {ceid} {code} {office} {dist}: row not found in OpenElections; "
                                 "re-check against the county report")
            log.append(f"{eid} {code}: OpenElections '{office}, district {dist}' rows filed as '{o2}, district {d2}' ({where})")
            corrected.update((eid, code, f"state-house-{d2}" if o2 == "State Representative" else f"state-senate-{d2}", p)
                             for p in ("D", "R", "L", "O", "W"))
        precinct_names.update({(eid, c): n for c, n in names.items()})
        if eid == "2020g":
            oe_2020 = rows
        tot = defaultdict(int)
        fam = defaultdict(dict)    # (code, family) -> contest: a precinct is in one district of each kind
        for code, d in rows.items():
            for contest, lst in d.items():
                f = district_family(contest)
                if f:
                    if fam[(code, f)] and contest not in fam[(code, f)]:
                        raise SystemExit(f"{eid} {code}: in two districts of {f}: {list(fam[(code, f)])} and {contest}")
                    fam[(code, f)][contest] = True
                for party, cand, v, bp in lst:
                    out_rows.append((eid, code, names[code], contest, party, bp,
                                     display_name(eid, contest, party, cand), v, SOURCE_IDS[eid]))
                    if contest == "governor":
                        tot[party] += v
                have[eid][contest].add(code)
        for p, v in canv.items():
            if tot.get(p) != v:
                raise SystemExit(f"{eid} governor {p}: precinct sum {tot.get(p)} != canvass {v}")
        log.append(f"{eid}: county Governor sums match the official canvass exactly {dict(canv)}")
        allc = set(rows)
        for contest in sorted({c for d in rows.values() for c in d}):
            # county-wide races must be on every precinct's ballot
            if countywide(contest) and have[eid][contest] != allc:
                raise SystemExit(f"{eid} {contest}: on {len(have[eid][contest])} of {len(allc)} precincts, not county-wide")
            csum = defaultdict(int)
            for code, d in rows.items():
                for party, _cand, v, _bp in d.get(contest, []):
                    csum[party] += v
            race_sums[(eid, contest)] = dict(csum)

    # ---------------- 2020 county offices (county's 2020 Precinct Summary Report, OCR)
    known_2020 = set(oe_2020)
    accepted, failed, ocr_names, ocr_pages, ocr_log = parse_reads(OCR_2020, want_2020, known_2020, name_to_code_2020)
    log += [f"2020g OCR: {x}" for x in ocr_log]
    if not OCR_2020:
        raise SystemExit("no OCR reads of the 2020 report found (run tools/ocr_2020_precinct_report.py)")
    log.append(f"2020g OCR: {len(OCR_2020)} reads ({', '.join(p.name for p in OCR_2020)}); "
               f"{len(accepted)} race boxes accepted, {len(failed)} not")
    # identity check: a page run's precinct code is confirmed only when its President, Governor, Attorney General,
    # U.S. House and state legislative boxes (those the OCR read) equal the OpenElections rows for that code, with at
    # least one box read and none differing
    ident = defaultdict(lambda: [0, []])
    for (code, contest), rows_ in accepted.items():
        if contest in ("president", "governor", "attorney-general", "us-house") or contest.startswith("state-"):
            # write-ins and zero-vote rows left aside (OCR can drop a '0  0%' row; zeros do not change any sum)
            oe = sorted((r[0], r[2]) for r in oe_2020.get(code, {}).get(contest, []) if r[0] != "W" and r[2])
            rep = sorted((p, v) for p, _n, v in rows_ if p != "W" and v)
            if oe == rep:
                ident[code][0] += 1
            else:
                ident[code][1].append(f"{contest}: OpenElections {oe} vs report {rep}")
    unconfirmed = {c for c in {k[0] for k in accepted} if ident[c][0] == 0 or ident[c][1]}
    log.append(f"2020g OCR: precinct identity confirmed for {len({k[0] for k in accepted}) - len(unconfirmed)} page runs "
               f"(page-1 and legislative boxes equal OpenElections); not confirmed: "
               f"{sorted(unconfirmed) or 'none'}")
    for c in sorted(unconfirmed):
        log.append(f"2020g OCR:   {c}: {ident[c][1] or 'no page-1 box read'}")
    sums20 = defaultdict(lambda: defaultdict(int))
    for (code, contest), rows_ in sorted(accepted.items()):
        if not contest.startswith("county-"):
            continue
        if code in unconfirmed:
            failures.append(("2020g", code, contest, "precinct identity of the report pages not confirmed"))
            continue
        for party, _nm, v in rows_:
            out_rows.append(("2020g", code, precinct_names[("2020g", code)], contest, party,
                             {"D": "DEM", "R": "REP", "L": "LIB", "W": "W", "O": "IND"}[party],
                             display_name("2020g", contest, party, ""), v, OCR_SOURCE))
            sums20[contest][party] += v
        have["2020g"][contest].add(code)
    for contest, s in sums20.items():
        race_sums[("2020g", contest)] = dict(s)
    for (code, contest), why in sorted(failed.items()):
        if contest.startswith("county-"):
            failures.append(("2020g", code, contest, why))
    # cross-check: the 2020 state legislative races in OpenElections against the same boxes in the county report
    xs_same, xs_diff = 0, []
    for (code, contest), rows_ in sorted(accepted.items()):
        if not contest.startswith("state-"):
            continue
        oe = sorted((p, v) for p, _c, v, _b in oe_2020.get(code, {}).get(contest, []) if p != "W" and v)
        rep = sorted((p, v) for p, _n, v in rows_ if p != "W" and v)
        if oe == rep:
            xs_same += 1
        else:
            xs_diff.append(f"{code} {contest}: OpenElections {oe} vs report page {ocr_pages.get((code, contest))} {rep}")
    log.append(f"2020g cross-check of OpenElections state legislative rows against the county report: {xs_same} precinct "
               f"boxes equal, {len(xs_diff)} differ")
    log += [f"2020g   differs: {x}" for x in xs_diff]

    # ---------------- 2022
    txt = (SRC / "sjc-county" / "57716.txt").read_text(encoding="utf-8", errors="replace")
    for cs in CAND_2022.values():
        for nm in cs.values():
            if nm not in txt:
                log.append(f"WARNING 2022 candidate name not found in report text: {nm}")
    res, fails, seats_2022 = parse_2022(SRC / "sjc-county" / "57716.txt", log)
    sums = defaultdict(lambda: defaultdict(int))
    tag_of = {"D": "DEM", "R": "REP", "L": "LIB", "W": "W"}
    for code, (name, found) in sorted(res.items()):
        precinct_names[("2022g", code)] = name.title()
        for contest in COUNTYWIDE_2022:
            if contest not in found:
                failures.append(("2022g", code, contest, fails.get((code, contest), "race block not found")))
        for (fc, contest), why in fails.items():
            if fc == code and contest not in COUNTYWIDE_2022:
                failures.append(("2022g", code, contest, why))
        for contest, lst in found.items():
            for tag, v, printed in lst:
                p = norm_party_2022(tag)
                if contest in CAND_2022:
                    cand = pretty_name(CAND_2022[contest][p]) if p in CAND_2022[contest] else ""
                elif contest.startswith(LOCAL_FAMILIES):
                    cand = local_name(contest, p, printed)
                else:
                    cand = display_name("2022g", contest, p, "") if p != "W" else ""
                out_rows.append(("2022g", code, precinct_names[("2022g", code)], contest, p,
                                 tag_of.get(p, tag), cand, v, SOURCE_IDS["2022g"]))
                sums[contest][p] += v
            have["2022g"][contest].add(code)
    for contest, s in sums.items():
        race_sums[("2022g", contest)] = dict(s)
    verify = {}
    for contest, exp in CANVASS_2022.items():
        got = {p: sums[contest].get(p, 0) for p in exp}
        verify[contest] = (got, exp, got == exp)

    for key in race_sums:
        if not known_contest(key[1]):
            raise SystemExit(f"{key}: contest outside the rule's list")

    # ---------------- county (or district) sums against the official totals
    official_check = {}     # (eid, contest) -> (got, expected, match, note)
    summary_check = {}      # 2022 township/town races checked against the report's summary page
    cand_check = {}         # (eid, contest) -> (candidate sums, official candidate totals, match)
    unofficial = {}         # (eid, contest) -> note: results.csv has the race but not with status "official"
    for key, got_all in sorted(race_sums.items()):
        eid, contest = key
        cid = official_id(eid, contest)
        e = official.get(cid) if cid else None
        if e is None:
            continue
        if e["status"] != {"official"}:
            unofficial[key] = (f"the guide's county total for this race ({cid}) has status {'/'.join(sorted(e['status']))}, "
                               "not official, so it is not used as a check")
            same = all(got_all.get(p, 0) == v for p, v in e["parties"].items())
            log.append(f"{eid} {contest}: precinct sums {'equal' if same else 'differ from'} the non-official "
                       f"results.csv figures {dict(e['parties'])} (not counted as a check)")
            continue
        exp = dict(e["parties"])
        if key in RESULTS_CSV_MISREADS:
            if exp == RESULTS_CSV_MISREADS[key][0]:
                log.append(f"{eid} {contest}: {RESULTS_CSV_MISREADS[key][1]}")
                continue
            # results.csv was corrected: check against it as for every other race, and drop the misread note
            log.append(f"{eid} {contest}: results.csv no longer has the misread figure; RESULTS_CSV_MISREADS can go")
        got = {p: got_all.get(p, 0) for p in exp}
        extra = {p: v for p, v in got_all.items() if p not in exp and v}
        note = ""
        if set(extra) - {"W"}:
            ok = False
            note = f"precinct data has parties the official rows do not: {extra}"
        else:
            ok = got == exp
            if extra:
                note = f"write-ins ({extra['W']}) are not in the official rows and are not checked"
        official_check[key] = (got, exp, ok, note)
    # 2022 township and town races that results.csv lacks: party sums against the summary page (CANVASS_2022_LOCAL)
    for contest, cands in CANVASS_2022_LOCAL.items():
        key = ("2022g", contest)
        if key not in race_sums:
            raise SystemExit(f"{key}: in CANVASS_2022_LOCAL but no precinct results were read")
        exp = defaultdict(int)
        for _nm, (pp, vv) in cands.items():
            exp[pp] += vv
        exp = dict(exp)
        got = {pp: race_sums[key].get(pp, 0) for pp in exp}
        extra = {pp: vv for pp, vv in race_sums[key].items() if pp not in exp and vv}
        ok = got == exp and not (set(extra) - {"W"})
        summary_check[key] = (got, exp, ok, f"write-ins ({extra['W']}) are not on the summary page and are not checked"
                              if extra.get("W") else "")
    # every candidate of a township or town race against the official candidate totals (the names in the precinct
    # report are matched to the official list; a wrong match would show up here)
    cand_sums = defaultdict(lambda: defaultdict(int))
    for eid, code, _nm, contest, party, _bp, cand, v, _src in out_rows:
        if contest.startswith(LOCAL_FAMILIES) and party != "W":
            cand_sums[(eid, contest)][cand] += v
    for key, sums_ in sorted(cand_sums.items()):
        exp = official_cands(*key)
        if exp is None:
            continue
        got = dict(sums_)
        want = {nm: vv for nm, (_pp, vv) in exp.items()}
        cand_check[key] = (got, want, got == want)
    federal_check = {}
    for key, exp in CANVASS_FEDERAL.items():
        got = dict(race_sums.get(key, {}))
        federal_check[key] = (got, exp, got == exp)

    # what each race's county sum was checked against (read by tools/build_map.py for the page's county lines)
    county_check = {}
    for (eid, c) in sorted(race_sums):
        basis, oks, note = [], [], ""
        if (eid, c) in official_check:
            basis.append("county canvass in the guide's results data")
            oks.append(official_check[(eid, c)][2])
            note = official_check[(eid, c)][3]
        if eid == "2022g" and c in CANVASS_2022:
            basis.append("county summary pages of the 2022 report")
            oks.append(verify[c][2])
        if eid in ("2020g", "2024g") and c == "governor":
            basis.append("county canvass")
            oks.append(True)
        if (eid, c) in federal_check:
            basis.append("county canvass (official summary report)")
            oks.append(federal_check[(eid, c)][2])
        if (eid, c) in summary_check:
            basis.append("summary pages of the 2022 report (official results)")
            oks.append(summary_check[(eid, c)][2])
            note = note or summary_check[(eid, c)][3]
            if (eid, c) in RESULTS_CSV_MISREADS and (eid, c) not in official_check:
                note = "; ".join(x for x in (note, RESULTS_CSV_MISREADS[(eid, c)][1]) if x)
        if (eid, c) in cand_check:
            oks.append(cand_check[(eid, c)][2])
        if not basis and (eid, c) in unofficial:
            note = unofficial[(eid, c)]
        seats = seats_2022.get(c, 1) if eid == "2022g" else 1
        winners, wnote = [], ""
        if seats > 1:
            e = official.get(official_id(eid, c))
            if eid == "2022g" and c in CANVASS_2022_LOCAL:
                ranked = sorted(CANVASS_2022_LOCAL[c].items(), key=lambda kv: -kv[1][1])
                if len(ranked) > seats and ranked[seats - 1][1][1] == ranked[seats][1][1]:
                    raise SystemExit(f"{eid} {c}: tie for the last seat")
                winners = [[nm, pp] for nm, (pp, _v) in ranked[:seats]]
                wnote = f"top {seats} by votes on the summary page"
            elif e and e["winners"]:
                winners = [[nm, pp] for nm, pp in e["winners"]]
                wnote = "the guide's results data"
        county_check[f"{eid}|{c}"] = {"checked_against": basis, "match": bool(basis) and all(oks), "note": note,
                                      "district": district_family(c) is not None, "seats": seats,
                                      "winners": winners, "winners_from": wnote}

    # ---------------- precinct areas
    vtd = json.load(open(SRC / "tigerweb-vtd2020" / "vtd.json", encoding="utf-8"))["features"]
    tw = json.load(open(ROOT / "sources" / "boundaries" / "townships.geojson", encoding="utf-8"))["features"]
    pl = json.load(open(ROOT / "sources" / "boundaries" / "places_incorporated.geojson", encoding="utf-8"))["features"]
    pl = [f for f in pl if f["properties"]["BASENAME"] not in ("La Paz", "Bremen")]
    areas = {}
    for f in vtd:
        nm = f["properties"]["NAME"]
        code = nm.split()[0]
        pts = sample_points(f["geometry"])
        tcount = defaultdict(int)
        pcount = defaultdict(int)
        for x, y in pts:
            for t in tw:
                if inside(x, y, t["geometry"]):
                    tcount[t["properties"]["BASENAME"]] += 1
                    break
            for p in pl:
                if inside(x, y, p["geometry"]):
                    pcount[p["properties"]["BASENAME"]] += 1
                    break
        n = len(pts)
        township = max(tcount, key=tcount.get) if tcount else None
        place, share = None, 0.0
        if pcount:
            place = max(pcount, key=pcount.get)
            share = pcount[place] / n
        areas[code] = {"name_vtd": nm, "township": township,
                       "township_share": round(tcount[township] / n, 3) if township else 0,
                       "place": place if share >= 0.5 else None,
                       "place_share": round(share, 3) if place else 0,
                       "straddles": bool(place) and 0.03 < share < 0.97,
                       "nv": "(NV)" in nm}

    # unmatched precincts per year
    unm = {}
    for eid in ("2020g", "2022g", "2024g"):
        codes = {c for (e, c) in precinct_names if e == eid}
        unm[eid] = sorted(c for c in codes if c not in areas)
    unmatched_vtd = {eid: sorted(c for c, a in areas.items() if c not in {k for (e, k) in precinct_names if e == eid} and not a["nv"])
                     for eid in ("2020g", "2022g", "2024g")}

    # write CSV
    dest = edir / "precinct_results.csv"
    with open(dest, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["election_id", "precinct_code", "precinct_name", "contest", "vote_for", "party", "ballot_party",
                    "candidate", "votes", "source_id"])
        for eid, code, name, contest, party, bp, cand, v, src in sorted(out_rows):
            if (eid, code, contest, party) in corrected:
                src = CORRECTION_SOURCE
            vf = seats_2022.get(contest, 1) if eid == "2022g" else 1
            w.writerow([eid, code, name, contest, vf, party, bp, cand, v, src])
    excluded = {f"{eid}|{code}|{contest}": why for eid, code, contest, why in failures}
    adest = edir / "derived" / "precinct_areas.json"
    adest.write_text(json.dumps({"note": "Township = largest overlap of the Census 2020 VTD with township polygons; place = incorporated place "
                                         "holding at least 50% of the VTD area (grid-sampled). Straddlers have place_share between 0.03 and 0.97. "
                                         "'excluded' lists precinct/race pairs left out because a check failed.",
                                 "areas": areas, "excluded": excluded,
                                 "county_check": county_check}, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")

    # ---------------- report
    print("== log")
    for line in log:
        print(" ", line)
    print("== 2022 parse")
    print(f"  precinct headers found: {len(res)}; race-level failures: {len(fails)}")
    for c, (got, exp, okk) in verify.items():
        print(f"  county sum {c}: {'MATCH' if okk else 'MISMATCH'} got {got} expected {exp}")
    print(f"== precinct/race pairs left out because a check failed ({len(failures)})")
    for eid, code, contest, why in failures:
        print(f"  {eid} {code} {contest}: {why}")
    print("== county or district sums vs the guide's official totals (results.csv, status official)")
    for (eid, c), (got, exp, okk, note) in sorted(official_check.items()):
        print(f"  {eid} {c}: {'MATCH' if okk else 'MISMATCH'} got {got} expected {exp}" + (f" ({note})" if note else ""))
    print("== 2022 township/town races vs the report's summary pages (CANVASS_2022_LOCAL)")
    for (eid, c), (got, exp, okk, note) in sorted(summary_check.items()):
        print(f"  {eid} {c}: {'MATCH' if okk else 'MISMATCH'} got {got} expected {exp}" + (f" ({note})" if note else ""))
    print("== township/town races: every candidate's sum vs the official candidate totals")
    for (eid, c), (got, exp, okk) in sorted(cand_check.items()):
        print(f"  {eid} {c}: {'MATCH' if okk else 'MISMATCH'}" + ("" if okk else f" got {got} expected {exp}"))
    for line in name_misses:
        print("  NAME NOT MATCHED:", line)
    print("== federal races vs the county's official summary reports (every party, write-ins included)")
    for (eid, c), (got, exp, okk) in sorted(federal_check.items()):
        print(f"  {eid} {c}: {'MATCH' if okk else 'MISMATCH'} got {dict(sorted(got.items()))} expected {dict(sorted(exp.items()))}")
    print("== races with no official county total (sums reported, not verified; shown as 'county sum not checked')")
    for k in sorted(county_check):
        if not county_check[k]["checked_against"]:
            eid, c = k.split("|")
            print(f"  {eid} {c}: {dict(sorted(race_sums[(eid, c)].items()))}" +
                  (f" ({county_check[k]['note']})" if county_check[k]["note"] else ""))
    print("== precinct codes with no VTD polygon:", {k: v for k, v in unm.items()})
    print("== VTDs (non-NV) with no results:", {k: len(v) for k, v in unmatched_vtd.items()})
    st = [(c, a["place"], a["place_share"], a["township"]) for c, a in areas.items() if a["straddles"]]
    print(f"== straddling precincts ({len(st)}):")
    for s in sorted(st, key=lambda s: (s[1] or "", s[0])):
        print("  ", s)
    print(f"wrote {dest} ({dest.stat().st_size:,} bytes) rows={len(out_rows)}; {adest}")
    bad = [k for k, v in verify.items() if not v[2]] + [k for k, v in official_check.items() if not v[2]] + \
          [k for k, v in federal_check.items() if not v[2]] + [k for k, v in summary_check.items() if not v[2]] + \
          [k for k, v in cand_check.items() if not v[2]] + (["candidate names"] if name_misses else [])
    if bad:
        print(f"FAILED: {len(bad)} race sum(s) differ from the official figures: {bad}")
        sys.exit(1)


if __name__ == "__main__":
    main()
