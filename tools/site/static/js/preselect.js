/* preselect.js: pages open on the reader's saved place (review pattern P4; civic/preselect.py; added 2026-11-09,
   Wave E batch 8). Each placeholder <p data-here-pre=KIND data-here-for=ID hidden> becomes a visible line
   ("Showing: ... [Show all]") once this script has changed the page, and only then:
     filter  a table_filter list (tablefilter.js deep mode): rows of other governments are hidden (rows carry
             data-here-layer); Reset, the Government filter or the line's button show everything again;
     first   groups of the reader's areas (data-here-layer) move to the top of the container; the button restores
             the usual order;
     one     pick_one items (pick_one.js) of the reader's area are opened; the keys come from the saved school
             corporation (data-here-keys="school") or a JSON map built from the guide's data
             (data-here-keys="json:<script id>"); the button shows every item;
     map     the reader's area is selected on the map (map.js), its panel showing; the button clears it.
   With no saved place nothing happens. An explicit #anchor in the address wins: the page opens as the link says and
   the line only offers the saved place. The saved place is read through window.civicHere (here.js) and never
   written anywhere. Runs on DOMContentLoaded, after every other part of app.js has set up its page. ASCII only;
   text is inserted with textContent. */
(function () {
  "use strict";
  var doc = document;
  var DOT = " " + String.fromCharCode(183) + " ";
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }
  function ev(name, detail) { return new CustomEvent(name, { detail: detail }); }

  function start(slot, ctl, apply) {
    if (window.civicHere.hashWins()) ctl.set("off");
    else { apply(); ctl.set("on"); }
  }

  /* ---------------------------------------------------------------- filter: governments in a table_filter list */
  function governments(m) {
    var out = ["St. Joseph County"].concat(m.names);
    out.push("state and legislative seats");
    return out.join(DOT);
  }
  function filterSlot(slot, m) {
    var id = slot.getAttribute("data-here-for");
    var list = doc.getElementById(id);
    var bar = null;
    each(doc.querySelectorAll(".tf[data-tf-table]"), function (b) { if (b.getAttribute("data-tf-table") === id) bar = b; });
    if (!list || !bar || bar.hidden) return;
    var test = function (row) { return m.wants(row.getAttribute("data-here-layer") || ""); };
    var hide = 0;
    each(list.querySelectorAll("[data-tf-row]"), function (r) { if (!test(r)) hide += 1; });
    if (!hide) return;
    var noun = slot.getAttribute("data-here-noun") || "rows";
    var govSel = bar.querySelectorAll('select[data-tf-key="government"]');
    /* "your governments" stands in for the Government filter: clear it before applying */
    function on() {
      each(govSel, function (s) { s.value = ""; });
      bar.dispatchEvent(ev("tf-scope", { test: test }));
    }
    var ctl = window.civicHere.line(slot, {
      onText: governments(m),
      onWhy: " Only the " + noun + " of your saved place's governments (kept on this device only). Every district " +
             "seat of those governments is listed: which districts are yours depends on your address.",
      offText: governments(m),
      applyLabel: "Show only these",
      undoLabel: "Show all",
      apply: on,
      undo: function () { bar.dispatchEvent(ev("tf-scope", null)); }
    });
    bar.addEventListener("tf-scope-cleared", function () { if (ctl.state() === "on") ctl.set("off"); });
    /* a group the scope empties (a calendar year with no seats for the reader's governments) keeps its place with a
       note saying so, and a Show all button (tablefilter.js data-tf-keep) */
    var empties = list.querySelectorAll("[data-tf-group-empty][data-here-empty]");
    each(empties, function (n) { n.setAttribute("data-here-text0", n.textContent); });
    function notes() {
      var on = ctl.state() === "on";
      each(empties, function (n) {
        while (n.firstChild) n.removeChild(n.firstChild);
        n.appendChild(doc.createTextNode(on ? n.getAttribute("data-here-empty") + " " : n.getAttribute("data-here-text0")));
        if (!on) return;
        var b = doc.createElement("button");
        b.type = "button";
        b.className = "btn btn-small here-pre-btn";
        b.textContent = "Show all";
        b.addEventListener("click", function () { bar.dispatchEvent(ev("tf-scope", null)); ctl.set("off"); notes(); });
        n.appendChild(b);
      });
    }
    list.addEventListener("rows-filtered", function () { window.setTimeout(notes, 0); });
    /* choosing one government by hand replaces "your governments" */
    each(govSel, function (s) {
      s.addEventListener("change", function () {
        if (ctl.state() === "on" && s.value) { bar.dispatchEvent(ev("tf-scope", null)); ctl.set("off"); }
      });
    });
    start(slot, ctl, on);
  }

  /* ---------------------------------------------------------------- first: the reader's groups first */
  function firstSlot(slot, m) {
    var box = doc.getElementById(slot.getAttribute("data-here-for"));
    if (!box) return;
    var groups = Array.prototype.filter.call(box.children, function (c) { return c.hasAttribute("data-here-layer"); });
    if (!groups.length) return;
    var anchor = groups[groups.length - 1].nextSibling;
    var usual = groups.slice();
    var mineG = groups.filter(function (g) { return m.sure(g.getAttribute("data-here-layer")); });
    var rest = groups.filter(function (g) { return mineG.indexOf(g) < 0; });
    var local = mineG.filter(function (g) { return g.getAttribute("data-here-layer") !== "state"; });
    function names(list) { return list.map(function (g) { return g.getAttribute("data-here-name") || ""; }).join(DOT); }
    function order(list) { list.forEach(function (g) { box.insertBefore(g, anchor); }); }
    if (!local.length) {
      var none = window.civicHere.line(slot, {
        noteLabel: "Local questions for your saved place",
        note: "none for " + m.label + " in the guide's data. The statewide questions come first, as for everyone."
      });
      none.set("note");
      return;
    }
    var ctl = window.civicHere.line(slot, {
      onLabel: "Showing first",
      onText: names(mineG),
      onWhy: " The questions for your saved place's areas (kept on this device only); every other question follows.",
      offText: names(local),
      applyLabel: "Show these first",
      undoLabel: "Show in the usual order",
      apply: function () { order(mineG.concat(rest)); },
      undo: function () { order(usual); }
    });
    start(slot, ctl, function () { order(mineG.concat(rest)); });
  }

  /* ---------------------------------------------------------------- one: open the reader's pick_one items */
  function openKeys() {
    var set = {};
    each(doc.querySelectorAll("details[data-one]"), function (d) { if (d.open) set[d.getAttribute("data-one")] = true; });
    return Object.keys(set).sort().join(",");
  }
  function oneSlot(slot, m) {
    var spec = slot.getAttribute("data-here-keys") || "";
    var keys = [], names = [], why = "", note = "";
    var known = {};
    each(doc.querySelectorAll("details[data-one]"), function (d) { known[d.getAttribute("data-one")] = d.getAttribute("data-one-name") || ""; });
    if (spec === "school") {
      if (!m.school || !Object.prototype.hasOwnProperty.call(known, m.school)) return;
      keys = [m.school];
      names = [known[m.school]];
      why = " Your saved school corporation (kept on this device only). Every other corporation is one click away below.";
    } else if (spec.indexOf("json:") === 0) {
      var node = doc.getElementById(spec.slice(5));
      var map = null;
      try { map = node ? JSON.parse(node.textContent) : null; } catch (e) { map = null; }
      if (!map) return;
      var hit = Object.prototype.hasOwnProperty.call(map.places || {}, m.place) ? map.places[m.place] : null;
      /* data-here-also (added 2026-11-09, elections/margins/): also open the reader's city or town, township and
         school corporation, when they chose them (map.alias: other keys the same area goes by on this page) */
      var also = (slot.getAttribute("data-here-also") || "").split(" ").filter(Boolean);
      if (also.length) {
        var extra = [];
        if (also.indexOf("muni") >= 0 && m.muni) extra.push(m.muni);
        if (also.indexOf("township") >= 0 && m.township) extra.push(m.township);
        if (also.indexOf("school") >= 0 && m.school) extra.push(m.school);
        var ak = [], an = [];
        extra.forEach(function (k) {
          ((map.alias || {})[k] || [k]).forEach(function (x) { if (Object.prototype.hasOwnProperty.call(known, x)) { ak.push(x); an.push(known[x]); } });
        });
        hit = { keys: ak.concat(hit ? hit.keys : []), names: an.concat(hit ? hit.names : []) };
      }
      if (!hit || !hit.keys.length) {
        note = m.label + " is in more than one commissioner or council district in the guide's precinct results, or the " +
               "guide cannot place all of it, so no district is opened. Find yours on the map.";
      } else {
        hit.keys.forEach(function (k, i) {
          if (Object.prototype.hasOwnProperty.call(known, k)) { keys.push(k); names.push(hit.names[i] || known[k]); }
        });
        why = slot.getAttribute("data-here-why") ||
              (" Every precinct the guide's data places in " + m.label + " voted in these districts' races in " +
               (map.years || "the latest elections") + " (precinct results). Your voter registration names your districts.");
      }
    }
    if (note) {
      window.civicHere.line(slot, { note: note }).set("note");
      return;
    }
    if (!keys.length) return;
    var want = keys.slice().sort().join(",");
    function apply() { doc.dispatchEvent(ev("one:choose", { keys: keys })); }
    var ctl = window.civicHere.line(slot, {
      onLabel: "Opened",
      onText: names.join(DOT),
      onWhy: why,
      offText: names.join(DOT),
      applyLabel: slot.getAttribute("data-here-apply") || "Open them",
      undoLabel: slot.getAttribute("data-here-undo") || "Show all",
      apply: apply,
      undo: function () { doc.dispatchEvent(ev("one:all", null)); }
    });
    /* the reader opening or closing items by hand: the line goes back to an offer */
    var pending = false;
    doc.addEventListener("toggle", function (e) {
      if (!e.target || !e.target.hasAttribute || !e.target.hasAttribute("data-one") || pending) return;
      pending = true;
      window.setTimeout(function () {
        pending = false;
        if (ctl.state() === "on" && openKeys() !== want) ctl.set("off");
      }, 0);
    }, true);
    start(slot, ctl, apply);
  }

  /* ---------------------------------------------------------------- map: select the reader's area */
  function mapSlot(slot, m) {
    var host = doc.getElementById(slot.getAttribute("data-here-for"));
    var root = host ? (host.classList.contains("cmap") ? host : host.querySelector(".cmap")) : null;
    if (!root) return;
    var uid = m.muni || m.township;
    var shape = null;
    each(root.querySelectorAll(".cmap-a[data-uid]"), function (a) { if (!shape && a.getAttribute("data-uid") === uid) shape = a; });
    if (!uid || !shape) return;
    var name = m.muni ? m.label : (m.short ? m.short + " Township" : m.label);
    var busy = false;
    function apply() { busy = true; root.dispatchEvent(ev("cmap-select", { uid: uid })); busy = false; }
    var ctl = window.civicHere.line(slot, {
      onLabel: "Selected on the map",
      onText: name,
      onWhy: " Your saved place (kept on this device only); its estimates are in the panel. Point at any other area to compare.",
      offText: name,
      applyLabel: "Select it on the map",
      undoLabel: "Clear",
      apply: apply,
      undo: function () { busy = true; root.dispatchEvent(ev("cmap-select", { uid: null })); busy = false; }
    });
    root.addEventListener("cmap-layer", function () { if (!busy && ctl.state() === "on") ctl.set("off"); });
    start(slot, ctl, apply);
  }

  /* ---------------------------------------------------------------- rows: the reader's rows first in each table
     (added 2026-11-09, money/campaigns/ "Every area"): rows carry data-here-layer and data-here-name; only the city or
     town, township and school corporation the reader certainly has (civicHere sure) move, since the county and the
     state are everyone's. The button puts every row back where it was. */
  function rowsSlot(slot, m) {
    var box = doc.getElementById(slot.getAttribute("data-here-for"));
    if (!box) return;
    var rows = Array.prototype.filter.call(box.querySelectorAll("tr[data-here-layer]"), function (r) {
      var l = r.getAttribute("data-here-layer");
      return /^(municipality|township|school):/.test(l) && m.sure(l);
    });
    if (!rows.length) return;
    var bodies = [];
    rows.forEach(function (r) { if (bodies.indexOf(r.parentNode) < 0) bodies.push(r.parentNode); });
    var usual = bodies.map(function (b) { return { b: b, kids: Array.prototype.slice.call(b.children) }; });
    var names = rows.map(function (r) { return r.getAttribute("data-here-name") || ""; }).join(DOT);
    function apply() {
      rows.slice().reverse().forEach(function (r) { r.parentNode.insertBefore(r, r.parentNode.firstChild); r.classList.add("here-mine"); });
    }
    function undo() {
      usual.forEach(function (u) { u.kids.forEach(function (k) { u.b.appendChild(k); }); });
      rows.forEach(function (r) { r.classList.remove("here-mine"); });
    }
    var ctl = window.civicHere.line(slot, {
      onLabel: "Showing first",
      onText: names,
      onWhy: " Your saved place's areas (kept on this device only), at the top of their tables; every other area follows.",
      offText: names,
      applyLabel: "Show these first",
      undoLabel: "Show in the usual order",
      apply: apply,
      undo: undo
    });
    start(slot, ctl, apply);
  }

  var KINDS = { filter: filterSlot, first: firstSlot, one: oneSlot, map: mapSlot, rows: rowsSlot };
  function run() {
    if (!window.civicHere) return;
    var m = window.civicHere.mine();
    if (!m) return;
    each(doc.querySelectorAll("[data-here-pre]"), function (slot) {
      var fn = KINDS[slot.getAttribute("data-here-pre")];
      if (fn) fn(slot, m);
    });
  }
  /* app.js is deferred: it runs while readyState is "interactive", before DOMContentLoaded, and before the later
     partials (here.js, tablefilter.js) have set up; so wait for DOMContentLoaded unless the page is already complete */
  if (doc.readyState !== "complete") doc.addEventListener("DOMContentLoaded", run);
  else run();
})();
