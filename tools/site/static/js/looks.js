/* Look switcher (civic/shell.py look_switch, static/css/looks.css).
   The inline script in <head> has already set html[data-look] from storage before first paint.
   This wires every [data-look-set] button (header and About page), keeps aria-pressed in sync,
   remembers the choice per device, and follows changes made in another tab. ASCII only. */
(function () {
  "use strict";
  var doc = document;
  var root = doc.documentElement;
  var KEY = "civic-look";
  var LOOKS = ["ballot", "line", "wayfinding"];

  function valid(v) { return LOOKS.indexOf(v) >= 0 ? v : "ballot"; }
  function save(v) {
    try { window.localStorage.setItem(KEY, v); } catch (e) { /* storage unavailable: choice lasts for this page only */ }
  }
  function sync(cur) {
    Array.prototype.forEach.call(doc.querySelectorAll("[data-look-set]"), function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-look-set") === cur ? "true" : "false");
    });
  }
  function apply(v) {
    var cur = valid(v);
    root.setAttribute("data-look", cur);
    sync(cur);
    return cur;
  }

  apply(root.getAttribute("data-look"));

  doc.addEventListener("click", function (ev) {
    var b = ev.target && ev.target.closest ? ev.target.closest("[data-look-set]") : null;
    if (!b) return;
    save(apply(b.getAttribute("data-look-set")));
  });

  window.addEventListener("storage", function (ev) {
    if (ev.key === KEY) apply(ev.newValue);
  });
})();
