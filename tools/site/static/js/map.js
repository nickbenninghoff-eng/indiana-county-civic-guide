/* Boundary map (civic/map.py): layer switcher, details panel, touch select-then-open. Without JS the
   SVG links and the lists still work. */
(function () {
  var doc = document;
  var root = doc.querySelector(".cmap");
  if (!root) return;
  var dataEl = doc.getElementById("cmap-data");
  var data = {};
  try { data = JSON.parse(dataEl.textContent); } catch (e) { return; }
  var panel = doc.getElementById("cmap-panel");
  var svg = root.querySelector(".cmap-svg");
  var hlg = svg.querySelector(".cmap-hl-g");
  var tabs = root.querySelector(".cmap-tabs");
  var NS = "http://www.w3.org/2000/svg";
  var hint = panel.firstElementChild.cloneNode(true);
  // selected: an area chosen by tap (touch). last: the area most recently hovered or focused; the panel
  // keeps showing it after the pointer leaves the map, until another area is hovered or the layer changes.
  var selected = null, last = null, lastTouch = false;
  var noHash = root.getAttribute("data-hash") === "off";
  doc.body.classList.add("cmap-js");
  tabs.hidden = false;

  function el(tag, cls, text) {
    var e = doc.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function show(uid) {
    var u = data[uid];
    if (!u) return;
    panel.textContent = "";
    panel.appendChild(el("h3", null, u.n));
    panel.appendChild(el("p", "cmap-type", u.t));
    var dl = el("dl", "cmap-facts");
    // data-lead on the map (the indicator maps): the fact with that key (u.fk) is marked as the one shaded
    var lead = root.getAttribute("data-lead");
    u.f.forEach(function (r, i) {
      var on = lead && u.fk && u.fk[i] === lead;
      dl.appendChild(el("dt", on ? "is-lead" : null, r[0])); dl.appendChild(el("dd", on ? "is-lead" : null, r[1]));
    });
    panel.appendChild(dl);
    // optional money-map fields (civic/money_map.py): ranked share bars, then caveat lines
    if (u.bars) u.bars.forEach(function (g) {
      panel.appendChild(el("p", "cmap-bars-h", g[0]));
      var ol = el("ol", "cmap-bars");
      g[1].forEach(function (b) {
        var li = el("li");
        var top = el("span", "cmap-bar-top");
        top.appendChild(el("span", "cmap-bar-l", b[0]));
        // b[3] (the amount) may be empty, e.g. a candidate with no reports on file (civic/campaign_map.py)
        top.appendChild(el("span", "cmap-bar-v", b[3] ? b[1] + " \u00b7 " + b[3] : b[1]));
        li.appendChild(top);
        var track = el("span", "cmap-bar-t");
        track.setAttribute("aria-hidden", "true");
        var fill = el("span", "cmap-bar-f");
        fill.style.width = Math.max(0, Math.min(100, Number(b[2]) || 0)) + "%";
        track.appendChild(fill);
        li.appendChild(track);
        ol.appendChild(li);
      });
      panel.appendChild(ol);
    });
    if (u.note) panel.appendChild(el("p", "cmap-note", u.note));
    if (u.cav) u.cav.forEach(function (c) { panel.appendChild(el("p", "cmap-note", c)); });
    var link = el("a", "btn cmap-open", u.open || "Open page");
    link.setAttribute("href", u.href);
    panel.appendChild(link);
    // optional further links, [[label, href], ...] (the budgets map: the unit's own page after "Show it below")
    if (u.more) u.more.forEach(function (m) {
      var p = el("p", "cmap-more");
      var a = el("a", null, m[0]);
      a.setAttribute("href", m[1]);
      p.appendChild(a);
      panel.appendChild(p);
    });
  }

  function highlight(uid, focus) {
    while (hlg.firstChild) hlg.removeChild(hlg.firstChild);
    if (!uid || !data[uid]) return;
    var p = doc.createElementNS(NS, "path");
    // an entry may leave out its path (the campaign-money map does, to keep the page small): use the shape's own
    var d = data[uid].d;
    if (!d) {
      var shp = svg.querySelector('.cmap-a[data-uid="' + uid + '"] path');
      d = shp ? shp.getAttribute("d") : "";
    }
    if (!d) return;
    p.setAttribute("d", d);
    p.setAttribute("class", "cmap-hl" + (focus ? " is-focus" : ""));
    hlg.appendChild(p);
  }

  function rest() {
    var uid = selected || last;
    if (uid && data[uid]) { show(uid); highlight(uid, false); }
    else { panel.textContent = ""; panel.appendChild(hint.cloneNode(true)); highlight(null); }
  }

  function setSelected(uid) {
    selected = uid;
    Array.prototype.forEach.call(svg.querySelectorAll(".cmap-a"), function (a) {
      a.classList.toggle("is-selected", uid !== null && a.getAttribute("data-uid") === uid);
    });
    rest();
  }

  svg.addEventListener("pointerover", function (ev) {
    if (ev.pointerType === "touch") return;
    var a = ev.target.closest && ev.target.closest(".cmap-a");
    if (!a || a.classList.contains("cmap-va")) return;
    var uid = a.getAttribute("data-uid");
    last = uid;
    show(uid); highlight(uid, false);
  });
  svg.addEventListener("pointerout", function (ev) {
    if (ev.pointerType === "touch") return;
    var a = ev.target.closest && ev.target.closest(".cmap-a");
    if (a && !a.classList.contains("cmap-va")) rest();
  });
  svg.addEventListener("focusin", function (ev) {
    var a = ev.target.closest && ev.target.closest(".cmap-a");
    if (!a || a.classList.contains("cmap-va")) return;
    var uid = a.getAttribute("data-uid");
    last = uid;
    show(uid); highlight(uid, true);
  });
  svg.addEventListener("focusout", function (ev) {
    /* Tab from a shape into the panel (its "Open page" link): the panel already shows that area. Redrawing it here
       removed the link focus was moving to, and focus fell back to the page (debug pass 2026-11-09). */
    if (ev.relatedTarget && panel.contains(ev.relatedTarget)) return;
    var a = ev.target.closest && ev.target.closest(".cmap-a");
    if (!a || !a.classList.contains("cmap-va")) rest();
  });
  svg.addEventListener("pointerdown", function (ev) { lastTouch = ev.pointerType === "touch" || ev.pointerType === "pen"; });
  svg.addEventListener("click", function (ev) {
    var a = ev.target.closest && ev.target.closest(".cmap-a");
    if (a && a.classList.contains("cmap-va")) return;
    if (!a) { if (lastTouch) setSelected(null); return; }
    var uid = a.getAttribute("data-uid");
    if (lastTouch && selected !== uid) { ev.preventDefault(); setSelected(uid); }
  });

  function setLayer(tab) {
    Array.prototype.forEach.call(root.querySelectorAll(".cmap-tab"), function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-layer") === tab ? "true" : "false");
    });
    Array.prototype.forEach.call(doc.querySelectorAll("[data-layer]"), function (el) {
      if (el.classList.contains("cmap-tab")) return;
      el.classList.toggle("is-on", el.getAttribute("data-layer") === tab);
    });
    last = null;
    setSelected(null);
    // Only the standalone map page records its layer in the address; an embedded map (the landing
    // page's picker) must leave the reader's own hash alone.
    // A map marked data-hash="off" (the budgets page's money map) also leaves it alone.
    if (!root.closest(".pick") && !noHash) { try { history.replaceState(null, "", "#" + tab); } catch (e) {} }
    root.dispatchEvent(new CustomEvent("cmap-layer", { detail: tab }));
  }
  // a mode script that changes what the panel shows (static/js/indicator_map.js) asks for a redraw
  root.addEventListener("cmap-refresh", rest);
  // another script selects an area (static/js/preselect.js, the saved-place preselect; added 2026-11-09, Wave E
  // batch 8): "cmap-select" with detail {uid} switches to the layer holding that area and selects it, so the panel
  // shows it until the reader points at another area; {uid: null} clears the selection. The address is not touched.
  root.addEventListener("cmap-select", function (ev) {
    var uid = ev.detail && ev.detail.uid ? ev.detail.uid : null;
    if (!uid) { last = null; setSelected(null); return; }
    var shape = null;
    Array.prototype.forEach.call(svg.querySelectorAll(".cmap-a[data-uid]"), function (a) {
      if (!shape && a.getAttribute("data-uid") === uid && !a.classList.contains("cmap-va")) shape = a;
    });
    if (!shape || !data[uid]) return;
    var g = shape.closest ? shape.closest("[data-layer]") : null;
    var tab = g ? g.getAttribute("data-layer") : null;
    var on = root.querySelector('.cmap-tab[aria-pressed="true"]');
    if (tab && (!on || on.getAttribute("data-layer") !== tab)) setLayer(tab);
    setSelected(uid);
  });
  tabs.addEventListener("click", function (ev) {
    var b = ev.target.closest && ev.target.closest(".cmap-tab");
    if (b) setLayer(b.getAttribute("data-layer"));
  });
  var want = noHash ? "" : (location.hash || "").replace("#", "");
  // #race-<race id> (links from the Results page): open "How areas voted" with that race; map_votes.js reads
  // data-want-race when its data file has loaded.
  if (/^race-[A-Za-z0-9-]+$/.test(want) && root.querySelector(".cmap-vctl")) {
    root.setAttribute("data-want-race", want.slice(5));
    want = "votes";
  }
  if (want === "cities" || want === "townships" || want === "schools" || (want === "votes" && root.querySelector(".cmap-vctl"))) setLayer(want);
  else setLayer(root.getAttribute("data-default-layer"));
})();
