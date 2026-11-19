# rot8 — Digimon AD-01 vs Yu-Gi-Oh! Magnificent Monsters + Delta Reign bonus — «اختار لاعبك» (retro arcade / synthwave)
# ONE timeline, whole-video render (render(t) deterministic)
import os, sys, math
os.environ.setdefault('CUES', 'yd_cues.json')
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dr_render.py'), encoding='utf-8').read()
exec(_src.split('# ---------- background')[0])  # shared helpers
OUT = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != 'frames' else '/home/claude/work/yd_v.mp4'
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
# synthwave sky (BGR): deep violet top -> magenta -> orange horizon at y=1180
HZ = 1180
sky = np.zeros((H, W, 3), np.float32)
k = np.clip(yy / HZ, 0, 1)[..., None]
top = np.array([70, 10, 40], np.float32); mid = np.array([140, 30, 200], np.float32); low = np.array([60, 120, 255], np.float32)
sky = np.where(k < .6, top + (mid - top) * (k / .6), mid + (low - mid) * ((k - .6) / .4))
sky[HZ:] = np.array([60, 8, 30], np.float32)
sky2 = np.zeros((H, W, 3), np.float32); k2 = np.clip(yy / H, 0, 1)[..., None]
sky2 = np.array([120, 60, 10], np.float32) * (1 - k2) + np.array([200, 200, 40], np.float32) * k2  # teal close-up stage
ALT = set()
SUN_C = (540, 1020); SUN_R = 330
def background(t, still=False, alt=False):
    if alt:
        f = sky2.copy(); f[::4] *= .86
        f += np.exp(-(((xx - 540) ** 2 + (yy - 900) ** 2) / (520 ** 2)))[..., None] * np.array([90, 90, 60], np.float32) * (0.8 + 0.2 * math.sin(t * 6))
        return f
    f = sky.copy()
    m = ((xx - SUN_C[0]) ** 2 + (yy - SUN_C[1]) ** 2 < SUN_R ** 2) & (yy < HZ)
    stripes = ((yy - 760) % 46 < (6 + (yy - 760) / 40)) & (yy > 900)
    sun = np.zeros((H, W, 3), np.float32); sun[:] = (90, 200, 255)
    f = np.where((m & ~stripes)[..., None], sun * (0.75 + 0.25 * (1 - (yy - 690) / 500)[..., None]), f)
    tt_ = 0 if still else t
    for i in range(1, 22):  # floor grid (perspective), scrolls toward viewer
        z = (i - (tt_ * 1.6) % 1) / 21; y = int(HZ + (H - HZ) * z ** 2)
        if HZ < y < H: cv2.line(f, (0, y), (W, y), (255, 80, 230), 3, cv2.LINE_AA)
    for i in range(-12, 13):
        cv2.line(f, (540 + i * 40, HZ), (540 + i * 260, H), (255, 80, 230), 3, cv2.LINE_AA)
    f[::4] *= .86  # CRT scanlines
    return f

