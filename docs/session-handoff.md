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
  Nick: "commit and push first, then go ahead" -> committed+pushed b6d5d28 (all prior work). Launched 2026-11-09:
  Sonnet research agent (district maps -> sources/boundaries/districts/*.geojson + manifest.csv, MAP-020..059,
  report planning/qa/district-maps-2026-11-09.md) and Opus build agent (campaigns index map + area pages + All filings
  + how-it-works; sources CFM-010..029; report planning/qa/campaigns-map-2026-11-09.md). When research lands, send the
  build agent a follow-up to wire districts if it has not. Then verify (build, tests, check_gov, browser) and ask Nick to commit.
- 2026-11-09: Nick asked why the 11-08 map audit missed campaigns and to redo it. Cause: it only considered existing
  boundaries, silently skipped pages, and I did not check its coverage (memory: feedback-page-audits-cover-every-page).
  Redo: page inventory planning/qa/page-inventory-2026-11-09.tsv (60 pages, by size/rows); Sonnet survey agent (read-only,
  one row per page) -> planning/qa/page-navigation-survey-2026-11-09.md. I then judge and give Nick a ranked list.
  DONE: survey has all 60 pages (I checked against the inventory). Ranked list given to Nick; waiting on his picks.
  New map work should wait for the campaigns agent (it is editing the map code).
- Nick picked all of items 1-9 with models "Sonnet, then Opus". Sonnet agent running NOW on the fixes that are not
  maps (5 data split, 6 about sources page, 7 landscape filters, 8 calendar filter, 9 collapse Gaps/Sources; report
  planning/qa/page-navigation-fixes-2026-11-09.md). Opus map batch (1 legislators, 2 county, 3 budgets per unit,
  4 schools) starts AFTER the campaigns agent finishes. Not approved: tax-bill picker; "click your spot" all-districts.
- District research DONE (planning/qa/district-maps-2026-11-09.md; 9 searches): GeoJSON for commissioner 1-3,
  council A-I, SB council 1-6 (Ord. 10906-22), Mishawaka 1-6 (medium confidence), House HD5,6,7,8,21, Senate SD8-11;
  MAP-020..039. SBCSC = image-only PDF (raw/sbcsc-board), Walkerton = street descriptions only. Sent to campaigns agent.
- Non-map fixes DONE per agent (planning/qa/page-navigation-fixes-2026-11-09.md; 87 tests): /data/ split into 13 pages,
  /about/sources/ with search, table_filter helper (landscape, calendar), Gaps/Sources folds, anchor forwarding (moved.js).
  NOT yet verified by me. Build has 2 broken links from in-progress campaigns pages; about->campaigns#method is in
  meta.py, which the campaigns agent was told not to touch: I fix that link myself after it finishes. Nick questions:
  Copy CSV copies all rows when filtered; landscape still 69 screens (paging or split?).

## Next step
(Superseded by the UPDATEs above.) Finish decision (1) (source + relabel the New Carlisle TIF reimbursements), then (2) the SBCSC 2025 receipts check,
then answer (4) with a concrete proposal; review the budgets-map agent's report when it lands (rerun build + tests,
look at the page in the browser); then ask Nick which map pages to build next and whether to commit.

## Session 2026-11-09 — running agents (state for compaction)
- Campaigns rebuild DONE (planning/qa/campaigns-map-2026-11-09.md): index map, 30 area pages, how-it-works,
  all-filings, district shapes (tools/build_district_shapes.py → derived/district_shapes.json). I verified: build
  PASSED (109 pages), 114 tests, check_gov 0, check_money 0, browser panel. I FOUND A BUG: the nested-period rule
  dropped Eli Wax's real 2023 annual (cfl-60837, $30,287.82 spent) because cfl-66082 (probably misdated 2024) is
  dated all of 2023 → panel showed "Republican (R) $61.63". Sent back to the campaigns agent: fix by cash chain,
  audit every dropped report, and make party sums say "N of M candidates with reports". AWAITING its fix.
- Campaigns decisions for Nick (from the agent): (1) the opening view is the whole county; (2) layers mix election years;
  (3) 2023 uses the filers' YTD (the county never posted 2023 pre-primary/pre-election reports); (4) adjusted expected
  reports; (5) split the 490 KB county campaigns page?
  Nick answered: (2) mixed years OK; (3) 2023 YTD yes; (4) adjusted expected reports OK; (5) wait for the UX review.
  (1) after explanation: KEEP the whole-county opening view (no change).
- Nick (2026-11-09): "this is way too much information... thoroughly investigate each page... We shouldn't have
  gigantic tables... more intuitive journey... keeping all of the information." His setup: ONE investigating agent,
  other agents on other tasks; map-click pages are "fine as is".
  RUNNING: Opus read-only UX reviewer (Chrome, own tab) → planning/qa/site-ux-review-2026-11-09.md (journey, shared
  patterns, every page with a verdict, build plan, questions). The landscape split is folded into it.
  RUNNING: Opus map batch (Playwright): legislators district map, county district map, budgets per-unit view, schools
  one-corp view, Copy CSV copies only the shown rows (Nick: "That's fine") → planning/qa/map-navigation-batch-2026-11-09.md.
- Everything since b6d5d28 is UNCOMMITTED (data split, about/sources, filters, folds, campaigns rebuild, districts).
- NEXT: verify the campaigns fix, then the map batch, then synthesize the UX review into a plan for Nick to approve.
- AUTHORIZATION (Nick, 2026-11-09, before sleeping): "Do a commit after the site-wide review is complete and the plan is
  established. After the commit, run the plan as you recommend. ... we can use the commit to return back if we have to."
  => COMMIT is authorized ONCE: after the UX review lands and I write the plan (planning/site-redesign-plan-2026-11-09.md),
  commit the working tree (campaigns, map batch, nav fixes, plan). NO push (not mentioned). NO deploy. Then execute the
  plan's batches without waiting for approval (subagents: implementation on Opus, mechanical on Sonnet). The commit is
  the rollback point. Usage guard: hook ~/.claude/hooks/usage-pause.sh (95% of 5h) needs Nick to register it in
  settings.json (guarded file; snippet given 2026-11-09).
- USAGE GUARD (Nick: pause all at 90% of 5h (was 95%), auto-resume after reset; no settings.json): background shell bi0ghe7fm (Nick: check every 15 min)
  running `USAGE_POLL_SEC=900 bash /c/Users/nickb/Indicators/trade-journal/tools/usage-guard.sh watch 90 99`.
  On "LIMIT REACHED": TaskStop every running agent (list below), start `usage-guard.sh wait 90 99` in the background,
  and do no other work. On "CLEAR TO RESUME": SendMessage each stopped agent "resume where you stopped; re-run your
  checks", then restart the watch. If the watch exits 2 (usage unreadable), treat it as over the limit and pause too.
  Running agents (2026-11-09 ~01:15 ET): UX reviewer a1adaadb3a52766f1 (opus), map batch aae2a5a09669d79ef (opus),
  campaigns fix a3470c306bf9fd68d (opus). Keep this list current as agents start and finish.
- 01:40 ET: campaigns Wax fix DONE and checked against raw filings (D5 $39,642.20; Wax $30,287.82; 66082 moved to
  2024; Verash, Dieter and Young Republicans recovered; 127 tests). I found Bolden-Simpson cfl-60884 using period
  $9,354.38 instead of YTD $24,607.97 (other blank-start 2023 annuals use YTD). Sent back (Part 4): fix the rule, audit
  all 22 2023 reports where YTD > period, and label YTD-based figures. Campaigns agent a3470c306bf9fd68d is running again.
- ~02:00 ET: UX review DONE (planning/qa/site-ux-review-2026-11-09.md, 109 pages, verdicts and a 9-batch build plan).
  PLAN WRITTEN: planning/site-redesign-plan-2026-11-09.md (open questions decided; B4 dropped per Nick's "Keep whole
  county"; waves A to E with models and file ownership). COMMIT waits until the map batch (aae2a5a09669d79ef) and campaigns
  Part 4 (a3470c306bf9fd68d) land and pass, so the rollback point builds clean. Then: commit (no push) → Wave A.
  Running agents now: map batch, campaigns Part 4.
- Campaigns Part 4 DONE and spot-checked (Mishawaka clerk $97,133.91 = 43,687.16 + 53,446.75; SB D5 $54,895.79): 2023
  uses the filer's YTD even when the form doesn't reconcile (flag ytd-unreconciled, visible note); other years keep the
  reconciliation gate; guard against cumulative YTD; 153 tests. Only the map batch (aae2a5a09669d79ef) is still running;
  when it lands and verifies → COMMIT (no push) → Wave A.
- ~02:40 ET: map batch DONE and verified (build PASSED 109 pages, 153 tests, check_gov 0, check_money OK, browser:
  legislators and county panels, schools collapsed). COMMITTED 240a3e8 = ROLLBACK POINT (not pushed; main ahead 1).
  Authorized by Nick's "Do a commit after the site-wide review is complete and the plan is established".
  WAVE A RUNNING: batch 0 bugs (Sonnet, Chrome) a41b089539960b172 → planning/qa/wave-a-batch0-2026-11-09.md;
  batch 1 shared patterns (Opus, Playwright) a9a5b11d6e16cb6f8 → planning/qa/wave-a-batch1-2026-11-09.md.
  Usage-guard agent list = these two. Next: verify Wave A → Wave B (batches 2 Opus, 3 Opus, 4 Sonnet; ≤3 at once).
  Map-batch data notes for Nick: four Superior Court seats with no current holder in terms.csv; school-new-prairie
  missing from derived/unit_id_aliases.csv; check the PHM seats wording (voted corporation-wide); cf_state name matching.
  Map-batch questions for Nick: fold county results by district? open the saved place by default? keep budgets "Show
  all units"? keep the legislators committee matrix? (Waves 7/8 will propose defaults.)
- Batch 0 DONE per agent (158 tests): .cov → .pcov on place pages; how-it-works ~20 screens (97-row grid); duplicate-CSS
  check in check.py; here-tag token pair; seat-diagram summary line. MY TODO in the Wave A check: B3 on index.html at
  400 px; B1/B3 in light mode and the other looks. Batch 1 is still running.
- ~03:30 ET: WAVE A VERIFIED (build PASSED, all tests OK, check_gov 0; browser: coverage grid 8,246 px in light;
  #contest deep link shows one contest + "Show every contest"; SB rail 7 real links). Not verified: the B3 seat
  diagram in light mode (it only shows once a place is chosen; recheck in Wave D). Batch 1 notes: results page 0.92 MB
  (batch 2 asked to slim); county rail map link → Treasurer 2024 looks arbitrary → batch 7 should drop or choose another.
  WAVE B RUNNING: batch 2 elections (Opus, Playwright) afdc5136dc7574827; batch 3 place template (Opus, Chrome)
  ae0573b497e66c905; batch 4 lists (Sonnet, Chrome) acb28aeb8aeddde1c. Reports planning/qa/wave-b-batch{2,3,4}-*.md.
  Usage-guard agent list = these three.
- Batch 4 DONE per agent (wave-b-batch4-2026-11-09.md; build PASSED 112 pages; 4 unit failures all on batch 2's
  in-progress pages). MY TODO at the Wave B check: JS-off + keyboard on history/people, all-filings, run pages;
  fix the entity_list helper (components.py): status_badge() escapes a Markup status → isinstance check (one line,
  after batches 2/3 finish); tbl-run-pick-copy anchor is gone (a copy button, acceptable).
- Batch 3 DONE per agent (wave-b-batch3-2026-11-09.md; 219 tests; places ~30% shorter; SB/Mishawaka council
  district maps; Walkerton wards listed, not drawn). Decisions taken: Party control before Budget (neutrality rule F6
  keeps Context away from the party-control chart) → accept; budget charts folded → accept for now, flag to Nick.
  Data note: the 2023 Walkerton judge race maps to office walkerton-judge vs offices.csv walkerton-town-judge → fix
  after Wave B. Only batch 2 (afdc5136dc7574827) is still running.
- ~05:00 ET: WAVE B VERIFIED (build PASSED 112 pages, 246 tests, check_gov 0, check_money OK; margins page 10 screens,
  landscape 3.5; old #margins forwards; the 599→608 write-in correction CONFIRMED: 9 races from 2012 had one named
  candidate plus an unnamed write-in line). Found: all-filings is JS-built (38 rows with JS off) → fix-up.
  RUNNING: fix-ups (Sonnet, Chrome) a1f726aeec8f5a194 [all-filings JS-off render, entity_list Markup, Walkerton
  judge contest→office alias + audit]; Wave C batch 5 judges (Sonnet, Chrome) a00d438ec0a12f2a8; batch 7 map-page
  follow-ups (Opus, Playwright) ad689fd287ee9bc5e. Usage-guard agent list = these three.
  For Nick's morning list: 599→608; party control before budget; folded budget charts on place pages; margins page
  0.83 MB; older races drawn on today's district lines (labelled); path 6 starts at turnout.
- Batch 5 judges DONE per agent (wave-c-batch5-2026-11-09.md; 252 tests; 14.3→7.5 screens). MY TODO: Playwright
  check at 1280/400, keyboard, JS-off (the agent only had a 597 px Chrome window).
  WAVE D batch 6 (nav and hubs, Opus, Chrome) a5332812644152724 started early: batches 2 and 4 are done and its files
  don't overlap the running agents. It includes the B3 seat-diagram light-mode check.
  Running now: fix-ups a1f726aeec8f5a194, batch 7 ad689fd287ee9bc5e, batch 6 a5332812644152724 (usage-guard list).
- ~06:00 ET: fix-ups DONE and VERIFIED (all-filings has 614 rows with JS off; entity_list Markup; CONTEST_OFFICE_ALIASES
  in civic/data.py: 59 aliases, all reviewed by me (school-board and at-large council spelling variants plus the
  Walkerton judge); unmatched contests 268→109; ambiguous ones left: Osceola wards 2011/2019, 2019g-osceola-unknown-office,
  2026g-new-prairie-schools-board-at-large-district-2). Batch 5 VERIFIED (400 px no overflow, 1280 = 6.1 screens,
  keyboard opens a row, JS-off fine). Running: batch 7 ad689fd287ee9bc5e, batch 6 a5332812644152724. Next: Wave E
  (batch 8 preselect, Opus; then batch 9 sticky nav, Sonnet) once batch 6 lands.
- ~06:40 ET: WAVE C VERIFIED (batch 7: build PASSED 113 pages, 277 tests, check_gov 0, check_money OK; only data change
  = derived/unit_id_aliases.csv +school-new-prairie (hand-maintained file, approved in the brief)). Seat wording "All
  voters in the corporation; member must live in X Township" CONFIRMED by me: PHM Madison seat 11,269 votes (2026) vs
  township pop 1,891. For Nick: someone could read the IC 20-23-4 board plans to confirm (Gaps row added). Running:
  batch 6 only. Next: Wave E.
- ~07:30 ET: WAVE D VERIFIED (build PASSED 113 pages, 298 tests, check_gov 0; browser: nav fits one row at 400 px
  dark; breadcrumbs from the sitemap; elections/index#vacancies forwards to how-it-works; hub 2.3 screens; Your place
  shows 45 place links with JS off). B3 seat-diagram second half fixed (.cite line-height). Note: the agent cleared
  civic-place in Chrome's localStorage (Nick's own saved place in that browser profile, if any, must be set again).
  Batch 6 questions, decided by me: keep "Your governments" heading → your-governments/; keep the legal page title
  "Judges and public questions"; dropping hand-written eyebrows = later cleanup; holder names on cards = later.
  WAVE E RUNNING: batch 8 preselect (Opus, Playwright) ab44df71ab1d3eeca; batch 9 sticky nav + anchor landing + phone
  masthead (Sonnet, Chrome) a69ab885790a97ba2. Usage-guard list = these two. After Wave E: final full check, update
  Roadmap + handoff, morning summary for Nick. NO second commit (only one was authorized).
- ~08:20 ET: batch 9 DONE and VERIFIED by me (anchors land at 111 px on fresh loads, incl. inside folds and forwarded
  ids; margins "find a race" map/filters still work after margins.js was deleted, because its only job was the landing
  fix). Phone masthead 256→184 px. Sticky bar on 19 pages (≥9.5 screens; Nick can narrow it to the 6 over 12).
  NOTE for Nick: money/campaigns/county is now the longest page (32.9 screens); he said "Wait" on splitting it until
  the review; the review/plan did not split it → propose it in the morning summary. Running: batch 8 only.
- ~09:00 ET: batch 8 DONE (324 tests) but I sent it back (Part 2): the tax bill picked 023 for Mishawaka from the
  here.js DEFAULT school (part of Mishawaka is in PHM, district 022) = a guess. Fix: store explicit vs default
  choices; picks only from explicit values; audit other pages for default-based specific claims; calendar note where a
  filtered year is empty. Agent ab44df71ab1d3eeca running (usage-guard list). After it: final full check, Roadmap +
  handoff, morning summary. Batch 9 verified.

## Morning summary (2026-11-09, ~09:40 ET): overnight redesign COMPLETE, UNCOMMITTED
- Rollback point: commit 240a3e8 (not pushed; main is 1 ahead of origin). Everything after it is in the working tree
  (88 paths). `git diff 240a3e8` to review; `git reset --hard 240a3e8` + `git clean` (careful) to roll back.
- Final checks: build PASSED 113 pages; 327 tests OK; check_gov 0 errors; check_money OK. Only data change since
  240a3e8 = derived/unit_id_aliases.csv +school-new-prairie.
- All waves A-E verified by me (build, tests and browser spot checks per wave; see the entries above). Things I sent
  back and were fixed: Wax report dropped ($61.63 R total); Bolden-Simpson period-vs-YTD; all-filings JS-only;
  tax bill guessing from a default school.
- Decisions taken overnight (Nick can overrule): review Q1-Q10 per plan; B4 kept whole-county default (Nick); party
  control before budget; folded budget charts on place pages; county rail map link dropped; seat wording "all voters
  in the corporation; member must live in X" (verified: PHM Madison 11,269 votes vs 1,891 residents); 599→608
  uncontested (write-in total lines; 9 races from 2012 verified); sticky bar on 19 pages ≥9.5 screens.
- Waiting on Nick: commit/push of the redesign; split money/campaigns/county (32.9 screens, now the longest page);
  read IC 20-23-4 board plans; older races on today's district lines OK?; path 6 stop order; Copy-all vs shown on
  dataset pages; earlier open items (license, commit email, Acrobat PDFs, deploy) unchanged.
- Usage guard: stopped at ~09:40 after all work finished (never hit 90%).
