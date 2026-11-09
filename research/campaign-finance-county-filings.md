# St. Joseph County, IN: locally filed campaign finance reports (county Candidate Filings page)

Collected 2026-11-07 via Claude in Chrome from https://www.sjcindiana.gov/2330/Candidate-Filings. All DocumentCenter links are `https://www.sjcindiana.gov/DocumentCenter/View/<ID>`. Neutral and factual; no private individuals' addresses recorded.

## 0. Status and scope (read first)

- The page posts **1,021 documents** in 16 tabs (none empty). That is far more than a handful: roughly 740 are non-committee-roster files, of which several hundred are CFA-4 scans, many 4 to 36 pages long.
- Every PDF is a scanned image with no text layer. In-browser OCR (pdf.js + tesseract.js) of the summary sheet takes 10 to 40 seconds per document and the form's boxed digits OCR poorly; line 14-18 values are frequently garbled. Full transcription of every CFA-4 is therefore **not done**.
- **Completed:** full inventory (section, ID, title) for all 736 financial/candidacy documents; counts for the 285 delegate/precinct-committee filings; summary-sheet OCR of 28 of the 78 documents in the **2026 Pre-General** tab, 14 of which are usable below with arithmetic cross-checks. Mueller 2023 Annual was already transcribed in `08-browser-findings.md` (not repeated).
- **Not done:** CFA-11 contributor/amount transcription (page-1 OCR returned only form headers; need visual zoom), Schedule A top-contributor lists, and every CFA-4 outside the 2026 Pre-General tab (2023, 2024, 2025 annual, 2024/2026 pre-primary and pre-election). Recommended next step: authorize a larger run (about 600 CFA-4s), ideally split across several browser sessions and with screenshot zoom for numeric lines, or file a records request for structured data (see section 5).
- Form notes: CFA-4 "This Period" is column A, "Year to Date" is column B. Line 16 = line 13 + 15c; line 18 = line 16 - 17c.

## 2. CFA-4 summary table (2026 Pre-General tab; period 4/11/2026 to 10/09/2026 unless noted)

"Derived" means computed from other OCR'd lines by the form's own arithmetic rather than read directly. Values in parentheses are OCR readings that failed the cross-check. Blank = not readable.

| ID (URL suffix) | Committee | Candidate | Office | Party | Report | Cash start (A) | Receipts this period (15c) | Receipts YTD (15c) | Expenditures this period (17c) | Expenditures YTD | Cash end (line 18) | Debts | Check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 72843 | Committee to Elect Abby Doyle | Abigail "Abby" Doyle | County Auditor | Republican | Pre-election, 4/11-10/09/2026, signed 10/16/2026 | 3,508.64 | 43,961.15 (derived; OCR 43,960.80) | 44,211.15 | 42,625.87 (derived) | 42,625.87 | 4,843.92 derived (OCR 5,063.92) | none read | OCR-uncertain: line 18 OCR differs from arithmetic by 220.00 |
| 72787 | Amy Rolfes for County Clerk | Amy Conlin Rolfes | County Clerk | Republican | Pre-election, 4/11-10/09/2026 | 19,254.86 | 27,670.11 (derived from line 16) | | 28,646.91 | 29,336.16 | 18,278.06 (derived) | | line 16 = 46,924.97 read; 17a 27,989.16 + 17b 657.75 = 28,646.91 OK; OCR-uncertain |
| 72846 | Amy Cressy for Prosecutor | Amy S. Cressy | (Prosecutor per committee name) | Democrat | Pre-election, 4/11-10/09/2026 | 19,981.24 | 35,381.00 (26,075.00 itemized + 9,306.00 unitemized) | 47,074.00 | 50,906.64 itemized + 295.87 unitemized (period assignment of 295.87 unverified) | 56,051.92 itemized | derived 4,159.73 if 295.87 is period | | receipts and line 16 (55,362.24; YTD 60,534.80) cross-check OK; expenditures OCR-uncertain |
| 72804 | Elect Jason Critchlow | Jason Critchlow | (not read) | Democrat | Pre-election, 4/11-10/09/2026 | 107,259.33 | 161,368.00 (159,368.00 itemized + 2,000.00 unitemized) | 216,608.00 (213,273.00 + 3,335.00) | | | | | receipts OK; expenditures line truncated (17a 17,228.50 period; 28,470.46 YTD)) |
| 72844 | (Amy Drake committee) | Amy Marie Drake | (not read) | Republican | Pre-election | | | 154,246.17 | | 143,036.48 | | | OCR-uncertain; only YTD figures readable |
| 72832 | Jamie O'Brien Committee | Jamie O'Brien | (not read) | Republican | Pre-election | 29,480.94 | 73,769.10 (73,219.10 + 550.00) | 90,465.83 (88,790.83 + 1,675.00) | | | | | receipts and line 16 (103,250.04; YTD 155,481.77) cross-check OK; expenditures not read |
| 72833 | Drake and O'Brien PAC | (PAC) | PAC | | Pre-election | 157.10 | 129,198.53 (126,268.35 + 2,930.18) | 135,226.53 (132,018.35 + 3,208.18) | | | | | receipts and line 16 (129,355.63; YTD 136,195.28) cross-check OK; expenditures not read |
| 72863 | Joe Thomas for County Council | Joe Thomas | County Council | Republican | Pre-election | 34,489.27 | 2,100.00 | 2,100.00 | 21,847.15 | 22,997.15 | 14,742.12 | | cross-check OK both columns (jan-1 balance 35,639.27) |
| 72855 | Committee to Elect Emily McClements | Emily McClements | (not read) | Independent | Pre-election | 0 (blank) | 3,223.99 (2,955.75 + 268.24) | 3,223.99 | 2,057.90 | 2,057.90 | 1,166.09 (derived) | | OK |
| 72858 | Baska for Harris Township Board | Jacob "Jake" Baska | Harris Township Board | Democrat | Pre-election | 844.03 | 1,127.48 | 2,633.61 | 1,250.00 | 1,912.10 | 721.51 | | cross-check OK both columns |
| 72854 | Portolese for Penn Township Trustee | Doris J. Portolese | Penn Township Trustee | Republican | Pre-election, 1/1-10/16/2026 | | | | 17,805.86 | | 4,493.76 | | line 16 = 22,299.62 read; minus 17c = 4,493.76 OK; receipts breakdown unreadable |
| 72852 | (Donlon committee) | Christy L. Donlon | (not read) | Democratic | Report 1/1-10/15/2026 | 0 | 1,250.00 | 1,250.00 | 1,030.97 | 1,030.97 | 219.03 | | OK |
| 72799 | St. Joseph County Young Republicans | (committee) | party committee | Republican | Pre-election | 2,396.59 | 1,659.98 | 2,446.98 | 970.17 | 1,922.67 | 3,086.90 (arithmetic gives 3,086.40) | | OCR-uncertain by 0.50 |
| 72806 | Committee to Elect John Maciejczyk, Prosecutor | John Maciejczyk | Prosecutor | GOP | period reads 8/01/26-10/09/26 | | about 30,260 | | | | | | OCR-uncertain; handwriting; not usable |

