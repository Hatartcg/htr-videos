"""ticker_vs.py — HTR «قفزات الأسبوع» weekly price-jump versus reel.
Template: clean stock-app / price-ticker look (off-white paper, navy type, mint ▲ / coral accents, live line charts,
rolling slot-digits for the hidden price). New for HTR on 23 Nov 2026 — differs from the dark 3D/motion templates.
python3 ticker_vs.py spec.json out.mp4 [--subs en]"""
import sys, json, math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
FD = '/home/claude/fonts/'
def F(name, s): return ImageFont.truetype(FD + name, s)
AR = lambda s: F('font_lalezar.ttf', s)
NUM = lambda s: F('font_anton.ttf', s)
TXT = lambda s: F('font_cairo.ttf', s)
PAPER, INK, MUTED, MINT, CORAL, GRID = (244, 246, 251), (14, 22, 48), (110, 120, 145), (22, 190, 140), (255, 84, 104), (222, 227, 238)
spec = json.load(open(sys.argv[1])); OUT = sys.argv[2]; SUBS = '--subs' in sys.argv
D = spec['dur']; NF = int(D * FPS)
def eo(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ebk(x, s=1.7): x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def tsize(d, s, f): b = d.textbbox((0, 0), s, font=f); return b[2] - b[0], b[3] - b[1], b
DARK = False
def text_img(s, f, fill=INK, stroke=0, sfill=None, pad=12):
    if DARK and tuple(fill) == INK: fill = (255, 255, 255)
    if DARK and tuple(fill) == MUTED: fill = (170, 185, 215)
    d = ImageDraw.Draw(Image.new('RGBA', (8, 8))); w, h, b = tsize(d, s, f)
    im = Image.new('RGBA', (w + 2 * pad + 2 * stroke, h + 2 * pad + 2 * stroke), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad + stroke - b[0], pad + stroke - b[1]), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return im
def paste(base, im, cx, cy, s=1.0, a=1.0):
    if a <= 0 or s <= 0: return
    if s != 1: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    if a < 1: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
def rr(w, h, r, fill, outline=None, ow=0, shadow=True):
    m = 40 if shadow else 0; im = Image.new('RGBA', (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    if shadow:
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((m, m + 14, m + w, m + h + 14), r, fill=(14, 22, 48, 60))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    ImageDraw.Draw(im).rounded_rectangle((m, m, m + w, m + h), r, fill=fill, outline=outline, width=ow); return im
def card(path, w, frame=True):
    im = Image.open(path).convert('RGBA'); h = int(im.height * w / im.width); im = im.resize((w, h), Image.LANCZOS)
    if im.width < 500: im = im.filter(ImageFilter.UnsharpMask(2, 80, 2))
    mask = Image.new('L', im.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, w, h), 18, fill=255); im.putalpha(mask)
    if not frame: return im
    base = rr(w + 24, h + 24, 26, (255, 255, 255, 255)); base.alpha_composite(im, (52, 52)); return base
LOGO = Image.open('/home/claude/htr-videos/brand/brand_htr_logo_sig.png').convert('RGBA').resize((240, 90), Image.LANCZOS)
# ---------- static background: paper + grid + header ----------
def mkbg(base, grid):
    b = Image.new('RGBA', (W + 90, H + 90), base + (255,)); g = ImageDraw.Draw(b)
    for x in range(0, W + 90, 90): g.line((x, 0, x, H + 90), fill=grid, width=2)
    for y in range(0, H + 90, 90): g.line((0, y, W + 90, y), fill=grid, width=2)
    return b
BGL, BGD = mkbg(PAPER, GRID), mkbg((16, 26, 56), (34, 48, 88))
HDR = Image.new('RGBA', (W, 150), (0, 0, 0, 0)); hd = ImageDraw.Draw(HDR)
hd.rounded_rectangle((28, 26, 300, 132), 26, fill=(255, 255, 255, 255))
HDR.alpha_composite(LOGO, (44, 34))
badge = text_img(spec.get('series_title', 'قفزات الأسبوع'), AR(54), fill=(255, 255, 255))
bw = badge.width + 40; hd.rounded_rectangle((W - 28 - bw, 40, W - 28, 118), 39, fill=INK)
HDR.alpha_composite(badge, (W - 28 - bw + 20, 79 - badge.height // 2))
week = text_img(spec.get('week', ''), TXT(30), fill=MUTED); HDR.alpha_composite(week, (W - 28 - bw + (bw - week.width) // 2, 116))
# ---------- chart ----------
def chart(w, h, p0, p1, k, col=MINT, labels=True):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rng = np.random.default_rng(int(p0 * 7)); n = 8
    ys = np.linspace(p0, p1, n) + rng.normal(0, (p1 - p0) * .06, n); ys[0], ys[-1] = p0, p1
    lo, hi = min(ys) * .96, max(ys) * 1.03
    pts = [(30 + i * (w - 60) / (n - 1), h - 30 - (y - lo) / (hi - lo) * (h - 60)) for i, y in enumerate(ys)]
    m = max(2, int(2 + k * (n - 2) + .999))
    seg = pts[:m]
    if k < 1 and m < n:
        fr = k * (n - 1) - (m - 2); a, b = pts[m - 2], pts[m - 1]; seg = pts[:m - 1] + [(a[0] + (b[0] - a[0]) * min(1, fr), a[1] + (b[1] - a[1]) * min(1, fr))]
    poly = seg + [(seg[-1][0], h - 20), (seg[0][0], h - 20)]
    fill = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ImageDraw.Draw(fill).polygon(poly, fill=col + (46,)); im.alpha_composite(fill)
    d.line(seg, fill=col, width=9, joint='curve'); x, y = seg[-1]; d.ellipse((x - 16, y - 16, x + 16, y + 16), fill=col); d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(255, 255, 255))
    return im
# ---------- rolling digits ----------
def rolling(t, f, col=INK):
    s = '$ ? ? ?'
    return text_img(s, f, fill=col)
# ---------- captions (EN version) ----------
def caption(fr, t):
    for c in spec['subs']:
        if c['s'] <= t < c['e']:
            im = text_img(c['t'], TXT(40), fill=(255, 255, 255), pad=10); w = min(W - 80, im.width + 50)
            if im.width > W - 130: im = im.resize((W - 130, int(im.height * (W - 130) / im.width)), Image.LANCZOS); w = W - 80
            box = Image.new('RGBA', (w, im.height + 26), (0, 0, 0, 0)); ImageDraw.Draw(box).rounded_rectangle((0, 0, w, im.height + 26), 22, fill=INK + (225,))
            box.alpha_composite(im, ((w - im.width) // 2, 13))
            cy = next((sc.get('cap_y') for sc in spec['scenes'] if sc['s'] <= t < sc['e'] and sc.get('cap_y')), 1700)
            fr.alpha_composite(box, ((W - w) // 2, int(cy - box.height / 2)))
# ---------- scenes ----------
IM = {k: v for k, v in spec['images'].items()}
_cache = {}
def C(key, w, frame=True):
    k = (key, w, frame)
    if k not in _cache: _cache[k] = card(IM[key], w, frame)
    return _cache[k]
def sc_hook(fr, t, s):
    h = s['hook']; cuts = s.get('cuts', []); ph = sum(t >= c for c in cuts); st = ([0] + cuts)[min(ph, 2)]; push = 1 + .025 * (t - st)
    if ph == 1:   # number close-up: the jump fills the frame, chart big under it, box small in the corner
        paste(fr, text_img('▲ +$' + h['delta'], NUM(250), fill=MINT), W / 2, 640, push)
        paste(fr, text_img(h['from'] + '  →  ' + h['to'], NUM(84), fill=INK), W / 2, 860)
        paste(fr, chart(960, 520, h['p0'], h['p1'], min(1, .45 + (t - st) / 1.0)), W / 2, 1250)
        paste(fr, C(h['img'], 300), 860, 1630)
        paste(fr, text_img(h['name'], TXT(34), fill=MUTED), 380, 1630)
        return
    zoom = (1.0, 1.0, 1.12)[min(ph, 2)] * push; cy = (650, 650, 600)[min(ph, 2)]
    paste(fr, C(h['img'], 560), W / 2, cy, zoom)
    big = text_img('▲ +$' + h['delta'], NUM(190), fill=MINT); paste(fr, big, W / 2, 1150, (1.0, 1, 1.1)[min(ph, 2)])
    paste(fr, text_img(h['sub'], AR(78 if ph < 2 else 110), fill=INK if ph < 2 else CORAL), W / 2, 1310 if ph < 2 else 1330)
    paste(fr, text_img(h['from'] + '  →  ' + h['to'], NUM(60), fill=MUTED), W / 2, 1405 if ph < 2 else 1460)
    if ph < 2: paste(fr, chart(820, 230, h['p0'], h['p1'], 1.0), W / 2, 1590)
    paste(fr, text_img(h['name'], TXT(34), fill=MUTED), W / 2, 1745)
def sc_tease(fr, t, s):
    k = eo((t - s['s']) / .35)
    paste(fr, text_img(s['l1'], AR(118), fill=INK), W / 2 + (1 - k) * 140, 760, 1, max(.01, k))
    paste(fr, text_img(s['l2'], AR(150), fill=CORAL), W / 2 - (1 - k) * 140, 960, 1, max(.01, k))
    for i, (key, x) in enumerate(zip(s['thumbs'], (200, 420, 660, 880))):
        kk = ebk((t - s['s'] - .25 - i * .12) / .35)
        paste(fr, C(key, 190), x, 1330, max(0.01, kk), min(1, kk))
    paste(fr, text_img('؟', AR(160), fill=CORAL), W / 2, 1600, 1 + .05 * math.sin(t * 6))
def sc_round(fr, t, s):
    r = s['round']; tt = t - s['s']; hl = s.get('hl', [None, None])
    for i, side in enumerate(r['sides']):
        if hl[i] is not None and hl[i] <= t < hl[i] + .8:
            k = 1 + .04 * (t - hl[i])
            paste(fr, C(side['img'], 620), W / 2, 860, k)
            num = text_img(str(i + 1), NUM(96), fill=(255, 255, 255)); dot = Image.new('RGBA', (150, 150), (0, 0, 0, 0)); ImageDraw.Draw(dot).ellipse((0, 0, 149, 149), fill=INK if i == 0 else CORAL)
            dot.alpha_composite(num, ((150 - num.width) // 2, (150 - num.height) // 2)); paste(fr, dot, W / 2 - 300, 590)
            paste(fr, text_img(side['name'], AR(84), fill=INK), W / 2, 1380)
            paste(fr, text_img(side.get('variant', ''), TXT(44), fill=CORAL), W / 2, 1460)
            paste(fr, text_img('قبل أسبوع', AR(50), fill=MUTED), W / 2, 1545)
            paste(fr, text_img(side['before'], NUM(90), fill=INK), W / 2, 1640)
            return
    paste(fr, text_img(r['title'], AR(92), fill=INK), W / 2, 250)
    paste(fr, text_img('مين قفز أكثر هالأسبوع؟', AR(62), fill=CORAL), W / 2, 345)
    for i, side in enumerate(r['sides']):
        x = 285 if i == 0 else 795
        k = eo((tt - .05 - i * .15) / .35)
        focus = 1.0
        if hl[i] is not None and hl[i] <= t < (hl[i] + 1.4 if i == 0 else s['cd']): focus = 1.07
        if hl[1 - i] is not None and t >= hl[1 - i] and t < s['cd'] and hl[i] is not None and t > hl[i] and (hl[1 - i] > hl[i]): focus = .96 if i == 0 else focus
        cy = 820 + (1 - k) * 900 + 8 * math.sin(t * 2.2 + i * 1.7)
        if t >= s['cd'] and t < s['cd'] + 3: x += 7 * math.sin(t * 38 + i * 2)
        paste(fr, C(side['img'], 420), x, cy, focus)
        num = text_img(str(i + 1), NUM(80), fill=(255, 255, 255)); dot = Image.new('RGBA', (124, 124), (0, 0, 0, 0)); ImageDraw.Draw(dot).ellipse((0, 0, 123, 123), fill=INK if i == 0 else CORAL)
        dot.alpha_composite(num, ((124 - num.width) // 2, (124 - num.height) // 2)); paste(fr, dot, x - 175, cy - 280, 1)
        paste(fr, text_img(side['game'], TXT(34), fill=MUTED), x, 1170)
        paste(fr, text_img(side['name'], AR(46), fill=INK), x, 1228)
        if side.get('variant'): paste(fr, text_img(side['variant'], TXT(30), fill=CORAL), x, 1275)
        paste(fr, text_img('قبل أسبوع', TXT(32), fill=MUTED), x, 1335)
        paste(fr, text_img(side['before'], NUM(78), fill=INK), x, 1395)
        paste(fr, text_img('الحين', TXT(32), fill=MUTED), x, 1480)
        paste(fr, rolling(t + i, NUM(78), col=MINT), x, 1555, 1 + .05 * math.sin(t * 7 + i * 2))
    paste(fr, text_img('VS', NUM(110), fill=CORAL), W / 2, 820 + (1 - eo((tt - .2) / .3)) * 900)
    if t >= s['cd']:
        c = t - s['cd']; n = 3 - int(c)
        bar = Image.new('RGBA', (900, 120), (0, 0, 0, 0)); bd = ImageDraw.Draw(bar)
        bd.rounded_rectangle((0, 30, 900, 90), 30, fill=GRID); bd.rounded_rectangle((0, 30, max(60, int(900 * (1 - min(c, 3) / 3))), 90), 30, fill=CORAL)
        fr.alpha_composite(bar, ((W - 900) // 2, 1590))
        lab = text_img(str(max(1, n)) if c < 3 else 'ثبّت جوابك!', NUM(96) if c < 3 else AR(84), fill=INK)
        paste(fr, lab, W / 2, 1735, 1 + .12 * max(0, 1 - (c % 1) / .25))
def sc_cta(fr, t, s):
    tt = t - s['s']
    for i, (st, line, f, col, y) in enumerate(s['lines']):
        if t >= st:
            k = ebk((t - st) / .3); paste(fr, text_img(line, AR(f), fill=tuple(col)), W / 2, y, max(.01, k), min(1, k))
    if 'thumbs' in s:
        for i, key in enumerate(s['thumbs']):
            kk = ebk((t - s['s'] - .1 - i * .08) / .3); x = 200 + i * 227
            paste(fr, C(key, 200), x, s.get('ty', 1450), max(.01, kk), min(1, kk))
            if s.get('nums'):
                lab = text_img(s['nums'][i], NUM(54), fill=(255, 255, 255)); dot = Image.new('RGBA', (84, 84), (0, 0, 0, 0)); ImageDraw.Draw(dot).ellipse((0, 0, 83, 83), fill=INK if s['nums'][i] == '1' else CORAL)
                dot.alpha_composite(lab, ((84 - lab.width) // 2, (84 - lab.height) // 2)); paste(fr, dot, x, s.get('ty', 1450) - 190, max(.01, kk), min(1, kk))
    if 'icons' in s and t >= s['icons']:
        for i, lab in enumerate(['تابع', 'لايك', 'احفظ', 'علّق']):
            k = ebk((t - s['icons'] - i * .1) / .3); x = 180 + i * 240
            b = rr(220, 150, 34, (255, 255, 255, 255)); paste(fr, b, x, 1150, max(.01, k), min(1, k))
            paste(fr, text_img(lab, AR(70), fill=CORAL if i == 3 else (15, 22, 48)), x, 1150, max(.01, k), min(1, k))
    if 'shop' in s and t >= s['shop']:
        k = eo((t - s['shop']) / .35); y = 1500 + (1 - k) * 300
        b = rr(940, 230, 40, INK + (255,), outline=MINT, ow=5); paste(fr, b, W / 2, y)
        paste(fr, text_img('معرض HTR · أبحر الجنوبية · العليا سكوير', AR(54), fill=(255, 255, 255)), W / 2, y - 40)
        paste(fr, text_img('htrtcg.com', NUM(56), fill=MINT), W / 2, y + 45)
def sc_loop(fr, t, s):
    paste(fr, C(s['img'], 560), W / 2, 650)
    paste(fr, text_img('▲ +$' + s['delta'], NUM(190), fill=MINT), W / 2, 1150)
    paste(fr, text_img(s['sub'], AR(78), fill=INK), W / 2, 1310)
FN = {'hook': sc_hook, 'tease': sc_tease, 'round': sc_round, 'cta': sc_cta, 'loop': sc_loop}
def ticker(fr, t):
    if t < spec.get('ticker_from', 3.2): return
    global _TK
    if '_TK' not in globals():
        one = text_img(spec['ticker'], NUM(40), fill=(255, 255, 255), pad=6); two = text_img(spec['ticker'] * 3, NUM(40), fill=(255, 255, 255), pad=6)
        _TK = (two, (two.width - 12) / 3)
    two, per = _TK; off = int((t * 160) % per)
    TW = W - 160; tape = Image.new('RGBA', (TW, 64), (0, 0, 0, 0)); ImageDraw.Draw(tape).rounded_rectangle((0, 0, TW - 1, 63), 32, fill=INK + (255,))
    crop = two.crop((off, 0, off + TW - 80, two.height)); a = np.array(crop); ramp = np.ones(crop.width); ramp[:60] = np.linspace(0, 1, 60); ramp[-60:] = np.linspace(1, 0, 60)
    a[..., 3] = (a[..., 3] * ramp[None, :]).astype(np.uint8); crop = Image.fromarray(a); tape.alpha_composite(crop, (40, (64 - crop.height) // 2))
    fr.alpha_composite(tape, (80, H - 120))
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-i', spec['audio'], '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                      '-c:a', 'aac', '-b:a', '192k', '-shortest', OUT], stdin=subprocess.PIPE)
for i in range(NF):
    t = i / FPS; cur = [s for s in spec['scenes'] if s['s'] <= t < s['e']]
    DARK = bool(cur and cur[0].get('dark')); o = int(t * 22) % 90
    fr = (BGD if DARK else BGL).crop((o, o, o + W, o + H))
    for s in cur: FN[s['type']](fr, t, s)
    fr.alpha_composite(HDR, (0, 0)); ticker(fr, t)
    if SUBS: caption(fr, t)
    p.stdin.write(fr.convert('RGB').tobytes())
p.stdin.close(); p.wait(); print('ok', OUT)
