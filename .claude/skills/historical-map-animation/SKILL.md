---
name: historical-map-animation
description: 'Create vertical 9:16 2.5D historical map animation videos synced to a user voiceover (.mp3) using a physical multi-layer architecture: clean 3D shaded topographic relief map plates (day & night), 2.5D ground-level dioramas, chroma-keyed RGBA chibi peg-doll characters, vessels, physical props (iron chains, timber planks, 3D barrels, cargo crates, reed bundles, watchtowers, camp banners, alpha-composited flames & embers), articulated stick-arm prop interactions, smooth S-curve camera tracking, auto-fit subtitles, and sparse one-shot foley SFX—strictly free of neon route lines. Follows a 4-stage workflow: (1) 10 viral title ideas, (2) timed voiceover script & scene-by-scene storyboard, (3) clean map plate & green-screen sprite generation, and (4) 30 FPS multi-layer video rendering with visual QA.'
---

# Historical Map Animation (Physical 2.5D All-in-One Skill)

## Summary

Produce vertical (`9:16`, `720x1280`, `30 FPS`) 2.5D historical map animation shorts synced to a user-provided voiceover (`.mp3`) using a strict 5-layer physical compositing architecture—**with zero colored neon route lines**:

1. **Layer 0 (Clean 3D Relief Map & 2.5D Diorama Plates)**: High-detail 3D shaded topographic relief maps (`900x1600` overscan) in matching day and moonlit-night lighting with warm parchment-tan terrain (`#B59F78`), terracotta cliffs, snow-capped peaks (`#F4F7FA`), slate-teal rivers/oceans (`#4B7282`), and subtle flat translucent territory tints—plus 2.5D ground-level deck/camp dioramas. Strictly empty plates with zero baked-in characters, ships, or text.
2. **Layer 1 (Atmospheric Water, Wind & Classic Map Labels)**: Subtle drifting water-crest ripples, translucent wind-gust ribbons, and classic bold italic serif map labels (`DejaVuSerif-BoldItalic.ttf`) with crisp drop shadows.
3. **Layer 2 (Tangible 2.5D Physical Props & Constructions)**: All narrative action is shown through physical objects rather than abstract lines—sequentially locking iron chain links (`draw_iron_chain`), timber plank bridges (`draw_timber_plank_bridge`), 3D wooden barrels (`draw_3d_wooden_barrel`), isometric cargo crates (`draw_3d_cargo_crate`), bundled reeds (`draw_reed_bundle`), wooden watchtowers, fluttering camp banners, flying parabolic scrolls, and alpha-composited translucent flame/ember clusters (`draw_flame_cluster`).
4. **Layer 3 (Articulated Cutout Sprites & Stick-Arm Rigging)**: Chroma-keyed RGBA cutout sprites (characters, warships, fire-boats, escape skiffs, campaign easels) extracted from `#00FF00` green-screen plates via HSV masking + green-spill suppression (`extract_green_screen_sprite`), animated with `spring_pop` scale pop-ins (`0.0 -> 1.16 -> 0.96 -> 1.0`), `parabolic_hop` arcs, `walk_bob` cycles, seasick green face tints, thin black stick-arms with white-gloved hands holding props (`pointer`, `sword`, `spear`, `jug`, `log`, `scroll`, `torch`), dynamic eyebrows (`neutral`, `angry`, `shocked`), and 8-frame directional motion-blur head-tilt snaps.
5. **Layer 4 (Continuous S-Curve Camera, Auto-Fit Subtitles & Sparse One-Shot Foley)**: Smooth `smootherstep` virtual camera tracking (`900x1600 -> 720x1280`) with optional deck-pitch roll and impact shake, lower-third 2–4 word captions that auto-shrink to preserve side margins, and sparse, unique one-shot procedural foley accents mixed gently under foreground narration (no repetitive per-scene audio loops).

## Mandatory 4-Stage Execution Workflow

### Stage 1: Present 10 Viral Title & Cold-Open Hook Ideas (If No Topic Is Provided)

