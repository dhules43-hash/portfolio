"""Stage 3: procedural clean map plates + #00FF00 green-screen sprites -> RGBA cutouts."""
import math, json, os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(OUT, exist_ok=True)
S = 2                      # plates rendered at 2x the 900x1600 overscan for crisp camera zooms
PW, PH = 900 * S, 1600 * S
rng = np.random.default_rng(208)

# ---------------- geography (world coords, 900x1600) ----------------
RIVER = [(-40, 470, 46), (90, 520, 50), (190, 590, 54), (280, 700, 60), (360, 790, 74),
         (440, 850, 92), (530, 862, 96), (620, 852, 92), (700, 815, 76), (780, 760, 64),
         (860, 690, 58), (950, 630, 56)]
HAN = [(740, 790, 26), (720, 640, 24), (690, 480, 22), (640, 300, 20), (600, 120, 18), (580, -40, 18)]
LAKE = (250, 1010, 105, 70)   # Dongting lake ellipse


def densify(pts, step=3.0):
    out = []
    for (x0, y0, r0), (x1, y1, r1) in zip(pts[:-1], pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        for i in range(n):
            u = i / n
            # catmull-ish smoothing via cosine blend of radius
            out.append((x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, r0 + (r1 - r0) * (0.5 - 0.5 * math.cos(u * math.pi))))
    out.append(pts[-1])
    return out


def smooth_poly(pts, iters=3):
    p = [list(q) for q in pts]
    for _ in range(iters):  # Chaikin
        q = [p[0]]
        for a, b in zip(p[:-1], p[1:]):
            q.append([0.75 * a[i] + 0.25 * b[i] for i in range(3)])
            q.append([0.25 * a[i] + 0.75 * b[i] for i in range(3)])
        q.append(p[-1])
        p = q
    return [tuple(v) for v in p]


RIVER_S = smooth_poly(RIVER)
HAN_S = smooth_poly(HAN)


def fbm(h, w, octaves=7, base=6, persist=0.52, seed=0):
    r = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh, gw = base * 2 ** o + 1, int(base * 2 ** o * w / h) + 1
        g = r.random((gh, gw)).astype(np.float32)
        acc += amp * cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC)
        tot += amp
        amp *= persist
    acc /= tot
    return (acc - acc.min()) / (acc.max() - acc.min())


def water_mask():
    m = np.zeros((PH, PW), np.uint8)
    wobble = fbm(PH // 4, PW // 4, 4, 8, seed=3)
    for x, y, r in densify(RIVER_S, 2):
        cv2.circle(m, (int(x * S), int(y * S)), int(r * S), 255, -1, cv2.LINE_AA)
    for x, y, r in densify(HAN_S, 2):
        cv2.circle(m, (int(x * S), int(y * S)), int(r * S * 0.5), 255, -1, cv2.LINE_AA)
    lx, ly, la, lb = LAKE
    cv2.ellipse(m, (lx * S, ly * S), (la * S, lb * S), -12, 0, 360, 255, -1, cv2.LINE_AA)
    cv2.ellipse(m, ((lx + 70) * S, (ly - 40) * S), (50 * S, 34 * S), 20, 0, 360, 255, -1, cv2.LINE_AA)
    # lake outlet to river
    cv2.line(m, ((lx + 90) * S, (ly - 50) * S), (440 * S, 880 * S), 255, 18 * S, cv2.LINE_AA)
    # irregular shorelines
    wb = cv2.resize(wobble, (PW, PH))
    blur = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 6 * S)
    m = ((blur + (wb - 0.5) * 0.28) > 0.5).astype(np.uint8) * 255
    return m


