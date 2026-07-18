/* Drawing pan/zoom.
   window.PanZoom — shared robust pan/zoom engine used by BOTH the inline
   elevation stage (main.js) and the fullscreen drawing overlay below.
   - pointer events with setPointerCapture on the container (try/catch),
     move/up/cancel ALSO bound to window so a drag survives the cursor leaving
     the element or a lost capture;
   - translate is applied BEFORE scale (transform-origin 0 0), so panning is in
     screen px and independent of zoom: at 3x zoom a drag of N px moves N px;
   - crisp vector zoom: when opts.img is given (the SVG <img>), zooming in
     grows the img's LAYOUT size so the browser re-rasterizes the vector at
     the new scale — transform-scaling alone upscaled a cached raster and
     went blurry; only the sub-step remainder rides on the CSS transform;
   - stale-pointer protection (missed pointerup used to leave a ghost pointer
     that made every later drag look like a pinch — the "can't drag" bug);
   - clamped so the drawing can never be lost fully off-screen;
   - wheel zooms toward the cursor; double-click steps zoom / resets when deep.
   window.DrawingViewer — fullscreen overlay: Prev/Next, Esc, Download SVG. */
(function () {
  "use strict";

  window.PanZoom = function (stage, plane, opts) {
    opts = opts || {};
    var pad = opts.pad || 34;   // fit padding (px)
    var KEEP = 56;              // px of drawing that must stay visible on screen
    var img = opts.img || null; // SVG <img> to layout-resize for crisp zoom
    var s = 1, tx = 0, ty = 0, natW = 0, natH = 0, fitS = 1, touched = false;
    var lastW = 0, lastH = 0;

    // power-of-2 layout upsizing that covers the current zoom, capped so huge
    // sheets don't allocate absurd rasters (≤ ~6000 css px on the long side)
    function rasterScale() {
      if (!img || !natW || s <= 1.001) return 1;
      var cap = Math.max(1, Math.min(4, 6000 / Math.max(natW, natH)));
      return Math.min(cap, Math.pow(2, Math.ceil(Math.log(s) / Math.LN2)));
    }

    function clamp() {
      if (!natW || !natH) return;
      var W = stage.clientWidth, H = stage.clientHeight;
      if (!W || !H) return;
      var w = natW * s, h = natH * s;
      var mx = Math.min(KEEP, w / 2), my = Math.min(KEEP, h / 2);
      if (tx > W - mx) tx = W - mx;
      if (tx < mx - w) tx = mx - w;
      if (ty > H - my) ty = H - my;
      if (ty < my - h) ty = my - h;
    }
    function apply() {
      clamp();
      var rs = 1;
      if (img && natW) {
        rs = rasterScale();
        var w = Math.round(natW * rs), h = Math.round(natH * rs);
        if (w !== lastW || h !== lastH) { // layout only when the step changes
          img.style.width = w + "px";
          img.style.height = h + "px";
          lastW = w; lastH = h;
        }
      }
      // translate FIRST => pan step is in stage px, unaffected by scale();
      // displayed size = layout(nat*rs) * (s/rs) = nat*s, same as before
      plane.style.transform = "translate(" + tx + "px," + ty + "px) scale(" + (s / rs) + ")";
    }
    function fit() {
      if (!natW || !natH) return;
      var W = stage.clientWidth, H = stage.clientHeight;
      if (!W || !H) return;
      s = Math.min((W - pad) / natW, (H - pad) / natH);
      if (!isFinite(s) || s <= 0) s = 1;
      fitS = s;
      tx = (W - natW * s) / 2;
      ty = (H - natH * s) / 2;
      touched = false;
      apply();
    }
    function zoomAt(cx, cy, f) {
      if (!natW) return;
      var r = stage.getBoundingClientRect();
      var px = cx - r.left, py = cy - r.top;
      var lo = Math.max(0.02, fitS * 0.2), hi = Math.max(16, fitS * 12);
      var ns = Math.max(lo, Math.min(hi, s * f));
      f = ns / s;
      tx = px - (px - tx) * f;   // keep the point under the cursor fixed
      ty = py - (py - ty) * f;
      s = ns; touched = true;
      apply();
    }

    // ---- pointers: capture on the stage, move/up bound to WINDOW ----
    var ptrs = {};               // pointerId -> [x,y] last seen (screen px)
    var pinchD = 0;
    function ids() { return Object.keys(ptrs); }
    function endAll() {
      ptrs = {}; pinchD = 0;
      stage.classList.remove("dragging");
    }
    stage.addEventListener("pointerdown", function (ev) {
      if (ev.button === 2) return;                 // right button: leave alone
      if (ev.pointerType === "mouse") { ptrs = {}; pinchD = 0; } // drop stale state
      ptrs[ev.pointerId] = [ev.clientX, ev.clientY];
      var l = ids();
      if (l.length === 2) {
        var a = ptrs[l[0]], b = ptrs[l[1]];
        pinchD = Math.hypot(a[0] - b[0], a[1] - b[1]);
      }
      try { stage.setPointerCapture(ev.pointerId); } catch (e) { /* window listeners cover us */ }
      stage.classList.add("dragging");
      ev.preventDefault();
    });
    window.addEventListener("pointermove", function (ev) {
      var prev = ptrs[ev.pointerId];
      if (!prev) return;
      if (ev.pointerType === "mouse" && ev.buttons === 0) { endAll(); return; } // missed pointerup
      ptrs[ev.pointerId] = [ev.clientX, ev.clientY];
      var l = ids();
      if (l.length >= 2) {       // pinch about the midpoint
        var a = ptrs[l[0]], b = ptrs[l[1]];
        var d = Math.hypot(a[0] - b[0], a[1] - b[1]);
        if (pinchD > 0 && d > 0) zoomAt((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, d / pinchD);
        pinchD = d;
      } else {                   // pan in screen px — zoom-independent
        tx += ev.clientX - prev[0];
        ty += ev.clientY - prev[1];
        touched = true;
        apply();
      }
    });
    function drop(ev) {
      if (!(ev.pointerId in ptrs)) return;
      delete ptrs[ev.pointerId];
      pinchD = 0;
      if (!ids().length) stage.classList.remove("dragging");
    }
    window.addEventListener("pointerup", drop);
    window.addEventListener("pointercancel", drop);
    window.addEventListener("blur", endAll);

    stage.addEventListener("wheel", function (ev) {
      ev.preventDefault();
      zoomAt(ev.clientX, ev.clientY, ev.deltaY > 0 ? 1 / 1.18 : 1.18);
    }, { passive: false });
    stage.addEventListener("dblclick", function (ev) {
      ev.preventDefault();
      if (s > fitS * 5) fit();                  // already deep in: reset
      else zoomAt(ev.clientX, ev.clientY, 2);   // otherwise step in at cursor
    });
    window.addEventListener("resize", function () {
      if (!touched && stage.clientWidth) fit();
    });

    return {
      setSize: function (w, h) { natW = w; natH = h; fit(); },
      fit: fit,
      zoomAt: zoomAt,
      zoom: function (f) {       // about the stage centre (toolbar buttons)
        var r = stage.getBoundingClientRect();
        zoomAt(r.left + r.width / 2, r.top + r.height / 2, f);
      }
    };
  };

  // ---------- fullscreen drawing overlay ----------
  window.DrawingViewer = function () {
    var el = document.getElementById("dv");
    var stage = document.getElementById("dv-stage");
    var plane = document.getElementById("dv-plane");
    var img = document.getElementById("dv-img");
    var codeEl = document.getElementById("dv-code");
    var nameEl = document.getElementById("dv-name");
    var subEl = document.getElementById("dv-sub");
    var idxEl = document.getElementById("dv-idx");
    var dlEl = document.getElementById("dv-download");

    var pz = window.PanZoom(stage, plane, { pad: 40, img: img });
    var list = [], idx = 0, lastSrc = "";

    function show() {
      var e = list[idx];
      codeEl.textContent = e.code || "";
      nameEl.childNodes[0].textContent = e.name;
      subEl.textContent = e.sub || "";
      idxEl.textContent = (idx + 1) + " / " + list.length;
      dlEl.href = e.src;
      dlEl.setAttribute("download", e.src.split("/").pop());
      var done = function () {
        // elevation SVGs carry only a viewBox — naturalWidth is unreliable
        // there, so prefer the catalogued sheet size when provided
        var w = e.w || img.naturalWidth || 1000;
        var h = e.h || img.naturalHeight || 700;
        pz.setSize(w, h); // PanZoom owns the img layout size (crisp zoom)
      };
      if (lastSrc === e.src) { done(); return; } // same sheet: load may not re-fire
      lastSrc = e.src;
      img.onload = done;
      img.src = e.src;
      if (img.complete) done();
    }

    function open(entries, at) {
      list = entries; idx = at || 0;
      el.classList.add("open");
      document.body.style.overflow = "hidden";
      show();
    }
    function close() {
      el.classList.remove("open");
      document.body.style.overflow = "";
    }
    function step(d) { idx = (idx + d + list.length) % list.length; show(); }

    document.getElementById("dv-close").addEventListener("click", close);
    document.getElementById("dv-reset").addEventListener("click", pz.fit);
    document.getElementById("dv-prev").addEventListener("click", function () { step(-1); });
    document.getElementById("dv-next").addEventListener("click", function () { step(1); });
    document.addEventListener("keydown", function (ev) {
      if (!el.classList.contains("open")) return;
      if (ev.key === "Escape") close();
      else if (ev.key === "ArrowLeft") step(-1);
      else if (ev.key === "ArrowRight") step(1);
    });
    window.addEventListener("resize", function () { if (el.classList.contains("open")) pz.fit(); });

    return { open: open, close: close };
  };
})();