If the user has not yet chosen a historical topic, present **10 viral historical map animation concepts** (`60–180s` format). For each concept, include:
* **Title**: High-curiosity title.
* **Cold-Open Hook (00:00–00:10)**: The sharpest geographic or strategic twist.
* **Visual Map & Sprite Gag**: The signature physical 2.5D construction, vessel choreography, or stick-arm prop gag (never neon route lines).

If the user already provided a topic, skip Stage 1 and move directly to Stage 2.

### Stage 2: Deliver the Timed Voiceover Script & Scene-by-Scene Storyboard

Write:
1. A **Timed Voiceover Script** (`00:00–02:15`, ~320–350 words) plus a clean copy-ready version when requested so the user can record or generate their `.mp3`.
2. A **Scene-by-Scene Multi-Layer Storyboard Table** (`10–14 scenes`) specifying for each scene:
   * Timestamp & voiceover beat
   * Layer 0 clean background plate (reusing 3–4 plates with continuous camera pans so geography stays connected)
   * Layer 1 & 2 physical 2.5D props, constructions, and serif map labels
   * Layer 3 cutout sprite choreography and stick-arm prop gags
   * Layer 4 S-curve camera trajectory and sparse one-shot foley cue

**Wait for the user's `.mp3` voiceover file** (or explicit approval) before running Stages 3 and 4 so every scene transition, action beat, subtitle, and foley hit syncs to the exact audio timestamps.

### Stage 3: Generate Clean 3D Map Plates & Isolated `#00FF00` Cutout Sprites

#### A. Clean 3D Topographic Relief Map Plate (`aspect_ratio="9:16"`)
```
Vertical 9:16 top-down 3D shaded topographic relief map of [GEOGRAPHIC_REGION], rendered in the exact style of a clean historical strategy map background plate. High-detail 3D mountain ridges, valleys, and coastlines with warm parchment-tan and olive-green terrain (#B59F78), snow-capped peaks (#F4F7FA), and slate-teal ocean and river waters (#4B7282). [OPTIONAL_TERRITORY_TINT: e.g., Subtle flat translucent dark-slate territory tint over the north and muted crimson-gold tint over the south with clean dark ink coastline borders]. Strictly an empty environment background plate only: NO characters, NO people, NO soldiers, NO animals, NO ships, NO text labels, NO UI, NO watermarks.
```

#### B. Clean Night/Twilight 3D Relief Map Plate (`aspect_ratio="9:16"`)
```
Vertical 9:16 top-down 3D shaded topographic relief map of [GEOGRAPHIC_REGION] at night under cool silver-blue moonlight, rendered in the exact style of a clean historical strategy map background plate. High-detail 3D terrain with moonlit dark-parchment land, deep navy-teal river/ocean waters, and dramatic shaded cliffs. Strictly an empty environment background plate only: NO characters, NO people, NO soldiers, NO animals, NO ships, NO text labels, NO UI, NO watermarks.
```

#### C. Clean 2.5D Ground-Level Diorama Plate (`aspect_ratio="9:16"`)
```
Vertical 9:16 2.5D ground-level historical environment background plate of [ENVIRONMENT_DESCRIPTION, e.g., the wide wooden plank deck of an ancient river warship]. Shallow depth-of-field misty background cliffs/terrain with a clear, well-lit foreground ground/deck plane where 2D cutout characters will stand. Warm historical cel-shaded illustration lighting. Strictly an empty environment background plate only: NO characters, NO people, NO soldiers, NO animals, NO text, NO watermarks.
```

#### D. Isolated `#00FF00` Chibi Peg-Doll Character Sprite (`aspect_ratio="1:1"`)
```
1:1 square isolated 2D vector cartoon character sprite on a solid, flat, uniform pure neon green (#00FF00) chroma-key background. Cute 2D chibi peg-doll historical character with a bell-shaped legless pawn body (smooth flat-bottomed pawn base, NO legs or feet), 1:2 head-to-body ratio, large round head, two solid black dot eyes, no nose, simple clean line mouth, bold dark-brown/black ink outlines, and soft cel-shading: [COSTUME_AND_HELMET_DETAILS]. Armless pawn torso so procedural stick-arms can be attached cleanly. Centered full-body cutout, NO drop shadow on background, NO text, NO green on the character costume.
```

