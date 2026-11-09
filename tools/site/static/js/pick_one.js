/* pick_one.js: "show one" navigation (civic/pick_one.py). Choosing an area on the map, in a list, in the table of
   contents or by an #anchor in the address opens that area's items (details[data-one=KEY]) and closes the other
   areas' items. Nothing is removed: every other area stays one click away on its summary line, and with JavaScript
   off every item ships open. Blocks or table rows marked data-one that are not <details> are hidden while some
   areas are open and theirs is not; a table whose rows are hidden fires "rows-filtered" so Copy CSV (static/app.js)
   copies only the rows shown. Runs after folds.js, which closes every details[data-fold] on load. ASCII only;
   text is inserted with textContent. */
(function () {
  "use strict";
  var doc = document;
  function all(sel) { return Array.prototype.slice.call(doc.querySelectorAll(sel)); }
  var items = all("details[data-one]");
  if (!items.length) return;
  var blocks = all("[data-one]").filter(function (el) { return el.tagName !== "DETAILS"; });
  var wraps = all("details[data-one-wrap]");
  var scopes = all("[data-one-scope]");
  var bars = all("[data-one-bar]");
  var names = {}, keys = [];
  items.forEach(function (d) {
    var k = d.getAttribute("data-one");
    if (!Object.prototype.hasOwnProperty.call(names, k)) { keys.push(k); names[k] = d.getAttribute("data-one-name") || k; }
  });

  function keyOf(el) {
    var n = el && el.closest ? el.closest("[data-one], [data-one-for]") : null;
    if (!n) return null;
    var k = n.getAttribute("data-one") || n.getAttribute("data-one-for");
    return Object.prototype.hasOwnProperty.call(names, k) ? k : null;
  }

  function targetOf(hash) {
    if (!hash || hash.length < 2) return null;
    var id = hash.slice(1);
    try { id = decodeURIComponent(id); } catch (e) { /* keep the raw id */ }
    return doc.getElementById(id);
  }

  function openKeys() {
    var open = {}, n = 0;
    items.forEach(function (d) {
      var k = d.getAttribute("data-one");
      if (d.open && !open[k]) { open[k] = true; n += 1; }
    });
    return { set: open, n: n };
  }

  function listNames(open) {
    var out = [];
    keys.forEach(function (k) { if (open[k]) out.push(names[k]); });
    if (out.length > 3) return out.slice(0, 3).join(", ") + " and " + (out.length - 3) + " more";
    return out.join(", ");
  }

  function sync() {
    var o = openKeys();
    var some = o.n > 0 && o.n < keys.length;
    var tables = [];
    blocks.forEach(function (el) {
      var hide = some && !o.set[el.getAttribute("data-one")];
      if (el.hidden !== hide) el.hidden = hide;
      var t = el.tagName === "TR" ? el.closest("table") : null;
      if (t && tables.indexOf(t) < 0) tables.push(t);
    });
    tables.forEach(function (t) {
      t.dispatchEvent(new CustomEvent("rows-filtered", { bubbles: true }));
    });
    scopes.forEach(function (s) {
      var note = s.querySelector("[data-one-empty]");
      if (!note) return;
      var has = false;
      if (some) {
        keys.forEach(function (k) { if (o.set[k] && s.querySelector('[data-one="' + k + '"]')) has = true; });
      }
      note.hidden = !some || has;
      if (!note.hidden) note.textContent = (s.getAttribute("data-one-empty-text") || "").replace("{name}", listNames(o.set));
    });
    bars.forEach(function (b) {
      var plural = b.getAttribute("data-one-plural") || "items";
      var state = b.querySelector("[data-one-state]");
      var txt;
      if (o.n === 0) txt = b.getAttribute("data-one-hint") || "";
      else if (o.n === keys.length) txt = "Showing all " + keys.length + " " + plural + ".";
      else if (o.n === 1) txt = "Showing " + listNames(o.set) + ". The other " + plural + " are collapsed below.";
      else txt = o.n + " of " + keys.length + " " + plural + " open: " + listNames(o.set) + ".";
      if (state) state.textContent = txt;
      var showAll = b.querySelector("[data-one-all]"), none = b.querySelector("[data-one-none]");
      if (showAll) showAll.hidden = o.n === keys.length;
      if (none) none.hidden = o.n === 0;
      b.hidden = false;
    });
  }

  function choose(k) {
    items.forEach(function (d) {
      var on = d.getAttribute("data-one") === k;
      if (d.open !== on) d.open = on;
    });
    wraps.forEach(function (w) { if (!w.open && w.querySelector('[data-one="' + k + '"]')) w.open = true; });
    sync();
  }

  function setAll(open) {
    items.forEach(function (d) { if (d.open !== open) d.open = open; });
    wraps.forEach(function (w) { if (w.open !== open) w.open = open; });
    sync();
  }

  /* open every closed <details> around the target (a chart's "Show table", say) */
  function reveal(t) {
    for (var n = t; n && n !== doc.body; n = n.parentElement) {
      if (n.tagName === "DETAILS" && !n.open) n.open = true;
    }
  }

  /* a link to an area (map shape, list, table of contents, panel link): choose it before the browser scrolls */
  doc.addEventListener("click", function (ev) {
    if (ev.defaultPrevented || ev.button > 0 || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
    var a = ev.target && ev.target.closest ? ev.target.closest("a[href]") : null;
    if (!a || !a.hash || a.hash.length < 2) return;
    if (a.pathname !== window.location.pathname || a.host !== window.location.host) return;
    var t = targetOf(a.hash);
    var k = keyOf(t);
    if (k === null) return;
    choose(k);
    reveal(t);
  });

  window.addEventListener("hashchange", function () {
    var t = targetOf(window.location.hash);
    var k = keyOf(t);
    if (k === null) return;
    choose(k);
    reveal(t);
    if (t.scrollIntoView) t.scrollIntoView();
  });

  bars.forEach(function (b) {
    b.addEventListener("click", function (ev) {
      var btn = ev.target && ev.target.closest ? ev.target.closest("button") : null;
      if (!btn) return;
      if (btn.hasAttribute("data-one-all")) setAll(true);
      else if (btn.hasAttribute("data-one-none")) setAll(false);
    });
  });

  /* a reader opening or closing a summary by hand */
  var pending = false;
  items.forEach(function (d) {
    d.addEventListener("toggle", function () {
      if (pending) return;
      pending = true;
      window.setTimeout(function () { pending = false; sync(); }, 0);
    });
  });

  /* on load: an address pointing inside an area chooses it (folds.js has already opened its fold) */
  var landing = targetOf(window.location.hash);
  var lk = keyOf(landing);
  if (lk !== null) {
    choose(lk);
    reveal(landing);
    if (landing.scrollIntoView) landing.scrollIntoView();
  } else {
    sync();
  }
})();
