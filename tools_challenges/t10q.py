"""HTR «أغلى ١٠ كروت في إصدار» — NO-REVEAL version (Nov 2026 owner rules).
#10..#2 shown with prices, #1 stays hidden (card back + ???) with a real 3-s countdown, CTA bar at the end.
python3 t10q.py spec.json cues | stills t.. | a b out.mp4
spec timing: intro, dur[0..8] (#10..#2), mystery (#1 incl. 3 s countdown), cta, end"""
import sys, json, math, numpy as np, cv2
from PIL import Image, ImageDraw
from common import *
SPEC = json.load(open(sys.argv[1])); TM = SPEC['timing']; CARDS = SPEC['cards']   # #10 .. #1 (last = hidden)
N = len(CARDS); T_INTRO = TM['intro']; DUR = TM['dur'] + [TM['mystery']]; T_CTA = TM['cta']; T_END = TM.get('end', 2.8)
ST = [T_INTRO + sum(DUR[:i]) for i in range(N)]; T_OUTRO = T_INTRO + sum(DUR); TOTAL = T_OUTRO + T_CTA + T_END
CD0 = ST[N - 1] + TM['mystery'] - 3.0          # countdown starts 3 s before #1 beat ends
bg = make_bg(cy=900)
CW = 560
SPR = []
for c in CARDS[:-1]:
    im = card_img(c['img'], CW); SPR.append(dict(n=card_spr(im, PURPLE, .6), s=card_spr(card_img(c['img'], 150))))
