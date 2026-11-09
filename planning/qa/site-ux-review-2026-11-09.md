# Site UX review: journey, layout and navigation, 2026-11-09

Read-only review of all 109 built pages in `site/st-joseph/`. Nothing in the site or generator was changed. Nothing committed.

## How this was measured

- **Screens** = rendered page height ÷ 800, measured in Chrome (own tab, same-origin iframes, JS on, folds closed as on load) at **1280 px** and **400 px** wide on 2026-11-09. Format below: `1280 / 400`. No page overflowed horizontally at either width.
- **Tables / rows / big tables** = parsed from the built HTML (`<table>` count, `<tr>` count, tables with 15+ rows). Most tables sit inside "Show table" `<details>`, so rows overstate pain; screens are the better measure.
- **Visual review**: desktop screenshots of 30+ pages in the default Ballot look, dark theme. The browser window would not go below about 500 px, so phone numbers come from the 400 px iframes, not from eyeballing. Light theme and the Line map and Wayfinding looks were **not** checked visually in this pass.
- **Generator code read**: `civic/sitemap.py`, `civic/shell.py`, `pages/elections.py` (landscape, results, calendar), the new `civic/pick_one.py` and `civic/district_map.py` from the map agent, plus the CSS for the bugs below.
- **Duplication** was measured by comparing paragraphs of 8+ words across pages (script in the scratchpad).
- **Web searches**: none.
- **Snapshot warning**: county/, schools/, money/budgets/ and state/your-legislators/ are being rebuilt by the map agent. Their numbers are from before that work lands.

### Bugs found on the way (fix first; all small)

| # | Where | What | Root cause | Fix |
|---|---|---|---|---|
| B1 | money/campaigns/how-it-works/ "How complete the record is" | The coverage grid's cells stack in one column. The table is **25,400 px tall** (31.7 of the page's 41.4 screens) | `static/css/places.css` line 5 defines a **global** `.cov { display:inline-block; ... }` for the place-page coverage chips. Every area CSS file is joined into one stylesheet, so it hits `table.cf-coverage td.cov` (`campaigns.css` line 13). `.cov-none` collides too (dashed border) | Scope the place rules (`.cov-strip .cov`, `.cov-strip .cov-none`), or rename them `.pcov-*`. The page should then drop to about 10 screens. Add a checker rule: no two area CSS files may define the same bare class |
| B2 | elections/calendar/ "What's on your next ballot", the saved place's card | The "Your place (saved on this device)" tag cannot be seen in dark mode: text rgb(27,26,23) on background rgb(27,27,27) | `.here-tag` uses `background: var(--ink); color: var(--surface)`. Inside the gold `.elx-next-card`, `--ink` is redefined dark, but `--surface` stays dark in dark mode | Give `.here-tag` its own token pair, or set both inside `.elx-next-card`. Check all 3 looks × 2 themes |
| B3 | index.html and your-governments/ seat diagram | The party-summary bullets ("Board of Commissioners (1 D, 2 R) · 3 seats") float inside the appointed-board row, to the right of the square glyphs. The SBCSC label's citation numbers overlap the box below it | Layout of `bodies_block` inside `.layer` rows (not traced further) | Put the body summary on its own line under the glyphs. Check at 400 px |
| B4 | money/campaigns/ map, first view | The default layer "County · Countywide offices" is one solid shape covering the whole map. The first thing a reader sees teaches nothing | Default-layer choice | Open on a layer with several areas, for example County council districts or Townships |
| B5 | elections/landscape/ "What this page does not do" | Says "No precinct maps… Precinct files are linked on Data and sources" without mentioning that /map/ already shows precinct results for 2020–2024 | Text written before the vote map existed | Add "Precinct results for the 2020–2024 general elections are on the map" with a link (wording rules apply) |

---

## 1. The journey

### 1.1 Entry points today

| Entry | What it offers | Observation |
|---|---|---|
| **Home** (`index.html`, 5.2 / 8.5 screens) | Big claim ("One address. 6 governments. 62 elected seats."), place picker (map + radio lists), seat diagram by layer, "Next on your ballot" strip, 7 path cards, county facts | Strong. It is the best page on the site for "who represents me", and the seat diagram is the clearest teaching graphic the guide has |
| **Top nav** | `Paths` (goes to `index.html#paths`) · `Reference ▾` (27 links in 4 groups) · `For teachers` · `About & methods` | "Reference" is a library word. Readers look for topics ("Elections", "Money"). "Paths" is unclear until you reach the cards. The menu has no hub pages: every link is a leaf |
| **Header search** | Combobox over the search index | Good. It is the fastest route for people who know a name |
| **"You are here" bar** | Saved place on every page; "Change" goes to `index.html#pick` | Good. But only 3 places use the saved place for content: the home page, the calendar marker and the your-governments picker. Every other page ignores it |
| **Footer "Browse everything"** | 8 links (Places, County, Schools, State, Elections, Money, History, Data) | These are effectively the section hubs. Several are not hubs (State, Elections are content pages) |
| **Learning paths** | 7 paths, each a sequence of section anchors across pages, with a path bar | The idea is good. Weaknesses: path 6 ("Elections by the numbers") sends readers into a 66-screen page 4 times, and the stops land in the middle of long pages |

### 1.2 Core flows: how they work today

**Flow A: where I live → who represents me → what they spend → how elections went → how to get involved**

```
Home: pick place ─► seat diagram ─► (layer title links) ─► place page / county / schools / state
                                                          │
place page ──► Recent results (inline) ──► elections/results (generic, not filtered to the place)
           ──► Budget (inline) ──► money/budgets (the whole 79-screen page)
           ✗  no link to money/campaigns/<this place>/      (campaign area pages have 1 inbound link each)
           ✗  no link to map/#race-… (how this place voted)
           ✗  no link to the tax rate for this place, community indicators for this place, or the calendar entry
           ✗  no link to "run for <this office>"
```

Measured in-content outbound links (main content only, excluding data/ pages):
- penn-township: 7 (about, results, budgets, what-is-a-budget, 3 places)
- south-bend: 11
- county: 6
- schools: 3
- landscape: 4
- history: 2 (about, community/people)

Inbound in-content links:
- money/index: 0
- indiana: 0
- every money/campaigns/<area>/ page: 1 (from the campaigns index only)
- every data/<set>/ page: 1

**Dead ends:** a reader who reaches a place, county or school page cannot get from there to:
- the money raised for those seats;
- that place's results in the explorer;
- the map view of how it voted;
- the "run for this seat" page.

**Flow B: learning path (student or teacher)**
`Paths` → path card → stop 1 (section anchor on a long page) → path bar "next" → … This works mechanically. Stops land in long pages whose next section is unrelated (the county page, landscape). Splitting landscape (section 3) gives the "Elections by the numbers" path four short pages, one per idea.

**Flow C: journalist or researcher**
Search → page → "Show table" → Copy CSV, or Data → dataset page → Copy CSV. Works. Weak points:
- Copy CSV copies every row even when the table is filtered (open item 2 of the fixes report);
- the results explorer has no per-contest deep link, so other pages can't link to one race.

**Flow D: someone thinking of running**
Home "Run for office" path → run/index → office page.
- The 6 office pages are **85% the same text** as run/index (45 of about 53 long paragraphs are identical).
- No page answers "which seat would I be running for at my address?" The district maps arriving now make that possible.
- Nothing links from a seat (county council District C) to its run page, its last margin, or its campaign money.

### 1.3 What's confusing today

1. **Four "where do I live" doors with overlapping content.**
   - Home picker + seat diagram.
   - `your-governments/`: the **same** picker and diagram again (158 of its 308 long paragraphs are identical to the home page), then a links list, a 25-row office table and meeting info.
   - `places/` map.
   - `map/` boundary map.

   The map and places pages are fine and do different jobs. your-governments repeating the home page is the confusing one.
