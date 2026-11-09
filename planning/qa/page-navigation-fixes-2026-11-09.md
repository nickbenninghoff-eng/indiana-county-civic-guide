# Page navigation fixes, 2026-11-09 (items 5 to 9)

Nothing committed. Build `--check` fails ONLY on links into pages owned by another agent (see "Open items").

## What changed

### Item 5: /data/ split
- 13 dataset pages, one per dataset: `data/<slug>/index.html` (results, elections, terms, offices, units, budgets, tax-rates, debt, cf-state, cf-local, cf-large, indicators, people). Each has the preview (first 50 rows), the "what is left out" note, the status mix, Copy CSV (the existing `meta.js` button, embedded JSON CSV, unchanged) and its own collapsed Sources list.
- Why per dataset, not per group: each page then carries exactly one CSV blob (results alone is 821 KB), the URLs are guessable, and the index can show one card per dataset.
- `/data/` is now an index: how to use, 5 groups of dataset cards (what it is, rows, columns, file, link, source count), a pointer to the pull page, Gaps (collapsed) and "Where the data comes from" (links to each dataset's Sources). The "Where the data comes from" 72-screen list is gone from the index; every dataset page lists its own sources, collapsed, with a count. Sources index for everything is `about/sources/`.
- "How to pull it yourself" moved to `data/pull/index.html`.
- There are no real file downloads (the site rule is no downloads), so "download" = Copy CSV on the dataset page.
- Anchors: `#ds-<name>` and `#ds-<name>-h`, `#datasets`, `#pull`, `#gaps`, `#sources` stay on the index (the cards link onward). Everything else moved (`ds-*-preview/-csv/-copy`, `indicator-defs`, `pull-*`, 819 `src-*`). `/data/` ships a `#moved-anchors` JSON map and new `static/js/moved.js` forwards an old link to the new page. With JS off such a link lands at the top of the index (the index has the cards).
- New: `pages/data_sets.py`, `civic/sitemap.py` (`DATA_PAGES` plus entries), `pages/meta.py` (`build_data` rewritten).

### Item 6: /about/ sources
- Sources index moved to `about/sources/index.html`: full list in the HTML, 6 kind groups as `<details>` (open without JS, collapsed by script), a search box plus kind filter (hidden until the script runs), "N of M sources shown", Reset, empty-state message, groups with matches open while filtering and return to their prior state after. A link to an entry the filter hid clears the filter.
- About keeps `#sources` as a short pointer section with links to each kind group (`sources/index.html#sources-<kind>`).
- Citations on About: shared `Citations` got an optional `href_base`; About sets it, so every citation goes to `sources/index.html#src-ID`. Footer "Sources index" link and Data page links updated.
- Old `about/#src-*` and `#sources-<kind>` forward to the new page (`moved.js`).
- New `static/js/sourcesearch.js`; `pages/meta.py` (`_source_index`, `build_sources_index`).

### Items 7 and 8: filters
- New shared `table_filter()` and `filter_empty_note()` in `civic/components.py`; `data_table` got an optional `row_attrs` argument (additive). New `static/js/tablefilter.js` and `static/css/tablefilter.css`: one labelled row of selects plus a words box, Reset, "N of M shown" (aria-live), empty message. The bar is `hidden` in the HTML and shown by script; rows are only hidden, never rendered by script.
- Landscape "Margins in every race": the old year/election/band/sort controls now use this helper (old `margins()` removed from `elections.js`) and gained Office (office group), Place and District (parsed from the contest name) plus a words box.
- "Up next": Year, Level, Government, words (seat or holder). "Current officeholders": Level, Government, "First took office by", words.
- Calendar "Every seat, by year": Year, Level, Government, words.
- The word box matches a `data-tf-text` field (contest or seat name, holder name), with the "(Democratic primary)" tail removed, because the page promises no party filter. Test covers it.
- Bug fixed on the way: the officeholders data table and the chart's table view shared the id `took-office-table`; the data table is now `took-office-list` (the chart keeps the old id, so the old anchor still resolves).

### Item 9: collapsed Gaps and Sources
- `fold_section()` in `civic/components.py`, used by `gaps_section` and `Citations.render`, so all pages that call `page.finish()` get it with no page edits (campaigns pages untouched). Summary shows the h2 with the count: "Sources on this page (24)", "Gaps on this page (3)".
- The HTML ships `<details open>`; `static/js/folds.js` closes them on load, so with JS off everything is visible and every citation works (better than a closed `<details>` with JS off). It reopens a fold on a click on a link into it (footnote, TOC `#sources`), on load with a hash, on hashchange, and on print.
- New `static/js/folds.js`, `static/css/sections_fold.css`.

## Screens (height / 800 at 1280 wide)

| Page | Before | After |
|---|---|---|
| /data/ | 159 | 5.7 (400 px: 9.1) |
| /data/results/ | n/a | 5.8 |
| /data/cf-local/ | n/a | 8.1 |
| /data/pull/ | (17.6 inside /data/) | 18.9 |
| /about/ | 98.6 | 11.9 (400 px: 19.9) |
| /about/sources/ | n/a | 2.3 collapsed (400 px: 3.4); 983 entries |
| /elections/landscape/ | 78.7 | 69.4 (tables are still long when unfiltered; the filters narrow them) |
| /elections/calendar/ | 29.7 | 21.3 |
| /county/ (sample of the Gaps/Sources change) | 31 | 23.9 |

## Anchor-preservation proof
Baseline: every `id` in the built site before any edit (9,069 ids, 60 pages; `scratchpad/baseline.json`). After: 9,588 ids in 75 pages. Pages not touched keep all ids. For the four edited pages:
- data: 865 ids left the page; 865 are forwarded by the map and exist on the target page (0 unresolved). The index keeps `ds-*`, `ds-*-h`, `datasets`, `pull`, `gaps`, `sources` itself.
- about: 1,061 ids left (`src-*`, `sources-<kind>` and their headings); 1,061 exist on `about/sources/` and are forwarded (0 unresolved). `#sources`, `#sources-h`, `#gaps` stay.
- calendar: no ids lost.
- landscape: only five controls lost, `mg-year/type/band/sort/count`, replaced by `tf-margins-table-*` (form controls, not link targets).
- Learning-path stops (`data/index.html#sources`, `about#sources`, landscape sections) still resolve (test).
Repeatable as `test_every_old_anchor_still_resolves`, fixture `tools/tests/fixtures/anchors_before_page_split.json`.

## Tests and checks
- `tools/tests/test_page_organization.py` (20 tests): old anchors, path stops, dataset page per slug with Copy CSV and row counts, index size and cards, sources page full list and search markup, About citations landing on the sources page, fold markup and count, citation hrefs resolving inside folds, filter markup versus row attributes for margins, up-next, officeholders and calendar, no party text in search fields, no duplicate ids.
- `unittest discover`: 87 tests OK. `check_gov.py`: 0 errors (23 warnings, existing).
- `build.py --check`: see open items.

## Browser checks (Playwright; 1280 and 400; ballot, line, wayfinding x light, dark)
- No console errors or page errors; no horizontal overflow on landscape, sources, data index, calendar in any of the 12 combinations. Screenshots `.playwright-mcp/fix-*.png`.
- Filters: margins 353; Office=City offices 78; Place=Mishawaka 27; District 3 -> 3; nonsense word shows the empty message; Reset restores 353; sort Newest first puts 2026-11-03 first. Up-next 71 -> 22 (Cities). Officeholders 163 rows (Townships filter works). Calendar 188 -> 32 (2027) -> 18 (2027 Cities).
- Sources search: "canvass" -> 1 of 983; only the matching group opens; empty message; Reset restores all and re-collapses; `#src-RES-001` opens its group.
- Folds: collapsed on load; `#gaps` opens Gaps; citation click and direct `#src-...` open Sources; TOC "Sources" click opens it.
- Redirects: `/data/#ds-cf-state-preview` -> `data/cf-state/`; `/data/#src-RES-001` -> `data/results/`; `/about/#src-RES-001` -> `about/sources/`; `/data/#ds-cf-state` stays.
- Copy CSV on /data/cf-state/ reports "Copied 100 rows."
- JS off: both folds open, 188 calendar rows visible, filter bar hidden, 983 source entries visible.

## Open items and questions for the owner
1. Build `--check` currently reports two broken links that come from `pages/campaigns.py` (another agent's work): `about/index.html -> ../money/campaigns/index.html#method` and `money/campaigns/all-filings/index.html -> ../index.html#areas` (campaigns builder import was failing mid-edit). Not mine; re-run when that work settles. Everything else passes, tests included.
2. Copy CSV on a filtered table still copies every row (app.js builds it; not changed). Wanted: copy only shown rows?
3. Landscape is still 69 screens unfiltered (352-row table). Page-through ("show 25 more") or splitting into Turnout / Margins / Incumbents pages was not part of this approval.
4. Timing screenshot flash: with JS on the folds are open for a moment before the script closes them (script runs deferred at end of body; content is below the fold on most pages).
5. A one-time scroll check: after clicking a citation, `:target` was positioned by the browser; I verified it opened and targeted, not the pixel offset under the sticky header.

## Files
New: `tools/site/pages/data_sets.py`, `tools/site/static/js/{folds,tablefilter,sourcesearch,moved}.js`, `tools/site/static/css/{sections_fold,tablefilter}.css`, `tools/tests/test_page_organization.py`, `tools/tests/fixtures/anchors_before_page_split.json`.
Changed: `tools/site/civic/components.py`, `tools/site/civic/sitemap.py`, `tools/site/civic/shell.py` (footer link), `tools/site/pages/meta.py`, `tools/site/pages/elections.py`, `tools/site/static/js/elections.js`.
