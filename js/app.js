/* app.js — builds the black/red brick cards and the clip cards from window.DATA_* */
(function () {
  "use strict";
  var faces = window.DATA_faces.faces;
  var summary = window.DATA_summary;
  var byId = {};
  faces.forEach(function (f) { byId[f.id] = f; });

  var BLACK_ORDER = ["black_gable_front", "black_slope_L", "black_slope_R",
    "black_side_outer_L", "black_side_outer_R", "black_side_inner_L", "black_side_inner_R"];
  var RED_ORDER = ["A_NE", "B_SW", "C_NW", "D_SE"];
  var CLIP_ORDER = RED_ORDER.concat(BLACK_ORDER);

  /* clip type meta (length / holes) from summary */
  var clipMeta = {};
  summary.clips.per_type.forEach(function (t) { clipMeta[t.type] = t; });

  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    return e;
  }
  function fmt(n) { return n.toLocaleString("en-GB"); }

  /* ---------- lightbox ---------- */
  var lb = document.getElementById("lightbox");
  var lbImg = document.getElementById("lightbox-img");
  var lbTitle = document.getElementById("lightbox-title");
  function openLightbox(src, title) {
    lbImg.src = src;
    lbTitle.textContent = title;
    lb.classList.add("open");
    lb.setAttribute("aria-hidden", "false");
  }
  function closeLightbox() {
    lb.classList.remove("open");
    lb.setAttribute("aria-hidden", "true");
    lbImg.src = "";
  }
  lb.addEventListener("click", function (e) { if (e.target === lb) closeLightbox(); });
  document.getElementById("lightbox-close").addEventListener("click", closeLightbox);
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeLightbox(); });

  function svgHolder(src, title) {
    var holder = el("div", "svg-holder");
    var img = el("img");
    img.src = src;
    img.alt = title;
    img.loading = "lazy";
    holder.appendChild(img);
    holder.title = "点击放大 Click to enlarge";
    holder.addEventListener("click", function () { openLightbox(src, title); });
    return holder;
  }

  /* ---------- brick cards (sections 2 & 3) ---------- */
  function brickCard(face) {
    var card = el("article", "face-card");
    card.appendChild(el("h3", null,
      '<span class="face-id">' + face.id + "</span>" + face.name_zh +
      '<span class="en">' + face.name_en + "</span>"));
    card.appendChild(svgHolder("svg/brick_" + face.id + ".svg",
      face.name_zh + " · " + face.name_en + " — 砖排布 Brick layout"));

    var wrap = el("div", "tbl-wrap");
    var t = el("table");
    t.innerHTML = "<thead><tr><th>砖型 Type ID</th><th>尺寸 Size (w×h mm)</th>" +
      '<th class="num">数量 Qty</th></tr></thead>';
    var tb = el("tbody");
    var qsum = 0;
    face.bricks.forEach(function (b) {
      qsum += b.qty;
      var tr = el("tr");
      tr.innerHTML = '<td><span class="type-chip">' + b.type_id + "</span></td>" +
        "<td>" + b.w + " × " + b.h + '</td><td class="num">' + fmt(b.qty) + "</td>";
      tb.appendChild(tr);
    });
    var tot = el("tr", "total-row");
    tot.innerHTML = "<td>合计 Face total</td><td>" +
      face.totals.area_m2.toFixed(2) + " m²</td><td class=\"num\">" + fmt(qsum) + "</td>";
    tb.appendChild(tot);
    t.appendChild(tb);
    wrap.appendChild(t);
    card.appendChild(wrap);

    if (face.totals.corner_pieces) {
      card.appendChild(el("p", "corner-note",
        "含转角平贴片 incl. flat-pair corner pieces: <b>" + face.totals.corner_pieces + "</b>"));
    }
    return card;
  }

  var blackWrap = document.getElementById("black-cards");
  BLACK_ORDER.forEach(function (id) { blackWrap.appendChild(brickCard(byId[id])); });
  var redWrap = document.getElementById("red-cards");
  RED_ORDER.forEach(function (id) { redWrap.appendChild(brickCard(byId[id])); });

  /* ---------- clip cards (section 4) ---------- */
  function clipCard(face) {
    var card = el("article", "face-card");
    card.appendChild(el("h3", null,
      '<span class="face-id ' + face.colour + '">' + face.id + "</span>" + face.name_zh +
      '<span class="en">' + face.name_en + "</span>"));
    card.appendChild(svgHolder("svg/clip_" + face.id + ".svg",
      face.name_zh + " · " + face.name_en + " — 卡扣排布 Clip layout"));

    var wrap = el("div", "tbl-wrap");
    var t = el("table");
    t.innerHTML = "<thead><tr><th>卡扣 Clip type</th><th>长度 Length (mm)</th>" +
      '<th class="num">数量 Qty</th><th class="num">孔/扣 Holes</th>' +
      '<th class="num">螺丝 Screws</th></tr></thead>';
    var tb = el("tbody");
    var qsum = 0, ssum = 0;
    face.clips.forEach(function (c) {
      var m = clipMeta[c.type] || {};
      qsum += c.qty; ssum += c.screws;
      var len = m.length_mm !== undefined ? m.length_mm : "—";
      if (m.shape === "right-trapezoid") len = m.length_mm + " (梯形 trapezoid, 40°)";
      var tr = el("tr");
      tr.innerHTML = "<td><span class=\"type-chip\">" + c.type + "</span></td>" +
        "<td>" + len + '</td><td class="num">' + fmt(c.qty) +
        '</td><td class="num">' + (m.holes_per_clip !== undefined ? m.holes_per_clip : "—") +
        '</td><td class="num">' + fmt(c.screws) + "</td>";
      tb.appendChild(tr);
    });
    var tot = el("tr", "total-row");
    tot.innerHTML = "<td colspan=\"2\">小计 Face subtotal（一孔一螺丝 1 hole = 1 screw）</td>" +
      '<td class="num">' + fmt(qsum) + '</td><td class="num">—</td><td class="num">' + fmt(ssum) + "</td>";
    tb.appendChild(tot);
    t.appendChild(tb);
    wrap.appendChild(t);
    card.appendChild(wrap);
    return card;
  }

  var clipWrap = document.getElementById("clip-cards");
  CLIP_ORDER.forEach(function (id) { clipWrap.appendChild(clipCard(byId[id])); });
})();