def back_img(w, q=True):
    h = int(w * 1.395); BK = Image.new('RGBA', (w, h), (0, 0, 0, 0)); bd = ImageDraw.Draw(BK)
    bd.rounded_rectangle((0, 0, w - 1, h - 1), int(w * .045), fill=(40, 30, 80, 255), outline=PURPLE + (255,), width=max(3, w // 70))
    for q_ in range(0, h + w, max(10, w // 11)): bd.line((q_ - h, 0, q_, h), fill=(58, 46, 106, 255), width=max(4, w // 35))
    if q:
        f = FB(int(w * .62)); bb = bd.textbbox((0, 0), '?', font=f)
        bd.text(((w - (bb[2] - bb[0])) / 2 - bb[0], (h - (bb[3] - bb[1])) / 2 - bb[1]), '?', font=f, fill=WHITE, stroke_width=max(2, w // 60), stroke_fill=(24, 18, 50))
    return BK
BACK = card_spr(back_img(CW), RED, .8); BACK_S = card_spr(back_img(150))
BACK_I = card_spr(back_img(500), PURPLE, .8)
S = end_assets(SPEC.get('tease', 'تابعنا عشان التحدي الجاي!'))
S.update(t1=txt('أغلى ١٠ كروت في', FL(96), WHITE), t2=fit_txt(SPEC['set_title'], FB, 88, 960, fill=PURPLE, glow=PURPLE), game=pill(SPEC['game'], FB(40), (24, 18, 50), fg=(160, 240, 230), border=TEAL),
         who=txt('رقم ١؟ أنت خمّن سعره!', FL(100), WHITE, glow=RED), hdr=pill('TOP 10 · ' + SPEC['set_short'], FB(34), (24, 18, 50), fg=LILAC, border=PURPLE),
         src=txt(SPEC['source'], FL(34), DIM), q=txt('كم سعر رقم ١؟', FL(110), WHITE, glow=PURPLE), cmt=pill('الجواب بأول تعليق 👇'.replace(' 👇', ''), FL(60), PURPLE, padx=56),
         guess=txt('خمّن سعره!', FL(120), WHITE, glow=RED), qp=txt('$ ? ? ?', FB(150), WHITE, stroke=8, glow=RED, gr=26),
         bar=pill('تابعنا • لايك • احفظ • علّق ولو بنقطة', FL(54), (24, 18, 50), fg=WHITE, border=TEAL, padx=44))
CNT = [txt(str(k), FB(330), WHITE, stroke=10, glow=RED, gr=30) for k in (1, 2, 3)]
RANK = [rrect(150, 96, 22, (PURPLE if i < N - 1 else RED) + (255,)) for i in range(N)]
RANKT = [txt(f'#{N - i}', FB(60), WHITE) for i in range(N)]
NAME = [fit_txt(c['name'], FB, 50, 900, fill=WHITE) for c in CARDS[:-1]] + [txt('???', FB(60), WHITE)]
RAR = [fit_txt(c['rarity'], FL, 40, 900, fill=LILAC) for c in CARDS[:-1]] + [txt('مين يكون؟', FL(44), LILAC)]
_digits = {}
def price_spr(v):
    s = f"${int(round(v)):,}"
    if s not in _digits:
        if len(_digits) > 400: _digits.clear()
        _digits[s] = txt(s, FB(130), WHITE, stroke=8, glow=PURPLE, gr=26)
    return _digits[s]
WMG = logo_spr(170, True)
def at(t):
    for i in range(N - 1, -1, -1):
        if t >= ST[i]: return i, t - ST[i]
def bar(f, t, y):
    blit(f, S['bar'], W / 2, y, 1 + .02 * math.sin(t * 5), 1)
def render(t):
    if t < T_INTRO:
        # HOOK: fully built from frame 0 and held STILL (calm 1-3 s); only a fast exit in the last .3 s
        out = eo((t - T_INTRO + .3) / .3)
        if t < TM.get('ib', 99):
            f = bg(0.0, 0, 16)
            blit(f, S['t1'], W / 2, 300 - 300 * out, 1, 1 - out); blit(f, S['t2'], W / 2, 420 - 300 * out, 1, 1 - out)
            blit(f, S['game'], W / 2, 530 - 300 * out, 1, 1 - out)
            blit(f, BACK, W / 2, 1010 + 900 * out, 1, 1)
            blit(f, S['who'], W / 2, 1560 + 500 * out, 1, 1 - out)
        else:   # hard cut: close-up on the mystery card (after the calm 1-3 s)
            k = t - TM['ib']; f = bg(t, .25, 20)
            blit(f, S['qp'], W / 2, 330 - 400 * out, 1 + .04 * math.sin(t * 6), 1 - out)
            blit(f, BACK, W / 2, 1000 + 900 * out, 1.22 + .02 * k, 1, 2 * math.sin(t * 3))
            blit(f, S['who'], W / 2, 1640 + 500 * out, 1, 1 - out)
    elif t < T_OUTRO:
        i, lt = at(t); D = DUR[i]; hid = i == N - 1
        f = bg(t, .25 if hid else 0, 20 if hid else 16)
        inn = eo(lt / .3); out = eo((lt - D + .2) / .2) if not hid else 0
        blit(f, S['hdr'], W / 2, 110, 1, 1)
        for j in range(N):
            col = GREEN if j < i else ((RED if hid else PURPLE) if j == i else (60, 52, 100)); cv2.circle(f, (int(W / 2 + (j - (N - 1) / 2) * 34), 180), 10 if j == i else 7, col[::-1], -1, cv2.LINE_AA)
        x = W / 2 + 1200 * (1 - inn) - 1200 * out
        if not hid:
            c = CARDS[i]; RT = min(1.2, D * .4); roll = min(1, lt / RT); v = c['price'] * (1 - (1 - roll) ** 3)
            blit(f, price_spr(v), W / 2, 320, 1 + .1 * env(lt, RT, .25), inn)
            blit(f, SPR[i]['n'], x, 900, 1 + .03 * math.sin(t * 2.5), 1, -4 * (1 - inn))
        else:
            sh = 6 * math.sin(t * 40) * (t >= CD0)
            blit(f, S['qp'], W / 2 + sh, 320, 1 + .04 * math.sin(t * 6), inn)
            blit(f, BACK, x + sh, 900, 1 + .03 * math.sin(t * 2.5), 1, -4 * (1 - inn))
        blit(f, RANK[i], x - 250, 470, ebk((lt - .1) / .3), 1); blit(f, RANKT[i], x - 250, 470, ebk((lt - .1) / .3), 1)
        blit(f, NAME[i], W / 2, 1360, 1, inn * (1 - out)); blit(f, RAR[i], W / 2, 1425, 1, inn * (1 - out))
        if hid and t >= CD0:
            k = int(t - CD0); ph = (t - CD0) - k
            blit(f, CNT[2 - min(k, 2)], W / 2, 900, 1.35 - .35 * eo(ph / .25), 1 - max(0, ph - .75) * 3)
            blit(f, S['guess'], W / 2, 1560, 1, 1)
        else:
            blit(f, S['src'], W / 2, 1700, 1, 1)
    elif t < T_OUTRO + T_CTA:
        k = t - T_OUTRO; f = bg(t, 0, 16)
        blit(f, S['q'], W / 2, 330, ebk(k / .3), 1)
        for j in range(N):
            r_, cc = divmod(j, 5); kk = ebk((k - .1 - j * .04) / .3)
            spr = BACK_S if j == 0 else SPR[N - 1 - j]['s']
            blit(f, spr, W / 2 + (cc - 2) * 190, 690 + r_ * 270, kk * (1.08 if j == 0 else 1), 1 if kk > 0 else 0)
        blit(f, S['cmt'], W / 2, 1300, ebk((k - .5) / .3) * (1 + .03 * math.sin(t * 6)), 1 if k > .5 else 0)
        bar(f, t, 1480)
        blit(f, S['src'], W / 2, 1700, 1, 1)
    else:
        f = bg(t, 0, 16); end_card(f, t - T_OUTRO - T_CTA, S); bar(f, t, 1330)
    if t < T_OUTRO + T_CTA: blit(f, WMG, W - 120, 215 if T_INTRO <= t < T_OUTRO else 80, .9, 1)
    fl = sum(env(t, ST[i], .1) * .25 for i in range(N)) + env(t, T_OUTRO, .12) * .4 + env(t, T_OUTRO + T_CTA, .15) * .5
    f = np.clip(f + (255 - f) * fl, 0, 255)
    if t > TOTAL - .4: f = f * max(0, (TOTAL - t) / .4)
    return f.astype(np.uint8)
def cues():
    ev = [['swipe', s] for s in ST] + [['tick', s + min(1.2, DUR[i] * .4)] for i, s in enumerate(ST[:-1])] + [['braam', ST[N - 1]], ['count', CD0], ['slam', T_OUTRO]]
    offs = [0.0] + [s + .15 for s in ST] + [T_OUTRO + .15]
    return dict(total=TOTAL, intro=0, outro=T_OUTRO, end=T_OUTRO + T_CTA, starts=ST, offs=offs, events=ev, rounds=[], countdown=CD0)
if __name__ == '__main__':
    json.dump(cues(), open('cues.json', 'w'))
    if sys.argv[2] == 'cues': print(TOTAL)
    elif sys.argv[2] == 'stills': stills(render, [float(x) for x in sys.argv[3:]], sys.argv[3] if False else 'st.jpg'); print(TOTAL)
    else: encode(render, float(sys.argv[2]), float(sys.argv[3]), sys.argv[4])
