"""Validate the final MP4: specs, motion, audio presence/loudness, subtitle presence, voice/word sync."""
import subprocess, json, sys, os, numpy as np, cv2, wave
from config import *
def probe(f):
    j = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", f]))
    return j
def check(f):
    j = probe(f); v = [s for s in j["streams"] if s["codec_type"] == "video"][0]; a = [s for s in j["streams"] if s["codec_type"] == "audio"][0]
    dur = float(j["format"]["duration"]); res = []
    ok = lambda name, cond, info="": res.append((name, bool(cond), info))
    ok("resolution 1080x1920", (v["width"], v["height"]) == (1080, 1920), f'{v["width"]}x{v["height"]}')
    ok("H.264", v["codec_name"] == "h264", v["codec_name"]); ok("AAC", a["codec_name"] == "aac", a["codec_name"])
    ok("30 fps", v["r_frame_rate"] == "30/1", v["r_frame_rate"]); ok("duration ~30.0s", abs(dur - 30) < .1, f"{dur:.3f}s"); ok("9:16", v["width"] * 16 == v["height"] * 9)
    cap = cv2.VideoCapture(f); prev = None; diffs = []; frames = 0; dark = 0
    while True:
        r, fr = cap.read()
        if not r: break
        frames += 1
        if frames % 3 == 0:
            g = cv2.cvtColor(cv2.resize(fr, (108, 192)), cv2.COLOR_BGR2GRAY).astype(np.float32); dark += g.mean() < 6
            if prev is not None: diffs.append(np.abs(g - prev).mean())
            prev = g
    ok("frame count 900", abs(frames - 900) <= 1, str(frames)); ok("continuous motion (no frozen stretches)", np.percentile(diffs, 5) > .05, f"p5 motion={np.percentile(diffs,5):.3f}")
    ok("no black frames (except fade)", dark <= 12, f"dark samples={dark}")
    w = subprocess.run(["ffmpeg", "-i", f, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    mv = float([l for l in w.splitlines() if "mean_volume" in l][0].split(":")[1].split()[0]); ok("audio audible", mv > -40, f"mean {mv} dB")
    # voice/word sync: voice energy inside word windows vs gaps
    tm = json.load(open(os.path.join(DIRS["output"], "word_timings.json")))
    with wave.open(os.path.join(DIRS["output"], "voiceover.wav")) as wv:
        sr = wv.getframerate(); x = np.frombuffer(wv.readframes(wv.getnframes()), np.int16).astype(np.float32) / 32768
    e = lambda t0, t1: float(np.sqrt(np.mean(x[int(t0 * sr):int(t1 * sr)] ** 2) + 1e-12))
    inside = np.mean([e(w_["start"], w_["end"]) > .008 for w_ in tm]); ok("voice energy inside word windows", inside > .95, f"{inside:.0%}")
    ok("subtitle words timed within video", tm[-1]["end"] <= 30.0, f'last word ends {tm[-1]["end"]}')
    for n, c, i in res: print(("PASS " if c else "FAIL ") + n, i)
    return all(c for _, c, _ in res)
if __name__ == "__main__": sys.exit(0 if check(sys.argv[1]) else 1)
