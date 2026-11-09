# Held money data: what was added (2026-11-08)

Nick approved these five datasets on 2026-11-08. They are data files only: nothing under `tools/site/` was edited, nothing is committed, and `tools/build_money.py` and `tools/res_main.py` were not run. The row-level log is in `data/editions/st-joseph/_corrections_applied_money.md`, in the section dated 2026-11-08.

## Added, by file

| File | Change |
|---|---|
| `data/editions/st-joseph/assessed_values.csv` | New, 732 rows: 256 `dlgf_certified` (2020-2026) and 476 `gateway_budget_estimate` (2012-2026) |
| `tools/build_assessed_values.py` | New builder. It writes only assessed_values.csv and needs PyMuPDF |
| `tools/tests/test_build_assessed_values.py` | New, 8 tests |
| `data/editions/st-joseph/indicator_values.csv` | +104 rows: 90 enrollment, 12 per-student, 2 state median |
| `data/indiana/indicators.csv` | +3 indicator definitions |
| `data/editions/st-joseph/budgets.csv` | +2 rows: South Bend 2026 adopted all funds; Redevelopment Commission 2026 amended |
| `data/editions/st-joseph/debt.csv` | +1 row: South Bend debt at 2026-01-01 |
| `data/editions/st-joseph/sources_money.csv` | +9 sources, MON-070 to MON-078 |
| `data/editions/st-joseph/gaps_money.csv` | 4 rows narrowed to what is still missing |
| `data/SCHEMA.md` | Documents assessed_values.csv, the table-only budget bases and kinds, the debt_type convention and the school indicators |
| `sources/money/` | Downloaded source files: `dlgf/` (budget orders 2020-2026, the 2022 amended order, the per-capita report), `idoe/` (enrollment xlsx), `southbend/` (March 2026 monthly report) |

## 1. Assessed value: the plan changed

**Finding.** The Gateway "Net Assessed Valuation" column is not the certified tax base. In 2026 it differs from the DLGF budget order for every unit that has both.

| Unit | Certified (budget order) | Gateway value | Difference |
|---|---|---|---|
| County | $14,611,493,562 | $10,000,000,000 (a round number) | -31.6% |
| South Bend | $4,396,041,441 | $3,358,949,843 | -23.6% |
| Mishawaka | $2,126,759,474 | $1,368,537,661 | -35.7% |

The full range runs from -35.7% (Mishawaka) to +2.7% (Airport). The Gateway figure is the unit's own working estimate, entered with its budget: many are round numbers, some are 0 or blank, and one is an obvious typo (Transpo 2014: $3,922,136).

**What I did instead.**
- **Certified values, 2020-2026.** I downloaded the county's DLGF certified budget orders for 2020-2026. The 2020 and 2021 orders are 404 on in.gov, so I used Internet Archive copies of the same DLGF URLs. I parsed the "Certified AV" column for every unit.
- **Gateway values kept, labelled.** They are in the file as `basis=gateway_budget_estimate`. Each row's note says by how much it differs from the certified value, where one exists.
- **2012-2019.** Only Gateway estimates exist for these years. Certified orders for them were not on the DLGF county page.

**Which fund.** Within a unit the AV can differ by fund, because fire territories, fire and debt funds, and school referendum funds cover different areas. Each row uses:
- the General fund (0101) for most units;
- Operations (3300) for schools;
- the fund named GENERAL for special units.

The `fund` column says which fund was used, and the notes list every other AV the order shows for that unit.

**Checks.**
- **D's proposals.** All 37 of D's 2026 values are reproduced exactly.
- **Hand checks against the PDF:**
  - county, p.5;
  - South Bend, p.21 (I viewed the rendered page; its General fund budget of $108,537,364 also equals budgets.csv);
  - Mishawaka, p.23;
  - Penn, p.16;
  - Portage, p.17;
  - SBCSC, p.37;
  - PHM, p.35;
  - SJCPL, p.42.
- **Older orders.** The county's 2020-2022 values were cross-checked with pdftotext: $9,386,302,045, $9,833,605,785 and $10,534,325,712.
- **Gateway duplicates.** Every Gateway row appears exactly 5 times and no duplicates conflict. The test checks this.

**Observation, not explained.** From 2025, John Glenn's Operations AV ($664.6M in 2025, $693.8M in 2026) is larger than its Debt Service AV ($454.2M in 2026). The difference equals Greene Township's AV, so the operating district appears to include Greene from 2025. The order does not say why.

## 2. Enrollment and spending per student

**Year convention, verified.**
- IDOE's data page lists the file as "Corporation Enrollment by Grade Level - (Updated - SY 2025-2026)". Sheet "2026" is therefore school year 2025-26, and the vintage is labelled "IDOE enrollment, school year 2025-26".
- Corroboration: the statewide kindergarten count drops in sheet "2021" (78,649 to 72,993), which is the fall-2020 school year.
- The file does not state a count date, so I did not claim one.
- Aggregators that show 14,486 for SBCSC "2025-26" are a year behind: that matches IDOE 2023-24 (14,484).

