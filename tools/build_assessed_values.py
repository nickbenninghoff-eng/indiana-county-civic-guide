"""Net assessed value (the property-tax base) for each local government, by budget year.

Writes ONE file: data/editions/st-joseph/assessed_values.csv

    unit_id,year,net_assessed_value,basis,fund,status,source_ids,notes

Two kinds of rows, told apart by `basis`. They are NOT the same measure and must not share a chart.

  dlgf_certified           The "Certified AV" the Department of Local Government Finance used to set the
                           unit's tax rate, read from the county's certified budget order for that year
                           (one PDF per year, saved under sources/money/dlgf/). Years 2020-2026.
  gateway_budget_estimate  The "Net Assessed Valuation" the unit entered with its budget, from the Gateway
                           budget download (sources/money/gateway_budget_county71_2012-2026.psv, MON-001).
                           Years 2012-2026. It is the unit's own working figure, not the certified one: many
                           are round numbers, and the 2026 figures run from 36% below to 3% above the certified
                           values (for 2026 the county auditor certified values to the DLGF on 2025-10-08,
                           budget order p.1). Kept for transparency and as
                           the only figure before 2020; not a measure of the tax base.

`year` is the budget year, i.e. taxes payable in that year. The order for 2026 is headed "BUDGET AND TAX
RATES FOR 2025 PAYABLE 2026": the values are the assessments made in the year before.

Which fund. Within one unit the certified AV can differ by fund: a fire territory, a fire-protection or
debt fund, or a school referendum fund is levied on a different area. The unit's row uses its General fund
(0101). Units with no General fund use: schools, Operations (3300); special units and the fire territory,
the lowest-numbered fund whose name contains GENERAL, else the unit's only AV. The `fund` column says which
fund, and `notes` lists every other AV the order shows for the unit. Gateway rows use the same rule
(schools: 0101 General through 2018, 3300 Operations from 2019, when Indiana replaced the school General
fund with Education and Operations funds).

The Gateway download repeats every fund row five times; rows are de-duplicated on the full row (the
download has no conflicting duplicates). Gateway values of 0 or blank are not written (the unit left the
field empty). School and township units that cross the county line show the St. Joseph County part only
in the budget order.

Unit ids are the money-file ids budgets.csv uses (UNITS in tools/build_money.py, read with ast; that
script is never run from here), plus two units the Gateway budget file does not list.

Needs PyMuPDF (`fitz`) to read the budget-order PDFs.

Run:  python -P -E tools/build_assessed_values.py            (writes the CSV, prints a check table)
      python -P -E tools/build_assessed_values.py --dry-run  (prints only)
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
GATEWAY = SRC / "gateway_budget_county71_2012-2026.psv"
OUT = ROOT / "data" / "editions" / "st-joseph" / "assessed_values.csv"
HEADER = ["unit_id", "year", "net_assessed_value", "basis", "fund", "status", "source_ids", "notes"]

# year -> (file under sources/money/dlgf/, source id, short label used in notes)
ORDERS = OrderedDict([
    (2020, ("St-Joseph-191231-2020-Certified-Budget-Order.pdf", "MON-074", "DLGF 2020 certified budget order (2019-12-31)")),
    (2021, ("St-Joseph-County-2021-Budget-Order.pdf", "MON-073", "DLGF 2021 certified budget order (2021-01-08)")),
    (2022, ("St-Joseph-2022-County-Budget-Order.pdf", "MON-072", "DLGF 2022 certified budget order")),
    (2023, ("St-Joseph-230109-2023-County-Budget-Order.pdf", "MON-071", "DLGF 2023 certified budget order (2023-01-09)")),
    (2024, ("St-Joseph-240116-2024-Budget-Order.pdf", "MON-070", "DLGF 2024 certified budget order (2024-01-16)")),
    (2025, ("St-Joseph-250109-2025-Budget-Order.pdf", "MON-027", "DLGF 2025 certified budget order (2025-01-09)")),
    (2026, ("St-Joseph-260114-2026-Budget-Order.pdf", "MON-026", "DLGF 2026 certified budget order (2026-01-14)")),
])
GATEWAY_SOURCE = "MON-001"

# Budget-order unit names that the Gateway budget file (and so UNITS in build_money.py) does not list.
EXTRA_NAMES = {
    "NEW PRAIRIE UNITED SCHOOL CORPORATION": "school-new-prairie",
    "OLIVE-NEW CARLISLE-HUDSON FIRE PROTECTION TERRITORY": "special-olive-new-carlisle-hudson-fpt",
    # the 2023 order spells it "Oliver-New Carlisle-Hudson" (p.42); same territory, unit code 0665
    "OLIVER-NEW CARLISLE-HUDSON FIRE PROTECTION TERRITORY": "special-olive-new-carlisle-hudson-fpt",
}
# Units whose budget-order AV covers only the St. Joseph County part of a cross-county unit.
CROSS_COUNTY = {"school-new-prairie", "school-union-north", "school-john-glenn", "school-phm"}

MONEY = r"\$([\d,]+)"
QUAD = re.compile(rf"{MONEY}\s+{MONEY}\s+{MONEY}\s+\$([\d.]+)\s*$")
FUND_START = re.compile(r"^(\d{4})\s+(.*)$")
UNIT_LINE = re.compile(r"Unit:\s*(\d{4})\s+(.+?)\s*$")


# ---------------------------------------------------------------- units

def load_unit_map() -> dict[str, str]:
    """UNITS from tools/build_money.py (Gateway unit name -> money id), read without executing it."""
    tree = ast.parse((ROOT / "tools" / "build_money.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "UNITS" for t in node.targets):
            units = ast.literal_eval(node.value)
            out = {norm(k): v[0] for k, v in units.items()}
            out.update({norm(k): v for k, v in EXTRA_NAMES.items()})
            return out
    raise SystemExit("UNITS table not found in tools/build_money.py")


def norm(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().upper())


def unit_order(unit_map: dict[str, str]) -> list[str]:
    seen = []
    for mid in unit_map.values():
        if mid not in seen:
            seen.append(mid)
    return seen


# ---------------------------------------------------------------- budget orders

def pdf_lines(path: Path) -> list[tuple[int, str]]:
    """(page, text) lines rebuilt from word positions. The orders' text layer interleaves table columns when
    read in stream order, so words are grouped by their vertical centre instead."""
    try:
        import fitz  # PyMuPDF
    except ImportError as e:  # pragma: no cover
        raise SystemExit("PyMuPDF (fitz) is needed to read the budget orders: pip install pymupdf") from e
    out = []
    with fitz.open(path) as doc:
        for pno, page in enumerate(doc, start=1):
            words = sorted(page.get_text("words"), key=lambda w: ((w[1] + w[3]) / 2, w[0]))
            line, last_y = [], None
            for w in words:
                y = (w[1] + w[3]) / 2
                if last_y is not None and abs(y - last_y) > 2.5:
                    out.append((pno, " ".join(x[4] for x in sorted(line, key=lambda x: x[0]))))
                    line = []
                line.append(w)
                last_y = y if last_y is None or abs(y - last_y) > 2.5 else last_y
            if line:
                out.append((pno, " ".join(x[4] for x in sorted(line, key=lambda x: x[0]))))
    return out


def dollars(s: str) -> int:
    return int(s.replace(",", ""))


def parse_order(path: Path) -> list[dict]:
    """Fund rows of one budget order: unit, fund code and name, certified budget and AV, page.

    A fund's code and name sit on the same line as its four amounts in most years; in some years (and for
    some rows) the code/name line comes just before or just after the amounts line. A code line waiting for
    its amounts, or an amounts line waiting for its code, is paired with the next line of the other kind."""
    rows, unit = [], None
    pend_fund = pend_quad = None
    for page, text in pdf_lines(path):
        m = UNIT_LINE.search(text)
        if m:
            unit = (m.group(1), norm(m.group(2)))
            pend_fund = pend_quad = None
            continue
        if unit is None:
            continue
        q = QUAD.search(text)
        f = FUND_START.match(text)
        if q:
            rec = {"unit_code": unit[0], "unit": unit[1], "page": page, "budget": dollars(q.group(1)),
                   "av": dollars(q.group(2)), "levy": dollars(q.group(3)), "rate": q.group(4)}
            head = text[:q.start()].strip()
            fh = FUND_START.match(head) if head else None
            if fh:
                rec.update(fund=fh.group(1), fund_name=fh.group(2).strip())
                rows.append(rec)
                pend_fund = pend_quad = None
            elif pend_fund:
                rec.update(fund=pend_fund[0], fund_name=pend_fund[1])
                rows.append(rec)
                pend_fund = None
            else:
                pend_quad = rec
            continue
        if f and not text.startswith("Unit Total"):
            code, name = f.group(1), f.group(2).strip()
            if pend_quad:
                pend_quad.update(fund=code, fund_name=name)
                rows.append(pend_quad)
                pend_quad = None
            else:
                pend_fund = (code, name)
    return rows


def unit_fund(funds: list[dict], mid: str) -> dict:
    """The fund whose AV stands for the unit (see the module docstring)."""
    by_code = {f["fund"]: f for f in funds}
    if "0101" in by_code:
        return by_code["0101"]
    if mid.startswith("school-") and "3300" in by_code:
        return by_code["3300"]
    gen = sorted((f for f in funds if "GENERAL" in f["fund_name"].upper() or "GEN" in f["fund_name"].upper().split()),
                 key=lambda f: f["fund"])
    if gen:
        return gen[0]
    if len({f["av"] for f in funds}) == 1:
        return sorted(funds, key=lambda f: f["fund"])[0]
    raise SystemExit(f"{mid}: no General fund and more than one AV; add a rule: "
                     + "; ".join(f"{f['fund']} {f['fund_name']} {f['av']}" for f in funds))


def certified(unit_map: dict[str, str]) -> tuple[dict, list[str]]:
    """{(mid, year): row-dict} from the budget orders, and a list of unmatched unit names."""
    out, unmatched = {}, []
    for year, (fn, sid, label) in ORDERS.items():
        path = SRC / "dlgf" / fn
        if not path.exists():
            raise SystemExit(f"missing budget order {path}")
        funds = parse_order(path)
        by_unit = OrderedDict()
        for f in funds:
            by_unit.setdefault(f["unit"], []).append(f)
        for name, fl in by_unit.items():
            mid = unit_map.get(name)
            if not mid:
                unmatched.append(f"{year}: {name}")
                continue
            # a unit can appear more than once (continued on the next page); fund codes are unique within it
            dedup = OrderedDict()
            for f in fl:
                dedup.setdefault(f["fund"], f)
            fl = list(dedup.values())
            uf = unit_fund(fl, mid)
            others = OrderedDict()
            for f in fl:
                if f["av"] != uf["av"]:
                    others.setdefault(f["av"], []).append(f"{f['fund']} {title(f['fund_name'])}")
            same = [f["fund"] for f in fl if f["av"] == uf["av"]]
            note = (f"{label}, 'Certified AV' column, fund {uf['fund']} {title(uf['fund_name'])} "
                    f"(p.{uf['page']}); the same AV is shown for {len(same)} of the unit's {len(fl)} funds.")
            if others:
                note += " Other bases in the same order: " + "; ".join(
                    f"{', '.join(v)}: ${k:,}" for k, v in others.items()) + "."
            if mid in CROSS_COUNTY:
                note += " St. Joseph County part only; the corporation also lies in another county."
            out[(mid, year)] = {"unit_id": mid, "year": str(year), "net_assessed_value": str(uf["av"]),
                                "basis": "dlgf_certified", "fund": f"{uf['fund']} {title(uf['fund_name'])}",
                                "status": "official", "source_ids": sid, "notes": note,
                                "_all": {f["fund"]: f["av"] for f in fl}}
    return out, unmatched


def title(s: str) -> str:
    return " ".join(w if re.fullmatch(r"[\d#&-]+|LIT|EMS|TIF", w) else w.capitalize() for w in s.split())


# ---------------------------------------------------------------- Gateway estimates

def gateway_rows_raw(path: Path = GATEWAY) -> list[dict]:
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        return list(csv.DictReader(f, delimiter="|"))


def dedupe(rows: list[dict]) -> list[dict]:
    """Drop exact duplicate rows (the download repeats each fund row five times), keeping first-seen order.
    Fails if two rows share (year, unit, fund) but disagree on Net Assessed Valuation."""
    seen, out, nav = set(), [], {}
    for r in rows:
        k = tuple(r.items())
        if k in seen:
            continue
        seen.add(k)
        key = (r["year"], r["unit_type"], r["unit_code"], r["fund_cd"])
        v = r["Net Assessed Valuation"]
        if key in nav and nav[key] != v:
            raise SystemExit(f"conflicting Net Assessed Valuation for {key}: {nav[key]} vs {v}")
        nav[key] = v
        out.append(r)
    return out


def gateway_fund(mid: str, year: int, funds: dict[str, dict]) -> dict | None:
    if "0101" in funds:
        return funds["0101"]
    if mid.startswith("school-"):
        return funds.get("3300")
    gen = sorted((f for c, f in funds.items() if "GEN" in f["fund_description"].upper()), key=lambda f: f["fund_cd"])
    if gen:
        return gen[0]
    if mid == "special-solid-waste":
        return funds.get("8210")
    return None


def gateway(unit_map: dict[str, str], cert: dict) -> dict:
    rows = dedupe(gateway_rows_raw())
    by = defaultdict(dict)
    for r in rows:
        mid = unit_map.get(norm(r["unit_name"]))
        if mid:
            by[(mid, int(r["year"]))][r["fund_cd"]] = r
    out = {}
    for (mid, year), funds in sorted(by.items()):
        f = gateway_fund(mid, year, funds)
        if f is None:
            continue
        raw = (f["Net Assessed Valuation"] or "").strip()
        if not raw:
            continue
        v = Decimal(raw)
        if v <= 0:
            continue
        val = int(v) if v == v.to_integral_value() else v.quantize(Decimal("0.01"))
        fund = f"{f['fund_cd']} {title(f['fund_description'].strip())}"
        note = ("Estimate, not the certified value: the Net Assessed Valuation the unit entered with its budget "
                f"in Gateway (budget download, fund {fund}). The certified value is set later, in the DLGF budget "
                "order; the entered figures are often rounded.")
        c = cert.get((mid, year))
        if c:
            cv = int(c["net_assessed_value"])
            diff = Decimal(str(val)) - cv
            if abs(diff) <= 1:
                note += f" Equals the certified value for {year} (${cv:,})."
            else:
                note += (f" Differs from the certified {year} value (${cv:,}, {c['source_ids']}) by "
                         f"{'+' if diff > 0 else '-'}${abs(diff):,.0f} ({diff / cv * 100:+.1f}%).")
        out[(mid, year)] = {"unit_id": mid, "year": str(year), "net_assessed_value": str(val),
                            "basis": "gateway_budget_estimate", "fund": fund, "status": "official",
                            "source_ids": GATEWAY_SOURCE, "notes": note}
    return out


# ---------------------------------------------------------------- main

def build(verbose: bool = True):
    unit_map = load_unit_map()
    cert, unmatched = certified(unit_map)
    if unmatched:
        raise SystemExit("budget-order units with no money id: " + "; ".join(unmatched))
    gw = gateway(unit_map, cert)
    order = unit_order(unit_map)
    rows = list(cert.values()) + list(gw.values())
    rows.sort(key=lambda r: (order.index(r["unit_id"]), int(r["year"]), r["basis"]))
    if verbose:
        print(f"certified rows: {len(cert)} ({min(y for _, y in cert)}-{max(y for _, y in cert)}); "
              f"Gateway estimate rows: {len(gw)}")
        for y in ORDERS:
            print(f"  {y}: {sum(1 for (_, yy) in cert if yy == y)} units in the budget order")
        print(f"{'unit':40} {'2026 certified':>16} {'2026 Gateway':>16}  diff")
        for mid in order:
            c, g = cert.get((mid, 2026)), gw.get((mid, 2026))
            if not c and not g:
                continue
            cv = int(c["net_assessed_value"]) if c else None
            gv = Decimal(g["net_assessed_value"]) if g else None
            d = f"{(gv - cv) / cv * 100:+.1f}%" if c and g else ""
            print(f"{mid:40} {cv or '':>16} {str(gv or ''):>16}  {d}")
    return rows, {"certified": cert, "gateway": gw}


def write(rows: list[dict]) -> None:
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")  # LF, as .gitattributes asks for data CSVs
        w.writerow(HEADER)
        for r in rows:
            w.writerow([r[h] for h in HEADER])


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    rows, _ = build()
    if "--dry-run" not in argv:
        write(rows)
        print(f"wrote {len(rows)} rows to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
