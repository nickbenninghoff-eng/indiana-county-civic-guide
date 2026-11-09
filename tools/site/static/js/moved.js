/* moved.js: forwards an old link to an id that moved to another page.
   data/index.html ships #moved-anchors (pages/data_sets.py moved_anchor_map): the long data page was split into
   one page per dataset, so #ds-results-preview, #pull-gateway or #src-RES-001 now live elsewhere.
   about/index.html: the sources index moved to about/sources/, so #src-... and #sources-<kind> go there.
   Any other page may ship #moved-anchors too (added 2026-11-09, Wave B batch 2: elections/landscape/ was split into
   margins, turnout, officeholders and the calendar; elections/results/ lost its turnout table):
   {"a": {old id: "relative/path/index.html" or "relative/path/index.html#new-id"}}. A destination without "#" keeps
   the old id. Paths are relative to the page that ships the map.
   A learning-path stop (#path-<id>-<n>, static/app.js) whose page is no longer this one goes to the stop's page, so
   an old path link keeps working after sitemap.PATHS is repointed.
   A map may also carry {"p": {id prefix: "relative/path/index.html"}} (added 2026-11-09, Wave D batch 6: the
   elections explainer moved from elections/index.html to elections/how-it-works/, so every old #src-<id> citation goes
   there with the same id). An exact "a" entry wins over a prefix.
   Runs only when the id is not on the page. ASCII only. */
(function () {
  "use strict";
  var doc = document;
  var site = doc.getElementById("site");
  var page = site ? site.getAttribute("data-page") : "";
  var root = (site && site.getAttribute("data-root")) || "./";
  var map = null;
  var node = doc.getElementById("moved-anchors");
  if (node) { try { map = JSON.parse(node.textContent); } catch (e) { map = null; } }
  var paths = null;
  var pnode = doc.getElementById("paths-data");
  if (pnode) { try { paths = JSON.parse(pnode.textContent); } catch (e) { paths = null; } }

  function pathStop(id) {
    var m = /^path-([a-z0-9-]+)-(\d+)$/.exec(id);
    if (!m || !paths || !paths.paths) return "";
    var stop = null;
    paths.paths.forEach(function (p) {
      var n = parseInt(m[2], 10);
      if (p.id === m[1] && n >= 1 && n <= p.stops.length) stop = p.stops[n - 1];
    });
    return stop && stop.page !== page ? root + stop.page : "";
  }

  function go() {
    var id = (window.location.hash || "").slice(1);
    if (!id) return;
    try { id = decodeURIComponent(id); } catch (e) { /* keep raw */ }
    var stopPage = pathStop(id);
    if (stopPage) { window.location.replace(stopPage + "#" + id); return; }
    if (doc.getElementById(id)) return;
    var dest = "";
    if (page === "about/index.html") {
      if (/^(src-|sources-)/.test(id)) dest = "sources/index.html";
    } else if (map && map.a) {
      dest = (Object.prototype.hasOwnProperty.call(map.a, id) ? map.a[id] : "") ||
             (page === "data/index.html" && map.src && id.indexOf("src-") === 0 ? map.src[id.slice(4)] : "") || "";
      if (!dest && map.p) {
        Object.keys(map.p).forEach(function (pre) {
          if (!dest && pre && id.indexOf(pre) === 0) dest = map.p[pre];
        });
      }
    }
    if (dest) window.location.replace(dest.indexOf("#") >= 0 ? dest : dest + "#" + id);
  }
  go();
  window.addEventListener("hashchange", go);
})();
