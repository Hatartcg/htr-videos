"""HTR «أغلى ١٠» — ELEVATOR ride to the top floor.  python3 elevator.py spec.json stills t.. | a b out.mp4"""
import sys, json, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
from common import *
SPEC = json.load(open(sys.argv[1])); TM = SPEC['timing']; CARDS = SPEC['cards']   # #10 .. #1
N = len(CARDS); T_INTRO = TM['intro']; DUR = TM['dur']; T_OUT = TM['outro']; T_END = 2.6
ST = [T_INTRO + sum(DUR[:i]) for i in range(N)]; T_OUTRO = T_INTRO + sum(DUR); TOTAL = T_OUTRO + T_OUT + T_END
RIDE = .75; OPEN = .45
LED = (255, 50, 60); STEEL = (170, 178, 192); CYAN = (90, 230, 255)
# --- static wall: brushed dark steel with panels/rivets
rng = np.random.default_rng(2)
WALL = np.zeros((H * 2, W, 3), np.float32)
nz = rng.normal(0, 1, (H * 2, W)).astype(np.float32); nz = cv2.GaussianBlur(nz, (0, 0), sigmaX=0.6, sigmaY=40)
WALL[:] = 38; WALL += nz[..., None] * 6
for y in range(0, H * 2, 320):
    cv2.line(WALL, (0, y), (W, y), (22, 22, 26), 6)
    for x in range(30, W, 120): cv2.circle(WALL, (x, y + 22), 5, (70, 72, 80), -1, cv2.LINE_AA); cv2.circle(WALL, (x, y - 22), 5, (70, 72, 80), -1, cv2.LINE_AA)
WALL[..., 0] += 6   # slight blue cast (BGR)
DX0, DX1, DY0, DY1 = 150, 930, 470, 1500      # door opening
def door_tex(w, h, flip):
    a = np.zeros((h, w, 3), np.float32); g = np.linspace(0, 1, w)[None, :]
    a[:] = (120 + 70 * (g if flip else 1 - g))[..., None]
    a += cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), sigmaX=.5, sigmaY=30)[..., None] * 10
    a[..., 0] += 10
    cv2.rectangle(a, (0, 0), (w - 1, h - 1), (60, 60, 70), 6)
    cv2.line(a, (8 if flip else w - 9, 0), (8 if flip else w - 9, h), (230, 230, 240), 2)
    return np.clip(a, 0, 255)
DW = (DX1 - DX0) // 2; DH = DY1 - DY0
DL = door_tex(DW, DH, False); DR = door_tex(DW, DH, True)
CW = 470
def fitimg(path, w, h):
    im0 = Image.open(path); ww = int(min(w, h * im0.width / im0.height)); return card_img(path, ww)
SPR = [dict(n=card_spr(fitimg(c['img'], 560, 780), CYAN, .55), g=card_spr(fitimg(c['img'], 560, 780), (255, 255, 255), .95), s=card_spr(fitimg(c['img'], 150, 210))) for c in CARDS]
S = end_assets(SPEC.get('tease', 'بكرة تحدي جديد'))
S.update(t1=txt('أغلى ١٠ كروت في', FL(92), WHITE), t2=fit_txt(SPEC['set_title'], FB, 96, 960, fill=WHITE, glow=CYAN), game=pill(SPEC['game'], FB(40), (20, 22, 30), fg=CYAN, border=CYAN),
         ride=txt('اطلع معي للدور الأخير!', FL(70), WHITE, glow=LED), floor=txt('الدور', FL(46), (200, 200, 210)), src=txt(SPEC['source'], FL(34), (160, 165, 180)),
         ph=txt('PENTHOUSE', FB(52), WHITE, glow=CYAN, gr=24), q=txt('عندك واحد منهم؟', FL(110), WHITE, glow=CYAN), cmt=pill('قول لنا بالتعليقات', FL(60), (200, 40, 60), padx=56))
