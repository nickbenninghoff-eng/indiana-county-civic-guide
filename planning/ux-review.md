# UX / Information-Architecture Review: St. Joseph County Civic Guide plan

Reviewer stance: adversarial. Reviewed 2026-11-07 against the research in `research/` (01–09, results 2010–2026, county campaign-finance filings). Nothing has been built, which is when these changes are cheapest.

**Bottom line.** The plan is a table of contents for a reference book, organized the way governments organize themselves (by unit: county, South Bend, Mishawaka, townships, state, money, people). Nobody arrives with "I'd like to learn about the county" as their question. They arrive with "who do I call," "what's on my ballot," "could I run," "where does my tax money go," or "is this thing biased." The research is strong enough to answer those questions well, but the plan buries the answers inside institution chapters, puts thin or derived data on the same footing as official data, and leaves three spots where a skeptical reader can fairly call the whole guide partisan. Fix the architecture first. Visual polish comes after.

---

## 1. Persona walkthroughs

Six personas. Persona 6 (operative) was added at the owner's request as a stress test of depth. How each persona uses the social and economic context layer is covered in section 3.5.

### 1.1 New resident, late 20s, votes only in presidential years

**What they try first.** They land on the page and look for something about *them*. The plan's first block is a "who represents me" ladder from state to schools. They read the explanation of each level, which is fine, but nothing tells them **which** township, school corporation, or council district they live in. St. Joseph County has 13 townships, 2 cities, 7 towns, at least 5 school corporations and 9 county council districts. A generic ladder says "you have a township trustee." It can't say "yours is Penn Township's trustee and your schools are PHM."

**Where they get stuck.**
- **The pothole.** Their actual question is "who fixes the road outside my apartment?" The answer depends on whether it's a city street, a county road or a state route. The plan has no service-to-government map at all ("who does what"); it has org charts. Org charts answer "who reports to whom." They don't answer "who do I call."
- **The election calendar is a wall.** "Which offices are up in which year (now–2030)" will render as a big table. What they need is one sentence: *"Your next election is the May 2027 city primary if you live in South Bend, Mishawaka or a town. If you live outside a city or town, nothing is on your ballot until 2028."* (Confirm 2027 town-election coverage and the primary date against IC 3-10 before publishing.) The calendar has the data to produce that sentence, but the plan doesn't ask it to.
- **"Why local elections matter" has no hook.** The strongest neutral fact in the research is turnout. The 2022 primary turnout was **7.46%** of registered voters and the 2023 municipal primary was **9.12%** (official county canvass). In practice, primaries decide many local seats. That fact should be on the first screen. The plan files it nowhere.
- **Staleness trap.** Their township trustee, plus most county row offices and three to five council seats, turn over on **Jan 1, 2027**, eight weeks from today. If v1 ships a static "current officeholders" list, it goes wrong for half the county on New Year's Day.

**What they want instead.** A "Find my governments" picker (city/town or township, then school corporation), a "Who handles this?" service list (roads, trash, police, schools, property-tax appeals, township assistance, library), and a single "your next vote" line. That's three screens at most. Everything deeper can stay optional.

### 1.2 Community-group organizer / civics teacher

**What they try first.** They want to send one link for a 45-minute session: "read this before Tuesday." On a single long page, the best they can do is "scroll to Money (budgets)." There are no lesson-sized units, no time estimates, no discussion prompts and no print version.

**Where they get stuck.**
- **Deep links aren't really planned.** "Jump-to menu" and "in-page navigation" usually mean anchors that break when sections are renamed, and that hand the student a 50-screen page with no clear stopping point.
- **Printing.** A long page with interactive charts prints badly: blank charts, cut tables, no source URLs. Teachers print things. Group organizers hand out paper at library meetings.
- **Cover for the room.** Before showing this to a class, a teacher needs a visible "about / methods / nonpartisan policy / who made this" page they can point a parent or principal to. The plan's last section, "Sources and get involved," mixes sources with calls to action. "Get involved" next to a page about the 2026 Democratic gains is exactly what an upset parent screenshots.
- **The South Bend budget cliff.** A teacher putting the budget chart on a projector will get the question "why did South Bend's budget drop from $427M to $170M in 2024?" The real answer is that state reporting changed (Gateway lists only 10 property-tax-supported funds from 2024 on). If the chart doesn't answer that in the chart itself, the teacher is stuck, or worse, a student walks away believing the budget was cut by 60%.

**What they want instead.** Separate, stable URLs per topic. Paths with a stated length ("4 stops, about 40 minutes"). A print stylesheet that prints the "as of" date and source URLs. A one-page handout for the three core topics. A methods/neutrality page they can cite.

### 1.3 Engaged voter considering a township board or school board run

**What they try first.** They look for "how to run," and the plan has put it inside the election calendar section, as one bullet among four.

