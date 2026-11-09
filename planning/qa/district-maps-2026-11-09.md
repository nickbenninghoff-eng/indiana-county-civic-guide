# District maps: what was found (2026-11-09)

Searches used: 9 of 40. Other lookups were direct fetches of known URLs and ArcGIS REST endpoints. Files are in `sources/boundaries/districts/`; the index is `manifest.csv`; sources are MAP-020 to MAP-039 in `data/editions/st-joseph/sources_maps.csv`.

## Summary table

| Set | File | Features | Status | Elections |
|---|---|---|---|---|
| County Commissioner 1-3 | county-commissioner-2022.geojson | 3 | official download | 2022, 2024, 2026 |
| County Council A-I | county-council-2022.geojson | 9 | official download | 2022, 2024, 2026 |
| South Bend Council 1-6 | south-bend-council-2022.geojson | 6 | official download | 2023 (and 2027 unless redrawn) |
| Mishawaka Council 1-6 | mishawaka-council-2022.geojson | 6 | official download | 2023 (and 2027) |
| SBCSC board SB1-SB5 | none | 0 | official PDF only (image) | 2024, 2026 |
| Walkerton wards 1-4 | none | 0 | street descriptions only | 2022 (and later) |
| Indiana House | in-house-2021.geojson | 5 | official download (Census) | 2022-2030 |
| Indiana Senate | in-senate-2021.geojson | 4 | official download (Census) | 2022-2030 |

Every GeoJSON is WGS84, keeps the source properties, and has a `district` property. Bounding boxes: county commissioner and county council -86.527/41.433 to -86.059/41.761 (exactly the county); South Bend -86.361/41.597 to -86.191/41.760; Mishawaka -86.216/41.624 to -86.098/41.736; state districts extend past the county as expected (House -86.584/41.426 to -85.870/41.761; Senate -86.931/41.171 to -85.651/41.761).

`district` labels as written: commissioner "1","2","3"; county council "A".."I"; South Bend and Mishawaka "1".."6"; House "HD5","HD6","HD7","HD8","HD21"; Senate "SD8","SD9","SD10","SD11".

## 1. County Commissioner districts

