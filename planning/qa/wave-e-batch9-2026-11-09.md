# Wave E, batch 9: sticky in-page nav, anchor landing, phone masthead, 2026-11-09

Spec: review pattern P9 and the batch 9 row. Nothing committed. Final checks: `build.py --check` PASSED (113 pages); unittest 308 OK (10 new, `tools/tests/test_wave_e_onpage.py`); `check_gov.py` 0 errors.

## 1. Sticky "On this page"

Measured every built page at 1280 px (iframe, scrollHeight/800, folds closed, JS on), 113 pages. Over about 9.5 screens and with a table of contents of 3+ links (19 pages, `civic/shell.py ONPAGE_PAGES`, marked `data-onpage="1"` on `#site`):

money/campaigns/county 32.9, campaigns/all-filings 23.7, history 21.7, campaigns/how-it-works 20.2, money/budgets 17.8, county 15.1, about 11.9, your-tax-bill 11.9, elections/how-it-works 11.5, places/mishawaka 11.5, community/people 11.3, calendar 11.2, places/south-bend 11.2, community/income-and-work 11.1, campaigns/mishawaka 10.4, campaigns/south-bend 10.3, elections/margins 9.9, elections/results 9.6, campaigns/sbcsc 9.5.

Left out: teach 9.1, campaigns/phm 9.4, state/index 8.0, every other page under 9, and money/campaigns/state-legislature (8.4, no toc). The threshold is a data list, so adding one is a one-line change.

Behavior (`static/js/onpage.js`, `static/css/onpage.css`):
- **Built from the page's own `nav.toc`.** One labelled select ("On this page", one option per toc link, the section in view is selected) plus a "Back to top" link, in a bar fixed under the sticky nav. It appears once the toc has scrolled out of sight. One select and one link: no focus trap, no key handling.
- **Choosing a section clicks the toc's own link**, so folds.js opens a fold that holds the target and the browser jumps natively.
- **Phone (760 px and under):** the label becomes visually hidden (still the select's label) and a "Back to top" link follows each h2 (hidden on wide screens, so not tabbable there). Back to top scrolls to 0, drops the stale hash and focuses the h1.
- **Does not cover anchors.** `html.has-onpage` sets `scroll-padding-top: nav height + 48 + 14 px`. JS sets `--nav-h` from the real nav (47, 56 or 53 px by look). Anchors land at 109 to 111 px, below the bar (bottom at 95 to 97). This also applies to Tab focus and the browser's own jumps.
- **Looks.** Ballot, Line map (rounded select, 1 px rule) and Wayfinding (surface-2 bar, 4 px rule) with existing tokens only; viewed in light and dark at 400 and 1280 px. Print hides it.
- **JS off:** the bar and the Back-to-top links are not in the shipped HTML (a test checks it); the plain, non-sticky toc stays.
- **Keyboard.** The bar sits right after the toc in the DOM. Tab and Shift+Tab (real key presses in Chrome) after a `#row-officers` landing put focus below the bar. The select changes the section on change, as native selects do.

## 2. Anchor landing after fonts

One site-wide script, `static/js/anchor_landing.js`. `margins.js` is deleted (its only job was this; it was untracked), and the README row is replaced.
- Runs on load, again when `document.fonts.ready` resolves and on `loadingdone`, and for 3 s on body resize.
- Compares the target's top with `scroll-padding-top + the target's scroll-margin-top` and calls `scrollIntoView({block:"start", behavior:"instant"})` only if more than 3 px off (the site sets `scroll-behavior: smooth`, hence "instant").
- Does nothing if the id is absent, the target is hidden in a closed fold, the navigation was reload or back/forward, or the reader pressed a key, touched, clicked, or used the wheel.
- **moved.js is unchanged.** It forwards a missing id by `location.replace`; the destination page then lands it with this script. folds.js opens folds at start-up, before this script's load handler, and the script skips a hidden target. No integration code was needed.
- **Tested:** fresh loads of 2 ids on each of 24 long and mid pages at 1280 and 400 (96 loads): every target at the expected offset (111 or 64), except 3 `#sources` targets on short-end pages (the target cannot scroll that far; they are fully visible). Forwarded: `elections/index.html#vacancies`, `#general`, `data/index.html#ds-results-preview`, `about/index.html#src-GOV-001` all land at 111 or 64 on the new page. Also `elections/margins#area-clay-township`, `officeholders#gov-south-bend`, `calendar#year-2027`, `your-governments#find`, `#paths`, and `#src-GOV-003` inside a closed Sources fold. The test iframe reuses warm fonts, so the original 214 px case itself was reproduced only logically; `elections/how-it-works#vacancies` now lands at 111 (before, 214 with no bar at a 64 target).

## 3. Phone masthead (`static/css/masthead.css`, 480 px and under)

Layout: title; date, version and "Not your county?" on one line; search; Look switcher and Theme side by side. Nothing removed: the "Look" word is visually hidden (the group keeps its accessible name), all buttons keep 44 px height, `.stamp` becomes `display: contents`.

| Width, calendar page | Masthead before | Masthead after | Masthead + nav before | after |
|---|---|---|---|---|
| 400, Ballot | 256 | 184 | 303 | 231 |
| 400, Line map | 256 | 184 | 313 | 241 |
| 400, Wayfinding | 256 to 264 | 184 | 309 to 317 | 237 |
| 360 | not measured | 205 to 213 (Theme wraps to its own row) | | 252 to 266 |

No horizontal scroll in 3 looks x light/dark at 400 and 360, no control outside the viewport, no button under 44 px.

## Not done or open
- Real browser could not be resized: wide and phone widths came from same-origin iframes (as earlier waves). JS-off was verified from the shipped HTML (and a unit test), not by turning JS off in the browser.
- Smooth scroll means a select jump takes a moment on a 20-screen page; that is the site's existing setting.
- `.mn-unit` and `.sp-block` carry their own `scroll-margin-top: 72px`, which adds to the new padding (they land at 136 to 184 px). Left alone (not my files).
- Question for Nick: the threshold (9.5 screens) is looser than the review's "about 12"; it adds about, tax bill, how-it-works, 2 places pages, 3 more. Say so if you want only the 6 pages over 12.

## Changed files (all uncommitted)
- `tools/site/civic/shell.py` (ONPAGE_PAGES, `data-onpage`)
- `tools/site/static/js/anchor_landing.js` (new), `tools/site/static/js/onpage.js` (new), `tools/site/static/js/margins.js` (deleted)
- `tools/site/static/css/onpage.css` (new), `tools/site/static/css/masthead.css` (new)
- `tools/site/README.md` (file table)
- `tools/tests/test_wave_e_onpage.py` (new)
- Untouched: nav.js, moved.js, folds.js, here.js, pick_one.js, tablefilter.js, nav.css, data files.