**Indicators added** (defined in `data/indiana/indicators.csv`):
- `school_enrollment_total`: 6 corporations, 2011-12 to 2025-26, whole corporation.
- `school_spending_per_student`: calendar years 2024 and 2025. DLGF divides total expenditures, net of interfund loans, transfers and investment purchases, by average daily membership (ADM).
- `school_spending_per_student_median`: state rows giving the median corporation, $15,983.06 for 2024 and $17,286.94 for 2025.

**Checks.** All 12 per-student values and their state ranks were checked visually on the rendered report pages:
- SBCSC: $24,129.63 (2024) and $24,600.56 (2025)
- PHM: $11,406.67 and $17,963.83
- Mishawaka: $20,017.68 and $15,241.25
- John Glenn: $11,047.54 and $14,144.41
- New Prairie: $14,111.19 and $14,617.30
- Union-North: $14,133.40 and $14,782.51

**Rebuild risk.** `tools/build_indicator_values.py` regenerates indicator_values.csv and would drop these 104 rows. SCHEMA.md now says so.

## 3. South Bend 2026 adopted budget: found

**The ordinance.** Ordinance No. 11229-25 (Substitute Bill 56-25), "2026 Annual Budget Appropriation and Property Tax Levy", passed 2025-10-13 and presented to the Mayor 2025-10-14. It is WebLink DocView id 401021, folder Ordinances > 2025, and is MON-078.

**Exhibit A grand total: $437,446,265.** I read it on the page image (p.8, "Page 5 of 5").
- The department totals sum to $437,446,264, a $1 rounding difference.
- The OCR text layer misreads the City Clerk total as 672,863; the image shows 572,863.

**Scope.**
- Includes water works funds 620, 622 and 625 (about $60.5M) and sewage works funds 641, 642 and 649 (about $60.4M).
- Transpo has its own ordinance, 11230-25.
- The Redevelopment Commission is not included.

**The row.** budgets.csv: `city-south-bend,2026,all_funds_incl_utilities,437446265,adopted,sb-ordinance-adopted-appropriations,official,MON-078;MON-030`.
- It is inserted just before the 2027 rows.
- The built South Bend place page still reads "Latest: $439,062,691 for 2027 (adopted ...)".

**Difference from the overview deck.** The September 2026 overview's "2026 Budget" figure ($429,975,283) was not used. It is $7,470,982 below the ordinance, and neither document says why; this is kept as a gap row.

## 4. Redevelopment Commission, 2026 amended budget: verified and added

**Verified in MON-077**, the March 2026 monthly report.

The Expenditure Summary (p.15), "Current Amended Budget", gives a total of $135,109,942:

| Funds | Amount |
|---|---|
| Tax increment financing funds | $107,047,275 |
| Redevelopment funds | $27,032,666 |
| Debt service | $1,030,000 |

The parts sum to $1 less than the printed total. The Revenue Summary (p.12) gives $48,613,328.

**The row.** It uses `basis=amended_all_funds` and `adopted_or_actual=amended`. That makes it non-primary in `money.py` (it is neither a BASIS_ORDER basis nor "adopted"), so it lands in the "Other reported figures, not charted" table. This is confirmed in the built page.

## 5. South Bend debt at 2026-01-01: verified and added

**Verified in MON-077**, pp.26-27: Total Debt at 1/1/26 is $298,686,137.

| Part | Amount |
|---|---|
| Civil city | $181,211,137 |
| Redevelopment Commission revenue bonds | $117,475,000 |

The civil city figure breaks down as:
- bonds, including water and sewage works revenue bonds: $157,333,000;
- capital leases: $21,502,679;
- loans: $1,970,636;
- interfund loan: $404,822.

The report projects $270,264,580 at 12/31/26.

**The row.** debt.csv, with a debt_type that does not start "Total end-of-year principal", so it stays off the 2024 chart.
- It is inserted after the existing 2026-09-04 row, so money.py's `sb_city` (the first non-2024 South Bend row) is unchanged.
- The note explains the date and source differences from the Gateway 2024 rows and from the budget page's $280.7M.

## Not found or not done

- **Certified AV 2012-2019.** Not on the DLGF county page. Lead: South Bend WebLink edoc 57819 holds the 2015 order pages for South Bend units only, as a scan.
- **Per-student spending before 2024.** Not pulled; earlier DLGF per-capita reports would have it.
- **RDC adopted budget, and any year after 2017.** Not located.
- **Ordinance vs overview difference.** Why the South Bend overview shows $7.47M less than the ordinance is not explained.

## Display hooks for the site agent

### 1. Assessed value (`assessed_values.csv`)

New loader: `ed.table("assessed_values")`.

**Chart only `basis == "dlgf_certified"`.**
- Never put `gateway_budget_estimate` on the same axis.
- If shown at all, show it in a separate table, labelled as "the unit's estimate entered with its budget".

