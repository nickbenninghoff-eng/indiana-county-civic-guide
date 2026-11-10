# Fact-check 2026-11-09: government money (agent F4)

Scope: budgets.csv, budget_breakdowns.csv, spending_breakdowns.csv, tax_rates.csv, assessed_values.csv, debt.csv, audits.csv
and the money pages (your-tax-bill, budgets, what-is-a-budget, data/budgets, data/debt, data/tax-rates, places money sections).
No CSV, builder or page file was edited: no confirmed error was found. Two source ambiguities and one unverifiable set are listed below.

## Checked in bulk (every row of the type, recomputed independently from the raw source)

| File / kind | Rows | Source | Result |
|---|---|---|---|
| budgets.csv advertised_all_funds, all_funds_incl_utilities, gateway_reported_funds, general_fund (MON-001) | 547 | sources/money/gateway_budget_county71_2012-2026.psv (de-duplicated; the 5x duplicate rows are identical) | all match to the dollar |
| tax_rates.csv sum_of_fund_net_rates | 471 | same PSV, sum of Net Tax Rate_adopted | all match (<= 0.00006) |
| tax_rates.csv general_fund_net_rate + park_fund_net_rate | 60 | same PSV | all match |
| tax_rates.csv certified_district_unit_rate 2025, 2026 | 376 | DLGF xlsx 2025/2026 (note: the 2026 file has the fund and district columns swapped relative to its header; the build handles it) | all match |
| tax_rates.csv certified_unit_rate 2026 (37) and 2025 (36) | 73 | DLGF budget orders (Unit Total lines: budget, levy, rate) | all match |
| tax_rates.csv certified_district_rate 2026, 2025 | 62 | budget order district table | all match |
| certified_district_rate 2024, 2023 | 62 | 2025/2024/2023 order comparison columns | match (comparison columns agree) |
| certified_district_rate 2022 | 31 | statewide xlsx 2022 re-downloaded (matches CSV exactly) | CSV = source; but see ambiguity A1 |
| tax_rates: sum of unit rates in each district vs district rate, 2025 and 2026 | 62 districts | CSV internal | all within 0.0005 |
| assessed_values.csv dlgf_certified 2020-2026 | 256 | budget-order PDFs: every AV value appears in the matching year's order; county, South Bend, Mishawaka, PHM, SBCSC, SJCPL General/Operations lines confirmed by unit for 2026 and 2023 | all OK |
| debt.csv 2024 class rows, totals, principal due | 51 class rows + totals/due | gateway_afr_debt_2024_county71.psv | all match |
| budget_breakdowns.csv afr_2024_actual_by_department | 32 | gateway_afr_disbursements_2024 PSV | all match; file totals $92.65M county, $110.25M South Bend, $42.52M Mishawaka match scope notes |
| spending_breakdowns.csv: counted + excluded = file total (spending) and income + excluded = receipts total, every unit, 2024 and 2025 | 39 units x 2 years | AFR disbursements-by-fund and receipts PSVs | reconciles to within $1 everywhere; 0 failures |
| spending_breakdowns.csv share column | all by_type, by_purpose, income rows | recomputed from amounts | all within 0.01 point |
| audits.csv filed dates and periods | 9 | SBOA PDFs/text in sources/recovered | all 9 match |

## Spot checks against primary documents

