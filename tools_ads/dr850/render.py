import sys, json, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
D = '/home/claude/dr850/'
FD = '/home/claude/htr-videos/fetch/'
C = json.load(open(D + 'cues.json'))
T = C['t']; TOTAL = C['TOTAL']
def FL(s): return ImageFont.truetype(FD + 'font_lalezar.ttf', s)
def FB(s): return ImageFont.truetype(FD + 'font_bungee.ttf', s)
def FA(s): return ImageFont.truetype(FD + 'font_anton.ttf', s)
PURP = (142, 117, 255); TEAL = (46, 196, 182); LIL = (200, 180, 255); WHITE = (255, 255, 255); DEEP = (14, 8, 34); PINK = (255, 90, 170)

def cl(x): return min(max(x, 0.0), 1.0)
def eo(x): x = cl(x); return 1 - (1 - x) ** 3
def ebk(x, s=1.9): x = cl(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def ein(x): x = cl(x); return x ** 3
def env(t, a, d): return max(0.0, 1 - (t - a) / d) if t >= a else 0.0
def win(t, a, b, fi=.18, fo=.18): return eo((t - a) / fi) * (1 - ein((t - (b - fo)) / fo))
def to_bgra(im): a = np.array(im.convert('RGBA')); return a[..., [2, 1, 0, 3]].copy()

def text_sprite(s, font, fill=WHITE, grad=None, stroke=0, stroke_fill=DEEP, glow=None, glow_r=18, pad=40):
    d0 = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    bb = d0.textbbox((0, 0), s, font=font, stroke_width=stroke)
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    ox, oy = pad - bb[0], pad - bb[1]
    mask = Image.new('L', (w, h), 0); ImageDraw.Draw(mask).text((ox, oy), s, font=font, fill=255)
    smask = Image.new('L', (w, h), 0); ImageDraw.Draw(smask).text((ox, oy), s, font=font, fill=255, stroke_width=stroke, stroke_fill=255)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if glow:
        g = Image.new('RGBA', (w, h), glow + (0,)); g.putalpha(smask.filter(ImageFilter.GaussianBlur(glow_r)).point(lambda v: min(255, int(v * 1.6))))
        out = Image.alpha_composite(out, g)
    sh = Image.new('RGBA', (w, h), (5, 0, 20, 0)); m2 = Image.new('L', (w, h), 0); m2.paste(smask, (0, 10)); sh.putalpha(m2.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * .7)))
    out = Image.alpha_composite(out, sh)
    if stroke:
        st = Image.new('RGBA', (w, h), stroke_fill + (0,)); st.putalpha(smask); out = Image.alpha_composite(out, st)
    if grad:
        y = np.linspace(0, 1, h)[:, None]; c0, c1 = np.array(grad[0], float), np.array(grad[1], float)
        col = np.broadcast_to((c0[None, :] * (1 - y) + c1[None, :] * y)[:, None, :], (h, w, 3))
        fillim = Image.fromarray(np.ascontiguousarray(col).astype(np.uint8), 'RGB').convert('RGBA')
    else:
        fillim = Image.new('RGBA', (w, h), fill + (255,))
    fillim.putalpha(mask); out = Image.alpha_composite(out, fillim)
    return to_bgra(out)

def pill(s, font, bg, fg=WHITE, padx=48, pady=22, border=None):
    d0 = ImageDraw.Draw(Image.new('RGBA', (10, 10))); bb = d0.textbbox((0, 0), s, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    w, h = tw + 2 * padx, th + 2 * pady
    im = Image.new('RGBA', (w + 60, h + 60), (0, 0, 0, 0))
    gl = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(gl).rounded_rectangle((30, 36, 30 + w, 36 + h), h // 2, fill=bg + (170,)); gl = gl.filter(ImageFilter.GaussianBlur(14))
    im = Image.alpha_composite(im, gl); d = ImageDraw.Draw(im)
    d.rounded_rectangle((30, 30, 30 + w, 30 + h), h // 2, fill=bg + (255,), outline=border, width=5 if border else 0)
    d.text((30 + padx - bb[0], 30 + pady - bb[1]), s, font=font, fill=fg)
    return to_bgra(im)

def img_sprite(path, w, glow=PURP, glow_r=40, rounded=0):
    im = Image.open(path).convert('RGBA'); s = w / im.width; im = im.resize((w, int(im.height * s)), Image.LANCZOS)
    if rounded:
        m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), rounded, fill=255)
        a = np.minimum(np.array(im.split()[3]), np.array(m)); im.putalpha(Image.fromarray(a))
    pad = glow_r * 2; c = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    g = Image.new('RGBA', c.size, glow + (0,)); ga = Image.new('L', c.size, 0); ga.paste(im.split()[3], (pad, pad))
    g.putalpha(ga.filter(ImageFilter.GaussianBlur(glow_r)).point(lambda v: min(255, int(v * 1.3))))
    c = Image.alpha_composite(c, g); c.alpha_composite(im, (pad, pad)); return to_bgra(c)

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
    sp = spr[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32)
    al = sp[..., 3:4] / 255 * a
    f[ya:yb, xa:xb] = f[ya:yb, xa:xb] * (1 - al) + sp[..., :3] * al

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
def radial(cx, cy, r): return np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)))[..., None]
BASE = np.zeros((H, W, 3), np.float32); BASE[:] = (34, 8, 14)
BASE += radial(540, 700, 700) * np.array([90, 40, 50], np.float32)
rng = np.random.default_rng(3)
STARS = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1.5, 4), rng.uniform(0, 6.28), rng.uniform(.3, 1)) for _ in range(90)]

