# Wave B, batch 2: Elections by the numbers, 2026-11-09

This batch splits the old one-page `elections/landscape/` (66 screens, 14 tables) into a short overview and three pages, one per measure. It also merges "Up next" into the calendar and moves the results page's turnout table. Nothing is committed.

Checks, all run at the end, after batches 3 and 4 had landed:
- `python -P -E tools/site/build.py --edition st-joseph --check` ends **PASSED** (112 pages).
- `python -P -E -m unittest discover -s tools/tests` gives **246 OK**. 27 of those are new, in `tools/tests/test_wave_b_numbers.py`.
- `python -P -E tools/check_gov.py` reports **0 errors** (23 warnings, all from before this batch).

## 1. What was built

| Page | What it is now |
|---|---|
| `elections/landscape/` "Elections by the numbers" (same URL, Q2) | A short overview: four summary cards in a 2×2 grid, each with a chart and links to its full page. The cards are Turnout, How close were the races?, Up next, and How officeholders first took office. Also "What this page does not do" (with B5), Gaps and Sources. 3.5 screens |
| **NEW** `elections/margins/` "Margins: how close each race was" (nav label "Close races", Q3) | See §1.1 |
| **NEW** `elections/turnout/` "Turnout and how ballots were cast" (nav "Turnout") | The turnout text, the two column charts and the denominators table (now in a see-all fold with Copy CSV), then Straight-party ballots. All moved verbatim |
| **NEW** `officeholders/` "Who holds office now" (Your governments, Q5) | The "how they first took office" chart is the lesson, followed by the sourced vacancy-caucus rule and a link to How vacancies are filled. Below that: every officeholder in one fold per government. Filters are Level, Government, First took office by and words. Each office links to its card on its government's page (`office-<id>`). The full table `took-office-list` is in a see-all fold with Copy CSV |
| `elections/calendar/` | "Every seat, by year" is now year sections `#year-2026` … `#year-2030`, each with one fold per government. For **2027 and 2028** each seat also shows the holder now, party label, since when, how they first took office, and the term-limit status (the old Up next columns). A filter bar runs over all years. Two see-all folds follow: the old **`up-next-table`** (71 rows, every column, same filters) and the old `calendar-table` (188 rows, same filters). The strip cards link to their year. The term-limit rule paragraph and note moved to "How this is computed" (`#term-limits`) |
| `elections/results/` | "Turnout first" (`#turnout`, a path stop) is now one sentence, the general-election turnout chart and a link to the turnout page. The 28-row table moved. The page is also smaller (§4) |

### 1.1 The margins page, section by section

**§1 The short answer** (`#short-answer`)
- It opens with the uncontested count and its definition: "**608 of the 981 races** for local office decided inside the county from 2010 to 2026 had no contest: no more candidates on the ballot than seats to fill." The COMPUTED badge and the canvass citations sit beside it (Q4).
- Four tiles follow: 608 / 344 / 29 / 981, then the line "981 = 608 + 344 + 29".
- One share bar (`#margin-bands`) shows uncontested, under 5, 5 to 15, over 15 and not measurable.
- The definitions callout `#bands` is kept verbatim, with one paragraph added that defines "uncontested".
- The old count paragraph is kept verbatim, with the new numbers.

**§2 By level of government** (`#by-level`)
- Small multiples with `share_bars`: 9 office groups in fixed office order (county, city/town, township, school, legislature), never ordered by value.
- Every group's bar includes its uncontested and not-measurable races, so a share is never shown without its base.
- Each group's label links to its level in §3.
- Colors are ink for uncontested and the accent ramp for the bands, darker for closer races. Not measurable uses the no-data mark. No party colors anywhere (Q10).

**§3 Find a race** (`#find`)
- The map is a `district_map` with 8 layers: Townships, Cities and towns, School corporations, Commissioner districts, County council districts, City council districts (South Bend and Mishawaka together), Indiana House, Indiana Senate.
  - Fills only tell neighbors apart.
  - The panel shows each area's contested, under 5, 5 to 15, over 15, uncontested and not-measurable counts, plus its closest race.
  - District layers carry a caveat: "The lines drawn are the ones used from 2022/2023. Races before that were held under earlier lines".
  - Each race held before the current lines says so in its row.
