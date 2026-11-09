/* Indicator maps on the community pages (pages/community_history.py indicator_map_section): the "Shade by" picker.
   The shade of every area for every indicator is computed at build time (#cmap-shade: {indicator: {unit id: 1..5,
   0 = not shaded}}); this script swaps the area classes and the legend, and tells static/js/map.js which panel row is
   the shaded one (data-lead). Without JavaScript the map shows the first indicator and the page's tables have every
   figure. */
(function () {
  var doc = document;
  var root = doc.querySelector(".cmap.cmap-indmap");
  if (!root) return;
  var node = doc.getElementById("cmap-shade");
  var sel = root.querySelector(".cmap-ind-select");
  if (!node || !sel) return;
  var shade = {};
  try { shade = JSON.parse(node.textContent); } catch (e) { return; }
  var wrap = root.querySelector(".cmap-ind");
  if (wrap) wrap.hidden = false;

  function each(list, fn) { Array.prototype.forEach.call(list, fn); }
  function cls(n) { return n ? "cmap-mm-" + n : "cmap-mm-none"; }

  function apply(ind) {
    var m = shade[ind] || {};
    each(root.querySelectorAll(".cmap-a[data-uid]"), function (a) {
      var c = cls(m[a.getAttribute("data-uid")]);
      var p = a.querySelector("path");
      if (p) p.setAttribute("class", "cmap-s cmap-mm " + c);
      var dot = a.querySelector("circle");
      if (dot) dot.setAttribute("class", "cmap-dot cmap-mm-dot " + c);
    });
    each(root.querySelectorAll(".cmap-mlegend[data-ind]"), function (lg) {
      lg.hidden = lg.getAttribute("data-ind") !== ind;
    });
    root.setAttribute("data-lead", ind);
    root.dispatchEvent(new CustomEvent("cmap-refresh"));
  }
  sel.addEventListener("change", function () { apply(sel.value); });
  if (sel.value && sel.value !== root.getAttribute("data-lead")) apply(sel.value);
})();
