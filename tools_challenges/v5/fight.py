"""HTR «أيهم أغلى؟» — arcade FIGHTING-GAME style.  python3 fight.py spec.json stills t.. | a b out.mp4"""
import sys, json, math, numpy as np, cv2
from PIL import Image, ImageDraw
from common import *
SPEC = json.load(open(sys.argv[1])); TM = SPEC['timing']; R = SPEC['rounds']; N = len(R)
P1 = (255, 40, 70); P2 = (40, 140, 255); STEEL = (190, 200, 220)
T_INTRO = TM['intro']; RI = 1.3; ASK = TM['ask']; THINK = 3.0; REV = TM['rev']; T_OUT = TM['outro']; T_END = 2.6
RLEN = [RI + ASK[i] + THINK + REV[i] for i in range(N)]
RST = [T_INTRO + sum(RLEN[:i]) for i in range(N)]; T_OUTRO = T_INTRO + sum(RLEN); TOTAL = T_OUTRO + T_OUT + T_END
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
# diagonal split  (right = P1 red, left = P2 blue)
D = (xx - W / 2) + (yy - 960) * 0.35
SIDE = np.clip(D / 40, -1, 1)[..., None]
BASE = np.zeros((H, W, 3), np.float32); BASE[:] = (14, 8, 10)
RED = np.array(P1[::-1], np.float32); BLU = np.array(P2[::-1], np.float32)
GLOWR = np.exp(-(((xx - 900) / 600) ** 2 + ((yy - 860) / 800) ** 2))[..., None]
GLOWB = np.exp(-(((xx - 180) / 600) ** 2 + ((yy - 860) / 800) ** 2))[..., None]
rng = np.random.default_rng(3); LINES = [(rng.uniform(0, H), rng.uniform(.5, 2.5), rng.uniform(2, 6)) for _ in range(40)]
def bg(t, shake=0.0, flash=None):
    f = BASE + RED * GLOWR * .32 * (SIDE > 0) + BLU * GLOWB * .32 * (SIDE <= 0)
    f = f.copy()
    for y0, sp, th in LINES:      # speed lines streaming toward centre
        y = int((y0 + t * 900 * sp) % H); x = int((t * 1500 * sp + y0 * 3) % (W + 400)) - 200
        cv2.line(f, (x, y), (x + 160, y - 56), (90, 80, 90), int(th), cv2.LINE_AA)
    # split seam
    for k in (-1, 1):
        pass
    p0 = (int(W / 2 + 960 * .35), 0); p1 = (int(W / 2 - 960 * .35), H)
    cv2.line(f, p0, p1, (255, 255, 255), 6, cv2.LINE_AA)
    if flash is not None: f = f + (255 - f) * flash
    if shake > 0:
        dx, dy = int(rng.uniform(-1, 1) * 30 * shake), int(rng.uniform(-1, 1) * 30 * shake)
        f = np.roll(f, (dy, dx), (0, 1))
    return f
CW = 420
def fitimg(path, w, h):
    im0 = Image.open(path); ww = int(min(w, h * im0.width / im0.height)); return card_img(path, ww)
def mk(path, col):
    im = fitimg(path, CW, 590); return dict(n=card_spr(im, col, .8), g=card_spr(im, (255, 255, 255), .9), d=card_spr(gray(im, .35)), s=card_spr(fitimg(path, 190, 265)))
C = [[mk(r['a']['img'], P1), mk(r['b']['img'], P2)] for r in R]
S = end_assets(SPEC.get('tease', 'بكرة تحدي جديد'))
S.update(sel=txt('اختار مقاتلك!', FL(120), WHITE, stroke=6, glow=P1), vs=txt('VS', FB(200), WHITE, stroke=10, glow=(255, 255, 255), gr=30),
         q=txt('أيهم أغلى؟', FL(96), WHITE, stroke=5, glow=P2), qbig=txt('أيهم أغلى؟', FL(150), WHITE, stroke=7, glow=P1, gr=26), fight=txt('FIGHT!', FB(190), WHITE, stroke=12, glow=P1, gr=30),
         ko=txt('K.O.', FB(210), (255, 255, 255), stroke=14, glow=P1, gr=30), win=pill('WINNER', FB(44), (20, 20, 30), fg=WHITE, border=(255, 255, 255), padx=30, pady=10),
         src=txt(SPEC['source'], FL(34), (170, 160, 180)), cont=txt('CONTINUE?', FB(120), WHITE, stroke=8, glow=P1),
         how=txt('كم جولة فزت فيها؟', FL(100), WHITE, stroke=4, glow=P2), cmt=pill('اكتبها بالتعليقات', FL(60), P1, padx=56),
         unk=txt('$ ? ? ?', FB(60), (220, 220, 235)))