- `pick_one`: the map, a link or `#area-<key>` opens that area's fold and collapses the others. With JS off, all 58 areas are open.
- **Areas → seats → races.** Areas are listed under level headings (`#lvl-county` … `#lvl-legislature`).
  - Each seat shows "N contested · N uncontested · closest X points (year)".
  - Each race row, newest first, shows: the margin in points and votes apart, its band, the date and election (or "Republican primary", the canvass label), and a 0–30 point strip with the band edges marked (`aria-hidden`; the number is in the text).
  - Then the two candidates compared: "Most votes: …" in one-seat races, "Last inside the 3 seats: … Next: …" in multi-seat races.
  - Then the status label, **Full result** (`results#contest-<id>`) and, for 2020–2024 generals on the vote map, **How areas voted** (`map#race-<id>`).
  - Uncontested races are listed under each seat, each linking to its full result, with the unopposed candidates.
- Filters are **Office, Place, District** and words (seat name or candidate name; no party field is matched, and there is no party filter).
  - They work through the new `tablefilter.js` deep mode: they hide seats, hide areas and levels left empty, and open the folds that match. Reset puts the folds back.
- Not on the map, but in the list: Countywide offices (row offices and courts) and LaVille schools (mostly in Marshall County). Walkerton wards, Osceola wards and school-board districts are seats inside their town or corporation; there are no ward or school-district shapes.

**§4 All races as a table** (`#all-races`)
- This is the old `margins-table`, with the same id and Copy button, in a see-all fold (`#margins-table-all`).
- It has the same 6 filters (year, election, band, office, place, district), words and sort (closest first / newest first), and copies only the shown rows.
- Each contest name links to its full result.

**§5** "What this page does not do" and the party-codes line, then Gaps and Sources.

The scope rules are unchanged:
- no statewide offices;
- no legislative districts in years they crossed the county line;
- no questions, retention or straight-party lines.

The band names and ids are also unchanged (`under-5`, `5-15`, `over-15`). Ordering is fixed: groups by office, races by margin or date.

### 1.2 One data correction (please review: the headline number changed from 599 to 608)

The old `margin()` counted the canvass's unnamed **"Write-in" total line** as a candidate. That made nine 2012 school-board races with one named candidate for one seat look "contested" by ~97 points. Examples are John Glenn Johnson Township, PHM Harris Township and New Prairie District 1.

Now:
- an unnamed write-in total is not a candidate;
- a named write-in ("Michael Schalk (write-in)") still is;
- write-in votes still count in the total of votes cast.

Two related fixes:
- "No more candidates than seats" is now checked before missing votes, so an uncontested race with blank vote counts is uncontested, not "not measurable".
- A race with no votes recorded is "not measurable", not uncontested.

Effect: uncontested 599 → **608**, contested 353 → **344**, over 15 points 152 → **143**. Under 5 (111), 5 to 15 (90) and not measurable (29) are unchanged.

The results explorer's UNCONTESTED tag now uses the same rule, through a `u` flag in its payload.

### 1.3 Edge cases handled
- **Tie:** Walkerton Ward 4, 2023 Republican primary, 55–55. It reads "0 points · tied", then "Tied: Kyle Norris (R) and Bryan Vandall (R), 55 votes each. The canvass marks Kyle Norris as elected; how the tie was settled is not in the guide's data."
- **Multi-seat races:** the row says "Last inside the N seats / Next".
- **Primaries:** candidates without a party code show no "(no party)" tag. The primary's own label names the party.
- **Not measurable:** 29 races are listed in their seat with the reason ("the seat count is not in the guide's data") and every candidate's name.
- **Partial data:** each row keeps its status label (FROM SCAN, UNOFFICIAL, SECONDARY …) and LOW CONFIDENCE when present.
- **Old district lines:** see §1.1.
- **County commissioner races named "2nd" / "3rd" (2016):** these are now District 2 and 3. They used to have no district in the filter.

## 2. Where every old landscape piece went

