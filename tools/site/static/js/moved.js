/* moved.js: forwards an old link to an id that moved to another page.
   data/index.html ships #moved-anchors (pages/data_sets.py moved_anchor_map): the long data page was split into
   one page per dataset, so #ds-results-preview, #pull-gateway or #src-RES-001 now live elsewhere.
   about/index.html: the sources index moved to about/sources/, so #src-... and #sources-<kind> go there.
   Runs only when the id is not on the page. ASCII only. */
(function () {
  "use strict";
  var doc = document;
  var site = doc.getElementById("site");
  var page = site ? site.getAttribute("data-page") : "";
  var map = null;
  var node = doc.getElementById("moved-anchors");
  if (node) { try { map = JSON.parse(node.textContent); } catch (e) { map = null; } }
  if (page !== "about/index.html" && !(page === "data/index.html" && map)) return;

  function go() {
    var id = (window.location.hash || "").slice(1);
    if (!id) return;
    try { id = decodeURIComponent(id); } catch (e) { /* keep raw */ }
    if (doc.getElementById(id)) return;
    var dest = "";
    if (page === "about/index.html") {
      if (/^(src-|sources-)/.test(id)) dest = "sources/index.html";
    } else if (map) {
      dest = map.a[id] || (id.indexOf("src-") === 0 ? map.src[id.slice(4)] : "") || "";
    }
    if (dest) window.location.replace(dest + "#" + id);
  }
  go();
  window.addEventListener("hashchange", go);
})();