NAME = [fit_txt(c['name'], FB, 50, 900, fill=WHITE, stroke=3) for c in CARDS]; RAR = [fit_txt(c['rarity'], FL, 40, 900, fill=(190, 195, 210)) for c in CARDS]
PRICE = [txt(f"${int(round(c['price'])):,}", FB(120 if i == N - 1 else 100), WHITE, stroke=6, glow=(CYAN if i == N - 1 else LED), gr=22) for i, c in enumerate(CARDS)]
# 7-segment floor display
SEG = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgedc', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg', 'L': 'fed'}
def seg_digit(f, ch, x, y, s, col, dim=(45, 18, 22)):
    w, h, th = 60 * s, 110 * s, 13 * s
    P = dict(a=((x, y), (x + w, y)), b=((x + w, y), (x + w, y + h / 2)), c=((x + w, y + h / 2), (x + w, y + h)), d=((x, y + h), (x + w, y + h)),
             e=((x, y + h / 2), (x, y + h)), f=((x, y), (x, y + h / 2)), g=((x, y + h / 2), (x + w, y + h / 2)))
    on = SEG.get(ch, '')
    for k, (p, q) in P.items():
        c = col if k in on else dim
        cv2.line(f, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), c[::-1], int(th), cv2.LINE_AA)
def floor_panel(f, s, glowk=0.0, arrow=0.0):
    cx, cy = W / 2, 250
    cv2.rectangle(f, (int(cx - 210), int(cy - 110)), (int(cx + 210), int(cy + 110)), (12, 10, 12), -1)
    cv2.rectangle(f, (int(cx - 210), int(cy - 110)), (int(cx + 210), int(cy + 110)), STEEL[::-1], 5)
    s = str(s); col = LED
    sc = .85; step = 100 * sc; xs = cx - (len(s) * step - 20 * sc) / 2
    for i, ch in enumerate(s): seg_digit(f, ch, xs + i * step, cy - 55 * sc, sc, col)
    # up arrow
    a = .4 + .6 * arrow
    pts = np.array([[cx + 130, cy + 30], [cx + 170, cy + 30], [cx + 150, cy - 20]], np.int32)
    cv2.fillPoly(f, [pts], tuple(int(v * a) for v in LED[::-1]))
    pts2 = np.array([[cx - 130, cy + 30], [cx - 170, cy + 30], [cx - 150, cy - 20]], np.int32)
    cv2.fillPoly(f, [pts2], tuple(int(v * a) for v in LED[::-1]))
def at(t):
    for i in range(N - 1, -1, -1):
        if t >= ST[i]: return i, t - ST[i]
def scene(f, t, scroll, door_o, inner=None, inner_sc=1.0, light=0.0):
    y0 = int(scroll) % H
    f[:] = WALL[y0:y0 + H]
    if scroll % 1 and False: pass
    # motion blur look while riding
    # opening interior
    cv2.rectangle(f, (DX0, DY0), (DX1, DY1), (8 + 60 * light, 8 + 60 * light, 12 + 60 * light), -1)
    if inner is not None:
        sub = f[DY0:DY1, DX0:DX1]
        g = np.exp(-(((np.arange(DX1 - DX0)[None, :] - (DX1 - DX0) / 2) / 380) ** 2 + ((np.arange(DY1 - DY0)[:, None] - 380) / 600) ** 2))[..., None]
        sub += g * np.array(CYAN[::-1], np.float32) * (.25 + .5 * light)
        tmp = f.copy(); blit(tmp, inner, W / 2, (DY0 + DY1) / 2, inner_sc, 1)
        f[DY0:DY1, DX0:DX1] = tmp[DY0:DY1, DX0:DX1]
    o = int(DW * door_o)
    # left door slides left, right door slides right (clip to opening)
    lw = DW - o
    if lw > 0:
        f[DY0:DY1, DX0:DX0 + lw] = DL[:, o:]
        f[DY0:DY1, DX1 - lw:DX1] = DR[:, :lw]
    # frame
    cv2.rectangle(f, (DX0 - 22, DY0 - 22), (DX1 + 22, DY1 + 22), (95, 98, 110), 22)
    cv2.rectangle(f, (DX0 - 34, DY0 - 34), (DX1 + 34, DY1 + 34), (30, 30, 36), 6)
