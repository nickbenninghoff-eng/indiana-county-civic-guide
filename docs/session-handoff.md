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
- License for the public repo (suggested: MIT for code, CC BY 4.0 for data/text) — none added yet.
- Whether to keep the Gmail address on commits or switch git to the GitHub noreply address.
- Close Adobe Acrobat, then the 21 leftover PDFs in Downloads can go to the Recycle Bin (all have copies in `sources/`).
- Optional: research the 2013 Roseland clerk theft case for the town's history.
- Public hosting of the site: only on Nick's explicit deploy trigger.

## Next step
Session ended 2026-11-08 for a computer restart, with everything committed and pushed (`main` = `origin/main`;
working tree clean before this handoff edit). Nothing was mid-stride: no agents running, no pending downloads.
On resume: read Roadmap.md Phase 5, rebuild the site, restart the preview (command above), then take Nick's answers
on the items above or continue with Phase 5's open optional items.
