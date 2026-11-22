"""Page shell: relative links at any depth, masthead, nav, footer, and the two output
forms required by the Artifact host:

* ``index.html`` (the site root) is published as THE page and wrapped in a skeleton by
  the host, so it is written WITHOUT doctype/html/head/body: it starts with <title>.
* every other page is a complete document.
"""
from __future__ import annotations

import posixpath
import re
from pathlib import Path

from . import sitemap
from .components import (Citations, drop_scoped, figure_notes, gaps_section, section, status_badge,  # noqa: F401
                         status_label)
from .data import fmt_date
from .glyph import GLYPH_ASSET, indiana_glyph, indiana_glyph_use, write_glyph_asset  # noqa: F401
from .html import Markup, esc, h, join, json_script

# One css2 request for every look (static/css/looks.css): Ballot = Barlow Condensed + Barlow,
# Line map = Space Grotesk + Inter, Wayfinding = Overpass; IBM Plex Mono for figures and codes in all.
FONTS = ("https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700"
         "&family=Barlow:ital,wght@0,400;0,500;0,600;0,700;1,400"
         "&family=IBM+Plex+Mono:wght@400;500;600"
         "&family=Inter:wght@400;500;600;700"
         "&family=Overpass:wght@400;600;700;800"
         "&family=Space+Grotesk:wght@500;700&display=swap")

LOOKS = (("ballot", "Ballot"), ("line", "Line map"), ("wayfinding", "Wayfinding"))
DEFAULT_LOOK = "ballot"

# Runs in <head> before the stylesheets so the first paint already has the reader's look (and theme).
# Storage access is wrapped: a blocked localStorage just means the default look. ASCII only.
LOOK_BOOT = ('<script>(function(){var d=document.documentElement,l="ballot",t=null;'
             'try{l=window.localStorage.getItem("civic-look")||l;t=window.localStorage.getItem("civic-theme");}catch(e){}'
             'if(l!=="line"&&l!=="wayfinding")l="ballot";d.setAttribute("data-look",l);'
             'if(t==="light"||t==="dark")d.setAttribute("data-theme",t);})();</script>')


# Ownership watermark (Nick, 2026-11-09: "add my name Nick Benninghoff; Phenomogen LLC as a watermark in the code for
# every page"). Source-only: an HTML comment plus author/copyright metas in every page's head, and a /*! */ banner
# at the top of the shared style.css and app.js (the "!" form survives minifiers). The holder and year come from
# edition.json (rights_holder, rights_year).
def rights_notice(cfg: dict) -> str:
    """e.g. 'Copyright 2026 Nick Benninghoff; Phenomogen LLC. Indiana County Civic Guide, St. Joseph County Edition.'"""
    holder = cfg.get("rights_holder") or cfg.get("author", "")
    year = cfg.get("rights_year") or str(cfg.get("data_as_of", ""))[:4]
    text = f"Copyright {year} {holder}. {cfg.get('series', '')}, {cfg.get('edition', '')}."
    # never let the text close or nest a comment, whichever syntax wraps it
    return re.sub(r"-{2,}|\*/|/\*|[<>]", " ", text).strip()


def rights_html(cfg: dict) -> Markup:
    """The page watermark: a comment and the author/copyright metas, for the document head."""
    holder = cfg.get("rights_holder") or cfg.get("author", "")
    return join([Markup(f"<!-- {rights_notice(cfg)} -->"),
                 h("meta", {"name": "author", "content": holder}),
                 h("meta", {"name": "copyright", "content": rights_notice(cfg)})], "\n")


def rights_banner(cfg: dict) -> str:
    """The watermark for the shared CSS and JS bundles."""
    return f"/*! {rights_notice(cfg)} */\n"


def look_switch(ident: str) -> Markup:
    """The Look switcher: three real buttons with aria-pressed (static/js/looks.js wires them).
    Hidden by CSS until the head script has set data-look, so without JS it never shows."""
    label_id = f"look-label-{ident}"
    return h("div", {"class": "look-switch", "role": "group", "aria-labelledby": label_id, "id": f"look-switch-{ident}"},
             h("span", {"class": "look-label", "id": label_id}, "Look"),
             h("span", {"class": "look-opts"},
               [h("button", {"type": "button", "class": "look-btn", "data-look-set": key,
                             "aria-pressed": "true" if key == DEFAULT_LOOK else "false"}, label)
                for key, label in LOOKS]))


