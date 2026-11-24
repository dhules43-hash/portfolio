"""Stage 4: multi-layer 2.5D compositing engine for 'The Chains That Burned an Empire' (Red Cliffs, 208 AD)."""
import math, json, os, sys, subprocess, wave
from functools import lru_cache
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")
W, H = 720, 1280
FPS = 30
SR = 44100
PS = 2  # plate supersample
FONT_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf"
FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
INK = (34, 24, 18)

# ------------------------------------------------------------------ easing (skill helpers)
def smoothstep(t):
    t = max(0.0, min(1.0, t)); return t * t * (3.0 - 2.0 * t)

def smootherstep(t):
    t = max(0.0, min(1.0, t)); return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

def spring_pop(t, dur=0.38):
    if t <= 0.0: return 0.0
    u = t / dur
    if u >= 1.0: return 1.0
    if u < 0.55: return 1.16 * smoothstep(u / 0.55)
    elif u < 0.82: return 1.16 - 0.20 * smoothstep((u - 0.55) / 0.27)
    return 0.96 + 0.04 * smoothstep((u - 0.82) / 0.18)

def parabolic_hop(t, t0, t1, p0, p1, hop_height=48.0):
    if t <= t0: return p0[0], p0[1], 0.0, 0.0
    if t >= t1: return p1[0], p1[1], 0.0, 0.0
    u = smootherstep((t - t0) / max(1e-4, t1 - t0))
    x = p0[0] + (p1[0] - p0[0]) * u
    y = p0[1] + (p1[1] - p0[1]) * u
    lift = math.sin(u * math.pi) * hop_height
    return x, y - lift, lift, math.sin(u * math.pi * 2.0) * 8.5

def walk_bob(t, speed=7.0, amp=4.0):
    return -abs(math.sin(t * speed)) * amp, math.sin(t * speed) * 4.0

def ramp(t, t0, t1):
    return smootherstep((t - t0) / max(1e-4, t1 - t0))

def lerp(a, b, u): return a + (b - a) * u

# ------------------------------------------------------------------ script + word timing
SCRIPT = [
    "In the winter of 208 AD, the most powerful warlord in China chained his entire navy together. And that one decision set the Yangtze River on fire.",
    "His name was Cao Cao. He had just conquered the north. Now, with a fleet carrying over two hundred thousand men, he sailed down the Yangtze to finish the job.",
    "Standing in his way were two underdogs. Liu Bei, a warlord with almost no land. And Sun Quan, the young ruler of the south. Together, they had maybe fifty thousand troops.",
    "But Cao Cao had a problem. His soldiers were northerners. They had never lived on water. The river rocked, the ships swayed, and his army got seasick. Then disease began spreading through the camps.",
    "So Cao Cao had an idea. He ordered his ships lashed together with iron chains and wooden planks. Suddenly, his fleet became a floating fortress. Steady. Stable. Soldiers could walk from ship to ship.",
    "Across the river, at a place called Red Cliffs, the southern commander Zhou Yu was watching. And his veteran general, Huang Gai, saw the flaw immediately. If the ships cannot move apart, they cannot escape a fire.",
    "So Huang Gai sent Cao Cao a letter. He said he wanted to switch sides, and would sail over with his ships. And Cao Cao believed him.",
    "Huang Gai prepared ten ships. He packed them with dry reeds and firewood, soaked everything in oil, and covered it with cloth. Behind each one, he tied a small escape boat.",
    "Then they waited for the wind. In winter, the wind here blows from the north. But one night, it turned. A strong southeast wind began to blow, straight toward Cao Cao's fleet.",
    "Huang Gai's ships sailed forward. Cao Cao's men lined the decks, pointing and cheering. Here come the defectors! Then, about a kilometer out, Huang Gai's crews set their ships on fire, and jumped into the escape boats.",
    "The burning ships slammed into the chained fleet. And the chains that made it strong now made it a trap. The fire leapt from deck to deck. Nothing could break free.",
    "Flames spread to the camps on shore. Smoke filled the sky. Cao Cao abandoned his fleet and fled north, through the mud and marshes. He would never conquer the south.",
    "China split into three kingdoms, and they would fight for the next sixty years. All because one man tried to stop his ships from rocking.",
]
TIM = json.load(open(os.path.join(HERE, "vo", "timing.json")))
CLIPS = TIM["scenes"]
TOTAL = TIM["total"]
NFRAMES = int(math.ceil(TOTAL * FPS))


def word_times(k):
    words = SCRIPT[k].split()
    wts = []
    for w in words:
        core = w.strip(",.!?'")
        wt = len(core) + 1.6
        pause = 0.0
        if w.endswith(","): pause = 4.0
        if w.endswith((".", "!", "?")): pause = 7.5
        wts.append((wt, pause))
    tot = sum(a + b for a, b in wts) - wts[-1][1]
    t0, t1 = CLIPS[k]
    out, acc = [], 0.0
    for (w, (wt, pause)) in zip(words, wts):
        s = t0 + (t1 - t0) * acc / tot
        acc += wt
        e = t0 + (t1 - t0) * acc / tot
        acc += pause
        out.append((w, s, e))
    return out

WT = [word_times(k) for k in range(len(SCRIPT))]


def wt(k, key, occ=0):
    n = 0
    for w, s, e in WT[k]:
        if key.lower() in w.lower():
            if n == occ: return s
            n += 1
    raise KeyError(key)


def caption_groups():
    groups = []
    for k in range(len(SCRIPT)):
        cur = []
        for i, (w, s, e) in enumerate(WT[k]):
            cur.append((w, s, e))
            if len(cur) >= 3 or w.endswith((",", ".", "!", "?")) and len(cur) >= 2 or i == len(WT[k]) - 1:
                groups.append([" ".join(x[0] for x in cur), cur[0][1], cur[-1][2]])
                cur = []
            elif w.endswith((".", "!", "?")) and len(cur) == 1 and i < len(WT[k]) - 1:
                pass
    for i in range(len(groups) - 1):  # hold until next caption (bridge tiny gaps)
        if groups[i + 1][1] - groups[i][2] < 0.6:
            groups[i][2] = groups[i + 1][1]
        else:
            groups[i][2] += 0.25
    return groups

CAPS = caption_groups()

# ------------------------------------------------------------------ assets
PLATES = {}

def plate(name):
    if name not in PLATES:
        PLATES[name] = cv2.cvtColor(cv2.imread(f"{A}/plate_{name}.png"), cv2.COLOR_BGR2RGB)
    return PLATES[name]

META = json.load(open(f"{A}/sprites.json"))
SPR = {n: Image.open(f"{A}/sprite_{n}.png").convert("RGBA") for n in META}
WMASK = np.load(f"{A}/water_mask.npy")
_r = np.random.default_rng(5)
_ys, _xs = np.where(WMASK[700:1000, 300:800] > 0)
_sel = _r.choice(len(_xs), 70, replace=False)
CRESTS = [(float(_xs[i] + 300), float(_ys[i] + 700), float(_r.random() * 6.28)) for i in _sel]


@lru_cache(maxsize=4096)
def sprite_scaled(name, w, h, flip):
    im = SPR[name].resize((max(2, w), max(2, h)), Image.Resampling.LANCZOS)
    if flip: im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return im


@lru_cache(maxsize=64)
def font(path, size):
    return ImageFont.truetype(path, max(6, int(size)))


