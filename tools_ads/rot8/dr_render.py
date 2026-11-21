# rot8 — Delta Reign «السعر ينكسر» — motion render (deterministic render(t); EDL in edl.md)
import sys, json, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
R = '/home/claude/htr-videos/'; F = R + 'fetch/'; OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/work/dr_v.mp4'
RANGE = (float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else None
W, H, FPS = 1080, 1920, 30
import os
C = json.load(open(R + 'tools_ads/rot8/' + os.environ.get('CUES', 'dr_cues.json'))); T = C['t']; TOTAL = C['total']
def FL(s): return ImageFont.truetype(F + 'font_lalezar.ttf', s)
def FB(s): return ImageFont.truetype(F + 'font_bungee.ttf', s)
def FA(s): return ImageFont.truetype(F + 'font_anton.ttf', s)
PURP = (90, 70, 80); CRIM = (210, 25, 50); INK = (28, 22, 30); TEAL = (46, 196, 182); WHITE = (255, 255, 255); DEEP = (14, 8, 34); PINK = (255, 80, 160); GOLDG = (255, 190, 90)
DARK = os.environ.get('THEME') == 'dark'
if DARK: INK = (250, 246, 240); PURP = (230, 40, 70)
POP = os.environ.get('THEME') == 'pop'
if POP: INK = (255, 255, 255); CRIM = (22, 28, 74); PURP = (20, 10, 40)
def cl(x): return min(max(x, 0.0), 1.0)
def eo(x): x = cl(x); return 1 - (1 - x) ** 3
def eio(x): x = cl(x); return 3 * x * x - 2 * x ** 3
def ebk(x, s=1.7): x = cl(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def to_bgra(im): a = np.array(im.convert('RGBA')); return a[..., [2, 1, 0, 3]].copy()

def text_sprite(s, font, fill=WHITE, stroke=0, stroke_fill=DEEP, glow=None, glow_r=18, pad=50):
    d0 = ImageDraw.Draw(Image.new('RGBA', (10, 10))); bb = d0.textbbox((0, 0), s, font=font, stroke_width=stroke)
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad; ox, oy = pad - bb[0], pad - bb[1]
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).text((ox, oy), s, font=font, fill=255, stroke_width=stroke + (6 if glow else 0))
    if glow:
        g = Image.new('RGBA', (w, h), glow + (0,)); g.putalpha(m.filter(ImageFilter.GaussianBlur(glow_r))); out = Image.alpha_composite(out, g)
    sh = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ImageDraw.Draw(sh).text((ox, oy + 9), s, font=font, fill=(0, 0, 0, 150), stroke_width=stroke, stroke_fill=(0, 0, 0, 150))
    out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(out).text((ox, oy), s, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return to_bgra(out)
def pill(s, font, bg, fg=WHITE, padx=46, pady=20):
    d0 = ImageDraw.Draw(Image.new('RGBA', (10, 10))); bb = d0.textbbox((0, 0), s, font=font)
    w, h = bb[2] - bb[0] + 2 * padx, bb[3] - bb[1] + 2 * pady
    im = Image.new('RGBA', (w + 60, h + 60), (0, 0, 0, 0)); g = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).rounded_rectangle((30, 36, 30 + w, 36 + h), h // 2, fill=bg + (160,)); im = Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(im); d.rounded_rectangle((30, 30, 30 + w, 30 + h), h // 2, fill=bg + (255,)); d.text((30 + padx - bb[0], 30 + pady - bb[1]), s, font=font, fill=fg)
    return to_bgra(im)
def cutout(p, thr=238):
    from scipy.ndimage import label
    im = Image.open(p).convert('RGBA'); a = np.array(im)
    if (a[..., 3] < 250).mean() > 0.05: return im
    white = a[..., :3].min(-1) > thr; lab, _ = label(white)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    a[..., 3] = np.where(np.isin(lab, list(edge)), 0, 255).astype(np.uint8); im = Image.fromarray(a); im.putalpha(im.split()[3].filter(ImageFilter.GaussianBlur(1))); return im
def img_sprite(im, w, glow=PURP, glow_r=40, rounded=0):
    s = w / im.width; im = im.resize((w, int(im.height * s)), Image.LANCZOS)
    if rounded:
        m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), rounded, fill=255)
        im.putalpha(Image.fromarray(np.minimum(np.array(im.split()[3]), np.array(m))))
    pad = glow_r * 2; c = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    if glow:
        g = Image.new('RGBA', c.size, glow + (0,)); ga = Image.new('L', c.size, 0); ga.paste(im.split()[3], (pad, pad))
        g.putalpha(ga.filter(ImageFilter.GaussianBlur(glow_r)).point(lambda v: min(255, int(v * 1.3)))); c = Image.alpha_composite(c, g)
    c.alpha_composite(im, (pad, pad)); return to_bgra(c)
