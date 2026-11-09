# Money in and money out charts: QA report (2026-11-08)

Scope: for each local government, show where the money comes from and how it is spent, using actual dollars from Indiana Gateway Annual Financial Reports (AFR). Money that is not the unit's own (passed through, moved between its own funds, borrowed, held for others) is shown separately and not charted. Nothing has been committed.

## Sources (sources_money.csv, appended rows MON-060..MON-068)

| id | what | local copy |
|---|---|---|
| MON-060 | Gateway AFR Disbursements by Fund, 2025, county 71 | sources/money/gateway_afr_disbursements_byfund_2025_county71.psv |
| MON-061 | same, 2024 | sources/money/gateway_afr_disbursements_byfund_2024_county71.psv |
| MON-062 | SBOA Funds Table (county chart of accounts, master 07/16/26) | sources/money/sboa/Funds-and-Accounts-Master-07_16_26.pdf |
| MON-063 | Gateway AFR Receipts, 2025, county 71 | sources/money/gateway_afr_receipts_2025_county71.psv |
| MON-064 | same, 2024 | sources/money/gateway_afr_receipts_2024_county71.psv |
| MON-065 | SBOA school manual, chapter 4 (school chart of accounts, 2025 update) | sources/money/sboa/SCHMAN04-2025Updated63025jw.pdf |
| MON-066 | SBOA revised fund numbers, cities and towns | sources/money/sboa/REVISED-FUND-NUMBER-CITIES-TOWNS.pdf |
| MON-067 | SBOA fund list, libraries | sources/money/sboa/Libraries_ChartofAccounts.pdf |
| MON-068 | SBOA county chart of accounts instructions | sources/money/sboa/county_chart_of_accounts_instructions.pdf |

The Gateway file-layout documentation and a saved copy of the download page (school year convention) are in sources/money/gateway_docs/. The SBOA PDFs are git-ignored (`sources/**/*.PDF` rule) like the other source PDFs. WebSearch calls used: 5 of the 20 allowed.

## Exclusion rule (same fund rule for money in and money out)

1. **Whole funds, by the SBOA fund-number ranges** for the unit's type:
   - County (MON-062, MON-068): 6000s settlement and distribution funds; 7100-7499 remittance (state and other-government shares); 5000-5999 payroll withholding and clearing; 4700-4749 self-insurance and 4016 IT internal service; 0001-0099 outside funds (clerk, sheriff and other money held for others).
   - Cities and towns (MON-066): 7701-7799 internal service; 8801-8825 pension and other trusts; 8850-8899 custodial; 8901-8999 payroll and clearing.
   - Schools (MON-065): 630 pension trust; 1100-1110 self-insurance; 1800-1849, 2300-2399, 2700-2799, 8000-8999 trust and custodial series; 9000-9999 clearing (payroll).
   - Libraries (MON-067): 700-799 internal service; 800-850 clearing; 900-999 trust.
2. **Named exceptions** where the chart is silent or the unit numbers funds its own way (South Bend, Indian Village, townships and special units have no usable chart). Each has a written reason in `NAMED_FUNDS` / `NAMED_PATTERNS` in tools/build_spending.py. These units show the badge "computed (exclusions reviewed by name)".
3. **Lines inside counted funds** that only move money between the unit's own funds: money out = section 4 (Transfers Out, other financing uses), D704 transfer out, D705/D706 interfund loans, D900 investments. Money in = R910 Transfers In, R911/R912 interfund loans and investments, school class 10 transfers, and cost-allocation receipts.
4. **Borrowing** (money in only): R903/R904 and school class 8 debt proceeds. Shown as "also borrowed $X", never counted as income.
5. **Counted once**: a county fund with the same fund number and amount as a special unit's fund in the same file is left to that unit ("Reported by another unit as its own").

Reconciliation is enforced in code: for each unit and year, counted + not counted = the file total, to the cent, on both sides. The build stops otherwise.

## Results, year used 2025 (2024 rows also in the file)

Money out (disbursements):

