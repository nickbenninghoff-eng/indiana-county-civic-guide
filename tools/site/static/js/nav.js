/* nav.js: the header's <details> menus (civic/shell.py _nav: one dropdown per nav item, Governments = #ref-menu,
   Learn = #learn-menu; _display: #display-menu) and, below 1100 px, the Menu button (#menu-btn).
   Without JavaScript the menus are plain <details>: they open and close natively and every link works; the Menu
   button is a link to #primary-nav, which CSS :target opens. This adds: aria-expanded on each summary kept in step
   with the menu, one menu open at a time, Escape closes the open menu and puts focus back on its summary, a click or
   focus outside closes it; the Menu button becomes a toggle (aria-expanded, Escape closes it). ASCII only. */
(function () {
  "use strict";
  var doc = document;

  /* ---- the Menu button (phase 6 step 1) */
  var head = doc.getElementById("site-head");
  var btn = doc.getElementById("menu-btn");
  var panel = doc.getElementById("primary-nav");
  if (head && btn && panel) {
    btn.setAttribute("role", "button");
    btn.setAttribute("aria-expanded", "false");
    var setOpen = function (on) {
      head.classList.toggle("menu-open", on);
      btn.setAttribute("aria-expanded", on ? "true" : "false");
    };
    btn.addEventListener("click", function (ev) {
      ev.preventDefault();
      setOpen(!head.classList.contains("menu-open"));
    });
    btn.addEventListener("keydown", function (ev) {
      /* a link-as-button answers Space as well as Enter */
      if (ev.key === " " || ev.key === "Spacebar") { ev.preventDefault(); setOpen(!head.classList.contains("menu-open")); }
    });
    doc.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && head.classList.contains("menu-open") && !head.querySelector(".head-menu details[open]")) {
        setOpen(false);
        btn.focus();
      }
    });
    doc.addEventListener("click", function (ev) {
      if (head.classList.contains("menu-open") && !head.contains(ev.target)) setOpen(false);
    });
  }

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