**Where they get stuck.**
- **Timing is the whole story, and the plan doesn't surface it.** Township trustees and boards were just elected (Nov 2026) for terms through 2030. Unless the research turns up staggered terms, the next regular township election is **2030**. For the next four years, the realistic way onto a township board is a **party caucus** filling a vacancy. Precinct committeepersons vote in that caucus, and they're elected in primaries. This guide's runner needs to hear that becoming a precinct committeeperson is the actual entry point. The data supports it: 225 precinct-committee/delegate filings in 2026 alone, plus documented caucus cases (Baxmeyer 2022, Hazen 2022, Beidinger 2026, Dawn Jones 2019). The plan treats caucus vacancies as a calendar footnote.
- **School boards just changed.** SEA 287 (2025) let school board candidates list a party for the first time, starting Nov 2026, and it created a "two-primary" affiliation rule that nearly knocked IPS candidates off the ballot. For a would-be school board candidate this is the most important fact in the guide. In the plan it lives in the schools section under "what they do, who's on them."
- **Mechanics gaps.** The research says primary filing deadlines were **not retrieved** (the 2026 candidate guide 404'd), and IC 3-13-11 caucus rules were only partly fetched. A "how to run" page that guesses here could hurt someone. They could miss a deadline.
- **Money.** They want to know what a township or school board race costs. There is **no** local campaign-finance data before 2023, and township/school data for 2018–2026 is "nothing." The plan's "local candidate reports 2023+" implies more than exists.

**What they want instead.** A "Run for office" path organized by office: eligibility, term, next regular election, how a vacancy gets filled, the forms (CAN-2, CAN-34 petition for school board, CAN-37 for precinct committee), where to file, and the finance obligations (CFA-1 committee, CFA-4 reports). Each item needs a statute or SOS link, and gaps should be labeled "verify with the County Voter Registration office" instead of guessed.

### 1.4 Skeptical partisan (either side)

Walk through it as a Republican first, then as a Democrat.

**Republican reader:**
- The county section's headline element is **"2026 shift in party control."** It's the most recent and most partisan-salient fact, the results behind it are **unofficial**, and it sits in the first institutional chapter. To this reader it reads as a victory lap.
- They open "Notable people." From the research list, a rough count: Democrats Brademas, Roemer, Kernan, Luecke, Buttigieg, Mueller, Donnelly, Bauer (x2), Dvorak (x2), Fry, Niezgodski (x2), plus the council "firsts." Republicans: Colfax (19th century), Hiler, Walorski, Mishler, Beutter, and possibly Rea and Wood. The research itself flags an "era imbalance... thin for 20th-century Republicans." The page will look like a Democratic hall of fame, with the sitting Democratic mayor profiled ahead of his own 2027 race.
- They open campaign finance. The only transcribed local figures are 14 usable rows from one filing tab, and they include the **Drake and O'Brien PAC (~$129k receipts)** next to partial or missing numbers for others. Selective transcription looks like opposition research.
- The 2021 redistricting narrative in the notes ("Republican-majority commissioners passed maps giving them a 2-1 advantage") attributes motive. Unless each claim is attributed ("WVPE reported...") and both sides' stated positions appear, this reader will say the guide editorializes.

**Democratic reader:**
- They see "first Republican council majority" (2022) and "GOP flips clerk, assessor" pulled from headline language, and Colfax's Credit Mobilier scandal and Bauer's walkout listed as "controversies." They ask why Walorski's entry has no controversy line, and why the guide notes Dvorak's non-prosecution decision in the Seeberg case. Whichever way it's done, inconsistent controversy rules will be read as targeting.
- They notice that the April 2026 ruling against the district-commissioner system (which affects their party's fortunes) is reported with no judge, case name or appeal status. That makes it look like a rumor the guide chose to amplify, or chose to downplay.

**Both:** photos. With about 25 licensed images, some officials will have portraits and others won't. Whoever gets a face looks "notable." Bigger cards, a larger photo, or a higher position on the page all read as emphasis.

**What they want instead:** visible selection rules applied mechanically, a disclosed count by party with an explanation if it skews, no "notable" treatment of anyone currently on a ballot or about to be, data shown as a full-range timeline (not a "shift" headline), and identical formatting for both parties everywhere.

### 1.5 Elkhart County resident who gets a link from a friend

**What they try first.** The friend shares a deep link to the budgets section. The link preview (og:title) says something like "Money: budgets," with no county. They click, see "County budget $248M," and some will assume it's *their* county.

**Where they get stuck.**
- The plan has **no edition identity at all** beyond the requirement. If the county name shows only on the landing page, every deep link and every screenshot loses it.
- Half the content *does* apply to them: how Indiana elections work, township law, SEA 1, the General Assembly, caucus rules, campaign-finance forms. The plan doesn't mark which parts those are, so they can't tell what's reusable.
- They may share legislators with St. Joseph. Research lists HD 21 (Wesco) and SD 9 (Mishler) as touching the county, and those districts plausibly cross into Elkhart or Marshall (verify against iga.in.gov). "Your legislators" is the single most likely place a neighbor-county visitor finds themselves, and the plan presents it as St. Joseph-only.

**What they want instead.** The county name on every page and in every share preview, a "Not St. Joseph County?" control showing the 92-county map with which editions exist, a "This chapter applies to every Indiana county" badge on generic chapters, and a note on legislative pages that districts cross county lines.

### 1.6 Local political operative (either party)

This persona is a **stress test of depth and data usefulness**. The guide doesn't serve them as a client. Most of what they want (margins, turnout, open seats, what campaigns cost, ballot mechanics) is neutral public information that every reader benefits from, including a first-time candidate of any party, a reporter, or a teacher explaining why primaries matter. The test: if the guide can answer the operative's factual questions, using the same metrics for both parties, it has real depth. If it can't, it's a brochure.

**What they try first.** They skip the paths and go straight to results, wanting a sortable table: every race 2010–2026, winner, margin in points, open seat or incumbent, turnout. The plan offers "results history" charts inside each unit chapter (county, South Bend, Mishawaka), so they'd have to click through five chapters and read charts to rebuild a table the guide already has internally. Their first reaction: "Just give me the CSV."

**Where they get stuck, by question:**

| They want | What the data supports | What the plan offers | Gap |
|---|---|---|---|
| **Competitive vs safe seats, margin trends** | Yes. Official results for every county race 2010–2026; margins are computable. The research already shows razor-thin races: Council B 2022 decided by 35 votes, Surveyor 2024 by 171, Treasurer 2024 by about 1,450. | Per-unit results charts | No cross-race margin view; no per-seat margin history across cycles. |
| **Turnout: odd-year municipal vs even-year** | Yes, and it's striking. 2023 municipal general **14.88%**, 2023 municipal primary 9.12%, vs 2024 general 54.53%, 2026 general 40.17% (unofficial). Note the denominators differ: municipal elections count only city/town registrants (about 115k vs about 194k). | Not planned | A turnout panel with the denominator explained, so nobody compares 15% of 115k to 40% of 194k as though they were the same base. |
| **Open seats, term-limited incumbents, upcoming vacancies** | Partly. Row officers are limited to 8 years in 12 (Redman was term-limited in 2026). Retirements are known from news (Cotter). Computing *future* term limits needs accurate first-elected dates, and row-officer history before 2020 is partial. | Not planned | An "Up next" table per cycle: seat, incumbent, first took office, term-limit status (COMPUTED), announced retirements (SINGLE SOURCE until confirmed). |
| **Caucus-appointed incumbents** | Yes, and it's bipartisan in the data: Baxmeyer (R, 2022) and Hazen (R, 2022) on the commissioners; Beidinger (D, 2026) on the SB council; Dawn Jones (D, 2019) as SB clerk. | Caucus vacancies appear as a calendar footnote | Every officeholder record should carry "first took office by: election / caucus / appointment." |
| **Straight-ticket share** | Partly. Straight-party totals are printed in county summaries 2010+, though 2010–2014 values are OCR. The share needs a ballots-cast denominator. Indiana's rules on what a straight-party vote covers have changed over the period; the research marks this "not found," so it has to be verified per year. | Not planned | A straight-party trend can only ship once the rule for each year is sourced. Otherwise the trend line mixes different ballots. |
| **Fundraising benchmarks** ("what a winning township / council / mayoral race costs") | **Mostly no.** Local reports exist only from 2023, as scans, with 14 usable rows transcribed. Mayoral 2019/2023 raised/spent: not found. Township/school: nothing. State legislators 2016–2026: yes. | "Local candidate reports 2023+" | Benchmarks can honestly exist only for state legislative races in v1. Local benchmarks need full transcription of a defined set, shown as a distribution of *all* candidates (winners and losers), with n stated. |
| **Ballot-access mechanics and deadlines** | Partly. Forms and petition rules are known; primary filing deadlines were **not retrieved**. | Bullet in calendar | Same fix as the Run path. It serves this persona identically. |
| **Party organization** (precinct committeepersons, chairs) | Partly. 225 precinct-committee/delegate filings in 2026; caucus statute partly fetched; "county chairs elected by committeepersons" is L-confidence. | Not planned | A neutral "How parties are organized under Indiana law" explainer, the same for every party with ballot access. |
| **Where the data comes from** | Yes. Sources are excellent and public: county results archive, Gateway bulk download, state CF bulk data, county filings page. | "Every figure linked" | No data-download page, no source inventory with notes on how to pull it, no precinct-file pointers. |

**What they want instead.** A results explorer with a margin column, a turnout panel, an "up next" open-seats table, and a `/data/` page with CSVs and source instructions. Every one of those is neutral if built symmetrically, and every one also serves the candidate (1.3), the teacher (1.2) and the skeptic (1.4), who wants to check the guide's numbers. They also want things the guide should refuse (below).

**What the guide should NOT provide, and why:**
1. **"Target," "pickup opportunity," "vulnerable incumbent," "battleground," or "flippable" labels, and any ranking of seats by one party's prospects.** These are strategy judgments that inherently take a side. Neutral form: margins shown as numbers, sorted by closeness regardless of who won.
2. **Forecasts, projections or "likely to" language** about future races. Prediction isn't education, and a wrong forecast becomes the bias story.
3. **Strategy advice of any kind** ("where to spend," "which precincts to canvass," "how to win a caucus"). The guide explains *how the caucus works*; it doesn't coach anyone to win one.
4. **Precinct-level targeting visualizations** (precinct maps of party strength, turnout-gap maps). Precinct results are public, so link the county's precinct files on `/data/`. But building targeting maps is the operative's job. There are also no official precinct boundary files in the research, so any precinct map would be inaccurate.
5. **Voter-file or individual-voter data** (who voted, vote history, contact info). It's out of scope for public education, it's sensitive, and use of the voter list is governed by state rules the guide shouldn't test.
6. **Donor contact lists.** Show committee totals, size distributions and contributor names *as they appear in official filings*, linked to the filing. Don't publish addresses or employers as a browsable or downloadable list; that serves solicitation, not understanding.
7. **Opposition-research dossiers** on individuals (votes, quotes, controversies compiled per person). The people-selection and controversy rules (section 6) already block this.
8. **Party-specific "how our side did" summaries.** Every summary covers all parties on the ballot.

**Do the operative and the skeptical partisan pull in opposite directions?** Yes, in four places. Each has a symmetric resolution:

| Tension | Operative wants | Skeptic fears | Resolution |
|---|---|---|---|
| Competitiveness | "Which seats are in play?" | A ranked list that implies one party's targets | Show **margin in points** for every race, sorted by margin regardless of party, with the margin bands defined in methods (e.g., under 5 pts / 5–15 / over 15) and applied mechanically. No forward-looking labels. The same view for every reader. |
| Caucus incumbents | Flag appointed incumbents as a weakness | "Unelected" framing used against one party | A neutral field on *every* officeholder ("took office by caucus, Aug 2022; later won election Nov 2022"). Never a separate "unelected" list. The data is bipartisan anyway. |
| Money depth | More dollar figures, sooner | Selective transcription that looks like opposition research | Only complete, defined sets. The coverage matrix shows exactly what's in and out. |
| Granularity | Precinct-level detail | A targeting tool wearing a civics costume | Countywide and district-level views in the guide; precinct files linked on `/data/`, not visualized. |

The resolving principle: **describe the past and the rules; don't evaluate the future.** Everything backward-looking and mechanical (margins, turnout, terms, filing rules, money totals) goes in, identically for all parties. Everything forward-looking and evaluative (targets, forecasts, advice) stays out. One place they *agree*: the operative's demand for raw data and sources is exactly what the skeptic needs to audit the guide. A strong `/data/` page is a neutrality feature, not a partisan one.

---

## 2. Ranked problems with the current plan

| # | Severity | Problem | Concrete fix |
|---|---|---|---|
| 1 | **Blocker** | **Organized by institution, not by question.** 11 parallel chapters, each internally complete, none answering what people arrive asking. The landing requirement ("easy to choose a path") can't be met when the sections *are* the paths. | Two layers: **reference pages** (by government/topic, which is where the research naturally lives) and **learning paths** (curated sequences of short "stops" across those pages). See section 3. |
| 2 | **Blocker** | **Officeholder data goes stale on Jan 1, 2027.** Most county row offices, council A/B/C/E/H, Commissioner D1, and all 13 township trustees/boards change hands. The trustee roster is also low-confidence (BallotReady, party unknown). | Model officeholders as **terms** (person, office, start, end, how selected, source), and render "current" from today's date. During Nov 3–Dec 31 show "Serving until Dec 31 / Takes office Jan 1 (results unofficial)." Ship no roster that's typed in by hand. |
| 3 | **Blocker** | **Budget charts will mislead.** The South Bend $427M to $166M Gateway series break, county "$90M vs $248M" (general fund vs all funds), and Mishawaka figures excluding utilities. Side-by-side "budgets" across units mix three different measures. | Every money figure carries a `basis` (general fund / advertised funds / all funds incl. utilities). Charts never splice bases. Series breaks are drawn *on the chart* as a gap with an inline note. A "What counts as a budget?" explainer opens the money chapter. Cross-unit comparisons use one basis only, and per resident. |
| 4 | **Blocker** | **Campaign finance can't meet "every race" and is currently selectively transcribed.** Local: scanned images, 2023+ only, 14 usable rows from 1 of ~16 tabs, OCR-uncertain values. Showing partial local numbers is bias by omission, even when it's accidental. | v1 local campaign finance = **coverage matrix** (which offices × which reports exist, are posted, are transcribed) + "how to read a CFA-4" + where to look. Publish local dollar figures only for a *complete, defined set* (e.g., every candidate committee in the 2026 Pre-General tab), visually verified, never a sample. State legislators 2016–2026 from bulk data can ship, with the spelling-variant undercount caveat. |
| 5 | **Major** | **"Notable people and families" is a bias magnet.** The research shows party and era skew, inconsistent controversy notes, sitting officials (Mueller, Mishler) included, and uneven photos. | Rename to **"People who shaped local government."** Publish entry rules (section 6) and apply them mechanically. No living person who holds office or is a declared candidate gets a profile card; they appear only in the officeholder directory. Controversies only when a documented official finding exists (investigation, court ruling, censure), applied to everyone. Show the party/era distribution of the set. |
| 6 | **Major** | **Headline framing of the 2026 results** ("2026 shift in party control") is recency- and party-salient, and unofficial. | Replace with a full-range **party-control timeline** for each body (Council, Commissioners, SB Council, General Assembly), as long as the data runs, with 2026 as the latest point, labeled UNOFFICIAL. No "shift," "sweep," or "flip" in headings. |
| 7 | **Major** | **Single page is the wrong container.** About 550KB of research becomes dozens of tables, a 33-mayor timeline, 15 years × ~25 units of budgets, and 2010–2026 results. One page means slow loads on phones, unusable deep links, impossible printing, no per-topic link previews, and no way to share generic chapters across editions. | **Multi-page static site** (section 3). |
| 8 | **Major** | **No address/place resolution, and no maps to support it.** "Who represents me" without telling people *which* district they're in fails the new resident. The research found no reusable district maps. | v1: a **place picker** (city/town/unincorporated township + school corporation), which is a finite list, plus a prominent hand-off to the Indiana Voter Portal (indianavoters.in.gov) for exact districts and sample ballot. Get county GIS district files later for a real lookup (v2). |
| 9 | **Major** | **"How to run" buried in the calendar; caucus/precinct-committee path absent; key mechanics unverified** (filing deadlines not retrieved). | A dedicated **Run for office** reference page plus path, organized by office. Every deadline links to SOS/IC; any gap is shown as "confirm with Voter Registration" with that office's contact info. Include "become a precinct committeeperson" as the entry point for caucus vacancies. |
| 10 | **Major** | **Services ("who does what") missing.** Org charts show hierarchy. People need responsibility. | A **"Who handles this?"** table: service → responsible unit(s) → elected official accountable → contact. Roads need a three-way split (city / county highway / INDOT) with "it depends" stated honestly. This needs a short research task (the gap is noted in section 7). |
| 11 | **Major** | **Courts omitted.** Circuit and Probate judges are elected on partisan ballots; Superior Court judges face **retention votes**, a merit-selection system research says only St. Joseph and one other county use. Retention questions are on voters' ballots and baffle them. | Add courts to the county reference page and to "Vote smarter" ("What is a judicial retention question?"). |
| 12 | **Major** | **Appointed boards with real power are invisible:** Redevelopment Commission, Board of Health, library boards, Airport Authority, Board of Public Works. This is where much of the "real complexity" is, and the owner's requirement 4 asks for exactly that. | Add an "**Unelected but powerful**" panel on each unit page: board, what it decides, **who appoints the members**. This ties accountability back to an elected official. |
| 13 | **Major** | **Towns and unincorporated residents are second-class.** The plan has full chapters for South Bend and Mishawaka. The 7 towns (Lakeville, Walkerton, North Liberty, New Carlisle, Osceola, Roseland, Indian Village) and rural township residents are lumped into section 6. | Generate a **place page** per city, town and township from the same template. Thin data shows as explicit "not yet researched" states, not empty boxes. |
| 14 | **Major** | **No cross-race "landscape" layer.** Results are scattered as per-unit charts. There's no margin view, no turnout comparison across odd/even years (14.88% vs 54.53%), no open-seat/term-limit table, and no record of how each incumbent first took office. The depth exists in the data but is invisible (persona 1.6; also serves 1.1, 1.3). | Add `/elections/landscape/`: a sortable results explorer with a margin column, a turnout panel with denominators explained, an "Up next" table (seat, incumbent, first took office by election/caucus, term-limit status COMPUTED), and straight-party share **only** for years where the straight-ticket rule is sourced. Same metrics for every party; sorted by margin, never by party; no forward-looking labels. |
| 15 | **Major** | **No data downloads or source inventory.** "Every figure linked" means one link per number. It doesn't let anyone check the guide's math or extend it. | Add `/data/`: CSV per table (results, terms, budgets, tax rates, CF coverage) with source and status columns, plus a "how to pull this yourself" note per source (county results archive, precinct files, Gateway bulk POST, state CF bulk CSVs, county filings page). This serves operatives, journalists and skeptics alike. |
| 16 | **Major** | **New scope (social and economic context) has no home and a built-in causation trap.** If demographics land on government or results pages ad hoc, readers will infer "this group caused that result," and partisans will read selection choices as framing. | One home (`/community/`), identical Context cards per unit, a landing strip kept away from election visuals, and demographics-and-voting discussed only through attributed published research with ecological-fallacy framing (section 3.5). Built as a re-runnable, FIPS-parameterized shared layer. |
| 17 | Minor | **"Mishawaka: same structure as South Bend"** but the data is much thinner (no mayors list; Wikipedia list 404'd; council party not shown). An identical template with empty slots looks broken. | Same template, with per-block **coverage badges** ("Mayors before 1979: not yet found"). Hide blocks with zero data and show a single "Gaps" list instead. |
| 18 | Minor | **The ladder runs state → schools (top-down).** Lived experience runs closest-first. | Order by proximity: city/town → township → schools → county → state. Show "levels" as overlapping layers, not a ladder (a ladder implies hierarchy; Indiana units are mostly *parallel* creations of the state, not subordinates of each other). |
| 19 | Minor | **"How a bill becomes law"** is generic and widely available; it spends space that county-relevant state content needs. | Replace with "**How the state shapes your local government**": home rule (IC 36-1-3), property-tax caps, SEA 1-2025 and HB 1210-2026, school funding formula, state-set election rules. Link out for bill process. |
| 20 | Minor | **Population since 1850** and the 33-mayor timeline are history, but they sit in the city chapters where people go for current facts. | Move to the History path/reference page. City pages show only the current structure plus the recent series. |
| 21 | Minor | **"Search" as a v1 requirement.** It costs real work on a single page and adds little over a good index. | On a multi-page static site, add Pagefind (static, near-free) late in v1, or defer. A good A–Z "Offices and terms" index matters more. |
| 22 | Minor | **"Every figure linked to its source" isn't enough.** Research tags confidence H/M/L, and some facts are OCR, derived, or "general knowledge." | Claim-level **status badges** (section 6), a methods page, a corrections log and a changelog. L-confidence or "general knowledge" facts never appear in headings or charts. They get verified or cut. |

---

## 3. Recommended information architecture

### 3.1 Single page or multi-page: **multi-page**, clearly

Single-page fails on every persona's key need:
- **Teachers** need stable, assignable, printable units.
- **Sharers** need per-page link previews that carry the county name.
- **The series** needs generic chapters shared across editions as *pages/modules*, not as sections cut out of a monolith.
- **Phones**: one page holding 2010–2026 results plus 15 years of budgets is too heavy.

Build a static multi-page site from data files (JSON/CSV in `data/`) through templates: one template per page type (place page, office page, election page, path stop). About 20–30 pages in v1. Navigation is a persistent header with five path entry points plus a "Reference" menu. Each page should be readable in 5–12 minutes.

### 3.2 Two layers: Reference and Paths

**Reference** is the encyclopedia: every page is complete on its topic and organized by government or topic. **Paths** are curated sequences of 4–7 *stops*. Each stop is one section of one reference page, shown with a path header ("Run for office · Stop 3 of 6 · How vacancies are filled"), a short "why this matters for your goal" lead-in, and "Next stop →" at the bottom. Path state lives in the URL (`?path=run&stop=3`), so a shared link keeps the path context. Nothing is written twice: the path is a playlist over reference content.

### 3.3 Revised sitemap (v1)

```
/                                   Landing (edition masthead, complexity visual, path cards)
/your-governments/                  Find my governments (place picker -> list of your units & seats)
/who-handles-this/                  Service -> responsible government -> accountable official
/elections/                         Indiana elections: how they work [GENERIC]
  /elections/calendar/              What's on the ballot when, 2026-2030 (county-filled cycle strip)
  /elections/results/               Results explorer 2010-2026 (filter by office/year; status badges)
  /elections/judges-and-questions/  Judicial retention, public questions, school-board party labels
  /elections/landscape/             Elections by the numbers: margins (every race, sorted by closeness),
                                    turnout odd vs even years (denominators explained), "Up next" open
                                    seats & term limits, how each incumbent first took office,
                                    straight-party share (only years with a sourced rule)
/run/                               Run for office [GENERIC rules + county contacts]
  /run/<office-type>/               Township board, school board, council, trustee, precinct committee
/places/                            All cities, towns, townships (cards)
  /places/south-bend/               Structure, council districts (schematic), offices & terms, budget link
  /places/mishawaka/
  /places/<town>/  /places/<township>/   (template-generated; coverage badges)
/county/                            County government: council, commissioners, row offices, courts,
                                    appointed boards, party-control timeline, commissioner-district litigation
/schools/                           School corporations: structure, board seats, SEA 287 change, referenda
/state/                             State government as it touches the county
  /state/your-legislators/          Districts touching the county (+ "districts cross county lines")
  /state/how-the-state-shapes-local/  Home rule, tax caps, SEA 1, LIT changes [GENERIC]
/money/
  /money/what-is-a-budget/          Definitions primer (general fund / advertised / all funds) [GENERIC]
  /money/your-tax-bill/             How one property-tax bill is split among taxing units (rates by unit)
  /money/budgets/                   Budgets by unit 2012-2026, single basis per chart, breaks marked
  /money/campaigns/                 How campaign finance works [GENERIC] + coverage matrix + state legislators
/community/                         The community: social & economic context (see 3.5)
  /community/people/                Population over time, age, race/ethnicity, households (Census categories)
  /community/income-and-work/       Income, poverty, employment by industry, major employers (sourced)
  /community/housing-and-education/ Tenure, values/rents, attainment, enrollment
  /community/research-on-voting/    What published studies say about place, economy and voting (attributed)
/history/                           Party-control timelines, mayors timeline, turning points,
                                    economic turning points (e.g., Studebaker's South Bend closure, 1963)
  /history/people/                  People who shaped local government (rule-based)
/data/                              CSV downloads + source inventory + "how to pull it yourself"
/teach/                             Lesson kits: path, time, prompts, printable handouts
/about/                             Methods, neutrality policy, status badges, who made this,
                                    corrections log, changelog, sources index
```

### 3.4 Learning paths (v1: five primary, two secondary, plus a teacher entry)

| Path card | For | Stops (each is a section of a reference page) | Time |
|---|---|---|---|
| **Who does what?** | New resident | Find my governments → Who handles this → Unelected but powerful (one example) → How to contact/attend a meeting | ~15 min |
| **Vote smarter in your next election** | Occasional voter | What's on your next ballot → What each office actually controls → Results history for those offices (turnout first) → Judges & public questions → Where to find candidate info (Voter Portal, filings) | ~25 min |
| **Run for office** | Prospective candidate | Pick an office → Eligibility, term, next regular election → Ballot access (primary / petition / school-board label) → Vacancies & caucuses → Precinct committeeperson → Campaign-finance obligations → Contacts | ~40 min |
| **Follow the money** | Engaged citizen, teachers | What counts as a budget → Your tax bill split by unit → Budgets over time (one basis) → How the state limits local revenue (caps, SEA 1) → Campaign money: what's public, what isn't | ~35 min |
| **How we got here** | History-minded, classes | Party-control timelines → Mayors timeline → Economic turning points (e.g., Studebaker 1963) → Political turning points (redistricting 2021, Bauer's 50 years, Brademas/Hiler, etc.) → People who shaped local government | ~35 min |
| **Elections by the numbers** | Candidates, reporters, operatives, data-minded voters | Turnout odd vs even years → Margins in every race → Up next: open seats & term limits → How incumbents took office (election / caucus) → Where the data comes from (`/data/`) | ~25 min |
| **Know your community** | New residents, teachers | Who lives here (population, age, households) → Work and income (industries, employers, poverty) → Housing and schools → How the tax base shapes budgets (links Follow the money) | ~25 min |
| *For teachers & groups* | Organizers | Links to `/teach/`: each path as a lesson with objectives, prompts, handout PDF/print view | n/a |

Rule: a path never contains a claim that isn't on a reference page. Paths add only framing sentences, and those follow the same neutrality rules.

The landing page shows the first five paths as cards. "Elections by the numbers" and "Know your community" appear as a second row of smaller cards, so the first screen stays a five-way choice (see wireframe).

### 3.5 Social and economic context ("The community")

The research for this is in progress in `research/10-demographics-economy.md`, which didn't exist when this review was written. The recommendations below are about structure and framing, not specific numbers.

**Placement: a mix, with one rule.** Give it one home and draw small, linked excerpts elsewhere.
1. **Home: `/community/`**, a reference section with four pages (sitemap above). This is where the full tables, trends, definitions, margins of error and sources live, and the only place that discusses published research on voting.
2. **Woven in: a "Context" card on each place and school page**, showing the same 5–6 indicators for every unit (population, median household income, poverty rate, owner-occupied share, bachelor's-or-higher share, and population change since 2010), each linked to `/community/`. Census geographies line up with Indiana's government units almost one to one: county (FIPS 18141), **places** (cities and towns), **county subdivisions** (Indiana townships are Census minor civil divisions), and **school districts** (including SAIPE child-poverty estimates). That makes this layer unusually clean, and it gives the budget pages a real per-resident denominator.
3. **Landing: a small backdrop strip, not the hero.** One line below the path cards: "St. Joseph County: [population] people · [N] jobs · largest employers include [sourced list] → Know your community." The hero stays about government overlap. Demographics must not sit next to party-control or results visuals on the landing page, because putting them side by side implies a relationship.
4. **History:** economic turning points (Studebaker's 1963 closure of South Bend production, population trend) go on the History timeline alongside political events, sourced. That's where cause-and-effect narratives naturally get asked, so the framing rules below apply with full force there.
5. **The rule:** demographic and economic data appears **alongside government data only as context for that unit** (per-resident budgets, tax base), **never overlaid on election results** in the guide's own charts. The relationship between demographics and voting is discussed *only* on `/community/research-on-voting/`, through published analyses.

**How each persona uses it**

| Persona | Use | Risk to manage |
|---|---|---|
| New resident (1.1) | "What kind of place did I move to?" Employers, housing, schools context. | Minimal. Keep it short and plainly worded. |
| Teacher / organizer (1.2) | Strong lesson material: why do South Bend's and Mishawaka's budgets differ (tax base, utilities)? What did losing Studebaker do to a city's finances and population? Students can compare their own township's Context card with others'. | Classroom discussion slides into "which groups vote which way." Provide a lesson prompt that teaches the **ecological fallacy** directly. That turns the risk into a learning objective. |
| Candidate (1.3) | Understand the district they'd represent: population, housing tenure, school enrollment. | Same as the operative, on a smaller scale. |
| Skeptical partisan (1.4) | Hunts for loaded selection: emphasizing poverty in one city as "decline," listing employers as boosterism, treating Notre Dame's tax-exempt status as a scandal, or a "research on voting" page that only cites studies flattering one side's voters. | Fixed indicator set applied to every unit; Census category names verbatim; employers chosen by a published rule (e.g., top N by employment from a named source); research page cites analyses by a stated inclusion rule, with each study's geography, period, method and authorship shown. |
| Operative (1.6) | Wants demographic × precinct vote overlays for targeting, and "which groups are persuadable." | **Decline in the guide.** That is targeting, and precinct-level demographics don't exist as clean Census geography anyway (precincts aren't Census units; you'd need allocation methods that introduce error). Provide the Census/BLS query definitions on `/data/` so anyone can pull the same unit-level data, and stop there. |
| Elkhart visitor (1.5) | The Context card is the fastest way to see "this is a different county." Its numbers also make a strong comparison hook ("see your county →"). | Comparisons must be to fixed benchmarks (Indiana, U.S.), or to *all* built editions. Never hand-picked "peer counties," which is a selection choice that can be read as framing. |

**Presenting demographics and voting without implying causation or stereotyping**
1. **No in-house correlations in v1.** The guide doesn't compute or chart its own "income vs. vote share" relationships. It summarizes **published** analyses, attributed by author, outlet and date, with each one's geography (county, township, precinct, national survey), period, method, and stated limits.
2. **Name the ecological fallacy every time.** A standard callout on the research page and any related lesson: "These patterns describe *places*, not *people*. A township where incomes are higher and that voted more for one party does not tell you how any higher-income person voted."
3. **Separate area-level from individual-level evidence.** Survey-based findings about individuals (with margins of error, usually national or state samples) are labeled as such and are never localized ("national surveys find X; no county-level survey exists").
4. **Language rules.** No causal verbs ("drives," "because of," "explains") unless the cited study claims causation and uses a causal design; then attribute the claim ("the authors argue..."). Use "areas with higher X tended to have..." phrasing. Never describe a demographic group as a voting bloc, "base," or "target."
5. **Symmetry.** If a page reports a pattern associated with one party's vote, it reports the same measure for the other party's vote, from the same study.
6. **Show uncertainty.** ACS 5-year estimates for small towns (Roseland, Indian Village) carry large margins of error. Display the MOE and grey out or flag estimates whose coefficient of variation exceeds a stated threshold (e.g., 30%). Always print the vintage ("ACS 2020–2024 5-year").
7. **Keep the history honest.** Economic events like the Studebaker closure are dated, sourced facts. Their effect on politics is described only through attributed historians or analysts, never as the guide's narrative.

**Edition split: this is the cleanest shared layer in the whole series.**
- **Indiana-generic (authored once, in `content/indiana/` and `data/indiana/`):** the indicator definitions and the exact Census/ACS/BLS (QCEW/LAUS) query specs, parameterized by FIPS; the explanatory text (what median household income means, why ACS has margins of error); chart templates; Indiana and U.S. benchmark values; the ecological-fallacy callout; the inclusion rule for published research; and Indiana-wide or national studies.
- **County-specific (generated or curated per edition):** indicator *values* (re-run the same queries with the edition's county FIPS and its places, county subdivisions and school districts, enumerated automatically from Census geography); the major-employers list (curated, sourced, by the published rule); the economic history narrative; and county-specific published analyses.
- **Mechanics:** `data/indiana/indicators.json` (id, label, table/variable, universe, MOE handling, display rule), and a fetch script that writes `data/editions/<county>/community/*.csv` stamped with the vintage and pull date. A new edition gets its Context cards and `/community/` pages for free, with zero hand-writing beyond employers and history. Re-running yearly when new ACS data releases refreshes every edition at once.

---

## 4. Landing page design

### 4.1 Concept

Complexity is shown as **overlap**: one place sits under a stack of governments, and each has elected seats. The visual is a stacked **layer diagram** for a chosen place, with **seat dots** (one dot = one elected seat that governs you; filled = you vote for it; ring = elected by others, e.g., other districts; square = appointed board). The counts are **computed at build time from the offices table, never typed in.** The numbers in the wireframe are placeholders marked `N`.

The default view shows a sample place (e.g., "South Bend, Council District 4, SBCSC") with a visible "Change place" control. Below it, the five path cards. Above the fold on desktop, path cards start right under the visual; on mobile, the visual collapses to one summary line plus a "See the layers" toggle.

### 4.2 Wireframe (desktop)

```
+--------------------------------------------------------------------------------------+
| [IN outline, St. Joseph filled in edition color]  INDIANA COUNTY CIVIC GUIDE          |
|                                                   ST. JOSEPH COUNTY EDITION           |
|                                                   Data as of Nov 7, 2026 · Not your county? v |
|  Paths  |  Reference v  |  For teachers  |  About & methods                 [search]  |
+--------------------------------------------------------------------------------------+
|                                                                                      |
|  One address. N governments. N elected seats.                                        |
|  Most of them were decided by fewer than 1 in 10 voters.                             |
|                                                                                      |
|  Showing:  [ South Bend v ]  [ Council District 4 v ]  [ South Bend schools v ]       |
|            (or look up your exact districts at the Indiana Voter Portal ->)          |
|                                                                                      |
|   STATE OF INDIANA ........ ● ● ● ● ● ● ●  ● ●        governor & statewide · your 2 legislators |
|   ST. JOSEPH COUNTY ....... ● ○ ○  ● ○○○○○○○○  ●●●●●●●●●  ●●  ■■■   commissioners · council · row officers · judges · boards |
|   CENTRE TOWNSHIP ......... ● ●●●                       trustee · board              |
|   CITY OF SOUTH BEND ...... ● ●  ● ●●● ○○○○○  ■■■       mayor · clerk · council      |
|   SOUTH BEND SCHOOLS ...... ● ●● ○○○○                   board                        |
|   LIBRARY / OTHER ......... ■ ■                         appointed boards             |
|                                                                                      |
|   ● you vote for this seat   ○ elected by other districts   ■ appointed, not elected  |
|   Counts computed from the guide's office data · how we count ->                      |
|                                                                                      |
|  NEXT ON YOUR BALLOT:  May 2027 city primary (mayor, clerk, council)   [calendar ->]  |
|  2026 general results are UNOFFICIAL until certified.                                 |
+--------------------------------------------------------------------------------------+
|  WHERE DO YOU WANT TO START?                                                         |
|                                                                                      |
|  +----------------+ +----------------+ +----------------+ +----------------+ +--------------+ |
|  | Who does what? | | Vote smarter   | | Run for office | | Follow the     | | How we got   | |
|  | Find your      | | Know what's on | | Filing,        | | money          | | here         | |
|  | governments &  | | your next      | | petitions,     | | Budgets, your  | | 160 years of | |
|  | who fixes what | | ballot & why   | | caucuses,      | | tax bill,      | | seats, mayors| |
|  |                | | it matters     | | money          | | campaign $     | | & turning pts| |
|  | 4 stops·15 min | | 5 stops·25 min | | 7 stops·40 min | | 5 stops·35 min | | 4 stops·30min| |
|  +----------------+ +----------------+ +----------------+ +----------------+ +--------------+ |
|                                                                                      |
|  [ Elections by the numbers: margins, turnout, open seats -> ]                       |
|  [ Know your community: people, work, housing, schools -> ]                          |
|                                                                                      |
|  Teaching or leading a group? Lesson kits & printables ->                            |
+--------------------------------------------------------------------------------------+
|  ST. JOSEPH COUNTY: [pop] people · [N] jobs · largest employers include [sourced]    |
|  ACS [vintage] · Know your community ->      (context strip; no election data nearby) |
+--------------------------------------------------------------------------------------+
|  Browse everything: Places · County · Schools · State · Elections · Money · History  |
+--------------------------------------------------------------------------------------+
|  Nonpartisan. Every figure links to its source. No ads, no endorsements.             |
|  How we choose what to include · Report a correction · Changelog                     |
|  Built from public records by [owner name]. [Disclosure of any party/campaign ties.] |
+--------------------------------------------------------------------------------------+
```

Mobile: the masthead collapses to a [county shape] "St. Joseph County Edition" bar; the layer diagram becomes a vertical list of layers with seat counts ("County · N seats · you vote for N"), with a "show seats" expander per layer; path cards stack full-width.

### 4.3 First-screen copy (draft)

> **One address. [N] governments. [N] elected seats.**
> If you live in St. Joseph County, Indiana, you are governed at once by the state, the county, a township, a school corporation, and often a city or town, plus appointed boards that tax and decide things too. Each one has its own officials, budget and election year.
>
> In the 2022 primary, **7.5%** of registered voters in the county cast a ballot. In the 2023 city primary, **9.1%** did. *(Official county canvass.)*
>
> You don't need to learn all of it. Pick where to start.

Notes on the copy:
- Neutral: turnout is a fact about all voters, not a party.
- "Fewer than 1 in 10" is accurate for both primaries cited; keep the footnote.
- Don't write "at least 6 governments" until the count is computed per place. Unincorporated residents have no city, so the numbers must change with the picker.

---

## 5. County-edition identity system

### 5.1 Visual marking (on every page, every print, every share preview)

1. **Series lockup:** "INDIANA COUNTY CIVIC GUIDE" (series wordmark, same in every edition) + "ST. JOSEPH COUNTY EDITION" (edition line).
2. **Locator glyph:** a simplified Indiana outline with the 92-county grid faint and the edition county **filled**. It's the favicon basis and the og:image corner mark. It works at 16px as a filled square in the state's top-north edge position; at larger sizes it's the full outline.
3. **Edition color:** each county gets one accent hue from a fixed series palette. **The palette must exclude party-coded red and blue** (and near-relatives). Suggested edition hues: teal, ochre, plum, forest, slate-violet, copper. St. Joseph could take one of these. Party colors are reserved for party data only, always paired with a text label (D/R/L/I) for accessibility and so color is never the only signal.
4. **Edition stamp:** "St. Joseph County Edition · Data as of 2026-11-07 · v1.0" in the header and in every print footer, along with the page URL.
5. **Share metadata:** og:title always ends "· St. Joseph County, IN"; og:image is the lockup plus the page title. This is what the Elkhart persona sees first.
6. **Scope badges on content blocks:**
   - `INDIANA-WIDE`: applies to every county (series-neutral styling, gray).
   - `ST. JOSEPH COUNTY`: county data (edition color).
   - `ST. JOSEPH EXCEPTION`: where state law treats this county differently (see 5.3).
7. **"Not your county?" control:** opens a map of Indiana's 92 counties. Edition counties are linkable; others say "Edition not built yet. The Indiana-wide chapters still apply to you" and link those chapters.

### 5.2 Content split: generic vs county-specific

| Module | Indiana-generic (shared across editions, authored once) | County-specific (swapped per edition, from data) |
|---|---|---|
| How local government fits together | Unit types (county, township, city, town, school corp, library, special districts), what each may do, home rule, units as parallel state creations | Which units exist here, counts, the place list, per-place unit stack |
| County government | Commissioners/council/row-officer roles, terms, term limits (Art. 6 §2), election rules | Officeholders (terms), district maps (schematic), party-control timeline, appointed boards roster, local litigation |
| Courts | Circuit/Superior/Probate roles; partisan vs retention systems | Which system this county uses, judges, retention results |
| Cities & towns | City classes, mayor-council structure by class, town council/clerk-treasurer | Each city/town's structure, officeholders, results, budgets |
| Townships | Trustee/board duties, township assistance, fire, cemeteries, budget role | Trustees & boards, township budgets, township results |
| Schools | Board structure options, SEA 287 party-label rules, funding formula, referenda law | Corporations here, seats/districts, referenda history, budgets/enrollment |
| Elections | Calendar rules (odd = municipal, even = state/county/township/school), primaries, petitions, vacancies/caucus law, voting methods & ID, absentee rules | County calendar fill (which seats, which years), vote centers, election-office contacts, results 2010+ |
| Run for office | Forms (CAN-2, CAN-19/21/34, CAN-37), eligibility, deadlines (from SOS), CFA forms & reporting schedule | Where to file locally, county party chair contacts (both parties, listed identically), local caucus examples |
| State government | Statewide offices, General Assembly structure & party control over time, governors, SEA 1/HB 1210 effects in general | Legislators whose districts touch the county, statewide races *as voted in the county* |
| Money | What-is-a-budget primer, Gateway/DLGF explainer, tax caps, LIT changes, campaign-finance law | Unit budgets, tax rates by unit, local CF coverage matrix & transcriptions, state legislator CF |
| Elections landscape | Metric definitions (margin, turnout denominators, margin bands), straight-party rule history by year, term-limit rules, table/chart templates | Computed values from the county's results and terms data |
| Community (social & economic) | Indicator definitions and Census/ACS/BLS query specs parameterized by FIPS, explanatory text, MOE rules, Indiana/U.S. benchmarks, ecological-fallacy callout, research-inclusion rule, statewide/national studies | Indicator values pulled for the county + its places, townships (county subdivisions) and school districts; employers list; economic history; local studies (see 3.5) |
| History | Optional statewide context | Party-control timelines, mayors, turning points, people |
| About/methods | Neutrality policy, badge definitions, people-selection rules | Edition sources, edition corrections log, edition gaps list |

### 5.3 The trap: "generic" content isn't fully generic

St. Joseph is a statutory exception in several ways the research already found: commissioners **elected by district** (one of three counties, and under a 2026 court ruling), **full legislative power vested in the council** (one of three counties), a **9-member council** (population-based), and **merit selection with retention for Superior Court**. City classes will differ in other editions too.

So generic modules must be written with **variant slots** driven by county config, not as static prose:

```
edition.json
{
  "county": "St. Joseph", "fips": "18141", "gateway_county_code": "71",
  "seat": "South Bend", "edition_color": "teal", "data_as_of": "2026-11-07",
  "variants": {
    "commissioner_election": "by_district",      // or "at_large_with_residency"
    "council_size": 9,                           // 7 in most counties
    "legislative_power": "council_full",         // or "split_commissioners_council"
    "superior_court_selection": "merit_retention",// or "partisan" / "nonpartisan"
    "cities": [{"name":"South Bend","class":"2"}, {"name":"Mishawaka","class":"2?"}]  // verify
  }
}
```

The generic text then reads "In most Indiana counties, X. **In St. Joseph County, Y** [ST. JOSEPH EXCEPTION badge]." A LaPorte edition flips the variant and the exception callout disappears.

### 5.4 Data model (so a new edition is a data swap)

Shared schema, one folder per edition (`data/editions/st-joseph/`), generic content in `content/indiana/`:

- `units` (id, type, name, parent/overlap, services[], website, contact)
- `offices` (id, unit, title, seats, district, term_years, cycle_years, partisan, how_filled_if_vacant, term_limit, statute)
- `terms` (person, office, start, end, party, selected_by: election|caucus|appointment, source, status)
- `people` (id, name, profile_eligible flag, criteria[], image_id)
- `elections` (date, type, status: official|unofficial|certified-at, source_doc_id)
- `results` (election, office, district, candidate, party, votes, pct_computed, winner)
- `budgets` (unit, year, basis, amount, source, series_id; `series_break` rows)
- `tax_rates` (unit, year, rate_per_100_av, source)
- `cf_filings` (committee, office, report, period, receipts, expenditures, cash, transcription_status, verified_visual)
- `appointed_boards` (board, unit, seats[], appointing_authority, powers)
- `indicators` (generic: id, label, source table/variable, universe, MOE rule) and `indicator_values` (edition: geography type + GEOID, indicator, value, moe, vintage, pulled_at)
- `employers` (name, sector, employment, source, as_of, selection_rule_id)
- `sources` (id, url, title, publisher, accessed, kind: primary|news|secondary|derived)
- `claims` (optional, for prose facts: text_key, source_ids, confidence, badge)

Statewide data (General Assembly control, governors, statewide offices, election law, SEA 1) lives once in `data/indiana/` and is shared by every edition. A new edition needs: `edition.json`, the county rows of each table (Gateway already filters by county code; county results archives differ by county and will be the main per-edition cost), and a county-specific History page.

---

## 6. Trust and neutrality checklist

**Wording**
- [ ] No "flip," "sweep," "seized," "landslide," "won back," "blue wave/red wave" in headings, chart titles or framing sentences. Say "party control of the council changed from R to D" in the timeline note, or nothing at all.
- [ ] Attribute every characterization. "Described by WNDU as the first Democratic board majority in 20 years" (and note that WVPE said "since 2012") rather than stating it as fact. Where sources conflict, show both.
- [ ] Describe disputes by each side's stated position, attributed (2021 redistricting: what the commissioners said, what the council said, what the settlement did). Never infer motive.
- [ ] Use consistent nouns: "candidate," "incumbent," "nominee." Same party label format everywhere ("Democrat (D)" / "Republican (R)" / "Libertarian (L)" / "Independent / no party").
- [ ] Keep a banned/loaded-term list in `/about/` (start from Ballotpedia's practice of avoiding terms that signal a position). Run it as a lint over content before each publish.

**Selection and emphasis**
- [ ] Candidate and officeholder order: by office, then district, then ballot order or alphabetical. **Never by party or vote share** except in an explicitly sorted results table.
- [ ] Charts default to the **full available range** (e.g., 2010–2026 results, 2012–2026 budgets). No start years chosen to show a trend. Budgets offer nominal and inflation-adjusted, and per-resident where comparing units.
- [ ] Party colors identical across all charts; every party mark carries a text label.
- [ ] **Photos:** within any set (current officeholders, a results table, a body's roster), either everyone gets an image or no one does. With about 25 licensed images, officeholder directories are text-only; images appear only in History where they illustrate an era.
- [ ] Equal card size, equal fields, equal prominence for every entry in a set.
- [ ] "Get involved" lists both major parties' county committees, minor parties with ballot access, the League of Women Voters (South Bend Area), and nonpartisan election-office contacts, all formatted identically. Put it on its own page, not next to results.

**People who shaped local government (selection rules, published on the page)**
- [ ] An entry qualifies on documented criteria only: (a) **TENURE**: held a county/city/legislative seat ≥ N years (pick N, e.g., 16, and apply it to everyone in the data); (b) **FIRST**: documented first (with source); (c) **HIGHER**: went from a local/county/legislative seat to statewide or federal office; (d) **FAMILY**: two or more members held elected office here.
- [ ] Apply the rules to the *full* data (mayors list, legislative histories), not to the research list as found. The research list is a sample with era and party skew; the rules must fill in under-researched Republicans and pre-1950 figures, or the page must say which eras are under-researched.
- [ ] **No profile cards for anyone currently in office or a declared candidate.** They're in the directory like everyone else. (Revisit once someone is out of office.)
- [ ] Controversy lines only for documented official findings (investigation report, court ruling, censure, indictment/outcome), applied to every entry by the same rule. A news-reported dispute isn't enough.
- [ ] Publish the count by party and era, with an explanation where it skews (e.g., "more Democrats meet the TENURE rule because the 1970–2020 legislative delegation was majority D").

**Data status labeling (visible badges, defined on /about/)**
- [ ] `OFFICIAL`: county canvass/certified source.
- [ ] `UNOFFICIAL as of <date time>`: election-night or uncertified (all 2026 general figures; also the 2024 primary file whose header says Unofficial despite its link label). A build check flags these after the expected certification date so they get re-pulled.
- [ ] `COMPUTED`: our arithmetic (percents, sums of funds, per-capita). Hover/tap shows the formula.
- [ ] `FROM SCAN`: transcribed from an image (CFA-4s); with "visually verified: yes/no." Unverified scan values don't ship.
- [ ] `SINGLE SOURCE`: one secondary/news source, no primary found.
- [ ] Research-tagged **L confidence** and "general knowledge" facts (e.g., the tax-cap percentages, straight-ticket status, other merit-selection county) are **verified or cut** before v1. They never appear in headings, charts or the landing page.
- [ ] Pending-litigation items (the commissioner-district ruling) show "status unknown as of <date>" and get no claim beyond what a primary or court record states. Find the case record before publishing.
- [ ] "Not found" is shown, not hidden: each page ends with a short **Gaps** list. This is a trust feature. Gaps shown openly read as honesty; gaps found by a critic read as concealment.

**Elections landscape layer (persona 1.6)**
- [ ] The same metrics for every race and every party: margin in points, turnout, open/incumbent, how the incumbent took office.
- [ ] Default sort is by margin (closest first) or by date. Never by party, and no party filter on the default view.
- [ ] Margin bands are defined once in methods and applied mechanically. No "safe," "toss-up," "target," "vulnerable," "pickup," "battleground" or "flippable" anywhere.
- [ ] Backward-looking only: no forecasts, no "likely," no strategy or resource advice.
- [ ] Turnout comparisons always show the denominator (municipal elections cover only city/town registrants).
- [ ] Straight-party share appears only for years where the guide sources what a straight-party vote covered.
- [ ] No precinct-level visualizations, voter-file data, donor contact details, or per-person opposition compilations. Precinct source files are linked on `/data/` only.

**Community (social and economic) layer**
- [ ] Fixed indicator set, identical for every unit; Census category names verbatim; vintage and MOE shown; unreliable small-area estimates flagged.
- [ ] Never overlaid on or placed next to election results in the guide's own visuals.
- [ ] Demographics-and-voting relationships come only from attributed published analyses, using the inclusion rule, with geography/period/method/limits stated and the ecological-fallacy callout.
- [ ] No causal verbs unless the cited study claims causation (and then attributed). No groups described as voting blocs.
- [ ] Comparisons are to Indiana/U.S. or to all built editions only. No hand-picked peers.
- [ ] Major employers by a published rule and source. No adjectives ("anchor," "engine," "struggling").

**Accountability**
- [ ] `/about/` names the author and discloses any party, campaign or advocacy ties (or states none).
- [ ] Corrections form plus a public corrections log with dates. A changelog per release.
- [ ] No ads, no donations framing tied to issues, no endorsements, no "scorecards."

---

## 7. What to cut or defer so v1 ships focused

**v1 must-have (the spine)**
1. Landing with the computed layer visual and five path cards.
2. Find my governments (place picker) + Indiana Voter Portal hand-off.
3. Who handles this? (needs a short research task: service → unit mapping, especially roads).
4. Elections: how they work (generic), calendar 2026–2030, results explorer 2010–2026 with status badges, judges and public questions.
5. Run for office: rules by office type, caucus/precinct committee path, forms, contacts. **Blocked on** retrieving official filing deadlines and IC 3-13-11 text.
6. County, places (South Bend, Mishawaka, towns, townships via template), schools: structure, terms-based officeholders, appointed boards, coverage badges.
7. Money: what-is-a-budget primer, tax-bill split by unit (rates data exists), budgets 2012–2026 with bases and breaks.
8. State: your legislators, how the state shapes local government.
9. About/methods/neutrality, corrections, changelog, print stylesheet.
10. Edition identity system (lockup, glyph, stamp, scope badges, og metadata, "Not your county?").

**Defer to v1.1 / v2**
- **Local campaign-finance dollar figures** until a complete, visually verified set exists (about 600 CFA-4s, or a public records request for electronic copies). v1 ships the coverage matrix, the explainer and state-legislator data.
- **History beyond the spine:** pre-2010 council/township history (research says thin), population since 1850, full 33-mayor portrait gallery. v1 History = party-control timelines + mayors timeline (text) + a short rule-based people set.
- **People profiles** beyond what the published rules produce from verified data.
- **Real address lookup and interactive district maps** (need county GIS files and license terms). v1 uses schematic, labeled-"not to scale" diagrams only where the shape is known.
- **Search** (add Pagefind late if time allows).
- **Elections landscape extras:** straight-party share (until the per-year rule is sourced; 2010–2014 values are also OCR), local fundraising benchmarks (until a complete transcribed set exists; v1 benchmarks = state legislative races only, shown as distributions with n), and future term-limit computations for offices whose pre-2020 history is partial. v1 landscape = margins, turnout, open seats from known retirements/limits, how incumbents took office.
- **Community layer extras:** `/community/research-on-voting/` ships only once at least a few published analyses pass the inclusion rule (otherwise, defer the page rather than run a thin, one-sided one). v1 community = fixed indicator set on `/community/` and Context cards for county, cities and townships. School-district cards and employment-by-industry trends can follow.
- **Teacher kit:** v1 ships one lesson kit (Vote smarter) with a printable handout to prove the format; the others come later.
- **Presentation/projector mode, per-precinct results, inflation toggles beyond budgets, special districts beyond the researched list** (housing authorities not found; Transpo appointing detail not found).

**Cut**
- "How a bill becomes law" as a standalone section (link out instead).
- "2026 shift in party control" as a section heading (it becomes the latest point on the timelines).
- A static, hand-typed "current officeholders" roster (replaced by terms data).

---

## Appendix: reference points consulted (4 of 10 web searches used)

- Ballotpedia editorial and neutrality practices: source curation across competing ideologies, a quality team auditing for neutrality, a style guide avoiding position-signaling terms. [About](https://ballotpedia.org/About_us), [Editorial policy](https://ballotpedia.org/Ballotpedia:Editorial_policy), [How we ensure factual content](https://ballotpedia.org/Ballotpedia:How_we_ensure_factual_content), [SF Public Press profile](https://www.sfpublicpress.org/ballotpedia-strives-to-earn-voters-trust-with-comprehensive-elections-guide/)
- UNC School of Government, *Local Government in North Carolina*: an interactive, CC BY-SA open textbook explicitly meant to be adapted to other states and settings, organized as "Local Government and You" before institutions. This is a precedent for both the you-first ordering and the generic/local split. [Pressbooks](https://pressbooks.pub/localgovernment), [PDF](https://sog.unc.edu/sites/www.sog.unc.edu/files/Local-Government-in-North-Carolina-1612811451.pdf)
- City of Guelph "user guide" (council / administration / how to get involved) and iCivics county games (citizen-request framing): support for service-first, not org-chart-first. [Guelph](https://renthomas.ca/city-of-guelph-user-guide-the-first-of-its-kind-in-canada), [NACo resources](https://www.naco.org/articles/naco-launches-new-civic-education-and-engagement-resources)
- **Local precedent to differentiate from (and possibly partner with):** League of Women Voters, South Bend Area publishes a *Citizen's Guide to Representative Government* (2019 edition found), a directory of officials; LWV Indiana publishes a statewide *Citizens Handbook* (2024), which is effectively the "Indiana-generic" layer in print. This guide should be the *learning* layer those directories lack, and should cite and link them. [2019 SJC guide](https://my.lwv.org/sites/default/files/2019_lwv_citizens_guide_final.pdf), [LWV Indiana handbook 2024](https://cdn.zephyrcms.com/3fc72ad2-2ad9-4402-972c-1c14c6179b2a/2024-0619-final-indiana-lwv-citizens-handbook.pdf), [LWV South Bend Area](https://my.lwv.org/indiana/south-bend-area)
