# rot9 — Digimon AD-01 vs Yu-Gi-Oh! Magnificent Monsters + Delta Reign bonus — cinematic redesign
# AI scene plates (Gemini, Hadi's subscription) + REAL product photos composited with contact shadow, reflection,
# parallax camera, light sweeps, embers and premium metallic type. Same cue timing as rot8 (approved voice, 0 credits).
# ONE timeline, whole-video render (render(t) deterministic).
import os, sys, math
os.environ.setdefault('CUES', 'yd_cues.json')
_src = open('/home/claude/htr-videos/tools_ads/rot8/dr_render.py', encoding='utf-8').read()
exec(_src.split('# ---------- background')[0])  # shared helpers: text_sprite, img_sprite, blit, cutout, easing, fonts
OUT = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != 'frames' else '/home/claude/work/yd2_v.mp4'
P = R + 'tools_ads/rot9/plates/'
PH = int(2752 * W / 1536)  # 1935

def plate(fn, blur=0):
    im = Image.open(P + fn).convert('RGB').resize((W, PH), Image.LANCZOS)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    return np.array(im)[..., ::-1].astype(np.float32)
PL = {k: plate(v) for k, v in dict(arc='p1_arcade.jpg', dig='p2_digimon.jpg', ygo='p3_ygo.jpg', dr='p4_delta.jpg', shw='p5_showroom.jpg').items()}
PLB = {k: plate(v, 9) for k, v in dict(arc='p1_arcade.jpg', dig='p2_digimon.jpg', ygo='p3_ygo.jpg', shw='p5_showroom.jpg').items()}
# pedestal top-centre (x, y) in frame coords, measured on the plates
PED = dict(arc=(540, 1205), dig=(540, 1090), ygo=(540, 1150), dr=(540, 1120), shw=(560, 1035))

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
EDGE = np.clip((np.minimum(xx, W - 1 - xx) - 10) / 22, 0, 1)[..., None] ** .8
VIG = EDGE * (1 - .38 * np.clip(((xx - 540) ** 2 / 560 ** 2 + (yy - 900) ** 2 / 1050 ** 2) - .3, 0, 1))[..., None]
rng = np.random.default_rng(9)
GRAIN = [rng.normal(0, 4.5, (H // 2, W // 2, 1)).astype(np.float32) for _ in range(6)]

def cam(img, t, t0, z0=1.06, z1=1.14, px=0.0, py=0.0, dur=3.5):
    """slow dolly-in + drift on the plate (camera move). img may be taller than H."""
    k = eio((t - t0) / dur); z = z0 + (z1 - z0) * k
    M = np.float32([[z, 0, (1 - z) * W / 2 + px * k], [0, z, (1 - z) * (img.shape[0] / 2) - (img.shape[0] - H) / 2 + py * k]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def embers(f, t, col, n=40, seed=1, speed=60, big=1.0, depth=1.0):
    r = np.random.default_rng(seed)
    for i in range(n):
        x, y, s, ph, v = r.uniform(0, W), r.uniform(0, H), r.uniform(1.5, 4.5) * big, r.uniform(0, 6.3), r.uniform(.4, 1.3)
        yy_ = (y - t * speed * v * depth) % (H + 40) - 20; xx_ = x + 26 * math.sin(t * .8 * v + ph)
        a = .5 + .5 * math.sin(t * 3 * v + ph)
        c = tuple(float(cc * (0.5 + .5 * a)) for cc in col)
        cv2.circle(f, (int(xx_), int(yy_)), int(s + 4), tuple(cc * .25 for cc in c), -1, cv2.LINE_AA)
        cv2.circle(f, (int(xx_), int(yy_)), int(s), c, -1, cv2.LINE_AA)

def sweep(f, t, t0, col=(255, 255, 255), d=.7, strength=.35):
    """diagonal light sweep across the frame (motivated by a cut / reveal)"""
    k = (t - t0) / d
    if not 0 <= k <= 1: return
    pos = -400 + k * (W + H + 800); band = np.exp(-(((xx + yy * .55) - pos) ** 2) / (2 * 110 ** 2))[..., None]
    f[:] = f + band * np.array(col, np.float32) * strength

def glowflash(f, t, t0, col=(255, 240, 220), d=.18, s=.55):
    if t0 <= t < t0 + d: f[:] = f + (np.array(col, np.float32) - f) * (1 - (t - t0) / d) ** 2 * s

def shake(t, t0, amp=14, d=.28):
    if t < t0 or t > t0 + d: return 0, 0
    k = (1 - (t - t0) / d) ** 2; return amp * k * math.sin((t - t0) * 90), amp * k * math.cos((t - t0) * 77)

# ---------- product sprites with reflection + contact shadow
def ld(p): return Image.open(F + p).convert('RGBA')
def product(im, w, glow, glow_r=34):
    s = w / im.width; im = im.resize((w, int(im.height * s)), Image.LANCZOS)
    a = im.split()[3]; bb = a.getbbox(); im = im.crop(bb)
    pad = glow_r * 2; refl_h = int(im.height * .45)
    c = Image.new('RGBA', (im.width + 2 * pad, im.height + refl_h + 2 * pad), (0, 0, 0, 0))
    g = Image.new('RGBA', c.size, glow + (0,)); ga = Image.new('L', c.size, 0); ga.paste(im.split()[3], (pad, pad))
    g.putalpha(ga.filter(ImageFilter.GaussianBlur(glow_r)).point(lambda v: min(255, int(v * .9)))); c = Image.alpha_composite(c, g)
    # reflection
    rf = im.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, im.width, refl_h)); ra = np.array(rf.split()[3]).astype(np.float32)
    ra *= np.linspace(.32, 0, refl_h)[:, None]; rf.putalpha(Image.fromarray(ra.astype(np.uint8))); rf = rf.filter(ImageFilter.GaussianBlur(2))
    c.alpha_composite(rf, (pad, pad + im.height + 4))
    # contact shadow
    sh = Image.new('L', c.size, 0); ImageDraw.Draw(sh).ellipse((pad + im.width * .08, pad + im.height - 16, pad + im.width * .92, pad + im.height + 22), fill=200)
    shl = Image.new('RGBA', c.size, (0, 0, 0, 0)); shl.putalpha(sh.filter(ImageFilter.GaussianBlur(14))); c = Image.alpha_composite(c, shl)
    c.alpha_composite(im, (pad, pad))
    arr = to_bgra(c); return arr, (pad + im.height)  # anchor = baseline row inside sprite

def put(f, spr, bx, by, s=1.0, a=1.0, rot=0.0):
    """place product so its base sits at (bx, by)"""
    arr, base = spr; h = arr.shape[0]
    cy = by - (base - h / 2) * s; blit(f, arr, bx, cy, s, a, rot)

DG = product(ld('ad01_gn1.png'), 520, (40, 140, 255)); DGP = product(ld('ad01_gn2.png').convert('RGBA'), 330, (40, 160, 255), 26)
YG = product(ld('ygo_mamo_box.png'), 560, (60, 190, 255)); DR = product(cutout(F + 'dr_box_b.jpg'), 470, (120, 60, 255))
LOGO = img_sprite(Image.open(R + 'tools_challenges/htr_logo.png').convert('RGBA'), 560, (255, 230, 200), 26)

# ---------- premium type
def metal(s, font, top, bot, stroke=5, stroke_col=(20, 10, 30), glow=None, glow_r=22, pad=60):
    d0 = ImageDraw.Draw(Image.new('RGBA', (10, 10))); bb = d0.textbbox((0, 0), s, font=font, stroke_width=stroke)
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad; ox, oy = pad - bb[0], pad - bb[1]
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if glow:
        m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).text((ox, oy), s, font=font, fill=255, stroke_width=stroke + 8)
        g = Image.new('RGBA', (w, h), glow + (0,)); g.putalpha(m.filter(ImageFilter.GaussianBlur(glow_r)).point(lambda v: min(255, int(v * 1.4)))); out = Image.alpha_composite(out, g)
    sh = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ImageDraw.Draw(sh).text((ox + 4, oy + 12), s, font=font, fill=(0, 0, 0, 170), stroke_width=stroke)
    out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(7)))
    st = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ImageDraw.Draw(st).text((ox, oy), s, font=font, fill=stroke_col + (255,), stroke_width=stroke, stroke_fill=stroke_col + (255,)); out = Image.alpha_composite(out, st)
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).text((ox, oy), s, font=font, fill=255)
    gy = np.linspace(0, 1, h)[:, None, None]; grad = np.array(top, np.float32) * (1 - gy) + np.array(bot, np.float32) * gy
    shine = np.exp(-((np.linspace(0, 1, h) - .38) ** 2) / .004)[:, None, None] * 60
    gi = np.clip(np.repeat(grad + shine, w, 1), 0, 255).astype(np.uint8); fill = Image.fromarray(gi, 'RGB').convert('RGBA'); fill.putalpha(m)
    out = Image.alpha_composite(out, fill); return to_bgra(out)
