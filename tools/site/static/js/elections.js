/* Elections pages: results explorer (elections/results).
   Deep link to one contest (review P10): an address ending in #contest-<contest id> (civic/related.py contest_href)
   opens the explorer showing only that contest, with "Show every contest in this election" to widen it. The same id
   is on the contest's row in the "every contest" table (a closed fold below), so without JavaScript the link lands on
   that row. Any filter change leaves the one-contest view.
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
    var byId = {};
    /* the payload leaves out what can be rebuilt (pages/elections.py build_results): the contest id is
       "<election id>-<i>" unless "fi" says i is the whole id; a missing status is "official"; a missing seat count
       ("vf", vote for) is 1 */
    data.contests.forEach(function (c) {
      c.id = c.fi ? c.i : c.e + "-" + c.i;
      if (!c.s) c.s = "official";
      if (c.vf === undefined) c.vf = "1";
      byId[c.id] = c;
    });
    var single = null;          /* the contest shown alone (from #contest-<id>), or null */
    /* saved-place preselect (added 2026-11-09, Wave E batch 8): the Place filter's "Your saved place's areas" option.
       hereTest(place index) says whether a place's contests are decided by the saved place's voters (data.pl: each
       place's layer, civic/preselect.py keys; "" = mixed or unknown, never left out). */
    var HERE = "here";
    var hereTest = null;
    var allBtn = null;

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
        if (!skipPlace && p) {
          if (p === HERE) { if (!hereTest || !hereTest(c.p)) return false; }
          else if (data.places[c.p] !== p) return false;
        }
        return true;
      });
    }
    function fillPlaces() {
      var keep = selPlace.value;
      var seen = {};
      base(true).forEach(function (c) { seen[data.places[c.p]] = true; });
      clearEl(selPlace);
      option(selPlace, "", "All places", false);
      if (hereTest) option(selPlace, HERE, "Your saved place's areas", keep === HERE);
      Object.keys(seen).sort().forEach(function (p) { option(selPlace, p, p, p === keep); });
      if (keep && keep !== HERE && !seen[keep]) selPlace.value = "";
      if (keep === HERE && !hereTest) selPlace.value = "";
    }

    function card(c) {
      var e = elections[c.e];
      var grp = data.groups[c.g];
      var art = el("article", "elx-card");
      if (c.id) art.setAttribute("data-contest", c.id);
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
      /* "u": no more candidates than seats, an unnamed write-in total not counted as a candidate (pages/elections.py margin) */
      if (!c.q && c.u) tags.appendChild(el("span", "elx-xc mono", " UNCONTESTED"));
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
      // races on the map's "How areas voted" layer (civic/map.py race_by_contest): open the map on this race
      if (c.m && data.links.map) {
        var mp = el("p", "elx-maplink");
        var ma = el("a", null, "See this race by area on the map");
        ma.href = data.links.map + "#race-" + c.m;
        mp.appendChild(ma);
        art.appendChild(mp);
      }
      if (c.id) {
        var lp = el("p", "elx-permalink");
        var la = el("a", null, "Link to this result");
        la.href = "#contest-" + c.id;
        lp.appendChild(la);
        art.appendChild(lp);
      }
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
      if (single) {
        count.textContent = "Showing one contest, from the link you followed: " + single.l + ", " + elections[single.e].name + ".";
      } else {
        count.textContent = matches.length + " contest" + (matches.length === 1 ? "" : "s") + " match" +
          (matches.length === 1 ? "es" : "") + (n < matches.length ? "; showing the first " + n + "." : ".");
      }
      if (allBtn) allBtn.hidden = !single;
      more.hidden = n >= matches.length;
    }
    function update() {
      matches = single ? [single] : base(false);
      shown = PAGE;
      render();
    }
    /* leave the one-contest view: a filter change, or the "Show every contest" button */
    function widen() { single = null; }
    selYear.addEventListener("change", function () { widen(); fillElections(true); fillPlaces(); update(); });
    selEl.addEventListener("change", function () { widen(); fillPlaces(); update(); });
    selGroup.addEventListener("change", function () { widen(); fillPlaces(); update(); });
    selPlace.addEventListener("change", function () { widen(); update(); });
    more.addEventListener("click", function () { shown += PAGE; render(); });
    fillElections();
    /* default view: the most recent election */
    var last = data.elections[data.elections.length - 1];
    if (last && selYear.value === last.y) selEl.value = last.id;
    fillPlaces();

    allBtn = el("button", "btn btn-small elx-all", "Show every contest in this election");
    allBtn.type = "button";
    allBtn.hidden = true;
    count.parentNode.insertBefore(allBtn, count.nextSibling);
    allBtn.addEventListener("click", function () {
      widen();
      update();
      try { history.replaceState(null, "", window.location.pathname + window.location.search); } catch (e) { /* keep the hash */ }
      count.setAttribute("tabindex", "-1");
      if (count.focus) count.focus();
    });

    function contestOf(hash) {
      var m = /^#contest-([A-Za-z0-9-]+)$/.exec(hash || "");
      return m && Object.prototype.hasOwnProperty.call(byId, m[1]) ? byId[m[1]] : null;
    }
    /* show one contest: its year and election in the filters (so widening shows its election), only it in the list */
    function showOne(c, scroll) {
      single = c;
      selYear.value = elections[c.e].y;
      fillElections(true);
      selEl.value = c.e;
      selGroup.value = "";
      fillPlaces();
      selPlace.value = "";
      update();
      /* folds.js opened the "every contest" fold because the address points at a row in it; the explorer shows
         the contest instead, so put the fold back the way the reader had it (closed) */
      var row = doc.getElementById("contest-" + c.id);
      var fold = row && row.closest ? row.closest("details[data-fold]") : null;
      if (fold && fold.open && !fold.hasAttribute("data-reader-open")) fold.open = false;
      var art = box.querySelector("[data-contest]");
      if (art && scroll) {
        art.setAttribute("tabindex", "-1");
        if (art.scrollIntoView) art.scrollIntoView();
        if (art.focus) art.focus({ preventScroll: true });
      }
    }
    /* a reader who opens the fold by hand keeps it open */
    var foldEl = doc.getElementById("every-contest-all");
    if (foldEl) {
      foldEl.querySelector("summary").addEventListener("click", function () {
        if (!foldEl.open) foldEl.setAttribute("data-reader-open", "");
        else foldEl.removeAttribute("data-reader-open");
      });
    }
    var first = contestOf(window.location.hash);
    if (first) {
      single = first;
      update();
      /* after folds.js (later in app.js) has run its own landing step */
      window.setTimeout(function () { showOne(first, true); }, 0);
      /* the browser scrolls to the fragment (the row in the closed fold) again once the page has loaded: put the
         contest back on screen, unless the reader has moved on */
      window.addEventListener("load", function () {
        window.setTimeout(function () {
          var art = single === first ? box.querySelector("[data-contest]") : null;
          if (art && art.scrollIntoView) art.scrollIntoView();
        }, 0);
      });
    } else {
      update();
    }
    window.addEventListener("hashchange", function () {
      var c = contestOf(window.location.hash);
      if (c) window.setTimeout(function () { showOne(c, true); }, 0);
      /* Back from #contest-<id> to the plain address: leave the one-contest view, as the "Show every contest" button
         does (it stayed on the one contest; debug pass 2026-11-09). Any other #anchor (a source link in the card) keeps
         the view. */
      else if (single && (window.location.hash || "").length < 2) { widen(); update(); }
    });

    /* saved-place preselect: here.js (later in app.js) is ready by DOMContentLoaded. A #contest-<id> or any other
       explicit #anchor wins: the explorer opens as the link says and the line only offers the saved place. */
    function preselect() {
      var slot = doc.querySelector('[data-here-pre="explorer"]');
      if (!slot || !window.civicHere) return;
      var m = window.civicHere.mine();
      if (!m) return;
      var pl = data.pl || [];
      hereTest = function (pi) { return m.wants(pl[pi] || ""); };
      var DOT = " " + String.fromCharCode(183) + " ";
      var text = ["St. Joseph County"].concat(m.names).concat(["statewide and legislative contests"]).join(DOT);
      function to(v) { widen(); fillPlaces(); selPlace.value = v; update(); }
      var ctl = window.civicHere.line(slot, {
        onText: text,
        onWhy: " The contests decided by your saved place's voters (kept on this device only); the Place filter says " +
               "\"Your saved place's areas\". Every legislative district that includes part of the county is listed: " +
               "yours depends on your address.",
        offText: text,
        applyLabel: "Show only these",
        undoLabel: "Show all places",
        apply: function () { to(HERE); },
        undo: function () { to(""); }
      });
      selPlace.addEventListener("change", function () {
        if (selPlace.value === HERE) { if (ctl.state() !== "on") ctl.set("on"); }
        else if (ctl.state() === "on") ctl.set("off");
      });
      fillPlaces();
      if (single || window.civicHere.hashWins()) ctl.set("off");
      else { selPlace.value = HERE; update(); ctl.set("on"); }
    }
    /* app.js is deferred: it runs while readyState is "interactive", before DOMContentLoaded, and before the later
       partials (here.js, tablefilter.js) have set up; so wait for DOMContentLoaded unless the page is already complete */
    if (doc.readyState !== "complete") doc.addEventListener("DOMContentLoaded", preselect);
    else preselect();
    /* a link to the contest already in the address (no hashchange): show it again */
    doc.addEventListener("click", function (ev) {
      var a = ev.target && ev.target.closest ? ev.target.closest("a[href]") : null;
      if (!a || a.pathname !== window.location.pathname || a.hash !== window.location.hash) return;
      var c = contestOf(a.hash);
      if (c) window.setTimeout(function () { showOne(c, true); }, 0);
    });
  }

  /* The margins page (elections/margins/) needs no script of its own: its filters are the shared table filter,
     static/js/tablefilter.js (deep mode for the "find a race" list), and its map is static/js/map.js with
     static/js/pick_one.js. */

  explorer();
})();
