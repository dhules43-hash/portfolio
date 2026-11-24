"""Shot frames (renders/shots/shNN/####.png) -> upscale 1080x1920 + grade + ref-style captions + mixed audio -> output/forssmann_ref_style.mp4"""
import os, sys, subprocess, glob, json, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..")); sys.path.insert(0, HERE)
from config import W, H, FPS, DIRS, ROOT
import subtitles_ref as subs
from shots import SHOTS, nfr

DUR = json.load(open(os.path.join(DIRS["output"], "timeline.json")))["duration"]


def mix(out):
    o = DIRS["output"]
    fc = ("[0:a]asplit=2[v][vs];[1:a]volume=0.55[m];[m][vs]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=300[md];"
          f"[2:a]volume=0.75[sx];[v][md][sx]amix=inputs=3:normalize=0:duration=longest,loudnorm=I=-14:TP=-1.5:LRA=8,atrim=0:{DUR}[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{o}/voiceover.wav", "-i", f"{o}/music.wav", "-i", f"{o}/sfx.wav", "-filter_complex", fc, "-map", "[a]", "-ar", "44100", out], check=True)


def frames():
    out = []
    for i in range(1, len(SHOTS) + 1):
        n = nfr(i); fs = sorted(glob.glob(os.path.join(ROOT, "renders", "shots", f"sh{i:02d}", "*.png")))
        fs = [f for f in fs if os.path.getsize(f) > 1000]
        if not fs: raise SystemExit(f"shot {i} has no frames")
        if len(fs) < n: print(f"WARNING shot {i}: {len(fs)}/{n}"); fs += [fs[-1]] * (n - len(fs))
        out += fs[:n]
    return out


def grade(img, rng):
    img = cv2.resize(img, (W, H), interpolation=cv2.INTER_LANCZOS4)
    blur = cv2.GaussianBlur(img, (0, 0), 1.5); img = cv2.addWeighted(img, 1.4, blur, -.4, 0)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32); hsv[:, :, 1] *= 1.12; img = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR)
    g = rng.normal(0, 2.6, (H // 2, W // 2)).astype(np.float32); g = cv2.resize(g, (W, H))[:, :, None]
    return np.clip(img.astype(np.float32) + g, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    fs = frames(); print("frames", len(fs), "duration", DUR)
    audio = os.path.join(DIRS["output"], "mix_ref.wav"); mix(audio); chunks = subs.load()
    final = os.path.join(DIRS["output"], "forssmann_ref_style.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio,
                            "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k",
                            "-shortest", "-movflags", "+faststart", final], stdin=subprocess.PIPE)
    rng = np.random.default_rng(1)
    for i, f in enumerate(fs): enc.stdin.write(subs.overlay(grade(cv2.imread(f), rng), i / FPS, chunks).tobytes())
    enc.stdin.close(); enc.wait(); print(final)
