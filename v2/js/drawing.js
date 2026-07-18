/* Drawing viewer overlay — wheel zoom to cursor, drag pan, double-click zoom,
   Prev/Next within an entry list, Esc, Download SVG. */
(function () {
  "use strict";

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

    var list = [], idx = 0;
    var s = 1, tx = 0, ty = 0, natW = 0, natH = 0;

    function applyT() {
      plane.style.transform = "translate(" + tx + "px," + ty + "px) scale(" + s + ")";
    }
    function fit() {
      if (!natW || !natH) return;
      var W = stage.clientWidth, H = stage.clientHeight;
      var pad = 40;
      s = Math.min((W - pad) / natW, (H - pad) / natH);
      if (!isFinite(s) || s <= 0) s = 1;
      tx = (W - natW * s) / 2;
      ty = (H - natH * s) / 2;
      applyT();
    }
    function show() {
      var e = list[idx];
      codeEl.textContent = e.code || "";
      nameEl.childNodes[0].textContent = e.name;
      subEl.textContent = e.sub || "";
      idxEl.textContent = (idx + 1) + " / " + list.length;
      dlEl.href = e.src;
      dlEl.setAttribute("download", e.src.split("/").pop());
      natW = 0; natH = 0;
      img.onload = function () {
        // elevation SVGs carry only a viewBox — naturalWidth is unreliable there,
        // so prefer the catalogued sheet size when provided
        natW = e.w || img.naturalWidth || 1000;
        natH = e.h || img.naturalHeight || 700;
        img.style.width = natW + "px";
        img.style.height = natH + "px";
        fit();
      };
      img.src = e.src;
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

    // pan
    var drag = null;
    stage.addEventListener("pointerdown", function (ev) {
      drag = { x: ev.clientX, y: ev.clientY };
      stage.classList.add("dragging");
      stage.setPointerCapture(ev.pointerId);
    });
    stage.addEventListener("pointermove", function (ev) {
      if (!drag) return;
      tx += ev.clientX - drag.x; ty += ev.clientY - drag.y;
      drag = { x: ev.clientX, y: ev.clientY };
      applyT();
    });
    stage.addEventListener("pointerup", function () { drag = null; stage.classList.remove("dragging"); });

    // zoom at cursor
    function zoomAt(cx, cy, f) {
      var r = stage.getBoundingClientRect();
      var px = cx - r.left, py = cy - r.top;
      var ns = Math.max(0.05, Math.min(12, s * f));
      f = ns / s;
      tx = px - (px - tx) * f;
      ty = py - (py - ty) * f;
      s = ns;
      applyT();
    }
    stage.addEventListener("wheel", function (ev) {
      ev.preventDefault();
      zoomAt(ev.clientX, ev.clientY, ev.deltaY > 0 ? 1 / 1.18 : 1.18);
    }, { passive: false });
    stage.addEventListener("dblclick", function (ev) { zoomAt(ev.clientX, ev.clientY, 2); });

    document.getElementById("dv-close").addEventListener("click", close);
    document.getElementById("dv-reset").addEventListener("click", fit);
    document.getElementById("dv-prev").addEventListener("click", function () { step(-1); });
    document.getElementById("dv-next").addEventListener("click", function () { step(1); });
    document.addEventListener("keydown", function (ev) {
      if (!el.classList.contains("open")) return;
      if (ev.key === "Escape") close();
      else if (ev.key === "ArrowLeft") step(-1);
      else if (ev.key === "ArrowRight") step(1);
    });
    window.addEventListener("resize", function () { if (el.classList.contains("open")) fit(); });

    return { open: open, close: close };
  };
})();
