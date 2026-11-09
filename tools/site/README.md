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
| `civic/sitemap.py` | Every page (`entries()`), the Reference menu groups and the learning `PATHS` |
| `civic/glyph.py` | Indiana glyph (masthead) and the 92-county map |
| `civic/neutrality.py` | Banned-term list used by the checker |
| `pages/landing.py`, `pages/county.py`, `pages/indiana_map.py` | Finished pages |
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
