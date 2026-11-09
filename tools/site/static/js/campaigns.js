/* campaigns.js: filing explorer on money/campaigns/. Rows come from #cf-data (built by pages/campaigns.py).
   Default order is office, district, committee (the order the data arrives in); amount sorts only on request.
   Inserts data with textContent only. ASCII only. */
(function () {
  "use strict";
  var doc = document;
  var node = doc.getElementById("cf-data");
  var block = doc.getElementById("cf-explorer-block");
  var controls = doc.getElementById("cf-controls");
  var tbody = doc.getElementById("cf-tbody");
  if (!node || !block || !controls || !tbody) return;
  var data;
  try { data = JSON.parse(node.textContent); } catch (e) { return; }
  var selCycle = doc.getElementById("cf-cycle");
  var selGroup = doc.getElementById("cf-group");
  var selComm = doc.getElementById("cf-committee");
  var selSort = doc.getElementById("cf-sort");
  var count = doc.getElementById("cf-count");
  var totalsBox = doc.getElementById("cf-totals");
  var site = doc.getElementById("site");
  var root = (site && site.getAttribute("data-root")) || "";
  if (!selCycle || !selGroup || !selComm || !selSort) return;

  // row fields (see _explorer_block in pages/campaigns.py)
  var CI = 0, OI = 1, GI = 2, CY = 3, CM = 4, CA = 5, PA = 6, RT = 7, AM = 8, PE = 9, PT = 10,
      REC = 11, EXP = 12, CASH = 13, ST = 14, DOC = 15, URL = 16, NOTE = 17;
  var rows = data.rows.map(function (r, i) { r.push(i); return r; });
  var IDX = 18;

  controls.hidden = false;
  block.hidden = false;

  function money(v) {
    if (v === null || v === undefined) return "blank on form";
    var parts = Math.abs(v).toFixed(2).split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return (v < 0 ? "-" : "") + "$" + parts[0] + "." + parts[1];
  }
  function el(tag, cls, text) {
    var e = doc.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = text;
    return e;
  }
  function clear(e) { while (e.firstChild) e.removeChild(e.firstChild); }
  function cfBadge(status) {
    var def = data.status[status] || [String(status).toUpperCase(), "Transcription status not recorded."];
    var a = el("a", "badge-link");
    a.href = "#method";
    a.setAttribute("aria-label", def[0] + ": " + def[1]);
    var s = el("span", "badge badge-cf badge-cf-" + (status || "none"), def[0]);
    s.title = def[1];
    a.appendChild(s);
    return a;
  }
  function computedBadge() {
    var a = el("a", "badge-link");
    a.href = root + "about/index.html#badges";
    a.setAttribute("aria-label", "COMPUTED: The guide's own arithmetic from other sourced figures.");
    var s = el("span", "badge badge-computed", "COMPUTED");
    s.title = "The guide's own arithmetic: the reports' this-period figures added up.";
    a.appendChild(s);
    return a;
  }

  function matches(r, useComm) {
    if (selCycle.value !== "" && String(r[CY]) !== selCycle.value) return false;
    if (selGroup.value !== "" && String(r[GI]) !== selGroup.value) return false;
    if (useComm && selComm.value !== "" && String(r[CI]) !== selComm.value) return false;
    return true;
  }

  function fillCommittees() {
    var keep = selComm.value;
    var seen = {};
    var list = [];
    rows.forEach(function (r) {
      if (!matches(r, false) || seen[r[CI]]) return;
      seen[r[CI]] = 1;
      list.push(r[CI]);
    });
    list.sort(function (a, b) {
      var x = data.committees[a].n.toLowerCase(), y = data.committees[b].n.toLowerCase();
      return x < y ? -1 : x > y ? 1 : a - b;
    });
    while (selComm.options.length > 1) selComm.remove(1);
    list.forEach(function (ci) {
      var c = data.committees[ci];
      var o = doc.createElement("option");
      o.value = String(ci);
      o.textContent = c.n + (c.c ? " (" + c.c + " (" + (c.p || "no party on the form") + "))" : "");
      selComm.appendChild(o);
    });
    selComm.value = seen[keep] ? keep : "";
  }

  function cmpNum(field, dir) {
    return function (a, b) {
      var x = a[field], y = b[field];
      var xn = x === null || x === undefined, yn = y === null || y === undefined;
      if (xn && yn) return a[IDX] - b[IDX];
      if (xn) return 1;      // blanks always last
      if (yn) return -1;
      if (x !== y) return dir * (x - y);
      return a[IDX] - b[IDX];
    };
  }
  function sortRows(list) {
    var s = selSort.value;
    if (s === "committee") {
      return list.sort(function (a, b) {
        var x = a[CM].toLowerCase(), y = b[CM].toLowerCase();
        return x < y ? -1 : x > y ? 1 : a[IDX] - b[IDX];
      });
    }
    if (s === "date") {
      return list.sort(function (a, b) {
        if (a[PT] === b[PT]) return a[IDX] - b[IDX];
        if (!a[PT]) return 1;
        if (!b[PT]) return -1;
        return a[PT] < b[PT] ? -1 : 1;
      });
    }
    var m = /^(receipts|spent|cash)-(asc|desc)$/.exec(s);
    if (m) {
      var field = { receipts: REC, spent: EXP, cash: CASH }[m[1]];
      return list.sort(cmpNum(field, m[2] === "asc" ? 1 : -1));
    }
    return list.sort(function (a, b) { return a[IDX] - b[IDX]; });
  }

  function headerRow(cls, text) {
    var tr = el("tr", cls);
    var th = el("th", null, text);
    th.setAttribute("scope", "colgroup");
    th.setAttribute("colspan", "8");
    tr.appendChild(th);
    return tr;
  }

  function rowEl(r, showOffice) {
    var tr = doc.createElement("tr");
    var th = el("th");
    th.setAttribute("scope", "row");
    th.appendChild(el("span", "cf-committee", r[CM] || "Committee name not written"));
    var who = [];
    if (r[CA]) who.push(r[CA]);
    who.push(data.parties[r[PA]]);
    th.appendChild(el("span", "cf-sub", who.join(" · ")));
    if (showOffice) th.appendChild(el("span", "cf-sub", data.offices[r[OI]]));
    tr.appendChild(th);
    tr.appendChild(el("td", null, data.types[r[RT]] + (r[AM] ? " (amended)" : "")));
    tr.appendChild(el("td", null, r[PE]));
    var unread = r[ST] === "unreadable";
    [REC, EXP, CASH].forEach(function (f) {
      tr.appendChild(el("td", "num", unread ? "not readable" : money(r[f])));
    });
    var st = el("td", "cf-status");
    st.appendChild(cfBadge(r[ST]));
    if (r[NOTE]) {
      var d = el("details", "cf-note-details");
      d.appendChild(el("summary", null, "Note"));
      d.appendChild(el("p", "cf-note", r[NOTE]));
      st.appendChild(d);
    }
    tr.appendChild(st);
    var form = el("td");
    if (r[URL]) {
      var a = el("a", null, "doc " + r[DOC]);
      a.href = /^https?:/.test(r[URL]) ? r[URL] : data.url + r[URL];
      a.target = "_blank";
      a.rel = "noopener";
      form.appendChild(a);
    } else {
      form.textContent = "doc " + r[DOC];
    }
    tr.appendChild(form);
    return tr;
  }

  function renderTotals() {
    clear(totalsBox);
    var ci = selComm.value;
    var t = ci !== "" ? data.totals[ci] : null;
    if (!t) { totalsBox.hidden = true; return; }
    var c = data.committees[+ci];
    totalsBox.appendChild(el("p", "cf-totals-h", "Reports added up, by cycle: " + c.n));
    var ul = el("ul", "cf-totals-list");
    Object.keys(t).sort().forEach(function (cy) {
      if (selCycle.value !== "" && selCycle.value !== cy) return;
      var x = t[cy];
      var li = el("li");
      li.appendChild(el("strong", null, data.cycles[+cy] + ": "));
      if (x.why !== undefined) {
        li.appendChild(doc.createTextNode(x.n + " report" + (x.n === 1 ? "" : "s") + ". Not added up. " + data.whys[x.why]));
      } else {
        li.appendChild(doc.createTextNode(
          x.n + " report" + (x.n === 1 ? "" : "s") + " covering " + x.p + ". Receipts " + money(x.r) +
          ", expenditures " + money(x.e) + ", cash on hand at the close of the last report " + money(x.cash) + ". "));
        li.appendChild(computedBadge());
      }
      ul.appendChild(li);
    });
    totalsBox.appendChild(ul);
    totalsBox.appendChild(el("p", "cf-sub", "Added up only when the reports' periods run back to back and every report's " +
      "own arithmetic checks. Fundraising doesn't measure support or predict results."));
    totalsBox.hidden = false;
  }

  function render() {
    var list = sortRows(rows.filter(function (r) { return matches(r, true); }));
    var grouped = selSort.value === "office";
    var frag = doc.createDocumentFragment();
    var lastG = null, lastO = null;
    var comms = {};
    list.forEach(function (r) {
      comms[r[CI]] = 1;
      if (grouped && r[GI] !== lastG) {
        lastG = r[GI];
        lastO = null;
        frag.appendChild(headerRow("cf-group-row", data.groups[r[GI]]));
      }
      if (grouped && r[OI] !== lastO) {
        lastO = r[OI];
        frag.appendChild(headerRow("cf-office-row", data.offices[r[OI]]));
      }
      frag.appendChild(rowEl(r, !grouped));
    });
    clear(tbody);
    if (!list.length) {
      var tr = el("tr");
      var td = el("td", null, "No filings match these choices.");
      td.setAttribute("colspan", "8");
      tr.appendChild(td);
      frag.appendChild(tr);
    }
    tbody.appendChild(frag);
    var nc = Object.keys(comms).length;
    if (count) {
      count.textContent = "Showing " + list.length + " report" + (list.length === 1 ? "" : "s") + " from " + nc +
        " committee" + (nc === 1 ? "" : "s") + (grouped ? ", by office." : ", in the order you chose.");
    }
    renderTotals();
  }

  selCycle.addEventListener("change", function () { fillCommittees(); render(); });
  selGroup.addEventListener("change", function () { fillCommittees(); render(); });
  selComm.addEventListener("change", render);
  selSort.addEventListener("change", render);
  fillCommittees();
  render();
})();