def heightmap(wm):
    dist = cv2.distanceTransform(255 - wm, cv2.DIST_L2, 5) / S  # world px from water
    n = fbm(PH, PW, 8, 5, 0.55, seed=11)
    ridge = 1.0 - np.abs(fbm(PH, PW, 7, 4, 0.5, seed=21) * 2 - 1)
    ridge = ridge ** 2.2
    yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32) / S
    # mountain belts: far north (Qinling), south-west hills, south-east hills
    belt = np.clip((330 - yy) / 260, 0, 1) * 1.0
    belt += np.exp(-(((xx - 150) / 210) ** 2 + ((yy - 1400) / 220) ** 2)) * 0.85
    belt += np.exp(-(((xx - 720) / 240) ** 2 + ((yy - 1270) / 260) ** 2)) * 0.75
    belt += np.exp(-(((xx - 300) / 200) ** 2 + ((yy - 230) / 200) ** 2)) * 0.5
    away = np.clip(dist / 220, 0, 1)
    h = 0.12 + 0.28 * n * away + ridge * (0.15 + 0.75 * np.clip(belt, 0, 1.2)) * away
    # Red Cliffs: steep escarpment on south bank
    rc = np.exp(-(((xx - 560) / 150) ** 2 + ((yy - 975) / 30) ** 2))
    h += rc * 0.30
    h = cv2.GaussianBlur(h, (0, 0), 1.2 * S)
    h = np.clip(h, 0, 1.15)
    h[wm > 0] = 0.0
    return h, dist, rc


def hillshade(h, az=315, alt=42, zf=520.0):
    gy, gx = np.gradient(h * zf / S)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    azr, altr = math.radians(360 - az + 90), math.radians(alt)
    sh = np.sin(altr) * np.cos(slope) + np.cos(altr) * np.sin(slope) * np.cos(azr - aspect)
    return np.clip(sh, 0, 1)


def hex2(c):
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def ramp(h):
    stops = [(0.00, hex2("#7E8A5A")), (0.17, hex2("#8F9460")), (0.30, hex2("#B59F78")),
             (0.52, hex2("#C2A57E")), (0.66, hex2("#A86F4C")), (0.80, hex2("#9A7A62")),
             (0.88, hex2("#F4F7FA")), (1.2, hex2("#F4F7FA"))]
    out = np.zeros(h.shape + (3,), np.float32)
    for (a, ca), (b, cb) in zip(stops[:-1], stops[1:]):
        m = (h >= a) & (h < b)
        u = ((h[m] - a) / (b - a))[:, None]
        out[m] = ca * (1 - u) + cb * u
    return out


def build_map_plates():
    wm = water_mask()
    h, dist, rc = heightmap(wm)
    sh = hillshade(h)
    col = ramp(h)
    # terracotta cliff faces
    rcc = np.clip(rc * 1.6, 0, 1)[..., None]
    col = col * (1 - rcc * 0.85) + hex2("#B5523A") * rcc * 0.85
    land = col * (0.50 + 0.72 * sh[..., None])
    # water
    wd = cv2.distanceTransform(wm, cv2.DIST_L2, 5) / S
    depth = np.clip(wd / 40, 0, 1)[..., None]
    water = hex2("#5E8794") * (1 - depth) + hex2("#41697A") * depth
    wmf = (cv2.GaussianBlur(wm, (3, 3), 0).astype(np.float32) / 255)[..., None]
    img = land * (1 - wmf) + water * wmf
    # dark ink coastline
    edge = cv2.morphologyEx(wm, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
    edge = cv2.GaussianBlur(edge, (3, 3), 0).astype(np.float32)[..., None] / 255
    img = img * (1 - edge * 0.55) + hex2("#2E2A24") * edge * 0.55
    # subtle paper grain + vignette
    grain = (rng.random((PH, PW)).astype(np.float32) - 0.5)[..., None] * 8
    yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32)
    vig = 1 - 0.22 * (((xx / PW - 0.5) ** 2 + (yy / PH - 0.5) ** 2) * 2.2)
    day = np.clip((img + grain) * vig[..., None], 0, 255).astype(np.uint8)
    Image.fromarray(day).save(f"{OUT}/plate_day.png")

    # territory-tinted variants (flat translucent tints + ink borders)
    north = (yy / S < 780 + 0 * xx) & (wm == 0)
    # north territory = everything above the river line
    rv = np.zeros((PH, PW), np.uint8)
    pts = np.array([[x * S, y * S] for x, y, r in RIVER_S] + [[PW + 10, -10], [-10, -10]], np.int32)
    cv2.fillPoly(rv, [pts], 255)
    north = (rv > 0) & (wm == 0)
    south = (rv == 0) & (wm == 0)
    west = south & (xx / S < 360)
    east = south & (xx / S >= 360)

    def tint(base, regions):
        o = base.astype(np.float32)
        for m, c, a in regions:
            mm = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 2 * S)[..., None]
            o = o * (1 - mm * a) + hex2(c) * mm * a
        return np.clip(o, 0, 255).astype(np.uint8)

    t2 = tint(day, [(north, "#3B4656", 0.30), (south, "#A8453A", 0.18)])
    Image.fromarray(t2).save(f"{OUT}/plate_day_2realms.png")
    t3 = tint(day, [(north, "#3B4656", 0.32), (west, "#C9A24A", 0.26), (east, "#A8453A", 0.24)])
    # ink border between west/east
    bord = np.zeros((PH, PW), np.uint8)
    cv2.line(bord, (360 * S, 760 * S), (360 * S, 1600 * S), 255, 3 * S)
    bord[wm > 0] = 0
    b = cv2.GaussianBlur(bord, (3, 3), 0).astype(np.float32)[..., None] / 255
    t3 = np.clip(t3 * (1 - b * 0.6) + hex2("#2E2A24") * b * 0.6, 0, 255).astype(np.uint8)
    Image.fromarray(t3).save(f"{OUT}/plate_day_3kingdoms.png")

    # night: moonlit, cool silver-blue
    shn = hillshade(h, az=40, alt=35)
    landn = (col * np.array([0.42, 0.48, 0.66])) * (0.35 + 0.85 * shn[..., None])
    watern = hex2("#24465A") * (1 - depth) + hex2("#132C3C") * depth
    imgn = landn * (1 - wmf) + watern * wmf
    imgn = imgn * (1 - edge * 0.5) + hex2("#0B1118") * edge * 0.5
    night = np.clip((imgn + grain * 0.6) * vig[..., None], 0, 255).astype(np.uint8)
    Image.fromarray(night).save(f"{OUT}/plate_night.png")
    np.save(f"{OUT}/water_mask.npy", cv2.resize(wm, (900, 1600)))


