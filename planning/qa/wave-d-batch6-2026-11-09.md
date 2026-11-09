# Wave D, batch 6: navigation and hubs, 2026-11-09

Spec: `site-ux-review-2026-11-09.md` sections 1.4 (target site map, nav mock-up, renames), 3.1 (your-governments) and 3.4 (elections/index split); plan decisions Q1, Q2, Q5 and Q9. Nothing is committed.

Checks, all run at the end:
- `python -P -E tools/site/build.py --edition st-joseph --check` ends **PASSED** (113 pages; one new page, `elections/how-it-works/`).
- `python -P -E -m unittest discover -s tools/tests` gives **298 OK**. 21 of those are new, in `tools/tests/test_wave_d_nav.py`.
- `python -P -E tools/check_gov.py` reports **0 errors** (23 warnings, all from before this batch).

## 1. Nav bar, before and after

Before: `Paths · Reference ▾ · For teachers · About & methods`. Reference had 4 groups ("Your governments", "Elections & running", "Money", "Context") of 27 leaf links and no hub links.

After (every page, `civic/shell.py _nav`, data in `civic/sitemap.py TOPICS`):

```
[ Your place ]  [ Topics ▾ ]  [ Learn ▾ ]  [ About ]

Topics ▾   (each heading is a link to its hub)
  YOUR GOVERNMENTS ›     ELECTIONS ›                 MONEY ›                   COMMUNITY & HISTORY ›     DATA ›
  Places                 Calendar                    What counts as a budget   Who lives here            All datasets
  County government      Results                     Your tax bill             Income & work             Pull it yourself
  Schools                By the numbers              Budgets                   Housing & education       Sources index
  State · Your legislators  Close races (margins)    Campaign money            Research on voting
  Who holds office now   Turnout                                               History
  Who handles this?      Judges & ballot questions                             People in local history
  Map                    How elections work
                         Run for office
Learn ▾    LEARNING PATHS › (index.html#paths): the 7 paths, "title · about N min", each linking to its stop 1
           TEACHING: For teachers and groups
```

- **Hubs.** Your governments → `your-governments/` (Your place), Elections → `elections/index.html` (new hub), Money → `money/`, Community & history → `community/`, Data → `data/`. `places/` and `history/` are leaves directly under their headings. A test checks that all of `places/ elections/ money/ community/ history/ data/ your-governments/` are linked from the Topics menu. See question 1.
- **Progressive enhancement.** Both menus are `<details>`, so with JS off they open and close natively and every link is a plain link. The Topics menu keeps `id="ref-menu"` (old fixtures and `app.js` use it). New `static/js/nav.js`:
  - sets `aria-expanded` on each summary, kept in step with the menu;
  - keeps one menu open at a time;
  - Escape closes the open menu and returns focus to its summary;
  - a click or focus outside closes it, so tabbing past the last link closes the menu.
