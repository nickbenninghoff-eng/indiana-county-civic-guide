# Data schema: Indiana County Civic Guide

The site is generated from these files. **Indiana-wide data** lives in `data/indiana/` and is shared by every county edition. **County data** lives in `data/editions/st-joseph/`. A new county edition = new `data/editions/<county>/` folder with the same files.

## Universal rules
- CSV, UTF-8, comma-separated, header row exactly as specified, RFC-4180 quoting (quote any field containing a comma, quote or newline). Dates `YYYY-MM-DD` (use `YYYY` or `YYYY-MM` when that's all that's known, and say so in `notes`). Money in plain dollars with no `$` or commas (`393342.90`). Percentages as numbers 0–100 with up to 2 decimals.
- Every row carries `status` and `source_ids`.
- **`status`** (exactly one):
  - `official`: certified or official government record (county canvass marked Official, statute text, adopted budget from Gateway/DLGF)
  - `unofficial`: election-night or uncertified (all 2026 general results; any file whose header says Unofficial). Put the "as of" date in notes.
  - `computed`: our arithmetic from other rows (percent from votes, sums, per-capita)
  - `from_scan`: transcribed from a scanned image (OCR or visual); notes say which
  - `secondary`: reliable secondary source (Wikipedia, Ballotpedia, reputable news) with no primary found
  - `single_source`: only one secondary source and not corroborated
- **`source_ids`**: semicolon-separated IDs from your area's sources file, e.g. `RES-012;RES-040`.
- **`confidence`** (where the file has the column): `high` / `medium` / `low`. Low-confidence facts are kept in data but flagged; the site won't show them in headings or charts.
- **Apply `planning/fact-check-report.md`.** Wherever it CORRECTED, CONTRADICTED or resolved a CONFLICT for something you're encoding, use the corrected value and cite the fact-check's source. Where it says REMOVE, don't encode the item. Log every fact-check finding you applied in your area's `_corrections_applied.md`.
- Never encode private individuals' addresses, phone numbers or e-mails.
- Neutral wording in every text field (no "flip", "sweep", "landslide", "seized", "won back", "wave", "safe", "target", "vulnerable"). Party labels: `D`, `R`, `L`, `I` (independent/no party), `G`, `NP` (nonpartisan), `W` (write-in), `O` (other; say which in notes).

## Sources (one file per area, merged later)
`sources_<area>.csv`: `id,url,title,publisher,accessed,kind,notes`. `kind` is `primary|news|secondary|statute|dataset|derived`. ID prefixes per area: RES (results), GOV (government/terms), MON (money), COM (community), PPL (people/images), IND (Indiana-wide), GAP (gap-fill).

## Indiana-wide (`data/indiana/`)
- `unit_types.csv`: `unit_type,label,plural,what_it_does,elected_bodies,can_levy_tax,statute,status,source_ids`
- `office_types.csv`: `office_type,label,unit_type,term_years,cycle,partisan,term_limit,vacancy_rule,statute,what_it_does,status,source_ids` (`cycle` = `even|odd|municipal|n/a`)
- `election_rules.csv`: `topic,rule_key,plain_language,detail,effective_from,effective_to,statute,status,confidence,source_ids` (calendar, primaries, straight-ticket by year, ID, absentee, petitions, caucus vacancies, school-board party labels, retention, citizen initiative, etc.)
- `statewide_offices.csv`: `office,what_it_does,term_years,elected_or_appointed,status,source_ids`
- `statewide_terms.csv`: `person,office,party,start,end,selected_by,status,confidence,source_ids,notes` (governors as far back as sourced; current statewide officers; 2026 winners marked unofficial)
- `general_assembly_control.csv`: `year,chamber,d_seats,r_seats,other_seats,total_seats,supermajority_party,status,source_ids,notes`
- `state_local_rules.csv`: `topic,plain_language,detail,statute,effective,status,confidence,source_ids` (home rule, tax caps, levy controls, LIT, SEA 1-2025, HB 1210-2026, DLGF role, school funding basics)
- `indicators.csv`: `indicator_id,label,definition,universe,source_dataset,table_variable,moe_rule,display_rule`

