import sys, subprocess, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
TOTAL = 14.6
VO = 0.5
T_YGO, T_BOX, T_RC, T_24, T_CARDS, T_PRICE, T_CTA = 1.3, 2.4, 3.7, 5.04, 6.4, 8.37, 10.63
FD = '/home/claude/fonts/'
def FL(s): return ImageFont.truetype(FD + 'font_lalezar.ttf', s)
def FB(s): return ImageFont.truetype(FD + 'font_bungee.ttf', s)
PINK = (255, 61, 154); VIOLET = (139, 92, 246); CYAN = (56, 225, 255); WHITE = (255, 255, 255); DEEP = (20, 10, 46)
rng = np.random.default_rng(7)

# ---------- helpers ----------
def eo(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def eio(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def ebk(x, s=1.9): x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def env(t, a, d): return max(0.0, 1 - (t - a) / d) if t >= a else 0.0

def to_bgra(im):
    a = np.array(im.convert('RGBA')); return a[..., [2, 1, 0, 3]].copy()

def text_sprite(s, font, fill=WHITE, grad=None, stroke=0, stroke_fill=(20, 10, 46), glow=None, glow_r=18, pad=40, shadow=True):
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
    if shadow:
        sh = Image.new('RGBA', (w, h), (10, 0, 30, 0)); m2 = Image.new('L', (w, h), 0); m2.paste(smask, (0, 10)); sh.putalpha(m2.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * .7)))
        out = Image.alpha_composite(out, sh)
    if stroke:
        st = Image.new('RGBA', (w, h), stroke_fill + (0,)); st.putalpha(smask); out = Image.alpha_composite(out, st)
    if grad:
        y = np.linspace(0, 1, h)[:, None]; c0, c1 = np.array(grad[0], float), np.array(grad[1], float)
        col = (c0 * (1 - y) + c1 * y)[:, None, :].repeat(w, 1) if False else np.broadcast_to((c0[None, :] * (1 - y) + c1[None, :] * y)[:, None, :], (h, w, 3))
        fillim = Image.fromarray(col.astype(np.uint8), 'RGB').convert('RGBA')
    else:
        fillim = Image.new('RGBA', (w, h), fill + (255,))
    fillim.putalpha(mask); out = Image.alpha_composite(out, fillim)
    return to_bgra(out)

