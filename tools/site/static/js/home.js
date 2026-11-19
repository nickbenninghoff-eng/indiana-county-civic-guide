/* home.js: the home page map and "Your governments" strip (pages/landing.py; phase 6, 2026-11-18). ASCII only; text
   is inserted with textContent; nothing is fetched or stored (the saved place is read through window.civicHere,
   static/js/here.js).

   1. Panel links. static/js/map.js draws the panel (name, type, the "Open ... page" button). This script copies the
      area's links (shipped hidden in #layer-data, one block per area, with real links: its page's tabs, its offices
      and their holders, its elections and money) in under the panel's type line each time map.js redraws it. The area
      is found from the panel's button, whose href is unique per area.
   2. Select, then open. A click on an area (or Enter on a focused one) selects it and keeps its links in the panel
      instead of leaving the page; a second click on the selected area, or the panel's button, opens its page. From
      the keyboard, focus moves to the panel's heading so Tab goes through its links; Escape returns to the area.
      With JavaScript off every area is a plain link to its page.
   3. Layer buttons inside a panel block ("County council", ...) switch the map to that layer. Before an area is
      chosen the panel lists the current layer's areas (2026-11-18); choosing one there selects it like the map does.
   4. Your governments. With a saved place the strip lists the reader's governments (the city or town, the township,
      the school corporation, the county) as buttons that select each on the map, and the map opens on the city or
      town (or the township). Only what the reader chose counts: civicHere.mine() never treats the guide's defaults
      as a choice, so a township or school corporation that was not chosen is named as not chosen. The strip follows
      a place picked on the page (the "civic:place" event from here.js). */