# ---------------- 2.5D diorama plates ----------------
def lerpc(a, b, u):
    return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))


def ridge_layer(d, y0, amp, color, seed, step=6):
    r = np.random.default_rng(seed)
    pts = [(0, PH)]
    ph = r.random() * 10
    for x in range(0, PW + step, step * S):
        y = y0 * S - (math.sin(x / (170 * S) + ph) * 0.5 + 0.5) * amp * S \
            - (math.sin(x / (63 * S) + ph * 2) * 0.5 + 0.5) * amp * 0.4 * S - r.random() * 6 * S
        pts.append((x, y))
    pts.append((PW, PH))
    d.polygon(pts, fill=color)


def build_deck_plate():
    im = Image.new("RGB", (PW, PH))
    d = ImageDraw.Draw(im)
    for y in range(0, PH):          # misty sky
        u = y / (760 * S)
        d.line([(0, y), (PW, y)], fill=lerpc((168, 186, 196), (226, 214, 190), min(1, u)))
    ridge_layer(d, 560, 230, (150, 158, 160), 1)
    ridge_layer(d, 650, 170, (126, 128, 122), 2)
    ridge_layer(d, 720, 110, (160, 112, 84), 3)       # reddish cliffs across river
    d.rectangle([0, 740 * S, PW, 900 * S], fill=(88, 124, 136))  # river band
    for k in range(40):
        x = rng.random() * PW
        y = (750 + rng.random() * 140) * S
        d.line([(x, y), (x + 40 * S, y)], fill=(130, 160, 168), width=2 * S)
    im = im.filter(ImageFilter.GaussianBlur(3 * S))  # shallow depth of field
    d = ImageDraw.Draw(im)
    # gunwale
    d.rectangle([0, 860 * S, PW, 905 * S], fill=(96, 60, 36))
    d.rectangle([0, 860 * S, PW, 872 * S], fill=(132, 88, 52))
    for x in range(0, 900, 90):
        d.rectangle([x * S, 800 * S, (x + 12) * S, 870 * S], fill=(104, 66, 38))
    d.rectangle([0, 796 * S, PW, 810 * S], fill=(120, 78, 44))
    # deck in perspective
    top, bot = 905, 1600
    d.rectangle([0, top * S, PW, PH], fill=(176, 128, 82))
    vx = 450
    for i in range(-14, 15):
        xb = vx + i * 110
        xt = vx + i * 40
        d.line([(xt * S, top * S), (xb * S, bot * S)], fill=(120, 82, 48), width=3 * S)
    yv = top
    gap = 22
    while yv < bot:
        d.line([(0, yv * S), (PW, yv * S)], fill=(150, 104, 62), width=2 * S)
        yv += gap
        gap *= 1.16
    # light pool
    arr = np.array(im).astype(np.float32)
    yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32) / S
    pool = np.exp(-(((xx - 450) / 420) ** 2 + ((yy - 1180) / 260) ** 2)) * 26
    arr += pool[..., None]
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(f"{OUT}/plate_deck.png")


