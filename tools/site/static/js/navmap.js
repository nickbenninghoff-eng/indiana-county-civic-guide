/* navmap.js: the map navigator (civic/navmap.py; maps on every major page, 2026-11-18). ASCII only; text is inserted
   with textContent; nothing is fetched or stored (the shapes are <use> references to assets/navmap.svg, which the
   browser loads like an image; the saved place is read through window.civicHere, static/js/here.js).

   Markup contract (civic/navmap.py navigator):
     <div class="nm" data-nm-target="ID [ID...]" data-nm-noun data-nm-plural data-nm-default="LAYER">
       .nm-bar (hidden without JS) > button.nm-tab[data-nm-layer][aria-pressed]
       svg.nm-svg > g.nm-layer[data-nm-layer] > ... a.nm-a[data-nm-key][data-nm-name][href]
       .nm-side > p.nm-status (role=status, aria-live polite), p.nm-peek, p.nm-actions (a.nm-open, button.nm-all),
                  ul.nm-chips > a.nm-chip[data-nm-key] (areas with no shape on this map)
     Rows: any element inside a target carrying data-nm="KEY KEY ..." (civic/navmap.py Tags).

   Behaviour:
   - Without JavaScript every area and chip is a plain link to the area's page; the default layer is drawn; the list
     is whole.
   - Pointing at or focusing an area says, in the peek line, how many rows it has on this page.
   - Selecting (click, Enter, or Space on an area with no page) filters every target to that area's rows and says so
     in the status line (polite live region): "Showing 9 offices for City of South Bend." The actions offer the area's
     page and "Show every ...". Selecting the selected area again follows its link. Focus never moves on its own.
   - A target with a table filter bar (static/js/tablefilter.js) is filtered through its "tf-scope" event, so the
     bar's count, folds and Copy CSV agree; other targets hide the rows with the class nm-out and hide a
     [data-nm-group] / [data-tf-group] that has no row left, opening a closed <details> that holds a shown row.
   - An area with no row on this page is not filtered to nothing: the status says so and the whole list stays.
   - The saved place: when the page has no saved-place line of its own ([data-here-pre]) and the reader came without
     an explicit #anchor, the reader's city or town (else township, else school corporation) is selected at load
     when it has rows here; the status says it comes from the saved place. On a page with its own saved-place line,
     a map selection first turns that line off (its button offers it again), and applying the line clears the map. */
