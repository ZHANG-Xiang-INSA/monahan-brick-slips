/* Site controller — face metadata, elevation workbench (search/filter/pan-zoom),
   data rail, tables, hash routing, cutting section, drawing-viewer catalogue,
   3D wiring (segmented layer presets), nav scrollspy + mobile menu, reveals. */
(function () {
  "use strict";

  var T = function (k) { return window.T(k); };

  // ---------- face metadata (visible naming; internal ids stay in data) ----------
  var FACES = [
    { code: "RED-01",   id: "A_NE",               model: "A_NE_side",             colour: "red",
      zh: "A墙 — 东北侧立面（楼梯侧）",  en: "Wall A — NE Side Elevation (Stair Side)",
      zhS: "A墙 · 东北侧",     enS: "Wall A · NE side" },
    { code: "RED-02",   id: "B_SW",               model: "B_SW_side",             colour: "red",
      zh: "B墙 — 西南侧立面",            en: "Wall B — SW Side Elevation",
      zhS: "B墙 · 西南侧",     enS: "Wall B · SW side" },
    { code: "RED-03",   id: "C_NW",               model: "C_NW_front",            colour: "red",
      zh: "C墙 — 西北正立面（入口）",    en: "Wall C — NW Front Elevation (Entrance)",
      zhS: "C墙 · 西北正面",   enS: "Wall C · NW front" },
    { code: "RED-04",   id: "D_SE",               model: "D_SE_garden",           colour: "red",
      zh: "D墙 — 东南花园立面",          en: "Wall D — SE Garden Elevation",
      zhS: "D墙 · 东南花园",   enS: "Wall D · SE garden" },
    { code: "BLACK-01", id: "black_gable_front",  model: "black_frontframe_+360", colour: "black",
      zh: "雨棚山墙正面",                en: "Canopy Gable Front",
      zhS: "雨棚山墙正面",     enS: "Canopy gable" },
    { code: "BLACK-02", id: "black_slope_L",      model: "black_slopeL_-4620",    colour: "black",
      zh: "雨棚左坡面",                  en: "Canopy Slope — Left",
      zhS: "雨棚左坡面",       enS: "Canopy slope L" },
    { code: "BLACK-03", id: "black_slope_R",      model: "black_slopeR_-4620",    colour: "black",
      zh: "雨棚右坡面",                  en: "Canopy Slope — Right",
      zhS: "雨棚右坡面",       enS: "Canopy slope R" },
    { code: "BLACK-04", id: "black_side_outer_L", model: "black_wallXn_+1720",    colour: "black",
      zh: "雨棚外侧壁 — 左",             en: "Canopy Outer Wall — Left",
      zhS: "雨棚外侧壁 · 左",  enS: "Outer wall L" },
    { code: "BLACK-05", id: "black_side_outer_R", model: "black_wallXp_+1720",    colour: "black",
      zh: "雨棚外侧壁 — 右",             en: "Canopy Outer Wall — Right",
      zhS: "雨棚外侧壁 · 右",  enS: "Outer wall R" },
    { code: "BLACK-06", id: "black_side_inner_L", model: "black_wallXp_-1400",    colour: "black",
      zh: "雨棚内侧壁 — 左",             en: "Canopy Inner Wall — Left",
      zhS: "雨棚内侧壁 · 左",  enS: "Inner wall L" },
    { code: "BLACK-07", id: "black_side_inner_R", model: "black_wallXn_-1400",    colour: "black",
      zh: "雨棚内侧壁 — 右",             en: "Canopy Inner Wall — Right",
      zhS: "雨棚内侧壁 · 右",  enS: "Inner wall R" }
  ];
  // drawing sheet sizes (viewBox px) — the elevation SVGs carry no width/height
  var SVG_SIZE = {
    A_NE: [1784, 423], B_SW: [1784, 485], C_NW: [1784, 473], D_SE: [1784, 810],
    black_gable_front: [919, 998], black_slope_L: [810, 998], black_slope_R: [810, 998],
    black_side_outer_L: [600, 998], black_side_outer_R: [600, 998],
    black_side_inner_L: [610, 998], black_side_inner_R: [610, 998]
  };
  FACES.forEach(function (f) {
    f.brickSvg = "svg/brick_" + f.id + ".svg";
    f.clipSvg = "svg/clip_" + f.id + ".svg";
    f.size = SVG_SIZE[f.id];
  });
  function faceByCode(code) {
    for (var i = 0; i < FACES.length; i++) if (FACES[i].code === code) return FACES[i];
    return null;
  }
  function faceCodeOfModelKey(key) {
    for (var i = 0; i < FACES.length; i++) if (FACES[i].model === key) return FACES[i].code;
    return null;
  }

  var faceData = {};
  (window.DATA_faces && window.DATA_faces.faces || []).forEach(function (f) { faceData[f.id] = f; });
  var clipTypeInfo = {};
  (window.DATA_summary && window.DATA_summary.clips && window.DATA_summary.clips.per_type || [])
    .forEach(function (c) { clipTypeInfo[c.type] = c; });

  var fmt = function (n) { return Number(n).toLocaleString("en-US"); };

  // ---------- state ----------
  var cur = FACES[0];          // current face (RED-01 default)
  var curLayer = "bricks";     // 'bricks' | 'clips'
  var faceFilter = "all";      // 'all' | 'red' | 'black'
  var faceQuery = "";
  var sort = { bricks: { col: 0, dir: 1 }, clips: { col: 0, dir: 1 } };
  var dviewer = null;
  var stagePZ = null;
  var reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---------- drawing-viewer catalogue ----------
  function dvEntries() {
    var out = [];
    FACES.forEach(function (f) {
      out.push({ code: f.code, name: f.zh + " · " + f.en, sub: T("kind_brick"), src: f.brickSvg, key: f.code + "|bricks", w: f.size[0], h: f.size[1] });
      out.push({ code: f.code, name: f.zh + " · " + f.en, sub: T("kind_clip"), src: f.clipSvg, key: f.code + "|clips", w: f.size[0], h: f.size[1] });
    });
    out.push({ code: "CUT-01", name: T("cut_bricks"), sub: T("cut_bricks_sub"), src: "svg/cut_brick_types.svg", key: "cut1", w: 2134, h: 1736 });
    out.push({ code: "CUT-02", name: T("cut_clips"), sub: T("cut_clips_sub"), src: "svg/cut_clip_types.svg", key: "cut2", w: 1180, h: 942 });
    return out;
  }
  function openViewerAt(key) {
    var list = dvEntries();
    for (var i = 0; i < list.length; i++) if (list[i].key === key) { dviewer.open(list, i); return; }
    dviewer.open(list, 0);
  }

  // ---------- centre drawing stage: pan / zoom / pinch ----------
  // (shared robust engine — window.PanZoom in drawing.js: pointer capture,
  //  window-bound move/up, zoom-independent screen-px pan, clamped, wheel-to-cursor)
  function StagePZ(stage, plane, img, onReady) {
    var pz = window.PanZoom(stage, plane, { pad: 30, img: img });
    var token = 0, lastSrc = "";
    return {
      load: function (src, w, h, alt) {
        token++;
        var my = token;
        stage.classList.add("loading");
        var done = function () {
          if (my !== token) return;
          var W = w || img.naturalWidth || 1000;
          var H = h || img.naturalHeight || 700;
          pz.setSize(W, H); // PanZoom owns the img layout size (crisp zoom)
          stage.classList.remove("loading");
          if (onReady) onReady();
        };
        img.alt = alt || "";
        if (lastSrc === src) { done(); return; } // same sheet — load may not re-fire
        lastSrc = src;
        img.onload = done;
        img.src = src;
        if (img.complete) done();
      },
      fit: pz.fit,
      zoom: pz.zoom
    };
  }

  // ---------- face navigator (search + filter + list) ----------
  function faceMatches(f) {
    if (faceFilter !== "all" && f.colour !== faceFilter) return false;
    if (!faceQuery) return true;
    var q = faceQuery.toLowerCase();
    return (f.code + " " + f.zh + " " + f.en + " " + f.zhS + " " + f.enS).toLowerCase().indexOf(q) >= 0;
  }
  function buildFaceList() {
    var host = document.getElementById("face-list-items");
    var zh = window.LANG() === "zh";
    host.innerHTML = "";
    var shown = 0;
    FACES.forEach(function (f) {
      if (!faceMatches(f)) return;
      shown++;
      var d = faceData[f.id] || { totals: {} };
      var b = document.createElement("button");
      b.type = "button";
      b.className = "face-item" + (f.colour === "black" ? " black" : "") + (f === cur ? " active" : "");
      b.setAttribute("data-code", f.code);
      b.innerHTML =
        '<span class="fi-bar"></span>' +
        '<span class="fi-body">' +
          '<span class="fi-code">' + f.code + "</span>" +
          '<span class="fi-name">' + (zh ? f.zhS : f.enS) + "</span>" +
          '<span class="fi-count">' + fmt(d.totals.bricks || 0) + " " + T("u_pcs") + "</span>" +
        "</span>" +
        '<span class="fi-thumb"><img loading="lazy" src="' + f.brickSvg + '" alt="' + f.code + '"></span>';
      b.addEventListener("click", function () { selectFace(f.code, true); });
      host.appendChild(b);
    });
    if (!shown) {
      var p = document.createElement("p");
      p.className = "fl-empty";
      p.textContent = T("fl_empty");
      host.appendChild(p);
    }
  }

  // ---------- data rail ----------
  function renderStats() {
    var d = faceData[cur.id] || { totals: {}, bricks: [], clips: [] };
    var t = d.totals || {};
    var typesCount = (d.bricks || []).length;
    var host = document.getElementById("fm-stats");
    var rows = [
      ["st_area", fmt(t.area_m2 || 0), "m²"],
      ["st_bricks", fmt(t.bricks || 0), T("u_pcs")],
      ["st_corner", fmt(t.corner_pieces || 0), T("u_pcs")],
      ["st_clips", fmt(t.clips || 0), T("u_ea")],
      ["st_screws", fmt(t.screws || 0), T("u_ea")],
      ["st_types", fmt(typesCount), ""]
    ];
    host.innerHTML = rows.map(function (r) {
      return '<div class="rs-row"><span class="rs-l">' + T(r[0]) + '</span>' +
        '<span class="rs-v">' + r[1] + (r[2] ? "<i>" + r[2] + "</i>" : "") + "</span></div>";
    }).join("");
  }

  // ---------- schedule tables ----------
  function sortRows(rows, s, numCols) {
    var r = rows.slice();
    r.sort(function (a, b) {
      var va = a[s.col], vb = b[s.col];
      if (numCols.indexOf(s.col) >= 0) { va = Number(va); vb = Number(vb); }
      if (va < vb) return -s.dir;
      if (va > vb) return s.dir;
      return 0;
    });
    return r;
  }

  function tableHTML(kind) {
    var d = faceData[cur.id] || { bricks: [], clips: [] };
    var s = sort[kind], html, rows, total;
    function th(labels, numFrom) {
      return "<tr>" + labels.map(function (l, i) {
        var cls = (i >= numFrom ? "num" : "") + (s.col === i ? " sorted" : "");
        var arr = s.col === i ? (s.dir > 0 ? "↑" : "↓") : "↕";
        return '<th class="' + cls + '" data-kind="' + kind + '" data-col="' + i + '">' + T(l) +
          '<span class="s-arr">' + arr + "</span></th>";
      }).join("") + "</tr>";
    }
    if (kind === "bricks") {
      rows = (d.bricks || []).map(function (r) { return [r.type_id, r.w + " × " + r.h, r.qty, r.w * r.h]; });
      rows = sortRows(rows, s, [2, 3]);
      total = (d.bricks || []).reduce(function (a, r) { return a + r.qty; }, 0);
      html = '<table class="spec"><caption>' + T("tbl_bricks") + "</caption><thead>" +
        th(["th_type", "th_size", "th_qty"], 2) + "</thead><tbody>";
      rows.forEach(function (r) {
        html += '<tr><td class="mono">' + r[0] + '</td><td class="mono">' + r[1] +
          '</td><td class="num">' + fmt(r[2]) + "</td></tr>";
      });
      html += '<tr class="total"><td>' + T("row_total") + '</td><td class="mono">—</td><td class="num">' +
        fmt(total) + "</td></tr></tbody></table>";
    } else {
      rows = (d.clips || []).map(function (r) {
        var info = clipTypeInfo[r.type] || {};
        return [r.type, info.length_mm || 0, r.qty, r.screws];
      });
      rows = sortRows(rows, s, [1, 2, 3]);
      var tq = 0, tscr = 0;
      (d.clips || []).forEach(function (r) { tq += r.qty; tscr += r.screws; });
      html = '<table class="spec"><caption>' + T("tbl_clips") + "</caption><thead>" +
        th(["th_type", "th_len", "th_qty", "th_screws"], 1) + "</thead><tbody>";
      rows.forEach(function (r) {
        html += '<tr><td class="mono">' + r[0] + '</td><td class="num">' + fmt(r[1]) +
          '</td><td class="num">' + fmt(r[2]) + '</td><td class="num">' + fmt(r[3]) + "</td></tr>";
      });
      html += '<tr class="total"><td>' + T("row_total") + '</td><td class="num">—</td><td class="num">' +
        fmt(tq) + '</td><td class="num">' + fmt(tscr) + "</td></tr></tbody></table>";
    }
    return html;
  }

  function renderTables() {
    document.getElementById("tbl-bricks-host").innerHTML = tableHTML("bricks");
    document.getElementById("tbl-clips-host").innerHTML = tableHTML("clips");
    var ths = document.querySelectorAll("#tbl-wrap th[data-kind]");
    for (var i = 0; i < ths.length; i++) {
      ths[i].addEventListener("click", function () {
        var k = this.getAttribute("data-kind"), c = Number(this.getAttribute("data-col"));
        if (sort[k].col === c) sort[k].dir = -sort[k].dir;
        else sort[k] = { col: c, dir: 1 };
        renderTables();
      });
    }
  }

  // ---------- face rendering ----------
  function renderDrawing(animate) {
    var stage = document.getElementById("fm-drawing");
    var src = curLayer === "clips" ? cur.clipSvg : cur.brickSvg;
    var alt = cur.code + " " + T(curLayer === "clips" ? "kind_clip" : "kind_brick");
    function go() { stagePZ.load(src, cur.size[0], cur.size[1], alt); }
    if (animate && !reducedMotion) {
      stage.classList.add("swap");
      setTimeout(go, 190);
    } else go();
  }

  function renderFace(animate) {
    var zh = window.LANG() === "zh";
    var title = document.getElementById("fm-title");
    title.className = "fm-title" + (cur.colour === "black" ? " black" : "");
    document.getElementById("fm-code").textContent = cur.code;
    document.getElementById("fm-zh").textContent = zh ? cur.zh : cur.en;
    document.getElementById("fm-en").textContent = zh ? cur.en : cur.zh;
    var items = document.querySelectorAll(".face-item");
    for (var i = 0; i < items.length; i++) {
      items[i].classList.toggle("active", items[i].getAttribute("data-code") === cur.code);
    }
    renderDrawing(animate);
    renderStats();
    renderTables();
  }

  function selectFace(code, updateHash, scroll) {
    var f = faceByCode(code);
    if (!f) return;
    var changed = f !== cur;
    cur = f;
    renderFace(changed);
    if (updateHash && history.replaceState) history.replaceState(null, "", "#face/" + code);
    if (scroll) document.getElementById("elevations").scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth" });
  }
  function stepFace(d) {
    var i = FACES.indexOf(cur);
    selectFace(FACES[(i + d + FACES.length) % FACES.length].code, true);
  }

  function handleHash() {
    var h = location.hash || "";
    var m = h.match(/^#face\/([A-Z]+-\d+)/);
    if (m && faceByCode(m[1])) selectFace(m[1], false, true);
  }

  // ---------- boot ----------
  document.addEventListener("DOMContentLoaded", function () {
    dviewer = window.DrawingViewer();

    var fmStage = document.getElementById("fm-drawing");
    stagePZ = StagePZ(fmStage, document.getElementById("fm-plane"),
      document.getElementById("fm-img"),
      function () { fmStage.classList.remove("swap"); });

    buildFaceList();
    renderFace(false);

    // search + colour filter
    var searchEl = document.getElementById("face-search");
    searchEl.addEventListener("input", function () {
      faceQuery = this.value.trim();
      buildFaceList();
    });
    var flt = document.querySelectorAll("#face-filter button");
    for (var ff = 0; ff < flt.length; ff++) {
      flt[ff].addEventListener("click", function () {
        faceFilter = this.getAttribute("data-f");
        for (var j = 0; j < flt.length; j++) flt[j].classList.toggle("active", flt[j] === this);
        buildFaceList();
      });
    }

    // segmented layer control (bricks / clips drawing)
    var segs = document.querySelectorAll("#fm-seg button");
    for (var i = 0; i < segs.length; i++) {
      segs[i].addEventListener("click", function () {
        curLayer = this.getAttribute("data-layer");
        for (var j = 0; j < segs.length; j++) segs[j].classList.toggle("active", segs[j] === this);
        renderDrawing(true);
      });
    }

    document.getElementById("fm-prev").addEventListener("click", function () { stepFace(-1); });
    document.getElementById("fm-next").addEventListener("click", function () { stepFace(1); });
    document.getElementById("fm-zin").addEventListener("click", function () { stagePZ.zoom(1.3); });
    document.getElementById("fm-zout").addEventListener("click", function () { stagePZ.zoom(1 / 1.3); });
    document.getElementById("fm-fit").addEventListener("click", function () { stagePZ.fit(); });
    document.getElementById("fm-open-dv").addEventListener("click", function () {
      openViewerAt(cur.code + "|" + curLayer);
    });

    // schedule disclosure (opened from the data rail)
    var tblWrap = document.getElementById("tbl-wrap");
    document.getElementById("rail-schedule").addEventListener("click", function () {
      tblWrap.classList.add("open");
      tblWrap.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "nearest" });
    });
    document.getElementById("tbl-close").addEventListener("click", function () {
      tblWrap.classList.remove("open");
    });

    // cutting cards
    document.getElementById("cut-open-1").addEventListener("click", function () { openViewerAt("cut1"); });
    document.getElementById("cut-open-2").addEventListener("click", function () { openViewerAt("cut2"); });
    document.getElementById("cut-fig-1").addEventListener("click", function () { openViewerAt("cut1"); });
    document.getElementById("cut-fig-2").addEventListener("click", function () { openViewerAt("cut2"); });

    window.addEventListener("hashchange", handleHash);

    // face deep-links should respond even when the hash is already set
    var faceLinks = document.querySelectorAll('a[href^="#face/"]');
    for (var fl = 0; fl < faceLinks.length; fl++) {
      faceLinks[fl].addEventListener("click", function (ev) {
        var m = this.getAttribute("href").match(/^#face\/([A-Z]+-\d+)/);
        if (!m) return;
        ev.preventDefault();
        if (history.replaceState) history.replaceState(null, "", "#face/" + m[1]);
        selectFace(m[1], false, true);
      });
    }

    // ---------- nav: mobile menu + scrollspy ----------
    var nav = document.getElementById("site-nav");
    var burger = document.getElementById("nav-burger");
    burger.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      burger.setAttribute("aria-expanded", open ? "true" : "false");
    });
    var navLinks = document.querySelectorAll("#nav-links a");
    for (var nl = 0; nl < navLinks.length; nl++) {
      navLinks[nl].addEventListener("click", function () {
        nav.classList.remove("open");
        burger.setAttribute("aria-expanded", "false");
      });
    }
    var spyIds = ["summary", "model", "elevations", "cutting"];
    var spyTick = false;
    function scrollSpy() {
      spyTick = false;
      var y = window.scrollY + 120;
      var act = "";
      for (var si = 0; si < spyIds.length; si++) {
        var el = document.getElementById(spyIds[si]);
        if (el && el.offsetTop <= y) act = spyIds[si];
      }
      if (window.innerHeight + window.scrollY >= document.body.scrollHeight - 4) act = spyIds[spyIds.length - 1];
      for (var sj = 0; sj < navLinks.length; sj++) {
        navLinks[sj].classList.toggle("active", navLinks[sj].getAttribute("href") === "#" + act);
      }
    }
    window.addEventListener("scroll", function () {
      if (!spyTick) { spyTick = true; requestAnimationFrame(scrollSpy); }
    }, { passive: true });
    scrollSpy();

    // ---------- section reveal (JS-applied so no-JS stays visible) ----------
    if ("IntersectionObserver" in window && !reducedMotion) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
        });
      }, { threshold: 0.08 });
      var secs = document.querySelectorAll(".sec");
      for (var sv = 0; sv < secs.length; sv++) {
        var r = secs[sv].getBoundingClientRect();
        if (r.top > window.innerHeight * 0.9) {
          secs[sv].classList.add("will-reveal");
          io.observe(secs[sv]);
        }
      }
    }

    // ---------- 3D ----------
    var shell = document.getElementById("viewer-shell");
    var container = document.getElementById("viewer3d");
    var overlay = document.getElementById("v-overlay");
    var viewer = null;

    function applyView(view) {
      if (!viewer) return;
      viewer.setLayer("red", view === "all" || view === "red");
      viewer.setLayer("black", view === "all" || view === "black");
      viewer.setLayer("clip", view === "all" || view === "clip");
    }
    function bootViewer() {
      viewer = window.initViewer3D({
        container: container,
        overlay: overlay,
        msgEl: document.getElementById("v-msg"),
        faceCodeOf: faceCodeOfModelKey,
        faceIdOf: function (key) {
          for (var i = 0; i < FACES.length; i++) if (FACES[i].model === key) return FACES[i].id;
          return null;
        },
        onPickFace: function (code) { selectFace(code, true, true); }
      });
      if (viewer) {
        var c = viewer.counts;
        document.getElementById("v-count").textContent =
          fmt(c.bricks) + " + " + fmt(c.clips) + " = " + fmt(c.bricks + c.clips);
        var act = document.querySelector("#v-seg button.active");
        if (act) applyView(act.getAttribute("data-view"));
        var lb = document.getElementById("v-labels");
        if (lb) viewer.setLabels(lb.checked);
      }
    }
    // build after full load so the loading state is visible and CDN had its chance
    if (document.readyState === "complete") setTimeout(bootViewer, 60);
    else window.addEventListener("load", function () { setTimeout(bootViewer, 60); });

    // segmented layer presets: all / red / black / clip
    var vsegs = document.querySelectorAll("#v-seg button");
    for (var vk = 0; vk < vsegs.length; vk++) {
      vsegs[vk].addEventListener("click", function () {
        for (var vj = 0; vj < vsegs.length; vj++) vsegs[vj].classList.toggle("active", vsegs[vj] === this);
        applyView(this.getAttribute("data-view"));
      });
    }
    var vLabels = document.getElementById("v-labels");
    if (vLabels) vLabels.addEventListener("change", function () {
      if (viewer) viewer.setLabels(this.checked);
    });
    document.getElementById("v-reset").addEventListener("click", function () { if (viewer) viewer.resetView(); });
    document.getElementById("v-all").addEventListener("click", function () { if (viewer) viewer.viewAll(); });
    document.getElementById("v-fs").addEventListener("click", function () {
      if (document.fullscreenElement) document.exitFullscreen();
      else if (shell.requestFullscreen) shell.requestFullscreen();
    });
    document.addEventListener("fullscreenchange", function () {
      var lab = document.querySelector("#v-fs span");
      lab.setAttribute("data-i18n", document.fullscreenElement ? "btn_fs_exit" : "btn_fs");
      lab.textContent = T(document.fullscreenElement ? "btn_fs_exit" : "btn_fs");
      setTimeout(function () { if (viewer) viewer.resize(); }, 80);
    });

    // language re-render for JS-built regions
    document.addEventListener("langchange", function () {
      buildFaceList();
      renderFace(false);
      if (viewer && viewer.refreshLabels) viewer.refreshLabels();
    });

    handleHash();
  });
})();
