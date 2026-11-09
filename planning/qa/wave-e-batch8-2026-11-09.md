# Wave E, batch 8: saved-place preselect, 2026-11-09

Spec: `site-ux-review-2026-11-09.md` pattern P4 ("saved-place preselect") and the batch 8 row. Nothing is committed.

Checks, all run at the end:
- `python -P -E tools/site/build.py --edition st-joseph --check` ends **PASSED** (113 pages).
- `python -P -E -m unittest discover -s tools/tests` gives **324 OK**. 16 of those are new, in `tools/tests/test_wave_e_preselect.py`.
- `python -P -E tools/check_gov.py` reports **0 errors** (23 warnings, all from before this batch).

## 1. What a reader with a saved place sees now

Every change is announced by one line above what changed: **"Showing: ... [Show all]"**, plus a short note saying it comes from the place saved on this device. The button undoes the change, and pressing it again re-applies it. If the reader changes the same control by hand, the line turns into an offer: "Your saved place: ... [Show only these]".

| Page | Behaviour |
|---|---|
| `elections/calendar/` | The "Every seat, by year" list is filtered to the reader's governments: county, city or town, township, school corporation, and state/legislative lines. The reader's government folds open. Example: Walkerton gives 81 of 188 seats. |
| `officeholders/` | Same filter. Example: Walkerton gives 54 of 163, and the seven governments shown are open. |
| `elections/results/` | The Place filter gets a new option, **"Your saved place's areas"**, and it is selected on load. It shows the contests the reader's voters decided: on the default view (2026 general), 37 for Walkerton and 46 for South Bend. The option survives changes of year, election and office. |
| `elections/judges-and-questions/` | The question groups for the reader's areas move first, right after Statewide. **Show in the usual order** puts them back. The moved groups also get the existing "Your place" / "Your school corporation" marker. If there are no local questions, the line says so ("none for Town of Walkerton in the guide's data"). |
| `money/your-tax-bill/` | The taxing district is preselected **only when exactly one district fits** (rule in §2). Otherwise the line names the districts that fit, each as a button, says why the guide can't tell them apart, and says that the district shown is the page's example. |
| `county/` | Opens the reader's commissioner and council district (officeholder line and results item) **only where the guide's precinct results prove it** (§3). Otherwise a note says why nothing was opened. |
| `schools/` | Opens the saved school corporation. If no school corporation is saved, nothing changes. |
| `community/people/`, `income-and-work/`, `housing-and-education/` | The reader's area is selected on the "Shade by" map: the city or town, or the township for unincorporated places. Its estimates show in the panel. **Clear** removes the selection. |

**Unknown parts of a saved place never hide anything.**
- If the township is not picked, it counts as every township the city lies in.
- If the school corporation is not picked, it counts as every corporation.
- Rows the build could not place (LaVille schools in the explorer) are always shown.
- Moving question groups first is stricter: only certain matches move.

**Rules kept:**
- With no saved place, nothing changes.
- With JavaScript off, every page ships exactly as before. The placeholder is hidden and empty, all folds are open and no row is hidden. Checked on all 8 pages.
- **An explicit `#anchor` wins.** `#year-2027`, `#gov-south-bend`, `#contest-…`, `#office-county-council-c`, `#office-phm-board-madison` and `#all-rates` all open as the link says, and the line only offers the saved place. Map layer names that `map.js` writes into the address do not count as anchors.
- **Privacy.** The saved place is only read from localStorage `civic-place`. Nothing writes it to the URL, history or network; a test checks the scripts for this.

**Not done: officeholder rows on the reader's own place page.** The only rows worth preselecting there are the South Bend and Mishawaka council districts. The guide can't derive those from a saved place, which has no address.

## 2. Tax district: never guessed

The rule is `civic/preselect.py tax_district_choice`, mirrored in `static/js/money.js fromPlace`. It starts from the districts whose name states the saved place (the existing `_district_prefill`), then:
1. **Keep the districts consistent with the saved township**, when one is saved.
2. **Keep those consistent with the saved school corporation**, when one is saved. "Consistent" means the school is in the district's name or in the state's per-district unit breakdown (`certified_district_unit_rate`, the latest year).
3. **Preselect only if exactly one district remains.**

If no district fits the saved school, the result is "conflict" and the page shows choices instead. Pinned cases:

| Saved place | Result |
|---|---|
| Unincorporated Penn + PHM | 031 |
| Unincorporated Penn, no school | choice 031 / 032 |
| Mishawaka + Penn + PHM | 022 |
| South Bend, township not picked | choice of 5 districts |
| South Bend + Penn + SBCSC | **conflict**: the state lists PHM in 033, so no pick |
| Walkerton | 015 |
| Greene | 010 |