def about_looks_section(ed, num: int | None) -> Markup:
    """About page block: what the three looks are and that the content is identical in each."""
    return section(
        "looks", num, "Choose a look",
        h("div", {"class": "about-looks"},
          h("p", None, "The guide comes in three looks. Pick the one that is easiest for you to read. "
                       "Every look shows exactly the same words, numbers, sources, badges and gaps. "
                       "Only the fonts, colors and shapes change."),
          look_switch("about"),
          h("p", {"class": "look-nojs muted"}, "Switching looks needs JavaScript. Without it, the guide shows the Ballot look."),
          h("ul", {"class": "look-list"},
            h("li", None, h("strong", None, "Ballot"), " (the default): black ink on paper, like a printed ballot, "
                          "with square boxes and heavy rules."),
            h("li", None, h("strong", None, "Line map"), ": clean and rounded, like a transit map. On the layer lists, "
                          "each kind of government is a colored line and your place is a stop."),
            h("li", None, h("strong", None, "Wayfinding"), ": big, bold signs, like road signs. Each kind of "
                          "government has its own sign color.")),
          h("p", None, "Party colors are the same in every look and appear only on party data, always with a text label. "
                       "The colors for kinds of government were checked to stay clearly different from the party colors."),
          h("p", None, "Your browser remembers the look on this device. Light or dark mode is a separate setting "
                       "(the Theme button) and works with every look. Printed pages use plain black ink on white.")),
        ed=ed)


# A hand-written hero eyebrow: plain text only (every page module writes one; see Page._main)
# Pages that stay over about 9.5 screens at 1280 px after the Wave A-D splits (measured 2026-11-09, height / 800, folds
# closed). static/js/onpage.js adds the sticky "On this page" bar and a "Back to top" link at each h2 on these pages,
# built from the page's own .toc. Without JavaScript they keep the plain table of contents.
ONPAGE_PAGES = frozenset({
    "money/campaigns/county/index.html", "money/campaigns/all-filings/index.html", "history/index.html",
    "money/campaigns/how-it-works/index.html", "money/budgets/index.html", "county/index.html", "about/index.html",
    "money/your-tax-bill/index.html", "elections/how-it-works/index.html", "places/mishawaka/index.html",
    "community/people/index.html", "elections/calendar/index.html", "places/south-bend/index.html",
    "community/income-and-work/index.html", "money/campaigns/mishawaka/index.html",
    "money/campaigns/south-bend/index.html", "elections/margins/index.html", "elections/results/index.html",
    "money/campaigns/sbcsc/index.html",
    "elections/compare/index.html"})   # phase 6 step 4: the margins page's content, now Compare: Close races
# phase 6 step 3 (2026-11-16): these became small forwarding pages (their content is on governments/<id>/, in tabs)
ONPAGE_PAGES = ONPAGE_PAGES - {"county/index.html", "places/mishawaka/index.html", "places/south-bend/index.html"}
# phase 6 step 4: elections/margins/ is a forwarding page too (its content is elections/compare/, listed above)
ONPAGE_PAGES = ONPAGE_PAGES - {"elections/margins/index.html"}
# phase 6 step 5 (2026-11-18): Compare budgets and the campaign area pages are short now (their detail is in folds or
# on government Money tabs), with no table of contents
ONPAGE_PAGES = ONPAGE_PAGES - {"money/budgets/index.html", "money/campaigns/county/index.html",
                               "money/campaigns/mishawaka/index.html", "money/campaigns/south-bend/index.html",
                               "money/campaigns/sbcsc/index.html"}

_LEGACY_EYEBROW = re.compile(r'<p class="eyebrow mono">[^<]*</p>')


