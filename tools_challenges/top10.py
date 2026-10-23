"""HTR «أغلى ١٠ كروت في إصدار» countdown.  python3 top10.py spec.json stills t.. | python3 top10.py spec.json a b out.mp4"""
import sys, json, math, numpy as np, cv2
from PIL import Image, ImageDraw
from common import *
SPEC = json.load(open(sys.argv[1])); TM = SPEC['timing']; CARDS = SPEC['cards']   # ordered #10 .. #1
N = len(CARDS); T_INTRO = TM['intro']; DUR = TM['dur']; T_OUT = TM['outro']; T_END = 2.6
ST = [T_INTRO + sum(DUR[:i]) for i in range(N)]; T_OUTRO = T_INTRO + sum(DUR); TOTAL = T_OUTRO + T_OUT + T_END
bg = make_bg(cy=900)
CW = 560
SPR = []
for c in CARDS:
    im = card_img(c['img'], CW); SPR.append(dict(n=card_spr(im, PURPLE, .6), g=card_spr(im, GREEN), s=card_spr(card_img(c['img'], 150))))
S = end_assets('كل أسبوع إصدار جديد')
S.update(t1=txt('أغلى ١٠ كروت في', FL(96), WHITE), t2=fit_txt(SPEC['set_title'], FB, 92, 960, fill=PURPLE, glow=PURPLE), game=pill(SPEC['game'], FB(40), (24, 18, 50), fg=(160, 240, 230), border=TEAL),
         who=txt('مين رقم ١؟', FL(110), WHITE, glow=RED), hdr=pill('TOP 10 · ' + SPEC['set_short'], FB(34), (24, 18, 50), fg=LILAC, border=PURPLE),
         src=txt(SPEC['source'], FL(34), DIM), q=txt('عندك واحد منهم؟', FL(110), WHITE, glow=PURPLE), cmt=pill('قول لنا بالتعليقات', FL(60), PURPLE, padx=56))
BK = Image.new('RGBA', (CW, int(CW * 1.395)), (0, 0, 0, 0)); bd = ImageDraw.Draw(BK); bd.rounded_rectangle((0, 0, BK.width - 1, BK.height - 1), 26, fill=(40, 30, 80, 255), outline=PURPLE + (255,), width=8)
for q in range(0, 1400, 50): bd.line((q - 800, 0, q, BK.height), fill=(58, 46, 106, 255), width=16)
BACK = card_spr(BK, PURPLE)
RANK = [rrect(150, 96, 22, (PURPLE if i < N - 1 else GREEN) + (255,)) for i in range(N)]
RANKT = [txt(f'#{N - i}', FB(60), WHITE) for i in range(N)]
NAME = [fit_txt(c['name'], FB, 50, 900, fill=WHITE) for c in CARDS]; RAR = [fit_txt(c['rarity'], FL, 40, 900, fill=LILAC) for c in CARDS]
_digits = {}
def price_spr(v, big=False):
    s = f"${int(round(v)):,}"
    k = (s, big)
    if k not in _digits:
        if len(_digits) > 400: _digits.clear()
        _digits[k] = txt(s, FB(150 if big else 130), WHITE, stroke=8, glow=GREEN if big else PURPLE, gr=26)
    return _digits[k]
def at(t):
    for i in range(N - 1, -1, -1):
        if t >= ST[i]: return i, t - ST[i]
def render(t):
    win = 0.0
    if T_INTRO <= t < T_OUTRO:
        i, lt = at(t)
        if i == N - 1: win = min(1, lt / .3)
    f = bg(t, win, 20 if win else 16)
    if t < T_INTRO:
        k = t; out = eo((t - T_INTRO + .3) / .3)
        blit(f, S['t1'], W / 2, 300 - 300 * out, ebk(k / .4), 1 - out); blit(f, S['t2'], W / 2, 420 - 300 * out, ebk((k - .2) / .4), (k > .2) * (1 - out))
        blit(f, S['game'], W / 2, 530 - 300 * out, ebk((k - .35) / .35), (k > .35) * (1 - out))
        blit(f, BACK, W / 2, 1000 + 900 * out, ebk((k - .5) / .5) * (1 + .02 * math.sin(t * 4)), 1 if k > .5 else 0, 3 * math.sin(t * 2))
        blit(f, S['who'], W / 2, 1520 + 500 * out, ebk((k - 1.2) / .35), 1 if k > 1.2 else 0)
    elif t < T_OUTRO:
        i, lt = at(t); c = CARDS[i]; D = DUR[i]; inn = eo(lt / .3); out = eo((lt - D + .2) / .2)
        blit(f, S['hdr'], W / 2, 110, 1, 1)
        for j in range(N):
            col = GREEN if j < i else (PURPLE if j == i else (60, 52, 100)); cv2.circle(f, (int(W / 2 + (j - (N - 1) / 2) * 34), 180), 10 if j == i else 7, col[::-1], -1, cv2.LINE_AA)
        roll = min(1, lt / min(1.0, D * .55)); v = c['price'] * (1 - (1 - roll) ** 3)
        blit(f, price_spr(v, i == N - 1), W / 2, 320, 1 + .1 * env(lt, D * .55 if D < 2 else 1.0, .25), inn)
        sp = SPR[i]['g'] if i == N - 1 and lt > .4 else SPR[i]['n']
        x = W / 2 + 1200 * (1 - inn) - 1200 * out
        blit(f, sp, x, 900, 1 + .03 * math.sin(t * 2.5), 1, -4 * (1 - inn))
        blit(f, RANK[i], x - 250, 470, ebk((lt - .1) / .3), 1); blit(f, RANKT[i], x - 250, 470, ebk((lt - .1) / .3), 1)
        blit(f, NAME[i], W / 2, 1360, 1, inn * (1 - out)); blit(f, RAR[i], W / 2, 1425, 1, inn * (1 - out))
        blit(f, S['src'], W / 2, 1700, 1, 1)
    elif t < T_OUTRO + T_OUT:
        k = t - T_OUTRO
        blit(f, S['q'], W / 2, 330, ebk(k / .4), 1)
        for j in range(N):
            r_, cc = divmod(j, 5); kk = ebk((k - .2 - j * .06) / .35)
            blit(f, SPR[N - 1 - j]['s'], W / 2 + (cc - 2) * 190, 690 + r_ * 270, kk, 1 if kk > 0 else 0)
        blit(f, S['cmt'], W / 2, 1330, ebk((k - 1.0) / .35) * (1 + .03 * math.sin(t * 6)), 1 if k > 1.0 else 0)
    else:
        end_card(f, t - T_OUTRO - T_OUT, S)
    if t < T_INTRO or T_OUTRO <= t < T_OUTRO + T_OUT: blit(f, S['wm'], W - 130, 80, 1, .9)
    fl = sum(env(t, ST[i], .1) * .25 for i in range(N)) + env(t, ST[N - 1], .2) * .5 + env(t, T_OUTRO + T_OUT, .15) * .5
    f = np.clip(f + (255 - f) * fl, 0, 255)
    if t > TOTAL - .4: f = f * max(0, (TOTAL - t) / .4)
    return f.astype(np.uint8)
def cues(): return dict(total=TOTAL, intro=0, outro=T_OUTRO, end=T_OUTRO + T_OUT, starts=ST, rounds=[])
if __name__ == '__main__':
    json.dump(cues(), open('cues.json', 'w'))
    if sys.argv[2] == 'stills': stills(render, [float(x) for x in sys.argv[3:]]); print(TOTAL)
    else: encode(render, float(sys.argv[2]), float(sys.argv[3]), sys.argv[4])
