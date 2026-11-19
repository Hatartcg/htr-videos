# rot10 — HTR store + website tour «تعال نلف في موقع هتر» — real site screens in a 3D phone, then real tournament footage
# ONE timeline, whole-video render (render(t) deterministic). Voice: Hadi HTR eleven_v4 + approved bank clips.
import os, sys, math
os.environ['CUES'] = 'st_cues.json'
_src = open('/home/claude/htr-videos/tools_ads/rot8/dr_render.py', encoding='utf-8').read()
exec(_src.split('# ---------- background')[0])
_y2 = open('/home/claude/htr-videos/tools_ads/rot9/yd2_render.py', encoding='utf-8').read()
exec(_y2[_y2.index('# ---------- premium type'):_y2.index('T_PICK')])  # metal(), gradients
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
exec(_y2[_y2.index('def embers'):_y2.index('# ---------- product sprites')])  # embers, sweep, glowflash, shake
OUT = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != 'frames' else '/home/claude/work/st_v.mp4'
S = R + 'tools_ads/rot10/site/'; V = R
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

# ---------- background: blurred showroom plate + drifting aurora (brand purple / teal)
def _bg(fn, k=.42): return cv2.resize(cv2.GaussianBlur(cv2.imread(R + 'tools_ads/rot9/plates/' + fn), (0, 0), 18), (W, int(W * 2752 / 1536))).astype(np.float32)[:H] * k
BGS = dict(shw=_bg('p5_showroom.jpg'), arc=_bg('p1_arcade.jpg', .5), dig=_bg('p2_digimon.jpg', .5), ygo=_bg('p3_ygo.jpg', .5))
BGSEQ = [(0, 'shw'), (3.25, 'arc'), (6.5, 'dig'), (8.6, 'arc'), (10.6, 'shw'), (12.4, 'ygo'), (15.85, 'arc'), (17.95, 'dig'), (19.65, 'shw'), (21.45, 'arc')]
def aurora(t):
    f = BGS[[k for t0, k in BGSEQ if t >= t0][-1]].copy()
    for cx, cy, r, col, sp in ((300, 500, 520, (255, 70, 150), .23), (800, 1300, 600, (200, 200, 40), .17), (600, 900, 420, (255, 120, 60), .31)):
        x = cx + 140 * math.sin(t * sp * 2 + cy); y = cy + 110 * math.cos(t * sp * 1.7 + cx)
        g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * r * r))[..., None]; f += g * np.array(col, np.float32) * .28
    return f