- Roseland special investigation 19010I (sources/recovered/sboa-towns/19010I_roseland.txt): complaint April 9, 2024; 65 debit-card Remitly transfers July 1 to Sept 23, 2024 totaling $10,500.30; 31 from Philippine IP addresses, $5,345.05; fireworks $1,019.30 (July 8, 2024); $11,519.60 + $10,621.50 = $22,141.10 charged; $38,300.70 questioned; $13,660 snow-plowing check; exit conference Dec 16, 2025; resignation Sept 11 / effective Sept 28 / rescinded Sept 26 / accepted Sept 30. All OK.
- South Bend 2027 expenditures $433,757,721, revenue $422,271,665, deficit $11,486,056 (General Plus $6,889,289, other $4,596,767), 2026 column $429,975,283: confirmed in sources/recovered/sb-2027-budget overview.
- South Bend 2024 overview (MON-006, fetched): grand total revenue $420,595,379, 2023 adopted $440,353,102, expenditures $447,213,320, net deficit $26,662,759. All match the CSV. The 14 revenue rows sum to the total; the PDF text has 14 labels and 14 values, the unlabeled last value row (6,024,186) lines up with PILOT, which supports the builder's label alignment (property taxes $94,996,997 ... PILOT $6,024,186). Alignment is structurally consistent but the PDF extraction offsets labels by one line, so it is not independently proven.
- Redevelopment Commission amended 2026 total $135,109,942 and revenue $48,613,328: confirmed in the March 2026 monthly report.
- County 2026 certified budget $135,682,675, levy $84,469,044; General fund budget $90,704,400 (rate 0.4207; levy 61,470,553 / AV 14,611,493,562 = 0.4207): OK.
- Your tax bill page, district 026 South Bend - Portage 2026: $4.9445 = 0.5781 + 2.6802 + 0.1278 + 1.1774 + 0.2487 + 0.0943 + 0.0380; shares 11.7, 54.2, 2.6, 23.8, 5.0, 1.9, 0.8 percent correct. 2025 $5.0426, 2024 $5.3548, 2023 $5.2897, 2022 $5.8190 match the order tables / statewide file.
- What-is-a-budget: 90,704,400 / 248,200,414 = 36.5%; / 135,682,675 = 66.9%; Mishawaka 49,604,404 / 77,919,352 = 64%; South Bend 62 to 83 funds with a budget per year 2012-2023 and 10 funds 2024: all recomputed from the PSV and correct.
- Money map: county $272,259,219 / 272,912 = $998; South Bend $436,192,171 / 103,453 = $4,216; Mishawaka $206,022,922 / 51,063 = $4,035; SBCSC, PHM, John Glenn counted-spending figures equal spending_breakdowns sums; South Bend "spending exceeded income by $95,393,896" = 436,192,171 - 340,798,275. OK.
- "Tax base: $X certified net assessed value for 2026 ($Y in 2020, +Z%)" on 29 places pages: all 29 match assessed_values.csv, growth percentages correct.
- Constant-dollar factors use data/indiana/cpi_u.csv (2012-2024 values match the BLS CPI-U annual averages I know; 2025 321.943 not independently verified).

## Fixes made

None.

## Unresolved / for Nick

A1. 2022 combined district rates, six districts (source ambiguity, not changed). tax_rates.csv takes 2022 from the DLGF statewide file (MON-033); it equals that file exactly. For districts 014 Lincoln (2.3292), 015 Walkerton (3.8431), 017 Olive (2.9454), 018 New Carlisle (4.1418), 034 Liberty (2.2046), 035 North Liberty (3.4692), the DLGF "Amended" 2022 budget order (sources/money/dlgf/St-Joseph-County-Budget-Order-2022-Amended.pdf, cross-county New Prairie unit, LaPorte AV change, 2022-05-16) and the 2023 order's comparison column both show higher values: 2.3301, 3.8440, 2.9721, 4.1685, 2.2055, 3.4701. The other 25 districts match the amended order. The original (pre-amendment) order matches the CSV for exactly those six, so the statewide file looks like a hybrid. The amended order is the later, final certification; the six 2022 figures on the tax bill page history line are probably slightly low (0.0009 to 0.0267 per $100). Only affects the "2022: $x" history line for those districts. Recommend switching to the amended-order values and citing MON-072 (amended copy), but it needs your call on which source governs.

A2. Local copy sources/money/southbend/Ordinance-11229-25_2026-Annual-Budget-Appropriation.pdf is 0 bytes (the source note says the direct download returned 0 bytes and the figure was read in the WebLink viewer). So the South Bend 2026 ordinance total $437,446,265 and the 2027 ordinance total $439,062,691 (MON-032; the packet in sources/recovered is a scan) could not be re-derived by me. Needs browser check. The 2027 overview ($433,757,721 expenditures) is verified.

A3. Mishawaka 2026 budget book figures (MON-010: $77,919,352 total, 15 funds, Fire $20,482,149, Police $17,343,945, Controller $5,960,348) and the 2024 book number $70,250,671 have no local copy; the Gateway sum for 2026 equals the stated total, the fund breakdown was not re-derived. Not checked.

A4. South Bend 2025 counted income ($340.8M) is $95.4M below counted spending ($436.2M); the page states this plainly. Not an error, but unusual: spending includes capital funds paying out earlier bond proceeds. Not investigated further.

A5. Population denominators (SBCSC 163,905 etc.) come from indicator_values.csv (another agent's area); not verified here.

## Not searched / not done

No web search used. sjcindiana.gov items: none needed. News-sourced rows (MON-007, 008, 009, 013, 014, 015, 036) not re-fetched; they are labeled secondary and quoted as published. Rows in budgets.csv for county/units 2027 (none exist). SBOA audits other than Roseland 19010I: only filed dates and periods checked, not findings text.

## Builder fixes needed

None.

## Build, checks, tests

No edits made, so no rebuild. tools/check_money.py: OK (all rows parse, no series mixes bases). tools/check_gov.py: errors=0, warnings=23 (not mine). Unit tests were started but not awaited (nothing changed by this agent).
