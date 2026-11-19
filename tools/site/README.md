# Site generator: Indiana County Civic Guide

Python 3 standard library only. Writes a static site for one county edition.

```
python -P -E tools\site\build.py --edition st-joseph          # build into site\st-joseph\
python -P -E tools\site\build.py --edition st-joseph --check  # build, then run the checker
python -P -E tools\site\check.py site\st-joseph               # checker only
```

Preview: `pm2` process `civic-guide-preview` serves `site/st-joseph/` at http://localhost:8787/.
Note: `index.html` has no doctype on purpose (the Artifact host wraps it), so the local preview of
the landing page renders without the host's skeleton.

## Layout

| Path | What it does |
|---|---|
| `build.py` | CLI. Loads the edition, runs a builder for every sitemap entry (stub if none), writes assets, prints data warnings |
| `check.py` | Links + fragments, `<title>`, index-vs-full-document, no literal colors outside the CSS token block, banned terms, contract extras |
| `civic/data.py` | `Edition`: every CSV/JSON joined; terms by date (`current_terms`, `incoming_terms`, `terms_on`), `contests_for_office` (derives the blank `results.office_id` from `contest_id`), `source()`, `gaps()`, `variant()`, `unit_alias()` for the money files' id scheme |
| `civic/html.py` | `h(tag, attrs, *children)` builder; everything is escaped unless it is `Markup` |
| `civic/shell.py` | `Site` / `Page`: relative links at any depth (`page.rel("county/index.html#boards")`), masthead, nav, banners, footer, root-index fragment vs full document |
| `civic/components.py` | `status_badge`, `scope_badge`, `Citations` (`page.cites.cite("GOV-001;GOV-003")`, `cite_compact`), `gaps_section`, `variant_slot`, `data_table` (Copy CSV), `officeholder_card`, `section`, `callout` |
| `civic/charts.py` | Inline SVG: `hbar`, `columns` (with `breaks` series-break markers), `line` (crosshair hover), `party_timeline`, `results_bars`, `seat_dots`. Each one returns a `<figure>` with a `<details>` table view |
| `civic/layers.py` | Seat-layer computation for the landing diagram (and the future Find-your-governments page); `COUNTING_RULES` is published on /about/#counting |
| `civic/picker.py` | Visible place picker (`place_picker`: choice lists, links without JS), `picker_state(data, None)` = no place chosen, `here_payload` (names for the "You are here" bar, shipped on every page as `#here-data`) |
| `civic/answers.py` | `answer_box(ed, page, unit, offices, links=...)`: the four-answer "At a glance" box on place pages and the county page |
| `civic/search.py` | Builds `assets/search-index.json` from the rendered pages (called by `Site.write`); party tags are display-only, never matched. Version 2 (2026-11-16): every office yields an "Office" item per tab with keywords (`TAB_KEYWORDS`: money/finance/campaign/spent/raised/donations → Money; results/election/primary/votes/margin → Elections; history/past/former → History), so "mayor money" or "sheriff results" lands on the tab. Items are `[type, label, sub, href, tag, keywords]`. Ranking lives in `static/js/search.js` `civicSearchCore` (`prepare`, `rank`), testable under node |
| `static/js/here.js`, `static/js/search.js` | Saved place (localStorage `civic-place`, ids only): bar, picker, layer rows, landing map as picker, page markers; header search combobox |
| `civic/map.py` (shared parts) | `government_layers` draws the three boundary layers for any map; `embedded_map` embeds a subset (places index, Schools page, shaded maps) without touching the URL hash; `race_by_contest` links Results contests to the "How areas voted" layer (`map/index.html#race-<id>`) |
| `civic/shading.py` | Sequential shading for maps: rounded natural breaks per layer (`class_breaks`, `classify`), the 5-step teal ramp (`static/css/money_map.css`), `shade_legend` |
| `civic/money_map.py` | Budgets page money map: counted spending per resident from `spending_breakdowns.csv` and the 2020 Census counts; panel, tables for units with no boundary |
| `civic/tax_base.py` | Tax base: certified net assessed value from `assessed_values.csv` (`dlgf_certified` rows only; the Gateway estimates are never charted), the "Tax base:" line on place, school and county pages, map panel facts |
| `civic/school_stats.py` | School corporation enrollment (IDOE) and spending per student with the state median (DLGF) from `indicator_values.csv`; Schools page and map panel facts |
| `static/js/indicator_map.js` | "Shade by" picker of the community pages' indicator maps (`pages/community_history.py indicator_map_section`) |
| `civic/pick_one.py`, `static/js/pick_one.js` | "Show one" navigation: each area's detail is a `<details data-one=KEY>` that ships open (JS off: everything visible); choosing an area (map shape, list link, TOC, old `#id`, back/forward) opens its items and folds the others. Rows marked `data-one` are hidden while another area is chosen. Used by your-legislators, county, budgets and schools Added 2026-11-09 (Wave C batch 7): `one_chips` (chip links that choose areas a map cannot draw: the budgets page's units with no boundary) and `one_wrap_see_all` (a See-all fold that also opens for the chosen area: the budgets debt table) |
| `civic/district_map.py` | Clickable election-district map (state House/Senate, county commissioner/council) from `derived/district_shapes.json`; same `.cmap` contract as the boundary map, so `map.js` gives the panel. Fills only separate neighbors (`static/css/district_map.css`), never party |
| `civic/holder_rows.py` | Compact officeholder rows (office, holder with party, since, next election) that open to the card's fields; keep the card ids `office-<id>` Added 2026-11-09 (Wave C batch 7): `seat_row` (seat · who votes · holder · term end; a plain fold, not a pick_one key, for seats nested inside an area's item: schools/) |
| `civic/related.py` | "More about <entity>" rail: `related_links(page, unit_id=None, office_id=None)` (and `related_items` for the raw links) reads only what exists (results, map race, campaign page, budget, tax rate, community, run page, calendar year); `contest_anchor` / `contest_href` link one contest in the results explorer (`elections/results/index.html#contest-<id>`, opened by `static/js/elections.js`). API reference: `planning/qa/wave-a-batch1-2026-11-09.md`. Added 2026-11-09 (Wave B batch 3): `seat_items(page, office_id, campaign_races=, on_page=)` links for one seat (its result on the page, in the explorer, on the map, its race card `#r-<contest>` on the campaign area page) and `campaign_race_anchor`; a town with no seat-specific run page gets `run/index.html` in the rail Added 2026-11-09 (Wave C batch 7): `related_rail(items, name=, rail_id=, heading_tag=)` renders a caller-chosen list (county adds its own links; schools and legislators put a rail inside each item) |
| `civic/preselect.py`, `static/js/preselect.js` (Wave E batch 8, 2026-11-09) | Saved-place preselect (review P4): pages open on the reader's saved place with a visible "Showing: ... [Show all]" line, and an explicit `#anchor` wins (the line then only offers the place). Build side: `here_layer(ed, unit_id)` / `here_attrs` (layer keys "county", "state", "library", "municipality:<id>", "township:<id>", "school:<id>" on rows and groups), `here_slot(kind, target)` (hidden placeholder; kinds filter, first, one, map, explorer, taxbill), `county_districts(ed, votes)` (commissioner and council district of a saved place only where every precinct that could hold it voted in one district, from `map_votes.json`), `district_hints` / `tax_district_choice` (the taxing district only when exactly one fits). Browser side: `window.civicHere` in `here.js` (`mine()`, `hashWins()`, `line(slot, opts)`); hooks added to shared scripts: `tablefilter.js` "tf-scope" event, `pick_one.js` "one:choose" / "one:all", `map.js` "cmap-select". Used on the calendar, officeholders, results explorer (`elections.js`), judges and questions, tax bill (`money.js`), county, schools and community maps. Report: `planning/qa/wave-e-batch8-2026-11-09.md` |
| `civic/components.py` (added 2026-11-09) | `see_all_fold` / `see_all_table`: "See all N rows" fold (ships open, `data-fold="see-all"`) with `table_filter` and Copy CSV inside; `entity_list`: one row per entity, each a pick_one `one_fold`, with a words box (`tablefilter.js` filters any list whose children carry `data-tf-row`) |
| `civic/charts.py` `money_pairs` (2026-11-16) | Raised (solid accent) and spent (outlined) bar per candidate on one scale (`vmax`, cents) so several charts compare; `label_w` lines up the bars of several charts; each row carries its own value text (a rounded news figure keeps its "as reported" words). Never party colors |
| `civic/charts.py` `share_bars` | Small multiples of 100% stacked bars (accent/ink ramps in `static/css/patterns.css`, never party colors), counts printed as text under each bar, table view |
| `civic/sitemap.py` | Every page (`entries()`, office tab pages from `civic/offices.py office_entries`), the header nav (`NAV`, `nav_of`), footer links (`FOOTER`), topic groups for search (`TOPICS`), breadcrumbs (`crumbs`) and the learning `PATHS` |
| `pages/elections_numbers.py` (added 2026-11-09) | Elections by the numbers: the `elections/landscape/` overview (four summary cards), `elections/margins/` (counts, share bars by level, a district/area map with one fold per area, every race by seat, the `margins-table` see-all), `elections/turnout/`, `officeholders/`. `margin_races(ed)` is the single list of races decided inside the county with their kind (uncontested, band, not measurable); `pages/elections.py margin()` treats an unnamed "Write-in" total as no candidate |
| `static/js/tablefilter.js` deep mode (added 2026-11-09) | A container with `data-tf-deep` filters every descendant `[data-tf-row]`; `[data-tf-group]` descendants hide when empty and their folds open while a filter is on (margins areas/seats, calendar years/governments, officeholders) |
| `static/js/moved.js` (extended 2026-11-09) | Any page may ship `#moved-anchors` `{"a": {old id: "relative/path.html[#new-id]"}, "p": {id prefix: "relative/path.html"}}` (`pages/elections.py moved_anchors(page, {...}, prefixes=)`); an old `#path-<id>-<n>` link whose stop moved goes to the stop's page |
| Header and navigation (phase 6 step 1, 2026-11-16; replaces the Wave D nav bar) | One row at desktop: lockup · primary nav · search · "My place" chip · "Display" control (`shell.py _masthead`). Primary nav is `sitemap.NAV`: Governments · Offices · Elections · Money · Learn, each item a link to its hub (`aria-current="page"` on the hub) plus a `<details>` dropdown (`#ref-menu`, `#offices-menu`, `#elections-menu`, `#money-menu`, `#learn-menu`) of at most `MAX_DROPDOWN` (6) links; no mega-menu. "Display" (`#display-menu`) holds the look switcher and the light/dark toggle. About, Data, Sources index, Corrections and Not your county are `sitemap.FOOTER` links; data date, version and Not your county sit in the footer stamp. Under 1100 px the nav, chip and Display fold behind the Menu button (`#menu-btn`, a link to `#primary-nav` with JS off; `static/js/nav.js` makes it a toggle). The 2026 UNOFFICIAL banner shows only on pages whose content carries an UNOFFICIAL badge or mark and names 2026 (`Page.shows_unofficial`). Styles: `static/css/masthead.css`; breadcrumbs in `static/css/nav.css`. Test: every sitemap page is within two clicks of the header, footer and hubs (`tools/tests/test_phase6_offices.py`) |
| Breadcrumbs | `sitemap.crumbs(by_path, path)` / `Page.crumb_nav()`: "Elections › Calendar" (the nav item, linked to its hub, then parent pages); a tab page's crumb comes from its entry ("Offices › City of South Bend › Mayor › Money", `Entry.crumb`). `Page._main` puts it in place of a page's hand-written hero eyebrow (`<p class="eyebrow mono">…</p>`), so page modules need not maintain those labels. `Entry.group` is the page's topic (`sitemap.topic_of`) |
| `pages/elections.py build_hub` / `build_how_it_works` | `elections/index.html` is the Elections hub (next election, 8 cards with one sourced fact each); the explainer is `elections/how-it-works/` with the same ids, forwarded from the hub by `#moved-anchors` (`HOW_IT_WORKS_IDS` plus the `src-` prefix) |
| `pages/participate.py build_governments` + `static/js/your_place.js` | "Your place" (your-governments/): one card per government (`.gov-item.yp-card[data-layer]`, seat counts as data attributes) for the saved place, the hero counts summed from the cards; with no saved place an inline list of place links that the script turns into buttons saving the place. No picker or seat diagram (they are the home page's) |
| `static/js/anchor_landing.js` | Site-wide: after the web fonts load, re-lands a fresh `#fragment` load on its target (scroll-padding + scroll-margin), unless the reader has scrolled, the page was reloaded, or the id is absent (moved.js forwards). Replaced the page-specific `margins.js` |
| `static/js/onpage.js` | Sticky "On this page" bar (a select built from the page's `.toc`, plus Back to top) and phone-only "Back to top" after each h2, on the pages in `shell.ONPAGE_PAGES` (`data-onpage="1"` on `#site`); CSS in `static/css/onpage.css`. Without JS the plain `.toc` stays |
| `static/css/masthead.css` | The whole header (one row at 1100 px and up; Menu button below; phone: lockup, search, Menu) |
| `civic/glyph.py` | Indiana glyph (masthead) and the 92-county map |
| `civic/neutrality.py` | Banned-term list used by the checker |
| `pages/landing.py`, `pages/county.py`, `pages/indiana_map.py` | Finished pages |
| Home page (phase 6, 2026-11-18): `pages/landing.py`, `static/js/home.js`, `static/css/home.css` | The county counted, a large search box (a second copy of the header search: `search.js` `bind(ids)`, one index load), the "Your governments" strip (saved place via `civicHere`; the picker in the `#pick` fold), the map with nine layers (the Offices hub model `pages/offices.py hub_areas`; no new geometry), five doors, next on the ballot, every government and district as a list (`#list`, the no-JS form). Click or Enter selects an area and `home.js` copies its links from `#layer-data` into the panel; a second click opens the page. Old home ids forward through `#moved-anchors`. Report: `planning/qa/phase6-home-2026-11-18.md`; tests `tools/tests/test_phase6_home.py` |
| `pages/places.py` place template (2026-11-09) | 22 city, town and township pages: At a glance, "More about" rail, Who holds office now (holder rows; South Bend and Mishawaka council district maps zoomed to the city, Walkerton's wards listed), How it's organized (one row per body, every office in a See-all fold), Recent results (one row per race, charts folded), Party control, Budget (state-report charts folded), State audits, Context. `_place_order` keeps the community figures away from results and party visuals. Report: `planning/qa/wave-b-batch3-2026-11-09.md` |
| `pages/stubs.py` | Stub for any sitemap entry without a builder (title, one-line description, path-stop anchors) |
| `static/style.css`, `static/app.js` | Design system and behavior; copied to `site/<edition>/assets/` (edition colors filled from `edition.json`) |
| `static/css/looks.css`, `static/js/looks.js` | Reader-selectable looks (Ballot default, Line map, Wayfinding) as `html[data-look]` token sets + component treatments; `shell.py` sets `data-look` in `<head>` before paint (`LOOK_BOOT`) and renders the header `look_switch()`. Party colors and chart data marks are never redefined per look |

## Recipe: add a page

1. Make sure the page is in `civic/sitemap.py` (`entries()`); it already is for every v1 section.
   Keep the `sections` anchors: learning-path stops land on them (`#path-<id>-<n>` scrolls to the anchor).
2. Create `pages/<name>.py`:

```python
from civic.components import section, data_table, status_badge
from civic.html import h

def build(site):
    ed = site.ed
    page = site.page("money/budgets/index.html", banners=False)   # title/description come from the sitemap
    c = page.cites
    page.add(h("header", {"class": "page-hero"},
               h("p", {"class": "eyebrow mono"}, "Reference · Money"),
               h("h1", None, page.title), h("p", {"class": "dek"}, page.description)))
    page.add(section("over-time", 1, "Budgets over time", ..., scope="county", ed=ed))
    page.finish(gaps=ed.gaps(files=["gaps_money"], pattern=r"budget"))   # Gaps + Sources, always last
    return page
```

3. Register it in `BUILDERS` in `build.py` (`"money/budgets/index.html": budgets.build`). The stub is replaced.
4. Build with `--check`. Fix every failure; read every data warning.

## Rules every page follows

- Text from data is escaped by `h()`. Never build HTML by string concatenation of data.
- Every factual sentence carries `page.cites.cite(source_ids)`; generic Indiana explanations come from the
  `plain_language` / `what_it_does` fields in `data/indiana/*.csv`. No sentence without a source or a data field.
- Show status: `status_badge(row["status"], page)`. Low-confidence rows never go in headings or charts.
- Party colors only in `party_timeline` and `results_bars`, always with text labels. Other charts use
  `m-accent` (edition color) or `m-ink`.
- County exceptions go through `variant_slot(ed, key, generic, {value: text}, page)`; unverified variants
  get the UNVERIFIED badge automatically from `edition.json`.
- Order people by office and district, never by party or vote share. Candidates keep ballot order.
- Links: `page.rel("path/index.html")`, always to a file (never a bare directory), `#hash` names only
  letters, digits and hyphens. No `?query`, no downloads, no print buttons, no alert/confirm.
- CSS: colors only as tokens inside the `TOKENS:BEGIN/END` block (light + both dark blocks). Markup never
  carries a literal color. JS inserts data with `textContent` only and stays ASCII.
- Source titles are rendered verbatim inside `data-verbatim`; the checker exempts them from the banned-term
  lint but prints a NOTE so a loaded headline stays visible.

## Parallel-safe conventions (added 2026-11-07, supersedes "register in BUILDERS")
- **Do not edit `build.py`.** In your module `pages/<area>.py`, define `PAGES = {"site/path/index.html": build_fn, ...}`; `build.py` discovers it automatically. Each `build_fn(site)` builds exactly that page.
- **Do not edit `static/style.css` or `static/app.js`** (shared, owned by the foundation). Put area styles in `static/css/<area>.css` and area scripts in `static/js/<area>.js`; the build appends them. Use only existing tokens; new tokens must be defined with light + both dark blocks inside your partial.
- Shared helpers in `civic/` may be **extended by adding new functions**, never by changing existing signatures or behaviour. If you need a change to an existing helper, add a new one next to it and say so in your report.
- Licensed images in `site/images/` are copied to `<edition>/images/` by the build; reference them as `images/<file>` (relative to the edition root, via the shell's link helper).

## Tab template: one thing, several short pages (phase 6 step 1, 2026-11-16)

`civic/tabs.py` turns one *thing* (an office now; a government, an election or a person later) into a set of real
pages, each its own URL, so tabs work with JavaScript off, can be linked and are found by search:

| Tab | Path | Shown when |
|---|---|---|
| Overview | `<base>index.html` | always |
| Elections | `<base>elections/index.html` | the caller's model has contests |
| Money | `<base>money/index.html` | the model has money figures, or years worth a "not posted online" line |
| History | `<base>history/index.html` | the model has holders |
| Sources | `<base>sources/index.html` | always, last: every citation and gap of the whole thing |

An empty tab is neither generated nor shown: decide the keys once from your data model and pass the SAME keys to the
sitemap and the builder, so a tab bar never links to a page that is not built.

```python
from civic import tabs as T

# sitemap (civic/sitemap.py entries(), through your model module, as civic/offices.py office_entries does):
T.tab_entries(base, title, description, keys, group="Offices", crumb=[("Offices", "offices/index.html"), ...])

# builder: register every tab path in PAGES, all calling one function that builds the whole set once and caches it
# on the site (pages/offices.py build_office), so the citation numbering is shared:
pages = T.build_tabs(site, base, keys, T.Head(kind="Office", title=..., facts=[...]),
                     {"overview": fn, "elections": fn, "money": fn, "history": fn, "sources": fn})
```

- Each tab repeats one header (`thing_header`): breadcrumb, display-face title (sentence case, about half the old hero
  size), a one-line facts strip, and the tab bar (`<nav class="tabs" id="tabs">`, `aria-current="page"` on the
  current tab; it scrolls inside itself at phone width, never the page).
- Citations are numbered once for the whole thing; footnote links on every tab go to the Sources tab, whose renderer
  runs last and calls `T.sources_body(page, gaps, notes=[...], title=...)` (notes, gaps, sources, what the marks mean).
- Bodies use `T.tab_section(id, title, ...)` (a small label and space, no box) and `T.status_mark(status, page)`
  (one small glyph; wording in its title and accessible name; the key is on the Sources tab at `#marks`).
- Styles: `static/css/tabs.css` (tokens only; all three looks). Tab pages carry the body class `thing-page`.

### Office pages (`civic/offices.py`, `pages/offices.py`)

- `civic/offices.py` is the model: `office_tabs(ed, oid)`, `contests(ed, oid)` (Edition.contests_for_office, newest
  first, the general before primaries), `money_model(ed, oid)` (campaign races from `pages/campaigns.py cf_all`, the
  same sums as the race cards; news-reported rows from `money_history.reported`; state legislators from
  `money_history.legislators`), `crumb`, `government_page`, `href(page, oid, tab)`, and `office_link(page, oid, tab)`
  for cross-links (None when the page is not built).
- `pages/offices.py` renders the Offices hub (`offices/index.html`: every office grouped by level and government,
  ids `county`, `cities`, `towns`, `townships`, `schools`, `state` and `g-<unit_id>`; a plain grouped list with
  JavaScript off, filters by level and next election with it) and the five tabs. It computes no figure.
- Links in: race cards (`campaign_pages.race_block` → Money tab), holder and seat rows (`holder_rows`), the results
  explorer (cards and the every-contest table → Elections tab), and the related rail (`office` item for one office,
  `offices` item for a unit).

### Person pages (`civic/people.py`, `pages/people.py`; 2026-11-16)

- `civic/people.py` is the model and the one identity function. `group_names(names, seats)` groups name strings
  (rules in its docstring, published on the hub); `identity(ed)` gives every string a person id (slug of given name +
  surname + suffix, the full slug or a counter only on a clash); `registry(ed)` adds the records, flags, the
  notable-people row and who gets a page (`THRESHOLD`, stated on the hub; candidates below it are listed there with
  their contests). `person_tabs` (overview, elections, money, sources; no History tab), `people_entries` (sitemap),
  `href_for_name(page, name)`, and `link_names(html, page)`.
- `link_names` runs once in `Page.render` (`civic/shell.py`): every name printed by `components.name_with_party`
  (`<span class="name-party">`) or a holder row (`mrw-name`) gets a link to its person page, never inside another
  link, a `<summary>`, a button or a form control, and never on the person's own pages. The party tag is unchanged.
- `pages/people.py` renders the hub (`people/index.html`: name search, filters by status, level and notable using
  `table_filter` token selects (`"tokens": True`, matched by `tablefilter.js` against a space-separated attribute),
  one fold per letter that ships open), the notable-people view (`people/notable/index.html`, built by
  `community_history.build_history_people`), the forwarding page at the old `history/people/` address, and the four
  tabs. Money figures are the race model's own (`civic/offices.money_model` / `cf_all`), never re-added.
- Search: one Person item per page plus "Name › Tab" items with the tab keywords (`civic/search.py`, `T_PTAB`).
- Nav: People sits in the Offices menu and the footer; the header row is full at 1280 px in every look.
- Tests: `tools/tests/test_phase6_people.py`; the old notable-page ids are in `tools/tests/fixtures/anchors_before_people.json`.

### Money (phase 6 step 5, 2026-11-18; `pages/money.py`, `pages/money_browser.py`, `pages/campaign_pages.py`)

- **Money hub** (`money/index.html`, `money.build_hub`): two doors, Government money (`#government`) and Campaign money
  (`#campaign`), each with its entry points and a small ranked preview, then the headline figures (`#facts`). The
  doors' container keeps the old `#pages` id.
- **Campaign money browser** (`pages/money_browser.py`): six real-URL views sharing `browser_head` (crumb, title, facts,
  a tab bar in the `civic/tabs.py` markup): By office (`money/campaigns/index.html`), By election (`by-election/`), By
  candidate (`by-candidate/`), By place (`by-place/`: the campaigns map and area list that were the index's `#map` and
  `#areas`; `campaign_pages.map_section`), Committees (`other-committees/`) and Every filing (`all-filings/`).
  `office_rows(ed)` is the per-office model (latest race with a report on file, years on record, news years); it adds
  nothing up: bars are the race model's own sums (`campaigns.cf_all`), news-reported figures are only linked. Offices
  are ranked by what their candidates reported spending; people are never ranked (By candidate is alphabetical).
- **Area pages** (`money/campaigns/<area>/`, `campaign_pages.build_area`): open on one `charts.money_rows` chart per
  election (each race linking to its office's Money tab, `#y<year>` when that tab has the year); every race card,
  report, the district map, the like-for-like comparison, other reports and large contributions follow in
  `see_all_fold`s (ship open, `folds.js` closes them and opens one when a link points inside). Every old id stays.
- **Compare budgets** (`money/budgets/index.html`, `money.build_budgets`): the money map (areas link to government
  Money tabs), per-resident budgets and tax base, certified tax rates and debt as `money.rank_rows` lists (HTML bars in
  the `money_rows` markup; `money.ranked` shows the top 10 and folds the rest on the same scale), the tax-base section
  (`#tax-base`, folded) and every government with its latest adopted total (`#over-time`). Each unit's block of the old
  page is on its government's Money tab; `money.budgets_moved` forwards the old ids (`#<unit>`, `bud-*`, `brk-*`,
  `obrk-*`, `other-*`, `sp-*`, `money-*`, `breakdown-*`, `flows-*`).
- **Budget column charts** (`money.flag_columns`, same signature): drawn as HTML (`.fcol*` in `static/css/money.css`), so
  they use the full column width on every page; heights are inline percentages; each column is focusable with the
  shared tooltip (`data-tv`/`data-tl`).
- `money.other_breakdown_parts` + `gov_parts.other_breakdowns_section`: the proposed / later-year / news-reported
  breakdowns (ids `obrk-*`) on the government Money tab (folded).
- Search: `civic/search.py` `PAGE_KEYWORDS` (plain words per money page) and `PAGE_ALIASES` ("Campaign finance",
  "Budgets", "Property tax bill" as extra Page items).
- Styles: `static/css/money_browser.css` (`cb-*`, `mh-*`). Tests: `tools/tests/test_phase6_money.py`; old ids in
  `tools/tests/fixtures/anchors_before_phase6_money.json`.
