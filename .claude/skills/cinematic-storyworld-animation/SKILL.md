---
name: cinematic-storyworld-animation
description: Create vertical cinematic 3D story animations with expressive hybrid 2D/3D characters, richly detailed environments, dramatic camera work, fast visual beats, word-synced subtitles, narration, and synchronized sound design. Supports historical-map sequences as an optional secondary mode.
allowed-tools: image_gen default_api google
---

# Cinematic Storyworld Animation

## Attached visual reference asset

The package includes `references/1000051211.mp4`. Treat this exact video as the primary visual reference whenever the user asks to reproduce or continue this style. Inspect the actual video (not only the written analysis) before planning shots: sample frames from beginning, middle and end; inspect pacing, shot composition, character appearance, environment design, lighting, transitions and caption treatment. Use `references/uploaded_video_analysis.md` as a companion observation note, not as a replacement for the video. Do not copy the reference's exact sequence, characters, dialogue or assets; create original scenes that preserve its broad visual language.

## Primary visual target

Use the uploaded reference video as the primary style target: a polished, stylized 3D medieval/fantasy story world with simple graphic-faced characters integrated into dimensional 3D environments. The target is NOT the old map-first format.

Default output:
- Vertical 9:16, 720x1280 or 1080x1920, 30 FPS.
- Stylized cinematic 3D environments: throne rooms, castles, villages, courtyards, forests, prisons, battlefields, roads, interiors and ruined cities.
- Hybrid character design: simple high-contrast round faces and minimal facial features, combined with dimensional clothing, props, shadows and scene lighting.
- Strong shot variety: establishing wides, medium character shots, close-ups, extreme close-ups, overheads and dramatic low angles.
- Visual beat every 1–3 seconds, while longer shots may continue if the camera or action changes.
- Narration-led storytelling with readable word-by-word or short-phrase captions.
- Cinematic lighting, atmospheric depth, environmental effects and carefully synchronized sound effects.

The reference video is approximately 65 seconds, 720x1280, 30 FPS. It moves through castle interiors, a throne room, large creature/dragon details, a crowded castle/courtyard, village exteriors, sunset gardens, moonlit scenes, a prison, destruction, overhead architecture and landscape/map-like imagery. Do not invent the story or identify the characters from visual appearance alone.

## Style profiles

### Profile A — Cinematic Storyworld (DEFAULT)
Use for the newly supplied reference video.
- Full 3D stylized environments with cinematic composition.
- Main character has a simple pale/white round face, minimal black eyes and mouth, expressive brows where appropriate, and a clearly readable silhouette.
- Clothing and body are dimensional, with believable folds, material response and contact shadows.
- Supporting characters use the same simplified face language but vary in costume, scale and silhouette.
- Large creatures, statues, armor, furniture and architecture should have detailed 3D forms.
- Warm torchlit interiors, golden sunset exteriors, cool moonlit nights and dramatic orange destruction lighting.
- Depth from foreground/midground/background separation, atmospheric haze, volumetric light and depth of field used selectively.
- Keep the character recognizable across all scenes; do not randomly change head shape, eye spacing, costume, colors or body proportions.

### Profile B — Historical Map Animation (LEGACY / OPTIONAL)
Use only when the user explicitly asks for map-led history visuals or a map sequence is essential.
- 3D shaded relief maps, parchment terrain, territory overlays, route lines, ships and chibi peg-doll characters.
- Keep the original palette and map-specific prompt templates in `references/legacy_map_style.md`.
- Map scenes may be inserted into a Profile A story as a short explanatory sequence, but should not dominate unless requested.

## Workflow

### Step 1 — Inspect source material and determine the story
1. If a video is supplied, inspect its full duration and sample frames across the beginning, middle and end. Describe only visible style and actions; do not infer unsupported plot details.
2. If narration/audio is supplied, measure duration with ffprobe and transcribe or use the supplied script.
3. If only a topic is supplied, research factual claims and draft a script appropriate to the requested duration.
4. Establish the intended audience, language, aspect ratio and target duration. Ask only for essential missing information.
5. Build a story outline with hook, setup, escalation, turning point and payoff.

### Step 2 — Create a continuity bible
Before generating scenes, define:
- Main character: front/side/three-quarter views, face, body proportions, costume, colors and signature props.
- Supporting cast: matching design language and distinct silhouettes.
- Environment bible: architecture, materials, palette, era, geography and recurring landmarks.
- Lighting bible: time-of-day and emotional lighting progression.
- Prop bible: important objects with consistent scale and design.
- Negative constraints: no unwanted text, logos, watermarks, extra limbs, face drift, costume drift or inconsistent props.

Create character turnaround/reference images first. Reuse the references for all shots. Do not rely on text prompts alone for continuity.

