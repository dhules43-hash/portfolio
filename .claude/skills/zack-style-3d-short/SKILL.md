---
name: zack-style-3d-short
description: Make a fully 3D, fast-cut vertical explainer short (9:16, ~30 s) in the viral "3D explainer" style — macro and ground-level cameras, lime-green highlights on the mechanism, dense neural narration, small sentence-case captions, foley and music — rendered with Blender (bpy + Cycles, CPU) and finished with ffmpeg. Use when the user asks for a 3D animated short, a "Zack D Films style" video, a Blender explainer video, or wants an existing short restyled to match a reference.
---

# 3D explainer short (Blender pipeline)

Read `reference/style-bible.md` first: it has the beat-by-beat breakdown of the reference video and the rules
(pacing, camera, look, captions, audio) that every new video must follow.

## Setup (once per machine)
```bash
pip install -r scripts/requirements.txt          # bpy 5.3 = Blender as a Python module; no GPU needed
# Kokoro voice model files -> $KOKORO_DIR (default: <studio>/../models), URLs in requirements.txt
```
EEVEE needs a GPU/EGL; in headless containers use **Cycles CPU** (the scripts already do).

## Workflow
1. **Research + script** — pick a story with a strange hook and a visual mechanism. Verify facts. Write 6–9 short
   sentences, 60–90 words, in the order *hook → mechanism → origin/attempt → demonstration → payoff*.
   Put them in `scripts/vo2.py:SENTENCES` (`SPOKEN` maps numerals to spoken words).
2. **Voice** — `python3 vo2.py` → `output/voiceover.wav`, `word_timings.json`, `timeline.json` (duration).
   Voice: `KOKORO_VOICE=am_michael KOKORO_SPEED=1.12` (try `am_adam`, `bm_george`). Aim for 26–30 s.
3. **Shot list** — print the word times, then edit `scripts/b3d/shots.py:SHOTS` so every cut lands on a caption-chunk
   boundary, 1.0–2.2 s per shot, 16–20 shots. Write one `shotN()` per shot using the helpers below and the camera
   grammar from the style bible (top-down hands, macro + lime highlight, ground-level, POV, wide close lenses, f/1.6–2.8).
4. **Preview** — one low-res still per shot, fix framing before committing CPU time:
   `SAMPLES=8 RW=270 RH=480 python3 b3d/shots.py N stills <t_abs> /tmp/p`
5. **Render** — `b3d/run_shots.sh` (resumable; skips frames already on disk; detach with `setsid nohup`).
   540×960 @ 14 samples + OpenImageDenoise ≈ 8–12 s/frame on 4 CPU cores → plan ~2–3 h for 30 s.
6. **Sound** — edit event times in `scripts/sound2.py` (cuts, foley) then `python3 sound2.py`.
7. **Finish** — `python3 b3d/finalize2.py` → Lanczos upscale to 1080×1920, sharpen, saturation, grain,
   reference-style captions (`subtitles_ref.py`), voice-ducked mix at −14 LUFS → `output/*.mp4`.
8. **QC** — `python3 quality_checker.py output/<file>.mp4`; watch it; check every caption chunk reads naturally.

## Building blocks (`scripts/b3d/core.py`, `scenes.py`, `shots.py`)
- `reset(n)`, `Cam(fstop).shot(f0,f1,pos0,pos1,target0,target1,lens0,lens1)`, `cam.handheld(amount)`;
  consecutive shots in one camera = hard cut. `set_interp(obj,'LINEAR')` for tracking shots.
- `Character(...)`, presets `doctor()`, `boss()`: skin-modifier body + armature + face (eyes, lids, brows, mouth, hair).
  Posing: `pose(frame, uarm_R=(x,y,z), ...)` in degrees. Axes: −X on `uarm/farm` raises/bends forward; `head` X nods,
  Y turns, Z tilts; `thigh` −X forward; `shin` +X bends. Also `walk()`, `talk()`, `blink()`, `brows(mood)`, `mouth()`, `lids()`.
  `attach(obj, bone, rest_space=True)` to give props to hands.
- Materials: `mat()`, `skin_mat()`, `ghost_mat()` (x-ray body), `highlight_mat()` + `pulse()` (lime glow), wood/tile/checker.
- Sets: `office()`, `op_room()`, `corridor()`, `xray_room()`, `stage()`; props: `arm_prop`, `heart_model`, `xray_image`,
  `curve_tube` + `grow()` (things sliding in), `text()`.

## Hard-won gotchas
- Read `obj.matrix_world` only after `bpy.context.view_layer.update()` (else freshly scaled props come out huge).
- Bone-parent with `parent_to_bone()`/`attach()`; plain `parent` + `matrix_world` assignment misplaces props.
- Objects inside other opaque objects (catheter in vein) are invisible — make the outer one translucent.
- Eased camera keys lag walking characters; use LINEAR on tracking shots.
- Big emissive objects close to camera blow out to white; keep emission ≤ 10 near lens.
- Background jobs may be capped at 2 h: render detached and resumable (`use_overwrite=False`, placeholders).