def build_cliffcamp_plate():
    im = Image.new("RGB", (PW, PH))
    d = ImageDraw.Draw(im)
    for y in range(0, PH):
        u = y / (820 * S)
        d.line([(0, y), (PW, y)], fill=lerpc((172, 190, 204), (236, 220, 192), min(1, u)))
    ridge_layer(d, 600, 200, (152, 160, 166), 7)
    ridge_layer(d, 700, 120, (132, 136, 130), 8)
    d.rectangle([0, 720 * S, PW, 980 * S], fill=(84, 120, 134))  # the river
    for k in range(50):
        x = rng.random() * PW
        y = (730 + rng.random() * 240) * S
        d.line([(x, y), (x + 50 * S, y)], fill=(126, 158, 170), width=2 * S)
    im = im.filter(ImageFilter.GaussianBlur(3 * S))
    d = ImageDraw.Draw(im)
    # red cliff top plateau (foreground ground plane)
    pts = [(0, 1000 * S)]
    for x in range(0, 901, 30):
        pts.append((x * S, (985 + math.sin(x / 70) * 10 + rng.random() * 6) * S))
    pts += [(PW, PH), (0, PH)]
    d.polygon(pts, fill=(170, 92, 62))
    # cliff face strata
    for k in range(9):
        y = 1010 + k * 26
        d.line([(0, y * S), (PW, (y + rng.random() * 18) * S)], fill=(146, 74, 50), width=3 * S)
    # grassy-dirt top surface where characters stand
    d.polygon([(0, 1090 * S), (PW, 1070 * S), (PW, PH), (0, PH)], fill=(190, 156, 112))
    for k in range(260):
        x, y = rng.random() * PW, (1090 + rng.random() * 510) * S
        d.ellipse([x, y, x + 6 * S, y + 3 * S], fill=(170, 136, 96))
    arr = np.array(im).astype(np.float32)
    yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32) / S
    arr += (np.exp(-(((xx - 450) / 420) ** 2 + ((yy - 1260) / 260) ** 2)) * 22)[..., None]
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(f"{OUT}/plate_cliffcamp.png")


# ---------------- green-screen sprites ----------------
G = (0, 255, 0)
INK = (46, 30, 22)


