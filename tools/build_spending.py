"""Money in and money out for each local government: actual 2024/2025 receipts and disbursements.

Reads the Gateway "Annual Financial Reports" files for St. Joseph County, pipe-delimited:
  Disbursements by Fund  sources/money/gateway_afr_disbursements_byfund_{2024,2025}_county71.psv (MON-061, MON-060)
  Receipts               sources/money/gateway_afr_receipts_{2024,2025}_county71.psv            (MON-064, MON-063)
and writes ONE file: data/editions/st-joseph/spending_breakdowns.csv

    unit_id,year,view,category,amount,share,basis,status,source_ids,notes
    view = income | income_excluded | passthrough_in_detail          (money in)
         | by_purpose | by_type | spending_excluded | passthrough_detail   (money out)
  *_excluded rows: the money that is not the unit's own, by kind (G_* groups); *_detail rows: the funds
  inside the "collected for other governments and passed on" group (top 6 + Other).
  Income adds: Transfers In, interfund loans, investments and cost allocations go to "moved between own
  funds"; bond and loan proceeds go to "borrowed". The fund rule below is the SAME for both sides.
  A year whose receipts are known to be misreported is kept but marked (basis ends "_held", notes start
  "HELD"); the site then shows the previous year's income (HELD_INCOME).

Counting rule (what is NOT the unit's own spending)
---------------------------------------------------
1. Whole funds are left out by fund number where the Indiana State Board of Accounts (SBOA) chart of
   accounts for that kind of unit defines the range (MON-062 county funds table, MON-065 school manual
   part 4, MON-066 cities and towns fund list, MON-067 libraries fund list; MON-068 county chart
   instructions):
     settlement and remittance funds (money collected for other governments or the state),
     payroll withholding / clearing funds, internal service funds (self-insurance and the like),
     pension, private-purpose trust and custodial funds (money held for others).
   Where the chart is silent (a unit numbers its funds its own way, or the type has no chart we could
   find), the fund is reviewed by name: NAMED_* below, each with a written reason.
2. Inside the funds that are counted, lines that only move money between the unit's own funds or
   accounts are left out: section 4 of the file (Transfers Out and, for schools, other financing uses),
   D704 transfer out, D705/D706 interfund loans and D900 purchase of investments.
3. County funds that another covered unit reports as its own in the same file (same fund number, same
   name, same amount) are counted once, with that unit.
For every unit and year: counted + not counted = the file total, to the cent (checked; the build fails
otherwise).

Categories
----------
by_type (civil units): the file's object classes mapped to plain labels (TYPE_LABELS).
by_purpose (civil units): the fund that paid, by an ordered rule table (PURPOSE_RULES); the first rule
that matches wins and every fund lands somewhere ("Other" last). Schools: the file's functional classes
(SCHOOL_PURPOSE); the school file has no object-class split, so schools get no by_type rows.
Each chart keeps the 6 largest categories and folds the rest into "Other" (fold_top()).

Unit ids are the money-file ids budgets.csv uses, read from the UNITS table in tools/build_money.py
WITHOUT running that script (ast.literal_eval of the assignment): build_money.py regenerates other
files and must never be run from here.

Run:  python -P -E tools/build_spending.py            (writes the CSV, prints review notes)
      python -P -E tools/build_spending.py --dry-run  (prints only)
"""
from __future__ import annotations

import ast
import csv
import re
import sys
from collections import OrderedDict, defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "sources" / "money"
OUT = ROOT / "data" / "editions" / "st-joseph" / "spending_breakdowns.csv"
YEARS = (2024, 2025)
FILES = {y: SRC / f"gateway_afr_disbursements_byfund_{y}_county71.psv" for y in YEARS}
RECEIPT_FILES = {y: SRC / f"gateway_afr_receipts_{y}_county71.psv" for y in YEARS}
FILE_SOURCE = {2025: "MON-060", 2024: "MON-061"}           # disbursements by fund
RECEIPT_SOURCE = {2025: "MON-063", 2024: "MON-064"}        # receipts
CHART_SOURCES = {"county": ["MON-062", "MON-068"], "city": ["MON-066"], "town": ["MON-066"],
                 "school": ["MON-065"], "library": ["MON-067"]}
HEADER = ["unit_id", "year", "view", "category", "amount", "share", "basis", "status", "source_ids", "notes"]
CENT = Decimal("0.01")
TOP_N = 6
OTHER = "Other"

# ---------------------------------------------------------------- units

# Bodies in the county file that the guide does not cover (multi-county, or not in the guide's list
# of governments). Listed in the report; never written.
SKIP_UNITS = {
    "MICHIANA AREA COUNCIL OF GOVERNMENT (6-30)": "multi-county council of governments (MACOG)",
    "ELKHART AND ST. JOSEPH COUNTIES HEAD START CONSORTIUM (6-30)": "two-county Head Start consortium",
    "ST. JOSEPH RIVER BASIN COMMISSION (6-30)": "multi-county river basin commission",
    "ST. JOSEPH COUNTY HOUSING CONSORTIU": "housing consortium; no budgets.csv or units.csv entry",
    "ST JOSEPH CO SOIL AND WATER CONSERVATION DISTRICT": "soil and water district; no budgets.csv or units.csv entry",
}


