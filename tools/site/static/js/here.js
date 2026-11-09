/* Your place: the "You are here" bar on every page, the visible place picker (civic/picker.py),
   the layer rows and counts it drives, the landing map as a picker, and small "your place" markers on
   place pages and the election calendar. Plain JS, ASCII only, data inserted with textContent only.

   Storage: localStorage "civic-place" = {"place": id, "township": id|"any", "school": id|"any", "set": [...]}
   (ids only; the same key and shape the earlier dropdown used, so a returning reader keeps their place).
   "set" (added 2026-11-09, Wave E batch 8 part 2) lists the parts the reader chose: "township" and/or "school".
   Choosing a place fills its township and school with the guide's defaults (civic/layers.py: a town's township, a
   city's usual school corporation); those are NOT in "set". An object without "set" (saved before this change) counts
   as all defaults. Only the preselect reads it: a default never makes a page claim something specific about the
   reader (the tax-bill district, "your school corporation").
   Every access is wrapped: with storage blocked the picker still works for the current page.

   This partial sorts before map.js in the built app.js, so it can relabel the landing map's links
   (which select a place here instead of opening a page) before map.js copies the panel hint. */
(function () {
  "use strict";
  var doc = document;
  var site = doc.getElementById("site");
  var ROOT = (site && site.getAttribute("data-root")) || "./";
  var KEY = "civic-place";
  var DOT = " " + String.fromCharCode(183) + " ";
  /* the address the reader came with, before any map script rewrites it (preselect: an explicit #anchor wins) */
  var HASH0 = window.location.hash;

  function readJSON(id) {
    var el = doc.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
  }
  var H = readJSON("here-data");
  if (!H || !H.places) return;
  function has(o, k) { return !!o && Object.prototype.hasOwnProperty.call(o, k); }
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }
  function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); }

  /* ------------------------------------------------------------ state */
  function normalize(v) {
    if (!v || typeof v !== "object" || !has(H.places, v.place)) return null;
    var p = H.places[v.place];
    var t = p.t || (has(H.townships, v.township) ? v.township : "any");
    var s = has(H.schools, v.school) ? v.school : "any";
    var set = [];
    if (v.set && v.set.indexOf) {
      if (v.set.indexOf("township") >= 0 && !p.t && t !== "any") set.push("township");
      if (v.set.indexOf("school") >= 0 && s !== "any") set.push("school");
    }
    return { place: v.place, township: t, school: s, set: set };
  }
  function load() {
    var raw = null;
    try { raw = window.localStorage.getItem(KEY); } catch (e) { raw = null; }
    if (!raw) return null;
    try { return normalize(JSON.parse(raw)); } catch (e) { return null; }
  }
  function save(st) {
    try {
      if (st) window.localStorage.setItem(KEY, JSON.stringify({ place: st.place, township: st.township, school: st.school,
                                                                  set: st.set || [] }));
      else window.localStorage.removeItem(KEY);
    } catch (e) { /* storage unavailable: the choice lasts for this page only */ }
  }
  /* default township and school for a newly chosen place (civic/layers.py rules) */
  function fresh(id) {
    var p = H.places[id];
    return normalize({ place: id, township: p.t || p.td || "any", school: p.sd || "any" });
  }

  var state = load();

  function placeOf(st) { return st ? H.places[st.place] : null; }
  function namesOf(st) {
    var p = placeOf(st), out = [];
    if (!p) return out;
    out.push({ text: p.n, href: p.u });
    if (!p.t) {
      if (st.township !== "any") out.push({ text: H.townships[st.township], href: "places/" + st.township + "/index.html" });
      else out.push({ text: "township not picked", href: null });
    }
    if (st.school !== "any") out.push({ text: H.schools[st.school], href: "schools/index.html#" + st.school });
    else out.push({ text: "school corporation not picked", href: null });
    return out;
  }
  function plainNames(st) {
    return namesOf(st).map(function (n) { return n.text; }).join(DOT);
  }

  /* ------------------------------------------------------------ "You are here" bar */
  var bar = doc.getElementById("here-bar");
  function renderBar() {
    if (!bar) return;
    var set = doc.getElementById("here-set"), none = doc.getElementById("here-none"), names = doc.getElementById("here-names");
    if (!set || !none || !names) return;
    clear(names);
    var list = namesOf(state);
    list.forEach(function (n, i) {
      if (i) names.appendChild(doc.createTextNode(DOT));
      var el;
      if (n.href) {
        el = doc.createElement("a");
        el.href = ROOT + n.href;
      } else {
        el = doc.createElement("span");
        el.className = "here-missing";
      }
      el.textContent = n.text;
      names.appendChild(el);
    });
    set.hidden = !state;
    none.hidden = !!state;
    bar.hidden = false;
  }

  /* ------------------------------------------------------------ picker */
  var picker = doc.querySelector("[data-picker]");
  var layerData = readJSON("layer-data");

  function upgradeChoices() {
    each(picker.querySelectorAll("a.choice[data-pick]"), function (a) {
      var b = doc.createElement("button");
      b.type = "button";
      b.className = "choice";
      b.setAttribute("data-pick", a.getAttribute("data-pick"));
      b.setAttribute("data-value", a.getAttribute("data-value"));
      b.setAttribute("aria-pressed", "false");
      b.textContent = a.textContent;
      a.parentNode.replaceChild(b, a);
    });
    each(picker.querySelectorAll("[data-js-only]"), function (el) {
      if (el.id !== "pick-township") el.hidden = false;
    });
    each(picker.querySelectorAll(".pick-nojs"), function (el) { el.hidden = true; });
  }

  function renderPicker() {
    if (!picker) return;
    var p = placeOf(state);
    each(picker.querySelectorAll("button.choice[data-pick]"), function (b) {
      var kind = b.getAttribute("data-pick"), v = b.getAttribute("data-value"), on = false;
      if (state) {
        if (kind === "place") on = state.place === v;
        else if (kind === "township") on = state.township === v;
        else if (kind === "school") on = state.school === v;
      }
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
    /* township question: only for a city or town; offer the townships it lies in (all if unknown) */
    var tg = doc.getElementById("pick-township");
    if (tg) {
      tg.hidden = !p || !!p.t;
      if (p && !p.t) {
        var inside = p.it && p.it.length ? p.it : null;
        each(tg.querySelectorAll("button.choice[data-pick='township']"), function (b) {
          var v = b.getAttribute("data-value");
          b.parentNode.hidden = !(v === "any" || !inside || inside.indexOf(v) >= 0 || v === state.township);
        });
        var note = doc.getElementById("pick-township-note");
        if (note) {
          note.textContent = inside && inside.length > 1
            ? p.s + " crosses township lines. Pick the township your address is in, or Not sure."
            : inside && inside.length === 1
              ? p.s + " lies in " + H.townships[inside[0]] + " in the guide's data."
              : "The guide's data doesn't say which township " + p.s + " is in. Pick yours, or Not sure.";
        }
      }
    }
    var status = doc.getElementById("pick-status-text");
    if (status) status.textContent = state ? plainNames(state) : "No place picked yet";
    var clr = doc.getElementById("pick-clear");
    if (clr) clr.hidden = !state;
  }

  /* ------------------------------------------------------------ layer rows, counts, next ballot */
  function setText(sel, val) { each(doc.querySelectorAll(sel), function (el) { el.textContent = val; }); }
  function setHidden(sel, hide) { each(doc.querySelectorAll(sel), function (el) { el.hidden = hide; }); }

  function renderLayers() {
    var rows = doc.querySelectorAll(".layer[data-layer]");
    var items = doc.querySelectorAll(".gov-item[data-layer], .gov-site[data-layer]");
    if (!rows.length && !items.length) return;
    var p = placeOf(state);
    var t = state ? state.township : "any", s = state ? state.school : "any";
    var want = { "state": 1, "county": 1, "library": 1 };
    want["township:" + t] = 1;
    want["school:" + s] = 1;
    if (p && p.m) want["municipality:" + p.m] = 1;
    var here = p ? (p.m ? "municipality:" + p.m : "township:" + t) : "";
    var tot = { gov: 0, elected: 0, vote: 0, appointed: 0, unknown: 0, unknownApp: 0 };
    var next = {};
    each(rows, function (el) {
      var id = el.getAttribute("data-layer");
      var on = !!want[id];
      el.hidden = !on;
      el.classList.toggle("is-here", on && id === here);
      if (!on) return;
      tot.gov += +el.getAttribute("data-gov");
      tot.elected += +el.getAttribute("data-elected");
      tot.vote += +el.getAttribute("data-vote");
      tot.appointed += +el.getAttribute("data-appointed");
      tot.unknown += +el.getAttribute("data-unknown");
      tot.unknownApp += +(el.getAttribute("data-unknown-appointed") || 0);
      var nx = {};
      try { nx = JSON.parse(el.getAttribute("data-next") || "{}"); } catch (e) { nx = {}; }
      var title = (el.querySelector(".layer-title") || {}).textContent || "";
      Object.keys(nx).forEach(function (y) {
        next[y] = next[y] || [];
        nx[y].forEach(function (lab) { next[y].push(lab + " (" + title + ")"); });
      });
    });
    each(items, function (el) { el.hidden = !want[el.getAttribute("data-layer")]; });
    if (!rows.length) return;
    setText('[data-count="gov"]', tot.gov);
    setText('[data-count="elected"]', tot.elected);
    setText('[data-count="vote"]', tot.vote);
    setText('[data-count="appointed"]', tot.appointed);
    setHidden('[data-count="atleast-gov"], [data-count="noplace"]', !!p);
    setHidden('[data-count="noplace-alt"]', !p);   // "this place" once one is picked (counts moved to the picker, 2026-11-09)
    setHidden('[data-count="atleast"]', !!p && tot.unknown === 0);
    setHidden('[data-count="atleast-appointed"], [data-count="appointed-unknown-note"]', tot.unknownApp === 0);
    setText("[data-here-text]", p ? plainNames(state) : "the governments everyone in the county has (no place picked yet)");
    var years = Object.keys(next).sort(), ny = years[0];
    var yEl = doc.getElementById("next-year"), dEl = doc.getElementById("next-dates"), oEl = doc.getElementById("next-offices");
    var dates = layerData && layerData.dates ? layerData.dates : {};
    if (yEl) yEl.textContent = ny || "Not in data";
    if (dEl) dEl.textContent = ny && dates[ny] ? "Primary " + dates[ny].primary + DOT + "General " + dates[ny].general : "";
    if (oEl) oEl.textContent = ny ? next[ny].join("; ") : "";
  }

  /* ------------------------------------------------------------ markers on other pages */
  function renderMarkers() {
    var p = placeOf(state);
    var mine = {};
    if (p) {
      if (p.m) mine[p.m] = "Your place";
      if (state.township !== "any") mine[state.township] = mine[state.township] || "Your township";
      if (state.school !== "any") mine[state.school] = "Your school corporation";
    }
    each(doc.querySelectorAll("[data-here-unit]"), function (el) {
      var uid = el.getAttribute("data-here-unit");
      var label = mine[uid] || "";
      el.classList.toggle("is-here", !!label);
      var tag = el.querySelector(".here-tag");
      if (label) {
        if (!tag) {
          tag = doc.createElement("p");
          tag.className = "here-tag";
          el.insertBefore(tag, el.firstChild);
        }
        tag.textContent = label + " (saved on this device)";
      } else if (tag) {
        tag.parentNode.removeChild(tag);
      }
    });
    each(doc.querySelectorAll("[data-here-uninc]"), function (el) {
      el.classList.toggle("is-here", !!p && !p.m);
    });
    each(doc.querySelectorAll("[data-here-note]"), function (el) {
      if (!p) { el.hidden = true; return; }
      el.textContent = p.m
        ? "Your saved place is " + p.n + ". Its card is marked below if its offices are on this ballot."
        : "Your saved place is " + p.n + ", outside every city and town. See the paragraph marked below.";
      el.hidden = false;
    });
  }

  function renderAll() {
    renderBar();
    renderPicker();
    renderLayers();
    renderMarkers();
  }

  function choose(next, announce) {
    state = next;
    save(state);
    renderAll();
    try { doc.dispatchEvent(new CustomEvent("civic:place", { detail: state })); } catch (e) { /* old browser */ }
    if (announce) {
      var status = doc.getElementById("pick-status-text");
      if (status) status.textContent = state ? plainNames(state) : "No place picked yet";
    }
  }

  function pickPlace(id) {
    if (!has(H.places, id)) return;
    if (state && state.place === id) return;
    choose(fresh(id), true);
  }
  function pickTownship(v) {
    if (!state || placeOf(state).t) return;
    choose(normalize({ place: state.place, township: v, school: state.school, set: chosen("township") }), true);
  }
  /* the parts the reader has chosen, plus this one (a pick of "Not sure" is normalized away: "any" is never "set") */
  function chosen(part) {
    var set = (state && state.set ? state.set : []).filter(function (x) { return x !== part; });
    set.push(part);
    return set;
  }
  function pickSchool(v) {
    if (!state) return;
    choose(normalize({ place: state.place, township: state.township, school: v, set: chosen("school") }), true);
  }

  if (picker) {
    upgradeChoices();
    picker.addEventListener("click", function (ev) {
      var b = ev.target.closest ? ev.target.closest("button.choice[data-pick]") : null;
      if (b) {
        var kind = b.getAttribute("data-pick"), v = b.getAttribute("data-value");
        if (kind === "place") pickPlace(v);
        else if (kind === "township") pickTownship(v);
        else if (kind === "school") pickSchool(v);
        return;
      }
      if (ev.target.closest && ev.target.closest("#pick-clear")) {
        choose(null, true);
        var first = picker.querySelector("button.choice[data-pick='place']");
        if (first) first.focus();
      }
    });
    /* School buttons need a place first: say so instead of silently ignoring the press. */
    picker.addEventListener("click", function (ev) {
      var b = ev.target.closest ? ev.target.closest("button.choice[data-pick='school']") : null;
      if (b && !state) {
        var status = doc.getElementById("pick-status-text");
        if (status) status.textContent = "Pick your city, town or township first, then your school corporation.";
      }
    });
  }

  /* ------------------------------------------------------------ landing map as a picker */
  var pickMap = picker ? doc.querySelector(".pick .cmap") : null;
  if (pickMap) {
    var hint = pickMap.querySelector(".cmap-hint");
    if (hint) hint.textContent = "Point at or focus an area to see what the guide knows about it. Select it to pick it as your place; the Open page link goes to its page.";
    each(pickMap.querySelectorAll(".cmap-a"), function (a) {
      var uid = a.getAttribute("data-uid");
      var label = a.getAttribute("aria-label") || "";
      var what = has(H.schools, uid) ? "Pick as your school corporation." : "Pick as your place.";
      a.setAttribute("aria-label", label.replace("Open page.", what));
    });
    /* capture phase: runs before map.js, so a click picks instead of following the link; map.js still
       updates its panel. The panel's own Open page link is not a .cmap-a and keeps working. */
    doc.addEventListener("click", function (ev) {
      var a = ev.target.closest ? ev.target.closest(".pick .cmap-a") : null;
      if (!a) return;
      ev.preventDefault();
      var uid = a.getAttribute("data-uid");
      if (has(H.places, uid)) pickPlace(uid);
      else if (has(H.places, "unincorporated-" + uid)) pickPlace("unincorporated-" + uid);
      else if (has(H.schools, uid)) {
        if (state) pickSchool(uid);
        else {
          var st = doc.getElementById("pick-status-text");
          if (st) st.textContent = "Pick your city, town or township first, then your school corporation.";
        }
      }
    }, true);
    /* map.js rewrites the address hash to its layer name on load; keep the address the reader came with */
    var hash0 = window.location.hash;
    window.setTimeout(function () {
      if (window.location.hash === hash0) return;
      try { history.replaceState(null, "", window.location.href.split("#")[0] + hash0); } catch (e) { /* ignore */ }
    }, 0);
  }

  renderAll();

  /* ------------------------------------------------------------ saved-place preselect (added 2026-11-09, Wave E batch 8)
     window.civicHere lets a page open on the reader's saved place (civic/preselect.py, static/js/preselect.js, and
     the results explorer and tax bill in elections.js / money.js). Contract:
       civicHere.mine()        null with no saved place; else {place, muni, townships, township, school, defaults, label,
                               names, wants(layerKey), sure(layerKey)}: the saved place's governments. township and
                               school are only what the reader chose ("set"; an unincorporated place's own township is
                               certain); a default stored with the place is in defaults and never treated as theirs.
                               An unknown township stands for every township the city lies in; an unknown school
                               corporation for every one, so nothing that may be the reader's is ever left out.
       civicHere.hashWins()    true when the reader came with an explicit #anchor (not a map layer name): the page
                               then opens as the link says and the line only offers the saved place.
       civicHere.line(slot, o) renders the visible "Showing: ..." line in a placeholder (civic/preselect.py here_slot)
                               and returns {set(state), state()}: "on" (o.apply has run; the button undoes it),
                               "off" (an offer: the button applies it) or "note" (text only, o.note).
     Nothing is written anywhere: the saved place stays in localStorage "civic-place", never in the address. */
  function mine() {
    var p = placeOf(state);
    if (!p) return null;
    /* only what the reader chose counts (state.set); a default filled in when the place was chosen does not */
    var set = state.set || [];
    var tw = p.t || (set.indexOf("township") >= 0 && state.township !== "any" ? state.township : "");
    var school = set.indexOf("school") >= 0 && state.school !== "any" ? state.school : "";
    var ts = [];
    if (tw) ts = [tw];
    else ts = p.it && p.it.length ? p.it.slice() : Object.keys(H.townships);
    var names = [];
    names.push(p.n);
    if (!p.t) {
      if (tw) names.push(H.townships[tw]);
      else names.push(ts.length === 1 ? H.townships[ts[0]] : "the " + ts.length + " townships " + p.s + " lies in (township not chosen)");
    }
    names.push(school ? H.schools[school] : "every school corporation (none chosen)");
    return {
      place: state.place, muni: p.m || "", township: tw, townships: ts, school: school,
      /* the guide's defaults still stored with the place: may order choices, never decide anything */
      defaults: { township: !tw && state.township !== "any" ? state.township : "",
                  school: !school && state.school !== "any" ? state.school : "" },
      label: p.n, short: p.s, names: names,
      wants: function (layer) {
        if (!layer) return true;                      /* a row the build could not place: never hidden */
        var i = layer.indexOf(":"), kind = i < 0 ? layer : layer.slice(0, i), id = i < 0 ? "" : layer.slice(i + 1);
        if (kind === "municipality") return id === p.m;
        if (kind === "township") return ts.indexOf(id) >= 0;
        if (kind === "school") return !school || id === school;
        return true;                                  /* county, state, library (service areas are not mapped) */
      },
      /* stricter: the layer is certainly the reader's (a township or school corporation that was not picked never
         is). For highlighting, where "may be yours" would only add noise. */
      sure: function (layer) {
        if (!layer) return false;
        var i = layer.indexOf(":"), kind = i < 0 ? layer : layer.slice(0, i), id = i < 0 ? "" : layer.slice(i + 1);
        if (kind === "municipality") return id === p.m;
        if (kind === "township") return ts.length === 1 && ts[0] === id;
        if (kind === "school") return !!school && id === school;
        return kind === "county" || kind === "state";
      }
    };
  }
  function hashWins() {
    var hsh = HASH0 || window.location.hash || "";
    if (hsh.length < 2) return false;
    var id = hsh.slice(1);
    try { id = decodeURIComponent(id); } catch (e) { /* keep the raw id */ }
    var layer = false;
    each(doc.querySelectorAll(".cmap-tab[data-layer]"), function (b) { if (b.getAttribute("data-layer") === id) layer = true; });
    return !layer;
  }
  function line(slot, o) {
    if (!slot) return null;
    var cur = "";
    clear(slot);
    var label = doc.createElement("span");
    label.className = "here-pre-label";
    var text = doc.createElement("span");
    text.className = "here-pre-text";
    var btn = doc.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-small here-pre-btn";
    var why = doc.createElement("span");
    why.className = "here-pre-why";
    slot.appendChild(label);
    slot.appendChild(text);
    slot.appendChild(doc.createTextNode(" "));
    slot.appendChild(btn);
    slot.appendChild(why);
    function set(s) {
      cur = s;
      if (s === "on") {
        label.textContent = (o.onLabel || "Showing") + ": ";
        text.textContent = o.onText;
        btn.textContent = o.undoLabel || "Show all";
        why.textContent = o.onWhy || " From your saved place, kept on this device only.";
      } else if (s === "off") {
        label.textContent = (o.offLabel || "Your saved place") + ": ";
        text.textContent = o.offText || o.onText;
        btn.textContent = o.applyLabel || "Show only these";
        why.textContent = o.offWhy || "";
      } else {
        label.textContent = (o.noteLabel || "Your saved place") + ": ";
        text.textContent = o.note || "";
        why.textContent = o.noteWhy || "";
      }
      btn.hidden = s === "note";
      slot.classList.toggle("is-on", s === "on");
      slot.hidden = false;
    }
    btn.addEventListener("click", function () {
      if (cur === "on") { if (o.undo) o.undo(); set("off"); }
      else if (cur === "off") { if (o.apply) o.apply(); set("on"); }
    });
    slot.setAttribute("role", "status");
    return { set: set, state: function () { return cur; } };
  }
  window.civicHere = { mine: mine, hashWins: hashWins, line: line };

  /* another tab changed the place: follow it */
  window.addEventListener("storage", function (ev) {
    if (ev.key !== KEY) return;
    state = load();
    renderAll();
  });
})();