def render(t):
    f = np.zeros((H, W, 3), np.float32)
    if t < T_INTRO:
        k = t
        scene(f, t, 0, 0.0)
        floor_panel(f, 'L', 0, .5 + .5 * math.sin(t * 6))
        o = eo((t - T_INTRO + .4) / .4)
        blit(f, S['t1'], W / 2, 650, ebk(k / .4), 1 - o); blit(f, S['t2'], W / 2, 790, ebk((k - .2) / .4), (k > .2) * (1 - o))
        blit(f, S['game'], W / 2, 920, ebk((k - .35) / .35), (k > .35) * (1 - o))
        blit(f, S['ride'], W / 2, 1250, ebk((k - .9) / .35), (k > .9) * (1 - o))
        blit(f, S['src'], W / 2, 1700, 1, 1 - o)
    elif t < T_OUTRO:
        i, lt = at(t); D = DUR[i]
        ride = min(1, lt / RIDE); scroll = (i + ride) * 640 + (t - ST[i]) * 0
        if lt < RIDE:   # doors closed, riding up
            scene(f, t, scroll * 1.0 + ride * 900, 0.0)
            # vertical motion streaks
            k = math.sin(math.pi * ride)
            if k > .05: f[:] = cv2.blur(f, (1, int(1 + 60 * k)))
            floor_panel(f, str(i + 1) if ride > .6 else (str(i) if i > 0 else 'L'), 0, 1)
        else:
            lo = lt - RIDE; door = eo(lo / OPEN); last = i == N - 1
            sp = SPR[i]['g'] if last and lo > .4 else SPR[i]['n']
            scene(f, t, (i + 1) * 640 + 900, door, sp, 1 + .02 * math.sin(t * 2.5), light=(1 if last else 0) * min(1, lo / .5))
            floor_panel(f, str(i + 1), 0, 0)
            if last: blit(f, S['ph'], W / 2, 400, ebk((lo - .2) / .3), 1 if lo > .2 else 0)
            # price + name plates
            k = ebk((lo - .25) / .35)
            blit(f, PRICE[i], W / 2, 1610, k * (1 + .08 * env(lo, .25, .25)), 1 if lo > .25 else 0)
            blit(f, NAME[i], W / 2, 1730, 1, eo((lo - .3) / .3)); blit(f, RAR[i], W / 2, 1795, 1, eo((lo - .35) / .3))
            out = eo((lt - D + .25) / .25)
            if out > 0: f[:] = f * (1 - .5 * out)
        blit(f, txt(f'#{N - i}', FB(64), WHITE, stroke=5, glow=LED), 130, 250, 1, 1)
    elif t < T_OUTRO + T_OUT:
        k = t - T_OUTRO
        scene(f, t, N * 640 + 900, 1.0, None, 1, light=1)
        blit(f, S['q'], W / 2, 260, ebk(k / .4), 1)
        for j in range(N):
            r_, cc = divmod(j, 5); kk = ebk((k - .2 - j * .06) / .35)
            blit(f, SPR[N - 1 - j]['s'], W / 2 + (cc - 2) * 165, 760 + r_ * 270, kk, 1 if kk > 0 else 0)
        blit(f, S['cmt'], W / 2, 1300, ebk((k - 1.0) / .35) * (1 + .03 * math.sin(t * 6)), 1 if k > 1.0 else 0)
    else:
        f[:] = (14, 10, 12); end_card(f, t - T_OUTRO - T_OUT, S)
    if t < T_INTRO or T_OUTRO <= t < T_OUTRO + T_OUT: blit(f, S['wm'], W - 120, 70, .8, .9)
    fl = env(t, ST[N - 1] + RIDE + .1, .35) * .8 if N else 0
    f = f + (255 - f) * fl
    if t > TOTAL - .4: f = f * max(0, (TOTAL - t) / .4)
    return np.clip(f, 0, 255).astype(np.uint8)
def voice_offsets():
    return [.3] + [ST[i] + RIDE + .1 for i in range(N)] + [T_OUTRO + .2]
def cues():
    ev = []
    for i in range(N): ev += [('ride', ST[i]), ('ding', ST[i] + RIDE - .05), ('doors', ST[i] + RIDE)]
    ev.append(('big', ST[N - 1] + RIDE + .1))
    return dict(total=TOTAL, intro=0, outro=T_OUTRO, end=T_OUTRO + T_OUT, events=ev, offs=voice_offsets())
if __name__ == '__main__':
    json.dump(cues(), open('cues.json', 'w'))
    if sys.argv[2] == 'stills': stills(render, [float(x) for x in sys.argv[3:]]); print(TOTAL)
    elif sys.argv[2] == 'cues': print(TOTAL)
    else: encode(render, float(sys.argv[2]), float(sys.argv[3]), sys.argv[4])