def pill(s, font, bg, fg=WHITE, padx=44, pady=20, border=None):
    d0 = ImageDraw.Draw(Image.new('RGBA', (10, 10))); bb = d0.textbbox((0, 0), s, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]; w, h = tw + 2 * padx, th + 2 * pady
    im = Image.new('RGBA', (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    gl = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(gl).rounded_rectangle((20, 24, 20 + w, 24 + h), h // 2, fill=(bg[0], bg[1], bg[2], 160)); gl = gl.filter(ImageFilter.GaussianBlur(10))
    im = Image.alpha_composite(im, gl); d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), h // 2, fill=bg + (255,), outline=border, width=4 if border else 0)
    d.text((20 + padx - bb[0], 20 + pady - bb[1]), s, font=font, fill=fg)
    return to_bgra(im)

def rounded(im, r):
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    im = im.convert('RGBA'); im.putalpha(m); return im

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
    reg = f[ya:yb, xa:xb]
    reg[:] = reg * (1 - al) + sp[..., :3] * al

def persp(spr, ang, s=1.0):
    """rotate sprite around vertical axis by ang degrees (perspective) and scale"""
    h, w = spr.shape[:2]; a = math.radians(ang); f = 1400.0
    pts = []
    for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        X, Z = x * math.cos(a), x * math.sin(a); k = f / (f + Z)
        pts.append((X * k * s, y * k * s))
    pts = np.float32(pts); mn = pts.min(0); pts -= mn - 10
    ow, oh = int(pts[:, 0].max() + 10), int(pts[:, 1].max() + 10)
    M = cv2.getPerspectiveTransform(np.float32([(0, 0), (w, 0), (w, h), (0, h)]), pts)
    return cv2.warpPerspective(spr, M, (ow, oh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

# ---------- assets ----------
logo = Image.open('/home/claude/htr-videos/fetch/bn_ohlogo.png').convert('RGBA')
def logo_spr(w):
    l = logo.resize((w, int(logo.height * w / logo.width)), Image.LANCZOS)
    g = Image.new('RGBA', (l.width + 120, l.height + 120), (0, 0, 0, 0)); gl = Image.new('RGBA', g.size, PINK + (0,))
    m = Image.new('L', g.size, 0); m.paste(l.getchannel('A'), (60, 60)); gl.putalpha(m.filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * .9)))
    g = Image.alpha_composite(g, gl); g.alpha_composite(l, (60, 60)); return to_bgra(g)
LOGO_BIG, LOGO_MID, LOGO_WM = logo_spr(560), logo_spr(460), logo_spr(150)

box = Image.open('/home/claude/htr-videos/fetch/ohy_1.jpg').convert('RGB')
box = box.crop((0, 290, 563, 890))  # boxes on table
def framed(im, w, r=36, border=PINK):
    im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS); im = rounded(im, r)
    pad = 60; c = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    gl = Image.new('RGBA', c.size, border + (0,)); m = Image.new('L', c.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((pad - 8, pad - 8, pad + im.width + 8, pad + im.height + 8), r + 8, fill=255)
    gl.putalpha(m.filter(ImageFilter.GaussianBlur(26)))
    c = Image.alpha_composite(c, gl); ImageDraw.Draw(c).rounded_rectangle((pad - 7, pad - 7, pad + im.width + 6, pad + im.height + 6), r + 7, fill=WHITE + (255,))
    c.alpha_composite(im, (pad, pad)); return to_bgra(c)
BOX = framed(box, 820)
BOX_SM = framed(box, 380, r=26)

CARD_IDS = ['c16_5', 'c4_2', 'c1_2', 'c3_2', 'c5_3']
def card_spr(cid, w=300):
    im = Image.open(f'cards/{cid}.png').convert('RGB'); im = im.resize((w, int(w * 1.45)), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(2, 80, 2)); im = rounded(im, 14)
    pad = 30; c = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new('RGBA', c.size, (0, 0, 0, 0)); m = Image.new('L', c.size, 0); m.paste(im.getchannel('A'), (pad, pad + 10))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * .6))); c = Image.alpha_composite(c, sh); c.alpha_composite(im, (pad, pad))
    return to_bgra(c)
CARDS = [card_spr(c) for c in CARD_IDS]
CARDS_BG = [card_spr(c, 230) for c in CARD_IDS]

S = dict(
    ya=text_sprite('يا عشاق', FL(150), fill=WHITE, glow=VIOLET),
    ygo=text_sprite('YU-GI-OH!', FB(160), grad=((255, 140, 200), PINK), stroke=10, stroke_fill=WHITE, glow=PINK, glow_r=26),
    bb=pill('BOOSTER BOX', FB(54), VIOLET),
    rc1=text_sprite('RARITY', FB(120), grad=(WHITE, (190, 170, 255)), stroke=8, stroke_fill=DEEP, glow=VIOLET),
    rc2=text_sprite('COLLECTION', FB(92), grad=((255, 160, 210), PINK), stroke=8, stroke_fill=DEEP, glow=PINK),
    n24=None,
    packs=text_sprite('باك في البوكس', FL(110), fill=WHITE, glow=VIOLET),
    holo=text_sprite('كل كروتها لامعة', FL(130), fill=WHITE, glow=PINK),
    holo2=pill('FOIL', FB(50), PINK),
    p850=text_sprite('850', FB(330), grad=(WHITE, (255, 150, 205)), stroke=14, stroke_fill=DEEP, glow=PINK, glow_r=34),
    sar=text_sprite('ريال', FL(130), fill=WHITE, glow=VIOLET),
    stock=pill('متوفر الآن', FL(56), (30, 18, 70), fg=WHITE, border=CYAN + (255,)),
    order=text_sprite('اطلبه الحين', FL(160), fill=WHITE, glow=PINK),
    url=pill('otakkuhaveen.com', FB(50), PINK),
    ygo_sm=text_sprite('YU-GI-OH!', FB(64), grad=((255, 160, 210), PINK), stroke=6, stroke_fill=WHITE, glow=PINK, glow_r=14),
)
NUMS = {n: text_sprite(str(n), FB(380), grad=(WHITE, (190, 170, 255)), stroke=14, stroke_fill=DEEP, glow=VIOLET, glow_r=34) for n in range(1, 25)}

