/* Header search (civic/shell.py _search, index built by civic/search.py into assets/search-index.json).
   ARIA 1.2 combobox: the input owns a listbox; arrows move the active option (aria-activedescendant),
   Enter opens it, Escape closes the list (a second Escape clears the box). Matching is case- and
   accent-insensitive: every typed word must be the start of a word in the name or its context line.
   Ranking: exact name, then name starts with the text, then all words in the name, then context matches;
   ties by kind (place, office, officeholder, person, page, section) and then alphabetically. Party tags
   are display text only, never matched or ranked. Without JS the form stays hidden and the
   "Browse everything" link shows. ASCII only; text inserted with textContent only. */
(function () {
  "use strict";
  var doc = document;
  var form = doc.getElementById("search-form");
  var input = doc.getElementById("site-search-input");
  var pop = doc.getElementById("site-search-pop");
  var list = doc.getElementById("site-search-list");
  var status = doc.getElementById("site-search-status");
  var nojs = doc.querySelector(".site-search .search-nojs");
  var site = doc.getElementById("site");
  if (!form || !input || !pop || !list || !status) return;
  var ROOT = (site && site.getAttribute("data-root")) || "./";
  var MAX = 10;
  var KIND_ORDER = [0, 1, 2, 3, 4, 5];

  form.hidden = false;
  if (nojs) nojs.hidden = true;

  var items = null, loading = false, failed = false, results = [], active = -1;

  function norm(s) {
    s = String(s || "").toLowerCase();
    if (s.normalize) s = s.normalize("NFD").replace(/[\u0300-\u036f]/g, "");   /* combining marks, escaped: the file stays ASCII */
    return s;
  }
  function words(s) { return norm(s).split(/[^a-z0-9]+/).filter(function (w) { return w; }); }

  function load() {
    if (items || loading) return;
    loading = true;
    var url = form.getAttribute("data-index");
    if (!window.fetch || !url) { failed = true; loading = false; return; }
    window.fetch(url).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    }).then(function (d) {
      var types = d.types || [];
      items = (d.items || []).map(function (it) {
        return { kind: it[0], type: types[it[0]] || "", label: it[1], sub: it[2] || "", href: it[3], tag: it[4] || "",
                 n: norm(it[1]), alt: norm(String(it[1]).replace(/^(City|Town) of /, "").replace(/ Township$/, "")),
                 lw: words(it[1]), sw: words(it[2]) };
      });
      loading = false;
      if (input.value) search();
    }).catch(function () {
      failed = true;
      loading = false;
      if (input.value) search();
    });
  }

  function prefixIn(tok, ws) {
    for (var i = 0; i < ws.length; i++) if (ws[i].indexOf(tok) === 0) return true;
    /* simple plural: "schools" also finds "school" */
    if (tok.length > 3 && tok.charAt(tok.length - 1) === "s") return prefixIn(tok.slice(0, -1), ws);
    return false;
  }

  function score(it, q, toks) {
    var inLabel = 0;
    for (var i = 0; i < toks.length; i++) {
      var l = prefixIn(toks[i], it.lw);
      if (!l && !prefixIn(toks[i], it.sw)) return -1;
      if (l) inLabel++;
    }
    if (it.n === q || it.alt === q) return 100;
    if (it.n.indexOf(q) === 0 || it.alt.indexOf(q) === 0) return 80;
    if (inLabel === toks.length) return 60;
    return 30 + inLabel;
  }

  function option(it, i) {
    var li = doc.createElement("li");
    li.id = "site-search-opt-" + i;
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
    if (i >= 0) input.setAttribute("aria-activedescendant", "site-search-opt-" + i);
    else input.removeAttribute("aria-activedescendant");
  }

  function search() {
    var q = norm(input.value).replace(/\s+/g, " ").trim();
    while (list.firstChild) list.removeChild(list.firstChild);
    results = [];
    if (q.replace(/[^a-z0-9]/g, "").length < 2) { open(false); status.textContent = ""; return; }
    if (!items) {
      status.textContent = failed ? "Search could not load here. Use Browse everything below." : "Loading the search list...";
      open(true);
      load();
      return;
    }
    var toks = words(q);
    var scored = [];
    items.forEach(function (it) {
      var s = score(it, q, toks);
      if (s >= 0) scored.push([s, it]);
    });
    scored.sort(function (a, b) {
      if (b[0] !== a[0]) return b[0] - a[0];
      if (a[1].kind !== b[1].kind) return KIND_ORDER[a[1].kind] - KIND_ORDER[b[1].kind];
      return a[1].n < b[1].n ? -1 : a[1].n > b[1].n ? 1 : 0;
    });
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
})();
