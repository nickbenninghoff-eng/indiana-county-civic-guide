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
| `civic/search.py` | Builds `assets/search-index.json` from the rendered pages (called by `Site.write`); party tags are display-only, never matched |
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
| `civic/charts.py` `share_bars` | Small multiples of 100% stacked bars (accent/ink ramps in `static/css/patterns.css`, never party colors), counts printed as text under each bar, table view |
| `civic/sitemap.py` | Every page (`entries()`), the Topics menu (`TOPICS`), breadcrumbs (`crumbs`) and the learning `PATHS` |
| `pages/elections_numbers.py` (added 2026-11-09) | Elections by the numbers: the `elections/landscape/` overview (four summary cards), `elections/margins/` (counts, share bars by level, a district/area map with one fold per area, every race by seat, the `margins-table` see-all), `elections/turnout/`, `officeholders/`. `margin_races(ed)` is the single list of races decided inside the county with their kind (uncontested, band, not measurable); `pages/elections.py margin()` treats an unnamed "Write-in" total as no candidate |
| `static/js/tablefilter.js` deep mode (added 2026-11-09) | A container with `data-tf-deep` filters every descendant `[data-tf-row]`; `[data-tf-group]` descendants hide when empty and their folds open while a filter is on (margins areas/seats, calendar years/governments, officeholders) |
| `static/js/moved.js` (extended 2026-11-09) | Any page may ship `#moved-anchors` `{"a": {old id: "relative/path.html[#new-id]"}, "p": {id prefix: "relative/path.html"}}` (`pages/elections.py moved_anchors(page, {...}, prefixes=)`); an old `#path-<id>-<n>` link whose stop moved goes to the stop's page |
| Navigation (Wave D batch 6, 2026-11-09) | Nav bar `Your place · Topics ▾ · Learn ▾ · About` (`shell.py _nav`). Topics comes from `sitemap.TOPICS` (each group heading links to its hub; `MENU_LABELS` for menu-only wording); Learn lists `PATHS` and teach/. Both menus are `<details>` (`#ref-menu`, `#learn-menu`), so they work with JS off; `static/js/nav.js` adds aria-expanded, one menu at a time, Escape and outside-click closing. Styles: `static/css/nav.css` |
| Breadcrumbs | `sitemap.crumbs(by_path, path)` / `Page.crumb_nav()`: "Topics · Elections · Calendar" with the topic and parent pages linked. `Page._main` puts it in place of a page's hand-written hero eyebrow (`<p class="eyebrow mono">…</p>`), so page modules need not maintain those labels. `Entry.group` is the page's topic (`sitemap.topic_of`) |
| `pages/elections.py build_hub` / `build_how_it_works` | `elections/index.html` is the Elections hub (next election, 8 cards with one sourced fact each); the explainer is `elections/how-it-works/` with the same ids, forwarded from the hub by `#moved-anchors` (`HOW_IT_WORKS_IDS` plus the `src-` prefix) |
| `pages/participate.py build_governments` + `static/js/your_place.js` | "Your place" (your-governments/): one card per government (`.gov-item.yp-card[data-layer]`, seat counts as data attributes) for the saved place, the hero counts summed from the cards; with no saved place an inline list of place links that the script turns into buttons saving the place. No picker or seat diagram (they are the home page's) |
| `static/js/anchor_landing.js` | Site-wide: after the web fonts load, re-lands a fresh `#fragment` load on its target (scroll-padding + scroll-margin), unless the reader has scrolled, the page was reloaded, or the id is absent (moved.js forwards). Replaced the page-specific `margins.js` |
| `static/js/onpage.js` | Sticky "On this page" bar (a select built from the page's `.toc`, plus Back to top) and phone-only "Back to top" after each h2, on the pages in `shell.ONPAGE_PAGES` (`data-onpage="1"` on `#site`); CSS in `static/css/onpage.css`. Without JS the plain `.toc` stays |
| `static/css/masthead.css` | Phone masthead (480 px and under): date line, search, then Look and Theme side by side |
| `civic/glyph.py` | Indiana glyph (masthead) and the 92-county map |
| `civic/neutrality.py` | Banned-term list used by the checker |
| `pages/landing.py`, `pages/county.py`, `pages/indiana_map.py` | Finished pages |
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