`test_tax_district_never_guesses` checks every place × township × school the picker allows: a district is picked only when it is the only one that fits. `test_js_rule_matches_python` runs the JS rule with node on the same cases and gets identical answers.

**Behaviour change in `money.js`.** The tax-bill choice used to be saved (`civic-taxbill-v2`) on every page load, so a first visit's example district (026) blocked the saved place on every later visit. It is now saved (`civic-taxbill-v3`) **only when the reader changes a picker**, and a choice the reader made still wins over the saved place. Old v2 values are ignored. A reader who had really picked a district before will see the saved place (or the example) once, until they pick again.

## 3. County districts: from the guide's own precinct results

`county_districts(ed, votes)` uses `derived/map_votes.json`: which commissioner and council race each precinct voted in, 2022 and 2024 (current lines), and the area each precinct was placed in. A place gets a district **only if every precinct that could hold part of it voted in the same district's race**. That means:
- its own precincts;
- every precinct in the same township that straddles a city or town line;
- every unplaced precinct naming the place, or naming a city in the same township for unincorporated areas.

No geometry is computed. The result is 10 places:

| Place | Commissioner | Council |
|---|---|---|
| Lakeville | 3 | F |
| North Liberty | 3 | F |
| Walkerton | 3 | F |
| Unincorporated Liberty | 3 | F |
| Unincorporated Lincoln | 3 | F |
| Unincorporated Madison | 3 | F |
| Unincorporated Union | 3 | F |
| New Carlisle | 1 | A |
| Unincorporated Greene | 1 | A |
| Unincorporated Olive | 1 | A |

These get nothing: the cities, Penn, Clay, Centre, Portage, Harris (unplaced Mishawaka precincts), German and Warren (an unplaced South Bend precinct), Indian Village, Roseland and Osceola (straddlers). The line says what this rests on: "Every precinct the guide's data places in … voted in these districts' races in 2022 and 2024 (precinct results). Your voter registration names your districts." Tests pin both the conservative straddler rule and the unplaced-precinct rule.

## 4. Browser checks (Playwright, own contexts)

**Saved places tested on all 8 pages.** No saved place; South Bend (city, township not picked); Walkerton (town); unincorporated Greene and unincorporated Penn (townships); Mishawaka + Penn + School City (for questions and the tax bill). Results are in §1–§3. No console errors anywhere.

**Interactions:**
- **Calendar:**
  - Show all, then Show only these, by mouse and by Enter.
  - Reset filters clears the scope and the line becomes an offer.
  - Choosing a single government releases the scope.
  - Show only these clears the Government filter first. An earlier build gave 0 rows here; fixed.
- **Officeholders:** words combine with the scope ("trustee" gives 1 of 163).
- **Results:** choosing another place releases the scope; choosing the option again re-applies it.
- **County:** opening another district by hand releases the scope; "Open them" re-opens D3 and F only.
- **Community map:** switching layer releases the selection; "Select it on the map" goes back to the cities layer and selects Walkerton. The address stays empty.
- **Tax bill:** a South Bend choice button (by keyboard) sets 004, the note becomes "Showing district 004 South Bend - Clay", and the choice is stored as the reader's.

**Matrix.** 8 pages × 3 looks × light/dark × 1280/400 = 96 loads. No horizontal overflow, readable token colors in every look, and the line wraps under the controls at 400 px.

**Keyboard (schools, 400 px).** The button is in the tab order between the map table's Copy CSV and the one-bar. It shows a 2 px focus outline and works with Enter and Space.

**Screenshots** are in `.playwright-mcp/`:
- `e8-elections-calendar-{1280,400}-ballot-{light,dark}.png`
- `e8-money-your-tax-bill-{1280,400}-{line,wayfinding}-{light,dark}.png`
- `e8-county-index.html-{1280,400}-wayfinding-{light,dark}.png`
- `e8-schools-400-keyboard.png`
- `e8-taxbill-400-southbend-choices.png`

## 5. Notes and questions for Nick

1. **Calendar, unincorporated reader.** The filtered calendar hides 2027 entirely (that ballot has city and town offices only), so the "2027" jump link has no target while the scope is on. The same already happens with the Year filter. The line explains the scope, and Show all restores it. Should a 2027 note stay visible instead?
2. **District seats.** The calendar, officeholders and results scopes keep every commissioner, council and legislative district of the reader's governments, because the address decides those. The line says so. Narrowing them would need the §3 derivation, or House and Senate equivalents, which were not built.
3. **Tax bill and default school.** For Mishawaka with the default school (School City of Mishawaka) and no township, the page picks 023 Mishawaka-Penn. The state's breakdown lists School City of Mishawaka in no other Mishawaka district. The line names the saved school it relied on. Is that acceptable, given the reader never chose that school explicitly?
4. A place changed in another tab updates the "You are here" bar as before, but a page already open keeps its line until reload.

