# Phase 6: person pages (2026-11-16)

Built by the people-pages agent (Opus). Nothing committed, pushed or deployed. No file under `data/` edited; none of
the forbidden tools run.

## What was built

- **Person pages** `people/<id>/` with real-URL tabs: Overview, Elections (only when the person is in results.csv),
  Money (only when there are figures), Sources. No History tab. Shared header strip (name, one line: office now or
  last, terms count, contests count; a "may be more than one person" line when it applies), breadcrumbs
  People › Name › Tab.
  - Overview: one fixed list of fields, in the same order for everyone: Offices now, Offices before, Races in the
    results, Party as recorded, Campaign money on record, Notable-people list. Then "Offices held" (each term with dates,
    how the person took office as terms.csv records it, party as recorded on that term), the notable-people card when
    the person is on that list (the same card as the list, built from the same code; no election-result lines), and
    "Names in the records" (each spelling and which files print it, plus the "may be more than one person" note).
    Party is always as recorded: one line when every record agrees, otherwise each recorded party with the records
    that carry it. Nothing is inferred.
  - Elections: every contest newest first, grouped by year; the newest year's results drawn as full-width bars
    (`charts.results_rows` via the office pages' `_contest_figure`), older years one line each with a Chart fold.
    Each contest links to the office's Elections tab (`#c-<contest>`) and to the election page's contest anchor.
  - Money: one bar pair per election on one scale (`charts.money_rows`), then each figure with where it comes from and
    links to the office's Money tab, the race card and the committee's money history; a see-all table with Copy CSV.
    Figures are the race model's own candidate sums (`offices.money_model` / `campaigns.cf_all`), the news-reported
    rows from `money_history.reported`, committee cycles no race counts (`money_history._parts`), and state filing
    years for legislators. Nothing re-added.
  - Sources: citations and gaps, as on the other tabbed pages.
- **People hub** `people/index.html`: Name search box first, then filters Office status (holds office now / has held /
  candidate), Level, Notable. A–Z letter links, then one fold per letter in a grid (all ship open, so with JavaScript
  off it is the plain full list; with it on they close and the page is 2.3 screens at 1280×900). Then "Candidates
  without a page (164)" (each linked to their contest) and the published threshold and name-matching rules. No map.
- **Notable-people view** `people/notable/index.html`: the old History › People list (built by the same
  `community_history.build_history_people`), with every old id, now under People. `history/people/` is a forwarding
  page (meta `civic-moved-to`, canonical, plain link, `#moved-anchors` for every old id), so netlify_prep.py emits the
  301. The notable view is its own URL rather than `people/#notable` because a Netlify 301 cannot carry a fragment.
- **Name links**: `civic/people.py link_names` runs once in `Page.render`, so every name printed by
  `components.name_with_party` (office, government, election, campaign and results pages) and every holder row
  (`mrw-name`) links to the person's page. It never links inside another link, a `<summary>`, a button or a form
  control, never on the person's own pages, and the party tag markup is unchanged. The officeholders table (names
  in `<strong>`, no party tag helper) links explicitly. `officeholders/` stays.
- **Search**: one Person item per page (other spellings as keywords) plus "Name › Tab" items with the tab keywords.
  "mueller money" → "James Mueller › Money" first (checked in the browser).
- **Nav**: People is in the **Offices dropdown** and the **footer**, not the header row: at 1280 px the header row is
  already full in all three looks (lockup to 347 px, nav to ~800, search, My place, Display to 1207). The Learn
  menu's "People in local history" now opens `people/notable/`; the learning-path stop was moved too.
- **Shorter pages** (at 1280×900, ballot look):
  - `governments/county/` Overview 6.5 → **4.8 screens**: council list shows 3 rows + "Show the other 6 council
    seats"; the countywide officers and judges (elected countywide, not on the map) are one fold; the Superior Court
    rule is a fold. Every row and id stays; a link to a folded row opens its fold (checked: `#office-county-auditor`).
  - `elections/compare/` Close races 8.6 → **4.65 screens**: the margin definitions are a fold (`#bands` opens it),
    the area map is a fold ("Show the map"), each level of government is one fold in a grid ("County · 13 areas"),
    and the by-level bars sit two to a row on wide screens. Choosing an area (link, old `#area-<id>`) opens its level
    (pick_one wrapper); the filters and the name box open the folds they match (checked: "Mueller" → 1 seat, Office
    filter → 9 seats). JS off: all 118 seats visible.
  - Neither reached exactly 4: what is left on each is charts and the map key that the tab is about. Getting to 4.0
    would mean folding the county district map or the Compare short-answer chart; I did not, as both are the main
    content. Say if you want that.

## Identity rules (as published on the hub)

The data has no person ids; `civic/people.py group_names` is the one function that decides, and the sitemap, pages,
search and links all read it.

1. Two strings are one person only when the full name agrees: `campaign_money.same_person` (same surname, suffixes and
   initials set aside, a shared given name, a nickname in quotes/parentheses counts as a given name), with given names
   also compared through community_history's nickname table (Stephen/Steve). Notes in parentheses ("(write-in)",
   "(interim)", "(printed …)") and titles (Dr., Rev., Hon.) are set aside first. A surname alone or initials alone
   never match anything.
2. Middle names/initials written on both must agree; a middle that is the other's nickname ("Bobby K") is not a
   middle. Suffixes written on both must agree. A suffix on one string only joins only when both hold the same office
   (or the same government when one has no office), since it can name a parent and a child.
3. When strings of one group disagree, the group is not merged: the disagreeing strings are sides; a string that
   would join several sides joins the one side it shares an office with if exactly one, else stands alone. Such pages
   name each other as possibly the same person.