| Old landscape piece | New home |
|---|---|
| Hero dek and scope | Overview (rewritten to name the 4 measures) |
| Turnout text, `#turnout-general`, `#turnout-primary`, `#turnout-denominators` | `elections/turnout/#turnout` (the table is in a see-all fold, same ids). The overview's Turnout card keeps `#turnout` |
| Margins callout `#bands` | `elections/margins/#bands` (verbatim, plus the "Uncontested" definition) |
| Margins count paragraph | Margins §1, under the tiles (verbatim, new numbers) |
| Band hbar `#margin-bands` | Margins §1 as a share bar with the same id (adds uncontested and not measurable; its table view lists every count) |
| Filters + `margins-table` (+ `-copy`, `tf-margins-table-*`) | Margins §4 see-all fold, same ids. Office, place and district filters also live in §3 |
| Canvass citation line, party codes | Margins §3 key line / §4 |
| Up next: intro, rule paragraph, filter, `up-next-table`, note | Calendar: intro in §4, the table as a see-all fold (same ids), rule and note in §5 "How this is computed" (`#term-limits`), holders in the 2027/2028 year lists |
| How incumbents took office: intro, `#took-office` hbar, filter, `took-office-list` | `officeholders/` (same ids); a summary card on the overview |
| Straight-party share (`#straight-party`, `straight-<eid>` tables, note) | `elections/turnout/#straight-party` (verbatim) |
| "What this page does not do" | Overview (full list, with B5); each leaf repeats the bullets that apply |
| Gaps | Overview keeps the union. Margins: seat-count and winner gaps. Turnout: straight-party and 2012 election-row gaps. Calendar: the "announced retirements" gap. Officeholders: the terms gaps |
| Results "Turnout first" table `#turnout-table` | `elections/turnout/#turnout-denominators` |

**B5:**
- The old line was "No precinct maps…".
- The new line, on the overview, turnout and margins: "No voter-file data or donor details. Precinct results for the 2020, 2022 and 2024 general elections are on the map, in its How areas voted layer [link to `map/index.html#list-votes`]; precinct files are linked on Data and sources."
- The years are read from `map_votes.json`.

## 3. Anchor proof

**Fixture.** `tools/tests/fixtures/anchors_before_wave_b2.json` holds every id that landscape (91), results (1,274) and calendar (50) had before this batch, taken from the built site. Source ids (`src-*`) are left out because they follow citations.

**Moved maps.** Landscape and results ship `#moved-anchors`. I extended `moved.js` so any page can do this, and a destination may give a new id: `{"turnout-table": "../turnout/index.html#turnout-denominators"}`.

**Tests**
- `test_every_old_anchor_still_resolves`: every old id is either still on its page, or its page's map sends it to a built page that has the target id.
- `test_moved_maps_point_at_real_ids_only`: every map entry has left its page and lands on an id that exists.
- `test_overview_keeps_card_anchors`: `#turnout`, `#margins`, `#up-next` and `#how-took-office` (and their `-h` heading ids) stay on the overview, so old links land on the right card even with JS off.
- `test_calendar_keeps_its_ids`.

**Browser check** (fresh loads; each landed with its target 64 px from the top):

| Old link | Lands on |
|---|---|
| `landscape#margins-table` | `margins#margins-table` |
| `#bands` | `margins#bands` |
| `#tf-margins-table-district` | `margins#tf-margins-table-district` |
| `#up-next-table` | `calendar#up-next-table` |
| `#took-office-list` | `officeholders#took-office-list` |
| `#straight-2024g` | `turnout#straight-2024g` |
| `#turnout-denominators` | `turnout#turnout-denominators` |
| `results#turnout-table` | `turnout#turnout-denominators` |
| `landscape#turnout`, `#how-took-office` | Stay on the overview cards |

**Learning path 6** now stops at turnout `#turnout`, margins `#short-answer`, calendar `#year-2027`, officeholders `#how-took-office`, then data `#sources`.
- An old bookmark such as `landscape#path-elections-by-the-numbers-2` is sent by `moved.js` to the stop's new page, and the path bar shows "Stop 2 of 5".
- The stop "Up next" lead no longer says "known retirements", which the guide does not collect.

