// Canvas painting: flat cartoon characters with thick ink outlines, signs and painted textures.
import * as THREE from 'three';

export const INK = '#1b1416';
export const FONT = 'InterBlack';

export function cv(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
export function tex(c, rep) {
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  if (rep) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rep[0], rep[1]); }
  return t;
}
export function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

// ---------------------------------------------------------------- heads
// canvas 400x400 = 1 world unit; head centre (200,250), radius 112
export function drawHead(o) {
  const c = cv(400, 400), g = c.getContext('2d');
  const cx = 200, cy = 250, r = 112, lx = (o.look || 0) * r * 0.12;
  g.lineJoin = 'round'; g.lineCap = 'round';
  // hair behind head
  if (o.hair) {
    g.fillStyle = o.hair; g.strokeStyle = INK; g.lineWidth = 9;
    const R = rng(7);
    for (let i = 0; i < 9; i++) {
      const a = Math.PI * (1.05 + i * 0.11), rr = r * (0.98 + R() * 0.06);
      g.beginPath(); g.arc(cx + Math.cos(a) * rr, cy + Math.sin(a) * rr, r * 0.26, 0, 7); g.fill(); g.stroke();
    }
  }
  // head
  g.fillStyle = o.skin || '#fbf7f2'; g.strokeStyle = INK; g.lineWidth = 11;
  g.beginPath(); g.ellipse(cx, cy, r, r * 0.97, 0, 0, 7); g.fill();
  g.save(); g.beginPath(); g.ellipse(cx, cy, r, r * 0.97, 0, 0, 7); g.clip();
  g.fillStyle = 'rgba(110,90,110,0.13)'; g.beginPath(); g.rect(0, 0, 400, 400); g.ellipse(cx - 20, cy - 22, r, r, 0, 0, 7); g.fill('evenodd');
  if (o.hair) { // fringe
    g.fillStyle = o.hair; const R = rng(3);
    for (let i = 0; i < 7; i++) { g.beginPath(); g.arc(cx - r * 0.75 + i * r * 0.25, cy - r * 0.86 + R() * 8, r * 0.2, 0, 7); g.fill(); }
  }
  g.restore();
  g.beginPath(); g.ellipse(cx, cy, r, r * 0.97, 0, 0, 7); g.stroke();
  if (o.hair && o.band) { // headband
    g.fillStyle = o.band; g.lineWidth = 7;
    g.beginPath(); g.moveTo(cx - r * 0.95, cy - r * 0.42); g.quadraticCurveTo(cx, cy - r * 0.62, cx + r * 0.95, cy - r * 0.42);
    g.lineTo(cx + r * 0.97, cy - r * 0.24); g.quadraticCurveTo(cx, cy - r * 0.44, cx - r * 0.97, cy - r * 0.24); g.closePath(); g.fill(); g.stroke();
    g.beginPath(); g.moveTo(cx + r * 0.95, cy - r * 0.35); g.lineTo(cx + r * 1.32, cy - r * 0.15); g.lineTo(cx + r * 1.22, cy - r * 0.02); g.lineTo(cx + r * 0.96, cy - r * 0.26); g.fill(); g.stroke();
  }
  // beard
  if (o.beard) {
    g.fillStyle = o.beard; g.lineWidth = 8;
    g.beginPath(); g.moveTo(cx - r * 0.84, cy + r * 0.12);
    g.quadraticCurveTo(cx - r * 0.7, cy + r * 1.05, cx, cy + r * 1.28);
    g.quadraticCurveTo(cx + r * 0.7, cy + r * 1.05, cx + r * 0.84, cy + r * 0.12);
    g.quadraticCurveTo(cx + r * 0.45, cy + r * 0.62, cx + r * 0.12, cy + r * 0.5);
    g.quadraticCurveTo(cx, cy + r * 0.62, cx - r * 0.12, cy + r * 0.5);
    g.quadraticCurveTo(cx - r * 0.45, cy + r * 0.62, cx - r * 0.84, cy + r * 0.12);
    g.closePath(); g.fill(); g.stroke();
  }
  // hats
  if (o.hat === 'turban') {
    g.lineWidth = 9;
    g.fillStyle = '#c8322f'; g.beginPath(); g.ellipse(cx, cy - r * 1.42, r * 0.38, r * 0.26, 0, Math.PI, 0); g.lineTo(cx + r * 0.38, cy - r * 1.3); g.lineTo(cx - r * 0.38, cy - r * 1.3); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = '#fffaf0'; g.beginPath(); g.ellipse(cx, cy - r * 0.9, r * 1.08, r * 0.55, 0, 0, 7); g.fill(); g.stroke();
    g.strokeStyle = '#d3c8b2'; g.lineWidth = 6;
    for (let i = 0; i < 4; i++) { g.beginPath(); g.moveTo(cx - r * 0.95 + i * r * 0.32, cy - r * 0.62); g.quadraticCurveTo(cx - r * 0.55 + i * r * 0.36, cy - r * 1.05, cx - r * 0.2 + i * r * 0.36, cy - r * 1.38); g.stroke(); }
    g.strokeStyle = INK; g.lineWidth = 9; g.beginPath(); g.ellipse(cx, cy - r * 0.9, r * 1.08, r * 0.55, 0, 0, 7); g.stroke();
    // plume + jewel
    g.fillStyle = '#f4f1ea'; g.lineWidth = 6;
    g.beginPath(); g.moveTo(cx + r * 0.05, cy - r * 1.05); g.quadraticCurveTo(cx + r * 0.55, cy - r * 1.6, cx + r * 0.75, cy - r * 1.95); g.quadraticCurveTo(cx + r * 0.2, cy - r * 1.7, cx - r * 0.1, cy - r * 1.1); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = '#e2b33c'; g.beginPath(); g.arc(cx, cy - r * 0.95, r * 0.17, 0, 7); g.fill(); g.stroke();
    g.fillStyle = '#2aa36d'; g.beginPath(); g.arc(cx, cy - r * 0.95, r * 0.09, 0, 7); g.fill();
  } else if (o.hat === 'helmet') {
    g.lineWidth = 10;
    // horse-tail plume
    g.fillStyle = '#d23a3a';
    g.beginPath(); g.moveTo(cx, cy - r * 1.28); g.quadraticCurveTo(cx + r * 1.1, cy - r * 1.45, cx + r * 1.28, cy - r * 0.35); g.quadraticCurveTo(cx + r * 0.85, cy - r * 1.05, cx, cy - r * 1.1); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = '#c9ced6';
    g.beginPath(); g.moveTo(cx - r * 1.05, cy - r * 0.32); g.bezierCurveTo(cx - r * 1.0, cy - r * 1.35, cx + r * 1.0, cy - r * 1.35, cx + r * 1.05, cy - r * 0.32); g.closePath(); g.fill(); g.stroke();
    g.strokeStyle = '#f5f7fa'; g.lineWidth = 9; g.beginPath(); g.moveTo(cx - r * 0.6, cy - r * 0.55); g.quadraticCurveTo(cx - r * 0.5, cy - r * 0.95, cx - r * 0.1, cy - r * 1.02); g.stroke();
    g.strokeStyle = INK; g.lineWidth = 8; g.fillStyle = '#d9a93a';
    g.beginPath(); g.moveTo(cx - r * 1.1, cy - r * 0.42); g.quadraticCurveTo(cx, cy - r * 0.55, cx + r * 1.1, cy - r * 0.42); g.lineTo(cx + r * 1.1, cy - r * 0.24); g.quadraticCurveTo(cx, cy - r * 0.37, cx - r * 1.1, cy - r * 0.24); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = INK; for (let i = 0; i < 9; i++) { const x = cx - r * 0.9 + i * r * 0.225; g.beginPath(); g.arc(x, cy - r * 0.37 - Math.cos((x - cx) / r) * r * 0.06, 4, 0, 7); g.fill(); }
    g.fillStyle = '#d9a93a'; g.beginPath(); g.moveTo(cx - r * 0.1, cy - r * 1.08); g.lineTo(cx, cy - r * 1.45); g.lineTo(cx + r * 0.1, cy - r * 1.08); g.closePath(); g.fill(); g.stroke();
  } else if (o.hat === 'byz') {
    g.lineWidth = 10; g.fillStyle = '#8f99a6';
    g.beginPath(); g.moveTo(cx - r * 1.03, cy - r * 0.3); g.bezierCurveTo(cx - r * 1.0, cy - r * 1.3, cx + r * 1.0, cy - r * 1.3, cx + r * 1.03, cy - r * 0.3); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = '#3b5fae'; g.beginPath(); g.moveTo(cx - r * 0.12, cy - r * 1.02); g.quadraticCurveTo(cx, cy - r * 1.45, cx + r * 0.5, cy - r * 1.35); g.quadraticCurveTo(cx + r * 0.2, cy - r * 1.15, cx + r * 0.12, cy - r * 1.02); g.closePath(); g.fill(); g.stroke();
    g.strokeStyle = INK; g.lineWidth = 7; g.beginPath(); g.moveTo(cx, cy - r * 1.03); g.lineTo(cx, cy - r * 0.32); g.stroke();
    g.fillStyle = '#c9a54a'; g.beginPath(); g.rect(cx - r * 1.06, cy - r * 0.42, r * 2.12, r * 0.16); g.fill(); g.stroke();
  } else if (o.hat === 'cap') {
    g.lineWidth = 9; g.fillStyle = o.capColor || '#b0402f';
    g.beginPath(); g.moveTo(cx - r * 0.85, cy - r * 0.45); g.bezierCurveTo(cx - r * 0.8, cy - r * 1.4, cx + r * 0.8, cy - r * 1.4, cx + r * 0.85, cy - r * 0.45); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = '#f1e7cf'; g.beginPath(); g.ellipse(cx, cy - r * 0.48, r * 0.95, r * 0.16, 0, 0, 7); g.fill(); g.stroke();
  }
  // face
  const e = o.expr || 'smug', eyL = cx - r * 0.34 + lx, eyR = cx + r * 0.34 + lx, ey = cy - r * 0.02;
  g.strokeStyle = INK; g.fillStyle = INK;
  const brow = (x0, y0, x1, y1, w = 13) => { g.lineWidth = w; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke(); };
  if (e === 'smug') {
    brow(eyL - r * 0.22, ey - r * 0.3, eyL + r * 0.17, ey - r * 0.24); brow(eyR - r * 0.17, ey - r * 0.26, eyR + r * 0.22, ey - r * 0.33);
    for (const x of [eyL, eyR]) { g.lineWidth = 9; g.beginPath(); g.moveTo(x - r * 0.17, ey - r * 0.04); g.lineTo(x + r * 0.17, ey - r * 0.05); g.stroke(); g.beginPath(); g.ellipse(x + r * 0.05, ey - r * 0.045, r * 0.11, r * 0.1, 0, 0, Math.PI); g.fill(); }
  } else if (e === 'angry') {
    brow(eyL - r * 0.24, ey - r * 0.4, eyL + r * 0.16, ey - r * 0.2, 15); brow(eyR - r * 0.16, ey - r * 0.2, eyR + r * 0.24, ey - r * 0.4, 15);
    for (const x of [eyL, eyR]) { g.beginPath(); g.ellipse(x + r * 0.02, ey + r * 0.02, r * 0.075, r * 0.09, 0, 0, 7); g.fill(); }
  } else if (e === 'shock') {
    for (const [x, s] of [[eyL, -1], [eyR, 1]]) { g.lineWidth = 11; g.beginPath(); g.arc(x, ey - r * 0.42, r * 0.2, Math.PI * (s < 0 ? 1.15 : 1.25), Math.PI * (s < 0 ? 1.75 : 1.85)); g.stroke(); }
    for (const x of [eyL, eyR]) { g.lineWidth = 7; g.fillStyle = '#ffffff'; g.beginPath(); g.arc(x, ey, r * 0.15, 0, 7); g.fill(); g.stroke(); g.fillStyle = INK; g.beginPath(); g.arc(x + lx * 0.3, ey + r * 0.01, r * 0.06, 0, 7); g.fill(); }
  } else if (e === 'sleep') {
    brow(eyL - r * 0.2, ey - r * 0.22, eyL + r * 0.16, ey - r * 0.22, 10); brow(eyR - r * 0.16, ey - r * 0.22, eyR + r * 0.2, ey - r * 0.22, 10);
    for (const x of [eyL, eyR]) { g.lineWidth = 9; g.beginPath(); g.moveTo(x - r * 0.15, ey); g.quadraticCurveTo(x, ey + r * 0.1, x + r * 0.15, ey); g.stroke(); }
  } else { // calm
    brow(eyL - r * 0.2, ey - r * 0.27, eyL + r * 0.16, ey - r * 0.27, 11); brow(eyR - r * 0.16, ey - r * 0.27, eyR + r * 0.2, ey - r * 0.27, 11);
    for (const x of [eyL, eyR]) { g.beginPath(); g.ellipse(x + lx * 0.2, ey, r * 0.06, r * 0.08, 0, 0, 7); g.fill(); }
  }
  if (o.moustache) {
    g.fillStyle = '#3a2620'; g.lineWidth = 6;
    for (const s of [-1, 1]) { g.beginPath(); g.moveTo(cx + lx, cy + r * 0.27); g.quadraticCurveTo(cx + lx + s * r * 0.3, cy + r * 0.2, cx + lx + s * r * 0.5, cy + r * 0.38); g.quadraticCurveTo(cx + lx + s * r * 0.28, cy + r * 0.36, cx + lx, cy + r * 0.36); g.closePath(); g.fill(); g.stroke(); }
  }
  // mouth
  const m = o.mouth || 'closed', my = cy + r * 0.48, mx = cx + lx;
  g.strokeStyle = INK; g.lineWidth = 8;
  if (e === 'angry') {
    const h = m === 'open' ? r * 0.3 : r * 0.2, w = r * 0.62;
    g.fillStyle = m === 'open' ? '#3a1a1e' : '#ffffff';
    g.beginPath(); g.roundRect(mx - w / 2, my - h / 2, w, h, r * 0.08); g.fill();
    if (m === 'open') { g.fillStyle = '#ffffff'; g.fillRect(mx - w / 2, my - h / 2, w, h * 0.33); }
    g.lineWidth = 4; for (let i = 1; i < 6; i++) { const x = mx - w / 2 + (w * i) / 6; g.beginPath(); g.moveTo(x, my - h / 2); g.lineTo(x, m === 'open' ? my - h / 2 + h * 0.33 : my + h / 2); g.stroke(); }
    if (m !== 'open') { g.beginPath(); g.moveTo(mx - w / 2, my); g.lineTo(mx + w / 2, my); g.stroke(); }
    g.lineWidth = 8; g.beginPath(); g.roundRect(mx - w / 2, my - h / 2, w, h, r * 0.08); g.stroke();
  } else if (e === 'shock') {
    g.fillStyle = '#3a1a1e'; g.beginPath(); g.ellipse(mx, my + r * 0.04, r * 0.13, r * 0.17, 0, 0, 7); g.fill(); g.stroke();
  } else if (m === 'open') {
    g.fillStyle = '#3a1a1e'; g.beginPath(); g.moveTo(mx - r * 0.18, my - r * 0.04); g.quadraticCurveTo(mx, my + r * 0.3, mx + r * 0.18, my - r * 0.04); g.closePath(); g.fill(); g.stroke();
  } else if (e === 'sleep') {
    g.fillStyle = '#3a1a1e'; g.beginPath(); g.ellipse(mx, my, r * 0.06, r * 0.07, 0, 0, 7); g.fill();
  } else {
    g.beginPath(); g.moveTo(mx - r * 0.14, my - r * 0.02); g.quadraticCurveTo(mx + r * 0.03, my + r * 0.08, mx + r * 0.2, my - r * 0.08); g.stroke();
  }
  return c;
}