GOLD = ((255, 246, 200), (214, 150, 40)); SILV = ((255, 255, 255), (150, 170, 200)); ORG = ((255, 230, 170), (255, 120, 20))
CYAN = ((230, 255, 255), (40, 190, 230)); RED = ((255, 220, 220), (230, 30, 60))
def ar(s, size, g=SILV, glow=(0, 0, 0), stroke=6): return metal(s, FL(size), g[0], g[1], stroke, (16, 8, 26), glow, 20)
def en(s, size, g=GOLD, glow=None, font=None): return metal(s, (font or FA)(size), g[0], g[1], 5, (24, 12, 6), glow, 24)

T_PICK = ar('اختار لاعبك', 150, SILV, (180, 60, 255))
E_DIG = en('DIGIMON', 150, ORG, (255, 120, 20)); E_AD = en('GENERATION AD-01', 70, SILV, (40, 140, 255))
E_YGO = en('YU-GI-OH!', 150, GOLD, (255, 180, 40)); E_MAMO = en('MAGNIFICENT MONSTERS', 64, SILV, (150, 70, 255))
E_VS = en('VS', 330, GOLD, (255, 90, 20)); T_WHO = ar('مين يكسب؟', 150, GOLD, (255, 120, 20))
T_C12 = ar('علّق 1 ولا 2', 130, SILV, (255, 60, 160))
E_1 = en('1', 230, ORG, (255, 120, 20)); E_2 = en('2', 230, GOLD, (150, 70, 255))
E_BONUS = en('BONUS STAGE', 120, RED, (255, 40, 80)); E_DR = en('DELTA REIGN', 96, SILV, (160, 60, 255))
T_DR = ar('بوكس دلتا رين كامل', 104, SILV, (200, 40, 90))
T_RB = ar('ريال بس!', 140, SILV, (255, 40, 80)); _NUM = {}
def num(n, size=300):
    k = (n, size)
    if k not in _NUM: _NUM[k] = en(str(n), size, RED if size < 300 else GOLD, (255, 50, 80))
    return _NUM[k]