#### E. Isolated `#00FF00` Vessel & Prop Sprites (`aspect_ratio="1:1"`)
```
1:1 square isolated 2D vector cartoon sprite on a solid, flat, uniform pure neon green (#00FF00) background. 2D cel-shaded [VESSEL_OR_PROP_DESCRIPTION, e.g., ancient wooden river warship / covered fire-boat / escape rowboat skiff / wooden A-frame campaign easel] in side-3/4 view with bold black ink outlines. Centered, NO water waves attached, NO shadow, NO text, NO green on the object.
```

### Stage 4: Multi-Layer 2.5D Compositing & Sparse One-Shot Foley Engine (`Python 3`)

Measure the uploaded `.mp3` duration with `ffprobe`, extract all `#00FF00` sprites to RGBA PNGs, synthesize sparse one-shot foley cues mixed gently under the narration, pipe `30 FPS` `720x1280` RGB24 frames into `ffmpeg` (`libx264 -preset fast -crf 20 -pix_fmt yuv420p`, AAC 192k, `-movflags +faststart`), and export 5–7 QA keyframes across major scenes for visual verification before delivery.

#### Core Verified Engine Helpers
```python
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

W, H = 720, 1280
OV_W, OV_H = 900, 1600
FPS = 30
SR = 44100


def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def smootherstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def spring_pop(t: float, dur: float = 0.38) -> float:
    if t <= 0.0:
        return 0.0
    u = t / dur
    if u >= 1.0:
        return 1.0
    if u < 0.55:
        return 1.16 * smoothstep(u / 0.55)
    elif u < 0.82:
        return 1.16 - 0.20 * smoothstep((u - 0.55) / 0.27)
    return 0.96 + 0.04 * smoothstep((u - 0.82) / 0.18)


def parabolic_hop(t: float, t0: float, t1: float, p0: tuple, p1: tuple, hop_height: float = 48.0):
    if t <= t0:
        return p0[0], p0[1], 0.0, 0.0
    if t >= t1:
        return p1[0], p1[1], 0.0, 0.0
    u = smootherstep((t - t0) / max(1e-4, t1 - t0))
    x = p0[0] + (p1[0] - p0[0]) * u
    y_linear = p0[1] + (p1[1] - p0[1]) * u
    lift = math.sin(u * math.pi) * hop_height
    tilt = math.sin(u * math.pi * 2.0) * 8.5
    return x, y_linear - lift, lift, tilt


def extract_green_screen_sprite(img_path: str, out_png_path: str, target_max_dim: int = 420) -> Image.Image:
    bgr = cv2.imread(img_path)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    green_mask = cv2.inRange(hsv, np.array([32, 65, 65]), np.array([90, 255, 255]))
    fg_mask = cv2.bitwise_not(green_mask)
    fg_mask[:8, :] = fg_mask[-8:, :] = fg_mask[:, :8] = fg_mask[:, -8:] = 0

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=1)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    fg_mask = cv2.erode(fg_mask, np.ones((3, 3), np.uint8), iterations=1)
    alpha = cv2.GaussianBlur(fg_mask, (3, 3), 0)

    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    spill = np.maximum(0.0, g - np.maximum(r, b))
    rgb[:, :, 1] = g - spill * 0.80
    rgba = np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), alpha])

    ys, xs = np.where(alpha > 20)
    if len(xs) > 0 and len(ys) > 0:
        h, w = fg_mask.shape
        rgba = rgba[max(0, int(ys.min()) - 4):min(h, int(ys.max()) + 5),
                    max(0, int(xs.min()) - 4):min(w, int(xs.max()) + 5)]

    pil_sp = Image.fromarray(rgba, mode="RGBA")
    if max(pil_sp.size) > target_max_dim:
        sc = target_max_dim / float(max(pil_sp.size))
        pil_sp = pil_sp.resize((max(8, int(pil_sp.size[0] * sc)), max(8, int(pil_sp.size[1] * sc))), Image.Resampling.LANCZOS)
    pil_sp.save(out_png_path)
    return pil_sp


def draw_flame_cluster(canvas_pil: Image.Image, cx: float, cy: float, t: float, intensity: float = 1.0, seed: int = 0):
    """Alpha-composited soft fire glow + animated tongues + rising embers (never overwrites canvas alpha)."""
    if intensity <= 0.02:
        return
    s = intensity
    pad = int(max(90, 115 * s))
    patch = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
    pd = ImageDraw.Draw(patch, "RGBA")
    pc = pad
    for mult, alpha_v in [(1.0, 26), (0.72, 42), (0.45, 65)]:
        gr = int(76 * s * mult * (0.94 + 0.06 * math.sin(t * 13.0 + seed)))
        pd.ellipse([pc - gr, pc - gr, pc + gr, pc + gr], fill=(255, 110, 20, int(alpha_v * min(1.0, s))))
    for k in range(5):
        ph = t * (10.0 + k * 2.1) + seed * 1.7 + k * 1.3
        ox = (k - 2) * 14 * s + math.sin(ph) * 5 * s
        fh = (44 + (k % 3) * 18) * s * (0.85 + 0.22 * abs(math.sin(ph)))
        fw = (15 + (k % 2) * 5) * s
        pd.polygon([
            (pc + ox - fw, pc + 8 * s),
            (pc + ox - fw * 0.6, pc - fh * 0.45),
            (pc + ox + math.sin(ph * 1.3) * 7 * s, pc - fh),
            (pc + ox + fw * 0.6, pc - fh * 0.45),
            (pc + ox + fw, pc + 8 * s),
        ], fill=(242, 82, 18, int(225 * min(1.0, s))))
        pd.polygon([
            (pc + ox - fw * 0.48, pc + 5 * s),
            (pc + ox + math.sin(ph * 1.3) * 4 * s, pc - fh * 0.62),
            (pc + ox + fw * 0.48, pc + 5 * s),
        ], fill=(255, 226, 92, int(240 * min(1.0, s))))
    for e in range(5):
        ep = (t * 1.1 + seed * 0.23 + e * 0.21) % 1.0
        ex = pc + math.sin(ep * 6.0 + e * 2.0 + seed) * 28 * s - ep * 20 * s
        ey = pc - 18 * s - ep * (pad - 12)
        er = max(2, int((1.0 - ep) * 4.5 * s))
        pd.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(255, 210, 85, int((1.0 - ep) * 230)))
    canvas_pil.alpha_composite(patch, (int(cx - pad), int(cy - pad)))
```

