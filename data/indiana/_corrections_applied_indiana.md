# Corrections applied: Indiana-wide layer

Source of corrections: `planning/fact-check-report.md` (IND-027). Verification done 2026-11-07 against FindLaw statute pages, the SOS 2026 legislation summary PDF (IND-001) and search summaries. WebSearch calls used: 7 of 15.

## Fact-check findings applied

| Fact-check finding | What the data now says | File / key |
|---|---|---|
| 04 said Indiana "eliminated straight-ticket voting in 2019" (CONTRADICTED) | Straight-party voting exists. Through 2026 it does not count for at-large multi-seat offices or school board (IC 3-11-2-10 text, verified). County 2026 results show 49,335 straight-ticket ballots. HEA 1377 (P.L. 99-2026, effective 2027-01-01) extends it to at-large partisan offices unless the voter marks individual candidates; school board excluded. | election_rules: straight_party_through_2026, straight_party_from_2027 |
| 09 summary of HEA 1377 said only that straight-party votes do not count for school board (CORRECTED, incomplete) | Full effect encoded from the SOS summary (sections, citations, effective date). The 2016 SB 61 attribution is kept at confidence=low. | election_rules: straight_party_2016_history |
| Supermajority "3/5, 60 House / 34 Senate" (CORRECTED) | Two-thirds: 67 House / 34 Senate, tied to the quorum rule. | election_rules: quorum_two_thirds; general_assembly_control notes |
| Quorum cited as Art. 4 sec. 10 (CORRECTED) | Art. 4 sec. 11, text read on FindLaw. | election_rules: quorum_two_thirds |
| Sessions end April 30 / March 15 (CORRECTED) | April 29 (statute page read) / March 14 (from search summaries, confidence=medium). | election_rules: session_length |
| 2027 House "54 R / 46 D" (UNVERIFIABLE) and Senate "15 D / 34 R" (CONTRADICTED, sums to 49) | Not encoded. Seat counts left blank; notes say Democrats broke the House Republican supermajority (first time since the 2012 election) and gained at least four Senate seats, unofficial. | general_assembly_control 2027 rows |
| "House speaker was ousted" (UNVERIFIABLE) | Dropped. Gap lists the question. | gaps_indiana |
| Comptroller: Bailey 49.1 vs 48.0 (CORRECTED) | Bailey (D) won, about 50% to 47% at 95% reporting per Capital Chronicle; Nieshalla conceded. Marked unofficial. Percentages from Wikipedia not used. | statewide_terms |
| Treasurer: Elliott 51.0 vs Kebe 49.0 (winner CONFIRMED, % UNVERIFIABLE) | Elliott (R) won; marked unofficial; no percentages. | statewide_terms |
| Secretary of State: Bayh won (CONFIRMED); statewide 51.8 / 42.6 unverified | Bayh (D) won, unofficial; statewide percentages not encoded. | statewide_terms |
| Auditor renamed "State Comptroller," reason not found (CONFLICT-RESOLVED) | Rename explained: HEA 1001-2023 (2023 budget) and SEA 221-2025 (P.L. 40-2025); the constitution still names Auditor of State. | statewide_offices, office_types |
| Governors since 1945 "from memory" (CONFIRMED, knowledge-only) | Encoded with confidence=medium and start years only; Schricker's earlier 1941-45 term noted. | statewide_terms |
| HB 1210: "expands disabled veteran relief" vs "delays SEA 1 LIT changes to 2029" (CONFLICT-RESOLVED) | The 05 reading is used; the veteran claim is not encoded. P.L. 157-2026 confirmed in the SOS summary. | state_local_rules: hea1210_2026, local_income_tax |
| SEA 1 "from 2028" (CORRECTED, stale) | Rate changes now 2029; LIT councils end 2027-07-01; cap 2.9%. "Cities of 3,500+" qualifier dropped (unconfirmed). | state_local_rules: local_income_tax |
| Property tax caps 1/2/3%, constitutional since 2010 (CONFIRMED statute, constitution text unverified) | Art. 10 sec. 1(f) text read on FindLaw (the Justia text in file 09 was stale). Statute IC 6-1.1-20.6-7.5 re-read. | state_local_rules: property_tax_caps |
| Veto override simple majority (CONFIRMED) | Encoded at confidence=medium (secondary text of Art. 5 sec. 14). | election_rules: veto_override |
| Governor 4 years, max 8 in 12 (CONFIRMED) | Art. 5 sec. 1 text read. confidence=high. | election_rules, office_types |
| Photo ID; no statewide citizen initiative (CONFIRMED, knowledge-only; add citations) | Photo ID verified against IC 3-11-8-25.1 (high). No-initiative cited to Ballotpedia (medium). | election_rules |
| DLGF budget-approval role (UNVERIFIABLE) | Encoded at confidence=medium from DLGF presentations; exact statute text listed in gaps. | state_local_rules: dlgf_role, levy_controls |
| Caucus procedures IC 3-13-5 / 3-13-11 (CONFIRMED, practice) | Encoded at confidence=medium; IC 3-13-11-1 re-read. | election_rules: legislative_vacancy_caucus, local_vacancy_caucus |
| 09 misread IC 36-2-3-4: opt-in counties get 4+3 council (CONTRADICTED) | Opt-in counties (185,000 to 300,000 people, resolution by 2023-09-01) get nine single-member districts; 4 district + 3 at-large is the default for other counties. | state_local_rules: county_council_structure; office_types |
| Whether any county opted in (UNVERIFIABLE) | Not stated in generic files; left to the edition. | state_local_rules |
| "St. Joseph one of three counties with elected-by-district commissioners" (UNVERIFIABLE) | Not repeated. | state_local_rules: county_government_split |
| Superior Court: "one of two merit counties (St. Joseph, Allen)" (CONTRADICTED) | Four: Lake, St. Joseph, Allen, Marion. 2021 HEA 1453 change noted; commission text still to be re-checked. | election_rules: merit_selection_counties |
| Prosecutor term limit (CONFLICT-RESOLVED) | Not on the Art. 6 sec. 2 8-in-12 list. | office_types, election_rules |
| Surveyor term limit (CONFLICT-RESOLVED) | Constitutional office but not on the list. | office_types |
| Second-class cities, 34,000 (CONFIRMED by statute band) | IC 36-4-1-1 re-read on FindLaw. | state_local_rules: municipal_classes |
| SEA 287 school board partisan (CONFIRMED) | Encoded at confidence=high with signing date, effective date and vote. | election_rules: partisan_school_board |
| Superintendent replaced by appointed Secretary of Education (CONFIRMED) | HEA 1005-2017 and HEA 1005-2019. | statewide_offices |
| "Retain Justice" rows are not Supreme Court justices (CORRECTED label) | A rule explains the label. | election_rules: retain_justice_labels |
| Not-checked areas: Art. 10 sec. 1 text, IC 3-11-8-25.1, 61/30-day limits | Art. 10 and IC 3-11-8-25.1 now verified; 61/30-day limits left in gaps. | gaps_indiana |