## County edition (`data/editions/st-joseph/`)
- `edition.json`: county config (name, fips, seat, gateway code, edition color, data_as_of, variants: see `planning/ux-review.md` §5.3). Written by the main session.
- `units.csv`: `unit_id,unit_type,name,parent_unit_ids,places_covered,website,status,source_ids,notes` (county; cities; towns; 13 townships; school corporations; libraries; special districts)
- `offices.csv`: `office_id,unit_id,office_type,title,district,seats,elected,partisan,term_years,next_election,status,source_ids,notes`
- `terms.csv`: `term_id,office_id,person,party,start,end,selected_by,first_selected_by,status,confidence,source_ids,notes` (`selected_by` = `election|caucus|appointment|unknown`; `end` blank = current; future terms starting 2027-01-01 from 2026 results are included with status unofficial)
- `appointed_boards.csv`: `board_id,unit_id,name,what_it_decides,seats,appointing_authorities,levies_tax,status,source_ids,notes`
- `elections.csv`: `election_id,date,type,scope,registered,ballots_cast,turnout_pct,straight_party_d,straight_party_r,straight_party_other,status,source_doc,source_ids,notes` (`type` = `primary|general|special|municipal_primary|municipal_general`; `scope` = countywide or which cities voted)
- `results.csv`: `election_id,contest_id,office_id,contest_label,district,party_primary,candidate,party,votes,pct,winner,vote_for,status,confidence,source_ids,notes` (`party_primary` = party ballot for primaries, blank for generals; `pct` computed if not printed, and then the note says so; public questions use candidate=`YES`/`NO`)
- `budgets.csv`: `unit_id,year,basis,amount,adopted_or_actual,series_id,status,source_ids,notes` (`basis` = `general_fund|advertised_all_funds|all_funds_incl_utilities|gateway_reported_funds`). Add `series_break` rows (amount blank) where the reporting basis changes, with an explanation in notes.
- `budget_breakdowns.csv`: `unit_id,year,kind,category,amount,basis,status,source_ids,notes` (`kind` = `spending|revenue`)
- `tax_rates.csv`: `unit_id,taxing_district,year,rate_per_100,rate_kind,status,source_ids,notes`
- `debt.csv`: `unit_id,year,debt_type,amount,status,source_ids,notes`
- `cf_state.csv`: `committee,candidate,office,district,party,year,receipts,expenditures,cash_end,top_funder_types,status,source_ids,notes` (state legislators from the state bulk data)
- `cf_local.csv`: produced later from `research/cf/` (Phase B)
- `indicator_values.csv`: `geo_type,geo_id,geo_name,indicator_id,value,moe,vintage,pulled_at,status,source_ids,notes` (`geo_type` = `county|place|town|county_subdivision|school_district|state|nation`; `place` = the two cities, `town` = incorporated towns)
- `employers.csv`: `name,sector,employees,as_of,selection_rule,status,source_ids,notes`
- `timeline.csv`: `date,category,title,description,status,confidence,source_ids` (`category` = `political|economic|government|legal|population`)
- `audits.csv` (optional): `unit_id,report_no,report_type,period_start,period_end,filed,auditor,findings,amount_charged,amount_questioned,referred_to,summary,status,source_ids,notes` — State Board of Accounts (or contracted CPA) reports per unit, shown in a "State audits" section on the unit's place page. `findings` = semicolon list of finding headings as printed in the report; `amount_charged` / `amount_questioned` = dollars as printed in the report's Summary of Charges / Questioned Costs (blank if none); `summary` only where the report's findings were read in full, attributed to the report. List every report on file for a unit the same way.
- `people.csv`: `person_id,name,offices_summary,parties,criteria,in_office_now,summary,documented_findings,image_id,status,confidence,source_ids,notes` (`criteria` = semicolon list of `TENURE|FIRST|HIGHER|FAMILY|TURNING_POINT`; `documented_findings` only for official findings such as court rulings, censures or settlements, attributed)
- `images.csv`: `image_id,subject,file_page_url,direct_url,license,credit,local_file,notes`
- `research_on_voting.csv`: `study_id,authors,title,outlet,date,geography,period,method,finding_summary,limits,url,status`
- `gaps.csv`: `area,item,why_missing,how_to_fill`