4. A group with records more than 20 years apart, no term spanning the gap, both stretches with a recorded party
   (not NP or W) and no shared party or government is marked "may be more than one person with this name". Nothing is
   merged or split on these grounds.

Ids: slug of given name + surname + suffix (`james-mueller`, `henry-davis-jr`); the full-name slug, then `-2`, only
on a clash.

## Counts

- 952 people (identity groups) from terms.csv, results.csv, people.csv and the campaign-finance files.
- **764 with a page**: 356 from terms.csv, 8 notable people with no term, 379 general/special-election candidates for
  a county, township, city, town, school-board or state-legislative seat, 21 primary candidates with campaign money on
  record. 166 hold an office now.
- 188 without a page: **164 below-threshold candidates listed on the hub** with links to their contests; the other 24
  are statewide or non-local candidates and partial names (see below), not listed.
- 246 groups join differently spelled strings (table below).
- 3 "may be the same person" families (rule 3); 0 pages flagged by rule 4.
- Pages built: 1,013 → **3,480** (+2,467 person-tab pages, the hub, the notable view).

## Merge table (every group that joins differently spelled strings)

Columns: id | strings joined | years on record | governments | parties as recorded. Full table (246 rows) is in the
appendix at the end of this file.

## Ambiguous and near cases (for review)

- **Split, named as possibly the same person (rule 3)**:
  - Lacy Hahn / Lacy Jaden Hahn / Lacy Jane Hahn (Mishawaka council): three pages, "Lacy Hahn" holds the seat.
  - Thomas L. McCormick vs Tom E. McCormick: "Tom McCormick" joined Tom E. (same Liberty Township Board seat).
  - Robert H. / Robert M. / Robert Middlebrook (Olive Township board): three pages.
- **Kept apart, not flagged**: Michael C. Berger vs Michael L. Berger (no bridging string); Schuyler Colfax vs
  Schuyler Colfax III (one-sided suffix, no shared office); William Scott Groves Jr. vs William Groves (one-sided
  suffix, check).
- **Merged across a one-sided suffix because the office is the same**: Joe Taylor / Joe Taylor III (state house),
  Curtis Hill / Curtis T. Hill Jr. (attorney general).
- **One page, more than one party recorded** (shown as recorded, each line with its records): Gerard Arthus (L, R),
  Kevin Conery (I, R), Henry Davis Jr (D, I), William Davis (D, R; county and South Bend, 2007–2012; no page),
  Derek Dieter (D, R), Marcus Ellison (D, I), Betty Kolacz (D, R), Jennifer McCormick (D, R; statewide, no page),
  Ryan Schafer (D, R), Mike Wozny (D, R). William Davis is the one most likely to be two people.
- **Long gaps, same party, not flagged**: B. Patrick Bauer (30 years), Carl Baxmeyer (31), John Brademas (33),
  Bob Kovach (40), Roger Parent (24; D council 1979–88, nonpartisan school board 2012).
- **Partial names never merged and given no candidate page**: "Carter", "Colpitts", "J. J. Kata", "J. Kata",
  "K. Brookins", "R. Kronewittier", "T. Brown", "Pfeifer (given name unconfirmed …)". "D. B. J. Schafer" has a term
  so has a page of its own.

## Decisions

- Notable view at its own URL (`people/notable/`) because a 301 cannot keep a fragment; every old card id
  (`person-ppl-0xx`, `person-<name>`) and section id is still on that page, and each card links to the person page.
- Low-confidence notable people (Burnie Bauer, Dave Wood, Edward Voorde, Jeff Rea, Margaret Prickett) are a
  flagged table row on the list, not a card, so their Overview shows the same flagged row and links to the list's
  `#low-confidence` table.
- Threshold: officeholders, notable people, every general/special-election candidate for a local or
  state-legislative seat, and primary-only candidates with campaign money on record. Primary-only candidates without
  money are listed on the hub with their contest. Partial names never get a candidate page.
- `table_filter` gained two additive, optional features (no existing call changed): `"tokens": True` on a control
  (matches a space-separated row value; tablefilter.js) and `search_first=True` (keyword only).