Read but not usable (page 1 not a clean summary sheet, or digits unreadable): Autumn Kaylor (72789, "Autumn for Auditor", Democrat), Brett Maurer (72848, Democrat), Cheryl Ashe (72793; 1-page, appears zero/low activity), Dan Caruso (72795, "Caruso for Council", Democrat), Carl Baxmeyer (72791, "Baxmeyer for Commissioner", 23 pages), Jan Cervelli (72861 and amendment 73116, "Jan Cervelli for County Council"), Cherie DeFreese (72850).

## 3. CFA-11 (large contribution notices) table

Posted in the 2026 Pre-General tab (IDs and filer names from titles). **Contributor and amount not yet transcribed** (page-1 OCR produced only form headers; needs zoomed visual read).

| ID | Candidate (from title) | Title as posted |
|---|---|---|
| 73114 | Abby Doyle | Abby Doyle CFA 11 |
| 72953, 73124, 73120 | Amy Drake | CFA 11, 11.2, 11.3 |
| 72951 | Amy Rolfes | Amy Rolfes CFA11 |
| 73111 | Carl Baxmeyer | CFA 11 |
| 73123 | Jamie O'Brien | CFA 11 |
| 72802, 72859 | Jan Cervelli | CFA 11, 11.2 |
| 73115, 72954 | John Maciejczyk | CFA 11, CFA-11 |
| 73112, 73121 | Mike Castellon | CFA 11, 11.2 |
| 73117 | Robert "Bob" Price | CFA 11 |
| 72882 | Robert "Bobby K" Kruszynski | CFA 11 |
| 73122, 73118 | Scott Ruszkowski | CFA 11, 11.2 |
| 72841 | William "Bill" Redman | CFA 11 |

Also in the 2026 Pre-Election tab (tab 3): CFA 11 files for Amy Rolfes (71873), Jamie O'Brien (71874), Scott Ruszkowski (71875), Amy Drake (71869), Cervelli (71870), Matt Clayton (71871), Ranjan Rohatgi (71872). Not read.

Amended CFA-4s noted in the 2026 Pre-General tab: Jan Cervelli (73116), Mike Castellon (73113 CFA 4, 73125 amendment), Michael Dvorak (73119), SJC GOP (72950, amendment 72952), Stephanie Ball amended primary (72778).

## 4. OCR-uncertain list

- 72843 Doyle: line 14 (Jan 1 balance) OCR 3,478.64 vs arithmetic 3,258.64; line 15c period OCR 43,960.80 vs arithmetic 43,961.15; line 18 OCR 5,063.92 vs arithmetic 4,843.92. Needs visual check.
- 72787 Rolfes: 15c and line 18 derived, not read; 15c OCR 7,650.86 is inconsistent.
- 72846 Cressy: which column 295.87 (17b) belongs to; ending cash unverified.
- 72804 Critchlow: expenditures and end cash unread.
- 72844 Drake, 72806 Maciejczyk, 72799 Young Republicans (0.50 mismatch): as noted above.
- 72832 O'Brien and 72833 Drake and O'Brien PAC: expenditures and end cash unread.
- All "check OK" rows rely on OCR of boxed digits that passed the form's arithmetic; the match makes misreads unlikely but they have not been visually confirmed.
- Candidate names and office fields were OCR'd from handwriting in places; confirm against the image before publishing.
- Amy Drake's committee: the Drake and O'Brien PAC amounts (about $129k receipts) are large; PAC and candidate committee are distinct filers.