// ---------------------------------------------------------------- bodies
// canvas 400x400 = 1 unit. Neck at y=62, torso bottom at y=300 (or 372 with skirt)
export function drawBody(o) {
  const c = cv(400, 400), g = c.getContext('2d'); const cx = 200;
  g.lineJoin = 'round'; g.lineCap = 'round';
  const bot = o.skirt ? 372 : 300, wb = o.skirt ? 116 : 102;
  const path = () => { g.beginPath(); g.moveTo(cx - 58, 62); g.bezierCurveTo(cx - 92, 120, cx - 120, 220, cx - wb, bot - 14); g.quadraticCurveTo(cx, bot + 22, cx + wb, bot - 14); g.bezierCurveTo(cx + 120, 220, cx + 92, 120, cx + 58, 62); g.closePath(); };
  g.fillStyle = o.main; path(); g.fill();
  g.save(); path(); g.clip();
  if (o.skirtColor) { g.fillStyle = o.skirtColor; g.fillRect(0, bot - 62, 400, 120); g.strokeStyle = INK; g.lineWidth = 6; g.beginPath(); g.moveTo(0, bot - 62); g.lineTo(400, bot - 62); g.stroke(); }
  if (o.pattern === 'studs') {
    for (let y = 105; y < bot - 70; y += 26) for (let x = cx - 110; x < cx + 120; x += 26) {
      g.fillStyle = '#f2dc8a'; g.beginPath(); g.arc(x + ((y / 26) % 2) * 13, y, 7, 0, 7); g.fill(); g.fillStyle = INK; g.beginPath(); g.arc(x + ((y / 26) % 2) * 13, y, 2.6, 0, 7); g.fill();
    }
  }
  if (o.pattern === 'stripes') { g.fillStyle = 'rgba(255,255,255,0.18)'; for (let x = 0; x < 400; x += 44) g.fillRect(x, 0, 18, 400); }
  // wear and shading
  g.fillStyle = 'rgba(40,20,40,0.16)'; g.beginPath(); g.rect(0, 0, 400, 400); g.ellipse(cx - 30, 170, 150, 230, 0, 0, 7); g.fill('evenodd');
  if (o.trim) { g.fillStyle = o.trim; g.fillRect(cx - 9, 70, 18, bot); g.strokeStyle = INK; g.lineWidth = 4; g.strokeRect(cx - 9, 70, 18, bot); }
  if (o.belt) { g.fillStyle = o.belt; g.fillRect(0, 196, 400, 26); g.strokeStyle = INK; g.lineWidth = 6; g.strokeRect(-10, 196, 420, 26); g.fillStyle = '#e2b33c'; g.fillRect(cx - 16, 194, 32, 30); g.strokeRect(cx - 16, 194, 32, 30); }
  if (o.pocket) { g.fillStyle = o.pocket; g.fillRect(cx + 30, 130, 44, 40); g.strokeStyle = INK; g.lineWidth = 5; g.strokeRect(cx + 30, 130, 44, 40); }
  g.restore();
  // collar
  g.fillStyle = o.collar || '#f6efe0'; g.strokeStyle = INK; g.lineWidth = 7;
  g.beginPath(); g.moveTo(cx - 52, 62); g.lineTo(cx, 116); g.lineTo(cx + 52, 62); g.closePath(); g.fill(); g.stroke();
  g.lineWidth = 11; path(); g.stroke();
  return c;
}

