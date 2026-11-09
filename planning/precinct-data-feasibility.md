# Precinct-level vote map layer: data feasibility (St. Joseph County, IN, FIPS 18141)

Collected 2026-11-08. Collect-and-report only; no conclusions on design. WebSearch used: 7 of 15. Not searched: Redistricting Data Hub, Indiana Election Division bulk files, county GIS open-data portal, news-org aggregations (NYT/Dave's Redistricting).

## Bottom line (facts found)

| Year | Races wanted | Precinct results found | Boundary match | Drill-down feasible? |
|---|---|---|---|---|
| 2024 general | President, Governor, U.S. Senate | OpenElections CSV (downloaded) and MEDSL (Dataverse, 74 MB file, filtered OK) | Census 2020 VTDs match 210 of 213 precinct codes; 3 precincts have no VTD polygon | Yes, with 3 precinct gaps to resolve |
| 2022 general | Sec. of State, Auditor, Treasurer | NOT found as machine-readable. Only 3 leads: county "Signed Official Report with precincts" (likely PDF, blocked to me), VEST/UF Election Lab (shapefile needs login, licence NC-ND), state ENR archive (no download links seen) | Unknown vintage for VEST; 2020 VTDs probably usable (see issues) | Unconfirmed. Township/city aggregation would need county-level data or PDF extraction |
| 2020 general | President, Governor | OpenElections CSV (downloaded); MEDSL file needs Harvard "guestbook" response (not downloaded) | Census 2020 VTDs: 221 of 221 names match exactly | Yes, cleanest year |

Straight-ticket: present at precinct level in both OpenElections files (2020 and 2024). See item 4.

## 1. Precinct-level results

| Source | URL | Years | Format | St. Joseph coverage | Match key | Licence | Issues |
|---|---|---|---|---|---|---|---|
| OpenElections Indiana (county files) | https://github.com/openelections/openelections-data-in | 2020 (`2020/20201103__in__general__st_joseph__precinct.csv`), 2024 (`2024/counties/20241105__in__general__st_joseph__precinct.csv`), also 2018 (`2018/counties/20181106__in__general__st_joseph__precinct.csv`, not downloaded). No 2022 folder in repo tree. | CSV, long format: county, precinct, office, district, party, candidate, votes | 2020: 221 precincts, 4,357 rows. 2024: 213 precincts, 17,470 rows. All races on the ballot, including Straight Party, Registered Voters, Ballots Cast | 2020: "Centre Twp 1" style (no code). 2024: "CENTRE TWP 1 010001" (6-digit code last token) | MIT (repo LICENSE.md) | 2020 and 2024 precinct naming differs. 2024 President REP+DEM sums to 53,585 / 55,215 (not yet checked against the official canvass). Candidate names differ in case/format by year. Write-ins carry party "WI" |
| MEDSL Precinct-Level Returns 2024 by Individual State | https://doi.org/10.7910/DVN/NYTPDU (file `2024-in-precinct-general.tab`, file id 13731143, 74 MB) | 2024 | CSV (original format), tidy | 24,990 St. Joseph rows; 428 distinct precinct strings because some rows use bare code `010001` and others the OpenElections-style full name (duplication; looks like two source feeds merged) | `precinct` = 6-digit code in most rows | CC0 1.0 | Risk of double counting if both name forms are included. Not saved to project (74 MB); filtered extract could be saved |
| MEDSL 2022 by Individual State (Indiana local file) | https://doi.org/10.7910/DVN/UYQIEP (`2022-in-local-precinct-general.tab`, id 10855180) | 2022 | CSV | NONE. File has 39 counties, zero rows for St. Joseph | n/a | CC0 | MEDSL README: "Only 36 of Indiana's 92 counties released precinct-level election results in 2022... systematically missing." |
| MEDSL 2022 State Offices | https://doi.org/10.7910/DVN/OAARCY (`STATE_precinct_general.csv`, 863 MB, id 14249788) | 2022 | CSV | Streamed and filtered: 0 Indiana rows for county 18141 (Indiana is not in this file) | n/a | CC0 | Confirms no MEDSL 2022 St. Joseph precinct data |
| MEDSL 2020 by Individual State | https://doi.org/10.7910/DVN/NT66Z3 (`2020_in_precinct_general.tab`, id 13582892, 31 MB) | 2020 | CSV | Not obtained: API returns "required Guestbook response for guestbookID 458" | | CC0 | Needs manual (browser) guestbook step; not needed since OpenElections 2020 exists. MEDSL says only 56 of 92 Indiana counties released 2020 precinct data |
| St. Joseph County Election Board | https://www.sjcindiana.gov/2392/Election-Results | 2022 general: "Signed Official Report with precincts" (per search snippet, not opened). Other precinct files exist: DocumentCenter 59999 (2022 primary by precinct), 68104 (2024 primary), others | PDF (county is likely the source for both OpenElections files) | Official source | Precinct code in report | Public record | Site and DocumentCenter return HTTP 403 / Cloudflare "Just a moment" to curl and WebFetch. I did not try to bypass it. Prior project notes (research/results-2020-2026.md) say precinct files were skipped on instruction and 60003 is a 96-page scanned file not opened. A snippet also shows a 2022 general election-night summary at DocumentCenter/View/57654 (partial, 23 of 42 vote centers, not final) |
| Indiana ENR (state) | https://enr.indianavoters.in.gov/archive/2022General/index.html | 2022 general archive (and current site) | JavaScript web app | Probably county/precinct drill-down in UI | | State public record | Fetched page has no download links; guessed JSON paths 404. Data API not identified. Not searched further |
| VEST via UF Election Lab | https://election.lab.ufl.edu/dataset/in-2022-precinct-level-election-results/ (also 2020, 2024 pages) | 2016, 2018, 2020, 2022, 2024 Indiana precinct boundaries + results | Shapefile (login required to download); `documentation22.txt` is free | Documentation says Indiana results cover U.S. Senate, Secretary of State, Auditor, Treasurer; results and precinct shapefile "provided by the Indiana Secretary of State Election Division"; many counties from county canvass reports | | Archive: CC BY-NC-ND 4.0 per documentation; dataset pages say licensing "apply only to cleaned datasets" | NoDerivatives and NonCommercial terms likely conflict with aggregating and republishing as a derived map. Not downloaded. Whether St. Joseph is present in the 2022 file is unverified. Possible fee-for-service lock |

## 2. Precinct boundaries

| Source | URL | Vintage | Format | St. Joseph coverage | Issues |
|---|---|---|---|---|---|
| Census 2020 Voting Districts via TIGERweb | `https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2020/MapServer/58/query` with `where=STATE='18' AND COUNTY='141'`, `outFields=*`, `outSR=4326`, `f=geojson`. (Layer 58 is "Voting Districts" in tigerWMS_Census2020; the `Legislative` service also has a Voting Districts layer, id 15.) | Reflects precincts around 2020 census date | GeoJSON (downloaded: `sources/precincts/tigerweb-vtd2020/vtd.json`, 1.4 MB) | 225 features. Fields GEOID, STATE, COUNTY, VTD, BASENAME, NAME, POP100, HU100, AREALAND. `NAME` and `BASENAME` = county 6-digit precinct code (e.g. `150005`) | Public domain (Census). Some names carry suffixes "(NV)" (e.g. `090607 (NV)`, `130113 (NV)`) = no-voters/no-population units, which have no results. The Census `VTD` field is an internal 6-digit id, not the county code, so use `NAME` |
| Indiana GIS: Voting Districts of Indiana USCB 2020 | https://gisdata.in.gov/server/rest/services/Hosted/Voting_Districts_of_Indiana_USCB_2020/FeatureServer | Census TIGER copy obtained Nov 2022 | Esri FeatureServer | Statewide | Same data as Census; licence field blank. Not needed |
| UF Election Lab St. Joseph precinct maps | https://election.lab.ufl.edu/dataset/st-joseph-county/ | 2018, plus 2016 commissioner basemaps | PDF only | Yes | Not machine-readable. Not usable for the map |
| County precinct maps | sjcindiana.gov DocumentCenter `voter_Precinct_*_8x11_2022` (e.g. View/19971, 20120) | 2022 | PDF maps per township | Yes | PDF only; county site blocks automated fetch. County GIS open-data portal: not searched |
| VEST shapefiles | see item 1 | 2020/2022/2024 | Shapefile (login) | Unverified | Licence issues above |

Boundary match tests (run locally):
- 2020 OpenElections names mapped to codes (township code x 10000 + number, or the 6-digit code for Mishawaka/South Bend): 221 of 221 match a VTD `NAME`.
- 2024 OpenElections 6-digit codes vs VTD `NAME`: 210 of 213 match. Unmatched in VTDs: 090308, 090508, 130518 (new or renumbered precincts after 2020).
- 15 VTDs have no 2024 results: 020024, 030004, 090208, 090505, 090601, 090607 (NV), 090608, 110008, 120004, 120005, 130109, 130113 (NV), 130417, 130507, 130610 (and others not displayed; list printed was truncated at 15). These are consolidated, renumbered, or no-voter units.
- Did Indiana re-precinct after 2021 redistricting? Evidence only from the match: 2024 has 213 populated precincts vs 225 VTDs and 3 codes absent from the 2020 VTD file, so some changes occurred between 2020 and 2024, but I found no published post-2020 St. Joseph boundary file. Indiana counties' precinct plans are filed with the Election Division; not searched.
- 2022 general: the 2022 precinct-map PDFs exist on the county site, so 2022 precincts likely sit between the 2020 and 2024 sets. Unverified.

## 3. Precinct to township / city assignment

Codes in the 6-digit precinct id: first 2 digits = township-level unit, next 4 = number. From the 2024 file (all 213 precincts):

| Prefix | Unit | Prefix | Unit | Prefix | Unit |
|---|---|---|---|---|---|
| 01 | Centre Twp | 06 | Liberty Twp | 11 | Penn Twp |
| 02 | Clay Twp | 07 | Lincoln Twp | 12 | Portage Twp |
| 03 | German Twp | 08 | Madison Twp | 13 | South Bend (city) |
| 04 | Greene Twp | 09 | Mishawaka (city) | 14 | Union Twp |
| 05 | Harris Twp | 10 | Olive Twp | 15 | Warren Twp |

- Township membership is encoded in the name for 13 of 15 units. South Bend (13) and Mishawaka (09) appear as their own units, so city membership for those two cities is directly in the name/code (assumes every 09/13 precinct lies within that city; not verified by spatial join).
- Smaller cities and towns (Roseland, New Carlisle, North Liberty, Walkerton, Lakeville, Osceola, Indian Village, etc.) are NOT encoded in the precinct id. Those precincts carry a township name only, and a precinct can straddle a town line. Needs a spatial join against `sources/boundaries/places_incorporated.geojson` (already in the project), with area-weighted or centroid assignment, and a decision on split precincts.
- 2020 file precinct text maps cleanly to the same codes (see tests above).

## 4. Straight-ticket votes by precinct

Available. Both OpenElections files have an office row `Straight Party` per precinct (2024: Democratic, Republican, Libertarian, We The People, Indiana Redemption Party; 2020: office `Straight Party` present). MEDSL 2024 has `STRAIGHT PARTY` (1,065 St. Joseph rows). Not found for 2022. Caveat: straight-party votes are counted in addition to or inside the office totals depending on the source; not checked.

## Sample rows (proving St. Joseph precincts)

2024 OpenElections (county,precinct,office,district,party,candidate,votes):
- St. Joseph,CENTRE TWP 1 010001,President Of The United States,,REP,Donald J. Trump Jd Vance,463
- St. Joseph,CENTRE TWP 1 010001,President Of The United States,,DEM,Kamala D. Harris Tim Walz,278
- St. Joseph,PORTAGE TWP 1 120001,Governor And Lieutenant Governor,,REP,Mike Braun Micah Beckwith,134
- St. Joseph,PORTAGE TWP 1 120001,Governor And Lieutenant Governor,,DEM,Jennifer G. Mccormick Terry Goodin,283
- St. Joseph,CENTRE TWP 1 010001,Straight Party,,,Republican,335

2020 OpenElections:
- St. Joseph,Centre Twp 1,President,,DEM,Joseph R Biden,283
- St. Joseph,Centre Twp 1,President,,REP,Donald J Trump,506
- St. Joseph,Centre Twp 1,Governor,,REP,Eric Holcomb,532
- St. Joseph,Centre Twp 1,Governor,,DEM,Woodrow (Woody) Myers,224
- Countywide 2020 President sums over precincts: DEM 59,896, REP 53,164 (computed from file)

MEDSL 2024: precinct `010001`, US PRESIDENT, REPUBLICAN, DONALD J TRUMP, 463.0, county_fips 18141.

Census VTD sample: GEOID 18141002240, NAME `150005`, POP100 1415; GEOID 18141001160, NAME `110008`, POP100 1529.

## Files saved (under sources/precincts/)

- `openelections-in/20201103__in__general__st_joseph__precinct.csv` (4,358 lines)
- `openelections-in/20241105__in__general__st_joseph__precinct.csv` (17,471 lines, 1.3 MB)
- `tigerweb-vtd2020/vtd.json` (225 St. Joseph VTD polygons, GeoJSON, 1.4 MB)

## Open problems

1. 2022 general St. Joseph precinct results: no machine-readable source found. Options not yet resolved: county "Signed Official Report with precincts" PDF (site blocks automated fetch; needs a human download or approved browser step, and may be a scanned PDF needing OCR); VEST shapefile (login, CC BY-NC-ND); ENR web app (no download links found).
2. Verify OpenElections 2020 and 2024 St. Joseph numbers against the county canvass totals before use (only the 2024 and 2020 presidential sums were computed, not compared with the official canvass).
3. 2024 has 3 precinct codes (090308, 090508, 130518) with no 2020 VTD polygon; 15 VTDs have no 2024 results. Need a post-2020 St. Joseph boundary source (county GIS or the precinct-map PDFs) or a plan to merge/split.
4. 2022 precinct set unknown; 2020 VTDs may mismatch 2022 for the same reason.
5. City/town assignment for small municipalities requires a spatial join and a rule for precincts split by town lines.
6. MEDSL 2024 file mixes two precinct name forms (428 strings for 213 precincts): dedupe if used.
7. Candidate/party labeling differs between years and sources (e.g. "Joseph R Biden" vs "Kamala D. Harris Tim Walz"; party "WI" for write-ins); mapping to D/R/other must be done per year.
8. Licence: OpenElections (MIT) and MEDSL (CC0) are clear; VEST/UF archive carries NC-ND terms.
9. Straight-party counting method and its effect on vote shares not checked.
