# Design direction, 2026-11-16 (APPROVED by Nick 2026-11-16, with the changes in section 0)

Nick's brief (2026-11-16): the site is "way too complex and complicated to navigate". Make it "more organized, easier
and intuitive to navigate, and beautiful". Redesign menus and pages; decide what to combine and relocate. Test case:
"how much money has been spent historically by mayor candidates in the Democratic primary" must be easy to find and
pleasant to read. Planning on Fable (main session); implementation on Opus (high/medium) and Sonnet.

Nothing in this file is built. No data changes are proposed anywhere in it.

## 0. Nick's decisions (2026-11-16) — these override anything below that disagrees

- **D1 approved**: "I like your design direction structure." Reorganize around Governments / Offices / People /
  Elections with tabs.
- **D2: keep the three looks** (Ballot & Ink, Line Map, Wayfinding), light and dark each. Section 5's "one look" is
  dropped. The switcher and the theme toggle move out of the header's main row into one compact "Display" control,
  so the header is still one row. Every new component must be styled through the existing look tokens
  (static/css/looks.css) and checked in all 3 looks x light/dark.
- **D3: person pages are included in this build** (read from "Let's include person pages not as well" as "now as
  well"; confirm with Nick if he meant otherwise). They come after offices, governments and elections.
- **D4: no mock-up step.** Go straight to the generator. Step 0 in section 7 is dropped; the foundation step's
  Mayor of South Bend page is the first thing Nick reviews.
- **New: maps organize the home page.** The home page leads with the county map as a way in: layers for cities and
  towns, townships, school corporations, county districts, city council districts and legislative districts; a click
  on an area opens a panel with that government's or district's links (its page, its offices, its elections, its
  money). Reuse the existing map code (civic/map.py, district_map.py, layers.py); no new geometry.

## 1. What is wrong today (measured on the live site, commit ef78b46)

**The test case.** The answer exists, but:
- Search finds nothing for "mayor money", "campaign finance mayor" or "primary". It only matches names of places,
  offices and people.
- The route is Topics > Money > Campaign money > (map) > City of South Bend > scroll 2.5 screens of a 12.4-screen page
  > "Mayor of South Bend" > open the fold "This seat over time: 16 elections" > read the third column of a table.
- The primary figures are sentences in bullet lists inside a table cell, filed under the *general* election row.
  There is no chart, and no way to compare 2011, 2015 and 2019 at a glance.

**The cause.** The site is organized by kind of record (Elections, Money, Your governments, Community & history,
Data). Readers ask about a thing: an office, a person, a place, an election. One office's facts are split across
pages. For Mayor of South Bend:

| Fact | Where it lives now |
|---|---|
| What the office does, who holds it | places/south-bend/, your-governments/, officeholders/ |
| Election results (general and primary, 1963 to 2023) | elections/results/ (explorer), places/south-bend/ (recent only) |
| How close the races were | elections/margins/ |
| Campaign money, current cycle | money/campaigns/south-bend/ |
| Campaign money, history and primaries | a fold inside the race card on money/campaigns/south-bend/ |
| List of mayors | history/ |
| Notable mayors | history/people/ |
| How to run for it | run/ |

**Symptoms of the same cause.**
- Pages are stacks of folds: money/budgets/ has 182 folds, 151 tables and 2,054 links; money/campaigns/county/ has
  262 folds and 48,600 words; places/south-bend/ has 29 folds and 423 links.
- The Topics menu shows 28 links in 5 columns. Three of them are near-duplicates (By the numbers, Close races,
  Turnout); "Who holds office now", "Places", "Map" and "Your place" overlap.
- Five bands of chrome sit above the content on every page: masthead, search + look switcher, nav bar, "pick your
  place" bar, UNOFFICIAL banner. On a 900 px screen the page title starts at about 280 px.
- Every page ends with "Gaps on this page (N)" and "Sources on this page (N)" sections, and status badges
  (COMPUTED, OFFICIAL, SINGLE SOURCE, SECONDARY) sit inline in running text.

## 2. The direction: one page per thing, the same lenses on each

Four kinds of thing, each with one home page, built from one template:

| Thing | Count | Home page | Exists today? |
|---|---|---|---|
| Government (county, cities, towns, townships, school corporations, special units) | 37+ | `/governments/<id>/` | Places yes (22); county and schools are one-off pages; the 6 school corporations share one page |
| Office (a seat or body: Mayor of South Bend, County Council District C, PHM board) | 127 | `/offices/<id>/` | **No.** This is the missing page |
| Person (officeholders and candidates) | about 400 | `/people/<id>/` | No (32 notable people share one page) |
| Election (2023 city election, 2024 general, each primary) | 42 | `/elections/<id>/` | No (one results explorer) |

Every home page has the same tabs, in the same order, showing only the ones that apply:

**Overview · Elections · Money · History · Sources**

- **Office page** (the test case): Overview = what it does, who holds it, term, next election, how to run.
  Elections = every general *and primary* contest, newest first, each a compact result bar. Money = one chart per
  cycle: each candidate's raised and spent, primary and general side by side, then the report table. History = every
  holder (the mayors timeline moves here).
- **Government page**: Overview = at a glance, its offices (each a link to an office page), contact. Elections =
  recent results and party control. Money = budget, money in and out, tax base, debt. History, Sources.
- **Person page**: offices held, every race run, their committees' money over time.
- **Election page**: turnout, then every contest on that ballot, each linking to its office.

Result for the test case: type "mayor" in search > "Mayor of South Bend" > **Money** tab. Two clicks. Or
Offices > South Bend > Mayor > Money. The tab opens on a chart of every cycle with money on record (2007, 2011, 2015,
2019 primaries from news reports; 2023 from filings), with a Primary / General switch and a party filter.

Tabs are real URLs (`/offices/south-bend-mayor/money/`), so they work with JavaScript off, can be linked and
searched, and each stays short. Target: no page over about 4 screens before the reader chooses to expand something.

## 3. Menus

**Top bar (one row):** logo · **Governments · Offices · Elections · Money · Learn** · search · "My place" chip.

| Menu | Opens to | Contains |
|---|---|---|
| Governments | Map + list by type | County, cities and towns, townships, school corporations, special units, state legislators' districts |
| Offices | Filterable list (by government, level, up next) | Every office with its current holder; "who holds office now" is this list |
| Elections | Timeline of elections + next ballot | Each election's page; Compare: close races, turnout, uncontested seats (one page, three tabs); judges and ballot questions |
| Money | Two doors: Government money, Campaign money | Budgets compared, tax bill; campaign money browser (by office, by election, by candidate) |
| Learn | Guides | How elections work, what counts as a budget, who handles this, run for office, how the state shapes local, learning paths, for teachers |

- No mega-menu. Each top item goes to a hub page that does the browsing; at most 6 links in any dropdown.
- **Search becomes the main door.** It indexes offices, people, governments and elections *with their tabs*, plus
  plain words ("money", "budget", "primary", "results"), so "mayor money" returns "Mayor of South Bend › Money".
- **Footer** holds: About and methods, Data downloads (the 13 data pages), Sources index, Corrections log, Community
  profile, Not your county, theme.
- "My place" stays, as one chip in the top bar. When set, hubs open filtered to the reader's governments.

## 4. What moves where (every current URL keeps working through a forward)

| Today | Becomes |
|---|---|
| places/<id>/ (22) | governments/<id>/ with tabs |
| county/ | governments/county/ with tabs; courts and appointed boards become sections under Overview |
| schools/ (6 corporations on one page) | 6 governments/<id>/ pages + a short "school board rules" guide under Learn |
| state/, state/your-legislators/ | 9 legislator office pages + governments list entry; state explainer to Learn |
| your-governments/, officeholders/, places/index, map/ | Governments hub (map + list) and Offices hub |
| who-handles-this/, elections/how-it-works/, money/what-is-a-budget/, state/how-the-state-shapes-local/, run/* (7), teach/ | Learn |
| elections/results/ (explorer) | elections/<id>/ pages + each office's Elections tab |
| elections/landscape/, margins/, turnout/ | elections/compare/ with three tabs |
| elections/calendar/ | Elections hub ("next on the ballot") + each office's Overview |
| money/campaigns/<area>/ (30), money history folds, "This seat over time" | Each office's Money tab; area pages become short lists of that government's offices with totals |
| money/campaigns/all-filings/, other-committees/, how-it-works/ | Campaign money browser; committees get person-style pages; how-it-works to Learn |
| money/budgets/ (182 folds) | Each government's Money tab + a short "Compare budgets" page (map, per-resident chart) |
| history/ | Mayors to mayor office pages; party control to government pages; turning points stay as one History guide |
| history/people/ | People hub ("notable" is a filter) |
| community/* (5) | Each government's Overview ("the community" strip) + one Community profile page |
| data/* (15), about/sources/ | Unchanged pages, linked from the footer |

Rough size: about 113 pages today become about 37 governments + 127 offices + 42 elections + hubs and guides, each
with up to 5 short tab pages. More URLs, far less on each. People pages (about 400) are the largest addition and can
be a later phase.

## 5. Visual direction

Aim: a calm reference work where the data is the decoration. Closer to a well-set almanac than a poster.

- **One look, light and dark.** Recommend retiring the three-look switcher (see decision D2). It occupies the
  header, triples every visual check, and forces every component to be designed for the weakest common case.
- **Type.** Keep the condensed display face for page titles only, at about half today's size and not all-caps for
  long names. Body and tables in the text face. Monospace only for document ids. Numbers right-aligned, tabular.
- **Chrome.** One header row, 56 to 64 px. The UNOFFICIAL notice appears only on pages that show 2026 figures, as a
  small line near the figure. Breadcrumb becomes "Offices › South Bend › Mayor".
- **Surfaces.** Remove most boxes and heavy rules. Sections are separated by space and a small label. Cards only
  for things you click.
- **Data first.** Every tab opens on a chart or a ranked list, with the table behind "Show the table" (already a
  pattern in civic/charts.py). Money per cycle = paired bars per candidate (raised solid, spent outlined, as now),
  shared scale across cycles so years compare.
- **Confidence without clutter.** Status badges become one small mark beside the figure (official / unofficial /
  from a news report / computed), with the wording in a tooltip and in the Sources tab. Party color rules and the
  neutrality rules do not change.
- **Sources and gaps** move to the Sources tab of each thing. Footnote numbers stay next to figures.

## 6. Decisions for Nick

- **D1. Reorganize around Governments / Offices / People / Elections with tabs** (sections 2 to 4), instead of
  another round of trimming the current topic structure. Recommended. It is the only option that fixes the test case
  at the root.
- **D2. One look or three.** Recommend one (a refined Ballot & Ink), keeping light/dark.
- **D3. People pages now or later.** Recommend later: offices, governments and elections first (they answer the
  test case); person pages in a second phase.
- **D4. Mock-ups before any generator work.** Recommend yes: 4 static pages with real data, published to a private
  Artifact link for Nick to click through: new header + home, Offices hub, Mayor of South Bend (all tabs), South
  Bend government page. Only after approval does the generator change.

## 7. How it would be built (after D1 to D4)

| Step | What | Model | Scale |
|---|---|---|---|
| 0 | Mock-ups (D4), revised until Nick approves the look and the journey | Opus high, 1 agent; Fable reviews | small |
| 1 | Foundation: tab template, new header/nav/footer, URL forwards for every old path and anchor, search index with tab and keyword entries, one-look CSS tokens | Opus high | medium |
| 2 | Office pages (127) from existing data and existing race-card / money-history / results code | Opus high | large |
| 3 | Government pages: places template to tabs; county, 6 school corporations, special units onto it | Opus medium | large |
| 4 | Election pages + Elections hub + Compare | Opus medium | medium |
| 5 | Money hub, campaign money browser, Compare budgets; retire the long pages | Opus medium | medium |
| 6 | Learn hub, footer pages, hubs polish; learning paths re-pointed | Sonnet | small |
| 7 | Checks: build --check, all tests, old-URL fixture, 400 px, light/dark, keyboard, JS-off, CSP; screenshots of every template | Sonnet + main session | medium |
| Later | People pages (D3) | Opus medium | large |

Expected total: in the range of the 2026-11-09 redesign (2 to 3M tokens) or somewhat more, spread over steps; at
most 3 agents at once; a commit as rollback point before step 1 (needs Nick's "commit"). Each step is verified in the
browser by the main session before the next starts. A fresh estimate and model choice go to Nick before each large
step is launched.

Rules carried over: no data CSV edits; never run res_main.py, build_money.py, build_gov.py,
build_community_people.py; neutrality rules unchanged; commit, push and deploy only on Nick's words.