@lru_cache(maxsize=512)
def text_img(txt, size, color, shadow=True):
    f = font(FONT_SERIF, size)
    bb = f.getbbox(txt)
    pad = max(4, size // 6)
    w, h = bb[2] - bb[0] + pad * 2 + 4, bb[3] - bb[1] + pad * 2 + 4
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    off = max(2, size // 14)
    if shadow:
        d.text((pad - bb[0] + off, pad - bb[1] + off), txt, font=f, fill=(20, 14, 10, 200))
    d.text((pad - bb[0], pad - bb[1]), txt, font=f, fill=color + (255,), stroke_width=max(1, size // 22), stroke_fill=(40, 28, 20, 255))
    return im

# ------------------------------------------------------------------ camera + context
class Cam:
    def __init__(self, cx, cy, z, roll=0.0, sx=0.0, sy=0.0):
        self.cx, self.cy, self.z, self.roll, self.sx, self.sy = cx, cy, z, roll, sx, sy


def cam_path(t, keys):
    """keys: [(t, cx, cy, z)], smootherstep S-curves between keyframes."""
    if t <= keys[0][0]: return keys[0][1:]
    for a, b in zip(keys[:-1], keys[1:]):
        if t <= b[0]:
            u = smootherstep((t - a[0]) / max(1e-4, b[0] - a[0]))
            return tuple(lerp(a[i], b[i], u) for i in (1, 2, 3))
    return keys[-1][1:]


def shake(t, t0, amp=10.0, dur=0.6):
    if t < t0 or t > t0 + dur: return 0.0, 0.0
    k = (1 - (t - t0) / dur) ** 2
    return math.sin(t * 91) * amp * k, math.cos(t * 77) * amp * k


class Ctx:
    def __init__(self, plate_name, cam, t, tint=None):
        self.cam, self.t = cam, t
        z = cam.z
        th = math.radians(cam.roll)
        c, s = math.cos(th), math.sin(th)
        self.c, self.s = c, s
        # world -> screen: R * ((w - c) * z) + center + shake
        k = z / PS
        M = np.array([[c * k, -s * k, 0], [s * k, c * k, 0]], np.float32)
        M[0, 2] = W / 2 + cam.sx - (c * cam.cx * z - s * cam.cy * z)
        M[1, 2] = H / 2 + cam.sy - (s * cam.cx * z + c * cam.cy * z)
        bg = cv2.warpAffine(plate(plate_name), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if tint is not None:
            bg = np.clip(bg.astype(np.float32) * np.array(tint, np.float32), 0, 255).astype(np.uint8)
        self.img = Image.fromarray(bg)
        self.d = ImageDraw.Draw(self.img, "RGBA")

    def P(self, x, y):
        z = self.cam.z
        dx, dy = (x - self.cam.cx) * z, (y - self.cam.cy) * z
        return (self.c * dx - self.s * dy + W / 2 + self.cam.sx, self.s * dx + self.c * dy + H / 2 + self.cam.sy)

    def L(self, v): return v * self.cam.z

    def visible(self, x, y, m=200):
        px, py = self.P(x, y)
        return -m < px < W + m and -m < py < H + m

# ------------------------------------------------------------------ Layer 1: water, wind, labels
def crests(ctx, t, alpha=1.0, night=False):
    col = (200, 225, 230) if not night else (120, 160, 190)
    for (x, y, ph) in CRESTS:
        u = ((t * 0.35 + ph / 6.28) % 1.0)
        a = math.sin(u * math.pi) * 150 * alpha
        if a < 8: continue
        x2 = x + u * 14
        px, py = ctx.P(x2, y)
        r = ctx.L(5)
        ctx.d.arc([px - r, py - r * 0.5, px + r, py + r * 0.5], 200, 340, fill=col + (int(a),), width=max(1, int(ctx.L(1.1))))


def wind_ribbons(ctx, t, ang_deg, strength, area=(250, 620, 800, 1100), n=12, seed=0):
    if strength <= 0.02: return
    a = math.radians(ang_deg)
    dx, dy = math.cos(a), math.sin(a)
    px_, py_ = -dy, dx
    r = np.random.default_rng(seed)
    x0, y0, x1, y1 = area
    span = 420.0
    for i in range(n):
        ox, oy = r.uniform(x0, x1), r.uniform(y0, y1)
        ph = r.random()
        u = (t * 0.45 + ph) % 1.0
        fade = math.sin(u * math.pi) * strength
        base = (u - 0.5) * span
        pts = []
        for j in range(14):
            s = base + j * 7.0
            w = math.sin(s * 0.03 + t * 3 + i) * 7
            pts.append(ctx.P(ox + dx * s + px_ * w, oy + dy * s + py_ * w))
        ctx.d.line(pts, fill=(245, 248, 255, int(150 * fade)), width=max(2, int(ctx.L(2.0))), joint="curve")


def label(ctx, txt, x, y, size, alpha=1.0, angle=0.0, color=(250, 242, 222)):
    if alpha <= 0.02: return
    sz = int(size * ctx.cam.z)
    if sz < 7: return
    im = text_img(txt, sz, color)
    ang = angle - ctx.cam.roll
    if abs(ang) > 0.3: im = im.rotate(ang, expand=True, resample=Image.Resampling.BICUBIC)
    if alpha < 0.99:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    px, py = ctx.P(x, y)
    ctx.img.paste(im, (int(px - im.width / 2), int(py - im.height / 2)), im)


def screen_title(img, txt, y, size, pop, color=(252, 236, 200)):
    if pop <= 0.02: return
    sz = int(size * pop)
    if sz < 6: return
    im = text_img(txt, sz, color)
    img.paste(im, (int(W / 2 - im.width / 2), int(y - im.height / 2)), im)

# ------------------------------------------------------------------ Layer 2: physical props
def rot(v, a):
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def draw_iron_chain(ctx, p0, p1, prog, t_lock=None):
    """Sequentially locking iron chain links between two world points."""
    if prog <= 0: return
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    n = max(3, int(L / 5.0))
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    shown = prog * n
    for i in range(n):
        if i >= shown: break
        local = min(1.0, shown - i)
        sc = spring_pop(local * 0.38)
        u = (i + 0.5) / n
        sag = math.sin(u * math.pi) * L * 0.08
        cx = p0[0] + (p1[0] - p0[0]) * u
        cy = p0[1] + (p1[1] - p0[1]) * u + sag
        px, py = ctx.P(cx, cy)
        lw, lh = ctx.L(3.6) * sc, ctx.L(2.2 if i % 2 == 0 else 0.8) * sc
        a = ang + math.radians(ctx.cam.roll)
        pts = [rot((math.cos(q) * lw, math.sin(q) * lh), a) for q in np.linspace(0, 2 * math.pi, 14)]
        pts = [(px + x, py + y) for x, y in pts]
        hot = 0.0
        if t_lock is not None and ctx.t > t_lock:
            hot = min(1.0, (ctx.t - t_lock) / 1.2)
        col = (int(lerp(62, 230, hot)), int(lerp(64, 90, hot)), int(lerp(70, 30, hot)))
        ctx.d.polygon(pts, outline=col + (255,), width=max(2, int(ctx.L(1.3))))
        if i % 2 == 0:
            ctx.d.line([pts[2], pts[4]], fill=(180, 182, 190, 220), width=max(1, int(ctx.L(0.6))))


def draw_timber_plank_bridge(ctx, p0, p1, prog, width=11):
    if prog <= 0: return
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    n = max(2, int(L / 4.2))
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0]) + math.radians(ctx.cam.roll)
    for i in range(int(prog * n + 0.999)):
        u = (i + 0.5) / n
        cx, cy = p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u
        local = min(1.0, prog * n - i)
        drop = (1 - smootherstep(local)) * 14
        px, py = ctx.P(cx, cy - drop)
        hw, hl = ctx.L(1.8), ctx.L(width / 2)
        pts = [rot(v, ang) for v in [(-hw, -hl), (hw, -hl), (hw, hl), (-hw, hl)]]
        ctx.d.polygon([(px + x, py + y) for x, y in pts], fill=(176, 128, 74, 255), outline=(84, 54, 30, 255))


def draw_3d_wooden_barrel(ctx, x, y, s, tilt=0.0):
    px, py = ctx.P(x, y)
    w, h = ctx.L(9 * s), ctx.L(12 * s)
    body = [(px - w * 0.42, py - h), (px - w * 0.5, py - h / 2), (px - w * 0.42, py), (px + w * 0.42, py), (px + w * 0.5, py - h / 2), (px + w * 0.42, py - h)]
    ctx.d.polygon(body, fill=(150, 96, 52, 255), outline=INK + (255,), width=max(1, int(ctx.L(0.8 * s))))
    ctx.d.polygon([(px + w * 0.1, py - h), (px + w * 0.42, py - h), (px + w * 0.5, py - h / 2), (px + w * 0.42, py), (px + w * 0.1, py)], fill=(120, 74, 40, 255))
    for f in (0.2, 0.8):
        ctx.d.line([(px - w * 0.47, py - h * f), (px + w * 0.47, py - h * f)], fill=(70, 72, 78, 255), width=max(1, int(ctx.L(1.1 * s))))
    ctx.d.ellipse([px - w * 0.42, py - h - h * 0.12, px + w * 0.42, py - h + h * 0.12], fill=(178, 124, 72, 255), outline=INK + (255,))


def draw_3d_cargo_crate(ctx, x, y, s):
    px, py = ctx.P(x, y)
    a = ctx.L(8 * s)
    top = [(px, py - a * 1.6), (px + a, py - a * 1.1), (px, py - a * 0.6), (px - a, py - a * 1.1)]
    left = [(px - a, py - a * 1.1), (px, py - a * 0.6), (px, py + a * 0.4), (px - a, py - a * 0.1)]
    right = [(px + a, py - a * 1.1), (px, py - a * 0.6), (px, py + a * 0.4), (px + a, py - a * 0.1)]
    ow = max(1, int(ctx.L(0.7 * s)))
    ctx.d.polygon(top, fill=(214, 172, 112, 255), outline=INK + (255,), width=ow)
    ctx.d.polygon(left, fill=(178, 132, 78, 255), outline=INK + (255,), width=ow)
    ctx.d.polygon(right, fill=(146, 104, 60, 255), outline=INK + (255,), width=ow)
    ctx.d.line([left[0], left[2]], fill=(110, 76, 44, 255), width=ow)
    ctx.d.line([right[0], right[2]], fill=(100, 68, 40, 255), width=ow)


def draw_reed_bundle(ctx, x, y, s, angle=0.0):
    px, py = ctx.P(x, y)
    a = math.radians(angle + ctx.cam.roll)
    L = ctx.L(16 * s)
    for k in range(-4, 5):
        o = rot((0, k * ctx.L(0.9 * s)), a)
        p0 = rot((-L / 2, 0), a); p1 = rot((L / 2, 0), a)
        col = (226, 194, 108, 255) if k % 2 else (196, 160, 82, 255)
        ctx.d.line([(px + p0[0] + o[0], py + p0[1] + o[1]), (px + p1[0] + o[0] * 1.3, py + p1[1] + o[1] * 1.3)], fill=col, width=max(1, int(ctx.L(1.0 * s))))
    for f in (-0.2, 0.2):
        c = rot((L * f, 0), a); e = rot((0, ctx.L(4.6 * s)), a)
        ctx.d.line([(px + c[0] - e[0], py + c[1] - e[1]), (px + c[0] + e[0], py + c[1] + e[1])], fill=(150, 46, 40, 255), width=max(1, int(ctx.L(1.4 * s))))


def draw_banner(ctx, x, y, h, color, t, dirx=1.0, seed=0, alpha=1.0):
    if alpha <= 0.02: return
    px, py = ctx.P(x, y)
    top = ctx.P(x, y - h)
    A_ = int(255 * alpha)
    ctx.d.line([(px, py), top], fill=(80, 52, 30, A_), width=max(2, int(ctx.L(h * 0.04))))
    fw, fh = ctx.L(h * 0.55) * dirx, ctx.L(h * 0.32)
    pts = []
    for j in range(9):
        u = j / 8
        wv = math.sin(t * 7 + u * 5 + seed) * ctx.L(h * 0.04) * u
        pts.append((top[0] + fw * u, top[1] + wv))
    for j in range(8, -1, -1):
        u = j / 8
        wv = math.sin(t * 7 + u * 5 + seed) * ctx.L(h * 0.04) * u
        pts.append((top[0] + fw * u, top[1] + fh + wv - fh * 0.15 * u))
    ctx.d.polygon(pts, fill=color + (A_,), outline=INK + (A_,))


def draw_watchtower(ctx, x, y, h, pop=1.0):
    if pop <= 0.02: return
    h *= pop
    px, py = ctx.P(x, y)
    w = ctx.L(h * 0.45); hh = ctx.L(h)
    lw = max(2, int(ctx.L(h * 0.04)))
    for sgn in (-1, 1):
        ctx.d.line([(px + sgn * w * 0.5, py), (px + sgn * w * 0.3, py - hh * 0.7)], fill=(96, 62, 34, 255), width=lw)
    ctx.d.line([(px - w * 0.45, py - hh * 0.1), (px + w * 0.35, py - hh * 0.6)], fill=(110, 72, 40, 255), width=lw)
    ctx.d.line([(px + w * 0.45, py - hh * 0.1), (px - w * 0.35, py - hh * 0.6)], fill=(110, 72, 40, 255), width=lw)
    ctx.d.rectangle([px - w * 0.42, py - hh * 0.78, px + w * 0.42, py - hh * 0.68], fill=(150, 104, 60, 255), outline=INK + (255,))
    ctx.d.polygon([(px - w * 0.55, py - hh * 0.78), (px, py - hh), (px + w * 0.55, py - hh * 0.78)], fill=(70, 74, 90, 255), outline=INK + (255,))


def draw_tent(ctx, x, y, s, color=(200, 190, 170)):
    px, py = ctx.P(x, y)
    w, h = ctx.L(14 * s), ctx.L(11 * s)
    ctx.d.polygon([(px - w, py), (px, py - h), (px + w, py)], fill=color + (255,), outline=INK + (255,), width=max(1, int(ctx.L(0.7 * s))))
    ctx.d.polygon([(px, py - h), (px + w, py), (px + w * 0.2, py)], fill=tuple(int(v * 0.8) for v in color) + (255,))
    ctx.d.polygon([(px - w * 0.18, py), (px, py - h * 0.45), (px + w * 0.18, py)], fill=(60, 40, 28, 255))


def draw_scroll(ctx, x, y, s, spin=0.0):
    px, py = ctx.P(x, y)
    a = math.radians(spin)
    hw, hh = ctx.L(7 * s), ctx.L(4 * s)
    pts = [rot(v, a) for v in [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]]
    ctx.d.polygon([(px + u, py + v) for u, v in pts], fill=(238, 222, 180, 255), outline=INK + (255,))
    for sgn in (-1, 1):
        c = rot((sgn * hw, 0), a); e = rot((0, hh * 1.3), a)
        ctx.d.line([(px + c[0] - e[0], py + c[1] - e[1]), (px + c[0] + e[0], py + c[1] + e[1])], fill=(140, 60, 40, 255), width=max(2, int(ctx.L(1.5 * s))))
    ctx.d.ellipse([px - ctx.L(1.6 * s), py - ctx.L(1.6 * s), px + ctx.L(1.6 * s), py + ctx.L(1.6 * s)], fill=(190, 40, 40, 255))


def draw_flame_cluster(canvas, cx, cy, t, intensity=1.0, seed=0):
    """Skill helper adapted to an RGB canvas: soft glow + tongues + embers on a transparent patch, mask-pasted."""
    if intensity <= 0.02: return
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
        pd.polygon([(pc + ox - fw, pc + 8 * s), (pc + ox - fw * 0.6, pc - fh * 0.45), (pc + ox + math.sin(ph * 1.3) * 7 * s, pc - fh),
                    (pc + ox + fw * 0.6, pc - fh * 0.45), (pc + ox + fw, pc + 8 * s)], fill=(242, 82, 18, int(225 * min(1.0, s))))
        pd.polygon([(pc + ox - fw * 0.48, pc + 5 * s), (pc + ox + math.sin(ph * 1.3) * 4 * s, pc - fh * 0.62),
                    (pc + ox + fw * 0.48, pc + 5 * s)], fill=(255, 226, 92, int(240 * min(1.0, s))))
    for e in range(5):
        ep = (t * 1.1 + seed * 0.23 + e * 0.21) % 1.0
        ex = pc + math.sin(ep * 6.0 + e * 2.0 + seed) * 28 * s - ep * 20 * s
        ey = pc - 18 * s - ep * (pad - 12)
        er = max(2, int((1.0 - ep) * 4.5 * s))
        pd.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(255, 210, 85, int((1.0 - ep) * 230)))
    canvas.paste(patch, (int(cx - pad), int(cy - pad)), patch)


def fire(ctx, x, y, intensity, seed=0):
    if intensity <= 0.02: return
    px, py = ctx.P(x, y)
    draw_flame_cluster(ctx.img, px, py, ctx.t, intensity * ctx.cam.z * 0.42, seed)


def smoke(ctx, x, y, s, seed=0, alpha=1.0):
    if alpha <= 0.02: return
    for k in range(6):
        u = (ctx.t * 0.25 + k / 6 + seed * 0.13) % 1.0
        sx = x + math.sin(u * 4 + seed + k) * 8 * s - u * 26 * s
        sy = y - u * 90 * s
        r = ctx.L((5 + u * 16) * s)
        px, py = ctx.P(sx, sy)
        a = int(math.sin(u * math.pi) * 120 * alpha)
        g = 60 + k * 6
        ctx.d.ellipse([px - r, py - r, px + r, py + r], fill=(g, g, g + 4, a))

# ------------------------------------------------------------------ Layer 3: sprites + rigs
def char(ctx, name, x, y, h, pop=1.0, tilt=0.0, flip=False, brows="neutral", arms=(), sick=0.0, mouth=None, snap=0.0):
    if pop <= 0.01: return
    m = META[name]
    sw0, sh0 = m["size"]
    shp = h * ctx.cam.z * pop
    k = shp / sh0
    w_, h_ = int(sw0 * k), int(sh0 * k)
    if h_ < 4: return
    im = sprite_scaled(name, w_, h_, flip)
    theta = tilt + ctx.cam.roll
    base = (w_ / 2, m["base_y"] * k)
    P = ctx.P(x, y)
    th = math.radians(theta)
    c, s = math.cos(th), math.sin(th)

    def mp(q):  # local (scaled, flipped) -> screen
        dx, dy = q[0] - base[0], q[1] - base[1]
        return (P[0] + dx * c + dy * s, P[1] - dx * s + dy * c)

    def loc(q):  # meta point -> scaled local w/ flip
        lx = q[0] * k
        if flip: lx = w_ - lx
        return (lx, q[1] * k)

    if abs(theta) > 0.2:
        r_im = im.rotate(theta, expand=True, resample=Image.Resampling.BICUBIC)
        cc = mp((w_ / 2, h_ / 2))
        ctx.img.paste(r_im, (int(cc[0] - r_im.width / 2), int(cc[1] - r_im.height / 2)), r_im)
    else:
        ctx.img.paste(im, (int(P[0] - base[0]), int(P[1] - base[1])), im)
    if snap > 0.02:  # directional motion-blur ghost for head-tilt snaps
        ghost = im.copy(); ghost.putalpha(ghost.getchannel("A").point(lambda v: int(v * 0.35 * snap)))
        ctx.img.paste(ghost, (int(P[0] - base[0] - 10 * snap * ctx.cam.z), int(P[1] - base[1])), ghost)
    r = m["r"] * k
    hc = mp(loc(m["head"]))
    if sick > 0.02:
        ctx.d.ellipse([hc[0] - r * 0.82, hc[1] - r * 0.5, hc[0] + r * 0.82, hc[1] + r * 0.82], fill=(120, 196, 92, int(110 * sick)))
    # dynamic eyebrows
    lw = max(2, int(r * 0.07))
    for e in m["eyes"]:
        ex, ey = loc(e)
        side = -1 if ex < loc(m["head"])[0] else 1
        if brows == "angry":
            a, b = (ex - side * 0.15 * r, ey - 0.16 * r), (ex + side * 0.13 * r, ey - 0.30 * r)
        elif brows == "shocked":
            a, b = (ex - 0.13 * r, ey - 0.36 * r), (ex + 0.13 * r, ey - 0.36 * r - side * 0.02 * r)
        else:
            a, b = (ex - 0.12 * r, ey - 0.24 * r), (ex + 0.12 * r, ey - 0.24 * r)
        ctx.d.line([mp(a), mp(b)], fill=INK + (255,), width=lw)
    if mouth == "o":
        mc = mp((loc(m["head"])[0], loc(m["head"])[1] + 0.40 * r))
        ctx.d.ellipse([mc[0] - r * 0.22, mc[1] - r * 0.17, mc[0] + r * 0.22, mc[1] + r * 0.17], fill=(244, 208, 170, 255))
        ctx.d.ellipse([mc[0] - r * 0.11, mc[1] - r * 0.14, mc[0] + r * 0.11, mc[1] + r * 0.14], fill=(60, 20, 20, 255), outline=INK + (255,))
    # stick arms + white gloves + props
    for side, ang, prop in arms:
        sh = loc(m["shoulderR"] if (side == "R") != flip else m["shoulderL"])
        S0 = mp(sh)
        a = math.radians(ang)
        dirx = math.cos(a) * (1 if side == "R" else -1)
        diry = math.sin(a)
        # rotate with sprite tilt
        dx, dy = dirx * c + diry * s, -dirx * s + diry * c
        Lr = 1.05 * r
        Hn = (S0[0] + dx * Lr, S0[1] + dy * Lr)
        ctx.d.line([S0, Hn], fill=INK + (255,), width=max(2, int(r * 0.08)))
        _prop(ctx, prop, Hn, (dx, dy), r)
        gr = r * 0.16
        ctx.d.ellipse([Hn[0] - gr, Hn[1] - gr, Hn[0] + gr, Hn[1] + gr], fill=(255, 255, 255, 255), outline=INK + (255,), width=max(1, int(r * 0.04)))


def _prop(ctx, prop, Hn, dv, r):
    if not prop: return
    if prop == "pointer":
        e = (Hn[0] + dv[0] * r * 1.4, Hn[1] + dv[1] * r * 1.4)
        ctx.d.line([Hn, e], fill=(120, 80, 40, 255), width=max(2, int(r * 0.06)))
        ctx.d.ellipse([e[0] - r * 0.06, e[1] - r * 0.06, e[0] + r * 0.06, e[1] + r * 0.06], fill=(200, 40, 40, 255))
    elif prop == "torch":
        e = (Hn[0] + dv[0] * r * 0.2, Hn[1] - r * 0.9)
        ctx.d.line([(Hn[0], Hn[1] + r * 0.25), e], fill=(110, 70, 36, 255), width=max(3, int(r * 0.1)))
        draw_flame_cluster(ctx.img, e[0], e[1], ctx.t, r / 160.0, 3)
    elif prop == "scroll":
        hw, hh = r * 0.32, r * 0.18
        ctx.d.rectangle([Hn[0] - hw, Hn[1] - hh, Hn[0] + hw, Hn[1] + hh], fill=(238, 222, 180, 255), outline=INK + (255,))
        ctx.d.ellipse([Hn[0] - r * 0.07, Hn[1] - r * 0.07, Hn[0] + r * 0.07, Hn[1] + r * 0.07], fill=(190, 40, 40, 255))
    elif prop == "spear":
        a, b = (Hn[0], Hn[1] + r * 0.9), (Hn[0], Hn[1] - r * 1.6)
        ctx.d.line([a, b], fill=(110, 76, 44, 255), width=max(2, int(r * 0.07)))
        ctx.d.polygon([(b[0] - r * 0.1, b[1]), (b[0], b[1] - r * 0.35), (b[0] + r * 0.1, b[1])], fill=(190, 194, 204, 255), outline=INK + (255,))
    elif prop == "sword":
        e = (Hn[0] + dv[0] * r * 1.1, Hn[1] + dv[1] * r * 1.1)
        ctx.d.line([Hn, e], fill=(214, 218, 226, 255), width=max(3, int(r * 0.1)))
    elif prop == "log":
        ctx.d.rounded_rectangle([Hn[0] - r * 0.7, Hn[1] - r * 0.16, Hn[0] + r * 0.7, Hn[1] + r * 0.16], int(r * 0.12), fill=(132, 88, 50, 255), outline=INK + (255,))


def ship(ctx, name, x, y, w, t, flip=False, ph=0.0, pop=1.0, tilt_extra=0.0, alpha=1.0, wake=True):
    if pop <= 0.01: return
    sw0, sh0 = META[name]["size"]
    wpx = w * ctx.cam.z * pop
    k = wpx / sw0
    w_, h_ = int(sw0 * k), int(sh0 * k)
    if w_ < 4: return
    bob = math.sin(t * 2.1 + ph) * 1.3
    tilt = math.sin(t * 1.7 + ph) * 2.2 + tilt_extra + ctx.cam.roll
    P = ctx.P(x, y + bob)
    if wake:
        rr = ctx.L(w * 0.42)
        ctx.d.ellipse([P[0] - rr, P[1] - rr * 0.16, P[0] + rr, P[1] + rr * 0.16], fill=(30, 50, 60, 60))
        u = (t * 0.8 + ph) % 1.0
        r2 = rr * (0.9 + u * 0.5)
        ctx.d.arc([P[0] - r2, P[1] - r2 * 0.2, P[0] + r2, P[1] + r2 * 0.2], 10, 170, fill=(220, 236, 240, int(150 * (1 - u))), width=max(1, int(ctx.L(1))))
    im = sprite_scaled(name, w_, h_, flip)
    if alpha < 0.99:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    im2 = im.rotate(tilt, expand=True, resample=Image.Resampling.BICUBIC) if abs(tilt) > 0.2 else im
    ctx.img.paste(im2, (int(P[0] - im2.width / 2), int(P[1] - im2.height * 0.86)), im2)

# ------------------------------------------------------------------ geography helpers
RIVER_PATH = [(-20, 478), (90, 522), (190, 592), (280, 700), (360, 788), (440, 846), (500, 858)]


def along(path, u):
    segs = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path[:-1], path[1:])]
    tot = sum(segs); d = u * tot
    for (a, b), L in zip(zip(path[:-1], path[1:]), segs):
        if d <= L:
            v = d / L
            return a[0] + (b[0] - a[0]) * v, a[1] + (b[1] - a[1]) * v, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        d -= L
    return path[-1][0], path[-1][1], 0.0