def blit(f, spr, cx, cy, s=1.0, a=1.0, rot=0.0):
    if a <= 0.003 or s <= 0.01: return
    h0, w0 = spr.shape[:2]
    if abs(rot) > .01 or abs(s - 1) > .002:
        M = cv2.getRotationMatrix2D((w0 / 2, h0 / 2), rot, s)
        nw = int(abs(w0 * s * math.cos(math.radians(rot))) + abs(h0 * s * math.sin(math.radians(rot)))) + 2
        nh = int(abs(h0 * s * math.cos(math.radians(rot))) + abs(w0 * s * math.sin(math.radians(rot)))) + 2
        M[0, 2] += nw / 2 - w0 / 2; M[1, 2] += nh / 2 - h0 / 2
        spr = cv2.warpAffine(spr, M, (nw, nh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    h, w = spr.shape[:2]; x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb: return
    sp = spr[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32); al = sp[..., 3:4] / 255 * a
    f[ya:yb, xa:xb] = f[ya:yb, xa:xb] * (1 - al) + sp[..., :3] * al

# ---------- background: deep purple studio + side light + soft floor glow (no grid: new look)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
def radial(cx, cy, r): return np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)))[..., None]
BASE = np.zeros((H, W, 3), np.float32); BASE[:] = (222, 224, 230)
BASE += radial(420, 700, 700) * np.array([22, 24, 25], np.float32)
BASE -= radial(980, 1850, 600) * np.array([40, 40, 30], np.float32)
if DARK:
    BASE = np.zeros((H, W, 3), np.float32); BASE[:] = (40, 22, 12)
    BASE += radial(700, 600, 700) * np.array([90, 60, 20], np.float32)
    BASE += radial(300, 1700, 600) * np.array([40, 20, 120], np.float32)
beam = np.zeros((H, W), np.float32); cv2.fillPoly(beam, [np.array([[0, 320], [470, 0], [640, 0], [0, 760]])], 1.0); beam = cv2.GaussianBlur(beam, (0, 0), 45)
BEAM = beam[..., None] * np.array([12, 10, 8], np.float32)
if DARK: BEAM = beam[..., None] * np.array([120, 110, 90], np.float32) * .25
rng = np.random.default_rng(8); DUST = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1.2, 3.2), rng.uniform(0, 6.28), rng.uniform(.2, .8)) for _ in range(70)]
VIG = (1 - .12 * np.clip(((xx - 540) ** 2 / 540 ** 2 + (yy - 960) ** 2 / 1100 ** 2) - .35, 0, 1))[..., None]
BG_RED = np.zeros((H, W, 3), np.float32); BG_RED[:] = (40, 30, 200); BG_RED += radial(540, 700, 800) * np.array([30, 40, 50], np.float32)
BG_NAVY = np.zeros((H, W, 3), np.float32); BG_NAVY[:] = (170, 150, 20); BG_NAVY += radial(540, 800, 800) * np.array([40, 40, 20], np.float32)
BG_TEAL = np.zeros((H, W, 3), np.float32); BG_TEAL[:] = (120, 140, 20)
POP_BG = {'sceneQ2': BG_NAVY, 'scene5': BG_NAVY, 'scene7b': BG_NAVY, 'scene4b': BG_NAVY, 'sceneQb': BG_NAVY, 'scene5b': BG_RED, 'scene8b': BG_TEAL}
def background(t, light=1.0):
    f = BASE + BEAM * (0.8 + 0.2 * math.sin(t * 1.3))
    if t < T['s2']: t = t * .35  # hook: dust slow (calm first 3 s)
    for (x, y, r, ph, sp) in DUST:
        y2 = (y - t * 40 * sp) % H; v = (.5 + .5 * math.sin(t * 2 * sp + ph)) * 200
        cv2.circle(f, (int(x + 30 * math.sin(t * .9 + ph)), int(y2)), int(r * 1.1), (150 + v * .2, 140 + v * .2, 225), -1, cv2.LINE_AA)
    return f * VIG * light

