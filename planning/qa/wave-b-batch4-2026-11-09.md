# Wave B, batch 4: lists instead of stacks, 2026-11-09

Uncommitted. Spec: `site-ux-review-2026-11-09.md` section 4 (batch 4), section 3 (pages), P5/P3. Helpers: `entity_list`, `see_all_fold`, `see_all_table` (`wave-a-batch1-2026-11-09.md`).

## 1. What changed

| Page | Before | After |
|---|---|---|
| history/people | 32 cards in a 3-column grid | `entity_list`: one row per person (name, first office and years, party as text, rule(s) met, status badge). Each row opens to the full card. Words box plus filters "First documented service" (era) and "Holds office now"; no party filter. Order unchanged (first year, then name) |
| money/campaigns/other-committees | one table per committee (cycle blocks) | `entity_list` per section: name, candidate and party as written, reports and cycles, status mix. Row opens to the same cycle blocks and tables. All 4 sections kept |
| money/campaigns/all-filings | one 479-row table built by JS | JS builds one row per committee (440 of them, in office order, with the office/group headings): committee, who it backs, reports on file, latest cash figure, status mix. Row opens to that committee's reports. The full table is in a closed fold "See all N filings as one table" with Copy CSV; the filters drive both and the fold label updates |
| who-handles-this | 18-row, 5-column table | `entity_list` (service, responsible governments, accountable officials, status badge; words box). Row opens to the 4 fields with links. The full table is in a see-all fold |
| run/index | "Pick an office" table | 6 office cards (seats, term, next election, link). `#tbl-run-pick` is now the card list. It is the single home of the shared steps |
| run/<6 offices> | 3.4 to 5.7 screens, about 85% shared text | Keep: role, term, seats table, dates, office variants, eligibility and filing window, school board's party-label rule. Ballot access, finance, vacancies and contacts are one-line summaries with a link to `run/index.html#...`; the section ids stay |
| data/pull | 5 sources open, 64-row table | One fold per source (heading ids kept inside the summary); indicator table in a see-all fold |
| community/income-and-work | employer tables open | Each employer table in a see-all fold; rule, source and status stay visible |
| campaign area pages | no link back | City, town, township and county areas link to their place page (22 pages) |

## 2. Where every old piece went
- People cards: every field (photo and credit, offices, party, rules, summary, findings, sources, badges) is in the row's body. The card h3 became a `<p>` because the row's summary now carries the h3.
- other-committees: all tables, cycle lines and notes are inside the committee rows, with the same table ids.
- all-filings: every filing is in the fold's table (same `cf-table`, `cf-table-copy` ids). Per-committee tables hold the same reports without the committee column (it is the row heading). The cycle totals box and count line moved out of the fold (same ids).
- who-handles-this: all five columns of every row are in the row body and in the fold table. Gaps and sources are unchanged.
- run office pages: the dropped paragraphs exist verbatim on run/index (ballot access, finance, vacancies, contact card, party list). The ten or so `src-*` citation ids those pages no longer list are forwarded (see 3).
- data/pull, income-and-work: nothing removed, only wrapped in folds.

