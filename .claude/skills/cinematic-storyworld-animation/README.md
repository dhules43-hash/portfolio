# Claude Skill — Cinematic Storyworld Animation v2

## Install
1. Unzip this package.
2. Copy the `historical-map-animation` folder into your Claude skills directory, or upload the folder contents as a project/skill.
3. Start a new Claude task and provide a script, narration audio, topic, or reference video.
4. Tell Claude to use the `Cinematic Storyworld` profile. The old map-first look is now optional under `Historical Map Animation (Legacy)`.

## Package contents
- `references/1000051211.mp4` — the actual uploaded reference video, included for Claude to inspect.
- `SKILL.md` — updated main instructions; cinematic storyworld is the default.
- `references/style_sheet.md` — analysis of the newly uploaded reference.
- `references/cinematic_prompt_templates.md` — character, environment, image-to-video, storyboard and thumbnail prompts.
- `references/uploaded_video_analysis.md` — measured properties and visible observations.
- `references/legacy_map_style.md` and `legacy_map_prompt_templates.md` — preserves the original map style.
- `scripts/engine_25d.py` and `scripts/foley_mixer.py` — original helper scripts retained, not represented as a complete renderer.
- `assets/scene_config_example.json` — updated scene planning example.

## Important
The included Python scripts are retained from the original skill. They are not a complete 3D animation engine. Complex 3D character motion should be generated with Blender or a suitable image/video model; Python/FFmpeg can handle compositing, subtitles, timing, audio mixing and final encoding.
