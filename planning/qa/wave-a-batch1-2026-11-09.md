# Wave A, batch 1: foundation patterns, 2026-11-09

This batch builds five shared patterns from `site-ux-review-2026-11-09.md` §2: P3, P1, P10, P5 and P7. Each is a helper added next to the existing ones; no existing signature changed. The work is uncommitted.

Checks, all run at the end:
- `python -P -E tools/site/build.py --edition st-joseph --check` ends **PASSED** (109 pages).
- `python -P -E -m unittest discover -s tools/tests` gives **187 OK**. 29 of those are new, in `tools/tests/test_wave_a_patterns.py`.
- `python -P -E tools/check_gov.py` reports **0 errors**.

## 1. What is on the site now

| Pattern | Where it shows | Status |
|---|---|---|
| P3 "See all rows" fold | `elections/results/` gets a new closed fold, "See all 1,225 contests", holding every contest as a table with Year, Office group and Place filters, a words box and Copy CSV | Live |
| P10 deep link to one contest | `elections/results/index.html#contest-<id>` opens the explorer with only that contest. Each explorer card now has a "Link to this result" link | Live |
| P1 "More about" rail | The South Bend place page and the county page, right after "At a glance" | Live, as proof only |
| P5 entity list | No page uses it yet. Every candidate page belongs to batch 4. It is unit-tested and was browser-checked on a throwaway demo page that the build then deleted | Helper only |
| P7 `share_bars` | No page uses it yet; batch 2 will use it for margins. It is unit-tested and browser-checked on the same demo page | Helper only |

## 2. API reference

### P3: `components.see_all_fold` / `components.see_all_table`

```python
see_all_fold(fold_id, count, body, noun="row", plural=None, hint="Copy CSV", label=None, cls="") -> Markup
see_all_table(table_id, headers, rows, *, noun="row", plural=None, caption=None, numeric=(), label=None,
              min_width=None, row_attrs=None, controls=None, search=None, sort=None, filter_label=None,
              intro=None, fold_id=None, summary=None) -> Markup
```

**Markup contract**
```html
<details class="fold-details see-all" id="FOLD_ID" data-fold="see-all" open>
  <summary class="fold-summary see-all-summary">
    <span class="see-all-label">See all 163 rows</span><span class="see-all-hint">Filters · Copy CSV</span>
    <span class="fold-toggle" aria-hidden="true"></span></summary>
  <div class="fold-body see-all-body"> intro · table_filter bar · filter_empty_note · data_table (+ #TABLE_ID-copy) </div>
</details>
```

**Behavior**
- It ships `open`, so with JS off every row is visible.
- `folds.js` closes it on load. It reopens the fold when the address or a link targets an id inside it, and it opens the fold for printing.
- `see_all_table` gives `fold_id` the default `<table_id>-all`.
- The filter arguments are exactly `table_filter`'s. Rows opt in through `row_attrs`, for example `{"data-tf-year": "2024"}`.
- The filter bar appears only when `controls`, `search` or `sort` is given.

**JS hooks**
- None new.
- `tablefilter.js` fires `rows-filtered`. `app.js` then relabels the Copy button ("Copy 5 shown rows") and copies only the shown rows.
- I checked this inside a closed fold, then after opening it: the clipboard held the header plus 5 rows.

**Example**
```python
page.add(hbar(...summary chart...),
         see_all_table("rates-all", ["Unit", "2024", "2025"], rows, noun="unit", caption="Every unit's rate",
                       row_attrs=[{"data-tf-kind": k} for k in kinds],
                       controls=[{"key": "kind", "label": "Kind", "options": [("city", "Cities"), ...]}],
                       search="Words"))
```

### P1: `civic/related.py` (new)

```python
related_links(page, unit_id=None, office_id=None, *, name=None, exclude=(), rail_id="related") -> Markup | None
related_items(page, unit_id=None, office_id=None) -> [RelatedLink(key, topic, text, href)]
```

**Inputs**
- `unit_id` can be a city, town, township, `county` or a school corporation.
- `office_id` alone means one office, for example `state-house-5`; the unit is then the office's own.
- An unknown id raises `KeyError`.

**Item keys, in fixed `ORDER`, and what each needs to exist**