def ld(p): return Image.open(F + p).convert('RGBA')
DGBOX = img_sprite(ld('ad01_gn1.png'), 470, (80, 200, 255), 40); DGPACK = img_sprite(ld('ad01_gn2.png'), 300, (80, 200, 255), 30)
YGBOX = img_sprite(ld('ygo_mamo_box.png'), 520, (255, 190, 90), 40)
DRBOX = img_sprite(cutout(F + 'dr_box_b.jpg'), 470, (190, 120, 255), 40)
LOGO = img_sprite(Image.open(R + 'tools_challenges/htr_logo.png').convert('RGBA'), 620, (40, 230, 255), 30)
def pix(s, size, fill, stroke=(20, 10, 40), scale=6):
    f = FB(max(8, size // scale)); d0 = ImageDraw.Draw(Image.new('L', (4, 4))); bb = d0.textbbox((0, 0), s, font=f, stroke_width=1)
    sm = Image.new('RGBA', (bb[2] - bb[0] + 6, bb[3] - bb[1] + 6), (0, 0, 0, 0))
    ImageDraw.Draw(sm).text((3 - bb[0], 3 - bb[1]), s, font=f, fill=fill, stroke_width=1, stroke_fill=stroke)
    a = np.array(sm); a[..., 3] = np.where(a[..., 3] > 110, 255, 0); sm = Image.fromarray(a)
    big = sm.resize((sm.width * scale, sm.height * scale), Image.NEAREST)
    out = Image.new('RGBA', (big.width + 24, big.height + 24), (0, 0, 0, 0)); sh = Image.new('RGBA', big.size, (0, 0, 0, 0)); sh.putalpha(big.split()[3].point(lambda v: v * .6))
    out.alpha_composite(sh, (16, 16)); out.alpha_composite(big, (4, 4)); return to_bgra(out)
CY = (90, 240, 255); MG = (255, 80, 220); YL = (255, 255, 255); OR = (255, 150, 60)
P_SELECT = pix('SELECT YOUR', 90, CY); P_PLAYER = pix('PLAYER', 140, MG)
P_1P = pix('1P', 70, CY); P_2P = pix('2P', 70, MG)
P_DIG = pix('DIGIMON', 70, YL); P_AD = pix('GENERATION AD-01', 58, CY)
P_YGO = pix('YU-GI-OH!', 70, YL); P_MAMO = pix('MAGNIFICENT MONSTERS', 50, MG)
P_ROUND = pix('ROUND 1', 150, YL); P_VS = pix('VS', 200, OR); P_FIGHT = pix('FIGHT!', 130, OR)
P_BONUS = pix('BONUS STAGE', 100, CY); P_SCORE = pix('SCORE', 60, YL)
P_SITE = pix('HTRTCG.COM', 64, CY); P_FOLLOW = pix('PRESS FOLLOW', 70, YL); P_CONT = pix('CONTINUE?', 100, MG)
def ar(s, size, fill=(255, 255, 255), stroke=7): return text_sprite(s, FL(size), fill=fill, stroke=stroke, stroke_fill=(30, 8, 60))
T_PICK = ar('اختار لاعبك', 130); T_WHO = ar('مين يكسب؟', 140); T_C12 = ar('علّق 1 ولا 2', 120, (255, 230, 120))
T_DR = ar('بوكس دلتا رين كامل', 100); T_850 = ar('850 ريال بس', 120, (120, 255, 235)); T_RB = ar('ريال بس!', 130, (255, 255, 255))
T_ON = ar('كلهم متوفرين أونلاين', 110); T_SHOW = ar('وفي معرضنا', 130)
T_OLAYA = ar('العليا سكوير', 180, (255, 255, 255), 9); T_ABHUR = ar('أبحر الجنوبية – جدة', 84, (255, 225, 245))
T_SHARE = ar('أرسله لخويك', 140); T_SHARE2 = ar('اللي يلعب يوغي أوو أو ديجيمون', 74, (255, 230, 120))
T_CMT = ar('علّق ولو بنقطة', 120); T_LIKE = ar('لايك وسيف', 120, (120, 255, 235)); P_TF = pill('تابع HTR', FL(84), (200, 30, 160))
_num = {}
def num(n):
    if n not in _num: _num[n] = pix(str(n), 110, YL)
    return _num[n]
def hpbar(f, x0, x1, y, col, p=1.0):
    cv2.rectangle(f, (x0, y), (x1, y + 46), (30, 10, 40), -1); cv2.rectangle(f, (x0, y), (x1, y + 46), (255, 255, 255), 4)
    cv2.rectangle(f, (x0 + 6, y + 6), (x0 + 6 + int((x1 - x0 - 12) * p), y + 40), col, -1)
def flash(f, t, t0, d=.08):
    if t0 <= t < t0 + d: f[:] = f + (255 - f) * (1 - (t - t0) / d) * .7
def shake(t, t0, amp=16, d=.3):
    if t < t0 or t > t0 + d: return 0, 0
    k = (1 - (t - t0) / d) ** 2; return amp * k * math.sin((t - t0) * 90), amp * k * math.cos((t - t0) * 77)
def slot(f, box, col, sel, t):
    cv2.rectangle(f, box[:2], box[2:], (40, 10, 50), -1); w = 10 if sel and int(t * 3) % 2 == 0 else 4
    cv2.rectangle(f, box[:2], box[2:], col[::-1], w)

def s_select(t, f):  # 0–3.05 calm: select screen, cursor blinks on 1P
    blit(f, P_SELECT, 540, 240); blit(f, P_PLAYER, 540, 380)
    slot(f, (70, 520, 520, 1180), CY, True, t); slot(f, (560, 520, 1010, 1180), MG, False, t)
    blit(f, DGBOX, 295, 850, .82); blit(f, YGBOX, 785, 850, .78)
    blit(f, P_1P, 295, 1250); blit(f, P_2P, 785, 1250); blit(f, T_PICK, 540, 1460)
def s_p1(t, f):  # P1 Digimon (cut on «ديجيمون»)
    dt = t - T['p1']; dx, dy = shake(t, T['p1'])
    hpbar(f, 60, 1020, 200, (255, 220, 90), eo(dt / .8)); blit(f, P_DIG, 540, 330)
    blit(f, DGBOX, 540 - 700 * (1 - ebk(dt / .35)) + dx, 860 + dy, 1.35 + .04 * math.sin(t * 3)); blit(f, DGPACK, 860, 1140, 1, cl((dt - .5) / .2), 10)
    blit(f, P_AD, 540, 1480, 1, cl((dt - 1.0) / .1)); flash(f, t, T['p1'])
def s_p2(t, f):  # P2 Yu-Gi-Oh (cut on «ضد»), enters from the right
    dt = t - T['p2']; dx, dy = shake(t, T['p2'])
    hpbar(f, 60, 1020, 200, (220, 80, 255), eo(dt / .8)); blit(f, P_YGO, 540, 330)
    blit(f, YGBOX, 540 + 700 * (1 - ebk(dt / .35)) + dx, 860 + dy, 1.3 + .04 * math.sin(t * 3))
    blit(f, P_MAMO, 540, 1480, 1, cl((dt - 1.0) / .1)); flash(f, t, T['p2'])
def faceoff(f, t, dt):
    hpbar(f, 60, 500, 200, (255, 220, 90)); hpbar(f, 580, 1020, 200, (220, 80, 255))
    blit(f, P_1P, 160, 300); blit(f, P_2P, 920, 300)
    blit(f, DGBOX, 290 + 10 * math.sin(t * 5), 800, .92, 1, -4); blit(f, YGBOX, 800 - 10 * math.sin(t * 5), 800, .9, 1, 4)
def s_round(t, f):  # ROUND 1 (cut on «مين يكسب»)
    dt = t - T['round']; faceoff(f, t, dt)
    blit(f, P_ROUND, 540, 560, 1.0 + .4 * (1 - ebk(dt / .25)), cl(dt / .06)); blit(f, P_VS, 540, 830, 1.0 + .1 * abs(math.sin(t * 8)))
    blit(f, T_WHO, 540, 1300); flash(f, t, T['round'])
def s_round2(t, f):  # «علّق 1 ولا 2» — numbers pulse
    dt = t - T['round2']; faceoff(f, t, dt)
    blit(f, num(1), 290, 1180, 1.0 + .15 * abs(math.sin(t * 7))); blit(f, num(2), 800, 1180, 1.0 + .15 * abs(math.sin(t * 7 + 1.5)))
    blit(f, P_FIGHT, 540, 560, 1, 1); blit(f, T_C12, 540, 1440, 1.0 + .2 * (1 - ebk(dt / .25)))
def s_bonus(t, f):  # BONUS STAGE: Delta Reign drops in, score counts to 850
    dt = t - T['bonus']; dx, dy = shake(t, T['bonus'] + .35, 14, .25)
    blit(f, P_BONUS, 540, 260, 1.0 + .3 * (1 - ebk(dt / .25)))
    blit(f, DRBOX, 540 + dx, 820 - 700 * (1 - ebk((dt - .1) / .35)) + dy, 1.2 + .03 * math.sin(t * 3))
    sc = int(850 * eo((dt - .4) / 1.4)) if dt > .4 else 0; blit(f, P_SCORE, 300, 1290); blit(f, num(sc), 700, 1290)
    blit(f, T_DR, 540, 1450, 1, cl((dt - .2) / .2)); blit(f, T_850, 540, 1580, 1.0 + .2 * (1 - ebk((dt - 1.8) / .25)), cl((dt - 1.8) / .1))
def s_site(t, f):  # «كلهم متوفرين أونلاين على موقعنا» — all three in a row
    dt = t - T['site']; blit(f, LOGO, 540, 300, 1.0 + .15 * (1 - ebk(dt / .3)))
    for i, (spr, x, s) in enumerate(((DGBOX, 220, .6), (YGBOX, 540, .6), (DRBOX, 860, .6))):
        blit(f, spr, x, 760 - 300 * (1 - ebk((dt - .1 * i) / .3)) + 8 * math.sin(t * 3 + i), s, cl((dt - .1 * i) / .1))
    blit(f, T_ON, 540, 1140, 1, cl((dt - .2) / .2)); blit(f, P_SITE, 540, 1300, 1, cl((dt - 1.2) / .1))
def s_show(t, f):  # «وفي معرضنا» — pixel map + pin
    dt = t - T['show']
    for i in range(9):
        yl = int(470 + i * 95 + (dt * 40) % 95); cv2.line(f, (120, yl), (960, yl + 40), (255, 160, 240), 4)
    for i in range(7):
        xl = int(140 + i * 140 + (dt * 40) % 140); cv2.line(f, (xl, 450), (xl + 50, 1300), (255, 160, 240), 4)
    k = ebk(dt / .35); py = int(800 - 160 * (1 - k)); cv2.circle(f, (540, py), 95, (90, 240, 255)[::-1], -1, cv2.LINE_AA); cv2.circle(f, (540, py), 36, (40, 10, 50), -1, cv2.LINE_AA)
    cv2.fillPoly(f, [np.array([[465, py + 45], [615, py + 45], [540, py + 190]], np.int32)], (255, 240, 90)); blit(f, T_SHOW, 540, 1440, 1, cl(dt / .15))
def s_olaya(t, f):  # cut on «العليا»: neon name card
    dt = t - T['olaya2']; f[:] = f * .35 + np.array([120, 20, 110], np.float32) * .65
    blit(f, P_CONT, 540, 520, 1, 1) if False else None
    blit(f, T_OLAYA, 540, 880, 1.0 + .25 * (1 - ebk(dt / .3))); blit(f, T_ABHUR, 540, 1090, 1, cl((dt - .15) / .2))
    cv2.rectangle(f, (90, 640), (990, 1200), (255, 240, 90), 6)
def s_share(t, f):  # share trigger
    dt = t - T['share']; blit(f, DGBOX, 300, 700, .7, 1, -6 + 3 * math.sin(t * 3)); blit(f, YGBOX, 780, 700, .68, 1, 6 - 3 * math.sin(t * 3))
    blit(f, T_SHARE, 540, 1180, 1.0 + .25 * (1 - ebk(dt / .25))); blit(f, T_SHARE2, 540, 1360, 1, cl((dt - .8) / .2))
def s_end(t, f):  # comment / like / save + PRESS FOLLOW (arcade continue screen)
    dt = t - T['end']; blit(f, P_CONT, 540, 300); blit(f, LOGO, 540, 600, .9 + .04 * math.sin(t * 6))
    blit(f, T_CMT, 540, 950, 1.0 + .2 * (1 - ebk(dt / .25))); blit(f, T_LIKE, 540, 1110, 1.0 + .08 * abs(math.sin(t * 7)), cl((dt - .9) / .2))
    if int(t * 3) % 2 == 0: blit(f, P_FOLLOW, 540, 1300)
    blit(f, P_TF, 540, 1460, 1.1 + .08 * abs(math.sin(t * 7)))

def s_follow(t, f):  # cut on «وتابعنا»: big PRESS FOLLOW + logo
    dt = t - T['follow']
    blit(f, LOGO, 540, 640, 1.0 + .15 * (1 - ebk(dt / .3)) + .03 * math.sin(t * 6))
    blit(f, P_FOLLOW, 540, 980, 1.2 if int(t * 3) % 2 == 0 else 1.1); blit(f, P_TF, 540, 1180, 1.3 + .1 * abs(math.sin(t * 7)))

def s_p1b(t, f):  # close-up on «Digimon Generation»: the English pack
    dt = t - T['p1b']; blit(f, DGPACK, 540, 860, 2.2 + .05 * eio(dt / 2), 1, -4 + 2 * math.sin(t * 3)); blit(f, P_AD, 540, 1560, 1.2)
def s_p2b(t, f):  # close-up on «Magnificent Monsters»
    dt = t - T['p2b']; blit(f, YGBOX, 540, 860, 1.75 + .05 * eio(dt / 2), 1, 3 - 2 * math.sin(t * 3)); blit(f, P_MAMO, 540, 1560, 1.25)
def s_b850(t, f):  # cut on the price: big 850
    dt = t - T['b850']; blit(f, DRBOX, 540, 700, .9, 1, 4); blit(f, num(850), 540, 1220, 1.6 + .3 * (1 - ebk(dt / .25))); blit(f, T_RB, 540, 1450, 1.0)
ALTS = ('s_p1', 's_p2', 's_round2', 's_b850', 's_share', 's_follow')

SC = [('s1', s_select), ('p1', s_p1), ('p1b', s_p1b), ('p2', s_p2), ('p2b', s_p2b), ('round', s_round), ('round2', s_round2), ('bonus', s_bonus), ('b850', s_b850), ('site', s_site), ('show', s_show), ('olaya2', s_olaya), ('share', s_share), ('end', s_end), ('follow', s_follow)]
def render(t):
    cur, st = SC[0][1], 0
    for k, fn in SC:
        if t >= T[k]: cur, st = fn, T[k]
    f = background(t, still=cur is s_select and t < 1.0, alt=cur.__name__ in ALTS); cur(t, f)
    z = 1 + (.02 * t if cur is s_select else .04 * (t - st)); px = 0 if cur is s_select else 8 * math.sin(t * .9)
    M = np.float32([[z, 0, (1 - z) * 540 + px], [0, z, (1 - z) * 960]]); f = cv2.warpAffine(f, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return np.clip(f, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'frames':
        for t in [float(x) for x in sys.argv[2].split(',')]: cv2.imwrite(f'/home/claude/work/y_{t:.1f}.jpg', render(t))
        sys.exit()
    n = int(round(TOTAL * FPS))
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    for i in range(n): p.stdin.write(render(i / FPS).tobytes())
    p.stdin.close(); p.wait(); print('ok', OUT, n)
