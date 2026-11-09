# Session handoff — Indiana County Civic Guide (St. Joseph County edition)

Last updated: 2026-11-08. Read `Roadmap.md` (Phase 5) first; this file is the short "where things stand" note.

## What this is
Static, sourced, nonpartisan-by-rule civic guide to St. Joseph County / South Bend / Mishawaka / towns / townships,
built to be reusable for other Indiana counties. Python stdlib generator; data in CSVs.

- Build: `python -P -E tools/site/build.py --edition st-joseph --check` → must end `PASSED: ...` and print no `BUILD FAILED`.
- Precinct data: `python -X utf8 -P -E tools/build_precinct_results.py --edition st-joseph`, then
  `python -P -E tools/build_map.py --edition st-joseph`.
- Governance data check: `python -P -E tools/check_gov.py` (0 errors since 2026-11-08).
- Local preview: pm2 process `civic-guide-preview` serving `site/st-joseph` on http://localhost:8787. Not saved with
  `pm2 save`, so it does not survive a reboot. Restart it (after a build, since `site/` is not in git) with:
  `pm2 start C:\Python313\python.exe --name civic-guide-preview --cwd C:\Users\nickb\local-gov-guide -- -m http.server 8787 --directory C:/Users/nickb/local-gov-guide/site/st-joseph`
  Run it from Bash: PowerShell 5.1 drops the bare `--`, and pm2 then rejects `--directory`.
- Private review link (Artifact, not public): https://claude.ai/artifact/3oF7hxKBPhBpq4S74vuHQ2 — republish with
  `file_path=site/st-joseph/index.html`, `root=site/st-joseph`, files from `planning/publish-files.json`
  (regenerate it if pages/assets change: every html except index + `assets/*` + referenced images).
- Theme options canvas (historical): https://claude.ai/artifact/EL6H3Knjif1ZfuVb4e5KHo

## Current state (all verified by build + browser unless noted)
- Three reader-selectable looks (Ballot & Ink default, Line Map, Wayfinding), light + dark; 400px no-overflow checked.
- Boundary map (cities/towns, townships, school corporations) + "How areas voted" layer:
  Level (Federal / State / County / Township & town) → Office → District/Township/Town → Year.
  102 races (2020/2022/2024 general ballots, every partisan race with precinct data). Every race's county/district sum
  equals the official totals except 2024 Probate Judge (marked "county sum not checked"; results.csv row is from_scan).
  Vote data in `assets/map-votes.json` (~477 KB, loaded on demand).
- OpenElections corrections (documented in `tools/build_precinct_results.py`, with county-report page refs; build
  stops if upstream changes): 2020 U.S. House Olive Twp 1 (16→106), Greene Twp 2 (158→156); 2020 South Bend 130111
  House 8 row filed as Senate 8.
- Party labels next to every person; body breakdowns like (5 D, 4 R).
- Disclosure: Nick is an organizer for the St. Joseph County Democratic Party; guide made independently on his own time.
- "State audits" section on every town page from `data/editions/st-joseph/audits.csv` (9 SBOA reports; Roseland 2024
  special investigation summarized in full, with an "About SBOA charges" explainer).

## Decisions this session (and why)
- Keep the precinct-level view; remove "report slant"/corrections-contact wording — Nick prefers more public data over
  appearing neutral (memory: feedback_civic-guide-data-over-optics). Accuracy, sourcing and equal rules stay mandatory.
- Reverted a review agent's lime map palette to calm teal/amber/neutral (optics-only change, looked garish).
- Did NOT use Indiana Gateway's employee-compensation lookup: it requires agreeing to no political use (IC 5-14-3-3(f)).
- Included the Roseland SBOA findings incl. items about the council president (Nick: "Yes"); no criminal charges found
  in news as of 2026-11-08 — re-check before any public release.
- Added township & town races to the map (Nick: "Add them"); multi-seat races colored by combined party votes with a
  stated caveat when parties ran different numbers of candidates.

## Known issues / open items
- SBCSC 2016 at-large fixed 2026-11-08 (two seats; McCullough did not win in 2016). Only the printed "Vote for" line on View/60008 is unread.
- **tools/site/ (the whole generator) was never in git**: .gitignore `site/` matched it. Now `/site/`; 58 files untracked, waiting on Nick's commit.
- Don't rerun tools/res_main.py over results.csv: it drops ~30 later hand fixes (see Roadmap).
- 2026-11-08 later: gap-fill pass applied (~340 edits; planning/qa/gapfill-2026-11-08-applied.md) and Money in and money out charts built (tools/build_spending.py → spending_breakdowns.csv; tests: `python -P -E -m unittest discover -s tools/tests`). Both UNCOMMITTED; decisions for Nick listed in Roadmap Phase 5. Never run res_main.py or build_money.py (they erase hand edits).
- 2026-11-08 research applied: SB 2027 adopted $439,062,691; LaVille rename 4-0 June 9, 2025; Wax seated Nov 24-Dec 14, 2020; Roseland no charges as of 2026-11-08. check_money.py is stale (518 false errors).
- Still not found: Eli Wax's oath day (window Nov 24-Dec 14, 2020); South Bend 2026 adopted all-funds total; the June 8,
  2026 LaVille resolution tally (minutes have none).
