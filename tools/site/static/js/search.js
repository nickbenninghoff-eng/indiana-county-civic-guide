/* Header search (civic/shell.py _search, index built by civic/search.py into assets/search-index.json).
   ARIA 1.2 combobox: the input owns a listbox; arrows move the active option (aria-activedescendant),
   Enter opens it, Escape closes the list (a second Escape clears the box). Matching is case- and
   accent-insensitive: every typed word must be the start of a word in the name, its context line or its
   keywords (an office tab's plain words, never shown: "money", "results", "history"...).
   Ranking: exact name, then name starts with the text, then all words in the name, then all words in the name or
   the keywords, then context matches. An office tab ("Mayor of South Bend > Money") ranks 25 lower unless a typed
   word names the tab or one of its keywords, so "mayor" lists the offices first and "mayor money" the Money tabs.
   Ties by kind (place, office, office tab, officeholder, person, page, section) and then the index's own order
   (offices in the county's listing order, everything else alphabetical). Party tags are display text only, never
   matched or ranked. Without JS the form stays hidden and the "Browse everything" link shows. ASCII only; text
   inserted with textContent only. The matching core is window.civicSearchCore (prepare, rank), so tools/tests can
   run it on the built index. */
var civicSearchCore = (function () {
  "use strict";
  /* kind index -> tie rank (civic/search.py TYPES: Place, Office, Officeholder, Person, Page, Section, Office tab,
     Election, Election tab; the last two added 2026-11-16) */
  var KIND_RANK = [0, 1, 3, 4, 5, 6, 2, 7, 8, 2, 2];
  var T_TAB = 6;
  var T_ETAB = 8;   /* an election page's tab ("2024 general election > Map") ranks like an office tab */
  var T_GTAB = 9;   /* a government page's tab ("City of South Bend > Money"; added 2026-11-16) ranks like an office tab */
  var T_PTAB = 10;  /* a person page's tab ("James Mueller > Money"; added 2026-11-16) ranks like an office tab */
  function norm(s) {
    s = String(s || "").toLowerCase();
    if (s.normalize) s = s.normalize("NFD").replace(/[\u0300-\u036f]/g, "");   /* combining marks, escaped: the file stays ASCII */
    return s;
  }
  function words(s) { return norm(s).split(/[^a-z0-9]+/).filter(function (w) { return w; }); }
  function prepare(d) {
    var types = d.types || [];
    return (d.items || []).map(function (it, i) {
      var label = String(it[1]);
      var tab = it[0] === T_TAB || it[0] === T_ETAB || it[0] === T_GTAB || it[0] === T_PTAB;
      /* a tab's own words: its name after the office ("Money") and its keywords */
      var tabName = tab && label.lastIndexOf(" \u203a ") >= 0 ? label.slice(label.lastIndexOf(" \u203a ") + 3) : "";
      return { kind: it[0], type: types[it[0]] || "", label: label, sub: it[2] || "", href: it[3], tag: it[4] || "",
               n: norm(label), alt: norm(label.replace(/^(City|Town) of /, "").replace(/ Township$/, "")),
               lw: words(label), sw: words(it[2]), kw: words(it[5] || ""), tw: words(tabName + " " + (it[5] || "")),
               tab: tab, i: i };
    });
  }
  function prefixIn(tok, ws) {
    for (var i = 0; i < ws.length; i++) if (ws[i].indexOf(tok) === 0) return true;
    /* simple plural: "schools" also finds "school" */
    if (tok.length > 3 && tok.charAt(tok.length - 1) === "s") return prefixIn(tok.slice(0, -1), ws);
    return false;
  }
  function score(it, q, toks) {
    var inLabel = 0, strong = 0, inTab = 0;
    for (var i = 0; i < toks.length; i++) {
      var l = prefixIn(toks[i], it.lw);
      var k = it.kw.length ? prefixIn(toks[i], it.kw) : false;
      if (!l && !k && !prefixIn(toks[i], it.sw)) return -1;
      if (l) inLabel++;
      if (l || k) strong++;
      if (it.tab && prefixIn(toks[i], it.tw)) inTab++;
    }
    var s;
    if (it.n === q || it.alt === q) s = 100;
    else if (it.n.indexOf(q) === 0 || it.alt.indexOf(q) === 0) s = 80;
    else if (inLabel === toks.length) s = 60;
    else if (strong === toks.length) s = 55;
    else s = 30 + inLabel;
    if (it.tab && !inTab) s -= 25;
    return s;
  }
  /* items (prepare output) matching the query, best first: [[score, item], ...] */
  function rank(items, query) {
    var q = norm(query).replace(/\s+/g, " ").trim();
    if (q.replace(/[^a-z0-9]/g, "").length < 2) return [];
    var toks = words(q);
    var scored = [];
    items.forEach(function (it) {
      var s = score(it, q, toks);
      if (s >= 0) scored.push([s, it]);
    });
    scored.sort(function (a, b) {
      if (b[0] !== a[0]) return b[0] - a[0];
      if (a[1].kind !== b[1].kind) return KIND_RANK[a[1].kind] - KIND_RANK[b[1].kind];
      return a[1].i - b[1].i;
    });
    return scored;
  }
  return { prepare: prepare, rank: rank, norm: norm };
})();
if (typeof window !== "undefined") window.civicSearchCore = civicSearchCore;
/* The combobox. One copy per search box: the header's (civic/shell.py _search) and, when the page has one, the home
   page's large box (pages/landing.py, ids "home-search-*"; added 2026-11-18, phase 6 home). Both share one load of
   the index. */
