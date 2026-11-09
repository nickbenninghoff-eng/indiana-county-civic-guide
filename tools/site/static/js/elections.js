/* Elections pages: results explorer (elections/results) and margins filters (elections/landscape).
   Data is inserted with textContent only. ASCII only. */
(function () {
  "use strict";
  var doc = document;

  function el(tag, cls, text) {
    var e = doc.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = String(text);
    return e;
  }
  function clearEl(e) { while (e.firstChild) e.removeChild(e.firstChild); }
  function fmtInt(n) {
    if (n === null || n === undefined || n === "") return "";
    var s = String(Math.round(Number(n)));
    return s.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }
  function option(sel, value, text, selected) {
    var o = el("option", null, text);
    o.value = value;
    if (selected) o.selected = true;
    sel.appendChild(o);
  }

  var BADGE = {
    official: "OFFICIAL", unofficial: "UNOFFICIAL", computed: "COMPUTED", from_scan: "FROM SCAN",
    secondary: "SECONDARY", single_source: "SINGLE SOURCE", low: "LOW CONFIDENCE"
  };
  function badge(key, root) {
    var a = el("a", "badge-link");
    a.href = root.about;
    var s = el("span", "badge badge-" + key, BADGE[key] || String(key).toUpperCase());
    a.appendChild(s);
    return a;
  }

  /* ------------------------------------------------------------ results explorer */
  function explorer() {
    var node = doc.getElementById("elx-data");
    var box = doc.getElementById("elx-results");
    if (!node || !box) return;
    var data;
    try { data = JSON.parse(node.textContent); } catch (e) { return; }
    var selYear = doc.getElementById("elx-year");
    var selEl = doc.getElementById("elx-election");
    var selGroup = doc.getElementById("elx-group");
    var selPlace = doc.getElementById("elx-place");
    var count = doc.getElementById("elx-count");
    var more = doc.getElementById("elx-more");
    var elections = {};
    data.elections.forEach(function (e) { elections[e.id] = e; });
    var PAGE = 30;
    var shown = PAGE;
    var matches = [];

    function fillElections(reset) {
      var y = selYear.value;
      var keep = reset ? "" : selEl.value;
      clearEl(selEl);
      option(selEl, "", y ? "All elections in " + y : "All elections", false);
      data.elections.slice().reverse().forEach(function (e) {
        if (!y || e.y === y) option(selEl, e.id, e.name, e.id === keep);
      });
    }
    function base(skipPlace) {
      var y = selYear.value, eid = selEl.value, g = selGroup.value, p = selPlace.value;
      return data.contests.filter(function (c) {
        var e = elections[c.e];
        if (y && e.y !== y) return false;
        if (eid && c.e !== eid) return false;
        if (g && String(c.g) !== g) return false;
        if (!skipPlace && p && data.places[c.p] !== p) return false;
        return true;
      });
    }
    function fillPlaces() {
      var keep = selPlace.value;
      var seen = {};
      base(true).forEach(function (c) { seen[data.places[c.p]] = true; });
      clearEl(selPlace);
      option(selPlace, "", "All places", false);
      Object.keys(seen).sort().forEach(function (p) { option(selPlace, p, p, p === keep); });
      if (keep && !seen[keep]) selPlace.value = "";
    }

    function card(c) {
      var e = elections[c.e];
      var grp = data.groups[c.g];
      var art = el("article", "elx-card");
      var head = el("header", "elx-card-head");
      head.appendChild(el("h3", "elx-card-title", c.l));
      head.appendChild(el("p", "elx-card-meta mono", e.name + " | " + grp + " | " + data.places[c.p]));
      var tags = el("p", "elx-tags");
      tags.appendChild(badge(c.s, data.links));
      var f = c.f || [];
      if (f.indexOf("low") >= 0) { tags.appendChild(doc.createTextNode(" ")); tags.appendChild(badge("low", data.links)); }
      if (f.indexOf("pctc") >= 0) { tags.appendChild(doc.createTextNode(" ")); tags.appendChild(badge("computed", data.links)); }
      if (c.x) {
        tags.appendChild(doc.createTextNode(" "));
        tags.appendChild(el("span", "elx-xc mono", "COUNTY PORTION ONLY"));
        tags.appendChild(doc.createTextNode(" "));
        var a = el("a", null, grp === "State legislature" ? "Districts and legislators" : "State government");
        a.href = grp === "State legislature" ? data.links.legislature : data.links.state;
        tags.appendChild(a);
      }
      var vf = parseInt(c.vf, 10);
      if (!c.q && !isNaN(vf) && c.c.length <= vf) tags.appendChild(el("span", "elx-xc mono", " UNCONTESTED"));
      if (!c.q && vf > 1) tags.appendChild(el("span", "elx-sub muted", " Vote for " + vf + "."));
      head.appendChild(tags);
      art.appendChild(head);
      var list = el("ol", "elx-cands");
      c.c.forEach(function (x) {
        var name = x[0], party = x[1], votes = x[2], pct = x[3], win = x[4], low = x[5];
        var li = el("li", "elx-cand");
        var lab = el("div", "elx-cand-lab");
        lab.appendChild(el("span", "elx-name", name));
        var sub = c.q ? "" : (party ? (data.parties[party] || party) + " (" + party + ")" : "No party listed");
        if (win === "Y" && !c.x) {
          var w = c.q ? "Majority" : "Elected";
          if (c.s === "unofficial") w += " (unofficial)";
          sub = sub ? sub + " | " + w : w;
        }
        if (low) sub = (sub ? sub + " | " : "") + "low confidence";
        if (sub) lab.appendChild(el("span", "elx-party mono", sub));
        li.appendChild(lab);
        var track = el("div", "elx-track");
        if (pct !== null && pct !== undefined) {
          var fill = el("div", "elx-fill " + (c.q ? "m-ink" : party === "D" ? "m-party-D" : party === "R" ? "m-party-R" : "m-party-other"));
          fill.style.width = Math.max(0.5, Math.min(100, pct)) + "%";
          track.appendChild(fill);
        }
        li.appendChild(track);
        li.appendChild(el("span", "elx-val mono",
          pct === null || pct === undefined ? "votes not recorded" : pct.toFixed(1) + "%" + (votes !== null ? " | " + fmtInt(votes) : "")));
        list.appendChild(li);
      });
      art.appendChild(list);
      var foot = el("p", "elx-card-foot muted");
      if (c.n !== undefined) foot.appendChild(doc.createTextNode("Note: " + data.notes[c.n] + " "));
      foot.appendChild(doc.createTextNode("Source: "));
      c.src.forEach(function (i, k) {
        var s = data.src[i];
        var a = el("a", null, s.id);
        a.href = "#src-" + s.id;
        a.title = s.t;
        if (k) foot.appendChild(doc.createTextNode(", "));
        foot.appendChild(a);
      });
      art.appendChild(foot);
      return art;
    }

    function render() {
      clearEl(box);
      var n = Math.min(shown, matches.length);
      for (var i = 0; i < n; i++) box.appendChild(card(matches[i]));
      if (!matches.length) box.appendChild(el("p", "muted", "No contests match these filters."));
      count.textContent = matches.length + " contest" + (matches.length === 1 ? "" : "s") + " match" +
        (matches.length === 1 ? "es" : "") + (n < matches.length ? "; showing the first " + n + "." : ".");
      more.hidden = n >= matches.length;
    }
    function update() {
      matches = base(false);
      shown = PAGE;
      render();
    }
    selYear.addEventListener("change", function () { fillElections(true); fillPlaces(); update(); });
    selEl.addEventListener("change", function () { fillPlaces(); update(); });
    selGroup.addEventListener("change", function () { fillPlaces(); update(); });
    selPlace.addEventListener("change", update);
    more.addEventListener("click", function () { shown += PAGE; render(); });
    fillElections();
    /* default view: the most recent election */
    var last = data.elections[data.elections.length - 1];
    if (last && selYear.value === last.y) selEl.value = last.id;
    fillPlaces();
    update();
  }

  /* ------------------------------------------------------------ margins table */
  function margins() {
    var table = doc.getElementById("margins-table");
    if (!table) return;
    var tbody = table.tBodies[0];
    var rows = Array.prototype.slice.call(tbody.rows);
    var sy = doc.getElementById("mg-year"), st = doc.getElementById("mg-type"),
        sb = doc.getElementById("mg-band"), ss = doc.getElementById("mg-sort"), out = doc.getElementById("mg-count");
    function apply() {
      var y = sy.value, t = st.value, b = sb.value, n = 0;
      var sorted = rows.slice();
      if (ss.value === "date") {
        sorted.sort(function (a, c) {
          var da = a.getAttribute("data-date"), dc = c.getAttribute("data-date");
          if (da !== dc) return da < dc ? 1 : -1;
          return parseFloat(a.getAttribute("data-margin")) - parseFloat(c.getAttribute("data-margin"));
        });
      } else {
        sorted.sort(function (a, c) { return parseFloat(a.getAttribute("data-margin")) - parseFloat(c.getAttribute("data-margin")); });
      }
      sorted.forEach(function (r) {
        var ok = (!y || r.getAttribute("data-year") === y) && (!t || r.getAttribute("data-type") === t) &&
                 (!b || r.getAttribute("data-band") === b);
        r.hidden = !ok;
        if (ok) n++;
        tbody.appendChild(r);
      });
      out.textContent = n + " race" + (n === 1 ? "" : "s") + " shown.";
    }
    [sy, st, sb, ss].forEach(function (s) { s.addEventListener("change", apply); });
  }

  explorer();
  margins();
})();
