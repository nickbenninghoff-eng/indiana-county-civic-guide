/* offices.js: the office pages and the Offices hub (pages/offices.py; phase 6, 2026-11-16). ASCII only; text is
   inserted with textContent; nothing is fetched or stored.

   1. Money tab (#mt-ctl): an Election switch (Both / Primary / General) and a neutral party filter (no party
      colors) above the charts. Shipped hidden: with JavaScript off every chart shows. Charts carry
      data-mt-phase ("whole": whole-cycle filings; "primary" / "general": news figures for that contest, or a cycle
      split at the pre-primary report, marked data-mt-split) and their rows data-party. Both shows the whole-cycle
      charts and the news charts of both contests; Primary and General show only their side. An election (or a
      state candidate) left with nothing to show is hidden, and a line says how many and why. The choice is kept in
      the address (#show=primary&party=D) so it can be linked; other #ids are left alone.
   2. Offices hub map (#offices-map): static/js/map.js draws the panel; this script adds the selected area's office
      list (shipped hidden in #ofm-lists, one block per area, with real links) under the panel's heading, each time
      map.js redraws it. The area is found from the panel's "open" link, whose href is unique per area.
   3. Offices hub, saved place (#ofh-pre): with a saved place (window.civicHere, static/js/here.js) the hub opens on
      it: the place (or its township) is selected on the map and the list shows only its governments' offices, with
      the visible "Showing: ... [Show all]" line. Only what the reader chose counts (civicHere.mine never treats the
      guide's defaults as a choice); an explicit #anchor in the address wins and the line only offers it. */