## 4. Screens and sizes

Screens are height ÷ 800, JS on, first load, Ballot look, light theme.

| Page | 1280 before | 1280 after | 400 before | 400 after |
|---|---|---|---|---|
| elections/landscape (overview) | 66.1 | **3.5** | 90.9 | **5.9** |
| elections/margins (new) | — | 9.9 | — | 14.9 |
| elections/turnout (new) | — | 5.4 | — | 7.2 |
| officeholders (new) | — | 4.8 | — | 6.6 |
| elections/calendar | 21.3 | **11.3** | 28.5 | **17.9** |
| elections/results | 10.5 | 9.7 | 21.4 | 19.6 |

JS off, everything open: margins 132.5, officeholders 43.0, calendar 56.1 screens. Everything is visible and reachable.

| Bytes (raw / gzipped) | Before | After |
|---|---|---|
| elections/results | 923,324 / 134,882 | **848,327 / 131,683** (−8% raw) |
| elections/landscape | 641,786 / 66,492 | 81,664 / 18,114 |
| elections/margins | — | 828,966 / 105,997 |
| elections/turnout | — | 97,470 / 18,274 |
| officeholders | — | 329,608 / 35,960 |
| elections/calendar | 254,613 / 28,074 | 444,343 / 44,556 (adds the year lists and the 71-row up-next table) |

**How the results page was slimmed, without losing content or link targets.** Every `#contest-<id>` row is kept, and the payload test still checks the ids.
- The every-contest table uses the short election name ("Nov 3, 2026 general"), the place filter by index, and no "(unofficial)" after "Elected" (the Status cell says it).
- The explorer payload drops the election prefix of each id, the default status "official" and the default "vote for 1". `elections.js` rebuilds them.
- The turnout table moved out.
- Gzipped, it barely moves, because the repetition was already compressible.

**How the long new lists are kept light.** They use plain status labels (no per-row link or tooltip; `plain_badge`) with one "Status labels are defined in About" link per section. Those badge links were ~240 bytes each, hundreds per page.

## 5. Browser checks (Playwright, own contexts)

- **Matrix:** 6 pages × 3 looks × light/dark × 1280/400 = 72 loads. The look and theme applied every time, with no horizontal overflow and no console errors.
- **Map:**
  - Hovering Clay Township fills the panel (11 contested, 7 under 5, 15 uncontested, closest 0.17 points).
  - Clicking it sets `#area-clay-township`, opens only Clay, and the state line reads "Showing Clay Township".
  - **Keyboard:** Enter on the "County council districts" tab, then focus District H: the panel names it. Enter opens `#area-council-h` alone.
- **Filters:**
  - Office = County council gives "9 of 135 seats shown", with 9 areas shown and opened. Reset gives 135 again, and only Clay is open, as before.
  - Words "Robbins" finds 1 seat.
  - Calendar: 2027 + "mayor" gives 2 seats, with Mishawaka and South Bend opened.
- **Copy CSV:** the margins table filtered to Under 5 + Township offices gives "45 of 344 races shown" and "Copy 45 shown rows".
- **Landing fix:**
  - A fresh load of `#area-clay-township` first ended 200 px off. Web fonts arrive after `pick_one.js` scrolls, and the text above rewraps.
  - The new `margins.js` re-lands once the fonts have loaded, unless the reader has scrolled, typed or clicked.
  - After the fix, 10 cases (margins areas, `#margins-table`, `officeholders#gov-south-bend`, `calendar#year-2027`, at 1280 and 400) all land at 64 px.
- **JS off:** all 61 / 34 / 67 folds are open, no row is hidden and filter bars are hidden. `#area-clay-township` lands on Clay.
- **Screenshots** are in `.playwright-mcp/`:
  - `wb2-before-landscape-1280.png`
  - `wb2-margins-1280-{top,short-answer,by-level,find,clay,keyboard-council-h}.png`
  - `wb2-margins-400-{walkerton,short-answer}.png`
  - `wb2-margins-{1280,400}-{line,wayfinding}-{light,dark}-clay.png`
  - `wb2-landscape-1280-*.png`, `wb2-turnout-1280-*.png`, `wb2-officeholders-1280-*.png`
  - `wb2-calendar-1280-by-year.png`, `wb2-calendar-400-2027-mayor.png`

