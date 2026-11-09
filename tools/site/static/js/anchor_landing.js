/* anchor_landing.js: lands a fresh load of an address with a #fragment on its target, after the web fonts arrive.
   One site-wide script (it replaces the page-specific copy that lived in margins.js). The browser scrolls to #id as
   soon as the page parses, but the web fonts load afterwards, the text above the target rewraps, and on a long page
   the target ends up a few hundred pixels off (for example elections/how-it-works/#vacancies at 214 px instead of 64).
   Once the page has loaded, again when the fonts are ready, and while the layout is still settling (3 s), this puts
   the target back where the browser puts it for an in-page jump: html scroll-padding-top plus the target's own
   scroll-margin-top, so it clears the sticky nav and the On this page bar (static/js/onpage.js).
   It does nothing when:
     - the id is not on the page (static/js/moved.js forwards an old id to the page that now holds it, and the
       destination page lands it with this script),
     - the target sits in a closed fold (static/js/folds.js opens the fold that holds the target at start-up, before
       this runs; a hidden target is left alone),
     - the page was reloaded or reached with Back/Forward (the browser restores the reader's own position),
     - the reader has scrolled, pressed a key, touched or clicked since the page opened.
   ASCII only. */
(function () {
  "use strict";
  var doc = document;
  var root = doc.documentElement;
  var hash = window.location.hash || "";
  if (hash.length < 2) return;

  try {
    var nav = window.performance && window.performance.getEntriesByType && window.performance.getEntriesByType("navigation")[0];
    if (nav && (nav.type === "reload" || nav.type === "back_forward")) return;
  } catch (e) { /* no navigation timing: treat as a fresh load */ }

  var moved = false;
  var done = false;
  ["wheel", "touchstart", "keydown", "mousedown", "pointerdown"].forEach(function (t) {
    window.addEventListener(t, function () { moved = true; }, { passive: true, capture: true });
  });
  /* a later in-page jump is handled natively (and by folds.js / moved.js); stop here */
  window.addEventListener("hashchange", function () { done = true; });

  function target() {
    var id = hash.slice(1);
    try { id = decodeURIComponent(id); } catch (e) { /* keep the raw id */ }
    return doc.getElementById(id);
  }
  function px(v) { var n = parseFloat(v); return isFinite(n) ? n : 0; }

  function land() {
    if (moved || done) return;
    var t = target();
    if (!t || !t.scrollIntoView) return;
    var r = t.getBoundingClientRect();
    if (!r.width && !r.height) return; /* inside a closed fold or display:none */
    var want = px(window.getComputedStyle(root).scrollPaddingTop) + px(window.getComputedStyle(t).scrollMarginTop);
    if (Math.abs(r.top - want) > 3) t.scrollIntoView({ block: "start", behavior: "instant" });
  }
  function later() { window.setTimeout(land, 0); }

  function start() {
    later();
    if (doc.fonts) {
      if (doc.fonts.ready) doc.fonts.ready.then(later);
      if (doc.fonts.addEventListener) doc.fonts.addEventListener("loadingdone", later);
    }
    if (window.ResizeObserver && doc.body) {
      var ro = new window.ResizeObserver(later);
      ro.observe(doc.body);
      window.setTimeout(function () { ro.disconnect(); done = true; }, 3000);
    } else {
      window.setTimeout(function () { done = true; }, 3000);
    }
  }
  if (doc.readyState === "complete") start();
  else window.addEventListener("load", start);
})();
