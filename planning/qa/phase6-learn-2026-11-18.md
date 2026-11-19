# Phase 6 step 6: Learn hub, learning paths, footer, stale-link sweep (2026-11-18)

Nothing committed. No `data/` edits; no forbidden build tools run.

## What was built

- **Learn hub** `learn/index.html` (`pages/learn.py`, new): header, then 10 guide cards (title link plus the linked page's own sitemap description, nothing new), then the 7 learning paths (title, "N stops, about M min", blurb, linking each path's first stop with `#path-<id>-1`). 2.0 screens at 1280 px, 4 at 400 px, no horizontal overflow. Whole card is the click target; the Run card also lists the six `run/<office>/` pages.
  Cards: How elections work, What counts as a budget, How campaign money works, Who handles this?, Run for office, How the state shapes local government, History and turning points, People in local history, Community profile, Lesson kits for teachers.
- **Learn dropdown** (6 links): Learning paths (`learn/#paths`), How elections work, What counts as a budget, Who handles this?, Run for office, History. Learn's hub is now `learn/index.html` (was `teach/`); `teach/` keeps its URL and content, is under Learn, and its crumb "Learn" now links to the hub. The home page no longer carries a paths list (Agent A), so the Learn hub is the path list.
- **Footer**: four labeled columns (`sitemap.FOOTER_COLUMNS`, `shell._footer`): Explore (Governments, Offices, Elections, Money, Learn, My place), People and place (People, Community profile, History, Not your county?), Data and sources (Data downloads, Sources index, Corrections log), About the guide (About and methods, How we choose what to include, What the badges mean, Choose a look, Changelog). Together they are still `#browse` (search's JS-off link). "Not your county?" is no longer duplicated in the stamp. Data date appears once. 2 columns at 400 px, 4 at desktop, no overflow. The "display/theme note": none existed in the footer; the "Choose a look" link (about/#looks) covers it.
- **Community profile**: the governments step left `community/index.html` as the hub linking the four sub-pages (people, income-and-work, housing-and-education, research-on-voting). Nothing merged. Linked from footer and Learn hub. F6 untouched.
- **School board rules guide**: not created by the governments step; not written here. The Learn hub links `run/school-board/` under Run for office. Open question below.

## Files

New: `tools/site/pages/learn.py`, `static/css/learn.css`, `static/css/footer.css`, `tools/tests/test_phase6_learn.py` (20 tests), `planning/qa/phase6-shots/learn-*.png` (hub 12 combinations, footers).

Shared-file edits (smallest possible):
- `civic/sitemap.py`: new `learn/index.html` Entry (after `teach/`); `LEARN_PAGE`; Learn item of `NAV` (hub and links); `NAV_OF_TOPIC["Community & history"]` to `learn/`; `nav_of` treats `learn/` like `teach/`; `crumbs` teach crumb links to the hub; new `FOOTER_COLUMNS` after `FOOTER` (FOOTER unchanged).
- `civic/shell.py`: `_footer` body only (columns; removed the old browse list, links row and stamp-county link).
- `pages/meta.py` line 391: About page link `history/people/` to `people/notable/` (stale link; unowned file).
- Older tests updated for the intended change: `test_wave_d_nav.py` (Learn hub is learn/, teach crumb, paths list read from the Learn hub, label list).

## Learning paths: re-pointed stops

None needed. Every stop already pointed at a live page (earlier steps re-pointed `county/#boards`, `elections/results/#turnout`, `elections/margins` etc.). Verified by test against the sitemap and the built site (page built, not forwarding, anchor id present). Flag for Agent B: two stops use `money/budgets/index.html` (Follow the money stop 3 `#over-time`; Know your community stop 4 `#tax-base`), and "Follow the money"/"Run" use `money/campaigns/how-it-works/` (keeps its URL). If `money/budgets/` becomes a forwarding page, `test_every_path_stop_points_at_a_live_page` fails and names the stop; re-point at the new Compare budgets page.

## Stale links

- Baseline measured on a fresh full build: **0** links from non-forwarding pages to forwarding pages (29 forwarding pages). An earlier build showed 2: `index.html` to `elections/margins/` (Agent A's home page, since fixed on their side) and `about/` to `history/people/` (fixed by me). `STALE_BASELINE = 0` in the test, so it can only stay at 0.
- Nothing left for other owners at this baseline. Note: Agent B's new money pages were mid-change during my runs.

## Checks

- `build.py --edition st-joseph --check`: PASSED (3484 pages, final code).
- `check_gov.py`: errors=0, warnings=23.
- `test_phase6_learn.py`: 20 tests OK. `test_wave_d_nav.py`: 21 OK.
- Full suite run (before the two final test edits): 549 tests, 7 failures + 1 error, none mine: `your-governments` ImportError of `pages.landing._unknown_split` (Agent A mid-edit; the function exists again now), and money/campaign failures from Agent B's in-progress work (`test_county_campaign_map` x3, `test_here_money_results`, `test_phase6_offices` two-clicks reachability of 9 `money/campaigns/<area>/` pages and its no-builder-failed). `test_phase6_learn.test_no_builder_failed` and `test_wave_d_nav` setUp failed in that run only because of the landing ImportError and pass now. I did not re-run the full suite after those agents settled.
- Browser (Playwright): Learn hub at 1280 and 400 px x 3 looks x light/dark: no horizontal overflow, 0 console errors. Footers screenshotted on office, about, elections pages. Keyboard: Tab reaches each card's title link, card shows a 2 px focus outline. A path link opens the path bar ("Stop 1 of 5"). JS off at 400 px: 10 cards, 4 footer columns, no overflow.

## Not verified / open

- Only a sample of footer screenshots (ballot light, and 400 px dark) were looked at by eye; I viewed 2 full-page hub shots, not all 12.
- Hub is 2.0 screens, as asked; at 400 px it is 4.
- Open question for the owner: should a "school board rules" guide be written (needs sourced content), or is `run/school-board/` plus the school corporation pages enough?
- Open: `teach/` stays a separate page under Learn; keep it, or fold the lesson kit into the hub later?
