/* tablefilter.js: one row of filters above a table (civic/components.py table_filter).
   Progressive enhancement: the bar ships with the hidden attribute and the table ships whole; this
   script shows the bar and then only hides rows (tr.hidden). Nothing is rendered by script.
   Markup contract:
     <div class="tf" data-tf-table="TABLE_ID" data-tf-total data-tf-noun data-tf-plural hidden>
       <select data-tf-key="KEY">   rows carry data-tf-KEY="value"; "" = all
       <input data-tf-q>            every word must appear in the row text
       <select data-tf-sort>        options carry data-spec="attr:dir:kind[,attr:dir:kind]"
       <button data-tf-reset>
       <p data-tf-count>
     </div>
     <p data-tf-empty="TABLE_ID" hidden>
   TABLE_ID may also name a list (any element, e.g. <ul class="ent-list">): its direct children carrying
   data-tf-row are filtered and sorted the same way (added 2026-11-09 for entity_list).
   Deep mode (added 2026-11-09, Wave B batch 2): a container with data-tf-deep filters every descendant carrying
   data-tf-row, wherever it sits (rows grouped under headings and folds: the margins page's areas and seats, the
   calendar's years and governments, the officeholders list). Rows are not re-sorted in deep mode. Each descendant
   marked data-tf-group is hidden while none of its rows is shown; while a filter is on, a group that is (or
   directly holds) a closed <details> with a shown row is opened, and closed again when the filters are cleared.
   Outside scope (added 2026-11-09, Wave E batch 8): the bar listens for a "tf-scope" event whose detail is
   {test: function (row) -> bool} (or null to drop it). Rows the test rejects are hidden as if filtered out, and count
   as filtered for the count line, the folds and Copy CSV. Reset drops the scope too and fires "tf-scope-cleared" on
   the bar. static/js/preselect.js uses it for the saved-place preselect ("Showing: your governments").
   A group marked data-tf-keep (part 2: the calendar's year sections, link targets) is never hidden: while none of
   its rows is shown, its [data-tf-group-empty] note shows instead.
   ASCII only. */