## Additional corrections found while verifying

- Research 04 said the General Assembly "convenes first Tuesday after first Monday in January." IC 2-2.1-1-2 says it organizes in November and reconvenes by the fourth Monday in January. Encoded from the statute.
- Research 04 counted 11 mail-ballot reasons. The statute page (IC 3-11-10-24) lists 13 items; the rule row names them without a count.
- The research's mention that the Senate had "3/5 present needed for quorum" was dropped (Art. 4 sec. 11 is two-thirds).
- Kernan is recorded as a succession (Lieutenant Governor after O'Bannon's death), not an election.

## Items marked [L] / from memory in the research

Verified here (confidence high): photo ID at polls; quorum section; governor term; session end April 29; straight-party status; absentee reasons; early voting window; property tax caps; municipal classes; township trustee; Superior Court retention; home rule.
Verified at medium: citizen initiative (Ballotpedia, secondary); veto override (secondary text); DLGF role (presentations); session end March 14.
Encoded at confidence=low and listed in gaps: precinct committeeperson term and county chair rule; independent-candidate signature number; library board terms and tax; straight-party 2016 attribution; SEA 1 deduction schedule.
Office duties for Attorney General, Secretary of State, Treasurer and Lieutenant Governor are general descriptions marked status=secondary (no primary source read).

