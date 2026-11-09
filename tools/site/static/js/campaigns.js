/* campaigns.js: filing explorer on money/campaigns/all-filings/. Every filing is a table row rendered in the HTML
   (pages/campaigns.py, #cf-table); with JavaScript off the whole table is there. This script only filters and sorts
   those rows (non-matching rows are taken out of the tbody, never deleted) and derives the one-row-per-committee
   list from clones of them. #cf-data holds only committee names, cycle totals and badge text. Default order is
   office, district, committee (the order the rows arrive in); amount sorts only on request. ASCII only. */
(function () {
  "use strict";
  var doc = document;
  var node = doc.getElementById("cf-data");
  var block = doc.getElementById("cf-explorer-block");
  var controls = doc.getElementById("cf-controls");
  var tbody = doc.getElementById("cf-tbody");
  var table = doc.getElementById("cf-table");
  if (!node || !block || !controls || !tbody || !table) return;
  var data;
  try { data = JSON.parse(node.textContent); } catch (e) { return; }
  var selCycle = doc.getElementById("cf-cycle");
  var selGroup = doc.getElementById("cf-group");
  var selComm = doc.getElementById("cf-committee");
  var selSort = doc.getElementById("cf-sort");
  var count = doc.getElementById("cf-count");
  var totalsBox = doc.getElementById("cf-totals");
  var listBox = doc.getElementById("cf-list");
  var foldLabel = doc.querySelector("#cf-all-fold .see-all-label");
  var site = doc.getElementById("site");
  var root = (site && site.getAttribute("data-root")) || "";
  if (!selCycle || !selGroup || !selComm || !selSort) return;

  // Each filing row carries data-ci (committee), data-oi (office), data-gi (office group), data-cy (cycle),
  // data-pt (period end), data-rec / data-exp / data-cash (numbers, absent when blank), data-st (the committee name is the .cf-committee text).
  function num(tr, k) { var v = tr.getAttribute("data-" + k); return v === null ? null : parseFloat(v); }
  var hdrs = {};
  var rows = [];
  Array.prototype.forEach.call(tbody.children, function (tr) {
    var hk = tr.getAttribute("data-hk");
    if (hk) { hdrs[hk] = tr; return; }
    rows.push({
      tr: tr, idx: rows.length,
      ci: +tr.getAttribute("data-ci"), oi: tr.getAttribute("data-oi"), gi: tr.getAttribute("data-gi"),
      cy: tr.getAttribute("data-cy"), cm: (tr.querySelector(".cf-committee") || {}).textContent || "", pt: tr.getAttribute("data-pt") || "",
      rec: num(tr, "rec"), exp: num(tr, "exp"), cash: num(tr, "cash"), st: tr.getAttribute("data-st")
    });
  });
  if (!rows.length) return;

  controls.hidden = false;
  var lb = doc.getElementById("cf-list-block");
  if (lb) lb.hidden = false;

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
    if (selCycle.value !== "" && r.cy !== selCycle.value) return false;
    if (selGroup.value !== "" && r.gi !== selGroup.value) return false;
    if (useComm && selComm.value !== "" && String(r.ci) !== selComm.value) return false;
    return true;
  }

  function fillCommittees() {
    var keep = selComm.value;
    var seen = {};
    var list = [];
    rows.forEach(function (r) {
      if (!matches(r, false) || seen[r.ci]) return;
      seen[r.ci] = 1;
      list.push(r.ci);
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
      if (x === null && y === null) return a.idx - b.idx;
      if (x === null) return 1;      // blanks always last
      if (y === null) return -1;
      if (x !== y) return dir * (x - y);
      return a.idx - b.idx;
    };
  }
  function sortRows(list) {
    var s = selSort.value;
    if (s === "committee") {
      return list.sort(function (a, b) {
        var x = a.cm.toLowerCase(), y = b.cm.toLowerCase();
        return x < y ? -1 : x > y ? 1 : a.idx - b.idx;
      });
    }
    if (s === "date") {
      return list.sort(function (a, b) {
        if (a.pt === b.pt) return a.idx - b.idx;
        if (!a.pt) return 1;
        if (!b.pt) return -1;
        return a.pt < b.pt ? -1 : 1;
      });
    }
    var m = /^(receipts|spent|cash)-(asc|desc)$/.exec(s);
    if (m) {
      var field = { receipts: "rec", spent: "exp", cash: "cash" }[m[1]];
      return list.sort(cmpNum(field, m[2] === "asc" ? 1 : -1));
    }
    return list.sort(function (a, b) { return a.idx - b.idx; });
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

  /* One row per committee: a <details> with the committee, who it backs, how many reports are on file, the cash
     figure on its latest report and the transcription-status mix; it opens to that committee's reports, which are
     clones of the table rows (the filings themselves exist once, in the table). */
  function statusMix(rs) {
    var n = {}, order = [];
    rs.forEach(function (r) { if (!n[r.st]) { n[r.st] = 0; order.push(r.st); } n[r.st] += 1; });
    return order.map(function (k) { return n[k] + " " + ((data.status[k] || [String(k).toUpperCase()])[0]); }).join(", ");
  }
  function reportsTable(rs) {
    var wrap = el("div", "table-wrap");
    wrap.setAttribute("role", "region");
    wrap.setAttribute("tabindex", "0");
    wrap.setAttribute("aria-label", "Reports of " + (rs[0].cm || "this committee"));
    var t = el("table", "data cf-table cf-comm-table");
    t.style.minWidth = "60rem";
    var cap = el("caption", null, "Reports on file: " + (rs[0].cm || "committee name not written"));
    cap.className = "visually-hidden";
    t.appendChild(cap);
    var thr = el("tr");
    ["Report", "Period", "Receipts this period", "Expenditures this period", "Cash on hand at close", "Status", "Form"]
      .forEach(function (x, i) {
        var th = el("th", i >= 2 && i <= 4 ? "num" : null, x);
        th.setAttribute("scope", "col");
        thr.appendChild(th);
      });
    var thead = el("thead");
    thead.appendChild(thr);
    t.appendChild(thead);
    var tb = el("tbody");
    rs.forEach(function (r) {
      var tr = r.tr.cloneNode(true);
      tr.removeChild(tr.firstElementChild);   /* the committee is the row's heading above the table */
      var typeCell = tr.firstElementChild;    /* the report-type cell becomes the row heading */
      var th = el("th");
      th.setAttribute("scope", "row");
      while (typeCell.firstChild) th.appendChild(typeCell.firstChild);
      tr.replaceChild(th, typeCell);
      tb.appendChild(tr);
    });
    t.appendChild(tb);
    wrap.appendChild(t);
    return wrap;
  }
  function renderList(list, grouped) {
    if (!listBox) return;
    clear(listBox);
    var order = [], by = {};
    list.forEach(function (r) {
      if (!by[r.ci]) { by[r.ci] = []; order.push(r.ci); }
      by[r.ci].push(r);
    });
    var ul = el("ul", "one-list ent-list cf-comm-list");
    var lastG = null, lastO = null;
    order.forEach(function (ci) {
      var rs = by[ci], c = data.committees[ci];
      if (grouped && rs[0].gi !== lastG) {
        lastG = rs[0].gi; lastO = null;
        ul.appendChild(el("li", "cf-list-group", data.groups[+rs[0].gi]));
      }
      if (grouped && rs[0].oi !== lastO) {
        lastO = rs[0].oi;
        ul.appendChild(el("li", "cf-list-office", data.offices[+rs[0].oi]));
      }
      var latest = rs.slice().sort(function (a, b) {
        return a.pt < b.pt ? -1 : a.pt > b.pt ? 1 : a.idx - b.idx;
      }).pop();
      var li = el("li", "ent-row");
      var d = el("details", "fold-details one-fold ent-item cf-comm");
      d.id = "cf-comm-" + ci;
      var sm = el("summary", "fold-summary one-summary");
      sm.appendChild(el("h3", "one-h ent-name", c.n || "Committee name not written"));
      var facts = [];
      if (c.c) facts.push(c.c + " (" + (c.p || "no party on the form") + ")");
      facts.push(rs.length + " report" + (rs.length === 1 ? "" : "s") + " on file");
      facts.push(latest.st === "unreadable" ? "latest report not readable" :
        "latest cash on hand: " + money(latest.cash) + (latest.pt ? " (" + latest.pt + ")" : ""));
      sm.appendChild(el("span", "one-digest ent-facts", facts.join(" \u00b7 ")));
      sm.appendChild(el("span", "ent-status cf-mix", statusMix(rs)));
      sm.appendChild(el("span", "fold-toggle")).setAttribute("aria-hidden", "true");
      d.appendChild(sm);
      var body = el("div", "fold-body one-body");
      body.appendChild(reportsTable(rs));
      d.appendChild(body);
      li.appendChild(d);
      ul.appendChild(li);
    });
    if (!order.length) ul.appendChild(el("li", "cf-list-empty", "No filings match these choices."));
    listBox.appendChild(ul);
    /* built here, so it starts closed except when it is small */
    if (order.length > 3) {
      Array.prototype.forEach.call(ul.querySelectorAll("details"), function (x) { x.open = false; });
    }
  }

  function render() {
    var list = sortRows(rows.filter(function (r) { return matches(r, true); }));
    var grouped = selSort.value === "office";
    table.classList.toggle("cf-grouped", grouped);
    var frag = doc.createDocumentFragment();
    var lastG = null, lastO = null;
    var comms = {};
    list.forEach(function (r) {
      comms[r.ci] = 1;
      if (grouped && r.gi !== lastG) {
        lastG = r.gi;
        lastO = null;
        if (hdrs["g" + r.gi]) frag.appendChild(hdrs["g" + r.gi]);
      }
      if (grouped && r.oi !== lastO) {
        lastO = r.oi;
        if (hdrs["o" + r.gi + "-" + r.oi]) frag.appendChild(hdrs["o" + r.gi + "-" + r.oi]);
      }
      frag.appendChild(r.tr);
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
    renderList(list, grouped);
    if (foldLabel) foldLabel.textContent = "See all " + list.length + " filing" + (list.length === 1 ? "" : "s") + " as one table";
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
