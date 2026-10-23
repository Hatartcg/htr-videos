"""HTR «أكثر ٥ ارتفعوا» — STOCK-MARKET terminal / breaking-news style.  python3 market.py spec.json stills t.. | a b out.mp4"""
import sys, json, math, numpy as np, cv2
from PIL import Image
from common import *
SPEC = json.load(open(sys.argv[1])); TM = SPEC['timing']; M = SPEC['movers']   # ordered #5 .. #1
N = len(M); T_INTRO = TM['intro']; DUR = TM['dur']; T_OUT = TM['outro']; T_END = 2.6
ST = [T_INTRO + sum(DUR[:i]) for i in range(N)]; T_OUTRO = T_INTRO + sum(DUR); TOTAL = T_OUTRO + T_OUT + T_END
UP = (30, 230, 120); DN = (255, 60, 80); TERM = (8, 12, 10); GRID = (22, 40, 30); AMBER_FREE = (220, 230, 225)
# --- background: terminal black w/ grid + scanlines
BG = np.zeros((H, W, 3), np.float32); BG[:] = TERM[::-1]
for x in range(0, W, 60): cv2.line(BG, (x, 0), (x, H), GRID[::-1], 1)
for y in range(0, H, 60): cv2.line(BG, (0, y), (W, y), GRID[::-1], 1)
BG[::3] *= .85
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - .55 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 2.2)[..., None]
BG *= np.clip(VIG, .3, 1)
TAPE_ITEMS = SPEC.get('tape', [])
def tape_sprite():
    parts = []
    for sym, ch in TAPE_ITEMS:
        col = UP if ch >= 0 else DN; arrow = '▲' if ch >= 0 else '▼'
        parts.append((txt(f'{sym}', FB(34), (230, 235, 230)), txt(f'{"+" if ch >= 0 else ""}{ch:.1f}%', FB(34), col)))
    w = sum(a.shape[1] + b.shape[1] - 60 for a, b in parts) + 40 * len(parts)
    T = np.zeros((96, w * 2 + 400, 4), np.uint8); x = 0
    for rep in range(2):
        for a, b in parts:
            for spr in (a, b):
                h_, w_ = spr.shape[:2]; sp = spr[max(0, (h_ - 96) // 2):max(0, (h_ - 96) // 2) + 96]; hh = sp.shape[0]; y0 = (96 - hh) // 2
                T[y0:y0 + hh, x:x + w_] = np.maximum(T[y0:y0 + hh, x:x + w_], sp)
                x += w_ - 50
            x += 40
    return T, w
TAPE, TAPEW = tape_sprite()
CW = 400
def fitimg(path, w, h):
    im0 = Image.open(path); ww = int(min(w, h * im0.width / im0.height)); return card_img(path, ww)
SPR = [dict(n=card_spr(fitimg(m['img'], CW, 560), UP, .5), s=card_spr(fitimg(m['img'], 150, 210))) for m in M]
S = end_assets(SPEC.get('tease', 'بكرة تحدي جديد'))
S.update(brk=pill('عاجل', FL(64), DN, padx=40, pady=10), live=pill('● LIVE', FB(30), (40, 10, 14), fg=DN, border=DN, padx=20, pady=6),
         h1=txt('أكثر ٥ كروت', FL(120), WHITE), h2=txt('ارتفعت هالأسبوع', FL(110), UP, glow=UP), hdr=txt('بورصة الكروت', FL(46), (200, 215, 205)),
         src=txt(SPEC['source'], FL(32), (130, 160, 140)), was=txt('قبل أسبوع', FL(40), (150, 165, 155)), now=txt('اليوم', FL(44), UP),
         q=txt('عندك واحد منهم؟', FL(110), WHITE, glow=UP), cmt=pill('قول لنا بالتعليقات', FL(60), (20, 120, 70), padx=56),
         top=pill('الأعلى ارتفاعاً هالأسبوع', FL(50), UP, fg=(5, 20, 10), padx=36), demo=txt(SPEC.get('demo', ''), FL(40), (255, 255, 255)) if SPEC.get('demo') else None)
TICK = [txt('$' + m['ticker'], FB(64), WHITE, stroke=3) for m in M]
NAME = [fit_txt(m['name'], FB, 46, 960, fill=WHITE, stroke=3) for m in M]; SUB = [fit_txt(m['set'], FL, 38, 960, fill=(160, 190, 170)) for m in M]
OLD = [txt(f"${m['old']:,.0f}", FB(60), (150, 150, 150)) for m in M]; NEW = [txt(f"${m['new']:,.0f}", FB(84), UP, stroke=4, glow=UP, gr=16) for m in M]
RK = [pill(f'#{N - i}', FB(52), (20, 60, 40), fg=WHITE, border=UP, padx=26, pady=8) for i in range(N)]
_pct = {}
def pct_spr(v, big):
    k = (int(v), big)
    if k not in _pct: _pct[k] = txt(f'+{int(v)}%', FB(190 if big else 170), UP, stroke=8, glow=UP, gr=28)
    return _pct[k]
def series(m):
    s = m.get('series')
    if s: return s
    rng = np.random.default_rng(int(m['new'] * 100) % 9999); n = 8; a = np.linspace(m['old'], m['new'], n)
    a[1:-1] += rng.normal(0, (m['new'] - m['old']) * .25, n - 2); a[0] = m['old']; a[-1] = m['new']; return list(a)
SER = [series(m) for m in M]
def chart(f, ser, prog, x0=70, y0=430, x1=1010, y1=780):
    cv2.rectangle(f, (x0, y0), (x1, y1), (14, 26, 18), -1); cv2.rectangle(f, (x0, y0), (x1, y1), (40, 80, 55), 2)
    for k in range(1, 4): y = y0 + (y1 - y0) * k / 4; cv2.line(f, (x0, int(y)), (x1, int(y)), (30, 55, 38), 1)
    lo, hi = min(ser), max(ser); pad = (hi - lo) * .2 + 1e-6; lo -= pad; hi += pad
    n = len(ser); pts = [(x0 + 30 + (x1 - x0 - 60) * i / (n - 1), y1 - 20 - (y1 - y0 - 40) * (v - lo) / (hi - lo)) for i, v in enumerate(ser)]
    upto = prog * (n - 1); poly = []
    for i in range(n - 1):
        if i > upto: break
        a, b = pts[i], pts[i + 1]; tt_ = min(1, upto - i); poly += [a, (a[0] + (b[0] - a[0]) * tt_, a[1] + (b[1] - a[1]) * tt_)]
    if len(poly) >= 2:
        P = np.array(poly, np.int32)
        fill = np.vstack([P, [[P[-1][0], y1], [P[0][0], y1]]])
        ov = f.copy(); cv2.fillPoly(ov, [fill], (60, 140, 80)); f[:] = f * .75 + ov * .25
        cv2.polylines(f, [P], False, UP[::-1], 7, cv2.LINE_AA)
        cv2.circle(f, tuple(P[-1]), 13, (255, 255, 255), -1, cv2.LINE_AA); cv2.circle(f, tuple(P[-1]), 24, UP[::-1], 3, cv2.LINE_AA)
    blit(f, txt('7 أيام', FL(30), (120, 150, 130)), x0 + 70, y0 + 30, 1, 1)
def frame_chrome(f, t):
    cv2.rectangle(f, (0, 0), (W, 96), (6, 10, 8), -1); cv2.line(f, (0, 96), (W, 96), (40, 80, 55), 2)
    off = int(t * 160) % TAPEW
    blit(f, TAPE[:, off:off + W + 200], W / 2 + 100, 48, 1, 1)
    cv2.rectangle(f, (0, 1820), (W, H), (6, 10, 8), -1)
    blit(f, S['hdr'], W - 170, 1866, 1, 1); blit(f, S['live'], 120, 1866, 1, .6 + .4 * (math.sin(t * 5) > 0))
def at(t):
    for i in range(N - 1, -1, -1):
        if t >= ST[i]: return i, t - ST[i]
def render(t):
    f = BG.copy()
    if t < T_INTRO:
        k = t; out = eo((t - T_INTRO + .3) / .3)
        x = -600 + 1600 * eo(k / .35)
        blit(f, S['brk'], W / 2, 330 - 400 * out, ebk(k / .3) * (1 + .06 * (math.sin(t * 12) > 0)), 1 - out)
        blit(f, S['h1'], W / 2, 520 - 400 * out, ebk((k - .2) / .35), (k > .2) * (1 - out)); blit(f, S['h2'], W / 2, 680 - 400 * out, ebk((k - .4) / .35), (k > .4) * (1 - out))
        # candles
        rng = np.random.default_rng(1); base = 1500; v = 0
        for j in range(14):
            kk = eo((k - .6 - j * .06) / .25)
            if kk <= 0: break
            o_ = v; v += rng.normal(18, 22); hi = max(o_, v) + 15; lo_ = min(o_, v) - 15; xj = 110 + j * 66; col = (UP if v >= o_ else DN)[::-1]
            sc = kk
            cv2.line(f, (xj, int(base - hi * sc)), (xj, int(base - lo_ * sc)), col, 3)
            cv2.rectangle(f, (xj - 18, int(base - max(o_, v) * sc)), (xj + 18, int(base - min(o_, v) * sc)), col, -1)
        if out > 0: f[:] = f * (1 - out * .6)
    elif t < T_OUTRO:
        i, lt = at(t); m = M[i]; D = DUR[i]; inn = eo(lt / .3); out = eo((lt - D + .25) / .25); last = i == N - 1
        blit(f, RK[i], 120, 175, ebk(lt / .3), 1 - out)
        for j in range(N):
            col = UP if j < i else ((255, 255, 255) if j == i else (50, 70, 60)); cv2.circle(f, (int(W / 2 + (j - (N - 1) / 2) * 34), 175), 10 if j == i else 7, col[::-1], -1, cv2.LINE_AA)
        roll = eo(min(1, lt / min(2.0, D * .5)))
        blit(f, pct_spr(m['pct'] * roll, last), W / 2, 315, (1 + .1 * env(lt, min(2.0, D * .5), .3)) * inn, 1 - out)
        chart(f, SER[i], min(1, lt / min(2.0, D * .5)))
        x = 300 - 700 * (1 - inn) - 700 * out
        blit(f, SPR[i]['n'], x, 1150, 1 + .02 * math.sin(t * 2), 1)
        cx = 770 + 600 * (1 - inn) + 600 * out
        blit(f, TICK[i], cx, 920, 1, 1)
        a = eo((lt - .5) / .4)
        blit(f, S['now'], cx, 1010, 1, a); blit(f, NEW[i], cx, 1085, ebk((lt - .7) / .35), 1 if lt > .7 else 0)
        cv2.arrowedLine(f, (int(cx), 1240), (int(cx), int(1240 - 85 * a)), UP[::-1], 8, cv2.LINE_AA, tipLength=.4)
        blit(f, S['was'], cx, 1285, 1, 1); blit(f, OLD[i], cx, 1350, 1, 1)
        cv2.line(f, (int(cx - 90), 1354), (int(cx + 90), 1346), (150, 150, 150), 5, cv2.LINE_AA)
        blit(f, NAME[i], W / 2, 1530, 1, inn * (1 - out)); blit(f, SUB[i], W / 2, 1590, 1, inn * (1 - out))
        if last: blit(f, S['top'], W / 2, 1670, ebk((lt - 1.0) / .35), (lt > 1.0) * (1 - out))
        blit(f, S['src'], W / 2, 1765, 1, 1 - out)
    elif t < T_OUTRO + T_OUT:
        k = t - T_OUTRO
        blit(f, S['q'], W / 2, 420, ebk(k / .4), 1)
        for j in range(N):
            kk = ebk((k - .2 - j * .08) / .35); blit(f, SPR[N - 1 - j]['s'], W / 2 + (j - 2) * 190, 760, kk, 1 if kk > 0 else 0)
            blit(f, txt(f"+{M[N - 1 - j]['pct']}%", FB(40), UP), W / 2 + (j - 2) * 190, 920, kk, 1 if kk > 0 else 0)
        blit(f, S['cmt'], W / 2, 1160, ebk((k - 1.0) / .35) * (1 + .03 * math.sin(t * 6)), 1 if k > 1.0 else 0)
    else:
        f[:] = TERM[::-1]; end_card(f, t - T_OUTRO - T_OUT, S)
    if t < T_OUTRO + T_OUT:
        frame_chrome(f, t)
        blit(f, S['wm'], W / 2, 175 if t < T_INTRO or t >= T_OUTRO else 1866, .7, .9)
    if S['demo'] is not None:
        cv2.rectangle(f, (0, 1795), (W, 1820), (0, 0, 160), -1)
        blit(f, S['demo'], W / 2, 1808, .6, 1)
    fl = sum(env(t, ST[i], .08) * .2 for i in range(N)) + env(t, ST[N - 1] + min(2.0, DUR[N - 1] * .5), .25) * .5
    f = f + (255 - f) * fl
    if t > TOTAL - .4: f = f * max(0, (TOTAL - t) / .4)
    return np.clip(f, 0, 255).astype(np.uint8)
def voice_offsets(): return [.25] + [ST[i] + .15 for i in range(N)] + [T_OUTRO + .2]
def cues():
    ev = [('news', 0.0)]
    for i in range(N): ev += [('swipe', ST[i]), ('tick', ST[i] + min(2.0, DUR[i] * .5))]
    ev.append(('bell', ST[N - 1] + min(2.0, DUR[N - 1] * .5)))
    return dict(total=TOTAL, intro=0, outro=T_OUTRO, end=T_OUTRO + T_OUT, events=ev, offs=voice_offsets())
if __name__ == '__main__':
    json.dump(cues(), open('cues.json', 'w'))
    if sys.argv[2] == 'stills': stills(render, [float(x) for x in sys.argv[3:]]); print(TOTAL)
    elif sys.argv[2] == 'cues': print(TOTAL)
    else: encode(render, float(sys.argv[2]), float(sys.argv[3]), sys.argv[4])