(function () {
  "use strict";
  var doc = document;
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }

  function setup() {
    var root = doc.getElementById("home-map");
    var panel = doc.getElementById("cmap-panel");
    var store = doc.getElementById("layer-data");
    var dataEl = doc.getElementById("cmap-data");
    if (!root || !panel || !store || !dataEl) return;
    var data = {};
    try { data = JSON.parse(dataEl.textContent); } catch (e) { return; }
    var byHref = {};
    Object.keys(data).forEach(function (uid) { byHref[data[uid].href] = uid; });
    var blocks = {};
    each(store.querySelectorAll("[data-hm-uid]"), function (b) { blocks[b.getAttribute("data-hm-uid")] = b; });
    var selected = null;

    /* ---------------------------------------------------------------- 1. panel links */
    /* before an area is chosen the panel shows how to use the map and the current layer's areas (pages/landing.py
       _start_panel); map.js puts back the block it saw at load, so show the list of the layer now on */
    function syncStart() {
      var on = root.querySelector('.cmap-tab[aria-pressed="true"]');
      var tab = on ? on.getAttribute("data-layer") : "";
      each(panel.querySelectorAll("[data-hm-list]"), function (l) {
        l.classList.toggle("is-on", l.getAttribute("data-hm-list") === tab);
      });
    }
    function fill() {
      var open = panel.querySelector("a.cmap-open");
      if (!open) { syncStart(); return; }
      var uid = byHref[open.getAttribute("href")];
      var have = panel.querySelector(".hm-block");
      if (have && have.getAttribute("data-hm-uid") === uid) return;
      if (have) have.parentNode.removeChild(have);
      if (!uid || !blocks[uid]) return;
      var copy = blocks[uid].cloneNode(true);
      var type = panel.querySelector(".cmap-type");
      var facts = panel.querySelector(".cmap-facts");
      if (facts && !facts.children.length) facts.parentNode.removeChild(facts);
      panel.insertBefore(copy, type ? type.nextSibling : open);
    }
    new MutationObserver(fill).observe(panel, { childList: true });

    function shapeOf(uid) {
      var found = null;
      each(root.querySelectorAll(".cmap-a[data-uid]"), function (a) {
        if (!found && a.getAttribute("data-uid") === uid) found = a;
      });
      return found;
    }

    function select(uid, focusPanel) {
      if (!uid || !data[uid] || !shapeOf(uid)) return false;
      root.dispatchEvent(new CustomEvent("cmap-select", { detail: { uid: uid } }));
      selected = uid;
      fill();
      if (focusPanel) {
        var hd = panel.querySelector("h3");
        if (hd) { hd.setAttribute("tabindex", "-1"); hd.focus(); }
      }
      return true;
    }

    /* ---------------------------------------------------------------- 2. select, then open */
    root.addEventListener("click", function (ev) {
      var a = ev.target.closest ? ev.target.closest(".cmap-a") : null;
      if (!a || !root.contains(a)) return;
      var uid = a.getAttribute("data-uid");
      if (uid === selected) return;                 /* second activation: follow the link */
      ev.preventDefault();
      var keyboard = ev.detail === 0;
      select(uid, keyboard);
      if (!keyboard) {
        /* on a phone the panel sits under the map: bring it into view */
        var r = panel.getBoundingClientRect();
        if (r.top > window.innerHeight - 80 && panel.scrollIntoView) panel.scrollIntoView({ block: "nearest" });
      }
    }, true);
    root.addEventListener("cmap-layer", function () { selected = null; });
    panel.addEventListener("keydown", function (ev) {
      if (ev.key !== "Escape" || !selected) return;
      var s = shapeOf(selected);
      if (s) { ev.preventDefault(); s.focus(); }
    });

    /* ---------------------------------------------------------------- 3. layer buttons in the panel */
    panel.addEventListener("click", function (ev) {
      /* an area in the panel's list: select it, as on the map (with JavaScript off it is a link to its page) */
      var pick = ev.target.closest ? ev.target.closest("a[data-hm-pick]") : null;
      if (pick) {
        if (select(pick.getAttribute("data-hm-pick"), true)) ev.preventDefault();
        return;
      }
      var b = ev.target.closest ? ev.target.closest("[data-hm-layer]") : null;
      if (!b) return;
      var want = b.getAttribute("data-hm-layer");
      each(root.querySelectorAll(".cmap-tab[data-layer]"), function (t) {
        if (t.getAttribute("data-layer") === want) { t.click(); t.focus(); }
      });
    });

    /* ---------------------------------------------------------------- 4. your governments */
    var text = doc.getElementById("home-mine-text");
    var pickLink = doc.getElementById("pick-h");
    function govButton(uid, label) {
      if (!data[uid]) return null;
      var b = doc.createElement("button");
      b.type = "button";
      b.className = "home-mine-btn";
      b.textContent = label;
      b.setAttribute("aria-label", label + ": show on the map");
      b.addEventListener("click", function () { select(uid, true); });
      return b;
    }
    function mine() {
      if (!text || !window.civicHere) return;
      var m = window.civicHere.mine();
      if (!m) return;
      while (text.firstChild) text.removeChild(text.firstChild);
      var bits = [];
      var munName = m.muni && data[m.muni] ? data[m.muni].n : "";
      if (m.muni) bits.push([m.muni, munName.replace(/^(City|Town) of /, "")]);
      if (m.township) bits.push([m.township, data[m.township] ? data[m.township].n : ""]);
      if (m.school) bits.push([m.school, data[m.school] ? data[m.school].n : ""]);
      var lead = doc.createElement("span");
      lead.textContent = "Your governments (saved on this device): ";
      text.appendChild(lead);
      var n = 0;
      bits.forEach(function (x) {
        var b = govButton(x[0], x[1]);
        if (!b) return;
        if (n) text.appendChild(doc.createTextNode(" "));
        text.appendChild(b);
        n += 1;
      });
      /* the county covers every address: not a map layer, a link to its page (the row above the map) */
      var county = doc.querySelector("#county-row .hm-county-name");
      if (county) {
        var ca = doc.createElement("a");
        ca.className = "home-mine-btn home-mine-link";
        ca.setAttribute("href", county.getAttribute("href"));
        ca.textContent = (county.textContent || "").replace(/ government$/, "");
        if (n) text.appendChild(doc.createTextNode(" "));
        text.appendChild(ca);
      }
      var gaps = [];
      if (!m.township) gaps.push("township");
      if (!m.school) gaps.push("school corporation");
      if (gaps.length) {
        var note = doc.createElement("span");
        note.className = "home-mine-note";
        var g = gaps.join(" and ");
        note.textContent = g.charAt(0).toUpperCase() + g.slice(1) + " not chosen.";
        text.appendChild(note);
      } else {
        text.appendChild(doc.createTextNode(" "));
      }
      if (pickLink) pickLink.textContent = gaps.length ? "Choose your " + gaps.join(" and ") + ", or change your place" : "Change your place";
      /* the map opens on the reader's city or town (or township), once; a later pick moves it */
      var uid = m.muni || m.township;
      if (uid) select(uid, false);
    }
    mine();
    doc.addEventListener("civic:place", function () {
      if (!window.civicHere || !window.civicHere.mine()) {
        if (text) text.textContent = "No place saved. Choose your city, town or township, and the map opens on your governments.";
        if (pickLink) pickLink.textContent = "Choose your place";
        return;
      }
      mine();
    });
  }

  /* app.js is deferred and runs before DOMContentLoaded, before the later partials (map.js) have set up */
  if (doc.readyState !== "complete") doc.addEventListener("DOMContentLoaded", setup);
  else setup();
})();