2. **Duplicate content between pages** (each needs one home and links elsewhere):

   | Content | Appears on | Proposed single home |
   |---|---|---|
   | Turnout by election (28 rows) | results `#turnout` and landscape `#turnout` | new `elections/turnout/` |
   | Seats on the next ballots, with holders | landscape "Up next" (71 rows) and calendar "Every seat, by year" (188 rows) | calendar |
   | Rules, filing, ballot access, campaign-finance duties, vacancies | run/index plus 6 run/* pages (85% identical) | run/index; office pages keep only office-specific facts |
   | Picker + seat diagram | index and your-governments | index (your-governments shows the result for the saved place) |
   | "What townships do" | twice on every township page (§1 and the first paragraph of §2) | §1 only |
   | Council "what it does" | 7 identical rows on the South Bend and Mishawaka "How it's organized" tables | one row per body ("Common Council: 6 district + 3 at-large seats") |
   | Money in and out (2024 state reports) | county `#money`, place pages `#budget`, budgets "2024 spending and revenue" (10.9 screens) | the unit's own page; budgets shows the selected unit (map work) |
   | Legislators' campaign money | your-legislators "Campaign money" (101 rows) and money/campaigns/state-legislature/ | campaigns/state-legislature; legislators shows the chosen district's summary row + link |
   | Current officeholders | county cards, place cards, schools cards, landscape 163-row table | new `officeholders/` directory (cards stay on each unit page) |
   | Party control charts | history, county, places, state | each unit keeps its own; history is the side-by-side view; each links to it |

3. **Labels.**
   - "Reference" (menu).
   - "Elections by the numbers" (URL `landscape`; readers can't guess what is inside).
   - "Context" group.
   - Two menu items both called **"People"**: community/people and history/people, though the latter isn't in the menu at all.
   - "Map" vs "Places" vs "Find your governments".
   - "Judges & questions" (questions are ballot questions).
4. **Menu coverage.** These pages are reachable only through links or search:
   - the 6 run/* pages;
   - history/people;
   - 13 dataset pages and data/pull;
   - 31 campaign area pages;
   - about/sources.

   That's fine for leaves, but each needs a clear parent (hub) that lists it.
5. **Giant tables as the primary UI** on:
   - landscape (354 + 164 + 72 rows);
   - calendar (189);
   - all-filings (479 reports);
   - other-committees (33 open tables);
   - your-legislators (101);
   - your-tax-bill (4 × 32–38);
   - the how-it-works coverage grid (B1);
   - map/ (103-row "every race" list);
   - budgets (151 tables, map work in flight).

### 1.4 Target site map

Principle: **five topic hubs, each with one learning-first overview, then leaves.** Every leaf links back to its hub and sideways to the same entity on other topics (the "More about…" rail, pattern P1).

```
Home (index)                          pick your place · seat diagram · next ballot · ways in        [Keep]
│
├─ Your governments  (hub = your-governments/, redesigned as "Your place": results for the saved place)
│   ├─ places/            all places on a map                                                       [Keep]
│   │   └─ places/<22>/   city, town, township pages                                              [Adjust template]
│   ├─ county/            (+ district map, in flight)                                             [Adjust after map]
│   ├─ schools/           (+ show one corporation, in flight)                                     [Adjust after map]
│   ├─ state/ · state/your-legislators/ (+ district map, in flight) · state/how-the-state-shapes-local/
│   ├─ officeholders/     NEW: every current elected officeholder, filter by government, "how they first took office"
│   ├─ who-handles-this/                                                                          [Adjust]
│   └─ map/               full boundary map + "How areas voted"                                   [Keep]
│
├─ Elections  (hub = elections/index.html, NEW hub; the explainer moves to elections/how-it-works/)
│   ├─ elections/how-it-works/      MOVED from elections/index.html (anchors forwarded)
│   ├─ elections/calendar/          absorbs "Up next" (holders + term limits per seat)          [Merge]
│   ├─ elections/results/           explorer; turnout table moves out                            [Adjust]
│   ├─ elections/landscape/         becomes "By the numbers" overview: 4 summary charts → leaves  [Split]
│   │   ├─ elections/margins/       NEW: "How close were local races?"
│   │   └─ elections/turnout/       NEW: turnout odd vs even years + straight-party share
│   ├─ elections/judges-and-questions/                                                           [Adjust]
│   └─ run/ (+ 6 office pages, trimmed to office-specific facts)                                 [Adjust / Merge]
│
├─ Money  (hub = money/index.html)                                                               [Keep]
│   ├─ money/what-is-a-budget/ · money/your-tax-bill/ (preselect from saved place) · money/budgets/ (map work)
│   └─ money/campaigns/ (map) → <31 area pages> · how-it-works (B1) · all-filings · other-committees
│
├─ Community & history  (hubs = community/index.html, history/index.html)
│   ├─ community/people · income-and-work · housing-and-education · research-on-voting            [Keep]
│   └─ history/ · history/people/ (list view)                                                    [Adjust / Redesign]
│
└─ Data  (hub = data/index.html) → 13 dataset pages · data/pull                                 [Keep / Adjust pull]

Learn: Paths (index#paths) + teach/ ·  About: about/ · about/sources/ · indiana/
```

**Navigation bar (recommended; see open question Q1):**

```
[ Your place ]  [ Topics ▾ ]  [ Learn ▾ ]  [ About ]           (4 items: fits 400 px on one row)

Topics ▾  ─ each group heading is a link to its hub; leaves underneath
  YOUR GOVERNMENTS ▸        ELECTIONS ▸              MONEY ▸                COMMUNITY & HISTORY ▸   DATA ▸
  Places                    Calendar                 What counts as a budget Who lives here         All datasets
  County                    Results                  Your tax bill           Income & work           Pull it yourself
  Schools                   By the numbers           Budgets                 Housing & education     Sources index
  State · Your legislators  Close races (margins)    Campaign money          Research on voting
  Who holds office now      Turnout                                          History
  Who handles this?         Judges & ballot questions                         People in local history
  Map                       How elections work
                            Run for office
Learn ▾   7 paths (title + minutes) · For teachers
```

**Renames:**

| Today | Proposed |
|---|---|
| Reference | Topics |
| Context | Community & history |
| Paths + For teachers | Learn |
| community "People" | "Who lives here" (already its page title) |
| history/people | "People in local history" |
| Judges & questions | Judges & ballot questions |
| Elections by the numbers | keep the title; nav label "By the numbers"; dek names the 4 measures |
| Find your governments | Your place |

**Merges and splits, summarized:**
- Split landscape into an overview + margins + turnout; officeholders gets its own page; Up next merges into the calendar.
- Split elections/index into a hub + how-it-works.
- Merge the duplicate picker on your-governments into the home page; your-governments becomes the personalized result.
- Merge the shared run/* text into run/index.

All moved anchors are forwarded with the existing `moved.js` + `#moved-anchors` pattern, and pinned by a fixture test, as in the data/about split.

---

## 2. Shared patterns (build once, reuse), ranked by pages fixed

| Rank | Pattern | Pages it fixes | Build on | Effort |
|---|---|---|---|---|
| P1 | **"More about <entity>" rail.** A short row of links after "At a glance" (or under the hero) to the same entity on other topics: its campaign money page, its results in the explorer, how it voted on the map, budget/tax rate, community indicators, run-for-this-seat, calendar entry | ~62: 22 places, county, schools, legislators, 31 campaign area pages (back to the place), budgets panel, landscape leaves, officeholders | new `civic/related.py` `related_links(page, unit_id=None, office_id=None)` that reads only what exists (`campaign_entries`, `money_id_for`, `race_by_contest`, `tax_base`); renders as the existing `bodies_block`/link list. It never invents a page | S |
| P2 | **Template dedupe.** One explainer per page and per site; repeated rows collapse to one row per body | ~42: 13 township pages (§1/§2 repeat), 22 place pages (council rows), 7 run pages (85% shared) | `places.py`, `participate.py` | S |
| P3 | **"See all rows" fold.** When a chart or list already summarizes a table, the full table moves into a closed fold ("See all 163 rows · Copy CSV") with the same filters. JS-off: ships open, like `fold_section` | ~16: landscape leaves, calendar, tax-bill "Every unit's rate", budgets debt, map "every race" list, legislators results/money, judges retention, history mayors/party control, income-and-work employer lists, data/pull, how-it-works coverage | `fold_section()` (exists) + `data_table`. Pair with "Copy CSV copies only the rows shown" (the `rows-filtered` event pick_one already fires) | S |
| P4 | **Pick your area → show one.** A map (or chips for no-shape units) whose click opens that area's detail and folds the rest. Plus a **saved-place preselect**: when the reader has a saved place, the page opens on it with "Showing: Penn Township · Show all" | ~12: county, legislators, schools, budgets (all in flight), South Bend / Mishawaka / Walkerton council districts on their place pages, margins, calendar (government), tax bill (district), campaigns/county (race), results explorer (place by map) | **in flight:** `civic/pick_one.py`, `civic/district_map.py`, `static/js/pick_one.js`, `here.js` saved place. Add one helper: `preselect_from_here(key_map)` (JS reads `civic-place` ids, picks the matching key) | M (after map agent) |
| P5 | **One row per entity, expandable.** A compact list (name · 2–3 key facts · status badge) where each row is a `<details>` holding the full card or table. Replaces stacks of cards and per-item tables | ~9: history/people (32 cards), other-committees (33 tables), all-filings (grouped by committee), judges-and-questions (15 question blocks), your-governments office table, who-handles-this, run office picker, officeholders directory, margins "group by seat" | `one_fold` from pick_one (same markup contract) + `table_filter` words box for search | M (once), S per page |
| P6 | **Summary chart first, then drill-down.** Every big dataset opens with one chart that answers the main question and whose bars or rows link into the detail (filtered list or anchor) | ~7: margins, turnout, officeholders, landscape overview, calendar (seat counts per level per year), tax bill, debt | existing `hbar`, `columns`, the tax-bill stacked bar | S each |
| P7 | **Small multiples (share bars).** One 100% stacked bar per group (office level, year, unit) with counts in text, never colored by party | ~4: margins by level, calendar seats by level per year, budgets after map work, judges retention by year | new `charts.share_bars()` (additive, per README rule). Reuse the stacked-bar look of tax-bill §2 | M |
| P8 | **Hub-and-leaf split** (sub-page per idea) with an overview of summary cards | 3 now: landscape, elections/index, your-governments. Highest value per page | `moved.js` anchor forwarding, `sitemap.PATHS` updates, fixture test | M |
| P9 | **Sticky in-page nav.** On pages still over about 12 screens after the above: a compact sticky "On this page" bar (desktop) or select (phone), plus "Back to top" at each h2 | ~12 after the other fixes: county, schools, history, places (SB/Mishawaka), calendar, results, judges, legislators, campaigns/county, teach | `shell.py` + the existing `.toc` | S–M |
| P10 | **Deep links to one contest.** Results explorer `#contest-<id>` opens with that contest shown. Lets margins, places, county and officeholders link to "the full result" | margins, places, county, schools, legislators, officeholders | `elections.js` (`map.js` already does `#race-<id>`) | S |

Not recommended: tabs that hide content without a URL. Every view must keep an anchor, because path stops and citations land on anchors.

---

## 3. Page by page

Format for each page: purpose · readers' top questions · now (screens `1280 / 400`, tables) · **verdict** · proposal · what replaces big tables · where content goes · effort · dependencies.

### 3.1 Home and "your place"

#### `index.html`: Home
- **Purpose.** Start: pick a place, see the governments and seats that cover it, choose a way in.
- **Top questions.** (1) Which governments cover me? (2) How many people do I elect, and who? (3) What's on my next ballot?
- **Now.** 5.2 / 8.5 screens (local preview without the host skeleton); 0 tables; map + picker lists; seat diagram; next-ballot strip; 7 path cards; 117 sources folded.
- **Verdict: Keep.** It is the house pattern for "pick an area and the page answers": the map and the lists drive the same state, the seat diagram updates, and the choice is saved for every other page.
- **Small fixes.**
  - B3 (seat-diagram layout).
  - Make each layer title in the diagram a link to that government's page, if it isn't already.
  - At 400 px the picker is 3+ screens of radio buttons. Show the map first and fold the "Outside a city or town? Pick your township" list once a city is chosen.
- **Content moves.** None.
- **Effort.** S.
- **Dependencies.** None.

#### `your-governments/`: Find your governments
- **Purpose.** Everything that covers my place, with seats, what each office controls and how to reach each body.
- **Top questions.** (1) List my governments and my officials. (2) What does each office decide? (3) When and where do they meet?
- **Now.** 8.4 / 12.1 screens. The picker + seat diagram are the same as the home page (158 of 308 long paragraphs identical). Then "Links to each government" (fold list), a 25-row "What each office controls" table, and "How to contact or attend a meeting". 118 sources.
- **Verdict: Redesign** (becomes "Your place").
- **Proposal.**
  - Drop the duplicate picker. Show a compact "Showing: City of South Bend · Portage Township · SBCSC · [Change]" bar. With JS off or no saved place, show the place chooser as a list of links (same as the home page's no-JS list).
  - Then one card per government in layer order. Each card shows: your seats (holder name, party label as text, term end), "what it controls" (one line from the office table), where it meets and how to contact it, and links (P1 rail).
  - The 25-row office table becomes a one-row-per-office list (P5) inside each government card. The full table stays in a "See all rows" fold.

```
YOUR PLACE                                          [Change place]
Showing: City of South Bend · township not picked · South Bend Community School Corp.
┌ STATE OF INDIANA ──────────────────────────────────── you vote for 8 ┐
│ Governor & statewide (6) · Your legislators (2: depends on address) │
│ ▸ What these offices decide      ▸ How to reach them    More: State ›  │
└──────────────────────────────────────────────────────────────────────┘
┌ ST. JOSEPH COUNTY ─────────────────────────────────── you vote for 22 ┐
│ Commissioner (your district: pick on the district map ›)              │
│ Council (your district ›) · Row officers (9) · Judges (11)            │
│ ▸ What these offices decide  ▸ Meetings: Board of Commissioners, …    │
│ More: county page · campaign money · results · budget                 │
└──────────────────────────────────────────────────────────────────────┘
… city, school corporation, library (appointed) …
▸ See all rows: What each office controls (25)     [Copy CSV]
```

- **Where content goes.**
  - The picker is the home page's (`index.html#pick`).
  - The seat diagram stays on the home page. This page shows the same counts in each card header.
  - The links list goes into the card bodies.
  - The office table goes into card lines plus the see-all fold.
  - Meetings go into the card bodies; `#meetings` stays as an anchor (path stop).
  - `#find`, `#offices` and `#meetings` keep their ids (path stops).
- **Effort.** M.
- **Dependencies.** P1, P5, `here.js` saved place.

#### `who-handles-this/`: Who handles this?
- **Purpose.** Match an everyday service to the government and official responsible.
- **Top questions.** (1) Who fixes my road, trash, water? (2) Who do I call? (3) Does it differ if I'm in the city?
- **Now.** 5.5 / 8.4 screens; one 18-row × 5-column table (4.2 screens).
- **Verdict: Adjust.**
- **Proposal.**
  - A one-row-per-service list (P5): service name · who handles it · accountable official. Each row expands to the full text and contact.
  - Add a words box (`table_filter`).
  - Preselect from the saved place where the row varies (city vs township) (P4).
- **Replaces the table.** A searchable list; the table stays in a see-all fold. This helps learning because readers scan by service name, not by reading a 5-column grid.
- **Content moves.** All cells go into the rows or their expansions. Gaps and sources are unchanged.
- **Effort.** S.
- **Dependencies.** P5.

### 3.2 Places and maps

#### `places/index.html`: Places
- **Purpose.** All 22 cities, towns and townships, on a map and as cards.
- **Top questions.** (1) Which place am I in? (2) What kind of government is it? (3) Open its page.
- **Now.** 5.4 / 10.5 screens; map with cities/towns and townships tabs, panel that keeps the last area, 22 cards.
- **Verdict: Keep.** Map click → panel → open page is the house pattern.
- **Small.** Mark the saved place's card (`is-here`), as the calendar does.
- **Effort.** S.

#### `map/index.html`: Map: who governs where
- **Purpose.** The full boundary explorer plus "How areas voted" (precinct results 2020–2024).
- **Top questions.** (1) Who governs this spot? (2) How did this area vote in race X? (3) Where are the lines?
- **Now.** 6.0 / 6.6 screens; 4 layer tabs; panel; "All areas as a list" is 3.4 screens, including a 103-row "Every race on the map" table.
- **Verdict: Keep.** It is the model page.
- **Small.**
  - Move the 103-row race list into a see-all fold (P3).
  - Add the new district layers when the map agent's `district_shapes.json` sets are wired in.
- **Effort.** S.

#### Place pages (template): `places/<id>/`, 22 pages

- **Purpose.** One government: how it's organized, who holds office, party control, results, budget, context.
- **Top questions.**
  1. Who represents me here, and when are they up?
  2. What does this government do and spend?
  3. How did recent races go, and who funds them?
- **Now** (screens `1280 / 400`, tables):

| Page | Screens | Tables | Note |
|---|---|---|---|
| places/centre-township/ | 10.2 / 15.3 | 11 | |
| places/clay-township/ | 10.3 / 15.5 | 11 | |
| places/german-township/ | 10.0 / 14.8 | 11 | |
| places/greene-township/ | 9.6 / 14.3 | 11 | |
| places/harris-township/ | 10.3 / 15.2 | 11 | |
| places/liberty-township/ | 9.9 / 14.8 | 11 | |
| places/lincoln-township/ | 9.9 / 15.0 | 11 | |
| places/madison-township/ | 9.6 / 14.3 | 11 | |
| places/olive-township/ | 9.9 / 15.0 | 11 | |
| places/penn-township/ | 10.9 / 16.6 | 13 | elects an assessor too |
| places/portage-township/ | 10.1 / 15.5 | 11 | |
| places/union-township/ | 8.8 / 13.9 | 10 | |
| places/warren-township/ | 10.0 / 14.9 | 11 | |
| places/indian-village/ | 6.7 / 10.4 | 5 | |
| places/lakeville/ | 8.4 / 12.7 | 10 | |
| places/new-carlisle/ | 10.3 / 15.0 | 9 | |
| places/north-liberty/ | 8.9 / 13.6 | 8 | |
| places/osceola/ | 9.7 / 14.7 | 13 | |
| places/roseland/ | 11.0 / 16.5 | 10 | |
| places/walkerton/ | 10.5 / 17.3 | 14 | wards 1–4 (shapes exist: `walkerton-wards`) |
| places/south-bend/ | 13.3 / 21.0 | 20 | council districts 1–6 + at-large; mayoral 17-row table |
| places/mishawaka/ | 12.6 / 19.7 | 20 | council districts 1–6 + at-large |

  None of these is a giant-table page. The cost is repetition and order:
  - Townships repeat the "What townships do" text inside "How it's organized" (§1 and §2 open with the same paragraph). 38 long paragraphs are identical across all 13 township pages.
  - The two city pages list 7 near-identical "what it does" rows for council districts.
  - No place page links to its campaign-money page, its results, its map vote view or its tax rate.
- **Verdict: Adjust** (template).
- **Proposal.**
  1. **Order:** At a glance → **More about (P1 rail)** → Who holds office now → How it's organized → Recent results → Budget → Party control → Context → Gaps → Sources. "Who holds office" first answers question 1.
  2. **Dedupe:**
     - Townships: §1 "What townships do" keeps the explainer; §2 starts at "In Penn Township, the guide's data lists…".
     - Cities and towns: the organization table gets one row per body ("Common Council · 6 district seats + 3 at-large · 4 years · 2027"). The per-district rows move to the see-all fold.
  3. **District map (South Bend, Mishawaka, Walkerton):** `district_map` + `pick_one` over council districts/wards. Clicking a district opens that member's card and that district's last result; the others fold. The shapes are already in `district_shapes.json` (`south-bend-council-2022`, `mishawaka-council-2022`, `walkerton-wards`).
  4. **Recent results:** keep the `results_bars` cards, with a link per contest to the explorer (P10) and to `map/#race-<id>` when present.
  5. **South Bend mayoral history (17 rows):** keep the chart and fold the table (P3).
- **Big tables replaced.** Only the per-district organization rows (folded) and the mayoral table (folded under its chart).
- **Where content goes.** Nothing leaves the page. Repeated text is removed only where the same paragraph already appears above on the same page. Rows move into folds.
- **Effort.** S (template), M (district maps for the 3 pages).
- **Dependencies.** P1, P3, P10; the district maps depend on the map agent landing `district_map`.

### 3.3 County, schools, state

#### `county/`: County government
- **Purpose.** Commissioners, council, row officers, courts, appointed boards, party control, results, money.
- **Top questions.** (1) Who is my commissioner and council member? (2) What do the row officers do? (3) What does the county spend?
- **Now.** 23.4 / 42.1 screens; 36 tables. Biggest sections:

  | Section | Screens |
  |---|---|
  | Officeholders (33 sequential cards) | 5.1 |
  | Recent results (every county race as `results_bars`) | 3.9 |
  | Money in and out | 3.3 |
  | How it's organized | 2.8 |
  | Party control | 2.4 |
- **Verdict: Adjust** (after the map work, which adds the commissioner/council district map and a short list for countywide officers).
- **After the map work, also do:**
  - (a) Recent results: show the chosen district's commissioner/council result inside its pick_one fold. Countywide offices (auditor, sheriff…) go in a compact list with "full result" links (P10); the `results_bars` grid moves to a see-all fold.
  - (b) Add the P1 rail: campaign money (money/campaigns/county/, courts/), your legislators, schools, history party control, run for county council.
  - (c) Party control: keep both charts; their tables are already in "Show table"; link to history `#control`.
  - (d) Money in and out stays here (this is the county's own page). The budgets page links here instead of repeating it.
- **Where content goes.** Unchanged except the results grid (fold).
- **Effort.** S after the map.
- **Dependencies.** Map agent; P1, P10.

#### `schools/`: School corporations
- **Purpose.** Six corporations: boards, seats, members, enrollment, money, referenda, the SEA 287 label change.
- **Top questions.** (1) Which corporation and board seat is mine? (2) Who's on the board and when are they up? (3) What does it spend per student?
- **Now.** 32.6 / 51.6 screens; 32 tables; the corporation map exists; each corporation is 4.3–5.7 screens stacked.
- **Verdict: Adjust** (after the map work, which shows only the selected corporation).
- **After the map work, also do:**
  - (a) In each corporation, merge the "Board seats and how they are elected" table (up to 16 rows) with the member cards. One row per seat: seat · who votes · holder · term end. Each row expands to the card. The table goes into the see-all fold.
  - (b) Add the SBCSC board-district layer (`sbcsc-board`) and the PHM board layer (`phm-board`) to the map.
  - (c) P1 rail per corporation: campaign money (money/campaigns/sbcsc/, phm/, …), that corporation's referenda on judges-and-questions, results, run for school board.
  - (d) Keep the "Corporations at a glance" comparison: it is the summary-first view.
- **Effort.** S–M after the map.
- **Dependencies.** Map agent; P1, P5.

#### `state/`: State government
- **Purpose.** Statewide offices, governors since 1945, General Assembly, party control, how a bill becomes law.
- **Top questions.** (1) Who are the statewide officials? (2) Which party controls the legislature? (3) How does a bill pass?
- **Now.** 8.0 / 11.1 screens; 5 tables (governors 17 rows).
- **Verdict: Keep.**
- **Small.**
  - Fold the governors table under a timeline-style list, or keep it as is.
  - Add a link to your-legislators near the top.
- **Effort.** S.

#### `state/your-legislators/`: Your legislators
- **Purpose.** Which Indiana House and Senate districts include part of the county, who holds them, results, campaign money.
- **Top questions.** (1) Which district am I in, and who represents me? (2) How did the last race go? (3) Who funds them?
- **Now.** 17.4 / 23.9 screens; 20 tables. Results 2012–2026 take 9.5 screens; campaign money is a 101-row table (2.5 screens).
- **Verdict: Adjust** (after the map work, which adds the House/Senate district map).
- **After the map work, also do:**
  - (a) Results: per-district fold (pick_one). The selected district shows its results 2012–2026 as one `results_bars` card per election, with the "county portion" note kept on every card.
  - (b) Campaign money: show the selected district's committees as summary rows, plus a link to money/campaigns/state-legislature/ (the same data, already one page). The 101-row table goes into a see-all fold.
  - (c) The extent table (9 rows) stays: it is the "county portion" caveat in table form.
- **Effort.** S after the map.
- **Dependencies.** Map agent; P3.

#### `state/how-the-state-shapes-local/`: How the state shapes local government
- **Purpose.** Home rule, tax caps, levy limits, SEA 1, HEA 1210, consolidation.
- **Top questions.** (1) What can local governments decide? (2) What changed in 2025–2026? (3) When does it take effect?
- **Now.** 7.9 / 11.4 screens; 9 short sections, 4 small tables.
- **Verdict: Keep.** A good explainer.
- **Effort.** None.

#### NEW `officeholders/`: Who holds office now (from the landscape split)
- **Purpose.** Every current elected officeholder in one place, and how each first took office.
- **Top questions.** (1) Who holds every seat? (2) How many came in by caucus or appointment, not by election? (3) Who are mine?
- **Proposal.**

```
WHO HOLDS OFFICE NOW                                   as of Nov 7, 2026
[hbar] How current officeholders first took office      COMPUTED
  Election ██████████████████ n   Caucus ███ n   Appointment █ n   Not stated █ n
  (each bar links to the list filtered to that value)
Why this matters: vacancies are filled by party caucus → How vacancies are filled ›
─────────────────────────────────────────────────────────────────────────────
Filter: [Level ▾] [Government ▾] [First took office by ▾] [words…]   163 of 163 shown
[Showing your place only ▸ Show all]           (preselect from the saved place, P4)
▾ St. Joseph County (32)
   Commissioner, District 1 · Carl Baxmeyer · Republican (R) · since Jan 1, 2023 · first by: election  OFFICIAL ¹
   …
▸ City of South Bend (11)  ▸ Penn Township (5) …
▸ See all rows (163) · Copy CSV
```

- **Where content comes from.** Landscape `#how-took-office`: intro text, `took-office` hbar, filter, the `took-office-list` table, and the "first_selected_by" note, all verbatim. The list is grouped by government (same order as `_place_order`). Each person links to their unit page card.
- **Effort.** S–M.
- **Dependencies.** P5, P6; anchors forwarded from landscape.

### 3.4 Elections

#### `elections/index.html`: How Indiana elections work
- **Purpose.** An explainer: offices and cycles, primaries, general election, straight-ticket, voting rules, county specifics, vacancies, SEA 287, no initiative or recall, candidate info.
- **Top questions.** (1) How do I vote, and what ID do I need? (2) Which offices are elected when? (3) How do vacancies get filled?
- **Now.** 11.5 / 18.0 screens; 5 tables (offices 27 rows); 9 sections.
- **Verdict: Split** (hub + explainer).
- **Proposal.**
  - `elections/index.html` becomes the **Elections hub**:
    - the next-ballot strip, reused from the home page;
    - cards for Calendar, Results, By the numbers, Close races, Turnout, Judges & ballot questions, How elections work, Run for office;
    - one live fact per card (for example "2026 general: unofficial until certified").
  - The explainer moves verbatim to `elections/how-it-works/` (the naming matches money/campaigns/how-it-works/). All 9 section anchors are forwarded with `moved.js`. The path stop `elections/index.html#candidate-info` is repointed in `PATHS`.

```
ELECTIONS                                           NEXT ON YOUR BALLOT  2027 · Primary May 4 · General Nov 2
┌ Calendar ──────────┐ ┌ Results ────────────┐ ┌ By the numbers ─────┐ ┌ Close races ───────┐
│ What's on each      │ │ Every race 2010–2026│ │ Turnout, margins,   │ │ 353 contested races │
│ ballot 2026–2030    │ │ by year and place   │ │ who holds office    │ │ 111 under 5 points  │
└─────────────────────┘ └─────────────────────┘ └─────────────────────┘ └─────────────────────┘
┌ Turnout ───────────┐ ┌ Judges & ballot q. ─┐ ┌ How elections work ─┐ ┌ Run for office ─────┐
└─────────────────────┘ └─────────────────────┘ └─────────────────────┘ └─────────────────────┘
```

- **Effort.** M (moved anchors, test fixture).
- **Dependencies.** P8; nav change (Q1).

#### `elections/calendar/`: Election calendar
- **Purpose.** What is on the ballot each year 2026–2030, deadlines, every seat by year.
- **Top questions.** (1) What's on my next ballot? (2) When are the deadlines? (3) When is seat X next up, and who holds it?
- **Now.** 21.3 / 28.6 screens:

  | Section | Screens |
  |---|---|
  | Year cards (good) | 0.8 |
  | Next ballot cards | 1.4 |
  | Deadlines | 0.9 |
  | "Every seat, by year" (188 rows × 7 columns; filter exists, unfiltered by default) | 16.1 |

  B2 contrast bug.
- **Verdict: Merge** (absorbs landscape "Up next") + Adjust.
- **Proposal.**
  - "Every seat, by year" becomes **year tabs that are anchors**: `#year-2027`, … The year cards at the top link to them; with JS off all years show.
  - Inside a year, seats are listed by government (P5 rows): seat · holder now · party label · since · first took office by · term-limit status. These are Up next's columns, now for every year.
  - The saved place preselects its government ("Showing your place · Show all").
  - The 188-row table stays in a see-all fold, with the filter and Copy CSV.
  - Up next's term-limit rule paragraph (`_rule_p county_row_office_term_limits`) and its computed-status note move to "How this is computed".

```
§4 EVERY SEAT, BY YEAR
[2026] [2027] [2028] [2029] [2030]        (anchors; JS shows one year)
2027 · Municipal primary May 4 · General Nov 2 · 46 seats              Showing: your place ▸ all
▾ City of South Bend (9 seats)
   Mayor · James Mueller · Democrat (D) · since 2020 · first by election · term limit: none in data   OFFICIAL
   Council District 1 · Canneth Lee · … · first by party caucus                                         OFFICIAL
▸ City of Mishawaka (9)   ▸ Town of Walkerton (6) …
▸ See all rows (188) · Copy CSV
```

- **What replaces the table, and why it helps.** Readers ask about one year and one government; grouping answers that in one screen. Adding the holder turns a schedule into "who you would be voting on".
- **Where content goes.**
  - All 188 rows go into the year lists + the fold.
  - Up next's 71 rows are the 2027–2028 subset, with every column kept.
  - Its intro and notes go to "How this is computed".
  - `#up-next` and `#up-next-table` are forwarded from landscape to `calendar/#year-2027`.
- **Effort.** M.
- **Dependencies.** P3, P4 (saved place), P5; landscape split.

#### `elections/results/`: Election results
- **Purpose.** An explorer of every contest 2010–2026 by year, election, office group and place.
- **Top questions.** (1) Who won race X? (2) How did my place vote? (3) Was it official?
- **Now.** 10.1 / 20.2 screens; a JS explorer (285 KB blob) with "show more"; a "Turnout first" 28-row table (1.7 screens) duplicates landscape turnout.
- **Verdict: Adjust.**
- **Proposal.**
  - (a) Replace the turnout table with one sentence + the general-election turnout chart + a link to `elections/turnout/`. Keep `#turnout` as an anchor (path stop "Results history, turnout first").
  - (b) Per-contest deep link `#contest-<id>` (P10).
  - (c) A "Place" option set to the saved place on load (P4).
  - (d) Later: districts as a place type once district shapes are wired (contest names already parse into districts on landscape).
- **Effort.** S–M.
- **Dependencies.** P10; turnout page.

#### `elections/judges-and-questions/`: Judges and public questions
- **Purpose.** Retention votes (Superior Court, state courts, county portion) and public questions; school-board labels.
- **Top questions.** (1) How did the judges on my ballot fare? (2) What did the question say, and how did it go? (3) Which questions applied to me?
- **Now.** 14.3 / 18.7 screens; 17 tables. Retention chart + 18-row and 36-row tables; "Public questions" is 7.5 screens: 15 stacked blocks, each with full wording + result bar.
- **Verdict: Adjust.**
- **Proposal.**
  - Public questions become a one-row-per-question list (P5), grouped by jurisdiction (Statewide, Mishawaka, SBCSC, New Prairie…) then year. Each row shows: date · jurisdiction · short label · yes % / no % as text · status badge. The row expands to the full verbatim wording + the existing bar figure.
  - Retention: keep the chart; fold both tables (P3).
  - Preselect the saved place's jurisdictions (P4).
- **Content moves.** None leaves the page.
- **Effort.** S–M.
- **Dependencies.** P5. Sequence after the landscape batch (same module).

#### `elections/landscape/`: Elections by the numbers (deep dive)

**Purpose.** The same measures for every race: turnout with its base, margins, the seats on the next ballots, how incumbents took office, straight-party share. Looking back only.

**Top questions by persona.**

| Persona | Questions |
|---|---|
| Resident | Was my race close? Do people vote in odd years? Who's up next where I live? |
| Student/teacher | Why is odd-year turnout lower? How often are local races uncontested? What's a caucus appointment? |
| Journalist | Closest races ever, by office; filter and copy the rows |
| Would-be candidate | Has this seat been close before? Is the incumbent term-limited? |

**Now.** 66.0 / 90.7 screens; 14 tables, 680 rows.

| Section | Screens at 1280 | What's in it |
|---|---|---|
| Turnout | 2.6 | 2 column charts (good) + a 28-row denominators table, always open |
| **Margins in every race** | **38.9** | Definitions callout, a count paragraph, a band hbar (3 bars), 7 filters + words + sort, and **one 354-row × 8-column table** ("Margins in every race decided inside the county, closest first"), each row 2–4 lines tall |
| Up next | 6.6 | Rule paragraph, filter, a 72-row table |
| How incumbents took office | 13.2 | hbar + filter + a 164-row table |
| Straight-party share | 2.6 | 2 small tables |
| Rules / Gaps / Sources | folded | |

What the margins table hides (computed from the built rows today):

| Fact | Count |
|---|---|
| Contested races, 2010–2026 | 353: 248 general, 105 primary |
| Uncontested (no more candidates than seats) | **599**, stated only in one sentence |
| Not measurable (votes missing or seat count unknown) | 29 |
| Under 5 / 5–15 / over 15 points | 111 / 90 / 152 |

| Office group | Contested | Under 5 | 5–15 | Over 15 |
|---|---|---|---|---|
| Township offices | 93 | 45 | 22 | 26 |
| City offices | 78 | 15 | 16 | 47 |
| School boards | 44 | 9 | 11 | 24 |
| County council | 39 | 8 | 7 | 24 |
| County row offices | 38 | 11 | 18 | 9 |
| Town offices | 21 | 7 | 8 | 6 |
| County commissioners | 20 | 9 | 3 | 8 |
| State legislature (district wholly in county) | 15 | 5 | 3 | 7 |
| County courts | 5 | 2 | 2 | 1 |

A reader can't see any of this pattern in a 354-row list sorted by margin. The table answers "find a row", not "what's going on".

**Verdict: Split.** Landscape becomes a short **overview** ("By the numbers"), and each measure gets its own page. The overview is the learning-first entry for path 6; the leaves are where people browse.

**Overview wireframe (`elections/landscape/`, about 4 screens):**

```
ELECTIONS BY THE NUMBERS
The same measures for every race and every party, looking back only.
┌ TURNOUT ─────────────────────────────┐  ┌ HOW CLOSE WERE THE RACES? ────────────┐
│ [columns: general-election turnout]   │  │ [share bar] 599 uncontested · 353      │
│ Even years 29–56%, odd years 14–21%   │  │ contested: 111 <5 pts · 90 · 152      │
│ Odd years: only city and town voters  │  │ Closest: Walkerton Ward 4 (R primary)  │
│ Turnout and the denominator ›         │  │ 2023, 0 votes apart ›  All races ›     │
└───────────────────────────────────────┘  └────────────────────────────────────────┘
┌ WHO HOLDS OFFICE NOW ────────────────┐  ┌ UP NEXT ───────────────────────────────┐
│ [hbar] first took office by:          │  │ 2027: 46 city and town seats            │
│ election · caucus · appointment       │  │ 2028: county, schools, legislature      │
│ Every officeholder ›                  │  │ Every seat and who holds it now ›       │
└───────────────────────────────────────┘  └────────────────────────────────────────┘
What this page does not do (verbatim list, + link to the vote map: B5)   Gaps ▸  Sources ▸
```

(The turnout ranges in the wireframe are illustrative only; the real numbers come from `elections.csv` with the existing citation and the COMPUTED badge.)

**NEW `elections/margins/`: "Margins: how close each race was".** This is the page Nick singled out.

Design goals:
- Answer "how close are local races?" in the first screen.
- Let a reader find *their* races by clicking the map (house pattern).
- Show "has this seat been close before?" for each seat.
- Keep all 353 rows, with Copy CSV, as a secondary view.

```
MARGINS: HOW CLOSE EACH RACE WAS                                     COUNTY · 2010–2026
Margin in points = votes of the last candidate inside the seats minus the next candidate,
divided by all votes in the contest.  [How the margin is measured ▸] (the callout, verbatim)

§1 THE SHORT ANSWER
 ┌──────────────┬──────────────┬──────────────┬──────────────┐
 │ 981 candidate│ 599 had no   │ 353 were     │ 29 can't be  │   (each tile cites; COMPUTED)
 │ races decided│ contest      │ contested    │ measured     │
 │ in the county│              │              │              │
 └──────────────┴──────────────┴──────────────┴──────────────┘
 (981 = 353 + 599 + 29: the same scope rules as today: no statewide offices, no legislative districts in
  years they crossed the county line, no questions, retention or straight-party lines)
 [share bar] uncontested ▓▓▓▓▓▓▓▓▓▓▓▓ | <5 pts ▒▒▒ | 5–15 ░░ | >15 ▓▓▓▓       (accent and ink only,
 Bands describe past results and say nothing about future races.             never party colors)

§2 BY LEVEL OF GOVERNMENT                       (small multiples: one share bar per office group)
 Township offices   93 contested ·  ▒▒▒▒▒▒▒▒▒░░░░▓▓▓▓▓   45 under 5 · 22 · 26   [see these ›]
 City offices       78 contested ·  ▒▒▒░░░▓▓▓▓▓▓▓▓▓▓▓   15 · 16 · 47          [see these ›]
 School boards      44 contested ·  ▒▒░░░▓▓▓▓▓▓▓▓▓      9 · 11 · 24           [see these ›]
 … 9 rows, fixed order (county → city/town → township → school → legislature), never by value
 + "uncontested" count per group, so a share is never shown without its base

§3 FIND A RACE
 [Townships] [Cities & towns] [School corps] [County districts] [City council districts] [Legislature]
 ┌──────────────── map (district_map, neutral fills) ───────┐ ┌ panel (keeps last area) ──────┐
 │  click an area → list below shows only its races          │ │ Clay Township                  │
 │                                                            │ │ 11 contested since 2010        │
 │                                                            │ │ 5 under 5 points               │
 │                                                            │ │ Closest: Township Board 2018,  │
 └────────────────────────────────────────────────────────────┘ │ 46 votes apart                 │
 Countywide offices (no sub-area): [County row offices] [Courts]   │ Show these races ›             │
                                                                   └────────────────────────────────┘
 Filter: [Year ▾][Election ▾][Band ▾][Office ▾][Place ▾][District ▾][words…]  Sort: [Closest ▾]
 View:  (•) Races  ( ) By seat                                     353 of 353 races shown  [Reset]

 RACES view (one row per race; 25 at a time, [Show 25 more]; JS-off: all rows)
 ┌──────────────────────────────────────────────────────────────────────────────────────────┐
 │ 0.17 pts · 46 votes   Clay Township: Township Board · 3 seats      Nov 6, 2018 general   │
 │ ▏▌ (margin tick on a 0–100 scale, band shading behind)                         OFFICIAL ³│
 │ Last inside the seats: Sandra J. Robbins (R) 4,280 · Next: Jennica S. Liberatore (D) 4,234│
 │ Full result ›   How areas voted ›  (only when on the vote map)                            │
 └──────────────────────────────────────────────────────────────────────────────────────────┘

 BY SEAT view (one row per office; expandable)
 ▸ Clay Township Trustee        2010 ● 2014 ● 2018 ● 2022 ●   (dots on a 0–30+ pt strip; text list in
                                                               the expansion: year · margin · names)
 ▸ County Council District A    …

§4 ALL ROWS                   ▸ See all 353 races as a table · Copy CSV (copies the rows shown)
§5 What this page does not do · Party codes · Gaps ▸ · Sources ▸
```

How it meets the rules:
- **Nonpartisan.**
  - Names and parties stay as text, as today.
  - No red/blue: bars use accent/ink like every non-results chart.
  - Groups and seats in fixed office order, never by value; races sorted by margin or date only, as today.
  - "No party filter" is kept: the filters are exactly today's (year, election, band, office, place, district, words). The words box still strips the "(Democratic primary)" tail.
  - No adjectives: "under 5 points", not "nail-biter" or "competitive".
- **Sourcing.**
  - Every row keeps its status badge and low-confidence badge.
  - The section-level canvass citation is kept.
  - The tiles carry the COMPUTED badge with "Margins computed from results.csv vote counts."
- **Accessible.**
  - Rows are `<li>` with text, not visual-only marks; the margin tick is `aria-hidden` (the number is in the text).
  - Filter bar = `table_filter` (labelled, aria-live count).
  - The map is the existing `district_map`: every area is an `<a href="#area-…">`; a plain "Areas" list with counts sits under the map for keyboard and JS-off readers.
  - "Show 25 more" is a button and focus moves to the first new row.
  - At 400 px each row stacks into 3 lines; no 60rem table min-width.
- **JS-off.** All 353 rows render as the list; the map links jump to the area list; the see-all table ships open (fold pattern).
- **Data needed (all in hand).**
  - `classify()` → office group + place.
  - `_district_of()` → district.
  - A key per race for pick_one: place unit id, district set item, or "countywide".
  - `contests_for_office` for the by-seat view.
  - `race_by_contest` for map links.
  - The uncontested count per office group: a new tally in the same loop, since today only the total `n_unc` is kept.

What replaces the 354-row table, and why it helps learning:
- §1 and §2 show the pattern (most races uncontested; township races are close more often) that the table hides.
- §3 turns "find my race" into a click instead of a scroll.
- The by-seat view answers the candidate's question directly.
- The table survives, unchanged, as §4 for researchers.

**NEW `elections/turnout/`: "Turnout and how ballots were cast".**

```
TURNOUT: ODD VS EVEN YEARS
Turnout = ballots cast ÷ registered voters. In odd years only city and town residents vote, so the base
is smaller (ranges sentence, verbatim, with citations + COMPUTED).
[columns: general + municipal general]   [columns: primaries + specials]      (existing charts)
Key: M = odd-year municipal, S = special, * = unofficial.  Gray columns are on a smaller base.
▸ See all rows: Turnout with its denominator (28) · Copy CSV       (was always open; now a fold)
§ STRAIGHT-PARTY BALLOTS   (moved verbatim from landscape; years limited to sourced rules)
Gaps ▸ Sources ▸
```

**Where every landscape piece goes:**

| Today (landscape) | Goes to |
|---|---|
| Hero dek + scope | Overview (kept) |
| Turnout text, 2 charts, denominators table | `elections/turnout/` (table in a see-all fold) |
| Margins definitions callout `#bands` | `elections/margins/` (callout verbatim; `#bands` kept there) |
| Margins count paragraph (353 / uncontested / not computable / left-out rules) | Margins §1 tiles + the paragraph, verbatim, under the tiles |
| Band hbar `#margin-bands` | Margins §1 (as a share bar incl. uncontested) + the original hbar kept in "Show table" form |
| Filters + `margins-table` (354 rows) | Margins §3 list + §4 table (same ids `margins-table`, `margins-table-copy`) |
| Canvass citation line, party-codes line | Margins §3 / §5 |
| Up next (rule paragraph, filter, 72-row table, note) | `elections/calendar/` (year lists + fold; rule → "How this is computed") |
| How incumbents took office (intro, hbar, filter, 164-row table) | `officeholders/` |
| Straight-party share (2 blocks + note) | `elections/turnout/` |
| "What this page does not do" | Overview (full list) + each leaf repeats the bullets that apply |
| Gaps (8) | Each leaf `finish()` with its own pattern; overview keeps the union |
| Sources (98) | Follow the citations automatically |

Anchors: `#turnout`, `#margins`, `#bands`, `#margins-table`, `#up-next`, `#up-next-table`, `#how-took-office`, `#took-office`, `#took-office-list`, `#straight-party`, `#turnout-general`, `#turnout-primary` go into the `#moved-anchors` map. The overview keeps `#turnout`, `#margins`, `#up-next` and `#how-took-office` as its own card ids, so old links still land on the right summary card even with JS off. Path 6 stops are repointed to the leaves. A test like `test_every_old_anchor_still_resolves` pins them.

**Effort.**

| Page | Effort |
|---|---|
| Overview | S |
| Turnout | S |
| Officeholders | S–M |
| Margins | M–L (map, list, by-seat view, share bars) |

**Dependencies.** P3, P4 (`district_map`, `pick_one`), P5, P6, P7, P10; sitemap/PATHS edits; `moved.js`.

#### Run pages

##### `run/index.html`: Run for office
- **Purpose.** Which offices you could run for, eligibility, ballot access, campaign finance, vacancies, contacts.
- **Top questions.** (1) Which office fits me, and when is it next up? (2) How do I get on the ballot? (3) What do I have to report?
- **Now.** 5.3 / 7.9 screens; a 7-row "Pick an office" table.
- **Verdict: Adjust.**
- **Proposal.**
  - Turn "Pick an office" into 7 cards (title · seats in the county · term · next election · link), using the existing card component.
  - This page becomes the **single home** of the shared steps that the office pages now repeat.
  - Add "Which seat is mine?" with links to the district maps (county council, city council, school board) once they exist.
- **Effort.** S.
- **Dependencies.** Run-page dedupe; district maps.

##### Office pages, 6 pages: `run/<office>/`

| Page | Screens | Long paragraphs | Identical to run/index |
|---|---|---|---|
| run/township-trustee/ | 5.7 / 8.0 | 52 | 45 |
| run/township-board/ | 5.7 / 8.1 | 53 | 44 |
| run/school-board/ | 5.5 / 8.0 | 54 | 45 |
| run/city-council/ | 5.2 / 7.5 | 52 | 45 |
| run/county-council/ | 5.3 / 7.7 | 55 | 45 |
| run/precinct-committeeperson/ | 3.4 / 5.0 | 34 | 25 |

- **Purpose.** Rules, forms, deadlines and the next election for one office.
- **Verdict: Merge** (shared text into run/index; each URL stays as a short office page).
- **Proposal.**
  - Each office page keeps only what is specific to it: what it does, seats-by-government table, term, next election, eligibility lines specific to the office, where to file locally.
  - The shared sections (ballot access, campaign-finance duties, vacancies) become one-line summaries linking to `run/index.html#ballot-access` etc. Their anchors stay on the office pages so the old links work.
  - Add "Which seat would I run for?" linking to the right district map, and a P1 rail: current holders (officeholders filtered), last margins (margins filtered), campaign money for that office.
  - For precinct committeeperson, add a link to the map's precinct layer.
- **Where content goes.** Every shared paragraph already exists verbatim on run/index (measured). Nothing is lost.
- **Effort.** S.
- **Dependencies.** P1.

### 3.5 Money

#### `money/index.html`: Money (hub)
- **Purpose.** Hub: headline figures and the money pages.
- **Top questions.** (1) How big are the budgets? (2) Where do I start? (3) What's my tax rate?
- **Now.** 2.4 / 4.7 screens; 10 headline tiles; 0 in-content inbound links.
- **Verdict: Keep.** The model for the other hubs.
- **Small.**
  - Make it the "Money" heading link in the Topics menu.
  - Add the campaigns map as a tile.
- **Effort.** S.

#### `money/what-is-a-budget/`: What counts as a budget
- **Purpose.** Explains bases (general fund, all funds, certified), series breaks, nominal vs constant dollars.
- **Top questions.** (1) Why do totals differ ($90M vs $136M vs $248M)? (2) Which number should I quote? (3) What is a series break?
- **Now.** 6.6 / 9.7 screens; 3 small tables.
- **Verdict: Keep.** A good primer.
- **Effort.** None.

#### `money/your-tax-bill/`: Your tax bill
- **Purpose.** One district's certified rate, how it is shared among units, every unit's rate, caps and credits.
- **Top questions.** (1) What's my rate? (2) Who gets my tax dollars? (3) How do caps work?
- **Now.** 11.9 / 14.2 screens; a 36-option "taxing district" select (codes like "026 South Bend - Portage"); "Every unit's rate" 8.1 screens (chart + 4 tables of 32–38 rows); 50 gaps (folded).
- **Verdict: Adjust.**
- **Proposal.**
  - (a) **Preselect from the saved place.** District names are city/town + township (+ school in 2 cases: 022, 032), so the saved place usually maps to 1 district, at most 2 (Mishawaka has 005, 022, 023, 036; Penn has 031, 032). Show "From your saved place: 026 South Bend - Portage (or pick another)". No address matching is claimed.
  - (b) Keep the stacked "How the rate is shared" bar: it is the best learning graphic in the money section.
  - (c) "Every unit's rate": keep the chart; the 4 tables go into see-all folds (P3).
  - (d) Later (M–L): a taxing-district map built as intersections of the township, city/town and school-corporation layers the guide already has. This needs a source check against the DLGF district list before drawing anything (the guide never draws boundaries itself; see Q6).
- **Effort.** S (a–c).
- **Dependencies.** P3, P4.

#### `money/budgets/`: Budgets by unit
- **Purpose.** Spending per resident map, budgets over time, comparison, 2024 spending/revenue, debt, tax base, libraries and special units.
- **Top questions.** (1) How much does my government spend, and on what? (2) Is it growing? (3) How much does it owe?
- **Now.** 79.1 / 104.5 screens; 151 tables:

  | Section | Screens |
  |---|---|
  | Map | 4.8 |
  | Over time (79 series) | 26.1 |
  | Per resident | 1.8 |
  | 2024 spending and revenue | 10.9 |
  | Debt | 13.9 |
  | Tax base | 3.7 |
  | Libraries & special units | 16.0 |
- **Verdict: Adjust** (after the map work, which shows one selected unit's history and debt below the map).
- **After the map work, also do:**
  - (a) "2024 spending and revenue: county, South Bend, Mishawaka" duplicates the county page `#money` and the place pages' Budget sections (same `money_in_out` helper). Show it only for the selected unit and link to the unit's page for the full flows.
  - (b) Libraries and special units (no boundary) go in the same pick list as chips beside the map, not a separate 16-screen section.
  - (c) The debt summary chart stays as the summary-first view; the 106-row table goes into a see-all fold.
  - (d) Keep "Comparing units: 2026 per resident" as the one cross-unit chart.
- **Effort.** S after the map.
- **Dependencies.** Map agent; P3.

#### Campaign finance

##### `money/campaigns/index.html`: Campaign money in local races
- **Purpose.** A map by place and race type, then each government's page.
- **Top questions.** (1) How much was spent in my races? (2) Who raised what? (3) How complete are the reports?
- **Now.** 7.3 / 10.1 screens; race-type filter; district shapes; panel; "Every area" list.
- **Verdict: Keep.** It is the newest example of the house pattern.
- **Small.** B4 (default layer).
- **Effort.** S.

##### `money/campaigns/how-it-works/`: How campaign finance reporting works
- **Purpose.** Reporting rules, what's public, how the guide reads and adds up forms, how complete the record is, delinquent filers.
- **Top questions.** (1) What must a committee report? (2) Can I trust these totals? (3) Which reports are missing?
- **Now.** 41.4 / 47.8 screens, of which 32.9 is "How complete the record is". That section is mostly bug B1 (a 98-row coverage grid whose cells stack in one column).
- **Verdict: Adjust.**
- **Proposal.**
  - Fix B1. That alone should bring the page to about 10 screens.
  - Then fold the coverage grid by office group (County / Township / City / Town / School) with the "Filings by election cycle" 3-row table as the summary.
- **Effort.** S.
- **Dependencies.** None (B1 is a CSS-only fix).

##### `money/campaigns/all-filings/`: Every local campaign filing
- **Purpose.** The researcher's view: all 479 filings with filters.
- **Top questions.** (1) Show me every report for committee X. (2) Filter by cycle and office. (3) Copy the rows.
- **Now.** 67.9 / 97.5 screens; one long grouped table (by office → committee), filters for cycle, office group, committee, order; a 37-row large-contributions table.
- **Verdict: Adjust.** It is meant to be the see-all page, so the table stays.
- **Proposal.**
  - Group by committee as one row per committee (P5): committee · candidate · party as written · reports on file · last cash on hand · status mix. Each row expands to its reports table.
  - Default: all collapsed (JS); with JS off all open.
  - Filters unchanged; "Copy CSV" copies all rows shown.
- **Effort.** S–M.
- **Dependencies.** P5; Copy CSV of shown rows.

##### `money/campaigns/other-committees/`: Party, PAC and other committees
- **Purpose.** Committees backing no single candidate, and forms with no office.
- **Top questions.** (1) Which PACs and party committees spend locally? (2) How much? (3) Which forms are unclear?
- **Now.** 21.9 / 25.0 screens; 33 open report tables, one per committee, each followed by transcription notes.
- **Verdict: Adjust.**
- **Proposal.** One row per committee (P5): name · cycle totals line (already written as a sentence) · reports on file · status. Each row expands to the table + notes. All 4 sections remain.
- **Effort.** S.
- **Dependencies.** P5.

##### Campaign area pages (template), 31 pages: `money/campaigns/<area>/`

- **Purpose.** One government's races: candidates in ballot order, whole-campaign figures, reports, same-period comparison, large contributions.
- **Top questions.** (1) How much did each candidate in my race raise and spend? (2) Is the record complete? (3) Who gave large amounts?
- **Now** (`1280 / 400` screens, tables):

| Page | Screens | Tables | Page | Screens | Tables |
|---|---|---|---|---|---|
| money/campaigns/county/ | 32.6 / 41.9 | 166 | money/campaigns/courts/ | 4.2 / 6.1 | 10 |
| money/campaigns/state-legislature/ | 8.4 / 12.7 | 9 | money/campaigns/south-bend/ | 9.5 / 12.5 | 47 |
| money/campaigns/mishawaka/ | 9.5 / 12.2 | 57 | money/campaigns/indian-village/ | 1.6 / 2.3 | 0 |
| money/campaigns/lakeville/ | 1.6 / 2.2 | 0 | money/campaigns/new-carlisle/ | 4.4 / 6.4 | 6 |
| money/campaigns/north-liberty/ | 4.2 / 6.1 | 6 | money/campaigns/osceola/ | 3.0 / 4.3 | 2 |
| money/campaigns/roseland/ | 5.6 / 8.1 | 7 | money/campaigns/walkerton/ | 8.2 / 11.4 | 22 |
| money/campaigns/centre-township/ | 5.0 / 7.2 | 5 | money/campaigns/clay-township/ | 5.9 / 8.2 | 7 |
| money/campaigns/german-township/ | 5.4 / 7.6 | 7 | money/campaigns/greene-township/ | 4.2 / 6.1 | 4 |
| money/campaigns/harris-township/ | 6.4 / 8.8 | 10 | money/campaigns/liberty-township/ | 4.0 / 6.0 | 3 |
| money/campaigns/lincoln-township/ | 4.0 / 5.9 | 3 | money/campaigns/madison-township/ | 3.8 / n/m | 2 |
| money/campaigns/olive-township/ | 4.7 / 6.7 | 6 | money/campaigns/penn-township/ | 7.1 / 9.8 | 21 |
| money/campaigns/portage-township/ | 5.0 / 7.0 | 10 | money/campaigns/union-township/ | 4.1 / 6.1 | 3 |
| money/campaigns/warren-township/ | 6.3 / 8.6 | 9 | money/campaigns/john-glenn/ | 6.2 / 8.6 | 6 |
| money/campaigns/new-prairie/ | 5.8 / 8.2 | 5 | money/campaigns/phm/ | 9.3 / 13.0 | 23 |
| money/campaigns/sbcsc/ | 9.5 / 13.0 | 17 | money/campaigns/school-city-mishawaka/ | 4.4 / 6.4 | 3 |
| money/campaigns/union-north/ | 6.1 / 8.5 | 5 | | | |

  The race card works: an all-candidates line with a COMPUTED badge, an "Incomplete" floor note, a small whole-campaign table, and reports in `<details>`.
- **Verdict: Keep** for 30 pages (just rebuilt; most are 2–10 screens). **Adjust** for `money/campaigns/county/`.
- **Template additions (S).**
  - A race index of chips under the hero ("Clerk · Assessor · Auditor · …"), anchors only.
  - Fold "Same report, same period".
  - P1 rail back to the place page, its results and its run page. Today these pages have 1 inbound link each, so add links from the place, county and schools pages.
- **county/ (Adjust).** 11 races in 2026 + 2024 races at 32.6 screens. Add a race picker (pick_one over races, keyed by office), so the reader opens one race at a time. With JS off all are open.
- **Effort.** S.
- **Dependencies.** P1, `pick_one`.

### 3.6 Community and history

#### `community/index.html`: The community
- **Purpose.** County vs Indiana and U.S., links to the 3 indicator pages, what the indicators mean.
- **Top questions.** (1) How does the county compare? (2) Where do I find population, income, housing? (3) How reliable are these numbers?
- **Now.** 4.6 / 7.7 screens; 6 small tables.
- **Verdict: Keep.**
- **Effort.** None.

#### `community/people/`: Who lives here
- **Now.** 11.3 / 14.7 screens; "shade by" indicator map; population charts.
- **Top questions.** (1) Is the population growing? (2) Age, race and households where I live? (3) How do townships compare?
- **Verdict: Keep.** House pattern (shade-by map).
- **Small.** Preselect the saved place on the map.
- **Effort.** S.

#### `community/income-and-work/`: Income and work
- **Now.** 13.1 / 16.6 screens; 13 tables; employer lists 3.2 screens.
- **Top questions.** (1) Typical income and poverty? (2) Which industries and employers? (3) Unemployment over time?
- **Verdict: Keep.**
- **Small.** Fold the 3 employer lists (P3) under one sentence that names the publishing rule.
- **Effort.** S.

#### `community/housing-and-education/`: Housing and education
- **Now.** 7.5 / 9.2 screens; shade-by map.
- **Top questions.** (1) Own vs rent? (2) Home values and rents? (3) Degrees by area?
- **Verdict: Keep.**
- **Effort.** None.

#### `community/research-on-voting/`: Research on place and voting
- **Now.** 3.7 / 6.3 screens; a list of studies with methods and limits.
- **Top questions.** (1) What do studies say? (2) How strong is each one? (3) Where are the raw data?
- **Verdict: Keep.**
- **Effort.** None.

#### `history/index.html`: History
- **Purpose.** Party control over time, mayors, turning points, South Bend population.
- **Top questions.** (1) Which party held which body, and when? (2) Who were the mayors? (3) What were the turning points?
- **Now.** 21.7 / 26.4 screens:
  - party control 5.6 screens (stacked charts per body);
  - mayors 4.5 (34-row table);
  - turning points 9.2 (a timeline that **already has a theme filter**).
- **Verdict: Adjust.**
- **Proposal.**
  - (a) Party control as small multiples: the same `party_timeline` charts in a 2-column grid on desktop, with a body chooser (anchors).
  - (b) Mayors: a timeline list per city (name · years · party label); the 34-row table goes into a fold.
  - (c) Turning points: add decade jump links next to the theme filter.
  - (d) P1 links from each chart to the body's own page (county, South Bend, Mishawaka), and back from there.
- **Effort.** S–M.
- **Dependencies.** P3, P1.

#### `history/people/`: People who shaped local government
- **Purpose.** 32 people chosen by published rules, with findings and sources.
- **Top questions.** (1) Who were the important figures? (2) Why was each chosen (which rule)? (3) What did they do?
- **Now.** 17.3 / **40.7** screens; 32 large cards in a 3-column grid with photos or initials (11.9 screens at desktop).
- **Verdict: Redesign** (layout only).
- **Proposal.**

```
THE PEOPLE (32)          Filter: [Era ▾] [Rule ▾] [Office ▾] [name…]   32 of 32 shown
▸ Schuyler Colfax · U.S. Representative, Speaker, Vice President · 1823–1885 · Whig/Republican (R) · rule: higher office
▸ William G. George · Mayor of South Bend 1865–1866 · Republican (R) · rule: first
… (expanding a row shows today's full card: photo + credit, offices, summary, findings, sources)
```

  - Keep "Selection rules" and "Who the rules picked, by party and era" (the summary) above the list. They are the learning frame.
  - No party filter (the site rule); party shown as text only.
- **Effort.** S–M.
- **Dependencies.** P5.

### 3.7 Data, teaching, about

#### `data/index.html`: Data and sources
- **Purpose.** How to use the tables; 13 dataset cards; pointer to pull; gaps.
- **Top questions.** (1) Which dataset has X? (2) How big is it, and where is the CSV? (3) Where does it come from?
- **Now.** 5.3 / 8.7 screens (after the split).
- **Verdict: Keep.**
- **Effort.** None.

#### Dataset pages (template), 13 pages: `data/<set>/`

- **Purpose.** One dataset: preview (first 50 rows), what's left out, status mix, Copy CSV, its own sources.
- **Top questions.** (1) What columns and rows? (2) How trustworthy (status mix)? (3) Copy it.
- **Now** (`1280 / 400` screens):

  | Page | Screens | Page | Screens |
  |---|---|---|---|
  | data/results/ | 5.4 / 6.1 | data/elections/ | 6.8 / 7.4 |
  | data/terms/ | 5.7 / 7.4 | data/offices/ | 8.4 / 9.3 |
  | data/units/ | 5.9 / 6.4 | data/budgets/ | 5.4 / 8.6 |
  | data/tax-rates/ | 4.2 / 7.6 | data/debt/ | 4.9 / 13.1 |
  | data/cf-state/ | 8.7 / 12.1 | data/cf-local/ | 8.0 / 9.2 |
  | data/cf-large/ | 4.6 / 6.2 | data/indicators/ | 4.2 / 9.1 |
  | data/people/ | 8.0 / 8.8 | | |

  One preview table each (33–51 rows).
- **Verdict: Keep.** These are the "see all rows" pages for journalists and are already the right shape. A 50-row preview is not a primary UI problem.
- **Small.** Link each dataset page to the reader-facing page that charts it ("See this data as: Close races, Results explorer…").
- **Effort.** S.

#### `data/pull/`: How to pull the data yourself
- **Purpose.** Where each public source lives, plus the query patterns.
- **Top questions.** (1) Where is source X? (2) What query did the guide use? (3) Which county codes?
- **Now.** 18.8 / 27.9 screens; one 64-row table; long prose per source.
- **Verdict: Adjust.**
- **Proposal.** One fold per source (P5/P3) under a short index of sources; the 64-row table goes into a fold.
- **Effort.** S.

#### `teach/`: For teachers and groups
- **Purpose.** Lesson kit (Vote smarter) + outlines for other paths.
- **Top questions.** (1) Is there a ready lesson? (2) What facts can I use? (3) Handouts?
- **Now.** 9.1 / 15.4 screens; 2 tables.
- **Verdict: Keep.**
- **Small.** When landscape splits, update the outline for path 6.
- **Effort.** S.

#### `about/`: About and methods
- **Now.** 11.9 / 18.4 screens (after the sources move); neutrality policy 3.5 screens.
- **Top questions.** (1) Who made this, and is it neutral? (2) What do the badges mean? (3) How do I report an error?
- **Verdict: Keep.**
- **Effort.** None.

#### `about/sources/`: Sources index
- **Now.** 2.1 / 3.2 screens collapsed; 983 entries; search.
- **Top questions.** (1) What is source X? (2) Search by name. (3) Which kind?
- **Verdict: Keep.**
- **Effort.** None.

#### `indiana/`: Indiana's 92 counties
- **Now.** 3.3 / 6.1 screens; state map.
- **Top questions.** (1) Is my county covered? (2) Which chapters apply everywhere?
- **Verdict: Keep.** 0 in-content inbound links is fine; it is reached through "Not your county?" in the masthead.
- **Effort.** None.

---

## 4. Build plan

Batches run in priority order (reader value per effort; shared patterns before their users). "Files" lists what each batch writes, so parallel batches don't collide.

| Batch | What | Value | Effort | Files touched | Can run in parallel with |
|---|---|---|---|---|---|
| **0. Bugs** | B1 `.cov` collision; B2 here-tag contrast; B3 seat diagram; B4 campaigns default layer; B5 sentence | High (B1 cuts 31 screens) | S | `static/css/places.css`, `static/css/here.css`, landing/looks CSS, `civic/campaign_map.py` or `pages/campaign_pages.py`, `pages/elections.py` (one sentence) | Everything; do B5 inside Batch 2 if that is running |
| **1. Foundation patterns** | P3 see-all fold helper (+ Copy CSV of shown rows); P1 `civic/related.py`; P10 results `#contest-<id>`; P5 `entity_list` on top of `one_fold` | Unlocks 2–6 | S–M | `civic/components.py` (additive), new `civic/related.py`, `static/app.js` (Copy CSV), `static/js/elections.js` (P10), new CSS partial | Batch 0 |
| **2. Elections by the numbers** | Landscape → overview + `elections/margins/` + `elections/turnout/` + `officeholders/`; Up next → calendar; results turnout dedupe; moved anchors; PATHS; tests | **Highest** (Nick's request; 66 → ~4 + leaves) | L | `pages/elections.py` (or a new `pages/elections_numbers.py`), `civic/sitemap.py`, `static/js/elections.js` + new `static/js/margins.js`, `static/css/elections.css`, `moved` map, `tools/tests/` | 3, 4 (different modules). Needs `pick_one`/`district_map` from the map agent for margins §3; ship §1, §2, §4 first if the map isn't ready |
| **3. Place template** | Dedupe, reorder, P1 rail, council-district maps for SB/Mishawaka/Walkerton, organization table one row per body | High (22 pages; fixes the main dead end) | S + M | `pages/places.py`, `static/css/places.css` | 2, 4 (not with 0's B1 edit to places.css: do B1 first) |
| **4. Lists instead of stacks** | history/people list; other-committees and all-filings by committee; who-handles-this list; run pages dedupe + run/index cards; data/pull folds; community employer folds | Medium | S each | `pages/community_history.py`, `pages/campaigns.py`, `pages/campaign_pages.py`, `pages/participate.py`, `pages/data_sets.py` | 2, 3. Split by module to run 2–3 agents at once |
| **5. Judges & questions** | Question list by jurisdiction, retention folds | Medium | S–M | `pages/elections.py` | After 2 (same module) |
| **6. Navigation and hubs** | Topics/Learn nav, renames, elections hub + `elections/how-it-works/` move, your-governments → "Your place", hub links in the menu | High for journey | M | `civic/shell.py`, `civic/sitemap.py`, `pages/elections.py` (index split), `pages/participate.py` (your-governments), `static/css` nav | After 2 (both edit `sitemap.py`/`elections.py`); after 4's participate work |
| **7. After the map work** | county results per district + rail; schools seat lists + board layers + rail; legislators results/money per district; budgets per-unit 2024 flows, special units as chips, debt fold | High | S–M each | `pages/county.py`, `pages/places.py` (schools), `pages/state.py`, `pages/money.py` | Only after the map agent finishes those files. Not parallel with 3 on `places.py` (schools lives there) |
| **8. Saved-place preselect** | P4 `preselect_from_here` on calendar, tax bill (district), officeholders, judges, community maps, results | Medium–high | S–M | `static/js/here.js` (additive), page JS | After 2 and 6 |
| **9. Sticky in-page nav** | P9 on pages still over ~12 screens | Low–medium | S–M | `civic/shell.py`, CSS | After 6 (same shell file) |
| **Later** | Taxing-district map (needs a DLGF source check); "by seat" history on margins if deferred; districts as a place type in the results explorer | — | M–L | — | — |

Ways of working that apply to every batch:
- Each batch ships with `build.py --check`, an old-anchor fixture test (as in `test_page_organization.py`), and checks at 1280 and 400 in 3 looks × 2 themes, keyboard, and JS-off.
- Batches 2–9 must not change existing helper signatures; per the README they add new functions.

---

## 5. Open questions for Nick (each with a recommendation)

1. **Nav bar.** Replace `Paths · Reference ▾ · For teachers · About` with `Your place · Topics ▾ · Learn ▾ · About`, with each Topics group heading linking to a hub?
   - *Recommendation: yes.* It fits on one row at 400 px, turns "Reference" into topics readers recognize, and gives every section a parent page.
2. **Landscape URL.** Keep `elections/landscape/` as the "By the numbers" overview (recommended: old links and the path keep working) or retire it into the new Elections hub?
   - *Recommendation: keep it as the overview.*
3. **Margins page name.** "Margins: how close each race was" (plain, matches the measure) vs "Close races" (shorter nav label)?
   - *Recommendation:* page title "Margins: how close each race was", nav label "Close races". Neither implies anything about future races.
4. **Uncontested races as the first fact.** The margins page would open with "599 of 981 candidate races decided inside the county (2010–2026) had no contest". That is a computed fact, under the page's existing scope rules, but it is a strong framing.
   - *Recommendation: yes, with the definition and COMPUTED badge right next to it.* It is the most useful civic lesson in the data and applies to all parties equally.
5. **Officeholders directory placement.** A new top-level `officeholders/` page in Your governments, or keep "how incumbents took office" inside elections?
   - *Recommendation: new page in Your governments.* "Who holds every seat" is a resident question. The caucus/appointment chart is its lesson.
6. **Taxing-district map.** Derive the 36 districts as intersections of layers the guide already has (township × city/town × school corporation)?
   - *Recommendation:* first ship the saved-place preselect (no new geometry). Build the map only after checking that the DLGF/county list of district definitions supports each intersection, because the guide's rule is that it never draws a boundary itself.
7. **Copy CSV on filtered views.** Copy only the rows shown (pick_one already announces filtering) or always everything?
   - *Recommendation:* copy what is shown, and label the button "Copy CSV (N rows shown)". A separate "Copy all" stays on the dataset page.
8. **Run office pages.** Trim to office-specific facts with links to run/index for the shared steps, or merge all 6 into run/index with an office picker and retire the URLs?
   - *Recommendation: trim and keep the URLs.* They are guessable, linked from paths, and become the place for "which seat would I run for?" once district maps exist.
9. **your-governments without a saved place.** Show the chooser inline (a list of links, no map) or send the reader to the home page picker?
   - *Recommendation: inline list of links.* JS-off works and nobody bounces.
10. **Margin chart colors.** Use the accent/ink ramp for bands (never red/blue).
    - *Recommendation: yes.* `results_bars` keeps its existing party-color rule only on full results cards, not on the margins page.

---

### Appendix: every built page and its verdict (109)

Verdict counts:

| Verdict | Pages | Which |
|---|---|---|
| Keep | 61 | |
| Adjust | 37 | including 22 place pages and campaigns/county |
| Redesign | 2 | your-governments, history/people |
| Split | 2 | elections/index, elections/landscape |
| Merge | 7 | elections/calendar + 6 run office pages |

New pages proposed: `elections/margins/`, `elections/turnout/`, `officeholders/`, `elections/how-it-works/` (moved).

| Page | Verdict | Page | Verdict |
|---|---|---|---|
| index.html | Keep | your-governments/index.html | Redesign |
| who-handles-this/index.html | Adjust | places/index.html | Keep |
| map/index.html | Keep | county/index.html | Adjust |
| schools/index.html | Adjust | state/index.html | Keep |
| state/your-legislators/index.html | Adjust | state/how-the-state-shapes-local/index.html | Keep |
| elections/index.html | Split | elections/calendar/index.html | Merge |
| elections/results/index.html | Adjust | elections/judges-and-questions/index.html | Adjust |
| elections/landscape/index.html | Split | run/index.html | Adjust |
| run/township-trustee/index.html | Merge | run/township-board/index.html | Merge |
| run/school-board/index.html | Merge | run/city-council/index.html | Merge |
| run/county-council/index.html | Merge | run/precinct-committeeperson/index.html | Merge |
| money/index.html | Keep | money/what-is-a-budget/index.html | Keep |
| money/your-tax-bill/index.html | Adjust | money/budgets/index.html | Adjust |
| money/campaigns/index.html | Keep | money/campaigns/how-it-works/index.html | Adjust |
| money/campaigns/all-filings/index.html | Adjust | money/campaigns/other-committees/index.html | Adjust |
| money/campaigns/county/index.html | Adjust | money/campaigns/courts/index.html | Keep |
| money/campaigns/state-legislature/index.html | Keep | money/campaigns/south-bend/index.html | Keep |
| money/campaigns/mishawaka/index.html | Keep | money/campaigns/indian-village/index.html | Keep |
| money/campaigns/lakeville/index.html | Keep | money/campaigns/new-carlisle/index.html | Keep |
| money/campaigns/north-liberty/index.html | Keep | money/campaigns/osceola/index.html | Keep |
| money/campaigns/roseland/index.html | Keep | money/campaigns/walkerton/index.html | Keep |
| money/campaigns/centre-township/index.html | Keep | money/campaigns/clay-township/index.html | Keep |
| money/campaigns/german-township/index.html | Keep | money/campaigns/greene-township/index.html | Keep |
| money/campaigns/harris-township/index.html | Keep | money/campaigns/liberty-township/index.html | Keep |
| money/campaigns/lincoln-township/index.html | Keep | money/campaigns/madison-township/index.html | Keep |
| money/campaigns/olive-township/index.html | Keep | money/campaigns/penn-township/index.html | Keep |
| money/campaigns/portage-township/index.html | Keep | money/campaigns/union-township/index.html | Keep |
| money/campaigns/warren-township/index.html | Keep | money/campaigns/john-glenn/index.html | Keep |
| money/campaigns/new-prairie/index.html | Keep | money/campaigns/phm/index.html | Keep |
| money/campaigns/sbcsc/index.html | Keep | money/campaigns/school-city-mishawaka/index.html | Keep |
| money/campaigns/union-north/index.html | Keep | community/index.html | Keep |
| community/people/index.html | Keep | community/income-and-work/index.html | Keep |
| community/housing-and-education/index.html | Keep | community/research-on-voting/index.html | Keep |
| history/index.html | Adjust | history/people/index.html | Redesign |
| data/index.html | Keep | data/results/index.html | Keep |
| data/elections/index.html | Keep | data/terms/index.html | Keep |
| data/offices/index.html | Keep | data/units/index.html | Keep |
| data/budgets/index.html | Keep | data/tax-rates/index.html | Keep |
| data/debt/index.html | Keep | data/cf-state/index.html | Keep |
| data/cf-local/index.html | Keep | data/cf-large/index.html | Keep |
| data/indicators/index.html | Keep | data/people/index.html | Keep |
| data/pull/index.html | Adjust | teach/index.html | Keep |
| about/index.html | Keep | about/sources/index.html | Keep |
| indiana/index.html | Keep | places/centre-township/index.html | Adjust |
| places/clay-township/index.html | Adjust | places/german-township/index.html | Adjust |
| places/greene-township/index.html | Adjust | places/harris-township/index.html | Adjust |
| places/liberty-township/index.html | Adjust | places/lincoln-township/index.html | Adjust |
| places/madison-township/index.html | Adjust | places/olive-township/index.html | Adjust |
| places/penn-township/index.html | Adjust | places/portage-township/index.html | Adjust |
| places/union-township/index.html | Adjust | places/warren-township/index.html | Adjust |
| places/indian-village/index.html | Adjust | places/lakeville/index.html | Adjust |
| places/new-carlisle/index.html | Adjust | places/north-liberty/index.html | Adjust |
| places/osceola/index.html | Adjust | places/roseland/index.html | Adjust |
| places/walkerton/index.html | Adjust | places/south-bend/index.html | Adjust |
| places/mishawaka/index.html | Adjust | | |
