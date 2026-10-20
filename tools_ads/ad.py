import sys, json, subprocess, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
C = json.load(open('/home/claude/ad1/cues.json'))
VO = C['VO']; TOTAL = C['TOTAL']
T = {k: v + VO for k, v in C['t'].items()}
FD = '/home/claude/htr-videos/fetch/'
def FL(s): return ImageFont.truetype(FD + 'font_lalezar.ttf', s)
def FB(s): return ImageFont.truetype(FD + 'font_bungee.ttf', s)
PURP = (142, 117, 255); TEAL = (46, 196, 182); LIL = (200, 180, 255); WHITE = (255, 255, 255); DEEP = (14, 8, 34); WA = (37, 211, 102)
rng = np.random.default_rng(5)

def eo(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def eio(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def ebk(x, s=1.9): x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def env(t, a, d): return max(0.0, 1 - (t - a) / d) if t >= a else 0.0
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

def pill(s, font, bg, fg=WHITE, padx=48, pady=22, border=None, icon=None):
    d0 = ImageDraw.Draw(Image.new('RGBA', (10, 10))); bb = d0.textbbox((0, 0), s, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]; iw = int(th * 1.3) + 24 if icon else 0
    w, h = tw + 2 * padx + iw, th + 2 * pady
    im = Image.new('RGBA', (w + 60, h + 60), (0, 0, 0, 0))
    gl = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(gl).rounded_rectangle((30, 36, 30 + w, 36 + h), h // 2, fill=bg + (170,)); gl = gl.filter(ImageFilter.GaussianBlur(14))
    im = Image.alpha_composite(im, gl); d = ImageDraw.Draw(im)
    d.rounded_rectangle((30, 30, 30 + w, 30 + h), h // 2, fill=bg + (255,), outline=border, width=5 if border else 0)
    d.text((30 + padx - bb[0] + iw, 30 + pady - bb[1]), s, font=font, fill=fg)
    if icon:
        r = int(th * .62); cx, cy = 30 + padx + r, 30 + h // 2
        wa_icon(d, cx, cy, r, fg, bg)
    return to_bgra(im)

def wa_icon(d, cx, cy, r, fg, bg):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=fg, width=max(4, r // 6))
    d.polygon([(cx - r * .75, cy + r * .5), (cx - r * 1.05, cy + r * 1.1), (cx - r * .25, cy + r * .9)], fill=fg)
    # handset
    k = r * .42
    d.rounded_rectangle((cx - k * 1.1, cy - k * 1.0, cx - k * .3, cy - k * .1), int(k * .3), fill=fg)
    d.rounded_rectangle((cx + k * .2, cy + k * .4, cx + k * 1.1, cy + k * 1.1), int(k * .3), fill=fg)
    d.line((cx - k * .75, cy - k * .3, cx + k * .55, cy + k * .8), fill=fg, width=int(k * .55))

def blit(f, spr, cx, cy, s=1.0, a=1.0, rot=0.0):
    if a <= 0.003 or s <= 0.01: return
    h0, w0 = spr.shape[:2]
    if abs(rot) > .01 or abs(s - 1) > .001:
        M = cv2.getRotationMatrix2D((w0 / 2, h0 / 2), rot, s)
        cw, ch = int(w0 * s * 1.5 + 4), int(h0 * s * 1.5 + 4)
        M[0, 2] += cw / 2 - w0 / 2; M[1, 2] += ch / 2 - h0 / 2
        spr = cv2.warpAffine(spr, M, (cw, ch), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    h, w = spr.shape[:2]; x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb: return
    sp = spr[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32)
    al = sp[..., 3:4] / 255.0 * a
    reg = f[ya:yb, xa:xb]; reg[:] = reg * (1 - al) + sp[..., :3] * al

def persp(spr, ang, s=1.0):
    h, w = spr.shape[:2]; a = math.radians(ang); fo = 1400.0; pts = []
    for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        X, Z = x * math.cos(a), x * math.sin(a); k = fo / (fo + Z); pts.append((X * k * s, y * k * s))
    pts = np.float32(pts); mn = pts.min(0); pts -= mn - 10
    ow, oh = int(pts[:, 0].max() + 10), int(pts[:, 1].max() + 10)
    M = cv2.getPerspectiveTransform(np.float32([(0, 0), (w, 0), (w, h), (0, h)]), pts)
    return cv2.warpPerspective(spr, M, (ow, oh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

def prod(name, w, glow=PURP):
    im = Image.open(f'/home/claude/ad1/img/{name}.png').convert('RGBA')
    im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    pad = 70; c = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    gl = Image.new('RGBA', c.size, glow + (0,)); m = Image.new('L', c.size, 0); m.paste(im.getchannel('A'), (pad, pad))
    gl.putalpha(m.filter(ImageFilter.GaussianBlur(30)).point(lambda v: int(v * .8)))
    c = Image.alpha_composite(c, gl); c.alpha_composite(im, (pad, pad)); return to_bgra(c)

# ---------- assets ----------
P = {k: prod(k, w, g) for k, w, g in [
    ('chaos_box', 470, PURP), ('op16', 560, TEAL), ('destined_box', 400, PURP), ('pitch', 360, TEAL), ('chaos_etb', 470, LIL),
    ('op17', 430, TEAL), ('greninja', 540, PURP), ('naruto', 300, TEAL), ('chaos_pack', 330, PURP), ('po', 470, TEAL)]}
CAR = ['destined_box', 'pitch', 'op17', 'greninja', 'naruto', 'chaos_etb']
S = dict(
    htr=text_sprite('HTR', FB(300), grad=(WHITE, LIL), stroke=12, stroke_fill=DEEP, glow=PURP, glow_r=34),
    tcg=text_sprite('TCG', FB(120), grad=(TEAL, (120, 240, 230)), stroke=8, stroke_fill=DEEP, glow=TEAL),
    q1=text_sprite('تدوّر على', FL(140), glow=PURP),
    q2=text_sprite('بوكسات؟', FL(210), grad=(WHITE, LIL), glow=PURP, glow_r=26),
    pk=text_sprite('POKÉMON', FB(96), grad=(WHITE, LIL), stroke=7, stroke_fill=DEEP, glow=PURP),
    op=text_sprite('ONE PIECE', FB(96), grad=(WHITE, (150, 240, 230)), stroke=7, stroke_fill=DEEP, glow=TEAL),
    new1=text_sprite('كل جديد', FL(180), glow=TEAL, glow_r=24),
    new2=text_sprite('عالم الـ', FL(130), grad=(WHITE, LIL), glow=PURP),
    tcg2=text_sprite('TCG', FB(110), grad=(TEAL, (150, 240, 230)), stroke=6, stroke_fill=DEEP, glow=TEAL),
    w_box=text_sprite('بوكسات', FL(200), grad=(WHITE, LIL), glow=PURP, glow_r=26),
    w_pack=text_sprite('باكات', FL(200), grad=(WHITE, (150, 240, 230)), glow=TEAL, glow_r=26),
    w_new=text_sprite('كل إصدار جديد', FL(150), glow=PURP, glow_r=24),
    ship1=text_sprite('نشحن لك', FL(190), glow=TEAL, glow_r=24),
    ship2=pill('لكل مناطق السعودية', FL(80), (40, 24, 90), border=TEAL + (255,)),
    talk=text_sprite('كلّمنا', FL(220), grad=(WHITE, (170, 255, 200)), glow=WA, glow_r=30),
    btn=pill('واتساب الحين', FL(92), WA, fg=WHITE, padx=60, pady=26, icon=True),
    phone=text_sprite('056 246 4664', FB(70), grad=(WHITE, LIL), stroke=5, stroke_fill=DEEP, glow=PURP, glow_r=12),
    book=text_sprite('واحجز بوكسك!', FL(120), glow=PURP),
    htr_sm=text_sprite('HTR TCG', FB(110), grad=(WHITE, LIL), stroke=7, stroke_fill=DEEP, glow=PURP, glow_r=22),
    handle=text_sprite('@hatar_tcg', FB(54), fill=LIL),
    jed=text_sprite('جدة', FL(64), fill=LIL),
    wm=text_sprite('HTR', FB(64), grad=(WHITE, LIL), stroke=4, stroke_fill=DEEP, glow=PURP, glow_r=10),
)
CHIPS = [pill(s, FL(52), c) for s, c in (('بوكيمون', (70, 50, 150)), ('ون بيس', (20, 110, 105)))]

# ---------- background ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
BASE = np.zeros((H, W, 3), np.float32)
top, bot = np.array(DEEP[::-1], np.float32), np.array((30, 12, 56)[::-1], np.float32)
k = (yy / H)[..., None]; BASE[:] = top * (1 - k) + bot * k
def radial(cx, cy, r): return np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)))[..., None]
GP = radial(W * .5, H * .42, 640) * np.array(PURP[::-1], np.float32)
GT = radial(W * .85, H * .85, 520) * np.array(TEAL[::-1], np.float32)
GW = radial(W * .5, H * .55, 700) * np.array(WA[::-1], np.float32)
# perspective grid floor
GRID = np.zeros((H, W), np.float32)
hor = H * .66
for i in range(1, 30):
    z = i / 30; y = hor + (H - hor) * (z ** 2.2)
    if y < H: GRID[int(y):int(y) + 2, :] = 1 * z
for j in range(-14, 15):
    x1 = W / 2 + j * 160
    cv2.line(GRID, (int(W / 2 + j * 12), int(hor)), (int(x1 * 1 + (x1 - W / 2) * 2), H), 0.7, 2)
GRID = cv2.GaussianBlur(GRID, (0, 0), 1.2)[..., None] * np.array(LIL[::-1], np.float32) * .22
STARS = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(2, 6), rng.uniform(0, 6.28), rng.uniform(1, 3), rng.uniform(20, 70)) for _ in range(80)]
BEAT = 60 / 124
def background(t):
    pulse = env(t % BEAT, 0, BEAT * .7)
    wa = eio((t - T['cta'] + .2) / .4)
    f = BASE + GP * (.3 + .08 * pulse) * (1 - .6 * wa) + GT * .35 + GW * .45 * wa
    gs = (t * 160) % 60
    g = np.roll(GRID, int(gs), axis=0) if True else GRID
    f = f + g * (1 + .8 * pulse)
    f = np.clip(f, 0, 255).astype(np.uint8)
    for x, y, r, ph, sp, vy in STARS:
        yy_ = (y - vy * t) % H; a = .4 + .6 * abs(math.sin(t * sp + ph))
        cv2.circle(f, (int(x), int(yy_)), int(r), (255, 235, 245), -1, cv2.LINE_AA) if a > .7 else None
    return f

HITS = [T['hook'], T['pk'], T['new'], T['box'], T['pack'], T['rel'], T['ship'], T['cta'], T['btn']]
def render(t):
    f = background(t).astype(np.float32)
    sh = sum(env(t, h, .25) for h in HITS) * 12
    # intro HTR slam
    if t < T['hook'] + .1:
        k = ebk(t / .35); out = eo((t - T['hook'] + .3) / .3)
        blit(f, S['htr'], W / 2, H * .43, (2.2 - 1.2 * eo(t / .3)) * (1 - .4 * out), min(1, t / .1) * (1 - out))
        blit(f, S['tcg'], W / 2, H * .53, ebk((t - .2) / .3), 1 - out)
    if T['hook'] - .05 < t < T['cta'] - .1:
        blit(f, S['wm'], 130, 110, 1, min(1, (t - T['hook']) / .3) * .9)
    # S1 hook: تدوّر على بوكسات؟ + pokemon / one piece
    if T['hook'] <= t < T['new'] + .2:
        lt = t - T['hook']; out = eio((t - T['new'] + .1) / .3)
        blit(f, S['q1'], W / 2 + 500 * (1 - eo(lt / .3)), H * .16 - 600 * out, 1, eo(lt / .2))
        if t > T['boxq']:
            k = t - T['boxq']; blit(f, S['q2'], W / 2, H * .25 - 600 * out, 1 + 1.4 * (1 - eo(k / .18)), min(1, k / .08))
        if t > T['pk']:
            k = t - T['pk']; x = W * .3 - 700 * (1 - eo(k / .4)) - 900 * out
            blit(f, P['chaos_box'], x, H * .45 + 14 * math.sin(t * 2), 1, 1, 12 * (1 - eo(k / .4)) - 4)
            blit(f, S['pk'], x, H * .61, ebk(k / .35) * .8, 1)
        if t > T['op']:
            k = t - T['op']; x = W * .72 + 700 * (1 - eo(k / .4)) + 900 * out
            blit(f, P['op16'], x, H * .72 + 14 * math.sin(t * 2 + 1), 1, 1, -12 * (1 - eo(k / .4)) + 4)
            blit(f, S['op'], x - 40, H * .83, ebk(k / .35) * .72, 1)
    # S2 carousel: كل جديد عالم TCG
    if T['new'] - .1 <= t < T['box'] + .15:
        lt = t - T['new']; out = eio((t - T['box'] + .05) / .25)
        n = len(CAR); spin = lt * 1.15 + 1.6 * (1 - eo(lt / .6))
        items = []
        for i, nm in enumerate(CAR):
            a = 2 * math.pi * i / n + spin; z = math.cos(a); x = W / 2 + math.sin(a) * 400
            items.append((z, x, nm, a))
        for z, x, nm, a in sorted(items):
            s = (.62 + .38 * (z + 1) / 2) * eo(lt / .35);
            spr = persp(P[nm], -math.degrees(math.sin(a)) * 35, s)
            blit(f, spr, x, H * .53 + (1 - z) * -40 + 1400 * out, 1, .35 + .65 * (z + 1) / 2)
        blit(f, S['new1'], W / 2, H * .17 - 800 * out, 1 + 1.2 * (1 - eo(lt / .18)), min(1, lt / .08))
        if t > T['world']:
            k = t - T['world']; blit(f, S['new2'], W / 2 + 130 + 600 * (1 - eo(k / .3)), H * .27 - 800 * out, 1, eo(k / .2)); blit(f, S['tcg2'], W / 2 - 170 - 600 * (1 - eo(k / .3)), H * .27 - 800 * out, 1, eo(k / .2))
    # S3 word slams بوكسات / باكات / كل إصدار جديد
    if T['box'] <= t < T['ship'] + .15:
        out = eio((t - T['ship'] + .05) / .25)
        for key, wk, pk, side in (('box', 'w_box', 'chaos_etb', -1), ('pack', 'w_pack', 'chaos_pack', 1)):
            if t >= T[key]:
                nxt = T['pack'] if key == 'box' else T['rel']
                k = t - T[key]; leave = eio((t - nxt + .02) / .22)
                blit(f, P[pk], W / 2 + side * 900 * leave, H * .47 + 10 * math.sin(t * 3), ebk(k / .4) * (1 + .03 * math.sin(t * 6)), 1 - leave, side * -5)
                blit(f, S[wk], W / 2 - side * 900 * leave, H * .2, 1 + 1.6 * (1 - eo(k / .16)), min(1, k / .06) * (1 - leave))
        if t >= T['rel']:
            k = t - T['rel']
            for i, nm in enumerate(['pitch', 'po', 'destined_box']):
                kk = eo((k - i * .08) / .4); x = W / 2 + (i - 1) * 320
                blit(f, P[nm], x, H * .5 + 900 * (1 - kk) + 1400 * out + (40 if i != 1 else -20), .78 if i != 1 else .95, 1, (i - 1) * 8 * kk)
            blit(f, S['w_new'], W / 2, H * .2 - 900 * out, 1 + 1.2 * (1 - eo(k / .18)), min(1, k / .08))
            for i, c in enumerate(CHIPS):
                if k > .35 + i * .1: blit(f, c, W / 2 + (.5 - i) * 300, H * .8 + 1400 * out, ebk((k - .35 - i * .1) / .3), 1)
    # S4 shipping
    if T['ship'] - .05 <= t < T['cta'] + .15:
        lt = t - T['ship']; out = eio((t - T['cta'] + .05) / .25)
        # parcel box sliding along dotted route
        span = T['cta'] - T['ship']
        p = eio(lt / max(.5, span * .8))
        pts = [(160, H * .66), (420, H * .54), (700, H * .62), (920, H * .48)]
        for i in range(60):
            u = i / 59
            if u > p + .02: break
            seg = min(2, int(u * 3)); uu = u * 3 - seg; (x0, y0), (x1, y1) = pts[seg], pts[seg + 1]
            cv2.circle(f, (int(x0 + (x1 - x0) * uu), int(y0 + (y1 - y0) * uu + 1400 * out)), 7, (182, 196, 46), -1, cv2.LINE_AA)
        for j, (x, y) in enumerate(pts):
            if p >= j / 3 - .01:
                cv2.circle(f, (int(x), int(y + 1400 * out)), 22, (255, 117, 142), -1, cv2.LINE_AA); cv2.circle(f, (int(x), int(y + 1400 * out)), 34, (255, 200, 230), 3, cv2.LINE_AA)
        seg = min(2, int(p * 3)); uu = min(1, p * 3 - seg); (x0, y0), (x1, y1) = pts[seg], pts[seg + 1]
        bx, by = x0 + (x1 - x0) * uu, y0 + (y1 - y0) * uu - 150
        blit(f, P['chaos_box'], bx, by + 1400 * out, .42 * ebk(lt / .4), 1, 6 * math.sin(t * 5))
        blit(f, S['ship1'], W / 2, H * .2 - 900 * out, 1 + 1.2 * (1 - eo(lt / .18)), min(1, lt / .08))
        if lt > .45: blit(f, S['ship2'], W / 2, H * .31 - 900 * out, ebk((lt - .45) / .3), 1)
    # S5 CTA
    if t >= T['cta']:
        lt = t - T['cta']
        rr = 300 * eo(lt / .6)
        if lt < .6: cv2.circle(f, (W // 2, int(H * .3)), int(rr + 40), (102, 211, 37), int(14 * (1 - lt / .6)) + 1, cv2.LINE_AA)
        blit(f, S['talk'], W / 2, H * .3, 1 + 1.5 * (1 - eo(lt / .18)), min(1, lt / .08))
        if t > T['btn']:
            k = t - T['btn']; tap = env(t, T['btn'] + .55, .25)
            blit(f, S['btn'], W / 2, H * .43, ebk(k / .35) * (1 - .06 * tap) * (1 + .02 * math.sin(t * 6)), 1)
            if k > .55:
                kk = k - .55; cv2.circle(f, (W // 2 + 120, int(H * .43)), int(30 + 260 * eo(kk / .6)), (230, 255, 230), max(1, int(10 * (1 - kk / .6))), cv2.LINE_AA) if kk < .6 else None
            # cursor
            cx = W / 2 + 120 + 300 * (1 - eo(k / .5)); cy = H * .43 + 40 + 300 * (1 - eo(k / .5))
            if k < 1.3:
                pts = np.int32([(cx, cy), (cx, cy + 70), (cx + 18, cy + 54), (cx + 34, cy + 86), (cx + 46, cy + 80), (cx + 30, cy + 48), (cx + 52, cy + 48)])
                cv2.fillPoly(f, [pts], (255, 255, 255), cv2.LINE_AA); cv2.polylines(f, [pts], True, (40, 20, 30), 3, cv2.LINE_AA)
            if k > .3: blit(f, S['phone'], W / 2, H * .52, ebk((k - .3) / .3), 1)
        if t > T['bookw']:
            k = t - T['bookw']; blit(f, S['book'], W / 2, H * .61, ebk(k / .3), 1)
        # end card
        if t > T['bookw'] + .6:
            k = t - T['bookw'] - .6
            blit(f, P['op16'], W * .17, H * .9 + 200 * (1 - eo(k / .4)), .45, eo(k / .3), -8)
            blit(f, P['chaos_box'], W * .83, H * .9 + 200 * (1 - eo(k / .4)), .5, eo(k / .3), 8)
            blit(f, S['htr_sm'], W / 2, H * .76, ebk(k / .35), 1)
            blit(f, S['handle'], W / 2 + 70, H * .84, 1, eo((k - .2) / .3)); blit(f, S['jed'], W / 2 - 230, H * .84, 1, eo((k - .2) / .3))
    f = np.clip(f, 0, 255)
    fl = env(t, 0.02, .25) * .8 + sum(env(t, h, .14) for h in (T['boxq'], T['box'], T['pack'], T['cta'])) * .35
    if fl > .01: f = f + (255 - f) * min(1, fl)
    f = f.astype(np.uint8)
    if sh > .5: f = cv2.warpAffine(f, np.float32([[1, 0, sh * math.sin(t * 93)], [0, 1, sh * math.cos(t * 71)]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    # vignette
    if t > TOTAL - .4: f = (f * max(0, (TOTAL - t) / .4)).astype(np.uint8)
    return f

VIG = (1 - .45 * np.clip(((xx - W / 2) ** 2 / (W * .75) ** 2 + (yy - H / 2) ** 2 / (H * .7) ** 2), 0, 1))[..., None]
def final(t): return (render(t) * VIG).astype(np.uint8)

if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        ts = [float(x) for x in sys.argv[2:]]; ims = [cv2.resize(final(t), (270, 480)) for t in ts]
        rows = [np.hstack(ims[i:i + 6] + [np.zeros((480, 270, 3), np.uint8)] * (6 - len(ims[i:i + 6]))) for i in range(0, len(ims), 6)]
        cv2.imwrite('/home/claude/ad1/st.jpg', np.vstack(rows))
    else:
        a, b, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
        p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for i in range(int(round(a * FPS)), int(round(b * FPS))):
            fa = final(i / FPS).astype(np.uint16); fb = final(i / FPS + .5 / FPS).astype(np.uint16)
            p.stdin.write(((fa + fb) // 2).astype(np.uint8).tobytes())
        p.stdin.close(); p.wait()