- Source: St. Joseph County GIS Hub (the county's own), ArcGIS FeatureServer `County_Commissioner_2022/FeatureServer/0`, 3 polygons, field `Dist`. Reached through the Hub group listing (MAP-020, MAP-023). The county website (sjcindiana.gov) and its Redistricting page sit behind a bot check; I did not try to get around it.
- In force: the 2021-22 redistricting fight ended with amended maps passed by the Commissioners and Council on 2022-03-01 and a judge's approval the next day (WVPE; MAP-034, MAP-035). Those govern the 2022 election (filing was reopened until 2022-03-04). The Commissioners first passed their own plan 2-1 in November 2021 and the Council overrode a veto 6-3 in December 2021; those earlier maps were not used for the 2022 election. No ordinance or resolution numbers were found.
- Check: using the 2024 official results by precinct, 73 of 73 District 2 precincts and 70 of 71 District 3 precincts sit in the matching polygon. The 71st (090204) is not in the current 2025 precinct layer. 2022 results were not independently tested.
- Confidence: high for 2024 and 2026; medium-high for 2022 (same layer, created Oct 2022, no evidence of a later change, but no 2022 precinct test).
- Odd: the current layer carries commissioner names (Baxmeyer, Morton, Hazen) from the 2025-26 board. Not used.

## 2. County Council districts A-I

- Source: `County_Council_2025/FeatureServer/0`, 9 polygons, field `COUNCIL_1` (MAP-021). The item is named 2025 and was created 2025-02-03, but the districts match the 2024 results exactly: all 96 precincts that voted in Districts D, F, G and I fall in the matching polygon.
- In force: the Council's amended maps from 2022-03-01 (see above). I could not establish whether the 2025 item changed any 2022 boundary; the 2024 match makes a change unlikely but it is not proven for 2022. File was named `county-council-2022` to match the effective election.
- Mishawaka's voter-precinct layer (MAP-027) carries a county council letter per precinct: 40 of 41 agree with this layer. Precinct 090204 says H there and tests F here (precinct no longer in the 2025 layer, so likely a precinct change).
- Confidence: high for 2024/2026, medium for 2022.

## 3. South Bend Common Council

- Source: City of South Bend ArcGIS MapServer `LandRecords/PublicEssentials/MapServer/2`, 6 polygons, field `Num` = 1-6 (MAP-024).
- In force: Ordinance 10906-22 (Bill 72-22), passed 2022-11-28, presented to the Mayor 2022-11-29 (MAP-025). It lists the precincts per district (83 precincts) under IC 36-4-6-3 and the 2020 population of 103,453. So the 2023 municipal election used the map from this ordinance. An older (pre-2022) map applied to earlier elections only; not collected.
- Check: the layer matches the ordinance's precinct lists (80 of 81 precincts tested; the miss is an oddly shaped precinct). Note the layer was created 2022-06-23, before the ordinance passed, and later edited; the geometry matches the ordinance anyway.
- 2027: no change found. The statute ties redistricting to the second year after each census, so the next is for 2032. This is from the ordinance text, not checked against a 2026 source.
- Confidence: high.

## 4. Mishawaka Common Council

- Source: City of Mishawaka GIS `Public/Council_Districts/MapServer/0` (MAP-026). 9 rows: districts 1-6 (kept) and 3 At-Large rows (no separate area; the at-large seats are voted citywide).
- In force: the city's website lists "Current Council District Boundaries (2023)", created 2023-01-27 (MAP-028). The download is a dead placeholder and the ordinance number was not found. The service document says "Council Districts 2023" but the layer metadata still says 2015. So it is likely the post-2020-census map applied in 2023, but I could not confirm that against an ordinance or a precinct list.
- Confidence: medium. A precinct-list check was not possible.

## 5. School boards

SBCSC (South Bend):
- Board has seven members: five elected by district (labelled SB1-SB5 on the map) and two at-large (MAP-031). Statute is IC 20-23-15 (section headings read only; MAP-038). The 2024 ballot labels were At-Large (choose two), District 3 and District 4 (MAP-037), which agrees with filings that say "District 1", "District 5", "At-Large". Note the map labels are "SB1..SB5", not "District n".
- Map: image-only PDF dated 2026-10-30 (`raw/sbcsc-board/SBCSCSchoolBoardMap_10302026.pdf`). No GIS layer found, no text layer, not hand-traced. I could not view the image (no PDF renderer here; the browser's PDF viewer would not screenshot). The PDF says it shows voter precincts, so a precinct-built fallback is feasible by a person reading it.
- Partial fallback built from official results: precincts that voted in District 3 (27) and District 4 (21) in 2024 (`raw/sbcsc-board/precincts_from_2024_results.json`). Districts 1, 2, 5 appear only in election years not in the CSV results the guide holds (2022 is a PDF report).
- Unknown: whether the district map changed between the 2024 and 2026 elections. The PDF is "updated October 30, 2026", a few days before the 2026 general election; the reason for the update is unstated.
- Status: official_pdf_only.

Penn-Harris-Madison:
- Seven trustees: Penn Township 3, Harris Township 2, Madison Township 1, one at-large (MAP-033). These are township residency seats, not drawn districts, so no new polygons are needed (townships already in `sources/boundaries/townships.geojson`).
- Who votes: the 2024 official results show the same 36 precincts voting for both the Penn and Harris seats, i.e. voted across the whole school corporation, with residency required. This is inferred from results; I did not find the statute section. Ballot wording "Penn Township (choose two)" fits. Filings' "Penn Township seat" = a seat held by a Penn resident.

## 6. Town councils

- Walkerton: five-member council, elected "both by ward and at large" (Code Sec. 11.01, MAP-036). Wards 1-4 are described by street boundaries (Ord. passed 12-1982; Ord. 2002-08); Ward 5 is the whole town (the at-large member). The ward map is on file with the Clerk-Treasurer; no download or GIS layer found. Wards 2, 3, 4 in filings fit this. Status not_found for a polygon file. The written description controls over the map.
- New Carlisle, North Liberty, Roseland: the 2022 official county report labels their council races AT-LARGE (existing source MAP-007). No ward maps exist.
- Lakeville, Osceola: not found in the 2022 report and not searched further. Unknown.

## 7. State legislative districts

- Source: Census TIGERweb Legislative MapServer layers 1 (Senate) and 2 (House), 2026 vintage (MAP-029, MAP-030). Indiana's legislative map was set in the 2021 redistricting and used 2022-2030; the 2026 vintage should be the same shapes (I did not compare with the 2022 vintage).
- Districts kept: House 5, 6, 7, 8, 21 (shares of the county's area about 10, 4, 70, 12, 3.5 percent); Senate 8, 9, 10, 11 (about 24, 22, 43, 12 percent). A box query alone also returned House 17, 20, 37, 48 and Senate 12, 17; sampling showed those only touch the box, not the county, so they are excluded. Cross-check: the 2024 OpenElections file has State Representative 5, 6, 7, 8, 21 and State Senate 8, 9, 10 on St. Joseph ballots; Senate 11 was not in the files read (not its election years).
- Confidence: high for the shapes; the 1 percent overlap cutoff for inclusion is mine.

## Not obtained / next steps

- Walkerton ward polygons (ask the Clerk-Treasurer, or build from the street descriptions plus precinct lines).
- SBCSC board polygons or precinct lists (read the PDF map, or request from the school corporation).
- Mishawaka ordinance text/number and the 2023 boundaries file.
- County redistricting ordinance and resolution numbers (county site blocked by a bot check).
- IC 20-23-15 section text (Justia and FindLaw blocked).
- Lakeville and Osceola.
- Pre-2022 county, South Bend and Mishawaka maps are not needed for the guide's 2022-2026 data.
