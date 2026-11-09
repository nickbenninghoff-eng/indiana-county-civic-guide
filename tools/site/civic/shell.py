"""Page shell: relative links at any depth, masthead, nav, footer, and the two output
forms required by the Artifact host:

* ``index.html`` (the site root) is published as THE page and wrapped in a skeleton by
  the host, so it is written WITHOUT doctype/html/head/body: it starts with <title>.
* every other page is a complete document.
"""
from __future__ import annotations

import posixpath
from pathlib import Path

from . import sitemap
from .components import Citations, gaps_section, section, status_badge
from .data import fmt_date
from .glyph import indiana_glyph
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
        return written


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
            Markup('<meta name="claude:viewport-fit-sides" content="cover">'),
            h("meta", {"name": "description", "content": self.description}),
            h("meta", {"property": "og:title", "content": og_title}),
            h("meta", {"property": "og:description", "content": self.description}),
            Markup(LOOK_BOOT),
            h("link", {"rel": "preconnect", "href": "https://fonts.googleapis.com"}),
            h("link", {"rel": "preconnect", "href": "https://fonts.gstatic.com", "crossorigin": True}),
            h("link", {"rel": "stylesheet", "href": FONTS}),
            h("link", {"rel": "stylesheet", "href": self.rel("assets/style.css")}),
        ]
        return join(tags, "\n")

    def _masthead(self) -> Markup:
        ed = self.ed
        cfg = ed.config
        return h("header", {"class": "masthead"},
                 h("a", {"class": "lockup", "href": self.rel("index.html"),
                         "aria-label": f"{cfg['series']}, {cfg['edition']}: home"},
                   indiana_glyph(ed, "glyph"),
                   h("span", {"class": "lockup-text"},
                     h("span", {"class": "series"}, cfg["series"]),
                     h("span", {"class": "edition"}, cfg["edition"]))),
                 h("div", {"class": "stamp"},
                   h("span", {"class": "stamp-date"}, "Data as of ",
                     h("time", {"datetime": cfg["data_as_of"]}, fmt_date(cfg["data_as_of"]))),
                   h("span", {"class": "stamp-ver"}, f"v{cfg.get('version', '')}"),
                   h("a", {"class": "stamp-county", "href": self.rel("indiana/index.html")}, "Not your county?"),
                   h("button", {"type": "button", "class": "theme-toggle", "id": "theme-toggle",
                                "aria-label": "Switch between light and dark theme"},
                     h("span", {"class": "theme-icon", "aria-hidden": "true"}), "Theme")),
                 self._search(),
                 look_switch("head"))

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
                               "placeholder": "Town, office or person", "autocomplete": "off", "spellcheck": "false",
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
        """"You are here" bar (static/js/here.js fills it from localStorage `civic-place`). Hidden without JS."""
        pick = self.rel("index.html#pick")
        return h("div", {"class": "here-bar", "id": "here-bar", "hidden": True},
                 h("p", {"class": "here-set", "id": "here-set", "hidden": True},
                   h("span", {"class": "here-pin", "aria-hidden": "true"}),
                   h("strong", {"class": "here-label"}, "You are here:"), " ",
                   h("span", {"class": "here-names", "id": "here-names"}),
                   h("a", {"class": "here-change", "href": pick}, "Change", h("span", {"class": "visually-hidden"}, " your place"))),
                 h("p", {"class": "here-none", "id": "here-none", "hidden": True},
                   h("span", {"class": "here-pin", "aria-hidden": "true"}),
                   h("a", {"class": "here-pick", "href": pick}, "Pick your place to see what applies to you")))

    def _nav(self) -> Markup:
        def link(path, label, extra_cls=None):
            target_path = path.split("#")[0]
            current = "page" if target_path == self.path and "#" not in path else None
            return h("a", {"href": self.rel(path), "aria-current": current, "class": extra_cls}, label)

        groups = []
        for g in sitemap.REFERENCE_GROUPS:
            items = [e for e in self.site.entries if e.group == g]
            groups.append(h("div", {"class": "menu-group"}, h("p", {"class": "menu-head"}, g),
                            h("ul", None, [h("li", None, link(e.path, e.nav)) for e in items])))
        ref_current = self.entry is not None and bool(self.entry.group)
        return h("nav", {"class": "nav", "aria-label": "Primary"},
                 h("ul", {"class": "nav-list"},
                   h("li", None, link("index.html#paths", "Paths")),
                   h("li", {"class": "nav-menu"},
                     h("details", {"id": "ref-menu"},
                       h("summary", {"class": "is-current" if ref_current else None}, "Reference"),
                       h("div", {"class": "menu-panel"}, groups))),
                   h("li", None, link("teach/index.html", "For teachers")),
                   h("li", None, link("about/index.html", "About & methods"))))

    def _banners(self) -> Markup:
        if not self.banners:
            return Markup("")
        out = []
        for b in self.ed.config.get("status_banners", []):
            out.append(h("div", {"class": "banner banner-unofficial", "role": "note", "id": f"banner-{b['id']}"},
                         status_badge("unofficial", self), h("p", None, b["text"])))
        return join(out)

    def _footer(self) -> Markup:
        ed = self.ed
        cfg = ed.config
        browse = [("places/index.html", "Places"), ("county/index.html", "County"),
                  ("schools/index.html", "Schools"), ("state/index.html", "State"),
                  ("elections/index.html", "Elections"), ("money/index.html", "Money"),
                  ("history/index.html", "History"), ("data/index.html", "Data")]
        disclosure = cfg.get("author_disclosure", "")
        if not disclosure or disclosure.startswith("["):
            disclosure_m = h("span", None, "Author disclosure statement: pending, to be published on ",
                             h("a", {"href": self.rel("about/index.html#author")}, "About"), ".")
        else:
            disclosure_m = h("span", None, esc(cfg.get("author_disclosure_short") or disclosure), " ",
                             h("a", {"href": self.rel("about/index.html#disclosure")}, "Full disclosure"), ".")
        return h("footer", {"class": "site-footer"},
                 h("nav", {"class": "browse", "id": "browse", "aria-label": "Browse everything"},
                   h("span", {"class": "browse-head mono"}, "Browse everything"),
                   h("ul", None, [h("li", None, h("a", {"href": self.rel(p)}, l)) for p, l in browse])),
                 h("div", {"class": "footer-main"},
                   h("p", {"class": "np"}, "Built to published ",
                     h("a", {"href": self.rel("about/index.html#neutrality")}, "neutrality rules"),
                     ". Every figure links to its source. No ads, no endorsements."),
                   h("ul", {"class": "footer-links"},
                     h("li", None, h("a", {"href": self.rel("about/index.html#methods")}, "How we choose what to include")),
                     h("li", None, h("a", {"href": self.rel("about/index.html#corrections")}, "Corrections log")),
                     h("li", None, h("a", {"href": self.rel("about/sources/index.html")}, "Sources index")),
                     h("li", None, h("a", {"href": self.rel("about/index.html#badges")}, "What the badges mean")),
                     h("li", None, h("a", {"href": self.rel("about/index.html#changelog")}, "Changelog"))),
                   h("p", {"class": "byline"}, f"Built from public records by {cfg.get('author', '')}. ", disclosure_m)),
                 h("p", {"class": "edition-stamp mono"},
                   f"{cfg['series']} · {cfg['edition']} · Data as of {cfg['data_as_of']} · v{cfg.get('version', '')}",
                   h("span", {"class": "print-only"}, f" · {self.path}")))

    # ---- output -------------------------------------------------------------------
    def render(self) -> str:
        paths_payload = {"root": self.root, "paths": [
            {"id": p["id"], "title": p["title"],
             "stops": [{"page": s["page"], "anchor": s["anchor"], "title": s["title"], "lead": s["lead"]}
                       for s in p["stops"]]} for p in sitemap.PATHS]}
        cls = "site" + (f" {self.body_class}" if self.body_class else "")
        body = join([
            h("a", {"class": "skip-link", "href": "#main"}, "Skip to content"),
            Markup(f'<div class="{esc(cls)}" id="site" data-root="{esc(self.root)}" data-page="{esc(self.path)}">'),
            self._masthead(),
            self._nav(),
            self._here_bar(),
            self._banners(),
            h("div", {"id": "path-bar", "class": "path-bar", "hidden": True, "aria-live": "polite"}),
            h("main", {"id": "main", "tabindex": "-1"}, join(self.parts, "\n")),
            self._footer(),
            Markup("</div>"),
            json_script("paths-data", paths_payload),
            json_script("here-data", self.site.here_data),
            h("script", {"src": self.rel("assets/app.js"), "defer": True}),
        ], "\n")
        if self.is_root_index:
            return f"{self._head()}\n{body}\n"
        return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
                f"{self._head()}\n</head>\n<body>\n{body}\n</body>\n</html>\n")