# ---------- phone mockup with real screenshots
def ld_screen(fn): return cv2.imread(S + fn)  # 750x1624 (2x of 375x812)
SCR = {k: ld_screen(v) for k, v in dict(home1='home_1.jpg', home2='home_2.jpg', deals='deals.jpg', games='games_0.jpg', grade='grading.jpg', sell='sell.jpg', member='member.jpg').items()}
PW, PH_ = 700, int(700 * 1624 / 750)  # screen size on canvas
BZ = 26  # bezel
def phone_frame():
    w, h = PW + 2 * BZ, PH_ + 2 * BZ; im = Image.new('RGBA', (w + 120, h + 120), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sh = Image.new('L', im.size, 0); ImageDraw.Draw(sh).rounded_rectangle((60, 80, 60 + w, 80 + h), 90, fill=190); sh = sh.filter(ImageFilter.GaussianBlur(30))
    shl = Image.new('RGBA', im.size, (0, 0, 0, 0)); shl.putalpha(sh); im = Image.alpha_composite(im, shl); d = ImageDraw.Draw(im)
    d.rounded_rectangle((60, 60, 60 + w, 60 + h), 90, fill=(18, 18, 24, 255), outline=(120, 120, 140, 255), width=4)
    d.rounded_rectangle((66, 66, 54 + w, 54 + h), 86, outline=(60, 60, 72, 255), width=3)
    d.rounded_rectangle((60 + w / 2 - 70, 60 + BZ + 14, 60 + w / 2 + 70, 60 + BZ + 50), 18, fill=(0, 0, 0, 255))  # dynamic island
    return np.array(im)[..., [2, 1, 0, 3]].astype(np.float32)
FRAME = phone_frame(); FX, FY = 60 + BZ, 60 + BZ
MASK = np.zeros((PH_, PW), np.uint8); cv2.rectangle(MASK, (0, 0), (PW, PH_), 255, -1)
MASK = np.array(Image.fromarray(np.zeros((PH_, PW), np.uint8)).convert('L')); _m = Image.new('L', (PW, PH_), 0); ImageDraw.Draw(_m).rounded_rectangle((0, 0, PW, PH_), 66, fill=255); MASK = np.array(_m).astype(np.float32)[..., None] / 255

def screen_img(key, scroll=0.0, key2=None, k=0.0, ripple=None):
    """screen content; key2/k = vertical swipe transition; scroll in px of source"""
    a = SCR[key]; img = cv2.resize(a, (PW, PH_), interpolation=cv2.INTER_AREA).astype(np.float32)
    if scroll: M = np.float32([[1, 0, 0], [0, 1, -scroll]]); img = cv2.warpAffine(img, M, (PW, PH_), borderMode=cv2.BORDER_REPLICATE)
    if key2 is not None and k > 0:
        b = cv2.resize(SCR[key2], (PW, PH_), interpolation=cv2.INTER_AREA).astype(np.float32); o = int(PH_ * eio(k))
        img = np.concatenate([img[o:], b[:o]], 0) if o > 0 else img
    if ripple:
        rx, ry, rt = ripple
        if 0 <= rt <= .6:
            r = 30 + 160 * eo(rt / .6); al = 1 - rt / .6
            ov = img.copy(); cv2.circle(ov, (int(rx), int(ry)), int(r), (255, 255, 255), -1, cv2.LINE_AA); img = img * (1 - .35 * al) + ov * (.35 * al)
            cv2.circle(img, (int(rx), int(ry)), int(26 * (1 - .3 * rt)), (255, 255, 255), 3, cv2.LINE_AA)
    return img

def phone(f, scr, cx, cy, s=1.0, tilt=0.0, roll=0.0, a=1.0):
    """composite phone (frame + screen) with a gentle 3D tilt (perspective), centred at cx,cy"""
    fh, fw = FRAME.shape[:2]; can = FRAME.copy()
    sc = np.dstack([scr, np.full(scr.shape[:2], 255, np.float32)]) * np.concatenate([np.ones((1, 1, 3)), np.ones((1, 1, 1))], 2)
    region = can[FY:FY + PH_, FX:FX + PW]; m = MASK
    region[..., :3] = region[..., :3] * (1 - m) + scr * m; region[..., 3:] = np.maximum(region[..., 3:], m * 255)
    # glass glare
    gl = np.clip(1 - np.abs((np.arange(PW)[None, :] + np.arange(PH_)[:, None] * .5) - (PW * .3 + 400 * math.sin(tilt * 3))) / 160, 0, 1)[..., None] * 22
    region[..., :3] += gl * m
    src = np.float32([[0, 0], [fw, 0], [fw, fh], [0, fh]])
    k = tilt; dx = fw * .07 * k; dy = fh * .035 * k
    dst = np.float32([[dx, -dy], [fw - dx, dy], [fw - dx, fh - dy], [dx, fh + dy]])
    Mp = cv2.getPerspectiveTransform(src, dst)
    R2 = cv2.getRotationMatrix2D((fw / 2, fh / 2), roll, s); R3 = np.vstack([R2, [0, 0, 1]]).astype(np.float32)
    Tm = np.float32([[1, 0, cx - fw / 2], [0, 1, cy - fh / 2], [0, 0, 1]])
    M = Tm @ R3 @ Mp
    out = cv2.warpPerspective(can, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    al = out[..., 3:] / 255 * a; f[:] = f * (1 - al) + out[..., :3] * al

# ---------- type
def ar(s, size, g=SILV, glow=(0, 0, 0), stroke=6): return metal(s, FL(size), g[0], g[1], stroke, (16, 8, 26), glow, 20)
def en(s, size, g=GOLD, glow=None): return metal(s, FA(size), g[0], g[1], 5, (24, 12, 6), glow, 24)
PURPG = ((240, 220, 255), (150, 90, 255)); TEALG = ((220, 255, 250), (40, 200, 190))
T1 = ar('تبي تعرف وش عندنا؟', 120, SILV, (150, 90, 255)); T1b = ar('تعال نلف في الموقع', 84, TEALG, (40, 200, 190))
C_DEAL = pill('عروض محدودة', FL(74), (200, 40, 70))
GAMES = [('POKÉMON', ((255, 245, 160), (230, 170, 20)), (230, 180, 20)), ('ONE PIECE', ((255, 220, 220), (220, 40, 50)), (230, 40, 60)), ('DIGIMON', ((220, 240, 255), (40, 130, 240)), (40, 140, 255))]
E_G = [en(n, 92, g, gl) for n, g, gl in GAMES]; T_MORE = ar('وأكثر!', 110, GOLD, (255, 140, 40))
T_TCG = ar('كل ألعاب TCG في مكان واحد', 74, SILV, (150, 90, 255))
C_SING = pill('سنقلز وسلابات', FL(70), (80, 50, 200)); C_CGC = pill('تقييم CGC', FL(70), (30, 120, 110))
B_CGC = ar('معتمدين رسمياً مع CGC', 78, GOLD, (255, 170, 60))
C_SELL = pill('بيع كروتك', FL(74), (120, 60, 220)); C_MEM = pill('عضويات HTR', FL(74), (30, 140, 130))
T_NOT = ar('مو بس أونلاين...', 128, SILV, (255, 80, 160))
T_OLAYA = ar('العليا سكوير', 160, GOLD, (255, 170, 60), 8); T_ABHUR = ar('أبحر الجنوبية – جدة', 80, SILV, (40, 200, 200))
T_WEEK = ar('بطولات كل أسبوع', 130, GOLD, (255, 120, 40))
T_Q1 = ar('أي لعبة تبي', 120, SILV, (150, 90, 255)); T_Q2 = ar('بطولتها الجاية؟', 140, GOLD, (255, 140, 40))
T_CM = ar('قول لنا بالتعليقات', 84, TEALG, (40, 200, 190))
P_SAVE = pill('احفظ الفيديو', FL(70), (60, 60, 90)); P_FOL = pill('تابع HTR', FL(78), (200, 30, 90))
E_SITE = en('HTRTCG.COM', 84, TEALG, (40, 200, 190))
LOGO = img_sprite(Image.open(R + 'tools_challenges/htr_logo.png').convert('RGBA'), 460, (255, 230, 200), 22)
def pin(f, cx, cy, s=1.0):
    r = int(70 * s); cv2.circle(f, (cx, cy), r + 16, (60, 200, 255), -1, cv2.LINE_AA)
    cv2.circle(f, (cx, cy), r, (40, 60, 230), -1, cv2.LINE_AA); cv2.circle(f, (cx, cy), int(r * .4), (255, 255, 255), -1, cv2.LINE_AA)
    cv2.fillPoly(f, [np.array([[cx - r * .8, cy + r * .6], [cx + r * .8, cy + r * .6], [cx, cy + r * 2.1]], np.int32)], (40, 60, 230), cv2.LINE_AA)

# ---------- real tournament footage (cropped clean of old captions)
class Clip:
    def __init__(s, src, t0, y0=0.0, y1=1.0, speed=1.0):
        s.src, s.t0, s.y0, s.y1, s.sp = V + src, t0, y0, y1, speed; s.cap = None; s.last = -1; s.img = None
    def frame(s, dt):
        if s.cap is None: s.cap = cv2.VideoCapture(s.src); s.fps = s.cap.get(5)
        idx = int((s.t0 + dt * s.sp) * s.fps)
        if idx != s.last:
            if idx != s.last + 1: s.cap.set(1, idx)
            ok, fr = s.cap.read()
            if ok:
                h, w = fr.shape[:2]; a, b = int(h * s.y0), int(h * s.y1); fr = fr[a:b]
                ch, cw = fr.shape[:2]; sc = max(W / cw, H / ch); fr = cv2.resize(fr, (int(cw * sc + .5), int(ch * sc + .5)), interpolation=cv2.INTER_LINEAR)
                oy, ox = (fr.shape[0] - H) // 2, (fr.shape[1] - W) // 2; s.img = fr[oy:oy + H, ox:ox + W].astype(np.float32)
            s.last = idx
        return s.img
CLIPS = [Clip('videos/htr_local_onepiece_1018.mp4', 5.3), Clip('reels/htr_local_onepiece.mp4', 17.6, .06, 1.0),
         Clip('videos/htr_local_onepiece_1018.mp4', 13.2), Clip('reels/htr_local_heroines_eb05_1102.mp4', 13.0, .06, 1.0),
         Clip('videos/htr_local_winner_1018.mp4', 5.0, .30, 1.0), Clip('reels/htr_local_heroines_eb05_1102.mp4', 17.0, .06, 1.0)]
CUTS = [T['tour'] + .9 * i for i in range(6)]
ENDC2 = Clip('videos/htr_local_winner_1018.mp4', 7.4, .30, .84, .4)
ENDC = Clip('reels/htr_local_heroines_eb05_1102.mp4', 11.0, .16, .80, .3)
def grade_ft(f):  # warm cinematic grade on footage
    f[..., 2] *= 1.06; f[..., 0] *= .94

# ---------- scenes
def phone_y(t): return 1040 + 10 * math.sin(t * 1.6)
def s_hook(t, f):
    f[:] = aurora(t); k = eo(t / .9)
    phone(f, screen_img('home1'), 540, phone_y(t) + 700 * (1 - k), .78, .25 * math.sin(t * .9), -2 + 2 * k)
    blit(f, T1, 540, 260, 1.0 + .03 * eio(t / 3), cl(t / .2)); blit(f, T1b, 540, 395, 1, cl((t - 1.2) / .25))
def s_deals(t, f):
    dt = t - T['deals']; f[:] = aurora(t)
    phone(f, screen_img('home1', key2='deals', k=cl(dt / .35), ripple=(PW * .5, PH_ * .55, dt - 1.2)), 540, phone_y(t), .78, .2 * math.sin(t * .9 + 1), 1.5 * math.sin(t * .7))
    blit(f, C_DEAL, 540, 270, 1.0 + .25 * (1 - ebk(dt / .3)), cl(dt / .1)); sweep(f, t, T['deals'] + .05, (255, 120, 180), .6, .25)
def s_games(t, f):
    dt = t - T['games']; f[:] = aurora(t)
    if t < T['grid']: scr = screen_img('deals', key2='games', k=cl(dt / .35))
    else: scr = screen_img('games', key2='home2', k=cl((t - T['grid']) / .35))
    zz = .74 if not (8.6 <= t < T['grid']) else .95; yo = 40 if zz < .9 else 260
    phone(f, scr, 540, phone_y(t) + yo, zz, .22 * math.sin(t * .9 + 2), -1.5 * math.sin(t * .6))
    blit(f, T_TCG, 540, 250, 1, cl(dt / .2))
    for i, (tg, x, y) in enumerate(((T['games'] + 2.05, 260, 560), (T['games'] + 2.85, 820, 760), (T['games'] + 3.7, 280, 1500))):
        d = t - tg
        if d > 0: blit(f, E_G[i], x, y + 8 * math.sin(t * 3 + i), (.9 + .3 * (1 - ebk(d / .3))), cl(d / .08), (-6, 5, -4)[i])
    if t > T['grid'] + .1: blit(f, T_MORE, 800, 1560, 1 + .25 * (1 - ebk((t - T['grid'] - .1) / .3)), cl((t - T['grid'] - .1) / .1), 6)
def s_grade(t, f):
    dt = t - T['grade']; f[:] = aurora(t)
    phone(f, screen_img('home2', key2='grade', k=cl(dt / .35)), 540, phone_y(t) + 30, .76, .22 * math.sin(t * .9 + 3), 1.2 * math.sin(t * .6))
    blit(f, C_SING, 330, 260, 1 + .2 * (1 - ebk(dt / .3)), cl(dt / .1)); blit(f, C_CGC, 760, 260, 1 + .2 * (1 - ebk((dt - 1.3) / .3)), cl((dt - 1.3) / .1))
    d2 = t - T['cgc']
    if d2 > 0: blit(f, B_CGC, 540, 1580, 1 + .3 * (1 - ebk(d2 / .3)), cl(d2 / .08)); sweep(f, t, T['cgc'], (255, 220, 140), .7, .3); glowflash(f, t, T['cgc'], (255, 230, 180), .15, .35)
def s_sell(t, f):
    dt = t - T['sell']; f[:] = aurora(t)
    if t < T['member']: scr = screen_img('grade', key2='sell', k=cl(dt / .35)); chip = C_SELL; d = dt
    else: scr = screen_img('sell', key2='member', k=cl((t - T['member']) / .35)); chip = C_MEM; d = t - T['member']
    phone(f, scr, 540, phone_y(t) + 30, .76, .22 * math.sin(t * .9 + 4), -1.2 * math.sin(t * .6))
    blit(f, chip, 540, 270, 1 + .25 * (1 - ebk(d / .3)), cl(d / .1))
def s_bridge(t, f):
    dt = t - T['bridge']; f[:] = aurora(t)
    k = eio(cl((dt - .9) / 1.1))  # phone flies away and shrinks
    phone(f, screen_img('member'), 540, phone_y(t) + 200 * k, .76 * (1 - .55 * k), .22 + .6 * k, 10 * k, 1 - k)
    blit(f, T_NOT, 540, 900 - 40 * eo(dt / 1.5), 1 + .2 * (1 - ebk(dt / .3)), cl(dt / .12))
    if dt > 1.85: glowflash(f, t, T['bridge'] + 1.85, (255, 255, 255), .2, .8)
def s_tour(t, f):
    i = max(j for j, c in enumerate(CUTS) if t >= c); dt = t - CUTS[i]
    fr = CLIPS[i].frame(dt)
    z = 1.12 + .05 * dt; M = np.float32([[z, 0, (1 - z) * W / 2], [0, z, (1 - z) * H / 2]]); f[:] = cv2.warpAffine(fr, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    grade_ft(f); glowflash(f, t, CUTS[i], (255, 255, 255), .1, .35)
    g = np.linspace(.75, 0, 640)[:, None, None]; f[:640] *= (1 - g); f[-560:] *= (1 - g[::-1][:560])
    if t < T['weekly']:
        d = t - T['tour']; pin(f, 540, 300, .8 + .04 * math.sin(t * 6)); blit(f, T_OLAYA, 540, 520, 1 + .25 * (1 - ebk(d / .3)), cl(d / .1)); blit(f, T_ABHUR, 540, 680, 1, cl((d - .3) / .2))
    else:
        d = t - T['weekly']; blit(f, T_WEEK, 540, 1520, 1 + .3 * (1 - ebk(d / .3)), cl(d / .08)); blit(f, LOGO, 540, 300, .8, cl(d / .2))
def s_end(t, f):
    dt = t - T['end']; fr = ENDC.frame(dt) if dt < 2.8 else ENDC2.frame(dt - 2.8); f[:] = fr; grade_ft(f); f *= .5
    glowflash(f, t, T['end'] + 2.8, (255, 255, 255), .12, .4)
    embers(f, t, (200, 160, 255), 35, 21, 50)
    blit(f, T_CM, 540, 330, 1, cl(dt / .2)); blit(f, T_Q1, 540, 480, 1 + .2 * (1 - ebk(dt / .3)), cl(dt / .1)); blit(f, T_Q2, 540, 640, 1 + .2 * (1 - ebk((dt - .4) / .3)), cl((dt - .4) / .1))
    for i, x in enumerate((300, 780, 300, 780)):
        lab = (E_G + [en('YU-GI-OH!', 92, GOLD, (255, 180, 40))])[i]; y = 900 + (i // 2) * 170; d = dt - .9 - .15 * i
        if d > 0: blit(f, lab, x, y + 6 * math.sin(t * 3 + i), .75 + .2 * (1 - ebk(d / .3)), cl(d / .08))
    d = dt - 3.2
    if d > 0: blit(f, P_SAVE, 330, 1330, 1 + .15 * (1 - ebk(d / .3)), cl(d / .1))
    d = dt - 4.0
    if d > 0: blit(f, P_FOL, 760, 1330, 1.05 + .08 * abs(math.sin(t * 7)), cl(d / .1))
    blit(f, E_SITE, 540, 1500, 1, cl((dt - 1.5) / .2))

SC = [('hook', s_hook), ('deals', s_deals), ('games', s_games), ('grade', s_grade), ('sell', s_sell), ('bridge', s_bridge), ('tour', s_tour), ('end', s_end)]
EDGE = np.clip((np.minimum(xx, W - 1 - xx) - 10) / 22, 0, 1)[..., None] ** .8
GRAIN = [np.random.default_rng(i).normal(0, 3.5, (H // 2, W // 2, 1)).astype(np.float32) for i in range(6)]
def render(t):
    cur = SC[0][1]
    for k, fn in SC:
        if t >= T[k]: cur = fn
    f = np.zeros((H, W, 3), np.float32); cur(t, f); f *= EDGE
    g = cv2.resize(GRAIN[int(t * FPS) % 6], (W, H), interpolation=cv2.INTER_NEAREST); f += g[..., None] if g.ndim == 2 else g
    return np.clip(f, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'frames':
        os.makedirs('/home/claude/work', exist_ok=True)
        for t in [float(x) for x in sys.argv[2].split(',')]: cv2.imwrite(f'/home/claude/work/st_{t:.1f}.jpg', render(t))
        sys.exit()
    n = int(round(TOTAL * FPS))
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    for i in range(n): p.stdin.write(render(i / FPS).tobytes())
    p.stdin.close(); p.wait(); print('ok', OUT, n)