GRID = [(440, 808), (530, 808), (620, 808), (440, 858), (530, 858), (620, 858)]
LOOSE = [(420, 800), (540, 790), (640, 822), (470, 852), (575, 866), (690, 850)]
SHIPW = 74
FIREBOATS_MAP = [(455, 922), (535, 930), (615, 922)]
TENTS = [(430, 748), (480, 740), (560, 742), (620, 750), (520, 735)]

# ------------------------------------------------------------------ scenes
def S(k): return CLIPS[k][0]

def fleet(ctx, t, slot_u=0.0, chains=0.0, planks=0.0, t_hot=None, burn=None, pops=None):
    """Cao Cao's fleet: loose -> chained grid. burn: list of per-ship fire intensities."""
    pos = []
    for i in range(6):
        x = lerp(LOOSE[i][0], GRID[i][0], slot_u)
        y = lerp(LOOSE[i][1], GRID[i][1], slot_u)
        pos.append((x, y))
    order = [0, 1, 2, 3, 4, 5]
    for i in order[:3]:
        ship(ctx, "warship", *pos[i], SHIPW, t, ph=i, pop=1.0 if pops is None else pops[i], tilt_extra=0 if slot_u < 1 else -math.sin(t * 1.7 + i) * 2.0)
    for row in (0, 3):
        for j in range(2):
            a, b = pos[row + j], pos[row + j + 1]
            p0, p1 = (a[0] + SHIPW * 0.36, a[1] - 6), (b[0] - SHIPW * 0.36, b[1] - 6)
            draw_timber_plank_bridge(ctx, p0, p1, ramp(planks, (row + j) * 0.12, (row + j) * 0.12 + 0.5))
            draw_iron_chain(ctx, (p0[0], p0[1] + 4), (p1[0], p1[1] + 4), ramp(chains, (row + j) * 0.14, (row + j) * 0.14 + 0.45), t_hot)
    for i in order[3:]:
        ship(ctx, "warship", *pos[i], SHIPW, t, ph=i, pop=1.0 if pops is None else pops[i], tilt_extra=0 if slot_u < 1 else -math.sin(t * 1.7 + i) * 2.0)
    if burn:
        for i, b in enumerate(burn):
            if b > 0.02:
                fire(ctx, pos[i][0], pos[i][1] - 12, b, seed=i * 3)
                fire(ctx, pos[i][0] + 20, pos[i][1] - 4, b * 0.7, seed=i * 3 + 1)
    # vertical chains between rows (front side)
    if chains > 0.6:
        for j in range(3):
            a, b = pos[j], pos[j + 3]
            draw_iron_chain(ctx, (a[0], a[1] + 2), (b[0], b[1] - 30), ramp(chains, 0.6 + j * 0.1, 0.9 + j * 0.03), t_hot)
    return pos