- **Current page.** "Your place" gets `aria-current` on your-governments; the Topics summary is marked on topic pages, Learn on teach/, About on about/*. Inside the menu the current leaf or hub heading gets `aria-current="page"`.
- **Groups are labelled lists.** Each group `<ul>` has `aria-labelledby` pointing at its heading.
- **Fits one row.** Measured on the calendar page in 3 looks × light/dark:

  | Width | Ballot | Line map | Wayfinding |
  |---|---|---|---|
  | 400 px | 73 px to spare | 41 px to spare | 62 px to spare |
  | 360 px | 33 px to spare | 1 px to spare | 22 px to spare |

  To make the Line map look fit at 360 px, its nav padding drops to 8 px below 420 px wide.
- **Wide screens.** At 1280 px the Topics panel shows 5 columns: 3 below 1000 px, 1 below 760 px. On a phone it scrolls (70vh, existing rule).
- **Keyboard (real key presses, Chrome).** Tab from "Your place" reaches the Topics summary, and Enter opens it (`aria-expanded="true"`). Tab then goes to the "Your governments" hub link, then Places. Escape closes the menu with focus back on "Topics". Opening Learn closes Topics. Tab from the last Topics link ("Sources index") closes the menu and lands on "Learn".

## 2. Renames applied

| Before | After | Where it comes from |
|---|---|---|
| Reference (menu, every hero eyebrow "Reference · …") | Topics | nav; sitemap breadcrumb |
| Context (group, eyebrows) | Community & history; Data is its own group | `Entry.group`, `TOPICS` |
| Paths + For teachers | Learn ▾ (paths with minutes + "For teachers and groups") | nav |
| About & methods (nav) | About | nav (page title unchanged) |
| community/people nav "People" | Who lives here | sitemap nav label |
| history/people (not in the menu) | "People in local history" in the menu and breadcrumb; page title unchanged | sitemap nav label |
| Judges & questions | Judges & ballot questions (nav, breadcrumb); page title "Judges and public questions" unchanged, see question 2 | sitemap nav label |
| Find your governments (title, nav, path stop, 2 in-page links) | Your place; path stop 1 of "Who does what?" is "Your governments"; the path blurb no longer names the old page | sitemap; `pages/elections.py` calendar link; `pages/map.py` link |
| Elections by the numbers | title kept; nav "By the numbers" (already so) | — |
| elections/index "How Indiana elections work" | the hub is "Elections"; the explainer keeps the title at `elections/how-it-works/` | sitemap |
| Elections & running (group) | Elections | sitemap |

**Breadcrumbs come from the sitemap now.**
- `sitemap.crumbs()` builds each breadcrumb:
  - "Topics · Elections · Calendar";
  - "Topics · Money · Campaign finance · City of South Bend";
  - "Topics · Community & history · History · People in local history";
  - "Learn · For teachers";
  - "About · Sources index".
- The topic and the parent pages are links; the page itself is `aria-current`. It renders as `<nav class="crumbs eyebrow mono" aria-label="Breadcrumb"><ol>`.
- Every page module still writes its own hero eyebrow (`<p class="eyebrow mono">Reference · Money</p>`), and most of those modules belong to other agents. So `Page._main` (shell) replaces the first such paragraph with the sitemap breadcrumb.
  - The labels are now correct on all 113 pages without touching those files. A scan of the built site finds no "Reference ·", "Context ·", "Find your governments" or "Judges & questions" left.
  - The one exception is `indiana/`: it has no topic and keeps its series eyebrow.
- `Entry.group` is now the page's topic for every topic page, including the campaign area pages, run office pages, place pages and dataset pages, which had no group before. The search index's page labels follow it.

## 3. Elections hub and `elections/how-it-works/`

- **`elections/index.html` "Elections" is now the hub** (`pages/elections.py build_hub`). It has:
  - a short orientation;
  - "Next election in the county": 2027, Primary May 4 · General Nov 2, with the rule citations and the COMPUTED badge. It also lists the governments with seats on that ballot, computed from `offices.next_election` with their sources;
  - the 2026-unofficial banner;
  - 8 cards in the review's order: Calendar, Results, By the numbers, Close races, Turnout, Judges & ballot questions, How elections work, Run for office.
- **One live fact per card, each sourced:**
  - Calendar: the next election year.
  - Results: 1,220 contests from 2010 to 2026; the latest is the Nov 3, 2026 general, with the UNOFFICIAL badge.
  - Close races: 608 of 981 races had no contest; 344 were contested, 111 of them by under 5 points (COMPUTED, canvass citations).
  - Turnout: the latest official general's turnout, cited.
  - Judges & ballot questions: counts of public questions and retention votes (COMPUTED).
  - Run for office: the six office pages.
- **Learning-path links.** The hub links to "Vote smarter" and "Elections by the numbers".
- **`elections/how-it-works/` "How Indiana elections work"** (`build_how_it_works`) is the old page, moved verbatim with the same section, table and citation ids.
- **Links into the moved sections were repointed:**
  - path stop "Vote smarter" #5 now goes to `how-it-works#candidate-info`;
  - run/index's candidate-information link;
  - the judges page's "More on the 2025 change" (`#school-boards`);
  - in `elections_numbers.py`, 3 links ("The straight-party rules" `#general`, and "How vacancies are filled" `#vacancies` twice). These are `href` targets only; see section 8.

## 4. "Your place" (your-governments/, review 3.1, Q9)

Same URL. `pages/participate.py build_governments`, new `static/js/your_place.js`.

- **Removed: the duplicate picker and seat diagram** (the 158 paragraphs that matched the home page). Both stay on the home page.
- **Hero.**
  - A "Showing: City of South Bend · township not picked · South Bend Community School Corporation · Change place" line (JS), linking to the home page picker.
  - The counts sentence, summed from the cards shown. With South Bend saved: 6 governments, 62 elected seats (you vote for 43), at least 50 appointed. That is identical to the home page's diagram for the same saved place (checked side by side).
- **§1 Your governments (`#find`, path stop).**
  - *No saved place:* an inline list of all 22 places (9 cities and towns, 13 townships). Each is a link to that place's page, so it works with JS off. With JS, each becomes a button (`aria-pressed`) that saves the place with the home picker's default township and school. It then shows that place's cards here and moves focus to the "Showing" line. The "You are here" bar follows through a `storage` event. A line points to the home page for the township inside a city and for the school corporation.
  - *Saved place:* the list hides and a "Choose a different place here" button (`aria-expanded`) brings it back.
  - *Cards,* one per government, in groups: Every address in the county (state, county, library), Townships, Cities and towns, School corporations. Each `li.gov-item.yp-card` shows:
    - its name, linked to its page, with the layer's citations;
    - "N elected · you vote for N · N appointed";
    - every seat group with its summary and notes, and the office titles in a fold that ships open;
    - the party breakdowns (`bodies_block`), the appointed-party note and the layer note;
    - "What these offices decide (N)": a fold that ships open, one line per office type with its term, the `what_it_does` text, its citation and a Run-for link where one exists;
    - links: "Who holds these seats now" (`officeholders#gov-<unit>`), latest result, campaign money, budget and next election, from `related_items`, plus "Your legislators" on the state card.

    The "pick one" township and school placeholders are cards too ("Your township (not picked yet)", with the seats every township has).
  - Every government page in the county is linked under the cards, so the page works as the Your governments hub: Places, County, Schools, State, Your legislators, Who holds office now, Who handles this?, Map.
- **§2 `#offices`:** one sentence, then the 25-row table in a "See all" fold (`tbl-office-types`, Copy CSV).
- **§3 `#meetings`:** unchanged text. The website list no longer ships `hidden`; `here.js` still filters it to the saved place.
- **JS off:** all 33 cards, the 22 links and every fold are visible, and the JS-only sentences are replaced by a no-JS one.

## 5. Where every old piece went

| Old piece | Now |
|---|---|
| your-governments picker (map-less lists, township and school questions, status line) | Home page `index.html#pick` (unchanged). Cities and townships survive as the inline link list (`#place-picker`, `#pick-places`, `#pick-uninc`, same ids) |
| Seat diagram rows `#layer-<id>`, `#seats-<id>` | Card `<li id="layer-<id>">` and card body `<div id="seats-<id>">`, same ids. Every seat group's summary, notes and titles, layer citations, party breakdowns, appointed note and layer note are in the card (a test checks each group's "label: summary" text and every note per layer) |
| Diagram "Show seats" toggles `#toggle-<id>` | Forwarded to `#layer-<id>` |
| `#layers`, `#layer-list` | Same ids on the card container |
| `#pick-township*`, `#pick-school*`, `#pick-status*`, `#pick-clear`, `#layer-data` | Forwarded to the same ids on `index.html` |
| "Links to each government and its seats" list | The cards |
| "What each office controls" table | Each card's "What these offices decide" lines, plus the full table in the §2 see-all fold (same table id) |
| Meetings list | §3, unchanged |
| elections/index.html: all 9 sections, 6 tables, gaps, every citation | `elections/how-it-works/`, same ids |

## 6. Anchor proof

- **Fixture.** `tools/tests/fixtures/anchors_before_wave_d6.json` holds every id on `elections/index.html` (124) and `your-governments/index.html` (268), taken from the built site before any edit.
- **Moved maps.**
  - The hub ships `#moved-anchors` with the 32 section, table and gaps ids (`HOW_IT_WORKS_IDS`).
  - It also forwards every citation id by prefix (`"p": {"src-": "how-it-works/index.html"}`). This is a small additive feature in `moved.js`, where an exact entry wins over a prefix.
  - your-governments ships its own map, described in section 5.
- **Tests:**
  - `test_every_old_elections_index_id_resolves`: each old id is on the hub, or the map sends it to how-it-works, where the id exists.
  - `test_moved_map_points_at_ids_that_left`.
  - `test_your_place_old_ids_kept_or_forwarded`: each old id is kept, or forwarded to a built page that has it. Every source the old page cited is still cited.
  - `test_vote_smarter_stop_moved_with_the_explainer`.
- **Browser** (fresh loads in a 1280 px iframe):

  | Old link | Lands on |
  |---|---|
  | `elections/index.html#vacancies` | `how-it-works#vacancies` |
  | `#caucus-incumbents-copy` | `how-it-works#caucus-incumbents-copy` |
  | `#src-ELX-007` | `how-it-works#src-ELX-007` |
  | `#gaps` | `how-it-works#gaps` |
  | `#path-vote-smarter-5` | `how-it-works#path-vote-smarter-5` (the stop, via `moved.js` path forwarding) |
  | `your-governments#pick-township` | `index.html#pick-township` (64 px from the top) |
  | `#toggle-county` | `#layer-county` (64 px) |
  | `#seats-municipality-south-bend` | stays on the page (64 px) |
  | `#layer-data` | `index.html#layer-data` |

  Some long-page targets end up below 64 px, for example `#vacancies` at 214 px. A direct load of `how-it-works#vacancies` does the same, so this is the existing late-font re-wrap (see question 5), not the forwarding.

## 7. Screens, B3 check, browser matrix

Screens are height ÷ 800, JS on, first load, Ballot look. "Before" was measured at the start of this batch with the browser's default theme; "after" in light.

| Page | Saved place | 1280 before | 1280 after | 400 before | 400 after |
|---|---|---|---|---|---|
| your-governments (Your place) | none | 7.3 | **5.0** | 10.3 | **6.7** |
| your-governments | South Bend | 8.4 | **5.7** | 11.7 | **7.4** |
| your-governments | Penn Twp (uninc.) | — | 5.2 | — | 6.8 |
| elections/index (hub) | — | 11.5 | **2.3** | 17.9 | **4.2** |
| elections/how-it-works (new) | — | — | 11.5 | — | 17.8 |
| index.html | none / South Bend | 4.8 / 5.3 | 4.8 / 5.4 | 8.0 / 8.5 | 8.1 / 8.5 |

With JS off, everything is open: your-governments is 50.7 screens at 400 px (all 33 cards), and the hub is 11.8 (Sources open).

**B3 (seat-diagram party-summary line), carried over.**
- Checked on index.html with South Bend saved, in 3 looks × light/dark × 1280/400 (12 loads), every layer opened. The party-summary line is under the glyphs every time.
- The check found the second half of B3, still present: a long layer title whose citation wraps onto its own line overlapped the "N elected" count by 3 to 4 px. This hit SBCSC in every look, the township placeholder at 400 px, and South Bend in Line map.
- Root cause: `.cite { line-height: 0 }`, so a line holding only the superscript had no height.
- Fix: `party.css` `.layer-head .layer-name .cite { line-height: 1.2 }`. After it, all 12 combinations measure clean.
- your-governments no longer has the diagram, so the B3 check there is moot. Its cards were checked in the same matrix.

**Browser matrix (Chrome, own tab, same-origin iframes).**
- your-governments, the hub and how-it-works × 3 looks × light/dark × 1280/400 (36 loads): look and theme applied every time, with no horizontal overflow.
- The nav one-row check is in section 1.
- Screenshots looked at by eye:
  - the Topics menu at 1280 (Ballot dark) and at 400 (Line map light);
  - Your place at 1280 (Ballot dark, no place and South Bend; Ballot light, Penn) and at 400 (Wayfinding dark);
  - the hub at 400 (Line map light);
  - the seat diagram in Ballot, Line map and Wayfinding light at 1280.

**Note on browser storage.** At the start I cleared `localStorage` "civic-place" on localhost:8787 without saving its value first. It is shared with the other agents' Chrome tabs. At the end I left `civic-place`, `civic-look` and `civic-theme` unset. If another agent's check relied on a saved place, it has to set it again.

## 8. Edits outside the listed ownership (all small)

- `pages/elections_numbers.py`: 3 link targets `elections/index.html#…` changed to `elections/how-it-works/index.html#…`. The build check fails on links to ids that left the hub, so this was required; no label or other change.
- `pages/elections.py`, judges code: 1 link target, the same change (`#school-boards`). Calendar code: the link text "Find your governments" is now "Your place".
- `pages/map.py`: the link text "Find your governments" is now "Your place".
- `pages/stubs.py`: the stub eyebrow "Reference" is now "Topics" (the shell replaces it anyway).
- `pages/landing.py`: one link under the seat diagram: "Your place: what each of these governments' offices decide, who holds the seats and how to reach them."
- `static/css/party.css`: the B3 follow-up rule above.
- `static/css/participate.css`: Your place styles.
- `tools/site/README.md`: 4 rows, plus the sitemap and moved.js rows updated.

**Label changes I did not make,** because the shell breadcrumb already corrects what readers see: the hand-written hero eyebrows in `campaigns.py`, `campaign_pages.py`, `community_history.py`, `county.py`, `money.py`, `places.py`, `state.py`, `data_sets.py`, `meta.py`, `map.py`, `elections_numbers.py` and `participate.py` (run, who). Their owners can drop that text at leisure; nothing depends on it.

`pages/meta.py`'s teach line "Stop 4: Judges and public questions" matches the unchanged page title, so I left it.

## 9. Questions for Nick

1. **"Your governments" heading → `your-governments/` (Your place), with `places/` as the first leaf.** The brief listed `places/` as the hub to reach from the heading; the review's site map names your-governments as the hub. I followed the review because the heading text then matches the page, and Your place now lists every government page in the county. Want the heading to go to `places/` instead? It is one line in `sitemap.TOPICS`.
2. **The judges page title stays "Judges and public questions"** ("public question" is Indiana's legal term). Only the nav and breadcrumb say "Judges & ballot questions". Rename the title too?
3. **Breadcrumbs by replacement.** The shell swaps each page's hand-written eyebrow for the sitemap breadcrumb (regex on the first `<p class="eyebrow mono">…</p>`, text only). It is tested and covers every page today. Should the page modules drop their eyebrow text in a later pass, so the swap is no longer needed?
4. **Your place cards carry no holder names.** Each card links to its government's fold on `officeholders/` ("Who holds these seats now") instead of repeating 163 holders. The review's mock-up showed holders inside the cards. Add them later, for example as `holder_rows` inside the card?
5. **Landing offset on long pages** (existing): an address target on a long page can end up 100 to 200 px low after the web fonts load. `margins.js` fixes it only on margins, officeholders and the calendar. Batch 9 (sticky in-page nav) could generalize it.
6. **The hub's "Next election" is county-wide** (2027: the cities and towns). Making it follow the saved place belongs to batch 8 (saved-place preselect).
7. **Not verified:** a real screen reader. Landmarks were checked from the markup and the accessibility attributes: the "Primary" and "Breadcrumb" navs, labelled menu groups, `aria-expanded`, `aria-current`, `aria-pressed`.
8. **Not verified:** the "Your township (pick one above)" placeholder sign on the home diagram looked dim in Wayfinding light. I did not measure its contrast, and it is not from this batch.

## 10. Files

New:
- `tools/site/static/css/nav.css`
- `tools/site/static/js/nav.js`
- `tools/site/static/js/your_place.js`
- `tools/tests/test_wave_d_nav.py`
- `tools/tests/fixtures/anchors_before_wave_d6.json`
- this report

Changed:
- `tools/site/civic/sitemap.py`: renames, groups, `TOPICS`, `MENU_LABELS`, `topic_of`, `crumbs`, new how-it-works entry, PATHS
- `tools/site/civic/shell.py`: `_nav`, `crumb_nav`, `_main`
- `tools/site/pages/elections.py`: hub, how-it-works, `moved_anchors(prefixes=)`, 2 links
- `tools/site/pages/participate.py`: Your place; the old `_gov_item` removed; run/index link
- `tools/site/pages/elections_numbers.py`: 3 hrefs
- `tools/site/pages/landing.py`: 1 link
- `tools/site/pages/map.py`, `tools/site/pages/stubs.py`: labels
- `tools/site/static/js/moved.js`: prefix forwarding
- `tools/site/static/css/participate.css`, `tools/site/static/css/party.css`
- `tools/site/README.md`