ROUND = [txt(f'ROUND {i + 1}', FB(150), WHITE, stroke=10, glow=P2, gr=26) for i in range(N)]
GAME = [pill(r['game'], FB(36), (20, 16, 26), fg=WHITE, border=STEEL) for r in R]
NM = [[fit_txt(r[k]['name'], FB, 44, 470, fill=WHITE, stroke=3) for k in 'ab'] for r in R]
SUB = [[fit_txt(r[k]['set'], FL, 34, 470, fill=STEEL) for k in 'ab'] for r in R]
HPN = [[fit_txt(r[k]['short'], FB, 34, 380, fill=WHITE) for k in 'ab'] for r in R]
PR = [[(txt(r[k]['price'], FB(84), WHITE, stroke=6, glow=(P1 if k == 'a' else P2), gr=24), txt(r[k]['price'], FB(60), (130, 125, 140))) for k in 'ab'] for r in R]
MULT = [pill(r['mult'], FL(56), (255, 255, 255), fg=(20, 16, 26), padx=44) for r in R]
WIN = [0 if r['a']['p'] > r['b']['p'] else 1 for r in R]
XS = [W / 2 + 255, W / 2 - 255]
DIGIT = [txt(str(n), FB(110), WHITE, stroke=6) for n in range(4)]
def hpbar(f, side, frac, name, alpha=1.0):
    # side 0 = right (P1), 1 = left (P2)
    x0, x1 = (W / 2 + 70, W - 40) if side == 0 else (40, W / 2 - 70)
    y0, y1 = 140, 186
    cv2.rectangle(f, (int(x0) - 4, y0 - 4), (int(x1) + 4, y1 + 4), (255, 255, 255), -1)
    cv2.rectangle(f, (int(x0), y0), (int(x1), y1), (40, 30, 30), -1)
    L = (x1 - x0) * frac
    col = (P1 if side == 0 else P2)[::-1]
    if side == 0: cv2.rectangle(f, (int(x0), y0), (int(x0 + L), y1), col, -1)
    else: cv2.rectangle(f, (int(x1 - L), y0), (int(x1), y1), col, -1)
    blit(f, name, (x0 + x1) / 2, 222, 1, alpha)
def rat(t):
    for i in range(N - 1, -1, -1):
        if t >= RST[i]: return i, t - RST[i]
