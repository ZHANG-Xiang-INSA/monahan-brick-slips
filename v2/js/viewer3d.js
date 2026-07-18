/* 3D viewer — three.js r128 (classic script), inline orbit controls, no ES modules.
   Extrudes the true cut outlines from window.DATA_model3d into merged
   BufferGeometry per (face × layer) so faces stay raycastable. */
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

  var LAYER_OF = { red_full: "red", red_cut: "red", red_corner: "red", black_full: "black", black_cut: "black", clip: "clip" };
  var BASE_RGB = {
    red:   [0.596, 0.278, 0.208],  // terracotta #98472f-ish
    black: [0.196, 0.184, 0.172],
    clip:  [0.486, 0.514, 0.545]   // steel grey
  };

  // returns {buckets:{key:{face,layer,positions[],colors[]}}, counts, bbox}
  function buildModelBuffers(DATA) {
    var buckets = {}, counts = { bricks: 0, clips: 0 };
    var bb = { min: [1e9, 1e9, 1e9], max: [-1e9, -1e9, -1e9] };

    function bucket(face, layer) {
      var key = face + "|" + layer;
      if (!buckets[key]) buckets[key] = { face: face, layer: layer, positions: [], colors: [] };
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
    for (i = 0; i < DATA.bricks.length; i++) {
      e = DATA.bricks[i];
      n = e.n ? norm(v3(e.n)) : v3(faces[e.f].n);
      var layer = LAYER_OF[e.k] || "red";
      var base = BASE_RGB[layer], jt = jitter(i);
      var rgb = [Math.max(0, base[0] + jt), Math.max(0, base[1] + jt), Math.max(0, base[2] + jt)];
      emitPrism(bucket(e.f, layer), e.pts, n, 0, hB, rgb);
      counts.bricks++;
    }
    for (i = 0; i < DATA.clips.length; i++) {
      e = DATA.clips[i];
      n = v3(faces[e.f].n);
      var jc = jitter(i + 90001) * 0.5;
      var rgbc = [BASE_RGB.clip[0] + jc, BASE_RGB.clip[1] + jc, BASE_RGB.clip[2] + jc];
      // clips extrude along -n; nudge off the wall plane to avoid z-fighting,
      // and give the 0.25 mm steel a 2 mm visual body so it reads on screen
      emitPrism(bucket(e.f, "clip"), e.pts, n, -0.0006, -0.0026, rgbc);
      counts.clips++;
    }
    return { buckets: buckets, counts: counts, bbox: bb };
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
      dom.setPointerCapture(ev.pointerId);
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

  // ---------- viewer wiring ----------

  window.initViewer3D = function (cfg) {
    // cfg: {container, overlay, msgEl, faceCodeOf(faceKey)->code|null, onPickFace(code)}
    var el = cfg.container;
    var failed = false;

    function fail() {
      if (failed) return;
      failed = true;
      cfg.overlay.classList.remove("hidden");
      cfg.overlay.querySelector(".v-progress").style.display = "none";
      cfg.msgEl.setAttribute("data-i18n", "v_fail");
      cfg.msgEl.textContent = window.T("v_fail");
      cfg.overlay.querySelector(".v-fail-link").style.display = "inline-block";
    }

    if (!window.THREE || !window.DATA_model3d) { fail(); return null; }

    var renderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    } catch (e) { fail(); return null; }

    renderer.setClearColor(0xffffff, 1);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    el.appendChild(renderer.domElement);

    var scene = new THREE.Scene();
    scene.add(new THREE.AmbientLight(0xffffff, 0.62));
    var d1 = new THREE.DirectionalLight(0xffffff, 0.55); d1.position.set(-6, -9, 12); scene.add(d1);
    var d2 = new THREE.DirectionalLight(0xfff3e2, 0.25); d2.position.set(9, 5, 4); scene.add(d2);

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
      mesh.userData = { faceKey: b.face, layer: b.layer, faceCode: cfg.faceCodeOf(b.face) };
      groups[b.layer].add(mesh);
      if (b.layer !== "clip") pickables.push(mesh);
    });
    scene.add(groups.red); scene.add(groups.black); scene.add(groups.clip);

    var bb = built.bbox;
    var center = new THREE.Vector3((bb.min[0] + bb.max[0]) / 2, (bb.min[1] + bb.max[1]) / 2, (bb.min[2] + bb.max[2]) / 2);
    var diag = Math.hypot(bb.max[0] - bb.min[0], bb.max[1] - bb.min[1], bb.max[2] - bb.min[2]);
    var HOME = { r: diag * 1.05, theta: -Math.PI / 2 - 0.62, phi: 1.12 }; // from the front-left, slightly above

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
      setLayer: function (layer, on) { groups[layer].visible = on; invalidate(); },
      resetView: function () { controls.set(center, HOME.r, HOME.theta, HOME.phi); },
      viewAll: function () { controls.set(center, diag * 1.35, HOME.theta, 1.05); },
      resize: resize
    };
  };
})();
