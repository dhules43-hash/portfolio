"""Reference-style captions: small clean white sentence-case text, soft drop shadow + thin outline,
2-3 word chunks timed to speech, lower third (~78% height), no colour highlighting, no pop."""
import json, os, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import W, H, DIRS

FONT = os.environ.get("CAP_FONT", "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
FS = int(os.environ.get("CAP_SIZE", 58)); Y = .775
_f = None; _cache = {}


def load(path=None, max_words=3):
    words = json.load(open(path or os.path.join(DIRS["output"], "word_timings.json")))
    FUNC = {"a", "the", "his", "into", "had", "to", "of", "in", "and", "own", "he", "it", "was", "by", "near", "until", "with", "right"}
    # split into clauses at punctuation, then into 2-3 word chunks that never end on a function word or strand one word
    clauses, cur = [], []
    for w in words:
        cur.append(w)
        if w["word"][-1] in ".,:;!?": clauses.append(cur); cur = []
    if cur: clauses.append(cur)
    chunks = []
    for cl in clauses:                       # DP: chunks of 2-3 words, penalise 1/4-word chunks and dangling function words
        n = len(cl); best = [0.] + [1e9] * n; prev = [0] * (n + 1)
        for j in range(1, n + 1):
            for k in range(1, 5):
                if j - k < 0: continue
                c = {1: 0 if n == 1 else 8, 2: 0, 3: .2, 4: 3}[k] + (5 if cl[j - 1]["word"].lower().strip(".,:;") in FUNC and j < n else 0)
                if best[j - k] + c < best[j]: best[j] = best[j - k] + c; prev[j] = j - k
        cuts = []; j = n
        while j > 0: cuts.append((prev[j], j)); j = prev[j]
        chunks += [cl[a:b] for a, b in reversed(cuts)]
    out = []
    for i, c in enumerate(chunks):
        end = chunks[i + 1][0]["start"] if i + 1 < len(chunks) else c[-1]["end"] + .3
        out.append(dict(text=" ".join(x["word"] for x in c).rstrip(".,:;"), start=c[0]["start"] - .03, end=end - .03))
    return out


def sprite(txt):
    global _f
    if txt in _cache: return _cache[txt]
    _f = _f or ImageFont.truetype(FONT, FS)
    w = int(_f.getlength(txt)) + 60; h = FS + 50
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
    d.text((32, 27), txt, font=_f, fill=(0, 0, 0, 200)); sh = sh.filter(ImageFilter.GaussianBlur(5))
    d = ImageDraw.Draw(sh)
    d.text((30, 22), txt, font=_f, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 150))
    a = np.array(sh); _cache[txt] = a; return a


def overlay(frame, t, chunks):
    for c in chunks:
        if c["start"] <= t < c["end"]:
            sp = sprite(c["text"]); h, w, _ = sp.shape
            x0 = (W - w) // 2; y0 = int(H * Y - h / 2)
            al = sp[:, :, 3:4] / 255.0
            roi = frame[y0:y0 + h, x0:x0 + w].astype(np.float32)
            frame[y0:y0 + h, x0:x0 + w] = (roi * (1 - al) + sp[:, :, 2::-1] * al).astype(np.uint8)
            break
    return frame
