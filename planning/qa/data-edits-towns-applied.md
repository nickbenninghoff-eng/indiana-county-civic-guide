# Town data edits: apply log (2026-11-08)

Edits: planning/qa/data-edits-towns.csv (100 rows). Research: planning/qa/towns-research.md.

## Renumbering (proposed -> assigned)

- GOV-201 -> GOV-103
- GOV-202 -> GOV-104
- GOV-203 -> GOV-105
- GOV-204 -> GOV-106
- GOV-205 -> GOV-107
- GOV-206 -> GOV-108
- GOV-207 -> GOV-109
- GOV-208 -> GOV-110
- GOV-209 -> GOV-111
- GOV-210 -> GOV-112
- GOV-211 -> GOV-113
- GOV-212 -> GOV-114
- GOV-213 -> GOV-115
- GOV-214 -> GOV-116
- GOV-215 -> GOV-117
- GOV-216 -> GOV-118
- GOV-217 -> GOV-119
- GOV-218 -> GOV-120
- GOV-219 -> GOV-121

## Applied (86)

- #0 GOV-103 new source row (proposed as GOV-103)
- #1 GOV-104 new source row (proposed as GOV-104)
- #2 GOV-105 new source row (proposed as GOV-105)
- #3 GOV-106 new source row (proposed as GOV-106)
- #4 GOV-107 new source row (proposed as GOV-107)
- #5 GOV-108 new source row (proposed as GOV-108)
- #6 GOV-109 new source row (proposed as GOV-109)
- #7 GOV-110 new source row (proposed as GOV-110)
- #8 GOV-111 new source row (proposed as GOV-111)
- #9 GOV-112 new source row (proposed as GOV-112)
- #10 GOV-113 new source row (proposed as GOV-113)
- #11 GOV-114 new source row (proposed as GOV-114)
- #12 GOV-115 new source row (proposed as GOV-115)
- #13 GOV-116 new source row (proposed as GOV-116)
- #14 GOV-117 new source row (proposed as GOV-117)
- #15 GOV-118 new source row (proposed as GOV-118)
- #16 GOV-119 new source row (proposed as GOV-119)
- #17 GOV-120 new source row (proposed as GOV-120)
- #18 GOV-121 new source row (proposed as GOV-121)
- #19 offices roseland-council next_election
- #20 offices roseland-council source_ids
- #21 offices new-carlisle-council seats
- #22 offices new-carlisle-council next_election
- #23 offices new-carlisle-council status
- #24 offices new-carlisle-council source_ids
- #25 offices new-carlisle-council notes
- #26 offices new-carlisle-clerk-treasurer next_election
- #27 offices new-carlisle-clerk-treasurer source_ids
- #28 offices new-carlisle-clerk-treasurer notes
- #29 offices north-liberty-council status
- #30 offices north-liberty-council next_election
- #31 offices north-liberty-council source_ids
- #32 offices north-liberty-council notes
- #33 offices north-liberty-clerk-treasurer inserted
- #34 offices lakeville-council seats
- #35 offices lakeville-council status
- #36 offices lakeville-council next_election
- #37 offices lakeville-council source_ids
- #38 offices lakeville-clerk-treasurer next_election
- #39 offices lakeville-clerk-treasurer status
- #40 offices lakeville-clerk-treasurer source_ids
- #41 offices indian-village-clerk-treasurer inserted
- #43 units indian-village status
- #44 units indian-village source_ids
- #45 units indian-village notes
- #46 units lakeville source_ids
- #47 units lakeville notes
- #48 units new-carlisle notes
- #49 units new-carlisle source_ids
- #50 units north-liberty notes
- #51 units north-liberty source_ids
- #52 terms roseland-clerk-treasurer__williams-inez__2024-01 end
- #53 terms roseland-council__catanzarite__2024-01 end
- #54 terms roseland-clerk-treasurer__rulli__2024-09 inserted
- #56 terms new-carlisle-clerk-treasurer__moffitt__2019-01 inserted
- #57 terms new-carlisle-clerk-treasurer__brown__2024-01 inserted
- #58 terms new-carlisle-council__kauffman__2023-01 inserted
- #59 terms new-carlisle-council__short__2023-01 inserted
- #60 terms new-carlisle-council__colanese__2024-01 inserted
- #61 terms new-carlisle-council__pemberton__2024-01 inserted
- #62 terms new-carlisle-council__abbott__2024-01 inserted
- #65 terms north-liberty-clerk-treasurer__kitchen__2019-01 inserted
- #66 terms north-liberty-council__randy-lemert__unk inserted
- #67 terms north-liberty-council__will-groves-jr__unk inserted
- #68 terms north-liberty-council__joe-reed__unk inserted
- #69 terms north-liberty-council__tom-england__unk inserted
- #70 terms north-liberty-council__gerry-brown__unk inserted
- #73 terms lakeville-clerk-treasurer__carr__unk inserted
- #74 terms lakeville-council__lori-kelly__unk inserted
- #75 terms lakeville-council__april-hathaway__unk inserted
- #76 terms lakeville-council__dean-rouch__unk inserted
- #77 terms indian-village-clerk-treasurer__jozwiak__2012-01 inserted
- #78 terms indian-village-clerk-treasurer__schosker__2004-01 inserted
- #79 terms indian-village-council__oppenheim__2013-01 inserted
- #80 terms indian-village-council__oppenheim__2005-01 inserted
- #81 terms south-bend-council-d5__wax__unk confidence
- #82 terms south-bend-council-d5__wax__unk source_ids
- #84 results 2026g-new-carlisle-council-at-large | Marcy L Kauffman vote_for=2
- #86 results 2026g-new-carlisle-council-at-large | Dan Caruso vote_for=2
- #88 results 2026g-new-carlisle-council-at-large | Marcellus (Marcel) Lebbin vote_for=2
- #90 results 2026g-north-liberty-council-at-large | Gerry E Brown vote_for=2
- #92 results 2026g-north-liberty-council-at-large | Tom England vote_for=2
- #94 results 2026g-roseland-council-at-large | Julie Mudrovich vote_for=1
- #96 results 2026g-roseland-council-at-large | Tom Clark vote_for=1
- #97 gaps_gov terms | Town officeholders: Lakeville, Indian Village, New Carlisle (clerk-treasurer and council 2018-2023), Osceola/Roseland/Walkerton before 2018, North Liberty before 2026
- #98 gaps_gov terms | Winners of 2026 multi-seat town races (New Carlisle, North Liberty, Roseland): seat counts not printed