// ---------------------------------------------------------------- ox (side view, facing +x)
export function drawOx() {
  const c = cv(640, 400), g = c.getContext('2d'); g.lineJoin = 'round'; g.lineCap = 'round'; g.strokeStyle = INK;
  // tail
  g.lineWidth = 9; g.beginPath(); g.moveTo(120, 150); g.quadraticCurveTo(70, 190, 86, 270); g.stroke();
  g.fillStyle = '#5a3a24'; g.beginPath(); g.ellipse(88, 276, 14, 22, 0, 0, 7); g.fill(); g.lineWidth = 6; g.stroke();
  // body
  g.lineWidth = 11; g.fillStyle = '#9a6238';
  g.beginPath(); g.roundRect(112, 118, 360, 170, 80); g.fill();
  g.save(); g.beginPath(); g.roundRect(112, 118, 360, 170, 80); g.clip();
  g.fillStyle = '#e9d3b4'; g.beginPath(); g.ellipse(300, 300, 160, 50, 0, 0, 7); g.fill();
  g.fillStyle = 'rgba(40,20,20,0.18)'; g.beginPath(); g.rect(0, 0, 640, 400); g.ellipse(270, 170, 210, 120, 0, 0, 7); g.fill('evenodd');
  g.restore(); g.beginPath(); g.roundRect(112, 118, 360, 170, 80); g.stroke();
  // yoke
  g.fillStyle = '#7a4a26'; g.lineWidth = 8; g.beginPath(); g.roundRect(420, 96, 40, 60, 10); g.fill(); g.stroke();
  // head
  g.fillStyle = '#9a6238'; g.lineWidth = 11;
  g.beginPath(); g.ellipse(520, 168, 74, 66, 0.2, 0, 7); g.fill(); g.stroke();
  // horns
  g.fillStyle = '#f3ead2'; g.lineWidth = 8;
  g.beginPath(); g.moveTo(488, 118); g.quadraticCurveTo(470, 60, 520, 40); g.quadraticCurveTo(500, 80, 516, 112); g.closePath(); g.fill(); g.stroke();
  g.beginPath(); g.moveTo(540, 112); g.quadraticCurveTo(580, 64, 620, 70); g.quadraticCurveTo(586, 90, 566, 124); g.closePath(); g.fill(); g.stroke();
  // ear
  g.fillStyle = '#7d4c2a'; g.beginPath(); g.ellipse(470, 140, 26, 14, -0.4, 0, 7); g.fill(); g.stroke();
  // muzzle
  g.fillStyle = '#e8c9a8'; g.beginPath(); g.ellipse(570, 200, 46, 36, 0.2, 0, 7); g.fill(); g.stroke();
  g.fillStyle = INK; g.beginPath(); g.ellipse(585, 196, 6, 8, 0, 0, 7); g.fill();
  // half-lidded eye
  g.lineWidth = 8; g.beginPath(); g.moveTo(512, 150); g.lineTo(546, 148); g.stroke();
  g.beginPath(); g.ellipse(532, 150, 11, 10, 0, 0, Math.PI); g.fill();
  return c;
}
export function drawOxLeg() {
  const c = cv(64, 256), g = c.getContext('2d'); g.lineJoin = 'round';
  g.fillStyle = '#8a5531'; g.strokeStyle = INK; g.lineWidth = 8;
  g.beginPath(); g.roundRect(12, 4, 40, 228, 14); g.fill(); g.stroke();
  g.fillStyle = '#2a1d18'; g.beginPath(); g.roundRect(8, 206, 48, 44, 10); g.fill(); g.stroke();
  return c;
}

