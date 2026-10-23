"""HTR «أيهم أغلى؟» VS quiz.  python3 vs.py spec.json stills t.. | python3 vs.py spec.json a b out.mp4"""
import sys, json, math, numpy as np, cv2
from PIL import Image
from common import *
SPEC = json.load(open(sys.argv[1])); TM = SPEC['timing']; R = SPEC['rounds']; N = len(R)
T_INTRO = TM['intro']; ASK = TM['ask']; REV = TM['rev']; THINK = 2.6; T_OUT = TM['outro']; T_END = 2.6
RLEN = [ASK[i] + THINK + REV[i] for i in range(N)]
RST = [T_INTRO + sum(RLEN[:i]) for i in range(N)]; T_OUTRO = T_INTRO + sum(RLEN); TOTAL = T_OUTRO + T_OUT + T_END
bg = make_bg(cy=780)
CW = 430
def mk(path):
    im = card_img(path, CW); return dict(n=card_spr(im), g=card_spr(im, GREEN), d=card_spr(gray(im)), s=card_spr(card_img(path, 200)))
C = [[mk(r['a']['img']), mk(r['b']['img'])] for r in R]
S = end_assets(SPEC.get('tease', 'كل أسبوع تحدي جديد'))
S.update(t1=txt('أيهم', FL(130), WHITE), t2=txt('أغلى؟', FL(190), PURPLE, glow=PURPLE), sub=pill('أغلب الناس يغلطون!', FL(52), (24, 18, 50), border=RED),
         vs=txt('VS', FB(92), WHITE, stroke=6, glow=PURPLE), q=txt('؟', FL(130), WHITE, glow=PURPLE), think=txt('فكّر بسرعة…', FL(58), WHITE, glow=RED),
         unk=txt('$???', FB(64), (200, 190, 255)), more=txt('أغلى', FL(46), WHITE), src=txt(SPEC['source'], FL(34), DIM),
         how=txt('كم جولة جبتها صح؟', FL(110), WHITE, glow=PURPLE), cmt=pill('اكتبها بالتعليقات', FL(60), PURPLE, padx=56))
from PIL import ImageDraw
BK = Image.new('RGBA', (300, 418), (0, 0, 0, 0)); bd = ImageDraw.Draw(BK)
bd.rounded_rectangle((0, 0, 299, 417), 22, fill=(40, 30, 80, 255), outline=PURPLE + (255,), width=6)
for q in range(0, 600, 34): bd.line((q - 300, 0, q, 417), fill=(60, 48, 110, 255), width=10)
_f = FL(240); _bb = bd.textbbox((0, 0), '؟', font=_f); bd.text((150 - (_bb[2] - _bb[0]) / 2 - _bb[0], 209 - (_bb[3] - _bb[1]) / 2 - _bb[1]), '؟', font=_f, fill=WHITE, stroke_width=8, stroke_fill=PURPLE)
BACK = card_spr(BK, PURPLE)
RH = [txt(f'الجولة {i + 1} من {N}', FL(54), LILAC) for i in range(N)]
GAME = [pill(r['game'], FB(36), (24, 18, 50), fg=(160, 240, 230), border=TEAL) for r in R]
NAMES = [[fit_txt(r[k]['name'], FB, 40, 460, fill=WHITE) for k in 'ab'] for r in R]
SETS = [[fit_txt(r[k]['set'], FL, 34, 460, fill=LILAC) for k in 'ab'] for r in R]
PR = [[(txt(r[k]['price'], FB(66), WHITE, glow=GREEN), txt(r[k]['price'], FB(56), (150, 140, 180))) for k in 'ab'] for r in R]
MULT = [pill(r['mult'], FL(54), GREEN, padx=44) for r in R]
WIN = [0 if r['a']['p'] > r['b']['p'] else 1 for r in R]
BADGE = pill('الأغلى', FL(44), GREEN, padx=30, pady=10)
XS = [W / 2 + 255, W / 2 - 255]   # first card on the right (RTL)
def rat(t):
    for i in range(N - 1, -1, -1):
        if t >= RST[i]: return i, t - RST[i]