| unit | file total | counted | not counted | rule |
|---|---|---|---|---|
| county-st-joseph | $1,056,345,369 | $272,259,219 | $784,086,150 | SBOA chart |
| city-south-bend | $507,298,509 | $436,192,171 | $71,106,338 | named review |
| city-mishawaka | $262,535,078 | $206,022,922 | $56,512,157 | SBOA chart |
| school-sbcsc | $365,204,857 | $285,392,217 | $79,812,640 | SBOA chart |
| school-phm | $294,584,608 | $181,762,175 | $112,822,432 | SBOA chart |
| school-mishawaka | $111,897,747 | $80,899,126 | $30,998,621 | SBOA chart |
| school-john-glenn | $33,699,607 | $26,720,281 | $6,979,325 | SBOA chart |
| school-union-north | $21,103,052 | $17,041,559 | $4,061,493 | SBOA chart |
| library-sjcpl | $37,112,712 | $24,392,647 | $12,720,065 | SBOA chart |
| library-mishawaka | $8,108,034 | $8,028,575 | $79,459 | SBOA chart |
| library-new-carlisle | $1,337,494 | $1,220,095 | $117,398 | SBOA chart |
| library-walkerton | $298,344 | $280,352 | $17,992 | SBOA chart |
| special-airport | $67,314,241 | $49,555,883 | $17,758,358 | named review |
| special-redevelopment-authority | $13,053,329 | $12,541,056 | $512,274 | named review |
| special-sb-transpo | $19,550,424 | $11,263,084 | $8,287,340 | named review |
| special-solid-waste | $4,086,797 | $3,914,889 | $171,909 | named review |
| special-regional-water-sewer | $1,656,817 | $1,302,718 | $354,099 | named review |
| town-north-liberty | $15,709,333 | $12,784,978 | $2,924,355 | SBOA chart |
| town-new-carlisle | $14,268,599 | $11,250,980 | $3,017,619 | SBOA chart |
| town-walkerton | $13,190,400 | $11,170,904 | $2,019,496 | SBOA chart |
| town-osceola | $2,609,113 | $2,122,920 | $486,193 | SBOA chart |
| town-roseland | $2,034,364 | $1,403,870 | $630,494 | SBOA chart |
| town-lakeville | $1,779,447 | $1,141,845 | $637,602 | SBOA chart |
| town-indian-village | $54,107 | $54,107 | $0 | named review |
| township-clay | $18,576,986 | $15,302,416 | $3,274,570 | named review |
| township-portage | $11,557,061 | $10,556,387 | $1,000,674 | named review |
| township-penn | $6,976,859 | $5,944,223 | $1,032,636 | named review |
| township-centre | $6,258,131 | $3,805,564 | $2,452,566 | named review |
| township-olive | $5,020,655 | $3,949,016 | $1,071,639 | named review |
| township-warren | $1,718,454 | $1,697,399 | $21,054 | named review |
| township-union | $1,527,309 | $1,347,932 | $179,377 | named review |
| township-liberty | $1,323,433 | $1,271,334 | $52,100 | named review |
| township-harris | $1,153,450 | $1,140,784 | $12,666 | named review |
| township-madison | $566,692 | $555,741 | $10,951 | named review |
| township-german | $476,034 | $465,951 | $10,083 | named review |
| township-greene | $279,292 | $69,292 | $210,000 | named review |
| township-lincoln | $191,560 | $183,781 | $7,779 | named review |

Money in (receipts), counted income / not counted / of which borrowed: county $288,664,906 / $801,764,750 / $14,534,628; South Bend $340,798,275 / $119,265,359 / $7,424,128; Mishawaka $206,359,777 / $61,788,451 / $0; SBCSC 2025 held (see below), 2024 shown: $282,665,287 / $63,942,805; PHM $149,368,014 / $121,451,270 / $7,950,000; Mishawaka schools $79,593,707 / $31,200,847 / $472,000; John Glenn $27,230,537; Union-North $16,962,953; SJCPL $21,195,372 (borrowed $4,639,836); airport $50,791,698; Transpo $2,833,473; Portage township $9,388,130 (borrowed $4,000,000); Union township borrowed $1,082,950; North Liberty borrowed $457,091. The full list prints when tools/build_spending.py runs.

Skipped (not covered by the guide, or multi-county): Michiana Area Council of Governments; Elkhart and St. Joseph Counties Head Start Consortium; St. Joseph River Basin Commission; St. Joseph County Soil and Water Conservation District; St. Joseph County Housing Consortium.

## Categories

- **Spending by expense type** (civil units): the file's object classes: 100 Salaries and benefits; 200 Supplies; 300 Services and contracts; 400 Township assistance; 500 Debt payments; 600 Capital projects; 800 Utility operating costs; 700 Other.
- **Spending by purpose** (civil units): the fund that paid, run through an ordered rule table (`PURPOSE_RULES`, first match wins): General operations; Utilities; Debt service; Township assistance; Economic development; Public safety and justice; Roads and streets; Parks, recreation, culture; Health; Planning and code enforcement; Central services and IT; Buildings and reserves; Grants; Gifts and donations; then Other. Every fund lands somewhere, and the test suite checks this.
- **Schools**: purpose = the file's functional classes (51 Instruction, 52 Support services, 53 Food and other services, 54 Buildings and construction, 55 Debt payments, 56 Other). The school file does not split spending by expense type, and the page says so.
- **Income**: civil units = Property taxes; Local income tax (LIT); Other local taxes; State and federal money; Utility bills; Charges, fees and fines; Interest earnings; Refunds and reimbursements; Other. Schools = Property taxes; Other local money; State money; Federal money; Other.
- Each chart shows the 6 largest plus Other. When there are exactly 7, all 7 are shown by name.
- Funds with more than 1% of a unit's counted spending that fell to Other: airport Miscellaneous Tax Receipts (3.2%); Roseland LOIT Special Distribution (1.3%); Walkerton Interest Earned (1.3%) and Non Reverting Operating (1.0%); Olive township Cemetery Fund 2024 (3.2%).

