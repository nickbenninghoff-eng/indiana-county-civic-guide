/* folds.js: the collapsible "Gaps" and "Sources" sections at the end of every page, and any other
   <details data-fold> (for example the source groups on about/sources/).
   The HTML ships these open so that with JavaScript off every row is on the page and every citation
   link works. This script closes them on load, then opens a fold whenever something inside it is the
   target of a link, of the address bar (#src-ABC) or of back/forward, and for printing. ASCII only. */
(function () {
  "use strict";
  var doc = document;

  function folds() { return Array.prototype.slice.call(doc.querySelectorAll("details[data-fold]")); }

  function targetOf(hash) {
    if (!hash || hash.length < 2) return null;
    var id = hash.slice(1);
    try { id = decodeURIComponent(id); } catch (e) { /* keep the raw id */ }
    return doc.getElementById(id);
  }

  /* Open every <details> around the target; a fold's own section (#gaps, #sources) opens its fold.
     Returns true if anything changed. */
  function reveal(target) {
    var changed = false;
    if (!target) return changed;
    var n;
    for (n = target; n && n !== doc.body; n = n.parentElement) {
      if (n.tagName === "DETAILS" && !n.open) { n.open = true; changed = true; }
    }
    if (target.classList && target.classList.contains("fold")) {
      var own = target.querySelector(":scope > details[data-fold]");
      if (own && !own.open) { own.open = true; changed = true; }
    }
    return changed;
  }

  /* 1. start collapsed, unless the page was opened on something inside a fold */
  var landing = targetOf(window.location.hash);
  folds().forEach(function (d) {
    var holdsTarget = landing && (d.contains(landing) || (landing.contains && landing.contains(d) && landing.classList.contains("fold")));
    if (!holdsTarget) d.open = false;
  });
  if (landing) {
    reveal(landing);
    /* closing the other folds moved the page: put the target back on screen */
    if (landing.scrollIntoView) landing.scrollIntoView();
  }

  /* 2. a link to something inside a closed fold (citation superscripts, the table of contents, the
     "Sources" link in a footer) opens it before the browser scrolls */
  doc.addEventListener("click", function (ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest("a[href]") : null;
    if (!a || !a.hash || a.hash.length < 2) return;
    if (a.pathname !== window.location.pathname || a.host !== window.location.host) return;
    reveal(targetOf(a.hash));
  });

  /* 3. address bar / back / forward */
  window.addEventListener("hashchange", function () {
    var t = targetOf(window.location.hash);
    if (reveal(t) && t.scrollIntoView) t.scrollIntoView();
  });

  /* 4. printing shows everything */
  var reopened = [];
  window.addEventListener("beforeprint", function () {
    reopened = folds().filter(function (d) { return !d.open; });
    reopened.forEach(function (d) { d.open = true; });
  });
  window.addEventListener("afterprint", function () {
    reopened.forEach(function (d) { d.open = false; });
    reopened = [];
  });
})();