## Critical Gotchas & Visual QA Checklist

* **Zero Neon Route Lines**: Depict every march, siege, naval crossing, or supply chain using tangible 2.5D objects (ships, iron chains, timber planks, barrels, crates, banners, watchtowers, flames) and connected camera pans across shared map plates.
* **Translucent Effects Require `alpha_composite`**: Never draw semi-transparent glows directly onto an `RGBA` canvas with `ImageDraw.Draw(canvas, "RGBA")` (Pillow overwrites alpha instead of blending). Always render translucent glows onto a transparent patch and apply `canvas.alpha_composite(patch, (x, y))`.
* **Outward-Raised Stick-Arm Angles**: Keep raised/cheering/shocked stick-arm angles between `-45°` and `-68°` (where `cos(ang) > 0` and `sin(ang) < 0`) so arms extend cleanly outward and upward instead of crossing inward over the character's face.
* **Auto-Fit Lower-Third Subtitles**: Measure text width with `draw.textbbox()` and automatically step down font size (`34pt -> 28pt`) whenever `tw > W - 56` so captions never clip at screen edges.
* **Clean FFmpeg Pipe Shutdown (Python 3.11+)**: Close `proc.stdin.close()`, read `proc.stderr.read()`, and call `proc.wait()` instead of `proc.communicate()` after closing `stdin`.
* **Sparse One-Shot Foley Only**: Keep foreground narration crystal clear (`0 dB`) and trigger unique, brief one-shot foley accents (`0.20–0.28` gain) only on major visual hits—never loop repetitive ambient SFX per scene.
* **Mandatory Keyframe QA**: Save 5–7 representative frames during rendering and inspect them visually for alpha halos, arm collisions, label clipping, and subtitle padding before delivering the `.mp4`.
