# Reference look: bright cartoon-history shorts

Use this when the user asks for the "reference" look (round white-headed stick people in a bright 3D world with big word captions). It replaces the matching parts of the house style in SKILL.md; everything else in SKILL.md still applies.

- Ink: near-black `#1b1416` for every character outline (thicker than the house style).
- Characters: large white round head with a soft crescent shade, strong angled brows, half-lidded eyes or dot eyes, simple mouths (smirk, gritted teeth, O). Small pear torso in saturated period clothing, thin black stick limbs, dark disc hands. Hats carry the identity (turban, helmet with plume, cap, headband with curly hair).
- Expressions per beat: smug, angry (gritted teeth, mouth flaps when talking), shock (round eyes, O mouth), sleep (closed arcs).
- World: bright saturated toon-shaded 3D, blue sky with painted clouds, green grass tufts, grey brick stone, blue water with painted ripples. No outlines on the 3D world.
- Captions: one or two spoken words at a time, white heavy sans (Inter Black) with a thick black stroke and a short drop shadow, centred at about 62% of frame height, pop-in scale. Never cover a face.
- A visual joke on the conflict line (a prop the commander pulls out on the punch word).
- Starter project: `video/` in this repo (Remotion + plain three.js): `src/art.js` (canvas painting of heads, bodies, oxen, signs, textures), `src/world.js` (terrain, locations, galleys, camera plan), `src/Video.jsx` (captions, dips).
- Stills: `npx remotion still ... --scale=0.25 --gl=swangle --browser-executable=<chromium headless shell>` take about 5 s each here.