def green_canvas(n=800):
    im = Image.new("RGB", (n, n), G)
    return im, ImageDraw.Draw(im)


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def draw_pawn(costume, skin=(244, 208, 170), helmet=None, trim=(214, 170, 64), beard=None, extra=None):
    im, d = green_canvas()
    cx = 400
    # bell-shaped armless pawn body
    body = [(cx - 78, 400), (cx - 96, 470), (cx - 128, 580), (cx - 170, 690), (cx - 180, 735),
            (cx + 180, 735), (cx + 170, 690), (cx + 128, 580), (cx + 96, 470), (cx + 78, 400)]
    d.polygon(body, fill=costume, outline=INK, width=9)
    # cel shade right half
    d.polygon([(cx + 20, 410), (cx + 78, 404), (cx + 96, 470), (cx + 128, 580), (cx + 170, 690),
               (cx + 176, 728), (cx + 40, 728)], fill=shade(costume, 0.80))
    d.line(body + [body[0]], fill=INK, width=9)
    # base rim and belt/trim
    d.rounded_rectangle([cx - 186, 712, cx + 186, 748], 16, fill=shade(costume, 0.7), outline=INK, width=8)
    d.rectangle([cx - 112, 540, cx + 112, 566], fill=trim, outline=INK, width=6)
    d.polygon([(cx - 60, 410), (cx, 480), (cx + 60, 410)], fill=trim, outline=INK, width=6)  # collar V
    if extra:
        extra(d, cx)
    # head
    hy, r = 262, 150
    d.ellipse([cx - r, hy - r, cx + r, hy + r], fill=skin, outline=INK, width=9)
    d.chord([cx - r + 8, hy - r + 8, cx + r - 8, hy + r - 8], -60, 60, fill=shade(skin, 0.92))
    if beard:
        d.chord([cx - 110, hy - 20, cx + 110, hy + 175], 10, 170, fill=beard, outline=INK, width=6)
    d.ellipse([cx - 62, hy + 2, cx - 34, hy + 30], fill=(20, 14, 10))
    d.ellipse([cx + 34, hy + 2, cx + 62, hy + 30], fill=(20, 14, 10))
    d.ellipse([cx - 56, hy + 6, cx - 48, hy + 14], fill=(255, 255, 255))
    d.ellipse([cx + 40, hy + 6, cx + 48, hy + 14], fill=(255, 255, 255))
    d.arc([cx - 30, hy + 40, cx + 30, hy + 80], 20, 160, fill=INK, width=7)
    d.ellipse([cx - 112, hy + 36, cx - 80, hy + 56], fill=(240, 160, 140))
    d.ellipse([cx + 80, hy + 36, cx + 112, hy + 56], fill=(240, 160, 140))
    if helmet:
        helmet(d, cx, hy, r)
    meta = {"head": (cx, hy), "r": r, "shoulderL": (cx - 92, 470), "shoulderR": (cx + 92, 470),
            "brow_y": hy - 22, "eyes": [(cx - 48, hy + 16), (cx + 48, hy + 16)], "base_y": 748}
    return im, meta


def helm_cao(d, cx, hy, r):
    d.chord([cx - r - 6, hy - r - 10, cx + r + 6, hy + r - 40], 180, 360, fill=(212, 168, 60), outline=INK, width=8)
    d.rectangle([cx - r - 10, hy - 70, cx + r + 10, hy - 44], fill=(176, 132, 40), outline=INK, width=7)
    d.polygon([(cx - 14, hy - r - 6), (cx, hy - r - 110), (cx + 14, hy - r - 6)], fill=(60, 64, 78), outline=INK, width=6)
    d.ellipse([cx - 30, hy - r - 150, cx + 30, hy - r - 90], fill=(150, 40, 40), outline=INK, width=6)


def helm_soldier(color):
    def f(d, cx, hy, r):
        d.polygon([(cx - r - 20, hy - 46), (cx, hy - r - 90), (cx + r + 20, hy - 46)], fill=color, outline=INK, width=8)
        d.rectangle([cx - r - 20, hy - 56, cx + r + 20, hy - 36], fill=shade(color, 0.7), outline=INK, width=6)
        d.ellipse([cx - 12, hy - r - 104, cx + 12, hy - r - 80], fill=(200, 60, 50), outline=INK, width=4)
    return f


def hat_liu(d, cx, hy, r):
    d.chord([cx - r, hy - r, cx + r, hy + r - 60], 180, 360, fill=(40, 36, 34), outline=INK, width=7)
    d.rounded_rectangle([cx - 46, hy - r - 70, cx + 46, hy - r + 30], 10, fill=(40, 36, 34), outline=INK, width=7)
    d.rectangle([cx - r - 30, hy - r - 74, cx + r + 30, hy - r - 58], fill=(40, 36, 34), outline=INK, width=6)


def crown_sun(d, cx, hy, r):
    d.chord([cx - r, hy - r, cx + r, hy + r - 70], 180, 360, fill=(48, 34, 28), outline=INK, width=7)
    d.polygon([(cx - 70, hy - r + 26), (cx - 70, hy - r - 50), (cx - 35, hy - r - 10), (cx, hy - r - 70),
               (cx + 35, hy - r - 10), (cx + 70, hy - r - 50), (cx + 70, hy - r + 26)], fill=(226, 180, 60), outline=INK, width=7)
    d.ellipse([cx - 12, hy - r - 20, cx + 12, hy - r + 4], fill=(190, 40, 50))