(function () {
  "use strict";
  var doc = document;
  var site = doc.getElementById("site");
  var ROOT = (site && site.getAttribute("data-root")) || "./";
  var MAX = 10;
  var core = civicSearchCore;
  /* the index, loaded once for every box on the page; each box asks to be told when it arrives */
  var shared = { items: null, loading: false, failed: false, waiting: [] };

  function loadIndex(url, done) {
    if (shared.items || shared.failed) { done(); return; }
    shared.waiting.push(done);
    if (shared.loading) return;
    shared.loading = true;
    function finish() {
      shared.loading = false;
      var w = shared.waiting;
      shared.waiting = [];
      w.forEach(function (f) { f(); });
    }
    if (!window.fetch || !url) { shared.failed = true; finish(); return; }
    window.fetch(url).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    }).then(function (d) {
      shared.items = core.prepare(d);
      finish();
    }).catch(function () {
      shared.failed = true;
      finish();
    });
  }

  /* ids: {form, input, pop, list, status, opt (option id prefix), nojs (selector of the no-JS link, optional)} */
  function bind(ids) {
    var form = doc.getElementById(ids.form);
    var input = doc.getElementById(ids.input);
    var pop = doc.getElementById(ids.pop);
    var list = doc.getElementById(ids.list);
    var status = doc.getElementById(ids.status);
    var nojs = ids.nojs ? doc.querySelector(ids.nojs) : null;
    if (!form || !input || !pop || !list || !status) return;

    form.hidden = false;
    if (nojs) nojs.hidden = true;

    var results = [], active = -1;

    function norm(s) { return core.norm(s); }

    function load() {
      loadIndex(form.getAttribute("data-index"), function () { if (input.value) search(); });
    }

    function option(it, i) {
      var li = doc.createElement("li");
      li.id = ids.opt + i;
      li.className = "search-opt";
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", "false");
      var main = doc.createElement("span");
      main.className = "search-opt-main";
      var name = doc.createElement("span");
      name.className = "search-opt-label";
      name.textContent = it.label + (it.tag ? " " + it.tag : "");
      main.appendChild(name);
      var kind = doc.createElement("span");
      kind.className = "search-opt-kind";
      kind.textContent = it.type;
      main.appendChild(kind);
      li.appendChild(main);
      if (it.sub && it.sub !== "Page") {
        var sub = doc.createElement("span");
        sub.className = "search-opt-sub";
        sub.textContent = it.sub;
        li.appendChild(sub);
      }
      li.addEventListener("mousedown", function (ev) { ev.preventDefault(); });
      li.addEventListener("click", function () { go(i); });
      return li;
    }

    function open(isOpen) {
      pop.hidden = !isOpen;
      input.setAttribute("aria-expanded", isOpen && results.length ? "true" : "false");
      if (!isOpen) setActive(-1);
    }

    function setActive(i) {
      active = i;
      Array.prototype.forEach.call(list.children, function (li, k) {
        var on = k === i;
        li.setAttribute("aria-selected", on ? "true" : "false");
        li.classList.toggle("is-active", on);
        if (on && li.scrollIntoView) li.scrollIntoView({ block: "nearest" });
      });
      if (i >= 0) input.setAttribute("aria-activedescendant", ids.opt + i);
      else input.removeAttribute("aria-activedescendant");
    }

    function search() {
      var q = norm(input.value).replace(/\s+/g, " ").trim();
      while (list.firstChild) list.removeChild(list.firstChild);
      results = [];
      if (q.replace(/[^a-z0-9]/g, "").length < 2) { open(false); status.textContent = ""; return; }
      if (!shared.items) {
        status.textContent = shared.failed ? "Search could not load here. Use Browse everything below." : "Loading the search list...";
        open(true);
        load();
        return;
      }
      var scored = core.rank(shared.items, q);
      results = scored.slice(0, MAX).map(function (x) { return x[1]; });
      results.forEach(function (it, i) { list.appendChild(option(it, i)); });
      var more = scored.length > MAX ? " Showing the first " + MAX + "; type more to narrow it." : "";
      status.textContent = scored.length
        ? scored.length + (scored.length === 1 ? " match." : " matches.") + more
        : "No matches. Try another spelling, or use Browse everything below.";
      open(true);
      setActive(-1);
    }

    function go(i) {
      var it = results[i];
      if (!it) return;
      open(false);
      window.location.href = ROOT + it.href;
    }

    input.addEventListener("focus", load);
    input.addEventListener("input", search);
    input.addEventListener("keydown", function (ev) {
      var n = results.length;
      if (ev.key === "ArrowDown") {
        ev.preventDefault();
        if (pop.hidden) search();
        if (n) setActive(active < n - 1 ? active + 1 : 0);
      } else if (ev.key === "ArrowUp") {
        ev.preventDefault();
        if (n) setActive(active > 0 ? active - 1 : n - 1);
      } else if (ev.key === "Enter") {
        ev.preventDefault();
        if (active >= 0) go(active);
        else if (n) go(0);
      } else if (ev.key === "Escape") {
        if (!pop.hidden) { ev.preventDefault(); open(false); }
        else if (input.value) { ev.preventDefault(); input.value = ""; status.textContent = ""; }
      } else if (ev.key === "Tab") {
        open(false);
      }
    });
    form.addEventListener("submit", function (ev) { ev.preventDefault(); });
    form.addEventListener("focusout", function (ev) {
      if (!ev.relatedTarget || !form.contains(ev.relatedTarget)) open(false);
    });
    doc.addEventListener("click", function (ev) {
      if (!pop.hidden && !form.contains(ev.target)) open(false);
    });
  }

  bind({ form: "search-form", input: "site-search-input", pop: "site-search-pop", list: "site-search-list",
         status: "site-search-status", opt: "site-search-opt-", nojs: ".site-search .search-nojs" });
  bind({ form: "home-search-form", input: "home-search-input", pop: "home-search-pop", list: "home-search-list",
         status: "home-search-status", opt: "home-search-opt-", nojs: ".home-search .search-nojs" });
})();