- Bug fixed on the way: the notable-people pool credited Schuyler Colfax III's 1898 mayoral term to Schuyler Colfax;
  the pool now uses the same identity as the person pages (the only change to that list's content).

## Build time and size

| | Before | After |
|---|---|---|
| Pages | 1,013 | 3,480 |
| Build | 108 s with --check | 57 s build alone; checker ~250 s (see below) |
| `site/st-joseph` | 136.9 MB, 1,054 files | 246.4 MB, 3,521 files (`people/` 108.6 MB) |

Each person page is ~38 KB, of which ~20 KB is the shared header and ~11 KB the two site-wide JSON blocks
(`here-data`, `paths-data`); the page's own content is ~2–4 KB. See open questions.

## Verification

- `python -P -E tools/site/build.py --edition st-joseph --check`: **PASSED**, 3,480 pages, no BUILD FAILED, 291 s
  (build ~57 s + checker ~235 s; the checker's time grows with the page count, it was 108 s total before). Note: the
  first full check found 5 broken links (low-confidence people's cards pointing at card ids that do not exist on the
  list); fixed (see Decisions).
- `python -P -E -m unittest discover -s tools/tests`: **534 tests OK** (was 500; +34 in the new
  `tools/tests/test_phase6_people.py`). Updated on purpose, with the same test count per file: `test_wave_b_batch4.py`
  (notable-list ids now checked on people/notable/), `test_wave_d_nav.py` (breadcrumb of the notable list; a "People"
  menu link may exist now but only to the person hub).
- `python -P -E tools/check_gov.py`: 0 errors (23 warnings, as before).
- Browser (Playwright, http://localhost:8787): 14 pages (hub, notable view, Mueller's 4 tabs, Buttigieg, Vandewalle,
  Lacy Hahn, Burnie Bauer, county Overview, Compare, the mayor's office page, officeholders) × 1280 and 400 px × 3 looks
  × light/dark: no horizontal overflow, 0 console errors. Hub filters: now 166, held 356, candidate 408, Cities 161,
  notable 37, name "mueller" 1. JS off: hub shows all 764 rows, filters hidden; Compare shows all 118 seats.
  Old `history/people/#person-ppl-011`, `#person-james-mueller`, `#people-list`, `#turning-points` land on
  people/notable/ with the id there. Header search "mueller money" → "James Mueller › Money" first. Keyboard: tab
  order runs through skip link, nav, search, then the page; folds open with Enter. Screenshots:
  `planning/qa/phase6-shots/people-*.png`.

## Not verified

- Every one of the 764 pages by eye: checked James Mueller (all tabs), Pete Buttigieg, Dave Vandewalle (township
  board), Robin Ackerson (candidate, never held office), Lacy Hahn (may be more than one person), Burnie Bauer (low
  confidence), and automated overflow/console checks on 14 pages × 2 widths × 3 looks × light/dark.
- Screen-reader pass.
- The Netlify 301 for `history/people/` (only netlify_prep's input, the meta tag, is tested).

## Data problems seen (not edited)

- Lacy Hahn's middle name is printed two ways (Jaden / Jane) in results.csv; one of them is likely a typo.
- Robert H. vs Robert M. Middlebrook on the Olive Township board ballots: same problem.
- William (Bill) Davis is D in one record and R in another (county and South Bend, 2007–2012).
- Pending notable people with no card: Janet Allen, Eugenia Braboy, Pfeifer (given name unconfirmed).
- Margaret Prickett's party is "presumed R" (low) in terms.csv, blank in people.csv (already on the roadmap).

## Open questions for Nick

1. Site size grew by 110 MB (2,467 small pages carrying the full header). Fine for Netlify, but the header and the two
   JSON blocks could load once from a shared file. Worth doing in the "final checks" step?
2. County Overview and Close races stop at ~4.7–4.8 screens; folding the county district map or the Compare chart
   would reach 4. Want that?
3. Should primary-only candidates without money get pages too (would add ~100 pages)?
4. Lacy Hahn and Robert Middlebrook: confirm whether the different middle names are one person; a name alias table
   (a data change) would then merge them under the published rules.

## Appendix: merge table (246 groups)

| id | strings joined | years | governments | parties as recorded |
|---|---|---|---|---|
| aaron-rypma | Aaron J. Rypma ; Aaron Rypma | 2014–2018 | new-carlisle | R |
| aaron-troutmiller | Aaron F. Troutmiller ; Aaron Troutmiller | 2014–2018 | county | R |
| abby-doyle | Abby Doyle ; Abigail "Abby" Doyle | 2025–2026 | county | R |
| alan-grzeskowiak | Alan Grzeskowiak ; Alan M. Grzeskowiak | 2022–2025 | penn-township | D |
| alex-bowman | Alex Bowman ; Alex C Bowman | 2020–2025 | in-senate, state | D |
| allen-williamson | Allen (Al) Williamson ; Allen J. Williamson ; Allen Williamson | 2010–2019 | new-prairie | NP |
| amy-cressy | Amy Cressy ; Amy S. Cressy ; Amy Suzanne Cressy | 2025–2027 | county | D |
| amy-drake | Amy Drake ; Amy Marie Drake | 2022–2026 | county | R |
| amy-rolfes | Amy Conlin Rolfes ; Amy Rolfes | 2022–2026 | county | R |
| andy-kostielney | Andrew "Andy" T. Kostielney ; Andrew T. "Andy" Kostielney ; Andrew T. (Andy) Kostielney ; Andrew T. Kostielney ; Andy Kostielney | 2009–2024 | county | R |
| andy-rutten | Andy Rutten ; Anthony (Andy) Rutten | 2022–2025 | county, phm | NP, R |
| anthony-underly | Anthony Underly ; Anthony V. "Tony" Underly ; Anthony V. Underly | 2014–2025 | olive-township | D |
| anthony-vanoverberghe | Anthony G. VanOverberghe ; Anthony Gerard VanOverberghe ; Anthony VanOverberghe ; Anthony Vanoverberghe | 2010–2027 | warren-township | D |
| april-hathaway | April Hathaway ; April L. Hathaway | 2015–2015 | lakeville | D |
| arden-balmer | Arden Balmer ; Arden W Balmer ; Arden W. Balmer | 2016–2026 | union-north | NP |
| autumn-kaylor | Autumn Giang Thu Kaylor ; Autumn Kaylor | 2026–2027 | county | D |
| barbara-woods | Barbara D. Woods ; Barbara Woods | 2010–2014 | greene-township | R |
| benjamin-blatt | Benjamin M. Blatt ; Benjamin Max Blatt | 2011–2015 | mishawaka | R |
| betty-kolacz | Betty A Kolacz ; Betty A. Kolacz ; Betty Kolacz | 2010–2026 | county, warren-township | D, R |
| bianca-tirado | Bianca Latrice Tirado ; Bianca Tirado | 2023–2025 | south-bend | D |
| bill-price | Bill Price ; William Price | 2018–2022 | harris-township | D |
| bill-redman | Bill Redman ; William Redman | 2018–2027 | county | D |
| bill-sniadecki | Bill Sniadecki ; William (Bill) Sniadecki | 2012–2025 | sbcsc | NP |
| bill-stroup | Bill Stroup ; William (Bill) Stroup | 2010–2022 | union-township | R |
| bob-beutter | Bob Beutter ; Robert Beutter | 1984–1984 | mishawaka |  |
| bob-kovach | Bob Kovach ; Robert Kovach | 1974–2025 | county, in-senate, mishawaka | D |
| bobby-kruszynski | "Bobby K" Kruszynski ; (Bobby K.) Kruszynski Jr. ; Bobby K Kruszynski ; Bobby K Kruszynski Jr ; Bobby K. Kruszynski Jr. ; Bobby Kruszynski ; Robert "Bobby K" Kruszynski ; Robert L. "Bobby K" Kruszynski Jr. | 2014–2027 | county, warren-township | D |
| brett-maurer | Brett C Maurer ; Brett Maurer | 2026–2027 | clay-township | D |
| brian-schmutzler | Brian S Schmutzler ; Brian Schmutzler | 2026–2026 | in-senate, state | R |
| bryan-albright | Bryan Albright ; Bryan L Albright | 2022–2027 | liberty-township | R |
| bryan-tanner | Bryan J Tanner ; Bryan J. Tanner ; Bryan Tanner | 2015–2027 | county, mishawaka | D |
| canneth-lee | Canneth J Lee ; Canneth J. Lee ; Canneth Lee | 2020–2025 | south-bend | D |
| carissa-smith | Carissa M Smith ; Carissa Smith | 2022–2027 | john-glenn | NP |
| carl-baxmeyer | Carl Baxmeyer ; Carl H Baxmeyer ; Carl H. Baxmeyer | 1987–2026 | clay-township, county, south-bend | R |
| charles-kulp | Charles A. Kulp ; Charles Kulp | 2022–2027 | lincoln-township | R |
| cheryl-ashe | Cheryl Ashe ; Cheryl L Ashe ; Cheryl Lynn Ashe | 2018–2027 | portage-township | D |
| chris-riley | Chris Riley ; Christopher Smith Riley | 2010–2027 | phm | NP, R |
| christian-mattix | Christian L Mattix ; Christian Lee Mattix ; Christian Mattix | 2016–2024 | john-glenn | NP |
| christine-carson | Christine Carson ; Christine L Carson | 2022–2027 | john-glenn | NP |
| christine-rowe | Christine K. Rowe ; Christine Rowe | 2010–2020 | lakeville, union-township | R |
| christopher-bowman | Christopher Bowman ; Christopher D Bowman | 2018–2027 | centre-township | D |
| christy-donlon | Christy Donlon ; Christy L Donlon | 2026–2027 | walkerton | D |
| craig-fry | Craig Fry ; Craig R. Fry | 1988–2012 | in-house, mishawaka, state | D |
| curtis-hill | Curtis Hill ; Curtis T. Hill Jr. | 2016–2024 | state | R |
| dale-devon | Dale DeVon ; Dale Devon ; Dale R. Devon | 2008–2026 | county, in-house, state | R |
| damien-cruz | Damien Cruz ; Damien P. Cruz | 2014–2018 | portage-township | D |
| dan-caruso | Dan Caruso ; Daniel J. Caruso Sr. ; Daniel Joseph Caruso Sr. | 2018–2027 | new-carlisle | D |
| dan-schaetzle | Dan Schaetzle ; Daniel Joseph Schaetzle | 2022–2026 | county | R |
| daniel-chamberlin | Daniel Chamberlin ; Daniel P Chamberlin ; Daniel P. Chamberlin | 2015–2025 | walkerton | R |
| daniel-drotar | Daniel Drotar ; Daniel R. Drotar | 2018–2019 | john-glenn | NP |
| daniel-zeiger | Daniel O. Zeiger ; Daniel Zeiger | 2012–2017 | union-north | NP |
| dave-wood | Dave Wood ; David A. (Dave) Wood ; David Allen (Dave) Wood | 2010–2025 | in-house, mishawaka, state | R |
| david-hoffman-jr | David Hoffman Jr ; David James Hoffman Jr | 2022–2026 | german-township | D |
| david-niezgodski | David L Niezgodski ; David L. Niezgodski ; David Lee Niezgodski ; David Niezgodski | 2006–2025 | in-house, in-senate, state | D |
| david-varner | David A. Varner ; David Varner | 2011–2015 | south-bend | R |
| dawn-jones | Dawn Jones ; Dawn M Jones ; Dawn M. Jones | 2012–2023 | sbcsc, south-bend | D, NP |
| deborah-fleming | Deborah A. Fleming ; Deborah Fleming | 2010–2024 | county | R |
| dennis-holland | Dennis D. Holland ; Dennis Holland | 2010–2019 | john-glenn | NP |
| dennis-jordan | Dennis J. Jordan ; Dennis Jordan | 2010–2018 | county | R |
| derek-dieter | Derek D Dieter ; Derek D. Dieter ; Derek Dieter | 2011–2025 | county, south-bend | D, R |
| diana-hess | Diana Hess ; Diana Lee Hess | 2014–2025 | county | D |
| doloris-schosker | Doloris A Schosker ; Doloris A. Schosker ; Doloris Anne Schosker ; Doloris Schosker | 2014–2027 | german-township | D |
| donald-o-blenis | Donald A. O'Blenis ; Donald O'Blenis | 2010–2014 | greene-township | D |
| doris-portolese | Doris J Portolese ; Doris J. Portolese ; Doris Portolese | 2014–2026 | penn-township | R |
| doug-chaffee | Dale Douglas Chaffee "Doug Chaffee" ; Doug Chaffee | 2012–2024 | phm | NP |
| earl-wigfall | Earl B Wigfall ; Earl Bernard Wigfall | 2026–2026 | county | D |
| eli-wax | Eli Wax ; Eliyahu A Wax | 2020–2025 | south-bend | R |
| elizabeth-mccombs | Elizabeth J. McCombs ; Elizabeth McCombs | 2015–2024 | roseland | D |
| eric-harris | Eric Harris ; Eric R. Harris | 2011–2026 | in-house, in-senate, south-bend, state | R |
| ethan-legg | Ethan Legg ; Ethan W. Legg | 2016–2018 | in-house, state | L |
| gabrel-kempf | Gabrel (Gabe) A Kempf ; Gabrel Kempf | 2022–2024 | sbcsc | NP |
| gene-brems | Gene Brems ; Gene L. Brems | 2010–2018 | lincoln-township | D |
| gene-reese | Gene Reese ; Robert E. Reese (Gene) | 2014–2026 | walkerton | R |
| george-moffett | George M. Moffett ; George Moffett | 2012–2018 | union-north | NP |
| gerry-brown | Gerry Brown ; Gerry E Brown ; Gerry E. Brown | 2010–2027 | north-liberty | R |
| gregg-hixenbaugh | Gregg A Hixenbaugh ; Gregg A. Hixenbaugh ; Gregg Hixenbaugh | 2019–2025 | mishawaka | D |
| harold-saunders | Harold (Irish) Saunders ; Harold Saunders | 2026–2027 | union-township | R |
| holly-parks | Holly Ann Parks ; Holly Parks | 2014–2027 | school-city-mishawaka | NP |
| jacob-baska | Jacob "Jake" Baska ; Jacob Baska | 2026–2027 | harris-township | D |
| james-christie | James Christie ; James R Christie | 2022–2023 | lincoln-township | R |
| james-pepple | James Pepple ; James W Pepple ; James W. Pepple | 2010–2022 | german-township | D |
| jamie-o-brien | James A O'Brien ; James A. (Jamie) O'Brien ; James Arthur O'Brien ; James O'Brien ; Jamie O'Brien | 2014–2026 | county | R |
| jamie-woods | Jamie C Woods ; Jamie C. Woods ; Jamie Woods | 2012–2025 | phm, sjc-courts | NP |
| jan-cervelli | Jan Cervelli ; Janice Ann Cervelli | 2025–2027 | county | D |
| janet-hooten | Janet (Jan) F. Hooten ; Janet F Hooten | 2018–2022 | greene-township | R |
| jared-mcqueen | Jared M McQueen ; Jared McQueen | 2020–2024 | union-north | NP |
| jason-banicki | Jason A. Banicki ; Jason Banicki | 2019–2024 | south-bend | D |
| jason-cichowicz | Jason Allen Cichowicz ; Jason Cichowicz | 2018–2025 | sjc-courts | D |
| jason-critchlow | Jason Critchlow ; Jason M Critchlow ; Jason M. Critchlow | 2010–2027 | phm, portage-township, south-bend | D, NP |
| jeanette-mccullough | Jeanette E McCullough ; Jeanette McCullough | 2016–2024 | sbcsc | NP |
| jeffery-emmons | Jeffery E. Emmons ; Jeffery Emmons | 2012–2017 | school-city-mishawaka | NP |
| jennifer-mccormick | Jennifer G McCormick ; Jennifer McCormick | 2016–2024 | state | D, R |
| jennifer-robinson | Jennifer L Robinson ; Jennifer L. Robinson ; Jennifer Robinson | 2018–2027 | german-township | D |
| jim-fox | James N. (Jim) Fox ; James N. Fox ; Jim Fox | 2010–2018 | county, sjc-courts | R |
| jim-garrett | James L. Garrett ; Jim Garrett | 2016–2024 | phm | NP |
| jo-broden | Jo Broden ; Jo M. Broden | 2015–2016 | south-bend | D |
| jodi-buoscio | Jodi Buoscio ; Jodi L. Buoscio | 2013–2016 | in-house, state | D |
| joe-reed | Joe Reed ; Joseph I Reed Jr. | 2025–2025 | north-liberty | R |
| joe-taylor-iii | Joe Taylor ; Joe Taylor III | 2016–2025 | in-house, state | D |
| john-broden | John Broden ; John E Broden ; John E. Broden | 2000–2025 | in-senate, sjc-courts, state | D |
| john-maciejczyk | John Maciejczyk ; John Michael Maciejczyk | 2024–2026 | county | R |
| john-mcgee | John A. McGee ; John McGee | 2010–2019 | lincoln-township | D |
| john-mcnamara | John McNamara ; John R McNamara ; John R. McNamara | 2012–2020 | county | D |
| john-murphy | John H. Murphy ; John Murphy | 2022–2025 | county | D |
| john-paczesny | John Andrew Paczesny ; John Paczesny | 2026–2027 | sbcsc | I, NP |
| john-roggeman | John J. Roggeman ; John Roggeman | 2011–2015 | mishawaka | D |
| john-schick | John Andrew Schick ; John Schick | 2014–2026 | state | L |
| joseph-carbone | Joe Carbone ; Joseph G Carbone | 2012–2025 | county | D |
| joshua-albright | Joshua A Albright ; Joshua A. Albright ; Joshua Albright | 2018–2027 | liberty-township | R |
| joshua-gobel | Joshua P Gobel ; Joshua Paul Gobel | 2022–2024 | clay-township | R |
| joshua-lange | Joshua David Lange ; Joshua Lange | 2026–2027 | penn-township | D |
| joyce-joiner | Joyce Amber Joiner ; Joyce Joiner | 2023–2025 | walkerton | R |
| julie-mudrovich | Julie Ann Mudrovich ; Julie Mudrovich | 2023–2027 | roseland | D |
| kareemah-fowler | Kareemah Fowler ; Kareemah N. Fowler | 2015–2025 | south-bend | D |
| karen-iovino | Karen Iovino (interim) ; Karen S. Iovino | 2011–2017 | lakeville | D |
| karen-vargo | Karen E Vargo ; Karen E. Vargo ; Karen Vargo | 2014–2026 | harris-township | R |
| karen-white | Karen L White ; Karen L. White ; Karen White | 1999–2025 | south-bend | D |
| karl-nichols | Karl Nichols ; Karl Stephen Nichols | 2016–2019 | sbcsc, south-bend | D |
| karman-eash | Karman Eash ; Karman L. Eash | 2014–2024 | union-north | NP |
| karol-jackson | Karol Jackson ; Karol S Jackson ; Karol S. Jackson | 2015–2025 | walkerton | D |
| kate-lee | Kate Lee ; Kathryn Sue Hiser Lee ; Kathryn Sue Hiser Lee (Kate) | 2022–2025 | sbcsc | I, NP |
| kathryn-chrapliwy | Kathryn Chrapliwy ; Kathryn T. Chrapliwy | 2014–2018 | walkerton | D |
| kathryn-jaworski | Kathryn Jaworski ; Kathryn R. Jaworski | 2018–2023 | greene-township | R |
| katie-bell | Katelyn Inabnit Bell ; Katie Bell ; Katie Inabnit Bell | 2024–2025 | phm | NP |
| keith-batzel | Keith Batzel ; Keith N Batzel | 2022–2027 | olive-township | R |
| kelly-carrico | Kelly Carrico ; Kelly Marie Carrico | 2022–2027 | union-township | R |
| kelvin-poindexter | Kelvin D. Poindexter ; Kelvin Poindexter | 2010–2019 | portage-township, south-bend | D |
| ken-cotter | Ken Cotter ; Kenneth "Ken" Cotter ; Kenneth P Cotter ; Kenneth P. Cotter | 2014–2025 | county | D |
| ken-lindsay | Ken Lindsay ; Kenneth E (Ken) Lindsay ; Kenneth E. (Ken) Lindsay ; Kenneth E. Lindsay | 2010–2026 | harris-township | R |
| kent-hizer | Kent D Hizer ; Kent D. Hizer ; Kent Hizer | 2010–2026 | county, penn-township | R |
| kevin-conery | Kevin (K C) Conery ; Kevin (KC) Conery ; Kevin Conery | 2022–2026 | clay-township, county | I, R |
| kevin-hawkins | Kevin Hawkins ; Kevin Jerome Hawkins | 2026–2027 | sbcsc | D, NP |
| kevin-lynch | Kevin A. Lynch ; Kevin Lynch | 2010–2014 | liberty-township | R |
| larry-beehler | Larry A Beehler ; Larry A. Beehler ; Larry Beehler | 2010–2027 | phm | NP |
| larry-romero | Larry H. Romero ; Larry Romero | 2010–2014 | phm | NP |
| leslie-wesley | Leslie Ann Wesley ; Leslie Wesley | 2016–2020 | sbcsc | NP |
| lori-camp | Lori A Camp ; Lori Ann Camp ; Lori Camp | 2025–2027 | county | D |
| lori-hamann | Lori Hamann ; Lori K Hamann ; Lori K. Hamann | 2015–2023 | south-bend | D |
| lori-kelly | Lori Kelly ; Lori L. Kelly (interim) | 2019–2019 | lakeville |  |
| loris-zappia | LORIS PATRICK ZAPPIA ; Loris Patrick Zappia ; Loris Zappia | 2024–2025 | sjc-courts | R |
| lynn-king | Lynn King ; Lynn King, Jr. | 2024–2024 | sbcsc | NP |
| marcellus-lebbin | Marcellus (Marcel) Lebbin ; Marcellus M. (Marcel) Lebbin | 2010–2026 | new-carlisle, phm | NP, R |
| marcus-ellison | Marcus Edward Ellison ; Marcus Ellison | 2011–2025 | sbcsc, south-bend | D, I, NP |
| marcy-kauffman | Marcy Kauffman ; Marcy L Kauffman ; Marcy Louise Kauffman | 2018–2027 | new-carlisle | D |
| mark-catanzarite | Mark A. Catanzarite ; Mark Catanzarite | 2012–2025 | county | D |
| mark-costello | Mark Costello ; Mark E Costello | 2022–2027 | sbcsc | NP |
| mark-telloyan | Mark P. Telloyan ; Mark Peter Telloyan ; Mark Telloyan | 2012–2025 | county, in-house, sjc-courts, state | NP, R |
| mark-voelker | Mark A Voelker ; Mark Voelker | 2022–2027 | county, penn-township | R |
| martha-tyler | Martha E. Tyler ; Martha Tyler | 2011–2015 | lakeville | R |
| matt-carroll | Matt Carroll ; Matthew Branch Carroll | 2023–2025 | mishawaka | D |
| matt-chaffee | Matt Chaffee ; Matt David Chaffee "Matt" ; Matthew David Chaffee "Matt" | 2022–2025 | phm | NP |
| matt-mammolenti | Matt Mammolenti ; Matthew Mammolenti | 2011–2025 | mishawaka | D |
| matthew-clayton | Matt Clayton ; Matthew Clayton ; Matthew Scott Clayton "Matt" | 2026–2026 | clay-township, county | R |
| matthew-lentsch | Matt Lentsch ; Matthew Lentsch | 2014–2018 | penn-township | R |
| melinda-fountain | Melinda (Mindy) Fountain ; Melinda J. (Mindy) Fountain | 2018–2025 | clay-township, in-senate, state | D |
| mellissa-johnson | Mellissa Johnson ; Mellissa Kay Johnson | 2020–2024 | school-city-mishawaka | NP |
| michael-dvorak | Michael A. Dvorak ; Michael Dvorak | 1986–2026 | county, in-house | D |
| michael-gotsch | Michael G. Gotsch ; Michael Gotsch | 2010–2011 | sjc-courts | D |
| michael-mcgann | Michael J McGann ; Michael J. McGann ; Michael McGann | 2016–2024 | county | D |
| michael-pence | Michael R. Pence ; Mike Pence | 2012–2016 | state | R |
| michael-ping | Michael L. Ping ; Michael Ping | 2011–2015 | mishawaka | R |
| michelle-shaw | Michelle M Shaw ; Michelle M. Shaw ; Michelle Shaw | 2022–2027 | clay-township | D |
| mike-bellovich | Michael Allen Bellovich ; Mike Bellovich | 2011–2024 | mishawaka | R |
| mike-castellon | MICHAEL CASTELLON "MIKE" ; Michael Castellon ; Michael Castellon "Mike" ; Mike Castellon | 2010–2026 | county, penn-township | R |
| mike-compton | Mike Compton ; S. Michael (Mike) Compton | 2011–2025 | mishawaka | D |
| mike-grzegorek | Michael D. Grzegorek ; Michael Dean Grzegorek ; Mike Grzegorek | 2010–2025 | county | D |
| mike-hamann | Michael J. Hamann ; Mike Hamann | 2010–2027 | county, south-bend | D |
| mike-schalk | Michael Schalk (write-in) ; Mike Schalk | 2022–2024 | roseland | O, W |
| muhammad-shabazz-ii | Muhammad A Shabazz II ; Muhammad A. Shabazz II ; Muhammad Shabazz II | 2022–2027 | portage-township | D |
| nancy-duncan | Nancy B Duncan ; Nancy Duncan | 2026–2027 | penn-township | D |
| oletha-jones | Oletha Jones ; Oletha L Jones ; Oletha L. Jones | 2014–2022 | sbcsc | NP |
| oliver-davis | Dr. Oliver J. Davis, Jr. ; Dr. Oliver James Davis, Jr. ; Oliver Davis ; Oliver J. Davis | 2011–2026 | county, in-house, south-bend, state | D |
| pat-richter | Pat Richter ; Patric "Pat" Richter ; Patric N (Pat) Richter | 2026–2027 | clay-township | D |
| patricia-jordan | Patricia Ann Jordan ; Patricia Jordan | 2020–2025 | county | R |
| peter-mullen | Peter H. Mullen ; Peter Mullen | 2010–2011 | county | D |
| peter-quist | Peter C Quist ; Peter Quist | 2023–2024 | osceola | R |
| phil-dotson | Phil Dotson ; Phillip (Phil) G. Dotson ; Phillip G. Dotson | 2012–2016 | county | D |
| phillip-king | Phillip J King ; Phillip J. King ; Phillip Joseph King ; Phillip King | 2012–2024 | new-prairie | NP |
| rafael-morton | RAFAEL MORTON ; Rafael A Morton ; Rafael A. Morton ; Rafael Morton | 2012–2025 | county | D |
| randy-figg | Randall L Figg ; Randall L Figg (Randy) ; Randy Figg | 2023–2025 | county | R |
| regina-preston | Regina Preston ; Regina W. Preston | 2015–2016 | south-bend | D |
| rhonda-richards | Rhonda Le Richards ; Rhonda Richards | 2023–2024 | south-bend | R |
| richard-mochel | Richard E. Mochel ; Richard Mochel | 2010–2014 | madison-township | R |
| richard-peterson | Richard Peterson ; Richard T. Peterson | 2010–2014 | liberty-township | R |
| richard-pfeil | Richard J. Pfeil ; Richard Pfeil | 2010–2024 | county, in-house, state | R |
| richard-schmidt | Richard L Schmidt ; Richard L. Schmidt ; Richard Schmidt | 2010–2027 | madison-township | R |
| richard-shail | Richard A. Shail ; Richard Alan Shail ; Richard Shail | 2012–2025 | new-prairie | NP |
| richard-ziegler | Richard J Ziegler Sr ; Richard Ziegler ; Richard Ziegler Sr. | 2010–2023 | centre-township, county | R |
| rick-coffman | Rick A Coffman ; Rick Coffman | 2022–2026 | john-glenn, walkerton | NP, R |
| rick-hunt | Richard "Rick" Hunt ; Richard (Rick) Hunt ; Rick Hunt | 2010–2018 | county, portage-township | D |
| robbie-thomas | Robbie M Thomas ; Robbie Thomas | 2014–2026 | clay-township | R |
| robert-borlik | Robert A Borlik ; Robert A. Borlik ; Robert Borlik | 2012–2021 | john-glenn | NP |
| robert-mccahill | Robert J. McCahill ; Robert McCahill | 2010–2014 | county | D |
| robert-price-sr | Robert (Bob) L Price ; Robert (Bob) L Price Sr | 2026–2026 | warren-township | R |
| rod-goodchild | Rod Goodchild ; Roderick (Rod) Goodchild | 2015–2024 | portage-township, south-bend | D |
| roger-parent | Roger O. Parent ; Roger Parent | 1979–2012 | sbcsc, south-bend | D, NP |
| ron-baker | Ron Baker ; Ron F Baker | 2026–2027 | centre-township | D |
| ron-banicki | Ron Banicki ; Ronald S Banicki (Ron) ; Ronald S. Banicki ; Ronald S. Banicki (Ron) | 2011–2025 | mishawaka | D |
| rosemary-mandrici | Rosemary Mandrici ; Rosemary R. Mandrici | 2010–2025 | county | D |
| ross-deal | Ross Deal ; Ross J Deal | 2011–2023 | in-house, mishawaka, state | D |
| rudy-monterrosa | RODOLFO MONTERROSA, JR ; Rodolfo (Rudy) Monterrosa Jr ; Rodolfo Monterrosa Jr. ; Rodolfo S. Monterrosa, Jr ; Rudy Monterrosa ; Rudy Monterrosa Jr | 2017–2027 | german-township, greene-township, sbcsc | D, NP |
| ryan-dvorak | Ryan Dvorak ; Ryan M Dvorak ; Ryan M. Dvorak | 2002–2026 | in-house, south-bend, state | D |
| ryan-hill | Ryan Hill ; Ryan William Hill | 2022–2027 | portage-township | D |
| ryan-mishler | Ryan D. Mishler ; Ryan Mishler | 2004–2025 | in-senate, state | R |
| sandra-ort | SANDRA K. ORT ; Sandra K Ort ; Sandra K. Ort ; Sandra Ort | 2010–2024 | greene-township | R |
| sandra-robbins | Sandra J. Robbins ; Sandra Robbins | 2018–2022 | clay-township | R |
| scott-searfoss | Scott D. Searfoss ; Scott Searfoss | 2026–2027 | warren-township | D |
| sean-coleman | Sean Coleman ; Sean J. Coleman | 2018–2019 | portage-township | D |
| sean-o-brien | Sean Bertrand O'Brien ; Sean O'Brien | 2018–2027 | clay-township | D |
| shane-whitmer | Shane Elliot Whitmer ; Shane Whitmer | 2010–2027 | greene-township | R |
| sheila-bergeron | Sheila A. Bergeron ; Sheila Ann Bergeron ; Sheila Bergeron | 2010–2012 | sbcsc, south-bend | NP, R |
| sheila-niezgodski | Sheila A. Niezgodski ; Sheila Ann Niezgodski ; Sheila Niezgodski | 2015–2025 | south-bend | D |
| sherry-bolden-simpson | Sherry Bolden-Simpson ; Sherry L Bolden-Simpson ; Sherry L. Bolden-Simpson | 2023–2025 | south-bend | D |
| stephanie-ball | Stephanie Ball ; Stephanie D Ball | 2019–2027 | county, sbcsc | D, NP |
| steve-luecke | Stephen J. Luecke ; Stephen Luecke ; Steve Luecke | 1988–2007 | south-bend | D |
| steven-bradley | Steven Bradley ; Steven Clark Bradley | 1999–1999 | south-bend | R |
| sue-dittmar | Sue A Dittmar ; Sue A. Dittmar ; Sue Dittmar | 2010–2022 | liberty-township | R |
| susan-moffitt | Susan I. Moffitt ; Susan Moffitt | 2011–2019 | new-carlisle | D |
| tami-springer | TAMARA "TAMI" SPRINGER ; Tamara "Tami" Springer ; Tamara Springer ; Tami Springer | 2018–2025 | county, penn-township | D |
| tera-klutz | Tera K Klutz ; Tera Klutz | 2018–2022 | state | R |
| terri-buckmaster | Terri Buckmaster ; Theresa (Terri) Buckmaster | 2015–2025 | walkerton | D |
| terri-rethlake | Terri J. Rethlake ; Terri Rethlake | 2010–2014 | county | D |
| terrie-bickel | Terrie Bickel ; Terrie L Bickel | 2022–2027 | madison-township | R |
| thomas-lindenman | Thomas J Lindenman ; Thomas J. Lindenman ; Thomas Lindenman | 2010–2027 | centre-township | R |
| thomas-mcclanahan | Thomas McClanahan ; Thomas O. McClanahan | 2010–2019 | german-township | D |
| thomas-schmidt | Thomas R. Schmidt ; Thomas Schmidt | 2003–2003 | south-bend | R |
| thomas-smith | Thomas Kevin Smith ; Thomas Smith | 2012–2020 | union-north | NP |
| thomas-strang | Thomas R Strang ; Thomas Strang | 2026–2027 | union-north | NP |
| tim-creason | Tim Creason ; Timothy T. Creason | 2022–2027 | olive-township | R |
| tim-wesco | Tim Wesco ; Timothy Wesco | 2010–2026 | in-house, state | R |
| timothy-jaycox | Timothy J Jaycox ; Timothy Jaycox | 2020–2024 | in-house, state | R |
| tina-miller | Christina (Tina) Miller ; Tina Miller | 2023–2024 | osceola | R |
| todd-mcgaughey | Todd A McGaughey ; Todd McGaughey | 2022–2027 | john-glenn | NP |
| tom-england | Thomas England ; Thomas S England ; Tom England | 2014–2027 | north-liberty | R |
| tom-mccormick | Tom E McCormick ; Tom E. McCormick ; Tom McCormick | 2018–2027 | county, liberty-township | R |
| tony-hazen | ANTHONY "TONY" HAZEN ; Anthony "Tony" Hazen ; Anthony (Tony) Hazen ; Tony Hazen | 2019–2025 | county, mishawaka | R |
| tony-imel | Tony H. Imel ; Tony Imel | 2014–2018 | warren-township | D |
| tony-violi | Anthony "Tony" Violi ; Tony Violi | 2023–2025 | mishawaka | D |
| troy-warner | Troy D. Warner ; Troy Warner | 2019–2025 | south-bend | D |
| valerie-schey | Valerie S. Schey ; Valerie Schey | 2011–2012 | south-bend | D |
| vicki-kitchen | Vicki Kitchen ; Vicki L Kitchen | 2019–2025 | north-liberty | R |
| victor-cummings | Victor CC Cummings ; Victor Cummings | 2026–2027 | county | D |
| wendy-yuhasz | Wendy L. Yuhasz ; Wendy Lu Yuhasz ; Wendy Yuhasz | 2018–2027 | warren-township | D |
| william-davis | William (Bill) Davis ; William F. Davis | 2007–2012 | county, south-bend | D, R |
| william-groves | William Groves ; William S. Groves | 2010–2019 | john-glenn | NP |
| woody-emmons | Dale "Woody" Emmons ; Dale (Woody) Emmons ; Woody Emmons | 2011–2025 | mishawaka | D |