## 5. What is NOT posted online (scope for a public records request)

- Election years with no posted local campaign finance reports: **2022 and earlier** (earliest tab is 2023 Annual). No 2023 pre-primary/pre-election tab, no 2025 pre-election tab.
- Posted: 2023 Annual; 2024 Pre-Primary, Pre-Election, Annual and Delinquent Annual; 2025 Annual; 2026 Pre-Election, May Primary tab, and 2026 Pre-General (with CFA-11). No **2024 Pre-General** or post-election/final reports tab for 2024; no 2026 **Annual** (due January 2027) or post-general reports yet.
- Coverage by committee is partial: the 2023 Annual tab lists 80 files, but per `08-browser-findings.md` only some committees appear for some periods; 2026 Pre-General has 78 files against more committees than that on the other tabs. A records request should ask for every CFA-4 filed with the County Election Board (Clerk) for each period, including ones not posted.
- Offices to cover in a request: mayors (South Bend, Mishawaka), common councils, county offices (auditor, clerk, prosecutor, assessor, sheriff, commissioner, council), township trustees and boards, school boards (2024 tab lists SB, Penn-Harris-Madison, John Glenn, Mishawaka, New Prairie and others; 2026 tab not read), and party committees (Democratic Central Committee, SJC Republican Party, Young Republicans, Mishawaka Republican City Committee, firefighters PAC, Save Our Schools PAC).
- Not posted as structured data: all files are image scans; there is no downloadable spreadsheet. Ask for electronic copies of the underlying filings or data exports.
- State-level filers (legislators, statewide) file with the Indiana Election Division; see `06-campaign-finance.md`.
- Precinct committee and delegate filings: counts only. 2026 = 225 documents; 2024 = 60 documents. These are candidacy filings, not finance reports.

## 1. Inventory by section (full list at end of file)

Source page: https://www.sjcindiana.gov/2330/Candidate-Filings (16 tab panels, all populated in the DOM; none empty). Every document URL is `https://www.sjcindiana.gov/DocumentCenter/View/<ID>`. Section totals are unique DocumentCenter IDs per tab; 1,021 in all.

| Tab | Section | Docs | Note |
|---|---|---|---|
| 0 | 2026 PRE General Election CFA-4 and CFA-11 | 78 | Mix of CFA-4 (period 4/11/2026-10/09/2026 where read) and CFA-11 large-contribution notices (titles containing "CFA 11") |
| 1 | 2026 General Ballot Vacancy | 17 | Candidacy filings for general-election ballot vacancies (one titled "CAN 12"); not opened |
| 2 | 2026 School Board | 17 | Not opened; likely school-board candidacy filings (no financial data read) |
| 3 | 2026 Pre-Election CFA-4 | 57 | CFA-4 reports (tab title); includes CFA-11 files; filed before the 2026 primary; not opened |
| 4 | 2026 Delegates and Precinct Committeeman | 225 | Candidacy filings (delegate / precinct committee). Counted only; not listed or transcribed. |
| 5 | 2026 May Primary | 114 | Per-candidate files named only by candidate; likely candidacy filings (CAN-x); not opened |
| 6 | 2025 Annual CFA-4 | 142 | CFA-4 annual reports (tab title); includes amended reports and an outgoing-treasurer report; not opened |
| 7 | 2024 Pre-Primary CFA-4 | 25 | CFA-4 (tab title); not opened |
| 8 | May 2024 Primary | 22 | Per-candidate files tagged (R)/(D); likely candidacy filings; not opened |
| 9 | 2024 Precinct Committeeman | 60 | Candidacy filings (delegate / precinct committee). Counted only; not listed or transcribed. |
| 10 | 2024 School Board | 25 | Per-candidate files tagged by school corporation; not opened |
| 11 | Late Ballot Vacancies | 3 | Not opened |
| 12 | 2024 Pre-Election CFA-4 | 34 | CFA-4 (tab title); not opened |
| 13 | 2024 Annual CFA-4 | 121 | CFA-4 annual reports (tab title); not opened |
| 14 | 2024 Delinquent Annual CFA-4 | 1 | Single file; not opened |
| 15 | 2023 Annual CFA-4 | 80 | CFA-4 annual reports (tab title); only Mueller summary transcribed (see 08-browser-findings.md) |

Tab 13 note: one ID is listed twice with the same name pattern in two tabs; counts above are per-tab. Tab 13 count is 121 unique IDs (122 anchors; one untitled link, ID 65643, appears between Broden and Maciejczyk).

Delegate / precinct counts: 2026 = 225 documents; 2024 = 60 documents (document counts, not necessarily unique candidates; one candidate may have more than one file).

### Full document list (tab, ID, title as posted)

**Tab 0: 2026 PRE General Election CFA-4 and CFA-11 (78 listed)**