// ---------------------------------------------------------------- props
export function drawPan() {
  const c = cv(256, 128), g = c.getContext('2d'); g.lineCap = 'round'; g.strokeStyle = INK;
  g.lineWidth = 16; g.beginPath(); g.moveTo(14, 64); g.lineTo(120, 64); g.stroke();
  g.strokeStyle = '#6b4a2e'; g.lineWidth = 9; g.beginPath(); g.moveTo(16, 64); g.lineTo(70, 64); g.stroke();
  g.fillStyle = '#2d2d33'; g.strokeStyle = INK; g.lineWidth = 9; g.beginPath(); g.ellipse(180, 64, 66, 54, 0, 0, 7); g.fill(); g.stroke();
  g.fillStyle = '#4a4a55'; g.beginPath(); g.ellipse(176, 58, 44, 34, 0, 0, 7); g.fill();
  g.strokeStyle = '#8e8e99'; g.lineWidth = 6; g.beginPath(); g.arc(176, 58, 30, 3.6, 4.6); g.stroke();
  return c;
}
export function drawStick(len, color, tip) {
  const c = cv(64, 512), g = c.getContext('2d'); g.lineCap = 'round';
  g.strokeStyle = INK; g.lineWidth = 16; g.beginPath(); g.moveTo(32, tip ? 60 : 12); g.lineTo(32, 500); g.stroke();
  g.strokeStyle = color; g.lineWidth = 8; g.beginPath(); g.moveTo(32, tip ? 62 : 14); g.lineTo(32, 498); g.stroke();
  if (tip === 'spear') { g.fillStyle = '#c9ced6'; g.strokeStyle = INK; g.lineWidth = 6; g.beginPath(); g.moveTo(32, 4); g.lineTo(50, 70); g.lineTo(14, 70); g.closePath(); g.fill(); g.stroke(); }
  if (tip === 'mop') { g.fillStyle = '#3b3025'; g.strokeStyle = INK; g.lineWidth = 6; g.beginPath(); g.ellipse(32, 470, 28, 40, 0, 0, 7); g.fill(); g.stroke(); }
  return c;
}

