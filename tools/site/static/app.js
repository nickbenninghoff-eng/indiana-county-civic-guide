/* Indiana County Civic Guide: behavior. Plain JS, no dependencies.
   Every feature enhances content that is already complete without JS.
   Data from the page is inserted with textContent only. */
(function () {
  "use strict";

  var doc = document;
  var root = doc.documentElement;
  var site = doc.getElementById("site");
  var ROOT = (site && site.getAttribute("data-root")) || "./";
  var PAGE = (site && site.getAttribute("data-page")) || "";
  var DOT = " " + String.fromCharCode(183) + " "; // middle dot, built so the file stays ASCII whatever charset the host sends

  function store(key, val) {
    try {
      if (val === undefined) return window.localStorage.getItem(key);
      window.localStorage.setItem(key, val);
    } catch (e) { /* storage unavailable: conveniences only */ }
    return null;
  }

  function readJSON(id) {
    var el = doc.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
  }

  /* ------------------------------------------------------------ theme */
  var savedTheme = store("civic-theme");
  if (savedTheme === "light" || savedTheme === "dark") root.setAttribute("data-theme", savedTheme);
  var themeBtn = doc.getElementById("theme-toggle");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var cur = root.getAttribute("data-theme");
      if (!cur) cur = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      var next = cur === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      store("civic-theme", next);
    });
  }

  /* ------------------------------------------------------------ tooltip */
  var tip = doc.createElement("div");
  tip.className = "tooltip";
  tip.setAttribute("role", "status");
  tip.hidden = true;
  doc.body.appendChild(tip);

  function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); }

  function showTip(lines, x, y) {
    clear(tip);
    lines.forEach(function (ln) {
      var row = doc.createElement("span");
      if (ln.key) {
        row.className = "tip-row";
        var k = doc.createElement("span");
        k.className = "tip-key " + ln.key;
        row.appendChild(k);
        var t = doc.createElement("span");
        t.textContent = ln.text;
        row.appendChild(t);
      } else {
        row.className = ln.strong ? "tip-v" : "tip-l";
        row.textContent = ln.text;
      }
      tip.appendChild(row);
    });
    tip.hidden = false;
    var w = tip.offsetWidth, h = tip.offsetHeight;
    var vw = window.innerWidth, vh = window.innerHeight;
    var left = Math.min(Math.max(8, x + 14), vw - w - 8);
    var top = y + 16 + h > vh - 8 ? y - h - 12 : y + 16;
    tip.style.left = left + "px";
    tip.style.top = Math.max(8, top) + "px";
  }
  function hideTip() { tip.hidden = true; }

  function tipLines(el) {
    var out = [];
    var v = el.getAttribute("data-tv"), l = el.getAttribute("data-tl");
    if (v) out.push({ text: v, strong: true });
    if (l) out.push({ text: l });
    return out;
  }

  doc.addEventListener("pointermove", function (ev) {
    var el = ev.target.closest ? ev.target.closest("[data-tv]") : null;
    if (el) showTip(tipLines(el), ev.clientX, ev.clientY);
    else if (!ev.target.closest || !ev.target.closest(".crosshair-hit")) hideTip();
  });
  doc.addEventListener("pointerleave", hideTip);
  doc.addEventListener("focusin", function (ev) {
    var el = ev.target.closest ? ev.target.closest("[data-tv]") : null;
    if (!el) return;
    var r = el.getBoundingClientRect();
    showTip(tipLines(el), r.left + Math.min(r.width, 160) / 2, r.bottom - 10);
  });
  doc.addEventListener("focusout", hideTip);
  window.addEventListener("scroll", hideTip, { passive: true });

  /* ------------------------------------------------------------ line charts: crosshair */
  Array.prototype.forEach.call(doc.querySelectorAll("svg[data-line]"), function (svg) {
    var data;
    try { data = JSON.parse(svg.getAttribute("data-line")); } catch (e) { return; }
    var hit = svg.querySelector(".crosshair-hit");
    var line = svg.querySelector(".crosshair");
    if (!hit || !line || !data.x.length) return;
    var idx = data.x.length - 1;
    function nearest(px) {
      var best = 0, bd = Infinity;
      data.x.forEach(function (x, i) { var d = Math.abs(x - px); if (d < bd) { bd = d; best = i; } });
      return best;
    }
    function show(i, cx, cy) {
      idx = i;
      line.setAttribute("x1", data.x[i]);
      line.setAttribute("x2", data.x[i]);
      line.setAttribute("visibility", "visible");
      var lines = [{ text: data.labels[i], strong: true }];
      data.series.forEach(function (s) { lines.push({ key: s.mark, text: s.values[i] + "  " + s.name }); });
      showTip(lines, cx, cy);
    }
    function svgX(clientX) {
      var m = svg.getScreenCTM();
      if (!m) return 0;
      var p = svg.createSVGPoint();
      p.x = clientX; p.y = 0;
      return p.matrixTransform(m.inverse()).x;
    }
    hit.addEventListener("pointermove", function (ev) { show(nearest(svgX(ev.clientX)), ev.clientX, ev.clientY); });
    hit.addEventListener("pointerleave", function () { line.setAttribute("visibility", "hidden"); hideTip(); });
    hit.addEventListener("focus", function () {
      var r = svg.getBoundingClientRect();
      show(idx, r.left + r.width / 2, r.top + 20);
    });
    hit.addEventListener("blur", function () { line.setAttribute("visibility", "hidden"); });
    hit.addEventListener("keydown", function (ev) {
      if (ev.key !== "ArrowLeft" && ev.key !== "ArrowRight") return;
      ev.preventDefault();
      var i = Math.max(0, Math.min(data.x.length - 1, idx + (ev.key === "ArrowRight" ? 1 : -1)));
      var r = svg.getBoundingClientRect();
      show(i, r.left + r.width / 2, r.top + 20);
    });
  });

  /* ------------------------------------------------------------ table views */
  Array.prototype.forEach.call(doc.querySelectorAll("details.chart-table"), function (d) {
    var s = d.querySelector("summary");
    function sync() { if (s) s.textContent = d.open ? "Hide table" : "Show table"; }
    d.addEventListener("toggle", sync);
    sync();
  });

  /* A table whose rows a filter has hidden (tablefilter.js, pick_one.js) is marked data-rows-filtered; Copy CSV then
     copies the header and the rows shown, and its button says how many. Unfiltered tables copy every row. */
  function bodyRows(table) {
    var out = [];
    Array.prototype.forEach.call(table.tBodies, function (tb) {
      Array.prototype.forEach.call(tb.rows, function (tr) { out.push(tr); });
    });
    return out;
  }

  function tableCSV(table) {
    var rows = [];
    var filtered = table.hasAttribute("data-rows-filtered");
    Array.prototype.forEach.call(table.querySelectorAll("tr"), function (tr) {
      if (filtered && tr.hidden && tr.parentNode && tr.parentNode.tagName === "TBODY") return;
      var cells = [];
      Array.prototype.forEach.call(tr.children, function (c) {
        var t = (c.textContent || "").replace(/\s+/g, " ").trim();
        cells.push(/[",\n]/.test(t) ? '"' + t.replace(/"/g, '""') + '"' : t);
      });
      rows.push(cells.join(","));
    });
    return rows.join("\n");
  }

  doc.addEventListener("rows-filtered", function (ev) {
    var table = ev.target;
    if (!table || table.tagName !== "TABLE" || !table.id) return;
    var rows = bodyRows(table);
    var shown = rows.filter(function (tr) { return !tr.hidden; }).length;
    var btn = doc.getElementById(table.id + "-copy");
    if (shown < rows.length) table.setAttribute("data-rows-filtered", String(shown));
    else table.removeAttribute("data-rows-filtered");
    if (!btn) return;
    if (!btn.hasAttribute("data-copy-label")) btn.setAttribute("data-copy-label", btn.textContent);
    if (shown === rows.length) btn.textContent = btn.getAttribute("data-copy-label");
    else if (shown === 0) btn.textContent = "No rows shown to copy";
    else btn.textContent = "Copy " + shown + " shown row" + (shown === 1 ? "" : "s");
    btn.disabled = shown === 0;
    var status = btn.parentNode.querySelector(".copy-status");
    if (status) status.textContent = "";
  });

  doc.addEventListener("click", function (ev) {
    var btn = ev.target.closest ? ev.target.closest("[data-copy-table]") : null;
    if (!btn) return;
    var table = doc.getElementById(btn.getAttribute("data-copy-table"));
    if (!table) return;
    var csv = tableCSV(table);
    var status = btn.parentNode.querySelector(".copy-status");
    if (!status) {
      status = doc.createElement("span");
      status.className = "copy-status";
      status.setAttribute("role", "status");
      btn.parentNode.appendChild(status);
    }
    function fallback() {
      var ta = btn.parentNode.querySelector("textarea.copy-fallback");
      if (!ta) {
        ta = doc.createElement("textarea");
        ta.className = "copy-fallback";
        ta.setAttribute("aria-label", "CSV text to copy");
        ta.rows = 4;
        ta.style.width = "100%";
        btn.parentNode.appendChild(ta);
      }
      ta.value = csv;
      ta.focus();
      ta.select();
      status.textContent = "Text selected: press Ctrl+C (or Cmd+C) to copy.";
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(csv).then(function () { status.textContent = "Copied."; }, fallback);
    } else {
      fallback();
    }
  });

  /* ------------------------------------------------------------ reference menu */
  var menu = doc.getElementById("ref-menu");
  if (menu) {
    doc.addEventListener("click", function (ev) { if (menu.open && !menu.contains(ev.target)) menu.open = false; });
    doc.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && menu.open) { menu.open = false; var s = menu.querySelector("summary"); if (s) s.focus(); }
    });
  }

  /* ------------------------------------------------------------ learning paths (#path-<id>-<n>) */
  var pathsData = readJSON("paths-data");
  var bar = doc.getElementById("path-bar");
  function link(text, href, cls) {
    var a = doc.createElement("a");
    a.href = href;
    a.textContent = text;
    if (cls) a.className = cls;
    return a;
  }
  function renderPath() {
    if (!pathsData || !bar) return;
    var m = /^#path-([a-z0-9-]+)-(\d+)$/.exec(window.location.hash || "");
    Array.prototype.forEach.call(doc.querySelectorAll(".path-target"), function (el) { el.classList.remove("path-target"); });
    if (!m) { bar.hidden = true; return; }
    var path = null;
    pathsData.paths.forEach(function (p) { if (p.id === m[1]) path = p; });
    var n = parseInt(m[2], 10);
    if (!path || n < 1 || n > path.stops.length) { bar.hidden = true; return; }
    var stop = path.stops[n - 1];
    clear(bar);
    var head = doc.createElement("p");
    head.className = "pb-head";
    head.textContent = "Path: " + path.title + DOT + "Stop " + n + " of " + path.stops.length + DOT + stop.title;
    var lead = doc.createElement("p");
    lead.className = "pb-lead";
    lead.textContent = stop.lead;
    var nav = doc.createElement("p");
    nav.className = "pb-nav";
    if (n > 1) {
      var prev = path.stops[n - 2];
      nav.appendChild(link("Previous stop", ROOT + prev.page + "#path-" + path.id + "-" + (n - 1)));
    }
    if (n < path.stops.length) {
      var nx = path.stops[n];
      nav.appendChild(link("Next stop: " + nx.title, ROOT + nx.page + "#path-" + path.id + "-" + (n + 1)));
    } else {
      nav.appendChild(link("End of path: all paths", ROOT + "index.html#paths"));
    }
    bar.appendChild(head);
    bar.appendChild(nav);
    bar.appendChild(lead);
    bar.hidden = false;
    var target = stop.page === PAGE ? doc.getElementById(stop.anchor) : null;
    if (target) {
      // put the path context right above the stop, so it is in view on arrival
      target.parentNode.insertBefore(bar, target);
      target.classList.add("path-target");
      bar.scrollIntoView({ block: "start", behavior: "instant" });
    }
  }
  window.addEventListener("hashchange", renderPath);
  if (/^#path-/.test(window.location.hash) && "scrollRestoration" in history) history.scrollRestoration = "manual";
  renderPath();
  // fonts and layout settle after DOMContentLoaded; land on the stop again once loaded
  window.addEventListener("load", function () { if (/^#path-/.test(window.location.hash)) renderPath(); });

  /* ------------------------------------------------------------ layer diagram + place picker */
  var layerData = readJSON("layer-data");
  var selPlace = doc.getElementById("pick-place");
  var selTown = doc.getElementById("pick-township");
  var selSchool = doc.getElementById("pick-school");
  if (layerData && selPlace && selTown && selSchool) {
    var places = {};
    layerData.places.forEach(function (p) { places[p.id] = p; });
    var layers = Array.prototype.slice.call(doc.querySelectorAll(".layer[data-layer]"));

    function setText(sel, val) {
      Array.prototype.forEach.call(doc.querySelectorAll(sel), function (el) { el.textContent = val; });
    }

    function update() {
      var place = places[selPlace.value];
      if (!place) return;
      var want = { "state": 1, "county": 1, "library": 1 };
      want["township:" + selTown.value] = 1;
      want["school:" + selSchool.value] = 1;
      if (place.muni) want["municipality:" + place.muni] = 1;
      var tot = { gov: 0, elected: 0, vote: 0, appointed: 0, unknown: 0 };
      var next = {};
      layers.forEach(function (el) {
        var on = !!want[el.getAttribute("data-layer")];
        el.hidden = !on;
        if (!on) return;
        tot.gov += +el.getAttribute("data-gov");
        tot.elected += +el.getAttribute("data-elected");
        tot.vote += +el.getAttribute("data-vote");
        tot.appointed += +el.getAttribute("data-appointed");
        tot.unknown += +el.getAttribute("data-unknown");
        var nx = {};
        try { nx = JSON.parse(el.getAttribute("data-next") || "{}"); } catch (e) { nx = {}; }
        var title = (el.querySelector(".layer-title") || {}).textContent || "";
        Object.keys(nx).forEach(function (y) {
          next[y] = next[y] || [];
          nx[y].forEach(function (lab) { next[y].push(lab + " (" + title + ")"); });
        });
      });
      setText('[data-count="gov"]', tot.gov);
      setText('[data-count="elected"]', tot.elected);
      setText('[data-count="vote"]', tot.vote);
      setText('[data-count="appointed"]', tot.appointed);
      Array.prototype.forEach.call(doc.querySelectorAll('[data-count="atleast"]'), function (el) { el.hidden = tot.unknown === 0; });
      var years = Object.keys(next).sort();
      var ny = years[0];
      var yEl = doc.getElementById("next-year"), dEl = doc.getElementById("next-dates"), oEl = doc.getElementById("next-offices");
      if (yEl) yEl.textContent = ny || "Not in data";
      if (dEl) dEl.textContent = ny && layerData.dates[ny] ? "Primary " + layerData.dates[ny].primary + DOT + "General " + layerData.dates[ny].general : "";
      if (oEl) oEl.textContent = ny ? next[ny].join("; ") : "";
      store("civic-place", JSON.stringify({ place: selPlace.value, township: selTown.value, school: selSchool.value }));
    }

    function applyPlace(keepOthers) {
      var place = places[selPlace.value];
      if (!place) return;
      if (place.township) {
        selTown.value = place.township;
        selTown.disabled = true;
      } else {
        selTown.disabled = false;
        if (!keepOthers) selTown.value = place.township_default || "any";
      }
      if (!keepOthers) selSchool.value = place.school_default || "any";
      update();
    }

    selPlace.addEventListener("change", function () { applyPlace(false); });
    selTown.addEventListener("change", update);
    selSchool.addEventListener("change", update);

    var saved = null;
    try { saved = JSON.parse(store("civic-place") || "null"); } catch (e) { saved = null; }
    if (saved && places[saved.place]) {
      selPlace.value = saved.place;
      if (saved.township) selTown.value = saved.township;
      if (saved.school) selSchool.value = saved.school;
      applyPlace(true);
    } else {
      applyPlace(true);
    }
  }

  Array.prototype.forEach.call(doc.querySelectorAll(".layer-toggle"), function (btn) {
    btn.addEventListener("click", function () {
      var layer = btn.closest(".layer");
      var open = !layer.classList.contains("open");
      layer.classList.toggle("open", open);
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      btn.textContent = open ? "Hide seats" : "Show seats";
    });
  });

  /* ------------------------------------------------------------ print (later public host) */
  window.addEventListener("beforeprint", function () {
    Array.prototype.forEach.call(doc.querySelectorAll("details.chart-table"), function (d) { d.open = true; });
  });
})();
