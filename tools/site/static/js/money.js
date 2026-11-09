/* Money section scripts. Plain JS, ASCII only. Data is inserted with textContent only.
   1. money/your-tax-bill/: the page already shows the default district and unit split without JS;
      this redraws them when the reader changes a picker.
   2. money/budgets/: the nominal / constant-dollar toggle for the budget charts (both versions are
      rendered by the build; this only shows one and hides the other). */
(function () {
  "use strict";
  var doc = document;

  function store(key, val) {
    try {
      if (val === undefined) return window.localStorage.getItem(key);
      window.localStorage.setItem(key, val);
    } catch (e) { /* conveniences only */ }
    return null;
  }
  function el(tag, cls, text) {
    var e = doc.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }
  function has(o, k) { return Object.prototype.hasOwnProperty.call(o, k); }

  /* ------------------------------------------------------------ 2. dollars toggle */
  (function () {
    var box = doc.getElementById("mn-dollars-toggle");
    if (!box) return;
    var radios = Array.prototype.slice.call(box.querySelectorAll("input[name='mn-dollars']"));
    var blocks = Array.prototype.slice.call(doc.querySelectorAll("[data-dollars]"));
    function apply(mode) {
      blocks.forEach(function (b) { b.hidden = b.getAttribute("data-dollars") !== mode; });
      radios.forEach(function (r) { r.checked = r.value === mode; });
      store("civic-dollars", mode);
    }
    radios.forEach(function (r) { r.addEventListener("change", function () { if (r.checked) apply(r.value); }); });
    box.hidden = false;
    var saved = store("civic-dollars");
    apply(saved === "real" ? "real" : "nominal");
  })();

  /* ------------------------------------------------------------ 1. tax bill */
  var dataEl = doc.getElementById("taxbill-data");
  var out = doc.getElementById("tb-out");
  var dOut = doc.getElementById("tb-district-out");
  if (!dataEl || !out || !dOut) return;
  var data;
  try { data = JSON.parse(dataEl.textContent); } catch (e) { return; }
  var sel = {
    district: doc.getElementById("tb-district"),
    year: doc.getElementById("tb-year"),
    place: doc.getElementById("tb-place"),
    township: doc.getElementById("tb-township"),
    school: doc.getElementById("tb-school"),
    library: doc.getElementById("tb-library")
  };
  for (var k in sel) { if (has(sel, k) && !sel[k]) return; }
  var specials = Array.prototype.slice.call(doc.querySelectorAll("input[data-special]"));
  var picker = doc.getElementById("tb-picker");
  var places = {}, districts = {};
  data.places.forEach(function (p) { places[p.id] = p; });
  data.districts.forEach(function (d) { districts[d.code] = d; });
  var SEGS = 6;
  var DOT = " " + String.fromCharCode(183) + " ";

  function hasOption(s, v) {
    for (var i = 0; i < s.options.length; i++) if (s.options[i].value === v) return true;
    return false;
  }
  function setSel(s, v) { if (v !== undefined && v !== null && hasOption(s, v)) s.value = v; }
  function scaleFor(v) { return Math.max(3, Math.ceil(v * 2) / 2 + 0.5); }
  function caps(bar, scale) {
    [[1, "1% cap"], [2, "2%"], [3, "3%"]].forEach(function (c) {
      var m = el("span", "mn-tb-cap");
      m.style.left = (c[0] / scale * 100).toFixed(2) + "%";
      m.appendChild(el("span", "mn-tb-cap-l mono", c[1]));
      bar.appendChild(m);
    });
  }
  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

  /* same wording as _rate_compare_text in tools/site/pages/money.py */
  function rateCompare(total, n, district, year) {
    if (district === null) return "The guide has no certified rate for this taxing district in " + year + ".";
    if (!n) return "Pick the units that tax the property to see how the district's rate is shared among them.";
    var diff = total - district;
    if (Math.abs(diff) < 0.00005) {
      return "The certified rates of the units picked add up to the district's certified rate ($" + district.toFixed(4) + ").";
    }
    return "The unit-wide certified rates of the units picked add up to $" + total.toFixed(4) + ", which is $" +
      Math.abs(diff).toFixed(4) + " " + (diff > 0 ? "more" : "less") + " than the district's certified rate of $" +
      district.toFixed(4) + ". The guide doesn't have the state's breakdown of each unit's rate within this district for " +
      year + ".";
  }

  /* same wording as _composition_text in tools/site/pages/money.py; differ: [[label, rate here, unit-wide rate]] */
  function compositionText(total, district, differ) {
    var outT = [];
    if (district !== null && Math.abs(total - district) < 0.00005) {
      outT.push("These unit rates add up to the district's certified rate ($" + district.toFixed(4) + ").");
    } else if (district !== null) {
      outT.push("These unit rates add up to $" + total.toFixed(4) + "; the district's certified rate is $" + district.toFixed(4) + ".");
    }
    if (differ.length) {
      outT.push("In this district the state lists some units at a rate other than their unit-wide certified rate: " +
        differ.map(function (x) { return x[0] + " $" + x[1].toFixed(4) + " here ($" + x[2].toFixed(4) + " unit-wide)"; }).join("; ") +
        ". A unit's rate in a district is the sum of the funds it levies there.");
    }
    return outT;
  }

  /* the state's per-district breakdown for the district and year chosen, or null */
  function composition() {
    var d = districts[sel.district.value];
    var y = sel.year.value;
    return d && d.units && has(d.units, y) && d.units[y].length ? d.units[y] : null;
  }

  function renderComposition(parts, year) {
    var d = districts[sel.district.value];
    var dr = districtRate();
    var total = 0;
    parts.forEach(function (p) { total += p[1]; });
    var scale = scaleFor(Math.max(total, dr || 0));
    clear(out);
    var p = el("p", "mn-tb-total");
    p.appendChild(el("span", "mono", year + " certified rates of the units that tax district " + d.code + " " + d.name + ": "));
    p.appendChild(el("strong", "mn-tb-sum", "$" + total.toFixed(4)));
    p.appendChild(doc.createTextNode(" per $100 of assessed value"));
    out.appendChild(p);
    var bar = el("div", "mn-tb-bar");
    bar.setAttribute("role", "img");
    bar.setAttribute("aria-label", "Stacked bar: district " + d.code + " units total $" + total.toFixed(4) +
      " per $100, split among the units listed below");
    var list = el("ul", "mn-tb-list");
    var differ = [];
    parts.forEach(function (pair, k) {
      var u = data.units[pair[0]] || { label: pair[0], role: "Unit", cert: {} };
      var r = pair[1];
      var share = total ? r / total * 100 : 0;
      var cls = "mn-seg-" + (k % SEGS);
      var seg = el("span", "mn-tb-seg " + cls);
      seg.style.width = (r / scale * 100).toFixed(2) + "%";
      seg.title = u.label + ": $" + r.toFixed(4) + " per $100 (" + share.toFixed(1) + "% of the district's rate)";
      bar.appendChild(seg);
      var li = el("li", "mn-tb-item");
      var key = el("span", "mn-tb-key " + cls);
      key.setAttribute("aria-hidden", "true");
      li.appendChild(key);
      li.appendChild(el("span", "mn-tb-role mono", u.role));
      li.appendChild(el("span", "mn-tb-name", u.label));
      li.appendChild(el("span", "mn-tb-val mono", "$" + r.toFixed(4) + DOT + share.toFixed(1) + "%"));
      list.appendChild(li);
      if (has(u.cert, year) && Math.abs(u.cert[year] - r) >= 0.00005) differ.push([u.label, r, u.cert[year]]);
    });
    caps(bar, scale);
    out.appendChild(bar);
    out.appendChild(list);
    compositionText(total, dr, differ).forEach(function (t) { out.appendChild(el("p", "mn-tb-compare", t)); });
  }

  function districtRate() {
    var d = districts[sel.district.value];
    var y = sel.year.value;
    return d && has(d.rates, y) ? d.rates[y] : null;
  }

  function renderDistrict() {
    var d = districts[sel.district.value];
    var year = sel.year.value;
    clear(dOut);
    if (!d) return;
    var r = has(d.rates, year) ? d.rates[year] : null;
    if (r === null) {
      dOut.appendChild(el("p", "mn-tb-total", "No certified rate in the guide's data for district " + d.code + " in " + year + "."));
      return;
    }
    var scale = scaleFor(r);
    var p = el("p", "mn-tb-total");
    p.appendChild(el("span", "mono", year + " certified rate, district " + d.code + " " + d.name + ": "));
    p.appendChild(el("strong", "mn-tb-sum", "$" + r.toFixed(4)));
    p.appendChild(doc.createTextNode(" per $100 of assessed value"));
    dOut.appendChild(p);
    var bar = el("div", "mn-tb-bar");
    bar.setAttribute("role", "img");
    bar.setAttribute("aria-label", "Bar: certified district rate $" + r.toFixed(4) + " per $100, with the 1%, 2% and 3% cap marks");
    var seg = el("span", "mn-tb-seg mn-seg-0");
    seg.style.width = (r / scale * 100).toFixed(2) + "%";
    bar.appendChild(seg);
    caps(bar, scale);
    dOut.appendChild(bar);
    var other = Object.keys(d.rates).filter(function (y) { return y !== year; }).sort().reverse()
      .map(function (y) { return y + ": $" + d.rates[y].toFixed(4); });
    if (other.length) dOut.appendChild(el("p", "muted mn-tb-other", other.join("; ")));
  }

  /* The reader's own choices on this page, saved only when the reader changes a picker (v3, 2026-11-09: v2 was also
     written on every load, so a first visit's example district hid the saved place on every later visit). */
  var TB_KEY = "civic-taxbill-v3";
  function saveState() {
    var spec = specials.filter(function (c) { return c.checked; }).map(function (c) { return c.value; });
    store(TB_KEY, JSON.stringify({ district: sel.district.value, year: sel.year.value, place: sel.place.value,
      township: sel.township.value, school: sel.school.value, library: sel.library.value, specials: spec }));
  }

  function renderUnits() {
    var year = sel.year.value;
    var comp = composition();
    if (picker) picker.hidden = !!comp;
    if (comp) { renderComposition(comp, year); return; }
    var place = places[sel.place.value] || {};
    var chosen = [["county-st-joseph", "County"]];
    if (place.muni) chosen.push([place.muni, "City or town"]);
    chosen.push([sel.township.value, "Township"], [sel.school.value, "School corporation"], [sel.library.value, "Library"]);
    specials.forEach(function (c) { if (c.checked) chosen.push([c.value, "Special unit"]); });
    var items = [], total = 0, n = 0;
    chosen.forEach(function (pair) {
      var mid = pair[0], role = pair[1];
      if (!mid || mid.indexOf("none:") === 0) {
        items.push({ role: role, label: null, rate: null, missing: mid ? "No certified rate in the guide's data" : "Not chosen" });
        return;
      }
      var u = data.units[mid];
      if (!u) return;
      var r = has(u.cert, year) ? u.cert[year] : null;
      items.push({ role: role, label: u.label, rate: r, missing: r === null ? "No certified rate in the guide's data for " + year : null });
      if (r !== null) { total += r; n += 1; }
    });
    var dr = districtRate();
    var scale = scaleFor(Math.max(total, dr || 0));
    clear(out);
    var p = el("p", "mn-tb-total");
    p.appendChild(el("span", "mono", year + " certified rates of the units picked: "));
    p.appendChild(el("strong", "mn-tb-sum", "$" + total.toFixed(4)));
    p.appendChild(doc.createTextNode(" per $100 of assessed value"));
    out.appendChild(p);
    var bar = el("div", "mn-tb-bar");
    bar.setAttribute("role", "img");
    bar.setAttribute("aria-label", "Stacked bar: units picked total $" + total.toFixed(4) + " per $100, split among the units listed below");
    var list = el("ul", "mn-tb-list");
    var k = 0;
    items.forEach(function (it) {
      var li;
      if (it.rate === null) {
        li = el("li", "mn-tb-item mn-tb-missing");
        var kn = el("span", "mn-tb-key mn-tb-key-none");
        kn.setAttribute("aria-hidden", "true");
        li.appendChild(kn);
        li.appendChild(el("span", "mn-tb-role mono", it.role));
        li.appendChild(el("span", "mn-tb-name", it.label || it.missing));
        li.appendChild(el("span", "mn-tb-val", it.label ? it.missing : ""));
        list.appendChild(li);
        return;
      }
      var share = total ? it.rate / total * 100 : 0;
      var cls = "mn-seg-" + (k % SEGS);
      var seg = el("span", "mn-tb-seg " + cls);
      seg.style.width = (it.rate / scale * 100).toFixed(2) + "%";
      seg.title = it.label + ": $" + it.rate.toFixed(4) + " per $100 (" + share.toFixed(1) + "% of the units picked)";
      bar.appendChild(seg);
      li = el("li", "mn-tb-item");
      var key = el("span", "mn-tb-key " + cls);
      key.setAttribute("aria-hidden", "true");
      li.appendChild(key);
      li.appendChild(el("span", "mn-tb-role mono", it.role));
      li.appendChild(el("span", "mn-tb-name", it.label));
      li.appendChild(el("span", "mn-tb-val mono", "$" + it.rate.toFixed(4) + DOT + share.toFixed(1) + "%"));
      list.appendChild(li);
      k += 1;
    });
    caps(bar, scale);
    out.appendChild(bar);
    out.appendChild(list);
    out.appendChild(el("p", "mn-tb-compare", rateCompare(total, n, dr, year)));
  }

  function render() { renderDistrict(); renderUnits(); }

  /* fill the unit pickers with what the district's name states; leave the rest to the reader */
  function applyDistrict() {
    var d = districts[sel.district.value];
    if (!d) return;
    var pre = d.pre || {};
    sel.place.value = hasOption(sel.place, pre.place || "") ? (pre.place || "") : "";
    var place = places[sel.place.value] || {};
    sel.township.value = hasOption(sel.township, pre.township || place.township || "") ? (pre.township || place.township || "") : "";
    var school = pre.school || place.school || "";
    sel.school.value = hasOption(sel.school, school) ? school : "";
    sel.library.value = "";
    specials.forEach(function (c) { c.checked = false; });
  }
  function applyPlace() {
    var place = places[sel.place.value];
    if (!place) return;
    if (place.township) setSel(sel.township, place.township);
    if (place.school) setSel(sel.school, place.school);
  }

  sel.district.addEventListener("change", function () { applyDistrict(); render(); saveState(); });
  sel.year.addEventListener("change", function () { render(); saveState(); });
  sel.place.addEventListener("change", function () { applyPlace(); renderUnits(); saveState(); });
  ["township", "school", "library"].forEach(function (k2) {
    sel[k2].addEventListener("change", function () { renderUnits(); saveState(); });
  });
  specials.forEach(function (c) { c.addEventListener("change", function () { renderUnits(); saveState(); }); });

  var saved = null;
  try { saved = JSON.parse(store(TB_KEY) || "null"); } catch (e) { saved = null; }
  if (saved && districts[saved.district]) {
    setSel(sel.district, saved.district);
    setSel(sel.year, saved.year);
    setSel(sel.place, saved.place);
    setSel(sel.township, saved.township);
    setSel(sel.school, saved.school);
    setSel(sel.library, saved.library);
    specials.forEach(function (c) { c.checked = (saved.specials || []).indexOf(c.value) >= 0; });
  }
  render();

  /* ------------------------------------------------------------ saved-place preselect (Wave E batch 8, 2026-11-09)
     With no choice of the reader's own saved on this page, start from the saved place (here.js window.civicHere):
     pick its taxing district only when exactly one district fits it, by the district names and the state's
     per-district breakdown (data.hints, civic/preselect.py district_hints and tax_district_for_saved, the same rule).
     Only the township and school the reader chose count; the defaults here.js stored with the place only order the
     choices (Wave E batch 8 part 2).
     Otherwise list the districts that fit and leave the page's example selected. Never guessed; nothing stored. */
  function fromPlace(m) {
    var hints = data.hints || {};
    var cands = data.districts.filter(function (d) { return (d.pre || {}).place === m.place; })
      .map(function (d) { return d.code; });
    if (!cands.length) return null;
    function h(c) { return hints[c] || { tw: [], sc: [] }; }
    if (m.township) {
      cands = cands.filter(function (c) { return !h(c).tw.length || h(c).tw.indexOf(m.township) >= 0; });
      if (!cands.length) return null;
    }
    if (m.school) {
      var ok = cands.filter(function (c) { return !h(c).sc.length || h(c).sc.indexOf(m.school) >= 0; });
      if (!ok.length) return { choices: cands, why: "conflict", fit_default: [] };
      cands = ok;
    }
    if (cands.length === 1) return { code: cands[0] };
    var tws = {};
    cands.forEach(function (c) { tws[h(c).tw.join(",")] = true; });
    var why = Object.keys(tws).length > 1 && !m.township ? "township" : "school";
    /* the guide's defaults stored with the place (not chosen by the reader) only order the choices */
    var dt = (m.defaults || {}).township || "", ds = (m.defaults || {}).school || "";
    var fit = [];
    if (dt || ds) {
      fit = cands.filter(function (c) {
        return (!dt || !h(c).tw.length || h(c).tw.indexOf(dt) >= 0) && (!ds || !h(c).sc.length || h(c).sc.indexOf(ds) >= 0);
      });
      if (fit.length === cands.length) fit = [];
    }
    return { choices: fit.concat(cands.filter(function (c) { return fit.indexOf(c) < 0; })), why: why, fit_default: fit };
  }
  function districtName(c) { return districts[c] ? c + " " + districts[c].name : c; }
  function preselect() {
    var slot = doc.querySelector('[data-here-pre="taxbill"]');
    if (!slot || !window.civicHere || saved) return;
    var m = window.civicHere.mine();
    if (!m) return;
    var r = fromPlace(m);
    var who = m.names.join(DOT);
    if (!r) return;
    if (r.code) {
      var example = sel.district.value;
      var exYear = sel.year.value;
      var useIt = function () { setSel(sel.district, r.code); applyDistrict(); render(); };
      var ctl = window.civicHere.line(slot, {
        onLabel: "From your saved place",
        onText: "district " + districtName(r.code),
        onWhy: " The only district whose name and state listing fit " + who + " (kept on this device only). Your tax " +
               "bill names your district: pick another above if it differs.",
        offLabel: "Your saved place fits",
        offText: "district " + districtName(r.code),
        applyLabel: "Show it",
        /* when the page's example is the reader's district too, there is nothing to go back to: offer the picker */
        undoLabel: r.code === example ? "Pick another district" : "Show the example district",
        apply: useIt,
        undo: function () {
          if (r.code === example) { sel.district.focus(); return; }
          setSel(sel.district, example); setSel(sel.year, exYear); applyDistrict(); render();
        }
      });
      sel.district.addEventListener("change", function () {
        if (sel.district.value === r.code) { if (ctl.state() !== "on") ctl.set("on"); }
        else if (ctl.state() === "on") ctl.set("off");
      });
      if (window.civicHere.hashWins()) ctl.set("off");
      else { useIt(); ctl.set("on"); }
      return;
    }
    /* more than one district fits: say which, and let the reader pick (buttons set the district picker) */
    clear(slot);
    var lab = el("span", "here-pre-label", "Your saved place: ");
    slot.appendChild(lab);
    var why = r.why === "township"
      ? " could be in any of these districts; the guide can't tell which without your township" +
        (m.school ? "" : " and school corporation") + ". Your tax bill names it:"
      : r.why === "conflict"
        ? " fits these districts by township, but the state lists another school corporation in them than the one " +
          "you chose. Your tax bill names your district:"
        : " could be in any of these districts (they differ by school corporation). Your tax bill names it:";
    slot.appendChild(el("span", "here-pre-text", who + why));
    var ul = el("ul", "here-pre-choices");
    r.choices.forEach(function (c) {
      var li = el("li");
      var b = el("button", "btn btn-small here-pre-btn", districtName(c));
      b.type = "button";
      b.addEventListener("click", function () {
        setSel(sel.district, c); applyDistrict(); render(); saveState();
        note.textContent = "Showing district " + districtName(c) + ".";
      });
      li.appendChild(b);
      ul.appendChild(li);
    });
    slot.appendChild(ul);
    if (r.fit_default && r.fit_default.length) {
      slot.appendChild(el("span", "here-pre-why", "Listed first: the district" +
        (r.fit_default.length > 1 ? "s that fit" : " that fits") + " the guide's usual " + (m.defaults.school ? "school corporation" : "township") + " for " + m.label +
        ", which you have not chosen; your address may be in any of these districts."));
    }
    var note = el("span", "here-pre-why", "The district shown below is the page's example, " +
      districtName(sel.district.value) + ", not a match for your place.");
    slot.appendChild(note);
    sel.district.addEventListener("change", function () {
      note.textContent = "Showing district " + districtName(sel.district.value) + ".";
    });
    slot.setAttribute("role", "status");
    slot.hidden = false;
  }
  /* app.js is deferred: it runs while readyState is "interactive", before DOMContentLoaded, and before the later
     partials (here.js, tablefilter.js) have set up; so wait for DOMContentLoaded unless the page is already complete */
  if (doc.readyState !== "complete") doc.addEventListener("DOMContentLoaded", preselect);
  else preselect();
})();