## Decisions for Nick

1. **SBCSC 2025 receipts are held.** The receipts file shows $251.8M of property tax in the Education Fund, and total receipts are $619.7M against $365.2M in disbursements. That looks misreported, so the page shows 2024 income with a note. The 2025 rows stay in the CSV, marked `_held`.
2. **South Bend Transpo fund 4 (payroll)** is excluded as payroll clearing. This leaves Transpo with only $2.8M of counted income, because most of its receipts are clearing, loans and transfers. Please confirm.
3. **South Bend 222 Central Services and 279 IT** are kept as spending, though they may work as internal service funds. 714 parental leave is also kept.
4. **County 1201/1204/1205** (tax-sale surplus and overpayments) are excluded as held for others, although the chart lists them as special revenue. 4020 fleet motor pool is excluded as internal service and 4917 recorder's escrow as held for others. Clerk fund 0022 (Quest) is kept.
5. **School 8400 prepaid lunch** is excluded under the 8000-series trust range, although the table lists it as type 2.
6. **Pension trust funds** (city and school) are excluded as held for others.
7. **Harris township D703 distributions** are counted as spending.
8. **County GM-Samsung and solid-waste funds** are excluded as reported by another unit, so they are counted once with that unit.
9. **Cost-allocation receipts** are treated as moved between own funds. **Portage township 5100 health insurance** is excluded as internal service.
10. **Civil units' state and federal money are one category**, because receipt codes R129-R134 are shared by state and federal grants. Schools are split.
11. **School year label**: Gateway says the year is the start of the school year, so 2025 = "2025-26 school year". Indiana school budgets are now on a calendar year, so this is worth a second look.
12. **Phones**: below 760px each chart keeps a 480px minimum and scrolls sideways inside its own box so the text stays readable. The page itself never scrolls sideways. This departs from the other charts on the site, which scale down.
13. **Income checks to look at**: Harris, Liberty and Union townships take in more than 1.5 times what they spend (2025). Portage township's counted income is more than twice its 2024 level.
14. Skipped soil and water district and housing consortium (no units.csv/budgets.csv entry).

## Tests

`python -P -E -m unittest discover -s tools/tests`: **17 tests, OK** (tools/tests/test_build_spending.py). They cover:

- known exclusions: county Settlement 6000, LIT shares, 5353/5354 withholding, 4700 health insurance, tax-sale surplus, outside funds; city, school, library and township equivalents; Transfers Out and D704/D705/D706/D900;
- the Settlement Fund amount;
- reconciliation to the cent, spending and income, every unit, both years;
- `by_type` summing to `by_purpose`;
- excluded categories summing to the excluded totals;
- pass-through detail rows summing to their group;
- the fund rule being identical for income and spending;
- debt proceeds always in Borrowed, never income; Transfers In excluded;
- every counted fund categorised; known purposes;
- `fold_top` behaviour (6 + Other, 7 named, Other last, ordering);
- school handling (no `by_type`, functional classes, Union-North present, year label);
- skipped units;
- the CSV on disk matching a fresh build.

The site build `python -P -E tools/site/build.py --edition st-joseph --check` **PASSED** (60 pages).

## Browser QA (Playwright, own isolated tab)

Pages:

- county#money
- places/south-bend, places/mishawaka, places/walkerton (town), places/clay-township (township)
- schools (5 corporations)
- money/budgets#money-in-out (9 libraries and special units)

Each page was checked at 1280 and 400px, in light and dark, in the ballot, line and wayfinding looks: 84 combinations, all clean.

- The page never scrolls sideways (overflow -15 at both widths).
- No element of a money block extends past the viewport.
- Chart labels do not overlap and are not clipped.
- All bars use `m-accent`: rgb(15,118,110) in light, rgb(45,212,191) in dark. No other colours.
- The grid is 2 columns at 1280 and 1 column at 400.
- The smallest chart text is 8.1px at 400px and 8.7-9.0px at 1280.
- No console errors or warnings.

Found and fixed during QA: in the wayfinding look, the county pass-through table scrolled inside its box at 400px because the base `table.data thead th { white-space: nowrap }` rule beat the block's override. The selector was made more specific, and the table now fits.

## Files changed

- New: tools/build_spending.py, data/editions/st-joseph/spending_breakdowns.csv (generated, 1513 rows), tools/site/civic/spending.py, tools/site/static/css/spending.css, tools/tests/test_build_spending.py, sources/money/sboa/*.pdf, sources/money/gateway_docs/*, this report.
- Edited: tools/site/civic/data.py (table registered, unit-id and view checks), tools/site/pages/county.py (new "Money in and money out" section 8), tools/site/pages/places.py (place pages and the Schools page), tools/site/pages/money.py (new section 6, libraries and special units), data/SCHEMA.md (spending_breakdowns entry).
- Appended rows only: data/editions/st-joseph/sources_money.csv (MON-060..MON-068).
- Not touched: Roadmap.md, docs/session-handoff.md, tools/build_money.py, tools/res_main.py, and every other data CSV.
