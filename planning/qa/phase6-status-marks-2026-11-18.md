# Phase 6: status marks, "About these figures" (2026-11-18)

Owner's request (2026-11-18): replace the inline "Incomplete…" caveats and status words beside heavily read figures with
an asterisk-style mark and one note at the bottom of the page. Design direction section 5, "Confidence without clutter".

## The system

- **Normal case, no mark.** An official, complete figure carries nothing (`status_badge("official")` returns empty).
- **Exceptions, one fixed symbol after the figure**, the same on every page, for every party, candidate and government
  (`civic/components.py FIGURE_MARKS`). Each symbol is a link to `#fnote-<kind>` (hyphens) on the same page, with the full
  meaning as `aria-label` and `title`, a word joiner before it so it never wraps away from its figure, and
  `white-space: nowrap`. Colors come only from look tokens (`--ink-2`; `--unofficial` for †), never party colors.

| Symbol | Kind | Note wording (exact) |
|---|---|---|
| * | incomplete | **Incomplete:** at least one expected report is not on file, so this total is a floor (the full amount may be higher). |
| † | unofficial | **Unofficial:** election-night or uncertified figures; they may change when the results are certified. |
| ‡ | secondary | **Secondary source:** from a news report or another reliable secondary source; no primary record has been found yet. |
| △ | single_source | **Single source:** only one news report or other secondary source gives this; not yet corroborated. |
| ‖ | computed | **Computed by the guide:** the guide's own arithmetic (a sum, share or conversion) from other sourced figures. |
| ¶ | from_scan | **From a scan:** transcribed from a scanned image of an official document. |
| ◊ | low | **Low confidence:** kept for completeness; not used in headings or charts. |
| ? | unverified | **Unverified:** recorded in the guide's configuration but not yet checked against a primary source. |
| ≈ | unreliable | **Unreliable estimate:** the margin of error is large compared with the estimate (CV above 30%, MOE ÷ 1.645 ÷ estimate), so treat it as unreliable; such estimates are shown in grey and never used in headings or charts. |
| ° | zero_moe | **No sampling error published:** the Census Bureau controls this total to its official population estimates (…), or the margin of error rounds to zero. |

Single source is △, not §, because the Ballot & Ink look numbers sections "§ 01".

- **Page-bottom note.** `shell.Page.render` scans the page's `<main>` for marks and section statuses and appends one
  `<aside id="figure-notes">` "About these figures" listing only those kinds, in the order above. Tab pages add "Where
  each figure comes from, and what every mark means: the Sources tab" (→ `sources/#marks`); other pages link to
  About `#badges`. No marks, no note. Static HTML: works with JavaScript off and prints.