(function () {
  "use strict";
  var doc = document;
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }
  function ev(name, detail) { return new CustomEvent(name, { detail: detail }); }

  function init(root) {
    var targets = (root.getAttribute("data-nm-target") || "").split(/\s+/).map(function (id) {
      return id ? doc.getElementById(id) : null;
    }).filter(Boolean);
    if (!targets.length) return;
    var noun = root.getAttribute("data-nm-noun") || "row";
    var plural = root.getAttribute("data-nm-plural") || "rows";
    var bar = root.querySelector(".nm-bar");
    var svg = root.querySelector(".nm-svg");
    var status = root.querySelector(".nm-status");
    var peek = root.querySelector(".nm-peek");
    var actions = root.querySelector(".nm-actions");
    var openLink = root.querySelector(".nm-open");
    var allBtn = root.querySelector(".nm-all");
    var fold = root.querySelector(".nm-fold");
    var hint = status ? status.textContent : "";
    var selected = null, fromSaved = false;
    root.classList.add("nm-js");
    if (bar) bar.hidden = false;

    /* rows and their keys, counted once */
    /* a row's keys: data-nm holds base-36 numbers into the page's key list, data-nm-dict on this root
       (civic/navmap.py compact_row_keys, 2026-11-18: the full keys on 1,200 rows weighed 57 KB on one page); a value
       that is not a number is a key as written */
    var dict = (root.getAttribute("data-nm-dict") || "").split(" ");
    var decoded = typeof WeakMap === "function" ? new WeakMap() : null;
    function keysAttr(r) {
      var got = decoded ? decoded.get(r) : null;
      if (got != null) return got;
      var out = (r.getAttribute("data-nm") || "").split(" ").map(function (t) {
        if (!t) return "";
        var i = /^[0-9a-z]+$/.test(t) && t.indexOf(":") < 0 ? parseInt(t, 36) : NaN;
        return (i === i && dict[i]) ? dict[i] : t;
      }).join(" ");
      if (decoded) decoded.set(r, out);
      return out;
    }
    var rows = [];
    targets.forEach(function (t) { each(t.querySelectorAll("[data-nm]"), function (r) { rows.push(r); }); });
    var keysOf = rows.map(function (r) { return " " + keysAttr(r) + " "; });
    var counts = {};
    /* data-nm-count: only the rows inside that element are counted (the Elections hub counts elections, not the
       next ballot's offices it also filters) */
    var countEl = root.getAttribute("data-nm-count") ? doc.getElementById(root.getAttribute("data-nm-count")) : null;
    if (countEl) keysOf = rows.filter(function (r) { return countEl.contains(r); }).map(function (r) {
      return " " + keysAttr(r) + " ";
    });
    keysOf.forEach(function (ks) {
      ks.split(" ").forEach(function (k) { if (k) counts[k] = (counts[k] || 0) + 1; });
    });
    function rowHas(r, key) { return (" " + keysAttr(r) + " ").indexOf(" " + key + " ") >= 0; }
    function tfBar(t) {
      var found = null;
      each(doc.querySelectorAll(".tf[data-tf-table]"), function (b) {
        if (!found && b.getAttribute("data-tf-table") === t.id && !b.hidden) found = b;
      });
      return found;
    }
    function areas() { return root.querySelectorAll("[data-nm-key]"); }
    function nameOf(key) {
      var n = "";
      each(areas(), function (a) {
        if (!n && a.getAttribute("data-nm-key") === key) n = a.getAttribute("data-nm-name") || a.getAttribute("aria-label");
      });
      return n;
    }
    function hrefOf(key) {
      var u = null;
      each(areas(), function (a) { if (u === null && a.getAttribute("data-nm-key") === key && a.hasAttribute("href")) u = a.getAttribute("href"); });
      return u;
    }
    function words(n) { return n + " " + (n === 1 ? noun : plural); }

    /* ---------------------------------------------------------------- filtering */
    var opened = [];
    function plain(t, key) {
      var inT = [];
      each(t.querySelectorAll("[data-nm]"), function (r) { inT.push(r); });
      inT.forEach(function (r) { r.classList.toggle("nm-out", !!key && !rowHas(r, key)); });
      each(t.querySelectorAll("[data-nm-group], [data-tf-group]"), function (g) {
        if (!key) { g.classList.remove("nm-out"); return; }
        var any = false;
        each(g.querySelectorAll("[data-nm]"), function (r) { if (!any && !r.classList.contains("nm-out")) any = true; });
        var holds = g.querySelectorAll("[data-nm]").length > 0;
        g.classList.toggle("nm-out", holds && !any);
      });
      /* a target that is itself a group (a cycle's section) hides when the choice leaves it no row */
      if (t.hasAttribute("data-nm-group")) {
        var left = false;
        inT.forEach(function (r) { if (!left && !r.classList.contains("nm-out")) left = true; });
        t.classList.toggle("nm-out", !!key && inT.length > 0 && !left);
      }
      if (key) {
        each(t.querySelectorAll("details"), function (d) {
          if (d.open) return;
          var any = false;
          each(d.querySelectorAll("[data-nm]"), function (r) { if (!any && !r.classList.contains("nm-out")) any = true; });
          if (any) { d.open = true; opened.push(d); }
        });
      }
    }
    function apply(key) {
      opened.forEach(function (d) { d.open = false; });
      opened = [];
      targets.forEach(function (t) {
        /* a list with its own filter script (data-nm-own: the filings explorer, campaigns.js) filters itself */
        if (t.hasAttribute("data-nm-own")) {
          t.dispatchEvent(ev("nm-scope", key ? { test: function (r) { return rowHas(r, key); } } : null));
          return;
        }
        var b = tfBar(t);
        if (b) {
          b.dispatchEvent(ev("tf-scope", key ? { nm: true, test: function (r) { return !r.hasAttribute("data-nm") || rowHas(r, key); } } : null));
          /* rows of this target outside the bar's rows (none in practice) follow the plain way */
        } else {
          plain(t, key);
        }
        /* the folds around the list, and a see-all fold or any closed fold inside it holding a shown row, open
           (tablefilter opens only its own groups); "Show every ..." closes again only what this script opened */
        if (key) {
          for (var up = t; up && up !== doc.body; up = up.parentElement) {
            if (up.tagName === "DETAILS" && !up.open) { up.open = true; opened.push(up); }
          }
          each(t.querySelectorAll("details"), function (d) {
            if (d.open) return;
            var any = false;
            each(d.querySelectorAll("[data-nm]"), function (r) { if (!any && rowHas(r, key) && !r.hidden) any = true; });
            if (any) { d.open = true; opened.push(d); }
          });
        }
      });
    }

    /* other saved-place lines on the page ("Showing: your governments"): a map choice turns them off */
    function pausePreselect() {
      each(doc.querySelectorAll("[data-here-pre].is-on .here-pre-btn"), function (b) { b.click(); });
    }

    /* the selected area's outline is drawn again on top (a copy of its <use>); moving the area itself would drop
       keyboard focus */
    var NS = "http://www.w3.org/2000/svg";
    var hl = null;
    if (svg) {
      hl = doc.createElementNS(NS, "g");
      hl.setAttribute("class", "nm-hl-g");
      hl.setAttribute("aria-hidden", "true");
      var clip = svg.querySelector("clipPath[id]");
      if (clip) hl.setAttribute("clip-path", "url(#" + clip.id + ")");
      svg.appendChild(hl);
    }
    function highlight(key) {
      if (!hl) return;
      while (hl.firstChild) hl.removeChild(hl.firstChild);
      if (!key) return;
      each(svg.querySelectorAll(".nm-a"), function (a) {
        if (a.getAttribute("data-nm-key") !== key) return;
        var u = a.querySelector("use");
        if (!u) return;
        var c = doc.createElementNS(NS, "use");
        c.setAttribute("href", u.getAttribute("href"));
        c.setAttribute("class", "nm-hl");
        hl.appendChild(c);
      });
    }

    function say(text) { if (status) status.textContent = text; }

    function setSelected(key, opts) {
      opts = opts || {};
      selected = key;
      fromSaved = !!opts.saved;
      each(areas(), function (a) {
        var on = !!key && a.getAttribute("data-nm-key") === key;
        a.classList.toggle("is-sel", on);
        if (on) a.setAttribute("aria-current", "true"); else a.removeAttribute("aria-current");
      });
      highlight(key);
      if (!key) {
        apply(null);
        say(opts.quiet ? hint : "Showing every " + noun + ".");
        if (actions) actions.hidden = true;
        return;
      }
      var name = nameOf(key);
      var n = counts[key] || 0;
      if (!opts.saved) pausePreselect();
      if (n) apply(key); else apply(null);
      var lead = opts.saved ? "Your saved place (kept on this device only): " : "";
      if (n) say(lead + "Showing " + words(n) + " for " + name + ".");
      else say(lead + "No " + plural + " for " + name + " on this page, so every " + noun + " is still shown.");
      var u = hrefOf(key);
      if (openLink) {
        openLink.hidden = !u;
        if (u) {
          openLink.setAttribute("href", u);
          openLink.textContent = "Open " + name;
        }
      }
      if (allBtn) allBtn.hidden = !n;
      if (actions) actions.hidden = !u && !n;
    }

    /* ---------------------------------------------------------------- layers */
    function setLayer(tab) {
      if (!svg) return;
      each(root.querySelectorAll(".nm-tab"), function (b) {
        b.setAttribute("aria-pressed", b.getAttribute("data-nm-layer") === tab ? "true" : "false");
      });
      each(svg.querySelectorAll(".nm-layer"), function (g) {
        g.classList.toggle("is-on", g.getAttribute("data-nm-layer") === tab);
      });
    }
    function layerOf(key) {
      var tab = null;
      if (!svg) return null;
      each(svg.querySelectorAll(".nm-a"), function (a) {
        if (!tab && a.getAttribute("data-nm-key") === key) {
          var g = a.closest(".nm-layer");
          tab = g ? g.getAttribute("data-nm-layer") : null;
        }
      });
      return tab;
    }
    if (bar) bar.addEventListener("click", function (e) {
      var b = e.target.closest ? e.target.closest(".nm-tab") : null;
      if (b) setLayer(b.getAttribute("data-nm-layer"));
    });

    /* ---------------------------------------------------------------- select, then open */
    function activate(a, e) {
      var key = a.getAttribute("data-nm-key");
      if (key === selected) return;          /* second activation: follow the link (an area with no page: stays) */
      if (e) e.preventDefault();
      var tab = layerOf(key);
      if (tab) setLayer(tab);
      setSelected(key);
    }
    root.addEventListener("click", function (e) {
      var a = e.target.closest ? e.target.closest("[data-nm-key]") : null;
      if (!a || !root.contains(a)) return;
      activate(a, e);
    });
    root.addEventListener("keydown", function (e) {
      var a = e.target.closest ? e.target.closest("[data-nm-key]") : null;
      if (!a || a.hasAttribute("href")) return;   /* a link already turns Enter into a click */
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); activate(a, null); }
    });
    if (allBtn) allBtn.addEventListener("click", function () {
      /* the button hides itself with the actions line: keep keyboard focus on the area that was selected (on the
         map or among the chips), so the reader is not dropped to the top of the page */
      var was = selected;
      setSelected(null);
      var back = null;
      if (was) {
        each(root.querySelectorAll("[data-nm-key]"), function (a) {
          if (!back && a.getAttribute("data-nm-key") === was && a.getClientRects().length) back = a;
        });
      }
      if (back && back.focus) back.focus();
      else if (status) { status.setAttribute("tabindex", "-1"); status.focus(); }
    });

    /* ---------------------------------------------------------------- peek: how many rows an area has here */
    function showPeek(a) {
      if (!peek) return;
      if (!a) { peek.textContent = ""; return; }
      var key = a.getAttribute("data-nm-key");
      var n = counts[key] || 0;
      peek.textContent = (a.getAttribute("data-nm-name") || a.getAttribute("aria-label")) + ": " + (n ? words(n) + " on this page" : "none on this page") +
        (key === selected ? ". Select again to open." : ".");
    }
    root.addEventListener("pointerover", function (e) {
      var a = e.target.closest ? e.target.closest(".nm-a") : null;
      if (a) showPeek(a);
    });
    root.addEventListener("pointerout", function (e) {
      var a = e.target.closest ? e.target.closest(".nm-a") : null;
      if (a) showPeek(null);
    });
    root.addEventListener("focusin", function (e) {
      var a = e.target.closest ? e.target.closest("[data-nm-key]") : null;
      showPeek(a);
    });
    root.addEventListener("focusout", function () { showPeek(null); });

    /* applying another saved-place line clears the map's choice */
    doc.addEventListener("click", function (e) {
      var b = e.target.closest ? e.target.closest(".here-pre-btn") : null;
      if (!b || root.contains(b)) return;
      window.setTimeout(function () {
        var slot = b.closest("[data-here-pre]");
        if (slot && slot.classList.contains("is-on") && selected) setSelected(null, { quiet: true });
      }, 0);
    });
    /* the table filter's Reset drops the map's scope too */
    targets.forEach(function (t) {
      var b = tfBar(t);
      if (b) b.addEventListener("tf-scope-cleared", function () { if (selected) setSelected(null); });
    });

    setLayer(root.getAttribute("data-nm-default"));

    /* ---------------------------------------------------------------- the saved place */
    var H = window.civicHere;
    if (!H || doc.querySelector("[data-here-pre]")) return;
    var m = H.mine();
    if (!m || H.hashWins()) return;
    var keys = [m.muni, m.township, m.school].filter(Boolean).map(function (u) { return "u:" + u; });
    for (var i = 0; i < keys.length; i++) {
      if (counts[keys[i]] && nameOf(keys[i])) {
        var tab = layerOf(keys[i]);
        if (tab) setLayer(tab);
        if (fold && !fold.open) fold.open = true;
        setSelected(keys[i], { saved: true });
        return;
      }
    }
  }

  function setup() { each(doc.querySelectorAll(".nm[data-nm-target]"), init); }
  /* app.js is deferred: wait until every partial (tablefilter.js, here.js) has set up */
  if (doc.readyState !== "complete") doc.addEventListener("DOMContentLoaded", setup);
  else setup();
})();