class Site:
    def __init__(self, ed, out_dir: Path):
        self.ed = ed
        self.out = Path(out_dir)
        self.entries = sitemap.entries(ed)
        self.by_path = {e.path: e for e in self.entries}
        self.pages: dict[str, "Page"] = {}
        self._here: dict | None = None
        self.search_index_bytes = 0

    @property
    def here_data(self) -> dict:
        """Place, township and school names for the "You are here" bar (civic/picker.py here_payload)."""
        if self._here is None:
            from .layers import build_layers
            from .picker import here_payload
            self._here = here_payload(self.ed, build_layers(self.ed))
        return self._here

    def page(self, path: str, title: str | None = None, description: str | None = None,
             banners: bool = False, body_class: str = "") -> "Page":
        entry = self.by_path.get(path)
        if entry is None:
            raise KeyError(f"{path} is not in civic/sitemap.py; add an Entry first")
        p = Page(self, path, title or entry.title, description or entry.description,
                 entry=entry, banners=banners, body_class=body_class)
        self.pages[path] = p
        return p

    def write(self) -> list[Path]:
        """Write every page, then the header search index (assets/search-index.json), which is built
        from the rendered pages so it only points at pages and anchors that exist."""
        from .search import write_index
        written = []
        rendered: dict[str, str] = {}
        for path, page in self.pages.items():
            dest = self.out / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            html = page.render()
            rendered[path] = html
            dest.write_text(html, encoding="utf-8", newline="\n")
            written.append(dest)
        self.search_index_bytes = write_index(self, rendered)
        # added 2026-11-18 (maps on every major page): the map navigator's shared shapes, assets/navmap.svg
        # (civic/navmap.py), one cached file every navigator page references instead of inlining geometry
        from .navmap import write_asset
        self.navmap_bytes = write_asset(self)
        self.site_data_bytes = write_site_data(self)
        self.glyph_bytes = write_glyph_asset(self)
        return written

    def site_data(self) -> dict:
        """The data every page's scripts share (2026-11-18, maps-cleanup brief part B item 2: it was inlined as two
        JSON blocks, ~11 KB on each of 3,500 pages): the saved-place data (here.js, your_place.js) and the learning
        paths (app.js, community.js, moved.js). Page links in it are site-relative; scripts add #site data-root."""
        return {"here": self.here_data,
                "paths": {"paths": [
                    {"id": p["id"], "title": p["title"],
                     "stops": [{"page": s["page"], "anchor": s["anchor"], "title": s["title"], "lead": s["lead"]}
                               for s in p["stops"]]} for p in sitemap.PATHS]}}


SITE_DATA = "assets/site-data.js"


def site_data_js(site) -> str:
    """assets/site-data.js: one cached script that sets window.civicData before assets/app.js runs (both deferred, so
    they run in document order). JSON is valid JavaScript once U+2028/U+2029 are escaped; '<' is escaped as in
    json_script, so the text is the same either way. Allowed by the CSP's script-src 'self'."""
    import json
    text = json.dumps(site.site_data(), ensure_ascii=False, separators=(",", ":"))
    text = text.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return ("/* Shared data for every page's scripts (civic/shell.py site_data): saved place, learning paths. */\n"
            f"window.civicData = {text};\n")


def write_site_data(site) -> int:
    dest = site.out / SITE_DATA
    dest.parent.mkdir(parents=True, exist_ok=True)
    js = site_data_js(site)
    dest.write_text(js, encoding="utf-8", newline="\n")
    return len(js.encode("utf-8"))


# A page displays unofficial figures when its content carries an UNOFFICIAL status badge or mark (phase 6 step 1)
# (2026-11-18: and the symbol mark or section caption of the "About these figures" system, components.figure_mark)
_UNOFFICIAL_MARK = re.compile(r'class="badge badge-unofficial"|class="smark smark-is-unofficial"'
                              r'|data-fmark="unofficial"|data-fscope="[^"]*\bunofficial\b')
_TAGS = re.compile(r"<[^>]+>")
# the symbol marks and section-wide statuses a page uses (components.figure_mark / scope_attrs), and the space a call
# site left before a mark (a mark sits right against its figure, like a footnote sign)
_FMARK_USE = re.compile(r'data-f(?:mark|scope)="([^"]+)"')
# a computed mark (components.figure_mark("computed"), link or span, caption or figure) with its word joiner
_COMPUTED_MARK = re.compile("⁠?<(a|span) class=\"fmark fmark-computed(?: fmark-scope)?\"[^>]*>‖</\\1>")
_QUIET_COMPUTED = '<span class="fquiet" data-fquiet="computed" data-word="COMPUTED" hidden></span>'
_FMARK_SPACE = re.compile("(?:[ \t\r\n]|&nbsp;|&#160;|\u00a0)+(?=\u2060<(?:a|span) class=\"fmark )")
# legends that show every badge or mark to define it (about/#badges, an office's Sources tab #marks) are not figures
_LEGENDS = re.compile(r'<(dl|ul) class="(?:badge-defs|marks-key)"[^>]*>.*?</\1>', re.S)


