"""Global configuration for the Zack-style studio (original cinematic 3D shorts)."""
import os
ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
DURATION = 30.0
TOTAL_FRAMES = int(DURATION * FPS)
RENDER_SCALE = 1.0            # software renderer internal scale (1.0 = native 1080x1920)
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
TTS_VOICE = "rms"             # ffmpeg-flite voice: awb, kal, kal16, rms, slt  (swap for Piper/ElevenLabs/Azure here)
SAMPLE_RATE = 44100
DIRS = {k: os.path.join(ROOT, k) for k in ("renders", "output", "scenes")}
DIRS["sfx"] = os.path.join(ROOT, "assets", "sound_effects")
DIRS["music"] = os.path.join(ROOT, "assets", "music")
for d in DIRS.values():
    os.makedirs(d, exist_ok=True)
BLENDER_BIN = os.environ.get("BLENDER_BIN", "blender")
