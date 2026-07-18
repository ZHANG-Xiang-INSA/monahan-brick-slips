/* viewer.js — Three.js r128 (classic build) hero viewer.
   Model space is z-up metres; mapped to three.js y-up via (x,y,z) -> (x, z, -y).
   InstancedMesh per brick category + clips; minimal inline orbit control (no ES modules). */
(function () {
  "use strict";
  var host = document.getElementById("viewer3d");
  var loading = document.getElementById("viewer-loading");

  if (typeof THREE === "undefined") {
    loading.textContent = "无法加载 Three.js（需要网络访问 CDN）。 Could not load Three.js from the CDN — 3D view unavailable offline.";
    return;
  }

  var DATA = window.DATA_model3d;
  var COLORS = {
    red_full: 0xa63b2a, red_cut: 0xd98e4a, red_corner: 0xcc2a7a,
    black_full: 0x2b2b33, black_cut: 0x6b6b78, clip: 0x2e7dd1
  };

  /* ---------- scene ---------- */
  var scene = new THREE.Scene();
  scene.background = new THREE.Color(0xefebe2);
  scene.fog = new THREE.Fog(0xefebe2, 40, 120);

  var camera = new THREE.PerspectiveCamera(45, 1, 0.1, 500);
  var renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true });
  } catch (e) {
    loading.textContent = "此浏览器不支持 WebGL。 WebGL is not available in this browser.";
    return;
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  host.appendChild(renderer.domElement);

  /* ---------- bounds (model coords) ---------- */
  var min = [1e9, 1e9, 1e9], max = [-1e9, -1e9, -1e9];
  DATA.bricks.forEach(function (b) {
    for (var i = 0; i < 3; i++) {
      min[i] = Math.min(min[i], b.c[i] - b.s[i] / 2);
      max[i] = Math.max(max[i], b.c[i] + b.s[i] / 2);
    }
  });
  var cx = (min[0] + max[0]) / 2, cy = (min[1] + max[1]) / 2, z0 = min[2];
  /* world position of a model point: (x-cx, z-z0, -(y-cy)) */
  function toWorld(c) { return [c[0] - cx, c[2] - z0, -(c[1] - cy)]; }

  /* ---------- instanced meshes ---------- */
  var unit = new THREE.BoxGeometry(1, 1, 1);
  var dummy = new THREE.Object3D();
  var groups = { red: new THREE.Group(), black: new THREE.Group(), clips: new THREE.Group() };
  scene.add(groups.red); scene.add(groups.black); scene.add(groups.clips);

  function buildInstanced(items, kind, parent, isClip) {
    var list = items.filter(function (it) { return it.k === kind; });
    if (!list.length) return;
    var mat = new THREE.MeshStandardMaterial({
      color: COLORS[kind],
      roughness: isClip ? 0.35 : 0.85,
      metalness: isClip ? 0.55 : 0.02
    });
    var mesh = new THREE.InstancedMesh(unit, mat, list.length);
    list.forEach(function (it, i) {
      var p = toWorld(it.c);
      dummy.position.set(p[0], p[1], p[2]);
      dummy.scale.set(Math.max(it.s[0], 0.002), Math.max(it.s[2], 0.002), Math.max(it.s[1], 0.002));
      dummy.rotation.set(0, 0, 0);
      dummy.updateMatrix();
      mesh.setMatrixAt(i, dummy.matrix);
    });
    mesh.instanceMatrix.needsUpdate = true;
    mesh.castShadow = true;
    mesh.receiveShadow = !isClip;
    parent.add(mesh);
  }
  buildInstanced(DATA.bricks, "red_full", groups.red, false);
  buildInstanced(DATA.bricks, "red_cut", groups.red, false);
  buildInstanced(DATA.bricks, "red_corner", groups.red, false);
  buildInstanced(DATA.bricks, "black_full", groups.black, false);
  buildInstanced(DATA.bricks, "black_cut", groups.black, false);
  buildInstanced(DATA.clips, "clip", groups.clips, true);

  /* ---------- lights & ground ---------- */
  scene.add(new THREE.HemisphereLight(0xfff6e8, 0xb0a894, 0.85));
  var sun = new THREE.DirectionalLight(0xffffff, 0.75);
  sun.position.set(14, 20, 10);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  var ext = Math.max(max[0] - min[0], max[1] - min[1], max[2] - min[2]);
  sun.shadow.camera.left = -ext; sun.shadow.camera.right = ext;
  sun.shadow.camera.top = ext; sun.shadow.camera.bottom = -ext;
  sun.shadow.camera.near = 1; sun.shadow.camera.far = 60;
  sun.shadow.bias = -0.0005;
  scene.add(sun);
  var fill = new THREE.DirectionalLight(0xdfe8ff, 0.25);
  fill.position.set(-10, 8, -12);
  scene.add(fill);

  var ground = new THREE.Mesh(
    new THREE.PlaneGeometry(ext * 6, ext * 6),
    new THREE.ShadowMaterial({ opacity: 0.22 })
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.01;
  ground.receiveShadow = true;
  scene.add(ground);
  var groundTint = new THREE.Mesh(
    new THREE.CircleGeometry(ext * 1.6, 48),
    new THREE.MeshStandardMaterial({ color: 0xe6e0d4, roughness: 1 })
  );
  groundTint.rotation.x = -Math.PI / 2;
  groundTint.position.y = -0.02;
  groundTint.receiveShadow = true;
  scene.add(groundTint);

  /* ---------- minimal orbit control ---------- */
  var target = new THREE.Vector3(0, (max[2] - min[2]) / 2, 0);
  var sph = { r: ext * 1.7, theta: Math.PI / 4.2, phi: Math.PI / 3.1 }; // radius, azimuth, polar
  function applyCamera() {
    sph.phi = Math.max(0.05, Math.min(Math.PI / 2 - 0.02, sph.phi));
    sph.r = Math.max(ext * 0.25, Math.min(ext * 6, sph.r));
    camera.position.set(
      target.x + sph.r * Math.sin(sph.phi) * Math.sin(sph.theta),
      target.y + sph.r * Math.cos(sph.phi),
      target.z + sph.r * Math.sin(sph.phi) * Math.cos(sph.theta)
    );
    camera.lookAt(target);
  }
  applyCamera();

  var drag = null;
  var cv = renderer.domElement;
  cv.style.touchAction = "none";
  cv.addEventListener("contextmenu", function (e) { e.preventDefault(); });
  cv.addEventListener("pointerdown", function (e) {
    drag = { x: e.clientX, y: e.clientY, btn: (e.button === 2 || e.shiftKey) ? "pan" : "rot" };
    cv.setPointerCapture(e.pointerId);
  });
  cv.addEventListener("pointermove", function (e) {
    if (!drag) return;
    var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    drag.x = e.clientX; drag.y = e.clientY;
    if (drag.btn === "rot") {
      sph.theta -= dx * 0.006;
      sph.phi -= dy * 0.006;
    } else {
      var panScale = sph.r * 0.0016;
      var fwd = new THREE.Vector3().subVectors(target, camera.position); fwd.y = 0; fwd.normalize();
      var right = new THREE.Vector3(-fwd.z, 0, fwd.x);
      target.addScaledVector(right, dx * panScale);
      target.y += dy * panScale;
      target.y = Math.max(-2, Math.min(max[2] - min[2] + 4, target.y));
    }
    applyCamera();
  });
  cv.addEventListener("pointerup", function () { drag = null; });
  cv.addEventListener("wheel", function (e) {
    e.preventDefault();
    sph.r *= (e.deltaY > 0 ? 1.1 : 0.9);
    applyCamera();
  }, { passive: false });

  /* pinch zoom */
  var pinch = null;
  cv.addEventListener("touchstart", function (e) {
    if (e.touches.length === 2) {
      pinch = Math.hypot(e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY);
    }
  }, { passive: true });
  cv.addEventListener("touchmove", function (e) {
    if (pinch && e.touches.length === 2) {
      var d = Math.hypot(e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY);
      sph.r *= pinch / d; pinch = d; applyCamera();
    }
  }, { passive: true });
  cv.addEventListener("touchend", function () { pinch = null; }, { passive: true });

  /* ---------- toggles ---------- */
  function bindToggle(id, group) {
    document.getElementById(id).addEventListener("change", function (e) {
      group.visible = e.target.checked;
    });
  }
  bindToggle("tog-red", groups.red);
  bindToggle("tog-black", groups.black);
  bindToggle("tog-clips", groups.clips);

  /* ---------- resize + loop ---------- */
  function resize() {
    var w = host.clientWidth, h = host.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  }
  window.addEventListener("resize", resize);
  resize();

  loading.style.display = "none";
  (function loop() {
    requestAnimationFrame(loop);
    renderer.render(scene, camera);
  })();
})();
