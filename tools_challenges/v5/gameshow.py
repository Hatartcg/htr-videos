"""HTR «خمّن السعر» — TV GAME-SHOW style (marquee bulbs, spotlights, buzzers, split-flap price board).
python3 gameshow.py spec.json stills t.. | a b out.mp4"""
import sys, json, math, numpy as np, cv2
from PIL import Image, ImageDraw
from common import *
SPEC = json.load(open(sys.argv[1])); TM = SPEC['timing']; R = SPEC['rounds']; N = len(R)
T_INTRO = TM['intro']; ASK = TM['ask']; THINK = 3.0; REV = TM['rev']; T_OUT = TM['outro']; T_END = 2.6
RLEN = [ASK[i] + THINK + REV[i] for i in range(N)]
RST = [T_INTRO + sum(RLEN[:i]) for i in range(N)]; T_OUTRO = T_INTRO + sum(RLEN); TOTAL = T_OUTRO + T_OUT + T_END
MAG = (255, 40, 150); TEAL_ = (0, 220, 210); REDB = (255, 60, 60); NAVY = (10, 8, 30); BULB = (255, 250, 240)
BTN = [REDB, TEAL_, MAG]; LET = ['أ', 'ب', 'ج']
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
BASE = np.zeros((H, W, 3), np.float32); BASE[:] = NAVY[::-1]
STAGE = np.clip((yy - 1250) / 300, 0, 1)[..., None]   # floor
BASE = BASE * (1 - STAGE * .3) + STAGE * np.array((60, 20, 40), np.float32)
# curtains on the sides
CURT = np.zeros((H, W), np.float32)
for side in (0, 1):
    xs_ = xx if side == 0 else (W - xx)
    m = np.clip((160 - xs_) / 160, 0, 1) * (.6 + .4 * np.cos(xs_ / 18))
    CURT = np.maximum(CURT, m)
BASE = BASE * (1 - CURT[..., None]) + CURT[..., None] * np.array((60, 20, 150), np.float32) * (.6 + .4 * np.cos(xx / 22))[..., None]
def cone(cx_top, ang, width=.22):
    a = np.arctan2(xx - cx_top, yy + 50) - ang
    return np.exp(-(a / width) ** 2) * np.clip(yy / 1600, 0, 1)
def bg(t, win=0.0):
    f = BASE.copy()
    for k, (x0, ph, col) in enumerate([(200, 0, MAG), (880, 1.7, TEAL_), (540, 3.1, (200, 200, 255))]):
        c = cone(x0, .35 * math.sin(t * .7 + ph), .16 + .05 * k)
        f += c[..., None] * np.array(col[::-1], np.float32) * (.22 + .25 * win)
    # spotlight pool on floor centre
    pool = np.exp(-(((xx - W / 2) / 360) ** 2 + ((yy - 1260) / 70) ** 2))[..., None]
    f += pool * 70
    return f
def bulbs(f, x0, y0, x1, y1, t, step=46, r=9, phase=0):
    pts = []
    for x in np.arange(x0, x1 + 1, step): pts += [(x, y0), (x, y1)]
    for y in np.arange(y0 + step, y1, step): pts += [(x0, y), (x1, y)]
    for k, (x, y) in enumerate(pts):
        on = ((k + int(t * 8) + phase) % 3) != 0
        c = BULB if on else (90, 80, 70)
        if on: cv2.circle(f, (int(x), int(y)), r + 7, (90, 120, 160), -1, cv2.LINE_AA)
        cv2.circle(f, (int(x), int(y)), r, c[::-1], -1, cv2.LINE_AA)
CW = 430
def fitimg(path, w, h):
    im0 = Image.open(path); ww = int(min(w, h * im0.width / im0.height)); return card_img(path, ww)