def hair_zhou(d, cx, hy, r):
    d.chord([cx - r, hy - r, cx + r, hy + r - 70], 180, 360, fill=(36, 28, 24), outline=INK, width=7)
    d.ellipse([cx - 50, hy - r - 80, cx + 50, hy - r + 10], fill=(36, 28, 24), outline=INK, width=7)
    d.rectangle([cx - 56, hy - r - 20, cx + 56, hy - r - 2], fill=(196, 50, 46), outline=INK, width=5)
    d.polygon([(cx + 56, hy - r - 14), (cx + 120, hy - r + 30), (cx + 100, hy - r + 44), (cx + 52, hy - r)], fill=(196, 50, 46), outline=INK, width=5)


def band_huang(d, cx, hy, r):
    d.chord([cx - r, hy - r, cx + r, hy + r - 70], 180, 360, fill=(150, 150, 150), outline=INK, width=7)
    d.rectangle([cx - r + 6, hy - 70, cx + r - 6, hy - 44], fill=(196, 46, 40), outline=INK, width=6)
    d.polygon([(cx + r - 10, hy - 64), (cx + r + 60, hy - 30), (cx + r + 40, hy - 10), (cx + r - 10, hy - 46)], fill=(196, 46, 40), outline=INK, width=5)


def armor_plates(d, cx):
    for k in range(3):
        y = 590 + k * 38
        d.arc([cx - 150 - k * 10, y - 30, cx + 150 + k * 10, y + 30], 20, 160, fill=INK, width=5)


def draw_warship():
    im, d = green_canvas()
    hull = [(80, 470), (130, 560), (650, 560), (730, 470), (690, 500), (110, 500)]
    d.polygon([(70, 440), (120, 570), (660, 570), (740, 440), (640, 480), (160, 480)], fill=(112, 70, 40), outline=INK, width=9)
    d.polygon([(120, 520), (660, 520), (650, 570), (130, 570)], fill=(86, 52, 30))
    for x in range(170, 640, 60):
        d.ellipse([x, 500, x + 22, 518], fill=(40, 28, 20))
    # two-storey cabin
    d.rectangle([220, 360, 580, 480], fill=(150, 100, 58), outline=INK, width=8)
    d.rectangle([270, 270, 530, 362], fill=(160, 112, 66), outline=INK, width=8)
    for x in range(240, 580, 56):
        d.rectangle([x, 395, x + 30, 440], fill=(60, 40, 26))
    d.polygon([(200, 362), (400, 320), (600, 362)], fill=(70, 74, 90), outline=INK, width=7)
    d.polygon([(250, 272), (400, 225), (550, 272)], fill=(70, 74, 90), outline=INK, width=7)
    # mast + slate-blue sail with gold trim
    d.rectangle([392, 70, 408, 270], fill=(90, 58, 34), outline=INK, width=4)
    d.polygon([(300, 90), (500, 90), (520, 230), (280, 230)], fill=(74, 88, 112), outline=INK, width=8)
    for y in (125, 160, 195):
        d.line([(292, y), (508, y)], fill=(214, 170, 64), width=5)
    d.polygon([(408, 70), (480, 50), (408, 30)], fill=(214, 170, 64), outline=INK, width=4)
    return im


