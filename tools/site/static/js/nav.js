/* nav.js: the primary nav's <details> menus (civic/shell.py _nav: Topics = #ref-menu, Learn = #learn-menu).
   Without JavaScript they are plain <details>: they open and close natively and every link works. This adds:
   aria-expanded on each summary kept in step with the menu, one menu open at a time, Escape closes the open menu
   and puts focus back on its summary, a click or focus outside closes it. ASCII only. */
(function () {
  "use strict";
  var doc = document;
  var menus = Array.prototype.slice.call(doc.querySelectorAll("details[data-nav-menu]"));
  if (!menus.length) return;

  function sync(d) {
    var s = d.querySelector("summary");
    if (s) s.setAttribute("aria-expanded", d.open ? "true" : "false");
  }
  menus.forEach(function (d) {
    sync(d);
    d.addEventListener("toggle", function () {
      sync(d);
      if (d.open) menus.forEach(function (o) { if (o !== d && o.open) o.open = false; });
    });
  });

  function openMenu() {
    for (var i = 0; i < menus.length; i++) if (menus[i].open) return menus[i];
    return null;
  }
  doc.addEventListener("keydown", function (ev) {
    if (ev.key !== "Escape") return;
    var d = openMenu();
    if (!d) return;
    d.open = false;
    var s = d.querySelector("summary");
    if (s) s.focus();
  });
  doc.addEventListener("click", function (ev) {
    var d = openMenu();
    if (d && !d.contains(ev.target)) d.open = false;
  });
  /* Tab out of an open menu (past its last link, or Shift+Tab before its summary) closes it */
  doc.addEventListener("focusin", function (ev) {
    var d = openMenu();
    if (d && !d.contains(ev.target)) d.open = false;
  });
})();
