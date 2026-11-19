# rot8 — One Piece EB-05 / OP-18 «صفحة مانقا» — ONE timeline, whole-video render (render(t) deterministic)
import os, sys, math
os.environ.setdefault('CUES', 'op_cues.json')
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dr_render.py'), encoding='utf-8').read()
exec(_src.split('# ---------- background')[0])  # shared helpers
from PIL import ImageOps  # shared helpers above: text_sprite, pill, img_sprite, blit, cutout, easing, fonts
OUT = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != 'frames' else '/home/claude/work/op_v.mp4'
PAPER = (232, 240, 246)  # BGR of warm paper
BLACK = (18, 16, 20); RED = (40, 30, 215)  # BGR
INKR = (215, 30, 40)  # RGB red ink for PIL
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rng = np.random.default_rng(11)
GRAIN = rng.normal(0, 5, (H // 4, W // 4)).astype(np.float32)
GRAIN = cv2.resize(GRAIN, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
SCREEN = ((((xx // 9) + (yy // 9)) % 2) * 6)[..., None]  # faint screentone
def paper(t):
    f = np.zeros((H, W, 3), np.float32); f[:] = PAPER
    g = np.roll(GRAIN, int(t * 30) % 40, axis=0)  # paper grain drifts: never a frozen frame
    return f + g - SCREEN * .5

# ---------- sprites
def ld(p): return Image.open(F + p).convert('RGBA')
EBBOX = img_sprite(ld('eb05en_pb2.webp'), 600, None)  # ENGLISH box (owner: no Japanese EB-05 box)
EBPACK = img_sprite(ld('eb05en_pb1.webp'), 470, None)
def gray_sil(im, w):
    a = np.array(im.convert('RGBA')); a[..., :3] = 60; return img_sprite(Image.fromarray(a), w, None)
EB_SIL = gray_sil(ld('eb05en_pb2.webp'), 520); OP_SIL = gray_sil(ld('op18_box.webp'), 560)
HANC = img_sprite(ld('eb05en_pb1.webp'), 470, None); NAMI = img_sprite(ld('eb05en_item01.webp'), 470, None)  # English packs only
KV = img_sprite(ld('eb05en_mv.webp'), 900, None, rounded=10)  # official EB-05 art (no card text)
OPBOX = img_sprite(ld('op18_box.webp'), 860, None); OPPACK = img_sprite(ld('rel_op18_box.webp'), 520, None)
DRBOX = img_sprite(cutout(F + 'dr_box_b.jpg'), 470, (150, 110, 255), 40)
LOGO = img_sprite(Image.open(R + 'tools_challenges/htr_logo.png').convert('RGBA'), 600, None)
INKC = (18, 16, 20)
T_OTW = text_sprite('ON THE WAY', FB(110), fill=INKC, pad=30)
T_HOOK = text_sprite('جايين… ومحد جاهز لهم', FL(118), fill=INKC)
T_EB = text_sprite('EB-05', FB(170), fill=(255, 255, 255), pad=30); T_HER = text_sprite('HEROINES EDITION', FB(66), fill=(255, 80, 95), pad=30)
T_BTL = text_sprite('بطلات ون بيس في سيت واحد', FL(84), fill=INKC)
T_OP = text_sprite('OP-18', FB(170), fill=INKC, pad=30); T_DOG = text_sprite('THE DOMINANCE OF GOD', FB(56), fill=INKR, pad=30)
T_Q = text_sprite('أي واحد تبغاه أول؟', FL(120), fill=INKC); T_CM = text_sprite('اكتب 1 ولا 2 بالكومنتات', FL(100), fill=INKR)
T_WAIT = text_sprite('وإلين يوصلون…', FL(110), fill=INKC); T_DR = text_sprite('DELTA REIGN · 850 ريال', FL(100), fill=(255, 255, 255), stroke=5, stroke_fill=(0, 0, 0))
T_SITE = text_sprite('HTRTCG.COM', FB(88), fill=INKC, pad=30); T_SHIP = text_sprite('التوصيل لين باب بيتك', FL(96), fill=INKR)
T_OLAYA = text_sprite('العليا سكوير', FL(170), fill=(255, 255, 255)); T_ABHUR = text_sprite('أبحر الجنوبية – جدة', FL(80), fill=(255, 225, 225))
T_SHARE = text_sprite('أرسله لخويك', FL(150), fill=INKC); T_SHARE2 = text_sprite('اللي يجمع ون بيس', FL(110), fill=INKR)
T_TBC = text_sprite('TO BE CONTINUED', FB(74), fill=(255, 255, 255), pad=30); P_FOLLOW = pill('تابع HTR', FL(84), (215, 30, 40))
T_CMT = text_sprite('علّق ولو بنقطة', FL(118), fill=INKC); T_LIKE = text_sprite('لايك وسيف', FL(118), fill=INKR)
def sfx_sprite(s, col, size=150):
    return text_sprite(s, FB(size), fill=col, stroke=8, stroke_fill=(18, 16, 20), pad=40)
SFX_DON = sfx_sprite('DON!!', (255, 255, 255), 170); SFX_BAM = sfx_sprite('BAM!', (215, 30, 40))

GUNKO = img_sprite(ld('op18_065_gunko_sp.webp'), 640, (255, 60, 70), 60, rounded=26)
GUNKO_SIL = gray_sil(ld('op18_065_gunko_sp.webp'), 560)
T_DATE = text_sprite('ينزل 20 نوفمبر', FL(110), fill=(255, 255, 255), stroke=6, stroke_fill=(18, 16, 20))
T_TOP = text_sprite('أقوى هت بالسيت؟', FL(130), fill=INKC)
T_GUN = text_sprite('GUNKO', FB(120), fill=(255, 255, 255), stroke=6, stroke_fill=(18, 16, 20), pad=30)
P_SP = pill('SUPER PARALLEL · 4TH ANNIVERSARY', FB(40), (215, 30, 40))
T_ONLINE = text_sprite('متوفر أونلاين', FL(130), fill=INKC)
T_WAIT1 = text_sprite('وش تنتظر؟', FL(150), fill=(255, 255, 255), stroke=8, stroke_fill=(18, 16, 20))
T_WAIT2 = text_sprite('ون بيس ما يجلس!', FL(116), fill=(255, 235, 235), stroke=7, stroke_fill=(18, 16, 20))

# ---------- manga drawing helpers (BGR on the numpy frame)
def panel(f, box, w=12): cv2.rectangle(f, (box[0], box[1]), (box[2], box[3]), BLACK, w, cv2.LINE_AA)
def fill_panel(f, box, col): cv2.rectangle(f, (box[0], box[1]), (box[2], box[3]), col, -1)
SPEED = [(r.uniform(0, 6.28), r.uniform(240, 420)) for r in [np.random.default_rng(5)] for _ in range(120)]
def speed(f, box, cx, cy, t, n=120, col=BLACK, k=1.0):
    m = np.zeros((H, W), np.uint8); cv2.rectangle(m, (box[0], box[1]), (box[2], box[3]), 255, -1)
    ov = np.zeros((H, W), np.uint8)
    for i, (a, r0) in enumerate(SPEED[:n]):
        a2 = a + .05 * math.sin(t * 6 + i); r0 = r0 * (1 + .08 * math.sin(t * 9 + i))
        p = np.array([[cx + r0 * math.cos(a2), cy + r0 * math.sin(a2)], [cx + 1500 * math.cos(a2 - .01), cy + 1500 * math.sin(a2 - .01)], [cx + 1500 * math.cos(a2 + .01), cy + 1500 * math.sin(a2 + .01)]], np.int32)
        cv2.fillPoly(ov, [p], 255)
    al = (cv2.bitwise_and(ov, m).astype(np.float32) / 255 * k)[..., None]; f[:] = f * (1 - al) + np.array(col, np.float32) * al
INK_BLOBS = [(r.uniform(0, 6.28), r.uniform(.75, 1.45), r.uniform(.06, .2)) for r in [np.random.default_rng(3)] for _ in range(26)]
def ink(f, cx, cy, R0, p, col=RED):
    """ink splash that grows with p in [0,1]"""
    if p <= 0: return
    R1 = R0 * eo(p); ov = f.copy(); cv2.circle(ov, (int(cx), int(cy)), int(R1), col, -1, cv2.LINE_AA)
    for (a, d, s) in INK_BLOBS:
        dd = d * R1; cv2.circle(ov, (int(cx + dd * math.cos(a)), int(cy + dd * math.sin(a))), int(s * R1), col, -1, cv2.LINE_AA)
    f[:] = f * .06 + ov * .94 if False else ov
def flash(f, t, t0, d=.08):
    if t0 <= t < t0 + d: f[:] = f + (255 - f) * (1 - (t - t0) / d) * .7
def shake(t, t0, amp=16, d=.3):
    if t < t0 or t > t0 + d: return 0, 0
    k = (1 - (t - t0) / d) ** 2; return amp * k * math.sin((t - t0) * 90), amp * k * math.cos((t - t0) * 77)

# ---------- scenes
def s_hook(t, f):  # 0–3.05: one still manga panel, silhouettes, calm
    b1 = (60, 260, 1020, 1240); fill_panel(f, b1, (214, 220, 226)); speed(f, b1, 540, 760, t, 70, (70, 70, 70), .55)
    blit(f, EB_SIL, 330, 790, 1, 1, -4); blit(f, OP_SIL, 760, 820, .78, 1, 4); panel(f, b1)
    b2 = (60, 1290, 1020, 1680); panel(f, b2)
    blit(f, T_OTW, 540, 1400); blit(f, T_HOOK, 540, 1570)
def s_eb(t, f):  # EB-05 ink reveal (cut on «EB»)
    dt = t - T['eb']; b1 = (60, 120, 1020, 1220); speed(f, b1, 540, 680, t, 120)
    ink(f, 540, 680, 380, dt / .35); dx, dy = shake(t, T['eb'])
    blit(f, EBBOX, 540 + dx, 690 + dy, 1.0 + .35 * (1 - ebk(dt / .3)), cl(dt / .08), -3); panel(f, b1)
    b2 = (60, 1270, 1020, 1690); fill_panel(f, b2, BLACK); panel(f, b2)
    blit(f, T_EB, 540, 1400, 1.0 + .3 * (1 - ebk(dt / .25))); blit(f, T_HER, 540, 1570, 1, cl((dt - 1.3) / .2))
    blit(f, SFX_DON, 830, 300, 1.0 + .4 * (1 - ebk(dt / .2)), cl(dt / .06), -12)
    flash(f, t, T['eb'])
def s_eb2(t, f):  # heroines: official art panel slides in (cut on «بطلات»)
    dt = t - T['eb2']; b1 = (60, 150, 1020, 1110); k1 = ebk(dt / .35)
    fill_panel(f, b1, (225, 205, 250)); blit(f, KV, 540 + 500 * (1 - k1), 630 + 12 * math.sin(t * 2), .98 + .03 * eio(dt / 2.4)); panel(f, b1)
    cv2.rectangle(f, (0, 0), (W, 148), PAPER, -1); cv2.rectangle(f, (0, 0), (58, H), PAPER, -1); cv2.rectangle(f, (1022, 0), (W, H), PAPER, -1); cv2.rectangle(f, (0, 1112), (W, 1180), PAPER, -1)
    blit(f, T_BTL, 540, 1290, 1, cl((dt - .1) / .2)); blit(f, EBPACK, 300, 1560, .55, 1, -8 + 3 * math.sin(t * 2)); blit(f, EBBOX, 720, 1580, .6, 1, 4)
def s_op(t, f):  # OP-18 (cut on «OP»): black panel, white speed lines, red ink
    dt = t - T['op']; b1 = (60, 160, 1020, 1240); fill_panel(f, b1, BLACK); speed(f, b1, 540, 720, t, 120, (240, 240, 240), .9)
    ink(f, 540, 720, 420, (dt - .1) / .35); dx, dy = shake(t, T['op'])
    blit(f, OPBOX, 540 + dx, 760 + dy, 1.0 + .3 * (1 - ebk(dt / .3)), cl(dt / .08)); panel(f, b1)
    blit(f, T_OP, 540, 1390, 1.0 + .3 * (1 - ebk(dt / .25))); blit(f, T_DOG, 540, 1560, 1, cl((dt - .9) / .2))
    blit(f, SFX_BAM, 250, 300, 1.0 + .4 * (1 - ebk(dt / .2)), cl(dt / .06), 10); flash(f, t, T['op'])
def split_page(f, t, dt, pulse=0.0):
    p1 = np.array([[60, 160], [1020, 160], [1020, 820], [60, 1020]], np.int32); p2 = np.array([[60, 1060], [1020, 860], [1020, 1560], [60, 1560]], np.int32)
    cv2.fillPoly(f, [p1], (240, 236, 250)); cv2.fillPoly(f, [p2], (60, 52, 50))
    blit(f, EBBOX, 330, 560, .78, 1, -4); blit(f, OPPACK, 760, 1250, .95, 1, 4)
    cv2.line(f, (60, 1040), (1020, 840), BLACK, 16, cv2.LINE_AA); cv2.polylines(f, [p1, p2], True, BLACK, 10, cv2.LINE_AA)
    for n, x, y, c in (('1', 880, 300, (40, 30, 215)), ('2', 200, 1430, (240, 240, 240))):
        r = 78 * (1 + pulse * abs(math.sin(t * 7 + (0 if n == '1' else 1.5)))); cv2.circle(f, (x, y), int(r), c, -1, cv2.LINE_AA); cv2.circle(f, (x, y), int(r), BLACK, 8, cv2.LINE_AA)
        blit(f, text_sprite_cache(n, (255, 255, 255) if n == '1' else (18, 16, 20)), x, y)
_TS = {}
def text_sprite_cache(s, col):
    k = (s, col)
    if k not in _TS: _TS[k] = text_sprite(s, FB(110), fill=col, pad=20)
    return _TS[k]
def s_vs(t, f):  # «أي واحد تبغاه أول؟» (cut on the question)
    dt = t - T['vs']; split_page(f, t, dt); blit(f, T_Q, 540, 1680, 1.0 + .2 * (1 - ebk(dt / .25)))
def s_vs2(t, f):  # «اكتب 1 ولا 2» — numbers pulse on the drum
    dt = t - T['vs2']; split_page(f, t, dt, .12); blit(f, T_CM, 540, 1680, 1.0 + .2 * (1 - ebk(dt / .25)))
def s_wait(t, f):  # «وإلين يوصلون…» empty panel, clock-like speed lines (part of vs2 → dr bridge)
    pass
def s_dr(t, f):  # purple ink floods the page, Delta Reign rises (cut on «بوكس»)
    dt = t - T['dr']; b1 = (60, 160, 1020, 1320); fill_panel(f, b1, (240, 236, 232))
    ink(f, 540, 740, 560, dt / .45, (150, 40, 110)); speed(f, b1, 540, 740, t, 90, (255, 220, 240), .5 * cl(dt / .4))
    blit(f, DRBOX, 540, 760 + 200 * (1 - ebk((dt - .1) / .4)), 1.15, cl((dt - .1) / .1)); panel(f, b1)
    blit(f, T_DR, 540, 1190, 1, cl((dt - 1.6) / .2)); blit(f, T_WAIT, 540, 1480, .8, 1)
def s_site(t, f):  # site panel (cut on «اطلب»)
    dt = t - T['site']; b1 = (60, 200, 1020, 900); fill_panel(f, b1, (250, 248, 244)); speed(f, b1, 540, 550, t, 80, (205, 205, 210), .7)
    blit(f, LOGO, 540, 520, 1.0 + .15 * (1 - ebk(dt / .3))); panel(f, b1)
    b2 = (60, 940, 1020, 1500); panel(f, b2); blit(f, T_SITE, 540, 1100, 1.0 + .2 * (1 - ebk(dt / .3)))
    if t > T['ship']: blit(f, T_SHIP, 540, 1300, 1, cl((t - T['ship']) / .2))
    blit(f, DRBOX, 860, 1560, .45, 1, 8 * math.sin(t * 2))
def s_show(t, f):  # showroom: street-map panel + pin (cut on «زورنا»)
    dt = t - T['show']; b1 = (60, 200, 1020, 1300); fill_panel(f, b1, (236, 232, 228))
    sh = (dt * 50) % 110
    for i in range(10): yl = int(220 + i * 110 + sh); cv2.line(f, (60, yl), (1020, yl + 50), (150, 145, 150), 5, cv2.LINE_AA)
    for i in range(7): xl = int(80 + i * 150 + sh); cv2.line(f, (xl, 200), (xl + 60, 1300), (150, 145, 150), 5, cv2.LINE_AA)
    k = ebk(dt / .35); cv2.circle(f, (540, int(700 - 160 * (1 - k))), 90, (40, 30, 215), -1, cv2.LINE_AA); cv2.circle(f, (540, int(700 - 160 * (1 - k))), 34, (232, 240, 246), -1, cv2.LINE_AA)
    tri = np.array([[470, int(740 - 160 * (1 - k))], [610, int(740 - 160 * (1 - k))], [540, int(880 - 160 * (1 - k))]], np.int32); cv2.fillPoly(f, [tri], (40, 30, 215)); panel(f, b1)
    blit(f, text_sprite_cache2('وفي معرضنا'), 540, 1460, 1, cl(dt / .15))
def text_sprite_cache2(s):
    if s not in _TS: _TS[s] = text_sprite(s, FL(120), fill=INKC)
    return _TS[s]
def s_olaya(t, f):  # full red ink page with the name (cut on «العليا»)
    dt = t - T['olaya2']; f[:] = np.array((40, 30, 205), np.float32) + GRAIN * 2; speed(f, (0, 0, W, H), 540, 900, t, 120, (70, 60, 235), .9)
    blit(f, T_OLAYA, 540, 880, 1.0 + .25 * (1 - ebk(dt / .3))); blit(f, T_ABHUR, 540, 1080, 1, cl((dt - .15) / .2))
def s_share(t, f):  # share trigger: official art + text
    dt = t - T['share']; b1 = (60, 160, 1020, 1000); fill_panel(f, b1, (230, 222, 250))
    blit(f, KV, 540, 600, .92 + .03 * math.sin(t * 2)); panel(f, b1)
    cv2.rectangle(f, (0, 0), (W, 158), PAPER, -1); cv2.rectangle(f, (0, 1002), (W, 1070), PAPER, -1)
    blit(f, T_SHARE, 540, 1180, 1.0 + .25 * (1 - ebk(dt / .25))); blit(f, T_SHARE2, 540, 1360, 1, cl((dt - .9) / .2))
def s_follow(t, f):  # TO BE CONTINUED + follow (cut on «وتابعنا»)
    dt = t - T['follow']; f[:] = np.array((22, 18, 24), np.float32) + GRAIN * 3; speed(f, (0, 0, W, H), 540, 760, t, 100, (90, 80, 95), .8)
    blit(f, LOGO, 540, 620, 1.0 + .12 * (1 - ebk(dt / .3)), 1, 2 * math.sin(t * 4)); blit(f, T_TBC, 540, 1010, 1, 1)
    arrow = np.array([[300, 1150], [700, 1150], [700, 1110], [800, 1185], [700, 1260], [700, 1220], [300, 1220]], np.int32); cv2.fillPoly(f, [arrow + [int(12 * math.sin(t * 8)), 0]], (40, 30, 215))
    blit(f, P_FOLLOW, 540, 1400, 1.25 + .1 * abs(math.sin(t * 7)))
def s_end(t, f):  # comment / like / save, loops to the hook panel look
    dt = t - T['end']; s_hook(t, f) if False else None
    b1 = (60, 260, 1020, 1060); fill_panel(f, b1, (214, 220, 226)); speed(f, b1, 540, 660, t, 90, (70, 70, 70), .6)
    blit(f, EBBOX, 330, 660, .75, 1, -4 + 3 * math.sin(t * 3)); blit(f, OPPACK, 760, 680, .8, 1, 4 - 3 * math.sin(t * 3)); panel(f, b1)
    blit(f, T_CMT, 540, 1240, 1.0 + .2 * (1 - ebk(dt / .25))); blit(f, T_LIKE, 540, 1420, 1.0 + .08 * abs(math.sin(t * 7)), cl((dt - .9) / .2))

def s_op2(t, f):  # same OP-18 panel + launch date stamp
    s_op(t, f); dt = t - T['date']
    blit(f, T_DATE, 540, 1730, 1.0 + .3 * (1 - ebk(dt / .25)), cl(dt / .08), -4)
def s_tease(t, f):  # «وأقوى هت بالسيت؟» — card silhouette, question
    dt = t - T['tease']; b1 = (60, 180, 1020, 1320); fill_panel(f, b1, (214, 220, 226)); speed(f, b1, 540, 740, t, 110, (60, 60, 60), .7)
    blit(f, GUNKO_SIL, 540, 750, 1.0 + .04 * math.sin(t * 6), 1, 3 * math.sin(t * 4)); panel(f, b1)
    blit(f, T_TOP, 540, 1500, 1.0 + .25 * (1 - ebk(dt / .25)))
def s_hit(t, f):  # reveal on «غونكو»: red ink + the card, foil sweep, shake
    dt = t - T['hit']; f[:] = np.array((22, 18, 24), np.float32) + GRAIN * 3; speed(f, (0, 0, W, H), 540, 820, t, 120, (60, 50, 215), .8)
    ink(f, 540, 820, 520, dt / .3, (40, 30, 200)); dx, dy = shake(t, T['hit'], 20, .35)
    blit(f, GUNKO, 540 + dx, 820 + dy, 1.0 + .45 * (1 - ebk(dt / .35)) + .02 * eio(dt / 2), cl(dt / .06), 3 - 4 * eio(dt / 2.5))
    sx = -400 + ((dt * 1000) % 1900); band = np.zeros((H, W), np.float32)
    cv2.fillPoly(band, [np.array([[int(sx + 320), 330], [int(sx + 440), 330], [int(sx + 140), 1320], [int(sx), 1320]])], 1.0)
    band = cv2.GaussianBlur(band, (0, 0), 22)[..., None]; m = np.zeros((H, W), np.float32); cv2.rectangle(m, (230, 370), (850, 1270), 1.0, -1)
    f[:] = f + band * m[..., None] * np.array([150, 230, 255], np.float32) * .55
    blit(f, T_GUN, 540, 1440, 1.0 + .3 * (1 - ebk((dt - .3) / .25)), cl((dt - .3) / .08)); blit(f, P_SP, 540, 1600, 1, cl((dt - .9) / .2))
    flash(f, t, T['hit'])
def s_site2(t, f):  # «راح يكون متوفر أونلاين على موقعنا»
    dt = t - T['site']; b1 = (60, 200, 1020, 900); fill_panel(f, b1, (250, 248, 244)); speed(f, b1, 540, 550, t, 80, (205, 205, 210), .7)
    blit(f, LOGO, 540, 520, 1.0 + .15 * (1 - ebk(dt / .3))); panel(f, b1)
    b2 = (60, 940, 1020, 1560); panel(f, b2); blit(f, T_ONLINE, 540, 1110, 1.0 + .2 * (1 - ebk(dt / .3))); blit(f, T_SITE, 540, 1330, 1, cl((dt - .8) / .2))
    blit(f, OPPACK, 860, 1660, .45, 1, 8 * math.sin(t * 2))
def s_wait(t, f):  # «وش تنتظر؟ ون بيس ما يجلس!» — urgency, red page, boxes fly
    dt = t - T['wait']; f[:] = np.array((40, 30, 205), np.float32) + GRAIN * 2; speed(f, (0, 0, W, H), 540, 760, t, 120, (70, 55, 230), .9)
    blit(f, OPBOX, 540, 640 + 18 * math.sin(t * 6), .85, 1, 3 * math.sin(t * 4)); dx, dy = shake(t, T['wait'], 12, .25)
    blit(f, T_WAIT1, 540 + dx, 1180 + dy, 1.0 + .3 * (1 - ebk(dt / .25))); blit(f, T_WAIT2, 540, 1400, 1.0 + .25 * (1 - ebk((dt - 1.0) / .25)), cl((dt - 1.0) / .08))
def s_end2(t, f):  # comment / like / save + follow pill (loop look of the hook)
    s_end(t, f); blit(f, P_FOLLOW, 540, 1620, 1.1 + .1 * abs(math.sin(t * 7)))

SC = [('s1', s_hook), ('eb', s_eb), ('eb2', s_eb2), ('op', s_op), ('date', s_op2), ('tease', s_tease), ('hit', s_hit), ('vs', s_vs), ('vs2', s_vs2), ('site', s_site2), ('show', s_show), ('olaya2', s_olaya), ('wait', s_wait), ('share', s_share), ('end', s_end2)]
def render(t):
    f = paper(t); cur, st = SC[0][1], 0
    for k, fn in SC:
        if t >= T[k]: cur, st = fn, T[k]
    cur(t, f)
    z = 1 + (.02 * t if cur is s_hook else .04 * (t - st)); px = 0 if cur is s_hook else 8 * math.sin(t * .9)
    M = np.float32([[z, 0, (1 - z) * 540 + px], [0, z, (1 - z) * 960]]); f = cv2.warpAffine(f, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return np.clip(f, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'frames':
        for t in [float(x) for x in sys.argv[2].split(',')]: cv2.imwrite(f'/home/claude/work/o_{t:.1f}.jpg', render(t))
        sys.exit()
    n = int(round(TOTAL * FPS))
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    for i in range(n): p.stdin.write(render(i / FPS).tobytes())
    p.stdin.close(); p.wait(); print('ok', OUT, n)