# ---------- sprites
BOXIM = cutout(F + 'dr_box_b.jpg')
BOX = img_sprite(BOXIM, 640, PURP, 40); BOXM = img_sprite(BOXIM, 300, PURP, 20); BOXS = img_sprite(BOXIM, 250, PURP, 16); BOXBG = img_sprite(BOXIM.filter(ImageFilter.GaussianBlur(4)), 560, None)
GOLD = img_sprite(Image.open(F + 'dra_c141a.jpg').convert('RGBA'), 640, GOLDG, 70, rounded=30)
SIRC = img_sprite(Image.open(F + 'dra_c138a.jpg').convert('RGBA'), 330, (255, 120, 60), 30, rounded=18)
RAIK = img_sprite(Image.open(F + 'dra_c136a.jpg').convert('RGBA'), 330, (120, 200, 255), 30, rounded=18)
LOGO = img_sprite(Image.open(R + 'tools_challenges/htr_logo.png').convert('RGBA'), 700, (20, 20, 60), 18)
def tag_sprite(label, big=False):
    w, h = (900, 620) if big else (430, 300)
    im = Image.new('RGBA', (w + 80, h + 120), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    g = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle((40, 80, 40 + w, 80 + h), 40, fill=(60, 40, 50, 110)); im = Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(24))); d = ImageDraw.Draw(im)
    d.rounded_rectangle((40, 70, 40 + w, 70 + h), 40 if not big else 70, fill=CRIM); hx = 40 + w // 2
    d.ellipse((hx - (22 if not big else 40), 100, hx + (22 if not big else 40), 100 + (44 if not big else 80)), fill=(235, 230, 232))
    f = FL(200) if label == '؟' and not big else (FA(330) if big else FA(160))
    bb = d.textbbox((0, 0), label, font=f); d.text((hx - (bb[2] + bb[0]) / 2, 70 + h * .58 - (bb[3] + bb[1]) / 2), label, font=f, fill=(255, 255, 255))
    return to_bgra(im)
TAGQ = tag_sprite('؟'); TAG980 = tag_sprite(os.environ.get('OLD','980'), True)
T_TITLE = text_sprite('DELTA REIGN', FB(92), fill=INK)
T_BKM = text_sprite('بكم تتوقعه؟', FL(150), fill=INK)
T_850 = text_sprite('850', FA(450), fill=CRIM)
T_RIYAL = text_sprite('ريال بس!', FL(160), fill=INK)
T_980s = text_sprite(os.environ.get('OLD','980'), FA(140), fill=(150, 145, 155))
T_36 = text_sprite('36', FA(540), fill=CRIM)
T_BAK = text_sprite('باك', FL(180), fill=INK)
P_HR = pill('HYPER RARE', FB(56), CRIM); T_MEGA = text_sprite('ميغا ريكوازا', FL(120), fill=INK)
T_CASE = text_sprite('CASE', FB(130), fill=INK); T_6 = text_sprite('6 بوكسات', FL(100), fill=CRIM)
T_4800 = text_sprite('4,800 ريال', FL(180), fill=CRIM)
def stamp_sprite():
    im = Image.new('RGBA', (760, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, 750, 250), 40, outline=(255, 255, 255), width=10, fill=CRIM + (255,))
    f = FL(130); s = 'وفّر 300 ريال'; bb = d.textbbox((0, 0), s, font=f); d.text((380 - (bb[2] + bb[0]) / 2, 130 - (bb[3] + bb[1]) / 2), s, font=f, fill=(255, 255, 255))
    return to_bgra(im)