T_ON = ar('كلهم متوفرين أونلاين', 112, SILV, (40, 200, 230)); E_SITE = en('HTRTCG.COM', 92, CYAN, (40, 200, 230))
T_SHOW = ar('وفي معرضنا', 150, GOLD, (40, 200, 200))
T_OLAYA = ar('العليا سكوير', 190, GOLD, (255, 170, 60), 8); T_ABHUR = ar('أبحر الجنوبية – جدة', 88, SILV, (40, 200, 200))
T_SHARE = ar('أرسله لخويك', 150, GOLD, (255, 120, 20)); T_SHARE2 = ar('اللي يلعب يوغي أوو أو ديجيمون', 76, SILV, (150, 70, 255))
T_CMT = ar('علّق ولو بنقطة', 130, GOLD, (255, 120, 20)); T_LIKE = ar('لايك وسيف', 120, CYAN, (40, 200, 230))
P_TF = pill('تابع HTR', FL(88), (200, 30, 90))

def pin(f, cx, cy, s=1.0):
    r = int(80 * s); cv2.circle(f, (cx, cy), r + 18, (60, 200, 255), -1, cv2.LINE_AA)
    cv2.circle(f, (cx, cy), r, (40, 60, 230), -1, cv2.LINE_AA); cv2.circle(f, (cx, cy), int(r * .4), (255, 255, 255), -1, cv2.LINE_AA)
    cv2.fillPoly(f, [np.array([[cx - r * .8, cy + r * .6], [cx + r * .8, cy + r * .6], [cx, cy + r * 2.1]], np.int32)], (40, 60, 230), cv2.LINE_AA)

