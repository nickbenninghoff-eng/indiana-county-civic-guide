/* "How areas voted" layer of the boundary map (civic/map.py vote_* helpers). The race data is a separate file,
   assets/map-votes.json (its address is in .cmap-vctl[data-src]), loaded the first time the layer is opened.
   Race picker: Level (buttons) -> Office (select) -> District, township or town (select, for offices elected in part
   of the county) -> Year (buttons, only years with results for that office). Without JavaScript this layer is not shown; the tables under the map have
   every race's county total and the default race by area. */
(function () {
  var doc = document;
  var root = doc.querySelector(".cmap");
  if (!root) return;
  var ctl = root.querySelector(".cmap-vctl");
  if (!ctl) return;
  var UD = {};
  try { UD = JSON.parse(doc.getElementById("cmap-data").textContent); } catch (e) { return; }
  var svg = root.querySelector(".cmap-svg");
  var panel = doc.getElementById("cmap-panel");
  var hlg = svg.querySelector(".cmap-hl-g");
  var drill = root.querySelector(".cmap-drill");
  var legend = doc.querySelector('.cmap-legend[data-layer="votes"]');
  var uncNote = doc.querySelector(".cmap-vunc");
  var jsTables = doc.querySelector(".cmap-vjs");
  var noJs = doc.querySelector(".cmap-nojs");
  var officeSel = doc.getElementById("cmap-office");
  var distSel = doc.getElementById("cmap-district");
  var distWrap = ctl.querySelector(".cmap-vf-district");
  var yearSeg = ctl.querySelector('[data-role="year"]');
  var NS = "http://www.w3.org/2000/svg";
  var CAVEAT = "Past results for this race only. They show how votes were cast here, not how any person or future election will go.";
  var PARTY = { D: "Democratic", L: "Libertarian", R: "Republican" };
  var IDX = { D: 0, R: 1, L: 2, O: 3, W: 4 };
  var GEO_NAME = { township: "Townships", place: "Cities and towns", precinct: "Precincts" };
  var V = null, RACE = {}, loading = false, failed = false;
  var PVIEW = true;
  var state = { level: null, office: null, district: null, year: null, race: null, geo: "township",
                drill: null, sel: null, last: null, active: false };
  // sel: an area chosen by click or tap. last: the area most recently hovered or focused; the panel keeps
  // showing it after the pointer leaves the map, until another area is hovered or the view changes.
  var touch = false;

  function el(tag, cls, text) {
    var e = doc.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }
  function n(v) { return Number(v).toLocaleString("en-US"); }
  function share(part, tot) { var x = tot ? part / tot * 100 : 0; return x > 0 && x < 0.05 ? "under 0.1%" : x.toFixed(1) + "%"; }
  function race() { return RACE[state.race]; }
  function office(key) { for (var i = 0; i < V.offices.length; i++) if (V.offices[i].key === key) return V.offices[i]; return null; }
  function racesOf(off, dist) {
    return V.races.filter(function (r) { return r.office === off && (r.district || null) === (dist || null); });
  }
  function yearsOf(off, dist) { return racesOf(off, dist).map(function (r) { return r.year; }).sort(function (a, b) { return b - a; }); }
  function vals(geo, key, rid) {
    var rec = geo === "precinct" ? V.precinct[key] : V[geo][key];
    return rec && rec.v ? rec.v[rid || state.race] || null : null;
  }
  function total(v) { return v[0] + v[1] + v[2] + v[3] + v[4]; }
  // the race's two leading parties, alphabetical (D, L, R; other parties last); [p, null] when uncontested
  function sides(r) {
    var p = r.pair.slice().sort(function (x, y) { return ((x === "O") - (y === "O")) || (x < y ? -1 : x > y ? 1 : 0); });
    return [p[0], p.length > 1 ? p[1] : null];
  }
  function pname(r, p) { return p === "O" ? (r.oparty || "Other party") : (PARTY[p] || p); }
  function cls(p) { return p === "D" ? "d" : (p === "R" ? "r" : "o"); }
  function code(p) { return p === "O" ? "Other" : p; }
  function marginPts(r, v) {
    var s = sides(r);
    if (!s[1]) return null;
    var a = v[IDX[s[0]]], b = v[IDX[s[1]]];
    return a + b ? (a - b) / (a + b) * 100 : null;
  }
  function marginText(r, v) {
    var s = sides(r);
    if (!s[1]) return "uncontested";
    var p = marginPts(r, v);
    if (p === null) return "no votes for either";
    if (Math.abs(p) < 0.05) return "Even";
    return code(p > 0 ? s[0] : s[1]) + " +" + Math.abs(p).toFixed(1);
  }
  function marginLabel(r) {
    var s = sides(r);
    if (!s[1]) return "Margin";
    return (s[0] === "D" && s[1] === "R") ? "Two-party margin" : "Margin (" + s[0] + " and " + s[1] + ")";
  }
  // did this area have precincts in the race's election year (so a missing result means "not on this ballot")?
  function existed(geo, key, r) {
    if (geo === "precinct") { var p = V.precinct[key]; return !!(p && p.e && p.e.indexOf(r.year) >= 0); }
    var e = V[geo][key];
    return !!(e && e.n && e.n[String(r.year)]);
  }
  function band(geo, key) {
    var r = race(), v = vals(geo, key);
    if (!v) return r.district && existed(geo, key, r) ? "cmap-vb-off" : "cmap-vb-none";
    var s = sides(r);
    if (!s[1]) return v[IDX[s[0]]] > 0 ? "cmap-vb-" + cls(s[0]) + "3" : "cmap-vb-none";
    var p = marginPts(r, v);
    if (p === null) return "cmap-vb-none";
    var a = Math.abs(p);
    if (a < V.bands[0]) return "cmap-vb-even";
    var k = a < V.bands[1] ? 1 : (a < V.bands[2] ? 2 : 3);
    return "cmap-vb-" + cls(p > 0 ? s[0] : s[1]) + k;
  }
  function nameOf(geo, key) {
    if (geo === "precinct") { var p = V.precinct[key]; return p ? p.n + " (" + key + ")" : key; }
    return UD[key] ? UD[key].n : key;
  }
  // the area a district, township or town race is limited to ("State Senate, District 8", "Centre Township",
  // "the town of Walkerton"), and the word for it
  function distName(r) { return r.area || (office(r.office).label + ", District " + r.district); }
  function unitWord(r) { return r.unit === "ward" ? "town" : (r.unit || "district"); }

  // ---------------------------------------------------------------- map colors and highlight
  function recolor() {
    each(svg.querySelectorAll(".cmap-va"), function (a) {
      var geo = a.getAttribute("data-vgeo"), key = a.getAttribute("data-vkey");
      var b = band(geo, key);
      a.querySelector("path").setAttribute("class", "cmap-s cmap-v " + b);
      var dot = a.querySelector(".cmap-v-dot");
      if (dot) dot.setAttribute("class", "cmap-dot cmap-v-dot " + b);
      var dim = false;
      if (geo === "precinct" && state.drill) {
        dim = (state.drill.kind === "township" ? a.getAttribute("data-t") : a.getAttribute("data-p")) !== state.drill.key;
      }
      a.classList.toggle("is-dim", dim);
      if (dim) a.setAttribute("tabindex", "-1"); else a.removeAttribute("tabindex");
    });
    each(svg.querySelectorAll(".cmap-vg"), function (g) {
      g.classList.toggle("is-on", g.getAttribute("data-vsub") === state.geo);
    });
  }
  function clearHl() { while (hlg.firstChild) hlg.removeChild(hlg.firstChild); }
  function hl(a, focus) {
    clearHl();
    var src = a && a.querySelector("path");
    if (!src) return;
    var p = doc.createElementNS(NS, "path");
    p.setAttribute("d", src.getAttribute("d"));
    p.setAttribute("class", "cmap-hl" + (focus ? " is-focus" : ""));
    hlg.appendChild(p);
  }
  function findAnchor(geo, key) { return svg.querySelector('.cmap-va[data-vgeo="' + geo + '"][data-vkey="' + key + '"]'); }

  // ---------------------------------------------------------------- legend
  function drawLegend() {
    if (!legend) return;
    var r = race(), s = sides(r);
    var txt = { "1": "+5 to 15", "2": "+15 to 30", "3": "+30 or more" };
    each(legend.querySelectorAll("li[data-band]"), function (li) {
      var k = li.getAttribute("data-band");
      var key = li.querySelector(".cmap-key"), t = li.querySelector(".cmap-lg-t");
      if (k === "off") {
        li.hidden = !r.district;
        if (r.district) t.textContent = "Not on this ballot (outside the " + unitWord(r) + ")";
        return;
      }
      if (k === "none") return;
      if (k === "even") { li.hidden = !s[1]; return; }
      var p = k.charAt(0) === "a" ? s[0] : s[1];
      if (!p || (!s[1] && k.charAt(1) !== "3")) { li.hidden = true; return; }
      li.hidden = false;
      key.setAttribute("class", "cmap-key cmap-vb-" + cls(p) + k.charAt(1));
      t.textContent = s[1] ? code(p) + " " + txt[k.charAt(1)] : pname(r, p) + " (" + code(p) + "), the only candidate";
    });
    if (uncNote) {
      // the race's notes, written by civic/map.py: uncontested, how a multi-seat race is counted, who votes in a town race
      var txt2 = [r.unote, r.snote, r.anote].filter(Boolean).join(" ");
      uncNote.hidden = !txt2;
      uncNote.textContent = txt2;
    }
  }

  // ---------------------------------------------------------------- panel
  function row(tbl, a, b, c, d) {
    var tr = el("tr");
    var th = el("th", null, a); th.setAttribute("scope", "row"); tr.appendChild(th);
    tr.appendChild(el("td", null, b));
    tr.appendChild(el("td", "num", c));
    tr.appendChild(el("td", "num", d));
    tbl.appendChild(tr);
  }
  function partyRows(r, v) {
    var out = [];
    ["D", "L", "R", "O"].forEach(function (p) {
      if (r.cand[p] || v[IDX[p]]) out.push([pname(r, p) + (p === "O" ? "" : " (" + p + ")"), r.cand[p] || "", v[IDX[p]]]);
    });
    if (v[4]) out.push(["Write-ins", "", v[4]]);
    return out;
  }
  function areaPart(geo, key, r, v) {
    // district race: how much of a township, city or town was on this ballot
    if (!r.district || geo === "precinct") return null;
    var e = V[geo][key], all = e && e.n ? e.n[String(r.year)] : 0;
    if (!v || !all || v[5] >= all) return null;
    return "Only part of this area is in " + distName(r) + ": " + v[5] + " of its " + all + " precincts in " + r.year +
      " had this race on the ballot, and only those are counted.";
  }
  function showPanel(geo, key) {
    var r = race(), v = vals(geo, key);
    panel.textContent = "";
    panel.appendChild(el("h3", null, nameOf(geo, key)));
    var kind = geo === "precinct" ? "Precinct" : (UD[key] ? UD[key].t : "");
    panel.appendChild(el("p", "cmap-type", kind + " · " + r.label + (r.uncontested ? " · uncontested" : "")));
    if (!v) {
      if (r.district && existed(geo, key, r))
        panel.appendChild(el("p", "cmap-note", "Not on this ballot: this " + (geo === "precinct" ? "precinct" : "area") +
          " is outside " + distName(r) + " in " + r.year + "."));
      else
        panel.appendChild(el("p", "cmap-note", "No results for this race in this area. The precinct may not have existed in " +
          r.year + ", or its results are not in the guide's data."));
      panel.appendChild(el("p", "cmap-note", CAVEAT));
      return;
    }
    var tot = total(v);
    var tbl = el("table", "cmap-vtab");
    tbl.appendChild(el("caption", "visually-hidden", r.label + " votes by party in " + nameOf(geo, key)));
    var thead = el("thead"), htr = el("tr");
    ["Party", "Candidate", "Votes", "Share"].forEach(function (t, i) { var th = el("th", i > 1 ? "num" : null, t); th.setAttribute("scope", "col"); htr.appendChild(th); });
    thead.appendChild(htr); tbl.appendChild(thead);
    var body = el("tbody");
    partyRows(r, v).forEach(function (pr) { row(body, pr[0], pr[1], n(pr[2]), share(pr[2], tot)); });
    tbl.appendChild(body);
    panel.appendChild(tbl);
    var dl = el("dl", "cmap-facts");
    var mt = marginText(r, v);
    var items = [[marginLabel(r), mt + (/\+/.test(mt) ? " points" : "")], ["Total votes cast in this race", n(tot)]];
    if (geo === "precinct") {
      var pe = V.precinct[key];
      if (pe.t && UD[pe.t]) items.push(["Township", UD[pe.t].n]);
      if (pe.p && UD[pe.p]) items.push(["City or town", UD[pe.p].n + (pe.ps < 0.97 ? " (part of the precinct is outside it)" : "")]);
    } else {
      items.push(["Precincts counted", String(v[5])]);
    }
    items.forEach(function (it) { dl.appendChild(el("dt", null, it[0])); dl.appendChild(el("dd", null, it[1])); });
    panel.appendChild(dl);
    var part = areaPart(geo, key, r, v);
    if (part) panel.appendChild(el("p", "cmap-note", part));
    if (r.uncontested) {
      var nc = 0;
      if (r.ncand) Object.keys(r.ncand).forEach(function (p) { nc += r.ncand[p]; });
      panel.appendChild(el("p", "cmap-note", r.seats
        ? "Uncontested: " + nc + " candidate" + (nc === 1 ? "" : "s") + " for " + r.seats + " seats, so " +
          (nc === 1 ? "the candidate was" : "all were") + " elected."
        : "Uncontested: one candidate was on the ballot."));
    }
    if (r.snote) panel.appendChild(el("p", "cmap-note", r.snote));
    if (r.anote) panel.appendChild(el("p", "cmap-note", r.anote));
    if (geo === "place" && V.place[key] && V.place[key].approx)
      panel.appendChild(el("p", "cmap-note", "Approximate: built from precincts mostly inside the town."));
    panel.appendChild(el("p", "cmap-note", CAVEAT));
    var acts = el("p", "cmap-acts");
    if (geo === "township" || geo === "place") {
      var b = el("button", "btn btn-small", PVIEW ? "Show its precincts" : "Show every race here");
      b.type = "button";
      b.addEventListener("click", function () {
        if (PVIEW) doDrill(geo, key); else { state.sel = { geo: geo, key: key, all: true }; rest(); }
      });
      acts.appendChild(b);
      if (UD[key]) { var l = el("a", "btn btn-small", "Open its page"); l.setAttribute("href", UD[key].href); acts.appendChild(l); }
    }
    if (acts.firstChild) panel.appendChild(acts);
  }
  // Every race of the selected year for one township, city or town (used when the precinct view is off).
  function showAll(geo, key) {
    panel.textContent = "";
    panel.appendChild(el("h3", null, nameOf(geo, key)));
    panel.appendChild(el("p", "cmap-type", (UD[key] ? UD[key].t + " · " : "") + "every race in " + state.year));
    var tbl = el("table", "cmap-vtab");
    tbl.appendChild(el("caption", "visually-hidden", "Every " + state.year + " race in " + nameOf(geo, key) + ": shares by party and margin"));
    var thead = el("thead"), htr = el("tr");
    ["Race", "D", "L", "R", "Margin"].forEach(function (t, i) { var th = el("th", i ? "num" : null, t); th.setAttribute("scope", "col"); htr.appendChild(th); });
    thead.appendChild(htr); tbl.appendChild(thead);
    var body = el("tbody");
    V.races.forEach(function (r) {
      if (r.year !== state.year) return;
      var v = vals(geo, key, r.id), tr = el("tr");
      if (!v && r.level === "local") return;   // other townships' and towns' races are not listed
      var th = el("th", null, r.label); th.setAttribute("scope", "row"); tr.appendChild(th);
      if (!v) { var td = el("td", null, r.district ? "not on this ballot" : "no results"); td.setAttribute("colspan", "4"); tr.appendChild(td); body.appendChild(tr); return; }
      var tot = total(v);
      [0, 2, 1].forEach(function (i) { tr.appendChild(el("td", "num", share(v[i], tot))); });
      tr.appendChild(el("td", "num", marginText(r, v)));
      body.appendChild(tr);
    });
    tbl.appendChild(body);
    panel.appendChild(tbl);
    panel.appendChild(el("p", "cmap-note", "Shares are of all votes cast in each race; the margin compares the race's two leading parties. Vote counts are in the tables under the map."));
    panel.appendChild(el("p", "cmap-note", "Past results only. They show how votes were cast here, not how any person or future election will go."));
    if (UD[key]) { var acts = el("p", "cmap-acts"), l = el("a", "btn btn-small", "Open its page"); l.setAttribute("href", UD[key].href); acts.appendChild(l); panel.appendChild(acts); }
  }
  function idle() {
    panel.textContent = "";
    if (!V) {
      panel.appendChild(el("p", "cmap-hint", failed
        ? "The election results file did not load. Every race's county total is in the table under the map."
        : "Loading election results..."));
      return;
    }
    var r = race();
    var msg = state.geo === "precinct"
      ? "Hover, focus or tap a precinct to see how it voted in " + r.label + "."
      : "Hover, focus or tap an area to see how it voted in " + r.label + ". Select a township, city or town to see " +
        (PVIEW ? "its precincts." : "its results in every race that year.");
    panel.appendChild(el("p", "cmap-hint", msg));
    panel.appendChild(el("p", "cmap-note", CAVEAT));
  }
  // An area can be shown only while it is drawn in the current view and is on the current race's ballot.
  function shown(s) {
    var a = s && findAnchor(s.geo, s.key);
    if (!a || a.classList.contains("is-dim")) return null;
    var g = a.closest(".cmap-vg");
    return g && !g.classList.contains("is-on") ? null : a;
  }
  function rest() {
    if (V && state.sel) {
      if (state.sel.all) showAll(state.sel.geo, state.sel.key); else showPanel(state.sel.geo, state.sel.key);
      hl(findAnchor(state.sel.geo, state.sel.key), false);
      return;
    }
    var a = V && shown(state.last);
    if (a) { showPanel(state.last.geo, state.last.key); hl(a, false); }
    else { state.last = null; idle(); clearHl(); }
  }

  // ---------------------------------------------------------------- drill-down list
  function drawDrill() {
    drill.textContent = "";
    if (!state.drill) { drill.hidden = true; return; }
    drill.hidden = false;
    var r = race();
    var top = el("div", "cmap-drill-top");
    top.appendChild(el("h3", null, "Precincts in " + nameOf(state.drill.kind, state.drill.key) + ": " + r.label));
    var back = el("button", "btn btn-small", "Back to " + GEO_NAME[state.drill.kind].toLowerCase());
    back.type = "button";
    back.addEventListener("click", function () { setGeo(state.drill.kind); });
    top.appendChild(back);
    drill.appendChild(top);
    var list = el("ul", "cmap-drill-list");
    var codes = Object.keys(V.precinct).filter(function (c) {
      var pe = V.precinct[c];
      return (state.drill.kind === "township" ? pe.t : pe.p) === state.drill.key && (pe.e || []).indexOf(r.year) >= 0;
    }).sort();
    codes.forEach(function (c) {
      var v = vals("precinct", c);
      var li = el("li");
      var b = el("button", "cmap-drill-btn");
      b.type = "button";
      var sw = el("span", "cmap-key " + band("precinct", c)); sw.setAttribute("aria-hidden", "true");
      b.appendChild(sw);
      b.appendChild(el("span", "cmap-drill-name", V.precinct[c].n + " (" + c + ")"));
      b.appendChild(el("span", "cmap-drill-m", v ? marginText(r, v) + " · " + n(total(v)) + " votes"
        : (r.district ? "not on this ballot" : "no results")));
      b.addEventListener("click", function () { state.sel = { geo: "precinct", key: c }; rest(); });
      b.addEventListener("focus", function () { showPanel("precinct", c); hl(findAnchor("precinct", c), true); });
      li.appendChild(b); list.appendChild(li);
    });
    if (!codes.length) list.appendChild(el("li", null, "No precincts with results are assigned to this area for " + r.year + "."));
    drill.appendChild(list);
  }

  // ---------------------------------------------------------------- tables for the selected race (under the map)
  function drawTables() {
    if (!jsTables) return;
    var r = race();
    jsTables.textContent = "";
    jsTables.hidden = false;
    if (noJs) noJs.hidden = true;
    var geos = ["township", "place"].concat(PVIEW ? ["precinct"] : []);
    jsTables.appendChild(el("p", "muted", "Below: " + r.label + " by area, for the race chosen on the map." +
      (r.district ? " Only precincts on this " + unitWord(r) + "'s ballot are counted." : "") +
      (r.snote ? " " + r.snote : "") + (r.anote ? " " + r.anote : "")));
    geos.forEach(function (geo) {
      var keys = Object.keys(geo === "precinct" ? V.precinct : V[geo]).filter(function (k) { return vals(geo, k); });
      keys.sort(function (a, b) { var x = nameOf(geo, a), y = nameOf(geo, b); return geo === "precinct" ? (a < b ? -1 : 1) : (x < y ? -1 : x > y ? 1 : 0); });
      var wrapper = el("div", "cmap-vt");
      wrapper.appendChild(el("h4", null, r.label + " by " + GEO_NAME[geo].toLowerCase()));
      if (!keys.length) { wrapper.appendChild(el("p", "muted", "No results by " + GEO_NAME[geo].toLowerCase() + " for this race.")); jsTables.appendChild(wrapper); return; }
      var wrap = el("div", "table-wrap");
      wrap.setAttribute("role", "region"); wrap.setAttribute("tabindex", "0");
      wrap.setAttribute("aria-label", r.label + " by " + GEO_NAME[geo].toLowerCase());
      var tbl = el("table", "data"); tbl.style.minWidth = "40rem";
      tbl.appendChild(el("caption", null, r.label + " by " + GEO_NAME[geo].toLowerCase()));
      var heads = [geo === "precinct" ? "Precinct (code)" : "Area", "Democratic", "Libertarian", "Republican",
                   "Other parties and write-ins", "Total votes", marginLabel(r)].concat(geo === "precinct" ? [] : ["Precincts"]);
      var thead = el("thead"), htr = el("tr");
      heads.forEach(function (t) { var th = el("th", null, t); th.setAttribute("scope", "col"); htr.appendChild(th); });
      thead.appendChild(htr); tbl.appendChild(thead);
      var body = el("tbody");
      keys.forEach(function (k) {
        var v = vals(geo, k), tr = el("tr"), th = el("th"); th.setAttribute("scope", "row");
        if (geo !== "precinct" && UD[k]) {
          var a = el("a", null, nameOf(geo, k) + (geo === "place" && V.place[k].approx ? " (approximate)" : ""));
          a.setAttribute("href", UD[k].href); th.appendChild(a);
          if (areaPart(geo, k, r, v)) th.appendChild(doc.createTextNode(" (part)"));
        } else th.textContent = nameOf(geo, k);
        tr.appendChild(th);
        [n(v[0]), n(v[2]), n(v[1]), n(v[3] + v[4]), n(total(v)), marginText(r, v)].concat(geo === "precinct" ? [] : [String(v[5])])
          .forEach(function (t) { tr.appendChild(el("td", null, t)); });
        body.appendChild(tr);
      });
      tbl.appendChild(body); wrap.appendChild(tbl); wrapper.appendChild(wrap);
      jsTables.appendChild(wrapper);
    });
  }

  // ---------------------------------------------------------------- race picker
  function pressed(container, attr, val) {
    each(container.querySelectorAll("[" + attr + "]"), function (b) {
      b.setAttribute("aria-pressed", b.getAttribute(attr) === String(val) ? "true" : "false");
    });
  }
  function fillSelect(sel, items, value) {
    sel.textContent = "";
    items.forEach(function (it) {
      var o = el("option", null, it[1]); o.value = it[0];
      if (it[0] === value) o.selected = true;
      sel.appendChild(o);
    });
  }
  function drawYears() {
    var focusIn = yearSeg.contains(doc.activeElement);
    var ys = yearsOf(state.office, state.district);
    yearSeg.textContent = "";
    ys.forEach(function (y) {
      var r = racesOf(state.office, state.district).filter(function (x) { return x.year === y; })[0];
      var b = el("button", "cmap-chip", String(y));
      b.type = "button";
      b.setAttribute("data-year", String(y));
      b.setAttribute("aria-pressed", y === state.year ? "true" : "false");
      if (r.uncontested) b.appendChild(el("span", "cmap-tag", " uncontested"));
      yearSeg.appendChild(b);
    });
    if (focusIn) { var cur = yearSeg.querySelector('[aria-pressed="true"]'); if (cur) cur.focus(); }
  }
  function drawPicker() {
    pressed(ctl, "data-level", state.level);
    var offs = V.offices.filter(function (o) { return o.level === state.level; });
    if (doc.activeElement !== officeSel || officeSel.value !== state.office)
      fillSelect(officeSel, offs.map(function (o) { return [o.key, o.label]; }), state.office);
    var off = office(state.office);
    distWrap.hidden = !off.districts;
    if (off.districts) {
      if (distSel.getAttribute("data-office") !== off.key || distSel.value !== state.district) {
        fillSelect(distSel, off.districts.map(function (d) {
          return [d, off.dnames && off.dnames[d] ? off.dnames[d] : off.dlabel + " " + d];
        }), state.district);
        distSel.setAttribute("data-office", off.key);
      }
      var dl = distWrap.querySelector("label");
      if (dl) dl.textContent = off.dlabel;
    }
    drawYears();
  }
  // Keep the year when the new choice has it, else take the newest; districts likewise keep or take the first
  // district with the current year (then the first district).
  function pickRace(level, off, dist, year) {
    var offs = V.offices.filter(function (o) { return o.level === level; });
    var o = office(off);
    if (!o || o.level !== level) o = offs[0];
    var d = null;
    if (o.districts) {
      if (o.districts.indexOf(dist) >= 0) d = dist;
      else {
        d = o.districts.filter(function (x) { return yearsOf(o.key, x).indexOf(year) >= 0; })[0] || o.districts[0];
      }
    }
    var ys = yearsOf(o.key, d);
    var y = ys.indexOf(year) >= 0 ? year : ys[0];
    var r = racesOf(o.key, d).filter(function (x) { return x.year === y; })[0];
    state.level = level; state.office = o.key; state.district = d; state.year = y; state.race = r.id;
  }
  // the selected race in the address (#race-<id>), so a reload or a shared link opens it again; standalone map only
  function writeRaceHash() {
    if (root.closest(".pick") || root.getAttribute("data-hash") === "off" || !state.race) return;
    try { history.replaceState(null, "", "#race-" + state.race); } catch (e) {}
  }
  function setRace(level, off, dist, year) {
    pickRace(level, off, dist, year);
    state.sel = null;
    if (state.drill && state.geo === "precinct") drawDrill();
    refresh();
    writeRaceHash();
  }

  function countyLine() {
    var p = ctl.querySelector(".cmap-vcounty");
    if (p) p.textContent = race().line;
  }
  function refresh() {
    if (!V) { idle(); return; }
    drawPicker();
    pressed(ctl, "data-vgeo-btn", state.geo);
    countyLine(); drawLegend(); recolor(); if (drill) drawDrill(); drawTables(); rest();
  }
  function setGeo(g) { state.geo = g; state.drill = null; state.sel = null; state.last = null; refresh(); }
  function doDrill(kind, key) { state.geo = "precinct"; state.drill = { kind: kind, key: key }; state.sel = null; state.last = null; refresh(); }

  ctl.addEventListener("click", function (ev) {
    var b = ev.target.closest && ev.target.closest("button");
    if (!b || !V) return;
    if (b.hasAttribute("data-level")) setRace(b.getAttribute("data-level"), state.office, state.district, state.year);
    else if (b.hasAttribute("data-year")) setRace(state.level, state.office, state.district, Number(b.getAttribute("data-year")));
    else if (b.hasAttribute("data-vgeo-btn")) setGeo(b.getAttribute("data-vgeo-btn"));
  });
  officeSel.addEventListener("change", function () { if (V) setRace(state.level, officeSel.value, state.district, state.year); });
  distSel.addEventListener("change", function () { if (V) setRace(state.level, state.office, distSel.value, state.year); });

  // ---------------------------------------------------------------- map pointer and focus
  function target(ev) {
    var a = ev.target.closest && ev.target.closest(".cmap-va");
    return a && !a.classList.contains("is-dim") ? a : null;
  }
  svg.addEventListener("pointerdown", function (ev) { touch = ev.pointerType === "touch" || ev.pointerType === "pen"; });
  svg.addEventListener("pointerover", function (ev) {
    if (!state.active || !V || ev.pointerType === "touch") return;
    var a = target(ev); if (!a) return;
    state.last = { geo: a.getAttribute("data-vgeo"), key: a.getAttribute("data-vkey") };
    showPanel(state.last.geo, state.last.key); hl(a, false);
  });
  svg.addEventListener("pointerout", function (ev) {
    if (!state.active || !V || ev.pointerType === "touch") return;
    if (target(ev)) rest();
  });
  svg.addEventListener("focusin", function (ev) {
    if (!state.active || !V) return;
    var a = target(ev); if (!a) return;
    state.last = { geo: a.getAttribute("data-vgeo"), key: a.getAttribute("data-vkey") };
    showPanel(state.last.geo, state.last.key); hl(a, true);
  });
  svg.addEventListener("focusout", function (ev) { if (state.active && V && target(ev)) rest(); });
  svg.addEventListener("click", function (ev) {
    if (!state.active) return;
    var a = ev.target.closest && ev.target.closest(".cmap-va");
    if (!a) { if (touch) { state.sel = null; rest(); } return; }
    ev.preventDefault();
    if (!V || a.classList.contains("is-dim")) return;
    var geo = a.getAttribute("data-vgeo"), key = a.getAttribute("data-vkey");
    if (geo === "precinct") { state.sel = { geo: geo, key: key }; rest(); return; }
    if (touch && !(state.sel && state.sel.key === key)) { state.sel = { geo: geo, key: key }; rest(); return; }
    if (PVIEW) doDrill(geo, key);
    else { state.sel = { geo: geo, key: key, all: true }; rest(); }
  });

  // ---------------------------------------------------------------- data file
  function load() {
    if (V || loading) return;
    loading = true;
    idle();
    var url = ctl.getAttribute("data-src");
    if (!window.fetch || !url) { failed = true; loading = false; idle(); return; }
    window.fetch(url).then(function (r) { if (!r.ok) throw new Error(String(r.status)); return r.json(); })
      .then(function (data) {
        V = data;
        V.races.forEach(function (r) { RACE[r.id] = r; });
        PVIEW = V.pview !== false;
        // a race asked for by the address (#race-<id>, set aside by map.js), else the default race
        var asked = root.getAttribute("data-want-race");
        root.removeAttribute("data-want-race");
        var d = (asked && RACE[asked]) || RACE[V["default"]] || V.races[0];
        pickRace(d.level, d.office, d.district, d.year);
        loading = false;
        if (state.active) refresh();
        if (asked && RACE[asked] && state.active) {
          writeRaceHash();
          try { root.scrollIntoView(); } catch (e) {}
        }
      })
      .catch(function () { failed = true; loading = false; if (state.active) idle(); });
  }
  function activate(on) {
    state.active = on;
    state.last = null;
    ctl.hidden = !on;
    if (on) { if (V) refresh(); else load(); }
    else { clearHl(); if (drill) drill.hidden = true; }
  }
  root.addEventListener("cmap-layer", function (ev) { activate(ev.detail === "votes"); });
  var cur = root.querySelector('.cmap-tab[aria-pressed="true"]');
  if (cur && cur.getAttribute("data-layer") === "votes") activate(true);
})();