## 3. Anchor proof
Fixture: `tools/tests/fixtures/anchors_before_batch4.json` (all ids on the 13 pages before the batch). `test_wave_b_batch4.py::test_every_old_id_still_resolves_or_is_forwarded` passes:
- All ids on history/people (including the 32 `person-ppl-NNN`, now on the `<details>`), other-committees, all-filings, who-handles-this, data/pull and income-and-work are still present.
- run office pages: `src-ELX-007`, `src-GOV-027`, `src-IND-026/038/041`, `src-MON-020`, `src-SVC-007/017/018/019/020` exist on run/index. Each office page ships a `#moved-anchors` map and `moved.js` forwards an old link there (test checks the map).
- run/index: the only id gone is `tbl-run-pick-copy` (the old table's Copy button); `tbl-run-pick` now names the cards.

## 4. Screens (height / 800 px; 1280 / 400 wide), before to after
| Page | 1280 | 400 |
|---|---|---|
| history/people | 17.3 to 7.7 | 40.7 to 13.0 |
| other-committees | 21.8 to 4.5 | 25.0 to 6.5 |
| all-filings | 67.9 to 23.7 | 97.5 to 39.3 |
| who-handles-this | 5.5 to 2.9 | 8.4 to 5.1 |
| run/index | 5.3 to 5.4 | 7.9 to 8.6 |
| run/township-trustee | 5.7 to 3.6 | 8.0 to 4.5 |
| run/township-board | 5.7 to 3.6 | 8.1 to 4.5 |
| run/school-board | 5.5 to 3.5 | 8.0 to 4.7 |
| run/city-council | 5.2 to 3.0 | 7.5 to 3.9 |
| run/county-council | 5.3 to 3.2 | 7.7 to 4.2 |
| run/precinct-committeeperson | 3.4 to 2.3 | 5.0 to 3.2 |
| data/pull | 18.8 to 2.0 | 27.9 to 2.6 |
| community/income-and-work | 13.1 to 11.1 | 16.6 to 13.7 |

run/index grows slightly: cards replace a table, and the page now holds the steps once. all-filings stays long because there really are 440 committees for 479 filings; the list is one row each.

## 5. Checks
- `build.py --edition st-joseph --check`: PASSED (112 pages) at my last run. Earlier runs failed only on batch 2's mid-edit pages.
- `unittest`: my 12 new tests in `test_wave_b_batch4.py` pass. The full run has 3 failures in `test_page_organization` (margins/up-next filters) and 1 error in `test_wave_a_patterns` (results contest ids). All concern batch 2's pages, which were mid-edit; none touch my files.
- `check_gov.py`: 0 errors (23 warnings, not mine).
- Browser (Chrome, own tab): 10 changed pages x 3 looks x light/dark x 1280 and 400 = 120 loads. The look and theme applied each time and there was no horizontal overflow. Checked the all-filings filter (a cycle filter gave 80 reports from 79 committees, the fold label and rows followed, a row opens to its table) and a people row opened by `#person-ppl-001`. Not done: dark and Line map screenshots of each page by eye (only programmatic overflow checks); keyboard-tab pass beyond the native `<details>` behavior; JS-off check in a browser (rows ship open in the HTML and the filter bars are hidden until JS).

## 6. Questions and caveats
1. **entity_list quirk.** `status` given as `Markup` is a `str`, so the helper passes it to `status_badge()` and prints the escaped HTML. I worked around it by passing the status key (people show the status badge only; "in office" shows as "present" in the years). The fix is one `isinstance(st, Markup)` check in `components.py` (not mine).
2. **all-filings with JS off.** It was already JS-only (the noscript text points to the area pages). I kept that: the per-committee list is built in `campaigns.js`, since 479 filings server-rendered twice would double a 227 KB page. Say if you want a server-rendered fallback.
3. **Facts per row.** The people rows carry 3 facts (office and years, party, rule), not the review's 2 to 3 plus rule filter. A Rule filter was skipped because people can meet several rules and the filter matches one value; the words box matches rule names.
4. **Not done.** The "Which seat is mine?" links and the run-page P1 rail (they need the district maps and `related.py` from other batches); history/index (not in this batch's list).

## 7. Files
Changed: `tools/site/pages/community_history.py`, `pages/campaigns.py`, `pages/campaign_pages.py`, `pages/participate.py`, `pages/data_sets.py`, `static/js/campaigns.js`, `static/css/community.css`, `campaigns.css`, `participate.css`.
New: `tools/tests/test_wave_b_batch4.py`, `tools/tests/fixtures/anchors_before_batch4.json`, this report.
Local wrappers (instead of changing helpers): `pull_fold` in `data_sets.py`, `run_index_link` and `moved_to_run_index` in `participate.py`, `committee_cycles(as_items=True)` in `campaign_pages.py`.
`moved.js` is unchanged (batch 2 rewrote it; I use its `#moved-anchors` map).