## Adapted (16)

- #42 offices indian-village-council inserted (office_type town_council is not in office_types.csv; used town_council_member)
- #55 terms roseland-council__mudrovich__2027-01 confidence medium plus computed note
- #63 terms new-carlisle-council__kauffman__2027-01 id already existed: merged into the existing row (sources, notes, confidence from the edit; person and dates of the existing row kept)
- #64 terms new-carlisle-council__caruso__2027-01 id already existed: merged into the existing row (sources, notes, confidence from the edit; person and dates of the existing row kept)
- #71 terms north-liberty-council__brown__2027-01 id already existed: merged into the existing row (sources, notes, confidence from the edit; person and dates of the existing row kept)
- #72 terms north-liberty-council__england__2027-01 id already existed: merged into the existing row (sources, notes, confidence from the edit; person and dates of the existing row kept)
- #83 results 2026g-new-carlisle-council-at-large | Marcy L Kauffman winner=Y with inference note
- #85 results 2026g-new-carlisle-council-at-large | Dan Caruso winner=Y with inference note and confidence=medium
- #87 results 2026g-new-carlisle-council-at-large | Marcellus (Marcel) Lebbin winner=N with inference note and confidence=medium
- #89 results 2026g-north-liberty-council-at-large | Gerry E Brown winner=Y with inference note and confidence=low
- #91 results 2026g-north-liberty-council-at-large | Tom England winner=Y with inference note and confidence=low
- #93 results 2026g-roseland-council-at-large | Julie Mudrovich winner=Y with inference note
- #95 results 2026g-roseland-council-at-large | Tom Clark winner=N with inference note and confidence=low
- #99 gaps_elections elections-calendar | Town office cycles for Roseland, New Carlisle, North Liberty and Lakeville item updated; why_missing refreshed
- extra: removed terms row new-carlisle-council__lebbin__2027-01 (Lebbin, 228 votes, is third of three; with two seats up he does not win, per results edit #87). The conflict (seat count inferred, not printed) is recorded in gaps_gov.csv and the results notes.
- extra: edit #56 (Moffitt 2019-2023 row) inserted as proposed, but it overlapped the existing Moffitt 2012-2023 row (single-seat office), so the existing row's end was shortened to 2018-12-31 (note added).

## Skipped (0)


## Conflicts recorded

- New Carlisle: Pemberton (current page, May 2026 minutes) vs Dave Doll (2025 archive page). Data shows Pemberton; gaps_gov row added; noted in office and term notes.
- Roseland: council size 3 (Wikipedia) vs a 3-2 vote (WNDU). seats=3 kept; gaps_gov row added; offices note retained.
- Inferred 2026 multi-seat winners (New Carlisle 2 seats, North Liberty 2, Roseland 1): winners set from the seats-up reading, results confidence lowered where the winner depends on it; Lebbin term row removed; gaps_gov row (edit #98) refreshed.
