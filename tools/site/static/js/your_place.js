/* your_place.js: the "Your place" page (your-governments/, pages/participate.py build_governments).
   Reads the saved place (localStorage "civic-place" = {"place": id, "township": id|"any", "school": id|"any"}, the key
   static/js/here.js writes) and shows only the cards of the governments that cover it, with the "Showing" line and the
   hero counts summed from those cards. With no saved place it shows the inline place list; its links become buttons
   that save the place (same defaults as the home picker) and show it here. here.js is told through a "storage" event,
   so the "You are here" bar follows. Without JavaScript every card and every link is on the page.
   Plain JS, ASCII only, data inserted with textContent only. */
(function () {
  "use strict";
  var doc = document;
  var dek = doc.getElementById("yp-dek");
  if (!dek) return;
  var KEY = "civic-place";
  var DOT = " " + String.fromCharCode(183) + " ";
  var site = doc.getElementById("site");
  var ROOT = (site && site.getAttribute("data-root")) || "./";
  var H = null;
  try { H = JSON.parse((doc.getElementById("here-data") || {}).textContent || "null"); } catch (e) { H = null; }
  if (!H || !H.places) return;
  function has(o, k) { return !!o && Object.prototype.hasOwnProperty.call(o, k); }
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }
  function q(sel) { return doc.querySelectorAll(sel); }

  function normalize(v) {
    if (!v || typeof v !== "object" || !has(H.places, v.place)) return null;
    var p = H.places[v.place];
    return { place: v.place, township: p.t || (has(H.townships, v.township) ? v.township : "any"),
             school: has(H.schools, v.school) ? v.school : "any" };
  }
  function load() {
    var raw = null;
    try { raw = window.localStorage.getItem(KEY); } catch (e) { raw = null; }
    if (!raw) return null;
    try { return normalize(JSON.parse(raw)); } catch (e) { return null; }
  }
  var current = null;   /* the place chosen on this page when storage is blocked */
  function save(st) {
    current = st;
    try { window.localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) { /* this page only */ }
  }
  function fresh(id) {
    var p = H.places[id];
    return normalize({ place: id, township: p.t || p.td || "any", school: p.sd || "any" });
  }

  var choosing = false;

  function names(st) {
    var p = H.places[st.place], out = [{ text: p.n, href: p.u }];
    if (!p.t) {
      out.push(st.township !== "any" ? { text: H.townships[st.township], href: "places/" + st.township + "/index.html" }
                                      : { text: "township not picked", href: null });
    }
    out.push(st.school !== "any" ? { text: H.schools[st.school], href: "schools/index.html#" + st.school }
                                 : { text: "school corporation not picked", href: null });
    return out;
  }

  function render() {
    var st = load() || current;
    var p = st ? H.places[st.place] : null;
    var want = { "state": 1, "county": 1, "library": 1 };
    want["township:" + (st ? st.township : "any")] = 1;
    want["school:" + (st ? st.school : "any")] = 1;
    if (p && p.m) want["municipality:" + p.m] = 1;
    var tot = { gov: 0, elected: 0, vote: 0, appointed: 0, unknown: 0, unknownApp: 0 };
    each(q(".yp-card[data-layer]"), function (el) {
      var on = !!want[el.getAttribute("data-layer")];
      el.hidden = !on;
      if (!on) return;
      tot.gov += +el.getAttribute("data-gov");
      tot.elected += +el.getAttribute("data-elected");
      tot.vote += +el.getAttribute("data-vote");
      tot.appointed += +el.getAttribute("data-appointed");
      tot.unknown += +el.getAttribute("data-unknown");
      tot.unknownApp += +el.getAttribute("data-unknown-appointed");
    });
    each(q("[data-yp-group]"), function (g) { g.hidden = !g.querySelector(".yp-card:not([hidden])"); });
    function set(k, v) { each(q('[data-yp="' + k + '"]'), function (el) { el.textContent = v; }); }
    function hide(k, v) { each(q('[data-yp="' + k + '"]'), function (el) { el.hidden = v; }); }
    set("gov", tot.gov); set("elected", tot.elected); set("vote", tot.vote); set("appointed", tot.appointed);
    hide("lead-none", !!p); hide("lead-place", !p);
    hide("atleast-gov", !!p);
    hide("atleast", !!p && tot.unknown === 0);
    hide("atleast-appointed", tot.unknownApp === 0);

    var showing = doc.getElementById("yp-showing"), list = doc.getElementById("yp-names");
    if (showing && list) {
      while (list.firstChild) list.removeChild(list.firstChild);
      if (st) {
        names(st).forEach(function (n, i) {
          if (i) list.appendChild(doc.createTextNode(DOT));
          var el = doc.createElement(n.href ? "a" : "span");
          if (n.href) el.href = ROOT + n.href; else el.className = "here-missing";
          el.textContent = n.text;
          list.appendChild(el);
        });
      } else {
        list.textContent = "no place picked yet";
      }
      showing.hidden = false;
    }
    var choose = doc.querySelector("[data-yp-choose]");
    if (choose) choose.hidden = !!p && !choosing;
    each(q("button.yp-choice"), function (b) {
      b.setAttribute("aria-pressed", st && st.place === b.getAttribute("data-yp-place") ? "true" : "false");
    });
    var again = doc.getElementById("yp-again");
    if (again) {
      again.parentNode.hidden = !p;
      again.setAttribute("aria-expanded", choosing ? "true" : "false");
      again.textContent = choosing ? "Hide the list of places" : "Choose a different place here";
    }
    each(q(".yp-none-note"), function (el) { el.hidden = !!p; });
  }

  /* the no-JavaScript sentences give way to the JavaScript ones */
  each(q(".yp-nojs"), function (el) { el.hidden = true; });
  each(q(".yp-js:not(.yp-none-note)"), function (el) { el.hidden = false; });

  /* place links become buttons that pick the place here (a link that did not go anywhere would mislead) */
  each(q("a.yp-choice[data-yp-place]"), function (a) {
    var b = doc.createElement("button");
    b.type = "button";
    b.className = "yp-choice";
    b.setAttribute("data-yp-place", a.getAttribute("data-yp-place"));
    b.setAttribute("aria-pressed", "false");
    b.textContent = a.textContent;
    a.parentNode.replaceChild(b, a);
  });

  function tellHere() {
    try { window.dispatchEvent(new StorageEvent("storage", { key: KEY })); } catch (e) { /* old browser: bar updates on next page */ }
  }

  doc.addEventListener("click", function (ev) {
    var b = ev.target.closest ? ev.target.closest("button.yp-choice") : null;
    if (b) {
      var id = b.getAttribute("data-yp-place");
      if (!has(H.places, id)) return;
      save(fresh(id));
      choosing = false;
      render();
      tellHere();
      var showing = doc.getElementById("yp-showing");
      if (showing) showing.focus();
      return;
    }
    if (ev.target.closest && ev.target.closest("#yp-again")) {
      choosing = !choosing;
      render();
      if (choosing) {
        var first = doc.querySelector("button.yp-choice");
        if (first) first.focus();
      }
    }
  });

  window.addEventListener("storage", function (ev) {
    if (ev.key === KEY) render();
  });
  render();
})();