def map_labels(ctx, t, a=1.0, night=False):
    col = (250, 242, 222) if not night else (210, 220, 240)
    label(ctx, "Yangtze River", 210, 640, 17, a, angle=-42, color=col)
    label(ctx, "Han River", 700, 470, 13, a * 0.9, angle=-72, color=col)
    label(ctx, "Dongting Lake", 255, 1012, 13, a * 0.9, color=col)
    label(ctx, "Jiangling", 140, 430, 14, a, color=col)
    label(ctx, "Xiakou", 820, 830, 14, a, color=col)


def sc1(t):  # hook
    T0 = 0.0
    cx, cy, z = cam_path(t, [(0, 470, 860, 0.84), (4.0, 520, 840, 1.25), (9.6, 535, 845, 1.9)])
    sx, sy = shake(t, wt(0, "fire"), 12, 0.8)
    ctx = Ctx("day_2realms", Cam(cx, cy, z, 0, sx, sy), t)
    crests(ctx, t)
    map_labels(ctx, t, 1 - ramp(t, 3.5, 5))
    pops = [spring_pop(t - 0.4 - i * 0.18) for i in range(6)]
    tc = wt(0, "chained")
    tf = wt(0, "fire")
    burn = [ramp(t, tf + i * 0.12, tf + i * 0.12 + 0.5) * 1.0 for i in range(6)]
    fleet(ctx, t, slot_u=ramp(t, tc - 0.8, tc + 0.3), chains=ramp(t, tc, tc + 2.0), planks=ramp(t, tc + 0.6, tc + 2.2), burn=burn, pops=pops)
    label(ctx, "Red Cliffs", 560, 1000, 18, ramp(t, 1.0, 2.0))
    screen_title(ctx.img, "208 AD", 150, 74, spring_pop(t - 0.3) * (1 - ramp(t, 4.0, 4.6)))
    screen_title(ctx.img, "THE BATTLE OF RED CLIFFS", 225, 30, spring_pop(t - 0.7) * (1 - ramp(t, 4.0, 4.6)))
    return ctx