# the one sentence that stands for every computed mark of a page (Page._with_figure_notes)
COMPUTED_ONCE = ("Computed figures are not marked one by one: every figure on this page that is the guide's own "
                 "arithmetic (a sum, share, per-resident amount or conversion of sourced figures) is covered by the "
                 "‖ entry above.")


def shows_unofficial(main_html: str, year: str | None = None) -> bool:
    """True when a page's content (its <main> HTML) shows a figure whose status is unofficial: an UNOFFICIAL badge
    (components.status_badge) or mark (civic/tabs.py status_mark), outside the legends that define the badges. With
    ``year``, the content must also name that year, so a page showing only older election-night figures (the 2015 city
    election is still labelled unofficial in results.csv) does not get the 2026 notice."""
    html = _LEGENDS.sub("", main_html)
    if not _UNOFFICIAL_MARK.search(html):
        return False
    return not year or re.search(rf"\b{re.escape(year)}\b", _TAGS.sub(" ", html)) is not None


class Page:
    def __init__(self, site: Site, path: str, title: str, description: str, entry=None,
                 banners: bool = False, body_class: str = ""):
        self.site = site
        self.ed = site.ed
        self.path = path
        self.title = title
        self.description = description
        self.entry = entry
        self.banners = banners
        self.body_class = body_class
        self.cites = Citations(site.ed)
        self.parts: list[Markup] = []
        # added 2026-11-16 (phase 6 step 4): a site path for <link rel="canonical"> (a forwarding page names the page
        # its content moved to); None writes no canonical link
        self.canonical: str | None = None
        # added 2026-11-16 (phase 6 step 3): extra <head> tags (a forwarding page's civic-moved-to meta, which
        # tools/site/netlify_prep.py turns into a 301; pages/governments.py forward_page)
        self.head_extra: list = []

    # ---- links --------------------------------------------------------------------
    @property
    def is_root_index(self) -> bool:
        return self.path == "index.html"

    @property
    def root(self) -> str:
        depth = self.path.count("/")
        return "../" * depth or "./"

    def rel(self, target: str) -> str:
        """Relative URL from this page to a site-root path ('county/index.html#boards')."""
        if target.startswith(("http://", "https://", "#", "mailto:", "tel:")):
            return target
        path, _, frag = target.partition("#")
        here = posixpath.dirname(self.path) or "."
        r = posixpath.relpath(path or self.path, here)
        return r + (f"#{frag}" if frag else "")

    def add(self, *items) -> None:
        self.parts.extend(i for i in items if i)

    def finish(self, gaps: list[dict] | None = None, gaps_intro: str | None = None) -> None:
        """Append the 'Gaps on this page' list (if given) and the per-page Sources list.
        Call last, after every citation on the page has been made."""
        if gaps is not None:
            self.add(gaps_section(gaps, self, gaps_intro))
        self.add(self.cites.render())

    # ---- chrome -------------------------------------------------------------------
    def _head(self) -> Markup:
        ed = self.ed
        og_title = f"{self.title} · {ed.county_label}, IN"
        tags = [
            h("title", None, f"{self.title} · {ed.county_label}" if not self.is_root_index else self.title),
            # index.html gets no <head>; a charset meta right after <title> keeps local previews
            # correct (the host's skeleton already declares UTF-8).
            Markup('<meta charset="utf-8">') if self.is_root_index else None,
            rights_html(ed.config),
            Markup('<meta name="claude:viewport-fit-sides" content="cover">'),
            h("meta", {"name": "description", "content": self.description}),
            h("meta", {"property": "og:title", "content": og_title}),
            h("meta", {"property": "og:description", "content": self.description}),
            Markup(LOOK_BOOT),
            h("link", {"rel": "preconnect", "href": "https://fonts.googleapis.com"}),
            h("link", {"rel": "preconnect", "href": "https://fonts.gstatic.com", "crossorigin": True}),
            h("link", {"rel": "stylesheet", "href": FONTS}),
            h("link", {"rel": "stylesheet", "href": self.rel("assets/style.css")}),
            h("link", {"rel": "canonical", "href": self.rel(self.canonical)}) if self.canonical else None,
            *self.head_extra,
        ]
        return join(tags, "\n")

    def _masthead(self) -> Markup:
        """The header (phase 6 step 1, 2026-11-16): one row at desktop width,
        logo · Governments · Offices · Elections · Money · Learn · search · "My place" chip · Display.
        Below 1100 px: logo, search and a Menu button; the menu (``#primary-nav``) holds the nav, the chip and the
        Display control. Without JavaScript the Menu button is a link to ``#primary-nav`` and CSS ``:target`` opens it;
        static/js/nav.js turns it into a toggle. "Data as of", the version and "Not your county?" are in the footer.
        Display (the three looks and light/dark) needs JavaScript, so it is hidden without it (looks.css: the look
        boot script sets html[data-look])."""
        ed = self.ed
        cfg = ed.config
        return h("header", {"class": "masthead site-head", "id": "site-head"},
                 h("a", {"class": "lockup", "href": self.rel("index.html"),
                         "aria-label": f"{cfg['series']}, {cfg['edition']}: home"},
                   indiana_glyph_use(ed, self.rel(GLYPH_ASSET), "glyph"),
                   h("span", {"class": "lockup-text"},
                     h("span", {"class": "series"}, cfg["series"]),
                     h("span", {"class": "series-short", "aria-hidden": "true"}, "Civic Guide"),
                     h("span", {"class": "edition"}, cfg["edition"]))),
                 # DOM order = visual order at desktop (nav, search, chip, Display), so keyboard focus follows the
                 # row; below 1100 px both .head-menu parts fold behind the Menu button (#primary-nav:target ~
                 # .head-tools opens the second part with JS off)
                 h("div", {"class": "head-menu", "id": "primary-nav"},
                   self._nav()),
                 self._search(),
                 h("div", {"class": "head-menu head-tools", "id": "head-tools"},
                   self._here_bar(),
                   self._display()),
                 h("a", {"class": "menu-btn", "id": "menu-btn", "href": "#primary-nav",
                         "aria-controls": "primary-nav head-tools"},
                   h("span", {"class": "menu-btn-icon", "aria-hidden": "true"}), "Menu"))

    def _display(self) -> Markup:
        """One compact control for the three looks and light/dark (Nick's decision D2: the looks stay, they leave the
        header's main row). A <details> menu like the nav's; the ids look-switch-head and theme-toggle are kept."""
        return h("details", {"class": "nav-dd display-menu", "id": "display-menu", "data-nav-menu": True},
                 h("summary", {"class": "display-btn"},
                   h("span", {"class": "theme-icon", "aria-hidden": "true"}), "Display"),
                 h("div", {"class": "menu-panel display-panel"},
                   look_switch("head"),
                   h("p", {"class": "display-theme"},
                     h("button", {"type": "button", "class": "theme-toggle", "id": "theme-toggle",
                                  "aria-label": "Switch between light and dark theme"},
                       h("span", {"class": "theme-icon", "aria-hidden": "true"}), "Light / dark"))))

    def _search(self) -> Markup:
        """Header search (static/js/search.js): an ARIA 1.2 combobox over assets/search-index.json.
        Without JS only the "Browse everything" link (the footer list) shows."""
        return h("div", {"class": "site-search", "id": "site-search"},
                 h("a", {"class": "search-nojs", "href": "#browse"}, "Browse everything"),
                 h("form", {"class": "search-form", "id": "search-form", "role": "search", "aria-label": "Search the guide",
                            "hidden": True, "data-index": self.rel("assets/search-index.json")},
                   h("label", {"class": "visually-hidden", "for": "site-search-input"}, "Search the guide"),
                   h("span", {"class": "search-icon", "aria-hidden": "true"}),
                   h("input", {"type": "text", "id": "site-search-input", "name": "q", "class": "search-input",
                               "placeholder": "Search offices, places, people", "autocomplete": "off", "spellcheck": "false",
                               "role": "combobox", "aria-expanded": "false", "aria-controls": "site-search-list",
                               "aria-autocomplete": "list", "aria-describedby": "site-search-help"}),
                   h("span", {"class": "visually-hidden", "id": "site-search-help"},
                     "Type two or more letters. Up and down arrows move through the results, Enter opens one, "
                     "Escape closes the list."),
                   h("div", {"class": "search-pop", "id": "site-search-pop", "hidden": True},
                     h("p", {"class": "search-status", "id": "site-search-status", "role": "status", "aria-live": "polite"}),
                     h("ul", {"class": "search-list", "id": "site-search-list", "role": "listbox", "aria-label": "Search results"}),
                     h("p", {"class": "search-foot"}, h("a", {"href": "#browse"}, "Browse everything")))))

    def _here_bar(self) -> Markup:
        """The "My place" chip (phase 6 step 1; it replaces the "You are here" bar under the nav). Without JavaScript,
        or with no saved place, it reads "My place" and links to Your place (your-governments/, which lists every place
        to pick from). With a saved place static/js/here.js shows the place's name in it (the full list of the
        reader's governments is its title) and the link stays. The old bar's ids are kept on the chip."""
        yp = self.rel(sitemap.YOUR_PLACE)
        cur = "page" if self.path == sitemap.YOUR_PLACE else None
        return h("div", {"class": "here-bar place-chip", "id": "here-bar"},
                 h("a", {"class": "chip here-none", "id": "here-none", "href": yp, "aria-current": cur},
                   h("span", {"class": "here-pin", "aria-hidden": "true"}), "My place"),
                 h("a", {"class": "chip here-set", "id": "here-set", "href": yp, "hidden": True, "aria-current": cur},
                   h("span", {"class": "here-pin", "aria-hidden": "true"}),
                   h("span", {"class": "visually-hidden"}, "My place: "),
                   h("span", {"class": "here-names", "id": "here-names"})))

    def _nav(self) -> Markup:
        """Primary nav (phase 6 step 1): Governments · Offices · Elections · Money · Learn (sitemap.NAV).

        Each item is a link to its hub page plus a <details> dropdown of at most sitemap.MAX_DROPDOWN links, so
        without JavaScript the hub links work and the dropdowns open and close natively; static/js/nav.js adds
        aria-expanded, one menu open at a time, Escape and outside-click closing. The item the page sits under is
        marked (class is-current; aria-current="page" on the hub link when the page is the hub). The Governments menu
        keeps the id "ref-menu" and Learn "learn-menu" (older fixtures and static/app.js use them)."""
        by_path = self.site.by_path
        here_item = sitemap.nav_of(self.path)
        items = []
        for it in sitemap.NAV:
            links = [(p, label) for p, label in it["links"] if p.split("#")[0] in by_path][:sitemap.MAX_DROPDOWN]
            cur = it is here_item
            hub_cur = "page" if it["hub"] == self.path else None
            lis = []
            for p, label in links:
                lc = "page" if p == self.path else None
                lis.append(h("li", None, h("a", {"href": self.rel(p), "aria-current": lc}, label)))
            items.append(h("li", {"class": "nav-item" + (" is-current" if cur else "")},
                           h("a", {"class": "nav-top", "href": self.rel(it["hub"]), "aria-current": hub_cur},
                             it["name"]),
                           h("details", {"class": "nav-dd", "id": it["menu_id"], "data-nav-menu": True},
                             h("summary", {"class": "nav-more"},
                               h("span", {"class": "visually-hidden"}, f"More in {it['name']}")),
                             h("ul", {"class": "menu-panel menu-list", "aria-label": it["name"]}, lis)) if lis else None))
        return h("nav", {"class": "nav", "aria-label": "Primary"}, h("ul", {"class": "nav-list"}, items))

    def crumb_nav(self) -> Markup | None:
        """The page's breadcrumb (sitemap.crumbs) as the hero eyebrow: <nav class="crumbs eyebrow mono"
        aria-label="Breadcrumb"> with an <ol>; the topic and parent pages are links, the page itself is
        aria-current. None for the home page and pages outside every topic."""
        items = sitemap.crumbs(self.site.by_path, self.path)
        if not items:
            return None
        lis = []
        for i, (label, target) in enumerate(items):
            last = i == len(items) - 1
            sep = h("span", {"class": "crumb-sep", "aria-hidden": "true"}, " › ") if i else None
            if target:
                body = h("a", {"href": self.rel(target)}, label)
            else:
                body = h("span", {"aria-current": "page" if last else None}, label)
            lis.append(h("li", None, sep, body))
        return h("nav", {"class": "crumbs eyebrow mono", "aria-label": "Breadcrumb"}, h("ol", None, lis))

    def shows_unofficial(self, main_html: str | None = None, year: str | None = None) -> bool:
        """Whether this page's content shows unofficial figures (module-level ``shows_unofficial``)."""
        return shows_unofficial(str(self._main()) if main_html is None else main_html, year)

    def _banners(self, main_html: str | None = None) -> Markup:
        """The status banners of edition.json (the 2026 UNOFFICIAL notice), same wording as before. Changed
        2026-11-16 (phase 6 step 1): no longer decided by the page's ``banners`` flag but by its content; a banner shows
        only on a page that displays unofficial figures and names the banner's year (its id starts with the year:
        "2026-unofficial")."""
        out = []
        for b in self.ed.config.get("status_banners", []):
            m = re.match(r"(\d{4})", b.get("id", ""))
            if not self.shows_unofficial(main_html, m.group(1) if m else None):
                continue
            out.append(h("div", {"class": "banner banner-unofficial", "role": "note", "id": f"banner-{b['id']}"},
                         status_label("unofficial", self), h("p", None, b["text"])))
        return join(out)

    def _footer(self) -> Markup:
        """Footer (phase 6 step 1; columns 2026-11-18): four short labeled columns (sitemap.FOOTER_COLUMNS: Explore, People
        and place, Data and sources, About the guide; together they are "Browse everything", the search's no-JavaScript
        fallback), the neutrality line, the byline, and the stamp with the data date (once) and version."""
        ed = self.ed
        cfg = ed.config
        by_path = self.site.by_path
        disclosure = cfg.get("author_disclosure", "")
        if not disclosure or disclosure.startswith("["):
            disclosure_m = h("span", None, "Author disclosure statement: pending, to be published on ",
                             h("a", {"href": self.rel("about/index.html#author")}, "About"), ".")
        else:
            disclosure_m = h("span", None, esc(cfg.get("author_disclosure_short") or disclosure), " ",
                             h("a", {"href": self.rel("about/index.html#disclosure")}, "Full disclosure"), ".")
        # phase 6 (2026-11-18): labeled columns (sitemap.FOOTER_COLUMNS); a link to a page that is not built is left out
        columns = []
        for heading, items in sitemap.FOOTER_COLUMNS:
            items = [(p, l) for p, l in items if p.split("#")[0] in by_path]
            if items:
                columns.append(h("div", {"class": "foot-col"},
                                 h("p", {"class": "foot-h mono"}, heading),
                                 h("ul", None, [h("li", None, h("a", {"href": self.rel(p),
                                                                     "aria-current": "page" if p == self.path else None}, l))
                                                for p, l in items])))
        return h("footer", {"class": "site-footer"},
                 h("nav", {"class": "browse foot-cols", "id": "browse", "aria-label": "Browse everything"}, columns),
                 h("div", {"class": "footer-main"},
                   h("p", {"class": "np"}, "Built to published ",
                     h("a", {"href": self.rel("about/index.html#neutrality")}, "neutrality rules"),
                     ". Every figure links to its source. No ads, no endorsements."),
                   h("p", {"class": "byline"}, f"Built from public records by {cfg.get('author', '')}. ", disclosure_m)),
                 h("p", {"class": "stamp footer-stamp mono"},
                   h("span", {"class": "stamp-date"}, "Data as of ",
                     h("time", {"datetime": cfg["data_as_of"]}, fmt_date(cfg["data_as_of"]))),
                   h("span", {"class": "stamp-ver"}, f"v{cfg.get('version', '')}")),
                 # the data date and version are in the stamp above (shown on screen and in print), so the colophon
                 # names only the series and edition (phase 6, 2026-11-16: the date was printed twice)
                 h("p", {"class": "edition-stamp mono"},
                   f"{cfg['series']} · {cfg['edition']}",
                   h("span", {"class": "print-only"}, f" · {self.path}")))

    # ---- output -------------------------------------------------------------------
    def _main(self) -> Markup:
        """The page's parts. A page whose hero still carries a hand-written eyebrow (<p class="eyebrow mono">, the
        pre-batch-6 "Reference · Money" labels in the page modules) gets the sitemap breadcrumb in its place, so the
        labels follow sitemap.py (Wave D batch 6 renames: Reference -> Topics, Context -> Community & history, ...).
        Only the first such paragraph is replaced, and only when the sitemap has a breadcrumb for the page."""
        html = join(self.parts, "\n")
        crumb = self.crumb_nav()
        if crumb is None:
            return html
        return Markup(_LEGACY_EYEBROW.sub(lambda m: str(crumb), str(html), count=1))

    def _with_figure_notes(self, main: Markup) -> Markup:
        """Added 2026-11-18 (phase 6, "About these figures"): the page's symbol marks (components.figure_mark) sit right
        against their figures (no space before a mark), and the page ends with one "About these figures" note listing
        only the symbols it uses, each meaning once (a mark inside a section that states the same status once, in its
        caption line, is dropped: components.drop_scoped). A tab page's note links on to the thing's Sources tab, another
        page's to the definitions on About. A page with no marks gets no note. Static HTML: works with JavaScript off."""
        html = _FMARK_SPACE.sub("", drop_scoped(str(main)))
        # "Computed" is said once per page (owner, 2026-11-18; maps-cleanup brief part B item 5): each computed mark
        # becomes a quiet marker (hidden, no symbol; Copy CSV still writes its word), so the status stays recorded on
        # its figure, and the note at the bottom of the page says it once.
        html, n_quiet = _COMPUTED_MARK.subn(_QUIET_COMPUTED, html)
        once_computed = bool(n_quiet)
        kinds = {k for m in _FMARK_USE.finditer(html) for k in m.group(1).split()}
        if once_computed:
            kinds.add("computed")
        if not kinds:
            return Markup(html)
        from .tabs import tab_path
        thing = self.entry.thing if self.entry is not None else ""
        src = tab_path(thing, "sources") if thing else ""
        if src and src in self.site.by_path and self.path != src:
            more = h("span", None, "Where each figure comes from, and what every mark means: the ",
                     h("a", {"href": self.rel(src + "#marks")}, "Sources tab"), ".")
        elif src and self.path == src:
            more = h("span", None, "Every mark is listed under ", h("a", {"href": "#marks"}, "What the marks mean"), ".")
        else:
            more = h("span", None, "Every mark is defined on ",
                     h("a", {"href": self.rel("about/index.html#badges")}, "About: how figures are marked"), ".")
        if once_computed:
            more = h("span", None, COMPUTED_ONCE, " ", more)
        return Markup(html + str(figure_notes(kinds, more)))

    def render(self) -> str:
        cls = "site" + (f" {self.body_class}" if self.body_class else "")
        onpage = ' data-onpage="1"' if self.path in ONPAGE_PAGES else ""
        main = self._main()
        # every person name printed with a party tag (and every candidate name in a results chart) links to the
        # person's page (phase 6 people pages, 2026-11-16; civic/people.py link_names)
        from .people import link_names
        main = Markup(link_names(str(main), self))
        main = self._with_figure_notes(main)
        # the map navigator's row keys, written once per page (civic/navmap.py)
        from .navmap import compact_row_keys
        main = Markup(compact_row_keys(str(main)))
        body = join([
            h("a", {"class": "skip-link", "href": "#main"}, "Skip to content"),
            Markup(f'<div class="{esc(cls)}" id="site" data-root="{esc(self.root)}" data-page="{esc(self.path)}"{onpage}>'),
            self._masthead(),
            self._banners(str(main)),
            h("div", {"id": "path-bar", "class": "path-bar", "hidden": True, "aria-live": "polite"}),
            h("main", {"id": "main", "tabindex": "-1"}, main),
            self._footer(),
            Markup("</div>"),
            # the shared script data (saved place, learning paths) is one cached file, not inlined on every page
            h("script", {"src": self.rel(SITE_DATA), "defer": True}),
            h("script", {"src": self.rel("assets/app.js"), "defer": True}),
        ], "\n")
        if self.is_root_index:
            return f"{self._head()}\n{body}\n"
        return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
                f"{self._head()}\n</head>\n<body>\n{body}\n</body>\n</html>\n")