72843 Abby Doyle, 73114 Abby Doyle CFA 11, 72844 Amy Drake, 72953 Amy Drake CFA 11, 73124 Amy Drake CFA 11.2, 73120 Amy Drake CFA 11.3, 72787 Amy Rolfes, 72951 Amy Rolfes CFA11, 72846 Amy S. Cressy, 72789 Autumn Kaylor, 72848 Brett Maurer, 72791 Carl Baxmeyer, 73111 Carl Baxmeyer CFA 11, 72850 Cherie DeFreese, 72793 Cheryl Ashe, 72852 Christy Donlon, 72795 Dan Caruso, 72854 Doris J. Portolese, 72833 Drake O'Brien PAC, 72855 Emily McClements, 72799 GOP Young Republicans, 72858 Jacob "Jake" Baska, 72832 Jamie O'Brien, 73123 Jamie OBrien CFA 11, 72861 Jan Cervelli, 72802 Jan Cervelli CFA 11, 72859 Jan Cervelli CFA 11.2, 73116 Jan Cervelli CFA 4 Amendment, 72804 Jason Critchlow, 72863 Joe Thomas, 72806 John Maciejczyk, 73115 John Maciejczyk CFA 11, 72954 John Maciejczyk CFA-11, 72865 John Paczesny, 72808 Josh Lange, 72867 Kelly Carrico, 72810 Kenneth E. "Ken" Lindsay, 72869 Lori Camp, 72812 Marcellus "Marcel" Lebbin, 72871 Marcy L. Kauffman, 72814 Mark Voelker, 72873 Matt Clayton, 72816 Michael "Mike" Castellon, 73119 Michael Dvorak CFA 4, 72875 Michelle M. Shaw, 73125 Mike Castellon Amendment CFA 4, 73112 Mike Castellon CFA 11, 73121 Mike Castellon CFA 11.2, 73113 Mike Castellon CFA 4, 72818 Mike Hamann, 72877 Muhammad Shabazz II, 72820 Nancy B. Duncan, 72879 Patric "Pat" Richter, 72822 R.Greg Payne, 72881 Ranjan Rohatgi, 73117 Robert "Bob" Price CFA 11, 72825 Robert "Bobby K" Kruszynski, 72882 Robert "Bobby K" Kruszynski CFA 11, 72826 Rodney "Rod" Laureys, 72885 Ron Baker, 72828 Ryan Callahan, 72887 Ryan Hill, 72830 Scott D. Searfoss, 72889 Scott Ruszkowski, 73122 Scott Ruszkowski CFA 11, 73118 Scott Ruszkowski CFA 11.2, 72776 Sharon Brinker, 72835 SJC Democratic Central Committee, 72856 SJC Fire Fighters PAC, 72950 SJC GOP CFA 4, 72952 SJC GOP CFA-4 Amend, 72837 Stephanie Ball, 72778 Stephanie Ball Amended Primary CFA 4, 72838 Veronica Vos, 72781 Vic Cummings, 72840 Wendy Lu yuhasz, 72784 William "Bill" Redman, 72841 William "Bill" Redman CFA 11

**Tab 1: 2026 General Ballot Vacancy (17 listed)**

72287 Christy Donlon 2, 72106 Tom Clark, 71976 Ron DeWinter, 72107 Matt Girard, 72099 Matt Clayton, 72286 Dan Caruso 2, 72100 Marcy L. Kauffman, 72101 Lloyd (Steve) Weldy, 72102 Dan Caruso, 72103 Dan Caruso CAN 12, 72285 Autumn Kaylor 2, 71977 Christy Donlon, 72104 Brianna Kosinski, 72105 Autumn Kaylor, 72117 Tom England, 72288 Marcy L. Kauffman 2, 72300 John Maciejczyk

**Tab 2: 2026 School Board (17 listed)**

71934 Cheryl Moody, 71984 Emily McClements, 71974 John Paczesny, 72018 Kevin Hawkins, 71971 Mark Costello, 71982 Chris Riley, 71890 Dana Sullivan, 71935 Jen Smoker, 71983 Larry Beehler, 71981 Holly Parks, 71979 Carissa Smith, 71978 Christine Carson, 71972 Dennis Leon Metz Jr., 71980 Todd A. McGaughey, 72079 Arden Balmer, 72080 Bradley Sherman, 72078 Thomas Strang

**Tab 3: 2026 Pre-Election CFA-4 (57 listed)**

70513 Abigail "Abby" Doyle, 70514 Amy Marie Drake, 70524 Amy Rolfes, 70525 Amy S. Cressy, 70526 Anthony Gerard VanOverberghe, 70527 Carl H. Baxmeyer, 71873 CFA 11 Amy Rolfes, 71874 CFA 11 Jamie OBrien, 71875 CFA 11 Scott Ruszkowski, 71869 CFA11 Amy Drake, 71870 CFA11 Cervelli, 71871 CFA11 Matt Clayton, 71872 CFA11 Ranjan Rohatgi, 70528 Cherie DeFreese, 71864 Cheryl Ashe, 70529 Daniel Joseph Schaetzle, 70530 Dave Thomas, 71462 Doug Stutzman, 70531 Drake and O'Brien PAC, 70532 Earl Bernard Wigfall, 70533 Jacob Jake Baska, 70534 James O'Brien, 70535 Janice Ann Cervelli, 70536 Jason Critchlow, 70537 Jennifer Louise Shabazz, 70538 Joe Thomas, 70540 Joshua David Lange, 70539 Joshua David Lange part2, 70541 Kelly Marie Carrico, 70542 Kenneth E. Lindsay, 70543 Lori Ann Camp, 70544 Lynn Coleman, 70545 Marcellus Marcel Lebbin, 70546 Matthew Clayton, 70547 Michael Castellon Mike part 2, 70548 Mike Castellon, 70549 Mike Hamann, 70550 Muhmmad A. Shabazz II, 70560 Pete Cook, 70551 Ranjan Rohatgi, 70552 Robert L. Bobby K Kruszynski JR., 70553 Rod Gene Laureys, 70554 Ron F. Baker, 70555 Ryan Callahan, 70556 Ryan William Hill, 70557 Scott D. Searfoss, 70558 Scott Ruszkowski, 70559 Sean O'Brien, 70515 Sharon Brinker, 70517 St. Joseph County Democratic Central Commitee, 70518 St. Joseph County Firefighters PAC, 70516 St. Joseph County Republican Party, 70519 St. Joseph County Young Republicans, 71298 Stephanie Ball, 70521 Tom McCormick, 70522 Veronica Vos, 70523 Victor CC Cummings