### Step 3 — Storyboard and visual beat map
1. Divide the narration into scenes based on meaning, not arbitrary equal durations.
2. Plan a visual change every 1–3 seconds: action, camera move, reaction, insert shot, lighting change, prop reveal or environment transition.
3. Use a mixture of:
   - Establishing wide shot
   - Medium character shot
   - Close-up / extreme close-up
   - Over-the-shoulder
   - Low-angle hero/villain shot
   - High-angle / overhead shot
   - Tracking shot
   - Insert shot of a key prop
4. Each shot must communicate one clear idea.
5. Include timecode, narration phrase, shot size, camera movement, character action, environment, lighting, transition, subtitle text and sound cue.
6. Avoid repeating the same camera angle for consecutive shots unless repetition is an intentional gag.

### Step 4 — Generate scene visuals
Use `references/cinematic_prompt_templates.md`.
- Generate a clean keyframe for every shot or clip.
- Maintain consistent character references and environment continuity.
- Prefer image-to-video animation for motion when available; otherwise animate layered elements in Python.
- Use 9:16 framing and keep important faces/props inside mobile-safe margins.
- Do not bake subtitles into generated images. Add captions during editing.
- Do not ask image models to render exact written text, labels, dates or numbers; add those in post-production.
- For 10-second generative clips, write a self-contained prompt with one continuous camera/action idea. For longer sequences, split into connected clips and specify matching start/end composition.

### Step 5 — Animate and edit
Use the Python engine as a compositor, not as a substitute for a full 3D animation package.
- Create parallax from foreground, character, prop and background layers where useful.
- Use smooth ease-in/ease-out camera moves, push-ins, pull-backs, pans, tilts and controlled handheld shake.
- Add character motion only when supported by source assets: bounce, turn, gesture, recoil, point, walk-cycle approximation or reaction.
- Use animated 3D/video source clips for complex motion such as creature movement, running, fighting, cloth simulation or complex interactions.
- Use particles and environmental motion sparingly: dust, smoke, embers, rain, snow, sparks, leaves and light shafts.
- Use match cuts, whip pans, foreground wipes, hard cuts and motivated dissolves. Do not use a transition on every shot.
- Keep motion readable; avoid excessive camera shake and unnecessary zooms.

### Step 6 — Captions and narration
- Use high-contrast white text with a thick dark outline/shadow, centered in the lower safe area, matching the reference.
- Default caption mode: word-by-word highlighting or short phrase chunks (2–5 words) synchronized to speech. Choose one consistent mode per video.
- Keep captions away from faces and key actions; adjust vertical position when necessary.
- Preserve exact narration wording. Do not paraphrase unless asked.
- Use natural human-like narration with expressive pacing. Avoid robotic delivery.
- Duck music and effects under speech; maintain clear dialogue intelligibility.

### Step 7 — Sound design
- Use scene-specific Foley: footsteps, armor, doors, cloth, impacts, fire, wind, creature sounds, crowd ambience, metal, stone, wood, water and cinematic transitions.
- Add low-level ambience only when it supports the location.
- Place transient sounds on visible actions and cuts.
- Avoid repetitive synthetic beeps, constant whooshes or random effects.
- Use licensed, original, public-domain or user-provided audio only. Do not imply procedural effects are realistic recordings.
- Mix and limit the final audio; check clipping and speech clarity.

### Step 8 — Quality control and delivery
Render and inspect the actual MP4. Check:
- Correct duration, 9:16 aspect ratio, frame rate and codec.
- Character identity/costume consistency.
- No broken anatomy, flicker, duplicated objects or unintended text.
- No empty frames, black gaps or frozen shots unless intentional.
- Camera movement and scene changes align with narration.
- Captions are accurate, readable and synchronized.
- Sound effects align with actions; narration remains clear.
- No copyrighted music or unlicensed assets.
Deliver:
1. Final MP4.
2. Script with timecodes.
3. Shot-by-shot storyboard.
4. Character and environment reference prompts.
5. Sound-effects cue sheet.
6. Thumbnail prompt and YouTube title/description/tags if requested.

## Important implementation notes
- `scripts/engine_25d.py` contains helper functions for 2.5D compositing and camera transforms. It is not a complete video production application and does not generate 3D scenes by itself.
- `scripts/foley_mixer.py` contains procedural sound design helpers. Generated effects are synthetic and must be auditioned.
- Use FFmpeg for frame/audio muxing and final encoding.
- For true 3D geometry, rigging, character animation and complex physics, use Blender or a suitable image/video generation system. Do not claim the current OpenCV compositor performs full 3D animation.
- Verify every function name against the actual Python source before calling it. If a requested sound function is missing, either implement it or choose an existing one.
- Do not fabricate historical details. Separate verified facts from creative dramatization.
