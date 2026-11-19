/* Elections pages (pages/elections.py, pages/election_pages.py, pages/elections_numbers.py). Phase 6 step 4
   (2026-11-16): the results explorer is gone; its job is done by the election pages (elections/<id>/contests/) and the
   office pages' Elections tabs. This script:
   1. elections/results/: an old link to one contest (#contest-<contest id>, civic/related.py contest_href) goes to
      that contest on its election's page (the #results-forward map: election id -> its Contests tab; "x" lists the
      contests whose id does not start with their election's). Without JavaScript the link lands on the contest's row
      in the every-contest table.
   2. A forwarding page (elections/margins/, turnout/, landscape/; a[data-forward]) opened without an #anchor follows
      its link; with an #anchor static/js/moved.js sends the id to the Compare tab that has it.
   3. An election's Contests tab opened on #contest-<id>: that contest's "Every candidate" fold opens.
   4. The Elections hub's "next ballot" cards open on the reader's saved place (window.civicHere, here.js): only the
      governments that are certainly theirs (a guide default never counts), with a button to show every card; an
      explicit #anchor wins (the line then only offers it). With no saved place, or without JavaScript, every card shows.
   ASCII only; text is inserted with textContent only. */
(function () {
  "use strict";
  var doc = document;
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }
  function safe(dest) {
    /* only a relative path written by the build: never a scheme or another host */
    return typeof dest === "string" && dest && !/^\s*([a-z][a-z0-9+.-]*:|\/\/|\\)/i.test(dest);
  }
  function hashId() {
    var id = (window.location.hash || "").slice(1);
    try { id = decodeURIComponent(id); } catch (e) { /* keep raw */ }
    return id;
  }

  /* ------------------------------------------------------------ 1. old #contest-<id> links on elections/results/ */
  function contestForward() {
    var node = doc.getElementById("results-forward");
    if (!node) return;
    var map;
    try { map = JSON.parse(node.textContent); } catch (e) { return; }
    function go() {
      var m = /^contest-([A-Za-z0-9-]+)$/.exec(hashId());
      if (!m) return;
      var cid = m[1];
      var eid = Object.prototype.hasOwnProperty.call(map.x || {}, cid) ? map.x[cid] : "";
      if (!eid) { var p = /^([0-9]{4}[a-z])-/.exec(cid); eid = p ? p[1] : ""; }
      var dest = eid && map.e && Object.prototype.hasOwnProperty.call(map.e, eid) ? map.e[eid] : "";
      if (safe(dest)) window.location.replace(dest + "#contest-" + cid);
    }
    go();
    window.addEventListener("hashchange", go);
  }

  /* ------------------------------------------------------------ 2. forwarding pages with no #anchor */
  function movedPage() {
    var a = doc.querySelector("a[data-forward]");
    if (!a || (window.location.hash || "").length > 1) return;
    var dest = a.getAttribute("href");
    if (safe(dest)) window.location.replace(dest);
  }

  /* ------------------------------------------------------------ 3. an election's contest opened by the address */
  function openContest() {
    var id = hashId();
    if (!/^contest-/.test(id)) return;
    var li = doc.getElementById(id);
    if (!li || !li.classList || !li.classList.contains("ep-contest")) return;
    var fold = li.querySelector("details.ep-fold");
    if (fold) fold.open = true;
  }

  /* ------------------------------------------------------------ 4. the hub's next ballot, on the saved place */
  function hubBallot() {
    var slot = doc.querySelector('[data-here-pre="explorer"][data-here-hub]');
    if (!slot || !window.civicHere) return;
    var box = doc.getElementById(slot.getAttribute("data-here-for"));
    if (!box) return;
    var m = window.civicHere.mine();
    if (!m) return;
    var cards = Array.prototype.filter.call(box.children, function (c) { return c.hasAttribute("data-here-layer"); });
    var mine = cards.filter(function (c) { return m.sure(c.getAttribute("data-here-layer")); });
    var DOT = " " + String.fromCharCode(183) + " ";
    if (!mine.length) {
      var none = window.civicHere.line(slot, {
        noteLabel: "Your saved place",
        note: m.label + ": none of its governments has a seat on this ballot in the guide's data.",
        noteWhy: " Kept on this device only. Every government with seats on it is listed below."
      });
      none.set("note");
      return;
    }
    var names = mine.map(function (c) { return c.getAttribute("data-here-name") || ""; }).join(DOT);
    function show(only) { cards.forEach(function (c) { c.hidden = only && mine.indexOf(c) < 0; }); }
    var ctl = window.civicHere.line(slot, {
      onText: names,
      onWhy: " The governments of your saved place (kept on this device only). Which district seats are yours " +
             "depends on your address.",
      offText: names,
      applyLabel: "Show only these",
      undoLabel: "Show every government",
      apply: function () { show(true); },
      undo: function () { show(false); }
    });
    if (window.civicHere.hashWins()) ctl.set("off");
    else {
      show(true);
      ctl.set("on");
      /* the offices fold (closed by folds.js on load) opens on the reader's own governments */
      var fold = doc.getElementById("ballot-offices");
      if (fold) window.setTimeout(function () { fold.open = true; }, 0);
    }
  }

  contestForward();
  movedPage();
  /* after static/js/folds.js (same bundle) has closed the folds on load */
  window.setTimeout(openContest, 0);
  window.addEventListener("hashchange", openContest);
  /* app.js is deferred: here.js (a later partial) is ready by DOMContentLoaded */
  if (doc.readyState !== "complete") doc.addEventListener("DOMContentLoaded", hubBallot);
  else hubBallot();
})();
