# Wave A, batch 0: layout bugs B1-B3 (2026-11-09)

## Changes
- **B1** `tools/site/static/css/places.css`, `tools/site/pages/places.py`: place-page coverage chips renamed `.cov*` -> `.pcov*` (`.pcov`, `.pcov-covered/-partial/-none`, `.pcov-strip`, `.pcov-name`). Campaigns keeps `.cov*`. No other generator or JS used the old names.
  - how-it-works: the grid renders as a grid (`td.cov` is `table-cell`). Table height 25,400 px -> 8,145 px. Page 16,218 px (about 20 screens at 800 px; the review's "about 10" was optimistic: the table is 97 office rows at about 62-84 px each, the rest of the page is about 8,000 px). Further shrinking would mean tighter cell padding or a narrower Office column; not done (out of scope).
  - Place pages (centre-township checked): chips unchanged (mono caps, solid/dashed borders).
- **B1 guard** `tools/site/check.py` (new check 7, `css_duplicate_bare_classes`, `CSS_DUP_ALLOWLIST`), test `tools/tests/test_css_duplicates.py` (5 tests). A bare class selector (selector exactly `.name`, alone or in a comma list, also inside @media) defined in 2+ `static/css/*.css` files fails the build check. Comments ignored.
  - Existing duplicates found among area files: **none** after the rename (allowlist is empty). Base `static/style.css` is not part of the rule; it overlaps area files on `.masthead` (search.css adds z-index) and `.next-strip`; those are intentional extensions, not reported.
- **B2** `tools/site/static/css/here.css`: `.here-tag` now uses its own pair `--here-tag-bg` / `--here-tag-ink` (defaults `--ink` / `--surface`); inside `.next-strip, .elx-next-card, .hl-callout` the pair is `--hl-ink` / `--hl`. Contrast measured on the live tag, 3 looks x light/dark: ballot 11.6 / 10.1, line 16.1 / 14.4, wayfinding 11.7 / 11.7. Visual check in dark Ballot on elections/calendar/ (saved place: City of South Bend, saved earlier through the site's picker; localStorage already held it).
- **B3** `tools/site/static/css/party.css`: `.layer-seats > .body-breakdowns, > .party-asof, > .layer-note` get `flex: 0 0 100%`, so the party summary and notes sit on their own line under the glyphs. Checked your-governments/ at 400 px (iframe, since the window resize did not change the viewport): county bullets under the glyphs, SBCSC/library layers: no citation overflows its layer head, no horizontal scroll (scrollWidth 385). The citation overlap was not reproduced separately after the fix. index.html uses the same `layer-seats` markup (pages/landing.py); not opened separately.

## Checks
- `build.py --edition st-joseph --check`: PASSED
- `unittest discover -s tools/tests`: 158 tests OK
- `tools/check_gov.py`: errors=0 (23 existing warnings)

## Not done / notes
- Browser matrix was sampled, not exhaustive: B2 all 6 combos by contrast measurement (one visual); B1 and B3 in the default look, dark theme only.
- Nothing committed. B4, B5 untouched.