## 6. Tests

New, in `tools/tests/test_wave_b_numbers.py` (27):
- **Anchors and paths:** the anchor proof (§3); path 6 stops land; no duplicate ids on the 6 pages.
- **Margins:**
  - the lede opens with the uncontested count and has the COMPUTED badge;
  - the tiles add up;
  - the table rows equal the contested count;
  - every one of the 981 races is in the find list and links to an existing `results#contest-<id>`;
  - every map shape links to an area fold that ships open;
  - no party classes and no party filter;
  - the find filters' options cover every value;
  - bands, scope and group order are pinned.
- **Other pages:**
  - turnout: one denominator row per election, plus the straight-party tables;
  - results: the turnout section points to the turnout page;
  - officeholders: list rows = table rows = current holders, and the folds ship open;
  - calendar: the up-next rows are 2027/2028 only, and holders appear in 2027 but not 2030;
  - B5 wording.
- **`margin()` unit tests:** write-in total, named write-in, write-in votes in the total, tie wording, multi-seat, uncontested with blank votes, and a missing seat count.
- **Static checks:** the scripts are ASCII with no innerHTML; `moved.js` handles new ids and path stops; `tablefilter.js` deep mode exists; the area and district helpers work.

Updated:
- `test_page_organization.py`: the landscape table and filter checks now point at their new pages (margins, calendar, officeholders).
- `test_wave_a_patterns.py`: the payload id test rebuilds ids from `e` + `i`.

## 7. Edits outside the listed ownership

All are small and additive:
- `static/js/moved.js`: a generic `#moved-anchors` map for any page, `#` destinations, and forwarding of repointed path stops. The data and about pages behave as before.
- `tools/tests/test_wave_a_patterns.py`: one line (payload id).
- `tools/site/README.md`: four rows in the Layout table.

I did not touch `shell.py`, `places.py`, `related.py`, the batch-4 modules, `county.py`, `state.py`, `money.py`, any data CSV, `Roadmap.md` or `docs/session-handoff.md`.

## 8. Questions for Nick

1. **The write-in correction moves the headline from 599 to 608 uncontested** (§1.2). It is a definition fix: an unnamed "Write-in" total is not a candidate. Keep it?
2. **District maps show today's lines for races back to 2010.** Every pre-2022/2023 race says it was held under earlier lines, and the panel says so too. Is that clear enough, or should pre-redistricting races be left off the district layers and kept only in the list?
3. **Margins page weight** is 0.83 MB raw / 106 KB gzipped. Most of it is the list (all 981 races with links) plus the researcher table (344 rows). Is that acceptable, or should the table be dropped in favor of Copy CSV from the list?
4. **Officeholders chart bars do not link** to a filtered list, as the review sketched. `hbar` has no link support, and the filter row sits right under the chart. Add it later if wanted.
5. **Path 6** now starts at the turnout page rather than the overview. The review says both "overview is the learning-first entry" and "stops are repointed to the leaves". Should the overview be added as stop 1?

## 9. Files

New:
- `tools/site/pages/elections_numbers.py`
- `tools/site/static/js/margins.js`
- `tools/tests/test_wave_b_numbers.py`
- `tools/tests/fixtures/anchors_before_wave_b2.json`
- this report

Changed:
- `tools/site/pages/elections.py`: `margin()` fix, `is_writein_total`, calendar merge, results turnout and slimming, `moved_anchors`, `plain_badge`, `badge_key`; the old landscape builder removed
- `tools/site/civic/sitemap.py`: 3 entries, landscape nav label "By the numbers", path 6
- `tools/site/static/js/elections.js`: payload rebuild, the `u` flag
- `tools/site/static/js/tablefilter.js`: deep mode, additive
- `tools/site/static/js/moved.js`
- `tools/site/static/css/elections.css`: overview, margins, officeholders, calendar
- `tools/site/README.md`
- `tools/tests/test_page_organization.py`
- `tools/tests/test_wave_a_patterns.py`
