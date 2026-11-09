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
    u.f.forEach(function (r) { dl.appendChild(el("dt", null, r[0])); dl.appendChild(el("dd", null, r[1])); });
    panel.appendChild(dl);
    if (u.note) panel.appendChild(el("p", "cmap-note", u.note));
    var link = el("a", "btn cmap-open", "Open page");
    link.setAttribute("href", u.href);
    panel.appendChild(link);
  }

  function highlight(uid, focus) {
    while (hlg.firstChild) hlg.removeChild(hlg.firstChild);
    if (!uid || !data[uid]) return;
    var p = doc.createElementNS(NS, "path");
    p.setAttribute("d", data[uid].d);
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
    if (!root.closest(".pick")) { try { history.replaceState(null, "", "#" + tab); } catch (e) {} }
    root.dispatchEvent(new CustomEvent("cmap-layer", { detail: tab }));
  }
  tabs.addEventListener("click", function (ev) {
    var b = ev.target.closest && ev.target.closest(".cmap-tab");
    if (b) setLayer(b.getAttribute("data-layer"));
  });
  var want = (location.hash || "").replace("#", "");
  if (want === "cities" || want === "townships" || want === "schools" || (want === "votes" && root.querySelector(".cmap-vctl"))) setLayer(want);
  else setLayer(root.getAttribute("data-default-layer"));
})();
