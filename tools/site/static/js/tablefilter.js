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
   ASCII only. */
(function () {
  "use strict";
  var doc = document;

  function each(list, fn) { Array.prototype.forEach.call(list, fn); }

  function init(bar) {
    var table = doc.getElementById(bar.getAttribute("data-tf-table"));
    if (!table || !table.tBodies.length) return;
    var tbody = table.tBodies[0];
    var rows = Array.prototype.slice.call(tbody.rows);
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
        r.hidden = !ok;
        if (ok) shown++;
      });
      var spec = specOf();
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
      apply();
    });
    bar.hidden = false;
    apply();
  }

  each(doc.querySelectorAll(".tf[data-tf-table]"), init);
})();