def topfade(f, h=520, a=.7):
    a *= float(os.environ.get('TOPK', '0'))
    g = np.linspace(a, 0, h)[:, None, None]; f[:h] *= (1 - g)

# ---------- scenes
def s_select(t, f):  # 0–3.05 calm: arcade stage, both fighters on the pedestal
    f[:] = cam(PL['arc'], t, 0, 1.0, 1.13, 50, -40, 3.05); topfade(f)
    embers(f, t, (120, 200, 255), 45, 3, 70, 1.2)
    bx, by = PED['arc']; put(f, DG, 330, by - 20, .76 + .01 * math.sin(t * 2)); put(f, YG, 750, by - 20, .72 + .01 * math.sin(t * 2 + 1))
    blit(f, T_PICK, 540, 330, 1.0 + .03 * eio(t / 3), cl(t / .25))
def s_p1(t, f):  # P1 Digimon lands on the digital arena (cut on «ديجيمون»)
    dt = t - T['p1']; dx, dy = shake(t, T['p1'] + .3)
    f[:] = cam(PL['dig'], t, T['p1'], 1.12, 1.04, 0, 0, 1.3); topfade(f)
    embers(f, t, (60, 160, 255), 50, 4, 90)
    bx, by = PED['dig']; drop = 900 * (1 - ebk(dt / .35))
    put(f, DG, bx + dx, by - drop + dy, .95 + .015 * math.sin(t * 3))
    blit(f, E_DIG, 540, 300, 1.0 + .25 * (1 - ebk(dt / .3)), cl(dt / .08)); blit(f, E_AD, 540, 1560, 1, cl((dt - .6) / .15))
    glowflash(f, t, T['p1'] + .3, (120, 200, 255)); sweep(f, t, T['p1'] + .35, (120, 200, 255))
def s_p1b(t, f):  # close-up on the English pack (cut on «Digimon Generation»)
    dt = t - T['p1b']; f[:] = cam(PLB['dig'], t, T['p1b'], 1.25, 1.32, 0, 0, 2.5); topfade(f, 400, .5)
    embers(f, t, (60, 160, 255), 35, 5, 70, 1.6, 1.4)
    put(f, DGP, 540, 1420, 1.9 + .06 * eio(dt / 2.5), 1, -3 + 2 * math.sin(t * 2.2)); blit(f, E_AD, 540, 1640, 1.1)
    sweep(f, t, T['p1b'] + .1, (255, 220, 160), .9, .25)