// ---------------------------------------------------------------- signs and painted textures
export function drawBoard(lines, opts = {}) {
  const w = opts.w || 1024, h = opts.h || 320, c = cv(w, h), g = c.getContext('2d');
  if (opts.cloth) {
    g.fillStyle = opts.bg || '#f3e6c4'; g.fillRect(0, 0, w, h);
    g.strokeStyle = opts.border || '#b8312f'; g.lineWidth = h * 0.09; g.strokeRect(h * 0.06, h * 0.06, w - h * 0.12, h - h * 0.12);
  } else {
    g.fillStyle = opts.bg || '#b88352'; g.fillRect(0, 0, w, h);
    const R = rng(11); g.strokeStyle = 'rgba(70,40,20,0.35)'; g.lineWidth = 4;
    for (let y = h / 4; y < h; y += h / 4) { g.beginPath(); g.moveTo(0, y + R() * 6); g.lineTo(w, y + R() * 6); g.stroke(); }
    for (let i = 0; i < 40; i++) { g.fillStyle = `rgba(60,30,15,${0.05 + R() * 0.12})`; g.beginPath(); g.ellipse(R() * w, R() * h, 6 + R() * 30, 3 + R() * 8, 0, 0, 7); g.fill(); }
    g.strokeStyle = '#5a3418'; g.lineWidth = 18; g.strokeRect(9, 9, w - 18, h - 18);
  }
  g.fillStyle = opts.color || '#2a1a14'; g.textAlign = 'center'; g.textBaseline = 'middle';
  const n = lines.length;
  lines.forEach((t, i) => { const fs = (opts.size || 0.55) * h / Math.max(1, n * 0.85); g.font = `${fs}px ${FONT}`; g.fillText(t, w / 2, h * (i + 0.5) / n + fs * 0.04); });
  if (opts.arrow) { g.fillStyle = '#2a1a14'; g.beginPath(); g.moveTo(w - 40, h / 2); g.lineTo(w - 130, h * 0.2); g.lineTo(w - 130, h * 0.8); g.closePath(); g.fill(); }
  return c;
}