- Certified 2026 results: re-run when the county posts the certified canvass (2026 rows are unofficial).
- 2013 ABC57 story on an earlier Roseland clerk charged with theft — offered to Nick, not researched.
- Nick's Downloads folder: 21 sjc-*/sb-2027budget-* PDFs, all hash-verified copies in `sources/`; recycling blocked
  because Adobe Acrobat holds them open — close Acrobat, then send to Recycle Bin.

## Repo notes
- Public GitHub repo (Nick approved public, 2026-11-08). No license file yet (Nick to choose). Raw full-text dumps of
  source documents (`sources/recovered/**/*.txt`) are ignored because they contain private individuals' contact details.
- Git repo created 2026-11-08. `.gitignore` excludes `site/` (build output), caches, and
  binary downloads under `sources/` (PDF/ZIP/images/XLSX/DOCX, ~1.6 GB; URLs are in the `sources_*.csv` files). Text
  inputs the builds read (OpenElections CSVs, county report text/OCR, boundaries, Gateway/ACS extracts) ARE committed.
  A fresh clone can rebuild data and site, but the OCR step (`tools/ocr_2020_precinct_report.py`) and campaign-finance
  rebuild need the ignored PDFs re-downloaded.
- Commit and deploy only on Nick's explicit trigger words (global CLAUDE.md). Public hosting = deploy trigger.

