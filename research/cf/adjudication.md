# Campaign finance double-entry adjudication

Adjudicated 2026-11-07 against the page images (`sources/cf/img/<batch>/<id>_p1_nums.jpg`, zoomed where needed).
The decisions below are encoded in `tools/build_cf_local.py`, which writes the adjudicated line-level readings to
`research/cf/cf_lines_final.csv`. `tools/validate_cf_local.py` re-checks them.

## The status rule (applied to every summary sheet, not only the sample)

Identities checked (CFA-4 summary sheet; A = this period, B = year to date):
15c = 15a + 15b; 17c = 17a + 17b; 16A = 13 + 15cA; 16B = 14 + 15cB; 18 = 16 - 17c (both columns); 18A = 18B.
**Same-span identity:** when the reporting period starts on Jan 1 of its own year, columns A and B cover the
same span, so 13A = 14B, 15cA = 15cB and 17cA = 17cB must also hold. This follows from the form's definitions,
but it is not listed in CF-VISUAL-BRIEF.md, so it is flagged for the owner.

* **filer-inconsistent**: the numbers as written violate at least one identity. This takes precedence over everything else.
* **derived**: no identity is violated, and at least one cell was blank, illegible (overwritten, smudged, stamp-covered) or
  clipped on the form, and the identities fix it at a **non-zero** value. The derived cells are named in `notes`.
