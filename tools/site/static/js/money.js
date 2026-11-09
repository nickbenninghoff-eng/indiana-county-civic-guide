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

  function saveState() {
    var spec = specials.filter(function (c) { return c.checked; }).map(function (c) { return c.value; });
    store("civic-taxbill-v2", JSON.stringify({ district: sel.district.value, year: sel.year.value, place: sel.place.value,
      township: sel.township.value, school: sel.school.value, library: sel.library.value, specials: spec }));
  }

  function renderUnits() {
    var year = sel.year.value;
    var comp = composition();
    if (picker) picker.hidden = !!comp;
    if (comp) { renderComposition(comp, year); saveState(); return; }
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
    saveState();
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

  sel.district.addEventListener("change", function () { applyDistrict(); render(); });
  sel.year.addEventListener("change", render);
  sel.place.addEventListener("change", function () { applyPlace(); renderUnits(); });
  ["township", "school", "library"].forEach(function (k2) { sel[k2].addEventListener("change", renderUnits); });
  specials.forEach(function (c) { c.addEventListener("change", renderUnits); });

  var saved = null;
  try { saved = JSON.parse(store("civic-taxbill-v2") || "null"); } catch (e) { saved = null; }
  if (saved && districts[saved.district]) {
    setSel(sel.district, saved.district);
    setSel(sel.year, saved.year);
    setSel(sel.place, saved.place);
    setSel(sel.township, saved.township);
    setSel(sel.school, saved.school);
    setSel(sel.library, saved.library);
    specials.forEach(function (c) { c.checked = (saved.specials || []).indexOf(c.value) >= 0; });
  } else {
    /* No tax-bill choice saved yet: start from the reader's saved place (here.js, localStorage
       "civic-place", unit ids). Pick the district whose name states that place, preferring the one
       that also states the saved township or school; fill only what the district name leaves open. */
    var cp = null;
    try { cp = JSON.parse(store("civic-place") || "null"); } catch (e) { cp = null; }
    var um = data.uidmap || {};
    if (cp && places[cp.place]) {
      var town = cp.township && um[cp.township] ? um[cp.township] : (places[cp.place].township || "");
      var school = cp.school && um[cp.school] ? um[cp.school] : "";
      var best = null;
      data.districts.forEach(function (d) {
        var pre = d.pre || {};
        if (pre.place !== cp.place) return;
        var score = 1 + (town && pre.township === town ? 2 : 0) + (school && pre.school === school ? 1 : 0);
        if (!best || score > best[0]) best = [score, d];
      });
      var pre0 = {};
      if (best) { setSel(sel.district, best[1].code); applyDistrict(); pre0 = best[1].pre || {}; }
      else { setSel(sel.place, cp.place); applyPlace(); }
      if (town && !pre0.township) setSel(sel.township, town);
      if (school && !pre0.school) setSel(sel.school, school);
    }
  }
  render();
})();