STAMP = stamp_sprite()
T_SITE = text_sprite('HTRTCG.COM', FB(92), fill=(255, 255, 255) if POP else (0, 130, 120))
T_SHIP = text_sprite('التوصيل لين باب بيتك', FL(96), fill=INK)
P_OLAYA = pill('العُليا سكوير', FL(84), (40, 160, 150)); T_ABHUR = text_sprite('أبحر الجنوبية – جدة', FL(72), fill=(255, 255, 255) if POP else (90, 85, 95))
T_CMT = text_sprite('علّق ولو بنقطة', FL(124), fill=INK); P_FOLLOW = pill('تابع HTR', FL(78), (200, 25, 55)); T_LIKE = text_sprite('لايك وسيف', FL(124), fill=INK)
def pin_sprite():
    im = Image.new('RGBA', (120, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(im); d.ellipse((10, 10, 110, 110), fill=(46, 196, 182)); d.polygon([(22, 80), (98, 80), (60, 150)], fill=(46, 196, 182)); d.ellipse((40, 40, 80, 80), fill=(14, 8, 34)); return to_bgra(im)
PIN = pin_sprite()
rs = np.random.default_rng(4)
SHARDS = []
for i in range(34):
    a = rs.uniform(0, 6.28); sz = rs.uniform(24, 90); pts = [(sz * math.cos(b), sz * math.sin(b)) for b in sorted(rs.uniform(0, 6.28, 3))]
    SHARDS.append((a, rs.uniform(900, 2100), rs.uniform(-600, 200), pts, rs.uniform(-720, 720)))

def shake(t, t0, amp=18, d=.32):
    if t < t0 or t > t0 + d: return 0, 0
    k = (1 - (t - t0) / d) ** 2; return amp * k * math.sin((t - t0) * 90), amp * k * math.cos((t - t0) * 77)
def whip(f, t, t0, d=.16):
    # motion-blur streak around a cut at t0 (both sides)
    x = abs(t - t0) / d
    if x >= 1: return f
    k = int(80 * (1 - x)) * 2 + 1; return cv2.blur(f, (k, 1))

def scene1(t, f):  # hook / loop end: box left (tilted), «?» tag hanging right — still
    blit(f, T_TITLE, 430, 230)
    blit(f, BOX, 420, 820, 1, 1, 4)
    sw = 6 * math.sin(t * 1.6 + .9); cv2.line(f, (700, 1050), (760 + int(4 * sw), 1170), (60, 50, 60), 6, cv2.LINE_AA)
    blit(f, TAGQ, 770 + 8 * sw, 1320, 1.0, 1.0, -sw - 6)
def scene2(t, f):  # close on the tag: 980
    k = eio((t - T['s2']) / (T['hit'] - T['s2']))
    blit(f, BOXBG, 330, 480, 1.0 + .05 * k, .45, 4)
    blit(f, TAG980, 560, 1080, 1.0 + .07 * k, 1.0, 2 * math.sin(t * 1.4) - 3)
def scene3(t, f):  # shatter -> 850
    dt = t - T['hit']; dx, dy = shake(t, T['hit'])
    blit(f, BOXBG, 330 + dx, 480 + dy, 1.05, .4, 4)
    if dt < 1.1:
        for (a, v, vy, pts, rr) in SHARDS:
            x = 560 + math.cos(a) * v * dt; y = 1080 + math.sin(a) * v * dt + vy * dt + 1500 * dt * dt
            ang = math.radians(rr * dt); p = np.array([[x + px * math.cos(ang) - py * math.sin(ang), y + px * math.sin(ang) + py * math.cos(ang)] for px, py in pts], np.int32)
            al = max(0, 1 - dt / 1.1); ov = f.copy(); cv2.fillPoly(ov, [p], (50, 25, 210)); cv2.polylines(ov, [p], True, (255, 255, 255), 2, cv2.LINE_AA); f[:] = f * (1 - al * .85) + ov * al * .85
    blit(f, T_980s, 760 + dx, 760 + dy, 1, cl(dt / .2))
    if dt > .05: cv2.line(f, (660 + int(dx), 795), (860 + int(dx), 725), (50, 25, 210), 12, cv2.LINE_AA)
    blit(f, T_850, 560 + dx, 1110 + dy, 1.0 + .7 * (1 - ebk(dt / .28)), cl(dt / .06))
    if t > T['riyal']: blit(f, T_RIYAL, 620, 1450, 1.0 + .25 * (1 - ebk((t - T['riyal']) / .22)), cl((t - T['riyal']) / .1))
    if dt < .09: f[:] = f * (1 - (1 - dt / .09) * .75) + np.array([50, 25, 210], np.float32) * (1 - dt / .09) * .75
def scene4(t, f):  # 36 packs: number right, cards fanned left, box low-left
    dt = t - T['s4']
    blit(f, RAIK, 290, 760, 1, cl(dt / .3), 16 - 4 * eo(dt / .5)); blit(f, SIRC, 380, 900, 1, cl(dt / .3), 4 - 4 * eo(dt / .5))
    blit(f, BOXM, 330, 1420, 1, 1, 6)
    blit(f, T_36, 740, 800, 1.0 + .3 * (1 - ebk(dt / .3)), 1)
    blit(f, T_BAK, 740, 1150, 1, cl((dt - .25) / .15))
def scene5(t, f):  # gold card hero (cut on «ميغا»)
    dt = t - T['mega']; s = .96 + .06 * eio(dt / 2.2); rot = 5 - 8 * eio(dt / 2.2)
    blit(f, GOLD, 560, 880, s, 1, rot)
    sx = -300 + ((dt * 900) % 1700)
    band = np.zeros((H, W), np.float32); cv2.fillPoly(band, [np.array([[int(sx + 300), 380], [int(sx + 420), 380], [int(sx + 120), 1430], [int(sx), 1430]])], 1.0)
    band = cv2.GaussianBlur(band, (0, 0), 22)[..., None]
    m = np.zeros((H, W), np.float32); cv2.rectangle(m, (220, 400), (900, 1370), 1.0, -1); f[:] = f + band * m[..., None] * np.array([150, 230, 255], np.float32) * .6
    blit(f, P_HR, 560, 1520, 1, cl((dt - .4) / .2)); blit(f, T_MEGA, 560, 1670, 1, cl((dt - .6) / .2))
def grid(f, t, dt, sc=1.0, oy=0):
    B = C['beat']
    for i in range(6):
        r, c = divmod(i, 3); x, y = 540 + (c - 1) * 310 * sc, oy + (640 + r * 330) * sc; d0 = .1 + i * B / 2
        p = ebk((dt - d0) / .3); blit(f, BOXS, x, y - 500 * (1 - p), sc, cl((dt - d0) / .1))
def scene6(t, f):  # case: 6 boxes drop on beats
    dt = t - T['s5']
    blit(f, T_CASE, 300, 230, 1, 1); blit(f, T_6, 760, 240, 1, cl((dt - .2) / .2)); grid(f, t, dt)
def scene6b(t, f):  # tighter framing + price (cut on «بأربعة»)
    dt = t - T['price']; grid(f, t, 9, 1.0, -200)
    blit(f, T_4800, 560, 1350, 1.0 + .3 * (1 - ebk(dt / .25)), cl(dt / .1))
def scene6c(t, f):  # stamp alone (cut on «توفّر»)
    dt = t - T['save']; grid(f, t, 9, .75, 60)
    blit(f, T_4800, 540, 1450, .75, 1)
    k = ebk(dt / .2, 1.2); dx, dy = shake(t, T['save'], 14, .25); blit(f, STAMP, 540 + dx, 1180 + dy, 2.1 - .9 * k, cl(dt / .06), -8)
def scene7(t, f):  # site
    dt = t - T['s6']
    blit(f, LOGO, 540, 360, 1.0 + .15 * (1 - ebk(dt / .3))); blit(f, BOXM, 330, 820, 1, 1, 6)
    blit(f, T_SITE, 540, 1150, 1.0 + .2 * (1 - ebk(dt / .3)))
    if t > T['ship']: blit(f, T_SHIP, 560, 1300, 1, cl((t - T['ship']) / .2))
def scene7b(t, f):  # showroom close-up (cut on «زورنا»)
    dt = t - T['s6b']
    sh = (dt * 60) % 120
    for i in range(8):
        yl = int(460 + i * 120 + sh); cv2.line(f, (120, yl), (960, yl + 60), (170, 165, 175), 4, cv2.LINE_AA)
    for i in range(7):
        xl = int(100 + i * 150 + sh); cv2.line(f, (xl, 480), (xl + 60, 1320), (170, 165, 175), 4, cv2.LINE_AA)
    k = ebk((t - T['olaya']) / .35) if t > T['olaya'] else 0; blit(f, PIN, 540, 900 - 160 * (1 - k) + 12 * math.sin(t * 5), 2.0, .35 + .65 * cl((t - T['olaya']) / .1))
    blit(f, P_OLAYA, 540, 1250, 1.2 + .04 * math.sin(t * 6)); blit(f, T_ABHUR, 540, 1400, 1, cl((dt - .3) / .2))
T_OLAYA_BIG = text_sprite('العُليا سكوير', FL(190), fill=(255, 255, 255))
T_ABHUR_W = text_sprite('أبحر الجنوبية – جدة', FL(84), fill=(220, 255, 250))
def scene7c(t, f):  # cut on «العليا»: teal full card, name big
    dt = t - T['olaya2']; f[:] = np.array([120, 140, 20], np.float32) * (0.9 + 0.1 * math.sin(t * 3))
    blit(f, PIN, 540, 640 + 10 * math.sin(t * 6), 2.4); blit(f, T_OLAYA_BIG, 540, 980, 1.0 + .25 * (1 - ebk(dt / .3)))
    blit(f, T_ABHUR_W, 540, 1180, 1, cl((dt - .15) / .2))
T_GUESS = text_sprite('اكتب توقعك بالكومنتات', FL(100), fill=INK)
T_ANS = text_sprite('الجواب بأول تعليق', FL(130), fill=(255, 255, 255) if POP else CRIM)
T_SHARE1 = text_sprite('أرسله لخويك', FL(150), fill=INK); T_SHARE2 = text_sprite('اللي يجمع بوكيمون', FL(110), fill=(255, 220, 225) if POP else CRIM)
TAGQ_BIG = tag_sprite('؟')
def bubble_sprite():
    im = Image.new('RGBA', (360, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, 350, 230), 60, fill=(255, 255, 255), outline=INK, width=10); d.polygon([(80, 220), (150, 222), (70, 290)], fill=INK)
    for i in range(3): d.ellipse((95 + i * 65, 100, 135 + i * 65, 140), fill=CRIM)
    return to_bgra(im)
BUBBLE = bubble_sprite()
def arrow_sprite():
    im = Image.new('RGBA', (200, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(im); AC = (255, 255, 255) if POP else CRIM; d.rectangle((75, 10, 125, 150), fill=AC); d.polygon([(10, 140), (190, 140), (100, 250)], fill=AC); return to_bgra(im)
ARROW = arrow_sprite()
def share_sprite():
    im = Image.new('RGBA', (300, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(20, 140), (280, 30), (200, 280), (150, 170)], fill=INK); d.polygon([(150, 170), (280, 30), (165, 230)], fill=CRIM); return to_bgra(im)
SHARE = share_sprite()
def sceneQ(t, f):  # question: «اكتب توقعك بالكومنتات»
    dt = t - T['sq']; sw = 5 * math.sin(t * 2.2)
    blit(f, BOXM, 300, 620, 1, 1, 6); blit(f, TAGQ_BIG, 760, 640, 1.3 + .2 * (1 - ebk(dt / .3)), 1, -sw)
    blit(f, BUBBLE, 540, 1080, 1.0 + .25 * (1 - ebk((dt - .1) / .3)) + .03 * math.sin(t * 8), cl(dt / .1))
    blit(f, T_GUESS, 560, 1400, 1, 1)
def sceneQ2(t, f):  # «الجواب بأول تعليق» + arrow down to the comments
    dt = t - T['sq2']; blit(f, TAGQ_BIG, 540, 560, 1.6, 1, 4 * math.sin(t * 2))
    blit(f, T_ANS, 560, 1000, 1.0 + .25 * (1 - ebk(dt / .25))); blit(f, ARROW, 540, 1300 + 40 * abs(math.sin(t * 5)), 1)
def sceneSH(t, f):  # share trigger
    dt = t - T['sh']; blit(f, SHARE, 540, 640, 1.0 + .3 * (1 - ebk(dt / .3)), 1, 8 * math.sin(t * 3))
    blit(f, T_SHARE1, 560, 1000, 1, 1); blit(f, T_SHARE2, 560, 1180, 1, cl((dt - .5) / .2)); blit(f, GOLD, 820, 1500, .38, 1, 10)
def scene8(t, f):  # outro = hook frame (loop) + like/save/comment/follow
    scene1(t, f); dt = t - T['s7']
    blit(f, T_CMT, 560, 1560, 1, cl(dt / .2)); blit(f, T_LIKE, 560, 1680, 1, cl((dt - .2) / .2))
    blit(f, P_FOLLOW, 560, 1790, 1.0 + .05 * math.sin(t * 9), cl((dt - T['follow_off']) / .2))

def scene8b(t, f):  # last card (cut on «وتابعنا»): logo + follow
    dt = t - T['s8']
    if POP:
        ov = f.copy()
        for i in range(16):
            an = t * 1.6 + i * math.pi / 8; cv2.line(ov, (540, 760), (int(540 + 1400 * math.cos(an)), int(760 + 1400 * math.sin(an))), (255, 255, 255), 26, cv2.LINE_AA)
        f[:] = f * .78 + ov * .22
    blit(f, LOGO, 540, 760 + 14 * math.sin(t * 7), 1.0 + .12 * (1 - ebk(dt / .3)), 1, 3 * math.sin(t * 5))
    blit(f, P_FOLLOW, 540, 1080, 1.4 + .12 * abs(math.sin(t * 7))); blit(f, T_LIKE, 540, 1260, 1)

def scene4b(t, f): scene4(t, f)
def scene5b(t, f): scene5(t, f)
def sceneQb(t, f): sceneQ(t, f)
SC_DEFAULT = [('s1', scene1), ('s2', scene2), ('hit', scene3), ('s4', scene4), ('mega', scene5), ('s5', scene6), ('price', scene6b), ('save', scene6c), ('s6', scene7), ('s6b', scene7b), ('olaya2', scene7c), ('s7', scene8), ('s8', scene8b)]
SC = [(x.split(':')[0], globals()[x.split(':')[1]]) for x in C['sc']] if 'sc' in C else SC_DEFAULT
WHIPS = [T[k] for k in C.get('whips', ['s4', 's5'])]
def render(t):
    f = background(t, .75 if T['s2'] <= t < T['hit'] else 1.0)
    cur, st = SC[0][1], 0
    for k, fn in SC:
        if t >= T[k]: cur, st = fn, T[k]
    if POP:
        f = POP_BG.get(cur.__name__, BG_RED).copy() * VIG
        for (x, y, rr, ph, sp) in DUST[:40]:
            y2 = (y - t * 40 * sp) % H; cv2.circle(f, (int(x + 30 * math.sin(t * .9 + ph)), int(y2)), int(rr * 1.2), (255, 255, 255), -1, cv2.LINE_AA) if t >= T['s4'] else None
    if cur is scene1: blit(f, T_BKM, 600, 1640)
    cur(t, f)
    # camera: slow motivated push-in per shot + drift (never a frozen frame)
    z = 1 + .045 * (t - st) + (.02 * (t - T['s7']) if t >= T['s7'] else 0); px = 10 * math.sin(t * .8)
    if cur is scene1: z, px = 1 + .03 * t, 0.0  # calm hook: slow push-in only
    if cur is scene8b: z = 1 + .06 * (t - st)
    M = np.float32([[z, 0, (1 - z) * 540 + px], [0, z, (1 - z) * 960]]); f = cv2.warpAffine(f, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    for w in WHIPS: f = whip(f, t, w)
    return np.clip(f, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'frames':
        for t in [float(x) for x in sys.argv[2].split(',')]: cv2.imwrite(f'/home/claude/work/f_{t:.1f}.jpg', render(t))
        sys.exit()
    a, b = RANGE or (0, TOTAL); n = int(round((b - a) * FPS))
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    for i in range(n): p.stdin.write(render(a + i / FPS).tobytes())
    p.stdin.close(); p.wait(); print('ok', OUT, n)