**Tab 5: 2026 May Primary (114 listed)**

68159 Abby Doyle, 68534 Alex Jimenez, 67948 Amy Marie Drake, 68243 Amy Drake - Amended, 68173 Amy Rolfes, 68435 Alexa Johnson, 68117 Anthony Vanoverberghe, 68536 Bertran Skelton, 68272 Betty Kolacz, 68363 Bill Redman, 68537 Billie Limberopoulas, 68538 Bobby K Kruszynski, 68539 Brandon Wardrip, 68030 Breanne Goodsell, 68281 Breanne Goodsell -, 68436 Brett C Maurer, 68540 Bryan Albright, 68336 Bryan Tanner, 68119 Carl H. Baxmeyer, 67924 Charles Kulp, 68028 Cherie DeFreese, 68350 Cheryl Lynn Ashe, 68541 Christopher Bowman, 68542 Christopher Winchell, 68543 Daniel Schaetzle, 67925 Dave Thomas, 68544 David Hoffman, 68545 Doloris Schosker, 68546 Earl Wigfall, 68547 Emily Dittmar, 68548 Emily Rupchok, 68549 Eric Griffin, 68550 Ethan Barden, 67951 Gail Figg, 68105 Gail Figg Amended CAN 12, 68551 Gene Reese, 68552 George Schafer, 68193 Gerry Brown, 68553 Jacob Baska, 68619 James O'Brien, 68106 Jan Cervelli, 68273 Jason M, Critchlow, 68337 Jennifer L Robinson, 67950 Joe Thomas, 68274 Joshua A. Albright, 68554 Joshua Lange, 68194 Judith Galloway, 68244 Julie Mudrovich, 68555 Karen Vargo, 68556 Karla Kreczmer-Baker, 68557 Kathryn Fischer, 68558 Kathryn Troester, 68107 Keith Batzel, 68108 Kelly Carrico, 68359 Kelsi Sheaks, 68559 Kenneth E. (Ken) Lindsay, 68437 Kent D Hizer, 68283 Kevin (KG) Conery, 68331 Kevin McClanahan, 68560 Kimberly Gorski, 68561 Kristian Verash, 68110 Lori A. Camp, 67926 Maggie DeMaegd, 68111 Maggie DeMaegd - Amended, 68245 Maggie DeMaegd - Amended 2, 68562 Marcellus (Marcel) Lebbin, 68332 Mark Voelker, 68563 Marka Johnson, 68564 Matthew Clayton, 68031 Matthew Meert, 68175 Matthew Meert, 68438 Michelle M Shaw, 68029 Mike Castellon, 68275 Mike Hamann, 68565 Misty Bozman, 68566 Muhammad Shabazz, 68113 Nancy B. Duncan, 68195 Patric N. (Pat) Richter, 68567 Peter Cook, 68114 Ranjan Rohatgi, 68568 Rhett Harris, 68569 Richard Schmidt, 68570 Rick Coffman, 68571 Ricky Smith, 68439 Robbie M. Thomas, 68572 Robert Fox, 68032 Robert H Middlebrook, 68573 Robert Payne, 68440 Robert (Bob) L. Price, 67946 Rod G. Laureys, 68351 Rod Laureys-, 68360 Ron Baker, 68334 Rudy Monterrosa, 68574 Russell King, 68178 Ryan Callahan, 68027 Ryan Schafer, 68310 Scott Ruszkowski, 68527 Scott Searfoss, 68575 Sean O'Brien, 68528 Shane Whitmer, 68529 Sharon Brinker, 68530 Sheila Laidig, 68271 Stephanie Ball, 68531 Terrie Bickel, 68115 Tim Creason, 68362 Timothy Lindewald, 68322 Thomas J. Lindenman, 68532 Thomas Zmyslo, 68795 Todd Matthys, 67949 Tom E. McCormick, 68533 Victor Cummings, 68116 Veronica Vos, 68013 Wendy Lu Yuhasz, 68242 Will Miller

**Tab 6: 2025 Annual CFA-4 (142 listed)**