def sc2(t):
    ts = S(1)
    keys = [(ts - 0.3, 420, 470, 1.15), (wt(1, "fleet") - 0.3, 420, 520, 1.1), (wt(1, "sailed"), 330, 650, 1.0), (CLIPS[1][1] + 0.3, 500, 800, 1.35)]
    cx, cy, z = cam_path(t, keys)
    ctx = Ctx("day_2realms", Cam(cx, cy, z), t)
    crests(ctx, t)
    map_labels(ctx, t)
    label(ctx, "THE NORTH", 450, 250, 30, ramp(t, wt(1, "north") - 0.3, wt(1, "north") + 0.3))
    tp = wt(1, "Cao")
    # crates of supplies stacking up next to Cao Cao
    tm = wt(1, "two")
    for i in range(6):
        p = spring_pop(t - tm - i * 0.12)
        if p > 0: draw_3d_cargo_crate(ctx, 500 + (i % 3) * 17 - (i // 3) * 8, 520 - (i // 3) * 14, 1.25 * p)
    label(ctx, "220,000 men", 535, 568, 15, ramp(t, tm + 0.3, tm + 0.8))
    point = wt(1, "sailed")
    arm = ("R", 35, "pointer") if t > point - 0.5 else ("R", -55, "sword")
    char(ctx, "cao", 420, 520, 110, spring_pop(t - tp + 0.1), arms=[arm, ("L", 60, None)],
         brows="angry" if t > wt(1, "conquered") else "neutral")
    draw_banner(ctx, 365, 520, 70, (62, 74, 92), t, -1, alpha=ramp(t, tp, tp + 0.4))
    # fleet sails down the Yangtze (physical ships, no route lines)
    tf = wt(1, "fleet")
    for i in range(6):
        u = ramp(t, tf + i * 0.35, CLIPS[1][1] + 0.2 + i * 0.1)
        if t < tf + i * 0.35: continue
        x, y, ang = along(RIVER_PATH, u * 0.97)
        gx, gy = LOOSE[i]
        f = ramp(u, 0.85, 1.0)
        x, y = lerp(x, gx, f), lerp(y, gy, f) + (i % 2) * 10 * (1 - f)
        ship(ctx, "warship", x, y, SHIPW, t, ph=i, pop=spring_pop(t - tf - i * 0.35))
    return ctx


def sc3(t):
    ts = S(2)
    keys = [(ts - 0.3, 500, 800, 1.35), (wt(2, "Liu") - 0.2, 380, 1000, 1.0), (wt(2, "Together"), 470, 1020, 1.0), (CLIPS[2][1] + 0.4, 540, 960, 1.45)]
    cx, cy, z = cam_path(t, keys)
    ctx = Ctx("day_2realms", Cam(cx, cy, z), t)
    crests(ctx, t)
    map_labels(ctx, t)
    fleet(ctx, t)
    tl, tsq, tg = wt(2, "Liu"), wt(2, "Sun"), wt(2, "Together")
    lp = parabolic_hop(t, tg, tg + 1.0, (230, 1170), (500, 1035), 60)
    sp = parabolic_hop(t, tg + 0.15, tg + 1.15, (690, 1150), (610, 1035), 60)
    draw_banner(ctx, lp[0] - 40, lp[1], 60, (150, 112, 70), t, -1, 1, spring_pop(t - tl))
    draw_banner(ctx, sp[0] + 40, sp[1], 60, (168, 50, 45), t, 1, 2, spring_pop(t - tsq))
    label(ctx, "Liu Bei", 230, 1195, 16, ramp(t, tl, tl + 0.4) * (1 - ramp(t, tg, tg + 0.3)))
    label(ctx, "Sun Quan", 690, 1175, 16, ramp(t, tsq, tsq + 0.4) * (1 - ramp(t, tg, tg + 0.3)))
    shocked = t > wt(2, "almost") and t < wt(2, "And")
    char(ctx, "liu", lp[0], lp[1], 95, spring_pop(t - tl + 0.1), tilt=lp[3], brows="shocked" if shocked else "neutral",
         arms=[("R", -55, None), ("L", -55, None)] if shocked else [("R", 60, None), ("L", 60, None)])
    char(ctx, "sun", sp[0], sp[1], 100, spring_pop(t - tsq + 0.1), tilt=sp[3], brows="angry", arms=[("R", -50, "sword"), ("L", 60, None)])
    label(ctx, "Red Cliffs", 560, 1072, 18, ramp(t, tg + 1.0, tg + 1.5))
    tf = wt(2, "fifty")
    label(ctx, "~50,000", 555, 1102, 15, ramp(t, tf, tf + 0.5))
    return ctx


def sc4(t):  # seasick on deck
    ts = S(3)
    roll = math.sin(t * 1.6) * (2.5 + 2.0 * ramp(t, wt(3, "rocked"), wt(3, "rocked") + 1))
    cx, cy, z = cam_path(t, [(ts - 0.3, 450, 1050, 0.95), (CLIPS[3][1], 450, 1120, 1.12)])
    ctx = Ctx("deck", Cam(cx, cy + math.sin(t * 1.6 + 1) * 8, z, roll), t)
    tsick, tdis = wt(3, "seasick"), wt(3, "disease")
    sick = ramp(t, tsick - 0.4, tsick + 0.4)
    # sliding cargo on the pitching deck
    slide = math.sin(t * 1.6) * 60
    draw_3d_cargo_crate(ctx, 150 + slide, 1090, 4.2)
    draw_3d_wooden_barrel(ctx, 770 + slide * 1.3, 1075, 3.6)
    draw_3d_wooden_barrel(ctx, 700 + slide * 1.1, 1100, 3.2)
    lean = math.sin(t * 1.6) * 7
    pro = wt(3, "problem")
    for i, (x, ph) in enumerate([(200, 0.0), (700, 1.4)]):
        p = spring_pop(t - ts - 0.2 - i * 0.2)
        ex = smootherstep(min(1, (t - tdis) * 2)) if t > tdis else 0
        char(ctx, "nsol", x, 1270, 330, p, tilt=lean + math.sin(t * 2.3 + ph) * 4, sick=sick * 1.2, brows="shocked" if sick > 0.5 else "neutral",
             mouth="o" if sick > 0.5 else None, arms=[("R", 70, "spear"), ("L", 75, None)] if sick < 0.5 else [("R", 80, None), ("L", 80, None)])
    tshock = ramp(t, pro - 0.1, pro + 0.15)
    snap = max(0.0, 1 - abs(t - pro) * 4)
    char(ctx, "cao", 450, 1330, 400, spring_pop(t - ts), tilt=lean * 0.7, brows="shocked" if t > pro else "neutral",
         mouth="o" if t > pro else None, sick=sick * 0.6, snap=snap,
         arms=[("R", -58, None), ("L", -58, None)] if t > pro else [("R", 60, None), ("L", 60, None)])
    if t > tdis:
        label(ctx, "DISEASE SPREADS", 450, 900, 34, ramp(t, tdis, tdis + 0.4), color=(230, 240, 200))
    return ctx


def sc5(t):  # lash the fleet together
    ts = S(4)
    cx, cy, z = cam_path(t, [(ts - 0.3, 520, 840, 1.6), (wt(4, "iron"), 530, 830, 2.15), (CLIPS[4][1] + 0.3, 530, 825, 2.3)])
    ctx = Ctx("day_2realms", Cam(cx, cy, z), t)
    crests(ctx, t)
    tl, ti, tw, tff, twk = wt(4, "lashed"), wt(4, "iron"), wt(4, "wooden"), wt(4, "fortress"), wt(4, "walk")
    for i, (x, y) in enumerate(TENTS):
        draw_tent(ctx, x, y, 1.0)
    label(ctx, "Wulin", 530, 712, 15)
    pos = fleet(ctx, t, slot_u=ramp(t, tl - 0.5, tl + 0.8), chains=ramp(t, ti - 0.2, ti + 2.2), planks=ramp(t, tw - 0.2, tw + 2.0))
    draw_watchtower(ctx, 530, 800, 34, spring_pop(t - tff))
    for i, (x, y) in enumerate(pos[:3]):
        draw_banner(ctx, x - 22, y - 26, 24, (62, 74, 92), t, 1, i, spring_pop(t - tff - 0.15 * i))
    # soldier walks ship-to-ship over the planks
    if t > twk - 0.4:
        u = ramp(t, twk - 0.4, CLIPS[4][1] + 0.2)
        bx = lerp(440, 620, u)
        by, tl_ = walk_bob(t, 9, 2.5)
        char(ctx, "nsol", bx, 800 + by, 24, spring_pop(t - twk + 0.4), tilt=tl_, arms=[("R", -50, None), ("L", -50, None)])
    label(ctx, "A FLOATING FORTRESS", 530, 900, 13, ramp(t, tff, tff + 0.4))
    char(ctx, "cao", 470, 745, 30, spring_pop(t - ts), arms=[("R", 30, "pointer"), ("L", 60, None)], brows="neutral")
    return ctx


def easel(ctx, t, x, y, fire_t):
    px, py = ctx.P(x, y)
    L = ctx.L
    ctx.d.line([(px - L(70), py), (px - L(40), py - L(250))], fill=(96, 62, 34, 255), width=int(L(8)))
    ctx.d.line([(px + L(70), py), (px + L(40), py - L(250))], fill=(96, 62, 34, 255), width=int(L(8)))
    ctx.d.rectangle([px - L(110), py - L(260), px + L(110), py - L(110)], fill=(238, 226, 194, 255), outline=INK + (255,), width=int(L(4)))
    # sketched chained fleet on the board
    for i in range(3):
        bx = px - L(66) + i * L(66)
        ctx.d.polygon([(bx - L(26), py - L(170)), (bx + L(26), py - L(170)), (bx + L(18), py - L(150)), (bx - L(18), py - L(150))], fill=(110, 80, 50, 255), outline=INK + (255,))
        ctx.d.line([(bx, py - L(170)), (bx, py - L(205))], fill=INK + (255,), width=int(L(3)))
        if i < 2:
            for j in range(4):
                cx_ = bx + L(26) + j * L(4)
                ctx.d.ellipse([cx_ - L(3), py - L(165), cx_ + L(3), py - L(158)], outline=(60, 60, 66, 255), width=max(1, int(L(1.5))))
    if t > fire_t:
        for i in range(3):
            draw_flame_cluster(ctx.img, px - L(66) + i * L(66), py - L(168), t, L(0.45) * spring_pop(t - fire_t - i * 0.12), i)


def sc6(t):  # Red Cliffs camp: the flaw
    ts = S(5)
    cx, cy, z = cam_path(t, [(ts - 0.3, 450, 1120, 0.96), (CLIPS[5][1] + 0.3, 450, 1160, 1.08)])
    ctx = Ctx("cliffcamp", Cam(cx, cy, z), t)
    tz, tw, th, tfl, tf = wt(5, "Zhou"), wt(5, "watching"), wt(5, "Huang"), wt(5, "flaw"), wt(5, "fire")
    draw_watchtower(ctx, 820, 1080, 210)
    draw_banner(ctx, 90, 1100, 190, (168, 50, 45), t, 1, 1)
    draw_banner(ctx, 700, 1090, 160, (168, 50, 45), t, 1, 2)
    label(ctx, "RED CLIFFS", 450, 840, 40)
    # distant enemy fleet across the river
    for i in range(5):
        ship(ctx, "warship", 160 + i * 140, 770, 120, t, ph=i, wake=False)
    for i in range(4):
        draw_iron_chain(ctx, (210 + i * 140, 752), (240 + i * 140, 752), 1.0)
    easel(ctx, t, 450, 1360, tf)
    zarm = ("R", 10, "pointer") if t > tw - 0.3 else ("R", 60, None)
    char(ctx, "zhou", 220, 1420, 330, spring_pop(t - tz + 0.2), arms=[zarm, ("L", 60, None)], brows="neutral")
    snap = max(0.0, 1 - abs(t - tfl) * 4)
    if t > tf:
        harms, br = [("R", -55, "torch"), ("L", 60, None)], "angry"
    elif t > tfl:
        harms, br = [("R", -60, None), ("L", -60, None)], "shocked"
    else:
        harms, br = [("R", 60, None), ("L", 60, None)], "neutral"
    char(ctx, "huang", 690, 1440, 340, spring_pop(t - th + 0.2), flip=True, brows=br, arms=harms, snap=snap, mouth="o" if tfl < t < tf else None)
    label(ctx, "Zhou Yu", 220, 1470, 26, ramp(t, tz, tz + 0.4) * (1 - ramp(t, tz + 3, tz + 3.5)))
    label(ctx, "Huang Gai", 690, 1490, 26, ramp(t, th, th + 0.4) * (1 - ramp(t, th + 3, th + 3.5)))
    return ctx


def sc7(t):  # the fake defection letter
    ts = S(6)
    cx, cy, z = cam_path(t, [(ts - 0.3, 545, 900, 1.45), (CLIPS[6][1] + 0.3, 540, 860, 1.7)])
    ctx = Ctx("day_2realms", Cam(cx, cy, z), t)
    crests(ctx, t)
    for x, y in TENTS: draw_tent(ctx, x, y, 1.0)
    fleet(ctx, t, slot_u=1, chains=1, planks=1)
    label(ctx, "Red Cliffs", 590, 1068, 16)
    tl, tb = wt(6, "letter"), wt(6, "believed")
    hold = t < tl
    char(ctx, "huang", 600, 1010, 60, spring_pop(t - ts + 0.2), brows="angry",
         arms=[("R", -50, "scroll" if hold else None), ("L", 60, None)])
    if not hold:
        x, y, lift, tilt = parabolic_hop(t, tl, tl + 1.3, (615, 975), (505, 745), 120)
        if t < tl + 1.3:
            draw_scroll(ctx, x, y, 1.3, spin=(t - tl) * 540)
    caught = t > tl + 1.3
    jx, jy, _, jt = parabolic_hop(t, tb, tb + 0.6, (490, 755), (490, 755), 22)
    char(ctx, "cao", jx, jy, 62, spring_pop(t - ts), tilt=jt,
         arms=[("R", -50, "scroll" if caught else None), ("L", -50, None)] if caught else [("R", 60, None), ("L", 60, None)],
         brows="neutral")
    label(ctx, "\"I surrender!\"", 505, 690, 14, ramp(t, tl + 1.3, tl + 1.7))
    return ctx


def sc8(t):  # rigging the fire ships
    ts = S(7)
    cx, cy, z = cam_path(t, [(ts - 0.3, 450, 1080, 0.92), (CLIPS[7][1] + 0.3, 460, 1050, 1.05)])
    ctx = Ctx("cliffcamp", Cam(cx, cy, z), t)
    tt, tr, to, tc, tb = wt(7, "ten"), wt(7, "reeds"), wt(7, "oil"), wt(7, "cloth"), wt(7, "escape")
    boats = [(200, 960), (450, 975), (700, 960)]
    for i, (bx, by) in enumerate(boats):
        p = spring_pop(t - tb - i * 0.15)
        if p > 0:
            ship(ctx, "skiff", bx - 115, by - 30, 95, t, ph=i + 2, pop=p)
            sx, sy = ctx.P(bx - 75, by - 40); ex, ey = ctx.P(bx - 95, by - 22)
            ctx.d.line([(sx, sy), (ex, ey)], fill=(200, 180, 130, 255), width=max(2, int(ctx.L(3))))
        ship(ctx, "fireboat", bx, by, 230, t, ph=i, pop=spring_pop(t - tt - i * 0.15))
    # supplies pile on the cliff-top
    for i in range(3): draw_3d_wooden_barrel(ctx, 90 + i * 40, 1250 + (i % 2) * 12, 3.0)
    for i in range(3): draw_reed_bundle(ctx, 120 + i * 30, 1210 - i * 12, 3.0, -10)
    # bundles + barrels fly into the boats
    for i in range(6):
        t0 = tr + i * 0.18
        if t < t0: continue
        x, y, _, tl_ = parabolic_hop(t, t0, t0 + 0.8, (140, 1200), (boats[i % 3][0] + (i // 3) * 30 - 15, boats[i % 3][1] - 60), 180)
        if t < t0 + 0.8: draw_reed_bundle(ctx, x, y, 3.0, tl_ * 6)
    for i in range(3):
        t0 = to + i * 0.2
        if t < t0: continue
        x, y, _, _ = parabolic_hop(t, t0, t0 + 0.8, (110, 1240), (boats[i][0], boats[i][1] - 50), 200)
        if t < t0 + 0.8: draw_3d_wooden_barrel(ctx, x, y, 3.0)
    if t > tc:  # oiled cloth glints
        for i, (bx, by) in enumerate(boats):
            a = math.sin(min(1, (t - tc - i * 0.15) * 2) * math.pi)
            if a > 0:
                px, py = ctx.P(bx, by - 90)
                ctx.d.ellipse([px - ctx.L(60), py - ctx.L(20), px + ctx.L(60), py + ctx.L(20)], fill=(255, 240, 200, int(120 * a)))
    char(ctx, "ssol", 300, 1400, 250, spring_pop(t - ts), arms=[("R", -20, "log"), ("L", -20, None)])
    char(ctx, "huang", 610, 1430, 300, spring_pop(t - ts - 0.2), flip=True, brows="angry", arms=[("R", 15, "pointer"), ("L", 60, None)])
    label(ctx, "x10 FIRE SHIPS", 450, 820, 34, ramp(t, tt + 0.3, tt + 0.7))
    return ctx


def sc9(t):  # waiting for the wind
    ts = S(8)
    cx, cy, z = cam_path(t, [(ts - 0.3, 520, 860, 1.05), (CLIPS[8][1] + 0.3, 540, 870, 1.35)])
    ctx = Ctx("night", Cam(cx, cy, z), t)
    crests(ctx, t, 0.8, night=True)
    for x, y in TENTS: draw_tent(ctx, x, y, 1.0, (140, 140, 150))
    fleet(ctx, t, 1, 1, 1)
    for i, (bx, by) in enumerate(FIREBOATS_MAP):
        ship(ctx, "skiff", bx - 22, by + 6, 30, t, ph=i + 3)
        ship(ctx, "fireboat", bx, by + 30, 54, t, ph=i)
    tn, ttu, tse = wt(8, "north"), wt(8, "turned"), wt(8, "southeast")
    # north wind blows south, then swings round to the southeast wind blowing north-west
    ang = lerp(95, 230, ramp(t, ttu - 0.2, ttu + 1.2))
    st = ramp(t, tn - 0.8, tn) * (1 - 0.7 * ramp(t, ttu - 0.6, ttu)) + ramp(t, ttu, ttu + 0.8) * 1.0
    wind_ribbons(ctx, t, ang, min(1, st), (250, 600, 820, 1150), 16)
    flip = 1 if ang < 160 else -1
    draw_banner(ctx, 600, 1000, 46, (168, 50, 45), t, -flip if t > ttu else 1, 3)
    label(ctx, "NORTH WIND", 520, 650, 22, ramp(t, tn, tn + 0.3) * (1 - ramp(t, ttu - 0.4, ttu)), color=(210, 220, 240))
    label(ctx, "SOUTHEAST WIND", 540, 1110, 22, ramp(t, tse, tse + 0.4), color=(255, 226, 160))
    label(ctx, "Red Cliffs", 600, 1040, 16, 1, color=(210, 220, 240))
    return ctx


NIGHT_TINT = (0.42, 0.5, 0.72)


def sc10a(t):  # cheering on deck at night
    ts = S(9)
    cx, cy, z = cam_path(t, [(ts - 0.3, 450, 1080, 0.98), (wt(9, "Then") + 0.3, 450, 1100, 1.08)])
    ctx = Ctx("deck", Cam(cx, cy, z, math.sin(t * 1.2) * 1.2), t, NIGHT_TINT)
    u = ramp(t, ts - 0.3, wt(9, "Then") + 0.3)
    for i, x in enumerate((260, 450, 640)):
        ship(ctx, "fireboat", x + (i - 1) * 40 * u, 830 + 12 * u, lerp(60, 120, u), t, ph=i, wake=True)
    tp, tc = wt(9, "pointing"), wt(9, "cheering")
    for i, (x, ph) in enumerate([(170, 0.0), (450, 1.0), (730, 2.0)]):
        hop = parabolic_hop(t, tc + i * 0.1, tc + 0.5 + i * 0.1, (x, 1290), (x, 1290), 30)
        if t > tc:
            arms = [("R", -55, "spear" if i == 1 else None), ("L", -55, None)]
        elif t > tp:
            arms = [("R", -15, "pointer"), ("L", 60, None)]
        else:
            arms = [("R", 60, None), ("L", 60, None)]
        char(ctx, "nsol", hop[0], hop[1], 300, spring_pop(t - ts - i * 0.12), tilt=hop[3], arms=arms, flip=(i == 2))
    label(ctx, "\"Here come the defectors!\"", 450, 960, 30, ramp(t, wt(9, "Here"), wt(9, "Here") + 0.3), color=(255, 236, 190))
    return ctx


def sc10b(t):  # ignite and abandon ship
    t0 = wt(9, "Then")
    cx, cy, z = cam_path(t, [(t0 - 0.3, 540, 880, 1.6), (CLIPS[9][1] + 0.3, 540, 870, 2.0)])
    ctx = Ctx("night", Cam(cx, cy, z), t)
    crests(ctx, t, 0.8, night=True)
    for x, y in TENTS: draw_tent(ctx, x, y, 1.0, (140, 140, 150))
    fleet(ctx, t, 1, 1, 1)
    tf, tj = wt(9, "fire"), wt(9, "jumped")
    adv = ramp(t, t0 - 0.3, CLIPS[9][1] + 0.6)
    wind_ribbons(ctx, t, 235, 0.6, (380, 820, 720, 1020), 8, 4)
    for i, (bx, by) in enumerate(FIREBOATS_MAP):
        y = lerp(by + 30, by + 4, adv)
        sk = ramp(t, tj, tj + 1.4)
        ship(ctx, "skiff", bx - 22 + sk * (i - 1) * 10, y + 6 + sk * 40, 30, t, ph=i + 3)
        ship(ctx, "fireboat", bx, y, 54, t, ph=i)
        fire(ctx, bx, y - 14, ramp(t, tf + i * 0.15, tf + i * 0.15 + 0.6) * 0.75, seed=i + 9)
        hx, hy, _, ht = parabolic_hop(t, tj + i * 0.12, tj + 0.7 + i * 0.12, (bx + 6, y - 12), (bx - 22, y + 4), 18)
        if t > tj + 0.7 + i * 0.12:
            hx, hy = bx - 22 + sk * (i - 1) * 10, y + 4 + sk * 40
        char(ctx, "ssol", hx, hy, 18, 1, tilt=ht, arms=[("R", -50, None), ("L", -50, None)])
    return ctx


def sc11(t):  # the trap closes
    ts = S(10)
    tsl, ttr, tle = wt(10, "slammed"), wt(10, "trap"), wt(10, "leapt")
    sx, sy = shake(t, tsl, 14, 0.9)
    cx, cy, z = cam_path(t, [(ts - 0.3, 540, 870, 2.0), (CLIPS[10][1] + 0.3, 530, 835, 1.7)])
    ctx = Ctx("night", Cam(cx, cy, z, 0, sx, sy), t)
    crests(ctx, t, 0.8, night=True)
    for x, y in TENTS: draw_tent(ctx, x, y, 1.0, (140, 140, 150))
    order = [5, 4, 3, 2, 1, 0]
    burn = [0.0] * 6
    for n, i in enumerate(order):
        st = tsl if n < 1 else tle + (n - 1) * 0.45
        burn[i] = ramp(t, st, st + 0.6) * 1.1
    fleet(ctx, t, 1, 1, 1, t_hot=ttr, burn=burn)
    for i, (bx, by) in enumerate(FIREBOATS_MAP):
        y = lerp(by + 4, by - 40, ramp(t, ts - 0.3, tsl))
        ship(ctx, "fireboat", bx, y, 54, t, ph=i, tilt_extra=-6 * ramp(t, tsl, tsl + 0.3))
        fire(ctx, bx, y - 14, 0.95, seed=i + 9)
    label(ctx, "NO ESCAPE", 530, 930, 18, ramp(t, ttr, ttr + 0.3), color=(255, 210, 160))
    return ctx


def sc12(t):  # rout
    ts = S(11)
    tc, tsm, tfl, tnv = wt(11, "camps"), wt(11, "Smoke"), wt(11, "fled"), wt(11, "never")
    cx, cy, z = cam_path(t, [(ts - 0.3, 530, 835, 1.7), (tfl - 0.4, 520, 760, 1.4), (CLIPS[11][1] + 0.3, 500, 560, 1.05)])
    ctx = Ctx("night", Cam(cx, cy, z), t)
    crests(ctx, t, 0.8, night=True)
    fleet(ctx, t, 1, 1, 1, t_hot=0, burn=[1.0] * 6)
    for i, (x, y) in enumerate(TENTS):
        draw_tent(ctx, x, y, 1.0, (140, 140, 150))
        fire(ctx, x, y - 4, ramp(t, tc + i * 0.2, tc + i * 0.2 + 0.6) * 0.8, seed=i + 20)
    for i in range(6):
        smoke(ctx, 420 + i * 45, 760 - (i % 2) * 30, 1.2, i, ramp(t, tsm - 0.3, tsm + 0.6))
    # Cao Cao runs north through the marsh
    u = ramp(t, tfl, tnv)
    x, y = lerp(520, 470, u), lerp(728, 470, u)
    by, tl_ = walk_bob(t, 11, 5) if tfl < t < tnv else (0, 0)
    if t > tfl:
        for j in range(5):
            mu = u - j * 0.06
            if mu > 0:
                mx, my = lerp(520, 470, mu), lerp(728, 470, mu)
                px, py = ctx.P(mx + (j % 2) * 6 - 3, my + 2)
                ctx.d.ellipse([px - ctx.L(4), py - ctx.L(1.6), px + ctx.L(4), py + ctx.L(1.6)], fill=(70, 52, 36, 200))
    look_back = t > tnv
    char(ctx, "cao", x, y + by, 40, spring_pop(t - ts + 0.3), tilt=tl_, brows="shocked", mouth="o",
         arms=[("R", -60, None), ("L", -60, None)], flip=look_back)
    label(ctx, "Huarong Road", 450, 560, 14, ramp(t, tfl, tfl + 0.5), color=(210, 220, 240))
    return ctx


def sc13(t):  # three kingdoms
    ts = S(12)
    cx, cy, z = cam_path(t, [(ts - 0.3, 480, 760, 1.05), (ts + 2.0, 450, 800, 0.84), (TOTAL, 450, 800, 0.82)])
    tk, tr = wt(12, "three"), wt(12, "rocking")
    ctx = Ctx("day_3kingdoms", Cam(cx, cy, z), t)
    # crossfade tint from 2 realms to 3 kingdoms
    a = ramp(t, tk - 0.3, tk + 0.8)
    if a < 0.99:
        other = Ctx("day_2realms", Cam(cx, cy, z), t)
        ctx.img = Image.blend(other.img, ctx.img, a)
        ctx.d = ImageDraw.Draw(ctx.img, "RGBA")
    crests(ctx, t)
    for name, (x, y), kd, col, d in [("cao", (450, 470), "WEI", (62, 74, 92), 0.0), ("liu", (190, 1170), "SHU", (150, 112, 70), 0.25), ("sun", (680, 1170), "WU", (168, 50, 45), 0.5)]:
        p = spring_pop(t - tk - d)
        draw_banner(ctx, x - 55, y, 80, col, t, -1, d * 10, min(1, p))
        char(ctx, name, x, y, 120, p, brows="angry", arms=[("R", -50, "sword"), ("L", 60, None)])
        label(ctx, kd, x, y + 45, 34, ramp(t, tk + d, tk + d + 0.3))
    # final gag: one lonely ship rocking hard
    tilt = math.sin(t * 5) * 14 * ramp(t, tr - 0.6, tr)
    ship(ctx, "warship", 530, 860, 80, t, pop=spring_pop(t - tr + 0.8), tilt_extra=tilt)
    screen_title(ctx.img, "THE CHAINS THAT", 120, 40, spring_pop(t - CLIPS[12][1] + 0.1))
    screen_title(ctx.img, "BURNED AN EMPIRE", 172, 40, spring_pop(t - CLIPS[12][1] - 0.1))
    return ctx


def mid(k):  # boundary between clip k-1 and clip k
    return (CLIPS[k - 1][1] + CLIPS[k][0]) / 2

SCENES = [
    (0.0, mid(1), sc1, "map"), (mid(1), mid(2), sc2, "map"), (mid(2), mid(3), sc3, "map"), (mid(3), mid(4), sc4, "deck"),
    (mid(4), mid(5), sc5, "map"), (mid(5), mid(6), sc6, "camp"), (mid(6), mid(7), sc7, "map"), (mid(7), mid(8), sc8, "camp"),
    (mid(8), mid(9), sc9, "night"), (mid(9), wt(9, "Then") - 0.15, sc10a, "deck"), (wt(9, "Then") - 0.15, mid(10), sc10b, "night"),
    (mid(10), mid(11), sc11, "night"), (mid(11), mid(12), sc12, "night"), (mid(12), TOTAL + 1, sc13, "map"),
]
XF = 0.28  # crossfade seconds at plate changes


def captions(img, t):
    d = ImageDraw.Draw(img)
    for txt, s, e in CAPS:
        if s - 0.05 <= t < e:
            size = 34
            while True:
                f = font(FONT_SANS, size)
                bb = d.textbbox((0, 0), txt, font=f, stroke_width=4)
                tw = bb[2] - bb[0]
                if tw <= W - 56 or size <= 28: break
                size -= 2
            if tw > W - 56:  # still too wide: wrap
                ws = txt.split(); h_ = len(ws) // 2
                lines = [" ".join(ws[:h_]), " ".join(ws[h_:])]
            else:
                lines = [txt]
            pop = 0.9 + 0.1 * spring_pop(t - s + 0.05, 0.25)
            f = font(FONT_SANS, int(size * pop))
            y = 1010
            for ln in lines:
                bb = d.textbbox((0, 0), ln, font=f, stroke_width=4)
                tw = bb[2] - bb[0]
                d.text(((W - tw) / 2 - bb[0], y - bb[1]), ln, font=f, fill=(255, 250, 236), stroke_width=4, stroke_fill=(20, 14, 10))
                y += (bb[3] - bb[1]) + 10
            break


def render(t):
    idx = 0
    for i, (a, b, fn, kind) in enumerate(SCENES):
        if a <= t < b: idx = i; break
    else:
        idx = len(SCENES) - 1
    a, b, fn, kind = SCENES[idx]
    img = fn(t).img
    if idx > 0 and t - a < XF and SCENES[idx - 1][3] != kind:
        prev = SCENES[idx - 1][2](t).img
        img = Image.blend(prev, img, smoothstep((t - a) / XF))
    # global fade in/out
    if t < 0.25 or t > TOTAL - 0.6:
        k = min(smoothstep(t / 0.25), smoothstep((TOTAL - t) / 0.6))
        img = Image.blend(Image.new("RGB", img.size, (0, 0, 0)), img, max(0.0, k))
    captions(img, t)
    return img

# ------------------------------------------------------------------ sparse one-shot foley
def foley_track():
    n = int((TOTAL + 1) * SR)
    out = np.zeros(n, np.float32)
    r = np.random.default_rng(1)

    def env(L, att=0.005, dec=0.3):
        t = np.arange(L) / SR
        return np.minimum(1, t / att) * np.exp(-t / dec)

    def put(t0, sig, g):
        i = int(t0 * SR); j = min(n, i + len(sig))
        if i < n: out[i:j] += sig[:j - i] * g

    def clank():
        L = int(0.5 * SR); tt = np.arange(L) / SR
        s = sum(np.sin(2 * np.pi * f * tt) * a for f, a in [(820, 1), (1370, 0.7), (2210, 0.5), (3120, 0.3)])
        return s * env(L, 0.001, 0.09) + r.normal(0, 0.3, L) * env(L, 0.001, 0.015)

    def whoosh(d=0.8, up=True):
        L = int(d * SR); x = r.normal(0, 1, L)
        y = np.zeros(L); a = 0.0
        for i in range(L):  # sweeping one-pole lowpass
            c = 0.02 + 0.25 * (i / L if up else 1 - i / L)
            a += c * (x[i] - a); y[i] = a
        return y * np.sin(np.linspace(0, np.pi, L)) * 2.5

    def pop():
        L = int(0.12 * SR); tt = np.arange(L) / SR
        return np.sin(2 * np.pi * (500 + 900 * tt / 0.12) * tt) * env(L, 0.002, 0.04)

    def drum():
        L = int(0.8 * SR); tt = np.arange(L) / SR
        return np.sin(2 * np.pi * (95 * np.exp(-tt * 3)) * tt * 1.0) * env(L, 0.002, 0.25) * 1.4

    def roar(d=1.6):
        L = int(d * SR); x = r.normal(0, 1, L)
        y = np.convolve(x, np.ones(60) / 60, "same")
        crack = (r.random(L) > 0.9993) * r.normal(0, 4, L)
        return (y * 3 + crack) * np.minimum(1, np.arange(L) / (0.05 * SR)) * np.exp(-np.arange(L) / (0.8 * SR))

    def boom():
        L = int(1.6 * SR); tt = np.arange(L) / SR
        return (np.sin(2 * np.pi * 55 * tt) * 1.5 + np.convolve(r.normal(0, 1, L), np.ones(30) / 30, "same") * 2) * env(L, 0.003, 0.45)

    def gong():
        L = int(3.0 * SR); tt = np.arange(L) / SR
        return sum(np.sin(2 * np.pi * f * tt) * a for f, a in [(180, 1), (271, 0.6), (437, 0.4), (612, 0.25)]) * env(L, 0.004, 1.1)

    def creak():
        L = int(0.9 * SR); tt = np.arange(L) / SR
        f = 140 + 40 * np.sin(tt * 9)
        return np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.25 * np.sin(np.linspace(0, np.pi, L)) * (0.6 + 0.4 * r.random(L))

    cues = [
        (0.7, pop(), 0.20), (wt(0, "chained"), clank(), 0.24), (wt(0, "fire"), roar(1.4), 0.26),
        (wt(1, "Cao"), drum(), 0.26), (wt(1, "fleet"), whoosh(1.0), 0.18),
        (wt(2, "Together"), whoosh(0.6), 0.16), (wt(3, "rocked"), creak(), 0.22),
        (wt(4, "iron"), clank(), 0.24), (wt(4, "iron") + 0.6, clank(), 0.18), (wt(4, "fortress"), drum(), 0.22),
        (wt(5, "flaw"), whoosh(0.5), 0.18), (wt(5, "fire"), roar(0.9), 0.20),
        (wt(6, "letter"), whoosh(0.9, False), 0.18), (wt(7, "escape"), pop(), 0.20),
        (wt(8, "turned"), whoosh(2.2), 0.24), (wt(9, "fire"), roar(1.6), 0.24),
        (wt(10, "slammed"), boom(), 0.28), (wt(10, "leapt"), roar(2.0), 0.22),
        (wt(11, "fled"), drum(), 0.22), (wt(12, "three"), gong(), 0.22),
    ]
    for t0, sig, g in cues:
        sig = sig / (np.max(np.abs(sig)) + 1e-6)
        put(t0, sig, g)
    return out


def write_audio(path):
    fx = foley_track()
    w = wave.open(path, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(fx, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()

# ------------------------------------------------------------------ render driver
def render_chunk(args):
    i0, i1, path = args
    proc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", path],
                            stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    for f in range(i0, i1):
        proc.stdin.write(render(f / FPS).tobytes())
    proc.stdin.close()
    err = proc.stderr.read()
    proc.wait()
    if proc.returncode: raise RuntimeError(err.decode())
    return path


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "qa"
    out = os.path.join(HERE, "out"); os.makedirs(out, exist_ok=True)
    if mode == "qa":
        ts = [float(x) for x in sys.argv[2:]] or [3, 8.5, 15, 27, 40, 55, 68, 78, 87, 97, 107, 114, 124, 134, 145]
        for t in ts:
            render(t).save(f"{out}/qa_{t:06.2f}.png")
        print("qa ok")
    else:
        from multiprocessing import Pool
        nproc = os.cpu_count() or 4
        n = NFRAMES
        step = math.ceil(n / (nproc * 3))
        chunks = [(i, min(n, i + step), f"{out}/seg_{i:06d}.mp4") for i in range(0, n, step)]
        with Pool(nproc) as p:
            segs = p.map(render_chunk, chunks)
        with open(f"{out}/segs.txt", "w") as f:
            for s in segs: f.write(f"file '{s}'\n")
        write_audio(f"{out}/foley.wav")
        final = sys.argv[2] if len(sys.argv) > 2 else f"{out}/red_cliffs.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{out}/segs.txt", "-i", os.path.join(HERE, "vo", "voiceover.wav"),
                        "-i", f"{out}/foley.wav", "-filter_complex", "[1:a]aresample=44100[v];[v][2:a]amix=inputs=2:normalize=0:duration=first[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", final], check=True)
        print("rendered", final)