| key | target | appears when |
|---|---|---|
| `place` | `places/<id>/`, `county/`, `schools/#<id>` | Always, except on that page itself. This is how campaign area pages link back to their place |
| `results` | `elections/results/#contest-<id>` | The head office (mayor, clerk-treasurer, trustee) or the given office has a contest from 2010 on |
| `map-votes` | `map/#race-<id>` | One of its offices has a race on "How areas voted" (`race_by_contest`). The head office's race is preferred |
| `campaigns` | `money/campaigns/<area>/` | The area page is in the sitemap. For state House and Senate offices it is `state-legislature` |
| `budget` | `money/budgets/#<unit id>` | A money-file id maps to the unit (the same rule `pages/money.py` uses for its block ids) |
| `tax-rate` | `money/your-tax-bill/#all-rates` | `tax_rates.csv` has rows for the unit |
| `community` | `community/people/#who` (cities, county) or `#townships` | `answers.population_rows` finds census rows |
| `run` | `run/<slug>/` | The unit has an elected seat of a type in `RUN_FOR_TYPE` |
| `calendar` | `elections/calendar/#y<year>` | The next regular election year (`layers._next`) is in `CALENDAR_YEARS` (2026–2030) |

**Markup contract**
```html
<nav class="related" id="related" aria-labelledby="related-h">
  <h2 class="related-h" id="related-h">More about South Bend</h2>
  <ul class="related-list"><li data-related="results"><a class="related-link" href="...">
    <span class="related-topic">Latest result</span><span class="related-text">Mayor, 2023</span></a></li>…</ul></nav>
```
- The h2 has `class` before `id`, so the header search does not index it.
- The rail is hidden in print.

**How "never a dead link" is enforced**
- Every target is a static `<a href>`, so `check.py` fails the build on any missing page or `#id`.
- `test_wave_a_patterns.Built` builds the two rail pages and every page they link to, then checks every link lands.
- `RelatedRules` pins the copied rules to their sources: `RESULTS_FROM` equals `pages/elections.RESULTS_FROM`, `CALENDAR_YEARS` equals `elections.YEARS`, `HEAD_TYPE` equals `answers.HEAD_OFFICE`, and every `RUN_FOR_TYPE` entry is in `participate.OFFICES`.

**Example for batch 3 and batch 7**
- Batch 3, place template: `related_links(page, uid)` after the answer box. Drop the `if uid == "south-bend"` guard in `pages/places.py`.
- Batch 7, legislators: `related_links(page, office_id="state-house-5", rail_id="related-house-5")`.
- Campaign area pages: `related_links(page, unit_id, exclude=("campaigns",))`. The page itself is already excluded automatically.

### P10: deep links to one contest

```python
related.contest_anchor(contest_id) -> "contest-<id>"     # ValueError if the id has other than [A-Za-z0-9-]
related.contest_href(page, contest_id) -> str | None     # None if the explorer doesn't list it (before 2010, unknown)
related.in_results(ed, contest_id) -> bool
related.latest_contest(ed, office_id) -> dict | None     # newest general contest the explorer lists
```

**Markup contract on the results page**
- Every explorer contest has a row in the "every contest" table.
- Each row's first cell is `<span id="contest-<id>">`.
- The explorer payload (`#elx-data`) now keeps `id` per contest.
- A test checks that the row ids and the payload ids are the same set.

**`static/js/elections.js` behavior**
- **On load or hashchange to `#contest-<id>`:**
  - it sets Year and Election to that contest's and shows only that card;
  - the state line reads "Showing one contest, from the link you followed: …";
  - a **Show every contest in this election** button appears;
  - the card is focused (`tabindex=-1`) and scrolled into view.
- **The fold stays as the reader had it.** `folds.js` opens the fold because the target row is inside it, so this script closes it again, unless the reader had opened it.
- **Load order.** The landing step runs in a `setTimeout(0)` after `folds.js`, and again after `load`, because the browser re-scrolls to the fragment.
- **Leaving the one-contest view:** any filter change does it. So does the button, which also clears the hash.
- **Same-hash link:** clicking a link to the contest already in the address re-shows it.
- **JS off:** the link lands on the table row. The table uses fixed layout, so rows above the target don't resize while the table loads.

**Example**
```python
href = contest_href(page, "2023g-south-bend-mayor")
if href: page.add(h("a", {"href": href}, "Full result"))
```

### P5: `components.entity_list`

```python
entity_list(list_id, items, *, noun="item", plural=None, search=None, controls=None, sort=None,
            filter_label=None, heading_tag="h3", label=None) -> Markup
items: [{key, name, facts?: [str|Markup] (2-3), status?: status key or Markup, body,
         item_id?, heading_id?, search?: extra words, attrs?: {"data-tf-<key>": value}}]
```