68240 Abigail Doyle, 67921 Al Delinski, 68241 Alan M. Grzeskowiak, 68267 Alex Bowman, 68082 Amy Cressy, 67909 Amy Drake, 68150 Amy Drake Exploratory, 67918 Amy Drake, 68207 Amy Rolfes, 68180 Andy Kostielney, 68083 Anthony Underly, 67983 Andy Rutten, 68330 Andy Rutten-, 68208 Anthony (Tony) Hazen, 68015 Benjamin Dallas, 68268 Bianca Tirado, 67927 Bryan Tanner, 68250 Candace Brown, 68251 Canneth Lee, 68209 Carl Baxmeyer, 67928 Charles Kulp, 67922 Cherie DeFreese, 68125 Cherie DeFreese-Amended, 68320 Christopher Riley, 67985 Dale (Woody) Emmons, 68211 Dan Schaetzle, 68151 Daniel P. Chamberlin, 68212 Dave Schmidt, 68252 Dave Wood, 68181 Debbie Ladyga-Block, 68157 Derek D. Deiter, 68213 Diana Hess, 68284 Doris Portolese, 67910 Drake and O'Brien PAC, 68321 Eli Wax, 68214 Emily Ditmar, 68160 Gary Fox, 68070 Gene Reese, 68034 Gerry E. Brown, 68285 Gregg Hixenbaugh, 68217 James Mueller, 68216 James Mueller - Outgoing treasurer report, 67911 James O'Brien, 67919 James O'Brien Amended, 68152 James O'Brien -, 68253 James Turnwald, 68170 Janice Cervelli, 68147 Jason Allen Cichowicz, 67912 Jason Critchlow, 68171 Jason Critchlow, 68035 Jason Mazurkiewicz, 68254 Jeff Fansler, 68338 Jennifer Robison, 68218 Jennifer Shabazz, 68255 Joe Thomas, 68071 John E. Broden, 68127 John E. Broden -Amended, 67913 John Maciejczyk, 67935 John Murphy, 68288 John Murphy, 68256 Joseph Carbone, 68072 Joseph I Reed, 68126 Joyce Amber Joiner, 68219 Judith Galloway, 68248 Julie Brown, 68220 Julie Mudrovich, 68182 Kareemah Fowler, 68153 Karol S.Jackson, 68166 Karen White, 68154 Kate Voelker, 68258 Katie Inabit Bell, 68221 Kathryn Sue Hiser Lee, 68084 Kenneth P. Cotter, 68210 Kenneth P. Cotter -, 68073 Kenneth E. Lindsay, 68259 Lacy Hahn, 68123 Lori Camp, 67914 Loris Zappia, 68155 Loris Zappia -, 68074 LouAnn Hazen, 67915 Maggie DeMaegd, 68172 Maggie DeMaegd, 67923 Marcus Ellison, 68276 Mark Catanzarite, 68222 Mary Beth Wisniewski, 68260 Matt Carroll, 68286 Matt Mammolent, 67916 Matthew Chaffee, 68223 Matthew Chaffee-, 68033 Michael Castellon, 68203 Michael Compton, 68441 Michael A. Dvorak, 68224 Mike Grzegorek, 68225 Mike Hamann, 68014 Nancy Pemberton, 68226 Oliver Davis -SB Common Council, 68227 Oliver Davis - SJC Commissioner, 68228 Ophelia Gooden Rodgers, 68051 Our P-H-M - Tradition of Excellence, 68229 Our P-H-M - Tradition of Excellence, 68161 Patricia Jordan, 68230 Patricia Jordan-, 68261 Rachel Tomas Morgan, 68075 Rafael A. Morton, 68148 Rafael A.Morton -, 67982 Randall Figg, 68124 Randall Figg - Amended, 68077 Randy Lemert, 68122 Ranjan Rohatgi, 68277 Ranjan Rohatgi -, 68262 Robert Kovach, 68165 Robert L. (Bobby K) Kruszynski Jr., 68156 Robert Middlebrook, 68231 Robert Gregory Payne, 67986 Rodney Gene Laureys, 68263 Ron Banicki, 68264 Rosemary Mandrici, 68265 Rudy Monterrossa, 68162 Ryan McCullough, 68164 Scott Ruszkowski, 68179 Sean O'Brien, 68232 Sharon Banicki, 68233 Sharon McBride, 68184 Sheila Niezgodski, 68183 Sheila Niezgodski, 68234 Sherry Bolden-Simpson, 67917 St. Joseph County Democratic Central Committee, 68235 St. Joseph County Democratic Central Committee, 69855 St. Joseph County Republican Party, 69856 St. Joseph County Young Republicans, 68266 Tami Springer, 68149 Theresa (Terri) Buckmaster, 68078 Thomas England, 67984 Thomas McCormick, 68121 Thomas McCormick-Amended, 68236 Tim Creason, 68079 Tony Violi, 68237 Troy Warner, 68080 Vicki L. Kitchen, 68238 Will Miller, 68081 William Scott Groves Jr., 68239 William Redman

**Tab 7: 2024 Pre-Primary CFA-4 (25 listed)**

64486 Amanda Mitchell, 62642 Andy Rutten, 62643 Candace Brown, 62644 Carolyn Topolski, 62624 Democratic Central Committee, 63665 Derek Dieter, 62625 Jason Chichowicz, 62626 Jason Piontek, 62627 Jenn Shabazz, 62628 Kent Hizer, 62629 Kris Verash, 62630 L. Zappia, 62631 Maggie DeMaegd, 62632 Mark Catanzarite, 62633 Mary Beth Wisniewski, 62634 Michael Rose, 62635 Mike McGann, 62657 Patricia Jordan, 62636 Rafael Morton, 62637 Randy Figg, 62638 Sharon Banicki, 63583 SJC GOP 2024 CFA-4, 62639 Tami Springer, 62640 Tom McCormick, 62641 Tony Hazen

