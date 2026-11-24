import React, { useLayoutEffect, useRef, useState, useEffect } from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, delayRender, continueRender, staticFile } from 'remotion';
import { createWorld } from './world.js';
import { WORDS, DIPS } from './words.js';

// Group words into short caption chunks (1-2 words), like punchy shorts captions.
const CHUNKS = (() => {
  const out = [];
  for (let i = 0; i < WORDS.length; i++) {
    let [w, s, e] = WORDS[i];
    const clean = (x) => x.replace(/[.,]/g, '');
    let text = clean(w);
    if (text.length <= 3 && i + 1 < WORDS.length && clean(WORDS[i + 1][0]).length <= 9 && WORDS[i + 1][1] - e < 250) { text += ' ' + clean(WORDS[i + 1][0]); e = WORDS[i + 1][2]; i++; }
    out.push({ text, s: s / 1000, e: e / 1000 });
  }
  out.forEach((c, i) => { const next = out[i + 1]; c.end = next ? Math.min(next.s, c.e + 0.6) : c.e + 0.6; });
  return out;
})();

const Captions = ({ t }) => {
  const c = CHUNKS.find((k) => t >= k.s - 0.03 && t < k.end);
  if (!c) return null;
  const k = Math.min(1, (t - c.s + 0.03) / 0.1);
  const scale = 0.82 + 0.18 * (1 - Math.pow(1 - k, 3)) + (k >= 1 ? 0 : 0.04 * Math.sin(k * Math.PI));
  return (
    <div style={{ position: 'absolute', left: 0, right: 0, top: '62.5%', display: 'flex', justifyContent: 'center' }}>
      <div style={{
        fontFamily: 'InterBlack', fontSize: 118, color: '#ffffff', letterSpacing: -1,
        WebkitTextStroke: '15px #111', paintOrder: 'stroke fill', transform: `scale(${scale})`,
        textShadow: '0 8px 0 rgba(0,0,0,0.35)', lineHeight: 1, whiteSpace: 'nowrap',
      }}>{c.text}</div>
    </div>
  );
};

export const Video = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;
  const canvasRef = useRef(null), worldRef = useRef(null);
  const [fontHandle] = useState(() => delayRender('font'));
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const f = new FontFace('InterBlack', `url(${staticFile('Inter-Black.otf')})`);
    f.load().then((ff) => { document.fonts.add(ff); setReady(true); continueRender(fontHandle); });
  }, []);
  useLayoutEffect(() => {
    if (!ready) return;
    if (!worldRef.current) worldRef.current = createWorld(canvasRef.current, width, height);
    worldRef.current.render(t);
  }, [ready, frame]);
  let dip = 0;
  for (const d of DIPS) dip = Math.max(dip, 1 - Math.abs(t - d) / 0.2);
  // light vignette
  return (
    <AbsoluteFill style={{ backgroundColor: '#cfe6fa' }}>
      <canvas ref={canvasRef} width={width} height={height} style={{ width, height }} />
      <AbsoluteFill style={{ background: 'radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 60%, rgba(30,20,30,0.28) 100%)' }} />
      {ready && <Captions t={t} />}
      <AbsoluteFill style={{ backgroundColor: '#f4ead5', opacity: Math.max(0, dip) }} />
    </AbsoluteFill>
  );
};