def render(t):
    win = 0.0
    if T_INTRO <= t < T_OUTRO:
        i, lt = rat(t); rv = ASK[i] + THINK
        if lt >= rv: win = min(1, (lt - rv) / .25) * (1 - max(0, (lt - RLEN[i] + .3) / .3))
    f = bg(t, win)
    if t < T_INTRO:
        k = t; out = eo((t - T_INTRO + .3) / .3)
        blit(f, S['t1'], W / 2, 360 - 300 * out, ebk(k / .4), 1 - out); blit(f, S['t2'], W / 2, 520 - 300 * out, ebk((k - .2) / .4), (k > .2) * (1 - out))
        for j, x in enumerate(XS):
            kk = ebk((k - .4 - j * .15) / .45); blit(f, BACK, x, 900 + 700 * (1 - kk) + 900 * out, 1.05, 1 if kk > 0 else 0, (8 if j == 0 else -8) * kk)
        blit(f, S['vs'], W / 2, 900 + 900 * out, ebk((k - .8) / .3), 1 if k > .8 else 0)
        blit(f, S['sub'], W / 2, 1250 + 400 * out, ebk((k - 1.0) / .3), 1 if k > 1.0 else 0)
    elif t < T_OUTRO:
        i, lt = rat(t); r = R[i]; rv = ASK[i] + THINK; L = RLEN[i]
        out = eo((lt - L + .3) / .3); inn = eo(lt / .35)
        blit(f, RH[i], W / 2, 120, 1, inn * (1 - out)); blit(f, GAME[i], W / 2, 200, 1, inn * (1 - out))
        for j in range(N):
            col = GREEN if j < i else (PURPLE if j == i else (60, 52, 100)); cv2.circle(f, (int(W / 2 + (j - 1) * 40), 262), 11 if j == i else 8, col[::-1], -1, cv2.LINE_AA)
        for j in range(2):
            x = XS[j] + (1 if j == 0 else -1) * 900 * (1 - eo((lt - j * .12) / .4)) + (1 if j == 0 else -1) * 900 * out
            if lt < rv: spr = C[i][j]['n']; sc = 1 + .02 * math.sin(t * 3 + j)
            else: spr = C[i][j]['g'] if j == WIN[i] else C[i][j]['d']; sc = (1.06 + .04 * env(lt, rv, .3)) if j == WIN[i] else .94
            blit(f, spr, x, 720, sc, 1, (-3 if j == 0 else 3) * (lt < rv))
            blit(f, NAMES[i][j], x, 1050, 1, inn * (1 - out)); blit(f, SETS[i][j], x, 1105, 1, inn * (1 - out))
            if lt < rv: blit(f, S['unk'], x, 1190, 1, inn * (1 - out))
            else:
                k2 = ebk((lt - rv) / .35)
                if j == WIN[i]:
                    blit(f, PR[i][j][0], x, 1190, k2, 1 - out); blit(f, BADGE, x, 420 - 10 * math.sin(t * 5), k2, 1 - out)
                else:
                    blit(f, PR[i][j][1], x, 1190, 1, 1 - out); cv2.line(f, (int(x - 110), 1192), (int(x - 110 + 220 * min(1, (lt - rv) / .25)), 1186), (69, 34, 255), 7, cv2.LINE_AA)
        vs_spr = S['q'] if ASK[i] <= lt < rv else S['vs']
        blit(f, vs_spr, W / 2, 720, (1 + .08 * math.sin(t * 8)) * (1 - out), inn)
        if ASK[i] - .1 <= lt < rv:
            p = min(1, (lt - ASK[i]) / THINK); blit(f, S['think'], W / 2, 1300, 1, 1)
            cv2.rectangle(f, (190, 1372), (890, 1392), (60, 40, 50), -1); cv2.rectangle(f, (190, 1372), (int(190 + 700 * (1 - p)), 1392), (69, 34, 255) if p > .6 else (255, 117, 142), -1)
        if lt >= rv: blit(f, MULT[i], W / 2, 1330, ebk((lt - rv - .3) / .35), (lt > rv + .3) * (1 - out))
        blit(f, S['src'], W / 2, 1700, 1, inn * (1 - out))
    elif t < T_OUTRO + T_OUT:
        k = t - T_OUTRO
        blit(f, S['how'], W / 2, 420, ebk(k / .4), 1)
        for i in range(N):
            kk = ebk((k - .3 - i * .15) / .4); y = 700 + i * 250
            blit(f, C[i][WIN[i]]['s'], W / 2, y, kk, 1 if kk > 0 else 0, (i - 1) * 4)
        blit(f, S['cmt'], W / 2, 1520, ebk((k - 1.0) / .35) * (1 + .03 * math.sin(t * 6)), 1 if k > 1.0 else 0)
    else:
        end_card(f, t - T_OUTRO - T_OUT, S)
    if t < T_OUTRO + T_OUT: blit(f, S['wm'], W - 130, 80, 1, .9)
    fl = sum(env(t, RST[i] + ASK[i] + THINK, .15) * .5 for i in range(N)) + env(t, T_OUTRO + T_OUT, .15) * .5
    f = np.clip(f + (255 - f) * fl, 0, 255)
    if t > TOTAL - .4: f = f * max(0, (TOTAL - t) / .4)
    return f.astype(np.uint8)
def cues(): return dict(total=TOTAL, intro=0, outro=T_OUTRO, end=T_OUTRO + T_OUT, rounds=[dict(start=RST[i], cd=RST[i] + ASK[i], reveal=RST[i] + ASK[i] + THINK, end=RST[i] + RLEN[i]) for i in range(N)])
if __name__ == '__main__':
    json.dump(cues(), open('cues.json', 'w'))
    if sys.argv[2] == 'stills': stills(render, [float(x) for x in sys.argv[3:]]); print(TOTAL)
    else: encode(render, float(sys.argv[2]), float(sys.argv[3]), sys.argv[4])
