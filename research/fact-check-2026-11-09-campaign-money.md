# Fact-check 2026-11-09: campaign finance (agent F3)

Scope: cf_local, cf_coverage, cf_delinquent, cf_large_contributions, cf_reported, cf_state, cf_state_history, cf_state_pacs and their sources, plus the money/campaigns pages. No CSV, builder or page file was changed (no confirmed error found).

## Whole-table checks (all rows)
- cf_local (479 rows): cash identity (start + receipts - spent = end) for both the period and year-to-date columns. 74 failures, every one is a row already marked `filer-inconsistent` (the form's own arithmetic does not tie; shown as filed with a note). No unflagged row fails. Dates in order except 8 rows with a blank/short period_to (documented as unreadable). Two apparent duplicate keys (Oliver Davis, 2025-01-14 and 2026-01-20 annuals) are separate zero-activity filings, not duplicates of one report.
- cf_coverage filings sum (479) equals cf_local rows (479). All source_ids resolve in sources_cf_local / sources_money / sources_cf_method.
- cf_state (100), cf_state_history (263), cf_state_pacs (61): every row re-summed from sources/money/cf/{year}_{Contribution,Expenditure}Data.csv.zip by FileNumber (history, PACs) or exact Committee name (cf_state), by filing year. 424 of 424 receipts and expenditures match to the cent; row counts quoted in the notes match; top-funder types spot-checked for 40 cf_state rows (2022, 2024-2026) match.
- Page display: every cf_state / cf_state_history / cf_state_pacs row appears on the built pages (state-legislature, other-committees) with the CSV figures, year and committee. All cf_local period receipts/spent/cash figures appear on the built pages (negatives shown as -$x).
- tools/validate_cf_local.py: OK. tools/check_money.py: no errors (only the existing year-over-year jump listing). tools/cf_double_entry_diff.py crashes with ZeroDivisionError (no second-reading input files present); not a data problem, not touched.

## Figures re-derived from the scans (page images in sources/cf/img)
cf_local, all match the form: cfl-72804 Critchlow 2026 pre-election (all lines); cfl-60871 Mueller 2023 annual (all lines); cfl-66217 Dem Central Committee 2024 annual; cfl-72791 Baxmeyer 2026 pre-election (17c derived, correct); cfl-72952 GOP 2026 pre-election amendment (as filed, cents off on form, noted); cfl-72833 Drake and O'Brien PAC 2026 (17cB 131,140.46 as filed, filer typo, noted); cfl-62625 Cichowicz 2024 pre-primary; cfl-68147 Cichowicz 2025 final (as filed).
cf_large_contributions: 73118 Wozny $11,500 (10/26/2026) and 73121 Pfeil $8,000 (4/22/2026) match.
cf_delinquent: all 18 names and order match the 2024 "Annual CFA 4 NOT Completed" list (doc 66024).
Cycle totals on the county page re-added by hand: Baxmeyer 2026 cycle ($245,956.96 raised / $220,367.66 spent = 2025 annual + 2026 period sums; the 2026 pre-election year-to-date column is wrong on the form, its Jan 1 cash is the pre-primary close, so the page's choice of period sums is right and reconciles to closing cash $68,639.96); Cichowicz 2024 cycle ($161,073.80 raised / $207,956.46 spent) match.

## cf_reported (34 rows vs cited articles, fetched from Wayback PDFs / Yahoo)
Checked against text: MON-081 (Howey 2007: $253,939, $118,892, $152,913, $33,797, $17,200 after Oct. 12), MON-082 (Howey 2011: $229,875.71, $127,192, $100,063.12, $69,204.79, $56,009, $19,382.82), MON-085 (Howey 2019: nearly $245,000, $91,000, about $153,000, $139,000, about $98,000, $40,000 wording as in the item, $19,000, $16,600, $15,300), MON-086 (Howey 2015: $136,605, $76,631.97, $365,479.94, $2,292, $2,087.26, $204.74), MON-087 (Manigault "more than $30,000"), MON-084 (Yahoo/Tribune P-H-M 2022: all six candidates' totals and the two non-filers). All OK. Not re-read: MON-083 (WNDU rounding, corroboration only) and the Critchlow $40,000 / Coleman / Williams-Preston / Davis lines beyond the text found (Coleman, Williams-Preston, Davis OK; Critchlow $40,000 OK).

## Counts
Checked about 700 figures (424 state rows fully re-summed, 479 cf_local rows mechanically, ~35 cf_reported, ~25 hand-read scan figures, 18 delinquent names, 2 CFA-11 entries). OK: all. Fixed: 0. Unresolved: 0 data errors.

## Observations (source ambiguity, not changed)
- Cichowicz 2025 final (cfl-68147): the filer wrote $12,397.54 as receipts and as expenditures (it is the closing cash balance). The page lists it as a 2026-cycle report "listed with the other reports" with $12,397.54 raised/spent. Transcribed as filed and flagged filer-inconsistent; the "raised" figure is probably the filer's error, but it is what the form says.
- 17 "filer-inconsistent" rows rest on the form's own typos; notes already document each.

## Not checked
sjcindiana.gov pages (blocked for scripts, not needed; scans are local). The remaining ~400 cf_local rows were only checked by the identity and page-presence tests, not against the images. No WebSearch used.