def render(t):
    shake = 0.0; flash = 0.0
    if T_INTRO <= t < T_OUTRO:
        i, lt = rat(t); a0 = RI; rv = RI + ASK[i] + THINK
        shake = env(lt, RI - .05, .25) * .8 + env(lt, rv, .35) * 1.0
        flash = env(lt, rv, .18) * .7 + env(lt, RI - .05, .12) * .5
    elif t < T_INTRO:
        shake = env(t, .6, .3) * .7; flash = env(t, .6, .12) * .5
    f = bg(t, shake, flash)
    if t < T_INTRO:
        k = t; out = eo((t - T_INTRO + .3) / .3)
        blit(f, S['qbig'], W / 2, 300 - 400 * out, ebk(k / .3), 1 - out)
        for j, x in enumerate(XS):
            kk = eo((k - .1) / .35); xx_ = x + (1 if j == 0 else -1) * 700 * (1 - kk) + (1 if j == 0 else -1) * 900 * out
            blit(f, C[0][j]['n'], xx_, 900, .85, 1 if kk > 0 else 0, (6 if j == 0 else -6))
        blit(f, S['vs'], W / 2, 900 + 900 * out, ebk((k - .6) / .3) * (1 + .05 * math.sin(t * 9)), 1 if k > .6 else 0)
        blit(f, S['sel'], W / 2, 1450 + 500 * out, ebk((k - 1.0) / .35), 1 if k > 1.0 else 0)
    elif t < T_OUTRO:
        i, lt = rat(t); r = R[i]; rv = RI + ASK[i] + THINK; L = RLEN[i]
        out = eo((lt - L + .3) / .3)
        if lt < RI:   # ROUND n ... FIGHT!
            if lt < .7: blit(f, ROUND[i], W / 2, 900, ebk(lt / .3), 1)
            else: blit(f, S['fight'], W / 2, 900, 1.6 - .6 * eo((lt - .7) / .2), 1 - max(0, (lt - 1.15) / .15))
            blit(f, GAME[i], W / 2, 1060, ebk((lt - .2) / .3), 1 if lt > .2 else 0)
        else:
            lt2 = lt - RI
            # health bars
            for j in range(2):
                if lt < rv: fr = 1.0
                else: fr = 1.0 if j == WIN[i] else max(0, 1 - (lt - rv) / .5)
                hpbar(f, j, fr * (1 - out) + 0 * out, HPN[i][j], 1 - out)
            # timer
            if lt < rv:
                cv2.rectangle(f, (W // 2 - 62, 112), (W // 2 + 62, 240), (20, 14, 20), -1); cv2.rectangle(f, (W // 2 - 62, 112), (W // 2 + 62, 240), (255, 255, 255), 4)
                if lt2 >= ASK[i]:
                    n = max(0, 3 - int(lt2 - ASK[i])); blit(f, DIGIT[min(3, n)], W / 2, 176, 1 + .25 * env(lt2 - ASK[i], 3 - n, .25), 1)
                else: blit(f, txt('99', FB(80), WHITE, stroke=5), W / 2, 176, 1, 1)
            else: blit(f, S['ko'], W / 2, 180, ebk((lt - rv - .45) / .3), 1 - out if lt > rv + .45 else 0)
            for j in range(2):
                ent = ebk(lt2 / .35, 1.2)
                x = XS[j] + (1 if j == 0 else -1) * 700 * (1 - min(1, lt2 / .25)) + (1 if j == 0 else -1) * 900 * out
                if lt < rv: spr = C[i][j]['n']; sc = (1.5 - .5 * min(1, lt2 / .22)) + .02 * math.sin(t * 6 + j); rot = (-5 if j == 0 else 5)
                else:
                    if j == WIN[i]: spr = C[i][j]['g']; sc = 1.08 + .05 * env(lt, rv, .3); rot = 0
                    else:
                        spr = C[i][j]['d']; sc = .9; rot = (-5 if j == 0 else 5) + 8 * math.sin(min(1, (lt - rv) / .4) * 12) * (1 - min(1, (lt - rv) / .4))
                blit(f, spr, x, 760, sc, 1, rot)
                blit(f, NM[i][j], x, 1110, 1, (1 - out)); blit(f, SUB[i][j], x, 1165, 1, 1 - out)
                if lt < rv: blit(f, S['unk'], x, 1250, 1, 1 - out)
                else:
                    k2 = ebk((lt - rv) / .3)
                    if j == WIN[i]: blit(f, PR[i][j][0], x, 1255, k2, 1 - out); blit(f, S['win'], x, 400, k2, 1 - out)
                    else:
                        blit(f, PR[i][j][1], x, 1255, 1, 1 - out); cv2.line(f, (int(x - 120), 1258), (int(x - 120 + 240 * min(1, (lt - rv) / .25)), 1250), (255, 255, 255), 8, cv2.LINE_AA)
                        blit(f, S['ko'], x, 760, .55 * ebk((lt - rv - .2) / .3), (1 - out) if lt > rv + .2 else 0, 14)
            if lt < rv: blit(f, S['vs'], W / 2, 760, (.55 + .04 * math.sin(t * 10)) * (1 - out), 1)
            if lt2 >= ASK[i] and lt < rv: blit(f, S['q'], W / 2, 1400, 1 + .05 * math.sin(t * 8), 1)
            if lt >= rv: blit(f, MULT[i], W / 2, 1400, ebk((lt - rv - .5) / .35), (lt > rv + .5) * (1 - out))
            blit(f, S['src'], W / 2, 1720, 1, 1 - out)
    elif t < T_OUTRO + T_OUT:
        k = t - T_OUTRO
        blit(f, S['cont'], W / 2, 380, ebk(k / .35) * (1 + .04 * math.sin(t * 8)), 1)
        n = max(0, 9 - int(k * 3)); blit(f, txt(str(n), FB(220), WHITE, stroke=10, glow=P1), W / 2, 640, 1 + .15 * env(k * 3 % 1, 0, .3), 1)
        blit(f, S['how'], W / 2, 920, ebk((k - .3) / .35), 1 if k > .3 else 0)
        for i in range(N):
            kk = ebk((k - .5 - i * .12) / .35); blit(f, C[i][WIN[i]]['s'], W / 2 + (i - (N - 1) / 2) * 240, 1210, kk, 1 if kk > 0 else 0, (i - 1) * 5)
        blit(f, S['cmt'], W / 2, 1480, ebk((k - 1.0) / .35) * (1 + .03 * math.sin(t * 6)), 1 if k > 1.0 else 0)
    else:
        end_card(f, t - T_OUTRO - T_OUT, S)
    if t < T_OUTRO + T_OUT: blit(f, S['wm'], W - 120, 70, .8, .9)
    if t > TOTAL - .4: f = f * max(0, (TOTAL - t) / .4)
    return np.clip(f, 0, 255).astype(np.uint8)
def cues():
    ev = []
    for i in range(N):
        ev += [('roundbell', RST[i]), ('fight', RST[i] + .75), ('slam', RST[i] + RI), ('count', RST[i] + RI + ASK[i]), ('ko', RST[i] + RI + ASK[i] + THINK)]
    return dict(total=TOTAL, intro=0, outro=T_OUTRO, end=T_OUTRO + T_OUT, events=ev,
                voice=SPEC.get('voice_at', []))
def voice_offsets():
    o = [.25]
    for i in range(N): o += [RST[i] + RI + .05, RST[i] + RI + ASK[i] + THINK + .08]
    o.append(T_OUTRO + .2); return o
if __name__ == '__main__':
    json.dump(dict(cues(), offs=voice_offsets()), open('cues.json', 'w'))
    if sys.argv[2] == 'stills': stills(render, [float(x) for x in sys.argv[3:]]); print(TOTAL)
    elif sys.argv[2] == 'cues': print(TOTAL)
    else: encode(render, float(sys.argv[2]), float(sys.argv[3]), sys.argv[4])