**Tab 8: May 2024 Primary (22 listed)**

61046 Andy Rutten (R), 61047 Anthony (Tony) Hazen (R), 61048 Candace Brown (R), 61049 Carolyn Topolski (D), 61050 Charlotte Wolf (D), 61051 Derek Dieter (R), 61052 Jason Piontek (D), 61031 Jenn Shabazz (D), 61032 Kent D Hizer (R), 61033 Kris Verash (R), 61034 Maggie DeMaegd (R), 61035 Mark Catanzarite (D), 61036 Mark Root (R), 61037 Mary Beth Wisniewski (D), 61038 Michael Rose (R), 61039 Mike McGann (D), 61040 Patricia Jordan (R), 61041 Rafael Morton (D), 61042 Randy Figg (R), 61043 Sharon Banicki (D), 61044 Tami Springer (D), 61045 Tom McCormick (R)

**Tab 10: 2024 School Board (25 listed)**

63520 Christian L Mattix (John Glenn-Liberty), 63442 Jared Egger (JG - Polk), 63444 Ryan Knowlton (JG-Johnson), 63268 Angela Layman (MI), 63509 Mellissa Kay Johnson (MI), 63463 Jill Smith (New Prarie Dist 1- At Large), 64377 Mike Yacullo, 63362 Gary Fox (PHM-Harris), 63440 Ryan McCullough (PHM-Penn), 63512 Art Klinger (PHM-Harris), 63513 Ben Dallas (MAGA) (PHM-Penn), 63511 Doug Chaffee (PHM-Penn), 63514 James Garrett (PHM-Penn), 63510 Katie Inabnit Bell (PHM-Penn), 63266 Annette Malone (SB), 63267 Jeanette McCullough (SB), 63516 Carlos Leyva (SB), 63524 Catrina Baker (SB), 63521 Gabrel (Gabe) A Kempf (SB), 63519 George L. Jones (SB), 63522 Kyla Henderson (SB), 63525 Lynn King (SB), 63517 Marcus Ellison (SB), 63523 Stephanie Ball (SB), 63518 William (Bill) Sniadecki (SB)

**Tab 11: Late Ballot Vacancies (3 listed)**

63662 Amanda Mitchell, 63664 Ed Fisher, 63663 Joseph G. Carbone

**Tab 12: 2024 Pre-Election CFA-4 (34 listed)**

64481 Amanda Mitchell, 64482 Andy Rutten, 64483 Anthony (Tony) Hazen, 64484 Candace Brown, 64485 Democratic Central Committee, 64452 Derek Deiter, 64453 Douglas Chaffee, 64454 Ed Fisher, 64455 Gary Fox, 64456 Jason Cichowicz, 64457 Jason Piontek, 64458 Jenn Shabazz, 64459 Jennifer Shabazz, 64460 Joseph Carbone, 64461 Katie Inabnit Bell, 64462 Loris Zappia, 64463 Lynn King, 64464 Maria Fleming, 64465 Mark Catanzarite, 64466 Mary Beth Wisniewski, 64467 Michael Rose, 64468 Mike McGann, 64469 Patricia Jordan, 64470 Rafael Morton, 64471 Randy Figg, 64472 Ryan McCullough, 64473 Save Our Schools, 64474 Sharon Banicki, 64475 SJC Young Republicans, 64476 St Joe County Young Republicans, 64477 St. Joseph County GOP, 64478 Tami Springer, 64479 Tom McCormick, 64480 William Sniadecki

**Tab 13: 2024 Annual CFA-4 (121 listed)**

