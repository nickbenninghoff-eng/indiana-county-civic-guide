# Phase 6 step 5: Money (2026-11-18)

Scope: row 5 of section 7 of `planning/design-direction-2026-11-16.md` (section 0 governs): the Money hub, the campaign
money browser, short campaign area pages, Compare budgets, forwards, full-width budget charts, search entries and
link fixes. Nothing under `data/` was edited and no data builder was run. Nothing was committed, pushed or deployed.

## 1. What was built

- **Money hub** (`money/index.html`, `pages/money.py build_hub`). Two doors side by side (one column at 400px):
  - **Government money** (`#government`): one line, then four entry points (Compare budgets, Your tax bill, each
    government's Money tab, What counts as a budget), then a preview: the top 5 by all advertised funds per resident.
  - **Campaign money** (`#campaign`): one line, then four entry points (By office, By election, By candidate, How
    campaign reporting works), then a preview: the five offices with the most reported spending.
  - Below the doors, the headline figures (`#facts`) as one compact list with status marks.
  - 1,947px to the footer at 1280px, about 2.2 screens.
- **Campaign money browser** (`pages/money_browser.py`, new). Six views share one tab bar (the `civic/tabs.py`
  markup):
  - **By office** (`money/campaigns/`):
    - The 10 offices with the most reported spending (`#most`, `money_rows` on one scale).
    - Every office by government, in a filter box (`#offices`).
    - The state legislature as a link grid.
    - "About these figures" (`#about`, `#obligations`, `#public`, `#method`).
  - **By election** (`by-election/`): the 2026, 2024 and 2023 cycles (`#c-2026`, `#c-2024`, `#c-2023`). Each shows its
    top 6 races, with the rest folded on the same scale. Earlier elections (`#earlier`) link to the office tabs'
    news-reported years; nothing there is added up.
  - **By candidate** (`by-candidate/`): 227 candidate entries as alphabetical letter folds. Nobody is ranked by money.
  - **By place** (`by-place/`): the campaigns map and the area list that used to be the index's `#map` and `#areas`,
    unchanged except that the list is folded.
  - **Committees** (`other-committees/`) and **Every filing** (`all-filings/`): content kept; the header is replaced by
    the shared browser header.
  - **The test case:** Money hub → Campaign money → By office → the first row, "Mayor of South Bend", links to
    `offices/south-bend-mayor/money/`.
    - That row's subtitle reads "2023, incomplete · also 2019, 2015, 2011, 2007 (news) · primary and general".
    - The office tab's own Primary / General switch takes it from there.
    - Clicking through in the browser, then choosing Primary, gives the state line "Showing: Primary · All parties".
    - See the deviation in section 9.
- **Area pages** (`money/campaigns/<area>/`, 30 pages, `campaign_pages.build_area`). Each page now opens on:
  - a head with its facts (totals, the latest election, links to the government page);
  - the same "Spent by all candidates" summary as before;
  - `#offices`: one ranked `money_rows` chart per election, each race linking to its office's Money tab at `#y<year>`
    (only when that tab has the year).
  - All the old detail follows in folds on the same page, with every id kept:
    - the district map
    - the per-election race cards (`#e-<eid>`)
    - the like-for-like comparison
    - other reports
    - large contributions
  - At 1280px: South Bend 1,970px (was 11,045), County 2,836px (was 34,893).
- **Compare budgets** (`money/budgets/`, replacing the long budgets page):
  - The money map (`#money-map`). Areas now open the government's Money tab.
  - Per resident (`#per-resident`):
    - all advertised funds (`#perres-af`)
    - general fund (`#perres-gf`)
    - assessed value (`#perres-av`)
  - Certified tax rates (`#rates`).
  - Debt (`#debt`, with the full debt-class table folded).
  - The tax-base section, folded (`#tax-base`, a learning-path stop).
  - Every government with its latest adopted total, folded (`#over-time`, a learning-path stop).
  - Every ranked list shows its top 10 and folds the rest on the same scale, and every row links to that government's
    Money tab.
  - Units sampled across types:
    - county: St. Joseph County
    - cities: South Bend, Mishawaka
    - towns: Walkerton, North Liberty, New Carlisle
    - townships: Penn, Centre, Olive and others
    - schools: SBCSC, PHM, John Glenn and others
    - special: the Airport Authority, the Redevelopment Authority, the Public Library
  - 4,126px to the footer at 1280px (was 13,661), about 4.6 screens.
- **Budget charts on government Money tabs:** `money.flag_columns` is now drawn as HTML columns (`.fcol*` in
  `static/css/money.css`, tokens only) instead of a fixed-viewBox SVG, so it fills the column.
  - Same function signature, same figure ids, table view kept.
  - Each column can be focused and has the shared tooltip.
  - The flag marks and the "reporting changed" breaks are kept.
  - Checked on South Bend (city), Penn Township and SBCSC (school corporation) at 1280px and 400px. The South Bend
    general-fund chart is 1,148px wide at 1280px.
- **Search** (`civic/search.py`, additive):
  - `PAGE_KEYWORDS` for the money pages.
  - `PAGE_ALIASES`, which add extra Page items:
    - "Campaign finance" and "Campaign money by office" → `money/campaigns/`
    - "Budgets" and "Budgets compared" → `money/budgets/`
    - "Property tax bill" → `money/your-tax-bill/`
  - "campaign money", "compare budgets" and "tax bill" match the page titles directly.
- **Other money pages:** their links now point at the new homes (primer, how-it-works, all-filings, other-committees).
  The URLs of `money/what-is-a-budget/` and `money/campaigns/how-it-works/` are unchanged.

## 2. URL map, old → new

No URL was retired: every old money URL is still built and serves content. **No Netlify 301s were needed, so none were
added.**

| Old URL | Now |
|---|---|
| `money/` | Money hub (two doors) |
| `money/budgets/` | Compare budgets (same URL) |
| `money/campaigns/` | Campaign money: By office (same URL) |
| `money/campaigns/<area>/` (30) | short area page (same URL) |
| `money/campaigns/other-committees/`, `all-filings/`, `state-legislature/`, `how-it-works/` | same URL |
| (new) | `money/campaigns/by-election/`, `by-candidate/`, `by-place/` |

Anchors that moved are forwarded by `#moved-anchors` (static/js/moved.js):

| Old anchor | New target |
|---|---|
| `money/budgets/#<unit>` and `#<money-id>` | `governments/<gid>/money/#budget` (`#tabs` when the unit has no budget series) |
| `money/budgets/#bud-<mid>-*`, `#brk-<mid>-*`, `#obrk-<mid>-*`, `#other-<mid>*`, `#sp-<unit>-*`, `#money-<unit>`, `#av-2026-<mid>` | the same id on the government's Money tab |
| `money/budgets/#breakdown-<unit>` | `…/money/#breakdowns` (only units with a 2024 breakdown) |
| `money/budgets/#flows-<unit>` | `…/money/#money-in-out` (only units with money in and out) |
| `money/budgets/` old section ids | `#over-time`, `#money-map-tables`, `#tax-base`, `#debt`, … |
| `money/budgets/#src-*` | `about/sources/` |
| `money/campaigns/#map`, `#areas`, `#cf-back`, `#cf-filter-h`, `#cf-list-*`, `#cf-*` area ids | `money/campaigns/by-place/` |
| `money/#pages-h` | `money/#pages` |

Checked live: `money/budgets/#south-bend` → `governments/south-bend/money/#budget`; `money/campaigns/#map` →
`by-place/#map`; `money/budgets/#obrk-city-mishawaka-2026` → `governments/mishawaka/money/#obrk-city-mishawaka-2026`.

Fixture `tools/tests/fixtures/anchors_before_phase6_money.json` holds every id of the old pages, taken from the build
before this step:
- budgets: 736 ids
- campaigns index: 75 ids
- hub: 42 ids
- every area page, other-committees, all-filings and state-legislature

`test_every_old_anchor_resolves` follows each id exactly as moved.js does (`tests/gov_moved.py`). Result: 0 lost.

## 3. Content moves

1. **Per-unit budget blocks** (old `money/budgets/#<unit>`: charts `bud-*`, the "other reported figures" tables
   `other-*`, AFR breakdowns `brk-*`, spending `sp-*`, money in and out `money-*`). These were already rendered on the
   government Money tabs by the same functions, so the copies on the budgets page were dropped and the ids forwarded.
2. **Other breakdowns** (`obrk-*`: Mishawaka 2026 ×3, the South Bend 2024 proposed budget, South Bend 2025 abc57) existed
   **only** on the old budgets page. They are now on the government Money tab in a new folded section,
   `#other-breakdowns`:
   - `money.other_breakdown_parts`
   - `gov_parts.other_breakdowns_section`
3. **Library and special-unit money in and out**: these were already on their government pages; forwarded.
4. **The campaigns map and area list** (old `money/campaigns/#map`, `#areas`) moved to `money/campaigns/by-place/`,
   unchanged.
5. **Area page detail** (race cards, district map, comparison, other reports, large contributions) stays on the same
   page, inside folds below the new offices chart.
6. **The money map's "no boundary" chips** on the old budgets page were dropped. The folded "every government" list
   (`#over-time`) names every unit, including the ones the map cannot draw (county, libraries, special units), and links
   each one to its Money tab.
7. **The debt-class table** stays on Compare budgets in a "Show the table" fold. The per-unit debt is also on each
   Money tab.
8. **The certified-rate table**: the latest year is ranked on Compare budgets. The full history of each unit's rates is
   on its Money tab (`#tax-base`).

## 4. Figure spot-checks (all asserted in `tools/tests/test_phase6_money.py`)

| Figure | Old page | New page(s) |
|---|---|---|
| Mayor of South Bend 2023, spent / raised | $610,625.36 / $393,342.90 | the same on the hub preview, By office row 1, the South Bend area page and the office Money tab |
| South Bend area, latest election | $830,504.38 / $623,352.65 | same |
| County area | $1,421,980.97 / $1,678,684.47 | same |
| Mishawaka area | $318,283.08 / $391,438.17 | same |
| PHM area | $3,393.00 / $0.00 | same |
| Penn Township area | $34,605.33 / $36,325.84 | same |
| South Bend 2027 adopted, all funds | $439,062,691 | same on the government Money tab (test_phase6_governments) |
| Every race on By election | race model total | `cm.usd(race.spent)` is present for every race (`test_every_race_is_on_by_election_with_its_own_total`) |

Bars are the race model's own sums (`campaigns.cf_all`). Nothing new is added up, and news-reported figures are only
linked. Money bars use no party classes (tested).

## 5. Size, before → after (1280×900, footer offset; byte size)

The "before" heights are the snapshot pages served with today's stylesheet.

| Page | Before px | After px | Screens after | Before bytes | After bytes |
|---|---|---|---|---|---|
| money/ (hub) | 1,531 | 1,947 | 2.2 | 51,014 | 65,091 |
| money/budgets/ | 13,661 | 4,126 | 4.6 | 1,840,521 | 419,013 |
| money/campaigns/ | 5,312 | 3,436 | 3.8 | 227,637 | 179,255 |
| money/campaigns/by-election/ | (new) | 3,312 | 3.7 | | 162,737 |
| money/campaigns/by-candidate/ | (new) | 1,387 | 1.5 | | 155,704 |
| money/campaigns/by-place/ | (new) | 1,934 | 2.1 | | 223,972 |
| money/campaigns/county/ | 34,893 | 2,836 | 3.2 | 1,224,397 | 1,277,172 |
| money/campaigns/south-bend/ | 11,045 | 1,970 | 2.2 | 376,120 | 399,087 |
| governments/south-bend/money/ | 3,777 | 3,957 | 4.4 | 195,363 | 199,939 |
| governments/penn-township/money/ | | 1,911 | 2.1 | | |
| governments/sbcsc/money/ | | 2,331 | 2.6 | | |

About the byte sizes:
- The area pages keep every race card, so their bytes are about the same; only what shows before expanding changed.
- other-committees (3,985px) and all-filings (18,759px) are existing content pages, kept as they were. all-filings is
  one long filterable table and was long before this step too.

## 6. Shared-file additions (smallest additive edits)

- `civic/shell.py`: one line after the margins line removes `money/budgets/` and four area pages (county, mishawaka,
  south-bend, sbcsc) from `ONPAGE_PAGES`, because they are short now.
- `civic/sitemap.py`:
  - The Money nav link "Budgets" is now "Compare budgets".
  - The `money/budgets` and `money/campaigns` entries have new titles and descriptions ("Compare budgets", "Campaign
    money"), so the breadcrumb is now "Money › Campaign money".
  - Top-level nav items are unchanged.
- `civic/search.py`: `PAGE_KEYWORDS` and `PAGE_ALIASES` for the money pages; the T_PAGE line passes the keywords.
- `civic/campaign_money.py` (`campaign_entries`): three entries (by-election, by-candidate, by-place).
- `civic/money_map.py`: the non-county map target is now the government Money tab (it was `money/budgets/#anchor`).
- `pages/gov_parts.py`: `other_breakdowns_section`, added to the Money tab after `breakdown_section`.
- Not touched:
  - `charts.py`, `tabs.py`, `moved.js`: no changes, only used.
  - `_redirects`: unchanged, since no URL was retired.
  - CSP: unchanged.
- New files:
  - `pages/money_browser.py`
  - `static/css/money_browser.css`
  - `tools/tests/test_phase6_money.py`
  - `tools/tests/fixtures/anchors_before_phase6_money.json`
- README: a "Money (phase 6 step 5)" section was added to `tools/site/README.md`.
- Older tests updated for the moved content, each with a dated comment:
  - `test_county_campaign_map` (the map is now on By place; the area map is in a fold)
  - `test_here_money_results` (the area list is on By place)
  - `test_wave_c_batch7` and `test_map_navigation` (budget chips and show-one items are gone; old ids must land on the
    government Money tab; government pages and about/sources are built for the anchor check)
  - `test_phase6_governments` (the South Bend tables are forwarded, not duplicated)
  - `test_wave_d_nav` (crumb "Campaign money")

## 7. Checks

- `python -P -E tools/site/build.py --edition st-joseph --check` (final run, 3,484 pages): **FAILED, 579 problems**.
  - **Every one of them** is a hash `#fnote-from_scan` (510), `#fnote-single_source` (54) or `#fnote-zero_moe` (15).
  - Those come from the figure-mark notes in `civic/components.py`, which another agent is changing during this session
    (the file was modified at 13:04). The new mark kinds use underscores, which the checker's fragment rule rejects.
  - Excluding those, there are **0 problems**. There are 0 problems from the money pages' own links, ids, colours or CSS.
  - An earlier run (before that change) also failed, but only on 104 `#show=primary`/`#show=general` links of mine
    plus `#y<year>` links to years an office tab doesn't have. Both are fixed (section 9).
  - A run in between showed 69 people/* pages empty mid-write (another build running at the same time).
- `python -P -E tools/check_money.py`: **OK** ("all rows parse; no series mixes bases; amounts numeric; every row has
  status and source_ids").
- `python -P -E tools/check_gov.py`: **errors=0**, warnings=23 (unchanged: blank term starts and similar).
- `tools/tests/test_phase6_money.py`: **19 tests OK**.
- The tests I updated pass:
  - test_county_campaign_map (12)
  - test_here_money_results (2)
  - test_map_navigation (21)
  - test_phase6_governments (14)
  - test_wave_d_nav (21)
  - test_money_history (21)
  - test_wave_b_batch4 (12)
  - test_wave_e_onpage, test_css_duplicates, test_security_escaping: OK
- Full suite (`unittest discover -s tools/tests`): **590 tests, 7 failures**. None comes from the money work except
  one, which is now fixed:
  - `test_phase6_offices.test_every_page_within_two_clicks`: `money/campaigns/state-legislature/` had lost its link from
    the old campaigns index. **Fixed:** By office's state-legislature block now links it. Re-run: passes.
  - The other agents' in-progress figure-mark and badge work:
    - `test_debug_pass.StaticJsIsAscii` (app.js:179 is not ASCII)
    - `test_phase6_elections.test_2026_unofficial_marked`
    - `test_phase6_offices.test_unofficial_banner_only_with_2026_unofficial_figures`
    - `test_phase6_offices.test_rounded_news_figures_keep_their_words` (passed on re-run)
    - `test_wave_a_patterns.EntityList.test_summary_line` (`badge-official`)
    - `test_wave_b_numbers.test_counts_add_up_and_open_with_uncontested` (`badge-computed` vs the new `fmark`)
  - `test_wave_c_batch7.test_every_old_anchor_lands`: the only id still lost is
    `state/your-legislators/#banner-2026-unofficial`, from the same unofficial-banner change. Not a money id.

## 8. Browser matrix (Playwright MCP, http://localhost:8787)

- Pages checked:
  - hub, By office, By election, By candidate, By place, Committees, Every filing
  - area pages: county, south-bend, lakeville (no races)
  - Compare budgets
  - government Money tabs: South Bend, Penn Township, SBCSC
- Each page was loaded at 1280 and 400 in all 3 looks × light and dark (168 page loads):
  - no horizontal page scroll anywhere
  - `data-look` applied
  - **0 console errors, 0 page errors**
- Keyboard: Tab order from the header reaches the view tabs (By office, By election, …), then the Mayor of South Bend
  row link. Bar columns on Money tabs can be focused and show the tooltip.
- With JavaScript off, all folds ship open (every figure is on the page), and there is no horizontal scroll.
- Old anchors forwarded live (section 2). The test-case click path works, including the Primary switch on the office
  tab.
- Screenshots in `planning/qa/phase6-shots/money-*.png`:
  - each new page type at 1280 ballot light (full page), 400 wayfinding light and 1280 line dark
  - Compare budgets at 1280 ballot light and 1280 wayfinding dark (full page)
  - the South Bend budget chart at 400 line dark
  - By office at 400 line dark
  - the South Bend Money tab with JS off

## 9. Deviations, failing or undone

- **The Primary / General deep links were dropped.**
  - The plan was to give each By office row "Primary · General" links to `…/money/#show=primary`.
  - The site checker forbids fragments that are not letters, digits or hyphens, and treats `show=primary` as a missing
    id (`build --check` failed on 104 such links).
  - The fix: the row says "primary and general" and links to the office's Money tab, where the switch sits at the top.
  - Changing the checker to allow the `show=`/`party=` hash state is a shared-tool decision, so it was left for Nick.
    If allowed, the links can come back with a two-line change in `money_browser._office_money_row`.
- **Compare budgets is about 4.6 screens before the footer** (the target is about 4). The money map (1,175px) and the
  per-resident pair take most of it. Folding the map's figure would bring it under 4, but would hide the page's first
  chart.
- `test_wave_c_batch7.test_every_old_anchor_lands` reports `state/your-legislators/#banner-2026-unofficial` as lost.
  That banner id was removed by other work (no 2026-unofficial banner is built any more). It is not a money page; it was
  left for its owner.
- `#over-time` (a learning-path stop) now lands on the section heading with its list folded. The summary line "Show all
  40 governments…" is right under it.

## 10. Open questions

1. Should the checker accept the office tab's `#show=primary` / `#show=general` hash state? If yes, the browser rows get
   direct Primary / General links again.
2. Is 4.6 screens acceptable for Compare budgets, or should the money map start folded?
3. The area pages are short to read but still heavy in bytes (County 1.28MB), because every race card is kept in a fold.
   Should the large-contribution lists move to the office or person pages in a later step?

## 11. Follow-up (2026-11-18): Money-tab state links

This answers open question 1, decided by the main session.

- **Checker** (`tools/site/check.py`): a narrow exception for the office Money tab's switch state, added via
  `MT_STATE_KEY`, `MT_SHOW` and `money_tab_state_problems`.
  - Only a fragment shaped like `key=` takes this path. It is accepted only when all of these hold:
    - its grammar is exactly what `offices.js parseHash` handles: `show=primary|general|both`, optionally followed by
      `&party=<code>`, in that order, with no repeated keys;
    - the target page ships the switch: `id="mt-ctl"`, a `data-mt-show` button for that view, and `assets/app.js`,
      which bundles offices.js;
    - the party code is one of the options in that page's `#mt-party`.
  - Everything else still fails:
    - any other key, order or value (for example `show=runoff`, `party=D&show=primary`, `show=primary&year=2023`)
    - a party the page does not offer
    - a `#show=` link to a page without the switch
    - all other fragments, which keep the letters/digits/hyphens rule
  - Tests are in `tools/tests/test_check_state_fragments.py` (6 tests, OK):
    - the pure function, in accept and reject cases
    - the checker run end to end on a two-page temporary site, for a valid state, an invalid view, an invalid party, an
      unknown key, a page without the switch, and an underscore id under the old rule
- **Direct links** (`pages/money_browser.py`): `view_links` adds "Primary · General" to each office row on By office.
  - Each link is `…/money/#show=primary` (or `#show=general`) and has an aria-label that names the office.
  - A link is offered only where that view shows something on the tab. `office_rows` now has `primary` and `general`
    flags:
    - both are set when any race's filings can be cut at the pre-primary report (`race_split.any`);
    - `primary` is also set when the news reported a party primary;
    - `general` is also set when the news reported a general election.
  - Offices with neither get no links.
  - `test_view_links_only_where_the_view_shows_something` checks this against every built office Money tab. For each
    office, the views offered must equal the set of `data-mt-phase="primary|general"` elements on its tab.
- **Mayor of South Bend.**
  - 2023 cannot be split: the county posted no 2023 pre-primary reports.
  - The Primary view shows the news-reported primaries:
    - Democratic: 2019, 2015 and 2011 (`mt-2019p-…-d`, `mt-2015p-…-d`, `mt-2011p-…-d`)
    - Republican: 2007 (`mt-2007p-…-r`)
  - The state line reads "Showing: Primary · All parties. 1 election is hidden: 2023 (whole-cycle figures only: the
    county posted no 2023 pre-primary reports)".
  - The link applies no party filter (same rule for every party). The Democratic primaries are most of what the view
    shows, but the 2007 Republican primary is shown too.
- **Browser** (Playwright):
  - Hub → By office → the "Primary" link on the Mayor of South Bend row is one click from By office. It lands on the
    Primary state with the Primary button pressed and the four primary charts visible.
  - Checked at 1280px and 400px; no horizontal scroll at 400px; 0 console errors.
  - Keyboard: Tab from the top of By office reaches "Mayor of South Bend", then the incomplete mark, then "Primary";
    Enter lands on the same state.
  - JS off: `#show=primary` opens the tab with all 7 money charts visible, none hidden.
  - Screenshots: `money-byoffice-views-400.png`, `money-mayor-primary-400.png`.
- **Checks after the follow-up:**
  - `build --check`: **PASSED** (3,484 pages, 0 problems; the `#fnote-*` problems are gone too, so none are excluded).
  - `test_phase6_money.py`: 20 tests OK.
  - `test_check_state_fragments.py`: 6 tests OK.
  - `check_money.py`: OK.
