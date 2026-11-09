/* sourcesearch.js: search box and kind filter for about/sources/. The full list is in the HTML; this only
   hides entries (li.hidden) and groups, shows the bar, and keeps a "N of M sources shown" count.
   While a filter is active the groups with matches are opened (folds.js closes them by default);
   clearing the filter puts every group back as it was. ASCII only. */
(function () {
  "use strict";
  var doc = document;
  var bar = doc.querySelector("[data-src-search]");
  if (!bar) return;
  var q = bar.querySelector("[data-src-q]");
  var kindSel = bar.querySelector("[data-src-kind]");
  var reset = bar.querySelector("[data-src-reset]");
  var count = bar.querySelector("[data-src-count]");
  var empty = doc.querySelector("[data-src-empty]");
  var groups = Array.prototype.slice.call(doc.querySelectorAll(".src-group[data-kind]"));
  var entries = [];
  groups.forEach(function (g) {
    Array.prototype.forEach.call(g.querySelectorAll("ul.source-index > li"), function (li) {
      entries.push({ li: li, group: g, text: (li.textContent || "").replace(/\s+/g, " ").toLowerCase() });
    });
  });
  var total = entries.length;
  var saved = null;

  function apply() {
    var words = q.value.toLowerCase().split(/\s+/).filter(Boolean);
    var kind = kindSel.value;
    var active = words.length > 0 || kind !== "";
    var per = new Map();
    var shown = 0;
    entries.forEach(function (e) {
      var ok = !kind || e.group.getAttribute("data-kind") === kind;
      for (var i = 0; ok && i < words.length; i++) if (e.text.indexOf(words[i]) < 0) ok = false;
      e.li.hidden = !ok;
      if (ok) { shown++; per.set(e.group, (per.get(e.group) || 0) + 1); }
    });
    if (active && !saved) {
      saved = groups.map(function (g) { var d = g.querySelector("details"); return d && d.open; });
    }
    groups.forEach(function (g, i) {
      var n = per.get(g) || 0;
      var tot = g.querySelectorAll("ul.source-index > li").length;
      g.hidden = active && n === 0;
      var d = g.querySelector("details");
      if (d && active) d.open = n > 0;
      var c = g.querySelector("[data-src-group-count]");
      if (c) c.textContent = active ? "(" + n + " of " + tot + ")" : "(" + tot + ")";
    });
    if (!active && saved) {
      groups.forEach(function (g, i) { var d = g.querySelector("details"); if (d) d.open = !!saved[i]; });
      saved = null;
    }
    count.textContent = shown + " of " + total + " sources shown.";
    if (empty) empty.hidden = shown !== 0;
  }

  /* a link or address to an entry the filter has hidden clears the filter so the entry can be seen */
  function unhideTarget() {
    var id = (window.location.hash || "").slice(1);
    if (!id) return;
    try { id = decodeURIComponent(id); } catch (e) { /* raw */ }
    var t = doc.getElementById(id);
    for (var n = t; n && n !== doc.body; n = n.parentElement) {
      if (n.hidden) { q.value = ""; kindSel.selectedIndex = 0; apply(); return; }
    }
  }
  doc.addEventListener("click", function (ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest("a[href]") : null;
    if (!a || !a.hash) return;
    var id = a.hash.slice(1), t = doc.getElementById(id);
    for (var n = t; n && n !== doc.body; n = n.parentElement) {
      if (n.hidden) { q.value = ""; kindSel.selectedIndex = 0; apply(); return; }
    }
  });
  window.addEventListener("hashchange", unhideTarget);

  q.addEventListener("input", apply);
  q.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && q.value) { q.value = ""; apply(); } });
  kindSel.addEventListener("change", apply);
  reset.addEventListener("click", function () { q.value = ""; kindSel.selectedIndex = 0; apply(); q.focus(); });
  bar.hidden = false;
  apply();
})();
