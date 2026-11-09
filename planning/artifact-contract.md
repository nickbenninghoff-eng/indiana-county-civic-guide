# Hosting contract: claude.ai Artifact (multi-file), summarized for builders

The site publishes first as a private claude.ai Artifact. These rules come from the Artifact tool and are enforced by its viewer and CSP. Every generated page must follow them.

## Files
- `index.html` = the page. At publish time it's wrapped in `<!doctype html><head>…</head><body>`, so write it with NO doctype/html/head/body tags: start with `<title>`, `<meta name="claude:viewport-fit-sides" content="cover">`, `<link>`/`<style>`, then content.
- Every OTHER `.html` file is served as-is, so it must be a complete document: `<!doctype html>`, `<html lang="en">`, `<head>` with `<meta charset="utf-8">`, `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`, `<meta name="claude:viewport-fit-sides" content="cover">`, `<title>`, base styles.
- Shared CSS/JS/images/fonts are published as files and referenced by RELATIVE paths with no leading slash. Links between pages are relative too (e.g. `../county/index.html`).
- Total page ≤ 16 MB, each file ≤ 16 MB.

## CSP / external resources
- Scripts only from cdnjs.cloudflare.com (preferred), cdn.jsdelivr.net/npm, unpkg.com, cdn.tailwindcss.com or code.jquery.com, pinned to exact versions. Prefer NO external JS: write plain JS in `assets/app.js`.
- Stylesheets only from fonts.googleapis.com (fonts from fonts.gstatic.com) or our own published files. Give every face a fallback stack.
- No other hosts: images, fetch and iframes elsewhere are blocked. Portraits and maps must be our own published files or inline SVG.
- Links to other websites are fine (they open in a new tab). mailto:/tel: are unreliable, so show addresses and numbers as selectable text.

## Viewer limits
- No downloads (`<a download>` and blob links are inert). The /data page shows tables plus a "Copy CSV" button (navigator.clipboard.writeText inside the click handler, with a select-the-text fallback).
- `window.print()` does nothing, so no Print buttons. Still ship a print stylesheet for the later public host.
- No alert/confirm/prompt dialogs.
- Routing: only plain `#name` hashes pass through (ASCII letters, digits, hyphens). No `#/path`, no `?query`. Never use the reserved names settings, sidebar, customize, upgrade, downloads or comment-*.
- localStorage only for per-viewer conveniences, wrapped in try/catch.

## Required page qualities
- Theme-aware: every color is a token on `:root` (light), redefined under `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {…; color-scheme: dark} }` AND `:root[data-theme="dark"] {…; color-scheme: dark}`. `body` sets an explicit background from a token. No literal colors in components.
- Responsive to ~400 px with no horizontal page scroll. The side gutter is `padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px))` on one outer wrapper, using `padding-block` for vertical padding. Only tables, diagrams and code scroll sideways, each in its own `overflow-x: auto` wrapper. Flex/grid children holding text get `min-width: 0`.
- A sticky header uses `top: env(safe-area-inset-top, 0px)`, with `body::before` painting the inset band.
- Complete at rest: no content hidden behind scroll-triggered animation. Respect prefers-reduced-motion. Visible keyboard focus. Every form control has a stable id.
- `<title>`: a short name for the page (e.g. "County Government · St. Joseph County").
- Avoid generic AI looks: no cream+terracotta serif, no purple gradients, no emoji section markers, no rounded-lg-everywhere card soup.
