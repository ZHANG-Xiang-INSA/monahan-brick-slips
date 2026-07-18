/* 3D viewer — three.js r128 (classic script), inline orbit controls, no ES modules.
   Extrudes the true cut outlines from window.DATA_model3d into merged
   BufferGeometry per (face × layer) so faces stay raycastable. Corner flats
   (kind red_corner: 215 lap + 107.5 return butting at the arris) are welded
   per course into ONE L-shaped prism with a slightly warmer terracotta so a
   quoin reads as a single wrapping piece, not two bricks — rendering only,
   the underlying entity data is untouched.
   Environment: gradient background, hemisphere + key + fill lights, soft
   ground shadow, subtle fog, sRGB output + ACES tone mapping.
   Labels: billboarded sprite pills (A/B/C/D 墙 + canopy) toggled from the
   toolbar; texts come from window.DATA_faces (name_zh / name_en). */
(function () {
  "use strict";

  // ---------- pure geometry build (no THREE dependency; testable) ----------

  function v3(a) { return { x: a[0], y: a[1], z: a[2] }; }
  function sub(a, b) { return { x: a.x - b.x, y: a.y - b.y, z: a.z - b.z }; }
  function cross(a, b) {
    return { x: a.y * b.z - a.z * b.y, y: a.z * b.x - a.x * b.z, z: a.x * b.y - a.y * b.x };
  }
  function dot(a, b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
  function norm(a) {
    var l = Math.sqrt(dot(a, a)) || 1;
    return { x: a.x / l, y: a.y / l, z: a.z / l };
  }

  // ear clipping of a simple polygon given as 2D points -> triangle index list
  function earClip(pts2) {
    var n = pts2.length, idx = [], i;
    if (n < 3) return idx;
    var order = [];
    var area = 0;
    for (i = 0; i < n; i++) {
      var j = (i + 1) % n;
      area += pts2[i][0] * pts2[j][1] - pts2[j][0] * pts2[i][1];
    }
    for (i = 0; i < n; i++) order.push(i);
    if (area < 0) order.reverse(); // force CCW
    function crossZ(a, b, c) {
      return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
    }
    function inTri(p, a, b, c) {
      var d1 = crossZ(a, b, p), d2 = crossZ(b, c, p), d3 = crossZ(c, a, p);
      return d1 >= -1e-12 && d2 >= -1e-12 && d3 >= -1e-12;
    }
    var guard = 0;
    while (order.length > 3 && guard++ < 10000) {
      var clipped = false;
      for (i = 0; i < order.length; i++) {
        var i0 = order[(i + order.length - 1) % order.length],
            i1 = order[i],
            i2 = order[(i + 1) % order.length];
        var a = pts2[i0], b = pts2[i1], c = pts2[i2];
        if (crossZ(a, b, c) <= 1e-12) continue; // reflex or degenerate
        var ok = true;
        for (var k = 0; k < order.length; k++) {
          var oi = order[k];
          if (oi === i0 || oi === i1 || oi === i2) continue;
          if (inTri(pts2[oi], a, b, c)) { ok = false; break; }
        }
        if (!ok) continue;
        idx.push(i0, i1, i2);
        order.splice(i, 1);
        clipped = true;
        break;
      }
      if (!clipped) break; // fallback: fan the rest
    }
    if (order.length === 3) idx.push(order[0], order[1], order[2]);
    else for (i = 1; i < order.length - 1; i++) idx.push(order[0], order[i], order[i + 1]);
    return idx;
  }

  // rectilinear union outline of two butting axis-aligned plan rectangles
  // (a corner lap + its 20 mm return) -> one CCW polygon, collinear points
  // merged. The union encloses exactly the same solid as the two boxes, so
  // this is a pure meshing change: continuous edges, no coincident faces.
  function unionOutline(A, B) {
    var eps = 5e-4, i, j;
    function axis(vals) {
      vals.sort(function (p, q) { return p - q; });
      var out = [vals[0]];
      for (var k2 = 1; k2 < vals.length; k2++) {
        if (vals[k2] - out[out.length - 1] > eps) out.push(vals[k2]);
      }
      return out;
    }
    var xs = axis([A.x0, A.x1, B.x0, B.x1]);
    var ys = axis([A.y0, A.y1, B.y0, B.y1]);
    function filled(ci, cj) {
      if (ci < 0 || cj < 0 || ci >= xs.length - 1 || cj >= ys.length - 1) return false;
      var x = (xs[ci] + xs[ci + 1]) / 2, y = (ys[cj] + ys[cj + 1]) / 2;
      return (x > A.x0 - eps && x < A.x1 + eps && y > A.y0 - eps && y < A.y1 + eps) ||
             (x > B.x0 - eps && x < B.x1 + eps && y > B.y0 - eps && y < B.y1 + eps);
    }
    // boundary edges of filled cells, interior kept on the left => CCW loop
    var next = {}, start = null;
    function edge(a0, b0, a1, b1) {
      next[a0 + "," + b0] = [a1, b1];
      if (!start) start = [a0, b0];
    }
    for (i = 0; i < xs.length - 1; i++) {
      for (j = 0; j < ys.length - 1; j++) {
        if (!filled(i, j)) continue;
        if (!filled(i, j - 1)) edge(i, j, i + 1, j);         // bottom, +x
        if (!filled(i + 1, j)) edge(i + 1, j, i + 1, j + 1); // right, +y
        if (!filled(i, j + 1)) edge(i + 1, j + 1, i, j + 1); // top, -x
        if (!filled(i - 1, j)) edge(i, j + 1, i, j);         // left, -y
      }
    }
    if (!start) return null;
    var loop = [], cur = start, guard = 0;
    do {
      loop.push(cur);
      cur = next[cur[0] + "," + cur[1]];
      if (!cur || ++guard > 64) return null;
    } while (cur[0] !== start[0] || cur[1] !== start[1]);
    var pts = [], out = [];
    for (i = 0; i < loop.length; i++) pts.push([xs[loop[i][0]], ys[loop[i][1]]]);
    for (i = 0; i < pts.length; i++) {
      var p0 = pts[(i + pts.length - 1) % pts.length], p1 = pts[i], p2 = pts[(i + 1) % pts.length];
      var cz = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0]);
      if (Math.abs(cz) > 1e-12) out.push(p1);
    }
    return out.length >= 4 ? out : null;
  }

  var LAYER_OF = { red_full: "red", red_cut: "red", red_corner: "red", black_full: "black", black_cut: "black", clip: "clip" };
  var BASE_RGB = {
    red:   [0.647, 0.255, 0.196],  // terracotta #A54132
    black: [0.235, 0.227, 0.219],  // lifted slightly so it reads on the dark stage
    clip:  [0.51, 0.545, 0.58]     // steel grey
  };
  // corner lap/return flats: one step warmer than the field so the quoin
  // column reads as a deliberate element — still clearly red brick, no shout
  var CORNER_RGB = [0.698, 0.290, 0.220]; // #B24A38 vs field #A54132
  // authored in sRGB; renderer outputs sRGB, so feed linear values to the GPU
  function srgb2lin(c) { return Math.pow(Math.max(0, c), 2.2); }

  // returns {buckets:{key:{face,layer,positions[],colors[]}}, counts, bbox}
  function buildModelBuffers(DATA) {
    var buckets = {}, counts = { bricks: 0, clips: 0 };
    var bb = { min: [1e9, 1e9, 1e9], max: [-1e9, -1e9, -1e9] };

    function bucket(face, layer, sub) {
      var key = face + "|" + layer + (sub ? "|" + sub : "");
      if (!buckets[key]) buckets[key] = { face: face, layer: layer, sub: sub || null, positions: [], colors: [] };
      return buckets[key];
    }

    function jitter(seed) { // deterministic small shade variation
      var x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
      return (x - Math.floor(x)) * 0.14 - 0.07;
    }

    function emitPrism(bkt, base, n, h0, h1, rgb) {
      // base: array of [x,y,z]; prism from base + n*h0 to base + n*h1
      var i, m = base.length;
      var lo = [], hi = [];
      for (i = 0; i < m; i++) {
        lo.push([base[i][0] + n.x * h0, base[i][1] + n.y * h0, base[i][2] + n.z * h0]);
        hi.push([base[i][0] + n.x * h1, base[i][1] + n.y * h1, base[i][2] + n.z * h1]);
        var p = base[i];
        if (p[0] < bb.min[0]) bb.min[0] = p[0]; if (p[0] > bb.max[0]) bb.max[0] = p[0];
        if (p[1] < bb.min[1]) bb.min[1] = p[1]; if (p[1] > bb.max[1]) bb.max[1] = p[1];
        if (p[2] < bb.min[2]) bb.min[2] = p[2]; if (p[2] > bb.max[2]) bb.max[2] = p[2];
      }
      // 2D projection basis on the plane
      var ref = Math.abs(n.z) < 0.9 ? { x: 0, y: 0, z: 1 } : { x: 1, y: 0, z: 0 };
      var u = norm(cross(ref, n)), v = cross(n, u);
      var pts2 = [];
      for (i = 0; i < m; i++) {
        var q = v3(base[i]);
        pts2.push([dot(q, u), dot(q, v)]);
      }
      var tris = earClip(pts2);
      var P = bkt.positions, C = bkt.colors;
      function tri(a, b, c) {
        P.push(a[0], a[1], a[2], b[0], b[1], b[2], c[0], c[1], c[2]);
        C.push(rgb[0], rgb[1], rgb[2], rgb[0], rgb[1], rgb[2], rgb[0], rgb[1], rgb[2]);
      }
      for (i = 0; i < tris.length; i += 3) {
        tri(hi[tris[i]], hi[tris[i + 1]], hi[tris[i + 2]]);          // top cap
        tri(lo[tris[i + 2]], lo[tris[i + 1]], lo[tris[i]]);          // bottom cap
      }
      for (i = 0; i < m; i++) { // side walls
        var j2 = (i + 1) % m;
        tri(lo[i], lo[j2], hi[j2]);
        tri(lo[i], hi[j2], hi[i]);
      }
    }

    var faces = DATA.faces, i, e, n, hB = DATA.meta.brick_h;

    // --- corner-flat welding (rendering only; entity data untouched) ------
    // Each course at an external corner is a 215 lap + a 107.5 return that
    // butt at the arris. Drawn as two prisms they read as two bricks (colour
    // step + coincident internal faces). Pair them by course + adjacency and
    // extrude the plan-union L instead: identical enclosed solid, continuous
    // edges, one shade per physical piece.
    var weldSkip = {}, weldPoly = {}, cornerStats = { welded: 0, solo: 0 }, cornerTotal = 0;
    (function () {
      var rects = [], tol = 1e-4, ci, cj, cb, cp;
      for (ci = 0; ci < DATA.bricks.length; ci++) {
        cb = DATA.bricks[ci];
        if (cb.k !== "red_corner") continue;
        cornerTotal++;
        if (!cb.pts || cb.pts.length !== 4) continue;
        var cn2 = cb.n || (faces[cb.f] && faces[cb.f].n);
        if (!cn2 || Math.abs(cn2[2]) > 1e-6) continue;       // vertical walls only
        var samex = true, samey = true;
        for (cj = 1; cj < 4; cj++) {                         // must sit in an axis plane
          if (Math.abs(cb.pts[cj][0] - cb.pts[0][0]) > tol) samex = false;
          if (Math.abs(cb.pts[cj][1] - cb.pts[0][1]) > tol) samey = false;
        }
        if (!samex && !samey) continue;
        var xs = [], ys = [], zs = [];
        for (cj = 0; cj < 4; cj++) {
          cp = cb.pts[cj];
          xs.push(cp[0], cp[0] + cn2[0] * hB);
          ys.push(cp[1], cp[1] + cn2[1] * hB);
          zs.push(cp[2]);
        }
        rects.push({
          i: ci,
          x0: Math.min.apply(null, xs), x1: Math.max.apply(null, xs),
          y0: Math.min.apply(null, ys), y1: Math.max.apply(null, ys),
          z0: Math.min.apply(null, zs), z1: Math.max.apply(null, zs)
        });
      }
      for (ci = 0; ci < rects.length; ci++) {
        var a = rects[ci];
        if (weldSkip[a.i] || weldPoly[a.i]) continue;
        for (cj = ci + 1; cj < rects.length; cj++) {
          var b = rects[cj];
          if (weldSkip[b.i] || weldPoly[b.i]) continue;
          if (Math.abs(a.z0 - b.z0) > tol || Math.abs(a.z1 - b.z1) > tol) continue;
          if (DATA.bricks[a.i].f === DATA.bricks[b.i].f) continue;
          if (a.x0 > b.x1 + tol || b.x0 > a.x1 + tol ||
              a.y0 > b.y1 + tol || b.y0 > a.y1 + tol) continue; // must butt at the arris
          // lead = the lap (longer leg); it draws the welded L and owns the bucket
          var la = Math.max(a.x1 - a.x0, a.y1 - a.y0), lb = Math.max(b.x1 - b.x0, b.y1 - b.y0);
          var lead = la >= lb ? a : b, mate = la >= lb ? b : a;
          var poly = unionOutline(lead, mate);
          if (!poly) continue;                               // fallback: leave both as-is
          weldPoly[lead.i] = { poly: poly, z0: Math.min(lead.z0, mate.z0), z1: Math.max(lead.z1, mate.z1) };
          weldSkip[mate.i] = 1;
          cornerStats.welded++;
          break;
        }
      }
      cornerStats.solo = cornerTotal - cornerStats.welded * 2;
    })();

    for (i = 0; i < DATA.bricks.length; i++) {
      e = DATA.bricks[i];
      counts.bricks++;
      if (weldSkip[i]) continue;                   // merged into its lap's welded L
      n = e.n ? norm(v3(e.n)) : v3(faces[e.f].n);
      var layer = LAYER_OF[e.k] || "red";
      var isCorner = e.k === "red_corner";
      var base = isCorner ? CORNER_RGB : BASE_RGB[layer];
      var jt = jitter(i) * (isCorner ? 0.6 : 1);   // calmer variation on the quoin
      var rgb = [srgb2lin(base[0] + jt), srgb2lin(base[1] + jt), srgb2lin(base[2] + jt)];
      var w = weldPoly[i];
      if (w) {
        var wl = [], wi;
        for (wi = 0; wi < w.poly.length; wi++) wl.push([w.poly[wi][0], w.poly[wi][1], w.z0]);
        emitPrism(bucket(e.f, layer, "corner"), wl, { x: 0, y: 0, z: 1 }, 0, w.z1 - w.z0, rgb);
        if (w.z1 > bb.max[2]) bb.max[2] = w.z1;    // base ring alone misses the top cap
      } else {
        emitPrism(bucket(e.f, layer, isCorner ? "corner" : null), e.pts, n, 0, hB, rgb);
      }
    }
    for (i = 0; i < DATA.clips.length; i++) {
      e = DATA.clips[i];
      n = v3(faces[e.f].n);
      var jc = jitter(i + 90001) * 0.5;
      var rgbc = [srgb2lin(BASE_RGB.clip[0] + jc), srgb2lin(BASE_RGB.clip[1] + jc), srgb2lin(BASE_RGB.clip[2] + jc)];
      // clips extrude along -n; nudge off the wall plane to avoid z-fighting,
      // and give the 0.25 mm steel a 2 mm visual body so it reads on screen
      emitPrism(bucket(e.f, "clip"), e.pts, n, -0.0006, -0.0026, rgbc);
      counts.clips++;
    }
    return { buckets: buckets, counts: counts, bbox: bb, corners: cornerStats };
  }
  window.buildModelBuffers = buildModelBuffers; // exposed for validation

  // ---------- inline orbit controls ----------

  function OrbitLite(camera, dom, opts) {
    var tgt = opts.target.clone();
    var sph = { r: opts.radius, theta: opts.theta, phi: opts.phi };
    var state = null, sx = 0, sy = 0, moved = 0;
    var self = { onchange: function () {}, onclickpick: null };

    function apply() {
      sph.phi = Math.max(0.05, Math.min(Math.PI - 0.05, sph.phi));
      sph.r = Math.max(opts.minR, Math.min(opts.maxR, sph.r));
      // z-up spherical
      camera.position.set(
        tgt.x + sph.r * Math.sin(sph.phi) * Math.cos(sph.theta),
        tgt.y + sph.r * Math.sin(sph.phi) * Math.sin(sph.theta),
        tgt.z + sph.r * Math.cos(sph.phi)
      );
      camera.up.set(0, 0, 1);
      camera.lookAt(tgt);
      self.onchange();
    }
    function pan(dx, dy) {
      var scale = sph.r * 0.0016;
      var fwd = new THREE.Vector3().subVectors(tgt, camera.position).normalize();
      var right = new THREE.Vector3().crossVectors(fwd, camera.up).normalize();
      var up = new THREE.Vector3().crossVectors(right, fwd).normalize();
      tgt.addScaledVector(right, -dx * scale).addScaledVector(up, dy * scale);
      apply();
    }
    dom.addEventListener("pointerdown", function (ev) {
      state = (ev.button === 2 || ev.shiftKey) ? "pan" : "rot";
      sx = ev.clientX; sy = ev.clientY; moved = 0;
      try { dom.setPointerCapture(ev.pointerId); } catch (e) {}
    });
    dom.addEventListener("pointermove", function (ev) {
      if (!state) return;
      var dx = ev.clientX - sx, dy = ev.clientY - sy;
      sx = ev.clientX; sy = ev.clientY;
      moved += Math.abs(dx) + Math.abs(dy);
      if (state === "rot") {
        sph.theta -= dx * 0.006;
        sph.phi -= dy * 0.006;
        apply();
      } else pan(dx, dy);
    });
    dom.addEventListener("pointerup", function (ev) {
      if (state && moved < 6 && ev.button === 0 && self.onclickpick) self.onclickpick(ev);
      state = null;
    });
    dom.addEventListener("pointercancel", function () { state = null; });
    dom.addEventListener("contextmenu", function (ev) { ev.preventDefault(); });
    dom.addEventListener("wheel", function (ev) {
      ev.preventDefault();
      sph.r *= (ev.deltaY > 0 ? 1.12 : 1 / 1.12);
      apply();
    }, { passive: false });
    // touch pinch
    var pinch = null;
    dom.addEventListener("touchstart", function (ev) {
      if (ev.touches.length === 2) {
        pinch = Math.hypot(ev.touches[0].clientX - ev.touches[1].clientX,
                           ev.touches[0].clientY - ev.touches[1].clientY);
      }
    }, { passive: true });
    dom.addEventListener("touchmove", function (ev) {
      if (ev.touches.length === 2 && pinch) {
        var d = Math.hypot(ev.touches[0].clientX - ev.touches[1].clientX,
                           ev.touches[0].clientY - ev.touches[1].clientY);
        sph.r *= pinch / d; pinch = d; apply();
        ev.preventDefault();
      }
    }, { passive: false });

    self.set = function (t, r, th, ph) {
      tgt.copy(t); sph.r = r; sph.theta = th; sph.phi = ph; apply();
    };
    self.apply = apply;
    apply();
    return self;
  }

  // ---------- label sprite painting ----------

  function pillPath(g, x, y, w, h, r) {
    g.beginPath();
    g.moveTo(x + r, y);
    g.lineTo(x + w - r, y);
    g.arcTo(x + w, y, x + w, y + r, r);
    g.lineTo(x + w, y + h - r);
    g.arcTo(x + w, y + h, x + w - r, y + h, r);
    g.lineTo(x + r, y + h);
    g.arcTo(x, y + h, x, y + h - r, r);
    g.lineTo(x, y + r);
    g.arcTo(x, y, x + r, y, r);
    g.closePath();
  }

  function paintLabel(sprite) {
    var d = sprite.userData.def;
    var zh = !window.LANG || window.LANG() === "zh";
    var text = (zh ? d.zh : d.en) || d.zh || "";
    // supersample 3x (dpr-aware) so the smaller label stays sharp when scaled down
    var dpr = Math.min(window.devicePixelRatio || 1, 2) * 3;
    var fs = 12, padX = 8, padY = 5, dotR = 2.5, dotGap = 6;
    var font = '600 ' + fs + 'px -apple-system,"Segoe UI",system-ui,"PingFang SC","Microsoft YaHei",sans-serif';
    var c = document.createElement("canvas");
    var g = c.getContext("2d");
    g.font = font;
    var tw = Math.ceil(g.measureText(text).width);
    var w = padX + dotR * 2 + dotGap + tw + padX;
    var h = fs + padY * 2;
    c.width = Math.ceil(w * dpr); c.height = Math.ceil(h * dpr);
    g = c.getContext("2d");
    g.scale(dpr, dpr);
    pillPath(g, 0.75, 0.75, w - 1.5, h - 1.5, (h - 1.5) / 2);
    g.fillStyle = "rgba(15,17,21,0.84)";
    g.fill();
    g.strokeStyle = "rgba(255,255,255,0.30)";
    g.lineWidth = 1;
    g.stroke();
    g.beginPath();
    g.arc(padX + dotR, h / 2, dotR, 0, Math.PI * 2);
    g.fillStyle = d.dot;
    g.fill();
    g.font = font;
    g.textBaseline = "middle";
    g.fillStyle = "#F4F2ED";
    g.fillText(text, padX + dotR * 2 + dotGap, h / 2 + 0.5);
    var tex = new THREE.CanvasTexture(c);
    tex.minFilter = THREE.LinearFilter;
    tex.generateMipmaps = false;
    if (THREE.sRGBEncoding !== undefined) tex.encoding = THREE.sRGBEncoding;
    if (sprite.material.map && sprite.material.map.dispose) sprite.material.map.dispose();
    sprite.material.map = tex;
    sprite.material.needsUpdate = true;
    // sizeAttenuation:false => constant screen size; 0.032 ≈ 4.2% of viewport
    // height (was 0.05 ≈ 6.5% — labels are neat annotations, not big chips)
    var H = 0.032;
    sprite.scale.set(H * (c.width / c.height), H, 1);
  }

  // ---------- viewer wiring ----------

  window.initViewer3D = function (cfg) {
    // cfg: {container, overlay, msgEl, faceCodeOf(faceKey)->code|null,
    //       faceIdOf(faceKey)->DATA_faces id|null, onPickFace(code)}
    var el = cfg.container;
    var failed = false;

    function fail() {
      if (failed) return;
      failed = true;
      // swap the skeleton for the static drawing preview (structure lives in the HTML)
      cfg.overlay.classList.remove("hidden");
      cfg.overlay.classList.add("failed");
    }

    if (!window.THREE || !window.DATA_model3d) { fail(); return null; }

    var renderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    } catch (e) { fail(); return null; }

    try {
      renderer.setClearColor(0x15171a, 1);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      // mild filmic tone: sRGB output + ACES, soft shadows
      if (THREE.sRGBEncoding !== undefined) renderer.outputEncoding = THREE.sRGBEncoding;
      if (THREE.ACESFilmicToneMapping !== undefined) {
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.06;
      }
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      el.appendChild(renderer.domElement);

      var scene = new THREE.Scene();
      var camera = new THREE.PerspectiveCamera(42, 1, 0.05, 500);

      var built = buildModelBuffers(window.DATA_model3d);
      var mat = new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide });
      var groups = { red: new THREE.Group(), black: new THREE.Group(), clip: new THREE.Group() };
      var pickables = [];
      Object.keys(built.buckets).forEach(function (key) {
        var b = built.buckets[key];
        var g = new THREE.BufferGeometry();
        g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(b.positions), 3));
        g.setAttribute("color", new THREE.BufferAttribute(new Float32Array(b.colors), 3));
        g.computeVertexNormals();
        var mesh = new THREE.Mesh(g, mat);
        mesh.userData = { faceKey: b.face, layer: b.layer, sub: b.sub || null, faceCode: cfg.faceCodeOf(b.face) };
        mesh.castShadow = b.layer !== "clip";
        groups[b.layer].add(mesh);
        if (b.layer !== "clip") pickables.push(mesh);
      });
      scene.add(groups.red); scene.add(groups.black); scene.add(groups.clip);

      var bb = built.bbox;
      var center = new THREE.Vector3((bb.min[0] + bb.max[0]) / 2, (bb.min[1] + bb.max[1]) / 2, (bb.min[2] + bb.max[2]) / 2);
      var diag = Math.hypot(bb.max[0] - bb.min[0], bb.max[1] - bb.min[1], bb.max[2] - bb.min[2]);
      var HOME = { r: diag * 1.05, theta: -Math.PI / 2 - 0.62, phi: 1.12 }; // from the front-left, slightly above

      // ----- environment: gradient sky, fog, lights, ground -----
      var bgc = document.createElement("canvas");
      bgc.width = 2; bgc.height = 512;
      var bgg = bgc.getContext("2d");
      var grad = bgg.createLinearGradient(0, 0, 0, 512);
      grad.addColorStop(0, "#20242a");   // matches the CSS gradient on #viewer3d
      grad.addColorStop(1, "#15171a");
      bgg.fillStyle = grad; bgg.fillRect(0, 0, 2, 512);
      var bgTex = new THREE.CanvasTexture(bgc);
      bgTex.minFilter = THREE.LinearFilter;
      bgTex.generateMipmaps = false;
      if (THREE.sRGBEncoding !== undefined) bgTex.encoding = THREE.sRGBEncoding;
      scene.background = bgTex;

      var fogCol = new THREE.Color(0x171a1f);
      if (fogCol.convertSRGBToLinear) fogCol.convertSRGBToLinear();
      scene.fog = new THREE.Fog(fogCol, diag * 2.6, diag * 7.5);

      var hemi = new THREE.HemisphereLight(0x9db4c6, 0x4c443e, 0.85); // sky / ground bounce
      scene.add(hemi);
      var key = new THREE.DirectionalLight(0xffe9d2, 0.9);            // warm key, front-left-top
      key.position.set(center.x - diag * 0.55, center.y - diag * 0.8, center.z + diag * 0.9);
      key.target.position.copy(center);
      key.castShadow = true;
      key.shadow.mapSize.width = 2048;
      key.shadow.mapSize.height = 2048;
      key.shadow.camera.left = -diag * 0.85;
      key.shadow.camera.right = diag * 0.85;
      key.shadow.camera.top = diag * 0.85;
      key.shadow.camera.bottom = -diag * 0.85;
      key.shadow.camera.near = diag * 0.2;
      key.shadow.camera.far = diag * 4;
      key.shadow.bias = -0.0004;
      if (key.shadow.normalBias !== undefined) key.shadow.normalBias = 0.03;
      scene.add(key); scene.add(key.target);
      var fill = new THREE.DirectionalLight(0xbdd2e8, 0.32);          // cool fill from behind-right
      fill.position.set(center.x + diag * 0.7, center.y + diag * 0.45, center.z + diag * 0.3);
      fill.target.position.copy(center);
      scene.add(fill); scene.add(fill.target);

      var groundZ = bb.min[2] - 0.01;
      var ground = new THREE.Mesh(
        new THREE.CircleGeometry(diag * 2.4, 64),
        new THREE.ShadowMaterial({ opacity: 0.34 })
      );
      ground.position.set(center.x, center.y, groundZ);
      ground.receiveShadow = true;
      scene.add(ground);
      // soft radial pool so the model reads grounded even if shadow maps fail
      var pc = document.createElement("canvas");
      pc.width = pc.height = 256;
      var pg = pc.getContext("2d");
      var rg = pg.createRadialGradient(128, 128, 10, 128, 128, 128);
      rg.addColorStop(0, "rgba(0,0,0,0.26)");
      rg.addColorStop(0.65, "rgba(0,0,0,0.10)");
      rg.addColorStop(1, "rgba(0,0,0,0)");
      pg.fillStyle = rg; pg.fillRect(0, 0, 256, 256);
      var poolTex = new THREE.CanvasTexture(pc);
      poolTex.minFilter = THREE.LinearFilter;
      poolTex.generateMipmaps = false;
      var pool = new THREE.Mesh(
        new THREE.PlaneGeometry(diag * 1.7, diag * 1.7),
        new THREE.MeshBasicMaterial({ map: poolTex, transparent: true, depthWrite: false })
      );
      pool.position.set(center.x, center.y, groundZ - 0.02);
      scene.add(pool);

      // ----- floating face labels (billboarded, DATA_faces names) -----
      var facesById = {};
      (window.DATA_faces && window.DATA_faces.faces || []).forEach(function (f) { facesById[f.id] = f; });
      var csum = {}, cn = {}, czmax = {};
      (function () { // per-face centroid + top from brick vertices (group by entity.f)
        var B = window.DATA_model3d.bricks;
        for (var i = 0; i < B.length; i++) {
          var e = B[i], a = csum[e.f];
          if (!a) { a = csum[e.f] = [0, 0, 0]; cn[e.f] = 0; czmax[e.f] = -1e9; }
          for (var j = 0; j < e.pts.length; j++) {
            a[0] += e.pts[j][0]; a[1] += e.pts[j][1]; a[2] += e.pts[j][2];
            if (e.pts[j][2] > czmax[e.f]) czmax[e.f] = e.pts[j][2];
          }
          cn[e.f] += e.pts.length;
        }
      })();
      function centroid(keys) {
        var s = [0, 0, 0], n = 0;
        for (var i = 0; i < keys.length; i++) {
          var k = keys[i];
          if (!csum[k]) continue;
          s[0] += csum[k][0]; s[1] += csum[k][1]; s[2] += csum[k][2]; n += cn[k];
        }
        return n ? [s[0] / n, s[1] / n, s[2] / n] : [center.x, center.y, center.z];
      }
      function recOf(faceKey) {
        var id = cfg.faceIdOf ? cfg.faceIdOf(faceKey) : null;
        return (id && facesById[id]) || null;
      }
      function shortName(rec, zh) { // "A墙 — 东北侧立面…" -> "A墙"; "Wall A — NE…" -> "Wall A"
        if (!rec) return "";
        var t = (zh ? rec.name_zh : rec.name_en) || "";
        return t.split("—")[0].split(" - ")[0].trim();
      }
      var DF = window.DATA_model3d.faces;
      var labelDefs = [];
      Object.keys(DF).forEach(function (fk) {     // the 4 red walls: A/B/C/D 墙
        if (DF[fk].grp !== "red_wall") return;
        var rec = recOf(fk), c = centroid([fk]), nn = DF[fk].n;
        labelDefs.push({
          zh: shortName(rec, true) || fk, en: shortName(rec, false) || fk,
          dot: "#C05540",
          pos: [c[0] + nn[0] * 0.55, c[1] + nn[1] * 0.55, c[2] + nn[2] * 0.55]
        });
      });
      (function () {                              // canopy gable front
        var fk = "black_frontframe_+360";
        if (!DF[fk] || !csum[fk]) return;
        var rec = recOf(fk), c = centroid([fk]);
        labelDefs.push({
          zh: rec ? rec.name_zh.replace(/正面$/, "") : "雨棚山墙",
          en: rec ? rec.name_en.replace(/\s*front$/i, "") : "Canopy gable",
          dot: "#8A847C",
          pos: [c[0], c[1] - 0.55, c[2] + 0.1]
        });
      })();
      (function () {                              // canopy body: slopes + side walls grouped
        var keys = Object.keys(DF).filter(function (k) {
          return DF[k].grp === "black" && k.indexOf("frontframe") < 0;
        });
        if (!keys.length) return;
        var c = centroid(keys), zTop = -1e9;
        for (var i = 0; i < keys.length; i++) {
          if (czmax[keys[i]] !== undefined && czmax[keys[i]] > zTop) zTop = czmax[keys[i]];
        }
        if (zTop < -1e8) zTop = c[2];
        labelDefs.push({ zh: "雨棚", en: "Canopy", dot: "#8A847C",
          pos: [c[0], c[1], zTop + 0.45] });
      })();
      (function () {                              // quoin columns (welded corner flats)
        var B = window.DATA_model3d.bricks, cols = [], i2, j2;
        for (i2 = 0; i2 < B.length; i2++) {
          if (B[i2].k !== "red_corner") continue;
          var p = B[i2].pts, sx = 0, sy = 0, zt = -1e9;
          for (j2 = 0; j2 < p.length; j2++) {
            sx += p[j2][0]; sy += p[j2][1];
            if (p[j2][2] > zt) zt = p[j2][2];
          }
          sx /= p.length; sy /= p.length;
          var hit = null;
          for (j2 = 0; j2 < cols.length; j2++) {
            if (Math.abs(cols[j2].x - sx) < 0.6 && Math.abs(cols[j2].y - sy) < 0.6) { hit = cols[j2]; break; }
          }
          if (!hit) { hit = { x: sx, y: sy, m: 0, zTop: -1e9 }; cols.push(hit); }
          hit.x = (hit.x * hit.m + sx) / (hit.m + 1);
          hit.y = (hit.y * hit.m + sy) / (hit.m + 1);
          hit.m++;
          if (zt > hit.zTop) hit.zTop = zt;
        }
        for (i2 = 0; i2 < cols.length; i2++) {
          var dx = cols[i2].x - center.x, dy = cols[i2].y - center.y;
          var dl = Math.hypot(dx, dy) || 1;
          labelDefs.push({
            zh: "转角", en: "Quoin", dot: "#B24A38",
            pos: [cols[i2].x + (dx / dl) * 0.4, cols[i2].y + (dy / dl) * 0.4,
                  Math.max(cols[i2].zTop * 0.55, 0.5)]
          });
        }
      })();
      var labelGroup = new THREE.Group();
      labelDefs.forEach(function (d) {
        var sp = new THREE.Sprite(new THREE.SpriteMaterial({
          transparent: true, depthTest: true, depthWrite: false,
          sizeAttenuation: false, toneMapped: false
        }));
        sp.userData.def = d;
        sp.position.set(d.pos[0], d.pos[1], d.pos[2]);
        sp.renderOrder = 10;
        paintLabel(sp);
        labelGroup.add(sp);
      });
      scene.add(labelGroup);

      // ----- controls / picking / loop -----
      var needsRender = true;
      function invalidate() { needsRender = true; }

      var controls = OrbitLite(camera, el, {
        target: center, radius: HOME.r, theta: HOME.theta, phi: HOME.phi,
        minR: diag * 0.12, maxR: diag * 4
      });
      controls.onchange = invalidate;

      // picking
      var ray = new THREE.Raycaster(), mouse = new THREE.Vector2();
      controls.onclickpick = function (ev) {
        var rect = renderer.domElement.getBoundingClientRect();
        mouse.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
        ray.setFromCamera(mouse, camera);
        var visible = pickables.filter(function (m) { return m.parent.visible; });
        var hit = ray.intersectObjects(visible, false)[0];
        if (hit && hit.object.userData.faceCode) cfg.onPickFace(hit.object.userData.faceCode);
      };
      el.classList.add("picking");

      function resize() {
        var w = el.clientWidth, h = el.clientHeight;
        if (!w || !h) return;
        renderer.setSize(w, h);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        invalidate();
      }
      window.addEventListener("resize", resize);
      resize();

      (function loop() {
        requestAnimationFrame(loop);
        if (needsRender) { needsRender = false; renderer.render(scene, camera); }
      })();

      cfg.overlay.classList.add("hidden");

      return {
        counts: built.counts,
        labelCount: labelDefs.length,
        setLayer: function (layer, on) { groups[layer].visible = on; invalidate(); },
        setLabels: function (on) { labelGroup.visible = !!on; invalidate(); },
        refreshLabels: function () { // re-paint in the current language
          for (var i = 0; i < labelGroup.children.length; i++) paintLabel(labelGroup.children[i]);
          invalidate();
        },
        resetView: function () { controls.set(center, HOME.r, HOME.theta, HOME.phi); },
        viewAll: function () { controls.set(center, diag * 1.35, HOME.theta, 1.05); },
        resize: resize
      };
    } catch (e) {
      fail();
      return null;
    }
  };
})();