def draw_fireboat():
    im, d = green_canvas()
    d.polygon([(110, 470), (170, 570), (610, 570), (700, 450), (600, 490), (190, 490)], fill=(120, 78, 44), outline=INK, width=9)
    d.polygon([(170, 530), (610, 530), (600, 570), (175, 570)], fill=(92, 58, 32))
    # mound of dry reeds and firewood
    for k in range(44):
        x = 210 + (k % 11) * 36
        y = 470 - (k // 11) * 34 + (k % 3) * 6
        d.line([(x - 30, y + 20), (x + 34, y - 30)], fill=(224, 190, 104), width=10)
        d.line([(x - 30, y + 20), (x + 34, y - 30)], fill=(176, 140, 70), width=3)
    # crimson oiled cloth cover
    d.chord([190, 300, 620, 560], 180, 360, fill=(170, 46, 40), outline=INK, width=8)
    for x in range(240, 600, 70):
        d.line([(x, 330), (x - 10, 432)], fill=(128, 30, 30), width=6)
    d.rectangle([396, 160, 408, 320], fill=(90, 58, 34), outline=INK, width=4)
    d.polygon([(408, 165), (520, 190), (408, 225)], fill=(200, 56, 46), outline=INK, width=5)
    return im


def draw_skiff():
    im, d = green_canvas()
    d.polygon([(170, 430), (240, 520), (560, 520), (630, 430), (540, 450), (260, 450)], fill=(140, 96, 58), outline=INK, width=9)
    d.line([(300, 440), (180, 560)], fill=(100, 70, 40), width=12)
    d.line([(500, 440), (620, 560)], fill=(100, 70, 40), width=12)
    d.ellipse([160, 540, 200, 580], fill=(100, 70, 40))
    d.ellipse([600, 540, 640, 580], fill=(100, 70, 40))
    return im


def extract_green_screen_sprite_meta(im, name, target_max_dim, meta=None):
    """Same HSV mask + spill suppression as the skill helper; also returns crop/scale for rig anchors."""
    p = f"{OUT}/_green_{name}.png"
    im.save(p)
    bgr = cv2.imread(p)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    green_mask = cv2.inRange(hsv, np.array([32, 65, 65]), np.array([90, 255, 255]))
    fg_mask = cv2.bitwise_not(green_mask)
    fg_mask[:8, :] = fg_mask[-8:, :] = fg_mask[:, :8] = fg_mask[:, -8:] = 0
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=1)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    fg_mask = cv2.erode(fg_mask, np.ones((3, 3), np.uint8), iterations=1)
    alpha = cv2.GaussianBlur(fg_mask, (3, 3), 0)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    spill = np.maximum(0.0, g - np.maximum(r, b))
    rgb[:, :, 1] = g - spill * 0.80
    rgba = np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), alpha])
    ys, xs = np.where(alpha > 20)
    h, w = fg_mask.shape
    y0, x0 = max(0, int(ys.min()) - 4), max(0, int(xs.min()) - 4)
    rgba = rgba[y0:min(h, int(ys.max()) + 5), x0:min(w, int(xs.max()) + 5)]
    sp = Image.fromarray(rgba, mode="RGBA")
    sc = 1.0
    if max(sp.size) > target_max_dim:
        sc = target_max_dim / float(max(sp.size))
        sp = sp.resize((max(8, int(sp.size[0] * sc)), max(8, int(sp.size[1] * sc))), Image.Resampling.LANCZOS)
    sp.save(f"{OUT}/sprite_{name}.png")
    m = {"size": sp.size}
    if meta:
        def tf(p):
            return [(p[0] - x0) * sc, (p[1] - y0) * sc]
        m.update({"head": tf(meta["head"]), "r": meta["r"] * sc, "shoulderL": tf(meta["shoulderL"]),
                  "shoulderR": tf(meta["shoulderR"]), "brow_y": (meta["brow_y"] - y0) * sc,
                  "eyes": [tf(e) for e in meta["eyes"]], "base_y": (meta["base_y"] - y0) * sc})
    return m


def build_sprites():
    metas = {}
    chars = {
        "cao": dict(costume=(62, 74, 92), helmet=helm_cao, extra=armor_plates),
        "liu": dict(costume=(138, 104, 66), helmet=hat_liu, trim=(226, 206, 160)),
        "sun": dict(costume=(168, 50, 45), helmet=crown_sun),
        "zhou": dict(costume=(236, 230, 218), helmet=hair_zhou, trim=(196, 50, 46)),
        "huang": dict(costume=(176, 52, 44), helmet=band_huang, beard=(214, 214, 214), extra=armor_plates),
        "nsol": dict(costume=(92, 100, 114), helmet=helm_soldier((86, 92, 106)), trim=(150, 150, 160), extra=armor_plates),
        "ssol": dict(costume=(164, 60, 50), helmet=helm_soldier((176, 64, 52)), trim=(220, 180, 90), extra=armor_plates),
    }
    for name, kw in chars.items():
        im, meta = draw_pawn(**kw)
        metas[name] = extract_green_screen_sprite_meta(im, name, 420, meta)
    metas["warship"] = extract_green_screen_sprite_meta(draw_warship(), "warship", 520)
    metas["fireboat"] = extract_green_screen_sprite_meta(draw_fireboat(), "fireboat", 480)
    metas["skiff"] = extract_green_screen_sprite_meta(draw_skiff(), "skiff", 360)
    json.dump(metas, open(f"{OUT}/sprites.json", "w"), indent=1)


if __name__ == "__main__":
    build_map_plates()
    build_deck_plate()
    build_cliffcamp_plate()
    build_sprites()
    print("assets ok")