def s_p2(t, f):  # P2 Yu-Gi-Oh descends in the golden beam (cut on «ضد»)
    dt = t - T['p2']; dx, dy = shake(t, T['p2'] + .3)
    f[:] = cam(PL['ygo'], t, T['p2'], 1.12, 1.04, 0, 0, 1.3); topfade(f)
    embers(f, t, (80, 200, 255), 45, 6, 45)
    bx, by = PED['ygo']; drop = 900 * (1 - ebk(dt / .38))
    put(f, YG, bx + dx, by - drop + dy, .92 + .015 * math.sin(t * 3))
    blit(f, E_YGO, 540, 300, 1.0 + .25 * (1 - ebk(dt / .3)), cl(dt / .08)); blit(f, E_MAMO, 540, 1560, 1, cl((dt - .6) / .15))
    glowflash(f, t, T['p2'] + .3, (120, 220, 255)); sweep(f, t, T['p2'] + .35, (100, 210, 255))
def s_p2b(t, f):  # close-up on «Magnificent Monsters»
    dt = t - T['p2b']; f[:] = cam(PLB['ygo'], t, T['p2b'], 1.25, 1.32, 0, 0, 2.2); topfade(f, 400, .5)
    embers(f, t, (80, 200, 255), 35, 7, 60, 1.6, 1.4)
    put(f, YG, 540, 1420, 1.35 + .05 * eio(dt / 2.2), 1, 2 - 2 * math.sin(t * 2.2)); blit(f, E_MAMO, 540, 1640, 1.1)
    sweep(f, t, T['p2b'] + .1, (255, 220, 160), .9, .25)
SPLIT = None
def split_bg(t, t0):
    a = cam(PL['dig'], t, t0, 1.1, 1.14, -40, 0, 2); b = cam(PL['ygo'], t, t0, 1.1, 1.14, 40, 0, 2)
    m = ((xx - 540) + (yy - 960) * .28 < 0)[..., None]; f = np.where(m, a, b)
    return f
def seam(f, t):
    pts = [];
    for i in range(14):
        y = i * 150; x = 540 - (y - 960) * .28 + (18 * math.sin(i * 2.3 + t * 30) if i % 2 else 0); pts.append([int(x), int(y)])
    p = np.array(pts, np.int32); cv2.polylines(f, [p], False, (255, 230, 200), 22, cv2.LINE_AA); cv2.polylines(f, [p], False, (255, 255, 255), 6, cv2.LINE_AA)
def faceoff(f, t):
    put(f, DG, 280, 1200 + 6 * math.sin(t * 3), .72, 1, -3); put(f, YG, 805, 1200 - 6 * math.sin(t * 3), .68, 1, 3)
def s_round(t, f):  # VS split (cut on «مين يكسب»)
    dt = t - T['round']; f[:] = split_bg(t, T['round']); topfade(f, 600, .6); seam(f, t)
    embers(f, t, (60, 200, 255), 50, 8, 100)
    faceoff(f, t); blit(f, E_VS, 540, 560, 1.0 + .6 * (1 - ebk(dt / .28)) + .04 * abs(math.sin(t * 8)), cl(dt / .05))
    blit(f, T_WHO, 540, 1560, 1, cl((dt - .2) / .15)); glowflash(f, t, T['round'], (255, 240, 220), .2, .7)
def s_round2(t, f):  # «علّق 1 ولا 2»
    dt = t - T['round2']; f[:] = split_bg(t, T['round']); topfade(f, 600, .6); seam(f, t)
    embers(f, t, (60, 200, 255), 50, 8, 100); faceoff(f, t)
    blit(f, E_1, 285, 520, 1.0 + .12 * abs(math.sin(t * 7)), cl(dt / .1)); blit(f, E_2, 800, 520, 1.0 + .12 * abs(math.sin(t * 7 + 1.5)), cl(dt / .1))
    blit(f, T_C12, 540, 1560, 1.0 + .2 * (1 - ebk(dt / .25)))
