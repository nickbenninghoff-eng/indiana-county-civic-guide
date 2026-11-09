/* Campaign-money map on money/campaigns/ (civic/campaign_map.py): the race-type row above the map, and the matching
   filter of the "Every area" list. static/js/map.js owns the layers, the panel and the layer tabs; this script only
   shows the tabs of the chosen race type (each type has one or more layers: its governments, then its district maps)
   and presses one. Without JavaScript the map shows its default layer, every shape is a link, and the list below the
   map shows every area. ASCII only; text is inserted with textContent. */
(function () {
  "use strict";
  var doc = document;
  var root = doc.querySelector(".cmap.cf-map");
  if (!root) return;
  var row = root.querySelector(".cf-types");
  var tabs = root.querySelector(".cmap-tabs");
  var head = doc.getElementById("cf-filter-h");
  if (!row || !tabs) return;
  var typeBtns = Array.prototype.slice.call(row.querySelectorAll(".cf-type"));
  var tabBtns = Array.prototype.slice.call(tabs.querySelectorAll(".cmap-tab"));
  var groups = Array.prototype.slice.call(doc.querySelectorAll("#areas .cf-group[data-cf-type]"));
  var tools = doc.getElementById("cf-list-tools");
  var state = doc.getElementById("cf-list-state");
  var allBtn = doc.getElementById("cf-list-all");
  var lastLayer = {};
  // one race type only (a township's page): no row to choose from, the office tabs are enough
  row.hidden = typeBtns.length < 2;
  if (head) head.hidden = typeBtns.length < 2;

  function typeOf(layer) {
    for (var i = 0; i < tabBtns.length; i++) {
      if (tabBtns[i].getAttribute("data-layer") === layer) return tabBtns[i].getAttribute("data-cf-type");
    }
    return null;
  }
  function labelOf(type) {
    for (var i = 0; i < typeBtns.length; i++) {
      if (typeBtns[i].getAttribute("data-cf-type") === type) return typeBtns[i].textContent;
    }
    return type;
  }
  function showTabs(type) {
    var n = 0;
    tabBtns.forEach(function (b) {
      var on = b.getAttribute("data-cf-type") === type;
      b.hidden = !on;
      if (on) n += 1;
    });
    tabs.classList.toggle("cf-tabs-one", n < 2);
    typeBtns.forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-cf-type") === type ? "true" : "false");
    });
  }
  function filterList(type) {
    if (!groups.length) return;
    groups.forEach(function (g) { g.hidden = type !== null && g.getAttribute("data-cf-type") !== type; });
    if (tools) tools.hidden = type === null;
    if (state) state.textContent = type === null ? "" : "Showing " + labelOf(type) + " only.";
  }
  // map.js announces every layer change (including its first one) with a cmap-layer event on the root
  root.addEventListener("cmap-layer", function (ev) {
    var t = typeOf(ev.detail);
    if (!t) return;
    lastLayer[t] = ev.detail;
    showTabs(t);
    // data-cf-auto-one (the county's own page, added 2026-11-09): a layer with a single shape (one countywide
    // office) shows its figures in the panel at once, through map.js's cmap-select.
    if (root.getAttribute("data-cf-auto-one") !== "on") return;
    var g = null;
    Array.prototype.forEach.call(root.querySelectorAll(".cmap-layer[data-layer]"), function (x) {
      if (x.getAttribute("data-layer") === ev.detail) g = x;
    });
    var shapes = g ? g.querySelectorAll(".cmap-a[data-uid]") : [];
    if (shapes.length === 1) {
      root.dispatchEvent(new CustomEvent("cmap-select", { detail: { uid: shapes[0].getAttribute("data-uid") } }));
    }
  });
  row.addEventListener("click", function (ev) {
    var b = ev.target.closest && ev.target.closest(".cf-type");
    if (!b) return;
    var t = b.getAttribute("data-cf-type");
    var want = lastLayer[t], btn = null;
    tabBtns.forEach(function (x) {
      if (x.getAttribute("data-cf-type") !== t) return;
      if (!btn || x.getAttribute("data-layer") === want) btn = x;
    });
    if (btn) btn.click();
    filterList(t);
  });
  if (allBtn) allBtn.addEventListener("click", function () { filterList(null); });
})();