**Markup contract**
```html
<div class="ent-block">
  [table_filter bar, data-tf-table="LIST_ID"] [<p data-tf-empty="LIST_ID" hidden>No people match…</p>]
  <ul class="one-list ent-list" id="LIST_ID">
    <li class="ent-row" data-tf-row data-tf-text="name facts words" data-tf-…>
      <details class="fold-details one-fold ent-item" open data-fold="one" data-one="KEY" data-one-name="NAME" id="ITEM_ID">
        <summary class="fold-summary one-summary"><h3 class="one-h ent-name">NAME</h3>
          <span class="one-digest ent-facts">fact · fact</span><span class="ent-status">badge</span>…</summary>
        <div class="fold-body one-body">BODY</div></details></li></ul></div>
```

**Behavior**
- Every row follows the `pick_one` contract:
  - rows ship open;
  - `folds.js` closes them on load;
  - a link or `#id` inside a row opens that row, and `pick_one.js` folds the others;
  - `one_bar(...)` works above the list for "Showing X · Show all · Collapse all".
- The status badge on the summary line is a plain span: a link inside `<summary>` would take over the toggle. Put the linked badge in `body`.
- Search matches the name, the facts and the `search` text, not the whole card.
- Callers sort the items. People go by office and district, never by party.

**JS hooks**
- `tablefilter.js` (additive change): `data-tf-table` may name any element. Its direct children with `data-tf-row` are filtered and sorted like table rows.
- `rows-filtered` still fires; `app.js` ignores it for non-tables.

**Example (batch 4, history/people)**
```python
entity_list("people-list", [{"key": p["id"], "name": p["name"], "item_id": f"person-{p['id']}",
             "facts": [p["office"], p["years"]], "status": p["status"], "body": card(p)} for p in people],
            noun="person", plural="people", search="Find a name or office")
```

### P7: `charts.share_bars`

```python
share_bars(fid, title, groups, series, subtitle=None, noun=("item", "items"), ramp="seq", note=None, status=None,
           page=None, group_header="Group", cite=None, show_zero=True) -> Markup
groups: [{label, counts: {series key: int}, href?: drill-down link, tip?}]   # in the order given
series: [{key, label, mark?}]                                                # stack and legend order
```

**Output**
- The standard chart `<figure class="chart chart-share">` with caption, status, legend (shown for 2 or more series), body, note and a "Show table" view with Copy CSV.
- The body is HTML, not SVG:
  - `.shb-row`: the label (a link when `href` is set) and "N races";
  - `.shb-bar` (`aria-hidden`): one `.shb-seg` per non-zero part, `flex-grow: count`, 2px surface gaps, 14px thick, 4px corners;
  - `.shb-counts`: every category's swatch, count and share as text, with zeros greyed;
  - one `0% / 50% / 100%` axis.
- Every count is printed as text, so the segments are not tab stops. Pointer hover shows `data-tv`/`data-tl` tooltips. Screen readers read the count lists.

**Colors (`static/css/patterns.css`)**
- `ramp="seq"` is for ordered categories: `m-share-0..3`, the accent at 100/72/48/28%, mixed with `--surface`.
- `ramp="alt"` is for unordered categories: `m-share-a0..a5`, alternating accent and ink, as in the tax-bill split.
- `series[i]["mark"]` overrides a step, for example `m-nodata` for "not in the data".
- Party classes are never used, and a test checks it.
- More series than the ramp has steps (4 or 6) raises `ValueError`; fold the tail into "Other" first.
- Contrast: the lightest seq step is low against the surface (1.3–1.5:1). That is acceptable only because every count is also text and in the table view. If a batch needs the lightest step to read as a shape, use 3 categories.

**Example (batch 2, margins)**
```python
share_bars("margin-levels", "How close were local races?", [{"label": lvl, "counts": c, "href": f"#lvl-{k}"} ...],
           [{"key": "unc", "label": "Uncontested"}, {"key": "lt5", "label": "Under 5 points"},
            {"key": "5to15", "label": "5 to 15 points"}, {"key": "gt15", "label": "Over 15 points"}],
           noun=("race", "races"), status="computed", page=page, group_header="Office level", cite=c.cite(src))
```

## 3. Browser checks (Playwright, isolated contexts)

**Matrix**
- 4 pages (results, South Bend, county, the demo) × 3 looks × light/dark × 1280/400 = 48 loads.
- The look and theme applied every time. There was no horizontal overflow and no console errors.
- Screenshots are in `.playwright-mcp/wa1-*.png`.

