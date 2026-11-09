"""Money in and money out for one local government (data: spending_breakdowns.csv, tools/build_spending.py).

    money_in_out(ed, page, money_id, level=3) -> Markup | None

Three parts, in this order:
  1. Where the money comes from: one ranked bar chart of counted income (view income).
  2. How it is spent: two ranked bar charts side by side, by purpose and by expense type (schools: by
     purpose only; the state's school file has no expense-type split).
  3. Money that passes through or moves between funds (not counted above): the excluded groups for money
     in and money out, each with one plain line, plus the largest pass-through funds by name.
Charts use charts.hbar with its default mark (m-accent): one neutral hue, largest first, "Other" last.
Every amount on the page comes from a CSV row; the builder checks that counted + not counted equals the
state file total to the cent for every unit and year.
"""
from __future__ import annotations

from collections import OrderedDict

from .charts import hbar
from .components import data_table, status_badge
from .data import split_ids
from .html import Markup, h

OTHER = "Other"
VIEWS = ("income", "income_excluded", "by_purpose", "by_type", "spending_excluded", "passthrough_detail",
         "passthrough_in_detail")

# excluded groups (as written by tools/build_spending.py) -> (short label, plain-language line)
GROUP_TEXT = OrderedDict([
    ("Collected for other governments and passed on (tax settlement and distributions)",
     ("Collected for other governments and passed on",
      "Money collected for other governments (and for the state) and paid on to them: it passes through this "
      "unit's books but isn't its to spend.")),
    ("Moved between the unit's own funds (transfers, loans, investments)",
     ("Moved between its own funds",
      "Transfers and loans from one of the unit's funds to another, and investments bought or sold. The money "
      "is counted once, where it is finally received or spent.")),
    ("Borrowed (bond and loan proceeds)",
     ("Borrowed",
      "Bond and loan proceeds. Borrowing is not income; repaying it shows up later as debt payments in the "
      "spending charts.")),
    ("Payroll withholding and clearing accounts",
     ("Held for others: payroll withholding and clearing",
      "Taxes and deductions taken out of employees' pay and held until they are paid to the IRS, the state and "
      "benefit providers, and other clearing accounts.")),
    ("Self-insurance and other internal service funds",
     ("Internal accounts: self-insurance and similar",
      "Employee health insurance and other funds that the unit's own departments pay into. Their costs are "
      "already counted in the departments' spending, so counting the fund too would count the same dollars twice.")),
    ("Pension, trust and custodial funds held for others",
     ("Held for others: pension, trust and custodial",
      "Pension funds for retirees and accounts held for other people: court-ordered payments, tax-sale money "
      "owed to owners or buyers, inmates' and residents' accounts.")),
    ("Reported by another unit as its own",
     ("Reported by another unit",
      "Funds the county's books also carry for another unit in this guide (the same fund and amount appear in "
      "that unit's report); they are counted with that unit.")),
    ("Left out as an error in the state's file",
     ("Left out: an error in the state's file",
      "A line in the unit's report to the state that cannot be right; the table below says what it is and why. "
      "The guide leaves it out of the charts and shows it here so the totals still add up to the state's file.")),
])

COUNTY_PASS = ("The county collects property taxes and excise taxes, and receives local income tax distributions, for "
               "the local governments in the county, and pays each its share (the settlement and remittance funds of "
               "the state's county chart of accounts). That money is recorded in the county's books but isn't the "
               "county's to spend.")
COUNTY_PASS_SRC = "MON-068;MON-062"

KIND_NOUN = {"county": "the county", "city": "the city", "town": "the town", "township": "the township",
             "school": "the school corporation", "library": "the library", "special": "this unit"}


