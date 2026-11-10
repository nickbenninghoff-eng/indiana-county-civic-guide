"""Every page of a county edition, the navigation menus and the learning paths.

Paths are relative to the edition's site root and always end in 'index.html'
(the Artifact host does not resolve bare directories). A page builder that writes one
of these paths replaces its stub; every entry without a builder gets a stub so links
never 404.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Entry:
    path: str
    title: str
    nav: str
    description: str
    scope: str = "county"          # indiana | county | mixed
    group: str = ""               # topic the page belongs to (TOPICS name; "" = none). The menu itself is TOPICS
    sections: list[tuple[str, str]] = field(default_factory=list)  # planned (anchor, title)


def _e(path, title, nav, description, scope="county", group="", sections=None):
    return Entry(path, title, nav, description, scope, group, list(sections or []))


# The data page is an index; each dataset has its own page at data/<slug>/index.html.
# (slug, page title, one line). The slug is the dataset's anchor without "ds-" (pages/meta.py DATASETS).
DATA_PAGES = [
    ("results", "Data: election results", "Every contest and candidate from 1963 to 2026, with a preview and Copy CSV."),
    ("elections", "Data: elections", "One row per election: date, type, registered voters, ballots cast and turnout."),
    ("terms", "Data: terms of office", "Who held each seat and when, with how they were chosen."),
    ("offices", "Data: offices", "Every elected office in the county: government, district, seats and term length."),
    ("units", "Data: units of government", "The county, cities, towns, townships, school corporations and special districts."),
    ("budgets", "Data: budgets", "Budget totals by unit and year, with reporting basis and series."),
    ("tax-rates", "Data: property tax rates", "Tax rates per $100 of assessed value, by unit, taxing district and year."),
    ("debt", "Data: debt", "Year-end principal owed by each unit, by type of debt."),
    ("cf-state", "Data: state campaign finance", "Receipts and spending of the committees of legislators whose districts include part of the county."),
    ("cf-local", "Data: local campaign finance", "One row per campaign-finance report filed with the county, as written on the form."),
    ("cf-large", "Data: local large contributions", "Contributions of $1,000 or more reported on the county's large-contribution forms."),
    ("indicators", "Data: community indicators", "Census and Bureau of Labor Statistics figures with margins of error."),
    ("people", "Data: people who shaped local government", "People chosen by the published rules, with offices and documented findings."),
]


def entries(ed) -> list[Entry]:
    county = ed.county_label
    out = [
        _e("index.html", f"Civic Guide · {county}", "Home",
           # Nick, 2026-11-09: the guide is a central reference for the whole county; the address lookup stays.
           f"A sourced reference for {county}'s local governments: who holds every seat, election results and "
           "close races, and the campaign money behind them. Look up the governments that cover your address."),
        # "Your place" (Wave D batch 6; was "Find your governments"): the result for the reader's saved place. The
        # picker and seat diagram are the home page's; this page keeps its URL and its path-stop ids.
        _e("your-governments/index.html", "Your place", "Your place",
           "Every government that covers your saved place: its seats, what each office decides, who holds the seats "
           "and how to reach it.",
           "county", "Your governments",
           [("find", "Your governments"), ("offices", "What each office controls"),
            ("meetings", "How to contact or attend a meeting")]),
        _e("who-handles-this/index.html", "Who handles this?", "Who handles this?",
           "Common services (roads, trash, schools, property records) matched to the government responsible and the official accountable.",
           "county", "Your governments", [("services", "Services and who handles them")]),
        _e("places/index.html", "Places", "Places",
           "Every city, town and township in the county, each with its structure, officeholders and budget links.",
           "county", "Your governments"),
        _e("officeholders/index.html", "Who holds office now", "Who holds office now",
           "Every current elected officeholder in the county, by government, and how each first took office.",
           "county", "Your governments",
           [("how-took-office", "How they first took office"), ("every", "Every officeholder, by government")]),
        _e("map/index.html", "Map: who governs where", "Map",
           "Interactive boundary map of cities and towns, townships and school corporations, each linked to its page.",
           "county", "Your governments"),
        _e("county/index.html", "County government", "County government",
           "Commissioners, council, row officers, courts and appointed boards of the county.",
           "mixed", "Your governments"),
        _e("schools/index.html", "School corporations", "Schools",
           "School corporations: board structure, seats, the 2025 party-label change and referenda.",
           "mixed", "Your governments"),
        _e("state/index.html", "State government", "State government",
           "Indiana's statewide offices and General Assembly, as they touch the county.",
           "mixed", "Your governments"),
        _e("state/your-legislators/index.html", "Your legislators", "Your legislators",
           "State House and Senate districts that include part of the county, and who holds them.",
           "county", "Your governments"),
        _e("state/how-the-state-shapes-local/index.html", "How the state shapes local government",
           "How the state shapes local", "Home rule, property tax caps, levy limits, SEA 1 (2025) and local income tax changes.",
           "indiana", "Your governments", [("caps", "Property tax caps and levy limits")]),
        # Elections hub (Wave D batch 6); the explainer that was here moved to elections/how-it-works/ (anchors
        # forwarded by static/js/moved.js, pages/elections.py HOW_IT_WORKS_IDS)
        _e("elections/index.html", "Elections", "Elections",
           "Where each part of the guide's election record is: the calendar, results, the numbers, judges and ballot "
           "questions, how elections work and how to run.",
           "county", "Elections", [("pages", "Election pages")]),
        _e("elections/how-it-works/index.html", "How Indiana elections work", "How elections work",
           "Calendar, primaries, ballot access, voting methods and ID, vacancies and caucuses.",
           "indiana", "Elections", [("offices", "Offices on the ballot"),
                                    ("candidate-info", "Where to find candidate information")]),
        _e("elections/calendar/index.html", "Election calendar", "Calendar",
           "What is on the ballot in each year from 2026 to 2030, filled in for this county.",
           "county", "Elections", [("next", "What's on your next ballot")]),
        _e("elections/results/index.html", "Election results", "Results",
           "Results 2010 to 2026 by office and year, each marked official, unofficial or from scan.",
           "county", "Elections", [("turnout", "Turnout first"), ("by-office", "Results by office")]),
        _e("elections/judges-and-questions/index.html", "Judges and public questions", "Judges & ballot questions",
           "Judicial retention votes, public questions and school-board party labels.",
           "mixed", "Elections", [("retention", "Judicial retention votes"),
                                            ("questions", "Public questions")]),
        _e("elections/landscape/index.html", "Elections by the numbers", "By the numbers",
           "Four measures for every race and every party, looking back: turnout, how close races were, the seats on the "
           "next ballots and how officeholders first took office.",
           "county", "Elections",
           [("turnout", "Turnout"), ("margins", "How close were the races?"),
            ("up-next", "Up next"), ("how-took-office", "How officeholders first took office")]),
        # Wave B batch 2 (2026-11-09): the landscape page's four measures, each on its own page
        _e("elections/margins/index.html", "Margins: how close each race was", "Close races",
           "Every race decided inside the county since 2010: how many had no contest, how close the others were, by "
           "level of government and on a map.",
           "county", "Elections",
           [("short-answer", "The short answer"), ("by-level", "By level of government"), ("find", "Find a race"),
            ("all-races", "All races as a table")]),
        _e("elections/turnout/index.html", "Turnout and how ballots were cast", "Turnout",
           "Turnout in every election since 2010 with its denominator, odd and even years, and straight-party ballots.",
           "county", "Elections",
           [("turnout", "Turnout: odd vs even years"), ("straight-party", "Straight-party ballots")]),
        _e("run/index.html", "Run for office", "Run for office",
           "Eligibility, terms, filing, petitions, caucuses and local contacts for each office.",
           "mixed", "Elections",
           [("pick", "Pick an office"), ("eligibility", "Eligibility, term and next election"),
            ("ballot-access", "Getting on the ballot"), ("vacancies", "Vacancies and caucuses"),
            ("contacts", "Contacts")]),
    ]
    for slug, label in [("township-trustee", "Township trustee"), ("township-board", "Township board"),
                        ("school-board", "School board"), ("city-council", "City council"),
                        ("county-council", "County council"), ("precinct-committeeperson", "Precinct committeeperson")]:
        secs = [("role", "What the office does")] if slug == "precinct-committeeperson" else []
        out.append(_e(f"run/{slug}/index.html", f"Run for {label.lower()}", label,
                      f"Rules, forms, deadlines and the next regular election for {label.lower()}.",
                      "mixed", "Elections", secs))
    out += [
        _e("money/index.html", "Money", "Money",
           "Budgets, your tax bill and campaign finance, with the reporting basis of every figure.",
           "mixed", "Money"),
        _e("money/what-is-a-budget/index.html", "What counts as a budget", "What is a budget?",
           "General fund, advertised all-funds and other bases, and why totals differ.",
           "indiana", "Money", [("basics", "What counts as a budget")]),
        _e("money/your-tax-bill/index.html", "Your tax bill", "Your tax bill",
           "How one property-tax bill is split among the units that tax you, from published rates.",
           "county", "Money", [("split", "Your tax bill, split by unit")]),
        _e("money/budgets/index.html", "Budgets by unit", "Budgets",
           "Budgets 2012 to 2026 for every unit, one basis per chart, with series breaks marked.",
           "county", "Money", [("over-time", "Budgets over time"), ("tax-base", "How the tax base shapes budgets")]),
        _e("money/campaigns/index.html", "Campaign finance", "Campaign finance",
           "Campaign money in local races by place: a map, then each government's races, candidates and reports.",
           "mixed", "Money", [("obligations", "Campaign-finance obligations"), ("public", "What's public and what isn't")]),
        _e("community/index.html", "The community", "Community",
           "Social and economic context: the same fixed indicators for every unit, with sources and margins of error.",
           "county", "Community & history"),
        _e("community/people/index.html", "Who lives here", "Who lives here",
           "Population over time, age, race and ethnicity, and households, using Census category names.",
           "county", "Community & history", [("who", "Who lives here")]),
        _e("community/income-and-work/index.html", "Income and work", "Income & work",
           "Income, poverty, jobs by industry and major employers chosen by a published rule.",
           "county", "Community & history", [("work", "Work and income")]),
        _e("community/housing-and-education/index.html", "Housing and education", "Housing & education",
           "Owner and renter households, home values and rents, educational attainment and enrollment.",
           "county", "Community & history", [("housing", "Housing and schools")]),
        _e("community/research-on-voting/index.html", "Research on place and voting", "Research on voting",
           "What published studies say about place, economy and voting, each attributed with its method and limits.",
           "mixed", "Community & history"),
        _e("history/index.html", "History", "History",
           "Party-control timelines, the mayors timeline, and political and economic turning points.",
           "county", "Community & history",
           [("control", "Party control over time"), ("mayors", "Mayors timeline"),
            ("economic", "Economic turning points"), ("political", "Political turning points")]),
        _e("history/people/index.html", "People who shaped local government", "People in local history",
           "People selected by published rules (tenure, firsts, higher office, families), with the rules shown.",
           "county", "Community & history", [("people", "People who shaped local government")]),
        _e("data/index.html", "Data and sources", "Data & sources",
           "Every table behind the guide, one page each with a preview and copy-to-clipboard CSV, and where the data comes from.",
           "mixed", "Data", [("sources", "Where the data comes from")]),
        *[_e(f"data/{slug}/index.html", title, title.replace("Data: ", ""), desc, "county", "Data",
             [("sources", "Sources")])
          for slug, title, desc in DATA_PAGES],
        _e("data/pull/index.html", "Data: how to pull it yourself", "How to pull the data yourself",
           "Where each public source lives and the query patterns the guide used, with this county's codes filled in.",
           "mixed", "Data", [("pull", "How to pull it yourself")]),
        _e("teach/index.html", "For teachers and groups", "For teachers",
           "Lesson kits built on the learning paths, with objectives, prompts and handouts.", "mixed"),
        _e("about/index.html", "About and methods", "About & methods",
           "Methods, neutrality policy, status badges, who made this, corrections and changelog.",
           "mixed", "",
           [("methods", "How we choose what to include"), ("badges", "Status and scope badges"),
            ("neutrality", "Neutrality policy"), ("counting", "How the layer diagram counts seats"),
            ("author", "Who made this"), ("corrections", "Corrections"), ("changelog", "Changelog"),
            ("sources", "Sources index")]),
        _e("about/sources/index.html", "Sources index", "Sources index",
           "Every source behind the guide, grouped by kind, with a search box.", "mixed", "",
           [("sources", "Sources index")]),
        _e("indiana/index.html", "Indiana's 92 counties", "Not your county?",
           "Choose a county edition. Editions not built yet still share the Indiana-wide chapters.", "indiana"),
    ]
    # one place page per city, town and township (template-generated later)
    for u in ed.tables["units"]:
        if u["unit_type"] in ("city", "town", "township"):
            kind = {"city": "City", "town": "Town", "township": "Township"}[u["unit_type"]]
            out.append(_e(f"places/{u['unit_id']}/index.html", u["name"], u["name"],
                          f"{kind} page: structure, offices and terms, results and budget links for {u['name']}.",
                          "county", "Your governments"))
    # campaign money: how reporting works, every filing, and one page per government (civic/campaign_money.py)
    from .campaign_money import campaign_entries
    out += [_e(*args) for args in campaign_entries(ed.tables["units"])]
    # every page in a topic names it (campaign area pages, run office pages...): search labels and stubs use it
    for e in out:
        t = topic_of(e.path)
        if t is not None and not e.group:
            e.group = t["name"]
    # attach path anchors to the pages they land on, so stubs carry the anchors
    by_path = {e.path: e for e in out}
    for p in PATHS:
        for stop in p["stops"]:
            e = by_path.get(stop["page"])
            if e is not None and stop["anchor"] and stop["anchor"] not in {a for a, _ in e.sections}:
                e.sections.append((stop["anchor"], stop["title"]))
    return out


# ---------------------------------------------------------------- navigation (Wave D batch 6, review section 1.4, Q1)
# Nav bar: Your place · Topics ▾ · Learn ▾ · About. Topics has one group per topic; each group heading links to the
# topic's hub page and the leaves follow the review's mock-up. A leaf is a site path, or a tuple of paths shown on
# one line ("State · Your legislators"). Labels are each entry's `nav`, unless MENU_LABELS gives a shorter menu label.
YOUR_PLACE = "your-governments/index.html"
TOPICS = [
    {"name": "Your governments", "hub": "your-governments/index.html",
     "leaves": ["places/index.html", "county/index.html", "schools/index.html",
                ("state/index.html", "state/your-legislators/index.html"), "officeholders/index.html",
                "who-handles-this/index.html", "map/index.html"]},
    {"name": "Elections", "hub": "elections/index.html",
     "leaves": ["elections/calendar/index.html", "elections/results/index.html", "elections/landscape/index.html",
                "elections/margins/index.html", "elections/turnout/index.html",
                "elections/judges-and-questions/index.html", "elections/how-it-works/index.html", "run/index.html"]},
    {"name": "Money", "hub": "money/index.html",
     "leaves": ["money/what-is-a-budget/index.html", "money/your-tax-bill/index.html", "money/budgets/index.html",
                "money/campaigns/index.html"]},
    {"name": "Community & history", "hub": "community/index.html",
     "leaves": ["community/people/index.html", "community/income-and-work/index.html",
                "community/housing-and-education/index.html", "community/research-on-voting/index.html",
                "history/index.html", "history/people/index.html"]},
    {"name": "Data", "hub": "data/index.html",
     "leaves": ["data/index.html#datasets", "data/pull/index.html", "about/sources/index.html"]},
]
REFERENCE_GROUPS = [t["name"] for t in TOPICS]   # kept for older callers: the topic names, in menu order
# Menu labels that differ from the entry's nav label (the mock-up's wording; the pages keep their titles)
MENU_LABELS = {
    "state/index.html": "State",
    "money/what-is-a-budget/index.html": "What counts as a budget",
    "money/campaigns/index.html": "Campaign money",
    "data/index.html#datasets": "All datasets",
    "data/pull/index.html": "Pull it yourself",
    "elections/margins/index.html": "Close races (margins)",
}
LEARN_PAGE = "teach/index.html"
ABOUT_PAGE = "about/index.html"

# Which topic a page belongs to, by its path (first match wins). Pages outside every topic: the home page, teach/,
# about/, indiana/.
_TOPIC_PREFIX = [
    ("your-governments/", "Your governments"), ("who-handles-this/", "Your governments"), ("places/", "Your governments"),
    ("officeholders/", "Your governments"), ("map/", "Your governments"), ("county/", "Your governments"),
    ("schools/", "Your governments"), ("state/", "Your governments"),
    ("elections/", "Elections"), ("run/", "Elections"),
    ("money/", "Money"),
    ("community/", "Community & history"), ("history/", "Community & history"),
    ("data/", "Data"),
]


def topic_of(path: str) -> dict | None:
    for prefix, name in _TOPIC_PREFIX:
        if path.startswith(prefix):
            return next(t for t in TOPICS if t["name"] == name)
    return None


def menu_label(by_path: dict, target: str) -> str:
    if target in MENU_LABELS:
        return MENU_LABELS[target]
    return by_path[target.split("#")[0]].nav


def crumbs(by_path: dict, path: str) -> list[tuple[str, str | None]]:
    """The breadcrumb for a page, from the sitemap: [(label, site path or None)], the last item being the page itself
    (path None). Topic pages: "Topics", the topic (linked to its hub), every parent page that exists (money/campaigns/
    for a campaign area page, history/ for history/people/, run/ for a run office page), then the page. teach/ and
    about/ pages start with "Learn" / "About". Empty for the home page and pages outside every topic."""
    e = by_path.get(path)
    if e is None or path == "index.html":
        return []
    out: list[tuple[str, str | None]] = []
    t = topic_of(path)
    if t is not None:
        out.append(("Topics", None))
        if path != t["hub"]:
            out.append((t["name"], t["hub"]))
    elif path.startswith("teach/"):
        out.append(("Learn", None))
    elif path.startswith("about/"):
        if path != ABOUT_PAGE:
            out.append(("About", ABOUT_PAGE))
    else:
        return []
    # parents: each ancestor directory with its own page, below the hub
    parts = path.split("/")[:-1]
    for i in range(1, len(parts)):
        anc = "/".join(parts[:i]) + "/index.html"
        if anc in by_path and anc != path and (t is None or anc != t["hub"]) and anc != ABOUT_PAGE:
            out.append((by_path[anc].nav, anc))
    label = t["name"] if t is not None and path == t["hub"] else e.nav
    out.append((label[:1].upper() + label[1:], None))
    return out


# Learning paths (ux-review 3.4). Each stop is one section of one reference page.
# 'lead' is a framing sentence only; it must never carry a factual claim.
PATHS = [
    {"id": "who-does-what", "title": "Who does what?", "blurb": "The governments that cover your place, and who fixes what.",
     "minutes": 15, "primary": True, "stops": [
        {"page": "your-governments/index.html", "anchor": "find", "title": "Your governments",
         "lead": "Start with the list of governments that cover your address."},
        {"page": "who-handles-this/index.html", "anchor": "services", "title": "Who handles this?",
         "lead": "Match everyday services to the government that runs them."},
        {"page": "county/index.html", "anchor": "boards", "title": "Unelected but powerful",
         "lead": "Some decisions sit with appointed boards. See who appoints them."},
        {"page": "your-governments/index.html", "anchor": "meetings", "title": "Contact or attend a meeting",
         "lead": "Where and how to reach each body."}]},
    {"id": "vote-smarter", "title": "Vote smarter", "blurb": "Know what's on your next ballot and why it matters.",
     "minutes": 25, "primary": True, "stops": [
        {"page": "elections/calendar/index.html", "anchor": "next", "title": "What's on your next ballot",
         "lead": "See which seats are up next where you live."},
        {"page": "your-governments/index.html", "anchor": "offices", "title": "What each office controls",
         "lead": "What the people you elect actually decide."},
        {"page": "elections/results/index.html", "anchor": "turnout", "title": "Results history, turnout first",
         "lead": "How many voters took part, then how each race came out."},
        {"page": "elections/judges-and-questions/index.html", "anchor": "retention", "title": "Judges and public questions",
         "lead": "The yes-or-no lines at the end of the ballot."},
        {"page": "elections/how-it-works/index.html", "anchor": "candidate-info", "title": "Where to find candidate information",
         "lead": "Official places to look up who is running."}]},
    {"id": "run", "title": "Run for office", "blurb": "Filing, petitions, caucuses and campaign money.",
     "minutes": 40, "primary": True, "stops": [
        {"page": "run/index.html", "anchor": "pick", "title": "Pick an office", "lead": "Compare the offices you could seek."},
        {"page": "run/index.html", "anchor": "eligibility", "title": "Eligibility, term and next election",
         "lead": "Who can run and when the seat is next on the ballot."},
        {"page": "run/index.html", "anchor": "ballot-access", "title": "Getting on the ballot",
         "lead": "Primaries, petitions and school-board labels."},
        {"page": "run/index.html", "anchor": "vacancies", "title": "Vacancies and caucuses",
         "lead": "How seats are filled between elections."},
        {"page": "run/precinct-committeeperson/index.html", "anchor": "role", "title": "Precinct committeeperson",
         "lead": "The party office that takes part in caucuses."},
        {"page": "money/campaigns/how-it-works/index.html", "anchor": "obligations", "title": "Campaign-finance obligations",
         "lead": "What a candidate must report, and when."},
        {"page": "run/index.html", "anchor": "contacts", "title": "Contacts", "lead": "Where to file and whom to ask."}]},
    {"id": "follow-the-money", "title": "Follow the money", "blurb": "Budgets, your tax bill and campaign money.",
     "minutes": 35, "primary": True, "stops": [
        {"page": "money/what-is-a-budget/index.html", "anchor": "basics", "title": "What counts as a budget",
         "lead": "Budget totals depend on which funds are counted."},
        {"page": "money/your-tax-bill/index.html", "anchor": "split", "title": "Your tax bill, split by unit",
         "lead": "One property-tax bill pays several governments."},
        {"page": "money/budgets/index.html", "anchor": "over-time", "title": "Budgets over time",
         "lead": "Each unit's budget on a single reporting basis."},
        {"page": "state/how-the-state-shapes-local/index.html", "anchor": "caps", "title": "How the state limits local revenue",
         "lead": "State law sets caps and limits on local taxes."},
        {"page": "money/campaigns/how-it-works/index.html", "anchor": "public", "title": "Campaign money: what's public",
         "lead": "What campaign reports show and what they leave out."}]},
    {"id": "how-we-got-here", "title": "How we got here", "blurb": "Seats, mayors and turning points over time.",
     "minutes": 35, "primary": True, "stops": [
        {"page": "history/index.html", "anchor": "control", "title": "Party control over time",
         "lead": "Which party held the seats, year by year."},
        {"page": "history/index.html", "anchor": "mayors", "title": "Mayors timeline", "lead": "Every mayor in the sources."},
        {"page": "history/index.html", "anchor": "economic", "title": "Economic turning points",
         "lead": "Dated, sourced events in the local economy."},
        {"page": "history/index.html", "anchor": "political", "title": "Political turning points",
         "lead": "Dated, sourced events in local politics."},
        {"page": "history/people/index.html", "anchor": "people", "title": "People who shaped local government",
         "lead": "Chosen by published rules, applied to everyone."}]},
    {"id": "elections-by-the-numbers", "title": "Elections by the numbers",
     "blurb": "Margins, turnout, open seats.", "minutes": 25, "primary": False, "stops": [
        # repointed to the pages split from elections/landscape/ (Wave B batch 2); static/js/moved.js sends an old
        # landscape/#path-elections-by-the-numbers-<n> link to the stop's new page
        {"page": "elections/turnout/index.html", "anchor": "turnout", "title": "Turnout: odd vs even years",
         "lead": "Turnout with its denominator shown."},
        {"page": "elections/margins/index.html", "anchor": "short-answer", "title": "How close were local races?",
         "lead": "Every race, the same measure."},
        {"page": "elections/calendar/index.html", "anchor": "year-2027", "title": "Up next: seats and term limits",
         "lead": "The seats on the next ballots, who holds them and the term-limit rule."},
        {"page": "officeholders/index.html", "anchor": "how-took-office", "title": "How incumbents took office",
         "lead": "Election, caucus or appointment."},
        {"page": "data/index.html", "anchor": "sources", "title": "Where the data comes from",
         "lead": "Every table and its source."}]},
    {"id": "know-your-community", "title": "Know your community",
     "blurb": "People, work, housing, schools.", "minutes": 25, "primary": False, "stops": [
        {"page": "community/people/index.html", "anchor": "who", "title": "Who lives here",
         "lead": "Population, age and households."},
        {"page": "community/income-and-work/index.html", "anchor": "work", "title": "Work and income",
         "lead": "Industries, employers and income."},
        {"page": "community/housing-and-education/index.html", "anchor": "housing", "title": "Housing and schools",
         "lead": "Housing tenure, values and schooling."},
        {"page": "money/budgets/index.html", "anchor": "tax-base", "title": "How the tax base shapes budgets",
         "lead": "Connects to Follow the money."}]},
]