**P10**
- **Fresh load** of `#contest-2023g-south-bend-mayor`: 1 card ("South Bend: Mayor"), the state line, Year 2023 and Election 2023g set, the fold closed, the card focused.
- **Show every contest in this election:** 28 cards; the hash is cleared and the button hidden.
- **Hashchange** to another contest: 1 card, and the fold stays closed.
- **Filter change:** leaves the one-contest view.
- **From the South Bend rail:** the card is on screen at both 1280 and 400, and Back returns to South Bend.
- **JS off:** the browser lands on the row with the full result.
  - The browser's smooth scroll takes about 1.5 s to reach it. My first measurements were taken mid-scroll, which is why the fixed table layout was added.

**P3**
- **Opening and filtering:** I opened the fold and filtered it to 2023 + "mayor": "5 of 1225 contests shown", the button read "Copy 5 shown rows", and the clipboard held 6 lines.
- **Keyboard:** Enter on the summary opens it.
- **Demo table:** filtering to 2012 gave "Copy 11 shown rows".

**P5 (demo)**
- **On load:** 0 of 14 rows open, and the bar reads "Pick an office to open it."
- **Keyboard:** Enter on a summary opens one row, and the state line names it.
- **Search:** "council 2028" shows 4 rows and the count line reads "4 of 14 offices shown."; a search with no match shows the empty note; Reset works.
- **`#office-county-council-c`:** opens that row alone.
- **JS off:** all 14 rows are open, and the filter bar and state bar stay hidden.

**P7 (demo)**
- **Legend, wrapping and axis:** the legend and the count lines wrap at 400 px. A long label wraps, and an empty group shows "No races in the guide's data." The axis lines up.
- **Hover:** the tooltip reads "6 of 22 (27%) · County offices · Uncontested".
- **Themes:** dark and wayfinding render correctly.

**P1**
- **Keyboard:** Tab moves through the rail links in order, with a visible focus ring.
- **400 px:** the links sit two per row.
- **JS off:** all 7 links are there.

## 4. Edits outside batch 1's own files (all minimal)

**`pages/elections.py`** (batch 2 owns it), needed for P3 and P10 on the results page:
- `_every_contest_table()` (new, about 35 lines) builds the fold;
- the payload keeps `id` (one line);
- one sentence was added to the `<noscript>`;
- the import line changed.

**`pages/places.py`** (batch 3 owns it): one import, plus one line in the hero, `related_links(page, uid) if uid == "south-bend" else None`.

**`pages/county.py`** (batch 7 owns it): one import, plus `related_links(page, "county")` in the hero.

**`static/js/tablefilter.js`:** the list support described under P5. Tables behave as before.

**`tools/site/README.md`:** three rows added to the Layout table.

## 5. Notes and questions for the main session

1. **Results page weight.** `elections/results/` grows from about 0.42 MB to 0.92 MB (132 KB gzipped). The new table has 1,225 rows. To keep it down, the status column is plain text and the filters use group indexes. Is that acceptable, or should batch 2 trim the candidate column?
2. **The county rail's map link is arbitrary.** The county has no head office, so its "On the map" link goes to the latest county race on the votes layer: Treasurer, 2024. Batch 7 may prefer `exclude=("map-votes",)`, or a race that matters more.
3. **The tax-rate link isn't specific.** It lands on the all-units chart (`#all-rates`) because there are no per-unit ids on that page. If batch 7 adds `id="rate-<unit>"`, change one line in `related.py`.
4. **Copied rules.** `related.py` copies four small rules from page modules: the results start year, the calendar years, the run-page types and the head offices. It does this so `civic/` never imports `pages/`. The tests fail if any of them drifts.
5. **Not done.** I did not update `Roadmap.md` or `docs/session-handoff.md`. I did not edit `check.py`, the `places.css`/`here.css`/looks CSS, or any data CSV.

## 6. Files

New:
- `tools/site/civic/related.py`
- `tools/site/static/css/patterns.css`
- `tools/tests/test_wave_a_patterns.py`
- this report

Changed:
- `tools/site/civic/components.py` (additions only)
- `tools/site/civic/charts.py` (additions only)
- `tools/site/static/js/elections.js`
- `tools/site/static/js/tablefilter.js`
- `tools/site/pages/elections.py`
- `tools/site/pages/places.py`
- `tools/site/pages/county.py`
- `tools/site/README.md`