export function stoneTex(seed = 1, base = '#a9aab0') {
  const c = cv(512, 512), g = c.getContext('2d'), R = rng(seed);
  g.fillStyle = '#6f6f78'; g.fillRect(0, 0, 512, 512);
  const bh = 64;
  for (let row = 0; row < 8; row++) {
    const off = row % 2 ? 64 : 0;
    for (let x = -off; x < 512; x += 128) {
      const v = 0.9 + R() * 0.18;
      const col = new THREE.Color(base).multiplyScalar(v);
      g.fillStyle = '#' + col.getHexString(); g.fillRect(x + 4, row * bh + 4, 120, bh - 8);
      g.fillStyle = 'rgba(255,255,255,0.12)'; g.fillRect(x + 4, row * bh + 4, 120, 8);
      if (R() < 0.3) { g.fillStyle = 'rgba(60,60,60,0.18)'; g.beginPath(); g.ellipse(x + 20 + R() * 80, row * bh + 20 + R() * 30, 8 + R() * 16, 4 + R() * 6, 0, 0, 7); g.fill(); }
    }
  }
  return c;
}
export function plankTex(base = '#8a5631', seed = 2, w = 512, h = 256, bands) {
  const c = cv(w, h), g = c.getContext('2d'), R = rng(seed);
  g.fillStyle = base; g.fillRect(0, 0, w, h);
  g.strokeStyle = 'rgba(50,25,10,0.45)'; g.lineWidth = 3;
  for (let y = 0; y < h; y += 16) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); for (let k = 0; k < 3; k++) { const x = R() * w; g.beginPath(); g.moveTo(x, y); g.lineTo(x, y + 16); g.stroke(); } }
  for (let i = 0; i < 60; i++) { g.fillStyle = `rgba(${R() < 0.5 ? '255,230,200' : '40,20,10'},${0.05 + R() * 0.1})`; g.beginPath(); g.ellipse(R() * w, R() * h, 4 + R() * 24, 2 + R() * 5, 0, 0, 7); g.fill(); }
  if (bands) {
    g.fillStyle = bands.color; g.fillRect(0, 0, w, h * bands.v); g.fillRect(0, h * (1 - bands.v), w, h * bands.v);
    g.fillStyle = '#e2b33c'; g.fillRect(0, h * bands.v - 5, w, 6); g.fillRect(0, h * (1 - bands.v) - 1, w, 6);
    g.fillStyle = '#2a1712'; for (let x = 30; x < w - 20; x += 50) { g.beginPath(); g.ellipse(x, h * bands.v * 0.55, 7, 5, 0, 0, 7); g.fill(); g.beginPath(); g.ellipse(x, h * (1 - bands.v * 0.55), 7, 5, 0, 0, 7); g.fill(); }
  }
  return c;
}
export function sailTex() {
  const c = cv(256, 256), g = c.getContext('2d'); g.fillStyle = '#f3ead6'; g.fillRect(0, 0, 256, 256);
  g.fillStyle = '#c4362f'; g.fillRect(0, 70, 256, 26); g.fillRect(0, 150, 256, 26);
  g.strokeStyle = 'rgba(120,90,60,0.35)'; g.lineWidth = 2; for (let x = 0; x < 256; x += 22) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, 256); g.stroke(); }
  return c;
}
export function stripeTex(a, b) {
  const c = cv(256, 64), g = c.getContext('2d'); for (let i = 0; i < 8; i++) { g.fillStyle = i % 2 ? a : b; g.fillRect(i * 32, 0, 32, 64); } return c;
}
export function waterTex() {
  const c = cv(512, 512), g = c.getContext('2d'), R = rng(5);
  g.fillStyle = '#3b92d4'; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 120; i++) {
    const x = R() * 512, y = R() * 512, w = 20 + R() * 60;
    g.strokeStyle = `rgba(${R() < 0.6 ? '150,210,245' : '40,110,180'},${0.35 + R() * 0.4})`; g.lineWidth = 3 + R() * 3; g.lineCap = 'round';
    for (const dx of [0, -512, 512]) for (const dy of [0, -512, 512]) { g.beginPath(); g.moveTo(x + dx, y + dy); g.quadraticCurveTo(x + dx + w / 2, y + dy - 6, x + dx + w, y + dy); g.stroke(); }
  }
  return c;
}
export function skyTex() {
  const c = cv(2048, 1024), g = c.getContext('2d'), R = rng(9);
  const gr = g.createLinearGradient(0, 0, 0, 1024);
  gr.addColorStop(0, '#2f7fd8'); gr.addColorStop(0.38, '#5fa6ea'); gr.addColorStop(0.5, '#cfe6fa'); gr.addColorStop(1, '#cfe6fa');
  g.fillStyle = gr; g.fillRect(0, 0, 2048, 1024);
  // painted puffy clouds near the horizon band
  for (let i = 0; i < 16; i++) {
    const x = R() * 2048, y = 400 + R() * 80, s = 18 + R() * 30;
    for (const dx of [0, -2048, 2048]) {
      for (let k = 0; k < 7; k++) {
        const px = x + dx + (k - 3) * s * 0.8, py = y - Math.sin((k / 6) * Math.PI) * s * 0.7;
        g.fillStyle = 'rgba(255,255,255,0.92)'; g.beginPath(); g.ellipse(px, py, s * (0.8 + R() * 0.4), s * (0.6 + R() * 0.3), 0, 0, 7); g.fill();
      }
      g.fillStyle = 'rgba(190,215,240,0.6)'; g.beginPath(); g.ellipse(x + dx, y + s * 0.35, s * 3, s * 0.3, 0, 0, 7); g.fill();
    }
  }
  return c;
}