* **verified**: every applicable identity holds as written and nothing had to be filled in.
* Blank handling: a blank cell that the identities fix at **zero** is read as "none" (nil), not as derived.
  Examples are a blank 15b where 15a = 15c, or a blank line 16 on an all-zero report. An identity is applied only when
  its result cell and at least one input are present. A column the filer left entirely blank (often all of column B
  except line 14) is "not completed": its identities are not applicable and nothing is derived in it. A blank cell is
  never filled from an input that itself fails an identity (so 65615's blank 18B stays blank).
* A digit-shape ambiguity that the reader resolved and that reads cleanly (e.g. a 1 written like a 7, "confirmed by
  arithmetic") stays a reading (verified). Digits that are physically overwritten, smudged, clipped or stamp-covered count as derived.

## 1. Cell conflicts (31 cells in 17 docs)

| doc | cell | first | second | final | why (image) |
|---|---|---|---|---|---|
| 61143 | l17aB | 5654.60 | 5634.60 | **5654.60** | Zoomed: third digit is the same 5 as in 17cB 5654.60; 17b is a dash. (Doc stays filer-inconsistent: 18A 2774.62 vs 18B 2774.60.) |
| 65634 | l19 | 1315.62 | 1315.67 | **1315.67** | Last digit partly cut at the cell edge; the stroke is a 7 (no base stroke like this filer's 2s). Low confidence; may be a misplaced cash figure. |
| 65634 | l15bB | blank | 0 | **0** | A slashed zero is written under 15aB. |
| 68257 | l18B | 336 | 336.22 | **336** (as written) | Written "336" with no cents. 5604.85 - 5268.63 = 336.22, and 18A = 352.22, so the form is filer-inconsistent. |
| 69855 | l15aA | 476038.34 | 476038.38 | **476038.38** (as written) | Zoomed: the last digit is an 8 (possibly 0 written over), not a 4. 15a + 15b = 482494.02 vs 15c 482493.98, so filer-inconsistent. |
| 69855 | l17bB | 0 | blank | **0** | "0" is fully visible. The rest of column B is clipped at the right edge, so column B is treated as not transcribed and YTD is left blank. |
| 60862 | l20 | 0 | blank | **0** | A handwritten 0 sits in line 20, partly under the RECEIVED stamp. |
| 65615 | l18B | 12.27 | blank | **blank** | 18B is empty on the form. The first reader had copied 18A. |
| 65627 | l17aA | blank | 880.57 | **880.57** | Faint but legible. The doc stays unreadable (most cells washed out). |
| 70545 | l15aA, l15bA, l17aA, l17bA, l15aB, l15bB, l17aB, l17bB (8 cells) | 0 | blank | **blank** | The cells read "N/A", not zero. Status unchanged (verified). |
| 73119 | l16A | blank | 3902.69 | **3902.69, derived** | The handwritten 16A entry is scribbled out, with a typed template "0.00" beside it. 13A 3902.69 + 15c 0 pins it. 14B is also blank (derived 3902.69). |
| 72879 | l16A, l16B | 678.59 | blank | **678.59, derived** | Line 16 is blank in both columns on the form. |
| 72885 | l15cA, l15cB | 1361.01 / 1649.73 | blank | **derived** | The 15c subtotal row is blank in both columns. |
| 72776 | l16B | 3025.00 | blank | **3025.00, derived** | 16B is blank on the form. |
| 64454 | l16A, l16B, l18B | 10151.73 / 10151.73 / 2030.80 | blank | **derived** | All three cells are blank on the form. |
| 66200 | l14B | 1135.00 | blank | **1135.00, derived** | 14B is blank; 16B = 1135.00 and 15cB = 0. |
| 68320 | l14B | 1135.00 | blank | **1135.00, derived** | Same pattern as 66200. |
| 68441 | l14B | 3902.69 | blank | **3902.69, derived** | Same pattern. |
| 71864 | l16A, l16B | 0 | blank | **blank (nil)** | Line 16 is blank. The identities give 0, so it is read as none and the doc stays **verified**. |

In every blank-vs-value case both readers agreed the cell is blank on the form. They differed only on whether to fill it in.

## 2. Status disagreements (28 docs)

| doc | first | second | final | why |
|---|---|---|---|---|
| 73119 | filer-inconsistent | derived | derived | Illegible 16A and blank 14B fixed by identities; nothing violated |
| 72879 | derived | verified | derived | line 16 blank, non-zero pin |
| 72885 | derived | verified | derived | 15c blank, non-zero pin |
| 72776 | derived | verified | derived | 16B blank |
| 60847 | filer-inconsistent | verified | derived | Column A holds; 15cA blank (= 15a 6100). Column B has only 14B, so it is not completed and not applicable |
| 64454 | derived | verified | derived | 16A/16B/18B blank |
| 66170 | filer-inconsistent | verified | verified | Column A holds; column B only line 14 (not completed) |
| 66200 | derived | verified | derived | 14B blank |
| 65631 | filer-inconsistent | verified | verified | Column A holds; column B entirely blank |
| 65636 | derived | verified | derived | 15aB last digit clipped at right edge (image) |
| 65649 | filer-inconsistent | derived | filer-inconsistent | 18A 2152.22 vs 18B 2136.22 as written (image); 13A reads 2235 |
| 68257 | filer-inconsistent | derived | filer-inconsistent | 18B written 336; 18A differs from 18B |
| 65652 | derived | filer-inconsistent | filer-inconsistent | Same-span: period 1/1-12/31/24 but 13A 332.23 vs 14B 284.35. 17aA is a 4 drawn as "L1" (47.88) and 17cA is blank |
| 65619 | derived | verified | derived | 16A/16B cents digits overwritten (image) |
| 71864 | derived | verified | verified | blank line 16 pins to 0 (nil) |
| 70553 | filer-inconsistent | verified | filer-inconsistent | 18A -2178.17 vs 18B 14266.38 (image) |
| 62637 | derived | verified | derived | Clerk stamp covers digits of 17aA/17bA (image) |
| 62639 | filer-inconsistent | verified | filer-inconsistent | Line 18 written 0.00 while 16 = 200.00 and 17c = 0.00 (image) |
| 68320 | derived | verified | derived | 14B blank |
| 68284 | filer-inconsistent | verified | filer-inconsistent | Same-span: full-year period but 13A differs from 14B, and 15c and 17c differ between columns |
| 67923 | filer-inconsistent | verified | derived | Lines 16 and 18 blank in both columns; pinned at 256.18 / 56.18 |
| 68222 | filer-inconsistent | verified | filer-inconsistent | Same-span violated (13A 5929.28 vs 14B 3203.03; 15c and 17c differ) |
| 68441 | derived | verified | derived | 14B blank |
| 68263 | filer-inconsistent | verified | filer-inconsistent | Same-span violated (13A 1345.80 vs 14B 3345.80; 15cA 2000 vs 15cB 0) |
| 69855 | derived | filer-inconsistent | filer-inconsistent | 15aA reads 476038.38 (image); 15a + 15b differs from 15c |
| 68239 | derived | verified | derived | 17c last digit overwritten (image) |
| 65637 | verified | derived | derived | 18B clipped at right edge, "2,800.1_" (image) |
| 68228 | verified | derived | derived | Overwritten 4/9 digits in 16 and 17a/17c (image) |

Final tally of the 28: derived 16, filer-inconsistent 9, verified 3.

## 3. The same rule applied outside the disputed set

Applying the rule uniformly changed 31 more statuses (29 single-read docs and 2 where both readers agreed). These are
mechanical consequences of the rule, mostly blank subtotal or total lines that are pinned at a non-zero value. Two
are worth noting. **64461** was marked verified, but its typed 18 (2,235.00) differs from 16 - 17c (2,219.00); this was
re-checked on the image and it is a filer error. **65645 and 68259** were called filer-inconsistent by both readers.
Under the rule they are derived: 65645's blank 15bA is fixed at 350.00 by its written 15cA, and 68259's blank line 18
is fixed at 284.35 by reading its blank expenditure lines as none. Seven single-read docs were moved to derived because
their first-reading notes describe overwritten, stamp-covered or clipped digits (60824, 60845, 60878, 64466, 66218,
65706, 68207). That decision was made from the notes, not from the images.

| doc | double entry | first | final | basis |
|---|---|---|---|---|
|  60824 | single | verified | derived | derived: unspecified overwritten digits |
|  60826 | single | verified | derived | derived: l17cA;l17cB |
|  60841 | single | verified | derived | derived: l16A;l16B |
|  60845 | single | verified | derived | derived: l15bA |
|  60852 | single | verified | derived | derived: l16A;l16B |
|  60858 | single | verified | derived | derived: l17cA |
|  60878 | single | verified | derived | derived: l17cA;l18A |
|  62636 | single | verified | derived | derived: l17cB;l18B |
|  62638 | single | verified | derived | derived: l15cA;l15cB |
|  64461 | single | verified | filer-inconsistent | 18A: written 2235.00, computed 2219.00; 18B: written 2235.00, computed 2219.00 |
|  64466 | single | verified | derived | derived: l15aB |
|  65628 | single | verified | derived | derived: l17cA;l17cB |
|  65635 | single | verified | derived | derived: l15cB |
|  65645 | agreed | filer-inconsistent | derived | derived: l15bA |
|  65672 | single | verified | filer-inconsistent | 18A 522.09 != 18B 526.09 |
|  65681 | single | verified | filer-inconsistent | period starts Jan 1 but 13A 1245.80 != 14B 1345.80; period starts Jan 1 but 15cA 100.00 != 15cB 0.00 |
|  65706 | single | verified | derived | derived: l17cB |
|  66175 | single | verified | derived | derived: l16A;l16B |
|  66218 | single | verified | derived | derived: l13A |
|  66387 | single | verified | derived | derived: l14B |
|  67986 | single | verified | derived | derived: l18B |
|  68082 | single | verified | derived | derived: l15cB |
|  68121 | single | verified | derived | derived: l16A |
|  68207 | single | verified | derived | derived: l15aB |
|  68232 | single | verified | derived | derived: l16A |
|  68237 | single | verified | derived | derived: l15cB;l17cB |
|  68259 | agreed | filer-inconsistent | derived | derived: l18A |
|  68260 | single | verified | derived | derived: l15cA;l15cB;l17cA;l17cB |
|  68264 | single | verified | derived | derived: l16A;l16B |
|  70521 | single | verified | derived | derived: l16A |
|  72791 | single | verified | derived | derived: l17cA;l17cB |

## 4. Spot-check of verified docs outside the sample

10 `verified` docs drawn at random (Python `random.seed(20261107)`) from the single-read set and compared cell by
cell against `_p1_nums.jpg`: 71462, 68152, 68221, 60846, 64471, 72846, 67915, 65678, 65656, 60873.
**10 of 10 matched** on every recorded cell, blank cell and line 19/20 value.

## 5. Other corrections made during adjudication

* **68321** (Eli Wax, 2025 annual) is in the manifest as a `.bin` file. It is actually a PNG and was never rendered,
  so it is missing from the 537 first readings. It was transcribed once from the PNG (typed form; all identities
  hold, so verified; double_entry = single). The manifest therefore holds 538 docs.
* 68161 and 68230: lines 19/20 read "N/A" and are recorded blank.
* Reader annotations embedded in name fields ("(as written)", "[sic]", "[handwriting hard to read]", etc.) were removed
  from committee/candidate/office. They remain in the first-reading notes carried into `cf_local.notes`.
