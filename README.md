# Indiana County Civic Guide — St. Joseph County edition

A source-cited web guide to local and state government in St. Joseph County, Indiana: the county, South Bend,
Mishawaka, the seven towns, the 13 townships and the school corporations. It covers who holds each office (with party
labels), how each body is chosen, election results and a precinct-level "How areas voted" map, budgets and tax rates,
state audits of local units, and local campaign finance. Every figure links to its source; gaps and conflicting
sources are listed rather than smoothed over. The generator is built to be reused for other Indiana counties.

**Author disclosure:** the author works as an organizer for the St. Joseph County Democratic Party. The guide is
independent work, made on the author's own time, and is not a party publication. It is written to published
neutrality rules (same rules for every party; see the About page's methods and neutrality sections).

## Build

Python 3 standard library only.

```
python -P -E tools/site/build.py --edition st-joseph --check     # writes site/st-joseph/, runs the checker
python -X utf8 -P -E tools/build_precinct_results.py --edition st-joseph   # precinct results + verification
python -P -E tools/build_map.py --edition st-joseph                # map shapes and vote data
```

The build must end with `PASSED` and print no `BUILD FAILED`. Serve `site/st-joseph/` with any static file server.

## Folders
- `data/editions/st-joseph/` — the edition's data (CSV; schema in `data/SCHEMA.md`); `data/indiana/` — statewide data.
- `tools/` — data builders and validators; `tools/site/` — the static site generator (pages, components, CSS/JS).
- `sources/` — text inputs the builders read (OpenElections precinct files, county report text, OCR output, boundaries,
  Census/Gateway extracts). Binary downloads (PDFs, ZIPs, images) and raw document text are not in the repository;
  every source's URL is in the `sources_*.csv` files.
- `research/` — research notes and campaign-finance transcriptions; `planning/` — plans, QA and fact-check reports.
- `Roadmap.md` — plan of record; `docs/session-handoff.md` — current state.

## Data notes
- 2026 general-election figures are unofficial until the county certifies them.
- Precinct results: OpenElections (MIT licence) for 2020 and 2024, the county's 2022 precinct report, and the county's
  scanned 2020 precinct report (OCR, verified box by box). Every race's county or district sum is checked against the
  official canvass; corrections to OpenElections are documented in `tools/build_precinct_results.py`.
- Local campaign finance: the county posts scanned filings for 2023 onward only.