def load_unit_map() -> dict[str, str]:
    """UNITS from tools/build_money.py (Gateway unit name -> money id), read without executing it."""
    tree = ast.parse((ROOT / "tools" / "build_money.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "UNITS" for t in node.targets):
            units = ast.literal_eval(node.value)
            return {k.upper(): v[0] for k, v in units.items()}
    raise SystemExit("UNITS table not found in tools/build_money.py")


def kind_of(afr_unit_type: str) -> str:
    return {"1": "county", "2": "city", "3": "town", "5": "school", "6": "library", "7": "township"}.get(afr_unit_type, "special")


# units whose fund numbers do not follow their type's SBOA chart, so every fund is reviewed by name
OFF_CHART = {
    "city-south-bend": "South Bend numbers its funds with its own three-digit scheme (101 General ... 760), "
                       "not the SBOA cities and towns chart.",
    "town-indian-village": "Indian Village numbers its funds 1-6, not the SBOA cities and towns chart.",
}
# unit types with no SBOA fund-number chart found (named review for every unit of the type)
NO_CHART_KINDS = {"township", "special"}

# ---------------------------------------------------------------- exclusion groups (plain words)
G_SETTLE = "Collected for other governments and passed on (tax settlement and distributions)"
G_PAYROLL = "Payroll withholding and clearing accounts"
G_INTERNAL = "Self-insurance and other internal service funds"
G_TRUST = "Pension, trust and custodial funds held for others"
G_TRANSFER = "Moved between the unit's own funds (transfers, loans, investments)"
G_OTHERUNIT = "Reported by another unit as its own"
G_BORROW = "Borrowed (bond and loan proceeds)"
EXCLUDED_ORDER = [G_SETTLE, G_PAYROLL, G_INTERNAL, G_TRUST, G_TRANSFER, G_OTHERUNIT]
G_SOURCE_ERROR = "Left out as an error in the state's file"
INCOME_EXCLUDED_ORDER = [G_BORROW, G_SETTLE, G_PAYROLL, G_INTERNAL, G_TRUST, G_TRANSFER, G_OTHERUNIT, G_SOURCE_ERROR]

# Individual receipt lines that are demonstrably wrong in the state's file, keyed by
# (unit id, year, fund name upper-case, receipt code, exact amount) so nothing else can match. Each is left out of
# counted income and shown on the page in its own group, so the reconciliation to the file total still holds.
KNOWN_SOURCE_ERRORS = {
    ("school-sbcsc", "2025", "EDUCATION", "1110", "251840353.20"):
        "$251,840,353 recorded as property taxes in the Education Fund. Indiana school Education Funds are paid for by "
        "state tuition support, not a property-tax levy; the state certified South Bend Community School Corporation's "
        "2025 levy for all funds at $95,794,532 (MON-027); without this line its property-tax receipts are $82.9 million "
        "(2024: $80.4 million) and its Education Fund took in $122.6 million against $131.0 million paid out "
        "(2024: $123.3 million in, $133.5 million out).",
}

# ---------------------------------------------------------------- SBOA chart rules (by fund number)


def county_chart(n: int, name: str):
    """SBOA county Funds Table (MON-062). Returns (group|None, reason, how) or None when the chart is
    silent for this number (caller then needs a named rule)."""
    if 1 <= n <= 99:
        return None                                     # outside funds: numbers reused locally -> named
    if 1000 <= n <= 2999:
        return (None, "statutory fund (1000-2999)", "chart")
    if 4700 <= n <= 4749:
        return (G_INTERNAL, "county chart 4700-4749 Self-Insurance (fund type 07, internal service)", "chart")
    if n == 4016:
        return (G_INTERNAL, "county chart 4016 IT Services (fund type 07, internal service)", "chart")
    if 4000 <= n <= 4999:
        return (None, "local authority fund (4000-4999)", "chart")
    if 5000 <= n <= 5999:
        return (G_PAYROLL, "county chart Accounting Funds 5000-5999 (payroll clearing and withholding, fund type 11)", "chart")
    if 6000 <= n <= 6999:
        return (G_SETTLE, "county chart Settlement Funds 6000s (property-tax, excise and income-tax settlement, fund type 11)", "chart")
    if 7000 <= n <= 7499:
        return (G_SETTLE, "county chart Remittance Funds 7100-7499 (collected for the state or other local governments, fund type 11)", "chart")
    if 8000 <= n <= 9199:
        return (None, "grant fund (8000-9199)", "chart")
    return None


def city_town_chart(n: int, name: str):
    """SBOA revised fund list for cities and towns, effective 2022-01-01 (MON-064)."""
    if 1101 <= n <= 1199 or 2201 <= n <= 2599 or 3301 <= n <= 3399 or 4401 <= n <= 4699 \
            or 5501 <= n <= 5510 or 6101 <= n <= 6999:
        return (None, "governmental, permanent or enterprise fund", "chart")
    if 7701 <= n <= 7799:
        return (G_INTERNAL, "cities and towns chart 7701-7799 Internal Service Funds", "chart")
    if 8801 <= n <= 8825:
        return (G_TRUST, "cities and towns chart 8801-8825 pension, private-purpose and investment trust funds", "chart")
    if 8850 <= n <= 8899:
        return (G_TRUST, "cities and towns chart 8850-8899 custodial funds", "chart")
    if 8901 <= n <= 8999:
        return (G_PAYROLL, "cities and towns chart 8901-8999 payroll, payroll withholding and clearing funds", "chart")
    return None


def school_chart(n: int, name: str):
    """SBOA school manual part 4, fund numbers and fund types (MON-063)."""
    if n == 630:
        return (G_TRUST, "school chart 0630 Post-Retirement/Severance Future Benefits (fund type 8, pension trust)", "chart")
    if 1100 <= n <= 1110:
        return (G_INTERNAL, "school chart 1100-1110 Self-Insurance (fund type 7, internal service)", "chart")
    if 1800 <= n <= 1849:
        return (G_TRUST, "school chart 1800-1849 Judgments (fund type 11, custodial)", "chart")
    if 2300 <= n <= 2399:
        return (G_TRUST, "school chart 2300-2399 Extra-Curricular Activities (fund type 11, custodial)", "chart")
    if 2700 <= n <= 2799:
        return (G_TRUST, "school chart 2700-2799 Scholarships and Awards (fund type 9, private-purpose trust)", "chart")
    if 8000 <= n <= 8999:
        return (G_TRUST, "school chart 8000 series trust funds (money held on behalf of another person or entity)", "chart")
    if 9000 <= n <= 9999:
        return (G_PAYROLL, "school chart 9000 series clearing funds (payroll withholdings 9000-9499, other clearing 9500-9999)", "chart")
    if 100 <= n <= 7999:
        return (None, "school fund counted", "chart")
    return None


def library_chart(n: int, name: str):
    """SBOA fund list / chart of accounts for libraries (MON-065)."""
    if 100 <= n <= 599:
        return (None, "governmental or permanent fund (100-599)", "chart")
    if 600 <= n <= 699:
        return (None, "enterprise fund (600-699)", "chart")
    if 700 <= n <= 799:
        return (G_INTERNAL, "library chart 700-799 internal service funds", "chart")
    if 800 <= n <= 850:
        return (G_PAYROLL, "library chart 800-850 clearing funds (PLAC, Evergreen, payroll, other clearing)", "chart")
    if 900 <= n <= 999:
        return (G_TRUST, "library chart 900-999 trust funds", "chart")
    return None


CHARTS = {"county": county_chart, "city": city_town_chart, "town": city_town_chart,
          "school": school_chart, "library": library_chart}

# ---------------------------------------------------------------- named rules (chart silent)
# (unit_id, fund number) -> (group or None, reason).  None = counted.
NAMED_FUNDS = {
    # St. Joseph County "outside funds" (numbers 0001-0099; the chart's titles for 0001-0009 differ from
    # the county's local use of those numbers, so each is reviewed by name).
    ("county-st-joseph", 1): (G_TRUST, "Treasurer after-settlement collections: the chart's 0001 After Settlement Collections, custodial (type 11)"),
    ("county-st-joseph", 2): (G_TRUST, "Sheriff's inmate trust: the chart's 0002 Sheriff's Inmate Trust, private-purpose trust (type 09)"),
    ("county-st-joseph", 3): (None, "Jail commissary: the chart's 0003 Jail Commissary, special revenue (type 02)"),
    ("county-st-joseph", 4): (None, "Juvenile Justice Center detention fund: county program fund"),
    ("county-st-joseph", 5): (None, "Juvenile Justice Center equipment reimbursement: county program fund"),
    ("county-st-joseph", 6): (G_TRUST, "Juvenile Justice Center restitution: collected and paid on to victims (custodial)"),
    ("county-st-joseph", 7): (None, "Juvenile Justice Center probation user fees: county program fund"),
    ("county-st-joseph", 9): (G_TRUST, "Clerk child-support cashbook: support payments passed on to families (custodial)"),
    ("county-st-joseph", 11): (G_TRUST, "Clerk Odyssey fund: the clerk's trust account for court-ordered payments (the chart's Clerk's Trust, custodial)"),
    ("county-st-joseph", 13): (G_TRUST, "Clerk trust and investment: clerk's trust account (custodial)"),
    ("county-st-joseph", 17): (G_TRUST, "Portage Manor resident trust: the chart's County Home Residents' Trust (custodial)"),
    ("county-st-joseph", 21): (None, "Sheriff inmate telephone: commission revenue the sheriff spends on jail programs; counted (review)"),
    ("county-st-joseph", 33): (None, "JP Morgan IPG equipment: equipment lease-purchase proceeds held at a bank; county money, counted"),
    ("county-st-joseph", 22): (None, "Clerk Quest system: clerk outside fund; not a trust or clearing account by its name, so counted (review)"),
    ("county-st-joseph", 26): (G_TRUST, "Police retirement plans: pension trust (benefits paid to retirees)"),
    ("county-st-joseph", 28): (G_TRUST, "DuComb resident trust: residents' money held in trust (custodial)"),
    ("county-st-joseph", 30): (None, "2021 DuComb escrow at a trustee bank: county bond proceeds; transfers out of it are left out by the line rule"),
    ("county-st-joseph", 31): (G_TRUST, "Sheriff civil and records collections: the chart's Sheriff's Cashbook (custodial)"),
    ("county-st-joseph", 34): (None, "2025 GO highway bond proceeds at a trustee bank: county money; transfers out of it are left out by the line rule"),
    ("county-st-joseph", 35): (None, "2025 parks bond proceeds at a trustee bank: county money; transfers out of it are left out by the line rule"),
    # numbers inside the chart's ranges but used for a holding/clearing purpose the chart lists elsewhere
    ("county-st-joseph", 1108): (G_TRUST, "Tax sale clearing (auditor): a clearing account; the chart's 1108 is Bid Deposits and Bonds Holding"),
    ("county-st-joseph", 1201): (G_TRUST, "Auditor tax overpayments: refunds of taxes paid in error (the chart lists 1201 as Surplus Tax, special revenue; left out because it returns taxpayers' money)"),
    ("county-st-joseph", 1204): (G_TRUST, "Tax sale redemption: money paid to redeem property, held for the tax-sale buyer (the chart lists it as special revenue; left out as money held for others)"),
    ("county-st-joseph", 1205): (G_TRUST, "Tax sale surplus: sale proceeds above the taxes owed, held for the former owner (the chart lists it as special revenue; left out as money held for others)"),
    ("county-st-joseph", 4020): (G_INTERNAL, "Fleet motor pool: a garage that serves other departments (internal service in substance; the chart has no 4020)"),
    ("county-st-joseph", 4917): (G_TRUST, "Recorder's escrow: customers' prepaid recording-fee deposits (custodial in substance)"),
    # towns: numbers the cities and towns chart does not define
    ("town-walkerton", 9999): (G_TRUST, "Town court: fines and costs collected and paid on (custodial in substance; outside the chart's ranges)"),
    ("town-walkerton", 9003): (None, "Donation fund numbered outside the chart (receipts only): counted"),
    ("town-walkerton", 1176): (None, "American Rescue Plan grant fund numbered outside the chart's grant range: counted"),
    ("town-lakeville", 1176): (None, "American Rescue Plan grant fund numbered outside the chart's grant range: counted"),
    ("town-north-liberty", 180): (None, "Lease bonds property tax: debt payments; number outside the chart, counted"),
    ("town-new-carlisle", 9600): (None, "Funds on deposit: only an investment purchase, which the line rule leaves out"),
    # South Bend (own numbering)
    ("city-south-bend", 226): (G_INTERNAL, "Liability insurance: the city's self-insurance fund (Gateway gives it the same state fund code as Mishawaka's 7704 Self-Insurance)"),
    ("city-south-bend", 711): (G_INTERNAL, "Self-funded employee benefits: self-insurance (internal service)"),
    ("city-south-bend", 713): (G_INTERNAL, "Unemployment compensation: self-insured unemployment claims (internal service)"),
    ("city-south-bend", 701): (G_TRUST, "Fire pension: pension trust (Gateway gives it the same state fund code as Mishawaka's 8801 Fire Pension)"),
    ("city-south-bend", 702): (G_TRUST, "Police pension: pension trust (Gateway gives it the same state fund code as Mishawaka's 8802 Police Pension)"),
    # special units
    ("special-sb-transpo", 4): (G_PAYROLL, "Payroll: a payroll clearing account (the cities and towns chart's 8901 and the library chart's 802 are payroll clearing funds); the Transportation fund also records salaries"),
    ("township-portage", 5100): (G_INTERNAL, "Health insurance: an employee-benefit fund; its receipts are Benefit Plan Contributions (R907) and it pays insurance (internal service in substance)"),
    ("special-solid-waste", 4704): (G_INTERNAL, "Solid waste health insurance: numbered in the county chart's 4700-4749 Self-Insurance range (internal service)"),
}
# by-name rules for every unit of a NO_CHART kind (townships, special units) and off-chart units
NAMED_PATTERNS = [
    (re.compile(r"PAYROLL (DEDUCTION|WITHHOLDING)S?\b|\bPAYROLL$|WITHHOLDING", re.I), G_PAYROLL,
     "payroll deductions or withholding held until paid to the IRS, the state and benefit providers (clearing account)"),
]

# lines (inside counted funds) that only move money between a unit's own funds or accounts
LINE_TRANSFER_CODES = {"D704": "transfer out to another fund", "D705": "interfund loan made",
                       "D706": "interfund loan repaid", "D900": "purchase of investments"}

# ---------------------------------------------------------------- categories

TYPE_LABELS = OrderedDict([
    ("100", "Salaries and benefits"),
    ("200", "Supplies"),
    ("300", "Services and contracts"),
    ("400", "Township assistance"),
    ("500", "Debt payments"),
    ("600", "Capital projects"),
    ("700", OTHER),
    ("800", "Utility operating costs"),
])

CLASS_NAMES = {"100": "Personal Services", "200": "Supplies", "300": "Services and Charges", "400": "Township Assistance",
               "500": "Debt service - principal and interest", "600": "Capital Outlays", "700": "Other Disbursements",
               "800": "Operations"}

SCHOOL_PURPOSE = OrderedDict([
    ("51", "Instruction"),
    ("52", "Support services"),
    ("53", "Food and other services"),
    ("54", "Buildings and construction"),
    ("55", "Debt payments"),
    ("56", "Other"),
])

UTIL_ENTS = re.compile(r"WATER|WASTEWATER|SEWER|ELECTRIC|STORM|TRASH|SOLID WASTE", re.I)
GENERAL_NAMES = re.compile(r"^(GENERAL( FUND)?|GENERAL TOWNSHIP FUND|TOWNSHIP( GENERAL)?( FUND)?|OPERATING( FUND)?|"
                           r"AVIATION|TRANSPORATION|TRANSPORTATION|SOLID WASTE MANAGEMENT FUND)$", re.I)

P_GENERAL = "General operations"
P_UTIL = "Utilities"
P_DEBT = "Debt service"
P_TA = "Township assistance"
P_ECON = "Economic development"
P_SAFETY = "Public safety and justice"
P_ROADS = "Roads and streets"
P_PARKS = "Parks, recreation, culture"
P_HEALTH = "Health"
P_CODE = "Planning and code enforcement"
P_CENTRAL = "Central services and IT"
P_CAPITAL = "Buildings and reserves"
P_GRANTS = "Grants"
P_GIFTS = "Gifts and donations"


def _rx(p: str):
    return re.compile(p, re.I)


# Ordered: the first rule that matches a fund wins. Each rule: (category, test(fund) -> bool, description)
PURPOSE_RULES = [
    (P_GENERAL, lambda f: bool(GENERAL_NAMES.match(f["name"].strip())) or f["general"],
     "the unit's general or main operating fund"),
    (P_UTIL, lambda f: (f["ent"] != "Governmental Activities" and bool(UTIL_ENTS.search(f["ent"])))
     or f["chart_util"] or bool(_rx(r"\b(WATER|SEWER|SEWAGE|WASTEWATER|W/W|ELECTRIC|STORM ?WATER|TRASH|REFUSE|GARBAGE|"
                                    r"SOLID WASTE|RECYCLING|AUTEN|GRANGER|WYATT - |CARRIAGE HILLS)\b").search(f["name"])),
     "enterprise utility funds (water, wastewater, electric, stormwater, trash) and utility-named funds"),
    (P_DEBT, lambda f: f["chart_debt"] or bool(_rx(r"DEBT|SINKING|BOND (AND|&) INT|\bB ?& ?I\b|BOND PAYMENT|BOND TAX|"
                                                   r"LEASE RENTAL|LEASE PMT|LEASE BONDS|REDEMPTION|BOND RESERV|MATURED BOND|"
                                                   r"\bG/?O BOND$|COST OF ISSUANCE|\bDS\b|BOND FUND$").search(f["name"])),
     "debt service, sinking, bond-and-interest and lease-rental funds"),
    (P_TA, lambda f: bool(_rx(r"TOWNSHIP ASSISTANCE|POOR RELIEF").search(f["name"])), "township assistance (poor relief) funds"),
    (P_ECON, lambda f: bool(_rx(r"\bTIF\b|DEVELOPMENT AREA|DEV AREA|ALLOCATION AREA|REDEVELOPMENT|RE-DEVELOPMENT|\bRED\. |"
                                r"ECONOMIC DEV|ECON(OMIC)? DEV|\bEDIT\b|C\.?E\.?D\.?I\.?T|\bEDC\b|\bEDA\b|SAMSUNG|GM PROJECT|"
                                r"COMMUNITY INVESTMENT|COMMUNITY DEVELOPMENT|INDUSTRIAL|STUDEBAKER|\bRDA\b|DOUBLE TRACK|"
                                r"SOUTH SHORE|HOUSING|REVOLVING|PROPERTY REHAB|EDDY STREET").search(f["name"])),
     "TIF and development-area funds, redevelopment, local income tax for economic development (EDIT/CEDIT), "
     "community development and housing"),
    (P_SAFETY, lambda f: bool(_rx(r"POLICE|FIRE|SHERIFF|\bEMS\b|AMBULANCE|EMERGENCY MEDICAL|DISPATCH|\b911\b|PUBLIC SAF|"
                                  r"LAW ENF|\bJAIL|COMMISARY|COMMISSARY|INMATE|CORRECTION|PROBATION|PRETRIAL|PROSECUTOR|"
                                  r"\bPROS\.|PUBLIC DEFENDER|COURT|CLERK|\bJJC\b|JUVENILE|DETENTION|MISDEMEANANT|DUCOMB|"
                                  r"CASA|VICTIM|\bVOCA\b|VIOLENCE|DRUG ENF|\bDEA\b|\bDARE\b|K-9|RIVER RESCUE|\bEMA\b|"
                                  r"HOMELAND|ACCIDENT REPORT|CRIME|ARSON|OFFENDER|DOMESTIC|DRCB|DISPUTE RESOLUTION|"
                                  r"IV-D|JUSTICE|LECE|L\.E\.C\.E|OPERATION PULLOVER|SAFTEY|CONTINU(E|ING) EDU").search(f["name"])),
     "police, fire and EMS, sheriff and jail, dispatch, courts, prosecutor, probation and corrections"),
    (P_ROADS, lambda f: bool(_rx(r"MOTOR VEHICLE|\bMVH\b|MVH|ROAD|STREET|BRIDGE|HIGHWAY|MAJOR MOVES|WHEEL TAX|CCMG|"
                                 r"COMMUNITY CROSSING|INDOT|THOROUGHFARE|LRSA|\bLRS\b|PARKING|TRAIL").search(f["name"])),
     "motor vehicle highway, local road and street, bridge, highway, wheel tax, Major Moves, Community Crossings and parking funds"),
    (P_PARKS, lambda f: bool(_rx(r"PARK(?!ING)|RECREATION|\bRECR\b|\bZOO\b|SPORTS|CENTURY CENTER|MORRIS|PERFORMING ARTS|"
                                 r"\bPAC\b|FIELDHOUSE|4TH OF JULY|FESTIVAL|COMMUNITY CENTER|COMMUNITY BUILDI|WETLAND BARN|"
                                 r"HISTORIC|CHRISTMAS|STORY STROLL|SUMMER READING|\bLARE\b|RELEAF|TOURISM|CONVENTION|"
                                 r"HERO BANNER").search(f["name"])),
     "parks and recreation, the zoo, sports and event venues, performing-arts and convention facilities"),
    (P_HEALTH, lambda f: bool(_rx(r"HEALTH(?! ?INS)|OPIOID|OPIOD|DRUG FREE|IMMUNIZATION|\bCHW|LEAD INITIATIVE|"
                                  r"ADULT PROTECTIVE|ANIMAL|DOG TAX|REAL SERVICES|PORTAGE MANOR|NACCHO|ALCOHOL|\bCSAP\b|"
                                  r"ADDICTION").search(f["name"])),
     "health department and public-health funds, opioid settlement, animal control"),
    (P_CODE, lambda f: bool(_rx(r"CODE ENFORCEMENT|CONSOLIDATED BUILDING|UNSAFE BUILDING|RENTAL UNITS|BUILDING DEPT|"
                                r"PLAN COMMISSION|PLANNING|ZONING|PROPERTY MAINTENANCE|RESIDENTIAL LEASE").search(f["name"])),
     "building, planning, zoning and code-enforcement funds"),
    (P_CENTRAL, lambda f: bool(_rx(r"CENTRAL SERVICES|IT / INNOVATION|INFORMATION TECHNOLOGY").search(f["name"])),
     "central services and information-technology funds"),
    (P_CAPITAL, lambda f: f["chart_capital"] or bool(_rx(r"CUM(ULATIVE|MULATIVE|\.)? ?CAP|CUMULATIVE BUILDING|CUM CAP|RAINY DAY|"
                                                         r"LEVY EXCESS|CONSTRUCTION|CAPITAL|PROCEEDS|IMPROVEMENT RESERVE|"
                                                         r"EQUIPMENT REPL|SALE OF SU|SURPLUS|\bCCIF\b|INFRASTRUCTURE|"
                                                         r"ENERGY SAV|BUILDING CORP|TOWN HOUSE|PROJECT FUND|IMPROVEMENT PROJECT|PASSENGER FACILITY|"
                                                         r"\bPFC\b|CONTRACTUAL").search(f["name"])),
     "cumulative capital, construction, bond-proceeds, rainy-day and other capital or reserve funds"),
    (P_GRANTS, lambda f: f["chart_grant"] or bool(_rx(r"GRANT|\bARPA\b|\bARP\b|AMERICAN RESCUE|RESCUE PLAN|CARES|COVID|CORONA|"
                                                      r"FEDERAL|TITLE |HAVA|EECBG").search(f["name"])),
     "federal and state grant funds, including American Rescue Plan funds"),
    (P_GIFTS, lambda f: bool(_rx(r"DONATION|GIFT|BEQUEST").search(f["name"])), "donation and gift funds"),
    (OTHER, lambda f: True, "funds no rule above matched"),
]

# ---------------------------------------------------------------- reading


def read_lines(year: int, receipts: bool = False) -> list[dict]:
    with open((RECEIPT_FILES if receipts else FILES)[year], encoding="utf-8-sig", newline="") as fh:
        return [dict(r) for r in csv.DictReader(fh, delimiter="|")]


def money(s: str) -> Decimal:
    return Decimal(s.strip() or "0").quantize(CENT)


def fund_number(line: dict, kind: str) -> int | None:
    raw = (line["Fund_code"] if kind == "school" else line["unit_fund_number"]).strip()
    return int(raw) if raw.isdigit() else None


def fund_key(line: dict) -> tuple:
    return (line["unit_fund_number"].strip(), line["Fund_code"].strip(), line["fund_name"].strip(), line["ent_name"].strip())


def group_units(lines: list[dict], unit_map: dict[str, str]):
    """{money_id: {"name", "kind", "lines"}} for covered units; skipped names returned separately."""
    units, skipped = {}, {}
    for r in lines:
        nm = r["unit_name"].strip()
        if nm.upper() in SKIP_UNITS:
            skipped[nm] = SKIP_UNITS[nm.upper()]
            continue
        mid = unit_map.get(nm.upper())
        if not mid:
            raise SystemExit(f"Unit not in tools/build_money.py UNITS and not skipped: {nm!r}")
        u = units.setdefault(mid, {"name": nm, "kind": kind_of(r["afr_unit_type"].strip()), "lines": []})
        u["lines"].append(r)
    return units, skipped

# ---------------------------------------------------------------- decisions


def rule_basis(mid: str, kind: str) -> str:
    """'sboa_chart' when the unit's funds follow an SBOA fund-number chart; 'named_review' otherwise."""
    if kind in NO_CHART_KINDS or mid in OFF_CHART:
        return "named_review"
    return "sboa_chart"


def fund_decision(mid: str, kind: str, fund: dict) -> tuple[str | None, str, str]:
    """(excluded group or None, reason, how) for one fund. how = chart | named | default."""
    n = fund["number"]
    named = NAMED_FUNDS.get((mid, n)) if n is not None else None
    if named:
        return named[0], named[1], "named"
    basis = rule_basis(mid, kind)
    if basis == "sboa_chart":
        chart = CHARTS[kind]
        res = chart(n, fund["name"]) if n is not None else None
        if res is None:
            if kind == "library" and n is not None and n < 100:
                return None, "numbered outside the library chart (below 100); reviewed by name: an ordinary library fund, counted", "named"
            raise SystemExit(f"{mid}: fund {fund['name']!r} number {n} is outside the {kind} chart and has no named rule")
        return res
    for rx, grp, why in NAMED_PATTERNS:
        if rx.search(fund["name"]):
            return grp, f"{fund['name'].strip()}: {why}", "named"
    return None, "reviewed by name: an ordinary fund of the unit, counted", "default"


def line_excluded(line: dict) -> str | None:
    if line["section"].strip() == "4":
        return "section 4 of the file (Transfers Out and other financing uses)"
    code = line["disburse_code"].strip()
    if code in LINE_TRANSFER_CODES:
        return LINE_TRANSFER_CODES[code]
    return None


def county_duplicates(units_year: dict) -> dict[str, str]:
    """County fund numbers whose total equals, to the cent, the total of the same-numbered fund another
    covered unit reports in the same file (the county auditor keeps that unit's books). {number: unit}"""
    county = units_year.get("county-st-joseph")
    if not county:
        return {}
    def totals(u):
        t = defaultdict(Decimal)
        for r in u["lines"]:
            t[r["unit_fund_number"].strip()] += money(r["amount"])
        return t
    ct = totals(county)
    dup = {}
    for mid, u in units_year.items():
        if mid == "county-st-joseph" or u["kind"] not in ("special",):
            continue
        for k, v in totals(u).items():
            if k in ct and ct[k] == v and v != 0:
                dup[k] = mid
    return dup


def purpose_of(fund: dict) -> tuple[str, str]:
    for cat, test, desc in PURPOSE_RULES:
        if test(fund):
            return cat, desc
    return OTHER, "funds no rule above matched"


def fund_info(mid: str, kind: str, line: dict) -> dict:
    n = fund_number(line, kind)
    chart_city = kind in ("city", "town") and mid not in OFF_CHART and n is not None
    chart_county = kind == "county" and n is not None
    chart_lib = kind == "library" and n is not None
    return {
        "number": n, "name": line["fund_name"].strip(), "ent": line["ent_name"].strip(),
        "general": (chart_county and n == 1000) or (chart_city and n == 1101) or (chart_lib and n == 100)
                   or (mid == "city-south-bend" and n == 101),
        "chart_util": chart_city and 6101 <= n <= 6699,
        "chart_debt": (chart_city and 3301 <= n <= 3399) or (chart_county and (4400 <= n <= 4499 or 4600 <= n <= 4699))
                      or (chart_lib and 300 <= n <= 399),
        "chart_capital": (chart_lib and 400 <= n <= 499),
        "chart_grant": (chart_county and 8000 <= n <= 9199) or (chart_city and (2401 <= n <= 2499 or 4500 <= n <= 4599))
                       or (chart_lib and 276 <= n <= 299),
    }


def analyse(mid: str, unit: dict, dups: dict | None = None) -> dict:
    """Everything for one unit-year: totals, included lines by category, excluded by group, fund log."""
    kind = unit["kind"]
    total = Decimal("0.00")
    purpose = defaultdict(Decimal)
    by_type = defaultdict(Decimal)
    excluded = defaultdict(Decimal)
    excl_detail = defaultdict(lambda: defaultdict(Decimal))     # group -> reason/fund label -> amount
    purpose_funds = defaultdict(lambda: defaultdict(Decimal))  # category -> fund name -> amount
    fund_log = {}                                               # fund key -> dict
    for r in unit["lines"]:
        amt = money(r["amount"])
        total += amt
        fk = fund_key(r)
        if fk not in fund_log:
            info = fund_info(mid, kind, r)
            if dups and r["unit_fund_number"].strip() in dups:
                other = dups[r["unit_fund_number"].strip()]
                grp, why, how = G_OTHERUNIT, f"same fund number, name and amount reported by {other}", "named"
            else:
                grp, why, how = fund_decision(mid, kind, info)
            if kind == "school":
                cat, cdesc = None, None
            else:
                cat, cdesc = purpose_of(info)
            fund_log[fk] = {"info": info, "group": grp, "why": why, "how": how, "purpose": cat,
                            "purpose_rule": cdesc, "counted": Decimal("0.00"), "excluded": Decimal("0.00")}
        fl = fund_log[fk]
        label = f"{fl['info']['name']} ({fl['info']['number'] if fl['info']['number'] is not None else fk[0]})"
        if fl["group"]:
            excluded[fl["group"]] += amt
            excl_detail[fl["group"]][label] += amt
            fl["excluded"] += amt
            continue
        lx = line_excluded(r)
        if lx:
            excluded[G_TRANSFER] += amt
            excl_detail[G_TRANSFER][lx] += amt
            fl["excluded"] += amt
            continue
        fl["counted"] += amt
        if kind == "school":
            cls = r["disburse_class_code"].strip()
            if r["section"].strip() != "2" or cls not in SCHOOL_PURPOSE:
                raise SystemExit(f"{mid}: unexpected school line section={r['section']} class={cls}")
            purpose[SCHOOL_PURPOSE[cls]] += amt
            purpose_funds[SCHOOL_PURPOSE[cls]][label] += amt
        else:
            cls = r["disburse_class_code"].strip()
            if r["section"].strip() != "0" or cls not in TYPE_LABELS:
                raise SystemExit(f"{mid}: unexpected civil line section={r['section']} class={cls}")
            by_type[TYPE_LABELS[cls]] += amt
            purpose[fl["purpose"]] += amt
            purpose_funds[fl["purpose"]][label] += amt
    included = sum(purpose.values(), Decimal("0.00"))
    excl_total = sum(excluded.values(), Decimal("0.00"))
    if included + excl_total != total:
        raise SystemExit(f"RECONCILIATION FAILED {mid}: counted {included} + not counted {excl_total} != file total {total}")
    if kind != "school" and sum(by_type.values(), Decimal("0.00")) != included:
        raise SystemExit(f"RECONCILIATION FAILED {mid}: by_type does not sum to counted total")
    return {"mid": mid, "kind": kind, "name": unit["name"], "total": total, "included": included,
            "excluded_total": excl_total, "purpose": dict(purpose), "by_type": dict(by_type),
            "excluded": dict(excluded), "excl_detail": excl_detail, "purpose_funds": purpose_funds,
            "funds": fund_log, "basis": rule_basis(mid, kind)}


def fold_top(cats: dict[str, Decimal], n: int = TOP_N) -> list[tuple[str, Decimal, list[str]]]:
    """Largest first; keep the n largest named categories and fold the rest (and any existing Other) into
    Other, which goes last. Returns [(category, amount, folded_names)]. Zero categories are dropped."""
    named = sorted(((k, v) for k, v in cats.items() if k != OTHER and v != 0), key=lambda kv: (-kv[1], kv[0]))
    if len(named) == n + 1 and not cats.get(OTHER):
        n += 1          # one leftover and no Other: show it under its own name (still at most n + 1 bars)
    keep, rest = named[:n], named[n:]
    other_amt = cats.get(OTHER, Decimal("0.00")) + sum((v for _, v in rest), Decimal("0.00"))
    out = [(k, v, []) for k, v in keep]
    folded = [k for k, _ in rest] + ([OTHER] if cats.get(OTHER) else [])
    if rest or cats.get(OTHER):
        out.append((OTHER, other_amt, folded))
    return out


# ---------------------------------------------------------------- income (receipts)
# Same fund decision as spending (fund_decision + the county duplicate rule from that year's disbursements),
# so the two sides cover the same funds. Inside counted funds these receipt lines are not income:
I_LINE_TRANSFER = {"R910": "transfer in from another fund", "R911": "interfund loan received",
                   "R912": "interfund loan repaid to this fund", "R901": "sale of investments"}
I_LINE_BORROW = {"R903": "tax anticipation warrant proceeds", "R904": "proceeds from borrowing"}
I_LINE_PAYROLL = {"R909": "payroll fund and clearing account receipts"}
I_LINE_INTERNAL = {"R907": "benefit plan contributions"}
BORROW_NAME = re.compile(r"BOND PROCEEDS|LOAN PROCEEDS|NOTE PROCEEDS|PROCEEDS OF (LONG-TERM )?DEBT|LEASE PROCEEDS", re.I)
ALLOCATION_NAME = re.compile(r"\bALLOCATION\b", re.I)   # charges billed to the unit's own other funds

I_PROP = "Property taxes"
I_LIT = "Local income tax (LIT)"
I_OTAX = "Other local taxes"
I_STATE = "State and federal money"   # the civil file does not separate the two
I_SCH_STATE = "State money"
I_FED = "Federal money"
I_UTIL = "Utility bills"
I_FEES = "Charges, fees and fines"
I_INT = "Interest earnings"
I_REFUND = "Refunds and reimbursements"
# R906 receipts into an economic development area (TIF) fund. In St. Joseph County these are mostly the companies
# repaying the county for water and sewer lines it builds at their expense for the New Carlisle projects (WVPE,
# 2024-07-19, MON-069); the state file does not name the payer, so the label says what the money is, not who paid.
I_DEVREIMB = "Development-area reimbursements"
DEV_AREA_FUND = re.compile(r"\bDEV(ELOPMENT)?\.? AREA\b|\bECONOMIC DEVELOPMENT AREA\b|\bALLOCATION AREA\b|\bTIF\b", re.I)
I_SCH_LOCAL_OTHER = "Other local money"

LIT_NAME = re.compile(r"\bCOIT\b|\bCEDIT\b|\bLOIT\b|\bLIT\b|\bEDIT\b|INCOME TAX|\bCAGIT\b", re.I)
PROP_NAME = re.compile(r"PROPERTY TAX|TAX LEVY|\bLEVY\b", re.I)
GRANT_CODES = ("R129", "R130", "R131", "R132", "R133", "R134")

INCOME_RULES = [   # (category, test(code, name) -> bool, description); first match wins
    (I_PROP, lambda c, n: c == "R101" or (c == "R108" and bool(PROP_NAME.search(n)) and not LIT_NAME.search(n)),
     "R101 General Property Taxes, and Other Taxes lines named as property tax"),
    (I_LIT, lambda c, n: c in ("R123", "R138", "R139", "R140", "R142") or (c == "R108" and bool(LIT_NAME.search(n))),
     "R123/R138/R139/R140/R142 local income tax distributions, and Other Taxes lines named COIT, CEDIT, LOIT or LIT"),
    (I_OTAX, lambda c, n: c in ("R107", "R108", "R114", "R135", "R137"),
     "R107 innkeeper's tax, R114 vehicle excise, R135 commercial vehicle excise, R137 wheel tax, R108 other taxes"),
    (I_STATE, lambda c, n: c in ("R109", "R110", "R111", "R112", "R113", "R116", "R119", "R122", "R136") + GRANT_CODES,
     "state-shared revenue (MVH, local road and street, cigarette, alcohol, casino, financial institution tax), "
     "payments in lieu of taxes, and R129-R134 Federal and State Grants and Distributions (one code for both)"),
    (I_UTIL, lambda c, n: c in ("R416", "R419", "R420", "R421", "R422", "R801"),
     "R421/R422 metered and unmetered utility sales, R420 sewage, R419 storm water, R416 garbage, R801 utility penalties"),
    (I_FEES, lambda c, n: c[:2] in ("R2", "R4", "R5"), "licenses and permits, charges for services, court costs, fines and fees"),
    (I_INT, lambda c, n: c == "R902", "R902 earnings on investments and deposits"),
    (I_REFUND, lambda c, n: c == "R906", "R906 refunds and reimbursements"),
    (OTHER, lambda c, n: True, "donations, sale of capital assets, other receipts"),
]


def income_category(kind: str, line: dict) -> str:
    if kind == "school":
        cls = line["receipt_class_code"].strip()
        if cls == "1":
            return I_PROP if line["Receipt_Code"].strip() == "1110" else I_SCH_LOCAL_OTHER
        if cls == "2":
            return I_SCH_LOCAL_OTHER
        if cls == "3":
            return I_SCH_STATE
        if cls == "4":
            return I_FED
        if cls in ("7", "9"):
            return OTHER
        raise SystemExit(f"unexpected school receipt class {cls}")
    code = line["Receipt_Code"].strip()
    if code == "R906" and DEV_AREA_FUND.search(line.get("fund_name", "")):
        return I_DEVREIMB
    # the state's line title (before "/") is generic ("Federal and State Grants ..."); keywords are read from the
    # unit's own account name after the "/"
    name = line["receipt_name"].split("/", 1)[1] if "/" in line["receipt_name"] else line.get("Unit_account_name", "")
    for cat, test, _ in INCOME_RULES:
        if test(code, name):
            return cat
    return OTHER


def income_line_excluded(kind: str, line: dict):
    """(group, reason) for a receipt line in a counted fund that is not income, else None."""
    name = line["receipt_name"]
    if kind == "school":
        cls = line["receipt_class_code"].strip()
        if line["section"].strip() == "3" or cls == "10":
            return G_TRANSFER, "transfers in and other financing sources (section 3 of the school file)"
        if cls == "8":
            return G_BORROW, "proceeds of long-term debt"
        return None
    code = line["Receipt_Code"].strip()
    if code in I_LINE_BORROW:
        return G_BORROW, I_LINE_BORROW[code]
    if BORROW_NAME.search(name):
        return G_BORROW, "bond or loan proceeds (named on the line)"
    if code in I_LINE_TRANSFER:
        return G_TRANSFER, I_LINE_TRANSFER[code]
    if code in I_LINE_PAYROLL:
        return G_PAYROLL, I_LINE_PAYROLL[code]
    if code in I_LINE_INTERNAL:
        return G_INTERNAL, I_LINE_INTERNAL[code]
    if ALLOCATION_NAME.search(name):
        return G_TRANSFER, "cost allocations billed to the unit's own other funds"
    return None


def analyse_receipts(mid: str, unit: dict, dups: dict | None = None) -> dict:
    kind = unit["kind"]
    total = Decimal("0.00")
    income = defaultdict(Decimal)
    excluded = defaultdict(Decimal)
    excl_detail = defaultdict(lambda: defaultdict(Decimal))
    income_detail = defaultdict(lambda: defaultdict(Decimal))
    fund_log = {}
    for r in unit["lines"]:
        amt = money(r["amount"])
        total += amt
        fk = fund_key(r)
        if fk not in fund_log:
            info = fund_info(mid, kind, r)
            if dups and r["unit_fund_number"].strip() in dups:
                grp, why, how = G_OTHERUNIT, f"same fund reported by {dups[r['unit_fund_number'].strip()]}", "named"
            else:
                grp, why, how = fund_decision(mid, kind, info)
            fund_log[fk] = {"info": info, "group": grp, "why": why, "how": how}
        fl = fund_log[fk]
        label = f"{fl['info']['name']} ({fl['info']['number'] if fl['info']['number'] is not None else fk[0]})"
        if fl["group"]:
            excluded[fl["group"]] += amt
            excl_detail[fl["group"]][label] += amt
            continue
        err = KNOWN_SOURCE_ERRORS.get((mid, r["year"].strip(), r["fund_name"].strip().upper(),
                                       r["Receipt_Code"].strip(), str(amt)))
        if err:
            excluded[G_SOURCE_ERROR] += amt
            excl_detail[G_SOURCE_ERROR][err] += amt
            continue
        lx = income_line_excluded(kind, r)
        if lx:
            excluded[lx[0]] += amt
            excl_detail[lx[0]][lx[1]] += amt
            continue
        cat = income_category(kind, r)
        income[cat] += amt
        detail = (r["receipt_name"].split("/")[0].strip() if kind != "school" else r["receipt_name"].strip()) or "(unnamed)"
        income_detail[cat][detail] += amt
    included = sum(income.values(), Decimal("0.00"))
    excl_total = sum(excluded.values(), Decimal("0.00"))
    if included + excl_total != total:
        raise SystemExit(f"RECEIPTS RECONCILIATION FAILED {mid}: counted {included} + not counted {excl_total} != file total {total}")
    return {"mid": mid, "kind": kind, "name": unit["name"], "total": total, "included": included,
            "excluded_total": excl_total, "income": dict(income), "excluded": dict(excluded),
            "excl_detail": excl_detail, "income_detail": income_detail, "funds": fund_log,
            "basis": rule_basis(mid, kind)}


# ---------------------------------------------------------------- output


def usd(d: Decimal) -> str:
    return f"${d:,.0f}"


def year_label(kind: str, year: int) -> str:
    return f"{year}-{str(year + 1)[-2:]} school year (state file year {year})" if kind == "school" else str(year)


def top_items(d: dict, k: int = 6) -> str:
    items = sorted(d.items(), key=lambda kv: -kv[1])
    s = "; ".join(f"{name} {usd(v)}" for name, v in items[:k])
    if len(items) > k:
        s += f"; and {len(items) - k} more ({usd(sum((v for _, v in items[k:]), Decimal('0')))})"
    return s


def unit_sources(a: dict, year: int) -> str:
    ids = [FILE_SOURCE[year]]
    if a["basis"] == "sboa_chart":
        ids += CHART_SOURCES[a["kind"]]
    return ";".join(ids)


def rows_for(a: dict, year: int) -> list[list[str]]:
    src = unit_sources(a, year)
    basis = f"afr_{year}_actual_all_funds_{a['basis']}"
    inc = a["included"]
    rows = []
    def pct(v, base):
        return f"{(v / base * 100):.2f}" if base else ""
    for cat, amt, folded in fold_top(a["purpose"]):
        if cat == OTHER:
            names = sorted({f for c in (folded or [OTHER]) for f in a["purpose_funds"].get(c, {})})
            parts = {f: a["purpose_funds"][c][f] for c in (folded or [OTHER]) for f in a["purpose_funds"].get(c, {})}
            note = ("Folded into Other: " + "; ".join(f"{c} {usd(a['purpose'][c])}" for c in folded if c != OTHER) + ". "
                    if any(c != OTHER for c in folded) else "")
            note += "Funds: " + top_items(parts) if names else ""
        else:
            note = "Funds: " + top_items(a["purpose_funds"][cat])
        rows.append([a["mid"], str(year), "by_purpose", cat, f"{amt:.2f}", pct(amt, inc), basis, "computed", src, note])
    if a["kind"] != "school":
        for cat, amt, folded in fold_top(a["by_type"]):
            classes = [f"{k} {CLASS_NAMES[k]}" for k, v in TYPE_LABELS.items() if v == cat or (cat == OTHER and v in folded)]
            note = "Object classes: " + "; ".join(classes)
            if cat == OTHER and any(c != OTHER for c in folded):
                note += ". Folded into Other: " + "; ".join(f"{c} {usd(a['by_type'][c])}" for c in folded if c != OTHER)
            rows.append([a["mid"], str(year), "by_type", cat, f"{amt:.2f}", pct(amt, inc), basis, "computed", src, note])
    for grp in EXCLUDED_ORDER:
        amt = a["excluded"].get(grp)
        if not amt:
            continue
        rows.append([a["mid"], str(year), "spending_excluded", grp, f"{amt:.2f}", pct(amt, a["total"]), basis, "computed",
                     src, top_items(a["excl_detail"][grp])])
    if a["excluded"].get(G_SETTLE):
        rows += detail_rows(a["mid"], year, "passthrough_detail", a["excl_detail"][G_SETTLE], a["excluded"][G_SETTLE],
                            basis, src, "Money paid out of funds held for other governments, by fund.")
    return rows


def detail_rows(mid: str, year: int, view: str, detail: dict, base: Decimal, basis: str, src: str, note: str) -> list[list[str]]:
    """Per-fund rows for one excluded group, top 6 + Other (rows sum exactly to the group)."""
    rows = []
    for cat, amt, folded in fold_top(dict(detail)):
        n = note + (f" Other = {len(folded)} smaller funds." if cat == OTHER and folded else "")
        rows.append([mid, str(year), view, cat, f"{amt:.2f}", f"{(amt / base * 100):.2f}" if base else "", basis,
                     "computed", src, n.strip()])
    return rows


# Unit-years whose receipts are written but not charted, with the reason (shown on the page). The renderer
# uses the latest income year whose basis does not end in "_held".
HELD_INCOME = {
    # (unit id, year): reason. Empty: SBCSC 2025's one bad line is now left out by KNOWN_SOURCE_ERRORS instead of
    # holding back the whole year.
}


def income_rows(a: dict, year: int) -> list[list[str]]:
    ids = [RECEIPT_SOURCE[year]] + (CHART_SOURCES[a["kind"]] if a["basis"] == "sboa_chart" else [])
    src = ";".join(ids)
    held = (a["mid"], year) in HELD_INCOME
    basis = f"afr_{year}_receipts_all_funds_{a['basis']}" + ("_held" if held else "")
    rows = []
    def pct(v, base):
        return f"{(v / base * 100):.2f}" if base else ""
    for cat, amt, folded in fold_top(a["income"]):
        parts = defaultdict(Decimal)
        for c in (folded if cat == OTHER else [cat]):
            for k, v in a["income_detail"].get(c, {}).items():
                parts[k] += v
        note = ("HELD (not charted): " + HELD_INCOME[(a["mid"], year)] + " ") if held else ""
        if cat == OTHER and any(c != OTHER for c in folded):
            note += "Folded into Other: " + "; ".join(f"{c} {usd(a['income'][c])}" for c in folded if c != OTHER) + ". "
        note += ("Receipt lines: " + top_items(parts)) if parts else ""
        rows.append([a["mid"], str(year), "income", cat, f"{amt:.2f}", pct(amt, a["included"]), basis, "computed", src, note])
    for grp in INCOME_EXCLUDED_ORDER:
        amt = a["excluded"].get(grp)
        if not amt:
            continue
        rows.append([a["mid"], str(year), "income_excluded", grp, f"{amt:.2f}", pct(amt, a["total"]), basis, "computed",
                     src, top_items(a["excl_detail"][grp])])
    if a["excluded"].get(G_SETTLE):
        rows += detail_rows(a["mid"], year, "passthrough_in_detail", a["excl_detail"][G_SETTLE], a["excluded"][G_SETTLE],
                            basis, src, "Money received into funds held for other governments, by fund.")
    return rows


def build(verbose: bool = True) -> tuple[list[list[str]], dict]:
    unit_map = load_unit_map()
    results, receipts, skipped_all, present = {}, {}, {}, {}
    for y in YEARS:
        units, skipped = group_units(read_lines(y), unit_map)
        skipped_all.update(skipped)
        present[y] = units
        dups = county_duplicates(units)
        for mid, u in units.items():
            results[(mid, y)] = analyse(mid, u, dups if mid == "county-st-joseph" else None)
        runits, rskipped = group_units(read_lines(y, receipts=True), unit_map)
        skipped_all.update(rskipped)
        for mid, u in runits.items():
            receipts[(mid, y)] = analyse_receipts(mid, u, dups if mid == "county-st-joseph" else None)
    rows = []
    order = sorted({m for (m, _) in results} | {m for (m, _) in receipts})
    for mid in order:
        for y in YEARS:
            if (mid, y) in receipts:
                rows += income_rows(receipts[(mid, y)], y)
            if (mid, y) in results:
                rows += rows_for(results[(mid, y)], y)
    info = {"results": results, "receipts": receipts, "skipped": skipped_all, "present": present}
    if verbose:
        report(info)
    return rows, info


def latest_year(info: dict, mid: str) -> int:
    return max(y for (m, y) in info["results"] if m == mid)


def report(info: dict) -> None:
    res = info["results"]
    print("Skipped (not covered by the guide):")
    for k, v in sorted(info["skipped"].items()):
        print(f"  {k}: {v}")
    mids = sorted({m for (m, _) in res})
    rec = info["receipts"]
    print("\nIncome (receipts), year used: file total, counted income, not counted, of which borrowed")
    for mid in sorted({m for (m, _) in rec}):
        y = max(yy for (m, yy) in rec if m == mid)
        a = rec[(mid, y)]
        print(f"  {mid:38s} {y}  total {usd(a['total']):>15s}  income {usd(a['included']):>14s}  "
              f"not counted {usd(a['excluded_total']):>14s}  borrowed {usd(a['excluded'].get(G_BORROW, Decimal(0))):>12s}")
    print("\nIncome checks (counted income vs the year before, receipts vs disbursements):")
    for (mid, y), a in sorted(rec.items()):
        prev = rec.get((mid, y - 1))
        sp = info["results"].get((mid, y))
        if prev and prev["included"] and a["included"] > 2 * prev["included"] and a["included"] > 1_000_000:
            print(f"  {mid} {y}: counted income {usd(a['included'])} is more than twice {y - 1} ({usd(prev['included'])})")
        if sp and sp["total"] and a["total"] > Decimal("1.5") * sp["total"] and a["total"] > 1_000_000:
            print(f"  {mid} {y}: receipts total {usd(a['total'])} vs disbursements total {usd(sp['total'])}"
                  + ("  [HELD]" if (mid, y) in HELD_INCOME else ""))
    print("\nUnit, year used, file total, counted, not counted, rule basis")
    for mid in mids:
        y = latest_year(info, mid)
        a = res[(mid, y)]
        print(f"  {mid:38s} {y}  total {usd(a['total']):>15s}  counted {usd(a['included']):>14s}  "
              f"not counted {usd(a['excluded_total']):>14s}  {a['basis']}")
    # completeness: 2025 vs 2024 fund counts
    print("\nCompleteness check (number of funds with lines, 2024 -> 2025):")
    for mid in mids:
        n = {y: len(res[(mid, y)]["funds"]) for y in YEARS if (mid, y) in res}
        flag = "  <-- fewer funds" if len(n) == 2 and n[2025] < 0.7 * n[2024] else ""
        print(f"  {mid:38s} {n}{flag}")
    print("\nFunds that fell to Other with more than 1% of a unit's counted spending:")
    for (mid, y), a in sorted(res.items()):
        if a["kind"] == "school" or not a["included"]:
            continue
        for fk, fl in a["funds"].items():
            if fl["purpose"] == OTHER and fl["counted"] > a["included"] / 100:
                print(f"  {mid} {y}: {fl['info']['name']} ({fl['info']['number']}) {usd(fl['counted'])} "
                      f"= {fl['counted'] / a['included'] * 100:.1f}%")


def write(rows: list[list[str]]) -> None:
    tmp = OUT.with_suffix(".csv.tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(HEADER)
        for r in rows:
            assert len(r) == len(HEADER), r
            w.writerow(r)
    tmp.replace(OUT)
    print(f"\nwrote {OUT.relative_to(ROOT)} ({len(rows)} rows)")


if __name__ == "__main__":
    out_rows, _ = build(verbose=True)
    if "--dry-run" not in sys.argv:
        write(out_rows)