def background(t, hue):
    f = BASE.copy()
    a = radial(540 + 260 * math.sin(t * .7), 650 + 120 * math.cos(t * .5), 520) * np.array(hue[0][::-1], np.float32) * .55
    b = radial(540 - 300 * math.sin(t * .6), 1350, 560) * np.array(hue[1][::-1], np.float32) * .45
    f += a + b
    # perspective grid floor
    hz = 1240
    for i in range(-12, 13):
        x0 = 540 + i * 70; x1 = 540 + i * 380
        cv2.line(f, (int(x0), hz), (int(x1), H), (120, 70, 60), 2, cv2.LINE_AA)
    off = (t * 0.6) % 1
    for k in range(10):
        z = (k + off) / 10; y = int(hz + (H - hz) * z ** 2.2)
        cv2.line(f, (0, y), (W, y), (110, 60, 55), 2, cv2.LINE_AA)
    for (x, y, r, ph, sp) in STARS:
        yy2 = (y - t * 60 * sp) % H; v = .5 + .5 * math.sin(t * 3 * sp + ph)
        cv2.circle(f, (int(x), int(yy2)), int(r), (255 * v, 220 * v, 230 * v), -1, cv2.LINE_AA)
    return f

# --- sprites
BOX = img_sprite(D + 'box.png', 760, glow=PURP, glow_r=50)
BOXS = img_sprite(D + 'box.png', 300, glow=PURP, glow_r=18)
HR = img_sprite(D + 'hr.png', 600, glow=(255, 200, 80), glow_r=55, rounded=26)
SIR = img_sprite(D + 'sir.png', 600, glow=(255, 120, 60), glow_r=55, rounded=26)
LOGO = img_sprite('/home/claude/htr-videos/tools_challenges/htr_logo.png', 640, glow=PURP, glow_r=30)
P850 = text_sprite('850', FB(270), grad=((255, 255, 255), LIL), stroke=10, glow=PURP, glow_r=30)
RIYAL = text_sprite('ريال بس!', FL(130), fill=WHITE, stroke=8, glow=TEAL)
OLD = text_sprite('900', FB(110), fill=(190, 180, 210), stroke=6)
TOP1 = text_sprite('DELTA REIGN', FB(96), grad=((255, 255, 255), LIL), stroke=6, glow=PURP)
TOP2 = text_sprite('BOOSTER BOX', FA(84), fill=(220, 210, 255), stroke=4)
PACKS = pill('36 باك', FL(110), PURP)
FULLBOX = pill('بوكس كامل', FL(96), TEAL, fg=DEEP)
BADGE = pill('850 ريال', FL(78), PURP, border=WHITE)
L_HR1 = text_sprite('MEGA RAYQUAZA ex', FB(66), fill=WHITE, stroke=5)
L_HR2 = text_sprite('HYPER RARE', FB(60), grad=((255, 230, 140), (255, 170, 60)), stroke=5, glow=(255, 160, 40))
L_SIR2 = text_sprite('SUPER ILLUSTRATION RARE', FB(48), grad=((255, 255, 255), LIL), stroke=5, glow=PURP)
CHANCE = pill('ممكن تطلع لك', FL(84), (40, 30, 80), border=LIL)
CASE_T = text_sprite('CASE', FB(110), grad=((255, 255, 255), LIL), stroke=7, glow=PURP)
CASE_T2 = text_sprite('كامل (6 بوكسات)', FL(84), fill=WHITE, stroke=6)
P4800 = text_sprite('4,800', FB(200), grad=((255, 255, 255), LIL), stroke=9, glow=PURP)
RIY2 = text_sprite('ريال', FL(110), fill=WHITE, stroke=7)
SAVE = pill('وفّر 300 ريال', FL(110), TEAL, fg=DEEP)
CTA1 = text_sprite('اطلب من موقع HTR', FL(120), fill=WHITE, stroke=8, glow=PURP)
URL = text_sprite('htrtcg.com', FB(92), grad=(TEAL, (140, 255, 230)), stroke=5, glow=TEAL)
DOOR = pill('يوصلك لين باب بيتك', FL(96), PURP, border=WHITE)
STOCK = pill('متوفر الحين', FL(80), (30, 160, 90))
ASK = text_sprite('أيّ وحدة تبيها؟', FL(130), fill=WHITE, stroke=8, glow=PINK)
N1 = pill('1', FB(90), PURP, border=WHITE, padx=40, pady=10)
N2 = pill('2', FB(90), TEAL, fg=DEEP, border=WHITE, padx=40, pady=10)
L_HR2s = text_sprite('HYPER RARE', FB(44), grad=((255, 230, 140), (255, 170, 60)), stroke=4, glow=(255, 160, 40))
L_SIRs = text_sprite('SUPER ILLUSTRATION', FB(34), grad=((255, 255, 255), LIL), stroke=4, glow=PURP)
L_RAY = text_sprite('MEGA RAYQUAZA ex', FB(56), fill=WHITE, stroke=5)
VS = text_sprite('VS', FB(150), grad=((255, 255, 255), PINK), stroke=8, glow=PINK)
CMT = pill('اكتب جوابك بالكومنتات', FL(88), PINK, fg=WHITE, border=WHITE)

