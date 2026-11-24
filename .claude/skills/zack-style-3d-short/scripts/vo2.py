"""Reference-style narration: dense, conversational, sentence-level neural TTS (Kokoro), tight pauses,
word timings estimated per sentence (syllable-weighted), music-bed-friendly. Writes output/voiceover.wav + word_timings.json."""
import os, json, re, numpy as np, subprocess
import soundfile as sf
from config import SAMPLE_RATE, DIRS, ROOT

SENTENCES = [
    "In 1929, a young doctor slid a tube into his own heart.",
    "His boss had forbidden it.",
    "So he numbed his arm, opened a vein near the elbow, and pushed a thin catheter inside.",
    "Inch by inch, it travelled up his arm, past his shoulder, until the tip reached his heart.",
    "Then, with the tube still inside him, he walked to the X-ray room to prove it.",
    "The image showed the catheter sitting right inside his heart.",
    "His boss was furious.",
    "But in 1956, the stunt earned him a Nobel Prize.",
]
SPOKEN = {"1929": "nineteen twenty-nine", "1956": "nineteen fifty-six"}
GAP = .16


def syl(w):
    w = re.sub(r"[^a-z]", "", w.lower()) or "a"
    n = len(re.findall(r"[aeiouy]+", w)); n -= 1 if w.endswith("e") and n > 1 else 0
    return max(1, n)


def tts(text, out):
    from kokoro_onnx import Kokoro
    d = os.environ.get("KOKORO_DIR", os.path.join(ROOT, "..", "models"))
    k = tts.k = getattr(tts, "k", None) or Kokoro(os.path.join(d, "kokoro-v1.0.onnx"), os.path.join(d, "voices-v1.0.bin"))
    s, sr = k.create(text, voice=os.environ.get("KOKORO_VOICE", "am_michael"), speed=float(os.environ.get("KOKORO_SPEED", "1.12")), lang="en-us")
    sf.write(out, s, sr)
    a, _ = sf.read(out)
    # trim leading/trailing silence
    e = np.abs(a) > .01; idx = np.nonzero(e)[0]
    a = a[max(0, idx[0] - 200): idx[-1] + 1200] if len(idx) else a
    return a, sr


def voiced_spans(a, sr, min_gap=.09):
    """Find internal pauses (for snapping word boundaries at commas)."""
    win = int(sr * .02); en = np.array([np.sqrt(np.mean(a[i:i + win] ** 2)) for i in range(0, len(a) - win, win)])
    quiet = en < .012; gaps = []; i = 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]: j += 1
            if (j - i) * .02 >= min_gap and i > 0 and j < len(quiet): gaps.append(((i * .02), (j * .02)))
            i = j
        else: i += 1
    return gaps


def build(lead=.15):
    work = os.path.join(ROOT, "scenes", "vo2"); os.makedirs(work, exist_ok=True)
    chunks = []; words = []; t = lead; sr0 = None
    for si, s in enumerate(SENTENCES):
        spoken = " ".join(SPOKEN.get(w.strip(".,"), w) for w in s.split())
        a, sr = tts(spoken, os.path.join(work, f"s{si}.wav")); sr0 = sr
        d = len(a) / sr
        toks = s.split(); wts = [sum(syl(x) for x in SPOKEN.get(w.strip(".,"), w).split()) + .35 for w in toks]
        # snap comma words to detected pauses
        gaps = voiced_spans(a, sr); comma_idx = [i for i, w in enumerate(toks[:-1]) if w.endswith(",")]
        bounds = []
        if len(gaps) >= len(comma_idx) and comma_idx:
            gaps = sorted(gaps, key=lambda g: g[1] - g[0], reverse=True)[:len(comma_idx)]; gaps.sort()
            seg_starts = [0] + [i + 1 for i in comma_idx]; seg_ends = comma_idx + [len(toks) - 1]
            times = [(0, gaps[0][0])] + [(gaps[k][1], gaps[k + 1][0]) for k in range(len(gaps) - 1)] + [(gaps[-1][1], d)]
            tw = sum(wts)
            ok = all(.45 < ((b1 - b0) / d) / (sum(wts[a0:a1 + 1]) / tw) < 2.2 for (a0, a1), (b0, b1) in zip(zip(seg_starts, seg_ends), times))
            if ok:
                for (a0, a1), (b0, b1) in zip(zip(seg_starts, seg_ends), times): bounds.append((a0, a1, b0, b1))
            else: bounds.append((0, len(toks) - 1, 0, d))
        else:
            bounds.append((0, len(toks) - 1, 0, d))
        for a0, a1, b0, b1 in bounds:
            tot = sum(wts[a0:a1 + 1]); c = b0
            for k in range(a0, a1 + 1):
                dd = (b1 - b0) * wts[k] / tot
                words.append(dict(word=toks[k], start=round(t + c, 3), end=round(t + c + dd, 3), scene=si + 1, phrase=si, ptext=s)); c += dd
        chunks.append((t, a)); t += d + GAP
    total = t - GAP + .55
    N = int(total * SAMPLE_RATE); track = np.zeros(N)
    for t0, a in chunks:
        x = np.interp(np.arange(int(len(a) * SAMPLE_RATE / sr0)) * sr0 / SAMPLE_RATE, np.arange(len(a)), a)
        i = int(t0 * SAMPLE_RATE); track[i:i + len(x)] += x[:N - i]
    raw = os.path.join(work, "vo_raw.wav"); sf.write(raw, np.clip(track, -1, 1), SAMPLE_RATE)
    final = os.path.join(DIRS["output"], "voiceover.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", "highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,equalizer=f=3500:t=q:w=1:g=2,volume=1.3",
                    "-ar", str(SAMPLE_RATE), final], check=True)
    json.dump(words, open(os.path.join(DIRS["output"], "word_timings.json"), "w"), indent=1)
    json.dump(dict(duration=round(total, 3)), open(os.path.join(DIRS["output"], "timeline.json"), "w"))
    return total, words


if __name__ == "__main__":
    total, w = build()
    print("duration", round(total, 2), "words", len(w))
    print(" ".join(f"{x['word']}@{x['start']:.2f}" for x in w))