66169 Alan Grzeskowiak, 65620 Amanda Mitchell, 65621 Amy Drake Council B, 65622 Amy Drake Exploratory, 65623 Amy Rolfes, 66025 Andy Kostielney, 65624 Andy Rutten, 65731 Anthony "Tony" Hazen, 65964 Anthony "Tony" Underly, 66168 Ashley Portolese-Miller, 65625 Bianca Tirado, 65626 Candace Brown, 65627 Canneth Lee, 65628 Carl Baxmeyer, 66219 Carolyn Topolski, 66170 Charlotte Wolfe, 65629 Cherie De Freese, 66200 Chris Riley, 65630 Dale "Woody" Emmons, 65631 Dan Schaetzle, 65632 Dave Schmidt, 65684 Dave Wood, 66570 Deb Fleming, 65633 Debbie Ladyga-Block, 65634 Derek Dieter, 66197 Desmont Upchurch, 65635 Diana Hess, 65685 Doris J. Portolese, 65636 Doug Chaffee, 66181 Ed Fisher, 66082 Eli Wax, 66196 Elizabeth J. McCombs, 66180 Elizabeth Parvu, 65637 Gary Fox, 66185 Gene Reese, 66448 George Lee Jones, 65992 Gloria Niedbalski, 65678 Gregg Hixenbaugh, 66172 Heather O'Connell, 65638 James Mueller, 66186 James Turnwald, 66171 Jason Banicki, 65639 Jason Critchlow, 68146 Jason Allen Cichowicz, 66173 Jason Kring, 65640 Jason Mazurkiewicz "Maz", 65641 Jenn Shabazz, 65642 Joe Thomas, 65741 John Broden, 65643 (untitled), 65644 John Maciejczyk, 66174 John Murphy, 65645 Joseph G. Carbone, 66175 Josh Gobel, 66568 Julie Brown, 65646 Karen White, 66077 Kareemah Fowler, 65647 Kate Lee, 65648 Kate Voelker, 65649 Katie Inabnit Bell, 68257 Katie Inabit Bell, 65650 Kenneth E. Lindsay, 65651 Kenneth P. Cotter, 66179 Kent Hizer, 66201 Kevin Conery, 66176 Kris Verash, 65652 Lacy Hahn, 66184 LaQuita Hughes, 65653 Lorris Patrick Zappia, 65978 Lou Ann Hazen, 65654 Mark Catanzarite, 65707 Mark Root, 65655 Mary Beth Wisniewski, 66177 Mary Ellen McNeil, 65656 Matt Carroll, 65657 Matt Chaffee, 65658 Matt Mammolent, 68201 Michael Compton, 66387 Michael A. Dvorak, 65993 Michael Rose, 66027 Mike Bellovich, 65659 Mike Castellon, 65660 Mike Grzegorek, 65732 Mike McGann, 65661 Oliver Davis -Commissioner Dist.2, 65662 Oliver Davis -Council Dist. At Large, 65663 Ophelia Gooden-Rodgers, 65664 Our P-H-M, 65665 Patricia Jordan, 66026 Patrick Reighter, 65666 Rachel Tomas Morgan, 65667 Rafael Morton, 65668 Randall Figg, 66218 Rhonda Richards, 66060 Richard Pfeil, 65680 Robert Kovach, 65669 Robert "Bobby K" Kruszynski, 66225 Roderick "Rod" Goodchild, 65681 Ron Banicki, 65670 Rosemary Mandrici, 65682 Rudy Monterrosa, 65671 Ryan McCullough, 66178 Sandra Ort, 65672 Save our Schools "SOS", 65673 Sean O'Brien, 65683 Sharon Banicki, 65674 Sharon McBride, 65614 Sheila Niezgodski, 65615 Sherry Bolden-Simpson, 66028 Sonia Perez, 66217 SJC Democratic Central Committee, 66220 SJC Young Republicans, 66167 St. Joseph County GOP, 65706 Tami Springer, 66227 Ted Booker, 66066 Tim Swager, 65616 Tom McCormick, 65617 Toni Violi, 65618 Troy Warner, 65619 William "Bill" Redman, 66195 William "Bill" Sniadecki

**Tab 14: 2024 Delinquent Annual CFA-4 (1 listed)**

66024 DELINQUENT CFA 4 Annual Report-

**Tab 15: 2023 Annual CFA-4 (80 listed)**

60890 Alan Grezeskowiak, 60891 Amy Drake, 60892 Amy Rolfes, 60818 Andy Kostielney, 60819 Anthony (Tony) Hazen, 60820 Anthony V Underly, 60821 Ashley Portolese-Miller, 60822 Bianca Tirado, 60823 Bill Redman, 60824 Bryan Tanner, 60825 Canneth Lee, 60826 Carl Baxmeyer, 60827 Cherie DeFreese, 60828 Dale (Woody) Emmons, 60829 Dan Chamberlin, 60830 Dan Schaetzle, 60831 Dave Schmidt, 60832 Dave Wood, 60833 Debbie Ladyga-Block, 60834 Derek Dieter, 60835 Diana Hess, 60836 Doris J. Portolese, 60837 Eli Wax, 60838 Elizabeth McCombs, 60839 Gloria Niedbalski, 60840 Gregg Hixenbaugh, 60841 IRP 2023 CFA, 60842 James Turnwald, 60843 Jason Banicki, 60844 Jason Cichowicz, 60845 Jason Critchlow, 60846 Jason Mazuriewicz, 60847 Jason Piontek, 60848 Jeff Fansler, 60849 Joe Thomas, 60850 John Broden, 60851 John Murphy, 60852 Josh Gobel, 60853 Joyce Joiner, 60854 Karol Jackson, 60855 Kate Lee, 60856 Kate Voelker, 60857 Kenneth Cotter, 60858 Lacy Hahn, 60859 Lou Ann Hazen, 60860 Maggie Demaegd, 60861 Mark Catanzarite, 60862 Mark Root, 60863 Mary Beth Wisniewski, 60864 Matt Carroll, 61000 Matt Chaffee, 60865 Matt Mammolent, 68199 Michael Compton 2023, 60866 Michael McGann, 60867 Mike Bellovich, 60868 Mike Castellon, 60869 Mike Grzegorek, 61142 Mishawaka Republican City Committee, 60870 Mueller 2023 Annual, 60871 Mueller 2023 Signed Summary, 60872 Oliver Davis, 60873 Ophelia Gooden-Rodgers, 60874 Rachel Tomas Morgan, 60875 Rafael Morton, 60876 Randall Figg, 60877 Robert (Bobby K) Kriuszynski, 60878 Robert Kovach, 60879 Ron Banicki, 60880 Rosemary Mandrici, 60881 Rudy Monterrosa, 60882 Sharon McBride, 60883 Sheila Niezgodski, 61143 Shelli Treely, 60884 Sherry Bolden-Simpson, 60885 SJC Democratic Central Committee, 61117 St. Joseph County Republican Party, 60886 Theresa (Terri) Buckmaster, 60887 Tom McCormick, 60888 Toni Violi, 60889 Troy Warner
