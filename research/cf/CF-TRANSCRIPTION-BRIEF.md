# Campaign finance transcription brief (Phase A: cell-level OCR, no screenshots)

Read `C:\Users\nickb\local-gov-guide\research\browser\BROWSER-AGENT-BRIEF.md` first for tab rules and PDF loading. This brief overrides it where they differ.

## Hard rules (lessons from the last run)
- NEVER set document.title, never start local servers, never POST data anywhere, never download files. Get data out ONLY through javascript_tool return values (keep each return under ~6,000 chars) and then write files with the Write/Edit tools.
- No screenshots in Phase A. Several agents share one Chrome window. Rows you can't validate go to the failures list for Phase B, which a single agent reads visually.
- Your own tab only. Close it when done.

## The form (Indiana CFA-4 summary sheet, usually page 1, sometimes page 2)
Two numeric columns: **A = "This Period"**, **B = "Year to Date"**.
Lines: 13 cash at start of period (A only) | 14 cash Jan 1 (B only) | 15a itemized receipts | 15b unitemized | 15c = 15a+15b | 16 = 13+15c (A), 14+15c (B) | 17a itemized expenditures | 17b unitemized | 17c = 17a+17b | 18 = 16-17c (cash at close) | 19 debts owed by committee | 20 debts owed to committee.
Header fields: committee name, candidate name, party, office sought, report type checkboxes (pre-primary / pre-election / annual / other), period from/through, amendment yes/no.

## Method: OCR each cell, not the whole page
1. Render the summary page at scale 3. Run normal tesseract on the full page and use `result.data.words` (with `bbox`) to locate:
   - the row label words ("13.", "14.", "15a.", "15b.", "15c.", "16.", "17a.", "17b.", "17c.", "18.", "19.", "20."), which give row y-bands
   - the column headers "This Period" and "Year to Date" (or "COLUMN A"/"COLUMN B"), which give column x-bands.
   Pages are often photographed at a slight skew, so take bands from the words themselves, not fixed fractions.
2. For each (row, column) cell: crop the canvas, upscale 2x, convert to grayscale, threshold (binarize), then OCR with a second worker configured `await w2.setParameters({tessedit_char_whitelist:'0123456789.,$', tessedit_pageseg_mode:'7'})`. Parse as dollars; a final ".dd" is cents, so a comma read as a period mid-number is a separator.
3. Header text fields come from the full-page OCR (names may need light cleanup; mark them `?` if unclear).
4. **Validate with the form's own arithmetic, in both columns:** 15c=15a+15b; 16=13+15c (A) / 14+15c (B); 17c=17a+17b; 18=16-17c; also 18A should equal 18B. Count how many identities pass.
   - All applicable identities pass → `status=verified`.
   - You can fix exactly one bad cell so that every identity passes → fix it, `status=derived`, and name the derived cell in notes.
   - Otherwise → `status=failed`, and add the doc to the failures list.
5. If page 1 isn't the summary sheet, try page 2. If neither is (e.g. it's a Schedule or a cover letter), record `status=not-summary`.
6. CFA-11, CAN-*, ballot-vacancy and precinct/delegate documents: don't transcribe. Just list them in the failures file under "Phase B: CFA-11" (CFA-11 only) or skip them (the others).

Process committees' most comprehensive report first (2023 Annual for 2023 city races; the latest pre-election/annual report for each 2024/2026 committee), then everything else in your slice.

## Output (append as you go, so progress survives if you're stopped)
- CSV `C:\Users\nickb\local-gov-guide\research\cf\cf-<slice>.csv` with this header:
  `doc_id,tab,committee,candidate,office,party,report_type,period_from,period_to,amended,l13A,l14B,l15aA,l15bA,l15cA,l16A,l17aA,l17bA,l17cA,l18A,l15aB,l15bB,l15cB,l16B,l17aB,l17bB,l17cB,l18B,l19,status,checks_passed,notes`
  Use plain numbers without $ or commas. Quote fields that contain commas.
- `C:\Users\nickb\local-gov-guide\research\cf\cf-<slice>-failures.md`: failed docs (id, title, which cells were unclear) and the CFA-11 list.
- Reuse the ArrayBuffer/doc cache and both OCR workers across documents. Don't recreate them per page.

## Run it as an in-page background loop (essential for context size)
Don't process documents one tool call at a time. Instead:
1. Navigate your tab to https://www.sjcindiana.gov/2330/Candidate-Filings and collect your slice's document IDs from the tab panels via javascript_tool (match by panel heading). Save the ID list to your failures/notes file first.
2. Define your pipeline functions on `window` (loadDoc, renderPage, locateBands, ocrCell, validate, toCsvRow).
3. Test them on 2–3 documents and look at the output carefully. Tune band detection until known-good documents verify. Known-good reference: Mueller 2023 Annual summary, ID 60871, should give l14B=262508.60, l15cB=393342.90, l17cB=610625.36, l18B=45226.14, l13A=98086.12, l15cA=32633.18, l17cA=85493.16, l18A=45226.14.
4. Start a non-awaited loop: `window._rows=[]; window._done=0; (async()=>{for(const id of ids){try{window._rows.push(await processDoc(id))}catch(e){window._rows.push(id+',ERROR,'+e.message)} window._done++}})();`
5. Poll every ~30–60 seconds (`await new Promise(r=>setTimeout(r,45000)); ({done:_done,total:ids.length,newRows:_rows.splice(0)})`) and append the new rows to your CSV with Bash (`cat >> file <<'EOF'`) or Edit.
6. Do NOT navigate the tab while the loop runs, because navigating kills it. If the loop dies, restart from the first unprocessed ID.
