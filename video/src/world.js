// One three.js world holding every location. Everything is a pure function of time t (seconds).
import * as THREE from 'three';
import { INK, cv, tex, rng, drawHead, drawBody, drawOx, drawOxLeg, drawPan, drawStick, drawBoard, stoneTex, plankTex, sailTex, stripeTex, waterTex, skyTex } from './art.js';
import { CUTS } from './words.js';

const sig = (v) => 1 / (1 + Math.exp(-v));
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const sstep = (a, b, v) => { const x = clamp((v - a) / (b - a), 0, 1); return x * x * (3 - 2 * x); };
const lerp = (a, b, k) => a + (b - a) * k;
const ease = (x) => { x = clamp(x, 0, 1); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const nz = (x, z) => Math.sin(x * 0.13 + Math.sin(z * 0.21)) * Math.cos(z * 0.17 + Math.sin(x * 0.11)) + 0.5 * Math.sin(x * 0.41 + z * 0.37);

// ------------------------------------------------------------------ terrain height
export function H(x, z) {
  let h = -3;
  // A: camp plateau (x≈0)
  h = Math.max(h, 9 * sig((z + 22) / 3) * sig((40 - Math.abs(x)) / 4) * sig((40 - z) / 3) - 3 + 0.12 * nz(x, z));
  // B: two shores holding the chain (x≈200)
  h = Math.max(h, 5.5 * (sig((179 - x) / 1.5) * sig((x - 120) / 3) + sig((x - 221) / 1.5) * sig((280 - x) / 3)) * sig((14 - z) / 3) * sig((z + 75) / 3) - 3);
  // C/D: the hill behind Galata (x≈405)
  h = Math.max(h, 13 * Math.exp(-(((x - 405) / 24) ** 2)) * Math.exp(-((z / 45) ** 2)) - 1.2 + 0.1 * nz(x, z) * sig((Math.abs(z) - 2) * 2));
  // E: city side of the sea wall (x≈805)
  h = Math.max(h, 3.5 * sig((z + 10.5) / 1.2) * sig((45 - Math.abs(x - 805)) / 4) * sig((30 - z) / 3) - 3);
  // far shore with the city
  h = Math.max(h, 3.8 * sig(-(z + 126) / 2.5) - 3 + 0.3 * nz(x, z) * sig(-(z + 140)));
  // mountains
  const m = sig(-(z + 215) / 14);
  if (m > 0.01) h = Math.max(h, m * (18 + 34 * Math.abs(Math.sin(x * 0.011 + 1.3)) + 16 * Math.abs(Math.sin(x * 0.031 + z * 0.02)) + 6 * nz(x * 2, z * 2)) - 3);
  return h;
}
const slopeX = (x, z = 0) => (H(x + 0.25, z) - H(x - 0.25, z)) / 0.5;
const G = (x, z, dy) => [x, Math.max(H(x, z), 0) + dy, z];

// ------------------------------------------------------------------ camera helpers
export function warpU(T, t) {
  const n = T.length; if (n < 2 || t <= T[0]) return 0; if (t >= T[n - 1]) return 1;
  const sec = []; for (let i = 0; i < n - 1; i++) sec.push((1 / (n - 1)) / (T[i + 1] - T[i]));
  const m = [0]; for (let i = 1; i < n - 1; i++) m.push((2 * sec[i - 1] * sec[i]) / (sec[i - 1] + sec[i])); m.push(0);
  let i = 0; while (t > T[i + 1]) i++;
  const h = T[i + 1] - T[i], x = (t - T[i]) / h, x2 = x * x, x3 = x2 * x;
  return (2 * x3 - 3 * x2 + 1) * (i / (n - 1)) + (x3 - 2 * x2 + x) * h * m[i] + (-2 * x3 + 3 * x2) * ((i + 1) / (n - 1)) + (x3 - x2) * h * m[i + 1];
}

export function createWorld(canvas, W, Hh) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(1); renderer.setSize(W, Hh, false);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog('#cfe3f3', 70, 520);
  const camera = new THREE.PerspectiveCamera(60, W / Hh, 0.1, 2500);

  // toon gradient (3 bands)
  const grad = new THREE.DataTexture(new Uint8Array([105, 185, 255]), 3, 1, THREE.RedFormat);
  grad.minFilter = grad.magFilter = THREE.NearestFilter; grad.needsUpdate = true;
  const toon = (color, map, extra = {}) => new THREE.MeshToonMaterial({ color, map: map || null, gradientMap: grad, ...extra });
  const basic = (o) => new THREE.MeshBasicMaterial(o);

  // lights
  const hemi = new THREE.HemisphereLight('#d7ecff', '#7c9a58', 1.25); scene.add(hemi);
  const sun = new THREE.DirectionalLight('#fff0d4', 2.1);
  sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
  const sc = sun.shadow.camera; sc.left = -28; sc.right = 28; sc.top = 28; sc.bottom = -28; sc.near = 1; sc.far = 140; sun.shadow.bias = -0.0006; sun.shadow.normalBias = 0.03;
  scene.add(sun); scene.add(sun.target);

  // sky dome following the camera
  const sky = new THREE.Mesh(new THREE.SphereGeometry(1800, 48, 24), basic({ map: tex(skyTex()), side: THREE.BackSide, fog: false, depthWrite: false }));
  sky.renderOrder = -10; scene.add(sky);

  // ---------------------------------------------------------------- terrain
  {
    const x0 = -150, x1 = 950, z0 = -345, z1 = 60, sx = 1.5, sz = 2;
    const nx = Math.round((x1 - x0) / sx), nzc = Math.round((z1 - z0) / sz);
    const geo = new THREE.PlaneGeometry(x1 - x0, z1 - z0, nx, nzc); geo.rotateX(-Math.PI / 2); geo.translate((x0 + x1) / 2, 0, (z0 + z1) / 2);
    const p = geo.attributes.position, col = new Float32Array(p.count * 3);
    const cSand = new THREE.Color('#e6d39c'), cG1 = new THREE.Color('#79c64b'), cG2 = new THREE.Color('#58a83b'), cM = new THREE.Color('#6f9c72'), cTop = new THREE.Color('#b9c7b4'), cSea = new THREE.Color('#c9b98a'), c = new THREE.Color();
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i), z = p.getZ(i), h = H(x, z); p.setY(i, h);
      if (h < -0.3) c.copy(cSea); else if (h < 0.35) c.copy(cSand);
      else { c.copy(cG1).lerp(cG2, clamp(0.5 + 0.5 * nz(x * 1.7, z * 1.7), 0, 1)); if (z < -190) c.lerp(cM, clamp((h - 6) / 14, 0, 1)).lerp(cTop, clamp((h - 38) / 14, 0, 1)); }
      col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
    }
    geo.setAttribute('color', new THREE.BufferAttribute(col, 3)); geo.computeVertexNormals();
    const terrain = new THREE.Mesh(geo, toon('#ffffff', null, { vertexColors: true })); terrain.receiveShadow = true; scene.add(terrain);
  }
  // water
  const wTex = tex(waterTex(), [160, 80]);
  const water = new THREE.Mesh(new THREE.PlaneGeometry(1400, 600), toon('#ffffff', wTex));
  water.rotation.x = -Math.PI / 2; water.position.set(400, 0, -140); water.receiveShadow = true; scene.add(water);

  // grass tufts near the camera spots
  function grass(cx, cz, w, d, count, seed, avoid) {
    const R = rng(seed), geo = new THREE.ConeGeometry(0.022, 0.24, 3); geo.translate(0, 0.12, 0);
    const mesh = new THREE.InstancedMesh(geo, toon('#ffffff'), count), m = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), s = new THREE.Vector3(), v = new THREE.Vector3(), c = new THREE.Color();
    let n = 0;
    for (let k = 0; k < count * 3 && n < count; k++) {
      const x = cx + (R() - 0.5) * w, z = cz + (R() - 0.5) * d, h = H(x, z);
      if (h < 0.4 || (avoid && avoid(x, z))) continue;
      e.set((R() - 0.5) * 0.5, R() * 6, (R() - 0.5) * 0.5); q.setFromEuler(e); const sc = 0.5 + R() * 0.6; s.set(sc, sc * (0.8 + R() * 0.6), sc);
      m.compose(v.set(x, h - 0.02, z), q, s); mesh.setMatrixAt(n, m); mesh.setColorAt(n, c.set(R() < 0.5 ? '#6fbf45' : '#8fd35a').multiplyScalar(0.85 + R() * 0.3)); n++;
    }
    mesh.count = n; return mesh;
  }

  // ---------------------------------------------------------------- generic props
  const stoneMap = tex(stoneTex(1), [3, 2]), stoneMat = toon('#ffffff', stoneMap);
  const woodMat = toon('#ffffff', tex(plankTex('#8a5631', 4), [1, 1]));
  const darkWood = toon('#6b4426');
  function box(w, h, d, mat) { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.castShadow = true; m.receiveShadow = true; return m; }
  function cyl(r0, r1, h, mat, seg = 16) { const m = new THREE.Mesh(new THREE.CylinderGeometry(r0, r1, h, seg), mat); m.castShadow = true; m.receiveShadow = true; return m; }
  function tower(r, h, roof, merlons = true) {
    const g = new THREE.Group();
    const map = tex(stoneTex(3), [Math.round(r * 2), Math.round(h / 3)]);
    const body = cyl(r, r * 1.06, h + 4, toon('#ffffff', map), 24); body.position.y = (h - 4) / 2; g.add(body);
    if (merlons) for (let i = 0; i < 12; i++) { const a = (i / 12) * Math.PI * 2, mm = box(r * 0.38, 1.0, 0.6, stoneMat); mm.position.set(Math.cos(a) * r * 0.95, h + 0.5, Math.sin(a) * r * 0.95); mm.rotation.y = -a; g.add(mm); }
    if (roof) { const rf = new THREE.Mesh(new THREE.ConeGeometry(r * 1.15, r * 1.6, 24), toon(roof)); rf.position.y = h + (merlons ? 1 : 0) + r * 0.8; rf.castShadow = true; g.add(rf); }
    return g;
  }
  function boardMesh(canvas, w, h) {
    const mats = [darkWood, darkWood, darkWood, darkWood, toon('#ffffff', tex(canvas)), darkWood];
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.1), mats); m.castShadow = true; return m;
  }
  function signPost(lines, w, h, postH, opts) {
    const g = new THREE.Group(); const p = cyl(0.07, 0.08, postH, darkWood, 8); p.position.y = postH / 2; g.add(p);
    const b = boardMesh(drawBoard(lines, opts), w, h); b.position.set(0, postH - h / 2 + 0.05, 0.08); g.add(b); g.board = b; return g;
  }
  function banner(lines, w, h, poleH) {
    const g = new THREE.Group();
    for (const s of [-1, 1]) { const p = cyl(0.06, 0.07, poleH, darkWood, 8); p.position.set(s * (w / 2 + 0.06), poleH / 2, 0); g.add(p); const k = new THREE.Mesh(new THREE.SphereGeometry(0.1, 10, 8), toon('#e2b33c')); k.position.set(s * (w / 2 + 0.06), poleH + 0.05, 0); g.add(k); }
    const geo = new THREE.PlaneGeometry(w, h, 8, 1); geo.translate(0, -h / 2, 0);
    const cloth = new THREE.Mesh(geo, toon('#ffffff', tex(drawBoard(lines, { cloth: true, w: 1024, h: Math.round(1024 * h / w), size: 0.62 })), { side: THREE.DoubleSide }));
    cloth.position.y = poleH - 0.12; g.add(cloth); g.cloth = cloth; return g;
  }

  // ---------------------------------------------------------------- galley
  const hullMap = tex(plankTex('#8a5631', 6, 512, 256, { color: '#b8312f', v: 0.13 }));
  const deckMap = tex(plankTex('#c49a63', 8, 512, 128));
  const sailMap = tex(sailTex());
  function galleyGeo() {
    const N = 32, pos = [], uv = [], idx = [];
    const ring = [];
    for (let i = 0; i <= N; i++) {
      const u = i / N, s = 2 * u - 1;
      const w = Math.max(0.02, s > 0 ? 0.95 * Math.sqrt(Math.max(0, 1 - Math.pow(s, 2.2))) : 0.95 * Math.sqrt(Math.max(0, 1 - Math.pow(-s, 3))));
      const yd = 1.0 + 0.6 * Math.max(0, (s - 0.75) / 0.25) ** 2 + 0.9 * Math.max(0, (-s - 0.7) / 0.3) ** 2;
      const ky = 0.55 * Math.max(0, (Math.abs(s) - 0.78) / 0.22) ** 2;
      const x = -4.5 + 9 * u;
      const pts = [[-w, yd], [-0.82 * w, ky + 0.36], [0, ky], [0.82 * w, ky + 0.36], [w, yd]];
      const vs = [0, 0.3, 0.5, 0.7, 1];
      pts.forEach(([z, y], k) => { pos.push(x, y, z); uv.push(u, 1 - vs[k]); });
      ring.push({ x, w, yd });
    }
    for (let i = 0; i < N; i++) for (let k = 0; k < 4; k++) { const a = i * 5 + k, b = a + 5; idx.push(a, b, a + 1, a + 1, b, b + 1); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.setIndex(idx); g.computeVertexNormals();
    // deck
    const dp = [], du = [], di = [];
    ring.forEach((r, i) => { dp.push(r.x, r.yd - 0.12, -r.w * 0.97, r.x, r.yd - 0.12, r.w * 0.97); du.push(i / N, 0, i / N, 1); });
    for (let i = 0; i < N; i++) { const a = i * 2; di.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
    const d = new THREE.BufferGeometry(); d.setAttribute('position', new THREE.Float32BufferAttribute(dp, 3)); d.setAttribute('uv', new THREE.Float32BufferAttribute(du, 2)); d.setIndex(di); d.computeVertexNormals();
    return { hull: g, deck: d, ring };
  }
  const GG = galleyGeo();
  const hullMat = toon('#ffffff', hullMap, { side: THREE.DoubleSide }), deckMat = toon('#ffffff', deckMap, { side: THREE.DoubleSide });
  const sailMat = toon('#ffffff', sailMap, { side: THREE.DoubleSide }), flagMat = toon('#c62f2f', null, { side: THREE.DoubleSide });
  const oarGeo = new THREE.CylinderGeometry(0.035, 0.05, 3.4, 6); oarGeo.translate(0, -1.7, 0);
  const wheelGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.18, 14); wheelGeo.rotateX(Math.PI / 2);
  const wheelMat = toon('#ffffff', tex((() => { const c = cv(128, 128), g = c.getContext('2d'); g.fillStyle = '#7a4a26'; g.fillRect(0, 0, 128, 128); g.strokeStyle = '#3a2210'; g.lineWidth = 10; g.beginPath(); g.moveTo(64, 0); g.lineTo(64, 128); g.moveTo(0, 64); g.lineTo(128, 64); g.stroke(); g.lineWidth = 14; g.beginPath(); g.arc(64, 64, 56, 0, 7); g.stroke(); return c; })()));
  function galley(seed, withCradle) {
    const R = rng(seed), root = new THREE.Group(), body = new THREE.Group(); root.add(body);
    const hull = new THREE.Mesh(GG.hull, hullMat); hull.castShadow = true; hull.receiveShadow = true; body.add(hull);
    const deck = new THREE.Mesh(GG.deck, deckMat); deck.receiveShadow = true; body.add(deck);
    const ram = new THREE.Mesh(new THREE.ConeGeometry(0.14, 1.3, 8), toon('#d9a93a')); ram.rotation.z = -Math.PI / 2; ram.position.set(5.0, 0.75, 0); body.add(ram);
    const mast = cyl(0.09, 0.11, 6.4, darkWood, 8); mast.position.set(0.6, 1.0 + 3.2, 0); body.add(mast);
    const yard = cyl(0.05, 0.05, 8.2, darkWood, 6); yard.position.set(0.9, 5.4, 0); yard.rotation.z = -1.02; body.add(yard);
    // lateen sail: triangle between yard ends and the deck at the mast
    const ya = new THREE.Vector3(0.9 - Math.sin(1.02) * 4.1, 5.4 - Math.cos(1.02) * 4.1, 0), yb = new THREE.Vector3(0.9 + Math.sin(1.02) * 4.1, 5.4 + Math.cos(1.02) * 4.1, 0);
    const sg = new THREE.BufferGeometry(); sg.setAttribute('position', new THREE.Float32BufferAttribute([ya.x, ya.y, 0.06, yb.x, yb.y, 0.06, 0.6, 1.6, 0.06], 3)); sg.setAttribute('uv', new THREE.Float32BufferAttribute([0, 0, 1, 1, 0.3, 1], 2)); sg.computeVertexNormals();
    const sail = new THREE.Mesh(sg, sailMat); sail.castShadow = true; body.add(sail);
    const flag = new THREE.Mesh(new THREE.PlaneGeometry(1.1, 0.45), flagMat); flag.position.set(0.6 + 0.55, 1.0 + 6.2, 0); body.add(flag);
    const oars = [];
    GG.ring.forEach((r, i) => { if (i % 4 !== 2 || i < 6 || i > 26) return; for (const s of [-1, 1]) { const piv = new THREE.Group(); piv.position.set(r.x, r.yd - 0.15, s * r.w); const o = new THREE.Mesh(oarGeo, darkWood); o.castShadow = true; piv.add(o); piv.userData = { s, ph: i * 0.3 }; body.add(piv); oars.push(piv); } });
    root.body = body; root.oars = oars; root.sail = sail; root.flag = flag; root.seed = R();
    if (withCradle) {
      const cr = new THREE.Group();
      for (const s of [-1, 1]) { const beam = box(7.4, 0.22, 0.22, darkWood); beam.position.set(0, 0.62, s * 0.55); cr.add(beam); }
      for (const x of [-3, -1, 1, 3]) { const tb = box(0.25, 0.3, 1.5, darkWood); tb.position.set(x, 0.8, 0); cr.add(tb); }
      const wheels = [];
      for (const x of [-2.8, 2.8]) for (const s of [-1, 1]) { const w = new THREE.Mesh(wheelGeo, wheelMat); w.position.set(x, 0.4, s * 0.85); w.castShadow = true; cr.add(w); wheels.push(w); }
      cr.visible = false; root.add(cr); root.cradle = cr; root.wheels = wheels;
    }
    scene.add(root); return root;
  }
  // place a galley: mode 'water' (floating) or 'land' (on cradle following terrain along x)
  function setGalley(gal, t, o) {
    gal.visible = o.visible !== false; if (!gal.visible) return;
    const yaw = o.yaw || 0; gal.rotation.set(0, yaw, 0);
    if (o.mode === 'land') {
      const pitch = Math.atan(slopeX(o.x, o.z || 0));
      gal.position.set(o.x, H(o.x, o.z || 0), o.z || 0); gal.rotation.set(0, yaw, pitch);
      gal.body.position.set(0, 0.92, 0); gal.body.rotation.set(0, 0, 0);
      if (gal.cradle) { gal.cradle.visible = true; gal.wheels.forEach((w) => (w.rotation.z = -o.x / 0.4)); }
      gal.oars.forEach((p) => p.rotation.set(p.userData.s * 1.45, 0, 0));
    } else {
      const ph = gal.seed * 10;
      gal.position.set(o.x, -0.42 + 0.07 * Math.sin(t * 1.7 + ph) + (o.dy || 0), o.z || 0);
      gal.body.position.set(0, 0, 0); gal.body.rotation.set(0.035 * Math.sin(t * 1.3 + ph), 0, (o.pitch || 0) + 0.02 * Math.sin(t * 1.1 + ph));
      if (gal.cradle) gal.cradle.visible = !!o.cradle;
      gal.oars.forEach((p) => { const a = o.row ? Math.sin(t * 3.2 + p.userData.ph) : 0; p.rotation.set(p.userData.s * (o.row ? 0.95 + 0.12 * Math.cos(t * 3.2 + p.userData.ph) : 1.1), a * 0.35, 0); });
    }
    gal.flag.rotation.y = 0.25 * Math.sin(t * 4 + gal.seed * 9);
  }

  // ---------------------------------------------------------------- characters (2D flat people in 3D)
  const headCache = new Map();
  const headTex = (key, o) => { if (!headCache.has(key)) headCache.set(key, tex(drawHead(o))); return headCache.get(key); };
  const limbMat = basic({ color: INK }), handMat = basic({ color: '#2b2024' });
  const limbGeo = (len, w) => { const g = new THREE.PlaneGeometry(w, len); g.translate(0, -len / 2, 0); return g; };
  const shadowTex = (() => { const c = cv(128, 128), g = c.getContext('2d'), gr = g.createRadialGradient(64, 64, 4, 64, 64, 62); gr.addColorStop(0, 'rgba(30,25,30,0.55)'); gr.addColorStop(1, 'rgba(30,25,30,0)'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); return tex(c); })();
  function makeChar(id, headO, bodyO, scale = 1, prop) {
    const root = new THREE.Group(), bb = new THREE.Group(); root.add(bb); bb.scale.setScalar(scale);
    const mat = (m) => basic({ map: m, transparent: true, alphaTest: 0.4, side: THREE.DoubleSide });
    const legs = [-1, 1].map((s) => { const p = new THREE.Group(); p.position.set(s * 0.075, 0.52, -0.004); const l = new THREE.Mesh(limbGeo(0.5, 0.045), limbMat); p.add(l); const f = new THREE.Mesh(new THREE.CircleGeometry(0.045, 12), limbMat); f.scale.set(1.6, 0.8, 1); f.position.set(s * 0.03, -0.5, 0); p.add(f); bb.add(p); return p; });
    const body = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), mat(tex(drawBody(bodyO)))); body.position.set(0, 0.73, 0); bb.add(body);
    const head = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), mat(headTex(id + 'calm', { ...headO, expr: 'calm' }))); head.position.set(0, 1.435, 0.004); bb.add(head);
    const arms = [-1, 1].map((s) => { const p = new THREE.Group(); p.position.set(s * 0.17, 0.98, 0.006); const a = new THREE.Mesh(limbGeo(0.42, 0.04), limbMat); p.add(a); const h = new THREE.Mesh(new THREE.CircleGeometry(0.055, 14), handMat); h.position.y = -0.42; h.position.z = 0.001; p.add(h); bb.add(p); return p; });
    let propMesh = null;
    if (prop) { propMesh = new THREE.Mesh(new THREE.PlaneGeometry(prop.w, prop.h), mat(tex(prop.canvas))); propMesh.position.set(prop.x || 0, -0.42 + (prop.y || 0), 0.003); propMesh.rotation.z = prop.rot || 0; arms[prop.arm === 'L' ? 0 : 1].add(propMesh); }
    const sh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), basic({ map: shadowTex, transparent: true, depthWrite: false })); sh.rotation.x = -Math.PI / 2; sh.scale.set(0.9 * scale, 0.5 * scale, 1); sh.renderOrder = 1;
    scene.add(sh); scene.add(root);
    const ch = { id, root, bb, legs, arms, head, body, sh, headO, prop: propMesh, scale };
    return ch;
  }
  function poseChar(ch, t, o) {
    const vis = o.visible !== false; ch.root.visible = vis; ch.sh.visible = vis; if (!vis) return;
    const y = o.y !== undefined ? o.y : Math.max(H(o.x, o.z), 0.0);
    ch.root.position.set(o.x, y, o.z);
    ch.sh.position.set(o.x, y + 0.03, o.z);
    // face the camera (yaw only)
    ch.root.rotation.y = Math.atan2(camera.position.x - o.x, camera.position.z - o.z);
    const ph = (o.ph || 0);
    const walk = o.walk ? t * 7 + ph : 0;
    const bob = o.walk ? Math.abs(Math.sin(walk)) * 0.04 : 0.012 * Math.sin(t * 2.4 + ph);
    ch.bb.position.y = bob;
    ch.bb.rotation.z = o.lean || 0;
    ch.legs[0].rotation.z = o.walk ? 0.38 * Math.sin(walk) : 0;
    ch.legs[1].rotation.z = o.walk ? -0.38 * Math.sin(walk) : 0;
    const sway = 0.06 * Math.sin(t * 2.0 + ph);
    ch.arms[0].rotation.z = (o.armL !== undefined ? o.armL : -0.12) + (o.walk && o.armL === undefined ? 0.35 * Math.sin(walk + Math.PI) : sway);
    ch.arms[1].rotation.z = (o.armR !== undefined ? o.armR : 0.12) + (o.walk && o.armR === undefined ? 0.35 * Math.sin(walk) : -sway);
    ch.head.rotation.z = (o.nod ? 0.05 * Math.sin(t * 5 + ph) : 0.025 * Math.sin(t * 1.6 + ph));
    const expr = o.expr || 'calm', mouth = o.mouth || 'closed';
    ch.head.material.map = headTex(ch.id + expr + mouth, { ...ch.headO, expr, mouth });
    if (ch.prop) ch.prop.visible = o.prop !== false;
  }
  function makeOx() {
    const root = new THREE.Group(), bb = new THREE.Group(); root.add(bb);
    const mat = (m) => basic({ map: m, transparent: true, alphaTest: 0.4, side: THREE.DoubleSide });
    const legTex = tex(drawOxLeg());
    const legs = [-0.62, -0.38, 0.42, 0.66].map((x, i) => { const p = new THREE.Group(); p.position.set(x, 0.62, i % 2 ? 0.002 : -0.003); const g = new THREE.PlaneGeometry(0.16, 0.64); g.translate(0, -0.32, 0); p.add(new THREE.Mesh(g, mat(legTex))); bb.add(p); return p; });
    const body = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 1.5), mat(tex(drawOx()))); body.position.set(0.1, 1.0, 0); bb.add(body);
    const sh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), basic({ map: shadowTex, transparent: true, depthWrite: false })); sh.rotation.x = -Math.PI / 2; sh.scale.set(2.6, 0.9, 1);
    scene.add(root); scene.add(sh);
    return { root, bb, legs, sh };
  }
  function poseOx(ox, t, o) {
    ox.root.visible = ox.sh.visible = o.visible !== false; if (!ox.root.visible) return;
    const y = H(o.x, o.z); ox.root.position.set(o.x, y, o.z); ox.sh.position.set(o.x, y + 0.03, o.z);
    ox.root.rotation.y = Math.atan2(camera.position.x - o.x, camera.position.z - o.z);
    const w = t * 5.5 + (o.ph || 0);
    ox.legs.forEach((l, i) => (l.rotation.z = o.walk ? 0.32 * Math.sin(w + (i % 2) * Math.PI + (i > 1 ? 0.6 : 0)) : 0));
    ox.bb.position.y = o.walk ? Math.abs(Math.sin(w)) * 0.03 : 0;
    ox.bb.rotation.z = Math.atan(slopeX(o.x, o.z)) * 0.8;
  }

  const SKIN = '#fbf7f2';
  const mehmed = makeChar('mehmed', { hat: 'turban', beard: '#3b2a22', skin: SKIN }, { main: '#2f8a57', trim: '#e6b93d', skirt: true, belt: '#c8342f' }, 1.08);
  const commander = makeChar('cmdr', { hat: 'helmet', moustache: true }, { main: '#a83232', pattern: 'studs', skirtColor: '#2b3f86', belt: '#6b4426' }, 1.05,
    { canvas: drawPan(), w: 0.56, h: 0.28, x: 0.2, y: 0.02, rot: 0.5, arm: 'R' });
  const workerSpecs = [
    [{ hair: '#2b1d18', band: '#f4f1ea' }, { main: '#c7743a', pocket: '#e8b04a', belt: '#5a3418' }],
    [{ hat: 'cap', capColor: '#b0402f' }, { main: '#5f8a3a', belt: '#3b2a1a' }],
    [{ hair: '#3a2418', band: '#d23a3a' }, { main: '#8b5fa8', belt: '#3b2a1a' }],
    [{ hat: 'cap', capColor: '#2f5fa8' }, { main: '#d4a447', pocket: '#b0402f' }],
  ];
  const mop = { canvas: drawStick(1, '#a8794a', 'mop'), w: 0.09, h: 0.75, x: 0.0, y: -0.25, rot: -0.2, arm: 'R' };
  const workers = workerSpecs.map((s, i) => makeChar('w' + i, s[0], s[1], 0.98, i < 2 ? mop : null));
  const spear = { canvas: drawStick(1, '#a8794a', 'spear'), w: 0.12, h: 1.6, x: 0.0, y: 0.55, rot: 0, arm: 'R' };
  const defenders = [0, 1, 2].map((i) => makeChar('d' + i, { hat: 'byz' }, { main: ['#3f6fc2', '#4a62b0', '#3a7cc9'][i], trim: '#e9d38a', belt: '#6b4426' }, 1.0, spear));
  const oxen = [makeOx(), makeOx()];

  // ---------------------------------------------------------------- LOCATION A: camp (x≈0)
  const locA = new THREE.Group(); scene.add(locA);
  const hA = H(0, 0);
  const banner1453 = banner(['1453'], 2.3, 0.62, 2.85); banner1453.position.set(0, hA, -1.4); locA.add(banner1453);
  const tentMap = tex(stripeTex('#c8342f', '#f4ead5'), [3, 1]);
  [[-3.6, -3.0, 1.6], [3.8, -4.2, 1.9], [-7, -7, 2.2], [7.5, -9, 2.4], [0.5, -10, 2.0]].forEach(([x, z, s]) => {
    const t = new THREE.Mesh(new THREE.ConeGeometry(s, s * 1.5, 18, 1, true), toon('#ffffff', tentMap, { side: THREE.DoubleSide })); t.position.set(x, H(x, z) + s * 0.75, z); t.castShadow = true; locA.add(t);
    const f = new THREE.Mesh(new THREE.PlaneGeometry(0.5, 0.28), flagMat); f.position.set(x + 0.25, H(x, z) + s * 1.5 + 0.2, z); locA.add(f);
    const pole = cyl(0.03, 0.03, 0.5, darkWood, 6); pole.position.set(x, H(x, z) + s * 1.5 + 0.1, z); locA.add(pole);
  });
  locA.add(grass(0, -2, 30, 22, 7000, 21));
  // a fleet in the water below the camp
  const fleetA = [0, 1, 2, 3].map((i) => galley(100 + i));

  // ---------------------------------------------------------------- far city (all along z≈-130)
  {
    const city = new THREE.Group(); scene.add(city);
    const wall = box(1100, 8, 3, toon('#ffffff', tex(stoneTex(2, '#c8bfae'), [180, 2]))); wall.position.set(400, 4.4, -129); city.add(wall);
    const tg = new THREE.CylinderGeometry(3, 3.2, 14, 12), tm = toon('#cbbfa9');
    const towers = new THREE.InstancedMesh(tg, tm, 40), m4 = new THREE.Matrix4();
    for (let i = 0; i < 40; i++) { m4.makeTranslation(-140 + i * 28, 6, -128.5); towers.setMatrixAt(i, m4); } city.add(towers);
    const R = rng(77), hg = new THREE.BoxGeometry(1, 1, 1), rg = new THREE.ConeGeometry(0.75, 0.6, 4); rg.rotateY(Math.PI / 4);
    const N = 900, houses = new THREE.InstancedMesh(hg, toon('#ffffff'), N), roofs = new THREE.InstancedMesh(rg, toon('#c0583a'), N);
    const q = new THREE.Quaternion(), s = new THREE.Vector3(), p = new THREE.Vector3(), c = new THREE.Color();
    for (let i = 0; i < N; i++) {
      const x = -140 + R() * 1080, z = -134 - R() * 40, w = 3 + R() * 4, d = 3 + R() * 4, h = 3 + R() * 6 + (z < -150 ? 3 : 0), y = H(x, z);
      m4.compose(p.set(x, y + h / 2, z), q, s.set(w, h, d)); houses.setMatrixAt(i, m4); houses.setColorAt(i, c.set(['#efe2c4', '#e8cfa0', '#d9c3a0', '#f2e9d6', '#dcb98c'][Math.floor(R() * 5)]));
      m4.compose(p.set(x, y + h + w * 0.25, z), q, s.set(w * 1.05, w * 0.9, d * 1.05)); roofs.setMatrixAt(i, m4);
    }
    city.add(houses); city.add(roofs);
    for (const x of [10, 200, 300, 520, 800]) {
      const b = new THREE.Group(), y = H(x, -152);
      const base = box(26, 14, 26, toon('#dcc49e')); base.position.y = 7; b.add(base);
      const dome = new THREE.Mesh(new THREE.SphereGeometry(10, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), toon('#8fa1b6')); dome.position.y = 14; b.add(dome);
      for (const [dx, dz] of [[13, 0], [-13, 0]]) { const hd = new THREE.Mesh(new THREE.SphereGeometry(6, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2), toon('#8fa1b6')); hd.position.set(dx, 11, dz); b.add(hd); }
      b.position.set(x, y, -152); city.add(b);
    }
  }

  // ---------------------------------------------------------------- LOCATION B: the chain (x≈200)
  const locB = new THREE.Group(); scene.add(locB);
  const tL = tower(3, 11, '#8a4a3a'); tL.position.set(180.5, H(176, -25), -25); locB.add(tL);
  const tR = tower(3, 11, '#8a4a3a'); tR.position.set(219.5, H(224, -25), -25); locB.add(tR);
  const NL = 64, linkGeo = new THREE.TorusGeometry(0.34, 0.1, 6, 14); linkGeo.scale(1.45, 1, 1);
  const links = new THREE.InstancedMesh(linkGeo, toon('#5a5c66'), NL); links.castShadow = true; locB.add(links);
  const logGeo = new THREE.CylinderGeometry(0.38, 0.38, 3.2, 12); logGeo.rotateZ(Math.PI / 2);
  const logMat = toon('#ffffff', tex(plankTex('#7d5232', 12, 256, 64)));
  const floats = []; for (let i = 0; i < 9; i++) { const l = new THREE.Mesh(logGeo, logMat); l.castShadow = true; l.receiveShadow = true; locB.add(l); floats.push(l); }
  const chainX0 = 183.4, chainX1 = 216.6, chainZ = -25;
  const chainY = (x, t) => { const k = (x - chainX0) / (chainX1 - chainX0) * 8; const f = k - Math.floor(k); return 0.42 - 0.38 * Math.sin(f * Math.PI) + 0.06 * Math.sin(t * 1.5 + x * 0.3); };
  const signGH = signPost(['GOLDEN HORN'], 3.2, 0.8, 2.6, { size: 0.6 }); signGH.position.set(200, -0.6, -26.6); locB.add(signGH);
  const shipsOut = [0, 1].map((i) => galley(200 + i));
  const shipsIn = [0, 1, 2, 3].map((i) => galley(210 + i));

  // ---------------------------------------------------------------- LOCATION C/D: Galata hill (x≈405)
  const locC = new THREE.Group(); scene.add(locC);
  const galata = tower(2.4, 18, '#5b6b84'); galata.position.set(420, H(420, -32), -32); locC.add(galata);
  const signGal = signPost(['GALATA'], 1.7, 0.55, 1.9, { arrow: true, size: 0.55 }); signGal.position.set(375.6, H(375.6, 2.7), 2.7); signGal.rotation.y = -0.45; signGal.userData.hideAfter = 16.85; locC.add(signGal);
  const roadLogs = []; const logGeo2 = new THREE.CylinderGeometry(0.14, 0.14, 2.5, 10); logGeo2.rotateX(Math.PI / 2);
  const dryMat = toon('#ffffff', tex(plankTex('#9a6a3e', 14, 256, 64))), greaseMat = new THREE.MeshPhongMaterial({ color: '#4a3220', shininess: 90, specular: '#fff3d0' });
  for (let x = 367.0; x <= 447; x += 0.62) { const l = new THREE.Mesh(logGeo2, dryMat); l.position.set(x, H(x, 0) + 0.1, 0); l.rotation.z = Math.atan(slopeX(x)); l.castShadow = true; l.receiveShadow = true; locC.add(l); roadLogs.push(l); }
  const buckets = [0, 1].map((i) => { const g = new THREE.Group(); const b = cyl(0.22, 0.18, 0.4, toon('#ffffff', tex(drawBoard(['GREASE'], { w: 512, h: 160, size: 0.6, bg: '#c49a63' }), [1, 1])), 16); b.position.y = 0.2; g.add(b); const top = new THREE.Mesh(new THREE.CircleGeometry(0.2, 16), toon('#2a1a10')); top.rotation.x = -Math.PI / 2; top.position.y = 0.395; g.add(top); locC.add(g); return g; });
  const hillShip = galley(300, true);
  const ropeMat = toon('#c9a46a'); const ropes = [0, 1].map(() => { const r = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 1, 6), ropeMat); scene.add(r); return r; });
  function setRope(r, a, b) { const d = new THREE.Vector3().subVectors(b, a); r.position.copy(a).addScaledVector(d, 0.5); r.scale.set(1, d.length(), 1); r.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.normalize()); }
  locC.add(grass(395, 6, 70, 18, 9000, 31, (x, z) => Math.abs(z) < 1.5));
  const downShips = [0, 1, 2, 3, 4].map((i) => galley(400 + i, true));
  const signCount = signPost(['SHIPS: 0'], 2.0, 0.8, 2.6, { size: 0.5 }); signCount.position.set(444, -0.4, 8.0); signCount.rotation.y = 0.9; locC.add(signCount);
  const countCanvas = cv(1024, 410); const countTex = tex(countCanvas); signCount.board.material[4] = toon('#ffffff', countTex);
  let lastCount = -1;
  function drawCount(n) { if (n === lastCount) return; lastCount = n; const src = drawBoard([n >= 70 ? '~70 SHIPS' : 'SHIPS: ' + n], { w: 1024, h: 410, size: 0.5 }); countCanvas.getContext('2d').drawImage(src, 0, 0); countTex.needsUpdate = true; }
  // splash particles
  const splashGeo = new THREE.SphereGeometry(1, 8, 6), splashMat = toon('#f4fbff');
  const splashes = downShips.map(() => { const m = new THREE.InstancedMesh(splashGeo, splashMat, 46); scene.add(m); return m; });
  const ringGeo = new THREE.RingGeometry(0.8, 1.0, 32); ringGeo.rotateX(-Math.PI / 2);
  const rings = downShips.map(() => { const m = new THREE.Mesh(ringGeo, basic({ color: '#ffffff', transparent: true })); scene.add(m); return m; });

  // ---------------------------------------------------------------- LOCATION E: sea wall (x≈805)
  const locE = new THREE.Group(); scene.add(locE);
  const wallTop = 6.2;
  const seaWall = box(80, wallTop + 3, 3, toon('#ffffff', tex(stoneTex(5, '#bdb6a8'), [16, 2]))); seaWall.position.set(805, (wallTop - 3) / 2, -10.5); locE.add(seaWall);
  for (let x = 767; x < 845; x += 1.3) { const m = box(0.75, 0.9, 0.5, stoneMat); m.position.set(x, wallTop + 0.45, -11.7); locE.add(m); }
  for (const x of [788, 822]) { const tw = tower(2.6, 10, '#8a4a3a'); tw.position.set(x, 0, -10.5); locE.add(tw); }
  const bannerApr = banner(['22 APRIL'], 1.9, 0.55, 0.01); bannerApr.children.forEach((c) => { if (c !== bannerApr.cloth) c.visible = false; }); bannerApr.position.set(805, wallTop - 0.45, -8.96); locE.add(bannerApr);
  locE.add(grass(805, -3, 40, 14, 4000, 41, (x, z) => z < -8.7));
  const shipsE = [0, 1, 2, 3, 4].map((i) => galley(500 + i));

  // ---------------------------------------------------------------- camera plan
  const g0 = (x, z, dy) => new THREE.Vector3(...G(x, z, dy));
  const V = (x, y, z) => new THREE.Vector3(x, y, z);
  const shipCX = (t) => 369 + 29 * ease((t - 26.4) / 5.3);
  const SHOTS = [
    { t: [0, 1.2, 5.3], pos: [g0(0.5, 4.8, 1.35), g0(0.3, 3.8, 1.32), g0(-0.15, 2.75, 1.3)], look: [g0(0, 0, 1.45), g0(0, 0, 1.42), g0(0, 0, 1.35)] },
    { t: [5.3, 7.7], pos: [V(190.6, 1.25, -20.2), V(194.6, 1.45, -19.6)], look: [V(193.5, 0.45, -25), V(197.6, 0.45, -25)] },
    { t: [7.7, 9.0, 10.2, 11.4, 14.4], pos: [V(194.6, 1.45, -19.6), V(196, 6.5, -21), V(198.5, 10.5, -13), V(200, 10.5, -4), V(200, 10.8, 0)], look: [V(197.6, 0.45, -25), V(198, 0, -25), V(200, 0, -25), V(200, 0.3, -24), V(200, 0.5, -25)] },
    { t: [14.4, 16.85], pos: [g0(368.7, 6.3, 2.2), g0(369.5, 5.4, 2.2)], look: [g0(380, -3.4, -4.0), g0(384, -6.2, -5.0)] },
    { t: [16.85, 19.0], pos: [V(361.5, 2.1, 10.5), V(363.2, 2.0, 8.6)], look: [V(364.5, 1.6, 0), V(366.0, 1.9, 0)] },
    { t: [19.0, 20.1, 21.3, 22.65], pos: [g0(366.4, 4.6, 1.55), g0(367.2, 4.6, 1.7), g0(371.5, 5.6, 2.5), g0(374.5, 6.2, 3.0)], look: [g0(371.5, 0, 0.3), g0(373, 0, 0.4), g0(383, 0, 1.2), g0(387.5, 0, 1.8)] },
    { t: [22.65, 26.35], pos: [g0(371.4, 6.9, 1.2), g0(371.45, 5.95, 1.2)], look: [g0(371.4, 3.2, 1.12), g0(371.45, 3.2, 1.12)] },
    { fn: (t) => { const sx = shipCX(t), off = lerp(6.2, 1.2, ease((t - 26.35) / 4.5)); return { pos: g0(sx + off - 1.6, 9.8, 2.6), look: g0(sx + off + 0.8, 0, 2.0) }; } },
    { t: [31.7, 36.8], pos: [V(452.5, 3.6, 12), V(450.5, 3.0, 9.6)], look: [V(431, 5.0, 0), V(439, 2.4, -1.5)] },
    { t: [36.8, 39.9, 42.5], pos: [V(805, wallTop + 1.25, -5.4), V(805, wallTop + 1.2, -6.0), V(805, wallTop + 6.2, -2.2)], look: [V(805, wallTop + 1.05, -10.3), V(805, wallTop + 1.05, -10.3), V(805, 1.6, -34)] },
    { t: [42.5, 46.6], pos: [V(196.2, 1.05, -21.2), V(200, 6.5, 3)], look: [V(194.2, 0.5, -25), V(200, 0.6, -40)] },
  ];
  SHOTS.forEach((s, i) => { s.t0 = CUTS[i]; s.t1 = CUTS[i + 1]; if (s.pos) { s.cp = new THREE.CatmullRomCurve3(s.pos); s.cl = new THREE.CatmullRomCurve3(s.look); } });
  const tmpL = new THREE.Vector3();
  function placeCamera(t) {
    let i = SHOTS.findIndex((s) => t >= s.t0 && t < s.t1); if (i < 0) i = SHOTS.length - 1;
    const s = SHOTS[i]; let pos, look;
    if (s.fn) ({ pos, look } = s.fn(t));
    else { const u = warpU(s.t, t); pos = s.cp.getPoint(u); look = s.cl.getPoint(u); }
    pos.y = Math.max(pos.y, Math.max(H(pos.x, pos.z), 0) + 0.5);
    camera.position.copy(pos); camera.lookAt(look); tmpL.copy(look);
    return i;
  }

  // ---------------------------------------------------------------- update
  const m4 = new THREE.Matrix4(), q4 = new THREE.Quaternion(), e4 = new THREE.Euler(), v4 = new THREE.Vector3(), s4 = new THREE.Vector3();
  function update(t) {
    const shot = placeCamera(t);
    const cx = camera.position.x;
    locA.visible = Math.abs(cx) < 120; locB.visible = Math.abs(cx - 200) < 120; locC.visible = Math.abs(cx - 405) < 120; locE.visible = Math.abs(cx - 805) < 120;
    sky.position.copy(camera.position);
    sun.position.copy(tmpL).add(v4.set(-22, 34, 18)); sun.target.position.copy(tmpL);
    wTex.offset.set(t * 0.004, t * 0.002);

    // --- A
    signGal.visible = t < 16.85;
    banner1453.cloth.scale.y = ease((t - 0.35) / 0.6) * 0.999 + 0.001;
    fleetA.forEach((g, i) => setGalley(g, t, { x: -14 + i * 9, z: -34 - (i % 2) * 7, yaw: 0.3, row: true, visible: locA.visible }));

    // --- characters (positions depend on location in use)
    const inC = locC.visible, inE = locE.visible, inA = locA.visible;
    if (inA) poseChar(mehmed, t, { x: 0, z: 0, expr: 'smug', nod: t > 3.2 && t < 4.2, armL: -0.2, armR: 0.25 });
    else if (inC) {
      const talkM = false;
      poseChar(mehmed, t, { x: 372.1, z: 3.2, expr: 'smug', look: 0, mouth: talkM ? 'open' : 'closed', armR: 0.2 });
    } else poseChar(mehmed, t, { visible: false });
    const talking = t > 23.8 && t < 26.25 && Math.sin(t * 22) > -0.1;
    poseChar(commander, t, { visible: inC && t >= 22.0 && t < 31.7, x: 370.75, z: 3.2, expr: 'angry', mouth: talking ? 'open' : 'closed', prop: t > 25.25, armR: t > 25.25 ? 1.2 + 0.08 * Math.sin(t * 6) : 0.15, armL: -0.25 });

    // workers: greasing (S6) then hauling (S8)
    const sx = shipCX(t);
    if (inC && t < 26.35) {
      const dab = (k) => 0.6 + 0.35 * Math.sin(t * 9 + k);
      poseChar(workers[0], t, { x: 383.2, z: -1.75, expr: 'calm', armR: t > 21.4 ? dab(0) : 0.3 });
      poseChar(workers[1], t, { x: 386.6, z: -1.75, expr: 'sleep', armR: t > 21.6 ? dab(2) : 0.3, ph: 2 });
      poseChar(workers[2], t, { visible: false }); poseChar(workers[3], t, { visible: false });
      buckets[0].position.set(383.9, H(383.9, -1.5), -1.5); buckets[1].position.set(387.3, H(387.3, -1.5), -1.5);
    } else if (inC) {
      poseChar(workers[0], t, { x: sx + 5.6, z: 1.35, walk: true, expr: 'angry', armL: 0.9, armR: 1.1, lean: -0.15 });
      poseChar(workers[1], t, { x: sx - 5.4, z: 1.3, walk: true, expr: 'angry', armL: 1.3, armR: 1.4, lean: -0.25, ph: 1, prop: false });
      poseChar(workers[2], t, { x: sx + 3.6, z: 1.5, walk: true, expr: 'calm', armL: 0.9, armR: 1.0, lean: -0.15, ph: 2 });
      poseChar(workers[3], t, { x: sx + 1.0, z: 1.6, walk: true, expr: 'smug', ph: 3 });
      buckets[0].position.set(375.9, H(375.9, -1.5), -1.5); buckets[1].position.set(379.3, H(379.3, -1.5), -1.5);
    } else workers.forEach((w) => poseChar(w, t, { visible: false }));

    // road logs appear on "road" and get greased on "smeared with grease"
    roadLogs.forEach((l, i) => {
      const x = l.position.x, appear = 20.1 + (x - 367) / 30 * 1.2;
      const k = ease((t - appear) / 0.25); l.visible = k > 0.01; l.scale.set(1, 1, Math.max(0.01, k));
      l.material = t > 21.4 + (x - 367) / 30 * 1.0 ? greaseMat : dryMat;
    });

    // the hill ship: floating at the shore (S4-S7), then hauled on its cradle (S8)
    if (t < 26.35) setGalley(hillShip, t, { mode: 'water', x: 363.1 + (t > 17 && t < 19 ? 0.12 * Math.max(0, Math.sin((t - 17) * 6)) : 0), z: 0 });
    else setGalley(hillShip, t, { mode: 'land', x: sx, z: 0 });
    poseOx(oxen[0], t, { visible: inC && t >= 26.35, x: sx + 7.4, z: 0.75, walk: true });
    poseOx(oxen[1], t, { visible: inC && t >= 26.35, x: sx + 8.6, z: -0.7, walk: true, ph: 1.3 });
    ropes.forEach((r, i) => { r.visible = inC && t >= 26.35; if (!r.visible) return; const bow = hillShip.localToWorld(v4.set(4.6, 1.85, 0)).clone(); const ox = oxen[i].root.position; setRope(r, bow, V(ox.x + 0.6, ox.y + 1.15, ox.z)); });

    // ships rolling down the far side (S9)
    downShips.forEach((g, i) => {
      const ts = 31.85 + i * 0.95, tau = t - ts;
      if (!inC || tau < -0.2) { g.visible = false; splashes[i].visible = false; rings[i].visible = false; return; }
      const xEntry = 443.5, xC = 405 + 38.5 * Math.min(1, Math.max(0, tau) / 2.0) ** 2;
      const zDrift = (i - 2) * 2.6 - 3;
      if (tau < 2.0) setGalley(g, t, { mode: 'land', x: xC, z: 0 });
      else { const k = tau - 2.0, d = 10 * (1 - Math.exp(-k * 1.1)); setGalley(g, t, { mode: 'water', cradle: true, x: xEntry + 2 + d, z: zDrift * (1 - Math.exp(-k * 0.8)), dy: 0.5 * Math.exp(-k * 3) * Math.sin(k * 9), pitch: -0.25 * Math.exp(-k * 2.5) }); }
      // splash
      const k = tau - 2.0, sp = splashes[i], rg = rings[i];
      sp.visible = k > 0 && k < 1.6; rg.visible = k > 0 && k < 2.2;
      if (sp.visible) {
        const R = rng(900 + i);
        for (let j = 0; j < 46; j++) {
          const a = R() * Math.PI * 2, vel = 2 + R() * 4, up = 4 + R() * 5, life = Math.min(k, 1.6);
          const x = xEntry + 3.5 + Math.cos(a) * vel * life * 0.6, z = Math.sin(a) * vel * life * 0.8, y = up * life - 6 * life * life;
          const s = Math.max(0, (0.18 + R() * 0.25) * (1 - life / 1.6));
          m4.compose(v4.set(x, Math.max(-0.2, y), z), q4, s4.set(s, s, s)); sp.setMatrixAt(j, m4);
        }
        sp.instanceMatrix.needsUpdate = true;
      }
      if (rg.visible) { const r = 1 + k * 3; rg.scale.set(r, 1, r); rg.position.set(xEntry + 3.5, 0.03, 0); rg.material.opacity = Math.max(0, 0.8 - k * 0.37); }
    });
    drawCount(Math.round(clamp((t - 32.9) / 1.4, 0, 1) * 70));

    // --- B: chain, floats, ships
    if (locB.visible) {
      for (let i = 0; i < NL; i++) {
        const x = lerp(chainX0, chainX1, i / (NL - 1)), y = chainY(x, t), xn = lerp(chainX0, chainX1, (i + 1) / (NL - 1));
        const ang = Math.atan2(chainY(xn, t) - y, xn - x);
        e4.set(i % 2 ? Math.PI / 2 : 0, 0, ang); q4.setFromEuler(e4); m4.compose(v4.set(x, y, chainZ), q4, s4.set(1, 1, 1)); links.setMatrixAt(i, m4);
      }
      links.instanceMatrix.needsUpdate = true;
      floats.forEach((f, i) => { const x = lerp(chainX0, chainX1, i / 8); f.position.set(x, 0.02 + 0.05 * Math.sin(t * 1.5 + x * 0.3), chainZ); f.visible = i > 0 && i < 8; });
      signGH.position.y = -0.6 + 0.05 * Math.sin(t * 1.3);
      signGH.scale.setScalar(Math.max(0.001, ease((t - 11.05) / 0.35)) * (t < 40 ? 1 : 1));
      // ships ram the chain and bounce back on "could not get past it"
      const pushK = ease((t - 8) / 4.6), bounce = t > 12.6 ? 1.6 * Math.exp(-(t - 12.6) * 1.2) * Math.sin((t - 12.6) * 5) : 0;
      shipsOut.forEach((g, i) => setGalley(g, t, { visible: t < 36, x: i ? 203.5 : 197, z: lerp(-8, -19.2, pushK) + Math.abs(bounce) + i * 3, yaw: Math.PI / 2, row: true }));
      shipsIn.forEach((g, i) => setGalley(g, t, { visible: t > 36, x: [190, 205, 196, 211][i], z: [-38, -40, -48, -50][i], yaw: Math.PI / 2 + [0.3, -0.2, 0.5, -0.4][i] }));
    } else { shipsOut.forEach((g) => (g.visible = false)); shipsIn.forEach((g) => (g.visible = false)); }

    // --- E: wall, defenders, harbor full of ships
    if (inE) {
      const awake = t > 39.3;
      defenders.forEach((d, i) => poseChar(d, t, { x: 803.2 + i * 1.8, z: -10.2, y: wallTop, expr: awake ? 'shock' : 'sleep', armR: awake ? 0.5 : 0.1, armL: awake ? -1.1 - 0.1 * Math.sin(t * 9 + i) : -0.15, lean: awake ? 0 : 0.12 * (i - 1), ph: i }));
      bannerApr.cloth.scale.y = ease((t - 37.4) / 0.5) * 0.999 + 0.001;
      shipsE.forEach((g, i) => setGalley(g, t, { x: [796, 812, 803, 790, 818][i], z: [-26, -28, -38, -44, -42][i], yaw: Math.PI / 2 + [0.2, -0.3, 0.1, 0.4, -0.2][i], row: false }));
    } else { defenders.forEach((d) => poseChar(d, t, { visible: false })); shipsE.forEach((g) => (g.visible = false)); }
    return shot;
  }

  function render(t) { update(t); renderer.render(scene, camera); }
  return { render, dispose: () => renderer.dispose() };
}