## 6. Files

New:
- `tools/site/civic/preselect.py`
- `tools/site/static/js/preselect.js`
- `tools/site/static/css/preselect.css`
- `tools/tests/test_wave_e_preselect.py`
- this report

Changed:
- **Additive changes to shared scripts:**
  - `tools/site/static/js/here.js`: `HASH0` and `window.civicHere`.
  - `tools/site/static/js/tablefilter.js`: the `tf-scope` and `tf-scope-cleared` events.
  - `tools/site/static/js/pick_one.js`: the `one:choose` and `one:all` events.
  - `tools/site/static/js/map.js`: the `cmap-select` event.
- **Page scripts:**
  - `tools/site/static/js/elections.js`: the explorer's "Your saved place's areas" option.
  - `tools/site/static/js/money.js`: the district rule, the line, and saving only on reader changes (v3).
- **Page modules (data attributes and slots only):**
  - `tools/site/pages/elections.py`: `contest_layer`, `SCHOOL_UNITS`, calendar row layers, explorer `pl`, question-group layers and the `#q-groups` wrapper. All old ids are kept.
  - `tools/site/pages/elections_numbers.py`: officeholder row layers.
  - `tools/site/pages/money.py`: `hints` and the slot.
  - `tools/site/pages/county.py`: `_here_districts` and the `#here-districts` JSON.
  - `tools/site/pages/places.py`: schools slot only.
  - `tools/site/pages/community_history.py`: the indicator map slot.
- `tools/site/README.md`: one Layout row.

I did not touch `civic/shell.py`, `civic/sitemap.py`, `moved.js`, `nav.js`, `margins.js`, any data CSV, `Roadmap.md` or the session handoff.

---

# Part 2: follow-ups from the coordinator, 2026-11-09

Checks, all run at the end:
- `build.py --check` ends **PASSED** (113 pages).
- unittest gives **327 OK**: 19 tests in `test_wave_e_preselect.py`, 3 of them new, and 2 rewritten.
- `check_gov.py` reports **0 errors**.

## 1. A default never makes a specific claim (question 3: the answer is no)

**Root cause.** When a reader chooses a place, `here.js` fills its township and school with the guide's defaults (`p.t || p.td`, `p.sd`). The preselect then treated those defaults as if the reader had chosen them. A Mishawaka reader who never chose a school was saved as School City of Mishawaka, and the tax bill picked 023. Part of Mishawaka is in 022 (PHM), 005 (Clay) and 036 (Harris).