(function () {
  "use strict";
  var doc = document;
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }
  var DOT = " " + String.fromCharCode(183) + " ";

  /* ---------------------------------------------------------------- 1. Money tab controls */
  function money() {
    var ctl = doc.getElementById("mt-ctl");
    if (!ctl) return;
    var btns = Array.prototype.slice.call(ctl.querySelectorAll("[data-mt-show]"));
    var sel = doc.getElementById("mt-party");
    var state = doc.getElementById("mt-ctl-state");
    var units = Array.prototype.slice.call(doc.querySelectorAll(".mt-year[data-mt-year], .mt-person"));
    var show = "both", party = "";

    function parseHash() {
      var h = (window.location.hash || "").replace(/^#/, "");
      if (!/(^|&)(show|party)=/.test(h)) return false;
      var out = { show: "both", party: "" };
      h.split("&").forEach(function (kv) {
        var i = kv.indexOf("="), k = kv.slice(0, i), v = kv.slice(i + 1);
        try { v = decodeURIComponent(v); } catch (e) { /* keep */ }
        if (k === "show" && (v === "primary" || v === "general" || v === "both")) out.show = v;
        if (k === "party") out.party = v;
      });
      var okParty = !out.party;
      each(sel.options, function (o) { if (o.value === out.party) okParty = true; });
      if (!okParty) out.party = "";
      show = out.show; party = out.party;
      return true;
    }
    function writeHash() {
      var bits = [];
      if (show !== "both") bits.push("show=" + show);
      if (party) bits.push("party=" + encodeURIComponent(party));
      var base = window.location.href.split("#")[0];
      try { history.replaceState(null, "", bits.length ? base + "#" + bits.join("&") : base); } catch (e) { /* ignore */ }
    }
    function phaseOk(el) {
      var ph = el.getAttribute("data-mt-phase");
      if (show === "both") return !el.hasAttribute("data-mt-split");
      return ph === show;
    }
    function partyOk(fig) {
      var rows = fig.querySelectorAll(".mrw-row[data-party]");
      var any = false;
      each(rows, function (r) {
        var ok = !party || r.getAttribute("data-party") === party;
        r.hidden = !ok;
        if (ok) any = true;
      });
      if (rows.length) return any;
      return !party || fig.getAttribute("data-party") === party;
    }
    function nameOf(u) {
      if (u.hasAttribute("data-mt-year")) return u.getAttribute("data-mt-year");
      var hd = u.querySelector("h2");
      return hd ? hd.textContent.replace(/\s+/g, " ").trim() : "";
    }
    function whyOf(u, phaseHit) {
      if (!phaseHit) {
        var holder = u.hasAttribute("data-mt-why-" + show) ? u : u.closest("[data-mt-why-" + show + "]");
        return holder ? holder.getAttribute("data-mt-why-" + show) : "nothing for this choice";
      }
      return "no figures for " + sel.options[sel.selectedIndex].text;
    }
    function apply() {
      btns.forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-mt-show") === show ? "true" : "false"); });
      sel.value = party;
      var hidden = [];
      units.forEach(function (u) {
        var figs = u.classList.contains("mt-person") ? [u] :
          Array.prototype.slice.call(u.querySelectorAll("figure[data-mt-phase]"));
        var phaseHit = false, shown = 0;
        figs.forEach(function (f) {
          var p = phaseOk(f);
          if (p) phaseHit = true;
          var ok = partyOk(f) && p;
          if (f !== u) f.hidden = !ok;
          if (ok) shown += 1;
        });
        /* whole-cycle totals and other non-chart parts follow the switch */
        each(u.querySelectorAll("[data-mt-phase]:not(figure)"), function (x) { x.hidden = !phaseOk(x); });
        u.hidden = shown === 0;
        if (!shown) hidden.push(nameOf(u) + " (" + whyOf(u, phaseHit) + ")");
      });
      var what = { both: "Primary and general", primary: "Primary", general: "General election" }[show];
      var txt = "Showing: " + what + DOT + sel.options[sel.selectedIndex].text + ".";
      if (hidden.length) {
        var noun = units.length && units[0].classList.contains("mt-person") ? "candidate" : "election";
        txt += " " + hidden.length + " " + noun + (hidden.length === 1 ? " is" : "s are") + " hidden: " + hidden.join("; ") + ".";
      }
      state.textContent = (show === "both" && !party) ? "" : txt;
      state.hidden = !state.textContent;
    }
    btns.forEach(function (b) {
      b.addEventListener("click", function () { show = b.getAttribute("data-mt-show"); apply(); writeHash(); });
    });
    sel.addEventListener("change", function () { party = sel.value; apply(); writeHash(); });
    window.addEventListener("hashchange", function () { if (parseHash()) apply(); });
    each(doc.querySelectorAll("[data-mt-hint]"), function (p) {
      p.textContent = "These filings can also be split at each committee's pre-primary report: choose Primary or " +
        "General above to see the two parts. Each part is a sum of whole reports; nothing is estimated.";
    });
    parseHash();
    ctl.hidden = false;
    apply();
  }

  /* ---------------------------------------------------------------- 2. hub map: the office list in the panel */
  function hubMap() {
    var root = doc.getElementById("offices-map");
    var panel = doc.getElementById("cmap-panel");
    var store = doc.getElementById("ofm-lists");
    var dataEl = doc.getElementById("cmap-data");
    if (!root || !panel || !store || !dataEl) return null;
    var data = {};
    try { data = JSON.parse(dataEl.textContent); } catch (e) { return null; }
    var byHref = {};
    Object.keys(data).forEach(function (uid) { byHref[data[uid].href] = uid; });
    var blocks = {};
    each(store.querySelectorAll("[data-ofm-uid]"), function (b) { blocks[b.getAttribute("data-ofm-uid")] = b; });
    function fill() {
      var open = panel.querySelector("a.cmap-open");
      if (!open) return;
      var uid = byHref[open.getAttribute("href")];
      var have = panel.querySelector(".ofm-block");
      if (have && have.getAttribute("data-ofm-uid") === uid) return;
      if (have) have.parentNode.removeChild(have);
      if (!uid || !blocks[uid]) return;
      var copy = blocks[uid].cloneNode(true);
      var type = panel.querySelector(".cmap-type");
      var facts = panel.querySelector(".cmap-facts");
      if (facts && !facts.children.length) facts.parentNode.removeChild(facts);
      panel.insertBefore(copy, type ? type.nextSibling : open);
    }
    new MutationObserver(fill).observe(panel, { childList: true });
    fill();
    return root;
  }

  /* ---------------------------------------------------------------- 3. hub: the saved place */
  function hubPlace(root) {
    var slot = doc.getElementById("ofh-pre");
    if (!slot || !window.civicHere) return;
    var m = window.civicHere.mine();
    if (!m) return;
    var bar = doc.querySelector('.tf[data-tf-table="offices-all"]');
    var uid = m.muni || (m.township || "");
    var shape = null;
    if (root && uid) each(root.querySelectorAll(".cmap-a[data-uid]"), function (a) { if (!shape && a.getAttribute("data-uid") === uid) shape = a; });
    var govs = ["St. Joseph County"].concat(m.names);
    govs.push("state and legislative seats");
    var test = function (row) { return m.wants(row.getAttribute("data-here-layer") || ""); };
    function on() {
      if (shape) root.dispatchEvent(new CustomEvent("cmap-select", { detail: { uid: uid } }));
      if (bar) bar.dispatchEvent(new CustomEvent("tf-scope", { detail: { test: test } }));
    }
    function off() {
      if (shape) root.dispatchEvent(new CustomEvent("cmap-select", { detail: { uid: null } }));
      if (bar) bar.dispatchEvent(new CustomEvent("tf-scope", { detail: null }));
    }
    var ctl = window.civicHere.line(slot, {
      onLabel: "Showing",
      onText: govs.join(DOT),
      onWhy: " Your saved place (kept on this device only): " + (shape ? "selected on the map, and " : "") +
             "only its governments' offices in the list. Every district seat of those governments is listed: which " +
             "districts are yours depends on your address.",
      offText: govs.join(DOT),
      applyLabel: "Show my place",
      undoLabel: "Show all",
      apply: on,
      undo: off
    });
    if (bar) bar.addEventListener("tf-scope-cleared", function () { if (ctl.state() === "on") ctl.set("off"); });
    if (window.civicHere.hashWins()) ctl.set("off");
    else { on(); ctl.set("on"); }
  }

  function run() {
    money();
    var root = hubMap();
    hubPlace(root);
  }
  /* app.js is deferred and runs before DOMContentLoaded, before the later partials (tablefilter.js) have set up */
  if (doc.readyState !== "complete") doc.addEventListener("DOMContentLoaded", run);
  else run();
})();
