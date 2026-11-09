/* Community and History pages: turning-points filter (history/index.html).
   The timeline is complete without JS; this only hides other categories on request.
   #political / #economic (and learning-path stops that land on them) pre-select the filter. */
(function () {
  "use strict";
  var doc = document;
  var list = doc.getElementById("tp-list");
  if (!list) return;
  var items = Array.prototype.slice.call(list.querySelectorAll(".tp-item"));
  var buttons = Array.prototype.slice.call(doc.querySelectorAll("[data-tp-filter]"));

  function apply(cat) {
    items.forEach(function (li) {
      var show = cat === "all" || li.getAttribute("data-cat") === cat;
      if (show) li.classList.remove("is-hidden"); else li.classList.add("is-hidden");
    });
    buttons.forEach(function (b) {
      if (b.hasAttribute("aria-pressed")) b.setAttribute("aria-pressed", b.getAttribute("data-tp-filter") === cat ? "true" : "false");
    });
  }

  buttons.forEach(function (b) {
    b.addEventListener("click", function () {
      var cat = b.getAttribute("data-tp-filter");
      apply(cat);
      if (!b.hasAttribute("aria-pressed")) {
        var pressed = doc.getElementById("tp-" + cat);
        if (pressed) pressed.focus();
      }
    });
  });

  function anchorFromHash() {
    var hash = window.location.hash || "";
    var m = /^#path-([a-z0-9-]+)-(\d+)$/.exec(hash);
    if (m) {
      var el = doc.getElementById("paths-data");
      var data = null;
      try { data = el ? JSON.parse(el.textContent) : null; } catch (e) { data = null; }
      if (!data) return "";
      var stopAnchor = "";
      data.paths.forEach(function (p) {
        var n = parseInt(m[2], 10);
        if (p.id === m[1] && n >= 1 && n <= p.stops.length) stopAnchor = p.stops[n - 1].anchor;
      });
      return stopAnchor;
    }
    return hash.replace(/^#/, "");
  }

  function fromHash() {
    var a = anchorFromHash();
    if (a === "political" || a === "economic") apply(a);
  }
  window.addEventListener("hashchange", fromHash);
  fromHash();
})();