HUE_A = (PURP, TEAL); HUE_B = ((255, 170, 60), PINK); HUE_C = (TEAL, PURP)

def render(t):
    s2, s3, s4, s5, s6 = T['box'], T['hr'], T['sir'], T['case'], T['cta']
    hue = HUE_B if s3 <= t < s5 else (HUE_C if t >= s6 else HUE_A)
    f = background(t, hue)
    hits = [s2, T['packs'], s3, s4, T['q'], T['one'], T['two'], T['cmt'], s5, T['save'], s6]
    pun = sum(env(t, h, .22) for h in hits)
    cam = 1 + .045 * pun
    shx = 10 * pun * math.sin(t * 90); shy = 8 * pun * math.cos(t * 77)
    def B(spr, cx, cy, s=1, a=1, rot=0): blit(f, spr, 540 + (cx - 540) * cam + shx, 960 + (cy - 960) * cam + shy, s * cam, a, rot)
    # ---- scene 1+2: box + price (0 .. s3)
    if t < s3 + .3:
        a = 1 - eo((t - s3) / .3)
        ent = ebk((t + .3) / .45)
        cut = 1 if t >= s2 else 0
        bs = (.82 * (.6 + .4 * ent) if not cut else 1.02) * (1 + .015 * math.sin(t * 2))
        by = (760 if not cut else 700) + 12 * math.sin(t * 1.4)
        B(BOX, 540, by, bs, a, (0 if not cut else 2 * math.sin(t * 1.3)))
        # top title
        B(TOP1, 540, 200 - 160 * (1 - eo((t + .2) / .3)), 1, a)
        B(TOP2, 540, 305, 1, a * eo((t + .1) / .3))
        # price block (frame 1 visible)
        pa = a if t < s2 else 0
        ps = ebk(cl((t + .3) / .4))
        B(P850, 540, 1470, ps, pa)
        B(RIYAL, 540, 1680, ebk(cl((t + .1) / .3)), pa)
        oa = pa * eo((t + .2) / .2)
        B(OLD, 880, 1290, .75, oa * .9)
        cv2.line(f, (int(815+shx), int(1300+shy)), (int(945+shx), int(1280+shy)), (90, 60, 255), 12, cv2.LINE_AA) if oa > .5 else None
        # scene 2 chips
        if t >= s2:
            B(FULLBOX, 540, 1380, ebk((t - s2) / .3), a)
            B(PACKS, 540, 1560, ebk((t - T['packs']) / .3) if t >= T['packs'] else 0, a)
            B(BADGE, 860, 470, ebk((t - s2 - .2) / .3), a)
    # ---- scene 3/4: pick-one challenge (VS)
    if s3 - .1 <= t < s5 + .3:
        a = 1 - eo((t - s5) / .3)
        q = T['q']
        if t < q:
            B(CHANCE, 540, 260, ebk((t - s3) / .3), a)
        else:
            B(ASK, 540, 250, ebk((t - q) / .35) * (1 + .03 * math.sin(t * 6)), a)
        B(BADGE, 540, 1800, 1, a)
        # card 1
        k1 = eo((t - s3) / .4)
        pul1 = 1 + .12 * env(t, T['one'], .5)
        B(HR, 280 - 600 * (1 - k1), 860, .74 * pul1 + .02 * math.sin(t * 2.5), a, -12 * (1 - k1) - 4 + 2 * math.sin(t * 2))
        B(N1, 280, 470, ebk((t - s3 - .2) / .3) * pul1, a)
        B(L_HR2s, 280, 1350, ebk((t - s3 - .3) / .3), a)
        # card 2
        if t >= s4:
            k2 = eo((t - s4) / .4)
            pul2 = 1 + .12 * env(t, T['two'], .5)
            B(SIR, 800 + 600 * (1 - k2), 860, .74 * pul2 + .02 * math.sin(t * 2.5 + 1), a, 12 * (1 - k2) + 4 - 2 * math.sin(t * 2))
            B(N2, 800, 470, ebk((t - s4 - .2) / .3) * pul2, a)
            B(L_SIRs, 800, 1350, ebk((t - s4 - .3) / .3), a)
        B(L_RAY, 540, 1460, ebk((t - s3 - .4) / .3), a)
        if t >= q:
            B(VS, 540, 860, ebk((t - q) / .3) * (1 + .08 * math.sin(t * 7)), a)
        if t >= T['cmt']:
            B(CMT, 540, 1610, ebk((t - T['cmt']) / .3) * (1 + .05 * math.sin(t * 8)), a)
    # ---- scene 5: case
    if s5 - .1 <= t < s6 + .3:
        a = 1 - eo((t - s6) / .3)
        B(CASE_T, 540, 230, ebk((t - s5) / .3), a)
        B(CASE_T2, 540, 360, ebk((t - s5 - .1) / .3), a)
        for i in range(6):
            r, c = divmod(i, 3); d = s5 + .08 * i
            k = ebk((t - d) / .35)
            B(BOXS, 210 + c * 330, 680 + r * 380 - 200 * (1 - eo((t - d) / .35)), .1 + .9 * k if t >= d else 0, a, 3 * math.sin(t * 2 + i))
        B(P4800, 420, 1250, ebk((t - s5 - .3) / .35), a)
        B(RIY2, 880, 1275, ebk((t - s5 - .45) / .3), a)
        B(SAVE, 540, 1500, ebk((t - T['save']) / .3) * (1 + .06 * math.sin(t * 9)) if t >= T['save'] else 0, a)
    # ---- scene 6: CTA
    if t >= s6 - .1:
        k = ebk((t - s6) / .4)
        B(LOGO, 540, 430, k)
        B(BOXS, 540, 820, ebk((t - s6 - .1) / .4) * 1.3, 1, 3 * math.sin(t * 2))
        B(BADGE, 540, 1080, ebk((t - s6 - .2) / .3))
        B(CTA1, 540, 1250, ebk((t - s6 - .1) / .35))
        B(URL, 540, 1380, ebk((t - s6 - .35) / .35))
        B(DOOR, 540, 1560, ebk((t - T['door']) / .35) * (1 + .05 * math.sin(t * 8)) if t >= T['door'] else 0)
        B(STOCK, 540, 1730, ebk((t - T['door'] - .4) / .3) if t >= T['door'] + .4 else 0)
    # flash on scene changes
    fl = max(env(t, s3, .15), env(t, s5, .15), env(t, s6, .15)) * .55
    if fl > 0: f = f * (1 - fl) + 255 * fl
    # vignette
    f *= VIG
    return np.clip(f, 0, 255).astype(np.uint8)

VIG = (1 - .55 * np.clip((((xx - 540) / 760) ** 2 + ((yy - 960) / 1150) ** 2), 0, 1) ** 1.5)[..., None]

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'still':
        ts = [float(x) for x in sys.argv[2].split(',')]
        ims = [Image.fromarray(render(t)[..., ::-1]).resize((270, 480)) for t in ts]
        sheet = Image.new('RGB', (270 * len(ims), 480))
        for i, im in enumerate(ims): sheet.paste(im, (270 * i, 0))
        sheet.save(D + 'sheet.png')
    else:
        a, b = int(sys.argv[2]), int(sys.argv[3])
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', D + f'part_{a}.mp4'], stdin=subprocess.PIPE)
        for i in range(a, b):
            t = i / FPS
            fr = render(t).astype(np.float32)
            t2 = (i + .5) / FPS
            fr = (fr + render(t2).astype(np.float32)) / 2
            p.stdin.write(fr.astype(np.uint8).tobytes())
        p.stdin.close(); p.wait()