# ---------- background ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
BASE = np.zeros((H, W, 3), np.float32)
top, bot = np.array(DEEP[::-1], np.float32), np.array((60, 14, 70)[::-1], np.float32)
k = (yy / H)[..., None]; BASE[:] = top * (1 - k) + bot * k
def radial(cx, cy, r): return np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)))[..., None]
GLOW_P = radial(W / 2, H * .45, 620) * np.array(PINK[::-1], np.float32)
GLOW_V = radial(W * .2, H * .15, 500) * np.array(VIOLET[::-1], np.float32)
ANG = np.arctan2(yy - H * .45, xx - W / 2)
RAYS = (0.5 + 0.5 * np.cos(ANG * 18))[..., None].astype(np.float32)
STARS = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(4, 13), rng.uniform(0, 6.28), rng.uniform(1.5, 4), rng.uniform(10, 40)) for _ in range(70)]
BPM = 150; BEAT = 60 / BPM
def star(f, x, y, r, col, a):
    if a <= 0.02: return
    pts = []
    for i in range(8):
        rr = r if i % 2 == 0 else r * .28; an = i * math.pi / 4
        pts.append((x + rr * math.cos(an), y + rr * math.sin(an)))
    ov = f.copy(); cv2.fillPoly(ov, [np.int32(pts)], col, cv2.LINE_AA); cv2.addWeighted(ov, a, f, 1 - a, 0, f)

def background(t):
    pulse = env((t % BEAT), 0, BEAT * .7) * (1 if t > T_YGO else .3)
    rot = t * .25
    rays = (0.5 + 0.5 * np.cos((ANG + rot) * 18))[..., None]
    f = BASE + GLOW_P * (.42 + .12 * pulse) + GLOW_V * .35 + rays * radial(W / 2, H * .45, 900) * 18 * (1 + pulse)
    f = np.clip(f, 0, 255).astype(np.uint8)
    for x, y, r, ph, sp, vy in STARS:
        yy_ = (y - vy * t) % H; a = .5 + .5 * math.sin(t * sp + ph)
        star(f, x, yy_, r * (.6 + .4 * a), (255, 220, 255), a * .8)
    return f

# ---------- scene renderer ----------
def flash_amt(t):
    return env(t, 0.05, .25) * .9 + env(t, T_YGO, .2) * .55 + env(t, T_PRICE + .03, .2) * .5 + env(t, T_CTA, .15) * .35

