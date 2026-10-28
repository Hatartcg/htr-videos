import sys, os, subprocess, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import *

KEY = os.environ['OH']
D = f'/home/claude/work/{KEY}/'
VO = 0.5
INK = (18, 12, 24)
PAPER = (246, 242, 250)

CFG = {
    'op14': dict(
        TOTAL=13.9, T_GAME=1.26, T_PROD=2.18, T_NAME=3.54, T_F1=5.26, T_F2=6.74, T_PRICE=8.78, T_CTA=10.34,
        game=['ONE PIECE'], sfx='DON!!', label='BOOSTER BOX', name=['OP-14', 'ENGLISH EDITION'],
        f1=dict(kind='num', n=24, cap='باك في البوكس'), f2=dict(kind='num', n=12, cap='كرت في كل باك', img='alt.png'),
        price='1,000', spot=PINK, seed=3),
    'ygo': dict(
        TOTAL=15.3, T_GAME=1.26, T_PROD=2.48, T_NAME=2.94, T_F1=4.77, T_F2=5.76, T_F2b=7.66, T_PRICE=9.64, T_CTA=11.85,
        game=['YU-GI-OH!'], sfx='DUEL!', label='BOOSTER BOX', name=['MAGNIFICENT', 'MONSTERS'],
        f1=dict(kind='num', n=3, cap='باكات في البوكس'), f2=dict(kind='num', n=15, cap='ULTRA RARE', en=True, img='alt.png', extra='+3 SECRET RARE'),
        price='179', spot=VIOLET, seed=5),
    'suk': dict(
        TOTAL=15.0, T_GAME=1.22, T_PROD=2.58, T_NAME=2.98, T_F1=4.34, T_F1b=5.94, T_F2=7.7, T_PRICE=9.78, T_CTA=11.62,
        game=['JUJUTSU', 'KAISEN'], sfx='DOMAIN!', label='HOODIE', name=['SUKUNA', 'HOODIE'],
        f1=dict(kind='caps', caps=['خامة عالية الجودة', 'دافي للأيام الباردة']), f2=dict(kind='grid', cap='ألوان متعددة'),
        price='200', spot=(220, 40, 90), seed=9),
    'st24': dict(
        TOTAL=14.6, T_GAME=1.14, T_PROD=2.75, T_NAME=3.9, T_F1=5.1, T_F2=7.38, T_PRICE=8.95, T_CTA=11.1,
        hook='تبي تبدأ؟', game=['ONE PIECE', 'CARD GAME'], sfx='SET SAIL!', label='STARTER DECK', name=['JEWELRY BONNEY', 'ST-24'],
        f1=dict(kind='num', n=51, cap='كرت جاهزة للعب'), f2=dict(kind='num', n=1, plus=True, cap='ومعاه باك بوستر!'),
        price='165', spot=PINK, seed=11, sfx_x=.6),
    'bleach': dict(
        TOTAL=13.6, T_GAME=1.3, T_PROD=1.95, T_NAME=3.0, T_F1=4.3, T_F1b=5.3, T_F2=6.2, T_PRICE=8.3, T_CTA=10.6,
        hook='مطر ولا معركة؟', game=['BLEACH'], sfx='SLASH!', label='ANIME MERCH', name=['SWORD UMBRELLA', 'BLEACH'],
        f1=dict(kind='caps', caps=['مقبض على شكل سيف', 'خفيفة وتنطوي بسهولة']), f2=dict(kind='grid', cap='تصاميم إيتشيغو وآيزن وبياكويا'),
        price='441', spot=(255, 61, 154), seed=21, order='اطلبها الحين!', stock='متوفرة الآن'),
}[KEY]
globals().update({k: v for k, v in CFG.items() if k.startswith('T')})
TOTAL = CFG['TOTAL']; SPOT = CFG['spot']
rng = np.random.default_rng(CFG['seed'])

def fit(spr, maxw=980):
    h, w = spr.shape[:2]
    return spr if w <= maxw else cv2.resize(spr, (maxw, int(h * maxw / w)), interpolation=cv2.INTER_AREA)

