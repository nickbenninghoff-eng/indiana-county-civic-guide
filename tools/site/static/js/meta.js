/* meta.js: data page. A "Copy CSV" button with data-copy-csv="<id>" copies the full dataset
   stored as a JSON string in <script type="application/json" id="<id>">. The preview table on
   the page holds only some rows, so this copies the embedded text, not the table. */
(function () {
  "use strict";
  var doc = document;

  function statusEl(btn) {
    var s = btn.parentNode.querySelector(".copy-status");
    if (!s) {
      s = doc.createElement("span");
      s.className = "copy-status";
      s.setAttribute("role", "status");
      btn.parentNode.appendChild(s);
    }
    return s;
  }

  doc.addEventListener("click", function (ev) {
    var btn = ev.target.closest ? ev.target.closest("[data-copy-csv]") : null;
    if (!btn) return;
    var holder = doc.getElementById(btn.getAttribute("data-copy-csv"));
    if (!holder) return;
    var csv;
    try { csv = JSON.parse(holder.textContent || "\"\""); } catch (e) { return; }
    var status = statusEl(btn);
    var rows = btn.getAttribute("data-rows") || "all";
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
      navigator.clipboard.writeText(csv).then(function () {
        status.textContent = "Copied " + rows + " rows.";
      }, fallback);
    } else {
      fallback();
    }
  });
})();