def render(t):
    f = background(t).astype(np.float32)
    sh = env(t, T_YGO, .3) * 18 + env(t, T_PRICE + .03, .3) * 16 + env(t, T_24 + .5, .2) * 8
    # S0 logo intro
    if t < VO + .15:
        k = ebk(t / .35); out = eo((t - .3) / .3)
        blit(f, LOGO_BIG, W / 2 + (W * .5 - W / 2) * out, H * .45 - 300 * out, k * (1 - .5 * out), 1 - out)
    if VO <= t < T_CTA - .1:  # watermark
        blit(f, LOGO_WM, 120, 120, 1, min(1, (t - VO) / .25) * .95)
    # S1
    if VO <= t < T_BOX + .25:
        lt = t - VO; out = eio((t - T_BOX + .05) / .3)
        for i, c in enumerate(CARDS_BG):  # background card wall
            x = W / 2 + (i - 2) * 230; y = H * .74 + 120 * (1 - eo((lt - i * .06) / .6)) + 20 * math.sin(t * 2 + i)
            blit(f, c, x, y + 400 * out, 1, .45 * eo((lt - i * .06) / .5), (i - 2) * 7)
        a = eo(lt / .25) * (1 - out)
        blit(f, S['ya'], W / 2 + 300 * (1 - eo(lt / .3)), H * .36, 1, a)
        if t >= T_YGO:
            k = t - T_YGO; s = 1 + 1.6 * (1 - eo(k / .18))
            blit(f, S['ygo'], W / 2, H * .47 - 200 * out, s * (1 - .3 * out) * (1 + .03 * math.sin(t * 9)), min(1, k / .08) * (1 - out))
    # S2 box
    if T_BOX <= t < T_24 + .2:
        lt = t - T_BOX; out = eio((t - T_24 + .1) / .3)
        ang = 75 * (1 - eo(lt / .6)) + 7 * math.sin(lt * 2.2) * eo(lt / .6)
        spr = persp(BOX, ang, .75 + .25 * ebk(lt / .6))
        # shine sweep
        if 1.0 < lt < 1.7:
            h, w = spr.shape[:2]; ys, xs = np.mgrid[0:h, 0:w]; p = (lt - 1.0) / .7 * (w + h * .6) - h * .3
            band = np.exp(-(((xs + ys * .5) - p) / 60.0) ** 2)
            spr = spr.copy(); spr[..., :3] = np.clip(spr[..., :3] + (band[..., None] * 160 * (spr[..., 3:4] > 0)), 0, 255).astype(np.uint8)
        blit(f, spr, W / 2 - 900 * out, H * .40 + 12 * math.sin(t * 2), 1, eo(lt / .2))
        if t > T_BOX + .35: blit(f, S['bb'], W / 2 - 900 * out, H * .13, ebk((t - T_BOX - .35) / .3), 1)
        if t > T_RC:
            k = t - T_RC
            blit(f, S['rc1'], W / 2 + 500 * (1 - eo(k / .3)) - 900 * out, H * .73, 1, eo(k / .2))
            blit(f, S['rc2'], W / 2 - 500 * (1 - eo((k - .12) / .3)) - 900 * out, H * .80, 1, eo((k - .12) / .2))
    # S3 24 packs
    if T_24 - .1 <= t < T_CARDS + .2:
        lt = t - T_24; out = eio((t - T_CARDS + .1) / .3)
        n = max(1, min(24, int(1 + 23 * eo(lt / .5))))
        s = 1 + .25 * env(t, T_24 + .5, .25)
        blit(f, NUMS[n], W / 2 + 900 * (1 - eo((lt + .1) / .25)) - 0, H * .40 - 1200 * out, s, 1)
        if lt > .45: blit(f, S['packs'], W / 2, H * .55 + 60 * (1 - eo((lt - .45) / .3)) + 1200 * out, 1, eo((lt - .45) / .2))
        # mini box
        blit(f, BOX_SM, W / 2, H * .77 + 1200 * out + 10 * math.sin(t * 2.5), ebk((lt - .2) / .4) * .9, 1)
    # S4 card fan
    if T_CARDS <= t < T_PRICE + .25:
        lt = t - T_CARDS; out = eio((t - T_PRICE + .05) / .3)
        for j in [0, 4, 1, 3, 2]:
            i = j - 2; k = ebk((lt - abs(i) * .07) / .55)
            x = W / 2 + i * 195 * k; y = H * .43 + abs(i) ** 1.6 * 34 * k - 900 * (1 - eo((lt - abs(i) * .07) / .4))
            spr = CARDS[j]
            # holo shimmer
            ph = (t * 1.3 + j * .2) % 1
            h, w = spr.shape[:2]
            if j == 2 or (lt > .6):
                ys, xs = np.mgrid[0:h, 0:w].astype(np.float32); u = (xs + ys * .7) / (w + h * .7)
                hue = ((u * 2 + ph) % 1)
                rb = np.stack([128 + 127 * np.cos(2 * np.pi * (hue + o)) for o in (0, .33, .66)], -1)
                band = np.exp(-((u - ((t * .6 + j * .13) % 1.4 - .2)) / .08) ** 2)[..., None]
                spr = spr.copy(); a_ = (spr[..., 3:4] > 200)
                spr[..., :3] = np.clip(spr[..., :3] * (1 - .25 * band) + rb * .25 * band * a_ + 90 * band * a_, 0, 255).astype(np.uint8)
            blit(f, spr, x, y + 1400 * out, 1.0 + (.12 if j == 2 else 0), 1, -i * 9 * k)
        if lt > .35: blit(f, S['holo'], W / 2, H * .70 + 1400 * out, ebk((lt - .35) / .35), 1)
        if lt > .6: blit(f, S['holo2'], W / 2, H * .79 + 1400 * out, ebk((lt - .6) / .3), 1)
    # S5 price
    if T_PRICE - .05 <= t < T_CTA + .25:
        lt = t - T_PRICE; out = eio((t - T_CTA + .05) / .3)
        blit(f, BOX_SM, W / 2, H * .25 - 1000 * out + 10 * math.sin(t * 2), ebk(lt / .45), 1, 4 * math.sin(t * 1.5))
        if lt > .03:
            k = lt - .03; s = 1 + 1.4 * (1 - eo(k / .16))
            blit(f, S['p850'], W / 2, H * .53 + 900 * out, s * (1 + .02 * math.sin(t * 8)), min(1, k / .06))
        if lt > .45: blit(f, S['sar'], W / 2, H * .66 + 900 * out, ebk((lt - .45) / .3), 1)
        if lt > 1.1: blit(f, S['stock'], W / 2, H * .76 + 900 * out, ebk((lt - 1.1) / .3), 1)
        if lt < 1.2:  # burst sparkles
            for i in range(26):
                an = i / 26 * 6.283 + .3; r = 120 + 700 * eo(lt / 1.0)
                star_a = (1 - lt / 1.2)
                fx = np.clip(f, 0, 255).astype(np.uint8); star(fx, W / 2 + r * math.cos(an), H * .53 + r * math.sin(an) * .8, 16, (255, 200, 255) if i % 2 else (255, 240, 120)[::-1] if False else (250, 230, 255), star_a); f = fx.astype(np.float32)
    # S6 CTA
    if t >= T_CTA:
        lt = t - T_CTA
        blit(f, LOGO_MID, W / 2, H * .30 + 8 * math.sin(t * 2), ebk(lt / .45), 1)
        if lt > .2: blit(f, S['order'], W / 2, H * .52, ebk((lt - .2) / .35), 1)
        if lt > .45: blit(f, S['url'], W / 2, H * .63, ebk((lt - .45) / .35) * (1 + .03 * math.sin(t * 6)), 1)
        if lt > .7: blit(f, S['ygo_sm'], W / 2, H * .75, ebk((lt - .7) / .35), 1)
        if lt > .7: blit(f, BOX_SM, W / 2, H * .87 + 20 * (1 - eo((lt - .7) / .4)), .55 * ebk((lt - .7) / .4), 1)
    f = np.clip(f, 0, 255)
    fl = flash_amt(t)
    if fl > .01: f = f + (255 - f) * fl
    f = f.astype(np.uint8)
    if sh > .5: f = cv2.warpAffine(f, np.float32([[1, 0, sh * math.sin(t * 93)], [0, 1, sh * math.cos(t * 71)]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    if t > TOTAL - .4: f = (f * max(0, (TOTAL - t) / .4)).astype(np.uint8)
    return f

if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        ts = [float(x) for x in sys.argv[2:]]; ims = [cv2.resize(render(t), (270, 480)) for t in ts]
        rows = [np.hstack(ims[i:i + 6] + [np.zeros((480, 270, 3), np.uint8)] * (6 - len(ims[i:i + 6]))) for i in range(0, len(ims), 6)]
        cv2.imwrite('st.jpg', np.vstack(rows))
    else:
        a, b, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
        p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for i in range(int(round(a * FPS)), int(round(b * FPS))):
            # 2-subframe motion blur
            fa = render(i / FPS).astype(np.uint16); fb = render(i / FPS + .5 / FPS).astype(np.uint16)
            p.stdin.write(((fa + fb) // 2).astype(np.uint8).tobytes())
        p.stdin.close(); p.wait()