# ---------- sprite makers ----------
def ink_text(s, font, fill=WHITE, stroke=14, shadow_col=None, off=12):
    """manga title: fill + thick ink stroke + hard offset spot-colour shadow"""
    d0 = ImageDraw.Draw(Image.new('RGBA', (10, 10))); bb = d0.textbbox((0, 0), s, font=font, stroke_width=stroke)
    pad = 30; w, h = bb[2] - bb[0] + 2 * pad + off, bb[3] - bb[1] + 2 * pad + off
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); ox, oy = pad - bb[0], pad - bb[1]
    if shadow_col: d.text((ox + off, oy + off), s, font=font, fill=shadow_col, stroke_width=stroke, stroke_fill=shadow_col)
    d.text((ox, oy), s, font=font, fill=fill, stroke_width=stroke, stroke_fill=INK)
    return to_bgra(im)

def bubble(s, font, tail=(-.25, 1), pad=(60, 40), fill=WHITE, fg=INK, jag=False):
    d0 = ImageDraw.Draw(Image.new('RGBA', (10, 10))); bb = d0.textbbox((0, 0), s, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]; w, h = tw + 2 * pad[0], th + 2 * pad[1]
    M = 90; im = Image.new('RGBA', (w + 2 * M, h + 2 * M), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx, cy = M + w / 2, M + h / 2
    if jag:
        pts = []
        for i in range(36):
            a = i / 36 * 2 * math.pi; r = 1.0 if i % 2 == 0 else .82
            pts.append((cx + (w / 2 + 40) * r * math.cos(a), cy + (h / 2 + 40) * r * math.sin(a)))
        d.polygon(pts, fill=INK); pts2 = [(cx + (x - cx) * .93, cy + (y - cy) * .9) for x, y in pts]; d.polygon(pts2, fill=fill)
    else:
        tx = cx + tail[0] * w; ty = cy + tail[1] * (h / 2 + 70)
        tri = [(tx, ty), (cx + tail[0] * w * .3 - 30, cy + h * .3), (cx + tail[0] * w * .3 + 40, cy + h * .3)]
        d.polygon(tri, fill=INK); d.ellipse((M - 10, M - 10, M + w + 10, M + h + 10), fill=INK)
        tri2 = [(tx + (cx - tx) * .12, ty + (cy - ty) * .12 - 6), tri[1], tri[2]]
        d.ellipse((M, M, M + w, M + h), fill=fill); d.polygon([(p[0], p[1] - 2) for p in tri2], fill=fill)
    d.text((cx - tw / 2 - bb[0], cy - th / 2 - bb[1]), s, font=font, fill=fg)
    return to_bgra(im)

def tag(s, font, bg=INK, fg=WHITE, skew=-8):
    d0 = ImageDraw.Draw(Image.new('RGBA', (10, 10))); bb = d0.textbbox((0, 0), s, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]; w, h = tw + 80, th + 44
    im = Image.new('RGBA', (w + 60, h + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(30 + 20, 8 + 8), (30 + w + 20, 8 + 8), (30 + w - 0, 8 + h + 8), (30 - 0, 8 + h + 8)], fill=SPOT)
    d.polygon([(30 + 20, 8), (30 + w + 20, 8), (30 + w, 8 + h), (30, 8 + h)], fill=bg)
    d.text((30 + 10 + 40 - bb[0], 8 + 22 - bb[1]), s, font=font, fill=fg)
    return to_bgra(im)

def panel_img(im, w, border=12, tone=True):
    im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    c = Image.new('RGBA', (im.width + 2 * border + 24, im.height + 2 * border + 24), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rectangle((24, 24, c.width - 1, c.height - 1), fill=SPOT + (255,))  # hard spot shadow
    d.rectangle((0, 0, c.width - 25, c.height - 25), fill=INK + (255,))
    c.paste(im, (border, border)); return to_bgra(c)

# ---------- assets ----------
logo = Image.open('/home/claude/oh/fetch/bn_ohlogo.png').convert('RGBA')
def logo_spr(w):
    l = logo.resize((w, int(logo.height * w / logo.width)), Image.LANCZOS)
    pd = int(w * .1); g = Image.new('RGBA', (l.width + 2 * pd + 20, l.height + 2 * pd + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.rounded_rectangle((20, 20, g.width - 1, g.height - 1), pd, fill=SPOT + (255,))
    d.rounded_rectangle((0, 0, g.width - 21, g.height - 21), pd, fill=INK + (255,))
    g.alpha_composite(l, (pd, pd)); return to_bgra(g)
LOGO_BIG, LOGO_MID, LOGO_WM = logo_spr(600), logo_spr(480), logo_spr(160)

prod = Image.open(D + 'main.png').convert('RGB')
PROD = panel_img(prod, 700 if prod.height / prod.width > 1.05 else 760)
PROD_SM = panel_img(prod, 340, border=8)
ALT = panel_img(Image.open(D + 'alt.png').convert('RGB'), 500, border=10) if os.path.exists(D + 'alt.png') else PROD_SM
GRID = [panel_img(Image.open(D + f'c{i}.png').convert('RGB'), 290, border=8) for i in (1, 3, 4, 5, 7, 8)] if CFG['f2']['kind'] == 'grid' else []

S = dict(
    ya=bubble(CFG.get('hook', 'تبي؟'), FL(120), tail=(.3, 1)),
    game=[fit(ink_text(g, FB(160 if len(CFG['game']) == 1 else 140), fill=WHITE, stroke=16, shadow_col=SPOT + (255,), off=16), 1000) for g in CFG['game']],
    sfx=ink_text(CFG['sfx'], FB(120), fill=SPOT, stroke=10, shadow_col=INK + (255,), off=8),
    label=tag(CFG['label'], FB(56)),
    name=[fit(ink_text(CFG['name'][0], FB(150), fill=WHITE, stroke=14, shadow_col=SPOT + (255,))), fit(tag(CFG['name'][1], FB(64), bg=WHITE, fg=INK))],
    burst=bubble(CFG['price'], FB(230 if len(CFG['price']) > 3 else 260), fill=SPOT, fg=WHITE, jag=True, pad=(90, 70)),
    sar=bubble('ريال بس!', FL(110), tail=(-.3, -1)),
    stock=tag(CFG.get('stock','متوفر الآن'), FL(64)),
    bam=ink_text('BAM!', FB(110), fill=WHITE, stroke=10, shadow_col=SPOT + (255,), off=8),
    order=bubble(CFG.get('order','اطلبه الحين!'), FL(140), tail=(.25, 1)),
    url=tag('otakkuhaveen.com', FB(52), bg=SPOT),
    game_sm=fit(ink_text(' '.join(CFG['game']), FB(66), fill=WHITE, stroke=8, shadow_col=SPOT + (255,), off=6), 900),
)
for k in ('f1', 'f2'):
    f = CFG[k]
    if f.get('cap'): S[k + 'cap'] = fit(tag(f['cap'], FB(70), bg=SPOT) if f.get('en') else bubble(f['cap'], FL(110), tail=(-.3, -1)))
    if f.get('caps'): S[k + 'caps'] = [fit(bubble(c, FL(104), tail=((-.3, -1) if i == 0 else (.3, -1)))) for i, c in enumerate(f['caps'])]
    if f.get('extra'): S[k + 'extra'] = tag(f['extra'], FB(60))
NMAX = max([CFG[k].get('n', 1) for k in ('f1', 'f2')])
PLUS = ink_text('+1', FB(400), fill=WHITE, stroke=20, shadow_col=SPOT + (255,), off=22)
NUMS = {n: ink_text(str(n), FB(400), fill=WHITE, stroke=20, shadow_col=SPOT + (255,), off=22) for n in range(1, NMAX + 1)}

# ---------- paper background + halftone ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
PAPERF = np.empty((H, W, 3), np.float32); PAPERF[:] = PAPER[::-1]
def halftone(cell, dens, col):
    """dot screen: dens (H,W) in 0..1 -> mask"""
    gx = (xx % cell) - cell / 2; gy = (yy % cell) - cell / 2
    r = np.sqrt(gx * gx + gy * gy); rad = dens * cell * .62
    return np.clip(rad - r + .5, 0, 1)[..., None] * (np.array(col[::-1], np.float32) - PAPERF)
dens = np.clip(((xx / W) * .6 + (1 - yy / H) * .5 - .35), 0, 1) * .9
TONE1 = halftone(18, dens, VIOLET)
dens2 = np.clip(((1 - xx / W) * .6 + (yy / H) * .6 - .5), 0, 1)
TONE2 = halftone(14, dens2, SPOT)
BG0 = np.clip(PAPERF + TONE1 * .55 + TONE2 * .45, 0, 255)
ANG = np.arctan2(yy - H * .45, xx - W / 2); RR = np.sqrt((xx - W / 2) ** 2 + (yy - H * .45) ** 2)
LINES = rng.uniform(0, 2 * np.pi, 90); LW = rng.uniform(.004, .014, 90)

def speedlines(f, amt, cx=W / 2, cy=H * .45, r0=330, seed=0):
    if amt <= .01: return f
    r2 = np.random.default_rng(seed)
    ov = f.copy().astype(np.uint8)
    for a, w in zip(LINES + r2.uniform(-.03, .03, len(LINES)), LW):
        r1 = r0 + r2.uniform(0, 160); R = 1500
        p = [(cx + r1 * math.cos(a), cy + r1 * math.sin(a)), (cx + R * math.cos(a - w), cy + R * math.sin(a - w)), (cx + R * math.cos(a + w), cy + R * math.sin(a + w))]
        cv2.fillPoly(ov, [np.int32(p)], INK[::-1], cv2.LINE_AA)
    return f * (1 - amt) + ov.astype(np.float32) * amt

def background(t, lines=0, cy=H * .45):
    f = BG0.copy()
    # slow tone drift
    sh = int(6 * math.sin(t * 1.3))
    if sh: f = np.roll(f, sh, axis=0)
    return speedlines(f, lines, cy=cy, seed=int(t * 15))

def panel_mask(poly):
    m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [np.int32(poly)], 255, cv2.LINE_AA); return (m.astype(np.float32) / 255)[..., None]
def draw_border(f, poly, th=12):
    fx = np.clip(f, 0, 255).astype(np.uint8); cv2.polylines(fx, [np.int32(poly)], True, INK[::-1], th, cv2.LINE_AA); f[:] = fx

def shine(spr, p01):
    h, w = spr.shape[:2]; ys, xs = np.mgrid[0:h, 0:w]; p = p01 * (w + h * .6) - h * .3
    band = np.exp(-(((xs + ys * .5) - p) / 50.0) ** 2)
    spr = spr.copy(); spr[..., :3] = np.clip(spr[..., :3] + (band[..., None] * 170 * (spr[..., 3:4] > 0)), 0, 255).astype(np.uint8)
    return spr

def ink_flash(t):  # black/white impact frames
    return env(t, T_GAME, .08) * 1.0 + env(t, T_PRICE + .02, .08) * 1.0

def wipe(t, t0):  # diagonal page-wipe transition progress (ink slab sweeping)
    return eio((t - t0 + .16) / .32)

def slab(f, p, col=INK):
    """diagonal slab sweeping right->left, p 0..1"""
    if p <= 0 or p >= 1: return
    x = 1600 - p * 3300; SW = 1700
    poly = [(x, 0), (x + SW, 0), (x + SW - 500, H), (x - 500, H)]
    fx = np.clip(f, 0, 255).astype(np.uint8); cv2.fillPoly(fx, [np.int32(poly)], col[::-1], cv2.LINE_AA)
    poly2 = [(x - 60, 0), (x, 0), (x - 500, H), (x - 560, H)]
    cv2.fillPoly(fx, [np.int32(poly2)], SPOT[::-1], cv2.LINE_AA); f[:] = fx

def num_scene(f, t, t0, t1, fc, which):
    lt = t - t0; n = fc['n']
    m = max(1, min(n, int(1 + (n - 1) * eo(lt / .5))))
    # top panel (number)
    top = [(40, 210), (W - 40, 170), (W - 40, 1010), (40, 1060)]
    sub = background(t, lines=.9 * (1 - .4 * eo(lt / 1)), cy=600)
    mk = panel_mask(top); f[:] = f * (1 - mk) + sub * mk
    s = 1 + 1.2 * (1 - eo(lt / .18)) + .12 * env(t, t0 + .5, .25)
    blit(f, PLUS if fc.get('plus') else NUMS[m], W / 2, 590, s, min(1, lt / .06), -4)
    draw_border(f, top)
    cap = S[which + 'cap']
    if lt > .4: blit(f, cap, W / 2 + 40, 990 + 40 * (1 - eo((lt - .4) / .25)), ebk((lt - .4) / .3), 1, 2)
    if fc.get('extra') and t > T_F2b: blit(f, S['f2extra'], W / 2, 1150, ebk((t - T_F2b) / .3), 1, -3)
    # bottom panel (image)
    side = ALT if fc.get('img') else PROD_SM
    sp = shine(side, (lt - .5) / .8) if .5 < lt < 1.3 else side
    yb = 1500 if not fc.get('extra') else 1560
    blit(f, sp, W / 2 + 700 * (1 - eo((lt - .15) / .35)), yb + 8 * math.sin(t * 2.4), .9, 1, -3 + 2 * math.sin(t * 1.4))

def caps_scene(f, t, t0, t1, fc):
    lt = t - t0
    blit(f, PROD_SM, W / 2, 470 + 8 * math.sin(t * 2), ebk(lt / .4) * 1.25, 1, -4)
    for i, (tc, spr) in enumerate(zip([t0 + .05, T_F1b], S['f1caps'])):
        if t > tc:
            k = t - tc; x = W / 2 + (650 if i % 2 == 0 else -650) * (1 - eo(k / .25))
            blit(f, spr, x + (60 if i == 0 else -60), 1020 + 300 * i, 1 + .12 * env(t, tc + .2, .25), eo(k / .15), 3 if i == 0 else -3)

def grid_scene(f, t, t0, t1, fc):
    lt = t - t0
    for i, spr in enumerate(GRID):
        r, c = divmod(i, 3); x = W / 2 + (c - 1) * 335; y = 470 + r * 400
        blit(f, spr, x, y + 6 * math.sin(t * 2 + i), ebk((lt - i * .06) / .35), 1, (-3, 2, -2, 3, -2, 2)[i])
    if lt > .45: blit(f, S['f2cap'], W / 2, 1360, ebk((lt - .45) / .3), 1, -2)

def render(t):
    lines = .85 * env(t, T_GAME, 1.4) + .9 * env(t, T_PRICE, 1.6) + .5 * env(t, T_PROD, .8)
    f = background(t, lines=min(1, lines))
    sh = env(t, T_GAME, .25) * 22 + env(t, T_PRICE + .03, .3) * 20 + env(t, T_F1, .15) * 8 + env(t, T_F2, .15) * 8
    # S0 logo stamp
    if t < VO + .2:
        k = t / .22; s = 2.2 - 1.2 * eo(k); out = eo((t - VO + .1) / .25)
        blit(f, LOGO_BIG, W / 2, H * .45 - 600 * out, s, min(1, k * 2) * (1 - out), -6 * (1 - eo(k)))
    if VO <= t < T_CTA - .1: blit(f, LOGO_WM, 125, 110, 1, min(1, (t - VO) / .2))
    # S1 hook
    if VO <= t < T_PROD:
        lt = t - VO
        blit(f, S['ya'], W / 2 - 60 + 500 * (1 - eo(lt / .25)), H * .27, ebk(lt / .3), 1, -3)
        if t >= T_GAME:
            for i, g in enumerate(S['game']):
                kk = t - T_GAME - i * .1
                if kk < 0: continue
                s = 1 + 2.0 * (1 - eo(kk / .14))
                blit(f, g, W / 2, H * (.47 + .1 * i), s * (1 + .02 * math.sin(t * 11)), min(1, kk / .05), -5)
            k = t - T_GAME - .25
            if k > 0: blit(f, S['sfx'], W * CFG.get('sfx_x', .72), H * .66 + len(S['game']) * 60, ebk(k / .25), 1, 12)
    # S2 product
    if T_PROD <= t < T_F1:
        lt = t - T_PROD
        ang = 60 * (1 - eo(lt / .5))
        spr = persp(PROD, ang, .8 + .2 * ebk(lt / .5))
        if .7 < lt < 1.4: spr = shine(spr, (lt - .7) / .7)
        blit(f, spr, W / 2 + 900 * (1 - eo(lt / .3)), H * .42 + 10 * math.sin(t * 2), 1, 1, -3 + 2 * math.sin(t * 1.2))
        if lt > .3: blit(f, S['label'], W * .36, H * .12, ebk((lt - .3) / .25), 1, -4)
        if t > T_NAME:
            k = t - T_NAME
            blit(f, S['name'][0], W / 2 - 600 * (1 - eo(k / .2)), H * .76, 1 + .5 * (1 - eo(k / .15)), 1, -4)
            if k > .15: blit(f, S['name'][1], W / 2 + 600 * (1 - eo((k - .15) / .2)), H * .84, 1, 1, -3)
    # facts
    if T_F1 <= t < T_F2:
        fc = CFG['f1']
        if fc['kind'] == 'num': num_scene(f, t, T_F1, T_F2, fc, 'f1')
        else: caps_scene(f, t, T_F1, T_F2, fc)
    if T_F2 <= t < T_PRICE:
        fc = CFG['f2']
        if fc['kind'] == 'num': num_scene(f, t, T_F2, T_PRICE, fc, 'f2')
        else: grid_scene(f, t, T_F2, T_PRICE, fc)
    # price
    if T_PRICE <= t < T_CTA:
        lt = t - T_PRICE
        blit(f, PROD_SM, W * .30, H * .20 + 8 * math.sin(t * 2), ebk(lt / .4), 1, -8)
        if lt > .02:
            k = lt - .02; s = 1 + 1.6 * (1 - eo(k / .14))
            blit(f, S['burst'], W / 2, H * .50, s * (1 + .025 * math.sin(t * 9)), min(1, k / .05), -4 + 2 * math.sin(t * 3))
        if lt > .2: blit(f, S['bam'], W * .74, H * .26, ebk((lt - .2) / .25), 1, 14)
        if lt > .45: blit(f, S['sar'], W * .62, H * .70, ebk((lt - .45) / .3), 1, 3)
        if lt > .95: blit(f, S['stock'], W * .40, H * .82, ebk((lt - .95) / .3), 1, -3)
    # CTA
    if t >= T_CTA:
        lt = t - T_CTA
        blit(f, LOGO_MID, W / 2, H * .25 + 6 * math.sin(t * 2), ebk(lt / .4), 1, -3)
        if lt > .15: blit(f, S['order'], W / 2, H * .46, ebk((lt - .15) / .3), 1, -3)
        if lt > .4: blit(f, S['url'], W / 2, H * .60, ebk((lt - .4) / .3) * (1 + .03 * math.sin(t * 6)), 1, -3)
        if lt > .6: blit(f, S['game_sm'], W / 2, H * .69, ebk((lt - .6) / .3), 1, -3)
        if lt > .6: blit(f, PROD_SM, W / 2, H * .83 + 20 * (1 - eo((lt - .6) / .4)), .7 * ebk((lt - .6) / .4), 1, 4)
    # page-wipe transitions
    for tw in (T_PROD, T_F1, T_F2, T_PRICE, T_CTA):
        p = wipe(t, tw)
        if 0 < p < 1: slab(f, p)
    f = np.clip(f, 0, 255)
    fl = ink_flash(t)
    if fl > .01: f = f * (1 - fl) + (255 - f) * fl  # inverted impact frame
    f = f.astype(np.uint8)
    if sh > .5: f = cv2.warpAffine(f, np.float32([[1, 0, sh * math.sin(t * 93)], [0, 1, sh * math.cos(t * 71)]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    if t > TOTAL - .35: f = (f * max(0, (TOTAL - t) / .35)).astype(np.uint8)
    return f

if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        ts = [float(x) for x in sys.argv[2:]]; ims = [cv2.resize(render(t), (270, 480)) for t in ts]
        rows = [np.hstack(ims[i:i + 6] + [np.zeros((480, 270, 3), np.uint8)] * (6 - len(ims[i:i + 6]))) for i in range(0, len(ims), 6)]
        cv2.imwrite(D + 'stm.jpg', np.vstack(rows))
    else:
        a, b, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
        p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for i in range(int(round(a * FPS)), int(round(b * FPS))):
            fa = render(i / FPS).astype(np.uint16); fb = render(i / FPS + .5 / FPS).astype(np.uint16)
            p.stdin.write(((fa + fb) // 2).astype(np.uint8).tobytes())
        p.stdin.close(); p.wait()