(function () {
  "use strict";
  var doc = document;

  function each(list, fn) { Array.prototype.forEach.call(list, fn); }

  function init(bar) {
    var table = doc.getElementById(bar.getAttribute("data-tf-table"));
    if (!table) return;
    var tbody, rows, groups = [];
    var deep = table.tagName !== "TABLE" && table.hasAttribute("data-tf-deep");
    if (deep) {
      tbody = null;
      rows = Array.prototype.slice.call(table.querySelectorAll("[data-tf-row]"));
      groups = Array.prototype.slice.call(table.querySelectorAll("[data-tf-group]"));
      if (!rows.length) return;
    } else if (table.tagName === "TABLE") {
      if (!table.tBodies.length) return;
      tbody = table.tBodies[0];
      rows = Array.prototype.slice.call(tbody.rows);
    } else {
      /* a list (civic/components.py entity_list): its direct children marked data-tf-row are the rows */
      tbody = table;
      rows = Array.prototype.filter.call(table.children, function (c) { return c.hasAttribute("data-tf-row"); });
      if (!rows.length) return;
    }
    var selects = Array.prototype.slice.call(bar.querySelectorAll("select[data-tf-key]"));
    var q = bar.querySelector("input[data-tf-q]");
    var sortSel = bar.querySelector("select[data-tf-sort]");
    var reset = bar.querySelector("[data-tf-reset]");
    var count = bar.querySelector("[data-tf-count]");
    var empty = doc.querySelector('[data-tf-empty="' + bar.getAttribute("data-tf-table") + '"]');
    var plural = bar.getAttribute("data-tf-plural") || "rows";
    var noun = bar.getAttribute("data-tf-noun") || "row";
    var texts = rows.map(function (r, i) {
      r._tfIndex = i;
      /* a row may name the text a reader's words match (data-tf-text); otherwise its whole text */
      var t = r.hasAttribute("data-tf-text") ? r.getAttribute("data-tf-text") : r.textContent;
      return (t || "").replace(/\s+/g, " ").toLowerCase();
    });
    var lastOrder = "";
    var scope = null;   /* outside scope (tf-scope event): a row test, or null */

    function specOf() {
      if (!sortSel) return null;
      var o = sortSel.options[sortSel.selectedIndex];
      var spec = o && o.getAttribute("data-spec");
      if (!spec) return null;
      return spec.split(",").map(function (part) {
        var p = part.split(":");
        return { attr: "data-" + p[0], dir: p[1] === "desc" ? -1 : 1, num: p[2] === "n" };
      });
    }
    function compare(spec) {
      return function (a, b) {
        for (var i = 0; i < spec.length; i++) {
          var s = spec[i];
          var x = a.getAttribute(s.attr) || "", y = b.getAttribute(s.attr) || "";
          if (s.num) { x = parseFloat(x); y = parseFloat(y); if (isNaN(x)) x = Infinity; if (isNaN(y)) y = Infinity; }
          if (x !== y) return (x < y ? -1 : 1) * s.dir;
        }
        return a._tfIndex - b._tfIndex;
      };
    }

    function apply() {
      var words = q ? q.value.toLowerCase().split(/\s+/).filter(Boolean) : [];
      var want = selects.map(function (s) { return [s.getAttribute("data-tf-key"), s.value]; })
                        .filter(function (p) { return p[1] !== ""; });
      var shown = 0;
      rows.forEach(function (r, i) {
        var ok = true;
        for (var k = 0; ok && k < want.length; k++) {
          if (r.getAttribute("data-tf-" + want[k][0]) !== want[k][1]) ok = false;
        }
        for (var w = 0; ok && w < words.length; w++) {
          if (texts[i].indexOf(words[w]) < 0) ok = false;
        }
        if (ok && scope && !scope(r)) ok = false;
        r.hidden = !ok;
        if (ok) shown++;
      });
      if (deep) showGroups(want.length > 0 || words.length > 0 || !!scope);
      var spec = deep ? null : specOf();
      var order = sortSel ? sortSel.value : "";
      if (spec && order !== lastOrder) {
        rows.slice().sort(compare(spec)).forEach(function (r) { tbody.appendChild(r); });
        lastOrder = order;
      }
      if (count) {
        count.textContent = shown + " of " + rows.length + " " + (rows.length === 1 ? noun : plural) + " shown.";
      }
      if (empty) empty.hidden = shown !== 0;
      table.setAttribute("data-tf-shown", String(shown));
      /* Copy CSV (static/app.js) copies only the rows shown and says how many */
      table.dispatchEvent(new CustomEvent("rows-filtered", { bubbles: true }));
    }

    /* deep mode: hide the groups with no shown row; while filtering, open the folds that hold a shown row */
    function foldOf(g) {
      if (g.tagName === "DETAILS") return g;
      for (var i = 0; i < g.children.length; i++) if (g.children[i].tagName === "DETAILS") return g.children[i];
      return null;
    }
    function showGroups(active) {
      groups.forEach(function (g) {
        var any = false;
        var inside = g.querySelectorAll("[data-tf-row]");
        for (var i = 0; i < inside.length && !any; i++) if (!inside[i].hidden) any = true;
        if (g.hasAttribute("data-tf-keep")) {
          /* a group that is a link target (the calendar's #year-<y>): stays on the page; its note says it is empty */
          g.hidden = false;
          var en = g.querySelector("[data-tf-group-empty]");
          if (en) en.hidden = any || !inside.length;
          return;
        }
        g.hidden = !any;
        var d = foldOf(g);
        if (!d) return;
        if (active && any && !d.open) { d.open = true; d._tfOpened = true; }
        else if (!active && d._tfOpened) { d.open = false; d._tfOpened = false; }
      });
    }

    selects.forEach(function (s) { s.addEventListener("change", apply); });
    if (sortSel) {
      lastOrder = sortSel.options[0].value;   /* the HTML is already in the first option's order; a restored choice re-sorts */
      sortSel.addEventListener("change", apply);
    }
    if (q) {
      q.addEventListener("input", apply);
      q.addEventListener("keydown", function (ev) {
        if (ev.key === "Escape" && q.value) { q.value = ""; apply(); }
      });
    }
    if (reset) reset.addEventListener("click", function () {
      selects.forEach(function (s) { s.selectedIndex = 0; });
      if (q) q.value = "";
      if (sortSel) sortSel.selectedIndex = 0;
      var had = !!scope;
      scope = null;
      apply();
      if (had) bar.dispatchEvent(new CustomEvent("tf-scope-cleared"));
    });
    bar.addEventListener("tf-scope", function (ev) {
      scope = ev.detail && typeof ev.detail.test === "function" ? ev.detail.test : null;
      apply();
    });
    bar.hidden = false;
    apply();
  }

  each(doc.querySelectorAll(".tf[data-tf-table]"), init);
})();