## Handed to the edition config (main session)

- St. Joseph County Superior Court nominating commission: 7 members (3 appointed by the Governor, 3 by the County Commissioners, 1 Supreme Court justice as chair); five most highly qualified nominees go to the Governor (courts.in.gov, IND-042). Check current IC 33-33-71 text after HEA 1453 (2021).
- Whether St. Joseph County opted into the nine-district council / three-district commissioner structure by 2023-09-01: not found; practice is consistent with opting in.
- April 2026 ruling that district-only commissioner elections violate the "free and equal elections" clause (ABC57, Apr 22, 2026): say "a judge ruled"; court, judge and appeal status unknown; underlying City of South Bend suit was filed in Marion County in February 2023.
- Straight-ticket totals for the county in 2026 (49,335; D 29,724, R 19,372).

## 2026-11-08: gap-fill A (election rules)

Source: `planning/qa/gapfill-2026-11-08-A-rules.md` and `-edits.csv` (41 rows). Every statute cited was read on Justia (2025 Indiana Code) in a browser on 2026-11-08; changes from the 2026 session were not checked. New sources IND-065 to IND-077. Log: `planning/qa/gapfill-2026-11-08-applied.md`.

### Applied
- New rule vote_centers (IC 3-11-18.1-3, -5, -13): vote at any vote center in the county; the plan needs a unanimous board vote.
- early_voting_period detail: at least 7 hours on each of the two Saturdays before Election Day; an optional third Saturday; counties under 20,000 may reduce to 4 hours (IC 3-11-10-26).
- straight_party_2016_history: confidence low -> medium, citing the IC 3-11-2-10 amendment history (P.L.21-2016) and Ballot Access News (SB 61 signed March 21, 2016).
- independent_petitions: filing window up to noon June 30 and certification by noon July 15 (IC 3-8-6-10), plus the 2027 window computed from the statute.
- independent_signature_example: the 2% rule (IC 3-8-6-3); confidence high.
- New rules local_candidate_registration (IC 3-8-1-1) and local_residency_requirements (IC 3-8-1-20 to -29 and -34; no minimum age is stated).
- New rule local_candidate_reports (IC 3-9-5-6, -7, -10): 25-day pre-election reports, due at noon 7 days later; annual report on the third Wednesday in January.
- New rule school_board_filing (IC 3-8-2.5-4; CAN-34 2026 revision): May 19 to noon June 18, 2026; 10 signatures.
- precinct_committeepersons detail: elected in May 2026, 2030 and every four years (IC 3-10-1-4.5). The county-chair rule stays low confidence.
- New rule municipal_2027_filing (confidence medium): Jan 6 to noon Feb 5, 2027 for declarations (calendar plus IC 3-8-2-4); petitions to noon June 30, 2027; election Nov 2, 2027.
- gaps_elections: the early-voting Saturdays row removed. The vote-center, straight-party, 2010/16/18 wording and 2028/2030 rows narrowed.
- gaps_services: the 2027 filing and campaign-finance rows removed. The eligibility, petition-count, school-board filing and precinct-committee rows narrowed.
- The South Bend and Mishawaka statutory class, and the 2010 public question label: see the gov and results logs.

### Adapted
- precinct_committeepersons statute: only IC 3-10-1-4.5 is cited. The proposed IC 3-6-2-1 was not confirmed.
- straight_party_2016_history: the effective date and the pre-2016 text are left as "not read", rather than asserted.
- Proposed confidence "medium-high" mapped to medium. One CAN-16 sentence and the IC 3-9-5-20.1 citation were dropped, because they were not verified.

### Notes-only
- 2026 public question article numbers: PQ1 Art. 1 Sec. 17 and PQ2 Art. 6 Sec. 6, from news leads only, put in the gap row.
- 2024 Public Question #1 on the county ballot: likely but unverified, put in the gap row.

### Skipped
- office_types eligibility rows (7). office_types.csv has no eligibility column; the content went into the local_residency_requirements rule instead.
- office_types precinct_committeeperson term_years. The statute sets the election years, not a term length.
- elections.csv 2016/2018 question text: no matching results rows.
- The county election board chair note: optional, and the guide does not describe that body.