**Fix: the saved place records what the reader chose.**
- `civic-place` gains an additive `"set"` list, e.g. `{"place": "mishawaka", "township": "any", "school": "phm", "set": ["school"]}`.
- `here.js` writes it only when the reader picks a township or a school (`pickTownship` / `pickSchool` through `chosen()`).
- Choosing a place (`fresh()`, and `your_place.js`'s place buttons) stores no `set`.
- Choosing "Not sure" drops that part from `set`.
- An object saved before this change has no `set`, so all of it counts as defaults.
- An unincorporated place's own township is certain: it is part of the place, not a default.

**Back-compat.** The stored shape is otherwise the same, so the "You are here" bar, the home picker, `your_place.js` and the layer rows read old and new objects alike. Browser check: an old object `{south-bend, portage-township, sbcsc}` still shows "City of South Bend · Portage Township · South Bend Community School Corporation" in the bar and the picker.

**`civicHere.mine()`** now returns only the chosen `township` and `school`. The defaults are in `mine().defaults`, and they never decide anything. Every page, checked:

| Page | Specific claim? | Rule now |
|---|---|---|
| Tax bill | Yes: "your district" | Pick only from the chosen township and school (`tax_district_for_saved`, mirrored in `money.js fromPlace`). Defaults only order the choice buttons ("Listed first: the district that fits the guide's usual school corporation for City of Mishawaka, which you have not chosen; your address may be in any of these districts"). |
| Schools | Yes: "Opened: your saved school corporation" | Opens only a chosen school. A default opens nothing. |
| Judges and questions | Yes: "questions for your saved place's areas" first | `sure()` uses only chosen parts, so a default school's group stays in place. The groups no longer carry `data-here-unit` for schools, so here.js's marker cannot label a default "Your school corporation". City and town groups still get the marker; the place itself was chosen. |
| Calendar, officeholders, results | No: convenience filters | They now use only chosen parts too. A default school shows every school corporation ("every school corporation (none chosen)"), so a default can never hide the reader's real board. |
| County districts | Uses the place only | Confirmed: `county_districts` is keyed by the place id, and a town's or unincorporated area's township comes from the guide's precinct data, not from the stored township. No change. |
| Community maps | Uses the place only (the city or town, or the unincorporated township) | No change. |
| here.js "Your township" marker on place pages, and the "You are here" bar | Existing behaviour, not preselect | Unchanged. They show the stored defaults as before, as the home picker does with its pressed default buttons. |

**Tests.**
- `test_tax_district_never_guesses` now covers every saved place × township × school, each chosen or default. It checks two things:
  - a pick happens only when the chosen parts alone leave one district;
  - dropping the defaults never changes the decision.
- New `test_mishawaka_default_vs_explicit_school`:
  - default school → choices 005 / 022 / 023 / 036, with 023 listed first;
  - chosen School City of Mishawaka → 023;
  - chosen PHM → choices 022 / 036;
  - chosen PHM + Penn → 022.
- The node parity test runs the JS `fromPlace` on the same chosen/default cases and matches Python exactly, including the order and `fit_default`.
- New `test_here_js_keeps_explicit_choices_apart`.

**Browser: Mishawaka saved three ways, through the real home-page picker (Playwright, own context).**

| Saved as | Tax bill | Schools | Questions |
|---|---|---|---|
| Place only, default school (stored `"set": []`) | No pick. Choices 023, 005, 022, 036, "Listed first" note, the example 026 shown and labelled as the example | Nothing opened | Statewide · Mishawaka first; School City stays in place |
| Chosen School City of Mishawaka (`"set": ["school"]`) | Picks **023** ("the only district whose name and state listing fit … School City of Mishawaka") | Opens School City | Statewide · Mishawaka · School City first |
| Chosen PHM | No pick. Choices 022 and 036 ("can't tell which without your township") | Opens PHM | — |
| Chosen PHM, then Penn Township (`"set": ["township","school"]`) | Picks **022** | — | — |

"Not sure" for the school stores `"set": ["township"]`. An old object without `set` (South Bend) gets choices, never a pick. No console errors. Screenshots: `.playwright-mcp/e8b-taxbill-mishawaka-default-{1280-light,400-dark}.png`.

**Effect on readers who saved a place before today.** Their township and school count as defaults until they choose them again on the home page. So the tax bill shows choices rather than a pick, and the schools page opens nothing for them. This is the conservative side of "never guess".

## 2. Calendar: an emptied year keeps its place

- The year sections (`#year-<y>`) are now `data-tf-keep` groups. `tablefilter.js` (additive) never hides such a group. While none of its rows is shown, it shows the group's `[data-tf-group-empty]` note instead.
- With the saved-place scope on, `preselect.js` swaps in the place wording and a **Show all** button: "2027: no seats for your saved place's governments (that ballot has city and town offices only). [Show all]". With ordinary filters the note reads "2027: no seats match the filters."
- The 2027 jump link now lands on the section and its note (unincorporated Greene; lands at 111 px below the sticky bar after the smooth scroll). Show all in the note clears the scope (188 of 188) and turns the main line into an offer.
- **Side effect.** `#year-2029` ("No regular election for any office in the guide's data") used to be hidden by the deep filter even with no filter on, so its jump link landed nowhere. It is now visible, as its markup intended.
- Test `test_calendar_years_stay_as_link_targets`. Screenshot: `.playwright-mcp/e8b-calendar-greene-2027-note-400-dark.png`. No overflow at 1280 light or 400 dark.

## 3. Files changed in part 2
- `tools/site/static/js/here.js`: `set` in normalize, save and the township/school picks; `mine()` uses chosen parts only, plus `defaults`; header comment.
- `tools/site/static/js/money.js`: `fromPlace` takes chosen parts and orders by defaults; the choice wording.
- `tools/site/static/js/preselect.js`: the calendar empty-year note.
- `tools/site/static/js/tablefilter.js`: `data-tf-keep` / `data-tf-group-empty` (additive).
- `tools/site/civic/preselect.py`: `tax_district_for_saved`.
- `tools/site/pages/elections.py`: calendar `data-tf-keep` and the empty note; no school markers on question groups.
- `tools/site/static/css/preselect.css`: `.cal-year-empty`.
- `tools/tests/test_wave_e_preselect.py`

I did not touch `your_place.js`: it stores a newly chosen place with no `set`, which is already correct. No data CSV was edited and nothing is committed.
