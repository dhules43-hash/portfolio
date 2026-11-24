# Style bible — "explainer 3D short" (from reference analysis)

Reference studied: *Why Soldiers Put Grenades In Glass Cups* — 26.6 s, 720×1280 (9:16), 29.97 fps,
stereo 44.1 kHz, integrated loudness −14.1 LUFS.

## 1. Beat-by-beat breakdown of the reference

| Time | Shot | Camera | Narration (caption chunk) |
|---|---|---|---|
| 0.0–0.9 | Soldier holds grenade + glass up to the lens | low angle, wide lens, blue sky | "It's put into" |
| 0.9–2.7 | Hands drop grenade into a glass on a table | **top-down macro**, hands fill frame | "a glass cup" |
| 2.7–3.5 | Fingers pull the pin | extreme close-up, shallow DOF | "before the / pin is pulled" |
| 3.5–6.2 | Glass walls **glow lime green** around the lever | macro, slow push along the object | "And the walls / would hold / the lever / in place / preventing it" |
| 6.5–8.3 | Grenade-in-glass, soldier blurred behind | low table-level, deep foreground | "from blowing up / Now some say" |
| 8.5–9.0 | Grenade texture | extreme macro | "this was invented" |
| 9.0–11.0 | Two soldiers pass the glass | medium two-shot, interior set | "by Soviet soldiers" |
| 11.0–12.5 | Soldier at a door | over-the-shoulder | "who would place / the glass" |
| 12.5–14.5 | Hand places glass on top of door | **POV hand**, close | "on top / of a slightly / open door" |
| 14.5–15.0 | Glass balanced on door edge | macro | "Whenever" |
| 15.0–17.0 | Enemies approach outside window | through-window, mid-wide | "enemy soldiers / tried to go in" |
| 17.0–18.5 | Door opens, glass tips | close, low | "the glass / would tip over" |
| 18.5–21.5 | **Slow-motion** glass shatter, lever flies | floor-level macro, hero object centred | "instantly / shattering / and releasing / the lever" |
| 22.0–23.0 | Fuze smoke; enemy walks past | floor-level, feet in background | "This would light / the fuze / and turn" |
| 23.5–25.0 | Exterior night, soldiers run out | wide, low | "a simple grenade / into a booby trap" |
| 25.0–26.5 | Explosion → enemy ragdolled on ground | wide → ground close-up | (payoff, no new info) |

## 2. Rules distilled

**Structure**
- Frame 1 already shows the strange thing (hook). No title card, no intro.
- Order: *what it is → how it works (mechanism, highlighted) → origin ("Now some say…") → demonstration → payoff/consequence*.
- 60–75 words in ~25–30 s (≈2.6–3 words/s). Narration is nearly continuous (pauses < 0.3 s).

**Editing**
- 18–20 shots per 26 s → average **1.3–1.6 s per shot**; never hold a shot longer than ~2.5 s.
- Cut on caption chunk boundaries. Camera is *always* moving (slow push / drift / track) + slight handheld.
- Payoff uses slow motion and debris/particles.

**Camera language**
- Macro on the key object with hands interacting (top-down or 3/4 down).
- Ground/table-level low angles with a hero object in the foreground and characters out of focus behind.
- Wide lenses (16–24 mm) placed close to the subject; very shallow depth of field (f/1.6–2.8).
- POV hand shots for actions.

**Look**
- Bright, saturated, sunny; cyan/blue skies and teal/blue interiors with warm skin and yellow/orange hero objects.
- Glossy materials, strong specular highlights, soft contact shadows.
- **Lime-green translucent glow** highlights the exact part being explained (pulses gently).
- Light film grain; no heavy vignette; no letterbox.

**Captions**
- Small (≈ 4.5 % of frame width per cap-height), white, **sentence case exactly as spoken**, thin dark outline + soft drop shadow.
- 2–3 words per chunk, centred at ~78 % frame height, swaps on speech — no karaoke colouring, no pop animation, no emojis.

**Audio**
- One calm, fast, conversational male narrator, close-mic'd, compressed, upfront.
- Quiet cinematic music bed ducked under the voice; foley for every on-screen action (clinks, slides, footsteps, door, shatter, explosion); whooshes on some cuts.
- Master to −14 LUFS, true peak ≤ −1.5 dB.

## 3. What this pipeline can and cannot match
- Matches: pacing, shot grammar, camera moves, DOF, lime highlights, caption style, narration density, sound design, loudness.
- Cannot fully match: the reference's photoreal scanned characters, cloth and hands (MetaHuman / Unreal-class assets).
  Procedural characters here are stylised. To close the gap, drop rigged realistic characters (.blend/.glb) into the scene
  and parent props/cameras the same way the shot functions do.
- Three.js is not used: it is a real-time web renderer without path tracing, physically based depth of field or offline
  sub-surface skin. Blender Cycles is the right tool for this look.
