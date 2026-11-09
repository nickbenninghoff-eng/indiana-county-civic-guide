# Local campaign finance: coverage notes

Companion to `data/editions/st-joseph/cf_coverage.csv` (office x cycle matrix) and `cf_local.csv` (478 filings from
510 summary-sheet docs). Built by `tools/build_cf_local.py` and checked by `tools/validate_cf_local.py`.

## How cycles are assigned
A filing's cycle comes from its `period_to` as written on the form (never from the county's batch folder):
through 2023 → **2023 municipal**; 2024 → **2024**; 2025-2026 → **2026**. Annual or final reports that close in
January-March count toward the previous year (e.g. a 2024 annual running to 2025-01-14). The 2025 annual reports are
counted in the 2026 cycle. For city and town offices (next elected in 2027) those 2025 reports are off-cycle; the
matrix notes say so. Seven filings with no period on the form are in a "period unknown" bucket.

`committees_with_all_expected` counts committees that filed every report type posted for that cycle:
2023 = Annual; 2024 = Pre-Primary, Pre-Election and Annual (or Final); 2026 = 2025 Annual, Pre-Primary and Pre-Election.

## Where the data is most complete
* **2023 municipal:** 79 committees, 80 filings; 76 committees have their annual report (the only 2023 report posted).
* **2024:** 120 committees, 169 filings, but only 14 committees have the full pre-primary + pre-election + annual set.
  The best-covered offices are County Commissioner District 3 (2 of 6 committees complete), County Council District I
  (2 of 4) and County Treasurer (2 of 3). Most township, school-board and municipal committees have only an annual
  report in 2024.
* **2026:** 156 committees, 222 filings; 17 committees complete. County Council Districts A (2 of 2), B (2 of 3) and
  C (2 of 3) are the most complete. The party and PAC committees are also well covered (4 of 6 complete). Clerk of
  the Circuit Court, Assessor, Auditor, Prosecutor and Commissioner District 1 each have one complete committee.

## Known gaps
1. **Nothing posted before 2023.** The county's pages start with the 2023 annual reports. One 2022 report
   (doc 60824, period to 2022-12-31) was posted with them, along with a few multi-year final reports that reach back
   to 2022. There are no 2023 pre-primary or pre-election reports.
2. **No 2026 post-election reports yet.** The 2026 annual reports (period ending 2026-12-31) are not due until January 2027.
   The latest 2026 pre-election periods end in October 2026, plus a few filers who wrote a later date.
   The 26 CFA-11 large-contribution notices (36 entries, in `cf_large_contributions.csv`) cover part of the gap
   between the pre-election report and election day.
3. **Doc 70515 (Sharon Brinker, 2026 pre-primary tab): RESOLVED 2026-11-08** (re-pulled in Chrome; summary sheet on page 3; figures transcribed and tied to doc 72776's opening cash). Original note: The rendered pages are a Schedule B and the
   form instructions; the summary sheet is beyond page 2 of the 8-page PDF. Not fetched. Brinker's 2026 pre-election
   report (doc 72776) is in `cf_local`.
4. **Doc 66024 (2024 delinquent tab):** the county's typed list headed "Annual CFA 4 NOT Completed" names
   **18** committees/candidates that had not filed 2024 annual reports. Only the count is recorded here.
5. **Doc 65627 (Canneth Lee, 2024 annual): unreadable.** The scan is washed out; it is in `cf_local` with
   `transcription_status = unreadable` and no figures. The few legible cells are in its notes. A better copy is needed.
6. **Doc 68321 (Eli Wax, 2025 annual)** was served as a PNG with a `.bin` extension. It was missed by the first pass and
   transcribed during adjudication (single reading). No action needed beyond a second read if wanted.
7. **12 filings have no office on the form** and no other form from the same committee that names one, so
   `office_normalized` is blank (row "(no office stated on form)"). Where results.csv shows the candidate on a ballot,
   the notes say so, but the office is not filled from it.
8. **Report periods that look miswritten are shown as written:** doc 66082 (Eli Wax, period written 2023 but evidently
   the 2024 report), doc 68014 (period written 2026 in the 2025 batch), and the 2016-for-2026 slips on CFA-11 docs
   72951 and 71873.
9. 2024 municipal-office committees: Mishawaka and South Bend council committees mostly have only annual reports,
   because there was no city election in 2024.