## Waiting on Nick
- Commit + push of everything since b2f89ed (gap-fill edits, money charts, budgets map when done) — only on his "commit"/"push".
- Which map-navigation pages to build next (audit 2026-11-08 recommends: Places, Schools, election-results links to the
  map; then Community data pages reusing the budgets map's shading mode; skip Your tax bill unless he wants it).
- Format for held money data (item 4 of his decisions): net_assessed_value.csv (37 units, DLGF 2026 budget order),
  school enrollment + per-pupil spending (42 rows; need indicator ids), SB 2026 $429,975,283 (derived from a 2027 deck,
  not the ordinance), RDC 2026 $135.1M amended budget, city debt $298.7M at 1/1/2026. I owe him a concrete proposal.
- License for the public repo (suggested: MIT for code, CC BY 4.0 for data/text) — none added yet.
- Whether to keep the Gmail address on commits or switch git to the GitHub noreply address.
- Close Adobe Acrobat, then the 21 leftover PDFs in Downloads can go to the Recycle Bin (all have copies in `sources/`).
- Optional: research the 2013 Roseland clerk theft case for the town's history.
- Public hosting of the site: only on Nick's explicit deploy trigger.

## Session 2026-11-08 (evening) — state at compaction
- Committed/pushed: b2f89ed (site generator into git, SBCSC 2016 fix, SB 2027 adopted budget, LaVille, Wax, Roseland,
  map panel keeps last area). Everything after that is UNCOMMITTED in the working tree.
- Done, uncommitted, verified: gap-fill pass (~340 edits; planning/qa/gapfill-2026-11-08-applied.md; check_gov 0 errors;
  I spot-checked judges, Robles/Monterrosa, Lakeville 2015, New Prairie 2024) and Money in and money out charts
  (tools/build_spending.py → spending_breakdowns.csv; civic/spending.py; 17 tests pass; I re-checked reconciliation
  against the raw Gateway files to the dollar; county page viewed at 1280px). Build PASSED.
- New sources downloaded (Nick gave blanket permission for public source material; saved as memory): Gateway AFR
  Disbursements by Fund 2024/2025 and Detailed Receipts 2025, filtered to county 71 in sources/money/*.psv.
- Running: Opus agent building the budgets-page money map (spending per resident shading, Nick's choice; hover panel;
  click → unit's money section; table for units without boundaries). Report → planning/qa/budgets-map-2026-11-08.md.
- Nick's decisions (2026-11-08): (1) investigate county "Refunds and reimbursements" $71.0M — IN PROGRESS: $61.2M is
  R906 receipts into New Carlisle Dev Area #1 ($33.8M) and #2 ($27.4M) TIF funds, which spent ~$68M that year; need a
  public source for who paid (likely developer reimbursement under a development agreement), then relabel/annotate in
  tools/build_spending.py (I_REFUND rule ~L596-617) and rerun it + tests. (2) Find and fix the SBCSC 2025 income
  discrepancy ($619.7M in vs $365.2M out; $251.8M property tax in the Education Fund) — NOT STARTED. (3) Greene Twp
  trustee phone: publish (already in units.csv) — resolved. (4) He asked what I need for the held money data → give a
  concrete format proposal.
- Rules learned: never run tools/res_main.py or tools/build_money.py (both erase hand edits); check_money.py is stale.

- UPDATE (later 2026-11-08): decisions (1)-(3) DONE (see Roadmap). Nick said "yes, go ahead with all five" for the
  held money data → Opus data agent running (assessed_values.csv + tools/build_assessed_values.py, enrollment and
  per-pupil indicators, SB 2026 adopted from the Oct 2025 ordinance, RDC 2026 amended, city debt 1/1/2026; data files
  only; report planning/qa/held-money-data-2026-11-08.md with DISPLAY HOOKS). Budgets-map agent also queued (Nick
  approved): Places map, Schools map, election-results → map race links, Community data "shade by indicator";
  NOT the tax-bill page. After both finish: send the display hooks to the map agent (it owns places.py/money.py/map
  code), then verify (build, tests, browser), then ask Nick to commit.

- UPDATE 2: budgets map + Places/Schools/results-links/Community maps DONE (49 tests, build PASSED, I checked the budgets
  map in the browser). Nick: race/Hispanic shares TABLE ONLY on community maps (done: RACE_IDS removed from the people
  page map call); keep towns visible. Held money data DONE (planning/qa/held-money-data-2026-11-08.md): assessed values
  from DLGF certified budget orders 2020-2026 (Gateway NAV is NOT the tax base; kept as labelled estimates), SB 2026
  adopted $437,446,265 (Ord. 11229-25), enrollment + per-student indicators, RDC amended, city debt. Map agent resumed
  to wire them into pages, fix the population-name bug (map.py), and update stale check_money.py. Then: verify, ask
  Nick to commit.

- UPDATE 3: map agent round 2 DONE, per its report (planning/qa/budgets-map-2026-11-08.md sections 7-10), not yet
  verified by me:
  - population() now matches by census_name (School City of Mishawaka 30,799; LaVille 7,532);
  - new civic/tax_base.py: certified AV line and bars on the budgets page, AV per resident, a "Tax base:" line on
    place, county and school pages, and in the map panels;
  - new civic/school_stats.py: enrollment and spending per student vs the state median on the Schools page and panels;
  - legend, amended_all_funds label, two city debt figures;
  - per-resident charts were empty (picked 2027); they now compare 2026;
  - check_money.py: 0 errors (was 613);
  - 67 tests pass.
  Items for Nick: per-resident AV uses ACS on the page but the 2020 Census in the panel; cross-county AV is the
  county part only; optional extras were skipped (levy example, AV per budget block, SB "Debt:" line, per-student
  bars); LaVille has no budget rows.
  VERIFIED by me 2026-11-08: build PASSED (60 pages), 67 tests OK, check_gov 0 errors, check_money 0 errors, browser:
  budgets AV-per-resident chart, money-map panel tax base, Schools enrollment/per-student lines. NEXT: ask Nick to commit;
  everything since b2f89ed is still UNCOMMITTED.

- 2026-11-09 NEW REQUEST (Nick): reorganize /money/campaigns/ (one 384 KB page; 479 filings, 231 candidates) around a map
  with a race-type filter and a side panel like /budgets. Nick's answers: (1) FIND OFFICIAL DISTRICT MAPS FIRST
  (county commissioner + council, city council, SBCSC board, Walkerton wards; plus state House/Senate) so each district
  is its own shape; (2) panel money = WHOLE-CYCLE spending per candidate summed across reports on file + party sums,
  with reports-on-file vs expected and an 'incomplete' flag; (3) SPLIT into area pages (index = map + filter + short
  list; Campaigns > <area> pages: races > candidates > filings; full table moves to an 'All filings' page + CSV);
  (4) INCLUDE state legislative districts (cf_state = sitting legislators by filing year, label the different basis).
  Status: plan + token estimate given to Nick; waiting on his go before launching agents.

## Next step
(Superseded by the UPDATEs above.) Finish decision (1) (source + relabel the New Carlisle TIF reimbursements), then (2) the SBCSC 2025 receipts check,
then answer (4) with a concrete proposal; review the budgets-map agent's report when it lands (rerun build + tests,
look at the page in the browser); then ask Nick which map pages to build next and whether to commit.