**Money > Budgets page:**
- **"How the tax base shapes budgets" section (`_tax_base`).** money.py line ~874 currently says the guide "does not yet have reliable assessed values by unit". Replace that with:
  - a certified-AV-over-time line for the county, South Bend and Mishawaka, 2020-2026;
  - a 2026 bar chart of certified AV by unit.
- **Per unit (`_unit_charts`).** Optionally add a small "tax base (certified AV)" line per unit.
- **Cross-county units.** New Prairie, Union-North, John Glenn and PHM are the St. Joseph County part only, so say so.

**Place pages** (places.py, the Budget section near `_budget_rows` / `money_in_out`):
- add "Tax base: $X certified net assessed value for 2026 (DLGF budget order)" with the row's source;
- map ids with `money_id_for(ed, uid)`;
- the county page gets the same.

**AV per resident.** Use the 2026 certified AV divided by `Money.population(mid)` (ACS 2020-2024).
- It works for the county, South Bend, Mishawaka and townships.
- Badge it as computed.
- For townships, note that the township AV includes the cities inside it.
- For the county, note that it covers everyone, city residents included.
- Suggested place: the "Per resident" section of the budgets page, as a third chart: "Certified assessed value per resident, 2026".

**Tax bill page (`build_tax_bill`).** Optionally explain that a rate times the certified AV equals the levy. Example: South Bend General, $2.1267 per $100 × $4,396,041,441 = $93,490,613, as on budget order p.21.

**Gaps.** The hub's gap pattern `assessed` already picks up the narrowed gap row.

### 2. Enrollment and spending per student

**Schools page (places.py `build_schools`, ~line 869).** It currently prints "Enrollment: Not in the guide's data yet". Replace that with:
- the latest `school_enrollment_total`, labelled "school year 2025-26", with a small 2011-12 to 2025-26 trend;
- the corporation id is the existing `school_district` geo_id (97000US...), so map school unit to geo by name the way `_school_unit` / the community code does.
- Add "Spending per student: $X (calendar year 2025; state median $17,286.94)" from `school_spending_per_student` and the state row `school_spending_per_student_median`. Badge it official and cite MON-076.
- Caption it: "total spending divided by average daily membership; not classroom spending; calendar year, not school year".
- Do not divide budgets by enrollment yourself: the enrollment count includes pre-K and differs from ADM.

**Community page.** `community_history.py` ~line 812 says "school enrollment are not in the guide's data yet". Its gap rows (~824-829) also say "No school_district rows". Both are now stale: point the text to the Schools page.

**Optional.** A 2025 per-student bar chart for the six corporations, with the state median drawn as a line.

### 3. South Bend 2026 adopted budget

**No code change is needed for it to chart.**
- It joins `sb-ordinance-adopted-appropriations`, the primary series of the all_funds_incl_utilities chart.
- The chart now shows "16 years with figures, 2012 to 2027".
- The 2027 adopted row stays the last row, so the place page and `place_budget_row` are unchanged (verified).

**Legend fix.** The legend in `_unit_charts` (money.py ~line 456) says "Gateway (state budget file), adopted" for every primary point. The ordinance points (2026 and 2027) are not from Gateway. Suggested legend label: "Gateway sum (2012-2023) or council ordinance (2026-2027), adopted". Alternatively, drive the label from the row's `series_id` or `source_ids`.

### 4. Redevelopment Commission, amended 2026

**Add a label** in money.py next to `BASIS["dlgf_certified"]`:

```python
BASIS["amended_all_funds"] = ("Amended budget, all funds (later financial report)",
                              "The unit's current amended budget for every fund it controls, from a financial report after adoption.")
```

Until that is added, the "Other reported figures" table shows the raw key `amended_all_funds` in its Basis column.

**Kind column.** It shows "amended" — fine.

**Checker.** Add `amended_all_funds` and `amended` to `tools/check_money.py`, which is already stale for `dlgf_certified`, 2027 rows and certified rate kinds.

### 5. South Bend debt at 2026-01-01

**Already rendered** in the "Debt by class and unit" table, and not charted.

**Paragraph update.** The paragraph under the 2024 debt chart (money.py ~line 709) mentions only the budget page's $280.7M, with a hard-coded date "2026-09-04". Suggest replacing it with both city-reported figures:
- "$298.7M at 2026-01-01 (civil city $181.2M + Redevelopment Commission bonds $117.5M; monthly financial report, MON-077)";
- "roughly $280.7M as of 2026-09-04 (budget page, MON-005)".

The data change is safe: `sb_city = next(... year != "2024")` still picks the 2026-09-04 row. Select rows by `debt_type` instead of by position, rather than relying on that.

**Optional.** On the South Bend place page, a line "Debt: $298.7M at the start of 2026 (city report)".

### 6. Rebuild risks

- **`tools/build_indicator_values.py`** would drop the 104 school rows. Either teach it these indicators or never re-run it without re-adding them.
- **`tools/build_money.py`** would drop the budgets, debt, sources and gaps edits, as before.
- **`tools/build_assessed_values.py`** is safe to re-run.
