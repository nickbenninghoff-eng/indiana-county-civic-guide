/* onpage.js: the sticky "On this page" bar and a "Back to top" link at each h2, on the long pages
   (civic/shell.py ONPAGE_PAGES marks them with data-onpage="1" on #site).
   Built from the page's own table of contents (nav.toc). Without JavaScript that table of contents is all there is:
   a plain list of links, not sticky. With it, once the table of contents has scrolled out of sight a compact bar
   appears under the primary nav: a labelled select (the section you are in is selected; choosing another jumps to it,
   by clicking the table of contents' own link, so folds.js opens any fold that holds the target) and "Back to top".
   The bar is position:fixed under the nav, so html gets a larger scroll-padding-top (class has-onpage, --nav-h and
   --onpage-h from static/css/onpage.css) and no jump or Tab lands behind it. It is one select and one link: nothing
   to trap focus. The h2 "Back to top" links show on phones only (CSS). ASCII only. */
(function () {
  "use strict";
  var doc = document;
  var root = doc.documentElement;
  var site = doc.getElementById("site");
  if (!site || site.getAttribute("data-onpage") !== "1") return;
  var toc = doc.querySelector("main nav.toc");
  var nav = doc.querySelector(".nav");
  if (!toc || !nav) return;

  var items = [];
  Array.prototype.forEach.call(toc.querySelectorAll("a[href^='#']"), function (a) {
    var id = a.getAttribute("href").slice(1);
    try { id = decodeURIComponent(id); } catch (e) { /* keep the raw id */ }
    var t = doc.getElementById(id);
    if (t) items.push({ a: a, target: t, label: (a.textContent || "").replace(/\s+/g, " ").trim() });
  });
  if (items.length < 3) return;

  function px(v) { var n = parseFloat(v); return isFinite(n) ? n : 0; }
  function el(tag, cls, text) {
    var e = doc.createElement(tag);
    if (cls) e.className = cls;
    if (text) e.textContent = text;
    return e;
  }

  /* ---- the bar */
  var bar = el("div", "onpage");
  bar.id = "onpage";
  bar.setAttribute("role", "group");
  bar.setAttribute("aria-label", "Move around this page");
  bar.hidden = true;
  var label = el("label", "onpage-label", "On this page");
  label.setAttribute("for", "onpage-select");
  var sel = el("select", "onpage-select");
  sel.id = "onpage-select";
  var first = el("option", "", "Jump to a section");
  first.value = "";
  sel.appendChild(first);
  items.forEach(function (it, i) {
    var o = el("option", "", (i < 9 ? "0" : "") + (i + 1) + "  " + it.label);
    o.value = String(i);
    sel.appendChild(o);
  });
  var top = el("a", "onpage-top", "Back to top");
  top.href = "#site";
  bar.appendChild(label);
  bar.appendChild(sel);
  bar.appendChild(top);
  toc.parentNode.insertBefore(bar, toc.nextSibling);
  root.classList.add("has-onpage");

  sel.addEventListener("change", function () {
    var it = items[parseInt(sel.value, 10)];
    if (it) it.a.click();
  });

  /* ---- Back to top: after each h2 (a phone-only link, see onpage.css) and in the bar */
  function toTop(ev) {
    ev.preventDefault();
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
    if (window.history && window.history.replaceState && window.location.hash) {
      try { window.history.replaceState(null, "", window.location.pathname + window.location.search); } catch (e) { /* keep the hash */ }
    }
    var h1 = doc.querySelector("main h1");
    if (h1) { h1.setAttribute("tabindex", "-1"); h1.focus({ preventScroll: true }); }
  }
  top.addEventListener("click", toTop);
  Array.prototype.forEach.call(doc.querySelectorAll("main h2"), function (h) {
    if (toc.contains(h)) return;
    var a = el("a", "to-top", "Back to top");
    a.href = "#site";
    a.addEventListener("click", toTop);
    h.parentNode.insertBefore(a, h.nextSibling);
  });

  /* ---- sizes: --nav-h from the real nav; scroll-padding-top follows (CSS) */
  function measure() {
    root.style.setProperty("--nav-h", nav.offsetHeight + "px");
  }
  measure();
  window.addEventListener("resize", measure);

  /* ---- show once the table of contents is above the nav; follow the section in view */
  var ticking = false;
  function update() {
    ticking = false;
    var navBottom = nav.getBoundingClientRect().bottom;
    var on = toc.getBoundingClientRect().bottom < navBottom;
    if (bar.hidden === on) bar.hidden = !on;
    if (!on) return;
    var line = px(window.getComputedStyle(root).scrollPaddingTop) + 24;
    var cur = -1;
    for (var i = 0; i < items.length; i++) {
      if (items[i].target.getBoundingClientRect().top <= line) cur = i; else break;
    }
    var want = cur < 0 ? "" : String(cur);
    if (sel.value !== want && doc.activeElement !== sel) sel.value = want;
  }
  function schedule() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(update);
    window.setTimeout(update, 150); /* a hidden or throttled frame may never run the animation frame */
  }
  window.addEventListener("scroll", schedule, { passive: true });
  window.addEventListener("resize", schedule);
  window.addEventListener("load", schedule);
  update();
})();