CS = [dict(n=card_spr(fitimg(r['img'], CW, 600), (255, 255, 255), .45), s=card_spr(fitimg(r['img'], 210, 290))) for r in R]
S = end_assets(SPEC.get('tease', 'بكرة تحدي جديد'))
S.update(t1=txt('خمّن', FL(170), WHITE, stroke=6, glow=MAG, gr=26), t2=txt('السعر!', FL(170), WHITE, stroke=6, glow=TEAL_, gr=26),
         sub=pill(SPEC['subtitle'], FL(50), (40, 10, 60), fg=WHITE, border=MAG), src=txt(SPEC['source'], FL(32), (180, 170, 210)),
         ok=txt('صح!', FL(150), WHITE, stroke=8, glow=TEAL_, gr=26), score=txt('كم جبت من ٣؟', FL(120), WHITE, stroke=5, glow=MAG),
         cmt=pill('اكتبها بالتعليقات', FL(60), MAG, padx=56), lock=txt('ثبّت جوابك!', FL(80), WHITE, glow=REDB))
RH = [txt(f'السؤال {i + 1} من {N}', FL(52), (230, 220, 255)) for i in range(N)]
NAME = [fit_txt(r['name'], FB, 46, 900, fill=WHITE, stroke=3) for r in R]; SET = [fit_txt(r['set'], FL, 38, 900, fill=(210, 200, 240)) for r in R]
OPT = [[txt(o, FB(54), WHITE, stroke=3) for o in r['options']] for r in R]
LTR = [txt(l, FL(70), WHITE, stroke=3) for l in LET]
TILE = {}
def tile(ch, h=110):
    k = (ch, h)
    if k not in TILE:
        w = int(h * .7); im = Image.new('RGBA', (w + 8, h + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((4, 4, w + 4, h + 4), 10, fill=(22, 20, 30, 255), outline=(80, 80, 100, 255), width=3)
        fnt = FB(int(h * .62)); bb = d.textbbox((0, 0), ch, font=fnt); d.text((4 + w / 2 - (bb[2] + bb[0]) / 2, 4 + h / 2 - (bb[3] + bb[1]) / 2), ch, font=fnt, fill=(255, 255, 255))
        d.line((6, h / 2 + 4, w + 2, h / 2 + 4), fill=(0, 0, 0, 255), width=3)
        TILE[k] = to_bgra(im)
    return TILE[k]
CH = '0123456789$,'
def flap(f, s, prog, cx, cy, h=110, seed=0):
    n = len(s); w = int(h * .7) + 6; x0 = cx - n * w / 2 + w / 2
    for i, ch in enumerate(s):
        p = (prog * (n + 4) - i) / 4      # staggered
        if p >= 1: c = ch; sq = 1
        elif p <= 0: c = ' '; sq = 1
        else:
            j = int(p * 12 + i * 3 + seed) % len(CH); c = CH[j]; sq = abs(math.cos(p * 12 * math.pi))
        t_ = tile(c if c != ' ' else ' ', h)
        if sq < .98: t_ = cv2.resize(t_, (t_.shape[1], max(2, int(t_.shape[0] * max(.08, sq)))))
        blit(f, t_, x0 + i * w, cy, 1, 1)
def button(f, k, cx, cy, lit, dim, t):
    col = BTN[k]; r = 64
    c = tuple(int(v * (.35 if dim else 1)) for v in col)
    if lit: cv2.circle(f, (int(cx), int(cy)), r + 26 + int(6 * math.sin(t * 14)), tuple(int(v * .5) for v in col[::-1]), -1, cv2.LINE_AA)
    cv2.circle(f, (int(cx), int(cy) + 10), r, tuple(int(v * .45) for v in c[::-1]), -1, cv2.LINE_AA)
    cv2.circle(f, (int(cx), int(cy)), r, c[::-1], -1, cv2.LINE_AA)
    cv2.circle(f, (int(cx - 18), int(cy - 20)), 16, (255, 255, 255), -1, cv2.LINE_AA)
    blit(f, LTR[k], cx, cy + 4, 1, .5 if dim else 1)
rng = np.random.default_rng(9); CONF = [(rng.uniform(0, W), rng.uniform(-400, 0), rng.uniform(200, 500), rng.uniform(-3, 3), BTN[rng.integers(0, 3)] if rng.random() < .7 else (255, 255, 255)) for _ in range(90)]
def confetti(f, k):
    if k <= 0 or k > 2.2: return
    for x, y, v, sp, col in CONF:
        yy_ = y + v * k * 1.6; xx_ = x + 40 * math.sin(k * 4 + sp)
        if 0 < yy_ < H:
            a = k * 6 + sp; dx, dy = 14 * math.cos(a), 7
            cv2.rectangle(f, (int(xx_ - dx), int(yy_ - dy)), (int(xx_ + dx), int(yy_ + dy)), col[::-1], -1)
def rat(t):
    for i in range(N - 1, -1, -1):
        if t >= RST[i]: return i, t - RST[i]
BX = [W / 2 + 300, W / 2, W / 2 - 300]   # أ on the right (RTL)
def render(t):
    win = 0.0
    if T_INTRO <= t < T_OUTRO:
        i, lt = rat(t); rv = ASK[i] + THINK
        if lt >= rv: win = min(1, (lt - rv) / .3)
    f = bg(t, win)
    if t < T_INTRO:
        k = t; out = eo((t - T_INTRO + .3) / .3)
        y = 560 - 500 * out
        cv2.rectangle(f, (110, int(y - 260)), (970, int(y + 260)), (40, 10, 50), -1); cv2.rectangle(f, (110, int(y - 260)), (970, int(y + 260)), (230, 200, 255), 6)
        bulbs(f, 110, y - 260, 970, y + 260, t)
        blit(f, S['t1'], W / 2, y - 90, ebk(k / .4), 1); blit(f, S['t2'], W / 2, y + 100, ebk((k - .25) / .4), 1 if k > .25 else 0)
        blit(f, S['sub'], W / 2, 960 - 500 * out, ebk((k - .6) / .35), (k > .6) * (1 - out))
        for j in range(3): button(f, j, BX[j], 1450 + 600 * out, (int(t * 4) % 3) == j, False, t) if k > .8 + j * .12 else None
    elif t < T_OUTRO:
        i, lt = rat(t); r = R[i]; rv = ASK[i] + THINK; L = RLEN[i]
        out = eo((lt - L + .3) / .3); inn = eo(lt / .4)
        blit(f, RH[i], W / 2, 110, 1, inn * (1 - out))
        # price board (split-flap)
        cv2.rectangle(f, (150, 175), (930, 335), (25, 10, 35), -1); cv2.rectangle(f, (150, 175), (930, 335), (230, 200, 255), 4)
        bulbs(f, 150, 175, 930, 335, t, step=40, r=6, phase=i)
        if lt < rv: flap(f, '$???', 1, W / 2, 255)
        else: flap(f, r['price'], min(1, (lt - rv) / 1.0), W / 2, 255, seed=i)
        # card on turntable
        spin = math.cos(min(1, lt / .9) * math.pi * 2) if lt < .9 else 1.0
        sx = max(.05, abs(spin)); c = CS[i]['n']
        if sx < .999: c = cv2.resize(c, (max(2, int(c.shape[1] * sx)), c.shape[0]))
        blit(f, c, W / 2 + 900 * out, 760 + 10 * math.sin(t * 2), (.85 + .15 * inn), 1)
        cv2.ellipse(f, (int(W / 2 + 900 * out), 1110), (300, 46), 0, 0, 360, (90, 60, 120), -1, cv2.LINE_AA); cv2.ellipse(f, (int(W / 2 + 900 * out), 1104), (300, 46), 0, 0, 360, (200, 170, 240), 3, cv2.LINE_AA)
        blit(f, NAME[i], W / 2, 1185, 1, inn * (1 - out)); blit(f, SET[i], W / 2, 1240, 1, inn * (1 - out))
        for j in range(3):
            kk = ebk((lt - .3 - j * .1) / .35)
            correct = j == r['answer']
            lit = (lt >= rv and correct) or (ASK[i] <= lt < rv and int((lt - ASK[i]) * 6) % 3 == j)
            dim = lt >= rv and not correct
            yb = 1530 + 700 * out
            # price label plate above button
            cv2.rectangle(f, (int(BX[j] - 130), int(yb - 175)), (int(BX[j] + 130), int(yb - 95)), (30, 15, 45) if not (lt >= rv and correct) else (40, 90, 80), -1)
            cv2.rectangle(f, (int(BX[j] - 130), int(yb - 175)), (int(BX[j] + 130), int(yb - 95)), BTN[j][::-1], 3)
            blit(f, OPT[i][j], BX[j], yb - 135, kk, .35 if dim else 1)
            if kk > 0: button(f, j, BX[j], yb, lit, dim, t)
        if ASK[i] <= lt < rv:
            n = 3 - int(lt - ASK[i]); blit(f, txt(str(max(1, n)), FB(150), WHITE, stroke=8, glow=REDB), W / 2, 1715, 1 + .3 * env(lt - ASK[i], 3 - n, .3), 1)
            blit(f, S['lock'], W / 2, 1530 + 2000 * 0, 1, 0)
        if lt >= rv:
            blit(f, S['ok'], BX[r['answer']], 1230 - 60, 0, 0)
            confetti(f, lt - rv)
        blit(f, S['src'], W / 2, 1810, 1, inn * (1 - out))
    elif t < T_OUTRO + T_OUT:
        k = t - T_OUTRO
        cv2.rectangle(f, (110, 240), (970, 520), (40, 10, 50), -1); cv2.rectangle(f, (110, 240), (970, 520), (230, 200, 255), 6); bulbs(f, 110, 240, 970, 520, t)
        blit(f, S['score'], W / 2, 380, ebk(k / .4), 1)
        for i in range(N):
            kk = ebk((k - .3 - i * .15) / .4); x = W / 2 + (1 - i) * 290
            blit(f, CS[i]['s'], x, 800, kk, 1 if kk > 0 else 0, (i - 1) * 4)
            blit(f, txt(R[i]['price'], FB(46), WHITE, stroke=3), x, 990, kk, 1 if kk > 0 else 0)
        for j, s_ in enumerate(['0/3', '1/3', '2/3', '3/3']):
            kk = ebk((k - .8 - j * .08) / .3); blit(f, pill(s_, FB(44), (40, 15, 60), fg=WHITE, border=BTN[j % 3], padx=28), W / 2 + (1.5 - j) * 200, 1170, kk, 1 if kk > 0 else 0)
        blit(f, S['cmt'], W / 2, 1360, ebk((k - 1.2) / .35) * (1 + .03 * math.sin(t * 6)), 1 if k > 1.2 else 0)
    else:
        f[:] = NAVY[::-1]; end_card(f, t - T_OUTRO - T_OUT, S)
    if t < T_OUTRO + T_OUT: blit(f, S['wm'], W - 120, 1860, .7, .9)
    fl = sum(env(t, RST[i] + ASK[i] + THINK, .15) * .45 for i in range(N))
    f = f + (255 - f) * fl
    if t > TOTAL - .4: f = f * max(0, (TOTAL - t) / .4)
    return np.clip(f, 0, 255).astype(np.uint8)
def voice_offsets():
    o = [.25]
    for i in range(N): o += [RST[i] + .1, RST[i] + ASK[i] + THINK + .05]
    o.append(T_OUTRO + .2); return o
def cues():
    ev = [('fanfare', 0.0)]
    for i in range(N): ev += [('spin', RST[i]), ('count', RST[i] + ASK[i]), ('correct', RST[i] + ASK[i] + THINK)]
    return dict(total=TOTAL, intro=0, outro=T_OUTRO, end=T_OUTRO + T_OUT, events=ev, offs=voice_offsets())
if __name__ == '__main__':
    json.dump(cues(), open('cues.json', 'w'))
    if sys.argv[2] == 'stills': stills(render, [float(x) for x in sys.argv[3:]]); print(TOTAL)
    elif sys.argv[2] == 'cues': print(TOTAL)
    else: encode(render, float(sys.argv[2]), float(sys.argv[3]), sys.argv[4])