def _f(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def usd(v) -> str:
    return f"${_f(v):,.0f}"


def usd_short(v) -> str:
    v = _f(v)
    a = abs(v)
    if a >= 1e9:
        return f"${v / 1e9:.2f}B"
    if a >= 1e7:
        return f"${v / 1e6:.1f}M"
    if a >= 1e6:
        return f"${v / 1e6:.2f}M"
    if a >= 1e4:
        return f"${v / 1e3:.0f}K"
    return f"${v:,.0f}"


def _rows(ed, mid: str) -> list[dict]:
    cache = getattr(ed, "_spending_cache", None)
    if cache is None:
        cache = {}
        for r in ed.table("spending_breakdowns"):
            cache.setdefault(r["unit_id"], []).append(r)
        ed._spending_cache = cache
    return cache.get(mid, [])


def _held(r: dict) -> bool:
    return r["basis"].endswith("_held")


def _pick_year(rows: list[dict], views: tuple[str, ...], allow_held: bool = False) -> str | None:
    ys = sorted({r["year"] for r in rows if r["view"] in views and (allow_held or not _held(r))})
    return ys[-1] if ys else None


def _year_label(kind: str, year: str) -> str:
    if kind == "school":
        return f"{year}-{str(int(year) + 1)[-2:]} school year"
    return year


def _kind(ed, mid: str) -> str:
    g = mid.split("-", 1)[0]
    return {"county": "county", "city": "city", "town": "town", "township": "township", "school": "school",
            "library": "library"}.get(g, "special")


def has_money_in_out(ed, mid: str) -> bool:
    return bool(_rows(ed, mid))


def _bars(fid: str, title: str, rows: list[dict], page, subtitle: str, note, cite) -> Markup:
    named = sorted([r for r in rows if r["category"] != OTHER], key=lambda r: -_f(r["amount"]))
    other = [r for r in rows if r["category"] == OTHER]
    bars = []
    for r in named + other:
        share = _f(r["share"])
        tip = r["category"] + ": " + usd(r["amount"]) + f" ({share:.1f}%)"
        if r.get("notes"):
            tip += ". " + (r["notes"][:220] + ("..." if len(r["notes"]) > 220 else ""))
        bars.append({"label": r["category"], "value": _f(r["amount"]),
                     "display": f"{share:.1f}% · {usd_short(r['amount'])}", "tip": tip})
    return hbar(fid, title, bars, subtitle=subtitle, money=True, status="computed", page=page,
                headers=["Category", "Share and amount"], note=note, cite=cite)


def _badge(page, basis_rows: list[dict]) -> Markup:
    named = any(r["basis"].removesuffix("_held").endswith("named_review") for r in basis_rows)
    note = ("Sums of the state's annual financial report lines, with pass-through money, transfers and "
            "borrowing left out by the guide's counting rule.")
    if named:
        note += " Computed (exclusions reviewed by name): this unit's funds don't follow an SBOA fund-number chart."
    return status_badge("computed", page, note)


def money_in_out(ed, page, mid: str, level: int = 3, label: str | None = None) -> Markup | None:
    rows = _rows(ed, mid)
    if not rows:
        return None
    c = page.cites
    kind = _kind(ed, mid)
    noun = KIND_NOUN[kind]
    hx, hy = f"h{level}", f"h{min(level + 1, 6)}"
    anchor = ed.unit_alias(mid) or mid
    sp_year = _pick_year(rows, ("by_purpose",))
    in_year = _pick_year(rows, ("income",))
    held_years = sorted({r["year"] for r in rows if r["view"] == "income" and _held(r)})
    def sel(view, year):
        return [r for r in rows if r["view"] == view and r["year"] == year]
    purpose, by_type = sel("by_purpose", sp_year), sel("by_type", sp_year)
    sp_excl = sel("spending_excluded", sp_year)
    income, in_excl = sel("income", in_year), sel("income_excluded", in_year)
    sp_src = ";".join(dict.fromkeys(s for r in purpose + sp_excl for s in split_ids(r["source_ids"])))
    in_src = ";".join(dict.fromkeys(s for r in income + in_excl for s in split_ids(r["source_ids"])))
    sp_total = sum(_f(r["amount"]) for r in purpose)
    in_total = sum(_f(r["amount"]) for r in income)
    sp_x = sum(_f(r["amount"]) for r in sp_excl)
    in_x = sum(_f(r["amount"]) for r in in_excl)
    borrowed = sum(_f(r["amount"]) for r in in_excl if r["category"].startswith("Borrowed"))
    out = []
    title = label or "Money in and money out"
    yl_sp = _year_label(kind, sp_year) if sp_year else ""
    yl_in = _year_label(kind, in_year) if in_year else ""
    out.append(h(hx, {"class": "sp-h"}, f"{title}, {yl_sp}" if yl_sp == yl_in or not yl_in else title))
    scope = [f"Actual money received and spent, as reported to the state for {yl_sp}" +
             (f" (income: {yl_in})" if in_year and in_year != sp_year else "") + ", all funds. ",
             f"Not counted in the charts: {usd(in_x)} of money in and {usd(sp_x)} of money out that passed through "
             f"{noun}'s books or moved between its own funds (listed below the charts). ",
             _badge(page, purpose + income), c.cite(";".join(dict.fromkeys(split_ids(sp_src) + split_ids(in_src))))]
    if kind == "school":
        scope.insert(1, "The state's file lists school data under the year the school year begins. ")
    out.append(h("p", {"class": "sp-scope"}, scope))

    # 1 income
    if income:
        civil_note = "" if kind == "school" else (" The state file uses one code for state and federal grants to "
                                                   "this kind of unit, so the two are shown together.")
        out.append(h(hy, {"class": "sp-sub"}, "Where the money comes from"))
        dev_note = None
        if any(r["category"] == "Development-area reimbursements" for r in income):
            dev_note = h("span", None, " Development-area reimbursements are payments into the county's economic "
                                       "development area funds, most likely the companies repaying the county for "
                                       "water and sewer lines it builds at their expense for the New Carlisle "
                                       "projects; the state file does not name the payer.", c.cite("MON-069"))
        held_note = None
        for y in held_years:
            if y > (in_year or ""):
                hr = next((r for r in rows if r["view"] == "income" and r["year"] == y), None)
                if hr:
                    held_note = hr["notes"].split("HELD (not charted): ", 1)[-1].split(" Receipt lines:")[0].split(" Folded into Other:")[0]
        out.append(h("div", {"class": "sp-grid"},
                     _bars(f"sp-{anchor}-income", f"Income by source, {yl_in}", income, page,
                           f"Counted income {usd(in_total)}",
                           h("span", None, "Taxes, state and federal money, charges and other receipts. Transfers "
                                           "between its own funds, borrowing and money held for others are not "
                                           "counted (see below)." + civil_note,
                             (" " + held_note) if held_note else "", dev_note),
                           c.cite(in_src))))
    # 2 spending
    if purpose:
        out.append(h(hy, {"class": "sp-sub"}, "How it is spent"))
        figs = [_bars(f"sp-{anchor}-purpose", f"Spending by purpose, {yl_sp}", purpose, page,
                      f"Counted spending {usd(sp_total)}",
                      ("Grouped by the state's functional classes for schools: instruction, support services "
                       "(including buses, building upkeep and administration), food and other services, buildings "
                       "and construction, and debt." if kind == "school" else
                       "Grouped by the fund that paid. General operations is the general fund, which pays for many "
                       "departments, so it is not one program. Economic development includes TIF, redevelopment and "
                       "local income tax for economic development."),
                      c.cite(sp_src))]
        if by_type:
            figs.append(_bars(f"sp-{anchor}-type", f"Spending by expense type, {yl_sp}", by_type, page,
                              f"Counted spending {usd(sp_total)}",
                              "Grouped by the state's expense classes: what the money bought (pay and benefits, "
                              "contracts, supplies, construction and equipment, debt payments).", c.cite(sp_src)))
        out.append(h("div", {"class": "sp-grid"}, figs))
        if kind == "school":
            out.append(h("p", {"class": "sp-note"}, "The state's school file reports spending by function only, not by "
                                                     "expense type, so schools have one spending chart."))
    # income vs spending, one neutral line
    if income and purpose and in_year == sp_year:
        diff = in_total - sp_total
        big = max(in_total, sp_total)
        bits = []
        if big and abs(diff) > 0.10 * big:
            if diff < 0:
                bits.append(f"In {yl_sp}, counted spending was {usd(-diff)} more than counted income. A difference "
                            "like this usually means projects paid for with money borrowed or saved in earlier years.")
            else:
                bits.append(f"In {yl_sp}, counted income was {usd(diff)} more than counted spending; money not spent "
                            "during the year stays in the unit's fund balances or is set aside for later projects.")
        if borrowed:
            bits.append(f"{noun[0].upper() + noun[1:]} also borrowed {usd(borrowed)} that year (not counted as income).")
        if bits:
            out.append(h("p", {"class": "sp-note"}, " ".join(bits)))
    elif borrowed:
        out.append(h("p", {"class": "sp-note"}, f"{noun[0].upper() + noun[1:]} also borrowed {usd(borrowed)} in {yl_in} "
                                                 "(not counted as income)."))

    # 3 pass-through block
    groups = [g for g in GROUP_TEXT if any(r["category"] == g for r in in_excl + sp_excl)]
    if groups:
        trs = []
        for g in groups:
            lab, line = GROUP_TEXT[g]
            if g.startswith("Collected for other") and kind == "county":
                line = h("span", None, COUNTY_PASS, c.cite(COUNTY_PASS_SRC))
            vin = next((r for r in in_excl if r["category"] == g), None)
            vout = next((r for r in sp_excl if r["category"] == g), None)
            trs.append([h("span", None, h("strong", {"class": "sp-kind"}, lab), h("span", {"class": "sp-what"}, line)),
                        usd(vin["amount"]) if vin else "none", usd(vout["amount"]) if vout else "none"])
        trs.append([h("strong", None, "Total not counted"), usd(in_x), usd(sp_x)])
        blk = [h(hy, {"class": "sp-sub"}, "Money that passes through or moves between funds (not counted above)"),
               h("p", None, f"This money is in {noun}'s report to the state, but it isn't {noun}'s own income or "
                            "spending, so the charts above leave it out. It is shown here because it is part of what "
                            "the books record. ", h("a", {"href": page.rel("money/what-is-a-budget/index.html")},
                                                    "What counts as a budget?")),
               data_table(f"sp-{anchor}-passthrough", ["Kind of money", f"Money in ({yl_in})",
                                                       f"Money out ({yl_sp})"], trs,
                          caption="Money not counted in the income and spending charts", numeric=(1, 2),
                          min_width=None)]
        det = sel("passthrough_detail", sp_year)
        if det:
            blk.append(_bars(f"sp-{anchor}-passfunds", f"Largest pass-through funds, money paid out, {yl_sp}",
                             [dict(r, category=r["category"].rsplit(" (", 1)[0]) if r["category"] != OTHER else r
                              for r in det], page,
                             f"{usd(sum(_f(r['amount']) for r in det))} collected for other governments and paid on",
                             "By fund, as named in the state file. Settlement funds carry the property and excise "
                             "taxes the county collects for the local governments in the county; the LIT funds carry "
                             "local income tax distributions.", c.cite(sp_src + ";" + COUNTY_PASS_SRC)))
        out.append(h("div", {"class": "sp-pass"}, blk))
    return h("div", {"class": "sp-block", "id": f"money-{anchor}"}, out)


def money_id_for(ed, unit_id: str) -> str | None:
    """The money-file id (e.g. 'city-south-bend') whose rows map to a units.csv id (e.g. 'south-bend')."""
    _rows(ed, "")
    for mid in ed._spending_cache:
        if ed.unit_alias(mid) == unit_id:
            return mid
    return None