- **Say it once.** `scope_attrs(kind)` on a section/chart/contest + one caption line (`scope_note`, `scope_mark`);
  `components.drop_scoped` (run in render) removes the marks of that kind inside it. Used by: every chart
  (`charts.figure`: the caption mark now speaks for the chart and its table, which removed ~1,000 repeated "computed"
  marks on government Money tabs with no change to money.py); every contest line (the line's mark covers its chart);
  election Contests tabs where all contests share a status (2026 general: one line "**Unofficial: every count on this
  tab.** …†" at the top, 150 marks → 1); office and person Elections tabs per year ("**Unofficial: every count for
  2026.**"; a year with only some unofficial contests gets "**Unofficial**†: the counts marked so are election-night…").
- **Unofficial keeps its word** at the top of its section: the scope lines above, `status_heading` beside results
  headings ("November 3, 2026 general election UNOFFICIAL†") and the elections hub row, and the edition banner (word
  badge, `status_label`).
- **Status columns keep words** (`status_label`, the old badge, unchanged), so Copy CSV text is unchanged there. Copy
  CSV writes any symbol in a cell as its word (`data-word`, `static/app.js tableCSV`). Data downloads untouched.
- Sources tab key (`tabs.marks_key`) and About `#badges` now list "No mark" plus every symbol.

## Inventory (built site, 3,484 pages)

Before = build of 2026-11-18 ~12:43 before any change; after = build with this change. Counts are elements in
`<main>`, legends excluded. b = word badge, m = old one-glyph mark, s = new symbol, w = the word in running text.

| Kind | Before | After |
|---|---|---|
| official | 5,309 badges + 3,767 marks | 0 marks; 1,071 words kept in Status columns |
| unofficial | 1,322 b + 1,332 m | 1,575 s + 180 b (Status columns) + 31 heading words; 2026 sections say it in words once |
| computed | 2,950 b + 623 m | 2,266 s + 292 b (Status columns) |
| secondary | 560 b + 241 m | 490 s + 229 b (Status columns) |
| single source | 37 b + 25 m | 55 s + 7 b |
| from scan | 426 b + 502 m | 580 s + 210 b |
| low | 63 b + 48 m | 61 s + 49 b |
| incomplete | 1,480 inline words/sentences | 718 s; 528 words left (explanations and the money map's labels, see below) |
| unreliable / ±0 (census) | 100 † + 25 ‡ (own legend, clashing symbols) | 90 ≈ + 15 ° (one system; the legend under 8 tables is one short line) |

By page type (before → after, inline status marks per type; full tables: scratch `inv_before.txt` / `inv_after.txt`):

| Page type | Before | After |
|---|---|---|
| elections/*/contests (42) | 330 unofficial + 36 secondary + 64 scan, each twice | 67 † + 15 ‡ + 32 ¶ (one per contest or one per tab) |
| offices/*/elections (122) | 506 † + 36 ‡ + 66 ¶ + 1,656 official | 337 † + 12 ‡ + 37 ¶, 0 official |
| people/*/elections (693) | 840 † + 62 ‡ + 162 ¶ + 2,836 official | 604 † + 25 ‡ + 86 ¶, 0 official |
| governments/*/money (40) | 1,346 computed + 199 official | 332 ‖ (chart captions say it once) |
| governments/*/overview (40) | 232 computed, 256 official, … | 140 ‖ + 92 Status-column words, 0 official marks |
| offices/*/money (86) | 112 "Incomplete: …" sentences | 56 * |
| people/*/money (244) | 232 "Incomplete: …" sentences | 116 * |
| money/campaigns + /* (38) | 1,127 "incomplete" words | 540 * + 525 words (explanations, map labels) |
| elections/* overview (52) | 1,028 official + 217 unofficial | 533 Status-column words + 117 † |

## Nothing lost (test)

`tools/tests/test_status_marks.py` (new; helper `tools/tests/status_marks_lib.py`; fixture
`tools/tests/fixtures/status_marks_before.json`, 43 pages, 1,563 (figure, status) pairs taken from the before build):

- every before pair is still on its page after: a mark of that kind in the same figure's row, or a section status that
  contains that row. All 43 pages: 0 lost (offices, governments, elections, people, state, community, money budgets and
  explainers, history, about, home; all ten kinds);
- on every built page: the symbols used = the note's entries, each symbol is its kind's, each link target exists and is
  a valid id, note wording exact, the note is the single last part of `<main>`; no marks → no note; forwarding pages
  have no note; the old one-glyph marks are gone;
- 2026: the Contests tab's word line is above the first contest and is the only † on the tab; an office's 2026 year
  section starts with "Unofficial: every count for 2026."; the banner keeps its word badge;
- helpers: official empty, one symbol per kind, accessible name/title/href, `link=False` span for `<summary>`, a figure
  with two statuses keeps both, nested scopes keep one caption mark, a different status is never dropped, CSS has no
  literal colors or party classes, Copy CSV writes the word.

Money campaign pages (another agent's, changing the same day) are not in the fixture; their per-kind counts were
compared instead: identical before and after (index: 109 incomplete, 2 computed; county: 83 computed, 61 incomplete,
25 scan).

## Files touched

Mine / unowned: `civic/components.py` (status_badge now the mark; added status_label, status_word, figure_mark,
status_symbol, status_heading, scope_mark, scope_attrs, scope_line, scope_note, figure_notes, drop_scoped, note_id,
mark_symbol, FIGURE_MARKS; entity_list summary uses the plain-span symbol), `civic/tabs.py` (status_mark delegates;
marks_key), `civic/shell.py` (note injection, space before a mark removed, unofficial detection, banner keeps its word),
`civic/charts.py` (chart caption scope; money_rows table cell joins markup instead of escaping it),
`pages/offices.py`, `pages/people.py`, `pages/election_pages.py`, `pages/elections.py`, `pages/elections_numbers.py`,
`pages/community_history.py`, `pages/state.py`, `pages/county.py`, `pages/places.py`, `pages/gov_parts.py`,
`pages/meta.py`, `static/css/fmarks.css` (new), `static/app.js` (Copy CSV).
Others' (after their reports): `pages/stubs.py` (legend keeps words), `pages/money_browser.py` (row labels: "2023*"
instead of "2023, incomplete"; "complete" dropped; its explainer retitled "How to read these reports", ids kept),
`pages/money_history.py`, `pages/campaign_pages.py` (race card total marked *, "Complete: …" sentence dropped, the
"Incomplete. The total covers only…" sentence → "Not on file*:" + the list).
Signatures of existing helpers unchanged.

## Tests changed (old badge words → new behaviour)

- `test_phase6_elections.py`: 2026 marks = `data-fmark/data-fscope="unofficial"`; contests tab has the word line and
  "Ahead:" (was "Ahead (unofficial count)"); banner-id skip rule accepts the new forms.
- `test_phase6_offices.py`: single-source mark is `data-fmark="single_source"`; banner test accepts the new forms.
- `test_wave_a_patterns.py`: an official entity row has no mark; an unofficial one has the symbol as a span, no link.
- `test_wave_b_fixups.py`: entity_list badge tests use an exception status (official is unmarked now).
- `test_wave_b_numbers.py`: margins lede carries `data-fmark="computed"`.

## Checks

- `python -P -E tools/site/build.py --edition st-joseph --check`: 3,484 pages, **PASSED** (final build ~13:53, all
  changes in). An earlier run failed with 579 problems: the note ids had underscores (`#fnote-from_scan`,
  `single_source`, `zero_moe`), which check.py rejects. Fixed at the root (`components.note_id`, hyphens), and the test
  now checks that every mark's target exists and is a valid id.
- Full suite `python -P -E -m unittest discover -s tools/tests`: **621 tests, OK** (1,250 s, final code).
  `test_status_marks.py` alone: 21 tests OK.
- `tools/check_gov.py`: errors=0, warnings=23 (the existing blank-start terms). `tools/check_money.py`: OK.
- `test_debug_pass` (non-ASCII in app.js): fixed. A literal word joiner had gone into app.js; it is now `⁠`.
- `test_phase6_offices` banner test: `elections/results/` got the 2026 banner only because its "how to read" legend
  printed an UNOFFICIAL badge. It shows no 2026 figure, so it no longer gets the banner. The test now checks the
  banner on the 2026 Contests tab and that it is gone from the finder.
- `test_wave_c_batch7` (`state/your-legislators/#banner-2026-unofficial`): passes. The id is still on the page because
  it shows unofficial 2026 county tallies.
- Browser (Playwright, localhost:8787, final build). Pages: office Money (mayor), government Money (South Bend),
  2026g Contests, person Money (James Mueller), Compare. Each at 1280 and 400 px × 3 looks × light/dark (60 views):
  - every mark's target exists;
  - no sideways scroll;
  - mark colors come from tokens (unofficial uses the amber token);
  - focus outline is solid 2px;
  - Enter on a mark scrolls smoothly to the note entry, which is highlighted;
  - with JavaScript off, the 2026 word line, the note and the marks are all there.
  - One defect found and fixed: chart-caption marks wrapped onto their own line at 400 px, because the caption is a
    flex row. The mark now sits inside the title span, and contest-line marks sit inside the result span.
- Screenshots in `planning/qa/phase6-shots/`, prefix `marks-`:
  - `marks-before-*-1280`: before the change, ballot look, light;
  - `marks-after-<page>-<width>-<look>-<theme>`;
  - `marks-after-focus-1280`, `marks-after-jump-to-note-1280`;
  - `marks-after-nojs-*`.
- Home page: the note has one "‖ Computed by the guide" entry, matching the page's 2 computed marks. This was checked
  after the home agent's follow-up build.

## Left as is / for others

- `civic/campaign_map.py` (money agent): map and bar labels in SVG/JSON keep "(incomplete)", ", incomplete" and the
  "Incomplete: N of N races…" box text (lines 179, 188, 204-205, 365, 413, 699, 710). An SVG label can't hold a link,
  so these need a design call (e.g. a `*` in the label plus the page note). Line 202's map box still says "Complete:
  every expected report is on file for every candidate" (a "Record" field in the map's JSON).
- Done in the money agent's files, as the coordinator asked:
  - `money/campaigns/` row labels: "2026*", "3 of 3 with reports*". The words "incomplete" and "complete" are gone.
  - The page's own explainer is retitled "How to read these reports", with the same ids. Only one "About these
    figures" is left.
  - Race cards: the total is marked *, and the "Complete: …" sentence is dropped.
- `pages/campaigns.py` 1012/1199 and `campaign_pages.py` 339/401/468/662, `money.py` 2162, `money_browser.py` 246:
  one explanation per section ("an incomplete total is a floor"); kept as the single short line per section.
- `civic/sitemap.py` (Learn): About section is still titled "Status and scope badges"; footer link "What the badges
  mean". Suggest "How figures are marked".
- `pages/elections.py` `_question_outcome`: "County voted yes (unofficial)" still says the word inside a scoped tab.

## Open questions for the owner

1. Symbols: * † ‡ △ ‖ ¶ ◊ ? ≈ °. Ten is a lot; most pages use one to three. Happy with them, or merge (e.g. low into ◊
   with unreliable)?
2. Status columns keep "OFFICIAL" words in tables. Keep, or blank official there too?
3. "Computed" is still marked on every computed figure outside charts (‖). It is the most frequent mark; it could be
   said once per tab instead.
