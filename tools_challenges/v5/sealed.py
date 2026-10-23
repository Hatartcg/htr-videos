"""HTR sealed-boxes weekly — CINEMATIC documentary / kinetic-typography style.
python3 sealed.py spec.json stills t.. | a b out.mp4      spec.timing.beats = durations of each voice beat"""
import sys, json, math, numpy as np, cv2
from PIL import Image
from common import *
SPEC = json.load(open(sys.argv[1])); B = SPEC['timing']['beats']; T_END = 2.6
BS = [sum(B[:i]) for i in range(len(B))]; T_MAIN = sum(B); TOTAL = T_MAIN + T_END
BOX = SPEC['boxes']
WARM = (255, 170, 90); COLD = (90, 170, 255); RED_ = (235, 40, 50); GREEN_ = (40, 210, 120)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1 - 1.25 * (((xx - W / 2) / W) ** 2 * 1.4 + ((yy - H / 2) / H) ** 2), 0, 1)[..., None]
rng = np.random.default_rng(4)
GRAIN = [rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
def bg(t, tint=COLD, glow_y=900, strength=1.0):
    f = np.zeros((H, W, 3), np.float32); f[:] = (10, 8, 8)
    g = np.exp(-(((xx - W / 2) / 520) ** 2 + ((yy - glow_y) / 640) ** 2))[..., None]
    f += g * np.array(tint[::-1], np.float32) * .55 * strength
    floor = np.clip((yy - 1300) / 500, 0, 1)[..., None]; f = f * (1 - floor * .5)
    # slow light leak
    lx = W * (.5 + .6 * math.sin(t * .23)); leak = np.exp(-(((xx - lx) / 300) ** 2 + ((yy - 200) / 500) ** 2))[..., None]
    f += leak * np.array(WARM[::-1], np.float32) * .25
    return f
def finish(f, t):
    gr = cv2.resize(GRAIN[int(t * 24) % 6], (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
    f = f * VIG + gr * 7
    f[:170] = 0; f[H - 170:] = 0          # letterbox
    return f
def cutout(path, w):
    im = Image.open(path).convert('RGBA'); im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    a = np.array(im); rgb = np.ascontiguousarray(a[..., :3]); m = np.zeros((rgb.shape[0] + 2, rgb.shape[1] + 2), np.uint8)
    for c in [(0, 0), (rgb.shape[1] - 1, 0), (0, rgb.shape[0] - 1), (rgb.shape[1] - 1, rgb.shape[0] - 1)]:
        if rgb[c[1], c[0]].min() > 225: cv2.floodFill(rgb, m, c, (0, 0, 0), (14, 14, 14), (14, 14, 14), cv2.FLOODFILL_MASK_ONLY | (255 << 8) | 8)
    bgm = m[1:-1, 1:-1] > 0
    fg = (~bgm).astype(np.uint8)
    if bgm.mean() > .01:
        cs, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cs = [c for c in cs if cv2.contourArea(c) > fg.size * .002]
        hull = cv2.convexHull(np.vstack(cs)); solid = np.zeros_like(fg); cv2.fillPoly(solid, [hull], 1)
        a[..., 3] = np.where(solid > 0, a[..., 3], 0)
    a[..., 3] = cv2.GaussianBlur(a[..., 3], (3, 3), 0)
    return to_bgra(Image.fromarray(a))
BIMG = [cutout(b['img'], 720) for b in BOX]
def yaw(spr, ang):
    h, w = spr.shape[:2]; c = math.cos(ang); s = math.sin(ang)
    ww = max(4, int(w * abs(c))); k = .12 * s
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    pad = int(h * .15)
    dst = np.float32([[0, pad - h * k], [ww, pad + h * k], [ww, pad + h - h * k], [0, pad + h + h * k]])
    M = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(spr, M, (ww, h + 2 * pad), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
def hero(f, k, x, y, ang, sc=1.0, alpha=1.0, rim=COLD):
    spr = yaw(BIMG[k], ang)
    # rim glow behind
    a = spr[..., 3].astype(np.float32) / 255; gl = cv2.GaussianBlur(a, (0, 0), 28)
    g = np.zeros_like(spr); g[..., :3] = np.array(rim[::-1], np.uint8); g[..., 3] = np.clip(gl * 255 * .9, 0, 255).astype(np.uint8)
    blit(f, g, x, y, sc * 1.05, alpha)
    blit(f, spr, x, y, sc, alpha)
    # reflection
    ref = spr[::-1].copy(); ref[..., 3] = (ref[..., 3].astype(np.float32) * np.linspace(.35, 0, ref.shape[0])[:, None]).astype(np.uint8)
    blit(f, ref, x, y + spr.shape[0] * sc * .98, sc, alpha * .8)
S = end_assets(SPEC.get('tease', 'بكرة تحدي جديد'))
def T_(s, size, col=WHITE, glow=None, stroke=0): return txt(s, FL(size), col, stroke=stroke, glow=glow, gr=24)
K = {k: T_(*v) if isinstance(v, list) else v for k, v in {}.items()}
CAP = [T_(c, 78, WHITE, None, 4) if c else None for c in SPEC['captions']]
BIGW = {k: txt(v[0], FL(v[1]), WHITE, stroke=8, glow=tuple(v[2]) if v[2] else None, gr=30) for k, v in SPEC['words'].items()}
NAMES = [fit_txt(b['name'], FB, 64, 900, fill=WHITE, stroke=3) for b in BOX]; GAMES = [pill(b['game'], FB(38), (20, 16, 18), fg=WHITE, border=(200, 200, 210)) for b in BOX]
def year_spr(y): return txt(str(y), FB(230), WHITE, stroke=8, glow=WARM, gr=30)
_pc = {}
def price_spr(v):
    k = int(round(v))
    if k not in _pc: _pc[k] = txt(f'${k:,}', FB(170), WHITE, stroke=8, glow=GREEN_, gr=30)
    return _pc[k]
SRC = txt(SPEC['source'], FL(32), (170, 160, 150))
BILL = None
def bill():
    im = np.zeros((70, 150, 4), np.uint8); cv2.rectangle(im, (0, 0), (149, 69), (60, 140, 70, 255), -1); cv2.rectangle(im, (6, 6), (143, 63), (120, 210, 140, 255), 3)
    cv2.circle(im, (75, 35), 20, (120, 210, 140, 255), 3); cv2.putText(im, '$', (64, 47), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (200, 255, 210, 255), 3, cv2.LINE_AA); return im
BILL = bill(); MONEY = [(rng.uniform(0, W), rng.uniform(-900, 0), rng.uniform(250, 520), rng.uniform(0, 6.28)) for _ in range(46)]
def money(f, k, amt=1.0):
    for j, (x, y, v, ph) in enumerate(MONEY):
        if j > len(MONEY) * amt: break
        yy_ = y + v * k; xx_ = x + 60 * math.sin(k * 2 + ph)
        if -80 < yy_ < H + 80: blit(f, BILL, xx_, yy_, .9, .9, 40 * math.sin(k * 3 + ph))
def hazard(f, y, h, k):
    band = np.zeros((h, W + 200, 3), np.uint8); band[:] = (20, 20, 20)
    for x in range(-200, W + 400, 80): cv2.fillPoly(band, [np.array([[x, 0], [x + 40, 0], [x + 40 - h, h], [x - h, h]], np.int32)], RED_[::-1])
    off = int(k * 120) % 80; f[y:y + h] = band[:, off:off + W]
def beat(t):
    for i in range(len(B) - 1, -1, -1):
        if t >= BS[i]: return i, t - BS[i]
def caption(f, i, lt):
    c = CAP[i] if i < len(CAP) else None
    if c is not None: blit(f, c, W / 2, 1600, ebk(lt / .3, 1.2), min(1, lt / .15) * (1 - max(0, (lt - B[i] + .15) / .15)))
def render(t):
    if t >= T_MAIN:
        f = np.zeros((H, W, 3), np.float32); f[:] = (10, 8, 8); end_card(f, t - T_MAIN, S); return np.clip(f * (max(0, (TOTAL - t) / .4) if t > TOTAL - .4 else 1), 0, 255).astype(np.uint8)
    i, lt = beat(t); D = B[i]; p = lt / D
    beat_kind = SPEC['beats'][i]
    if beat_kind == 'lineup':
        f = bg(t, WARM, 900, .5)
        for j in range(len(BOX)):
            on = lt > .3 + j * .45
            x = W / 2 + (j - (len(BOX) - 1) / 2) * 330
            spr = BIMG[j] if on else (BIMG[j] * np.array([.12, .12, .12, 1])).astype(np.uint8)
            blit(f, spr, x, 900, .42 * (1 + .03 * p), 1)
            if on: blit(f, BIGW['flash'], x, 900, 0, 0)
        blit(f, BIGW['hook'], W / 2, 420, ebk((lt - .2) / .4), 1 if lt > .2 else 0)
    elif beat_kind.startswith('intro'):
        k = int(beat_kind[-1]); f = bg(t, COLD if k == 0 else WARM, 820)
        hero(f, k, W / 2, 820, -.5 + .7 * p, .95 + .08 * p)
        blit(f, GAMES[k], W / 2, 300, ebk(lt / .3), 1); blit(f, NAMES[k], W / 2, 390, ebk((lt - .1) / .3), 1)
        y0 = BOX[k]['year']; blit(f, year_spr(y0), W / 2, 1420, ebk((lt - .6) / .35), 1 if lt > .6 else 0)
    elif beat_kind.startswith('price'):
        k = int(beat_kind[-1]); f = bg(t, GREEN_, 820, .9)
        money(f, lt, .6 + .4 * k)
        hero(f, k, W / 2, 780, .2 + .25 * p, 1.0 - .05 * p, rim=GREEN_)
        y0 = BOX[k]['year']; y1 = SPEC['now_year']; yr = int(y0 + (y1 - y0) * eo(min(1, lt / .8)))
        blit(f, year_spr(yr), W / 2, 330, .8, 1)
        v = BOX[k]['price'] * eo(min(1, max(0, lt - .3) / 1.3))
        blit(f, price_spr(v), W / 2, 1420, 1 + .08 * env(lt, 1.6, .3), 1 if lt > .3 else 0)
        blit(f, SRC, W / 2, 1695, 1, 1 if lt > .5 else 0)
    elif beat_kind == 'supply':
        f = bg(t, COLD, 950, .6)
        n0 = 12; gone = int(min(n0 - 2, lt / (D * .8) * (n0 - 2)))
        for j in range(n0):
            r_, c_ = divmod(j, 4); x = W / 2 + (c_ - 1.5) * 200; y = 1180 - r_ * 175
            if j < n0 - gone: blit(f, BIMG[0], x, y, .24, 1)
            elif j == n0 - gone and lt % 1 < .3: pass
        blit(f, BIGW['supply'], W / 2, 400, ebk(lt / .35), 1)
        blit(f, txt(f'{n0 - gone}', FB(150), WHITE, stroke=6, glow=RED_), W / 2, 1440, 1 + .1 * env(lt % (D * .8 / (n0 - 2) + 1e-6), 0, .2), 1)
    elif beat_kind == 'invest':
        f = bg(t, GREEN_, 900, .7)
        pts = []; n = 30
        for j in range(int(n * min(1, lt / (D * .7))) + 1):
            x = 140 + j * (800 / n); y = 1300 - (j / n) ** 1.6 * 700 - 40 * math.sin(j * 1.3); pts.append((x, y))
        if len(pts) > 1: cv2.polylines(f, [np.array(pts, np.int32)], False, GREEN_[::-1], 12, cv2.LINE_AA); cv2.circle(f, tuple(np.int32(pts[-1])), 22, (255, 255, 255), -1, cv2.LINE_AA)
        blit(f, BIGW['invest'], W / 2, 420, ebk((lt - .2) / .35), 1 if lt > .2 else 0)
    elif beat_kind == 'warn':
        f = bg(t, RED_, 900, .7)
        hero(f, 1, W / 2, 900, .15 * math.sin(lt * 2), .9, rim=RED_)
        hazard(f, 300, 70, lt); hazard(f, 1450, 70, lt + .5)
        blit(f, BIGW['dont'], W / 2, 900, ebk((lt - .4) / .25) * (1 + .03 * math.sin(lt * 20)), 1 if lt > .4 else 0, -8)
    elif beat_kind == 'choice':
        f = bg(t, COLD, 900, .5)
        cv2.rectangle(f, (0, 170), (W // 2, H - 170), (30, 40, 120), -1); cv2.rectangle(f, (W // 2, 170), (W, H - 170), (40, 90, 40), -1)
        f[:] = f * .6 + bg(t, COLD, 900, .5) * .4
        cv2.line(f, (W // 2, 170), (W // 2, H - 170), (255, 255, 255), 6)
        blit(f, BIGW['open'], W * .75, 760, ebk(lt / .3), 1); blit(f, BIGW['keep'], W * .25, 760, ebk((lt - .5) / .3), 1 if lt > .5 else 0)
        blit(f, BIGW['vs'], W / 2, 760, ebk((lt - .3) / .3), 1 if lt > .3 else 0)
        blit(f, BIMG[0], W * .75, 1180, .3, 1, -6); blit(f, BIMG[1], W * .25, 1180, .3, 1, 6)
    elif beat_kind == 'cta':
        f = bg(t, WARM, 900, .7)
        blit(f, BIGW['cmt'], W / 2, 800, ebk(lt / .35) * (1 + .03 * math.sin(lt * 6)), 1)
        blit(f, S['ig'], W / 2, 1050, ebk((lt - .4) / .35), 1 if lt > .4 else 0)
    else:
        f = bg(t)
    caption(f, i, lt)
    if t < T_MAIN: blit(f, S['wm'], W - 120, 240, .7, .85)
    fl = sum(env(t, BS[j], .12) * .35 for j in range(1, len(B)))
    f = f + (255 - f) * fl
    f = finish(f, t)
    return np.clip(f, 0, 255).astype(np.uint8)
def voice_offsets(): return [BS[i] + .12 for i in range(len(B))]
def cues():
    ev = [('braam', BS[i]) if SPEC['beats'][i].startswith(('intro', 'warn')) else ('hit', BS[i]) for i in range(len(B))]
    ev += [('cash', BS[i] + 1.6) for i in range(len(B)) if SPEC['beats'][i].startswith('price')]
    return dict(total=TOTAL, intro=0, outro=T_MAIN, end=T_MAIN, events=ev, offs=voice_offsets())
if __name__ == '__main__':
    json.dump(cues(), open('cues.json', 'w'))
    if sys.argv[2] == 'stills': stills(render, [float(x) for x in sys.argv[3:]]); print(TOTAL)
    elif sys.argv[2] == 'cues': print(TOTAL)
    else: encode(render, float(sys.argv[2]), float(sys.argv[3]), sys.argv[4])