def s_bonus(t, f):  # Delta Reign rises from the crystal; score counts to 850
    dt = t - T['bonus']; dx, dy = shake(t, T['bonus'] + .45, 16, .3)
    f[:] = cam(PL['dr'], t, T['bonus'], 1.14, 1.04, 0, 0, 2.0); topfade(f)
    embers(f, t, (120, 60, 255), 60, 9, 120, 1.2)
    bx, by = PED['dr']; rise = 500 * (1 - ebk((dt - .1) / .4))
    put(f, DR, bx + dx, by - 40 + rise + dy, .95 + .02 * math.sin(t * 3), cl((dt - .1) / .15))
    blit(f, E_BONUS, 540, 250, 1.0 + .3 * (1 - ebk(dt / .25)), cl(dt / .06)); blit(f, E_DR, 540, 380, 1, cl((dt - .3) / .15))
    sc = int(850 * eo((dt - .5) / 1.4)) if dt > .5 else 0; blit(f, num(sc, 200), 540, 1470, 1, cl((dt - .5) / .1))
    blit(f, T_DR, 540, 1640, 1, cl((dt - .25) / .2)); glowflash(f, t, T['bonus'] + .45, (200, 120, 255), .22, .6); sweep(f, t, T['bonus'] + .5, (200, 140, 255))
def s_b850(t, f):  # cut on the price: big 850
    dt = t - T['b850']; f[:] = cam(PL['dr'], t, T['b850'], 1.3, 1.36, 0, -60, 1.8); f *= .7; topfade(f)
    embers(f, t, (120, 60, 255), 60, 10, 140, 1.4)
    put(f, DR, 720, 1420, .6, 1, 6); blit(f, num(850, 320), 470, 560, 1.0 + .35 * (1 - ebk(dt / .25)), 1, -4); blit(f, T_RB, 470, 820, 1, cl((dt - .25) / .15), -4)
    glowflash(f, t, T['b850'], (255, 255, 255), .15, .6)
def s_site(t, f):  # «كلهم متوفرين أونلاين على موقعنا» — all three on the arcade stage
    dt = t - T['site']; f[:] = cam(PL['arc'], t, T['site'], 1.08, 1.0, 0, 0, 3.4); topfade(f)
    embers(f, t, (255, 120, 220), 40, 11, 60)
    bx, by = PED['arc']
    for i, (spr, x, s) in enumerate(((DG, 250, .5), (DR, 830, .55), (YG, 540, .5))):
        k = ebk((dt - .12 * i) / .35); put(f, spr, x, by - 15 - 600 * (1 - k), s, cl((dt - .12 * i) / .1))
    blit(f, LOGO, 540, 300, 1.0 + .15 * (1 - ebk(dt / .3)), cl(dt / .1)); blit(f, T_ON, 540, 1530, 1, cl((dt - .2) / .2)); blit(f, E_SITE, 540, 1690, 1, cl((dt - 1.0) / .15))
    sweep(f, t, T['site'] + .1, (255, 200, 255))
def s_show(t, f):  # «وفي معرضنا» — the showroom, pin drops onto the counter
    dt = t - T['show']; f[:] = cam(PL['shw'], t, T['show'], 1.0, 1.08, 0, 0, 2.0); topfade(f, 500, .5)
    embers(f, t * .6, (200, 230, 255), 25, 12, 25, .8)
    bx, by = PED['shw']; blit(f, LOGO, bx, by - 110, .55, cl((dt - .2) / .2))
    k = ebk(dt / .4); pin(f, bx, int(by - 470 - 260 * (1 - k)), 1.0)
    blit(f, T_SHOW, 540, 1560, 1.0 + .15 * (1 - ebk(dt / .25)), cl(dt / .12)); sweep(f, t, T['show'] + .1, (255, 240, 210), .9, .3)
def s_olaya(t, f):  # cut on «العليا»: name card over the showroom
    dt = t - T['olaya2']; f[:] = cam(PLB['shw'], t, T['olaya2'], 1.15, 1.22, 0, 0, 1.4); f *= .55
    embers(f, t, (255, 220, 160), 30, 13, 40)
    blit(f, T_OLAYA, 540, 880, 1.0 + .25 * (1 - ebk(dt / .3))); blit(f, T_ABHUR, 540, 1090, 1, cl((dt - .15) / .2))
    pin(f, 540, 560, .8 + .05 * math.sin(t * 5)); glowflash(f, t, T['olaya2'], (255, 240, 210), .15, .5)
