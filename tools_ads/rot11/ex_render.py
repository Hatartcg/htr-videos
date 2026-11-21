# rot11 — OP-18 «DEAD BOXES?» explainer (style: edit-styles/talking-head-explainer, graphics-only version)
# ONE timeline, deterministic render(t). Fixed title bar, word-synced captions, stickers that pop on the spoken word.
import os, sys, json, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
R = '/home/claude/htr-videos/'; F = R + 'fetch/'
_src = open(R + 'tools_ads/rot8/dr_render.py', encoding='utf-8').read()
os.environ['CUES'] = 'dr_cues.json'
_argv = sys.argv; sys.argv = ['x']
exec(_src.split('# ---------- background')[0])  # helpers: text_sprite, pill, img_sprite, blit, fonts, easing
sys.argv = _argv
C = json.load(open(R + 'tools_ads/rot11/ex_cues.json')); O = C['off']; TOTAL = C['total']; CAP = C['caps']
OUT = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != 'frames' else '/home/claude/work/ex_v.mp4'
RANGE = (float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else None
RED = (226, 38, 52); TEALc = (32, 190, 170); WHITE = (255, 255, 255); NAVY = (14, 20, 36)
def bgr(c): return (c[2], c[1], c[0])

# ---------- background: charcoal-navy desk, slow dot grid, red glow behind the stage
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
BASE = np.zeros((H, W, 3), np.float32); BASE[:] = bgr((16, 22, 38))
BASE += (np.exp(-(((xx - 540) ** 2) / 700 ** 2 + ((yy - 860) ** 2) / 620 ** 2))[..., None] * np.array(bgr((60, 30, 40)), np.float32))
VIG = (1 - .45 * np.clip(((xx - 540) ** 2 / 560 ** 2 + (yy - 960) ** 2 / 1100 ** 2) - .25, 0, 1))[..., None]
def background(t, glow=0.0, glow_col=RED):
    f = BASE.copy()
    oy = (t * 14) % 60
    dots = (((xx % 60) - 30) ** 2 + (((yy + oy) % 60) - 30) ** 2 < 5).astype(np.float32)[..., None]
    f += dots * 14
    if glow > 0: f += np.exp(-(((xx - 540) ** 2 + (yy - 820) ** 2) / 520 ** 2))[..., None] * np.array(bgr(glow_col), np.float32) * .35 * glow
    return f * VIG

# ---------- sprite factories
def ld(p): return Image.open(F + p).convert('RGBA')
def panel(w, h, fill, r=40, alpha=235, border=None):
    im = Image.new('RGBA', (w + 80, h + 80), (0, 0, 0, 0)); sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((40, 52, 40 + w, 52 + h), r, fill=(0, 0, 0, 140)); im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(im); d.rounded_rectangle((40, 40, 40 + w, 40 + h), r, fill=fill + (alpha,), outline=border, width=6 if border else 0)
    return im
def draw_x(d, cx, cy, s, col, w):
    d.line((cx - s, cy - s, cx + s, cy + s), fill=col, width=w); d.line((cx - s, cy + s, cx + s, cy - s), fill=col, width=w)
def draw_check(d, cx, cy, s, col, w):
    d.line((cx - s, cy, cx - s * .3, cy + s * .7), fill=col, width=w); d.line((cx - s * .3, cy + s * .7, cx + s, cy - s * .7), fill=col, width=w)
def label_sprite(en, ar):  # small uppercase label like the reference (EARLY REPORTS …)
    fe, fa = FB(40), FL(48)
    d0 = ImageDraw.Draw(Image.new('RGBA', (5, 5))); be = d0.textbbox((0, 0), en, font=fe); ba = d0.textbbox((0, 0), ar, font=fa)
    w = (be[2] - be[0]) + (ba[2] - ba[0]) + 120; h = 86
    im = panel(w, h, (255, 255, 255), r=43, alpha=255); d = ImageDraw.Draw(im)
    d.rounded_rectangle((40, 40, 40 + (be[2] - be[0]) + 60, 40 + h), 43, fill=RED + (255,))
    d.text((70 - be[0], 40 + (h - (be[3] - be[1])) / 2 - be[1]), en, font=fe, fill=WHITE)
    d.text((40 + (be[2] - be[0]) + 80 - ba[0], 40 + (h - (ba[3] - ba[1])) / 2 - ba[1] - 4), ar, font=fa, fill=NAVY)
    return to_bgra(im)
def stamp(txt, col=RED, size=120):
    f = FB(size); d0 = ImageDraw.Draw(Image.new('RGBA', (5, 5))); bb = d0.textbbox((0, 0), txt, font=f)
    w, h = bb[2] - bb[0] + 80, bb[3] - bb[1] + 70
    im = Image.new('RGBA', (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), 22, outline=col + (255,), width=14)
    d.text((20 + 40 - bb[0], 20 + 35 - bb[1]), txt, font=f, fill=col + (255,))
    a = np.array(im); rng = np.random.default_rng(3); n = rng.random(a.shape[:2]) < .12; a[..., 3][n] = (a[..., 3][n] * .35).astype(np.uint8)
    return to_bgra(Image.fromarray(a))
def mini_box(dead):
    im = ld('op18_box.webp'); s = 230 / im.width; im = im.resize((230, int(im.height * s)), Image.LANCZOS)
    c = Image.new('RGBA', (270, im.height + 40), (0, 0, 0, 0)); c.alpha_composite(im, (20, 20))
    if dead:
        g = np.array(c); g[..., :3] = (g[..., :3].mean(-1, keepdims=True) * .55).astype(np.uint8); c = Image.fromarray(g)
        d = ImageDraw.Draw(c); draw_x(d, 135, c.height // 2, 58, RED + (255,), 20)
    return to_bgra(c)
def badge(kind, col, r=70):
    im = Image.new('RGBA', (2 * r + 40, 2 * r + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((20, 20, 20 + 2 * r, 20 + 2 * r), fill=col + (255,), outline=WHITE + (255,), width=8)
    (draw_x if kind == 'x' else draw_check)(d, r + 20, r + 20, r * .45, WHITE + (255,), 16); return to_bgra(im)
def bubble(w=150):
    im = Image.new('RGBA', (w + 40, w + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w, 20 + w * .72), 34, fill=WHITE + (255,)); d.polygon([(50, 20 + w * .68), (40, 20 + w * .95), (90, 20 + w * .68)], fill=WHITE + (255,))
    for k in range(3): d.ellipse((20 + w * (.25 + .25 * k) - 11, 20 + w * .36 - 11, 20 + w * (.25 + .25 * k) + 11, 20 + w * .36 + 11), fill=NAVY + (255,))
    return to_bgra(im)
def plane(w=120):
    im = Image.new('RGBA', (w + 40, w + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(20, 20 + w * .45), (20 + w, 20), (20 + w * .62, 20 + w), (20 + w * .45, 20 + w * .58)], fill=WHITE + (255,))
    d.line((20 + w * .45, 20 + w * .58, 20 + w, 20), fill=(200, 210, 230, 255), width=6); return to_bgra(im)
def caption_sprite(s, hi=False):
    return text_sprite(s, FL(92), fill=(255, 90, 100) if hi else WHITE, stroke=7, stroke_fill=(0, 0, 0), pad=30)

# title bar (fixed whole video)
def title_sprite():
    w, h = 900, 230; im = panel(w, h, (255, 255, 255), r=36, alpha=255); d = ImageDraw.Draw(im)
    d.rounded_rectangle((40, 40, 40 + w, 40 + 120), 36, fill=RED + (255,)); d.rectangle((40, 120, 40 + w, 160), fill=RED + (255,))
    f = FB(84); bb = d.textbbox((0, 0), 'DEAD BOXES?', font=f); d.text((40 + (w - (bb[2] - bb[0])) / 2 - bb[0], 40 + (120 - (bb[3] - bb[1])) / 2 - bb[1]), 'DEAD BOXES?', font=f, fill=WHITE)
    f2 = FL(66); s2 = 'OP-18 · وش السالفة؟'; bb = d.textbbox((0, 0), s2, font=f2); d.text((40 + (w - (bb[2] - bb[0])) / 2 - bb[0], 160 + (110 - (bb[3] - bb[1])) / 2 - bb[1] - 6), s2, font=f2, fill=NAVY)
    return to_bgra(im)
TITLE = title_sprite()
HTRTAG = pill('HTR', FB(40), NAVY)

BOX = img_sprite(ld('op18_box.webp'), 860, RED, 50)
BOX_S = img_sprite(ld('op18_box.webp'), 470, None)
EBBOX = img_sprite(ld('eb05en_pb2.webp'), 470, None)
PACK = img_sprite(ld('rel_op18_box.webp'), 430, None)
LOGO = img_sprite(Image.open(R + 'tools_challenges/htr_logo.png').convert('RGBA'), 520, None)
ST_DEAD = stamp('DEAD BOX', size=118); ST_UNPUB = stamp('NOT PUBLISHED', (150, 160, 180), 64)
MB = mini_box(False); MBD = mini_box(True)
L_REP = label_sprite('EARLY REPORTS', 'بلاغات أولية'); L_EB = label_sprite('SAME STORY?', 'نفس القصة؟')
L_RATE = label_sprite('PULL RATES', 'نسب السحب'); L_MKT = label_sprite('MARKET PRICE', 'سعر السوق')
L_YOU = label_sprite('YOUR CALL', 'وش رايك؟'); L_AV = label_sprite('IN STOCK', 'متوفر عندنا')
T_HITS = text_sprite('HITS', FB(64), fill=(200, 210, 230), pad=20)
NUMS = {n: text_sprite(str(n), FB(190), fill=WHITE if n else (255, 70, 80), stroke=6, stroke_fill=(0, 0, 0), pad=30) for n in range(9)}
T_EQ = text_sprite('=?', FB(150), fill=WHITE, stroke=6, stroke_fill=(0, 0, 0), pad=30)
T_OP18 = text_sprite('OP-18', FB(66), fill=WHITE, pad=20); T_EB05 = text_sprite('EB-05', FB(66), fill=(255, 160, 200), pad=20)
def rate_card():
    w, h = 760, 560; im = panel(w, h, (255, 255, 255), r=44, alpha=255); d = ImageDraw.Draw(im)
    f = FB(54); bb = d.textbbox((0, 0), 'BANDAI', font=f); d.text((40 + (w - (bb[2] - bb[0])) / 2 - bb[0], 80), 'BANDAI', font=f, fill=NAVY)
    f2 = FB(230); bb = d.textbbox((0, 0), '??%', font=f2); d.text((40 + (w - (bb[2] - bb[0])) / 2 - bb[0], 180), '??%', font=f2, fill=RED)
    f3 = FL(60); s = 'نسبة الهت في البوكس'; bb = d.textbbox((0, 0), s, font=f3); d.text((40 + (w - (bb[2] - bb[0])) / 2 - bb[0], 470), s, font=f3, fill=(90, 100, 120))
    return to_bgra(im)
RATE = rate_card()
CH_YES = pill('يأكد؟', FL(70), (70, 80, 100)); CH_NO = pill('ينفي؟', FL(70), (70, 80, 100))
def price_chart():
    w, h = 900, 600; im = panel(w, h, (24, 32, 54), r=40, alpha=250, border=(60, 74, 104)); d = ImageDraw.Draw(im)
    y200 = 40 + 400; d.line((80, y200, 40 + w - 40, y200), fill=(255, 255, 255, 120), width=4)
    for x in range(80, 40 + w - 40, 36): d.line((x, y200, x + 18, y200), fill=(255, 255, 255, 230), width=5)
    fl = FB(40); d.text((90, y200 + 14), '$200', font=fl, fill=(220, 230, 245))
    fl2 = FL(40); d.text((40 + w - 300, 40 + h - 70), 'eBay · تقريبي', font=fl2, fill=(150, 160, 185))
    return to_bgra(im)
CHART = price_chart()
P300 = text_sprite('$300', FB(130), fill=WHITE, stroke=6, stroke_fill=(0, 0, 0), pad=30)
P200 = text_sprite('<$200', FB(150), fill=(255, 70, 80), stroke=6, stroke_fill=(0, 0, 0), pad=30)
def side_panel(top, bottom, col, kind):
    w, h = 470, 640; im = panel(w, h, col, r=40, alpha=245); d = ImageDraw.Draw(im)
    f = FL(64); y = 90
    for line in top:
        bb = d.textbbox((0, 0), line, font=f); d.text((40 + (w - (bb[2] - bb[0])) / 2 - bb[0], y), line, font=f, fill=WHITE); y += 92
    return to_bgra(im)
PL = side_panel(['للي يجمع', 'ويلعب'], None, (22, 140, 128), 'v'); PR = side_panel(['للي يفتح', 'عشان الهت'], None, (180, 30, 44), 'x')
V_OK = text_sprite('خبر حلو', FL(96), fill=WHITE, stroke=6, stroke_fill=(0, 0, 0), pad=24); V_BAD = text_sprite('خسارة', FL(96), fill=WHITE, stroke=6, stroke_fill=(0, 0, 0), pad=24)
BG_OK = badge('v', TEALc); BG_X = badge('x', RED)
BTN_A = pill('حلو', FL(130), (22, 150, 136)); BTN_B = pill('خربوها', FL(130), (200, 30, 46))
T_VS = text_sprite('ولا', FL(90), fill=(200, 210, 230), pad=20); T_CMT = text_sprite('بكلمة وحدة بالتعليقات', FL(76), fill=WHITE, pad=24)
BUB = bubble(); PLANE = plane()
P_SHARE = pill('أرسله لخويك اللي يفتح بوكسات', FL(64), (44, 70, 130)); P_SAVE = pill('احفظه', FL(76), (70, 80, 100)); P_FOL = pill('تابع HTR', FL(76), RED)
P_SITE = pill('HTRTCG.COM', FB(60), RED); T_ONL = text_sprite('أونلاين', FL(110), fill=WHITE, stroke=6, stroke_fill=(0, 0, 0), pad=24)
T_PLUS = text_sprite('+ المعرض', FL(96), fill=(255, 200, 205), stroke=6, stroke_fill=(0, 0, 0), pad=24)
T_OLAYA = text_sprite('العليا سكوير', FL(170), fill=WHITE, stroke=8, stroke_fill=(0, 0, 0), pad=30)
T_ABHUR = text_sprite('أبحر الجنوبية – جدة', FL(84), fill=(255, 205, 210), stroke=6, stroke_fill=(0, 0, 0), pad=24)
CAPS = [(c[0], c[1], caption_sprite(c[2], c[3] if len(c) > 3 else False)) for c in CAP]

def pop(t, t0, d=.28): return ebk((t - t0) / d) if t >= t0 else 0.0
def fadein(t, t0, d=.2): return cl((t - t0) / d)
def shake(t, t0, amp=16, d=.3):
    if not (t0 <= t < t0 + d): return 0, 0
    k = 1 - (t - t0) / d; return amp * k * math.sin(t * 90), amp * k * math.cos(t * 77)

# ---------- beats (times from ex_cues.json; words at cue times)
K = C['k']
def s1(t, f):  # hook: box on screen from frame 1, DEAD BOX slams on «فاضية»
    fl = 1 + .015 * math.sin(t * 2.2); dead = t >= K['dead']
    g = f
    blit(f, BOX, 540, 830 + 10 * math.sin(t * 1.6), .98 * fl)
    if dead:
        p = pop(t, K['dead'], .22); blit(f, ST_DEAD, 540, 840, 1.8 - .8 * p if p < 1 else 1.0, cl(p * 2), -12)
def s2(t, f):  # case grid fills, then each box gets ✗, hits count 8 → 0
    blit(f, L_REP, 540, 520, pop(t, O['L2']))
    for i in range(12):
        r, c = divmod(i, 4); cx, cy = 165 + c * 250, 700 + r * 190
        ti = O['L2'] + .15 + i * .1; tx = K['grid_x'] + i * .12
        if t < ti: continue
        blit(f, MBD if t >= tx else MB, cx, cy, .82 * pop(t, ti, .22))
    n = 8 - int(cl((t - K['grid_x']) / (12 * .12 + .3)) * 8)
    blit(f, T_HITS, 540, 1110, fadein(t, O['L2'] + .6)); blit(f, NUMS[n], 540, 1230, fadein(t, O['L2'] + .6) * (1.15 if n == 0 and t < K['grid_x'] + 1.9 else 1.0))
def s3(t, f):  # OP-18 vs EB-05
    blit(f, L_EB, 540, 520, pop(t, O['L3']))
    blit(f, BOX_S, 290 - 300 * (1 - eo((t - O['L3']) / .35)), 820, .95); blit(f, T_OP18, 290, 1090, fadein(t, O['L3'] + .2))
    te = K['eb']
    if t >= te - .1:
        blit(f, EBBOX, 790 + 300 * (1 - eo((t - te + .1) / .35)), 820, .95); blit(f, T_EB05, 790, 1090, fadein(t, te))
        blit(f, T_EQ, 540, 820, pop(t, te + .25))
def s4(t, f):  # pull rates not published
    blit(f, L_RATE, 540, 520, pop(t, O['L4']))
    blit(f, RATE, 540, 860, pop(t, O['L4'] + .15) * (1 + .01 * math.sin(t * 3)))
    if t >= K['unpub']: blit(f, ST_UNPUB, 540, 990, pop(t, K['unpub'], .22), 1, -8)
    if t >= K['yes']: blit(f, CH_YES, 330, 1240, pop(t, K['yes']))
    if t >= K['no']: blit(f, CH_NO, 750, 1240, pop(t, K['no']))
def s5(t, f):  # price under $200
    blit(f, L_MKT, 540, 520, pop(t, O['L5']))
    blit(f, CHART, 540, 900, fadein(t, O['L5'] + .1, .25))
    # falling line drawn progressively: chart inner box x 130..950, $200 line at y ~ 900-300+40+400
    x0, y0 = 150, 650; pts = [(150, 650), (300, 640), (430, 700), (560, 690), (690, 820), (820, 980), (930, 1030)]
    pr = cl((t - O['L5'] - .3) / 2.4); nseg = pr * (len(pts) - 1)
    for i in range(int(nseg) + 1):
        if i >= len(pts) - 1: break
        a, b = pts[i], pts[i + 1]; u = cl(nseg - i); bx = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        cv2.line(f, a, (int(bx[0]), int(bx[1])), bgr((255, 70, 80)), 12, cv2.LINE_AA)
    if pr > 0:
        i = min(int(nseg), len(pts) - 2); u = cl(nseg - i); a, b = pts[i], pts[i + 1]
        cv2.circle(f, (int(a[0] + (b[0] - a[0]) * u), int(a[1] + (b[1] - a[1]) * u)), 20, bgr((255, 255, 255)), -1, cv2.LINE_AA)
    blit(f, P300, 330, 760, fadein(t, O['L5'] + .3) * (1 - .6 * cl((t - K['p200']) / .3)))
    if t >= K['p200']: blit(f, P200, 650, 1250, pop(t, K['p200']))
def s6(t, f):  # split: collectors vs openers
    blit(f, L_YOU, 540, 520, pop(t, O['L6']))
    blit(f, PL, 285, 920, pop(t, O['L6'] + .2)); blit(f, PR, 795, 920, pop(t, K['open'] - .2))
    if t >= K['good']: blit(f, BG_OK, 285, 1100, pop(t, K['good'])); blit(f, V_OK, 285, 1230, fadein(t, K['good']))
    if t >= K['loss']: blit(f, BG_X, 795, 1100, pop(t, K['loss'])); blit(f, V_BAD, 795, 1230, fadein(t, K['loss']))
def s7(t, f):  # vote in comments + share + save + follow
    blit(f, BUB, 540, 560, pop(t, O['L7']))
    blit(f, BTN_A, 540, 780, pop(t, K['a'])); blit(f, T_VS, 540, 905, fadein(t, K['a'] + .3)); blit(f, BTN_B, 540, 1030, pop(t, K['b']))
    blit(f, T_CMT, 540, 1180, fadein(t, O['L7'] + .5))
    if t >= K['share']:
        k = pop(t, K['share']); blit(f, P_SHARE, 540, 1290, k)
        blit(f, PLANE, 900 + 60 * (t - K['share']), 1160 - 40 * (t - K['share']), k, 1, 10)
    if t >= K['save']: blit(f, P_SAVE, 380, 1420, pop(t, K['save']))
    if t >= K['fol']: blit(f, P_FOL, 700, 1420, pop(t, K['fol']))
def s8(t, f):  # in stock online
    blit(f, L_AV, 540, 520, pop(t, O['L8']))
    blit(f, BOX_S, 380, 820, pop(t, O['L8'] + .1) * 1.1); blit(f, PACK, 790, 860, pop(t, O['L8'] + .3) * .9, 1, 6)
    blit(f, T_ONL, 540, 1120, pop(t, K['onl'])); blit(f, P_SITE, 540, 1250, pop(t, K['onl'] + .2))
    if t >= K['plus']: blit(f, T_PLUS, 540, 1390, pop(t, K['plus']))
def s9(t, f):  # showroom
    blit(f, LOGO, 540, 700, pop(t, O['OL']) * .9)
    if t >= K['olaya']: blit(f, T_OLAYA, 540, 1000, pop(t, K['olaya']))
    blit(f, T_ABHUR, 540, 1150, fadein(t, O['OL'] + .2))
SCN = [(0, s1), (O['L2'] - .05, s2), (O['L3'] - .05, s3), (O['L4'] - .05, s4), (O['L5'] - .05, s5), (O['L6'] - .05, s6), (O['L7'] - .05, s7), (O['L8'] - .05, s8), (O['OL'] - .02, s9), (K['loop'], s1)]
GLOW = {s1: 1.0, s2: .6, s3: .5, s4: .3, s5: .8, s6: .4, s7: .5, s8: .9, s9: 1.0}

def render(t):
    cur, st = SCN[0][1], 0
    for t0, fn in SCN:
        if t >= t0: cur, st = fn, t0
    f = background(t, GLOW[cur])
    cur(t, f)
    # header + small HTR tag always on
    blit(f, TITLE, 540, 340); blit(f, HTRTAG, 940, 1560, .9)
    # word-synced captions (one chunk at a time)
    for a, b, spr in CAPS:
        if a <= t < b: blit(f, spr, 540, 1480 if cur in (s7, s8) else 1420, .9 + .1 * ebk((t - a) / .15)); break
    # camera: slow push-in per beat + tiny drift; hit-shakes on stamps
    z = 1 + .02 * (t - st); dx, dy = shake(t, K['dead']); ex, ey = shake(t, K['grid_x'] + 12 * .12, 10); dx += ex; dy += ey
    M = np.float32([[z, 0, (1 - z) * 540 + dx], [0, z, (1 - z) * 900 + dy]]); f = cv2.warpAffine(f, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    if cur is not s1 and t - st < .12: f = f * (1 - .25 * (1 - (t - st) / .12)) + 255 * .25 * (1 - (t - st) / .12)  # quick flash on each beat cut
    return np.clip(f, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'frames':
        for t in [float(x) for x in sys.argv[2].split(',')]: cv2.imwrite(f'/home/claude/work/ex_{t:.1f}.jpg', render(t))
        sys.exit()
    a, b = RANGE or (0, TOTAL); n = int(round((b - a) * FPS))
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    for i in range(n): p.stdin.write(render(a + i / FPS).tobytes())
    p.stdin.close(); p.wait(); print('ok', OUT, n)