def s_share(t, f):  # share trigger
    dt = t - T['share']; f[:] = split_bg(t, T['share']); f *= .75; topfade(f, 600, .6); seam(f, t)
    faceoff(f, t); blit(f, T_SHARE, 540, 430, 1.0 + .25 * (1 - ebk(dt / .25))); blit(f, T_SHARE2, 540, 1560, 1, cl((dt - .8) / .2))
def s_end(t, f):  # comment / like / save
    dt = t - T['end']; f[:] = cam(PLB['arc'], t, T['end'], 1.05, 1.12, 0, 0, 2.5); f *= .7
    embers(f, t, (255, 120, 220), 40, 14, 60)
    blit(f, LOGO, 540, 480, .9 + .03 * math.sin(t * 5)); blit(f, T_CMT, 540, 880, 1.0 + .2 * (1 - ebk(dt / .25)))
    blit(f, T_LIKE, 540, 1060, 1.0 + .06 * abs(math.sin(t * 7)), cl((dt - .9) / .2)); blit(f, P_TF, 540, 1300, 1.1 + .08 * abs(math.sin(t * 7)))
def s_follow(t, f):  # cut on «وتابعنا»
    dt = t - T['follow']; f[:] = cam(PL['arc'], t, T['follow'], 1.12, 1.16, 0, 0, 2.6); f *= .6
    f *= .85 + .2 * (.5 + .5 * math.sin(t * 5))
    embers(f, t, (255, 120, 220), 70, 15, 140, 1.3); sweep(f, t, T['follow'] + 1.3, (255, 200, 255), 1.0, .3)
    blit(f, LOGO, 540, 640, 1.0 + .15 * (1 - ebk(dt / .3)) + .03 * math.sin(t * 6)); blit(f, P_TF, 540, 1060, 1.3 + .1 * abs(math.sin(t * 7)))
    sweep(f, t, T['follow'] + .1, (255, 200, 255))

SC = [('s1', s_select), ('p1', s_p1), ('p1b', s_p1b), ('p2', s_p2), ('p2b', s_p2b), ('round', s_round), ('round2', s_round2), ('bonus', s_bonus), ('b850', s_b850), ('site', s_site), ('show', s_show), ('olaya2', s_olaya), ('share', s_share), ('end', s_end), ('follow', s_follow)]
def render(t):
    cur = SC[0][1]
    for k, fn in SC:
        if t >= T[k]: cur = fn
    f = np.zeros((H, W, 3), np.float32); cur(t, f)
    f = f * EDGE
    wm = float(os.environ.get('WARM', '.1')); f[..., 2] *= 1 + wm; f[..., 1] *= 1 + wm * .35; f[..., 0] *= 1 - wm * .5  # warm grade
    f = 255 * (np.clip(f, 0, 255) / 255) ** float(os.environ.get('GAM', '.5')) + float(os.environ.get('LIFT', '0'))  # brighter grade
    g = cv2.resize(GRAIN[int(t * FPS) % 6], (W, H), interpolation=cv2.INTER_NEAREST); f += g[..., None] if g.ndim == 2 else g
    return np.clip(f, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'frames':
        os.makedirs('/home/claude/work', exist_ok=True)
        for t in [float(x) for x in sys.argv[2].split(',')]: cv2.imwrite(f'/home/claude/work/y2_{t:.1f}.jpg', render(t))
        sys.exit()
    n = int(round(TOTAL * FPS))
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    for i in range(n): p.stdin.write(render(i / FPS).tobytes())
    p.stdin.close(); p.wait(); print('ok', OUT, n)
